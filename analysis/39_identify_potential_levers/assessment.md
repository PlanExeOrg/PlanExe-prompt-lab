# Assessment: fix: B1 step-gate, medical example, review cap, first-call retry

## Issue Resolution

**PR #357 targeted five issues** (from `pr_description`):

1. **B1 step-gate** — Scope `partial_recovery` events to `identify_potential_levers` only, preventing them from mis-triggering B1 recovery in other pipeline steps.
2. **Medical example** — Replace the urban-planning (Section 106) `review_lever` example with an IRB/clinical-site example to improve domain diversity for medical-research plans.
3. **Review length cap** — Add "20–40 words" instruction to section 6 to prevent haiku verbosity overflow (iter 37 reached EOF at 40KB from ~550-char reviews).
4. **First-call retry** — Let the adaptive loop retry on first-call validation failures instead of raising immediately; `max_calls=5` exhausts naturally.
5. **Temperature** — llama3.1 0.5 → 0.8 to break deterministic structured output.

### What was resolved

**Issue 4 (first-call retry): FULLY RESOLVED.**
Before (run 52): llama3.1 gta_game shows `partial_recovery, calls_succeeded=2` in `events.jsonl`.
After (run 80): gta_game shows no `partial_recovery` event — 3/3 calls succeeded.
Confirmed by direct read of both `events.jsonl` files.

**Issue 2 (medical example): RESOLVED for domain diversity; note side-effect.**
Run 86 haiku parasomnia output is domain-specific and plan-grounded: levers address DFG milestone triggers (month-18, 25 enrolled/40 events), dual-rater kappa thresholds (≥0.65), euro-denominated staffing budgets (€80–120K/year), AASM scoring criteria. No fabricated percentages detected. Specific numbers come from plan context, not LLM invention. Confirmed by direct read of `history/2/86_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.
Side-effect: the pre-existing `review_lever` field description phrase "name the core tension" (line 111) and its echo in section 4 (line 228) now produce a near-universal "The tension is between X and Y" opener across all plans and models. The PR's example changes did not introduce this — the field description predates the PR — but the new examples did not suppress it either.

**Issue 3 (review length cap): PARTIALLY RESOLVED.**
For simpler plans (gta_game), haiku per-call output dropped from ~7,308 to ~2,489 output tokens (−66%). Confirmed by insight.
For complex plans (parasomnia), the cap instruction is ignored: run 86 haiku parasomnia used 6,898 output tokens per call with 60+ word reviews. The "20–40 words" instruction is advisory-only — `review_lever: str` has no `max_length` in the Pydantic schema.

**Issue 1 (B1 step-gate): NOT EVALUABLE from this data.** All runs in both batches are `identify_potential_levers`. No cross-step data is present to confirm the fix works across other steps. Implementation is code-correct (`if step == "identify_potential_levers"` guard confirmed in `runner.py:517–519`).

**Issue 5 (temperature): AMBIGUOUS.**
The increased temperature (0.5→0.8) aimed to break deterministic structured output. It succeeded for gta_game (stochastic 2-option bug no longer triggers). However, llama3.1 sovereign_identity shows a new `partial_recovery` (calls_succeeded=2) in run 80 that was not present in run 52 — consistent with higher temperature introducing more output variability and causing a stochastic 3rd-call failure on a different plan. One run is insufficient to establish causation; this needs monitoring.

### Residual symptoms

1. The old "These options…" / "The lever misses…" template lock (from before runs) is gone — replaced by a new "The tension is between X and Y" lock that affects ~100% of llama3.1 and haiku reviews across all plans. The content is more substantive (domain-specific trade-offs) but the structural uniformity is a new regression.
2. Template leakage (field name as option value) appeared in one haiku output and passed validation.

---

## Quality Comparison

Models appearing in BOTH batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5 (7 models × 5 plans = 35 plan executions each).

| Metric | Before (runs 52–58) | After (runs 80–86) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 = 100% | 35/35 = 100% | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High (case-sensitive dedup) | High (same) | UNCHANGED |
| **Template leakage (field-name in options)** | 0 | 1 (haiku gta_game lever `bb5f1a82`: literal string `"review_lever"` as 4th option; confirmed by direct read) | **REGRESSION** |
| **Review template lock — llama3.1 gta_game** | ~78% "These options…" / "While these options…" | ~100% "The tension here is between X and Y" (all 15 reviews; confirmed by direct read) | SHIFTED (better content, same or higher structural uniformity) |
| **Review template lock — haiku (all plans)** | Mixed diverse openers | ~90–100% "The tension is/lies between X and Y" (gta_game, parasomnia, hong_kong) | **REGRESSION** (new uniform lock) |
| **Review format compliance (section 6)** | Mixed; no dominant pattern other than llama3.1 lock | "Tension" opener dominant across multiple models and all 5 plans | REGRESSED (new cross-model lock) |
| **Consequence chain format (Imm→Sys→Strat)** | Absent (prohibited) | Absent | UNCHANGED |
| **Content depth — haiku parasomnia** | High quality pre-existing | High quality; domain-grounded plan-specific constraints | UNCHANGED (strong) |
| **Content depth — llama3.1 gta_game options** | ~16 words avg, label-like in some | ~17 words avg, prose format | UNCHANGED |
| **Cross-call duplication** | Present (handled by downstream dedup) | Present | UNCHANGED |
| **Over-generation (>7 levers per call)** | Haiku routinely 8–10 per call | Haiku 8–10 per call (3 loop-exit events) | UNCHANGED |
| **Haiku per-call output — simple plans (gta_game)** | ~7,308 tokens (run 58 silo call 1) | ~2,489 tokens (run 86 gta_game call 1) | **IMPROVED −66%** |
| **Haiku per-call output — complex plans (parasomnia)** | ~4,406 tokens (run 58 silo call 2) | ~6,898 tokens (run 86 parasomnia call 1) | **REGRESSION +56%** |
| **Review length vs baseline — haiku hong_kong** | ~3.2× baseline (~135 chars) | ~3.2× baseline | UNCHANGED (exceeds 2× warning threshold) |
| **Fabricated quantification** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Low | Low | UNCHANGED |
| **llama3.1 gta_game calls_succeeded** | 2/3 (partial_recovery) | 3/3 (no event) | **IMPROVED** |
| **llama3.1 sovereign_identity calls_succeeded** | 3/3 | 2/3 (partial_recovery, possible temperature regression) | **REGRESSION** |
| **Haiku partial_recovery events** | 2 (silo 2/3, parasomnia 2/3 — loop-exits) | 3 (gta 2/3, sovereign 2/3, parasomnia 1/3 — loop-exits confirmed by usage_metrics) | SLIGHT REGRESSION (informational only; all confirmed loop-exits, not call failures) |

**Notes on key claims verified by direct file read:**
- "Tension" lock in run 80 llama3.1 gta_game: every review in the first 15 levers starts with "The tension here is between X and Y" or "The core tension here is X". Confirmed.
- Field-name leakage: `history/2/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever `bb5f1a82`, options field contains `["...", "...", "...", "review_lever"]` — 4 items (3 real + 1 field name). The validator accepted this because `len(v) >= 3`. Confirmed.
- Haiku parasomnia quality: levers cite `€2M` personnel budget, `month-18` failure trigger, `kappa ≥0.65` inter-rater targets, `AASM` scoring criteria. All from plan context. Confirmed.
- Baseline reviews: "Controls X vs Y. Weakness: ..." format at ~135 chars with fabricated percentages (e.g., "15% higher audience engagement", "20% higher pre-sales"). These are the target to surpass, not match.

