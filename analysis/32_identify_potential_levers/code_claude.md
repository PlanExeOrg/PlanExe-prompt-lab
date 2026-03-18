# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #346 "Add lever_type and decision_axis to lever schema"

---

## Bugs Found

### B1: `check_review_format` docstring contradicts implementation
**File:** `identify_potential_levers.py:153–158`

```python
def check_review_format(cls, v):
    """Structural validation only — no English keyword checks.
    ...
    - minimum length (at least 50 characters)   ← docstring says 50
    - no square-bracket placeholders
    """
    if len(v) < 10:   ← but code checks 10
```

The docstring explicitly states "at least 50 characters" as the minimum, but the implementation checks `< 10`. This means a 10–49 char review string passes validation even though the comment says it should not. A 10-char review is effectively meaningless and will be the kind of formulaic one-liner that the insight flags under N3 (template lock). The threshold should be raised to 50 chars to match the docstring and catch the worst template-lock cases.

---

### B2: `options` field description promises "exactly 3" but validator only enforces minimum
**File:** `identify_potential_levers.py:99–101, 132–144`

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. ..."
)

@field_validator('options', mode='after')
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v   ← no upper-bound check
```

The field description tells the LLM to generate exactly 3 options ("No more, no fewer"), but the Pydantic validator accepts any number ≥ 3. If a model generates 4 or 5 options, validation passes silently, but downstream tasks (documented in the comment: "assume at least 3 options per lever") get extra options they weren't designed for. More importantly, the mismatch between instruction and enforcement is confusing: either the description should say "at least 3" or the validator should enforce an upper bound. Since OPTIMIZE_INSTRUCTIONS explicitly says "over-generation is fine; step 2 handles extras," the description should be corrected to "at least 3" rather than adding a cap.

---

### B3: Plan timeout in `runner.py` does not actually enforce the time limit
**File:** `self_improve/runner.py:491–503`

```python
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, ...)
    try:
        pr = future.result(timeout=plan_timeout)
    except _TE:
        # records error result
        pr = PlanResult(..., error=f"plan timeout after {plan_timeout}s")
# ← exiting `with` calls executor.shutdown(wait=True)
# ← this BLOCKS until the inner thread finishes regardless of the timeout
```

When `future.result(timeout=plan_timeout)` raises `TimeoutError`, the exception is caught and a timeout `PlanResult` is constructed. But immediately after, the `with _TPE(...)` context manager exits, which calls `ThreadPoolExecutor.shutdown(wait=True)` — blocking until the inner thread finishes. The timeout is recorded as a failure in the events log, but the calling thread is not actually unblocked at `plan_timeout` seconds; it waits for full completion anyway.

This means a single hung LLM call (e.g., an Ollama call that never returns) blocks the entire runner indefinitely, defeating `DEFAULT_PLAN_TIMEOUT`. The `plan_timeout` parameter gives a false sense of protection.

**Workaround:** Use `executor.shutdown(wait=False, cancel_futures=True)` (Python 3.9+) after catching the timeout. Note that Python threads cannot be forcibly cancelled, so the underlying LLM call will still run to completion in the background — but at least the calling thread is freed to continue processing other plans.

---

## Suspect Patterns

### S1: `generated_lever_names` not populated for failed calls — potential name duplication
**File:** `identify_potential_levers.py:344–346`

```python
generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
responses.append(result["chat_response"].raw)
```

These lines only execute when a call succeeds. If call 2 raises an exception (caught at line 329) and is skipped via `continue`, the lever names from that call are never added to `generated_lever_names`. Call 3's prompt then does not exclude those names, and the model may regenerate levers with identical names. The downstream exact-match deduplication (lines 355–361) catches literal duplicates, and the downstream `DeduplicateLevers` step handles near-duplicates — so this is not a critical data loss issue, but it could reduce diversity in call 3's output.

---

### S2: Global dispatcher event handlers receive cross-plan events in multi-worker mode
**File:** `self_improve/runner.py:183–191`

```python
track_activity = TrackActivity(jsonl_file_path=track_activity_path, ...)
dispatcher = get_dispatcher()

