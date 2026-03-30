# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #457 "Strip UUIDs from full lever context string in enrich step"

---

## Bugs Found

### B1 — System prompt provides no UUID prohibition for free-text fields
**File:** `enrich_potential_levers.py:159–172` (`ENRICH_LEVERS_SYSTEM_PROMPT`)

The system prompt instructs models to "Name the specific levers it enhances/constrains" but says nothing about *how* to name them — by name, by ID, or by both. The field descriptions in `LeverCharacterization` say "Name the specific levers" (lines 139, 143) but also don't prohibit UUID use. The per-batch prompt (lines 233–240) then explicitly surfaces `Lever ID: {uuid}` for every lever in the batch:

```python
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    ...
])
```

This is a prompt contract violation: the OPTIMIZE_INSTRUCTIONS at lines 88–92 states "Models should reference levers by name only in free-text fields," but neither the system prompt nor the field descriptions encode that constraint. Models see `Lever ID:` in the input and have no instruction telling them not to reproduce it in output. The absence of an explicit prohibition is the root cause of all UUID contamination in synergy/conflict text.

---

### B2 — `errors` field type annotation mismatches its default
**File:** `enrich_potential_levers.py:181`

```python
errors: List[Dict[str, Any]] = None
```

The declared type is `List[Dict[str, Any]]` but the default is `None`. The `__post_init__` guard (lines 182–183) handles this at runtime, but the annotation is wrong — it should be `Optional[List[Dict[str, Any]]] = None`. Type checkers (mypy, pyright) will flag every callsite that passes `errors=None` or receives the field before `__post_init__` runs.

---

### B3 — No count validation on `BatchCharacterizationResult.characterizations`
**File:** `enrich_potential_levers.py:147–149`

```python
class BatchCharacterizationResult(BaseModel):
    characterizations: List[LeverCharacterization] = Field(
        description="A list containing the full characterization for each requested lever in the batch."
    )
```

There is no `max_length` constraint and no code-level check that the model returned exactly `len(batch)` characterizations. When the model returns more entries than requested (as haiku does in run 4/33), the extras are silently logged as `unknown_lever_id` errors. The real levers are still enriched, but the `errors` list grows with noise, and there is no fast-fail path.

Separately, when the model returns *fewer* entries than requested (e.g. silently drops a lever), the missing levers are only detected at the final assembly loop (lines 318–320) where they become `incomplete` errors. There is no per-batch count check after a successful parse.

---

### B4 — `execute_function` closure captures `chat_message_list` by reference in a loop
**File:** `enrich_potential_levers.py:254–259`

```python
while pending_batches:
    ...
    chat_message_list = [system_message, ChatMessage(...)]

    def execute_function(llm: LLM) -> dict:
        ...
        chat_response = sllm.chat(chat_message_list)  # closes over the loop variable
```

`execute_function` is redefined each iteration and closes over the name `chat_message_list`, not the value. Because `llm_executor.run()` is currently synchronous and blocking, the correct value is always in scope at call time. However, if `LLMExecutor.run` is ever refactored to retry asynchronously (e.g., a deferred callback, a background thread, or an async variant), the closure will silently capture the *next* iteration's `chat_message_list`. The identical pattern appears in `identify_potential_levers.py:319–327`. The safe fix is to capture by value: `def execute_function(llm, _msgs=chat_message_list): ...`.

---

### B5 — `_run_levers` warns on `calls_succeeded < 3` even for fast-converging models
**File:** `runner.py:131–133`

