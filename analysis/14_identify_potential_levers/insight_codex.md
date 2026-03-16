# Insight Codex

## Rankings

- **Tier A**: `history/1/04_identify_potential_levers`, `history/1/05_identify_potential_levers`, `history/1/07_identify_potential_levers`. These runs are fully successful, keep structural violations near zero, and avoid the severe under-fill seen in the salvaged partial outputs.
- **Tier B**: `history/1/06_identify_potential_levers`, `history/1/08_identify_potential_levers`. Both are fully successful, but `1/06` is shorter/shallow on some consequences and `1/08` is extremely verbose and produces 21+ levers per plan.
- **Tier C**: `history/1/03_identify_potential_levers`, `history/1/02_identify_potential_levers`. These runs are important because they show the PR working, but they still contain one hard failure each and also ship salvaged outputs with only 12 and 7 final levers.

## Negative Things

- First-call failures still kill the whole plan. `history/1/02_identify_potential_levers/events.jsonl` shows `20250321_silo` and `20260308_sovereign_identity` failing on `review_lever` validation, and `history/1/03_identify_potential_levers/events.jsonl` shows `20260310_hong_kong_game` failing on invalid JSON. PR #292 does not help these cases.
- Salvaged outputs are materially thinner than the baseline target. `history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json` contains only 1 response and `002-10-potential_levers.json` contains only 7 levers; `history/1/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json` contains 2 responses and `002-10-potential_levers.json` contains 12 levers.
- The prompt still over-constrains `review_lever` relative to weaker models. The registered prompt at `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt` requires both `Controls ... vs. ...` and `Weakness:` markers; the remaining hard failures are still dominated by that validator.
- Template leakage persists as bracket placeholders in some successful outputs. Example: `history/1/04_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` has reviews like `Controls [Production speed] vs. [City authenticity]` and `Controls [Language accessibility] vs. [Local authenticity]`.
- Some successful outputs still miss the measurable-indicator requirement. Example: `history/1/02_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` lever 1 (`Hong Kong Location Strategy`) says `Immediate: High production costs → Systemic: Limited filming locations due to logistics and permits → Strategic: Reduced creative freedom...` with no numeric indicator.
- The haiku run is operationally improved but bloated. `history/1/08_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` contains 21 levers, and the `Screenplay Adaptation: Twist Subversion vs. Psychological Coherence` entry alone has a 1,273-character consequence and a 437-character review.

## Positive Things

- The after cohort is slightly more reliable than the before cohort: 32/35 successful plans after PR #292 versus 31/35 before, while using the same registered prompt in `analysis/13_identify_potential_levers/meta.json` and `analysis/14_identify_potential_levers/meta.json`.
- The targeted behavior now exists in artifacts, not just in theory. Before this PR, every successful output I checked had 3 stored responses; after the PR there are 2 successful outputs with fewer than 3 responses, which means prior successful calls are now preserved instead of being discarded.
- `history/1/02_identify_potential_levers/outputs/20250329_gta_game/activity_overview.json` records 2 llama calls, while the paired raw file stores only 1 successful response and the final output still ships 7 levers. That is strong evidence of a later-call failure being recovered instead of turning into a total-plan failure.
- `history/1/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json` preserves 2 successful responses and 12 final levers. This is precisely the failure mode PR #292 claimed to fix.
- Structural quality in successful outputs remains strong overall. In the after cohort, every successful lever still has exactly 3 options, and I found zero option-prefix leakage such as `Conservative:` / `Moderate:` / `Radical:` that did appear before.
- Relative to baseline training data, the current prompt produces richer, more domain-specific lever names and deeper consequences/reviews. Example baseline output `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` starts with `Narrative Innovation Strategy`, while `history/1/04_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` starts with the more grounded `Hong Kong Architecture as Narrative Engine` and gives a clearer trade-off narrative.

## Comparison

- **Versus baseline**: baseline outputs are shorter and cleaner on total-count discipline (exactly 15 levers/plan), but they are less specific and often repeat names. Across the 5 baseline plans, only 53 of 75 lever names are unique after normalization; duplicates include repeated `Technological Adaptation Strategy` in `baseline/train/20250321_silo/002-10-potential_levers.json` and repeated `Technical Feasibility Strategy` / `Policy Advocacy Strategy` blocks in `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json`.
- **Versus previous-analysis runs**: before the PR, successful outputs were all full 3-response merges. After the PR, two outputs are clearly partial saves. The trade-off is that completeness drops on those plans, but the system now preserves 19 levers that previously would have been at risk of total loss.
- **Run quality spread**: `1/05` is the cleanest “production-like” run because it stays close to baseline count discipline (15.4 levers/output) without the placeholder leakage seen in `1/04`; `1/04` is richer but still leaks bracket placeholders; `1/08` is fully successful but likely too verbose for downstream compression and review.
- **Failure distribution**: after the PR, remaining hard failures cluster around call-1 schema/JSON problems, not later-call loss. That is a real improvement in failure mode, even though it is not yet a full reliability fix.

