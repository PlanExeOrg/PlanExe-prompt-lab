# Baseline Comparison: identify_potential_levers

PR: [https://github.com/PlanExeOrg/PlanExe/pull/346](https://github.com/PlanExeOrg/PlanExe/pull/346)
Change: Add `lever_type` and `decision_axis` fields to lever schema.

## Success Rate


| Model (run)                                | Succeeded | Total | Rate | Failures                                                                                       |
| ------------------------------------------ | --------- | ----- | ---- | ---------------------------------------------------------------------------------------------- |
| baseline (gold standard)                   | 5         | 5     | 100% | —                                                                                              |
| ollama-llama3.1 (run 31)                   | 3         | 5     | 60%  | 20250329_gta_game (validation, options < 3), 20260310_hong_kong_game (validation, options < 3) |
| openrouter-openai-gpt-oss-20b (run 32)     | 5         | 5     | 100% | —                                                                                              |
| openai-gpt-5-nano (run 33)                 | 5         | 5     | 100% | —                                                                                              |
| openrouter-qwen3-30b-a3b (run 34)          | 5         | 5     | 100% | —                                                                                              |
| openrouter-openai-gpt-4o-mini (run 35)     | 5         | 5     | 100% | —                                                                                              |
| openrouter-gemini-2.0-flash-001 (run 36)   | 5         | 5     | 100% | —                                                                                              |
| anthropic-claude-haiku-4-5-pinned (run 37) | 5         | 5     | 100% | —                                                                                              |


Notes:

- Run 31 (llama3.1) failures were pre-PR validation failures where the model produced options arrays with fewer than 3 items. Those plans are missing from analysis.
- Run 34 (qwen3-30b) sovereign_identity plan had calls_succeeded=2 but still produced output; all 5 plans have output files.
- Run 36 (gemini-flash) sovereign_identity produced only 6 levers vs 15 in baseline (explained below).

---

## Quantitative Comparison

All figures are averages across successful plans. Baseline averages are across all 5 plans (75 levers total).

### Lever Count


| Plan                              | Baseline | llama3.1   | gpt-oss-20b | gpt-5-nano | qwen3-30b | gpt-4o-mini | gemini-flash | haiku-4-5 |
| --------------------------------- | -------- | ---------- | ----------- | ---------- | --------- | ----------- | ------------ | --------- |
| 20250321_silo                     | 15       | 18         | 18          | 19         | 19        | 17          | 18           | 21        |
| 20250329_gta_game                 | 15       | — (failed) | 18          | 18         | 13        | 16          | 18           | 21        |
| 20260308_sovereign_identity       | 15       | 16         | 19          | 18         | 20        | 14          | **6**        | 21        |
| 20260310_hong_kong_game           | 15       | — (failed) | 18          | 18         | 20        | 17          | 18           | 21        |
| 20260311_parasomnia_research_unit | 15       | 13         | 18          | 18         | 17        | 16          | 18           | 21        |
| **Avg per plan**                  | **15.0** | **15.7**   | **18.2**    | **18.2**   | **17.8**  | **16.0**    | **15.6**     | **21.0**  |
| Plans succeeded                   | 5        | 3          | 5           | 5          | 5         | 5           | 5            | 5         |


Note: gemini-flash sovereign_identity delivered only 6 levers (vs baseline 15), likely a truncation issue.

### Options Compliance (exactly 3 options per lever)


| Model                             | Levers with 3 options | Violations | Violation Rate |
| --------------------------------- | --------------------- | ---------- | -------------- |
| baseline                          | 75/75                 | 0          | 0%             |
| ollama-llama3.1                   | 47/47                 | 0          | 0%             |
| openrouter-openai-gpt-oss-20b     | 91/91                 | 0          | 0%             |
| openai-gpt-5-nano                 | 91/91                 | 0          | 0%             |
| openrouter-qwen3-30b-a3b          | 89/89                 | 0          | 0%             |
| openrouter-openai-gpt-4o-mini     | 80/80                 | 0          | 0%             |
| openrouter-gemini-2.0-flash-001   | 78/78                 | 0          | 0%             |
| anthropic-claude-haiku-4-5-pinned | 105/105               | 0          | 0%             |


All runs that produced output passed the 3-options constraint. The two llama3.1 failures were rejected before saving output, so no violations appear in output files.

### Description Length (average characters per lever)


| Model                             | Avg Consequences | Avg Review |
| --------------------------------- | ---------------- | ---------- |
| baseline                          | 279              | 152        |
| ollama-llama3.1                   | 216              | 226        |
| openrouter-openai-gpt-oss-20b     | 275              | 142        |
| openai-gpt-5-nano                 | 304              | 190        |
| openrouter-qwen3-30b-a3b          | 235              | 165        |
| openrouter-openai-gpt-4o-mini     | 244              | 179        |
| openrouter-gemini-2.0-flash-001   | 338              | 247        |
| anthropic-claude-haiku-4-5-pinned | **549**          | **523**    |


Baseline range: consequences 265–298 chars; review 147–165 chars.

- haiku-4-5 produces consequences roughly 2x baseline length and review roughly 3.5x baseline. The extra verbosity is substantive (detailed multi-paragraph analysis, quantified trade-offs) rather than padding.
- gemini-flash consequences are slightly above baseline; review is above baseline.
- gpt-oss-20b and qwen3-30b are nearest to baseline in consequences; gpt-oss-20b review is slightly below baseline.
- llama3.1 consequences are below baseline; review is above.

### Name Uniqueness


| Model                             | Unique Names / Total | Uniqueness Rate |
| --------------------------------- | -------------------- | --------------- |
| baseline                          | 53/75                | 70.7%           |
| ollama-llama3.1                   | 47/47                | 100%            |
| openrouter-openai-gpt-oss-20b     | 91/91                | 100%            |
| openai-gpt-5-nano                 | 91/91                | 100%            |
| openrouter-qwen3-30b-a3b          | 89/89                | 100%            |
| openrouter-openai-gpt-4o-mini     | 79/80                | 98.8%           |
| openrouter-gemini-2.0-flash-001   | 78/78                | 100%            |
| anthropic-claude-haiku-4-5-pinned | 105/105              | 100%            |


The baseline itself has 22 non-unique names (e.g., "Resource Allocation Strategy", "Technological Adaptation Strategy", "Information Control Policy" each appear in multiple call outputs for the same plan set). All experiment models produce fully unique names per lever set (gpt-4o-mini has one duplicate across 5 plans).

### lever_type Field


| Model                             | lever_type present | Notes                  |
| --------------------------------- | ------------------ | ---------------------- |
| baseline                          | 0/75               | Not in baseline schema |
| ollama-llama3.1                   | 0/47               | Not present            |
| openrouter-openai-gpt-oss-20b     | 0/91               | Not present            |
| openai-gpt-5-nano                 | 0/91               | Not present            |
| openrouter-qwen3-30b-a3b          | 0/89               | Not present            |
| openrouter-openai-gpt-4o-mini     | 0/80               | Not present            |
| openrouter-gemini-2.0-flash-001   | 0/78               | Not present            |
| anthropic-claude-haiku-4-5-pinned | 0/105              | Not present            |


**lever_type is absent in all runs including the post-PR experiment runs.** The PR (#346) introduced `lever_type` as a field in the code, but none of the experiment runs (32–37 which use the new prompt/code) produce a `lever_type` field in their JSON outputs. The `lever_classification` field (format: `"<type> — <description>"`) is present in all experiment outputs and carries the type taxonomy, but it is not the separate `lever_type` field expected by the new schema.

### decision_axis Field


| Model                       | decision_axis present | Notes                     |
| --------------------------- | --------------------- | ------------------------- |
| baseline                    | 0/75                  | Not in baseline schema    |
| All experiment runs (31–37) | 0                     | Not present in any output |


**decision_axis is absent in all runs.** This is a new field introduced in PR #346. Its absence from all experiment outputs (including runs 32–37) indicates the new schema fields are not being populated in the saved JSON, or the runs predate or do not reflect the fully applied PR.

### lever_classification Field Validity

All experiment runs include a `lever_classification` field (absent from baseline). The expected vocabulary is: `methodology`, `execution`, `governance`, `dissemination`, `product`, `operations`.


| Model                             | Levers with valid type | Invalid type count | Invalid examples                                                                                                                         |
| --------------------------------- | ---------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| baseline                          | N/A                    | N/A                | —                                                                                                                                        |
| ollama-llama3.1                   | 36/47                  | 11                 | "ecosystem", "social hierarchy", "resource prioritization", "information control", "participant_recruitment", "procurement", "standards" |
| openrouter-openai-gpt-oss-20b     | 91/91                  | 0                  | —                                                                                                                                        |
| openai-gpt-5-nano                 | 90/91                  | 1                  | "methods"                                                                                                                                |
| openrouter-qwen3-30b-a3b          | 89/89                  | 0                  | —                                                                                                                                        |
| openrouter-openai-gpt-4o-mini     | 79/80                  | 1                  | "sound design"                                                                                                                           |
| openrouter-gemini-2.0-flash-001   | 78/78                  | 0                  | —                                                                                                                                        |
| anthropic-claude-haiku-4-5-pinned | 105/105                | 0                  | —                                                                                                                                        |


llama3.1 has substantial type leakage: 23% of levers use custom type labels that are not in the controlled vocabulary. All newer models (runs 32–37) nearly fully comply.

### Template Leakage

Checked for verbatim copying of prompt example phrases ("This lever controls", "by choosing between A, B, and C", "example lever name"). Initial false-positive check revealed "option A/B" matches were substring hits within words like "architecture" or within real option text. After manually verifying hits:


| Model               | Confirmed template leakage |
| ------------------- | -------------------------- |
| baseline            | None                       |
| All experiment runs | None confirmed             |


No genuine verbatim copying of prompt template text was found in any run.

---

## Quality Assessment

### ollama-llama3.1 (run 31)

- **Weakest performer**: 40% failure rate (2/5 plans failed validation before saving)
- Successfully processed plans show adequate lever counts and all-3-options compliance
- 23% of lever_classification values are out-of-vocabulary (use domain-specific labels instead of the 6-value taxonomy)
- Consequences are shorter than baseline (-63 chars avg)
- Despite failures, produces fully unique names and no options violations in output
- **Overall: WORSE** — validation failures disqualify it as reliable

### openrouter-openai-gpt-oss-20b (run 32)

- 100% success rate; lever count above baseline (avg 18.2 vs 15)
- Consequences closely match baseline length (275 vs 279); review slightly below (142 vs 152)
- Zero type violations; 100% name uniqueness
- Lever content is substantive and domain-appropriate
- **Overall: COMPARABLE**

### openai-gpt-5-nano (run 33)

- 100% success rate; lever count above baseline (avg 18.2)
- Consequences slightly above baseline (304 vs 279); review above baseline (190 vs 152)
- One type violation ("methods" instead of "methodology") in 91 levers
- Produces richer, more detailed lever analysis
- **Overall: COMPARABLE to slightly BETTER**

### openrouter-qwen3-30b-a3b (run 34)

- 100% success rate; variable lever count (13–20 per plan, avg 17.8)
- Consequences below baseline (235 vs 279); review matches baseline well (165 vs 152)
- Zero type violations; 100% name uniqueness
- **Overall: COMPARABLE**

### openrouter-openai-gpt-4o-mini (run 35)

- 100% success rate; lever count close to baseline (avg 16.0 vs 15)
- Consequences slightly below baseline (244 vs 279); review slightly above (179 vs 152)
- One type violation ("sound design" in hong_kong_game) and one duplicate name across plans
- **Overall: COMPARABLE**

### openrouter-gemini-2.0-flash-001 (run 36)

- 100% success rate; BUT sovereign_identity plan produced only 6 levers vs 15 baseline — a significant output truncation
- Remaining 4 plans: avg ~18 levers each
- Longest consequences (338 chars) and review (247 chars) among comparable-sized models
- Zero type violations; 100% name uniqueness
- **Overall: MIXED** — truncation on one plan is a notable quality issue

### anthropic-claude-haiku-4-5-pinned (run 37)

- 100% success rate; highest lever count (avg 21 per plan, 40% above baseline)
- Consequences dramatically above baseline (549 vs 279 — ~2x); review dramatically above baseline (523 vs 152 — ~3.4x)
- Zero type violations; 100% name uniqueness
- Content is very detailed: consequences include multi-step causal chains, quantified tradeoffs, and explicit tension descriptions; reviews are extensive
- The verbosity is a quality difference: haiku produces fundamentally more analytical depth per lever
- **Overall: BETTER** (with caveat that much higher verbosity changes the output character)

---

## New Schema Fields Assessment (lever_type and decision_axis)

The PR (#346) was specifically about adding `lever_type` and `decision_axis` to the lever schema. These fields are:

- **lever_type**: a categorical field (methodology/execution/governance/dissemination/product/operations)
- **decision_axis**: a one-sentence description of the controllable choice

**Neither field appears in any experiment output across all 7 runs.** This means:

1. The `lever_classification` field in experiment outputs carries the type taxonomy in a combined `"<type> — <description>"` format, but it is not split into separate `lever_type` and `decision_axis` fields.
2. None of the experiment runs produce the new schema as separate keys. This could indicate:
  - The runs were executed before the PR code was fully applied to the pipeline
  - The schema fields are validated/present internally but stripped before JSON serialization
  - The runs are testing an earlier or intermediate version of the code

The baseline does not contain `lever_type` or `decision_axis` either, which is expected since the baseline predates PR #346.

---

## Model Ranking

1. **anthropic-claude-haiku-4-5-pinned (run 37)** — Best quality: 100% success, most levers, deepest analysis, zero schema violations. Verbose but substantive.
2. **openai-gpt-5-nano (run 33)** — 100% success, above-baseline detail, minimal schema issues.
3. **openrouter-openai-gpt-oss-20b (run 32)** — 100% success, baseline-matching length, clean schema compliance.
4. **openrouter-qwen3-30b-a3b (run 34)** — 100% success, variable lever counts, clean schema compliance.
5. **openrouter-openai-gpt-4o-mini (run 35)** — 100% success, near-baseline counts, minor issues.
6. **openrouter-gemini-2.0-flash-001 (run 36)** — 100% success but truncated sovereign_identity output is a notable defect.
7. **ollama-llama3.1 (run 31)** — 40% failure rate; significant schema vocabulary drift in successful runs.

---

## Overall Verdict

**MIXED**: The experiment runs (32–37) show improved reliability compared to the baseline (100% success for 6 of 7 models vs. 60% for llama3.1). All post-PR models pass options compliance, achieve high name uniqueness, and use the lever_classification vocabulary correctly. However, **neither `lever_type` nor `decision_axis` — the two new fields explicitly targeted by PR #346 — appear in any experiment output**, meaning the core measurable goal of the PR cannot be confirmed from this data. The `lever_classification` field is present and carries overlapping information, but the separation into two distinct fields is missing.

---

## Recommendations

1. **Verify PR application**: Confirm that runs 32–37 used a codebase where PR #346 was fully merged and the JSON serialization outputs `lever_type` and `decision_axis` as separate top-level keys in each lever object.
2. **Inspect LeverCleaned serialization**: The PR description states both fields "propagate through `Lever` → `LeverCleaned` → JSON output". If the output files here are missing the fields, the serialization step may be excluding them. Review `LeverCleaned.model_dump()` or equivalent export logic.
3. **gemini-flash truncation on sovereign_identity**: Run 36 produced only 6 levers for this plan (vs 15 baseline). Investigate whether this is a context-length issue, a model refusal, or a truncated API response.
4. **ollama-llama3.1 vocabulary drift**: 23% invalid lever_classification values in run 31. If this model is to be supported, add stricter prompt instructions or a normalization step for the classification taxonomy.
5. **haiku verbosity**: haiku-4-5 produces 2–3.5x longer field values than baseline. While content quality is high, downstream systems that expect baseline-length text may need adjustment. Consider whether a max-length constraint is appropriate.
6. **Baseline name uniqueness**: The baseline itself has 29% duplicate names (due to multiple LLM calls per plan returning similar lever names). Models produce 100% unique names, which may indicate different call/deduplication behavior. Confirm this is intentional.

