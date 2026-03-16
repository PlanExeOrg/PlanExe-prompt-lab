# Assessment: fix: replace two-bullet review_lever prompt with single flowing example

## Issue Resolution

**What the PR was supposed to fix:** PR #316 replaced the `review_lever` field description's
"First sentence… / Second sentence…" two-bullet format with a single flowing example:
> "This lever governs the tension between centralization and local autonomy, but the options
> overlook transition costs."

The motivation was that llama3.1 interpreted the two-bullet format as two *alternative*
formats rather than one required format, causing call-1 schema validation failures that
triggered partial recoveries.

**Is the issue resolved?**

Yes, with caveats.

The primary targeted symptom — "Weakness:" text leaking into the `consequences` field — is
fully eliminated in runs 60–66. Run 59 (old prompt, llama3.1) showed "Weakness:" contamination
in 8/12 hong_kong_game consequence fields (67%). All runs 60–66 show clean consequences with
zero contamination.
Evidence: `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
(lever "Location Sourcing": consequences include "Weakness: The plan does not account for…")
vs. `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`
(consequences clean).

Call reliability for llama3.1 improved: run 60 had 2 partial_recovery events (silo and
parasomnia, calls_succeeded=2); runs 61–66 each show 15/15 plans with calls_succeeded=3.
Overall: 103/105 = 98.1%.

**Residual symptoms:**

Two code changes that should have been part of the PR were missed:
- **B1**: `Lever.review_lever` Pydantic field description at `identify_potential_levers.py:92–100`
  still contains the old "Two sentences. First sentence… Weakness:" format. llama_index sends
  this as part of the JSON schema on every structured LLM call, directly contradicting the
  new single-sentence example in the external prompt file. This schema contradiction is the
  root-level code cause of the run 60 partial recoveries and the verbatim-copy failure.
- **B2**: Hardcoded `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` at `identify_potential_levers.py:216–218`
  also retains the old format. Standalone test runs and the `__main__` block now silently
  diverge from production behaviour.

---

## Quality Comparison

Only **ollama-llama3.1** appears in both batches (run 59 = before; runs 60–66 = after).
All other models (qwen3, gpt-oss-20b, gpt-5-nano, gpt-4o-mini, gemini, haiku) appeared only
in analysis 21 runs 53–58 and have no corresponding runs in analysis 22; they are excluded
from this table. Baseline references use
`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`.

| Metric | Before (run 59, llama3.1 + old) | After (runs 60–66, llama3.1 + new) | Verdict |
|--------|--------------------------------|--------------------------------------|---------|
| **Success rate** (calls_succeeded=3) | Not logged (runs 53–59 lacked the field) | 98.1% (103/105) | IMPROVED |
| **"Weakness:" in consequences** | 67% (8/12 hong_kong levers) | 0% (all runs 60–66) | IMPROVED |
| **Bracket placeholder leakage** | None detected | None detected | UNCHANGED |
| **Option count violations** (≠ 3 options) | None detected | None detected | UNCHANGED |
| **Lever name uniqueness** | Near-dups present (domain-generic names) | Near-dups present ("Partnership Model", "Partnership Structure", "Partnership Ecosystem" in run 60 gta_game) | UNCHANGED |
| **Template leakage — review field** | ~100% "X vs Y. Weakness: Z" boilerplate | ~95% "This lever governs/manages tension between X and Y, but…" | UNCHANGED (different template, same rigidity) |
| **Verbatim prompt-example copy** | 0 | 1 (run 60 gta_game lever "Location Strategy", exact match to prompt section 4) | REGRESSED |
| **Review format compliance** | Old two-part "Controls X vs Y / Weakness:" pattern | New single flowing sentence | IMPROVED (structurally) |
| **Consequence chain format** (Immediate → Systemic → Strategic) | Not used | Not used | UNCHANGED |
| **Content depth — review length** | ~100 chars avg (hong_kong_game) | ~165 chars avg (hong_kong_game) | IMPROVED |
| **Content depth — option length** | ~80 chars avg (hong_kong_game) | ~100 chars avg (hong_kong_game) | IMPROVED |
| **Label-only options** (<30 chars, no verb) | ~3 per run | ~5 (run 60 call-1 gta_game); ~2 avg runs 61–66 | SLIGHTLY REGRESSED (run 60); neutral overall |
| **Cross-call duplication** | Present (domain-generic names across calls) | Present | UNCHANGED |
| **Over-generation** (>7 levers per call) | Not applicable under old cap | Runs 60–66: 18–20 levers per plan (expected; DeduplicateLeversTask handles extras) | INFORMATIONAL |
| **Field length vs baseline** (consequences) | ~1.7× baseline (~200 chars vs ~240 baseline) | ~1.1× baseline (~255 chars run 60, ~240 baseline) | IMPROVED (closer to baseline) |
| **Fabricated quantification** (% claims, dollar figures) | 0 for llama3.1 | 0 for llama3.1 | UNCHANGED |
| **Marketing-copy language** | Minimal | Minimal | UNCHANGED |
| **`strategic_rationale` null rate** | Not logged in run 59 | 100% null (all run 60 call-1 responses) | NEW VISIBILITY (pre-existing issue) |

**OPTIMIZE_INSTRUCTIONS alignment check:**
The PR moves toward "realistic, feasible, actionable plans" by improving structural correctness
and consequence cleanliness. The new review format is more substantive than the clipped old
format. No new violations of the known-problems list are introduced.

However, the "single-example template lock" observed in runs 60–66 (95%+ reviews follow an
identical prefix) is a direct instance of a pattern not yet in OPTIMIZE_INSTRUCTIONS. The known
problems list documents "fragile English-only validation" but not "single-example template
lock." This should be added (see Backlog).

---

## New Issues

**N-new-1. Template lock migrated, not cured.**
The old "X vs Y. Weakness: Z" pattern is gone. The new "This lever governs the tension
between X and Y, but the options overlook Z" pattern is equally rigid — 90–100% of all
reviews across runs 60–66 use it. The root cause (llama3.1 pattern-matches on the one
provided example) is untreated. A different example with different syntax would produce a
different-but-equally-formulaic output.

**N-new-2. Verbatim prompt-example copy (new failure mode).**
Run 60 gta_game lever "Location Strategy" has `review` = exact text from prompt section 4
("This lever governs the tension between centralization and local autonomy, but the options
overlook transition costs."). The old two-bullet format did not produce this failure mode.
The new single unambiguous example made it easy for the model to copy it directly.
Evidence: `history/1/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

