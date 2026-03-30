# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — UUID contamination in `full_lever_context_str` (C3 not implemented)

**File:** `enrich_potential_levers.py:190`

```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

The full context string exposes raw UUIDs alongside lever names. This string is injected into every batch prompt at line 224, so models see UUID patterns in the "full list" section and then copy them into free-text `synergy_text` / `conflict_text` fields when referencing other levers. The fix (`f"- {lever.name}"`) removes the UUID from the context while keeping it only in the per-lever batch details (line 214: `f"Lever ID: {lever.lever_id}\n"`), so the ID-echo mechanism for result matching still works.

Impact: llama3.1 89%, gemini 34%, gpt-oss-20b 53% UUID contamination in free-text fields. This is the highest-impact unfixed bug.

---

### B2 — C1/C2 interaction: `num_output` is the wrong metric for batch-size decisions

**File:** `enrich_potential_levers.py:175–185`, specifically line 181

```python
num_output = probe_llm.metadata.num_output
if num_output < SMALL_OUTPUT_THRESHOLD:
    batch_size = SMALL_OUTPUT_BATCH_SIZE
```

`num_output` reflects LlamaIndex's `max_tokens` setting — it is the maximum output budget the framework passes to the provider, not the model's actual context-window capacity. PR #453's C1 change bumped `max_tokens` for gpt-oss-20b from 8192 → 128000, which inflated `num_output` from 8192 to 128000. The check `128000 < 16384` is now `False`, so C2's protective batch reduction does **not** trigger for gpt-oss-20b despite its `context_window=3900`.

The correct metric for batch-size decisions is `context_window` (the model's actual token budget per call). C1 changed `max_tokens` (output limit); C2 used `max_tokens`/`num_output` as a proxy for total context capacity. These are semantically different. The two changes coupled in a way that silently disables C2 for exactly the model it was designed to protect.

Concrete evidence: gpt-oss-20b's metadata post-C1 shows `"context_window": 3900, "num_output": 128000` (see `history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`). The model runs with `batch_size=5` and fails 3/5 plans via `empty_response`.

---

### B3 — `Lever.consequences` field description contradicts OPTIMIZE_INSTRUCTIONS on English-keyword guidance

**File:** `identify_potential_levers.py:113–119`

```python
consequences: str = Field(
    description=(
        ...
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        "those belong exclusively in review_lever. "
        ...
    )
)
```

OPTIMIZE_INSTRUCTIONS (lines 86–92) explicitly warns:

> "A Pydantic field description containing a structural phrase (e.g. 'name the core tension') is read as a literal instruction — models start every output with 'The tension is…'. Describe the required content … not the expected sentence structure."

The `consequences` description names the exact banned phrases (`'Controls ... vs.'`, `'Weakness:'`) inline, violating this guideline. Small models read the field description as a prompt template and begin echoing these forbidden phrases, creating the very artifacts the prohibition is trying to prevent. The same problem exists in the `LeverCleaned.consequences` field at lines 208–216 (exact duplicate). The `check_review_format` validator was correctly updated to avoid English keywords, but the field descriptions were not.

---

### B4 — `_run_plan_task` per-plan log file captures the wrong thread

**File:** `runner.py:543–546`

```python
thread_filter = _ThreadFilter(threading.current_thread().ident)
file_handler.addFilter(thread_filter)
root_logger.addHandler(file_handler)
```

`_run_plan_task` sets up a log filter for **its own** thread ident, then immediately submits the actual work to an inner `ThreadPoolExecutor(max_workers=1)` (line 555). All log records from `run_single_plan` originate in the **inner executor thread**, whose ident is different from `_run_plan_task`'s ident. The `_ThreadFilter` rejects them. The per-plan `log.txt` file captures only the handful of log calls emitted in `_run_plan_task` itself (before and after `future.result()`), missing all the detailed LLM execution logs. This is a debugging quality regression introduced by the timeout-wrapping mechanism.

---

## Suspect Patterns

### S1 — Word-count target in `LeverCharacterization.description` promotes the padding OPTIMIZE_INSTRUCTIONS warns against

**File:** `enrich_potential_levers.py:123–124`

```python
description: str = Field(
    description="A comprehensive description (80-100 words) of the lever's purpose, scope, and key success metrics."
)
```

OPTIMIZE_INSTRUCTIONS line 71–73 documents: "Word-count padding. Models inflate to hit the 80-100 word target with filler phrases." This field description directly mandates the word count that causes padding. The same target is repeated in `ENRICH_LEVERS_SYSTEM_PROMPT` line 154. Repeating an already-known-bad pattern in both the field description and the system prompt amplifies the behavior.

---

### S2 — Silent lever loss when LLM echoes wrong `lever_id`

**File:** `enrich_potential_levers.py:247–255`

```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update({...})
    else:
        logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
