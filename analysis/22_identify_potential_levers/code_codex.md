# Code Review (codex)

## Bugs Found

### B1 — Parallel runs attach per-plan `TrackActivity` handlers to one shared dispatcher

- Root cause lives in `self_improve/runner.py:105`, `self_improve/runner.py:109`, `self_improve/runner.py:150`, and `self_improve/runner.py:405`.
- `run_single_plan()` creates one `TrackActivity` instance per plan, then registers it on the global LlamaIndex dispatcher. During multi-worker runs, every active handler receives every LLM event until its plan completes. `TrackActivity` writes each event to disk at `worker_plan/worker_plan_internal/llm_util/track_activity.py:396` and `worker_plan/worker_plan_internal/llm_util/track_activity.py:406`, so one completion event becomes N writes when N plans are running.
- That has two bad effects: per-plan activity streams are cross-contaminated while the run is active, and the runner pays O(workers²) event-write overhead. In the prompt-lab harness, that is a credible contributor to 600 s timeouts.
- Fix: do not register per-plan handlers on a shared dispatcher during parallel runs. Either force `workers=1` when activity tracking is enabled, or route events through a per-thread/per-plan dispatcher/context filter.

### B2 — Follow-up prompts embed raw model output without escaping

- The bug is in `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:264` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270`.
- `generated_lever_names` comes from prior model output, then gets interpolated directly into the next user prompt as `[...]` with ad-hoc quoting. A lever name containing `"`, `]`, or a newline can break the list shape and change the instruction semantics for calls 2 and 3.
- That is a prompt-construction bug and a prompt-injection/template-leakage vector. The input here is untrusted model text, so it should be serialized as data, not spliced into prose.
- Fix: serialize the blocklist with `json.dumps(generated_lever_names, ensure_ascii=False)` and explicitly tell the model to treat it as a data-only exclusion list.

### B3 — PR #316 makes the `review_lever` contract self-contradictory

- The changed hunk is at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:92` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:215`. The validator that still accepts the output is at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128`.
- The PR says `review_lever` is "two sentences" but replaces the exemplar with a single sentence: “This lever governs the tension between centralization and local autonomy, but the options overlook transition costs.” Because `check_review_format()` only checks minimum length and square brackets, one-sentence outputs now pass even though the prompt still claims two sentences are required.
- So the PR does not actually make the format consistent; it silently broadens the accepted contract without updating validation or downstream schema text.
- This is already visible in PR-run artifacts such as `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json:15` and `history/1/62_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json:26`, where many `review_lever` values are a single copied sentence.
- Fix: choose one contract and align all three surfaces: prompt, field descriptions, and validator. If you want two thoughts, model them as structured fields instead of sentence-count prose.

## Suspect Patterns

### S1 — One malformed lever still invalidates the whole structured call

- The relevant code is `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:115`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:153`, and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:300`.
- A single lever with the wrong option count, or a response with only 4 levers, makes the entire `DocumentDetails` parse fail. The later partial-recovery logic only preserves earlier successful calls; it does not salvage valid levers inside the failed call.
- I cannot prove from these two files alone how aggressively `as_structured_llm(...).chat(...)` retries after validation failure, so I am marking this as suspect rather than confirmed. But it is a plausible source of wasted time/tokens and of the `partial_recovery` events seen in `history/1/60_identify_potential_levers/events.jsonl:3` and `history/1/60_identify_potential_levers/events.jsonl:12`.

### S2 — PR #316 updates the raw `review_lever` instructions but leaves the cleaned schema stale

- The stale schema text is still at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:185`.
- `Lever.review_lever` is what the LLM sees, but `LeverCleaned.review` still documents the old `Controls ... / Weakness:` pattern. That does not change generation directly, yet it leaves two schema surfaces disagreeing after the PR.

### S3 — `self_improve.runner` inherits production worker counts for a much heavier harness

- The relevant code is `self_improve/runner.py:234` and `self_improve/runner.py:401`.
- The self-improve harness runs 3 structured calls per plan, adds tracking/event logging, and may execute many plans per run, but it still blindly uses `luigi_workers` from the main pipeline config. That is probably fine for the normal pipeline, but it is a risky default for prompt-lab evaluation where each unit of work is heavier and where B1 amplifies the cost of parallelism.

