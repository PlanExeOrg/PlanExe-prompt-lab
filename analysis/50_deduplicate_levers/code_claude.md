# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py` (PR #373 — the new file)
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — Silent failure on LLM error returns false "ok" with all-primary fallback
**File:** `deduplicate_levers.py:219–226`

```python
try:
    result = llm_executor.run(execute_function)
    batch_result = result["chat_response"].raw
    metadata_list.append(result.get("metadata", {}))
except PipelineStopRequested:
    raise
except Exception as e:
    logger.error(f"Batch deduplication call failed: {e}")
    # ← no raise, batch_result stays None
```

When the LLM call throws any exception other than `PipelineStopRequested`, the code logs the error and continues. `batch_result` remains `None`. The subsequent block at lines 232–241 is skipped entirely (`if batch_result is not None`), so `decisions` stays empty. Then the fallback at lines 244–252 fires for every input lever, defaulting each to score=2 (primary). All levers are kept with the justification "Not scored by LLM. Keeping as primary to avoid data loss."

The caller (`_run_deduplicate` in `runner.py`) always returns `PlanResult(status="ok", calls_succeeded=1)` — it has no visibility into whether the LLM call succeeded. The run appears as a success in `outputs.jsonl` even when deduplication never happened.

**Impact:** Undetectable silent failure. The `events.jsonl` will show `run_single_plan_complete` with no error, but the output file contains no real deduplication. Downstream steps receive a full 18-lever list instead of a deduplicated one, silently.

---

### B2 — Duplicate lever_id in model response overwrites first entry silently
**File:** `deduplicate_levers.py:233–255`

```python
for score_decision in batch_result.decisions:
    if score_decision.lever_id not in input_lever_ids:
        logger.warning(...)
        continue
    decisions.append(LeverDecision(...))   # ← no dedup check on lever_id
```

The code validates that the lever_id exists in the input set, but does not check if it has already been added to `decisions`. If the model returns the same `lever_id` twice, both entries are appended.

Then at line 255:
```python
decisions_by_id = {d.lever_id: d for d in decisions}
```
This dict comprehension silently takes the **last** entry for any duplicate lever_id. The first entry's score and justification are lost.

**Observed consequence (N5 from insight):** llama3.1 on `hong_kong_game` returned lever `32ad06c5` twice — once at position 0 (score=1, real justification) and again at position 18 (score=1, justification: "This lever is a duplicate of another lever and should not be scored separately."). The dict comprehension picked the second entry. The output file correctly shows:
```json
"deduplication_justification": "This lever is a duplicate of another lever and should not be scored separately."
```
The lever was kept (score=1 in both entries so no data loss this time), but with a nonsensical justification. Had the scores differed, the result would be unpredictable.

**Fix:** Add a `seen_decision_ids: set[str]` check inside the loop:
```python
if score_decision.lever_id in seen_decision_ids:
    logger.warning(f"Duplicate lever_id in response: '{score_decision.lever_id}'. Keeping first entry.")
    continue
seen_decision_ids.add(score_decision.lever_id)
```

---

### B3 — `_score_to_classification` return annotation includes unreachable "remove" branch
**File:** `deduplicate_levers.py:120–127`

```python
def _score_to_classification(score: int) -> Literal["primary", "secondary", "remove"]:
    """Map a Likert score to a classification label."""
    if score >= 2:
        return "primary"
    elif score >= 1:
        return "secondary"
    else:
        return "remove"
```

This function is only called at line 268, inside the block that already filtered `lever_decision.score < 1`. So `score` is always ≥ 1 when this function runs, and `"remove"` is never returned.

The annotation `Literal["primary", "secondary", "remove"]` contradicts `OutputLever.classification: Literal["primary", "secondary"]` (line 116). Any static type checker will flag the call site as potentially returning "remove" when the field only accepts "primary" or "secondary". If the filter at line 259 is ever changed (e.g., threshold moved to `< 2`), the type annotation would silently allow "remove" into `OutputLever`, causing a Pydantic `ValidationError` at runtime.

---

### B4 — No minimum-lever-count guard after deduplication
**File:** `deduplicate_levers.py:254–276`

After building `output_levers`, there is no check that a reasonable number of levers survived. When llama3.1 inverts the Likert scale on the silo plan, 17 of 18 levers receive scores of -1 or -2 and are filtered out. The function returns successfully with `len(deduplicated_levers) == 1`. The caller emits no warning. The output file is written as if the run succeeded.

