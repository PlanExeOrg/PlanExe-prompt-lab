# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1: User prompt is appended twice for the first LLM call

**File:** `identify_potential_levers.py:148–174`

`chat_message_list` is initialized at lines 148–157 with a `SYSTEM` + `USER(user_prompt)` pair:

```python
chat_message_list = [
    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
    ChatMessage(role=MessageRole.USER, content=user_prompt),   # ← already here
]
```

Then `user_prompt_list` is defined as `[user_prompt, "more", "more"]`. In the first loop iteration, the loop body at lines 169–174 appends the user prompt **again**:

```python
chat_message_list.append(
    ChatMessage(role=MessageRole.USER, content=user_prompt_item)  # ← duplicated
)
```

So the message sequence sent to the LLM on the first call is:

```
SYSTEM → USER(user_prompt) → USER(user_prompt)
```

Consecutive user messages without an interleaved assistant turn are unusual. Most inference APIs either silently merge them, ignore the second, or behave inconsistently — which explains why the first call and third call can be clean for a given model while the second call (which sees a proper SYSTEM→USER→ASSISTANT→USER→ASSISTANT→USER sequence) behaves differently. The doubled initial prompt also wastes tokens on every call.

**Fix direction:** Remove `user_prompt` from the initial `chat_message_list` (keep only the SYSTEM message), and let the loop handle all three user turns uniformly. Alternatively, start `user_prompt_list` with `"more", "more"` (two items) and keep the initialization as-is.

---

### B2: Assistant content stored as a dict, not a string

**File:** `identify_potential_levers.py:197–202`

```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].raw.model_dump(),  # ← dict, not str
    )
)
```

`model_dump()` returns a Python `dict`. ChatMessage's `content` field is typed as `str`. Llama-index coerces or serializes this internally, but the exact serialization is implementation-specific and may not match what the LLM produced verbatim. This means the conversation history fed back into subsequent calls (calls 2 and 3) can differ in format from the actual model response, potentially confusing the model about the expected output structure.

---

### B3: No post-call validation of lever count or field content

**File:** `identify_potential_levers.py:204–223`

After each LLM call the code appends `result["chat_response"].raw` directly to `responses` with no checks on:

1. Whether `response.levers` actually contains exactly 5 entries (Pydantic enforces the type as `list[Lever]` but not the length).
2. Whether any `review_lever` strings contain unfilled bracket placeholders (`\[.*?\]`).
3. Whether any lever has fewer or more than 3 options.

All three of these violations appear in the history runs and survive to the final `002-10` file.

---

### B4: No deduplication of lever names at merge time

**File:** `identify_potential_levers.py:207–223`

The three responses are merged with:

```python
for response in responses:
    levers_raw.extend(response.levers)
```

There is no cross-call uniqueness check. Each of the three independent LLM calls receives the same plan context and the same system prompt, so they naturally converge on the same high-level themes and produce repeated lever names. This is a structural artifact of the multi-call approach, not a model failure.

The docstring at line 3 acknowledges this: *"The output contains near duplicates, these have to be deduplicated."* But it defers that to `deduplicate_levers.py` (step `002-11`), leaving the `002-10` file with 33%+ name duplication.

---

### B5: No preflight model validation before scheduling runs

**File:** `runner.py:315–389` (the `run()` function)

The runner iterates over all plan directories and calls `run_single_plan()` for each one. `LLMModelFromName.from_names()` is called inside `run_single_plan()` (line 93) — once per plan, at execution time, not before the loop starts. If a model name is unresolvable (e.g., a config entry is missing), this is only discovered when the first plan attempt fails. In run 08, this caused all five plans to fail with "LLM not found" after negligible processing time (0.01–0.02s each).

A preflight call to `LLMModelFromName.from_names()` before the plan loop would surface this error immediately with a clear message rather than producing five silent per-plan failures.

---

### B6: Global state (`set_usage_metrics_path`) modified outside the lock in threaded mode

