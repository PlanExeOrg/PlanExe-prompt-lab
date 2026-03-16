# Insight Codex

## Rankings

1. **Run 91 — `openai-gpt-5-nano`**: best balance of reliability, specificity, and contract compliance; 5/5 plans succeeded, no observed structural violations, and outputs stayed materially richer than baseline without Haiku-level verbosity.
2. **Run 93 — `openrouter-openai-gpt-4o-mini`**: also 5/5 successful, concise relative to the rest of the field, and no observed schema/format violations.
3. **Run 92 — `openrouter-qwen3-30b-a3b`**: fully reliable and clean, but usually stayed at the low end of the requested lever count (`5,5,5` or `6,7,5` patterns), so it explored less surface area than the top two.
4. **Run 94 — `anthropic-claude-haiku-4-5-pinned`**: the PR clearly helped this model operationally, but it remains extremely verbose and now occasionally over-generates to 8 levers in a raw response.
5. **Run 90 — `openrouter-openai-gpt-oss-20b`**: solid on successful plans, but still lost `20260308_sovereign_identity` to JSON extraction failure.
6. **Run 89 — `ollama-llama3.1`**: partial operational success, but this run had the messiest contract slippage after the PR: over-generation (`8` and `9` lever responses), three 2-option levers, and malformed review fields.
7. **Run 88 — `openrouter-nvidia-nemotron-3-nano-30b-a3b`**: unchanged from the prior run family in the worst way; 0/5 plans completed because the model still failed JSON extraction on every plan.

## Negative Things

- The PR fixed the targeted `max_length=7` failure mode, but it did **not** improve overall run success: before and after both finished `28/35` plans successfully.
- Raw-response compliance with the prompt’s “5 to 7 levers per response” guidance got worse after the PR: before there were `0` raw responses over 7 levers; after there were `3` (`2` in run 89, `1` in run 94). The prompt still says `5 to 7 levers per response` in `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:4`.
- Run 89 introduced the clearest downstream quality issue: in `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:48`, `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:58`, and `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:68`, the levers `Music and Score`, `IP Rights and Censorship`, and `Revenue Strategy` have only **2** options each, violating the exact-3-options contract.
- The same run 89 file also shows review-format drift: `Music and Score` and `IP Rights and Censorship` contain only `Weakness:` without the required `Controls ...` clause, while `Revenue Strategy` contains `Controls ...` but omits `Weakness:`.
- Nemotron remains a hard blocker. `history/0/88_identify_potential_levers/outputs.jsonl:1` shows all five plans failing with `Could not extract json string from output`, exactly the same failure family seen in `history/0/81_identify_potential_levers/outputs.jsonl:1`.
- Haiku still overshoots the desired depth by a wide margin. Its after-run average consequence length was `886.1` characters versus the baseline training average of `279.5`, so the PR fixed reliability, not verbosity.

## Positive Things

- The specific PR target was real and is now gone. Before the PR, haiku lost `20250329_gta_game` to `List should have at most 7 items after validation, not 8` in `history/0/87_identify_potential_levers/outputs.jsonl:2`; after the PR, haiku completed all 5 plans in `history/0/94_identify_potential_levers/outputs.jsonl:1`.
- Schema-related operational waste dropped to zero. Before: `2` validation-related plan failures, including `1` explicit `too_long` failure. After: `0` validation-related failures and `0` `too_long` failures.
- The PR recovered useful content rather than just changing logging. The after set captured `514` merged levers versus `497` before, a net gain of `17` levers with the same number of total plan attempts.
- Cross-call duplication remained low and improved slightly after the PR (`13` duplicate raw lever names before vs `10` after), which suggests the extra recovered responses were not merely more repeated content.
- Compared with the baseline training data, the current runs are much better at domain-specific naming. Baseline GTA levers include generic names like `Technological Integration Strategy`, `World Design Strategy`, `Monetization Strategy`, and `Risk Mitigation Strategy` in `baseline/train/20250329_gta_game/002-10-potential_levers.json:4`, `baseline/train/20250329_gta_game/002-10-potential_levers.json:26`, `baseline/train/20250329_gta_game/002-10-potential_levers.json:37`, and `baseline/train/20250329_gta_game/002-10-potential_levers.json:48`, while run 94 GTA levers use more project-anchored names such as `Narrative Scope and Story Architecture`, `Procedural Generation Depth vs. Hand-Crafted Fidelity`, and `Multiplayer Architecture and Revenue Model` in `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4`, `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:15`, and `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:26`.
- Template leakage stayed effectively zero in the experiment runs: I found no bracket placeholders and no forbidden option prefixes like `Option A:` / `Choice 1:` in either the before or after groups.

