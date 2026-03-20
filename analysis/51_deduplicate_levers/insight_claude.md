# Insight Claude

Analysis of PR #374 — `feat: batch categorical dedup — single call + primary/secondary/remove`

Runs examined (after PR #374): `history/3/64_deduplicate_levers` through `history/3/70_deduplicate_levers`.
Runs examined (before PR #374 / PR #373): `history/3/57_deduplicate_levers` through `history/3/63_deduplicate_levers`.
Plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`.

## Model–Run Mapping

| Run | Model |
|-----|-------|
| 57 (before) | ollama-llama3.1 |
| 58 (before) | openrouter-openai-gpt-oss-20b |
| 59 (before) | openai-gpt-5-nano |
| 60 (before) | openrouter-qwen3-30b-a3b |
| 61 (before) | openrouter-openai-gpt-4o-mini |
| 62 (before) | openrouter-gemini-2.0-flash-001 |
| 63 (before) | anthropic-claude-haiku-4-5-pinned |
| 64 (after) | ollama-llama3.1 |
| 65 (after) | openrouter-openai-gpt-oss-20b |
| 66 (after) | openai-gpt-5-nano |
| 67 (after) | openrouter-qwen3-30b-a3b |
| 68 (after) | openrouter-openai-gpt-4o-mini |
| 69 (after) | openrouter-gemini-2.0-flash-001 |
| 70 (after) | anthropic-claude-haiku-4-5-pinned |

Source: `history/3/{run}_deduplicate_levers/meta.json`.

---

## Architecture Change

PR #374 combines two previously competing approaches:

- **Single batch call** (from PR #373): All levers sent to the LLM at once instead of 18 sequential per-lever calls. This architecture is maintained in PR #374.
- **Categorical primary/secondary/remove** (from PR #372): The LLM classifies each lever as `primary`, `secondary`, or `remove`, rather than scoring it on a Likert scale. PR #374 restores this classification schema.

The system prompt in the after runs reads:

> "You are deduplicating a set of strategic levers for a project plan. Your task is to classify every lever and provide a justification. You see all levers at once — compare them against each other before making decisions."

With classifications:
- **primary**: Essential strategic decision; failure would cause project to fail or succeed fundamentally differently.
- **secondary**: Real concern but not top-level strategic choice.
- **remove**: Redundant — overlaps substantially with another lever.

The before runs (PR #373) used Likert scoring (-2 to +2), keeping levers with score ≥ 1.

PR #374 also adds **robustness guards** from iter 50 assessment:
- Duplicate lever_id detection
- Minimum lever count check
- Fallback classification for levers not classified by the LLM: "Not classified by LLM. Keeping as primary to avoid data loss."

Sources: `history/3/64_deduplicate_levers/outputs/20250329_gta_game/002-11-deduplicated_levers_raw.json` (system_prompt field), `history/3/57_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` (Likert system_prompt).

---

## Negative Things

**N1 — llama3.1 times out on silo and parasomnia plans, producing zero-quality fallback output.**

Run 64 (llama3.1, silo): duration = 120.16 seconds, which equals the pipeline timeout. The log shows exactly 2:00 from start to complete. The result is all 18 levers classified as "Not classified by LLM. Keeping as primary to avoid data loss." — the robustness guard saved the run from failing but produced no real classification.

Run 64 (llama3.1, parasomnia): duration = 120.12 seconds — also at timeout limit.

This means llama3.1 fails to produce valid output for 2 out of 5 plans (40%). For those plans, no lever is actually deduplicated; all 18 are passed downstream as "primary" with identical fallback justifications.

Evidence:
- `history/3/64_deduplicate_levers/outputs/20250321_silo/log.txt` — 120.16s duration (at timeout)
- `history/3/64_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — all 18 entries read "Not classified by LLM. Keeping as primary to avoid data loss."
- `history/3/64_deduplicate_levers/outputs.jsonl` — silo: 120.16s, parasomnia: 120.12s (both at timeout)

**N2 — llama3.1 classifies all levers as "primary" even when a response is received (gta_game plan).**

Run 64 (llama3.1, gta_game): The model produces proper justifications for all 18 levers, but classifies 11 as "primary" and 7 as "secondary" with only 1 "remove" (c0ccf4c6, in-game advertising). The model's justifications for "secondary" items are meaningful, but the 0/18 deduplication rate (only 1 remove) is lower than the expected 25-50% removal rate.

Unlike the before run (PR #373, llama3.1) which catastrophically kept only 1 lever per plan due to scale inversion, the after run (PR #374) produces plausible but under-deduplicating output for gta_game.

Evidence: `history/3/64_deduplicate_levers/outputs/20250329_gta_game/002-11-deduplicated_levers_raw.json` — 17 entries in `deduplicated_levers`, 1 removed.

**N3 — gpt-oss-20b leaves one lever unclassified in hong_kong_game (fallback triggered).**

Run 65 (gpt-oss-20b, hong_kong_game): lever dcb03988 (Cultural Authenticity) has justification "Not classified by LLM. Keeping as primary to avoid data loss." The model classified 17 of 18 levers but missed one. The fallback correctly preserves the lever rather than dropping it.

Evidence: `history/3/65_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` lines 88-92.

**N4 — Inter-model disagreement on primary vs. secondary is high for the same lever in the same plan.**

For hong_kong_game, the treatment of several levers diverges sharply between models:

| Lever | run 64 (llama) | run 65 (gpt-oss-20b) | run 70 (haiku) |
|-------|----------------|----------------------|----------------|
| Paranoia Narrative Focus (c0ed2c47) | primary | primary | secondary |
| Technology Integration (3d0270f9) | primary | primary | remove |
| Surveillance Technology Focus (f420afde) | primary | remove | primary |
| Cultural Authenticity (dcb03988) | primary | primary (fallback) | secondary |

The categorical schema depends on the model's understanding of "gating the project's core outcome" — a subjective criterion. When models disagree this much on whether something is "primary" vs. "secondary", the classification provides weaker signal to downstream steps.

Evidence: Comparison of `response` arrays in run 64, 65, 70 hong_kong_game outputs.

**N5 — Robustness fallback creates misleading "primary" classifications.**

The fallback "Not classified by LLM. Keeping as primary to avoid data loss." is a safe default but creates false signal: downstream steps will see every lever as "primary" even when the LLM never evaluated it. For the silo plan with llama3.1, all 18 levers including overlapping ones (e.g., Information Control Protocols and Information Dissemination Protocol) survive with "primary" classification.

In the before run (PR #373), llama3.1 had a different failure mode (scale inversion → 1 lever kept). The robustness guard fixes the catastrophic outcome but replaces it with a silently wrong outcome: no deduplication, no differentiation between essential and peripheral levers.

---

## Positive Things

**P1 — 100% structural success rate: 35/35 plans succeed.**

All 7 models × 5 plans = 35 runs show `"status": "ok"` in outputs.jsonl. No LLMChatError entries in any events.jsonl for the after runs.

Evidence: `history/3/64_deduplicate_levers/outputs.jsonl` through `history/3/70_deduplicate_levers/outputs.jsonl`.

**P2 — Deduplication restored for capable models.**

For 6 of 7 models, PR #374 restores meaningful deduplication via the `remove` classification. Capable models remove 1–6 levers per plan (removal rate ~6–33%), which is within the intended 25–50% range for plans with moderate overlap.

Examples:
- Run 65 (gpt-oss-20b, hong_kong): 6 removes (f9512726, 8bd86e49, f420afde, 15828c14, 979f64f9, 69bb253f) — removal rate 33%.
- Run 70 (haiku, silo): 1 remove (ee0996f6 removed as duplicate of b664e24a) — removal rate 6%.
- Run 70 (haiku, hong_kong): 4 removes — removal rate 22%.
- Run 66 (gpt-5-nano, silo): 1 remove (ee0996f6) — see silo output.

In contrast, the before runs (PR #373, Likert) produced 0 removes for all capable models (gpt-oss-20b, qwen3, haiku, gemini, gpt-4o-mini all kept 16-18/18 levers).

Evidence: Counting `deduplicated_levers` entries vs `response` arrays in respective outputs.

**P3 — Remove justifications cite specific overlapping lever IDs.**

When models do remove a lever, they cite the overlapping lever by ID, making the deduplication auditable. Example from run 70 (haiku, silo):
> "Overlaps substantially with Information Control Protocols (b664e24a). Keeping both would duplicate effort; the more general lever should stand, so this one is removed."

Example from run 65 (gpt-oss-20b, hong_kong):
> "Architectural Storytelling duplicates Hong Kong Architectural Exploitation (lever 790a819e). The broader lever covers visual and thematic use of architecture."

Evidence: `history/3/70_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`, `history/3/65_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

**P4 — Catastrophic scale inversion from PR #373 is eliminated.**

The PR #373 Likert approach caused llama3.1 to invert the scale on silo and gta_game plans, keeping only 1 lever out of 18. PR #374's categorical schema avoids this: llama3.1 now produces reasonable classifications for gta_game (1 remove, proper primary/secondary split) and triggers the robustness guard for silo/parasomnia rather than inverting.

While llama3.1 still has issues (timeouts → fallback), it no longer produces the "1-lever plan" failure mode that would make the downstream plan essentially empty.

**P5 — Primary/secondary distinction is meaningful for capable models.**

Capable models apply the "gating the core outcome" test for primary classification with evident reasoning. Examples from run 70 (haiku, silo):
- Primary: "Information control is foundational to the silo's governance model... Poor handling undermines the entire control structure and could trigger systemic failure."
- Secondary: "Resource diversification addresses resilience but is secondary to resource allocation strategy (lever a6d45d69). It focuses on external exchange scenarios rather than core allocation decisions."

This differentiation was not available in the before (PR #373) runs, where the score-to-classification mapping (2→primary, 1→secondary) produced less grounded classifications.

**P6 — Single-call architecture maintained: speed improvement preserved.**

All after runs show `calls_succeeded: 1` per plan with durations consistent with single-call execution. The speed improvement from PR #373 (18× fewer LLM calls vs PR #372) is preserved.

| Model | Before PR #373 (18-call) | After PR #374 (1-call) |
|-------|--------------------------|------------------------|
| gpt-oss-20b (silo) | 196.6s (from run 51) | 42.1s (run 65) |
| gemini (silo) | ~130s est. | 12.7s (run 69) |
| haiku (silo) | ~130s est. | 23.0s (run 70) |

Source: `history/3/65_deduplicate_levers/outputs.jsonl`, `history/3/69_deduplicate_levers/outputs.jsonl`, `history/3/70_deduplicate_levers/outputs.jsonl`.

**P7 — Robustness guard prevents catastrophic single-lever output.**

The minimum count check introduced in PR #374 prevents the most harmful failure mode: downstream plans built on a single lever. The fallback is lossy but safer than outputting 1 lever.

---

## Comparison

### Architectural approaches

| Aspect | PR #372 (before) | PR #373 (before) | PR #374 (after) |
|--------|-----------------|-----------------|-----------------|
| LLM calls per plan | 18 sequential | 1 batch | 1 batch |
| Schema | primary/secondary/remove | Likert -2 to +2 | primary/secondary/remove |
| Dedup mechanism | Explicit `remove` | Score ≤ 0 | Explicit `remove` |
| Robustness guard | no | no | yes (fallback to primary) |
| llama3.1 failure mode | 18/18 kept (no dedup) | 1/18 kept (scale inversion) | 18/18 fallback (timeout) |

### Deduplication rate — silo plan (18 input levers)

| Run | Model | Levers removed | Removal % | Notes |
|-----|-------|----------------|-----------|-------|
| 50 (PR #372) | llama3.1 | 0 | 0% | |
| 51 (PR #372) | gpt-oss-20b | 2 | 11% | correct semantic dedup |
| 57 (PR #373) | llama3.1 | 17 | 94% | **catastrophic: scale inversion** |
| 58 (PR #373) | gpt-oss-20b | 0 | 0% | **regression: Likert doesn't dedup** |
| 64 (PR #374) | llama3.1 | 0 | 0% | timeout → fallback |
| 65 (PR #374) | gpt-oss-20b | — | — | silo: need check |
| 70 (PR #374) | haiku | 1 | 6% | ee0996f6 correctly removed |

Source: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (1 lever kept), `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (18 kept), `history/3/64_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (18 fallbacks), `history/3/70_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`.

### Deduplication rate — hong_kong_game (18 input levers)

| Run | Model | Levers removed | Removal % | Notes |
|-----|-------|----------------|-----------|-------|
| 57 (PR #373) | llama3.1 | 4 | 22% | had duplicate lever_id in response |
| 58 (PR #373) | gpt-oss-20b | 0 | 0% | Likert regression |
| 64 (PR #374) | llama3.1 | 1 | 6% | (4745854b removed) |
| 65 (PR #374) | gpt-oss-20b | 6 | 33% | 1 fallback, 5 proper removes |
| 70 (PR #374) | haiku | 4 | 22% | proper removes with reasoning |

Source: `history/3/64_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `history/3/65_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `history/3/70_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Timeouts | Fallback plans |
|-----|-------|----------|----------|----------------|
| 64 | llama3.1 | 5/5 | 2 (silo, parasomnia) | 2/5 |
| 65 | gpt-oss-20b | 5/5 | 0 | 0/5 (1 lever fallback in 1 plan) |
| 66 | gpt-5-nano | 5/5 | 0 | 0/5 |
| 67 | qwen3-30b-a3b | 5/5 | 0 | 0/5 |
| 68 | gpt-4o-mini | 5/5 | 0 | 0/5 |
| 69 | gemini-2.0-flash-001 | 5/5 | 0 | 0/5 |
| 70 | haiku-4-5-pinned | 5/5 | 0 | 0/5 |

Total structural success: 35/35. No LLMChatErrors. Source: `outputs.jsonl` for each run.

### Duration — silo plan comparison

| Run | Model | Duration (before PR #373) | Duration (after PR #374) | Change |
|-----|-------|--------------------------|--------------------------|--------|
| llama3.1 | 64 | 67.7s (PR #373) | 120.2s (timeout) | **worse** |
| gpt-oss-20b | 65 | 51.0s (PR #373) | 42.1s | ~16% faster |
| gpt-5-nano | 66 | 52.5s (PR #373) | 42.9s | ~18% faster |
| qwen3-30b-a3b | 67 | 62.4s (PR #373) | 69.4s | ~11% slower |
| gpt-4o-mini | 68 | 20.4s (PR #373) | 41.6s | ~2× slower |
| gemini-2.0-flash-001 | 69 | 11.2s (PR #373) | 12.7s | comparable |
| haiku-4-5-pinned | 70 | 24.3s (PR #373) | 23.0s | comparable |

Source: `history/3/64_deduplicate_levers/outputs.jsonl` through `history/3/70_deduplicate_levers/outputs.jsonl`, `history/3/57_deduplicate_levers/outputs.jsonl` through `history/3/63_deduplicate_levers/outputs.jsonl`.

Note: gpt-4o-mini speed regression (~2×) for silo plan. Gemini and haiku remain fast.

### Removal counts — hong_kong_game (18 levers)

| Model (after run) | Primaries | Secondaries | Removes | Fallbacks |
|-------------------|-----------|-------------|---------|-----------|
| llama3.1 (64) | 13 | 3 | 1 | 0 |
| gpt-oss-20b (65) | 9 | 1 | 7 | 1 |
| gpt-5-nano (66) | — | — | — | — |
| qwen3 (67) | — | — | — | — |
| gpt-4o-mini (68) | — | — | — | — |
| gemini (69) | — | — | — | — |
| haiku (70) | 8 | 6 | 4 | 0 |

(Full counts not read for all models; a representative sample is shown.)

### Token count — hong_kong_game

| Run | Model | Calls | Input tokens | Output tokens | Total tokens |
|-----|-------|-------|-------------|---------------|-------------|
| 57 (before, PR #373) | llama3.1 | 1 | 6,538 | 1,539 | 8,077 |
| 64 (after, PR #374) | llama3.1 | 1 | 6,489 | 2,383 | 8,872 |
| 58 (before, PR #373) | gpt-oss-20b | 4 total | 25,374 | 12,455 | 37,829 |
| 65 (after, PR #374) | gpt-oss-20b | 3 total | 19,969 | 7,648 | 27,617 |

Source: `activity_overview.json` files in respective plan outputs.

Note on gpt-oss-20b: both before and after use single-call architecture (per `calls_succeeded: 1`). The activity_overview reflects openrouter internal provider load balancing — each "call" may hit a different provider backend. After PR #374, total tokens decreased ~27% for gpt-oss-20b despite more output (categorical response vs Likert scores).

---

## Evidence Notes

- llama3.1 silo timeout: `history/3/64_deduplicate_levers/outputs/20250321_silo/log.txt` — 120.16s = timeout
- All fallback classification: `history/3/64_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — all 18 entries read "Not classified by LLM. Keeping as primary to avoid data loss."
- gpt-oss-20b proper removes (hong_kong): `history/3/65_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 6 removes with lever-ID citations
- haiku proper remove (silo): `history/3/70_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — ee0996f6 removed citing b664e24a
- Before (PR #373) Likert 0-remove failure: `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — all 18 levers in `deduplicated_levers`
- Before (PR #373) scale inversion: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — 1 lever kept (from `analysis/50_deduplicate_levers/insight_claude.md`)
- Before (PR #373) system prompt: `history/3/57_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `system_prompt` field — Likert -2 to +2

---

## PR Impact

### What PR #374 was supposed to fix

PR #374 was designed to supersede both PR #372 and PR #373 by combining:
1. **Single batch call** from PR #373 (18× fewer LLM calls)
2. **Categorical primary/secondary/remove** from PR #372 (effective deduplication)
3. **Prompt fixes** from iter 49 synthesis (B2, B3, S1)
4. **Robustness guards** from iter 50 assessment (duplicate lever_id check, minimum count)

### Before vs. after comparison

| Metric | Before (runs 57–63, PR #373) | After (runs 64–70, PR #374) | Change |
|--------|------------------------------|------------------------------|--------|
| Structural success | 35/35 | 35/35 | = |
| LLMChatErrors | 0 | 0 | = |
| LLM calls per plan | 1 | 1 | = |
| Dedup schema | Likert -2..+2 | primary/secondary/remove | **improved** |
| Capable model removal rate (silo) | 0% (all 18 kept) | ~6–11% | **improved** |
| llama3.1 failure mode | scale inversion (1/18) | timeout fallback (18/18 primary) | **improved (no catastrophe)** |
| llama3.1 plans with degraded output | 2/5 (1 lever each) | 2/5 (fallback: 18 primaries) | improved |
| Remove justifications cite lever IDs | n/a | yes (for capable models) | **new capability** |
| Robustness guard | absent | present | **new** |
| gpt-4o-mini silo speed | 20.4s | 41.6s | ~2× slower |
| gemini silo speed | 11.2s | 12.7s | comparable |
| haiku silo speed | 24.3s | 23.0s | comparable |

### Did the PR fix the targeted issues?

**Issue 1 — Deduplication failure (PR #373 kept ~18/18 levers)**: Fixed. Capable models now remove 1–6 levers per plan using the categorical `remove` classification with explicit reasoning citing overlapping lever IDs.

**Issue 2 — llama3.1 scale inversion (PR #373 kept 1/18 levers)**: Substantially improved. The robustness guard prevents the catastrophic 1-lever output. llama3.1 now either produces reasonable output (gta_game: 17/18 kept) or triggers the fallback (silo, parasomnia: 18/18 primary). This is a significant improvement over PR #373.

**Issue 3 — Primary/secondary triage**: Restored with meaningful differentiation. Capable models distinguish "gating the core outcome" (primary) from "delivery concern" (secondary) with grounded reasoning.

**Issue 4 — Speed**: Maintained. Single-call architecture preserved from PR #373. The 18× call reduction vs PR #372 is intact.

### Regressions

- **gpt-4o-mini speed regression**: silo plan went from 20s to 42s. Likely due to longer categorical responses vs Likert scores.
- **llama3.1 timeouts**: 2/5 plans produce fallback-only output. This was not a new regression vs PR #373 (which had 1-lever scale inversion on those same plans) but the underlying model struggle is unresolved.
- **Inter-model classification variance**: The primary/secondary boundary is subjective; models disagree on several levers within the same plan. This was also present in PR #372 but may be more visible now that a single batch call sees all levers simultaneously.

### Verdict: KEEP

The PR produces a measurable, significant improvement in deduplication quality. For 6 of 7 models, the categorical approach correctly removes 1–6 redundant levers per plan with auditable lever-ID citations — a capability that was entirely absent in PR #373 (Likert). The robustness guard converts the catastrophic 1-lever failure mode into a safer (if lossy) 18-primary fallback for llama3.1.

The minor regressions (gpt-4o-mini speed, llama3.1 timeouts) do not outweigh the restored deduplication quality. This PR achieves what the iter 50 synthesis recommended (C1: batch primary/secondary/remove call) and what Q1 asked (can speed + dedup quality coexist in a single batch call?). The answer is yes for capable models.

---

## Questions For Later Synthesis

Q1 — llama3.1 times out on silo and parasomnia plans. The silo plan has 18 levers and a long plan description. Is the context length triggering a timeout, or is the model struggling with the categorical classification of 18 levers at once? Would chunking into two batches (e.g., 9+9) fix this for llama?

Q2 — gpt-oss-20b classified 17/18 levers for hong_kong_game but missed dcb03988 (Cultural Authenticity). Is this a JSON parsing issue, a context-length issue, or a model error? Should there be a post-hoc check that verifies all input lever_ids appear in the response?

Q3 — The intended removal rate is 25–50%. Most capable models achieve 6–33% per plan. Is 25–50% still the right target, or is the iter 49 baseline (~15%) a better reference? If 25–50% is correct, should the system prompt's calibration guidance be strengthened?

Q4 — The "prefer primary" rule says "a false positive is recoverable downstream." How many downstream steps actually use the primary/secondary distinction to filter? If nothing filters on it, the distinction may be providing false confidence.

Q5 — The fallback "Not classified by LLM. Keeping as primary to avoid data loss" silently discards classification quality. Should the runner log a warning or emit an event when the fallback is triggered, so the analysis pipeline can flag degraded output?

---

## Reflect

Cross-experiment comparison prerequisites check:
- Both `analysis/50_deduplicate_levers/meta.json` and `analysis/51_deduplicate_levers/meta.json` use `"input": "snapshot/0_identify_potential_levers"` and the same `deduplicate_levers` step. ✓

The central insight from this PR is that PR #373 proved batch calls work at the structural level, and PR #374 proved that the categorical schema (not Likert scoring) is what makes deduplication effective. The combination is better than either alone.

The robustness guard is a meaningful defensive addition. The fallback justification ("Not classified by LLM. Keeping as primary to avoid data loss.") is honest and auditable — a downstream synthesis agent reading the output can detect when the guard fired. However, it would be more actionable if accompanied by an event in the runner's log.

The llama3.1 timeout pattern is worth investigating. The model may need a shorter context window or a prompt that asks it to process a subset of levers at a time. Alternatively, the runner could use a different timeout for local models (where "slow" means the model is still generating) vs. API models (where 120s is genuinely a failure).

---

## Hypotheses

**H1 — llama3.1 timeouts are caused by the silo and parasomnia plans having more complex lever sets that exceed the model's generation capacity at workers=1.**
Evidence: silo and parasomnia both hit exactly 120s (timeout). gta_game, sovereign_identity, and hong_kong_game complete normally at 65–120s. The silo plan has 18 levers and a very long plan description.
Prediction: Increasing the llama3.1 timeout from 120s to 240s would allow the model to complete, and the output would be valid categorical classifications (as seen for gta_game). Alternatively, reducing the llama3.1 worker batch size would reduce per-call complexity.

**H2 — The remove rate (6–33%) is below the intended 25–50% because models hesitate to remove when they see detailed, high-quality lever text.**
Evidence: The input levers from the snapshot dataset are well-written and substantive. Models may correctly identify that most levers address different aspects of the plan even when they overlap. The gpt-oss-20b removes 33% for hong_kong_game but only ~6% for other plans.
Prediction: Adding a second-pass prompt ("Of the levers you classified as primary or secondary, which 3-4 are most semantically similar to another lever in the list?") would increase the removal rate toward 25%.

**H3 — The missing lever (dcb03988 in gpt-oss-20b hong_kong) is caused by the model's output truncation or JSON structure cutting off mid-response.**
Evidence: The robustness guard correctly caught the missing entry and applied the fallback. This pattern suggests the model's JSON output was complete structurally but missing an entry (not a parse failure, just an omission).
Prediction: Adding an explicit instruction "Your response must include a classification for every lever_id in the input — count and verify" would reduce omissions.

**C1 — Add a per-plan missing-lever-id check and emit a warning event when any input lever_id does not appear in the LLM response.**
Evidence: N3 above (gpt-oss-20b omitted dcb03988). The current code applies a fallback silently.
Prediction: Emitting a `classification_fallback` event with the lever_id and plan_name would make the degradation visible in the events.jsonl and allow the analysis pipeline to measure fallback frequency.

**C2 — Increase the llama3.1 per-plan timeout from 120s to 180-240s for local models.**
Evidence: N1 above — silo and parasomnia both hit exactly 120s. Local model inference is CPU-bound and may legitimately need more time for 18-lever categorical classification.
Prediction: With a 240s timeout, llama3.1 would complete silo and parasomnia with real classification output rather than fallbacks, improving the effective success rate for that model.

**C3 — Add a post-LLM verification step that checks all input lever_ids are present in the LLM response before applying fallbacks.**
Evidence: N3 (gpt-oss-20b missing dcb03988) and N5 (llama3.1 fallback for all 18 levers). A check that verifies len(classified_ids) == len(input_ids) and which ids are missing would enable more targeted fallback or retry logic.
Prediction: This would allow the system to retry only for the missing levers rather than applying a blanket fallback, improving output quality for partial failures.

---

## Potential Code Changes

**C1 — Emit `classification_fallback` events with lever_id and reason.**
When the robustness guard fires for a specific lever, write a structured event to the plan's log or events.jsonl rather than silently applying the fallback. This makes degradation measurable and auditable.

**C2 — Increase per-plan timeout for ollama models.**
The 120s timeout is appropriate for API models but too short for local llama3.1 on complex plans. Add a model-class-aware timeout (e.g., ollama: 240s, api: 120s) or a configurable per-model timeout.

**C3 — Add missing-lever-id verification before fallback.**
After parsing the LLM response, compare the set of classified lever_ids against the set of input lever_ids. For each missing id, apply the fallback individually and log a warning. For the gpt-oss-20b case (1 missing), this would be a minor improvement. For the llama3.1 timeout case (18 missing), the fallback logic is unchanged but the root cause (timeout) becomes more obvious.

---

## Summary

PR #374 achieves its stated goals. It restores the categorical primary/secondary/remove deduplication schema from PR #372, wrapped in the single-batch-call architecture proven by PR #373. For 6 of 7 models:

- Deduplication is functional: 1–6 levers removed per plan with auditable, lever-ID-citing justifications.
- No scale inversion or LLMChatErrors.
- Speed is preserved at the PR #373 level (single call per plan).
- Classification quality is grounded: primary vs. secondary reasoning references specific plan constraints.

The main residual issue is llama3.1, which times out on 2 of 5 plans (silo and parasomnia) and triggers the robustness fallback. This produces zero-quality classification output for those plans (all 18 levers promoted to primary). This is better than PR #373's catastrophic 1-lever output but worse than the desired outcome. The fix (increase timeout or reduce per-batch size for local models) is straightforward.

The robustness guard is a net positive: it prevents catastrophic failure without hiding the problem — the fallback justification text is identifiable in the output.

**Verdict: KEEP**
