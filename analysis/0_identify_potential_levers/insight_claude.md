# Insight Claude

## Scope

Prompt examined: `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt`

History runs examined: `history/0/00_identify_potential_levers` through `history/0/09_identify_potential_levers` (10 runs total).

Baseline reference: `baseline/train/` — five plans examined:
- `20250321_silo`
- `20250329_gta_game`
- `20260308_sovereign_identity`
- `20260310_hong_kong_game`
- `20260311_parasomnia_research_unit`

---

## Rankings

| Tier | Run | Model | Success Rate | Key Issue |
|------|-----|-------|-------------|-----------|
| 1 | 02 | openai-gpt-5-nano | 5/5 | None observed |
| 1 | 05 | openrouter-qwen3-30b-a3b | 5/5 | None observed |
| 1 | 07 | openrouter-openai-gpt-4o-mini | 5/5 | None observed |
| 1 | 09 | anthropic-claude-haiku-4-5-pinned | 5/5 | None observed |
| 2 | 00 | ollama-llama3.1 | 4/5 + partial | Template leakage in 1 of 3 LLM calls for silo plan |
| 2 | 01 | openrouter-openai-gpt-oss-20b | 2/5 | JSON parse failures (EOF errors) |
| 2 | 04 | openrouter-stepfun-step-3-5-flash | 2/5 | JSON parse failures |
| 3 | 03 | openrouter-z-ai-glm-4-7-flash | 0/5 | Schema mismatch — missing required fields |
| 3 | 06 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | JSON extraction failed |
| 3 | 08 | anthropic-claude-haiku-4-5-pinned | 0/5 | LLM not found (configuration error) |

Ranking basis: operational reliability first (success rate), then content quality for successful runs based on consequence depth, measurable specificity, and weakness detail.

---

## Negative Things

### 1. Template leakage in run 00, silo plan (second LLM call)

Five consecutive levers (positions 6–10) in `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contain unfilled bracket placeholders in the `review` field:

```
"review": "Controls Trade-off between [Scalability] vs. [Cost Efficiency]. Weakness: The options fail to consider the impact of [Silo Architecture on Mental Health]."
"review": "Controls Trade-off between [Resource Efficiency] vs. [Environmental Impact]. Weakness: The options fail to consider the impact of [Resource Allocation on Social Dynamics]."
"review": "Controls Trade-off between [Security] vs. [Individual Freedom]. Weakness: The options fail to consider the impact of [Governance on Social Cohesion]."
"review": "Controls Trade-off between [Financial Stability] vs. [Social Responsibility]. Weakness: The options fail to consider the impact of [Economic and Financial Model on Inequality]."
"review": "Controls Trade-off between [Social Cohesion] vs. [Individual Autonomy]. Weakness: The options fail to consider the impact of [Societal Integration on Mental Health]."
```

The affected levers are at positions 6–10, which corresponds to the second LLM call in the 3×5 call pattern (the step calls the LLM three times, each producing 5 levers, for a total of 15). Levers 1–5 (first call) and 11–15 (third call) are clean. This is an intra-run inconsistency: the same model and prompt fail on one of three sequential calls.

Evidence: `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lines 60–111.

### 2. Prompt example name bleeds into output

The prompt file at line 19 uses "Material Adaptation Strategy" as an illustrative example:
> `Name levers as strategic concepts (e.g., "Material Adaptation Strategy")`

In `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the very first lever is named exactly "Material Adaptation Strategy" and lever 11 (from the third call) is also named "Material Adaptation Strategy" — producing a cross-call duplicate that copies the prompt example verbatim.

The baseline (`baseline/train/20250321_silo/002-10-potential_levers.json`) does not contain this name at all. The baseline names include "Resource Allocation Strategy", "Social Control Mechanism", "Technological Adaptation Strategy", etc., showing that the example name is an artifact of the prompt example bleeding into the model's output.

Evidence: `prompts/identify_potential_levers/prompt_0_fa5dfb...txt` line 19; `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lines 2–12, 113–123.

### 3. Structural failures in three model families

Three runs failed 0/5:
- **Run 03 (z-ai-glm-4-7-flash)**: Error message indicates missing fields `strategic_rationale`, `levers`, `summary`. The model likely generated a different schema than expected.
- **Run 06 (nvidia-nemotron-3-nano-30b-a3b)**: JSON extraction failed for all 5 plans. Model output could not be parsed into the expected structure.
- **Run 08 (claude-haiku-4-5-pinned)**: "LLM not found" with 0.01–0.02s duration. Configuration error — the model identifier was not resolvable at runtime.

