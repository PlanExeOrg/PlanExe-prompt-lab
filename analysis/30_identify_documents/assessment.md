# Assessment: cap DocumentDetails list fields to reduce IdentifyDocumentsTask output size

PR #342 — first `identify_documents` iteration. No prior analysis exists, so this
assessment compares against the baseline training data in `baseline/train/`.

## Issue Resolution

**What the PR was supposed to fix:** JSON truncation timeouts caused by unbounded
list fields in `DocumentDetails`. The model fills all four list fields without
constraint, producing output that truncates at ~260 lines.

**Is the issue resolved?** Partially. For 3 of 7 models (llama3.1, gpt-5-nano,
gemini-flash) the fix works — all 5 plans succeed. But for haiku (1/5), gpt-oss-20b
(4/5), qwen3-30b (4/5), and gpt-4o-mini (4/5), failures persist or are newly introduced:

- **Truncation still occurs** for haiku (3 plans), gpt-oss-20b (1 plan), qwen3-30b (1 plan)
  — the item count cap doesn't help when each item has 500-700 char descriptions
- **New `too_long` validation failures** for gpt-4o-mini (7 items vs max 6) and haiku
  (12 items vs max 6) — the hard cap rejects entire responses

**Residual symptoms:** The root cause (per-item verbosity) is unaddressed. Capping item
count reduces total output size but doesn't prevent individual items from being verbose
enough to cause truncation.

## Quality Comparison (vs Baseline)

| Metric | Baseline | PR #342 (best model) | PR #342 (avg) | Verdict |
|--------|----------|---------------------|---------------|---------|
| Success rate | 5/5 (100%) | 5/5 gemini/llama/nano | 28/35 (80%) | REGRESSED |
| Avg documents_to_find per plan | 12.2 | 9.0 (gemini) | 6.6 | REGRESSED |
| Avg documents_to_create per plan | 16.8 | 9.0 (gemini) | 7.1 | REGRESSED |
| Avg total documents per plan | 29.0 | 18.0 (gemini) | 13.7 | REGRESSED |
| Avg find description length (chars) | 270 | 271 (gemini) | 167 | MIXED |
| Avg create description length (chars) | 230 | 295 (gemini) | 193 | MIXED |
| Duplicates | 0 | 1 (llama, hk_game) | ~0 | UNCHANGED |

**Document count is the biggest regression.** The baseline averaged 29 documents total
per plan; the best PR model (gemini-flash) produces 18 (62% of baseline), and most
others produce 11-14 (38-48%). The `max_length=6` cap on primary fields plus
`max_length=3` on part2 fields gives a theoretical maximum of 18 documents — already
below the baseline average of 29.

**Description quality varies widely by model.** gemini-flash matches baseline quality.
haiku produces excessively verbose descriptions (~480 chars, 178% of baseline) which
drives truncation. llama3.1 produces terse descriptions (~70 chars, 25% of baseline).

## New Issues

1. **`max_length=6` is too aggressive.** Baseline data shows 12-17 documents per
   category. The cap of 6+3=9 max per category is well below baseline norms and causes
   validation rejections for models that try to exceed it.

2. **False `partial_recovery` monitoring.** `runner.py` hardcodes `expected_calls=3`
   for all steps, but `identify_documents` is a single-call step. This causes 35/35
   false positive `partial_recovery` events, making post-hoc analysis unreliable.

3. **Missing deduplication in `cleanup()`.** The `seen_names` guard present in
   `identify_potential_levers.py` was never ported to `identify_documents`. Observed:
   llama3.1 duplicated "Hong Kong Labour Laws and Regulations" in hong_kong_game.

## Verdict

**NO**: The PR causes more harm than good. While it helps well-behaved models that
already produce small outputs, the `max_length=6` caps are far too tight relative to
baseline expectations (12-17 documents per category). The caps cause new validation
failures for 2 models and reduce document count by ~50% across the board. The
underlying truncation problem (per-item verbosity) is not addressed.

## Recommended Next Change

**Proposal**: Raise `max_length` caps from 6/3 to 15/8 and add soft description length
guidance to the system prompt ("Each description: 2-4 sentences, 100-250 characters").

**Why**: The hard caps need to be safety nets, not tight constraints. Baseline data
shows 12-17 items per category, so caps should be above that range. Soft prompt
guidance for description length addresses the actual truncation root cause (per-item
verbosity) without rejecting valid responses.

**What to verify in next iteration**:
- haiku success rate improves from 1/5 (should be 3-5/5 with higher caps + length guidance)
- gpt-4o-mini no longer hits `too_long` validation
- Document count recovers toward baseline levels (target: 20+ total)
- Description length converges across models (target: 150-300 chars)

**Risks**: Raising caps without verbosity guidance could re-introduce truncation for
haiku. The two changes should be paired.

## Backlog

- **Fix false `partial_recovery` events**: Change `_run_documents()` to return
  `calls_succeeded=None` (the guard at runner.py:514 already handles None).
- **Add deduplication in `cleanup()`**: Port `seen_names` guard from
  `identify_potential_levers.py`.
- **`OPTIMIZE_INSTRUCTIONS` constant**: This is self-improve guidance (not runtime
  code). It is intentionally not injected into the system prompt. The code review
  misidentified it as dead code. Consider adding a comment to the constant clarifying
  its purpose to prevent future misdiagnosis.
- **`steps_to_create`/`steps_to_find` sub-lists**: No `max_length` constraint on these
  nested lists. Lower priority — address after the primary caps are calibrated.
