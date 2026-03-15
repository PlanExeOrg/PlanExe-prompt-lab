# Code Review (codex)

## Bugs Found

- **B1 — The structured-output schema gives the model instructions that conflict with the step contract.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:30`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:33`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:36`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:58`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:61`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:99`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:111`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:114`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181`.
  `IdentifyPotentialLevers.execute()` uses `llm.as_structured_llm(DocumentDetails)`, so the Pydantic field descriptions become part of the model-facing schema prompt. Those descriptions do not match the system prompt: `consequences` is described as a generic plain-prose 30-word field, `options` is described as `2-5 options`, `review_lever` does not require the literal `Weakness:` form, and `summary` is optional and generic. That hidden schema prompt directly competes with the explicit step contract (`Immediate → Systemic → Strategic`, exactly 3 options, exact review wording, non-null summary), which is a strong code-level explanation for the format drift in runs 35/36/37 and the null summaries in run 33.

- **B2 — The step never enforces exact lever count, option count, or required non-placeholder fields.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:33`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:58`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:61`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:216`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:218`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:224`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:269`.
  The code relies on descriptions like “Propose exactly 5 levers” and “2-5 options”, but there are no validators, no `min_length` / `max_length` constraints, no placeholder checks, and no regex checks for the consequence/review surface form. After each call, it blindly flattens every returned lever into the final artifact. That means a 6-lever response, a 2-option lever, a blank option, a `placeholder` lever, or a null summary is treated as structurally valid as long as it parses into the loose schema.

- **B3 — The 3-call generation loop self-conditions on prior assistant output and grows the prompt every round.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:150`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:162`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:166`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:173`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:201`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:211`.
  Calls 2 and 3 do not start from a fresh prompt. Instead, they append another user message to the existing conversation and then append the full prior assistant response back into history. The only novelty instruction is “Generate 5 MORE levers with completely different names”. That creates two problems: later calls are primed by the model’s own earlier wording, and the prompt payload grows with each round. This is a concrete root cause for repeated stylistic/template patterns across batches and a plausible code-side contributor to the haiku timeouts and truncation failures on the longest plans.

- **B4 — The prompt-lab runner promotes malformed-but-parseable output to `ok` with no quality gate or regeneration.**
  `prompt_optimizer/runner.py:113`, `prompt_optimizer/runner.py:114`, `prompt_optimizer/runner.py:118`, `prompt_optimizer/runner.py:120`, `prompt_optimizer/runner.py:123`, `prompt_optimizer/runner.py:125`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:237`.
  `run_single_plan()` treats `IdentifyPotentialLevers.execute()` as successful if it returns without throwing. It immediately writes `002-9-potential_levers_raw.json` and `002-10-potential_levers.json`, then records `status="ok"`. There is no post-parse validator for the exact 5×3 contract, the consequence chain, numeric systemic metrics, `Controls ... vs. ... Weakness: ...`, prefix leakage, blank options, or placeholders. That is why runs 35, 36, 37, and 38 can all surface “successful” plans despite obvious contract violations in the final artifact.

- **B5 — Per-plan activity logging is not isolated when the runner uses multiple workers.**
  `prompt_optimizer/runner.py:96`, `prompt_optimizer/runner.py:97`, `prompt_optimizer/runner.py:104`, `prompt_optimizer/runner.py:108`, `prompt_optimizer/runner.py:139`, `prompt_optimizer/runner.py:141`, `prompt_optimizer/runner.py:380`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:207`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:213`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:302`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:311`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:371`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:396`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:406`.
  The runner creates one `TrackActivity` handler per plan and registers it on the global dispatcher while other plans may be running concurrently (`luigi_workers` is often 4 for the reviewed models). The code only locks handler add/remove, not event handling. `TrackActivity` guards duplicate writes for `usage_metrics.jsonl`, but it does not filter `activity_overview.json` or the per-plan `track_activity.jsonl` by plan/task identity before writing. In parallel runs, each plan-local tracker can therefore observe other plans’ LLM events, which makes call counts and per-plan activity files unreliable.

## Suspect Patterns

- **S1 — The runner deletes `track_activity.jsonl` even when the run fails.**
  `prompt_optimizer/runner.py:99`, `prompt_optimizer/runner.py:143`.
  This does not create the malformed outputs, but it does erase the most detailed per-event trace that could explain why a specific plan timed out, retried, or produced an extra instrumentation count. That makes issues like the missing/inconsistent `activity_overview.json` much harder to diagnose after the fact.

