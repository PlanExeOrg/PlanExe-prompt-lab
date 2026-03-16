# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

Supporting context read:
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py`
- `worker_plan/worker_plan_internal/llm_util/llm_errors.py`
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`

---

## Bugs Found

### B1 — `set_usage_metrics_path` race condition in parallel runs
**File:** `prompt_optimizer/runner.py:106, 140`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # line 106 — outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)                  # line 109 — inside lock

# … LLM execution runs here (can take minutes) …

finally:
    set_usage_metrics_path(None)                                   # line 140 — outside lock
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)          # line 142 — inside lock
```

`set_usage_metrics_path` writes to a **global** (module-level) variable. The
comment at lines 97–98 says "we hold a lock while configuring … to avoid
cross-thread interference," but the lock is **not** held around this call. When
`workers > 1`, concurrent threads can interleave:

1. Thread A sets path → `planA/usage_metrics.jsonl`
2. Thread B sets path → `planB/usage_metrics.jsonl`
3. Thread A's LLM call fires → metrics are written to `planB`'s file
4. Thread B's `finally` sets path → `None`, clearing it while Thread A's call is
   still in flight

Result: usage metrics are silently misattributed or discarded across plans.
The `dispatcher.add_event_handler` and `.remove` are correctly protected by
`_file_lock`, making the comment doubly misleading — the lock covers only the
list mutations, not the global path.

---

### B2 — `check_review_format` validates substring presence, not prefix position
**File:** `identify_potential_levers.py:95`

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
```

This is a substring check, not a prefix check. Two correctness issues:

1. **Wrong position passes silently.** A value such as
   `"Weakness: The options fail to consider Controls Speed vs. Safety."` contains
   `'Controls '` so it passes — even though `Controls` is inside the *Weakness*
   clause, not the first sentence. The intended invariant (sentence 1 begins with
   `Controls`) is not enforced.

2. **`vs.` token is not validated at all.** The prompt mandates the exact token
   `vs.` but the validator never checks for it. A model writing
   `"Controls X versus Y. Weakness: …"` passes validation and produces
   inconsistently formatted output for downstream consumers, while still consuming
   the full inference budget.

The fix would be to use `v.startswith('Controls ')` and additionally check that
`' vs. '` or `'. Weakness:'` appears in the correct sequence.

---

### B3 — TOCTOU race in history run-directory creation
**File:** `prompt_optimizer/runner.py:257–285`

```python
def _next_history_counter(history_dir: Path) -> int:      # reads filesystem
    …

def _history_run_dir(prompt_lab_dir: Path, step_name: str) -> Path:
    counter = _next_history_counter(history_dir)           # read
    run_dir = history_dir / bucket / entry
    run_dir.mkdir(parents=True, exist_ok=True)             # create (non-atomic)
    return run_dir
```

Two concurrent invocations of `main()` (e.g., two terminal tabs) both call
`_next_history_counter`, both observe the same maximum, compute the same counter,
and both create `history/1/17_identify_potential_levers/` with `exist_ok=True`.
Both processes then write `meta.json`, `events.jsonl`, and plan outputs into the
same directory, silently overwriting each other. The resulting history entry is
corrupt and the counter never advances.

---

## Suspect Patterns

### S1 — `finally` block removes handler that may never have been added
**File:** `prompt_optimizer/runner.py:108–143`

```python
with _file_lock:
    dispatcher.add_event_handler(track_activity)   # line 109

t0 = time.monotonic()
try:
    …
finally:
    set_usage_metrics_path(None)
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)  # line 142
```

If `dispatcher.add_event_handler` at line 109 raises (e.g., the dispatcher
rejects duplicate handlers), execution jumps past the `try` block's setup and
into the `finally`. The `finally` then calls `.remove()` on a handler that was
never added, raising a `ValueError` that shadows the original exception and makes
the root cause invisible in logs.

Additionally, `.event_handlers.remove(track_activity)` accesses the LlamaIndex
dispatcher's internal list attribute directly. If LlamaIndex changes its internal
storage structure, this call silently breaks. A safer pattern would be a matching
`remove_event_handler(track_activity)` API call (if one exists) or a guard:
`if track_activity in dispatcher.event_handlers`.

---

### S2 — `execute_function` closure over loop variable `messages_snapshot`
**File:** `identify_potential_levers.py:247–257`

```python
for call_index in range(1, total_calls + 1):
    …
    messages_snapshot = list(call_messages)          # re-bound each iteration

    def execute_function(llm: LLM) -> dict:
        chat_response = sllm.chat(messages_snapshot) # captured by reference
        …

    result = llm_executor.run(execute_function)
```

Python closures capture variable *names*, not values. `execute_function`
captures the name `messages_snapshot` from the enclosing scope. The pattern is
safe as written because `execute_function` is consumed in the same iteration
(before `messages_snapshot` is rebound). However:

