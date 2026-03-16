# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Thread-safety race on global `set_usage_metrics_path` in runner.py

**File**: `prompt_optimizer/runner.py:106`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # ← outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)  # ← inside lock
```

`set_usage_metrics_path` writes to global state but is called **outside** `_file_lock`. When `workers > 1`, two threads can interleave: thread A sets its path, thread B overwrites it before thread A finishes, so thread A's usage metrics land in thread B's output directory (or vice versa). The `finally` block at line 140 has the same problem:

```python
set_usage_metrics_path(None)          # ← outside lock
with _file_lock:
    dispatcher.event_handlers.remove(track_activity)   # ← inside lock
```

Both calls should move inside `_file_lock` alongside the dispatcher operations.

---

### B2 — Partial LLM call results are silently discarded on failure

**File**: `identify_potential_levers.py:231–240`

```python
try:
    result = llm_executor.run(execute_function)
except PipelineStopRequested:
    raise
except Exception as e:
    llm_error = LLMChatError(cause=e)
    ...
    raise llm_error from e
```

The loop makes 3 calls. If call 1 and call 2 succeed and call 3 fails, the `responses` list already contains 2 valid `DocumentDetails` objects (lines 242–244 have already appended them). But raising on call 3 unwinds the entire `execute()` method, discarding those 2 responses and all their levers. The caller gets nothing instead of a partial result.

This is the direct code-level cause of the empty output directories observed in runs 88 and 90 (plans fail with zero output files even though earlier calls may have returned valid JSON).

---

### B3 — No enforcement of `options == 3` after parse

**File**: `identify_potential_levers.py:47–50, 60–71`

The `options` field description says "Exactly 3 options for this lever. No more, no fewer," but there is no `@field_validator` that enforces `len(options) == 3`. The only validator on this field (`parse_options`, lines 60–71) only converts a stringified JSON array to a list; it does not check the length. A model returning 2 or 4 options passes Pydantic validation silently, enters `levers_cleaned`, and flows into the final `002-10-potential_levers.json` with no warning.

This is why run 89 produced three levers with 2 options each in the final output (insight_codex.md: "levers with wrong option count: 3").

---

## Suspect Patterns

### S1 — `execute_function` closure inside a loop is fragile

**File**: `identify_potential_levers.py:221–229`

```python
for call_index in range(1, total_calls + 1):
    ...
    messages_snapshot = list(call_messages)

    def execute_function(llm: LLM) -> dict:
        sllm = llm.as_structured_llm(DocumentDetails)
        chat_response = sllm.chat(messages_snapshot)   # closes over loop variable
        ...
```

This works correctly today because `llm_executor.run` is synchronous and invokes the function before the loop variable is reassigned. However, if `llm_executor.run` ever becomes async or defers the callable, it will silently read the wrong (latest) `messages_snapshot`. The safe pattern is to pass the snapshot as a default argument: `def execute_function(llm: LLM, _snap=messages_snapshot) -> dict:`.

---

### S2 — No overflow clamping before merge

**File**: `identify_potential_levers.py:247–249`

```python
levers_raw: list[Lever] = []
for response in responses:
    levers_raw.extend(response.levers)
```

After PR #286 removed `max_length=7`, a raw response with 8 or 9 levers flows directly into the merged list with no log entry or metric. The PR's stated justification is that `DeduplicateLeversTask` handles extras, but this step's own output (`002-10-potential_levers.json`) can silently contain 21–24 levers per plan. There is no telemetry to distinguish normal counts from overflow counts.

---

### S3 — Case-sensitive deduplication

**File**: `identify_potential_levers.py:255–258`

```python
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

Exact string matching. "Revenue Strategy" and "revenue strategy" are treated as distinct levers. The 3-call prompt already instructs models to use different names, so in practice the deduplication mostly catches accidental exact repeats. The downstream `DeduplicateLeversTask` is supposed to handle semantic near-duplicates, so this is likely acceptable, but the discrepancy between what the comment in the docstring promises and what the code enforces is worth noting.

---

### S4 — `min_length=5` has no tested lower-bound coverage

**File**: `identify_potential_levers.py:81–84`

```python
levers: list[Lever] = Field(
    min_length=5,
    description="Propose 5 to 7 levers."
)
```

The `min_length=5` constraint is kept from before PR #286. No run in 81–94 triggered it (insight_claude.md, Q2), so it is untested. If a model consistently returns 4 levers, the entire call fails and is re-raised as `LLMChatError` — the same class of hard failure the PR was designed to avoid, just on the lower bound. Whether 5 is the right floor is unvalidated.

---

## Improvement Opportunities

### I1 — Add `@field_validator('options')` to enforce exactly 3 items

**File**: `identify_potential_levers.py:60–71`

Add a length check inside `parse_options` (or a separate validator) so that levers with wrong option counts are rejected at parse time rather than silently accepted:

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) != 3:
        raise ValueError(f"options must have exactly 3 items, got {len(v)}")
    return v
```

This would make run 89's malformed levers fail loudly at the response level, allowing a retry, rather than polluting the final merged output.

---

### I2 — Collect partial results instead of raising on 3rd-call failure

**File**: `identify_potential_levers.py:231–240`

Change the loop so that if calls 1–2 succeeded and call 3 fails, the method returns a partial result (or logs a warning and continues) rather than discarding everything. For example: convert the `raise` inside the loop to a `logger.warning` + `break` when `len(responses) >= 1` already has valid data. This would preserve levers from successful calls.

---

### I3 — Add per-call overflow telemetry

**File**: `identify_potential_levers.py:242–244`

After appending to `responses`, emit a debug/warning log if `len(result["chat_response"].raw.levers) > 7`:

```python
lever_count = len(result["chat_response"].raw.levers)
if lever_count > 7:
    logger.warning(f"Call {call_index}: model returned {lever_count} levers (soft limit is 7)")
