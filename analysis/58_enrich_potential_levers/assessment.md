# Assessment: Adaptive batch size, guarded retry, and gpt-oss-20b config fix for enrich step

## Issue Resolution

**PR #455 targeted five distinct problems:**

### 1. gpt-oss-20b BadRequestError (max_tokens 8192→65536, context_window=131072)
**RESOLVED.** The "LLM batch interaction failed." errors that killed all 5 gpt-oss-20b plans
in run 86 are completely gone in run 14. All 5 plans produce valid `002-12-enriched_levers_raw.json`
files with 0 errors. Verified: run 14 / gta_game metadata shows `context_window=131072,
num_output=65536`. gta_game and parasomnia complete with `status=ok` at 136–146 s. The
root cause (8192 max_tokens leaving only ~3 K input headroom → BadRequestError) is
eliminated.

**Residual symptom:** 3 of 5 plans (hong_kong_game, silo, sovereign_identity) still receive
`status=error` with "plan timeout after 600s". This is a *different* failure mode than
before — the enrichment finishes and the output is written to disk, but LLMExecutor's
provider failover sequence (6–9 attempts × 60–90 s each) exhausts the orchestrator's 600 s
ceiling. The enriched lever files are usable; only the pipeline status is wrong.

### 2. Adaptive batch size (batch_size=2 when context_window < SMALL_CONTEXT_THRESHOLD=6000)
**PARTIAL — with unintended regression.** The feature was designed to help gpt-oss-20b
(which before this PR reported a small default context_window). After the config fix in
change 1, gpt-oss-20b now correctly reports `context_window=131072` and is NOT in the
small-batch path. However, llama_index's `OpenRouter_LLM` returns `context_window=3900`
universally for all OpenRouter-proxied models. Since 3900 < 6000, batch_size=2 fires for
qwen3-30b (~32 K actual context), gpt-4o-mini (128 K actual), and gemini-flash (1 M
actual) — three models that do not need it. Verified: run 17 / silo metadata shows four
entries each with `context_window=3900` (4 batches for 7 levers, 2 levers/batch). The
adaptive feature now protects nothing and penalises three unrelated models.

### 3. Guarded retry (pending_batches loop with depth=1 and MAX_RETRY_BUDGET_SECONDS=300)
**PARTIAL.** The retry infrastructure correctly prevents hard batch failures from
propagating and operates cleanly for the 6 non-gpt-oss-20b models. The `MAX_RETRY_BUDGET_SECONDS`
guard only fires in the `except Exception` path — it does not cap time spent inside a
single successful (but slow) `llm_executor.run()` call. For gpt-oss-20b, each call may
internally run 6–9 provider attempts before succeeding, consuming the full plan budget
without ever reaching the retry budget check.

### 4. Error tracking (errors field in JSON output)
**RESOLVED.** Run 13 (llama3.1) shows the feature working correctly: two `unknown_lever_id`
and two `incomplete` errors for UUID-mutated lever IDs are recorded in
`002-12-enriched_levers_raw.json`. Before this PR, such failures were silent.

### 5. OPTIMIZE_INSTRUCTIONS updates (three new entries)
**RESOLVED.** Consequence echoing, UUID cross-reference format inconsistency, and max_tokens
overflow are all documented. These align with findings from analysis 54 and give future
iterations a clear rationale.

---

## Quality Comparison

