# Insight Codex

Examined `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt`, the prior prompt `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`, all five baseline training plans under `baseline/train/`, the previous-analysis runs `history/1/24_identify_potential_levers` through `history/1/30_identify_potential_levers`, and the current runs `history/1/31_identify_potential_levers` through `history/1/37_identify_potential_levers`.

## Rankings

- **Best-balanced after runs:** run 32 (`openrouter-openai-gpt-oss-20b`) ≈ run 34 (`openrouter-qwen3-30b-a3b`) ≈ run 35 (`openrouter-openai-gpt-4o-mini`). They stay close to baseline lengths, remove chain leakage entirely, and avoid the worst placeholder/number problems.
- **Biggest remaining after-run issues:** run 33 (`openai-gpt-5-nano`) for bracket-template review leakage; run 37 (`anthropic-claude-haiku-4-5-pinned`) for long fields plus unsupported numeric claims in options.
- **Largest before→after improvement by matched model:** run 30 → run 37 on verbosity and fabricated quantification, and run 27 → run 34 on field bleed.

## Negative Things

- **Bracket-template leakage got worse in one model family.** Prompt 4 bans bracket-wrapped templates at `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:30`, but run 33 still copies bracketed review text such as `Controls [platform resilience through platform-neutral governance] vs. [vendor lock-in risk and procurement inertia]...` in `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:77`. Pooled placeholder count rises from 12 before to 36 after, entirely concentrated in run 33.
- **Summary exactness is still poor.** The `summary` instruction is unchanged in prompt 4 (`prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:23`-`:25`), and after-runs still achieve only `11/104` exact matches. All 11 exact matches come from run 31; runs 32–37 contribute `0` exact summaries. Example non-exact summary: `history/1/32_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json:73`.
- **Unsupported numeric claims still survive in options.** The PR sharply reduced them, but did not eliminate them. Run 37 still invents percentage splits and performance deltas such as `40%` travel-time reduction and `40/40/20` financing splits in `history/1/37_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:118` and `history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:216`-`:218`. Run 34 also invents silo resource splits like `60%`, `75%`, and `300%` in `history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:18`-`:19` and `:150`.
- **Marketing language remains low-frequency but not gone.** Prompt 4 explicitly forbids it at `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:32`, yet run 35 still says `cutting-edge` in `history/1/35_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:62`, and run 36 still says `breakthrough` / `cutting-edge` in `history/1/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:49`, `:95`, and `:162`.
- **Run 37 is still close to the old verbosity trap.** It no longer exceeds the 2× baseline warning threshold, but it remains the longest after-run at 495.7-char consequences, 276.1-char options, and 291.9-char reviews — `1.77×`, `1.84×`, and `1.92×` baseline respectively.

## Positive Things