- If `LLMExecutor.run()` ever defers or caches `execute_function` across
  iterations (e.g., future background retry logic), it would silently use the
  *last* iteration's `messages_snapshot`.
- If validation-retry logic (currently `max_validation_retries=0`) is enabled in
  a future call site, validation feedback is never injected into
  `messages_snapshot` before the retry, so the retry sends the identical prompt
  with no correction — wasting inference budget.

The low-risk fix is to use a default-argument capture:
`def execute_function(llm: LLM, _snap=messages_snapshot) -> dict:`.

---

## Improvement Opportunities

### I1 — No JSON-truncation detection; EOF errors treated like any other failure
**File:** `identify_potential_levers.py:259–278`; `llm_executor.py:41–51`

Runs 18 and 20 both failed on the parasomnia plan with
`EOF while parsing a list at line 25 column 5` — the LLM hit its output-token
limit mid-response. This error surfaces as a `json.JSONDecodeError`, which is
**not** in `_TRANSIENT_PATTERNS`:

```python
_TRANSIENT_PATTERNS: list[str] = [
    "rate limit", "timeout", "connection", …   # EOF / json not listed
]
```

Because it is not transient, `LLMExecutor` does not retry it. The exception
propagates to `identify_potential_levers.py:264`, gets wrapped in `LLMChatError`,
and (for call 1) immediately fails the plan.

A targeted fix: add `"eof while parsing"` and `"unexpected end"` to
`_TRANSIENT_PATTERNS`, or introduce a dedicated `LLMResponseTruncatedError`
subclass of `LLMChatError` with a flag that the outer loop can detect and use to
increase the `max_tokens` budget before retrying. This would recover the 2
parasomnia failures in runs 18 and 20.

---

### I2 — All-or-nothing Pydantic validation discards entire plans on one bad lever
**File:** `identify_potential_levers.py:86–99, 259–281`

When `DocumentDetails` is validated by LlamaIndex's structured LLM interface, a
`ValidationError` on any single `Lever` rejects the entire response. Run 23
hong_kong produced 7 levers that all failed `check_review_format` (all missing
`Controls ` prefix), discarding 52 s of inference with zero usable output.

Because validation happens inside `sllm.chat()` (llama_index internals), the raw
LLM response containing 7 otherwise-structurally-valid levers is never exposed to
the application code. Options for recovery:

- **Auto-correction before rejection (lightest touch):** In
  `check_review_format`, attempt to prepend `"Controls "` when the field contains
  `" vs. "` but not `"Controls "`. Re-validate after correction. Only raise
  `ValueError` if the corrected form still fails.

- **Per-lever partial recovery:** Attempt to parse the raw LLM JSON manually and
  construct `DocumentDetails` lever-by-lever, skipping only invalid levers instead
  of the entire response. This requires bypassing the structured LLM wrapper for
  the raw string.

Either approach would convert run 23 hong_kong from 0 levers to 7 levers.

---

### I3 — `vs.` token not enforced by the validator despite being in the prompt
**File:** `identify_potential_levers.py:95–98`

The `check_review_format` validator checks for `'Controls '` and `'Weakness:'`
but not for `'vs.'`. The prompt specifies the exact format:
`Controls [Tension A] vs. [Tension B].` A model using `versus`, `and`, or
`/` would pass validation and produce output that is structurally inconsistent.
The validator should either check for `' vs. '` or normalise variants
(`versus` → `vs.`) before storing.

---

### I4 — Exact-name deduplication misses semantic near-duplicates
**File:** `identify_potential_levers.py:290–294`

```python
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

Only exact-string matches are deduplicated here. Run 21 produced "Resource
Management for Longevity" and "Resource Utilization for Resilience" — different
names, nearly identical `consequences` and `options` — both passing through to
the 17-lever final output. The downstream `DeduplicateLeversTask`
(`deduplicate_levers.py`) uses an LLM-based per-lever classification, which is
better, but is also sequence-order-dependent and may miss cases where both levers
arrive late in a long list (context dilution).

A lightweight improvement: before appending a lever, compute a short fingerprint
(e.g., first 60 chars of `consequences`) and skip levers whose fingerprint was
already seen. This is cheaper than embeddings and catches the most common
verbatim-consequence duplicates without changing the downstream dedup step.

---

### I5 — No token-budget control; verbose plans hit provider limits silently
**File:** `identify_potential_levers.py:249–257`

The `consequences` field description says "Target length: 3–5 sentences (~60–120
words)" but this is advisory only — the Pydantic schema has no `max_length`. The
parasomnia plan consistently generated longer outputs than other plans across
multiple models (evidence: runs 18, 20 EOF truncation; run 23 timeout at 373 s).

The `LLMExecutor` and `IdentifyPotentialLevers.execute()` have no mechanism to
pass a `max_tokens` parameter to the underlying LLM call (the call is via
`sllm.chat(messages_snapshot)` with no keyword arguments). Adding a
`max_tokens` parameter to `IdentifyPotentialLevers.execute()` — and threading it
through to `llm.as_structured_llm(DocumentDetails)` or the chat call — would give
operators a knob to reduce truncation risk for known-verbose plans.

---

### I6 — `_file_lock` comment contradicts its actual scope
**File:** `prompt_optimizer/runner.py:97–109`

```python
# Set up per-plan usage tracking.
# set_usage_metrics_path and the dispatcher are global state, so we hold
# a lock while configuring and running to avoid cross-thread interference.
track_activity = TrackActivity(…)

