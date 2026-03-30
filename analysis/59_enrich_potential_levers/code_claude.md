# Code Review (claude)

## Bugs Found

### B1 — Banned phrases hard-coded in `Lever.consequences` field description

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:115–118`

```python
consequences: str = Field(
    description=(
        ...
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        "those belong exclusively in review_lever. "
        ...
    )
)
```

The `OPTIMIZE_INSTRUCTIONS` constant (lines 80–82) explicitly warns:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."

Yet the `Lever.consequences` Pydantic field description names the exact banned phrases "Controls ... vs." and "Weakness:". This field description is passed verbatim to the LLM as part of the structured-output schema. For weak models (llama3.1, qwen3-30b), this "Do NOT include" prohibition acts as a template: they copy the named phrases into `review_lever`, which then propagates to downstream synergy/conflict text.

Note: the same language appears in `LeverCleaned.consequences` (lines 209–215), but `LeverCleaned` is never sent to an LLM, so it is harmless there.

**Fix:** Remove the phrase-naming prohibition from `Lever.consequences`. Replace it with a structural cue such as "Describe direct effects and downstream trade-offs only. Do not include critique or evaluation language." — following the guideline to describe required content, not forbidden patterns.

---

### B2 — `partial_recovery` event fires for normal 2-call completions

**Files:**
- `self_improve/runner.py:131–135` (`_run_levers`)
- `self_improve/runner.py:577–583` (`_run_plan_task`)

```python
# _run_levers
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )

# _run_plan_task
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

The comment immediately above the `_run_levers` check (lines 128–130) states:
> "A 2-call success is normal for models that produce 8+ levers per call."

With `min_levers=15` and models that generate 8 levers per call, a 2-call run produces 16 levers (≥ 15) and exits correctly. Yet the `< 3` threshold emits a `partial_recovery` event and a `WARNING` log for every such successful 2-call run. The event name and `expected_calls=3` label are misleading: they make a normal outcome look like a failure, polluting `events.jsonl` with false alerts and making it harder to spot real problems.

**Fix:** Lower the warning threshold to `< 2` (flag only single-call completions) or base the check on actual lever count (e.g., warn only if `len(result.levers) < min_levers`) rather than call count.

---

### B3 — UUIDs in `full_lever_context_str` cause UUID cross-references in synergy/conflict output

**File:** `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py:209`

```python
full_lever_context_str = "\n".join([
    f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize
])
```

The `OPTIMIZE_INSTRUCTIONS` constant (lines 88–92) explicitly documents this as a known problem:
> "UUID cross-reference format inconsistency. The full_lever_context_str includes lever_id UUIDs, causing models to copy UUIDs into synergy_text and conflict_text in varying formats (full UUID, 8-char truncated, backtick-quoted name, plain name)."

The code still includes lever UUIDs in the context string despite this being a documented known problem. This directly causes the UUID cross-reference formatting inconsistency seen in synergy/conflict fields: models copy the UUID from the context string into `synergy_text` instead of using the lever name.

**Fix:** Remove lever_id from the context string:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```
The lever_id is only needed in the batch prompt (so the LLM can return it), not in the full-list context. The batch `lever_details_for_prompt` already includes `lever_id` per lever.

---

## Suspect Patterns

### S1 — Closure over loop variable in both `execute_function` definitions

**Files:**
- `identify_potential_levers.py:317–327` — `execute_function` closes over `messages_snapshot`
- `enrich_potential_levers.py:252–259` — `execute_function` closes over `chat_message_list`

In both files, `execute_function` is a closure that captures a loop-local variable by Python name binding (not by value). This is currently safe because `llm_executor.run(execute_function)` is called immediately in the same iteration. However, if `llm_executor.run` were ever changed to defer the call (e.g., via async dispatch or thread pool), the closure would capture the last value of the loop variable instead of the current one.

The pattern is idiomatic Python for deferred execution but risky as the codebase evolves. Using a default-argument capture (`def execute_function(llm, _msgs=messages_snapshot): ...`) would make the binding explicit and immune to deferred-execution bugs.

---

### S2 — Adaptive batch size probe creates a full LLM instance to read metadata

**File:** `enrich_potential_levers.py:197–204`

```python
probe_llm = llm_executor.llm_models[0].create_llm()
context_window = probe_llm.metadata.context_window
```

Creating a full LLM object just to read `context_window` may trigger authentication, connection setup, or rate-limit initialization depending on the provider. The bare `except Exception` silently falls back to the default batch size on any failure, which could mask configuration errors (e.g., a bad API key causing the probe to fail, leaving the wrong batch size in effect). The comment does not indicate what failure modes are expected.

---

### S3 — `options` field description and validator are inconsistent

**File:** `identify_potential_levers.py:121–159`

The `Lever.options` field description says "Exactly 3 options for this lever. No more, no fewer." but `check_option_count` only rejects `len(v) < 3` — it allows 4, 5, or more options through silently. The `DocumentDetails` comment at line 189 says "Over-generation is fine" and points to `DeduplicateLeversTask`. This is intentional, but the field description sent to the LLM ("No more, no fewer") contradicts the actual validation behavior. If a model generates 4 options (reading "no more"), the validator accepts it — but the LLM was instructed it would be rejected. This contradiction may cause weaker models to oscillate between 3 and 4 options across calls.

---

### S4 — Thread-safety gap: TrackActivity handler added under lock but active without lock

**File:** `self_improve/runner.py:248–282`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
...
finally:
    with _file_lock:
        set_usage_metrics_path(None)
        dispatcher.event_handlers.remove(track_activity)
```

