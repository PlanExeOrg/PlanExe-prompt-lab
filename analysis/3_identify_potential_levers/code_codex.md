# Code Review (codex)

## Bugs Found

- **B1 — The 3-call loop self-conditions on prior JSON and only enforces name novelty.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:160`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:166`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:171`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:199`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:209`.
  Calls 2 and 3 do not ask for different *topics* or *mechanisms*; they only say “Generate 5 MORE levers with completely different names”. At the same time, the code appends the previous assistant response back into `chat_message_list`, using the full structured JSON when `message.content` is empty. That means later calls are primed by the model’s own previous wording and only pushed to rename it. This is a direct code-level explanation for cross-batch semantic duplication, repeated review stems, and repeated consequence phrasing. It also inflates the prompt every turn, which makes small-context models more likely to fail on later calls.

- **B2 — The schema is strict about wrapper fields that the final artifact throws away.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:53`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:54`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:235`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267`.
  `DocumentDetails` requires `strategic_rationale` and `summary`, but `save_clean()` writes only the flattened `levers` list. So the optimizer rejects outputs that have usable levers but omit the wrapper, even though those wrapper fields are not used in `002-10-potential_levers.json`. This matches the `gpt-4o-mini` failures where the model returned `{"levers": [...]}` and the entire plan was discarded.

- **B3 — The code does not enforce the actual contract of the merged lever artifact.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:33`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:57`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:213`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:220`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267`.
  The prompt says “exactly 5 levers per response” and “exactly 3” options, but the schema only uses descriptions. `options` is typed as a plain `list[str]`, `levers` is a plain `list[Lever]`, and the merge path blindly flattens whatever came back. There is no post-merge rejection for one-option levers, 6-lever responses, placeholder/meta levers, malformed consequence chains, or incomplete reviews. That is why structurally invalid outputs can still be saved as successful final artifacts.

- **B4 — The embedded prompt text contains the exact leakage phrases seen in the bad runs, and one instruction pair is internally ambiguous.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:94`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:100`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:101`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:104`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:110`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:111`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:117`.
  The default prompt literally includes `Systemic: 25% faster scaling through...`, `Material Adaptation Strategy`, and `Weakness: The options fail to consider ...`. Those exact phrases are reproduced in the failed-quality runs. Separately, the prompt tells the model to show a `conservative → moderate → radical` progression while only banning prefixes like `Option A:` and `Choice 1:`. That leaves `Conservative:`, `Moderate:`, and `Radical:` looking acceptable, which matches the option-prefix violations.

- **B5 — The optimizer runner disables the retry and validation-repair mechanisms, so transient/provider/parser failures become final data points.**
  `prompt_optimizer/runner.py:93`, `prompt_optimizer/runner.py:94`, `prompt_optimizer/runner.py:130`, `prompt_optimizer/runner.py:133`.
  `run_single_plan()` builds `LLMExecutor(llm_models=llm_models)` with no `RetryConfig` and no validation retries, then converts any exception into a terminal `status="error"`. For a prompt-optimization harness this is a real bug: it measures prompt quality through a single brittle call path, even though the shared executor already supports transient retries and validation retries. The empty-output, truncated-JSON, missing-wrapper, and timeout failures in the insight files are exactly the kinds of failures a hardened optimizer should retry or repair before counting a prompt run as failed.

## Suspect Patterns

- **S1 — The optimizer evaluates pre-dedup output even though this module already documents that duplicates are expected downstream.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:4`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:5`, `prompt_optimizer/runner.py:118`, `prompt_optimizer/runner.py:121`.
  The step docstring says duplicates are expected and handled by `deduplicate_levers.py`, but the runner stops after `IdentifyPotentialLevers.execute()` and writes that raw brainstorm set as the quality artifact. That may be intentional for prompt tuning, but it means some “quality” findings are really about evaluating the brainstorming stage without the cleanup stage the full pipeline normally runs.

- **S2 — Multi-call failures are wrapped without call index context.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:188`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:194`.
  This step makes 3 separate LLM calls, but every failure is wrapped as a generic `LLM chat interaction failed`. That loses whether batch 1, 2, or 3 failed, which makes it harder to distinguish “first call cannot parse at all” from “later call overflowed after chat history grew”. It does not create the quality problems by itself, but it hides useful debugging information for exactly the failure cluster seen in runs 24–31.

- **S3 — There is no preflight budget check against context growth.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:155`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:199`, `prompt_optimizer/runner.py:113`.
  The step always does 3 full structured calls, and later calls include earlier assistant JSON. There is no estimate of prompt size, no check of model metadata, and no adaptive downgrade for small-context models. Given the observed `3900`-token model in the insight notes, this omission is suspicious enough to deserve a guard.

## Improvement Opportunities

- **I1 — Make follow-up calls stateless or semi-stateless.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:160`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:166`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:199`.
  Rebuild each call from `system prompt + project context + concise already-covered topics`, instead of replaying the previous assistant JSON. Carry forward normalized topic summaries, not the model’s raw wording. This should cut template leakage, repeated review stems, and semantic duplicates while also shrinking prompt size.

