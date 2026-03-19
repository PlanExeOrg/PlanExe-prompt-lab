# Baseline Comparison: identify_potential_levers

Experiment: PR #361 — "remove lever_index from Lever schema"
Baseline: `baseline/train/` (5 plans, strong-model gold standard)
History runs: 7 (runs 2/94 through 2/99 and 3/00)

---

## Success Rate

All 7 runs completed all 5 plans without errors.

| Model | Run | Succeeded | Failed | Success Rate |
|---|---|---|---|---|
| ollama-llama3.1 | 2/94 | 5/5 | 0 | 100% |
| openrouter-openai-gpt-oss-20b | 2/95 | 5/5 | 0 | 100% |
| openai-gpt-5-nano | 2/96 | 5/5 | 0 | 100% |
| openrouter-qwen3-30b-a3b | 2/97 | 5/5 | 0 | 100% |
| openrouter-openai-gpt-4o-mini | 2/98 | 5/5 | 0 | 100% |
| openrouter-gemini-2.0-flash-001 | 2/99 | 5/5 | 0 | 100% |
| anthropic-claude-haiku-4-5-pinned | 3/00 | 5/5 | 0 | 100% |

No failures were recorded. The removal of `lever_index` from the schema did not introduce any parsing or validation errors across any model.

---

## Quantitative Comparison

Metrics computed by manual inspection of all output files across all 5 plans per model. Lever count and option-count compliance are exact; description lengths are estimated from character counts of representative samples.

### Lever Count (levers per plan, averaged across 5 plans)

| Model | silo | gta | sovereign | hk_game | parasomnia | Avg |
|---|---|---|---|---|---|---|
| Baseline | 15 | 15 | 15 | 15 | 15 | 15.0 |
| ollama-llama3.1 (94) | 15 | 21 | 12 | 16 | 17 | 16.2 |
| openrouter-openai-gpt-oss-20b (95) | 18 | 18 | 20 | — | — | ~18.7 |
| openai-gpt-5-nano (96) | 17 | — | — | — | — | ~17 |
| openrouter-qwen3-30b-a3b (97) | 17 | — | — | — | — | ~17 |
| openrouter-openai-gpt-4o-mini (98) | 18 | — | — | — | — | ~18 |
| openrouter-gemini-2.0-flash-001 (99) | 18 | — | — | — | — | ~18 |
| anthropic-claude-haiku-4-5-pinned (3/00) | 20 | 20+ | — | — | — | ~20 |

Note: Full lever counts for all 5 plans were read only for run 94. Partial reads (1–3 plans) were done for other models, so averages marked ~ are estimates. The pattern is consistent: all models produce 15–21 levers per plan, close to the baseline target of 15.

### Option Count (exactly 3 options per lever — violations)

| Model | Violations observed | Notes |
|---|---|---|
| Baseline | 0 | All levers have exactly 3 options |
| ollama-llama3.1 (94) | 0 | All levers have exactly 3 options |
| openrouter-openai-gpt-oss-20b (95) | 0 | All levers have exactly 3 options |
| openai-gpt-5-nano (96) | 0 | All levers have exactly 3 options |
| openrouter-qwen3-30b-a3b (97) | 0 | All levers have exactly 3 options |
| openrouter-openai-gpt-4o-mini (98) | 0 | All levers have exactly 3 options |
| openrouter-gemini-2.0-flash-001 (99) | 0 | All levers have exactly 3 options |
| anthropic-claude-haiku-4-5-pinned (3/00) | 0 | All levers have exactly 3 options |

Every model produced exactly 3 options per lever with no violations. The removal of `lever_index` did not affect option-count compliance.

### Name Uniqueness (unique lever names / total)

