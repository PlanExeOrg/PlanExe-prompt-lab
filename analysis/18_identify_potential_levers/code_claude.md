# Code Review (claude)

Reviewed files:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

PR under review: #297 — "fix: simplify lever prompt to restore content quality"

---

## Bugs Found

### B1 — `Lever.consequences` Pydantic field description still mandates old chain format

**File:** `identify_potential_levers.py:34–46`

```python
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "
        ...
    )
)
```

When `llm.as_structured_llm(DocumentDetails)` is called, llama_index serializes the
Pydantic schema — including all `Field(description=...)` strings — into a JSON schema that
is sent to the model as the tool/function definition. For OpenAI-compatible and
Anthropic-structured-output backends this schema is passed alongside the system prompt.

The field description tells the model to use `Immediate → Systemic → Strategic` with a
mandatory `%` quantification. The updated system prompt (prompt_4) says the opposite.
Most strong models (haiku, gemini, qwen3) resolve the contradiction in favor of the system
prompt. Weaker models (llama3.1) receive two conflicting instructions simultaneously, which
contributes to erratic behavior in later calls.

This is the most significant gap left by PR #297. The PR updated the external prompt file
but did not update the Pydantic schema description that is sent to every model on every call.

### B2 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant not updated

**File:** `identify_potential_levers.py:154–196`

The hardcoded fallback constant still mandates:
- `"Chain three SPECIFIC effects: 'Immediate: [effect] → Systemic: [impact] → Strategic: [implication]'"` (line 163)
- `"Include measurable outcomes: ... a % change, capacity shift, or cost delta"` (line 164)
- `"Show clear progression: conservative → moderate → radical"` (line 169)
- `"Radical option must include emerging tech/business model"` (line 193)

This constant is used in two paths:
1. When `execute()` is called without a `system_prompt` argument (lines 213–214), e.g. from
   any caller that does not use the runner.
2. When running the module directly (`__main__`, line 375): `IdentifyPotentialLevers.execute(llm_executor, query)` — no `system_prompt` argument.

Ad-hoc testing via `python -m worker_plan_internal.lever.identify_potential_levers` uses
the stale constant and will reproduce the old fabricated-% and chain-format failures
regardless of the external prompt file.

### B3 — `LeverCleaned.consequences` field description is also stale

**File:** `identify_potential_levers.py:130–139`

`LeverCleaned` is used only for output storage (not for structured LLM generation), so this
does not affect model behavior. However, it is the same old chain format with mandatory
quantification. The stale description is misleading for anyone reading the code and masks
whether the PR was applied completely.

### B4 — Thread safety: `set_usage_metrics_path` called outside lock

**File:** `runner.py:106`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)                 # inside lock

t0 = time.monotonic()
try:
    result = IdentifyPotentialLevers.execute(...)                 # outside lock
finally:
    set_usage_metrics_path(None)                                  # outside lock
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)
```

`set_usage_metrics_path` sets a global path. When `workers > 1`, two threads can execute
this sequence concurrently:

1. Thread A sets path to `plan_a/usage_metrics.jsonl`
2. Thread B sets path to `plan_b/usage_metrics.jsonl`  ← overwrites A's setting
3. Thread A runs LLM calls; metrics land in `plan_b/usage_metrics.jsonl` (wrong file)

The comment on lines 97–98 says "hold a lock while configuring and running to avoid
cross-thread interference", but the actual lock does not cover `set_usage_metrics_path` or
the LLM execution. With sequential workers (default) this is not triggered, but it is a
latent bug.

### B5 — Bracket placeholders in `review_lever` field description copied literally by some models

**File:** `identify_potential_levers.py:51–57`

```python
review_lever: str = Field(
    description=(
        "Required format: Two sentences. "
        "Sentence 1: 'Controls [Tension A] vs. [Tension B].' "
        "Sentence 2: 'Weakness: The options fail to consider [specific factor].' "
        ...
    )
)
```

The field description uses `[Tension A]`, `[Tension B]`, and `[specific factor]` as
bracket placeholders. These appear in the JSON schema sent to every model. Some models
(gpt-5-nano, run 33) interpret the brackets as format placeholders and copy them verbatim
into output: `Controls [centralization vs decentralization] vs. [platform lock-in]...`

The same bracket templates appear in prompt_4 lines 21–22 as well, so the signal is doubled.
PR #297 added `"NO placeholder consequences or bracket-wrapped templates"` to the
prohibitions (prompt_4 section 5), but the bracket format is still shown as the target
format in section 4 — the prohibition and the example contradict each other.

---

## Suspect Patterns

### S1 — Multi-call user message for calls 2/3 does not reinforce option quality

**File:** `identify_potential_levers.py:231–235`

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```

The opening instruction for calls 2 and 3 only says "generate more with different names."
It does not reinforce the quality requirements from the system prompt: "each option must be
a complete strategic approach," "not just labels," etc. For weaker models (llama3.1), this
implicit lower bar on calls 2/3 may contribute to the observed option quality degradation
in later calls (N1).

Additionally, the `[{names_list}]` format wraps the names list in square brackets, which
may subtly reinforce bracket usage in models already prone to bracket output (B5).

