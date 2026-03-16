# Code Review (codex)

## Bugs Found

- **B1 — Partial-recovery loop aborts too early.** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:264-278`, any exception after at least one successful call logs a warning and then `break`s at line 278. That means a call-2 failure suppresses call 3 entirely, even though the surrounding design is explicitly “3 calls, keep partial results”. This is a real control-flow bug, not just a prompt issue.

- **B2 — `review_lever` validation does not enforce the contract it claims to enforce.** The schema and prompt describe an exact two-sentence format in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:51-57`, `:145-150`, and `:178-183`, but the actual validator at `:86-99` only checks for the substrings `"Controls "` and `"Weakness:"`. It does not require `vs.`, does not require the `The options fail to consider ...` wording, does not reject bracket placeholders, and does not cap the field to two sentences. That mismatch lets most near-miss reviews ship as “valid”, which matches the insight files' exact-format drift.

- **B3 — Runner bookkeeping is not exception-safe after the start event.** `_run_plan_task()` emits `run_single_plan_start` before doing any work in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:298`, then assumes the rest of the path cannot fail unexpectedly. But `run_single_plan()` has cleanup in `finally` at `:139-143`, and `_run_plan_task()` itself writes terminal events and `outputs.jsonl` only after `run_single_plan()` returns at `:300-311`. If cleanup or bookkeeping raises, the run is left with only a start event, and `future.result()` at `:388-389` can abort the whole batch. That is a credible code-level explanation for the “start-only” incomplete run footprint.

## Suspect Patterns

- **S1 — The prompt/schema contains multiple literal placeholders that models can copy.** Bracketed templates such as `[Tension A]`, `[Tension B]`, `[specific factor]`, and `[effect]` appear in the raw field descriptions and system prompt at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36-44`, `:53-56`, `:130-138`, `:147-150`, and `:163-183`. Because `as_structured_llm(DocumentDetails)` uses that schema text directly, these placeholders are part of what the model sees. That is a strong leakage vector for the placeholder-copying seen in `review_lever`.

- **S2 — One bad lever invalidates the whole call.** The structured call is made against `DocumentDetails` in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260`, and `DocumentDetails.levers` requires a valid list of `Lever` items at `:109-112`. Because `Lever` has hard validators for `options` and `review_lever` at `:60-99`, one malformed lever causes the entire response to fail validation. That architecture fits the “all-or-nothing cascade” described in the insight files.

- **S3 — The step is hard-wired to over-generate.** The loop is fixed at `total_calls = 3` in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:222`, and calls 2/3 explicitly ask for `5 to 7 MORE levers` at `:233-235`. There is no adaptive stop once enough unique levers exist, and dedup only removes exact name matches at `:289-296`. This makes 15+ merged levers inevitable and explains why the final artifact systematically exceeds the per-response limit.

