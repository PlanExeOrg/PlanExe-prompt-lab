# Codex Insight: identify_potential_levers (analysis 7)

Scope examined:
- Prompt: `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`
- History runs: `history/0/53_identify_potential_levers` through `history/0/59_identify_potential_levers`
- Baseline reference set: `baseline/train/*/002-9-potential_levers_raw.json` and `baseline/train/*/002-10-potential_levers.json`

I treated the baseline as a comparison set, not as a perfect gold standard, because the new prompt is stricter than many baseline artifacts.

## Negative Things

- **Run 53 is operationally unusable.** All 5 plans failed with `Could not extract json string from output` in `history/0/53_identify_potential_levers/outputs.jsonl`.
- **Run 54 is structurally valid but too generic.** It has the worst measurable-consequence score among successful full runs (59/75 missing), the most repeated stock options (11), and repeated full option strings across plans (only 209 unique options out of 225).
- **Run 55 has promising content but poor reliability.** Two plans failed JSON validation (`trailing characters at line 11 column 4`) in `history/0/55_identify_potential_levers/outputs.jsonl`, and the successful plans often miss the exact arrow-chain format even when the substance is good.
- **Run 56 is the strongest content candidate, but still drifts from the exact format.** It keeps measurable outcomes almost everywhere, yet 16/75 consequences miss the exact `Immediate → Systemic → Strategic` separator pattern and 25/75 radical options do not clearly introduce emerging tech or a novel business model.
- **Run 57 has a severe field-boundary failure.** In all 60 saved levers, `consequences` also contain review text (`Controls ... Weakness:`), e.g. `history/0/57_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`. That is a schema-level content leak even though the JSON is valid.
- **Run 58 is the best balance overall, but still too generic in some names/options.** It reuses cross-domain names such as `Funding-Resource Allocation Strategy` and `Technology-Integration Strategy` in both GTA and parasomnia outputs, and some “radical” options are not actually radical.
- **Run 59 over-optimizes for richness and ignores format discipline.** It is far longer than baseline, has 30/75 chain violations, 15/75 review-template misses, 1 placeholder leak, and 1 direct generic-option violation.
- **The prompt’s “radical option” instruction is still weakly enforced across almost every run.** Even baseline misses my heuristic on 52/75 radical options; runs 54 and 58 are especially weak here.

## Positive Things

- **The prompt does improve raw-call diversity.** Baseline raw outputs average only 10.6 unique lever names per 15 raw levers, while runs 54–59 average 15.0 unique raw names whenever a raw file exists.
- **Exactly-5-per-response is no longer the main problem.** Every available raw response in baseline and runs 54–59 contains exactly 5 levers in `002-9-potential_levers_raw.json`.
- **Runs 56 and 58 are the best prompt-level candidates.** Both complete all 5 plans, keep high uniqueness, and usually include concrete metrics and explicit weaknesses.
- **Run 56 shows the strongest consequence depth.** Its average `consequences` length is 412.3 chars with only 1 measurable-outcome miss.
- **Run 58 shows the best operational efficiency among successful full runs.** It completed all 5 plans with the lowest average duration (49.9s) and no parse failures.
- **Run 59 demonstrates that the prompt can elicit highly specific, domain-aware reasoning.** The problem is not lack of intelligence; it is lack of output-shape discipline.
- **Baseline remains useful as a quality anchor for domain specificity.** Even where it violates the new stricter prompt, it often gives sharper, more domain-grounded option sets than run 54 or the generic names in run 58.

## Comparison

Relative to baseline, the current prompt mostly succeeds at **increasing exact uniqueness** but not at **consistently enforcing the requested format**.

- **Baseline vs. new runs on diversity:** baseline final outputs have only 52 unique lever names across 75 levers because the merged files still contain repeated names such as `Resource Allocation Strategy` and `Technological Adaptation Strategy` in `baseline/train/20250321_silo/002-10-potential_levers.json`. Runs 54, 56, 57, and 59 reach 75/75 unique names; run 58 is close at 73/75.
- **Baseline vs. new runs on domain specificity:** baseline often uses stronger domain-specific option content. Example: `baseline/train/20250321_silo/002-10-potential_levers.json` includes a third option with “AI-driven resource allocation ... incorporating blockchain for transparency,” while run 54’s matching silo file falls back to a generic consequence (`Reduced waste and energy consumption`) and a review with no weakness (`Controls Resource Optimization vs. Human Labor Costs.`).
- **Best overall quality/compliance trade-off:** run 58 is the best all-around candidate because it combines full completion, fast runtime, 225/225 unique options, 74/75 measurable consequences, and full review-template compliance. Its main weakness is genericity, not failure.
- **Best depth candidate:** run 56 is strongest if the goal is richer strategic content. It has much better depth than run 58, but its formatting drift suggests the prompt is underspecified on exact separators and on what counts as “radical.”
- **Most instructive failure mode:** run 57 shows that a model can satisfy topical richness while silently corrupting field boundaries. This is a strong argument for post-generation validation rather than prompt-only fixes.
- **Least useful successful run:** run 54 is reliable but too templated. It looks like the model learned the outer shape of the prompt without internalizing the measurable/trade-off requirements.
- **Run 59 is an overcorrection.** It solves shallowness by writing essay-length fields, but that breaks the requested terse templates and even reintroduces a placeholder (`[specific pathway]`) in `history/0/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`.