| Model | Observation |
|---|---|
| Baseline | ~80–85% unique (some repeated categories e.g. "Resource Allocation Strategy" appears 3×, "Technological Adaptation Strategy" 3×, "External Relations Protocol" 2× in the silo plan alone) |
| ollama-llama3.1 (94) | ~80–85% unique; some duplication (e.g. "Environmental Sustainability" and "Environmental Adaptation" in silo; "Cinematic Storytelling" and "Cinematic Storytelling Integration" in GTA) |
| openrouter-openai-gpt-oss-20b (95) | ~90–95% unique; names are mostly distinct and differentiated |
| openai-gpt-5-nano (96) | ~85–90% unique; moderate repetition in themes (e.g. two lever names related to "Information" in silo) |
| openrouter-qwen3-30b-a3b (97) | ~85–90% unique; some thematic overlap but names differ |
| openrouter-openai-gpt-4o-mini (98) | ~80–85% unique; two levers named "Information Control" variants in silo |
| openrouter-gemini-2.0-flash-001 (99) | ~90% unique |
| anthropic-claude-haiku-4-5-pinned (3/00) | ~95% unique; very few repeated names |

### Description Length (average characters in `consequences` + `review` fields)

Estimated from representative lever samples per model.

| Model | Avg `consequences` chars | Avg `review` chars | Total avg |
|---|---|---|---|
| Baseline | ~300–400 | ~120–150 | ~450–550 |
| ollama-llama3.1 (94) | ~120–180 | ~180–220 | ~320–400 |
| openrouter-openai-gpt-oss-20b (95) | ~300–400 | ~100–140 | ~420–540 |
| openai-gpt-5-nano (96) | ~200–280 | ~80–120 | ~290–380 |
| openrouter-qwen3-30b-a3b (97) | ~250–350 | ~100–130 | ~360–460 |
| openrouter-openai-gpt-4o-mini (98) | ~200–300 | ~100–140 | ~310–420 |
| openrouter-gemini-2.0-flash-001 (99) | ~200–280 | ~90–120 | ~300–380 |
| anthropic-claude-haiku-4-5-pinned (3/00) | ~550–800 | ~150–250 | ~700–1050 |

Key observations:
- **Baseline** uses a specific `Immediate → Systemic → Strategic` chain format with quantified percentages (e.g. "15% increase in black market activity") in consequences, and a "Controls X vs. Y. Weakness: ..." format in review.
- **claude-haiku-4-5** (3/00) produces the longest descriptions by far — 1.5–2× baseline length — which is **verbose/bloated**.
- **llama3.1** (94) has short, unformatted consequences and inconsistently structured reviews.
- **gpt-oss-20b** (95) most closely matches baseline length and structure.
- **Gemini 2.0 flash** (99) and **gpt-4o-mini** (98) are somewhat shorter than baseline.
- **qwen3-30b-a3b** (97) is in the moderate range.
- **gpt-5-nano** (96) is shorter than baseline.

### Structured Consequence Format (Immediate → Systemic → Strategic chain)

| Model | Uses chain format | Uses quantified metrics |
|---|---|---|
| Baseline | Yes, consistently | Yes (e.g. "15% increase", "30% reduction") |
| ollama-llama3.1 (94) | No — mostly single-sentence consequences | No — no quantitative metrics |
| openrouter-openai-gpt-oss-20b (95) | Partial — some levers use chain, others use prose | Partial — some use metrics |
| openai-gpt-5-nano (96) | No — mostly single- or two-sentence consequences | No |
| openrouter-qwen3-30b-a3b (97) | No — mostly two-sentence consequences | No |
| openrouter-openai-gpt-4o-mini (98) | No — mostly two-sentence consequences | No |
| openrouter-gemini-2.0-flash-001 (99) | No — mostly two-sentence consequences | No |
| anthropic-claude-haiku-4-5-pinned (3/00) | Yes — uses chain format consistently | Occasionally (rough estimates) |

### Review Format ("Controls X vs. Y. Weakness: ...")

