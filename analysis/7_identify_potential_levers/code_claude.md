# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Multi-call chat history contaminates calls 2 and 3 with prior review text

**File:** `identify_potential_levers.py:234–242`

```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=(
            result["chat_response"].message.content
            or result["chat_response"].raw.model_dump_json()
        ),
    )
)
```

After each LLM call, the full assistant response (raw JSON, including every `review_lever` field) is appended to `chat_message_list`. Calls 2 and 3 therefore receive the complete serialised `DocumentDetails` objects from prior calls as context. Each `review_lever` value contains `"Controls [A] vs. [B]. Weakness: ..."` text.

For models that aggressively continue patterns from the assistant turn (qwen3-30b, documented as the most susceptible), the prior JSON conditions the next generation: the model sees `"review_lever": "Controls X vs. Y. Weakness: ..."` in the prior assistant block and copies that structure into the `consequences` field of the next batch.

The user_prompt (original plan documents) is sent only in call 1 (line 197). Calls 2 and 3 receive only a short name-exclusion instruction (lines 199–203), so the prior assistant JSON is the *dominant* context for those calls — there is no re-grounding in the actual plan text.

This is the root cause of the 100%-contamination pattern in qwen3-30b across runs 43, 50, and 57.

---

### B2 — Trailing-character JSON failure has no recovery path

**File:** `identify_potential_levers.py:223–232`

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

When `sllm.chat(chat_message_list)` is called (line 215) and a model emits a 6th lever fragment *after* the closing brace of the main JSON object, Pydantic raises `"Invalid JSON: trailing characters at line N column M [type=json_invalid]"`. This exception is caught at line 228, wrapped as `LLMChatError`, and immediately re-raised. The entire plan fails with no attempt to truncate the output before the trailing content and retry validation.

Before `max_length=5` was added to `DocumentDetails.levers`, gpt-oss-20b presumably produced 6-lever responses that were silently accepted (or the 6th lever caused an over-count in the merged output, visible as the batch-6 violation). With `max_length=5` now enforced by the schema, the 6th lever's presence at the raw-extraction stage produces the new "trailing characters" failure mode (run 55: 2/5 plans fail).

---

### B3 — Race condition on `set_usage_metrics_path` in multithreaded mode

**File:** `runner.py:106, 140`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # line 106 — no lock held

with _file_lock:
    dispatcher.add_event_handler(track_activity)                  # line 108-110
...
finally:
    set_usage_metrics_path(None)                                  # line 140 — no lock held
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)
```

`set_usage_metrics_path` modifies a global (process-wide) path. When `workers > 1`, multiple threads call this setter concurrently without holding `_file_lock`. Race scenarios:

1. Thread A sets path to `A/usage_metrics.jsonl`; Thread B immediately overwrites it with `B/usage_metrics.jsonl`. Thread A's LLM calls then write to B's file (or to no file if Thread B's `finally` resets it to `None` first).
2. Thread B's `finally` block calls `set_usage_metrics_path(None)` while Thread A is mid-execution, silently disabling A's metric tracking.

The lock correctly guards `dispatcher.add_event_handler` / `remove` but not the path setter.

---

## Suspect Patterns

### S1 — `execute_function` closure captures `chat_message_list` by reference

**File:** `identify_potential_levers.py:213–221`

```python
def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(chat_message_list)
    ...
```

`execute_function` closes over `chat_message_list`, which is mutated on lines 206–211 in each loop iteration. Because `llm_executor.run()` currently appears synchronous, the closure always sees the correct list state. However, if `llm_executor.run()` ever stores the callable for retry/async execution, a later invocation would see a list that has been extended with subsequent messages from further iterations — silently passing wrong context to a retry. This pattern is fragile.

---

### S2 — `summary: str` with no default silently breaks models that previously returned null

**File:** `identify_potential_levers.py:79–81`

```python
summary: str = Field(
    description="Are these levers well picked? ..."
)
```

In batch 6, llama3.1 produced 14 null `summary` values across run 47. With `summary: str` (no `Optional`, no default), any model that omits the field now fails the entire plan at the Pydantic validation step rather than returning a partial result. This is likely intentional (forcing the summary), but it is a silent breaking change. Run 54 (llama3.1) was 5/5 in batch 7, implying llama3.1 now reliably generates summaries — but this has not been verified by reading raw files. If a new model omits the field, the failure mode (Pydantic ValidationError) will look identical to a JSON-format failure and may be mistaken for a content error.

---

### S3 — Dispatcher event handlers are added/removed under lock but fired outside

**File:** `runner.py:108–112, 141–143`

```python
with _file_lock:
    dispatcher.add_event_handler(track_activity)
...
with _file_lock:
    dispatcher.event_handlers.remove(track_activity)
