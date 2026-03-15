# Insight Codex

## Rankings

- **Best full-success / best current drop-in:** Run `36` (`history/0/36_identify_potential_levers`). It is the only 5/5-success run here with zero option-count violations, zero numeric-metric misses, zero review-template misses, and zero null summaries in raw outputs, but it achieves that by compressing options into short labels (`53.4` avg option chars vs `150.2` in baseline). Representative artifact: `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`.
- **Best richness / easiest to salvage with light normalization:** Run `35` (`history/0/35_identify_potential_levers`). It keeps 5/5 coverage, baseline-like field lengths, and good raw summaries, but it drifts hard on the literal review/consequence format required by the prompt. Representative artifacts: `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`, `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`, `history/0/35_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- **Best partial-success exemplar:** Run `34` (`history/0/34_identify_potential_levers`). When it lands, the successful files are structurally strong and closer to the prompt than baseline on chain/numeric compliance, but `2/5` cases still fail JSON extraction/parsing. Representative artifacts: `history/0/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`, `history/0/34_identify_potential_levers/outputs.jsonl:4`, `history/0/34_identify_potential_levers/outputs.jsonl:5`.
- **Worst operationally:** Run `32` and run `38`. Run `32` succeeds on only `1/5` cases due JSON extraction / EOF failures, while run `38` both times out and emits malformed sovereign-identity output with a blank option and a literal `placeholder` lever. Evidence: `history/0/32_identify_potential_levers/outputs.jsonl:1`, `history/0/32_identify_potential_levers/outputs.jsonl:3`, `history/0/38_identify_potential_levers/outputs.jsonl:4`, `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:65`, `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:71`.

## Negative Things

- **The prompt’s literal contract is still brittle across most runs.** The prompt requires `Immediate: ... → Systemic: ... → Strategic: ...` plus `Controls [Tension A] vs. [Tension B]. Weakness: ...` at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9`, `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:25`, and `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:26`, but run `35` rewrites both forms (`Immediate: ...; Systemic: ...; Strategic: ...` and `Trade-off controls ...`) at `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16` and `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`, run `32` substitutes `versus` for `vs.` at `history/0/32_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:11`, and run `37` drops the chain labels entirely at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.
- **Run `33` is structurally inconsistent even though it completes all 5 cases.** In raw outputs it alternates review halves instead of producing the full required `Controls ... Weakness: ...` string, e.g. `review_lever` is only `Controls Costs vs. Controls Growth.` at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, then only `Weakness: ...` at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:26`; the final file preserves that split at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` and `history/0/33_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`.
- **Run `33` also breaks the exact-3-options rule in a concentrated tail failure.** The parasomnia file ends with nine levers that have only two options, starting at `history/0/33_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:70` and continuing through `history/0/33_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:95`, directly conflicting with `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:5`.
- **Run `36` over-optimizes for short-form schema compliance and underdelivers on option substance.** The prompt says options must be complete strategic approaches and self-contained descriptions at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:20` and `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:41`, but run `36` emits label-like options such as `Government-Subsidized Construction` and `Tokenized Infrastructure Bonds` at `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7` and `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:9`.
- **Run `37` is fast but gives up the hardest part of the prompt: measurable chained consequences.** Its first silo lever replaces the required chain with generic prose (`Choosing a diversified funding strategy will likely enhance...`) at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`; quantitatively that becomes `75/75` consequence-chain violations and `30/75` non-numeric consequences.
- **Run `38` is not just verbose; it is malformed.** The sovereign-identity final output contains a fourth blank option at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:65` followed immediately by a literal `placeholder` lever with empty fields at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:71`. Its raw output shows the same prompt-level breach: the first response already exceeds the mandated five levers and contains `name: "placeholder"` at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:75`, despite the prompt’s `EXACTLY 5 levers per response` rule at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:4`.
- **Operational reliability is still a first-order problem for some models.** Run `32` fails four cases with JSON extraction / EOF errors at `history/0/32_identify_potential_levers/outputs.jsonl:1`, `history/0/32_identify_potential_levers/outputs.jsonl:2`, `history/0/32_identify_potential_levers/outputs.jsonl:3`, and `history/0/32_identify_potential_levers/outputs.jsonl:4`. Run `38` times out on the two longest cases at `history/0/38_identify_potential_levers/outputs.jsonl:4` and `history/0/38_identify_potential_levers/outputs.jsonl:5`.

## Positive Things

