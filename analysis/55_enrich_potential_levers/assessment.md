# Assessment: Add per-batch retry for enrich step, update OPTIMIZE_INSTRUCTIONS

## Issue Resolution

**What the PR was supposed to fix**: PR #452 addressed three items:
- **B1**: Add per-batch retry — split failing batches in half and retry rather than aborting the plan. Primary target: recover gpt-oss-20b from 0/5 success caused by output token overflow on BATCH_SIZE=5.
- **B4**: Fix `runner.py:_run_enrich` to report actual `batches_succeeded` instead of hardcoded `1`.
- **D5**: Document two new known problems in `OPTIMIZE_INSTRUCTIONS`: consequence echoing without elaboration, and UUID cross-reference format inconsistency.

**Is the issue resolved?**

**B1 — Partially.** The retry mechanism works and recovered gpt-oss-20b from 0/5 to 2/5 plans. The silo plan's `usage_metrics.jsonl` for run 93 directly confirms the mechanism: one batch produced exactly 8192 output tokens (invalid JSON at DeepInfra), triggering a split into two sub-batches that each succeeded on Amazon Bedrock (`1968 in / 3201 out` and `2139 in / 7504 out`). The gta_game plan also recovered via the same path.

However, the root cause is unaddressed: `BATCH_SIZE=5` produces output that overflows gpt-oss-20b's 8192-token hard limit on virtually every batch, because its `context_window=3900` and the verbose enrichment format (consequences+review added by PR #451) generates output near or at the cap. Three plans (sovereign_identity, hong_kong_game, parasomnia) now fail after consuming the full 600s budget via retry cascades rather than failing quickly as in run 86.

**B4 — Yes.** Confirmed: all after-PR runs (92–98) report actual batch counts (`calls_succeeded: 3` for silo plans, `4` for gta_game plans with 20 levers). Before-PR runs (85–91) all reported `calls_succeeded: 1` regardless of actual batch count.

**D5 — No runtime impact.** OPTIMIZE_INSTRUCTIONS is developer documentation only; the two new entries (consequence echoing, UUID format inconsistency) are not injected into the runtime system prompt. Content quality for all 6 working models is unchanged between runs 85–91 and 92–98 (all within ±7% variation, within normal stochastic range for non-deterministic LLM outputs).

**Residual symptoms**:
- Three gpt-oss-20b plans now always timeout at 600s instead of failing fast (~30s before). This consumes ~1800s of extra runner time per test run with no added value.
- UUID cross-reference at `enrich_potential_levers.py:168` unchanged: D5 documented the problem but the one-line code fix was not included. Confirmed in run 92 (llama3.1): conflict_text contains `(9bc93565-67b1-49fc-afb9-4d310510f698)` — a full 36-char UUID.

---

## Quality Comparison

All 7 models appear in both batches (runs 85–91 before, runs 92–98 after). The only material behavioral change is gpt-oss-20b (0/5 → 2/5). All other 6 models show field-length changes within ±7% of their run 85–91 values — within normal stochastic variation for non-deterministic models with no prompt changes.

