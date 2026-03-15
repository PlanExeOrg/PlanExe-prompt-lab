# Insight Codex

## Rankings

1. **Run 42 — `openai-gpt-5-nano`**: best overall content quality and strongest contract adherence among successful runs; slower than all other successful models.
2. **Run 44 — `openrouter-openai-gpt-4o-mini`**: fastest and fully reliable, but systematically skips the required trade-off language and drops 6 of 15 summaries.
3. **Run 43 — `openrouter-qwen3-30b-a3b`**: high uniqueness and no null summaries, but severe field-boundary leakage (`Controls` / `Weakness:` text appears inside `consequences`).
4. **Run 41 — `openrouter-openai-gpt-oss-20b`**: good specificity and measurable consequences, but one failed plan and repeated null summaries.
5. **Run 45 — `anthropic-claude-haiku-4-5-pinned`**: rich and detailed, but extremely verbose and operationally fragile (one timeout, very long fields).
6. **Run 40 — `ollama-llama3.1`**: structurally weak despite full completion; summaries are null, one lever has only 2 options, and most content is too terse.
7. **Run 39 — `openrouter-nvidia-nemotron-3-nano-30b-a3b`**: unusable; all 5 plans failed JSON extraction.

## Negative Things

- **Run 39 is a complete reliability failure.** All five plans ended in `ValueError('Could not extract json string from output: ')` in `history/0/39_identify_potential_levers/outputs.jsonl`.
- **Run 40 misses the prompt's substantive requirements even when it returns JSON.** Example: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` starts with `"Dictatorial Rule"` / `"Meritocratic Council"` style options, a minimal consequence string (`"Immediate: Compliance → Systemic: Stability → Strategic: Autocracy"`), and a review with no weakness sentence. Its raw summaries are all `null` in `history/0/40_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`.
- **Run 41 is partially good but incomplete.** It produced stronger, measurable consequences (for example the first Hong Kong lever in `history/0/41_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`), but `history/0/41_identify_potential_levers/outputs.jsonl` shows a hard failure on `20260311_parasomnia_research_unit`, and 6 of its 12 summaries are `null` across the completed plans.
- **Run 43 has the clearest template/field leakage problem.** In `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the first `consequences` field includes `"Controls Cost Efficiency vs. Industrial Resilience. Weakness: ..."`, which belongs in `review`, not `consequences`. Aggregated metrics show this leakage in 45/75 consequences for `Controls` text and 60/75 for `Weakness:` text.
- **Run 44 is structurally clean but semantically underpowered.** The first silo lever in `history/0/44_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` has measurable outcomes, but no explicit trade-off text in `consequences`. Across the run, this happened in 75/75 levers. It also lost 6 summaries to `null`, visible for example in `history/0/44_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`.
- **Run 45 is too long for comfort and appears to push the system into timeout territory.** The first lever in `history/0/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` is high quality but already much longer than baseline. The run then times out on `20260311_parasomnia_research_unit` in `history/0/45_identify_potential_levers/outputs.jsonl` after 432.62 seconds.
- **Baseline training data is not fully aligned with the current prompt.** Baseline files also miss many prompt requirements: 23 duplicate lever names across 75 levers, 21/75 consequences without a measurable indicator, 64/75 consequences without explicit trade-off wording, and 42/75 radical options without an obvious emerging-tech / business-model keyword by heuristic.

## Positive Things

- **Run 42 is the strongest prompt-compliance candidate.** It completes all 5 plans, keeps 75/75 unique lever names, has only 1 duplicated option across 225 options, and has 0 null summaries. The first silo lever in `history/0/42_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` is the clearest positive example: measurable systemic effect, explicit trade-offs, three distinct options, and a concrete weakness.
- **Run 42 meaningfully improves on baseline uniqueness.** Baseline has 52 unique names across 75 levers; run 42 has 75/75 unique names.
- **Run 44 is operationally attractive.** It is the fastest successful run by far (43.5 s average per plan-set from `history/0/44_identify_potential_levers/outputs.jsonl`) while still producing 72 unique names and 225 unique options.
- **Run 43 achieves excellent exact-match uniqueness.** It has 74 unique names out of 75 and 225 unique options out of 225, which is better than baseline on diversity even though its field separation is worse.
- **Run 41 and run 45 both show that richer content is reachable.** Run 41's first Hong Kong lever and run 45's first silo lever demonstrate that the models can generate grounded, domain-specific consequences with measurable impacts instead of generic labels.
- **The raw/final data structure is internally consistent.** In both baseline and successful runs, `002-9-potential_levers_raw.json` contains 3 responses, each with 5 levers, and `002-10-potential_levers.json` contains the merged 15-lever output. This means the prompt's `EXACTLY 5 levers` rule is being honored at the raw-response level even though the final merged artifact has 15 levers.

## Comparison

The most important comparison is **baseline vs. run 42 vs. run 44 vs. run 43**.

- **Baseline** is useful as a shape reference, but not as a pure quality gold standard. It is longer than most runs and often well-formed, yet it repeats lever names heavily within plans. For example, `baseline/train/20250321_silo/002-10-potential_levers.json` repeats `"Technological Adaptation Strategy"`, `"Resource Allocation Strategy"`, and `"External Relations Protocol"`.
- **Run 42** is the best direct improvement over baseline. It removes the baseline repetition problem, preserves strong summaries, and usually satisfies the measurable/trade-off requirements. Its main weakness is speed and some review-format drift (`"Trade-off: ..."` instead of always starting with `"Controls ..."`).
- **Run 44** is the best if throughput matters more than strict prompt adherence. It is much faster than run 42, but it systematically omits explicit trade-offs in `consequences`, which the prompt explicitly asked for in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`.
- **Run 43** is a mixed case: the content is diverse and often crisp, but the model appears to blur field boundaries. That makes it risky for downstream consumers that assume `consequences` and `review` carry different semantics.
- **Run 40** is worse than baseline on nearly every meaningful dimension except exact name uniqueness. It looks like a model that understands the JSON skeleton but not the requested richness.
- **Run 45** is better than baseline on depth but worse on operational reliability. If latency and timeout risk matter, it is not a safe default.