Downstream steps (EnrichLevers, FocusOnVitalFewLevers) are designed to operate on 8–15 levers and select from them. Receiving 1 lever produces a degenerate downstream plan.

The insight file's C2 proposes: validate `len(deduplicated_levers) >= 5` (25% of 18 input levers) and raise or warn. Even a `logger.warning()` would surface this in the log and `events.jsonl`.

---

### B5 — `calls_succeeded` hardcoded to 1 regardless of actual LLM success
**File:** `runner.py:151–156`

```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,  # filled by caller
    calls_succeeded=1,  # single batch call
)
```

The comment says "single batch call" — but this is misleading. If the LLM call failed (B1), `calls_succeeded=1` is still returned. The caller has no way to distinguish "LLM succeeded, 1 call" from "LLM failed, fallback used, 0 actual calls". In contrast, `_run_levers` at line 120 computes `actual_calls = len(result.responses)` dynamically.

---

## Suspect Patterns

### S1 — `consequences` field description names banned English phrases
**File:** `identify_potential_levers.py:116–119`

```python
consequences: str = Field(
    description=(
        ...
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        "those belong exclusively in review_lever. "
```

`OPTIMIZE_INSTRUCTIONS` (lines 61–82) explicitly warns:
> Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases.

This `Field(description=...)` text is sent to the LLM as part of the JSON schema and is visible to the model. It names "Controls ... vs." and "Weakness:" as banned phrases, which per OPTIMIZE_INSTRUCTIONS creates a template-lock risk: small models may start copying these exact substrings into `consequences`. This is a direct contradiction between the documented guidance and the implementation.

The same text appears verbatim in `LeverCleaned.consequences` (lines 209–214), which is a downstream-only schema and never sent to an LLM — so it's harmless there, but creates confusion about which schema is LLM-facing.

---

### S2 — `partial_recovery` warning threshold fires on normal 2-call runs
**File:** `runner.py:125–127` and `runner.py:546–552`

```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

The comment at lines 121–124 says: "A 2-call success is normal for models that produce 8+ levers per call." The adaptive loop in `identify_potential_levers.py` targets 15 levers with a 5-call budget. A model generating 8 levers per call hits 15 in exactly 2 calls and stops — a clean success. Yet `calls_succeeded=2 < 3` triggers the warning and emits a `partial_recovery` event.

This creates false positives in `events.jsonl` for healthy runs with high-output models. Analysis pipelines that count `partial_recovery` events to detect LLM failures will over-count.

---

### S3 — `execute_function` closure captures `chat_message_list` by reference
**File:** `deduplicate_levers.py:211–214`

```python
def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchDeduplicationResult)
    chat_response = sllm.chat(chat_message_list)
    return {"chat_response": chat_response, "metadata": dict(llm.metadata)}
```

`chat_message_list` is a list defined at line 206. Closures in Python capture variables by reference, not by value. In the single-call batch approach, `execute_function` is only called once via `llm_executor.run()`, so mutation is not a practical concern here. However, if `llm_executor.run()` internally retries with fallback LLMs, `chat_message_list` is shared across all retry attempts — which is correct (no chat history accumulation to worry about). This is safe as-is but worth noting if the code evolves to append assistant turns.

This is a contrast to the multi-call loop in `identify_potential_levers.py` which correctly captures `messages_snapshot = list(call_messages)` (line 317) to avoid mutation issues. The same defensive copy could be applied in `deduplicate_levers.py` for consistency.

---

## Improvement Opportunities

### I1 — Add scale-inversion sanity check
**File:** `deduplicate_levers.py` — after line 241 (after building `decisions`)

If more than 75% of scored levers receive score ≤ -1, the model likely inverted the Likert scale. Add a check:
```python
negative_count = sum(1 for d in decisions if d.score <= -1)
if len(decisions) > 0 and negative_count / len(decisions) > 0.75:
    logger.warning(
        f"Possible Likert scale inversion: {negative_count}/{len(decisions)} levers scored <= -1. "
        f"Check justifications for 'highly relevant' text paired with negative scores."
    )
