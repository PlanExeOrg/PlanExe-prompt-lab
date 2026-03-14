# Insight Claude

Prompt: `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt`
Runs analyzed: `0/10`, `0/12`, `0/13`, `0/14`, `0/15`, `0/16` (all `identify_potential_levers`)

---

## Rankings

| Rank | Run | Model | Quality | Notes |
|------|-----|-------|---------|-------|
| 1 | 12 | anthropic-claude-haiku-4-5-pinned | High | Richest options, most project-specific, zero "25%" template |
| 2 | 10 | openai-gpt-5-nano | Medium-High | Good depth, moderate template leakage |
| 3 | 13 | openrouter-openai-gpt-oss-20b | Medium | 1 plan failure, good output when successful |
| 4 | 14 | openrouter-qwen3-30b-a3b | Medium | Follows format, options shorter than run 12 |
| 5 | 15 | openrouter-openai-gpt-4o-mini | Medium-Low | Generic lever names, moderate depth |
| 6 | 16 | ollama-llama3.1 | Low | Label-style options, extra levers, name duplicates |

---

## Negative Things

### 1. Template leakage: "25% faster scaling through"

The prompt (§2 Lever Quality Standards) contains this example metric:
> "Include measurable outcomes: 'Systemic: 25% faster scaling through...'"