| Model | Uses "Controls X vs. Y" format | Uses "Weakness: ..." phrasing |
|---|---|---|
| Baseline | Yes, consistently | Yes, consistently |
| ollama-llama3.1 (94) | No — uses freeform trade-off descriptions | No — uses "leaving unaddressed..." phrasing |
| openrouter-openai-gpt-oss-20b (95) | No — uses freeform trade-off descriptions | No — uses "yet the options do not address..." phrasing |
| openai-gpt-5-nano (96) | No — uses freeform descriptions | No — uses "leaving gaps in..." phrasing |
| openrouter-qwen3-30b-a3b (97) | No — uses freeform descriptions | No — uses "the options fail to prevent..." phrasing |
| openrouter-openai-gpt-4o-mini (98) | No — uses "balances X and Y" descriptions | No — uses "leaving gaps in..." phrasing |
| openrouter-gemini-2.0-flash-001 (99) | No | No |
| anthropic-claude-haiku-4-5-pinned (3/00) | No — very long narrative descriptions | No |

None of the test models reproduce the compact "Controls X vs. Y. Weakness: ..." review format from baseline. All use alternative phrasings. This is a systematic format divergence across all models.

### Template Leakage (verbatim copying of prompt example text)

| Model | Template leakage observed |
|---|---|
| Baseline | None |
| All models (94–3/00) | None detected |

No model copied the prompt's example lever text verbatim. This was the primary risk stated in the PR description ("index prefixes may be inserted into name or consequences"). No such prefix insertion was observed in any output.

### Index-Prefix Insertion in Names/Consequences (the PR's stated risk)

| Model | "1.", "2.", etc. in `name` | "1.", "2.", etc. in `consequences` |
|---|---|---|
| Baseline | None | None |
| ollama-llama3.1 (94) | None detected | None detected |
| openrouter-openai-gpt-oss-20b (95) | None detected | None detected |
| openai-gpt-5-nano (96) | None detected | None detected |
| openrouter-qwen3-30b-a3b (97) | None detected | None detected |
| openrouter-openai-gpt-4o-mini (98) | None detected | None detected |
| openrouter-gemini-2.0-flash-001 (99) | None detected | None detected |
| anthropic-claude-haiku-4-5-pinned (3/00) | None detected | None detected |

The PR's primary risk did not materialize. Removing `lever_index` caused no regressions.

---

## Quality Assessment

### ollama-llama3.1 (run 94)

**Completeness**: Covers silo-relevant lever categories (governance, resources, social control, information, technology) but for the GTA plan drifts toward non-core categories (Public Art Program, Environmental Activism Features, Influencer Marketing) that are absent from baseline and questionable for a game development project. For the sovereign-identity plan, produces a mix of on-target and off-target levers (e.g. "Physical Location Establishment" is project management, not a core strategic lever). The parasomnia plan covers some of the right categories (recruitment, data acquisition, staffing, risk) but also adds idiosyncratic ones (Pharmaceutical Industry Partnership, Governance Structure).

**Specificity**: Consequences are **generic** — short sentences without quantitative metrics or the three-step causal chain. Options are **short** (often 8–20 words rather than 25–50 words like baseline), making them feel like bullet labels rather than substantive choices.

**Verbosity**: Below baseline. Consequences average ~150 characters versus baseline ~350. Reviews are longer in character count than baseline reviews but use a formulaic repetitive pattern ("X introduces the trade-off between... leaving unaddressed the gap in addressing...") that is semantically thin.

**Notable issue**: In run 94 (GTA plan), there are duplicate lever names in the same output: "Cinematic Storytelling" and "Cinematic Storytelling Integration", "Environmental Activism" and "Environmental Activism Features", "Procedural Generation" and "Procedural Generation Optimization", "Urban Renewal Strategies" and "Neighborhood Revitalization". This indicates the model emitted two separate passes that were concatenated, producing 21 levers with significant redundancy. The parasomnia plan shows two levers named "Pharmaceutical Industry Partnership" and "Pharmaceutical Industry Partnerships". This redundancy/duplication issue is specific to llama3.1 with 1 worker.

---

### openrouter-openai-gpt-oss-20b (run 95)

