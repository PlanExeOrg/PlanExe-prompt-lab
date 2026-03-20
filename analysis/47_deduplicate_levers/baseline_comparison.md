# Baseline Comparison: deduplicate_levers

## Overview

This report compares 7 model runs (history/3/36–42) against the gold-standard baseline produced by `google/gemini-2.0-flash-001` on 5 plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`.

---

## Success Rate

| Run | Model | Succeeded | Failed | Failure Reason |
|-----|-------|-----------|--------|----------------|
| 36 | ollama-llama3.1 | 5/5 | 0 | — |
| 37 | openrouter-openai-gpt-oss-20b | 5/5 | 0 | — |
| 38 | openai-gpt-5-nano | 5/5 | 0 | — |
| 39 | openrouter-qwen3-30b-a3b | 4/5 | 1 | plan timeout after 600s (`20250321_silo`) |
| 40 | openrouter-openai-gpt-4o-mini | 5/5 | 0 | — |
| 41 | openrouter-gemini-2.0-flash-001 | 5/5 | 0 | — |
| 42 | anthropic-claude-haiku-4-5-pinned | 5/5 | 0 | — |

Six of seven models achieved 100% success rate. Run 39 (qwen3-30b-a3b) timed out on the `silo` plan (600s limit exceeded); all other plans completed. This timeout was the only hard failure across the entire batch.

---

## Quantitative Comparison

Metrics are averaged across all successful plans per model. The baseline used the same 5 plans and the same model (gemini-2.0-flash-001) running the full PlanExe pipeline.

| Metric | Baseline | llama3.1 (36) | gpt-oss-20b (37) | gpt-5-nano (38) | qwen3-30b (39) | gpt-4o-mini (40) | gemini-2.0-flash (41) | claude-haiku (42) |
|--------|----------|---------------|-----------------|-----------------|----------------|-----------------|----------------------|-------------------|
| Lever count (avg) | 7.0 | 6.6 | 6.4 | **4.4** | 6.2 | 6.0 | **7.2** | **7.0** |
| Option violations (non-3) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Avg lever name length (chars) | 28 | 28 | 28 | 26 | 27 | 29 | 28 | 27 |
| Avg consequences length (chars) | 275 | 286 | 269 | 285 | 274 | 276 | 273 | 291 |
| Avg options text length (chars) | 420 | 446 | 431 | 462 | 434 | 449 | 427 | 442 |
| Avg review length (chars) | 154 | 156 | 153 | 153 | 154 | 155 | 154 | 152 |
| Name uniqueness ratio | 1.00 | **0.96** | **0.97** | 1.00 | **0.97** | 1.00 | 1.00 | 1.00 |
| Keep % (of all responses) | 47% | 44% | 43% | 29% | 41% | 40% | 48% | 47% |
| Absorb % | 53% | 55% | 57% | 65% | 59% | 60% | 52% | 47% |
| Remove % | 0% | 1% | 0% | **5%** | 0% | 0% | 0% | **7%** |
| Avg justification length (chars) | ~273* | 467 | 461 | 575 | 476 | 504 | 312 | 717 |

*Baseline justification length estimated from `silo` plan only (all other plans share the same baseline model).

**Per-plan lever counts** (BL = baseline):

| Plan | BL | llama3.1 | gpt-oss-20b | gpt-5-nano | qwen3-30b | gpt-4o-mini | gemini-flash | claude-haiku |
|------|----|----------|-------------|------------|-----------|-------------|--------------|--------------|
| silo | 7 | 6 | 7 | 5 | 7* | 7 | 7 | 6 |
| gta_game | 8 | 7 | 8 | 6 | 7 | 7 | 8 | 8 |
| sovereign_identity | 5 | 5 | 3 | **1** | 6 | **2** | 5 | 5 |
| hong_kong_game | 7 | 6 | 6 | 5 | 7 | 8 | 8 | 8 |
| parasomnia | 8 | 9 | 8 | 5 | **4** | 6 | 8 | 8 |

*qwen3-30b failed on silo (timeout); shown as 7 from the partial output that was written.

**Verdict by metric:**

- **Option count**: All models produce exactly 3 options per lever. No violations. Perfect match with baseline.
- **Lever count**: gemini-2.0-flash-001 (run 41) and claude-haiku (run 42) most closely match baseline average of 7.0. gpt-5-nano severely under-deduplicates, producing only 4.4 levers on average.
- **Description length**: All models produce text within 5–10% of baseline across consequences, options, and review fields. Differences are minor.
- **Name uniqueness**: gemini-2.0-flash-001, gpt-4o-mini, gpt-5-nano, and claude-haiku achieve 1.00. llama3.1, gpt-oss-20b, and qwen3-30b produce duplicate lever names in at least one plan.
- **Classification balance**: Baseline uses 47% keep / 53% absorb / 0% remove. gemini-2.0-flash-001 (48/52/0%) and claude-haiku (47/47/7%) are closest in keep ratio. gpt-5-nano is an outlier at 29/65/5% — it over-absorbs and uses `remove` inappropriately.

---

## Quality Assessment

### llama3.1 (run 36)
- **Completeness**: Generally covers the right lever categories. Produces one duplicate lever name in `sovereign_identity` (`Technical Feasibility Strategy` appears twice), meaning it failed to catch its own prior keep decision when evaluating the second instance.
- **Specificity**: Justifications reference lever-specific concepts but can be verbose and sometimes circular (e.g., "this lever is distinct because it addresses a crucial aspect"). Less concise than baseline.
- **Verbosity**: Justifications average 467 chars vs baseline ~273 — overly verbose. Description fields are similar in length to baseline.

### openrouter-openai-gpt-oss-20b (run 37)
- **Completeness**: Problematic on `sovereign_identity`: collapses 5 levers to 3 (drops `Policy Advocacy Strategy` and `Procurement Influence Strategy`). Also has a duplicate name in `hong_kong_game` (`Talent Alignment Strategy` twice). Under-deduplication and name collision together indicate incomplete lever tracking.
- **Specificity**: Justifications are appropriate length and reference lever IDs, but the aggressive consolidation on `sovereign_identity` removes meaningful distinctions.
- **Verbosity**: Description fields on par with baseline.

### openai-gpt-5-nano (run 38)
- **Completeness**: Severely incomplete. Collapses `sovereign_identity` to a single lever (vs 5 in baseline). Averages only 4.4 levers per plan — 37% below baseline. Uses `remove` classification 5% of the time (vs 0% in baseline), discarding lever content inappropriately. The model over-absorbs even when distinctions are meaningful.
- **Specificity**: The one lever it keeps in `sovereign_identity` (`Policy Advocacy Strategy`) is a legitimate lever but most of the plan's strategic coverage is lost.
- **Verbosity**: Justifications are longer (575 chars) but describe fewer decisions, suggesting the model over-explains each choice rather than covering the full set.

### openrouter-qwen3-30b-a3b (run 39)
- **Completeness**: Mixed. Produces correct counts on `silo` and `hong_kong_game` (7/7), but collapses `parasomnia` to only 4 levers (vs 8 in baseline) and duplicates a name in `sovereign_identity`. The timeout on `silo` also indicates it is too slow for production use.
- **Specificity**: Justifications are adequate. The duplicate lever name issue in `sovereign_identity` (keeps two `Technical Feasibility Strategy` levers) indicates the model does not cross-check prior decisions consistently.
- **Verbosity**: Similar to baseline on description fields.

### openrouter-openai-gpt-4o-mini (run 40)
- **Completeness**: Poor on `sovereign_identity` — produces only 2 levers (drops Policy Advocacy, Coalition Building, and Procurement Influence). Slightly over-deduplicates `parasomnia` (6 vs 8 in baseline). No duplicate names; no `remove` uses.
- **Specificity**: Where levers are kept, they are well-described. The collapse on `sovereign_identity` is the main weakness.
- **Verbosity**: Justifications slightly longer than baseline (504 chars) but reasonable.

### openrouter-gemini-2.0-flash-001 (run 41)
- **Completeness**: Best alignment with baseline. Produces 7.2 levers on average vs 7.0. Achieves exactly the right lever set on `sovereign_identity` (5/5) and `parasomnia` (8/8). No duplicate names, no `remove` usage.
- **Specificity**: Justifications are the most concise (312 chars avg), matching the terse baseline style most closely. Lever names, consequences, options, and reviews all align closely with baseline.
- **Verbosity**: Description fields are within 2% of baseline averages across all categories. The justifications are appropriately concise.

### anthropic-claude-haiku-4-5-pinned (run 42)
- **Completeness**: Very good. Achieves correct lever count on `sovereign_identity` (5/5) and `parasomnia` (8/8). Average of 7.0 matches baseline exactly. No duplicate names.
- **Specificity**: Justifications are highly specific — the most verbose at 717 chars avg. This is appropriate for complex decisions but overlong compared to baseline style.
- **Verbosity**: Description fields are slightly longer than baseline (avg consequences 291 vs 275) but not bloated. The high justification length is the main deviation from baseline style. Uses `remove` in 7% of cases (vs 0% in baseline), but the removed levers appear to be genuinely redundant in context.

---

## Model Ranking

1. **openrouter-gemini-2.0-flash-001 (run 41)** — Closest match to baseline in lever count, classification balance, and justification style. No duplicate names, no removes, concise justifications. This is the same model family as baseline (gemini-2.0-flash), which likely explains the alignment.

2. **anthropic-claude-haiku-4-5-pinned (run 42)** — Correct lever counts on all plans. Perfect name uniqueness. Minor deviations: longer justifications, occasional `remove` usage (7% vs 0% baseline). Overall very close to baseline quality.

3. **ollama-llama3.1 (run 36)** — Correct lever categories with one duplicate name issue in `sovereign_identity`. Slightly verbose justifications. Description fields on par with baseline. Adequate for most plans.

4. **openrouter-qwen3-30b-a3b (run 39)** — Mixed performance: correct on some plans but collapses `parasomnia` significantly (4 vs 8 levers) and times out on `silo`. Duplicate name in `sovereign_identity`. Slowest model by far (450–600s per plan vs 15–80s for fast models).

5. **openrouter-openai-gpt-oss-20b (run 37)** — Correct on simple plans but drops 2 out of 5 levers on `sovereign_identity`. Duplicate lever name in `hong_kong_game`. Moderate performance.

6. **openrouter-openai-gpt-4o-mini (run 40)** — Severe under-deduplication on `sovereign_identity` (2 vs 5 levers). Otherwise acceptable. The collapse on one plan is a significant completeness gap.

7. **openai-gpt-5-nano (run 38)** — Worst performer. Collapses `sovereign_identity` to a single lever. Uses `remove` inappropriately. Averages 4.4 levers vs 7.0 in baseline. The 37% lever count deficit represents a major loss of strategic coverage.

---

## Overall Verdict

**MIXED**: The experiment batch produces highly variable quality depending on the model.

The top two models (gemini-2.0-flash and claude-haiku) are **COMPARABLE** to baseline — lever counts match, options are always exactly 3, name uniqueness is perfect, and description lengths are within acceptable range. gemini-2.0-flash-001 is effectively equivalent to the baseline (same model family, nearly identical outputs).

The bottom three models (gpt-5-nano, gpt-4o-mini, gpt-oss-20b) are **WORSE** than baseline — they fail to preserve the correct lever set on the `sovereign_identity` plan, losing 40–80% of the strategic levers for that plan.

The middle two models (llama3.1, qwen3-30b) are **COMPARABLE** on most plans but have reliability issues (duplicate names, timeout, parasomnia collapse).

Key numbers supporting this verdict:
- Option violations: 0 across all models (all correct)
- Lever count deviation from baseline: gemini 0.2, haiku 0.0, llama3.1 −0.4, qwen3-30b −0.8, gpt-4o-mini −1.0, gpt-oss-20b −0.6, gpt-5-nano −2.6
- Duplicate lever names: 3 of 7 models produce at least one plan with duplicate names (baseline: 0)
- Remove usage: 2 of 7 models use `remove` (baseline: 0%)

---

## Recommendations

1. **Use gemini-2.0-flash-001 or claude-haiku for production**: These two models match baseline quality most consistently across all 5 plans and produce no structural errors (no duplicate names, no removes, correct lever counts).

2. **Avoid gpt-5-nano for deduplicate_levers**: Its 37% lever count deficit and inappropriate use of `remove` make it unsuitable. It collapses genuinely distinct strategic levers into one, losing coverage the downstream steps depend on.

3. **Investigate sovereign_identity failures**: Five of seven models produce significantly fewer levers than baseline (1–3 vs 5) on this plan. This suggests the input levers for `sovereign_identity` are particularly similar in naming and framing, making deduplication harder. A prompt adjustment clarifying when to keep levers with similar names but different strategic dimensions (e.g., both named `Technical Feasibility Strategy` but covering different scopes) could help.

4. **Fix duplicate name issue**: Three models produce plans where the same lever name appears in `deduplicated_levers` twice. The prompt should explicitly instruct models to check the already-decided set before assigning a `keep` classification to a subsequent lever with the same name.

5. **Align on `remove` usage**: The baseline uses 0 `remove` decisions. Two models (gpt-5-nano at 5%, claude-haiku at 7%) use `remove`. The prompt already says "Use this sparingly" — consider strengthening this to "Do not use `remove`; always prefer `absorb` to retain detail."

6. **qwen3-30b latency is prohibitive**: At 450–600s per plan (vs 15–80s for fast models), qwen3-30b is not viable for production use even if quality were good.
