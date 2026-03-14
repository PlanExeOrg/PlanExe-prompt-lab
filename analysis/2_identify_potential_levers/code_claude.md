# Code Review (claude)

## Bugs Found

### B1 — Assistant turn serialization may produce `None` content (high severity)

**File:** `identify_potential_levers.py:196`

```python
chat_message_list.append(
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=result["chat_response"].message.content,
    )
)
```

When `llm.as_structured_llm(DocumentDetails)` is used, the underlying LLM may use
function-calling or tool-use protocols (especially for OpenAI-compatible and Anthropic
models). In those protocols the model's structured output is delivered via a tool/function
call, not the message's text `content` field. `message.content` is therefore often `None`
or an empty string.

Consequence: the assistant turn appended to `chat_message_list` for calls 2 and 3 has
`content=None`. The model never sees what it generated in prior calls. For call 2 and 3 the
effective conversation becomes:

```
System: <instructions>
User:   <plan content>
Asst:   None          ← previous levers invisible
User:   "more"
Asst:   None          ← previous levers invisible
User:   "more"
```

The model has no memory of what it produced, which is the direct root cause of the
cross-call lever duplication problem (all runs: 33% unique name rate, byte-for-byte
identical responses).

A safe fix is to serialize the structured response explicitly:

```python
# Option A: serialize parsed object back to JSON
assistant_content = result["chat_response"].raw.model_dump_json()
# Option B: fall back to JSON if content is None/empty
assistant_content = (
    result["chat_response"].message.content
    or result["chat_response"].raw.model_dump_json()
)
```

---

### B2 — `set_usage_metrics_path` called outside the thread lock (medium severity)

**File:** `runner.py:106` (outside lock), `runner.py:108-109` (inside lock)

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # line 106 — no lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)                  # line 108-109
```

`set_usage_metrics_path` mutates global state. When `workers > 1` (parallel plan
execution), two threads can overwrite each other's metric path, so usage metrics from plan
A are written to plan B's file and vice versa. The `finally` block also calls
`set_usage_metrics_path(None)` outside the lock (`runner.py:140`), racing with the next
thread's setup call.

This does not affect lever quality, but it corrupts usage metric files and may produce
misleading cost/token counts.

---

### B3 — Lever count not validated; merged file can exceed 15 levers (low severity)

**File:** `identify_potential_levers.py:204-206`

```python
levers_raw: list[Lever] = []
for response in responses:
    levers_raw.extend(response.levers)
```

The `DocumentDetails.levers` field is defined as `list[Lever]` with a description of
"Propose exactly 5 levers", but pydantic does not enforce a length constraint. If a model
returns 6+ levers in one call (as seen in runs 18 and 23: 16 and 19 levers in a merged
file), the merge blindly extends the list. The downstream clean file (002-10) becomes
invalid for any consumer that expects exactly 15 levers.

---

## Suspect Patterns

### S1 — "more" follow-up prompts carry no context about prior levers

**File:** `identify_potential_levers.py:155-158`

```python
user_prompt_list = [
    user_prompt,
    "more",
    "more",
]
```

Even after B1 is fixed (assistant content properly serialized), the user prompts for calls
2 and 3 are just `"more"`. There is no instruction to generate *different* levers, name
constraints, or reference to what was already produced. A model that does see its prior
output may still interpret "more" as "give me more of the same", producing near-identical
content rather than exploring the remaining solution space.

This is the second layer of the duplication mechanism on top of B1.

---

### S2 — Prompt example name "Material Adaptation Strategy" leaks into output

**File:** `identify_potential_levers.py:104`

```python
   - Name levers as strategic concepts (e.g., "Material Adaptation Strategy")
```

This concrete example name is copied verbatim by weaker models (runs 17 and 18). The
example is domain-specific enough to sound like a real answer but generic enough for any
plan, making it a high-leakage candidate. There is no prompt-level guard against copying it.

---

### S3 — "25% faster scaling" in the measurable-outcomes example invites hallucination

**File:** `identify_potential_levers.py:95`

```python
     • Include measurable outcomes: "Systemic: 25% faster scaling through..."