```
This would have caught the llama3.1 silo run (17/18 scores ≤ -1 = 94%) and gta_game run before the catastrophic 1-lever output was written.

---

### I2 — Add minimum-lever-count guard with warning
**File:** `deduplicate_levers.py` — after line 276 (`logger.info(...)`)

```python
min_expected = max(3, len(input_levers) // 4)  # 25% floor
if len(output_levers) < min_expected:
    logger.warning(
        f"Only {len(output_levers)} levers survived deduplication "
        f"(expected at least {min_expected} from {len(input_levers)} input). "
        f"Possible scale inversion or over-aggressive scoring."
    )
```
This catches the llama3.1 scale-inversion case (1 lever from 18) and surfaces it without halting the pipeline.

---

### I3 — Emit LLM failure as a structured event, not just a log message
**File:** `deduplicate_levers.py:225–226`

The exception handler currently only calls `logger.error(...)`. The `runner.py` infrastructure has `_emit_event()` for structured event logging. A failed LLM call in `deduplicate_levers` is invisible in `events.jsonl`, making it impossible to distinguish "succeeded, kept all levers" from "LLM failed, silently kept all levers via fallback."

Since `deduplicate_levers.py` doesn't have access to `events_path`, the fix belongs in `_run_deduplicate` in `runner.py`: expose the LLM call success/failure from `DeduplicateLevers.execute()` (e.g., via a `calls_succeeded: int` field on the return object), then emit a `partial_recovery` event when `calls_succeeded == 0`.

---

### I4 — `OPTIMIZE_INSTRUCTIONS` in `deduplicate_levers.py` should document Likert scale-inversion risk
**File:** `deduplicate_levers.py:30–75`

The `OPTIMIZE_INSTRUCTIONS` block at lines 54–74 documents "Blanket-primary", "Over-inclusion", "Hierarchy-direction errors", and "Calibration capping" as known problems. It does not document the scale-inversion failure (llama3.1 scoring -2 with "highly relevant" justifications). This failure mode is now confirmed empirically across at least 2 plans and should be added to `OPTIMIZE_INSTRUCTIONS` so future prompt engineers know to guard against it.

---

### I5 — Conceptual mismatch between step name and prompt intent not documented
**File:** `deduplicate_levers.py` module docstring (lines 1–16)

The module docstring says "deduplicates the list using a single-call Likert scoring approach" and the scoring scale is described. But neither the docstring nor `OPTIMIZE_INSTRUCTIONS` acknowledges that **Likert relevance scoring ≠ deduplication**. The step is called `DeduplicateLevers` and lives in `deduplicate_levers.py`, but the prompt asks "How relevant is this lever to this specific project plan?" — not "Is this lever redundant with another lever?"

This conceptual gap should be documented: the current prompt eliminates levers that are irrelevant to the plan, but does not enforce removal of overlapping levers that are individually relevant. A lever can score 1 ("somewhat relevant") while being fully redundant with another lever — and the code keeps it. The `OPTIMIZE_INSTRUCTIONS` mentions "Over-inclusion" but doesn't name the root cause.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|--------------------|--------------------|
| **N1 — llama3.1 inverts Likert scale** (silo, gta_game: 17/18 removed) | No scale-inversion detection (missing I1). B4: no minimum-lever guard. Code happily produces 1-lever output. |
| **N2 — capable models keep all 18 levers** (gpt-oss-20b: 0 removed) | I5: conceptual mismatch. The prompt asks "relevance" not "redundancy." Overlapping levers score 1 and are kept. No code-level fix possible without redesigning the prompt. |
| **N3 — relevance ≠ deduplication** (architectural flaw) | I5: the `OPTIMIZE_INSTRUCTIONS` does not acknowledge this mismatch. The scoring schema (`LeverScoreDecision`) has no field for "redundancy with lever X." |
| **N4 — gpt-oss-20b ignores calibration guidance** | Prompt-only issue. The system prompt says "Expect 25-50% of levers to score 0 or below. If you score everything 1 or 2, reconsider." This is non-binding. No code-level enforcement. |
| **N5 — llama3.1 duplicate lever_id in hong_kong_game response** | B2: no duplicate-lever_id check in the `decisions` loop. The second (misleading) entry wins silently. |
| **P1 — 100% structural success rate** | The `BatchDeduplicationResult` Pydantic schema is well-designed and parseable by all models. The `Literal[-2, -1, 0, 1, 2]` type on `score` constrains the model effectively for capable models. |
| **P4 — score-to-classification mapping preserves triage dimension** | `_score_to_classification` correctly maps 2→primary and 1→secondary (B3 notes the "remove" branch is dead code but doesn't affect correctness for the kept levers). |

---

## PR Review

### Does the implementation match the intent?

PR #373's stated goal is to replace 18 sequential per-lever LLM calls with a single batch call. The implementation achieves this: `deduplicate_levers.py` makes exactly one call via `sllm.chat(chat_message_list)` and processes all levers simultaneously. The speed goal (18× fewer API calls) is met.

### Bugs specific to the PR implementation

**The batch approach uses the same Pydantic schema for all 18 levers simultaneously.** `BatchDeduplicationResult.decisions` has no `max_length` constraint. When llama3.1 returns 19 decisions for 18 levers (N5), the schema accepts all 19 entries. The duplicate is filtered by `input_lever_ids` check... except it passes that check because the duplicate lever_id IS a valid input id. So the duplicate survives into `decisions` (B2).

**The fallback on LLM failure is too aggressive.** If the batch call fails, all levers default to score=2 (primary) with the justification "Not scored by LLM. Keeping as primary to avoid data loss." This is a reasonable safe fallback, but it's invisible to the caller (B1, B5). The prior 18-call approach could partially succeed: if 15 of 18 calls succeeded, 15 levers were scored. The batch approach is binary: 1 call either succeeds or fails entirely.

**The PR does not include a `save_clean` call in `runner.py`.** `_run_levers` (line 117–118) writes both `002-9-potential_levers_raw.json` and `002-10-potential_levers.json` (raw + clean). `_run_deduplicate` (line 148–149) only writes `002-11-deduplicated_levers_raw.json`. The `save_clean()` method exists on `DeduplicateLevers` (line 303) but is never called in the self-improve runner. If any downstream step reads a clean (non-raw) lever file for the deduplicated list, it will fail to find it.

**The `DEDUPLICATE_SYSTEM_PROMPT` does not mention that levers should be compared against each other for redundancy.** It says "When two levers cover similar ground, score the more general one higher" — but the primary question the model is asked is "How relevant is this lever to this specific project plan?" This frames the task as relevance scoring, not deduplication. Models correctly answer the relevance question and return high scores for all marginally relevant levers. The PR's implementation cannot produce good deduplication results because the prompt does not ask for deduplication (N2, N3, I5).

### Edge cases the PR misses

1. **Empty `decisions` after successful LLM call.** If the model returns `BatchDeduplicationResult(decisions=[])`, all levers hit the fallback at lines 244–252 and default to score=2. No warning is emitted.

2. **All levers score exactly 0.** The threshold is `score < 1` to remove. All 18 levers scoring exactly 0 would all be removed, producing an empty `deduplicated_levers`. The code handles this without error — `output_levers` is `[]` — but no minimum-lever check fires (B4).

3. **Model returns lever_ids with different UUIDs but matching lever names.** The code only checks `lever_id` membership in `input_lever_ids`. If the model fabricates a new UUID that's not in the input, the entry is logged as "unknown lever_id" and skipped. The associated lever then falls into the "not scored" fallback and defaults to primary. This is correct behavior but worth noting.

---

## Summary

PR #373 achieves its stated performance goal (18→1 LLM call) but introduces or fails to guard against several code-level problems:

**Confirmed bugs (this PR):**
- **B1**: Silent LLM failure propagates as `status="ok"` with all-primary fallback; caller cannot distinguish success from failure.
- **B2**: Duplicate `lever_id` in model response causes first entry to be silently overwritten by the last; wrong justification appears in output (confirmed in run 57 hong_kong_game).
- **B3**: `_score_to_classification` return type annotation includes unreachable `"remove"` that contradicts `OutputLever.classification`, creating a latent type-safety issue.
- **B4**: No minimum-lever-count guard; llama3.1 scale inversion producing 1/18 levers is returned as a successful run.
- **B5**: `calls_succeeded` hardcoded to 1 in `runner.py`; cannot distinguish actual LLM success from fallback.

**Suspect patterns (cross-cutting):**
- **S1**: `Lever.consequences` field description names banned English phrases, contradicting `OPTIMIZE_INSTRUCTIONS`' guidance against naming banned phrases.
- **S2**: `partial_recovery` threshold of `< 3` fires false positives for successful 2-call runs.

**Root cause of the quality regression documented in insight_claude.md:**
The Likert prompt asks "How relevant is this lever to this specific plan?" rather than "Is this lever redundant with another lever?" These are different questions. Relevance scoring cannot produce good deduplication (N2, N3). This is an architectural/prompt design issue, not a code bug, but it is the primary cause of the deduplication failure observed in runs 57–63. Code changes (B1–B5) can improve robustness but cannot fix the underlying conceptual mismatch without redesigning the prompt schema.
