# Assessment: Recover partial results when a lever generation call fails

## Issue Resolution

**PR #292 targeted**: When call 2 or 3 of the 3-call lever loop fails with a validator rejection
(or any other exception), all levers from prior successful calls were discarded. A single bad lever
caused total plan failure. The fix: if `len(responses) >= 1` when an exception fires, log a warning
and `break` instead of re-raising. If `len(responses) == 0` (call 1 failed), still raise — nothing
to recover.

**Is the issue resolved?** Yes, for the scenario the PR targets.

Direct evidence from two recovered plans:

- **llama3.1 gta_game**: Run 0/95 (before PR #292) — directory contains only
  `activity_overview.json` and `usage_metrics.jsonl`, 0 levers. Run 1/02 (after) — directory
  contains `002-10-potential_levers.json` with **7 levers**, all with valid
  `"Controls X vs. Y. Weakness: ..."` review format. Raw file
  (`002-9-potential_levers_raw.json`) has exactly **1 `strategic_rationale` entry**, confirming
  only call 1 succeeded and PR #292's partial recovery path fired for calls 2–3.

- **haiku silo**: Run 1/01 (before PR #292) — directory contains only `usage_metrics.jsonl`,
  0 levers (the `check_option_count` cascade from lever 7 having 7 options). Run 1/08 (after) —
  **23 levers**, high quality, raw file has **3 `strategic_rationale` entries** (all 3 calls
  succeeded; the editorial-commentary issue from run 1/01 did not recur, so partial recovery was
  available as a safety net but was not triggered).

**Residual symptoms (expected, by design):**

- llama3.1 still fails on 2/5 plans (silo, sovereign_identity in run 1/02) because call 1 itself
  hits the `check_review_format` validator — `len(responses) == 0` when the first call fails, so
  the error is still raised. This is the documented behavior of PR #292. The root cause is
  llama3.1's systematic non-compliance with the combined `review_lever` format (see New Issues).

- gpt-oss-20b hong_kong_game fails in run 1/03 with invalid JSON (not related to PR #292 or the
  validators).

---

## Quality Comparison

Models present in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, gemini-2.0-flash, haiku.

Before = runs 0/95–1/01 (analysis/13 "after" batch); After = runs 1/02–1/08 (this batch).
Note: gpt-4o-mini appears only in the after batch (run 1/06); gemini-2.0-flash appears in both.

| Metric | Before (0/95–1/01) | After (1/02–1/08) | Verdict |
|--------|---------------------|-------------------|---------|
| **Overall success rate** | 31/35 (88.6%) | 32/35 (91.4%) | IMPROVED (+1) |
| **Shared-model success rate** | 26/30 (86.7%) | 27/30 (90.0%) | IMPROVED (+1) |
| **Plans with 0 levers due to cascade** | 3 (0/95 silo+gta_game; 1/01 silo) | 1 (1/02 silo; still call-1 failures) | IMPROVED (−2 cascade failures) |
| **Plans recovered by partial recovery** | 0 | 2 (1/02 gta_game: 7 lvrs; 1/03 parasomnia: 12 lvrs) | IMPROVED |
| **Option count violations in artifacts** | 0 | 0 | UNCHANGED |
| **Review-format violations in artifacts** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 7/563 (1.2%) | 6/568 (1.1%) | UNCHANGED (within variance) |
| **Lever name uniqueness** | 563/563 (100.0%) | 568/568 (100.0%) | UNCHANGED |
| **Template leakage (Conservative:/Moderate:/Radical:)** | 20 cells (run 0/95) | 0 cells | IMPROVED (model variance; prompt unchanged) |
| **Missing Immediate→Systemic→Strategic chain** | 1/563 (0.2%) | 0/568 (0.0%) | UNCHANGED |
| **Missing measurable consequence** | 53/563 (9.4%) | 46/568 (8.1%) | IMPROVED slightly |
| **Consequences contaminated with review text** | ~71 (qwen3-dominated) | ~67% of qwen3 levers | UNCHANGED |
| **Avg option length (chars)** | 132.2 | 132.7 | UNCHANGED |
| **Avg review length (chars)** | 177.5 | 183.6 | UNCHANGED |
| **Total merged levers** | 563 | 568 | UNCHANGED (+5) |
| **Partial successful outputs (< 3 calls)** | 0 | 2 | NEW (intended behavior) |
| **Over-generation (haiku, >7 levers/call)** | haiku avg 21.0/plan | haiku avg 21.4/plan | UNCHANGED (informational; downstream dedup handles it) |
| **llama3.1 success** | 3/5 | 3/5 | UNCHANGED (different plans; gta_game recovered, sovereign_identity now fails) |
| **haiku success** | 4/5 | 5/5 | IMPROVED (+1; silo recovered) |
| **gpt-oss-20b success** | 4/5 | 4/5 | UNCHANGED (different plan fails: hong_kong_game vs parasomnia) |
| **gpt-5-nano success** | 5/5 | 5/5 | UNCHANGED |
| **qwen3 success** | 5/5 | 5/5 | UNCHANGED |
| **gemini-2.0-flash success** | 5/5 | 5/5 | UNCHANGED |

Note on gpt-4o-mini (after only, run 1/06): 5/5, 17–20 levers per plan, no validation issues.
Not included in shared-model comparison; recommend retaining in future test matrices.

---

## New Issues

### NI1 — Partial recovery is invisible to the event log and caller (observability gap)
The `break` in PR #292's exception handler exits silently. `runner.py` emits only
`run_single_plan_complete` / `run_single_plan_error` — no partial-recovery event. `outputs.jsonl`
records `"status": "ok"` for both full 3-call results and 1-call salvages.
The only audit mechanism is manually counting `strategic_rationale` entries in the raw file.
(code_claude B2; code_codex B4; insight_claude N5)

### NI2 — `break` after call-2 failure suppresses call-3 (opportunity loss)
When call-2 fails after call-1 succeeded, the `break` exits the loop and call-3 never runs.
Code_codex B5 confirms: a `continue` instead of `break` would let call-3 attempt, potentially
doubling recovered levers (e.g., gta_game could produce ~14 levers from calls 1+3 instead of 7
from call 1 alone). The name denylist for call-3 would be slightly shorter (call-2 names missing),
but downstream `DeduplicateLeversTask` handles any near-duplicates.

### NI3 — `activity_overview.json` inflated under parallel workers (data correctness)
Code_claude (B1) identifies that `_update_activity_overview` in `track_activity.py:207–252` has
no cross-plan thread-local guard, while `_record_file_usage_metric` already has one. With
`workers > 1` (all runs except llama3.1's workers=1: runs 1/03–1/08), every plan's
`activity_overview.json` accumulates token/cost data from all concurrent workers. Per-plan cost
attribution is incorrect by a factor of up to N workers. Not introduced by PR #292 but visible
in this batch.

### NI4 — llama3.1 call-1 failures remain structural (pre-existing, now prominent)
Two plans (silo, sovereign_identity) fail every llama3.1 run because call-1 itself hits
`check_review_format`. Run 1/02 shows 100% alternating Controls-only / Weakness-only levers on
call-1 for these plans. This is a pre-existing model compliance issue, not introduced by PR #292,
but now clearly the dominant remaining reliability problem.

---

## Verdict

**YES**: PR #292 resolves the CONDITIONAL from analysis/13 assessment. The partial recovery guard
eliminates total plan failures caused by call-2/3 validator rejections when prior calls succeeded.
Direct evidence: llama3.1 gta_game 0→7 levers; haiku silo 0→23 levers. No regressions introduced.
Overall success rate improves from 31/35 (88.6%) to 32/35 (91.4%). The combined state of
PR #289 + PR #292 is now correct: validators catch malformed levers, partial recovery preserves
earlier good results.

---

## Recommended Next Change

**Proposal**: Fix the `review_lever` prompt — replace the two-bullet instruction in both the
field `description` (`identify_potential_levers.py:51–58`) and the system prompt (section 4)
with a single combined example string showing both clauses in one field.

**Evidence**: Cross-agent consensus (insight_claude H1, insight_codex H1, code_claude S3/I4,
code_codex B1/S1). Run 1/02 (llama3.1, silo) shows 100% alternating pattern on call-1: every
lever has either `"Controls Resource Competition vs. Social Unrest."` or `"Weakness: The options
fa...ychological well-being."` — never both in the same field. The current prompt presents the
two clauses as separate bullet points, which weaker models interpret as two alternative formats.
Since call-1 has no prior responses to fall back on, this triggers the total plan failure that
PR #292 cannot recover from. All 2 remaining llama3.1 call-1 failures trace to this root cause.
The prompt file hash is unchanged between analysis/13 and analysis/14 (same sha256), confirming
no prompt change was made in PR #292.

**Verify**: After the prompt change, run llama3.1 for at least 2 runs (10 plans total).

- Check `events.jsonl` for llama3.1: `check_review_format` errors should decrease or disappear
  for silo and sovereign_identity. Target: 0 call-1 review_lever failures (was 7 violations each
  in runs 0/95, 1/02).
- Inspect resulting `002-10-potential_levers.json` for llama3.1: every lever's `review` field
  must contain both `Controls X vs. Y.` and `Weakness:` in the same string.
- Verify no regression for currently-passing models: gpt-5-nano, qwen3, gpt-4o-mini,
  gemini-2.0-flash, haiku should still produce 5/5 with valid review format.
- Measure whether the combined example causes review diversity to decrease (e.g., all models
  copying "fail to consider" verbatim). Check for template homogeneity in review fields.
- Also verify the registered prompt file (`prompts/identify_potential_levers/prompt_2_75f59ab...txt`)
  is updated, as `runner.py` reads the system prompt from disk (this file) when `--system-prompt-file`
  is passed. The in-code `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant is only used as
  fallback when no file is passed.

**Risks**:

- The combined example may become a template that smaller models (llama3.1, haiku) copy
  verbatim, producing low-diversity reviews with the same "fail to consider" phrasing. Watch for
  homogeneity in review fields across levers.
- llama3.1's non-compliance may be a model capability limitation rather than a prompt clarity
  issue; if the format failure is intrinsic, the prompt fix will not fully resolve the 3/5
  success rate. In that case, fallback options are: per-lever repair validator (code_codex I1) or
  treating llama3.1 as a non-conformant model for this step.
- The same prompt section also contains the `[Tension A]` / `[Tension B]` bracket placeholders
  in the example. If the fix adds a concrete example alongside these, the brackets may be
  reinforced. Best practice: show only one example with real text, no brackets.

**Prerequisites**: PR #292 must be merged (it is). No other prerequisites. This is a pure prompt
change with no schema or validator modifications.

---

## Backlog

### Resolved by PR #292 (remove from backlog):
- **B1/cascade (call-level rejection cascade)**: The core cascade bug — any LLM call failure
  discarding all prior accumulated levers — is resolved for call-2/3 failures. The CONDITIONAL
  from analysis/13 is fulfilled.

### Promoted to immediate priority (from deferred):
- **Prompt: two-bullet `review_lever` instruction** (was D2/D3 in synthesis/13, now Direction 1
  in synthesis/14): Root cause of all remaining llama3.1 call-1 failures.

### Still open (carried forward):
- **`break` vs `continue` for call-2 failures** (NI2 above): Very low effort, zero risk. Change
  one character at `identify_potential_levers.py:278`. Do in same PR as prompt fix.
- **Partial-recovery telemetry** (NI1 above): Add a structured event to `events.jsonl` when
  partial recovery fires. Low effort; makes future analysis machine-readable.
- **qwen3 consequence contamination**: ~67% of qwen3 levers copy review text into `consequences`.
  Post-parse repair validator recommended. Medium effort, no risk of cascade (repair, not reject).
- **`activity_overview.json` inflation under parallel workers** (NI3 above): One-line guard fix
  in `track_activity.py:207`. Corrects per-plan cost metrics for all `workers > 1` runs.
- **Prompt contradiction (conservative/moderate/radical)**: Prompt teaches "Show clear progression:
  conservative → moderate → radical" while prohibiting those labels. Responsible for template
  leakage bursts (20 cells in run 0/95). Bundle fix with the review_lever prompt change.
- **gpt-oss-20b rotating JSON failures**: Context-length sensitivity causing different plan to
  fail each run (sovereign_identity → parasomnia → hong_kong_game). Longer-term fix: prompt-length
  budgeting or pre-summary truncation before sending to the model.
- **Consequences contamination repair validator**: 71 levers across models have `consequences`
  ending with `"Controls … Weakness: …"` text. Add `@field_validator('consequences', mode='after')`
  that strips trailing review text.
- **Overflow telemetry**: Add a warning log when a raw call returns > 7 levers. Very low effort;
  makes over-generation visible without inspecting artifacts.
- **Per-lever non-fatal `review_lever` validator**: If the prompt fix does not fully resolve
  llama3.1 call-1 failures, escalate to replacing all-or-nothing `DocumentDetails` rejection with
  per-lever linting that allows valid siblings to survive a single malformed lever.
