# Code Review (codex)

## Bugs Found

### B1 — Calls 2 and 3 reuse contaminated assistant history instead of starting from a clean prompt
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:183-211`, the code builds one `chat_message_list` and keeps appending to it across all 3 calls.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:196-203`, calls 2 and 3 only add `Generate 5 MORE levers...` plus a blacklist of names; they do not rebuild a fresh message set with the original plan documents.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:234-245`, the previous assistant payload is appended back into the conversation and then becomes part of the next call's context.
- This is a real prompt-construction bug, not just a style issue: later generations are conditioned on prior generated JSON/review text, so field leakage and format drift can propagate from call 1 into calls 2 and 3.

### B2 — The code feeds back the loosest assistant representation, not the normalized structured result
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:234-241`, the carry-forward assistant message prefers `result["chat_response"].message.content` and only falls back to `result["chat_response"].raw.model_dump_json()`.
- That means even when the structured parser successfully extracted `DocumentDetails`, the next call may still be shown the original raw assistant text instead of the cleaned canonical JSON.
- If `message.content` contains extra prose, paraphrased templates, or subtly malformed formatting, that noisier form becomes the seed for the next generation round.
- This directly increases the chance of contamination like `Controls ... Weakness:` leaking into `consequences` on later calls.

### B3 — The schema contract for `consequences` and `review_lever` is descriptive only; invalid content is written straight through
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30-40` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:47-53` describe strict format requirements, but the only actual field validator is the `options` parser at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:56-67`.
- The clean-output path at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:253-264` and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:302-304` blindly copies `lever.consequences` and `lever.review_lever` into the final artifact.
- Result: content that violates the field boundary contract can still pass type validation and be saved as if it were valid output.
- That matches the qwen run behavior exactly: JSON is valid, but the wrong field content survives into `002-10-potential_levers.json` unchanged.

## Suspect Patterns

### S1 — Mandatory `summary` adds failure surface and token load, but the clean artifact discards it
- `summary` is required at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:79-80`.
- The step stores it in raw responses at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270-276`, but `save_clean()` writes only lever items at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:302-304`.
- So each of the 3 LLM calls must generate an extra required paragraph that is not used by the main scored output. That likely worsens latency and parse fragility on weaker models, especially after `levers` was tightened to exactly 5.

### S2 — Exact-5 enforcement is useful, but there is no repair path when a model over-generates
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:74-77` makes `levers` an exact-length field.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94` constructs `LLMExecutor` with default settings, so this runner does not opt into validation retries.
- Combined with `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:213-224`, a near-miss response becomes a hard plan failure instead of a targeted retry like “return exactly 5 items and no trailing text.”
- This looks like a strong contributor to the new `lever_index 6` / trailing-characters failures.

### S3 — Later calls are likely to become less domain-grounded as the conversation grows
- On call 1, the model sees the full plan documents via `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:196-197`.
- On calls 2 and 3, the new user message shrinks to a blacklist-only delta at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:198-203`, while the conversation keeps expanding with prior generated output.
- Even though the original plan text is technically still in the history, it becomes farther away and less salient than the earlier generated levers.
- That is a plausible code-level cause of generic naming/template drift in weaker models.

### S4 — The runner comments claim per-plan isolation, but the lock does not cover the actual LLM run
- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:96-109` says configuration and running should be protected because dispatcher state is global, but only handler registration is under the lock.
- The actual call to `IdentifyPotentialLevers.execute()` happens outside that critical section at `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:111-116`, with removal later at `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:139-143`.
- I do not think this explains the lever-quality issues directly, but it can contaminate per-plan telemetry when multiple workers are used.

## Improvement Opportunities

