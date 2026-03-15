# Synthesis

## Cross-Agent Agreement

All four analysis files (insight_claude, insight_codex, code_claude, code_codex) converge on the
following points:

1. **PR #283's retry config does not fix the observed failure modes.** All three failures (run 81:
   empty JSON; run 83: EOF truncation; run 87: schema count violation) are structural or behavioral,
   not transient network faults. The retry path in `runner.py:94` fires on the same model with the
   same prompt, so none of these failure classes becomes recoverable.

2. **No content validation exists before `save_clean`.** Both code reviews independently identified
   that `save_clean` (lines 304–306) writes any schema-valid `Lever` without inspecting field
   content. This allows review text inside `consequences`, label-like one-word options, and
   unmeasurable consequence chains to be recorded as successful output. This is the root cause of
   the majority of silent quality failures across all runs.

3. **The `max_length=7` Pydantic constraint hard-fails instead of truncating.** When a model
   returns 8 levers, the `ValidationError` propagates out of `execute()` immediately. The two prior
   calls' valid levers are discarded with no trace on disk. Both code reviews called this out as the
   direct cause of run 87's `gta_game` failure.

4. **Each LLM call starts a fresh conversation; prior assistant turns are not threaded.**
   `call_messages` at lines 209–215 is always `[system, user]`. Later calls know only which names
   to avoid, not what was actually generated. Both code reviews flag this as the driver of
   conceptual repetition across calls in weaker models.

5. **Failure artifacts are deleted unconditionally.** `track_activity_path.unlink(missing_ok=True)`
   at `runner.py:143` runs in the `finally` block for every plan, success or failure. Raw model
   output is never saved for failed plans. All four files note that this makes error classification
   require re-running rather than inspecting existing artifacts.

6. **Race condition on global `set_usage_metrics_path`.** Both code reviews confirm that line 106
   (`set_usage_metrics_path(...)`) runs outside `_file_lock`, while `IdentifyPotentialLevers.execute()`
   at line 114 also runs outside the lock. The lock only protects `dispatcher.add_event_handler`
   (lines 108–109). With `workers > 1`, multiple threads overwrite the same global path concurrently.

7. **Run 85's `consequences` field is contaminated with review text at scale.** Both insight files
   confirm that `Controls ... vs. ... Weakness: ...` text bleeds into `consequences` for run 85.

---

## Cross-Agent Disagreements

### 1. Run ranking: insight_claude ranks run 87 first; insight_codex ranks run 84 first

**insight_claude** prioritises content depth — run 87 (claude-haiku) produces the longest,
most domain-specific consequences (~500 chars avg, measurable indicators in most levers) and is
ranked #1 despite one hard failure.

**insight_codex** prioritises the balance of reliability and quality — run 84 (gpt-5-nano) is
the only batch that is both fully successful (5/5) and consistently strong on uniqueness, field
depth, measurability, and trade-off articulation. It ranks run 87 third because of its verbosity
(avg 948 chars for `consequences`) and one schema failure.

**Resolution:** Both are defensible given different objectives. For the optimization loop, run 84
is the better target model because it proves the prompt *can* work with full reliability. Run 87
is the better ceiling reference for content quality. Neither framing is wrong; the synthesis should
track both.

### 2. Scope of run 85 field contamination