```

If the LLM returns a truncated, reformatted, or hallucinated UUID in `LeverCharacterization.lever_id`, the lookup fails silently (only a warning is logged). At the assembly step (lines 287–294), levers without `description/synergy_text/conflict_text` are logged as errors and dropped. The user sees a reduced lever count with no clear explanation. Because the batch details at line 214 include the full UUID (`f"Lever ID: {lever.lever_id}\n"`), most models echo it correctly, but the failure mode is invisible when it occurs.

---

### S3 — `_run_levers` false-positive warning at `actual_calls < 3`

**File:** `runner.py:127–133`

```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

The adaptive loop targets `min_levers=15` with `max_calls=5`. A model producing 8+ levers per call reaches 16 levers in 2 calls and stops early — a completely normal success. This triggers the `actual_calls < 3` warning for every such run, producing misleading "partial recovery" events in `events.jsonl`. The warning was designed for error recovery (fewer calls than expected because earlier calls failed), but it conflates early-stop-on-success with failure.

---

### S4 — `execute_function` closure captured by reference inside `enrich_potential_levers.py` while loop

**File:** `enrich_potential_levers.py:234–242`

```python
def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)   # captures outer name
    ...

result = llm_executor.run(execute_function)
```

`chat_message_list` is a name in the enclosing scope, captured by reference. Since `execute_function` is called immediately via `llm_executor.run()` in the same iteration, the value is current and correct. However, if `llm_executor.run()` were ever to defer or retry across loop iterations (e.g., an async refactor), the closure would capture a stale `chat_message_list`. The same pattern exists in `identify_potential_levers.py:319–326` where `messages_snapshot` is explicitly captured to prevent this. For consistency and safety, `enrich_potential_levers.py` should take the same approach.

---

## Improvement Opportunities

### I1 — C3: Strip UUID from `full_lever_context_str`

**File:** `enrich_potential_levers.py:190`

Change:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
to:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

This is a one-line fix with high expected impact. The per-lever batch details at lines 213–219 still include `lever.lever_id`, so the ID-echo and map-lookup mechanism is unaffected. The UUID is only removed from the full-list context string where it causes copy contamination in free-text fields.

---

### I2 — C4: Use `context_window` alongside `num_output` for adaptive batch size

**File:** `enrich_potential_levers.py:98–105`, `175–185`

Add a `SMALL_CONTEXT_THRESHOLD` constant (e.g., `8000`) and also check `context_window`:

```python
SMALL_CONTEXT_THRESHOLD = 8000   # new, near line 104

# Inside execute(), probe both dimensions:
num_output = probe_llm.metadata.num_output
context_window = probe_llm.metadata.context_window
if num_output < SMALL_OUTPUT_THRESHOLD or context_window < SMALL_CONTEXT_THRESHOLD:
    batch_size = SMALL_OUTPUT_BATCH_SIZE
```

