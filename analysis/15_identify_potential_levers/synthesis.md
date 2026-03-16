# Synthesis

## Cross-Agent Agreement

All four agents agree on the following:

1. **`break` → `continue` in the call-2/3 failure handler** is the single highest-leverage, lowest-risk code fix. Every agent flags it independently (insight_claude C1, code_claude B1/I1, code_codex B1/I1). The line at `identify_potential_levers.py:278` is confirmed in source.

2. **All-or-nothing Pydantic validation is a real architectural problem.** When any one `Lever` fails validation, the entire `DocumentDetails` response is discarded. code_claude labels it B4, code_codex labels it S2/I3, and insight_claude's N1 documents the concrete incident (gpt-5-nano parasomnia: 6 levers all invalid → 357 seconds of compute wasted, plan fails).

3. **qwen3-30b `consequences` contamination** (review text leaking into the `consequences` field) is persistent and affects ~33% of levers in sampled runs. All agents agree a post-parse repair validator is the right fix.

4. **Bracket placeholder leakage** from `[Tension A]`, `[Tension B]`, `[specific factor]` embedded in Pydantic field descriptions flows directly into LLM output (confirmed in run 1/12 hong_kong_game). Both code reviews flag it as a structural prompt/schema issue (code_codex S1/I4; insight_codex H4/C3).

5. **prompt_3 successfully fixed llama3.1's `review_lever` format failures for silo and sovereign_identity.** This is the confirmed positive result of the iteration (insight_claude H1/P1; code_claude confirms check_review_format is what llama3.1 was hitting).

6. **`check_review_format` validator is weaker than documented.** It checks for `'Controls '` and `'Weakness:'` but not `' vs. '`, the `The options fail to consider` wording, or the two-sentence constraint (code_claude S3; code_codex B2).

---

## Cross-Agent Disagreements

### Disagreement 1: Did run 1/12 parasomnia produce a `ValidationError`?

- **insight_claude** (N1, E2): Yes. Cites `history/1/12_identify_potential_levers/events.jsonl` lines 18–19 and `outputs.jsonl` showing parasomnia with `"status": "error"` and 6 ValidationError entries (`review_lever = 'Not applicable here'`).
- **insight_codex**: Claims "I found **no** `ValidationError`/Pydantic-schema failures in `events.jsonl` or `outputs.jsonl` for Runs 09–16."

**Verdict: insight_claude is correct.** code_claude B4 describes the exact all-or-nothing validation architecture that would produce this failure. The source code at lines 60–99 confirms hard validators on `options` (exactly 3) and `review_lever` (must contain `'Controls '` and `'Weakness:'`). A response with `review_lever = 'Not applicable here'` for all 6 levers would definitively fail these validators, causing the entire `DocumentDetails` to be rejected. insight_codex likely searched the second-attempt events files or used a different keyword. The code architecture makes insight_claude's finding structurally inevitable.

### Disagreement 2: `review_lever` exact compliance rates

- **insight_claude**: "Every output file I inspected showed `review` fields in the required format." Only run 1/12 parasomnia had a validation failure.
- **insight_codex**: Shows many runs with low exact review compliance (run 13: 15/85, run 15: 17/90, run 16: 0/77) by strict regex.

**Verdict: Both are correct for different definitions.** insight_claude is checking whether the validator *passes* (contains `'Controls '` and `'Weakness:'`), which is a weak check. insight_codex uses a strict regex for the complete two-sentence formula. Most outputs pass the validator while failing strict literal conformance. The validator at lines 95–99 only checks substrings, so near-misses like `"Controls bulk procurement vs. modular sourcing. Weakness: The options ignore supply chain resilience"` pass the code check but fail the strict pattern. This gap is B2 in code_codex and S3 in code_claude.

### Disagreement 3: Run quality ranking

- **insight_codex** ranks run 14 (gpt-4o-mini) as #1 overall and run 12 (gpt-5-nano) as #3 for summary compliance.
- **insight_claude** flags gpt-5-nano as having the worst failure mode (N1, N2) and gpt-4o-mini as unproblematic.

**Verdict: Not a real contradiction.** insight_codex ranks by output *quality* metrics (uniqueness, consequence depth, format compliance), not reliability. insight_claude ranks by *success rate*. Both perspectives are valid for different optimization objectives.

---

## Top 5 Directions

