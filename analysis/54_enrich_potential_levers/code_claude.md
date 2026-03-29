# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`

PR under review: #451 ("Include consequences and review in enrich batch prompt")

---

## Bugs Found

### B1 — No per-batch retry in `enrich_potential_levers.py:216-218`

```python
except Exception as e:
    logger.error(f"LLM batch interaction failed ...")
    raise ValueError("LLM batch interaction failed.") from e
```

Any single batch failure immediately raises and kills the entire plan — no retry, no
partial fallback. `identify_potential_levers.py` has a 5-call adaptive loop with per-call
error recovery (lines 329-348), but `enrich_potential_levers.py` has none. A transient
timeout or token overflow on one batch of 5 levers causes all remaining batches to be
discarded and the plan marked "error".

This is the root cause of gpt-oss-20b's 0/5 success rate (N1 in the insight): the model
overflows tokens on batch 1, raises immediately, and all five plans fail.

### B2 — Full UUIDs in `full_lever_context_str` (`enrich_potential_levers.py:156`)

```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

The context list that models use to write synergy/conflict lever references includes full
36-char UUIDs. Models treat the context format as a copy template. This explains:
- llama3.1 synergy/conflict containing `(ed16c55c-fd66-41a1-b5e8-b22eccadbaaf)` style refs
- qwen3-30b using truncated 8-char UUIDs before PR #451
- qwen3-30b's UUID format inconsistency after the PR (N4): more context changes how
  the model interprets the format signal, producing name-only in some plans and full UUIDs
  in others

The `lever_id` field is never referenced downstream in synergy/conflict text — only the
`name` is needed for human-readable output. Emitting UUIDs here provides no useful
information while actively degrading output quality.

### B3 — Incomplete enrichment silently drops levers (`enrich_potential_levers.py:220-228`)

```python
final_characterized_levers = []
for lever_id, data in enriched_levers_map.items():
    if all(k in data for k in ['description', 'synergy_text', 'conflict_text']):
        try:
            final_characterized_levers.append(CharacterizedLever(**data))
        except ValidationError as e:
            logger.error(...)
    else:
        logger.error(f"Characterization incomplete for lever '{lever_id}'. Skipping this lever.")
```

If the LLM omits a lever from a batch response (returns 4 of 5), that lever is silently
dropped with only a log error. The caller in `runner.py` always returns `status="ok"` and
`calls_succeeded=1` (B4 below) regardless of how many levers were actually enriched.
Downstream steps (FocusOnVitalFewLevers, ScenarioGeneration) receive fewer levers than
expected with no indication that enrichment was incomplete. There is no minimum threshold
check before returning.

### B4 — `calls_succeeded` hardcoded to 1 in `_run_enrich` (`runner.py:183`)

```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=1,  # ← always 1, regardless of batch count
)
```

With `BATCH_SIZE = 5` and typically 10–15 levers, enrich makes 2–3 LLM calls per plan,
not 1. The hardcoded value makes monitoring tools that inspect `calls_succeeded` mislead-
ing and prevents detecting partial batch failures. `_run_levers` correctly returns
`len(result.responses)` (line 126).

### B5 — Partial recovery threshold fires for normal 2-call runs (`runner.py:131`, `runner.py:579`)

```python
# runner.py:131
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")

# runner.py:577-583
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The comment at line 128 acknowledges that "a 2-call success is normal for models that
produce 8+ levers per call." Despite this, the warning and event fire for all 2-call runs.
A model returning 8 levers on call 1 and 7 on call 2 (15 total, ≥ `min_levers`) triggers
"partial_recovery" even though the step succeeded fully. This pollutes events.jsonl and
confuses analysis that treats `partial_recovery` as a quality signal.

---

## Suspect Patterns

### S1 — Closure variable capture in loop bodies

`identify_potential_levers.py:319` and `enrich_potential_levers.py:192` both define
`execute_function` inside a loop that captures a loop-local variable by reference:

```python
# identify_potential_levers.py
messages_snapshot = list(call_messages)
def execute_function(llm: LLM) -> dict:
    chat_response = sllm.chat(messages_snapshot)  # captures by reference

# enrich_potential_levers.py
chat_message_list = [system_message, ChatMessage(...)]
def execute_function(llm: LLM) -> dict:
    chat_response = sllm.chat(chat_message_list)  # captures by reference
```

Since `llm_executor.run()` appears to call the function synchronously, the captured
variable hasn't been reassigned yet when `execute_function` executes — no bug today. But
if the executor ever calls the function asynchronously (e.g., for retry in a background
thread), the closure will use the variable's value at call time, not at definition time,
potentially sending the wrong batch's messages. This is a latent bug.

### S2 — `TrackActivity` dispatcher is global; per-plan handlers receive cross-plan events (`runner.py:248-251`)

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`dispatcher` is the LlamaIndex global event dispatcher. When `workers > 1`, multiple
plans run concurrently, each adding its own `TrackActivity` handler. Every LLM event
from any plan fires on all registered handlers. Plan A's `track_activity` receives Plan B's
LLM events and writes them to Plan A's `track_activity.jsonl`.