```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

The comment directly above this block (lines 127–130) says "A 2-call success is normal for models that produce 8+ levers per call." A model that returns 8 levers on call 1 and 8 on call 2 correctly satisfies `min_levers=15` and stops — but this block fires a false `partial_recovery` warning. The same false event is emitted by `_run_plan_task` at lines 577–583. The warning threshold should be `< 2` (one call succeeded, implying only one batch completed rather than two), or the check should use `len(generated_lever_names) < min_levers` as the signal.

---

## Suspect Patterns

### S1 — Global dispatcher shared across parallel plan workers
**File:** `runner.py:248–251`, `runner.py:280–282`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path` uses thread-local storage (each worker thread gets its own path). But `dispatcher` is a global singleton. When `workers > 1`, every plan's `TrackActivity` handler is added to the same dispatcher simultaneously. All handlers receive all LLM events from all concurrent plans. Whether this causes cross-plan contamination in `track_activity.jsonl` depends on whether `TrackActivity` filters by thread. If it doesn't, each plan's log collects events from other plans. The `_file_lock` makes the add/remove setup *atomic* but does not isolate events at runtime. This is worth confirming in `TrackActivity`.

---

### S2 — `__main__` test block in `enrich_potential_levers.py` uses different JSON shape than `runner.py`
**File:** `enrich_potential_levers.py:363–364` vs `runner.py:172–173`

`runner.py` loads the deduplicated levers file and extracts the nested key:
```python
json_dict = json.load(f)
lever_item_list = json_dict["deduplicated_levers"]
```

The `__main__` block in `enrich_potential_levers.py` loads the file and passes the whole object:
```python
input_levers = json.load(f)
result = EnrichPotentialLevers.execute(..., raw_levers_list=input_levers)
```

If the test data file produced by `deduplicate_levers.py` has the `{"deduplicated_levers": [...]}` top-level structure (which it does, per runner.py line 173), the `__main__` block will fail silently or produce a Pydantic validation error because `InputLever(**lever)` would receive dict keys like `"deduplicated_levers"` as a field instead of a list of lever dicts. This makes the standalone test runner broken for real deduplicated output.

---

### S3 — `Lever.consequences` field description contains English-only prohibition text
**File:** `identify_potential_levers.py:114–120`

```python
consequences: str = Field(
    description=(
        ...
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        ...
    )
)
```

The `OPTIMIZE_INSTRUCTIONS` at lines 61–68 explicitly warns: "Hard-coded English substring checks (e.g. `'Controls ' not in response_str`) will reject perfectly valid levers whenever the model responds in the prompt's language." That warning covers validators, but the same problem applies to field *descriptions* sent to the LLM. When the LLM responds in Japanese, Chinese, or Arabic (as the OPTIMIZE_INSTRUCTIONS says it may), the English phrase "Do NOT include 'Controls ... vs.'" is meaningless instruction noise that could confuse function-calling models attempting to follow it. The field description is part of the structured-output schema passed to the LLM; it acts as a prompt instruction and must be language-agnostic.

---

## Improvement Opportunities

### I1 — Add explicit UUID prohibition to `ENRICH_LEVERS_SYSTEM_PROMPT`
**File:** `enrich_potential_levers.py:159–172`

Add a direct constraint under Output Requirements:
> "Important: In `synergy_text` and `conflict_text`, refer to other levers by lever **name only**. Do not include `lever_id` UUID values or any ID strings (e.g. `6415a78e-...`) in these free-text fields."

This is insight C1. Expected impact: eliminates same-batch UUID copying for models that respect instruction-level constraints (all models tested except llama3.1 in adversarial cases).

---

### I2 — Post-process `synergy_text` and `conflict_text` to strip UUID patterns
**File:** `enrich_potential_levers.py:267–276` (after the characterization merge loop)

After writing `description`, `synergy_text`, `conflict_text` into `enriched_levers_map`, apply a regex strip:
```python
import re
_UUID_PATTERN = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
```
Strip from `synergy_text` and `conflict_text` before final assembly. This is insight C2. Defensive, model-agnostic, works regardless of prompt compliance.

---

### I3 — Instruct the LLM to return exactly N characterizations per batch
**File:** `enrich_potential_levers.py:242–250` (user prompt construction)

The user prompt says "Provide the ... for the following N levers" but doesn't say "return exactly N characterizations — no more, no fewer." After PR #457 removes UUIDs from the full context, haiku generates extra characterizations with fabricated IDs. Adding "Return exactly {len(batch)} characterizations, one per lever in this batch. Do not invent additional levers." would constrain this behavior for function-calling models.

