# Insight Claude

Analysis of runs 81–87 for `identify_potential_levers` (prompt_2).
PR under review: [#283](https://github.com/PlanExeOrg/PlanExe/pull/283) — "Enable retry config in prompt optimizer runner".

---

## Rankings

| Rank | Run | Model | Plans OK/Total | Content Quality |
|------|-----|-------|----------------|-----------------|
| 1 | 87 | anthropic-claude-haiku-4-5-pinned | 4/5 | Excellent — domain-specific, measurable |
| 2 | 84 | openai-gpt-5-nano | 5/5 | Good — specific metrics, blockchain overuse |
| 3 | 85 | openrouter-qwen3-30b-a3b | 5/5 | Good — adequate, template leakage in consequences |
| 4 | 83 | openrouter-openai-gpt-oss-20b | 4/5 | Good — adequate specificity, 1 EOF failure |
| 5 | 86 | openrouter-openai-gpt-4o-mini | 5/5 | Medium — generic weaknesses |
| 6 | 82 | ollama-llama3.1 | 5/5 | Poor — very short consequences, formulaic |
| 7 | 81 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | n/a — total failure |

---

## Negative Things

### 1. Run 81: Total failure (model incompatible with JSON schema)

All 5 plans failed with identical error:

```
ValueError('Could not extract json string from output: ')
```

Source: `history/0/81_identify_potential_levers/outputs.jsonl` lines 1–5.

The model (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) returns empty output when asked to produce structured JSON. This is a structural model incompatibility, not a transient failure. The PR's retry logic would not resolve this.

### 2. Run 82: Consequence depth far below baseline

Run 82 (ollama-llama3.1) produces consequences of ~100–160 characters each — roughly 3–4× shorter than the baseline reference:

```json
"Immediate: Reduced construction time → Systemic: Lowered resource costs → Enhanced scalability"
```

Source: `history/0/82_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1.

The three-step chain format is present but all fields are abstract placeholders with no measurable indicators, violating the prompt's requirement: "Include measurable outcomes: 'Systemic: [a specific, domain-relevant second-order impact with a measurable indicator, such as a % change, capacity shift, or cost delta]'".

### 3. Run 82: Generic weakness fill-ins (template leakage)

Of 17 levers in run 82's silo output, 13 weaknesses follow the verbatim pattern `"The options fail to consider the potential for/impact on [generic noun]"` with no domain specificity:

- "…the potential for psychological manipulation within the controlled environment."
- "…the potential for technological obsolescence within the confined environment."
- "…the potential for information asymmetry within the controlled environment."
- "…the potential impact on social mobility."
- "…the potential impact on biodiversity."

Two levers (Silo Governance, Environmental Stewardship) have NO weakness sentence at all — only "Controls X vs. Y." — which is a hard constraint violation per the prompt's validation protocol.

Source: `history/0/82_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` levers 14, 16.

### 4. Run 85: Review text bleeds into consequences field

For lever "Resource Allocation Prioritization", the `consequences` field ends with the review text duplicated inline:

```json
"consequences": "Immediate: Diverts 60% of agricultural output to high-protein synthetic foods …
 Controls efficiency vs. equity. Weakness: The options fail to consider the psychological impact of dietary monotony.",
"review": "Controls efficiency vs. equity. Weakness: The options fail to consider the psychological impact of dietary monotony."
```

Source: `history/0/85_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1.

This is template leakage where the model has appended the review block inside the consequences field. The runner does not detect or strip it. Every downstream consumer of the consequences string receives contaminated content.

### 5. Run 83: One plan fails with JSON EOF (context truncation)

Plan `20260311_parasomnia_research_unit` failed with:

```
1 validation error for DocumentDetails
 Invalid JSON: EOF while parsing a list at line 36 column 5
```

Source: `history/0/83_identify_potential_levers/outputs.jsonl` line 4.

The response was truncated before the JSON array closed. This could be a model context-limit issue (model generates a very long response and hits a limit), not a transient network failure. Retries may or may not help — if the model reliably generates oversized responses for complex plans, retrying will reproduce the same truncation.

### 6. Run 87: One plan fails with per-call lever count violation

Plan `20250329_gta_game` failed with:

```
1 validation error for DocumentDetails
levers
  List should have at most 7 items after validation, not 8
```

Source: `history/0/87_identify_potential_levers/outputs.jsonl` line 2.

The model (claude-haiku-4-5-pinned) generated 8 levers in a single LLM call, exceeding the schema's max-7 limit. Retries will not help — the model has a tendency to over-generate and would likely reproduce the same count. This is a model compliance failure on count, not a transient error.

### 7. Consequence quality gap vs. baseline

The baseline silo reference (`baseline/train/20250321_silo/002-10-potential_levers.json`) has consequences averaging ~390 chars with domain-specific metrics and specific causal chains. Run 82 averages ~110–160 chars with abstract nouns. Only run 87 (claude-haiku) matches or exceeds baseline depth, at ~400–600 chars per consequence.

---

## Positive Things

### 1. Runs 82, 84, 85, 86: 5/5 plan success rate

Four of seven runs completed all five training plans without error. The retry infrastructure is not the driver here — these models simply handle JSON extraction reliably for this step.

### 2. Run 87 (claude-haiku): Exceptional content quality

Run 87's successful outputs are the highest-quality levers in this batch. Example from `history/0/87_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

```json
{
  "name": "Information Asymmetry Architecture",
  "consequences": "Immediate: Leadership restricts or curates information about external conditions, creating controlled narratives for residents → Systemic: Belief in external toxicity remains unquestioned, increasing compliance by ~40–60% but reducing capacity for independent decision-making and alternative planning → Strategic: Long-term stability depends on maintaining this information barrier; any breach of truth threatens social cohesion and may trigger rebellion or mass psychological distress.",
  "review": "Controls fabricated order vs. psychological autonomy. Weakness: The options fail to consider the psychological and neurological effects of prolonged isolation and sensory deprivation on residents, or how mass disillusionment might manifest when truth eventually emerges."
}
```

This consequence chain:
- Names a specific mechanism ("controlled narratives")
- Gives measurable Systemic impact ("~40–60% compliance increase")
- Articulates a genuine strategic tension ("breach of truth")
- The review weakness is domain-specific and non-generic

This matches the prompt's validation protocol format and exceeds baseline quality.

### 3. Retry infrastructure correctly added (PR #283 scope)

For transient API/network failures (not represented in these runs but plausible in production), the PR correctly adds RetryConfig with up to 2 retries and exponential backoff. This is sound defensive engineering.

### 4. All successful runs: Zero option prefix violations

The prompt prohibits "Option A:", "Choice 1:", "Conservative:", "Moderate:", "Radical:" prefixes. No violations were observed in runs 82–87. Schema enforcement appears effective here.

### 5. All successful runs: Exactly 3 options per lever

Schema enforces 3 options. Every lever across all successful runs complies. No over- or under-counting.

### 6. Run 83 and 84: Good measurable outcome inclusion

Both models (gpt-oss-20b and gpt-5-nano) include quantified metrics in most consequences:

```json
"consequences": "Immediate: Centralize procurement of bulk materials to secure volume discounts. Systemic: Lowers material cost by 12% but increases inventory holding costs by 8% and reduces flexibility to adapt to design changes. Strategic: Cost savings enhance budget slack but constrain design agility…"
```

Source: `history/0/83_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 2.

---

## Comparison

### Runs vs. baseline (silo plan)

| Source | Lever count | Avg consequence length (chars) | Measurable metrics present | Generic weaknesses |
|--------|-------------|-------------------------------|----------------------------|--------------------|
| Baseline train | 26 | ~390 (est.) | Yes | Mixed |
| Run 81 (nemotron) | 0 (all failed) | — | — | — |
| Run 82 (llama3.1) | 17 | ~130 (direct read) | No | 13/17 generic |
| Run 83 (gpt-oss-20b) | 19 | ~380 | Yes | Mixed |
| Run 84 (gpt-5-nano) | 19 | ~370 | Yes | Low |
| Run 85 (qwen3-30b) | 15 | ~387 | Yes | Low, but 1 bleed-in |
| Run 86 (gpt-4o-mini) | 16 | ~295 (est.) | Partial | Moderate |
| Run 87 (claude-haiku) | 21 | ~500 (direct read) | Yes, most | Low, domain-specific |

Notes:
- "Lever count" is the merged total across multiple LLM calls — the per-call max is 7. High counts indicate the step made ≥3 LLM calls per plan.
- Avg consequence length is estimated from direct file reads; some Explore agent estimates differed and are excluded.
- Baseline has 26 levers because it was produced by a high-capacity reference model with additional context.

### PR impact on failure modes

| Run | Error type | Would retries help? |
|-----|-----------|---------------------|
| 81 | Model produces no JSON | No — structural model failure |
| 83 | EOF while parsing JSON | Possibly — if truncation is non-deterministic |
| 87 | Schema: 8 levers > max 7 | No — model behavior, not transient |

---

## Quantitative Metrics

### Table 1: Operational reliability across runs

| Run | Model | Plans OK | Plans Failed | Failure category |
|-----|-------|----------|--------------|-----------------|
| 81 | nvidia-nemotron-3-nano-30b-a3b | 0/5 | 5/5 | JSON extraction failure |
| 82 | ollama-llama3.1 | 5/5 | 0/5 | — |
| 83 | openai-gpt-oss-20b | 4/5 | 1/5 | EOF JSON truncation |
| 84 | openai-gpt-5-nano | 5/5 | 0/5 | — |
| 85 | openrouter-qwen3-30b-a3b | 5/5 | 0/5 | — |
| 86 | openrouter-openai-gpt-4o-mini | 5/5 | 0/5 | — |
| 87 | anthropic-claude-haiku-4-5-pinned | 4/5 | 1/5 | Schema: 8 levers > max 7 |

Sources: `history/0/{run}_identify_potential_levers/outputs.jsonl` for each run.

### Table 2: Template leakage in review field (silo plan)

| Run | Total levers | Generic "fail to consider potential for/impact on" | Missing weakness | Review bleed into consequences |
|-----|-------------|----------------------------------------------------|-----------------|-------------------------------|
| 82 | 17 | 13/17 (76%) | 2/17 (12%) | 0 |
| 83 | 19 | 4/19 (21%) | 0 | 0 |
| 84 | 19 | 3/19 (16%) | 0 | 0 |
| 85 | 15 | 3/15 (20%) | 0 | 1/15 (7%) |
| 86 | 16 | 6/16 (38%) | 0 | 0 |
| 87 | 21 | 2/21 (10%) | 0 | 0 |

Note: "Generic" is counted when the weakness phrase could apply to any lever with no domain-specific reasoning. E.g., "The options fail to consider the potential impact on biodiversity" (run 82) is generic; "The options fail to consider jurisdictional constraints under German data protection law" (run 87) is domain-specific.

### Table 3: Consequence depth by run (silo plan, estimated from direct reads)

| Run | Shortest consequence (chars) | Longest consequence (chars) | Has measurable indicator |
|-----|-----------------------------|-----------------------------|--------------------------|
| 82 | ~95 | ~155 | No |
| 83 | ~200 | ~500 | Yes |
| 84 | ~300 | ~600 | Yes |
| 85 | ~200 | ~480 | Yes |
| 86 | ~130 | ~300 | Partial |
| 87 | ~350 | ~700 | Yes |
| Baseline | ~220 | ~750 | Yes |

### Table 4: Duration per plan (seconds)

| Run | Min | Max | Notes |
|-----|-----|-----|-------|
| 81 | 100 | 132 | All failed, time wasted |
| 82 | 73 | 123 | Fast (llama3.1) |
| 83 | 41 | 225 | Variable (1 failure at 158 s) |
| 84 | 193 | 237 | Slow (gpt-5-nano) |
| 85 | 76 | 127 | Medium |
| 86 | 52 | 72 | Fast |
| 87 | 125 | 210 | Slow (4 plans); gta failed at 169 s |

Sources: `outputs.jsonl` for each run.

---

## Evidence Notes

1. **Run 82 raw call structure confirmed**: `history/0/82_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows two `"responses"` entries: first batch produces levers 1–7 (`lever_index` 1–7); second batch produces levers 8+. The merged `002-10` therefore has 17 levers total. This is multi-call architecture by design. The schema's 7-lever-per-call limit does not cap the merged total.

2. **Baseline pipeline has deduplication**: `baseline/train/20250321_silo/` contains `002-11-deduplicated_levers_raw.json`. Runner history outputs only go through `002-10`. Comparing raw merged lever counts between history runs and baseline is valid; the baseline `002-10` was also the pre-dedup output.

3. **Run 85 template bleed confirmed** from `history/0/85_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1 (`7bcb5a0c`): the `consequences` string ends with "Controls efficiency vs. equity. Weakness: The options fail to consider the psychological impact of dietary monotony." — identical to the `review` field value.

4. **Run 87 parasomnia output quality**: `history/0/87_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` shows lever "Participant Stay Duration and Event-Yield Strategy" with ~500-char consequence including domain-specific estimates ("per-participant cost by approximately €3,200–4,800"). This demonstrates claude-haiku follows the domain-language instruction.

5. **Option count constraint enforcement**: Checked run 83 silo leverage 1–6: all have exactly 3 options. Same for runs 82, 84, 85, 86, 87. Schema validation enforces this consistently.

---

## Questions For Later Synthesis

1. **Is the dedup step (002-11) downstream of the runner's scope?** If so, high lever counts (15–21) in run outputs are normal and not a quality problem per se. The relevant count for content quality is per-call (capped at 7), not the merged total.

2. **Does the retry config actually fire in any run?** The PR adds retries, but none of the observed errors are transient. Synthesis should verify whether retry-class errors appear in other step experiments.

3. **Why does run 84 (gpt-5-nano) over-index on blockchain?** Multiple levers in the silo output end with a radical option referencing "blockchain-based" X. Is this a model training artifact or a prompt cue ("at least one unconventional/innovative approach")?

4. **Is run 87's 8-lever failure on gta_game related to plan complexity?** The gta_game plan may have a longer or more complex context that prompts the model to generate more levers. Should the prompt add a per-call count reminder?

5. **Does the option progression (conservative → moderate → radical) hold?** The prompt requires this ordering but run 87 sometimes starts with the radical option first. Should the prompt enforce ordering more explicitly?

---

## Reflect

The runs expose two separate orthogonal quality axes:

**Reliability axis**: Runs 81, 83 (partial), 87 (partial) show that model selection and per-call schema limits are the primary drivers of operational failure. PR #283's retry config adds correct defensive behavior but is unlikely to change success rates for the specific failure modes observed here — all three are structural or behavioral, not transient.

**Content quality axis**: The gap between run 82 (llama3.1) and run 87 (claude-haiku) is striking. The same prompt_2 produces 100-char abstract chains from llama3.1 and 500-char measurable, domain-specific chains from claude-haiku. This suggests the prompt's quality enforcement instructions (measurable indicators, domain-specific naming, specific weaknesses) are only effective for models with sufficient instruction-following capacity.

The template leakage in weaknesses (run 82: 76% generic) points to a prompt weakness: the review format ("Controls [Tension A] vs. [Tension B]. Weakness: The options fail to consider [specific factor].") is easy to satisfy with generic fill-ins. Weaker models treat the brackets as wildcard slots rather than as substitution guidance.

---

## Potential Code Changes

**C1** (Structural): The multi-call architecture merges 7 levers per call into 15–21 total per plan. Downstream steps (002-11 deduplication) reduce this. If the runner's outputs are compared to per-call expectations, analysts will incorrectly flag merged counts as violations. The runner could annotate `002-10-potential_levers.json` with a `call_count` field to make the multi-call structure explicit.
Evidence: `history/0/82_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows 2+ response objects merged into 17 levers.
Expected effect: Prevents false constraint-violation reports from analysts.

**C2** (Defensive): Run 87's failure is a schema validation error after response parsing. The runner could attempt to truncate the levers list to the max (7) instead of raising a validation error, since the content is otherwise valid. This would sacrifice one lever per call but avoid a total plan failure.
Evidence: `history/0/87_identify_potential_levers/outputs.jsonl` line 2: "List should have at most 7 items after validation, not 8".
Expected effect: Run 87 success rate improves from 4/5 to 5/5 for this class of failure.

**C3** (Fallback model): Run 81 fails 5/5 because the model cannot produce JSON at all. The retry config in PR #283 uses the same model for retries. Adding a fallback model (e.g., a known-reliable model for structured output) after exhausting primary retries would convert these failures to partial successes.
Evidence: `history/0/81_identify_potential_levers/outputs.jsonl` lines 1–5 — all five plans fail with the same error pattern, indicating a model-level issue, not a request-level transient.
Expected effect: Run 81 success rate improves from 0/5 to 5/5 (with fallback model).

---

## Hypotheses

**H1** (Prompt): Strengthen the weakness specificity requirement.
Current wording: "Identify a specific weakness: 'Weakness: The options fail to consider [specific factor].'" — models fill in generic nouns.
Proposed change: Add "The specific factor MUST be concrete and domain-relevant. Generic phrases ('potential impact on X', 'potential for Y') are prohibited. Cite an actual mechanism, a named stakeholder group, or a real constraint."
Evidence: Run 82 has 76% generic weaknesses; run 87 has 10% generic weaknesses. The difference correlates with instruction-following capacity, but strengthening the prohibition may close the gap for weaker models.
Expected effect: Generic weakness rate drops in runs 82 and 86 categories.

**H2** (Prompt): Add explicit example of a measurable systemic consequence.
Current wording: "'Systemic: [a specific, domain-relevant second-order impact with a measurable indicator, such as a % change, capacity shift, or cost delta]'". Weaker models ignore this and write "Systemic: Enhanced resource efficiency."
Proposed change: Provide a concrete negative example and a concrete positive example inline:
  - Bad: "Systemic: Improved productivity."
  - Good: "Systemic: Raises throughput by 15% but increases raw material cost by 8%, compressing margin on standardized units."
Evidence: Run 82 averages ~130-char consequences with no quantitative content; run 83 averages ~380 chars with inline percentages. An example may raise run 82 closer to run 83.
Expected effect: Measurable-indicator compliance improves for llama3.1 and gpt-4o-mini class models.

**H3** (Prompt): Prevent review field from being appended inside consequences.
Current wording does not mention field separation. Models with lower instruction-following (run 85) conflate the two fields.
Proposed change: Add "The `consequences` field MUST NOT contain any trade-off summary or weakness statement. Those belong only in `review_lever`."
Evidence: `history/0/85_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1 shows the bleed-in pattern.
Expected effect: Eliminates field contamination in run 85 class models.

---

## Summary

Seven models were tested against prompt_2 for `identify_potential_levers` across 5 training plans (35 plan runs total):

- **Run 81** (nvidia-nemotron-3-nano-30b): Complete failure (0/5) — model cannot generate JSON. Retry config (PR #283) will not help. This model should be excluded from future experiments for this step.
- **Run 82** (llama3.1): Perfect reliability (5/5) but lowest content quality — very short abstract consequences (~130 chars), 76% generic weaknesses, 12% missing weakness fields. Requires prompt reinforcement or model replacement.
- **Run 83** (gpt-oss-20b): Good quality (4/5), one EOF truncation failure that retries may occasionally resolve but not reliably.
- **Run 84** (gpt-5-nano): Good quality (5/5), specific measurable outcomes, but over-indexes on blockchain in radical options.
- **Run 85** (qwen3-30b): Good quality (5/5), but one instance of review text contaminating the consequences field — a clear prompt compliance failure.
- **Run 86** (gpt-4o-mini): Medium quality (5/5), consequences shorter than baseline, moderate generic weaknesses.
- **Run 87** (claude-haiku-4-5-pinned): Best content quality (4/5), longest and most domain-specific consequences (~500 chars), 10% generic weakness rate. One failure from exceeding the 7-lever-per-call schema limit — not addressable by retries.

**PR #283 assessment**: The retry config is correctly implemented defensive infrastructure. However, none of the three observed failure modes (structural model incompatibility, JSON truncation, schema count violation) are classic transient failures. The PR is unlikely to improve the 30/35 success rate. Its value lies in protecting against network-level transient failures not observed in this batch.

**Top improvement opportunities**:
1. Prompt H1: Prohibit generic weakness phrases explicitly (impacts runs 82, 86)
2. Code C2: Gracefully truncate 8-lever responses to 7 instead of hard-failing (impacts run 87 class)
3. Code C3: Add a fallback model for JSON-extraction-incapable models (impacts run 81 class)
4. Prompt H2: Provide concrete positive/negative examples for measurable systemic consequences (impacts runs 82, 86)
