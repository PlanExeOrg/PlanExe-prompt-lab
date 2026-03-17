# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude and code_claude) agree on the following:

1. **Summary field removal is the right call but incomplete.** The PR claimed to remove `DocumentDetails.summary` (B1) and the matching system prompt section (B2). Both agents confirm the field is still present in the current code (`identify_potential_levers.py:164`). The insight treats this as "unambiguously positive if done"; the code review confirms it is not done. Both agree it should be removed.

2. **Template lock on "This lever governs the tension between" is the primary quality regression.** The 100% lock rate for llama3.1 in run 75 (vs 71% in run 67) is flagged by both agents. The insight traces it to the slimmed call-2/3 prefix (N1, E2); the code review identifies the fix as adding a negative constraint (I1).

3. **qwen3's "Core tension:" opener is a model-native template pattern not covered by OPTIMIZE_INSTRUCTIONS.** Both agents recommend a negative constraint and a documentation addition to `OPTIMIZE_INSTRUCTIONS` (insight E4, P3; code review I2, I3).

4. **Strong models (haiku, gemini, gpt-4o-mini) are unaffected.** All three completed 5/5 plans cleanly in both before and after sets. No regressions on those models.

5. **Anti-fabrication holds.** No fabricated percentage claims in matched models before or after the PR. The removal of duplicate reminders from the call-2/3 prefix did not cause regression.

6. **PR #334's "at least 15 words" instruction is misplaced.** It appears only in the call-2/3 prefix, not in system prompt section 6. Call 1 is unenforced. Both agents note this (insight N4, code review B3/I4).

---

## Cross-Agent Disagreements

**Disagreement 1: PR #334 implementation status**

The insight (written from the perspective of run outputs) assessed the PR's token-saving changes as "clearly positive with no negative side effects" and rated P4 ("summary field removal is an unambiguous engineering improvement"). The code review found the summary field is **still present** in the code — lines 164–166 still show `summary: str = Field(...)` with no default, and lines 232–234 of the system prompt still instruct models to generate a summary.

**Verdict: Code review is correct.** Reading the source confirms the field and its prompt section are present. The insight's positive assessment of P4 was based on the PR's stated intent, not the actual code state. The token savings and validation risk reduction have not yet materialized.

**Disagreement 2: Cause of llama3.1 template lock regression**

The insight frames the second-example disappearance (N5) as "may be a consequence of the slimmed call-2/3 prefix" and recommends verifying the prefix diff first (E2, H1). The code review treats the slimmed prefix as the confirmed mechanism (citing B3 — call 1 was always prefix-free, so the second example only reached llama3.1 via calls 2/3, and slimming removed that reinforcement).

**Verdict: Code review's causal explanation is more tightly reasoned.** Call 1 has never had any extra prefix or example reinforcement — it receives only `user_prompt`. Calls 2/3 previously had more content, including potentially a re-statement of both examples. With the slim, only the first example in the system prompt is seen by llama3.1 on all three calls. However, since the pre-PR prefix content is not directly visible in the current code, the "confirmed" label is slightly overstated; the mechanism is plausible, not proven. The fix (add negative constraint against the first-example opener) is correct regardless of which side of the debate wins.

**Disagreement 3: Runner.py B4 severity**

The code review flags B4 (global dispatcher handler pollution across concurrent threads) as an actionable bug. The insight does not mention it at all. There is no run-output evidence that B4 corrupts plans — it affects per-plan debug tracking files only.

**Verdict: Both positions are defensible.** B4 is a real defect but its impact is limited to observability tooling, not plan output quality. It should be logged but deprioritized against content-quality changes.

---

## Top 5 Directions

