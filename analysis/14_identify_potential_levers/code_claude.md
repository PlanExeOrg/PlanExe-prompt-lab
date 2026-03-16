# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`
- (supporting) `worker_plan/worker_plan_internal/llm_util/track_activity.py`
- (supporting) `worker_plan/worker_plan_internal/llm_util/usage_metrics.py`
- (supporting) `worker_plan/worker_plan_internal/llm_util/llm_executor.py`

---

## Bugs Found

### B1 — `activity_overview.json` inflated under parallel workers
**File**: `track_activity.py:207–252` (`_update_activity_overview`)

When `workers > 1` in runner.py, all plan threads share the same global llama_index dispatcher.
Each call to `dispatcher.add_event_handler(track_activity)` registers a new `TrackActivity` for a
specific plan. Since the add/remove lock is only held for those two operations (not during the LLM
call), all handlers are simultaneously active. Every LLM completion event therefore fires
**every** registered handler.

`_record_file_usage_metric` (track_activity.py:302–328) has a thread-local guard:
```python
current_path = get_usage_metrics_path()
if current_path is not None and current_path.parent != self.jsonl_file_path.parent:
    return
```
This correctly suppresses cross-plan writes to `usage_metrics.jsonl`.

`_update_activity_overview` (track_activity.py:207–252) has **no such guard**. With 4 workers, each
plan's `activity_overview.json` will accumulate token/cost data from all 4 plans' LLM calls. The
per-plan file becomes meaningless for cost attribution.

---

### B2 — Partial recovery is invisible to the caller
**File**: `identify_potential_levers.py:272–278`

PR #292 breaks out of the loop with partial results when calls 2 or 3 fail. The `break` at line 278
correctly exits the loop, but the returned `IdentifyPotentialLevers` object has no flag or count
indicating partial recovery. `runner.py` calls `IdentifyPotentialLevers.execute()` and receives a
result that looks identical whether all 3 calls succeeded or only 1 did.

The `run_single_plan` function (runner.py:77–143) writes the raw JSON and emits a
`run_single_plan_complete` event with no partial-recovery signal. The only audit mechanism is
counting `"strategic_rationale"` entries in `002-9-potential_levers_raw.json` by hand.

A caller that checks `len(result.responses) < 3` would detect partial recovery without any new
fields, but no code currently does this.

---

## Suspect Patterns

### S1 — Misleading thread-safety comment in runner.py
**File**: `runner.py:97–109`

```python
# Set up per-plan usage tracking.
# set_usage_metrics_path and the dispatcher are global state, so we hold
# a lock while configuring and running to avoid cross-thread interference.
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # ← outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)
```

The comment says "we hold a lock while configuring", but `set_usage_metrics_path` is called
**before** the lock and is already thread-local (`usage_metrics.py:28` uses `threading.local()`).
The comment suggests a correctness property that doesn't match the implementation. A future
maintainer reading this could either (a) conclude `set_usage_metrics_path` is safe because it's
inside the lock (it's not), or (b) assume it needs to be inside the lock for correctness (it
doesn't, because it's already thread-local). The comment should be rewritten.

---

### S2 — `check_review_format` does not verify clause ordering
**File**: `identify_potential_levers.py:86–99`

```python
if 'Controls ' not in v:
    raise ValueError(...)
if 'Weakness:' not in v:
    raise ValueError(...)
```

A string like `"Weakness: blah Controls X vs. Y."` passes validation despite having clauses in the
wrong order. The prompt requires `"Controls ... vs. ... Weakness: ..."` in that sequence, but the
validator enforces keyword presence only. The prompts' wording and downstream display logic both
assume "Controls" appears before "Weakness" — an out-of-order response could cause visual confusion
in the UI without failing validation.

---

### S3 — `review_lever` description uses separate bullets, not a combined example
**File**: `identify_potential_levers.py:51–58` and system prompt section 4

The field description says:
```
Sentence 1: 'Controls [Tension A] vs. [Tension B].'
Sentence 2: 'Weakness: The options fail to consider [specific factor].'
```
And the system prompt (section 4) repeats this as two separate bullet points. Weaker models
(confirmed: llama3.1 in runs 1/02) interpret these as two alternative formats, producing either
a Controls-only or a Weakness-only field. The prompt does not provide a single combined example
showing both clauses in one field. This structural ambiguity is the root cause of N1 in
insight_claude.

---

