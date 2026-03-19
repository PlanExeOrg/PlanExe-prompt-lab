# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`
- `llm_config/anthropic_claude.json`
- `llm_config/baseline.json`
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py`

PR under review: #351 "fix: adaptive retry loop, haiku max_tokens, relax review_lever"

---

## Bugs Found

### B1 — `partial_recovery` event fires for all steps, including `identify_documents`

**File:** `self_improve/runner.py:514–518`

```python
if pr.calls_succeeded is not None and pr.calls_succeeded < 3:
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

`_run_documents` always returns `PlanResult(calls_succeeded=1)` (line 155). Since `1 < 3` is True, every `identify_documents` run emits a spurious `partial_recovery` event with `calls_succeeded=1, expected_calls=3`. The PR introduced this check for the identify_potential_levers adaptive loop without gating it on the step name.

The fix is to add `and step == "identify_potential_levers"` to the condition, or to have `_run_levers` return a sentinel value that explicitly signals partial recovery rather than relying on the caller to infer it from the call count.

---

### B2 — `partial_recovery` event fires on legitimate early-stop (false positive)

**Files:** `self_improve/runner.py:115–117` and `runner.py:514–518`

The adaptive loop in `identify_potential_levers.py` stops when `len(generated_lever_names) >= min_levers` (line 326), which can occur after 2 calls if a model produces 8+ levers per call (8+8=16 ≥ 15). In that case `len(result.responses) == 2`, and `runner.py` emits `partial_recovery` even though the run was a clean success.

```python
# runner.py:115
expected_calls = 3
actual_calls = len(result.responses)
if actual_calls < expected_calls:
    logger.warning(...)   # fires on legitimate early-stop
```

With `min_levers=15` and models producing 5–7 levers per call, the typical case requires 3 calls, so this is unlikely in practice today. But the code carries no comment documenting this assumption, and if `min_levers` is reduced or a model's output count increases, the false-positive will silently appear.

---

### B3 — `partial_recovery` event carries no failure reason

**Files:** `self_improve/runner.py:514–518`; `identify_potential_levers.py:306–320`

When a mid-loop call fails, the exception is captured at line 307 and logged at lines 308–309, but neither the exception class nor its message is threaded back to the runner. The `partial_recovery` event in `events.jsonl` only contains `calls_succeeded` and `expected_calls`. There is no way to distinguish a timeout from a Pydantic validation error from an API cap error just by reading the events.

This makes Q1 from the insight unanswerable: "Is the haiku partial_recovery caused by the 3rd call failing at the API level, or by a Pydantic validation error?"

The path for the fix: `PlanResult` (`runner.py:96–102`) could carry a `last_error: str | None = None` field. `_run_levers` would capture the last exception in the loop and set it. `_run_plan_task` would include it in the partial_recovery event.

---

### B4 — No word-count validator on `options` — short label-style options pass silently

**File:** `identify_potential_levers.py:99–102, 124–136`

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option must be a complete "
                "strategic approach (a full sentence with an action verb), not a label."
)
```

The `check_option_count` validator (lines 124–136) only enforces a minimum of 3 items. The system prompt section 6 requires "at least 15 words with an action verb" per option, but no Pydantic validator enforces this. Options as short as 5 words ("Prioritize gentrification-driven revitalization") pass validation without error, ship to downstream tasks, and accumulate in the output JSON.

The proposed fix (from insight C3): add a `field_validator('options', mode='after')` that raises `ValueError` if any option has fewer than 12 words. Using `len(option.split()) < 12` is language-agnostic and avoids the English-only validation problem documented in `OPTIMIZE_INSTRUCTIONS`.

---

## Suspect Patterns

### S1 — All three `review_lever` examples use "options" as the grammatical subject

**File:** `identify_potential_levers.py:224–226`

```
"Switching from seasonal contract labor to year-round employees stabilizes harvest quality,
 but none of the options price in the idle-wage burden during the 5-month off-season."

"Routing the light-rail extension through the historic district unlocks ridership but triggers
 Section 106 heritage review; the options assume permits will clear on the standard timeline."

"Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a
 regional hurricane season can correlate all three simultaneously — correlation risk absent
 from every option."
```

All three examples culminate in a phrase whose grammatical subject is "the options" or "every option." Weaker models (llama3.1) latch onto this pattern and reproduce it in ~89% of reviews (run 45 gta_game), even when the model shifts from "The options overlook" to "none of the options address." The pattern is a structural artifact of the examples, not of the lever's domain.

`OPTIMIZE_INSTRUCTIONS` lines 69–79 document this template-lock risk and state that examples must "avoid reusable transitional phrases that fit any domain." The current examples violate that constraint.

---

### S2 — No upper bound on `options` count per lever

**File:** `identify_potential_levers.py:99–102, 124–136`

The system prompt says "Exactly 3 options" and the `Lever.options` field description says "No more, no fewer." But the only Pydantic validator checks `len(v) < 3`; models returning 4, 5, or 6 options pass silently. If any downstream task (e.g., ScenarioGeneration) assumes exactly 3 options per lever, this is a silent integrity failure. The comment at `DocumentDetails.levers` (lines 161–163) explicitly defends the absence of an upper cap on levers because DeduplicateLeversTask handles extras. That argument does not apply to options: no downstream task is designed to trim over-long option lists.

---

### S3 — `expected_calls=3` hardcoded in two places with no link to `max_calls=5`

**Files:** `runner.py:115`, `runner.py:518`; `identify_potential_levers.py:264`

```python
# identify_potential_levers.py
max_calls = 5      # adaptive loop ceiling

