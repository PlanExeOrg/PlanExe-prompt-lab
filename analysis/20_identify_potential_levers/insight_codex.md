# Insight Codex

I examined the registered prompt at `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt`, the baseline training outputs in `baseline/train/*/002-10-potential_levers.json`, the previous-run history outputs in `history/1/38_identify_potential_levers/` through `history/1/45_identify_potential_levers/`, the current-run outputs in `history/1/46_identify_potential_levers/` through `history/1/52_identify_potential_levers/`, and the current PR worktree file `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`.

## Negative Things

- Unsupported quantification persists after the PR. The after runs contain 24 percentage claims across 634 levers, up slightly from 20 across 630 levers before the PR. Examples: `history/1/46_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` adds `"Allocate 70% of agricultural output..."`, and `history/1/51_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` adds `"reducing asset production by approximately 30%"` and `"24+ months"` in `Open-World Scale and Regional Depth`.
- Marketing-copy language is low but not gone. After runs still contain 5 levers using banned words such as `cutting-edge`, despite the prohibition in `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt`.
- Claude Haiku remains the closest model to the baseline-length warning threshold. In the after runs its average option length is 1.85× baseline and review length is 1.89× baseline, so it is not yet a >2× regression, but it is the main verbosity watchlist item.
- The PR does not improve call completion reliability. Raw artifacts still show fewer than 3 returned calls in some cases: previous runs had 34 third-call responses across 35 plan outputs, while current runs have 33. I found no corresponding `LLMChatError` entries in any `history/1/*_identify_potential_levers/events.jsonl`, so the missing calls likely come from a different control-flow path.

## Positive Things

- The targeted defect is fixed. Before the PR, short-label options leaked into final outputs only in the llama run: 47 short options across `history/1/45_identify_potential_levers/outputs/*/002-10-potential_levers.json`. After the PR, there are 0 short options across all current outputs.
- The fix works at the source, not just after deduplication. In `history/1/45_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, call 3 emits `Ecological Integration` options as bare labels (`Bioregenerative Systems`, `Closed-Loop Ecology`, `Synthetic Ecosystems`). In `history/1/52_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, call 3 emits full strategic sentences for the same stage of generation.
- Option completeness improves overall, not just for llama. Across all models, raw call-2 options rise from 16.6 average words before the PR to 20.9 after, and raw call-3 options rise from 15.6 to 21.2 average words.
- Final outputs stay structurally clean. Before and after both have 0 option-count violations, 0 prefix-label violations, and 0 placeholder leaks across all final `002-10-potential_levers.json` artifacts.
- Current runs are materially better than baseline training data on duplication and template leakage. Baseline outputs average only 10.6 unique lever names per 15-lever output and use the `Immediate: → Systemic: → Strategic:` consequence template in 70 of 75 levers; both previous and current history batches are 100% exact-unique within each output and show 0 chain-template leakage.

## Comparison

The baseline training set is not a gold standard on credibility: it contains repeated lever names, 58 percentage claims across 75 levers, and 70 chain-template consequences, as seen in files such as `baseline/train/20250321_silo/002-10-potential_levers.json` and `baseline/train/20250329_gta_game/002-10-potential_levers.json`. Against that baseline, both previous and current runs are cleaner on uniqueness and template leakage.

Relative to the immediately previous runs, the current runs improve the exact issue this PR targeted: follow-up-call option quality. The biggest measurable gain is in `ollama-llama3.1`, where raw call-3 average option length rises from 6.2 words to 13.1 words and the short-label rate falls from 47/102 to 0/69. Other models were already at 0 short labels before the PR, but most of them still produce longer and more complete call-2/3 options after the reminder.

The field-length profile remains healthy against baseline. Overall after-run averages are 297.8 chars for consequences, 142.5 for options, and 173.2 for reviews, versus baseline 279.5 / 150.2 / 152.3. That is 1.07× / 0.95× / 1.14× baseline, so there is no >2× warning-sign regression. The PR increases option length toward baseline rather than beyond it.

The remaining mismatch with `OPTIMIZE_INSTRUCTIONS` is credibility, not sentence completeness. The PR branch code at `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` explicitly warns against fabricated numbers, hype language, and vague aspirations. The current outputs now align better on vague aspirations, but they still violate the fabricated-number rule often enough to merit a follow-up.

## Quantitative Metrics

### Overall output metrics

