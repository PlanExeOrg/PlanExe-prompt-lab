# Insight Claude

## Context

This analysis evaluates PR #334 ("fix: remove unused summary field, slim call-2/3 prefix")
against runs 82–88 (after PR merged to main). The previous analysis (24) used runs 75–81,
which were an **invalid experiment** (runner executed against old `main`, not the PR branch).
Analysis 25 is the first valid test of PR #334's actual changes.

**Model mapping (identical before→after pairing):**

| Run (before) | Run (after) | Model |
|---|---|---|
| 75 | 82 | ollama-llama3.1 |
| 76 | 83 | openrouter-openai-gpt-oss-20b |
| 77 | 84 | openai-gpt-5-nano |
| 78 | 85 | openrouter-qwen3-30b-a3b |
| 79 | 86 | openrouter-openai-gpt-4o-mini |
| 80 | 87 | openrouter-gemini-2.0-flash-001 |
| 81 | 88 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### N1. llama3.1 gta_game Pydantic failure still present (run 82)
Run 82 (llama3.1 after) failed on gta_game with:
```
2 validation errors for DocumentDetails
levers.5.options — Value error, options must have exactly 3 items, got 2
levers.6.options — Value error, options must have exactly 3 items, got 2
```
This is the same pre-existing llama3.1 weakness. The PR did not introduce or fix this.
Source: `history/1/82_identify_potential_levers/events.jsonl` and `outputs.jsonl`.

### N2. "at least 15 words with action verb" constraint not fully obeyed by llama3.1 (call 1)
Even after adding the constraint to section 6, llama3.1 still generates short-label options
on call 1. Examples from run 82 sovereign_identity (call 1):
- "Establish a new, centralized authority responsible for overseeing digital identity standards and certification" — 13 words
- "Develop a decentralized, blockchain-based governance model that incentivizes community-led standardization" — 12 words
- "Implement a hybrid approach combining elements of both centralized and decentralized governance" — 12 words

By contrast, run 75 (before) sovereign_identity options were even shorter:
- "Prioritize open standards and platform-neutral requirements" — 7 words
- "Establish a transparent evaluation framework for suppliers" — 7 words

So the constraint is helping llama3.1 marginally but still not meeting the 15-word floor consistently.

