# Codex Insight: identify_potential_levers (analysis 11)

Scope examined:

- Prompt: `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt`
- History runs: `history/0/81_identify_potential_levers` through `history/0/87_identify_potential_levers`
- Baseline reference set: `baseline/train/*/002-9-potential_levers_raw.json` and `baseline/train/*/002-10-potential_levers.json`
- Source checked for likely causes: `../PlanExe/prompt_optimizer/runner.py:94`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:54`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`, and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:250`

I used the baseline as a comparison set, not a gold standard. The baseline itself still has heavy boilerplate review phrasing and repeated exact lever names, so improvement should be judged relative to that weaker reference, not against perfect prompt compliance.

## Rankings

1. **Run 84 (`openai-gpt-5-nano`)** — best overall balance of quality and reliability: 5/5 successful plans, 90/90 exact-unique names, only 2 missing measurable systemic clauses, and only 1 missing trade-off marker.
2. **Run 83 (`openrouter-openai-gpt-oss-20b`)** — strongest concise batch, but one invalid-JSON failure keeps it behind run 84.
3. **Run 87 (`anthropic-claude-haiku-4-5-pinned`)** — richest content, but too verbose and one plan fails for returning 8 levers.
4. **Run 86 (`openrouter-openai-gpt-4o-mini`)** — fastest reliable run, but strategic consequences are often thin on explicit trade-offs.
5. **Run 85 (`openrouter-qwen3-30b-a3b`)** — structurally reliable, but 56/78 consequences leak review text into the wrong field.
6. **Run 82 (`ollama-llama3.1`)** — reliable but materially shallower than baseline and other successful runs.
7. **Run 81 (`openrouter-nvidia-nemotron-3-nano-30b-a3b`)** — unusable; all 5 plans fail before producing JSON.

## Negative Things

- **N1 — Retry config does not rescue content/format failures.** Run 81 still fails all 5 plans with `Could not extract json string from output` in `history/0/81_identify_potential_levers/outputs.jsonl`. Run 83 still loses `20260311_parasomnia_research_unit` to truncated JSON in `history/0/83_identify_potential_levers/outputs.jsonl`. Run 87 still loses `20250329_gta_game` because the model returned 8 levers, violating the schema in `history/0/87_identify_potential_levers/outputs.jsonl`. The code path in `../PlanExe/prompt_optimizer/runner.py:94` adds retries, but the remaining failures are semantic/schema failures, not obviously transient network faults.
- **N2 — Run 82 satisfies the schema but often misses the intent of the prompt.** In `history/0/82_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `Resource Optimization` uses label-like options such as `Lean Construction Scheduling` and `Material Recycling and Reuse`, and its consequence is only `Immediate: Reduced construction time → Systemic: Lowered resource costs → Strategic: Enhanced scalability`. Quantitatively, run 82 has 80 short options under 50 characters, 57 missing measurable systemic clauses, and 86/86 consequences without an explicit trade-off marker.
- **N3 — Run 85 has a severe field-boundary leak that the current validator misses.** In `history/0/85_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, the `Architectural Storytelling Framework` consequence ends with `Controls authenticity vs. logistical flexibility. Weakness: ...`, even though `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42` explicitly forbids review text inside `consequences`. This contamination appears in 56 of 78 saved levers.
- **N4 — Run 87 over-corrects toward verbosity.** It has the best depth metrics, but average `consequences` length reaches 948 characters, average `review` length reaches 370 characters, and average option length reaches 298 characters. `history/0/87_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows multi-clause, essay-like fields that are much heavier than the prompt’s intended compact structure.
- **N5 — Run 86 is reliable but strategically under-articulated.** It succeeds on all 5 plans and is the fastest run, yet 59 of 89 consequences omit an explicit trade-off marker. Example: `Narrative Depth and Complexity` in `history/0/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` ends `This fosters a loyal player base that drives long-term franchise success.` without the required downside or tension.
- **N6 — The baseline is still repetitive enough that exact uniqueness alone is not a sufficient success metric.** Baseline exact uniqueness is only 52/75, with 22 duplicate exact lever names across raw calls and 61 names ending in generic suffixes like `Strategy`, `Framework`, or `Protocol`. The most extreme case is `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json`, where the final file contains only 5 exact-unique names out of 15 saved levers.
- **N7 — Boilerplate review phrasing remains high across nearly all successful runs.** The prompt itself requires `Controls ... vs. ...` plus `Weakness: ...`, and that turns into robotic repetition: 73/75 baseline reviews match the exact `Weakness: The options ...` template, and the count remains 73 in run 82, 56 in run 83, 90 in run 84, 74 in run 85, 89 in run 86, and 81 in run 87.

## Positive Things

