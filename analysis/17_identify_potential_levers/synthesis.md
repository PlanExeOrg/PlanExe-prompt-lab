# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **Overall success rate is the highest observed (34/35, 97.1%)** — up from 88.6% in analysis/16 and 91.4% in analysis/15.

2. **gpt-oss-20b parasomnia EOF is a chronic, unresolved failure** — present in three consecutive batches (runs 18, 20, 25), always the same error (`Invalid JSON: EOF while parsing a list`), and not classified as a transient/retriable error by `_TRANSIENT_PATTERNS` in `llm_executor.py`.

3. **qwen3 consequence contamination (review text leaking into `consequences`) affects 100% of levers** across all plans in run 27, with no validator to detect or repair it. Code reviewers confirm there is no `@field_validator` on `consequences` despite its field description explicitly forbidding "Controls" and "Weakness:" text.

4. **`summary` field description contradicts the system prompt** — `DocumentDetails.summary` description (lines 113–115) says "Are these levers well picked? ... 100 words." while `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 requires the strict format `Add '[full strategic option]' to [lever]`. For structured LLM calls, the field description is what the model sees, so the generic description wins. This directly explains 0/15 summary exact-format compliance for runs 25–30.

5. **`strategic_rationale` and `summary` are dead-generated overhead** — both fields are in `DocumentDetails`, generated three times per plan (once per LLM call), but neither appears in `save_clean()` output. They waste tokens and increase truncation risk.

6. **No preflight model name validation** — invalid model aliases (e.g., `openrouter-paid-gemini-2.0-flash-001` in run 29) are only discovered when each plan attempt executes, burning one failed start per plan before recovery.

7. **Haiku's hong_kong recovery** (0 levers in run 23 → 5/5 in run 30) is attributed in insight_claude to a "review_lever auto-correction" being implemented. Both code reviewers independently verify that **no such auto-correction exists** in `check_review_format` (lines 86–99). The validator still only raises on failure; it does not prepend "Controls ". The recovery is therefore prompt-driven (prompt_2 → prompt_3 improved format compliance for haiku on this plan).

8. **Haiku (run 30) produces the best content quality** — most specific quantification, longest consequences and options, zero field contamination, 5/5 plans.

---

## Cross-Agent Disagreements

### Disagreement 1: Auto-correction present or not?

**insight_claude** infers that the analysis/16 recommendation (auto-prepend "Controls ") was implemented based on haiku's hong_kong recovery. **Both code reviewers** read the actual source and confirm `check_review_format` (lines 86–99) has no auto-prepend logic whatsoever. The code reviewers are correct. Haiku recovered because prompt_3 better elicits the "Controls" prefix, not because of a code change.

**Implication for robustness:** If haiku regresses on a future plan by omitting "Controls" again, there is still no safety net in code. The validator will reject levers, and the plan will fail.

### Disagreement 2: Is the runner's missing RetryConfig a bug?

**code_codex** classifies the runner's lack of `RetryConfig` as a distinct bug (B2), noting that the production pipeline at `run_plan_pipeline.py:171–174` explicitly passes `retry_config=RetryConfig()` while the optimizer at `runner.py:93–94` uses a bare `LLMExecutor`. **code_claude** does not separately flag this, but confirms that adding "eof while parsing" to `_TRANSIENT_PATTERNS` would enable retry on the next fallback LLM. Both diagnoses are compatible: the transient pattern fix is what classifies the error as retriable; the RetryConfig determines whether validation retries happen on a single model. For the EOF case, the fallback-chain retry is the relevant mechanism.

### Disagreement 3: Severity of summary non-compliance

**insight_codex** treats summary format compliance as the most consistently broken instruction and rates it highly. **code_claude** and **code_codex** both note that `summary` is not output by `save_clean()` and therefore has no downstream functional impact — it only appears in the raw JSON. Resolving the description conflict (or removing the field entirely) is still worthwhile for diagnostic accuracy and token savings, but it is lower priority than fixes that prevent plan failures.

---

## Top 5 Directions

### 1. Add `"eof while parsing"` to `_TRANSIENT_PATTERNS`
- **Type**: code fix
- **Evidence**: code_claude (I1), code_codex (I3+B2), insight_claude (N1, C1), insight_codex (C2). Three consecutive batches (runs 18, 20, 25) lose the entire `parasomnia_research_unit` plan on the same error. The pattern `"eof while parsing"` is absent from `_TRANSIENT_PATTERNS` in `llm_executor.py:41–51`. The error line advanced from 25 → 58 between batches, showing provider-side variability, which means a retry has a real chance of succeeding.
- **Impact**: gpt-oss-20b parasomnia failure converts from guaranteed plan loss to a retried attempt. Expected improvement: 0/3 → 1–2/3 parasomnia successes across batches. Batch success rate would reach 35/35.
- **Effort**: low — one-line addition to `_TRANSIENT_PATTERNS`
- **Risk**: The string `"eof while parsing"` is highly specific and won't match schema mismatch errors. Very low false-positive risk. Effectiveness depends on whether a fallback model is configured for gpt-oss-20b runs; if only one model is in the chain, the retry exhausts immediately.

### 2. Remove `strategic_rationale` and `summary` from `DocumentDetails`
- **Type**: code fix (schema change)
- **Evidence**: code_claude (I2, I3), code_codex (B5, I6), insight_claude (C3), insight_codex (implicitly via token analysis). Both fields are confirmed absent from `save_clean()` output (lines 344–346). `strategic_rationale` is `Optional[str]` and always generated; `summary` is required `str` and generated with conflicting instructions. Together they add an estimated 300–700 output tokens per call × 3 calls = up to 2,100 tokens per plan in wasted generation.
- **Impact**: Broader reduction of per-call token budget pressure. Haiku completed parasomnia in 291s (close to the likely timeout threshold); gpt-oss-20b is truncated on parasomnia. Removing these fields reduces the likelihood of truncation on verbose plans. Also eliminates the B2 summary description conflict automatically. Removing both fields requires also removing the corresponding section from `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (section 4, lines 181–183).
- **Effort**: medium — remove two fields from `DocumentDetails`, update the system prompt, check for any downstream code reading raw JSON `summary`.
- **Risk**: The summary field was intended for diagnostic use. Removing it eliminates that diagnostic. If summary is useful for prompt development feedback loops, consider a post-merge single-call diagnostic instead of generating it three times per plan.

