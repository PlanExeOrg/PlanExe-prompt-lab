# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` (primary — PR #452 target)
- `self_improve/runner.py` (B4 fix target)
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py` (context only — not changed by PR)

PR diff was unavailable via `gh pr diff`; review is based on current file state plus PR description
in insight_claude.md and known-before/after behavior from runs 85–98.

---

## Bugs Found

### B1 — No retry depth limit: cascading splits exhaust the plan timeout

**File**: `enrich_potential_levers.py:239–246`

```python
except Exception as e:
    lever_ids = [lever.lever_id for lever in batch]
    if len(batch) > 1:
        mid = len(batch) // 2
        ...
        pending_batches.insert(0, batch[mid:])
        pending_batches.insert(0, batch[:mid])
    else:
        logger.error(...)
```

There is no depth counter. A batch of 5 that fails produces sub-batches of 2 and 3. If the
sub-batch of 3 also fails it produces 1+2. If the sub-batch of 2 fails it produces 1+1. Worst
case, 5 failing levers create up to 9 LLM calls (5 + 2 + 1 + 1) before hitting single-lever
skip. Each call can consume its full provider timeout before failing.

For gpt-oss-20b (context_window=3900, DeepInfra), each failing batch call takes 30–60 s. With
three plans of 15 levers each, and multi-level retry on every batch, this compounds to fill the
entire 600 s budget — confirmed in run 93 (N1, N3 in insight).

**Fix direction**: track a `retry_depth` field alongside each pending batch (e.g. store tuples
`(batch, depth)`). Skip retry when `depth >= 1` and log the skip. This caps the overhead at one
extra round of splits.

---

### B2 — No remaining-time guard before queueing retries

**File**: `enrich_potential_levers.py:244–246`

The retry insertion happens unconditionally:
```python
pending_batches.insert(0, batch[mid:])
pending_batches.insert(0, batch[:mid])
```

`EnrichPotentialLevers.execute()` has no concept of elapsed time. It cannot know that the
calling thread is 580 s into a 600 s plan budget. Retries are inserted even when there is
insufficient time to complete them, wasting the remainder of the plan timeout on calls that will
never finish.

**Fix direction**: Pass an optional deadline (`time.monotonic()` + budget) into `execute()`.
Before inserting sub-batches, check `time.monotonic() < deadline - safety_margin`. If not, log
and skip.

---

### B3 — UUID injected into `full_lever_context_str` despite known-problem documentation

**File**: `enrich_potential_levers.py:168`

```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

The OPTIMIZE_INSTRUCTIONS block added by D5 (lines 87–91) explicitly documents this as a known
problem: "The full_lever_context_str includes lever_id UUIDs, causing models to copy UUIDs into
synergy_text and conflict_text in varying formats." The PR updated the documentation but not the
code. The raw UUID is still exposed to the model on every batch call.

Confirmed in run 92 (llama3.1): conflict_text contains
`"(9bc93565-67b1-49fc-afb9-4d310510f698)"`.

**Fix**: `f"- {lever.name}"` (name only).

---

### B4 — Silent under-generation: partial batch results accepted without retry

**File**: `enrich_potential_levers.py:225–232`

```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update(...)
    else:
        logger.warning(...)
```

If the LLM returns characterizations for only 3 of 5 requested levers (which weaker models do
when they truncate output), `batches_succeeded` is incremented at line 223 and the 2 missing
levers are silently dropped. They eventually get excluded at line 254 (`if all(k in data …)`),
logged as errors, and omitted from the output — but there is no retry. The caller has no
indication that levers were silently skipped within a "succeeded" batch.

**Fix direction**: After processing `batch_result.characterizations`, compare the set of
returned `lever_id`s against `{lever.lever_id for lever in batch}`. If levers are missing, log
a warning with the count and the missing IDs. Optionally re-queue the missing levers as a
new single-call batch.

---

## Suspect Patterns

### S1 — Late-binding closure over mutable loop variable

**File**: `enrich_potential_levers.py:210–220`

```python
chat_message_list = [system_message, ChatMessage(role=MessageRole.USER, content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)   # captures by reference
    ...

result = llm_executor.run(execute_function)
```

`execute_function` closes over `chat_message_list` by name, not by value. In the current
synchronous call path this is safe: `run()` calls `execute_function` before the next loop
iteration reassigns `chat_message_list`. However, if `LLMExecutor.run()` ever caches or
re-invokes the function asynchronously (e.g. for retries with fallback models), it would
use the *next* batch's message list. A defensive fix is a default argument binding:
`def execute_function(llm, _msgs=chat_message_list)`.

---

### S2 — Global dispatcher mutation with multiple workers

