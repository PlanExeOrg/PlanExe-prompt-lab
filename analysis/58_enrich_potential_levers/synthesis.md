# Synthesis

## Cross-Agent Agreement

Both the insight and code review agents agree on the following:

- **PR #455 verdict: CONDITIONAL.** The gpt-oss-20b `max_tokens`/`context_window` config fix is confirmed effective (BadRequestError eliminated, 0/5 → 5/5 valid output files). Error tracking works correctly. OPTIMIZE_INSTRUCTIONS additions are accurate.
- **B1 is the most critical introduced regression.** `SMALL_CONTEXT_THRESHOLD=6000` inadvertently captures all OpenRouter-proxied models (which report `context_window=3900` universally), forcing batch_size=2 on qwen3-30b, gpt-4o-mini, and gemini-flash — three models with actual context windows of 32K–1M tokens.
- **B2 is the root cause of gpt-oss-20b's remaining timeouts.** `MAX_RETRY_BUDGET_SECONDS=300` only guards the `pending_batches` retry loop; it does not cap the time spent inside a single `llm_executor.run()` call. LLMExecutor's provider failover sequence (6–9 attempts × 60–90 s each) consumes the full 600 s plan timeout even when enrichment ultimately succeeds.
- **Input data discrepancy (N3) confounds all before/after field-length and percent-claim comparisons.** Before runs used `snapshot/1_deduplicate_levers` (15–18 levers); after runs use `baseline/train` (7–8 levers). Any metric that scales with lever count is unreliable.
- **llama3.1 UUID mutations (N5) are now visible via error tracking**, but the enrichment for those levers is silently discarded.

---

## Cross-Agent Disagreements

There are no significant disagreements between the two agents. The code review provides more granular code-level location detail (exact line numbers, closure-by-reference latent bug B5, log thread filter issue S2), while the insight provides richer run-level evidence. All claims are consistent and mutually reinforcing.

One nuance: the insight frames N4 (percent claims in gpt-4o-mini/haiku output, 16 each) as "confounded" and does not attribute it to PR #455. The code review does not address N4 directly. Source code reading confirms the confound: the percent figures originate from `02-10-potential_levers.json` consequences fields in the `baseline/train` input data, not from the adaptive batch size or any PR change. This finding should not drive the next iteration.

---

## Top 5 Directions

### 1. Fix SMALL_CONTEXT_THRESHOLD — lower from 6000 to 3000
- **Type**: code fix
- **Evidence**: Confirmed by both agents (B1/N2). Verified in source: `enrich_potential_levers.py:112` sets `SMALL_CONTEXT_THRESHOLD = 6000`; line 195 checks `if context_window < SMALL_CONTEXT_THRESHOLD`. llama_index's `OpenRouter_LLM` returns `context_window=3900` for all OpenRouter models regardless of actual capability. 3900 < 6000 → batch_size=2 fires for qwen3-30b (~32K actual), gpt-4o-mini (128K actual), and gemini-flash (1M actual). After the gpt-oss-20b config fix in this same PR, that model correctly reports `context_window=131072` and is *not* in the small-batch path. The adaptive feature currently protects nothing and penalises three unrelated models.
- **Impact**: 15/35 runs (3 model types × 5 plans each) revert from 3–4 API calls per plan back to 1–2. Eliminates the "batch boundary blindness" risk for those models. Zero change to success rate (all three models were already at 5/5), but removes unnecessary API cost and prompt fragmentation.
- **Effort**: low — 1-line constant change
- **Risk**: minimal. OpenRouter's universal fallback is 3900; setting the threshold to 3000 excludes it. Any genuinely small-context model (<3000) still triggers the small-batch path. If a future model legitimately needs batch_size=2, the threshold can be tuned further.

