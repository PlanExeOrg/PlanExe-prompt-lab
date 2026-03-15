# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Conflicting `options` cardinality between Pydantic schema and system prompt

**File:** `identify_potential_levers.py:34` vs `:90`

`Lever.options` field description:
```python
options: list[str] = Field(
    description="2-5 options for this lever."   # ← says 2-5
)
```

System prompt directive:
```python
- Each lever's `options` field must contain exactly 3 qualitative strategic choices  # ← says exactly 3
```

The Pydantic field description is embedded in the JSON schema sent to the LLM as structured output. The schema says "2-5" while the natural-language system prompt says "exactly 3". These are contradictory instructions; the LLM receives both and must arbitrate. Models that weight the schema description more heavily will generate non-3-option levers without any error being raised.

Evidence: run 26 has 14 levers with only 1 option; run 31 has at least one 1-option lever (codex insight, `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`).

---

### B2 — Per-call lever count is never validated

**File:** `identify_potential_levers.py:57-59` and `:213-229`

```python
levers: list[Lever] = Field(
    description="Propose exactly 5 levers."   # description only; no validator
)
```

There is no `@field_validator` or `model_validator` enforcing `len(levers) == 5`. A model returning 4 or 6 levers passes Pydantic validation silently, and the merge at lines 213-216 aggregates whatever count was produced. The total lever count therefore varies from the expected 15.

Evidence: codex insight notes run 31 has "a 6-lever response in raw output leading to 16 final levers." This also means `generated_lever_names` (line 209) grows by the wrong count, making the anti-duplication list for call 2/3 incorrect.

---

## Suspect Patterns

### S1 — Dispatcher event handlers are globally shared when `workers > 1`

**File:** `runner.py:104,108-109,141-143`

```python
dispatcher = get_dispatcher()           # global singleton
...
with _file_lock:
    dispatcher.add_event_handler(track_activity)
```

When `workers > 1`, multiple threads register separate `TrackActivity` instances on the same global dispatcher. Because LLM execution happens outside the lock, the dispatcher fires events to **all registered handlers simultaneously**. Every concurrent plan's LLM calls get written into every other plan's `track_activity.jsonl` file.

This is harmless in practice only because line 143 deletes the file:
```python
track_activity_path.unlink(missing_ok=True)
```
If that deletion were ever removed (e.g., to debug a parallel run), cross-plan event mixing would surface as incorrect data. The comment at lines 96-98 says "we hold a lock while configuring and running" but the lock does not cover the actual `IdentifyPotentialLevers.execute` call.

---

### S2 — `execute_function` closure captures mutable list by reference inside a loop

**File:** `identify_potential_levers.py:178-186`

```python
for call_index in range(1, total_calls + 1):
    ...
    chat_message_list.append(ChatMessage(...))

    def execute_function(llm: LLM) -> dict:
        sllm = llm.as_structured_llm(DocumentDetails)
        chat_response = sllm.chat(chat_message_list)  # captures outer list
        ...

    result = llm_executor.run(execute_function)
```

The closure is safe today because `llm_executor.run()` is synchronous and finishes before the next iteration mutates `chat_message_list`. However, if `LLMExecutor` ever becomes async or if retries delay execution, the captured list could have grown by then. A safer pattern would be to pass `chat_message_list` as a default argument: `def execute_function(llm: LLM, messages=chat_message_list)`.

---

## Improvement Opportunities

### I1 — Remove the "25% faster scaling" example from the system prompt

**File:** `identify_potential_levers.py:95`

```python
• Include measurable outcomes: "Systemic: 25% faster scaling through..."
```

This verbatim phrase is copied into the Systemic field by multiple models. Run 28 shows it in all 75 levers across 5 plans (codex: "72 uses of `25% faster`"). The example is too specific; models treat it as a fill-in template.

Suggested replacement: `"Systemic: [second-order impact with a measurable indicator, e.g., a % change or capacity shift]"`. The bracketed placeholder signals that the model should substitute its own domain-specific value, not copy the phrase.

---

### I2 — Remove the "Material Adaptation Strategy" example lever name

