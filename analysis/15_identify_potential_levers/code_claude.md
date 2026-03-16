# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — `break` in call-2/3 error handler skips call-3 entirely
**File:** `identify_potential_levers.py:278`

When call-2 (or call-3) fails and at least one prior response exists (`len(responses) > 0`),
the code logs a warning and does `break`, exiting the loop immediately. This means a call-2
failure silently prevents call-3 from running, discarding a full third of possible lever
candidates.

```python
# line 272-278
if len(responses) == 0:
    raise llm_error from e
logger.warning(...)
break   # ← should be `continue`
```

`continue` would allow call-3 to attempt generation even when call-2 failed, potentially
recovering 5–7 additional levers from the iteration.

**Severity:** Medium. No data corruption; output is simply fewer levers than possible.

---

### B2 — `set_usage_metrics_path` called outside the thread lock
**File:** `runner.py:106`

`set_usage_metrics_path` stores a global path. When `workers > 1`, multiple threads call
this function concurrently without holding `_file_lock`. Thread A's path can be overwritten
by Thread B before Thread A's LLM execution has started, so LLM usage events for Thread A
are written into Thread B's `usage_metrics.jsonl`.

```python
# line 106 — races with other threads
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")

with _file_lock:            # line 108 — lock covers only add_event_handler
    dispatcher.add_event_handler(track_activity)

t0 = time.monotonic()
try:
    ...
    result = IdentifyPotentialLevers.execute(...)   # line 114 — lock already released
```

The comment on lines 97–99 acknowledges that `set_usage_metrics_path` is global state, but
the code does not actually protect it with the lock.

**Severity:** Medium under parallel workers (the default for most non-ollama models is 4
workers). Usage metrics are silently written to the wrong file.

---

### B3 — Dispatcher event handlers are not isolated during LLM execution (cross-thread event mixing)
**File:** `runner.py:104–143`

`dispatcher` is a process-global llama-index object. Each worker thread adds its own
`track_activity` handler (line 109), but the lock is released before `IdentifyPotentialLevers.execute()` runs. During execution, all currently-registered handlers receive all events. With 4 workers active simultaneously, every event fired by any plan's LLM call is dispatched to all 4 `track_activity` handlers, causing each plan's `track_activity.jsonl` to contain events from every other concurrent plan.

This is why the `track_activity.jsonl` thread-safety issue was noted in analysis/14 (NI3). The
per-plan `_file_lock` guard protects appending to shared files but does nothing to isolate
the dispatcher's handler set during execution.

**Severity:** Medium. Cross-plan event mixing corrupts `track_activity.jsonl`. This is then
immediately deleted (line 143) so the impact is mostly invisible, but it means the
`usage_metrics.jsonl` data (which `set_usage_metrics_path` controls) is also potentially
mixed.

---

### B4 — All-or-nothing Pydantic validation: one bad lever rejects the entire LLM response
**File:** `identify_potential_levers.py:109–112` (the `levers` list field in `DocumentDetails`)

When an LLM returns a list of levers where even one fails validation (wrong option count,
`review_lever` format violation, etc.), Pydantic rejects the entire `DocumentDetails` object.
All valid levers from that call are discarded and the exception propagates to the `except`
block in `execute()`. For a call that produces 6 well-formed levers and 1 bad one, 6 levers
are thrown away.

This is the "all-or-nothing cascade" described in N1 (insight_claude): gpt-5-nano parasomnia
produced 6 levers all with `review_lever = 'Not applicable here'`, but the root mechanism
would equally discard a response with 6 valid levers and 1 invalid one.

**Severity:** Medium. Exact frequency is unknown but confirmed for gpt-5-nano parasomnia
(run 1/12). Any model that occasionally produces one non-compliant lever in a batch loses
the entire batch.

---

## Suspect Patterns

### S1 — `track_activity_path.unlink()` deletes the file on every run
**File:** `runner.py:143`