### 1. Complete the summary field removal (B1 + B2)
- **Type**: code fix
- **Evidence**: code_claude B1, B2; insight_claude P4 (intent confirmed, not implemented). Source confirmed at `identify_potential_levers.py:152–166` (field) and `232–234` (system prompt section 4, `summary` instructions).
- **Impact**: Every LLM call in every run generates a summary string that is silently discarded. Removing it saves tokens on 3 calls × N plans per run. It also eliminates a validation failure point: if any model omits the required field the entire `DocumentDetails` response fails Pydantic and must be retried. The cleanup in the system prompt also removes dead instructions that currently consume tokens and may cause model confusion.
- **Effort**: Low — delete 3 lines from the schema (`DocumentDetails.summary` field), delete the matching system prompt sub-section (lines 232–234), remove `summary` from the system-prompt section 4 block.
- **Risk**: Near zero. No downstream code reads `summary`. The raw file (`002-9-potential_levers_raw.json`) will no longer contain the field, but nothing consumes it.

### 2. Add negative constraint against "This lever governs the tension between" opener (I1)
- **Type**: prompt change
- **Evidence**: insight_claude N1, N5; code_claude I1. Run 75 (llama3.1): 100% template lock. Run 67 (before): 71% lock. The second example ("Prioritizing X over Y carries hidden costs") dropped from 29% → 0%.
- **Impact**: Breaks 100% first-example lock for llama3.1. Benefits all models by reducing the pull of the first example as a default. Content quality of `review_lever` fields improves across all plans, not just the problematic silo plan.
- **Effort**: Low — append one sentence to the `review_lever` field description and/or system prompt section 4:
  > `Do NOT open with "This lever governs the tension between". Name the specific trade-off directly.`
- **Risk**: Low. Negative constraints carry a small risk of over-correction (models avoid the phrase even when it would be accurate), but the current 100% lock rate makes any diversification a net improvement.

### 3. Add negative constraint for qwen3's "Core tension:" opener and document in OPTIMIZE_INSTRUCTIONS (I2 + I3)
- **Type**: prompt change + documentation
- **Evidence**: insight_claude P3, E4; code_claude I2, I3. Runs 76–78 (qwen3) consistently open with "Core tension:" — a model-native template not derived from either prompt example. `OPTIMIZE_INSTRUCTIONS` only documents prompt-example-driven lock, not model-native patterns.
- **Impact**: Improves review diversity for qwen3, which is the most frequently run model in the after set (3 of 7 runs). Also documents a new class of problem so future optimization iterations know what to look for.
- **Effort**: Low for the negative constraint (one sentence); Low for the OPTIMIZE_INSTRUCTIONS addition (3–4 lines).
- **Risk**: Very low. The constraint targets a specific phrase. Adding to OPTIMIZE_INSTRUCTIONS is documentation only — no runtime risk.

### 4. Move "at least 15 words with an action verb" into system prompt section 6 (B3 / I4)
- **Type**: prompt change
- **Evidence**: code_claude B3, I4; insight_claude N4. The constraint currently lives only in the call-2/3 user prefix (line 283). Call 1 uses only `user_prompt` with no additional instructions. The PR's stated goal of "uniform enforcement across all calls" is unmet.
- **Impact**: Ensures call 1 obeys the same option-length floor as calls 2/3. For models that generate label-style options on call 1, this raises the floor. Insight N4 shows most models already exceed this threshold, so the primary beneficiary is weak models (llama3.1) producing short labels on their first call.
- **Effort**: Low — add one bullet to section 6 of the system prompt:
  > `- Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.`
- **Risk**: Very low. Options that already exceed 15 words are unaffected.

### 5. Fix global dispatcher event handler pollution in runner.py multi-worker mode (B4)
- **Type**: code fix
- **Evidence**: code_claude B4. `get_dispatcher()` returns a process-wide singleton. In multi-worker mode, each plan's `TrackActivity` handler is appended to the global handler list, causing all concurrent plans' events to broadcast to all handlers. Per-plan tracking files are unreliable for debugging.
- **Impact**: Fixes debugging data quality for multi-worker runs (workers=4 is the default for most models in this test set). Does not affect plan output quality or token usage. Improves observability reliability.
- **Effort**: Medium — requires either per-plan dispatcher scoping or a filtering predicate on each handler to discard events from other plans.
- **Risk**: Medium — modifying the llama_index dispatcher integration could introduce subtle regressions. Requires careful testing.