## Quantitative Metrics

Method note: exact uniqueness lowercases and strips punctuation from lever names; “semantic” uniqueness additionally removes stopwords. In these runs the two measures did not diverge.

| Cohort | Successful plans | Mean levers / successful output | Exact unique names | Semantic unique names | Partial successful outputs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline (`baseline/train/`) | 5/5 (100.0%) | 15.00 | 53/75 (70.7%) | 53/75 (70.7%) | 0 |
| Before (`history/0/95`-`history/1/01`) | 31/35 (88.6%) | 18.16 | 563/563 (100.0%) | 563/563 (100.0%) | 0 |
| After (`history/1/02`-`history/1/08`) | 32/35 (91.4%) | 17.75 | 568/568 (100.0%) | 568/568 (100.0%) | 2 |

| Cohort | Avg name chars | Avg consequence chars | Avg review chars | Avg option chars |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 27.7 | 279.5 | 152.3 | 150.2 |
| Before | 38.6 | 400.7 | 177.5 | 132.2 |
| After | 36.5 | 403.6 | 183.6 | 132.7 |

| Cohort | Missing measurable consequence | Missing `Immediate/Systemic/Strategic` chain | Option-prefix leakage | Bracket placeholder leakage |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 21/75 (28.0%) | 5/75 (6.7%) | 0/75 (0.0%) | 0/75 (0.0%) |
| Before | 53/563 (9.4%) | 1/563 (0.2%) | 7/563 (1.2%) | 7/563 (1.2%) |
| After | 46/568 (8.1%) | 0/568 (0.0%) | 0/568 (0.0%) | 6/568 (1.1%) |

| Run | Model | Successes | Errors | Mean levers / success | Partial saves | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `history/1/02_identify_potential_levers` | `ollama-llama3.1` | 3 | 2 | 14.33 | 1 | Salvages `gta_game`, but still loses 2 plans to `review_lever` failures |
| `history/1/03_identify_potential_levers` | `openrouter-openai-gpt-oss-20b` | 4 | 1 | 16.75 | 1 | Salvages `parasomnia`, but still has 1 invalid-JSON failure |
| `history/1/04_identify_potential_levers` | `openai-gpt-5-nano` | 5 | 0 | 18.00 | 0 | Rich output, but 6 bracket-placeholder leaks |
| `history/1/05_identify_potential_levers` | `openrouter-qwen3-30b-a3b` | 5 | 0 | 15.40 | 0 | Cleanest count discipline, closest to baseline volume |
| `history/1/06_identify_potential_levers` | `openrouter-openai-gpt-4o-mini` | 5 | 0 | 18.40 | 0 | Fully successful, but 3 consequences miss numeric indicators |
| `history/1/07_identify_potential_levers` | `openrouter-gemini-2.0-flash-001` | 5 | 0 | 18.40 | 0 | Strong structure, but 7 consequences still omit numeric indicators |
| `history/1/08_identify_potential_levers` | `anthropic-claude-haiku-4-5-pinned` | 5 | 0 | 21.40 | 0 | Best success rate improvement, but very verbose and oversized |

## Evidence Notes

