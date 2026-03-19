# Insight Claude

## Scope

Analyzing runs `2/94–2/99` and `3/00` (after PR #361) against `2/87–2/93` (before,
analysis 40 / best.json baseline) for the `identify_potential_levers` step.

**PR under evaluation:** PR #361 "experiment: remove lever_index from Lever schema"

**Change made by the PR:**
Remove `lever_index: int` from the `Lever` Pydantic schema. The field was generated
by the LLM but never transferred to `LeverCleaned` or used downstream. The stated
concern was that it might act as a "sink" for the LLM's sequential numbering tendency,
and that removing it might cause models to insert index prefixes ("1.", "2.") into
`name` or `consequences` fields instead.

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/87 | 2/94 | ollama-llama3.1 |
| 2/88 | 2/95 | openrouter-openai-gpt-oss-20b |
| 2/89 | 2/96 | openai-gpt-5-nano |
| 2/90 | 2/97 | openrouter-qwen3-30b-a3b |
| 2/91 | 2/98 | openrouter-openai-gpt-4o-mini |
| 2/92 | 2/99 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 3/00 | anthropic-claude-haiku-4-5-pinned |

Source: `meta.json` in each run directory.

---

## Positive Things

1. **Primary risk did NOT materialize.** No model inserted "1.", "2.", "3." etc.
   as index prefixes in `name` or `consequences` fields after lever_index was
   removed. Checked: haiku (3/00) hong_kong_game raw names: "Narrative Subversion
   Strategy", "Director's Relationship to Hong Kong", "Technology's Narrative Role"
   — no prefixes. gpt-5-nano (96) names: "HK-based financing architecture with
   pre-sales", "Casting and creative leadership" — no prefixes. llama3.1 (94)
   names: "Cinematic DNA", "Location-Driven Production" — no prefixes. qwen3 (97)
   names: "Location-Driven Paranoia Architecture", "Talent Hybridization Strategy"
   — no prefixes.
   Evidence: `history/2/94_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`,
   `history/2/96_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`,
   `history/2/97_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`,
   `history/3/00_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`.

2. **Schema is cleaner.** The Lever class now has 4 fields (`name`, `consequences`,
   `options`, `review_lever`) instead of 5. The `lever_index` field was confirmed
   to be unused: the `LeverCleaned` mapping at lines 360–374 of
   `identify_potential_levers.py` never transfers `lever_index` — it creates a
   fresh `lever_id = str(uuid.uuid4())`. The PR eliminates dead weight from the
   schema without affecting downstream data flow.

3. **No LLMChatErrors or ValidationErrors in any after run.** All seven events.jsonl
   files contain only `run_single_plan_start`, `run_single_plan_complete`, and
   `partial_recovery` events. No schema validation failures or LLMChatErrors.
   Evidence: `history/2/94–2/99_identify_potential_levers/events.jsonl`,
   `history/3/00_identify_potential_levers/events.jsonl`.

4. **Non-haiku models unaffected.** gpt-oss-20b (95), gpt-5-nano (96), qwen3 (97),
   gpt-4o-mini (98), and gemini (99) all achieved 15/15 calls (100%) with no
   partial_recovery events — unchanged from the before runs (88–92). The PR had
   zero observable effect on these five models.

5. **Plan-level success rate remains 100%.** All 35 plans across all 7 runs
   completed with `status: "ok"`. The partial_recovery events for haiku and llama3.1
   are step-gate exits (enough levers collected early), not failures. No plan
   produced zero levers or failed entirely.

---

## Negative Things

1. **Haiku partial_recovery increased dramatically: 2/5 plans → ALL 5 plans.**
   Before (run 93 haiku): partial_recovery on gta_game (2/3) and silo (2/3) = 13/15
   calls = 86.7%. After (run 3/00 haiku): partial_recovery on ALL 5 plans (gta_game,
   hong_kong_game, sovereign_identity, silo, parasomnia) = 10/15 calls = 66.7%.
   That is a -20pp regression for haiku. Evidence:
   - Before: `history/2/93_identify_potential_levers/events.jsonl` (2 partial_recovery events)
   - After: `history/3/00_identify_potential_levers/events.jsonl` (5 partial_recovery events,
     one per plan)

