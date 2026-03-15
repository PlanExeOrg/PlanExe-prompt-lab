# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Race condition: `set_usage_metrics_path` called outside lock (`runner.py:106`)

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # line 106 — OUTSIDE lock

with _file_lock:                          # line 108
    dispatcher.add_event_handler(track_activity)   # line 109

t0 = time.monotonic()
try:
    ...
    result = IdentifyPotentialLevers.execute(...)   # line 114 — OUTSIDE lock
```

`set_usage_metrics_path` sets a module-level global. If `workers > 1` (parallel plans), multiple threads each call `set_usage_metrics_path` concurrently without the lock, then all call `IdentifyPotentialLevers.execute` concurrently. Each thread overwrites the global path with its own value. Usage metrics from one plan end up appended to a sibling plan's file. The comment at line 98 explicitly acknowledges the global-state risk ("so we hold a lock while configuring and running") but the implementation only locks the event-handler registration, not the metrics path or the actual execution.

The `_file_lock` must wrap both `set_usage_metrics_path` and `IdentifyPotentialLevers.execute` — or, better, the usage metrics path must be made thread-local.

### B2 — No partial result saved on multi-call failure (`identify_potential_levers.py:229–238`)

The `execute()` loop makes 3 sequential LLM calls. If call 1 and call 2 succeed but call 3 raises, the `LLMChatError` propagates out of `execute()` immediately. The `responses` list built so far is abandoned; neither `save_raw` nor `save_clean` is ever called. Call 1 and call 2's levers are discarded with no trace on disk.

The runner's `except Exception` block at `runner.py:130` captures only `str(e)` in the `PlanResult`. No raw output is written for the partial work. This explains why the `outputs/` directory is empty for failed plans (e.g. run 81).

### B3 — `max_length=7` Pydantic constraint hard-fails instead of truncating (`identify_potential_levers.py:78–82`)

```python
levers: list[Lever] = Field(
    min_length=5,
    max_length=7,
    description="Propose 5 to 7 levers."
)
```

When a model returns 8 levers, Pydantic raises `ValidationError: List should have at most 7 items after validation, not 8`. This propagates through `execute()` as an uncaught exception (it's not a `PipelineStopRequested`) and causes the whole plan to fail. The first two calls' valid levers are discarded (see B2). A simple pre-validation truncation to 7 would preserve all valid content. This is the direct cause of run 87's `gta_game` failure.

### B4 — `generated_lever_names` accumulates without deduplication (`identify_potential_levers.py:240`)

```python
generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
```

If a model returns a name that was already in `generated_lever_names` (despite the blacklist prompt — possible for non-compliant models), that name is added again. The next call's blacklist prompt then lists it twice: `"name1", "name1", …`. This is harmless in practice but makes the deduplication contract unclear and wastes prompt tokens.

---

## Suspect Patterns

### S1 — Each LLM call is a fresh conversation; no assistant turn is threaded through (`identify_potential_levers.py:209–215`)

```python
call_messages = [
    system_message,
    ChatMessage(role=MessageRole.USER, content=prompt_content),
]
```

Calls 2 and 3 carry only a list of names to avoid, not the actual content from call 1's response. The model starts fresh every time. This means:
- Weaker models (run 82, llama3.1) can produce structurally identical levers under different names because they have no context for what was already said.
- The blacklist prevents exact name reuse but allows near-duplicate concepts and formulaic option structures to repeat verbatim across calls.

Including the prior assistant turn (`ChatMessage(role=MessageRole.ASSISTANT, content=json.dumps(prior_response.model_dump()))`) would give later calls genuine context, enabling semantic anti-duplication rather than just name anti-duplication.

The memory context for this project notes "iteration 2, fix assistant turn serialization" — this pattern is the code-level root of that concern.

### S2 — Unused loop counter `i` (`identify_potential_levers.py:252`)

```python
for i, lever in enumerate(levers_raw, start=1):
```

`i` is never referenced in the loop body. `lever_id` is generated via `uuid.uuid4()` independently. Dead variable.

### S3 — `track_activity_path.unlink` deletes the tracking file (`runner.py:143`)

```python
track_activity_path.unlink(missing_ok=True)
```

This runs unconditionally in the `finally` block, erasing per-plan activity data regardless of success or failure. For failed plans this removes the only timing/token signal that would help diagnose whether the failure was a context-limit truncation, a slow network stall, or a model-side rejection. Preserving the file on error would improve auditability.

### S4 — Content validation is entirely absent before `save_clean` (`identify_potential_levers.py:304–306`)

```python
def save_clean(self, file_path: str) -> None:
    levers_dict = self.lever_item_list()
    Path(file_path).write_text(json.dumps(levers_dict, indent=2))
