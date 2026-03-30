# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude and code_claude) agree on:

- **PR verdict: CONDITIONAL.** B4 (`calls_succeeded` reporting) is a clean, confirmed fix. B1 (per-batch retry) works for the 2 plans it recovered but is incomplete. D5 (OPTIMIZE_INSTRUCTIONS) is documentation only with no runtime effect.
- **No retry depth limit.** `enrich_potential_levers.py:239–246` splits indefinitely; a batch of 5 can cascade to 9 calls, each consuming its full provider timeout. Confirmed cause of gpt-oss-20b's 3 timeout failures in run 93.
- **No remaining-time guard.** Retries are inserted unconditionally at line 244–246 regardless of budget remaining.
- **UUID still present at line 168.** `full_lever_context_str` still includes `lever.lever_id` despite D5 documenting this as a known problem. Confirmed in run 92 (llama3.1 conflict_text contains `(9bc93565-67b1-49fc-afb9-4d310510f698)`).
- **Adaptive BATCH_SIZE needed.** `BATCH_SIZE = 5` at line 95 is hardcoded. gpt-oss-20b has `context_window=3900` and `num_output=8192`; BATCH_SIZE=5 reliably overflows its output token limit, causing the retry cascade. Root cause is not addressed by the PR.
- **Silent partial success.** If the LLM returns 3/5 levers from a "succeeded" batch, the missing 2 are silently dropped. `batches_succeeded` is incremented and no retry is triggered.
- **B4 is clean and confirmed.** All after-PR runs (92–98) report actual batch counts; before-PR runs (85–91) all reported `calls_succeeded: 1`.

## Cross-Agent Disagreements

No substantive disagreements between the two agents. Both analysed the same evidence trail and reached consistent conclusions. The code review is more granular on structural issues (S1 late-binding closure, S2 global dispatcher, S3 over-generation validator); the insight analysis focuses on run-level impact metrics. These are complementary, not contradictory.

**Source verification of disputed or high-stakes claims:**

- **UUID at line 168** (confirmed): `full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])` — UUID is present.
- **No retry depth limit** (confirmed): `enrich_potential_levers.py:239–246` has no depth counter; the only termination condition for the cascade is `len(batch) == 1`.
- **B4 fix in runner.py** (confirmed): `runner.py:184` reads `calls_succeeded=result.batches_succeeded` (was `calls_succeeded=1` before PR).
- **BATCH_SIZE hardcoded at line 95** (confirmed): `BATCH_SIZE = 5` — no per-model configuration exists.
- **S3 over-generation** (confirmed, intentional): `check_option_count` at `identify_potential_levers.py:147–158` only enforces `< 3`; the inline comment says "Over-generation (>3) is tolerable" — this is deliberate policy. Not a bug.

---

## Top 5 Directions

### 1. Adaptive BATCH_SIZE for small-context models
- **Type**: code fix
- **Evidence**: Both agents (I1 in code_claude, C1 in insight_claude). gpt-oss-20b with `context_window=3900` produces output at or near the 8192-token hard limit on every BATCH_SIZE=5 call. Confirmed via `usage_metrics.jsonl` for run 93: one batch produced exactly 8192 output tokens and was returned as invalid JSON.
- **Impact**: Eliminates the root cause of gpt-oss-20b batch failures. Expected to recover all 5 plans (currently 2/5) without triggering retries. Also eliminates the retry timeout cascade (N1, N3) as a side effect. `enrich_potential_levers.py:95,159`.
- **Effort**: Medium. `BATCH_SIZE` is computed before any LLM call but `llm.metadata["context_window"]` is only accessible inside `execute_function`. Options: (a) add an optional `batch_size` parameter to `execute()` and detect model context window in `runner.py`'s `_run_enrich` before calling; (b) do a pre-flight metadata-only call. Option (a) is lower risk.
- **Risk**: Low. Smaller batches mean more LLM calls but each call stays within output limits. Overall token cost is unchanged; latency improves because retries are eliminated.

