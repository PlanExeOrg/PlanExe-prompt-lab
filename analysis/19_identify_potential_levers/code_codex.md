# Code Review (codex)

## Bugs Found

### B1 — PR #299’s new `review_lever` validator under-validates the contract it still documents
On the PR branch `fix/review-brackets-and-i18n-validator`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:92`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:157`, and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:216` still describe `review_lever` as a **two-sentence** field whose first sentence names the core tension and whose second sentence identifies a weakness. But the new `check_review_format()` only checks two things: length `>= 20` and absence of `[` / `]`.

That means all of these would now pass validation even though they violate the documented contract:

- one long sentence with no weakness,
- two sentences in the wrong order,
- vague filler like `This is a thoughtful strategic tension worth exploring.`

So the PR does not actually replace the old English-only validator with a real structural validator; it replaces it with a very weak length check. This is the clearest code-level explanation for the post-PR format drift in `insight_claude.md` (qwen3 / gpt-4o-mini switching away from the stable `Controls X vs. Y. Weakness: ...` shape) and for the generally thinner review content on weaker models.

### B2 — The code promises sentence-level option quality, but only validates option count
In the current source, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:47` says each option must be a “complete strategic approach (a full sentence with an action verb), not a label.” The only validator is `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:75`, which checks `len(v) == 3` and nothing else.

So label-only outputs such as `"Threat Assessment"` or `"Closed-Loop Ecology"` pass untouched as long as there are three of them. That exactly matches the llama3.1 failure pattern in `insight_claude.md` and `insight_codex.md`: later calls degrade into 2–3 word labels because the schema never enforces the “full sentence with an action verb” contract it advertises.

### B3 — `prompt_optimizer/runner.py` is not actually thread-safe despite the comment claiming it is
`/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:96` says usage tracking is global state and that the code will “hold a lock while configuring and running.” The implementation does not do that:

- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:106` calls `set_usage_metrics_path(...)` **outside** the lock.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:108` only locks while adding the event handler.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:114` runs the full LLM step **without** the lock.
- `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:140` and `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:141` clear the same global state at teardown.

With `workers > 1`, multiple plans can have handlers registered at the same time, and each handler can receive another plan’s events. The shared usage-metrics path can also be swapped mid-run by another thread. This does not directly explain the textual quality regressions, but it can corrupt `track_activity.jsonl`, `usage_metrics.jsonl`, and timing evidence used to diagnose them.

## Suspect Patterns

### S1 — The local `main` checkout is still pre-PR, so source inspection and run artifacts can disagree
The current checked-out file at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:51`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:88`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113`, and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:154` still contains the old placeholder-heavy review guidance, the English-only `Controls` / `Weakness:` validator, and the old `summary` description.

But the local branch `fix/review-brackets-and-i18n-validator` contains the PR-style changes. Since `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:33` imports `IdentifyPotentialLevers` directly from the working tree, experiments run from `main` would not reproduce the post-PR behavior seen in the insight files. That strongly suggests the artifacts were generated from the PR branch (or another checkout), not from the `main` tree currently visible to review.

### S2 — The later-call diversity control is prompt-bloating and too weak to prevent degraded repeats
`/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:222`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:231`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:233`, and `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:290` show a fixed three-call loop that keeps appending every prior lever name into a bracketed blacklist for later calls.

That has two likely side effects:

- later prompts get progressively longer and more brittle,
- the model is only forbidden from repeating exact names, not semantically similar levers or low-effort label-only options.

This pattern lines up with the exact failure shape in the insight files: llama3.1 is good in call 1, then gets worse in later calls; raw duplicate names also rise before downstream dedup cleans them up.

### S3 — `OPTIMIZE_INSTRUCTIONS` exists on the PR branch, but nothing enforces it
On `fix/review-brackets-and-i18n-validator`, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27` introduces a useful `OPTIMIZE_INSTRUCTIONS` constant. But the constant is not interpolated into `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:196`, and there is no test or validator that checks alignment with it.

So the branch now has two independent contracts:

- a prose “known problems” list in `OPTIMIZE_INSTRUCTIONS`, and
- the actual schema / prompt / validator behavior.

That is exactly how drift happens. The branch says “avoid hype, fabricated numbers, and English-only validation,” but only some of that is enforced in the code path that actually runs.

## Improvement Opportunities

### I1 — Keep the i18n fix, but restore real structure to `review_lever`
Update `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128` on the PR branch so the validator remains language-agnostic **without** collapsing to a pure length check. A better middle ground would be:

- require at least two non-empty sentences,
- reject square brackets,
- require the first sentence to contain a tension pair shape (for example, a separator like `vs.` / `versus` / locale-specific equivalent supplied by prompt text, or at minimum two contrasted noun phrases),
- require the second sentence to be materially distinct and longer than a tiny threshold.

If exact `Controls` wording is important downstream, repair it in a post-parse normalizer instead of hard-rejecting non-English text.