**File:** `runner.py:96–110`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # ← outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)
```

When `workers > 1`, multiple threads execute `run_single_plan()` concurrently. `set_usage_metrics_path` writes to a module-level global. Between one thread setting the path and acquiring the lock, another thread can overwrite it. This means usage metrics for one plan can be written to another plan's directory, or lost entirely. The comment at lines 97–98 acknowledges these are global-state concerns but the lock scope does not cover `set_usage_metrics_path`.

---

### B7: Schema field description contradicts system prompt on option count

**File:** `identify_potential_levers.py:33–35`

```python
options: list[str] = Field(
    description="2-5 options for this lever."
)
```

The system prompt (line 90) says: *"Each lever's `options` field must contain exactly 3 qualitative strategic choices."*

The Pydantic field description says *"2-5 options"*. In structured-output mode, LLM providers use the field description to guide generation. This ambiguity gives the model latitude to produce 2 or 4 or 5 options — which is exactly what runs 00 and 09 did.

---

## Suspect Patterns

### S1: Assistant message content format may not round-trip cleanly

**File:** `identify_potential_levers.py:200`

`result["chat_response"].raw.model_dump()` produces a nested dict with keys like `strategic_rationale`, `levers`, `summary`. This is stored as the `content` of an ASSISTANT ChatMessage. For the second and third calls, this dict-as-content appears in the conversation history. Models are trained on string conversation histories, so a Python dict passed as `content` may not serialize to exactly what the model originally generated. If llama-index JSON-encodes it, the structure may differ from the model's original text response.

### S2: `LLMChatError` wraps and re-raises, masking original exception type

**File:** `identify_potential_levers.py:191–195`

```python
except Exception as e:
    llm_error = LLMChatError(cause=e)
    ...
    raise llm_error from e