### 2. Fix gpt-oss-20b plan timeouts — increase step-level timeout
- **Type**: code/config fix
- **Evidence**: Confirmed by both agents (B2/N1/I4). Verified in `runner.py:93`: `DEFAULT_PLAN_TIMEOUT = 600`. Verified in `enrich_potential_levers.py:277–281`: the `MAX_RETRY_BUDGET_SECONDS` elapsed check only fires in the `except Exception` path — it never runs when a batch ultimately succeeds after a long provider failover chain. For gpt-oss-20b, 6–9 sequential provider attempts × 60–90 s each = 540–810 s per plan, consuming the entire 600 s ceiling.
- **Impact**: gpt-oss-20b recovers from 2/5 to 5/5 status=ok. The three "failed" plans already write valid enriched lever files to disk — the only thing broken is the orchestrator-level status. Raising the plan timeout to 900 s (or adding a per-step timeout override) would convert these to genuine successes at no quality cost.
- **Effort**: low–medium — either raise `DEFAULT_PLAN_TIMEOUT` in `runner.py`, or add a step-specific override in the llm_config for gpt-oss-20b.
- **Risk**: A higher timeout permits slower models to occupy workers longer. With 7 parallel plans this is manageable; the real risk is masking a future infinite hang. A 900–1200 s ceiling is generous enough for gpt-oss-20b's known behavior and still catches true hangs.

### 3. Remove banned phrases from identify_potential_levers.py field description
- **Type**: prompt change (Pydantic field description)
- **Evidence**: Confirmed in code review (B4). Verified at `identify_potential_levers.py:116–118`: the `consequences` field description contains `"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"`. OPTIMIZE_INSTRUCTIONS lines 79–82 explicitly warns that small models treat prohibition text as a template and copy the banned phrases. The field description has not been updated despite OPTIMIZE_INSTRUCTIONS being updated.
- **Impact**: Affects all 35 runs across all models in the identify step, which feeds into the enrich step. Removing the named-phrase prohibition reduces the risk of weak models (llama3.1, qwen3-30b) echoing "Controls ... vs." or "Weakness:" into the consequences field. Since consequences text is carried into the enrich step's user prompt, cleaner consequences reduce noise available for consequence-echoing (N4/OPTIMIZE_INSTRUCTIONS entry 1).
- **Effort**: low — remove the specific banned-phrase sentence; retain structural guidance ("do not include critique text").
- **Risk**: Without the explicit prohibition, weak models might produce review/critique text in the consequences field. However, OPTIMIZE_INSTRUCTIONS's own reasoning (lines 79–82) argues the prohibition makes this *more* likely. Risk is manageable.

### 4. Fix review_lever field description structural phrases
- **Type**: prompt change (Pydantic field description)
- **Evidence**: Code review I2. Verified at `identify_potential_levers.py:125–133`: `review_lever` field description contains "identify the primary trade-off … then state the specific gap". OPTIMIZE_INSTRUCTIONS lines 87–92 warns that structural phrases like these cause models to begin every output with "The primary trade-off is…". The examples in the system prompt provide variety, but the field description overrides them for models that weight field descriptions heavily.
- **Impact**: Affects all 35 runs in the identify step. Prevents template-lock on "The primary trade-off is…" / "The specific gap is…" for weaker models, improving review_lever diversity and credibility. Aligns with OPTIMIZE_INSTRUCTIONS goals (realistic, grounded content).
- **Effort**: low — rewrite two sentences in the field description to focus on content rather than sentence structure.
- **Risk**: A field description change is always a prompt change; behavior can shift unexpectedly for any model. Test with a self_improve iteration before merging, per the docstring at `identify_potential_levers.py:98–101`.

### 5. Fuzzy UUID matching for llama3.1 lever mutations
- **Type**: code fix
- **Evidence**: Confirmed by both agents (N5/I3). Verified in run 13 outputs and at `enrich_potential_levers.py:262–271`: when `char.lever_id` is not in `enriched_levers_map`, the enrichment is discarded and an `unknown_lever_id` error is recorded. llama3.1 consistently garbles only the final UUID segment (e.g., `bca5bca5cc7c18408` instead of `bca5cc7c7cc18408`); the prefix is always correct.
- **Impact**: Recovers 2 plans' worth of UUID-mutated lever enrichments for llama3.1 (2/35 runs, 4 errors). Not a success-rate change (those plans still produce output), but raises enrichment completeness from N–1 to N levers for affected plans.
- **Effort**: medium — implement an edit-distance or prefix-based fuzzy match fallback when exact UUID lookup fails.
- **Risk**: A fuzzy match that is too permissive could link a mutated UUID to the wrong lever if multiple levers share a similar prefix. Safe implementation: only accept a fuzzy match when exactly one candidate has a Levenshtein distance ≤ 3 from the returned ID.

