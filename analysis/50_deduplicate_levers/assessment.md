# Assessment: feat: single-call Likert scoring for deduplicate_levers (PR #373)

## Issue Resolution

**What the PR was supposed to fix:**
PR #373 replaces 18 sequential per-lever LLM calls with a single batch call. Each of the 18 input levers is scored on a 5-point Likert scale (−2 to +2) based on relevance to the plan. Levers scoring ≥1 are kept; levers scoring ≤0 are removed. The PR description states it "supersedes PR #372."

**Is the issue resolved?**
The speed goal is fully achieved: 1 call instead of 18, with measured speedups of 1.5–6.3× across plans and models (silo gpt-oss-20b: 196.6s → 51.0s, parasomnia haiku: ~120s → 24.3s). All 35 runs parsed successfully (35/35 `status: ok`).

However, the deduplication purpose of the step is not resolved — it is broken by the approach:

1. **Relevance ≠ deduplication.** The Likert prompt asks "How relevant is this lever to this specific plan?" not "Is this lever redundant with another lever?" A lever can be highly relevant to a plan AND fully redundant with another. Capable models (gpt-oss-20b, qwen3, haiku, gemini, gpt-4o-mini) score overlapping levers at 1–2 and keep them both. Before (PR #372), gpt-oss-20b correctly removed 2 overlapping levers from the silo plan (`de8ff746` Technological Integration Strategy into `99e29b00`, and `ee0996f6` Information Dissemination Protocol into `b664e24a`). After, the same model scores both pairs 1 and keeps all 18.
   Evidence: `history/3/51_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (2 `remove` entries) vs `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (0 scores ≤0, all 18 in `deduplicated_levers`).

2. **llama3.1 inverts the Likert scale catastrophically.** On silo (run 57) and gta_game (run 57), llama3.1 scores 17 of 18 levers as −1 or −2, while the justifications say "highly relevant." Only 1 lever survives. This is complete scale inversion: the scores are the opposite of the text.
   Evidence confirmed in `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`: lever `9ed3015e` (Agricultural System Design), score=−2, justification: "This lever is **highly relevant** to the project plan." Same pattern for levers `91eadbb9`, `125ce960`, `55d11248`, `9bc93565`, `51e3a6e2`, `f14b8361`, `ee0996f6`, `36621fe3`, `19e66d20`. The single survivor is `a6d45d69` (Resource Allocation Strategy, score=1).

**Residual symptoms of the original issue:**
None of the issues originally targeted by the PR (speed) are residual — speed is achieved. But the original functionality of the step (deduplication) is now absent for capable models and catastrophically broken for llama3.1.

---

## Quality Comparison

All 7 models appear in both batches (runs 50–56 before, runs 57–63 after), on the same 5 plans.

Note: many metrics in the template are properties of the upstream `identify_potential_levers` generation step and are passed through unchanged by `deduplicate_levers`. These are marked **N/A (upstream)** — the dedup step cannot improve or degrade them.

| Metric | Before (PR #372, runs 50–56) | After (PR #373, runs 57–63) | Verdict |
|--------|------------------------------|------------------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLM calls per plan** | 18 (sequential) | 1 (batch) | IMPROVED |
| **Duration, silo (gpt-oss-20b)** | 196.6s | 51.0s (3.9×) | IMPROVED |
| **Duration, parasomnia (haiku est.)** | ~120s | 24.3s (>5×) | IMPROVED |
| **Avg levers kept (silo, capable models)** | ~16/18 | ~17/18 | REGRESSED (less dedup) |
| **Dedup quality (gpt-oss-20b, silo)** | 2 overlapping levers removed with explicit overlap reasoning | 0 levers removed (both overlapping pairs scored 1, kept) | REGRESSED |
| **Dedup quality (haiku, hong_kong_game)** | 7/18 removed (39%) | ~4/18 removed (22%); insight_claude estimated ~1 — actual file shows 4 score≤0 | REGRESSED |
| **llama3.1, silo** | 18/18 kept (no dedup) | 1/18 kept (scale inversion) | CATASTROPHIC REGRESSION |
| **llama3.1, gta_game** | ~16–18/18 kept | 1/18 kept (scale inversion) | CATASTROPHIC REGRESSION |
| **Explicit overlap citation** | All `remove` entries cite absorbing lever UUID | No equivalent field; no explicit overlap citation | REGRESSED |
| **Primary/secondary triage** | Present (score 2→primary, 1→secondary via `_score_to_classification`) | Present (same mapping preserved) | UNCHANGED |
| **Calibration guidance compliance** | N/A (PR #372) | gpt-oss-20b ignores "Expect 25–50% to score ≤0" — all 18 scored ≥1 | REGRESSED (new failure) |
| **Cross-call duplication** | 18 calls per plan — potential for cross-call duplicate names | 1 batch call — structural elimination | IMPROVED |
| **Bracket placeholder leakage** | ~0 (upstream step) | ~0 (upstream step) | N/A (upstream) |
| **Option count violations** | Upstream step | Upstream step | N/A (upstream) |
| **Lever name uniqueness** | Upstream step | Upstream step | N/A (upstream) |
| **Template leakage** | Upstream step | Upstream step | N/A (upstream) |
| **Review format compliance** | Upstream step | Upstream step | N/A (upstream) |
| **Consequence chain format** | Upstream step | Upstream step | N/A (upstream) |
| **Content depth** | Upstream step | Upstream step | N/A (upstream) |
| **Over-generation count** | N/A (dedup step) | N/A (dedup step) | N/A |
| **Field length vs baseline** | baseline/train/ is empty — no comparison possible | baseline/train/ is empty | N/A |
| **Fabricated quantification** | Upstream step | Upstream step | N/A (upstream) |
| **Marketing-copy language** | Upstream step | Upstream step | N/A (upstream) |

**OPTIMIZE_INSTRUCTIONS alignment:**
The goal of the pipeline (per `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS) is realistic, feasible, actionable plans. The dedup step's role is to reduce the lever set so downstream steps receive a focused, non-redundant input. PR #373 breaks this: capable models now pass all 18 levers through unchanged, so EnrichLevers and FocusOnVitalFewLevers receive a noisier, more redundant input than before. This works against actionability. The llama3.1 1-lever pathology is even worse: downstream steps designed for 8–15 levers receive a degenerate 1-lever list, producing a plan built on a single dimension.

---

## New Issues

**N1 — Architectural flaw: relevance ≠ deduplication (no code fix possible without redesign).**
The prompt asks "How relevant is this lever to this specific plan?" Capable models correctly answer this question and score all marginally relevant levers at 1–2. The step can no longer detect redundancy between pairs of levers unless one of them is so marginal that it scores 0 — a condition that rarely fires when both levers address real project concerns. This is not a prompt-wording bug; it is a category error in the scoring schema.

**N2 — llama3.1 Likert scale inversion (catastrophic, undetected).**
On silo and gta_game, llama3.1 writes "highly relevant" in justifications but assigns −2 scores. The code has no sanity check. The run records `status: ok`. The 1-lever output is silently passed downstream.

**N3 — Silent LLM failure falls back to all-primary output with `status: ok` (B1 in code_claude).**
If the batch LLM call throws any exception other than `PipelineStopRequested`, `batch_result` stays `None`, all levers default to score=2 (primary), and `runner.py` returns `calls_succeeded=1`. The caller cannot distinguish a genuine success from a silent fallback.

**N4 — Duplicate lever_id in model response overwrites first entry silently (B2 in code_claude).**
Confirmed in run 57 (llama3.1, hong_kong_game): lever `32ad06c5` appears twice in the response. The dict comprehension at line 255 takes the last entry. The lever is kept with a nonsensical justification ("This lever is a duplicate of another lever and should not be scored separately.").

**N5 — No minimum lever count guard (B4 in code_claude).**
When llama3.1 produces 1 surviving lever, the code records success and writes the output. Downstream steps receive a degenerate input. A `len(output_levers) < max(3, len(input_levers) // 4)` check would surface this.

**N6 — `calls_succeeded` hardcoded to 1 regardless of actual LLM outcome (B5 in code_claude).**
`runner.py` always returns `calls_succeeded=1` from `_run_deduplicate`, even when the LLM call failed and the fallback fired. Monitoring pipelines that rely on `calls_succeeded` to detect failures will not catch this.

**N7 — Dead code in `_score_to_classification` type annotation (B3 in code_claude).**
Return type is `Literal["primary", "secondary", "remove"]` but `"remove"` is unreachable (function only called when `score >= 1`). Contradicts `OutputLever.classification: Literal["primary", "secondary"]`. Latent type-safety issue.

**Surfaced latent issue: iter 49 prompt bugs B2, B3, S1 still unaddressed.**
The iter 49 synthesis recommended fixing: (B2) contradictory `primary` fallback instruction, (B3) template-lock in `secondary` definition, (S1) calibration anchored to 15 levers. PR #373 superseded PR #372 without applying any of these fixes. They must be incorporated in the recommended next PR.

---

## Verdict

**NO**: PR #373 achieves its stated speed goal (18→1 LLM call, 1.5–6.3× faster) but introduces two severe quality regressions — deduplication failure for all capable models (relevance scoring cannot detect redundancy), and catastrophic 1-lever output for llama3.1 on at least 2 of 5 plans — making it a net negative that should be reverted.

---

## Recommended Next Change

**Proposal:**
Restore the `primary/secondary/remove` taxonomy from PR #372 as the classification schema, but keep the single batch-call architecture from PR #373. All 18 levers are submitted in one LLM call; each lever receives a `classification` label (primary / secondary / remove) rather than a Likert score. The filter changes from `score < 1` to `classification == "remove"`. Also incorporate the three iter-49 prompt fixes (B2, B3, S1) and the two robustness guards (minimum lever count, duplicate lever_id dedup) in the same PR.

**Evidence:**
- The batch architecture is proven: all 7 models successfully parse `BatchDeduplicationResult` in one call (PR #373 runs 57–63, 35/35 success).
- The primary/secondary/remove schema produced meaningful deduplication before: 15% remove rate across 630 decisions in iter 49 (cross_iteration_verdict.md). All three categories fully exercised.
- The Likert approach produces 0% effective deduplication for capable models (gpt-oss-20b silo: 0/18 removed after, 2/18 before) and catastrophic results for llama3.1 (1/18 kept after).
- Categorical labels (primary/secondary/remove) cannot be numerically inverted; the llama3.1 polarity-reversal failure mode is structurally impossible with the PR #372 schema.
- Iter 49 synthesis `## Recommendation` (confirmed by both agents in analysis/50): "fixing the template-lock trigger and the contradictory fallback instruction will raise llama3.1's remove rate on sovereign_identity from 0 toward the 3–5 expected."

**Verify in the next iteration:**
1. **gpt-oss-20b, silo**: Confirm that `de8ff746` (Technological Integration Strategy) and `ee0996f6` (Information Dissemination Protocol) are again classified `remove` with explicit absorbing lever IDs in justification. This was the regression confirmed against `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`.
2. **llama3.1, sovereign_identity**: The B3 template-lock fix should produce >0 `remove` entries (was 0/18 in run 50 before, and 17/18 scale-inverted in run 57 after). Expect 3–5 removals after the fix.
3. **llama3.1, silo and gta_game**: Verify no scale-inversion pathology (>75% negative scores). The categorical schema makes this impossible by construction, but verify the `deduplicated_levers` count is ≥8.
4. **All models, all plans**: Verify the minimum-lever guard emits no warnings (i.e., no run produces fewer than 5 surviving levers).
5. **Calibration compliance**: Verify that gpt-oss-20b and qwen3 no longer keep all 18 levers. Before-fix, both scored everything 1–2 on silo. The updated calibration text ("Expect to remove 25–50% of input levers") should increase remove rates for conservative models.
6. **Duration**: Verify the single-batch architecture is preserved. The `calls_succeeded` field in `outputs.jsonl` should report 1 for successful runs, 0 for fallback-triggered runs (once B5 is fixed).

**Risks:**
- **Weaker models in batch mode**: llama3.1 may struggle to apply primary/secondary/remove consistently when all 18 levers appear simultaneously in one prompt. In the per-lever mode (PR #372), the model evaluated one lever at a time. In batch mode, the model must compare 18 levers against each other. llama3.1's performance on sovereign_identity (0 removes, template-lock) suggests it already struggles to discriminate; the batch context may make this worse. Monitor sovereign_identity specifically.
- **Token budget**: Submitting all 18 levers plus the full plan context in a single prompt is larger than any single call in the 18-call approach. For plans with long lever descriptions (e.g., hong_kong_game), the combined prompt may approach context limits for models with smaller windows (llama3.1: 131K per `metadata` field — should be fine, but verify).
- **B2 prompt fix regression**: Replacing the contradictory `primary` fallback instruction may cause some models to classify fewer levers as primary (if they were relying on the "last resort = primary" interpretation). Watch for models that shift from the expected ~58% primary rate to significantly lower.
- **Duplicate lever_id guard**: The `seen_decision_ids` check keeps the first entry on duplicates. If llama3.1 returns a corrected version of a lever as the second entry (as it did in run 57 hong_kong_game with the self-referential justification), the first (potentially wrong) entry wins. Log a warning so these cases are visible.

**Prerequisite issues:**
None of the recommended changes depend on other unmerged work. The batch architecture is already proven feasible. The iter-49 prompt fixes (B2, B3, S1) are independent prompt-text changes. The code guards (min lever count, duplicate lever_id) are additive.

---

## Backlog

**Resolved from before (iter 49):** None. The iter 49 bugs (B2: contradictory fallback, B3: template-lock secondary definition, S1: 15-lever calibration) were never addressed — PR #373 superseded PR #372 instead. These remain open and must be incorporated in the next PR.

**Carry forward from iter 49:**
- **B2**: Contradictory `primary` fallback instruction in `deduplicate_levers.py:102`. Fix: replace "only as a last resort / classify as primary to avoid data loss" with two-case guidance (uncertain primary/secondary → prefer primary; uncertain remove/keep → prefer secondary).
- **B3**: Template-lock in `secondary` definition in `deduplicate_levers.py:91`. Fix: replace the memorizable dictionary phrase with a conditional test question ("If this lever were ignored entirely, would the project fail or succeed in a fundamentally different way?").
- **S1**: Removal calibration anchored to 15 levers in `deduplicate_levers.py:106`. Fix: replace with proportional guidance ("Expect to remove 25–50% of input levers").
- **B1 (runner)**: False `partial_recovery` events for normal 2-call runs (`runner.py:125, 546–552`). Fix: change threshold from `< 3` to `< 2`.

**New issues to add:**
- **B4 (new)**: No minimum-lever-count guard after `deduplicate_levers`. Confirmed: llama3.1 silo/gta_game produce 1/18 surviving levers with `status: ok`. Add `len(output_levers) >= max(3, len(input_levers) // 4)` check with `logger.warning()`.
- **B-dedup (new)**: Duplicate `lever_id` in model response overwrites first entry silently (confirmed run 57, hong_kong_game). Add `seen_decision_ids: set[str]` check, keep first entry, log warning.
- **B-silent (new)**: Silent LLM failure propagates as `status: ok` with all-primary fallback. Fix: expose `calls_succeeded` from `DeduplicateLevers.execute()`, emit `partial_recovery` event on fallback in `runner.py`.
- **S1 (new — identify_potential_levers)**: `Lever.consequences` field description names banned phrases ("Controls ... vs.", "Weakness:") in the LLM-facing schema, contradicting `OPTIMIZE_INSTRUCTIONS` guidance. Fix: rephrase to describe what the field should contain, not what it must not copy.

**Closed:**
- llama3.1 degenerate Risk-Framing collapse (iter 49 issue): Was eliminated by PR #372 and does not reappear under PR #373 (llama3.1's failure mode changed to scale inversion, not catch-all collapse). Closed.