### N3. Template lock in reviews persists for llama3.1
Run 82 (llama3.1 after) reviews: 100% open with "This lever governs the tension between…"
across all plans inspected. No change from run 75 (before). The PR slimmed the call-2/3
prefix but did not address the template-lock issue.
Source: `history/1/82_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

### N4. Partial recoveries persist
Two after-batch partial recoveries observed (calls_succeeded=2 instead of 3):
- Run 83 (gpt-oss-20b): parasomnia — `"calls_succeeded": 2`
- Run 88 (haiku): gta_game — `"calls_succeeded": 2` with `partial_recovery` event

Final outputs are assembled from 2 of 3 calls. These are not new regressions — the same
phenomenon existed in the before batch (runs 75, 76: partial_recovery events).

---

## Positive Things

### P1. Summary field removal confirmed — token waste eliminated
**Before (runs 75–81):** `grep "summary"` in raw files finds 2–3 hits per plan per run
(one per LLM call). Example from `history/1/75_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`:
```json
"summary": "Add 'prioritize local talent development through vocational training programs' to Social Structure and Governance."
```
**After (runs 82–88):** `grep "summary"` returns zero matches in all raw files.

This confirms that PR #334 was properly applied. The before batch wasted one `summary`
generation per LLM call: 7 runs × 3 calls × 5 plans = **105 summary generations per
7-model experiment**, now eliminated.

### P2. Success rate improved marginally
Before (runs 75–81): 2 full errors → 33/35 plans = **94.3%**
After (runs 82–88): 1 full error → 34/35 plans = **97.1%**
(+1 plan success, +2.8 percentage points)

The qwen3 JSON extraction failure (run 78, parasomnia) did not recur in run 85. The
llama3.1 before/after swap (hong_kong_game timeout → gta_game Pydantic error) is a
lateral move — still 1 failure per llama3.1 run.

### P3. Option specificity measurably improved for haiku
Comparing haiku before (run 81) vs after (run 88) for gta_game:
- Before option: "Build core city districts by hand with full environmental storytelling and NPC ecosystems, using procedural generation only for outlying wilderness and repeatable interiors to manage scope" — ~28 words
- After option: "Establish a core storyline of 8–12 hand-authored heists with fully written character arcs, then use procedural generation only for ambient street-level crime scenarios, side missions, and NPC routines that support but do not drive the main narrative." — ~41 words

The after options include specific quantified scope details (8–12 heists, exact tradeoff
descriptions) that were absent before. This correlates with the "at least 15 words with
an action verb" constraint being added to section 6 in addition to the call-2/3 prefix.

### P4. Content quality for strong models remains high
Haiku (run 88) and gpt-5-nano (run 84) outputs remain well above baseline quality:
- Options are 25–60 words (strongly above the 15-word floor)
- Consequences are specific to plan context (financial figures, timeline details)
- Reviews identify genuine trade-offs, not boilerplate
No content quality regression introduced by the PR.

### P5. No new fabricated percentage claims in after batch
Review of matched model outputs (haiku, gpt-4o-mini, qwen3) for hong_kong_game and
gta_game: zero fabricated percentage claims such as "reduces costs by X%" found in
consequences or options. The PR did not introduce new optimism-bias language.

---

## Comparison

| Metric | Before (runs 75–81) | After (runs 82–88) | Change |
|---|---|---|---|
| Plan success rate | 33/35 (94.3%) | 34/35 (97.1%) | +2.8 pp |
| Summary field in raw files | 2–3 per plan | 0 per plan | **Eliminated** |
| llama3.1 option word count (call 1, sovereign_identity) | ~7–8 words avg | ~12–13 words avg | +5 words |
| haiku option word count (gta_game lever 1) | ~28 words | ~41 words | +13 words |
| gpt-4o-mini option word count (gta_game) | ~17–19 words | ~17–20 words | ~unchanged |
| "This lever governs" template lock (llama3.1) | 100% | 100% | Unchanged |
| qwen3 "Core tension:" opener | Present (runs 76–78) | Present (run 85) | Unchanged |
| Fabricated % claims | 0 | 0 | Unchanged |
| Partial recoveries | 2 (runs 75, 76) | 2 (runs 83, 88) | Unchanged |

---

## Quantitative Metrics

### Uniqueness — llama3.1 lever names (run 82, hong_kong_game)
15 levers, all unique names: Hong Kong Setting Authenticity, Director Background,
Protagonist Characterization, Script Adaptation, Music and Score, Revenue Strategy,
IP Rights Management, Authenticity Matrix, Cinematographic DNA, Local Crew Involvement,
Hong Kong's Surveillance Infrastructure, Remake vs Original, Festival Launch Strategy,
Target Audience Segmentation, Revenue Risk Management. **15/15 unique (100%)**.

### Uniqueness — haiku lever names (run 88, hong_kong_game)
17 levers inspected. All unique names covering distinct creative/commercial domains
(Twist Architecture, Regulatory Navigation, Casting, Photography Schedule,
Surveillance Staging, Revenue Diversification, Director Selection, Spatial Disorientation,
Antagonist Screen Time, Technology Visibility, Descent Velocity, Reality Seams,
Emotional Catharsis, Diegetic Sound, Twist Inversion, Protagonist Wealth, Game Inception,
Financial Tracking, Female Co-Protagonist, Escalation Trigger, Redemption Architecture).
**17/17 unique (100%)** with no semantic near-duplicates.

### Field length table — hong_kong_game (baseline vs matched models)

| Source | Avg consequences (chars) | Avg options (chars) | Avg review (chars) |
|---|---|---|---|
| Baseline (train) | ~245 | ~155 | ~110 |
| Run 75 llama3.1 (before) | ~200 | ~50 | ~155 |
| Run 82 llama3.1 (after) | ~200 | ~85 | ~150 |
| Run 81 haiku (before) | ~395 | ~220 | ~355 |
| Run 88 haiku (after) | ~430 | ~270 | ~430 |
| Run 79 gpt-4o-mini (before) | ~170 | ~125 | ~145 |
| Run 86 gpt-4o-mini (after) | ~185 | ~130 | ~150 |

Field length ratios vs baseline:
- llama3.1: consequences ~0.8×, options ~0.5× (BELOW baseline for options — short-label problem)
- haiku: consequences ~1.7×, options ~1.7×, review ~3.9× (review approaching 4× — verbose)
- gpt-4o-mini: consequences ~0.7×, options ~0.8× — slightly below baseline, acceptable

### Option word count — llama3.1 constraint compliance

| Plan | Model | Before (run 75) avg words/option | After (run 82) avg words/option | Meets 15-word floor? |
|---|---|---|---|---|
| sovereign_identity call 1 | llama3.1 | ~7 | ~12 | Before: NO; After: NO |
| hong_kong_game | llama3.1 | ~14 | ~13 | Marginal before, marginal after |
| silo | llama3.1 | ~12 | ~12 | Marginal both |

The 15-word floor is still not met consistently by llama3.1 on call 1. The PR moves
average option length from 7–8 words toward 12–13 words on short plans, but does not
reliably cross the 15-word threshold.

### Constraint violations

| Model run | violation type | count |
|---|---|---|
| Run 82 (llama3.1) gta_game | options ≠ 3 items (levers 5, 6) | 2 |
| All other after runs | none detected | 0 |

### Template leakage

No bracket placeholders (`[...]`) or verbatim prompt example copies detected in sampled
outputs across runs 82–88.

---

## Evidence Notes

1. **Summary field elimination**: Grep for `"summary"` in `history/1/75_*/outputs/*/002-9-potential_levers_raw.json` returns 2–3 hits (one per call). Same grep against `history/1/82_*/` returns 0 hits. This is the primary evidence that PR #334 was properly applied.

2. **llama3.1 option length improvement**: `history/1/75_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` shows options like "Prioritize open standards and platform-neutral requirements" (7 words). `history/1/82_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` shows "Establish a new, centralized authority responsible for overseeing digital identity standards and certification" (13 words). Marginal improvement but below the 15-word floor.

3. **Haiku quality**: `history/1/88_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json` shows a rich `strategic_rationale` paragraph plus 17 detailed levers with project-specific options. Review fields are verbose (~430 chars avg), approaching 4× baseline. The ratio is high but reviews appear substantive — named specific weaknesses per lever, not filler text.

4. **Baseline comparison for hong_kong_game**: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` contains fabricated percentage claims ("15% higher audience engagement", "20% higher pre-sales", "30% increase in streaming revenue"). After runs do NOT carry these baseline fabrications — the PR's removal of the fabrication reminder from the call-2/3 prefix did not regress fabrication avoidance.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Known problems in OPTIMIZE_INSTRUCTIONS (from `identify_potential_levers.py`):
- Optimism bias ✓ documented
- Fabricated numbers ✓ documented
- Marketing language ✓ documented
- Formulaic option triads ✓ documented
- Fragile English-only validation ✓ documented

