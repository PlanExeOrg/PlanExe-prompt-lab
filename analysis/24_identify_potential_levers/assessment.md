# Assessment: fix: remove unused summary field, slim call-2/3 prefix

## Issue Resolution

**What PR #334 was supposed to fix:**

1. Remove `DocumentDetails.summary` — a required Pydantic field never used downstream
2. Remove the matching summary validation section from the system prompt
3. Add "at least 15 words with an action verb" to system-prompt section 6 for uniform
   enforcement across all three calls
4. Slim the call-2/3 user prefix by removing duplicate quality/anti-fabrication reminders

**Verification against current code (`identify_potential_levers.py`):**

| Claim | Code state | Location |
|-------|-----------|----------|
| Remove `DocumentDetails.summary` field | **NOT DONE** | Line 164: `summary: str = Field(...)` still present, still required |
| Remove summary prompt section | **NOT DONE** | Lines 232–234: `- For \`summary\`:` sub-section still present |
| Add 15-word floor to section 6 | **NOT DONE in section 6** | Line 243–246: section 6 has no word-count constraint; constraint exists only in call-2/3 prefix (line 283) |
| Slim call-2/3 prefix | **DONE** | Lines 281–285: compact prefix with names list, 15-word reminder, no-fabrication reminder |

**Residual symptoms:** Every LLM call on every plan still generates a `summary` string that is immediately discarded. The required field means any response that omits `summary` fails full Pydantic validation and must be retried. Token waste and validation risk from B1/B2 persist unchanged.

---

## Quality Comparison

**Shared models in both batches:**
- llama3.1 (run 60 ↔ run 75)
- qwen3 (run 63 ↔ runs 76–78)
- gpt-4o-mini (run 64 ↔ run 79)
- gemini (run 65 ↔ run 80)
- haiku (run 66 ↔ run 81)

**Models only in "before" (analysis 22):** gpt-oss-20b (run 61), gpt-5-nano (run 62)

**Important context:** Between analysis 22 (PR #316, runs 60–66) and analysis 24 (PR #334,
runs 75–81), intermediate PR #326 also merged. PR #326 added a second review_lever
example and fixed B1/B2 from analysis 22 (Lever.review_lever Pydantic description +
IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT). Quality improvements that appear between
analysis 22 and analysis 24 are therefore not all attributable to PR #334.