- **S4 — Worker-count resolution is profile-blind and merge-order dependent.** `_resolve_workers()` in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:224-254` glob-loads every `llm_config/*.json`, merges them into one dict, and picks the first matching model entry that survives the merge. That bypasses the same profile-selection logic used by `get_llm()`, so `meta.json` and thread-pool sizing can silently drift from the actual runtime model profile.

## Improvement Opportunities

- **I1 — Replace `break` with `continue` and emit a partial-recovery event.** The bug at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:278` is the lowest-risk fix. Pair it with a new event from `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:303-311` or directly from the lever step so analysis can distinguish “hard failure” from “recovered with fewer calls”.

- **I2 — Add real post-parse normalization for `review`, `consequences`, and `options`.** Right now the clean model in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:117-152` is a pass-through, and the copy into final output at `:299-305` preserves every format defect. A repair layer here could normalize near-miss `review_lever` text, strip leaked `Controls ... Weakness: ...` tails out of `consequences`, and reject/repair `Title: description` options.

- **I3 — Salvage good levers instead of rejecting whole responses.** The structured-call boundary at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260` is too coarse for noisy models. A better design is: extract JSON once, validate each lever individually, keep good levers, and log repairs/rejections. That would directly reduce the “one bad field discards 300+ seconds of work” failure mode.

- **I4 — Remove bracket placeholders from the schema/prompt, or swap them for concrete examples.** The repeated placeholder text in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36-44`, `:53-56`, and `:163-183` is not neutral wording; it is copyable output. Replacing those with one concrete valid example and one invalid example would likely help both placeholder leakage and exact-format compliance.

- **I5 — Stop paying token/latency cost for outputs that the step never uses.** `DocumentDetails` still asks the model for `strategic_rationale` and `summary` in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:101-115`, but the clean result stored at `:312-346` only keeps the levers. On slower models, that unused generation budget likely hurts latency and may crowd out the fields that actually matter.

- **I6 — Make the call count adaptive to the target unique-lever range.** The fixed `total_calls = 3` at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:222` guarantees merged over-generation. Stop once the cleaned list reaches the desired unique count, or ask for fewer “MORE levers” on later calls.

- **I7 — Harden runner cleanup and terminal logging.** Guard `dispatcher.event_handlers.remove(track_activity)` in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:141-142`, wrap `_run_plan_task()` in its own `try/except/finally` around terminal event writing at `:298-311`, and log `exc_info=True` at `:132`. That would make incomplete runs much easier to diagnose.

- **I8 — Resolve worker count through the same config/profile path as model creation.** `_resolve_workers()` in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:224-254` should use the active llm-config/profile loader instead of a raw glob merge. Even when it does not break correctness, it makes speed comparisons and `meta.json` less trustworthy.

## Trace to Insight Findings

- **B1 / I1** map directly to the backlog item called out in `insight_claude.md` (“`break` → `continue` in call-2 failure handler”). The current code at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:278` exactly matches that diagnosis.

- **B2** explains why `insight_codex.md` reports weak *exact* `review_lever` compliance even when many runs produced no schema failures. The validator in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:86-99` is too weak to enforce the literal protocol.

- **S1 / I4** explain the placeholder leakage noted in `insight_codex.md` for run 12. The bracketed schema/prompt templates in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36-44`, `:53-56`, and `:163-183` give the model exact leakable text.

- **I2** explains the persistent qwen formatting issues from both insight files: there is no code-side guard for `Title: description` options, and no repair pass for `consequences` contaminated with review text. The final output copy step at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:299-305` preserves both defects unchanged.

- **S2 / I3** explain the gpt-5-nano parasomnia collapse in `insight_claude.md`: when one response fails the `Lever` schema, the whole `DocumentDetails` call fails at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-260` instead of salvaging the valid levers.

- **S3 / I6** explain the systematic over-generation called out in both insight files. The merged output is oversized because the code is explicitly written to make three 5–7 lever calls, not because models are spontaneously disobeying a global 5–7 total limit.

- **B3 / I7** match the “run 1/09 incomplete” footprint in `insight_claude.md`: start event present, no terminal event, no `outputs.jsonl`, leftover `track_activity.jsonl`. The control-flow hole is in `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:139-143`, `:298-311`, and `:388-389`.

- **I5** is a likely contributor to the extreme slowness highlighted for `openai-gpt-5-nano` in `insight_claude.md`: the model is asked to generate `strategic_rationale` and `summary` on every call even though the step discards them from the clean output.

## Summary

The strongest code-level findings are: a real `break`/`continue` bug in the multi-call loop, a `review_lever` validator that is much weaker than the documented contract, and runner bookkeeping that can plausibly leave “start-only” history runs when cleanup/logging fails. Beyond that, the current architecture leans too heavily on whole-response structured validation and too lightly on post-parse repair. That combination explains why the step is simultaneously strict enough to throw away expensive generations and permissive enough to let many off-format outputs pass through unchanged.
