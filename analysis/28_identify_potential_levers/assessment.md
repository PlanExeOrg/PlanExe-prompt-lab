# Assessment: fix: remove template-lock phrase and deduplicate examples

## Issue Resolution

**PR #340 targeted two issues:**

**B1 — Remove lockable phrase "the options neglect" from the third `review_lever` example**
The before batch (runs 96–02) showed llama3.1 using "The options [fail/neglect/overlook]" in 16/16 gta_game reviews (100%) and 11/12 parasomnia reviews (92%). The PR replaced example 3's text from "the options neglect that a single hurricane season…" to "a regional hurricane season can correlate all three simultaneously — correlation risk absent from every option."

**Result: Partially resolved for gta_game, not resolved for parasomnia.**
- gta_game: 100% → 62.5% (10/16 reviews). Only first-call levers (1–6) shifted to "[Lever name] lever overlooks/neglects…"; second and third call levers (7–16) still use "The options [verb]" at ~100%.
- Parasomnia: 92% → 100% (18/18). No improvement; the model substituted equivalent openers ("The options assume…", "The options overlook…", "The options miss…").
- gpt-5-nano run 05 gta_game lever 2 review still contains: `"the options neglect explicit risk hedges"` — confirming the lock source extends to examples 1 or 2, not just the now-changed example 3.

