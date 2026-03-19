# Assessment: fix: remove 'core tension' template lock from field description

## Issue Resolution

**What the PR was supposed to fix:** The `review_lever` field description contained the phrase
"name the core tension" (also present in Section 4 of the system prompt), which caused
near-universal "The tension is between X and Y" opener lock for llama3.1 (~100%) and haiku
(~75%) across all plans. PR #358 rewrote both locations to "identify the primary trade-off this
lever introduces, then state the specific gap the three options leave unaddressed," and changed
Section 6 from "under 2 sentences" to "one sentence (20–40 words)".

**Is the issue resolved?** Yes, definitively.

- **haiku (run 93 vs run 86) hong_kong_game:** "tension" opener dropped from 15/20 (75%) to
  0/20 (0%). Evidence: `history/2/86…/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  (review 1: "The tension lies between fidelity to source material…") vs
  `history/2/93…/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  (review 1: "Levers one through three attempt twist mitigation, but all three options require…").
- **llama3.1 (run 87 vs run 80):** "tension" opener dropped from ~100% to ~0%. Evidence:
  `history/2/87…/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  (review 1: "Not leveraging Hong Kong's existing infrastructure could lead to missed
  opportunities…" — no "tension" opener at all).
- Source code confirmed: `identify_potential_levers.py:116–124` (Lever.review_lever field
  description) and `identify_potential_levers.py:236` (Section 4 system prompt header) both
  now use "identify the primary trade-off… state the specific gap the three options leave
  unaddressed" — "core tension" is gone from both prompt-facing paths.

**Residual symptoms:** A secondary template lock has emerged. The replacement phrase "state the
specific gap the **three options** leave unaddressed" uses "the three options" as grammatical
subject, which models echo verbatim. In haiku hong_kong_game run 93, 17/20 reviews (85%) end
with "none of the three options address…" or "All three options X, but none directly Y."
Confirmed in `history/2/93…/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
levers 2–7 all open with "All three options…". The trigger is `identify_potential_levers.py:120`
— same mechanism as the original bug, different surface form. This is documented as a known
risk in OPTIMIZE_INSTRUCTIONS lines 73–82 ("Template-lock migration").

---

## Quality Comparison

Models present in **both** batches: llama3.1 (runs 80/87), gpt-oss-20b (81/88), gpt-5-nano
(82/89), qwen3-30b-a3b (83/90), gpt-4o-mini (84/91), gemini-2.0-flash-001 (85/92),
haiku-4-5 (86/93). All 7 models appear in both batches; full comparison is valid.

| Metric | Before (runs 80–86) | After (runs 87–93) | Verdict |
|--------|--------------------|--------------------|---------|
| **Overall call success rate** | 100/105 = 95.2% | 102/105 = 97.1% | IMPROVED +1.9pp |
| **Haiku call success rate** | 11/15 = 73.3% | 13/15 = 86.7% | IMPROVED +13.4pp |
| **llama3.1 call success rate** | 14/15 = 93.3% | 14/15 = 93.3% | UNCHANGED |
| **gpt-oss-20b / gpt-5-nano / qwen3 / gpt-4o-mini / gemini** | 15/15 each (100%) | 15/15 each (100%) | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Partial_recovery events (total)** | 4 (haiku: 3, llama: 1) | 3 (haiku: 2, llama: 1) | IMPROVED −1 |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High (no duplicates noted) | High | UNCHANGED |
| **Template leakage (field name in options)** | 1 (haiku run 86, "review_lever" as option) | 0 observed | IMPROVED (1→0; stochastic) |
| **"Tension" opener lock (haiku hong_kong_game)** | 15/20 = 75% | 0/20 = 0% | **FIXED** |
| **"Tension" opener lock (llama3.1)** | ~100% (run 80 gta_game) | ~0% (run 87) | **FIXED** |
| **"None/All three options" secondary lock (haiku)** | ~10% (run 86, occasional) | ~85% (run 93 hong_kong_game) | **REGRESSED — new secondary lock** |
| **Review format (old "Controls X vs Y" pattern)** | 0 (correctly absent) | 0 | UNCHANGED |
| **Consequence chain (Immediate→Systemic→Strategic)** | 0 (not in current prompt) | 0 | UNCHANGED (N/A) |
| **Content depth — haiku option length** | ~210 chars/option avg (run 86) | ~220–350 chars/option (run 93 hong_kong_game) | IMPROVED (more specific, plan-grounded) |
| **Cross-call duplication** | Low | Low | UNCHANGED |
| **Over-generation count (>7 levers per call)** | Haiku: 3/5 plans exit early (≥8 levers/call) | Haiku: 2/5 plans exit early | SLIGHT IMPROVEMENT |
| **Review length vs baseline — haiku silo** | ~300 chars / ~50 words = 3.3× baseline | ~260 chars / ~42 words = 2.9× baseline | SLIGHT IMPROVEMENT (still above 2× warning) |
| **Fabricated quantification (% claims)** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | 0 | 0 | UNCHANGED |

