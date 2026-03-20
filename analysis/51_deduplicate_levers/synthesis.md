# Synthesis

## Cross-Agent Agreement

Only one insight file (`insight_claude.md`) and one code review file (`code_claude.md`) are present — both from the same model. Consensus across the two analyses:

- **Verdict: KEEP.** PR #374 is a significant improvement over its predecessors. The categorical primary/secondary/remove schema (from PR #372) combined with the single-batch architecture (from PR #373) is superior to either alone.
- **Deduplication restored.** 6 of 7 models now correctly remove 1–6 levers per plan with lever-ID-citing justifications — a capability completely absent in the PR #373 Likert baseline (0 removes across all capable models).
- **llama3.1 timeout is the main residual issue.** silo and parasomnia plans both hit exactly 120s, triggering the robustness fallback (18/18 primary, zero real classification). This is better than PR #373's catastrophic 1-lever output but still produces zero-quality deduplication.
- **The failure path has a critical observability gap.** When the LLM call fails entirely (B1), `outputs.jsonl` still records `status="ok"` and `calls_succeeded=1`. A fully-degraded run is indistinguishable from a clean run without reading every `_raw.json` file and scanning for the fallback justification string.
- **B2 is a straightforward one-line bug.** `user_prompt=project_context` at `deduplicate_levers.py:272` stores the project description (a subset of the prompt) instead of the full assembled prompt that was actually sent to the LLM.

---

## Cross-Agent Disagreements

No true cross-agent disagreement exists (both files are from the same model). One internal tension worth noting:

**Insight says the fallback is "honest and auditable" because the justification text is identifiable.** Code review says this is a problem because `outputs.jsonl` records `status="ok"`. Both are correct about different audiences: a human reading `_raw.json` can spot the fallback string, but an automated pipeline reading `outputs.jsonl` cannot. The resolution is: both are true simultaneously, and both point to the same fix — emit a structured event alongside the fallback.

Source code confirms all five bugs flagged by the code review:
- **B1 confirmed**: `deduplicate_levers.py:196–205` — `batch_result` stays `None` after `except Exception`, execution falls through to the fallback path with no re-raise.
- **B2 confirmed**: `deduplicate_levers.py:272` — `user_prompt=project_context` is literally present in the file; the local variable `user_prompt` (constructed at lines 179–183) holds the full prompt.
- **B3 confirmed**: `runner.py:155` — `calls_succeeded=1  # single batch call` is hardcoded with a comment.
- **B4 confirmed**: Lines 229–236 — `logger.warning(...)` only; no event emitted to `events.jsonl`.
- **S1 confirmed**: `LLMExecutor(llm_models=llm_models)` at `runner.py:206` uses defaults `max_retries=0`, `max_validation_retries=0` — no retry before total fallback fires.

---

## Top 5 Directions

### 1. Fix silent failure masking and expose LLM success state (B1 + B3 + S2)
- **Type**: code fix
- **Evidence**: code_claude B1, B3, S2; insight N1, N5; confirmed in `deduplicate_levers.py:196–205`, `runner.py:151–156`
- **Impact**: Affects every future iteration's measurement fidelity. Currently 2/35 runs (llama3.1 silo + parasomnia) show `status="ok"` and `calls_succeeded=1` despite zero real LLM classification. Without this fix, the self-improvement loop cannot programmatically distinguish a clean run from a fully-degraded one. Fixing this enables downstream analysis scripts to filter degraded runs out of quality metrics.
- **Effort**: medium — requires adding a `llm_call_succeeded: bool` field to the `DeduplicateLevers` dataclass (set to `batch_result is not None`), then reading it in `_run_deduplicate()` to set `status="degraded"` and `calls_succeeded=0` appropriately.
- **Risk**: Low. The fallback logic itself (keep all as primary) is unchanged — only the reported status changes. Downstream pipeline steps that read `deduplicated_levers` are unaffected.

