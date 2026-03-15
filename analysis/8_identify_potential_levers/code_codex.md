# Code Review (codex)

## Bugs Found

### B1 — The step still invites and accepts 5–7 levers, which contradicts the prompt-lab contract of exactly 5
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78-82`, `DocumentDetails.levers` is defined with `min_length=5` and `max_length=7`, so the structured schema explicitly accepts over-generation.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:201-205`, calls 2 and 3 tell the model to `Generate 5 to 7 MORE levers`, which directly conflicts with the prompt-lab prompt at `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:3-5`.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244-247`, every returned lever is flattened into the final list with no per-call count repair.
- This is a confirmed root-cause bug for the 17/19-lever artifacts: the code and schema still endorse the older 5–7 behavior even when the registered prompt says exactly 5.

### B2 — The prompt-optimizer runner disables the retry behavior the main pipeline already uses
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94`, the harness constructs `LLMExecutor(llm_models=llm_models)` with default settings only.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/plan/run_plan_pipeline.py:171-175`, the main pipeline creates `LLMExecutor(..., retry_config=RetryConfig())`, so the optimizer harness is materially less fault-tolerant than normal PlanExe execution.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/llm_util/llm_executor.py:262-283`, the executor already supports validation retries, but the optimizer never enables them.
- Result: a single malformed structured response becomes a hard plan failure in prompt optimization runs instead of a retryable near-miss. That matches the all-or-nothing extraction failures and the one-off schema failure seen in the insight files.

### B3 — Most of the output contract is prose-only, so structurally bad content passes validation and is saved unchanged
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34-58`, the strict rules for `consequences`, `options`, and `review_lever` live only in field descriptions.
- The only real validator in this file is `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60-71`, which merely parses a stringified JSON array for `options`.
- There is no executable check that `options` contains exactly 3 items, that each option is a full strategic sentence, that `review_lever` contains both `Controls ...` and `Weakness:`, or that `consequences` stays free of review text.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:251-259`, the cleaned artifact copies those raw strings straight through.
- This is a confirmed code-level explanation for “successful but low-quality” outputs such as label-only options, half-complete reviews, and `Controls` / `Weakness:` leakage surviving into `002-10-potential_levers.json`.

### B4 — Merge/save logic preserves duplicates and over-counts instead of repairing them
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:240-247`, lever names from each call are only used to build the next blacklist; there is no final uniqueness check.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260`, every flattened lever is assigned a fresh UUID and written to the cleaned list, even if the name already appeared in an earlier call.
- Because duplicate names are rewrapped as distinct `lever_id`s, downstream consumers of `002-10-potential_levers.json` see them as separate valid levers rather than obvious collisions.
- This directly explains the duplicate-name findings in the insight files and is why over-generated responses become oversized final artifacts instead of being normalized back to the intended contract.

## Suspect Patterns

### S1 — The built-in prompt still contains a strong template-leakage example
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:142-145` tells the model to name levers as strategic concepts specific to the domain and gives `"[Domain]-[Decision Type] Strategy"` as the example.
- The prompt-lab candidate prompt used in these runs contains the same wording at `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:18-20`.
- This is not a parser bug by itself, but it is a plausible leakage vector for robotic prefixes like `Silo-... Strategy`.

### S2 — Later calls are only guided by a name blacklist, not by semantic coverage
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:197-217`, calls 2 and 3 get a list of prior names plus the original plan text, but no normalized summary of what dimensions are already covered.
- That means the anti-duplication mechanism is surface-level: a model can satisfy the blacklist by renaming a lever while still repeating the same underlying idea.
- This likely contributes to cross-call near-duplicates and generic reframings, but I would want more surrounding context before calling it a definite bug.

### S3 — `summary` is mandatory for each call even though the cleaned artifact discards it
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:83-85` makes `summary` required.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:266-286` keeps summaries only in the raw artifact.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:298-300` writes only cleaned levers, not summaries.
- Requiring an extra paragraph three times per plan may be adding latency and validation surface without improving the scored `002-10` artifact.

## Improvement Opportunities

### I1 — Align the schema and follow-up prompt with the exact-5 contract
- Change `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78-82` from `5..7` to exactly 5.
- Change `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203-205` from `Generate 5 to 7 MORE levers` to `Generate 5 MORE levers`.
- Add exact-length enforcement for `options` at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:47-50` so “exactly 3” is executable, not descriptive.
- This would remove the main prompt/code contradiction that currently explains the count regressions.