**insight_claude** reports 1/15 contaminated consequences in the silo plan. **insight_codex**
reports 56/78 contaminated consequences across all five plans, citing
`history/0/85_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
as the clearest case.

**Resolution:** Both are correct measurements of different scopes. insight_codex's 56/78 (72%)
figure is more representative of the overall run 85 behaviour. The silo plan happened to be a
milder case. The 72% rate confirms this is a systemic model behaviour, not a one-off.

### 3. Is `summary` a wasted-token bug?

**code_codex** labels the mandatory `summary` and optional `strategic_rationale` fields in
`DocumentDetails` as a logic error (B2): they are generated on every call but never appear in
the cleaned output (`002-10-potential_levers.json`). **code_claude** does not flag this.

**Resolution:** Confirmed from source. `save_clean` calls `lever_item_list()` which returns only
`LeverCleaned` objects. `summary` and `strategic_rationale` from `DocumentDetails` are discarded.
Three calls × ~100-word `summary` = ~300 words of mandatory generation that never improves output.
This is a real token-cost and truncation-pressure issue, especially on long plans (run 83 EOF).

---

## Top 5 Directions

### 1. Truncate 8-lever lists to 7 instead of hard-failing
- **Type**: code fix
- **Evidence**: code_claude B3/I1, code_codex B3, insight_claude §6, insight_codex N1. Confirmed
  at `identify_potential_levers.py:78–82` (`max_length=7`). Run 87 `gta_game` fails with
  "List should have at most 7 items after validation, not 8". The other two prior calls' valid
  levers are discarded completely.
- **Impact**: Converts run 87-class hard failures to partial successes with no content loss.
  In this batch: 1 plan recovered per run. In production with claude-class models (which over-generate
  more often), the rate could be higher. Because this is a code fix, it benefits all models equally.
- **Effort**: Low. Catch the `ValidationError` in the `execute()` loop, slice `.raw.levers` to 7,
  re-validate, continue. Approximately 5–8 lines of code.
- **Risk**: Minimal. The 8th lever is discarded rather than causing a full plan failure. The 7
  retained levers are valid. The downstream dedup step (`002-11`) already reduces lever counts
  further, so losing one lever per call rarely changes the final deduplicated output.

### 2. Add a negative example for `consequences`/`review_lever` field separation
- **Type**: prompt change
- **Evidence**: insight_claude H3, insight_codex H2, code_codex I6. Run 85 has 56/78 contaminated
  consequences (72%) despite the current prohibition already in the schema description at
  `identify_potential_levers.py:42–43` ("Do NOT include 'Controls ... vs.', 'Weakness:' …").
  The prohibition alone is insufficient for qwen3-class models.
- **Impact**: Eliminates the run 85-class contamination. Affects every model that confuses
  `consequences` and `review_lever` fields. Because this is a prompt change, it directly targets
  the failure site without requiring a code change.
- **Effort**: Low. Add two lines to the Prohibitions section of the system prompt, plus a
  concrete bad example.
- **Risk**: Low. Adding a negative example and explicit prohibition cannot degrade compliant models.
  It may slightly increase prompt length (~40 tokens).

### 3. Thread prior assistant turns between LLM calls
- **Type**: code change
- **Evidence**: code_claude S1, code_codex S1/I4. Confirmed at `identify_potential_levers.py:209–215`:
  `call_messages = [system_message, ChatMessage(role=USER, content=prompt_content)]` — always a
  fresh conversation. Later calls see only a name deny-list, not the actual content from prior calls.
  insight_claude notes this widens the quality gap between models; insight_codex notes it allows
  "semantically duplicated levers under different names". The project memory explicitly records
  "iteration 2, fix assistant turn serialization" as the planned next step.
- **Impact**: Reduces conceptual repetition across calls for weaker models. Stronger models already
  resist name reuse; weaker models (run 82 class) produce structurally identical levers because they
  have no context for what was previously generated. This is the highest-breadth code change for
  content quality improvement across all models.
- **Effort**: Medium. `call_messages` for calls 2 and 3 must include the prior `ChatMessage(role=ASSISTANT, …)`
  with the serialized prior response. Requires testing that structured LLM backends accept
  multi-turn chat history in `as_structured_llm` mode.
- **Risk**: Medium. Some LLM providers do not handle multi-turn structured output well. The
  assistant turn must be serialized correctly (JSON of the `DocumentDetails` model) or the model
  may treat it as user input.

### 4. Add content validators before `save_clean`
- **Type**: code change
- **Evidence**: code_claude S4/I2, code_codex B1/I1. Confirmed: `save_clean` at lines 304–306
  writes any schema-valid payload without inspecting field content. This passes run 82's one-word
  options, run 85's contaminated consequences, and run 86's one-sided strategic clauses into the
  final artifact as if they were successful outputs.
- **Impact**: Surfaces currently-silent quality failures. A sidecar `002-10-quality_warnings.json`
  file with per-lever flags would give the analysis pipeline machine-readable signals instead of
  requiring manual inspection of every output. Does not improve output directly but prevents false
  "ok" classification of poor-quality artifacts.
- **Effort**: Medium. String inspection checks (presence of "Controls " / "Weakness:" in
  `consequences`, option length < 50 chars, missing "Systemic:" label, missing quantitative
  signal) can be added to `save_clean` or a new `validate()` method on `IdentifyPotentialLevers`.
- **Risk**: Low. These are logging/warning-only checks unless coupled with a retry path. Without
  a repair loop, they surface the problem without fixing it.

### 5. Add full-sentence option requirement and measurability example to prompt
- **Type**: prompt change
- **Evidence**: insight_codex H1 (option shape), insight_claude H2 (measurability examples).
  Run 82 has 80/86 options under 50 characters (e.g. "Lean Construction Scheduling", "Material
  Recycling and Reuse"), which are labels rather than strategic approaches. Run 86 has 59/89
  consequences missing an explicit trade-off marker. Run 82 has 57/86 missing measurable systemic
  clauses.
- **Impact**: Improves run 82-class models (llama3.1, gpt-4o-mini) that treat the options field
  as a label list. Adding a positive/negative example pair for the systemic consequence clause may
  raise measurability compliance for weaker models without harming strong ones.
- **Effort**: Low. Two additions to the system prompt: (a) an explicit minimum-length / action-verb
  requirement for options; (b) a concrete Bad/Good example pair for the systemic clause.
- **Risk**: Low for strong models. Weaker models may partially comply; unlikely to degrade existing
  run 83/84/87 quality.

---

## Recommendation

**Pursue direction 1 first: truncate over-limit lever lists instead of hard-failing.**

**Why first:** It is the only change with a guaranteed, deterministic outcome — a model that
previously caused a total plan failure now produces a valid, complete output with 7 levers instead
of 8. The fix requires no prompt re-testing, no model re-evaluation, and no architectural change.
The logic change is localized to the `execute()` loop in `identify_potential_levers.py`.

**Why not directions 2–5 first:** Prompt changes (directions 2 and 5) require a new run across
all models to measure effect, and their impact is probabilistic. Content validation (direction 4)
surfaces problems without fixing them and needs a repair loop to produce quality gains. Assistant
turn threading (direction 3) is the right structural next step but has medium implementation risk
and is planned for iteration 2.

**Specific change:**

File: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

In the `execute()` loop, after `result = llm_executor.run(execute_function)` (line 230), before
accessing `result["chat_response"].raw.levers`, add a truncation guard:

```python
raw_doc = result["chat_response"].raw
if len(raw_doc.levers) > 7:
    logger.warning(
        f"Call {call_index}: model returned {len(raw_doc.levers)} levers "
        f"(max 7); truncating to 7."
    )
    raw_doc = raw_doc.model_copy(update={"levers": raw_doc.levers[:7]})
    result = {**result, "chat_response": result["chat_response"]}
    # Replace the raw attribute on the existing response object:
    result["chat_response"].raw = raw_doc