# runner.py (_run_levers)
expected_calls = 3  # hardcoded; no reference to max_calls or min_levers

# runner.py (_run_plan_task)
expected_calls=3    # hardcoded again
```

Three independent constants control related behavior with no linkage. If `max_calls` or `min_levers` is tuned, the runner's threshold silently drifts. At minimum these should share a named constant or be derived from the loop parameters.

---

### S4 — gpt-oss-20b `max_tokens=8192` may be insufficient for a reasoning model

**File:** `llm_config/baseline.json:34`

The current config already sets `max_tokens: 8192` for `openrouter-openai-gpt-oss-20b`. Yet run 46 (after PR #351) still produced `EOF while parsing a list at line 47` for hong_kong_game. The model's own comment says "This is a reasoning model, and uses more tokens than LLMs." For reasoning models that consume tokens on internal chain-of-thought before emitting the output, the effective output budget at 8192 max_tokens may be much less than 8192. The haiku fix (reducing from 16000 to match the API cap) does not translate directly to a reasoning model where the token budget is shared between reasoning and output.

If `max_tokens` for gpt-oss-20b was already 8192 at the time of run 46 and still produced truncation, a different fix is needed — either a higher `max_tokens` value (to give more room after reasoning), or per-call prompt compression.

---

## Improvement Opportunities

### I1 — Log failure reason in `partial_recovery` event

**File:** `runner.py:514–518`; `identify_potential_levers.py:306–320`

Extend `PlanResult` with `last_error: str | None = None`. In `IdentifyPotentialLevers.execute`, save the last caught exception (lines 306–320) and surface it through the return value. In `_run_plan_task`, include `failure_reason=pr.last_error` in the partial_recovery event. This directly answers Q1/C2 from the insight.

---

### I2 — Add per-option minimum word-count validator

**File:** `identify_potential_levers.py:124–136`

Add a second `@field_validator('options', mode='after')` that raises `ValueError` if any option has fewer than 12 words (conservative; catches the 5–10 word labels without being too tight). Using `.split()` avoids English-only string matching.

```python
@field_validator('options', mode='after')
@classmethod
def check_option_quality(cls, v):
    for opt in v:
        if len(opt.split()) < 12:
            raise ValueError(
                f"option is too short ({len(opt.split())} words): {opt!r}; "
                f"expected at least 12 words"
            )
    return v
