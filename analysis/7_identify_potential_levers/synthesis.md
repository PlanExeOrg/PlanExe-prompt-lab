# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **Multi-call chat history contamination is the confirmed root cause of qwen3-30b's 100% field-boundary failure.** Every agent identifies lines 234–242 of `identify_potential_levers.py` (appending prior assistant JSON to the history) combined with calls 2/3 having no re-grounding in the original plan (lines 196–203) as the mechanism. This maps to B1 (code_claude), B1 (code_codex), N3 (insight_claude), and the "severe field-boundary failure" in insight_codex.

2. **The gpt-oss-20b trailing-character failure is a side effect of `max_length=5` enforcement.** Before that schema constraint, 6-lever responses were silently accepted or merged as 16-lever artifacts. With it enforced, the 6th lever fragment causes a hard Pydantic validation error that fails the entire plan. This is B2 (code_claude), S2 (code_codex), N2 (insight_claude), and the "JSON trailing-character failures" in insight_codex.

3. **The `max_length=5` / `min_length=5` schema enforcement is working correctly.** Zero lever-count overflow violations in batch 7 vs. 1 in batch 6. All four agents treat this as confirmed progress.

4. **nemotron is operationally dead.** Six consecutive 0/5 batches with no parseable JSON output. No agent proposes any prompt or code fix that would help it.

5. **llama3.1 is structurally reliable but substantively shallow.** Zero measurable indicators in Systemic clauses, generic "Silo-X Strategy" naming, options ~49 chars vs. haiku's ~240 chars. All agents agree prompt fixes are unlikely to improve it — it lacks the output capacity.

6. **The schema validates structure but not field content.** Only `options` has a real field validator. `consequences` and `review_lever` accept any string, so contaminated content passes type validation and is written to the final artifact unchanged. Both code review agents flag this explicitly.

---

## Cross-Agent Disagreements

### Disagreement 1: Is haiku (run 59) the best result or an overcorrection?

**insight_claude** ranks run 59 #1 ("deepest content, rich measurable indicators") with average consequence length ~591 chars.

**insight_codex** calls run 59 "an overcorrection": 30/75 chain-format violations, 15/75 review-template misses, 1 placeholder leak (`[specific pathway]`), and one prohibited generic option (`Optimize heavily for PS5/Series X hardware...`). It ranks run 58 (gpt-4o-mini) as the best candidate.

**Verdict after reading source:** Both are partially right. insight_claude measured substance (quantitative indicators, option depth); insight_codex measured format compliance. The data confirms both: run 59's `consequences` average 1127 chars (vs. the 60–120 word target in the field description), review fields average 447 chars (vs. the two-sentence format), and the placeholder appears in the sovereign_identity output. insight_codex is correct that format discipline is weaker in run 59. However, the underlying intelligence is genuine — the content itself is richer. The correct interpretation is that run 59 demonstrates what the model can produce when given latitude, not that it is the best operational candidate.

### Disagreement 2: Is code_codex's "B2" (loosest assistant representation) a distinct bug from B1?

**code_claude** treats the contamination issue as a single root cause (B1): prior assistant JSON is appended to history.

**code_codex** splits this into two bugs: B1 (prior assistant JSON in history at all) and B2 (preferring `message.content` over `raw.model_dump_json()` when it exists, which may carry prose/noise the structured parser had already absorbed).

**Verdict after reading source lines 234–242:** Both bugs exist. `message.content` is tried first (`result["chat_response"].message.content or result["chat_response"].raw.model_dump_json()`). If the model responded with a prose wrapper around the JSON, `message.content` includes that prose while `raw.model_dump_json()` is the clean parsed output. code_codex is correct that this is an independent issue — but it is secondary to B1. Fixing B1 (resetting the message list) makes B2 irrelevant for the contamination problem: if calls 2/3 start fresh, there is no carry-forward at all.

### Disagreement 3: Should "radical option must include emerging tech/business model" be a hard requirement?

**insight_codex** treats radical-option misses (52/75 in baseline, 63/75 in run 54, 52/75 in run 58) as a significant failure.

**insight_claude** does not flag the radical-option clause as a major concern and focuses instead on measurable indicators and contamination.

**Verdict:** insight_codex is flagging a real pattern, but the heuristic ("must include emerging tech/business model") is too strict for some domains. Both the baseline and gpt-4o-mini (the operationally strongest model) fail it. This is a useful signal for prompt refinement but not an actionable bug.

---

## Top 5 Directions

### 1. Reset Message Context for Calls 2 and 3

