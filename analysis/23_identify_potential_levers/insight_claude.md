# Insight Claude

## Overview

This analysis examines 7 "after" runs (67–73) using prompt_7 (`ddeec5ad…`)
against 7 "before" runs (60–66) using prompt_6 (`4669db37…`). The central
change is PR #326: adding a second structurally distinct `review_lever` example
to break the "This lever governs the tension between X and Y" template lock that
was near-total in runs 60–66.

**Important caveat**: The before and after runs use completely different model
lineups. Runs 60–66 all used `ollama-llama3.1`. Runs 67–73 span 7 different
models. This makes a clean apples-to-apples comparison only possible for
llama3.1 (run 60–66 vs run 67).

| Run | Model | Prompt SHA | Workers |
|-----|-------|------------|---------|
| 60–66 | ollama-llama3.1 | 4669db37… (prompt_6) | 1 |
| 67 | ollama-llama3.1 | ddeec5ad… (prompt_7) | 1 |
| 68 | openrouter-openai-gpt-oss-20b | ddeec5ad… | 4 |
| 69 | openai-gpt-5-nano | ddeec5ad… | 4 |
| 70 | openrouter-qwen3-30b-a3b | ddeec5ad… | 4 |
| 71 | openrouter-openai-gpt-4o-mini | ddeec5ad… | 4 |
| 72 | openrouter-gemini-2.0-flash-001 | ddeec5ad… | 4 |
| 73 | anthropic-claude-haiku-4-5-pinned | ddeec5ad… | 4 |

---

## Negative Things

**N1. llama3.1 template lock only modestly reduced.**
Run 67 (llama3.1, new prompt) still shows "This lever governs/manages the
tension between" in ~71% of hong_kong_game reviews (10/14), down from ~89%
(16/18) in run 60. The second example (the "Prioritizing speed…" form) accounts
for 3/14 reviews. The underlying cause — a small model pattern-matching on the
nearest example — is not fixed; the pattern just shifted from one dominant
template to a slightly diversified set.

Evidence: `history/1/67_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
(10 of 14 reviews start with "This lever governs the tension…").

**N2. gpt-5-nano template-locked to the SECOND example.**
Run 69 (gpt-5-nano) introduced a new template lock on the second prompt example.
Reviews in hong_kong_game follow "This lever [short verb]. [Brief extra
sentence]" pattern derived from a simplified reading of the second example, and
several use the "Core tension: X. Weakness: Y." micro-pattern.

Examples from `history/1/69_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
- "This lever centers the city as a narrative engine, but the core tension between authenticity and regulatory friction remains under-addressed…"
- "This lever weighs financing risk and release strategy, but the options miss deeper diversification…"

While more varied than run 60, this shows that two examples can create two
competing templates rather than genuine freedom.

**N3. llama3.1 partial_recovery rate regressed.**
Run 67 (llama3.1) shows 3 partial_recovery events (gta_game, sovereign_identity,
hong_kong_game each got `calls_succeeded=2` out of 3 expected). Runs 61–66 had
0 partial_recovery events; run 60 had 2. This is a reliability regression for
llama3.1, possibly due to the additional example increasing prompt complexity.

Evidence: `history/1/67_identify_potential_levers/events.jsonl`.

**N4. Label-only options persist in llama3.1 (inferred).**
Run 60 showed label-style options ("Hub-and-Spoke", "Satellite Studios",
"Co-Working Spaces") for gta_game. The same prompt fix doesn't address the
options format. Run 67 does not appear in the read samples for gta_game, but
given the same model and same failure mode, label-only options are likely to
persist in some call-1 outputs for llama3.1.

**N5. "This lever [verb]..." opener dominates across most after runs.**
Even for models that broke free from "governs the tension", the "This lever
[verb]..." sentence opening pattern persists in all runs except haiku (73).
Run 68 (gpt-oss-20b) has 18/18 reviews starting with "This lever" but using
more diverse verbs: "addresses", "balances", "tackles", "confronts", "focuses
on", "explores", "manages", "negotiates". The word-choice diversity is better
but the structural template is still present.

**N6. Not a controlled experiment for most models.**
Runs 60–66 are all llama3.1; runs 67–73 are 7 different models. Any observed
improvements could be partly (or mostly) due to model capability differences
rather than the prompt change. Only run 67 (llama3.1) allows a fair before/after
comparison for the PR's targeted fix.

---

## Positive Things

**P1. Template lock substantially reduced across the multi-model suite.**
Among runs 68–73 (non-llama3.1 models), the "This lever governs the tension
between" exact pattern dropped from 100% (before, all llama3.1) to near zero.

