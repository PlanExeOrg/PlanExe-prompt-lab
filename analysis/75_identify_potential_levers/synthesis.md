# Synthesis

## Cross-Agent Agreement

Only one agent file completed (code_claude.md). The insight_claude.md file contains only an
error notice: `# ERROR: claude timed out` (1200s limit exceeded). The synthesis below is
therefore drawn entirely from code_claude.md cross-referenced with direct inspection of the
source files and haiku run 5/38 output.

**Confirmed by code review and output inspection:**

- PR #481 makes two effective changes (Lever.consequences field description + system prompt
  Section 2) and one dead-code change (LeverCleaned.consequences, which is explicitly
  documented as never sent to an LLM).
- The primary fabrication site across analyses 73–74 and confirmed in run 5/38 is the
  `options` field, not `consequences`. The PR does not address this field.
- The `review_lever` field description still contains the phrase "the specific gap the three
  options leave unaddressed," which is the confirmed template-lock root cause. Reviews in
  haiku run 5/38 (hong_kong_game) repeat "all three options leave unresolved…", "none of the
  three options adequately addresses…", "all three options either concede…", etc. — 4+ levers
  in a single plan showing the same opener.
- The "typically" loophole persists: haiku run 5/38 produces `"typically adding 2–4 weeks and
  8–15% to post-production budget"` in the consequences field — the field PR #481 explicitly
  tightened. The phrase "typically" reframes industry estimates as domain citations.

---

## Cross-Agent Disagreements

No cross-agent comparison is possible: one agent completed and one timed out. The code review
findings were independently verified against the source file and raw outputs, so the conclusions
stand without a second opinion to reconcile.

---

## Top 5 Directions

### 1. Fix `review_lever` field description to eliminate template lock
- **Type**: prompt change (Pydantic field description + system prompt Section 4)
- **Evidence**: B4 (code_claude), analyses 73/E4 and 74/Template Lock Status table (prior
  context). Direct output evidence from haiku run 5/38: 4 of 16 levers start with "all three
  options…" / "none of the three options…" — a ~25% rate in a single plan, consistent with
  the 70–94% lock rate measured in analysis 74.
- **Impact**: Affects all models; template lock is a structural quality defect that makes
  reviews formulaic regardless of domain. Fixing it improves output diversity on every run,
  every model, every prompt. This is the highest-breadth change available.
- **Effort**: Low — single field description rewrite + matching Section 4 update.
- **Risk**: Must not name the banned phrase in the replacement text (OPTIMIZE_INSTRUCTIONS
  warning: "small models treat the prohibition text as a template and copy the banned phrases").
  The fix must use goal-oriented language only.

### 2. Add verbatim-numbers constraint to `options` field description
- **Type**: prompt change (Pydantic field description)
- **Evidence**: B2 (code_claude). Directly confirmed in haiku run 5/38:
  - "Mainland Revenue Independence": option `"40–50% of the budget originates from a major
    Western streaming platform"` — fabricated %.
  - "Post-Production Investment Allocation": `"Allocate 65% of the HK$470 million post-
    production budget"` (65% fabricated), `"Commit 50% of post-production resources"` (50%
    fabricated).
  - "Sound Design Investment": `"HK$8–12M"`, `"HK$4–5M"`, `"HK$18–22M"` — all derived from
    a single context figure (HK$470M total).
  - Analysis 74: gpt-oss-20b shows 60%/40%/20% in options across multiple plans.
- **Impact**: Closes the dominant fabrication source that PR #481 missed. Affects haiku and
  gpt-oss-20b at minimum; likely other models too. Directly improves plan credibility.
- **Effort**: Low — one line addition to options field description.
- **Risk**: Adding length to the field description slightly increases context overhead; low risk.

### 3. Close the "typically" loophole in `consequences`
- **Type**: prompt change (field description + system prompt Section 2)
- **Evidence**: B3 (code_claude). Confirmed in haiku run 5/38 "Sound Design Investment"
  consequences: `"typically adding 2–4 weeks and 8–15% to post-production budget"` — these
  are industry-knowledge estimates framed as typical/standard facts. The current constraint
  "do not calculate, derive, or estimate figures" does not block inference from domain
  knowledge when hedged with "typically".
  Also: "Financing Structure and Mainland China Revenue Contingency" review contains
  `"Mainland China represents 15–25% of global box office"` — another industry-estimate
  figure that leaked through.
- **Impact**: Completes what PR #481 attempted. Haiku consequences still contain derived
  figures post-PR. Fixing this requires adding explicit language that domain-knowledge
  estimates ("typically X%", "industry standard Y weeks") are also prohibited.
- **Effort**: Low — one sentence addition to the existing constraint in Lever.consequences
  and system prompt Section 2.
- **Risk**: Very low. Additive wording only.

### 4. Add a BAD/GOOD counter-example to Section 5 (Prohibitions)
- **Type**: prompt change (system prompt only)
- **Evidence**: I3 (code_claude). The abstract "NO fabricated statistics or percentages"
  prohibition has been present since before PR #358 and continues to be ignored by haiku and
  gpt-oss-20b. Concrete examples work better for mid-tier models than abstract rules.