## Improvement Opportunities

### I1 — Align the live system prompt with `OPTIMIZE_INSTRUCTIONS`

- `OPTIMIZE_INSTRUCTIONS` says each lever should include at least one conservative, low-risk path at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:48`.
- The live system prompt instead pushes “at least one unconventional or non-obvious approach” at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:205`.
- That is the opposite bias. If the goal is grounded, feasible planning, the prompt should explicitly require one conservative/default option and only optionally encourage one unconventional option when justified.

### I2 — Add an anti-copy guard for exemplars

- The PR’s new exemplar is at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:94` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:217`.
- The wording is highly copyable, and the outputs already show leakage. Examples include `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json:15`, `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json:26`, and `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json:37`.
- Either add an explicit instruction like “Do not copy the example wording,” or use multiple stylistically different examples so the model learns the semantic target instead of one repeated sentence frame.

### I3 — Normalize lever names for both blocklisting and deduplication

- The two relevant spots are `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:331`.
- Today the code compares raw strings. A low-cost improvement is to canonicalize with `strip()`, whitespace collapse, and `casefold()` both when building the "already-generated names" list and when filtering final results.
- That will not replace downstream semantic dedup, but it will catch trivial repeats earlier and make follow-up prompts more reliable.

### I4 — Preserve real failure context when partial recovery happens

- The swallow-and-continue path is at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:305`. The runner only emits aggregate counts at `self_improve/runner.py:126` and `self_improve/runner.py:331`.
- Right now a partial recovery event tells you that a call failed, but not which call, which validator rejected it, or which `LLMChatError.error_id` to inspect.
- Emitting the failed call index and error id into the raw output metadata and `events.jsonl` would make prompt regressions much easier to debug.

## Trace to Insight Findings

- The two iteration-22 insight files contain no substantive findings; both are timeout placeholders. So there is no detailed insight-to-code mapping available from `analysis/22_identify_potential_levers/insight_claude.md:1` and `analysis/22_identify_potential_levers/insight_codex.md:1`.
- The strongest timeout hypothesis inside the reviewed code is B1: `self_improve/runner.py:401` enables parallel execution, and each parallel plan adds another active `TrackActivity` writer to the shared dispatcher. That creates avoidable write amplification during long prompt-lab runs.
- PR #316’s qualitative effect is easier to trace. The new single-sentence exemplar from `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:94` / `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:217` shows up almost verbatim in generated outputs like `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json:15` and `history/1/63_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:15`.
- The weakest-model issue also does not appear fully solved: `history/1/60_identify_potential_levers/events.jsonl:3` and `history/1/60_identify_potential_levers/events.jsonl:12` still show `partial_recovery` under `ollama-llama3.1`.

## PR Review

- The diagnosis behind PR #316 is directionally reasonable. Replacing the literal “First sentence / Second sentence” wording probably does reduce one kind of weak-model misread.
- I do not think the implementation fully matches the intent.
- Gap 1: the PR says “two sentences” while showing a one-sentence exemplar at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:94` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:215`.
- Gap 2: the validator at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128` does not enforce either the old two-sentence format or the new one-sentence example, so the contract remains loose and implicit.
- Gap 3: the cleaned output schema remains on the old contract at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:185`.
- Gap 4: the new exemplar is copied nearly verbatim across outputs, which is exactly the kind of template leakage the review should avoid.
- My recommendation is to either:
  - make `review_lever` explicitly one sentence everywhere and remove every “two sentences” reference, or
  - keep two semantic parts, but encode them as structured fields such as `core_tension` and `missed_weakness`, then compose the display string after validation.
- As written, I would not treat PR #316 as sufficient. It likely reduces one failure mode, but it does so by loosening the contract and increasing exemplar leakage rather than by making the format robust.

## Summary

- The main confirmed issues are the shared-dispatcher tracking bug in `self_improve/runner.py`, the unescaped interpolation of lever names into follow-up prompts, and the PR’s self-contradictory `review_lever` contract.
- The strongest non-PR improvement is to make the runner’s parallel tracking architecture safe or single-threaded.
- The strongest PR-specific fix is to align prompt text, validator behavior, and schema text around one explicit `review_lever` contract, while adding an anti-copy guard for the exemplar.