**File**: `runner.py:248–250, 280–282`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path` is thread-local (safe), but `dispatcher.add_event_handler` adds to a
**global** handler list. When `workers > 1`, N `TrackActivity` objects are registered
simultaneously. LlamaIndex will fire events to *all* of them, so LLM events from plan A flow
into plan B's `usage_metrics.jsonl`. This is likely a pre-existing issue not introduced by
PR #452 and is benign when `workers == 1` (the common case for gpt-oss-20b), but it is worth
noting.

---

### S3 — `check_option_count` validator allows more than 3 options

**File**: `identify_potential_levers.py:147–158`

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v
```

The field description says "Exactly 3 options for this lever. No more, no fewer." The validator
only enforces `< 3`. Over-generation (4, 5, 6 options) passes silently. Downstream steps that
iterate over exactly 3 options could get unexpected results. The comment above the validator
(line 153) says "Over-generation (>3) is tolerable" — if that is the deliberate policy, the
field description should say ">= 3 options" rather than "exactly 3".

---

## Improvement Opportunities

### I1 — Adaptive BATCH_SIZE for small-context models (critical)

**File**: `enrich_potential_levers.py:95, 159–168`

```python
BATCH_SIZE = 5   # hardcoded
```

gpt-oss-20b has `context_window=3900` and `num_output=8192`. With BATCH_SIZE=5, the enriched
output for 5 levers consistently overflows the 8192-token output cap. The retry mechanism (B1)
is treating a symptom; the root cause is that BATCH_SIZE=5 is too large for this model.

`LLMExecutor.run()` passes an `LLM` instance to `execute_function`, which has `llm.metadata`
available. A per-call adaptive batch size can be computed there:

```python
# inside execute_function, or before building pending_batches:
context_window = llm.metadata.get("context_window", 8192)
effective_batch = 2 if context_window < 6000 else BATCH_SIZE
```

Expected outcome for gpt-oss-20b: BATCH_SIZE=2 → output ~3500 tokens/batch → no overflow →
no retries → all 5 plans complete within budget. This would eliminate the root cause behind
N1, N2, and N3.

---

### I2 — No observability for skipped levers in enrich step

**File**: `runner.py:577–583`

The `partial_recovery` event is emitted only for `identify_potential_levers`:

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

For `enrich_potential_levers`, if levers are skipped (single-lever batch failure or under-
generation), `PlanResult` does not carry that information and no event is emitted. The operator
only sees `status="ok"` with a normal `calls_succeeded`, while the output JSON silently has
fewer levers than the input.

**Fix direction**: Add a `levers_skipped: int | None` field to `PlanResult`. Set it from
`len(levers_to_characterize) - len(result.characterized_levers)` in `_run_enrich`. Emit a
`partial_recovery` event when `levers_skipped > 0`.

---

### I3 — Description elaboration guidance missing from runtime system prompt

**File**: `enrich_potential_levers.py:136–149` (`ENRICH_LEVERS_SYSTEM_PROMPT`)

OPTIMIZE_INSTRUCTIONS (lines 82–86) documents "consequence echoing without elaboration" as a
known problem for llama3.1. The current description instruction is:

> `description`: (80-100 words) Clearly explain the lever's purpose, what it controls, its
> objectives, and key success metrics.

This does not explicitly prohibit echoing consequences verbatim. Adding one sentence such as
"Do not paraphrase the lever's consequences field — use it only as grounding context, then
elaborate on purpose, scope, and decision-relevant implications that go beyond it." would
directly address the known problem. (Labeled H1 in insight_claude.md.)

---

### I4 — `enriched_levers_map` ordering lost if LLM returns levers out of order

**File**: `enrich_potential_levers.py:252–260`

```python
for lever_id, data in enriched_levers_map.items():
```

`enriched_levers_map` is a plain `dict` built from the input list, preserving insertion order
(Python 3.7+). But if the LLM returns characterizations for levers in a different order from
the batch, `enriched_levers_map` retains the original order while accepting updates keyed by
`lever_id`. The final output order is the original input order, regardless of LLM return order.
This is correct and worth preserving explicitly with a comment.

---

## Trace to Insight Findings

| Insight observation | Code location | Root cause |
|---------------------|---------------|------------|
| N1 — gpt-oss-20b timeouts after retry | `enrich_potential_levers.py:239–246` (B1 above) | No retry depth limit; every failing batch generates more retries, each consuming full provider timeout |
| N2 — gpt-oss-20b context_window=3900 makes batch failures systematic | `enrich_potential_levers.py:95` (I1 above) | BATCH_SIZE=5 hardcoded; no adaptive sizing for small-context models |
| N3 — Timeout wastes runner budget | `enrich_potential_levers.py:244–246` (B2 above) | No remaining-time guard; retries inserted even when budget is nearly exhausted |
| N4 — UUID in full_lever_context_str | `enrich_potential_levers.py:168` (B3 above) | `lever_id` still included in context string despite D5 documenting the problem |
| N5 — D5 has no runtime effect | `enrich_potential_levers.py:27–92` | OPTIMIZE_INSTRUCTIONS is developer documentation only; it is never injected into the runtime system prompt |
| P1 — Retry works for 2/5 gpt-oss-20b plans | `enrich_potential_levers.py:237–250` | Split logic is correct for cases that complete within budget |
| P2 — calls_succeeded fixed | `runner.py:184` | `result.batches_succeeded` now read from `EnrichPotentialLevers` result instead of hardcoded `1` |