```

The lock serialises structural mutations to `event_handlers`, but event *dispatch* (fired from within `sllm.chat(...)`) happens outside any lock. In multithreaded mode, this means events from Plan B's LLM call can be delivered to Plan A's `TrackActivity` handler if the lists are not safely iterated, depending on the LlamaIndex dispatcher implementation. If the dispatcher iterates `event_handlers` without its own lock, a concurrent `remove()` mid-iteration would raise `RuntimeError: list changed size during iteration`. The current code relies on LlamaIndex's dispatcher being thread-safe internally — that assumption is not verified.

---

## Improvement Opportunities

### I1 — Reset message context for calls 2 and 3 (direct fix for B1)

**File:** `identify_potential_levers.py:195–244`

For `call_index > 1`, construct a *fresh* `chat_message_list` containing:

```
[SYSTEM, USER(user_prompt + "\n\nAlready-generated names: [...]")]
```

Do not include any prior assistant JSON. This removes the contamination conduit entirely. The name-exclusion diversity benefit is preserved because the blacklist is still provided in the user turn. The model is re-grounded in the actual plan documents on each call, which is also likely to improve domain specificity for calls 2 and 3 (currently they only see the name list, not the plan).

---

### I2 — Truncation fallback for trailing-character extraction failure (fix for B2)

**File:** `identify_potential_levers.py:213–215`

When `sllm.chat()` raises a Pydantic validation error matching `"trailing characters"`, extract the raw string from the response, find the last `}` that closes the outermost JSON object (e.g., by walking back from the end), truncate there, and attempt re-validation. This would recover the valid 5-lever payload that the model did produce and avoid a full plan failure caused by one extraneous fragment.

---

### I3 — Post-merge field contamination check

**File:** `identify_potential_levers.py:249–264`

After flattening levers into `levers_raw` (lines 249–251), scan each `consequences` value for the substrings `"Controls "` and `"Weakness:"`. Emit a warning log per violation. Optionally, strip the contaminated suffix before constructing `LeverCleaned`. This provides a safety net for contamination that survives any prompt fix and makes the issue visible in logs even when the output appears structurally valid.

---

### I4 — Assert lever count invariant after merge

**File:** `identify_potential_levers.py:249–251`

Add a post-merge assertion or warning:

```python
expected = total_calls * 5
if len(levers_raw) != expected:
    logger.warning(f"Expected {expected} levers, got {len(levers_raw)}")
```

Currently, if a schema change allows variable-length lever lists (e.g., `min_length` is reduced for a future experiment), the merged output could silently contain fewer than 15 levers. The downstream `deduplicate_levers.py` step expects a specific count. Explicit count validation here makes regression visible.

---

### I5 — Thread-safe `set_usage_metrics_path` (fix for B3)

**File:** `runner.py:106, 140`

Wrap both `set_usage_metrics_path` calls inside `_file_lock`, matching the treatment of `dispatcher.add_event_handler`. Alternatively, consider per-thread metrics tracking (thread-local storage) to avoid global-state contention entirely when `workers > 1`.

---

### I6 — Re-include plan documents in calls 2/3 user message

**File:** `identify_potential_levers.py:199–203`

The current call-2/3 user message is:

```
"Generate 5 MORE levers with completely different names. Do NOT reuse any of these already-generated names: [...]"
```

This contains no plan context. Domain-specific lever naming and consequence specificity both require knowledge of the plan. With the fresh-context fix from I1, the full `user_prompt` is re-sent each time, naturally solving this too. Without I1, the plan content is absent from calls 2 and 3, which explains the tendency of calls 2/3 to produce more generic names and consequences than call 1.

---

## Trace to Insight Findings

| Code location | Bug/Pattern | Explains insight finding |
|---|---|---|
| `identify_potential_levers.py:234–242` | **B1** — prior assistant JSON appended to history | **N3** (qwen3 100% contamination in runs 43, 50, 57); **insight_codex N** ("Run 57 has severe field-boundary failure — consequences contain review text in all 60 levers"); **insight_claude C2** |
| `identify_potential_levers.py:223–232` | **B2** — no recovery from trailing-character Pydantic error | **N2** (gpt-oss-20b new failure mode: `lever_index 6` trailing characters, runs 55); **insight_claude C1**; **insight_codex N** ("Run 55 has promising content but poor reliability — two plans failed JSON validation") |
| `runner.py:106, 140` | **B3** — `set_usage_metrics_path` race in multithreaded mode | Potentially explains unreproducible per-plan timing anomalies and missing usage metric files in parallel runs; not directly named in insights but is a latent correctness issue |
| `identify_potential_levers.py:199–203` | **I6** — no plan context in calls 2/3 user message | **N5** (llama3.1 generic "Silo-X Strategy" naming — calls 2+3 have no plan anchor); **insight_codex N** ("Run 58 reuses cross-domain names like `Funding-Resource Allocation Strategy` across unrelated plans") |
| `identify_potential_levers.py:79–81` | **S2** — `summary: str` no default | **P2** (insight_claude: summary now consistently populated; previously 14 nulls in run 47); **insight_claude Q2** ("Is the summary requirement responsible for success/failure changes?") |
| `identify_potential_levers.py:74–78` (`max_length=5`) | Schema enforcement (not a bug, but the trigger for B2) | **P1** (lever count overflow eliminated in batch 7); **N2** (gpt-oss-20b regression — prior overflow silently succeeded, now fails with trailing-char error) |

---

## Summary

**Two confirmed bugs with direct evidence in the insight files:**

**B1** is the highest-priority fix. The multi-call chat history accumulation (lines 234–242) is the *proven* root cause of qwen3-30b's 100% contamination rate across three consecutive batches. The fix (I1) is well-defined: reset the message list for calls 2 and 3 so prior assistant JSON is never in context. This is synthesis/6 Direction 2, still unimplemented.

**B2** is the root cause of the gpt-oss-20b regression in run 55. The model generates a 6th lever fragment, and the code has no truncation/recovery path — it immediately fails the whole plan. A truncation-before-validate fallback (I2) would recover the valid 5-lever payload and restore gpt-oss-20b to its batch-6 reliability.

**B3** is a thread-safety defect in `runner.py` that affects all parallel runs. It is not yet visible in the insight data (all observed failures are model-quality issues), but it will cause subtle metric corruption as the worker count increases.

The three improvement opportunities **I1 + I3 + I6** together address the contamination family of issues at both the generation and validation levels. **I2** addresses the extraction-failure family. These map directly to the top-ranked recommendations in both insight files.
