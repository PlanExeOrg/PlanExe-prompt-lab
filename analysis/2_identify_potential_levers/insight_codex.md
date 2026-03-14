# Insight Codex

## Rankings

- **Tier A:** Run `22` (`openrouter-openai-gpt-4o-mini`) and run `20` (`openai-gpt-5-nano`). Run `22` is the strongest diversity performer: all five files succeed, all five average `15/15` unique lever names, and it has zero duplicate names or template leakage in the final artifacts. Its main weakness is contract drift on the exact `Immediate:` label in 45 of 75 levers. Run `20` is the best baseline-like run on length and measurable outcomes, but its reviews drift from the required `Controls ... vs. .... Weakness:` template in 60 of 75 levers.
- **Tier B:** Run `23` (`anthropic-claude-haiku-4-5-pinned`) and run `21` (`openrouter-qwen3-30b-a3b`). Run `23` is rich and specific, but it times out on one plan, overproduces to 19 levers on `20250321_silo`, and is much longer than baseline. Run `21` is operationally reliable and structurally clean, but its options are extremely short and it collapses to repeated five-lever sets on several plans.
- **Tier C:** Run `18` (`ollama-llama3.1`). It completes all plans, but it is heavily templated: average uniqueness is only `5.2/15`, it copies the prompt example name 12 times, misses numeric outcomes on all 76 levers, and overproduces to 16 levers on `20260310_hong_kong_game`.
- **Tier D:** Run `17` (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) and run `19` (`openrouter-openai-gpt-oss-20b`). These are mostly reliability failures rather than serious candidates for prompt tuning.

## Negative Things

- Literal-format compliance is still brittle across otherwise good runs. The prompt explicitly requires `Immediate: ... → Systemic: ... → Strategic: ...` and reviews of the form `Controls [Tension A] vs. [Tension B]. Weakness: ...` in `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:8` and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`. Run `22` omits the literal `Immediate:` opener on 45 levers; the first silo lever starts `Implementing advanced resource management will lead to immediate cost savings → ...` at `history/0/22_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`. Run `20` rewrites the review opener to `Trade-off:` at `history/0/20_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:11`. Run `18` drops the `Weakness:` token entirely in `history/0/18_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:11`.
- Cross-call duplication remains a major failure mode. Run `18` averages only `5.2` unique names per 15-lever file, and run `21` averages `9.0`; both often repeat the same five names three times. In run `21`, `Material Adaptation Strategy` repeats at `history/0/21_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4`, `:59`, and `:114`, with the same pattern for `Financial Resilience Framework` and `Talent Allocation Model`.
- The prompt example name leaks directly into outputs. The prompt uses `Material Adaptation Strategy` as an example at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:19`, and run `18` copies it 12 times across four plans, for example at `history/0/18_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`, `:59`, and `:114`.
- Reliability is still weak for two models. Run `17` fails four of five plans with empty extraction or invalid JSON in `history/0/17_identify_potential_levers/outputs.jsonl:1`, `:2`, `:3`, and `:5`. Run `19` also fails four of five, and one failure is a conversational clarification request instead of JSON in `history/0/19_identify_potential_levers/outputs.jsonl:1`.
- Run `23` appears to hit a verbosity ceiling. Its average consequence length is `682.2` characters, average option length `308.4`, and average review length `385.5`, versus baseline `279.5`, `150.2`, and `152.3`. It also times out on `20260310_hong_kong_game` in `history/0/23_identify_potential_levers/outputs.jsonl:5`, and its silo output expands to 19 levers with extra tail entries such as `Entertainment, Recreation, and Existential Meaning-Making Infrastructure` at `history/0/23_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:202`.

## Positive Things