- **P1 — Run 84 is the clearest improvement over baseline quality.** `history/0/84_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains domain-shaped names like `Governance architecture for a closed society` and `Life-support and ecosystem resilience`, and the consequences carry both measurable indicators and trade-offs. Across all 90 levers, run 84 has only 2 missing measurable systemic clauses and 1 missing trade-off marker.
- **P2 — Runs 83 through 87 eliminate exact duplicate names across successful plans.** Baseline raw outputs contain 22 duplicate exact names across the five training plans; run 82 reduces that to 13; runs 83, 84, 85, 86, and 87 all reach 0 exact raw-name duplicates. That suggests the anti-duplication wording in the prompt is working.
- **P3 — Run 83 is the best concise model behavior in this batch.** `history/0/83_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` shows specific, numerically grounded levers such as `Coalition Amplification` and `Policy Framing`, while staying much shorter than run 87. Its averages are 329 characters for `consequences`, 129 for `review`, and 102 for options.
- **P4 — Run 86 is operationally attractive.** It is the fastest fully successful run at 62.2 seconds average over successful plans in `history/0/86_identify_potential_levers/outputs.jsonl`, versus 94.6 for run 82, 98.8 for run 85, and 222.4 for run 84.
- **P5 — Placeholder leakage appears fixed in this batch.** I found 0 bracket-placeholder strings in baseline and in every successful run’s cleaned output files. That is a real improvement over earlier prompt variants, and it means this prompt version is at least not regressing into literal placeholder text.

## Comparison

- **Against baseline, the new prompt clearly improves exact uniqueness and domain specificity in the best runs.** Baseline lands at 52/75 exact-unique names with 61 generic suffix names. Run 84 improves that to 90/90 exact-unique names with only 19 generic suffix names; run 83 reaches 70/70 with only 11 generic suffix names.
- **Against baseline, run 82 is worse on depth even though it is more unique.** Baseline average option length is 150 characters; run 82 drops to 77. Baseline has 0 short options under 50 characters; run 82 has 80. Baseline misses explicit trade-off markers in 28/75 consequences; run 82 misses them in 86/86.
- **Against baseline, runs 83 and 84 are the strongest prompt successes.** They retain uniqueness gains while also improving consequence depth and keeping review leakage at 0. Run 83 improves measurable systemic coverage from 66/75 baseline to 70/70. Run 84 improves it to 88/90 while also expanding field richness.
- **Against baseline, run 85 is mixed.** It improves uniqueness and reduces generic naming, but it introduces a new field-boundary failure that the baseline does not have: 56/78 consequences contain review text in the wrong field.
- **Against baseline, run 86 trades quality for speed.** It removes duplication and generic naming, but it underperforms the baseline on explicit trade-off articulation: 59/89 missing trade-off markers versus 28/75 in baseline.
- **Against baseline, run 87 improves specificity but overshoots brevity and stability.** It is more information-dense than baseline on almost every field, but the added detail comes with one schema failure and much heavier prose.

## Quantitative Metrics

`002-10-potential_levers.json` is the flattened final artifact for all calls, so lever-count contract compliance is judged from `002-9-potential_levers_raw.json` and `outputs.jsonl`, not from the final file’s total lever count.

### Reliability and throughput

| Run | Model | OK plans | Error plans | Success rate | Avg successful duration (s) | Failure mode |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 81 | `openrouter-nvidia-nemotron-3-nano-30b-a3b` | 0 | 5 | 0% | 0.0 | empty JSON extraction |
| 82 | `ollama-llama3.1` | 5 | 0 | 100% | 94.6 | - |
| 83 | `openrouter-openai-gpt-oss-20b` | 4 | 1 | 80% | 92.4 | invalid JSON |
| 84 | `openai-gpt-5-nano` | 5 | 0 | 100% | 222.4 | - |
| 85 | `openrouter-qwen3-30b-a3b` | 5 | 0 | 100% | 98.8 | - |
| 86 | `openrouter-openai-gpt-4o-mini` | 5 | 0 | 100% | 62.2 | - |
| 87 | `anthropic-claude-haiku-4-5-pinned` | 4 | 1 | 80% | 181.2 | too many levers |

### Uniqueness and average field lengths

| Batch | Plans | Levers | Exact-unique names | Avg name chars | Avg consequence chars | Avg review chars | Avg option chars | Raw exact duplicate names |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5 | 75 | 52/75 | 27.7 | 279.5 | 152.3 | 150.2 | 22 |
| Run 81 | 0 | 0 | - | - | - | - | - | - |
| Run 82 | 5 | 86 | 86/86 | 23.2 | 146.3 | 132.5 | 76.7 | 13 |
| Run 83 | 4 | 70 | 70/70 | 27.1 | 329.3 | 128.8 | 101.5 | 0 |
| Run 84 | 5 | 90 | 90/90 | 47.9 | 414.1 | 159.8 | 120.4 | 0 |
| Run 85 | 5 | 78 | 78/78 | 30.6 | 376.0 | 136.1 | 73.8 | 0 |
| Run 86 | 5 | 89 | 89/89 | 35.8 | 255.1 | 154.9 | 112.1 | 0 |
| Run 87 | 4 | 84 | 84/84 | 56.7 | 948.0 | 369.9 | 298.1 | 0 |

### Constraint-oriented quality checks

| Batch | Short options under 50 chars | Missing measurable systemic clause | Missing explicit trade-off marker | Review missing `Controls ... vs.` | Consequence contains review text | Option 3 not longest option |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0 | 9 | 28 | 0 | 0 | 5 |
| Run 82 | 80 | 57 | 86 | 10 | 0 | 48 |
| Run 83 | 16 | 0 | 4 | 0 | 0 | 1 |
| Run 84 | 1 | 2 | 1 | 1 | 0 | 10 |
| Run 85 | 6 | 1 | 0* | 0 | 56 | 38 |
| Run 86 | 0 | 2 | 59 | 0 | 0 | 23 |
| Run 87 | 0 | 0 | 7 | 0 | 0 | 22 |

`*` Run 85’s trade-off score is artificially flattering because many consequences literally embed the `Controls ... Weakness:` review text, which satisfies the marker heuristic for the wrong reason.

### Template leakage and repetition

| Batch | Generic suffix names (`Strategy`, `Framework`, etc.) | Boilerplate `Weakness: The options ...` reviews | Bracket placeholder strings |
| --- | ---: | ---: | ---: |
| Baseline | 61 | 73 | 0 |
| Run 82 | 28 | 73 | 0 |
| Run 83 | 11 | 56 | 0 |
| Run 84 | 19 | 90 | 0 |
| Run 85 | 24 | 74 | 0 |
| Run 86 | 12 | 89 | 0 |
| Run 87 | 9 | 81 | 0 |

## Evidence Notes

- `history/0/81_identify_potential_levers/outputs.jsonl` is the cleanest proof that retry-by-itself is insufficient here: every plan ends with `Could not extract json string from output` and no `002-10-potential_levers.json` files are produced.
- `history/0/82_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows why run 82 underperforms qualitatively: `Resource Optimization` and `Social Structure` are generic, and their options read like labels rather than complete strategic approaches.
- `history/0/83_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` is the best example of concise, numerically grounded output in this batch. `Coalition Amplification` and `Policy Framing` both contain measurable systemic effects and concrete radical options.
- `history/0/84_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` is the strongest positive artifact overall. `Governance architecture for a closed society` uses domain-specific naming, contains measurable outcomes, and ends with a real trade-off.
- `history/0/85_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` is the clearest proof of field contamination: the consequence for `Architectural Storytelling Framework` contains both `Controls ...` and `Weakness:` even though that material belongs only in the review field.
- `history/0/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` illustrates the run 86 pattern: strong structure, measurable systemic clause, but the strategic clause often lacks an explicit downside or countervailing force.
- `history/0/87_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows the upside and downside of run 87 at once: very specific, domain-grounded prose, but also much heavier-than-necessary fields.
- `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` is the best baseline comparison file because it shows both strengths and weaknesses: good domain fit, but only 5 exact-unique names repeated across 15 saved levers.
- `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34` through `:55` explicitly require measurable consequences, trade-offs, and a strict two-sentence review format, so the artifact failures above are genuine contract misses rather than analysis preference calls.
- `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203` and `:250` explain why exact-name uniqueness improves but silent content failures still pass: the code asks later calls for `5 to 7 MORE levers with completely different names`, then only deduplicates by exact `lever.name` before saving clean output.

## Questions For Later Synthesis

- Is the best next move to optimize around **run 84’s quality profile** or **run 86’s speed/reliability profile**?
- Should the prompt switch from `5 to 7 levers per response` to an exact count such as `6`, given run 87’s overflow failure and the general instability of upper-bound compliance?
- Is boilerplate review phrasing acceptable if the rest of the lever is strong, or should the next prompt revision explicitly relax the review template to recover more natural language?
- Should the next prompt revision explicitly forbid consequence-review contamination with a negative example, or is that better handled in code validation?
- Is exact name uniqueness actually the right objective, or should later synthesis prefer some semantic convergence around the truly central levers of a plan?

## Reflect

The strongest signal in this batch is that the prompt revision successfully improved **exact uniqueness** and, in the better models, **domain-shaped naming**. The biggest remaining quality gap is not duplication; it is **content discipline inside each field**. Run 82 proves that unique names are not enough. Run 85 proves that schema-valid JSON is not enough. Run 87 proves that “more detail” is not automatically better. Run 84 is the clearest evidence that the prompt can work, but it also suggests that the margin between “rich enough” and “too verbose” is model-sensitive.

I also think the PR context matters: the code change in `../PlanExe/prompt_optimizer/runner.py:94` addresses transient failures by enabling retries, but the surviving failures in these artifacts are mostly not retryable transport faults. They are extraction, truncation, and schema/content-compliance failures. That means the next gains probably come more from **prompt tightening plus output validation** than from additional retry tuning.

### H1

**Change:** Add a hard option-shape rule such as `Each option must be one full sentence of at least 12 words and include both an action and the mechanism used.`

**Evidence:** Run 82 has 80 short options under 50 characters, with examples like `Lean Construction Scheduling` and `Material Recycling and Reuse` in `history/0/82_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

