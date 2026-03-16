# Baseline vs Run 100: gemini-2.0-flash Lever Output Quality Comparison

The baseline training data was generated with gemini-2.0-flash. Run 100 is also
gemini-2.0-flash but after several optimization iterations (prompt improvements,
max_length removal, option/review validators). This comparison measures whether
the optimizations improved output quality for the same model.

## Prompt Changes Between Versions

| Aspect | Baseline (prompt_0) | Run 100 (prompt_2) |
|---|---|---|
| Lever count | "EXACTLY 5 levers per response" | "5 to 7 levers per response" |
| Lever naming | "Name levers as strategic concepts (e.g., 'Material Adaptation Strategy')" | "Name each lever using language drawn directly from the project's own domain -- avoid formulaic patterns or repeated prefixes" |
| Measurable outcomes | "Systemic: 25% faster scaling through..." | "Systemic: [a specific, domain-relevant second-order impact with a measurable indicator, such as a % change, capacity shift, or cost delta]" |
| Prefix prohibition | Basic list | Expanded to include "Conservative:", "Moderate:", "Radical:" |

---

## Per-Plan Comparison Table

| Plan | Metric | Baseline | Run 100 | Delta |
|---|---|---|---|---|
| **Silo** | Raw levers | 15 | 18 | +3 |
| | Merged levers | 15 | 18 | +3 |
| | Unique names / total | 11/15 (73%) | 18/18 (100%) | +27pp |
| | 3-option compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Avg option length (chars) | 142 | 116 | -26 |
| | Avg consequence length (chars) | 286 | 368 | +82 |
| | Chain format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Review format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Bracket leakage | 0 | 0 | same |
| | Option prefix leakage | 0 | 0 | same |
| | Cross-call name dups | 3 | 0 | -3 |
| **GTA Game** | Raw levers | 15 | 18 | +3 |
| | Merged levers | 15 | 18 | +3 |
| | Unique names / total | 14/15 (93%) | 18/18 (100%) | +7pp |
| | 3-option compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Avg option length (chars) | 116 | 110 | -6 |
| | Avg consequence length (chars) | 279 | 363 | +84 |
| | Chain format compliance | 10/15 (67%) | 18/18 (100%) | +33pp |
| | Review format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Bracket leakage | 0 | 0 | same |
| | Option prefix leakage | 0 | 0 | same |
| | Cross-call name dups | 1 | 0 | -1 |
| **Sovereign Identity** | Raw levers | 15 | 19 | +4 |
| | Merged levers | 15 | 19 | +4 |
| | Unique names / total | 5/15 (33%) | 19/19 (100%) | +67pp |
| | 3-option compliance | 15/15 (100%) | 19/19 (100%) | same |
| | Avg option length (chars) | 151 | 99 | -52 |
| | Avg consequence length (chars) | 265 | 368 | +103 |
| | Chain format compliance | 15/15 (100%) | 19/19 (100%) | same |
| | Review format compliance | 15/15 (100%) | 19/19 (100%) | same |
| | Bracket leakage | 0 | 0 | same |
| | Option prefix leakage | 0 | 0 | same |
| | Cross-call name dups | 5 | 0 | -5 |
| **Hong Kong Game** | Raw levers | 15 | 18 | +3 |
| | Merged levers | 15 | 18 | +3 |
| | Unique names / total | 12/15 (80%) | 18/18 (100%) | +20pp |
| | 3-option compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Avg option length (chars) | 162 | 119 | -43 |
| | Avg consequence length (chars) | 269 | 494 | +225 |
| | Chain format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Review format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Bracket leakage | 0 | 0 | same |
| | Option prefix leakage | 16 | 0 | -16 |
| | Cross-call name dups | 3 | 0 | -3 |
| **Parasomnia** | Raw levers | 15 | 18 | +3 |
| | Merged levers | 15 | 18 | +3 |
| | Unique names / total | 11/15 (73%) | 18/18 (100%) | +27pp |
| | 3-option compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Avg option length (chars) | 180 | 137 | -43 |
| | Avg consequence length (chars) | 298 | 366 | +68 |
| | Chain format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Review format compliance | 15/15 (100%) | 18/18 (100%) | same |
| | Bracket leakage | 0 | 0 | same |
| | Option prefix leakage | 0 | 0 | same |
| | Cross-call name dups | 3 | 0 | -3 |

---

## Aggregate Comparison Table

| Metric | Baseline (75 levers) | Run 100 (91 levers) | Change |
|---|---|---|---|
| Total raw levers (3 calls x 5 plans) | 75 | 91 | +16 (+21%) |
| Total merged levers | 75 | 91 | +16 (+21%) |
| Unique names / total | 53/75 (71%) | 91/91 (100%) | **+29pp** |
| 3-option compliance | 75/75 (100%) | 91/91 (100%) | same |
| Avg option length (chars) | 150 | 116 | **-34 (-23%)** |
| Avg consequence length (chars) | 279 | 392 | **+113 (+40%)** |
| Chain format compliance (Immediate/Systemic/Strategic) | 70/75 (93%) | 91/91 (100%) | **+7pp** |
| Review format compliance (Controls X vs. Y + Weakness:) | 75/75 (100%) | 91/91 (100%) | same |
| Bracket placeholder leakage | 0 | 0 | same |
| Option prefix leakage (labels like "Conservative:") | 16 | 0 | **-16** |
| Cross-call name duplications | 15 | 0 | **-15** |

---

## Qualitative Assessment with Examples