### S4 — `generated_lever_names` uses exact-match deduplication
**File**: `identify_potential_levers.py:290–306`

```python
seen_names: set[str] = set()
...
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

Two names that are identical except for capitalization or punctuation (e.g. "Tech Integration" vs.
"tech integration") will not be deduplicated here. Since downstream `DeduplicateLeversTask` handles
semantic deduplication, this is low-risk in practice, but an in-call exact-match could miss
near-identical names from the "avoid these names" prompt injection.

---

## Improvement Opportunities

### I1 — Emit structured partial-recovery signal from runner.py
**File**: `runner.py:300–312` (`_run_plan_task`)

After `run_single_plan` returns a `PlanResult` with `status="ok"`, check whether the raw output
file has fewer than `total_calls` (3) `strategic_rationale` entries. Simpler: expose a
`responses_count` field on `PlanResult` and populate it from `len(result.responses)` before the
raw file is written. Then emit:

```python
if result_responses_count < total_calls:
    _emit_event(events_path, "run_single_plan_partial_recovery",
                plan_name=plan_name,
                calls_succeeded=result_responses_count,
                calls_total=3,
                levers_recovered=len(result.levers))
```

This resolves insight_claude N5 without modifying the `IdentifyPotentialLevers` internal loop.

---

### I2 — Add missing cross-plan guard to `_update_activity_overview`
**File**: `track_activity.py:207–211`

Add the same thread-local guard that `_record_file_usage_metric` already has:

```python
def _update_activity_overview(self, event_data: dict) -> None:
    from worker_plan_internal.llm_util.usage_metrics import get_usage_metrics_path
    current_path = get_usage_metrics_path()
    if current_path is not None and current_path.parent != self.jsonl_file_path.parent:
        return
    ...
```

This is a one-line fix that prevents the B1 inflation under parallel workers.

---

### I3 — `check_review_format` should verify clause ordering
**File**: `identify_potential_levers.py:86–99`

Replace the two independent `in` checks with an order-aware check:

```python
ctrl_pos = v.find('Controls ')
weak_pos = v.find('Weakness:')
if ctrl_pos == -1:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if weak_pos == -1:
    raise ValueError("review_lever must contain 'Weakness: ...'")
if ctrl_pos > weak_pos:
    raise ValueError("review_lever: 'Controls ...' must appear before 'Weakness:'")
```

---

### I4 — Prompt: replace two-bullet `review_lever` instruction with a combined example
**File**: `identify_potential_levers.py:154–196` (system prompt), field description lines 51–58

Replace the two-bullet description in both the field `description` kwarg and the system prompt's
section 4 with a single-line example that shows the combined form:

```
review_lever example (copy this format exactly):
"Controls centralization vs. local autonomy. Weakness: The options fail to account for transition costs."
Both clauses MUST appear in a single field, in this order, with no other text between them.
```

Evidence: insight_claude H1 and insight_codex H1 both identify the two-bullet format as the root
cause of llama3.1's alternating Controls-only / Weakness-only failures.

---

### I5 — `DocumentDetails.levers` min_length error produces opaque messages for callers
**File**: `identify_potential_levers.py:109–112`

When a model returns fewer than 5 levers, Pydantic raises a ValidationError mentioning
`min_length`. This exception travels up through `LLMExecutor`, gets wrapped in `LLMChatError`,
and is logged. The log message is useful, but the error classification in `usage_metrics.py`
(line 38) maps `"validation error"` to `"invalid_json"` — which misrepresents the failure. A
dedicated category like `"schema_violation"` would give cleaner metrics.

---

### I6 — `_record_file_usage_metric` guard has an implicit `None` pass-through
**File**: `track_activity.py:312–313`

```python
if current_path is not None and current_path.parent != self.jsonl_file_path.parent:
    return
```

When `current_path is None` (after `set_usage_metrics_path(None)` in the runner's `finally`
block), the guard evaluates to False and does **not** early-return. However, the downstream
`record_usage_metric` call will silently no-op because `path` is None there. This is safe in
practice but the guard's intent is obscured. A more explicit guard:

```python
if current_path is None or current_path.parent != self.jsonl_file_path.parent:
    return