- Run `22` is the clearest evidence that the prompt can drive strong breadth. It succeeds on all five plans, produces `75/75` unique lever names across the successful corpus, and has zero duplicate names, zero option-count violations, zero review-format violations, zero measurable-outcome misses, and zero template leakage in the final artifacts.
- Run `20` is the best match to baseline depth without the baseline's measurable-outcome gaps. Its average lengths (`274.0` consequence, `152.1` option, `153.7` review) are almost exactly baseline (`279.5`, `150.2`, `152.3`), while numeric-outcome misses drop from baseline `21/75` to `0/75`.
- Run `21` shows that strict structural compliance is possible without retries or leakage: all five plans succeed, all files have 15 levers with 3 options each, and there are zero chain-label misses, zero review-format misses, and zero placeholder/prefix leakage.
- Run `23` shows the ceiling for strategic specificity. The first silo lever already introduces explicit internal collapse horizons and governance trade-offs at `history/0/23_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `:11`, which is more assumption-challenging than most baseline entries.
- Even the weaker successful runs avoid simple copying from the baseline corpus. Exact baseline name overlap is `0/76` for run `18`, `0/75` for runs `20` and `21`, and `0/64` for run `23`; only run `22` shows small overlap at `6/75` despite much higher uniqueness than baseline.

## Comparison

- The baseline training set is not a gold-standard target; it is mixed. Baseline files average only `10.6` unique names out of 15, and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats the same five names three times (`Technical Feasibility Strategy`, `Policy Advocacy Strategy`, `Coalition Building Strategy`, `Procurement Influence Strategy`, `EU Standards Engagement Strategy`) at lines `4`, `15`, `26`, `37`, `48`, then again at `59`, `70`, `81`, `92`, `103`, and again at `114`, `125`, `136`, `147`, `158`.
- Relative to baseline, run `22` is the biggest diversity improvement: `15.0` unique names per file versus baseline `10.6`, and `71` unique names across its 75 total levers versus baseline `52/75`. The trade-off is exact-format drift on the consequence opener.
- Relative to baseline, run `20` is the best “safe” improvement. It preserves baseline-like length and structural completeness, improves measurable outcomes from `21` misses to `0`, but sacrifices exact review phrasing by consistently using `Trade-off:` rather than `Controls ... vs. ...`.
- Relative to baseline, run `21` improves uniqueness on two plans (`20250321_silo` and `20260311_parasomnia_research_unit`) but regresses badly on others by collapsing to repeated five-name sets. Its average option length of `64.2` characters is less than half the baseline average `150.2`, which suggests terse labels rather than full strategic pathways.
- Relative to baseline, run `18` is worse on almost every quality dimension except runtime reliability: shorter options (`89.8` vs. `150.2`), lower uniqueness (`5.2` vs. `10.6`), total numeric-outcome failure (`76/76` misses), prompt-example copying, and one 16-lever merged artifact.
- Relative to baseline, run `23` is more ambitious but operationally fragile. It is far more detailed, but the longer text correlates with one timeout and one overproduced file; this looks like a “too much quality per call” failure mode rather than a lack of capability.

## Quantitative Metrics

### Coverage and uniqueness

| Variant | Model | OK plans | Error plans | Avg unique names/file | Duplicate names/file | Corpus unique names | Baseline name overlap |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline train | n/a | 5 | 0 | 10.6 | 4.4 | 52 / 75 | n/a |
| Run 17 | `openrouter-nvidia-nemotron-3-nano-30b-a3b` | 1 | 4 | 8.0 | 7.0 | 8 / 15 | 0 / 15 |
| Run 18 | `ollama-llama3.1` | 5 | 0 | 5.2 | 10.0 | 23 / 76 | 0 / 76 |
| Run 19 | `openrouter-openai-gpt-oss-20b` | 1 | 4 | 5.0 | 10.0 | 5 / 15 | 0 / 15 |
| Run 20 | `openai-gpt-5-nano` | 5 | 0 | 8.4 | 6.6 | 42 / 75 | 0 / 75 |
| Run 21 | `openrouter-qwen3-30b-a3b` | 5 | 0 | 9.0 | 6.0 | 45 / 75 | 1 / 75 |
| Run 22 | `openrouter-openai-gpt-4o-mini` | 5 | 0 | 15.0 | 0.0 | 71 / 75 | 6 / 75 |
| Run 23 | `anthropic-claude-haiku-4-5-pinned` | 4 | 1 | 13.5 | 2.5 | 54 / 64 | 0 / 64 |

### Average field lengths (characters)

| Variant | Consequences | Options | Review |
|---|---:|---:|---:|
| Baseline train | 279.5 | 150.2 | 152.3 |
| Run 17 | 236.9 | 116.5 | 140.8 |
| Run 18 | 188.4 | 89.8 | 154.8 |
| Run 19 | 219.5 | 75.3 | 123.8 |
| Run 20 | 274.0 | 152.1 | 153.7 |
| Run 21 | 177.2 | 64.2 | 140.9 |
| Run 22 | 238.5 | 106.9 | 148.8 |
| Run 23 | 682.2 | 308.4 | 385.5 |

### Constraint violations and template leakage

| Variant | Lever count drift | Option-count violations | Missing chain labels | Missing numeric outcomes | Review-format violations | Prefix leakage | Bracket leakage | Prompt-example copies |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline train | 0 | 0 | 5 | 21 | 0 | 0 | 0 | 0 |
| Run 17 | 0 | 0 | 0 | 0 | 15 | 0 | 0 | 0 |
| Run 18 | 1 | 0 | 0 | 76 | 16 | 0 | 0 | 12 |
| Run 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Run 20 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 1 |
| Run 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| Run 22 | 0 | 0 | 45 | 0 | 0 | 0 | 0 | 0 |
| Run 23 | 4 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |

### Per-plan uniqueness counts

| Variant | `20250321_silo` | `20250329_gta_game` | `20260308_sovereign_identity` | `20260310_hong_kong_game` | `20260311_parasomnia_research_unit` |
|---|---:|---:|---:|---:|---:|
| Baseline train | 11 | 14 | 5 | 12 | 11 |
| Run 17 | — | — | 8 | — | — |
| Run 18 | 5 | 5 | 5 | 6 | 5 |
| Run 19 | 5 | — | — | — | — |
| Run 20 | 9 | 13 | 5 | 10 | 5 |
| Run 21 | 15 | 5 | 5 | 5 | 15 |
| Run 22 | 15 | 15 | 15 | 15 | 15 |
| Run 23 | 19 | 15 | 5 | — | 15 |

Interpretation:

- `Lever count drift` in the table above means the total number of extra merged levers beyond the expected 15-per-file baseline across successful files.
- Perfect uniqueness is achievable on this step; run `22` proves that the repeated-five-name pattern is not inherent to the task.
- Baseline-like field lengths do not guarantee prompt compliance; run `20` matches baseline depth but still misses the exact review format.
- Template leakage here is mostly **prompt-example copying** rather than bracket placeholders or `Option A:` labels in this batch of runs.
- Overproduction is rare but high impact when it occurs; runs `18` and `23` each show that a single file can make the merged artifact invalid.

## Evidence Notes

- Prompt contract: `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:4`, `:5`, `:9`, `:10`, `:19`, `:25`, `:26`.
- Baseline repetition benchmark: `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:4`, `:59`, `:114` and neighboring repeated name lines.
- Run `18` prompt-example leakage: `history/0/18_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`, `:59`, `:114`.
- Run `18` review-format drift and overproduction: `history/0/18_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:11`, `:154`, `:158`, `:169`.
- Run `20` review-format drift despite otherwise strong lengths: `history/0/20_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:11`, `:22`.
- Run `21` repeated five-name set: `history/0/21_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4`, `:15`, `:26`, `:59`, `:70`, `:81`, `:114`, `:125`, `:136`.
- Run `22` exact-label drift with otherwise strong diversity: `history/0/22_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.
- Run `23` verbosity and overproduction: `history/0/23_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`, `:11`, `:158`, `:202`.
- Run `17` extraction failures: `history/0/17_identify_potential_levers/outputs.jsonl:1`, `:2`, `:3`, `:5`.
- Run `19` conversational non-JSON failure: `history/0/19_identify_potential_levers/outputs.jsonl:1`.
- Run `23` timeout: `history/0/23_identify_potential_levers/outputs.jsonl:5`.