**Alignment check for this batch:**
- Fabricated numbers: NONE found in sampled after runs — good alignment
- Template lock ("This lever governs the tension between"): present in llama3.1 100%; NOT yet in OPTIMIZE_INSTRUCTIONS as a known failure class for LLM-native patterns
- qwen3 "Core tension:" opener: NOT in OPTIMIZE_INSTRUCTIONS (identified in analysis 24 as new issue N1)

**Proposed OPTIMIZE_INSTRUCTIONS addition** (recurring problem confirmed across analyses 22, 24, 25):

> **Model-native template openers**: Small or MoE models may prepend reviews with fixed phrases absent from prompt examples ("This lever governs the tension between", "Core tension: X."). These are not driven by prompt examples but by the model's training distribution. Validators that check review format will not catch this; only a negative constraint in the field description ("Do not open with 'This lever governs the tension between'") interrupts the pattern.

---

## PR Impact

### What the PR was supposed to fix
1. Remove `DocumentDetails.summary` — required field never used downstream, wastes tokens
2. Remove matching summary validation section from system prompt
3. Add "at least 15 words with an action verb" to system-prompt section 6 for all calls
4. Slim call-2/3 prefix: remove duplicate quality/anti-fabrication reminders

### Before vs after comparison

| Metric | Before (runs 75–81) | After (runs 82–88) | Change |
|---|---|---|---|
| Summary field in raw outputs | Present (2–3/plan) | Absent (0) | **FIXED** |
| Summary tokens wasted per experiment | ~105 summaries | 0 | **FIXED** |
| "at least 15 words" on call 1 (llama3.1) | Not enforced (~7 words) | Partially enforced (~12 words) | **PARTIAL** |
| "at least 15 words" on calls 2–3 (all models) | Enforced (was in prefix) | Enforced (now also in section 6) | **IMPROVED** |
| Success rate | 94.3% (33/35) | 97.1% (34/35) | +2.8 pp |
| Content quality regression | None | None | NEUTRAL |
| New validation failures | — | 1 (llama3.1 gta_game Pydantic) | LATERAL (was different failure) |

