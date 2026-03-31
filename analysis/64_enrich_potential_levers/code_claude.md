# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py` (context)

---

## Bugs Found

### B1 — UUID at end of `lever_details_for_prompt` breaks small-model `lever_id` matching

**File:** `enrich_potential_levers.py:240–247`

```python
lever_details_for_prompt = "\n\n".join([
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}\n"
    f"(internal reference: {lever.lever_id})"
    for lever in batch
])
```

This is the PR #464 change itself. The UUID was demoted from the first line (`Lever ID: {uuid}`) to the last line, relabeled as `(internal reference: {uuid})`.

Small models (llama3.1, gpt-5-nano) use a positional heuristic: they treat the first item in a structured block as the identifier to echo back into structured-output fields. With the UUID at the end, these models return the lever *name* as the `lever_id` value. The matching code at line 276 performs a strict UUID-key lookup:

```python
if char.lever_id in enriched_levers_map:  # keyed by UUID
```

A lever name never matches a UUID key, so every characterization is silently dropped and logged as `unknown_lever_id`. This directly causes the 100% → 0% regression for llama3.1 and the 100% → 29% regression for gpt-5-nano observed in runs 55 and 57.

### B2 — No name-based fallback in `enriched_levers_map` lookup

**File:** `enrich_potential_levers.py:275–284`

```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update({...})
    else:
        logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
        errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

When a model returns a lever name as `lever_id`, the lookup fails and the characterization is permanently discarded. There is no secondary lookup against lever names. A `name → lever_id` reverse map built once at line 218 would allow recovering these characterizations cleanly, since (as shown in the insight data) the names llama3.1 returns are correct — only the identifier field is wrong.

This bug interacts with B1: B1 causes models to return names; B2 ensures those names are never matched. B2 exists independently of PR #464 (it would also surface if the matching code encountered any other form of identifier mismatch), but it becomes the critical failure path once B1 is triggered.

---

## Suspect Patterns

### S1 — `LeverCharacterization.lever_id` field description gives no extraction instruction

**File:** `enrich_potential_levers.py:139`

```python
lever_id: str = Field(description="The uuid of the lever")
```

The description tells models *what* the field represents but not *where* to find the value. Before PR #464 the UUID was the first thing in the block (`Lever ID: {uuid}`), making it trivially easy for any model to associate `lever_id` with that value. After PR #464 the UUID is buried at the end under a label (`(internal reference: {uuid})`) that does not lexically match the field name `lever_id` or its description "The uuid". Small models have no signal to parse to the end of the block.

A stronger description — e.g., `"Copy the UUID exactly from the '(internal reference: ...)' line at the end of the lever block"` — would partially compensate for the positional change. The `OPTIMIZE_INSTRUCTIONS` note at line 91-92 of `identify_potential_levers.py` warns that field descriptions are read as literal instructions; the same principle applies here.

### S2 — "Exactly one per lever" in system prompt conflicts with "exactly N" in user prompt

**File:** `enrich_potential_levers.py:178` (system prompt) and `enrich_potential_levers.py:254–255` (user prompt)

System prompt (line 178):
```
Return exactly one characterization per lever requested — no more, no fewer.
```

User prompt (lines 254–255):
```python
f"Return exactly {len(batch)} characterizations — one per lever, no more, no fewer. "
```

The system prompt's "exactly one" is grammatically ambiguous — "one per lever" means N total, but "one" could also be parsed as a blanket count of 1. The user prompt's "exactly {N}" is unambiguous but duplicative. When these conflict for haiku (which reads both), the model may be confused about whether one or N is the canonical constraint. Neither instruction is enforced post-processing: there is no code-level check that `len(batch_result.characterizations) == len(batch)`, and over-/under-generation is handled only by the UUID-key matching logic that silently drops phantoms and marks missing levers as `incomplete`.

### S3 — `OPTIMIZE_INSTRUCTIONS` entry for UUID is accurate about format but silent about position risk

**File:** `enrich_potential_levers.py:95–97`

```
Short hex prefixes and integer indices both caused matching failures
across different model types — keep the full UUID for reliable
structured-output matching.
```

This entry documents UUID *format* (full UUID vs. short prefix) but not UUID *position* (first line vs. last line). PR #464 kept the full UUID but changed its position, and the entry gives no warning that position also affects matching. A reader of `OPTIMIZE_INSTRUCTIONS` would not see any red flag before applying the PR's approach to future work.

The insight proposes a concrete addition (quoted in §"OPTIMIZE_INSTRUCTIONS Alignment"). It should be added verbatim.

### S4 — `_run_plan_task` thread handler not guarded against `remove` failure

**File:** `runner.py:280–283`

```python
finally:
    with _file_lock:
        set_usage_metrics_path(None)
        dispatcher.event_handlers.remove(track_activity)
    track_activity_path.unlink(missing_ok=True)
    _maybe_generate_activity_overview(plan_output_dir)