| Metric | Before (runs 85–91) | After (runs 92–98) | Verdict |
|--------|---------------------|-------------------|---------|
| **Overall success rate** | 30/35 (85.7%) | 32/35 (91.4%) | **IMPROVED** (+2 plans via retry) |
| **gpt-oss-20b success** | 0/5 | 2/5 (3 timeout at 600s) | **PARTIALLY IMPROVED** |
| **All other models success** | 30/30 (100%) | 30/30 (100%) | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 100% | 100% | UNCHANGED |
| **Template leakage** | None (eliminated by PR #451) | None | UNCHANGED |
| **Review format compliance** | Not measured | Not measured | N/A |
| **Consequence chain format** | N/A (pass-through field) | N/A | N/A |
| **Content depth — llama3.1 description** | 316 chars (0.65× baseline) | 339 chars (0.70× baseline) | Marginal IMPROVED (still below 0.75×) |
| **Content depth — gpt-5-nano description** | 658 chars (1.36× baseline) | 647 chars (1.34× baseline) | UNCHANGED (within noise) |
| **Content depth — qwen3-30b description** | 372 chars (0.77× baseline) | 375 chars (0.78× baseline) | UNCHANGED |
| **Content depth — gpt-4o-mini description** | 482 chars (1.00× baseline) | 492 chars (1.02× baseline) | UNCHANGED |
| **Content depth — gemini description** | 456 chars (0.94× baseline) | 456 chars (0.94× baseline) | UNCHANGED |
| **Content depth — haiku description** | 568 chars (1.17× baseline) | 581 chars (1.20× baseline) | UNCHANGED |
| **Field length vs baseline — all models** | 0.65–1.36× | 0.70–1.34× | UNCHANGED (no model > 2×) |
| **Cross-call duplication** | Not reported | Not reported | N/A |
| **Over-generation count** | N/A | N/A | N/A |
| **Fabricated quantification** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Not detected | Not detected | UNCHANGED |
| **CJK character contamination** | 1 (run 88, qwen3-30b, silo) | 0 | **IMPROVED** (stochastic) |
| **UUID refs in text (llama3.1)** | Present | Present (unchanged) | UNCHANGED |
| **calls_succeeded reporting** | Hardcoded `1` for all plans | Actual batch counts (3–4) | **IMPROVED** |
| **gpt-oss-20b timeout behavior** | Fast fail (~30s) for 3/5 failing plans | 600s timeout for 3/5 failing plans | **REGRESSED** (runner efficiency) |
| **LLMChatError count** | 0 | 0 | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS alignment**: D5 accurately documents two observed failure modes (consequence echoing, UUID format). Neither entry has a runtime effect — they are self-improve guidance only. The UUID code fix documented in D5 remains unimplemented at line 168. A further addition warranted: document that `BATCH_SIZE=5` is too large for models with `context_window < 6000` — this would help future iterations recognize the adaptive batch size need as a known infrastructure constraint.

---

## New Issues

1. **gpt-oss-20b always-slow-timeout** (N1, N3 in insight): Three plans that previously failed fast (~30s each) now consume the full 600s budget via retry cascades. Total runner time for gpt-oss-20b increased from ~1862s (3 fast-fails + 2 never-ran) to ~2200s (3×600s + 195s + 229s) per run. This is a regression in runner efficiency — more time wasted, same failure outcome for 3/5 plans.

2. **No retry depth limit** (B1 in code review): `enrich_potential_levers.py:239–246` splits batches indefinitely — a batch of 5 that consistently fails can cascade to 9 LLM calls (5+2+1+1) before reaching single-lever skip. No depth counter exists. For gpt-oss-20b, each failing call takes 30–60s, which fills the plan budget before the cascade terminates.

3. **No remaining-time guard** (B2 in code review): Sub-batches are inserted unconditionally at `pending_batches.insert(0, ...)` regardless of elapsed time. If 580s of a 600s budget have been consumed, retries are still queued and the plan will timeout rather than gracefully stopping.

4. **UUID code fix deferred from D5**: OPTIMIZE_INSTRUCTIONS now explicitly documents `full_lever_context_str` UUID exposure as a known problem (lines 87–91), but `enrich_potential_levers.py:168` still reads `f"- {lever.lever_id}: {lever.name}"`. The documentation and code are inconsistent. Confirmed in run 92: llama3.1 conflict_text contains full 36-char UUIDs.

5. **Silent partial success within a "succeeded" batch** (B4 in code review): If an LLM returns 3/5 levers from a "succeeded" batch, `batches_succeeded` is incremented and the 2 missing levers are silently dropped (excluded at line 254, logged as errors). No retry is triggered for the missing levers. The caller sees `status="ok"` with fewer enriched levers than the input.

---

## Verdict

**CONDITIONAL**: Keep the PR for the B4 fix (calls_succeeded reporting), which is clean and unambiguously correct. Keep the B1 retry as a safety net, but it requires immediate follow-up to be net-positive for gpt-oss-20b: the 3 recovered-by-timeout plans are not recoverable within 600s regardless of retry strategy, and the retry cascade now wastes 1800s per run on them. The three required follow-ups are:

1. **Adaptive BATCH_SIZE** based on `context_window` (eliminates gpt-oss-20b root cause — BATCH_SIZE=2 would likely recover all 5 plans without any retries)
2. **Retry depth limit (max 1 split) + remaining-time guard** (prevents 3×600s timeout accumulation for non-recoverable plans)
3. **UUID fix at line 168** (one-line change — closes the gap between D5 documentation and code)

---

## Recommended Next Change

**Proposal**: Add adaptive BATCH_SIZE based on model `context_window`, bundled with the UUID fix at line 168 and retry guards (depth limit + time check). In `runner.py`'s `_run_enrich`, detect the model's context window via a metadata probe before calling `execute()`, then pass `batch_size=2` when `context_window < 6000`. At line 168, change `f"- {lever.lever_id}: {lever.name}"` to `f"- {lever.name}"`. In the retry handler (lines 239–246), add a depth counter stored alongside each pending batch and skip retry when `depth >= 1`; also add a `time.monotonic() < deadline - safety_margin` check before inserting sub-batches.

**Evidence**: Convincing on all three changes. gpt-oss-20b's `context_window=3900` and `num_output=8192` are confirmed from run 93 metadata. Usage metrics for the silo plan confirm that one batch produced exactly 8192 output tokens (the hard limit) before failing — this is systematic at BATCH_SIZE=5, not stochastic. The UUID issue is confirmed by direct inspection of run 92 (llama3.1 conflict_text: `(9bc93565-67b1-49fc-afb9-4d310510f698)`). D5 in the merged PR already declares this a known problem. The retry depth issue is confirmed by run 93 events.jsonl (3 plans timeout at exactly 600s, not early). All three fixes are source-code verified and have low-risk implementations.

**Verify**:
- gpt-oss-20b (equivalent of run 93): Confirm 5/5 plans succeed with BATCH_SIZE=2. No retries should trigger. Usage_metrics should show output tokens consistently below 8192 per batch. Plans should complete in ~300–400s, not 600s.
- gpt-oss-20b: Confirm description quality is preserved at BATCH_SIZE=2 — spot-check descriptions in sovereign_identity and hong_kong_game plans (which timed out in run 93) to verify rich, grounded content comparable to the silo plan in run 93.
- llama3.1 (equivalent of run 92): Confirm full UUID strings no longer appear in synergy_text and conflict_text after line 168 fix. Look for name-only references like `"conflicts with Knowledge Preservation Strategy"` instead of `"conflicts with Knowledge Preservation Strategy (9bc93565-67b1-49fc-afb9-4d310510f698)"`.
- qwen3-30b: Check whether UUID format inconsistency (name-only vs full UUID across plans) is resolved. Run 95 had no CJK leak; verify that also holds in the next run.
- All models: Verify `calls_succeeded` counts remain accurate. For gpt-oss-20b with BATCH_SIZE=2, expect higher batch counts per plan (≈8 for 15 levers vs 3 before).
- Monitor for residual UUID contamination: `lever.lever_id` still appears in `lever_details_for_prompt` at line 171 (`f"Lever ID: {lever.lever_id}\n"`). If UUID refs persist in llama3.1 or qwen3-30b outputs after the line 168 fix, the `Lever ID:` label in the batch details is the remaining source and may need to be removed in a follow-up.

**Risks**:
- BATCH_SIZE=2 means gpt-oss-20b makes ~8 LLM calls per plan (vs 3 at BATCH_SIZE=5). This increases provider latency and cost for gpt-oss-20b specifically. For other models, batch size is unchanged — no cost impact.
- The metadata probe implementation adds one extra LLM API call per plan run unless `llm.metadata` is accessible without a call. The synthesis suggests two approaches: (a) a pre-flight metadata call in `runner.py` before `execute()`, or (b) accessing `llm.metadata` inside `execute_function`. Option (b) avoids the extra call but requires the batch size decision to be made inside the function. Prefer option (b) if possible.
- After line 168 fix: if any downstream code parses UUID patterns from synergy/conflict text to extract lever relationships, those parsers will break. This would be a pre-existing bug (haiku, gpt-4o-mini, gpt-5-nano already use name-only references), but worth checking.
- Retry depth limit (max 1 split) means a batch that would have recovered via a second split now fails faster. This is acceptable — the benefit of fast failure outweighs the marginal recovery gain from a second split.

**Prerequisites**: None for the UUID fix. Adaptive BATCH_SIZE requires access to `llm.metadata["context_window"]` — available inside `execute_function` per the code review. Retry guards are independent of batch size.

---

## Backlog

**Resolved — remove from backlog**:
- B1 (no per-batch retry): Addressed by PR #452. Mechanism works (2/5 gpt-oss-20b plans recovered); root cause fix (adaptive batch size) is the next step.
- B4 (calls_succeeded hardcoded to 1): Fully resolved by PR #452.

**Open — carry forward**:
- **C1 (critical)**: Adaptive BATCH_SIZE based on `context_window` — eliminates gpt-oss-20b root cause. `enrich_potential_levers.py:95`. Priority 1. Bundle with C2 and C3.
- **C2 (high)**: Retry depth limit (max 1 split) + remaining-time guard — prevents 3×600s timeout pattern. `enrich_potential_levers.py:239–246`. Bundle with C1.
- **C3 (high)**: Fix UUID in `full_lever_context_str` at line 168 — one-line change (`f"- {lever.name}"`). D5 documentation already merged but code not updated. Bundle with C1.
- **H1 (medium)**: Add anti-echoing clause to description guidance in `ENRICH_LEVERS_SYSTEM_PROMPT` — llama3.1 still at 0.70× baseline description length (target ≥0.75×). `enrich_potential_levers.py:144`. Defer until batch-size and UUID work is verified; test as an isolated iteration to measure effect cleanly.
- **D3 / Direction 4 (content quality)**: Qualitative mechanism guidance for synergy/conflict fields. qwen3-30b still at 0.74–0.76× baseline for synergy/conflict — the highest remaining content quality gap for working models. The "(40-60 words)" quantitative target provides no guidance on what those words should contain. Defer.
- **B3 (data integrity)**: Silent partial success within a "succeeded" batch — if LLM returns 3/5 levers, `batches_succeeded` is incremented and 2 levers are silently dropped. Add post-batch comparison and `levers_skipped` field in `PlanResult`; emit a `partial_recovery` event. Lower urgency than C1–C3.
- **B5 (silent lever drop at enriched_levers_map)**: `enrich_potential_levers.py:252–260` logs errors for incomplete enrichment but returns no count to caller. No minimum threshold enforced. Downstream steps receive fewer levers than expected silently.
- **S1–S3 (latent, low priority)**: Concurrency bugs in runner.py (late-binding closure capture `enrich_potential_levers.py:210–220`, global dispatcher cross-contamination `runner.py:248–250`, unsafe list mutation `runner.py:280–282`). Not triggered at `workers=1`. Address before enabling parallel workers.
- **I5 (documentation)**: `check_option_count` validator accepts >3 options despite "Exactly 3" field description. Intentional per inline comment — update field description to ">= 3 options" to match actual policy.
