# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Assistant turn content is a Python dict, not a string
**File:** `identify_potential_levers.py:193–198`

```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].raw.model_dump(),
    )
)
```

`result["chat_response"].raw` is the parsed `DocumentDetails` Pydantic object.
`.model_dump()` produces a Python `dict`. When LlamaIndex serializes this
`ChatMessage` for subsequent API calls it will stringify the dict using Python
repr syntax (`{'strategic_rationale': ..., 'levers': [...]}`) rather than
proper JSON. The LLM on the second and third "more" turns therefore sees
malformed continuation context, not the JSON it originally emitted.

The correct value is the raw assistant text, which is
`result["chat_response"].message.content` (the actual JSON string the model
produced), or alternatively `json.dumps(result["chat_response"].raw.model_dump())`.

**Severity:** High — affects every multi-turn run. Models with strong
instruction-following may cope; weaker models are likely confused by the
Python-dict representation, which can cause worse structural compliance on
turns 2 and 3.

---

### B2 — Race condition: `set_usage_metrics_path` called outside the file lock in multi-worker runs
**File:** `runner.py:96–116`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # ← not locked

with _file_lock:
    dispatcher.add_event_handler(track_activity)                   # ← locked

t0 = time.monotonic()
try:
    ...
    result = IdentifyPotentialLevers.execute(...)                  # ← not locked
```

The comment at line 97–98 says "so we hold a lock while configuring and
running," but the lock covers only the `add_event_handler` call. The
`set_usage_metrics_path` global write and the full `IdentifyPotentialLevers.execute()`
call both run outside the lock. When `workers > 1`, two threads can interleave:

1. Thread A: `set_usage_metrics_path(plan_A/usage_metrics.jsonl)`
2. Thread B: `set_usage_metrics_path(plan_B/usage_metrics.jsonl)`  ← overwrites A's path
3. Thread A: runs LLM — metrics now written to plan_B's directory

**Severity:** Medium — only triggers when `luigi_workers > 1`. Corrupts
per-plan usage metrics; does not corrupt lever outputs.

---

### B3 — No per-call lever count validation before appending to the merged list
**File:** `identify_potential_levers.py:203–206`

```python
levers_raw: list[Lever] = []
for response in responses:
    levers_raw.extend(response.levers)
```

Each `DocumentDetails.levers` field is `list[Lever]` with no min/max
enforcement. If a model returns 7 levers in one call the merged list silently
grows to 17; if it returns 3 the list ends up at 13. The expected total is
`3 calls × 5 levers = 15`.

**Severity:** Medium — produces wrong-sized outputs that break downstream
assumptions. Manifests in run 16 (llama3.1 → 20 levers) and run 10
(15.2 levers average, one plan with 16).

---

## Suspect Patterns

### S1 — "more" prompt carries no context of already-generated levers
**File:** `identify_potential_levers.py:155–158`

```python
user_prompt_list = [
    user_prompt,
    "more",
    "more",
]
```

The second and third turns send only the bare string `"more"`. The model has
no reminder of which lever names it already produced and is therefore free to
generate the same themes again. The assistant history (even if serialized
correctly) contains the full `DocumentDetails` wrapper including
`strategic_rationale` and `summary`, not a compact list of lever names the
model can easily reason about.

This is the root cause of cross-call thematic redundancy observed across all
successful models (N8 in insight_claude).

---

### S2 — System prompt embeds a concrete numeric example that gets copied verbatim
**File:** `identify_potential_levers.py:95`

```
"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"
```

The prompt uses a literal worked example. Weaker models treat this as a
template to fill in rather than an illustration of the required structure.
Run 10 (gpt-5-nano) copies "25% faster scaling through" into 11 of 15 levers.

---

### S3 — `DocumentDetails` wrapper schema increases JSON extraction failure surface
**File:** `identify_potential_levers.py:53–62`

The structured output type requires `strategic_rationale`, `levers`, and
`summary` at the top level. Models that cannot reliably emit the full wrapper
(e.g. a truncated response, or a model that only returns the levers array)
cause total plan failure rather than partial recovery. Run 13 (gpt-oss-20b)
failed one plan because the response was cut off mid-lever; run 11 (nemotron)
failed all plans because it returned non-JSON output rather than the
structured schema.

There is no fallback path that tries to extract just the `levers` array if the
full `DocumentDetails` parse fails.

---

### S4 — `_history_run_dir` counter is not atomic across concurrent processes
**File:** `runner.py:257–285`

`_next_history_counter` scans the history directory and returns `max + 1`.
Two `runner.py` processes started within milliseconds can observe the same max
and produce the same run directory path. `mkdir(exist_ok=True)` silences the
collision rather than detecting it, and both processes then write into the
same run directory, overwriting each other's `meta.json`, `events.jsonl`, and
`outputs.jsonl`.

---

## Improvement Opportunities

### I1 — Feed prior lever names into "more" calls (addresses S1 / N8 / H3)
**File:** `identify_potential_levers.py:163–170`

After each LLM call, collect the names of generated levers and inject them
into the next user message:

```python
# pseudo-code, not a patch
already_names = ", ".join(r.name for resp in responses for r in resp.levers)
next_user_content = f"more\n\nAlready covered: {already_names}. Do not repeat these topics."
```

Expected effect: reduces duplicate lever names and cross-call thematic
clustering without changing the model or prompt preamble.

---

### I2 — Assert exactly 5 levers per response before accepting the batch (addresses B3 / N5)
**File:** `identify_potential_levers.py:200`

After `responses.append(result["chat_response"].raw)`, check:

```python
n = len(result["chat_response"].raw.levers)
if n != 5:
    raise ValueError(f"Expected 5 levers in turn {user_prompt_index}, got {n}")