### S2 — `summary` field description conflicts with prompt format requirement

**File:** `identify_potential_levers.py:113–115`

```python
summary: str = Field(
    description="Are these levers well picked? Are they well balanced? Are they well thought out? Point out flaws. 100 words."
)
```

The system prompt (prompt_4 lines 23–25) says:
```
• Identify ONE critical missing dimension
• Prescribe CONCRETE addition: "Add '[full strategic option]' to [lever]"
```

The Pydantic field description gives a completely different instruction: open-ended critique
in ~100 words. Models receive both via schema and system prompt and must choose between them.
Runs 32–37 achieve 0 exact summary matches (0/104 after excluding run 31's 11/15). The field
description is the likely cause: it actively directs models away from the format the prompt
requires.

### S3 — No option minimum-length validation

**File:** `identify_potential_levers.py:73–84`

`check_option_count` validates that there are exactly 3 options but does not check content
length. Label-only options like `"Centralized Authority"` (2 words) pass validation
identically to a 25-word complete strategic approach. The N1 issue (7/21 llama3.1 levers
with label-only options) reaches the output file undetected because the validator only
checks the count.

### S4 — One bad lever fails the entire call

**File:** `identify_potential_levers.py:73–84, 259–278`

If a single `Lever` inside a `DocumentDetails` response fails `check_option_count`, Pydantic
rejects the entire `DocumentDetails` object. The `except Exception` handler at line 264
catches this as a complete call failure. For call 1 (lines 272–273), this propagates as
`LLMChatError`, discarding all levers that call produced. For calls 2/3 it falls back to
partial results. There is no way to salvage the 4–6 valid levers when 1 lever has the wrong
option count.

---

## Improvement Opportunities

### I1 — Update `Lever.consequences` description to match prompt_4

**File:** `identify_potential_levers.py:34–46`

Replace the mandatory chain format and quantification requirement with language matching
prompt_4: "describe the direct effect of pulling this lever, then at least one downstream
implication or trade-off; do not fabricate percentages or cost estimates; target 2–4
sentences." This removes the contradictory signal in the JSON schema.

### I2 — Update `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant

**File:** `identify_potential_levers.py:154–196`

Replace the constant's content with the text of prompt_4 (or a functionally equivalent
version). This ensures that ad-hoc testing and any code path that does not supply a
`system_prompt` argument gets the same behavior as production runs.

### I3 — Update `LeverCleaned.consequences` description

**File:** `identify_potential_levers.py:130–139`

Same update as I1 for the `LeverCleaned` class. No behavior change, but removes the stale
documentation that makes the PR appear incomplete.

### I4 — Fix thread safety for `set_usage_metrics_path`

**File:** `runner.py:106–143`

Either (a) extend the lock to cover `set_usage_metrics_path` and the full LLM execution, or
(b) make usage metrics tracking thread-local rather than global. The current code works only
because the default `workers=1`. If a config sets `workers > 1`, usage metrics will cross
between plan files.

### I5 — Add option minimum word-count validator

**File:** `identify_potential_levers.py`

Add a `field_validator` on `options` that rejects any option shorter than, say, 8 words.
This would catch the N1 label-only options (`"Centralized Authority"`, `"Maximize Efficiency"`)
at parse time and convert them into a retryable validation error rather than a silent quality
failure. The system prompt says "not just labels" — this enforces it structurally.

### I6 — Align `summary` field description with prompt format

**File:** `identify_potential_levers.py:113–115`

Replace the open-ended "Are these levers well picked?..." description with the concrete
format from prompt_4: `Add '[full strategic option]' to [lever]`. This removes the
conflicting signal that drives the 0% exact match rate in runs 32–37.

### I7 — Replace bracket placeholders in `review_lever` description and prompt with concrete examples

**File:** `identify_potential_levers.py:51–57`; `prompt_4.txt:20–22`