## Questions For Later Synthesis

1. Should later evaluation treat exact literal labels (`Immediate:` and `Controls ... vs. ...`) as hard requirements, or is semantic equivalence acceptable? This matters because run `22` is otherwise the strongest run.
2. Is cross-call uniqueness a true objective for the merged 15-lever artifact? The prompt only says each response must contain exactly five levers, but the downstream artifact clearly benefits from 15 distinct names.
3. Should prompt-example phrase reuse (`Material Adaptation Strategy`) count as automatic template leakage, or only when it recurs across multiple calls as in runs `18` and `21`?
4. Is there a maximum useful verbosity for this step? Run `23` may be strategically best on some entries, but the timeout and 2-3x field lengths suggest diminishing returns.
5. Should baseline weaknesses be normalized away during scoring? Baseline itself repeats names and often misses measurable outcomes, so “matching baseline” is not enough.

## Reflect

The main lesson from this batch is that the prompt is good at eliciting **either** breadth **or** exact template obedience, but not consistently both. Run `22` demonstrates that high diversity is achievable without retries or placeholder leakage. Run `20` demonstrates that near-baseline length and measurable specificity are achievable. But no run combines run `22`'s uniqueness, run `20`'s baseline-like pacing, and exact literal compliance on both the consequence opener and review wording.

The baseline comparison is especially important here because the baseline is partially flawed. It already tolerates repeated five-name sets and missing measurable outcomes, especially in `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` and `baseline/train/20260311_parasomnia_research_unit/002-10-potential_levers.json`. That means a run can be meaningfully better than baseline while still violating the prompt, or can look baseline-like while preserving baseline weaknesses.