**Residual symptom:** Examples 1 and 2 in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` lines 224–225 still use "none of the options price in" and "the options assume" respectively. These are live template-lock sources, confirmed by run 05 gpt-5-nano output. The root cause (all three examples using "the options" as the critique's grammatical subject) was not fully addressed.

**B2 — Remove duplicate examples from `Lever` Pydantic field description**
Resolved cleanly. Token savings confirmed: `activity_overview.json` for llama3.1 parasomnia run 03 shows `input_tokens: 6433`, a reduction consistent with the ~150–200 token saving per call. The consequences contamination bug ("A weakness in this approach is that…" in the `consequences` field) is absent in run 03 — absent in all 16 gta_game levers — a probable downstream benefit of removing the doubled example signal.

---

## Quality Comparison

Models appearing in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5.

| Metric | Before (runs 96–02) | After (runs 03–09) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 = 100.0% | 34/35 = 97.1% | REGRESSED (-2.9pp) |
| **LLMChatErrors** | 0 | 1 (run 04, gpt-oss-20b, sovereign_identity: JSON EOF at line 58) | REGRESSED (likely non-deterministic) |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (< 3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High; exact-match dedup only | High; typo duplicate confirmed (run 03: "Multplayer Modes" + "Multiplayer Modes") | UNCHANGED / minor |
| **Template leakage — llama3.1 gta_game** | 16/16 = 100% "The options [verb]" | 10/16 = 62.5% "The options [verb]" (calls 2–3: ~100%, call 1: new lock "[Lever name] lever [verb]") | PARTIALLY IMPROVED |
| **Template leakage — llama3.1 parasomnia** | 11/12 = 92% | 18/18 = 100% | REGRESSED |
| **Template leakage — gpt-5-nano** | Not tracked | Present (run 05, lever 2: "the options neglect") | PERSISTS |
| **Review format compliance** | Stable | Stable | UNCHANGED |
| **Consequence chain format** | Stable | Stable | UNCHANGED |
| **Content depth (avg option length)** | Stable | Stable | UNCHANGED |
| **Cross-call duplication** | Monitored | Monitored | UNCHANGED |
| **Over-generation (> 7 levers/call)** | Not observed | Not observed | UNCHANGED |
| **Consequences contamination (llama3.1)** | Present (run 96, levers 1–6: "A weakness in this approach is that…") | Absent (run 03) | **FIXED** |
| **Fabricated % claims in consequences (llama3.1 gta_game)** | 0 (run 96) | 5 (run 03, levers 1–6: "by at least 20/15/25/30/20%") | **NEW REGRESSION** |
| **Fabricated % claims — other models** | Stable | Stable | UNCHANGED |
| **Marketing-copy language** | Stable | Stable; run 03 levers contain "cutting-edge" in lever 3 consequences | UNCHANGED |
| **Partial recovery events** | 4 (runs 96, 99, 01×2) | 2 (run 03×2) | IMPROVED |
| **Field length ratios vs baseline** | Stable | Stable (llama3.1 run 03 gta_game review: ~0.68×, consistent with formulaic brevity) | UNCHANGED |
| **B2 token savings** | N/A (doubled) | ~150–200 tokens saved per call (verified via activity_overview.json) | **IMPROVED** |

**OPTIMIZE_INSTRUCTIONS alignment:**
The current OPTIMIZE_INSTRUCTIONS (lines 27–80) contains a contradiction: lines 77–79 praise the agriculture example ("none of the options price in the idle-wage burden") as "the correct structural template" while line 224 shows that same example still uses "none of the options" — an options-centric opener that weaker models copy. This partial-accuracy in the documentation now misleads: a developer following lines 77–79 would not recognise example 1 as a template-lock source. Additionally, two new patterns confirmed in runs 03–09 are not yet documented:
1. Multi-call template divergence (first call shifts format; later calls revert to old pattern due to stateless prompt re-exposure)
2. Replacement-example contamination (swapping one example can introduce a new leakage vector in a different field)

---

## New Issues

1. **Fabricated % claims introduced in llama3.1 first-call consequences.** Run 03 gta_game levers 1–6 all contain fabricated magnitude claims in `consequences`: "by at least 20%", "by at least 15%", "by at least 25%", "by at least 30%", "by at least 20%". These were zero in run 96. The most plausible explanation is that the replacement example 3's causal-chain structure ("a regional hurricane season can correlate all three simultaneously") cued llama3.1 into appending magnitude estimates to consequence sentences. This directly contradicts the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers and the system prompt section 2 prohibition. **This is the most actionable new regression from this PR.**

2. **Lock displacement rather than elimination.** The gta_game improvement (100% → 62.5%) hides a structural shift: first-call levers now use "[Lever name] lever [verb]" — itself a formulaic pattern across all 6 first-call levers. The lock moved within the call sequence, it was not broken. All second- and third-call levers (7–16) remain at ~100% "The options [verb]".

3. **OPTIMIZE_INSTRUCTIONS self-contradiction.** Lines 77–79 describe example 1 as "the correct structural template" but example 1 still uses "none of the options price in" — a copyable options-centric opener. This note was correct in the sense that the tail is non-portable, but it incorrectly implies the opener is safe. Future developers relying on this note will not recognise example 1 as a template-lock risk.

4. **gpt-oss-20b JSON truncation failure** (run 04, sovereign_identity). A single plan failed with `EOF while parsing a list at line 58 column 5`. This is likely non-deterministic (B2 reduces prompt token count, making truncation *less* likely, not more). Not credibly caused by PR #340.

---

## Verdict

**CONDITIONAL**: Keep B2 (duplicate example removal) unconditionally; B1 (example 3 replacement) is a partial fix that must be followed up by replacing all three examples.

B2 is a clean, verified improvement: ~150–200 token savings per call, consequences contamination eliminated, no downsides detected. It should be kept regardless of the B1 outcome.

B1 fell short of its stated goal (eliminate the 100% gta_game and 92% parasomnia lock). The partial improvement in gta_game (100% → 62.5%) validates the hypothesis that example replacement shifts the lock, but fixing one of three equally lock-prone examples is insufficient. The fabricated % regression introduced by the replacement example is a content quality hit that affects llama3.1's first-call output across all plans using gta_game-style prompts. The PR is acceptable to keep because B2's benefits outweigh B1's shortfall, but a follow-up PR replacing all three examples is required before this issue is considered resolved.

---

## Recommended Next Change

**Proposal:** Replace all three `review_lever` examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 224–226) with domain-specific critiques whose grammatical subject is never "the options", "none of the options", or any options-as-subject construction. Simultaneously verify the replacement example 3's consequences text contains no percentage claims or quantitative causal chains that could cue fabricated magnitude claims in llama3.1.

**Evidence:**
- Example 2 (`identify_potential_levers.py:225`) uses "the options assume permits will clear on the standard timeline" — the direct source of the persistent "The options assume…" pattern in parasomnia run 03 (18/18 reviews).
- Example 1 (`identify_potential_levers.py:224`) uses "none of the options price in" — structurally equivalent opener; still produces "The options…"-style copying.
- Example 3 (post-PR) ends with "correlation risk absent from every option" — still options-anchored; and its causal structure introduced 5 fabricated % claims in run 03 gta_game levers 1–6 consequences.
- gpt-5-nano run 05 lever 2 contains "the options neglect" — proved examples 1 or 2 are the active source after example 3 was changed.
- Partial improvement (gta_game call 1: 100% → 62.5%) confirms that changing one example does shift the pattern. The synthesis predicts changing all three completes the shift.
- The current OPTIMIZE_INSTRUCTIONS (lines 73–79) documents the failure mode precisely but contains a self-contradiction by praising example 1 as the correct template.

**Verify in next iteration:**
- llama3.1 gta_game: "The options [verb]" rate across all three calls (target: < 20% in all calls, not just call 1)
- llama3.1 parasomnia: "The options [verb]" rate (was 100% in run 03; target: meaningfully reduced)
- llama3.1 gta_game consequences: fabricated "by at least X%" claims (target: 0, as in run 96)
- gpt-5-nano gta_game: confirm "the options neglect" is absent from lever reviews
- Partial recovery count (was 2 in run 03; monitor for changes)
- Field length ratios vs baseline (watch for new verbosity regressions from replacement examples)
- Call 1 vs calls 2–3 divergence: do all three calls now use consistent (non-options-centric) patterns?

**Risks:**
1. Each replacement example could itself introduce a new portable copyable pattern. The PR #340 experience (replacement introduced "[Lever name] lever [verb]" as a new first-call lock) is the canonical cautionary example. New examples must be reviewed for portability before merging.
2. If replacement examples include quantitative language (specific numbers, percentages), llama3.1 may copy them into `consequences`. New examples must model qualitatively framed consequences exclusively.
3. Changing all three examples simultaneously is a larger prompt change than changing one. If a regression appears in the next batch, it will be harder to isolate which example caused it. Consider testing with one changed example per iteration if attribution matters; accept the slower pace.
4. The OPTIMIZE_INSTRUCTIONS note (lines 73–79) must be corrected in the same PR — if it still praises example 1's opener as safe after example 1 is changed, future iterations will again replicate the same mistake.

**Prerequisite issues:** None. B2 is already in place (examples no longer duplicated in the Pydantic field description), so the system prompt is now the single injection point. The next PR edits three bullet strings in one location.

---

## Backlog

**Resolved and removable:**
- B1/B2 from analysis 27 (duplicate examples, lockable phrase "the options neglect" in example 3) — partially resolved by PR #340. B2 fully done. B1 partially done; carry forward as incomplete.
- Consequences contamination ("A weakness in this approach is that…") in llama3.1 — resolved in run 03. Monitor in next iteration to confirm it does not recur.

**Carry forward (unchanged):**
- Template lock "The options [verb]" — root cause unresolved; all three examples still use options-as-subject structure. Primary target for next PR.
- OPTIMIZE_INSTRUCTIONS self-contradiction (lines 77–79 praise example 1 as safe while it contains a copyable opener). Fix in same PR as example replacement.
- I1 / cross-field contamination validator (`consequences` field). Contamination appears resolved by B2 in run 03, but no structural validator enforces it. Low priority while contamination is absent; revisit if it recurs.
- I2 / relax `DocumentDetails min_length=5` for calls 2 and 3. Partial recovery count dropped from 4 to 2; monitor before acting.
- S1 / shared dispatcher thread-safety in `runner.py`. Affects usage-tracking side channel, not plan output. Defer.
- B4 / `Lever.options` field description says "Exactly 3" but validator enforces minimum 3. Clean fix, bundle with next prompt PR.
- gpt-oss-20b JSON truncation (run 04, sovereign_identity). Likely non-deterministic. Re-run to confirm before treating as a bug.
- Multi-call template divergence — add to OPTIMIZE_INSTRUCTIONS in next PR.
- Replacement-example contamination (new pattern from this analysis) — add to OPTIMIZE_INSTRUCTIONS in next PR.

**New additions:**
- **Fabricated % claims in llama3.1 consequences (run 03 gta_game, levers 1–6).** Introduced by PR #340. Appears linked to replacement example 3's causal sentence structure. Fix: ensure all replacement examples have qualitative consequences with no percentage claims. Verify in next iteration.
- **First-call vs later-call lock divergence.** New pattern: call 1 shifts to "[Lever name] lever [verb]" while calls 2–3 retain "The options [verb]". The lock must be verified across all three calls, not just call 1. Document in OPTIMIZE_INSTRUCTIONS.
