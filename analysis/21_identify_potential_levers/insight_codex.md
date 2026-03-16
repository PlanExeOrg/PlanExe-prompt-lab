# Insight Codex

## Negative Things

- Unsupported percentage claims are still present after the PR. Using the source plan text as the grounding check, I count 19 unsupported percentage tokens across 13 of 626 final levers in runs 53–59, only a small improvement from 22 tokens across 15 of 634 levers in runs 46–52.
- The remaining fabrication is not confined to one domain. It still appears in silo, Hong Kong film, and parasomnia outputs. Examples: `history/1/54_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` invents “70% of the food required” even though `baseline/train/20250321_silo/001-2-plan.txt` contains no percentages; `history/1/54_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` invents 30% / 20% / 15% budget splits even though `baseline/train/20260310_hong_kong_game/001-2-plan.txt` supplies only the total HK$470m budget, not allocation percentages; `history/1/53_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` invents a 90% event-capture threshold while the plan only gives `70–80%` and `20%` in `baseline/train/20260311_parasomnia_research_unit/001-2-plan.txt`.
- A new short-option relapse appears in the after batch: 21 options under 5 words after vs. 0 before and 0 in the baseline training outputs. The concentration is almost entirely in `history/1/53_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, which contains option strings like “Implement multi-layered structural reinforcement” and “Deploy AI-driven monitoring”. These are slogans/labels, not fully worked strategic approaches.
- Silent partial-call loss persists and slightly worsens. Three after-run raw files contain only 2 responses instead of 3: `history/1/54_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`, `history/1/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json`, and `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`. I checked `history/1/46_identify_potential_levers/events.jsonl` through `history/1/59_identify_potential_levers/events.jsonl`; none contain `LLMChatError`, so the missing call is still not observable from the event logs.
- `OPTIMIZE_INSTRUCTIONS` says levers must be realistic, feasible, actionable, must avoid fabricated numbers, hype, vague aspirations, and English-only validation. The PR branch aligns with that intent in `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27`, but current outputs still violate the fabricated-number rule and the “not a slogan” rule.

## Positive Things

- Structural compliance stays strong. Across runs 53–59 I found 0 wrong option-count levers, 0 option-prefix labels, 0 bracket placeholders, and 0 within-file duplicate lever names.
- Length discipline remains close to the baseline training data. Average consequence / option / review lengths are 39.31 / 18.61 / 23.10 words after the PR, only 1.17× / 0.98× / 1.13× the baseline averages. None crosses the 2× warning threshold.
- Marketing-copy leakage is low and slightly improved: 7 hits after vs. 8 before. Residual examples are isolated, such as “cutting-edge technology” in `history/1/56_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.
- Global naming diversity is still good. Exact duplicate names across the whole batch drop from 15 to 12 despite repeating the same five plans seven times.
- The PR wording itself is directionally correct. The registered prompt already bans fabricated numbers at `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:8` and `:32`; the PR branch sensibly repeats that rule in the follow-up-call prompt at `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272`.

## Comparison

- Versus the previous batch, the after batch is a small credibility improvement, not a fix. Unsupported percentage tokens drop 22 → 19, but the problem still survives in 13 levers and one after-run outlier (`history/1/58_identify_potential_levers/...`) is as bad as the worst before-run outlier.
- Versus the baseline training data, both before and after batches are much more disciplined on fabrication. The baseline set contains 58 unsupported percentage tokens across just 75 levers, with obvious invented numbers in files like `baseline/train/20250321_silo/002-10-potential_levers.json`. So baseline is useful as a length anchor, but not as a credibility gold standard.
- The PR seems to help some plans and not others. GTA improves materially (7 unsupported tokens before → 3 after), parasomnia improves slightly (7 → 5), Hong Kong stays flat (5 → 5), and silo gets worse (3 → 6).
- The new short-option relapse weakens alignment with `OPTIMIZE_INSTRUCTIONS` even though verbosity stays controlled overall. This is a different failure mode than unsupported percentages, but it matters because downstream scenario selection prefers decisive-looking options even when they are too shallow to schedule or resource.

## Quantitative Metrics

### Batch Overview

