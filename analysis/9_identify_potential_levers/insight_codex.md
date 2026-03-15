# Codex Insight: identify_potential_levers (analysis 9)

Scope examined:

- Prompt: `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:1`
- History runs: `history/0/67_identify_potential_levers` through `history/0/73_identify_potential_levers`
- Baseline reference set: `baseline/train/*/002-9-potential_levers_raw.json` and `baseline/train/*/002-10-potential_levers.json`
- Code checked for explanation of regressions: `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:124`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`, and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244`

I used the baseline as a comparison set, not a gold standard. Baseline outputs are weaker on exact uniqueness and measurable consequences, but they avoid the rigid project-prefix naming pattern that this prompt revision appears to trigger.

## Negative Things

- **N1 — The naming-template leak is real, and it is strongest in otherwise-compliant runs.** The registered prompt explicitly gives `"[Domain]-[Decision Type] Strategy"` as the example pattern in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:19`. That exact behavior appears in artifacts: all 15 silo lever names in `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` are `Silo-... Strategy`, all 15 GTA names in `history/0/70_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` are `GTA-... Strategy`, and run 68 even produces `Denmark-Procurement-Strategy Strategy` in `history/0/68_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`.
- **N2 — The step still has a prompt/code contract mismatch on lever count, and runs 68 and 73 visibly follow the code more than the registered prompt.** The registered prompt says “EXACTLY 5 levers per response” in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:4`, but the step schema still accepts 5–7 levers in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78` and later calls still ask for `Generate 5 to 7 MORE levers` in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`. In run 68 the raw response sizes are `[5,7,5]`, `[5,6,7]`, `[5,7,7]`, `[5,7,7]`, `[5,7,7]` across the five plans; the cleaned files therefore save 17–19 levers per plan in `history/0/68_identify_potential_levers/outputs/*/002-10-potential_levers.json`. Run 73 repeats the same pattern in `history/0/73_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json` and also fails `20260310_hong_kong_game` outright in `history/0/73_identify_potential_levers/outputs.jsonl`.
- **N3 — Run 71 has a severe field-boundary leak.** The code repeatedly says consequences must not contain review text in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42` and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:106`, yet 60 of 75 saved levers in run 71 still append `Controls ... Weakness:` inside `consequences`. `history/0/71_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows this pattern on the first several entries.
- **N4 — Run 68 is the weakest successful batch.** It over-generates on 9 of 15 raw responses, saves 92 final levers instead of 75, misses measurable indicators in 62 consequences, leaves 13 reviews without either `Controls` or `Weakness:`, and keeps 7 placeholder-bearing fields. Concrete examples are in `history/0/68_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, where multiple consequences still contain bracket placeholders such as `Immediate: [Invalidate existing power structures] ...`.
- **N5 — Run 73 is insightful but far too verbose and operationally unstable.** It succeeds on only 4 of 5 plans, its average `consequences` length reaches 867.7 characters, average option length reaches 335.5 characters, and three saved levers still miss the required chain format. `history/0/73_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` shows paragraph-sized options and reviews that are much longer than the prompt’s intended compact format.
- **N6 — Run 72 looks clean structurally but still drifts away from the plan’s native decision space.** In `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `Silo-Resource Allocation Strategy` frames the choice as government grants, PPPs, and crowdfunding, whereas the baseline silo artifact `baseline/train/20250321_silo/002-10-potential_levers.json` frames resource allocation around internal quotas, markets, and AI redistribution inside the silo itself.
- **N7 — Run 67 is a complete batch failure.** Every plan errors in `history/0/67_identify_potential_levers/outputs.jsonl`, mostly with `Could not extract json string from output`, so it provides no usable content signal.

## Positive Things

- **P1 — Run 69 is the best overall balance of compliance, depth, and diversity.** It succeeds on all 5 plans, produces exactly 75 final levers, reaches 75/75 unique names and 225/225 unique options, and has zero count, chain, measurable-outcome, review-format, placeholder, or field-boundary violations. `history/0/69_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` opens with `Silo-Construction Strategy`, whose consequences and options are specific, measured, and compact.
- **P2 — Run 70 has the strongest consequence depth.** It also goes 5/5 with no structural violations, and its average `consequences` length (417.5 chars) is the richest in the clean set without becoming as unbounded as run 73. `history/0/70_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` shows well-formed three-step chains with explicit cost, throughput, and oversight trade-offs.
- **P3 — Relative to baseline, runs 69–72 materially improve consequence discipline.** Baseline still misses measurable indicators in 21 of 75 consequences and has only 52 unique names across 75 levers, while runs 69–72 all hit zero measurable misses and three of them reach 75 unique names.
- **P4 — The successful runs largely keep option structure intact.** Every successful run preserves exactly 3 options per lever, and none of runs 69–73 use banned option prefixes such as `Option A:` or `Conservative:` in the saved final outputs.

## Comparison

- **Best overall run:** **69** (`openrouter-openai-gpt-oss-20b`). It is the only run in this batch that is simultaneously fully successful, exactly on-count, fully unique, zero-placeholder, zero-review-leak, and only minimally affected by the naming template (1 narrow domain-prefix case).
- **Runner-up:** **70** (`openai-gpt-5-nano`). Content quality is very high, but the prompt’s naming example exerts much more force here: 25 domain-template names, including all 15 GTA levers and 10 Hong Kong levers.
- **Third:** **72** (`openrouter-openai-gpt-4o-mini`). Structurally excellent, but its naming is the most robotic among the clean runs: 75/75 names end in `Strategy`, 63/75 are hyphenated `... Strategy`, and the entire silo file becomes `Silo-X Strategy`.
- **Fourth:** **71** (`openrouter-qwen3-30b-a3b`). Good uniqueness and count compliance, but the consequence/review boundary is broken badly enough that I would not trust the cleaned files without repair.
- **Fifth:** **73** (`anthropic-claude-haiku-4-5-pinned`). It shows interesting domain reasoning, especially for the parasomnia plan, but it over-generates, over-explains, and loses one plan entirely.
- **Sixth:** **68** (`ollama-llama3.1`). This batch still over-generates, duplicates names, leaves placeholders, and drops required review pieces.
- **Unusable:** **67** (`openrouter-nvidia-nemotron-3-nano-30b-a3b`). Total extraction failure.

Against the baseline, this batch shows a real trade: the new prompt pressures models toward stronger measurable consequences and better exact uniqueness, but the rigid naming example introduces a new style failure that baseline artifacts mostly avoided. Baseline silo names in `baseline/train/20250321_silo/002-10-potential_levers.json` are plain labels such as `Resource Allocation Strategy` and `Social Control Mechanism`; the best-performing current runs often sound more machine-generated even when their metrics are stronger.

## Quantitative Metrics

Definitions used below:

- **Cross-response dup names** = exact lever names repeated across the 3 raw response groups within the same plan.
- **Raw != 5** = raw response groups whose `levers` array did not contain exactly 5 items.
- **Domain-template names** = names matching a plan-specific project prefix plus `Strategy`, e.g. `Silo-Resource Allocation Strategy` or `GTA-World Studio Co-Location Strategy`.
- **Review leak** = `consequences` contains `Controls` or `Weakness:` text that belongs in `review`.

### Coverage and uniqueness


| Set      | Model                   | Plans ok | Final levers | Unique names | Unique options | Cross-response dup names |
| -------- | ----------------------- | -------- | ------------ | ------------ | -------------- | ------------------------ |
| baseline | reference               | 5/5      | 75           | 52           | 225            | 15                       |
| 67       | nemotron-3-nano-30b-a3b | 0/5      | 0            | 0            | 0              | 0                        |
| 68       | llama3.1                | 5/5      | 92           | 77           | 268            | 14                       |
| 69       | gpt-oss-20b             | 5/5      | 75           | 75           | 225            | 0                        |
| 70       | gpt-5-nano              | 5/5      | 75           | 75           | 225            | 0                        |
| 71       | qwen3-30b-a3b           | 5/5      | 75           | 75           | 225            | 0                        |
| 72       | gpt-4o-mini             | 5/5      | 75           | 72           | 225            | 2                        |
| 73       | claude-haiku-4-5        | 4/5      | 69           | 69           | 207            | 0                        |


### Average field length (characters)


| Set      | Name | Consequences | Option | Review |
| -------- | ---- | ------------ | ------ | ------ |
| baseline | 27.7 | 279.5        | 150.2  | 152.3  |
| 68       | 30.0 | 156.6        | 92.5   | 152.0  |
| 69       | 32.1 | 352.4        | 100.5  | 128.3  |
| 70       | 45.9 | 417.5        | 126.4  | 149.2  |
| 71       | 37.3 | 343.3        | 67.1   | 132.8  |
| 72       | 32.1 | 235.2        | 114.7  | 158.0  |
| 73       | 55.3 | 867.7        | 335.5  | 432.6  |


### Constraint violations


| Set      | Raw != 5 | Final count != 15 plans | Chain missing | Measure missing | Review missing either part | Review leak | Placeholder leak |
| -------- | -------- | ----------------------- | ------------- | --------------- | -------------------------- | ----------- | ---------------- |
| baseline | 0        | 0                       | 5             | 21              | 0                          | 0           | 0                |
| 68       | 9        | 5                       | 0             | 62              | 13                         | 0           | 7                |
| 69       | 0        | 0                       | 0             | 0               | 0                          | 0           | 0                |
| 70       | 0        | 0                       | 0             | 0               | 0                          | 0           | 0                |
| 71       | 0        | 0                       | 0             | 0               | 0                          | 60          | 0                |
| 72       | 0        | 0                       | 0             | 0               | 0                          | 0           | 0                |
| 73       | 5        | 3                       | 3             | 0               | 0                          | 0           | 0                |


### Template leakage


| Set      | Names ending `Strategy` | Hyphenated `... Strategy` | Domain-template names |
| -------- | ----------------------- | ------------------------- | --------------------- |
| baseline | 50                      | 0                         | 0                     |
| 68       | 66                      | 36                        | 22                    |
| 69       | 71                      | 41                        | 1                     |
| 70       | 73                      | 47                        | 25                    |
| 71       | 64                      | 19                        | 0                     |
| 72       | 75                      | 63                        | 15                    |
| 73       | 13                      | 9                         | 0                     |


What the numbers mean:

- Runs **69** and **70** are the cleanest by hard constraints.
- Run **72** is deceptively “perfect” on contract metrics while still strongly leaking the prompt’s naming template.
- Run **71** has excellent top-line uniqueness but its 60 review leaks make the saved files low-trust.
- Run **68** and **73** show the practical effect of the exact-5 vs 5–7 mismatch: over-generation moves straight through into cleaned artifacts.

## Evidence Notes

- The old prompt wording is definitely what these runs saw: the raw artifact `history/0/72_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` stores the same `"[Domain]-[Decision Type] Strategy"` line that appears in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:19`.
- Run 72’s silo file is the clearest naming-template exhibit: `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains 15 consecutive `Silo-... Strategy` names.
- Run 70’s GTA file shows the same issue on a different domain: `history/0/70_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` contains 15 `GTA-... Strategy` names.
- Run 68’s sovereign identity file shows that the pattern can become nonsensical: `history/0/68_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` includes `Denmark-Procurement-Strategy Strategy`.
- Run 71’s silo file shows hard field contamination: `history/0/71_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` places `Controls ... Weakness:` inside `consequences`, despite the code’s explicit prohibition in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42`.
- Run 73’s failure is explicit, not inferred: `history/0/73_identify_potential_levers/outputs.jsonl` says the Hong Kong plan failed because the returned list had only 1 lever.
- Baseline still matters as a counterweight: `baseline/train/20250321_silo/002-10-potential_levers.json` uses plainer names and more scenario-native trade-offs for silo governance/resource tensions than run 72’s funding-heavy reframing.