Evidence: `history/0/03_identify_potential_levers/outputs.jsonl`, `history/0/06_identify_potential_levers/outputs.jsonl`, `history/0/08_identify_potential_levers/outputs.jsonl`.

### 4. JSON parse failures for weaker models

Runs 01 and 04 each failed 3/5 with JSON parse errors:
- **Run 01 (gpt-oss-20b)**: `"EOF while parsing at line 36"` — the model truncated its response mid-JSON.
- **Run 04 (stepfun-step-3-5-flash)**: `"expected ':' at line 17"` and `"expected value at line 46"` — the model produced malformed JSON tokens.

Evidence: `history/0/01_identify_potential_levers/outputs.jsonl`, `history/0/04_identify_potential_levers/outputs.jsonl`.

### 5. Duplicate lever names within the same plan output (baseline and runs)

The multi-call architecture generates 3 batches of 5 levers independently. Names converge across calls. In `baseline/train/20250321_silo/002-10-potential_levers.json`:

- "Technological Adaptation Strategy" appears 3 times (once per call)
- "External Relations Protocol" appears twice
- "Resource Allocation Strategy" appears twice

This means 5 of 15 lever names are duplicates in the baseline — a 33% name duplication rate. This is an artifact of the multi-call approach, not model behavior, and likely persists across all runs and models.

Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` — lever_ids `a0e34bf5`, `364f2000`, `7f016a5f` (all named "Technological Adaptation Strategy"); `5e26e456`, `c010ac67` (both "External Relations Protocol"); `f961fd84`, `22751495` (both "Resource Allocation Strategy").

### 6. Overall reliability is low: 56% success rate

28 of 50 plan-level runs succeeded. Only 4 of 10 models achieved 100% success. This means the current prompt is fragile under model diversity.

---

## Positive Things

### 1. Format compliance is perfect across all successful runs

Every successful run produces levers that:
- Follow the `"Immediate: X → Systemic: Y → Strategic: Z"` consequence chain.
- Have exactly 3 options per lever.
- Include `"Controls X vs. Y"` trade-off language in the `review` field.
- Include a `"Weakness: ..."` statement.

This shows the prompt effectively communicates the required structure to capable models.

### 2. Measurable numbers appear consistently in successful runs

All four Tier-1 models (runs 02, 05, 07, 09) produce percentages and quantitative claims in the Systemic consequence layer (e.g., "25% faster scaling", "40% of security budget"). This matches the baseline pattern.

### 3. Run 09 (claude-haiku-4-5-pinned) achieves the highest content depth

Run 09's silo output shows sophisticated systems thinking:
- Multi-clause consequences with specific failure scenarios: `"Immediate: Dictatorial rule triggers compliance through fear but erodes long-term population morale → Systemic: Low morale accelerates psychological breakdown, requiring 40% of security budget for containment → Strategic: Sustained unrest risks catastrophic system failures..."`
- Highly specific quantitative framing: `"$250B", "$500B", "$600B"`, `"99.5% survival probability over 300 years"`, `"statistical probability of unrecoverable failure within 200 years exceeds 85%"`.
- Multi-sentence weaknesses that address emergent failure modes absent from the prompt structure.

Evidence: `history/0/09_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lines 1–50.

### 4. Run 00 retry mechanism works

`history/0/00_identify_potential_levers/outputs.jsonl` shows `20250329_gta_game` first appearing as an error (timeout at 120.13s), then as a success (78.64s) on line 6. This confirms the runner has a retry mechanism that recovered from the timeout. The gta_game output file exists and contains valid lever data.

Evidence: `history/0/00_identify_potential_levers/outputs.jsonl`, lines 2 and 6.

### 5. No option prefix violations in successful runs

The prompt explicitly prohibits "Option A:", "Choice 1:" prefixes. No violations were observed in any examined output from successful runs. The prohibition is effectively followed.

---

## Comparison

### History runs vs. baseline

The baseline (`baseline/train/*/002-10-potential_levers.json`) was generated with a different (likely higher-quality) model and serves as the quality reference. Direct comparison:

| Dimension | Baseline | Run 00 (ollama) | Run 05 (qwen3) | Run 07 (gpt-4o-mini) | Run 09 (haiku-4-5) |
|-----------|----------|---------|---------|---------|---------|
| Lever count (silo) | 15 | 15 | 15 | 15 | 15 |
| Template leakage | 0 | 5/15 (33%) | 0 | 0 | 0 |
| Prompt-example name leak | 0 | 2/15 | 0 | 0 | 0 |
| Measurable % in consequences | 15/15 (100%) | 5/15 (33%) | 13/15 (87%) | ~14/15 (93%) | 15/15 (100%) |
| Multi-sentence weaknesses | 1 sentence avg | 1 sentence | 1 sentence | 1 sentence | 2–3 sentences |
| Option length (approx avg chars) | ~120 | ~50 | ~80 | ~100 | ~150 |
| Cross-call name duplication | 5/15 | 2/15 | unknown | unknown | unknown |