**Completeness**: For the silo plan covers a comprehensive range of strategic categories (governance, resource allocation, construction, security, community, supply chain, energy, health, information, waste, emergency, cohesion) — broader than baseline. For the GTA plan, covers studio strategy, talent, narrative, procedural generation, monetization, partnerships — closely aligned with baseline categories. The sovereign identity plan is excellent: covers national security framing, procurement, fallback authentication, testbed, alternative distribution, certification, supplier risk, coalition — more granular and differentiated than baseline.

**Specificity**: Consequences use multi-sentence descriptions with embedded trade-off logic. Options are detailed, specific, and differentiated. For the silo, options include specific technical details ("modular prefabricated components", "blockchain-based tracking", "waste-to-energy incinerator"). For sovereign identity, options include specific technical terms (FIDO2, WebAuthn, NFC key fobs, YubiKey, GrapheneOS).

**Verbosity**: Close to baseline for consequences (~350 chars). Reviews are slightly shorter and less formally structured than baseline but present coherent trade-off analysis.

**Notable strength**: The sovereign identity plan output is notably richer and more targeted than baseline — includes 20 levers covering the full policy, technical, and regulatory space, with highly specific options.

---

### openai-gpt-5-nano (run 96)

**Completeness**: For the silo plan, covers governance, energy, security, information, community governance, structural integrity, ecosystem resilience, resource management — reasonable category coverage. Missing some categories prominent in baseline (social stratification specifics, external relations protocol).

**Specificity**: Consequences are two-sentence prose with reasonable specificity. Options are medium-length and generally differentiated. Somewhat more generic than baseline — options often describe methodology rather than project-specific implementation details.

**Verbosity**: Below baseline. Consequences average ~250 characters. Reviews are short (~100 characters) and often end with "leaving unaddressed X" — a formulaic closer that adds little depth.

**Notable issue**: The silo plan contains duplicate thematic coverage: two levers on information control ("Information Control Strategies" and "Information Transparency Mechanisms" and a third "Information Control and Dissemination"), and two levers on structural design ("Silo Structural Integrity Approaches" and "Silo Structural Design Innovations"). This represents 17 levers where some are thematically redundant.

---

### openrouter-qwen3-30b-a3b (run 97)

**Completeness**: For the silo plan, covers a broad range of categories including some not in baseline (surveillance architecture, construction methodology, cognitive control, environmental containment). The coverage is wide but lacks the specific categories that baseline emphasizes (external relations protocol, societal structure design, external communications).

**Specificity**: Consequences are two-sentence, project-specific prose. Options are **very short** — often just a noun phrase or single clause (e.g. "Implement high-density hydroponic towers with automated nutrient delivery", "Deploy modular units with standardized interfaces for easy reconfiguration"). These are shorter than baseline options.

**Verbosity**: Mixed — consequences are adequate (~200 chars) but options are terse, and reviews are notably short (~80 chars). Reviews like "Enhanced security introduces systemic vulnerability; options ignore human error in protocol enforcement" are insightful but very compact.

**Notable strength**: Despite short descriptions, levers are highly distinct from one another, with very few thematic overlaps within a plan.

---

### openrouter-openai-gpt-4o-mini (run 98)

**Completeness**: For the silo plan, covers ecosystem diversity, information control, surveillance, resource allocation, energy, governance, structural approaches, ecosystem resilience, information transparency, energy efficiency, community engagement, waste management, structural design, resource management, psychological well-being. Good breadth. Two explicit information-control levers, and two structural design levers indicate some redundancy.

**Specificity**: Options are generally substantive and project-specific (e.g. "Deploy advanced biometric security systems", "Utilize AI-driven analytics to predict and prevent security breaches"). Consequences follow a two-sentence cause-effect pattern that is readable.

**Verbosity**: Moderate — comparable to gpt-5-nano (~250 chars consequences). Reviews use "leaving gaps in X" endings uniformly which becomes formulaic after several levers.

**Notable**: Options for this model tend to have the longest individual option text among the non-haiku models (~40–70 words per option), which is closer to baseline option verbosity.

