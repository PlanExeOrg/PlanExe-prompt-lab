# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #375 — *feat: broaden remove to include irrelevant levers, shorten justification*

---

## Bugs Found

### B1 — Total LLM failure silently produces status="ok" with all-secondary output

**Files:** `deduplicate_levers.py:198-205`, `runner.py:151-156`

```python
# deduplicate_levers.py:198-205
try:
    result = llm_executor.run(execute_function)
    batch_result = result["chat_response"].raw
    metadata_list.append(result.get("metadata", {}))
except PipelineStopRequested:
    raise
except Exception as e:
    logger.error(f"Batch deduplication call failed: {e}")
```

When the LLM call fails (network error, schema validation error, timeout), the exception is caught and logged, but `batch_result` stays `None`. Execution then falls through to the missing-decisions loop at line 228-236, which defaults every lever to `"secondary"` with the justification `"Not classified by LLM. Keeping as secondary to avoid data loss."`.

The caller (`_run_deduplicate`, runner.py:151-156) unconditionally returns:
```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=1,  # single batch call
)
```

So a complete LLM failure writes `status="ok"` and `calls_succeeded=1` to `outputs.jsonl`. The only signal that anything went wrong is the fallback justification text inside the raw output file. This means the analysis pipeline's success/failure metrics are unreliable for the deduplicate step — a run that failed entirely looks identical to a successful run from the outside.

**Fix:** At minimum, detect when all decisions come from fallback (i.e., `batch_result is None` after the try/except) and either raise the error or return `PlanResult(status="error")` instead of `status="ok"`. Alternatively, emit a `deduplication_fallback` event in `events.jsonl` so the analysis pipeline can detect it.

---

### B2 — `user_prompt` field stores only project_context, not the full prompt sent to LLM

**File:** `deduplicate_levers.py:271-272`

```python
return cls(
    user_prompt=project_context,   # ← only the project context
    ...
)
```

The actual prompt sent to the LLM is constructed at lines 179-183:
```python
user_prompt = (
    f"**Project Context:**\n{project_context}\n\n"
    f"**Levers to classify ({len(input_levers)} total):**\n{levers_json}\n\n"
    f"Classify every lever as primary, secondary, or remove."
)
```

This full string (with levers JSON appended) is what `sllm.chat(chat_message_list)` sends. But `save_raw()` stores `user_prompt=project_context`, which is only the first third of the actual input. Anyone inspecting the raw output file sees an incomplete picture of what was sent to the model — the levers JSON and instruction are absent from the saved record.

**Fix:** Change `user_prompt=project_context` to `user_prompt=user_prompt` (the full constructed string) in the `cls(...)` call at line 272.

---

## Suspect Patterns

### S1 — Justification length constraint is advisory only; weak models ignore it

**File:** `deduplicate_levers.py:83-85`

```python
justification: str = Field(
    description="Concise justification for the classification (~20-30 words)."
)
```

The PR description states "Shorter justifications: ~20-30 words (down from ~40-80). Less output = llama3.1 more likely to finish within timeout." There is no Pydantic `max_length` constraint — only a description hint that the LLM reads as a suggestion. Capable models (haiku, gpt-oss-20b) comply and produce ~18-25 words. llama3.1 produces ~40 words (N2 in insight), essentially unchanged from before the PR.

The insight notes "The mechanism is likely a Pydantic max_length constraint" — but there is none. The shorter output for API models is achieved by prompt instruction alone, which llama3.1 ignores. A hard character cap (e.g. `max_length=200`, ≈30-35 words) would enforce the constraint for all models, including llama3.1, and more reliably prevent timeout.

---

### S2 — System prompt tension between conservative and aggressive removal guidance

**File:** `deduplicate_levers.py:138-143`

```python
- When uncertain between removing and keeping, prefer secondary over remove
  to avoid discarding a potentially important lever.
- Expect to remove 25-50% of the input levers. If you classify everything as
  primary or secondary, reconsider — the input almost always contains
  near-duplicates and overlap.
```

These two instructions conflict. The first says "when in doubt, don't remove." The second says "you should expect to remove 25-50%." For weak models (llama3.1), the conservative instruction wins — the model defaults to keeping everything and produces 0 removes even when obvious redundancies exist (N1 in insight: run 71, silo, 0 removes for levers like `ee0996f6` that clearly overlap `b664e24a`).

The expected removal count guidance on line 143 is good, but it loses the argument against the more explicit "prefer secondary over remove" on line 139. Consider making the expected-removal instruction come first, and reframing the conservative tie-breaker as a secondary concern.

---

### S3 — OPTIMIZE_INSTRUCTIONS hierarchy guidance contradicts the new system prompt

**File:** `deduplicate_levers.py:55-58`

```python
- Hierarchy-direction errors. Models remove the general lever and keep
  the narrow one — reversed from correct behavior. The more general
  lever should survive; the specific one should be removed.
```

