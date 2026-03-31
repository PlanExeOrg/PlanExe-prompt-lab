# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: PlanExeOrg/PlanExe#469 ("Reduce word counts, add anti-echoing, and use verbatim id guidance")

---

## Bugs Found

### B1 — `errors.append` for `unknown_lever_id` conflates noise with real failures

**File:** `enrich_potential_levers.py:284–285`

```python
logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

When an LLM over-generates a characterization for a fabricated `lever_id` (e.g. `"dummy_override"`, hex-format UUIDs haiku invented in run 68), the characterization is correctly discarded — `enriched_levers_map` only maps real IDs, so the `if char.lever_id in enriched_levers_map` branch is never taken. All real levers are enriched correctly.

The bug is appending this to `errors`. The `errors` list is written to the output file (`002-12-enriched_levers_raw.json`) and read by the analysis pipeline. The list is meant to signal real processing failures (`batch_retry`, `batch_skipped`, `validation_error`, `incomplete`). Appending `unknown_lever_id` inflates the error count and causes the analysis to treat benign over-generation as a quality signal. This is why the insight file shows haiku with "5 errors" before and "2 errors" after — those are all noise entries.

**Fix:** Remove `errors.append(...)` on line 285; keep `logger.warning(...)` on line 284. The warning log is sufficient for debugging.

---

### B2 — `partial_recovery` event fires for normal 2-call successful runs

**File:** `runner.py:131–133` and `runner.py:577–584`

```python
# runner.py:131
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")

# runner.py:577–584
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The comment on line 127–130 explicitly acknowledges: "A 2-call success is normal for models that produce 8+ levers per call." Yet the threshold is `< 3`, which fires for every clean 2-call run. `calls_succeeded` is `len(result.responses)` — it counts successful responses, not failed ones. A model that generates 8 levers per call reaches the 15-lever target in 2 clean calls, triggering a spurious `partial_recovery` event. The event name implies error recovery happened when none did.

**Fix:** Track whether any call actually failed (the `except` branch in the adaptive loop already logs `call_index` when it retries). Or lower the threshold to `< 2` so only single-call runs trigger the event.

---

## Suspect Patterns

### S1 — `lever_id` field description is ambiguous about where to find the ID

**File:** `enrich_potential_levers.py:138`

```python
lever_id: str = Field(description="The id of the lever — copy it verbatim from the prompt, without XML tags")
```

The phrase "from the prompt" is imprecise. The user prompt contains `<lever>uuid-here</lever>` — the tags are part of the prompt text. A weak model could read "copy it verbatim from the prompt" as an instruction to copy the full `<lever>uuid-here</lever>` string and then attempt to strip tags itself, or copy the whole tag string without stripping. The system prompt is clearer ("copy the id verbatim from inside the tags — strip the XML tags but do not alter the id itself"), but when a model processes the Pydantic field description first (as it does in structured-output mode), the ambiguous field description may prime the wrong behavior before the system prompt can correct it.

The `"dummy_override"` entry in run 89 is consistent with haiku misreading this guidance as: "invent a placeholder to put in the lever_id field when you're not sure." There is no negative constraint anywhere saying "do not use placeholder text."

### S2 — `lever_id` guidance is duplicated across field description and system prompt with inconsistent framing

**File:** `enrich_potential_levers.py:138` and `enrich_potential_levers.py:170–171`

The field description says: `"copy it verbatim from the prompt, without XML tags"`
The system prompt says: `"copy the id verbatim from inside the tags — strip the XML tags but do not alter the id itself"`

Both instructions say the same thing but with different wording. Two locations means two places to update when the guidance changes. More importantly, "from the prompt" vs. "from inside the tags" are not the same instruction — one is vague, the other is precise. If the field description is changed to match the system prompt's precision, they would be redundant but unambiguous.

### S3 — `execute_function` closure captures loop variable without a snapshot

**File:** `enrich_potential_levers.py:261–268`

```python
chat_message_list = [system_message, ChatMessage(role=MessageRole.USER, content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)  # captures by reference
```