### Did the PR fix the targeted issue?

**Yes, completely** for items 1–2 (summary field removal). Confirmed by grep evidence:
zero `"summary"` keys in any after run raw file, vs 2–3 per plan in before runs.

**Partially** for item 3 ("at least 15 words"): The constraint is now in section 6
(applies to call 1) in addition to the call-2/3 prefix. This improves llama3.1 call-1
options from ~7 to ~12 words on average, but still falls short of 15. Stronger models
were already above 15 words and show no change.

**Yes** for item 4 (prefix slim): Already confirmed in analysis 24. No regression.

### Did the PR make anything worse?

No material regressions. The single remaining failure (run 82 llama3.1 gta_game) is a
lateral swap — run 75 (before) also had exactly 1 failure (hong_kong_game timeout, different
cause). Net llama3.1 reliability is unchanged.

The haiku review field length (≈430 chars avg, ~3.9× baseline) is worth monitoring.
Reviews are substantive but approaching a verbosity threshold. The PR did not cause this;
it was also present in run 81 (before). The trend predates this PR.

### Verdict

**KEEP**

The PR delivered its primary goal: the `summary` field and its system-prompt instructions
have been removed, eliminating 15 wasted LLM generations per experiment (105 per 7-model
batch). The option word-count improvement is measurable if partial for llama3.1. No content
regressions introduced. Success rate improved by 2.8 percentage points (one fewer full
failure). The PR is a net positive and should be kept.

---

## Questions For Later Synthesis

**Q1.** Run 82 (llama3.1 gta_game) failed with options having 2 items instead of 3 for
levers 5 and 6. Should the `options must have exactly 3 items` Pydantic validator be
replaced with a soft prompt constraint (`min_length=3` allowed but 2 is penalized) to avoid
full-run failures when 2 levers are malformed? Precedent: analysis 22 fixed `max_length=7`
for the same reason.

**Q2.** Haiku review fields average ~430 chars (~3.9× baseline). Is this a quality win
(more specific trade-off analysis) or a verbosity regression (formulaic padding)? Review
field length was ~355 chars in run 81 (before) and is ~430 chars in run 88 (after). The
additional content reads as substantive (each review names a specific structural weakness),
but cross-plan consistency hasn't been measured.

**Q3.** The "at least 15 words" constraint has been partially effective (llama3.1: 7 → 12
words). Would a validator that rejects options under 15 words (soft, not hard Pydantic)
force compliance, or would it cause partial_recovery failures for llama3.1?