> **⚠️ Input data warning:** Before runs (3/85–91, from PR #451 experiments) used
> `snapshot/1_deduplicate_levers` (15–18 levers/plan). After runs (4/13–19) use
> `baseline/train` (7–8 levers/plan). All metrics that scale with lever count — field
> lengths, percent-claim totals, cross-call duplication counts — are confounded by this
> difference. Only structural/categorical metrics can be reliably compared.

All 7 models appear in both batches and are used for comparison.

| Metric | Before (runs 85–91) | After (runs 13–19) | Verdict |
|--------|---------------------|--------------------|---------|
| **Success rate (status=ok)** | 30/35 (85.7%) | 32/35 (91.4%) | IMPROVED |
| gpt-oss-20b status=ok | 0/5 | 2/5 | IMPROVED |
| gpt-oss-20b valid output files on disk | ~1/5 (partial, truncated) | 5/5 | IMPROVED |
| BadRequestError events | 2 (run 86) | 0 | IMPROVED |
| Error tracking field present | No | Yes (operational) | IMPROVED |
| OPTIMIZE_INSTRUCTIONS entries | 6 | 9 | IMPROVED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | No duplicates | No duplicates | UNCHANGED |
| **Template leakage** (post-PR#451) | 0 | 0 | UNCHANGED |
| **Review format compliance** (`Controls X vs Y`) | Consistent | Consistent | UNCHANGED |
| **Consequence chain format** (`Immediate → Systemic → Strategic`) | Present in inputs | Present in inputs | UNCHANGED |
| **Marketing-copy language** | None observed | None observed | UNCHANGED |
| **OpenRouter batch API calls/plan** | 1 (full batch) | 3–4 (batch_size=2) | REGRESSED |
| **Fabricated percent claims** | 0 | 45 total (gpt-4o-mini 16, haiku 16, others 2–6) | CONFOUNDED |
| **Field length vs baseline** | 0.65–1.19× range | higher (7–8 levers vs 15–18) | CONFOUNDED |
| **Cross-call duplication** | Low | Low | UNCHANGED |
| **Over-generation (>7 levers/call)** | N/A (batch_size=5, 5/5 levers/call) | Not observed | UNCHANGED |
| llama3.1 UUID mutations | Silent (no tracking) | 4 errors visible in run 13 | SURFACED |

**Notes on confounded metrics:**

*Fabricated percent claims (45 total after):* This increase cannot be attributed to PR #455.
The `baseline/train` consequences fields contain explicit percentages (e.g. "30% reduction in
innovative output", "15% increase in black market activity") that are absent or rarer in the
`snapshot/1_deduplicate_levers` input used for before runs. Verified in run 17 / silo output:
every description echoing a percentage copies it directly from the consequences field in
`baseline/train/20250321_silo/002-10-potential_levers.json`. This is consequence-echoing
(documented in OPTIMIZE_INSTRUCTIONS after PR #455, entry 1) not fabrication — the numbers
originate in the input data. Causal direction cannot be isolated without controlling for
input data.

*Field length vs baseline:* After runs show longer average fields than before, but this is
expected — fewer levers per plan (7–8 vs 15–18) means each lever receives more per-call
attention. Ratios cannot be meaningfully compared across this input change.

*OpenRouter batch API calls:* This is a confirmed regression, not a confound. The 3–4
calls/plan for qwen3-30b, gpt-4o-mini, and gemini-flash (vs 1 before) result directly from
the adaptive batch_size=2 bug (SMALL_CONTEXT_THRESHOLD=6000 > OpenRouter's 3900 fallback).
Verified: run 17 silo shows `calls_succeeded=4` in outputs.jsonl; before-run 89 shows
`calls_succeeded=1`.

---

## New Issues

### C1 — Adaptive batch_size=2 triggered for all OpenRouter models (regression introduced)
The `SMALL_CONTEXT_THRESHOLD=6000` constant at `enrich_potential_levers.py:112` exceeds
llama_index's universal OpenRouter fallback of 3900. Three models — qwen3-30b (~32 K actual),
gpt-4o-mini (128 K actual), gemini-flash (1 M actual) — now process 3–4 API batches per
plan where before they processed 1. The original target model (gpt-oss-20b) no longer
triggers the feature after the config fix in this same PR. The adaptive feature currently
protects nothing and increases cost and batch-boundary blindness risk for three production
models.

### C2 — gpt-oss-20b plan timeout is a new failure mode
3/5 gpt-oss-20b plans receive `status=error` due to 600 s plan timeout rather than the
prior BadRequestError. The failure mode changed; the outcome for the pipeline is the same.
Root cause: LLMExecutor's provider failover sequence makes 6–9 sequential provider attempts
(DeepInfra → Fireworks → Together → Nebius → Amazon Bedrock → …), each 60–90 s. The
`MAX_RETRY_BUDGET_SECONDS=300` guard does not cover time inside a successful-but-slow
`llm_executor.run()` call.

### C3 — Orphaned threads continue API calls after plan timeout (surfaced latent issue)
`runner.py:554–566` submits `run_single_plan` to a nested `ThreadPoolExecutor`. When
`future.result(timeout=600)` fires, the Python thread continues running. With 3 plans
timing out per gpt-oss-20b run, up to 15 uncontrolled LLM calls may be in flight, driving
up API costs and potentially causing rate-limit cascades for subsequent plans.

### C4 — llama3.1 UUID mutations now visible (latent issue surfaced by error tracking)
Run 13 shows 4 errors across 2 plans: `unknown_lever_id` and `incomplete` for UUID-mutated
lever IDs. These were silently dropped before PR #455. The mutations are consistent with B2
(full UUIDs in `full_lever_context_str` at `enrich_potential_levers.py:156`) — llama3.1
copies and garbles the UUID from the context string. The enrichment for those levers is
lost without retry.

---

## Verdict

**CONDITIONAL**: The gpt-oss-20b config fix and error tracking are clear, durable improvements
that should be kept. However, the adaptive batch size introduces a confirmed regression
affecting 43% of runs (3 models × 5 plans), and gpt-oss-20b still fails 3/5 plans at the
orchestrator level. The PR should be accepted with a required follow-up to fix
`SMALL_CONTEXT_THRESHOLD` before the next experiment batch.

**Required for acceptance:**
1. Lower `SMALL_CONTEXT_THRESHOLD` from 6000 to 3000 (`enrich_potential_levers.py:112`).
   One-line fix. Eliminates the unintended batch_size=2 for OpenRouter models.
2. Fix gpt-oss-20b plan timeouts (increase `DEFAULT_PLAN_TIMEOUT` or add a per-step
   timeout override to accommodate multi-provider failover).

---

## Recommended Next Change

**Proposal:** Lower `SMALL_CONTEXT_THRESHOLD` from 6000 to 3000 in
`enrich_potential_levers.py:112`. This is a one-line constant change.

```python
# Before
SMALL_CONTEXT_THRESHOLD = 6000

# After
SMALL_CONTEXT_THRESHOLD = 3000
```

**Evidence:** Confirmed by both insight and code review agents. llama_index's `OpenRouter_LLM`
reports `context_window=3900` universally for all OpenRouter-proxied models regardless of
actual capability. Verified in run 17 (gpt-4o-mini), run 16 (qwen3-30b), and run 18
(gemini-flash) silo outputs — all show `context_window=3900` with 4 metadata entries
indicating 4 batches processed at batch_size=2. Before-run 89 (gpt-4o-mini) shows
`calls_succeeded=1`. Setting the threshold to 3000 places OpenRouter's 3900 safely above
the cutoff; any genuinely constrained model (<3000) still triggers small-batch mode.

**Verify in next iteration:**
- qwen3-30b, gpt-4o-mini, and gemini-flash revert to `calls_succeeded=2` (for 7-lever
  plans at batch_size=5, `ceil(7/5)=2`). If still 3–4, the threshold change did not take
  effect or another factor is active.
- gpt-oss-20b continues to use its normal batch_size (not batch_size=2) — confirm
  `context_window=131072` still reported and threshold not triggered.
- Synergy/conflict text cross-lever references for qwen3-30b: check that levers from
  different batches are referenced correctly now that all 7 levers are in one or two
  batches instead of four. The batch-boundary blindness risk documented in
  OPTIMIZE_INSTRUCTIONS should diminish.
- No regression in success rates for the three OpenRouter models (all were 5/5 with
  batch_size=2; they should remain 5/5 with normal batch size).

**Risks:**
- The threshold change is safe for all current production models. If a future model
  genuinely has context_window=3001–5999, it would incorrectly be excluded from the
  small-batch path. The conservative choice (3000) leaves adequate headroom.
- Reverting to larger batches for qwen3-30b/gpt-4o-mini/gemini-flash increases per-batch
  prompt size, which was not a problem before PR #455. No regression expected.
- If the OPTIMIZE_INSTRUCTIONS "batch boundary blindness" concern was masking a real
  inter-lever reference quality regression in the four-batch runs, reverting to two-batch
  runs should improve this. Worth checking in the next iteration.

**Prerequisites:** None. This fix is self-contained.

**OPTIMIZE_INSTRUCTIONS update recommended:** The PR already added a note about max_tokens
overflow (entry 3). A follow-up entry should document the OpenRouter `context_window=3900`
metadata fallback as a known pitfall for any future feature that probes model metadata:
"llama_index's OpenRouter_LLM reports context_window=3900 for all models regardless of
actual capability. Do not use context_window from llama_index metadata to gate features for
OpenRouter-proxied models."

---

## Backlog

**Resolved by PR #455 (remove from backlog):**
- B1 from analysis 54 (no per-batch retry / gpt-oss-20b 0/5 failure): Partially resolved.
  The BadRequestError root cause is fixed; gpt-oss-20b now produces valid output. The retry
  infrastructure is in place. The remaining timeout issue (C2 above) is a different problem
  and should be tracked separately. B1 as originally stated (no retry at all) can be closed.

**Still open (carry forward):**
- B2 from analysis 54 (full UUIDs in `full_lever_context_str`): Not addressed by PR #455.
  llama3.1 UUID mutations (C4 above) are caused by this bug. Still at `enrich_potential_levers.py:156`.
- D3 from analysis 53 (qualitative mechanism guidance for synergy/conflict): Unaddressed.
  qwen3-30b synergy/conflict terseness remains. The batch_size=2 regression may have
  masked or exacerbated this; re-evaluate after the SMALL_CONTEXT_THRESHOLD fix.

**New items to add:**
- C2 (gpt-oss-20b plan timeout): `MAX_RETRY_BUDGET_SECONDS` does not cap time inside a
  successful LLMExecutor.run() call. Fix: increase `DEFAULT_PLAN_TIMEOUT` for the enrich
  step or add a per-step timeout override in runner.py.
- C3 (orphaned threads after plan timeout): `runner.py:554–566`. Add a cancellation event
  polled between batches, or pass the plan budget into `EnrichPotentialLevers.execute()`.
- C4 / I3 from analysis 58 code review (fuzzy UUID matching for llama3.1): Implement
  prefix-based or edit-distance fallback in `enrich_potential_levers.py:262–271` to recover
  UUID-mutated lever enrichments. Low urgency but now confirmed affecting 2/35 plans.
- B4 from analysis 58 code review (banned phrases in `consequences` field description at
  `identify_potential_levers.py:116–118`): OPTIMIZE_INSTRUCTIONS was updated to warn
  against this pattern; the field description itself has not been fixed. Remove the
  phrase-specific prohibition (`"Do NOT include 'Controls ... vs.', 'Weakness:'"`) and
  replace with structural guidance.
- I2 from analysis 58 code review (`review_lever` structural field description at
  `identify_potential_levers.py:125–133`): "identify the primary trade-off … then state
  the specific gap" are structural instructions that cause template-lock. Replace with
  content-focused language.
- N3 (input data discrepancy): Future enrich_potential_levers experiments should use the
  same input dataset for before and after runs. The before baseline (runs 3/85–91) used
  `snapshot/1_deduplicate_levers`; all subsequent experiments use `baseline/train`. This
  confounded field-length and percent-claim comparisons in this analysis. Establish
  `baseline/train` as the canonical input for all future enrich step experiments.
- S1 (orphaned thread / API runaway): `runner.py:554–566`. Tracked above as C3.
- S2 (per-plan log.txt missing worker thread logs): `runner.py:540–548`. `_ThreadFilter`
  is scoped to the orchestrator thread, not the `run_single_plan` thread. Fix by passing
  the file handler to the worker thread. Improves debuggability for timeout investigations.
- B5 (closure captures `chat_message_list` by reference): `enrich_potential_levers.py:247`.
  Latent; matches the pattern in `identify_potential_levers.py:317` which defensively
  snapshots. Safe today; fix before any async refactoring.
