# Insight Codex

Examined `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`, the five baseline training plans under `baseline/train/`, and history runs `history/1/24_identify_potential_levers` through `history/1/30_identify_potential_levers`.

## Rankings

- **Best content richness on successful plans:** run 30 (`anthropic-claude-haiku-4-5-pinned`) > run 29 (`openrouter-gemini-2.0-flash-001`) ≈ run 26 (`openai-gpt-5-nano`) ≈ run 25 (`openrouter-openai-gpt-oss-20b`) > run 28 (`openrouter-openai-gpt-4o-mini`) > run 27 (`openrouter-qwen3-30b-a3b`) > run 24 (`ollama-llama3.1`).
- **Best operational reliability:** run 28 > runs 24/26/27/30 > run 25 > run 29.
- **Best balance for later synthesis:** run 28 is the cleanest speed/quality compromise; run 30 is the richest but most verbose; run 25 is strong but incomplete because one plan failed.

## Negative Things

- **Summary-format compliance is still near-zero.** The prompt explicitly asks for `summary` to prescribe an addition in the form `Add '[full strategic option]' to [lever]` (`prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:27`-`:29`), but six of seven history runs produced `0/15` exact matches; only run 24 managed `14/15`.
- **The “radical option must include emerging tech/business model” clause is broadly not landing.** Even the strongest runs still miss it often by heuristic scan of the third option: run 25 missed 23, run 28 missed 63, run 30 missed 90. This suggests either the instruction is too buried or too brittle for non-tech domains.
- **Run 27 has major field bleed.** In 66 of 85 final levers, the `consequences` field also contains the `review` text. Example: `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` appends `Controls security vs. autonomy. Weakness: ...` directly inside `consequences`, then repeats the same text in `review` at `:11`.
- **Run 24 still leaks placeholders and over-generates.** `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:93` contains bracket placeholders (`Immediate: [Establish a strict hierarchical structure ...]`) even though the prompt forbids placeholder consequences. The raw file for the same plan has response sizes `8/6/7`, so it also breaks the `5 to 7 levers per response` cap.
- **Run 25 has a real execution failure, not just weak content.** `history/1/25_identify_potential_levers/events.jsonl:7` and `history/1/25_identify_potential_levers/outputs.jsonl:2` show a `run_single_plan_error` caused by `Invalid JSON: EOF while parsing a list`, which dropped the entire `20260311_parasomnia_research_unit` plan.
- **Run 29 suffers from infrastructure failure before it succeeds.** `history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5` and matching entries in `history/1/29_identify_potential_levers/events.jsonl:2`-`:10` show five create-stage failures because `openrouter-paid-gemini-2.0-flash-001` was not found in config. The later successful outputs hide a serious wasted-attempt problem.
- **Run 26 collapses distinct reviews into repeated boilerplate.** The exact review string `Controls centralization vs. local autonomy. Weakness: The options fail to consider transition costs.` appears 12 times across multiple files, including `history/1/26_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:77` and `history/1/26_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:143`.
- **Run 24 is too shallow despite high uniqueness.** It has perfect exact-name uniqueness but the shortest average consequences (`19.2` words) and shortest options (`10.7` words), plus 55 consequences without any measurable indicator.

## Positive Things