- **The PR’s main target was fixed: chain-format leakage disappeared.** Prompt 3 explicitly required `Immediate → Systemic → Strategic` at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:8`-`:10`; prompt 4 removes that requirement and replaces it with a shorter grounded consequence instruction at `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:8`. The result is stark: before-runs had `614/614` chained consequences; after-runs had `0/637`.
- **Unsupported percentage claims collapsed.** Using an exact-token heuristic that checks each lever’s `%` claims against the plan brief in `baseline/train/<plan>/001-2-plan.txt` and `baseline/train/<plan>/005-2-project_plan.md`, unsupported percentage claims fall from `864` before to `25` after. Baseline itself is worse than the after set on this measure (`58` unsupported claims across only 75 levers).
- **Consequences moved back toward baseline length.** Pooled average consequence length drops from `417.2` chars before to `309.1` after, much closer to the baseline average of `279.5`. The best concise after examples look materially cleaner than the verbose prompt-3 outputs; compare `history/1/32_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` with `history/1/30_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:5`.
- **Field bleed disappeared.** Before-runs had 66 cases where `consequences` also contained the `Controls ... Weakness:` review string, e.g. `history/1/27_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` duplicating the review at `:11`. I found `0` such cases in the after-runs.
- **Review diversity improved.** Exact review uniqueness improves from `593/614` before to `636/637` after. The old repeated-review problem in run 26 is gone.
- **Operationally, the after set is cleaner.** There are final outputs for all `35/35` plan-run combinations after the PR, versus `34/35` before. The logs also contain `0` `LLMChatError` entries after, versus six logged failures before (`history/1/25_identify_potential_levers/events.jsonl:7` plus the transient create-stage alias failures in `history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5`).

## Comparison

- **Against baseline:** the baseline training data is not a clean gold standard for credibility. It still contains the old chain format and unsupported percentages, e.g. `history`-style text like `Immediate: ... 15% increase ... Strategic:` in `baseline/train/20250321_silo/002-10-potential_levers.json:5`. The after-runs are therefore better than baseline on chain leakage and unsupported quantification, while staying reasonably close to baseline on field lengths.
- **Against prompt-3 runs:** prompt 3 forced every successful model into the same structural pattern: chained consequences, pervasive quantification, and sometimes catastrophic verbosity. The clearest pre-PR example is run 30, where a single consequence stretches into a dense three-stage paragraph with invented engagement deltas in `history/1/30_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:5` and `:16`.
- **Across the after-runs:** run 32, run 34, and run 35 are the best evidence that the simplification helped without causing a length explosion. Run 33 shows a new failure mode — copying bracket placeholders from the review template. Run 37 shows that high-capability models still need an explicit guard against numeric invention in options, even after the consequence rule was simplified.
- **On the removed conservative→moderate→radical template:** I found no literal option-label leakage (`Conservative:`, `Moderate:`, `Radical:`) in either before or after outputs, so the benefit of deleting that clause is not visible as a string-level cleanup. The measurable wins come from reduced numeric fabrication and shorter consequences, not from label removal.

## Quantitative Metrics

### Length and Uniqueness (pooled)

| Corpus | Final successful plans | Final levers | Unique names | Unique reviews | Avg consequence chars | Consequence vs baseline | Avg option chars | Option vs baseline | Avg review chars | Review vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline training data | 5 | 75 | 52 | 75 | 279.5 | 1.00× | 150.2 | 1.00× | 152.3 | 1.00× |
| Before PR (runs 24–30) | 34 | 614 | 608 | 593 | 417.2 | 1.49× | 133.7 | 0.89× | 173.8 | 1.14× |
| After PR (runs 31–37) | 35 | 637 | 628 | 636 | 309.1 | 1.11× | 124.8 | 0.83× | 174.0 | 1.14× |

### Constraint / Template / Credibility Metrics (pooled)

| Corpus | Chain-format consequences | Unsupported `%` claims* | Marketing hits | Placeholder count | Field bleed | Review exact-format | Summary exact-format |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline training data | 75 / 75 | 58 | 4 | 0 | 0 | 75 / 75 (100.0%) | n/a |
| Before PR (runs 24–30) | 614 / 614 | 864 | 16 | 12 | 66 | 573 / 614 (93.3%) | 8 / 102 (7.8%) |
| After PR (runs 31–37) | 0 / 637 | 25 | 7 | 36 | 0 | 575 / 637 (90.3%) | 11 / 104 (10.6%) |

\* `Unsupported % claims` is a heuristic count: each percentage token in lever fields is checked against the plan’s source brief in `baseline/train/<plan>/001-2-plan.txt` and `baseline/train/<plan>/005-2-project_plan.md`. This correctly preserves grounded claims like the parasomnia plan’s `20%` ceiling (`baseline/train/20260311_parasomnia_research_unit/001-2-plan.txt:4` and `history/1/37_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:5`), but it should still be read as an audit heuristic, not a proof of fabrication.

### After-Run Breakdown

| Run | Model | Levers | Avg consequence chars | Avg option chars | Avg review chars | Unsupported `%` claims | Placeholder count | Review exact-format | Summary exact-format |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 31 | `ollama-llama3.1` | 98 | 228.8 | 86.7 | 171.8 | 1 | 0 | 91 / 98 | 11 / 15 |
| 32 | `openrouter-openai-gpt-oss-20b` | 84 | 274.5 | 91.0 | 132.0 | 1 | 0 | 84 / 84 | 0 / 14 |
| 33 | `openai-gpt-5-nano` | 90 | 289.4 | 108.6 | 147.6 | 0 | 36 | 39 / 90 | 0 / 15 |
| 34 | `openrouter-qwen3-30b-a3b` | 80 | 245.7 | 72.3 | 143.5 | 4 | 0 | 80 / 80 | 0 / 15 |
| 35 | `openrouter-openai-gpt-4o-mini` | 83 | 239.6 | 112.9 | 149.2 | 0 | 0 | 83 / 83 | 0 / 15 |
| 36 | `openrouter-gemini-2.0-flash-001` | 90 | 336.5 | 83.0 | 145.1 | 0 | 0 | 89 / 90 | 0 / 15 |
| 37 | `anthropic-claude-haiku-4-5-pinned` | 112 | 495.7 | 276.1 | 291.9 | 19 | 0 | 109 / 112 | 0 / 15 |

## Evidence Notes

- Prompt 3 is the direct source of the old failure modes: forced chain and measurable outcomes at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:8`-`:10`, conservative→moderate→radical at `:13`-`:16`, and forced emerging-tech radical option at `:38`-`:40`.
- Prompt 4 explicitly removes those pressures and bans fabricated stats / marketing at `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:8`, `:30`-`:32`, and `:35`-`:37`.
- Baseline still contains the old structural pattern: `baseline/train/20250321_silo/002-10-potential_levers.json:5` includes both the chain syntax and an unsupported `15%` claim.
- The worst prompt-3 verbosity example I found is `history/1/30_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:5`, followed by similarly over-quantified text at `:16`.
- Field bleed is obvious in run 27: `history/1/27_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` embeds the same `Controls ... Weakness:` text repeated in the review at `:11`.
- Prompt 4 can produce crisp non-chain consequences when the model follows it: `history/1/32_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5` and `history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.
- Placeholder regression is visible in run 33 reviews: `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:77`, `:88`, and `:99`.
- Marketing leakage after the PR is low-volume but concrete: `history/1/35_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:62` and `history/1/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:95`.
- Some remaining numeric claims are clearly unsupported, but not all numbers are fabricated. The parasomnia `20%` ceiling is grounded in the project brief at `baseline/train/20260311_parasomnia_research_unit/001-2-plan.txt:4` and echoed in `history/1/37_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:5`; by contrast, the Hong Kong financing splits at `history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:216`-`:218` are not supported by the brief I inspected.
- The only pre-PR schema/parse loss that actually removed a final plan is the JSON failure in `history/1/25_identify_potential_levers/events.jsonl:7`. The run-29 failures in `history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5` are real logged `LLM chat interaction failed` entries, but they are create-stage alias/config problems rather than prompt-content problems.

## PR Impact

The PR was supposed to restore content quality by removing the mandatory `Immediate → Systemic → Strategic` chain, mandatory quantification, the conservative→moderate→radical progression template, and the forced emerging-tech radical option, while adding explicit bans on fabricated stats and marketing language.

### Before vs After

| Metric | Before (runs 24–30) | After (runs 31–37) | Change |
| --- | --- | --- | --- |
| Final successful plans | 34 / 35 | 35 / 35 | +1 plan |
| Avg consequence chars | 417.2 (1.49× baseline) | 309.1 (1.11× baseline) | -108.1 chars |
| Chain-format consequences | 614 / 614 (100.0%) | 0 / 637 (0.0%) | Eliminated |
| Unsupported `%` claims* | 864 | 25 | -839 (-97.1%) |
| Field bleed (`Controls ... Weakness:` inside `consequences`) | 66 / 614 | 0 / 637 | Eliminated |
| Review uniqueness | 593 / 614 (96.6%) | 636 / 637 (99.8%) | +3.2 pts |
| Placeholder count | 12 | 36 | +24 (worse) |
| Review exact-format compliance | 573 / 614 (93.3%) | 575 / 637 (90.3%) | -3.0 pts |
| Summary exact-format compliance | 8 / 102 (7.8%) | 11 / 104 (10.6%) | +2.8 pts |
| Logged `LLMChatError` entries | 6 | 0 | -6 |

### Did the PR fix the targeted issue?

Yes, on the main issue. The direct failure modes named in the PR — chain formatting and fabricated quantification — improved massively and measurably:

- The chain requirement disappears completely after the prompt change (`614/614` before → `0/637` after).
- Unsupported percentage claims collapse by about `97%` on the exact-token audit heuristic (`864` → `25`).
- Consequence length returns much closer to baseline (`417.2` → `309.1` chars), and the extreme verbosity seen in run 30 does not recur.

These are not marginal gains. They are visible across all matched model pairs, including the hardest cases: run 30 → run 37 drops from `255` percentage claims to `21`, and run 27 → run 34 drops field bleed from `66` to `0`.

### Regressions

There are regressions, but they are narrower than the gains:

- Run 33 introduces a new bracket-template review failure mode, pushing placeholder count from `12` before to `36` after.
- Review exact-format compliance slips from `93.3%` to `90.3%`, again mostly because of run 33.
- Summary formatting remains broadly unsolved.
- Run 37 still invents unsupported numeric splits in options.

These regressions matter, but they do not outweigh the removal of the PR’s primary content-quality regressions. Also, the logged reliability improvement should be interpreted carefully: some of the before-side failures were prompt-independent config issues (`history/1/29_identify_potential_levers/outputs.jsonl:1`-`:5`). The content-quality improvement remains strong even if those are ignored.

### Verdict

**KEEP.** The PR produces a significant, measurable improvement on the exact problems it set out to fix: consequence chains are gone, unsupported quantification is dramatically reduced, consequence length is back near baseline, and the worst field-bleed artifacts disappear. Follow-up work is still needed for bracket placeholders, summary exactness, and residual numeric invention in option fields, but the PR is a net quality win.

## Questions For Later Synthesis

- Should the `review_lever` template stop showing square brackets entirely, since run 33 copies them literally despite the prompt-level prohibition?
- Should the no-fabricated-statistics rule be broadened to say **nowhere in consequences, options, or review**, not just implied by the consequence guidance?
- Is summary exactness important enough to justify either a much harder prompt rule or a tiny post-processing repair?
- Do we want a lightweight post-generation lint for marketing words and unsupported percentages, especially for verbose models like Haiku?

## Reflect

- **H1:** Replace the bracketed `review_lever` template with a natural-language literal example and an explicit line saying `Do not copy square brackets into the output.` Evidence: run 33 leaks 36 bracket placeholders into final reviews despite prompt 4’s ban at `prompts/identify_potential_levers/prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt:30`. Expected effect: recover review exact-format compliance without reintroducing verbosity.
- **H2:** Add a field-global prohibition: `Do not invent percentages, market shares, budget splits, capacity margins, or cost deltas anywhere in consequences, options, or review unless the exact number appears in the project context.` Evidence: most remaining unsupported claims now sit in option fields, especially run 37 (`history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:216`-`:218`). Expected effect: reduce the residual 25 unsupported `%` claims without hurting the chain-format win.
- **H3:** Make `summary` a one-line hard requirement: `summary must be exactly one sentence starting with Add ' and contain no preamble.` Evidence: after-runs still hit only `11/104` exact summaries, with runs 32–37 at zero exact matches. Expected effect: improve summary consistency with minimal impact on content quality.
- **H4:** Add a soft brevity target for options and reviews on verbose models, e.g. `each option should fit in one sentence` and `review should stay under ~160 characters unless the project context requires more.` Evidence: run 37 remains near the 2× baseline warning threshold on both options and reviews. Expected effect: keep the content-quality win while preventing a smaller relapse into verbosity.