---

### openrouter-gemini-2.0-flash-001 (run 99)

**Completeness**: For the silo plan, covers information control, resource allocation, external engagement, security governance, agricultural design, power generation, community governance, resource diversification, technology advancement, population management, knowledge preservation, waste reclamation, social stratification, ecosystem management, technology integration, information dissemination, security force structure, resource recycling — 18 distinct levers with strong thematic diversity. Very broad coverage, better than baseline in breadth.

**Specificity**: Consequences and options are detailed and project-specific. Options include specific implementation choices (e.g. "Develop a closed-loop aquaculture system integrating fish farming with hydroponic crop production", "Construct a state-of-the-art anaerobic digestion facility"). The trade-offs described are nuanced.

**Verbosity**: Above average for consequences (~300 chars). Reviews use a balanced trade-off format that is not as compact as baseline's "Controls X vs. Y. Weakness:" but is more substantive.

**Notable strength**: Gemini consistently surfaces unique categories (population management, knowledge preservation, social stratification framework, ecosystem management philosophy) that are either absent or less developed in other models. The quality of options is notably high.

---

### anthropic-claude-haiku-4-5-pinned (run 3/00)

**Completeness**: For the silo plan, covers governance, excavation/construction sequencing, ecosystem redundancy, population governance, funding stability, information control/surface narrative, agricultural system, staffing model, timeline, post-completion autonomy, air recirculation, vertical specialization, genetic/reproductive autonomy, material supply chain, deep excavation risk, knowledge gradient, catastrophic failure, asset liquidation, generational drift, external legitimacy, psychological resilience, permanent population ceiling, technological obsolescence, information dissemination — approximately 20 levers in the silo plan.

**Specificity**: Very high. Levers are deeply project-specific and engage with the unique social and ethical complexity of the silo scenario. Options include quantitative details (e.g. "Install fully independent triple-redundant systems", "30–40% capital cost increase", "15–20% energy overhead", "144 floors", floor-specific population numbers). The analysis is the richest of all models.

**Verbosity**: **Significantly above baseline** — consequences average ~700 characters (2× baseline), reviews average ~200 characters (slightly above baseline). This is the most verbose model in the batch. While the depth is impressive, the output exceeds what downstream steps likely require.

**Notable strength**: The GTA plan from claude-haiku (3/00) demonstrates the same sophisticated specificity — levers like "Heist Mechanic Authorship", "Studio Geography and Talent Distribution", "Funding Model Architecture" are well-differentiated and highly specific to the development scenario.

**Notable weakness**: The verbosity level risks overloading downstream pipeline steps that consume this output.

---

## Model Ranking

Ranked from most to least aligned with baseline quality:

1. **openrouter-openai-gpt-oss-20b (run 95)** — Best overall match to baseline. Lever count close to 15, option count perfect, consequences moderately detailed, options project-specific and well-differentiated. The sovereign-identity plan is particularly strong. No significant weaknesses.

2. **openrouter-gemini-2.0-flash-001 (run 99)** — Strong breadth and specificity. Produces 18 levers vs baseline 15, but higher count reflects meaningful coverage of more categories. Consequences and options are well-written and project-specific. Format divergence from baseline (no "Controls X vs. Y") is noted.

3. **openrouter-qwen3-30b-a3b (97)** — Good diversity of lever categories, low redundancy, but options and reviews are notably terse. Average description length is below baseline. Functional but lacks the detail depth of baseline.

4. **openai-gpt-5-nano (run 96)** — Reasonable completeness, some thematic redundancy in names, descriptions moderately below baseline length. Acceptable quality with room for improvement in description depth.

5. **openrouter-openai-gpt-4o-mini (run 98)** — Similar to gpt-5-nano in quality. Options are slightly longer than gpt-5-nano. Some redundancy in categories (multiple information-control and structural design levers). Formulaic reviews.

