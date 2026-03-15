# Synthesis

## Cross-Agent Agreement

All four analysis artifacts agree on the following points:

1. **Run 39 (nemotron-3-nano) is a complete and persistent failure.** Zero parseable outputs in 4 consecutive batch-runs (runs 24, 25, 32, 39). All four files call for skipping or warning on this model.

2. **Run 42 (gpt-5-nano) is the best overall quality.** Ranked #1 by both insight agents, strongest prompt-compliance evidence, 0 null summaries, 75/75 unique lever names.

3. **`strategic_rationale` is null in 100% of responses across all runs.** Both code review agents identify the same root cause: the field is `Optional[str]` with `default=None`, and the system prompt never instructs models to fill it. No model fills a field that the schema marks optional and the prompt doesn't ask for.

4. **The `consequences` field has a length target (`150–300 words`) that is grossly miscalibrated versus baseline (~56 words).** Both code review agents flag this as the direct code-side cause of run 45 (haiku) timing out on parasomnia at 432s.

5. **The `review_lever` field description is weaker than the system prompt.** The field says "identify one specific weakness" without requiring the `Weakness:` prefix. The system prompt requires both `Controls [A] vs [B]` AND `Weakness: ...` in every review. Both code review agents independently trace run 40's 15/15 alternating-only reviews to this schema/prompt mismatch.

6. **Post-parse validation is absent.** A response that returns 4 levers, 2 options, or null required fields is silently accepted as a success. Both code reviewers flag this as the primary mechanism allowing bad output to reach the artifacts.

7. **B5 (telemetry race condition in runner.py).** Both code reviews confirm that `set_usage_metrics_path` is called outside `_file_lock` (line 106), and that per-plan `activity_overview.json` can count events from other plans under parallel execution. The "10 LLM calls where 9 were expected" anomaly noted in insight_claude is a direct consequence.

---

## Cross-Agent Disagreements

### Disagreement 1: Is `summary` universally null?

**insight_claude** says the `summary` field is null in 100% of responses across all 7 runs.
**insight_codex** reports run 42 has 0 null summaries and run 43 also has 0.