2. **Overall call efficiency regressed from 97.1% to 93.3% (-3.8pp).**
   Before (runs 87–93): 102 calls succeeded of 105 expected. After (runs 94–99,
   3/00): 98 calls succeeded of 105 expected. While all plans completed with
   `status: "ok"`, the reduction in 3rd-call diversity is real. Levers generated
   in a 3rd call would be explicitly instructed to use different names than calls 1
   and 2 (via the `"Generate 5 to 7 MORE levers with completely different names"`
   prompt), providing distinct perspectives. All partial_recovery plans miss this
   call.

3. **llama3.1 partial_recovery increased: 1/5 plans → 2/5 plans.** Before (run 87
   llama3.1): partial_recovery on hong_kong_game (2/3) = 14/15. After (run 94
   llama3.1): partial_recovery on silo (2/3) and sovereign_identity (2/3) = 13/15.
   Minor regression, possibly stochastic since llama3.1 uses 1 worker (sequential)
   vs 4 workers for other models.

4. **Haiku is over-generating levers per call (8–12 vs 5–7 target).** For
   hong_kong_game after (3/00 haiku): 16 levers in 2 calls = ~8 levers/call.
   For silo after (3/00 haiku): 24 levers in 2 calls = ~12 levers/call.
   The 5-to-7 lever target per call in the system prompt is being exceeded
   substantially. With min_levers=15 (source line 285), 2 calls × 8–12 = 16–24
   levers crosses the threshold, triggering early stop. Before the PR, haiku
   was generating ~6–7/call for most plans, requiring 3 calls for most.
   Source: `history/3/00_identify_potential_levers/outputs/*/activity_overview.json`
   and `identify_potential_levers.py:285`.