**File:** `identify_potential_levers.py:104`

```python
- Name levers as strategic concepts (e.g., "Material Adaptation Strategy")
```

This example is adopted verbatim as the first lever name in runs 25 and 26, even for plans where it is semantically incorrect (e.g., `hong_kong_game` film production plan). The `(e.g., ...)` construct is being interpreted as a template to copy.

Suggested replacement: `- Name levers as strategic concepts (e.g., "[Domain-Specific Strategy Name]")` or remove the parenthetical entirely and rely on the general description.

---

### I3 — Prefix prohibition is incomplete: omits "Conservative:", "Moderate:", "Radical:"

**File:** `identify_potential_levers.py:100-101,117`

```python
• Show clear progression: conservative → moderate → radical
• NO prefixes (e.g., "Option A:", "Choice 1:")
```

The directive uses "conservative → moderate → radical" as the framing, but the prohibition examples only list neutral prefixes like "Option A:". Models reasonably infer that "Conservative:", "Moderate:", "Radical:" are acceptable since they match the named progression style. Run 25 silo batch 1 confirms exactly this interpretation.

Fix: extend the prohibition list at line 117 to: `NO prefixes/labels in options (e.g., "Option A:", "Choice 1:", "Conservative:", "Moderate:", "Radical:")`.

---

### I4 — `strategic_rationale` and `summary` should be optional (or have defaults)

**File:** `identify_potential_levers.py:53-62`

```python
class DocumentDetails(BaseModel):
    strategic_rationale: str = Field(...)   # required
    levers: list[Lever] = Field(...)
    summary: str = Field(...)               # required
```

Both wrapper fields are required. When a model returns only `{"levers": [...]}` (run 30, gpt-4o-mini), Pydantic raises `ValidationError: strategic_rationale Field required; summary Field required` and the entire plan is rejected — even though the 5 levers themselves are valid and usable.

Fix: change both fields to `Optional[str] = Field(default=None, ...)`. This converts 2 of run 30's 5 failures into successes without any prompt change.

---

### I5 — No context window guard for small-context models

**File:** `runner.py:93-94` (and `identify_potential_levers.py:138`)

```python
llm_models = LLMModelFromName.from_names(model_names)
llm_executor = LLMExecutor(llm_models=llm_models)
```

No pre-flight check confirms the model's context window is large enough before dispatching plans. Nemotron-3-nano has a 3900-token context window (visible in run 25's raw metadata). Complex plans (parasomnia, hong_kong) likely exceed it, causing silent empty-output failures (all 5 plans failed in run 24).

Fix: after `llm.create_llm()`, check `llm.metadata.context_window` and skip (with a warning) any model below a minimum threshold (e.g., 8192 tokens) for this pipeline step. Alternatively, log the context window in `meta.json` at run start so failures can be diagnosed immediately.

---

### I6 — `LLMExecutor` created without `max_validation_retries`

**File:** `runner.py:94`

```python
llm_executor = LLMExecutor(llm_models=llm_models)  # max_validation_retries=0
```

The default `max_validation_retries=0` means Pydantic validation failures (run 30's missing wrapper fields, run 31's placeholder levers) never trigger a retry on the same model. `LLMExecutor` already supports `max_validation_retries` and exposes `validation_feedback` for injecting the error back into the prompt.

Fix: create the executor with `max_validation_retries=1`. When validation fails, the error feedback ("2 validation errors: strategic_rationale Field required") is injected into the next attempt's prompt, giving the model a chance to self-correct.

---

### I7 — Anti-duplication instructions cover names only, not semantic topics

**File:** `identify_potential_levers.py:163-168`

```python
names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]"
)
```

The deduplication instruction only lists lever *names*. Models can produce new names while covering near-identical topics (run 28 parasomnia: 5 of 10 cross-batch pairs are semantic duplicates, e.g., "Adaptive Facility Footprint Strategy" vs. "Localized Modular Footprint Diffusion"). Name-level uniqueness does not guarantee idea diversity.

