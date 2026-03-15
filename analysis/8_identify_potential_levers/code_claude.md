# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Follow-up call user prompt hardcodes "5 to 7 MORE levers", contradicting candidate system prompt
**File:** `identify_potential_levers.py:203`

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    ...
)
```

When the runner supplies a candidate system prompt that says "EXACTLY 5 levers per response", this hardcoded user message for calls 2 and 3 directly contradicts it. Because user-turn instructions typically dominate system-turn instructions in practice, models follow the user turn and return 7 levers instead of 5. The candidate prompt's constraint is silently overridden for every multi-call run.

This is the single highest-impact bug in the file. It is the primary code-level cause of the 5→7→7 lever count pattern observed in runs 61 and 66.

---

### B2 — `DocumentDetails.levers` schema allows 5–7, silently validating overcount as success
**File:** `identify_potential_levers.py:78–82`

```python
levers: list[Lever] = Field(
    min_length=5,
    max_length=7,
    description="Propose 5 to 7 levers."
)
```

The Pydantic schema permits 5, 6, or 7 levers per response. When a model returns 7 levers (caused by B1), Pydantic accepts it without error, the response is appended to `responses`, and 7 levers are merged into the final file. The pipeline never detects the overcount; the caller gets a "success" result with 19 or 21 levers instead of 15.

If the intended contract is "exactly 5 per call", the schema bounds must match that contract.

---

### B3 — Levers from all sub-calls merged without per-call count check
**File:** `identify_potential_levers.py:244–247`

```python
levers_raw: list[Lever] = []
for response in responses:
    levers_raw.extend(response.levers)
```

All levers from all 3 responses are appended unconditionally. There is no assertion or check on the per-call lever count before merging. If a call returned 7 levers (due to B1+B2), the overcount propagates silently into `levers_raw` and then into the clean output file. The only downstream signal is that the saved `002-10-potential_levers.json` has more than 15 entries, which no code currently validates.

---

### B4 — No deduplication of lever names across sub-calls before saving
**File:** `identify_potential_levers.py:244–247` (same merge block)

The `generated_lever_names` list at line 195/240 is used only to construct the "do NOT reuse" instruction in the next call's user prompt. That instruction is advisory; models can and do ignore it. When a duplicate name is generated (runs 61 and 65 each had one duplicate name, run 65 had "Silo-Information Control Strategy" at positions 3 and 13), the merge loop extends without any deduplication check. The final clean file contains levers with identical names and different content, which confuses any downstream consumer that keys on name.

---

### B5 — `set_usage_metrics_path` called outside `_file_lock` in multi-worker context
**File:** `runner.py:106, 140`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)   # inside lock
```

The comment at lines 97–98 explicitly notes that `set_usage_metrics_path` is global state, yet it is called without holding `_file_lock`. When `workers > 1`, two threads can call `set_usage_metrics_path` concurrently, and each thread's LLM activity may be written to another plan's metrics file (or to the last-set path for both plans). The `dispatcher.add_event_handler` call is correctly inside the lock, but the usage metrics path is not. The `finally` block at line 140 has the same gap.

---

## Suspect Patterns

### S1 — Partial-response schema failure kills the entire plan with no recovery path
**File:** `identify_potential_levers.py:229–238`

When Pydantic validation raises (run 66, hong_kong_game — model returned only `strategic_rationale` without `levers`/`summary`), the exception is wrapped in `LLMChatError` and re-raised, aborting the entire plan immediately. The pipeline has no mechanism to detect the "partial response" case (present `strategic_rationale`, absent `levers`) and retry with an explicit instruction to complete the levers array. Because this failure mode produced valid partial JSON (just the wrong top-level keys), a targeted retry would likely have succeeded.

### S2 — No minimum output-token guard before running a model
**File:** `identify_potential_levers.py:176–242` (execute method), `runner.py:93–94`

`LLMExecutor` is constructed and immediately run without inspecting model metadata. Llama3.1 (run 61) has `num_output: 256`, which makes it structurally impossible to generate 5 complete levers (each ~100+ tokens). The pipeline proceeds, gets truncated/compressed responses, and saves degraded outputs as "successful". A pre-run check on `llm.metadata.num_output` against a minimum threshold (e.g., 2048) would reject or warn for such models before wasting time.

### S3 — `LLMExecutor` constructed with no retry configuration
**File:** `runner.py:94`

```python
llm_executor = LLMExecutor(llm_models=llm_models)
```

No retry count or retry policy is visible. Single-call failures (run 60 all 5 plans, run 62 one plan) are never retried. If LLMExecutor supports retry configuration, it is not used here. The only fallback mechanism is the ordered `llm_models` list (primary + fallbacks), but that switches models rather than retrying the same model on transient failures.

### S4 — `execute_function` closure defined inside a loop (Python late-binding caveat)
**File:** `identify_potential_levers.py:219–227`

```python
for call_index in range(1, total_calls + 1):
    ...
    messages_snapshot = list(call_messages)

    def execute_function(llm: LLM) -> dict:
        ...chat(messages_snapshot)...

    result = llm_executor.run(execute_function)
```

Python closures bind names, not values. If `llm_executor.run` deferred or threaded execution, `messages_snapshot` would refer to the loop variable's current value at call time, not capture time. In the current synchronous path this is safe because `run` blocks before the next iteration reassigns `messages_snapshot`. However, the pattern is fragile: if `LLMExecutor.run` ever gains async/deferred behavior, all 3 calls would share the last iteration's `messages_snapshot`. Using a default-argument capture (`def execute_function(llm, _snap=messages_snapshot): ...`) would make this unconditionally safe.

---

## Improvement Opportunities

### I1 — Parameterize expected lever count; derive follow-up prompt from it
**File:** `identify_potential_levers.py:192–206`