```

The specific percentage (25%) is copied by at least three models (runs 20, 21, 22). All
five levers in several runs have "25%" in their consequences. The problem is that the
example provides a number without establishing *how* to derive one from the plan; models
memorize the format and the digit.

---

### S4 — No explicit "JSON only" output instruction

**File:** `identify_potential_levers.py:85-127` (system prompt)

The system prompt contains no statement like "Your entire response must be a single valid
JSON object. Do not include any explanatory text, questions, or commentary outside the
JSON." Run 19 (gpt-oss-20b) returned a conversational clarification question instead of
JSON. The prompt structure implies JSON via pydantic schema injection, but that expectation
is implicit.

---

### S5 — `field_validator` for `options` only handles stringified JSON; silent fail on other types

**File:** `identify_potential_levers.py:40-51`

```python
@field_validator('options', mode='before')
@classmethod
def parse_options(cls, v):
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return v
```

If a model returns `options` as a dict (not a list), the validator silently passes it
through and pydantic will raise a validation error later. The error message will be
confusing. This is minor but could obscure the actual model failure mode during debugging.

---

## Improvement Opportunities

### I1 — Inject prior lever names into calls 2 and 3 to enforce cross-call diversity

**File:** `identify_potential_levers.py:155-170`

After B1 is fixed, the "more" prompts should explicitly list already-generated lever names
and instruct the model to use different names:

```python
# Build the follow-up prompt dynamically after each call
already_named = [l.name for l in prior_responses_levers]
follow_up = (
    "Generate 5 MORE levers. "
    "You MUST use lever names that are completely different from: "
    + ", ".join(f'"{n}"' for n in already_named)
    + ". Do not reuse any name from the list above."
)
```

This is the code-level implementation of insight C1. Combined with B1 fix, it would raise
cross-call uniqueness from ~33% to potentially 70–100%.

---

### I2 — Replace "Material Adaptation Strategy" with a neutral placeholder

**File:** `identify_potential_levers.py:104`

Change:
```
   - Name levers as strategic concepts (e.g., "Material Adaptation Strategy")
```
To something non-domain-specific:
```
   - Name levers as strategic concepts (e.g., "Resource Allocation Model")
```
Or omit the example entirely. This eliminates template leakage for weaker models (insight H1).

---

### I3 — Replace the "25% faster scaling" measurable-outcome example

**File:** `identify_potential_levers.py:95`

Change:
```
     • Include measurable outcomes: "Systemic: 25% faster scaling through..."
```
To a causal-mechanism framing that does not invite number-copying:
```
     • State the concrete causal mechanism: explain HOW the systemic effect
       operates (name the actor, the process, and the consequence chain) rather
       than inserting a percentage figure.
```
This addresses insight H3 / runs 20–22 hallucinating "25%" repeatedly.

---

### I4 — Add explicit "JSON only, no dialogue" instruction to the system prompt

**File:** `identify_potential_levers.py:85-127`

Add at the top of the system prompt (section 1):
```
Your ENTIRE response must be a single valid JSON object conforming to the schema.
Do not include any explanatory text, commentary, or questions outside the JSON.
```
This prevents the conversational-response failure mode seen in run 19 (insight H4 / C2-codex).

---

### I5 — Add a post-merge lever-count and format validator

**File:** `identify_potential_levers.py:203-220`

After building `levers_cleaned`, add validation:

```python
if len(levers_cleaned) != 15:
    logger.warning(
        f"Expected 15 levers after merge, got {len(levers_cleaned)}"
    )
for lc in levers_cleaned:
    if len(lc.options) != 3:
        logger.warning(f"Lever '{lc.name}' has {len(lc.options)} options, expected 3")
