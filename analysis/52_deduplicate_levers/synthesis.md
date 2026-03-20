# Synthesis

## Cross-Agent Agreement

Both the insight agent and code review agent agree on the following:

**PR #375 verdict: KEEP.** The primary objective — eliminating llama3.1 timeouts on the silo and parasomnia plans — is confirmed fixed. Before: 2/5 plans timed out and produced all-primary fallback output. After: 0/5 timeouts, 35/35 plans succeed with real LLM output.

**Shorter justifications work for capable models, not for llama3.1.** Capable API models (haiku, gpt-oss-20b) produce ~55% shorter justifications after the PR; llama3.1 is unchanged at ~40 words. Both agents attribute this to the lack of a hard constraint — only advisory text in the Pydantic field description (confirmed in `deduplicate_levers.py:83-85`).

**llama3.1 still produces 0 removes on the silo plan despite completing within timeout.** Both agents flag this as the main residual deficiency (insight N1, code review S2). The system prompt has a tension between "prefer secondary over remove" (lines 139-140) and "expect to remove 25-50%" (lines 141-143) that resolves in favor of the conservative instruction for weak models.

**OPTIMIZE_INSTRUCTIONS documents the old overlap-preference rule.** The code review (S3) and insight reflection both note that `deduplicate_levers.py:55-58` still says "the more general lever should survive; the specific one should be removed" — directly contradicting the PR's new "keep the one that better captures the strategic decision" rule.

**Silent total-failure risk is unresolved.** Both agents confirm B1: a complete LLM call failure in `deduplicate_levers.py:198-205` is silently swallowed; `runner.py:151-155` unconditionally returns `status="ok"` and `calls_succeeded=1`. Fallback text changed from "primary" to "secondary" (an improvement) but the core visibility gap remains.

---

## Cross-Agent Disagreements

There is one minor framing disagreement:

**The mechanism by which llama3.1's timeout was fixed.** The insight agent describes the improvement as "shorter output reduces generation time" and says "the mechanism is likely a Pydantic max_length constraint." The code review corrects this: there is **no** Pydantic max_length — only advisory text. The insight's characterization of the mechanism is wrong in its parenthetical guess, but its causal observation is correct (shorter output → completed within timeout). Source of truth: `deduplicate_levers.py:83-85` — no `max_length` parameter exists. Code review is correct; the constraint is advisory-only.

This disagreement has a practical consequence: the timeout fix is more fragile than the insight implies. A future plan with more levers or more complex content could re-trigger the timeout because llama3.1 ignores the advisory and still writes ~40-word justifications (the timeout was cleared by only ~5 seconds margin on the silo plan).

---

## Top 5 Directions

### 1. Fix the system prompt instruction ordering that causes llama3.1 to produce 0 removes
- **Type**: prompt change
- **Evidence**: Insight N1 + code review S2. Run 71 (llama3.1, silo): 0 removes despite completing within timeout. Levers `ee0996f6` and `19e66d20` clearly overlap primary levers but are classified primary/secondary. Root cause is `DEDUPLICATE_SYSTEM_PROMPT` lines 139-143: "prefer secondary over remove" appears before "expect to remove 25-50%". For weak models the conservative instruction wins and effectively vetoes the expected-removal guidance. Capable models (haiku, gemini) correctly remove both levers in the same plan.
- **Impact**: Improves llama3.1 classification quality from 0-remove (low signal, keeps near-duplicates) to some removes (better signal, reduces noise for downstream steps). Affects all weak-model runs on any plan. Content quality improvement: downstream FocusOnVitalFewLevers and ScenarioGeneration receive a cleaner, deduplicated lever set.
- **Effort**: Low — prompt reordering in `deduplicate_levers.py:133-143`. No schema changes.
- **Risk**: Could slightly increase removal rate for borderline levers across all models. The safeguard ("prefer secondary when genuinely uncertain after comparing") should prevent over-aggressive removal for capable models. Worth verifying in the next iteration.

