# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — `strategic_rationale` and `summary` are Optional with `default=None`

**File:** `identify_potential_levers.py:61–71`

```python
class DocumentDetails(BaseModel):
    strategic_rationale: Optional[str] = Field(
        default=None,
        ...
    )
    ...
    summary: Optional[str] = Field(
        default=None,
        ...
    )
```

Both fields have `Optional[str]` with `default=None`. Pydantic structured output treats this as "this field is not required". The LLM JSON schema will show these as optional fields that can be omitted. No validator or prompt instruction overrides this. The system prompt (section 4, lines 128–130) says to fill `summary` with a concrete format, but since the schema marks it optional, every model takes the path of least resistance and omits it. This directly causes the 100%-null rate observed for both fields across all 7 runs.

---

### B2 — `summary` field description contradicts system prompt instruction

**File:** `identify_potential_levers.py:68–71`

```python
summary: Optional[str] = Field(
    default=None,
    description="Are these levers well picked? Are they well balanced? Are they well thought out? Point out flaws. 100 words."
)
```

The JSON schema description says "Are these levers well picked? ... Point out flaws. 100 words." — a general qualitative question.

The system prompt (lines 128–130) says: "Identify ONE critical missing dimension" and "Prescribe CONCRETE addition: 'Add \'[full strategic option]\' to [lever]'".

These are genuinely different instructions. The schema description asks for a balanced critique; the system prompt demands a specific format with a concrete `Add '...' to ...` sentence. When structured output is used, the LLM sees the schema description directly. The contradiction means even a model trying to fill the field could produce either form and still be "following instructions". This compounds B1.

---

### B3 — No `field_validator` enforcing exactly 5 levers per call

**File:** `identify_potential_levers.py:65–67`

```python
levers: list[Lever] = Field(
    description="Propose exactly 5 levers."
)
```

The description says "exactly 5" but there is no `field_validator` to enforce this. If a model returns 4, 6, or more levers, Pydantic accepts the response without complaint and all levers are appended to `levers_raw` (lines 231–232). Three calls producing 5+5+6 levers would silently yield 16 in the merged output. The insight files document exactly this: prior batches (runs 33, 35, 37, 38) produced 16-lever gta_game outputs non-deterministically.

---

### B4 — `review_lever` field description omits the `Weakness:` prefix requirement

**File:** `identify_potential_levers.py:43–45`

```python
review_lever: str = Field(
    description="Critique this lever. State the core trade-off it controls (e.g., 'Controls Speed vs. Quality'). Then, identify one specific weakness in how its options address that trade-off."
)
```

The schema description (what the LLM sees in the JSON schema for structured output) does not include the required `Weakness:` prefix. The system prompt section 4 (lines 126–127) specifies:
- `"Controls [Tension A] vs. [Tension B]."`
- `"Weakness: The options fail to consider [specific factor]."`

But the field description only says "identify one specific weakness" without the required prefix. This allows models to satisfy the field description without including `Weakness:`. Run 40 (llama3.1) produced alternating controls-only / weakness-only reviews; neither half had both components, suggesting the model interpreted the two bullet points in the system prompt as alternatives rather than a combined requirement.

---

### B5 — Race condition: `set_usage_metrics_path` called outside `_file_lock`

**File:** `runner.py:97–114`

```python
# comment: "set_usage_metrics_path and the dispatcher are global state,
#           so we hold a lock while configuring and running"
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # line 106 — outside lock

with _file_lock:                                                    # line 108
    dispatcher.add_event_handler(track_activity)                   # line 109

t0 = time.monotonic()
try:
    result = IdentifyPotentialLevers.execute(...)                   # line 114 — outside lock
```

The comment on lines 97–98 correctly identifies that `set_usage_metrics_path` and `dispatcher` are global state requiring a lock. However, `set_usage_metrics_path` on line 106 is called *before* the lock. The `finally` block also calls `set_usage_metrics_path(None)` on line 140 outside the lock. When `workers > 1`, two threads can interleave:

1. Thread A calls `set_usage_metrics_path(path_A)` — line 106
2. Thread B calls `set_usage_metrics_path(path_B)` — line 106
3. Thread A's LLM call writes metrics to `path_B` (wrong file)

The entire `execute()` call also runs without holding the lock, meaning any global state set in step 3 is unprotected during the actual LLM execution.

---

## Suspect Patterns

### S1 — Assistant message falls back to full `model_dump_json()` when content is empty

**File:** `identify_potential_levers.py:215–223`

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

Some LLMs (particularly those using native structured output) return an empty `message.content` while putting structured data only in the raw response. When `message.content` is falsy, the code falls back to serializing the full Pydantic model as JSON with `model_dump_json()`. This produces an assistant message containing all 5 levers with full field content — potentially hundreds of tokens of JSON. On calls 2 and 3, the LLM sees this large JSON blob as the prior assistant turn, which can:
- Cause the model to treat the JSON structure as the expected response format (template leakage)
- Inflate the token context significantly for subsequent calls
- Confuse the model about what the "Generate 5 MORE levers" user message means in context

---

### S2 — No code-side enforcement of the lever name uniqueness prohibition

**File:** `identify_potential_levers.py:174, 180–183, 225`

```python
generated_lever_names: list[str] = []
...
names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]"
)
...
generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
```

The prohibition against reusing names is conveyed via the follow-up prompt only. There is no code-side check after each call that verifies the returned lever names are actually new. If a model ignores the instruction and reuses a name, the duplicate passes silently into `levers_raw`. The insight files note that baseline has 23 duplicate names across 75 levers — this pattern could persist if models ignore the prohibition.

---

### S3 — `consequences` target length may be driving timeouts

**File:** `identify_potential_levers.py:35–37`

```python
description=(
    ...
    "Target length: 150–300 words."
)
```

The field description specifies 150–300 *words*. At ~5 chars/word, 150 words ≈ 750 chars and 300 words ≈ 1500 chars. The insight files show run 45 (haiku) averaging ~700 chars per consequence (~140 words), within the specified range. The baseline averages ~280 chars (~56 words) — well below the specified minimum.

The 150-word minimum is much larger than the baseline. For high-verbosity models like haiku, it may be driving the ~700-char consequences that, when multiplied across 5 levers × 3 calls, cause the parasomnia plan to exceed the API timeout at 432s. Meanwhile, the baseline's ~56-word consequences suggest the original intent was shorter output. This measurement unit mismatch (baseline was calibrated on shorter output; the field now requests 3× longer) is a root cause of the haiku timeout.

---

## Improvement Opportunities

### I1 — Add `field_validator` to enforce exactly 5 levers per call

Add to `DocumentDetails`:

```python
@field_validator('levers')
@classmethod
def enforce_five_levers(cls, v):
    if len(v) != 5:
        raise ValueError(f"Expected exactly 5 levers, got {len(v)}")
    return v
```

This would cause Pydantic to reject over- or under-count responses at the structured-output parse stage, triggering a retry via LLMExecutor rather than silently accepting a 4- or 6-lever batch.

---

### I2 — Make `strategic_rationale` and `summary` required (or remove them)

If these fields are intended to be LLM-generated, change `Optional[str]` to `str` and remove `default=None`. This forces the JSON schema to mark them required, giving the LLM no legal way to omit them.

If they are intended to be filled by a later pipeline stage, document that in a code comment and the system prompt, and strip them from the LLM schema entirely to avoid confusion.

---

### I3 — Align `summary` field description with system prompt format

The field description should match what section 4 of the system prompt requires:

```python
description=(
    "Required format: First sentence identifies ONE critical missing dimension. "
    "Second sentence prescribes a concrete addition: "
    "\"Add '[full strategic option]' to [lever name].\" "
    "Two sentences only."
)
```

---

### I4 — Add post-merge validation before saving

After merging levers from 3 calls, validate each lever before writing to file. At minimum:

- Consequence contains `"Immediate:"`, `"Systemic:"`, `"Strategic:"` substrings
- Review contains both `"Controls "` and `"Weakness:"` substrings
- Consequence does NOT contain `"Controls "` or `"Weakness:"` (cross-contamination guard)
- Options list has exactly 3 elements, each > 30 characters
- No lever name appears more than once in the merged list

