# Synthesis

## Cross-Agent Agreement

Only one insight file (`insight_claude.md`) and one code review file (`code_claude.md`) are present for this analysis — both from the same Claude agent. Cross-referencing is therefore between the behavioral/quantitative view (insight) and the structural/code view (code review).

Both files agree on the following:

1. **PR #457 verdict: CONDITIONAL — keep the change.** The 86% UUID contamination reduction (105 → 15 occurrences) is real, measurable, and directionally correct. The one-line change in `full_lever_context_str` is safe and has no correctness side effects.

2. **Root cause of residual contamination (B1 / N2):** The `ENRICH_LEVERS_SYSTEM_PROMPT` contains no prohibition against copying UUIDs into free-text fields. The per-batch prompt (`lever_details_for_prompt`, lines 233–240) still surfaces `Lever ID: {uuid}` for every lever in the current batch. The PR removed one UUID source (the full-context list) but not the other (per-batch details). This is the structural reason llama3.1 went from 54 → 15 UUID occurrences rather than → 0.

3. **Haiku regression is benign but real (N3 / B3 / Gap 3):** After PR #457, haiku produces 7 extra `LeverCharacterization` objects with fabricated IDs across 3 plans. The actual 35/35 real levers are enriched correctly — the fabricated entries are discarded. The regression is not silent failure but it adds noise to the errors list. Both files identify the same two fixes: (a) add "Return exactly N characterizations" to the user prompt (I3), and (b) strengthen the `lever_id` field description to say "copy verbatim" (I4).

4. **OPTIMIZE_INSTRUCTIONS is stale after PR #457 (I6 / H1):** Lines 88–92 of `enrich_potential_levers.py` still say "The full_lever_context_str includes lever_id UUIDs" in present tense. This is no longer true. Both files call for an update.

5. **Top follow-ups are I1 and I3**, in that order: prompt prohibition on UUIDs in free-text fields, then exact-count constraint on batch responses.

---

## Cross-Agent Disagreements

No disagreements between files. One item worth resolving from source code:

**Is the `__main__` block JSON mismatch (S2) a real bug?**

Code review claims the `__main__` block loads the deduplicated levers file as a whole JSON object (line 364: `input_levers = json.load(f)`) without extracting the `"deduplicated_levers"` key, whereas `runner.py` lines 172–173 correctly does `json_dict["deduplicated_levers"]`. Confirmed in source:

- `enrich_potential_levers.py:364`: `input_levers = json.load(f)` — passes whole dict to `execute()`
- `enrich_potential_levers.py:188`: `[InputLever(**lever) for lever in raw_levers_list]` — iterates over dict keys, not lever list
- `runner.py:172–173`: `json_dict = json.load(f)` then `lever_item_list = json_dict["deduplicated_levers"]`

S2 is a real bug: the `__main__` standalone test would fail or silently produce garbage with real deduplicated output. Low priority for the optimization loop but real.

**Is B5 (false partial_recovery warning) in enrich_potential_levers or identify_potential_levers?**

Confirmed in `runner.py` lines 577–583: the `partial_recovery` event is gated on `step == "identify_potential_levers"`. The `< 3` threshold is also used in `_run_levers()` (lines 131–134), which maps to the identify step. The enrich step uses `batches_succeeded` as its `calls_succeeded`, and has no equivalent warning. B5 applies to the identify step's runner, not to enrich. Out of scope for this analysis but worth noting.

---

## Top 5 Directions

### 1. Add explicit UUID prohibition to `ENRICH_LEVERS_SYSTEM_PROMPT`
- **Type**: prompt change
- **Evidence**: B1 (code review), N2 (insight), Gap 2 (code review). Confirmed: `ENRICH_LEVERS_SYSTEM_PROMPT` lines 159–172 contain no prohibition against UUIDs in free-text fields. `lever_details_for_prompt` lines 233–240 still surfaces `Lever ID: {uuid}` for every per-batch lever. OPTIMIZE_INSTRUCTIONS already states "Models should reference levers by name only in free-text fields" but this instruction appears only in the developer notes, not in the LLM-facing prompt.
- **Impact**: Targets llama3.1's residual 15 UUID occurrences (all from per-batch IDs after the cross-batch vector was closed by PR #457). Expected reduction: 15 → 0 for well-behaved models; llama3.1 may partially comply. Gemini and gpt-oss-20b are already clean — no regression risk. Also closes the conceptual gap that haiku's extra-characterization behavior may partly exploit.
- **Effort**: low — one sentence addition to an existing prompt block
- **Risk**: low — purely additive; no schema changes, no retry logic changes. llama3.1 may not fully comply (poor instruction follower in adversarial cases), but no downside exists.

