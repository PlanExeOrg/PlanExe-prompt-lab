# Assessment: Adaptive batch size, guarded retry, and max_tokens bump for enrich step

## Issue Resolution

**What the PR was supposed to fix** (from PR #453 description):

| Claim | Status |
|-------|--------|
| C1 — max_tokens bump for gpt-oss-20b (8192 → 128000) to fix output truncation | **PARTIAL** |
| C2 — Adaptive batch size (batch_size=2 when num_output < 16384) | **FLAWED** (C1 disables it for gpt-oss-20b) |
| B4 — Guarded retry (depth=1, 300s budget) to prevent unbounded cascade | **YES** |
| D5 — Accurate batch counting | Duplicate credit — already fixed by PR #452 |
| OPTIMIZE_INSTRUCTIONS updates | Duplicate credit — already added by PR #452 |

**B4 (guarded retry) — fully resolved**: The 3×600s timeout cascade from PR #452 is completely
eliminated. Before PR #453, gpt-oss-20b spent ~2224s per run on timeouts (3 plans × 600s each).
After, failing plans abort in <2s each via fast `empty_response`, reducing total runner time to
~520s — a 4.3× improvement.

Evidence: `history/4/00_enrich_potential_levers/outputs/20260308_sovereign_identity/usage_metrics.jsonl`
shows 3 calls, all `"error": "empty_response"` in <0.7s each. Compare with
`history/3/93_enrich_potential_levers/outputs.jsonl` which shows 3 plans at exactly 600s each.

**C1 (max_tokens bump) — partially resolved**: For gta_game and silo, gpt-oss-20b now produces
complete, well-formed JSON (3173–7924 output tokens per batch). The truncation-at-8192-tokens
barrier is gone for providers that accept the large `max_tokens` setting. Confirmed in
`history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — 7
well-formed levers with full content.

However, 3 plans (sovereign_identity, hong_kong_game, parasomnia) still fail. The likely cause:
`max_tokens=128000 >> context_window=3900` — some OpenRouter providers enforce the actual model
limit and reject requests that specify a wildly larger output budget, returning `empty_response`
instead of truncating. The C1 bump may have overcorrected.

Evidence: `history/4/00_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`
contains `"characterized_levers": []` — empty output, zero levers enriched.

**C1/C2 interaction — design bug**: By inflating `max_tokens` to 128000 (C1), `num_output`
(which LlamaIndex derives from `max_tokens`) became 128000. C2's check
`num_output < SMALL_OUTPUT_THRESHOLD (16384)` is therefore `128000 < 16384 = False`, silently
disabling the protective batch-size reduction for the exact model it was intended to help.
gpt-oss-20b runs with `batch_size=5` in all after runs.

Evidence: `history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
metadata: `"context_window": 3900, "num_output": 128000`. The model uses full `BATCH_SIZE=5`.

**Residual symptoms**: gpt-oss-20b remains at 2/5 functional success. The failure mode improved
(timeout → fast empty_response) but the underlying problem — an output-constrained model being
fed batches too large for its actual context window — is unresolved.

---

## Quality Comparison

**Critical caveat — input data changed**: Analysis 54 used `snapshot/1_deduplicate_levers`
(78 levers, 14–18 per plan), while analysis 56 uses `baseline/train` (35 levers, 5–8 per plan).
Per-lever field length averages remain comparable, but batch count, throughput, and total volume
metrics are confounded. Improvements in per-lever field lengths for some models may reflect
simpler input levers rather than PR #453 changes specifically.

All 7 models appear in both batches: llama3.1 (85→99), gpt-oss-20b (86→4/00), gpt-5-nano
(87→4/01), qwen3-30b (88→4/02), gpt-4o-mini (89→4/03), gemini-flash (90→4/04), haiku (91→4/05).

| Metric | Before (runs 85–91, analysis 54) | After (runs 99/4/00–4/05, analysis 56) | Verdict |
|--------|-----------------------------------|----------------------------------------|---------|
| **Success rate (status)** | 31/35 (88.6%) | 35/35 (100%) | IMPROVED |
| **Success rate (functional)** | 31/35 (88.6%) | 32/35 (91.4%) | UNCHANGED |
| **gpt-oss-20b plans succeeded** | 0/5 (truncation errors) | 2/5 (3/5 empty_response) | PARTIALLY IMPROVED |
| **gpt-oss-20b runner time** | ~1862s | ~520s | IMPROVED 4.3× |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Template leakage** | None (eliminated by PR #451) | None | UNCHANGED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |
| **Fabricated % claims (new)** | 0 | 0 new fabrications | UNCHANGED |
| **% claims echoed from input** | N/A | 36/209 (17%) appearing in desc fields | APPARENT INCREASE — all are echoes of input `consequences` numbers, not new fabrications; a form of consequence echoing |
| **Marketing-copy language** | Not measured | Not measured | N/A |
| **llama3.1 desc length ratio** | 0.65× baseline | 0.76× baseline | IMPROVED |
| **gpt-5-nano desc length ratio** | 1.36× baseline | 1.41× baseline | UNCHANGED (noise) |
| **qwen3-30b desc length ratio** | 0.77× baseline | 0.96× baseline | IMPROVED (partially confounded by input change) |
| **gpt-4o-mini desc length ratio** | 1.00× baseline | 1.13× baseline | SLIGHT INCREASE, within range |
| **gemini desc length ratio** | 0.94× baseline | 1.12× baseline | IMPROVED (partially confounded) |
| **haiku desc length ratio** | 1.17× baseline | 1.25× baseline | UNCHANGED (noise) |
| **gpt-oss-20b desc length ratio** | 0/5 (no data) | 1.36× (2/5 success) | IMPROVED for successful plans |
| **haiku synergy/conflict length** | syn 1.59×, conf 1.64× | syn 1.66×, conf 1.71× | SLIGHTLY INCREASED, still within 2× limit |
| **qwen3-30b synergy/conflict** | syn 0.74×, conf 0.76× | syn 0.81×, conf 0.85× | IMPROVED (partially confounded) |
| **UUID contamination (llama3.1)** | 96% (75/78 levers) | 89% (31/35 levers) | MARGINAL IMPROVEMENT (C3 still unimplemented) |
| **UUID contamination (gpt-oss-20b)** | ~36% (5/14 levers) | 53% (8/15 levers) | APPARENT INCREASE (limited data, stochastic) |
| **UUID contamination (qwen3-30b)** | 29% (23/78 levers) | 6% (2/35 levers) | IMPROVED (smaller batches reduce UUID copy probability) |
| **UUID contamination (gemini)** | 32% (25/77 levers) | 34% (12/35 levers) | STOCHASTIC (no trend; run 96 from PR #452 showed 0%) |
| **UUID contamination (haiku)** | 6% (5/78 levers) | 3% (1/35 levers) | MARGINAL IMPROVEMENT |
| **UUID contamination (gpt-5-nano)** | 4% | 0% | IMPROVED |
| **C2 adaptive batch (gpt-oss-20b)** | N/A | Disabled by C1 (bug) | NEW BUG |
| **C2 adaptive batch (other models)** | N/A | Correctly triggers batch_size=2 | NEW IMPROVEMENT |
| **Retry depth limit** | Absent | depth=1, 300s budget | FIXED |

**Content quality summary**: No model exceeds the 2× verbosity warning threshold. All models
improved or held steady on field length ratios. The 36 percentage claims appearing in
descriptions are echoes of numbers already present in the input `consequences` field —
documented as consequence echoing in OPTIMIZE_INSTRUCTIONS, not new fabrications. UUID
contamination (llama3.1 89%, gemini 34%) remains the dominant content quality problem and is
unrelated to PR #453.

**OPTIMIZE_INSTRUCTIONS alignment**: The current OPTIMIZE_INSTRUCTIONS (lines 28–93) already
documents consequence echoing (lines 82–87) and UUID cross-reference format inconsistency
(lines 88–92) — both added by PR #452. The C1/C2 `max_tokens`/`context_window` conflation
revealed by this PR is not yet documented. The code at line 190 still reads
`f"- {lever.lever_id}: {lever.name}"` (C3 unfixed), confirming the UUID entry is still
accurate but the fix is still outstanding.

---

## New Issues

**N1 — C1/C2 interaction bug (new)**: The max_tokens bump in C1 inflated `num_output` to
128000 for gpt-oss-20b, making C2's `num_output < 16384` threshold permanently false for that
model. C2 now protects every model EXCEPT the one it was designed for. The correct metric is
`context_window` (the model's actual per-call token budget), which remains 3900 for gpt-oss-20b
regardless of max_tokens. Code location: `enrich_potential_levers.py:181`.

**N2 — max_tokens overcorrection causing provider rejections (new)**: Setting
`max_tokens=128000 >> context_window=3900` may cause OpenRouter providers that enforce the
actual model limit to return `empty_response` rather than truncate. The 3 failing plans
(sovereign_identity, hong_kong_game, parasomnia) all fail via empty_response in <1s, suggesting
upstream rejection. A more conservative bump (e.g., max_tokens=32000 or 65536) would clear the
old 8192 truncation limit while staying closer to provider expectations.

**N3 — Input data change breaks comparison chain**: The runner was switched from
`snapshot/1_deduplicate_levers` to `baseline/train`, violating the cross-experiment comparison
prerequisite. Content quality improvements observed for qwen3-30b, gemini, and gpt-4o-mini
cannot be cleanly attributed to PR #453 vs. the simpler input levers.

**N4 — Duplicate credit in PR description**: The PR description claims D5 (accurate batch
counting) and OPTIMIZE_INSTRUCTIONS updates as changes introduced by PR #453. Both were
already implemented by PR #452 (confirmed in analysis 55 runs 92–98). The PR description is
misleading for audit purposes, though the implementations themselves are correct.

**Previously latent issue surfaced**: The `_run_plan_task` thread filter bug
(`runner.py:543–548`) captures the outer thread's ident but plan work runs in an inner
`ThreadPoolExecutor`. Per-plan `log.txt` files are nearly empty. This was introduced by the
timeout-wrapping mechanism in PR #452 or #453 and becomes visible when debugging is needed.

---

## Verdict

**CONDITIONAL**: Keep PR #453 for the guarded retry (clear win: 4.3× reduction in wasted
runner time), but schedule C4 (context_window threshold fix) and C3 (UUID strip) as immediate
follow-ups before the next optimization iteration.

**Justification**:

The guarded retry is the strongest change in the PR: it is correctly implemented, has no
design flaws, and measurably eliminates the 1800s timeout waste from PR #452. This alone
justifies keeping the PR.

The max_tokens bump (C1) is partially correct — it restored output for 2/5 gpt-oss-20b plans —
but it introduced the C1/C2 interaction bug and may be causing provider rejections for the
remaining 3 plans. The C2 adaptive batch logic is not wrong in isolation; it was undermined by
C1's side-effect on `num_output`. Neither change should be reverted, but C4 (adding a
`context_window` check to C2's condition) is needed to close the loop.

gpt-oss-20b's functional success rate is unchanged at 2/5 — the improvement is operational
(fast-fail vs. timeout) not functional. The PR makes the system behave more efficiently but
does not actually fix the content delivery gap for this model.

**Conditions for full YES**:
1. C4: Fix C2 threshold to check `context_window < SMALL_CONTEXT_THRESHOLD` in addition to
   `num_output`. This will route gpt-oss-20b (context_window=3900) to batch_size=2 regardless
   of max_tokens.
2. C3: Strip UUID from `full_lever_context_str` at line 190. This is orthogonal to PR #453
   and was documented as a priority in analysis 55.

---

## Recommended Next Change

**Proposal**: Strip UUIDs from `full_lever_context_str` (C3) — one-line change at
`enrich_potential_levers.py:190` from `f"- {lever.lever_id}: {lever.name}"` to
`f"- {lever.name}"`. This is the synthesis recommendation from analysis 56.

**Evidence**: The evidence is strong and multi-sourced. llama3.1 synergy/conflict fields contain
full UUIDs in 89% of levers (confirmed in `history/3/99_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
— e.g., "Ethical Oversight Framework has strong synergy with the Resource Management Philosophy
`(ccd48764-fc2c-4926-82a0-fb54ff5f00dc)`"). Gemini shows 34% UUID rate in analysis 56 (12/35
levers), with wide stochastic variance. The UUID appears in the full-list context string
(`enrich_potential_levers.py:190`) but serves no purpose in free-text output — only names are
needed for human-readable synergy/conflict references. The per-lever batch prompt at lines
213–219 still includes `lever.lever_id`, so the `enriched_levers_map` lookup mechanism is
unaffected by the change. Both agents agree on this finding with no disagreement.

**Verify**:
- Primary: After C3, check that llama3.1's UUID contamination rate drops from 89% toward <5%
  across all 5 plans. Check `history/*/synergy_text` and `conflict_text` for any remaining
  UUID-format strings (`[0-9a-f]{8}-[0-9a-f]{4}-…`).
- Secondary: Verify gemini's UUID rate drops from ~34% toward 0%. Gemini showed high variance
  (0% in run 96, 32–34% in other runs) — a consistent drop after C3 would confirm the
  context string was the cause rather than stochastic routing.
- Lever matching: Confirm `enriched_levers_map` lookups still succeed at 100% (no lever silently
  dropped due to the change). The UUID is still in the per-batch prompt so the LLM should still
  echo it back correctly.
- Content quality: Check that removing UUIDs from the context does not affect description,
  synergy, or conflict text quality for models that were already clean (gpt-5-nano 0%, haiku 3%).

**Risks**:
- The `enriched_levers_map` key is `lever.lever_id`, and the LLM must echo back the UUID in
  `LeverCharacterization.lever_id` for the lookup to succeed. After C3, the full-list context no
  longer shows UUIDs. If any model stops echoing UUIDs in `lever_id` (because it only sees the
  name in context), those levers will be silently dropped (S2 bug). To monitor: check that
  `batches_succeeded` in `events.jsonl` matches expected batch counts after C3.
- Small models (llama3.1) might shift from UUID copy to name-only references in synergy/conflict,
  which is the desired behavior. However, if they also stop echoing the `lever_id` UUID in the
  JSON response, levers get dropped. A safeguard: add a `lever_id` format check in the assembly
  step to surface this early.

**Prerequisite issues**:
C3 is orthogonal to C4 and can be implemented independently. It does not depend on resolving
the C1/C2 interaction bug. However, both C3 and C4 should be confirmed as part of the same
analysis iteration to get a clean before/after comparison.

**Note**: The synthesis also defers C4 (context_window threshold fix) immediately after C3. If
C4 is bundled with C3 in one PR, verify that gpt-oss-20b now triggers `batch_size=2` by checking
its adaptive batch log entries. A gpt-oss-20b functional success rate improvement from 2/5 toward
5/5 is the primary success metric for C4.

---

## Backlog

### Resolved (removable):
- **B4 (timeout cascade)**: Unbounded retry cascade causing 3×600s timeouts for gpt-oss-20b.
  Fixed by guarded retry in PR #453. Remove from backlog.
- **C1 (gpt-oss-20b max_tokens truncation at 8192)**: The 8192 hard truncation barrier is
  removed. The PR partially addresses this — 2/5 plans succeed. The remaining 3/5 failures are
  a different mechanism (empty_response, likely from C1/C2 interaction bug). Replace the
  "truncation at 8192" entry with the narrower "max_tokens overcorrection / empty_response"
  issue below.

### Remaining:
- **C3 (UUID in `full_lever_context_str`)**: `enrich_potential_levers.py:190`. llama3.1 89%,
  gemini 34% UUID contamination. One-line fix. **Highest priority.**
- **C4 (C2 threshold uses wrong metric)**: `enrich_potential_levers.py:181` uses `num_output`
  instead of `context_window` for adaptive batch size. Disables C2 protection for gpt-oss-20b.
  Fix: `if num_output < SMALL_OUTPUT_THRESHOLD or context_window < SMALL_CONTEXT_THRESHOLD`.
  **Second priority.**
- **max_tokens overcorrection (new)**: gpt-oss-20b `max_tokens=128000 >> context_window=3900`
  may cause provider rejections (empty_response). If C4 alone does not restore 5/5 success,
  reduce `max_tokens` from 128000 to ~32000 or 65536 in `baseline.json`.
- **I3 (anti-echoing instruction)**: llama3.1 description at 0.76× baseline, still below 1.0×.
  Add explicit anti-echoing directive to `ENRICH_LEVERS_SYSTEM_PROMPT` description field.
- **D3 (qualitative mechanism guidance for synergy/conflict)**: qwen3-30b synergy/conflict is
  still terse (0.81–0.85×). Add mechanism-level guidance to field descriptions.
- **B3 (English-phrase bans in `consequences` field description)**: `identify_potential_levers.py:113–119`
  names forbidden phrases inline, violating OPTIMIZE_INSTRUCTIONS "field-description template lock"
  guidance. Rewrite to describe what is wanted structurally.
- **OPTIMIZE_INSTRUCTIONS: max_tokens/context_window confusion**: Document the C1/C2 interaction
  trap so future self-improve agents do not repeat it. Add entry: "max_tokens vs context_window
  confusion. `num_output` reflects LlamaIndex's `max_tokens` setting, not the model's actual
  context window. Batch-size decisions must check `context_window`, not `max_tokens`/`num_output`."
- **S2 (silent lever drop on UUID mismatch)**: `enrich_potential_levers.py:248–255`. If LLM
  echoes wrong lever_id, lever silently dropped. Add UUID format check before map lookup.
- **S3 (false-positive partial_recovery warning)**: `runner.py:131`. Fires on normal 2-call
  completions. Lower threshold to `< 2` or distinguish early-stop from recovery.
- **B4-log (thread filter captures wrong thread)**: `runner.py:543–548`. Per-plan `log.txt`
  files nearly empty because filter captures outer thread ident, not inner executor thread.
