# Code Review (claude)

Source files reviewed:
- `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `PlanExe/self_improve/runner.py`

---

## Bugs Found

### B1 — Race condition: `set_usage_metrics_path` unprotected in parallel execution

**File**: `runner.py:107, 150`

```python
# Line 107 — called OUTSIDE _file_lock, before the try block
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")

with _file_lock:
    dispatcher.add_event_handler(track_activity)   # locked

t0 = time.monotonic()
try:
    result = IdentifyPotentialLevers.execute(...)   # LLM calls happen here
    ...
finally:
    set_usage_metrics_path(None)                    # Line 150 — also OUTSIDE lock
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)
```

`set_usage_metrics_path` sets module-level global state. The comment at line 98–100 says "we hold a lock while configuring and running to avoid cross-thread interference" but the lock is NOT held during `set_usage_metrics_path` (lines 107, 150) or during `IdentifyPotentialLevers.execute()`.

In parallel execution (`workers > 1`), the race is:

1. Thread A: `set_usage_metrics_path(path_A)` — global now points to plan A
2. Thread B: `set_usage_metrics_path(path_B)` — global clobbered, now points to plan B
3. Thread A's LLM calls write metrics to plan B's file
4. Thread A finishes: `set_usage_metrics_path(None)` — clears the path while Thread B is still running, silently dropping B's remaining metrics

All runs 61–66 (4 workers each) are affected. Usage metrics may be written to the wrong plan's file or dropped entirely. This explains why `insight_codex.md` observes that telemetry is incomplete and failures visible in `usage_metrics.jsonl` are hard to correlate with plan identity.

---

### B2 — Per-call LLM failures not emitted to `events.jsonl`

**File**: `identify_potential_levers.py:304–318`

```python
except Exception as e:
    llm_error = LLMChatError(cause=e)
    logger.debug(f"LLM chat interaction failed [{llm_error.error_id}]: {e}")
    logger.error(f"LLM chat interaction failed [{llm_error.error_id}]", exc_info=True)
    if len(responses) == 0:
        raise llm_error from e
    logger.warning(
        f"Call {call_index} of {total_calls} failed [{llm_error.error_id}], "
        f"continuing with {len(responses)} prior call(s)."
    )
    continue
```

When calls 2 or 3 fail and partial recovery is used, the `LLMChatError` is written only to the Python logger. No event is emitted that reaches `events.jsonl`. The `runner.py` code emits a `partial_recovery` event (with counts) but never records the failure cause (JSON parse error, timeout, validation error, etc.).

The `identify_potential_levers.py` class has no access to `events_path`, so the failure information cannot reach `events.jsonl` without an architectural change (e.g., a failure-callback parameter to `execute()`).

The result: diagnosing why run 60 had partial recovery on two plans requires digging into `usage_metrics.jsonl` rather than `events.jsonl` — confirmed by `insight_codex.md`: "run 60 definitely had failures, visible only in `usage_metrics.jsonl`."

---

## Suspect Patterns

### S1 — `_resolve_workers` uses `min()` across primary and fallback models

**File**: `runner.py:249–264`

```python
for name in model_names:
    config = all_configs.get(name)
    ...
    workers_candidates.append(w)

return min(workers_candidates) if workers_candidates else 1
```

`model_names[0]` is the primary model; subsequent names are fallbacks. If the primary model has `luigi_workers=4` and a fallback has `luigi_workers=1`, `min([4, 1]) = 1`, silently throttling to sequential execution. The caller has no indication that a fallback config is limiting parallelism. The primary model's `luigi_workers` value is the relevant one (since the fallback is only tried when the primary fails). Consider using the primary's value or at least logging which model's config is limiting workers.

---

### S2 — `track_activity.jsonl` is created and immediately deleted

**File**: `runner.py:100–103, 152–153`

```python
track_activity_path = plan_output_dir / "track_activity.jsonl"
track_activity = TrackActivity(
    jsonl_file_path=track_activity_path,
    write_to_logger=False,
)
...
finally:
    ...
    track_activity_path.unlink(missing_ok=True)
