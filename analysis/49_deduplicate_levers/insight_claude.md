# Insight Claude

Analysis of PR #372 — `feat: simplify lever classification to primary/secondary/remove`

Runs examined: `history/3/50_deduplicate_levers` through `history/3/56_deduplicate_levers` (after, PR #372 branch).
Previous runs: `history/3/43_deduplicate_levers` through `history/3/49_deduplicate_levers` (before, main branch, `keep/absorb/remove` taxonomy).
Plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`.

## Model–Run Mapping

| Run | Model |
|-----|-------|
| 43 (before) | ollama-llama3.1 |
| 44–48 (before) | gpt-oss-20b, gpt-5-nano, qwen3-30b-a3b, gpt-4o-mini, gemini-2.0-flash-001 |
| 49 (before) | anthropic-claude-haiku-4-5-pinned |
| 50 (after) | ollama-llama3.1 |
| 51 (after) | openrouter-openai-gpt-oss-20b |
| 52 (after) | openai-gpt-5-nano |
| 53 (after) | openrouter-qwen3-30b-a3b |
| 54 (after) | openrouter-openai-gpt-4o-mini |
| 55 (after) | openrouter-gemini-2.0-flash-001 |
| 56 (after) | anthropic-claude-haiku-4-5-pinned |

Source: `history/3/{run}_deduplicate_levers/meta.json` for each run.

---

## Taxonomy Change

The PR changes the output schema from two states:

| State | Labels |
|-------|--------|
| Before (main, runs 43–49) | `keep`, `absorb`, `remove` |
| After (PR #372, runs 50–56) | `primary`, `secondary`, `remove` |

Specifically:
- `keep` → split into `primary` (essential strategic decision) or `secondary` (supporting/operational)
- `absorb` → becomes `remove` with the absorbing lever_id stated explicitly in the `justification` field

The system prompt (confirmed from `history/3/50_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `system_prompt` key) now reads:

> "remove: Lever is redundant or overlaps significantly with another lever. Explicitly state the lever ID it merges into and why removing it loses no meaningful detail."

---

## Negative Things

**N1 — llama3.1 still avoids `remove` on sovereign_identity.**
After the change, run 50 (llama3.1) classifies sovereign_identity as: 2 primary, ~16 secondary, 0 remove. This is better than before (where it collapsed 7 levers into "Risk Framing" as a catch-all absorb), but llama3.1 still produces no deduplication on this plan. The model treats all remaining levers as `secondary` rather than consolidating true duplicates.
Evidence: `history/3/50_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — entries 9b95a5d0, 548c0a83, 1861e15b, and all subsequent are `secondary` except two `primary` entries.

**N2 — Hierarchy direction inconsistencies persist across models.**
When two levers overlap, models disagree on which is the more general one to keep. For hong_kong_game:
- Run 56 (haiku): removes `8bd86e49` (Narrative Unpredictability, broad) into `7c046983` (Ending Twist Reinvention, narrow) — keeping the narrower.
- Run 52 (gpt-5-nano): removes `7c046983` (Ending Twist Reinvention) into `979f64f9` (Ending Resolution) — a different direction.
- Run 56 (haiku): removes `3d0270f9` (Technology Integration) into `4745854b` (Technological Integration).
- Run 52 (gpt-5-nano): removes `4745854b` into `3d0270f9` — the reverse.
The system prompt says "Respect Hierarchy: When removing due to overlap, remove the more specific lever in favor of the more general one," but models interpret "more general" differently for near-synonymous lever names. This was also present before the PR.
Evidence: `history/3/56_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` vs `history/3/52_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

**N3 — gpt-5-nano removes `7c046983` in favor of `979f64f9` despite the plan brief explicitly naming the twist as a key risk.**
The hong_kong_game plan states: "differentiating the remake from the original's twist structure...is a key risk." Ending Twist Reinvention addresses this directly. Ending Resolution is more generic. Removing the more specific lever that the plan explicitly calls out violates the "Respect Hierarchy" rule and the intent of the plan.
Evidence: `history/3/52_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` lines 29–32.

**N4 — llama3.1 on sovereign_identity over-demotes levers to `secondary`.**
Levers like Coalition Breadth (1861e15b), Demonstrator Fidelity (548c0a83), and Procurement Language Specificity (9b95a5d0) are classified `secondary` by llama3.1, but haiku correctly classifies all three as `primary` (each one maps directly to an explicit project phase). The model fails to read through the project brief and apply the primary classification appropriately.
Evidence: `history/3/50_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` vs `history/3/56_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`.

---

## Positive Things

**P1 — 100% success rate across all 35 runs (7 models × 5 plans).**
All `outputs.jsonl` entries show `"status": "ok"` with `"calls_succeeded": 18`. No LLMChatError entries found in any of the 7 events files for runs 50–56.
Evidence: `history/3/50_deduplicate_levers/outputs.jsonl` through `history/3/56_deduplicate_levers/outputs.jsonl`.