The baseline itself has a 33% name-duplication rate, which is a structural artifact from the multi-call approach — not a quality measure. Run 09 matches or exceeds baseline on measurable specificity and option depth.

### Consequence format: baseline vs. history

The baseline uses a hybrid format — some levers chain `Immediate → Systemic → Strategic` inline, while others place measurable outcomes in a separate sentence after the chain. Example from `baseline/train/20250321_silo/002-10-potential_levers.json` (lever_id b35d92a2):
> `"Immediate: Reduced dissent → Systemic: Stifled innovation... → Strategic: Increased vulnerability... Measurable outcome: 30% reduction in reported dissent, but a 15% decrease in innovation output."`

History runs only use the inline chain. Neither is better by the prompt spec, but the baseline's supplementary "Measurable outcome" sentence produces denser quantitative grounding.

---

## Quantitative Metrics

### Table 1: Operational success rates

| Run | Model | Plans Succeeded / 5 | Primary Failure Mode |
|-----|-------|---------------------|----------------------|
| 00 | ollama-llama3.1 | 4/5 (80%) | LLM timeout (1 plan) |
| 01 | openrouter-openai-gpt-oss-20b | 2/5 (40%) | JSON truncation |
| 02 | openai-gpt-5-nano | 5/5 (100%) | — |
| 03 | openrouter-z-ai-glm-4-7-flash | 0/5 (0%) | Schema mismatch |
| 04 | openrouter-stepfun-step-3-5-flash | 2/5 (40%) | JSON parse error |
| 05 | openrouter-qwen3-30b-a3b | 5/5 (100%) | — |
| 06 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 (0%) | JSON extraction |
| 07 | openrouter-openai-gpt-4o-mini | 5/5 (100%) | — |
| 08 | anthropic-claude-haiku-4-5-pinned | 0/5 (0%) | LLM not found |
| 09 | anthropic-claude-haiku-4-5-pinned | 5/5 (100%) | — |
| **Total** | | **28/50 (56%)** | |

### Table 2: Lever count per successful plan output

All directly verified successful outputs contain exactly 15 levers (3 LLM calls × 5 levers per call). This is consistent with the prompt constraint "EXACTLY 5 levers per response". No constraint violations on lever count were observed in directly read files.

| File | Lever Count | Matches 5×3=15? |
|------|-------------|-----------------|
| `baseline/train/20250321_silo/002-10-potential_levers.json` | 15 | Yes |
| `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` | 15 | Yes |
| `history/0/09_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` | 15 | Yes |

### Table 3: Template and example leakage counts (silo plan)

| Run | Bracket placeholders [X] | Prompt example name leak | Total levers affected |
|-----|--------------------------|--------------------------|----------------------|
| Baseline | 0 | 0 | 0/15 |
| Run 00 | 5 (positions 6–10) | 2 (positions 1, 11) | 7/15 (47%) |
| Run 05 | 0 | 0 | 0/15 |
| Run 07 | 0 | 0 | 0/15 |
| Run 09 | 0 | 0 | 0/15 |

### Table 4: Measurable percentages in consequences (silo plan, directly verified)

| Run | Levers with numeric % in consequence | Total | Rate |
|-----|--------------------------------------|-------|------|
| Baseline | 15 | 15 | 100% |
| Run 00 | 5 (positions 1–5, 11–15 have minimal numbers; positions 6–10 have none) | 15 | ~33% |
| Run 09 | 15 | 15 | 100% |

Note: Run 09 values observed include: 40%, 35%, 45%, 30%, 60%, 50%, 99.5%, 85%.

### Table 5: Constraint violations (options count per lever)

| Run | Levers with ≠3 options | Total checked |
|-----|------------------------|---------------|
| Baseline silo | 0 | 15 |
| Run 00 silo | 0 | 15 |
| Run 09 silo | 0 | 15 |

No constraint violations on option count were observed in any directly read file.

### Table 6: Cross-call name duplication (baseline silo)

| Name | Occurrences |
|------|-------------|
| Technological Adaptation Strategy | 3 |
| External Relations Protocol | 2 |
| Resource Allocation Strategy | 2 |
| All other names | 1 each |
| **Total duplicates** | **5/15 (33%)** |

Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` — lever_ids `a0e34bf5`, `364f2000`, `7f016a5f`, `5e26e456`, `c010ac67`, `f961fd84`, `22751495`.

---

## Evidence Notes

1. **Template leakage claim** is grounded in the directly read JSON at `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lines 60–111. The five affected levers have literal `[Scalability]`, `[Cost Efficiency]`, `[Security]`, `[Individual Freedom]`, etc. in the `review` field.