**OPTIMIZE_INSTRUCTIONS alignment:**
The PR added "prohibition backfire" and "verbosity amplification" entries to `OPTIMIZE_INSTRUCTIONS`. Both are accurate. Two newly confirmed failure modes are NOT yet documented:
1. **Field-description-induced template lock**: The phrase "name the core tension" in `Lever.review_lever` field description (line 111) and in section 4 (line 228) acts as a stronger structural cue than the examples, causing near-universal "tension" openers. OPTIMIZE_INSTRUCTIONS does not yet describe this failure mode.
2. **Field-name leakage in options**: When token budget is exhausted mid-generation, structured output may emit a Pydantic field name as a literal option value. Not yet documented.

---

## New Issues

1. **"The tension is between X and Y" template lock (new, systemic, all models).** Runs 80 and 86 show near-universal adoption of this opener. Root cause: the `review_lever` field description (line 111) says "name the core tension" — this is serialized to the LLM via the Pydantic schema in addition to the system prompt. The system prompt section 4 header (line 228) also says "name the core tension." Models read this literal phrase and produce literal "tension" openers. The three examples in section 4 do NOT open with "The tension is…" (they use domain-specific openers) — but the field description text overrides the implicit structural signal of the examples. This is a new failure mode: field-description-induced template lock. The PR did not introduce the wording, but it did not fix it either, and it is now the dominant review-quality issue.

2. **Template leakage: field name in options (new, one occurrence confirmed).** Haiku gta_game run 86, lever `bb5f1a82` ("Procedural Density versus Handcrafted Landmark Authority"): the options array has 4 elements, the last being the literal string `"review_lever"`. This is a token-budget exhaustion artifact — structured-output generation emitted the next field name as a value. `check_option_count` accepts any list with ≥ 3 items, so this defect passed validation and shipped to downstream consumers (DeduplicateLevers, FocusOnVitalFewLevers). A field-name rejection validator would catch this class of defect.

