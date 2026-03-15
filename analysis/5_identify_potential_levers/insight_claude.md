# Insight Claude

## Rankings

- **Tier A:** Run `45` (`anthropic-claude-haiku-4-5-pinned`). Highest output quality in the batch — multi-sentence consequences with percentage ranges, compound descriptive lever names, and fully-elaborated self-contained options (~252 chars each). Only one timeout failure (parasomnia, 432.62s), an improvement over the prior haiku run (runs 38, 31) which timed out on both hong_kong and parasomnia.
- **Tier B:** Run `42` (`openai-gpt-5-nano`). Fully reliable (5/5), proper I→S→S chain with explicit measurable percentages in every consequence, lever names include domain scope ("Underground Silo Governance Strategy"), option text ~142 chars average.
- **Tier B:** Run `43` (`openrouter-qwen3-30b-a3b`). Fully reliable (5/5), proper chain and specific percentages. Penalized one tier from run 42 because the review content is systematically duplicated inside the consequences field, adding length without adding distinct information.
- **Tier C:** Run `44` (`openrouter-openai-gpt-4o-mini`). Fully reliable (5/5) and the fastest multi-capable run (~43.5s avg). Produces a proper I→S→S chain (a positive change from run 37 in the prior batch which had zero chain compliance). Consequence depth is moderate (~270 chars). Lever names consistently use "Silo-" domain prefix.
- **Tier C:** Run `41` (`openrouter-openai-gpt-oss-20b`). 4/5 success rate (parasomnia fails with JSON extraction). Good depth (~350 chars consequences), proper chain and measurable metrics.
- **Tier D:** Run `40` (`ollama-llama3.1`). Fully reliable (5/5) but two systematic violations: (1) consequence effects are single-word token stubs ("Compliance", "Stability") with no measurable outcomes, averaging ~67 chars; (2) the review field alternates between Controls-only and Weakness-only across levers — none contain both components as required.
- **Tier E:** Run `39` (`openrouter-nvidia-nemotron-3-nano-30b-a3b`). 0/5 plans succeed (all fail with `"Could not extract json string from output: ""`). This is the fourth consecutive failure set for this model (runs 24, 25, 32, 39). No viable output for any plan.

---

## Negative Things

- **Run 39 complete failure (all plans).** All five plans fail with the same error at `history/0/39_identify_potential_levers/outputs.jsonl:1–5`: `"Failed to run. Exhausted all LLMs. Failure summary: Attempt 0 with LLMModelFromName(name='openrouter-nvidia-nemotron-3-nano-30b-a3b') failed during 'execute' stage: ValueError('Could not extract json string from output: '')"`. The model produces no parseable JSON. This is the fourth batch in which this model fails (runs 24, 25, 32, 39). The prompt change had no effect.

- **Run 40 single-word consequence effects.** The prompt at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9–10` requires consequences to "Include measurable outcomes" with "a specific, domain-relevant second-order impact with a measurable indicator, such as a % change, capacity shift, or cost delta." Run 40 (llama3.1) produces single-word effect tokens across all 15 levers in every plan, e.g. `"Immediate: Compliance → Systemic: Stability → Strategic: Autocracy"` at `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`. The I→S→S syntactic chain is present but each node is an abstract concept, not a specific effect with a measurable indicator. Average consequence length ~67 chars vs. baseline ~280 chars.

- **Run 40 review format: alternating rather than dual-component.** The prompt validation protocol (`prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:24–28`) requires each review to contain BOTH "Controls [Tension A] vs. [Tension B]" AND "Weakness: The options fail to consider [specific factor]." Run 40 (llama3.1) alternates: odd-positioned levers output Controls-only (e.g. `"Controls Power vs. Empowers People."`) and even-positioned levers output Weakness-only (e.g. `"Weakness: The options fail to consider the impact of AI on human employment."`). Zero levers in run 40 contain both components. Evidence: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` (Controls-only) vs. `…:19` (Weakness-only).

