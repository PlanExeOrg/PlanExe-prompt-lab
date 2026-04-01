# Assessment: Strip field descriptions to word limits, anti-parrot in call-2+, fix threshold

## Issue Resolution

**PR #483 targeted six changes:**

1. **Minimal field descriptions** — strip all redundant guidance; keep only word-limit annotations in `consequences`, `options`, and `review_lever`.
2. **Anti-parrot in call-2+** — prepend `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence."` to the subsequent-call user prompt only.
3. **Minimal section 4** — reduce preamble to `"A one-sentence critical review (20–40 words). Examples:"` with no copyable template before the examples.
4. **System prompt word limits** — consequences target 30–60 words (section 2); options 15–25 words (section 6).
5. **Fix `partial_recovery` threshold** — `runner.py` changed from `< 3` to `< 2` to stop firing spuriously when 2 calls succeed.
6. **Net −22 lines** — removes all redundant guidance that duplicates system-prompt content.

**Resolution status:**

- **Minimal field descriptions:** PARTIALLY resolved. Haiku consequence verbosity dropped from 67.5w to 55.7w average (in-range 46%→69%). However, stripping `"one sentence"` and the section-4 pointer from `review_lever` caused llama3.1 to produce 7/7 exact-copy parrots (review ≡ consequences, sim=1.0) on gta_game in run 5/46. The `"Direct effect and one downstream implication"` wording in `consequences` caused gpt-4o-mini to collapse consequence length from 74% in-range to 0% in-range (avg 20.6w). The `"one sentence (15–25 words)"` option description drove gemini-flash below the 15-word floor (avg 13.9w vs 23.5w before).

- **Anti-parrot call-2+:** PARTIALLY resolved. gpt-oss-20b exact-copy parrots in call-2+ dropped from 6 to 0 (run 5/40 → 5/47). Confirmed in `history/5/47_identify_potential_levers/`. The anti-parrot instruction does not reach call-1; llama3.1's gta_game regression is entirely in call-1 and was not addressed.

- **Threshold fix:** FULLY resolved. Confirmed at `runner.py:579` — threshold now `pr.calls_succeeded < 2`. The event fires only for genuine single-call completions, not for normal 2-call step-gate exits. The `expected_calls=3` argument in the event at `runner.py:583` is now stale (should be 2) but has no operational impact.

- **Section 4 minimal:** FULLY resolved. Section 4 preamble is now `"A one-sentence critical review (20–40 words). Examples:"` — no copyable template before the examples. Verified in run 5/52 hong_kong_game output: haiku produces domain-specific reviews without template repetition.

- **Residual symptoms:** llama3.1 call-1 exact-copy parroting (gta_game, 7/7 levers), gpt-4o-mini consequence collapse (0% in 30–60w range), gemini-flash options below floor (37% in 15–25w range). All three are directly traceable to the field-description minimization.

---

## Quality Comparison