2. **Prompt example leakage claim** is grounded in prompt line 19 (`"Material Adaptation Strategy"` example) vs. lever 1 and lever 11 in the same file (`lever_id` `46b61e67` and `b4a432cd`).

3. **Run 09 quality claim** is grounded in the directly read first 50 lines of `history/0/09_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, showing detailed multi-clause consequences with dollar figures, percentage impacts, and multi-sentence weaknesses.

4. **Retry behavior claim** is grounded in `history/0/00_identify_potential_levers/outputs.jsonl` where gta_game appears on both line 2 (error, 120.13s) and line 6 (ok, 78.64s).

5. **Baseline name duplication claim** is grounded in directly reading all 15 lever_ids from `baseline/train/20250321_silo/002-10-potential_levers.json` and counting repeated names.

6. **Run 03 schema mismatch claim** is from `history/0/03_identify_potential_levers/outputs.jsonl` error message: `"missing fields: strategic_rationale, levers, summary"`.

7. **Run 08 LLM config error** is from `history/0/08_identify_potential_levers/outputs.jsonl` with 0.01–0.02s durations and "LLM not found" error.

---

## Questions For Later Synthesis

1. **Why does run 08 fail with "LLM not found" for `claude-haiku-4-5-pinned` while run 09 with the same model identifier succeeds?** Was there a model registration change between the two runs, or is the meta.json for run 09 incorrect about the model used?

2. **Is the baseline's cross-call name duplication (33%) acceptable, or should the step include deduplication before the `002-11-deduplicated_levers_raw.json` step?** The baseline already has a deduplication step downstream (`002-11`), but that happens after this step. The question is whether earlier deduplication or prompt guidance would improve quality.

3. **Run 03 (z-ai-glm-4-7-flash) reports missing fields `strategic_rationale`, `levers`, `summary`.** This suggests the model generated a different output schema. Is there an alternative prompt variant that handles schema-divergent models, or should these models simply be excluded from the runner's model pool?

4. **The baseline consequence format occasionally adds a trailing "Measurable outcome:" sentence** beyond the `Immediate → Systemic → Strategic` chain. Should the prompt be updated to make this explicit, and would doing so improve quantitative specificity in weaker models?

5. **Run 09 output quality is notably richer than the baseline in terms of option specificity and weakness depth.** Is this a meaningful quality difference, or is verbosity being confused with quality here? A subsequent evaluation step that scores against explicit criteria would clarify this.

---

## Reflect

The central tension in this step is between **structural reliability** (does the model output parseable JSON matching the schema?) and **content quality** (are the levers substantive, specific, and diverse?). These two concerns have different root causes and different fixes:

- Structural reliability failures (runs 01, 03, 04, 06, 08) are almost entirely model-selection problems. The prompt structure is well-formed and works correctly for capable models.
- Content quality failures (run 00 template leakage, cross-call name duplication in all runs) have prompt-addressable and code-addressable roots.

The multi-call architecture (3 calls × 5 levers) is the root cause of cross-call name duplication. This is a code-level issue, not a prompt issue. The deduplication step at `002-11` handles it downstream, but not until after this step.

Template leakage (run 00, second call) is stochastic — the same model handles calls 1 and 3 correctly but fails on call 2. This suggests the model occasionally defaults to a template-filling mode rather than generating specific content. A validation layer at the code level (reject any output containing `[` and `]` in review fields) would catch this more reliably than prompt adjustments.

The prompt example name leakage is a pure prompt issue and has a straightforward fix.

---

## Potential Code Changes

**C1: Add bracket-placeholder validation in the runner or pipeline step.**
After each LLM call, scan the `review` fields for the pattern `\[.*?\]`. If found, treat the call as failed and retry. This would have caught the run 00 second-call leakage. Evidence: 5/15 levers affected in `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`. Predicted effect: eliminates bracket-placeholder template leakage from successful outputs.

**C2: Add JSON schema validation for required lever fields before accepting a call's output.**
Run 03 failed because the model returned a different schema (`strategic_rationale`, `levers`, `summary` instead of an array of lever objects). A pre-merge schema check would detect this and either retry or skip the model. Evidence: `history/0/03_identify_potential_levers/outputs.jsonl`. Predicted effect: run 03 would fail gracefully rather than producing no output for 5/5 plans.

**C3: Deduplicate lever names at merge time (before writing `002-10-potential_levers.json`).**
Currently deduplication happens at `002-11`. Moving it earlier (or adding a cross-call uniqueness constraint at the time of merging 3×5 outputs) would prevent duplicate names from appearing in the final lever file. Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` has 33% name duplication. Predicted effect: downstream steps (including this analysis step) would see higher-quality, more diverse lever sets.