## Quantitative Metrics

### Reliability / Coverage

| Run | Model | Successful plans | Errors | Avg duration (s) |
| --- | --- | ---: | ---: | ---: |
| baseline | baseline reference | 5 | 0 | n/a |
| 39 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0 | 5 | 109.7 |
| 40 | ollama-llama3.1 | 5 | 0 | 78.0 |
| 41 | openrouter-openai-gpt-oss-20b | 4 | 1 | 116.9 |
| 42 | openai-gpt-5-nano | 5 | 0 | 197.3 |
| 43 | openrouter-qwen3-30b-a3b | 5 | 0 | 155.1 |
| 44 | openrouter-openai-gpt-4o-mini | 5 | 0 | 43.5 |
| 45 | anthropic-claude-haiku-4-5-pinned | 4 | 1 | 204.8 |

### Uniqueness / Duplication

| Run | Levers | Unique names | Duplicate names | Duplicate options | Duplicate names within plan | Repeated summaries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 75 | 52 | 23 | 0 | 22 | 0 |
| 39 | 0 | 0 | 0 | 0 | 0 | 0 |
| 40 | 75 | 75 | 0 | 28 | 0 | 10 |
| 41 | 60 | 60 | 0 | 4 | 0 | 3 |
| 42 | 75 | 75 | 0 | 1 | 0 | 0 |
| 43 | 75 | 74 | 1 | 0 | 0 | 2 |
| 44 | 75 | 72 | 3 | 0 | 0 | 3 |
| 45 | 60 | 60 | 0 | 0 | 0 | 0 |

### Average Field Lengths (characters)

| Run | Name | Consequences | Option | Review | Summary |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 27.7 | 279.5 | 150.2 | 152.3 | 443.7 |
| 39 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 40 | 34.7 | 167.0 | 91.4 | 122.6 | 0.0 |
| 41 | 32.7 | 499.7 | 104.9 | 135.9 | 268.6 |
| 42 | 46.8 | 385.6 | 120.8 | 150.0 | 318.6 |
| 43 | 31.7 | 311.5 | 64.7 | 142.2 | 284.4 |
| 44 | 33.0 | 284.5 | 131.1 | 158.1 | 200.9 |
| 45 | 52.5 | 1320.6 | 355.2 | 388.4 | 1219.9 |

### Constraint / Leakage Counts