The `finally` block deletes `track_activity.jsonl` after every plan, regardless of success
or failure. This is likely intentional (the file is a transient artifact created by
`TrackActivity`), but if the file ever contains diagnostically useful information, it is
silently lost. The call happens after `dispatcher.event_handlers.remove(track_activity)` is
complete but before any other code can read the file.

---

### S2 — Resume summary inflates `total` count for replayed plans
**File:** `runner.py:462–468`

When a run is resumed after partial failure, `outputs.jsonl` accumulates both the original
"error" record and the later "ok" record for the same plan. The final summary counts all
records:

```python
total = len(plans)   # includes duplicate error + ok entries for re-run plans
```

For a 5-plan run where 1 plan failed and then succeeded on resume, the summary prints
"5/6 plans succeeded" instead of "5/5".

---

### S3 — `check_review_format` only checks for `'Controls '`, not for `' vs. '`
**File:** `identify_potential_levers.py:95–96`

The validator accepts any string containing `'Controls '` — for example, `"Controls the
tension between A and B"` passes even though the required format is `"Controls [A] vs. [B]."`.
The `vs.` separator is the most diagnostic marker of the two-part template, but it is not
checked.

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
# 'vs.' is never checked
```

This does not cause false negatives for the failures observed so far (all failures lack
`Controls ` entirely), but it could allow subtly malformed reviews to pass.

---

### S4 — Duplicate lever name deduplication is case-sensitive and exact
**File:** `identify_potential_levers.py:290–294`

```python
seen_names: set[str] = set()
...
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

`"Resource Allocation"` and `"resource allocation"` are treated as distinct levers.
Near-duplicates with punctuation differences (`"AI Governance"` vs. `"AI-Governance"`) also
pass through. The downstream `DeduplicateLeversTask` handles semantic deduplication, so this
is not critical, but the name-exact guard here is weaker than implied.

---

## Improvement Opportunities

### I1 — Replace `break` with `continue` in the call failure handler
**File:** `identify_potential_levers.py:278`

Change `break` to `continue`. When call-2 fails but call-1 succeeded, call-3 should still
run. Zero cascading risk. This is the highest-leverage single-line fix available.

---

### I2 — Add partial-recovery telemetry event
**File:** `identify_potential_levers.py:274–278`

When the `break` path fires (and after the fix above, the `continue` path), emit a log or
structured event recording which call number failed and how many levers were already
recovered. This would give analysis scripts an explicit signal rather than requiring them to
infer partial recovery from lever counts.

---

### I3 — Post-parse `consequences` contamination repair validator
**File:** `identify_potential_levers.py` (add a `@field_validator('consequences', mode='after')` to `Lever`)

qwen3-30b consistently embeds `review_lever` text (`"Controls X vs. Y. Weakness: ..."`) at
the end of the `consequences` field (N6, insight_claude; ~33% of silo levers in run 1/13).
A repair validator that strips any trailing `"Controls … Weakness: …"` suffix from
`consequences` would clean this up without rejecting the lever or requiring another LLM call.

The existing field description already contains the prohibition:
> "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this
> field"

A validator enforcing this with a repair (not a reject) would make the prohibition
operationally effective.

---

### I4 — Move `set_usage_metrics_path` inside the thread lock
**File:** `runner.py:106` → move into the `with _file_lock:` block at lines 108–110

This serializes the global-path assignment relative to `add_event_handler`, so both
operations are atomic from other threads' perspective. The LLM execution itself still runs
outside the lock (correct — holding the lock during LLM calls would serialize all plans).

---

### I5 — Fix resume summary to deduplicate by plan name
**File:** `runner.py:462–468`

When summarizing, take the last record per plan name rather than counting all rows:

```python
by_name = {}
for p in plans:
    by_name[p["name"]] = p   # last record wins
plans = list(by_name.values())
```

This gives accurate "ok/total" counts after a resume.

---

### I6 — Strengthen `check_review_format` to verify the `vs.` separator
**File:** `identify_potential_levers.py:95–96`

Add `if ' vs. ' not in v:` (or a regex for `Controls .+ vs\. .+`) to catch reviews that
contain `Controls` but omit the `vs.` separator. This closes the gap between the validator's
intent and its actual enforcement.

