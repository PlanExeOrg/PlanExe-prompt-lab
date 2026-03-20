# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — Silent LLM failure masking in `DeduplicateLevers.execute()` (deduplicate_levers.py:196–205)

```python
try:
    result = llm_executor.run(execute_function)
    batch_result = result["chat_response"].raw
    metadata_list.append(result.get("metadata", {}))
except PipelineStopRequested:
    raise
except Exception as e:
    logger.error(f"Batch deduplication call failed: {e}")
```

When the LLM call fails (timeout, network error, exhausted retries), `batch_result` stays `None`. The `except` block only logs and does not re-raise. Execution falls through to the fallback path, which silently assigns `"primary"` to every input lever. No exception reaches `_run_deduplicate()`, so the runner reports `status="ok"` and `calls_succeeded=1`.

This is the root cause of the llama3.1 silo/parasomnia behaviour observed in runs 64: 120.16s → all 18 levers receive `"Not classified by LLM. Keeping as primary to avoid data loss."`, yet `outputs.jsonl` records `{"status": "ok", "calls_succeeded": 1}`.

The fallback is a reasonable data-loss guard, but the silent masking of the failure is a separate problem — it makes complete LLM failure indistinguishable from a successful run in `outputs.jsonl`.

### B2 — Wrong field stored as `user_prompt` in result constructor (deduplicate_levers.py:272)

```python
return cls(
    user_prompt=project_context,   # ← BUG: should be user_prompt
    ...
)
```

The variable `user_prompt` (constructed at lines 179–183, containing the full prompt including the levers JSON) is what was actually sent to the LLM. `project_context` is just the project description, which is a subset. The saved `_raw.json` file's `user_prompt` field therefore omits the levers JSON, making it impossible to reconstruct the exact prompt from the saved file alone.

### B3 — `calls_succeeded` hardcoded to 1 regardless of LLM success (runner.py:155)

```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=1,  # always 1, even when the LLM call failed
)
```

When the LLM times out and the fallback runs, this still reports `calls_succeeded=1`. `DeduplicateLevers.execute()` does not expose `llm_executor.attempt_count` or a success flag, so the runner has no way to set this correctly without access to the executor state. The result: runs where zero real classifications occurred are indistinguishable from clean runs in `outputs.jsonl`.

### B4 — No `classification_fallback` event emitted to events.jsonl (deduplicate_levers.py:228–236, runner.py)

When the fallback fires (either total LLM failure or per-lever missing classification), only a Python logger warning is produced. Nothing is written to `events.jsonl`. The insight analysis pipeline that reads `events.jsonl` has no way to detect or count degraded runs programmatically. The runner's `_run_plan_task` always writes either `run_single_plan_complete` or `run_single_plan_error` — never a middle state for "completed but with fallback".

### B5 — `partial_recovery` event gating excludes `deduplicate_levers` step (runner.py:546–552)

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

This quality-gate event is only emitted for the `identify_potential_levers` step. There is no equivalent check for `deduplicate_levers`. A complete deduplication failure (18/18 fallback) produces no `partial_recovery` event and no other quality signal in `events.jsonl`.

---

## Suspect Patterns

### S1 — Single batch call has no retry logic (deduplicate_levers.py:195–205)

PR #372 used 18 sequential per-lever calls; a single LLM failure only lost one lever's classification. PR #374's single batch call means one failure loses all 18 classifications. The `LLMExecutor.run()` will retry if `retry_config.max_retries > 0` or `max_validation_retries > 0`, but `LLMExecutor(llm_models=llm_models)` is constructed in `run_single_plan()` (runner.py:206) with defaults `max_retries=0` and `max_validation_retries=0`. No retry is attempted before the total fallback fires.

The single-call architecture makes retry-on-failure more important, not less.

### S2 — `_run_deduplicate` always returns `status="ok"` (runner.py:137–156)

`DeduplicateLevers.execute()` never raises an exception (B1 above). Therefore `_run_deduplicate` always returns `status="ok"`. A run where the LLM call timed out and all 18 levers were silently promoted to "primary" looks identical to a perfect run in the runner's output.

### S3 — `execute_function` closes over mutable `chat_message_list` (deduplicate_levers.py:190–193)

```python
def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchDeduplicationResult)
    chat_response = sllm.chat(chat_message_list)
    return {"chat_response": chat_response, "metadata": dict(llm.metadata)}
```