### 2. Add Pydantic max_length constraint to the justification field
- **Type**: code fix
- **Evidence**: Code review S1 + insight N2. The PR's timeout fix works for capable models because they follow the "~20-30 words" advisory. llama3.1 produces ~40 words unchanged. The silo timeout margin is only ~5 seconds (114.75s vs. 120s). A future plan with more levers or more verbose content will trigger a timeout again because the length constraint has no enforcement teeth.
- **Impact**: Makes the timeout fix model-agnostic. A `max_length=200` constraint (≈30-35 words) in the Pydantic field forces llama3.1 to truncate output at schema validation, preventing accumulation of long justifications across 18 levers. Currently the only model-agnostic guard is the advisory text, which weak models ignore.
- **Effort**: Very low — single-line change: `justification: str = Field(description="...", max_length=200)` in `deduplicate_levers.py:83`.
- **Risk**: Very low. max_length truncates at validation; if a model produces a justification longer than 200 chars, the Pydantic validator rejects it and triggers a retry. The retry produces a shorter attempt. Edge case: if the model consistently exceeds max_length and exhausts retries, the lever falls to secondary fallback — same behavior as a total LLM failure today. This is acceptable.

### 3. Fix B1: Emit a deduplication_fallback event when total LLM failure silently produces all-secondary output
- **Type**: code fix
- **Evidence**: Code review B1. `deduplicate_levers.py:196-205` catches any LLM exception and leaves `batch_result = None`. All levers then default to `"secondary"` with fallback text. `runner.py:151-155` returns `status="ok"` and `calls_succeeded=1` unconditionally. The analysis pipeline cannot distinguish a run that failed entirely from one that succeeded without inspecting every output file's justification text.
- **Impact**: Improves observability for all models and plans. Makes silent failures detectable in `events.jsonl` without parsing output files. Would have caught the PR #374 all-primary fallback cases automatically. Affects correctness of success rate metrics used in this very analysis pipeline.
- **Effort**: Low. Fix has two parts: (1) in `deduplicate_levers.py`, detect `batch_result is None` and emit a warning-level log or set a flag; (2) in `runner.py:_run_deduplicate`, either emit a `deduplication_fallback` event or return `status="error"` when the fallback was triggered. The minimum fix is a `deduplication_fallback` event emission.
- **Risk**: Low. Changing `status="ok"` to `status="error"` for total failures would cause the analysis pipeline to count them correctly but could break callers that assume deduplicate always returns ok. Emitting an event while keeping `status="ok"` is the safer first step.

### 4. Update OPTIMIZE_INSTRUCTIONS to match the new overlap-preference rule
- **Type**: code fix (documentation)
- **Evidence**: Code review S3/I4. `deduplicate_levers.py:55-58` still says: "The more general lever should survive; the specific one should be removed." PR #375 changed the system prompt to: "keep the one that better captures the strategic decision." These are different criteria. The next person who runs a self-improvement iteration on the deduplicate step will read the OPTIMIZE_INSTRUCTIONS, apply the "keep general" heuristic, and produce a prompt that contradicts the current system prompt. This will also appear as a confusing regression in synthesis reports.
- **Impact**: Prevents documentation-driven regression in future optimization iterations. Low direct quality impact on current runs.
- **Effort**: Trivial — edit two sentences in `deduplicate_levers.py:55-58`.
- **Risk**: None.