- **The newer prompt clearly improves name diversity versus baseline.** Baseline final outputs contain only 52 unique names across 75 levers and repeated labels like `Technological Adaptation Strategy` three times in `baseline/train/20250321_silo/002-10-potential_levers.json:26`, `:92`, and `:147`. Every successful history run reached exact-name uniqueness of 100% on its produced levers.
- **Most history runs materially improve measurable consequences over baseline.** Baseline still has 21 consequences without a measurable indicator; runs 25, 27, 28, and 30 have zero such misses, and run 29 has only 3.
- **Cross-call duplication is mostly eliminated.** Baseline and run 24 each have 22 duplicate lever names across the three raw responses per plan, but runs 25 through 30 reduce exact cross-call duplicate names to zero.
- **Run 28 is the cleanest balanced run.** It completed all 5 plans, had no error attempts, averaged only `56.11s` per successful plan, and had zero placeholder leaks, zero field-bleed cases, and zero missing-measurement consequences.
- **Run 30 produces the strongest strategic depth.** It has by far the longest average consequences (`121.2` words), options (`39.3` words), and reviews (`41.6` words). Example: `history/1/30_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` provides quantified second-order effects and a clear market-positioning implication.
- **Run 25 is the best strict-content run among completed plans.** On the 4 plans it finished, it had zero measurement misses, zero placeholder leaks, zero cross-call duplicate names, and the lowest estimated radical-option misses (`23`). Example: `history/1/25_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` includes a 15% indicator and `:9` gives a genuine business-model shift via equity crowdfunding.

## Comparison

- **Baseline vs history prompt behavior:** the baseline raw prompt still required the same summary pattern, but it also enforced `EXACTLY 5 levers per response` and encouraged more formulaic strategic naming (`baseline/train/20250321_silo/002-9-potential_levers_raw.json:383`). The current prompt changes that to `5 to 7 levers` and asks for domain language in lever names (`prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:4` and `:18`-`:20`).
- **What improved over baseline:** exact name uniqueness, cross-call duplicate-name reduction, and measurable consequence coverage all improved in most history runs.
- **What did not improve:** summary exact-format compliance was already weak in baseline and remains weak now. This looks like a persistent instruction-following problem, not a one-off model issue.
- **What regressed in some runs:** baseline average option length (`19.0` words) is still better than runs 24 (`10.7`), 25 (`12.7`), 27 (`8.5`), and 28 (`14.3`). The newer prompt helps diversity, but several models respond by getting terser rather than more strategic.
- **Model-specific failure modes dominate more than prompt-wide collapse.** Run 24 over-generates and leaks placeholders; run 26 repeats review boilerplate; run 27 bleeds fields; run 29 wastes attempts on config; run 30 is rich but not format-tight.
- **The best evidence that the prompt change helped is naming, not summaries.** The old prompt’s example-style naming correlates with baseline duplicates, while the newer domain-language instruction correlates with zero duplicate names in runs 25–30.

## Quantitative Metrics

Metrics below are computed from the final merged levers in `002-10-potential_levers.json`, the raw three-response files in `002-9-potential_levers_raw.json`, and the run-level `outputs.jsonl` / `events.jsonl` where relevant. `radical_miss` is heuristic: it flags third options that do not obviously mention emerging tech or a business-model shift.

### Operational / Contract Metrics

| Run | Model | Ok plans | Error attempts | Avg ok sec | Avg levers / plan | Summary exact matches | Raw lever-count violations |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | baseline reference | - | - | - | 15.0 | 0 / 15 | 0 |
| 24 | ollama-llama3.1 | 5 | 0 | 119.86 | 17.0 | 14 / 15 | 4 |
| 25 | openrouter-openai-gpt-oss-20b | 4 | 1 | 129.75 | 17.5 | 0 / 12 | 0 |
| 26 | openai-gpt-5-nano | 5 | 0 | 239.47 | 18.2 | 0 / 15 | 0 |
| 27 | openrouter-qwen3-30b-a3b | 5 | 0 | 149.44 | 17.0 | 0 / 15 | 0 |
| 28 | openrouter-openai-gpt-4o-mini | 5 | 0 | 56.11 | 17.6 | 0 / 15 | 0 |
| 29 | openrouter-gemini-2.0-flash-001 | 5 | 5 | 36.88 | 18.0 | 0 / 15 | 0 |
| 30 | anthropic-claude-haiku-4-5-pinned | 5 | 0 | 188.91 | 21.0 | 0 / 15 | 0 |

### Diversity / Depth Metrics

