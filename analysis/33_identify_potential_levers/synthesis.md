# Synthesis

## Cross-Agent Agreement

Both `insight_claude` and `code_claude` agree on all major findings. No disagreements exist between agents. Consensus:

1. **qwen3 regression is the most critical issue.** Adding `lever_classification` as a required `str` field caused qwen3 to fail 3/5 plans (silo, sovereign_identity, hong_kong_game) with `Field required: lever_classification`. The adaptive retry offers zero recovery because the guard at `identify_potential_levers.py:338` raises immediately when `len(responses) == 0` (i.e., first call fails). Success rate dropped 97.1% → 88.6% (-8.5pp), a net loss of 3 plans.

2. **`lever_classification` system prompt examples are generic template-lock vectors.** All three Section 2 examples ("governance — who oversees the review process", "methodology — which data collection approach to use", "execution — how to sequence the rollout phases") are portable phrases that fit any domain. llama3.1 copies "how to sequence the rollout phases" four times across unrelated levers in hong_kong_game — exactly the template-lock failure documented in `OPTIMIZE_INSTRUCTIONS` lines 69–79.

3. **`expected_calls=3` is stale in runner.py.** Both B3 (`runner.py:115`) and B4 (`runner.py:514–518`) fire spurious warnings and false-positive `partial_recovery` events for plans that legitimately complete in 1 call under the adaptive retry design. This poisons event-based downstream analysis.

4. **`check_review_format` docstring is wrong.** Line 154 says "minimum length (at least 50 characters)" but line 157 checks `< 10`. Trivial but misleading.

5. **Adaptive retry is a genuine improvement for under-generating models.** llama3.1's lever counts improved meaningfully (sovereign_identity: 12→18, hong_kong: 13→16). The retry works correctly for calls 2–5; the gap is first-call failures only.

6. **haiku max_tokens fix and review_lever minimum relaxation are clean and correct**, with no observed regressions.

## Cross-Agent Disagreements

None. Both agents independently identified the same bugs (B1–B4), suspects (S1–S2), and priority order. Source code reading confirms all claims:
- `identify_potential_levers.py:338`: `if len(responses) == 0: raise llm_error` — confirms B2 (first-call no-retry).
- `runner.py:115`: `expected_calls = 3` — confirms B3.
- `runner.py:514–518`: `pr.calls_succeeded < 3` / `expected_calls=3` — confirms B4.
- `identify_potential_levers.py:229–230`: all three examples are generic — confirms S1.
- `identify_potential_levers.py:154,157`: docstring says 50, check is `< 10` — confirms B1.

## Top 5 Directions

