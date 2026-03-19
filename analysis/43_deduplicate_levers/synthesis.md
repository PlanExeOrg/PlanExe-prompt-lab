# Synthesis

## Cross-Agent Agreement

Both agents (insight and code review) agree on all major findings:

- **llama3.1 blanket-keep is fixed**: avg kept dropped from 10.6 to 7.0. The primary target of PR #364 is achieved.
- **gpt-4o-mini over-inclusion is untouched**: avg kept 9.4→9.6, statistically unchanged. The calibration hint alone does not move this model.
- **gemini sovereign_identity is a new regression**: 5→9 kept, while all 6 other models landed at 5. The "expect 4–8" upper bound in the calibration hint caused gemini to stop absorbing after reaching 5 (the lower end of the range), though the correct answer requires 10 absorbs.
- **B3 fix is only half-done**: `_build_compact_history` at line 99 is correctly fixed with conditional `...`. But `all_levers_summary` at line 175 still appends `...` unconditionally on every entry regardless of whether the consequence string was actually truncated. Both agents flag this independently.
- **The calibration hint range "4–8" needs widening**: the upper bound acts as a stopping signal for models; "4–10" is more accurate.
- **100% schema success rate maintained**: No LLMChatError events in either period. PR did not break validation for any model.

## Cross-Agent Disagreements

There are no substantive disagreements between agents. The code review goes deeper into `runner.py` bugs (B2 spurious `partial_recovery` events, B3 nested `ThreadPoolExecutor` defeating per-plan log filtering) that the insight file does not cover — these are independent findings, not conflicting ones. The insight file marked the B3 fix as "confirmed fixed" without examining `all_levers_summary`; the code review identifies that as an error of omission, not a factual disagreement.

**Source code verification of disputed claims:**

- **B1 confirmed** (`deduplicate_levers.py:175`): `f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}..."` — `...` is unconditional. Line 99 in `_build_compact_history` correctly uses `{'...' if len(d.justification) > 80 else ''}` as the template for the fix.
- **S1/I1 confirmed** (`deduplicate_levers.py:133`): `"expect 4–8 to be absorbed or removed"` is present verbatim.
- **B2 confirmed** (`runner.py:125–128` and `546–552`): Both locations check `pr.calls_succeeded < 3`; the inline comment at line 122 says "A 2-call success is normal for models that produce 8+ levers per call" — confirming the threshold is wrong.
- **B3 confirmed** (`runner.py:514–527`): `_ThreadFilter` is created on the outer thread, then `run_single_plan` is submitted to an inner `ThreadPoolExecutor`. The inner thread has a different ident, so its logs are filtered out.
- **I3 confirmed**: `DEDUPLICATE_SYSTEM_PROMPT` defines "absorb" but provides no worked example of absorb reasoning.

---

## Top 5 Directions

### 1. Widen calibration hint from "4–8" to "4–10"
- **Type**: prompt change
- **Evidence**: S1 (code review), N2/Q5/C1 (insight), verified at `deduplicate_levers.py:133`
- **Impact**: Directly explains and fixes the gemini sovereign_identity regression (9→5 kept). Prevents premature stopping on high-duplicate plans where the correct absorb count exceeds 8. All other 6 models landed at 5 kept on sovereign_identity, confirming 10 absorbs is the correct answer for that plan — outside the current hint range. The fix is a single line. Risk to models that need more absorb pressure is minimal: widening the upper bound only allows more absorbs on plans where many are needed.
- **Effort**: low (one line in `deduplicate_levers.py:133`)
- **Risk**: Models already operating at 6–8 absorbs could theoretically push toward 10 unnecessarily. But the data shows this is not a concern: no model shows over-absorbing in the after-PR runs. The phrase "do not stop early" explicitly guards against premature stopping without forcing over-absorption.

### 2. Fix `all_levers_summary` unconditional `...` (complete the B3 fix)
- **Type**: code fix
- **Evidence**: B1 (code review), verified at `deduplicate_levers.py:175`. The insight file incorrectly marked B3 as "fully fixed."
- **Impact**: Every run of `deduplicate_levers` passes `all_levers_summary` to the LLM as the global comparison context (system message, visible for every per-lever call). Any lever with `consequences ≤ 120 chars` is shown with a false `...`, signaling truncation that didn't happen. This affects all 7 models × 5 plans = 35 runs. The misleading `...` can cause models to treat the context as incomplete when evaluating levers early in the list, creating uncertainty that may bias classification. Trivial to fix using the exact pattern already in line 99.
- **Effort**: trivial (one line, change `:120}..."` to `:120}{'...' if len(lever.consequences) > 120 else ''}"`)
- **Risk**: None. The fix pattern is already proven in `_build_compact_history`.