| Metric | Baseline train (5 outputs) | Before runs 38/40-45 (35 outputs) | After runs 46-52 (35 outputs) |
| --- | ---: | ---: | ---: |
| Avg levers per output | 15.0 | 18.0 | 18.1 |
| Exact unique names per output | 10.6 / 15.0 (70.7%) | 18.0 / 18.0 (100%) | 18.1 / 18.1 (100%) |
| Avg consequence chars | 279.5 | 295.8 | 297.8 |
| Avg option chars | 150.2 | 121.8 | 142.5 |
| Avg review chars | 152.3 | 169.0 | 173.2 |
| Short options | 0 / 225 (0.0%) | 47 / 1890 (2.5%) | 0 / 1902 (0.0%) |
| Percentage claims | 58 | 20 | 24 |
| Marketing-copy levers | 3 | 6 | 5 |
| Chain-template consequences | 70 / 75 (93.3%) | 0 / 630 (0.0%) | 0 / 634 (0.0%) |

### Constraint violations and template leakage

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Final options with wrong count | 0 | 0 | 0 |
| Final short-label options (≤3 words) | 47 | 0 | -47 |
| Final prefixed options (`Option A`, `Choice 1`, etc.) | 0 | 0 | 0 |
| Final placeholder leaks (`[` / `]`) | 0 | 0 | 0 |
| Raw call-2 short-label options | 0 / 648 (0.0%) | 0 / 663 (0.0%) | neutral |
| Raw call-3 short-label options | 47 / 648 (7.3%) | 0 / 615 (0.0%) | fixed |

### Length ratios vs baseline

| Field | Before / Baseline | After / Baseline | Warning threshold |
| --- | ---: | ---: | --- |
| Consequences | 1.06× | 1.07× | >2.0× |
| Options | 0.81× | 0.95× | >2.0× |
| Reviews | 1.11× | 1.14× | >2.0× |

### Raw follow-up-call option quality by model

| Model | Before call-3 short options | After call-3 short options | Before call-3 avg words | After call-3 avg words |
| --- | ---: | ---: | ---: | ---: |
| `anthropic-claude-haiku-4-5-pinned` | 0 / 108 | 0 / 105 | 34.9 | 38.6 |
| `ollama-llama3.1` | 47 / 102 | 0 / 69 | 6.2 | 13.1 |
| `openai-gpt-5-nano` | 0 / 90 | 0 / 90 | 14.5 | 16.4 |
| `openrouter-gemini-2.0-flash-001` | 0 / 93 | 0 / 93 | 11.3 | 21.4 |
| `openrouter-openai-gpt-4o-mini` | 0 / 87 | 0 / 84 | 15.6 | 17.6 |
| `openrouter-openai-gpt-oss-20b` | 0 / 93 | 0 / 93 | 14.3 | 23.1 |
| `openrouter-qwen3-30b-a3b` | 0 / 75 | 0 / 81 | 8.6 | 11.8 |

### Event-log audit

| Check | Before | After |
| --- | ---: | ---: |
| `LLMChatError` entries in `events.jsonl` | 0 | 0 |
| Pydantic/schema failures observed in event logs | 0 | 0 |

## Evidence Notes

- `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt` requires options to be “complete strategic approaches” and forbids generic labels, fabricated percentages, and marketing language.
- `history/1/45_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows the pre-PR failure mode directly in call 3: `Ecological Integration` has three label-only options.
- `history/1/52_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows the post-PR correction directly in call 3: `Ecological Balance` has full-sentence options with clear actions.
- `history/1/46_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` still violates the anti-fabrication rule via `"Allocate 70% of agricultural output..."`.
- `history/1/51_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` still violates the anti-fabrication rule via `"approximately 30%"` and `"24+ months"` in `Open-World Scale and Regional Depth`.
- `baseline/train/20250321_silo/002-10-potential_levers.json` and `baseline/train/20250329_gta_game/002-10-potential_levers.json` demonstrate that the baseline itself contains the old chain-template consequence style, percentage fabrication, and `cutting-edge` language.
- `../PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` contains the follow-up-call reminder: `Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.` It also contains `OPTIMIZE_INSTRUCTIONS` warning against fabricated numbers, hype language, vague aspirations, and English-only validation.

## PR Impact

The PR was supposed to fix a very specific failure mode: llama call-2/3 responses drifting from full-sentence options into 2-3 word labels when the blacklist of already-used names got longer.

### Before vs after on the targeted issue

