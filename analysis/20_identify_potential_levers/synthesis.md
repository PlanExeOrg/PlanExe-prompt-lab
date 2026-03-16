# Synthesis

## Cross-Agent Agreement

All four analysis files (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

**PR #309 verdict: KEEP.** The label-only option degradation in llama3.1 calls 2 and 3 is completely eliminated. All agents confirm: before = 47 short-label options across 1,890 total (2.5%), after = 0 across 1,902 total (0%). The call-3 average option word count for llama3.1 rose from 6.2 to 13.1 words. No regressions were introduced in other models. Success rate holds at 35/35 (100%) for the third consecutive clean sweep.

**Unsupported quantification persists.** Both insight files flag fabricated % claims after the PR (24 claims across 634 levers vs. 20 before). Both code reviews identify I1/I5 (add anti-fabrication reminder to the same call-2/3 prompt block) as the natural next fix. Strong cross-agent consensus.

**The production constant is out of date with prompt_5.** The checked-in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` still contains mandatory measurable estimates, the conservative→moderate→radical triad, and "Radical option must include emerging tech/business model." These instructions are not used by the optimizer runner (which loads prompt_5 via `--system-prompt-file`) but ARE used by the production pipeline (`run_plan_pipeline.py:386` calls `execute()` with no `system_prompt` override). The PR #309 worktree already updates the constant to match prompt_5, resolving this on merge.

**Some outputs returned fewer than 3 raw calls with no logged error.** insight_codex counts 33 third-call responses in runs 46–52 vs. 34 in runs 38–45. code_claude and code_codex both trace this to the exception-handling path. The worktree already changes `break` → `continue` (line 318), which is one of the changes bundled in PR #309.

---

## Cross-Agent Disagreements

**Where did they disagree:**

**Disagreement 1 — Scope of PR #309 changes in the worktree.**
code_claude catalogues four separate bugs (B1–B4) "in the main branch" that are "fixed in the PR branch," treating the worktree as a comprehensive multi-fix PR. code_codex frames B2 ("split-brain prompt") and B3 ("fabrication-forcing constant") as separate unresolved production bugs. **Resolution by source inspection:** The worktree at `.claude/worktrees/silly-purring-lovelace/...identify_potential_levers.py` confirms code_claude is right — the worktree contains all prior-PR improvements (structural validator at line 128–143, grounded consequences description at line 80–87, updated system prompt at lines 196–235, `OPTIMIZE_INSTRUCTIONS` constant at line 27–69, `continue` at line 318). These are accumulated improvements from PRs #268 and #299 that are now stacked in the #309 branch. After PR #309 merges to main, B1–B4 will all be resolved. code_codex's framing of them as "remaining" is incorrect for the post-merge state.

**Disagreement 2 — Severity of the missing-call anomaly.**
code_claude says the `break` → `continue` change "explains C3" and is already fixed. code_codex labels the partial-success path "the main confirmed code bug" and flags it as still unresolved. **Resolution:** Both are right in different scopes. The `continue` fix is in the worktree and will merge; it prevents call 3 from being silently dropped when call 2 fails. But code_codex's I1 (emit `partial` status rather than `ok` for incomplete runs) is a separate observability concern that neither the main branch nor the PR worktree addresses — that remains open.

**Disagreement 3 — `check_review_format` validator laxity.**
code_codex S1 flags the structural-only validator (length ≥ 20 chars, no brackets) as "almost structure-free" and potentially accepting low-information reviews. code_claude calls the same validator "correct" and notes it resolves the multilingual breakage. **Resolution:** Both concerns are valid but at different risk levels. The structural validator is the right direction (OPTIMIZE_INSTRUCTIONS explicitly warns against English-only keyword checks). The risk of accepting low-quality reviews is real but low-priority: the 35/35 success rate is maintained, and review quality across runs 46–52 shows no observable regression in substantive content.

---

## Top 5 Directions

### 1. Add anti-fabrication reminder alongside the sentence-completeness reminder in call-2/3 prompts
- **Type**: prompt change (one-line addition in Python source)
- **Evidence**: insight_codex H2, code_claude I1, code_codex I5 — three independent agents all flag this as the natural next step using identical reasoning: the sentence-completeness reminder fixed label degradation by restating a critical rule at the attention-decay point; the same mechanism should address fabricated numbers, which also accumulate in later calls
- **Impact**: 24 unsupported % claims across 634 levers (3.8%) in runs 46–52 affect all models — qwen3 "Allocate 70% of agricultural output", haiku "approximately 30%"/"24+ months", llama3.1 "90% waste reduction." A companion anti-fabrication line at the same position would reduce these without changing any other behavior. Prior evidence (PR #309 itself) shows this pattern works for llama3.1 call-3 quality; fabricated numbers are at least as susceptible to attention-decay reinforcement.
- **Effort**: low — one sentence appended to the call-2/3 prompt block (worktree line 274)
- **Risk**: minimal. The instruction matches an existing prohibition in both the system prompt (worktree line 228) and `OPTIMIZE_INSTRUCTIONS` (lines 52–54). Models that already avoid fabricating numbers are unaffected.

### 2. Emit `partial` status and `completed_calls` metadata when fewer than 3 calls succeed
- **Type**: code change in `identify_potential_levers.py` and `runner.py`
- **Evidence**: code_codex B1/I1 — partial call failures silently surface as `status="ok"` plans, making it impossible to distinguish a full 3-call run from a 1-call run in `events.jsonl`; confirmed by insight_codex counting 33 (not 35) third-call responses in runs 46–52 with no corresponding error events
- **Impact**: Makes call-completion regressions detectable before they accumulate into a batch-level quality drop. Currently a model that silently fails call 3 on every plan will score 35/35 success with ~7 levers per plan instead of ~18 — indistinguishable from a healthy run. Affects all models when they encounter schema validation failures on later calls.
- **Effort**: medium — add `completed_calls` and `expected_calls` to `IdentifyPotentialLevers.to_dict()` output, add a `partial` status check in `runner.py:302`
- **Risk**: downstream consumers that pattern-match `status == "ok"` would need updating; schema-level addition with a new field is safe if consumers ignore unknown fields

### 3. Add minimum word-count warning validator for options (no rejection, warning-only)
- **Type**: code change in `identify_potential_levers.py`
- **Evidence**: code_claude I2, code_codex I2, insight_claude N1 — the "at least 15 words with an action verb" rule is in the call-2/3 reminder (worktree line 274) but unenforced in code; llama3.1 call-3 average is 13.1 words vs. 18 for call-1; qwen3 call-3 averages 11.8 words
- **Impact**: Makes option-depth regressions measurable before they reach the analysis pipeline. If the call-2/3 reminder wording drifts in a future PR, this validator catches the regression immediately rather than requiring post-hoc analysis of raw artifacts.
- **Effort**: low — add a `@field_validator('options', mode='after')` that counts words per option and emits `logger.warning` without raising; similar to existing `check_option_count`
- **Risk**: warning-only adds no retry overhead; does not affect success rate or token cost

### 4. Enforce "Controls X vs. Y" first-sentence pattern across models
- **Type**: prompt change (system prompt addition)
- **Evidence**: insight_claude H1 — qwen3, gpt-4o-mini, and llama3.1 all produce non-"Controls" review first sentences ("Balances X vs. Y", "Manages X vs. Y", "Resource allocation vs. Y"); this was explicitly allowed by PR #299's validator relaxation but means downstream consumers that expect "Controls" format receive varied phrasing
- **Impact**: Affects review field format consistency across models. Not a quality regression (review content is substantive), but inconsistency across models complicates downstream text processing that parses `review` fields.
- **Effort**: low — add one instruction line to the system prompt: `First sentence must follow the exact pattern: "Controls [Tension A] vs. [Tension B]." where the action verb is literally the word "Controls".`
- **Risk**: moderate — models might re-introduce square-bracket placeholders when following a strict template (this is the exact failure mode that PR #299 fixed). Should be paired with a check that the `[` bracket validator still holds.

### 5. Document blacklist-attention-decay pattern in `OPTIMIZE_INSTRUCTIONS`
- **Type**: code documentation change
- **Evidence**: insight_codex H3 — the root cause of call-2/3 quality degradation (quality contracts stated in the system prompt lose attention weight as the `Do NOT reuse` blacklist grows) is now confirmed experimentally but not documented; future prompt editors may not know to restate key quality rules in call-2/3 prompts
- **Impact**: Low immediate impact, high long-term value. If future optimization iterations add new quality rules (e.g., domain-specificity requirements) or new call positions, the pattern "restate quality rules immediately after the exclusion blacklist" will be applied correctly the first time rather than discovered after regressions.
- **Effort**: very low — append a paragraph to `OPTIMIZE_INSTRUCTIONS` (worktree lines 27–69)
- **Risk**: zero runtime risk; documentation only

---

## Recommendation

**Pursue Direction 1 first: add anti-fabrication reminder to the call-2/3 prompt block.**

**Why first:** It uses the same proven mechanism as PR #309 (inline reminder immediately after the exclusion blacklist), targets an issue that spans all models (not just llama3.1), has zero risk of regression, and requires a single-line code change. The evidence is confirmed quantitatively: 24 fabricated % claims across 634 levers (3.8%) in runs 46–52, up slightly from 20 in runs 38–45. This is the most direct credibility threat to the generated plans — a fabricated "90% waste reduction" or "70% of agricultural output" undermines the entire lever's decision value.

**What to change:** In `identify_potential_levers.py`, the call-2/3 prompt block (worktree line 271–276):

```python
# Current (worktree lines 271–276):
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    f"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n\n"
    f"{user_prompt}"
)

# Proposed:
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    f"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n"
    f"Do not invent percentages, cost savings, or performance deltas — use qualitative language unless the project document supplies the number.\n\n"
    f"{user_prompt}"
)
```

The new line follows the exact same placement rationale: it restates an existing system-prompt rule (worktree line 228: "NO fabricated statistics or percentages without evidence from the project context") at the point where model attention has shifted to the exclusion blacklist and the original rule has decayed. The instruction is concrete, measurable, and aligns directly with the `OPTIMIZE_INSTRUCTIONS` anti-fabrication goal (lines 52–54).

---

## Deferred Items

**Direction 2 (partial-success observability):** Worth doing in the next iteration after the anti-fabrication fix. Two missing third-call runs per batch is low frequency but creates invisible quality variance. Adding `completed_calls` metadata is architectural scaffolding that pays off every future analysis.

**Direction 3 (word-count warning validator):** Low effort but blocked on confirming whether the 15-word floor in the call-2/3 reminder is producing the right results. After one more batch with the anti-fabrication reminder added, check if llama3.1 call-3 word counts converge toward call-1 naturally. If not, add the code-level warning to make the gap measurable.

**Direction 4 (review format consistency):** Low priority. The structural validator is working correctly; review format diversity is cosmetic, not a plan quality issue. Revisit only if downstream consumers of the `review` field report parsing problems.

**Direction 5 (`OPTIMIZE_INSTRUCTIONS` blacklist-decay note):** Should be bundled into the same PR as Direction 1, since the anti-fabrication fix IS an instance of this pattern. Add the documentation when the code change lands.

**haiku verbosity (insight_claude N1, insight_codex):** Haiku averages 1.85–2.5× baseline option length. Still below the 2× warning threshold for options; review length at 2.5× is from substantive multi-clause content, not padding. No action needed this iteration; monitor in analysis/21.