```

Any `Lever` that passes Pydantic schema validation (correct field types and list lengths) is saved unconditionally — including levers whose `consequences` field contains review text (`Controls … vs. … Weakness: …`), options that are short labels rather than full sentences, and consequences that lack a measurable systemic clause. The prompt's quality contract is not checked in code at all.

---

## Improvement Opportunities

### I1 — Truncate over-limit lever lists instead of hard-failing (`identify_potential_levers.py:78–82`)

Before constructing the `DocumentDetails` result from the structured LLM response, detect a `ValidationError` whose message matches "List should have at most N items" and truncate the levers list to `max_length` (7) before re-validating. This converts run 87's gta_game failure class into a partial success with no content loss.

Alternatively, catch the `ValidationError` in the `execute()` loop at the call-level, truncate `chat_response.raw.levers` to 7, and continue the loop rather than raising.

### I2 — Add post-generation content checks before `save_clean`

Log (or optionally retry) when:
- Any `lever.consequences` contains `"Controls "` or `"Weakness:"` (review bleed-in, run 85 class).
- Any `lever.options` element is shorter than 50 characters (label-like options, run 82 class).
- Any `lever.consequences` lacks both `"Systemic:"` and a quantitative signal (no `%`, no digit followed by a unit word).

These checks do not require schema changes — just string inspection in `save_clean` or a `validate()` method on `IdentifyPotentialLevers`. Findings can be written to a `002-10-quality_warnings.json` sidecar file so that the analyzer has machine-readable signals rather than requiring manual inspection.

### I3 — Save failed raw model text to disk (`runner.py:130–138` / `identify_potential_levers.py:229–238`)

When `execute()` raises, the runner catches the exception and writes only `str(e)` to `outputs.jsonl`. The model's raw response — whether it was an empty string (run 81), truncated JSON (run 83), or an over-limit list (run 87) — is gone. Writing the raw text (or the partial `responses` list accumulated so far) to `002-9-potential_levers_raw_partial.json` would give analysts direct evidence for root-cause classification without requiring another run.

### I4 — Annotate merged output with `call_count` field

The `to_dict()` / `save_raw()` output does not record how many LLM calls contributed to the merged lever list. Analysis tools comparing `002-10-potential_levers.json` to per-call expectations (max 7 levers each) currently cannot distinguish a 3-call merge from a 1-call result. Adding `"call_count": len(self.responses)` to `to_dict()` makes the multi-call architecture explicit and prevents false constraint-violation reports from automated analysis.

### I5 — Constant `total_calls = 3` ignores diminishing returns (`identify_potential_levers.py:192`)

Three calls always run unconditionally, targeting 15–21 levers per plan. If a downstream deduplication step will reduce that to 8–12 anyway, the third call is often pure overhead. An early-exit check after each call (`if len(generated_lever_names) >= min_levers_threshold: break`) would save latency without reducing final quality.

---

## Trace to Insight Findings

| Code location | Insight observation |
|---|---|
| **B3** `identify_potential_levers.py:78–82` (`max_length=7` hard-fails) | Directly causes insight_claude §6 and insight_codex N1 (run 87 `gta_game` fails with "List should have at most 7 items after validation, not 8"). Retry config (PR #283) cannot fix this because the failure is a schema constraint, not a transient network fault. |
| **B2** `identify_potential_levers.py:229–238` (no partial save on failure) | Explains why runs 81, 83, 87 produce empty `outputs/` directories for their failed plans — no raw text is written even when earlier calls succeeded. Directly cited by insight_codex C3. |
| **S4** `identify_potential_levers.py:304–306` (no content validation in `save_clean`) | Root cause of insight_claude §4 and insight_codex N3: run 85's `consequences` field contains `"Controls … Weakness: …"` review text. The schema allows any string; no code guard exists. Also explains why run 82's label-like 2-word options pass through silently — schema only checks list length, not option content. |
| **S1** `identify_potential_levers.py:209–215` (no assistant turn threading) | Contributes to insight_claude §2 and insight_codex N2 (run 82): weaker models produce formulaic, repetitive content across calls because each call starts fresh with no prior output visible. The model cannot avoid conceptual repetition, only exact name repetition. |
| **B1** `runner.py:106` (race condition on usage metrics path) | Would corrupt `usage_metrics.jsonl` for any run using `workers > 1`. Not directly observed in insight artifacts (all analyzed runs likely used `workers = 1`) but is latent and will manifest when a model config enables parallel plans. |
| **I3** (no raw save on failure) | Directly cited as insight_codex C3: "outputs.jsonl gives only the terminal error summary … hard to inspect what the model actually emitted." |
| **I4** (no `call_count` annotation) | Directly cited as insight_claude C1: analysts "will incorrectly flag merged counts as violations" without knowing how many calls merged into the final file. |
| **B4** `generate_lever_names` accumulates duplicates | Minor contributor to the name blacklist becoming noisy in later calls. Not a content-quality driver but adds noise to calls 2 and 3 prompts. |

---

## Summary

The two most impactful bugs are:

1. **B3** (schema rejects 8-lever responses instead of truncating): directly causes plan failures for otherwise high-quality models (run 87 class). A one-line truncation before validation would fix this.

2. **S4 / I2** (no content validation in `save_clean`): the cleaner trusts any schema-valid payload. This is why run 85's consequence-review contamination and run 82's label-like options pass silently into the final artifact. Post-generation content checks are the highest-leverage code-side improvement available.

Secondary concerns: **B2** (no partial save on failure) makes it harder to debug error classes and is what insight_codex C3 specifically asks for. **B1** (race condition on usage metrics path) is a correctness bug that will surface as soon as parallel execution is enabled.

The multi-call architecture (**S1**) is a structural issue where calls 2 and 3 lack the content of prior assistant turns. This widens the quality gap between weak and strong models: strong models resist conceptual repetition via instruction-following; weak models repeat structures with only names changed.