- **Run `34` shows the strongest “prompt actually working” sample among successful outputs.** Its successful silo file uses domain-shaped names, literal consequence chains, numeric systemic effects, and complete three-option sets at `history/0/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4` and `history/0/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`.
- **Run `35` is the closest full-success run to baseline richness.** Its average consequence length (`260.5`) and option length (`133.4`) are much closer to baseline (`279.5`, `150.2`) than runs `33`, `34`, or `36`, and unlike run `33` it fills all raw summaries in the required “missing dimension + concrete addition” slot, e.g. `history/0/35_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- **Run `36` demonstrates that the current prompt can achieve clean outer-structure compliance across all five plans.** It keeps `0` option-count violations, `0` missing-weakness reviews, `0` review-opener violations, and `0` non-numeric consequences across `75` final levers.
- **Baseline training data is richer than most history runs, but it is not perfectly strict gold.** Baseline lever 1 in silo is detailed and domain-anchored at `baseline/train/20250321_silo/002-10-potential_levers.json:4`, and baseline raw summaries are populated at `baseline/train/20250321_silo/002-9-potential_levers_raw.json:62`; however baseline still uses the stock weakness phrase at `baseline/train/20250321_silo/002-10-potential_levers.json:22`, and the metrics below show baseline itself has `5` chain violations and `21` non-numeric consequences.

## Comparison

- **Against baseline, the main trade-off in this batch is richness vs. literal compliance.** Baseline options average `150.2` chars and consequences `279.5`, while run `36` shrinks to `53.4` and `208.6`; run `35` is much closer on depth (`133.4`, `260.5`) but drifts harder on literal formatting.
- **Run `36` beats baseline on mechanical discipline but loses strategic texture.** Baseline still has `21` non-numeric consequences and repeated `Strategy` naming, but its options are full approaches; run `36` cleans up numeric/review compliance yet often collapses options into labels (`history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7`).
- **Run `35` is the opposite trade.** It preserves rich options, rich summaries, and complete coverage, but deviates more sharply from the prompt’s literal `vs.` and arrow-chain wording than baseline does (`history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`, `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`).
- **Run `34` is the only run here that plausibly outperforms baseline on both specificity and strictness in its successful subset, but it is not operationally dependable enough to recommend unmodified.** See the strong silo sample at `history/0/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4` versus the parse failures at `history/0/34_identify_potential_levers/outputs.jsonl:4` and `history/0/34_identify_potential_levers/outputs.jsonl:5`.
- **Runs `33` and `37` are both worse than baseline for different reasons.** Run `33` is structurally broken in review/summary handling despite full coverage; run `37` is operationally excellent but abandons the prompt’s most informative consequence format.

## Quantitative Metrics

Computed from `baseline/train/*/002-10-potential_levers.json`, `baseline/train/*/002-9-potential_levers_raw.json`, `history/0/{32..38}_identify_potential_levers/outputs/*/002-10-potential_levers.json`, `history/0/{32..38}_identify_potential_levers/outputs/*/002-9-potential_levers_raw.json`, and each run’s `outputs.jsonl`.

### Operational Metrics

| Run | Model | OK cases | Error cases | Final levers | Avg duration s | Max duration s | Raw null summaries | Bad raw 5-lever responses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | baseline | 5 | 0 | 75 | n/a | n/a | 0 | 0 |
| 32 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 1 | 4 | 15 | 152.59 | 232.04 | 0/3 | 0 |
| 33 | ollama-llama3.1 | 5 | 0 | 75 | 68.45 | 80.32 | 15/15 | 0 |
| 34 | openrouter-openai-gpt-oss-20b | 3 | 2 | 45 | 213.52 | 280.83 | 4/9 | 0 |
| 35 | openai-gpt-5-nano | 5 | 0 | 75 | 199.11 | 221.79 | 0/15 | 0 |
| 36 | openrouter-qwen3-30b-a3b | 5 | 0 | 75 | 126.67 | 172.21 | 0/15 | 0 |
| 37 | openrouter-openai-gpt-4o-mini | 5 | 0 | 75 | 33.09 | 36.12 | 2/15 | 0 |
| 38 | anthropic-claude-haiku-4-5-pinned | 3 | 2 | 47 | 318.05 | 721.45 | 0/9 | 1 |

Interpretation: run `36` is the best full-coverage operational compromise. Run `34` is too fragile to ship as-is. Run `38` is outside a safe latency envelope.

### Uniqueness Counts

| Run | Unique names | Unique consequences | Unique reviews | Unique systemic phrases |
| --- | --- | --- | --- | --- |
| baseline | 52/75 | 75/75 | 75/75 | 75/75 |
| 32 | 15/15 | 15/15 | 15/15 | 15/15 |
| 33 | 75/75 | 66/75 | 52/75 | 54/75 |
| 34 | 44/45 | 45/45 | 45/45 | 45/45 |
| 35 | 75/75 | 75/75 | 69/75 | 37/75 |
| 36 | 75/75 | 75/75 | 74/75 | 60/75 |
| 37 | 74/75 | 75/75 | 75/75 | 45/75 |
| 38 | 47/47 | 47/47 | 47/47 | 30/47 |

Interpretation: run `35` and run `37` look strong on raw uniqueness, but that overstates quality because both also have large formatting drifts. Run `36` gives the best balance of uniqueness and structural regularity among the 5/5 runs.

### Average Field Lengths

| Run | Avg name chars | Avg consequence chars | Avg option chars | Avg review chars | Avg radical option chars |
| --- | --- | --- | --- | --- | --- |
| baseline | 27.7 | 279.5 | 150.2 | 152.3 | 179.3 |
| 32 | 51.9 | 288.6 | 99.6 | 167.5 | 119.9 |
| 33 | 33.3 | 141.7 | 87.8 | 129.5 | 79.2 |
| 34 | 29.3 | 216.1 | 75.3 | 127.7 | 98.4 |
| 35 | 43.7 | 260.5 | 133.4 | 152.8 | 157.7 |
| 36 | 31.6 | 208.6 | 53.4 | 137.3 | 57.1 |
| 37 | 33.3 | 197.7 | 123.9 | 149.5 | 134.3 |
| 38 | 49.6 | 867.0 | 355.2 | 426.9 | 375.7 |

Interpretation: run `35` is the closest full-success run to baseline depth. Run `36` is substantially too terse in options. Run `38` is far beyond the baseline envelope and correlates with timeouts / malformed output.

### Constraint Violations

| Run | Option-count violations | Consequence chain violations | No numeric consequence | Review opener violations | Missing `Weakness:` | Prefixed options | Placeholders |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0 | 5 | 21 | 0 | 0 | 0 | 0 |
| 32 | 0 | 0 | 0 | 15 | 0 | 0 | 0 |
| 33 | 9 | 0 | 59 | 30 | 13 | 0 | 0 |
| 34 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |
| 35 | 0 | 38 | 5 | 73 | 0 | 0 | 0 |
| 36 | 0 | 30 | 0 | 0 | 0 | 0 | 0 |
| 37 | 0 | 75 | 30 | 0 | 0 | 0 | 0 |
| 38 | 2 | 17 | 1 | 1 | 1 | 0 | 0 |

Interpretation: the current prompt does not reliably lock down the exact consequence/review surface form. A validator+retry loop would catch most of this batch’s failures.

### Template Leakage / Structural Anchoring

| Run | `The options fail to consider` | Names ending `Strategy` | Hyphen-`Strategy` names | Radical hype-tech options |
| --- | --- | --- | --- | --- |
| baseline | 8 | 50 | 0 | 24 |
| 32 | 0 | 15 | 1 | 4 |
| 33 | 62 | 47 | 21 | 15 |
| 34 | 14 | 30 | 29 | 34 |
| 35 | 60 | 74 | 40 | 53 |
| 36 | 8 | 75 | 16 | 20 |
| 37 | 22 | 73 | 60 | 11 |
| 38 | 0 | 17 | 14 | 11 |

Interpretation: prompt line `19` (`"[Domain]-[Decision Type] Strategy"`) and line `26` (`"The options fail to consider ..."`) appear to be strong anchoring surfaces. Baseline already contains some of that style, but runs `35`-`37` amplify it far beyond baseline.

## Evidence Notes

- **Prompt contract:** `EXACTLY 5 levers`, exact `3` options, consequence chain wording, review wording, and summary instruction are all explicit at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:4`, `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:5`, `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9`, `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:25`, and `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:27`.
- **Baseline reference quality:** Baseline silo lever 1 is a good content anchor for the intended depth (`baseline/train/20250321_silo/002-10-potential_levers.json:4`), while baseline raw summaries show the downstream schema expects populated summary text (`baseline/train/20250321_silo/002-9-potential_levers_raw.json:62`).
- **Run `33` raw evidence points to a generation problem, not just post-processing.** The alternating half-reviews and null summaries already exist in the raw artifact at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:26`, and `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- **Run `35` shows that the summary instruction is recoverable without changing schema.** Its raw summaries follow the requested `critical missing dimension` / `Add ... to ...` pattern at `history/0/35_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- **Run `38` demonstrates both prompt noncompliance and pipeline fragility.** The raw file already contains `placeholder` content at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:75`, and the final file preserves a blank option plus placeholder lever at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:65` and `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:71`.

## Questions For Later Synthesis

- Should synthesis optimize for **literal prompt compliance** (favoring run `36`) or **semantic richness that could be normalized in code** (favoring run `35` / the successful subset of run `34`)?
- Is the prompt line `19` naming example helpful, or is it over-anchoring models into `X-Y Strategy` names that are less natural than baseline’s naming mix?
- Should the stock weakness phrase at prompt line `26` be diversified, or should synthesis accept it because baseline itself already contains that phrase style in several files?
- Is the `summary` field actually used downstream enough to justify hard validation, or should the pipeline stop requesting it if later steps ignore it?
- Are the run `32` / `34` extraction failures mainly a JSON-repair problem, or are they a symptom that the prompt is too large / too strict for weaker models?

## Reflect

- **H1:** Tighten the review instruction to forbid synonyms and partial outputs: require one exact string pattern, e.g. `Output review_lever as a single field: Controls X vs. Y. Weakness: ... Do not use 'versus', 'Trade-off', or split these across fields.` Evidence: prompt requirement at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:25`; drift in run `32` (`...versus...`) at `history/0/32_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:11`; split reviews in run `33` raw at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15` and `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:26`; `Trade-off` drift in run `35` at `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`.
- **H2:** Add an explicit anti-label rule for options, such as `Each option must be a full sentence with an action verb and at least ~12 words.` Evidence: prompt lines `20` and `41`, plus run `36` label options at `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7` and `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:9`.
- **H3:** Add a hard self-check for consequence formatting: `If any consequence lacks all three labels and at least one number in Systemic, regenerate before answering.` Evidence: prompt lines `9`-`10`; run `37` prose consequences at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`; run `35` semicolon chains at `history/0/35_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`.
- **H4:** Make summary non-optional in the instruction and state that `null` is invalid. Evidence: prompt lines `27`-`29`; run `33` null summaries at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`; contrasting compliant summary in run `35` at `history/0/35_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- **H5:** Reduce example anchoring by replacing the single naming mold and the single weakness stem with more varied examples or abstract prose. Evidence: prompt line `19` and line `26`; leakage table shows `Hyphen-Strategy` names jump from `0` in baseline to `29` in run `34`, `40` in run `35`, and `60` in run `37`, while `The options fail to consider` jumps from `8` in baseline to `62` in run `33` and `60` in run `35`.