```

This surfaces the overproduction problem (llama3.1 generating 6–7 per call)
as an explicit failure rather than a silently inflated merged list.

---

### I3 — Add post-merge total count guard (addresses B3 / C3 in insight_codex)
**File:** `identify_potential_levers.py:219`

After building `levers_cleaned`, enforce:

```python
if len(levers_cleaned) != len(user_prompt_list) * 5:
    raise ValueError(
        f"Expected {len(user_prompt_list) * 5} levers after merge, "
        f"got {len(levers_cleaned)}"
    )
```

---

### I4 — Add preflight model availability check before batch starts (addresses N1 / C1 in insight_codex)
**File:** `runner.py:93–94`

```python
llm_models = LLMModelFromName.from_names(model_names)
```

Run 09 wasted all five plans because the model name was not registered.
`LLMModelFromName.from_names` (or the underlying config loader) should be
called once before the plan loop with an explicit existence check that raises
immediately rather than failing per-plan.

---

### I5 — Add post-merge name deduplication or warning (addresses N4, N7 / C2 in insight_claude)
**File:** `identify_potential_levers.py:208–219`

After building `levers_cleaned`, detect exact duplicate names:

```python
seen_names: set[str] = set()
for lever in levers_cleaned:
    if lever.name in seen_names:
        logger.warning(f"Duplicate lever name: {lever.name!r}")
    seen_names.add(lever.name)
```

A stricter version would raise or trigger a retry rather than just logging.

---

### I6 — Replace worked-example metric with a structural placeholder (addresses S2 / N3 / H1)
**File:** `identify_potential_levers.py:95`

Change:
```
"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"
```
to:
```
"Include measurable outcomes: 'Systemic: [specific quantified impact, e.g. percentage change in X] through [mechanism]'"
```

This preserves the structural cue while removing the concrete text that
weaker models copy verbatim.

---

### I7 — Add graceful fallback: extract `levers` array from wrapper-shaped JSON (addresses S3 / N insight_codex C4)
**File:** `identify_potential_levers.py` (in the `execute_function` closure or caller)

If `sllm.chat()` fails because the model returned `{"levers": [...]}` or a
truncated response, a secondary parse attempt that extracts the `levers` field
directly would recover otherwise-usable responses. Run 13's parasomnia failure
was a truncation where content up to the truncation point was valid.

---

## Trace to Insight Findings

| Code location | Bug/Pattern | Insight observation |
|---|---|---|
| `identify_potential_levers.py:193–198` | B1 — dict content in assistant turn | Potentially degrades model behaviour on turns 2 and 3 for all runs; hard to isolate but consistent with structural drift observed in runs 14/15 (insight_codex) |
| `runner.py:106` | B2 — race on `set_usage_metrics_path` | Usage metrics files may contain wrong-plan data when `workers > 1` |
| `identify_potential_levers.py:203–206` | B3 — no per-call count check | N5: llama3.1 produces 20 levers; run 10 averages 15.2 levers (insight_claude Table A; insight_codex Uniqueness table) |
| `identify_potential_levers.py:155–158` | S1 — bare "more" prompt | N8: cross-call thematic redundancy (governance/resource/information themes repeated 2–3× across all models); insight_claude question 3; insight_codex cross-call duplication proxy table |
| `identify_potential_levers.py:95` | S2 — concrete example metric | N3: gpt-5-nano copies "25% faster scaling through" in 11/15 levers (insight_claude Table C) |
| `identify_potential_levers.py:53–62` | S3 — full wrapper schema, no fallback | Run 13 one plan failure (truncated JSON); run 11 total failure (no JSON at all); insight_codex C4 |
| `runner.py:257–285` | S4 — non-atomic history counter | Concurrent process collision would corrupt run directories; not observed in runs 09–16 but a latent risk |

---

## Summary

Three confirmed bugs were found:

- **B1** (High): The assistant's `ChatMessage.content` is set to a Python dict
  from `model_dump()` instead of the original JSON string the model produced.
  This corrupts the conversation history passed to turns 2 and 3, giving the
  model a Python-repr continuation rather than valid JSON. Fix: use
  `result["chat_response"].message.content` (the raw string) or
  `json.dumps(result["chat_response"].raw.model_dump())`.

- **B2** (Medium): A race condition in `runner.py` when `workers > 1` — the
  `set_usage_metrics_path` global is written outside the file lock, so
  per-plan metrics can be written to the wrong plan's directory.

- **B3** (Medium): No per-call or post-merge lever count guard. Models that
  return more or fewer than 5 levers per turn silently produce wrong-sized
  merged outputs (observed: 20 levers for llama3.1, 16 for gpt-5-nano on one
  plan).

Two structural patterns drive the majority of quality issues:

- **S1** (bare "more" prompt) causes cross-call thematic redundancy across all
  successful models. This is the single highest-leverage code change available:
  injecting a list of already-generated lever names into turns 2 and 3.

- **S2** (concrete numeric example in the system prompt) directly causes
  template leakage in run 10 (73% of levers copy "25% faster scaling through").
  Replacing it with a structural placeholder costs nothing and eliminates the
  leakage vector.

The improvements most likely to improve output quality across all models are,
in priority order: fix B1, implement I1 (lever-name context in "more" turns),
implement I6 (remove concrete example), implement I2+I3 (count guards).