Multiple models copy this phrase almost verbatim into their output. In `history/0/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, four of fifteen levers contain the string "25% faster scaling through" (levers: Self-Sufficiency, Information Sovereignty, Modular Construction, Funding and Economic Sovereignty). Other models use "25% faster" or substitute "30%/40%" while keeping the same sentence skeleton. Run 12 (claude-haiku) is the only model that avoids the pattern entirely.

### 2. Prompt field-name inconsistency → JSON parse failure

The prompt (§4 Validation Protocols) reads:
> "For `review_lever`: • State the trade-off explicitly..."

The output schema uses the field name `review`, not `review_lever`. In `history/0/13_identify_potential_levers/outputs.jsonl`, the parasomnia plan fails with:

```
LLM chat interaction failed [7659a74ce3e1]: Failed to run. Exhausted all LLMs.
...ValueError('Could not extract json string from output:
...\"review_lever\": \"Controls Safety vs. Naturalistic Environment...
```

The model (gpt-oss-20b) read `review_lever` from the prompt and emitted that field name, causing the JSON extractor to fail. The error also shows the model wrapped levers in a `strategic_rationale` outer object that the parser rejected.

### 3. Label-style options violate the "full description" requirement

Run 16 (llama3.1) consistently produces one- to four-word option labels instead of full strategic descriptions. From `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

```json
"options": [
  "Domestic Material Sourcing",
  "Strategic Partnerships for Supply Chain Optimization",
  "Implementation of Advanced Recycling and Repurposing"
]
```

The prompt explicitly prohibits "NO generic option labels (e.g., 'Optimize X', 'Tolerate Y')". Average option length for run 16 is ~43 chars vs ~200 chars for run 12.

### 4. Lever count inflation in run 16 (llama3.1)

All runs with `workers=4` produce 15 levers per plan (3 LLM calls × 5 levers each). Run 16 (`workers=1`) produces 20 levers per plan (4 calls × 5) in every plan checked. This indicates the pipeline emits a different number of batches depending on the worker count. The extra batch produces additional levers that go through the deduplication step (`002-11`) but inflate raw output.

Evidence: `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains 20 entries (counted); other runs have 15.

### 5. Exact-name duplicates within a single plan output (run 16)

Run 16 (llama3.1) silo output contains:
- "Material Adaptation Strategy" twice (lever_ids `fb6ffa36` and `2bf5058d`)
- "Security and Surveillance Strategy" (lever `6f1d87d7`) and "Surveillance and Security Protocol" (lever `e09240f9`) as near-duplicates

This cross-call duplication indicates the model is not aware of previously generated levers in prior calls.

### 6. Semantic redundancy across calls in all models

Even without exact-name duplicates, all runs show semantic overlap across their 3–4 batches. Run 10 (gpt-5-nano) silo contains:
- Two self-sufficiency/governance levers (#1 "Self-Sufficiency and Resilience Architecture", #6 "Self-Sufficiency Governance Architecture")
- Three funding/economics levers (#5, #10, #13)

Run 12 (haiku) silo has three distinct governance levers across batches (#1, #6, #11). The deduplication step (`002-11`) should handle this, but its effectiveness is unclear from the available data.

### 7. Consequence chain format inconsistency in run 16

The prompt requires `"Immediate: [effect] → Systemic: [impact] → Strategic: [implication]"`. Run 16 frequently omits the arrows and shortens chains. Example from `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

```json
"consequences": "Immediate: Efficient material sourcing → Systemic: Reduced construction timeline
  through optimized resource allocation → Strategic: Enhanced resilience to supply chain disruptions."
```

Some levers in run 16 have no measurable figures and very short systemic claims.

---

## Positive Things

### 1. Run 12 (claude-haiku): exceptional option depth and project specificity

Options are full strategic narratives, not summaries. From `history/0/12_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever "Information Architecture and Exterior Reality Control", option 2:

> "Curate strictly controlled information flows: allow limited scientific research 'proving' exterior toxicity through rigged experiments, manage historical narratives through authorized archives, and stage periodic simulated exterior contamination events to reinforce necessity"

This is highly specific to the Silo project context and could not be confused with a generic template.

### 2. Review field quality in runs 12 and 10

Run 12 reviews explicitly identify structural weaknesses that go beyond the prompt template. Example from lever "Population Stratification Model":

> "Weakness: All options ignore reproduction and population growth governance—without explicit breeding restrictions or severe demographic controls, any stratification model collapses within 3-4 generations as lower tiers demographically overwhelm upper capacity."

This is a genuine analytical observation, not a fill-in-the-blank template.

### 3. 100% plan completion for five of six runs

Runs 10, 12, 14, 15, and 16 show `status: ok` for all five plans in their `outputs.jsonl`. Run 13 has one failure (parasomnia). This indicates the prompt and toolchain are generally stable.

### 4. Speed: runs 12 and 15 are fast and reliable

Run 12 (haiku) completes the silo plan in 91.96s and all five plans in <135s each. Run 15 (gpt-4o-mini) is the fastest at <55s per plan. Both are significantly faster than run 10 (gpt-5-nano) at 404.91s for silo alone.

---

## Comparison

### Against baseline training data

`baseline/train/20260310_hong_kong_game/002-13-vital_few_levers_raw.json` (a later-stage step: "vital few" from a prior pipeline run) shows levers named: "Narrative Innovation Strategy", "Talent Alignment Strategy", "Geopolitical Risk Mitigation Strategy", "Hong Kong Identity Amplification Strategy", "Distribution Architecture Strategy". These are deeply project-specific, contextually motivated, and contain full strategic descriptions.

Run 12 (haiku) most closely matches baseline depth for its plans. Run 14 (qwen3) and run 15 (gpt-4o-mini) produce levers that are generically named and could apply to any project.

### Run 16 (llama3.1) vs all others

The gap between run 16 and other models is qualitative, not just quantitative. The llama3.1 options read as noun phrases describing tool categories ("Advanced Biometric Identification") rather than strategic commitments. This likely causes downstream problems in the synthesis and selection steps that depend on options being interpretable as distinct strategic choices.

---

## Quantitative Metrics

### Lever counts per plan (merged output)

| Run | Model | workers | levers/plan | Expected | Violation |
|-----|-------|---------|-------------|----------|-----------|
| 10 | gpt-5-nano | 4 | 15 | 15 | No |
| 12 | claude-haiku | 4 | 15 | 15 | No |
| 13 | gpt-oss-20b | 4 | 15 (4 plans) | 15 | No (parasomnia=0) |
| 14 | qwen3-30b | 4 | 15 | 15 | No |
| 15 | gpt-4o-mini | 4 | 15 | 15 | No |
| 16 | llama3.1 | 1 | 20 | 15 | Yes |

### Plan completion (status=ok)

| Run | Model | Plans ok / total |
|-----|-------|-----------------|
| 10 | gpt-5-nano | 5/5 |
| 12 | claude-haiku | 5/5 |
| 13 | gpt-oss-20b | 4/5 |
| 14 | qwen3-30b | 5/5 |
| 15 | gpt-4o-mini | 5/5 |
| 16 | llama3.1 | 5/5 |

### Approximate average option length (chars) — silo plan

Measured from first 3 levers in each output file:

| Run | Model | Avg option length (chars) | Assessment |
|-----|-------|--------------------------|------------|
| 12 | claude-haiku | ~195 | Rich, specific |
| 10 | gpt-5-nano | ~117 | Adequate |
| 13 | gpt-oss-20b | ~145 | Adequate |
| 15 | gpt-4o-mini | ~92 | Borderline |
| 14 | qwen3-30b | ~54 | Short |
| 16 | llama3.1 | ~43 | Label-level |

### Template leakage: "25% faster scaling through" occurrences in silo output

| Run | Model | Occurrences |
|-----|-------|-------------|
| 10 | gpt-5-nano | 4 |
| 14 | qwen3-30b | 2 |
| 15 | gpt-4o-mini | 1 |
| 13 | gpt-oss-20b | 1 |
| 16 | llama3.1 | 1 |
| 12 | claude-haiku | 0 |

### Constraint violations by category

| Violation type | Run 10 | Run 12 | Run 13 | Run 14 | Run 15 | Run 16 |
|----------------|--------|--------|--------|--------|--------|--------|
| Plan failure | 0 | 0 | 1 | 0 | 0 | 0 |
| Lever count wrong | 0 | 0 | 0 | 0 | 0 | 1 (all plans) |
| Exact name duplicate | 0 | 0 | 0 | 0 | 0 | 1+ (silo) |
| Label-style options | 0 | 0 | 0 | 0 | 0 | ~many |
| "25%" template leakage | 4 | 0 | 1 | 2 | 1 | 1 |

### Duration (seconds) by plan

| Run | Model | silo | gta_game | sovereign | hk_game | parasomnia |
|-----|-------|------|----------|-----------|---------|------------|
| 10 | gpt-5-nano | 404.9 | 232.2 | 253.0 | 290.2 | 241.0 |
| 12 | claude-haiku | 92.0 | 86.5 | 116.1 | 120.9 | 131.2 |
| 13 | gpt-oss-20b | 218.1 | 162.4 | 198.3 | 240.3 | 61.2* |
| 14 | qwen3-30b | 114.7 | 65.7 | 168.2 | 141.2 | 115.0 |
| 15 | gpt-4o-mini | 45.2 | 45.5 | 47.5 | 54.1 | 53.3 |
| 16 | llama3.1 | 101.2 | 69.9 | 117.7 | 98.3 | 84.1 |

*parasomnia failed mid-run at 61.2s

---

## Evidence Notes

- `history/0/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`: 15 levers; "25% faster scaling" appears 4 times; semantic duplicates in funding/economics domain.
- `history/0/12_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`: 15 levers; 0 "25% faster" instances; options are multi-sentence strategic descriptions averaging ~195 chars.
- `history/0/13_identify_potential_levers/outputs.jsonl`: parasomnia error explicitly shows `review_lever` field name and `strategic_rationale` wrapper in raw LLM response — both rejected by the extractor.
- `history/0/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`: 15 levers; options avg ~54 chars; all correctly follow `Immediate → Systemic → Strategic` format.
- `history/0/15_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`: 15 levers; lever names are generic ("Resource Allocation Strategy", "Governance and Control Framework" appears twice with different content).
- `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`: 20 levers; "Material Adaptation Strategy" appears twice (lever_ids `fb6ffa36` and `2bf5058d`); options are noun phrases not strategic descriptions.
- `baseline/train/20260310_hong_kong_game/002-13-vital_few_levers_raw.json`: Baseline reference shows highly specific, project-contextual lever names and deep option descriptions — closest match is run 12.
- Prompt file `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt`: Line 9 says `"Systemic: 25% faster scaling through..."` as example. Line 26 says `"For \`review_lever\`:"` while schema uses `review`.

---

## Questions For Later Synthesis

1. Does the deduplication step (`002-11`) successfully remove the semantic duplicates created by cross-call repetition? The missing `002-11` files for some runs (noted as deleted in git status) suggest instability in that step.
2. Is run 16 (llama3.1 with workers=1) producing 20 levers intentionally (a different target per run) or is it a code bug tied to worker count?
3. The parasomnia plan in run 13 failed due to the `review_lever` field name. Is this a one-model issue or does the same field name confusion appear in other models' raw outputs even when they succeed?
4. Should the prompt's "25% faster scaling" example be removed, replaced with a format placeholder, or is some numeric anchoring desirable?
5. Run 12 (claude-haiku) produces the highest quality output but is not the fastest. Is there a quality–speed trade-off here that the synthesis step should evaluate explicitly?

---

## Reflect

The most striking finding is the large quality gap between run 12 (claude-haiku) and run 16 (llama3.1), with all other models falling between them. This gap is not purely about instruction-following (all models follow the JSON schema), but about contextual grounding: claude-haiku infers project-specific tensions from the plan text and encodes them in options, while llama3.1 generates context-free category labels.

The "25% faster scaling" template leakage is a prompt design issue, not a model capability issue — the prompt literally provides this string as a fill-in target. Removing or abstracting it would immediately improve output diversity.

The `review_lever` vs `review` field name inconsistency is a clear prompt bug that causes a reproducible failure for at least one model.

---

## Potential Code Changes

C1: **Worker-count-dependent batch count** — `history/0/16_identify_potential_levers` with `workers=1` produces 20 levers (4 batches) while `workers=4` runs produce 15 (3 batches). The runner code should fix the number of LLM call batches regardless of worker count, so merged lever counts are consistent.

C2: **JSON field name tolerance** — The extractor rejects responses with `review_lever` instead of `review`. Either accept both field names in the parser, or (better) fix the prompt to say `review` consistently.

C3: **Cross-call context passing** — Models that produce exact-name duplicates (run 16) are not aware of prior-batch lever names. If the runner concatenated prior lever names into each subsequent call's context, models could avoid the overlap.

---

## Prompt Hypotheses

H1: **Remove "25% faster scaling through" example metric** — Replace with a format placeholder like `"Systemic: [N]% [measurable outcome] through [mechanism]"`. Expected effect: reduction of literal "25% faster scaling" copies across all models; more diverse, project-driven numeric claims.
Evidence: 4 occurrences in run 10 silo; 2 in run 14; 1 each in runs 13, 15, 16. Only run 12 (claude-haiku) avoids it.

H2: **Align prompt field name with schema** — Change `"For \`review_lever\`:"` in §4 to `"For \`review\`:"`. Expected effect: eliminates the `review_lever` field in model outputs; prevents JSON extraction failure for models that anchor on the prompt field name.
Evidence: run 13 parasomnia failure, with raw output containing `"review_lever"` as the key.

H3: **Add a full-description option example** — Models producing label-style options (run 16) may need an explicit example of what a complete strategic option looks like. Add a concrete multi-sentence example to §6 "Option Structure Enforcement". Expected effect: increases average option length in weaker models; reduces label-style outputs.
Evidence: run 16 average option length ~43 chars vs run 12 ~195 chars.

H4: **Add "do not repeat lever names from prior calls" instruction** — If the step makes multiple sequential calls per plan, instruct the model in each subsequent call to avoid lever names already used. Expected effect: reduction in exact-name and near-name duplicates across batches.
Evidence: run 16 has duplicate "Material Adaptation Strategy"; all runs show semantic redundancy across batches.

---

## Summary

Six runs of the same prompt (`fa5dfb88...`) were tested across six models. Run 12 (claude-haiku-4-5-pinned) produces the highest-quality output: long, contextually grounded options, zero template leakage, and full constraint compliance. Run 16 (llama3.1) is the weakest: label-style options, inflated lever counts (20 vs expected 15), and exact-name duplicates within a plan.

Two concrete prompt defects are present:
1. The example metric "25% faster scaling through" is copied verbatim by most models (except haiku), flattening consequence quality.
2. The field name `review_lever` in the prompt conflicts with the schema field `review`, causing a reproducible JSON extraction failure for at least one model (run 13, parasomnia plan).

The code-level issue (worker-count-dependent batch count producing 20 vs 15 levers in run 16) should be investigated independently of the prompt.

From a model selection perspective: claude-haiku produces near-baseline quality, is significantly faster than gpt-5-nano, and avoids template leakage. The synthesis step should consider whether quality differences across models reflect model capability versus prompt sensitivity.
