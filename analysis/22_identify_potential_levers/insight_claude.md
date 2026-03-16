# Insight Claude

## Overview

Analyzed runs 60–66 (post-PR #316, single-example review_lever format) against run 59
(the only pre-PR llama3.1 run with the old prompt). All current runs use `ollama-llama3.1`
with prompt SHA `4669db37…`. The previous analysis (21) covered runs 53–59 with mixed
models; only run 59 (llama3.1 + old prompt SHA `9c5b2a0d…`) provides a true
apples-to-apples comparison.

**Model assignments:**

| Run | Model | Prompt |
|-----|-------|--------|
| 59 | ollama-llama3.1 | OLD (9c5b2a0d…) |
| 60–66 | ollama-llama3.1 | NEW (4669db37…) |

Runs 53–58 (qwen3, gpt-oss-20b, gpt-5-nano, gpt-4o-mini, gemini, haiku) with the old
prompt provide context on other models but are not directly comparable for this PR's
targeted fix.

---

## Positive Things

**P1. Validation errors no longer silently corrupt consequences.**
Run 59 (OLD prompt, llama3.1) shows "Weakness:" text leaking into the `consequences`
field — e.g., lever "Location Sourcing" consequences: "…potentially delaying production.
Weakness: The plan does not account for the possibility of location scouting taking
longer than anticipated." This is structurally wrong content in the wrong field.
Runs 60–66 (NEW prompt) show clean consequences without "Weakness:" contamination.
Evidence: `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`,
`history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`.

**P2. call-1 validation success improved from run 60 onward.**
Run 60 shows 2 `partial_recovery` events (silo: calls_succeeded=2, parasomnia:
calls_succeeded=2). Runs 61–66 show zero `partial_recovery` events with all plans
reporting calls_succeeded=3. The new single-sentence format appears simpler to
produce consistently, reducing schema validation failures in the second through seventh
runs.
Evidence: `history/1/60_identify_potential_levers/events.jsonl`,
`history/1/61_identify_potential_levers/events.jsonl` through `66`.

**P3. No fabricated percentages in any run 60–66 output.**
Checked `002-10-potential_levers.json` for gta_game and hong_kong_game across runs 60,
61. No numeric percentage or cost-delta claims found. This continues the PR #313
improvement documented in analysis 21.

**P4. Review field length improved over old llama3.1 output.**
Run 59 hong_kong_game reviews (OLD): ~90–115 chars each.
Run 60 hong_kong_game reviews (NEW): ~150–190 chars each.
The new format's complete sentence structure ("This lever governs… but the options
overlook…") naturally produces a more substantive review than the clipped "X vs Y.
Weakness: Z." format of run 59.

**P5. Consequence field quality is cleaner.**
Run 59 consequences frequently include a dangling "Weakness:" clause that belongs
in `review_lever`. Run 60 consequences are structurally clean, focusing on direct
effects and downstream implications. Example run 60 gta_game consequence: "Establishing
a primary development location in Los Angeles would provide access to existing talent
pools and industry connections, but might limit the team's ability to attract diverse
perspectives from other cities. Downstream, this could result in a more localized game
experience."

---

## Negative Things

**N1. Template leakage replaced old template with new template — different pattern, same problem.**
Run 59 (OLD): ALL reviews follow "X vs Y. Weakness: The plan/options [assume/fail to
account for]…" — 100% formulaic.
Runs 60–66 (NEW): ALL reviews follow "This lever governs/manages the tension between
X and Y, but the options overlook/underestimate/miss/neglect Z." — also 100% formulaic.
The fix substituted one rigid template for another. The root cause (llama3.1 pattern-matches
on the single given example and applies it universally) is untreated.
Evidence: `history/1/60_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
(18/18 reviews follow the new pattern).

**N2. Verbatim copy of prompt example in run 60 gta_game.**
The first lever in run 60's gta_game output has `review` field:
`"This lever governs the tension between centralization and local autonomy, but the
options overlook transition costs."`
This is the exact example string from the prompt under section 4 (Validation Protocols).
The model reproduced the example text directly for a real lever, confusing example as
output rather than as guide.
Evidence: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`,
lever "Location Strategy". Prompt: `prompts/identify_potential_levers/prompt_6_4669db3…txt`.

**N3. Label-only options in call-1 output for gta_game (run 60).**
The same run 60 gta_game call-1 output has options like `"Hub-and-Spoke"`, `"Satellite
Studios"`, `"Co-Working Spaces"` — single-phrase labels rather than "complete strategic
approaches." The prompt explicitly prohibits "NO generic option labels (e.g., 'Optimize
X', 'Tolerate Y')" and requires "Each option should be a concrete, actionable approach."
These options survive into the final `002-10-potential_levers.json` (call-2/3 levers
have full sentences, but merged results retain the label-style options from call-1).
Evidence: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`,
lever_index 1 "Location Strategy".

**N4. Duplicate/near-duplicate lever names persist.**
Run 60 gta_game (20 levers after dedup) contains: "Partnership Model", "Partnership
Structure", "Partnership Ecosystem" — three separate levers covering partnerships.
Similarly: "Talent Acquisition" and "Talent Attraction" appear as separate levers.
The deduplication step removes exact-match duplicates but not near-duplicates covering
the same strategic topic. This inflates lever count without adding coverage.
Evidence: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

**N5. Run 60 partial_recovery: first run after PR still had 2/5 plan failures.**
The silo and parasomnia plans in run 60 show calls_succeeded=2 rather than 3. The
partial_recovery events confirm at least one call-1 output failed schema validation.
While runs 61–66 show clean success, the first post-PR run was not clean.
Note: The `calls_succeeded` field was not present in pre-PR outputs.jsonl (runs 53–59),
so a direct before/after success-rate comparison is not possible from the logged data.
Evidence: `history/1/60_identify_potential_levers/events.jsonl`.

**N6. All calls set `strategic_rationale: null` (call-1 gta_game run 60).**
The raw response shows `"strategic_rationale": null`. This field was intended to capture
the model's reasoning about lever selection. Its consistent nullification suggests llama3.1
does not produce this field and the schema allows it as optional. Loss of this field
means the reviewer cannot verify whether levers are chosen strategically or arbitrarily.
Evidence: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`,
response[0] `strategic_rationale: null`.

---

## Comparison

### llama3.1 Before vs. After

| Dimension | Run 59 (OLD prompt) | Runs 60–66 (NEW prompt) |
|-----------|--------------------|-----------------------|
| Review format | "X vs Y. Weakness: …" | "This lever governs tension between X and Y, but Z" |
| "Weakness:" in consequences | Yes (structural contamination) | No |
| Verbatim example copy | N/A | 1 lever (run 60 gta_game) |
| Template leakage rate (review) | ~100% | ~100% |
| Fabricated percentages | 0 | 0 |
| Label-style options | Some | Some (run 60 call-1) |
| calls_succeeded (observable) | Not logged | 13/15 run 60; 15/15 runs 61–66 |
| Avg review length (hong_kong) | ~100 chars | ~165 chars |
| Lever count (hong_kong) | 12 | 18 |
| Lever count (gta_game) | 21 | 20 |
| Lever count (parasomnia) | ~12 (est.) | 13 (partial, 2 calls) |

### Comparison to Baseline
The baseline training data (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`)
was generated with a very old prompt version and contains 13+ fabricated percentage
claims using the "Immediate → Systemic → Strategic" consequence chain format (per
analysis 21's P4 finding). Current runs (60–66) have cleaner consequences with no
fabricated numbers, so they are substantively ahead of the old baseline in those dimensions.

Baseline consequences for hong_kong_game: ~240 chars.
Run 60 hong_kong_game consequences: ~250 chars.
Run 59 hong_kong_game consequences: ~200 chars (but includes "Weakness:" contamination).

---

## Quantitative Metrics

### Review Template Leakage

| Run | Plan | Total Levers | Reviews starting "This lever governs/manages…" | Exact example copy |
|-----|------|-------------|-----------------------------------------------|-------------------|
| 59 (OLD) | hong_kong_game | 12 | 0 | 0 |
| 59 (OLD) | gta_game | 21 | 0 | 0 |
| 60 (NEW) | hong_kong_game | 18 | 17/18 = 94% | 0 |
| 60 (NEW) | gta_game | 20 | 18/20 = 90% | 1 (exact match) |
| 60 (NEW) | parasomnia | 13 | 13/13 = 100% | 0 |

(All current runs show near-identical review patterns — only run 60 sampled for brevity.)

### Old Template Leakage (run 59)

| Plan | Total Levers | Reviews with "The plan assumes…" boilerplate | "Weakness:" in consequences |
|------|-------------|---------------------------------------------|---------------------------|
| hong_kong_game | 12 | 8/12 = 67% | 8/12 = 67% |
| gta_game | 21 | 21/21 = 100% | 0 |

### calls_succeeded Summary (current runs only)

| Run | silo | gta | sovereign | hong_kong | parasomnia | Total |
|-----|------|-----|-----------|-----------|------------|-------|
| 60 | 2* | 3 | 3 | 3 | 2* | 13/15 |
| 61 | 3 | 3 | 3 | 3 | 3 | 15/15 |
| 62 | 3 | 3 | 3 | 3 | 3 | 15/15 |
| 63 | 3 | 3 | 3 | 3 | 3 | 15/15 |
| 64 | 3 | 3 | 3 | 3 | 3 | 15/15 |
| 65 | 3 | 3 | 3 | 3 | 3 | 15/15 |
| 66 | 3 | 3 | 3 | 3 | 3 | 15/15 |

*partial_recovery events. Overall: 103/105 = 98.1%.

### Average Field Lengths (hong_kong_game, sampled levers)

| Source | Consequences (chars) | Review (chars) | Option avg (chars) |
|--------|---------------------|---------------|-------------------|
| Baseline | ~240 | ~145 | ~90 |
| Run 59 (OLD llama3.1) | ~200 | ~100 | ~80 |
| Run 60 (NEW llama3.1) | ~255 | ~165 | ~100 |

All ratios are within 1.1× of baseline length — no verbosity regression.

### Constraint Violations

| Run | Label-only options (<30 chars) | Options with prefix labels | Exact example copy |
|-----|-------------------------------|---------------------------|-------------------|
| 59 | ~3 | 0 | 0 |
| 60 | ~5 (call-1 gta, silo) | 0 | 1 |
| 61–66 | ~2 avg | 0 | 0 est. |

---

## Evidence Notes

1. **Verbatim example**: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   lever "Location Strategy", `review` field = "This lever governs the tension between
   centralization and local autonomy, but the options overlook transition costs." —
   exact match to prompt text in section 4.

2. **"Weakness:" in consequences (old format)**: `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
   lever "Location Sourcing" consequences includes "Weakness: The plan does not
   account for…". This contamination does not appear in any run 60–66 output.

3. **Label options (new format)**: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`
   lever "Location Strategy" options: ["Hub-and-Spoke", "Satellite Studios",
   "Co-Working Spaces"] — one-phrase labels, not actionable descriptions.

4. **Near-duplicate levers**: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   contains "Partnership Model", "Partnership Structure", "Partnership Ecosystem" as
   distinct levers — covering the same strategic space.

5. **Partial recovery**: `history/1/60_identify_potential_levers/events.jsonl` shows:
   `{"event": "partial_recovery", "plan_name": "20250321_silo", "calls_succeeded": 2,
   "expected_calls": 3}` and the same for parasomnia. No such events in runs 61–66.

6. **Baseline fabrication**: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`
   contains "15% higher audience engagement", "20% higher pre-sales", "30% increase
   in streaming revenue" — fabricated numbers from the old unoptimized prompt. Current
   runs show no such fabrications.

---

## PR Impact

### What the PR Was Supposed to Fix

PR #316 replaced the `review_lever` field description's "First sentence… / Second
sentence…" two-bullet format with a single flowing example:
> "This lever governs the tension between centralization and local autonomy, but the
> options overlook transition costs."

The motivation: llama3.1 interprets the two-bullet format as two *alternative* formats
rather than one required format, causing call-1 validation failures.

### Before vs. After Comparison Table

| Metric | Before (run 59, llama3.1 + old) | After (runs 60–66, llama3.1 + new) | Change |
|--------|--------------------------------|-------------------------------------|--------|
| "Weakness:" in consequences | Present (67% of hong_kong levers) | Eliminated | ✅ Fixed |
| Review format follows example | Two-part "X vs Y. Weakness: Z" | "This lever governs… but…" | Changed |
| Template leakage (review) | ~100% formulaic | ~100% formulaic | ➡ Same |
| Verbatim prompt example copy | None | 1 case (run 60 gta_game) | ❌ Worse |
| Label-style options | Present in some calls | Present in some calls (run 60) | ➡ Same |
| calls_succeeded=3 rate (logged) | Not logged | 98.1% (103/105) | ✅ Improved |
| No partial_recovery | Runs 61–66: 0 | Runs 61–66: 0 | ✅ Clean |
| Fabricated percentages | 0 | 0 | ➡ Same |
| Near-duplicate lever names | Present | Present | ➡ Same |

### Did the PR Fix the Targeted Issue?

**Yes, with caveats.** The structural problem (old format causing "Weakness:" to appear
in the `consequences` field) is eliminated in all runs 60–66. The review_lever field
now consistently produces a single grammatically complete sentence matching the example's
structure. Runs 61–66 show 100% call success rate (no partial_recovery), consistent with
fewer schema validation failures.

**However**, the PR replaced one template-leakage pattern with another. The model does
not understand the review_lever *concept* — it pattern-matches on the *syntax* of the
example. A different example with different syntax would produce different-but-equally-
formulaic output. The underlying issue (single example → single template) persists.

One regression: run 60 gta_game copied the example text verbatim into a real lever's
review, which is a template leakage failure the old format did not exhibit.

### Regressions

- **Verbatim example copy** (N2): New format enables a more direct copy failure mode.
- **Run 60 partial recovery** (N5): First post-PR run still had 2/5 plan failures —
  though unclear if this reflects a pre-existing issue now made visible by new logging.

### Verdict

**CONDITIONAL** — The PR fixes the structural contamination problem (Weakness: in
consequences) and appears to improve call reliability for llama3.1 (0 partial_recovery
in runs 61–66). However, the new single-sentence example produces a new template-leakage
pattern equally rigid as the old one, plus a new failure mode (verbatim copy). The fix
is directionally correct but incomplete. A follow-up hypothesis (H1 below) is needed
to break the single-template lock.

---

## Questions For Later Synthesis

1. Was the `partial_recovery` event and `calls_succeeded` field added to the runner
   simultaneously with PR #316, or independently? If added simultaneously, partial
   failures in run 59 were always happening — they were just not logged.

2. Do runs 61–66 genuinely show zero call-1 validation failures, or did the runner's
   retry logic silently absorb them after adding the new single-sentence format?

3. Are the label-style options ("Hub-and-Spoke", "Satellite Studios") a llama3.1 artifact
   specific to certain plans (gta_game being a concrete product with recognizable industry
   terms), or does it occur across all plans?

4. Can we confirm that the near-duplicate lever names ("Partnership Model", "Partnership
   Structure", "Partnership Ecosystem") are consistent across runs 61–66 for gta_game,
   or is it run-specific?

---

## Reflect

The PR correctly identified that a two-part example causes format confusion in weaker
models. But the solution (one flowing example) still gives the model a syntactic template
to latch onto. The fundamental problem is that any single example creates a single
template. A model like llama3.1 that relies heavily on in-context pattern matching will
repeat the pattern regardless of semantic instructions to vary it.

The analysis also reveals that `strategic_rationale: null` across all call-1 responses
suggests llama3.1 systematically ignores that field. If the strategic_rationale was
intended to guide lever selection quality, its loss is a content quality gap invisible
in the final output.

The OPTIMIZE_INSTRUCTIONS goal of "realistic, feasible, actionable plans" is partially
met: the current reviews are more substantive than run 59's boilerplate, but the formulaic
"tension between X and Y, but overlook Z" pattern does not distinguish well between
genuinely high-stakes levers and minor tactical choices.

---

## Potential Code Changes

**H1** (Prompt): Provide 2–3 varied review examples with different sentence structures
to prevent the model from pattern-matching on a single template. One example could use
"Controls" language, another "Governs", another a direct assertion, forcing the model
to express the concept rather than copy the syntax.
*Expected effect*: Reduced "This lever governs the tension between…" prefix rate from
~95% to <50%.
*Evidence*: N1, run 60 where 17/18 reviews start with identical prefix.

**H2** (Prompt): Add an explicit prohibition in section 5 (Prohibitions): "Do not
start your review with 'This lever governs the tension between' — vary the opening."
And: "Do not copy the example text literally into your output."
*Expected effect*: Eliminates verbatim example copying; reduces but does not eliminate
template leakage.
*Evidence*: N2, verbatim copy in run 60 gta_game.

**H3** (Prompt): Move the review_lever example into the schema field description
(Pydantic docstring level) rather than the system prompt, so it appears at the exact
point the model is filling that field rather than at a distance in the system prompt.
*Expected effect*: Example is more precisely anchored, less likely to be confused with
output in earlier levergeneration (call-1).
*Evidence*: N2, the verbatim copy happened in call-1 output.

**C1** (Code): Add a validator that checks `review_lever` for exact match against any
prompt example strings, rejecting verbatim copies.
*Expected effect*: Eliminates the N2 failure mode.
*Evidence*: N2, `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

**C2** (Code): Add a validator that flags label-style options (strings <30 chars with
no verb). Options like "Hub-and-Spoke" do not meet the prompt's "complete strategic
approach" requirement.
*Expected effect*: Forces retry when call-1 produces label-only options; improves
downstream option quality for weaker models.
*Evidence*: N3, run 60 gta_game call-1 options.

**C3** (Code): Check if `strategic_rationale` being null should trigger a soft warning
or affect lever quality scoring. If the field is consistently null for llama3.1, consider
removing it from the schema to eliminate confusion, or making it a required non-null
string with a minimum length.
*Evidence*: N6, `strategic_rationale: null` in run 60 gta_game call-1.

**C4** (Code/OPTIMIZE_INSTRUCTIONS): Document the new failure mode observed here —
"single-example template lock: when the prompt provides exactly one format example,
weaker models will reproduce that exact format in every output, eliminating diversity.
Provide ≥2 varied examples or add a do-not-copy prohibition." Add to OPTIMIZE_INSTRUCTIONS
known-problems list.
*Evidence*: N1, N2.

---

## Summary

PR #316 successfully eliminated the "Weakness: in consequences" contamination pattern
present in run 59 (llama3.1 + old prompt) and improved call success rates (0/5 partial
recoveries in runs 61–66). The new single-sentence review example is structurally
simpler and easier for llama3.1 to produce without format confusion.

However, the PR introduced a new problem: all reviews now follow "This lever governs
the tension between X and Y, but the options overlook Z" — a rigid new template that
is just as formulaic as the old one. One lever in run 60 gta_game copied the example
verbatim, which is a form of template leakage not present before.

Verdict: **CONDITIONAL KEEP**. The core fix (structural format improvement) is valid
and should be retained. The follow-up work (H1/H2 above) is needed to break the
single-template pattern-matching behavior in llama3.1.