```

This makes post-PR over-generation visible without reverting the schema change.

---

### I4 — Move `set_usage_metrics_path` inside `_file_lock` in runner.py

**File**: `prompt_optimizer/runner.py:106, 140`

Both the setup and teardown calls to `set_usage_metrics_path` should be inside `_file_lock` to match the dispatcher operations and prevent cross-thread metric contamination (see B1).

---

### I5 — Save partial outputs on plan failure

**File**: `prompt_optimizer/runner.py:130–138`

The `run_single_plan` exception handler at line 130 catches all errors and returns a `PlanResult(status="error")` — but `plan_output_dir` exists and is empty. Saving whatever partial data exists (e.g., `responses` if available) before returning the error would aid diagnosis. This is the code-side complement to the insight-reported empty output directories.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| Runs 88, 90: empty output directories on failure (insight_claude.md §C4) | **B2** — exception on any LLM call discards all previously collected responses |
| Run 89: 3 levers with 2 options each in final output (insight_codex.md table, row 89) | **B3** — no `len(options) == 3` validator; bad levers pass Pydantic silently |
| Run 89: incomplete review fields (missing `Controls` or `Weakness:`) pass through | **B3** / **S2** — no post-parse field-format enforcement; the description is guidance, not a validator |
| Post-PR over-generation: 3 raw responses with >7 levers not flagged (insight_codex.md) | **S2** — no overflow telemetry after `max_length` removal |
| Usage metrics potentially cross-contaminated under parallel workers | **B1** — `set_usage_metrics_path` called outside `_file_lock` |
| qwen3 consequence contamination (review text bleeds into consequences field) | Not caused by a code bug; the `consequences` field description in `Lever` (lines 34–46) already says "Do NOT include 'Controls ... vs.', 'Weakness:'" but there is no validator that enforces this. A post-parse strip/reject for levers where `consequences` ends with a substring matching `review_lever` would catch it — currently no such check exists. |

---

## PR Review

**PR #286**: Remove `max_length=7` hard constraint on levers schema.

### Does the implementation match the intent?

**Yes.** The change is minimal and correct:

```python
# Before
levers: list[Lever] = Field(min_length=5, max_length=7, ...)

# After
# No max_length constraint: if a model returns more than 7 levers, the downstream
# DeduplicateLeversTask handles extras. A hard cap would discard the entire response
# and waste tokens retrying.
levers: list[Lever] = Field(min_length=5, ...)
```

The comment explains the rationale. The evidence confirms it: run 87 haiku failed with `type=too_long` on 8 levers; run 94 haiku succeeded on the same plan with the same model.

### Edge cases the PR misses

1. **Over-generation is now invisible.** Removing `max_length` means `>7` levers per raw call silently inflate the merged output. The PR adds no warning, counter, or clamping. The insight files report 3 raw responses exceeded 7 levers in runs 88–94. Nothing in the code surfaces this.

2. **`min_length=5` is the remaining hard failure.** The PR correctly preserves it, but the same logic that made `max_length=7` harmful could apply: a model consistently returning 4 levers would fail every call and discard all levers, with no partial recovery. This edge case is documented in insight_claude.md Q2 as untested.

3. **The PR does not address option-count enforcement (B3)**. The freed schema allows >7 levers per call, but a lever with 2 options still passes. These are separate dimensions of output quality, and neither the old nor the new schema validates option count.

### Does the PR introduce new issues?

No regressions observed. The llama timeout (run 89) is independent of the schema change. Models that previously stayed within 7 levers still do; the 3 overflow responses (runs 89, 94) are edge cases, not systematic failures.

### Verdict

The PR is **correct and well-scoped**. The targeted failure class is eliminated; no regressions. The follow-on work (I3: overflow telemetry; B3: option-count validation) is separate and should not block this change.

---

## Summary

| ID | Severity | Description |
|---|---|---|
| B1 | Medium | Thread-safety race: `set_usage_metrics_path` called outside `_file_lock` in `runner.py` — usage metrics can cross-contaminate plans under parallel workers |
| B2 | Medium | Partial LLM call results discarded on failure — all levers from successful calls lost if any call raises |
| B3 | Medium | No `len(options) == 3` post-parse validator — levers with wrong option count pass silently into final output |
| S1 | Low | Closure over loop variable `messages_snapshot` — safe now, fragile if `llm_executor.run` becomes async |
| S2 | Low | No overflow telemetry after PR #286 removed `max_length=7` — >7 levers per call is invisible |
| S3 | Low | Case-sensitive exact deduplication — "Revenue Strategy" vs "revenue strategy" are distinct |
| S4 | Low | `min_length=5` is untested — could cause symmetric hard failures for under-generating models |
| I1 | Improvement | Add `@field_validator('options')` enforcing exactly 3 items |
| I2 | Improvement | Return partial result when some calls succeed and one fails |
| I3 | Improvement | Emit warning log when raw call returns >7 levers |
| I4 | Improvement | Move `set_usage_metrics_path` inside `_file_lock` (fixes B1) |
| I5 | Improvement | Save partial outputs to disk on plan failure for post-mortem diagnosis |

The most impactful unfixed issues are **B1** (data integrity under parallel execution), **B2** (wasted work on partial failures), and **B3** (silent option-count violations degrading final output quality). PR #286 is correctly implemented and should be kept.