## Comparison

### Against baseline training data

- Baseline is stricter on count discipline: every baseline raw file is exactly `5,5,5` levers per response, while the current after group contains three responses above 7.
- Baseline is shorter and more repetitive. Across all 5 training plans, baseline yields `75` total levers but only `52` unique normalized names (`0.693` uniqueness ratio), with repeated labels inside the same merged outputs such as `Technological Adaptation Strategy` appearing three times in the silo baseline output.
- The current prompt family produces substantially more diverse naming: the after group yields `514` merged levers with `513` unique normalized names (`0.998` uniqueness ratio). This is a real improvement in diversity, though it also means merged outputs are much larger than baseline.
- Baseline is materially more concise: baseline averages `279.5` chars for consequences and `150.2` chars per option, while the after group averages `414.1` chars for consequences and `135.6` chars per option. So the current prompt buys specificity mostly through longer causal chains, not longer options.

### Before vs after (same prompt family, PR in between)

- The after group is **operationally cleaner on schema handling** but **not cleaner overall**. Validation failures disappeared, but unrelated failures (timeouts and JSON extraction failures) kept the aggregate success rate flat.
- The biggest paired win is haiku: `4/5` successful plans before → `5/5` after, and `84` merged levers before → `106` after.
- The biggest paired loss is llama: `5/5` successful plans before → `4/5` after, plus new over-generation and malformed outputs. This is not evidence that the PR broke llama, but it does show that removing the hard cap exposes prompt-noncompliant outputs that were previously impossible to pass through schema validation.
- GPT-5-nano, Qwen3, and GPT-4o-mini are essentially neutral across the PR boundary: same success counts, similar output lengths, and no new contract failures.

## Quantitative Metrics

### Aggregate comparison

Note: `002-10-potential_levers.json` is the merged multi-call output, so the `5 to 7 levers` rule is measured on raw per-response counts from `002-9-potential_levers_raw.json`, not on the merged final file.

| Set | Successful plans | Total plans | Total merged levers | Unique normalized names | Uniqueness ratio | Avg name chars | Avg consequence chars | Avg review chars | Avg option chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline train | 5 | 5 | 75 | 52 | 0.693 | 27.7 | 279.5 | 152.3 | 150.2 |
| Before (81–87) | 28 | 35 | 497 | 495 | 0.996 | 37.3 | 411.6 | 181.6 | 131.4 |
| After (88–94) | 28 | 35 | 514 | 513 | 0.998 | 38.3 | 414.1 | 188.8 | 135.6 |

### Constraint and leakage metrics

| Set | Missing final outputs | Validation-related plan errors | `too_long` plan errors | Raw responses `<5` levers | Raw responses `>7` levers | Levers with wrong option count | Missing `Controls` in review | Missing `Weakness:` in review | Placeholder leakage | Forbidden option prefixes | Cross-call duplicate raw names |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline train | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 22 |
| Before (81–87) | 7 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 |
| After (88–94) | 7 | 0 | 0 | 0 | 3 | 3 | 4 | 3 | 0 | 0 | 10 |

### Current-run detail