### 1. Per-lever salvage: filter bad levers instead of rejecting entire responses
- **Type**: code fix
- **Evidence**: code_claude B4/I3; code_codex S2/I3; insight_claude N1 (gpt-5-nano parasomnia: 357 seconds wasted when 6 levers all failed). Confirmed by source: `DocumentDetails` uses Pydantic structured validation over the whole `levers` list, so one bad `Lever` aborts the full call.
- **Impact**: Prevents complete plan failure when even one lever is malformed. In run 1/12 parasomnia, all 6 levers had the same bad `review_lever` value — but for any model that produces 6 good levers and 1 bad one, the 6 good ones are silently discarded. This affects all models that occasionally produce non-compliant levers. Success rate improvement: 32/35 → potential 33+/35.
- **Effort**: Medium. Requires extracting JSON first, then validating levers individually (e.g., in a try/except per-lever loop or a `@model_validator` that filters instead of rejects). The structured LLM call at line 249 (`sllm.chat(messages_snapshot)`) returns a `DocumentDetails` object; the fix must happen either at parse time or by switching to raw JSON parsing + per-item validation.
- **Risk**: Downstream steps must handle variable lever counts gracefully. `DeduplicateLeversTask` already does. The `min_length=5` constraint on `DocumentDetails.levers` may need loosening or per-call relaxation.

---

### 2. `break` → `continue` in the call-2/3 failure handler
- **Type**: code fix
- **Evidence**: insight_claude C1; code_claude B1/I1; code_codex B1/I1. Unanimously flagged. Source line 278 confirmed: `break` when `len(responses) > 0`.
- **Impact**: When call-2 fails, call-3 currently never runs. Fixing to `continue` allows call-3 to attempt generation, potentially recovering 5–7 additional levers. Affects all models that experience transient call-2 failures (timeouts, auth errors, parsing errors). No runs in this batch had a call-2-specific failure, but it's a latent bug that silently degrades any partial-failure scenario.
- **Effort**: Trivial (one character change at line 278).
- **Risk**: None. If call-3 also fails, the existing `len(responses) == 0` guard on the first exception prevents empty-result propagation; subsequent exceptions fall into the same `break`-after-warning path (now `continue`, which terminates the loop anyway if call_index == total_calls).

---

### 3. Post-parse `consequences` contamination repair validator
- **Type**: code fix
- **Evidence**: insight_claude N6/C3; code_claude I3; code_codex I2; insight_codex H4/C3. qwen3-30b consistently embeds `"Controls ... Weakness: ..."` review text at the end of `consequences`. ~33% of levers in run 1/13 silo; potentially higher across other plans.
- **Impact**: Cleans qwen3 output without rejecting levers or requiring additional LLM calls. Downstream steps receive unpolluted `consequences` fields. Quality improvement for all qwen3 runs.
- **Effort**: Low. Add a `@field_validator('consequences', mode='after')` to `Lever` that detects and strips any trailing `"Controls … Weakness: …"` suffix (regex: `r'\s*Controls\s.+?Weakness:.+$'` with `re.DOTALL`).
- **Risk**: Low. The repair strips only what the field description already prohibits. An overly broad regex could strip legitimate text; use a conservative pattern anchored to the end of the string after the `Systemic/Strategic` chain.

---

### 4. Add a scientific/research domain worked example to the `review_lever` prompt instruction
- **Type**: prompt change
- **Evidence**: insight_claude H2/N1; insight_codex H1. gpt-5-nano returned `"Not applicable here"` for all 6 parasomnia levers — the model could not map `"Controls [Tension A] vs. [Tension B]"` to a medical research context. insight_codex H1 recommends adding invalid examples alongside the valid example.
- **Impact**: Prevents the "domain doesn't have strategic tensions" failure mode for scientific/medical plans. Affects any model that struggles to apply business-framing templates to research contexts. Currently gpt-5-nano is the confirmed failure; potentially other models could hit this on future scientific plans.
- **Effort**: Low. Add one concrete worked example using a research domain (e.g., parasomnia or similar):
  > `Controls participant recruitment breadth vs. data quality stringency. Weakness: The options fail to consider protocol fatigue effects on long-term retention.`
  Place it immediately after the two-sentence format spec in the `review_lever` field description (line ~53) or in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (line ~178).
- **Risk**: Low for compliant models. May slightly increase prompt length, which matters for llama3.1 timeouts on parasomnia.

---

### 5. Post-parse `review_lever` canonicalizer for near-miss normalization
- **Type**: code fix
- **Evidence**: insight_codex C1; code_codex I2; code_claude noted S3. Run 11: 53/62 exact. Run 14: 58/89 exact. Run 16: 0/77 exact — but these are semantic near-misses, not garbage. A canonicalizer in `LeverCleaned` construction (lines 299–305) could normalize `"Controls A and B"` → `"Controls A vs. B."` and `"Weakness: options omit X"` → `"Weakness: The options fail to consider X."` using a template rewrite.
- **Impact**: Large jump in formal exact-match compliance without another LLM call. Affects runs 13, 14, 15, 16 that produce semantically correct but syntactically drifted reviews. Particularly high value if downstream evaluation uses exact string matching.
- **Effort**: Medium. Requires careful regex/NLP parsing to identify and rewrite `Controls ... vs. ...` and `Weakness:` clauses without corrupting valid content. A regex-based approach is fragile; a simple template extraction may be more robust (extract the two tensions and the weakness phrase, then reformat).
- **Risk**: Medium. Overcorrection could transform a slightly-off but meaningful review into a syntactically correct but semantically flattened one. Needs test coverage.