---

### I4 — `LeverCharacterization.lever_id` field description should emphasize exact match
**File:** `enrich_potential_levers.py:134`

```python
lever_id: str = Field(description="The uuid of the lever")
```

The description is minimal. Strengthening it to "The exact lever_id UUID from the 'Lever ID:' field in the input — copy it verbatim, do not modify or invent" would reduce haiku's fabricated-ID regression and llama3.1's UUID corruption.

---

### I5 — `DocumentDetails.levers` has `min_length=5` but no `max_length`
**File:** `identify_potential_levers.py:190–193`

```python
levers: list[Lever] = Field(
    min_length=5,
    description="Propose 5 to 7 levers."
)
```

The system prompt says "5 to 7 levers" and this is enforced on the low end. The high end has no constraint. The comment above correctly documents that over-generation is intentional, but if a model returns 20 levers in one call, the adaptive loop may exit early at call 1 with 20 raw levers instead of the intended ~15 from 2–3 balanced calls. This doesn't break anything (deduplication handles extras), but it reduces naming diversity since all levers come from one generation context.

---

### I6 — `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` is stale after PR #457
**File:** `enrich_potential_levers.py:88–92`

The current text says:
> "The full_lever_context_str includes lever_id UUIDs, causing models to copy UUIDs..."

After PR #457, `full_lever_context_str` no longer includes UUIDs. The OPTIMIZE_INSTRUCTIONS entry should be updated to reflect:
1. The fix has been applied for the full context list.
2. The *per-batch* prompt (`lever_details_for_prompt`) still exposes `Lever ID:` — this is now the active UUID vector for same-batch levers.
3. Haiku's new behavior: generates extra fabricated-ID characterizations when the full context lacks UUID anchors.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| **N2** — llama3.1 still has 7 UUID occurrences after PR (same-batch levers) | B1: no UUID prohibition in `ENRICH_LEVERS_SYSTEM_PROMPT`; per-batch prompt at line 233 still surfaces `Lever ID: {uuid}` |
| **N3** — haiku generates 7 new `unknown_lever_id` errors with fabricated IDs | B3: `BatchCharacterizationResult.characterizations` has no max count; I3: no "exactly N" instruction; removing UUIDs from full context (PR #457) removed the grounding anchor haiku used |
| **N4** — fabricated percentages echo from `consequences` into descriptions | Pre-existing: the `consequences` field in `InputLever` carries fabricated % strings from step 1; nothing strips or flags them before passing to the LLM |
| **P3** — llama3.1 phantom ID errors eliminated | PR #457 correctly removes the UUID source from `full_lever_context_str`; cross-batch ID copying ends |
| **P1/P2** — gemini/gpt-oss-20b UUID contamination eliminated | Same as P3 — for these models the cross-batch copy was the only source |
| S1 (insight) — shared dispatcher in parallel runs | S1 above: global dispatcher adds all handlers simultaneously |
| S2 (this review) — `__main__` test block JSON mismatch | S2 above — broken standalone test |
| B5 (this review) — false `partial_recovery` warnings | B5 above — threshold fires for successful 2-call runs |

---

## PR Review

### Change
PR #457 modifies line 209 of `enrich_potential_levers.py`:
```python
# Before
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])

# After
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

### Does the implementation match the intent?

**Yes, for the stated goal.** Removing UUIDs from `full_lever_context_str` correctly eliminates cross-batch UUID copying. The change is minimal, isolated, and has no side effects on the batch processing logic, retry logic, or output schema.

### Gaps in the PR

**Gap 1 — Same-batch UUID copying is not addressed.**
`lever_details_for_prompt` (lines 233–240) still includes `Lever ID: {uuid}` for every lever in the current batch. Any model that tends to reproduce contextual ID strings (llama3.1, and to a lesser degree haiku) will continue to copy UUIDs from this section into `synergy_text` and `conflict_text` for same-batch cross-references. This explains why llama3.1 went from 54 → 15 UUID occurrences rather than 54 → 0. The PR is intentionally incomplete on this point (the ID is needed for structured output routing), but the OPTIMIZE_INSTRUCTIONS and system prompt should explicitly flag the remaining vector.

**Gap 2 — No compensating prompt instruction added.**
The PR removes a UUID source without adding an instruction telling models not to use UUIDs in synergy/conflict text. This is the most direct fix for both Gap 1 (B1 above) and the haiku regression (B3/I3 above). A one-sentence addition to `ENRICH_LEVERS_SYSTEM_PROMPT` would be the natural companion to the line change.

**Gap 3 — Haiku regression introduced without mitigation.**
Haiku (a function-calling model) used the full context's UUIDs as grounding to produce the correct number of characterizations. After removal, haiku generates 7 extra `LeverCharacterization` objects with fabricated IDs across 3 plans. The real levers are all correctly enriched (35/35), so functional correctness is unaffected. But the `errors` list now has 7 spurious entries. Adding "Return exactly {len(batch)} characterizations" to the user prompt (I3) is the targeted fix.

**Gap 4 — `OPTIMIZE_INSTRUCTIONS` not updated.**
The OPTIMIZE_INSTRUCTIONS block (lines 88–92) describes the UUID problem in the present tense, but the PR has partially fixed it. The entry should be updated to document (a) the fix applied, (b) the remaining per-batch vector, and (c) haiku's new fabrication behavior.

### Are there code correctness issues introduced by the PR?

No. The change is a one-line list comprehension edit. It cannot introduce crashes, incorrect data, or schema violations. The `full_lever_context_str` is only used in the `user_prompt` string (line 244), which is purely informational context for the LLM. Removing the UUID from that string is safe.

### Verdict

The PR is **correct and worth keeping** — 86% UUID contamination reduction is a meaningful, measurable improvement. The implementation precisely matches the stated intent. The gaps noted above are pre-existing design choices (the per-batch ID exposure) or behavioral regressions (haiku) that should be addressed in a follow-up, not by reverting this PR.

---

## Summary

**Confirmed bugs:**
- **B1** (high impact): No UUID prohibition in `ENRICH_LEVERS_SYSTEM_PROMPT` or field descriptions; models have no prompt-level instruction against copying `Lever ID:` values into free-text fields. Root cause of all residual UUID contamination.
- **B2** (low impact): `errors` field type annotation mismatch (`List[...]` defaulting to `None`); type-checker noise only.
- **B3** (medium impact): `BatchCharacterizationResult.characterizations` has no count validation; when models return extra entries (haiku) or too few (silent drop), there is no per-batch detection.
- **B4** (latent): `execute_function` closure captures `chat_message_list` by reference in a loop; safe now but fragile against async refactoring.
- **B5** (low impact): False `partial_recovery` warnings when 2-call runs legitimately hit the 15-lever target.

**Key improvements:**
- **I1**: Add explicit UUID prohibition sentence to `ENRICH_LEVERS_SYSTEM_PROMPT` (addresses B1, N2 residual).
- **I2**: Post-process strip of UUID patterns from `synergy_text`/`conflict_text` (defensive fallback for any model).
- **I3**: Add "Return exactly N characterizations" instruction to per-batch user prompt (addresses B3, N3 haiku regression).
- **I4**: Strengthen `LeverCharacterization.lever_id` field description to emphasize verbatim copy (reduces haiku fabrication).
- **I6**: Update `OPTIMIZE_INSTRUCTIONS` to reflect PR #457 state and document remaining per-batch UUID vector.

**PR #457 assessment:** Correct, minimal, and effective for gemini and gpt-oss-20b (100% fix). Partial for llama3.1 (74% reduction, residual from per-batch prompt). Introduces a benign haiku regression (7 extra fabricated-ID entries, real levers unaffected). Should be kept; follow-up needed for I1/I3.