- **Run 43 review content duplicated in consequences.** Qwen3-30b consistently appends the review's trade-off and weakness text to the end of the consequences field, then repeats the same content in the review field. Example from `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`: consequences ends with `"...Controls Cost Efficiency vs. Industrial Resilience. Weakness: The options fail to consider long-term soil degradation from intensive farming."` while the review field reads `"Controls Cost Efficiency vs. Industrial Resilience. Weakness: The options fail to consider long-term soil degradation from intensive farming."` — word-for-word identical. This makes consequence lengths appear higher (~320 chars) than they genuinely are without the duplication.

- **Run 41 JSON extraction failure on parasomnia.** The plan `20260311_parasomnia_research_unit` fails with `"Could not extract json string from output: ''"` at `history/0/41_identify_potential_levers/outputs.jsonl:5`. This is the same model (`openrouter-openai-gpt-oss-20b`) that had JSON-extraction failures in run 34 (two plans) and EOF-truncation failures previously. The parasomnia plan is the only failure here, suggesting this plan's complexity still overwhelms this model's JSON generation reliability.

- **Run 45 API timeout on parasomnia.** The plan `20260311_parasomnia_research_unit` fails with `APITimeoutError` at 432.62 seconds in `history/0/45_identify_potential_levers/outputs.jsonl:5`. While this is an improvement over the prior haiku run (run 38, which timed out on both hong_kong at 426.62s and parasomnia at 721.45s), the single-plan timeout confirms the persistent parasomnia complexity issue for high-verbosity models.

- **strategic_rationale field universally null.** Across all seven runs and all plans, the `strategic_rationale` field in `002-9-potential_levers_raw.json` is null in every response object. Evidence: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:5` (response 1), `:64` (response 2), `:123` (response 3). This field appears in the raw schema but no model populates it.

- **summary field universally null.** Similarly, the `summary` field in every response object across all runs is null. The prompt prescribes a concrete summary format ("Add '[full strategic option]' to [lever]") but no model fills this field. Evidence: same file as above.

- **Run 40 option text is label-style.** Options average ~35 chars, not self-contained strategic descriptions as the prompt requires. Example: `"Dictatorial Rule"`, `"Meritocratic Council"`, `"Decentralized Blockchain-based Governance"` at `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7–9`. Compare to run 42's `"Phase the build with modular prefabrication and centralized control to minimize external exposure and maintain stringent security."` at `history/0/42_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:8`.

---

## Positive Things

- **No option prefix violations across any run.** Scanning all successful runs (40–45), no option starts with `"Option A:"`, `"Choice 1:"`, `"Conservative:"`, `"Moderate:"`, or `"Radical:"`. The "Radical radical" double-word leak from run 38 (haiku) does not recur in run 45. Evidence: manual scan of `history/0/4[0-5]_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

- **Run 44 (gpt-4o-mini) now produces proper I→S→S chain.** In the prior batch, run 37 (gpt-4o-mini, same model) produced zero chain-formatted consequences across all 75 levers. Run 44 produces proper chains with measurable outcomes in every lever, e.g. `"Immediate: Establish strict information dissemination protocols → Systemic: Reduce dissent and misinformation by 30% through controlled messaging → Strategic: Create a cohesive community identity that aligns with the silo's objectives..."` at `history/0/44_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`. This is a notable improvement, though it may be non-deterministic (same model, same prompt).

- **Run 45 reduces haiku timeout failures from 2/5 to 1/5.** Prior haiku run (run 38) timed out on both `hong_kong_game` (426.62s) and `parasomnia_research_unit` (721.45s). Run 45 completes `hong_kong_game` in 151.35s and only times out on `parasomnia_research_unit` (432.62s). Evidence: `history/0/45_identify_potential_levers/outputs.jsonl`.

- **Lever count is exactly 15 for all successful runs and all plans.** No run in this batch produces 16 levers for any plan. In the prior batch, runs 33, 35, 37, and 38 each produced 16 levers for gta_game. This batch (40–45) shows no such overflow. Evidence: `lever_id` counts in `002-10-potential_levers.json` for gta_game across runs 40–45 all return 15.

