# Code Review (claude)

## Bugs Found

**B1 — Misleading `partial_recovery` warning condition**
`runner.py:131`

```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} succeeded")
```

The comment directly above (lines 128-130) says *"A 2-call success is normal for models that produce 8+ levers per call."* But the condition fires at `actual_calls < 3`, which includes `actual_calls == 2` — exactly the case the comment calls normal. The condition should be `< 2` to match the intent. As written, a healthy 2-call run emits a misleading `partial_recovery` warning and then also triggers an `partial_recovery` event in `events.jsonl` (runner.py:577-583) which the analysis pipeline may interpret as a failure sign.

**B2 — Case-sensitive lever deduplication**
`identify_potential_levers.py:368`

```python
if lever.name in seen_names:
```

`seen_names` is a plain Python `set`. Two levers whose names differ only in capitalisation (e.g., `"Market Positioning"` vs `"Market positioning"`) pass through as distinct levers and are both forwarded to the downstream deduplication step. Small models that inconsistently capitalise names can produce more near-duplicates than expected, increasing token cost in the next step.

**B3 — `LeverCleaned.consequences` description silently diverges from `Lever.consequences`**
`identify_potential_levers.py:209-215`

`LeverCleaned` is documented as "never sent to an LLM" (line 196), so its field descriptions are documentation-only. However, the `consequences` and `options` descriptions in `LeverCleaned` are verbatim copies of those in `Lever`. When the `Lever` field descriptions are updated (as PR #471 did), the `LeverCleaned` copies must be manually kept in sync. There is no test or comment enforcing this. The PR #471 update did maintain sync, but there is no structural guarantee against future drift. Not a runtime bug, but a maintenance trap.

## Suspect Patterns

**S1 — Dispatcher event handler cross-contamination under parallel execution**
`runner.py:248-250`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

When `workers > 1`, multiple threads add their own `TrackActivity` handlers to the shared LlamaIndex dispatcher. Because all registered handlers receive all events from all threads, each plan's `TrackActivity` instance accumulates events from every concurrently running plan, not just its own. The lock covers setup/teardown atomicity, not the execution window. In practice the contaminated data is discarded — `track_activity_path.unlink(missing_ok=True)` (line 283) deletes the file before `_maybe_generate_activity_overview` reads from `usage_metrics.jsonl` instead. The final per-plan output is therefore correct, but any logic that relies on `track_activity.jsonl` during execution would be incorrect. The pattern is fragile and should be noted.

**S2 — `review_lever` minimum length of 10 chars is extremely permissive**
`identify_potential_levers.py:173`

The validator enforces `len(v) >= 10`. A 10-character string (e.g. `"Too risky."`) passes validation and would be meaningless as a critical review. The comment says "50 chars is the soft target but not enforced here." Given that the `enrich_potential_levers` step depends on the quality of the `review` field, letting 10-char placeholders pass silently could degrade enrichment quality. The soft target is never enforced anywhere in the pipeline.

**S3 — `strategic_rationale` description contains prescriptive sentence instructions**
`identify_potential_levers.py:185`

```python
description="A concise strategic analysis (around 100 words) of the project's core tensions
and trade-offs. This rationale must JUSTIFY why the selected levers are the most critical
levers for decision-making. For example, explain how the chosen levers navigate the
fundamental conflicts between speed, cost, scope, and quality."
```

`OPTIMIZE_INSTRUCTIONS` warns that field descriptions containing structural phrases cause template lock. The phrase `"For example, explain how the chosen levers navigate the fundamental conflicts between speed, cost, scope, and quality"` names a specific example domain (speed/cost/scope/quality) that small models copy verbatim. Because `strategic_rationale` is chain-of-thought (not passed downstream), template lock here only wastes tokens, but it may crowd out the model's genuine reasoning when context is limited.

## Improvement Opportunities

**I1 — Sync `LeverCleaned` descriptions automatically**
`identify_potential_levers.py:195-224`

Extract the shared `consequences` and `options` field descriptions into module-level string constants (e.g. `_CONSEQUENCES_DESCRIPTION`, `_OPTIONS_DESCRIPTION`) and reference them from both `Lever` and `LeverCleaned`. This makes PR-style description changes a single-point edit and eliminates the copy-paste drift risk (see B3).

**I2 — Harden `check_review_format` minimum length**
`identify_potential_levers.py:173`

Raise the structural minimum from 10 to 40 characters. The system prompt already requires "one sentence (20–40 words)"; 40 characters is the minimum character count for 20 words at average word length. This aligns the validator with the system prompt's stated constraint and rejects low-quality outputs earlier rather than passing them to downstream steps.

**I3 — Fix the `partial_recovery` warning threshold**
`runner.py:131`

Change the condition to `if actual_calls < 2:` (or remove the `_run_levers`-level warning entirely, since `events.jsonl` already captures `partial_recovery` at runner.py:577). As written, a normal 2-call run triggers a spurious warning that analysis tooling may flag as an anomaly.

**I4 — Make `min_levers` a parameter of `execute()`**
`identify_potential_levers.py:291`

`min_levers = 15` is hardcoded inside the method. Exposing it as an optional parameter with default 15 allows callers (including the self-improve runner) to tune the target without patching the source. This is especially useful for rapid experimentation.

**I5 — Case-normalise seen_names in the deduplication guard**
`identify_potential_levers.py:365-369`

Change to `lever.name.lower()` lookup and insertion so capitalisation variants are caught before the downstream DeduplicateLeversTask. Preserve the original casing in `LeverCleaned.name`.

## Trace to Insight Findings

The insight file for this run reported a timeout (`Claude Code exceeded the 1200s time limit`), so no quality observations are available from the insight. Based on the code review:

- **B1** (misleading warning) would cause the analysis pipeline to emit false-positive `partial_recovery` events even on clean runs, potentially making healthy models appear partially degraded.
- **B2** (case-sensitive dedup) could add extra near-duplicate levers that inflate token cost in subsequent steps, contributing to slow or timed-out runs when models produce many variants.
- **S1** (dispatcher contamination) is a background correctness concern for parallel runs; it does not explain a timeout directly.
- **S2** (permissive review_lever minimum) could allow very short, low-quality reviews through, degrading downstream enrichment quality — but would not by itself cause a timeout.
- The timeout is most likely a model-level or infrastructure issue, not a code bug in these files; no code-level root cause can be confirmed from the available evidence.

## PR Review

**PR #471 — Replace negative-priming prohibition with positive framing in `consequences` field**

**What the PR changes**: Removes the explicit prohibition `"Do NOT include 'Controls ... vs.', 'Weakness:'"` from the `consequences` field description in both `Lever` and `LeverCleaned`, replacing it with the positive directive `"Focus on cause-effect relationships and factual outcomes; save critical assessments for the review_lever field."`.

**Does the implementation match the intent?** Yes. The change is applied consistently in both models. The PR correctly applies the principle documented in `OPTIMIZE_INSTRUCTIONS` lines 82-83: *"Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."*

**Effect scope**: The change to `Lever.consequences` (line 112-119) directly affects LLM output because `Lever` is the schema used with `as_structured_llm`. The change to `LeverCleaned.consequences` (lines 209-215) has **no effect on LLM behaviour** since `LeverCleaned` is never sent to an LLM (documented at line 196). The `LeverCleaned` change is documentation alignment, not functional.

**Gaps and edge cases**:

1. **Mild template-lock risk in the replacement text.** The phrase "cause-effect relationships" is a memorable noun phrase that could itself become a boilerplate opener ("This lever creates cause-effect relationships..."). It is substantially less risky than naming the exact banned phrases, so the PR is an improvement, but the field description is not fully neutral prose.

2. **`LeverCleaned` change is cosmetic only.** The PR description presents this as a dual-model fix, which is accurate but may give a false impression of double impact. Only the `Lever` change matters for LLM output quality.

3. **System prompt is untouched.** Section 2 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (runner.py lines 234-238) also describes `consequences` quality. That text does not currently contain prohibitory language, so no corresponding system-prompt change is needed. If the system prompt is updated later and re-introduces a prohibition for `consequences`, the PR's benefit would be partially undone.

4. **Small-model coverage.** For the very weakest models (e.g. 3B parameter quantised models), Pydantic field descriptions in the JSON schema have weaker influence than the system prompt. The fix targets the field description, which is the right place for mid-tier models; very small models may still need a reinforcing change in the system prompt.

**Overall verdict**: The PR is correct, safe, and aligned with documented best practices. The functional improvement is limited to `Lever.consequences`; the `LeverCleaned` change is harmless housekeeping. No new bugs are introduced.

## Summary

| ID | Type | Severity | Location | One-line description |
|----|------|----------|----------|----------------------|
| B1 | Bug  | Medium   | runner.py:131 | `actual_calls < 3` warns on normal 2-call runs; should be `< 2` |
| B2 | Bug  | Low      | identify_potential_levers.py:368 | Case-sensitive dedup misses capitalisation variants |
| B3 | Bug  | Low      | identify_potential_levers.py:209-215 | `LeverCleaned` descriptions copy-pasted; no structural sync guarantee |
| S1 | Suspect | Low   | runner.py:248-250 | Dispatcher handler contamination under parallel workers |
| S2 | Suspect | Low   | identify_potential_levers.py:173 | `review_lever` min length 10 chars too permissive |
| S3 | Suspect | Low   | identify_potential_levers.py:185 | `strategic_rationale` description names a domain example (speed/cost/scope) |
| I1 | Improvement | — | identify_potential_levers.py:195-224 | Extract shared field descriptions as named constants |
| I2 | Improvement | — | identify_potential_levers.py:173 | Raise `review_lever` minimum to 40 chars |
| I3 | Improvement | — | runner.py:131 | Fix partial_recovery threshold to `< 2` |
| I4 | Improvement | — | identify_potential_levers.py:291 | Expose `min_levers` as a parameter |
| I5 | Improvement | — | identify_potential_levers.py:368 | Case-normalise the deduplication guard |

The most actionable fix is **B1** — the `< 3` threshold emits false-positive `partial_recovery` events on healthy 2-call runs, polluting the self-improve analysis signal. **PR #471** is sound and should be merged; its primary benefit is eliminating the template-leakage risk for `consequences` in mid-tier models.
