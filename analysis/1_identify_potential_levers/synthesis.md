# Synthesis

## Cross-Agent Agreement

All four analysis files (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **Bare "more" prompt causes cross-call thematic redundancy.** Every successful model repeats governance, resource, and information themes across the three LLM calls because the second and third turns carry no record of what was already generated. This is confirmed in source lines 155–158.

2. **The concrete metric example in the system prompt causes template leakage.** `"Systemic: 25% faster scaling through..."` at line 95 of `identify_potential_levers.py` is the phrase gpt-5-nano copied in 11 of 15 levers (73%). All agents identify this as a prompt-construction defect, not a model quirk.

3. **No per-call or post-merge lever count validation.** Lines 203–206 blindly flatten all responses with `levers_raw.extend(response.levers)` and no count check. This is confirmed to produce 20-lever outputs (llama3.1) and a malformed 16-item file (gpt-5-nano, gta_game plan).

4. **Run 09 preflight failure wastes all five plans.** The model name validation happens per-plan inside `run_single_plan()` rather than once at run start. One missing alias produces five identical failures.

5. **claude-haiku (run 12) produces the best quality output.** Confirmed across both insight files: zero duplicates, plan-specific levers, rich consequences.

6. **gpt-4o-mini (run 15) and llama3.1 (run 16) produce the weakest output.** Both have duplicate lever names, generic content, and in llama3.1's case prefix leakage and bracket placeholders.

---

## Cross-Agent Disagreements

### Bug numbering collision: code_claude B1 vs code_codex B1

These are different bugs assigned the same label:

- **code_claude B1** (line 193–198): The assistant's `ChatMessage.content` is set to `result["chat_response"].raw.model_dump()` — a Python `dict`. When LlamaIndex serializes this for the next API call, it produces Python repr syntax (`{'strategic_rationale': ...}`) not JSON. Turns 2 and 3 receive malformed continuation context.
- **code_codex B1** (line 93–96): The prompt contains the literal metric phrase that leaks into weaker model outputs.

**Verdict**: Both are real. The naming collision is an artifact of independent labeling. In this synthesis, these are called **BUG-A** (dict content) and **BUG-B** (metric exemplar) to avoid confusion.

### Is BUG-A (dict content) high-impact?

code_claude rates it High; code_codex rates it as a suspect pattern (S1). Reading the source confirms the dict is passed at line 196:

```python
content=result["chat_response"].raw.model_dump(),
```

`model_dump()` returns a Python dict. LlamaIndex's `ChatMessage` has a `content: Any` field, but downstream serialization to the API expects a string. The actual JSON string the model produced is available at `result["chat_response"].message.content`. The dict-vs-string mismatch is real and affects every multi-turn run.

code_codex (S1) is right to flag provider-dependent coercion as a risk, but understates the severity. code_claude (B1) is correct that this is a confirmed code bug.

### Is run 12 (claude-haiku) too verbose?

insight_codex identifies verbosity (consequence avg 657 chars vs baseline 279) as a negative. insight_claude considers it a strength ("plan-specific, high-depth"). Both are correct from different perspectives: for ideation richness it is excellent; for token efficiency and truncation risk it is a liability. This is not a real disagreement — it is a trade-off the prompt currently does not constrain.

### Runner.py race condition

code_claude B2 identifies a race on `set_usage_metrics_path` when `workers > 1`. Reading lines 106–143 confirms: `set_usage_metrics_path` is called before the lock (line 106) and `IdentifyPotentialLevers.execute()` runs without the lock (line 114). The `finally` block at line 140 cleans up afterward, which partially mitigates writes to the wrong path — but Thread B can still overwrite Thread A's path during execution. The bug is real. code_codex does not flag it, so this is an agreement gap, not a true disagreement. The bug is confirmed.

---

## Top 5 Directions

### 1. Fix assistant turn: use raw string content instead of model_dump() dict

- **Type**: code fix
- **Evidence**: code_claude B1 (High). Confirmed in `identify_potential_levers.py:196`. `result["chat_response"].raw.model_dump()` produces a Python dict; `result["chat_response"].message.content` is the actual JSON string the model emitted.
- **Impact**: Affects every multi-turn run, every model, every plan. Turns 2 and 3 currently receive malformed continuation context (Python repr instead of JSON). Structural compliance on turn 2 and 3 may improve for all models, especially weaker ones. This is the only code bug that corrupts the conversation history on 100% of runs.
- **Effort**: Low — one line change in `identify_potential_levers.py:196`.
- **Risk**: Very low. The fix makes the assistant history match what the model actually saw. No behavior change when the model's continuation is correct; only improvement when it is degraded by the dict repr.

---

### 2. Make "more" turns stateful: include already-generated lever names

- **Type**: code change (+ implicit prompt change in continuation messages)
- **Evidence**: code_claude S1/I1, code_codex B3/I3, insight_claude N8/H3, insight_codex H1. Confirmed in `identify_potential_levers.py:155–158`. `user_prompt_list = [user_prompt, "more", "more"]` — no feedback to the model about covered topics.
- **Impact**: Reduces cross-call thematic redundancy for all successful models. gpt-4o-mini has 3.8 average duplicate names per file; llama3.1 has 1.2; gpt-oss-20b has 0.8. All would benefit. This is the single highest-leverage change for output quality.
- **Effort**: Low-medium. After each LLM call, collect lever names from `responses[-1].levers` and inject into the next user message: `f"Generate 5 more levers. Already covered: {names}. Do not repeat these topics."`. Requires modifying the loop at lines 163–200.
- **Risk**: Low. The only risk is that the message becomes slightly longer, but it stays well within token limits for any model that successfully completes three turns.

---

### 3. Replace concrete metric exemplar with a structural placeholder

- **Type**: prompt change
- **Evidence**: code_claude S2/I6, code_codex B1/I1, insight_claude N3/H1. Confirmed in `identify_potential_levers.py:95`: `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"`. gpt-5-nano copies this phrase in 11/15 levers (73% leakage rate). claude-haiku copies it 0 times; weaker models are most affected.
- **Impact**: Eliminates the template leakage vector for gpt-5-nano class models. No negative effect on stronger models (they ignore the example already). Fixes a structural defect in the prompt that is shipped to all users, not just in testing.
- **Effort**: Low — single line replacement in the system prompt constant at line 95 of `identify_potential_levers.py`.
- **Risk**: Very low. The changed line still communicates the same structural requirement; it just removes the concrete text that acts as a fill-in-the-blank template.

---

### 4. Add per-call and post-merge lever count validation

- **Type**: code fix
- **Evidence**: code_claude B3/I2/I3, code_codex B2/I2. Confirmed: `levers_raw.extend(response.levers)` at lines 203–206 performs no count check. Observed: llama3.1 produces 20 levers, gpt-5-nano produces 16 levers on one plan.
- **Impact**: Makes contract violations explicit failures rather than silently malformed "successful" outputs. The schema field `list[Lever]` has no min/max constraint, so any count passes today. With validation, downstream steps receive either correct 15-lever outputs or a retryable error.
- **Effort**: Low — two assertions: one inside the loop (assert `len(response.levers) == 5` per call) and one after merge (assert `len(levers_raw) == 15`). No retry logic required initially; surfacing the error is the first step.
- **Risk**: Medium. Models that currently produce wrong counts will now fail explicitly. This may increase the visible error rate on weaker models (llama3.1, gpt-5-nano on edge cases), which is the correct outcome but requires callers to handle it.

---

### 5. Preflight model availability check before plan loop

- **Type**: code fix
- **Evidence**: code_claude I4, code_codex B4/I4, insight_claude N1. Confirmed: `LLMModelFromName.from_names(model_names)` is called inside `run_single_plan()` at runner.py line 93, not once at run start. Run 09 (stepfun) failed all five plans identically because of a single missing model alias.
- **Impact**: Converts five-plan wasted run into one immediate startup error. Saves time and prevents misleading "all plans failed" results when the cause is a configuration typo.
- **Effort**: Low-medium. Move or duplicate the model resolution logic to run before the plan loop in `runner.py`, and raise an error if any model alias is not found in the config.
- **Risk**: Low. The change only moves when the error fires, not whether it fires.

---

## Recommendation

**Pursue Direction 1 first: fix the assistant turn content from `model_dump()` dict to the raw string.**

**File:** `identify_potential_levers.py`
**Line:** 196

**Current code:**
```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].raw.model_dump(),
    )
)
```

**Fixed code:**
```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].message.content,
    )
)
```

**Why first:** This is the only bug that corrupts the conversation state on 100% of runs, 100% of models, for every turn after the first. The current code passes a Python dict as the assistant's message content. When LlamaIndex serializes `ChatMessage` for the next API call, a dict in `content` is coerced via Python repr (`{'strategic_rationale': 'some text', 'levers': [...]}`) rather than being emitted as valid JSON. The model on turn 2 therefore sees its own prior output in an unparseable format. This degrades structural compliance on turns 2 and 3 for all models and is the likely partial cause of the label drift observed in runs 14/15 (missing `Immediate:`/`Systemic:`/`Strategic:` chain labels) and the option format violations in run 16.

The fix is `result["chat_response"].message.content`, which is the verbatim string the model emitted (already a valid JSON document). This is a one-line change with no side effects, and it makes the continuation context structurally correct for the first time.

After this fix, Direction 2 (stateful "more" turns) should be implemented next, as cross-call thematic redundancy is the dominant quality problem visible across all successful runs.

---

## Deferred Items

- **Direction 3 (metric exemplar → structural placeholder)**: Small, safe prompt change worth doing in the same batch as Direction 2 but not blocking anything.

- **Direction 5 (preflight model check)**: Operational improvement. Worth doing before the next large model comparison run, but does not affect output quality.

- **Runner.py race condition on `set_usage_metrics_path`** (code_claude B2): Only affects runs with `workers > 1`. The `finally` block partially mitigates it. Fix by moving `set_usage_metrics_path` inside the `_file_lock` block, and also acquiring the lock during `IdentifyPotentialLevers.execute()` if usage metric correctness matters. Low priority since the prompt-lab runs typically use a single worker.

- **Non-atomic history counter** (code_claude S4): Latent race condition in `runner.py` when two processes start simultaneously. Not observed in runs 09–16. Fix with a file-based lock or atomic directory creation if concurrent runner invocations become common.

- **Structured output fallback parsing** (code_claude I7, code_codex I5): If the model returns a `{"levers": [...]}` wrapper or a truncated response, a secondary parse attempt could recover partial results. Worth implementing once the higher-priority fixes are stable.

- **Per-model length guidance** (insight_codex H2, code_codex I7): Run 12 (claude-haiku) averages 657 chars per consequence vs baseline 279. Adding a length target like "Consequences: ~30 words" to the prompt would reduce token cost without sacrificing structure. The current `Lever.consequences` field description already says "30 words" but the system prompt does not enforce it. Enforcing it consistently would help.

- **Global uniqueness instruction across all three turns** (insight_codex H1): Adding an explicit cross-turn uniqueness instruction to the system prompt (`"Across all three responses, the 15 lever names must be distinct"`) is complementary to Direction 2 but less precise than dynamically feeding already-covered names.

- **Post-merge deduplication** (code_claude I5, insight_claude C2): A defensive deduplication or warning pass after merge is useful as a safety net even after Direction 2 is implemented. Not first priority because Direction 2 attacks the root cause.