### 3. Fix (or remove) `DocumentDetails.summary` field description
- **Type**: code fix
- **Evidence**: code_claude (B2), code_codex (B1, I1). Confirmed in source: line 113–115 says "Are these levers well picked? … 100 words." vs. system prompt lines 181–183 requiring `Add '[full strategic option]' to [lever]`. For structured LLM calls (`as_structured_llm(DocumentDetails)`), the Pydantic field description is the primary per-field instruction seen by the model. Five of seven models achieve 0/15 exact-format compliance; only llama3.1 (which uses the same system prompt) achieves 14/15 — suggesting the description overrides the system prompt for most models.
- **Impact**: If the field is kept, aligning the description to `"Identify ONE critical missing option. Format: Add '[full strategic option]' to [lever name]. No preamble."` is expected to raise compliance from ~0% to measurable. If the field is removed as part of direction 2, this is moot.
- **Effort**: low (one-line description change) or none (if field is removed)
- **Risk**: Near-zero. The description change only affects how the model formats `summary`; it cannot regress lever quality.

### 4. Add `@field_validator` on `Lever.consequences` to detect and strip review contamination
- **Type**: code fix
- **Evidence**: code_claude (I4), code_codex (B4, I2), insight_claude (N2, C2), insight_codex (H2, C3). qwen3 contaminates 66/85 final levers across all plans in run 27. The field description at lines 42–44 explicitly prohibits "Controls" and "Weakness:" text in `consequences`, but there is no runtime enforcement. The contaminated text is copied verbatim into clean output at lines 299–305.
- **Impact**: qwen3 clean artifacts would have correct `consequences` fields. No effect on other models (none produce this contamination pattern). Downstream steps consuming `consequences` receive clean data.
- **Effort**: low — add a `@field_validator('consequences', mode='after')` following the pattern of `check_review_format`. Strip trailing suffix starting with `Controls ` and containing `Weakness:`, or at minimum log a warning.
- **Risk**: A consequences field that legitimately discusses trade-offs (e.g., "Controls [some factor]...") could be incorrectly stripped. The validator should only trigger when the suffix closely matches the `review_lever` pattern (e.g., the text that follows `→ Strategic:` and starts with `Controls `).

### 5. Add pre-flight model name validation before the plan execution loop
- **Type**: code fix
- **Evidence**: code_claude (I5, I6), code_codex (B3, I4), insight_claude (N4, C4). Run 29 burned 5 wasted plan starts because `openrouter-paid-gemini-2.0-flash-001` was not a registered alias. The invalid name is only detected inside `run_single_plan()`, one per plan. With workers > 1, all plans fail simultaneously before recovery.
- **Impact**: Eliminates run-29-style infrastructure failures entirely. Clean `events.jsonl` with no spurious failure entries. Wall-clock savings (5 wasted plan starts).
- **Effort**: low — call `LLMModelFromName.from_names(model_names)` once before the plan loop at `runner.py:375`, raising immediately if any name fails. Alternatively, add a dedicated `validate_model_names()` probe.
- **Risk**: None — this is a fail-fast check that converts silent per-plan failures into one early batch failure with a clear error message.