---

## Recommendation

**Implement `break` → `continue` first** (Direction 2), followed immediately by Direction 1 (per-lever salvage).

Rationale for doing Direction 2 first:

1. **Zero risk, one character.** The fix at `identify_potential_levers.py:278` changes `break` to `continue`. It cannot regress any existing behavior. Every analysis agent agrees it should be done.

2. **It is a prerequisite for accurately measuring Direction 1's impact.** If call-2 is silently broken and call-3 never runs, the "per-lever salvage" fix (Direction 1) only recovers levers from a truncated two-call result. Fixing call-loop continuity first gives the correct baseline for measuring salvage value.

3. **It applies universally.** The `break` bug fires for any model on any plan when call-2 encounters an exception. The all-or-nothing validation failure (Direction 1) is currently only confirmed for gpt-5-nano on parasomnia; `break` affects all models with transient call-2 failures.

**Specific change:**
- **File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- **Line:** 278
- **Change:** `break` → `continue`
- **Optional addition (line 275):** emit a structured partial-recovery log event:
  ```python
  logger.warning(
      f"Call {call_index} of {total_calls} failed [{llm_error.error_id}], "
      f"continuing to next call. Partial results: {len(responses)} call(s), "
      f"{sum(len(r.levers) for r in responses)} levers."
  )
  continue  # was: break
  ```

After merging this fix, the next PR should implement Direction 1 (per-lever salvage) to address the gpt-5-nano all-or-nothing failure mode, followed by Direction 3 (consequences repair validator) for qwen3 output quality.

---

## Deferred Items

**Near-term (next 1–2 iterations):**

- **Direction 1 (per-lever salvage):** Do this immediately after Direction 2 lands. It addresses the highest-severity single failure mode (357s wasted, plan fails).
- **Direction 3 (consequences repair validator):** Low effort, high quality gain for qwen3. Add after per-lever salvage.
- **Direction 4 (domain example in prompt):** Add a research/medical worked example for `review_lever`. Low effort.

**Medium-term:**

- **Direction 5 (review_lever canonicalizer):** Worth doing once the validation architecture (Directions 1–2) is stable. Requires careful implementation to avoid semantic corruption.
- **Strengthen `check_review_format`** (code_claude S3, code_codex B2): Add `' vs. '` check to the validator at `identify_potential_levers.py:95–96`. Low effort but currently blocked by the all-or-nothing architecture — strengthening the validator would increase rejection rates until Direction 1 is in place.
- **Remove bracket placeholders from Pydantic field descriptions** (code_codex S1/I4): Replace `[Tension A]`, `[Tension B]`, `[specific factor]` in field `description=` strings with concrete non-copyable examples. Addresses run 1/12 placeholder leakage.

**Lower priority:**

- **`set_usage_metrics_path` thread-safety** (code_claude B2/I4): Move inside the `with _file_lock:` block at `runner.py:106`. Real race condition but impact is limited to `usage_metrics.jsonl` correctness.
- **Resume summary deduplication** (code_claude S2/I5): Fix `runner.py:462–468` to deduplicate by plan name before counting, so resumed runs report "5/5" not "5/6".
- **Adaptive call count** (code_codex I6): Stop calling at 3 regardless; stop early once enough unique levers exist. Reduces token waste but requires new logic.
- **`strategic_rationale` / `summary` token cost** (code_codex I5): These fields are generated but discarded from `LeverCleaned`. Consider removing them from `DocumentDetails` or making them optional to reduce generation cost on slow models (gpt-5-nano total: ~2963s for 5 plans).
- **gpt-oss-20b hong_kong_game JSON failure** (insight_claude N4/H3, E5): Consistently fails JSON extraction on this plan across runs 1/03 and 1/11. Likely context-length sensitivity. Requires investigation of hong_kong_game plan size vs. other plans.
- **llama3.1 parasomnia timeout** (insight_claude N3): 120s timeout is too short for the parasomnia plan. Consider a plan-adaptive timeout or a plan-specific context reduction.
- **Runner cleanup hardening** (code_codex B3/I7): Wrap `_run_plan_task()` in its own try/except for terminal event writing. This explains run 1/09's "start-only" incomplete state.
