# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **PR #289 validators are correct and working as designed.** Both `check_option_count` and `check_review_format` caught real violations that previously shipped silently: 3 two-option levers and 7 malformed review fields in run 89 are now blocked. No malformed levers appear in any post-PR successful artifact. The targeted bugs are fixed.

2. **The B1/cascade bug is the critical unresolved issue.** The 3-call loop in `execute()` at `identify_potential_levers.py:231–240` re-raises any exception, discarding all accumulated `responses`. With validators now rejecting calls more frequently — especially for llama3.1, which has near-zero compliance with the combined `review_lever` format — this converts "malformed output" into "no output" for entire plans. Two plans (silo, gta_game) in run 95 produce zero levers despite the model generating 9+ before failing.

3. **Partial result recovery (Direction 2) is urgently needed.** PR #289 shipped Direction 1 alone; the analysis/12 assessment explicitly flagged this as a prerequisite companion and warned of the cascade risk. All four agents call this the highest-priority next fix.

4. **Consequence contamination persists unchanged.** 71 levers before the PR and 71 after have `consequences` fields ending with `"Controls … Weakness: …"` text that belongs in `review_lever`. The PR does not address this. All agents flag it; none disagree.

5. **Overall success rate (28/35 → 31/35) is inflated by model lineup change.** Shared-model success rate regressed 92% → 84% as a side effect of validators correctly catching violations. All agents agree this is the validators working correctly, not a quality regression.

---

## Cross-Agent Disagreements

### Disagreement 1: PR verdict (KEEP vs. CONDITIONAL)

- **insight_codex**: KEEP — "the new failures are an acceptable trade if the next iteration addresses repair/retry strategy."
- **insight_claude, code_claude, code_codex**: CONDITIONAL — PR is incomplete without Direction 2; validators converting "malformed output" to "no output" is worse from a user perspective.

**Verdict**: CONDITIONAL is correct. The validators are right, but the cascade effect makes llama3.1 plans produce zero levers instead of imperfect levers. This is a meaningful regression that warrants the condition. insight_codex's KEEP verdict is based on the same evidence but treats the regression as acceptable — this is a values call, not a factual disagreement.

### Disagreement 2: Multilingual concern for check_review_format

- **code_codex** (B1): Flags that `check_review_format` uses English literals (`"Controls "`, `"Weakness:"`) and cites `prompt_optimizer/AGENTS.md:165-168` as establishing that validators must be language-agnostic because plans may be multilingual.
- **code_claude, insight_claude, insight_codex**: Do not raise this concern.

**Verdict**: The multilingual concern is theoretically valid, but all 5 plans currently tested (silo, gta_game, hong_kong_game, sovereign_identity, parasomnia) are English-language plans. All successful post-PR runs pass the validator cleanly. The concern is real but low-priority given the current test matrix. Verified: the system prompt at `identify_potential_levers.py:127–168` is English-only, so non-English generation would require a different prompt first.

### Disagreement 3: Root cause of template leakage

- **code_codex** (S1): Identifies the specific prompt contradiction: line 15 of the prompt teaches "conservative → moderate → radical" as the design pattern, while line 32 prohibits `Conservative:`, `Moderate:`, `Radical:` labels. The contradiction is the root cause of the 20 leakage cells in the after runs.
- **insight_codex**: Observes leakage worsened after the PR but does not identify the prompt contradiction.
- **code_claude, insight_claude**: Do not identify this root cause.

**Verdict**: code_codex's S1 is the most specific and plausible explanation. Source code at `identify_potential_levers.py:138–142` confirms the system prompt says "Show clear progression: conservative → moderate → radical" while also listing "NO prefixes" at line 158. This tension is real and code_codex is likely right.

### Disagreement 4: check_review_format validator strength

- **code_codex** (B4) and **code_claude** (E1): Both note the validator only checks for substring presence, not exact format — `vs` vs `vs.` punctuation, bracket placeholders, and two-sentence structure all pass. 71/563 post-PR levers still fail the stricter prompt shape.
- **insight_claude** and **insight_codex**: Confirm this observation in the data but do not count it as a validator bug.

**Verdict**: Both code review agents are correct. Confirmed by source: the field description at `identify_potential_levers.py:53–57` requires exact two-sentence format `"Controls [A] vs. [B]. Weakness: ..."`, but the validator (on the PR branch) only checks for `"Controls "` and `"Weakness:"` substrings. The validator is weaker than the contract, but stronger than nothing.

---

## Top 5 Directions