- **Lever name uniqueness is 15/15 in all successful runs.** No repeated lever names within any plan output. The baseline silo has 5 duplicate names across its 15 levers (3× "Technological Adaptation Strategy", 2× "Resource Allocation Strategy"). All six successful run models avoid this. Evidence: `history/0/40–45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all names are distinct in each file.

- **Run 45 (haiku) lever names follow the domain-specific [Domain]-[Decision] compound convention.** Names like `"Governance-Transparency Trade-off Strategy"`, `"Population-Composition Selection Strategy"`, `"External-Narrative Information-Control Architecture"`, `"Ecosystem-Carrying-Capacity Management Model"` at `history/0/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` directly implement the prompt's `"[Domain]-[Decision Type] Strategy"` instruction with the richest semantic precision in this batch.

- **Run 42 (gpt-5-nano) provides the most consistently structured Trade-off format in reviews.** Every review uses the pattern `"Trade-off: Controls [A] vs [B]. Weakness: The options fail to consider [factor]."` with specific and non-generic weakness identification. Evidence: `history/0/42_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` (`"Trade-off: Controls speed vs security. Weakness: The options fail to consider long-term governance legitimacy and external regulatory compliance."`).

---

## Comparison

### Comparison to baseline training data

The baseline (`baseline/train/20250321_silo/002-10-potential_levers.json`) has 15 levers generated by an earlier model run (prompt_0) with consequences averaging ~280 chars and options ~150 chars. It contains 5 duplicate lever names (confirmed at `baseline/train/20250321_silo/002-10-potential_levers.json`: "Technological Adaptation Strategy" at positions 3, 9, 14; "Resource Allocation Strategy" at positions 1, 11; "External Relations Protocol" at positions 10, 15). Reviews in the baseline are mostly well-formed with both Controls and Weakness components.

Run 45 (haiku) substantially exceeds baseline quality: ~700 chars avg consequences, ~252 chars avg options, zero name duplication, richly domain-specific lever names that do not exist in baseline. It also introduces lever concepts absent from baseline such as population genetics policy, succession architecture, and existential contingency planning — all relevant to the silo domain.

Run 42 (gpt-5-nano) matches or slightly exceeds baseline in consequence depth (~390 chars vs ~280) and meets baseline in option length (~142 chars vs ~150). It is the closest match to the baseline quality profile among fully reliable runs.

Run 44 (gpt-4o-mini) is roughly comparable to baseline in option length (~117 chars) but falls slightly below on consequence depth (~270 chars vs ~280). Its domain framing ("Silo-" prefix) is more consistent than the baseline.

Run 40 (llama3.1) is well below baseline in both consequence depth (~67 chars vs ~280) and option length (~35 chars vs ~150). Its coverage of the domain is also narrower (governance, resources, surveillance, economics, information control) vs. baseline's wider spread.

The two hardest plans (hong_kong and parasomnia) continue to cause failures: run 41 (gpt-oss-20b) and run 45 (haiku) each fail one of these. This matches the prior-batch pattern where runs 34 and 38 also failed on these same plans.

---

## Quantitative Metrics

### Operational / Structural

| Run | Model | Plans OK | Plans Failed | Avg sec (ok) | Failure mode |
|-----|-------|----------|--------------|--------------|--------------|
| 39 | nvidia-nemotron-3-nano-30b-a3b | 0/5 | 5 | N/A | JSON extraction (all 5) |
| 40 | ollama-llama3.1 | 5/5 | 0 | ~77.9 | — |
| 41 | openrouter-openai-gpt-oss-20b | 4/5 | 1 | ~106.8 | JSON extraction (parasomnia) |
| 42 | openai-gpt-5-nano | 5/5 | 0 | ~197.3 | — |
| 43 | openrouter-qwen3-30b-a3b | 5/5 | 0 | ~155.1 | — |
| 44 | openrouter-openai-gpt-4o-mini | 5/5 | 0 | ~43.5 | — |
| 45 | anthropic-claude-haiku-4-5-pinned | 4/5 | 1 | ~147.8 | API timeout (parasomnia 432.62s) |

Sources: `history/0/[39–45]_identify_potential_levers/outputs.jsonl`

### Lever Count per Plan (002-10-potential_levers.json)

| Run | silo | gta | sovereign | hong_kong | parasomnia |
|-----|------|-----|-----------|-----------|------------|
| baseline | 15 | 15 | — | — | — |
| 40 | 15 | 15 | 15 | 15 | 15 |
| 41 | 15 | 15 | 15 | 15 | — (failed) |
| 42 | 15 | 15 | 15 | 15 | 15 |
| 43 | 15 | 15 | 15 | 15 | 15 |
| 44 | 15 | 15 | 15 | 15 | 15 |
| 45 | 15 | 15 | 15 | 15 | — (failed) |

No 16-lever overflow this batch. Prior batch (runs 33, 35, 37, 38) showed gta_game overflows. The gta overflow appears non-deterministic.

Sources: `lever_id` occurrence counts in `002-10-potential_levers.json` and `002-9-potential_levers_raw.json` per run.

### Approximate Average Field Lengths — 20250321_silo plan

| Run | Avg consequence chars | Avg option chars | I→S→S chain | Measurable outcome |
|-----|----------------------|------------------|-------------|--------------------|
| baseline | ~280 | ~150 | Present | Partial (~50%) |
| 40 (llama) | ~67 | ~35 | Present (thin) | **Absent** (0/15) |
| 41 (gpt-oss) | ~350 | ~78 | Present | Present |
| 42 (gpt-5-nano) | ~390 | ~142 | Present | Present |
| 43 (qwen3) | ~320 | ~72 | Present (but includes review text) | Present (inflated) |
| 44 (gpt-4o-mini) | ~270 | ~117 | Present | Present |
| 45 (haiku) | ~700 | ~252 | Present | Present |

Note: Run 43's consequence averages are inflated by ~80 chars of duplicated review content appended to each consequence.

### Constraint Violations — silo plan (15 levers per run)

| Run | No measurable outcome | Review incomplete (not both Controls+Weakness) | strategic_rationale=null | summary=null |
|-----|----------------------|------------------------------------------------|--------------------------|--------------|
| baseline | ~7/15 | ~2/15 | n/a | n/a |
| 40 | **15/15** | **15/15** (alternating pattern) | 15/15 | 15/15 |
| 41 | 0/15 | 0/15 | 15/15 | 15/15 |
| 42 | 0/15 | 0/15 | 15/15 | 15/15 |
| 43 | 0/15 | 0/15 | 15/15 | 15/15 |
| 44 | 0/15 | 0/15 | 15/15 | 15/15 |
| 45 | 0/15 | 0/15 | 15/15 | 15/15 |

Sources: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (run 40 violations); `history/0/[41-45]_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### Template Leakage and Prefix Violations