### 2. Retry depth limit + remaining-time guard
- **Type**: code fix
- **Evidence**: B1 and B2 in code_claude, N1 and N3 in insight_claude. Confirmed by run 93 events.jsonl (3 plans timeout at 600s each). `enrich_potential_levers.py:239–246`.
- **Impact**: Even with direction #1 in place, this is a safety net for future models or larger plans. Without it, any batch failure on a slow model consumes the entire plan budget via cascading splits. With a depth limit of 1 and a remaining-time check, failing plans fail in ~60–120s instead of 600s. Reduces wasted runner time from ~1800s to ~300s for non-recoverable gpt-oss-20b plans today.
- **Effort**: Low. Store `(batch, depth)` tuples in `pending_batches`. Before inserting sub-batches, check `depth < 1`; otherwise skip retry. Add `time.monotonic() < deadline - safety_margin` check before inserting.
- **Risk**: Low. Belt-and-suspenders: worst case, a plan that would have recovered via a second split now fails faster. The retry still triggers on the first split (depth=0 → depth=1), covering the common case.

### 3. Fix UUID in `full_lever_context_str` (line 168)
- **Type**: code fix (one line)
- **Evidence**: B3 in code_claude, N4 in insight_claude, and D5 in the PR itself (OPTIMIZE_INSTRUCTIONS updated to document this, but the code fix was not included). `enrich_potential_levers.py:168`.
- **Impact**: Eliminates UUID leakage from synergy_text and conflict_text for UUID-sensitive models (confirmed: llama3.1 run 92 — full 36-char UUID in conflict_text). Affects all 35 runs but most visible in llama3.1 (5 plans). Aligns code with the D5 documentation that was already merged. Resolves the inconsistency where OPTIMIZE_INSTRUCTIONS says "this is a known problem" but the code still has the problem.
- **Effort**: Trivial. Change `f"- {lever.lever_id}: {lever.name}"` to `f"- {lever.name}"` at line 168.
- **Risk**: Near-zero. The synergy/conflict instructions already say "Name the specific levers it enhances/constrains" — models reference by name, not ID. Removing the ID only helps.

### 4. Silent partial success detection with re-queue
- **Type**: code fix
- **Evidence**: B4 in code_claude (distinct from the runner.py B4 — this is an enrich-step internal bug). `enrich_potential_levers.py:225–232`.
- **Impact**: Currently, if an LLM returns 3/5 levers from a "succeeded" batch, `batches_succeeded` is incremented and the 2 missing levers are silently dropped, appearing as errors at line 260. No retry is triggered. The caller gets `status="ok"` with fewer enriched levers than expected. Adding a post-batch comparison (returned lever_ids vs expected lever_ids) and optionally re-queuing missing levers as single-lever batches would improve reliability for weak models that truncate output.
- **Effort**: Medium. Comparison is trivial; re-queuing requires determining whether to retry (adds calls) or just log and flag with `levers_skipped` in the result. At minimum: emit a warning with the missing lever count.
- **Risk**: Low for logging-only; medium if re-queuing (could loop if the model consistently fails for a specific lever).

### 5. Anti-echoing clause in description guidance
- **Type**: prompt change
- **Evidence**: I3 in code_claude, H1 in insight_claude. D5 added "consequence echoing without elaboration" to OPTIMIZE_INSTRUCTIONS but did not update the runtime system prompt. llama3.1 still at 0.70× baseline description length (run 92 vs baseline). `enrich_potential_levers.py:144`.
- **Impact**: llama3.1 description richness could improve from 0.70× toward 0.80–0.90× baseline. The current instruction ("Clearly explain the lever's purpose, what it controls, its objectives, and key success metrics") does not explicitly prohibit restating the `consequences` field. Adding one sentence — "Do not paraphrase the lever's consequences field — use it only as grounding context, then elaborate on purpose, scope, and decision-relevant implications that go beyond it." — would directly address the documented problem.
- **Effort**: Low. One sentence addition to `ENRICH_LEVERS_SYSTEM_PROMPT` at line 144.
- **Risk**: Medium. May inflate description length for models that already produce adequate elaboration. Could push gpt-5-nano or haiku (already at 1.20–1.34× baseline) further over 1.5×. Should be tested as an isolated iteration.

