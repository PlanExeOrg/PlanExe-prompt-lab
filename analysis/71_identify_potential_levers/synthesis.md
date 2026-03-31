# Synthesis

## Cross-Agent Agreement

Both the insight and code review agents (both claude) converge on the same root cause and priority:

1. **B3 / I1 is the dominant finding.** The anti-fabrication constraint ("Never invent percentages, costs, or timeframes — only cite numbers that appear in the project context") does not prohibit arithmetic derivation from real plan numbers. PR #475's Fix 3 made fabrication **worse** (HKD refs: 5→20, +4×; dollar-sign refs: 6→28, +4.7×). Both agents trace this directly to the constraint's logical gap: "only cite numbers from context" reads as a permission floor, not a ceiling, so models cite real plan numbers AND derive additional amounts from them.

2. **B2 explains why Fix 1 failed.** `Lever.review_lever` has "1–2 sentences" in the Pydantic field description (line 127) but "one sentence (20–40 words)" in system prompt section 6 (line 260). Both agents confirm this contradiction was introduced by PR #475 itself. Review length barely changed (−3.3%), consistent with models receiving conflicting signals and averaging them.

3. **PR #475 verdict: CONDITIONAL.** Both agents agree the PR preserved zero template leakage, zero execution errors, and 100% success rate from PR #358, but delivered no measurable benefit on its stated goals. Keep the structural/cosmetic changes; follow up on fabrication regression.

4. **B1 (closure capture) is latent, low severity.** Both agents classify this as a maintenance risk, not an active bug. Currently safe in synchronous execution.

---

## Cross-Agent Disagreements

There are no inter-agent disagreements (only one insight and one code-review file, both from claude). The only unresolved question is whether to keep the anti-fabrication constraint in both the Pydantic field description and the system prompt (I6: duplication may backfire), or consolidate to one location. The code review raises this as speculative; the insight file raises the same question (Question 4). Neither agent has experimental data to resolve it. Source code confirms the duplication at lines 113–117 (`Lever.consequences` field description) and line 232 (system prompt section 2) — the wording is identical in both locations.

---

## Top 5 Directions

### 1. Extend anti-fabrication constraint to explicitly prohibit arithmetic derivation
- **Type**: prompt change
- **Evidence**: B3 (code_claude), I1 (code_claude), Findings 1–3 (insight_claude). All three fabrication patterns (haiku: HK$75M extrapolation from Fund reference; gpt-oss-20b: HK$141M/HK$117.5M/HK$70.5M derived from HK$470M; gpt-5-nano: moderate regression) trace to the same loophole. The constraint says "only cite numbers that appear in the project context" — models read this as authorizing them to deeply engage with plan financials, then derive breakdowns.
- **Impact**: Directly targets the 4× HKD regression. Affects haiku and gpt-oss-20b (the two models with significant regressions). A code fix cannot substitute here because the model's downstream reasoning (deriving 30% of a real budget) happens before output, not in the output.
- **Effort**: Low — two-line prompt change at lines 113–117 and 232 in `identify_potential_levers.py`.
- **Risk**: Overly restrictive wording could cause models to omit legitimate quantitative context (e.g., if the plan states HK$470M, models should still be able to reference that exact figure). The fix must allow verbatim citation while prohibiting derivation.

### 2. Align `review_lever` length target across field description and system prompt
- **Type**: prompt change
- **Evidence**: B2 (code_claude), Finding 4 (insight_claude). Line 127 says "1–2 sentences"; line 260 says "one sentence (20–40 words)". PR #475 created this inconsistency by updating the field description without updating section 6. Haiku's review averages ~310 chars (~60 words), consistent with following the more permissive field description.
- **Impact**: Resolves the contradictory signal that prevented Fix 1 from having any effect. Affects all models that read both the Pydantic schema and the system prompt (primarily haiku and any other structured-output-aware models).
- **Effort**: Low — single-line fix. The authoritative target must be decided first: OPTIMIZE_INSTRUCTIONS line 84 says "Keep review_lever examples concise and enforce a length cap" — this favors "one sentence (20–40 words)" as the stricter target. The field description at line 127 should be changed to match.
- **Risk**: Low. No structural change.

### 3. Document arithmetic derivation pattern in OPTIMIZE_INSTRUCTIONS
- **Type**: prompt change (meta-documentation)
- **Evidence**: C2 (insight_claude). The current OPTIMIZE_INSTRUCTIONS block (lines 27–93) documents fabrication at lines 52–54: "Do not invent percentages, cost savings, market-share figures, or performance deltas." This does not distinguish direct invention from arithmetic derivation. The pattern — model sees HK$470M, computes 30%=HK$141M, presents as fact — is a distinct failure mode that future analysis agents and prompt authors should recognize.
- **Impact**: Low direct impact on current runs, but prevents regression in future optimization iterations by giving analysis agents the vocabulary to recognize and flag the pattern early. Affects OPTIMIZE_INSTRUCTIONS quality.
- **Effort**: Very low — add 2–3 sentences to the existing "Fabricated numbers" bullet in OPTIMIZE_INSTRUCTIONS.
- **Risk**: None.