- **Type**: code fix
- **Evidence**: All four agents flag this. code_claude B1, code_codex B1, insight_claude C2/N3, insight_codex N/Comparison. Root cause of qwen3-30b 100% contamination for three consecutive batches (runs 43, 50, 57 = ~60 levers per batch fully corrupted). Identified as "Direction 2" in synthesis/6 but not yet implemented.
- **Impact**: Eliminates qwen3-30b consequence contamination (100% → ~0%). Re-grounding calls 2/3 in the original plan documents also likely reduces generic naming in those calls (S3, code_codex) — improving llama3.1 and gpt-4o-mini lever specificity for calls 2 and 3. Restores qwen3-30b to a usable candidate.
- **Effort**: Low. The fix is a 5-line change: instead of appending to `chat_message_list`, construct a fresh list `[SYSTEM, USER(user_prompt + "\n\nDo NOT reuse any of these already-generated lever names: [...]")]` for `call_index > 1`. The original `chat_message_list` is still used for call 1 unchanged.
- **Risk**: The name-exclusion blacklist is preserved in the new user turn, so diversity pressure is maintained. The risk is that the model loses awareness of the structural choices made in prior calls — but that is the desired effect. The one edge case is if a model performs better on calls 2/3 because it sees prior well-formed examples; this is unlikely for qwen3 (which is actively harmed by it) and unconfirmed for others.

---

### 2. Truncation Recovery for Trailing-Character Extraction Failures

- **Type**: code fix
- **Evidence**: code_claude B2/I2, code_codex S2/I4, insight_claude N2/C1, insight_codex N ("run 55 two plans failed JSON validation"). gpt-oss-20b went from 5/5 (run 48) to 3/5 (run 55) after `max_length=5` enforcement. The model produces valid JSON for 5 levers followed by a 6th lever fragment; the current code raises `LLMChatError` and fails the entire plan with no recovery.
- **Impact**: Restores gpt-oss-20b from 60% to ~100% success rate. May also help other models that occasionally over-generate under strict count enforcement. Does not affect the 4 already-100%-success models.
- **Effort**: Medium. Requires catching the specific Pydantic `json_invalid: trailing characters` error variant, extracting the raw response string, finding the last `}` that closes a valid top-level JSON object, slicing there, and re-running validation. This is careful string surgery with some failure modes (e.g., if the model generates multiple malformed objects).
- **Risk**: The truncation heuristic (find the last closing brace of the outermost object) may fail for deeply nested structures or if the model produces multiple top-level objects. A safer variant is to attempt JSON parsing progressively from the end, which is more robust but more complex.

---

### 3. Post-Generation Semantic Field Validator

- **Type**: code fix
- **Evidence**: code_claude I3, code_codex B3/I3, insight_codex ("field-boundary failure" / "most instructive failure mode"). qwen3-30b's contamination survives into `002-10-potential_levers.json` because there is no content-level check after JSON structure parsing. The schema only validates types and counts.
- **Impact**: Catches contamination that any prompt fix fails to prevent. Provides defense-in-depth: even if B1 fix reduces qwen3 contamination, some future model or edge case may reintroduce it. The validator would at minimum log a warning, and optionally strip the contaminated suffix before writing the final artifact.
- **Effort**: Low for warning-only mode (scan `consequences` for `"Controls "` and `"Weakness:"` after the merge at lines 249–264). Medium for stricter enforcement (reject the lever and trigger regeneration). The warning-only version is a 10-line addition.
- **Risk**: False positives if a valid strategic consequence legitimately contains the word "Controls" or "Weakness" (e.g., a lever about "Controls Engineering Strategy"). The check should require both markers together in a specific pattern (`"Controls X vs. Y."`) to reduce false positives.

---

### 4. Prompt: Add One Gold Example + Anti-Example for `consequences` and `review_lever`

- **Type**: prompt change
- **Evidence**: insight_codex H1, insight_claude (implicit in quality analysis). Runs 55 and 56 often contain the right substance but miss exact `→` separators; run 59 paraphrases `review_lever` instead of using the strict `Controls A vs. B.` form. Chain-format misses: 16/75 (run 56), 30/75 (run 59). Review-template misses: 15/75 (run 59).
- **Impact**: Reduces format violations in the 56/59 family of models (stronger models that have depth but drift on exact separators). Would not help nemotron or llama3.1 substantially. Best candidates to benefit: gpt-5-nano, haiku.
- **Effort**: Low-medium. Requires writing one tight example consequence (`Immediate: [X] → Systemic: [Y, with % delta] → Strategic: [Z, naming trade-off]`) and one anti-example (consequence that contains "Controls" or uses semicolons instead of `→`). Add to the system prompt in the "Validation Protocols" section.
- **Risk**: Examples can anchor model output in unhelpful ways — models may echo the domain of the example rather than the actual plan. Use a clearly fictional or highly abstract example domain to avoid anchoring.

---

### 5. Make `summary` Optional or Remove from Response Schema