| Run | Wrong option count | Missing measurable consequence | Missing trade-off in consequence | Review missing `Controls ... vs ...` | Review missing `Weakness:` | Null summaries | Summary missing `Add ... to ...` | Option prefix leakage | Generic option labels | Radical option missing emerging-tech / biz-model keyword* | `consequences` leaked `Controls` | `consequences` leaked `Weakness:` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0 | 21 | 64 | 0 | 0 | 0 | 0 | 0 | 24 | 42 | 0 | 0 |
| 39 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 40 | 1 | 60 | 75 | 17 | 13 | 15 | 15 | 1 | 0 | 55 | 0 | 0 |
| 41 | 0 | 0 | 60 | 0 | 0 | 6 | 10 | 0 | 11 | 15 | 0 | 0 |
| 42 | 0 | 0 | 17 | 14 | 0 | 0 | 0 | 0 | 9 | 12 | 0 | 0 |
| 43 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | 0 | 2 | 45 | 45 | 60 |
| 44 | 0 | 0 | 75 | 0 | 0 | 6 | 6 | 0 | 1 | 42 | 0 | 0 |
| 45 | 0 | 2 | 52 | 0 | 0 | 0 | 11 | 0 | 2 | 17 | 0 | 0 |

\* The emerging-tech / business-model metric is heuristic: I counted missing cases with a keyword scan (`AI`, `blockchain`, `tokenized`, `robotics`, `crowdfunding`, etc.), so this number is directionally useful, not a perfect semantic judgment.

### Metric Notes

- I treated `002-9-potential_levers_raw.json` as the source of truth for the prompt's `exactly 5 levers per response` requirement, because the merged `002-10-potential_levers.json` intentionally contains 15 levers.
- The `Review missing Controls` metric is strict about the presence of a `Controls A vs B.` style phrase. Run 42 is penalized here partly because some reviews say `Trade-off: ...` without the literal `Controls` prefix, even when the underlying reasoning is acceptable.
- `Generic option labels` is an exact-match heuristic for beginnings like `Optimize`, `Improve`, `Balance`, etc.; it is conservative and under-counts semantically generic options.

## Evidence Notes

1. **Prompt contract source**: `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt` requires 5 levers per response, 3 options per lever, measurable systemic effects, explicit trade-offs, `Controls ... vs ...` plus `Weakness:` in review, and one critical missing dimension in the summary.
2. **Raw/final merge behavior**: `baseline/train/20250321_silo/002-9-potential_levers_raw.json` and `history/0/42_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` both show 3 responses, each containing 5 levers; the corresponding `002-10-potential_levers.json` files contain 15 merged levers.
3. **Baseline duplication evidence**: `baseline/train/20250321_silo/002-10-potential_levers.json` repeats `Technological Adaptation Strategy` three times and `Resource Allocation Strategy` twice.
4. **Run 40 structural weakness**: `history/0/40_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` contains `Denmark-Project Governance Strategy` with only 2 options; `history/0/40_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` has three `null` summaries.
5. **Run 42 best-case evidence**: `history/0/42_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` includes `"Prefabricated modules reduce on-site labor hours by 20% ... Throughput increases by 25% ... Trade-offs: speed vs security; cost savings vs governance risk."`
6. **Run 43 field leakage evidence**: `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` puts `"Controls Cost Efficiency vs. Industrial Resilience. Weakness: ..."` inside the `consequences` field.
7. **Run 44 summary loss evidence**: `history/0/44_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` has one non-null summary followed by two `null` summaries.
8. **Run 45 timeout evidence**: `history/0/45_identify_potential_levers/outputs.jsonl` records `APITimeoutError` on `20260311_parasomnia_research_unit` after 432.62 seconds.

## Questions For Later Synthesis

- Should the optimizer prefer **prompt compliance** over **baseline similarity** when baseline artifacts themselves violate several prompt constraints?
- Is run 42's slower but cleaner output preferable to run 44's faster but systematically less compliant output?
- Should run 45's extreme verbosity be considered a quality win or an operational regression, given the timeout evidence?
- Are repeated / null summaries a prompt issue, a parser / schema-validation issue, or a post-processing issue?
- Is the run 43 field-leakage problem best solved with stronger prompt wording, stricter structured-output validation, or both?

## Reflect

### H1

