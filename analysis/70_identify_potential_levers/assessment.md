# Assessment: Replace negative-priming with positive framing and reduce output verbosity in identify step

## Issue Resolution

**What PR #473 was supposed to fix:**

1. **Positive framing**: Replace `"Do NOT include 'Controls ... vs.', 'Weakness:'"` with `"Focus on cause-effect relationships and factual outcomes"` in the `consequences` field description (both `Lever` and `LeverCleaned`).
2. **Reduced output targets**: consequences 2–4 → 2–3 sentences, options "full sentence" → "one sentence", review_lever to "1–2 sentences".
3. **Primary goal**: Help gpt-oss-20b complete within 600s. The step makes 3 LLM calls per plan; slow providers take 200–1000s per call. PR #471 caused 5/5 gpt-oss-20b plans to timeout; this PR supersedes it.

**Is the issue resolved?**

**Goal 1 (positive framing): NEUTRAL.**
The "Controls X vs. Y. Weakness:" pattern was already absent in the before batch (runs 2/87–93, PR #358): 0/633 levers in before, 0/646 levers after. The change was preventative, not corrective. No measurable improvement.

**Goal 2 (output reduction): MIXED — failed for the most important model.**
Most models showed modest length reductions (gpt-oss-20b consequences: −15%; qwen3: −11%; others ±5%). However, haiku — the only model exceeding the 2× verbosity warning threshold — increased consequences length by +13% (515 → 584 chars, 1.8× → 2.1× baseline). The PR's stated reduction goal was not achieved for the model that needed it most. Root cause confirmed: the PR updated the field description to "2–3 sentences" (line 118) but left the system prompt at "2–4 sentences" (line 232), creating contradictory guidance. Haiku appears to weight the system prompt over the field description.

**Goal 3 (gpt-oss-20b timeout fix): PARTIAL.**
Compared to PR #471 (0/5 completions), PR #473 recovers to 3/5 — an improvement. However, compared to the before batch (PR #358, the best-known baseline: 5/5 completions, max 209s), gpt-oss-20b is now at 3/5 with silo (600s timeout) and parasomnia (600s timeout) still failing. The fix is insufficient relative to the pre-regression baseline.

**Residual symptoms:**
- haiku's "None of the options" / "All three options" template lock (~85% rate in hong_kong_game), introduced by PR #358's field description change, persists unchanged — PR #473 did not address this.
- The B1 length inconsistency means haiku's verbosity increased rather than decreased.

---

## Quality Comparison

Models present in **both** batches: llama3.1 (2/87 vs 4/97), gpt-oss-20b (2/88 vs 4/98), gpt-5-nano (2/89 vs 4/99), qwen3-30b-a3b (2/90 vs 5/00), gpt-4o-mini (2/91 vs 5/01), gemini-2.0-flash (2/92 vs 5/02), haiku-4-5 (2/93 vs 5/03). All 7 models in both batches; comparison fully valid.

| Metric | Before (2/87–93, PR#358) | After (4/97–5/03, PR#473) | Verdict |
|--------|--------------------------|---------------------------|---------|
| **Success rate — gpt-oss-20b plans** | 5/5 (100%) | 3/5 (60%) | REGRESSION −40pp |
| **Success rate — haiku partial recovery plans** | 2/5 | 2/5 | UNCHANGED |
| **Success rate — all other models** | 5/5 each (100%) | 5/5 each (100%) | UNCHANGED |
| **Success rate — overall plan completion** | 35/35 (100%) | 33/35 (94%) | REGRESSION |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High | High | UNCHANGED |
| **"Controls X vs Y / Weakness:" pattern** | 0 | 0 | UNCHANGED |
| **Consequence chain (Imm→Syst→Strat)** | Not in prompt | Not in prompt | N/A |
| **haiku consequences length vs baseline** | 515 chars / 1.8× | 584 chars / **2.1×** | REGRESSION (exceeds 2× warning) |
| **gpt-oss-20b consequences length vs baseline** | 283 chars / 1.0× | 240 chars / 0.9× | slight IMPROVEMENT |
| **gemini consequences length vs baseline** | 362 chars / 1.3× | 345 chars / 1.2× | slight IMPROVEMENT |
| **Other models consequences vs baseline** | 0.6–1.0× | 0.6–0.9× | UNCHANGED |
| **haiku review length vs baseline** | 321 chars / 2.1× | 343 chars / 2.3× | REGRESSION |
| **Fabricated % claims — gpt-oss-20b** | 0 occurrences | **4 occurrences** | REGRESSION |
| **Fabricated $ amounts — gpt-oss-20b** | 1 occurrence | **5 occurrences** | REGRESSION |
| **Fabricated time — gpt-oss-20b** | 1 occurrence | **3 occurrences** | REGRESSION |
| **Fabricated % claims — haiku** | 5 occurrences | **9 occurrences** | REGRESSION |
| **Fabricated time — haiku** | 9 occurrences | **15 occurrences** | REGRESSION |
| **llama3.1 "primary trade-off" template lock** | 5/82 = 6.1% | 7/87 = 8.0% | slight REGRESSION |
| **haiku "None of options" template lock (hong_kong_game)** | ~85% (residual from PR #358) | ~85% | UNCHANGED (not addressed) |
| **Marketing-copy language** | 0 | 0 | UNCHANGED |
| **System prompt / field desc consistency** | Consistent | **Inconsistent** (B1: "2–3" vs "2–4"; B2: "1–2 sentences" vs "one sentence") | NEW BUG |

Evidence for fabricated numbers:
- `history/4/98_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
  - "Budget Allocation" lever: "Shifting 10% of the production budget to digital set extensions reduces on‑location shooting days by two, saving HK$5m in permit costs"
  - "Audience Engagement" lever: "will raise P&A by roughly HK$10m, potentially boosting Hong Kong box office by 15% of the target gross"
  - "Risk Mitigation" lever: "The added legal fees of HK$2m"
  - "Marketing Narrative" lever: "potentially increasing domestic ticket sales by 10%"
  None of these figures appear in the project context.

Evidence for haiku verbosity regression:
- `history/5/03_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`: Consequences fields average 580+ chars; options fields contain multi-clause sentences exceeding 100 words each.

Evidence for haiku template lock persistence:
- `history/5/03_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`: Reviews include "None of the options guarantee both critical acclaim and commercial pre-sales momentum simultaneously", "All three options struggle with the fundamental problem...", "None of the options provides simultaneous cost relief and creative freedom", "None fully reconciles authentic environment with production efficiency" — essentially every lever has a "None/All three options" terminal clause.

**OPTIMIZE_INSTRUCTIONS alignment:**
- OPTIMIZE_INSTRUCTIONS warns against fabricated numbers (lines 52–55): gpt-oss-20b and haiku are regressing on this metric. The `consequences` field description now says "Focus on cause-effect relationships and factual outcomes" immediately before the "only cite numbers if the project context provides evidence" constraint. Models may satisfy the cause-effect requirement by inventing metrics.
- OPTIMIZE_INSTRUCTIONS warns against verbosity amplification: haiku now exceeds the 2× warning threshold at 2.1× on consequences.
- The PR does not update OPTIMIZE_INSTRUCTIONS to document the "cause-effect framing amplifies fabrication" pattern (a new failure mode worth adding).

---

## New Issues

1. **Consequences length target inconsistency (B1, HIGH, introduced by PR #473).**
   `identify_potential_levers.py:118` (field description): "Target length: 2–3 sentences."
   `identify_potential_levers.py:232` (system prompt section 2): "Target length: 2–4 sentences."
   PR #473 updated the field description but not the system prompt. This directly explains haiku's verbosity increase: haiku ignores the field description and follows the system prompt's looser "2–4" target. This is the most impactful new issue — it means the output-reduction goal cannot be verified until this inconsistency is resolved.

2. **review_lever length target inconsistency (B2, MEDIUM, introduced by PR #473).**
   `identify_potential_levers.py:127`: "1–2 sentences"
   `identify_potential_levers.py:260`: "one sentence (20–40 words)"
   Three conflicting sources exist for review_lever length (field description, system prompt section 4, system prompt section 6). Models resolve contradictions stochastically.

3. **Fabricated numbers regression for gpt-oss-20b (MEDIUM).**
   gpt-oss-20b had essentially clean output before (0 pct, 1 dollar, 1 time). After PR #473 it fabricates specific cost/time figures for the hong_kong_game plan (HK$2m, HK$5m, HK$10m, 15% box office, 4-week delay estimates). The positive "cause-effect relationships" framing likely reduces the psychological salience of the "only cite numbers if the project context provides evidence" constraint. All fabricated figures are in a single plan (4/98 hong_kong_game) — possibly exacerbated by that plan's rich financial context (HK$470m budget) providing a template for invented figures.

4. **gpt-oss-20b still times out on 2/5 plans (silo, parasomnia).**
   These plans fail consistently at 600s. The before batch completed all 5 plans in under 210s. The root cause (total token count × 3 calls × slow API latency) was not addressed structurally. A prompt-token audit of the two failing plans vs the three passing plans would clarify whether this is prompt size or API variability.

5. **haiku "None of the options" template lock persists (~85% rate).**
   This was identified as a new secondary lock in analysis 40. PR #473 did not target it. It remains active in run 5/03 hong_kong_game (verified: nearly every review uses "None/All three options" terminal clause).

---

## Verdict

**CONDITIONAL**: Keep the PR because it partially recovers from PR #471's catastrophic gpt-oss-20b failure (0/5 → 3/5 completions) and its positive framing change is consistent with OPTIMIZE_INSTRUCTIONS practice. However, the PR falls short of the best baseline (PR #358) on gpt-oss-20b reliability (5/5 → 3/5), haiku verbosity (1.8× → 2.1×), fabricated numbers (worsened for both gpt-oss-20b and haiku), and introduces a confirmed bug (B1: system prompt / field description length inconsistency). The following fixes are required before this branch of optimization can make net progress:

1. Fix B1 (system prompt "2–4 sentences" → "2–3 sentences" at line 232).
2. Investigate and fix gpt-oss-20b remaining timeouts (silo, parasomnia).
3. Strengthen the number-evidence constraint adjacent to the "cause-effect relationships" directive to reverse the fabricated numbers regression.
4. Fix B2 (align review_lever length targets across all three sources).

---

## Recommended Next Change

**Proposal:** Fix the consequences length target inconsistency (B1) by changing `identify_potential_levers.py:232` from `"Target length: 2–4 sentences."` to `"Target length: 2–3 sentences."` This is a single-token change in one line. Bundle with direction 2 (reorder/strengthen the number-evidence constraint in the `consequences` field description) and direction 3 (align `review_lever` length targets and reword to break the "primary trade-off introduced by this lever" template lock) in the same PR.

**Evidence:** Compelling on B1. The synthesis cites the confirmed root cause chain: PR #473 changed field description line 118 to "2–3 sentences" but left system prompt line 232 at "2–4 sentences" → haiku follows system prompt → consequences grew +13% (515→584 chars, now 2.1× baseline) despite the stated output-reduction goal. The fix is purely mechanical: make both sources agree. Evidence for fabricated numbers is correlational (positive framing change preceded fabrication increase) but consistent across two models (gpt-oss-20b and haiku) and documented in the code review as a known risk pattern.

**Verify in the next iteration:**
- **B1 fix effect on haiku**: After system prompt update, confirm haiku consequences drop toward 1.8× or below. If haiku still exceeds 2× despite consistent "2–3 sentences" guidance, escalate to a `field_validator` character cap (~500 chars) as structural enforcement.
- **Fabricated numbers**: After reordering the number-evidence constraint to immediately follow the "cause-effect" directive, re-count fabricated pct/dollar/time occurrences for gpt-oss-20b (target: back to ~0) and haiku (target: ≤5). If gpt-oss-20b hong_kong_game still invents HK$ figures, investigate whether the plan's financial context (HK$470m budget) is amplifying the issue.
- **gpt-oss-20b timeouts**: After both B1 and number-constraint fixes, check if silo and parasomnia now complete. If still timing out, perform a token-count audit comparing those plans' system_prompt + user_prompt lengths against the 3 plans that complete (gta_game 564s, sovereign_identity 87s, hong_kong_game 265s) to determine whether prompt length or API latency variability is the primary driver.
- **llama3.1 "primary trade-off introduced" template lock**: After rewriting the review_lever field description to remove "the primary trade-off this lever introduces" as an opener phrase, verify the lock rate drops below 3% (from current 8%). Watch for lock migration to the replacement phrase.
- **haiku "None/All three options" template lock**: This was not targeted by PR #473. Confirm it still persists at ~85% in hong_kong_game. If the review_lever field description reword (direction 3) changes the lock rate, document the delta.
- **OPTIMIZE_INSTRUCTIONS**: Confirm the "cause-effect framing amplifies fabrication" pattern is added as a new entry after line 55 (per I5 in code_claude analysis 70).

**Risks:**
- **B1 fix may not be sufficient for haiku**: Even with consistent "2–3 sentences" guidance, haiku may still produce 500+ char consequences. If haiku ignores text-hint constraints regardless of consistency, a field_validator cap is the only structural recourse. Prepare this as a fallback.
- **Number-constraint reorder may reduce output grounding**: Moving the evidence constraint to immediately after the "cause-effect" directive could cause models to produce shorter, less grounded consequences (replacing fabricated metrics with vague qualitative language). Monitor that consequence specificity is maintained after the change.
- **gpt-oss-20b timeouts may be API latency variability**: If the two failing plans (silo, parasomnia) timeout due to server load variation unrelated to prompt size, no prompt change will reliably fix them. The PR description acknowledges this: "run 2/88 was on 2026-03-19 and run 4/98 was on 2026-03-31; server load differences cannot be ruled out." A retry at a different time with the same prompt would test this hypothesis before further optimization.
- **Template-lock migration on review_lever reword**: Per OPTIMIZE_INSTRUCTIONS lines 73–82, any new structural phrase in the review_lever field description may become the next locked opener. The proposed replacement must avoid making "the options" or any schema element the grammatical subject. The synthesis (analysis 40) provides tested draft wording: "name a real-world constraint or risk that all three strategies collectively sidestep — expressed in terms specific to this project's domain."

**Prerequisite issues:** B1 must be fixed before the output-reduction experiment is interpretable. Without consistent length guidance, haiku's verbosity measurement is confounded. All other direction 2–3 fixes can be bundled into the same single PR as B1.

---

## Backlog

**Resolved — remove from backlog:**
- "Do NOT include 'Controls X vs Y / Weakness:'" prohibitive language in consequences field description. Replaced with positive framing in PR #473. The pattern was already absent in the before batch; this change is complete and defensive.

**New — add to backlog:**
- **HIGH: Consequences length target inconsistency (B1).** `identify_potential_levers.py:232` still says "2–4 sentences" while field description (line 118) says "2–3 sentences". Confirmed root cause of haiku's verbosity regression. Fix: single-token change at line 232. Target for next PR.
- **HIGH: Fabricated numbers regression.** gpt-oss-20b hong_kong_game: 4 pct, 5 dollar, 3 time occurrences (all invented). Correlates with "Focus on cause-effect relationships" framing without adjacent number-evidence constraint. Fix: reorder sentences in `consequences` field description; add stronger "never invent numbers" reminder immediately after cause-effect directive. Also add to OPTIMIZE_INSTRUCTIONS (I5).
- **MEDIUM: review_lever length target inconsistency (B2).** Three conflicting sources: field description "1–2 sentences" (line 127), system prompt section 4 (no length), system prompt section 6 "one sentence (20–40 words)" (line 260). Fix: align all three to "one sentence (20–40 words)" as the canonical target.
- **MEDIUM: gpt-oss-20b timeout on silo and parasomnia.** Two of five plans consistently fail at 600s. First, audit token counts for these two plans vs the three that complete. If prompt size is the driver, shorten the system prompt (section-level token audit). If latency variability, schedule test reruns at off-peak times.

**Carry over from analysis 40 backlog (unchanged):**
- **HIGH: Secondary "None/All three options" template lock (haiku, ~85%).** `identify_potential_levers.py:120` — "the three options leave unaddressed." PR #473 did not address this. Still active in run 5/03 hong_kong_game. Target: rewrite review_lever field description to remove "the three options" as grammatical subject (per synthesis analysis 40, Direction 1, draft wording available).
- **MEDIUM: Field-name rejection validator for `options`.** `check_option_count` accepts any 3-item list including literal field names. One instance in haiku run 86. Low frequency; fix is ~6 lines.
- **MEDIUM: `partial_recovery` event conflates early-stop with genuine call failure.** `runner.py:577–583` fires for `calls_succeeded < 2`, which also triggers for legitimate 1-call early-stop (model generated ≥15 levers in one call). Analysis false-positive. Fix: add `lever_count` field to `PlanResult`; emit `early_exit` vs `partial_recovery` based on lever count vs min_levers.
- **LOW: Review length still above 2× baseline for haiku.** After run 5/03 haiku: consequences 2.1×, review 2.3×. Deferred until B1 fix is confirmed effective.
- **LOW: Wrong model name in `check_option_count` docstring.** `identify_potential_levers.py:143` says "Run 82 (llama, gta_game)" — run 82 is gpt-5-nano, not llama. Bundle with any housekeeping pass.