In `identify_potential_levers.py:317–321`, the developer explicitly added `messages_snapshot = list(call_messages)` and used `messages_snapshot` inside the closure. This was presumably added to guard against late-binding closure capture. `enrich_potential_levers.py` skips this snapshot. In current synchronous execution, `llm_executor.run()` calls `execute_function` before the loop variable is reassigned, so there is no bug — but the inconsistency between the two files suggests the snapshot was added in one place for a reason that may apply equally here.

### S4 — `enriched_levers_map` covers all levers, so a cross-batch lever_id match silently updates the wrong batch's lever

**File:** `enrich_potential_levers.py:219, 277–282`

```python
enriched_levers_map = {lever.lever_id: lever.model_dump() for lever in levers_to_characterize}
# ...
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update(...)
```

The map contains every lever across all batches. If the LLM (processing batch 1 of levers A, B, C) returns a characterization for lever D from batch 2, that characterization is accepted and stored. Batch 2 then overwrites it. The net result is correct, but the batch 1 call wasted tokens enriching lever D, and the batch context for batch 1 may produce lower-quality enrichment for lever D than batch 2's context would. A stricter check against `{lever.lever_id for lever in batch}` would catch this.

---

## Improvement Opportunities

### I1 — Remove `errors.append` for `unknown_lever_id` (see B1)

This is the highest-priority fix. Remove line 285 in `enrich_potential_levers.py`. The `logger.warning` on line 284 is sufficient to track these events for debugging. This will immediately reduce the noise in the analysis pipeline and make haiku's real error rate visible (it's 0 for most plans, not "2" or "5").

### I2 — Add placeholder guard to `lever_id` guidance

The `"dummy_override"` pattern is a new failure mode introduced by the verbatim guidance. Add a narrow negative constraint directly in the system prompt:

> "The id must be an exact copy of the string inside the `<lever>` tags — do not substitute placeholder text such as 'dummy', 'test', 'override', or any other invented string."

Unlike general prohibitions (which OPTIMIZE_INSTRUCTIONS warns against), this is narrow enough to be specific without teaching models new phrasings to copy.

### I3 — Update `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` to document the semantic-placeholder pattern

**File:** `enrich_potential_levers.py:28–107`