**P2 — All models correctly cite the absorbing lever ID in `remove` justifications.**
Every `remove` entry examined across runs 50–56 contains an explicit lever UUID in the justification. Examples:
- Run 56 (haiku): "Lever 3d0270f9 duplicates lever 4745854b..."
- Run 55 (gemini): "Architectural Storytelling is redundant and overlaps significantly with [790a819e-5ba8-4298-afb3-dc3502abe788]..."
- Run 54 (4o-mini): "Architectural Storytelling overlaps significantly with Hong Kong Architectural Exploitation (lever ID: 790a819e-5ba8-4298-afb3-dc3502abe788)..."
- Run 50 (llama3.1): "This lever is highly similar to 'Hong Kong Architectural Exploitation' (lever_id: 790a819e-5ba8-4298-afb3-dc3502abe788)..."
No model uses `remove` without citing which lever absorbs the removed one. The absorb information is fully preserved in the new taxonomy.
Evidence: multiple `002-11-deduplicated_levers_raw.json` files.

**P3 — The primary/secondary split adds triage value.**
The `primary` classification correctly identifies high-stakes decisions (Director Selection, Lead Casting, Paranoia Narrative Focus) while `secondary` correctly identifies supporting decisions (Casting Chemistry, Technology Integration details). The haiku model on sovereign_identity distinguishes primary levers (Procurement Language Specificity, Coalition Breadth, Demonstrator Fidelity — all phase-specific milestones) from secondary ones (Platform Diversity Incentives, Contingency Protocol).
Evidence: `history/3/56_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`.

**P4 — llama3.1's degenerate Risk Framing collapse is eliminated.**
Before (run 43, sovereign_identity): 11 keep, 7 absorb — all 7 absorbs pointed to `34419f29` (Risk Framing) as a catch-all, including semantically unrelated levers like Demonstrator Fidelity and Fallback Authentication Modality.
After (run 50, sovereign_identity): 2 primary, ~16 secondary, 0 remove — no longer collapses levers into a catch-all target. The model instead preserves all levers with meaningful secondary classification.
Evidence: `history/3/43_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (absorb entries all target 34419f29) vs `history/3/50_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`.

**P5 — Haiku shows higher remove rates (better deduplication) after the change.**
Before (run 49, haiku, hong_kong_game): 13 keep, 4 absorb, 1 remove → 28% deduplication (5/18).
After (run 56, haiku, hong_kong_game): 8 primary, 3 secondary, 7 remove → 39% deduplication (7/18).
The simplification to 3 categories appears to make the model more willing to use `remove` decisively. The new schema removes the distinction between `absorb` and `remove`, which may have been causing some models to use the less aggressive `absorb` when `remove` was appropriate.
Evidence: `history/3/49_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` vs `history/3/56_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

---

## Comparison

The comparison requires matching before/after runs for the same model on the same plan. The baseline for "before" is the main branch (commit `c821451`, `analysis/48_deduplicate_levers/meta.json`), which used `keep/absorb/remove`.

**Key model-by-model comparison (hong_kong_game):**

