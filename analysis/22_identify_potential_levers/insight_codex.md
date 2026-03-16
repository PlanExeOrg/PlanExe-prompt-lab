# Insight Codex

Examined:
- Prompt: `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:1`
- History runs: `history/1/60_identify_potential_levers/` through `history/1/66_identify_potential_levers/`
- Baseline outputs for the same five plans under `baseline/train/`
- PlanExe step and optimization notes: `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:144`

## Rankings

- **A-tier:** run `62`, run `65`. Best balance of grounding, uniqueness, and low fabricated-number leakage. Run `65` is the strongest qualitative exemplar; run `62` is the cleanest length/credibility compromise.
- **B-tier:** run `61`, run `64`. Strong structural compliance and near-baseline length, but review phrasing is highly templated and run `61` still leaks one unsupported percentage claim.
- **C-tier:** run `63`. Compact and mostly clean, but it reintroduces unsupported numeric claims in options.
- **D-tier:** run `60`. The prompt avoids fake percentages here, but output quality is generic and the run relies on partial recovery after `invalid_json`/`timeout` failures.
- **F-tier:** run `66`. Major content-quality regression: precision theater, unsupported percentages, and field-length inflation beyond the baseline warning threshold.

## Negative Things

- **Run `66` regresses hard on content quality.** It violates the prompt's anti-fabrication intent (`prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:7`) with unsupported numeric splits and thresholds such as `60–70% of principal photography`, `40-50% of budget`, `51%/49%` equity, `3–5%` interest, and `estimated 40%` throughput reduction in `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:64`, `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:184`, `history/1/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:63`, `history/1/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:73`, `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:31`.
- **Review formatting misses the stated two-sentence contract in most runs.** The prompt asks for `review_lever` as "two sentences" in `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:19`, but approximate compliance is poor in runs `60`, `61`, `63`, and `64` and only clearly good in run `65`.
- **Run `60` is structurally salvageable but qualitatively weak.** It has partial recovery events in `history/1/60_identify_potential_levers/events.jsonl:3` and `history/1/60_identify_potential_levers/events.jsonl:12`, plus underlying `invalid_json` and `timeout` failures visible only in `history/1/60_identify_potential_levers/outputs/20250321_silo/usage_metrics.jsonl:4` and `history/1/60_identify_potential_levers/outputs/20260311_parasomnia_research_unit/usage_metrics.jsonl:3`. The recovered content also drifts into generic, weakly grounded names like `Forklift Strategy` in `history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:81`.
- **Template leakage is still unresolved.** Baseline reviews are locked into `Controls ... Weakness:` form in `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:11`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:22`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:33`; prompt 6 mostly swaps that for `This lever ...` openings, e.g. `history/1/61_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:11`, `history/1/61_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:22`.
- **Soft 5–7 guidance still gets ignored by some models.** Run `60` had four responses over 7 levers and run `66` had three. This no longer causes schema failure, but it does increase token cost and verbosity.

## Positive Things

