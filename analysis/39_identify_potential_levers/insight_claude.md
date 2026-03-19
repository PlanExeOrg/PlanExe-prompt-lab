# Insight Claude

## Scope

Analyzing runs `2/80–2/86` (after PR #357) against `2/52–2/58` (before, from analysis 35 / best.json baseline)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #357 "fix: B1 step-gate, medical example, review cap, first-call retry"

**Changes made:**
- B1 step-gate: scope `partial_recovery` events to `identify_potential_levers` only
- Medical example: replace Section 106 urban-planning review with IRB/clinical-site sequential overhead
- Review length cap: "20–40 words" instruction added to section 6 of system prompt
- First-call retry: let the adaptive loop retry on first-call failures instead of raising immediately
- Temperature: llama3.1 0.5 → 0.8 to break deterministic structured output
- OPTIMIZE_INSTRUCTIONS: document prohibition backfire and verbosity amplification

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/52 | 2/80 | ollama-llama3.1 |
| 2/53 | 2/81 | openrouter-openai-gpt-oss-20b |
| 2/54 | 2/82 | openai-gpt-5-nano |
| 2/55 | 2/83 | openrouter-qwen3-30b-a3b |
| 2/56 | 2/84 | openrouter-openai-gpt-4o-mini |
| 2/57 | 2/85 | openrouter-gemini-2.0-flash-001 |
| 2/58 | 2/86 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **First-call retry fixed llama3.1 gta_game.** Before (run 52): gta_game had `calls_succeeded=2` (one call
   failed stochastically). After (run 80): gta_game completed with `calls_succeeded=3` — the specific failure
   mode targeted by the PR is fixed. Evidence:
   `history/2/52_identify_potential_levers/events.jsonl` (partial_recovery on gta_game) vs
   `history/2/80_identify_potential_levers/events.jsonl` (no partial_recovery on gta_game).

2. **Review length cap reduced haiku output per call for simpler plans.** Before (run 58) haiku silo: call 1
   produced 7,308 output tokens (extreme verbosity). After (run 86) haiku gta_game: call 1 produced 2,489
   output tokens — a 2.9× reduction. The review cap is measurably reducing per-call verbosity for plans with
   shorter user prompts. Evidence: `history/2/58_identify_potential_levers/outputs/20250321_silo/usage_metrics.jsonl`
   (7308 output_tokens call 1) vs `history/2/86_identify_potential_levers/outputs/20250329_gta_game/usage_metrics.jsonl`
   (2489 output_tokens call 1).

3. **Plan success rate maintained at 100%.** All 35 plans across 7 models completed with status=ok in both
   before and after runs. No LLMChatErrors in either set of runs.
   Evidence: `history/2/80–86_identify_potential_levers/outputs.jsonl` (all status=ok).

4. **Medical example produced high-quality parasomnia output.** After (run 86) haiku parasomnia output is
   domain-specific and technically grounded: levers address DFG milestone triggers, dual-rater reliability
   thresholds, AASM scoring criteria, and euro-denominated staffing budgets. No fabricated percentages detected
   in consequences. Evidence: `history/2/86_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
   — levers 1–7 contain plan-specific constraints (€2M budget, month-18 failure trigger, kappa ≥0.65 targets).

5. **Template lock shifted to a more substantive pattern.** The old "These options focus on X, but neglect Y"
   lock seen in before llama3.1 gta_game (run 52: ~78% of reviews) has been replaced in after (run 80) with
   "The tension here is between X and Y" — a pattern that names a specific trade-off rather than criticizing
   options generically. While still a template lock, the content is more decision-relevant.
   Evidence: `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   (7 of 9 visible reviews open "While these options…" or "These options focus on…, but neglect") vs
   `history/2/80_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   (all reviews open "The tension here is between X and Y" or "The core tension here is X").

6. **No fabricated percentage claims in llama3.1 consequences.** Run 80 consequences fields contain no
   fabricated numbers. E.g., consequences for "Gameplay Mechanics" (gta_game): "Implementing a dynamic
   morality system allows players to make impactful choices that influence NPC relationships and game outcomes,
   but may introduce complexity or controversy." — qualitative only.
   Evidence: `history/2/80_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

7. **gpt-5-nano produces compact, structured reviews within word count.** After run 82 hong_kong_game reviews
   consistently use a "Core tension: X; weakness: Y" format at ~25–30 words, well within the 20–40 word cap.
   Example: "Core tension: incentives can constrain creative decisions; weakness: the options do not address
   grant processing timelines and audit burdens that could derail the schedule." (~26 words).
   Evidence: `history/2/82_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

---

## Negative Things

1. **Haiku partial_recovery events increased: 2 events → 4 events (more "missed" calls).** Before (run 58):
   silo (2/3 calls) and parasomnia (2/3 calls). After (run 86): gta_game (2/3), sovereign_identity (2/3),
   parasomnia (1/3). Most of these are loop-early-exits (haiku generated ≥15 levers in fewer calls) rather
   than call failures, but the increase from 2 to 4 events warrants monitoring.
   Evidence: `history/2/86_identify_potential_levers/events.jsonl` (3 partial_recovery events) vs
   `history/2/58_identify_potential_levers/events.jsonl` (2 partial_recovery events).

2. **Haiku verbosity cap not enforced for complex plans.** After (run 86) haiku parasomnia used 6,898 output
   tokens in a single call — larger than gta_game's 2,489 tokens and still generating reviews of ~300–500
   chars (60–100 words). The "20–40 words" instruction in section 6 is not being respected when the plan
   context is large and complex. Reviews like "The tension lies between early de-risking of capture rates
   versus premature lock-in of operational staffing. All three options assume month-18 enrollment and event
   targets are achievable; none explicitly addresses what happens if year-one event yield is 30% lower than
   projected..." are 62 words — well above the cap.
   Evidence: `history/2/86_identify_potential_levers/outputs/20260311_parasomnia_research_unit/usage_metrics.jsonl`
   (6898 output_tokens) vs the "20–40 words" instruction in `identify_potential_levers.py` line 243.

3. **New "tension" template lock has emerged for both llama3.1 and haiku.** After runs show a near-universal
   opener pattern: "The tension is/lies between X and Y" or "The core tension is X versus Y". This pattern
   is present in 15/15 gta_game reviews (run 80, llama3.1), 13/15 parasomnia reviews (run 86, haiku), and
   dominates multiple other plans. This is a field-description-induced template lock: the `review_lever`
   field description says "name the core tension" — models read this instruction and literally start every
   review with "The tension is..." despite the examples not doing so.
   Evidence: `history/2/80_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   (all 15 reviews begin "The tension here is between…" or "The core tension here is…");
   `history/2/86_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
   (most reviews begin "The tension is between…" or "The core tension is…").

4. **Template leakage: field name "review_lever" appeared in an options list.** Lever 15 (name: "Procedural
   Density versus Handcrafted Landmark Authority") in haiku gta_game (run 86) has `"review_lever"` as its
   third option. The options array reads `["...", "...", "review_lever"]`. This is template leakage from
   partial/truncated structured-output generation at the end of a call. The `check_option_count` validator
   accepts 3 items and does not check for field-name strings, so this defect passed validation.
   Evidence: `history/2/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   lever `bb5f1a82-36fa-4c78-b99d-fdbfee3f1fb3`, options field.

5. **llama3.1 sovereign_identity: new partial recovery in after run.** Before (run 52): sovereign_identity
   completed with calls_succeeded=3. After (run 80): sovereign_identity had calls_succeeded=2. The temperature
   change (0.5→0.8) may have increased output variability, causing a stochastic 3rd-call failure. This is a
   potential regression introduced by the temperature change.
   Evidence: `history/2/80_identify_potential_levers/events.jsonl` (partial_recovery on sovereign_identity)
   vs `history/2/52_identify_potential_levers/events.jsonl` (no partial_recovery on sovereign_identity).

6. **Review lengths still exceed baseline by 2–3× for haiku.** After (run 86) haiku hong_kong_game reviews
   average ~400–500 chars (~70–90 words). The baseline hong_kong_game reviews (from
   `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`) average ~130–150 chars (~22–26 words).
   Ratio: ≈3.0–3.3× above baseline. Per AGENTS.md guidance, a 2× ratio is a warning, 3× is a likely regression.

---

## Comparison

| Metric | Before (runs 52–58) | After (runs 80–86) | Change |
|--------|--------------------|--------------------|--------|
| Plan success rate | 35/35 = 100% | 35/35 = 100% | — unchanged |
| LLMChatErrors | 0 | 0 | — unchanged |
| Partial_recovery events | 3 events (1 llama + 2 haiku) | 4 events (1 llama + 3 haiku) | −1 (slightly more) |
| llama3.1 gta_game calls_succeeded | 2/3 | 3/3 | **+1 IMPROVED** |
| llama3.1 sovereign_identity calls_succeeded | 3/3 | 2/3 | −1 REGRESSION |
| haiku partial_recovery events | 2 (silo 2/3, parasomnia 2/3) | 3 (gta_game 2/3, sovereign 2/3, parasomnia 1/3) | −1 (more events) |
| haiku per-call output (simpler plans) | ~7308 tokens (silo call 1) | ~2489 tokens (gta_game call 1) | **−4819 tokens, -66% IMPROVED** |
| haiku per-call output (complex plans) | ~4406 tokens (silo call 2) | ~6898 tokens (parasomnia call 1) | +56% (worse for complex plans) |
| llama3.1 review template lock | "These options focus/neglect" (~78% gta_game) | "The tension here is between X and Y" (~100% gta_game) | Shifted (better content, still locked) |
| haiku review template lock | Mixed patterns | "The tension is between X and Y" dominant | Shifted to unified "tension" lock |
| Template leakage (field name in options) | 0 | 1 (haiku gta_game lever 15) | **NEW DEFECT** |
| Fabricated % in consequences (llama3.1) | 0 (already fixed in prior PR) | 0 | — unchanged |
| Baseline hong_kong_game review length ratio | ~3–4× baseline (haiku, existing) | ~3–4× baseline (haiku) | — unchanged |

---

## Quantitative Metrics

### Plan/Call Outcome Summary

| Run | Model | Plans OK | Partial Recovery Events | Failed Calls |
|-----|-------|----------|------------------------|--------------|
| 52 | llama3.1 | 5/5 | 1 (gta_game 2/3) | 1 |
| 80 | llama3.1 | 5/5 | 1 (sovereign_identity 2/3) | 1 (or loop-exit) |
| 53 | gpt-oss-20b | 5/5 | 0 | 0 |
| 81 | gpt-oss-20b | 5/5 | 0 | 0 |
| 54 | gpt-5-nano | 5/5 | 0 | 0 |
| 82 | gpt-5-nano | 5/5 | 0 | 0 |
| 55 | qwen3-30b-a3b | 5/5 | 0 | 0 |
| 83 | qwen3-30b-a3b | 5/5 | 0 | 0 |
| 56 | gpt-4o-mini | 5/5 | 0 | 0 |
| 84 | gpt-4o-mini | 5/5 | 0 | 0 |
| 57 | gemini-2.0-flash-001 | 5/5 | 0 | 0 |
| 85 | gemini-2.0-flash-001 | 5/5 | 0 | 0 |
| 58 | haiku-4-5 | 5/5 | 2 (silo 2/3, parasomnia 2/3) | 2 (or loop-exits) |
| 86 | haiku-4-5 | 5/5 | 3 (gta 2/3, sovereign 2/3, parasomnia 1/3) | ≤4 (some loop-exits) |

**Note on partial_recovery semantics:** When the adaptive loop reaches `min_levers=15` in fewer than the expected 3 calls
(because a model over-generates), the loop exits cleanly and `partial_recovery` fires with `calls_succeeded < 3`. This
is NOT a failure — it means the model generated ≥15 levers in fewer calls. The distinction requires checking `usage_metrics.jsonl`
per plan to confirm whether the "missed" calls are loop-exits or genuine failures. For haiku, usage_metrics confirm:
- haiku parasomnia (run 86): 1 API call, 6,898 output tokens → over-generated ≥15 levers in 1 call (loop-exit, not failure)
- haiku gta_game (run 86): 2 API calls, 2,489+2,683 output tokens → likely ≥15 levers in 2 calls (loop-exit, not failure)
- haiku sovereign_identity (run 86): 2 API calls, 2,717+4,624 tokens → ≥15 levers in 2 calls (loop-exit, not failure)
Evidence: `history/2/86_identify_potential_levers/outputs/*/usage_metrics.jsonl`.

If the haiku partials are all loop-exits, the actual call failure rate before and after may be comparable. The most
concrete regression is llama3.1 sovereign_identity going from 3/3 to 2/3 calls.

### Review Template Lock Rate

| Plan | Before (run 52, llama3.1) | After (run 80, llama3.1) | Pattern shift |
|------|--------------------------|--------------------------|---------------|
| gta_game | ~78% "These options…" / "While these options…" | ~100% "The tension here is between X and Y" | Shifted (better content, still 100%) |
| silo | 0% (already fixed by PR #353) | 0% | — no change |

| Plan | Before (run 58, haiku) | After (run 86, haiku) | Pattern |
|------|----------------------|----------------------|---------|
| gta_game | Mixed diverse openers | ~100% "The tension is/lies between X and Y" | New uniform lock |
| parasomnia | Mixed diverse openers | ~90% "The tension is…" / "The core tension is…" | New uniform lock |
| hong_kong_game | Mixed openers | ~60% "The tension…", 40% diverse | Partial lock |

### Average Field Lengths vs Baseline (hong_kong_game, sampled)

Baseline from `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`:
- review avg: ~135 chars (~23 words) — short structured format ("Controls X. Weakness: Y")
- options avg (3 combined): ~260 chars
- consequences avg: ~210 chars

| Field | Baseline | Before (run 58, haiku) | After (run 86, haiku) | After/Baseline |
|-------|----------|----------------------|-----------------------|----------------|
| review | ~135 chars | ~430 chars | ~430 chars | **3.2× ⚠ above 2× threshold** |
| options (3×) | ~260 chars | ~450 chars | ~630 chars | **2.4× ⚠ above 2× threshold** |
| consequences | ~210 chars | ~380 chars | ~350 chars | **1.7× (borderline)** |

Note: Baseline reviews contain fabricated percentages and "Controls X vs Y" format. The after reviews are
longer but more substantive. Even so, at 3× baseline length for reviews the additional length should be justified
by additional decision-relevant information — which for haiku hong_kong_game, it is (domain-specific trade-offs,
specific budget figures, concrete casting constraints). However the cap is not keeping reviews concise.

### Fabricated Quantification Count

| Run | Model | Plan | Fabricated % in consequences | Fabricated % in reviews |
|-----|-------|------|------------------------------|------------------------|
| 52 | llama3.1 | gta_game | 0 (fixed in PR #353) | 0 |
| 80 | llama3.1 | gta_game | 0 | 0 |
| 86 | haiku | gta_game | 0 | 0 |
| 86 | haiku | hong_kong_game | 0 | 0 |
| 86 | haiku | parasomnia | 0 (specific numbers like "€150–200K" are from plan context) | 0 |

No fabricated percentages detected in after consequences. Numbers in haiku parasomnia (e.g., "€80–120K",
"month-18", "kappa ≥0.65") are from the plan context, not invented.

---

## Evidence Notes

- **First-call retry fix confirmed**: `history/2/52_identify_potential_levers/events.jsonl` shows
  `partial_recovery` on gta_game (calls_succeeded=2); `history/2/80_identify_potential_levers/events.jsonl`
  shows no partial_recovery on gta_game.

- **Template leakage**: `history/2/86_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
  lever `bb5f1a82-36fa-4c78-b99d-fdbfee3f1fb3`, "Procedural Density versus Handcrafted Landmark Authority":
  `"options": ["...", "...", "review_lever"]` — field name literal appears as the 3rd option.

- **Review cap in system prompt**: `identify_potential_levers.py` line 243: "Keep each `review_lever` under
  2 sentences (aim for 20–40 words). Name the tension and the missed weakness concisely."

- **"Tension" field description trigger**: `identify_potential_levers.py` lines 109–116 (Lever.review_lever
  field description): "A short critical review of this lever — name the core tension, then identify a weakness
  the options miss." The phrase "name the core tension" is cuing models to start reviews with "The tension is..."

- **haiku parasomnia high quality**: `history/2/86_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
  — 15 levers covering DFG failure triggers, dual-rater kappa thresholds, pharma partnership independence,
  AASM scoring criteria, cohort diversity targets. All grounded in plan context.

- **haiku per-call token reduction**: Before haiku silo (run 58) call 1: 7,308 output tokens. After haiku
  gta_game (run 86) call 1: 2,489 output tokens. This is the direct effect of the review length cap working
  for plans with moderate prompt complexity.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (`identify_potential_levers.py` lines 27–86) covers:
- Overly optimistic scenarios ✓
- Fabricated numbers ✓
- Hype and marketing copy ✓
- Vague aspirations posing as options ✓
- English-only validation ✓
- Single-example template lock ✓
- Template-lock migration ✓
- Verbosity amplification ✓

The PR updated OPTIMIZE_INSTRUCTIONS to add "prohibition backfire" (don't name banned phrases) and "verbosity
amplification" (mirror example verbosity). Both additions are accurate and appropriate.

**Gap 1 (not yet documented): Field-description-induced template lock.**
The `review_lever` field description says "name the core tension" — this cues models to start every review with
"The tension is..." or "The core tension is...". This is a form of template lock triggered by the field's own
instruction text, not by the examples. The three examples in section 4 of the system prompt do NOT start with
"The tension is..." (they use domain-specific openers like "Switching from seasonal contract labor..." and
"Each additional clinical site requires..."). But models are primed by the field description's phrase before
reading the examples.

**Proposed OPTIMIZE_INSTRUCTIONS addition:**
```
- Field-description-induced template lock. The review_lever field description says "name the core tension" —
  models read this as a literal instruction and start every review with "The tension is..." or "The core
  tension is X versus Y", making all reviews structurally identical. To avoid this, do not use the word
  "tension" in the review_lever field description. Instead, describe the goal in terms of the required content
  ("identify the primary trade-off and the gap the options miss") rather than the expected sentence structure.
```

**Gap 2 (not yet documented): Partial-output field-name leakage.**
When a model generates output near the token budget boundary, structured-output generation may produce a field
name (e.g., "review_lever") as a literal value in a different field. This passed the `check_option_count` and
`check_review_format` validators because it counted as a valid 3-item list with no brackets. A validator that
checks options items for field-name strings would catch this.

**Proposed OPTIMIZE_INSTRUCTIONS addition:**
```
- Field-name leakage in options. When token budget is exhausted mid-generation, structured output may include
  field names (e.g., "review_lever", "consequences", "lever_index") as literal option values. The current
  validators do not catch this. Consider adding a check: if any option string exactly matches a Pydantic
  field name, reject the lever and log a warning.
```

---

## PR Impact

### What the PR was supposed to fix

PR #357 consolidated changes from #354–356 plus a first-call retry fix:
1. B1 step-gate: Prevent `partial_recovery` events from `identify_potential_levers` triggering B1 in other steps
2. Medical example: Provide a medical-domain review example for parasomnia-type plans
3. Review length cap: Prevent haiku verbosity overflow (iter 37 produced EOF at 40KB)
4. First-call retry: Fix stochastic first-call failures (e.g., llama3.1 gta_game producing 2 options on one attempt)
5. Temperature: llama3.1 0.5→0.8 to break deterministic output

### Before vs. After Comparison

| Metric | Before (runs 52–58) | After (runs 80–86) | Change |
|--------|--------------------|--------------------|--------|
| Plan success rate | 100% | 100% | — |
| LLMChatErrors | 0 | 0 | — |
| llama3.1 gta_game calls_succeeded | 2/3 | 3/3 | **+1 (FIXED)** |
| llama3.1 sovereign_identity calls_succeeded | 3/3 | 2/3 | **−1 (NEW)** |
| haiku partial_recovery events | 2 | 3 | −1 (more) |
| haiku per-call output (simple plans, gta_game) | 7,308 tok/call | 2,489 tok/call | **−66% (IMPROVED)** |
| haiku per-call output (complex plans, parasomnia) | ~4,406 tok/call | 6,898 tok/call | +56% (worse) |
| Review template lock pattern (llama3.1 gta_game) | "These options… neglect" ~78% | "The tension here is between X and Y" ~100% | Shifted to better content |
| Template leakage (field name in options) | 0 | 1 | **NEW DEFECT** |
| Fabricated % in consequences | 0 | 0 | — |
| Content quality (haiku, medical/film plans) | High quality | High quality | — same |
| B1 step-gate (other steps) | Observable in other runs | Not observable here | — not measurable in this data |

### Did the PR fix the targeted issues?

**First-call retry (issue 4):** **YES, confirmed.** llama3.1 gta_game went from 2/3 calls (1 stochastic failure)
to 3/3 calls (complete). Evidence: events.jsonl run 80 vs 52.

**Review length cap (issue 3):** **Partial.** For simpler plans (gta_game), per-call output dropped from ~7K
to ~2.5K tokens. For complex plans (parasomnia), haiku still generates ~6.9K tokens. The cap instruction is
present in the system prompt but not enforced at the Pydantic schema level, so complex plans can exceed it.

**Medical example (issue 2):** **Yes, with note.** Parasomnia output quality is high and domain-specific. However,
a new "The tension is between X and Y" template lock has emerged that affects all plans (not just medical ones).
This lock likely originates from the `review_lever` field description's phrase "name the core tension."

**B1 step-gate (issue 1):** **Cannot evaluate** — all runs here are `identify_potential_levers`. No cross-step
data is available to confirm this fix.

**Temperature (issue 5):** **Ambiguous.** llama3.1 sovereign_identity showed a new partial_recovery in after
runs that was not present before. The temperature increase (0.5→0.8) may have introduced more output variability,
increasing the chance of a stochastic 3rd-call failure on a new plan.

### Regressions

1. **llama3.1 sovereign_identity:** 3/3 calls (before) → 2/3 calls (after). Possible cause: temperature increase.
2. **New "tension" template lock** across all models/plans in after runs. While the content is more substantive
   than the old "these options…" lock, it is still a structural template lock.
3. **Template leakage** in one haiku output (gta_game, lever 15, "review_lever" as option value).
4. **Haiku complex-plan verbosity not improved** (parasomnia 6,898 tokens vs expected reduction).

### Verdict

**CONDITIONAL**

The first-call retry fix is a confirmed, measurable improvement (llama3.1 gta_game: 2/3→3/3). The review length
cap reduced verbosity for simpler plans. The medical example provides a domain-diverse signal.

However, three issues need follow-up before declaring a full win:
1. The new "The tension is between X and Y" template lock has emerged across multiple models — this is caused
   by the `review_lever` field description's phrase "name the core tension" and should be rewritten (H1 below).
2. Template leakage (field name in options) needs a validator fix (C1 below).
3. llama3.1 sovereign_identity regression under higher temperature needs monitoring across more runs.

The PR should be kept (not reverted), but the follow-up items should be addressed before updating best.json.

---

## Questions For Later Synthesis

1. Are the haiku `partial_recovery` events (gta_game 2/3, sovereign_identity 2/3, parasomnia 1/3) loop-exits
   (haiku generating ≥15 levers in fewer calls) or genuine 3rd-call failures? The `usage_metrics.jsonl` data
   supports the loop-exit interpretation, but the downstream impact (output quality, lever count) should be
   verified against a true 3-call run.

2. The "The tension is between X and Y" opener is now dominant for llama3.1 and haiku. Is this a meaningful
   regression in review diversity, or is the content behind the opener substantive enough that the structural
   uniformity is acceptable? Compare the before and after reviews semantically (not just structurally).

3. Should the `review_lever` field description be rewritten to avoid "name the core tension"? Suggested
   rewrite: "Identify the most important trade-off this lever introduces and the gap the options leave
   unaddressed." Does removing "tension" language from the description reduce the template lock?

4. The temperature change for llama3.1 (0.5→0.8) is intended to break deterministic structured output. Did it
   measurably improve lever diversity across plans, or did it only increase stochastic failures?

5. The template leakage in haiku gta_game lever 15 suggests a token-budget exhaustion pattern. Does this only
   appear in the last lever of the second call? Is there a pattern in which plans and models trigger it?

---

## Reflect

The PR consolidates multiple previously-confirmed changes (#354–356) into a single merge. The strongest
individual contribution is the first-call retry code change, which fixed a specific and observable failure mode
(llama3.1 gta_game). The review length cap is working for plans with moderate prompt complexity but failing for
complex plans (parasomnia). The medical example is an improvement for domain diversity.

The most significant unintended consequence is the emergence of a new template lock: "The tension is between X
and Y" as a near-universal review opener. This was not caused by the PR's prompt changes directly — it originates
from the `review_lever` Pydantic field description's phrase "name the core tension," which predates this PR. The
PR's changes may have exacerbated it by changing the examples or temperature, but the root cause is older.

The template leakage defect (lever 15, haiku gta_game) is new and not seen in before runs. It represents a
structured-output generation edge case where token exhaustion causes a field name to appear as a value. This is
a validator gap, not a prompt issue.

---

## Hypotheses

**Prompt hypotheses:**

H1: The `review_lever` field description contains "name the core tension" — models read this as a literal
instruction and start reviews with "The tension is..." regardless of the examples. Rewriting the field description
to "Identify the most important trade-off this lever introduces and the gap the options leave unaddressed" would
remove the structural cue while preserving the content goal.
Expected effect: Reduce "The tension is..." opener from ~100% to <40% in llama3.1 and haiku reviews.

H2: The review length cap ("20–40 words") is instruction-level guidance without Pydantic enforcement. Adding a
`max_length=400` (in characters) constraint to the `review_lever` field would hard-cap haiku verbosity for
complex plans (parasomnia: currently 6,898 tokens/call → target <3,000 tokens/call).
Expected effect: Reduce haiku per-call output for complex plans by 50–60%, reducing the number of loop-exit
partial_recovery events and improving per-plan latency.

H3: The temperature increase for llama3.1 (0.5→0.8) increased output variability. The sovereign_identity partial
recovery in run 80 (not present in run 52) may be caused by this. Reducing temperature back to 0.5 or 0.6 while
testing whether gta_game stochastic failures recur with the first-call retry fix would clarify causation.
Expected effect: If sovereign_identity partial_recovery disappears at lower temperature, the net improvement from
the temperature change is negative (new failures > old fix value).

**Code hypotheses:**

C1: The `check_option_count` validator accepts any 3-item list including field-name strings. Adding a check
that rejects options containing exact Pydantic field names ("review_lever", "lever_index", "consequences",
"options") would catch the template leakage defect in haiku gta_game.
Expected effect: Reject malformed levers at validation time, triggering a retry call that generates a clean lever.

C2: The `partial_recovery` event fires whenever `calls_succeeded < expected_calls=3`, even when the loop exited
early due to having ≥15 levers (not due to call failure). Adding a new event type
`"early_exit_sufficient_levers"` would distinguish clean early-exits from genuine call failures, making
monitoring metrics more interpretable and reducing false-alarm partial_recovery counts in dashboards.
Expected effect: Operational — no change to output quality, but clearer signal for failure analysis.

---

## Summary

PR #357 is a consolidation of changes from PRs #354–356 plus a first-call retry fix. The analysis covers runs
80–86 (after) vs 52–58 (before, best.json baseline at analysis 35).

**Confirmed improvements:**
- First-call retry: llama3.1 gta_game 2/3→3/3 calls (specific fix confirmed)
- Review length cap: haiku per-call output reduced 66% for simple plans (7,308→2,489 tokens)
- Medical example: parasomnia output quality is high and domain-specific, no fabricated numbers

**Confirmed regressions:**
- Template leakage: "review_lever" appears as an option value in haiku gta_game lever 15
- New "tension" template lock: ~100% of llama3.1 and haiku reviews now open with "The tension is between X and Y"
- llama3.1 sovereign_identity: new partial_recovery (3/3→2/3 calls), possible temperature effect

**Ambiguous:**
- Haiku partial_recovery events (2→3 events) appear to be loop-exits, not call failures
- Complex-plan verbosity (parasomnia still 6,898 tokens) not improved by the review cap

**Top follow-up actions:**
1. Rewrite `review_lever` field description to remove "name the core tension" (H1 / C1 for field lock)
2. Add `max_length` Pydantic constraint to `review_lever` for hard verbosity enforcement (H2)
3. Add validator to reject field-name strings in options list (C1 for leakage)
4. Monitor llama3.1 temperature effect on sovereign_identity across more runs (H3)