| Run | Option prefix leak | Double-word prefix | Placeholder text | Review-in-consequences |
|-----|--------------------|--------------------|------------------|------------------------|
| 40 | 0 | 0 | 0 | 0 |
| 41 | 0 | 0 | 0 | 0 |
| 42 | 0 | 0 | 0 | 0 |
| 43 | 0 | 0 | 0 | **15/15** |
| 44 | 0 | 0 | 0 | 0 |
| 45 | 0 | 0 | 0 | 0 |

---

## Evidence Notes

- Run 39 exact error for all plans: `"LLM chat interaction failed [...]: Failed to run. Exhausted all LLMs. Failure summary: - Attempt 0 with LLMModelFromName(name='openrouter-nvidia-nemotron-3-nano-30b-a3b') failed during 'execute' stage: ValueError('Could not extract json string from output: '')"` at `history/0/39_identify_potential_levers/outputs.jsonl:1–5`.

- Run 40 (llama3.1) consequence example — lever "Silo Governance Strategy": `"Immediate: Compliance → Systemic: Stability → Strategic: Autocracy"` at `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`. Three single-word nodes; no percentage, capacity shift, or cost delta.

- Run 40 review alternation pattern for silo, first six levers: positions 0, 2, 4 → `"Controls X vs. Y."` format (no Weakness); positions 1, 3, 5 → `"Weakness: The options fail to consider..."` format (no Controls). Source: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11, 19, 27, 35, 43, 51`.

- Run 42 (gpt-5-nano) activity overview: `history/0/42_identify_potential_levers/outputs/20250321_silo/activity_overview.json` shows 10 LLM calls total (not 9), with `gpt-5-nano-2025-08-07` model used. This suggests 3 lever-generation calls + additional calls (deduplication, review, or pipeline steps).

- Run 43 (qwen3) consequence duplication example: consequences field ends with `"...Controls Cost Efficiency vs. Industrial Resilience. Weakness: The options fail to consider long-term soil degradation from intensive farming."` and the review field reads `"Controls Cost Efficiency vs. Industrial Resilience. Weakness: The options fail to consider long-term soil degradation from intensive farming."` at `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5,11`.

- Run 44 (gpt-4o-mini) chain compliance example: `"Immediate: Establish strict information dissemination protocols → Systemic: Reduce dissent and misinformation by 30% through controlled messaging → Strategic: Create a cohesive community identity..."` at `history/0/44_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`. This contrasts with run 37 (prior batch, same model) where all consequences were plain prose.

- Run 45 (haiku) longest consequence example: `"Immediate: Choosing between centralized authoritarian control versus distributed compartmentalized governance directly determines decision-making speed and internal coordination efficiency. → Systemic: A fully opaque command structure reduces administrative overhead by 30–40% but increases defection risk and external scrutiny pressure by up to 60%... → Strategic: The governance model determines whether the silo becomes a self-perpetuating closed system or evolves into a sustainable hybrid model..."` (~910 chars) at `history/0/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.