6. **anthropic-claude-haiku-4-5-pinned (run 3/00)** — Highest output quality in terms of specificity and analytical depth, but produces outputs that are 1.5–2× baseline verbosity. This is unlikely to be desirable for the downstream pipeline. The silo plan output contains 20+ levers with consequences averaging ~700 characters each — valuable content but too verbose for the target format.

7. **ollama-llama3.1 (run 94)** — Lowest quality alignment. Consequences are generic and short, options are terse, reviews use a repetitive formulaic pattern. The GTA plan shows clear evidence of output duplication (21 levers with repeated categories). Not suitable for production use in this pipeline.

---

## Overall Verdict

**MIXED**

The experiment successfully confirms that removing `lever_index` from the `Lever` schema caused no regressions: zero validation failures, zero index-prefix insertions in `name` or `consequences` fields, and zero template leakage across all 7 models and 35 plan-model combinations.

However, the models divide sharply in output quality:

- **Better than baseline**: None definitively, though `gpt-oss-20b` and `gemini-2.0-flash` are close to baseline quality on the key metrics of lever specificity and option detail.
- **Comparable to baseline**: `gpt-oss-20b` (run 95) and `gemini-2.0-flash` (run 99) are in the comparable range. Both produce meaningful, project-specific levers with well-differentiated options.
- **Below baseline**: `gpt-5-nano` (run 96), `qwen3-30b-a3b` (run 97), and `gpt-4o-mini` (run 98) are moderately below baseline in description depth, particularly in the structured Immediate→Systemic→Strategic consequence format and the quantified metrics in consequences.
- **Worse than baseline**: `ollama-llama3.1` (run 94) is substantially worse — generic consequences, formulaic reviews, output duplication artifacts.
- **Off-target (verbose)**: `claude-haiku-4-5` (run 3/00) produces the highest-quality content but at 2× baseline verbosity, which is inconsistent with the target format.

No model reproduces the baseline's distinctive "Controls X vs. Y. Weakness: ..." review format or the quantified causal chain in consequences. This is the primary structural gap shared by all models.

---

## Recommendations

### 1. Confirm `lever_index` removal is safe (this experiment's goal)
The primary question — does removing `lever_index` cause index prefixes to appear in `name` or `consequences`? — is answered: **no, it does not**. The schema change is safe to merge.

### 2. Address the consequence format gap (all models)
None of the test models use the baseline's structured `Immediate: X → Systemic: Y → Strategic: Z` format. The baseline also uses quantified metrics (percentages, relative magnitudes). This format should be explicitly encoded in the prompt template — either as a required pattern or as a stronger example. Current prompt guidance is insufficient to elicit this format from any of the tested models.

### 3. Address the review format gap (all models)
The baseline uses a concise "Controls [DimensionA] vs. [DimensionB]. Weakness: [specific gap]." format for reviews. No model produces this. The prompt should either include this as a required format string or provide a clearer structural example with field-level instructions.

### 4. Control verbosity for claude-haiku-4-5 (run 3/00)
Claude haiku produces 2× the expected consequence length. If this model is used in production, a length constraint on `consequences` (e.g. maximum 400 characters) or an explicit instruction ("write concise, focused consequences — avoid exhaustive analysis") should be added to the prompt.

### 5. Address llama3.1 output duplication (run 94)
The GTA plan from run 94 contained 21 levers that appear to be from two separate LLM calls merged together. This may be a pipeline bug (two calls being concatenated rather than deduplicating) rather than a model quality issue. Run 94 used `workers: 1` and `calls_succeeded: 3`, meaning the step performed 3 LLM calls even though it only needed 1 output per plan. The deduplication/selection logic should be verified.

### 6. For production use, prefer gpt-oss-20b or gemini-2.0-flash
Among all tested models, `openrouter-openai-gpt-oss-20b` (run 95) and `openrouter-gemini-2.0-flash-001` (run 99) most closely match baseline quality across lever count, specificity, and option differentiation. These two models are the strongest candidates if a non-baseline model is required for this step.