```

This surfaces overproduction (runs 18: 16 levers, run 23: 19 levers) before the file is
written, allowing the caller to retry or flag the result.

---

### I6 — Add `Field(min_length=5, max_length=5)` constraint on `DocumentDetails.levers`

**File:** `identify_potential_levers.py:57-59`

```python
levers: list[Lever] = Field(
    description="Propose exactly 5 levers.",
    min_length=5,
    max_length=5,
)
```

Pydantic v2 supports `min_length`/`max_length` on list fields. This would cause a
`ValidationError` immediately when a model returns 4 or 6+ levers, making the failure
explicit rather than silently merging the wrong count.

---

### I7 — Fix `set_usage_metrics_path` thread safety in runner

**File:** `runner.py:106-109`

Move the metrics path setup inside the lock alongside the dispatcher handler:

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

And do the same for the `finally` cleanup block at `runner.py:140-142`.

---

## Trace to Insight Findings

| Insight finding | Code location | Root cause |
|---|---|---|
| Cross-call lever duplication (all runs: 33% unique names) | `identify_potential_levers.py:193-198` | **B1**: `message.content` is None for structured LLMs → assistant turns are invisible → model has no memory of prior calls |
| "more" prompt doesn't request diverse levers | `identify_potential_levers.py:157-158` | **S1**: follow-up prompts carry no anti-repetition instruction |
| "Material Adaptation Strategy" template leakage (runs 17, 18) | `identify_potential_levers.py:104` | **S2**: prompt example name is copied verbatim by weak models |
| Hallucinated "25%" percentages (runs 20, 21, 22) | `identify_potential_levers.py:95` | **S3**: example number in prompt is memorized instead of derived |
| Dialogue/non-JSON response failures (run 19) | `identify_potential_levers.py:85-127` | **S4**: no explicit "respond only in JSON" instruction |
| Overproduction (run 18: 16 levers, run 23: 19 levers) | `identify_potential_levers.py:204-206` | **B3**: no lever-count validation; blind extend |
| Metrics cross-contamination in parallel runs | `runner.py:106`, `runner.py:140` | **B2**: `set_usage_metrics_path` called outside thread lock |

---

## Summary

**The single most impactful bug is B1** (assistant turn serialization). When using
`as_structured_llm`, `message.content` is typically `None` for function-calling-based
models (OpenAI, Anthropic). The code appends this null content as the assistant turn in the
multi-turn chat, meaning call 2 and call 3 have no memory of what was generated. Every run
re-generates from scratch, producing identical or near-identical levers. This is confirmed by:

- All 6 producing runs showing exactly 33% unique lever names (5 unique out of 15)
- Byte-for-byte identical responses within a single run (run 18, run 22)
- The project memory noting "Next: iteration 2, fix assistant turn serialization"

**B1 fix + I1 (inject prior names)** together address the dominant quality failure
(cross-call duplication) at the code level, without requiring any prompt changes.

**S2 + S3** are prompt defects in the system prompt constant in the same Python file; they
require only editing the string literal. They explain template leakage (runs 17, 18) and
hallucinated percentages (runs 20–22).

**S4** (no JSON-only instruction) explains run 19's complete failure mode and is a one-line
prompt addition.

**B3 + I6** address the overproduction bug (runs 18, 23) where models return more than 5
levers per call, producing a merged file with 16 or 19 levers instead of 15.

Priority order:
1. B1 — fix assistant turn serialization (highest leverage, eliminates duplication root cause)
2. I1 — inject prior lever names in follow-up prompts (second layer of diversity enforcement)
3. S2 — remove/replace "Material Adaptation Strategy" example (trivial, high impact for weak models)
4. S3 — replace "25% faster scaling" example (trivial, prevents hallucinated numbers)
5. S4 — add explicit JSON-only instruction (prevents dialogue-response failures)
6. B3 / I6 — enforce 5-lever count via pydantic or post-merge validation