| Metric | Before (46–52) | After (53–59) | Baseline train | Notes |
|---|---:|---:|---:|---|
| Final levers | 634 | 626 | 75 | 35 plan outputs in each before/after batch |
| Global unique names | 619 | 614 | 52 | Exact-match uniqueness across the whole batch |
| Global duplicate names | 15 | 12 | 23 | Lower is better |
| Unsupported percentage tokens | 22 | 19 | 58 | Counted only when the exact % token is absent from the source plan text |
| Levers with unsupported % | 15 (2.4%) | 13 (2.1%) | 54 (72.0%) | Token support checked against `001-2-plan.txt` |
| Short options `<5` words | 0 | 21 | 0 | New after-batch regression |
| Wrong option-count levers | 0 | 0 | 0 | Exact-3-option contract holds |
| Option-prefix labels | 0 | 0 | 0 | No `Option A:` / `Choice 1:` leakage |
| Placeholder / bracket leakage | 0 | 0 | 0 | No `[...]` template residue |
| Marketing-keyword hits | 8 | 7 | 3 | `game-changing`, `cutting-edge`, etc. |
| Plans with only 2 raw responses | 2 | 3 | n/a | Silent partial-call issue persists |
| `LLMChatError` events | 0 | 0 | n/a | None logged in any audited `events.jsonl` |

### Average Field Lengths

| Field (words) | Before | After | Baseline | Before / Baseline | After / Baseline |
|---|---:|---:|---:|---:|---:|
| Consequences | 39.13 | 39.31 | 33.67 | 1.16× | 1.17× |
| Options | 18.92 | 18.61 | 19.03 | 0.99× | 0.98× |
| Review | 22.81 | 23.10 | 20.45 | 1.12× | 1.13× |

### Plan-Level Unsupported Percentage Impact

| Plan | Before unsupported % tokens / levers | After unsupported % tokens / levers | Change |
|---|---:|---:|---|
| `20250321_silo` | 3 / 3 levers | 6 / 4 levers | Worse |
| `20250329_gta_game` | 7 / 3 levers | 3 / 1 lever | Better |
| `20260308_sovereign_identity` | 0 / 0 levers | 0 / 0 levers | Flat |
| `20260310_hong_kong_game` | 5 / 3 levers | 5 / 3 levers | Flat |
| `20260311_parasomnia_research_unit` | 7 / 6 levers | 5 / 5 levers | Slightly better |

### Notable Outlier Runs

| Run | Signal | Why it matters |
|---|---|---|
| `history/1/51_identify_potential_levers` | 12 unsupported % tokens | Worst before-run fabrication cluster |
| `history/1/53_identify_potential_levers` | 20 short options `<5` words | New shallow-option relapse after the PR |
| `history/1/58_identify_potential_levers` | 13 unsupported % tokens | Worst after-run fabrication cluster |
| `history/1/59_identify_potential_levers` | 2 plans with only 2 raw responses | Silent observability gap still open |

## Evidence Notes

- The registered prompt already contains the anti-fabrication policy: `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:8` says to use numbers only when the project context provides evidence, and `:32` bans fabricated statistics or percentages.
- The PR branch adds the reminder exactly where the PR description says: `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-275`. The mainline file still lacks that follow-up reminder at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:233-235`.
- `OPTIMIZE_INSTRUCTIONS` in the PR branch explicitly warns against fabricated numbers, hype language, vague aspirations, and English-only validation in `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27-68`.
- Unsupported after-run examples are auditable against the plan text:
  - `history/1/54_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:106` says “70% of the food required”, but `baseline/train/20250321_silo/001-2-plan.txt` contains no percentages.
  - `history/1/54_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:40-42` invents 30% / 20% / 15% budget allocations, while `baseline/train/20260310_hong_kong_game/001-2-plan.txt:6` supplies only the total budget and timeline.
  - `history/1/53_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:40` says “90% event capture rates”, while `baseline/train/20260311_parasomnia_research_unit/001-2-plan.txt:4` supplies `70–80%` and `20%`, not 90%.
- The new shallow-option issue is easy to verify in `history/1/53_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:117` and nearby entries, which contain multiple 3–4 word options.
- Baseline credibility is poor on this metric. `baseline/train/20250321_silo/002-10-potential_levers.json:16`, `:27`, `:49`, and later entries include invented 20–40% claims even though the source plan has none.

## PR Impact

The PR was supposed to reduce unsupported quantitative fabrication in calls 2 and 3 by repeating the anti-fabrication rule after the long “do not reuse these names” blacklist.

| Metric | Before (runs 46–52) | After (runs 53–59) | Change |
|---|---:|---:|---|
| Unsupported percentage tokens | 22 | 19 | -3 |
| Levers with unsupported % | 15 / 634 (2.4%) | 13 / 626 (2.1%) | Slight improvement |
| Worst single-run unsupported % total | 12 (`run 51`) | 13 (`run 58`) | Worse outlier |
| Short options `<5` words | 0 | 21 | Regression |
| Plans with only 2 raw responses | 2 | 3 | Regression |
| Marketing-keyword hits | 8 | 7 | Slight improvement |
| Avg option length vs baseline | 0.99× | 0.98× | Flat |

My read: the PR helps a little, but it does not fix the targeted issue in a robust way.

- The anti-fabrication rate improves only marginally.
- The improvement is mixed by plan instead of broad-based.
- A new shallow-option outlier appears in the after batch.
- Silent partial-call loss remains unsolved and slightly worse.

The targeted issue therefore remains open. The after batch still contains unsupported budget splits and invented thresholds, especially in `history/1/58_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