```
...would express the intent clearly: only write when this handler's directory matches the
current thread's plan.

---

## Trace to Insight Findings

| Insight finding | Root cause code location | Explanation |
|----------------|--------------------------|-------------|
| N1 — llama3.1 review_lever alternating failures | S3 / I4 — `identify_potential_levers.py:51–58` + system prompt section 4 | Two-bullet prompt instruction is interpreted by weaker models as two alternative formats. |
| N2 — llama3.1 gta_game only 7 levers | PR #292 (partial recovery working as designed); B2 — no partial signal | The break at line 278 exits after call 1; the absence of a partial flag means it looks like a full success to the runner. |
| N3 — gpt-oss-20b rotates JSON failure across plans | Not a code bug; LLM context-length sensitivity. The validation pipeline correctly catches and reports it. | |
| N4 — qwen3 consequence contamination | Not a code bug; model copies `review_lever` text. A post-parse repair validator (insight C3) would fix it in code. | |
| N5 — No partial_result metadata flag in events | B2 — partial recovery not exposed from `IdentifyPotentialLevers.execute()` → runner.py has no signal to emit | Fix: I1 (check `len(result.responses)` in runner and emit event). |
| B1 (insight) — activity_overview.json inflated under parallel workers | B1 (this review) — `track_activity.py:207` missing cross-plan guard | `_update_activity_overview` has no thread-local path filter unlike `_record_file_usage_metric`. |
| Codex bracket placeholder leakage (`[Production speed]`) | Not a code bug; model copies field description placeholder text. No code guard exists. | A post-parse validator stripping bracket patterns from option text would fix it. |
| Codex I2 — lever count discipline | S4 / I4; downstream DeduplicateLeversTask handles over-generation; no hard cap needed | |

---

## PR Review

**PR #292 — "Recover partial results when a lever generation call fails"**

### Does the implementation match the intent?

**Yes.** The change at `identify_potential_levers.py:259–278` correctly implements partial recovery:

```python
except Exception as e:
    llm_error = LLMChatError(cause=e)
    ...
    if len(responses) == 0:        # call 1 failed — nothing to recover
        raise llm_error from e
    logger.warning(...)            # call 2 or 3 failed — keep prior results
    break
```

The conditional on `len(responses) == 0` is the right gate: it preserves the pre-PR behavior
(always raise) when there's nothing to recover, and exits the loop with partial data otherwise.
The evidence from insight_claude P1 and insight_codex confirms the behaviour: `gta_game` produces
7 levers (from 1 successful call) instead of 0.

### Bugs or gaps in the PR itself

**Gap 1 — No structured partial-recovery signal** (B2 above):
The `break` exits silently. The caller in runner.py cannot distinguish a 3-call full result from a
1-call partial result without inspecting `len(result.responses)`. This means:
- `events.jsonl` never records a partial-recovery event (insight N5)
- `outputs.jsonl` records `"status": "ok"` for both full and partial results
- Downstream quality signals are undifferentiated

**Gap 2 — `PipelineStopRequested` re-raise is correct but asymmetric**:
`PipelineStopRequested` is re-raised unconditionally (line 261–263) before the partial recovery
check. This is correct — a pipeline stop should not be silenced regardless of whether prior calls
succeeded. The asymmetry is intentional and correct.

**Gap 3 — The warning log is only emitted once per partial recovery**, regardless of how many
calls failed. If calls 2 AND 3 would have failed (but `break` exits after call 2 fails, so call 3
never runs), only one warning is logged. This is fine — it accurately reflects what happened.

**No regressions introduced**: The PR's change is localized to the `except Exception` block. The
success path, the `PipelineStopRequested` path, the metadata collection, the lever deduplication,
and the final result assembly are all unchanged.

### Verdict

The PR is correct and the targeted fix works. The one actionable gap is B2 (no partial signal),
which should be addressed in a follow-up as I1.

---

## Summary

The code is well-structured and the PR #292 change is correct. Three actionable items stand out:

**Highest priority (affects data quality)**:
- **B1**: `_update_activity_overview` in track_activity.py has no cross-plan filter, inflating
  per-plan `activity_overview.json` files when `workers > 1`. Fix: one-line guard (I2).

**Medium priority (observability)**:
- **B2**: Partial recovery produces no structured signal. runner.py cannot emit a telemetry event
  for partial recoveries without inspecting the raw output. Fix: check `len(result.responses)`
  in `run_single_plan` and emit an event (I1).

**Medium priority (model compliance, prompt)**:
- **S3/I4**: The two-bullet `review_lever` instruction in the field description and system prompt
  causes llama3.1 to treat the two clauses as alternatives. This is the root cause of all
  remaining `review_lever` format failures. Fix: replace with a single combined example string (I4).