| Run | Unique names | Cross-call duplicate names | Avg consequence words | Avg option words | Avg review words |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 52 / 75 | 22 | 33.7 | 19.0 | 20.5 |
| 24 | 85 / 85 | 22 | 19.2 | 10.7 | 22.8 |
| 25 | 70 / 70 | 0 | 43.6 | 12.7 | 16.9 |
| 26 | 91 / 91 | 0 | 52.1 | 14.5 | 18.2 |
| 27 | 85 / 85 | 0 | 41.4 | 8.5 | 16.3 |
| 28 | 88 / 88 | 0 | 29.5 | 14.3 | 19.3 |
| 29 | 90 / 90 | 0 | 50.5 | 16.0 | 20.2 |
| 30 | 105 / 105 | 0 | 121.2 | 39.3 | 41.6 |

### Violation / Leakage Metrics

| Run | Missing measurable consequence | Consequence→review bleed | Strict review-template mismatches | Placeholder leaks | Likely radical-tech misses |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 21 | 0 | 0 | 0 | 49 |
| 24 | 55 | 0 | 0 | 6 | 71 |
| 25 | 0 | 0 | 0 | 0 | 23 |
| 26 | 2 | 0 | 41 | 0 | 35 |
| 27 | 0 | 66 | 0 | 0 | 57 |
| 28 | 0 | 0 | 0 | 0 | 63 |
| 29 | 3 | 0 | 0 | 0 | 59 |
| 30 | 0 | 0 | 0 | 0 | 90 |

### Review Duplication

| Run | Duplicate review reuses | Worst repeated review | Count |
| --- | ---: | --- | ---: |
| baseline | 0 | none | 1 |
| 24 | 0 | none | 1 |
| 25 | 0 | none | 1 |
| 26 | 19 | `Controls centralization vs. local autonomy. Weakness: The options fail to consider transition costs.` | 12 |
| 27 | 1 | `Controls standardization vs. vendor flexibility. Weakness: The options fail to account for legacy system integration challenges.` | 2 |
| 28 | 0 | none | 1 |
| 29 | 0 | none | 1 |
| 30 | 0 | none | 1 |

Interpretation:

- Perfect exact-name uniqueness does **not** mean perfect diversity; run 24 is unique by name but shallow by option/consequence depth.
- Run 30’s depth is real, but it comes with extreme verbosity and poor adherence to the radical-option clause.
- Run 28 is the strongest all-around operational profile, while run 25 is strongest on strict content features among completed plans.
- The summary format is the most consistently ignored instruction in the entire batch.

## Evidence Notes

