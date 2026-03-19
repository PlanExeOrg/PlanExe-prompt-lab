# Synthesis

## Cross-Agent Agreement

Both `insight_claude` and `code_claude` agree on the following:

1. **Template lock is the top content-quality issue.** All three `review_lever` examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 224–226) use "options" or "every option" as their grammatical subject. Weaker models copy this structure, producing ~89% options-centric reviews for llama3.1 — worsened from 62.5% before the PR, despite the PR not touching the examples. The root cause is in the examples themselves (S1 / H1).

2. **`partial_recovery` event has no failure reason.** The adaptive loop correctly catches mid-loop exceptions and continues with prior levers, but the exception class and message are discarded before the event is written. This makes haiku's 3rd-call failures on silo/parasomnia undiagnosable from events.jsonl alone (B3 / C2 / Q1).

3. **No word-count validator on `options` lets short labels through.** The `check_option_count` validator only enforces `len(v) >= 3`. llama3.1 calls 2–3 produce options as short as 5 words ("Prioritize gentrification-driven revitalization"). These pass Pydantic, ship downstream, and accumulate in output JSON (B4 / C3 / N5 / E4).

4. **gpt-oss-20b JSON truncation persists.** EOF at mid-JSON for run 46 (hong_kong_game) mirrors the run 04 failure (sovereign_identity). The PR fixed haiku's cap but left gpt-oss-20b producing the same error pattern (N2 / S4).

5. **The PR's core implementations are sound.** Adaptive loop termination logic, exception handling (first call re-raises; subsequent calls continue), review_lever minimum relaxation, and lever_classification removal are all correct and net-positive.

---

## Cross-Agent Disagreements

**Proposed fix for gpt-oss-20b truncation (C1 vs. S4):**

- `insight_claude` recommends applying the same `max_tokens` fix to gpt-oss-20b as was applied to haiku (insight C1): confirm the API output cap and cap the config value.
- `code_claude` (S4) points out that `baseline.json:34` already sets `max_tokens: 8192` for `openrouter-openai-gpt-oss-20b`. If that value was active during run 46 and truncation still occurred, then the haiku-style fix is already in place and insufficient for a reasoning model, because reasoning tokens consume part of the `max_tokens` budget before output tokens are emitted.

**Code review is more accurate here.** I verified `baseline.json` directly: `max_tokens: 8192` is already present for `openrouter-openai-gpt-oss-20b`. Yet run 46 still truncated. The insight's C1 recommendation is moot — the same fix is already applied. A different approach is needed (e.g., prompt compression, structured output format hints, or accepting 4/5 success rate until the provider offers a solution).

**Fabricated % fix attribution:**

- `insight_claude` notes that fabricated % claims disappeared from llama3.1 gta_game (run 03 → run 45) and raises Q4: what caused the fix if the system prompt didn't change?
- `code_claude` does not attribute this. Most likely explanation: lever_classification removal changed the schema the model was producing, reducing constraint saturation that correlated with hallucinated statistics. Could also be run-to-run non-determinism. Not dispositive either way.

---

## Top 5 Directions

