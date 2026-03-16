# Insight Codex

## Rankings

- **Best current runs:** `history/0/96_identify_potential_levers`, `history/0/99_identify_potential_levers`, `history/1/00_identify_potential_levers`.
- **Weakest current runs:** `history/0/95_identify_potential_levers` (two review-format validator failures plus label leakage), `history/1/01_identify_potential_levers` (one option-count validator failure plus bracket placeholders), `history/0/97_identify_potential_levers` (many reviews still miss the exact `vs.` formatting).
- **Best previous runs:** `history/0/92_identify_potential_levers`, `history/0/93_identify_potential_levers`.
- **Weakest previous runs:** `history/0/88_identify_potential_levers`, `history/0/89_identify_potential_levers`.

## Negative Things

- The PR fixed the *targeted* silent-schema problems, but it also converts some malformed generations into hard failures. In the after set, `events.jsonl` shows 4 `run_single_plan_error` entries whose `error` strings begin with `LLM chat interaction failed...`; all 4 are validator-driven or schema-driven (`history/0/95_identify_potential_levers/events.jsonl`, `history/0/96_identify_potential_levers/events.jsonl`, `history/1/01_identify_potential_levers/events.jsonl`).
- Review strings are still often not in the exact prompt shape `Controls [Tension A] vs. [Tension B]. Weakness: ...` even when they pass the new validator. I counted 71/563 after levers with non-exact review formatting, mostly because they say `vs` instead of `vs.` or use bracket placeholders. Example: `history/0/97_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` has `Controls speed of delivery vs operational costs. Weakness: ...`; `history/1/01_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` has `Controls [protagonist's culpability and victim status] vs. [audience sympathy and sustained engagement]. ...`.
- Consequences are still contaminated with review text in 71 after levers, exactly the same count as the before set. Example after: `history/0/98_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` first lever ends its `consequences` with `Controls short-term implementation friction vs. long-term sovereignty. Weakness: ...`. Example before: `history/0/92_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` first lever does the same.
- Template leakage got worse after the PR: 20 option/review cells contain prohibited labels or bracket placeholders, versus 0 in the previous-analysis runs and 0 in baseline. The leakage is concentrated in `history/0/95_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` (`Conservative:`, `Moderate:`, `Radical:` prefixes) and `history/1/01_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (bracket placeholders in `review`).
- The “radical option” instruction is still overfitting some plans into repetitive tech tropes. In `history/0/95_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`, the exact option `Introduce a blockchain-based identity verification system` appears 7 times across different levers.
- One current success outlier remains shallow on measurable outcomes: all 51 levers shipped in `history/0/95_identify_potential_levers` lack a numeric or otherwise measurable `Systemic:` clause, despite the prompt requiring one. Compare that to the same prompt file, which explicitly says consequences must include a measurable outcome: `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt`.

## Positive Things

- The PR appears to have fixed the two specific silent-acceptance bugs it targeted. In the previous-analysis runs, 3 levers shipped with `options` length != 3 and 7 shipped reviews were missing either `Controls` or `Weakness:`. In the after runs, both counts drop to 0 in successful outputs.
- The option-count validator catches a real failure mode instead of letting it silently ship. Before: `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` contains `Music and Score`, `IP Rights and Censorship`, and `Revenue Strategy` with only 2 options each. After: `history/1/01_identify_potential_levers/outputs.jsonl` fails `20250321_silo` with `options must have exactly 3 items, got 7`, so the malformed lever set does not ship.
- The review-format validator also catches real malformed outputs. After: `history/0/95_identify_potential_levers/outputs.jsonl` shows both `20250321_silo` and `20250329_gta_game` failing because some `review_lever` values contained only `Controls ...` or only `Weakness: ...`. Those exact failure modes previously shipped in run 89.
- Overall plan success improved despite the new checks: 31/35 successful plans after versus 28/35 before.
- Strong after-run examples are better than baseline on specificity and quantitative grounding. `history/0/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` has consequences such as `Raise GPU load by 25% and reduce average frame rate by 10% on target consoles`, while baseline examples are generally shorter and less operationally detailed (for example `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`).

## Comparison

Compared with baseline training data, both the before and after runs generate much longer and more unique lever sets, but they also introduce failure patterns that baseline does not show. Baseline has 0 option-count violations, 0 review-marker omissions, 0 template leakage, and 0 consequence contamination in `baseline/train/*/002-10-potential_levers.json`. By contrast, the current prompt/run combination still produces exact-format drift, field contamination, and occasional validator-triggered retries.

Compared with the previous-analysis runs (`history/0/88_identify_potential_levers` through `history/0/94_identify_potential_levers`), the after runs clearly improve the targeted schema-validity metrics. The trade-off is that malformed outputs now fail fast instead of silently shipping. This is desirable for data integrity, but it means the remaining prompt-quality issues now surface as explicit run failures.

The strongest current runs (`96`, `99`, `100`) look more consistent than the strongest previous runs on option-count integrity and review marker presence. The weakest current runs are still informative: they reveal where the prompt and post-processing are not robust enough to satisfy the new validators reliably.

## Quantitative Metrics

### Dataset Summary

| Dataset | Plans evaluated | Successful plans | Success rate | Output files written | Levers | Avg levers per successful plan |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline train | 5 | 5 | 100.0% | 5 | 75 | 15.0 |
| Before PR (`88`-`94`) | 35 | 28 | 80.0% | 28 | 514 | 18.4 |
| After PR (`95`-`101`) | 35 | 31 | 88.6% | 31 | 563 | 18.2 |

### Uniqueness and Length

| Dataset | Unique lever names / levers | Unique options / option strings | Avg name len | Avg consequences len | Avg review len | Avg option len |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline train | 52 / 75 (69.3%) | 225 / 225 (100.0%) | 27.7 | 279.5 | 152.3 | 150.2 |
| Before PR | 513 / 514 (99.8%) | 1537 / 1542 (99.7%) | 38.3 | 414.1 | 188.8 | 135.6 |
| After PR | 558 / 563 (99.1%) | 1677 / 1689 (99.3%) | 39.2 | 412.5 | 182.2 | 136.5 |

Interpretation: uniqueness is extremely high in both experimental sets, so the dominant issues are not copy-paste duplication at the aggregate level. The bigger quality problems are *format compliance* and *field contamination*. The one notable duplication pocket is `history/0/95_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`, where the same blockchain option recurs 7 times.

### Constraint Violations and Leakage

| Metric | Baseline train | Before PR | After PR |
| --- | ---: | ---: | ---: |
| Levers with `options` count != 3 | 0 | 3 | 0 |
| Reviews missing `Controls` marker | 0 | 4 | 0 |
| Reviews missing `Weakness:` marker | 0 | 3 | 0 |
| Reviews not matching exact `Controls ... vs. ... Weakness: ...` shape | 0 | 78 | 71 |
| Consequences missing measurable outcome | 21 | 61 | 56 |
| Consequences contaminated with `Controls` / `Weakness:` text | 0 | 71 | 71 |
| Template leakage cells (`Conservative:` / `Moderate:` / `Radical:` / bracket placeholders) | 0 | 0 | 20 |

### Plan Error Causes from `events.jsonl`

| Window | Plan errors | Main causes |
| --- | ---: | --- |
| Before PR | 7 | 6 JSON-extraction failures in `history/0/88_identify_potential_levers/events.jsonl` and `history/0/90_identify_potential_levers/events.jsonl`; 1 timeout in `history/0/89_identify_potential_levers/events.jsonl` |
| After PR | 4 | 2 review-format validator failures in `history/0/95_identify_potential_levers/events.jsonl`; 1 invalid JSON in `history/0/96_identify_potential_levers/events.jsonl`; 1 option-count validator failure in `history/1/01_identify_potential_levers/events.jsonl` |

Note: `events.jsonl` does not use a literal `LLMChatError` event name here. Instead, the failures appear as `run_single_plan_error` rows whose `error` field starts with `LLM chat interaction failed...`.

## Evidence Notes

- **Prompt requirement for exact structure:** `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt` requires exactly 3 options, measurable `Systemic:` impacts, and a `review_lever` containing both `Controls ... vs. ...` and `Weakness:`.
- **Before PR, malformed outputs shipped:** `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` includes three levers with only 2 options. The same file also has a review that is only `Weakness: ...` and another that is only `Controls ...`.
- **After PR, the same classes of malformed outputs fail instead of shipping:** `history/0/95_identify_potential_levers/outputs.jsonl` shows review-format validation failures; `history/1/01_identify_potential_levers/outputs.jsonl` shows an option-count validation failure (`got 7`).
- **Exact-format drift still survives validation:** `history/0/97_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` uses `Controls speed of delivery vs operational costs. Weakness: ...` (missing the prompt’s `vs.` punctuation). `history/1/01_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` uses bracket placeholders in review tensions.
- **Field contamination persists before and after:** `history/0/92_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` and `history/0/98_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` both append `Controls ... Weakness: ...` text inside `consequences`.
- **Baseline remains cleaner structurally:** `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` keep consequences and review separate and contain no label leakage.

## PR Impact

The PR was supposed to stop two silent downstream-corruption problems:

1. levers shipping with the wrong number of options, and
2. `review_lever` values shipping without the required `Controls` / `Weakness:` markers.

### Before vs After

| Metric | Before (`88`-`94`) | After (`95`-`101`) | Change |
| --- | ---: | ---: | --- |
| Successful plans | 28 / 35 | 31 / 35 | +3 successful plans |
| Success rate | 80.0% | 88.6% | +8.6 pp |
| Shipped levers with `options` count != 3 | 3 | 0 | Fixed |
| Shipped reviews missing `Controls` marker | 4 | 0 | Fixed |
| Shipped reviews missing `Weakness:` marker | 3 | 0 | Fixed |
| Validator-caused plan failures | 0 | 3 | New explicit failures |
| Reviews still not in exact prompt shape | 78 / 514 (15.2%) | 71 / 563 (12.6%) | Slight improvement, not fixed |
| Consequences contaminated with review text | 71 / 514 (13.8%) | 71 / 563 (12.6%) | Flat in count |
| Template leakage cells | 0 | 20 | Worse |

### Did it fix the targeted issue?

Yes. On the metrics the PR explicitly targeted, the improvement is clear and measurable. The before set silently shipped 3 malformed option lists and 7 malformed review markers; the after set ships none of those defects. The after-set failures in `history/0/95_identify_potential_levers/outputs.jsonl` and `history/1/01_identify_potential_levers/outputs.jsonl` show the validators doing the intended job: rejecting bad structures instead of letting them leak downstream.

### Regressions

The PR does introduce a cost: three current plan failures are directly caused by the new validators or schema parsing, where the previous window had no validator-caused failures. Also, the validators do not address the broader prompt-quality issues that still dominate the step: exact-format drift, review text leaking into consequences, and template leakage. In other words, the PR fixes *schema integrity* more than it fixes *generation quality*.

### Verdict

**KEEP**

Reason: the PR produces a real and auditable improvement on the exact defects it was designed to prevent, and overall success rate also improves. The new failures are an acceptable trade if the next iteration addresses repair/retry strategy so malformed-but-salvageable outputs do not cost a full plan.

## Questions For Later Synthesis

- Should the next move be a prompt change or a repair pass for the persistent `consequences` contamination? This issue survives both before and after windows unchanged in absolute count.
- Is the exact `vs.` punctuation important downstream, or is the current marker-only validator enough? If downstream parsing depends on exact format, the present validator is too weak.
- Should template leakage be handled with stronger prompt exemplars or with a post-generation linter that rewrites obvious `Conservative:` / `Moderate:` / `Radical:` labels?
- Is the “emerging tech/business model” instruction pushing too many radical options toward repeated blockchain tropes, especially in sovereign identity?

## Reflect

The main lesson from this batch is that the PR improves **trustworthiness of shipped structure** more than **semantic quality**. That is still a worthwhile win. The after runs make it much easier to see the remaining problems, because malformed structures are now surfaced as explicit failures instead of hiding in downstream artifacts.

## Potential Code Changes

- **C1. Add a lightweight repair pass for field contamination.** If `consequences` contains `Controls ` or `Weakness:`, split that trailing segment into `review` before saving. Evidence: 71 contaminated consequences before and 71 after, with concrete examples in `history/0/92_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` and `history/0/98_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`. Expected effect: cleaner outputs without extra LLM retries.
- **C2. Keep the validators, but salvage obvious option-list overflow when possible.** The `history/1/01_identify_potential_levers/outputs.jsonl` failure includes `options must have exactly 3 items, got 7`, suggesting parser spillover rather than a wholly useless lever set. Expected effect: preserve more successful plans while still blocking silent corruption.
- **C3. Add a post-save linter for exact review shape and prohibited label leakage.** The current validator catches missing markers but not `vs` vs `vs.`, bracket placeholders, or `Conservative:` / `Moderate:` / `Radical:` leakage. Expected effect: reduce 71 exact-format misses and 20 leakage cells without turning them all into hard failures.

## Summary

- The PR fixes its two intended silent-failure modes: no shipped bad option counts and no shipped missing review markers in the after runs.
- Overall success also improves from 80.0% to 88.6%.
- The remaining issues are now more visible: exact review formatting still drifts, consequences still absorb review text, and template leakage actually worsens in the after window.
- Prompt hypotheses: **H1** add one explicit JSON exemplar that separates `consequences` from `review`; **H2** add negative examples for `Conservative:` / `Moderate:` / `Radical:` and bracket placeholders; **H3** require diversity among radical options to avoid repeated blockchain tropes; **H4** restate that every `Systemic:` clause must include a numeric or otherwise auditable metric.
- Code hypotheses: **C1-C3** above.