This decouples C2 from C1's `max_tokens` bump: gpt-oss-20b's `context_window=3900 < 8000` would still trigger `batch_size=2` regardless of how large `max_tokens`/`num_output` is. OPTIMIZE_INSTRUCTIONS should record this as a known infrastructure trap (see PR #453 description for proposed wording).

---

### I3 — Add anti-echoing instruction to `ENRICH_LEVERS_SYSTEM_PROMPT`

**File:** `enrich_potential_levers.py:146–158`

llama3.1 at 0.76× baseline description length is improving but still below 1.0×. OPTIMIZE_INSTRUCTIONS (lines 82–87) documents consequence echoing as a known problem, but the system prompt does not guard against it. Add to Output Requirement 1:

```
**`description`:** (80-100 words) … The description must add new context
beyond what `consequences` states — do not summarize or rephrase the
consequences field. Ground the description in the lever's mechanism, scope,
and measurable success criteria.
```

---

### I4 — Match enrichment results by lever name instead of UUID, or validate UUID format

**File:** `enrich_potential_levers.py:121`, `248`

The current approach requires the LLM to echo back a 36-character UUID. An alternative: include the UUID only as a comment in the batch prompt (`# lever_id: <uuid>`) and match by `lever.name` instead. Name matching is more robust to minor formatting variations. If UUID matching is retained, add a lightweight regex format check (`[0-9a-f-]{36}`) before the map lookup to catch hallucinated IDs early with a better error message.

---

### I5 — `_run_enrich` lacks a `partial_enrichment` event for incomplete lever sets

**File:** `runner.py:165–185`

When `EnrichPotentialLevers.execute()` silently drops levers (because characterization failed or `lever_id` didn't match), the `PlanResult` shows `status="ok"` with the full `batches_succeeded` count. There is no signal in `events.jsonl` that only N of M levers were enriched. Adding a `partial_enrichment` event analogous to the `partial_recovery` event for levers (line 577) would make these failures visible in analysis.

---

## Trace to Insight Findings

| Code location | Insight observation |
|---|---|
| `enrich_potential_levers.py:190` (B1) | N3: "llama3.1 emits full UUIDs in 31/35 levers' synergy/conflict fields (89% rate)"; UUID contamination table shows gemini 34%, gpt-oss-20b 53% |
| `enrich_potential_levers.py:181` (B2) | N1: "C1/C2 interaction bug: max_tokens bump disables adaptive batch for gpt-oss-20b"; gpt-oss-20b runs with batch_size=5 despite context_window=3900 |
| `enrich_potential_levers.py:181` (B2) | N2: gpt-oss-20b fails 3/5 plans via empty_response; N2 notes the possible cause is max_tokens=128000 >> context_window=3900 causing provider rejection |
| `identify_potential_levers.py:113–119` (B3) | Relates to OPTIMIZE_INSTRUCTIONS lines 86–92 ("Field-description template lock") — the `consequences` field description names the exact phrases it wants to ban |
| `runner.py:543–546` (B4) | Not directly observed in this run's insight, but explains why per-plan log.txt files would be empty if debugging were needed |
| `enrich_potential_levers.py:123–124` (S1) | P4: llama3.1 description length 0.76× — the word-count target in the field description promotes padding, keeping descriptions short and formulaic |
| `enrich_potential_levers.py:247–255` (S2) | UUID contamination evidence: if LLM returns wrong lever_id, lever silently dropped rather than matched by name |
| `runner.py:127–133` (S3) | P4: llama3.1 completing in 2 calls (8+ levers/call) would emit spurious "partial_recovery" warnings |

---

## PR Review

**PR #453: "Adaptive batch size, guarded retry, and max_tokens bump for enrich step"**

### C1 — max_tokens bump (baseline.json): PARTIALLY CORRECT

The bump from 8192 → 128000 correctly removes the hard truncation barrier for gpt-oss-20b on providers that accept large `max_tokens`. For 2/5 plans it works (gta_game, silo), producing correct complete JSON (3173–7924 output tokens per batch). However, the analysis shows the PR does not validate that `max_tokens` does not exceed `context_window`. Setting `max_tokens=128000` when `context_window=3900` causes some OpenRouter providers to return empty_response rather than truncating. A more conservative bump (e.g., `max_tokens=32000`) would clear the 8192 truncation while staying closer to provider expectations.

### C2 — Adaptive batch size (`enrich_potential_levers.py:175–185`): FLAWED BY DESIGN

The implementation is correct as written — it probes `num_output` and applies `SMALL_OUTPUT_BATCH_SIZE` when below the threshold. The flaw is in the choice of metric: `num_output` is `max_tokens` (an LlamaIndex output budget setting), not `context_window` (the model's actual per-call token capacity). These are different dimensions. C1's simultaneous inflation of `max_tokens` from 8192 → 128000 makes C2's threshold check trivially false for gpt-oss-20b, defeating the protection intended for it. The two changes were not designed as a coupled unit.

**The correct fix is C4 (I2 above):** check `context_window` in addition to `num_output`.

### B4 — Guarded retry (`enrich_potential_levers.py:98–100, 262–266`): CORRECT

`MAX_RETRY_DEPTH=1` and `MAX_RETRY_BUDGET_SECONDS=300` are well-chosen. The implementation correctly checks `depth < MAX_RETRY_DEPTH` and `elapsed < MAX_RETRY_BUDGET_SECONDS` before splitting. The 3×600s timeout cascade from PR #452 is fully eliminated: gpt-oss-20b now fails 3 plans in <2s each (fast empty_response) vs. 600s each before. This is the strongest positive change in the PR.

One edge case: the `retry_start_time` is set once at the top of `execute()` (line 201), not per-batch. This means the 300s budget is shared across all batches, not per-batch. For a plan with many levers and early batch failures, later batches have less retry budget. This is intentional (a global budget prevents runaway retries), but could cause legitimate late batches to skip retry when the budget is exhausted by early failures. The current behavior is safe but slightly conservative.

### D5 — Accurate batch counting (`runner.py:184`): CORRECT

`calls_succeeded=result.batches_succeeded` correctly reads the actual batch count from `EnrichPotentialLevers`. This was already fixed by PR #452 per analysis 55; the PR description's claim to fix it is redundant but the implementation is correct.

### C3 / OPTIMIZE_INSTRUCTIONS — UUID fix: NOT IMPLEMENTED

The PR description does not mention C3. The UUID contamination fix (`f"- {lever.name}"` at line 190) was documented as a priority in analysis 55 but is absent from this PR. llama3.1 UUID contamination remains at 89%, gemini at 34%.

---

## Summary

**For `enrich_potential_levers.py` (the PR target):**

- **B1** (line 190): UUID in `full_lever_context_str` is the highest-impact unfixed bug. One-line fix. Not included in PR #453.
- **B2** (line 181): C2's `num_output` threshold is the wrong metric; C1 inflated it for gpt-oss-20b, disabling the protection. Should use `context_window` instead of / in addition to `num_output`. This is the core C1/C2 coupling flaw.
- **S1** (line 123): Word-count target in `description` field description is documented as causing padding but is retained unchanged.
- **S2** (line 248): Silent lever loss when LLM echoes wrong UUID deserves a better failure path.

**For `identify_potential_levers.py`:**

- **B3** (lines 113–119, 208–216): `consequences` field description names the exact English phrases it wants banned, contradicting OPTIMIZE_INSTRUCTIONS lines 86–92 on field-description template lock.
- **S3** (runner.py line 130): `actual_calls < 3` warning fires on normal 2-call early-stop completions, creating misleading `partial_recovery` events.

**For `runner.py`:**

- **B4** (lines 543–546): `_ThreadFilter` captures `_run_plan_task`'s thread ident but the actual plan work runs in the inner executor thread, making per-plan `log.txt` files nearly empty.

**PR #453 assessment:**
The guarded retry (B4) is a clear win — it eliminates 1800s of wasted time and is correctly implemented. The max_tokens bump (C1) partially works. The adaptive batch size (C2) is undermined by its own companion change (C1), leaving gpt-oss-20b unprotected. The C3 UUID fix and C4 context_window threshold fix are the most important follow-ups.
