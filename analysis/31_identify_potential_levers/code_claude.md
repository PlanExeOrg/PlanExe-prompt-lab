# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`
- `llm_config/anthropic_claude.json` (supporting evidence)
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py` (supporting evidence)

PR under review: #346 — "Add lever_type and decision_axis to lever schema"

---

## Bugs Found

### B1 — `lever_type` hard validator with no fuzzy normalization
**File:** `identify_potential_levers.py:126–135`

```python
@field_validator('lever_type', mode='after')
@classmethod
def normalize_lever_type(cls, v):
    normalized = v.strip().lower()
    if normalized not in cls.VALID_LEVER_TYPES:
        raise ValueError(
            f"lever_type must be one of {sorted(cls.VALID_LEVER_TYPES)}, got {v!r}"
        )
    return normalized
```

The validator does `strip().lower()` but immediately hard-rejects anything not in the enumerated set. There is no fuzzy normalization step — no edit-distance mapping, no lookup table for semantically adjacent strings. A model returning `'coalition_building'` (directly on-topic for a sovereign identity research project) gets a full plan failure with no retry tolerance and no correction pass.

`LLMExecutor` (llm_executor.py:263–283) supports `max_validation_retries` to retry on `ValidationError`, but `IdentifyPotentialLevers.execute()` constructs its executor without setting this parameter (it uses the default `max_validation_retries=0`). So even if validation feedback were injected into a follow-up prompt, the current call site doesn't enable it.

**Direct cause of N2** (llama3.1 `coalition_building` rejection, run 24).

---

### B2 — `max_tokens: 16000` in haiku config exceeds the model's actual API output limit
**File:** `llm_config/anthropic_claude.json:34` (and line 14 for the non-pinned variant)

```json
"max_tokens": 16000
```

Anthropic claude-haiku-4-5 has an API-enforced output cap of approximately 8,192 tokens. The config requests 16,000; the API silently clamps to ~8,192. Developers reading the config see 16,000 and assume they have a generous output budget, but the actual ceiling is roughly half that.

Before PR #346, haiku's per-call response averaged roughly ~4,000 tokens — safely inside the real cap. PR #346 added `lever_type` (~15 chars) and `decision_axis` (~289 chars avg for haiku) to every lever. With 7 levers × 3 calls, this adds ~6,000–8,000 chars (~1,500–2,000 tokens) per plan. Some calls pushed above the ~8,192-token effective ceiling, causing truncated JSON. The truncation points in the event log (column 29,300 and column 43,016) are consistent with ~7,300–10,750 tokens of output at ~4 chars/token.

No code checks whether `max_tokens` exceeds the model's real output cap; no pre-call size estimate exists to warn when approaching the limit.

**Direct cause of N1** (haiku JSON-EOF truncation failures in runs 30, plans `gta_game` and `silo`).

---

### B3 — Timeout not actually enforced: `with _TPE()` blocks until thread finishes
**File:** `runner.py:491–503`

```python
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, plan_dir, output_dir, model_names, step)
    try:
        pr = future.result(timeout=plan_timeout)
    except _TE:
        logger.error(f"{plan_name}: killed after {plan_timeout}s (plan timeout)")
        pr = PlanResult(...)
```

When `future.result(timeout=plan_timeout)` raises `TimeoutError`, the correct `PlanResult` is created and execution continues — but then the `with` block exits, calling `executor.shutdown(wait=True)`. This blocks the outer runner thread until the inner LLM thread completes, which may be long after the timeout. Python's `ThreadPoolExecutor` cannot forcibly cancel a running thread, and `cancel_futures=True` only cancels queued (not started) tasks.

The net effect: `plan_timeout=600` creates the timeout result object but does not prevent blocking for the full LLM call duration. If a stuck haiku call runs for 900 seconds, the outer thread waits 900 seconds regardless of the 600-second setting.

The fix requires either: (a) manually calling `executor.shutdown(wait=False)` after catching `TimeoutError` (accepting the thread leak as unavoidable with CPython's threading model), or (b) not using the `with` block at all.

---

### B4 — `options` field description contradicts the validator's behavior
**File:** `identify_potential_levers.py:112` and `158–170`

The field description sent to the LLM says:
```
"Exactly 3 options for this lever. No more, no fewer."
```

But `check_option_count` only enforces the lower bound:
```python
if len(v) < 3:
    raise ValueError(f"options must have at least 3 items, got {len(v)}")