### 3. Add worked absorb example to `DEDUPLICATE_SYSTEM_PROMPT`
- **Type**: prompt change
- **Evidence**: N1/C2/Q2 (insight), I3 (code review). gpt-4o-mini's justifications uniformly contain "is a distinct and essential strategic decision" — a boilerplate phrase indicating the model evaluates each lever in isolation rather than comparing levers to each other. The system prompt defines `absorb` but provides zero demonstration of absorb reasoning.
- **Impact**: gpt-4o-mini remains the only unfixed over-inclusion target (9.6/15 avg kept). A worked example showing comparative lever reasoning ("lever X's consequences substantially overlap lever Y on Z — absorb X into Y") would break the isolationist evaluation pattern. Affects 5/35 after-PR runs (gpt-4o-mini plans). OPTIMIZE_INSTRUCTIONS already names over-inclusion as a known failure mode and recommends worked examples.
- **Effort**: medium (need to write a concise, domain-neutral example that doesn't trigger template-lock for other models; OPTIMIZE_INSTRUCTIONS warns about verbosity amplification from examples)
- **Risk**: Adding a single absorb example risks template-lock for weaker models that copy the example's phrasing. Should use a domain-specific mechanism in the example rather than reusable transitional phrases. Should keep it to one sentence showing the comparison, not a multi-sentence trace.

### 4. Fix `partial_recovery` threshold in `runner.py` (< 3 → < 2)
- **Type**: code fix
- **Evidence**: B2 (code review), verified at `runner.py:125–128` and `runner.py:546–552`. Inline comment at line 122 explicitly says "A 2-call success is normal for models that produce 8+ levers per call."
- **Impact**: Every 2-call success for identify_potential_levers generates a false `partial_recovery` event in `events.jsonl`. These events pollute the analysis pipeline, making it harder to distinguish genuine partial failures from normal 2-call completions. Affects analysis quality, not production output.
- **Effort**: trivial (two occurrences of `< 3` → `< 2` in runner.py)
- **Risk**: Minimal. A genuine 1-call partial recovery with ≥15 levers is a corner case; the threshold `< 2` would still flag a 0-call completion (which would be an exception anyway).

### 5. Document calibration capping as 5th failure mode in `OPTIMIZE_INSTRUCTIONS`
- **Type**: code change (documentation)
- **Evidence**: I5 (code review), confirmed from N2/Q1/Q5 (insight). The four currently documented failure modes (blanket-primary, over-inclusion, hierarchy-direction, chain absorption) omit the capping behavior observed in this iteration.
- **Impact**: Makes future self-improve iterations aware of this failure mode from the start, preventing future prompts from adding narrow ranges without noting the stopping-signal risk. OPTIMIZE_INSTRUCTIONS is the primary memory for the self-improve loop on this step.
- **Effort**: low (add 4–5 lines to `deduplicate_levers.py:26–48`)
- **Risk**: None.

---

## Recommendation

**Pursue direction 1 (widen calibration hint) and direction 2 (fix `all_levers_summary` `...`) in a single iteration.**

Both are in the same file (`deduplicate_levers.py`), both are one-line changes, both are confirmed bugs with direct evidence from the data, and neither carries meaningful risk.

**Direction 1 is the highest priority** because it explains a measured regression introduced by the PR (gemini sovereign_identity: 5→9 kept) and the fix is mechanically certain: the calibration hint's upper bound of 8 is empirically wrong for the sovereign_identity plan, which has 10 true near-duplicate pairs. The fix:

**File:** `deduplicate_levers.py:133`

Change:
```
In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed. If you find zero absorb/remove decisions, reconsider: the input almost always contains near-duplicates. Do not keep every lever.
```

To:
```
In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed. Plans with many near-duplicate names may require 10 or more absorbs — do not stop early. If you find zero absorb/remove decisions, reconsider: the input almost always contains near-duplicates. Do not keep every lever.
```

**Direction 2 (B1) should accompany it in the same PR:**

**File:** `deduplicate_levers.py:175`

Change:
```python
f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}..."
```
To:
```python
f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}{'...' if len(lever.consequences) > 120 else ''}"
```

These two changes together produce a clean, low-risk PR that fixes a confirmed regression, completes an incomplete bug fix, and has no measurable downside.

---

## Deferred Items

- **I3 (worked absorb example for gpt-4o-mini)**: High potential impact but medium effort and template-lock risk. Needs careful example design (domain-specific, concise, not copyable by weaker models). Do this in the iteration after direction 1+2 are validated.
- **B2 (runner.py `partial_recovery` threshold `< 3` → `< 2`)**: Trivial fix, but affects analysis tooling only, not production output. Bundle with the next runner.py change.
- **B3 (nested ThreadPoolExecutor defeats per-plan logging)**: Real bug but low urgency — log files are useful for diagnosis but not on the critical path. Address when runner.py gets a larger refactor.
- **I4 (`review_lever` validator minimum 10 chars vs 20–40 word target)**: Valid discrepancy in `identify_potential_levers.py`. The 10-char minimum is too permissive. Raising to 50 chars is safe and language-agnostic. Defer to an identify_potential_levers iteration.
- **I5 (OPTIMIZE_INSTRUCTIONS 5th failure mode — calibration capping)**: Low-effort addition. Include in the same PR as direction 1+2 or do as a standalone documentation-only commit.
- **S2 (`options` field description says "Exactly 3, no more" but validator accepts 4+)**: The policy is "over-generation tolerable, under-generation not" per the comment — but the field description actively contradicts that. Fix the field description to match policy. Low urgency.
- **N4 (fabricated percentages from upstream)**: Upstream issue in `identify_potential_levers`. Not a regression from this PR. Address in a future identify_potential_levers iteration.
- **Q4 (do downstream steps actually use `classification: primary|secondary`?)**: If `vital_few_levers` and `scenario_generation` don't consume the classification field, the split motivation from D8/synthesis-42 is unimplemented. Verify before investing further in secondary classification tuning.
