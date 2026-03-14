# Insight Claude

Analysis of `identify_potential_levers` outputs across history runs 00–09, compared against baseline. All runs use the same registered prompt (`prompt_0_fa5dfb88...`). Each run produces 15 levers per plan (3 LLM calls x 5 levers).

## Rankings

**Tier 1 — Genuinely better than baseline:**
1. **Run 09** (`anthropic-claude-haiku-4-5-pinned`) — Best overall. Unique lever names, deeply project-grounded, reviews 5–7x longer than any other run with specific failure-mode analysis.
2. **Run 04** (`openrouter-stepfun-step-3-5-flash`) — Excellent quality but only 3/5 plans succeeded. Creative, vivid, domain-specific. The best levers in the entire dataset come from 04 and 09.

**Tier 2 — Comparable to baseline:**
3. **Run 01** (`openrouter-openai-gpt-oss-20b`) — Solid conservative/moderate/radical option progression with technical specificity. Some name repetition across calls.
4. **Run 05** (`openrouter-qwen3-30b-a3b`) — Good quality, creative option details, some duplication across calls.

**Tier 3 — Worse than baseline or flawed:**
5. **Baseline** (`gemini-2.0-flash`) — Consistent but formulaic. Heavy concept repetition (sovereign_identity: 5 concepts repeated 3x = 15 levers).
6. **Run 02** (`openai-gpt-5-nano`) — Good lever names but critically damaged by "25% faster scaling" appearing in 14/15 consequences fields on silo. A robotic template pattern.
7. **Run 07** (`openrouter-openai-gpt-4o-mini`) — Weakest successful run. sovereign_identity is literally the same 5 concepts repeated 3 times with paraphrased options. Reviews average 83–86 characters — the shortest of all runs.
8. **Run 00** (`ollama-llama3.1`) — Worst overall. Bracket placeholders in reviews, 4/15 levers have fewer than 3 options on sovereign_identity, copies the example lever name from the system prompt.

**Failed runs:** 03 (schema instead of data), 06 (empty output), 08 (config error).

## Quantitative Evidence

### Unique Lever Names (Exact Match)

| Run | Model | Silo Unique/15 | Sovereign Identity Unique/15 |
|-----|-------|:-:|:-:|
| Baseline | gemini-2.0-flash | 10 | 5 |
| 00 | ollama-llama3.1 | 13 | 13 |
| 01 | openrouter-openai-gpt-oss-20b | 12 | 10 |
| 02 | openai-gpt-5-nano | 8 | 15 |
| 04 | openrouter-stepfun-step-3-5-flash | 15 | N/A (failed) |
| 05 | openrouter-qwen3-30b-a3b | 12 | 10 |
| 07 | openrouter-openai-gpt-4o-mini | 10 | 5 |
| 09 | anthropic-claude-haiku-4-5-pinned | 8 | 15 |

Baseline and 07 score 5/15 on sovereign_identity — meaning the same 5 concepts are used across all 3 calls. Run 09 and 02 achieve perfect 15/15 uniqueness on sovereign_identity. On silo, only 04 achieves 15/15.

Exact-match uniqueness is misleading for runs 02 and 09 on silo. Both have ~8 exact-unique names, but for different reasons: 09 uses near-synonyms like "Resource Allocation Strategy" / "Resource Optimization Strategy" (conceptually the same lever with different titles), while 02's lever names ARE diverse but the consequences content is robotically identical.

### Average Review Length (Characters)

| Run | Silo | Sovereign Identity |
|-----|-----:|---:|
| Baseline | 108 | 107 |
| 00 | 100 | 82 |
| 01 | 98 | 100 |
| 02 | 104 | 121 |
| 04 | 136 | N/A |
| 05 | 99 | 103 |
| 07 | 86 | 83 |
| **09** | **503** | **685** |

Run 09 reviews are 5–7x longer than every other run. This is not padding — the extra length contains specific failure-mode analysis, entity names, and budget figures.

### Option Count Violations

- **Run 00, sovereign_identity**: 4 out of 15 levers have fewer than 3 options (2 levers with 2 options, 2 levers with 1 option). The model fails the "exactly 3 options" constraint in later "more" calls.
- **Run 09, sovereign_identity**: 1 lever has a garbage 4th option (`" Consequences, Review, Options"`) — a hallucinated schema fragment.
- All other runs: exactly 3 options per lever on all plans.

