# Assessment: Tighten number constraint in consequences to verbatim-only

## Issue Resolution

**What the PR was supposed to fix:** PR #481 replaced `"only cite numbers if the project context
provides evidence for them"` with `"use numbers only when the project context provides them
directly — do not calculate, derive, or estimate figures"` in `Lever.consequences` (field
description), `LeverCleaned.consequences` (dead code — never sent to LLM), and system prompt
Section 2. The motivation was that analyses 69–74 measured fabricated percentage claims in
consequences (haiku: 20 instances before PR #478, 0 after); PR #481 extends that wording to
the current baseline.

**Is the issue resolved in the post-fix outputs?**

Partially. The strengthened wording eliminates the `"provides evidence"` loophole that allowed
models to reason "the context implies this percentage." However two gaps remain:

1. **"Typically" loophole persists in consequences.** Haiku run 5/38 hong_kong_game lever
   "Sound Design Investment" consequences reads: `"typically adding 2–4 weeks and 8–15% to
   post-production budget"`. The word "typically" reframes an industry-knowledge estimate as
   a contextual fact, bypassing "do not calculate, derive, or estimate figures." The new wording
   does not explicitly prohibit domain-knowledge hedging.
   Evidence: `history/5/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
   (lever "Sound Design Investment", consequences field).

2. **Primary fabrication site is `options`, not `consequences`.** PR #481 tightened the wrong
   field. The dominant fabrication violations observed in haiku run 5/38 hong_kong_game occur
   in the `options` field, which has no verbatim-numbers constraint:
   - "Mainland Revenue Independence" option 2: `"40–50% of the budget originates from a major
     Western streaming platform"` — fabricated % allocation (not in project context)
   - "Post-Production Investment Allocation" options: `"Allocate 65% of the HK$470 million
     post-production budget"` (65% fabricated), `"Commit 50% of post-production resources"`
     (50% fabricated)
   - "Sound Design Investment" options: `"HK$8–12M"`, `"HK$4–5M"`, `"HK$18–22M"` — derived
     from the single context figure HK$470M total; individual allocations are fabricated
   Evidence: same file as above.

3. **LeverCleaned.consequences change is dead code.** The `LeverCleaned` class is explicitly
   documented at line 197: "never sent to an LLM." Updating its field description has zero
   behavioral effect. The PR description counts this as one of "three locations" but only two
   matter.

**Residual symptoms from analysis 40:** The secondary `review_lever` template lock
("All three options X / none of the options Y") was identified as the primary open issue in
analysis 40. PR #481 does not touch the `review_lever` field description.
Direct count of run 5/38 hong_kong_game: **20/21 reviews (95%)** end with "none/all three
options" or "the options do not address" — essentially unchanged from the ~85% measured in
analysis 40 (run 2/93). The template lock persists and may be slightly worse.
Evidence: `history/5/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
(every review field; lever 18 "Surveillance Technology Diegesis" is the sole exception).

---

## Quality Comparison

**Model mapping (shared across both batches):**

| Before (analysis 40) | After (analysis 75) | Model |
|---|---|---|
| 2/87 | 5/32 | ollama-llama3.1 |
| 2/88 | 5/33 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/34 | openai-gpt-5-nano |
| 2/90 | 5/35 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/36 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/37 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/38 | anthropic-claude-haiku-4-5-pinned |

All 7 models appear in both batches. Full comparison valid.

**Note on insight coverage:** `insight_claude.md` for analysis 75 timed out (error after 1200s).
All findings below are drawn from `code_claude.md`, `synthesis.md`, and direct inspection of
haiku run 5/38 outputs. Evidence is independently verified against source files.

| Metric | Before (runs 2/87–2/93) | After (runs 5/32–5/38) | Verdict |
|--------|------------------------|------------------------|---------|
| **Overall call success rate** | 102/105 = 97.1% | 103/105 = 98.1% | IMPROVED +1.0pp |
| **llama3.1 call success rate** | 14/15 = 93.3% | 15/15 = 100% | IMPROVED +6.7pp |
| **Haiku call success rate** | 13/15 = 86.7% (silo 2/3, gta_game 2/3) | 13/15 = 86.7% (silo 2/3, gta_game 2/3) | UNCHANGED |
| **gpt-oss-20b / gpt-5-nano / qwen3 / gpt-4o-mini / gemini** | 15/15 = 100% each | 15/15 = 100% each | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High | High | UNCHANGED |
| **Template leakage (field names in options)** | 0 | 0 | UNCHANGED |
| **"Controls X vs Y" review format** | 0 | 0 | UNCHANGED (N/A) |
| **"Immediate → Systemic → Strategic" chain** | 0 | 0 | UNCHANGED (N/A) |
| **"Tension" opener lock (haiku)** | 0% (fixed in PR #358) | 0% | UNCHANGED |
| **"All three options / none of options" lock (haiku hong_kong_game)** | ~85% (17/20 reviews, run 2/93) | ~95% (20/21 reviews, run 5/38) | UNCHANGED / SLIGHTLY WORSE |
| **Fabricated % in consequences (haiku)** | 0 (confirmed, analysis 40) | 1 instance via "typically" loophole (run 5/38) | REGRESSED (loophole active) |
| **Fabricated % in options (haiku)** | Not deeply sampled in analysis 40 | Confirmed: 5+ fabricated figures in run 5/38 hong_kong_game | NEW CONFIRMED ISSUE |
| **Fabricated industry estimate in review (haiku)** | 0 | 1 ("Mainland China represents 15–25% of global box office", run 5/38) | REGRESSED |
| **Review length vs baseline — haiku silo** | ~260 chars / ~42 words = 2.9× baseline | ~300+ chars (lever 2 = 421 chars / ~70 words multi-sentence) | REGRESSED / UNCHANGED |
| **Marketing-copy language** | 0 | 0 | UNCHANGED |
| **Cross-call duplication** | Low | Low | UNCHANGED |
| **Over-generation (>7 levers per call, haiku)** | 2/5 plans exit after 2 calls | 2/5 plans exit after 2 calls (silo, gta_game) | UNCHANGED |
| **Field length vs baseline (consequences, haiku)** | ~2.5–3× baseline | ~2.5–3× baseline | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS alignment:**
PR #481 moves slightly closer to the "no fabricated numbers" goal for the consequences field.
However, the options field — the primary fabrication site — remains completely unprotected.
The tightened wording does not address the "typically"/"commonly" domain-knowledge hedge,
which is a documented bypass not yet captured in OPTIMIZE_INSTRUCTIONS. The review_lever
template lock (OPTIMIZE_INSTRUCTIONS §Field-description template lock, lines 86–92) was the
highest-priority issue in analysis 40 and is not addressed by this PR. The net effect on
OPTIMIZE_INSTRUCTIONS goals (realistic, feasible, actionable) is marginal positive.

---

## New Issues

1. **"Typically" qualifier as domain-knowledge bypass (consequences field, confirmed).**
   Haiku run 5/38 produces `"typically adding 2–4 weeks and 8–15% to post-production budget"`.
   The phrase "typically" frames industry-standard estimates as accepted domain facts, bypassing
   "do not calculate, derive, or estimate figures." The fix must explicitly name hedge qualifiers
   ("typically", "usually", "commonly", "industry standard") as prohibited vehicles for
   numerical estimation when the project context does not supply the figure verbatim.
   File: `identify_potential_levers.py:111–120` (Lever.consequences) and system prompt Section 2.

2. **`options` field confirmed as primary fabrication site (haiku, unprotected).**
   PR #481 fixed consequences; the dominant violation site is options. Five confirmed fabricated
   figures in a single plan (run 5/38 hong_kong_game): 40–50%, 65%, 50%, HK$8–12M, HK$4–5M,
   HK$18–22M. The `options` field description contains no verbatim-numbers constraint.
   File: `identify_potential_levers.py:122–125`.

3. **LeverCleaned dead-code churn pattern established.**
   PR #481 updated `LeverCleaned.consequences` despite the class being explicitly documented as
   never sent to an LLM (lines 197, 201–202). This established a pattern: future maintainers may
   mirror Lever field-description changes into LeverCleaned unnecessarily, inflating PR diffs
   and misleading reviewers about which changes actually matter. The risk is that future PRs
   omitting the LeverCleaned mirror are flagged as incomplete.

4. **Fabricated industry estimate in review field (haiku, new instance).**
   Run 5/38 lever "Financing Structure and Mainland China Revenue Contingency" review contains:
   `"Mainland China represents 15–25% of global box office"` — an industry-knowledge estimate
   not present verbatim in the hong_kong_game project context. The review field has no number
   constraint at all.

---

## Verdict

**CONDITIONAL**: The two effective changes (Lever.consequences field description + system
prompt Section 2) are syntactically correct, directionally sound, and non-regressive — they
strengthen the wording without breaking any working behavior. However, the PR does not address
the dominant fabrication site (options field), leaves the "typically" domain-knowledge bypass
open in consequences, and does not touch the review_lever template lock that was identified as
the highest-priority issue in analysis 40 and confirmed still active at ~95% in haiku run 5/38.

**Conditions to keep:** (a) Immediately follow with verbatim-numbers constraint on the `options`
field; (b) Fix the `review_lever` field description to remove "the three options leave unaddressed"
as grammatical subject; (c) Close the "typically" loophole in consequences with explicit language
prohibiting hedge-qualified industry estimates.

---

## Recommended Next Change

**Proposal:** Rewrite the `review_lever` field description (lines 125–134) and its matching
Section 4 header (line 249) to remove "the specific gap the three options leave unaddressed"
and replace it with goal-oriented language that does not reference the output structure as a
grammatical subject. This is the synthesis recommendation from analysis 75.

**Draft wording** (`identify_potential_levers.py:125–134`, `Lever.review_lever`):
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
And update Section 4 system prompt header (line 249) to match.

**Evidence:** Compelling. The synthesis cites a direct causal chain:
- `identify_potential_levers.py:127–129` says "state the specific gap the **three options**
  leave unaddressed" — models parse "three options" as a sentence-subject instruction
- Run 5/38 haiku hong_kong_game: 20/21 reviews (95%) end with "none/all three options" or
  "options do not address" — the structural lock is dominant and persistent
- Analysis 40 measured the same lock at 85% — it has not decreased with PR #481
- OPTIMIZE_INSTRUCTIONS lines 73–82 document exactly this failure mode ("Template-lock migration")
- Both agents in analysis 40 independently identified this as top priority; code_claude in
  analysis 75 (B4) confirms it remains the top unresolved structural issue

**Verify in next iteration:**
- **Primary target:** Count "all three options / none of [the] options" rate in haiku
  hong_kong_game (run 5/38 baseline: 20/21 = 95%). Target: drop to <20%.
- **Verify wording doesn't re-introduce subject-reference:** Check whether "all three strategies
  collectively" (from analysis 40 synthesis draft) triggers a new "all three strategies" lock.
  The safer draft above ("would persist even if all three options were executed perfectly") uses
  "all three options" as object (not subject) — verify this distinction holds in practice.
- **Check other models for template lock:** gpt-oss-20b (run 5/33) and qwen3-30b (run 5/35)
  were not deeply sampled. The code_claude notes that lock rates of 70–94% were measured for
  haiku and higher for gpt-oss-20b in analysis 74 — verify these models show improvement.
- **Haiku success rate:** Confirm stays at or above 86.7% (13/15). Changing the field
  description could affect review length and thus partial_recovery behavior.
- **Options fabrication (haiku):** After fixing the review_lever, immediately check options
  fields for run 5/38-equivalent. The options fix should be bundled or follow immediately.

**Risks:**
- **New subphrase lock from the draft wording:** "would persist even if all three options were
  executed perfectly" contains "all three options" — even as object rather than subject this
  could still be mirrored. Consider further removing "options" entirely: "would persist
  regardless of which approach is chosen."
- **Content quality regression:** The current lock produces plan-specific X-slots ("none of the
  three options addresses whether the lead actor will have creative approval…"). If the new
  wording yields more generic gap statements ("the project's resource constraints"), content
  quality regresses even if lock rate drops. Track average specificity of the Y-slot.
- **Review length may not improve:** The one-sentence constraint and review length remain
  unchanged by this fix. Haiku silo (analysis 75) already shows a 421-char multi-sentence
  review; fixing the template lock alone won't enforce the length limit.

**Prerequisite issues:** None. The review_lever rewrite is a standalone change.

**Recommended bundle:** Pair the review_lever fix with the options verbatim-numbers constraint
(add `"Use only numbers that appear verbatim in the project context; do not calculate, derive,
or estimate figures."` to `Lever.options` field description at lines 122–125) and the
"typically" loophole closure for consequences (add explicit prohibition on hedge qualifiers in
`Lever.consequences` and system prompt Section 2). Three targeted changes, one PR.

**OPTIMIZE_INSTRUCTIONS update:** Add the "typically" loophole as a named bypass to the
"Fabricated numbers" entry. Current text warns against fabrication; it does not warn that
domain-knowledge hedges ("typically X%", "industry standard Y weeks") are an active bypass
that survives "do not estimate figures." Capturing this in OPTIMIZE_INSTRUCTIONS prevents
future prompt iterations from re-opening the same loophole.

---

## Backlog

**Resolved — remove from backlog:**
- Nothing fully resolved by PR #481. The consequences constraint is strengthened (partial fix)
  but the issue remains open due to the "typically" loophole and the unprotected options field.

**Updated — change severity:**
- **HIGH: Fabricated numbers in `options` field.** Previously noted as undetected in analysis 40;
  now confirmed in run 5/38 haiku hong_kong_game (5+ fabricated figures). Move from "may be
  present" to confirmed HIGH priority. Fix: add verbatim-numbers constraint to `Lever.options`
  field description (`identify_potential_levers.py:122–125`).

**New — add to backlog:**
- **HIGH: "Typically" qualifier loophole in consequences.** Haiku run 5/38 produces
  `"typically adding 2–4 weeks and 8–15%"` — domain-knowledge estimate reframed as typical
  industry fact. Add explicit prohibition on hedge qualifiers to `Lever.consequences` field
  description and system prompt Section 2.
- **MEDIUM: Fabricated industry estimate in review field.** No number constraint exists in
  `review_lever`. Haiku produced "Mainland China represents 15–25% of global box office" in a
  review. Consider whether a verbatim-numbers constraint should also apply to review_lever,
  or whether fixing the template lock first will reduce review verbosity enough to eliminate
  this.
- **LOW: LeverCleaned dead-code mirroring pattern.** PR #481 updated `LeverCleaned.consequences`
  despite it never being sent to an LLM. Collapse `LeverCleaned` field descriptions to terse
  one-liners (`description="Cleaned consequences text from Lever.consequences."`) to prevent
  future wasted PR diff and misleading reviewers.

**Carry over from analysis 40 backlog (unchanged):**
- **HIGH: `review_lever` template lock — "three options leave unaddressed".** Still active at
  ~95% (haiku hong_kong_game run 5/38, 20/21 reviews). Confirmed top priority. PR #481 does
  not address this. Fix: rewrite field description to remove "three options" as grammatical
  subject (see Recommended Next Change above).
- **MEDIUM: Field-name rejection validator for `options`.** One instance in haiku run 86 (prior
  batch). Not rechecked in analysis 75; still unimplemented.
- **MEDIUM: `partial_recovery` event conflates loop-exit with call failure.** Unchanged.
  Haiku partial_recovery events in run 5/38 are confirmed loop-exits (silo 2/3, gta_game 2/3).
- **LOW: Review length still 2.5–4× above baseline for haiku.** Run 5/38 silo shows one
  review at 421 chars / ~70 words (multi-sentence, 1.75× the 40-word limit). Unchanged from
  analysis 40. Addressing the template lock first may reduce average length by eliminating the
  templated predicate clause.
- **LOW: Wrong model name in `check_option_count` docstring** (`identify_potential_levers.py:143`
  says "Run 82 (llama, gta_game)"; run 82 is gpt-5-nano). Unchanged; no operational impact.