### 1. Partial result recovery in the 3-call loop (B1 fix)
- **Type**: code fix
- **Evidence**: Confirmed bug in `identify_potential_levers.py:231–240`. All four agents flag this. code_claude (I1), code_codex (B3/I2), insight_claude (C1), insight_codex (C2) all recommend this fix. Run 95 produces 0 output for 2 plans because of it.
- **Impact**: Directly fixes the llama3.1 cascade (silo, gta_game in run 95 → 0 levers) and the haiku cascade (silo in run 1/01 → 0 levers). Any future validator addition will also benefit. Converts "1 bad call → all 3 calls discarded" into "1 bad call → 2 calls' levers returned with warning." Affects every model under failure conditions.
- **Effort**: Low — change `raise llm_error from e` to `if len(responses) == 0: raise; else: break` in the exception handler at line 236–240. Add a metadata flag for partial completion. ~5 lines.
- **Risk**: If the first call fails (no data at all), behavior is unchanged (still re-raises). The only change is: when call 2 or 3 fails after prior successes, return what was accumulated. No risk of shipping zero-data results — the guard is `len(responses) == 0`.

### 2. Consequences contamination repair validator
- **Type**: code fix (field validator with repair logic, not rejection)
- **Evidence**: 71/514 before-PR levers and 71/563 after-PR levers have `consequences` ending with `"Controls … Weakness: …"` text. Confirmed in source: `identify_potential_levers.py:42–44` already prohibits this ("Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field") but there is no enforcement. code_claude (I4), code_codex (I3), insight_claude (N5, C1), insight_codex (C1 repair pass) all flag this.
- **Impact**: Affects 12.6% of shipped levers across all models. Specifically confirmed in qwen3 (run 98), gpt-oss-20b (run 96). Implementing as a repair (truncate at first `"Controls "` or `"Weakness:"` occurrence in `consequences`) rather than a rejection avoids any cascade failures and directly improves output quality for all models.
- **Effort**: Low — add a `@field_validator('consequences', mode='after')` to `Lever` that truncates the tail. No rejection, just repair. ~10 lines.
- **Risk**: Repair could truncate legitimate content that happens to use the word "Controls". Low risk given the specificity of "Controls X vs. Y." as a format marker. Can be scoped to match only at sentence boundaries.

### 3. Fix prompt contradiction causing template leakage
- **Type**: prompt change
- **Evidence**: code_codex (S1) identifies the specific contradiction: `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` at line 138 instructs "Show clear progression: conservative → moderate → radical" and at line 158 prohibits `Conservative:`, `Moderate:`, `Radical:` prefixes. Template leakage worsened in after runs (0 → 20 cells). insight_codex H2 also recommends negative examples for these labels.
- **Impact**: Affects models that try to follow the "conservative → moderate → radical" framing literally (llama3.1 in run 95 sovereignty outputs, haiku). Removing the explicit label names from the progression description eliminates the contradiction. Secondary benefit: reduces bracket placeholder leakage (S2) if combined with a concrete output example.
- **Effort**: Low — edit the system prompt. Change "Show clear progression: conservative → moderate → radical" to something like "Show a range from cautious to transformative approaches" without naming the banned labels. ~2 lines.
- **Risk**: May slightly reduce structural clarity for models that benefit from the explicit progression. Low risk — the prohibition already exists; making the two instructions consistent is safe.

### 4. llama3.1 review_lever format fix (prompt example)
- **Type**: prompt change
- **Evidence**: insight_claude (H1): llama3.1 treats `review_lever` as two alternative formats ("Controls X vs. Y." OR "Weakness: ..."), never combining them. Run 95 shows 100% alternating pattern — 0 levers have both components. This causes systematic failure after PR #289. The combined format is required but never demonstrated as a concrete single-field example.
- **Impact**: If llama3.1 learns to combine both components, run 95's 2 plan failures (silo, gta_game) would likely recover. However, this fix interacts with Direction 1: with partial result recovery in place, llama3.1 failures become partial results rather than total failures, so Direction 4 becomes less urgent.
- **Effort**: Low-Medium — add an explicit one-line example to the system prompt section 4 (`Validation Protocols`): `"Example: 'Controls rapid deployment vs. system stability. Weakness: The options fail to consider regulatory timeline.'"`
- **Risk**: Larger models (gpt-5-nano, qwen3, gemini) already comply; an example is unlikely to hurt them. Main risk: the example becomes a template that smaller models copy verbatim, producing low-diversity reviews.

### 5. Overflow telemetry for calls returning > 7 levers
- **Type**: code fix (observability)
- **Evidence**: Direction 3 from analysis/12 synthesis, not included in PR #289. code_claude (I3), insight_claude (C3). After removing `max_length=7` (correctly removed in an earlier PR), over-generation is invisible. Runs can return 15–20 levers without any log entry.
- **Impact**: Low direct impact on success rate, but high diagnostic value. Makes it possible to see when models over-generate without needing to manually inspect artifacts. Feeds future iteration analysis.
- **Effort**: Very low — add 3 lines after `responses.append(...)` at `identify_potential_levers.py:243`:
  ```python
  lever_count = len(result["chat_response"].raw.levers)
  if lever_count > 7:
      logger.warning(f"Call {call_index} returned {lever_count} levers (expected ≤7)")
  ```