### 1. Replace all three `review_lever` examples with non-options-centric critiques
- **Type**: prompt change
- **Evidence**: S1 (code_claude), H1 (insight_claude). All three examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` lines 224–226 culminate in a phrase whose grammatical subject is "the options" or "every option." This directly contradicts `OPTIMIZE_INSTRUCTIONS` lines 69–79, which warn that examples must "avoid reusable transitional phrases that fit any domain." The template lock worsened from 62.5% → 89% for llama3.1 gta_game reviews (insight comparison table, row "Template lock").
- **Impact**: Affects ALL llama3.1 plans and any weaker model that copies sentence structure from examples. Reviews currently read like boilerplate ("none of the options address this risk"). Replacing examples with domain-specific critiques that name a concrete project tension — without referencing "the options" at all — would break the structural anchor weaker models copy. `OPTIMIZE_INSTRUCTIONS` lines 69–79 document the exact problem and already provide the correct exemplar ("the idle-wage burden during the 5-month off-season" critique names a domain-specific implication). The existing agriculture example should be kept; the light-rail and catastrophe-risk examples should be rewritten.
- **Effort**: Low — two example rewrites in the system prompt string.
- **Risk**: Weaker models may shift lock to whatever new phrase is reused across the replacement examples. Examples must be structurally different from each other, not just from current examples. Verify that neither new example contains a reusable transition phrase.

### 2. Fix B1: Step-gate the `partial_recovery` event check in `runner.py`
- **Type**: code fix
- **Evidence**: B1 (code_claude). `runner.py:514` checks `pr.calls_succeeded is not None and pr.calls_succeeded < 3`. `_run_documents` returns `PlanResult(calls_succeeded=1)` unconditionally (line 155). Since `1 < 3` is always True, every `identify_documents` run emits a spurious `partial_recovery` event. The `step` parameter is in scope at `_run_plan_task` (line 463), making the fix a one-line addition.
- **Impact**: Corrects events.jsonl integrity for all pipeline steps that use this runner. Analysis pipelines that count `partial_recovery` events to assess retry behavior will stop over-counting. This is a silent data corruption: every `identify_documents` benchmark run currently produces misleading partial_recovery entries.
- **Effort**: Very low — add `and step == "identify_potential_levers"` to the condition at line 514.
- **Risk**: None. The condition becomes more specific; no currently-expected partial_recovery events are suppressed because `_run_documents` never has a partial recovery scenario.

### 3. Add minimum word-count validator to `Lever.options`
- **Type**: code fix
- **Evidence**: B4 (code_claude), C3 / N5 / E4 (insight_claude). The system prompt section 6 requires "at least 15 words with an action verb" per option but no Pydantic validator enforces this. Options as short as 5 words pass validation and ship downstream. The `check_option_count` validator at lines 124–136 only checks item count ≥ 3.
- **Impact**: Directly prevents label-style options (5–10 words) from reaching downstream tasks (DeduplicateLevers, EnrichLevers, ScenarioGeneration). Forces the model to retry if any option is under-length. Uses `len(opt.split()) < 12` — language-agnostic, avoids the English-only validation problem documented in `OPTIMIZE_INSTRUCTIONS`. A threshold of 12 (not 15) provides a conservative buffer below the prompt's stated requirement, catching clear violations without over-rejecting borderline options.
- **Effort**: Low — one new `@field_validator('options', mode='after')` method.
- **Risk**: Increases retry count for llama3.1 on calls 2–3. With the adaptive loop (max_calls=5), this is tolerable — rejecting and retrying a batch with short options is preferable to shipping them downstream. Risk of over-rejection is low at threshold 12.

### 4. Add `last_error` field to `PlanResult` and surface it in `partial_recovery` event
- **Type**: code fix
- **Evidence**: B3 (code_claude), C2 (insight_claude), Q1 (insight_claude). The adaptive loop at `identify_potential_levers.py:306–320` catches exceptions and logs them but does not thread the exception detail back to the caller. The `partial_recovery` event only records `calls_succeeded` and `expected_calls`. The failure mode (API cap, Pydantic validation error, network timeout) is unobservable from events.jsonl.
- **Impact**: Enables diagnosis of haiku's 3rd-call failures on silo/parasomnia (run 51). Without this, the question "is 8192 max_tokens too tight for haiku on complex plans?" cannot be answered from benchmark data. Also surfaces Pydantic rejection causes, helping distinguish template-lock rejections from truncation from timeouts.
- **Effort**: Low-medium — add `last_error: str | None = None` to `PlanResult`; capture last exception in the loop; include in partial_recovery event.
- **Risk**: None for correctness. Adds one optional field to the events.jsonl schema.

### 5. Investigate and address gpt-oss-20b persistent JSON truncation
- **Type**: code fix (config or prompt change)
- **Evidence**: N2 (insight_claude), S4 (code_claude). `baseline.json:34` already has `max_tokens: 8192` for gpt-oss-20b, yet run 46 still truncated at line 47 of the JSON output. For a reasoning model, internal chain-of-thought consumes tokens from the same `max_tokens` budget before producing output, so the effective output window may be far less than 8192.
- **Impact**: Recovers 1 persistent failure per 5-plan batch for gpt-oss-20b. Recovering this would bring overall success rate from 94.3% back toward 97.1%.
- **Effort**: Medium — requires confirming with provider docs what gpt-oss-20b's output token cap is after reasoning, then choosing between a higher `max_tokens`, a shorter prompt, or a fallback model.
- **Risk**: If `max_tokens` is increased beyond what the provider allows for this model tier, the request will fail with a different error. Investigation needed before applying a fix.

---

## Recommendation

**Replace all three `review_lever` examples with non-options-centric critiques (Direction 1).**

**Why first:** Template lock is the only issue that degrades the content quality of ALL successful plans for an entire model tier. The 89% options-centric review rate for llama3.1 means that nearly every review field in llama3.1 output reads as "none of the options address [X]" — a sentence structure that is domain-independent, adds no analytical value, and violates `OPTIMIZE_INSTRUCTIONS` lines 69–79. This affects ~26% of models in the benchmark set (llama3.1 is 1/7 models) across all 5 plans. The other top directions fix correctness bugs (B1), prevent future regressions (B4), or enable diagnostics (B3) — none of them improve the actual content of plans that currently succeed.

**What to change — file and location:**

`PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 224–226 inside `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`, section "4. Validation Protocols":