**Baseline note:** The `baseline/train/` data uses a "Controls X vs Y / Weakness:" review format
(~90 chars, ~17 words) with fabricated percentages in consequences ("15% increase in black
market activity", "30% reduction"). The current prompt correctly prohibits both patterns. The
baseline is useful as a *length* reference point but should not be used as a content quality
target.

**OPTIMIZE_INSTRUCTIONS alignment:**
PR #358 added two entries to OPTIMIZE_INSTRUCTIONS: "Field-description template lock" (lines
86–92) and "Template-lock migration" (implicitly lines 73–82 updated). Both are accurate and
useful. However, the PR simultaneously documents the failure mode and reintroduces it in
milder form: the new field description "state the specific gap the **three options** leave
unaddressed" violates the guidance in lines 73–78 ("Each example must name a domain-specific
mechanism or constraint directly rather than referencing 'the options' as grammatical subject").
The PR documents the rule and then breaks it — a detail that should be flagged in the next PR
message. No new violations of OPTIMIZE_INSTRUCTIONS goals (realistic/feasible/actionable) were
introduced.

---

## New Issues

1. **Secondary "None/All three options" template lock (confirmed, ~85% haiku).**
   After eliminating "The tension is between X and Y", haiku (run 93) shifted to
   "All three options X, but none [of the three options] address Y" in ~85% of hong_kong_game
   reviews and ~50% of silo reviews. Trigger: `identify_potential_levers.py:120` — "state the
   specific gap the **three options** leave unaddressed." The subject "three options" is mirrored
   verbatim. This is the same field-description template-lock mechanism as the original, predicted
   by OPTIMIZE_INSTRUCTIONS "Template-lock migration" entry. It is a softer lock than the original
   (the subject/content varies per lever; only the predicate "none address" is templated), but it
   affects ~85% of haiku reviews and likely affects other small models not yet checked in detail.

2. **Stale `LeverCleaned.review` field description (code hygiene, no runtime impact).**
   `identify_potential_levers.py:212` still reads: `"A short critical review — names the core
   tension, then identifies a weakness the options miss."` The PR updated `Lever.review_lever`
   but missed this field. The code comment (lines 208–210) confirms it is never serialized to
   an LLM, so there is no runtime effect. However, it's a copy-paste trap for future maintainers
   and directly contradicts the PR's stated goal.

3. **Wrong model name in `check_option_count` docstring (minor, no runtime impact).**
   `identify_potential_levers.py:143` says "Run 82 (llama, gta_game)". Run 82 is
   `openai-gpt-5-nano`, not llama. Run 80 is `ollama-llama3.1`. Misleads future debugging.

4. **Latent issue surfaced: llama3.1 partial_recovery shifted plans (not fixed).**
   Before (run 80): sovereign_identity was the plan with 2/3 calls. After (run 87): hong_kong_game
   is the plan with 2/3 calls. The count is unchanged (1 event per llama3.1 run), but the specific
   plan is different, confirming this is stochastic rather than plan-specific. Not a new regression.

---

## Verdict

**YES**: The primary template lock ("The tension is between X and Y") is definitively eliminated
for both llama3.1 and haiku (0% after vs 75–100% before), haiku's success rate improved +13.4pp
(73.3%→86.7%), overall success rate improved +1.9pp (95.2%→97.1%), and no regressions appeared
on the five previously-clean models. The secondary "None/All three options" lock (~85% haiku) is
a known, documented failure mode (template-lock migration) that is milder than the original and
is the clear target for the next iteration.

---

## Recommended Next Change

**Proposal:** Rewrite the `review_lever` field description (line 116–124) to remove "the three
options" as grammatical subject. Replace "state the specific gap the three options leave
unaddressed" with "name a real-world constraint or risk that all three strategies collectively
sidestep — expressed in terms specific to this project's domain." Apply the same rewrite to the
Section 4 header at `identify_potential_levers.py:236`. Bundle the `LeverCleaned.review` cleanup
(B1) into the same PR since it's trivial.

**Evidence:** Compelling. The synthesis (analysis 40) cites a specific, confirmed causal chain:
- `identify_potential_levers.py:120` says "the three options leave unaddressed"
- Run 93 haiku hong_kong_game shows 17/20 reviews (85%) containing "none of the three options
  address…" or "All three options X, but none Y"