### 4. Post-processing numeric cross-reference validation
- **Type**: code fix
- **Evidence**: C1 (insight_claude), I4 (code_claude). After the LLM returns lever output, a lightweight regex pass could extract dollar amounts and percentages from `consequences` and `options`, check each against the `user_prompt` for verbatim presence, and trigger a targeted retry with the specific fabricated value named. This would catch derivation patterns that prompt constraints miss.
- **Impact**: Model-agnostic code fix — benefits all models. Particularly valuable for the haiku domain-extrapolation case (HK$75M Film Development Fund subsidy) where even a perfect prompt constraint may not prevent domain-knowledge-based fabrication. Adds latency only when fabrication is detected.
- **Effort**: Medium — requires a regex extraction step, a presence check against user_prompt, and a retry loop with a targeted correction message in the lever cleaning block (lines 356–378).
- **Risk**: False positives (flagging numbers that are genuinely in the plan but formatted differently, e.g. "470 million" vs "HK$470M") could cause unnecessary retries. Requires careful regex design. Also increases token cost on fabrication-heavy plans/models.

### 5. Diversify rhetorical structure of `review_lever` examples
- **Type**: prompt change
- **Evidence**: I3 (code_claude), OPTIMIZE_INSTRUCTIONS lines 76–82. The three examples in system prompt section 4 (lines 247–249) all follow a "trade-off + exception/reversal" template ("stabilizes X, but Y burden…", "requires X overhead, so Y does not halve Z", "reduces X on paper, but Y can correlate all three"). OPTIMIZE_INSTRUCTIONS explicitly warns against shared sentence patterns and "reusable transitional phrases that fit any domain." Haiku's review_lever outputs following a "X trade-off; Y unaddressed gap" structure is consistent with structural template lock.
- **Impact**: Medium-term quality improvement. Reduces sentence-pattern template lock in review_lever, particularly for haiku and weaker models. Affects all plans.
- **Effort**: Low to medium — rewriting the three examples to span distinct rhetorical structures (e.g., one using a conditional, one a comparison, one a causal chain) and distinct domains. Must not introduce new reusable phrases per OPTIMIZE_INSTRUCTIONS.
- **Risk**: Changing examples risks introducing new template patterns. Requires careful drafting and a validation run.

---

## Recommendation

**Fix Direction 1 first: extend the anti-fabrication constraint to explicitly prohibit arithmetic derivation.**

This is the only change that directly addresses the 4× HKD fabrication regression — the single most significant regression introduced across the PR #475 evaluation. Every other open issue (length inconsistency, example structure, post-processing validation) is secondary to the quality regression where models are now generating more fabricated financial figures than before the fix was supposed to prevent them.

**What to change — file, lines, exact wording:**

**File:** `identify_potential_levers.py`

**Location 1:** `Lever.consequences` field description, lines 113–117.

Current:
```python
"Never invent percentages, costs, or timeframes — only cite numbers that appear in the project context. "
```

Replace with:
```python
"Never invent percentages, costs, or timeframes. "
"Do not perform arithmetic on plan numbers to produce derived figures — "
"if a specific sub-allocation, percentage split, or per-unit price is not stated "
"verbatim in the project context, omit it entirely. "
"Only reference numbers that appear word-for-word in the project context. "
```

**Location 2:** System prompt section 2, line 232.

Current:
```
Never invent percentages, costs, or timeframes — only cite numbers that appear in the project context.
```

Replace with:
```
Never invent percentages, costs, or timeframes. Do not perform arithmetic on plan numbers to produce derived figures — if a specific sub-allocation, percentage split, or per-unit price is not stated verbatim in the project context, omit it entirely. Only reference numbers that appear word-for-word in the project context.
```

**Rationale for this specific wording:**
- "Do not perform arithmetic" directly closes the logical gap: models are currently treating derivation from real numbers as compliant.
- "if … not stated verbatim in the project context, omit it entirely" shifts the constraint from a permission floor ("only cite from context") to a strict ceiling ("only verbatim").
- "word-for-word" adds emphasis that the number must appear as-is, not as the output of the model's domain knowledge about what a Film Development Fund might allocate.

**Also include Direction 2 in the same PR** (low effort, directly caused by PR #475): update system prompt section 6 (line 260) from `"one sentence (20–40 words)"` to `"1–2 sentences (up to 60 words)"` to match the field description at line 127, or update the field description to match the system prompt. Either direction resolves the contradiction; matching the more permissive "1–2 sentences" is consistent with what was intended by PR #475.

---

## Deferred Items

- **I4 / post-processing numeric validation** (Direction 4): Worth building, but higher effort and prompt constraints should be tried first. If Direction 1 does not reduce fabrication sufficiently, add code-level numeric cross-referencing as a follow-up.

- **I3 / rhetorical structure diversification** (Direction 5): Low urgency since there are no active template-lock complaints in the current batch. Schedule for the next quality improvement round after fabrication regression is resolved.

- **I5 / runner.py warning threshold** (code_claude): `if actual_calls < 3` generates false positives for models that legitimately stop after 2 calls (7–8 levers/call). The threshold should be `< 2` or conditioned on lever count. Very low urgency — log noise only, does not affect output quality.

- **I6 / anti-fabrication constraint duplication**: Speculative hypothesis that duplicating the constraint in both the Pydantic field description and system prompt amplifies model engagement with plan financials. Worth a controlled experiment (remove from field description, keep in system prompt) only after Direction 1 has been measured, to isolate the variable.

- **B1 / closure capture**: Latent risk if `LLMExecutor.run()` is ever made async. Leave a code comment documenting the risk; a default-argument capture (`def execute_function(llm: LLM, _msgs=messages_snapshot)`) is the safe fix if async execution is planned.

- **S2 / second-call re-exposure to full financial context**: For plans with heavy financial data, the second-call prompt re-injects the full user_prompt including all HK$ figures, structurally pushing the model toward financial levers on subsequent calls. Monitor whether Direction 1 resolves this or whether the second-call prompt needs a "no new financial figures" addendum for subsequent calls only.