---

## Recommendation

**Do direction 1 first: complete the summary field removal (B1 + B2).**

This is the highest-confidence, lowest-risk change with immediate token savings on every run. The change is three mechanical deletions:

**In `identify_potential_levers.py`:**

1. Delete the `summary` field from `DocumentDetails` (lines 164–166):
   ```python
   # DELETE these 3 lines:
   summary: str = Field(
       description="One sentence prescribing a concrete addition to a specific lever. Example: \"Add 'partner with a regional distributor' to Supply Chain Strategy.\""
   )
   ```

2. Delete the `summary` sub-section from system prompt section 4 (lines 232–234):
   ```
   # DELETE these 3 lines from IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT:
      - For `summary`:
        One sentence prescribing a concrete addition to a specific lever.
        Example: "Add 'partner with a regional distributor for last-mile logistics' to Supply Chain Strategy."
   ```
   Also remove the blank line separator if it becomes orphaned.

**Why first:**

- It is the PR's own stated goal — the code never executed it. Running any further experiment while the `summary` field is still required means every LLM call continues to waste tokens generating text that is immediately discarded.
- Token cost is proportional to run count: with 7 "after" runs × 3 calls × 5 plans = 105 summary generations that were paid for and discarded. Future iterations multiply this waste.
- Zero risk: the field has no downstream readers confirmed by source inspection.
- It unblocks a clean re-assessment: once B1+B2 are done, a single re-run will show whether removing the field introduction affects other model behavior, clearing the way for the template-lock fix (direction 2) to be evaluated cleanly.

Direction 2 (negative constraint against "This lever governs the tension between") should follow immediately after — it is equally low-risk and directly addresses the most visible quality regression in the after set.

---

## Deferred Items

**S1 — Case-sensitive lever name deduplication** (`identify_potential_levers.py:279, 341`): Near-duplicate levers differing only by capitalization pass through. The downstream `DeduplicateLevers` step handles these, so this is a latent inefficiency rather than a bug. Low urgency.

**S2 — Partial recovery results indistinguishable from full success on resume** (`runner.py:122–131`): A plan that succeeded with 1/3 calls is marked `status="ok"` and will never be retried. This means thin lever sets (5 levers instead of 15–21) can persist silently. Medium priority for runs where reliability is critical, but does not affect prompt quality experiments.

**S3 — Single validation error rejects the entire response** (`identify_potential_levers.py:131–132`): If one lever has 4 options, the entire `DocumentDetails` response is rejected and retried. A trim-to-3 salvage path would reduce retry cost. Relevant to N3 (qwen3 ValueError in run 78). Medium priority — investigate whether a salvage path is safe given downstream 3-option assumption.

**H2 — Verify qwen3 "Core tension:" in pre-PR run 70**: If qwen3's model-native template predates PR #334, the pattern is not a regression introduced by the prompt change. Check `history/1/70_identify_potential_levers` review fields to confirm (relevant to direction 3 targeting the constraint).

**H4 — Run 80 (gemini) shallow output risk**: Completion in 33–38 seconds is fast. Content quality should be spot-checked against run 72 before declaring gemini's post-PR behavior fully equivalent.

**E1 — gpt-5-nano fabrication discrepancy**: Prior analysis 23 reported zero fabricated percentages in run 69; current agent collection found multiple % claims in hong_kong_game output. Verify by reading `history/1/69_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`. If confirmed, the prior analysis verdict for gpt-5-nano should be revised.

**Q4 — Consider deprioritizing llama3.1 from standard test suite**: Persistent partial_recovery issues (run 67 and run 75) and the strongest template lock make it a low-signal test subject. A cleaner suite would be: qwen3 × 1 (not ×3), gemini, haiku, gpt-4o-mini — and replace llama3.1 with a more reliable small model.