**N-new-3. Pydantic schema contradiction (B1 — latent before, now confirmed).**
The Pydantic `Lever.review_lever` field description was never updated by PR #316. It still
says "Two sentences… Weakness:" while the external prompt says single sentence. This means
every structured LLM call sends conflicting instructions. The conflict was latent before run
60; PR #316 made it observable by creating an explicit mismatch between the two instruction
sources.

**N-new-4. `strategic_rationale: null` now visible for llama3.1.**
The `calls_succeeded` and partial_recovery logging added alongside PR #316 makes it visible
that llama3.1 returns `strategic_rationale: null` for every call-1 response. This was
pre-existing but previously invisible.

---

## Verdict

**CONDITIONAL**: The PR is directionally correct and worth keeping — it eliminates "Weakness:"
contamination from consequence fields, simplifies the review format in a way llama3.1 can
produce without call-1 failures, and measurably improves call reliability (98.1% success in
runs 61–66 vs. unlogged in run 59). However, the PR is incomplete: the Pydantic field
description (B1) and hardcoded constant (B2) were not updated, leaving a schema contradiction
in every production call. The template lock issue (N-new-1) is a content-quality regression
affecting all 35 plans across all 7 runs and is higher priority than the structural fix that
recovered run 60 partial recoveries. The conditions for full acceptance are: (1) fix B1+B2,
and (2) pursue Direction 3 (varied review examples) to break template lock.

---

## Recommended Next Change

**Proposal:** Fix `Lever.review_lever` Pydantic field description (B1) and
`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` hardcoded constant (B2) in a single commit to
bring both instruction sources into alignment with the PR #316 external prompt file change.
This closes the schema contradiction that causes run 60 partial recoveries and the verbatim-
copy failure mode.