### Placeholder / Template Patterns

- **Run 00**: 5/15 silo levers contain bracket placeholders in reviews: `"Controls Trade-off between [Scalability] vs. [Cost Efficiency]."` The model copies the prompt's template literally.
- **Run 02**: 14/15 silo levers contain `"25% faster scaling"` in the consequences field. The model found one acceptable metric and applied it mechanically to everything.
- **Run 00**: Copies the system prompt's example lever name "Material Adaptation Strategy" and uses it for the sovereign_identity plan — which has nothing to do with materials.

## Qualitative Evidence

### Strong Lever Names (project-grounded, specific)

- Run 09, silo: `"Population Composition & Demographic Control"`
- Run 09, sovereign_identity: `"Procurement Language Anchor Point: Danish Unilateral vs. EU-Embedded Requirements"`
- Run 09, sovereign_identity: `"Phase Three Contingency Reallocation: Procurement Push vs. Standards and Publication Focus"`
- Run 04, silo: `"Psychosocial Resilience Engine"`, `"Excavation Velocity Strategy"`, `"Crisis Autarky Level"`

### Weak Lever Names (generic, template-copied)

- Run 00, sovereign_identity: `"Material Adaptation Strategy"` — literally copied from the system prompt example
- Run 07, sovereign_identity: `"Supplier Diversification Strategy"` (repeated 3x across calls)
- Run 07, silo: `"Resource Allocation Strategy"` (repeated 2x with near-identical options)
- Baseline, sovereign_identity: `"Coalition Building Strategy"` (repeated 3x)

### Strong Review Excerpts

Run 09, silo, "Construction Sequencing and Capital Deployment":
> The options ignore geopolitical risk; a massive construction project mobilizing tens of thousands of workers and hundreds of billions in funding will inevitably trigger government investigation, international scrutiny, and potential seizure. None address strategies for regulatory capture, political narrative management, or diplomatic positioning to neutralize state intervention.

Run 04, silo, "Information & Narrative Control":
> Controls Stability vs. Truth. Weakness: The options assume a static outside condition and do not plan for the scenario where the outside becomes verifiably safe, creating an irreconcilable conflict between the control narrative and observable reality.

Run 09, sovereign_identity, "Incumbent Operator Engagement and Adversarial Risk":
> The collaborative early-adopter approach assumes smaller banks want to diversify authentication without alienating the dominant MitID ecosystem, a risky assumption if market pressure favors consolidation over redundancy. The transparent multi-stakeholder model may simply give the incumbent operator a seat at the table to slow decisions without committing to change.

### Weak Review Excerpts

Run 00, silo:
> Controls Trade-off between [Scalability] vs. [Cost Efficiency]. Weakness: The options fail to consider the impact of [Silo Architecture on Mental Health].

Run 07, sovereign_identity:
> Controls Cost vs. Quality. Weakness: The options may not adequately address the immediate budget constraints faced by public entities.

Run 00, sovereign_identity:
> Controls dependency vs. autonomy. Weakness: The options fail to consider the complexities of existing infrastructure.

## Code Bug: Double User Prompt

Confirmed: `identify_potential_levers.py` sends the user prompt twice on the first call.

The code pre-loads `chat_message_list` with `[SYSTEM, USER(user_prompt)]` (lines 148–157), then the loop (lines 167–173) appends the same `user_prompt` again before the first call:

- **Call 1**: `[SYSTEM, USER(prompt), USER(prompt)]` — prompt sent twice
- **Call 2**: `[SYSTEM, USER(prompt), USER(prompt), ASSISTANT(resp1), USER("more")]`
- **Call 3**: `[SYSTEM, USER(prompt), USER(prompt), ASSISTANT(resp1), USER("more"), ASSISTANT(resp2), USER("more")]`

This likely contributes to the repetition problem across calls. The model sees the same prompt context twice and then receives a bare "more" instruction — which gives it no guidance about avoiding repetition with previous responses.

## Prompt Improvement Hypotheses

### H1: Fix the double-prompt bug and replace "more" with a targeted continuation

The code sends the user prompt twice (confirmed bug) and uses bare `"more"` for continuation. Replace with a continuation prompt like: *"Generate 5 additional levers that are materially distinct from the levers you have already produced. Do not repeat or rephrase any strategic dimension already covered. Focus on second-order risks, implementation-specific decisions, and project-specific constraints not yet addressed."*