Replace the hardcoded "5 to 7" in the follow-up call prompt with a variable that matches the candidate prompt's contract. If the contract changes to "exactly 5", only one place needs updating and both the schema (B2) and the user message (B1) stay in sync.

### I2 — Add per-call lever count assertion (truncate or retry) after parsing
**File:** `identify_potential_levers.py:240–242`

After `responses.append(result["chat_response"].raw)`, assert that `len(response.levers) == expected_count`. On violation, either:
- Truncate to the first `expected_count` levers and log a warning, or
- Retry the call with an explicit count correction message.

Either approach prevents overcount levers from silently reaching the merged output.

### I3 — Add cross-call name deduplication before saving the clean file
**File:** `identify_potential_levers.py:249–260`

After the flatten loop, build a `seen_names` set and skip (or rename) any `LeverCleaned` whose `name` is already in the set. Log a warning for each duplicate detected so it is visible in run artifacts.

### I4 — Add retry for partial-response schema validation failures
**File:** `identify_potential_levers.py:229–238`

Catch `LLMChatError` (or the underlying Pydantic `ValidationError`) specifically for the case where the raw response contains `strategic_rationale` but is missing `levers`. On detection, construct a follow-up message asking the model to emit the full `DocumentDetails` structure (the strategic rationale is already done; only the `levers` and `summary` arrays are needed). This would have recovered run 66's hong_kong_game plan.

### I5 — Guard against extreme `num_output` before starting execution
**File:** `identify_potential_levers.py:177` or `runner.py:93`

After constructing `llm_executor`, inspect `metadata.num_output` for each model. If `num_output < MIN_OUTPUT_TOKENS` (e.g., 2048), log an error and either raise or skip. This would have surfaced llama3.1's 256-token ceiling before degraded outputs were saved as "successful".

### I6 — Protect `set_usage_metrics_path` with `_file_lock` in runner
**File:** `runner.py:106, 140`

Move `set_usage_metrics_path(...)` inside the `with _file_lock:` block (both the setup and the teardown in `finally`). This eliminates the race condition when `workers > 1`.

---

## Trace to Insight Findings

| Insight issue | Root-cause code location | Explanation |
|---|---|---|
| **N3 (claude) — Lever count inflation in llama3.1 runs 61** | `identify_potential_levers.py:203` (B1) | Follow-up call says "5 to 7 MORE", so model returns 7; `max_length=7` schema (B2) accepts it. |
| **N4 (claude) — Label-only options in llama3.1 calls 2/3** | `identify_potential_levers.py:203` (B1) + no `num_output` guard (S2) | With only 256 output tokens and a mandate to produce 7 levers, the model abbreviates option text to noun phrases. |
| **N7 (claude) — Duplicate lever names across calls** | `identify_potential_levers.py:244–247` (B4) | No deduplication check before extending `levers_raw`. |
| **N2 (claude) — Schema validation failure on hong_kong_game** | `identify_potential_levers.py:229–238` (S1) | No partial-response recovery; single Pydantic error kills the whole plan. |
| **N1 (codex) — Prompt/code contract conflict on lever count** | `identify_potential_levers.py:78–82` (B2) + `:203` (B1) | Both the Pydantic schema and the follow-up user message allow 5–7 while the candidate system prompt requires exactly 5. |
| **N3 (codex) — Run 64 `consequences` contains review text** | Not a code bug per se; field boundary is defined only in field descriptions with no runtime validation. I3 (codex) aligns: add a post-parse validator that rejects `consequences` containing "Controls" or "Weakness:". |
| **N5 (codex) — Run 66 saves 17–19 lever files** | `identify_potential_levers.py:203` (B1) + `:244–247` (B3) | 7-lever responses from calls 2/3 are merged unconditionally. |
| **C2 (codex) — Set minimum `num_output` floor** | No guard in `identify_potential_levers.py` or `runner.py` (S2) | See I5 above. |
| **C3 (codex + claude) — Add cross-call deduplication** | `identify_potential_levers.py:244–247` (B4) | See I3 above. |
| **C4 (codex) — Add retry on extraction/validation failure** | `runner.py:94` (S3) + `identify_potential_levers.py:229–238` (S1) | See I4 above. |
| **B5 (this review) — Race condition on usage metrics** | `runner.py:106, 140` (B5) | `set_usage_metrics_path` unprotected in multi-worker mode. |

---

## Summary

The two most impactful bugs are both in `identify_potential_levers.py`:

1. **B1** (`line 203`): The follow-up call user message hardcodes "Generate 5 to 7 MORE levers", directly overriding any candidate system prompt that requires exactly 5. This single line explains the `[5, 7, 7]` response counts and all the downstream overcount artifacts in runs 61 and 66.

2. **B2** (`line 78–82`): The `DocumentDetails.levers` Pydantic schema allows 5–7, so 7-lever responses are validated as successes. The schema must match the intended contract to act as a hard enforcement boundary.

The merge loop (B3, B4) has no count assertion and no name deduplication, so any overcount or duplicate that slips through B1/B2 is silently saved.

In `runner.py`, the only confirmed bug is B5: `set_usage_metrics_path` is global state that is updated outside `_file_lock`, making it a race condition when `workers > 1`. All other runner patterns are suspect but not confirmed bugs without seeing `LLMExecutor` internals.

Highest-priority fixes, in order:
1. **B1** — change "5 to 7 MORE" to match the candidate prompt's lever count
2. **B2** — change `max_length=7` to match that same count
3. **B3/B4** — add post-merge count assertion and name deduplication
4. **B5** — bring `set_usage_metrics_path` inside `_file_lock`
5. **S1/I4** — add partial-response retry for schema failures
6. **S2/I5** — add `num_output` floor check