- **Prompt 6 is materially better than baseline on fabricated quantification for most models.** Baseline contains many unsupported percentages, e.g. `15%`, `20%`, `30%`, `10%` in `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:5`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:16`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:27`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:38`. Runs `60`, `62`, `64`, and `65` reduce unsupported percentage claims to zero; run `61` has one and run `63` has three.
- **Name uniqueness improves sharply versus baseline.** Baseline has only `52/75` exact-unique names, with obvious duplicates such as `Narrative Innovation Strategy`, `Talent Alignment Strategy`, and `Distribution Architecture Strategy` repeated in `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:4`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:15`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:26`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:114`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:125`, `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:136`. Runs `61`, `62`, `63`, `64`, `65`, and `66` all reach exact uniqueness across final merged levers.
- **No prompt-example placeholders or option-label prefixes leaked into outputs.** Across all seven runs I found zero square-bracket placeholders and zero `Option A` / `Choice 1` prefixes, so the prohibition set in `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:28` is working.
- **The current code aligns well with the no-`max_length` principle in `OPTIMIZE_INSTRUCTIONS`.** `DocumentDetails.levers` has `min_length=5` but no `max_length` in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:149`, so over-generation in runs `60` and `66` does not show up as `LLMChatError` / `ValidationError` drops. That is a real improvement over the failure mode documented in `analysis/AGENTS.md`.
- **Partial recovery works as intended.** The code path in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:299` preserves earlier valid calls instead of discarding everything, and run `60` demonstrates that this keeps outputs usable despite mid-run failures.
- **Run `65` shows the target style is achievable.** `Procurement Language Specificity` is specific, actionable, and numerically restrained in `history/1/65_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`.

## Comparison

- **Baseline is not a quality ceiling.** It is duplicate-heavy and full of unsupported percentages, especially in Hong Kong game outputs (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json:4`). So “matching baseline length” is not enough by itself.
- **Prompt 6 creates two distinct regimes.** Runs `61`–`65` mostly improve credibility over baseline by cutting fabricated numbers while preserving or improving uniqueness. Run `66` breaks that pattern and reintroduces the exact “fabricated numbers + verbose restatement” problem that `analysis/AGENTS.md` warns about.
- **Run `65` is the clearest evidence that the prompt can yield realistic, feasible, actionable levers.** The sovereign-identity outputs stay anchored to procurement, standards, certification, and coalition choices rather than drifting into generic management advice (`history/1/65_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`).
- **Run `60` improves on baseline’s fake percentages but regresses on domain grounding.** `Forklift Strategy` and generic `Stakeholder Engagement` are weaker than baseline’s domain-specific, if over-quantified, lever names in the same plan (`history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:81`, `history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:92`).
- **OPTIMIZE_INSTRUCTIONS alignment is mixed.** The no-hype and no-max-length goals are mostly met, but run `66` still violates the “fabricated numbers” and “realistic, feasible, actionable” intent in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:46` by adding pseudo-precise thresholds and budget splits unsupported by project context.

Per-plan length comparison for the two strongest-looking long-form runs:

| Plan | Run 65 consequence ratio | Run 65 option ratio | Run 65 review ratio | Run 66 consequence ratio | Run 66 option ratio | Run 66 review ratio |
|---|---:|---:|---:|---:|---:|---:|
| 20250321_silo | 1.23 | 1.08 | 1.34 | 1.29 | 1.89 | 2.27 |
| 20250329_gta_game | 1.29 | 1.17 | 1.51 | 1.74 | 2.26 | 1.80 |
| 20260308_sovereign_identity | 1.25 | 1.01 | 1.33 | 2.13 | 2.08 | 2.65 |
| 20260310_hong_kong_game | 1.16 | 0.97 | 1.26 | 2.11 | 1.80 | 2.38 |
| 20260311_parasomnia_research_unit | 1.01 | 0.83 | 1.11 | 1.99 | 1.80 | 2.16 |

Interpretation: run `65` is longer than baseline but stays below the 2× warning threshold. Run `66` trips the warning broadly, especially on `review`, which exceeds 2× baseline in 4 of 5 plans.

## Quantitative Metrics

Uniqueness counts:

| Source | Levers | Unique names | Exact uniqueness | Normalized uniqueness | Raw cross-call duplicate names |
|---|---:|---:|---:|---:|---:|
| baseline | 75 | 52 | 52/75 | 52/75 | n/a |
| 60 | 91 | 90 | 90/91 | 90/91 | 10 |
| 61 | 90 | 90 | 90/90 | 90/90 | 0 |
| 62 | 91 | 91 | 91/91 | 91/91 | 0 |
| 63 | 74 | 74 | 74/74 | 74/74 | 1 |
| 64 | 83 | 83 | 83/83 | 83/83 | 0 |
| 65 | 92 | 92 | 92/92 | 92/92 | 1 |
| 66 | 108 | 108 | 108/108 | 108/108 | 0 |

Note: exact and normalized uniqueness are identical here, so the remaining duplication issue is mostly literal duplicate names, not punctuation/casing variants.

Average field lengths versus baseline:

| Source | Avg consequences chars | Ratio vs baseline | Avg option chars | Ratio vs baseline | Avg review chars | Ratio vs baseline |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 279.5 | 1.00 | 150.2 | 1.00 | 152.3 | 1.00 |
| 60 | 221.6 | 0.79 | 96.2 | 0.64 | 151.2 | 0.99 |
| 61 | 258.1 | 0.92 | 134.7 | 0.90 | 172.2 | 1.13 |
| 62 | 287.9 | 1.03 | 115.4 | 0.77 | 170.8 | 1.12 |
| 63 | 240.0 | 0.86 | 85.8 | 0.57 | 158.4 | 1.04 |
| 64 | 248.9 | 0.89 | 129.2 | 0.86 | 163.2 | 1.07 |
| 65 | 331.3 | 1.19 | 149.4 | 0.99 | 198.6 | 1.30 |
| 66 | 516.7 | 1.85 | 292.5 | 1.95 | 342.7 | 2.25 |

Constraint and recovery metrics:

| Source | Responses >7 levers | Responses <5 levers | Plans with partial recovery | Logged call errors |
|---|---:|---:|---:|---|
| 60 | 4 | 0 | 2 | invalid_json:1, timeout:1 |
| 61 | 0 | 0 | 0 | - |
| 62 | 0 | 0 | 0 | - |
| 63 | 0 | 0 | 0 | - |
| 64 | 0 | 0 | 0 | - |
| 65 | 0 | 0 | 0 | - |
| 66 | 3 | 0 | 0 | - |

Approximate review-format compliance:

| Run | Reviews with <2 periods | Total reviews | Approx. two-sentence compliance |
|---|---:|---:|---:|
| 60 | 91 | 91 | 0/91 |
| 61 | 66 | 90 | 24/90 |
| 62 | 38 | 91 | 53/91 |
| 63 | 57 | 74 | 17/74 |
| 64 | 78 | 83 | 5/83 |
| 65 | 17 | 92 | 75/92 |
| 66 | 39 | 108 | 69/108 |

This is approximate because punctuation can be noisy, but it is directionally useful: the prompt asks for two sentences and many runs still default to one long sentence.

Template leakage / fabricated-quantification metrics:

| Source | Unsupported % claims | Marketing hits | Placeholder hits | Option label prefixes | Reviews starting `This lever` | Unique review openings |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 58 | 4 | 0 | 0 | 0 | 35 |
| 60 | 0 | 2 | 0 | 0 | 91 | 1 |
| 61 | 1 | 0 | 0 | 0 | 90 | 1 |
| 62 | 0 | 0 | 0 | 0 | 82 | 4 |
| 63 | 3 | 0 | 0 | 0 | 74 | 1 |
| 64 | 0 | 3 | 0 | 0 | 83 | 1 |
| 65 | 0 | 0 | 0 | 0 | 92 | 1 |
| 66 | 16 | 1 | 0 | 0 | 106 | 2 |

Important nuance: baseline already has its own review template monoculture (`Controls ... Weakness:`), so prompt 6 does not create templating from scratch; it mostly changes the template family.

## Evidence Notes

- **Prompt-level anchoring is visible.** The prompt gives a single `review_lever` example beginning `This lever governs...` in `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:20`, and the Pydantic field description repeats that example in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:92`. Most runs then begin reviews with `This lever ...`.
- **Run `65` is the best “grounded but not bloated” specimen.** `Procurement Language Specificity` stays specific to procurement language, fallback mechanisms, and audits, with no fabricated percentages in `history/1/65_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`.
- **Run `60` shows the trade-off between resilience and quality.** Partial recovery preserves outputs, but the rescued content contains generic levers like `Forklift Strategy` and `Stakeholder Engagement` in `history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:81`.
- **Run `63` leaks unsupported percentages even though the output is compact.** Examples: `Allocate 70% of resources...`, `Secure 100% government funding...`, and `Expand to 12 suites only after achieving 90% event capture rate` in `history/1/63_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:40` and `history/1/63_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:40`.
- **Run `66` is more “precision theater” than “marketing copy.”** The problem is not hype words so much as unsupported operational exactness: budget splits, posterior thresholds, random-sample percentages, and throughput estimates in `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:27`, `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:31`, `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:40`, `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:64`, `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:184`.
- **Events telemetry is incomplete.** I checked all selected `events.jsonl` files and found no `LLMChatError` or `ValidationError` entries. However, run `60` definitely had failures, visible only in `usage_metrics.jsonl`. That makes schema-vs-model-vs-timeout diagnosis harder than it should be.