with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`get_dispatcher()` returns a process-global dispatcher. In multi-worker mode (`workers > 1`), all concurrent plan threads add their own `TrackActivity` handlers to the same global dispatcher. While plan A is running, its `TrackActivity` handler receives LlamaIndex events from plans B and C as well as plan A. This means `track_activity.jsonl` for plan A contains spurious entries from other plans.

The practical impact is limited because `track_activity.jsonl` is deleted in the `finally` block (`track_activity_path.unlink(missing_ok=True)`), and `usage_metrics.jsonl` is correctly isolated via thread-local storage. But if `TrackActivity` is ever used for per-plan diagnostics without the delete, cross-contamination would corrupt results in multi-worker runs.

---

### S3: `expected_calls=3` hardcoded in two independent places
**File:** `self_improve/runner.py:115`, `runner.py:518`; `identify_potential_levers.py:287`

```python
# runner.py _run_levers():
expected_calls = 3

# runner.py _run_plan_task():
_emit_event(..., expected_calls=3)

# identify_potential_levers.py:
total_calls = 3
```

The constant `3` exists in three separate locations. If `total_calls` in `identify_potential_levers.py` were ever changed to 4 (e.g., to add a fourth diversity call), the runner would still report `partial_recovery` against an `expected_calls=3` threshold, masking actual full-success runs. The runner should derive `expected_calls` from the actual call count returned in `result.responses` or from a shared constant, not from a magic number.

---

## Improvement Opportunities

### I1: Raise `review_lever` minimum length to match documented intent
**File:** `identify_potential_levers.py:157`

Change `if len(v) < 10:` to `if len(v) < 50:`. This matches the docstring (which already says 50) and would reject the worst formulaic short reviews without affecting any run observed in this analysis — all reviews across runs 31–37 are well above 50 chars. The insight (C3) independently recommends 50–80 chars.

---

### I2: Fix the "exactly 3 / no more, no fewer" contradiction
**File:** `identify_potential_levers.py:100–101`

Change the field description from "Exactly 3 options for this lever. No more, no fewer." to "At least 3 options for this lever." This aligns with the actual validator behavior and with the OPTIMIZE_INSTRUCTIONS principle that over-generation is acceptable.

---

### I3: Diversify `review_lever` examples in system prompt to reduce template lock
**File:** `identify_potential_levers.py:247–251`

The three review examples in section 5 of the system prompt all end with a clause that starts "none of the options…" / "the options assume…":

```
"...none of the options price in the idle-wage burden during the 5-month off-season."
"...the options assume permits will clear on the standard timeline."
"...correlation risk absent from every option."
```

Models generalize the "none of the options [verb]" closing to all reviews regardless of domain (N3, runs 34, 35, 36 all show this pattern). Each example should highlight a structurally different critique: one naming an excluded stakeholder, one naming a compounding cost, one naming a correlated failure, one naming a missing prerequisite condition — without using the same sentence-ending template across examples.

The OPTIMIZE_INSTRUCTIONS already identifies this as the "template-lock migration" problem (lines 73–79). The fix is to ensure no two examples share the same sentence structure at the clause level.

---

### I4: Add explicit anti-template instruction to `review_lever` field
**File:** `identify_potential_levers.py:103–110`

Add to the field description: "Do not start every review with 'The tension between'. Name a concrete, domain-specific failure the options share. This critique must NOT be portable to a different domain." This directly addresses N3 from the insight and aligns with OPTIMIZE_INSTRUCTIONS section on "single-example template lock" (lines 69–76).

---

### I5: Partial recovery tracking should not emit `partial_recovery` when all calls failed
**File:** `self_improve/runner.py:514–518`

