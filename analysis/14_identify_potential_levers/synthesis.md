# Synthesis

## Cross-Agent Agreement

All four files (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

**PR #292 verdict: KEEP.** The partial-recovery change works as designed. Evidence is concrete: llama3.1 gta_game produces 7 levers instead of 0; haiku silo produces 23 levers instead of 0. No regressions introduced. Success rate improved from 31/35 (88.6%) to 32/35 (91.4%).

**Root cause of remaining call-1 failures: the two-bullet `review_lever` prompt.** All four files identify that the system prompt (section 4) and the field `description` present the `Controls ... vs. ...` and `Weakness: ...` clauses as separate bullet points. Weaker models (confirmed: llama3.1) interpret these as two alternative formats and alternate — producing Controls-only levers and Weakness-only levers in the same call. Since call-1 has no prior responses to fall back on, this triggers a total plan failure. Both H1 hypotheses (insight_claude, insight_codex) and S3/I4 (code_claude) and B1/S1 (code_codex) converge on this as the dominant remaining reliability issue.

**Partial-recovery telemetry is missing.** All four files flag the observability gap: the `break` exits silently, `runner.py` emits only `run_single_plan_complete` / `run_single_plan_error`, and `events.jsonl` records no partial-recovery event. The only audit mechanism is manually counting `"strategic_rationale"` entries in raw files. (insight_claude N5/C1; insight_codex C1; code_claude B2/I1; code_codex B4/I3.)

**qwen3 consequence contamination is real but orthogonal to the PR.** ~67% of qwen3 levers copy review_lever text verbatim into the `consequences` field. No validator or repair pass touches `consequences`. (insight_claude N4/H2; code_claude trace; code_codex B2.)

**gpt-oss-20b rotates JSON failures across plans — context-length sensitivity, not PR-related.** Three consecutive runs each fail on a different plan (sovereign_identity, parasomnia, hong_kong_game). Not caused by PR #292. (insight_claude N3/H3; code_codex S2.)

---

## Cross-Agent Disagreements

### Disagreement 1: Is the `break` after call-2 failure a bug (B5, code_codex) or correct design?

**code_codex (B5):** The unconditional `break` at line 278 means a call-2 failure silently suppresses call-3 entirely. A call-2 failure produces a 7-lever output (call-1 only) when a `continue` would let call-3 run and potentially yield 14 levers.

**code_claude:** Describes the `break` as correct, noting that the warning is emitted once and the behavior is acceptable given the PR intent.

**Source code verdict:** code_codex is factually correct about the behavior. Lines 227–278 show: if call_index=2 raises, `len(responses) >= 1`, so we `break` and call_index=3 never executes. Whether this is a bug depends on design intent. The PR description says "keep levers from prior successful calls" — it does not say "skip remaining calls." A `continue` instead of `break` would preserve call-1 results AND attempt call-3, at the cost of call-3 being slightly under-prompted (the call-2 names were not added to the denylist). This is a real improvement opportunity with negligible risk.

### Disagreement 2: Should the `review_lever` validator be made non-fatal per-lever (code_codex I1) or is a prompt fix sufficient?

**code_codex (I1):** Replace the all-or-nothing English-literal substring gate with a per-lever linter/repair path. Also cites `AGENTS.md:165-168` rule that validators must be language-agnostic.

**code_claude (I4/S3):** Frames the fix as a prompt change (add a combined example), not a validator redesign. Does not raise the language-agnostic rule.

**Source code verdict:** Both are complementary, not mutually exclusive. The prompt fix is lower risk and faster. Making the validator per-lever non-fatal is a larger refactor. The language-agnostic rule is worth noting but has not caused observed failures (all data is English). Prompt fix first, validator refactor later.

### Disagreement 3: `activity_overview.json` inflation (B1, code_claude only)

**code_claude (B1):** `_update_activity_overview` in `track_activity.py:207–252` has no cross-plan thread-local guard. Under parallel workers, every plan's activity_overview.json accumulates token/cost data from all workers simultaneously. The fix is one line (same guard as `_record_file_usage_metric`).

**code_codex:** Does not mention this bug.

**Source code verdict:** code_claude's analysis is credible. The guard in `_record_file_usage_metric` at track_activity.py:302–328 is explicitly absent from `_update_activity_overview`. This is a real data correctness bug for any run with `workers > 1` (runs 1/03 through 1/08 all use workers=4).

---

## Top 5 Directions

### 1. Fix the `review_lever` prompt — replace two-bullet instruction with a single combined example
- **Type**: prompt change (+ optional code change)
- **Evidence**: insight_claude H1, insight_codex H1, code_claude S3/I4, code_codex B1/S1 — full cross-agent consensus. Run 1/02: llama3.1 silo shows 100% alternating Controls-only / Weakness-only levers on call-1. All 2 remaining llama3.1 call-1 failures trace to this root cause.
- **Impact**: Potentially converts 2 llama3.1 call-1 failures per run to successes. Also benefits any other weaker model that encounters similar prompt misinterpretation. No other models currently fail on this, but the prompt hardening reduces fragility.
- **Effort**: low — change one section of the prompt file and field description in `Lever.review_lever`
- **Risk**: Model behavior change in the positive direction only. No schema change. The validator already enforces correctness; the fix targets compliance at generation time.

### 2. Change `break` to `continue` after call-2 failure to allow call-3 to run
- **Type**: code fix
- **Evidence**: code_codex B5, confirmed by source code reading (line 278 unconditionally exits the loop).
- **Impact**: When call-2 fails but call-1 succeeded, call-3 now runs. Best case: output doubles from 7 to ~14 levers (adding call-3's ~7 levers). Worst case (call-3 also fails): same result as today. The name denylist for call-3 will be slightly shorter (call-2's names missing), but downstream `DeduplicateLeversTask` handles any near-duplicates.
- **Effort**: very low — change `break` to `continue` at line 278. One character change.
- **Risk**: Low. If call-2 fails due to a structural model format issue, call-3 will likely also fail — partial recovery still catches it. No regression path exists.

### 3. Add partial-recovery telemetry to `events.jsonl` / `runner.py`
- **Type**: code change (observability)
- **Evidence**: insight_claude N5/C1, insight_codex C1, code_claude B2/I1, code_codex B4/I3 — full cross-agent consensus.
- **Impact**: Allows the analysis pipeline to count partial-recovery plans programmatically. Makes PR #292's activation visible without raw file inspection. Enables future monitoring and downstream policy (e.g., "plans with < 3 calls get flagged for review").
- **Effort**: low — in `runner.py`, check `len(result.responses) < 3` after `execute()` returns and emit a structured event.
- **Risk**: None. Additive change only. Does not affect generation behavior or artifact content.

### 4. Repair qwen3 consequence contamination — post-parse strip of trailing review text
- **Type**: code fix (validator/repair pass)
- **Evidence**: insight_claude N4/H2/C3, code_claude trace, code_codex B2/I2. Confirmed in data: ~67% of qwen3 levers in run 1/05 have `Controls ... Weakness: ...` text duplicated from `review_lever` into `consequences`.
- **Impact**: Cleans up ~10 of 15 levers per qwen3 plan. Prevents misleading consequence text from reaching downstream tasks. A repair pass (not rejection) avoids introducing new cascade failures.
- **Effort**: medium — add a `field_validator` on `consequences` that strips trailing `Controls [A] vs. [B].\s+Weakness:.*$` pattern. Needs careful regex to avoid over-stripping.
- **Risk**: Repair logic could strip valid consequence text if the model writes consequence text that incidentally starts with "Controls". Low probability but non-zero. Unit test with examples from run 1/05.

### 5. Fix `activity_overview.json` inflation under parallel workers
- **Type**: code fix (data correctness)
- **Evidence**: code_claude B1/I2. Source code: `_update_activity_overview` in `track_activity.py:207–252` lacks the cross-plan thread-local guard that `_record_file_usage_metric` already has.
- **Impact**: Corrects per-plan token/cost data in `activity_overview.json` for all runs with `workers > 1` (which is all runs except llama3.1's workers=1). Currently these files overcount costs by a factor of up to N workers.
- **Effort**: very low — one-line guard addition to `_update_activity_overview`, mirroring the existing guard in `_record_file_usage_metric`.
- **Risk**: None. The fix is strictly additive (early return when the handler is not the responsible plan). No change to generation behavior.

---

## Recommendation

**Pursue Direction 1 first: fix the `review_lever` prompt.**

**Why first**: It is the only change that directly addresses the remaining call-1 plan failures for llama3.1 (2/5 failure rate: silo, sovereign_identity). All other open issues — missing telemetry, qwen3 contamination, activity_overview inflation — are quality/observability improvements that do not change plan success rates. The prompt fix has the highest impact-to-effort ratio.

**What to change**:

1. **Field description** (`identify_potential_levers.py:51–58`): Replace the two-bullet format with a single combined example:
   ```python
   review_lever: str = Field(
       description=(
           "Required format: Two sentences in a single field. "
           "Example: 'Controls centralization vs. local autonomy. "
           "Weakness: The options fail to account for transition costs.' "
           "The 'Controls [A] vs. [B].' sentence MUST come first, "
           "followed immediately by the 'Weakness: ...' sentence. "
           "Both sentences are mandatory in every response."
       )
   )
   ```

2. **System prompt** (`identify_potential_levers.py:178–181`, section 4 `review_lever` bullets): Replace the two separate bullet points with a single combined instruction:
   ```
   - For `review_lever` (one field, two sentences, in this order):
     "Controls [Tension A] vs. [Tension B]. Weakness: The options fail to consider [specific factor]."
     Both clauses are mandatory in every response, in this exact order, in one field.
   ```

3. **Registered prompt file** (`prompts/identify_potential_levers/prompt_2_75f59ab...txt`): Apply the same consolidation to the Validation Protocols section (section 4). The runner reads this file from disk (`runner.py:436–459`); the in-code `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant is only used when no `--system-prompt-file` is passed.

**Expected outcome**: Reduce llama3.1 call-1 failures from 2/5 to 0–1/5 by clarifying that both clauses belong in the same field. The fix is a prompt change only — no schema, validator, or call structure is modified.

---

## Deferred Items

**Direction 2 (change `break` to `continue`)**: Very low effort and zero risk. Should be done in the same PR as the prompt fix or immediately after. The gta_game case would have produced ~14 levers instead of 7 with this change.

**Direction 3 (partial-recovery telemetry)**: Also low effort. Should be added to make future analysis machine-readable instead of requiring raw-file inspection. Does not affect success rates.

**Direction 4 (qwen3 consequence repair)**: Medium effort. Cosmetic improvement only — qwen3 currently produces 5/5 successful plans. Address after the high-priority reliability items.

**Direction 5 (activity_overview.json guard)**: One-line fix. Corrects silent data corruption in cost metrics for parallel runs. Should be done but does not affect plan success rates.

**gpt-oss-20b JSON failures (S2 / insight N3)**: Rotating per-plan context-length failures. Longer-term fix: prompt-length budgeting or pre-summary truncation before sending to the model (code_codex I6). Not actionable until the higher-priority prompt/code fixes are in place.

**Per-lever non-fatal `review_lever` validator (code_codex I1)**: Larger refactor — replace the all-or-nothing `DocumentDetails` rejection with per-lever linting that allows a batch to succeed even if some levers have malformed reviews. High value if the prompt fix (Direction 1) doesn't fully resolve llama3.1 call-1 failures. Attempt after observing the prompt fix's effect.

**`check_review_format` clause-ordering check (code_claude I3/S2)**: Add `ctrl_pos > weak_pos` ordering check. Low priority — no observed failures from out-of-order clauses. Correctness hardening, not urgency.

**gpt-4o-mini retention (insight_claude Q5)**: Run 1/06 showed 5/5 with 17–20 levers and no validation issues. Retain in future test matrices as a cost-effective alternative to gemini-2.0-flash.
