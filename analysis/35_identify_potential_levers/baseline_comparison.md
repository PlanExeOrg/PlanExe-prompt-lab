# Baseline Comparison: identify_potential_levers

**PR**: #353 — Replace review_lever examples to break template lock
**Analysis dir**: `analysis/35_identify_potential_levers/`
**Baseline**: `baseline/train/` (5 plans, claude-sonnet-3.5, iteration 34 baseline)

## Success Rate

All runs loaded all 5 plans successfully.

| Run | Model | Plans | Successes | Failures |
|-----|-------|-------|-----------|----------|
| 52 | ollama-llama3.1 | 5 | 5 | 0 |
| 53 | openrouter-openai-gpt-oss-20b | 5 | 5 | 0 |
| 54 | openai-gpt-5-nano | 5 | 5 | 0 |
| 55 | openrouter-qwen3-30b-a3b | 5 | 5 | 0 |
| 56 | openrouter-openai-gpt-4o-mini | 5 | 5 | 0 |
| 57 | openrouter-gemini-2.0-flash-001 | 5 | 5 | 0 |
| 58 | anthropic-claude-haiku-4-5-pinned | 5 | 5 | 0 |

Note: Run 58 (Claude Haiku 4.5) had `calls_succeeded=2` for `20250321_silo` and `20260311_parasomnia_research_unit`, meaning one of the three LLM calls failed per plan, but the output file was still produced.

## Quantitative Comparison

### Lever Count per Plan

| Plan | Baseline | llama3.1 | GPT-OSS-20B | GPT-5-nano | Qwen3-30B | GPT-4o-mini | Gemini-2.0-Flash | Claude-Haiku-4.5 |
|------|----------|----------|-------------|------------|-----------|-------------|-----------------|-----------------|
| silo | 15 | 21 | 19 | 18 | 15 | 18 | 19 | 23 |
| gta_game | 15 | 15 | 18 | 18 | 19 | 16 | 19 | 21 |
| sovereign_identity | 15 | 19 | 18 | 18 | 19 | 17 | 12 | 21 |
| hong_kong_game | 15 | 17 | 18 | 18 | 18 | 17 | 18 | 21 |
| parasomnia | 15 | 17 | 18 | 19 | 17 | 17 | 18 | 15 |
| **Average** | **15.0** | **17.8** | **18.2** | **18.2** | **17.6** | **17.0** | **17.2** | **20.2** |

All models produce more levers than the baseline (15.0 avg). Claude Haiku 4.5 produces the most (20.2 avg). Gemini-2.0-Flash has one anomalous plan (sovereign_identity: 12 levers — possible truncation or generation failure).

### Option Count Compliance (exactly 3 options per lever)

| Metric | Baseline | llama3.1 | GPT-OSS-20B | GPT-5-nano | Qwen3-30B | GPT-4o-mini | Gemini-2.0-Flash | Claude-Haiku-4.5 |
|--------|----------|----------|-------------|------------|-----------|-------------|-----------------|-----------------|
| Total levers | 75 | 89 | 91 | 91 | 88 | 85 | 86 | 101 |
| Violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Compliance | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

All models perfectly comply with the 3-options requirement. No violations detected across any run or plan.

### Average Consequences Field Length (chars, per plan averaged across levers)

| Plan | Baseline | llama3.1 | GPT-OSS-20B | GPT-5-nano | Qwen3-30B | GPT-4o-mini | Gemini-2.0-Flash | Claude-Haiku-4.5 |
|------|----------|----------|-------------|------------|-----------|-------------|-----------------|-----------------|
| silo | 286 | 186 | 306 | 264 | 232 | 270 | 329 | 629 |
| gta_game | 279 | 228 | 256 | 296 | 247 | 258 | 365 | 480 |
| sovereign_identity | 265 | 225 | 321 | 278 | 220 | 263 | 347 | 728 |
| hong_kong_game | 269 | 222 | 253 | 267 | 285 | 251 | 366 | 663 |
| parasomnia | 298 | 129 | 309 | 260 | 253 | 266 | 355 | 600 |
| **Average** | **279** | **198** | **289** | **273** | **247** | **262** | **352** | **620** |

Baseline avg ~279 chars. Claude Haiku 4.5 exceeds 2x baseline (620 chars). Gemini-2.0-Flash is 26% above baseline. GPT-OSS-20B matches baseline well. llama3.1 is below baseline, especially on parasomnia (129 chars avg — notably shallow).

### Average Review Field Length (chars, per plan averaged across levers)