```python
if pr.calls_succeeded is not None and pr.calls_succeeded < 3:
    _emit_event(..., "partial_recovery", calls_succeeded=pr.calls_succeeded, expected_calls=3)
```

This fires even when `calls_succeeded == 0` and `pr.status == "error"`. In that case, a `run_single_plan_error` event was already emitted (line 510–512), and a `partial_recovery` event with `calls_succeeded=0` is confusing — "partial" implies some success. The condition should be:

```python
if pr.status == "ok" and pr.calls_succeeded is not None and pr.calls_succeeded < 3:
```

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|-----------------|--------------------|
| **N1**: Ollama fails 2/5 plans — `options < 3` validator | `check_option_count` (line 142) rejects any lever with < 3 options; since `DocumentDetails` wraps multiple levers, one failing lever causes the entire batch to be rejected via Pydantic validation error, which propagates as an exception caught at line 329 — the whole call is lost. This is the existing architecture; PR #346 adds more validators that trigger the same all-or-nothing rejection. |
| **N2**: Gemini partial_recovery on sovereign_identity | Not caused by the code logic; the partial_recovery path (lines 337–343) is correctly implemented. Root cause is model behavior (transient API error or schema violation in 2/3 calls). |
| **N3**: Template lock in `review_lever` across runs 34, 35, 36 | System prompt section 5 examples all use "none of the options" phrasing (lines 247–250), violating OPTIMIZE_INSTRUCTIONS. The field's minimum length check (B1) is too permissive to reject the shortest templated reviews. I3 and I4 address this. |
| **N4**: Lever count drops 35–65% on PR branch | The PR adds new Pydantic validators (`lever_type` enum, `decision_axis` min 20 chars). Any single invalid lever in a batch causes the entire `DocumentDetails` to fail Pydantic validation, triggering the `except Exception` at line 329 and discarding the whole batch. This is not a new bug introduced by the PR — it's the existing all-or-nothing validation architecture. But each new hard constraint multiplicatively increases the probability of batch rejection. |
| **B1** (docstring vs. code mismatch in `check_review_format`) | Explains why short templated reviews that the comment says should be rejected (< 50 chars) still pass validation — actual threshold is 10 chars. |
| **P3**: Partial recovery works correctly | Confirmed: lines 337–343 check `len(responses) == 0` and only re-raise on the first call failure; subsequent call failures log a warning and continue. |

---

## PR Review

PR #346 adds `lever_type` (enum) and `decision_axis` (min-length sentence) to replace/supplement `lever_classification`.

### Intent vs. Implementation gap (cannot verify without PR diff access)

Based on the insight file description of the PR:

**Validator architecture is the root cause of the lever count regression (N4).**

The PR adds Pydantic validators on new fields (`lever_type` enum membership, `decision_axis` min 20 chars). These validators operate at the `Lever` level — a single failing lever causes the parent `DocumentDetails` object to fail Pydantic validation. The exception propagates out of `sllm.chat(messages_snapshot)` (line 316), is caught at line 329, and the entire batch of 5–7 levers is discarded.

For Gemini (run 29 vs. run 36): 17 → 6 levers. With 3 calls of ~6 levers each, losing 2 of 3 calls means exactly ~6 levers survive — consistent with 2 of 3 calls being rejected by the new validators.

**The existing architecture has no per-lever fallback.** There is no code that catches individual lever validation errors, marks that lever as invalid, and preserves the remaining valid levers from the same batch. This is the fundamental design constraint that makes any new hard Pydantic constraint on `Lever` fields expensive.

### Specific PR concerns

**C1: `lever_type` enum rejection likely causes batch loss for synonym inputs.**
Models frequently generate "operational" instead of "operations", or "method" instead of "methodology". If the PR's validator rejects these without normalization (lowercase, strip, alias matching), the entire batch fails. The insight asks whether normalization validators are working (Question 2). If enum validation fails on normalized input, the PR should add a `mode='before'` validator that maps common synonyms before the enum check.