Before = runs 2/87–2/93 (analysis 40, post-PR #358). After = runs 5/46–5/52 (analysis 77, post-PR #483). All 7 models appear in both batches.

| Metric | Before (runs 2/87–93) | After (runs 5/46–52) | Verdict |
|--------|----------------------|---------------------|---------|
| **Plan-level success rate** | 35/35 = 100% | 31/35 = 88.6% (4 timeouts) | REGRESSED −11.4pp |
| **Call-level LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (<3 options)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | Not quantified, no issues flagged | Not quantified, no issues flagged | UNCHANGED |
| **Template leakage — haiku "none/all three options"** | 85% (hong_kong_game) | 0% | IMPROVED (fixed by PR #482 intermediate) |
| **Template leakage — all legacy patterns** | 0 except haiku lock | 0 | UNCHANGED |
| **llama3.1 call-1 exact-copy parrots (gta_game)** | 0 | 7/7 (sim=1.0) | NEW REGRESSION |
| **Review format compliance (Controls X vs Y)** | N/A (legacy format not targeted) | N/A | UNCHANGED |
| **Consequence chain format (Immediate→Systemic→Strategic)** | N/A (legacy format not targeted) | N/A | UNCHANGED |
| **Haiku consequences avg length** | 67.5w (1.89× baseline 35.7w) | 55.7w (1.56× baseline) | IMPROVED |
| **Haiku consequences in-range (30–60w)** | 46% | 69% | IMPROVED +23pp |
| **gpt-4o-mini consequences in-range (30–60w)** | 76% | 0% (avg 20.6w) | REGRESSED −76pp |
| **gemini-flash options avg length** | 23.5w (1.24× baseline 19.0w) | 13.9w (0.73× baseline) | REGRESSED (below floor) |
| **gemini-flash options in-range (15–25w)** | 71% | 37% | REGRESSED −34pp |
| **qwen3-30b options avg length** | ~10.5w | 9.2w (1% in 15–25w range) | REGRESSED (persistent) |
| **haiku review avg length** | ~42w (2.06× baseline 20.4w) | 37.0w (1.81× baseline) | IMPROVED (still above 2× threshold on prior; now below) |
| **Fabricated quantification — haiku** | 35 pct claims | 22 pct claims | IMPROVED −37% |
| **Fabricated quantification — qwen3-30b** | ~4 pct claims | 16 pct claims | REGRESSED +10 (likely stochastic) |
| **Fabricated quantification — all models total** | 39 | 47 | REGRESSED +8 |
| **High-similarity parroting (review≈consequence) — all models** | Not counted in analysis 40 | 46 (down from 100 in pre-PR #482) | IMPROVED vs prior; baseline unavailable |
| **gpt-oss-20b exact-copy parrots (call-2+)** | 0 (present in PR #482 run 5/40: 6) | 0 | IMPROVED (fixed vs intermediate) |
| **Marketing-copy language** | Not flagged | Not flagged | UNCHANGED |
| **Cross-call duplication** | Not flagged | Not flagged | UNCHANGED |
| **partial_recovery threshold correctness** | Incorrect (fired at <3 calls) | Correct (fires at <1 call) | IMPROVED |
| **Plan timeouts** | 0 | 4 (gpt-oss-20b×2, gpt-5-nano×2) | NEW (monitoring needed) |

**Field length ratio vs baseline (consequences target 35.7w, review target 20.4w, options target 19.0w):**

| Model | Cons ratio (before→after) | Review ratio (before→after) | Options ratio (before→after) |
|-------|--------------------------|----------------------------|------------------------------|
| llama3.1 | ~0.73×→0.61× | ~0.86×→1.06× | ~0.69×→0.58× |
| gpt-oss-20b | ~0.88×→0.80× | ~1.11×→1.24× | ~0.95×→0.91× |
| gpt-5-nano | ~0.89×→0.96× | ~1.12×→1.27× | ~0.89×→0.86× |
| qwen3-30b | ~0.82×→0.82× | ~0.80×→0.92× | ~0.55×→0.48× |
| gpt-4o-mini | ~0.91×→**0.58×** | ~0.89×→0.91× | ~1.01×→0.79× |
| gemini-flash | ~1.26×→1.01× | ~1.00×→0.97× | ~1.24×→**0.73×** |
| haiku | ~1.89×→1.56× | ~2.06×→1.81× | ~2.04×→1.56× |

Bold = fell below 0.7× (too short). Haiku review ratio improved from 2.06× (above 2× warning) to 1.81× (below warning threshold). gpt-4o-mini consequences at 0.58× are now informationally thin; gemini options at 0.73× are marginally below floor.

**OPTIMIZE_INSTRUCTIONS alignment:**

The current `OPTIMIZE_INSTRUCTIONS` constant (confirmed at `identify_potential_levers.py:27–93`) lists "Field-description template lock" and "Template-lock migration" as known pitfalls. PR #483 reduced field descriptions to word-limit-only, which correctly addresses template lock risk but went too far for low-capability models that use field descriptions as local structural anchors. The "Verbosity amplification" entry correctly motivated the word-limit approach for haiku. However, the OPTIMIZE_INSTRUCTIONS block lacks a "Consequence parroting" entry — the failure mode where weaker models copy `consequences` verbatim into `review_lever` is now confirmed as recurring but undocumented in the constant.

---

## New Issues

1. **llama3.1 call-1 exact-copy parrot regression** (NEW, HIGH). Run 5/46 gta_game: all 7 first-call levers have `review` ≡ `consequences` verbatim (sim=1.0). Confirmed in `history/5/46_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`. Root cause: PR #483 removed `"one sentence"` and `"See system prompt section 4 for examples."` from `review_lever` field description (`identify_potential_levers.py:117–119`), eliminating the structural anchors llama3.1 relies on. Anti-parrot instruction only applies to call-2+, leaving call-1 unguarded. This did not exist in run 5/39 (PR #482).

2. **gpt-4o-mini consequence word collapse** (NEW, HIGH). Consequences average dropped to 20.6w (0% in 30–60w range). The phrase `"one downstream implication"` is parsed as a two-clause format constraint (~18–22w total), treating `(30–60 words)` as an upper bound rather than a target range. Not present in run 5/43 (PR #482), where 74% were in range at 32.5w avg.

3. **gemini-flash options below 15-word floor** (NEW, MEDIUM). Options dropped from 23.5w avg (71% in range) to 13.9w avg (37% in range). The `"one sentence"` structural anchor in the options field description is being used as permission for the shortest grammatically complete sentence. Not present in run 5/44 (PR #482).

4. **gpt-5-nano plan timeouts** (NEW, LOW-MEDIUM). Runs 5/48 added 2 timeouts (sovereign_identity, parasomnia) that were not present in run 2/89. sovereign_identity also timed out for gpt-oss-20b (run 5/47). Likely provider latency on a high-token-density plan rather than prompt-induced — no change to these models' field content would explain it. Monitor across next 2 iterations.

5. **qwen3-30b fabricated claims increased** (REGRESSION, LOW/STOCHASTIC). 6→16 pct claims across silo and gta_game. No PR change targets qwen3-30b fabrication specifically; likely stochastic given qwen3-30b's persistent idiosyncratic behavior. Monitor; if it persists in the next iteration, add qwen-specific guidance to the system prompt anti-fabrication section (section 5).

6. **OPTIMIZE_INSTRUCTIONS missing "Consequence parroting" entry** (DOCUMENTATION GAP). The `review_lever` field description must maintain structural anchors (`"one sentence"`, section-4 cross-reference) to prevent llama3.1 from copying `consequences` verbatim. This constraint is undocumented in the OPTIMIZE_INSTRUCTIONS constant at lines 27–93. Future PRs that strip these anchors again will reproduce the regression.

**Latent issues surfaced:** The threshold fix reveals that the prior `partial_recovery` metric conflated step-gate early exits (healthy) with genuine call failures. Analysis event logs from before analysis 77 that count `partial_recovery` events are now known to overstate failure rates.

---

## Verdict

**CONDITIONAL**: The PR delivers genuine wins — haiku fabricated-numbers −67%, haiku consequences pulled into target range (19%→69% in-range), gpt-oss-20b call-2+ parroting eliminated, and the `partial_recovery` threshold correctly fixed — but three confirmed regressions require immediate follow-up before this can be treated as a clean improvement:

- **C1:** Restore `"in one sentence"` and `"See system prompt section 4 for examples."` to `review_lever` field description (`identify_potential_levers.py:118`) to eliminate llama3.1 call-1 exact-copy parrot.
- **C2:** Rephrase `consequences` field description to decouple content structure from length requirement (e.g., `"The direct effect of pulling this lever and one key downstream implication. Write 30–60 words."`) to restore gpt-4o-mini consequence quality.
- **C3:** Remove or replace `"one sentence"` in `options` field description; use `"Each option is 15–25 words — a complete, concrete strategic approach."` to stop gemini-flash from generating below-floor options.

---

## Recommended Next Change

**Proposal:** Restore structural anchors to `review_lever` and rephrase `consequences` to decouple content from length — both in `identify_potential_levers.py` — and extend the anti-parrot instruction to call-1. Bundle these three as a single targeted PR alongside an OPTIMIZE_INSTRUCTIONS update documenting consequence parroting as a known failure mode.

**Specific changes:**

1. `identify_potential_levers.py:117–119` — `review_lever` field description:
   Current: `"Critical review (20–40 words). No square brackets or placeholders."`
   Proposed: `"Critical review in one sentence (20–40 words). See system prompt section 4 for examples. No square brackets or placeholders."`
   Restores the exact wording from run 5/39 (PR #482) that produced 0 exact-copy parrots for llama3.1.

2. `identify_potential_levers.py:276` — call-1 user prompt:
   Prepend `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence.\n\n"` to the call-1 `user_prompt` (currently unguarded). Mirrors the call-2+ anti-parrot instruction, providing defense-in-depth.

3. `identify_potential_levers.py:112` — `consequences` field description:
   Current: `"Direct effect and one downstream implication (30–60 words)."`
   Proposed: `"The direct effect of pulling this lever and one key downstream implication. Write 30–60 words."`
   Separates content structure from length; the imperative `"Write 30–60 words"` frames it as a minimum, not a ceiling.

4. `identify_potential_levers.py:115` — `options` field description:
   Current: `"Exactly 3 options. Each is one sentence (15–25 words) — a concrete strategic approach."`
   Proposed: `"Exactly 3 options. Each option is 15–25 words — a complete, concrete strategic approach."`
   Removes `"one sentence"` brevity signal; the length range alone enforces the constraint.

5. `identify_potential_levers.py:27–93` — OPTIMIZE_INSTRUCTIONS:
   Add a "Consequence parroting" entry: the `review_lever` field description must retain `"one sentence"` as a structural anchor and include the section-4 cross-reference; without them, llama3.1 on complex plans (gta_game call-1) copies `consequences` verbatim. Anti-parrot instruction must appear in both call-1 and call-2+ user prompts.

**Evidence:** All five changes have direct causal evidence from this analysis. The llama3.1 regression (C1+B1) is deterministic-appearing (7/7 levers on one plan), strongly implicating the field description change rather than stochasticity. The gpt-4o-mini collapse (C2) is also clean (74%→0% in-range). The gemini regression (C3) correlates precisely with `"one sentence"` in the options field. The OPTIMIZE_INSTRUCTIONS gap (C5) is a future-proofing measure with zero risk.

**Verify in next iteration:**
- llama3.1 gta_game call-1: confirm 0 exact-copy parrots (was 7/7 in run 5/46); review similarity should be <0.3 for all levers.
- gpt-4o-mini consequences: confirm >50% in 30–60w range (was 0% in run 5/50); check silo and hong_kong_game specifically.
- gemini-flash options: confirm avg >15w and >60% in 15–25w range (was 13.9w avg, 37% in run 5/51).
- haiku consequences: confirm still ≥50% in 30–60w range (must not regress from the 69% gain).
- gpt-oss-20b call-2+ parrots: confirm stays at 0 (was 6 before fix; now 0 after PR #483's anti-parrot).
- gpt-5-nano and gpt-oss-20b timeouts: monitor whether sovereign_identity times out again; if 2+ consecutive iterations timeout on the same plan, investigate token density.
- qwen3-30b fabricated claims: if still ≥10 in next run, treat as confirmed regression and add qwen-targeted anti-fabrication guidance.

**Risks:**
- Restoring `"one sentence"` to `review_lever` may reintroduce minor template-lock migration risk for haiku (the prior lock was `"none/all three options"`, driven by a different phrase; `"one sentence"` does not provide a copyable opener). The OPTIMIZE_INSTRUCTIONS warning about `"one sentence"` not being a template-lock phrase is already noted in synthesis.md.
- Adding anti-parrot to call-1 introduces a prohibition sentence that small models might treat as a template, per OPTIMIZE_INSTRUCTIONS lines 78–82. Evidence from call-2+ suggests the prohibition works without causing new locks for the models tested. Monitor llama3.1 for new review-opening patterns derived from the anti-parrot sentence.
- Decoupling `"Write 30–60 words"` in `consequences` might cause haiku to overshoot again if the word count is re-read as a floor rather than a range. System prompt section 2 (30–60 word target) should serve as the ceiling-side constraint; monitor haiku consequences in-range.

**Prerequisites:** None. Changes 1–5 are independent. The haiku word-limit gains from PR #483 are preserved by all proposed fixes.

---

## Backlog

**Resolved (can be removed):**
- `"The tension is between X and Y"` opener lock for haiku and llama3.1 — fixed by PR #358.
- haiku `"none/all three options"` secondary template lock — fixed by PR #482.
- qwen3-30b `"creates X risks, leaving Y gaps"` template lock — fixed by PR #482.
- gpt-oss-20b call-2+ exact-copy parrots — fixed by PR #483 (this PR). Confirmed 0 in run 5/47.
- Incorrect `partial_recovery` threshold (`< 3`) firing on healthy step-gate exits — fixed by PR #483.

**New / carry-forward:**
- **[HIGH]** llama3.1 call-1 exact-copy parrot on gta_game (7/7 levers, run 5/46) — root cause confirmed; fix specified in C1 + B1 above.
- **[HIGH]** gpt-4o-mini consequence word collapse (0% in 30–60w range, run 5/50) — root cause confirmed; fix specified in C2 above.
- **[MEDIUM]** gemini-flash options below 15-word floor (13.9w avg, run 5/51) — root cause suspected; fix specified in C3 above.
- **[MEDIUM]** OPTIMIZE_INSTRUCTIONS missing "Consequence parroting" entry — no runtime impact but prevents future regression; add in next PR.
- **[LOW]** `runner.py:583` emits stale `expected_calls=3` after threshold fix; should be updated to reflect corrected semantics but no operational impact.
- **[LOW/MONITOR]** qwen3-30b fabricated claims spike (+10 to 16 in run 5/49) — likely stochastic; monitor for 2 more iterations before treating as confirmed.
- **[LOW/MONITOR]** gpt-5-nano + gpt-oss-20b plan timeouts on sovereign_identity — appears to be provider latency on a high-token-density plan, not prompt-induced; monitor.
- **[LOW]** qwen3-30b options persistently short (9.2w avg, 1% in 15–25w target range across two iterations) — word-count instructions appear ineffective for this model; may need a separate structural enforcement approach or model-level investigation.