```

A model returning 4 or 5 options passes validation silently. The `LeverCleaned` version of the field (line 229–231) repeats the same "Exactly 3 options. No more, no fewer." description. The intent (explained in the `DocumentDetails` comment at line 194–196) is to *allow* over-generation, letting `DeduplicateLeversTask` trim extras. But telling the LLM "no more, no fewer" then silently accepting 4+ is a misleading instruction that can increase model confusion and produce non-deterministic outputs.

---

## Suspect Patterns

### S1 — No pre-call output-size estimation for verbose models
**File:** `identify_potential_levers.py:306–341`, `llm_config/anthropic_claude.json`

With `max_tokens: 16000` silently clamped to ~8,192 for haiku, and no code that estimates the expected response size before calling the LLM, the system has no way to warn (or reduce lever count) when a plan's lever payload is likely to overflow. The combination of:
- haiku's structural verbosity (consequences 2.44× baseline, review 3.71× baseline)
- 3 calls per plan × 5–7 levers per call
- the new lever_type + decision_axis fields from PR #346

means large plans can silently exceed the cap on any call. The failure is only detected after the truncated JSON fails to parse.

---

### S2 — Global LlamaIndex dispatcher in multi-worker runs
**File:** `runner.py:187–192`, `217–219`

```python
dispatcher = get_dispatcher()
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`get_dispatcher()` returns a **global** singleton. In parallel plan execution (`workers > 1`), every worker thread adds its own `TrackActivity` handler to the same global dispatcher. Events from any thread trigger all registered handlers. A plan running in thread A can cause thread B's `track_activity` handler to fire and write to thread B's `track_activity.jsonl`. The `_file_lock` only makes the setup/teardown atomic, not the event routing.

In practice the impact is limited because `track_activity.jsonl` is deleted in the `finally` block (line 220) and `usage_metrics.jsonl` uses thread-local storage (safe). But in any future use of `TrackActivity` for persistent data, this contamination would produce incorrect per-plan attribution.

---

### S3 — English-only `decision_axis` template in system prompt
**File:** `identify_potential_levers.py:249`

```
"This lever controls X by choosing between A, B, and C."
```

`OPTIMIZE_INSTRUCTIONS` (lines 61–68) explicitly warns against English-only validators, but the system prompt itself still hardcodes the English template. The `check_decision_axis` validator only checks `len(v) >= 20`, which passes any sufficiently long string in any language. For non-English plan prompts, the model may produce a semantically valid decision_axis in the prompt language that passes validation but breaks any downstream consumer expecting the English `"by choosing between"` phrasing. The haiku "whether" variant (N5) is a softer symptom of the same gap: the format requirement is not structurally validated, only implicitly guided by the English template.

---

### S4 — Case-sensitive duplicate lever name detection
**File:** `identify_potential_levers.py:375`

