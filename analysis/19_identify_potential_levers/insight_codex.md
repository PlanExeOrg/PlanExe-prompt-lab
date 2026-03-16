# Insight Codex

## Rankings
- Strongest current runs: `history/1/40_identify_potential_levers` (`openai-gpt-5-nano`), `history/1/44_identify_potential_levers` (`openrouter-openai-gpt-oss-20b`), and `history/1/38_identify_potential_levers` (`openrouter-qwen3-30b-a3b`). All three have zero bracket leakage, zero bad summaries, zero raw duplicate names, and little-to-no marketing or fabricated percentages.
- Middle tier: `history/1/42_identify_potential_levers` and `history/1/41_identify_potential_levers`. Structure is clean, but marketing language still appears, especially in `history/1/41_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:62`.
- Weakest current runs: `history/1/43_identify_potential_levers` and `history/1/45_identify_potential_levers`. `43` still fabricates numeric thresholds such as `70%` in review text at `history/1/43_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:22`; `45` repeats raw lever names heavily before deduplication, e.g. `Regulatory Framework Update` at `history/1/45_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:41`, `history/1/45_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:135`, and `history/1/45_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:196`.

## Negative Things
- Residual fabricated quantification remains concentrated in `history/1/43_identify_potential_levers`. The parasomnia output still invents thresholds and schedule deltas like `70%` and `4–8 weeks` without evidence from the project brief at `history/1/43_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:22` and `history/1/43_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:29`.
- Marketing-copy leakage is lower than before, but not gone. Examples include `cutting-edge graphics` in `history/1/41_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:62` and `Partner with a major tech company for cutting-edge AI integration` in `history/1/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:106`.
- Raw cross-call duplication got worse overall: 10 duplicate raw lever names across runs `31–37` versus 21 across runs `38,40–45`. The regression is almost entirely `ollama-llama3.1`; dedup cleans the final file, but repeated names still waste call budget and reduce candidate diversity.
- The sibling `PlanExe` checkout available to this analysis still shows the old placeholder-heavy descriptions and English-only validator in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:54`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113`, and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:179`. I also could not find an `OPTIMIZE_INSTRUCTIONS` constant anywhere under `../PlanExe` during repo-wide search, so I could not literally perform that part of the requested check.

## Positive Things
- The PR’s main prompt-level goal clearly helped: bracket/template leakage disappeared from the raw responses. Before the PR, `openai-gpt-5-nano` emitted bracketed reviews like `Controls [platform resilience through platform-neutral governance] vs. [vendor lock-in risk and procurement inertia]...` at `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:87`; after the PR, the analogous field is clean prose at `history/1/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:76`.
- Summary alignment improved dramatically. Before the PR, many runs prefaced the `Add ...` instruction with extra commentary, e.g. `Summary: ... Add ...` at `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:73` and a bracketed placeholder at `history/1/31_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json:261`. After the PR, summaries are consistently one-sentence additions such as `Add an external audit...` at `history/1/40_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json:73` and `Add 'develop a technical benchmarking framework...'` at `history/1/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:62`.
- Final-output uniqueness remains excellent. Baseline training data averages only 10.6 unique lever names out of 15 per plan, while both before and after runs average fully unique final lever names per output after deduplication.
- Length discipline is much healthier than the earlier prompt-optimizer regressions documented in `analysis/AGENTS.md`: current runs stay near baseline lengths instead of exploding past 2×.
- I checked all fourteen `events.jsonl` files for runs `31–37` and `38,40–45` and found zero `LLMChatError` entries, so there is no evidence here of schema-level retries or discarded full responses.

## Comparison
- Against baseline training data in `baseline/train/*/002-10-potential_levers.json`, the current runs are close in consequence and review length: 1.03× baseline for consequences and 1.08× for review, with options shorter than baseline at 0.78×. No field crosses the 2× warning threshold.
- Against the previous analysis slice (`history/1/31_identify_potential_levers` through `history/1/37_identify_potential_levers`), the current slice fixes the two directly observable prompt-contract problems: bracket leakage drops from 37 raw hits to 0, and bad summaries drop from 90/105 summaries to 0/105.
- The before/after change is not just structural. The new prompt explicitly forbids square brackets, fabricated percentages, and marketing language at `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:20`, `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:23`, `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:31`, and `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:33`, and the outputs move in that direction.
- The non-English validator part of the PR is not well exercised by this training slice. All five plans appear English-language, so the removal of the English-only `Controls` / `Weakness:` checks cannot be confirmed from these runs alone.

## Quantitative Metrics

### Uniqueness and structure

| Metric | Baseline (`baseline/train`) | Before (`31–37`) | After (`38,40–45`) |
| --- | ---: | ---: | ---: |
| Plans / outputs examined | 5 | 35 | 35 |
| Avg final levers per output | 15.0 | 18.2 | 18.0 |
| Avg unique final names per output | 10.6 | 18.2 | 18.0 |
| Avg final duplicate names per output | 4.4 | 0.0 | 0.0 |
| Total raw duplicate names | n/a | 10 | 21 |
| Option-count violations | n/a | 0 | 0 |
| Option-prefix violations | n/a | 0 | 0 |
| `LLMChatError` entries in `events.jsonl` | n/a | 0 | 0 |

### Average field lengths vs baseline

| Field | Baseline avg chars | Before avg chars | Before ratio | After avg chars | After ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Consequences | 279.5 | 302.5 | 1.08× | 287.1 | 1.03× |
| Review | 152.3 | 169.0 | 1.11× | 164.9 | 1.08× |
| Option | 150.2 | 119.1 | 0.79× | 116.7 | 0.78× |

### Template leakage and quality signals

| Metric | Before (`31–37`) | After (`38,40–45`) | Change |
| --- | ---: | ---: | ---: |
| Raw bracket hits in response fields | 37 | 0 | -37 |
| Bad summaries (`not startswith "Add "`) | 90 / 105 | 0 / 105 | -90 |
| Raw review-format violations | 0 | 0 | 0 |
| Fabricated percentage claims in final outputs | 27 | 20 | -7 |
| Marketing-language hits in final outputs | 23 | 18 | -5 |
| Triad-template term hits (`conservative/moderate/radical`) | 7 | 5 | -2 |

### Current-run breakdown

| Run | Model | Raw dup names | Bracket hits | Bad summaries | % claims | Marketing hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `38` | `qwen3-30b-a3b` | 0 | 0 | 0 | 1 | 0 |
| `40` | `gpt-5-nano` | 0 | 0 | 0 | 0 | 0 |
| `41` | `gpt-4o-mini` | 0 | 0 | 0 | 0 | 9 |
| `42` | `gemini-2.0-flash-001` | 0 | 0 | 0 | 0 | 3 |
| `43` | `claude-haiku-4-5` | 0 | 0 | 0 | 18 | 1 |
| `44` | `gpt-oss-20b` | 0 | 0 | 0 | 0 | 0 |
| `45` | `ollama-llama3.1` | 21 | 0 | 0 | 1 | 5 |

## Evidence Notes
- Old placeholder leakage is directly visible in `history/1/33_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:87` and `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:87`.
- Old summary mismatch is visible in `history/1/33_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:73` and `history/1/31_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json:261`.
- New clean summary/review behavior is visible in `history/1/40_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json:15`, `history/1/40_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json:73`, `history/1/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:76`, and `history/1/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:62`.
- The new registered prompt’s anti-placeholder / anti-marketing / anti-fabrication language appears at `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:20`, `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:23`, `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:25`, and `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt:31`.
- The current `PlanExe` checkout still shows the stale source-side contract at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:54`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113`, and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:179`.

## PR Impact

The PR was supposed to do three things: remove bracket placeholders from review guidance, remove fragile English-only validation, and align `summary` with the prompt-4 style one-sentence concrete addition.

| Metric | Before (`31–37`) | After (`38,40–45`) | Change |
| --- | ---: | ---: | ---: |
| Raw bracket hits in response fields | 37 | 0 | strong improvement |
| Bad summaries (`not startswith "Add "`) | 90 / 105 | 0 / 105 | strong improvement |
| Avg consequence length | 302.5 | 287.1 | modest improvement |
| Avg review length | 169.0 | 164.9 | slight improvement |
| Fabricated % claims | 27 | 20 | modest improvement |
| Marketing-language hits | 23 | 18 | modest improvement |
| Raw duplicate names | 10 | 21 | regression |
| `LLMChatError` entries | 0 | 0 | neutral |

- The placeholder-removal part of the PR worked. The pre-PR slice still contains bracketed response text, while the post-PR slice contains none.
- The summary-alignment part also worked and is the clearest win. Pre-PR, 90 of 105 summaries contained extra commentary before the requested addition; post-PR, every summary starts with `Add ...`.
- The English-only validator change is not falsified, but it is also not proven by this dataset because there are no obvious non-English plan prompts in the training slice.
- The main regression is unrelated to the PR’s stated goal: `ollama-llama3.1` now repeats raw lever names more often before deduplication. That looks like a separate diversity/control issue in multi-call generation, not a failure of the placeholder/summary fix.

**Verdict: KEEP.** The PR produces a significant measurable improvement on two of its three explicit targets, does not create schema failures, and nudges content length and fabricated-claim counts in the right direction. The one visible regression is real but orthogonal.

## Questions For Later Synthesis
- Is the raw-duplication regression in `ollama-llama3.1` worth a code fix, or is downstream dedup sufficient given that final files stay unique?
- Should the prompt add an explicit negative example for unsupported numeric thresholds, since `claude-haiku-4-5` still invents percentages despite the prohibition?
- Is the local `../PlanExe` checkout out of sync with the experiments? The run artifacts show the PR effect, but the source tree visible to analysis still contains the old placeholder-heavy validator contract.
- Do we want to broaden the anti-marketing ban beyond a few phrases to also discourage generic names like `Innovative Revenue Strategies`?

## Reflect
- H1: Keep the concrete `review_lever` and `summary` examples exactly in the registered prompt. Evidence: the before/after delta on bracket leakage and summary format is too large to be noise. Expected effect: preserve the 0/105 bad-summary rate and 0 bracket-leakage rate.
- H2: Add one explicit negative example for fabricated numeric thresholds in `review` and `consequences`. Evidence: `history/1/43_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:22` still invents a `70%` threshold. Expected effect: reduce the remaining 20 percentage-claim hits, especially in Haiku.
- H3: Add a brief ban on generic `innovative/strategic/cutting-edge` naming in lever titles and option phrasing unless the source prompt itself uses that language. Evidence: `history/1/41_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:15` and `history/1/41_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:62`. Expected effect: lower the remaining 18 marketing hits without hurting structure.

## Potential Code Changes
- C1: Bring `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` into sync with the prompt-lab prompt. The source-side `review_lever` description and validator still require placeholder-styled English markers at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:54` and `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, and the `summary` description is still `100 words` at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113`. Expected effect: make the behavior robust outside prompt-lab registration and remove the i18n risk the PR targeted.
- C2: Add the missing `OPTIMIZE_INSTRUCTIONS` constant, or restore it if this checkout is stale. It should explicitly encode the observed quality goals: no bracket placeholders, no English-only validators, no fabricated percentages, no marketing-copy naming, and no cross-call name repetition. Expected effect: future prompt iterations have a stable, auditable policy target.
- C3: Strengthen multi-call anti-duplication. The current prompt for later calls passes prior names inside brackets at `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:233`, yet `ollama-llama3.1` still repeats names heavily in raw output. Expected effect: better diversity and less wasted token budget before deduplication.

## Summary
- This PR materially improves the observable prompt/output contract: bracket leakage falls from 37 to 0, bad summaries from 90/105 to 0/105, and field lengths stay close to baseline rather than drifting verbose.
- Remaining issues are narrower: Haiku still fabricates some numeric thresholds, 4o-mini and llama still use some marketing language, and llama repeats raw lever names before deduplication.
- The visible run artifacts support keeping the PR, while follow-up work should focus on source-code/prompt alignment and raw multi-call diversity.