---

## PR Review

### B1 (per-batch retry) — Implementation is correct but incomplete

The retry logic in `enrich_potential_levers.py:237–250` correctly:
- catches exceptions per batch
- splits a failing batch of N into halves
- inserts sub-batches at the front of `pending_batches` (correct FIFO order for sub-tasks)
- skips single-lever failures rather than aborting the plan

Missing from the PR:
1. **No depth limit** (code bug B1 above). The insight recommends one split level only; the
   current code splits indefinitely down to size-1.
2. **No time guard** (code bug B2 above). The enrich step has no budget awareness.
3. **D5 notes the UUID bug but the fix was excluded** (code bug B3 above). This is a minor
   omission but leaves the documented problem open.

These gaps mean the intent (recover gpt-oss-20b without wasting time budget) is only half
achieved: 2 plans recovered but 3 plans now timeout instead of failing fast.

### B4 (calls_succeeded reporting) — Clean and correct

`runner.py:184` now reads `result.batches_succeeded`. `EnrichPotentialLevers.execute()` sets
`batches_succeeded` at line 223 for every successfully processed batch. For gpt-oss-20b's silo
run (3 original batches + 1 retry pair), the count is 4, which matches the usage_metrics
evidence. This fix is complete and has no edge cases.

### D5 (OPTIMIZE_INSTRUCTIONS update) — Accurate documentation, no runtime effect

The two new entries (lines 82–91) accurately describe observed problems. They have no runtime
effect (N5 in insight). The UUID entry is inconsistent with the code (B3 above) — the
documentation says it's a problem, but the fix was deferred.

### Edge cases the PR misses

1. **Partial success within a batch** (B4 above): if 3/5 levers are returned by a successful
   LLM call, the batch is counted as succeeded and the 2 missing levers are silently dropped.
   There is no retry path for partial under-generation.

2. **Sub-batch ordering**: `pending_batches.insert(0, batch[mid:])` then
   `pending_batches.insert(0, batch[:mid])` results in `[batch[:mid], batch[mid:], ...]` — the
   first half is processed before the second half. This is the expected order and is correct.

3. **`batches_succeeded` counts only top-level successes**: a batch that failed and then
   succeeded as two sub-batches contributes 2 to `batches_succeeded` (one per sub-batch), not
   1. This inflates the count slightly relative to "original batches" but is still more
   informative than the former hardcoded `1`.

---

## Summary

**PR #452 introduced two changes with correct intent but one incomplete implementation:**

- **B4 (calls_succeeded)** is cleanly fixed in `runner.py:184`. No issues.

- **B1 (retry)** works for simple cases (single failure per plan) but has two missing guards:
  a depth limit (B1 above) and a remaining-time check (B2 above). These cause gpt-oss-20b's
  3 failing plans to exhaust the full 600 s budget instead of failing quickly, which is worse
  than the pre-PR behavior for those plans.

- **D5 (OPTIMIZE_INSTRUCTIONS)** documents the UUID problem accurately (lines 87–91) but the
  corresponding one-line code fix (`enrich_potential_levers.py:168`) was not included. This is
  the highest-confidence, lowest-risk change in the backlog.

**Highest-impact follow-up actions** (in order):

| Priority | Action | File:line | Expected impact |
|----------|--------|-----------|-----------------|
| C1 | Adaptive BATCH_SIZE based on `context_window` | `enrich_potential_levers.py:95,159` | Eliminates gpt-oss-20b root cause; all 5 plans likely succeed |
| C2 | Add retry depth limit (max 1 split) | `enrich_potential_levers.py:239` | Prevents timeout cascade; failing plans fail in ~60–120 s |
| C3 | Fix `full_lever_context_str` to name-only | `enrich_potential_levers.py:168` | Eliminates UUID leakage for llama3.1 and qwen3-30b |
| C4 | Add remaining-time guard before retry | `enrich_potential_levers.py:244` | Belt-and-suspenders for C2 |
| H1 | Add anti-echoing clause to description guidance | `enrich_potential_levers.py:144` | Improves llama3.1 description quality toward baseline |