**Resolution (source code verified):** The `summary` field in `DocumentDetails` (line 68) is `Optional[str]` with `default=None`. Making a field optional does not prevent a capable model from filling it. `gpt-5-nano` (run 42) and `qwen3-30b` (run 43) do populate it despite the Optional declaration, while `llama3.1` (run 40) and weaker models do not. `insight_claude`'s "universally null" claim appears to have over-extrapolated from run 40 behavior. `insight_codex`'s per-run breakdown is more accurate. **`strategic_rationale`, not `summary`, is the field that is universally null** — the system prompt never mentions it at all (confirmed: it does not appear in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`).

### Disagreement 2: Root cause of run 43 (qwen3) review-in-consequences contamination

**code_claude (S1)** attributes this partly to the `model_dump_json()` fallback in the assistant message (line 219–222), which inserts a full JSON blob into the chat history and may train subsequent calls to blend fields.
**code_codex (S2)** frames it more broadly as accumulated chat history conditioning: calls 2 and 3 condition on the model's prior output, amplifying formatting mistakes.

**Resolution:** Both are partially right. The multi-call conversation design (lines 176–223) does accumulate prior output into context, and the `model_dump_json()` fallback does produce an uncontrolled JSON blob as the assistant turn when `message.content` is empty. Neither factor alone is a confirmed cause; the codex framing is broader and more accurate. The field description mismatch (no explicit prohibition against review text in consequences) is likely the primary cause, with S1/S2 acting as amplifiers.

### Disagreement 3: Run 44 (gpt-4o-mini) rank

**insight_claude** ranks run 44 Tier C (below qwen3 Tier B) due to shallow consequence depth.
**insight_codex** ranks run 44 #2 overall (behind run 42) due to operational speed advantage.

**Resolution:** This is a genuine trade-off between compliance and throughput, not a factual error. Run 44 is the fastest at 43.5s/plan and fully reliable, but has 75/75 consequences missing explicit trade-off language (confirmed by codex constraint table). Both rankings are defensible under different objectives.

### Disagreement 4: Does the runner lack production retry config?

**code_codex (B4)** flags that `runner.py:94` creates `LLMExecutor(llm_models=llm_models)` with no `RetryConfig`, while the real pipeline uses `RetryConfig()`. This makes prompt-lab experiments harsher than production.
**code_claude** does not flag this as a separate bug.

**Resolution (source code verified):** Line 94 of `runner.py` confirms: `llm_executor = LLMExecutor(llm_models=llm_models)` — no `RetryConfig` argument. **code_codex is correct.** This means the runner has `max_retries=0`, so transient timeout/empty-response failures that production would retry are counted as failures in the prompt-lab data. This is a real experiment-skew bug.

---

## Top 5 Directions

### 1. Fix `consequences` field description: add trade-off requirement and correct length target
- **Type**: schema change (also fixes a prompt/schema mismatch)
- **Evidence**: code_codex B3 + code_claude S3 (length miscalibration); code_codex S1 + code_claude (trade-off language missing in consequences). Supported by both insight agents. Run 44 missing trade-offs in 75/75 consequences; run 40 in 75/75; run 41 in 60/75; run 43 in 30/75 — total 240/450 (53%) of all levers across successful runs lack explicit trade-off language in consequences. Haiku (run 45) times out on parasomnia at 432s, directly traceable to the 150-300 word minimum (~750–1500 chars per consequence vs. baseline ~280 chars).
- **Impact**: Reducing the target from "150–300 words" to "3–5 sentences" will prevent haiku timeout on parasomnia. Adding an explicit trade-off requirement and a prohibition against review text in consequences will fix the 53% missing-trade-off rate and the qwen3 contamination. Affects all runs and all models.
- **Effort**: low — 3-line change to the `consequences` field description in `identify_potential_levers.py:30–37`
- **Risk**: Setting the length target too low could reduce depth for high-quality models. Targeting 3–5 sentences preserves meaningful content while bounding verbosity. The prohibition against review text is safe since it reinforces existing field boundaries.

### 2. Align `review_lever` field description with the dual-component requirement
- **Type**: schema change
- **Evidence**: code_claude B4, code_codex S1. Run 40 (llama3.1) produces 15/15 reviews that alternate Controls-only or Weakness-only but never both — directly traced to the field description only saying "identify one specific weakness" without requiring the `Weakness:` prefix. Both insight agents document this violation.
- **Impact**: Forces all models to see the same requirement in the structured-output schema that the system prompt states. Expected to fix run 40's 15/15 review violations and prevent regression in other models. Affects all runs.
- **Effort**: low — 1-line change to `review_lever` field description in `identify_potential_levers.py:43–45`
- **Risk**: very low. Models that already produce both components (runs 41, 42, 43, 44, 45) will not be disrupted.

### 3. Remove `strategic_rationale` or add it to the system prompt; make `summary` non-optional
- **Type**: code fix + prompt change
- **Evidence**: code_claude B1+B2, code_codex B1. `strategic_rationale` is null in 100% of responses across all runs because (a) it is `Optional[str]` with `default=None` and (b) the system prompt never asks for it. `summary` has a contradictory description (general critique in field desc vs. specific "Add '...' to ..." format in system prompt).
- **Impact**: Removing `strategic_rationale` from the schema eliminates dead weight and false signal. Making `summary` non-optional (`str`, no default) forces models that comply with the schema to populate it; aligning its field description with the `"Add '[option]' to [lever]"` format removes the conflicting instruction. Affects all runs/models.
- **Effort**: low — remove 6 lines for `strategic_rationale`; change 2 lines for `summary` (type + description)
- **Risk**: medium — making `summary` required will cause Pydantic parsing to fail for models that currently omit it (llama3.1 run 40, gpt-4o-mini partially). Those failures would trigger LLMExecutor retries, which is the correct behavior but could increase latency for weaker models.

### 4. Add `field_validator` enforcing exactly 5 levers per call and exactly 3 options per lever
- **Type**: code fix
- **Evidence**: code_claude B3+I1+I6, code_codex B2+I2. Prior batches (runs 33, 35, 37, 38) show non-deterministic 16-lever gta_game outputs. Run 40 sovereign_identity produced one lever with only 2 options. No validator currently prevents these.
- **Impact**: Deterministically prevents 16-lever merged output (currently requires lucky model behavior). Allows LLMExecutor to retry any call that returns ≠5 levers rather than silently accepting it. Affects all models.
- **Effort**: low — 10 lines of validator code in `DocumentDetails` and `Lever`
- **Risk**: low. Increases retry frequency for models that currently return wrong counts, which correctly treats them as failures rather than successes.

### 5. Skip or warn on persistently-failing models (nemotron-3-nano-30b-a3b)
- **Type**: code fix (runner)
- **Evidence**: C8/insight_claude, I7/code_claude, I6/code_codex. Run 39 model has failed with identical `"Could not extract json string from output: ''"` error in 4 consecutive batch runs (24, 25, 32, 39). Each run wastes ~540s across 5 plan failures.
- **Impact**: Saves ~9 minutes per experiment batch. Removes noise from insight analyses. Zero impact on prompt quality.
- **Effort**: low — 5 lines in runner.py to check model names against a configurable skip list before constructing LLMExecutor
- **Risk**: very low. Model can be un-skipped if it is updated upstream.

---

## Recommendation

**Do Direction 1 first: fix the `consequences` field description in `identify_potential_levers.py`.**

This is the highest-impact single change because:

1. It is confirmed by both code review agents independently, with two distinct evidence chains (length miscalibration causing timeouts; trade-off language omission causing 53% of levers to lack explicit tension framing).
2. It affects the largest number of observed violations: 240 out of 450 levers across successful runs are missing explicit trade-off language in consequences — this is not a single-model artifact, it affects runs 40, 41, 43, and 44.
3. It has a direct causal link to the only observed timeout: haiku at 432s on parasomnia is directly caused by ~700-char consequences per lever (× 5 levers × 3 calls = 10,500 chars of consequence text per plan, pushing total tokens over the API timeout threshold).
4. It is a pure schema fix requiring zero hypothesis-testing — the root cause is confirmed in code and the fix is unambiguous.

**Specific change** — `identify_potential_levers.py`, the `consequences` field description in the `Lever` class (lines 30–37):

**Current:**
```python
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "
        "Target length: 150–300 words."
    )
)
```

**Proposed:**
```python
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "
        "The Systemic or Strategic clause MUST name an explicit trade-off between two competing forces "
        "(e.g. 'This accelerates delivery but increases defect risk'). "
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        "those belong exclusively in review_lever. "
        "Target length: 3–5 sentences (approximately 60–120 words)."
    )
)
```

This single change:
- Reduces haiku verbosity by replacing the 150–300 word target with a 3–5 sentence / 60–120 word target (in line with baseline calibration of ~56 words)
- Adds the trade-off language requirement directly to the field description that structured-output models see, fixing the 53% missing-trade-off rate
- Adds a prohibition on review text appearing in consequences, which addresses the qwen3 contamination pattern

The change also partially addresses Direction 2 (review field content boundaries) and sets up Direction 3 (schema cleanup) as a natural follow-on.

---

## Deferred Items

**Direction 2 (review_lever dual-component fix):** Should be done in the same iteration as Direction 1, or immediately after. Change `review_lever` field description from `"Critique this lever. State the core trade-off it controls (e.g., 'Controls Speed vs. Quality'). Then, identify one specific weakness..."` to `"Required format: Two sentences. Sentence 1: 'Controls [Tension A] vs. [Tension B].' Sentence 2: 'Weakness: The options fail to consider [specific factor].' Both sentences are mandatory in every response."` This directly fixes run 40's 15/15 alternating-only review violations.

**Direction 3 (remove strategic_rationale, make summary required):** Low-risk cleanup for a later iteration. Remove `strategic_rationale` from `DocumentDetails` (it is never requested by the system prompt and is null in 100% of responses). Separately evaluate whether making `summary` non-optional causes acceptable retry overhead.

**Direction 4 (lever count validator):** Low-effort defensive code change. Add `@field_validator('levers')` enforcing `len == 5` to `DocumentDetails`, and a matching validator for `options` enforcing `len == 3` to `Lever`. The 16-lever gta overflow did not appear in runs 39–45 but it is non-deterministic and will recur.

**Direction 5 (skip nemotron):** Pure operational improvement. Worth doing before the next batch run to save experiment time.

**code_codex B4 (runner retry config):** The runner uses `LLMExecutor(llm_models=llm_models)` with no `RetryConfig`, meaning `max_retries=0`. Production uses `RetryConfig()`. This inflates observed failure counts in prompt-lab experiments. Adding `retry_config=RetryConfig()` to the runner's LLMExecutor constructor would make experiment reliability data more representative of production behavior. Worth doing before drawing strong reliability conclusions from batch comparisons.

**B5 telemetry race condition:** Both code reviews confirm `set_usage_metrics_path` is called outside `_file_lock` (line 106) and that `activity_overview.json` events can bleed across concurrent plans. Fix by moving both the setup call (line 106) and the teardown call (line 140) inside `_file_lock`. This is a correctness bug but does not affect prompt quality — defer until after quality-focused changes are shipped.

**H1 (consequence chain example for llama3.1-class models):** insight_claude and insight_codex both suggest adding an illustrative example of a well-formed consequence to anchor thin models. This is a reasonable prompt hypothesis to test after the field description fix, since the field description change alone may not be sufficient for llama3.1.

**Parasomnia plan timeout pattern:** Runs 41 (gpt-oss-20b) and 45 (haiku) both fail specifically on `20260311_parasomnia_research_unit`. This plan appears to be structurally harder (likely a longer or more complex input). A plan-specific input-length check before execution, or a plan-specific `max_tokens` cap, could prevent this without altering prompt behavior for other plans.