| Metric | Before (runs 60–66) | After (runs 75–81) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate — llama3.1** | 13/15 calls_succeeded (run 60: 2 partial_recovery, 0 full errors) | 1 full error (hong_kong_game, ReadTimeout) + 2 partial_recovery (run 75) | REGRESSED |
| **Success rate — qwen3** | 15/15 (run 63) | ~14.3/15 avg (runs 76/77: 5/5; run 78: 4/5, parasomnia ValueError) | SLIGHT REGRESSION |
| **Success rate — gpt-4o-mini, gemini, haiku** | 15/15 each (runs 64–66) | 15/15 each (runs 79–81) | UNCHANGED |
| **"Weakness:" contamination in consequences** | 0% (fixed by PR #316) | 0% | UNCHANGED |
| **Review template lock — llama3.1** | ~100% "This lever governs the tension between…" (run 60) | ~100% "This lever governs the tension between…" (run 75) | UNCHANGED (vs analysis 22 baseline); **REGRESSED** vs intermediate PR #326 state where 29% used second example |
| **Second review example present (llama3.1)** | 0% (single example in runs 60–66) | 0% in run 75 | UNCHANGED vs analysis 22; **REGRESSED** vs PR #326 state (29%) |
| **Verbatim example copy** | 1 case (run 60 gta_game Location Strategy — exact match to prompt example) | 0 cases confirmed across runs 75–81 | IMPROVED |
| **Bracket placeholder leakage** | Not found in sampled outputs | Not found | UNCHANGED |
| **Option count violations** | 0 (hard validator rejects != 3 options) | 0 | UNCHANGED |
| **Lever name uniqueness** | Near-duplicates present (run 60 gta_game: "Partnership Model" / "Partnership Structure" / "Partnership Ecosystem") | Not explicitly measured for after batch | NOT MEASURED |
| **Content depth — avg option length (llama3.1 silo)** | ~113 chars (run 60) | ~110 chars (run 75) | UNCHANGED |
| **Content depth — avg consequence length (llama3.1 silo)** | ~150 chars (run 60) | ~174 chars (run 75) | UNCHANGED (1.16× — below 2× warning) |
| **Field length ratio vs baseline** | Consequences ~1.1×, review ~1.1× baseline | Same order (~0.9–1.1×) | UNCHANGED |
| **Fabricated quantification (% claims)** | 0 in matched models | 0 in matched models | UNCHANGED |
| **Marketing-copy language** | Not measured systematically | Not measured systematically | NOT MEASURED |
| **Cross-call lever name duplication** | Present (case-sensitive dedup only) | Present (case-sensitive dedup only) | UNCHANGED |
| **Over-generation count** | 17–21 levers per run (informational) | 16–21 levers per run (informational) | UNCHANGED — downstream DeduplicateLeversTask handles extras |
| **Review diversity — qwen3** | Not measured (run 63 not analyzed) | "Core tension:" dominant opener (runs 76–78) — model-native template | NEW ISSUE (see §C) |
| **"at least 15 words" uniform enforcement** | Call-2/3 only (misplaced before PR) | Call-2/3 only (unchanged; PR claimed section 6) | UNCHANGED |
| **Two review examples in Pydantic + system prompt** | No (single example; PR #316 state) | Yes (added by intermediate PR #326) | IMPROVED (not by PR #334) |
| **summary field token waste** | Required field, tokens wasted per run | Still required, tokens still wasted | UNCHANGED (PR #334 did not execute this) |

**Summary:** For strong models (haiku, gemini, gpt-4o-mini) the PR is neutral — no regressions, no improvements. For llama3.1 there is a slight reliability regression (first full error on hong_kong_game) and no recovery of review diversity. The second review example that peaked at 29% under PR #326 returned to 0% under PR #334, indicating the call-2/3 prefix slim removed implicit reinforcement that the weaker model relied on.

**OPTIMIZE_INSTRUCTIONS alignment:** The current `OPTIMIZE_INSTRUCTIONS` (lines 27–73) documents single-example template lock at lines 69–72 — correctly updated by an intermediate commit. It does NOT yet document model-native template patterns (qwen3's "Core tension:" opener). The PR #334 changes do not add or remove OPTIMIZE_INSTRUCTIONS content, so alignment is unchanged from the intermediate state.

---

## New Issues

**N1. qwen3 model-native "Core tension:" template (not covered by OPTIMIZE_INSTRUCTIONS).**
Runs 76–78 (qwen3) consistently open reviews with "Core tension: X." — a phrase absent from
both review_lever examples in the prompt. This is not prompt-driven template lock; it is a
model-native output pattern from qwen3-30b-a3b. OPTIMIZE_INSTRUCTIONS warns about
prompt-example-driven lock but not model-native lock. A negative constraint ("Do not open
with 'Core tension:'") would be needed to address this.

**N2. qwen3 run 78 parasomnia JSON extraction failure (ValueError).**
`history/1/78_identify_potential_levers/events.jsonl` records `ValueError: Could not extract
json string from output` for parasomnia_research_unit (duration 67.91s). This failure type
was not seen in run 63 (qwen3, before). It may trace to qwen3's `<think>` reasoning tokens
leaking into the JSON output, or to the hard validator rejecting a response where one lever
had != 3 options. Not definitively caused by PR #334.

**N3. llama3.1 review diversity regression relative to PR #326 peak.**
The intermediate PR #326 state (run 67) showed 29% of llama3.1 silo reviews using the second
example ("Prioritizing speed over reliability carries hidden costs: none of the options address
rollback complexity."). Run 75 (PR #334) shows 0% — a return to the analysis 22 baseline. The
plausible cause: the call-2/3 prefix previously contained content that reinforced or echoed the
second example; the prefix slim removed it. This is a latent regression that went undetected
because it was masked by the improvement from PR #326.

**Latent issue surfaced: B1+B2 never executed.** The code review confirms that the summary
field and its system-prompt instructions remain in place despite PR #334's stated removal. Any
future analysis that assumes the token savings have materialized will be incorrect.

---

## Verdict

**CONDITIONAL**: The PR's primary engineering goal (removing the unused `summary` field and
its system-prompt instructions) was not executed. The field remains required at line 164,
consuming tokens on 3 calls × 5 plans = 15 summary generations per run that are silently
discarded. The one change that did land — slimming the call-2/3 prefix — is neutral for
strong models and caused a measurable regression in review diversity for llama3.1 (second
example dropped from 29% in the intermediate PR #326 state to 0%). Accept this PR only after:
(1) completing the summary field removal (delete `summary: str = Field(...)` at line 164 and
the matching prompt sub-section at lines 232–234), and (2) verifying whether the call-2/3
prefix slim was the cause of the llama3.1 second-example regression — if confirmed, restore
a reference to the second example in the call-2/3 prefix or add a negative constraint against
the first-example opener.

---

## Recommended Next Change

**Proposal:** Complete summary field removal (B1 + B2): delete `DocumentDetails.summary: str`
from the Pydantic schema (line 164) and delete the matching `- For \`summary\`:` sub-section
from the system prompt (lines 232–234). Both must be removed atomically — leaving either in
place wastes tokens or confuses models. The code change is three mechanical line deletions with
zero downstream risk (confirmed by source inspection: `lever_item_list()`, `save_clean()`, and
all downstream tasks never read `summary`).

**Evidence:** Code review B1/B2 confirm the field is present and required at line 164; system
prompt lines 232–234 confirm the dead instructions remain. The insight treats P4 ("summary
removal is unambiguous positive") as correct in intent but notes it was not executed. Every
7-run experiment wastes 105 summary generations (7 runs × 3 calls × 5 plans). Future batches
multiply this waste. Zero confirmed negative side effects from removing the field.

**Verify in the next iteration:**
- Confirm `summary` field is absent from `002-9-potential_levers_raw.json` files — a single
  grep for `"summary":` in raw output files should return zero matches.
- Confirm no Pydantic validation errors increased after removal — check events.jsonl
  across all model runs for new `LLMChatError` events on plans that previously succeeded.
- Spot-check haiku (run 81 equivalent) and qwen3 outputs: if removing the summary field
  changes the token budget available to levers, option/consequence lengths may shift slightly.
  Verify average option length stays in the 100–160 char range.
- For llama3.1, re-run on silo and gta_game and check whether the 15-word option floor
  (call-2/3 only) changes behavior now that summary tokens are freed — or whether llama3.1
  still produces short-label options on call 1.

**What could go wrong:**
- If any model (particularly small models like llama3.1) was using the `summary` field as a
  "planning scratch pad" that improved its lever quality, removal might slightly degrade lever
  depth for that model. The risk is low — there is no evidence `summary` text correlates with
  lever quality — but the first run after removal should sample lever depths.
- The system-prompt section 4 currently lists both `review_lever` and `summary` sub-sections.
  After deleting the `summary` sub-section, verify that the remaining `review_lever` sub-section
  is still structurally intact and that no surrounding blank lines or headers become orphaned.
- Run 78 (qwen3, ValueError) may reappear with or without this change. It is not caused by the
  `summary` field. Watch for ValueError in qwen3 parasomnia runs in the next batch.

**Prerequisite issues:** None. B1+B2 are self-contained and do not depend on any other fix.
They should precede the template-lock negative constraint (Direction 2) so that subsequent
experiments are interpreted against a cleaner baseline.

**After B1+B2: Direction 2 — add negative constraint against "This lever governs the tension
between" opener.** This is the single highest-leverage change for reducing template lock in
llama3.1 and benefits all models. Append to the `review_lever` field description and/or system
prompt section 4:
> `Do NOT open with "This lever governs the tension between". Name the specific trade-off directly.`

Also add a companion negative constraint for qwen3's "Core tension:" opener (I2 from code
review) and document model-native template patterns in OPTIMIZE_INSTRUCTIONS (I3).

---

## Backlog

**Items resolved since analysis 22 (can be removed):**
- ~~B1 (analysis 22): Lever.review_lever Pydantic field description still used old two-sentence
  format~~ — Fixed by intermediate PR #326. Current code (lines 96–107) has two structurally
  distinct examples.
- ~~B2 (analysis 22): IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT still used old format~~ — Fixed
  by intermediate PR #326. System prompt section 4 (lines 226–231) now has two examples.
- ~~Single-example template lock not in OPTIMIZE_INSTRUCTIONS~~ — Added. Lines 69–72 document
  this known problem.

**Carry-forward (unresolved from analysis 22):**
- Label-style options validator (C2 / I1 from analysis 22): No validator added for options
  < ~25 chars with no verb. llama3.1 still produces label-style options on call 1 for plans
  like gta_game. Medium priority.
- Near-duplicate lever names (case-sensitive dedup only): "Partnership Model" / "Partnership
  Structure" / "Partnership Ecosystem" type near-duplicates still pass through to downstream
  DeduplicateLeversTask. Low priority.

**New items added from analysis 24:**
- **[HIGH] B1+B2 (summary field):** `DocumentDetails.summary: str` required but never used.
  Delete field and matching system-prompt sub-section (lines 232–234). Unexecuted PR #334 goal.
- **[HIGH] I1: Negative constraint against "This lever governs the tension between" opener.**
  100% template lock in run 75 (llama3.1). Append to review_lever description and/or section 4.
- **[MEDIUM] I2+I3: Negative constraint for qwen3 "Core tension:" opener + OPTIMIZE_INSTRUCTIONS
  documentation.** Model-native template pattern not covered. Add "Do not open with 'Core tension:'"
  and document the model-native-template failure class in OPTIMIZE_INSTRUCTIONS.
- **[MEDIUM] B3/I4: Move "at least 15 words with an action verb" into system-prompt section 6.**
  Currently call-2/3 prefix only (line 283); call 1 is unenforced. PR #334 claimed uniform
  enforcement but did not add the constraint to section 6 (lines 243–246).
- **[LOW] B4: Global dispatcher event handler shared across concurrent worker threads.**
  `runner.py` — per-plan tracking files unreliable in multi-worker mode. Observability impact
  only; no effect on plan output quality.
- **[LOW] S1: Case-insensitive lever name deduplication.** "Supply Chain Strategy" vs "supply
  chain strategy" would pass through as distinct levers. Low urgency.
- **[LOW] Q4: Consider replacing llama3.1 in standard test suite.** Chronic partial_recovery
  across runs 60 and 75; strongest template lock; full timeout on hong_kong_game in run 75.
  Low signal per run. Candidate replacement: a more reliable small model.

---

## INVALID EXPERIMENT

This entire iteration is invalid. The runner was executed from the main PlanExe
repo (`/Users/neoneye/git/PlanExeGroup/PlanExe`) which was on the `main` branch,
not the PR #334 branch (`fix/lever-content-changes`). The
`run_optimization_iteration.py` script uses `cwd=PLANEXE_DIR` when spawning the
runner, and `PLANEXE_DIR` points to the main repo checkout. Since
`python3.11 -m self_improve.runner` imports `identify_potential_levers.py` from
whatever code is in the working directory, all 7 model runs (history 75–81)
tested the `main` branch code — not the PR's changes.

Consequence: the assessment above compares `main` (runs 75–81) against an older
`main` snapshot (runs 53–59 from analysis 22). The findings about the summary
field still being present at line 164 are correct for `main` but irrelevant to
PR #334, which does remove it. No conclusions about PR #334's actual impact can
be drawn from this data.

The experiment needs to be re-run with the runner executing from the worktree
(or with the main repo checked out to the PR branch) so that the PR's code
changes are actually tested.