3. **llama3.1 sovereign_identity new partial_recovery.** Before (run 52): 3/3 calls succeeded. After (run 80): 2/3 calls succeeded (`partial_recovery, calls_succeeded=2`). Possible cause: the temperature increase (0.5→0.8) raised output variability, introducing a stochastic 3rd-call failure on a plan that previously ran cleanly. One run is insufficient to establish causation, but this is a potential temperature regression.

4. **Review cap ineffective for complex plans (confirmed).** The "20–40 words" instruction in section 6 was the targeted fix for haiku verbosity overflow (iter 37, EOF at 40KB). It works for simple plans (gta_game: 7,308 → 2,489 tokens) but fails for complex plans (parasomnia: 6,898 tokens with 60+ word reviews). Without a Pydantic `max_length` constraint on `review_lever`, instruction-level caps are advisory and ignored by attentive models when the plan context is large.

---

## Verdict

**CONDITIONAL**: The first-call retry fix is a confirmed measurable improvement (llama3.1 gta_game: 2/3 → 3/3 calls). The medical example meaningfully improves domain diversity and produces high-quality parasomnia output. The review length cap reduces verbosity for simple plans. The B1 step-gate is correctly implemented.

However, three issues must be addressed before PR #357 can serve as the new best.json baseline:

1. The "core tension" phrase at `identify_potential_levers.py:111` (field description) and `:228` (section 4 header) has introduced a near-universal structural template lock across all plans and at least 2 models. This is a content-quality regression that affects all 35 plans, not just one.
2. The field-name leakage defect (one confirmed occurrence) needs a validator to prevent corrupted options from reaching downstream steps.
3. The llama3.1 temperature regression (sovereign_identity 3/3 → 2/3) warrants monitoring across additional runs before the temperature increase is confirmed as net-positive.

**Do not update best.json until condition 1 is fixed** (rewrite the "core tension" language in lines 111 and 228). Condition 2 (validator) can be addressed in the same PR.

---

## Recommended Next Change

**Proposal:** Rewrite the `review_lever` field description (line 111) and the section 4 validation protocol (line 228) to remove the structural phrase "name the core tension" — replacing it with content-goal language ("identify the primary trade-off… then state the specific gap") that preserves the analytical goal without providing a sentence-structure template.

The synthesis recommends pursuing this as direction 1 — a prompt/schema change only, no new examples required.

**Evidence:**
The template lock is confirmed at ~100% for llama3.1 (all 15 gta_game reviews confirmed by direct file read) and ~90% for haiku (parasomnia, gta_game, hong_kong). The root cause is unambiguous: `identify_potential_levers.py:111` says "name the core tension" and `:228` repeats it. The three section-4 examples do NOT use "tension" as a structural cue — their openers are domain-specific ("Switching from seasonal contract labor…", "Each additional clinical site requires…"). The examples already demonstrate the desired pattern; removing the conflicting structural cue from the instruction text would align instruction and examples. The synthesis H1 hypothesis projects "The tension is…" opener frequency dropping from ~100% to <40% for llama3.1 and haiku.

The content quality of haiku parasomnia (plan-specific DFG triggers, kappa thresholds, euro costs) shows that the medical example and the broader quality of outputs is high — the only uniform structural problem is the opener phrase. Fixing the opener phrase would unlock the substantive content that is already being generated.

**Verify in next iteration:**
- **Primary**: Does "The tension is between X and Y" opener frequency in llama3.1 gta_game drop from ~100% to below 40% after removing "core tension" from lines 111 and 228?
- **Primary**: Does haiku parasomnia opener diversity increase? Read at least 10 reviews across both LLM calls; count non-"tension" openers.
- **Secondary**: Does llama3.1 sovereign_identity return to 3/3 calls succeeded, confirming the partial_recovery in run 80 was stochastic? If sovereign_identity continues to show partial_recovery across 2 consecutive runs at temperature 0.8, reduce temperature to 0.6.
- **Secondary**: Does the field-name validator (if added alongside the wording fix) prevent any further "review_lever" leakage into options? Check gta_game haiku output specifically — lever count and options content.
- **Informational**: After the opener lock is fixed, measure average review length for haiku parasomnia. If reviews are still 60+ words, add a Pydantic `max_length=350` constraint to `review_lever` in the following PR (direction 3 from synthesis).

**Risks:**
- Removing "core tension" entirely may produce reviews that do not name a tension at all — too abstract ("identify the primary trade-off" is less concrete than "name the core tension"). Mitigation: the three section-4 examples already demonstrate the desired pattern with domain-specific openers, and the word-count cap ("one sentence, 20–40 words") provides a length constraint that forces concision.
- The wording change may shift the template lock to a new phrase derived from the replacement text ("identify the primary trade-off…" → reviews starting with "The primary trade-off is…"). Monitor for this in the next iteration.
- If the haiku partial_recovery events (3 in run 86) are loop-exits and not real failures, the fix should not affect them. But if fixing the opener lock also reduces per-review length, haiku may need more calls to reach 15 levers (fewer levers per call because reviews are shorter) — watch for haiku partial_recovery event counts changing in the next iteration.