The practical impact is mitigated because `track_activity_path.unlink(missing_ok=True)`
discards the file afterward (line 283), and `_maybe_generate_activity_overview` reads only
from the thread-local `usage_metrics.jsonl`. However, if `TrackActivity` generates an
`activity_overview.json` directly (for non-Anthropic backends), that file may contain
cross-plan events. The thread filter applied to the log file handler (line 545) is not
applied to the dispatcher handler.

### S3 — Direct list mutation `dispatcher.event_handlers.remove()` (`runner.py:282`)

```python
dispatcher.event_handlers.remove(track_activity)
```

This mutates the global handlers list directly. If another thread is simultaneously
iterating the list to dispatch an event, this could raise a `RuntimeError` ("list changed
size during iteration") or silently skip a handler. The lock at line 280 protects the
remove itself but not concurrent list iteration by the dispatcher. Whether the LlamaIndex
dispatcher holds its own lock during iteration is not visible from this file.

---

## Improvement Opportunities

### I1 — Use name-only in `full_lever_context_str` (`enrich_potential_levers.py:156`)

Change:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
to:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

UUIDs in the context list serve no purpose (synergy/conflict text uses names, not IDs)
and actively encourage models to copy UUID format into output text. This directly addresses
B2 (UUID format inconsistency in qwen3-30b after PR #451, N4 in insight).

### I2 — Add per-batch retry with backoff or reduced batch size (`enrich_potential_levers.py:199-218`)

The current raise-on-any-failure pattern (B1) means one overflowing batch kills all
subsequent batches. A minimal fix: on exception, log the error and continue to the next
batch rather than raising. The incomplete levers will be caught at line 228 and logged.
A stronger fix: retry the failed batch with levers processed one at a time (batch size 1).

### I3 — Add explicit elaboration instruction for `description` field to prevent consequence-echoing

After PR #451, llama3.1 descriptions dropped from 386 to 316 chars (0.65× baseline, N2
in insight). The model is summarizing the `consequences` text verbatim rather than using
it as grounding for a richer description. The current field instruction in
`ENRICH_LEVERS_SYSTEM_PROMPT` says "(80-100 words) Clearly explain the lever's purpose,
what it controls, its objectives, and key success metrics." Adding explicit guidance to
use consequences as context, not as the description itself, would help:

> "Use the Consequences field as background grounding, but write a description that
> elaborates on purpose, scope, and success metrics in at least 3 original sentences —
> do not paraphrase or summarize the Consequences text directly."

### I4 — Update `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` with consequence-echoing failure mode

The current `OPTIMIZE_INSTRUCTIONS` list (lines 27-81) does not mention the failure mode
observed in N2: weak models summarizing `consequences` verbatim in the `description` field
after the PR added those fields to the prompt. This should be added as a distinct entry
under "Known problems to guard against":

> "Consequence echoing. When `consequences` and `review` are included in the batch
> prompt, weak models may rephrase the consequences field verbatim as the description
> rather than using it as grounding for a richer explanation of purpose, scope, and
> success metrics."

### I5 — `options` validator allows >3 options despite "Exactly 3" specification (`identify_potential_levers.py:147-158`)

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v
```

The validator comment says "Over-generation (>3) is tolerable; under-generation is not,"
which contradicts the field description ("Exactly 3 options. No more, no fewer.") and the
system prompt directive. Models producing 4 or 5 options are silently accepted, and
downstream consumers may not handle >3 options correctly. At minimum, the field description
and system prompt should be consistent with the actual enforcement policy.

### I6 — `consequences` field description contains English-only anti-patterns despite OPTIMIZE_INSTRUCTIONS warning (`identify_potential_levers.py:113-119`)

```python
consequences: str = Field(
    description=(
        "...Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field..."
    )
)
```

`OPTIMIZE_INSTRUCTIONS` explicitly warns at lines 61-68: "Validators and auto-correct
logic must not rely on English keywords like 'Controls', 'Weakness:', 'versus'/'vs.'
being present in the LLM output." The `consequences` field description then names those
exact English phrases as anti-patterns. Models receiving prompts in Chinese, Japanese, or
Arabic will not recognize these English-specific patterns as instructions. The prohibition
should be stated structurally ("do not include critique or trade-off text — that belongs
in `review_lever`") rather than by listing English-language examples.

### I7 — Qualitative mechanism guidance missing for synergy/conflict (D3 gap)

qwen3-30b's synergy/conflict texts remain terse (0.74-0.76× baseline) despite the PR.
The current system prompt provides a quantitative "(40-60 words)" target but no guidance
on *what kind* of information should go in those words. Guidance like "name the specific
mechanism by which the two levers interact, and identify one concrete consequence of that
interaction" would prevent terse placeholder-style outputs ("This lever synergizes with X
to improve outcomes").

---

## Trace to Insight Findings

| Insight observation | Code location | Explanation |
|---------------------|---------------|-------------|
| N1: gpt-oss-20b 0/5 success unchanged | `enrich_potential_levers.py:216-218` (B1) | No per-batch retry; one token overflow raises and kills all batches |
| N2: llama3.1 description brevity 0.65× | `enrich_potential_levers.py:133` + missing guidance (I3) | System prompt says "(80-100 words)" but doesn't warn against consequence-summarizing; weak models take the shorter path |
| N3: qwen3-30b CJK char leak | No code bug; probabilistic | Adding consequences+review alters token probability distribution near multilingual boundaries; no structural guard exists |
| N4: qwen3-30b UUID format inconsistency | `enrich_potential_levers.py:156` (B2, I1) | Full UUIDs in `full_lever_context_str` are a format template; more context makes model interpretation less deterministic |
| N5: ~18-20% input token increase | Expected consequence of PR | Each lever adds ~200-400 chars of consequences+review text; no bug |
| P1: gpt-5-nano template artifact eliminated | PR #451 correctly adds consequences+review context | More specific context reduces probability of generic template output |
| P2/P3: Grounded conflict/description | PR #451 correctly adds consequences+review context | Direct mechanism: consequences language now in prompt context |
| `partial_recovery` events in runs with 2 calls | `runner.py:131,579` (B5) | Threshold `< 3` fires for normal 2-call success |

---

## PR Review

### What the PR changes

`enrich_potential_levers.py:171-178` — adds `Consequences` and `Review` to
`lever_details_for_prompt` in the batch body. No other files changed.

### Does the implementation match the intent?

Yes. The PR adds exactly the two fields identified in analysis 53 synthesis direction 1.
The construction is correct:

```python
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"   # ← added
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}"                 # ← added
    for lever in batch
])
```

Label names (`Consequences:`, `Review:`) match the semantic content of `InputLever.
consequences` and `InputLever.review`. No duplication, no field ordering issues.

### Gaps in the PR

**G1 — `full_lever_context_str` intentionally left unchanged at line 156.**
The PR author noted the UUID format issue (B2) as a separate deferred item. This is the
right call for PR hygiene (one concern per PR), but the insight shows B2's impact
worsened post-PR: qwen3-30b's format is now inconsistent across plans where it was
previously consistently wrong (truncated UUIDs). The gap is known and should be
tracked.

**G2 — No length guard on `lever.consequences` or `lever.review` in the prompt.**
If a lever's `consequences` field is very long (e.g., from a verbose upstream model),
the batch prompt token count grows unboundedly. For gpt-oss-20b (already failing due to
token overflow) this exacerbates B1. A soft truncation guard (e.g., limit each
`consequences` to 500 chars in the prompt) would keep token counts bounded.

**G3 — The PR adds context but doesn't add an anti-echoing instruction.**
As observed in N2, adding `consequences` to the prompt can cause weak models to echo it
rather than use it as grounding. The PR would have been more complete with the elaboration
instruction from I3 added simultaneously.

### Could the change introduce new issues?

- **Yes for weak models (N2):** Providing `consequences` text gives llama3.1 a shorter
  path — summarize consequences → done. Without an explicit anti-echoing instruction, this
  is a regression in description depth.
- **Yes for multilingual models (N3):** Adding more English-language context fields
  near the language boundary of multilingual models increases CJK leak probability. Not
  systematic, but observable.
- **Potential for verbosity overflow models:** For models that are already near output
  token limits (gpt-oss-20b), adding ~200-400 input tokens per lever increases the output
  it tries to produce proportionally, making overflow more likely.

### Verdict

The PR is correct and should be kept. The primary gains (gpt-5-nano template elimination,
cross-model consequence grounding) outweigh the regressions. The gaps (G1-G3) are
appropriate candidates for follow-up PRs.

---

## Summary

**Confirmed bugs:**
- **B1** (critical): No per-batch retry in `enrich_potential_levers.py` — single batch
  failure kills entire plan. Root cause of gpt-oss-20b 0/5 success.
- **B2** (quality): Full UUIDs in `full_lever_context_str` encourage UUID copying in
  synergy/conflict text; worsened post-PR for qwen3-30b.
- **B3** (silent data loss): Incomplete enrichment silently drops levers with no count
  returned to caller.
- **B4** (monitoring): `calls_succeeded=1` hardcoded in `_run_enrich`, always wrong for
  multi-batch plans.
- **B5** (false positive): `partial_recovery` warning/event fires for normal 2-call
  success runs.

**Top improvement opportunities:**
- **I1**: Name-only `full_lever_context_str` — directly fixes N4 UUID inconsistency.
- **I2**: Per-batch retry — directly fixes B1 and gpt-oss-20b failures.
- **I3/I4**: Anti-consequence-echoing guidance in system prompt and
  `OPTIMIZE_INSTRUCTIONS` — directly addresses llama3.1 N2 brevity regression.
- **I7**: Qualitative mechanism guidance for synergy/conflict — addresses D3 gap
  (qwen3-30b terseness).

**PR #451 assessment:** Implementation is correct and clean. Produces measurable quality
improvements (gpt-5-nano template elimination, grounded conflict texts). The ~18-20%
token cost increase is the expected and confirmed trade-off. Three pre-existing gaps
(B1 retry, B2 UUID format, D3 qualitative guidance) were intentionally deferred and
remain the highest-priority follow-up items.