**Evidence**: Runs with the worst cross-call duplication (baseline: 5 unique/15 on sovereign_identity, run 07: 5 unique/15) show the model simply regenerating the same categories. A targeted continuation would directly attack this.

### H2: Enforce uniqueness — reject duplicate lever names in code

Add post-response validation: if a newly generated lever name fuzzy-matches a previous lever name, retry or discard. Currently no validation exists — the merge step (lines 207–223) is a blind concatenation.

**Evidence**: Every run except 04 (silo) has significant cross-call duplication. Deduplication exists as a separate downstream step (`deduplicate_levers.py`) but runs too late — the optimizer already wasted 2/3 of its budget generating duplicates.

### H3: Require project-specific anchoring in lever names

Add to the system prompt: *"Every lever name must reference a specific entity, technology, constraint, or measurable factor from the source material. Do not use generic labels like 'Resource Allocation Strategy' or 'Coalition Building Strategy'."*

**Evidence**: The gap between run 09's `"Procurement Language Anchor Point: Danish Unilateral vs. EU-Embedded Requirements"` and run 07's `"Supplier Diversification Strategy"` is entirely explained by whether the model anchors to project specifics. The strongest lever names (04, 09) contain project nouns; the weakest (00, 07, baseline) are generic strategy labels.

### H4: Ban template leakage explicitly

Add: *"Do not use square-bracket placeholders. Do not use the template pattern 'Controls X vs. Y' unless you fill in specific, project-grounded tensions. Do not copy lever names from any examples."*

**Evidence**: Run 00 copies the system prompt's example name ("Material Adaptation Strategy") and uses bracket placeholders verbatim. The template pattern `"Controls Trade-off between [X] vs. [Y]"` appears in 5/15 silo levers.

### H5: Set a review length floor

Add: *"Each review must be at least 150 characters and must identify at least one specific failure mechanism not already named in the lever title or options."*

**Evidence**: Runs 00 and 07 average 82–86 characters per review — too short for substantive criticism. Run 09 averages 503–685 characters. A floor of ~150 characters would push the weaker models toward more substance without requiring 09-level verbosity.

### H6: Separate generation from critique

The system prompt overloads one call with formatting, strategy generation, option design, and critical review. Split into: (1) generate levers and options, (2) a second pass that reviews and critiques. This reduces instruction complexity per call.

**Evidence**: The weakest models (00, 07) struggle with multiple constraints simultaneously — they follow the structural template but produce shallow content. Separating concerns may improve compliance.

## What Codex Got Wrong

1. **Codex claims run 02 is "the cleanest structured run" with "15 unique lever names on all 5 train plans."** This is misleading. While 02 has unique names on sovereign_identity, the silo output has only 8 exact-unique names, and — critically — 14/15 consequences fields contain the robotic `"25% faster scaling"` metric. This is structural compliance masking content failure.

2. **Codex undervalues run 04.** It's dismissed as "partially usable" (3/5) but the 3 plans that succeeded contain some of the best individual levers in the entire dataset. "Psychosocial Resilience Engine", "Crisis Autarky Level", and "Excavation Velocity Strategy" are more creative and grounded than anything in runs 02 or 05.

3. **Codex says run 09 "overshoots in verbosity."** This frames depth as a trade-off. The extra length in run 09 reviews is almost entirely substantive analysis — failure modes, entity-specific risks, budget-aware critique. The problem isn't verbosity; it's that other runs are too shallow.

4. **Codex misses the double-prompt bug severity.** It notes the bug exists but treats it as a minor code smell. The double-prompt likely amplifies cross-call duplication by biasing the model toward the original prompt's framing, making "more" calls produce variations-on-a-theme rather than genuinely new strategic dimensions.

5. **Codex doesn't quantify the baseline weakness.** Baseline scores 5/15 unique names on sovereign_identity — meaning 10 out of 15 levers are duplicates. That's the bar we're trying to beat. Most runs clear it easily on name diversity alone; the real question is content depth.

## Key Takeaway

The prompt is not broken — run 09 proves it can produce excellent output. The problem is fragile: most models fall into repetition, generic labels, and template-following. The highest-leverage fixes are (1) fix the double-prompt bug, (2) replace "more" with an anti-repetition continuation prompt, and (3) add post-generation validation to reject duplicates before they accumulate. These are code changes, not prompt changes, and they would improve output quality across all models.