### I2 — Make prompt-optimizer runs use the executor’s retry features, and wire retries into the prompt
- Update `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94` to pass at least `retry_config=RetryConfig()` and a nonzero `max_validation_retries`.
- Then update `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:217-227` so `execute_function` checks `llm_executor.validation_feedback` and appends a short corrective instruction on retry.
- Right now the retry feedback path described in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/llm_util/llm_executor.py:211-216` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/llm_util/llm_executor.py:262-283` is effectively unused by this step.
- This is the clearest code-level mitigation for partial structured responses like the `strategic_rationale`-only failure.

### I3 — Add a post-response validation/repair gate before writing cleaned levers
- Before `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260`, validate each lever for:
  - exact `Immediate → Systemic → Strategic` structure,
  - at least one measurable indicator,
  - no `Controls` or `Weakness:` in `consequences`,
  - both required sentences in `review_lever`,
  - non-label options.
- If a call fails these checks, retry that call or repair only the offending levers instead of silently saving invalid-but-parseable content.
- This would turn many current “successful but poor-quality” cases into either recoveries or explicit failures.

### I4 — Deduplicate normalized lever names at merge time
- Add a normalization pass around `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:240-260` that compares names case-insensitively and strips punctuation/spacing noise.
- On collision, either regenerate the offending call or drop the weaker duplicate before assigning final UUIDs.
- This would prevent identical names like repeated `... Information Control Strategy` from surviving as separate final levers.

### I5 — Revisit whether `summary` should be required in this step
- If `summary` is only diagnostic and not consumed by the cleaned artifact, consider making it optional at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:83-85` or moving it behind a debug-only mode.
- This should reduce token pressure and shrink the failure surface for weaker models without changing the final lever list format.

## Trace to Insight Findings

- **Insight Claude N3/N4/N5 and Insight Codex N1/N4** are best explained by **B1 + B3**. The code still allows 5–7 levers, and it has no executable checks for sentence-shaped options or full `review_lever` content.
- **Insight Claude N7 and Insight Codex duplicate-name findings** map directly to **B4**. The step merges all calls and assigns fresh UUIDs without any deduplication or collision handling.
- **Insight Claude N2** maps most directly to **B2** and **I2**. A partial structured response currently becomes a hard failure in the prompt-optimizer harness even though the executor has retry hooks designed for this class of error.
- **Insight Claude N1 / Insight Codex run-60 total extraction failure** is only partially explained here. **B2** explains why the harness does not recover, but the actual low-level JSON extraction failure appears to live below these two files.
- **Insight Claude N6 and Insight Codex generic/template leakage observations** are most consistent with **S1** and **S2**: the prompt includes a very copyable naming template, and the multi-call diversification logic only blacklists names rather than concepts.
- **Insight Codex run-64 field-boundary leak** maps directly to **B3**. There is no validator preventing review text from being saved inside `consequences`.
- **Insight Claude’s note about `num_output: 256` for llama3.1** is not explained by these two files. That looks like an LLM-config issue outside the reviewed scope.

## Summary

The strongest confirmed root cause is a code-contract mismatch: the prompt-lab experiment says each response must return exactly 5 levers, but `identify_potential_levers.py` still accepts and even requests 5–7 on later calls. The merge path then writes every returned lever straight into the cleaned artifact.

The second major issue is that the prompt-optimizer harness is less resilient than the real pipeline. It does not enable the executor’s retry features, so recoverable parse/validation near-misses become full plan failures during prompt experiments.

Finally, most quality rules here are non-enforcing prose. Because the schema only checks coarse structure, bad-but-parseable content survives untouched into `002-10-potential_levers.json`. If I were prioritizing fixes, I would do them in this order: exact-5 contract alignment, retry/repair wiring, then semantic validation and merge-time deduplication.