---

## Recommendation

**Fix B1: lower `SMALL_CONTEXT_THRESHOLD` from 6000 to 3000.**

This should be done first because it is a confirmed code bug with a trivial one-line fix, affects 43% of runs (15/35 across three model types), and has no meaningful downside risk.

**File:** `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
**Line:** 112
**Change:**
```python
# Before
SMALL_CONTEXT_THRESHOLD = 6000

# After
SMALL_CONTEXT_THRESHOLD = 3000
```

**Why 3000:** OpenRouter's llama_index fallback is 3900. Setting the threshold to 3000 places OpenRouter-proxied models safely above the cutoff while still protecting any genuinely small-context model (< 3000 tokens). The feature was originally designed for gpt-oss-20b before its context_window config was fixed; after PR #455, no current production model should trigger batch_size=2. The conservative choice is to lower the threshold rather than remove the feature entirely, preserving it as a safety net.

**Expected outcome:** qwen3-30b, gpt-4o-mini, and gemini-flash revert to batch_size determined by `BATCH_SIZE` (5 levers per call) or the natural `ceil(n_levers / 5)` split, reducing calls_succeeded from 4 → 2 for 7-lever plans and eliminating unnecessary prompt fragmentation. Batch boundary blindness risk documented in OPTIMIZE_INSTRUCTIONS is correspondingly reduced.

---

## Deferred Items

**B2/I4 — gpt-oss-20b plan timeout (second priority):** Raise `DEFAULT_PLAN_TIMEOUT` to 900 s for the enrich step, or add a per-step timeout override to `runner.py`. The enriched lever data is already written to disk; only the orchestrator status is wrong. This is a straightforward fix but touches `runner.py` which is shared across all steps.

**B4 — Banned phrases in `consequences` field description (`identify_potential_levers.py:116–118`):** Remove `"Do NOT include 'Controls ... vs.', 'Weakness:'"` from the field description. Retain structural guidance. Requires a self_improve iteration on the identify step before merging.

**I2 — `review_lever` structural field description (`identify_potential_levers.py:125–133`):** Replace "identify the primary trade-off … then state the specific gap" with content-focused language: e.g., "A concise analysis of the core trade-off and the blind spot in the three options." Requires a self_improve iteration.

**N5/I3 — Fuzzy UUID matching for llama3.1:** Implement prefix-based or edit-distance fallback in `enrich_potential_levers.py:262–271`. Affects only llama3.1 and recovers ~4 lever enrichments per iteration. Low urgency.

**S1 — Orphaned thread after plan timeout:** `runner.py:554–566` submits work to a nested `ThreadPoolExecutor`; on timeout, the thread continues consuming API resources. Add a cancellation event polled between batches in `EnrichPotentialLevers.execute()`. Medium effort, prevents API cost runaway for slow models.

**S2 — per-plan `log.txt` missing worker thread logs:** `_ThreadFilter` is scoped to the `_run_plan_task` thread, not the `run_single_plan` thread. Fix by passing the file handler to `run_single_plan` and applying the filter to its thread ID. Improves debuggability for future timeout investigations.

**B5 — Closure captures `chat_message_list` by reference:** `enrich_potential_levers.py:247–254` should snapshot `list(chat_message_list)` before the closure, matching the pattern in `identify_potential_levers.py:317`. Latent bug today; becomes an active bug if `LLMExecutor.run()` ever becomes async.

**S3 / I5 — `batches_succeeded` overcounts:** Increment only when all characterizations in a batch matched known lever IDs, to make `calls_succeeded` in `outputs.jsonl` a reliable quality signal.

**N3 — Input data discrepancy:** Future self_improve iterations for `enrich_potential_levers` should ensure before and after runs use the same input dataset (`baseline/train`). The before baseline (runs 3/85–91) used `snapshot/1_deduplicate_levers`; this confounds all field-length and percent-claim comparisons.