Fix: extend the prompt for call 2 and 3 to also describe the topics already covered at a high level: `"The following TOPICS are already covered: [short descriptions]. Generate levers that address different strategic dimensions."` Even a single-sentence per-lever topic summary injected into the context would substantially reduce semantic overlap.

---

### I8 — No post-merge sanitization of the final lever list

**File:** `identify_potential_levers.py:213-229`

After the 3 LLM calls are merged into `levers_cleaned`, there is no validation of the merged artifact. The following invalid content can reach downstream pipeline stages without any error:

1. **Placeholder levers** — run 31 writes a lever literally named "Placeholder Removed - Framework Compliance" with options `["Removed"]` and review `"Structural compliance marker"` into the final `002-10-potential_levers.json` (codex insight, `:59`).
2. **Wrong option count** — run 26 levers with 1 option pass through (B1 above).
3. **Wrong total lever count** — if a call returns 6 levers (B2 above), the final file has 16 levers.

Fix: after line 229, add a post-merge filter:
- Remove levers whose name contains "Placeholder" or "Removed".
- Remove levers with option count != 3 (or log a warning and keep, but flag for downstream).
- Log a warning if `len(levers_cleaned)` != 15.

---

## Trace to Insight Findings

| Code Location | Insight Finding |
|---|---|
| **B1** `Lever.options` "2-5" vs. system prompt "exactly 3" | Codex C3: "add a post-merge sanitizer that rejects … any lever whose option count is not exactly 3"; run 26 option-count violations (14 levers with 1 option) |
| **B2** No per-call lever count validator | Codex insight: "run 31 contains a 6-lever response in raw output leading to 16 final levers" |
| **S1** Shared dispatcher, parallel workers | Does not cause output errors but explains why `track_activity.jsonl` cleanup was added (runner.py:143) |
| **I1** "25% faster scaling" example | Claude N3: "Pervasive '25% faster scaling' template leakage" in runs 26 and 28; Codex: "72 uses of `25% faster`" in run 28 |
| **I2** "Material Adaptation Strategy" example | Claude N4: name leakage across runs 25, 26 in multiple plans including hong_kong |
| **I3** Incomplete prefix prohibition | Claude N7: "Option prefix violations in some runs" — run 25 silo batch 1 uses "Conservative:", "Moderate:", "Radical:" |
| **I4** Required `strategic_rationale` / `summary` | Claude C1, Codex C1: run 30 fails 2/5 plans because model returns levers without wrapper fields |
| **I5** No context window guard | Claude C2, Codex evidence: nemotron 3900-token window → 0/5 successes run 24, 1/5 run 25 |
| **I6** `max_validation_retries=0` | Codex C2: "add extraction repair … followed by one constrained retry" |
| **I7** Name-only anti-duplication | Claude N5, Q2: "cross-call duplication … driven by … code passing the same user context to all 3 calls without diversity instructions" |
| **I8** No post-merge sanitization | Claude C3, Codex C3: run 31 placeholder lever in final artifact; run 26 single-option levers in final artifact |

---

## Summary

The code is structurally sound for the happy path (capable models on well-sized plans) but has two confirmed bugs and several gaps that become failure modes for weaker or edge-case models.

**Highest-priority fixes:**

1. **B1 / I4** — The `options` cardinality conflict (2-5 vs. exactly 3) and the required wrapper fields (`strategic_rationale`, `summary`) are the two code-level issues that most directly cause observed run failures. Both are single-line fixes with high expected impact.

2. **I1 / I2** — The "25% faster scaling" and "Material Adaptation Strategy" prompt examples are the direct source of the most pervasive content quality problem (template leakage). These are single-phrase replacements in the system prompt string.

3. **I8** — Post-merge sanitization (placeholder detection, option-count check) would prevent invalid content from silently propagating to downstream pipeline stages.

4. **B2 + I7** — Enforcing exactly 5 levers per call and extending the anti-duplication instruction to cover topics (not just names) would improve the structural consistency and semantic diversity of the merged output.

Items I3, I5, I6 are lower priority but each recovers a distinct observable failure mode (prefix labels, empty outputs from small-context models, validation errors with no retry).
