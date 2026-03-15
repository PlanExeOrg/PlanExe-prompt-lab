# Codex Insight: identify_potential_levers (analysis 8)

Scope examined:
- Prompt: `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`
- History runs: `history/0/60_identify_potential_levers` through `history/0/66_identify_potential_levers`
- Baseline reference set: `baseline/train/*/002-9-potential_levers_raw.json` and `baseline/train/*/002-10-potential_levers.json`
- Code checked for explanation of regressions: `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:73`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:192`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244`, and `../PlanExe/prompt_optimizer/runner.py:93`

I treated the baseline as a comparison set, not as a perfect gold standard. Baseline outputs are structurally steadier than some current runs, but they also contain duplicate lever names and often miss the newer prompt’s stronger trade-off / radical-option expectations.

## Negative Things

- **N1 — The biggest regression is a prompt/code contract conflict around lever count.** The registered prompt says “EXACTLY 5 levers per response” in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`, but the step code still allows 5–7 levers (`../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78`) and explicitly asks later calls to “Generate 5 to 7 MORE levers” (`../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`). That contradiction shows up directly in saved artifacts: run 61 raw responses are `[5,7,7]` for every successful plan in `history/0/61_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json`, and the cleaned files save 19 levers per plan in `history/0/61_identify_potential_levers/outputs/*/002-10-potential_levers.json`.
- **N2 — Run 60 is a total operational failure.** All 5 plans fail with `Could not extract json string from output` in `history/0/60_identify_potential_levers/outputs.jsonl`, so it provides no usable comparison set.
- **N3 — Run 64 has a severe field-boundary leak.** In 60/75 saved levers, `consequences` contains review text (`Controls ... Weakness:`). A clear example is `history/0/64_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, where the `consequences` field repeats the same `Controls ... Weakness:` sentence that also appears in `review`.
- **N4 — Run 61 is structurally “successful” but contract-poor.** It saves 95 final levers instead of 75, misses measurable indicators in 66/95 consequences, has 55/285 short label-like options, and has 14 review fields missing either `Controls` or `Weakness:`. Example: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` includes options such as `Hierarchical Governance` and reviews that are only half-complete.
- **N5 — Run 66 is rich but still off-contract in multiple ways.** It fails 1/5 plans in `history/0/66_identify_potential_levers/outputs.jsonl`, over-generates on 4/12 raw responses, saves 19 levers for silo and 17 for GTA/sovereign identity, and its summaries drift into proposing sixth/eighth levers. In `history/0/66_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, one summary explicitly says `Add an eighth lever titled 'Professional Workforce Development & Knowledge Continuity Strategy'`.
- **N6 — Run 65 is fast and clean, but often too generic or scenario-drifting.** For `20250321_silo`, baseline `Resource Allocation Strategy` discusses internal distribution and black-market dynamics in `baseline/train/20250321_silo/002-10-potential_levers.json`, while run 65’s `Silo-Resource Allocation Strategy` shifts into grants, PPPs, and crowdfunding in `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`. This looks more like generic project-finance templating than the plan’s in-world decision space.
- **N7 — Even the best run still has a small leak.** Run 63 is strongest overall, but `history/0/63_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains a `consequences` field for `Modular Deep-Site Construction Strategy` that ends with `Weakness: ...`, showing that the current prompt still does not fully isolate field boundaries.

## Positive Things

- **P1 — Run 63 is the best overall balance of richness and compliance.** It succeeds on all 5 plans, reaches 75/75 unique final lever names and 225/225 unique options, has 0 measurable-indicator misses, and only 5 chain-format misses.
- **P2 — Run 62 is the best “compact but still strategic” failed batch.** It only saves 60 levers because one plan fails, but the 4 successful plans have 59/60 unique names, 0 measurable-indicator misses, and relatively strong explicit trade-off language. `history/0/62_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` is a good example of concise, quantified consequences with a real trade-off.
- **P3 — Run 65 is the best operational performer.** It is the only fully successful run under 40 seconds average duration (`history/0/65_identify_potential_levers/outputs.jsonl`), while also maintaining 15 final levers per plan and 0 chain / 0 measurable-indicator misses.
- **P4 — The new prompt can clearly elicit more unique content than baseline.** Baseline final files contain only 52 unique names across 75 final levers, while runs 63 and 64 reach 75/75 and run 65 reaches 74/75.
- **P5 — Baseline is still useful as a domain-specificity anchor.** Although baseline repeats names inside plans (for example, `Technological Adaptation Strategy`, `Resource Allocation Strategy`, and `External Relations Protocol` repeat in `baseline/train/20250321_silo/002-10-potential_levers.json`), it often stays closer to the scenario’s native tensions than runs 61 or 65.

## Comparison

Relative to baseline, this batch improves **diversity** but is still unstable on **contract compliance**.

- **Diversity:** baseline has 52/75 unique final names and an average of 4.4 repeated names per plan. Runs 63 and 64 eliminate intra-plan name duplication entirely, and run 65 nearly does so.
- **Count discipline:** baseline always saves 15 final levers per plan. Runs 61 and 66 regress badly here by saving 19 and 17 lever files because later calls can still emit 7 levers.
- **Measured consequences:** baseline misses measurable indicators in 21/75 consequences. Runs 62, 63, 64, 65, and 66 all hit 0 misses on this metric, so the prompt is working on numerical specificity.
- **Field separation:** baseline has no `Controls`/`Weakness:` leakage into `consequences`. Run 64 regresses sharply (60/75 leaks), and run 63 still has one isolated leak.
- **Trade-off phrasing:** baseline already underperforms here (63/75 misses by my heuristic), but run 65 is even weaker at 73/75 misses despite otherwise clean structure. Runs 62 and 63 are materially better than baseline on this dimension.
- **Summary discipline:** baseline summaries all use the requested `Add ...` pattern in raw outputs; run 66 falls to 1/12, and run 62 falls to 4/12. This matters because later synthesis may want to reuse those summaries as structured critique, not free-form essays.

My ranking for this batch is:

1. **Run 63 (`openai-gpt-5-nano`)** — best overall quality; slow.
2. **Run 65 (`openrouter-openai-gpt-4o-mini`)** — best operational run; shallower and more generic.
3. **Run 62 (`openrouter-openai-gpt-oss-20b`)** — good successful outputs, but only 4/5 reliable.
4. **Run 66 (`anthropic-claude-haiku-4-5-pinned`)** — rich reasoning, but count/summary/format drift is too large.
5. **Run 64 (`openrouter-qwen3-30b-a3b`)** — structurally valid JSON, but field contamination makes it hard to trust.
6. **Run 61 (`ollama-llama3.1`)** — overgeneration and generic templating outweigh the 5/5 completion rate.
7. **Run 60 (`openrouter-nvidia-nemotron-3-nano-30b-a3b`)** — unusable.

## Quantitative Metrics

### Operational / Raw-output metrics

| Set | Model | Success | Avg duration (s) | Raw responses found | Raw responses with !=5 levers | Final levers saved | Summarys using `Add ...` pattern |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | n/a | 5/5 | n/a | 15 | 0 | 75 | 15/15 |
| 60 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | n/a | 0 | 0 | 0 | 0/0 |
| 61 | ollama-llama3.1 | 5/5 | 101.0 | 15 | 10 | 95 | 10/15 |
| 62 | openrouter-openai-gpt-oss-20b | 4/5 | 83.3 | 12 | 0 | 60 | 4/12 |
| 63 | openai-gpt-5-nano | 5/5 | 235.1 | 15 | 0 | 75 | 14/15 |
| 64 | openrouter-qwen3-30b-a3b | 5/5 | 121.3 | 15 | 0 | 75 | 15/15 |
| 65 | openrouter-openai-gpt-4o-mini | 5/5 | 37.5 | 15 | 0 | 75 | 15/15 |
| 66 | anthropic-claude-haiku-4-5-pinned | 4/5 | 119.3 | 12 | 4 | 68 | 1/12 |

### Uniqueness metrics

| Set | Unique final names | Unique final options | Unique raw names | Avg repeated names per plan |
|---|---:|---:|---:|---:|
| Baseline | 52/75 | 225/225 | 52/75 | 4.4 |
| 61 | 85/95 | 276/285 | 85/95 | 2.0 |
| 62 | 59/60 | 180/180 | 59/60 | 0.0 |
| 63 | 75/75 | 225/225 | 75/75 | 0.0 |
| 64 | 75/75 | 225/225 | 75/75 | 0.0 |
| 65 | 74/75 | 225/225 | 74/75 | 0.2 |
| 66 | 68/68 | 204/204 | 68/68 | 0.0 |

### Average field lengths (characters)

| Set | Name | Consequences | Option | Review | Raw summary |
|---|---:|---:|---:|---:|---:|
| Baseline | 27.7 | 279.5 | 150.2 | 152.3 | 443.7 |
| 61 | 33.3 | 148.4 | 81.6 | 142.0 | 213.3 |
| 62 | 34.0 | 331.2 | 100.4 | 129.6 | 589.7 |
| 63 | 45.8 | 477.8 | 126.7 | 153.7 | 487.7 |
| 64 | 35.0 | 359.4 | 70.2 | 140.9 | 331.9 |
| 65 | 36.5 | 252.2 | 116.4 | 156.6 | 414.3 |
| 66 | 55.6 | 849.1 | 285.3 | 368.3 | 1125.8 |

### Constraint-violation metrics

| Set | Chain misses | No measurable indicator | No explicit trade-off | Review missing `Controls` | Review missing `Weakness:` | Short options | Weak radical option |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 5 | 21 | 63 | 0 | 0 | 0 | 42 |
| 61 | 0 | 66 | 92 | 6 | 8 | 55 | 72 |
| 62 | 15 | 0 | 39 | 0 | 0 | 0 | 18 |
| 63 | 5 | 0 | 21 | 0 | 0 | 0 | 13 |
| 64 | 0 | 0 | 12 | 0 | 0 | 10 | 41 |
| 65 | 0 | 0 | 73 | 0 | 0 | 0 | 44 |
| 66 | 58 | 0 | 54 | 0 | 0 | 0 | 30 |

### Template leakage / cross-call duplication metrics

| Set | `Controls` / `Weakness:` leaked into `consequences` | Bracket placeholder leak in content | Avg repeated names per plan |
|---|---:|---:|---:|
| Baseline | 0 | 0 | 4.4 |
| 61 | 0 | 0 | 2.0 |
| 62 | 0 | 0 | 0.0 |
| 63 | 1 | 0 | 0.0 |
| 64 | 60 | 1 | 0.0 |
| 65 | 0 | 0 | 0.2 |
| 66 | 0 | 0 | 0.0 |

## Evidence Notes

- **Prompt/code conflict is directly visible in source.** The prompt requires exactly 5 levers in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`, but `DocumentDetails.levers` allows 5–7 at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78`, and later calls explicitly ask for `5 to 7 MORE levers` at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`.
- **The step currently flattens all raw levers without count repair.** `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244` through `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:247` simply extend `levers_raw` with every response’s levers. That behavior matches run 61’s 19-lever final files and run 66’s 17/19-lever final files.
- **Run 64 contamination is not hypothetical.** In `history/0/64_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, the first few saved levers have `consequences` that end with `Controls ... Weakness: ...`, and the same text is repeated in the adjacent `review` field.
- **Run 64 also has a literal bracket placeholder in summary text.** `history/0/64_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json` includes `Add 'Employee Well-Being Infrastructure Strategy' to [Legal Compliance Framework Strategy]`.
- **Run 61 genericity is easy to audit.** In `history/0/61_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `Silo-Cohesion Strategy` offers `Hierarchical Governance`, `Decentralized Community Management`, and `Holistic Ecosystem Stewardship`, which are label-like rather than concrete strategies.
- **Baseline duplicates are real, not inferred.** `baseline/train/20250321_silo/002-10-potential_levers.json` repeats `Technological Adaptation Strategy`, `Resource Allocation Strategy`, and `External Relations Protocol` within one merged file.

## Questions For Later Synthesis

- Should the next experiment treat runs 61 and 66 mainly as **code-contract failures** rather than prompt failures, since the implementation still invites 5–7 levers on calls 2 and 3?
- Is the project optimizing for **strict saved-output contract** or **maximum strategic richness**? Run 66 is rich but badly off-shape; run 65 is stable but can drift into generic project-management language.
- Should summary quality matter in scoring if `summary` is only present in raw files and not in the cleaned artifact used downstream?
- Should trade-off detection be enforced more literally in prompt or code, given that even baseline and run 65 often imply trade-offs without using strong marker phrases?
- Is there a need for a per-model blacklist or fallback policy for models that repeatedly fail extraction (`60`) or repeatedly leak fields (`64`)?

## Reflect

- The strongest finding here is not model-specific wording quality; it is the **mismatch between the registered prompt and the implementation**. That mismatch can explain why some models output 7 levers even though the current prompt says 5.
- My trade-off and radical-option metrics are heuristic. They are useful for ranking runs, but they are not full semantic judgments. Some entries imply trade-offs without using the literal cues I counted.
- I measured field lengths and uniqueness only on saved artifacts. That means run 60 disappears from content-quality metrics because it never produced usable outputs.
- Baseline remains a useful comparison anchor, but not a perfect target. It is structurally cleaner than runs 61/64/66 in some ways, yet it still underperforms on uniqueness and often misses the newer prompt’s stronger formatting demands.

## Prompt Hypotheses

### H1

**Change:** Add a stronger anti-overgeneration sentence to the system prompt, such as: `Return exactly 5 levers even if any later instruction asks for more; never propose a sixth, seventh, or eighth lever.`

**Evidence:** The current prompt already says exactly 5, but runs 61 and 66 still produce raw response counts of `[5,7,7]` and save 19/17-lever files in `history/0/61_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json` and `history/0/66_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json`.

**Predicted effect:** More models should resist the later-call instruction drift, reducing count violations even before code changes land.

### H2

**Change:** Add an explicit negative example for field separation: `If you write 'Controls' or 'Weakness:' inside consequences, the answer is invalid.`

**Evidence:** Run 64 leaks review text into 60/75 `consequences` fields, and run 63 still has a one-off leak in `history/0/63_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

**Predicted effect:** Cleaner separation between `consequences` and `review`, especially for qwen-like models that appear to merge fields under current wording.

### H3

**Change:** Make the summary format literal and two-part, for example: `Sentence 1 must start with 'One critical missing dimension is ...'. Sentence 2 must start with 'Add ...'. Do not propose a sixth/eighth lever.`

**Evidence:** Run 66 collapses to 1/12 `Add ...` summaries and repeatedly proposes extra levers in `history/0/66_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json`. Run 62 also drifts from the requested summary shape in `history/0/62_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`.

**Predicted effect:** Raw summaries become more reusable as structured critique rather than free-form commentary.

### H4

**Change:** Add stronger domain anchoring language, e.g. `Every lever must clearly reference the plan’s native actors, assets, constraints, or world logic; avoid generic project-finance or corporate strategy language unless the plan itself is about financing.`

**Evidence:** Run 65’s silo output reframes resource allocation around grants, PPPs, and crowdfunding in `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, whereas the baseline silo output focuses on internal distribution and black-market behavior in `baseline/train/20250321_silo/002-10-potential_levers.json`.

**Predicted effect:** Better preservation of plan-specific decision spaces without sacrificing the clean structure seen in run 65.

## Potential Code Changes

### C1

**Change:** Resolve the count contradiction in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` by changing `DocumentDetails.levers` from `min_length=5, max_length=7` to exactly 5, and change later-call text from `Generate 5 to 7 MORE levers` to `Generate 5 MORE levers`.

**Evidence:** Source conflict at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78` and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`; artifact evidence in run 61 and run 66 raw/final files.

**Predicted effect:** Eliminates the main source of 19/17-lever saved files and aligns implementation with the registered prompt.

### C2

**Change:** Add a post-raw validation/repair step before flattening, so outputs with the wrong lever count or obvious field contamination are rejected or retried instead of being saved as-is.

**Evidence:** The current code simply flattens every raw lever at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244`, which allows run 61’s overlong files and run 64’s contaminated consequences to pass into `002-10-potential_levers.json`.

**Predicted effect:** Fewer silently bad “successful” runs, especially for models that emit valid JSON but violate the field contract.

### C3

**Change:** Add explicit validators for cleaned `consequences` and `review` fields, checking for required labels, at least one measurable indicator, and banning `Controls` / `Weakness:` in `consequences`.

**Evidence:** The descriptive intent is already written into `LeverCleaned.consequences` at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:98`, but runs 63 and 64 show that description-only guidance is not enough.

**Predicted effect:** Better enforcement of the saved-output contract across models, independent of prompt adherence.

### C4

**Change:** Add retry / repair behavior in `../PlanExe/prompt_optimizer/runner.py` or the underlying executor path when extraction or structured validation fails.

**Evidence:** `../PlanExe/prompt_optimizer/runner.py:94` constructs `LLMExecutor(llm_models=llm_models)` with no visible retry configuration, and this batch contains one total-failure run (60) plus single-plan failures in runs 62 and 66.

**Predicted effect:** Higher batch completion rate, especially for models that fail on one plan but usually recover on a second attempt.

## Summary

- **Best overall run:** 63 (`openai-gpt-5-nano`) — strongest content/compliance balance, but slow.
- **Best fast run:** 65 (`openrouter-openai-gpt-4o-mini`) — operationally excellent, but watch for generic domain drift and weak explicit trade-off phrasing.
- **Most important root cause:** the code still invites 5–7 levers on later calls, which conflicts with the registered prompt and explains the major overcount regressions in runs 61 and 66.
- **Most serious content bug in this batch:** run 64’s consequence/review leakage; the JSON is valid, but the field boundary is not.
- **Highest-leverage next moves:** fix the code-level count mismatch first (`C1`/`C2`), then strengthen field-boundary validation (`C3`), and only then iterate on prompt wording (`H2`/`H4`).
