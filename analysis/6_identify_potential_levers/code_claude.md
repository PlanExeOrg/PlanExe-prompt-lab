# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — No validator enforcing exactly-5-levers-per-call constraint
**File:** `identify_potential_levers.py:74–76`

```python
levers: list[Lever] = Field(
    description="Propose exactly 5 levers."
)
```

The field description instructs the LLM to produce exactly 5 levers, but there is no Pydantic `field_validator` (or `min_length`/`max_length` annotation) to enforce this at parse time. Pydantic will accept a list of any length. When a model returns 6 levers in a single response, the code at lines 248–250 blindly extends the flat list:

```python
levers_raw: list[Lever] = []
for response in responses:
    levers_raw.extend(response.levers)
```

A 6-lever response across 3 calls produces 16 total levers instead of 15, which then propagates intact into the saved `002-10-potential_levers.json`. There is no count check anywhere in `execute()` or `save_clean()`.

---

### B2 — Global `set_usage_metrics_path` modified outside the file lock (race condition when `workers > 1`)
**File:** `runner.py:106, 140`

```python
# Line 106 — outside the lock
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")

with _file_lock:                          # Line 108
    dispatcher.add_event_handler(track_activity)  # Line 109
```

`set_usage_metrics_path` writes to a module-level global. When `workers > 1`, multiple threads call `run_single_plan` concurrently. Because the path assignment is not protected by `_file_lock`, two threads can interleave:

1. Thread A calls `set_usage_metrics_path(path_A)`
2. Thread B calls `set_usage_metrics_path(path_B)` — overwrites the global
3. Thread A's LLM activity is now logged to `path_B` instead of `path_A`

The same race applies to the `set_usage_metrics_path(None)` call in the `finally` block (line 140), which can null out the path while another thread's LLM call is in flight, silently dropping metrics.

The dispatcher `add`/`remove` calls are correctly protected by `_file_lock`, making the asymmetry with `set_usage_metrics_path` clearly a bug.

---

### B3 — `finally` cleanup of `dispatcher.event_handlers` via direct list access
**File:** `runner.py:142`

```python
dispatcher.event_handlers.remove(track_activity)
```

`dispatcher.event_handlers` is accessed as a raw list. If `remove()` is called and `track_activity` is not present (e.g., `add_event_handler` raised before the `try` block was entered), this raises `ValueError` and masks the original exception. The `add` call at line 109 precedes the `try` block, so a failure there bypasses the `finally` entirely, but if a future refactor moves the boundary this becomes a silent exception-swallowing bug.

---

## Suspect Patterns

### S1 — `summary` is `Optional[str]` with default `None`
**File:** `identify_potential_levers.py:77–80`

```python
summary: Optional[str] = Field(
    default=None,
    description="Are these levers well picked? ..."
)
```

Because `summary` has a default of `None`, models that skip the field pass Pydantic validation without error. The system prompt (line 146–148) instructs models to produce a summary, but a schema-level Optional gives weaker models a valid escape hatch. Codex insight confirms 14 null summaries in run 47, 10 in run 48, and 4 in run 51.

---

### S2 — `strategic_rationale` is `Optional[str]` with default `None`
**File:** `identify_potential_levers.py:70–73`

Same pattern as S1. `strategic_rationale` was null in 100% of responses across all 7 models in prior analysis batches. Run 52 is the first confirmed non-null value. The insight poses the question (Q2) of whether a schema change caused this — but the current code shows it is still `Optional[str]` with `default=None`, meaning the model is still free to omit it. If non-null output is desired, the field should be required.

---

### S3 — Assistant turn serialization falls back to `model_dump_json()` when `message.content` is falsy
**File:** `identify_potential_levers.py:233–241`

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

For structured LLM outputs, `message.content` may be `None` or empty for certain back-ends (some providers return the structured object in `raw` without a text `content`). When that happens, the fallback `model_dump_json()` inserts a full JSON-serialized `DocumentDetails` object into the assistant turn. Depending on the model, this JSON-as-text representation of the previous response may differ from what the model originally produced, potentially confusing models on subsequent calls. For models with conversation conditioning (notably qwen3-30b), this could reinforce or reproduce baseline patterns (insight N5, E5).