The setup and teardown are protected by `_file_lock`, but the entire execution between add and remove is unprotected. If two threads call `dispatcher.event_handlers.remove(track_activity)` concurrently and `event_handlers` is a plain list, the `remove` call could raise `ValueError` if another thread's handler was already removed. This is likely safe in practice (each thread adds its own `TrackActivity` instance), but the type of `event_handlers` is not visible here and the pattern is fragile.

---

## Improvement Opportunities

### I1 — Add lever_id format validation before enriched_levers_map lookup

**File:** `enrich_potential_levers.py:267–276`

```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update(...)
    else:
        logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
        errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

The current check (`char.lever_id in enriched_levers_map`) catches phantom IDs after the fact but provides no diagnostic about *why* the ID is wrong. For llama3.1, the root cause is UUID truncation (e.g., `056fa843-5572-40a5-bca5-bca5cc18408` — 35 chars, missing last digit). A UUID format pre-check would immediately distinguish:
- Format-invalid ID (truncated/hallucinated UUID): likely a non-function-calling model misformatting structured output
- Format-valid but unrecognized ID: model invented a valid UUID not from the input

Adding `import re; UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')` and checking it before the map lookup would make the error type more specific and the diagnostic more actionable.

---

### I2 — Add validator to detect fabricated percentages in `consequences` field at source

**File:** `identify_potential_levers.py:111–119`

The insight (N4) shows fabricated percentage claims in `consequences` propagating into `enrich_potential_levers` descriptions for all 7 models. The root cause is at `identify_potential_levers`: the `consequences` field has no numeric-claim validator despite the system prompt saying "Do not fabricate percentages or cost estimates."

A `@field_validator('consequences', mode='after')` checking for `\d+%` or `\d+x\b` patterns would catch fabricated statistics at generation time, before they enter the pipeline and get echoed downstream. It need not reject — a warning-level log entry is sufficient to quantify the problem's prevalence across models.

---

### I3 — Update `OPTIMIZE_INSTRUCTIONS` to distinguish phantom lever IDs from phantom lever names

**File:** `enrich_potential_levers.py:65–66`

The current "Phantom lever references" entry in `OPTIMIZE_INSTRUCTIONS` covers lever *names* referenced in synergy/conflict text that don't exist in the input. PR #456 surfaced a distinct issue: lever *IDs* returned in the characterization schema itself that are not in the input (`unknown_lever_id` errors). These are different failure modes:

- Phantom name: model writes "synergizes with Stakeholder Engagement Lever" but no such lever exists
- Phantom ID: model returns `"lever_id": "056fa843-..."` (truncated UUID) causing the characterization to be silently discarded

The OPTIMIZE_INSTRUCTIONS should add a separate entry for phantom lever IDs, note that non-function-calling models (`is_function_calling_model: false`) are most susceptible, and recommend the UUID format pre-check (I1 above).

---

### I4 — Use `field(default_factory=list)` for `errors` in `EnrichPotentialLevers` dataclass

**File:** `enrich_potential_levers.py:180–184`