- Run 45 timeout: `history/0/45_identify_potential_levers/outputs.jsonl:5` — `"LLM chat interaction failed [2fc11c4936ea]: Failed to run. Exhausted all LLMs. Failure summary: - Attempt 0 with LLMModelFromName(name='anthropic-claude-haiku-4-5-pinned') failed during 'execute' stage: APITimeoutError('Request timed out or interrupted...')"` at 432.62s.

- Baseline silo duplicate names confirmed at `baseline/train/20250321_silo/002-10-potential_levers.json`: "Technological Adaptation Strategy" at list indices 2, 8, 13; "Resource Allocation Strategy" at indices 0, 10; "External Relations Protocol" at indices 9, 14.

---

## Questions For Later Synthesis

1. **Is run 44 gpt-4o-mini's chain compliance genuinely improved or is it non-deterministic?** Run 37 (prior batch, same model) had 0/75 chain-formatted consequences; run 44 produces proper chains in every lever. Are these from different model snapshots (version pinning on openrouter?), or is this within-model variance? Confirming stability via re-test would determine whether gpt-4o-mini can be reliably used for this step.

2. **Should the `strategic_rationale` and `summary` fields be removed from the schema, or is there a way to prompt for them?** Both fields are null in 100% of responses across all 7 runs. If these fields provide no value, removing them reduces schema complexity. If they are theoretically valuable, a more explicit prompt instruction with examples may be needed.

3. **What causes run 43 (qwen3-30b) to append review content to consequences?** This seems like the model decided to put all validation content in the consequences field. Is this a thinking-mode artifact (qwen3 has extended reasoning), a prompt ambiguity, or consistent qwen3 behavior? Checking whether this also occurred in run 36 (prior qwen3 run, analysis/4) would help distinguish model-specific vs. context-specific.

4. **Does `parasomnia_research_unit` consistently overwhelm the two weakest JSON-generation models (nemotron, gpt-oss-20b) and the highest-verbosity model (haiku)?** If parasomnia is structurally different (e.g., longer or more complex input), a code-side pre-check on plan input length could predict failures before they waste time.

5. **Is the 16-lever gta overflow from prior batch fixed, or did it simply not trigger this time?** Prior batch (runs 33, 35, 37, 38) showed 16-lever gta outputs. This batch shows 15/15 for all runs. Since the prompt and model are unchanged, this is likely non-deterministic. Should C2 (enforce 5-lever-per-call limit) be implemented to make this deterministic?