## Questions For Later Synthesis

- Is the project willing to trade a small amount of uniqueness for more human-sounding lever names, or should exact uniqueness remain the stronger objective?
- Should later evaluations rank run 69 above run 70 because of naming naturalness, even though run 70’s consequences are somewhat richer?
- Are we sure the runner/prompt-registration workflow always records the actual prompt text used at execution time, given that the current source prompt in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:143` already says to avoid formulaic patterns while the registered prompt file for this batch still contains the old template example?

## Reflect

### H1

**Change:** Remove the rigid example `"[Domain]-[Decision Type] Strategy"` from the registered prompt and replace it with a negative instruction such as `avoid repeated project-name prefixes across the full lever set`.

**Evidence:** The example is present in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:19`, and the leak is strongest in runs 70 and 72 (`history/0/70_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`).

**Predicted effect:** The clean runs keep their structural gains while dropping the repetitive `Silo-... Strategy` / `GTA-... Strategy` voice.

### H2

**Change:** Add an explicit anti-pattern line for naming, e.g. `Do not start most levers with the same project noun; vary the head noun across the 5 levers.`

**Evidence:** Run 72 is structurally perfect by most metrics but still lands at 15 domain-template names in the silo file. Run 70 does the same for all 15 GTA levers and 10 Hong Kong levers.