```python
@dataclass
class EnrichPotentialLevers:
    errors: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
```

The `None`-default pattern for a mutable field is a documented Python dataclass footgun. The `__post_init__` fix is correct, but `field(default_factory=list)` is the idiomatic, footgun-free form:

```python
from dataclasses import dataclass, field
errors: List[Dict[str, Any]] = field(default_factory=list)
```

This eliminates the `__post_init__` boilerplate and removes any ambiguity about whether `None` is ever a valid value.

---

### I5 — `review_lever` length cap is not enforced in `check_review_format`

**File:** `identify_potential_levers.py:161–177`

The system prompt (line 263) says "Keep each `review_lever` to one sentence (20–40 words)" but `check_review_format` only enforces a 10-character minimum. A 300-word `review_lever` passes validation. Combined with the "Verbosity amplification" known problem in OPTIMIZE_INSTRUCTIONS, this means models can produce very long review text that inflates downstream context and degrades scenario quality. A soft upper bound (e.g., reject > 500 characters) would catch runaway outputs without being too strict for legitimate edge cases.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Root Cause |
|----------------|---------------|------------|
| N2 — llama3.1 phantom lever IDs (3 levers unenriched) | `enrich_potential_levers.py:267–276` | No lever_id format pre-validation; truncated UUIDs from non-function-calling model are silently treated as unknown (B3-adjacent, I1) |
| N3 — gpt-5-nano "Purpose:" template reappears in gta_game | `identify_potential_levers.py:115–118` | `consequences` field description contains named banned phrases ("Controls ... vs.", "Weakness:") that small models treat as templates (B1) |
| N4 — Fabricated % claims in description fields (all models, pre-existing) | `identify_potential_levers.py:111–119` → `enrich_potential_levers.py:233–249` | `consequences` field has no validator rejecting numeric fabrications; enrich prompt includes `consequences` text verbatim, models echo it into `description` (I2) |
| OPTIMIZE_INSTRUCTIONS: UUID cross-reference format inconsistency | `enrich_potential_levers.py:209` | `full_lever_context_str` still includes UUIDs despite documented known problem (B3) |
| Consequence echoing (OPTIMIZE_INSTRUCTIONS) | `enrich_potential_levers.py:233–249` | `lever_details_for_prompt` includes `Consequences: {lever.consequences}` which models summarize verbatim instead of building a richer description |
| P2/P3 — Batch count normalized after PR | `enrich_potential_levers.py:196–204` | Adaptive batch size probe correctly reads `context_window` (not `num_output`) — implementation is correct |

---

## PR Review

**PR #456:** "Adaptive batch size, guarded retry, and OpenRouter config fixes for enrich step"

### Adaptive batch size (lines 196–204)