---

## Recommendation

**Pursue direction #1 (Adaptive BATCH_SIZE) first, and bundle direction #3 (UUID fix) into the same PR.**

**Why #1 first:** gpt-oss-20b's failure mode is entirely explained by BATCH_SIZE=5 producing output that consistently overflows the model's 8192-token hard limit when `context_window=3900`. The PR #452 retry mechanism is symptom treatment: it recovers 2 plans, but 3 plans still fail because the retry cascade itself consumes the full 600s budget. With BATCH_SIZE=2, each batch produces ≈3500 output tokens — within the limit — and no retries are needed. This would move gpt-oss-20b from 2/5 to 5/5, adding 3 plan successes and eliminating ~1800s of wasted runner time per test run.

**Why bundle #3:** The UUID fix is a one-line change at `enrich_potential_levers.py:168`. D5 (already merged in this PR) explicitly documented UUID cross-reference format inconsistency as a known problem in OPTIMIZE_INSTRUCTIONS. Including the code fix in the same PR closes that gap. It is zero-risk and requires no testing beyond confirming llama3.1 run output no longer contains raw UUIDs.

**Specific changes:**

**For #1 (Adaptive BATCH_SIZE):**

In `runner.py`, pass a `batch_size` argument to `_run_enrich` based on a pre-detected context window, or add detection at the start of `EnrichPotentialLevers.execute()`:

```python
# enrich_potential_levers.py — after line 159, add a pre-flight detection pass
# (call llm_executor.run with a trivial function that returns llm.metadata)
# Then set effective_batch_size = 2 if context_window < 6000 else BATCH_SIZE
# and use effective_batch_size when building pending_batches at line 181
```

The simpler implementation: add `batch_size: int = BATCH_SIZE` as a parameter to `execute()`, and in `runner.py`'s `_run_enrich`, do a metadata probe before calling `execute`:

```python
# runner.py _run_enrich — before calling EnrichPotentialLevers.execute():
def probe_fn(llm):
    return dict(llm.metadata)
meta = llm_executor.run(probe_fn)
effective_batch = 2 if meta.get("context_window", 8192) < 6000 else 5

result = EnrichPotentialLevers.execute(
    llm_executor, project_context=project_context,
    raw_levers_list=lever_item_list,
    batch_size=effective_batch
)
```

**For #3 (UUID fix):**

```python
# enrich_potential_levers.py line 168 — change:
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
# to:
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

**Also add direction #2 (retry guards) to the same PR as a safety net.** The retry mechanism should remain as a safety net for other edge cases, but cap it at depth=1 and add a time check. This prevents future models from hitting the same timeout exhaustion pattern.

---

## Deferred Items

- **Direction #4 (silent partial success detection):** Worth doing, but lower urgency. The current behaviour logs errors at line 260 — skipped levers are detectable in log output. A structured `levers_skipped` field in `PlanResult` and a `partial_recovery` event for the enrich step (matching the existing pattern for identify) would improve observability. Implement after the batch size and retry guard work.

- **Direction #5 (anti-echoing prompt clause):** Defer until after batch size and UUID work is complete and verified. llama3.1 at 0.70× baseline is below ideal but not broken — it produces complete, valid output. A prompt change should be its own isolated iteration so its effect can be measured cleanly.

- **S1 (late-binding closure, enrich_potential_levers.py:212–217):** Technically a latent bug — `execute_function` closes over `chat_message_list` by name. In the current synchronous call path this is safe, but a defensive default argument binding (`def execute_function(llm, _msgs=chat_message_list)`) would make the intent explicit. Low priority; address during refactor.

- **S2 (global dispatcher mutation, runner.py:248–250):** Pre-existing issue, not introduced by PR #452. Benign when `workers=1`. Track for later if parallel worker support is added.

- **Identify step `check_option_count` validator (S3 in code_claude):** Confirmed intentional per inline comment — over-generation is tolerable, under-generation is not. The field description ("Exactly 3 options") is inconsistent with the policy but this is a documentation issue, not a code bug. Consider updating the field description to ">= 3 options" to match policy.