| Run | Model | Successful plans | Merged levers | Uniqueness ratio | Avg consequence chars | Avg review chars | Raw responses `>7` | Wrong option count | Review missing `Controls` | Review missing `Weakness:` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 88 | `openrouter-nvidia-nemotron-3-nano-30b-a3b` | 0/5 | 0 | 0.000 | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| 89 | `ollama-llama3.1` | 4/5 | 71 | 1.000 | 162.9 | 146.9 | 2 | 3 | 4 | 3 |
| 90 | `openrouter-openai-gpt-oss-20b` | 4/5 | 72 | 1.000 | 288.0 | 123.7 | 0 | 0 | 0 | 0 |
| 91 | `openai-gpt-5-nano` | 5/5 | 90 | 1.000 | 389.5 | 164.7 | 0 | 0 | 0 | 0 |
| 92 | `openrouter-qwen3-30b-a3b` | 5/5 | 78 | 1.000 | 362.6 | 136.1 | 0 | 0 | 0 | 0 |
| 93 | `openrouter-openai-gpt-4o-mini` | 5/5 | 97 | 1.000 | 240.3 | 157.9 | 0 | 0 | 0 | 0 |
| 94 | `anthropic-claude-haiku-4-5-pinned` | 5/5 | 106 | 1.000 | 886.1 | 348.6 | 1 | 0 | 0 | 0 |

## Evidence Notes

- Prompt contract: `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:4` explicitly requires `5 to 7 levers per response`, and `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:5` requires exactly `3` options per lever.
- Targeted before-PR failure: `history/0/87_identify_potential_levers/outputs.jsonl:2` records haiku failing `20250329_gta_game` with `List should have at most 7 items after validation, not 8`.
- Targeted after-PR recovery: `history/0/94_identify_potential_levers/outputs.jsonl:2` shows `20250329_gta_game` succeeding, and the rest of `history/0/94_identify_potential_levers/outputs.jsonl` is also fully `ok`.
- New soft-count overflow after the PR is directly visible in raw artifacts: `history/0/94_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:167` contains a `lever_index: 8`; `history/0/89_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:90` and `history/0/89_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:101` contain `lever_index: 8` and `lever_index: 9` entries.
- Run 89’s structural drift is visible in `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:48`, `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:58`, and `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:68`, where `Music and Score`, `IP Rights and Censorship`, and `Revenue Strategy` each expose the wrong number of options and malformed review fields.
- Persistent unrelated failure family: `history/0/81_identify_potential_levers/outputs.jsonl:1` and `history/0/88_identify_potential_levers/outputs.jsonl:1` both show nemotron failing plans with `Could not extract json string from output`.
- Baseline genericity and duplication are visible in `baseline/train/20250329_gta_game/002-10-potential_levers.json:37`, `baseline/train/20250329_gta_game/002-10-potential_levers.json:48`, `baseline/train/20250321_silo/002-10-potential_levers.json:26`, and `baseline/train/20250321_silo/002-10-potential_levers.json:114`, where names like `Monetization Strategy`, `Risk Mitigation Strategy`, `Technological Adaptation Strategy`, and `Resource Allocation Strategy` recur.

## PR Impact

The PR was supposed to remove a harmful schema hard cap: `DocumentDetails.levers` should no longer reject a response just because a model returns 8 levers, since downstream deduplication can handle overflow.

### Before vs after for the targeted problem

| Metric | Before (81–87) | After (88–94) | Change |
| --- | ---: | ---: | ---: |
| Successful plans | 28/35 | 28/35 | 0 |
| Validation-related plan failures | 2 | 0 | -2 |
| Explicit `too_long` failures | 1 | 0 | -1 |
| Total merged levers captured | 497 | 514 | +17 |
| Unique normalized names | 495 | 513 | +18 |
| Cross-call duplicate raw names | 13 | 10 | -3 |
| Raw responses `>7` levers | 0 | 3 | +3 |
| Avg consequence chars | 411.6 | 414.1 | +2.5 |

### Did the PR fix the intended issue?

Yes. The clearest before/after pair is haiku:

- Before: `history/0/87_identify_potential_levers/outputs.jsonl:2` shows `20250329_gta_game` failing because the model produced 8 levers and hit `type=too_long`.
- After: `history/0/94_identify_potential_levers/outputs.jsonl:2` shows haiku succeeding on `20250329_gta_game`, and `history/0/94_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:167` demonstrates that an 8-lever raw response can now pass through instead of being discarded.

This is exactly what the PR set out to fix.

### Regressions