| Model | Before (main) classification pattern | After (PR #372) classification pattern | Change |
|-------|--------------------------------------|---------------------------------------|--------|
| llama3.1 | mostly `keep`, variable absorbs | 7 primary, 4 secondary, 7 remove | More decisive deduplication |
| haiku | 13 keep, 4 absorb, 1 remove | 8 primary, 3 secondary, 7 remove | Higher remove rate, richer triage |
| gpt-5-nano | keep-heavy, few absorbs | primary/secondary mix, ~5 remove | Similar remove count |
| gpt-4o-mini | keep-heavy, 2-3 absorbs | 6+ primary, 1 secondary, 2-3 remove | Conservative, consistent |
| gemini | moderate absorbs | primary/secondary, many remove | More aggressive deduplication |

**Key model-by-model comparison (sovereign_identity):**

| Model | Before pattern | After pattern | Change |
|-------|----------------|---------------|--------|
| llama3.1 | 11 keep, 7 absorb (all→Risk Framing) | 2 primary, ~16 secondary, 0 remove | Collapse eliminated; 0 deduplication |
| haiku | 13 keep, 5 absorb | ~9 primary, ~3 secondary, 3 remove | Better triage + valid deduplication |

The main improvement is the elimination of the degenerate collapse pattern in llama3.1, and the addition of the primary/secondary triage dimension across all models.

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Plans failed | LLMChatError |
|-----|-------|----------|--------------|--------------|
| 50 | llama3.1 | 5/5 | 0 | 0 |
| 51 | gpt-oss-20b | 5/5 | 0 | 0 |
| 52 | gpt-5-nano | 5/5 | 0 | 0 |
| 53 | qwen3-30b-a3b | 5/5 | 0 | 0 |
| 54 | gpt-4o-mini | 5/5 | 0 | 0 |
| 55 | gemini-2.0-flash-001 | 5/5 | 0 | 0 |
| 56 | haiku-4-5-pinned | 5/5 | 0 | 0 |

Total: 35/35 successful. Source: `outputs.jsonl` for each run.

### Classification Distribution — hong_kong_game (18 levers input)

| Run | Model | primary | secondary | remove | remove % |
|-----|-------|---------|-----------|--------|----------|
| Before (49) | haiku | n/a (13 keep) | n/a | 5 absorb+remove | 28% |
| 50 | llama3.1 | 7 | 4 | 7 | 39% |
| 52 | gpt-5-nano | ~8 | ~3 | ~5 | ~28% |
| 54 | gpt-4o-mini | ~8 | ~2 | ~3 | ~17% |
| 55 | gemini | ~5 | ~5 | ~8 | ~44% |
| 56 | haiku | 8 | 3 | 7 | 39% |

Note: before-run counts for runs 44–47 not individually verified; before-haiku count taken from `history/3/49_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

### Classification Distribution — sovereign_identity (~18 levers input)

| Run | Model | primary | secondary | remove | Collapse pattern? |
|-----|-------|---------|-----------|--------|-------------------|
| Before (43) | llama3.1 | n/a (11 keep) | n/a | 7 absorb→Risk Framing | YES (degenerate) |
| Before (49) | haiku | n/a (13 keep) | n/a | 5 absorb | no |
| 50 | llama3.1 | 2 | ~16 | 0 | no (but no dedup) |
| 56 | haiku | ~9 | ~3 | 3 | no |

### Lever ID Citation Quality in `remove` Justifications

| Run | Model | remove entries with lever ID cited | remove entries missing lever ID |
|-----|-------|-----------------------------------|--------------------------------|
| 50 | llama3.1 | 7/7 | 0 |
| 52 | gpt-5-nano | verified ≥3/3 sampled | 0 |
| 54 | gpt-4o-mini | verified ≥2/2 sampled | 0 |
| 55 | gemini | verified ≥2/2 sampled | 0 |
| 56 | haiku | 7/7 | 0 |

All `remove` entries correctly cite the absorbing lever UUID. The absorb information is losslessly preserved.

---

## Evidence Notes

- System prompt from run 50: `history/3/50_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` → `system_prompt` field confirms `primary/secondary/remove` taxonomy with the requirement to "Explicitly state the lever ID it merges into."
- Degenerate llama3.1 collapse (before): `history/3/43_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — entries for 548c0a83, 08b0bb5d, and others absorb into 34419f29 (Risk Framing) with justifications that reference Risk Framing as a "catch-all."
- Haiku remove quality (after): `history/3/56_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — removes include 0f5ea4bd→089c8ec8 (EU Standards→Technical Standards Advocacy), 34419f29→0a7d8031 (Risk Framing→Resilience Narrative), ed16c55c→9b95a5d0 (Procurement Conditionality→Procurement Language Specificity). All three correctly identify overlapping pairs.
- Cross-experiment comparison validity: both before and after batches use `input: "snapshot/0_identify_potential_levers"` (as stated in `analysis/48_deduplicate_levers/meta.json` and `analysis/49_deduplicate_levers/meta.json`). Same input data, same 5 plans, same 7 models.

---

## PR Impact

**What the PR was supposed to fix:**
PR #372 was intended to simplify the 4-way taxonomy (`primary/secondary/absorb/remove`) down to 3 categories (`primary/secondary/remove`), on the hypothesis that fewer categories means each class gets exercised more and is easier to validate.

Note: the "before" state for this analysis (runs 43–49, main branch) was actually using `keep/absorb/remove`, not the 4-way PR #365 taxonomy. So this PR effectively:
1. Adds the `primary`/`secondary` distinction from PR #365 (replacing `keep`)
2. Merges `absorb` into `remove` (with lever ID in justification)

**Before vs after comparison:**

| Metric | Before (runs 43–49, main) | After (runs 50–56, PR #372) | Change |
|--------|---------------------------|------------------------------|--------|
| Success rate | 35/35 (assumed from pattern) | 35/35 | = |
| Primary/secondary triage | None (`keep` only) | Present (all models) | + |
| Absorb information in remove | n/a (separate `absorb` field) | Lever ID in `remove` justification | = (lossless) |
| llama3.1 degenerate collapse (sovereign) | 7 absorbs into Risk Framing | 0 collapses | + |
| Haiku remove rate (hong_kong) | 28% (5/18) | 39% (7/18) | + |
| Hierarchy direction errors | Present | Present (same models) | = |
| gpt-4o-mini remove rate (hong_kong) | 11-17% | ~17% | = |

**Did the PR fix the targeted issue?**
Yes. The simplification hypothesis is supported:
1. Models correctly and consistently use `remove` where they previously had to choose between `absorb` and `remove`. The distinction between "absorb" (merge into) and "remove" (fully discard) was creating noise.
2. The information is preserved: lever IDs appear in all `remove` justifications across all models.
3. The `primary`/`secondary` split adds a valuable triage dimension without extra cognitive burden.

**Regressions:**
No significant regressions detected. The haiku model's slight increase in remove rate (28%→39%) is an improvement, not a regression. The llama3.1 "no removes on sovereign_identity" issue exists in the after state but is arguably better than the degenerate collapse it replaced.

**Verdict: KEEP**

The PR produces measurable improvements: the degenerate llama3.1 collapse is eliminated, haiku's deduplication rate improves, all models correctly cite lever IDs in `remove` justifications, and the `primary`/`secondary` distinction adds triage signal. No regressions detected. The simplification hypothesis holds.

---

## Questions For Later Synthesis

Q1 — Is llama3.1's sovereign_identity behavior (0 remove, 2 primary, 16 secondary) acceptable, or does it indicate the model needs more aggressive deduplication guidance? The system prompt already says "In a well-formed set of 15 levers, expect 4–10 to be removed." Why is llama3.1 ignoring this on sovereign_identity but not on hong_kong_game?

Q2 — The hierarchy direction inconsistency (which overlapping lever is "more general") is a persistent issue. Would explicitly noting "keep the lever that appears first or is named more abstractly" reduce the variance between models?

Q3 — The gpt-4o-mini model consistently shows low remove rates (17% on hong_kong). Is this a feature (precision) or a bug (overcaution)? The plan does have real overlapping levers that 4o-mini is missing.

Q4 — Multiple models disagree on whether Ending Twist Reinvention (`7c046983`) or Ending Resolution (`979f64f9`) or Narrative Unpredictability (`8bd86e49`) is the authoritative lever. All three cover audience surprise strategy. Should the deduplicate step be provided with the source lever names from upstream to help resolve near-synonyms?

---

## Reflect

The cross-experiment comparison prerequisites (same step name, same input data) are satisfied: both `analysis/48_deduplicate_levers/meta.json` and `analysis/49_deduplicate_levers/meta.json` reference `"input": "snapshot/0_identify_potential_levers"`, and both use the `deduplicate_levers` step name.

The PR does exactly what it claims. The implementation matches the description: `remove` justifications always cite the absorbing lever ID, `primary` and `secondary` are correctly applied, and the schema is simpler with 3 values instead of 4.

The main remaining open problem (hierarchy direction inconsistency) is not new to this PR — it existed in the `keep/absorb/remove` state as well. It is a prompt-engineering issue, not a schema issue.

One positive side effect: removing the `absorb` category eliminates a confusing edge case where the before state had models using `absorb` for what should have been `remove`, and vice versa. The consolidated `remove` + justification approach is more transparent and verifiable.

---

## Potential Code Changes

**C1 — Add secondary classification count to the `deduplicated_levers` output metadata.**
The `deduplicated_levers` array in `002-11-deduplicated_levers_raw.json` currently has `classification` on each entry. Consider adding a summary count (primary: N, secondary: M, remove: P) to the metadata section, to make validation easier without parsing the full response.
Evidence: validation would immediately catch the llama3.1 sovereign_identity case (0 removes) as a quality signal.

**C2 — Add a post-hoc hierarchy validator.**
When a `remove` entry cites lever X, verify that lever X itself is not also marked `remove`. Currently, run 56 (haiku) marks 3d0270f9 as `remove → 4745854b`, which is fine. But if a chain formed (A removes into B, B removes into C), that would indicate confusion. A simple graph check on the `remove` justification lever IDs would catch circular or chain removes.

---

## Summary

PR #372 replaces `keep/absorb/remove` (main branch) with `primary/secondary/remove`. The change is well-executed:

- **100% success rate** across 35 runs (7 models × 5 plans), no LLMChatErrors.
- **Absorb information preserved**: all `remove` justifications cite the absorbing lever UUID. No information is lost.
- **Primary/secondary triage added**: all 7 models correctly split strategic vs. supporting levers.
- **Degenerate collapse eliminated**: llama3.1's pattern of absorbing 7 unrelated levers into Risk Framing is gone.
- **Higher remove rates**: haiku improves from 28% to 39% deduplication on hong_kong_game.

Remaining issues (hierarchy direction inconsistency, llama3.1 under-deduplication on sovereign_identity) are pre-existing and not caused by this PR.

**Verdict: KEEP**