| Plan | Baseline | llama3.1 | GPT-OSS-20B | GPT-5-nano | Qwen3-30B | GPT-4o-mini | Gemini-2.0-Flash | Claude-Haiku-4.5 |
|------|----------|----------|-------------|------------|-----------|-------------|-----------------|-----------------|
| silo | 147 | 202 | 145 | 190 | 184 | 206 | 202 | 834 |
| gta_game | 150 | 198 | 144 | 217 | 183 | 234 | 243 | 608 |
| sovereign_identity | 147 | 208 | 172 | 191 | 182 | 231 | 263 | 778 |
| hong_kong_game | 153 | 251 | 140 | 192 | 214 | 209 | 245 | 672 |
| parasomnia | 165 | 175 | 163 | 189 | 222 | 223 | 256 | 636 |
| **Average** | **152** | **207** | **153** | **196** | **197** | **221** | **242** | **706** |

Baseline avg ~152 chars. Claude Haiku 4.5 is 4.6x baseline (706 chars) — extremely verbose. Gemini-2.0-Flash is 59% above baseline. GPT-OSS-20B barely above baseline (153 chars).

### Name Uniqueness (unique names / total per plan)

All experiment runs achieve 1.00 (100%) name uniqueness within each plan. The baseline has lower uniqueness (avg ~0.70) due to repeated lever names across the multi-call outputs: for example, "Resource Allocation Strategy" appears 3x and "Technological Adaptation Strategy" appears 3x in the silo baseline. This structural improvement is consistent across all experimental models.

### Template Leakage ("the options" as grammatical subject in review field)

This is the primary metric targeted by PR #353. The old review_lever examples caused models to generate reviews starting with patterns like "The options don't address...", "The options fail to...", "The options overlook...", etc. — verbatim structural copying of the example template.

Detection method: review field (lowercased) contains "the options" AND at least one of: "don't", "do not", "fail to", "miss ", "overlook", "neglect", "lack ", "assume", "ignore".

**Baseline**: 75/75 levers exhibit this pattern (100% leakage). This is expected — the baseline was generated with the old prompt before PR #353.

| Model | Total Levers | Leaky Reviews | Leakage Rate |
|-------|-------------|---------------|--------------|
| Baseline (old prompt) | 75 | 75 | 100% |
| llama3.1 (run 52) | 89 | 6 | 7% |
| GPT-5-nano (run 54) | 91 | 20 | 22% |
| GPT-OSS-20B (run 53) | 91 | 23 | 25% |
| Claude-Haiku-4.5 (run 58) | 101 | 42 | 42% |
| GPT-4o-mini (run 56) | 85 | 55 | 65% |
| Qwen3-30B (run 55) | 88 | 59 | 67% |
| Gemini-2.0-Flash (run 57) | 86 | 79 | 92% |

The PR successfully broke template lock for llama3.1, GPT-OSS-20B, and GPT-5-nano. Moderate improvement for Claude Haiku 4.5. Minimal effect on Qwen3-30B and GPT-4o-mini. Gemini-2.0-Flash is nearly unchanged.

## Quality Assessment

### llama3.1 (run 52)
Lever count elevated at 17.8 avg. Consequences fields are short (~198 chars avg) — notably shallow on parasomnia (129 chars avg). Review fields are moderate and largely free of template lock (7% leakage, 6 out of 89 levers). Most reviews are genuinely original criticisms. Options text is terse but structurally correct. Levers are domain-relevant and plan-appropriate throughout.

### GPT-OSS-20B (run 53)
Good breadth at 18.2 avg levers. Consequences length (~289 chars) matches baseline well. Review length (~153 chars) is barely above baseline. Template leakage at 25% (23/91), clustered primarily on silo (10/19 levers) and sovereign_identity (7/18). GTA and Hong Kong plans are completely clean. Sovereign_identity levers are particularly rich (e.g., "Platform Integrity Signal Decoupling," "Resilience Benchmarking Protocol," "Alternative Push Notification Architecture"). Some lever names use "Lever" suffix (e.g., "Narrative Complexity Lever").

### GPT-5-nano (run 54)
Consistent 18.2 avg levers. Consequences (~273 chars) near baseline. Review (~196 chars) above baseline. Template leakage at 22% (20/91), mainly concentrated in gta_game (8 levers) and sovereign_identity (7 levers). Unique silo levers cover original angles (e.g., "Closed-loop utility and agricultural resilience," "Modular construction and staged underground assembly," "Phased commissioning of life-support modules across floors").

### Qwen3-30B (run 55)
Lever count 17.6 avg. Consequences (~247 chars) below baseline. Review (~197 chars) above baseline. Template leakage at 67% (59/88) — very high. The PR only partially worked for Qwen3. gta_game is particularly bad (17/19 levers leak). Reviews structurally follow "The options fail to...", "The options overlook...", "The options don't..." patterns despite the new examples.