---

### I5 — Include `set_usage_metrics_path` inside `_file_lock` scope

Move both the setup and teardown calls inside the lock to prevent race conditions when `workers > 1`:

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

And in the `finally` block:

```python
finally:
    with _file_lock:
        set_usage_metrics_path(None)
        dispatcher.event_handlers.remove(track_activity)
```

---

### I6 — Add `field_validator` for option count in `Lever`

Run 40 produced one lever with only 2 options (sovereign_identity plan). The `options` field description says "Exactly 3 options" but there is no validator:

```python
@field_validator('options')
@classmethod
def enforce_three_options(cls, v):
    if len(v) != 3:
        raise ValueError(f"Expected exactly 3 options, got {len(v)}")
    return v
```

---

### I7 — Guard against known-failing models before execution

Run 39 (nvidia-nemotron-3-nano-30b-a3b) has failed with the same JSON extraction error in 4 consecutive batch runs (24, 25, 32, 39). Each failure wastes ~540s of execution time. A configurable `KNOWN_FAILING_MODELS` set with an early warning or skip in the runner would prevent this:

```python
KNOWN_FAILING_MODELS = {"openrouter-nvidia-nemotron-3-nano-30b-a3b"}
```

---

## Trace to Insight Findings

| Insight observation | Code root cause |
|---|---|
| `strategic_rationale` null in 100% of responses, all 7 runs | B1: field declared `Optional` with `default=None` |
| `summary` null in 100% of responses, all 7 runs | B1: same; compounded by B2 (description contradicts system prompt) |
| Run 40 reviews alternate Controls-only / Weakness-only (0 reviews with both) | B4: field description omits `Weakness:` prefix requirement; schema doesn't enforce dual-component format |
| Prior batch 16-lever gta_game overflow (runs 33, 35, 37, 38) | B3: no `field_validator` on `DocumentDetails.levers` |
| Run 43 appends review text into `consequences` field | S1 (partial): if `message.content` is empty, `model_dump_json()` may train models to blend fields in chat context; B4 (partial): weak field boundary descriptions |
| Run 45 haiku times out on parasomnia (432s) | S3: 150–300 word target in field description drives verbose output, far above baseline calibration |
| Run 40 one lever has only 2 options | No `field_validator` on `Lever.options` (see I6) |
| Usage metrics may be written to wrong plan directory when workers > 1 | B5: `set_usage_metrics_path` called outside `_file_lock` |
| Run 39 wastes ~540s per batch despite 4 consecutive complete failures | No known-model early-exit (see I7) |
| Insight codex H4: "stronger prompt wording for dual-component review" needed | B4: the schema-level description (what LLMs see via structured output) is weaker than the system prompt text |

---

## Summary

The two most impactful bugs are B1 and B3. **B1** (Optional fields with `default=None`) directly causes the universal-null pattern for `strategic_rationale` and `summary`; this is not a model failure but a schema design choice that actively prevents models from filling the fields. **B3** (no lever count validation) allows over-generation to pass silently; the 16-lever gta_game overflow in prior batches would be deterministically prevented by a `field_validator`.

**B2** and **B4** are consistency bugs: the `summary` description contradicts the system prompt's format requirement, and the `review_lever` schema omits the `Weakness:` prefix that is required in the system prompt. Both cause models that attempt to comply to produce outputs that violate at least one of the two conflicting instructions.

**B5** is a threading correctness issue in the runner that affects accuracy of per-plan usage metrics when parallel workers are used.

**S1** (assistant message `model_dump_json` fallback) and **S3** (150–300 word consequence target far above baseline calibration) are the primary suspects for the haiku verbosity/timeout problem and for potential context contamination in multi-call conversations.

The highest-priority fixes are: enforce required fields (B1), align `summary` description with system prompt (B2), add a `field_validator` for lever count (B3), and strengthen the `review_lever` schema to match the system prompt's dual-component requirement (B4).
