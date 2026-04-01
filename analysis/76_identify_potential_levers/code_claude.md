# Code Review (claude)

## Bugs Found

### B1 — `partial_recovery` event threshold is inconsistent with log warning threshold
**File:** `self_improve/runner.py:131–133` vs `runner.py:577–583`

`_run_levers` emits a logger.warning whenever `actual_calls < 3`:
```python
# runner.py:131
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```
But `_run_plan_task` only emits the `partial_recovery` event to `events.jsonl` when `calls_succeeded < 2`:
```python
# runner.py:577
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 2):
    _emit_event(events_path, "partial_recovery", ...)
```
The comment above the warning (runner.py:128–130) explicitly says "A 2-call success is normal for models that produce 8+ levers per call." So the log warning fires as a false alarm for 2-call successes, while the recorded event does not. Monitoring dashboards that watch `events.jsonl` will miss these log-level warnings; log watchers will flag normal completions. The two thresholds should agree: either both use `< 2` (only flag true partial recovery) or both use `< 3` (flag anything below the expected 3-call path).

---

### B2 — Global dispatcher contamination under parallel plan execution
**File:** `self_improve/runner.py:248–251`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```
`set_usage_metrics_path` uses thread-local storage (comment says so). But `dispatcher.add_event_handler(track_activity)` appends to the **globally shared** llama_index dispatcher. When `workers > 1`, every thread's `TrackActivity` handler is added to the same dispatcher. All LLM events from all concurrent plans are broadcast to **all** registered handlers simultaneously. A plan's `track_activity` file will contain events from other plans running in parallel. The `_file_lock` guard only makes the registration atomic; it does not scope the handler to the current thread's events.

This is a correctness bug for any run with `luigi_workers > 1`. The `finally` block at runner.py:280–282 eventually removes the handler, but the data written during the concurrent window is already corrupted.

---

### B3 — Timed-out plan thread continues writing output after timeout is recorded as an error
**File:** `self_improve/runner.py:553–566`

```python
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, ...)
    try:
        pr = future.result(timeout=plan_timeout)
    except _TE:
        pr = PlanResult(
            name=plan_name, status="error", ...,
            error=f"plan timeout after {plan_timeout}s",
        )
```
When `future.result()` raises `TimeoutError`, the error result is recorded immediately. However, the underlying `run_single_plan` thread is **not cancelled** — Python's `ThreadPoolExecutor` has no cancellation mechanism for already-running futures. The thread continues executing and will eventually write output files (lever JSON, usage metrics, etc.) to `plan_output_dir`.

Consequence: `outputs.jsonl` records the plan as errored (status=`"error"`), but the `outputs/<plan_name>/002-10-potential_levers.json` file appears on disk with valid content. The insight analysis in run 40 (gpt-oss-20b) confirms this exactly: two plans recorded `"plan timeout after 600s"` in `events.jsonl` yet both produced complete lever files with 18 levers each (Insight Negative #4). The plan looks errored to the harness but succeeded on disk — a silent inconsistency between the event log and filesystem state.

Additionally, the leaked thread's `finally` block in `run_single_plan` (runner.py:279–282) has not executed when the error is recorded. The stale `TrackActivity` handler remains in the global dispatcher (compounding B2) until the thread eventually completes.

---

## Suspect Patterns

### S1 — Subsequent-call user prompt provides no review-quality reinforcement
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:300–305`

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```
This is the only modification for calls 2+. The system prompt is identical across all calls (same `system_message` object, runner.py:308–313), so the review quality instructions ARE present. However, the modified user message shifts the model's focus to name diversity. For weaker models, the imperative "Generate MORE levers with completely different names" at the top of the message appears to dominate attention — the model prioritizes novelty over quality and falls back to shallow strategies (consequence restatement for llama3.1). There is no reminder that `review_lever` must be a genuine critical assessment, not a paraphrase of consequences.

This is the most likely code-level root cause of llama3.1's consequence-parroting regression in later calls (Insight Negative #1).

---

### S2 — `strategic_rationale` chain-of-thought field is silently skippable
**File:** `identify_potential_levers.py:182–185`

```python
strategic_rationale: Optional[str] = Field(
    default=None,
    description="A concise strategic analysis (around 100 words)..."
)
```
The comment says this field "forces the LLM to reason about the project's trade-offs before generating levers" and "Do NOT remove." But with `Optional[str]` and `default=None`, a model that omits the field entirely passes validation silently. The chain-of-thought benefit is lost without any warning or retry. Models that skip this field in early calls may produce lower-quality levers — especially relevant for weaker models that are already prone to shallow analysis.

---

### S3 — No cross-field validation for consequence parroting
**File:** `identify_potential_levers.py:160–176`

The `check_review_format` validator enforces minimum length (10 chars) and no square brackets. It cannot detect the specific quality failure where `review_lever` is a near-verbatim restatement of `consequences` with only modal verb substitution ("could" → "can"). This requires comparing two sibling fields, which needs a `model_validator` on `Lever`, not a `field_validator`.

The insight (Negative #1) shows levers where `consequences = "Failing to prepare for emergencies could result in catastrophic consequences"` and `review_lever = "Failing to prepare for emergencies can result in catastrophic consequences"` — over 90% word overlap, yet both fields pass all validators.

---

### S4 — `options` field accepts > 3 items without any warning
**File:** `identify_potential_levers.py:146–158`

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v
```
The field description says "Exactly 3 options… No more, no fewer." The system prompt repeats "exactly 3." But there is no upper-bound validator. A model returning 4 or 5 options passes silently. This is different from the intentional over-generation of levers (which has an explicit comment at `DocumentDetails.levers` explaining the design decision). Options with > 3 items are not trimmed downstream — they remain in the saved lever JSON and could confuse the `EnrichLevers` and `ScenarioGeneration` steps that assume exactly 3 options per lever.