- **Risk**: None. Read-only logging.

---

## Recommendation

**Implement Direction 1: Partial result recovery in the 3-call loop.**

**Why first**: This is the only fix that directly addresses the CONDITIONAL verdict on PR #289. The validators are correct; the cascade is the problem. Every other direction is lower urgency because:
- Without this fix, every future validator addition risks more plan-level failures.
- With this fix, llama3.1's 2 plan failures in run 95 recover to partial results (levers from calls 1 and 2, if they succeeded), and haiku's 1 plan failure in run 1/01 similarly recovers.
- It's 5 lines of code, no design ambiguity, confirmed fix, zero risk of regression on passing models.

**Exact change — file: `identify_potential_levers.py`, lines 231–240:**

Current code:
```python
try:
    result = llm_executor.run(execute_function)
except PipelineStopRequested:
    raise
except Exception as e:
    llm_error = LLMChatError(cause=e)
    logger.debug(f"LLM chat interaction failed [{llm_error.error_id}]: {e}")
    logger.error(f"LLM chat interaction failed [{llm_error.error_id}]", exc_info=True)
    raise llm_error from e
```

Replace with:
```python
try:
    result = llm_executor.run(execute_function)
except PipelineStopRequested:
    raise
except Exception as e:
    llm_error = LLMChatError(cause=e)
    logger.debug(f"LLM chat interaction failed [{llm_error.error_id}]: {e}")
    logger.error(f"LLM chat interaction failed [{llm_error.error_id}]", exc_info=True)
    if len(responses) == 0:
        raise llm_error from e
    logger.warning(f"Call {call_index} failed [{llm_error.error_id}], returning partial results from {len(responses)} prior call(s).")
    break
```

Also add a metadata flag after the loop so callers can detect partial completion:
```python
metadata["partial_result"] = len(responses) < total_calls
```

**Expected outcome**: llama3.1 run 95 recovers to partial output (levers from whichever of calls 1–3 succeeded before the validator rejection). The plan no longer produces zero output. The CONDITIONAL on PR #289 becomes KEEP.

---

## Deferred Items

**D1 — Consequences contamination repair (Direction 2 above)**: Implement after partial result recovery. It does not interact with the cascade and can be done in any order, but Direction 1 is higher urgency. Low risk, quick win.

**D2 — Prompt contradiction fix for template leakage (Direction 3)**: Implement as part of the next prompt iteration. Remove "conservative → moderate → radical" label names from the progression instruction to eliminate the contradiction with the prohibition. Also add a concrete `review_lever` example that shows both `Controls` and `Weakness:` in one string (addresses llama3.1 format confusion from Direction 4 at the same time).

**D3 — llama3.1 review_lever prompt example (Direction 4)**: Bundle with D2 into a single prompt PR. With partial result recovery in place (D1), llama3.1 failures become partial results rather than total plan failures, making this less urgent.

**D4 — Overflow telemetry (Direction 5)**: Trivial addition; include in any future PR as a drive-by improvement.

**D5 — Lever-level recovery (code_claude I2, code_codex I2)**: Larger refactor — parse each lever individually rather than as a `DocumentDetails` unit to allow "accept 6 of 7 levers" rather than "accept 0 of 7." Implement after Direction 1 is in place and the residual cascade-from-validators pattern is re-analyzed. Requires changing `sllm.chat` to return raw JSON and iterating.

**D6 — Multilingual validator concern (code_codex B1)**: Monitor as non-English plans are added. Currently all test plans are English; the English-literal `"Controls "` / `"Weakness:"` markers match the English system prompt. Revisit if multilingual plans enter the test matrix.

**D7 — runner.py race condition (code_claude B2, I5)**: `set_usage_metrics_path` called outside `_file_lock` at `runner.py:106` is a real race condition when `workers > 1`. Low risk for current single-user operation but worth fixing. Bundle with another runner.py PR.

**D8 — Exact review format validator tightening**: Current `check_review_format` only checks for keyword presence, leaving 71 levers with `vs` vs `vs.` drift, bracket placeholders, and incorrect ordering passing validation. A stricter regex (`r'Controls .+ vs\. .+\. Weakness: .+'`) would close this gap. Implement only after the prompt improvements (D2/D3) reduce the base rate of format drift, otherwise this creates more cascade failures.

**D9 — Soften "radical option must include emerging tech/business model" instruction (code_codex I6)**: Responsible for repeated blockchain tropes (7 identical options in sovereign_identity run 95). Replace with "radical option must be non-obvious and distinct from the other two" to allow domain-appropriate innovation without over-indexing on technology.