---

## Recommendation

**Do direction 1 first: add `"eof while parsing"` to `_TRANSIENT_PATTERNS` in `llm_executor.py`.**

**Why this first:**
- It is the only change that directly converts a concrete plan failure (gpt-oss-20b parasomnia) into a success. The other directions improve output quality, reduce token waste, or clean up infrastructure noise — none of them rescue a lost plan.
- Three consecutive batches have lost the same plan with the same error. This is the longest-standing unresolved failure in the iteration history.
- The fix is a single-line addition with near-zero regression risk.
- The error string is highly specific (`"eof while parsing"`) and targets a real provider-side truncation, not a model capability failure.

**Exact change:**

File: `worker_plan/worker_plan_internal/llm_util/llm_executor.py`, line 41

Current:
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

Change to:
```python
_TRANSIENT_PATTERNS: list[str] = [
    "rate limit", "rate_limit", "ratelimit", "429",
    "timeout", "timed out", "connection", "connect",
    "temporarily unavailable", "503", "502", "500",
    "overloaded", "capacity", "try again",
    "server error", "internal error",
    "nonetype", "'none' object", "none' object is not",
    "eof while parsing",
]
```

**Caveat:** For this retry to fire, there must be a fallback model configured in the chain for the gpt-oss-20b runner. If gpt-oss-20b is the only model in the chain, the transient classification causes a retry but with no alternative model available. Verify that the runner config for this model includes at least one fallback (e.g., a second provider variant) before expecting 35/35 success. If no fallback is configured, pair this with direction 2 (schema slimming) to reduce the likelihood of truncation in the first place.

---

## Deferred Items

**D1 — Add RetryConfig to optimizer runner (code_codex B2):** The optimizer constructs `LLMExecutor` without `RetryConfig`, while the production pipeline at `run_plan_pipeline.py:171–174` passes `retry_config=RetryConfig()`. This gap means validation retries (e.g., a lever with wrong option count) get only one attempt in the optimizer. Lower priority than the EOF fix because validation retries are less common than plan failures, but worth aligning.

**D2 — Remove `strategic_rationale` and `summary` from `DocumentDetails` (direction 2):** Deferred until after direction 1 because it requires: (a) verifying no downstream code reads raw JSON `summary`; (b) updating the system prompt to remove section 4; (c) considering whether a post-merge diagnostic summary call would be valuable. Combine with direction 3 (fix description) if the field is kept.

**D3 — Add `@field_validator` on `consequences` (direction 4):** qwen3 is not a primary target model for the prompt optimizer. If qwen3 is removed from the model pool or deprioritized, this fix becomes lower value. Defer until qwen3's place in the rotation is confirmed.

**D4 — Pre-flight model name validation (direction 5):** The run-29 wasted starts are a one-time infrastructure annoyance. The stale `openrouter-paid-gemini-2.0-flash-001` alias in the LLM config should also be corrected directly (rename or remove it). The preflight validation is defense-in-depth against future config typos.

**D5 — Implement `review_lever` auto-correction in `check_review_format` (analysis/16 original recommendation, not yet implemented):** The validator at lines 86–99 only rejects non-conforming reviews; it does not auto-prepend "Controls ". Haiku's hong_kong recovery was prompt-driven (prompt_3), not code-driven. If haiku regresses on a new plan with the same "Controls" omission pattern, this will matter again. Auto-prepend logic (`if ' vs. ' in v and 'Weakness:' in v and not v.startswith('Controls '): v = 'Controls ' + v`) would provide a reliable safety net. Defer because prompt_3 appears to have resolved the immediate trigger.

**D6 — Investigate llama3.1 bracket contamination in call-3 (insight_claude N3, code_codex S2):** The third call's prompt injects prior lever names as a bracketed list (`[names_list]` at line 231–234), and the field descriptions themselves use `[direct first-order effect]` bracket placeholders. llama3.1 appears to interpret these as format templates on the third call. Potential fix: change the names injection format from `[{names_list}]` to a newline-separated list or numbered list without brackets. Low priority because this is a cosmetic quality issue (brackets in consequences, not plan failure) and llama3.1 still achieves 5/5 plan success.

**D7 — Investigate gpt-5-nano 136k output token anomaly (insight_claude reflection):** Run 26 generated 136k total tokens for the silo plan (vs. ~40k for other models). Cost is $0 (test/free tier), so this currently has no financial impact. If gpt-5-nano moves to a paid endpoint, this would be 3–4× the expected cost. Root cause likely: the model generates extremely verbose JSON per lever. Schema slimming (direction 2) would help reduce this automatically.