```

The `TrackActivity` handler writes events to `track_activity_path`, which is unconditionally deleted in the finally block. If the intent is to capture per-plan dispatcher events transiently and then discard them, this is correct but deserves a comment explaining why the file is deleted (e.g., "temporary; captured data flows into usage_metrics via the dispatcher"). Without context, this looks like orphaned code or a cleanup oversight.

---

### S3 — Non-deterministic config merge in `_resolve_workers`

**File**: `runner.py:241–246`

```python
for json_file in llm_config_dir.glob("*.json"):
    try:
        with open(json_file) as f:
            all_configs.update(json.load(f))
```

`glob()` returns files in filesystem order (non-deterministic). If two config files define the same model name with different `luigi_workers`, the last file processed wins. In practice this is unlikely to matter, but it means the resolved worker count could differ between machines or OS versions.

---

## Improvement Opportunities

### I1 — Concept-level anti-repetition in inter-call prompt

**File**: `identify_potential_levers.py:269–276`

```python
names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    ...
)
```

The exclusion list is names only. A model that appends a qualifier to an existing name ("Digital Identity Standards" → "Digital Identity Standards Enforcement") is technically compliant while generating a conceptually identical lever. The downstream `DeduplicateLeversTask` must then catch these, but the pre-dedup lever pool contains wasteful near-duplicates.

Proposed change: replace "completely different names" with "entirely different strategic topics and concepts" and frame the name list as examples of concepts to avoid, not just names:

```python
topic_summary = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 to 7 MORE levers covering entirely different strategic topics and concepts. "
    f"Do NOT generate a lever that addresses the same topic as any of these — "
    f"even under a different name: [{topic_summary}]\n"
    ...
)
```

Expected effect: fewer semantic duplicates in weak models (llama3.1, qwen3) without requiring downstream semantic dedup to compensate.

---

### I2 — Single `review_lever` example anchors all models to identical openings

**File**: `identify_potential_levers.py:94–98` (Pydantic field description) and `identify_potential_levers.py:216–218` (system prompt section 4)

Both locations provide the same single example:
> "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs."

Across all 7 runs, between 82–106 of ~91 reviews begin with "This lever governs" or "This lever controls" — a near-total template takeover confirmed in `insight_codex.md`'s template leakage table. The prompt itself creates this monoculture by providing only one stylistic template.

Mitigation: provide 2–3 stylistically varied examples in the Pydantic field description, or add an explicit instruction to vary opening phrasing:

> "Vary your review style — do not begin every review the same way."

---

### I3 — Conservative-path requirement not reinforced in calls 2 and 3

**File**: `identify_potential_levers.py:270–276`

The inter-call prompt (lines 270–276) reinforces option-length and anti-fabrication requirements but does NOT repeat the conservative-path requirement from `OPTIMIZE_INSTRUCTIONS` (lines 50–51):
> "Each lever's options should include at least one conservative, low-risk path"

As a result, weaker models (llama3.1) satisfy the conservative-path requirement on call 1 levers (which see the full system prompt) but drift toward hybrid/moderate-only choices on calls 2–3. Adding a one-line reminder would reinforce it across all calls:

```python
f"Each lever must include at least one explicitly conservative, low-risk option — "
f"not just a 'hybrid' or 'balanced' approach.\n"
```

---

### I4 — `OPTIMIZE_INSTRUCTIONS` missing "precision theater" pattern

**File**: `identify_potential_levers.py:27–69`

`OPTIMIZE_INSTRUCTIONS` guards against fabricated percentages and marketing language, but not against a third failure mode: pseudo-precise operational thresholds that avoid hype words while still being fabricated. Examples from run 66 (haiku):
- "60–70% of principal photography"
- "40–50% of budget"
- "51%/49% equity split"
- "3–5% interest rate"
- "estimated 40% throughput reduction"

These pass the current prompt prohibitions (no marketing language, no vague aspirations) while violating the spirit of the anti-fabrication rule. `insight_codex.md` calls this "precision theater."

Add to `OPTIMIZE_INSTRUCTIONS` known-problems list:

> - **Precision theater.** Models may avoid marketing language yet still produce unsupported
>   pseudo-precise thresholds: budget splits, equity percentages, throughput figures,
>   probability estimates. These are as fabricated as "15% market-share growth". The
>   prohibition on fabricated numbers applies equally to derived operational specifics
>   (e.g., "60–70% of photography budget") unless the project context contains the
>   exact figure.

---

### I5 — Per-call failure callback to surface errors in `events.jsonl`

**File**: `identify_potential_levers.py:299–318`, `runner.py:115–117`

To address B2 without restructuring the class, add an optional `on_call_failure` callback parameter to `IdentifyPotentialLevers.execute()`:

```python
@classmethod
def execute(
    cls,
    llm_executor: LLMExecutor,
    user_prompt: str,
    system_prompt: Optional[str] = None,
    on_call_failure: Optional[callable] = None,
) -> 'IdentifyPotentialLevers':
    ...
    except Exception as e:
        llm_error = LLMChatError(cause=e)
        if on_call_failure:
            on_call_failure(call_index, llm_error)
        ...