PR #375 changed the system prompt to: "When two levers overlap, keep the one that **better captures the strategic decision** and remove the other" (line 130-131). But `OPTIMIZE_INSTRUCTIONS` still documents the old rule: "The more general lever should survive." These are different criteria — strategic framing vs. generality.

Future prompt engineers reading `OPTIMIZE_INSTRUCTIONS` as a guide will apply the old "keep general" heuristic, which contradicts the current system prompt. This mismatch will make it harder to reason about and debug overlap-handling regressions.

---

### S4 — Minimum-survival warning threshold is too permissive

**File:** `deduplicate_levers.py:258-264`

```python
min_expected = max(3, len(input_levers) // 4)
```

For 18 input levers: `max(3, 18 // 4) = max(3, 4) = 4`. The warning only fires if fewer than 4 levers survive — a 78% removal rate. But `OPTIMIZE_INSTRUCTIONS` states the expected removal is 25-50%, implying 50-75% of levers should survive (9-13 from 18). The threshold should be closer to `len(input_levers) // 3` (6 from 18) to catch genuinely over-aggressive removal. The current threshold would miss a model that removes 14/18 levers.

---

### S5 — Duplicate lever name detection in identify_potential_levers is case-sensitive

**File:** `identify_potential_levers.py:364-369`