```python
seen_names: set[str] = set()
...
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

The deduplication is case-sensitive. A model returning `"Team Structure"` in call 1 and `"team structure"` in call 3 would produce two levers with visually identical names in the output. The downstream `DeduplicateLeversTask` is designed to handle semantic duplicates, but exact case-variant duplicates should be caught here. The fix is `seen_names.add(lever.name.lower())` and `if lever.name.lower() in seen_names`.

---

## Improvement Opportunities

### I1 — Fuzzy lever_type normalization before hard rejection
**File:** `identify_potential_levers.py:128–135`

Add a normalization lookup table before the hard `ValueError`. A minimal table covers the most common model deviations:

```python
_LEVER_TYPE_ALIASES = {
    "coalition_building": "governance",
    "stakeholder_engagement": "governance",
    "outreach": "dissemination",
    "technical": "methodology",
    "tech": "methodology",
    "ops": "operations",
    "delivery": "execution",
}
```

If `normalized` is in `_LEVER_TYPE_ALIASES`, return the canonical value instead of raising. Log the normalization so analysts can track which models produce non-enumerated types and whether the aliases need expanding.

Alternatively, enable `max_validation_retries=1` in `IdentifyPotentialLevers.execute()` so that a `ValidationError` on a single lever triggers a retry with the structured Pydantic feedback injected into the prompt (`llm_executor.validation_feedback`). The infrastructure already exists in `LLMExecutor` — the call site just doesn't use it.

---

### I2 — Raise haiku `max_tokens` to reflect the real API cap, or document the discrepancy
**File:** `llm_config/anthropic_claude.json:14, 34`

Either:
- Set `max_tokens` to 8192 (the actual haiku-4-5 cap) so the config reflects reality and prevents false assumptions, OR
- Keep 16000 but add a comment explaining the API silently caps it

Also add a note to `OPTIMIZE_INSTRUCTIONS` that per-lever field additions increase response size and can push verbose models (especially haiku) past the effective output ceiling — the risk that C4 in the insight file proposes documenting.

---

### I3 — Align `options` field description with the asymmetric validator
**File:** `identify_potential_levers.py:112`

Replace "Exactly 3 options for this lever. No more, no fewer." with "At least 3 options for this lever. If you generate more, extras will be trimmed downstream." This makes the instruction honest about what the validator actually enforces and avoids confusing weaker models that try to comply with the "no more" constraint.

---

### I4 — Add `decision_axis` format guidance for binary decisions
**File:** `identify_potential_levers.py:249`

System prompt section 2 should explicitly address the "whether" variant. Two concrete options:
- Prohibit it: "Do not use 'whether'; all axes must name 3 explicit choices."
- Permit it with structure: "For binary decisions use: 'This lever controls X by choosing between A or B.'"

Currently 24% of haiku's axes use the "whether" form (N5). Without explicit guidance, models will continue to be inconsistent.

---

### I5 — Enable `max_validation_retries` on the LLMExecutor call site
**File:** `identify_potential_levers.py:294–344`

`LLMExecutor` supports `max_validation_retries` (llm_executor.py:180) which retries on Pydantic `ValidationError` and injects structured error feedback via `llm_executor.validation_feedback`. The current call site creates:

```python
llm_executor = LLMExecutor(llm_models=llm_models)
```

This defaults to `max_validation_retries=0`. Setting `max_validation_retries=1` would give weaker models (llama3.1, haiku) one retry attempt with the specific validation error message included in the prompt. The `execute_function` closure would need to check `llm_executor.validation_feedback` and prepend it to the messages. This is especially effective for `lever_type` rejections, which produce clear, machine-readable feedback.

---

### I6 — Fix `_run_plan_task` timeout to not block on shutdown
**File:** `runner.py:491–503`

Replace the `with` block with a manual try/finally that calls `executor.shutdown(wait=False)` after catching `TimeoutError`:

```python
executor = _TPE(max_workers=1)
future = executor.submit(run_single_plan, plan_dir, output_dir, model_names, step)
try:
    pr = future.result(timeout=plan_timeout)
except _TE:
    logger.error(f"{plan_name}: killed after {plan_timeout}s (plan timeout)")
    pr = PlanResult(name=plan_name, status="error",
                    duration_seconds=float(plan_timeout),
                    error=f"plan timeout after {plan_timeout}s")
    executor.shutdown(wait=False)  # don't block; accept thread leak
