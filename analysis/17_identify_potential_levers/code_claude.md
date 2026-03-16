# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py` (consulted for `_TRANSIENT_PATTERNS`)

---

## Bugs Found

### B1 — `set_usage_metrics_path()` called outside `_file_lock` (runner.py:106)

**File:** `prompt_optimizer/runner.py`, lines 106–109

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # ← outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path()` writes to global state, but is called *before* acquiring
`_file_lock`. The comment at line 97 explicitly acknowledges that both
`set_usage_metrics_path` and the dispatcher are global state that requires the lock.
`dispatcher.add_event_handler()` is protected; the path setter is not.

With `workers > 1`, two threads can interleave as follows:
1. Thread A sets path to `plan_A/usage_metrics.jsonl`
2. Thread B sets path to `plan_B/usage_metrics.jsonl` (overwrites A's value)
3. Thread A acquires the lock, adds its handler — but the handler now logs to B's path

The `finally` block has the same issue: `set_usage_metrics_path(None)` at line 140 is
also outside the lock. A thread completing `plan_A` can null-out the path while
`plan_B` is actively writing metrics, silently dropping B's usage data.

**Severity:** Data corruption / silent data loss when `workers > 1`.

---

### B2 — `DocumentDetails.summary` field description contradicts system prompt

**File:** `identify_potential_levers.py`, lines 113–115 vs. lines 181–183

The Pydantic `Field(description=...)` for `summary` says:

```python
summary: str = Field(
    description="Are these levers well picked? Are they well balanced? "
                "Are they well thought out? Point out flaws. 100 words."
)
```

The system prompt (`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`, section 4) says:

```
For `summary`:
  • Identify ONE critical missing dimension
  • Prescribe CONCRETE addition: "Add '[full strategic option]' to [lever]"
```

For structured LLM calls (`llm.as_structured_llm(DocumentDetails)`), the model
receives the Pydantic schema including field `description` attributes. These
descriptions are the primary per-field instructions the model sees at generation
time. The `description` here guides the LLM toward a general critique essay
("Are these levers well picked?"), while the system prompt instructs a specific
prescription format (`Add '...' to [lever]`). The two instructions conflict,
and the permissive description reliably wins.

**Observable effect:** insight_codex Table 1 shows `summary` exact-format matches
of `0/15` for runs 25–30 (every model except llama3.1 at `14/15`). This is the
most consistently ignored instruction in the batch, and the conflict between the
field description and system prompt is the direct cause.

---

## Suspect Patterns

### S1 — `check_review_format` auto-correction implied by iteration title but absent in code

**File:** `identify_potential_levers.py`, lines 86–99

The iteration-17 memory title is "review_lever auto-correct", and
`analysis/16_identify_potential_levers/assessment.md` recommended prepending
"Controls " to `review_lever` values that contain `" vs. "` and `"Weakness:"` but
lack the leading word "Controls". However, the validator as written only rejects:

```python
@field_validator('review_lever', mode='after')
@classmethod
def check_review_format(cls, v):
    if 'Controls ' not in v:
        raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
    if 'Weakness:' not in v:
        raise ValueError("review_lever must contain 'Weakness: ...'")
    return v
```

No auto-prepend logic is present. If the recommendation was implemented, it would
appear here as something like:

```python
if ' vs. ' in v and 'Weakness:' in v and not v.startswith('Controls '):
    v = 'Controls ' + v
```

**Implication:** haiku's hong_kong recovery (run 23 → run 30: 0 levers → 5/5) may
be due to the prompt change (prompt_2 → prompt_3) improving haiku's format compliance
on that plan, rather than a code-level auto-correction. The insight's inference that
auto-correction was implemented is not confirmed by the code. This matters for
predicting robustness: if haiku regresses on future plans, the corrective mechanism
may not be in place.

---

### S2 — `Lever.lever_index` generated but discarded

**File:** `identify_potential_levers.py`, lines 28–30, 292–306

The `Lever` model has a `lever_index: int` field that the LLM populates on every
call. The `LeverCleaned` model has no corresponding field. The copy loop at lines
299–305 transfers `name`, `consequences`, `options`, and `review_lever` — silently
dropping `lever_index`. The index is written to the raw JSON (via `save_raw`) but
never reaches the clean output.

Beyond the minor token waste, the lost index could be used to detect call-internal
ordering anomalies (e.g., a model that resets indices to 1 on every call, signalling
template-collapse). Currently that signal is invisible.

---

## Improvement Opportunities

### I1 — Add `"eof while parsing"` to `_TRANSIENT_PATTERNS` (llm_executor.py:41)

**File:** `worker_plan/worker_plan_internal/llm_util/llm_executor.py`, line 41

Current `_TRANSIENT_PATTERNS` covers rate limits, timeouts, and server errors but
not JSON truncation:

```python
_TRANSIENT_PATTERNS: list[str] = [
    "rate limit", "rate_limit", "ratelimit", "429",
    "timeout", "timed out", "connection", "connect",
    "temporarily unavailable", "503", "502", "500",
    "overloaded", "capacity", "try again",
    "server error", "internal error",
    "nonetype", "'none' object", "none' object is not",
]
```

The gpt-oss-20b parasomnia failure is:

```
Invalid JSON: EOF while parsing a list at line 58 column 5
```

This is a provider-side truncation, not a model capability problem (the model got to
line 58 vs. line 25 in an earlier batch, showing variability). Adding
`"eof while parsing"` (matched case-insensitively via the existing `.lower()` call)
would enable automatic retry on the next fallback LLM.

Adding `"invalid json"` more broadly would also catch other truncation variants
(e.g., `"Invalid JSON: expected value at line 1 column 1"`), but that risks retrying
on genuine schema mismatches. `"eof while parsing"` is more targeted.

**Expected effect:** gpt-oss-20b parasomnia failure (three consecutive batches, runs
18, 20, 25) converts from permanent plan loss to a retried attempt. Success rate on
parasomnia rises from 0/3 to potentially 1–2/3 across batches.

---

### I2 — Remove `strategic_rationale` from `DocumentDetails`

**File:** `identify_potential_levers.py`, lines 102–105

`strategic_rationale` is an `Optional[str]` field on `DocumentDetails`. It is
generated by the LLM on every call (models typically fill optional fields when
they appear in the schema), included in `save_raw()` output, but **not** included
in `save_clean()` output (which only serializes `self.levers`). It is dead generation
overhead on every one of the three LLM calls per plan.

The existing comment at lines 106–108 notes the intentional removal of a `max_length`
cap on `levers`. The `strategic_rationale` field deserves the same attention: if it
adds no downstream value, removing it from the schema reduces per-call output token
count, which matters for haiku on parasomnia (291s, close to timeout even when
successful) and for gpt-oss-20b where token budget is the failure mechanism.

Estimated savings: ~200–500 output tokens per call × 3 calls × N plans. The exact
impact varies by model verbosity.

---

### I3 — Align `DocumentDetails.summary` description to system prompt (or remove the field)

**File:** `identify_potential_levers.py`, lines 113–115

Following from B2: if `summary` is retained, its `description=` should be changed to
reinforce the `Add '...' to [lever]` format that the system prompt requires. The
field description is what the structured LLM reads at schema time; it overrides or
dilutes the system prompt's instruction for this field.

If `summary` is removed entirely: like `strategic_rationale`, it does not appear in
`save_clean()` output and carries no downstream validation. Removing it eliminates
the conflicting guidance and saves tokens.

If kept, the description should read something like:
`"Identify ONE critical missing option. Format: Add '[full strategic option]' to [lever name]. No preamble."`

---

### I4 — Add `@field_validator` for `consequences` to detect review-text contamination

**File:** `identify_potential_levers.py`, lines 34–46

The `consequences` field description already prohibits `Controls`, `Weakness:`, and
review text (lines 42–43). However, there is no runtime check. qwen3 contaminated
66/85 final `consequences` fields across runs 27 (all plans), and the field
description prohibition had no effect.

A `@field_validator('consequences', mode='after')` could:
- **At minimum:** log a warning when `"Controls "` and `"Weakness:"` appear together
  near the end of `consequences` — this makes the contamination visible in run logs
  rather than silent.
- **Optionally:** strip the trailing suffix matching the review pattern. This is
  riskier (could strip intentional content) but would rescue qwen3 outputs from being
  permanently contaminated in the clean file.

The validator on `Lever` is the right location (mirrors the existing
`check_review_format` pattern).

---

### I5 — Pre-flight model name validation before plan execution loop

**File:** `prompt_optimizer/runner.py`, lines 93, 370–389

`LLMModelFromName.from_names(model_names)` is called inside `run_single_plan()`,
which runs per plan (either sequentially or in a thread pool). If the primary model
name is invalid (e.g., `openrouter-paid-gemini-2.0-flash-001` as in run 29), the
error is only discovered when the first plan attempt is made. With `workers > 1`,
all N plan threads attempt the invalid name simultaneously, all fail, and then all
retry with the fallback — producing two complete waves in `events.jsonl`.

A single call to `LLMModelFromName.from_names(model_names)` before the plan loop
(as a validation probe that is then discarded) would catch invalid names before any
plan execution begins. Alternatively, `_resolve_workers()` already reads `llm_config`
to resolve worker counts; it could also validate that every model name exists in the
merged config and warn on unknown names.

**Expected effect:** Run 29's 5 wasted start attempts are eliminated, saving wall
time and making `events.jsonl` cleaner for analysis.

---

### I6 — Fix stale `openrouter-paid-gemini-2.0-flash-001` LLM config alias

**File:** LLM config JSON file(s) in `llm_config/` (not reviewed directly)

Run 29 shows the primary model name `openrouter-paid-gemini-2.0-flash-001` is not
registered, while `openrouter-gemini-2.0-flash-001` works. The "paid" variant appears
to be a stale alias from an earlier config iteration. Removing or correcting this
alias prevents the entire wave-1 failure in future runs using the gemini model.

This is a config change, not a code change, but worth flagging here since it
explains the "two waves" anomaly in `events.jsonl`.

---

## Trace to Insight Findings

| Insight observation | Code issue |
|---|---|
| N1 — gpt-oss-20b parasomnia EOF (3rd consecutive batch) | I1: `"eof while parsing"` absent from `_TRANSIENT_PATTERNS` in `llm_executor.py:41` |
| N2 — qwen3 consequence contamination (100%, all plans) | I4: no `@field_validator` on `consequences` to detect/strip review text |
| N3 — llama3.1 bracket contamination in call-3 | No direct code cause found; likely a prompt-context interaction; see S2 for signal loss |
| N4 — Run 29 gemini initial config failure (all 5 plans fail first wave) | I5: no pre-flight model validation; I6: stale "paid" alias in LLM config |
| N5 — qwen3 options label-like and short | No code cause; this is model behavior under the current prompt |
| P2 — haiku hong_kong recovery inferred as auto-correction | S1: `check_review_format` has no auto-prepend; recovery may be prompt-driven, not code-driven |
| insight_codex: summary exact-format compliance 0/15 (runs 25–30) | B2: `DocumentDetails.summary` field description directly contradicts the system prompt format |
| insight_codex C2: JSON repair path for truncated responses | I1: adding EOF to `_TRANSIENT_PATTERNS` gives retry without requiring a repair path |
| insight_codex C3: post-parse lint for field bleed | I4: `@field_validator` on `consequences` |
| insight_claude C3: dead generation of `strategic_rationale`/`summary` | I2, I3: remove or slim these fields from `DocumentDetails` |
| insight_claude C4: fix gemini model name config | I6 |
| Parallel-run data integrity | B1: `set_usage_metrics_path()` race condition when `workers > 1` |

---

## Summary

The two confirmed bugs are:

**B1** (runner.py:106) is a thread-safety defect: `set_usage_metrics_path()` modifies
global state outside `_file_lock`, while the related dispatcher call is protected.
With `workers > 1` this silently routes usage metrics to the wrong plan's file or
drops them entirely. It does not affect correctness of lever output, but corrupts
the observability data.

**B2** (identify_potential_levers.py:113) is the most impactful: the `summary` field's
`description=` text in the Pydantic schema directly contradicts the system prompt's
required `Add '...' to [lever]` format. Because structured LLMs use the field
description as their primary per-field instruction, the description wins — producing
0/15 summary format compliance in five of seven model runs. Fixing the description
(or removing the field) is the minimal change to address the batch's largest
instruction-following gap.

The highest-value improvement is **I1**: adding `"eof while parsing"` to
`_TRANSIENT_PATTERNS` is a one-line change in `llm_executor.py` that converts
gpt-oss-20b's chronic parasomnia failure from permanent plan loss to a retried
attempt. Combined with **I2** (removing `strategic_rationale` dead generation) and
**I3** (fixing or removing the `summary` field), the per-call token budget shrinks,
reducing timeout risk on verbose plans like parasomnia.

**S1** is an open question: the auto-correction described in the iteration-17 title
and inferred by insight_claude's analysis is not present in `check_review_format`.
The code only rejects. Synthesis should confirm whether haiku's hong_kong recovery
came from a prompt change or from a code change in another file not reviewed here.