- Both agents (insight_claude, code_claude) independently identify the same root cause
- OPTIMIZE_INSTRUCTIONS lines 73–82 predict this failure mode precisely
- The proposed rewording ("a real-world constraint or risk that all three strategies collectively
  sidestep") avoids making "the options" the grammatical subject and forces domain-specific content

**Verify in the next iteration:**
- **Primary target:** Count "none of the three options address" / "All three options" opener rate
  for haiku (run 93 → next run, hong_kong_game and silo). Target: drop from 85% to <20%.
- **llama3.1:** Check for the same lock in llama3.1 after runs — it was not deeply sampled in
  analysis 40 beyond confirming the "tension" lock was gone.
- **gpt-4o-mini and gemini:** Check for "None/All three options" pattern in runs 91/92 (not
  sampled in analysis 40). Determine whether the secondary lock is haiku+llama3.1-only or broader.
- **Template-lock migration:** Watch whether the new phrase "all three strategies collectively
  sidestep" or "real-world constraint" becomes the next locked subphrase. If it does, the
  OPTIMIZE_INSTRUCTIONS "Template-lock migration" entry (lines 69–82) already provides guidance.
- **Haiku success rate:** Confirm it stays at or above 86.7% (13/15 calls) — the improvement
  in analysis 40 was likely partly due to shorter required output ("one sentence"), not just the
  field description change. Regression here would suggest the length constraint is the primary
  driver.
- **Template leakage (field name in options):** Check whether the "review_lever" option-value
  defect (seen in run 86 haiku gta_game) reappears. It was stochastic and the field-name
  validator (recommended in analysis 39) was never implemented.

**Risks:**
- **New subphrase lock:** The phrase "all three strategies collectively sidestep" contains
  "all three strategies" — potential mirror point for models if the subject-referencing pattern
  persists. The OPTIMIZE_INSTRUCTIONS warning is clear: avoid any phrase that references
  the options/strategies as grammatical subject. The draft wording in the synthesis should
  be checked against this criterion before merging.
- **Review content regression:** The current "All three options X, but none Y" lock, while
  structurally uniform, does produce plan-specific content in the X and Y slots (verified in
  run 93 hong_kong_game levers). If the new wording produces more generic gap statements (e.g.,
  "the project's resource constraints"), that would be a content quality regression worth
  tracking even if structural lock rate drops.
- **Haiku partial_recovery events:** Two remain (gta_game 2/3, silo 2/3). These are loop-exits,
  not failures, but changing the field description may affect how many levers haiku generates
  per call, potentially altering which plans trigger early exit.

**Prerequisite issues:** None. This is a standalone field-description change with no dependencies
on the field-name validator (analysis 39 backlog item) or the `partial_recovery` event taxonomy
fix (ongoing backlog).

---

## Backlog

**Resolved — remove from backlog:**
- "Core tension" template lock in `Lever.review_lever` field description and Section 4 system
  prompt. Both fixed in PR #358. Confirmed 0% in after runs for haiku and llama3.1.

**New — add to backlog:**
- **HIGH: Secondary "None/All three options" template lock.** `identify_potential_levers.py:120`
  — "state the specific gap the **three options** leave unaddressed." Same mechanism as original
  lock. Active in haiku at ~85% (hong_kong_game) and ~50% (silo). Target for next PR.
- **LOW: Stale `LeverCleaned.review` field description.** `identify_potential_levers.py:212`
  still says "names the core tension." No runtime impact; code hygiene. Bundle with next PR.
- **LOW: Wrong model name in `check_option_count` docstring.** `identify_potential_levers.py:143`
  says "Run 82 (llama, gta_game)" — should be "Run 80 (llama3.1, gta_game)". Bundle with any
  future housekeeping pass.

**Carry over from analysis 39 backlog:**
- **MEDIUM: Field-name rejection validator for `options`.** `check_option_count` at lines 130–142
  accepts any 3-item list, including lists containing literal field names (e.g., "review_lever").
  One instance occurred in haiku run 86 (gta_game, lever bb5f1a82). Not addressed in PR #358.
  Risk is low-frequency but the fix is trivial (~6 lines).
- **MEDIUM: `partial_recovery` event conflates early loop-exit with genuine call failure.**
  `runner.py:517–523` fires for both cases. All current haiku partial_recovery events are
  confirmed loop-exits, not failures, but dashboards cannot distinguish them. Implement separate
  `early_exit_sufficient_levers` event type when analysis tooling needs programmatic distinction.
- **LOW: Review length still 2.5–3× above baseline for haiku.** After run 93 haiku silo:
  ~260 chars (~42 words) vs baseline ~90 chars (~17 words). The "one sentence (20–40 words)"
  constraint is partially effective but not bringing haiku to baseline length. Deferred until
  template-lock migration is resolved — fixing structural lock may also reduce average length
  by removing the templated preamble phrase.
- **LOW: `consequences` field description names prohibited pattern ("Controls X vs Y").** Risk
  of prohibition-backfire in small models. Rewrite to describe what the field should contain
  (not what it should avoid). Deferred — no confirmed regression from this yet.
