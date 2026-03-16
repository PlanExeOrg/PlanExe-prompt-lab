# Code Review (codex)

Note: PR-specific line references below refer to the local PR branch `fix/partial-result-recovery` at commit `ecd8ab3b`. In this PR, `worker_plan/worker_plan_internal/lever/identify_potential_levers.py` changed; `prompt_optimizer/runner.py` is unchanged versus `origin/main`.

## Bugs Found

- **B1 — `review_lever` validation is still hardcoded to English literals, so call-1 failures remain structural and multilingual outputs are invalid by construction.** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:86-99` accepts a review only if it literally contains `Controls ` and `Weakness:`. That is exactly the brittle failure mode described in the insight files: weaker models alternate between a `Controls ...` clause and a `Weakness: ...` clause, and any first-call miss aborts the entire plan. It also directly violates the repo rule that prompt-optimizer validators must be language-agnostic (`prompt_optimizer/AGENTS.md:165-168`).

- **B2 — The `consequences` contract is documentation-only, so both missing numeric indicators and qwen-style review contamination pass untouched.** The schema says `consequences` must include `Immediate → Systemic → Strategic`, a measurable indicator, and must not contain `Controls ...` / `Weakness:` text (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34-45`), but the only validators in the model are for `options` and `review_lever` (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:60-99`). There is no validator or repair pass for `consequences`, so the current code path explains both insight findings: non-numeric consequence chains still ship, and qwen can copy `review_lever` text verbatim into `consequences` without being rejected or cleaned.

- **B3 — Placeholder leakage is allowed end-to-end because the active prompt teaches bracket scaffolding and the validator never rejects unreplaced placeholders.** The registered prompt used in this analysis batch literally teaches `"Controls [Tension A] vs. [Tension B]."` and `"Weakness: The options fail to consider [specific factor]."` (`prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:23-29`). The source validator in `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:95-98` only checks for marker presence, so copied bracket placeholders like `Controls [Production speed] vs. [City authenticity]` pass as “valid.” That matches the bracket-placeholder leakage reported in the successful `1/04` artifacts.

- **B4 — PR #292 recovers partial results but never records that recovery anywhere machine-readable.** The new PR path logs a warning and `break`s when a later call fails after at least one success (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:264-278`), but the returned object carries no `partial_recovery`, `failed_call_index`, or `responses_succeeded` field (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:312-333`). `prompt_optimizer/runner.py:302-311` then emits only `run_single_plan_complete` / `run_single_plan_error` and appends only `PlanResult{name,status,duration,error}`. This is the direct code-level reason the insight files had to infer salvage by manually counting `responses` in `002-9-potential_levers_raw.json`.

- **B5 — PR #292 stops at the first later-call failure, so a call-2 miss suppresses call 3 entirely and guarantees thinner salvage than necessary.** After a successful call 1, any exception in call 2 or call 3 reaches `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:264-278`; if `responses` is non-empty, the code `break`s out of the loop immediately. That means a call-2 failure does not merely preserve prior work — it also prevents call 3 from ever running. This is an important missed edge case in the PR itself, and it fits the thin salvaged artifacts: a raw file with exactly 1 stored response means the second call failed and the third call was skipped, not “calls 2 and 3 both failed independently.”

## Suspect Patterns

- **S1 — The active prompt teaches `review_lever` as two separate bullets instead of one exact combined string.** The registered prompt says `State the trade-off explicitly` and `Identify a specific weakness` as separate bullets (`prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:23-29`), while the schema description wants one field containing both sentences in order (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:51-58`). That mismatch is a plausible root cause of the llama3.1 pattern where outputs alternate between `Controls ...`-only and `Weakness: ...`-only reviews.

- **S2 — The runner and step do no prompt-length budgeting, so long plans go straight into structured JSON generation with no compression or truncation guard.** `prompt_optimizer/runner.py:56-66` concatenates the full contents of `001-2-plan.txt`, `002-6-identify_purpose.md`, and `002-8-plan_type.md` verbatim. Then each later call in `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:227-236` prepends an ever-growing name denylist and resends the full original prompt. That is a plausible explanation for the rotating gpt-oss-20b invalid-JSON failures landing on whichever plan is longest or most verbose in a given batch.

- **S3 — The option instructions are internally contradictory and remain a template-leakage vector.** The active prompt asks options to `Show clear progression: conservative → moderate → radical` (`prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:12-16`) while also banning the literal prefixes `Conservative:`, `Moderate:`, and `Radical:` (`prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:31-36`). That contradiction is exactly the sort of prompt construction that can teach the forbidden surface form even when the model is told not to emit it.

## Improvement Opportunities

- **I1 — Replace the English-literal `review_lever` gate with a language-agnostic per-lever linter/repair path.** The current all-or-nothing substring check in `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:86-99` is both too brittle and too strong. A safer design is: parse levers, repair or flag malformed reviews per lever, and only reject the specific lever if repair fails. That would preserve valid sibling levers and would comply with `prompt_optimizer/AGENTS.md:165-168`.

- **I2 — Add a real `consequences` validator or repair pass.** The source already states the intended contract at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34-45`; it should be enforced. A low-risk fix is a post-parse repair that strips trailing `Controls ... Weakness: ...` contamination and a validator that checks for the three labels plus some numeric signal before final save.

- **I3 — Make partial recovery explicit in the artifact schema and event log.** Extend `IdentifyPotentialLevers.to_dict()` in `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:321-333` to include fields such as `partial_recovery`, `failed_call_index`, `calls_attempted`, and `calls_succeeded`, and emit a dedicated event from `prompt_optimizer/runner.py:302-311`. That would close the observability gap without changing generation behavior.

- **I4 — Continue after a later-call failure instead of unconditional `break`, or retry that call with a reduced-context prompt.** The PR currently exits the loop at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-278`. If the goal is “recover as much as possible,” the more faithful implementation is to keep prior successes and still attempt remaining scheduled calls, or at least retry the failed call once with a shorter prompt or simpler schema.