```

`list.remove()` raises `ValueError` if the item is not present. If `run_single_plan` raises before the `add_event_handler` call takes effect (e.g., if the lock acquisition in the try block fails), the `finally` block would raise `ValueError`, masking the original exception. The `finally` block should use a try/except or check membership before removing.

---

## Improvement Opportunities

### I1 — Add name-to-UUID fallback in matching code (implements C2 from insight)

**File:** `enrich_potential_levers.py:218` and `enrich_potential_levers.py:275–284`

Build a reverse map alongside `enriched_levers_map`:

```python
enriched_levers_map = {lever.lever_id: lever.model_dump() for lever in levers_to_characterize}
name_to_lever_id = {lever.name: lever.lever_id for lever in levers_to_characterize}
```

Then in the matching loop, fall back to name lookup:

```python
if char.lever_id in enriched_levers_map:
    target_id = char.lever_id
elif char.lever_id in name_to_lever_id:
    target_id = name_to_lever_id[char.lever_id]
    logger.info(f"Resolved lever name '{char.lever_id}' to UUID '{target_id}' via name fallback")
else:
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
    continue
enriched_levers_map[target_id].update({...})
```

This recovers llama3.1 outputs where the model returns the correct lever name. The insight's data shows llama3.1 names are accurate — only the identifier field is wrong. Name ambiguity is not a concern for typical lever sets (names are designed to be distinct).

### I2 — Update `OPTIMIZE_INSTRUCTIONS` with UUID position risk

**File:** `enrich_potential_levers.py:88–97`

Add the entry proposed in the insight file to the `Known problems` section, after the existing UUID leakage entry:

```
- UUID position vs structured-output matching. Small models (e.g.,
  llama3.1, gpt-5-nano) use positional heuristics to populate the
  lever_id field: they treat the first item in each block as the
  identifier. Moving the UUID to the end (even with a clear label like
  "(internal reference:)") causes these models to return the lever name
  as lever_id, which breaks all downstream matching. Keep the UUID
  prominent (first or labeled early) in per-batch lever details, while
  using separate techniques (PR #457's full-context UUID removal) to
  prevent UUID leakage into free-text fields.
```

### I3 — Strengthen `LeverCharacterization.lever_id` description to reference extraction source

**File:** `enrich_potential_levers.py:139`

Change:
```python
lever_id: str = Field(description="The uuid of the lever")
```
To:
```python
lever_id: str = Field(description="The UUID of the lever — copy it exactly from the '(internal reference: ...)' line at the end of the lever block.")
```

This tells models the extraction source and reduces positional heuristic behavior.

### I4 — The `partial_recovery` event threshold in `runner.py` is wrong for `enrich_potential_levers`

**File:** `runner.py:577–583`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

This partial-recovery check is gated to `identify_potential_levers` only (line 577). The `enrich_potential_levers` step also tracks `batches_succeeded` (via `PlanResult.calls_succeeded`), but no equivalent warning is emitted for it. An enrichment run where 0 batches succeeded (all levers lost) would show `status=ok` with `calls_succeeded=2` and no event-level warning — exactly the silent failure mode described in the `OPTIMIZE_INSTRUCTIONS` at lines 99–103. An analogous guard for `enrich_potential_levers` would make monitoring easier.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| N1 — llama3.1 100% → 0% | B1 (UUID at end) + B2 (no name fallback): all characterizations dropped as `unknown_lever_id` |
| N2 — gpt-5-nano 100% → 29% | B1 + B2: same mechanism, partial recovery on 2 of 5 plans |
| N3 — gpt-oss-20b minor regression | B1 (weaker effect): model uses names for 3 levers on one plan but correctly extracts UUID on others |
| N4 — haiku fabricated-UUID errors persist | Neither B1 nor B2: haiku generates phantom characterizations with invented UUIDs; S2's exact-count instruction did not suppress this behavior because there is no post-processing enforcement |
| P1 — qwen3/gpt-4o-mini/gemini unaffected | These models parse the full block before populating structured-output fields, correctly extracting `(internal reference: {uuid})` regardless of position |
| P2 — No LLMChatError / Pydantic failures | Schema validation is structural (field presence, types); name strings pass the `lever_id: str` field cleanly. Errors are semantic (wrong value), not structural |

---

## PR Review

### PR #464 — "Move UUID to end of lever details, add positive framing and exact-count"

**Change 1: UUID repositioned to end of block (B1)**

The implementation correctly moves the UUID to the last line and wraps it in `(internal reference: ...)`. The intent — reducing UUID copy-paste into free-text — is sound, but the approach is unilateral: it improves UUID leakage at the cost of breaking `lever_id` matching for small models. The PR description says "Full UUID kept for reliable matching — no mapping code changes needed," which is incorrect: the `OPTIMIZE_INSTRUCTIONS` note it cited ("keep the full UUID for reliable structured-output matching") was about UUID *format*, not about UUID *position* being sufficient on its own. A code safety net (I1) is needed for the change to be safe across model sizes.

**Change 2: Positive framing in system prompt (line 176)**

```
In `synergy_text` and `conflict_text`, always refer to other levers by their name — for example, write "Policy Advocacy Strategy", not an identifier.
```

The intent is correct and the positive framing follows the `OPTIMIZE_INSTRUCTIONS` principle ("Do NOT use negative prohibitions naming 'UUID' or 'Lever ID'"). The example ("write 'Policy Advocacy Strategy', not an identifier") is clear. No bug here, though the insight notes the benefit is unconfirmed without checking UUID occurrence counts in synergy/conflict texts.

**Change 3: Exact-count instruction (lines 178, 254–255)**

Adding the instruction in both system and user prompts is redundant (see S2). The system prompt's "exactly one" phrasing is subtly ambiguous compared to the user prompt's "exactly N." Neither instruction has a corresponding code-level check. The insight confirms this had no effect on haiku over-generation. The instruction is harmless but doesn't accomplish its stated goal.

**Change 4: `OPTIMIZE_INSTRUCTIONS` update**

The update documents the new UUID-at-end approach as a known-good mitigation, but does not document the risk that small models require positional prominence to echo `lever_id` correctly. Future developers reading `OPTIMIZE_INSTRUCTIONS` would see no warning against the position change. I2 proposes the text that should have been added.

**Missing from the PR:**

- No code-level fallback (I1) to handle the case where models return lever names instead of UUIDs.
- No update to `LeverCharacterization.lever_id` description to point models at the extraction source (I3).
- `OPTIMIZE_INSTRUCTIONS` not updated with the position risk (I2).

**Verdict:** The PR introduces a net regression. The UUID leakage fix (Change 1) is directionally correct but incomplete without I1. The positive framing (Change 2) is a safe improvement. The exact-count instruction (Change 3) is ineffective. The `OPTIMIZE_INSTRUCTIONS` update (Change 4) is incomplete and should include a position-risk warning.

---

## Summary

PR #464's core regression is mechanical and localized:

1. **B1** (`enrich_potential_levers.py:240–247`): UUID moved to last line → small models return lever name as `lever_id`.
2. **B2** (`enrich_potential_levers.py:276`): strict UUID key lookup → names are silently dropped as `unknown_lever_id`.

These two bugs compose to produce 100% failure for llama3.1 and 71% failure for gpt-5-nano with no error surfaced at the `PlanResult` level (status remains "ok").

The fastest fix is either:
- **H1 (revert)**: Restore `Lever ID: {uuid}` as the first line of `lever_details_for_prompt`. Known-good behavior, no code changes needed.
- **C2 (code fix)**: Keep the UUID-at-end format but add the name-to-UUID fallback (I1). Requires also updating the `lever_id` field description (I3) and `OPTIMIZE_INSTRUCTIONS` (I2).

H1 is lower risk. C2 preserves the UUID leakage improvement but adds code complexity. The insight data shows the leakage benefit of C1 cannot be confirmed from the available outputs, so H1's cost is low.

The `identify_potential_levers.py` and `runner.py` files show no bugs related to the PR. S4 in `runner.py` is a minor defensive-coding issue unrelated to PR #464.