My practical ranking for next-round leverage is: **58 first, 56 second, 55/57 as conditional signals, 54 and 59 mainly as warning cases, 53 as a parser/reliability failure case**.

## Quantitative Metrics

### Operational reliability

| Run | Model | OK plans | Error plans | Avg sec | Max sec | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| baseline | baseline reference | 5 | 0 | n/a | n/a | reference only |
| 53 | `openrouter-nvidia-nemotron-3-nano-30b-a3b` | 0 | 5 | 109.7 | 125.1 | extraction failure on every plan |
| 54 | `ollama-llama3.1` | 5 | 0 | 78.9 | 100.9 | reliable but shallow |
| 55 | `openrouter-openai-gpt-oss-20b` | 3 | 2 | 76.1 | 150.4 | JSON trailing-character failures |
| 56 | `openai-gpt-5-nano` | 5 | 0 | 224.8 | 279.9 | strongest depth, slow |
| 57 | `openrouter-qwen3-30b-a3b` | 4 | 1 | 84.3 | 134.8 | one parse failure |
| 58 | `openrouter-openai-gpt-4o-mini` | 5 | 0 | 49.9 | 54.7 | fastest successful full run |
| 59 | `anthropic-claude-haiku-4-5-pinned` | 5 | 0 | 213.9 | 470.4 | verbose and slow tail |

### Final-output quality metrics (`002-10-potential_levers.json`)

| Run | Total levers | Unique names | Unique options | Avg consequence chars | Avg review chars | Avg option chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 75 | 52 (0.693) | 225 (1.000) | 279.5 | 152.3 | 150.2 |
| 53 | 0 | 0 | 0 | n/a | n/a | n/a |
| 54 | 75 | 75 (1.000) | 209 (0.929) | 165.1 | 153.5 | 87.7 |
| 55 | 45 | 45 (1.000) | 134 (0.993) | 293.3 | 121.0 | 77.3 |
| 56 | 75 | 75 (1.000) | 217 (0.964) | 412.3 | 148.5 | 125.6 |
| 57 | 60 | 60 (1.000) | 179 (0.994) | 380.0 | 136.2 | 70.6 |
| 58 | 75 | 73 (0.973) | 225 (1.000) | 270.6 | 156.5 | 120.5 |
| 59 | 75 | 75 (1.000) | 225 (1.000) | 1127.1 | 447.1 | 374.3 |

Interpretation:
- Exact uniqueness is **not enough**. Run 54 gets perfect name uniqueness but still feels templated.
- Run 59’s uniqueness is perfect because it writes very long bespoke text, but that same behavior causes contract drift.
- Run 58 is closest to baseline length while preserving high compliance.

### Constraint-violation counts

These counts are heuristic but directly tied to the prompt contract.

| Run | Measurable consequence missing | Review trade-off missing | Review weakness missing | Chain format missing | Radical option missing emerging-tech/business-model cue |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 21 | 0 | 0 | 5 | 52 |
| 53 | 0 | 0 | 0 | 0 | 0 |
| 54 | 59 | 9 | 6 | 0 | 63 |
| 55 | 0 | 0 | 0 | 15 | 16 |
| 56 | 1 | 1 | 0 | 16 | 25 |
| 57 | 0 | 0 | 0 | 0 | 36 |
| 58 | 1 | 0 | 0 | 0 | 52 |
| 59 | 2 | 15 | 0 | 30 | 31 |

Interpretation:
- Run 54 fails the core improvement target: it often uses the right shell without the required measurable middle effect.
- Runs 55 and 56 often contain the right content but miss the exact delimiter format.
- Run 58 is strong on strict review/consequence format but weak on the “radical option” clause.
- Run 59 is where verbosity starts to compete with compliance.

### Template leakage / duplication counts