- **I5 — Turn on first-call repair/retry instead of giving schema/JSON failures exactly one shot.** `prompt_optimizer/runner.py:93-94` constructs `LLMExecutor` with default settings, so the step gets no validation retry help. `worker_plan_internal/llm_util/llm_executor.py:180-207` already has `max_validation_retries` and validation-feedback plumbing; `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:249-257` could inject that feedback into the next attempt. That would specifically target the remaining call-1 failures that PR #292 cannot salvage.

- **I6 — Budget the prompt length before sending it to weaker structured-output models.** The current runner path at `prompt_optimizer/runner.py:56-66` and `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:227-236` never trims long plan context. A simple char/token budget or pre-summary step would likely reduce the rotating invalid-JSON failures on gpt-oss-20b.

- **I7 — If prompt-level fixes are pursued, apply them to the registered prompt file used by the runner, not only to `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`.** `prompt_optimizer/runner.py:436-459` reads `--system-prompt-file` from disk, and the analysis metadata points to `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt`. So the useful prompt fixes here are: show one exact combined `review_lever` example, remove literal bracket placeholders, and avoid teaching `conservative/moderate/radical` wording in the first place.

## Trace to Insight Findings

- `insight_claude.md` N1 and `insight_codex.md` “first-call failures still kill the whole plan” map directly to **B1** and **S1**. The code still makes `review_lever` a literal English gate, and the prompt still teaches the two required clauses separately.

- `insight_claude.md` N2 and the thin salvaged outputs in `insight_codex.md` map directly to **B5**. A successful call 1 followed by a failed call 2 produces exactly the observed one-response salvage because call 3 is never attempted.

- `insight_claude.md` N3 and `insight_codex.md` rotating gpt-oss-20b JSON failures are best explained by **S2**, plus the lack of first-call retry/repair captured in **I5** and **I6**.

- `insight_claude.md` N4 and `insight_codex.md` missing measurable indicators map directly to **B2**. The source describes a strict `consequences` format but never validates or repairs it.

- `insight_claude.md` N5 maps directly to **B4**. The PR warning lives only in logs; neither the raw artifact schema nor `events.jsonl` / `outputs.jsonl` records partial recovery.

- `insight_codex.md` bracket-placeholder leakage maps directly to **B3**. The active prompt teaches bracket placeholders, and the validator treats them as valid because it only checks for `Controls` / `Weakness:` markers.

- The oversize haiku outputs are not a PR #292 regression. They follow the existing design: the prompt asks for 5–7 levers per response (`prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt:3-5`) and the step hardcodes 3 calls (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:222-227`), so 15–21 pre-dedup levers are expected when all three calls succeed.

## PR Review

- **Does the implementation match the intent?** Mostly yes. The core PR change at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:264-278` does stop later-call failures from wiping out earlier successful calls. Since successful results are appended before the loop finishes (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:280-282`) and flattened only after the loop (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:284-318`), the PR genuinely preserves prior batches that used to be lost.

- **What gap remains?** First-call failures are still total failures by design (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-273`). That matches the PR description, but it also means the dominant remaining reliability problem is untouched: weak models that miss the `review_lever` or JSON contract on call 1 still abort the plan.

- **What bug does the PR itself leave behind?** The unconditional `break` at `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-278` is too blunt. It salvages prior work, but it also gives up on all remaining calls. For a call-2 failure, that makes the saved output smaller than it needs to be.

- **What observability gap remains?** The PR adds only a logger warning. Because `prompt_optimizer/runner.py:302-311` still records only success/error at the plan level, analysts cannot tell “3 clean calls” from “1 salvaged call” without inspecting raw files.

- **Any prompt-construction or chat-history regression in this PR?** I did not find one. `prompt_optimizer/runner.py:56-66` builds the user prompt the same way as `worker_plan/worker_plan_internal/plan/run_plan_pipeline.py:380-384`, and each identify call still sends a fresh `[system, user]` pair (`worker_plan/worker_plan_internal/lever/identify_potential_levers.py:238-245`) rather than accidentally duplicating user or assistant history.

- **Overall assessment.** Keep the PR idea, but treat the implementation as incomplete. PR #292 fixes the specific “later-call failure discards prior calls” bug, but it still leaves three important quality gaps in place: call-1 brittleness, no partial-save telemetry, and premature loop exit after the first salvaged failure.

## Summary

PR #292 is a real improvement, but the code review shows why the after-cohort still has the same shape of failures.

The biggest confirmed bug is still the English-literal `review_lever` validator: it makes first-call schema failures structural, not incidental. The second confirmed bug is that `consequences` has a strict written contract but no enforcement, which cleanly explains both the missing measurable indicators and the qwen contamination. The PR-specific gaps are also clear: partial recovery is invisible to the artifacts, and a call-2 failure aborts call 3 entirely, which is why salvaged outputs are useful but thin.

If I were prioritizing follow-ups, I would do them in this order: make `review_lever` validation language-agnostic and non-fatal per lever, add explicit partial-recovery telemetry, and change the later-call `break` into either “continue remaining calls” or “retry with reduced context.”