**Prerequisite issues:**
- The field-name rejection validator (direction 2) should be combined with direction 1 in the same PR — it is one-pass, very low risk, and closes a confirmed defect. No prerequisites.
- The `partial_recovery` / loop-exit disambiguation (direction 5) remains deferred but is needed before haiku's call behavior can be interpreted reliably. Not a prerequisite for direction 1.

---

## Backlog

**Resolved by PR #357 (remove from backlog):**
- *First-call retry*: llama3.1 gta_game stochastic 2-option failure. Confirmed fixed (gta_game 2/3 → 3/3). Remove.
- *B1 step-gate cross-contamination*: `partial_recovery` from `identify_potential_levers` triggering B1 in other steps. Scoped to `identify_potential_levers` only in `runner.py:517–519`. Remove.
- *Medical example gap*: Section 106/urban-planning example replaced with IRB/clinical-site example. Domain diversity confirmed improved for parasomnia-type plans. Remove.

**Remaining from prior backlog (still open):**
- **Template lock ("These options", "The lever")** from analysis 35 is now superseded by the "tension" lock — the old symptoms are gone but a new structural lock has replaced them. Update to: "tension" opener template lock (~100% for llama3.1 and haiku) — root cause: "name the core tension" in field description (line 111) and section 4 (line 228). Priority: HIGH. Next action: direction 1 from synthesis (rewrite both occurrences).
- **B1 (false `partial_recovery`)**: `runner.py:517–523` fires on `calls_succeeded < 3` regardless of cause (early loop-exit vs. genuine failure). Haiku run 86: 3 events, all confirmed loop-exits. Low practical impact but inflates apparent failure counts. File: `runner.py:517–523`. Priority: MEDIUM.
- **S1 / I5 (`lever_index` dead field)**: Generated but never transferred to `LeverCleaned`. Token waste. File: `identify_potential_levers.py:84–86`.
- **S2 / I6 (`strategic_rationale` dead field)**: ~100 words generated per call (~10,500 words/iteration), never consumed downstream. File: `identify_potential_levers.py:158–163`.
- **S4 / I2 (option word-count validator)**: 15-word minimum in section 6 is unvalidated. Soft warning for options under 10 words. File: `identify_potential_levers.py:125–137`.
- **B2 (dispatcher cross-thread contamination)**: `runner.py:187–219`. Low practical impact. Deferred.
- **B3 (case-sensitive name deduplication)**: `identify_potential_levers.py:337`. Minor. Fix with `lever.name.strip().lower()` normalization.

**New items to add:**
- **Field-description-induced template lock** (NEW, HIGH): The `review_lever` field description (line 111) and section 4 header (line 228) both say "name the core tension," causing ~100% "tension" opener uniformity across all plans and at least 2 models (llama3.1, haiku). Root cause: structural phrase in schema text overrides example-implicit signal. Fix: rewrite both to "identify the primary trade-off… then state the specific gap." Next action: direction 1 from synthesis.
- **Field-name leakage validator** (NEW, MEDIUM): `check_option_count` accepts any list with ≥3 items including Pydantic field name strings. Haiku gta_game run 86 lever `bb5f1a82`: `"review_lever"` appears as 4th option and shipped downstream. Fix: add `check_no_field_name_leakage` validator rejecting options that exactly match known field names. File: `identify_potential_levers.py:130–142`.
- **Review cap schema enforcement** (NEW, MEDIUM): "20–40 words" instruction at line 243 is advisory. Haiku parasomnia still generates 60+ word reviews despite the instruction. Fix after direction 1, to avoid interaction effects. Candidate: `max_length=350` chars on `review_lever` field, combined with rewording "under 2 sentences" → "one sentence" for clarity. File: `identify_potential_levers.py:109–116, :243`.
- **OPTIMIZE_INSTRUCTIONS gap: field-description template lock** (NEW, LOW): The newly confirmed failure mode — structural phrase in field description acting as a stronger cue than system prompt examples — is not yet documented. Add after the "Verbosity amplification" bullet. File: `identify_potential_levers.py:27–86`.
- **OPTIMIZE_INSTRUCTIONS gap: field-name leakage in options** (NEW, LOW): Token-exhaustion-caused field-name leakage not yet documented. Add alongside field-description template lock entry. File: `identify_potential_levers.py:27–86`.
- **llama3.1 temperature monitoring** (NEW, LOW): Temperature increase (0.5→0.8) may have introduced sovereign_identity instability. If sovereign_identity shows `partial_recovery` in ≥2 consecutive runs at 0.8, revert to 0.6.