```

The underlying thread can't be killed in CPython, but at least the outer runner thread is no longer blocked, allowing other plans to continue.

---

### I7 — Post-processing `lever_type` diversity check
**File:** `identify_potential_levers.py:368–392`

After merging all levers from 3 calls, compute the lever_type distribution and log a warning when any single type exceeds ~33% of total levers. This catches N6-style governance bias (gpt-5-nano at 35%) during development and regression testing without modifying the validator or prompt.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| **N1** — Haiku JSON-EOF truncation (run 30, `gta_game`, `silo`) | B2: `max_tokens: 16000` exceeds haiku's real ~8,192 cap; S1: no pre-call size guard |
| **N2** — llama3.1 `lever_type='coalition_building'` rejection | B1: hard validator, no fuzzy normalization; no `max_validation_retries` at call site (I5) |
| **N4** — Success rate −8.6 pp overall | B1 + B2 combined: 1 new llama3.1 failure + 2 new haiku failures, all PR-caused |
| **N5** — Haiku 24% "whether" decision_axis variant | S3: English-only template not structurally validated; I4: no guidance for binary decisions |
| **N6** — gpt-5-nano governance bias (35%) | No diversity check in post-processing (I7) |
| **N7** — Template leakage ("The options [verb]") | Pre-existing issue; not introduced or worsened by this PR |
| Timeout events not always interrupting plans | B3: `with _TPE()` shutdown blocks outer thread |
| Duplicate levers with different case | S4: case-sensitive `seen_names` set |

---

## PR Review

### What the PR adds
- `lever_type` field on `Lever` and `LeverCleaned` (lines 89–94, 213–215)
- `decision_axis` field on `Lever` and `LeverCleaned` (lines 95–100, 216–218)
- `normalize_lever_type` validator (lines 126–135)
- `check_decision_axis` min-length validator (lines 137–143)
- System prompt section 2 "Lever Classification" (lines 247–249)
- Propagation through the `LeverCleaned` conversion (lines 385–387)

### Does the implementation match the intent?

Partially. The PR description says "type normalization + rejection of invalid types" — the `strip().lower()` is the normalization, and hard rejection is correct as a last resort. But the PR does not add a fuzzy normalization step before rejection, and does not enable validation retries at the call site. For a validator that hard-rejects any non-enumerated string, both of those safeguards are needed to avoid plan failures on edge-case model outputs.

### Gaps in the PR

1. **No `max_tokens` adjustment** (B2). The PR adds ~300–400 chars per lever to the response payload. The haiku `max_tokens: 16000` was already silently clamped to ~8,192 by the API. The PR should have either documented this risk or increased the practical output budget (e.g., by reducing the number of levers requested when the model is known to be verbose).

2. **Hard validator with no recovery path** (B1). The PR adds `normalize_lever_type` but uses a pure allow-list with no fuzzy normalization. Combined with `max_validation_retries=0` at the call site, a single off-enumeration lever_type causes the entire plan to fail. The PR description says "type normalization" but the implementation only normalizes case; it does not normalize semantically-adjacent values.

3. **`decision_axis` "whether" variant** (N5, I4). The system prompt says "Use the template: 'This lever controls X by choosing between A, B, and C.'" but this is guidance, not a structural requirement. The validator only checks `len >= 20`. 24% of haiku's outputs use `"This lever controls whether..."` instead. The PR does not address whether this is acceptable.

4. **English-only template not flagged** (S3). The new `decision_axis` format guidance is English-only, violating the principle documented in `OPTIMIZE_INSTRUCTIONS` (lines 61–68). The PR does not add a note to `OPTIMIZE_INSTRUCTIONS` about this new English-only dependency.

5. **`options` description vs validator mismatch** (B4 — pre-existing, not introduced by PR). The PR does not fix the "Exactly 3, no more, no fewer" description that contradicts the asymmetric validator.

### What the PR does correctly

- The new fields propagate cleanly through `Lever → LeverCleaned → JSON` with no serialization gaps.
- The `check_decision_axis` validator is structurally correct (length check only, no English keyword dependency).
- `VALID_LEVER_TYPES` as a `ClassVar[set]` is an efficient O(1) lookup.
- Section 2 of the system prompt is well-placed and gives clear examples of the six types.
- The new fields add genuine downstream value: `lever_type` enables categorization filtering, `decision_axis` makes the controllable choice explicit for the scenario picker.

---

## Summary

PR #346 delivers genuinely useful schema additions — `lever_type` and `decision_axis` are correctly implemented, well-propagated, and add actionable structure to lever output. The PR's content quality goals are achieved for 5 of 7 models.

However, two direct reliability regressions were introduced that were not caught before merging:

**B1** — The `lever_type` validator hard-rejects any non-enumerated string with no fuzzy normalization and no validation retry enabled at the call site. One plan failure resulted (llama3.1, `sovereign_identity`).

**B2** — `max_tokens: 16000` in the haiku config exceeds the model's real API output cap (~8,192 tokens). PR #346's additional per-lever fields (~300–400 chars each) pushed haiku's per-call response size over the effective ceiling for two plans. Two plan failures resulted (haiku, `gta_game` and `silo`).

These bugs account for all 3 net-new plan failures observed in iteration 31 (success rate drop from 94.3% to 85.7%).

Additional findings not introduced by this PR:

**B3** — The plan timeout in `runner.py` creates the correct `PlanResult` on `TimeoutError` but does not prevent the outer thread from blocking until the LLM call finishes anyway, due to `ThreadPoolExecutor.shutdown(wait=True)` in the `with` block's `__exit__`.

**B4** — The `options` field description says "Exactly 3, no more, no fewer" but the validator only enforces the lower bound. This is a misleading LLM instruction.

**S2** — The global LlamaIndex dispatcher collects event handlers from all parallel plan threads, risking cross-plan event routing in multi-worker mode (benign in practice today, fragile by design).

Priority fixes: B2 (document or correct haiku `max_tokens`), B1 (add fuzzy lever_type normalization or enable `max_validation_retries=1` at the call site).