`chat_message_list` is defined once and captured by reference. If LLMExecutor retries (e.g., after adding a retry config), successive calls all use the same list. This is correct — the list is not mutated. However, if a future enhancement accumulates validation feedback into `chat_message_list` (as identify_potential_levers does for multi-call), this closure pattern would require care. Currently safe, but worth noting as a friction point.

### S4 — Minimum lever count check threshold may be too low (deduplicate_levers.py:258–264)

```python
min_expected = max(3, len(input_levers) // 4)
```

For 18 input levers: `max(3, 4) = 4`. If a model removes 14/18 levers (78%), only 4 survive, which still clears this threshold without triggering a warning. The fallback (18/18 primary, 0 removed) trivially satisfies it. The check is not sensitive enough to catch over-keeping or over-removal in realistic scenarios.

---

## Improvement Opportunities

### I1 — Emit a `classification_fallback` event with per-lever details

When the fallback fires (B4 above), emit a structured event to the runner:

```
classification_fallback | plan_name | fallback_count | cause ("llm_failed" or "lever_missing")
```

This makes degraded runs detectable in `events.jsonl` without reading every `_raw.json`. Maps directly to insight C1 and Q5.

### I2 — Distinguish "LLM failed entirely" vs "LLM missed specific levers" in fallback justification

Currently both cases use identical text: `"Not classified by LLM. Keeping as primary to avoid data loss."` A caller reading the JSON cannot determine whether the LLM produced zero output (timeout) or 17/18 classifications with one omitted. Using `"LLM call failed — no classifications received."` for the total-failure case and `"Not classified by LLM — lever absent from response."` for the partial-miss case would make the difference visible without changing the fallback logic.

### I3 — Expose LLM-call success flag from `DeduplicateLevers` result

Add a boolean field (e.g., `llm_call_succeeded: bool`) or an integer (`llm_call_count: int`) to the `DeduplicateLevers` dataclass. `_run_deduplicate()` can read it to set the correct `calls_succeeded` value (fixing B3) and potentially set `status="degraded"` instead of `status="ok"` (fixing S2).

### I4 — Model-class-aware timeout for `LLMExecutor`

The llama3.1 LLM has a `request_timeout` of 120s (set in its llm_config JSON, enforced by the llama_index Ollama backend). This timeout is appropriate for API models but too short for local CPU-bound inference on complex 18-lever prompts. Two approaches:
- Increase `request_timeout` in the `ollama-llama3.1` llm_config JSON (operator-side fix, no code change needed).
- Add a runner-level flag `--local-model-timeout` that overrides the LLM config timeout for ollama-class models.

The runner's `DEFAULT_PLAN_TIMEOUT = 600` is not the bottleneck — the 120s limit comes from inside the LLM client. Maps to insight C2.

### I5 — Add post-response verification that all input `lever_id`s appear in the LLM response

After parsing `batch_result.decisions`, the code builds `seen_ids` and checks for missing IDs (line 228). This is correct but emits only a Python logger warning. Wrap the check in a helper that also returns the missing IDs, then emit an event or include the missing IDs in the fallback justification text. Maps to insight C3.

### I6 — Retry on partial classification failure (missing lever_ids)

When the LLM returns a valid response but omits some lever_ids (as gpt-oss-20b did for `dcb03988` in hong_kong_game, run 65), the current code silently applies the fallback for the missing IDs. A retry with an explicit instruction ("You missed these lever_ids: [dcb03988] — classify them now") would be more likely to recover the real classification than the generic primary fallback.

---

## Trace to Insight Findings

| Insight observation | Code location | Bug/Pattern |
|---------------------|---------------|-------------|
| N1: llama3.1 times out on silo/parasomnia, all 18 levers get fallback justification, `status="ok"` | deduplicate_levers.py:204, runner.py:155 | B1, B3 |
| N3: gpt-oss-20b misses dcb03988 (Cultural Authenticity), fallback triggered | deduplicate_levers.py:228–236 | B4 (no event), I5, I6 |
| N5: fallback creates misleading "primary" that is indistinguishable from real classifications in outputs.jsonl | deduplicate_levers.py:204, runner.py:155 | B1, B3, B4 |
| Q5: "should the runner log a warning when fallback is triggered" | deduplicate_levers.py:228–236, runner.py | B4, I1 |
| C1: "emit classification_fallback event with lever_id and reason" | runner.py, deduplicate_levers.py | B4, I1 |
| C2: "increase llama3.1 timeout from 120s to 180–240s" | llm_config (not in reviewed files) | I4 |
| C3: "add post-LLM verification of all input lever_ids" | deduplicate_levers.py:228–236 | I5 |
| H3: "missing lever (dcb03988) caused by output truncation or model omission" | deduplicate_levers.py:228–236 | confirmed: model omission caught by existing seen_ids check, but no event emitted (B4) |