My current bias is that **cross-call diversity and post-generation validation** are the biggest leverage points. Diversity is the biggest visible upside in this batch, and the main failures are machine-checkable: wrong review prefix, missing literal chain opener, repeated name sets, overlong responses, and occasional non-JSON fallbacks.

## Prompt Hypotheses

- **H1:** Add an explicit final self-check that requires the **exact literal forms** `Immediate:` / `Systemic:` / `Strategic:` and `Controls X vs. Y. Weakness:` before the model finalizes. Evidence: run `22` misses the exact `Immediate:` label on 45 levers; run `20` rewrites reviews to `Trade-off:`; run `18` drops `Weakness:` despite otherwise coherent reviews. Expected effect: higher exact-format compliance without sacrificing the content quality already visible in runs `20` and `22`.
- **H2:** Add a direct prohibition against **reusing example lever names** and against repeating the same five lever names across multiple calls in the merged artifact. Evidence: prompt example `Material Adaptation Strategy` is copied repeatedly in run `18`, and run `21` repeats the same five names three times on several plans. Expected effect: improved merged-artifact diversity and lower template leakage.
- **H3:** Add a stronger measurable-outcome requirement such as `every consequence must contain at least one numeric quantity, percentage, time horizon, or count`. Evidence: run `18` misses numeric outcomes on all 76 levers, while run `20` reaches `0/75` misses under the same base prompt. Expected effect: fewer vague consequences, especially on weaker local/open models.
- **H4:** Add a brevity target such as `keep each consequence under ~320 characters and each review under ~220 characters unless a specific hidden assumption requires more`. Evidence: run `23` is 2-3x baseline length and times out once, while run `20` stays close to baseline length and still delivers useful specificity. Expected effect: lower timeout risk and less overproduction without forcing generic outputs.
- **H5:** Add an instruction that `options must be full strategic approaches, not short labels`, with a minimum specificity cue such as naming actors, mechanisms, or timing. Evidence: run `21` is structurally clean but its average option length is only `64.2` characters, far below baseline `150.2`, and many options read like compressed labels. Expected effect: preserve structural compliance while increasing decision usefulness.

## Potential Code Changes

- **C1:** Add a merged-artifact validator that rejects or retries outputs unless the final file has exactly 15 levers, exactly 3 options per lever, and the required literal markers in consequences and reviews. Evidence: run `18` writes 16 levers on `20260310_hong_kong_game`, run `23` writes 19 on `20250321_silo`, run `20` drifts to `Trade-off:`, and run `22` drops `Immediate:`. Expected effect: harden output quality regardless of model idiosyncrasies.
- **C2:** Add a post-merge dedupe/rerank pass over lever names and near-duplicate lever sets across the three source calls. Evidence: baseline sovereign identity, run `18`, run `21`, and run `23` all show repeated five-name patterns. Expected effect: better solution-space breadth even when individual calls are locally valid.
- **C3:** Strengthen JSON extraction and retry policy when the model emits clarification text, empty text, or truncated JSON. Evidence: run `17` fails mostly with empty extraction; run `19` includes a conversational “Could you let me know...” reply instead of JSON at `history/0/19_identify_potential_levers/outputs.jsonl:1`. Expected effect: convert some Tier D failures into usable outputs without prompt changes.
- **C4:** Add response-length safeguards at execution time, such as a stricter output-token cap or an automatic retry with a shorter-system-message variant when the first pass exceeds a threshold. Evidence: run `23` is dramatically longer than baseline and ends with an API timeout. Expected effect: reduce timeouts and merged-file overproduction on high-detail models.
- **C5:** Add analysis-time scoring that separates **semantic quality** from **literal contract compliance**. Evidence: run `22` may be strategically the best run despite failing the exact `Immediate:` string; baseline itself misses several measurable outcomes. Expected effect: better synthesis decisions and less overfitting to surface formatting.

## Summary

The best levers from this batch are clear:

- Run `22` shows the highest achievable diversity.
- Run `20` shows the best baseline-like depth and measurable specificity.
- Run `23` shows the upper bound of strategic richness, but also where verbosity starts to break the pipeline.

The biggest actionable opportunities are also clear:

- tighten literal-format self-checks,
- explicitly ban prompt-example reuse and repeated five-name sets,
- validate merged outputs before writing them,
- and harden extraction/retry behavior for non-JSON or overlong responses.

If synthesis wants the next prompt candidate to be low-risk, I would start from a run-`20` / run-`22` blend: keep run `20`'s pacing, import run `22`'s diversity target, and then use code-level validation to catch the exact-label failures that neither run solves on its own.