6. **Could the run 40 (llama3.1) review alternation pattern be a schema alignment issue in the raw JSON structure?** The raw file (`002-9-potential_levers_raw.json`) shows responses alternating between two review patterns. If the model sees the two sub-requirements (Controls; Weakness) as separate items to fulfill alternately rather than combining them, a prompt change could fix this.

---

## Reflect

- The main quality gap in this batch is the divide between heavy models that produce deep, specific content (haiku, gpt-5-nano) and lighter models that satisfy syntactic format but not semantic depth (llama3.1). Run 40 technically passes the I→S→S chain check but its single-word nodes fail the measurable-outcome requirement entirely.
- The qwen3 review-in-consequences duplication is a structural artifact not previously seen in this step. It suggests the model's interpretation of "Validation Protocols" may be to include them inline in every field rather than exclusively in `review_lever`.
- The universal null for `strategic_rationale` and `summary` suggests either (a) the schema expects these to be filled by a later pipeline step, not the LLM, or (b) the prompt does not sufficiently direct models to populate them. Given zero models fill these fields, the prompting for them is ineffective.
- Run 45 haiku's improvement from 3/5 → 4/5 is real progress. If the parasomnia plan is exceptionally hard for high-verbosity models, a plan-specific `max_tokens` cap at the code level could prevent the final timeout without altering prompt behavior.
- The gpt-4o-mini chain improvement (run 37 → run 44) is encouraging but unverified as stable. The prior analysis tagged this as a likely candidate for an H1 chain-example fix; if the improvement is non-deterministic, that fix is still needed.

---

## Potential Code Changes

- **C1 (carried from prior analysis): Validate consequence chain format post-merge.** Check each consequence for the presence of `"Immediate:"`, `"Systemic:"`, and `"Strategic:"` tokens. Flag or retry levers that lack the chain. Evidence: run 40 has formally valid structure but trivially thin content — this check would not help for run 40 (it passes syntactically), but it guards against regression to run 37-style collapses. Expected effect: catch consequence-chain regressions without re-running the whole step.

- **C2 (carried from prior analysis): Enforce strict lever count = 5 per LLM call in raw validation.** The 16-lever gta overflow did not appear in this batch but it is known to appear non-deterministically. Rejecting any raw call with ≠ 5 levers and retrying would stabilize the merged count at exactly 15. Expected effect: eliminate lever count variance across runs.

- **C3 (carried from prior analysis): Add per-call `max_tokens` limit for haiku.** Run 45 generates ~700 chars per consequence for silo (extrapolated: parasomnia likely produces much longer output). A 3000–4000 token cap per call would prevent the haiku timeout while preserving its quality for all but the most extreme plans. Evidence: `history/0/45_identify_potential_levers/outputs.jsonl:5` (parasomnia 432s timeout).

- **C6 (new): Validate review field contains both "Controls" and "Weakness" substrings.** Run 40 produces 15/15 reviews that are missing one of the two required components. A post-merge check for both `"Controls "` and `"Weakness:"` in the review field would detect this pattern and could flag or retry the specific lever. Evidence: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11, 19, 27, 35…`

- **C7 (new): Detect review-in-consequences cross-contamination.** Run 43 appends `"Controls [A] vs. [B]. Weakness: ..."` text to the end of every consequence. A check for consequence fields ending with a pattern like `/Controls .+ vs\..*Weakness:/` would detect this contamination and could strip the duplicate section from consequences before the file is stored. Evidence: `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.

- **C8 (new): Add a warning or skip condition for the nemotron-3-nano model.** This model has failed in four consecutive batch runs (runs 24, 25, 32, 39), always with the same JSON extraction error. Continuing to include it in test batches wastes execution time (avg ~108s per failed plan = ~540s per run). An early-exit or model-skip mechanism for known-failing models would save ~9 minutes per batch. Evidence: `history/0/39_identify_potential_levers/meta.json` (model: `openrouter-nvidia-nemotron-3-nano-30b-a3b`).