| Run | Placeholder items | Generic option items | Stock option items | Repeated option occurrences | Consequences containing review text |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0 | 0 | 0 | 0 | 0 |
| 54 | 0 | 0 | 11 | 16 | 0 |
| 55 | 0 | 0 | 0 | 1 | 0 |
| 56 | 0 | 0 | 0 | 8 | 0 |
| 57 | 0 | 0 | 0 | 1 | 60 |
| 58 | 0 | 0 | 0 | 0 | 0 |
| 59 | 1 | 1 | 0 | 0 | 0 |

Interpretation:
- Run 54 is the clearest template-leak run.
- Run 57 is not repetitive in the usual sense, but it has a more serious leakage problem: review text is copied into the wrong field in every saved item.
- Run 59 is the only run here with direct placeholder and direct prohibited-generic leakage.

### Raw-call duplication (`002-9-potential_levers_raw.json`)

| Run | Avg responses/file | Avg raw levers/file | Avg unique raw names | Avg duplicate raw-name occurrences | Avg unique raw options | Avg duplicate raw-option occurrences |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3.0 | 15.0 | 10.6 | 4.4 | 45.0 | 0.0 |
| 54 | 3.0 | 15.0 | 15.0 | 0.0 | 41.8 | 3.2 |
| 55 | 3.0 | 15.0 | 15.0 | 0.0 | 44.7 | 0.3 |
| 56 | 3.0 | 15.0 | 15.0 | 0.0 | 43.4 | 1.6 |
| 57 | 3.0 | 15.0 | 15.0 | 0.0 | 44.8 | 0.2 |
| 58 | 3.0 | 15.0 | 15.0 | 0.0 | 45.0 | 0.0 |
| 59 | 3.0 | 15.0 | 15.0 | 0.0 | 45.0 | 0.0 |

Interpretation:
- This is the prompt’s biggest genuine win: it removes baseline-style within-file lever-name duplication at raw-generation time.
- Run 58 is especially clean here: full raw diversity without repeated raw options.

## Evidence Notes

