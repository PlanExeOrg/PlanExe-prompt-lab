# Code Review (claude)

## Bugs Found

### B1 — `partial_recovery` event fires for valid step-gate exits (runner.py:517–523)

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ..., expected_calls=3)
```

The check `calls_succeeded < 3` fires whenever a run uses fewer than 3 LLM calls,
regardless of whether the `min_levers=15` threshold was met. A haiku run that
produces 20 levers in 2 calls is a successful early step-gate exit — it should not
trigger `partial_recovery`. The event name misleadingly signals degraded output when
the run was entirely healthy.

Root cause: runner.py has no access to how many levers were produced — only the call
count. The `IdentifyPotentialLevers` result is not inspected for `len(result.levers)`.

Fix: surface the final lever count in `PlanResult.calls_succeeded` or a new field,
and emit `partial_recovery` only when `len(result.levers) < min_levers`.

**Severity: medium** — emits false-positive events that distort the insight analysis
(the "3.8pp regression" and "haiku -20pp" observations in the insight file are
partially measuring valid early exits, not failures).

---

### B2 — Silent under-delivery: error swallowing can return fewer than min_levers levers (identify_potential_levers.py:336–342)

```python
if len(responses) == 0 and call_index == max_calls:
    raise llm_error from e
logger.warning(f"Call {call_index} ... failed, continuing with {len(responses)} prior call(s).")
continue
```

If call 1 succeeds with 8 levers and calls 2–5 all fail, the function returns
successfully with 8 levers — below `min_levers=15` — without raising any error.
The caller receives `status="ok"` from `runner.py` because no exception was thrown.
The `partial_recovery` event fires only because `calls_succeeded < 3`, but the
underlying cause (repeated LLM errors) is lost.

Fix: after the loop, check `len(generated_lever_names) < min_levers` and either
raise, or record a diagnostic field in the result. This is distinct from the
valid early-exit case in B1.

**Severity: low** — masked by the `partial_recovery` event, but root cause is obscured.

---

### B3 — Global dispatcher receives event handlers from all concurrent threads (runner.py:190–194, 220–222)

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`dispatcher` is a process-wide LlamaIndex singleton. When `workers > 1`, each
thread adds its own `TrackActivity` handler to the same dispatcher. Every LLM event
fired by any thread is delivered to every registered handler — meaning thread A's
LLM calls write into thread B's `track_activity.jsonl` and vice versa.

The contamination is largely harmless in practice because `track_activity_path` is
deleted at line 223 (`unlink(missing_ok=True)`) and the `activity_overview.json` is
rebuilt from thread-local `usage_metrics.jsonl` instead. But if any code path reads
`track_activity.jsonl` before the `finally` block runs, it would see mixed events.

The `_file_lock` guards the `add_event_handler` call but cannot prevent the
dispatcher from broadcasting to all registered handlers — locking the registration
does not make dispatching thread-local.

**Severity: low** — mitigated by the `unlink` in `finally`.

---

## Suspect Patterns

### S1 — `execute_function` closure captures `messages_snapshot` by name (identify_potential_levers.py:311–315)

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

Python closures capture variables by reference, not value. If `llm_executor.run()`
were ever to defer calling `execute_function` (e.g., via async scheduling or thread
pool), it would read the `messages_snapshot` binding from a later loop iteration.
Today `run()` is synchronous so this is safe, but the pattern is fragile. Using
a default-argument capture (`def execute_function(llm, _snap=messages_snapshot)`)
would make this robust.

**Current risk: none** — but a latent trap if `LLMExecutor.run()` is made async.

---

### S2 — `options` field description contradicts the validator (identify_potential_levers.py:115–118, 141–153)

Field description: `"Exactly 3 options for this lever. No more, no fewer."`
Validator (line 151): `if len(v) < 3: raise ValueError(...)`  — upper bound absent.

The model reads "no more, no fewer" as a hard constraint. The validator accepts 4+
options silently. This inconsistency could cause confusion: a model that follows the
description literally generates exactly 3; a model that ignores it might generate 5,
pass validation, and go downstream with extra options that break callers expecting
exactly 3. The comment at line 181–183 (`DocumentDetails.levers`) correctly explains
why `max_length` is absent there, but the `options` field has a different situation —
the description explicitly says "no more".

**Fix**: Either drop "No more, no fewer" from the description, or add an upper-bound
validator that trims rather than rejects (to avoid a full retry).

---

### S3 — English-specific prohibition text in `consequences` field description (identify_potential_levers.py:110–112)

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"
```