---

## Improvement Opportunities

### I1 — Add review-guidance note to subsequent-call user prompt
**File:** `identify_potential_levers.py:300–305`

The subsequent-call prompt could include a single reminder sentence:
```
"Each review_lever must be a genuine critical assessment — not a restatement of the consequence — in one sentence (20–40 words)."
```
This targets llama3.1's later-call degradation. Risk: if the wording itself becomes a template target, it could introduce a new pattern. Should be tested in isolation against llama3.1. Unlike adding to the field description, this is in the user turn only and does not affect call 1 at all.

---

### I2 — Add `model_validator` for consequence-parroting detection
**File:** `identify_potential_levers.py`, after `check_review_format`

```python
@model_validator(mode='after')
def check_review_not_parroting_consequence(self) -> 'Lever':
    cons_words = set(self.consequences.lower().split())
    rev_words = set(self.review_lever.lower().split())
    if len(cons_words) > 0:
        overlap = len(cons_words & rev_words) / len(cons_words)
        if overlap > 0.7:
            raise ValueError(
                f"review_lever is too similar to consequences "
                f"(word overlap {overlap:.0%}); write a genuine critical assessment"
            )
    return self
```
This would reject llama3.1's consequence restatements at validation time and force a retry. Caveat: the threshold needs tuning to avoid rejecting legitimate short phrases that naturally share words with consequences.

---

### I3 — Enforce minimum length on `strategic_rationale`
**File:** `identify_potential_levers.py:182–185`

Change `Optional[str]` to `str` with `min_length=50`, or keep it optional but add a `model_validator` on `DocumentDetails` that logs a warning when it's `None`. The chain-of-thought benefit requires the field to actually be populated.

---

### I4 — Align `partial_recovery` thresholds
**File:** `runner.py:131` and `runner.py:578`

Either:
- Lower the log-warning threshold to `< 2` (match the event threshold), or
- Raise the event threshold to `< 3` (match the log-warning).

The comment at runner.py:128–130 says 2-call success is normal. If that's true, both thresholds should use `< 2`. If the threshold should be 3, the comment is wrong.

---

### I5 — Remove fragile cross-reference in `review_lever` field description
**File:** `identify_potential_levers.py:129`

```python
"See system prompt section 4 for examples. "
```
This hard-codes "section 4" into the Pydantic schema. If the system prompt is restructured and examples move to a different section, this cross-reference silently becomes wrong. Replace with the neutral:
```
"See system prompt for examples. "
```
Or remove it entirely — the field description change in PR #482 is specifically designed to avoid directing models to structure; a pointer to "examples" in the schema may be redundant now that the preamble in the system prompt is plain.

---

### I6 — Add fabricated-number validator on `consequences` and `options`
**File:** `identify_potential_levers.py`, `Lever` model

The OPTIMIZE_INSTRUCTIONS block (lines 52–54) and system prompt section 5 both prohibit fabricated numbers, but haiku's fabrication rate increased from 22.6% to 30.9% after PR #482 (Insight Negative #2). A structural validator is more reliable than prose prohibition:

```python
import re
_FABRICATED_NUMBER_PATTERN = re.compile(
    r'\d+\s*%|\d+\s*percent|\$\s*\d+|\d+x\b', re.IGNORECASE
)

@field_validator('consequences', 'options', mode='after')
@classmethod
def check_no_fabricated_numbers(cls, v):
    text = v if isinstance(v, str) else ' '.join(v)
    matches = _FABRICATED_NUMBER_PATTERN.findall(text)
    if matches:
        raise ValueError(
            f"Field contains numeric claims that must not be estimated: {matches}. "
            "Use qualitative language instead."
        )
    return v
```
Caveat: this would also reject numbers drawn from the project context. To avoid false positives, the validator could accept a whitelist of numbers extracted from the `user_prompt`, but that requires passing context into the validator (not straightforward with Pydantic field validators). A simpler approach: emit a warning rather than raise, and record a metric in events.jsonl for later analysis.

---

### I7 — Fix thread-local isolation for `TrackActivity` under parallel execution
**File:** `runner.py:248–251`

The fix for B2 is to use a per-plan dispatcher or to filter events by thread ID inside `TrackActivity`, similar to how `_ThreadFilter` filters log records. A simple approach: pass the current thread's ID to `TrackActivity` and have it check `threading.current_thread().ident` before writing. This mirrors the existing `_ThreadFilter` pattern already used for log files.

---

## Trace to Insight Findings

| Insight Finding | Code Root Cause |
|----------------|----------------|
| **Negative #1 — llama3.1 consequence parroting in later calls** | S1: subsequent-call prompt shifts focus to name diversity with no review-quality guard. S3: `check_review_format` cannot detect near-verbatim consequence restatement. |
| **Negative #2 — haiku fabricated numbers increased (+8.3pp)** | No validator rejects numeric claims (I6 is the missing guard). System prompt section 5 prohibition is prose-only — insufficient for haiku. |
| **Negative #3 — haiku consequence length 2.18× baseline** | `consequences` field description requires "at least one downstream implication or trade-off" with a soft "Target length: 2–3 sentences" cap. Haiku interprets this as permission for dense, clause-heavy sentences. No hard length enforcement exists. |
| **Negative #4 — gpt-oss-20b timeout plans still wrote complete output** | B3: timed-out `run_single_plan` thread continues running after `TimeoutError`. The plan completes and writes lever files even though `events.jsonl` records it as an error. This is not a random coincidence — it is the expected behavior given the implementation. |
| **Positive #5 — no LLMChatErrors or ValidationErrors in runs 39–45** | Validator design is correct: `min_length=5` on levers, `check_option_count`, and `check_review_format` all function as designed. The `parse_options` validator handles stringified JSON arrays from some LLMs. These constraints hold. |
| **Positive #7 — OPTIMIZE_INSTRUCTIONS is accurate** | The file's OPTIMIZE_INSTRUCTIONS block (lines 27–93) correctly predicts the problem PR #482 fixes (Field-description template lock, lines 86–92). This is good documentation hygiene. |
| **Negative #1 — first-call vs later-call quality split** | B3 + S1 combined: the adaptive loop always sends independent 2-message conversations (no accumulated history). Call 2 gets a "Generate MORE levers, avoid these names" prefix that dominates weaker models' attention. No per-call quality check exists. |

---

## PR Review

### What PR #482 changes

Based on the current source and the insight description of the PR:

1. **`review_lever` field description** (identify_potential_levers.py:126–132): stripped to `"Critical review of this lever (one sentence, 20–40 words). See system prompt section 4 for examples. Do not use square brackets or placeholder text."` — no structural phrase.
2. **Section 4 preamble** (identify_potential_levers.py:247): changed to `"A one-sentence critical review. Examples:"` — plain, no copyable structure.
3. Three examples unchanged.

### Does the PR fix what it claims?

**Yes, for its stated targets.** The insight confirms:
- qwen3-30b `"X creates Y risks, leaving Z gaps"` template eliminated (0 instances across 101 levers in run 42).
- haiku `"All three options X, but none address Y"` template eliminated (~0% after vs. ~85% before).
- gpt-oss-20b `"options do not address/overlook"` pattern eliminated.

The mechanism is correct: structural phrases in field descriptions act as fill-in-the-blank templates for smaller models. Removing the phrase eliminates the template. The examples-only approach works because no single example provides a copyable sentence opener.