---

### I7 — Per-call conversation context: include prior assistant turns in calls 2 and 3
**File:** `identify_potential_levers.py:230–245`

Calls 2 and 3 inject the previously-generated **names** into the user prompt but do not
include the prior **assistant response** in the message history. The model therefore cannot
see the actual content of previous levers, only their names. Adding the assistant turn from
call-1 to the messages for call-2 (and calls 1+2 to call-3) would give the model richer
context for producing complementary rather than merely name-distinct levers.

This would also reduce the `consequences` contamination and `options` prefix violations
observed in qwen3-30b, since the model could see the quality bar set by earlier calls.

Risk: longer context per call; models with small context windows (like local ollama models)
might time out more frequently. Could be gated on a flag.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Root Cause |
|---|---|---|
| N1 (gpt-5-nano parasomnia: all 6 levers rejected, plan fails) | `identify_potential_levers.py:109–112` | B4 — entire `DocumentDetails` rejected when any `Lever` fails Pydantic validation |
| N3 (llama3.1 ReadTimeout on parasomnia) | `runner.py` (no timeout config surface) | No configurable per-plan timeout exposed by the runner; timeout is buried in model config |
| N6 (qwen3 `consequences` contamination ~33% of levers) | `identify_potential_levers.py:34–46` | No post-parse repair validator; field description prohibition is not enforced in code (I3) |
| N8 (lever count exceeds prompt's "5–7" per call) | `identify_potential_levers.py:106–112` | Intentional design — `max_length` deliberately omitted; note on line 106 documents this |
| insight_claude C1 (call-2 failure blocks call-3) | `identify_potential_levers.py:278` | B1 — `break` instead of `continue` |
| insight_claude C2 (no partial-recovery event) | `identify_potential_levers.py:274–278` | No structured event emitted when a non-first call fails (I2) |
| insight_claude C4 (`activity_overview.json` thread-safety) | `runner.py:104–143` | B3 — dispatcher handlers not isolated during execution; B2 — `set_usage_metrics_path` unprotected |
| insight_codex C1 (post-generation `review_lever` canonicalizer) | `identify_potential_levers.py:86–99` | S3 — validator only checks `'Controls '`; near-miss reviews pass unrepaired |
| insight_codex C3 (placeholder/label detector) | `identify_potential_levers.py` | No post-parse label or bracket-placeholder check on `options` or `review_lever` fields |
| S2 (resume summary inflates total) | `runner.py:462–468` | Append-only `outputs.jsonl` not deduplicated before counting |

---

## Summary

**Two confirmed bugs with meaningful quality impact:**

- **B1** (`break` vs. `continue`): A one-character fix that allows call-3 to run after
  call-2 fails. Currently, any call-2 exception silently caps output at the call-1 results
  (5–7 levers instead of 10–15+). This is the highest-leverage code change available.

- **B4** (all-or-nothing Pydantic validation): Any single non-compliant lever field
  (`review_lever = 'Not applicable here'`, wrong option count, etc.) causes the entire LLM
  response to be discarded. This directly explains run 1/12 parasomnia's complete failure
  after 357 seconds of compute. A repair approach (filter-bad-levers rather than reject-all)
  would recover partial responses.

**Two concurrency bugs affecting parallel workers (B2, B3):**

Both involve global state (`set_usage_metrics_path`, `dispatcher` event handlers) that is not
properly isolated between threads when `workers > 1`. Under 4-worker configurations (the
default for most cloud models), usage metrics may be written to the wrong files and
track_activity events from one plan may appear in another plan's handler. The immediate
visible effect is limited (the `track_activity.jsonl` files are deleted at the end of each
run), but the underlying race is real.

**Highest-priority improvements:**

1. **I1** — `break` → `continue` (fixes B1, zero risk)
2. **I3** — Post-parse `consequences` repair validator (fixes qwen3 contamination, I3)
3. **I4** — Lock `set_usage_metrics_path` (fixes B2)
4. **I2** — Partial-recovery telemetry (observability, low effort)