The OPTIMIZE_INSTRUCTIONS (lines 61–68) specifically warns that English-keyword
checks will fail on non-English inputs. While this text is in a Pydantic *field
description* (prompt instruction) rather than a code validator, the effect is the
same: a model responding in Japanese, Arabic, or German will not produce "Controls"
or "Weakness:" regardless, so the instruction is irrelevant for non-English outputs
and wastes token budget. For English outputs, models that don't know what "Controls
… vs." means structurally will be confused by the cryptic pattern reference.

**Fix**: Replace with a structural description: "Do not include critical analysis or
trade-off commentary in this field — those belong in review_lever."

---

## Improvement Opportunities

### I1 — Raise `min_levers` from 15 to 18 (identify_potential_levers.py:285)

With haiku now generating 8–12 levers per call (post PR #361), `min_levers=15` is
crossed in 2 calls for every plan (2 × 8 = 16 ≥ 15). The third call uses a
diversity-constraining prompt ("Generate MORE levers with completely different
names") that produces a qualitatively different perspective. Consistently missing
the third call reduces per-plan lever diversity.

Setting `min_levers = 18` would require haiku to complete a third call even at 8
levers/call (2 × 8 = 16 < 18 → third call needed). Models generating 6–7/call
already need 3 calls (3 × 7 = 21 ≥ 18) and would be unaffected.

Risk: minimal. Models generating ≥ 18 levers in 2 calls (9+/call) would still exit
early, but this is the upper edge of haiku's current range.

---

### I2 — Add `lever_count` to `PlanResult` and fix `partial_recovery` semantics (runner.py:96–101, 517–523)

`PlanResult` currently tracks only `calls_succeeded`. Adding `lever_count: int`
would allow:
1. Emitting `partial_recovery` only when `lever_count < min_levers` (not when
   `calls_succeeded < 3`).
2. Recording lever yield per run in `outputs.jsonl` for trend analysis.

This would correctly distinguish "haiku produced 20 levers in 2 calls (healthy)" from
"model produced 8 levers in 1 call after 4 failures (degraded)".

---

### I3 — Surface whether min_levers was met in the loop result (identify_potential_levers.py:380–386)

`IdentifyPotentialLevers` does not expose whether the adaptive loop exited because
the threshold was met or because `max_calls` was exhausted. Adding a boolean field
`min_levers_met: bool` (or `exit_reason: str`) to the result dataclass would let
`runner.py` emit more precise events without needing to reimplement the threshold
logic.

---

### I4 — OPTIMIZE_INSTRUCTIONS: add "schema field count affects per-call lever compactness" note (identify_potential_levers.py:27–93)

The current OPTIMIZE_INSTRUCTIONS documents most known failure modes but is missing
one now confirmed by PR #361: removing (or adding) a field from the `Lever` schema
changes the per-lever JSON token footprint. A one-field removal made each lever's
JSON ~15–20 tokens shorter, which caused haiku to fit 8–12 levers per call instead
of 6–7, triggering the step-gate after 2 calls instead of 3.

Proposed addition after the "Verbosity amplification" entry (line 83–85):
> Schema field count side effects. Removing or adding fields from the `Lever` schema
> changes the per-lever JSON token footprint. Fewer fields → more compact JSON →
> more levers per call → earlier step-gate exit. After any schema field change,
> verify that haiku and llama3.1 still require 3 calls. If they now consistently
> exit after 2 calls, raise `min_levers`.

---

### I5 — OPTIMIZE_INSTRUCTIONS: add "over-generation per call" note (identify_potential_levers.py:43–44)

Line 43–44 says "Over-generation is fine; step 2 handles extras." This is true at
the *plan* level. But consistent per-call over-generation (8–12 instead of 5–7)
causes the step-gate to exit early, reducing lever diversity by skipping the
third call's unique-names constraint.

Proposed replacement:
> Over-generation at the plan level is fine — step 2 handles extras. However, some
> models consistently generate 8–12 levers per call instead of the 5–7 target,
> causing the step-gate to exit after 2 calls and skipping the third call's
> diversity-constraining prompt. If a model always exits after 2 calls, raise
> `min_levers` to restore 3-call behavior.

---

## Trace to Insight Findings

| Insight observation | Code location | Explanation |
|---|---|---|
| Haiku partial_recovery: 2/5 → 5/5 plans after PR | runner.py:517–523 (B1) + identify_potential_levers.py:285 (I1) | The B1 false-positive means ALL 2-call runs emit `partial_recovery`. The real mechanism: min_levers=15 is crossed by haiku's 8–12/call rate. |
| Overall call efficiency -3.8pp (97.1% → 93.3%) | identify_potential_levers.py:285, 348 | Step-gate fires at 15 levers. With haiku generating 8–12/call, 2 calls × 8 = 16 ≥ 15 for every plan. |
| Events show partial_recovery for "healthy" haiku runs | runner.py:517–523 (B1) | Hardcoded `expected_calls=3` treats early-exit success as failure. |
| "None/all three options" review_lever template lock | identify_potential_levers.py:119–127 (review_lever field description) | OPTIMIZE_INSTRUCTIONS entry at lines 86–92 predicts this: structural cues in field descriptions drive template lock. The field description "state the specific gap the three options leave unaddressed" encourages "none of the three options…" responses. This is a pre-existing issue not introduced by PR #361. |
| Silo review length increase (304 → 420 chars) | identify_potential_levers.py:256 | Section 6 says "Keep each review_lever to one sentence (20–40 words)" but the validator at line 167 only enforces a 10-char minimum. The 20–40 word instruction has no enforcement, allowing verbosity creep. |
| Haiku per-call lever count increased (6–7 → 8–12) | PR #361 removed lever_index + identify_potential_levers.py:285, 348 | Fewer JSON fields per lever → more compact output → more levers fit in model's per-call token budget. Documented in I4. |

---

## PR Review

**PR #361: "experiment: remove lever_index from Lever schema"**

### What changed

The `lever_index: int` field was removed from the `Lever` Pydantic class. The field
was LLM-generated but never read downstream: `LeverCleaned` at lines 360–374 assigns
`lever_id = str(uuid.uuid4())` fresh, without reading `lever_index` from the source
`Lever` object. The removal eliminates dead schema weight.

### Is the implementation correct?

Yes. The mapping at lines 360–374 confirms `lever_index` was never transferred:

```python
lever_cleaned = LeverCleaned(
    lever_id=lever_id,        # fresh uuid, not from lever.lever_index
    name=lever.name,
    consequences=lever.consequences,
    options=lever.options,
    review=lever.review_lever,
)
```

No downstream code reads `lever_index`. The PR is mechanically correct.

### Does it fix the stated problem?

Fully: zero models inserted "1.", "2." index prefixes in `name` or `consequences`
fields after the removal (confirmed across all 7 models, 5 plans each). The "sink"
concern was not needed — models did not leak sequential numbering into other fields.

### Unintended consequence: haiku step-gate regression

The PR has one observable side effect: haiku now generates 8–12 levers per call
instead of ~6–7, causing the step-gate (`min_levers=15`) to fire after 2 calls
for every plan. Before the PR, haiku needed 3 calls for 3/5 plans.

Plausible mechanism: removing the `lever_index: int` field makes each lever's
structured JSON output ~15–20 tokens shorter. Haiku's per-call output budget is
similar before and after (confirmed by token counts: ~2600–2900 tokens/call before
and after). With fewer tokens consumed per lever, more levers fit per call.

This is not a code bug introduced by the PR — it's a behavioral consequence of
schema compactness. The PR is correct; the step-gate threshold needs recalibration
(I1).

### Gaps in the PR

None in the code change itself. The PR description correctly identified the risk
(index prefix leakage) and the field's unused status. The only missing piece is a
corresponding update to `min_levers` (which was outside the PR's stated scope).

### Verdict

The PR change is correct and should be kept. The schema is cleaner. The only
required follow-up is I1 (raise `min_levers` from 15 to 18) to restore 3-call
behavior for haiku.

---

## Summary

The codebase is generally well-structured with good documentation in
`OPTIMIZE_INSTRUCTIONS`. The most significant finding is **B1**: the `partial_recovery`
event in `runner.py` fires for any `calls_succeeded < 3`, including legitimate
early step-gate exits where min_levers was fully met. This means the "regression"
metrics in the insight file (haiku: 86.7% → 66.7%) partially measure valid early
exits rather than failures.

The core mechanical issue causing the haiku regression is `min_levers=15` being
too easily crossed at haiku's new 8–12 levers/call rate (**I1**). PR #361's removal
of `lever_index` is confirmed correct and the field was genuinely dead code.

Structural issues worth fixing:
- **B1**: false-positive `partial_recovery` events (runner.py:517–523)
- **B2**: error swallowing can silently under-deliver levers (identify_potential_levers.py:336–342)
- **S2**: `options` field description says "no more, no fewer" but validator allows >3 (identify_potential_levers.py:115–118)
- **I1**: raise `min_levers` from 15 to 18 to restore 3-call behavior for haiku
- **I4/I5**: update OPTIMIZE_INSTRUCTIONS with schema-compactness and per-call over-generation notes