- **Impact**: Reinforces constraint for models where field descriptions alone are insufficient.
  Synergistic with directions 2 and 3. Per OPTIMIZE_INSTRUCTIONS, the example should use a
  neutral domain (not the current plan domain) to avoid the model copying it verbatim.
- **Effort**: Low — 3–5 lines of new prompt text.
- **Risk**: Must use a neutral-domain example (e.g., a construction or healthcare context) to
  avoid introducing a new template-lock vector. Low risk if done carefully.

### 5. Simplify `LeverCleaned` field descriptions
- **Type**: code quality / maintenance (no effect on LLM output)
- **Evidence**: B1 (code_claude). LeverCleaned is explicitly marked "never sent to an LLM"
  at line 197 and 201–202. PR #481 unnecessarily mirrors Lever's field description changes
  into LeverCleaned, establishing a false expectation that all three locations equally matter.
  Future maintainers may incorrectly infer that LeverCleaned descriptions are prompt-facing.
- **Impact**: Reduces maintenance surface and prevents future wasted PR diff. Zero effect on
  LLM output quality.
- **Effort**: Low — collapse verbose field descriptions in LeverCleaned to terse one-liners.
- **Risk**: Negligible. Pure documentation change.

---

## Recommendation

**Do first: Fix the `review_lever` field description (Direction 1), paired with its
corresponding Section 4 update (I2+I4).**

**Why first:** Template lock is the most pervasive structural quality defect. It degrades
review diversity across all models, all plans, all iterations — not just the fabrication cases
that affected haiku. The lock rate was measured at 70–94% for haiku and higher for gpt-oss-20b
in analysis 74. Every run produces mechanically identical `review_lever` openers regardless of
domain or context, which erodes the credibility and distinctiveness of the entire lever set.
This fix has the highest breadth (affects every model, every run) for the lowest effort.

**Why not Direction 2 first:** The options fabrication is high-severity but model-specific
(haiku, gpt-oss-20b). The template-lock affects all models. Both should be done, but the
template-lock fix benefits more runs.

**Specific change — two locations:**

**Location 1:** `identify_potential_levers.py` lines 125–134, `Lever.review_lever` field description:

```python
review_lever: str = Field(
    description=(
        "A short critical review (one sentence, 20–40 words): name the primary "
        "trade-off this lever forces, then identify a real-world constraint or "
        "risk that would persist even if all three options were executed perfectly. "
        "See system prompt section 4 for examples. "
        "Do not use square brackets or placeholder text."
    )
)
```

Key changes:
- Removes "identify the primary trade-off this lever introduces, then state the specific gap
  the three options leave unaddressed" — the copyable structural template.
- Replaces with goal-oriented language ("name the primary trade-off", "identify a real-world
  constraint or risk") that describes what to produce, not how the sentence should start.
- Changes "leave unaddressed" to "would persist even if all three options were executed
  perfectly" — functionally equivalent intent, but not a copyable sentence opener.
- Does NOT name the banned phrase anywhere (per OPTIMIZE_INSTRUCTIONS: naming banned phrases
  causes small models to copy them).

**Location 2:** System prompt Section 4, `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` at line 249:

Replace:
```
"A short critical review — identify the primary trade-off this lever
introduces, then state the specific gap the three options leave unaddressed."
```

With:
```
"A short critical review (one sentence, 20–40 words): name the primary trade-off this lever
forces, then identify a real-world constraint or risk that would persist even if all three
options were executed perfectly."
```

The field description and system prompt must stay in sync; divergence between them confuses
structured-output models that reference both.

---

## Deferred Items

**Direction 2 — Add verbatim-numbers constraint to `options` field** (I1): Should follow
immediately after Direction 1. Add to `Lever.options` field description:
```
"Use only numbers that appear verbatim in the project context; do not calculate,
derive, or estimate figures."
```

**Direction 3 — Close the "typically" loophole** (B3): Extend the existing constraint in
Lever.consequences and system prompt Section 2 with:
```
"Do not use 'typically', 'usually', 'commonly', or similar qualifiers to introduce
industry-standard estimates — if the project context does not supply the figure verbatim,
omit it."
```

**Direction 4 — BAD/GOOD example in Section 5** (I3): Add a concrete fabrication example
using a neutral domain (e.g., construction). Draft:
```
- NO fabricated statistics or percentages. Example:
  BAD: "Allocate 20% of the budget to permits." (20% is not in the context)
  GOOD: "Allocate a contingency portion of the budget to permit fees."
```

**Direction 5 — Simplify LeverCleaned field descriptions** (B1/I5): Collapse to terse
one-liners (`description="Cleaned consequences text from Lever.consequences."`) to prevent
future maintainers from mirroring LLM-facing prompt changes into dead-code documentation.

**S2 — Miscalibrated warning threshold in runner.py** (line 131): The warning fires at
`actual_calls < 3`, which is the normal success case for models that produce 8+ levers per
call. Adjust to `actual_calls < 2` (or restructure to check lever count rather than call
count) to eliminate false-positive log noise.

**PR #481 verdict (carried forward):** CONDITIONAL — the two effective changes (Lever field
description + system prompt Section 2) are correct and non-regressive. Merge, but immediately
follow with the options constraint (Direction 2) and the review_lever rewrite (Direction 1).
The LeverCleaned change in PR #481 is dead code but harmless.