- The PR did **not** improve overall success rate because other failure families still dominate: nemotron is still 0/5, llama timed out once, and GPT-OSS still had one JSON extraction failure.
- Removing the hard cap predictably exposes prompt noncompliance. After the PR, three raw responses exceeded the soft `5 to 7` target. This is not a reason to revert, but it is a real follow-up item.
- One after-run (89) also shipped malformed levers with 2 options and incomplete review fields. Those issues are not obviously caused by the cap removal, but they show the pipeline still needs stronger post-parse enforcement if model quality varies.

### Verdict

**KEEP**

Reason: the PR removed the exact targeted failure mode (`too_long` / validation discard), recovered previously lost output, and introduced no measurable increase in hard plan failures. Aggregate success stayed flat only because unrelated failure classes remained. The visible downside is soft over-generation (`>7` raw responses), which should be handled with prompt tightening or downstream trimming rather than by restoring the harmful schema cap.

## Questions For Later Synthesis

- Should the prompt be tightened from “5 to 7 levers” to “produce exactly 5, 6, or 7 levers; extras will be discarded” to reduce new post-PR over-generation?
- Should the pipeline validate and repair per-lever contract issues after parse (wrong option count, missing `Controls`, missing `Weakness:`) so that one noisy model does not silently degrade merged quality?
- Is haiku’s extreme verbosity desirable for downstream steps, or does it create unnecessary token bloat without equivalent decision quality gains?
- Should merged-output size itself become a tracked metric, since baseline is always 15 levers while some current runs now reach 21–24 levers per plan?

## Reflect

- **H1**: Add an explicit line to the system prompt saying that each raw response must contain **no more than 7 levers** and that overflow will be discarded. Evidence: run 89 silo raw output contains `lever_index` 8 and 9; run 94 silo raw output contains `lever_index` 8. Expected effect: fewer over-generated raw responses without reintroducing schema-level hard failures.
- **H2**: Add a compactness instruction for consequences and reviews, e.g. “keep each consequence under ~450 characters and each review under ~220 characters.” Evidence: after-run haiku averages `886.1` chars for consequences and `348.6` for reviews, far beyond baseline compactness. Expected effect: preserve richness while lowering token cost and reducing overly essay-like levers.
- **H3**: Strengthen the review-field instruction to require both clauses literally: `Controls ...` **and** `Weakness: ...`. Evidence: run 89 Hong Kong output omitted one or the other multiple times. Expected effect: fewer review-format violations on weaker models.
- **C1**: After parse, clamp any raw response above 7 levers before merge and log an `overflow_count` metric instead of failing the whole call. Evidence: the PR proved that failing hard on 8 levers is worse than keeping the content, but the current pipeline still lets overflow propagate invisibly into larger merged outputs. Expected effect: keep the recovery benefit of the PR while restoring output-size predictability.
- **C2**: Add per-lever post-parse validation/repair for `options == 3` and review subclauses. Evidence: run 89 produced three 2-option levers and malformed reviews in a successful final artifact. Expected effect: prevent low-quality but parseable responses from degrading downstream tasks.
- **C3**: Investigate JSON extraction robustness separately from this PR. Evidence: nemotron stayed 0/5 before and after, and GPT-OSS still had one extraction failure after. Expected effect: a real increase in total plan success, which the PR alone could not deliver.

## Potential Code Changes

- **C1**: Implement a non-failing overflow handler between raw parse and merge: if a response returns 8+ levers, keep the first 7 (or best 7) and record telemetry. This preserves the PR’s benefit while making merged output sizes more stable.
- **C2**: Add a strict-but-local repair pass for each lever item: if options are not length 3 or if review is missing `Controls` / `Weakness:`, either retry that response or drop that lever with a warning. Run 89 is the main motivating artifact.
- **C3**: Instrument failure taxonomy in the runner summary so the analysis loop can separate schema failures, extraction failures, and timeouts without manual log reading.

## Summary

The PR is a real fix for a real bug. It eliminated the specific `max_length=7` schema failure, recovered previously lost haiku output, and reduced validation-related failures from `2` to `0`. It did **not** raise aggregate success because unrelated timeout/extraction failures still dominate some models. The main new issue is soft over-generation in raw responses, which is a follow-up prompt/post-processing problem, not evidence that the removed hard cap should come back.
