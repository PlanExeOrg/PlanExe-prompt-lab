# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`
- `llm_config/baseline.json`

PR under review: #454 — Adaptive batch size, guarded retry, and max_tokens bump for enrich step.

---

## Bugs Found

### B1 — UUID leakage in `full_lever_context_str` (enrich_potential_levers.py:198)

```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

Including `lever_id` UUIDs in the full-lever context string causes llama3.1 to echo full UUIDs (e.g. `b35d92a2-c2a2-42e9-9836-eee6bae98898`) into `synergy_text` and `conflict_text`. The problem is documented in `OPTIMIZE_INSTRUCTIONS` (lines 89–92) but the code is unchanged. Replacing with `f"- {lever.name}"` removes the UUID signal entirely.

This is also a likely contributor to B2's `unknown_lever_id` hallucinations: when the context string includes UUIDs, llama3.1 sometimes constructs plausible-looking but non-existent UUIDs in its output.

### B2 — max_tokens=128000 consumes nearly all of gpt-oss-20b's 131072-token context window (baseline.json:34 + enrich_potential_levers.py:186–193)

`baseline.json` sets `max_tokens: 128000` for `openrouter-openai-gpt-oss-20b`. The model's actual context window is 131072 tokens (as stated in the comment on line 24). This leaves only **3072 tokens for input text**, but individual lever descriptions already consume 3675–3909 input tokens. Every batch — including single-lever batches at retry depth=1 — fails with:

```
BadRequestError: you requested about 131909 tokens (3909 of text input, 128000 in the output).
```

The adaptive batch size code (`enrich_potential_levers.py:186–193`) correctly detects `context_window=3900` and sets `batch_size=2`, but `context_window=3900` is a LlamaIndex metadata artifact — not the model's true 131072 context window. There is no corresponding logic to cap `max_tokens` at a safe fraction of the real context window.

Root causes:
1. `baseline.json:34` — `max_tokens: 128000` for a 131072-token context model.
2. `baseline.json:23–43` — `openrouter-openai-gpt-oss-20b` has no explicit `context_window` field in `arguments` (unlike `openai-gpt-5-nano` at line 11 which has `"context_window": 400000`). LlamaIndex falls back to an internal registry value of ~3900, which does not reflect the model's real capacity. The adaptive batch size accidentally benefits from this wrong value (gets `batch_size=2`), but it means the adaptive code has no reliable way to compute a safe `max_tokens` cap.

The result: all 5 levers for plans with longer context (sovereign_identity, hong_kong_game, parasomnia) are silently skipped and the plan reports `status: "ok"` with zero characterized levers.

Minimum fix: reduce `max_tokens` to ≤65536 in `baseline.json` for gpt-oss-20b, or add `"context_window": 131072` to its `arguments` so the adaptive code can compute `min(max_tokens, context_window // 2)`.

### B3 — `_run_enrich` returns `status="ok"` with zero characterized levers (runner.py:165–185)

```python
def _run_enrich(plan_dir, plan_output_dir, llm_executor) -> PlanResult:
    ...
    result = EnrichPotentialLevers.execute(...)
    ...
    return PlanResult(
        name=plan_name,
        status="ok",
        duration_seconds=0,
        calls_succeeded=result.batches_succeeded,
    )
```

There is no check for `len(result.characterized_levers) == 0`. When all batches fail (B2 scenario), `characterized_levers` is empty and `batches_succeeded=0`, but the runner still returns `status="ok"`. The downstream resume logic at `runner.py:619–622` marks this plan as completed and skips it on re-runs. Downstream steps silently receive an empty lever list.

### B4 — `batches_succeeded` incremented on partial LLM responses (enrich_potential_levers.py:252–254)

```python
result = llm_executor.run(execute_function)
batch_result: BatchCharacterizationResult = result["chat_response"].raw
all_metadata.append(result["metadata"])
batches_succeeded += 1
```

`batches_succeeded` is incremented whenever the LLM call doesn't throw, regardless of how many levers were actually returned. If the model returns characterizations for 2 of 5 batch levers, `batches_succeeded` is incremented by 1 and the remaining 3 levers silently fall through as `incomplete`. The metric is inflated and masks partial enrichment. The `outputs.jsonl` `calls_succeeded` field inherits this inflation.

---

## Suspect Patterns

### S1 — False-positive "partial recovery" warning in `_run_levers` (runner.py:131–134)

```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

The adjacent comment says "A 2-call success is normal for models that produce 8+ levers per call." Yet the condition fires for `actual_calls == 2`, which is exactly the "normal" case the comment describes. A model producing 8 levers per call completes in 2 calls (8+8=16 ≥ 15), emitting a spurious warning about "partial recovery" when everything succeeded. The warning threshold should be `actual_calls == 0` (genuine failure) or the warning should be removed entirely.

### S2 — `Lever.options` field description contradicts the validator (identify_potential_levers.py:121–159)

The `options` field description (line 122) says "Exactly 3 options for this lever. No more, no fewer." The validator at line 157 only enforces `len(v) < 3`. Models that strictly follow field descriptions may expect a hard rejection for 4+ options; models that produce 4 options will pass silently. The discrepancy between "No more, no fewer" and "min=3" is intentional (per the validator docstring) but the field description should be updated to match actual enforcement: "At least 3 options." Leaving "no more than 3" in the description while accepting 4+ could generate unexpected LLM behavior for models that treat field descriptions as hard constraints.

### S3 — `save_raw()` omits `batches_succeeded` (enrich_potential_levers.py:318–326)

```python
def save_raw(self, file_path: str) -> None:
    output_data = {
        "metadata": self.metadata,
        "errors": self.errors,
        "characterized_levers": [lever.model_dump() for lever in self.characterized_levers]
    }
```

`batches_succeeded` is used by `runner.py` before saving (`calls_succeeded=result.batches_succeeded`), but it is never written to disk. The saved JSON cannot be used to reconstruct or verify the batch success count after the fact, complicating post-hoc analysis.

### S4 — Missing `context_window` in gpt-oss-20b baseline config (baseline.json:23–43)

The `openai-gpt-5-nano` entry explicitly configures `"context_window": 400000`. `openrouter-openai-gpt-oss-20b` does not, despite its comment stating "131,072 context". LlamaIndex falls back to an internal default (~3900) that bears no relation to the real model window. Any code that probes `llm.metadata.context_window` for gpt-oss-20b (like the adaptive batch size logic at enrich_potential_levers.py:188) gets a value that is wrong by 33×. This inconsistency between the comment and the configuration is a maintenance hazard.

---

## Improvement Opportunities

### I1 — Strip UUIDs from `full_lever_context_str` (enrich_potential_levers.py:198)

Change:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
to:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

This is the direct fix for B1 and reduces N3 hallucination risk. Synergy/conflict fields should reference levers by name anyway (per OPTIMIZE_INSTRUCTIONS lines 89–92).

### I2 — Cap max_tokens relative to context_window in adaptive sizing (enrich_potential_levers.py:186–193 / baseline.json:34)

Two-pronged fix:
1. In `baseline.json`, add `"context_window": 131072` to gpt-oss-20b's `arguments` and reduce `max_tokens` to ≤65536.
2. Optionally: in `enrich_potential_levers.py`, after probing `context_window`, derive a safe max_tokens cap. This requires passing it into the LLM creation path, which is currently not exposed in `execute_function`.

The simpler and more reliable fix is (1): correct `baseline.json` so the configured max_tokens is at most half the real context window.

### I3 — Return `status="error"` when characterized_levers is empty (runner.py:165–185)

Add a guard at the end of `_run_enrich`:
```python
if not result.characterized_levers:
    raise ValueError(f"All {len(lever_item_list)} levers failed enrichment — zero characterized levers produced")
```
This converts a silent failure into a visible `status="error"` in `outputs.jsonl` and prevents the resume logic from marking a zero-lever plan as completed.

### I4 — Detect partial batch responses (enrich_potential_levers.py:256–265)

After the success path, check if the number of returned characterizations matches the batch size:
```python
returned_ids = {char.lever_id for char in batch_result.characterizations}
batch_ids = {lever.lever_id for lever in batch}
missing = batch_ids - returned_ids
if missing:
    logger.warning(f"LLM returned {len(batch_result.characterizations)}/{len(batch)} characterizations; missing: {missing}")
```
Currently only `unknown_lever_id` (LLM returns extras) is logged. The symmetric case (LLM returns fewer) is silently accepted and the un-returned levers end up as `incomplete` with no direct linkage to the batch that was supposed to produce them.

### I5 — Persist `batches_succeeded` in `save_raw()` (enrich_potential_levers.py:318–326)

Add `"batches_succeeded": self.batches_succeeded` to the `output_data` dict so the metric is preserved on disk for post-hoc analysis and is consistent with what `runner.py` reports in `outputs.jsonl`.

### I6 — Fix false-positive `partial_recovery` warning threshold (runner.py:131–134)

Change the warning condition from `actual_calls < 3` to `actual_calls == 0` to only fire on genuine total failure. Alternatively, log at INFO level for `actual_calls in (1, 2)` with a message like "completed in {actual_calls} calls" to distinguish fast-success from failure.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| N1 — gpt-oss-20b: 0 characterized levers for 3/5 plans despite `status="ok"` | **B2**: `max_tokens=128000` in baseline.json leaves only 3072 input tokens; all batches fail with `BadRequestError`. **B3**: `_run_enrich` never checks for empty output before returning `status="ok"`. |
| N1 — error pattern: 3 `batch_retry` + 6 `batch_skipped` + 5 `incomplete` for sovereign_identity | **B2** + correct retry logic: batch of 2 fails → 1 `batch_retry`, splits into 1+1 at depth=1, each fails → 2 `batch_skipped`. 3 initial batches × this pattern = 3 retry + 6 skipped. All 5 levers unenriched → 5 `incomplete`. |
| N2 — llama3.1 UUID leakage in synergy_text / conflict_text | **B1**: `full_lever_context_str` at line 198 includes `lever.lever_id` UUIDs. OPTIMIZE_INSTRUCTIONS documents this but the fix was not applied. |
| N3 — llama3.1 `unknown_lever_id` hallucination in gta_game | **B1** contributing factor: UUID format in the context string gives llama3.1 a template for constructing plausible-but-wrong UUIDs. |
| P3 — accurate batch counting now implemented | **Fixed in PR**: `calls_succeeded=result.batches_succeeded` (runner.py:184) replaces the previous hardcoded `1`. But **B4** means the count is still inaccurate for partial batch responses. |
| P1 / Comparison table — gpt-oss-20b failures now complete in <2s vs 600s | **Correctly implemented**: guarded retry at enrich_potential_levers.py:269–298 with `MAX_RETRY_DEPTH=1` and `MAX_RETRY_BUDGET_SECONDS=300`. |
| Insight Q3 — should zero-lever plans report `status="error"`? | **B3**: confirmed yes, the code should raise when characterized_levers is empty. |

---

## PR Review

### PR #454: Adaptive batch size, guarded retry, and max_tokens bump for enrich step

**1. Adaptive batch size (enrich_potential_levers.py:184–193) — Correctly implemented**

The PR correctly uses `context_window` (not `num_output`) for the threshold check. For gpt-oss-20b, LlamaIndex reports `context_window=3900`, so `batch_size=2` is correctly selected. The logic itself is sound.

**Edge case missed**: `context_window=3900` for gpt-oss-20b is a LlamaIndex metadata artifact, not the model's real window (131072). The PR has no way to know the real window from the LlamaIndex API, which is why the max_tokens fix must come from the config side (baseline.json) rather than the code side.

**2. max_tokens bump: 8192 → 128000 for gpt-oss-20b (baseline.json:34) — Introduces regression B2**

The motivation (prevent JSON truncation) is correct. The chosen value (128000) is wrong for a 131072-token context model: `131072 − 128000 = 3072` input tokens. Even a single lever requires 3675–3909 tokens. The PR should have set `max_tokens` to ≤65536 (roughly `context_window // 2`) rather than 128000.

The comment on line 24 of baseline.json already states "131,072 context" — the PR author had the correct window value available but did not check whether `max_tokens=128000` left sufficient input headroom.

**3. Guarded retry (enrich_potential_levers.py:267–298) — Correctly implemented**

`MAX_RETRY_DEPTH=1`, `MAX_RETRY_BUDGET_SECONDS=300`, time budget check, depth guard, and the `insert(0, ...)` ordering all look correct. Failed batches split once, sub-batches skip on continued failure. The retry turns 600s hangs into <2s fail-fast detections for `BadRequestError`. No bugs found here.

**4. Accurate batch counting (runner.py:184) — Improvement over hardcoded 1, but incomplete**

`calls_succeeded=result.batches_succeeded` correctly counts actual successful LLM calls. However, `batches_succeeded` is incremented even when the LLM returns a partial response (**B4**). For a batch that returns 2 of 5 characterizations, `batches_succeeded` goes up by 1 and the metric appears healthy while 3 levers silently drop. The fix in the PR is a real improvement over the pre-PR hardcoded value, but the metric is still not fully reliable.

**5. OPTIMIZE_INSTRUCTIONS additions — Correct documentation, zero code fix**

The PR adds "consequence echoing" and "UUID cross-reference format inconsistency" to `OPTIMIZE_INSTRUCTIONS`. These entries are accurate descriptions of the observed problems. However, the UUID leakage entry explicitly identifies line 198 as the root cause and does not fix it. Future PRs should close the gap between the documented problem and the code change.

**Overall PR assessment**: Three of the four changes (adaptive batch size, guarded retry, accurate batch counting) are implemented correctly and deliver real improvements. The max_tokens=128000 value is a miscalibration that introduces a new silent failure mode worse than the original: instead of a timeout with visible error, affected plans produce zero levers with `status="ok"`. The fix is a one-line change in `baseline.json`.

---

## Summary

The most impactful issues are:

1. **B2 + B3** (silent zero-lever failure for gpt-oss-20b): `max_tokens=128000` in `baseline.json` combined with the model's real 131072-token context window leaves only 3072 input tokens. All batches fail. The runner silently reports `status="ok"`. Fix: reduce `max_tokens` to ≤65536 for gpt-oss-20b in `baseline.json`; add a zero-lever guard in `_run_enrich`.

2. **B1** (UUID leakage in llama3.1 synergy/conflict): A trivial one-character change at `enrich_potential_levers.py:198` — drop `lever.lever_id:` from the context string — eliminates UUID injection and reduces hallucinated UUIDs.

3. **B4** (inflated batches_succeeded metric): Partial LLM responses are counted as full successes, masking silent lever loss.

Suspect patterns S1 (false-positive warning) and S3 (batches_succeeded not persisted) are low-severity but easy to fix alongside the above.
