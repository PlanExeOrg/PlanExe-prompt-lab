# Synthesis

## Cross-Agent Agreement

Both `insight_claude.md` and `code_claude.md` reach identical verdicts and share the same core findings:

1. **REVERT** — PR #373's Likert scoring approach should be reverted. Both agents agree the speed improvement is real and valuable, but the quality regressions are too severe to accept.

2. **100% structural success, 0% deduplication quality** — 35/35 runs produce valid JSON. But capable models (gpt-oss-20b, qwen3, haiku, gemini, gpt-4o-mini) keep 16-18 of 18 levers with no meaningful removal. The step is structurally succeeding while functionally doing nothing.

3. **llama3.1 scale inversion is catastrophic** — On silo and gta_game, llama3.1 scores 17/18 levers as -1 or -2 while its own justifications say "highly relevant." Result: 1 lever out of 18 reaches downstream. Both agents trace this to the absence of a minimum-lever-count guard (insight C2, code B4).

4. **Relevance ≠ deduplication** — The root architectural flaw: the prompt asks "How relevant is this lever to this plan?" not "Is this lever redundant with another?" A lever can be highly relevant and fully redundant with another. The Likert approach cannot distinguish these cases. Both agents identify this as the primary cause of the quality regression (insight N2/N3, code I5/N2/N3).

5. **Batch approach is architecturally sound** — The 18→1 call reduction works. All models parse the batch schema. The problem is the scoring schema, not the batching.

6. **B2 (duplicate lever_id) confirmed by both** — insight N5 observes llama3.1 returning lever `32ad06c5` twice; code B2 identifies the missing `seen_decision_ids` check that lets the second entry overwrite the first.

7. **S1 (naming banned phrases in field description)** — Both agents flag that `Lever.consequences` field description names "Controls ... vs." and "Weakness:" — phrases explicitly listed in `OPTIMIZE_INSTRUCTIONS` as template-lock risks that must NOT be named.

---

## Cross-Agent Disagreements

No material disagreements. The agents cover complementary aspects:
- `insight_claude.md` analyzes model behavior across 35 runs with quantified score distributions and before/after comparisons.
- `code_claude.md` finds the code-level mechanisms that explain those behaviors (B1–B5, S1–S3).

One nuance: `code_claude.md` raises B3 (`_score_to_classification` dead "remove" branch contradicts `OutputLever.classification` type). This is correct and verified — line 120 declares `Literal["primary", "secondary", "remove"]` but line 268 only calls the function when `score >= 1`, making "remove" unreachable, and `OutputLever.classification` (line 116) only accepts `Literal["primary", "secondary"]`. This is a latent type-safety issue but has no runtime impact in the current code.

**Verified from source code:**
- `deduplicate_levers.py:219–226` — B1 confirmed: exception swallowed, `batch_result` stays None, all levers default to score=2.
- `deduplicate_levers.py:233–241, 255` — B2 confirmed: no seen-id check; dict comprehension takes the last duplicate entry.
- `deduplicate_levers.py:120–127` — B3 confirmed: dead "remove" branch in type annotation.
- `deduplicate_levers.py:254–276` — B4 confirmed: no minimum-lever guard after building output_levers.
- `runner.py:151–156` — B5 confirmed: `calls_succeeded=1` hardcoded regardless of LLM success.
- `identify_potential_levers.py:116–119` — S1 confirmed: "Controls ... vs." and "Weakness:" named explicitly in the field description sent to LLMs.
- `runner.py:125–127` — S2 confirmed: `< 3` threshold fires false-positive warnings for clean 2-call successes.

---

## Top 5 Directions