set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # NOT locked

with _file_lock:                                                    # only this is locked
    dispatcher.add_event_handler(track_activity)
```

The comment creates a false sense of security: it implies the lock covers
`set_usage_metrics_path`, but the lock is only acquired for the dispatcher call.
This will confuse future readers and maintainers into believing the usage-metrics
path is already protected. Either the comment should be corrected, or (better)
`set_usage_metrics_path` should be moved inside the `_file_lock` block — or the
design should use thread-local state for per-plan metrics paths.

---

## Trace to Insight Findings

| Insight finding | Code location | Root cause |
|---|---|---|
| N1 — Parasomnia fails with `EOF while parsing` (runs 18, 20) | `llm_executor.py:41–51`, `identify_potential_levers.py:259–278` | EOF/json errors not in `_TRANSIENT_PATTERNS`; no retry or token-budget control (I1, I5) |
| N1 — Parasomnia APITimeoutError 373 s (run 23) | `identify_potential_levers.py:249–257` | No `max_tokens` parameter exposed; verbose domain exhausts provider timeout (I5) |
| N2 — Run 23 hong_kong: 7 validation errors, 0 levers output | `identify_potential_levers.py:86–99` | All-or-nothing validation; no per-lever recovery or auto-correction (I2, B2) |
| N2 — `review_lever` missing `Controls` prefix causes hard reject | `identify_potential_levers.py:95` | Substring check does not enforce prefix position or `vs.` token (B2, I3) |
| N4 — Semantic near-duplicates ("Resource Management for Longevity" vs "Resource Utilization for Resilience") pass through dedup | `identify_potential_levers.py:290–294` | Only exact-name dedup between calls; consequences fingerprint not checked (I4) |
| N5 — Formulaic `Weakness:` clauses pass validation | `identify_potential_levers.py:95–99` | Validator only checks token presence, not content quality; no length or novelty check (I3) |
| C1 (insight hypothesis) — retry with higher max_tokens | `identify_potential_levers.py:249`, `llm_executor.py:41` | No EOF error subtype; no max_tokens parameter path (I1, I5) |
| C2 (insight hypothesis) — auto-correct `Controls` prefix | `identify_potential_levers.py:86–99` | Hard Pydantic reject; no correction step before `ValueError` (I2) |
| C3 (insight hypothesis) — embedding dedup | `identify_potential_levers.py:290–294` | Exact-name-only dedup; no fingerprint or similarity fallback (I4) |
| Usage metrics may be misattributed in parallel runs | `runner.py:106, 140` | `set_usage_metrics_path` not protected by `_file_lock` (B1) |

---

## Summary

The code is well-structured and the existing partial-recovery logic (line 272:
keep results if any prior calls succeeded) is a good defensive pattern. No
catastrophic logic inversions or data-loss bugs in the core lever-generation
path.

**Three confirmed bugs:**

- **B1** (runner.py:106, 140): `set_usage_metrics_path` is not protected by
  `_file_lock`, causing usage-metrics misattribution across parallel plans.
- **B2** (identify_potential_levers.py:95): `check_review_format` uses substring
  presence (`not in`) instead of prefix position (`startswith`), and does not
  validate the `vs.` token at all. This allows structurally wrong reviews to pass
  and structurally correct reviews to fail inconsistently.
- **B3** (runner.py:257–285): TOCTOU race in history run-directory creation; two
  concurrent runner invocations can collide on the same counter and overwrite each
  other's results.

**Highest-priority improvements (directly explaining observed failures):**

- **I1**: Add EOF/truncation detection to `_TRANSIENT_PATTERNS` or introduce a
  `LLMResponseTruncatedError` to enable targeted retry with higher `max_tokens`.
  This would recover the 2 parasomnia failures in runs 18 and 20.
- **I2**: Add auto-correction in `check_review_format` before raising
  `ValueError` (prepend `"Controls "` when `" vs. "` is present). This would
  recover run 23 hong_kong's 7 discarded levers.
- **I3**: Extend `check_review_format` to verify `' vs. '` is present in the
  first sentence, making the validator match what the prompt requires.