**Verdict: CONDITIONAL.** I would keep the PR only if it is immediately followed by a stronger grounding mechanism (prompt or code) for unsupported numeric claims. The one-line reminder is low-risk and directionally correct, but it is not a sufficient standalone fix.

## Questions For Later Synthesis

- Are the 21 short options in run 53 coming from call 1, or did calls 2/3 ignore the existing “complete strategic sentence” reminder as well?
- Should unsupported-number detection treat a model’s conversion of a supplied range (for example `70–80%`) into a new threshold (`80%` or `90%`) as fabrication? I think yes, but it should be made explicit in the metric spec.
- Is run 58 a prompt-saturation case tied to long budget-heavy plans, or just ordinary model variance? The fabrication pattern there looks like “numerically partition the budget” behavior.
- Should the optimizer stop using the baseline training outputs as a credibility reference for this step, given that the baseline itself contains many fabricated percentages?

## Reflect

- **H1** — Add the anti-fabrication reminder to call 1 as well, not just calls 2/3. Evidence: the system prompt already bans fabricated numbers, but unsupported percentages still survive and the after batch shows a fresh silo relapse. Expected effect: reduce first-call leakage and make the rule feel primary rather than secondary.
- **H2** — Add an explicit negative example about budget partitioning and threshold invention: “If the plan gives a total budget or a range, do not invent allocation percentages or a stricter threshold unless that exact number appears in the document.” Evidence: Hong Kong outputs repeatedly invent 30/20/15 budget splits from a real HK$470m total, and parasomnia outputs invent 80–90% thresholds from a supplied `70–80%` range. Expected effect: suppress the specific failure pattern that the generic reminder did not eliminate.
- **H3** — Add a short anti-slogan reminder near the option rule, or restate the full-sentence rule in the call-1 prompt path. Evidence: 21 sub-5-word options appear only after the PR batch, almost all in one run. Expected effect: preserve the current good verbosity discipline without letting terse labels slip through.
- The strongest new pattern I would add to `OPTIMIZE_INSTRUCTIONS` is not “fabricated numbers” in general — that is already listed — but **derived numeric partitioning**: when a real total budget, headcount, or range is present, models invent unsupported percentages, splits, or thresholds that look plausible because they are mathematically related to a real number in the source text.

## Potential Code Changes

- **C1** — Add a grounding audit for numeric claims. For each lever field, extract percentage tokens and compare them against the source plan text. At minimum emit telemetry; ideally reject or downgrade outputs with unsupported percentages. Evidence: this audit is easy to compute from `002-10-potential_levers.json` plus `001-2-plan.txt`, and it isolates the real problem better than raw `%` counting.
- **C2** — Add an actionable-option validator or warning for options below a minimum word count or without an action verb. Evidence: `history/1/53_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains many 3–4 word options even though the quality goal is “complete strategic approaches”.
- **C3** — Record `completed_calls` / partial-call metadata and log why a call disappeared. Evidence: after the PR there are still 3 raw files with only 2 responses, and the audited `events.jsonl` files do not expose the cause.
- **C4** — Add a regression test around the follow-up prompt assembly so the branch-only reminder at `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-275` cannot silently disappear when prompt text is refactored.

## Summary

The PR is well-motivated and slightly helpful, but not decisive. Unsupported percentage claims fall only from 22 to 19, remain visible in 13 levers, and one after-run still shows a large fabrication cluster. Structural quality stays high and verbosity stays close to baseline, but the after batch introduces a new short-option relapse and does not resolve silent partial-call loss. My recommendation is **CONDITIONAL**: keep the PR only as a small incremental improvement, not as the full fix for anti-fabrication.