Replace `[Tension A]`, `[Tension B]`, `[specific factor]` with a concrete, non-bracket
example: `"Controls short-term execution speed vs. long-term architectural risk. Weakness:
The options fail to consider regulatory approval timelines."` Add an explicit prohibition:
`"Do NOT write literal square brackets in your output — replace each placeholder with actual
content."` This closes the gap that PR #297's prohibition alone did not close (run 33 still
produced 36 bracket instances despite the prohibition at prompt_4 line 30).

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|---|---|
| N1 — llama3.1 label-only options in call-2/3 | S1 (no quality reinforcement in multi-call prompt); S3 (no min-length validator) |
| N2 — llama3.1 fabricated % in consequences | B1 (stale `Lever.consequences` field description still mandates `% change or cost delta`) |
| N3 — llama3.1 "Direct Effect / Downstream Implication" sub-headers | B1 (field description's chain format prompts sub-header extraction); prompt_4 line 8 uses "direct effect" and "downstream implication" as guidance words, which llama3.1 reuses literally |
| N4 — qwen3 fabricated % in options | B1 (field description does not prohibit fabrication in options, only the system prompt does) |
| run 33 bracket placeholder leakage (36 instances) | B5 (bracket placeholders in `review_lever` field description + prompt_4 section 4; prohibition in section 5 conflicts with the example in section 4) |
| 0% exact summary match in runs 32–37 | S2 (field description gives contradictory instruction vs. system prompt's concrete format) |
| llama3.1 multi-call quality degradation (analysis/17 bracket consequences → analysis/18 label-only options) | S1 (each call has no quality reinforcement); B1 (stale field description gives mixed signals) |
| Ad-hoc `__main__` testing would reproduce old fabricated-% behavior | B2 (stale `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant) |
| Metrics may land in wrong plan file with workers > 1 | B4 (thread-unsafe `set_usage_metrics_path`) |

---

## PR Review

### What the PR changed

PR #297 replaced prompt_3 with prompt_4 as the external system prompt file. The key changes
in the prompt file were:

- Removed mandatory `Immediate → Systemic → Strategic` chain in consequences ✓
- Removed `conservative → moderate → radical` option template ✓
- Removed "Radical option must include emerging tech/business model" ✓
- Added "NO fabricated statistics or percentages without evidence" ✓
- Added "NO marketing language" ✓
- Changed target consequence length from "3–5 sentences" to "2–4 sentences" ✓
- Changed `review_lever` section heading from "Validation Protocols" to clarified format ✓

### What the PR missed

**Critical gap — Pydantic field descriptions not updated (B1)**

The `Lever.consequences` description at `identify_potential_levers.py:34–46` still says
`"Required format: 'Immediate: [effect] → Systemic: [impact] → Strategic: [implication]'. All
three labels and at least one quantitative estimate are mandatory."` This description is part
of the JSON schema sent to every LLM on every call. It directly contradicts the updated
system prompt.

The practical impact varies by model strength: haiku, gemini, and qwen3 appear to follow the
system prompt and largely ignore the conflicting field description. llama3.1 receives the
contradiction and continues to produce behavior consistent with the old field description
(fabricated %, sub-headers). This is not a coincidence — it's the expected outcome of a
weaker model receiving two conflicting format instructions.

**Hardcoded fallback constant not updated (B2)**

`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 154–196) is not part of the production
code path (runner.py always passes the file contents), but it is used by the `__main__`
block and by any caller that omits `system_prompt`. The constant still mandates chain format
and fabricated metrics. A developer testing via `python -m worker_plan_internal.lever.identify_potential_levers`
would see the old broken behavior and could mistakenly believe the PR had no effect.

**Bracket placeholder contradiction not resolved (B5)**

Prompt_4 section 4 shows `[Tension A]`, `[Tension B]`, `[specific factor]` as the target
format, while section 5 says "NO placeholder consequences or bracket-wrapped templates." The
prohibition and the example fight each other. The `Lever.review_lever` Pydantic field
description (lines 51–57) also uses the bracket format. For run 33 (gpt-5-nano), this
double bracket signal overrode the prohibition, producing 36 bracket instances across all
final outputs.

### Does the PR achieve its stated goal?

Yes, substantially. The content quality regressions it targeted — mandatory chain format,
fabricated quantification, excessive length — are eliminated or drastically reduced for the
four strongest models (haiku, gemini, qwen3, gpt-4o-mini). The 97.1% → 100% success rate
improvement and the 3.6× file-size reduction for haiku hong_kong are real, measurable gains.

The PR is incomplete rather than wrong. The changes to the external prompt file were
necessary and effective. The Pydantic schema was not updated to match, which creates a
persistent low-level contradictory signal that matters most for weaker models. A complete
implementation of the PR's intent would also update `Lever.consequences` (B1),
`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (B2), and resolve the bracket template
contradiction (B5).

---

## Summary

The most significant finding is **B1**: the `Lever.consequences` Pydantic field description
(`identify_potential_levers.py:34–46`) was not updated by PR #297. It still mandates the
`Immediate → Systemic → Strategic` chain with mandatory `%` quantification, contradicting
the updated system prompt in every structured LLM call. Strong models resolve the
contradiction by following the system prompt; weaker models (llama3.1) do not, which
explains N2 (fabricated %) and N3 (sub-header format) in this analysis batch.

The second most actionable finding is **S2**: the `DocumentDetails.summary` field
description actively directs models toward a different format than the system prompt
requires, explaining the 0% exact summary match rate across runs 32–37.

**B4** (thread-safety in runner.py) is a latent but real bug that does not affect current
runs (workers=1 by default) but would corrupt usage metrics silently if any model config
sets `luigi_workers > 1`.

**B5** (bracket placeholder contradiction) is directly observable in run 33's 36 placeholder
instances and is not fully addressed by the current prohibition.

Priority order for follow-up work:
1. **B1** — update `Lever.consequences` field description to match prompt_4 (highest impact, affects every model)
2. **B2** — update `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant
3. **S2 / I6** — align `summary` field description with concrete format
4. **B5 / I7** — replace bracket placeholders with a concrete non-bracket example
5. **S1 / I5** — add quality reinforcement to multi-call prompts; add option minimum-length validator
6. **B4 / I4** — fix thread safety for `set_usage_metrics_path`