### 1. Lever Name Diversity and Domain Specificity

This is the single most dramatic improvement.

**Baseline — Sovereign Identity** was catastrophic: all three LLM calls produced
the exact same 5 lever names ("Technical Feasibility Strategy", "Policy Advocacy
Strategy", "Coalition Building Strategy", "Procurement Influence Strategy", "EU
Standards Engagement Strategy"), repeated verbatim 3 times. The merged file
contained 15 levers but only 5 unique names.

**Run 100 — Sovereign Identity** produced 19 fully unique names covering a much
broader strategic surface: "Platform Integrity Assessment", "Fallback
Authentication Path Design", "Trust Anchor Diversification", "App Distribution
Neutrality", "Integrity Signal Independence", "Procurement Neutrality
Enforcement", "Platform Exit Strategy Definition", "Legislative Action Pursuit",
"Public Awareness Campaign Scope", etc. These names are highly domain-specific
and non-formulaic.

**Baseline — GTA Game** names were generic: "Technological Integration Strategy",
"Risk Mitigation Strategy", "Monetization Strategy" (2x), "Risk Mitigation
Protocol". Three different levers all named variants of "Risk Mitigation".

**Run 100 — GTA Game** names are strikingly domain-specific: "Criminal Economy
Simulation", "Vehicle Customization Depth", "Heist Mechanics Complexity", "NPC
Interaction Fidelity", "Law Enforcement Response Dynamism", "Radio Station
Diversity", "City Infrastructure Degradation", "Faction Allegiance System".

### 2. Consequence Chain Richness

**Baseline — Hong Kong Game** consequence example (269 chars avg):
> "Altering the core narrative impacts audience expectations. Immediate: Viewer
> disorientation -> Systemic: 15% higher audience engagement due to novelty ->
> Strategic: Increased critical acclaim but potentially polarizing initial
> audience reception."

**Run 100 — Hong Kong Game** consequence example (494 chars avg):
> "Immediate: Audience expectations are manipulated through misdirection and
> unreliable narration. -> Systemic: Viewers experience increased uncertainty
> and engagement, measured by audience surveys indicating a 20% rise in perceived
> unpredictability. -> Strategic: The film overcomes the 'spoiler effect' of the
> original, enhancing its appeal and critical reception by delivering a genuinely
> surprising experience. This mitigates risk of negative reviews due to
> predictability but increases the complexity of script development."

Run 100 consequences are 40% longer on average with more explicit trade-off
descriptions and more specific measurable indicators.

### 3. Option Prefix Elimination

**Baseline — Hong Kong Game** had 16 prefixed options across 4 levers:
- "Faithful Adaptation: Maintain the original plot structure..."
- "Subversive Parallel: Mirror the original's structure..."
- "Traditional Workflow: Utilize standard film production..."
- "Established Star: Cast a well-known international actor..."

**Run 100** has zero prefixed options across all 91 levers.

### 4. Strategic Space Breadth

**Baseline — Silo** covers 5 broad categories repeated 3x: Resource Allocation,
Social Structure, Tech Adaptation, External Relations, Information Control.

**Run 100 — Silo** covers 18 distinct dimensions: Information Control, Resource
Allocation, Social Stratification, Tech Advancement, External Communication,
Security System Architecture, Community Governance, Ecosystem Management,
Knowledge Dissemination, Population Management, Internal Justice, Agricultural
Production, Energy Generation, Waste Recycling, Technological Innovation,
Educational Curriculum. The added dimensions (agriculture, energy, waste,
education, justice, population) are all highly relevant to the silo scenario.

---

## Wins and Losses Summary

| Dimension | Winner | Magnitude |
|---|---|---|
| Lever count (more strategic dimensions) | Run 100 | +21% more levers |
| Name uniqueness | Run 100 | 71% → 100% |
| Cross-call duplication | Run 100 | 15 dups → 0 |
| Option prefix leakage | Run 100 | 16 → 0 |
| Consequence chain format | Run 100 | 93% → 100% |
| Consequence richness (length) | Run 100 | +40% longer |
| Domain specificity of names | Run 100 | Qualitative win |
| Strategic space breadth | Run 100 | Qualitative win |
| Option length (conciseness) | Run 100 | -23% (more concise, not worse) |
| 3-option compliance | Tie | 100% in both |
| Review format compliance | Tie | 100% in both |
| Template/bracket leakage | Tie | 0 in both |

No metrics regressed.

---

## Verdict: BETTER

Run 100 is unambiguously better than the baseline across every measured dimension.

**Major wins**: Lever name uniqueness jumped from 71% to 100%, eliminating the
worst failure mode (Sovereign Identity went from 33% to 100%). Cross-call
duplication was completely eliminated (15 → 0). The strategic space covered by
each plan is dramatically broader and more domain-specific.

**Moderate wins**: Consequence chains are 40% richer on average, with more
explicit trade-off analysis and more specific measurable indicators. Chain format
compliance went from 93% to 100%. Option prefix leakage (16 instances in
baseline Hong Kong plan) was completely eliminated.

**Maintained standards**: 3-option compliance, review format compliance, and zero
template leakage were already perfect in the baseline and remain perfect.

The most impactful change was the prompt instruction to "avoid formulaic patterns
or repeated prefixes" combined with the 5-to-7 lever range, which together forced
the model to explore a much wider strategic space and produce genuinely distinct
lever concepts for each call. The sovereign identity plan is the most compelling
proof: it went from 5 unique concepts (each repeated 3x) to 19 unique concepts
with zero overlap.