- **Prompt requirements are explicit and strict.** The prompt requires measurable systemic effects, explicit `Controls A vs. B` reviews, one weakness, and radical options with emerging tech/business models in `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`.
- **Baseline shows strong domain anchoring but imperfect deduplication.** In `baseline/train/20250321_silo/002-10-potential_levers.json`, `Resource Allocation Strategy` appears multiple times, but one instance is very strong: `15% increase in black market activity`, a domain-relevant weakness, and a radical option with blockchain transparency.
- **Run 54’s shallow/generic pattern is visible immediately.** In `history/0/54_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `Silo-Resource Allocation Strategy` has `Immediate: Efficient resource distribution → Systemic: Reduced waste and energy consumption → Strategic: Enhanced long-term sustainability` and review text `Controls Resource Optimization vs. Human Labor Costs.` with no weakness. The same file also uses the stock option `Create a hybrid system combining both deterministic and probabilistic approaches`.
- **Run 55 failures are parser-level, not subtle content misses.** `history/0/55_identify_potential_levers/outputs.jsonl` records `Invalid JSON: trailing characters at line 11 column 4` for sovereign identity and parasomnia.
- **Run 56 has strong substance but imperfect formatting.** In `history/0/56_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`, `Resilience-by-Design Contracting Strategy` includes a measurable delta (`25 percentage points`, `+2.0M DKK`) but uses semicolons rather than the exact `Immediate: ... → Systemic: ... → Strategic: ...` chain. In `history/0/56_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `External Engagement and Exit-Scenario Strategy` ends with `Create open-innovation partnerships...`, which is not clearly an emerging-tech/business-model radical move.
- **Run 57 has a clear field-leak bug.** In `history/0/57_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, `consequences` ends with `Controls clinical safety vs. behavioral authenticity. Weakness: ...`, duplicating the review content into the wrong field.
- **Run 58 is cleanest structurally but can go generic across domains.** `Funding-Resource Allocation Strategy` appears in both `history/0/58_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` and `history/0/58_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`; the same is true for `Technology-Integration Strategy`. In the silo file, the radical option for `Silo-Information Control Strategy` is just `Implement a transparent information-sharing platform...`, which is not notably radical.
- **Run 59 violates explicit prohibitions despite high intelligence.** In `history/0/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`, one option still contains `[specific pathway]`. In `history/0/59_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, one option begins `Optimize heavily for PS5/Series X hardware...`, directly conflicting with the prompt’s ban on generic labels like `Optimize X`. In `history/0/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, the review starts `Controls the tension between ...` instead of the requested `Controls A vs. B.` form.
- **Run 53 is a pure extraction failure case.** `history/0/53_identify_potential_levers/outputs.jsonl` shows the same `Could not extract json string from output` error for all five plans.

## Questions For Later Synthesis

- Is the project optimizing for **best prompt across many models**, or for **best prompt for the strongest model family**? That matters because run 56 and run 58 suggest different prompt priorities.
- Should the synthesis treat the “radical option must include emerging tech/business model” clause as a hard requirement, or is it too strict for some domains? Baseline and run 58 both struggle here.
- Should “exact format compliance” outrank “strategic richness” when they trade off? Run 56 vs. run 58 is the main decision point.
- Does the team want a prompt that is robust to weaker local models like `ollama-llama3.1`, or should weaker-model performance be discounted if stronger hosted models comply better?
- Is the review-field exact wording (`Controls A vs. B.`) intentionally rigid, or would semantically equivalent forms be acceptable if code-level normalization exists?

## Reflect

A key takeaway is that this prompt version fixed the **old diversity problem** more effectively than it fixed the **new formatting/compliance problem**. The raw outputs are much less duplicative than baseline. That is real progress. But the next leverage point is not “ask for even more creativity.” It is “narrow the acceptable shape and add enforcement.”

The runs also split into two families:
- **54 / 58**: cleaner shape, lighter reasoning
- **56 / 59**: richer reasoning, more drift

That suggests the prompt is currently under-specified on how to balance depth against format. The best next iteration probably borrows run 56’s richness and run 58’s discipline rather than pushing further in either extreme.

## Prompt Hypotheses

- **H1. Add one short gold example and one short anti-example for `consequences` + `review_lever`.** Evidence: run 55 and run 56 often contain the right substance but miss exact separators; run 59 paraphrases the review template instead of using `Controls A vs. B.`. Expected effect: lower chain-format misses and lower review-template misses without reducing depth.
- **H2. Tighten the naming instruction so lever names must include a project-specific noun, not just a generic compound strategy label.** Evidence: run 58 reuses `Funding-Resource Allocation Strategy` and `Technology-Integration Strategy` across unrelated domains. Expected effect: preserve uniqueness while increasing domain anchoring.
- **H3. Clarify what counts as a radical option with 2–3 acceptable patterns.** Evidence: radical-option misses remain high in baseline (52), run 54 (63), and run 58 (52). Expected effect: more consistent third-option escalation, especially on smaller models.
- **H4. Add a concise length ceiling in the prompt (for example: each field should usually be one sentence or under a soft character budget).** Evidence: run 59 produces very rich but contract-breaking outputs (1127 avg chars in `consequences`, 447 in `review`). Expected effect: reduce verbosity drift while preserving specificity.
- **H5. Explicitly forbid copying `Controls` or `Weakness` into `consequences`.** Evidence: run 57 leaks review text into every saved consequence. Expected effect: may reduce field contamination for models that mimic nearby schema language too aggressively.

## Potential Code Changes

- **C1. Add a post-generation validator/normalizer before writing `002-10-potential_levers.json`.** Evidence: runs 55, 56, 57, and 59 often contain valid strategic content that misses exact formatting. A validator could reject or normalize semicolon-separated chains, enforce `Controls A vs. B. Weakness: ...`, and catch `consequences` containing `Controls`/`Weakness`.
- **C2. Add structured retry/repair for JSON extraction failures in the step runner.** Evidence: run 53 fails 5/5 on extraction, and runs 55 and 57 lose plans to invalid JSON in `outputs.jsonl`. Expected effect: higher usable sample count across weaker or less JSON-stable models.
- **C3. Add a radical-option compliance check.** Evidence: the prompt alone is not reliably producing emerging-tech/business-model third options. A lightweight validator could either reject the item or trigger a targeted regeneration of just the third option.
- **C4. Add soft length guards in code, not just the prompt.** Evidence: run 59 demonstrates that stronger models will happily exceed the intended output granularity. Expected effect: keep later pipeline steps easier to compare and deduplicate.

## Summary

The prompt revision meaningfully improves **diversity** but not yet **discipline**.

Best signals:
- **Run 58** is the best current candidate for broad usability: fast, complete, high uniqueness, and clean structure.
- **Run 56** is the best candidate for richer strategy quality if the next revision can tighten format compliance.

Main failure patterns to address next:
- generic/measurable-light outputs on weaker models (run 54)
- parser fragility (runs 53, 55, 57)
- field contamination (run 57)
- verbosity and paraphrased-template drift (run 59)
- weak enforcement of truly radical third options (almost all runs)

If I had to pick the highest-leverage next move, I would combine **H1 + H3 + H4** at the prompt level and **C1 + C2** at the code level.
