# Assessment: Positive framing, consistent word counts, and stronger number-evidence constraint

## Issue Resolution

**What PR #475 was supposed to fix** (from `pr_description`):

1. **Fix 1 — Consistent length targets**: Align all three sources (Pydantic field desc ×2, system
   prompt) to "2–3 sentences" for consequences. PR #473 left the system prompt at "2–4", which
   caused haiku 2.1× baseline verbosity.
2. **Fix 3 — Stronger number-evidence constraint**: "Never invent percentages, costs, or
   timeframes — only cite numbers that appear in the project context." Placed before the
   cause-effect directive to suppress gpt-oss-20b HK$ invention seen in PR #473.
3. **Positive framing**: Replace "Do NOT include 'Controls ... vs.'" with positive wording.
4. **Reduced output**: options "one sentence", review_lever "1–2 sentences" (same as #473).

**Is the issue resolved?**

| Claimed fix | Result | Evidence |
|---|---|---|
| Fix 1: haiku verbosity | **NOT FIXED** | haiku avg_cons: 515 → 557 chars (+8%). Insight: contradiction between "1–2 sentences" in Pydantic field desc (line 127) and "one sentence" in system prompt section 6 (line 260) — models received conflicting signals and averaged them. |
| Fix 3: fabricated numbers | **MADE WORSE** | Total HKD references: 5 → 20 (+4×). Dollar-sign references: 6 → 28 (+4.7×). gpt-oss-20b HKD: 1→6. haiku HKD: 3→11, $: 4→19. |
| Positive framing | **NEUTRAL** | Zero "Controls X vs Y" in both batches — no downside, no observable effect. |
| Reduced output | **NEGLIGIBLE** | Avg options: 479.3 → 477.8 (−0.3%). Avg review: 198.8 → 192.3 (−3.3%). Within noise. |

**Residual symptoms from prior PRs:** The secondary "All three options X, but none Y" haiku template
lock (~85% in hong_kong_game) introduced by PR #358 is still present. Confirmed from reading
`history/5/10_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
of the first 7 lever reviews, 6 use the pattern ("All three options manage…, but none directly
addresses…"; "All three options balance…, but none directly solves…", etc.). PR #475 did not
target this issue, so it is unchanged. The "tension" opener lock (target of PR #358) remains at 0%.

**Fabrication confirmed from sampled files:**

- `history/5/05.../20260310_hong_kong_game/002-10-potential_levers.json` — gpt-oss-20b "Capital
  Allocation and Incentive Lever": options cite `HK$141 million` (≈30% of HK$470M),
  `HK$117.5 million` (≈25%), `HK$70.5 million` (≈15%) — all derived by arithmetic from the
  plan's real HK$470M budget; none appear verbatim in the plan.
- `history/5/10.../20260310_hong_kong_game/002-10-potential_levers.json` — haiku "Financing
  Structure and Mainland China Exposure": cites "Hong Kong Film Development Fund (up to HK$75M)"
  — plan mentions the Fund but gives no dollar amount. "Release Strategy" lever: "premium VOD
  pricing (HK$60-80 for 48-hour rental, modeled on recent high-profile releases)" — entirely
  fabricated from domain knowledge.

---

## Quality Comparison

All 7 models appear in both batches (llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini,
gemini-2.0-flash, haiku-4-5). Full comparison valid.

| Metric | Before (2/87–93) | After (5/04–10) | Verdict |
|--------|-----------------|-----------------|---------|
| **Overall call success rate** | 35/35 = 100% | 35/35 = 100% | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High, no duplicates observed | High, no duplicates observed | UNCHANGED |
| **Template leakage ("Controls X vs Y" in name)** | 0 | 0 | UNCHANGED |
| **Review format ("Controls X vs Y" pattern)** | 0 | 0 | UNCHANGED |
| **Consequence chain (Immediate→Systemic→Strategic)** | N/A (not in prompt) | N/A (not in prompt) | UNCHANGED (N/A) |
| **Content depth — avg options total (chars)** | 479.3 | 477.8 | UNCHANGED (−0.3%) |
| **Cross-call duplication** | Low | Low | UNCHANGED |
| **Over-generation (>7 levers/call, informational)** | haiku: 93 total levers | haiku: 101 levers (+8.6%) | SLIGHT INCREASE (gta_game domain effect; handled by DeduplicateLeversTask) |
| **Field length vs baseline — name** | 36.2 (1.31× baseline) | 36.0 (1.30×) | UNCHANGED |
| **Field length vs baseline — consequences** | 297.8 (1.07× baseline) | 299.8 (1.07×) | UNCHANGED |
| **Field length vs baseline — options** | 479.3 (1.06× baseline) | 477.8 (1.06×) | UNCHANGED |
| **Field length vs baseline — review** | 198.8 (1.31× baseline) | 192.3 (1.26×) | UNCHANGED (−3.3%, within noise) |
| **Haiku avg_cons (chars)** | 515 | 557 | **REGRESSED +8%** |
| **Fabricated quantification — HKD refs (total)** | 5 | 20 | **REGRESSED +4×** |
| **Fabricated quantification — $ refs (total)** | 6 | 28 | **REGRESSED +4.7×** |
| **Fabricated quantification — Pct% claims (total)** | 39 | 40 | UNCHANGED (+2.6%, within noise) |
| **gpt-oss-20b HKD fabrication** | 1 | 6 | **REGRESSED +6×** |
| **haiku HKD fabrication** | 3 | 11 | **REGRESSED +3.7×** |
| **qwen3 Pct% claims** | 4 | 1 | IMPROVED −75% |
| **Marketing-copy language (hype phrases)** | Low, stable | Low, stable | UNCHANGED |
| **LLMChatErrors / ValidationErrors** | 0 | 0 | UNCHANGED |
| **"Tension" opener lock (haiku, all plans)** | 0% (fixed in PR #358) | 0% | UNCHANGED (fix held) |
| **"All three options X, but none Y" lock (haiku)** | ~85% hong_kong_game (run 93) | ~86% hong_kong_game (run 5/10, 6/7 levers sampled) | UNCHANGED (not targeted by PR #475) |

**Baseline ratios**: All field lengths remain under 1.31× baseline — well within the 2× warning
threshold. No field-length regression from this PR.

**OPTIMIZE_INSTRUCTIONS alignment**: PR #475 does not update OPTIMIZE_INSTRUCTIONS. The existing
entries (fabricated numbers at lines 52–54, template-lock migration at lines 73–82, field-description
template lock at lines 86–92) remain accurate. However, the "Fabricated numbers" entry (lines 52–54)
says "Do not invent percentages, cost savings, market-share figures, or performance deltas" — it does
not distinguish *direct invention* from *arithmetic derivation* from real plan numbers. This is the
loophole that drove the 4× HKD regression. The PR moved the constraint position but did not close
the semantic gap. OPTIMIZE_INSTRUCTIONS should be updated to document arithmetic derivation as a
distinct failure mode (see Recommended Next Change).

---

## New Issues

1. **B2 (Medium) — Contradictory review_lever length targets introduced by PR #475.**
   `Lever.review_lever` field description at line 127 says "1–2 sentences"; system prompt section 6
   at line 260 says "one sentence (20–40 words)." This contradiction was introduced by the PR (which
   updated the field description to "1–2 sentences" but left section 6 unchanged). Models receive
   conflicting signals: haiku follows the Pydantic field description (which is injected directly
   into the structured-output JSON schema) over the system prompt, producing reviews averaging
   ~310 chars (~60 words) — well above the 40-word system-prompt cap. This is the direct cause of
   Fix 1's failure.

2. **B3 (Critical for quality) — Anti-fabrication constraint permits arithmetic derivation.**
   The constraint "Never invent percentages, costs, or timeframes — only cite numbers that appear
   in the project context" reads as a permission floor: models cite real plan numbers AND derive
   additional amounts from them. The wording does not prohibit: (a) arithmetic splitting
   (HK$470M → HK$141M at 30%); (b) domain-knowledge extrapolation (HK$75M Film Development Fund
   subsidy); (c) analogical pricing ("HK$60–80 for 48-hour rental, modeled on recent releases").
   The 4× HKD regression traces directly to this semantic gap. Confirmed across gpt-oss-20b (run
   5/05) and haiku (run 5/10) hong_kong_game outputs.

3. **B1 (Low, latent) — Python closure captures loop variable by reference.**
   In `identify_potential_levers.py:315–325`, the `execute_function` closure refers to
   `messages_snapshot` by name. In synchronous execution this is safe (closure called before
   re-assignment). If `llm_executor.run()` is ever made async, the closure could capture a later
   iteration's snapshot. Low severity today; maintenance risk if execution model changes.

4. **Arithmetic derivation not documented in OPTIMIZE_INSTRUCTIONS.** The existing "Fabricated
   numbers" entry (lines 52–54) does not distinguish arithmetic derivation from direct invention.
   Future analysis agents will not recognize the pattern from OPTIMIZE_INSTRUCTIONS alone. Should
   be added in the next PR.

---

## Verdict

**CONDITIONAL**: The PR preserved all structural gains from PR #358 (100% success rate, zero
template leakage, zero validation errors, zero LLMChatErrors), and the positive-framing change is
correct. However, both stated quality improvements failed: Fix 1 (verbosity) had no effect due to
a self-introduced contradiction (B2), and Fix 3 (fabrication) made fabrication 4× worse by
strengthening a constraint that models interpret as a permission floor rather than a ceiling (B3).
Keep the cosmetic/structural changes; the fabrication regression requires an immediate follow-up PR
that explicitly prohibits arithmetic derivation from real plan numbers.

---

## Recommended Next Change

**Proposal**: Extend the anti-fabrication constraint to explicitly prohibit arithmetic derivation
from real plan numbers. Apply at two locations in `identify_potential_levers.py`: the
`Lever.consequences` Pydantic field description (lines 113–117) and system prompt section 2
(line 232). Also align the `review_lever` length target across the field description (line 127)
and system prompt section 6 (line 260) to eliminate the B2 contradiction.

**Evidence**: Strong and multi-source.

- gpt-oss-20b run 5/05 hong_kong_game: options cite HK$141M, HK$117.5M, HK$70.5M — all arithmetic
  derivations of HK$470M (plan provides only the total). None appear verbatim in plan.
- haiku run 5/10 hong_kong_game: "Hong Kong Film Development Fund (up to HK$75M)" — plan mentions
  the Fund but gives no subsidy figure; "HK$60–80 for 48-hour rental, modeled on recent releases" —
  fabricated from domain knowledge.
- HKD total: 5 → 20 (+4×); $ total: 6 → 28 (+4.7×) across the full 7-model batch.
- Both insight_claude and code_claude (analysis 71) independently trace all three fabrication
  patterns to the same semantic gap in the constraint wording.
- The synthesis (analysis 71) provides exact replacement wording for both locations.

**Exact wording (from synthesis, analysis 71):**

Location 1 — `Lever.consequences` field description (lines 113–117):
```
"Never invent percentages, costs, or timeframes. "
"Do not perform arithmetic on plan numbers to produce derived figures — "
"if a specific sub-allocation, percentage split, or per-unit price is not stated "
"verbatim in the project context, omit it entirely. "
"Only reference numbers that appear word-for-word in the project context. "
```

Location 2 — System prompt section 2 (line 232):
```
Never invent percentages, costs, or timeframes. Do not perform arithmetic on plan numbers
to produce derived figures — if a specific sub-allocation, percentage split, or per-unit
price is not stated verbatim in the project context, omit it entirely. Only reference
numbers that appear word-for-word in the project context.
```

Also bundle in the same PR (low effort, fixes B2): update system prompt section 6 (line 260)
from "one sentence (20–40 words)" to "1–2 sentences" to match the field description at line 127,
or vice versa — the synthesis recommends the more permissive "1–2 sentences" as consistent with
PR #475's intent.

Also bundle: add "Arithmetic derivation" to OPTIMIZE_INSTRUCTIONS (lines 52–54) distinguishing
it from direct fabrication.

**Verify in the next iteration:**

- **Primary**: Total HKD references across both hong_kong_game runs (gpt-oss-20b and haiku).
  Target: drop from 20 back to ≤5 (before-PR #475 level).
- **gpt-oss-20b (run 5/05)**: Specifically check "Capital Allocation and Incentive Lever" options.
  HK$141M, HK$117.5M, HK$70.5M should disappear. Confirm the HK$470M base figure is still
  cited correctly (it is real and should still be allowed).
- **haiku (run 5/10)**: Verify HK$75M (Film Development Fund) and "HK$60–80 for 48-hour rental"
  disappear. Verify haiku still produces financing-domain levers with qualitative language for
  amounts not in the plan.
- **gpt-5-nano**: Moderate regression (HKD 1→3). Should drop to ≤1.
- **qwen3-30b**: Already improved (pct% 4→1). Should remain at ≤1.
- **llama3.1, gpt-4o-mini, gemini**: Were at 0 HKD/$ in both batches; confirm no regression.
- **Review verbosity (haiku)**: After aligning the length targets, haiku avg review should drop
  from ~310 chars (~60 words) toward the 40-word system-prompt cap. If it doesn't, investigate
  whether the field description or system prompt is being weighted more heavily.
- **Field length ratios**: All fields were at 1.06–1.31× baseline before the PR; should remain
  below 2× after the fabrication fix. Watch for overcorrection (models becoming too terse when
  explicitly prohibited from citing numbers).

**Risks:**

- **Overcorrection / omission**: "Only reference numbers that appear word-for-word" may cause
  models to omit even verbatim plan numbers (HK$470M, HK$195M) from consequences and options.
  The fix must preserve legitimate citation of real plan figures. The phrase "appear word-for-word"
  is key — watch for models interpreting it too literally and stripping all numerical context.
- **Domain-knowledge extrapolation edge case**: haiku's HK$75M fabrication was grounded in domain
  knowledge of the Film Development Fund (the plan mentions the fund; haiku inferred a plausible
  amount). "Word-for-word" prohibition should catch this (HK$75M is not in the plan). Verify haiku
  references the Fund qualitatively ("the Hong Kong Film Development Fund, which offers cash
  incentives for qualifying productions") without inventing a dollar amount.
- **Constraint duplication may amplify engagement** (speculative, I6 from code_claude): The
  anti-fabrication constraint appears identically in both the Pydantic field description and
  system prompt. Doubled emphasis may cause models to engage more deeply with financial plan data
  (satisfying the "cite from context" directive) and then derive from it. If Direction 1 does not
  reduce fabrication sufficiently, experiment with removing the constraint from the field
  description and keeping it only in the system prompt, to isolate which location drives behavior.
- **"All three options" secondary lock** still present in haiku at ~85%. The next iteration
  should note whether the fabrication fix changes lever content in ways that also affect the lock
  rate, but this is not expected — the issues are orthogonal (one affects what numbers models
  cite; the other affects how they phrase the review's gap statement).

**Prerequisite issues**: None. The fabrication constraint fix is standalone. The B2 alignment fix
(review_lever length) is also standalone and should be bundled.

---

## Backlog

**Resolved — remove from backlog:**
- Nothing from the prior backlog (analysis 40) is resolved by PR #475.

**Status update — carry forward from analysis 40:**
- **HIGH (carried): Secondary "All three options X, but none Y" template lock.** Still active in
  haiku at ~85–90% (run 5/10 hong_kong_game: 6/7 sampled reviews use this pattern). PR #475 did
  not target this. Next PR after the fabrication fix should address
  `identify_potential_levers.py:120–124` ("state the specific gap the three options leave
  unaddressed" → "name a real-world constraint or risk that all three strategies collectively
  sidestep — expressed in domain-specific terms"). See analysis 40 assessment for exact wording.
- **LOW (carried): Stale `LeverCleaned.review` field description.** `identify_potential_levers.py:212`
  still says "names the core tension." No runtime impact. Bundle with next housekeeping PR.
- **LOW (carried): Wrong model name in `check_option_count` docstring.** Line 143 says "Run 82
  (llama, gta_game)"; correct is "Run 80 (llama3.1, gta_game)". Bundle with next housekeeping PR.
- **MEDIUM (carried): `partial_recovery` conflates early loop-exit with genuine call failure.**
  `runner.py:517–523`. Low urgency — well-understood in analysis notes. Implement `early_exit`
  event type when analysis tooling needs programmatic distinction.
- **MEDIUM (carried): Field-name rejection validator for `options`.** `check_option_count`
  accepts any 3-item list including literal field names. Stochastic, seen once in run 86 haiku.

**New — add to backlog:**
- **CRITICAL: Fix 3 fabrication regression.** Anti-fabrication constraint (lines 113–117, 232)
  permits arithmetic derivation from real plan numbers. Active regression: HKD +4×, $ +4.7×.
  Requires semantic extension of constraint wording to explicitly prohibit derived arithmetic and
  domain-knowledge extrapolation. Target for next PR (see Recommended Next Change).
- **MEDIUM: B2 — review_lever length contradiction.** Line 127 ("1–2 sentences") contradicts
  line 260 ("one sentence (20–40 words)"). Introduced by PR #475. Bundle with fabrication fix PR.
- **LOW: Document arithmetic derivation in OPTIMIZE_INSTRUCTIONS.** Lines 52–54 cover "fabricated
  numbers" but do not distinguish arithmetic derivation from direct invention. Add 2–3 sentences
  distinguishing the two failure modes. Bundle with next PR.
- **LOW: B1 — Python closure latent bug.** `execute_function` in adaptive loop captures
  `messages_snapshot` by name, not value (`identify_potential_levers.py:315–325`). Safe in
  synchronous execution; risk if executor becomes async. Fix: `def execute_function(llm,
  _msgs=messages_snapshot)`. Bundle with next code-quality pass.