```python
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

If a model produces "Director Selection" in call 1 and "director selection" in call 2, both pass the deduplicate check and appear in the output. The second lever with an identical concept would then need to be caught by `DeduplicateLevers`. Lowercasing both the stored name and the comparison name would catch this class of near-duplicate.

---

### S6 — `partial_recovery` warning fires when fast model reaches min_levers in < 3 calls

**File:** `runner.py:546-552`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

A model that generates 8+ levers per call and reaches `min_levers=15` in 2 calls (calls_succeeded=2) emits a `partial_recovery` event — but the run was entirely successful. The same threshold in `_run_levers` at line 125 issues a `logger.warning`. These false-positive warnings create noise in `events.jsonl` and may be misread as failures during analysis. The threshold should be based on lever count, not call count, or the event should be renamed to something that more accurately reflects what happened (e.g., `early_termination` for success cases).

---

## Improvement Opportunities

### I1 — Emit a `deduplication_fallback` event when LLM failure triggers all-secondary

**Files:** `deduplicate_levers.py:204-206`, `runner.py`

When the LLM call fails and all levers fall through to secondary (B1), no event is emitted in `events.jsonl`. The analysis pipeline cannot distinguish a successful deduplicate run from a silent failure without inspecting the justification text in each output file. Adding a `deduplication_fallback` event would make this detectable without parsing output files.

---

### I2 — Emit `low_removal_rate_warning` event for deduplicate step (insight C2)

**File:** `runner.py`, after `_run_deduplicate`

The `identify_potential_levers` step emits a `partial_recovery` event for low call count. The `deduplicate_levers` step has no equivalent. Adding a `low_removal_rate_warning` event when the removal rate is < 5% for plans with ≥ 14 input levers would allow the analysis pipeline to flag llama3.1-style "0 removes despite completing" cases (N1 in insight) without manual inspection.

---

### I3 — Add post-LLM justification-lever reference check (insight C1)

**File:** `deduplicate_levers.py`, after line 225

When a lever is classified as `remove`, the justification should reference the overlapping lever (by name or ID). Adding a check that verifies the referenced lever name/ID exists in the input would catch the qwen3 justification-swap bug (N3 in insight: two levers' justifications were swapped, each describing the other). The check would not retry automatically, but could emit a `justification_mismatch_warning` event for traceability.

---

### I4 — Update OPTIMIZE_INSTRUCTIONS to match new overlap preference (S3 above)

**File:** `deduplicate_levers.py:55-58`

Replace "The more general lever should survive; the specific one should be removed" with the PR #375 rationale: "Keep the lever that better captures the strategic decision — this may be either the more general or the more specific lever, depending on which one a project manager would actually act on."

---

### I5 — Add a canary plan that exercises the "irrelevant" remove criterion

**Context:** PR #375's key new capability — removing levers that are "irrelevant to this specific plan" — produced zero irrelevant removals across 35 runs (N5 in insight). The current 5 test plans don't expose this feature.

Adding one plan with a known-irrelevant upstream lever (e.g., a software-delivery plan where upstream generated a "physical office location" lever) would allow direct validation in subsequent iterations and confirm the "irrelevant" criterion is understood correctly by models.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|----------------|-------------------|
| N1 — llama3.1 silo 0 removes despite completing | S2: "prefer secondary" vs "remove 25-50%" conflict. Conservative instruction wins for weak models. |
| N2 — llama3.1 justifications still ~40 words despite shorter-justification goal | S1: No Pydantic `max_length` on justification; advisory "~20-30 words" is ignored by llama3.1. |
| N3 — qwen3 swaps justifications between two remove-classified levers | No code check for justification-lever alignment (I3). The model confuses lever identities during batch reasoning; no validator catches it. |
| N5 — No "irrelevant" removals in any of 35 after-runs | I5: Test plans don't contain irrelevant levers; the new criterion is never triggered. |
| C2 (proposed): emit low_removal_rate_warning | I2: No such event is currently emitted for the deduplicate step. |
| P1 — llama3.1 timeout fixed | Shorter prompt descriptions + "~20-30 words" hint (S1) provide enough output reduction for API models to help llama3.1 barely complete in time, though the mechanism is fragile (no hard cap). |
| Silent total LLM failure risk | B1 + B2: failure recorded as ok, full prompt not saved. |

---

## PR Review

### Changes assessed

| PR claim | Code implementation | Assessment |
|----------|--------------------|----|
| "triaging" framing | `deduplicate_levers.py:114` — "You are triaging a set of strategic levers" | ✓ Correctly implemented |
| Broadened `remove` to cover irrelevant levers | `deduplicate_levers.py:128-131` — "or it is irrelevant to this specific plan" | ✓ Correctly implemented |
| Better overlap handling: "keep the better strategic" | `deduplicate_levers.py:131` — "keep the one that better captures the strategic decision" | ✓ Correctly implemented |
| Shorter justifications (~20-30 words) | `deduplicate_levers.py:84` — description text only; no `max_length` constraint | ⚠ Partially implemented — advisory only |
| Fallback to `secondary` instead of `primary` | `deduplicate_levers.py:234-235` — "classification='secondary'" | ✓ Correctly implemented |
| Renamed `BatchDeduplicationResult` → `DeduplicationResult` | `deduplicate_levers.py:87` | ✓ Correctly implemented |

### Gaps and edge cases

**Shorter justification (S1 / N2):** The PR description says "~20-30 words (down from ~40-80). Less output = llama3.1 more likely to finish within timeout." The implementation adds only advisory text in the Pydantic field description. For capable models this works, but llama3.1 produces ~40 words unchanged (N2). The PR achieves enough reduction that llama3.1 barely completes, but the mechanism is fragile: if a future plan has more levers or more complex content, the advisory text will be insufficient and timeouts will recur. A `max_length` constraint (e.g., 200 characters) would make this robust.

**OPTIMIZE_INSTRUCTIONS not updated (S3):** The hierarchy-direction guidance in `OPTIMIZE_INSTRUCTIONS` (line 56-58) still says "the more general lever should survive", contradicting the PR's new "keep the strategically better one" guidance. This documentation debt will confuse future optimization iterations.

**"Irrelevant" criterion untestable (N5):** The new `remove` criterion is logically correct but cannot be validated against the current 5 test plans. The PR would benefit from a note that a synthetic validation plan is needed for subsequent verification (I5).

**No regression in classification logic:** The broadened `remove` definition does not affect existing correct behavior for overlapping levers — it only adds a new trigger condition. The "prefer secondary over remove when uncertain" safeguard (line 138-140) prevents the new "irrelevant" criterion from causing over-aggressive removal. This is a safe design.

**Silent-failure risk preserved:** The PR does not address B1. The fallback text changed from "Keeping as primary" to "Keeping as secondary", which is an improvement (primary count won't be inflated), but the core issue — a total LLM failure being recorded as `status="ok"` — remains.

---

## Summary

The three highest-priority findings are:

**B1 (confirm bug):** A complete LLM call failure in `deduplicate_levers.py` is silently swallowed. All levers fall through to the secondary fallback, and `runner.py` records `status="ok"` with `calls_succeeded=1`. The run is indistinguishable from success in `outputs.jsonl`.

**B2 (confirm bug):** `save_raw()` stores only `project_context` in the `user_prompt` field, not the full prompt that includes the levers JSON. The saved output is an incomplete replay of what was sent to the LLM.

**S1 (suspect pattern, explains N2):** The PR's shorter-justification goal is implemented via advisory description text only. No Pydantic `max_length` constraint exists. Capable models comply; llama3.1 does not. This explains why llama3.1 justifications remain at ~40 words (N2) even after the PR. A character cap would make the constraint model-agnostic.

**S2/S3 (suspect patterns, explain N1):** The system prompt contains a tension between "prefer secondary over remove" and "expect to remove 25-50%", with the conservative instruction appearing first. For weak models, the conservative instruction dominates, contributing to 0-remove behavior for llama3.1 on the silo plan (N1). The `OPTIMIZE_INSTRUCTIONS` hierarchy-direction guidance also still documents the old "keep general" rule, contradicting the PR's new "keep strategically better" guidance.

The PR correctly implements its stated goals for capable models and achieves the critical llama3.1 timeout fix (P1). The gaps are in enforcement robustness (B1, S1) and documentation consistency (S3).