### I2 — Add a real option-quality gate or repair pass
The contract at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:47` is stronger than the validator at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:75`. Add a lightweight post-parse check for each option, such as:

- minimum word count,
- presence of a verb,
- punctuation / sentence shape,
- rejection of title-case labels with no verb.

That would directly target the persistent llama3.1 label-only options without needing to overfit the prompt.

### I3 — Make multi-call generation adaptive instead of always doing three full rounds
The loop at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:222` should stop once enough unique levers exist, or at least reduce later call size. Right now the code always asks for `5 to 7 MORE levers` at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:233`, even after a strong first call.

An adaptive policy would:

- stop after call 1 or call 2 when uniqueness is already good,
- cap the prior-name blacklist,
- normalize names before blacklist / dedup checks,
- restate option-quality requirements in later-call prompts.

That is the cleanest code-level response to the repeated llama3.1 later-call degradation and raw duplication regression.

### I4 — Make `OPTIMIZE_INSTRUCTIONS` executable, not just advisory
If `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:27` is intended as the policy source of truth, wire it into the system prompt assembly near `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:196` or add a test that checks the system prompt / schema descriptions / validators stay aligned with its known-problems list.

Right now the constant is helpful documentation for reviewers, but it does not constrain runtime behavior.

### I5 — Serialize runner instrumentation or isolate it per worker
Fix `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:96`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:106`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:108`, `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:114`, and `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:140` so the lock actually covers the whole region that depends on global state, or move usage / activity tracking into process-local state.

Without that, parallel prompt-optimizer runs produce unreliable telemetry even when the JSON outputs themselves are fine.

## Trace to Insight Findings

- **B1 → `insight_claude.md` N2 / N3.** The PR branch intentionally removes English-only checks, but because the replacement validator is only a length-and-brackets gate, it also stops enforcing the documented two-sentence tension/weakness structure. That explains why qwen3 and gpt-4o-mini can drift to `Balances ...`, `Encourages ...`, `Focuses ...`, and other shallow variants while still passing validation.
- **B2 → `insight_claude.md` N1 and `insight_codex.md` raw quality notes.** Label-only options persist because the code never validates the “full sentence with an action verb” requirement it advertises.
- **S2 + I3 → `insight_claude.md` N1 and `insight_codex.md` raw-duplication regression.** The failure is call-position-dependent, and the code’s fixed three-call loop plus growing name blacklist is a plausible root cause.
- **B3 + I5 → timing / evidence anomalies such as `insight_claude.md` N4.** I do not think this explains textual quality, but it can absolutely distort the run telemetry used to compare models and durations.
- **S1 → `insight_codex.md` “sibling checkout still shows the old validator/prompt.”** That observation is correct: the currently checked-out `main` tree is not the same contract as the PR branch that matches the run artifacts.
- **S3 + I4 → OPTIMIZE_INSTRUCTIONS alignment concern from the prompt.** The branch adds a policy constant, but because nothing consumes it, future drift is still easy.

## PR Review

I could not use `gh pr diff 299` in this offline environment, but the local branch `fix/review-brackets-and-i18n-validator` clearly contains the changes described in PR #299.

My read is:

1. **The PR does achieve two of its stated goals.** The branch removes the bracket-placeholder examples from the `review_lever` descriptions, relaxes the old English-only validator, and aligns `summary` with the one-sentence `Add ...` form. Those changes match the observed improvement in bracket leakage and summary formatting.
2. **The validator change overshoots.** Replacing `Controls` / `Weakness:` substring checks with a real structural validator would have been good, but the actual implementation at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:128` on the PR branch is too weak to preserve the documented review shape. That is a genuine regression in format control, even if it is an improvement for i18n.
3. **The PR does not touch the root cause of the llama3.1 option-quality failures.** Nothing in the branch adds an option-content validator, a later-call repair step, or an adaptive call loop, so the label-only-option problem is expected to persist.
4. **The new `OPTIMIZE_INSTRUCTIONS` work is only advisory.** Useful for analysis, but not yet runtime-enforced.
5. **Operationally, the review checkout is behind.** The `main` tree still contains the pre-PR contract, so anyone reading only `main` would draw the wrong conclusion unless they also inspect the PR branch.

Bottom line: **keep the PR’s direction, but tighten the implementation before calling it complete.** The i18n fix is worthwhile, but the current validator change is too permissive and leaves the review field under-specified.

## Summary

The most important code issue is not that PR #299 allows non-English reviews; that part is correct. The problem is that the replacement validator is so weak that it no longer enforces the branch’s own documented review structure.

The second major gap is older and still unresolved: option quality is specified in prose but never validated, which is why llama3.1 can keep emitting label-only options in later calls.

If I were ranking follow-up work, I would do this next:

1. strengthen `review_lever` validation without reintroducing English-only checks,
2. add an option-quality gate / repair path,
3. make the three-call loop adaptive,
4. fix runner concurrency so telemetry stays trustworthy,
5. make `OPTIMIZE_INSTRUCTIONS` part of the executable contract.