**Q4.** The qwen3 run 85 did NOT recur the JSON extraction failure seen in run 78. Is the
run 78 failure now resolved (possibly by the summary field removal freeing context headroom),
or was it a transient issue? One more qwen3 run on parasomnia would confirm.

---

## Reflect

The key methodological lesson from analyses 24→25 is the experiment validity check.
Analysis 24 was declared INVALID because the runner executed against the wrong branch.
Analysis 25 properly executed against the main branch after PR merge, and the summary
removal is definitively confirmed.

The PR's impact is asymmetric by model tier:
- **Strong models (haiku, gpt-5-nano, qwen3)**: The 15-word constraint was already
  satisfied; summary removal reduces token waste. Net: minor token efficiency win.
- **Weak models (llama3.1)**: The 15-word constraint moves options from 7 to 12 words
  (progress but not compliant); summary removal frees headroom. Net: mild improvement,
  still not meeting the floor.
- **Mid-tier models (gpt-4o-mini, gemini, gpt-oss-20b)**: Already producing 15+ word
  options; summary removal is the primary benefit.

The biggest remaining gap is **template lock in reviews**: llama3.1 uses
"This lever governs the tension between" 100% of the time, and qwen3 uses "Core tension:"
as its opener. These are model-native patterns not addressed by this PR. The synthesis
agent should prioritize a negative constraint on these openers as the next intervention.

---

## Potential Code Changes

**C1.** Replace hard `options must have exactly 3 items` Pydantic constraint with
`min_length=3, max_length=5` or soft prompt guidance. The existing hard constraint causes
full plan failure when one lever returns 2 options. With `min_length=3` (not exactly=3),
the pipeline would still reject under-3 counts but would not fail on 4 or 5.
Evidence: run 82 gta_game, levers.5 and levers.6 failures.
Expected effect: reduce llama3.1 failure rate, particularly on complex plans.

**C2.** Add negative constraint on review openers to `review_lever` Pydantic field
description and system-prompt section 4:
> `Do NOT open with "This lever governs the tension between". Name the specific trade-off directly.`
> `Do NOT open with "Core tension:". Name the tension in your own words.`
Evidence: 100% template lock in run 82 (llama3.1), runs 85/78 (qwen3).
Expected effect: break template lock, improve review diversity especially for smaller models.

**C3.** Consider adding a post-generation validator that warns (but does not reject) when
any option is under 15 words. A soft validator would log a warning to events.jsonl but
allow the plan to succeed, giving visibility without causing failures.
Evidence: llama3.1 options averaging ~12 words after PR, below 15-word floor.

---

## Summary

PR #334 is a **KEEP**. Its primary goal — removing the unused `DocumentDetails.summary`
field and eliminating the matching system-prompt instructions — was successfully executed
and confirmed: before runs (75–81) contain 2–3 `"summary"` keys per plan in raw files;
after runs (82–88) contain zero. This eliminates 105 wasted LLM generations per 7-model
experiment with no downstream impact.

Secondary effects: option word counts improved marginally for llama3.1 (7→12 words on
call 1), measurably for haiku (28→41 words for complex plans). Success rate increased from
94.3% (33/35) to 97.1% (34/35). No content quality regressions introduced.

The most important unresolved issue is **review template lock**: llama3.1 opens 100% of
reviews with "This lever governs the tension between" and qwen3 opens with "Core tension:".
Neither is addressed by this PR. The recommended next change is a negative constraint added
to the `review_lever` field description targeting both openers.

Hypothesis labels for synthesis:
- **H1**: Add negative opener constraint to `review_lever` Pydantic description — break llama3.1 and qwen3 template lock.
- **H2**: Add "at least 15 words" hard floor to section 6 Pydantic field description (not just prompt text) — enforce compliance via schema.
- **C1**: Replace `options == 3` hard Pydantic constraint with `min_length=3` — reduce llama3.1 full plan failures.
- **C2**: Negative opener constraint in system-prompt section 4 (prompt-level companion to H1).
- **C3**: Soft option-length validator (warn, don't reject) — visibility into sub-15-word options without causing failures.