## Potential Code Changes

- **C1:** Add a post-parse lint that rejects or repairs bracket placeholders in any final lever field. Evidence: run 33 produces final reviews like `Controls [centralization vs decentralization]...` in `history/1/33_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:77`. Expected effect: catch a high-salience quality failure that the prompt alone does not currently prevent.
- **C2:** Add a context-aware unsupported-number detector as runner telemetry or a retry trigger. The source brief already exists locally in `baseline/train/<plan>/001-2-plan.txt` and `005-2-project_plan.md`; that is enough to compare claimed percentages against known numeric context. Expected effect: automatically surface or suppress the residual unsupported `%` claims that still slip through in runs 31, 32, 34, and 37.
- **C3:** Record quality telemetry per run: chain-count, placeholder-count, unsupported-number-count, marketing hits, review exact-format rate, and summary exact-format rate. Evidence: those metrics explain the PR outcome much better than raw success rate. Expected effect: make later PR evaluations faster and less dependent on manual forensics.

## Summary

- Prompt 4 is a real improvement. It removes the exact structural behaviors that were damaging credibility: chained consequences, forced quantification, and the worst verbosity spikes.
- The pooled after-set is much closer to baseline on consequence length and much cleaner than both baseline and prompt-3 runs on unsupported percentages.
- The main remaining problems are narrower: bracket-template reviews in run 33, poor summary exactness almost everywhere, and residual numeric invention in some option fields, especially run 37.
- My verdict is **KEEP**.