### 1. Revert PR #373: restore primary/secondary/remove taxonomy in a single batch call
- **Type**: workflow change + prompt change
- **Evidence**: insight N2, N3, N6; code I5, N2, N3; both REVERT verdicts. Supported by iter 49 synthesis which found primary/secondary/remove produced 58%/27%/15% splits — all three categories meaningfully exercised. PR #373 abandons a working deduplication mechanism to fix a speed problem, but the speed problem can be solved while keeping the mechanism.
- **Impact**: Restores deduplication for all 7 models. Eliminates the "capable models keep all 18 levers" failure mode (N2). Preserves the 18→1 call speed improvement (PR #373's architecture is kept; only the schema changes). Fixes N1 (llama3.1 scale inversion) indirectly — the primary/secondary/remove taxonomy is a categorical label, not a scale, so there is no polarity to invert.
- **Effort**: Medium. Requires adapting the PR #372 `DEDUPLICATE_SYSTEM_PROMPT` and Pydantic schema (`LeverScoreDecision`) to work as a batch call rather than per-lever calls. The batch architecture from PR #373 is proven feasible — all models parse `BatchDeduplicationResult` successfully. The change is: replace `Literal[-2, -1, 0, 1, 2]` score field with `Literal["primary", "secondary", "remove"]` classification field; update system prompt to ask "Is this lever redundant?" instead of "Is this lever relevant?"; update the filter from `score < 1` to `classification == "remove"`.
- **Risk**: Weaker models (llama3.1) may struggle to apply the three-way taxonomy consistently when all 18 levers appear simultaneously in one prompt. This should be verified against the 5-plan benchmark. The iter 49 bugs (B2: contradictory fallback, B3: template-lock in secondary definition, S1: calibration for 18 levers) should be fixed in this combined PR rather than deferred again.

### 2. Add minimum-lever-count guard (B4)
- **Type**: code fix
- **Evidence**: code B4; insight C2. llama3.1 returns 1 lever on silo (run 57) and gta_game (run 57). Both runs emit `status="ok"`. Downstream steps receive a 1-lever list.
- **Impact**: Catches any future catastrophic deduplication failure — regardless of whether direction 1 is implemented. The check is model-agnostic and approach-agnostic. A `logger.warning()` (or `logger.error()`) when `len(output_levers) < max(3, len(input_levers) // 4)` surfaces the failure before the output file is written. Optionally, a `status="partial"` return from `_run_deduplicate` would make the failure visible in `outputs.jsonl`.
- **Effort**: Low. Add ~5 lines after line 276 of `deduplicate_levers.py`.
- **Risk**: Near zero. A warning-only check cannot break any existing behavior. Even a retry/error path would only fire on extreme cases (< 25% of input levers surviving).

### 3. Fix silent LLM failure propagating as success (B1 + B5)
- **Type**: code fix
- **Evidence**: code B1, B5. When the batch LLM call throws any exception other than `PipelineStopRequested`, the error is logged but `batch_result` stays `None`. All levers default to score=2. `runner.py` returns `calls_succeeded=1` and `status="ok"`. The `outputs.jsonl` record is indistinguishable from a genuine success.
- **Impact**: Currently masked in the test data because all 35 runs happen to succeed. But the failure path is live code and will trigger under network errors, rate limits, or structured-output parse failures. When it fires, analysis pipelines that trust `outputs.jsonl` will not detect the failure. Fix: (a) expose a `calls_succeeded: int` field on `DeduplicateLevers` (count 1 on LLM success, 0 on fallback); (b) in `_run_deduplicate`, emit a `partial_recovery` event when `calls_succeeded == 0`; (c) change the hardcoded `calls_succeeded=1` to use the actual value.
- **Effort**: Low–medium. The pattern is already implemented correctly in `_run_levers` (line 120: `actual_calls = len(result.responses)`).
- **Risk**: Low. Change is additive — adds observability without changing behavior.

### 4. Fix duplicate lever_id in model response (B2)
- **Type**: code fix
- **Evidence**: code B2; insight N5. llama3.1 returned lever `32ad06c5` twice in hong_kong_game (run 57). The second entry (with a self-referential justification) overwrote the first. The dict comprehension at line 255 silently takes the last entry.
- **Impact**: Prevents nonsensical justifications (and potentially different scores) from winning when the model hallucinates a duplicate. Add a `seen_decision_ids: set[str]` check inside the loop at lines 233–241, keeping the first entry and logging a warning on the second.
- **Effort**: Low. 4–5 lines added to the existing loop.
- **Risk**: Near zero. Only fires when the model returns duplicate lever_ids, which is already an error condition.

### 5. Remove banned-phrase names from `Lever.consequences` field description (S1)
- **Type**: prompt change (field description)
- **Evidence**: code S1; `OPTIMIZE_INSTRUCTIONS` lines 78–82 in `identify_potential_levers.py`. The `consequences` field description explicitly names "Controls ... vs." and "Weakness:" as banned phrases. `OPTIMIZE_INSTRUCTIONS` states: "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."
- **Impact**: Affects all models on all plans at the `identify_potential_levers` step (upstream of deduplication). The field description is part of the JSON schema sent to every model. Removing the named phrases reduces template-lock risk for small/mid-tier models. The prohibition can be rephrased structurally: instead of naming the banned phrases, describe what the field should contain: "Describe the direct effect and downstream implication. Do not include critique, trade-off analysis, or evaluative text — those belong in review_lever."
- **Effort**: Low. Edit 2 lines in `identify_potential_levers.py` (lines 119–121). The same text appears in `LeverCleaned.consequences` (lines 209–214) but that schema is never sent to an LLM — harmless, but can be cleaned up for consistency.
- **Risk**: Low. The change removes template-lock bait, which should only improve or preserve output quality. No structural change to the schema or pipeline.

---

## Recommendation

**Implement direction 1: revert the Likert schema and restore the primary/secondary/remove taxonomy in a single batch call.**

This is the right first move because it directly fixes the root cause of the quality regression while preserving the speed gain. The speed improvement (18→1 calls) is the only thing PR #373 did correctly, and that architecture is proven: all 7 models parse `BatchDeduplicationResult` without errors. The problem is exclusively the scoring schema and the prompt question.

**Specific changes required:**

**File: `deduplicate_levers.py`**

1. Replace `LeverScoreDecision.score: Literal[-2, -1, 0, 1, 2]` with `classification: Literal["primary", "secondary", "remove"]` (plus a `justification` field as before, with an explicit `supersedes` field for "remove" entries naming which lever this one is absorbed into).

2. Replace `DEDUPLICATE_SYSTEM_PROMPT` content. The new prompt should:
   - Ask "Is this lever redundant with another lever?" (deduplication question), not "How relevant is this lever to this plan?" (relevance question).
   - Define: `primary` = core strategic lever; `secondary` = supporting lever; `remove` = substantially overlaps another lever — name the lever it is absorbed into.
   - Carry the prior calibration: "Expect 10–20% of levers to be classified as `remove`."
   - Include the system-prompt fixes identified in iter 49 (B2: remove contradictory fallback language; B3: revise the secondary definition to avoid template-lock; S1: calibrate explicitly for 18-lever inputs).

3. Update the filter at line 259 from `lever_decision.score < 1` to `lever_decision.classification == "remove"`.

4. Update `_score_to_classification` — or remove it entirely since the classification is now direct from the model.

5. While editing: add the minimum-lever-count guard (direction 2) and the duplicate lever_id check (direction 4) — both are low-effort and should ship in the same PR.

**File: `runner.py`**

6. Fix `calls_succeeded=1` hardcoding (direction 3) — expose an actual success flag from `DeduplicateLevers.execute()`.

**Expected outcome:** Capable models should resume removing ~10–20% of levers (the overlapping ones) with explicit `supersedes` justifications, matching PR #372 behavior. llama3.1 should no longer exhibit scale inversion because there is no numeric scale to invert. Speed remains at 1 call per plan.

---

## Deferred Items

- **Direction 5 (S1 — banned-phrase names in field description)**: Worth fixing but belongs in a separate `identify_potential_levers` iteration, not the deduplication PR.

- **S2 (partial_recovery false positives at `< 3` calls)**: The threshold should be changed to `< 2` to reflect that 2-call successes are normal. Low-effort fix, but not urgent.

- **I4 (document scale-inversion in OPTIMIZE_INSTRUCTIONS)**: After the Likert approach is reverted, this is moot. If a future PR reintroduces numeric scoring, add this warning then.

- **I3 (structured event for LLM failure)**: Valuable for production observability but requires more scaffolding. Defer to a dedicated observability pass.

- **Q1 (speed goal as standalone follow-up)**: The PR #372 taxonomy batched in a single call (this recommendation) satisfies the speed goal. No further work needed on this question.

- **Q2 (why llama3.1 inverts on some plans but not others)**: The inversion pattern (silo, gta_game: inverted; hong_kong_game: partial) is worth investigating for diagnostic purposes, but the fix (direction 1) eliminates the failure mode regardless of its cause.

- **Q4 (iter 49 prompt bugs B2, B3, S1)**: These were identified in the prior synthesis and never addressed. They should be incorporated in the PR that implements direction 1 above, not deferred again.