**Predicted effect:** Reduces model tendency to satisfy “domain-specific” by mechanically prepending the project name.

### H3

**Change:** Strengthen domain anchoring with a sentence like `Keep options inside the plan’s native operational world; avoid generic financing, PPP, or crowdfunding language unless the plan explicitly centers financing strategy.`

**Evidence:** Run 72’s `Silo-Resource Allocation Strategy` in `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` drifts into grants, PPPs, and crowdfunding, while baseline `baseline/train/20250321_silo/002-10-potential_levers.json` keeps the same lever inside the silo’s internal allocation logic.

**Predicted effect:** Better plan-grounded levers without sacrificing the measurable and review-format gains of runs 69–72.

### H4

**Change:** Add explicit brevity bounds to the prompt, for example `Keep each consequence under ~90 words, each review under ~45 words, and each option to one sentence.`

**Evidence:** Run 73’s averages balloon to 867.7 characters for `consequences`, 432.6 for `review`, and 335.5 for `options`, with examples in `history/0/73_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

**Predicted effect:** Preserves high-information runs while preventing one model from turning every field into a mini-essay.

## Potential Code Changes

### C1

**Change:** Make the schema and follow-up prompt exactly match the registered contract: set `DocumentDetails.levers` to exactly 5 items and change the follow-up call text from `Generate 5 to 7 MORE levers` to `Generate 5 MORE levers`.

**Evidence:** Source mismatch at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78` and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203`; artifact evidence in `history/0/68_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json` and `history/0/73_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json`.

**Predicted effect:** Eliminates 17–19 lever cleaned outputs and reduces avoidable plan failures caused by under/over-length response groups.

### C2

**Change:** Add post-generation validation before flattening raw levers into cleaned levers: reject or retry when `consequences` contains review text, when placeholders remain, or when response groups are not length 5.

**Evidence:** The code currently just flattens all raw levers in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244` through `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:260`. That allows run 68 placeholders and run 71 consequence/review contamination to pass directly into `002-10-potential_levers.json`.

**Predicted effect:** Fewer silent “successful” artifacts that are valid JSON but bad step outputs.

### C3

**Change:** Make prompt provenance single-source and auditable: either generate registered prompt artifacts directly from the runtime system prompt, or save the full prompt text used into run metadata and compare that in analysis.

**Evidence:** The registered prompt file for this batch still contains the rigid template example at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:19`, while the current source prompt in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:143` has already changed to `avoid formulaic patterns or repeated prefixes`.

**Predicted effect:** Future analysis becomes less ambiguous about whether a PR actually changed the prompt used in the evaluated history runs.

## Summary

- **Most important prompt finding:** the rigid naming example strongly leaks into outputs, especially in runs 70 and 72.
- **Best overall run:** **69**, because it is both clean and comparatively natural.
- **Most important code finding:** the exact-5 prompt and 5–7 code path are still misaligned, and that mismatch directly explains runs 68 and 73.
- **Baseline comparison:** newer runs improved measurable consequences and uniqueness, but several also became more formulaic and less human-sounding.
- **Highest-leverage next moves:** prioritize `C1` and `H1`, then add `C2` to stop placeholders/review leaks from being saved as if they were good outputs.

