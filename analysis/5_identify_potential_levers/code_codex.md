# Code Review (codex)

## Bugs Found

- **B1 — `strategic_rationale` and `summary` are optional in the schema, and `strategic_rationale` is never actually requested by the system prompt.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:61`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:68`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:101`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:124`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:195`.
  `IdentifyPotentialLevers.execute()` uses `llm.as_structured_llm(DocumentDetails)`, so the model is judged against the `DocumentDetails` schema. In that schema, both top-level fields default to `None`, so omission is valid. On top of that, the system prompt never mentions `strategic_rationale` at all; it only gives instructions for `review_lever` and `summary`. The result is that the model has no hard requirement to populate either field, which is a direct code-level explanation for the universal `strategic_rationale = null` and recurring `summary = null` seen in the insight files.

- **B2 — The code never enforces the advertised `exactly 5 levers` / `exactly 3 options` contract.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:39`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:40`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:65`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:66`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:229`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:236`.
  The schema uses plain `list[str]` for `options` and plain `list[Lever]` for `levers`; there is no `min_length`, `max_length`, or validator enforcing the counts promised in the descriptions. After parsing, the implementation blindly flattens every returned lever into the final artifact. That means a 2-option lever or a 6-lever raw response still counts as success if it parses, which matches the run-40 two-option defect and the previously observed 16-lever overflow risk.

- **B3 — The model-facing schema explicitly asks for extremely long consequence fields, which inflates outputs and raises timeout risk.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36`.
  Each lever's `consequences` field is described as `Target length: 150–300 words.` With 5 levers per call and 3 calls per plan, the step is implicitly asking for roughly 2,250–4,500 words of consequence text alone, before options, reviews, summary, or rationale. That target is far above the length bands that the insight files treat as healthy, and it is a straightforward code-side cause of the run-45 verbosity spike and timeout pressure on complex plans like `parasomnia_research_unit`.

- **B4 — The prompt-lab runner does not use the same retry behavior as the real pipeline, so its reliability experiments are harsher than production.**
  `../PlanExe/prompt_optimizer/runner.py:93`, `../PlanExe/prompt_optimizer/runner.py:94`, `../PlanExe/worker_plan/worker_plan_internal/plan/run_plan_pipeline.py:155`, `../PlanExe/worker_plan/worker_plan_internal/plan/run_plan_pipeline.py:171`, `../PlanExe/worker_plan/worker_plan_internal/plan/run_plan_pipeline.py:174`.
  `runner.py` constructs `LLMExecutor(llm_models=llm_models)` with no retry config, which means `retry_config.max_retries == 0`. The real pipeline path uses `RetryConfig()` when creating the executor. So the optimizer run that generated these insight files will fail immediately on transient timeout / empty-response conditions that the production task would retry. This does not explain every bad output, but it is a real experiment-skew bug and it likely exaggerates failures such as the timeout-prone or empty-response models.

- **B5 — Per-plan activity telemetry is cross-contaminated when the runner uses parallel workers.**
  `../PlanExe/prompt_optimizer/runner.py:99`, `../PlanExe/prompt_optimizer/runner.py:104`, `../PlanExe/prompt_optimizer/runner.py:108`, `../PlanExe/prompt_optimizer/runner.py:141`, `../PlanExe/prompt_optimizer/runner.py:380`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:302`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:313`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:396`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:406`.
  `runner.py` adds one `TrackActivity` handler per plan to a shared global dispatcher while multiple plans run concurrently. `TrackActivity` only guards `usage_metrics.jsonl` writes with the thread-local path check; it does **not** guard `_update_activity_overview()` or the raw event log append. So every active handler can count and persist events from other plans. That makes per-plan `activity_overview.json` unreliable under parallel execution, which is a strong explanation for the insight note that a run showed 10 LLM calls where the step structure suggests 9.

## Suspect Patterns

- **S1 — The structured-output schema and the system prompt disagree on several important requirements.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:39`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:43`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:68`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:109`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:124`.
  The system prompt says consequences must include explicit trade-offs, options must show conservative→moderate→radical progression with one unconventional choice and no prefixes, and reviews must contain both a `Controls ... vs. ...` sentence and a `Weakness:` sentence. The schema descriptions do not enforce most of that: `consequences` omits the trade-off requirement, `options` omits progression/prefix requirements, and `review_lever` does not require the literal `Weakness:` surface form. Because structured-output backends lean heavily on field descriptions, this mismatch is a plausible root cause for run-44 missing trade-offs in `consequences`, run-42 drifting to `Trade-off:` instead of `Controls`, and run-40 producing under-specified options/reviews.

- **S2 — Calls 2 and 3 are generated from accumulated chat history instead of a fresh prompt, so the model conditions on its own prior output.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:171`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:176`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:187`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:215`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:225`.
  The second and third turns only say `Generate 5 MORE levers with completely different names`, then feed the model its previous full structured answer as assistant history. That makes later turns mimic earlier wording and mistakes rather than independently regenerate from the source documents. I would not call this the sole cause of the qwen field-boundary leakage, but it is a credible amplifier for repeated stylistic artifacts and self-reinforcing prompt drift.