### 2. Add "Return exactly N characterizations" instruction to per-batch user prompt
- **Type**: prompt change
- **Evidence**: B3 (code review), N3 (insight), I3 (code review), Gap 3 (code review). `BatchCharacterizationResult.characterizations` has no `max_length` constraint (confirmed at lines 147–149). The user prompt says "provide the … for the following N levers" but never says "no more, no fewer." Haiku generated 7 extra entries when the full-context UUID anchor was removed.
- **Impact**: Targets haiku's 7 new `unknown_lever_id` errors (3 plans). Expected: 7 → 0 or near-zero for function-calling models. Low risk that other models produce more than N entries — none did before or after the PR.
- **Effort**: low — add one sentence to the user prompt string at line 247: `f"Return exactly {len(batch)} characterizations, one per lever. Do not add characterizations for levers not listed in this batch."`
- **Risk**: low — too-strict instructions can theoretically cause a model to drop a lever if it can't characterize it, but this is better than the current silent over-generation.

### 3. Post-process UUID strip from `synergy_text` and `conflict_text`
- **Type**: code fix
- **Evidence**: C2 (insight), I2 (code review). Both files independently recommend a regex strip after the characterization merge loop (lines 267–276).
- **Impact**: Eliminates all UUID contamination regardless of model prompt compliance. Model-agnostic. Works for llama3.1 even if it ignores the prompt prohibition (Direction 1). Reduces 15 → 0 UUID occurrences guaranteed.
- **Effort**: medium — requires adding a compiled regex, applying it to `char.synergy_text` and `char.conflict_text` at lines 269–272, and testing the pattern doesn't strip valid content. Pattern: `r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'` (standard UUID format, case-insensitive).
- **Risk**: low — a lever name that happens to look like a UUID is extremely unlikely. The strip only removes the UUID token, not surrounding prose.

### 4. Strengthen `LeverCharacterization.lever_id` field description
- **Type**: prompt change
- **Evidence**: I4 (code review). Confirmed: line 134 reads `lever_id: str = Field(description="The uuid of the lever")` — minimal, gives no hint that the model must copy the ID verbatim and not invent one.
- **Impact**: Reduces haiku's fabricated-ID entries (haiku is a function-calling model sensitive to field descriptions) and may reduce llama3.1's UUID corruption in structured output. Addresses the input-side of haiku's regression: if haiku knows it must copy the ID exactly, it is less likely to fabricate new UUIDs for extra entries.
- **Effort**: low — single field description change: `"The exact lever_id UUID from the 'Lever ID:' field in the input for this lever — copy it verbatim, do not modify or invent a new value."`
- **Risk**: low — strengthening a field description is purely additive.

### 5. Update `OPTIMIZE_INSTRUCTIONS` to reflect post-PR #457 state
- **Type**: documentation / workflow change
- **Evidence**: I6 (code review), H1 (insight). Confirmed stale: lines 88–92 of `enrich_potential_levers.py` still say "The full_lever_context_str includes lever_id UUIDs" — this has been false since PR #457 merged. The active UUID vector is now `lever_details_for_prompt` (per-batch prompt), and haiku's new behavior (extra fabricated-ID characterizations) is undocumented.
- **Impact**: Ensures the next self-improve iteration has accurate context. Prevents future experiments from "re-fixing" a problem that's already fixed, or missing the residual per-batch vector. Medium signal-value since the optimizer reads OPTIMIZE_INSTRUCTIONS directly.
- **Effort**: low — update the existing entry and add two new sub-bullets.
- **Risk**: none.

---

## Recommendation

**Implement Direction 1 first: add an explicit UUID prohibition to `ENRICH_LEVERS_SYSTEM_PROMPT`.**

**Why first:** It is the direct, targeted fix for the root cause of all remaining UUID contamination. B1 (no prohibition) is the structural gap that the PR left open. All 15 residual UUID occurrences (llama3.1, runs 4/27) trace to `lever_details_for_prompt` exposing `Lever ID:` without any instruction prohibiting its reproduction in free-text output. The prohibition is already the stated intent in OPTIMIZE_INSTRUCTIONS ("Models should reference levers by name only in free-text fields") — it just isn't in the LLM-facing prompt.

Direction 2 (exact-N instruction) is also very low effort and can be bundled into the same PR since it targets a different surface (user prompt vs system prompt) with no interaction risk. Bundle both.

**Specific change — file: `enrich_potential_levers.py`, lines 159–172 (`ENRICH_LEVERS_SYSTEM_PROMPT`)**

Add the following as a fourth output requirement, immediately after the existing point 3:

```python
ENRICH_LEVERS_SYSTEM_PROMPT = """
You are an expert systems analyst and strategist. ...

**Output Requirements (for each lever in the batch):**
1.  **`description`:** ...
2.  **`synergy_text`:** ...
3.  **`conflict_text`:** ...
4.  **Important — lever references:** In `synergy_text` and `conflict_text`, refer to
    other levers by **name only**. Do not reproduce any `lever_id` UUID value in these
    free-text fields, even when a UUID appears in the lever details provided below.

You MUST respond with a single JSON object ...
"""
```

**Specific change — file: `enrich_potential_levers.py`, line 247 (user prompt)**

Replace:
```python
f"Please provide the `description`, `synergy_text`, and `conflict_text` for the following {len(batch)} levers. "
f"Analyze them against the full list provided above.\n\n"
```

With:
```python
f"Please provide the `description`, `synergy_text`, and `conflict_text` for the following {len(batch)} levers. "
f"Return exactly {len(batch)} characterizations — one per lever listed below, no more, no fewer. "
f"Analyze them against the full list provided above.\n\n"
```

**Expected outcome:** llama3.1 residual UUID count 15 → 0 or near-zero; haiku fabricated-ID errors 7 → 0 or near-zero; no regressions for other models. If llama3.1 partially ignores the prohibition, Direction 3 (post-process strip) can be added as a follow-up.

Also update `OPTIMIZE_INSTRUCTIONS` (Direction 5) in the same PR since it is zero-risk and zero-effort, and keeps the optimization loop's context accurate.

---

## Deferred Items

- **Direction 3 (post-process UUID strip, I2/C2):** Do this if Direction 1 does not fully eliminate llama3.1 residual UUIDs. It is a defensive guarantee but has slightly more code surface. Best to try the prompt fix first, measure, then add the regex only if needed.
- **Direction 4 (strengthen lever_id field description, I4):** Low effort, bundle with Direction 1/2 PR if the change is cheap enough. Independently valuable for haiku structured output quality.
- **B2 (type annotation mismatch, `errors: List[...] = None`):** Fix opportunistically when touching the `EnrichPotentialLevers` dataclass. Change to `Optional[List[Dict[str, Any]]] = None`. Zero functional impact.
- **B4 (closure capture by reference in `execute_function`):** Latent risk only. Safe to fix with `def execute_function(llm, _msgs=chat_message_list):` but not urgent unless async refactoring begins.
- **B5 (false `partial_recovery` warning in runner.py for identify step):** Fix the threshold to `< 2` or use a lever-count check. Out of scope for enrich step analysis.
- **S1 (global dispatcher shared across parallel plan workers):** Requires investigation into `TrackActivity` filter behavior. Do not change without confirming the contamination exists empirically.
- **S2 (`__main__` block JSON mismatch):** Fix by extracting `input_levers = json.load(f)["deduplicated_levers"]` at line 364. Trivial fix, but affects test infrastructure only.
- **S3 (English-only prohibition text in `identify_potential_levers.py` field descriptions):** In scope for the identify step optimizer, not enrich. Note: `LeverCleaned` at lines 208–215 copies the same English-only prohibition text in its `consequences` field description — this is documentation-only (not sent to LLM) so it's not a functional risk.
- **N4 (fabricated percentages echoing from `consequences`):** Pre-existing upstream issue from `identify_potential_levers` step. Not addressable in the enrich step. The fix belongs in the identify step prompt.
- **I5 (no max_length on DocumentDetails.levers):** In the identify step. The comment at line 187 explains this is intentional. Not urgent.
- **N1 / gpt-oss-20b throughput:** Run a repeat experiment to determine if 3/5 timeouts are noise or a stable regression. If stable, investigate model availability or routing for `openrouter-gpt-oss-20b`.