### Edge cases and gaps in the PR

**Gap 1 — Cross-reference in field description creates fragile coupling.**
Line 129: `"See system prompt section 4 for examples."` This is a Pydantic field description that encodes a hardcoded section number. The system prompt's section numbering is not pinned and will break this reference if sections are reordered. The cross-reference also partially re-introduces a directive ("See section 4"), which is the opposite direction of the PR's minimalization effort. The field description and system prompt should be independently self-sufficient (see I5).

**Gap 2 — Section 6 length limit is disconnected from Section 4 examples.**
System prompt Section 6 (line 262) says "Keep each `review_lever` to one sentence (20–40 words)." Section 4 contains the examples. A model reading Section 4 examples (which run ~33–37 words each) and then Section 6 will see consistency. However, models reading only Section 4 (e.g., attending to the field description cross-reference "see section 4") may not encounter the length limit. The PR leaves this cross-section gap unchanged.

**Gap 3 — PR does not address the fabricated-number regression.**
Insight Negative #2 documents that haiku's fabricated number rate rose from 22.6% to 30.9% after this PR. The PR description acknowledges this is from PR #479's "positive framing" instruction (carried unchanged). But no change in PR #482 addresses it — neither a validator, nor a stronger prohibition, nor removal of the positive-framing instruction. The regression is acknowledged but left to a future PR.

**Gap 4 — llama3.1 subsequent-call review degradation not addressed.**
The insight explicitly notes (Negative #1) that later-call levers in llama3.1 degrade to consequence restatements. The PR correctly identifies that the before-run's structural template (`"X introduces trade-offs; three options leave unaddressed [gap]"`) was also formulaic. But the replacement (minimal description + name-only subsequent-call prompt) provides insufficient guidance for llama3.1 in calls 2+. A single anti-parroting note in the subsequent-call prompt (I1) would address this without affecting call 1 or other models.

**Gap 5 — No update to `OPTIMIZE_INSTRUCTIONS` for the consequence-parroting pattern.**
The OPTIMIZE_INSTRUCTIONS block documents known failure modes. The llama3.1 consequence-parroting pattern observed in run 39 is a new failure mode (not the structural template lock, but a different kind of shallowness). The PR does not add an entry for it. Adding a "Consequence parroting" entry (alongside "Template-lock migration" and "Field-description template lock") would make this findable for future maintainers.

### Implementation correctness

The PR implementation matches its intent. The field description change and section 4 preamble change are surgically minimal. The three examples are preserved unchanged, which is correct — they are high-quality and structurally distinct (agricultural/clinical/insurance domains, three different rhetorical shapes). There is no structural duplication between them that would produce template lock.

---

## Summary

The code is well-structured overall. Field validators use structural checks rather than English-keyword matching (honoring the fragile-validator warning in OPTIMIZE_INSTRUCTIONS). The adaptive loop design is sound: independent calls with name-exclusion lists prevent duplication, and downstream deduplication handles over-generation.

**Three confirmed bugs:**

- **B1**: Warning vs. event threshold mismatch for `partial_recovery` (runner.py:131 vs 578) — monitoring inconsistency.
- **B2**: Global dispatcher contamination when `workers > 1` (runner.py:250) — `TrackActivity` handlers from concurrent plans cross-pollinate each other's event files.
- **B3**: Timed-out plan thread continues writing output after error is recorded (runner.py:558) — explains why insight run 40 shows "plan timeout after 600s" in events but complete lever files on disk.

**Three key suspects:**

- **S1**: Subsequent-call prompt has no review-quality reinforcement, likely causing llama3.1's consequence-parroting regression in calls 2+.
- **S3**: No cross-field validator to detect consequence parroting — the failure mode passes all validation silently.
- **S4**: `options` field silently accepts > 3 items; no downstream trimmer exists for options (unlike levers).

**PR #482 assessment:** The implementation is correct and achieves its stated goal. Three template locks (qwen3-30b, haiku, gpt-oss-20b) are eliminated by removing the structural phrase from the `review_lever` field description. Two regressions are acknowledged but not addressed: haiku fabricated numbers (+8.3pp) and llama3.1 review shallowing in later calls. The highest-priority follow-ups are I1 (subsequent-call anti-parroting note), I6 (fabricated-number validator), and I5 (remove fragile cross-reference "See system prompt section 4").