```

Alternatively, catch `ValidationError` from `llm_executor.run(execute_function)` specifically
when it matches "List should have at most", extract the raw text, slice the levers list to 7,
and re-validate. The simpler approach is to truncate at the object level before the name
accumulation at line 240, since the structured LLM backend has already parsed the JSON.

The safest implementation given the llama_index API: wrap line 240 onward in a check:

```python
levers = result["chat_response"].raw.levers
if len(levers) > 7:
    logger.warning(f"Call {call_index}: truncating {len(levers)} levers to 7")
    levers = levers[:7]
generated_lever_names.extend(lever.name for lever in levers)
responses.append(result["chat_response"].raw)
```

Note: this does not change what is stored in `responses` (the full `DocumentDetails` object),
but the first-7-only names are passed to the deny-list for subsequent calls, and the 8th lever
is excluded from `levers_raw` at line 246 because `responses` still holds the full object.
A cleaner approach replaces the `levers` field on the `raw` object before appending.

The exact form depends on whether `DocumentDetails` is immutable; since it is a `BaseModel`,
`model_copy(update={"levers": levers[:7]})` is the idiomatic Pydantic v2 truncation.

**Expected outcome:** Run 87's `gta_game` failure class is eliminated. Claude-haiku and similar
high-quality models that occasionally over-generate become fully reliable without any prompt change.

---

## Deferred Items

- **Race condition on `set_usage_metrics_path` (B1/code_claude, S3/code_codex):** Real bug but
  latent — all tested runs used `workers=1`. Needs fixing before any parallel-plan experiment.
  Fix: move `set_usage_metrics_path` inside `_file_lock` and either keep the entire execute call
  inside the lock (serialises plans) or switch `usage_metrics` to thread-local storage.

- **Mandatory `summary` tokens not used in output (B2/code_codex):** The `DocumentDetails.summary`
  field is generated on every call but discarded by `save_clean`. Marking it `Optional` with
  `default=None` would reduce per-call response size, ease truncation pressure on long plans
  (run 83 EOF), and shorten run 87's verbose outputs. Low effort, low risk.

- **Save failed raw artifacts (I3/code_claude, I5/code_codex, B4/code_codex):** Move
  `track_activity_path.unlink(missing_ok=True)` from unconditional `finally` to the success
  branch only. Write partial `responses` list to `002-9-potential_levers_raw_partial.json` in
  the `except` block. Medium effort, high auditability value for future rounds.

- **Prompt: negative example for generic weakness phrases (H1/insight_claude):** Run 82 has 76%
  generic weaknesses ("The options fail to consider the potential for X"). A prohibition with
  a named-mechanism requirement may help. Deferred because it affects only weaker models and
  requires a full re-run to measure.

- **Prompt: explicit contrast word for trade-off (H3/insight_codex):** Requiring "but", "while",
  or "however" in the systemic/strategic clause targets run 86's 59/89 missing trade-off markers.
  Simple to add, deferred as a batch with the other prompt changes.

- **Prompt: upper bounds on field length (H4/insight_codex):** Run 87 averages 948 chars per
  consequence ("mini-essays"). Adding a soft word limit ("~80 words") would preserve depth
  while reducing verbosity. Combine with the trade-off and option changes in a single prompt
  iteration.

- **Assistant turn threading (direction 3 above):** Highest-breadth content quality improvement,
  planned for iteration 2. Defer until the simpler fixes above are confirmed in a new run.

- **Annotate `002-10` with `call_count` field (C1/insight_claude, I4/code_claude):** Prevents
  automated analysis tools from flagging merged lever counts (15–21) as per-call violations.
  Minimal effort; add `"call_count": len(self.responses)` to `to_dict()`.