- **Type**: code fix
- **Evidence**: code_codex S1/I5, code_claude S2. `summary` is required (`summary: str`, no default) in `DocumentDetails` but is only stored in the raw file (`002-9-potential_levers_raw.json`) and discarded by `save_clean()`. It adds mandatory token generation for every one of 3 LLM calls (×5 plans ×N runs), increases parse-failure surface (a model omitting summary now fails the plan), and explains why batch 6 saw 14 null summaries from llama3.1 and why run 55 (gpt-oss-20b) may be generating summaries plus 6th lever fragments.
- **Impact**: Reduces failure surface for weaker models. Reduces latency for all models (one fewer required paragraph per call). Does not affect the quality of the final `002-10-potential_levers.json` artifact at all since `save_clean()` does not write summary.
- **Effort**: Very low. Change `summary: str` to `summary: Optional[str] = None` (or remove the field entirely from `DocumentDetails` if it has no downstream use). Requires confirming the field has no other consumers.
- **Risk**: If summary was added deliberately to force the model to self-evaluate (improving lever quality indirectly through chain-of-thought), removing it may reduce quality on stronger models. Inspection of run 59 (where summaries are well-formed) vs. run 54 (where they are shallow) does not suggest summaries are significantly improving lever quality. The risk is low.

---

## Recommendation

**Implement Direction 1: Reset the message context for calls 2 and 3.**

**Why first:** This is the single change that addresses the most severe, most persistent, most thoroughly confirmed issue in the dataset. qwen3-30b has produced 100% contaminated consequences for three consecutive batches (runs 43, 50, 57) — approximately 180 corrupted levers in total. The root cause is confirmed in the source code (lines 196–244 of `identify_potential_levers.py`): calls 2 and 3 receive prior assistant JSON as dominant context with no re-grounding in the actual plan. It was already identified in synthesis/6 as the highest-priority direction and has not been implemented.

**What to change:**

File: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

Lines 195–211 (the loop setup) and lines 234–242 (the assistant message append).

Current logic (simplified):
```python
chat_message_list = [SYSTEM]
for call_index in range(1, 4):
    if call_index == 1:
        content = user_prompt
    else:
        content = f"Generate 5 MORE levers ... Do NOT reuse: [{names_list}]"
    chat_message_list.append(USER(content))
    result = llm_executor.run(execute_function)          # execute_function reads chat_message_list
    chat_message_list.append(ASSISTANT(result.content))  # ← contamination added here
    generated_lever_names.extend(...)
```

Proposed fix: build a fresh message list per call, carrying only the name exclusion forward:
```python
for call_index in range(1, 4):
    names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
    if call_index == 1:
        call_messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]
    else:
        exclusion_note = (
            f"Generate 5 MORE levers with completely different names. "
            f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
            f"{user_prompt}"
        )
        call_messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=exclusion_note),
        ]

    def execute_function(llm: LLM) -> dict:
        sllm = llm.as_structured_llm(DocumentDetails)
        chat_response = sllm.chat(call_messages)   # ← fresh list each call
        ...

    result = llm_executor.run(execute_function)
    generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
    responses.append(result["chat_response"].raw)
```

Key properties of this fix:
- No prior assistant JSON is ever in the context for calls 2/3.
- The original plan (`user_prompt`) is included every call, so domain grounding is maintained.
- The name exclusion list is still provided, preserving diversity pressure.
- The closure over `call_messages` (a new local variable each iteration) also resolves the S1 suspect pattern (code_claude) where `execute_function` closed over the mutating `chat_message_list`.
- `chat_message_list` can be removed from the outer scope entirely.

**Expected outcome:** qwen3-30b contamination rate drops from 100% to near 0%. Calls 2/3 for all models will be better domain-grounded, likely improving specificity for llama3.1 and gpt-4o-mini in those calls. Batch success rate should recover to ≥85.7% (the batch 6 level), assuming no new regressions.

---

## Deferred Items

**D1 — Trailing-character recovery (Direction 2 above, code_claude B2/I2).** Implement after B1 fix is confirmed working. Restores gpt-oss-20b to ~100% success. Worth doing but lower urgency than B1.

**D2 — Post-generation semantic field validator (Direction 3 above, code_claude I3).** Add warning-only version (10 lines) as a monitoring layer after B1 fix. If contamination recurs in a new model, the logs will catch it immediately.

**D3 — Prompt example addition (Direction 4 above, codex H1).** Deferred until after code fix batch is evaluated. Format compliance may naturally improve once calls 2/3 are re-grounded in plan context. If chain-format violations persist in run 56-family models after B1, add one gold example to the system prompt.

**D4 — Make `summary` optional (Direction 5 above, codex S1/I5).** Low-risk cleanup. Deferred until core contamination fix is validated. Confirm no downstream consumer of `summary` before removing.

**D5 — nemotron model skip mechanism (insight_claude Q3).** Six consecutive 0/5 batches. Propose adding it to a known-bad model blocklist in the runner to avoid wasting compute. This is an operational decision, not a fix.

**D6 — Thread-safety fix for `set_usage_metrics_path` (code_claude B3, code_codex S4).** Real concurrency defect in `runner.py:106, 140`. Wrapping both calls in `_file_lock` is a one-line fix per call site. Deferred because it does not affect lever quality, only metric accounting accuracy at `workers > 1`.

**D7 — Use `raw.model_dump_json()` instead of `message.content` for carry-forward (code_codex B2/I2).** If any carry-forward is kept in a future design (e.g., a multi-turn approach for specific models), use the canonical normalized JSON, not the raw assistant text. Not applicable if B1 fix eliminates carry-forward entirely.