```

The caller in `runner.py` can then emit the failure event:

```python
def on_call_failure(call_index, error):
    _emit_event(events_path, "llm_call_failed",
                plan_name=plan_name,
                call_index=call_index,
                error_id=error.error_id,
                error=str(error.cause))

result = IdentifyPotentialLevers.execute(
    llm_executor, user_prompt,
    system_prompt=system_prompt,
    on_call_failure=on_call_failure,
)
```

This makes per-call failure causes visible in `events.jsonl` without changing the return type or error-recovery behavior.

---

## Trace to Insight Findings

| Insight observation | Code root cause |
|---------------------|-----------------|
| **N1** — Run 60 semantic duplication (24 levers, 8 near-identical) | **I1**: inter-call prompt constrains lever *names* only (lines 269–276); name-only dedup at lines 333–336 lets concept duplicates through |
| **N2** — Run 60 partial recovery, no LLMChatError in events.jsonl | **B2**: per-call exception is caught and logged to Python logger but not emitted to events.jsonl (lines 304–318) |
| **N4** — Review formula repetition ("This lever governs…" in ~85–100% of reviews) | **I2**: single example in Pydantic field description (line 95) and system prompt (line 217) anchors all models to one template |
| **N5** — Conservative path missing in llama3.1 calls 2 and 3 | **I3**: conservative-path requirement in OPTIMIZE_INSTRUCTIONS not repeated in inter-call prompt (lines 270–276) |
| **insight_codex N1** — Run 66 regresses with precision theater (unsupported percentages) | **I4**: OPTIMIZE_INSTRUCTIONS (lines 46–57) prohibits marketing language and "fabricated percentages" but does not name the precision-theater pattern, which models treat as distinct from vague hype |
| **insight_codex evidence note** — "Events telemetry is incomplete; run 60 failures visible only in usage_metrics.jsonl" | **B2**: `LLMChatError` on partial recovery is only logged, never emitted as an event |
| **insight_codex evidence note** — Usage metrics potentially unreliable in parallel runs | **B1**: `set_usage_metrics_path` sets module-global state outside `_file_lock`; parallel threads clobber each other's path (lines 107, 150) |
| **insight_codex C2** — "Emit per-call failure events into events.jsonl" | **B2** + **I5**: confirmed architectural gap; callback pattern closes it without restructuring the class |
| **insight_codex H1** — Template monoculture in review openings | **I2**: single example in both Pydantic field description and system prompt drives convergence |

---

## Summary

**Two confirmed bugs:**

**B1** is the most severe in production: `set_usage_metrics_path` is called outside `_file_lock` in a function that runs in a thread pool (`workers > 1`). In parallel runs (61–66, all using 4 workers), usage metrics from different plans can be written to the wrong file or dropped when the path is cleared mid-execution. The comment at line 98 says the lock prevents this but the code does not enforce it.

**B2** is an observability bug: when a partial-recovery call fails, the error reason (JSON parse failure, timeout, validation rejection) is logged only to Python's logger and never reaches `events.jsonl`. This makes it impossible to distinguish transient model failures from prompt-induced structural failures using the events telemetry alone.

**Four improvement opportunities** have clear prompt-quality impact:

- **I1** (concept-level anti-repetition): the highest-leverage code-side change. Prevents semantic duplication at the source without requiring semantic dedup to compensate.
- **I2** (varied review examples): cheap one-line fix that breaks the "This lever governs" monoculture seen in all 7 runs.
- **I3** (conservative path in calls 2–3): reinforces an existing OPTIMIZE_INSTRUCTIONS requirement that currently has no effect on calls 2 and 3.
- **I4** (precision theater in OPTIMIZE_INSTRUCTIONS): names a known failure mode (run 66) so future prompt iterations can address it explicitly.