**Predicted effect:** Reduces label-like options and should move weak models closer to baseline depth without harming strong models.

### H2

**Change:** Add an explicit negative example for field separation: `Do not put 'Controls ...' or 'Weakness:' inside consequences; if you do, the response is invalid.`

**Evidence:** Run 85 leaks review text into 56/78 consequences, despite the current prohibition in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42` and `:106`.

**Predicted effect:** Reduces the run 85 failure mode and makes the distinction between strategic consequences and critique more salient for weaker models.

### H3

**Change:** Strengthen the consequence template to require one explicit contrast word in the systemic or strategic clause, for example `Use 'but', 'while', or 'however' to name the trade-off.`

**Evidence:** Run 86 misses explicit trade-off markers in 59/89 consequences even though the prompt already asks for trade-offs. The GTA examples in `history/0/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` are clear, measurable, and still too one-sided.

**Predicted effect:** Keeps fast models usable while forcing more balanced strategic reasoning.

### H4

**Change:** Add compact upper bounds such as `Keep each consequence under ~120 words, each review under ~45 words, and each option to one sentence.`

**Evidence:** Run 87 averages 948 characters for `consequences`, 370 for `review`, and 298 for options. The file `history/0/87_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows several fields turning into mini-essays.

**Predicted effect:** Preserves the richness of run 87-style reasoning while reducing bloat and likely improving schema stability.

