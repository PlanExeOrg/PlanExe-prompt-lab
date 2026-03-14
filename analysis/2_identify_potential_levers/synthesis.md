# Synthesis

## Cross-Agent Agreement

All four analysis files (insight_claude, insight_codex, code_claude, code_codex) converge on
the same core findings:

1. **Cross-call lever duplication is the dominant quality failure.** Every run that produced
   output generated at most 5 unique lever names out of 15 (33% uniqueness). The 3-call runner
   design intends diversity, but something prevents the model from seeing its prior output.

2. **"Material Adaptation Strategy" template leakage** affects weak models (runs 17, 18). All
   agents agree the cause is the concrete example name in the prompt (`identify_potential_levers.py:104`).

3. **Hallucinated percentage figures** (25%, 15%, 20%, etc.) in consequences affect runs 20, 21,
   and 22. All agents agree the cause is the `"Systemic: 25% faster scaling through..."` example
   in the prompt (`identify_potential_levers.py:95`).

4. **High failure rate for weak models** (runs 17 and 19: 4/5 plans failed each). All agents
   identify the same failure modes: truncated JSON (EOF) and conversational/non-JSON replies.

5. **"more" follow-up prompts are underspecified.** All agents flag that the two continuation
   turns (`identify_potential_levers.py:155-158`) provide no anti-repetition constraint.

---

## Cross-Agent Disagreements

### Disagreement 1: Root cause of cross-call duplication

**code_claude** identifies a concrete code bug: `message.content` is `None` for
function-calling-based models (OpenAI, Anthropic) when using `as_structured_llm`. The
structured output is returned via `raw`, not via the text `content` field. The assistant turn
appended to `chat_message_list` at `identify_potential_levers.py:196` therefore carries
`content=None`, making prior responses completely invisible to subsequent calls.

**code_codex** labels the "more" prompt underspecification as the primary bug (their B2),
attributing duplication to the absence of a novelty directive rather than serialization failure.

**Verdict: code_claude is correct.** Verification of the source code at line 196 confirms
`content=result["chat_response"].message.content`. For OpenAI and Anthropic models using
function-calling protocols, this field is `None` or empty — the structured payload is in
`result["chat_response"].raw`. This means the assistant history injected into calls 2 and 3
is literally blank for these model families, which explains why even strong models (haiku,
gpt-5-nano) show 33% uniqueness: they generate from scratch each time. code_codex's "more"
prompt issue is real but secondary — it is the second layer of the problem after the
serialization fix.

### Disagreement 2: Run 22 (gpt-4o-mini) quality rank

**insight_codex** rates run 22 as Tier A (best diversity: 15/15 unique names per file, zero
template leakage). **insight_claude** rates it #4 (adequate), citing generic/irrelevant options
like blockchain suggestions that don't fit the plan context.

**Verdict: Both are partially correct.** Run 22 is the structural diversity champion but has
content quality issues (generic radical options). The right framing is that run 22 proves
15-unique-name output is achievable from the same prompt, but run 23 (haiku) sets the ceiling
for content specificity.

### Disagreement 3: Whether the optimizer is scoring the right artifact

**code_codex** uniquely raises that `002-10-potential_levers.json` is a pre-dedup intermediate
file — the pipeline's own docstring notes duplicates are expected and handled downstream by
`deduplicate_levers.py`. If the analysis is scoring this pre-dedup stage, some of the observed
"failures" (repeated names) may be expected behavior.

**Verdict: Valid concern, but secondary.** Fixing B1 (serialization) and using novelty-aware
follow-ups would make the pre-dedup artifact genuinely diverse, which is the right goal
regardless of downstream dedup. However, code_codex's I6 recommendation (score post-dedup too)
is worth tracking.

---

## Top 5 Directions

### 1. Fix assistant turn serialization (`message.content` is None)
- **Type**: code fix
- **Evidence**: code_claude B1 (primary); confirmed by reading `identify_potential_levers.py:196`.
  All 6 producing runs show exactly 33% name uniqueness. Byte-for-byte identical responses within
  a single run (runs 18, 22) can only occur if the model has no memory of its own output.
  Project memory also notes "Next: iteration 2, fix assistant turn serialization."
- **Impact**: Directly fixes the root cause of cross-call duplication for all function-calling
  models (OpenAI, Anthropic). Expected uniqueness increase from 33% to 70–100% for capable
  models. Affects all 7 runs except ollama-llama3.1 (which may use text completion, not
  function-calling).
- **Effort**: Low. One-line change at `identify_potential_levers.py:196`.
- **Risk**: Low. The fallback form `content or raw.model_dump_json()` is safe: for models that
  already return content as text (e.g., llama3.1), the original path is preserved; only None
  cases fall through to the serialized raw object.

### 2. Make follow-up prompts novelty-aware (replace bare "more")
- **Type**: code fix + prompt change
- **Evidence**: code_claude S1, code_codex B2, insight_claude C1, insight_codex I2. All four
  files flag this. Even after fixing B1 (model can now see prior output), a bare "more" can
  be interpreted as "give me more of the same." Injecting the already-generated lever names
  explicitly removes ambiguity.
- **Impact**: Second layer of diversity enforcement. After B1 fix, this should push cross-call
  uniqueness from the 70% range toward 90–100% for capable models. Affects all models.
- **Effort**: Low-medium. Requires extracting lever names after each call and building a dynamic
  follow-up string at `identify_potential_levers.py:155-170`.