### GPT-4o-mini (run 56)
Lever count 17.0 avg. Consequences (~262 chars) near baseline. Review (~221 chars) above baseline. Template leakage at 65% (55/85). GPT-4o-mini reviews consistently use "The options do not address...", "The options overlook..." — strongly templated. Similar failure mode to Qwen3.

### Gemini-2.0-Flash (run 57)
Lever count 17.2 avg. Anomaly: sovereign_identity produced only 12 levers (possible truncation). Consequences (~352 chars) well above baseline (+26%). Review (~242 chars) well above baseline (+59%). Template leakage at 92% (79/86) — nearly identical to baseline behavior. The PR had essentially no effect. Despite richer content (longer fields), the template structure remains fully locked. Almost every review uses "the options" as grammatical subject.

### Claude-Haiku-4.5 (run 58)
Highest lever count at 20.2 avg. Consequences (~620 chars) more than 2x baseline. Review (~706 chars) more than 4x baseline — extremely verbose. Template leakage at 42% (42/101). Some reviews are genuinely original using "Core tension:" prefix (e.g., "Core tension: balancing enrollment speed and sample quality"), while others still use the "the options" pattern. The "Core tension:" prefix is a new structural stereotype not present in baseline. `calls_succeeded=2` on two plans (silo and parasomnia) indicates occasional LLM call failures, though outputs were still produced.

## Model Ranking

1. **llama3.1** (run 52) — Best template lock reduction (7%). Most original review commentary across all plans. Main weakness: shallow consequences fields (~198 chars avg, below baseline 279).
2. **GPT-5-nano** (run 54) — 22% leakage, solid consequences depth (~273 chars), good domain specificity in lever names. Very close to GPT-OSS-20B.
3. **GPT-OSS-20B** (run 53) — 25% leakage, good consequences depth (~289 chars, matching baseline). Leakage concentrated in specific plans only (silo and sovereign_identity).
4. **Claude-Haiku-4.5** (run 58) — Richest overall content (620 chars consequences, 706 chars review), but 42% leakage and extremely verbose reviews (4.6x baseline). Intermittent call failures noted.
5. **Qwen3-30B** (run 55) — 67% leakage. PR had limited effect. Consequences below baseline (~247 chars).
6. **GPT-4o-mini** (run 56) — 65% leakage. Template very persistent despite example swap.
7. **Gemini-2.0-Flash** (run 57) — 92% leakage. Near-unchanged from old template behavior. The example swap had essentially no effect.

## Overall Verdict

**MIXED**: PR #353 successfully broke template lock for llama3.1 (the primary target, 7% residual leakage down from 100%), and also meaningfully helped GPT-OSS-20B (25%) and GPT-5-nano (22%). These three models now produce genuinely original review commentary. However, Qwen3-30B (67%), GPT-4o-mini (65%), Gemini-2.0-Flash (92%), and Claude-Haiku-4.5 (42%) continue to exhibit substantial template lock. The fix effectiveness is model-dependent. All models maintain 100% option-count compliance and produce more levers than the baseline (15.0 avg). The PR achieves its stated goal for the primary target (llama3.1) and is a clear improvement for the three top-ranked models.

## Recommendations

1. **Confirm PR success for llama3.1**: The primary target shows excellent improvement (7% leakage). The PR achieves its stated goal for this model. Iteration 35 is a valid baseline for llama3.1 going forward.

2. **Investigate Gemini-2.0-Flash failure**: At 92% leakage despite new examples, the template lock in Gemini appears structural — possibly related to instruction-following behavior or RLHF alignment toward certain review patterns. May require explicit "do not start review with the options" instructions rather than just example substitution.

3. **Address Qwen3 and GPT-4o-mini**: Both at 65–67% leakage. These models pattern-match on review structure even when examples change. Consider adding explicit anti-pattern instructions alongside example replacement for these models.

4. **Claude Haiku 4.5 verbosity**: Review fields averaging 706 chars (4.6x baseline) may be excessive for downstream processing. Consider adding length guidance to the prompt when using Haiku-class models.

5. **llama3.1 consequences depth**: At 198 chars avg (below baseline 279 chars), the consequences field is the main quality weakness for llama3.1. Additional chain-of-thought or elaboration guidance may help smaller local models generate richer consequences text.

6. **Baseline update**: The baseline itself exhibits 100% template leakage in review fields (generated by the old prompt). Future baseline versions should be regenerated with the fixed prompt to establish a clean reference point for this metric.