---

## PR Review

### Does the implementation match the intent?

**Goal 1 — Single batch call**: Implemented correctly. `execute()` makes exactly one `llm_executor.run(execute_function)` call. The `LLMExecutor` retry mechanism (`max_retries=0` by default) does not fire, so there is genuinely one LLM call per plan. ✓

**Goal 2 — Categorical primary/secondary/remove**: Implemented correctly. `BatchDeduplicationResult` / `LeverClassificationDecision` use a `Literal["primary", "secondary", "remove"]` type, enforced by Pydantic at parse time. The system prompt defines all three classes with decision criteria. ✓

**Goal 3 — Prompt fixes from iter 49 (B2, B3, S1)**: The system prompt includes "compare them against each other before making decisions" and "When two levers overlap, remove the more specific one and keep the more general one." These address the iter 49 issues. ✓

**Goal 4 — Robustness guards (duplicate lever_id, minimum count)**: Both guards are present:
- Duplicate lever_id: lines 217–219 (keep first, skip duplicate).
- Minimum count: lines 257–264 (warning when output < max(3, N//4)).
- Missing lever fallback: lines 228–236.
✓ for the stated guards.

### Gaps and bugs in the PR

**Gap 1 — Robustness guard for missing levers does not guard against total LLM failure (B1)**

The PR's robustness guard handles the case "LLM responds but omits a lever". It does not handle the case "LLM call fails entirely". When the call fails, `batch_result=None`, and the fallback applies to all 18 levers — but the PR presents this as a success. This is the most significant gap: the guard fires in exactly the wrong case (complete failure) while appearing to succeed.

**Gap 2 — No observability for fallback firing (B4)**

The PR adds no mechanism to detect when the robustness guard fires. The `classification_fallback` event mentioned in the iter 50 assessment as a desired addition was not implemented. The analysis pipeline cannot distinguish a clean run from a full-fallback run without reading every `_raw.json` file and scanning for the fallback justification string.

**Gap 3 — `user_prompt` field stores wrong value (B2)**

The `DeduplicateLevers` result stores `project_context` in the `user_prompt` field instead of the assembled prompt. This is a straightforward implementation bug — the variable `user_prompt` is in scope at the `return cls(...)` call (line 271) but `project_context` is passed instead.

**Gap 4 — `calls_succeeded=1` is always hardcoded (B3)**

The PR's architecture uses "single batch call", so `calls_succeeded=1` seems correct as a description of intent. But it's hardcoded as a literal rather than derived from the actual call outcome, meaning it reports success even when the call failed.

### Minor positive observations

- The `input_lever_ids` set check (line 214) correctly rejects hallucinated lever_ids the LLM might invent. This is a solid guard.
- The `seen_ids` deduplication (lines 217–219) correctly handles duplicate lever_ids in the LLM response (a problem noted in PR #373 llama3.1 run).
- Ordering of output levers follows input order (line 241–255 iterates `input_levers`), which preserves the original brainstorm sequence. This is better than iterating decisions, which may have arbitrary LLM-output order.
- The empty-justification guard at line 247–248 prevents zero-length deduplication justifications from reaching downstream steps.

---

## Summary

The PR achieves its stated architectural goals — single batch call with categorical classification — and the system prompt is well-constructed. The robustness guards add value.

The most impactful issues are not about the PR's design choices but about the failure path:

1. **B1** is the highest-priority bug: a complete LLM failure (timeout) is swallowed silently, producing a result that looks like success. The 18/18 fallback and the 1/1 gpt-oss-20b partial miss are both invisible in `outputs.jsonl`. Fix: after the `except` block, check if `batch_result is None` and either re-raise (if all levers would be fallback) or emit an event indicating total failure.

2. **B2** is easy to fix: change `user_prompt=project_context` to `user_prompt=user_prompt` on line 272.

3. **B4** is important for the self-improvement loop: without `classification_fallback` events, the analysis pipeline cannot programmatically distinguish clean runs from degraded ones.

4. **I4** (local model timeout) is a configuration-level fix: increasing the `request_timeout` in the `ollama-llama3.1` llm_config JSON from 120s to 240s would likely eliminate the llama3.1 silo/parasomnia timeout failures without any code changes.