### 1. Make `lever_classification` Optional to recover qwen3 (or add retry-on-first-call-failure)
- **Type**: code fix
- **Evidence**: insight_claude (negative #1, C1), code_claude (B2, I1, I2). Confirmed: `identify_potential_levers.py:111` (`lever_classification: str`), `identify_potential_levers.py:338–339` (immediate raise on first-call failure).
- **Impact**: Recovers qwen3's 3/5 failed plans, restoring success rate from 88.6% to 97.1% (or better). Two implementation paths: (a) change `lever_classification: str` to `lever_classification: Optional[str] = Field(default=None, ...)` — the simplest, lowest-risk change; (b) modify `identify_potential_levers.py:338` to continue instead of raise when the error is a Pydantic `ValidationError` and `call_index == 1`, giving qwen3 a second attempt with an explicit reminder to generate the field.
- **Effort**: Low (path a is a one-line type change + validator guard update; path b is ~5 lines of exception-type discrimination).
- **Risk**: Path (a) — low; the validator `check_lever_classification` already enforces minimum length when the field is present, so Optional means absent levers pass validation. The downstream enrich step adding detail may fill in or tolerate missing classifications. Path (b) — medium; distinguishing Pydantic `ValidationError` from network/auth errors requires careful exception handling to avoid infinite retry loops on non-recoverable errors.

### 2. Replace generic `lever_classification` system prompt examples with non-portable domain-specific phrases
- **Type**: prompt change
- **Evidence**: insight_claude (negative #3, C3), code_claude (S1, I3). Confirmed: `identify_potential_levers.py:229–230` — all three examples are portable; `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 7/16 levers carry copied phrases.
- **Impact**: Reduces template lock for llama3.1 (and any other model prone to copying), improving classification accuracy across all llama3.1 plans. Currently 7/16 levers in hong_kong_game carry wrong classifications due to verbatim copying. This is a content quality fix that affects all llama3.1 users of the lever pipeline.
- **Effort**: Low (a prompt-text substitution). New examples should follow the OPTIMIZE_INSTRUCTIONS "agriculture example" pattern: concrete, domain-anchored, non-portable.
  - Replace `"governance — who oversees the review process"` → `"governance — which of the four county agencies has authority to sign the discharge permit"`
  - Replace `"methodology — which data collection approach to use"` → `"methodology — whether to run paired-sample or repeated-measures ANOVA for the sleep-disruption dataset"`
  - Replace `"execution — how to sequence the rollout phases"` → `"execution — which city blocks to relay the water main in first to minimize service interruption"`
  - Also replace the single example in `Lever.lever_classification` field description (`identify_potential_levers.py:115`) with a domain-specific one.
- **Risk**: Low. Replacing examples cannot make lever quality worse than it currently is (7/16 wrong). The OPTIMIZE_INSTRUCTIONS pattern for `review_lever` proves domain-specific examples reduce template lock without harming other models.

### 3. Remove or update hardcoded `expected_calls=3` in runner.py
- **Type**: code fix
- **Evidence**: code_claude (B3, B4, I4). Confirmed: `runner.py:115` (`expected_calls = 3`), `runner.py:514–518` (`calls_succeeded < 3` → emits `partial_recovery` event).
- **Impact**: Eliminates false-positive `partial_recovery` events that pollute `events.jsonl` for any plan completed in 1 call (a legitimate outcome under the adaptive retry). The event fires even on successful fast runs, causing the assessment pipeline to misclassify them as degraded. Clean fix: remove the `partial_recovery` event block entirely (since "fewer than N calls" is now the happy-path), and remove the `expected_calls=3` warning in `_run_levers`. Or derive `expected_calls` dynamically from `max_calls` in `IdentifyPotentialLevers`.
- **Effort**: Low (remove two stale code blocks).
- **Risk**: Low. Removing a spurious warning and spurious event cannot break correctness; it only cleans up misleading signals in analysis output.

### 4. Fix `check_review_format` docstring to match implementation
- **Type**: code fix
- **Evidence**: insight_claude (negative #5), code_claude (B1). Confirmed: `identify_potential_levers.py:154` ("at least 50 characters"), `identify_potential_levers.py:157` (`< 10`).
- **Impact**: Documentation accuracy only — no behavioral change. Any developer adding a new validator or reading the existing one will get incorrect expectations from the docstring today.
- **Effort**: Trivial (change "at least 50 characters" to "at least 10 characters" in the docstring).
- **Risk**: None.

### 5. Document new required-field failure pattern in OPTIMIZE_INSTRUCTIONS
- **Type**: workflow change (meta-documentation)
- **Evidence**: insight_claude (OPTIMIZE_INSTRUCTIONS alignment #1 and #3), code_claude (I5). This is a preventative fix for future PRs.
- **Impact**: Prevents the qwen3-class regression from recurring when new required fields are added. The existing OPTIMIZE_INSTRUCTIONS already documents template lock, fabricated numbers, fragile English validation — but not the "new required field → first-call validation failure → no retry recovery" failure mode. Adding this warning makes the constraint design visible to future contributors and analysis agents.
- **Effort**: Low (add ~5 lines to `OPTIMIZE_INSTRUCTIONS`).
- **Risk**: None. Documentation-only change.

## Recommendation

**Fix Direction 1 first: change `lever_classification` to `Optional[str] = Field(default=None, ...)` in `identify_potential_levers.py`.**

**Why first:** The qwen3 regression (3/5 plans failing) is the largest measurable impact from this PR. It is a direct, confirmed regression — not a hypothesis. It brought success rate from 97.1% to 88.6%. The fix is low-risk, low-effort, and independent of everything else.

**What to change:**

In `identify_potential_levers.py:111–117`, change:
```python
lever_classification: str = Field(
    description=(
        "Brief classification: category and what this lever controls. "
        "Format: 'category — what this lever decides'. "
        "Example: 'governance — who oversees the review process'."
    )
)
```
to:
```python
lever_classification: Optional[str] = Field(
    default=None,
    description=(
        "Brief classification: category and what this lever controls. "
        "Format: 'category — what this lever decides'. "
        "Example: 'governance — who oversees the review process'."
    )
)
```

In `identify_potential_levers.py:163–169`, update the validator to short-circuit on `None`:
```python
@field_validator('lever_classification', mode='after')
@classmethod
def check_lever_classification(cls, v):
    if v is None:
        return v
    if len(v) < 10:
        raise ValueError(f"lever_classification is too short ({len(v)} chars); expected at least 10")
    return v
```

This allows qwen3's otherwise-valid lever batches to pass validation on the first call, recovering the 3/5 failures. The field remains present and high-quality for haiku, gemini, gpt-5-nano, and gpt-4o-mini (which already generate it reliably). The `LeverCleaned` output model carries `lever_classification: str` for downstream use — that field may also need to become `Optional[str]` to avoid a mapping error when the raw value is `None`.

Also update `LeverCleaned.lever_classification` at `identify_potential_levers.py:195`:
```python
lever_classification: Optional[str] = Field(
    description="Brief classification: category and what this lever decides."
)
```

**After this fix**, verify qwen3 recovers to 5/5, then pursue Direction 2 (replace generic examples) to address llama3.1 template lock — both fixes together bring the PR to a net-positive state.

## Deferred Items

- **Direction 2 (replace generic examples)**: Pursue immediately after Direction 1. The template lock produces semantically incorrect lever_classification values for ~44% of llama3.1 levers in affected plans. It is a content quality issue, not a hard failure, but it degrades output for one of the primary target models.

- **Direction 3 (remove stale `expected_calls=3` in runner.py)**: Low effort, should be bundled with Direction 1 or 2 in the same PR to avoid polluting the assessment pipeline with false `partial_recovery` events.

- **Direction 4 (fix `check_review_format` docstring)**: Trivial one-liner. Bundle with any nearby PR touching validators.

- **Direction 5 (OPTIMIZE_INSTRUCTIONS documentation)**: Worth doing after Direction 1 is confirmed working, so the new pattern entry reflects the chosen solution (Optional field approach vs retry-on-first-call approach).

- **S4 / MEMORY.md "iteration 2" — assistant turn serialization**: Not addressed in this PR. Each adaptive retry call is stateless (system + user only). Adding prior assistant responses to subsequent call messages would let the model generate genuinely complementary levers rather than parallel batches. This is the next major architectural improvement after the current regression is resolved.

- **haiku `review` field verbosity (3–4× baseline)**: Pre-existing issue, not introduced by this PR. The PR did not worsen it significantly. Investigate whether downstream scenario generation is affected by overly long review fields; consider a max_length soft guidance in the system prompt.