- **S2 — Cross-call novelty is enforced only on names, not on mechanisms or trade-offs.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:160`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:166`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:211`.
  The follow-up prompt forbids reusing earlier names, but it does not forbid reusing the same strategic idea under a new label. That is not the direct cause of the gta 16-lever count bug, but it is a likely contributor to near-duplicate levers and repeated “hyphen-Strategy” naming across calls.

## Improvement Opportunities

- **I1 — Align the schema with the real contract and enforce it in code.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:23`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:53`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181`.
  Make the field descriptions match the intended output exactly, then add validators: 5 levers per response, 3 options per lever, non-empty/non-placeholder strings, required `summary` if it matters, and exact consequence/review pattern checks. Right now the hidden schema prompt and the actual contract disagree.

- **I2 — Rebuild the chat history per call instead of replaying prior assistant JSON.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:150`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:166`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:201`.
  For calls 2 and 3, start from `[system, original project brief + explicit exclusion list]` rather than the entire previous conversation. Carry forward only the normalized exclusion data you actually need, not the model’s full prose/JSON output. That should reduce template anchoring, prompt growth, and timeout pressure.

- **I3 — Add a validator+retry layer before writing the final files and before returning `status="ok"`.**
  `prompt_optimizer/runner.py:113`, `prompt_optimizer/runner.py:118`, `prompt_optimizer/runner.py:125`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:216`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:237`.
  After each raw response, reject or retry responses that do not have exactly 5 levers, 3 options per lever, valid consequence chains, valid review strings, and non-placeholder content. Then run the same checks again on the merged 15-lever artifact before saving it. This is the highest-leverage fix for the 16-lever gta outputs, 2-option tails, chainless consequences, and placeholder debris.

- **I4 — Add output-budget guardrails for verbose models.**
  `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:157`, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:201`, `prompt_optimizer/runner.py:93`, `prompt_optimizer/runner.py:114`.
  The reviewed path has no guard against runaway verbosity: no cap on follow-up context size, no per-call budget check, and no shortening strategy for difficult plans. Even without changing provider-level settings, trimming cross-call context and enforcing reasonable field-length targets before accepting output would reduce the timeout/truncation failure mode seen on the longest plans.

- **I5 — Make telemetry collection single-plan or properly scoped.**
  `prompt_optimizer/runner.py:96`, `prompt_optimizer/runner.py:108`, `prompt_optimizer/runner.py:380`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:207`, `worker_plan/worker_plan_internal/llm_util/track_activity.py:371`.
  If the optimizer needs trustworthy `activity_overview.json`, either run one plan at a time when tracking activity or tag/filter every instrumentation event by plan/task before writing per-plan files. The current setup makes activity files unreliable under parallel execution.

## Trace to Insight Findings

- **B1** explains the broad surface-form drift in both insight files: run 37’s plain-prose consequences, run 35’s semicolon/`Trade-off controls` rewrites, run 36’s short label-like options, and run 33’s null summaries all match the weaker, contradictory schema descriptions more closely than the stated system prompt contract.

- **B2 + I3** explain the hard structural failures highlighted in the insights: the recurring gta `16`-lever output, run 33’s 2-option tail failure, and run 38’s blank option / `placeholder` lever all pass because the code never enforces exact counts or rejects placeholder content after parsing.

- **B3 + I2 + I4** explain the reliability split on long plans. Replaying the full prior assistant output into calls 2 and 3 increases context size and encourages the model to elaborate in the same style, which fits the haiku timeouts and the gpt-oss / nemotron truncation pattern on the heaviest plans.

- **B4** explains why the optimizer reports high plan-success counts even when the output contract is visibly broken. The runner has no concept of “quality failure”: if parsing succeeds, runs like 35/36/37 are counted as `ok` even when consequence chains, review wording, or option structure are wrong.

- **B5 + S1 + I5** explain the instrumentation anomalies called out in `insight_claude.md` and `insight_codex.md`, especially the inconsistent call counts and missing/uneven activity artifacts. The current telemetry path is global, concurrent, and partly deleted at teardown.

- **S2** helps explain why several runs show high exact-name uniqueness but still feel semantically repetitive. The follow-up call only bans previously used names, not previously used strategic mechanisms.

## Summary

The biggest root cause here is not a single provider quirk; it is that the code accepts almost any parseable object as success while feeding the model mixed instructions from two prompt layers.

The priority order I would use is:

1. **I1 + I3** — make the schema and validator enforce the real 5×3 output contract.
2. **I2** — stop replaying prior assistant JSON into later calls.
3. **I4** — add context/output budget guardrails for verbose models.
4. **I5** — fix per-plan telemetry so the optimizer’s diagnostics can be trusted.

Those changes together explain most of the observed problems: extra levers, missing chains, weak review formatting, placeholder spillover, timeout-heavy long plans, and noisy activity logs.
