# Code Review (codex)

## Bugs Found

- **B1 — The step now explicitly permits over-generation and then saves every extra lever as if it were valid output.** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:78-81`, the schema accepts `5..7` levers; in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:203-205`, both the base prompt and follow-up prompt ask for `5 to 7`; then `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244-260` blindly flattens all returned levers into the cleaned list. That guarantees `17+` final levers whenever a model emits 6 or 7 in any batch.

- **B2 — The cleaned artifact has no quality gate at all.** `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:244-260` copies raw lever fields straight into `LeverCleaned`, and `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121` writes that cleaned list directly to `002-10-potential_levers.json`. There is no rejection path for duplicate names, placeholder text, review text leaking into `consequences`, malformed `review`, or wrong per-batch counts. This turns many “bad but parseable” model outputs into silent successes.

- **B3 — Most of the claimed contract is only documentation, not validation.** The only real validator in the step is `parse_options()` at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60-71`. By contrast, the critical rules are only prose in field descriptions: consequences separation at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34-45`, exactly-3 options at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:47-50`, and review format at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:51-58`. Pydantic therefore accepts polluted `consequences`, partial `review_lever`, and short label-like options as long as the fields are strings/lists.

- **B4 — Failure runs discard the most useful debugging evidence.** In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121`, raw and clean artifacts are only saved on success. On failure, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:130-143` returns a terse error string and then deletes `track_activity.jsonl`. For parse-failure runs, that means the analysis keeps the error summary but loses the per-plan prompt snapshot, intermediate event trail, and token/activity details that would help explain why a model failed.

## Suspect Patterns

- **S1 — Fresh-context follow-ups only remember exact prior names, not prior content.** `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:195-217` resets the chat to `[system, user]` on every call and only carries forward a flat list of previously generated names. That means calls 2 and 3 cannot see prior options, prior consequences, or the earlier batch’s strategic rationale; they can only avoid exact string reuse. This is a plausible cause of thematic duplication under different names and of later calls running out of “novel” names while still repeating the same decision space.

- **S2 — Current source and evaluated prompt history are out of sync, and runner-level provenance is too weak to make that obvious.** The current source prompt says “avoid formulaic patterns or repeated prefixes” at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:143`, but the registered prompt used in the insight runs still contains the template example `"[Domain]-[Decision Type] Strategy"` at `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:19`. Meanwhile `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:347-363` stores only a SHA in `meta.json`, not a run-level prompt snapshot. That makes later code review easy to misalign with the prompt actually executed.

- **S3 — The current source always makes exactly 3 LLM calls per plan, so any history showing 4 raw batches came from another revision or wrapper.** `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:192-197` hard-codes `total_calls = 3`. If the run artifacts truly show four batches for a plan, the analysis is looking at a different commit or a different execution path than the current file.

## Improvement Opportunities

- **I1 — Re-enforce the contract in code, not prose.** Put `min_length=5` and `max_length=5` on `DocumentDetails.levers`, `min_length=3` and `max_length=3` on `Lever.options`, and add validators for `review_lever` and `consequences` so malformed-but-JSON-compliant responses fail fast instead of being saved.

- **I2 — Add a post-generation acceptance gate before flattening/saving.** Between `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:240` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:260`, validate each batch for exact lever count, duplicate names, placeholder remnants, `Controls`/`Weakness:` leakage into `consequences`, and missing `Controls ... Weakness:` structure in `review_lever`. Retry the batch instead of promoting it to `002-10-potential_levers.json`.

- **I3 — Carry forward semantic anti-duplication context, not just names.** For calls 2 and 3, pass a compact summary of already-covered tensions/themes or the previous lever names plus one-line summaries. The current exact-name-only memory is too weak to prevent near-duplicate batches.

- **I4 — Persist failure artifacts.** On exceptions in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:130-143`, write a failure-sidecar with the prompt, model metadata, last known raw response/error payload, and keep `track_activity.jsonl` instead of deleting it. That would make parse-failure analysis dramatically easier.

- **I5 — Save prompt provenance centrally per run.** In addition to the SHA at `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:347-363`, write the exact prompt text or a copied prompt file into the run directory so fully failed runs are still auditable.

- **I6 — Retain useful wrapper fields instead of discarding them.** `strategic_rationale` and `summary` are parsed into `DocumentDetails` at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:73-85`, but the cleaned output drops them entirely at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:298-300`. Preserving them would help downstream synthesis and later audit of why a batch was generated.

- **I7 — Reduce schema fragility for weaker models.** The step requires wrapper fields like `summary` even though the runner’s cleaned artifact only needs the levers. Making non-essential wrapper fields optional, or salvaging valid `levers` when only `summary` is missing/malformed, would likely improve success rates for weaker models without weakening the final cleaned contract.

## Trace to Insight Findings

- **B1 explains the count problems in both insight files.** Because the source explicitly allows `5..7` and then saves every lever, it directly accounts for the over-generated 17–19 lever outputs called out in `insight_claude.md` N4 and `insight_codex.md` N2. It also means the evaluated prompt’s “EXACTLY 5” instruction at `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:4` is not the operative contract anymore.

- **B2 explains why structurally bad outputs still appear as successful artifacts.** Since there is no acceptance gate before `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121`, duplicate names in `insight_claude.md` N3, placeholder leakage in `insight_codex.md` N4, review pollution in `insight_claude.md` N6 / `insight_codex.md` N3, and partial review fields in `insight_claude.md` N7 can all pass through unchanged.

- **B3 explains the field-boundary and format failures.** The code says “Do NOT include `Controls` or `Weakness:` in consequences” in prose at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:42-43`, but there is no validator to enforce it, which lines up with `insight_claude.md` N6 and `insight_codex.md` N3. The same lack of enforcement also explains malformed `review_lever` noted in `insight_claude.md` N7.

- **B4 explains why the Nemotron failures remain hard to diagnose.** `insight_claude.md` N1 and `insight_codex.md` N7 show total parse failure, but the runner currently preserves only the error string in `outputs.jsonl`; it drops plan-level raw/debug artifacts on failure. That is an observability bug more than a generation bug, but it blocks root-cause analysis.

- **S1 is the best code-level explanation for duplicate themes and weak novelty control.** The follow-up prompt only bans exact previous names, so it can easily produce semantically overlapping levers under new names, matching `insight_claude.md` N3 and the cross-response duplication concerns in `insight_codex.md`.

- **S2 explains the apparent contradiction between the code review and the prompt-leak evidence.** The current source no longer contains the template leak; the historical registered prompt does. So the domain-prefix behavior in `insight_claude.md` N2/N8 and `insight_codex.md` N1 is real, but it comes from the executed prompt artifact rather than the current `identify_potential_levers.py` prompt string.

- **S3 explains one discrepancy in the later synthesis questions.** The current source cannot by itself create four per-plan batches, because it hard-codes three calls. If the analysis counted four, that count must come from a different code revision or some wrapper-level orchestration, not from the present file.

## Summary

- The strongest confirmed code issue is that the step now accepts `5..7` levers and then blindly persists all of them, which directly explains the count violations.
- The second major issue is missing enforcement: most quality rules are descriptive text, not validators, so malformed-but-parseable outputs become “successful” cleaned artifacts.
- The current source does **not** explain the template-leak runs directly; that leak is in the historical registered prompt, while the source prompt has already been changed.
- The runner also throws away too much evidence on failure, which makes full-batch parse failures much harder to debug than they should be.
