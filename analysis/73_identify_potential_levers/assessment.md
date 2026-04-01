# Assessment: Allow verbatim plan numbers only, positive framing, and tighter targets

## Issue Resolution

**What PR #478 was supposed to fix (from meta.json):**

1. **Verbatim numbers only** — close the arithmetic-derivation loophole (HK$470M→HK$141M from #475) by adding "Use numbers only when the project context provides them directly — do not calculate, derive, or estimate figures" to both field descriptions and Section 5.
2. **Positive framing** — replace "Do NOT include 'Controls ... vs.'" with "Save critical assessments for the review_lever field." to avoid prohibition-backfire in small models.
3. **Tighter targets** — consequences 2–3 sentences, options one sentence, review_lever one sentence (20–40 words). Applied consistently across field descriptions and system prompt.
4. **Section 5 prohibition** — global "NO calculated, derived, or estimated figures" in the system prompt.

**Resolution status:**

1. **Verbatim numbers in consequences**: Resolved. Haiku (5/24) hong_kong_game correctly uses plan-supplied figures in consequences: "US$120–220 million worldwide gross", "US$25 million marketing budget", "45–55 shooting days". Zero fabricated percentage claims or arithmetic derivations in consequences.

2. **Verbatim numbers in options**: NOT resolved. Haiku (5/24) generates 10+ estimated numeric ranges per plan in options fields: "2,500+ screens in key markets", "300–500 select screens", "premium-VOD window at 60 days" / "90+ days", "4–5 iconic Hong Kong locations", "10–12 neighborhoods", "70 percent of shooting days" / "30 percent", "25-day core block" / "20-day second block". These figures are not verbatim from the hong_kong_game project context. The verbatim-numbers prohibition was added to `consequences` field description and Section 5 globally, but was **not added to the `options` field description** (code_claude B3). Models following field descriptions selectively (haiku) apply the constraint to the documented field but not to others.
   Evidence: `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` levers 4, 7, 9, 11.

3. **Positive framing**: Resolved. No "Controls X vs. Y" pattern appears in any run 5/18–5/24 output. The replacement text ("Save critical assessments for the review_lever field") is low-risk.

4. **Tighter targets**: Partially resolved. gpt-4o-mini (5/22) and gpt-5-nano (5/20) follow the 2–3 sentence consequence target (~240 chars, on target). Haiku (5/24) still produces 3–5 sentences in consequences (~500 chars, over target). Llama3.1 (5/18) under-generates consequences (~110 chars, 1 sentence, well below target).

5. **Primary issue from analysis/40 (secondary template lock)**: NOT addressed. The "all three options / none of the options" pattern in `review_lever` was the top recommendation from analysis/40's synthesis and was explicitly documented in OPTIMIZE_INSTRUCTIONS. PR #478 did not touch the `review_lever` field description or Section 4. The pattern persists at 70% (hong_kong_game) to 94% (sovereign_identity) in haiku reviews.
   Evidence confirmed by direct file inspection: in `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, levers 1, 3, 5, 7, 8, 9, 10 all contain "the options do not address", "the options leave unaddressed", "none of the options explicitly address", "all three options risk", "all three options struggle", "all three options leave the boundary" — approximately 7/10 in the first 10 levers inspected (~70%), consistent with the insight file's 14/20 count.

**Residual symptoms**: Template lock active at 70–94% haiku, 28–33% gpt-4o-mini/gpt-5-nano. Fabricated numeric ranges in all haiku options fields.

---

## Quality Comparison

All 7 models appear in both batches. "Before" = runs 2/87–2/93 (analysis/40); "After" = runs 5/18–5/24 (analysis/73).

| Metric | Before (runs 2/87–2/93) | After (runs 5/18–5/24) | Verdict |
|--------|------------------------|----------------------|---------|
| **Overall call success rate** | 102/105 = 97.1% | 102/105 = 97.1% | UNCHANGED |
| **Haiku call success rate** | 13/15 = 86.7% | 13/15 = 86.7% | UNCHANGED |
| **Llama3.1 call success rate** | 14/15 = 93.3% | 14/15 = 93.3% | UNCHANGED |
| **Other 5 models success rate** | 15/15 each = 100% | 15/15 each = 100% | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (<3)** | 0 | 0 | UNCHANGED |
| **Template lock haiku (hong_kong_game)** | 17/20 = 85% | 14/20 = 70% | IMPROVED −15pp (root cause unaddressed) |
| **Template lock haiku (sovereign_identity)** | Not measured | 16/17 = 94% | NEW DATA — high |
| **Template lock gpt-4o-mini** | Not measured | ~6/18 = 33% | NEW DATA — moderate |
| **Template lock gpt-5-nano** | Not measured | ~5/18 = 28% | NEW DATA — moderate |
| **Template lock llama3.1** | ~0% | ~0% | UNCHANGED (different review style) |
| **Haiku review avg length** | ~260 chars (~42 words) | ~220 chars (~44 words) | IMPROVED −15% |
| **Haiku consequences length vs baseline** | Not measured | ~500 chars = **2.2× baseline** (above 2× warning) | PERSISTING ISSUE |
| **Haiku review length vs baseline** | ~2.9× baseline | ~2.4× baseline | IMPROVED (still above 2× warning) |
| **Fabricated % claims in lever fields** | 0 | 0 | UNCHANGED |
| **Marketing-copy language ("cutting-edge" etc.)** | 0 | 0 | UNCHANGED |
| **Estimated/derived numbers in options (haiku)** | Low / not measured | ~10+ per plan | REGRESSED (new issue surfaced) |
| **Verbatim numbers in consequences (haiku)** | Not enforced at field level | Enforced; working correctly | IMPROVED |
| **"Controls X vs Y" in consequences** | 0 | 0 | UNCHANGED (already resolved prior to both batches) |
| **Consequences framing (positive redirect)** | Prohibition-phrasing present | Positive framing ("Save critical assessments…") | IMPROVED |
| **Lever name uniqueness** | High (DeduplicateLeversTask handles downstream) | High (llama3.1 semantic duplication observed but expected) | UNCHANGED |
| **Cross-call lever name duplication** | Present in llama3.1 | Present in llama3.1 | UNCHANGED (expected) |
| **Over-generation (>7 levers/call)** | Haiku: 2 early exits | Haiku: 2 early exits (silo, sovereign_identity) | UNCHANGED |
| **Partial-recovery events (log warning)** | Haiku 2, llama3.1 1 | Haiku 2, llama3.1 1 | UNCHANGED (all are step-gate early exits, not failures) |

**OPTIMIZE_INSTRUCTIONS alignment:**

| Guideline | Status |
|-----------|--------|
| Fabricated numbers | Partially fixed — consequences ✓, options still generating estimates (haiku) ✗ |
| Template-lock migration (documented pitfall) | **Still active** — "the three options leave unaddressed" in field description ✗ |
| Field-description template lock (documented pitfall) | **Still present** — field description references "the three options" ✗ |
| Hype and marketing copy | 0 instances — fully compliant ✓ |
| Verbosity amplification | Review length improved slightly; consequences still over-long for haiku ✗ |
| Asymmetric field-description constraints | Not documented in OPTIMIZE_INSTRUCTIONS — B3 gap reveals this recurring pattern |

---

## New Issues

1. **Estimated/derived numbers in options (haiku) now measurable.** Before, the insight noted this was "not measured." After, it is confirmed at ~10+ estimated figures per haiku plan in options (screen counts, VOD windows, shooting-day splits). This was likely present before but untracked. The issue is surfaced by PR #478's verbatim-numbers focus drawing attention to the options field gap (code_claude B3). **This is a regression by surfacing** — the constraint was added to consequences but not options, creating a visible asymmetry.

2. **Template lock rate varies significantly by plan for haiku.** hong_kong_game: 70%; sovereign_identity: 94%. The bureaucratic/policy context of sovereign_identity appears to map more naturally to the "None addresses the core blocker" review structure, elevating the lock rate. This plan-context sensitivity was not visible in the before data.

3. **Partial-recovery threshold mismatch between warning and event.** Code review (B4) confirms: `runner.py:131` warns at `actual_calls < 3`; `runner.py:578–583` emits the event only at `calls_succeeded < 2`. Normal 2-call completions (haiku silo, haiku sovereign_identity in this batch) trigger the warning log but NOT the `partial_recovery` event. The insight and code review both note this but ascribe the events to different causes; they are complementary observations, not contradictions. This pre-existing inconsistency was identified in analysis/40 as S2/I2 but remains unfixed.

4. **`LeverCleaned.review` field description updated (backlog item closed).** The insight (E7) confirms that `identify_potential_levers.py:220–222` now reads `"Critical review of this lever."` — the stale "names the core tension" text from analysis/40 B1 appears to have been cleaned up in an intermediate PR. This backlog item is resolved.

5. **No new structural failures or schema errors introduced.** The PR makes no changes to validators, schema types, or the retry loop. No LLMChatErrors in any run.

---

## Verdict

**CONDITIONAL**: The PR's improvements (positive framing, verbatim-numbers in consequences, tighter length targets) are valid and produce incremental gains with no regressions, but the primary open issue from analysis/40 — the "all three options / none of the options" template lock in `review_lever` — was explicitly skipped. At 70–94% occurrence in haiku reviews and 28–33% in gpt-4o-mini/gpt-5-nano, this is the dominant content quality problem in this pipeline step. Keep the PR; immediately follow with the two-line field-description fix (B1+B2) and the verbatim-numbers addition to options (B3).

---

## Recommended Next Change

**Proposal**: Fix the `review_lever` field description and Section 4 system prompt to remove "the three options" as grammatical anchor (B1+B2), and add the verbatim-numbers constraint to the `options` field description (B3). These are three targeted string substitutions in `identify_potential_levers.py`, bundled as one PR.

Specific changes (from synthesis/73):

- **B1** (`identify_potential_levers.py:125–131`, `Lever.review_lever` field description):
  Replace: `"the gap the three options leave unaddressed"`
  With: `"name a real-world constraint or risk that all three approaches collectively sidestep"`

- **B2** (`identify_potential_levers.py:245`, Section 4 system prompt):
  Replace: `"then state the specific gap the three options leave unaddressed"`
  With: `"then name a real-world constraint or risk that all three approaches collectively sidestep"`

- **B3** (`identify_potential_levers.py:121–124`, `options` field description):
  Add: `"Use only numbers that appear verbatim in the project context; do not estimate or derive figures."`

**Evidence**: Both insight_claude and code_claude independently identify B1+B2 as the primary unresolved issue from analysis/40. Confirmed at source: `identify_potential_levers.py:125–131` still reads `"the gap the three options leave unaddressed"` and line 245 repeats it. Haiku output confirms 70% lock rate (hong_kong_game, 14/20 levers) and 94% lock rate (sovereign_identity, 16/17 levers). Analysis/40 synthesis predicted this fix would reduce haiku lock rate from ~85% to <20%. The wording "collectively sidestep" removes "the options" as grammatical subject while preserving the two-part structure (trade-off + gap). For B3: the exact same constraint already works for consequences — haiku correctly uses verbatim figures there while generating estimates in options. OPTIMIZE_INSTRUCTIONS (lines 86–92) explicitly documents this failure mode; the fix directly applies its guidance.

**Verify in next iteration**:
- Haiku hong_kong_game: template lock rate should drop from 70% to <20% (count "all three options", "none of the options", "the options do not" patterns in 002-10 reviews across all 5 plans).
- Haiku sovereign_identity: template lock rate should drop from 94% to <20% — this was the highest-lock plan and is the critical regression case.
- gpt-4o-mini hong_kong_game: lock rate should drop from ~33% to near 0% — mid-tier models are less susceptible; if still >15% after B1+B2, example structure (I3) may be contributing.
- Haiku options fields: estimated figures like "2,500+ screens", "300–500 screens", "70 percent of shooting days" should disappear. Verify levers 4, 7, 9, 11 in hong_kong_game 002-10.
- Haiku consequences: the verbatim figures (US$120–220M, US$25M, 45–55 days) should remain intact — confirm the B3 change does not regress the working consequences constraint.
- Watch for template-lock migration: if "collectively sidestep" or "all three approaches" becomes the new recurring sub-phrase in >30% of reviews, the field description has migrated rather than fixed. OPTIMIZE_INSTRUCTIONS already warns about this pattern.

**Risks**:
- Template-lock migration: the new phrase "all three approaches collectively sidestep" still references "approaches" as a group. Weaker models may echo "all three approaches" as the new opener. Monitor carefully. The phrase is harder to copy verbatim than "the three options leave unaddressed" because it is more idiomatic, but haiku's mirroring tendency makes this plausible.
- Llama3.1 under-generation: llama3.1 already under-generates consequences (1 sentence vs. 2–3 target). Adding the verbatim-numbers constraint to options may further restrict its option generation. Check llama3.1 option lengths in the next iteration.
- Example structure (I3): Two of three Section 4 examples use "X, but Y" adversative structure. If B1+B2 reduce the "none of the options" lock, a residual "but" structure may persist. This is a deferred risk, not a blocking issue.

**Prerequisites**: None. B1+B2+B3 are independent string changes requiring no prior fixes. The positive-framing change from PR #478 is already in place.

---

## Backlog

**Resolved (can be removed):**
- `LeverCleaned.review` stale description ("names the core tension") — E7 confirms this was cleaned up in an intermediate PR; no longer "names the core tension".

**Active (carry forward):**
- **B1+B2 (HIGH)**: "Three options" grammatical anchor in `review_lever` field description and Section 4 — primary open issue, not addressed by PR #478. Top priority for next PR.
- **B3 (HIGH)**: `options` field description missing verbatim-numbers constraint — haiku generates 10+ estimated figures per plan in options despite global Section 5 prohibition. Second priority in same next PR.
- **B4 (LOW)**: Partial-recovery threshold mismatch — `runner.py:131` warns at `< 3` calls but `runner.py:578–583` emits event at `< 2`. Spurious warning log on every normal 2-call completion. One-line fix, bundle in housekeeping PR.
- **I3 (MEDIUM, deferred)**: Section 4 examples all use "X, but Y" adversative structure — adds to template-lock risk. Defer until after B1+B2 are verified.
- **S2/I2 (LOW)**: Differentiate `partial_recovery` (genuine failure) from step-gate early exit (over-generation). Medium effort; defer until analysis tooling needs the distinction.
- **I4 (LOW)**: Add to OPTIMIZE_INSTRUCTIONS: document asymmetric field-description constraint gap (constraint added to `consequences` but not `options`) as a known maintenance pitfall. Zero-risk, should be bundled with B1+B2+B3 PR.
- **S3 (LOW)**: Shared `dispatcher` singleton not thread-isolated across parallel plan runs. Low frequency; defer.
- **S4 (LOW)**: `dispatcher.event_handlers.remove` in finally block can raise `ValueError` masking original exception. 3-line guard, opportunistic fix when touching `runner.py`.