## Questions For Later Synthesis

- Should the next iteration optimize around the run `62` / run `65` profile, or harden the prompt specifically against the run `66` failure mode first?
- Is review-field two-sentence compliance worth enforcing in code, or is it better handled as a soft prompt/style objective?
- Should unsupported percentages be treated as a prompt issue or as a post-parse quality gate in code?
- Does run `60` justify any prompt change at all, or is it mostly a model/runtime issue that should be handled through telemetry and recovery rather than wording?
- Is it acceptable that over-generation persists (>7 levers per response) now that the schema no longer hard-fails, or should the pipeline trim extras earlier to save tokens?

## Reflect

- **H1:** Remove the single `This lever governs...` example, or replace it with 2–3 stylistically different examples plus an explicit instruction to vary openings. Evidence: prompt example at `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt:22`, field description at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, and the near-total `This lever ...` takeover in runs `60`–`66`. Expected effect: less review monoculture without sacrificing structural validity.
- **H2:** Strengthen the anti-fabrication wording from “no fabricated percentages” to “do not invent or derive new percentages, thresholds, budget splits, posterior rules, or cost calculations unless the exact figure already appears in the project context.” Evidence: run `66` examples in `history/1/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:63`, `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:184`, `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:31`. Expected effect: reduce the precision-theater failure mode that survives current prompt wording.
- **H3:** Add explicit brevity budgets for `options` and `review_lever` (for example: one sentence per option, <=35 words; review <=2 short sentences). Evidence: run `66` field-length ratios of `1.85x`, `1.95x`, and `2.25x` versus baseline. Expected effect: lower token use and fewer long pseudo-operational tangents.
- **H4:** Rephrase the count instruction to “generate 5 to 7 levers and stop; extras will be discarded” so the model understands that over-generation is not rewarded. Evidence: over-cap responses in runs `60` and `66` despite the current `5 to 7` instruction. Expected effect: fewer 8–15 lever responses and lower cost, with no need to reintroduce a harmful schema `max_length`.