**Correct.** The probe reads `context_window` (the model's actual token budget) rather than `num_output` (max_tokens config). The `SMALL_CONTEXT_THRESHOLD=3000` is set intentionally below the OpenRouter fallback value of 3900 to prevent false positives. The intent is valid.

**Gap:** Models with a genuine `context_window` between 3000 and 3900 would not receive the small batch size. No known deployed model falls in this range, but the gap is narrow enough to surprise if a new model is added with a context window in this range without an explicit `context_window` override in `baseline.json`.

**Gap:** The `except Exception` on the probe (lines 203–204) silently ignores all probe failures. If `create_llm()` raises a configuration error, the run proceeds with default batch_size=5, which may be too large for the model. A narrower exception type (e.g., `AttributeError`, `RuntimeError`) plus a `logger.warning` for unexpected failures would improve debuggability.

### Guarded retry (lines 283–308)

**Correct.** The `can_retry` guard checks three conditions: `len(batch) > 1`, `depth < MAX_RETRY_DEPTH`, and `elapsed < MAX_RETRY_BUDGET_SECONDS`. The insert-at-0 pattern correctly prepends sub-batches to process them before continuing with the remaining original batches:

```python
pending_batches.insert(0, (batch[mid:], depth + 1))
pending_batches.insert(0, (batch[:mid], depth + 1))
# Result: [batch[:mid], batch[mid:], <remaining original batches>]
```

**Minor style issue:** `pending_batches.pop(0)` on a list is O(n). For the typical 2-batch-per-plan case this is inconsequential, but a `collections.deque` with `popleft()`/`appendleft()` would be semantically cleaner.

### Error tracking (lines 276, 295, 308, 317–320)

**Correct.** Four distinct error types (`unknown_lever_id`, `batch_retry`, `batch_skipped`, `incomplete`) are tracked with enough context to reconstruct what happened offline. The insight (N2) confirms this: the llama3.1 phantom-ID bug was discovered *because* of this new field. The `save_raw` output format (metadata, errors, characterized_levers) is backward-compatible.

**Note:** The `errors` dataclass field uses `None` as sentinel with `__post_init__` initialization (see I4). This works but `field(default_factory=list)` is cleaner.

### `batches_succeeded` counter (line 265)

**Correct.** Counter increments for each successful LLM call, including split sub-batches. A 5-lever batch that fails and splits into 2+3 will count as 2 on success, not 1. This inflates `batches_succeeded` relative to "number of original batches" but accurately reflects "number of successful LLM calls," which is the more useful metric for cost/retry analysis.

### OPTIMIZE_INSTRUCTIONS updates

**Correct** for the two entries added (max_tokens overflow, OpenRouter context_window fallback). The new entries match the root causes confirmed by runs 4/20–26.

**Missing:** No entry added for phantom lever IDs (`unknown_lever_id` error type). This was discovered *by this PR's error tracking* and should be documented in OPTIMIZE_INSTRUCTIONS while the details are fresh (see I3).

### Did the PR fix the targeted issues?

| Claim | Assessment |
|-------|-----------|
| OpenRouter cw fix (3900 → correct values) | YES — confirmed by metadata inspection (P2) |
| gpt-oss-20b max_tokens overflow | YES — 0/5 → 4/5 (P1) |
| Adaptive batch size avoids false positives | YES — SMALL_CONTEXT_THRESHOLD=3000 < 3900 (P3) |
| Guarded retry on batch failure | YES — implemented, not triggered in runs 4/20–26 (P4) |
| Error tracking in raw output | YES — directly surfaced llama3.1 phantom ID bug (P5) |
| Accurate batches_succeeded | YES — runner.py uses `result.batches_succeeded` (line 184) |

**No regressions introduced by the PR.** The gpt-5-nano "Purpose:" template reappearance (N3) is input-dependent and pre-existing (the template suppression from PR #451 is fragile, not a regression from this PR). The llama3.1 phantom ID issue (N2) was pre-existing and only made visible by the PR's error tracking.

---

## Summary

### identify_potential_levers.py

The main code-quality issue is **B1**: the `Lever.consequences` field description names exact banned phrases ("Controls ... vs.", "Weakness:") in a "Do NOT include" prohibition, directly violating the OPTIMIZE_INSTRUCTIONS guidance against naming banned phrases. This is a prompt-quality bug that may explain why gpt-5-nano's "Purpose:" template reappeared (N3) — weak models read the prohibition text as instructions rather than constraints, and copy the banned phrases into fields where they don't belong.

The fabricated-percentage problem (N4) is pre-existing and has no validator at source; adding a `field_validator` on `consequences` to detect `\d+%` patterns (I2) would quantify it and block propagation to the enrich step.

The `partial_recovery` false alert (B2) creates event noise for all normal 2-call completions — a minor operational quality issue.

### enrich_potential_levers.py

The unresolved documented issue is **B3**: UUIDs in `full_lever_context_str` despite being listed as a known problem in OPTIMIZE_INSTRUCTIONS since at least analysis 54. Removing UUIDs from the context string (I2/B3 fix) is a one-line change that would eliminate the UUID cross-reference contamination in synergy/conflict fields.

The phantom lever ID diagnostic (I1) would improve visibility into llama3.1 failures by distinguishing format-invalid IDs (truncated UUIDs) from format-valid but unrecognized IDs.

### PR #456

**Assessment: SOUND.** The PR correctly fixes the targeted infrastructure problems. The adaptive batch size, guarded retry, and error tracking are implemented correctly. The OpenRouter context_window fixes are confirmed effective (P1–P3). No new bugs were introduced.

Follow-up actions the PR enables but leaves open:
1. Add OPTIMIZE_INSTRUCTIONS entry for phantom lever ID generation (I3)
2. Remove UUIDs from `full_lever_context_str` (B3)
3. Fix `Lever.consequences` field description to remove named banned phrases (B1)