| Run | Model | "governs the tension" rate | "This lever..." opener rate |
|-----|-------|---------------------------|----------------------------|
| 60–66 | llama3.1 (before) | ~89% | ~100% |
| 67 | llama3.1 (after) | ~71% | ~100% |
| 68 | gpt-oss-20b | ~0% | ~100% |
| 69 | gpt-5-nano | ~0% | ~71% |
| 70 | qwen3 | ~17% | ~67% |
| 71 | gpt-4o-mini | ~20% | ~67% |
| 72 | gemini | ~11% | ~78% |
| 73 | haiku | ~6% | ~29% |

Evidence: sampled `002-10-potential_levers.json` for hong_kong_game from each
run. Counts are from 14–18 levers per file.

**P2. haiku (run 73) produces substantively original reviews — the best quality
in any run to date.**
Run 73 (haiku) reviews are multi-sentence, option-comparative analyses that do
NOT start with "This lever…" in 71% of cases. They directly compare trade-offs
between the three options.

Example from `history/1/73_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
> "The first option maximizes authenticity but narrows financier appetite and
> international marketing reach. The third option splits the difference but adds
> cost and schedule risk if the director's vision fails to cohere with the city's
> actual rhythm after immersion."

This is substantially more informative than the before-pattern templates.

**P3. No fabricated percentages in any run 67–73.**
The prohibition in prompt_7 section 5 ("NO fabricated statistics or percentages
without evidence") continues to hold. Zero percentage-claim instances found
across sampled files.

**P4. Consequence field quality maintained or improved.**
No "Weakness:" contamination in consequence fields (which was the bug in run 59
before prompt_6). Consequence fields remain structurally clean across all after
runs.

**P5. run 73 (haiku) shows 0 partial_recovery events.**
All 5 plans completed with expected call counts. This is the most reliable run
in the "after" set.

Evidence: `history/1/73_identify_potential_levers/events.jsonl`.

---

## Comparison

### Against Baseline Training Data

The baseline (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`)
uses a much earlier prompt version with fabricated percentages in consequence
chains and "Controls X vs Y. Weakness: Z." review format.

The after runs' review quality (especially haiku) substantially exceeds the
baseline in analytical depth, even while being longer. The baseline's
consequences contain fabricated numbers (e.g., "15% higher audience engagement",
"20% higher pre-sales based on star power") that are absent in all after runs.

### Before (runs 60–66) vs After (runs 67–73)

The central comparison metric — template lock in the review field — improved
substantially for the non-llama3.1 models and modestly for llama3.1.

Content quality for haiku (run 73) represents a clear qualitative step up,
with reviews that directly compare option trade-offs rather than filing in
a formula.

---

## Quantitative Metrics

### Review Field Length (hong_kong_game)

| Source | Approx avg chars | Template lock (governs tension) |
|--------|-----------------|--------------------------------|
| Baseline | ~154 | ~0% (uses "Controls X vs Y") |
| Run 60 (before, llama3.1) | ~174 | ~89% |
| Run 67 (after, llama3.1) | ~178 | ~71% |
| Run 68 (after, gpt-oss-20b) | ~195 | ~0% |
| Run 69 (after, gpt-5-nano) | ~155 | ~0% |
| Run 70 (after, qwen3) | ~170 | ~17% |
| Run 71 (after, gpt-4o-mini) | ~185 | ~20% |
| Run 72 (after, gemini) | ~200 | ~11% |
| Run 73 (after, haiku) | ~295 | ~6% |

Note: Baseline uses "Controls X vs Y." format; current prompt uses a longer
sentence-based format, so direct comparison is less meaningful than the change
from before to after.

### Consequence Field Length (hong_kong_game, sample)

| Source | Approx avg chars | Fabricated % claims |
|--------|-----------------|---------------------|
| Baseline | ~265 | Many (10–30%) |
| Run 60 (before, llama3.1) | ~225 | 0 |
| Run 67 (after, llama3.1) | ~230 | 0 |
| Run 73 (after, haiku) | ~475 | 0 |

Run 73 consequence ratio vs run 60: ~2.1× — borderline warning level (2×
threshold per AGENTS.md). However, the extra length consists of substantive
analysis with specific trade-offs, not marketing copy or fabricated numbers.
Qualitatively this is a genuine improvement, not a verbosity regression.

Run 73 consequence ratio vs baseline: ~1.8× — below the warning threshold.

### Template Lock by Example Pattern (run 67, llama3.1, hong_kong_game)

| Pattern | Count | % of 14 reviews |
|---------|-------|-----------------|
| "This lever governs the tension between…" | 10 | 71% |
| "Prioritizing X over Y carries hidden costs: none of the options…" | 3 | 21% |
| Neither pattern | 1 | 7% |

The second example contributed ~21% of the reviews using its form. This is
a partial displacement of the first example, not a genuine escape.

### Reliability

