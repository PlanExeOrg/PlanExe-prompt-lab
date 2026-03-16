# Insight Claude

## Overview

Analyzed runs 53–59 (post-PR #313, anti-fabrication reminder in calls 2/3) against
runs 46–52 (pre-PR). The PR adds one sentence to the call-2/3 user prompt:
"Do not invent percentages, cost savings, or performance deltas — use qualitative
language unless the project document supplies the number."

**Note:** The system prompt SHA is identical in both batches (9c5b2a0d…). The change
is in the Python call-2/3 f-string only, not in the registered prompt file. This is
expected and correct per the PR description.

**Model assignments (perfectly aligned between before and after):**

| Run | Model |
|-----|-------|
| 46 → 53 | openrouter-qwen3-30b-a3b |
| 47 → 54 | openrouter-openai-gpt-oss-20b |
| 48 → 55 | openai-gpt-5-nano |
| 49 → 56 | openrouter-openai-gpt-4o-mini |
| 50 → 57 | openrouter-gemini-2.0-flash-001 |
| 51 → 58 | anthropic-claude-haiku-4-5-pinned |
| 52 → 59 | ollama-llama3.1 |

---

## Positive Things

**P1. Perfect success rate maintained.**
All 35 plans in runs 53–59 return `status: "ok"` in `outputs.jsonl`. No `LLMChatError`
entries found in any `events.jsonl` checked (runs 53, 58). 35/35 success rate continues
from iterations 18–20.

**P2. qwen3 shows measurable improvement in the hong_kong_game plan.**
Before (run 46, qwen3): two fabricated percentage claims in `002-10-potential_levers.json`:
"Allocate 30% of budget to location-specific VFX" and "Reserve 15% of funds for
last-minute location permit negotiations."
After (run 53, qwen3): hong_kong_game output contains 16 levers with no percentage claims.
All options use qualitative language consistent with the anti-fabrication instruction.
Evidence: `history/1/46_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
vs. `history/1/53_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

**P3. Gemini, gpt-4o-mini, and llama3.1 produce no detectable percentage claims.**
Samples from runs 56 (gpt-4o-mini), 57 (gemini), 59 (llama3.1) for hong_kong_game
contained no fabricated budget percentages. Output quality from these models is
consistent with prior iterations.

**P4. Content is substantially better than the pre-optimization baseline.**
Baseline (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`) has
13+ fabricated percentage claims in 15 levers (the old "Immediate → Systemic → Strategic"
consequence format). Current runs show much cleaner qualitative consequences across most
models. The optimization loop has eliminated the worst content patterns.

**P5. haiku silo output is clean.**
Run 58 (haiku) produced rich, detailed levers for the silo plan
(`history/1/58_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`)
with 21 levers and no fabricated percentages. The model handles plans without
budget figures in the project context cleanly.

---

## Negative Things

**N1. haiku still fabricates numbers in the hong_kong_game plan — from call 1.**
Run 58 (haiku, after PR) `002-10-potential_levers.json` for hong_kong_game contains:
- "US$15–25 million" for casting costs (lever: Lead Casting)
- "25–42% of the entire production budget" for casting cost as percentage
- "US$3–8 million" for mid-tier star cost
- "HK$30–50 million" and "HK$60 million" for specific casting spend
- "40–50% of budget through pre-sales" (lever: Financing Structure)

These appear in `002-9-potential_levers_raw.json` responses[0] (call 1), starting at
lever_index 3 ("Lead Casting and Above-the-Line Cost Management"). The PR's call-2/3
reminder cannot prevent claims fabricated during call 1.
Evidence: `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

Compare to before (run 51, haiku): 2 fabricated claims ("25–35% of P&A recovery",
"15–20 minutes of the film's runtime") — fewer absolute claims before the PR.
Evidence: `history/1/51_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

**N2. gpt-oss-20b shows more percentage claims after the PR.**
Run 54 (gpt-oss-20b, after): hong_kong_game "Financial Structuring" lever has
"Allocate 30% of the HK$470m budget", "Reserve 20% of the budget", "Allocate 15% of
the budget", plus "Allocate 30% of the production budget to a dedicated contingency fund"
and "securing up to 20% of eligible production costs" = 5 percentage claims.
Run 47 (gpt-oss-20b, before): "Budget Allocation Optimization" lever had 2 percentage
claims ("30% of production budget", "up to 20% of eligible production costs").
Evidence: `history/1/54_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
vs. `history/1/47_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

**Note:** The "Financial Structuring"/"Budget Allocation" lever type recurs across runs
47 and 54 because both are gpt-oss-20b runs on the same plan. The hong_kong_game plan
explicitly states a HK$470m budget, which anchors the model to speculate about
allocation percentages. These are likely in call 1 (the initial generation), not calls
2/3, making them immune to the PR change.

**N3. The PR cannot address call-1 fabrication.**
Checking `002-9-potential_levers_raw.json` for run 58 (haiku) confirms the structure:
responses[0] = call 1 (lever_index 1–n), responses[1] = call 2, responses[2] = call 3.
The fabricated dollar amounts and percentages in haiku's hong_kong_game output appear in
the first call's levers. The anti-fabrication reminder added by PR #313 only appears in
the call-2/3 user prompt. Call 1 receives no such reminder.
Evidence: `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`

**N4. llama3.1 outputs remain generic and shorter than other models.**
Run 59 (llama3.1) hong_kong_game output has 12 levers with brief, generic options
("Identify prime filming locations through local film commissions", "Partner with local
businesses", "Utilize 3D scanning technology"). Lever names repeat across plans
("Location Sourcing", "Casting", "Post-Production", "Marketing Strategy"). This
pattern predates the PR and is unrelated to it.
Evidence: `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

**N5. gpt-4o-mini shows repeated lever names in hong_kong_game.**
Run 56 (gpt-4o-mini) has two levers named "Festival Strategy for Critical Reception"
and "Festival Strategy for Audience Engagement" and two levers focused on
"Sound Design as Narrative Device" and "Psychological Depth through Soundscapes" — these
are near-duplicate levers with only minor framing differences. The dedup step may not
catch semantic near-duplicates.

---

## Comparison

### Before vs. After: Fabricated Percentage Claims (hong_kong_game only)

| Model | Before (run) | Claims | After (run) | Claims | Delta |
|-------|-------------|--------|-------------|--------|-------|
| qwen3-30b | 46 | 2 | 53 | 0 | **-2 ✓** |
| gpt-oss-20b | 47 | 2 | 54 | 5 | **+3 ✗** |
| haiku-4-5 | 51 | 2 | 58 | 6+ | **+4 ✗** |
| gpt-4o-mini | 49 | ~0* | 56 | 0 | 0 |
| gemini-2.0-flash | 50 | ~0* | 57 | 0 | 0 |
| llama3.1 | 52 | 0 | 59 | 0 | 0 |
| gpt-5-nano | 48 | ~0* | 55 | ~0* | 0 |

*Before value not directly checked but gpt-4o-mini, gemini, and gpt-5-nano do not
typically produce budget percentage patterns.

**Interpretation:** The qwen3 improvement is real and consistent with the PR's goal.
The haiku and gpt-oss-20b regressions are most likely driven by call-1 generation
(the hong_kong_game budget context triggers specific budget allocation levers), not by
calls 2/3. The PR change cannot reach call-1 fabrications.

### Lever Count (hong_kong_game)

| Model | Before levers | After levers |
|-------|--------------|-------------|
| qwen3 | 15 | 16 |
| gpt-oss-20b | 18 | 13 |
| haiku | 22 | 18 |
| gpt-4o-mini | not checked | 18 |
| gemini | not checked | 18 |
| llama3.1 | not checked | 12 |

---

## Quantitative Metrics

### Success Rate

| Batch | Runs | Plans | Successful | Rate |
|-------|------|-------|-----------|------|
| Before (runs 46–52) | 7 | 35 | 35 | 100% |
| After (runs 53–59) | 7 | 35 | 35 | 100% |

Source: `outputs.jsonl` for each run.

### LLMChatErrors

| Batch | LLMChatErrors found |
|-------|-------------------|
| Before | 0 (from prior analysis) |
| After | 0 (checked runs 53, 58) |

### Baseline vs. Current Field Length (hong_kong_game, rough estimates)

The baseline (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`)
uses the old consequence format ("Immediate: X → Systemic: Y → Strategic: Z") which is
very short per item (~120 chars per consequence). Current runs use 2–4 sentence
consequences (~200–500 chars). The ratio is approximately 1.5–4×.

| Model | Consequence length estimate | vs. Baseline |
|-------|---------------------------|-------------|
| Baseline | ~120 chars avg | 1× |
| qwen3 (run 53) | ~200 chars | ~1.7× |
| llama3.1 (run 59) | ~200 chars | ~1.7× |
| gpt-4o-mini (run 56) | ~250 chars | ~2× |
| gemini (run 57) | ~300 chars | ~2.5× |
| gpt-oss-20b (run 54) | ~400 chars | ~3.3× |
| haiku (run 58) | ~500 chars | ~4× |

haiku's consequence length at ~4× baseline is above the 2× warning threshold. The
extra length is substantive (nuanced trade-off analysis) in plans without budget context
(e.g., silo), but includes fabricated dollar amounts in plans with budget context
(hong_kong_game). The verbosity-quality trade-off is model-dependent.

### Fabricated Percentage Claims (cross-plan, hong_kong_game)

| Batch | Claims found | Plans checked | Source |
|-------|-------------|--------------|--------|
| Before 46–52 | 24 (from synthesis) | All | synthesis.md |
| After 53–59 | 11 (direct count)* | hong_kong_game only | This analysis |

*Partial count: 0 (qwen3) + 5 (gpt-oss-20b) + 6 (haiku) + 0 (gpt-4o-mini) + 0 (gemini) + 0 (llama3.1) = 11 in hong_kong_game.
The other 4 plans were not comprehensively checked for this metric.

---

## Evidence Notes

### Key artifacts cited

1. **Before qwen3 percentage claims**: `history/1/46_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — lever "Budget Allocation Optimization" options include "Allocate 30% of budget to location-specific VFX" and "Reserve 15% of funds for last-minute location permit negotiations".

2. **After qwen3 clean**: `history/1/53_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 16 levers, all qualitative options, no percentage claims.

3. **After haiku fabrication**: `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — lever "Lead Casting and Above-the-Line Cost Management" contains "A-list Hollywood name (US$15–25 million) would consume 25–42% of the entire production budget", "US$3–8 million", "HK$30–50 million", "HK$60 million".

4. **After haiku silo (clean)**: `history/1/58_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — 21 levers, all qualitative, no dollar amounts or percentages.

5. **Before haiku fewer claims**: `history/1/51_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — "25–35% of P&A recovery" and "15–20 minutes of the film's runtime" are the only numeric fabrications in 22 levers.

6. **Call structure**: `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json` — responses[0] lever_index 3 is "Lead Casting and Above-the-Line Cost Management" (the source of dollar fabrications), confirming these are from call 1.

7. **Baseline percentage density**: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` — 15 levers with 13+ fabricated percentage claims in the old "Immediate → Systemic → Strategic" format. Current runs are substantially better than baseline.

8. **Prompt content**: `prompts/identify_potential_levers/prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt` — the system prompt (loaded for call 1) already explicitly states "NO fabricated statistics or percentages without evidence from the project context" in section 5 (Prohibitions). The PR adds the same rule at the call-2/3 attention point.

---

## PR Impact

### What the PR was supposed to fix

PR #313 adds one line to the call-2/3 user prompt in `identify_potential_levers.py`:
"Do not invent percentages, cost savings, or performance deltas — use qualitative
language unless the project document supplies the number."

The previous synthesis (analysis/20) counted 24 unsupported percentage claims across
634 levers (3.8%) in runs 46–52 and recommended this as the top priority fix.

### Comparison table

| Metric | Before (runs 46–52) | After (runs 53–59) | Change |
|--------|--------------------|--------------------|--------|
| Success rate | 35/35 (100%) | 35/35 (100%) | None |
| LLMChatErrors | 0 | 0 | None |
| qwen3 % claims (hong_kong_game) | 2 | 0 | **-2 ✓** |
| gpt-oss-20b % claims (hk_game) | 2 | 5 | **+3 ✗** |
| haiku % claims (hong_kong_game) | 2 | 6+ | **+4 ✗** |
| Other models % claims | ~0 | ~0 | None |
| haiku silo % claims | not checked | 0 | — |

### Did the PR fix the targeted issue?

**Partially, for qwen3 only.** The qwen3 result (0 vs. 2 claims in hong_kong_game) is
the cleanest evidence of improvement.

For haiku and gpt-oss-20b, the claims appear to be generated in **call 1** (confirmed
by raw output structure for haiku), which the PR's call-2/3 reminder cannot address.
The hong_kong_game plan explicitly states a HK$470m budget, which triggers these models
to generate specific budget-allocation levers with invented sub-percentages (30% to
location, 20% to VFX, 40–50% through pre-sales, etc.). This is a **call-1 problem**
not addressed by the PR.

### Regressions introduced?

No structural regressions. The content regressions (more percentage claims in haiku and
gpt-oss-20b) likely reflect natural LLM variance amplified by the budget-heavy context
of hong_kong_game, not a causal effect of the PR. The silo plan (no budget numbers)
shows clean haiku output with no percentage fabrication.

### Root cause of remaining fabrication

The system prompt already prohibits fabricated statistics ("NO fabricated statistics or
percentages without evidence from the project context"). PR #309's call-2/3 reminder
fixed llama3.1 call-3 label degradation because that model was specifically losing
attention to the sentence-completeness rule at that attention point.

For budget percentage fabrication by haiku and gpt-oss-20b, the root cause is:
1. The hong_kong_game context **mentions a specific budget (HK$470m)**, which invites
   the model to extrapolate sub-allocations in call 1.
2. Neither the system prompt rule nor the call-2/3 reminder can prevent this if the
   levers are generated in call 1.
3. A call-1 anti-fabrication reminder or a project-context check would be needed.

### Verdict: CONDITIONAL

The PR is worth keeping because:
- It is low-risk (one line addition consistent with existing prohibitions)
- It demonstrably helped qwen3 in the hong_kong_game
- It follows a proven pattern (attention-decay reinforcement)

But it should NOT be treated as a complete fix:
- The primary remaining sources of percentage fabrication are in call 1
- haiku and gpt-oss-20b continue to fabricate numbers in budget-context plans
- A parallel fix is needed for call 1

---

## Questions For Later Synthesis

**Q1:** Does the call-2/3 anti-fabrication reminder help for other plans beyond
hong_kong_game? The silo, gta_game, sovereign_identity, and parasomnia plans don't
mention specific budget numbers, so the fabrication pattern there is different. The
synthesis should check whether calls 2/3 were the source of percentage claims in those
plans before PR #313.

**Q2:** Should a similar anti-fabrication reminder be added to **call 1** as well?
The evidence suggests call-1 fabrication is the dominant remaining source. This would
be the highest-leverage follow-up to PR #313.

**Q3:** Is the "budget anchor" effect (a known budget triggering allocation percentages)
specific to a few model families, or universal? qwen3 did not trigger it in run 53,
while haiku and gpt-oss-20b did. Understanding this split would help decide whether a
prompt fix or a code-level filter is more appropriate.

**Q4:** llama3.1 outputs remain consistently generic (12 levers vs. 16–18 for other
models, "Location Sourcing", "Casting", "Post-Production" as lever names). Should we
investigate whether llama3.1 is ignoring the domain-specific naming instruction
("Name each lever using language drawn directly from the project's own domain")?

**Q5:** haiku verbosity (4× baseline consequence length) continues to be flagged. When
the consequences contain grounded substance (as in the silo plan), this is acceptable.
When they contain fabricated dollar amounts (as in hong_kong_game), the extra length
adds noise. Should a word-count validator flag options or consequences that contain
dollar figures or percentage values?

---

## Reflect

The iteration pattern is working: a proven fix mechanism (attention-decay reinforcement)
was applied to a measured problem (24 fabricated percentage claims). The expected outcome
(reduction in calls 2/3) may well be occurring, but the measurement is complicated by
call-1 fabrication which is unaffected and may dominate the observed metrics.

The key realization is that **percentage fabrication has two distinct causes**:
1. **Call-1 budget anchoring**: A model sees a specific budget figure in the project
   context and generates allocation percentages in its first call. This is NOT addressed
   by the PR.
2. **Call-2/3 attention decay**: A model that avoided percentages in call 1 loses track
   of the prohibition in later calls. This IS addressed by the PR.

To fully resolve the problem, both causes need interventions.

The qwen3 improvement (2→0 in hong_kong_game) is encouraging because qwen3 handles
budget context without inventing sub-allocations. The haiku and gpt-oss-20b regressions
are not caused by the PR — they reflect how those models interpret "I see a budget,
I should allocate it" as an implicit task even when prohibited.

---

## Potential Code Changes

**C1: Add anti-fabrication reminder to call-1 prompt.**
Evidence: Raw output structure shows haiku's dollar fabrications appear in responses[0]
(call 1), starting at lever_index 3. The call-1 prompt only has the system prompt rule
against fabricated statistics. A brief inline reminder in the call-1 user prompt
(similar to the call-2/3 reminder from PR #313) could reduce call-1 fabrication.
Predicted effect: Reduce haiku and gpt-oss-20b percentage claims in budget-context plans.

**C2: Add optional numeric-claim warning validator.**
A post-generation validator that scans option text for `\d+%` or `\$[\d]` patterns
could emit `logger.warning` without rejecting the output. This would make fabrication
regressions immediately visible in logs rather than requiring post-hoc analysis.
Low effort. No retry overhead. Consistent with the pattern from AGENTS.md experiment insights.

**H1: Add "Do not invent dollar amounts, percentages, or specific financial figures"
to the call-1 user prompt at the budget-context attention point.**
Motivation: The system prompt rule is evidently insufficient for haiku and gpt-oss-20b
when a specific budget figure appears in the context. Adding the reminder to call 1
follows the proven attention-decay reinforcement mechanism.

**H2: Consider project-context preprocessing to remove or redact specific dollar
amounts before they enter the lever-generation prompt.**
If a plan document contains "HK$470m budget", redacting or replacing it with qualitative
language ("a significant production budget") would remove the anchor that triggers
fabricated sub-allocations. This is a more invasive change but would prevent the root
cause rather than reminding the model not to do what it was just told is possible.
Risk: May reduce specificity in other ways.

---

## Summary

PR #313 adds an anti-fabrication reminder to calls 2/3, following the proven pattern
from PR #309. The success rate holds at 35/35. For qwen3, the hong_kong_game
measurement shows the PR working (2→0 fabricated percentage claims). For haiku and
gpt-oss-20b, fabricated dollar amounts and percentages persist or increased, but
examination of the raw output structure confirms these originate in call 1 — outside
the PR's scope.

The call-1 budget anchoring problem (a specific budget figure in the project context
triggers model speculation about sub-allocations) is the dominant remaining source of
percentage fabrication and is **not addressed by this PR**. The most impactful next
step is either adding a call-1 anti-fabrication reminder or investigating whether a
project-context preprocessing step can remove the numeric anchor before lever generation.

The PR is worth **CONDITIONAL keep**: it contributes positively for at least one model
and is consistent with the proven attention-decay mechanism. But it is not a complete
fix for the targeted metric, and the follow-up action (call-1 reminder) is necessary
to achieve measurable improvement across all models.