### H5

**Change:** Ask for an exact lever count per response, ideally `6`, instead of a 5–7 range.

**Evidence:** Run 87 fails one plan with 8 levers in `history/0/87_identify_potential_levers/outputs.jsonl`, and the source still prompts later calls with `Generate 5 to 7 MORE levers` in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`.

**Predicted effect:** Fewer schema-boundary failures and more stable final output sizes across models.

## Potential Code Changes

### C1

**Change:** Add a repair/reask path for content-format failures, not just transport retries. When extraction fails, JSON is truncated, or the lever count exceeds schema bounds, re-prompt with the validation error and ask for corrected JSON.

**Evidence:** Run 81 fails on empty extraction, run 83 on invalid JSON, and run 87 on too many levers in `outputs.jsonl`. The current runner only adds generic retry behavior in `../PlanExe/prompt_optimizer/runner.py:94`.

**Predicted effect:** Converts a meaningful fraction of current hard failures into salvageable retries because the error classes are mostly structured-output failures, not unavailable-service failures.

### C2

**Change:** Add post-generation content validation before `save_clean`: reject or retry outputs when options are too short, when consequences contain `Controls`/`Weakness`, or when consequences lack both a measurable systemic clause and a trade-off marker.

**Evidence:** The code in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:250` through `:264` only deduplicates by exact name and then copies `consequences`, `options`, and `review_lever` straight into the cleaned artifact. That allows run 82’s label-like options and run 85’s consequence-review contamination to be saved as if they were successful outputs.

**Predicted effect:** Fewer silent quality regressions in `002-10-potential_levers.json`, especially from models that pass schema validation but miss the real contract.

### C3

**Change:** Save failed raw model text or structured-output error context into the history directory for each failed plan.

**Evidence:** `outputs.jsonl` gives only the terminal error summary, which makes it easy to see that runs 81, 83, and 87 failed but hard to inspect what the model actually emitted. That weakens later analysis of whether retries, prompts, or model choice caused the failure.

**Predicted effect:** Better auditability for future optimization rounds and more direct evidence for whether a prompt fix or code fix is needed.

## Summary

- **Best overall run:** **84**. It is the only batch here that is both fully successful and consistently strong on uniqueness, field depth, measurability, and trade-off articulation.
- **Most important negative finding:** retries alone do not address the dominant failure classes in this step; content validation and repair loops matter more.
- **Most important prompt finding:** stronger wording improved exact uniqueness, but the next leverage point is field discipline, especially full-sentence options, explicit trade-offs, and clean separation between `consequences` and `review`.
- **Most important code finding:** the cleaner currently trusts any schema-valid payload too much; it should validate content quality before saving.
- **Highest-leverage next moves:** pursue **H1**, **H2**, and **H4** on the prompt side, and **C1** plus **C2** on the code side.