**Change:** Add an explicit negative instruction that `consequences` must never contain `Controls` or `Weakness:` language, and that those phrases belong only in `review`.

**Evidence:** Run 43 leaks review text into `consequences` at high rates (45/75 `Controls`, 60/75 `Weakness:`), with a concrete example in `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

**Predicted effect:** Better field separation and lower risk that downstream consumers misread review text as consequence text.

### H2

**Change:** Add explicit target bands for verbosity, such as a moderate-length consequence and review, plus a ban on label-only options.

**Evidence:** Run 40 is too terse (`avg_option_len = 91.4`, `avg_summary_len = 0.0`), while run 45 is excessively long (`avg_conseq_len = 1320.6`, `avg_summary_len = 1219.9`) and times out once.

**Predicted effect:** More runs in the run-42 / baseline range instead of collapsing into either skeletal or bloated outputs.

### H3

**Change:** Strengthen the prompt's measurable-trade-off language by marking outputs invalid unless the `Systemic:` clause includes a numeric indicator and the `Strategic:` clause or trailing sentence includes an explicit trade-off.

**Evidence:** Run 44 misses trade-off language in 75/75 consequences despite otherwise decent structure; run 40 misses measurable indicators in 60/75 consequences and trade-offs in 75/75.

**Predicted effect:** Fewer superficially valid but strategically bland levers.

### H4

**Change:** Make the summary instruction more literal: require exactly one sentence beginning `One critical missing dimension is ...` and one sentence beginning `Add '...' to ...`.

**Evidence:** Run 40 produces 15/15 null summaries, run 41 has 6 null summaries, and run 44 has 6 null summaries in their raw files.

**Predicted effect:** Better completion consistency for the `summary` field and fewer partially populated raw responses.

### H5

**Change:** Add a diversity instruction that the 3 raw responses for a plan must not reuse the same lever names or summary recommendation.

**Evidence:** Baseline has 22 within-plan duplicate names; run 40 repeats summaries 10 times; run 43 repeats summary text twice with the same `Citizen Engagement Strategy` recommendation in `history/0/43_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`.

**Predicted effect:** More useful merged 15-lever artifacts and less cross-call redundancy.

## Potential Code Changes

### C1

**Change:** Add a post-generation validator that rejects raw responses with null summaries, wrong option counts, missing measurable/trade-off clauses, or field leakage (`Weakness:` inside `consequences`).

**Evidence:** These violations already pass through into saved artifacts in runs 40, 41, 43, and 44.

**Predicted effect:** Fewer low-quality artifacts will survive to `002-10-potential_levers.json`, independent of model choice.

### C2

**Change:** Add cross-response deduplication or diversity scoring before merging the 3 raw responses into the 15-lever final file.

**Evidence:** Baseline has 22 within-plan duplicate names; run 40 and run 43 repeat summary recommendations across responses.

**Predicted effect:** Higher effective diversity in the merged artifact without requiring a better base model.

### C3

**Change:** Add model-specific retry / repair logic for JSON extraction failures and timeout-prone generations.

**Evidence:** Run 39 fails all 5 plans with `Could not extract json string from output`, and run 45 times out on one plan after more than 7 minutes.

**Predicted effect:** Better coverage across weaker or slower models, and fewer wasted runs during prompt experiments.

### C4

**Change:** Separate **baseline similarity scoring** from **prompt-contract compliance scoring** in the evaluation workflow.

**Evidence:** Baseline training artifacts themselves violate multiple current prompt requirements, so a scorer that rewards only similarity may prefer non-compliant outputs.

**Predicted effect:** Future prompt optimization should converge toward outputs that are both baseline-compatible and instruction-faithful, rather than one or the other.

## Summary

- The best current prompt/model pairing in this batch is **run 42**, with **run 44** as the best speed-first fallback.
- The main failure modes are **total parse failure** (run 39), **under-specified content** (run 40), **null summaries / partial completion** (runs 40, 41, 44), **field leakage** (run 43), and **over-verbose timeout risk** (run 45).
- Baseline is a useful reference but not a gold-standard contract target; several of its artifacts are less compliant with the current prompt than run 42.
- The highest-leverage next moves look like: stronger prompt wording around field boundaries and brevity, plus code/workflow validation for null summaries, option counts, trade-off/measurable checks, and cross-response deduplication.