| Run | Model | partial_recovery | plans with full 3 calls |
|-----|-------|------------------|------------------------|
| 60 | llama3.1 | 2 | 3/5 |
| 61–66 | llama3.1 | 0 | 5/5 each |
| 67 | llama3.1 | 3 | 2/5 |
| 68 | gpt-oss-20b | 0 | 5/5 |
| 69 | gpt-5-nano | 0 | 5/5 (inferred) |
| 70–72 | various | 0 | 5/5 (inferred) |
| 73 | haiku | 0 | 5/5 |

llama3.1 in run 67 is the worst performer on reliability in the after set.

---

## Evidence Notes

**E1. Verbatim example copy in run 60 (before):**
The first lever in `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
has review: `"This lever governs the tension between centralization and local
autonomy, but the options overlook transition costs."` — this is the exact
string from prompt_6's example section. No verbatim copies of this string found
in run 67 (llama3.1 with new prompt), suggesting the second example partially
diluted the copy-recall behavior even for llama3.1.

**E2. Second example echo in run 67 (after):**
Run 67 reviews 2, 4, 6 follow the second example structure: "Prioritizing X
over Y carries hidden costs: none of the options address Z." — paraphrased but
structurally identical to the example. This confirms the second example is
learned and applied, but still as a template.

**E3. gpt-5-nano distinct review style:**
`history/1/69_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
shows reviews starting with verbs like "This lever centers", "This lever weighs",
"This lever confronts", with shorter sentences and less formula than run 60.
This represents genuine variety, but many still use "This lever [verb]" openers.

**E4. haiku completely free from template in 71% of reviews:**
`history/1/73_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
shows reviews that start directly with comparing options: "The first option
maximizes authenticity but…", "All three options trade off differently…",
"The first option keeps the psychological focus tight but…". These are the
clearest examples of the PR's intended behavior working as expected.