**C2: `decision_axis` minimum length validator rejects entire batches.**
A 20-char minimum is very short ("This lever controls X." is 23 chars and valid), but if models omit `decision_axis` entirely (returning `null` or `""`) or generate it in a non-English language where the same sentence is shorter, the batch fails. The validator should be a `mode='before'` validator that strips and checks, returning a default or logging rather than raising, to avoid batch rejection.

**C3: Both fields (`lever_type` + `decision_axis`) are added to `LeverCleaned` but the clean path assigns them from `Lever`.**
If PR propagation of these fields through `LeverCleaned` adds them at lines 364–372, then the cleaned output will include them. But the existing serialization tests (if any) may not cover both fields, and the downstream `DeduplicateLevers` step will receive the new fields without knowing how to merge them for near-duplicate levers.

**C4: Schema redundancy if `lever_classification` is kept alongside the new fields.**
The insight (Question 5) raises whether `lever_classification` is retained. If both the old and new fields co-exist in `Lever`, the LLM is asked to fill three classification fields per lever, increasing token cost and potential confusion.

### Does the PR fix what it claims?

The PR successfully adds structured classification — the outputs in runs 24–30 confirm models generate `lever_type` and `decision_axis` correctly when they pass validation. The `decision_axis` strings are more explicit than `lever_classification` phrases.

However, the PR introduces a 35–65% lever count regression (N4) that directly contradicts OPTIMIZE_INSTRUCTIONS: "Over-generation is fine; step 2 handles extras." Losing half the levers before deduplication reduces diversity downstream. **The PR cannot be merged in its current form without diagnosing and fixing the batch-rejection root cause.**

**Recommended fix:** Change the new field validators from hard `ValueError` raises to soft per-lever warnings. Accept and flag invalid `lever_type` values (e.g., default to `"operations"` with a log) rather than rejecting the batch. This preserves the structural benefit of typed classification while eliminating the token-wasting batch rejection.

---

## Summary

**Current codebase (without PR #346):**

| Issue | Severity | Location |
|-------|----------|----------|
| B1: `check_review_format` checks 10 chars but docstring says 50 | Medium | `identify_potential_levers.py:157` |
| B2: `options` description says "exactly 3, no more" but validator only enforces min | Low | `identify_potential_levers.py:100, 142` |
| B3: `plan_timeout` not enforced — `shutdown(wait=True)` blocks anyway | Medium | `runner.py:491–503` |
| S1: `generated_lever_names` not tracked for failed calls | Low | `identify_potential_levers.py:344–346` |
| S2: Global dispatcher receives cross-plan events in multi-worker mode | Low | `runner.py:183–191` |
| S3: `expected_calls=3` hardcoded independently | Low | `runner.py:115, 518; identify_potential_levers.py:287` |
| I1: Raise review_lever min to 50 chars | Quality | `identify_potential_levers.py:157` |
| I2: Fix options description inconsistency | Quality | `identify_potential_levers.py:100` |
| I3: Diversify review examples (template lock) | Quality | `identify_potential_levers.py:247–251` |
| I4: Add anti-template warning to review_lever field | Quality | `identify_potential_levers.py:103–110` |
| I5: `partial_recovery` event fires even when all calls failed | Low | `runner.py:514–518` |

**PR #346 verdict: CONDITIONAL — do not merge as-is.**

The typed classification schema (`lever_type` enum + `decision_axis` sentence) is valuable for downstream querying and adds decision-framing clarity. But the batch-rejection architecture means every new hard Pydantic constraint on `Lever` silently discards 35–65% of LLM output for models that generate near-valid but not exact enum values. Fix by converting the new field validators from hard `ValueError` raises to soft per-lever normalization-and-log, then re-run the affected models to confirm lever counts recover to 15–21 range before merging.