---

### S4 — No in-pipeline deduplication of lever names
**File:** `identify_potential_levers.py:3–5, 248–250`

The file docstring acknowledges: "The output contains near duplicates … The deduplication is done in the `deduplicate_levers.py` script." The `execute()` method appends the full list of generated lever names to `generated_lever_names` (line 243) and includes them in subsequent call prompts to reduce exact duplicates. However, this is advisory only — the model may still produce near-duplicate names (semantically equivalent with different phrasing), and no deduplication occurs inside `execute()`. The 16-lever output from run 52 is saved directly without any count or identity check.

---

### S5 — `LLMExecutor` constructed with no retry or validation configuration
**File:** `runner.py:93–94`

```python
llm_models = LLMModelFromName.from_names(model_names)
llm_executor = LLMExecutor(llm_models=llm_models)
```

No retry count, no parse-error recovery, no per-call timeout. When a model returns unparseable output (nemotron's `"Could not extract json string from output: ''"` in run 46), the exception propagates immediately to `PlanResult(status="error")` without any retry attempt. Five consecutive full-batch failures for nemotron waste ~8 minutes per batch with no mitigation.

---

## Improvement Opportunities

### I1 — Add a `field_validator` to enforce exactly-5-levers-per-response
**File:** `identify_potential_levers.py` — `DocumentDetails.levers`

Add a Pydantic validator that raises `ValueError` when `len(levers) != 5`. This would cause the structured-output layer to reject and retry (or raise to the caller) instead of silently accepting 6-lever responses. Alternatively, use Pydantic v2 `min_length=5, max_length=5` annotation on the `list[Lever]` field.

Expected effect: eliminates the 16-lever artifact (run 52 hong_kong_game plan).

---

### I2 — Add a minimum word/character floor to the `options` field description
**File:** `identify_potential_levers.py:43–46`

Current description says "Each option must be a complete strategic approach (a full sentence with an action verb), not a label." This is qualitative. llama3.1 still produces 2–3-word labels averaging 18 chars (insight N3, E6). Adding a concrete minimum — e.g., "Each option must be at least 12 words describing a concrete approach" — gives weaker models a quantitative target to aim for.

Expected effect: may push llama3.1 option length from ~18 chars toward a longer minimum, though capacity constraints may limit compliance.

---

### I3 — Make `summary` a required field (remove `Optional` / `default=None`)
**File:** `identify_potential_levers.py:77–80`

Changing `summary: Optional[str] = Field(default=None, ...)` to `summary: str = Field(...)` removes the escape hatch that allows models to omit it. Pydantic will reject responses without a `summary` value, forcing a re-generation or raising an error the caller can handle.

Expected effect: eliminates null summaries in runs that currently produce them (14 in run 47, 10 in run 48, 4 in run 51).

---

### I4 — Add a post-generation validator for consequence field contamination
**File:** `identify_potential_levers.py` — after lines 252–263

After cleaning levers, add a check that rejects or flags any `lever.consequences` string containing the phrases `Controls` followed by `vs.` or the literal `Weakness:`. These are the exact markers that identify review-text leakage from qwen3-30b (insight N2, C1 in insight file). A post-generation filter could either strip the contaminated tail or log a warning before saving.

Expected effect: prevents contaminated levers from being saved to `002-10-potential_levers.json` even when the schema prohibition in the field description is ignored by the model.

---

### I5 — Protect `set_usage_metrics_path` inside `_file_lock` in `run_single_plan`
**File:** `runner.py:106, 140`

Move both `set_usage_metrics_path(...)` calls inside the `_file_lock` block, or switch from a module-level global to a thread-local or per-call parameter. The dispatcher add/remove is already locked; extending the lock to cover the path assignment removes the race condition when `workers > 1`.

---

### I6 — Add a per-call output token cap to bound verbosity for verbose models
**File:** `runner.py:93–94` or `identify_potential_levers.py:212–214`

gpt-5-nano generates 33,741 output tokens per plan (insight N4). Passing a `max_tokens` parameter when constructing the LLMExecutor (or when calling `sllm.chat()`) would cap verbosity and reduce timeout risk on harder plans. A cap of ~3,000–4,000 tokens per call should be sufficient for 5 well-formed levers while preventing the ~10× verbosity seen in run 49.

---

### I7 — Add a model skip list or capability filter to the runner
**File:** `runner.py` — `run_single_plan` or `main`

nemotron-3-nano-30b-a3b has produced 0 parseable outputs across 5 consecutive full batches (insight N1, C4). Adding an opt-in skip list (e.g., via a CLI flag `--skip-model` or a `"skip": true` field in the model config JSON) would avoid wasting 8 minutes per batch on known-failing models. The runner already reads `llm_config/*.json` for `luigi_workers` (lines 232–235); the same mechanism could carry a `skip` flag.

---

## Trace to Insight Findings

| Code location | Issue | Explains insight observation |
|---|---|---|
| `identify_potential_levers.py:74–76` (B1) | No length validator on `levers` list | Codex N: run 52 produces 16 levers (hong_kong_game); one raw response has 6 levers. Table: `Raw resp !=5` = 1 for run 52. |
| `runner.py:106, 140` (B2) | `set_usage_metrics_path` race when `workers > 1` | Silent metric loss for concurrent plan runs; usage_metrics.jsonl may contain interleaved or missing entries for runs with workers > 1 |
| `identify_potential_levers.py:77–80` (S1) | `summary: Optional[str] = None` | Claude N: null summaries in runs 47 (14), 48 (10), 51 (4). Codex table: "Null summaries" column. |
| `identify_potential_levers.py:70–73` (S2) | `strategic_rationale: Optional[str] = None` | Claude P2 / Q2: strategic_rationale null in all runs 39–45, non-null only in run 52. Still Optional in source. |
| `identify_potential_levers.py:233–241` (S3) | Fallback to `model_dump_json()` in assistant turn | Claude N5 / Codex comparison: qwen3-30b reproduces baseline levers verbatim (E5). Multi-call conditioning with JSON serialized previous output may reinforce the model's own prior responses. |
| `identify_potential_levers.py:43–46` (S1 + I2) | Options description lacks quantitative floor | Claude N3 / Codex N: llama3.1 emits 2–3-word label options (~18 chars). "Not a label" instruction is qualitative; model ignores it. |
| `runner.py:93–94` (S5) | No retry on parse failure | Claude N1: nemotron fails all 5 plans per batch with JSON extraction error. 5 consecutive full-batch failures. |
| `identify_potential_levers.py:38–39` | Prohibition already present in `consequences` description | Claude Q1: prohibition IS in source code; qwen3-30b still contaminates 100% of call-1 levers (run 50). Model ignores schema field descriptions. Confirms that a post-generation validator (I4) is needed. |

---

## Summary

**Two confirmed bugs:**

- **B1** (identify_potential_levers.py:74–76): The `levers` list has no length validator, so a 6-lever model response flows through undetected and produces a 16-lever final artifact. Fix: add `min_length=5, max_length=5` or a `field_validator`.

- **B2** (runner.py:106, 140): `set_usage_metrics_path` is not protected by `_file_lock`, causing a race condition when `workers > 1`. Usage metrics from concurrent plan runs can be written to the wrong file or silently dropped.

**Key structural gap explaining most model-quality issues:** `summary` and `strategic_rationale` are both `Optional[str]` with `default=None`. This is the root cause of null-summary regressions across multiple models and the historical absence of `strategic_rationale`. Making these required fields would eliminate the escape hatch.

**The qwen3 contamination prohibition is already in the source** (lines 38–39 of `Lever.consequences`). The fact that run 50 still shows 100% contamination confirms the model ignores schema field descriptions. A post-generation validator (I4) is the necessary complement.

**The llama3.1 label regression** is partly a model capability issue, but the lack of a quantitative minimum in the options description (I2) removes the one lever prompt engineering has over weak instruction-followers.

**The runner has no retry logic** (S5 / I6): nemotron fails reliably across five batches with a known error pattern. Basic retry-on-parse-failure would not fix a fundamentally incapable model but would reduce wasted time on transient errors.