---

## Prompt Hypotheses

- **H1 (carried from prior analysis): Add a structural consequence chain example with measurable outcome.** The prompt specifies the chain format at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9–10` but provides no illustrative example. Run 40 (llama3.1) satisfies the syntactic pattern but produces single-word nodes. Adding a minimal example like `"Immediate: [specific action or trigger] → Systemic: [domain-relevant outcome, e.g. 15% reduction in X or +20% increase in Y over 2 years] → Strategic: [long-term implication for the project's core trade-off]"` could anchor what "measurable outcome" means for smaller models. Expected effect: push llama3.1-class models to include metric placeholders rather than abstract tokens.

- **H2 (carried from prior analysis): Add a per-consequence length advisory targeting ~200–350 chars.** Run 40 averages ~67 chars (far below target); run 45 averages ~700 chars (causes timeouts). Neither is optimal. An explicit `"Each consequence should be approximately 200–350 characters"` instruction would bound both extremes. Expected effect: reduce haiku timeouts by discouraging multi-sentence elaboration while encouraging llama3.1 to expand beyond single-word tokens.

- **H3 (new): Clarify that review content must NOT appear in the consequences field.** Run 43 (qwen3) duplicates the review in every consequence. Adding a prohibition like `"The consequences field must NOT include trade-off summaries or weakness statements — those belong exclusively in review_lever."` could prevent this. Evidence: `history/0/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`. Expected effect: eliminate qwen3-class review-in-consequences contamination, producing cleaner separation of analytical content.

- **H4 (new): Make the dual-component review requirement more explicit.** The current instruction `"State the trade-off explicitly: 'Controls [Tension A] vs. [Tension B].' Identify a specific weakness: 'Weakness: The options fail to consider [specific factor].'"` uses two separate bullet points. Run 40 treats these as two separate options to choose between rather than combine. Adding `"Both components are required in every review_lever response — the trade-off sentence first, then the weakness sentence."` could prevent the alternation pattern. Evidence: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (alternating Controls-only / Weakness-only pattern). Expected effect: force llama3.1 to combine both in each review.

- **H5 (new): Suppress `strategic_rationale` and `summary` fields from the schema or add explicit instructions to fill them.** Both fields are null in 100% of responses across all runs, including high-quality models like haiku and gpt-5-nano. If the fields are meant to be populated by the LLM, an explicit prompt example or instruction is needed. If they are pipeline-filled later, documenting this in the prompt schema would clarify intent. Expected effect: either populate the fields (if added to prompt) or remove dead weight from the schema.

---

## Summary

- **Reliability holds for most models.** Five of seven runs achieve ≥ 4/5 success rate. Two persistent failure modes continue: nemotron (0/5, now across 4 batch-runs) and the parasomnia plan causing failures in gpt-oss-20b and haiku.
- **Quality split sharpens toward two clusters.** Run 45 (haiku) and run 42 (gpt-5-nano) deliver output well above baseline depth. Run 40 (llama3.1) is structurally valid but semantically thin — its consequences pass the I→S→S check but contain no measurable outcomes and its reviews violate the dual-component requirement.
- **New structural issue in run 43.** Qwen3-30b appends review content inside every consequence, creating redundant fields. This is a new failure mode not observed in prior batches.
- **gpt-4o-mini chain compliance has improved but may be non-deterministic.** Run 44 shows proper chains (contrast with run 37's complete chain failure). This should be verified by re-running before relying on it.
- **Three high-priority actions emerge:** (1) C8 — skip or warn on nemotron-3-nano model (persistent four-run failure); (2) H4 — require both review components explicitly in one combined instruction to fix llama3.1 alternation; (3) H1 — add a structural consequence example with measurable metric to anchor llama3.1-class models above single-word nodes.
- **Best candidate for next iteration:** Run 42 (gpt-5-nano) as operational baseline, with H1 + H4 added to prompt to address the llama3.1 pattern, and C3 (max_tokens cap) implemented to prevent haiku timeouts on parasomnia.