### I1 — Rebuild a fresh message list for each of the 3 lever-generation calls
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:195-215`, create a fresh list each time: system prompt + original `user_prompt` + a short exclusion note for already-used names.
- Do not append prior assistant JSON into calls 2 and 3.
- This is the highest-leverage fix because it removes the contamination conduit while preserving diversity pressure.

### I2 — If any carry-forward is kept, use canonical normalized data only
- Change `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:237-240` to use `result["chat_response"].raw.model_dump_json()` or, better, a compact synthesized list of generated names.
- Never prefer raw `message.content` for prompt carry-forward.
- That would reduce propagation of provider-specific formatting noise.

### I3 — Add semantic validators or a repair pass before writing `002-10-potential_levers.json`
- Add field validators in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` that reject:
  - `consequences` containing `Controls` or `Weakness:`
  - missing `Immediate → Systemic → Strategic` structure
  - `review_lever` missing the two required sentences
- Alternatively, insert a normalization/repair pass just before `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:253-264`.
- This would catch field-boundary leaks that the current type-only schema misses.

### I4 — Turn on validation retries in the prompt optimizer runner for this step
- At `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94`, instantiate `LLMExecutor` with `max_validation_retries > 0` for this experiment harness.
- Then make `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:213-224` inspect `llm_executor.validation_feedback` and append a short correction note on retry.
- This is the clearest code-level mitigation for the new gpt-oss “6th lever fragment” failures.

### I5 — Make `summary` optional or remove it from this step's required response schema
- Revisit `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:79-80`.
- If the summary is not used in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:302-304`, it should not be a mandatory output for every one of the 3 calls.
- This should reduce verbosity, latency, and failure surface without harming the final lever artifact.

### I6 — Add a final merged-output check for duplicate or overly generic lever names
- After merging at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:248-264`, verify that the 15 lever names are distinct and sufficiently domain-grounded.
- If the merged set fails, regenerate only the offending call instead of accepting a weak but valid batch.
- This would address the “structurally valid but generic” model behavior that prompt-only instructions are not reliably fixing.

## Trace to Insight Findings

- **Insight Claude N3 / Insight Codex severe field-boundary leak in run 57** is best explained by **B1 + B2 + B3**. The code keeps prior assistant output in the conversation, later calls are driven by that history, and there is no validator stopping `Controls ... Weakness:` from surviving in `consequences`.
- **Insight Claude N2 / Insight Codex run 55 parser failures (`lever_index 6`, trailing characters)** are not caused by one single line here, but **S2 + I4** explain why they become hard failures: exact-length validation exists, but the runner/step pair does not use a repair retry path.
- **Insight Claude N4/N5 and Insight Codex generic/template-heavy weaker-model behavior** are plausibly explained by **S3**. Calls 2 and 3 are less explicitly grounded in the project documents and increasingly grounded in previously generated levers, which is exactly the setup that tends to produce abstract cross-domain strategy names.
- **Insight Claude P1** is consistent with `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:74-77`: exact-length enforcement clearly fixed the previous over-count issue.
- **Insight Claude P2 and the observed regression risk in weaker models** match **S1**: requiring `summary` likely improved completeness for stronger models, but it also adds mandatory output that the clean file throws away.
- **Insight Codex complaints about format drift in runs 56 and 59** are reinforced by **B3**. The code has strong prose instructions, but almost no executable validation beyond basic types/counts.
- **Insight Claude N6 / Insight Codex run 53 full extraction failure** is **not fully explained by these two files**. The reviewed code does not contain the JSON-extraction implementation; what it does show is that the step has no recovery path once structured parsing fails.

## Summary

The main root cause I see is not the prompt text itself; it is the call structure.

`identify_potential_levers.py` is running a 3-call generation loop as one growing chat thread, then feeding prior assistant output back into later calls. That creates a direct contamination path and weakens domain grounding over time. On top of that, the schema only enforces counts/types, not the actual field contract, so bad-but-parseable content is saved as valid output.

The highest-leverage fix is to change the multi-call strategy: fresh context per call, original plan documents included every time, only a compact exclusion list carried forward, plus light semantic validation/repair before saving. After that, add validation retries in the runner so near-miss outputs do not become full plan failures.