The current OPTIMIZE_INSTRUCTIONS documents UUID leakage and the shift to XML tags (PR #466 and PR #469 history), but does not mention the new `"dummy_override"` failure mode: a model generating a semantic placeholder string in the `lever_id` field instead of a UUID-format fabrication. Document this as a known problem so future prompt engineers know it has been observed and what caused it (verbatim guidance interpreted as permission to invent).

### I4 — Calibrate `partial_recovery` event threshold in `runner.py`

**File:** `runner.py:131, 579`

Change the condition from `calls_succeeded < 3` to only fire when at least one call in the adaptive loop actually failed (i.e., hit the `except` branch). The simplest approach: track `calls_failed` in `IdentifyPotentialLevers.execute()` and include it in `PlanResult`. Emit `partial_recovery` only when `calls_failed > 0`.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| N1 — haiku `"dummy_override"` in run 89 gta_game | S1/S2: `lever_id` field description says "from the prompt" (ambiguous) and has no placeholder guard. The "verbatim" instruction was interpreted as permission to substitute. |
| P3 — haiku error count dropped from 5 to 2 but still nonzero | B1: `errors.append` for `unknown_lever_id` records noise as errors. The "2" remaining errors are still noise — both real levers are enriched correctly. |
| P1 — gpt-oss-20b no longer times out | Correctly traced in insight to shorter prompts generating faster. No code bug here. |
| P2 — Field lengths reduced across all models | Word count changes in field descriptions and system prompt directly control LLM output. Working as intended. |
| Q5 — Was B2 (suppress `errors.append`) included in PR #469? | No. Line 285 in `enrich_potential_levers.py` still appends `unknown_lever_id` to `errors`. B2 from analysis 65 was not part of PR #469. |

---

## PR Review

### What the PR changes (from current code in `enrich_potential_levers.py`)

**`LeverCharacterization` field descriptions:**
- `lever_id`: changed from (prior wording) to `"The id of the lever — copy it verbatim from the prompt, without XML tags"`
- `description`: reduced from 80–100 to 50–70 words; added "Add new insight beyond what consequences and review already state."
- `synergy_text` / `conflict_text`: reduced from 40–60 to 20–40 words

**`ENRICH_LEVERS_SYSTEM_PROMPT`:**
- Added: "For `lever_id` in your response, copy the id verbatim from inside the tags — strip the XML tags but do not alter the id itself."
- Updated word counts throughout output requirements
- Added anti-echoing: "Add new insight beyond what the consequences and review fields already state."

### Does the implementation match intent?

**Verbosity reduction — YES.** The word count targets in field descriptions and system prompt now match (50–70 / 20–40). Both the Pydantic schema description and the system prompt state the same targets. P1 (gpt-oss-20b timeout resolved) and P2 (all models now within or below baseline range) confirm this works.

**Anti-echoing — PARTIALLY.** The instruction "Add new insight beyond what consequences and review already state" is present in both the field description and the system prompt, which is good for redundancy. The qualitative improvement is visible in haiku (P5). However, there is no structural mechanism (e.g. a validator) to detect echoing — it relies entirely on models following the prompt.

**Verbatim id guidance — PARTIALLY.** The `lever_id` guidance successfully prevents the hyphen-stripping regression from PR #468 (P4 confirmed). But the new `"dummy_override"` failure (N1) shows the guidance introduced a new pattern: haiku generating a semantic placeholder instead of a UUID-format fabrication. This is a side effect of replacing "hexadecimal UUID" with the vaguer "copy it verbatim from the prompt."

### Gaps and edge cases the PR misses

1. **No placeholder guard.** The verbatim guidance doesn't say "the id must come from the `<lever>` tags in the current batch — do not invent strings." The `"dummy_override"` error confirms this gap.

2. **B2 from analysis 65 not addressed.** `errors.append({"type": "unknown_lever_id", ...})` at line 285 was flagged as noise in analysis 65 and recommended for removal. PR #469 did not include this fix. The haiku error count comparison in the insight (5 → 2) is therefore measuring noise reduction indirectly, not a real improvement.

3. **Field description and system prompt wording are not identical.** "Copy it verbatim from the prompt, without XML tags" (field) vs. "copy the id verbatim from inside the tags — strip the XML tags but do not alter the id itself" (system prompt). These should say the same thing in both locations.

4. **Anti-echoing instruction wording differs between field description and system prompt.** Field: "Add new insight beyond what consequences and review already state." System prompt: "Add new insight beyond what the consequences and review fields already state." One says "consequences and review," the other "the consequences and review fields." Minor, but both locations must be updated together when the instruction changes.

### Bugs introduced by the PR

The PR's `lever_id` guidance change (avoiding "uuid" and "hexadecimal") successfully solved hyphen-stripping but introduced the `"dummy_override"` failure mode (N1). This is not a code bug — it is a prompt-engineering trade-off. The fix (I2) is narrow and specific enough to address without reintroducing the previous regression.

---

## Summary

**Confirmed bugs (actionable):**
- **B1** (`enrich_potential_levers.py:285`): `errors.append` for `unknown_lever_id` pollutes the error list with over-generation noise; remove the append, keep the warning log.
- **B2** (`runner.py:131, 579`): `partial_recovery` event fires for normal 2-call runs; miscalibrated threshold.

**Suspect patterns (monitor):**
- **S1/S2**: `lever_id` field description is ambiguous ("from the prompt") and inconsistent with the system prompt's more precise wording; likely cause of the `"dummy_override"` failure in haiku.
- **S3**: Missing `messages_snapshot` pattern in `enrich_potential_levers.py` (present in `identify_potential_levers.py`).
- **S4**: Cross-batch `lever_id` match accepted silently.

**Highest-priority improvements:**
- **I1** (= B1 fix): Remove `errors.append` for `unknown_lever_id` — one-line change, immediate signal quality improvement.
- **I2**: Add placeholder guard to `lever_id` guidance to prevent the `"dummy_override"` pattern.
- **I3**: Document the semantic-placeholder pattern in `OPTIMIZE_INSTRUCTIONS`.

PR #469 delivers its stated goals (verbosity reduction, anti-echoing, hyphen-stripping fix) and is an improvement over PR #466. The two gaps that matter most are B1 (unfixed from analysis 65) and the S1/S2 ambiguity in `lever_id` guidance that introduced a new failure mode.
