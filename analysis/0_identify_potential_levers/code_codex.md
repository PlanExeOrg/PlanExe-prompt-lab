# Code Review (codex)

## Bugs Found

- **B1 — The first LLM call receives the same user prompt twice.** `IdentifyPotentialLevers.execute()` seeds `chat_message_list` with the full `user_prompt`, then iterates `user_prompt_list = [user_prompt, "more", "more"]` and appends `user_prompt` again before the first call. That means call 1 sees `SYSTEM + USER(prompt) + USER(prompt)`, while calls 2 and 3 do not. This is a real chat-history bug, not just a style issue, and it can overweight prompt examples and other anchoring language in the first batch. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:148-174`.

- **B2 — The step never enforces its own output contract before writing `002-10-potential_levers.json`.** The prompt requires exactly 5 levers per response and exactly 3 options per lever, but the Pydantic model only describes those constraints in `Field(...)` text; there is no validator on `len(levers)`, `len(options)`, review format, consequence labels, or placeholder leakage. The cleaned output is written straight to disk unchanged. That means malformed-but-parseable outputs survive into final artifacts. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:33-51`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:53-62`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:207-223`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:261-263`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121`.

- **B3 — Runner summaries count attempts, not plans, so resume/retry runs produce misleading totals.** `run()` keeps prior error rows in `outputs.jsonl` and only skips plans that later have an `ok` row. `main()` then summarizes by counting every row in `outputs.jsonl`, so a plan that fails once and succeeds later is counted twice in `total` and double-counted in duration. This is a confirmed logic bug in the reporting path. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:335-345`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:311`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:461-468`.

- **B4 — The runner's thread-safety around usage tracking is broken.** The comment says the code must hold a lock while configuring and running because dispatcher handlers and usage-metrics path are global state, but the lock only covers `add_event_handler()` / `remove()`. `set_usage_metrics_path(...)` and the actual `IdentifyPotentialLevers.execute(...)` call run outside the lock, while `run()` may execute multiple plans concurrently. That allows plans to overwrite each other's usage-metrics target and event-handler state. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:96-109`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:111-143`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:324-325`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:379-389`.

## Suspect Patterns

- **S1 — The 3-call generation strategy is a fragile continuation loop, not three clean samples.** After each response, the code appends the prior assistant output and then sends the one-word user prompt `"more"`. There is no explicit uniqueness instruction, no restatement of the formatting contract, and no guard against reusing prior lever names. This looks like a likely cause of cross-call duplication and batch-to-batch inconsistency. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:159-174`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:197-205`.

- **S2 — Assistant history is fed back as a Python `dict`, not a clearly serialized message.** The follow-up conversation stores `result["chat_response"].raw.model_dump()` directly as assistant `content`. If the underlying chat adapter stringifies this loosely, weaker models may see an awkward Python/JSON hybrid instead of clean natural-language context, which could contribute to schema drift or malformed follow-up generations. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:197-201`.

- **S3 — Duplicate names are acknowledged but intentionally allowed through the final file boundary.** The module header says duplicates are expected and deferred to a later dedupe step, and the merge path simply flattens all three responses and writes them. That may be acceptable architecturally, but it means `002-10-potential_levers.json` is knowingly lower quality than it could be. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:4-5`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:207-223`.

- **S4 — The runner has no upfront model-resolution check.** It constructs `LLMModelFromName` wrappers per plan and only discovers a bad model alias inside each plan execution. That pattern matches a failure mode where one bad model name creates one error per plan instead of one immediate run-level abort. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:315-390`.

## Improvement Opportunities

- **I1 — Fix the duplicated first prompt and make the multi-call protocol explicit.** Build the first request once, then either make two independent follow-up calls or use explicit continuation prompts like “Generate 5 additional levers that do not reuse prior lever names.” This removes the duplicated first prompt and gives later calls a clearer contract. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:148-174`.

- **I2 — Add hard validation before accepting each batch and before writing the merged file.** Enforce: exactly 5 levers per response, exactly 3 options per lever, consequence string starts with `Immediate:`, review starts with `Controls` and contains `Weakness:`, and no `[` / `]` placeholder scaffolding in any final field. Reject-and-retry bad batches instead of persisting them. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:33-62`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:165-223`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121`.

- **I3 — Stop treating `002-10-potential_levers.json` as a blind concatenation of three batches.** Deduplicate or rerank merged levers before writing the final file, or rename the current artifact to make clear it is only a merged-raw intermediate. This would remove the repeated-name issue at the point where downstream readers actually inspect the file. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:4-5`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:207-223`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:118-121`.

- **I4 — Add run-level model preflight validation.** Resolve all requested model names once before launching plan work, and fail fast if any alias is missing. That avoids wasting an entire run on a configuration mistake. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:315-390`.

- **I5 — Serialize prior assistant output intentionally.** If prior outputs must stay in context, feed back a compact JSON string or a curated summary of previously used lever names and themes; do not pass a raw `model_dump()` object as chat content. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:197-201`.

- **I6 — Either make usage/event tracking per-thread or widen the lock to cover the whole execution window.** The current hybrid approach keeps concurrency for the LLM call while still depending on global mutable state, which is the worst combination. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:96-143`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:379-389`.

- **I7 — Summarize by latest status per plan name, not raw row count.** Keep `outputs.jsonl` as an append-only attempt log if desired, but compute success totals from the latest row for each plan. Refs: `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:335-345`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:461-468`.

## Trace to Insight Findings

- **Run 00 template leakage / prompt anchoring:** **B1** is the clearest concrete bug here. Duplicating the entire user prompt on the first call increases anchoring pressure, and **S1/S2** show that later calls are driven by a brittle continuation protocol (`"more"` plus replayed assistant output) rather than a fresh constrained generation. Even when that is not the sole cause, it is exactly the kind of chat-history bug that can produce intra-run inconsistency.

- **Run 00 / Run 02 bracket placeholders surviving into final reviews:** **B2** explains why this reaches disk at all. There is no final-field validation for placeholder patterns, so any parseable response containing bracket scaffolding is accepted and written.

- **Run 09 option-count violations, and other format drifts in Runs 02/05/07:** **B2** also explains these directly. The contract lives only in prompt text and field descriptions, not in executable validation.

- **Baseline and run-history duplicate lever names:** **S1** and **S3** explain this best. The step is designed as a 3-batch merge with no uniqueness enforcement at merge time, and the continuation prompt is too weak to force novelty across batches.

- **Run 08 `LLM not found` repeated across all plans:** **S4/I4** map cleanly to this. The runner does not validate model names once at startup, so a bad alias is rediscovered inside every plan execution.

- **Run 03 schema mismatch and Runs 01/04/06 malformed JSON failures:** **B2/I2** explain why these are hard failures instead of recoverable batches. There is no caller-side validation/retry loop tailored to this step's contract before the batch is accepted or rejected.

- **Insight note that one plan appears twice in `outputs.jsonl` after retry/resume:** **B3** is the code-level explanation for why those duplicate rows remain and why naive summaries from `outputs.jsonl` are misleading.

## Summary

- The strongest confirmed bug is the **double user-prompt bug** in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:148-174`.
- The strongest quality gap is the **absence of executable validation** before writing merged lever artifacts; this directly permits option-count violations, placeholder leakage, and format drift.
- The biggest structural design issue is that the step writes a **raw 3-batch concatenation** as `002-10-potential_levers.json`, which bakes duplicate names into the artifact seen by downstream analysis.
- On the runner side, the most important operational fixes are **model preflight validation**, **plan-level summary deduping**, and **repairing the broken global-state concurrency handling**.