- `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:23`-`:29` defines a strict `review_lever` pattern and a strict `summary` prescription. The outputs mostly honor the review shape but not the summary shape.
- `baseline/train/20250321_silo/002-9-potential_levers_raw.json:383` shows the earlier baseline prompt wording: `EXACTLY 5 levers per response` and more formulaic lever naming. This likely explains why baseline has repeated names like `Technological Adaptation Strategy` in `baseline/train/20250321_silo/002-10-potential_levers.json:26`, `:92`, and `:147`.
- `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:93` contains a forbidden placeholder consequence (`Immediate: [Establish a strict hierarchical structure ...]`), and the raw source for the same plan contains one of the few exact-format summaries at `history/1/24_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:95`.
- `history/1/25_identify_potential_levers/events.jsonl:7` is the only JSON/schema-like failure in this batch: `Invalid JSON: EOF while parsing a list`. I did **not** find the earlier max-length style `LLMChatError` pattern here; the current failure is truncated JSON, not over-generation against a hard array cap.
- `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `:11` prove a structural merge/field-separation issue: review text is duplicated inside `consequences` and then again in `review`.
- `history/1/28_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:84` shows the dominant summary failure mode: a reasonable explanatory preamble followed by `Add ...`, which is useful content but not the exact requested shape.
- `history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5` documents five wasted attempts due to a missing model alias before the run later succeeds.
- `history/1/30_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:9` shows why the radical-option heuristic still flags strong outputs: the third option is strategically interesting, but it is neither obvious emerging tech nor a business-model innovation despite the prompt requiring one.

## Questions For Later Synthesis

- Is summary exactness important enough to justify a stricter prompt or post-processing repair, or is the current “explanatory preamble + Add ...” pattern acceptable?
- Should the radical-option rule be softened to “emerging tech **or** unconventional business/governance model” so film / research / public-sector projects do not get awkwardly forced into tech jargon?
- Is run 30’s verbosity a feature or a liability for downstream steps that must read and rank these levers?
- Does run 27’s consequence/review bleed come from the model alone, or from a post-processing/merging path that fails to separate fields when the model repeats the review string?
- Are duplicate reviews in run 26 a prompt problem (“exact order” overweights the template) or a merge/dedup problem that should be fixed in code?

## Reflect

- **H1:** Move the `summary` requirement to a final, explicit hard instruction such as “`summary` must start with `Add '` and contain no preamble sentence.” Evidence: the prompt already states the desired format (`prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:27`-`:29`), but runs 25–30 all miss it on every raw response. Expected effect: raise summary exact-format compliance from ~0% to something measurable without reducing strategic usefulness.
- **H2:** Add an explicit field-separation prohibition: “`consequences` must not contain `Controls` or `Weakness:` text; that belongs only in `review_lever`.” Evidence: run 27 contaminates 66/85 final `consequences` fields with review text (`history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`). Expected effect: reduce structural bleed without needing a code repair.
- **H3:** Add a uniqueness requirement for `review_lever`, e.g. “each weakness must be specific to this lever and should not repeat across levers.” Evidence: run 26 repeats the same review sentence 12 times across plans. Expected effect: improve diagnostic usefulness of the review field and reduce template collapse.
- **H4:** Rephrase the radical-option rule to fit domain variation: “third option must introduce an emerging tech, unconventional business model, or unconventional governance mechanism appropriate to the domain.” Evidence: the current clause (`prompts/...:38`-`:40`) is widely missed even by high-quality outputs; run 30’s third options are strong but often not tech/business-model specific. Expected effect: better domain-fit and fewer forced or artificial radical options.

## Potential Code Changes

- **C1:** Fix model-name/config resolution so invalid aliases fail before the batch starts, not plan-by-plan at runtime. Evidence: run 29 burns five create-stage attempts on a missing alias (`history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5`). Expected effect: eliminate wasted retries and make reliability metrics reflect model quality rather than config accidents.
- **C2:** Add a JSON-repair / salvage path for truncated responses before discarding a plan. Evidence: run 25 loses the entire `parasomnia_research_unit` plan on `Invalid JSON: EOF while parsing a list` (`history/1/25_identify_potential_levers/events.jsonl:7`). Expected effect: recover some fraction of otherwise-lost outputs and reduce sensitivity to minor truncation.
- **C3:** Add a post-parse lint/repair pass that detects `Strategic: ... Controls ... Weakness:` in `consequences` and moves the suffix into `review`. Evidence: run 27’s final artifacts preserve obvious field contamination. Expected effect: rescue structurally valid content from near-miss generations.
- **C4:** Record step-specific quality telemetry automatically (summary exact match, field bleed, placeholder count, cross-call duplicate names, likely radical-option misses). Evidence: these failure modes are visible in artifacts but currently require manual forensic analysis. Expected effect: faster synthesis and more reliable regression detection in future prompt iterations.

## Summary

- The prompt change appears to have **helped naming diversity a lot**: all successful history runs beat baseline on exact lever-name uniqueness, likely because the old baseline prompt encouraged formulaic “Strategy” naming.
- The biggest remaining prompt-wide problem is **summary noncompliance**; the strict summary rule is being ignored across almost every model and even baseline.
- The strongest content runs are **30** for depth and **25** for strict content quality on completed plans; the strongest operational run is **28**.
- The most important non-prompt issues are **run 29’s broken model alias**, **run 25’s truncated-JSON failure**, and **run 27’s field bleed**, all of which look fixable in code or workflow.