## Potential Code Changes

- **C1:** Add strict post-generation validation on raw outputs before promotion to final artifacts: every response must have exactly 5 levers, every final lever must have exactly 3 options, `summary` must be non-null, `review` must match the full `Controls ... vs. ... Weakness: ...` pattern, and `consequences` must contain `Immediate:`, `Systemic:`, `Strategic:`, arrows, and a numeral. Evidence: run `33` raw split reviews / null summaries at `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, `history/0/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`; run `38` raw placeholder at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:75`.
- **C2:** On validation failure, retry the LLM call instead of accepting malformed-but-parseable content. The most common failures in this batch are exactly the sort of surface-form defects that a retry could fix cheaply. Evidence: run `35` and run `37` are fully generated but violate prompt-surface requirements rather than domain reasoning requirements.
- **C3:** Add a bounded JSON-repair / truncation-recovery path for extractable near-misses, then fall back to retry. Evidence: run `32` and run `34` both die on `Could not extract json string` / `Invalid JSON: EOF while parsing a list` at `history/0/32_identify_potential_levers/outputs.jsonl:1`, `history/0/32_identify_potential_levers/outputs.jsonl:3`, and `history/0/34_identify_potential_levers/outputs.jsonl:5`.
- **C4:** Add output-size / latency guardrails before timeouts and malformed spillover become final artifacts. Evidence: run `38` averages `318.05s`, peaks at `721.45s`, and produces massively out-of-envelope field lengths plus placeholder debris (`history/0/38_identify_potential_levers/outputs.jsonl:5`, `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:71`).

## Summary

- The strongest current lever is **not** a single prompt tweak; it is the combination of a smaller prompt cleanup and a strict validator+retry layer.
- If choosing a prompt direction only, run `36` is the safest full-success template, but it needs help to avoid label-like options.
- If choosing a content direction only, run `35` is the most promising full-success richness candidate, but it needs enforcement on the literal review/consequence format.
- Run `34` is the most encouraging evidence that the prompt can work well, but only if the pipeline stops accepting / surfacing parse-fragile generations.