- **Risk**: Low. Worst case: model ignores the exclusion list and still repeats names — same
  outcome as current behavior.

### 3. Remove concrete exemplar strings from the system prompt
- **Type**: prompt change
- **Evidence**: code_claude S2 + S3, code_codex B1 (their numbering), insight_claude H1 + H3,
  insight_codex I1. Strong consensus across all files. Two separate exemplar strings cause two
  separate failure modes.
  - `"Material Adaptation Strategy"` at `identify_potential_levers.py:104` → template leakage
    in runs 17 and 18 (12 copies in run 18 alone).
  - `"Systemic: 25% faster scaling through..."` at `identify_potential_levers.py:95` →
    hallucinated percentages in runs 20, 21, 22.
- **Impact**: Eliminates template leakage for weak models; replaces hallucinated figures with
  causal mechanism descriptions for mid-tier models. Affects 5 of 7 runs.
- **Effort**: Low. Edit two string literals in the system prompt constant.
- **Risk**: Low. Strong models (haiku) already ignore these examples; weaker models are the
  ones that copy them.

### 4. Add explicit JSON-only output instruction
- **Type**: prompt change
- **Evidence**: code_claude S4, code_codex (implied by B4), insight_claude H4. Run 19 failed 4/5
  plans by returning a conversational clarification question instead of JSON. The current prompt
  has no explicit "respond only with JSON" directive.
- **Impact**: Converts some Tier D failures (runs 17, 19 style) into usable outputs. Narrow
  scope — only affects models that produce dialogue fallbacks, not those with EOF truncation.
- **Effort**: Low. Add one or two sentences to the top of the system prompt.
- **Risk**: Very low. JSON-only instructions are standard practice and don't harm compliant models.

### 5. Enforce lever count via pydantic constraints and post-merge validation
- **Type**: code fix
- **Evidence**: code_claude B3 + I5 + I6, code_codex B3 + I3. Run 18 produced 16 levers; run 23
  produced 19 levers. These are saved as `ok` artifacts despite violating the "exactly 5 per
  call / 15 total" contract. Pydantic v2 supports `min_length=5, max_length=5` on list fields.
- **Impact**: Prevents malformed artifacts from propagating downstream; makes overproduction
  visible (currently silent). Affects only edge cases (2 of 7 runs had overproduction), but
  correctness matters for any consumer expecting exactly 15 levers.
- **Effort**: Low. Add `min_length=5, max_length=5` to `DocumentDetails.levers` Field and a
  post-merge count warning in `IdentifyPotentialLevers.execute()`.
- **Risk**: Low. A `ValidationError` on overproduction is better than silently writing an
  invalid artifact.

---

## Recommendation

**Fix B1: assistant turn serialization. This should be done first.**

**File:** `identify_potential_levers.py`, line 196.

**Current code:**
```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].message.content,
    )
)
```

**Fix:**
```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=(
            result["chat_response"].message.content
            or result["chat_response"].raw.model_dump_json()
        ),
    )
)
```

**Why first:**

This is the confirmed root cause of the dominant failure mode. The 33% unique-name rate seen
in all 6 producing runs is not a prompt problem or a model capability problem — it is a data
plumbing problem: call 2 and call 3 receive a `None` assistant turn and regenerate from
scratch. The fix is a single expression change that is safe for all model families (text-only
models fall through to `raw.model_dump_json()` only if `content` is falsy, which for llama3.1
it will not be).

This is also already identified as the planned next step in the project memory
("iteration 2, fix assistant turn serialization").

After this fix, the follow-up "more" improvement (Direction 2) should be applied in the same
iteration to fully close the diversity gap: once the model can see its prior output, changing
"more" to "Generate 5 MORE levers with completely different names from: [list]" ensures the
model acts on that information.

---

## Deferred Items

- **Exemplar string removal (Direction 3)** — High value, easy to do. Should be bundled with the
  B1 fix in the same PR or as the immediate follow-up.

- **Explicit JSON-only instruction (Direction 4)** — Low effort; add to the same prompt edit as
  Direction 3.

- **Pydantic lever count enforcement (Direction 5)** — Defensive hardening; do after the
  diversity fixes so overproduction behavior is understood before adding a hard gate.

- **code_claude B2 / runner.py thread safety** — `set_usage_metrics_path` is called outside the
  lock at `runner.py:106` and `runner.py:140`. This corrupts usage metrics in parallel runs but
  does not affect lever quality. Fix separately as a housekeeping item.

- **insight_codex H1 (literal format self-check)** — Adding a prompt directive to emit the exact
  `Immediate:` / `Controls ... vs. ...` tokens is lower priority than diversity. The format
  compliance violations are cosmetic compared to duplicate lever names.

- **code_codex S2 (score post-dedup artifact)** — Worth doing to get a cleaner quality signal
  from the prompt optimizer, but not urgent until the diversity fixes land.

- **code_codex I4 / B4 (validation retry hooks in LLMExecutor)** — A good reliability
  improvement for weak models, but requires deeper changes to the executor call path. Defer
  until the prompt and serialization fixes are validated.

- **code_codex I5 (compress continuation context)** — The context-growth pattern may be
  contributing to haiku's timeout on hong_kong_game. After B1 is fixed and the full assistant
  payload is being serialized into each continuation, monitor whether timeouts increase. If they
  do, compress to lever-name summaries only.
