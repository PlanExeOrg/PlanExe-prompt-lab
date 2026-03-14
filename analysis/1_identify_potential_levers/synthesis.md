# Synthesis

## Cross-Agent Agreement

All four analysis files agree on the following:

1. **Template leakage** — The literal string `"Systemic: 25% faster scaling through..."` in the production system prompt (`identify_potential_levers.py:95`) causes most models to copy or paraphrase it. Both insight files document this; both code reviews confirm the string is baked into the constant.

2. **No cardinality enforcement** — `DocumentDetails.levers` and `Lever.options` are unvalidated `list[...]` fields. The description says "exactly 5" but there is no `max_length` constraint. Both code reviews flag this as the direct cause of run 16's inflated lever count.

3. **"more" prompts have no deduplication pressure** — The three sequential calls use bare `"more"` as follow-up text (`identify_potential_levers.py:155-159`), giving models no instruction to avoid lever names from prior calls. All agents flag this as the root cause of cross-batch duplicates.

4. **Race condition on `set_usage_metrics_path`** — `runner.py:106` calls `set_usage_metrics_path` before the `with _file_lock:` block at line 108. Both code reviews identify this as a confirmed data-corruption bug under `workers > 1`.

5. **Assistant turn passed as `dict` not `str`** — `identify_potential_levers.py:196` passes `result["chat_response"].raw.model_dump()` (a Python dict) as `ChatMessage.content`. Both code reviews flag this as a latent correctness issue that degrades multi-turn context fidelity.

---

## Cross-Agent Disagreements

### Disagreement 1: Cause of run 16's 20-lever output

**insight_claude** hypothesized that `workers=1` triggers an extra LLM call batch (4 calls × 5 levers = 20).

**code_codex** refutes this by reading the raw artifact: `history/0/16_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows three responses with lever counts `[5, 5, 10]`, not four batches. The code always makes exactly three turns (`identify_potential_levers.py:155-159`); worker count only affects plan-level parallelism in the ThreadPoolExecutor (`runner.py:375-389`).

**Verdict: code_codex is correct.** The cause is llama3.1 over-generating 10 levers in one structured call, which the schema silently accepts. Worker count is irrelevant to batch count.

### Disagreement 2: `review_lever` vs `review` as cause of run 13 failure

**insight_claude** identified the field name mismatch (`review_lever` in prompt vs `review` in schema) as the cause of the run 13 parasomnia JSON extraction failure.

**code_claude (S1) and code_codex** both refute this. The `Lever` Pydantic class at `identify_potential_levers.py:36` uses `review_lever`, matching the prompt at line 109. The `review` name is in `LeverCleaned` (line 81), the cleaned export layer — an intentional two-layer design documented in the class docstring at line 64. The run 13 failure was caused by the model wrapping its entire output in a `strategic_rationale` outer key (visible in the error trace in `history/0/13_identify_potential_levers/outputs.jsonl`), which is a structured-output recovery failure, not a field-name mismatch.

**Verdict: code_claude/code_codex are correct.** The `review_lever` naming is intentional. The run 13 failure is a brittle parse-recovery issue (all-or-nothing `raise` at `identify_potential_levers.py:191`).

### Disagreement 3: Quality ranking

**insight_claude** ranks run 12 (claude-haiku) #1 for contextual depth and zero template leakage.
**insight_codex** ranks run 13 (gpt-oss-20b) #1 for prompt-shape adherence (lowest constraint violations: 0.2 average) and run 12 last among compliant runs due to verbosity and 0/15 summary format score.

**Verdict: both are right in different frames.** For *content quality and downstream usability* (option depth, project specificity), run 12 wins. For *formal schema compliance* (exact marker syntax, review format, summary format), run 13 wins when it succeeds. Run 12's high `avg constraint violations` (13.4) reflects missing `%` metrics (37 violations) and missing arrows (30) — real format gaps even though the content is richer.

---

## Top 5 Directions

### 1. Enforce `max_length=5` on `DocumentDetails.levers` and `max_length=3` (or `max_length=5`) on `Lever.options`
- **Type**: code fix
- **Evidence**: Both code reviews (code_claude B2/I2, code_codex B2/I1); confirmed in `identify_potential_levers.py:33-35,57-59`. Directly caused run 16's 20-lever output and accepts >3 options silently across all runs.
- **Impact**: All models. Converts silent over-generation into explicit validation errors at parse time. Stops inflated lever counts from reaching `002-10-potential_levers.json`. Also catches wrong-option-count violations currently logged as `ok` runs.
- **Effort**: Low — 2 field declarations changed.
- **Risk**: A model that reliably returns 6 levers will now fail that call instead of silently inflating output. This surfaces a latent failure more visibly. Could increase error rates for llama3.1 and similar weak models until prompts are also improved.

### 2. Replace the literal "25% faster scaling through" example with a format placeholder
- **Type**: prompt change (also in hardcoded constant)
- **Evidence**: insight_claude §1, H1; code_claude I1; code_codex B1. Confirmed at `identify_potential_levers.py:95`. Affects 5/6 runs (all except haiku). Run 10 has 4 literal copies in the silo output alone.
- **Impact**: All models using the external prompt (`prompts/identify_potential_levers/prompt_0_fa5dfb88...txt`) AND the internal constant. Reduces verbatim copy rate, forces model-invented metrics, improves consequence diversity.
- **Effort**: Low — change one line in the system prompt constant and/or the external prompt file.
- **Risk**: Negligible. The placeholder `[N]% [measurable outcome] through [mechanism]` is semantically equivalent but non-copyable. No functional change to the pipeline.

### 3. Fix race condition: move `set_usage_metrics_path` inside the lock
- **Type**: code fix
- **Evidence**: code_claude B1/I4; confirmed at `runner.py:106-109`. When `workers > 1`, Thread A and Thread B can interleave their `set_usage_metrics_path` calls, causing all token usage to be written to the last plan's file.
- **Impact**: All multi-threaded runs (workers=4 for most models). Usage metrics are currently silently corrupted — one plan gets double-counts, others get none. Affects any downstream analysis of token spend per plan.
- **Effort**: Low — move two lines inside the existing `with _file_lock:` block. The `finally` cleanup at line 140 should mirror the fix.
- **Risk**: None. The lock already exists; this is a pure ordering fix.

### 4. Replace bare `"more"` follow-up prompts with prior-lever-name injection
- **Type**: code change + prompt change
- **Evidence**: insight_claude §5-6, H4; code_claude I5; code_codex I3; confirmed at `identify_potential_levers.py:155-159`. All runs show semantic redundancy across batches; run 16 has exact-name duplicates.
- **Impact**: All models. Reduces exact-name and near-name duplicates, lowering the deduplication burden in the downstream `deduplicate_levers.py` step. Improves diversity of the 15-lever pool.
- **Effort**: Medium — requires building a dynamic message like `"Generate 5 more levers. Do not reuse any of these names: {', '.join(prior_names)}"` using lever names collected from prior responses.
- **Risk**: Slightly longer prompt tokens per call. Weak models may still drift semantically even when prevented from reusing exact names.

### 5. Fix assistant turn serialization: `model_dump()` → `json.dumps(model_dump())`
- **Type**: code fix
- **Evidence**: code_claude B3/I3; code_codex suspect pattern; confirmed at `identify_potential_levers.py:196`. The dict passed as `ChatMessage.content` is serialized inconsistently by different LLM backends — some use Python `repr()` with single-quoted keys, making the prior context unreadable to the model.
- **Impact**: All models, second and third "more" calls. Gives models properly formatted JSON context of prior responses, strengthening their ability to avoid repeating lever concepts. Likely contributing to run 13's parasomnia failure (malformed context may have caused the model to re-emit the entire `DocumentDetails` structure instead of a bare response).
- **Effort**: Low — change one expression on line 196.
- **Risk**: Low. All well-formed LLM backends accept `str` content; the current `dict` path is backend-dependent.

---

## Recommendation

**Do direction 2 first: remove the "25% faster scaling through" literal from the system prompt.**

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, line 95
**Also update:** `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt` (same string, same line context)

**Current:**
```
     • Include measurable outcomes: "Systemic: 25% faster scaling through..."