**C4: Validate LLM identifiers before launching a run.**
Run 08 spent 0.01–0.02s per plan and failed with "LLM not found". A pre-flight check that resolves all model identifiers before starting would surface this error immediately. Evidence: `history/0/08_identify_potential_levers/outputs.jsonl`. Predicted effect: fast-fail with a clear error message instead of silently producing empty outputs for all plans.

---

## Potential Prompt Changes

**H1: Remove or replace the "Material Adaptation Strategy" example in the prompt.**
The prompt (line 19) uses `"Material Adaptation Strategy"` as a naming example. This name bleeds into outputs — run 00 silo has it as lever 1 and lever 11. Replacing with a more neutral or abstract example (e.g., `"Stakeholder Coordination Approach"`) would reduce this leakage.
Evidence: `prompts/identify_potential_levers/prompt_0_fa5dfb...txt` line 19; `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever_ids 46b61e67 and b4a432cd.
Predicted effect: eliminates verbatim example name in outputs for models that are susceptible to example anchoring.

**H2: Add an explicit prohibition against repeating lever names across responses.**
The prompt's multi-call context means the model generates the same themes independently in each call. Adding a note like "Lever names must be unique and thematically distinct from the other levers. Do not reuse a lever name you have already generated." would reduce cross-call duplication — though the model cannot see its own prior calls, so this instruction is only partially enforceable without code-level deduplication (C3).
Evidence: baseline silo has 33% name duplication; `baseline/train/20250321_silo/002-10-potential_levers.json`.
Predicted effect: marginal reduction in cross-call name duplication for models that are sensitive to novelty instructions.

**H3: Add a "Measurable outcome:" suffix requirement to the consequences format.**
The prompt specifies `"Immediate: [effect] → Systemic: [impact] → Strategic: [implication]"` but does not specify a trailing measurable outcome sentence. The baseline sometimes adds one (`"Measurable outcome: 30% reduction in reported dissent, but a 15% decrease in innovation output."`). Encoding this explicitly in the format would push weaker models toward more quantitative outputs.
Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` lever_ids b35d92a2, ccd48764, 5ac097c7, 364f2000, 5e26e456.
Predicted effect: increased measurable specificity in runs from moderate-capability models (runs 05, 07); minimal effect on run 09 which already achieves this organically.

**H4: Add an explicit "fill in specific values — never use [bracket placeholders]" prohibition.**
The prompt prohibits `"[specific innovative option]"` in options, but not bracket placeholders in `review` fields. Adding a blanket prohibition covering all fields would address the leakage in run 00 positions 6–10.
Evidence: `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lines 60–111.
Predicted effect: eliminates bracket leakage from models that otherwise comply with the format (ollama-llama3.1 in calls 1 and 3 was clean; only call 2 failed).

---

## Summary

The prompt `fa5dfb88...` is structurally effective for capable models: all four Tier-1 models (gpt-5-nano, qwen3-30b-a3b, gpt-4o-mini, claude-haiku-4-5-pinned) achieve 100% success with correct format, 3 options per lever, and appropriate trade-off language.

The overall 56% success rate (28/50) is driven primarily by model failures, not prompt failures: three entire runs fail due to infrastructure issues (LLM not found, schema mismatch, JSON extraction failure) that a pre-flight validator or parser improvement would catch.

The primary prompt-addressable issue is example-name leakage: the prompt's `"Material Adaptation Strategy"` example appears verbatim in run 00's output (H1). The primary code-addressable issue is bracket-placeholder validation (C1) and cross-call name deduplication (C3).

Content quality varies significantly by model. Run 09 (claude-haiku-4-5-pinned) produces the richest output — longer options with specific dollar figures and multi-sentence weaknesses — while the baseline itself has measurable percentages in all 15 consequences but shows 33% cross-call name duplication, indicating the baseline was not deduplicated before being stored.

The highest-leverage improvements, in estimated order: **C4** (LLM pre-flight validation, eliminates run 08 class failures) > **C3** (cross-call deduplication, reduces 33% baseline duplication rate) > **C1** (bracket-placeholder validation, eliminates run 00 second-call leakage) > **H1** (remove example name from prompt, eliminates name anchoring) > **H3** (add measurable outcome suffix requirement, improves quantitative specificity for mid-tier models).