```

All non-`PipelineStopRequested` exceptions from the LLM call are wrapped in `LLMChatError`. In `run_single_plan()` (runner.py:130), the outer `except Exception` catches these and stores `str(e)` as the error message. If `LLMChatError.__str__` doesn't include the original exception's message, the diagnostic stored in `outputs.jsonl` may be less informative than the underlying error (e.g., "LLM not found" might appear as a generic wrapper message).

### S3: Resume logic only skips completed plans, does not retry partial failures

**File:** `runner.py:335–345`

On resume, plans with `status == "ok"` are skipped. Plans with `status == "error"` are retried. This is correct behavior. However, if a plan produced a partial output (e.g., wrote `002-9` but not `002-10` due to a crash mid-write), the resume logic does not detect this and the stale partial file is silently used. The output files are not validated before being skipped.

---

## Improvement Opportunities

### I1: Validate lever count per LLM response

After each call, assert (or log a warning when) `len(response.levers) != 5`. Counts outside 5 should trigger a retry rather than being silently merged into the final output. This would catch the option-count violations in runs 00 and 09.

### I2: Validate bracket placeholders and option counts before accepting a response

Add a post-parse validator that rejects any response containing `[` and `]` in `review_lever` fields, and any lever with fewer or more than 3 options. Return a retry signal rather than accepting and merging the contaminated output. This would have caught the second-call leakage in run 00.

### I3: Deduplicate lever names at merge time

After `levers_raw.extend(response.levers)`, track seen names and skip (or rename) duplicates before populating `levers_cleaned`. Cross-call deduplication before writing `002-10` would reduce the baseline's 33% name-duplication rate without waiting for the downstream `002-11` step.

### I4: Preflight model resolution

In `runner.py:run()`, resolve all model names once before the plan loop starts. If any model is not found, fail fast with a clear error rather than discovering the failure per-plan.

### I5: Fix option count description to match system prompt

Change the `Lever.options` field description from `"2-5 options for this lever."` to `"Exactly 3 options for this lever."` to align structured-output guidance with the system prompt constraint.

### I6: Move `set_usage_metrics_path` inside the lock for thread safety

In `run_single_plan()`, acquire `_file_lock` before calling `set_usage_metrics_path` and release it only after `dispatcher.add_event_handler`. This prevents cross-thread metric path contamination when `workers > 1`.

### I7: Initialize chat_message_list without the initial user message

Remove the duplicate initial `USER(user_prompt)` from `chat_message_list` initialization (or drop it from `user_prompt_list`). This gives all three LLM calls a uniform, non-redundant conversation structure.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Root Cause |
|---|---|---|
| Template leakage in run 00, second call (insight_claude §1; insight_codex negative §2) | `identify_potential_levers.py:148–174` (B1), `identify_potential_levers.py:204` (B3) | B1's doubled user prompt creates an unusual two-consecutive-USER sequence for call 1, then calls 2 and 3 see a conversation history that includes the doubled opener — this can push weaker models into template-filling mode on later calls. B3's absence of validation lets the leaked output pass through unchanged. |
| Bracket placeholders survive to `002-10` output (both insights) | `identify_potential_levers.py:204` (B3) | No post-call validation checks for `\[.*?\]` in `review_lever`; the contaminated call-2 response is accepted and merged. |
| Cross-call name duplication (33% in baseline) (insight_claude §5, Table 6; insight_codex negative §8) | `identify_potential_levers.py:207–210` (B4) | Each call gets the same prompt with no knowledge of names chosen in prior calls; names are merged without deduplication at line 210. |
| Run 09 option-count violations (insight_claude Codex negative §7; insight_codex Table constraint violations) | `identify_potential_levers.py:33–35` (B7) | Field description says "2-5 options", system prompt says "exactly 3". The structured-output layer guides generation by the field description, giving the model permission to produce 2–5. |
| Run 00 option-count violations (7 violations per insight_codex Table) | `identify_potential_levers.py:33–35` (B7) + B3 | Same field description ambiguity; no post-call count check. |
| Run 08 "LLM not found" for all 5 plans (insight_claude §3; insight_codex negative §1) | `runner.py:93` inside `run_single_plan()` (B5) | Model resolution is deferred to per-plan execution; no preflight catch. |
| Run 03 schema mismatch (missing `strategic_rationale`, `levers`, `summary`) (insight_claude §3) | `identify_potential_levers.py:204` (B3) | No schema validation before accepting a response; `DocumentDetails` Pydantic parsing may raise, but the error is caught at the runner level and produces an error row rather than a retry. |
| JSON truncation/parse failures for weaker models (insight_claude §4) | B3 + S2 | No retry at the call level inside `execute()`; the exception is wrapped in `LLMChatError` and propagated to `run_single_plan()`, which records it as a plan-level failure with no per-call retry. |
| Global metric contamination risk when `workers > 1` | `runner.py:106` (B6) | `set_usage_metrics_path` not protected by the lock. |
| Resume does not detect stale partial outputs | `runner.py:335–345` (S3) | Only `status == "ok"` lines in `outputs.jsonl` are checked; no file-level integrity validation. |

---

## Summary

The two most impactful bugs are:

**B1 (doubled user prompt)** is the most structurally surprising. Every first LLM call receives `SYSTEM → USER(plan) → USER(plan)` — two consecutive identical user messages. This is the plausible root cause of the stochastic intra-run inconsistency observed in run 00 (calls 1 and 3 are clean; call 2, which has a properly structured history built on top of the malformed first call, behaves differently).

**B3 (no post-call validation)** is the widest-impact gap. Bracket placeholder leakage, option-count violations, and schema mismatches all survive to the final `002-10` file because nothing checks them before the merge step.

**B4 (no merge-time deduplication)** is structurally guaranteed to produce duplicates whenever the same plan is processed with three independent calls — which is every single run.

**B5 (no preflight model validation)** is the sole cause of run 08's complete 0/5 failure rate. It is the easiest fix with the highest per-fix return.

**B7 (field description contradicts system prompt on option count)** is the likely cause of option-count violations in runs 00 and 09: structured-output providers use the field-level description for generation guidance, and "2-5 options" is more permissive than the system prompt's "exactly 3".

The prompt-level issues (example name leakage, bracket placeholder prohibition, measurable-outcome suffix) described in both insight files are genuine quality gaps, but they are secondary to these code-level failures. Fixing B1, B3, B4, and B5 would materially improve the operational success rate and output cleanliness independent of any prompt changes.