```

**Replace with:**
```
     • Include measurable outcomes: "Systemic: [N]% [measurable outcome] through [mechanism]"
```

**Rationale for doing this first:**

- It requires changing exactly one line in one place (plus the mirrored external prompt file). No functional risk, no schema changes, no failure modes introduced.
- It affects output quality across 5 of 6 tested models. Every model except claude-haiku copies or paraphrases this string, flattening consequence diversity across *all* plans and *all* levers — this is the most widespread quality defect found.
- Unlike direction 1 (Pydantic constraints), this change immediately improves output for models that are already succeeding (runs 10, 14, 15) rather than surfacing new failures.
- Unlike direction 3 (race condition), this affects output quality that users and evaluators see directly, not just internal metrics bookkeeping.
- Unlike directions 4 and 5, the change is a single-token substitution with zero moving parts.

After this prompt fix is applied and re-evaluated, direction 1 (Pydantic `max_length=5` on levers) should be the next change — it hardens the pipeline against silent over-generation from any model and converts the run 16 behavior from a silent data quality issue into a visible, diagnosable validation error.

---

## Deferred Items

- **Direction 3 (race condition in runner.py)**: Fix before the next batch of multi-threaded runs. The bug is confirmed and the fix is trivial, but it affects internal metrics rather than output quality, so it is not blocking prompt iteration work.

- **Direction 4 (prior-lever-name injection)**: Worth implementing after the prompt and schema fixes are validated. The semantic redundancy it addresses is real but partially mitigated by the downstream `deduplicate_levers.py` step.

- **Direction 5 (assistant turn serialization)**: Fix this alongside direction 4, since both affect multi-turn context fidelity and the fix is a one-line change.

- **code_claude I6 / code_codex I4 (partial-result save on failure)**: Implement when run 13-style failures (single-call failure aborting an entire plan) recur in testing. Low priority while failure rate is 1/30 plans.

- **code_codex I5 (resolve worker count from selected profile)**: The `_resolve_workers` merge-all-configs approach is architecturally fragile but has not caused incorrect behavior in observed runs. Defer until profile-selection logic is centralized.

- **insight_codex question: add downstream reduction steps to runner**: If the evaluation target shifts from the 15-lever intermediate artifact to the final "vital few" output, the runner should optionally chain into `deduplicate_levers.py`. Not needed while the prompt-lab is specifically optimizing the `identify_potential_levers` step in isolation.

- **Run 12 (claude-haiku) verbosity**: The haiku model produces the highest-quality content but has 13.4 average constraint violations, mostly missing `%` metrics (37) and missing arrows in consequence chains (30). A targeted prompt addition that makes the `Immediate → Systemic → Strategic` arrow syntax and the `%` metric requirement more salient could bring haiku closer to full compliance without sacrificing content depth. Defer until the leakage fix is applied and re-evaluated.
