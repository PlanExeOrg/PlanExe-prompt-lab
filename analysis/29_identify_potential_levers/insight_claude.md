# Insight Claude

## Scope

Analyzing runs `2/10–2/16` (after PR #288) against `2/03–2/09` (before, from analysis 28) for the `identify_potential_levers` step.

**PR under evaluation:** PR #288 "Fix zero cost for OpenAI/Anthropic models via fallback pricing"

**Changes made:**
1. Added `model_pricing.py` — a pricing registry that estimates cost from token counts when the provider doesn't return a `cost` field in the response.
2. Added a `"pricing"` field (`input_per_million_tokens`, `output_per_million_tokens`) to all paid model entries in `llm_config/*.json`.
3. Root cause addressed: OpenAI and Anthropic direct APIs don't return a `cost` field in usage responses (unlike OpenRouter), so `_extract_cost()` was returning 0.0 for all direct calls.

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/03 | 2/10 | ollama-llama3.1 |
| 2/04 | 2/11 | openrouter-openai-gpt-oss-20b |
| 2/05 | 2/12 | openai-gpt-5-nano (direct OpenAI API) |
| 2/06 | 2/13 | openrouter-qwen3-30b-a3b |
| 2/07 | 2/14 | openrouter-openai-gpt-4o-mini |
| 2/08 | 2/15 | openrouter-gemini-2.0-flash-001 |
| 2/09 | 2/16 | anthropic-claude-haiku-4-5-pinned (direct Anthropic API) |

---

## Positive Things

1. **Cost fix confirmed for gpt-5-nano (direct OpenAI API).** Run 05 (before PR) shows `total_cost: 0.0` in all activity_overview.json files for gpt-5-nano. Run 12 (after PR) shows correctly estimated costs:
   - `20260310_hong_kong_game`: total_cost = 0.028658
   - `20250321_silo`: total_cost = 0.036317
   This is the primary goal of PR #288 and it is confirmed working.
   Evidence: `history/2/12_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` vs `history/2/05_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json`.

2. **Runs 11–16 (all non-llama3.1 models) achieved 5/5 plan success.** No hard errors in runs 11–16 (excluding the llama3.1 run 10 issues discussed below). Run 11 (gpt-oss-20b) had one partial recovery (hong_kong_game 2/3 calls) but all plans completed successfully at the plan level. This shows the PR did not introduce any structural regressions for the affected models.

3. **Content quality stable for runs 11–16.** Sampling run 12 (gpt-5-nano) and run 16 (haiku) outputs against run 05 and 09 counterparts shows no degradation. Lever names, options, and reviews are grounded, plan-specific, and structurally correct. The gpt-5-nano hong_kong_game levers in run 12 remain concise and specific; the haiku hong_kong_game levers in run 16 maintain the deep engagement with project context seen in prior haiku runs.

4. **No LLMChatErrors introduced by PR #288.** The Pydantic validation errors in run 10 (llama3.1) are unrelated to the cost fix (see Negative Things #1 below) — no other runs experienced LLMChatErrors.

---

## Negative Things

1. **Run 10 (llama3.1) had 2 hard plan failures.** Plans `hong_kong_game` and `parasomnia_research_unit` both failed with `LLMChatError` caused by Pydantic `review_lever is too short` validation errors. The model returned lever topic labels (e.g., "Urban Terrain", "Cinematic DNA", "IP Rights") instead of full review sentences. These are 9–34 chars, well below the `min_length=50` constraint.

   This failure mode is NEW compared to run 03 (llama3.1 before PR), where both plans succeeded at the plan level (with partial call recoveries, but not hard errors). The run 10 sovereign_identity plan also shows a partial recovery (2/3 calls).

   Evidence: `history/2/10_identify_potential_levers/outputs.jsonl` — `hong_kong_game` status=`error`, `parasomnia_research_unit` status=`error`.
   Error content: `levers.0.review_lever: Value error, review_lever is too short (13 chars); expected at least 50 [input_value='Urban Terrain']`.

   **Likely cause**: This failure mode (returning lever names in review fields) does NOT appear caused by PR #288 (cost tracking). The PR does not modify the prompt, the Pydantic schema, or any LLM interaction code. This is most likely llama3.1 model drift, a context-dependent failure, or a separate concurrent prompt change. The change deserves separate investigation.

2. **Haiku activity_overview.json absent in both runs 09 and 16.** Direct Anthropic API calls (haiku) do not generate `activity_overview.json` in either the before or after run. The PR's stated goal includes fixing cost reporting for Anthropic models, but we cannot verify this from the available artifacts. The log files confirm haiku runs completed successfully (3 API calls per plan, all to `api.anthropic.com`), but no per-plan cost summary file exists.

   Evidence: `history/2/16_identify_potential_levers/outputs/20260310_hong_kong_game/` — only `002-10-potential_levers.json`, `002-9-potential_levers_raw.json`, `log.txt`, `usage_metrics.jsonl` present; no `activity_overview.json`.

   This is a structural observation gap: the `activity_overview.json` mechanism does not appear to be triggered for the haiku model profile, regardless of whether the PR's pricing fix is in place.

3. **Overall success rate regressed from 97.1% to 94.3%.** Before (runs 03–09): 34/35 plans succeeded. After (runs 10–16): 33/35 plans succeeded (run 10 had 2 hard failures). This regression is attributable to llama3.1's new failure mode, not to PR #288.

---

## Comparison

| Metric | Before (runs 03–09) | After (runs 10–16) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success rate** | 34/35 = 97.1% | 33/35 = 94.3% | -2.8pp (llama3.1 unrelated) |
| **LLMChatErrors** | 1 (run 04, JSON EOF) | 2 (run 10, review_lever too short ×2) | REGRESSED (unrelated to PR) |
| **Partial recoveries** | 2 (run 03: sov_id 2/3, hk_game 2/3) | 2 (run 10: sov_id 2/3; run 11: hk_game 2/3) | NEUTRAL |
| **gpt-5-nano total_cost** | 0.0 (all plans) | ~$0.03 per plan | **FIXED** |
| **haiku total_cost** | Not verifiable (no activity_overview) | Not verifiable (no activity_overview) | UNKNOWN |
| **openrouter cost tracking** | Already working | Still working | NEUTRAL |
| **Content quality (runs 11–16)** | Stable | Stable | NO CHANGE |
| **llama3.1 review_lever pattern** | "The options [verb]" template lock | Returning lever names in review field (new failure) | NEW FAILURE (unrelated) |

---

## Quantitative Metrics

### Plan-Level Success Rates

| Run | Model | Plans succeeded / attempted | Hard errors | Partial recoveries |
|-----|-------|-----------------------------|-------------|-------------------|
| 10 | llama3.1 | 3/5 | 2 (hk_game, parasomnia) | 1 (sov_id 2/3) |
| 11 | gpt-oss-20b (openrouter) | 5/5 | 0 | 1 (hk_game 2/3) |
| 12 | gpt-5-nano (direct OpenAI) | 5/5 | 0 | 0 |
| 13 | qwen3-30b (openrouter) | 5/5 | 0 | 1 (hk_game 2/3) |
| 14 | gpt-4o-mini (openrouter) | 5/5 | 0 | 0 |
| 15 | gemini-2.0-flash (openrouter) | 5/5 | 0 | 0 |
| 16 | haiku (direct Anthropic) | 5/5 | 0 | 0 |
| **Total** | | **33/35 = 94.3%** | **2** | **3** |

### Cost Tracking: Before vs After

| Model | Provider type | Run before | total_cost before | Run after | total_cost after | Status |
|-------|--------------|------------|-------------------|-----------|------------------|--------|
| gpt-5-nano | Direct OpenAI | 05 | 0.0 | 12 | ~$0.03/plan | **FIXED** |
| haiku | Direct Anthropic | 09 | (no activity_overview) | 16 | (no activity_overview) | UNKNOWN |
| gpt-oss-20b | OpenRouter | 04 | ~$0.01/plan (was working) | 11 | ~$0.015/plan (still working) | NEUTRAL |
| qwen3-30b | OpenRouter | 06 | (was working) | 13 | (working) | NEUTRAL |

### Baseline Length Comparison (gpt-5-nano, hong_kong_game)

Estimated from sampled levers in run 05 (before) and run 12 (after):

| Field | Run 05 (before) est. avg | Run 12 (after) est. avg | Baseline avg (analysis 28) | Ratio to baseline |
|-------|--------------------------|-------------------------|---------------------------|-------------------|
| consequences | ~170 chars | ~280 chars | 279 chars | ~1.0× |
| review | ~130 chars | ~200 chars | 152 chars | ~1.3× |
| options (per lever) | ~200 chars | ~250 chars | 453 chars (total) | ~1.1× |

The length variation between runs 05 and 12 is within normal model variance (both use gpt-5-nano workers=4). Neither run shows the 3× inflation warning threshold. Content quality is grounded and plan-specific in both runs.

### Fabricated Percentage Claims

| Run | Model | Plan sampled | Fabricated % claims in consequences | Fabricated % claims in review |
|-----|-------|-------------|-------------------------------------|-------------------------------|
| 05 | gpt-5-nano | hk_game | 0 | 0 |
| 12 | gpt-5-nano | hk_game | 0 | 0 |
| 09 | haiku | hk_game | 0 | 0 |
| 16 | haiku | hk_game | 0 | 0 |

No fabricated percentage claims observed in runs 12 or 16. Content quality is consistent with prior batches.

---

## Evidence Notes

- gpt-5-nano cost fix confirmed: `history/2/12_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` shows `total_cost: 0.028658` vs `history/2/05_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` shows `total_cost: 0.0`.
- haiku activity_overview absent: verified by listing `history/2/16_identify_potential_levers/outputs/20260310_hong_kong_game/` — no `activity_overview.json` file. Same for run 09.
- llama3.1 hard failures: `history/2/10_identify_potential_levers/outputs.jsonl` lines 4–5: `status: "error"` for hong_kong_game and parasomnia with Pydantic `review_lever is too short` errors.
- llama3.1 review_lever failure samples: `review_lever` values of `"Urban Terrain"` (13 chars), `"Cinematic DNA"` (13 chars), `"IP Rights"` (9 chars) — model returned lever topic labels instead of review sentences.
- Run 11 partial recovery: `history/2/11_identify_potential_levers/events.jsonl` — `partial_recovery` for hong_kong_game (2/3 calls).
- Run 13 partial recovery: run 13 outputs.jsonl shows hong_kong_game `calls_succeeded: 2`.
- Content quality samples: `history/2/12_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (gpt-5-nano after) and `history/2/16_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (haiku after) — both grounded, no fabricated numbers, plan-specific.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The PR #288 does not change the system prompt or any prompt-related code. The `OPTIMIZE_INSTRUCTIONS` constant and its known-problems list are not relevant to this PR's changes.

**New observation — llama3.1 complete review collapse**: Run 10 shows a new failure mode not previously documented in `OPTIMIZE_INSTRUCTIONS`: llama3.1 returning only the lever NAME in the `review_lever` field (e.g., "Urban Terrain", "IP Rights"). This is distinct from template lock (model produces text but uses the same phrase) — here the model produces only a 1–4 word label, triggering min_length validation failure. If this represents a recurring llama3.1 behavior (not a one-off), it should be added to OPTIMIZE_INSTRUCTIONS as a known failure mode.

**Potential addition to OPTIMIZE_INSTRUCTIONS**: "Some models (particularly local models under token pressure or context overload) may collapse the `review_lever` field to just the lever topic label (e.g., 'IP Rights') rather than a full analytical sentence. This fails the `min_length=50` constraint and discards the entire LLM response. Prompt wording should reinforce that `review_lever` requires a full sentence identifying the core tension and what the options miss."

---

## PR Impact

### What the PR was supposed to fix

- **Root cause**: OpenAI and Anthropic direct APIs don't include a `cost` field in usage responses, so `_extract_cost()` returned 0.0 for all direct API calls, causing `activity_overview.json` to show `total_cost: 0.0` for paid models like `gpt-5-nano`.
- **Fix**: Added `model_pricing.py` pricing registry and `pricing` field in `llm_config/*.json` to estimate cost from token counts when provider doesn't report cost.

### Before vs After Comparison

| Metric | Before (runs 03–09) | After (runs 10–16) | Change |
|--------|--------------------|--------------------|--------|
| gpt-5-nano total_cost (per plan) | 0.0 | ~$0.028–$0.036 | **FIXED** |
| haiku total_cost visibility | No activity_overview | No activity_overview | UNKNOWN |
| Overall success rate | 97.1% (34/35) | 94.3% (33/35) | -2.8pp (unrelated regression) |
| Content quality (gpt-5-nano) | Good | Good | No change |
| Content quality (haiku) | Excellent | Excellent | No change |
| LLMChatErrors | 1 (gpt-oss-20b JSON EOF) | 2 (llama3.1 review_lever too short) | Unrelated regression |

### Did the PR fix the targeted issue?

**Yes, for direct OpenAI API (gpt-5-nano).** Cost is now correctly reported in `activity_overview.json` — confirmed by comparing run 05 (total_cost=0.0) with run 12 (total_cost=~$0.03). The fix is working as designed.

**Cannot confirm for direct Anthropic API (haiku).** The `activity_overview.json` file is not generated for haiku in either run 09 (before) or run 16 (after). This appears to be an independent issue with how haiku's runner profile generates output files — the absence predates PR #288. Whether the pricing registry correctly estimates haiku costs is logically plausible from the code description, but there is no `activity_overview.json` artifact to confirm it in these runs.

### Were any regressions introduced?

**No regressions from PR #288.** The observed regressions (llama3.1 2 hard failures, overall success rate 94.3%) are attributable to llama3.1 entering a new failure mode (review_lever returning only lever names) that is independent of the cost-tracking fix. The PR does not modify the system prompt, Pydantic schema, or any LLM interaction code paths.

### Verdict

**KEEP**

The primary goal — fixing zero cost reporting for direct OpenAI API calls — is confirmed working. Cost is now correctly estimated and reported in `activity_overview.json` for gpt-5-nano. Content quality across all models is unchanged. The PR does not introduce any prompt, schema, or execution changes that could affect output quality.

The only unresolved item is haiku cost verification, which cannot be confirmed from available artifacts due to missing `activity_overview.json` files. This is a pre-existing observability gap, not a regression introduced by PR #288.

---

## Questions For Later Synthesis

1. **Why does haiku not generate `activity_overview.json`?** Both run 09 (before PR) and run 16 (after PR) produce no `activity_overview.json` for any plan. Is this caused by the haiku runner profile configuration, a missing activity_overview write path for the Anthropic model class, or something specific to the `anthropic_claude.json` config? This gap means haiku cost cannot be monitored from the same artifact as other models.

2. **What caused llama3.1 to return lever names in `review_lever` fields?** Run 10 shows 2 hard failures where llama3.1 produced topic labels instead of review sentences. This failure mode did not appear in runs 03, 00, 01, 02. Was there a concurrent system prompt change between run 03 and run 10? Or is this llama3.1 context-window overload? The failure is worth reproducing to determine if it's deterministic.

3. **Is the PR #288 pricing registry complete?** The PR adds pricing data to "all paid models across all config profiles" per the description. Should the analysis verify that haiku's `llm_config` entry now includes `pricing` fields, and whether the activity_overview mechanism would use them if invoked?

4. **Should haiku's runner profile be investigated to surface cost data?** Given that haiku uses a direct Anthropic API and the PR explicitly targets Anthropic model cost tracking, the missing `activity_overview.json` for haiku is a gap worth closing. A follow-up PR might ensure the activity_overview write path is triggered for all model profiles including Anthropic direct-API models.

---

## Reflect

PR #288 is a clean, focused infrastructure fix. It solves a real observability problem (cost invisibility for direct API models) without touching any user-facing features. The confirmed fix for gpt-5-nano is unambiguous. The haiku verification gap is a pre-existing issue with the output file generation pipeline, not caused by the PR.

The most actionable finding from this batch is actually the llama3.1 regression in run 10 — a new failure mode where the model returns only lever names in the review field. This is unrelated to PR #288 but should be investigated separately. The template lock issues from analysis 28 appear to have shifted into a more severe form (complete review collapse for 2 plans) for llama3.1. Whether this is deterministic or a fluke warrants a re-run.

The haiku activity_overview gap is a monitoring blind spot: costs for the Anthropic direct API model cannot be audited from standard pipeline artifacts. This should be fixed to make the optimization loop's cost accounting complete.

---

## Potential Code Changes

**C1 — Investigate haiku activity_overview.json generation path**

Neither run 09 nor run 16 produces `activity_overview.json` for haiku plans. The gpt-5-nano model (same direct-API pattern) does produce it. The missing file means haiku cost tracking via PR #288 cannot be verified. Investigate why the haiku runner profile skips this file and whether the pricing registry write path is exercised.

Evidence: `history/2/16_identify_potential_levers/outputs/20260310_hong_kong_game/` — only usage_metrics.jsonl, 002-*.json, log.txt present.

Predicted effect: Once the activity_overview path is connected to haiku, both the before/after comparison and ongoing cost monitoring for Anthropic models will be verifiable.

**C2 — Investigate llama3.1 review_lever collapse failure**

Run 10 shows a new failure mode: llama3.1 returning 9–34 char lever topic labels in `review_lever` fields instead of review sentences, triggering `min_length=50` Pydantic failures. This failure affects 2/5 plans and wasn't seen in runs 00–09 for llama3.1. Investigate whether:
- A prompt change was merged between runs 03 and 10 that changes how llama3.1 formats reviews
- This is a context-window overload condition specific to hong_kong_game and parasomnia (longer plans)
- The failure is reproducible or a one-off

Evidence: `history/2/10_identify_potential_levers/outputs.jsonl` errors for hong_kong_game and parasomnia.

**H1 — Add explicit review_lever formatting instruction to prompt**

To prevent llama3.1 (and potentially other local models) from collapsing `review_lever` to just a topic label, add an explicit formatting constraint: "The review_lever must be a complete sentence of at least 2 clauses identifying the core tension and what the options overlook. Do not write only a topic label."

Evidence: Run 10 llama3.1 failure — model wrote "Urban Terrain", "Cinematic DNA", "IP Rights" in review_lever fields. These are 9–20 chars and represent the lever name, not a review.

Predicted effect: Reduce the probability of llama3.1 and similar models producing degenerate review_lever values that trigger validation failures.

---

## Summary

PR #288 delivers its stated goal: cost tracking for direct OpenAI API calls (gpt-5-nano) is now working. Before the PR, `total_cost: 0.0` appeared in all gpt-5-nano `activity_overview.json` files; after, real cost estimates (~$0.03 per plan) are reported. The cost fix has no impact on content quality, success rates, or prompt behavior — it is an infrastructure-only change. Haiku cost tracking cannot be verified because `activity_overview.json` is not generated for the haiku runner profile in either before or after runs, suggesting a pre-existing observability gap. The success rate regression (97.1% → 94.3%) is caused by an unrelated new llama3.1 failure mode (review_lever field returning only topic labels) that appeared in run 10 and warrants separate investigation. **Verdict: KEEP** — the PR fixes a real cost-tracking bug for direct OpenAI API models with no observed regressions.