## Potential Code Changes

- **C1:** Add a post-parse quality audit after lever cleaning in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:329` that flags unsupported `%` claims and field-length outliers, then selectively repairs or regenerates only offending levers. Evidence: run `66` passes schema validation but still fails content-quality checks across multiple plans.
- **C2:** Emit per-call failure events into `events.jsonl` from the exception path in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:299`. Evidence: run `60` failures are visible in `usage_metrics.jsonl` but not in `events.jsonl`, making `LLMChatError` / schema-failure analysis unnecessarily brittle.
- **C3:** Add a soft review-shape checker near `check_review_format` in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:127` that repairs one-sentence reviews instead of failing whole calls. Evidence: the prompt asks for two sentences, but many successful outputs still ship one-sentence reviews.
- **C4:** Update `OPTIMIZE_INSTRUCTIONS` in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27` to add a new known problem: **precision theater / example anchoring**. Current known problems cover hype and fabricated numbers, but not the pattern where a model avoids hype words yet produces unsupported pseudo-precise thresholds and clones a single example structure.
- **C5:** Do **not** reintroduce `max_length=7` on `DocumentDetails.levers`. The current evidence supports the existing soft-cap design in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:149`: run `60` and run `66` over-generate, but they do not fail at the schema layer.

## Summary

- Prompt 6 is directionally good: versus baseline it dramatically improves name uniqueness and, in runs `61`–`65`, nearly eliminates unsupported percentage claims.
- The biggest remaining problem is not structural validity; it is **content-quality instability**, especially run `66`'s verbose, pseudo-precise options and reviews.
- The highest-leverage next steps look like: reduce example anchoring, harden against derived numeric claims, and add code-side telemetry/quality audits rather than tightening schema caps.