```python
# Current (options-centric subjects in all three):
- "Switching from seasonal contract labor to year-round employees stabilizes harvest quality,
   but none of the options price in the idle-wage burden during the 5-month off-season."
- "Routing the light-rail extension through the historic district unlocks ridership but triggers
   Section 106 heritage review; the options assume permits will clear on the standard timeline."
- "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a
   regional hurricane season can correlate all three simultaneously — correlation risk absent
   from every option."
```

**Proposed replacement** (agriculture example kept; light-rail and catastrophe examples rewritten to remove "the options" as subject):

```python
- "Switching from seasonal contract labor to year-round employees stabilizes harvest quality,
   but the idle-wage burden during the 5-month off-season adds a fixed cost that erases the
   per-unit savings unless utilization reaches year-round levels."
- "Section 106 heritage review for the historic-district alignment triggers a mandatory
   45–180-day public comment period that falls entirely outside the project schedule —
   any opening date committed before permits clear is betting on the minimum review
   timeline, not the median."
- "Pooling catastrophe risk across three coastal regions reduces expected annual loss on paper,
   but a single regional hurricane season can correlate all three simultaneously, turning
   the diversification assumption into a concentration risk at the worst possible moment."
```

Key changes: the agriculture example now names the mechanism directly ("adds a fixed cost") rather than indicting the options. The light-rail example names a concrete timeline constraint rather than saying "the options assume." The catastrophe example names a systemic exposure rather than pointing at what "every option" omits. All three critiques are non-portable — a weaker model cannot reuse the sentence structure across different domains.

---

## Deferred Items

**D1 — Fix B1 (step-gate partial_recovery check).** One-line fix at `runner.py:514`: add `and step == "identify_potential_levers"`. Low effort, should be done in the next PR.

**D2 — Add word-count validator to `Lever.options`.** `@field_validator('options', mode='after')` checking `len(opt.split()) < 12`. Should accompany the next schema change PR to avoid a standalone micro-PR.

**D3 — Add `last_error` to `PlanResult` and surface in `partial_recovery` event.** Required before haiku max_tokens can be tuned further. Block haiku tuning until this diagnostic is in place.

**D4 — Investigate gpt-oss-20b truncation.** Confirm with provider whether gpt-oss-20b's output-token budget after reasoning is less than 8192. If so, either increase `max_tokens`, shorten prompts, or accept the current 4/5 success rate for this model. Do not apply another `max_tokens` reduction (that strategy is already exhausted at 8192).

**D5 — Add style-diversity instruction to continuation prompt (H2/I4).** The second-call prompt at `identify_potential_levers.py:273–278` only asks for new lever names. Adding "Vary your critique format and option detail level compared to earlier batches." may reduce the quality drop in calls 2–3 for llama3.1. Lower priority than example replacement because it addresses a symptom (call 2–3 quality drop) rather than the root cause (examples that permit lock-in).

**D6 — Document inner-retry amplification in `OPTIMIZE_INSTRUCTIONS`.** gpt-5-nano produced 8 total API calls for 3 `calls_succeeded` in run 47 (insight E, "inner × outer retry amplification"). This is untracked. Add a note to `OPTIMIZE_INSTRUCTIONS` flagging when `activity_overview.json` shows `calls > calls_succeeded × max_calls_per_batch × 1.5` as a monitoring threshold.

**D7 — Verify B2 (false-positive partial_recovery on legitimate early-stop).** With `min_levers=15` and models producing ~7 levers/call, 3 calls are typically needed. But if any model consistently produces 8+ levers/call, 2-call runs will emit spurious partial_recovery events. Add a comment to `runner.py:115–117` documenting this assumption and the threshold at which it breaks.