| Metric | Before (38/40-45) | After (46-52) | Change |
| --- | ---: | ---: | ---: |
| Final short-label options across all models | 47 / 1890 (2.5%) | 0 / 1902 (0.0%) | -47 |
| Final short-label options in `ollama-llama3.1` | 47 / 246 (19.1%) | 0 / 273 (0.0%) | fixed |
| Raw call-3 short-label options in `ollama-llama3.1` | 47 / 102 (46.1%) | 0 / 69 (0.0%) | fixed at source |
| Raw call-3 avg option words in `ollama-llama3.1` | 6.2 | 13.1 | +6.9 |
| Overall raw call-2 avg option words | 16.6 | 20.9 | +4.3 |
| Overall raw call-3 avg option words | 15.6 | 21.2 | +5.6 |
| Avg final option chars | 121.8 | 142.5 | +20.7 |
| `LLMChatError` entries | 0 | 0 | neutral |
| Percentage claims | 20 | 24 | +4 |

The fix clearly addresses the intended problem. The before artifact `history/1/45_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows the exact label-collapse behavior described in the PR. The after artifact `history/1/52_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows that the same third call now returns sentence-level options. That improvement also propagates to the final output set: there are no short options anywhere in runs 46-52.

I do not see a meaningful regression tied to this PR. The only negative movement is a small increase in unsupported quantitative claims (20 → 24), but that issue predates the PR, is explicitly banned by both the registered prompt and `OPTIMIZE_INSTRUCTIONS`, and is far smaller in scope than the removed short-label failure. Uniqueness, option-count compliance, placeholder leakage, and event-log stability all remain flat or improve.

**Verdict: KEEP**

## Questions For Later Synthesis

- Why do 2 current outputs still end up with fewer than 3 raw calls returned even though no `LLMChatError` appears in `events.jsonl`?
- Should the anti-fabrication instruction be repeated in the same call-2/3 reminder block that fixed sentence completeness?
- Should Haiku’s near-threshold verbosity be handled with prompt wording, or is it acceptable because it still stays below the 2× baseline warning line?
- Do downstream steps actually benefit from the broader call-2/3 option-length increase seen in Gemini and GPT-OSS, or is that just more words?

## Reflect

- **H1**: Keep the explicit call-2/3 sentence reminder. Evidence: llama call-3 short labels fall from 47/102 to 0/69, and no final short options survive in the after runs. Expected effect: future multi-call models with blacklist-attention decay should stay at or near 0% short-label options.
- **H2**: Add one adjacent sentence to the call-2/3 reminder forbidding unsupported percentages and date-like effort claims. Evidence: the after runs still contain 24 unsupported percentage claims, with concrete examples in `history/1/46_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `history/1/51_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`. Expected effect: reduce fabricated-number leakage without sacrificing option completeness.
- **H3**: Add a note to `OPTIMIZE_INSTRUCTIONS` about blacklist-driven attention decay in follow-up prompts. Evidence: the failure occurs specifically in later calls after the `Do NOT reuse these names` block becomes long; the PR fixes it by restating the most important quality rule immediately after that block. Expected effect: future prompt edits will preserve critical quality rules in follow-up calls.

## Potential Code Changes

- **C1**: Add a soft post-generation quality check for options before final merge: minimum word count plus a simple action-verb heuristic, with rewrite-or-drop behavior instead of silent acceptance. Evidence: pre-PR llama short labels survive from raw call 3 into final outputs in `history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `history/1/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`. Expected effect: future regressions are caught even if prompt wording drifts.
- **C2**: Add telemetry or a warning-level validator for fabricated quantification (`%`, explicit cost deltas, unsupported duration claims) in consequences/options/review. Evidence: `OPTIMIZE_INSTRUCTIONS` forbids invented numbers, yet after-run outputs still emit them. Expected effect: make credibility regressions measurable before they reach downstream planning steps.
- **C3**: Investigate why some outputs return only 2 raw calls despite fixed `total_calls = 3` and no `LLMChatError` in the corresponding `events.jsonl`. Expected effect: clarify whether there is a non-exception early exit, timeout, or serialization issue affecting completeness.

## Summary

The PR does what it claims: it removes the llama follow-up-call collapse into 2-3 word option labels, and the effect is visible both in raw call-3 artifacts and in the final merged outputs. The broader output profile remains healthy against baseline on uniqueness, template leakage, and field lengths. The main unresolved issue is credibility drift from unsupported numbers, not option sentence quality. On the evidence in runs 38/40-45 versus 46-52, this PR is a clear **KEEP**.