### 5. Fix B2: Store the full constructed prompt (not just project_context) in the user_prompt field
- **Type**: code fix
- **Evidence**: Code review B2. `deduplicate_levers.py:271-272`: `user_prompt=project_context` — stores only the first ~third of the actual prompt sent to the LLM. The levers JSON and "Classify every lever..." instruction are omitted. Anyone inspecting the raw output file (including the analysis pipeline's insight agents) sees an incomplete picture of what was sent to the model.
- **Impact**: Improves debuggability and replay fidelity. Would allow the insight agent to read the full prompt from the raw output file without accessing the input lever file separately. Medium practical value for the analysis pipeline.
- **Effort**: Trivial — one-line change: `user_prompt=project_context` → `user_prompt=user_prompt` at `deduplicate_levers.py:272`.
- **Risk**: None functionally. The stored `user_prompt` field will be larger (includes levers JSON). File size increases slightly but not meaningfully.

---

## Recommendation

**Pursue Direction 1 first: fix the system prompt instruction ordering to surface expected-removal guidance before the conservative tie-breaker.**

**Why this first:** The most visible remaining quality deficit after PR #375 is that llama3.1 produces 0 removes on the silo plan even when it completes within the timeout (run 71: 18 levers in, 8 primary + 10 secondary + 0 removes out). Levers `ee0996f6` and `19e66d20` obviously overlap primary levers — capable models agree they should be removed — but llama3.1 keeps them. Downstream steps (EnrichLevers, FocusOnVitalFewLevers, ScenarioGeneration) receive a noisier lever set as a result. Since the pipeline's purpose is to produce realistic, actionable plans, having 18 undeduplicated levers flow to enrichment is a content-quality regression that affects every llama3.1 plan on every future run.

**What to change in `deduplicate_levers.py:133-143`:**

Current rules block (in DEDUPLICATE_SYSTEM_PROMPT):
```
- When uncertain between primary and secondary, prefer primary — a false
  positive is recoverable downstream.
- When uncertain between removing and keeping, prefer secondary over remove
  to avoid discarding a potentially important lever.
- Expect to remove 25-50% of the input levers. If you classify everything as
  primary or secondary, reconsider — the input almost always contains
  near-duplicates and overlap.
```

Proposed replacement:
```
- When uncertain between primary and secondary, prefer primary — a false
  positive is recoverable downstream.
- Expect to remove 25-50% of the input levers. The input almost always
  contains near-duplicates and overlap. If you are classifying everything
  as primary or secondary, you are likely missing redundancies — go back
  and compare the levers more carefully before finalizing.
- When genuinely uncertain between removing and keeping a specific lever
  after comparing it against others, prefer secondary over remove.
```

**Why this ordering:** Moving the expected-removal rate above the conservative tie-breaker makes the removal expectation the primary framing, with the tie-breaker as a narrow exception for genuine borderline cases. The added instruction to "go back and compare" is a chain-of-thought nudge that may help llama3.1 catch redundancies it initially overlooks. The conservative fallback remains — it is narrowed to "after comparing" rather than being the default disposition.

**Also do Direction 2 in the same PR** (add `max_length=200` to the justification field): it is a trivial one-line change that makes the timeout fix robust for all future plans, regardless of content complexity. Its low effort and zero risk mean deferring it gains nothing.

---

## Deferred Items

**B1 (silent failure → status=ok):** High importance for metrics reliability but not a content-quality issue for successful runs. Do in the PR after next, or whenever a silent failure causes a confusing analysis result.

**B2 (full prompt not stored):** Trivial fix; can be bundled with any nearby change. No urgency.

**S3/I4 (OPTIMIZE_INSTRUCTIONS update):** Should be bundled with Direction 1 since both touch `deduplicate_levers.py`. Replace lines 55-58 with: "Hierarchy-direction errors. Models remove the general lever and keep the narrow one. PR #375 changed the preference from 'keep the more general lever' to 'keep the one that better captures the strategic decision' — either the general or the specific lever may be correct depending on which one a project manager would actually act on."

**S4 (min-survival warning threshold too permissive):** `max(3, len(input_levers) // 4)` fires at 78% removal for 18 levers. Changing to `len(input_levers) // 3` would fire at 67% removal — still permissive, but would catch a model that removes 14/18 levers. Low priority since over-removal is theoretically bounded by the "prefer secondary" rule and no over-removal has been observed.

**S5 (case-sensitive duplicate name detection in identify_potential_levers):** Affects upstream step, not this step. Minor; defer.

**S6 (partial_recovery false positives in runner.py):** Events noise issue. Fix when the events pipeline is being cleaned up.

**H2/I5 (synthetic test plan for "irrelevant" lever criterion):** The PR's new irrelevant-lever removal cannot be validated against the current 5 plans. Adding one synthetic plan with a known-irrelevant upstream lever (e.g., a software-delivery plan with a "physical office location" lever generated upstream) would allow direct validation in the next iteration.

**N3/H3 (qwen3 justification swap for multiple remove-classified levers):** qwen3 correctly classifies both levers as remove but swaps their justification text. The outcome is correct; the reasoning is garbled. Consider adding a name-based cross-reference check (I3) or restructuring the prompt to name the target lever explicitly in the justification template. Low urgency since classification outcome is correct.