- **I2 — Align validation with the artifact that is actually saved.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:53`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:57`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267`.
  Either keep `strategic_rationale` and `summary` in the final saved artifact, or make them optional for this step. Then add real validators for the things downstream actually depends on: exactly 5 levers per response, exactly 3 options per lever, and non-placeholder review/consequence fields.

- **I3 — Add a post-merge sanitizer before writing `002-10-potential_levers.json`.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:213`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:220`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267`.
  Reject or regenerate any lever with wrong option count, placeholder/meta text, duplicated name/topic, or missing review components. Right now the merge path is a pure flatten-and-save pass.

- **I4 — De-template the prompt and close the prefix ambiguity.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:100`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:104`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:111`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:117`.
  Replace literal examples with placeholders or multiple varied examples, and explicitly ban copied stems such as `25% faster scaling`, `Material Adaptation Strategy`, `The options fail to consider`, plus label prefixes `Conservative:`, `Moderate:`, and `Radical:`.

- **I5 — Turn on runner-side retries and use validation feedback.**
  `prompt_optimizer/runner.py:93`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:178`.
  The optimizer should instantiate `LLMExecutor` with transient retries and at least one validation retry, then make `IdentifyPotentialLevers.execute()` inspect retry feedback and append a corrective note only on retry attempts. That would make prompt comparisons less sensitive to random transport/schema failures.

- **I6 — Add a context-window guard before launching the 3-call plan run.**
  `prompt_optimizer/runner.py:113`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:155`.
  Estimate the token budget of `project context + prompt + previous outputs`, compare it against model metadata, and either refuse undersized models or switch to fewer/leaner follow-up calls. This is the cleanest code-side mitigation for the small-context failures described in the insight files.

## Trace to Insight Findings

- **B1** explains `insight_claude.md` N5 and `insight_codex.md` “reasoning diversity” problems: later batches are encouraged to rename prior ideas rather than explore new mechanisms, because the code only bans name reuse and replays earlier JSON verbatim.
- **B1 + S3 + I6** explain `insight_claude.md` N2.1/N2.4 and the note about Nemotron’s `3900` context window: the step grows the prompt across 3 calls and never checks whether the chosen model can hold that history.
- **B2** directly explains `insight_claude.md` N2.3 and `insight_codex.md` run `30`: the schema rejects missing `strategic_rationale`/`summary` even though `save_clean()` discards those fields.
- **B3** explains `insight_claude.md` N6/N9 and `insight_codex.md` constraint-violation table: one-option levers, malformed review fields, placeholder content, and wrong per-response counts are not programmatically rejected anywhere in this step.
- **B4** explains `insight_claude.md` N3/N4/N7 and `insight_codex.md` template-leakage metrics: the problematic strings are hard-coded in the prompt, and the prefix rule is ambiguous.
- **B5** explains `insight_claude.md` N1/N2 and `insight_codex.md` operational table: the optimizer runner is currently measuring single-attempt fragility, not the best recoverable result the shared executor infrastructure could achieve.
- **S1** is a caveat for synthesis: some duplication complaints may partly reflect that prompt-lab captures the brainstorming stage before the full pipeline’s deduplication stage.

## Summary

The main root cause is not one bug but a stack of compounding choices:
1. the multi-call loop reuses prior generated JSON and only asks for new names,
2. validation is backward (strict on discarded wrapper fields, weak on the artifact that matters),
3. the prompt text itself contains the exact leakage stems seen in bad runs, and
4. the optimizer runner does not use the retry/repair capabilities already present in the shared LLM executor.

If I had to prioritize fixes, I would do them in this order: **I2/I3** (validate the right artifact), **I1** (stop self-conditioning across batches), **I5** (turn on retries for the optimizer), then **I4/I6** (de-template prompt wording and add context-budget guards).