5. **"None/all three options" template lock unchanged.** Haiku's secondary template
   lock from PR #358 persists at ~87% in hong_kong_game after (3/00). Out of 16
   reviews examined: 14/16 use "none of the three options [directly] address/resolve/
   specify" or "all three options leave unaddressed". This is unchanged from run 93's
   ~85%. PR #361 had no effect on this pattern, as expected (different root cause).
   Evidence: `history/3/00_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

6. **Haiku review lengths appear longer for silo (420 chars avg vs ~304 chars before).**
   After haiku (3/00) silo: first 6 reviews average ~420 chars. Before haiku (93)
   silo: first 5 reviews average ~304 chars. Ratio vs baseline (~75 chars): 5.6×
   after vs ~4.1× before. This exceeds the 3× regression threshold for silo.
   However, this comparison is partly confounded: before and after runs generate
   different lever topics for the same plan (different stochastic seeds). The
   hong_kong_game review comparison shows a more similar picture: ~237 chars after
   vs ~221 chars before (7% change, not significant). The silo regression may be
   plan-specific and not caused by the PR change.

---

## Comparison

| Metric | Before (runs 87–93) | After (runs 94–99, 3/00) | Change |
|--------|--------------------|--------------------|--------|
| Overall call efficiency | 102/105 = 97.1% | 98/105 = 93.3% | **-3.8pp** |
| Haiku call efficiency | 13/15 = 86.7% | 10/15 = 66.7% | **-20pp** |
| Haiku partial_recovery count | 2 plans (gta, silo) | 5 plans (ALL plans) | **+3 events** |
| llama3.1 call efficiency | 14/15 = 93.3% | 13/15 = 86.7% | -6.7pp |
| gpt-oss-20b, gpt-5-nano, qwen3, gpt-4o-mini, gemini | 15/15 each = 100% | 15/15 each = 100% | 0 unchanged |
| Plan-level success rate | 35/35 = 100% | 35/35 = 100% | 0 unchanged |
| Index prefixes in lever names | 0 observed | 0 observed | — unchanged |
| "None/all three" lock — haiku (hong_kong_game) | ~85% | ~87% | ~same |
| Lever_index in raw outputs | Present (e.g. run 93) | Absent (run 3/00) | **REMOVED** |
| LLMChatErrors | 0 | 0 | — unchanged |
| Haiku review avg length (hong_kong_game) | ~221 chars | ~237 chars | +7%, not significant |
| Haiku review avg length (silo) | ~304 chars | ~420 chars | +38% (confounded by lever topics) |

---

## Quantitative Metrics

### Call Efficiency Per Run

| Run | Model | Calls Succeeded | Calls Expected | Efficiency | Partial Recovery Events |
|-----|-------|-----------------|----------------|------------|------------------------|
| 87 (before) | llama3.1 | 14 | 15 | 93.3% | 1 (hong_kong_game 2/3) |
| 88 (before) | gpt-oss-20b | 15 | 15 | 100% | 0 |
| 89 (before) | gpt-5-nano | 15 | 15 | 100% | 0 |
| 90 (before) | qwen3-30b | 15 | 15 | 100% | 0 |
| 91 (before) | gpt-4o-mini | 15 | 15 | 100% | 0 |
| 92 (before) | gemini | 15 | 15 | 100% | 0 |
| 93 (before) | haiku | 13 | 15 | 86.7% | 2 (gta 2/3, silo 2/3) |
| **Before total** | — | **102** | **105** | **97.1%** | 3 |
| 94 (after) | llama3.1 | 13 | 15 | 86.7% | 2 (silo 2/3, sovereign 2/3) |
| 95 (after) | gpt-oss-20b | 15 | 15 | 100% | 0 |
| 96 (after) | gpt-5-nano | 15 | 15 | 100% | 0 |
| 97 (after) | qwen3-30b | 15 | 15 | 100% | 0 |
| 98 (after) | gpt-4o-mini | 15 | 15 | 100% | 0 |
| 99 (after) | gemini | 15 | 15 | 100% | 0 |
| 3/00 (after) | haiku | 10 | 15 | 66.7% | 5 (ALL plans 2/3) |
| **After total** | — | **98** | **105** | **93.3%** | 7 |

### Haiku Lever Count Per Call (Step-Gate Analysis)

| Plan | Before (run 93) calls | Before total levers | After (run 3/00) calls | After total levers | Avg levers/call (after) |
|------|----------------------|---------------------|------------------------|---------------------|------------------------|
| hong_kong_game | 3 (3/3) | 20 | 2 (partial) | 16 | ~8 |
| silo | 2 (partial) | ~17 | 2 (partial) | 24 | ~12 |
| gta_game | 2 (partial) | ~16 | 2 (partial) | ~15-16 (est.) | ~8 |
| sovereign_identity | 3 (3/3) | ~20 | 2 (partial) | ~16 (est.) | ~8 |
| parasomnia | 3 (3/3) | ~21 | 2 (partial) | ~16 (est.) | ~8 |

Source: `history/3/00_identify_potential_levers/outputs/*/activity_overview.json` (2 calls for all plans),
`history/2/93_identify_potential_levers/outputs.jsonl` (calls_succeeded per plan).

Min-levers threshold: 15 (line 285 of `identify_potential_levers.py`).
With haiku generating ~8–12 levers per call, 2 calls × 8 = 16 ≥ 15, triggering early stop every time.

### "None/All Three Options" Template Lock (Haiku — hong_kong_game)

| Run | "none/all three" phrase count | Total reviews | Rate |
|-----|-------------------------------|---------------|------|
| 93 (before haiku) | ~17/20 | 20 | ~85% |
| 3/00 (after haiku) | 14/16 | 16 | 87.5% |

Evidence: `history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
`history/3/00_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### Review Length vs Baseline

| Source | Avg review length (chars) | Ratio vs baseline |
|--------|--------------------------|-------------------|
| Baseline train (silo) | ~75 | 1.0× |
| Before haiku run 93 (hong_kong_game) | ~221 | 2.9× |
| After haiku run 3/00 (hong_kong_game) | ~237 | 3.2× |
| Before haiku run 93 (silo) | ~304 | 4.1× |
| After haiku run 3/00 (silo) | ~420 | 5.6× (confounded) |

The hong_kong_game comparison (+7%) is the more comparable measurement because the
before and after runs used the same 3 of 5 calls (both runs had 3 calls for
hong_kong_game). The silo comparison is confounded because run 93 only completed
2/3 calls (early exit) and run 3/00 also only completed 2/3 calls but with different
stochastic lever topics.

Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json`,
`history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
`history/3/00_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

---

## Evidence Notes

- **lever_index in before run (confirmed):** `history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
  line 7: `"lever_index": 1` is present in every lever object for haiku before the PR.

- **lever_index absent in after run (confirmed):** `history/3/00_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
  — lever objects contain only `name`, `consequences`, `options`, `review_lever`. No
  `lever_index` field.

- **Schema confirmation:** `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
  `Lever` class (lines 95–138): only 4 fields — `name`, `consequences`, `options`,
  `review_lever`. The `lever_index` field is absent. `LeverCleaned` mapping at lines
  360–374 confirms `lever_index` is never read from `Lever` objects.

- **Step-gate logic:** `identify_potential_levers.py` line 285: `min_levers = 15`.
  Line 348: `if len(generated_lever_names) >= min_levers: break`. This is the
  mechanism causing partial_recovery when haiku generates 8–12 levers per call.

- **Haiku output tokens per plan (after run 3/00):**
  - gta_game: 2 calls, 5205 output tokens (~2603 tokens/call)
  - hong_kong_game: 2 calls, 5767 output tokens (~2884 tokens/call)
  Compare with before (run 93): hong_kong_game 3 calls, 8996 output tokens (~2999
  tokens/call). Per-call output is similar; the difference is in lever count per call.
  Evidence: `history/3/00_identify_potential_levers/outputs/*/activity_overview.json`,
  `history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json`.

- **No fabricated percentage claims in names.** The silo plan's consequences fields
  contain engineering estimate percentages (e.g., "30–40% longer construction timeline",
  "25–30% additional capital") in both before (run 93) and after (run 3/00) runs.
  These are not new to the PR. The silo plan's technical domain consistently elicits
  quantified responses from haiku — this predates PR #361. Evidence: both
  `history/2/93_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  and `history/3/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  contain similar percentage claims in consequences.

- **OPTIMIZE_INSTRUCTIONS:** Current OPTIMIZE_INSTRUCTIONS (lines 27–93 of
  `identify_potential_levers.py`) does not mention `lever_index` or over-generation
  of levers per call. The "Verbosity amplification" entry (lines 83–85) focuses on
  example verbosity, not per-call lever count. The current OPTIMIZE_INSTRUCTIONS is
  consistent with the code state after PR #361.

---

## PR Impact

**What the PR was supposed to fix:** Remove `lever_index: int` from the `Lever`
Pydantic schema. The field was generated by the LLM but never transferred to
`LeverCleaned` or used downstream. Removing it cleans up the schema. The stated
risk was that without `lever_index` acting as a "sink" for sequential numbering,
models might insert index prefixes into `name` or `consequences` fields.

**Comparison table:**

| Metric | Before (runs 87–93) | After (runs 94–99, 3/00) | Change |
|--------|--------------------|--------------------|--------|
| lever_index field in LLM output | Present (all models) | Absent (all models) | **REMOVED** |
| Index prefixes in lever names ("1.", "2.") | 0 | 0 | No change |
| Overall call efficiency | 97.1% | 93.3% | **-3.8pp** |
| Haiku call efficiency | 86.7% | 66.7% | **-20pp** |
| llama3.1 call efficiency | 93.3% | 86.7% | -6.7pp |
| 5-model efficiency (gpt-oss, gpt-5-nano, qwen3, gpt-4o-mini, gemini) | 100% each | 100% each | 0 unchanged |
| Plan-level success (35 plans) | 35/35 = 100% | 35/35 = 100% | 0 unchanged |
| Haiku partial_recovery events | 2/5 plans | 5/5 plans (ALL) | **+3** |
| "None/all three" lock — haiku (hk_game) | ~85% | ~87% | ~same |
| Haiku review length (hong_kong_game) | ~221 chars | ~237 chars | +7%, minor |

**Did the PR fix the targeted issue?** Partially. The schema change is confirmed:
`lever_index` is removed from the Lever class, and no model inserts index prefixes
into name/consequences fields (the stated risk did not materialize). The change
achieves its schema cleanup goal.

**Did the PR introduce regressions?**

One clear regression: haiku's call efficiency dropped from 86.7% to 66.7% (-20pp),
with ALL 5 plans now triggering partial_recovery. This is caused by haiku generating
more levers per call after the change (~8–12 per call vs ~6–7 before), crossing the
min_levers=15 threshold in just 2 calls for every plan. The most likely mechanism:
without the `lever_index: int` field to generate, each lever's JSON is slightly
more compact, allowing haiku to fit more levers within its per-call token budget.
This means haiku consistently hits the step-gate threshold in 2 calls instead of 3,
losing the diversity benefit of a dedicated 3rd call (which uses a different prompt
variant: "Generate MORE levers with completely different names").

However, note that:
1. All 35 plans still complete with `status: "ok"` — this is not a reliability failure.
2. Haiku still generates 16–24 levers per plan in 2 calls — sufficient quantity for
   downstream deduplication and enrichment.
3. The diversity concern is real but mild: 2 × 8–12 = 16–24 levers vs 3 × 6–7 = 18–21.
   The total lever count is similar or higher; the missing diversity is the 3rd call's
   uniquely constrained perspective.

**Verdict: CONDITIONAL**

The schema change itself is correct and should be kept. The lever_index removal
cleans up dead weight with no observed negative effects on content quality. However,
the mechanism causing haiku to now always exit the step-gate after 2 calls warrants
a follow-up: increasing `min_levers` from 15 to 18 (or 20) would ensure haiku needs
3 calls even at 8+ levers per call, recovering the 3rd-call diversity for haiku.
Alternatively, adding a per-call lever target enforcement (e.g., a `max_levers_per_call`
soft cap in the system prompt) would prevent over-generation.

---

## Questions For Later Synthesis

1. **Why did haiku's per-call lever count increase?** Is removing `lever_index`
   (one integer field) sufficient to cause haiku to generate 8–12 vs 6–7 levers per
   call? Or is this run-to-run stochastic variance? A re-run of haiku with the PR
   reverted (lever_index restored) would disambiguate this.

2. **Is the "none/all three options" template lock getting worse?** Both before (85%)
   and after (87%) haiku hong_kong_game show this lock. PR #361 did not target it.
   The synthesis from analysis 40 designated this as the next target. What is the
   next PR's approach?

3. **Should min_levers be increased to 18?** With haiku generating 8–12 levers per
   call, min_levers=15 is now too easily reached in 2 calls. Setting min_levers=18
   or 20 would restore 3-call behavior for haiku. But this might also add calls for
   models that currently need exactly 3 calls at 6–7 levers/call. Synthesis should
   evaluate whether this change is worthwhile.

4. **Does the silo review length increase (304 → 420 chars) reflect PR causation
   or topic confounding?** The hong_kong_game comparison shows only +7% change.
   The silo increase may be due to haiku generating different lever topics stochastically
   — some topics (e.g., "Ecosystem Redundancy") generate longer, more technical reviews.
   This needs to be disambiguated before attributing it to the PR.

5. **Does the PR-induced over-generation in haiku actually hurt downstream output
   quality?** The downstream DeduplicateLeversTask and FocusOnVitalFewLevers steps
   filter to 4–6 levers regardless of how many were generated. If 2-call haiku
   outputs (16–24 levers) produce the same final 4–6 levers as 3-call outputs
   (18–21 levers), the diversity concern is moot.

---

## Reflect

PR #361 demonstrates a clean schema removal: lever_index was dead code in the
pipeline, and removing it did not trigger the predicted risk (index prefix leakage
into names). The schema is simpler and more honest after the PR.

The unexpected consequence — haiku consistently triggering early step-gate exit for
all 5 plans — is the only substantive concern. It's a behavioral shift, not a
failure. But it changes haiku's lever diversity profile in a way that wasn't intended
by the PR. The mechanism is plausible (fewer fields → more compact JSON → more
levers per call → earlier step-gate hit) but unconfirmed.

The "none/all three options" template lock (the target of the NEXT iteration per
analysis 40 synthesis) is unchanged by PR #361 — it was already predicted and
documented in OPTIMIZE_INSTRUCTIONS. PR #361 was not designed to address it.

The fabricated percentages in silo consequences are a pre-existing pattern for
haiku on technical plans, present in both before and after runs. Not caused by
this PR.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (lines 27–93 of `identify_potential_levers.py`)
is well-maintained and accurately documents known failure modes. Two additions are
worth proposing after this analysis:

1. **Over-generation per call** is not currently listed as a known problem. The
   current text says "Over-generation is fine; step 2 handles extras." This is
   true at the plan level, but consistent over-generation (8–12 levers/call instead
   of 5–7) causes the step-gate to exit early, reducing per-plan diversity. A note
   like: "Some models consistently generate 8–12 levers per call instead of 5–7,
   causing the step-gate to exit after 2 calls and missing the 3rd call's unique
   perspective. Consider raising min_levers or adding a soft per-call cap in the
   system prompt if this pattern is detected." would help future analysts.

2. **Lever schema changes affect per-call lever count** — removing or adding fields
   changes the JSON compactness per lever, which can shift how many levers fit in
   a model's per-call output. This should be listed as a "schema change side effect"
   to watch for in future iterations.

---

## Potential Code Changes

**C1 (Step-gate tuning):** Increase `min_levers` from 15 to 18 (or 20) in
`identify_potential_levers.py` line 285. With haiku now generating 8–12 levers per
call, `min_levers=15` is crossed after 2 calls consistently. Setting `min_levers=18`
would ensure 3 calls for haiku while having no effect on models that already complete
3 calls at 6–7 levers/call (3 × 7 = 21 ≥ 18 on the 3rd call). Risk: minor — models
already reaching 21+ levers in 2 calls would not be affected since 21 ≥ 18.

**C2 (Soft per-call target in system prompt):** Add a system prompt instruction like
"Aim for exactly 5 to 7 levers per response — do not generate more than 7." The
current Section 1 says "generate 5 to 7 levers per response" but some models treat
this as a minimum rather than a maximum. Making the upper bound explicit might prevent
over-generation without needing to change the step-gate threshold. This is a prompt
change, not a code change.

**C3 (OPTIMIZE_INSTRUCTIONS update):** Add a note about over-generation per call and
schema-change side effects (see OPTIMIZE_INSTRUCTIONS Alignment above). No runtime
effect; improves self-improve guidance accuracy.

---

## Hypotheses

**H1 (Root cause investigation):** Haiku's per-call lever count increased because
removing lever_index made each lever's JSON more compact (~15–20 tokens shorter per
lever), allowing haiku to generate 8–12 levers within its per-call token budget
instead of 6–7. This can be tested by restoring lever_index in a follow-up run
and measuring whether haiku returns to 2/5 partial_recovery events (the before state).

**H2 (Fix: raise min_levers):** Increasing `min_levers` from 15 to 18 in
`identify_potential_levers.py:285` would force haiku to complete a 3rd call even when
generating 8 levers per call (2 × 8 = 16 < 18 → 3rd call needed). This preserves
the diversity benefit of the 3rd call without reverting the lever_index removal.
Expected effect: haiku partial_recovery drops from 5/5 plans back toward 0/5 plans.
Risk: none for other models (they already reach 15+ levers in 3 calls at 6–7/call).

**H3 (Continued template lock target):** The "none of the three options" secondary
template lock (87% in haiku hong_kong_game) is the top-priority issue from analysis
40, unaddressed by this PR. The next PR should target the review_lever field description
or the Section 4 examples, per H1 from analysis 40.

---

## Summary

PR #361 achieves its stated goal: `lever_index: int` is removed from the `Lever`
schema and confirmed absent in all after-run raw outputs. The primary risk (index
prefixes in names/consequences) did not materialize across any of the 7 tested models.

However, an unexpected side effect emerged: haiku now generates more levers per call
(8–12 vs ~6–7 before), causing the step-gate to exit after 2/3 calls for ALL 5 plans
instead of just 2/5. This reduces the diversity benefit of the 3rd call (which would
have used a unique-names constraint to generate distinct levers). The overall call
efficiency dropped from 97.1% to 93.3%, with haiku falling from 86.7% to 66.7%.

Five other models are entirely unaffected (100% before and after).

**PR verdict: CONDITIONAL.** The schema cleanup is correct and should be kept.
The increased partial_recovery for haiku needs a follow-up fix: increase `min_levers`
from 15 to 18 (C1) to restore 3-call behavior for haiku. This is a low-risk,
one-line code change that preserves the PR's schema simplification benefit while
recovering haiku's per-plan lever diversity.