- PR target behavior is visible in `history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`, `history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, and `history/1/02_identify_potential_levers/outputs/20250329_gta_game/activity_overview.json`.
- A second recovered case is visible in `history/1/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json` and `history/1/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.
- Remaining hard failures are auditable in `history/1/02_identify_potential_levers/events.jsonl` and `history/1/03_identify_potential_levers/events.jsonl`.
- Before-run option-label leakage is easy to confirm in `history/0/95_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, where options begin with `Conservative:`, `Moderate:`, and `Radical:`.
- After-run bracket leakage is easy to confirm in `history/1/04_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.
- Baseline duplication is visible in `baseline/train/20250321_silo/002-10-potential_levers.json` and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json`.

## PR Impact

PR #292 (`Recover partial results when a lever generation call fails`) was supposed to stop the 3-call loop from throwing away earlier successful lever batches when call 2 or call 3 fails. The prompt is unchanged between `analysis/13_identify_potential_levers/meta.json` and `analysis/14_identify_potential_levers/meta.json`, so the before/after comparison is reasonably clean.

| Metric | Before (`history/0/95`-`history/1/01`) | After (`history/1/02`-`history/1/08`) | Change |
| --- | ---: | ---: | ---: |
| Successful plans | 31/35 (88.6%) | 32/35 (91.4%) | +1 successful plan |
| Top-level plan errors | 4 | 3 | -1 |
| Successful outputs with `< 3` stored responses | 0 | 2 | +2 |
| Levers preserved in partial successes | 0 | 19 | +19 |
| `review_lever` hard failures | 2 | 2 | No change |
| Invalid-JSON hard failures | 1 | 1 | No change |
| Option-count hard failures | 1 | 0 | -1 |
| Mean levers / successful output | 18.16 | 17.75 | -0.41 |

Interpretation:

- **Did it fix the targeted issue?** Yes, for the narrow scenario it targeted. `history/1/02_identify_potential_levers/outputs/20250329_gta_game/` and `history/1/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/` are concrete examples where partial prior responses survive into a successful final artifact. I found no such successful partial outputs in the previous-analysis run set.
- **Did it improve overall reliability?** Slightly. The success rate moved from 31/35 to 32/35 and the total hard-error count dropped by one. That is real but modest.
- **Did it introduce regressions?** No clear new regression is visible in the artifacts. The lower mean lever count is explained by the intended behavior: salvaged outputs with 7 and 12 levers replace what would previously have been total failure. The main unresolved weakness is not new: first-call schema/JSON failures still abort the plan.

**Verdict: KEEP.** The PR does the thing it claims to do, the preserved outputs are materially useful, and I do not see evidence that it makes successful outputs worse beyond the expected “partial is smaller than full” trade-off.

## Questions For Later Synthesis

- Should downstream steps treat 7-lever and 12-lever salvaged outputs as acceptable, or should they trigger a low-cost repair/retry path?
- Should salvaged outputs be marked explicitly in `outputs.jsonl` or `002-9-potential_levers_raw.json` so later analysis can distinguish “full 3-call success” from “partial salvage”? 
- Is the remaining `review_lever` validator too brittle for weaker models, especially given that the prompt encourages a two-part structure but not a single exact sentence format?
- Should total lever count be constrained more tightly to stay closer to the 15-lever baseline and reduce downstream deduplication/compression work?

## Reflect

- **H1**: Rewrite the prompt’s `review_lever` instruction to show one exact combined string, not two separate bullets. Evidence: the remaining hard failures in `history/1/02_identify_potential_levers/events.jsonl` repeatedly alternate between outputs containing only `Controls ...` or only `Weakness: ...`. Expected effect: fewer call-1 schema failures on weaker models.
- **H2**: Change the prompt from `5 to 7 levers per response` to `exactly 5 levers per response` unless there is a deliberate reason to over-produce. Evidence: baseline training files consistently ship 15 levers/plan, while many current runs produce 18-21 levers and `history/1/08_identify_potential_levers` reaches 21.4 levers/output on average. Expected effect: tighter total volume, lower deduplication burden, and less downstream verbosity.

## Potential Code Changes

- **C1**: Add an explicit “salvaged partial result” marker to `outputs.jsonl` and/or `002-9-potential_levers_raw.json`, including how many calls succeeded and which call failed. Evidence: the only way to prove PR #292 worked was by manually correlating `activity_overview.json`, raw-response counts, and final outputs. Expected effect: easier monitoring, better QA, and clearer downstream policy decisions.
- **C2**: Add a lightweight repair pass for `review_lever` before hard validation, for cases where the content clearly contains both ideas but not the exact expected formatting. Evidence: the remaining top-level failures are still dominated by `review_lever` formatting in `history/1/02_identify_potential_levers/events.jsonl`. Expected effect: convert some current hard failures into valid call-1 outputs without weakening downstream schema guarantees too much.
- **C3**: Add an optional post-merge cap or score-based pruning step so 18-21 lever outputs can be trimmed toward the baseline 15 when needed. Evidence: `history/1/08_identify_potential_levers/outputs/*/002-10-potential_levers.json` consistently overshoots baseline volume, even when quality is decent. Expected effect: more stable downstream workload and easier human review.

## Summary

PR #292 is a real improvement. The artifacts show two successful partial recoveries that did not exist in the previous-analysis cohort, and overall reliability nudges upward from 31/35 to 32/35 successful plans. The main remaining problem is still call-1 brittleness around `review_lever` and occasional invalid JSON, not the later-call discard bug the PR set out to fix.