### 2. Emit structured `classification_fallback` events (B4 + I1)
- **Type**: code fix
- **Evidence**: code_claude B4, I1, I2; insight C1, Q5; confirmed — no event emission in `deduplicate_levers.py:228–236` or `runner.py`
- **Impact**: Enables the analysis pipeline to detect and count degraded runs programmatically by reading `events.jsonl` alone, without scanning every `_raw.json`. Differentiates the two fallback causes: total LLM failure (all 18 missing) vs. partial omission (gpt-oss-20b missing 1 lever). Also provides the missing middle state in `events.jsonl` (currently only `run_single_plan_complete` or `run_single_plan_error` are emitted — never "completed with degradation").
- **Effort**: medium — add an event emission call in the fallback path inside `DeduplicateLevers.execute()` (or plumb a signal back to `runner.py` via the returned object) with fields: `plan_name`, `fallback_count`, `cause` (`"llm_failed"` or `"lever_missing"`).
- **Risk**: Low. Additive change; existing consumers of `events.jsonl` that don't know the new event type will ignore it.

### 3. Fix `user_prompt` field stores wrong value (B2)
- **Type**: code fix
- **Evidence**: code_claude B2, Gap 3; confirmed at `deduplicate_levers.py:272`
- **Impact**: One-line fix. The `_raw.json` saved files currently store only the project description in `user_prompt`, making it impossible to reconstruct the exact LLM prompt from the saved file alone. This affects debugging and reproducibility for all 35 runs. The variable `user_prompt` (the full assembled prompt including levers JSON) is in scope on line 272 but `project_context` is passed instead.
- **Effort**: trivial — change `user_prompt=project_context` to `user_prompt=user_prompt` at `deduplicate_levers.py:272`.
- **Risk**: None. Purely changes what is saved in the artifact; no pipeline behavior changes.

### 4. Increase llama3.1 per-model timeout (I4)
- **Type**: workflow change (config)
- **Evidence**: insight N1, H1, C2; code_claude I4; both analyses agree on the cause and fix
- **Impact**: Directly fixes 2/5 plans (silo and parasomnia) for llama3.1, converting silently-degraded 18/18-fallback runs into real categorical classification. Both plans hit exactly 120s (the `request_timeout` in the llm config JSON), confirming the timeout — not the model — is the bottleneck. The gta_game plan completes at 65–90s with valid output, confirming llama3.1 can produce correct classifications given more time.
- **Effort**: trivial — change `request_timeout` in the `ollama-llama3.1` LLM config JSON from 120 to 240 (no code change needed). The `DEFAULT_PLAN_TIMEOUT = 600` in `runner.py` is not the bottleneck.
- **Risk**: Low. Worst case: llama3.1 takes 240s on complex plans instead of 120s, still producing fallbacks. The only downside is slower failure detection for local model issues.

### 5. Add missing-lever-id verification and targeted retry (I5 + I6)
- **Type**: code fix
- **Evidence**: code_claude I5, I6; insight N3, H3, C3; gpt-oss-20b omitted `dcb03988` in hong_kong_game (run 65)
- **Impact**: Handles partial classification failures (model returns valid response but omits one lever_id). Currently the code already detects missing IDs (lines 228–236) but applies the generic primary fallback silently. A retry with explicit prompt `"You missed these lever_ids: [dcb03988] — classify them now"` would recover the real classification. Affects rare cases (1/35 runs in this dataset) but is a general correctness improvement.
- **Effort**: medium — add a post-response missing-ID check that constructs a follow-up message for any omitted lever_ids, using the existing `LLMExecutor.run()` mechanism for one retry.
- **Risk**: Low. The retry path only fires when the primary path missed IDs. No behavioral change for the 34/35 runs that had complete responses.

---

## Recommendation

**Pursue directions 3 + 1 + 2 in a single PR, in that order of implementation.**

Start with **B2** (one line, zero risk, verifiable immediately), then add **B1+B3** (expose `llm_call_succeeded` flag), then **B4** (emit `classification_fallback` event). These three are all in `deduplicate_levers.py` and `runner.py` and address a single root problem: the failure path is invisible to automated analysis.

**Specific changes:**

**File: `deduplicate_levers.py`**

1. Line 272 — fix B2:
   ```python
   # Before:
   user_prompt=project_context,
   # After:
   user_prompt=user_prompt,
   ```