```

---

### I3 — Replace options-centric review examples with domain-specific, non-portable critiques

**File:** `identify_potential_levers.py:224–226`

All three examples should be rewritten so that neither "the options" nor "every option" appears. The critique should name a concrete project-level tension that cannot be rephrased as a generic "options do not address X" sentence. The agriculture example already does this with the idle-wage sentence structure; the other two examples should follow the same pattern.

Example replacement for the light-rail example (does not use "options" as subject):
> "Section 106 heritage review triggers a mandatory comment period of 45–180 days that sits outside the project manager's control — any fixed opening date committed before permits clear is betting on the minimum review timeline, not the median."

---

### I4 — Add style-diversity instruction to continuation prompt

**File:** `identify_potential_levers.py:273–278`

The current continuation prompt (call 2+) instructs the model to generate new lever names but says nothing about varying critique style or option depth. Adding "Vary your critique format and the level of detail in options compared to earlier batches." would reduce the stylistic drift observed in llama3.1 calls 2–3 (shorter options, more formulaic reviews) vs. call 1.

---

### I5 — Detect over-options silently: add max upper bound or downstream trim

**File:** `identify_potential_levers.py:99–102`

Either add a `max_length=5` to the `options` field (accepting up to 5 and letting the model exceed 3 occasionally) or add a validator that trims to 3 (preserving the first 3) rather than rejecting. The current silent pass of 4–6 options could cause downstream breakage.

---

## Trace to Insight Findings

| Insight Finding | Root Cause in Code |
|---|---|
| N4 — llama3.1 template lock worsened to ~89% options-centric reviews | S1: all three `review_lever` examples use "options" as grammatical subject |
| N5 / E4 — llama3.1 gta_game options as short as 5 words pass validation | B4: no word-count validator on `options` |
| Q1 / C2 — can't diagnose why haiku call 3 fails on silo/parasomnia | B3: failure reason absent from `partial_recovery` event |
| N3 — haiku partial_recovery for silo/parasomnia (2 of 5 plans) | B3 + B1: failure mode unattributed; may be API cap or Pydantic; can't tell |
| N2 — gpt-oss-20b JSON truncation persists after PR | S4: reasoning model may exhaust 8192 token budget on internal reasoning before producing full JSON |
| Quantitative metric: "inner × outer retry amplification" (gpt-5-nano 8 calls for 3 successes) | B3 is partially responsible: Pydantic rejections inside `LLMExecutor` are counted as "calls" in usage_metrics but not visible as a partial_recovery cause |
| B2 would become visible if identify_documents is ever benchmarked via this runner | B1 (step-agnostic partial_recovery) would produce misleading events.jsonl |

---

## PR Review

### Adaptive retry loop (`identify_potential_levers.py:263–328`)

**Implementation is correct.** The loop terminates on `len(generated_lever_names) >= min_levers` or exhaustion of `max_calls`. The exception handling is correct: first-call failure re-raises (line 314–315); subsequent failures continue with prior results (line 320). `messages_snapshot` correctly freezes the per-call message list before defining the closure, avoiding closure-over-loop-variable bugs in deferred execution paths.

**Gap 1 (B1/B2):** The runner's partial_recovery check uses hardcoded `expected_calls=3` and is not gated on the step name. This is a bug introduced by the PR — the check fires for `identify_documents` runs (which always complete in 1 call) and could fire as a false positive on a legitimately fast 2-call run.

**Gap 2 (B3):** The partial_recovery event carries no failure reason. When call 3 fails and prior levers are preserved, the events.jsonl entry says nothing about why call 3 failed. This was a missed opportunity in the PR.

### Haiku max_tokens 16000 → 8192 (`llm_config/anthropic_claude.json:14, 34`)

**Fix is correct.** Both `anthropic-claude-haiku-4-5` (line 14) and `anthropic-claude-haiku-4-5-pinned` (line 34) are set to 8192. Insight P5 confirms no haiku JSON-EOF errors in run 51.

**Side effect (not a PR bug, but a consequence):** The reduced budget means haiku now requires a 3rd call for complex plans (2 calls × ~7 levers = 14 < 15). If the 3rd call fails, `partial_recovery` fires. This is a real but mild regression — plans are still "ok" with fewer levers rather than catastrophically failing.

### `review_lever` minimum 50 → 10 (`identify_potential_levers.py:150`)

**Correct.** The comment at lines 146–148 documents the reasoning. No evidence of rejection events or quality downsides in the after runs.

### lever_classification removal

**Not visible in the current files** (already absent). Insight P6 confirms the success rate recovery (88.6% → 94.3%). No observed regressions.

### gpt-oss-20b max_tokens (not explicitly in PR #351)

The current `baseline.json:34` already has `max_tokens: 8192` for `openrouter-openai-gpt-oss-20b`. If this value was present during run 46 and truncation still occurred, then the insight's C1 recommendation ("apply same max_tokens fix as haiku") is already implemented but insufficient. For a reasoning model, a different approach may be needed (see S4).

---

## Summary

The PR's core logic is sound. The adaptive loop is correctly implemented, haiku's max_tokens fix is correct, and the review_lever minimum relaxation is the right structural change. The lever_classification removal is clearly beneficial.

**Bugs introduced or exposed by the PR:**

1. **B1 (critical):** `partial_recovery` fires for `identify_documents` (calls_succeeded=1 < 3 always True). Every identify_documents run emits a false partial_recovery event. Gate the check on `step == "identify_potential_levers"`.

2. **B3 (important):** `partial_recovery` event has no failure reason. The adaptive loop correctly catches and continues on exceptions, but discards the exception detail before the event is written. Fix: add `last_error` field to `PlanResult`.

3. **B2 (minor):** Technically possible false-positive partial_recovery if a model produces ≥8 levers per call and the threshold is met in 2 calls. Unlikely with current models but undefended.

**Pre-existing quality issues the PR did not address:**

4. **B4 / I2:** No word-count validator on options lets 5-word labels pass Pydantic. Direct cause of N5/E4 in runs 45 and 45 (llama3.1, calls 2–3).

5. **S1 / I3:** All three `review_lever` examples use "options" as grammatical subject, directly causing and worsening the template lock pattern in llama3.1 (62.5% → 89% in gta_game). This is the most impactful quality issue and is fixable with a one-time example rewrite.

**Priority order for follow-up:**
1. Fix B1 (step-gate the partial_recovery check) — correctness bug in events.jsonl
2. Fix S1 (replace review examples) — template lock root cause, directly affects output quality
3. Fix B3 (log failure reason) — diagnostic gap blocking haiku partial_recovery analysis
4. Fix B4 (word-count validator) — prevents short label options from shipping to downstream tasks