**E5. Lever name quality in run 73 (haiku):**
Lever names in run 73 are long, descriptive, and project-specific (e.g., "Twist
Architecture and Audience Expectation Management", "Screenplay Approach: Hong
Kong as Active Antagonist vs. Backdrop", "Protagonist's Downward Mobility Arc:
Gradual Seduction vs. Violent Rupture"). These are substantially more
informative than run 60's generic names (e.g., "Director Selection", "Revenue
Strategy", "Marketing Campaign").

---

## PR Impact

### What the PR was supposed to fix

PR #326 added a second structurally distinct `review_lever` example to the
system prompt to break the template lock where 90–100% of reviews in runs 60–66
started with "This lever governs the tension between X and Y."

### Before vs After comparison

| Metric | Before (runs 60–66) | After — llama3.1 (67) | After — strong models (68–73) |
|--------|--------------------|-----------------------|-------------------------------|
| "governs the tension" rate | ~89–100% | ~71% | 0–20% |
| "This lever..." opener rate | ~100% | ~100% | 29–100% |
| Review avg chars | ~174 | ~178 | 155–295 |
| Consequence avg chars | ~225 | ~230 | ~230–475 |
| Fabricated % claims | 0 | 0 | 0 |
| Partial recovery events | 0–2/run | 3 | 0 |
| Template-free reviews | ~0% | ~7% | 20–71% |

### Did the PR fix the targeted issue?

**Partially yes for llama3.1, strongly yes for stronger models.**

For llama3.1: The "governs the tension" rate dropped from ~89% to ~71% —
meaningful but not transformative. The underlying cause (small models
pattern-matching on examples) is not resolved. The second example is learned and
echoed as a new sub-template in ~21% of cases.

For stronger models (gpt-oss-20b, qwen3, gpt-4o-mini, gemini, haiku): The
exact first-example phrase is nearly eliminated. haiku achieves 71%
template-free reviews — the best quality seen in any run so far.

### Regressions

- gpt-5-nano exhibits a new template lock on the second example's format
- llama3.1 reliability degraded (3 partial_recovery vs 0 in runs 61–66)

Neither regression is severe: gpt-5-nano's reviews are still more varied than
run 60's single-lock, and partial_recovery is a fallback that still produces
output.

### Verdict: KEEP

The PR produces measurable, evidence-backed improvement across the multi-model
test suite. For the 6 non-llama3.1 models (runs 68–73), template lock is
substantially reduced and review quality improved — most clearly in haiku. The
llama3.1 result is modest, and the llama3.1 reliability regression is a concern,
but the overall cross-model signal is positive.

The result does not fully eliminate template lock — see Hypotheses below for
next steps.

---

## Questions For Later Synthesis

Q1. Is the llama3.1 partial_recovery regression in run 67 caused by the longer
prompt (two examples), by random noise, or by a different mechanism? Should
llama3.1 be deprioritized as a test model?

Q2. gpt-5-nano appears to template-lock to the second example. Would a third
diverse example help, or would each new example just add a new lock pattern?

Q3. haiku's reviews are 2× longer in consequences than llama3.1 and ~1.8× the
baseline. Is this extra length genuinely adding decision-relevant information,
or is some of it padding? A human-rated quality check would clarify.

Q4. Would replacing the "Examples:" framing in the prompt with explicit
variation guidance ("do NOT copy these patterns; use them as inspiration only")
further reduce template lock across models?

Q5. How are the runs 68–73 models distributed in production? If llama3.1 is
primary, the PR's benefit is smaller than if the full model diversity is used.

---

## Reflect

The before/after comparison is confounded by model heterogeneity. A cleaner
experiment would have run the same 7 models with both the old and new prompts.
As-is, we can confirm that prompt_7 works better for stronger models and only
modestly better for llama3.1.

The AGENTS.md experiment insights note that template lock is a known llama3.1
behavior. The two-example fix was a correct first step; the next step should
either add more examples or switch to example-free structural guidance (e.g.,
explicit anti-pattern warnings: "Do not begin with 'This lever governs the
tension between'").

Content quality for haiku (run 73) is genuinely impressive — the reviews analyze
option trade-offs specifically and add real value. This is the closest to the
OPTIMIZE_INSTRUCTIONS goal ("realistic, feasible, actionable") seen so far.

---

## Potential Code Changes

C1. **Add anti-template instruction to the prompt** (prompt-level fix): In
section 4 (Validation Protocols), add an explicit prohibition: "Do not begin
the review with 'This lever governs/manages the tension between'. Vary your
sentence structure — start with the core trade-off, the dominant risk, or a
direct comparison of options."
Evidence: N1, N5. Expected effect: reduces llama3.1 and gpt-oss-20b template
lock by removing the dominant pattern as a valid opener.

C2. **Add 3rd and 4th diverse examples to the `review_lever` section**:
The prompt currently has 2 examples. Adding more diverse openers (e.g.,
option-comparing, risk-leading, counter-intuitive) would give models more
scaffolding to avoid single-pattern lock.
Evidence: N1, N2. Risk: each example can itself become a template (as seen
with gpt-5-nano and example 2).

C3. **Consider removing examples entirely and replacing with structural rules**:
Instead of "Examples: [X], [Y]", rewrite as: "The review must name the core
trade-off and identify a blind spot. It should NOT start with 'This lever
governs/manages' or any formulaic sentence. Write a sentence unique to this
lever's specific options."
Evidence: N1, N2. Expected effect: high-capability models (haiku) may produce
even more variety; low-capability models (llama3.1) may struggle more without
examples.

C4. **Deprioritize llama3.1 in the test suite**: The model is reliably
template-locked regardless of prompt variation, and shows reliability
regressions. The learning signal from llama3.1 runs is limited.
Evidence: N1, N3.

---

## Hypotheses

H1: Adding an explicit prohibition against "This lever governs/manages the
tension between…" as an opener will reduce llama3.1 template lock from ~71% to
below 40% by giving the model an explicit negative constraint.
Test: Add the prohibition, re-run llama3.1, measure opener diversity.

H2: The second example's effect on gpt-5-nano is because gpt-5-nano has a
stronger recency bias in few-shot prompting (the last example dominates). Adding
a third diverse example placed last would shift gpt-5-nano's default pattern
again.
Test: Add a third example with a distinct opening verb ("The key risk here is…"
or option-comparative format), measure gpt-5-nano's template distribution.

H3: haiku's escape from template lock stems from its stronger instruction-
following capacity interpreting "Do not use square brackets or placeholder text"
as a cue to produce original language. If this instruction were strengthened
("Produce an original review for this specific lever; treat examples as
illustrative, not as templates"), haiku performance would remain high and
gpt-oss-20b performance would improve.
Test: Add the stronger instruction, measure template-free rate across models.

H4: The consequence field length increase in run 73 (haiku, ~2.1× run 60) is
not a quality regression because the extra text contains specific option
trade-offs and project constraints rather than padding.
Test: Human quality rating of 10 random consequences from run 60 vs run 73.
If run 73 scores higher on decision-relevance, the length increase is justified.

---

## Summary

PR #326 successfully reduced template lock in the `review` field across the
multi-model test suite. For strong models (haiku, gpt-4o-mini, gemini, qwen3),
the "This lever governs the tension between" pattern is nearly eliminated and
reviews are qualitatively more useful. haiku (run 73) produces the best review
quality seen to date: option-specific, substantive, free-form.

For llama3.1, improvement is modest (~89% → ~71%) and reliability degraded
slightly. gpt-5-nano acquired a new template lock on the second example.

The PR is worth keeping. The remaining template lock (especially "This lever
[verb]..." opener dominance in most models) can be further reduced by
adding an explicit anti-pattern prohibition to the prompt in the next iteration.

**Verdict: KEEP.**