**Evidence:** Code review B1 (confirmed at `identify_potential_levers.py:92–100`): the field
description sent in the JSON schema still instructs the model to produce "Two sentences" with
a "Weakness:" clause, directly contradicting the new system prompt example. Code review B2
(confirmed at `identify_potential_levers.py:216–218`): the hardcoded default retains the old
prompt_5 text. Synthesis cross-references both findings and traces them to run 60 partial
recoveries (N5 in insight). The fix is 5 lines for B1 and one paragraph rewrite for B2.

**Verify:**
- Run the next iteration with the B1+B2 fix applied. Check: (a) run 1 (equivalent of run 60)
  no longer shows partial_recovery events for silo or parasomnia; (b) the `review_lever` field
  in run 1 gta_game no longer contains a verbatim copy of the example string.
- Check that template leakage rate ("This lever governs the tension between…" prefix) does
  NOT improve solely from B1+B2 — template lock requires Direction 3 (varied examples).
  If the rate stays at 90–100% after B1+B2, that confirms template lock is the next issue.
- Verify `strategic_rationale: null` rate is unchanged (this is a pre-existing llama3.1
  behaviour, not introduced by B1+B2).
- Check that label-only options in call-1 gta_game (N3) remain at the same frequency —
  B1+B2 should not affect this either way.

**Risks:**
- B1 change aligns the field description with the new single-sentence format. If the
  Pydantic validator still enforces `min_length=1` (it does), this is safe. The risk is
  that closing the contradiction exposes a different latent issue — e.g., the model now
  consistently follows a format that other validators are not calibrated for.
- B2 change only affects standalone/test calls; production runs use the external prompt
  file. Risk is negligible, but post-change the `__main__` test block output will change;
  any golden-file tests based on the old format would need updating.
- Neither B1 nor B2 addresses template lock. After fixing both, the 95% "governs tension
  between X and Y" prefix will persist. The next iteration should plan for Direction 3
  (2–3 varied examples) regardless, otherwise the content-quality improvement will remain
  blocked.

**Prerequisite issues:** None. B1 and B2 are self-contained code edits. They should be done
before Direction 3 (varied examples), because the field description change and example changes
must be consistent — drafting new examples into an unchanged field description would recreate
the same contradiction.

---

## Backlog

**Resolved (can be removed):**
- "Weakness: contamination in llama3.1 consequences" — fully eliminated in runs 60–66.
  The structural fix works and is stable across all 7 post-PR runs.

**New issues to add:**
- **B1 (High)**: `Lever.review_lever` Pydantic field description at `identify_potential_levers.py:92–100`
  still uses old "Two sentences / Weakness:" format — contradicts external prompt, confuses
  model on every structured call. Fix: rewrite to match prompt_6 single-sentence format.
- **B2 (Medium)**: `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant at `identify_potential_levers.py:216–218`
  not updated; production vs. test divergence. Fix: rewrite section 4 to match prompt_6.
- **N-new-1 (Medium)**: Template lock — 90–100% of llama3.1 reviews follow "This lever
  governs the tension between X and Y, but the options overlook Z." Needs Direction 3
  (2–3 structurally varied examples). Do after B1+B2 are fixed.
- **N-new-2 (Low)**: Verbatim prompt-example copy in run 60 gta_game. Add a validator (I2)
  that rejects `review_lever` values that match known example strings. Pair with H2 (explicit
  prohibition in system prompt section 5).
- **I5 (Low)**: Add "single-example template lock" as a sixth known problem to
  `OPTIMIZE_INSTRUCTIONS` at `identify_potential_levers.py:27–68`. Document that small
  models (llama3.1 family) reproduce a single format example universally; provide ≥2
  structurally varied examples or add a do-not-copy prohibition.

**Continuing backlog (unchanged from analysis 21):**
- Call-1 anti-fabrication reminder (haiku, gpt-oss-20b budget-anchor fabrication) — still
  unaddressed; no llama3.1 runs affected so not observable in analysis 22 data.
- Label-style option validator (I1/Direction 4) — ~2–5 label-only options per run persist.
- `set_usage_metrics_path()` race condition in `runner.py:107` (B3) — latent for single-worker
  llama3.1; activates with multi-worker models.
- `strategic_rationale: null` for llama3.1 — either require or remove the field (S5).
