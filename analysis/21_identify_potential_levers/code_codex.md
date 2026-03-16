# Code Review (codex)

## Bugs Found

- **B1 — PR #313 leaves the dominant fabrication path untouched: call 1 gets no extra grounding reminder.** In `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:266-277`, call 1 still uses `prompt_content = user_prompt`, while the new anti-fabrication sentence is added only in the `else` branch at `:274-275`. That means the first 5–7 levers in every run are still generated without the new reminder, which matches the insight finding that the surviving `%`/currency fabrications are showing up in `responses[0]`.

- **B2 — Partial-call failures are silently reported as successful runs.** In `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:300-319`, any exception after at least one successful call is swallowed and the loop continues, but the returned object at `:353-359` contains no `partial` flag, failed call index, or error IDs. Then `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:123-129` returns `status="ok"` whenever any cleaned output is saved, and `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:302-311` logs `run_single_plan_complete` with no hint that one of the three calls failed. This exactly explains the audited pattern of raw files with only 2 responses and no `LLMChatError` visibility in `events.jsonl`.

- **B3 — The “complete strategic sentence” rule is not validated, so slogan-like options pass unchanged.** The PR branch says options must be full strategic approaches in `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:88-90`, and the follow-up prompt repeats that at `:272-275`, but the only implemented validator at `:115-126` checks option count only. There is no minimum word count, sentence check, or action-verb check. This is a direct code-level explanation for the run-53 relapse where 3–4 word labels like “Deploy AI-driven monitoring” were accepted as valid options. It also violates the branch’s own `OPTIMIZE_INSTRUCTIONS` warning against “a slogan” outputs at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:58-68`.

## Suspect Patterns

- **S1 — Cross-call dedup is name-only, not concept-aware.** Follow-up calls blacklist only previously generated names in `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270-276`, and the post-merge cleanup skips only exact duplicate names at `:330-337`. That design will stop literal name reuse, but it will not stop semantic near-duplicates with slightly different phrasing. This is a plausible source for the repeated festival/sound-design lever families called out in the insight files.

- **S2 — Optimizer metadata cannot distinguish system-prompt changes from code-only prompt tweaks.** `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:347-363` records only `system_prompt_sha256` plus model/system info. PR #313 changes inline follow-up user-prompt text in code, not the registered system prompt, so before/after runs naturally keep the same SHA even though the effective prompt changed. This does not create bad levers by itself, but it weakens experiment observability and made this PR harder to audit from `meta.json` alone.

## Improvement Opportunities

- **I1 — Apply the anti-fabrication reminder to call 1 too, and make the failure mode explicit.** The highest-leverage fix is to mirror the new follow-up reminder into the call-1 branch at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267-275`. I would make it more specific than the current generic sentence: explicitly forbid deriving allocation percentages from a total budget and inventing stricter thresholds from a supplied range.

- **I2 — Add a numeric-grounding audit before saving cleaned output.** The source plan text is already available as `user_prompt` from `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:56-66`, and `IdentifyPotentialLevers.execute()` already has both the source text and the cleaned lever objects in hand at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:325-359`. A lightweight validator can extract `%`/currency tokens from lever text, compare them against the source text, and at minimum emit warnings plus raw metadata. That would catch the exact unsupported-budget-split and invented-threshold failures the insight files found.

- **I3 — Enforce option quality in code, not just in prose.** Extend the existing options validator at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:115-126` so it rejects obviously label-like options: e.g. fewer than N words, no verb, or no terminal punctuation. If hard rejection feels too expensive, normalize this into a soft quality gate that records warnings and marks the run as partial-quality.

- **I4 — Persist partial-call telemetry in both raw JSON and `events.jsonl`.** The code already knows which call failed inside `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:300-319`, but it throws that information away before returning at `:353-359`. Add fields like `completed_calls`, `failed_call_indices`, and `error_ids`, and have `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:302-311` emit a distinct `run_single_plan_partial` event instead of a misleading clean success.

- **I5 — Persist the effective per-call prompt or at least its hash, plus the code revision.** The actual follow-up prompt is assembled dynamically at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270-276`, but the runner metadata at `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:347-363` stores only the system prompt hash. Recording per-call prompt hashes and the git commit would make PRs like #313 auditable from artifacts instead of requiring source checkout archaeology.

## Trace to Insight Findings

- **B1 → fabricated percentages/dollar amounts still appearing after the PR.** This is the code-level explanation for `insight_claude.md` N1/N2/N3 and the matching unsupported-number findings in `insight_codex.md`: the PR reminder only executes for calls 2/3, while several of the audited bad levers were generated in call 1.

- **B2 → silent 2-response raw files with no logged LLM error.** This maps directly to the `insight_codex.md` observation that several after-run raw artifacts contain only 2 responses even though the audited `events.jsonl` files show no `LLMChatError` entries.

- **B3 → short-option relapse in run 53.** The code currently trusts prompt wording instead of validating option quality, so a model that ignores the reminder can still ship 3-word or 4-word labels. That matches the `insight_codex.md` short-option regression.

- **S1 → near-duplicate lever families.** Name-only dedup is a plausible source for the `insight_claude.md` note about repeated “Festival Strategy” / “Sound Design” levers that differ mostly in framing.

- **S2 / I5 → harder PR assessment than necessary.** The insight files note that the system-prompt SHA stayed identical before/after. The runner code explains why: this PR changes code-built user prompts, and that change is not fingerprinted anywhere in the run metadata.

## PR Review

- **Implementation vs. intent:** The commit itself is mechanically correct. It inserts the new sentence at the intended attention-decay point, immediately after the name blacklist in follow-up calls, at `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:272-276`. I do not see a prompt-ordering bug, duplicated user message, or chat-history corruption in the diff.

- **Main gap:** The change is too narrow for the failure mode it targets. Because `/Users/neoneye/git/PlanExeGroup/PlanExe/.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:267-268` leaves call 1 untouched, the PR cannot fix the raw-artifact cases where unsupported numbers are generated in `responses[0]`. That is the biggest reason the measured improvement is small and model-dependent.

- **Secondary gap:** The PR is still prompt-only. There is no corresponding validator for unsupported numeric claims, so even calls 2/3 can ignore the reminder with no consequence. The same pattern already shows up in option quality: the reminder exists, but without validation the model can still emit shallow labels.

- **Observability gap remains:** The PR does not touch `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, so partial-call loss is still reported as clean success, and the run metadata still cannot fingerprint code-only prompt changes.

- **Verdict:** **CONDITIONAL keep.** The change is low-risk and directionally correct, but it is not a complete fix for the targeted issue. I would keep it only together with a follow-up patch that covers call 1 and adds numeric/partial-run telemetry.

## Summary

- The strongest confirmed root causes are: **call-1 coverage gap**, **silent partial-call success reporting**, and **missing option-quality validation**.
- The PR itself is assembled correctly, but it only addresses one of the three call sites and relies entirely on model obedience.
- The next patch should add the reminder to call 1, add a numeric-grounding audit, and expose partial-call failures in artifacts and events.