2. Add `llm_call_succeeded: bool` to the `DeduplicateLevers` dataclass (line ~150):
   ```python
   @dataclass
   class DeduplicateLevers:
       user_prompt: str
       system_prompt: str
       response: List[LeverDecision]
       deduplicated_levers: List[OutputLever]
       metadata: List[Dict[str, Any]]
       llm_call_succeeded: bool  # False when LLM call failed entirely (batch_result is None)
   ```

3. After the `except` block (line ~205), set the flag:
   ```python
   batch_result: BatchDeduplicationResult | None = None
   llm_call_succeeded = False
   metadata_list: List[dict] = []
   try:
       result = llm_executor.run(execute_function)
       batch_result = result["chat_response"].raw
       metadata_list.append(result.get("metadata", {}))
       llm_call_succeeded = True
   except PipelineStopRequested:
       raise
   except Exception as e:
       logger.error(f"Batch deduplication call failed: {e}")
   ```

4. At the end of the missing-ID loop (after line 236), add event/log distinction for total vs partial failure:
   ```python
   if not llm_call_succeeded:
       logger.warning(
           f"LLM call failed entirely — all {len(input_levers)} levers defaulted to primary."
       )
       # Update justification to distinguish from partial miss:
       for d in decisions:
           if d.justification == "Not classified by LLM. Keeping as primary to avoid data loss.":
               d.justification = "LLM call failed — no classifications received. Keeping as primary to avoid data loss."
   ```

5. Pass `llm_call_succeeded` to the constructor at line 271.

**File: `runner.py`**

6. In `_run_deduplicate()` (lines 151–156), read the flag:
   ```python
   return PlanResult(
       name=plan_name,
       status="ok" if result.llm_call_succeeded else "degraded",
       duration_seconds=0,
       calls_succeeded=1 if result.llm_call_succeeded else 0,
   )
   ```

7. Emit a `classification_fallback` event when `result.llm_call_succeeded` is `False` or when any lever got the fallback justification (check `result.response` for entries with the fallback justification string).

**Why this cluster first:**
The self-improvement loop reads `outputs.jsonl` to measure success rates. With B1+B3 unresolved, the 2 degraded llama3.1 runs count as successes — inflating the 35/35 "100% success" metric. Fixing B1+B3 changes those to `status="degraded"`, making the true success rate 33/35 (94%) for PR #374. Future iterations will be measured against this accurate baseline. B4 makes the degradation visible in `events.jsonl` for programmatic detection.

B2 is bundled because it's a one-line fix in the same file with zero risk, and having the correct `user_prompt` in the saved artifacts matters for debugging the timeout cases that these fixes will make visible.

---

## Deferred Items

**I4 — Increase llama3.1 timeout to 240s (config change).**
Should be done as a separate minimal PR (config JSON change only, no code). This directly fixes 2/35 degraded runs for llama3.1 without any code risk. Defer slightly so it can be measured against the corrected observability baseline established by the main PR.

**I5+I6 — Missing-lever-id retry (direction 5).**
Worth doing in a follow-up iteration. The gpt-oss-20b partial miss (1/35 runs) is a low-frequency event but reflects a general model behavior (truncating output near the end of large responses). A targeted retry is more correct than the primary fallback. Defer until after the observability fixes make it possible to count fallback frequency reliably.

**N4 — Inter-model classification variance.**
High variance in primary/secondary assignment across models for the same lever (e.g., "Technology Integration" is primary for llama3.1, primary for gpt-oss-20b, but `remove` for haiku). This is an inherent limitation of the subjective "gating the core outcome" criterion. Possible mitigation: add concrete anchor examples to the system prompt for each classification level (analogous to the review_lever examples in identify_potential_levers.py). Low urgency — downstream FocusOnVitalFewLevers further filters the primary/secondary set.

**Q4 — Verify downstream consumption of primary/secondary field.**
The insight file asks: if nothing downstream filters on the primary/secondary distinction, the classification may be providing false confidence. This should be verified by reading EnrichLevers and FocusOnVitalFewLevers before investing in further classification calibration.

**S4 — Minimum lever count threshold too low.**
`max(3, len(input_levers) // 4)` = 4 for 18-lever input. A model removing 14/18 levers (78%) still clears the warning threshold. Consider raising to `max(5, len(input_levers) // 3)` in a separate PR after more data on typical removal rates per model.