- **S3 — Name diversity is enforced only by a follow-up prompt, not by validation or normalization.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:174`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:180`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:225`.
  The implementation tracks prior names and asks for `completely different names`, but it never normalizes names, never checks duplicates inside the same 5-lever batch, and never rejects near-duplicates after parsing. That leaves diversity to model compliance alone. It does not explain the current batch's strong uniqueness, but it remains a weak point that matches the baseline duplicate-name history and could regress nondeterministically.

## Improvement Opportunities

- **I1 — Make the top-level contract explicit in the schema: either require `summary` / `strategic_rationale` or remove them.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:68`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:101`.
  If these fields matter, they should be non-optional and the system prompt should explicitly instruct the model to fill them. If they do not matter, remove them from the structured schema so they stop acting as dead weight.

- **I2 — Add hard schema constraints and post-parse validation before writing `status="ok"`.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:39`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:65`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:229`, `../PlanExe/prompt_optimizer/runner.py:118`, `../PlanExe/prompt_optimizer/runner.py:125`.
  The highest-leverage change is to reject or retry raw responses that do not have exactly 5 levers, exactly 3 options, non-null required fields, and minimally valid consequence/review formats. That would catch the run-40 two-option lever, null summaries, missing `Weakness:` reviews, and review text leaking into `consequences` before they are written as successful artifacts.

- **I3 — Align the field descriptions with the real prompt contract.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:39`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:43`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:68`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:109`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:124`.
  The schema should mention the same things the prompt cares about: trade-off wording inside `consequences`, exact review structure (`Controls ... vs. ...` plus `Weakness:`), anti-prefix rules, and the concrete `Add '...' to ...` summary form. Right now the model is being given two overlapping but non-identical contracts.

- **I4 — Shorten consequence targets to a realistic band and bound long-plan verbosity.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36`.
  Replacing the `150–300 words` target with a much tighter character or sentence budget would directly attack the run-45 bloat/timeout pattern and should also help smaller models avoid collapsing into label-like outputs by giving them a clearer target.

- **I5 — Rebuild calls 2 and 3 from the original plan context plus an exclusion list, not from the whole prior conversation.**
  `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:176`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181`, `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:215`.
  A fresh prompt per batch would reduce self-copying, keep context size stable, and make later calls less likely to inherit earlier field-boundary or formatting mistakes.

- **I6 — Make the runner mirror production execution more faithfully and add model-specific safeguards.**
  `../PlanExe/prompt_optimizer/runner.py:93`, `../PlanExe/prompt_optimizer/runner.py:300`, `../PlanExe/prompt_optimizer/runner.py:349`.
  Use the same retry config as the pipeline, consider optional validation retries, and add an explicit skip/warn path for models with repeated empty-JSON failure signatures. That will make prompt-lab comparisons more trustworthy and save time on known-bad model runs.

- **I7 — Scope telemetry to a single plan or tag/filter events by plan before writing per-plan files.**
  `../PlanExe/prompt_optimizer/runner.py:99`, `../PlanExe/prompt_optimizer/runner.py:108`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:396`, `../PlanExe/worker_plan/worker_plan_internal/llm_util/track_activity.py:406`.
  Right now the optimizer is producing per-plan telemetry from a shared concurrent event stream. Either serialize telemetry capture or route events to handlers by plan identity.

## Trace to Insight Findings

- **B1** explains the universal `strategic_rationale = null` finding and the recurring `summary = null` findings in runs 40, 41, and 44. The code currently makes omission valid and does not even ask for `strategic_rationale` in the system prompt.

- **B2** explains the run-40 lever with only 2 options and the broader concern about historical 16-lever overflow. The implementation never enforces the promised 5×3 structure after parsing.

- **B3** explains the run-45 verbosity spike and timeout risk. The code is explicitly asking for word counts that are large enough to produce the kind of bloated consequences reported in both insight files.

- **S1** explains several systematic contract drifts: run-44 missing trade-off language in `consequences`, run-42 preferring `Trade-off:` over literal `Controls`, and run-40 producing weak option/review structure. Those are exactly the requirements that are weak or missing in the model-facing field descriptions.

- **S2** is a plausible amplifier for the run-43 field-boundary leakage and other repeated style artifacts. Feeding the model its own prior JSON back into the conversation encourages the same pattern to recur in later batches.

- **B4** explains why prompt-lab reliability can look worse than the real pipeline on transient failures. The reviewed runner is not using the production retry policy.

- **B5** explains the `activity_overview.json` anomaly called out in `insight_claude.md` / `insight_codex.md` for run 42. The per-plan overview can count events from other plans when workers run in parallel.

- **I6** is the main code-side response to the persistent run-39 empty-JSON model failure and the run-41 / run-45 operational fragility: make the experiment runner more fault-tolerant and stop spending cycles on repeatedly failing models.

## Summary

The strongest confirmed bugs are:

1. top-level fields that are optional or not even asked for,
2. missing enforcement of the 5×3 structural contract,
3. an overlong consequence target that encourages bloated generations,
4. a runner that is not faithful to production retry behavior, and
5. cross-plan telemetry contamination under parallel execution.

The biggest quality lever is to stop treating `parseable JSON` as equivalent to `good output`. Tightening the schema, aligning it with the prompt, and validating outputs before they are written would directly address most of the observed failures: null summaries, short/label-like options, incomplete reviews, field leakage, and verbosity-driven timeout risk.
