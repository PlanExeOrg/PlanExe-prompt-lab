# Insight Claude

## Overview

This analysis evaluates PR #473 ("Replace negative-priming with positive framing and reduce output
verbosity in identify step"), comparing runs from analysis 70 (after PR) against the best known-good
baseline from analysis 40 (PR #358, registered in `analysis/best.json`).

**Current runs (after PR #473):**
- `4/97` — ollama-llama3.1 (workers=1)
- `4/98` — openrouter-openai-gpt-oss-20b (workers=4)
- `4/99` — openai-gpt-5-nano (workers=4)
- `5/00` — openrouter-qwen3-30b-a3b (workers=4)
- `5/01` — openrouter-openai-gpt-4o-mini (workers=4)
- `5/02` — openrouter-gemini-2.0-flash-001 (workers=4)
- `5/03` — anthropic-claude-haiku-4-5-pinned (workers=4)

**Before runs (PR #358, best baseline):**
- `2/87`–`2/93` (same 7 models, same order)

All runs used `baseline/train` (5 plans) as input. Comparison is valid (same step, same input).

---

## Negative Things

**1. gpt-oss-20b still times out (2/5 plans).**
Run `4/98` (gpt-oss-20b, after PR #473):
- `20250321_silo`: error, 600s timeout
- `20260311_parasomnia_research_unit`: error, 600s timeout
- `20250329_gta_game`: 564s (near-timeout)

Source: `history/4/98_identify_potential_levers/outputs.jsonl`.
Before (run `2/88`, PR #358): 0/5 timeouts, max 209s per plan.
PR #471 (run `4/91`): 5/5 timeouts (catastrophic). PR #473 recovered to 3/5 completions, but
the stated goal of "helps gpt-oss-20b complete within 600s" is not fully achieved.

**2. haiku verbosity increased, not decreased.**
After PR #473, haiku consequences avg is 584 chars vs 515 chars before (PR #358) — a +13%
increase. Consequences are now 2.1× the baseline average (279 chars), up from 1.8×.
Review field also grew: 343 chars vs 321 chars before (+7%).

Source: computed from `history/2/93_*/outputs/` vs `history/5/03_*/outputs/`.
The PR reduced the stated target from "2-4 sentences" to "2-3 sentences" for consequences,
but haiku ignored this constraint. haiku is the model that most exceeds baseline verbosity.

**3. Fabricated numbers increased for gpt-oss-20b and haiku.**

| Model | Before pct% | After pct% | Before $ | After $ | Before time | After time |
|-------|-------------|------------|----------|---------|-------------|------------|
| llama3.1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss-20b | 0 | **4** | 1 | **5** | 1 | **3** |
| haiku | 5 | **9** | 3 | 2 | 9 | **15** |

Source: regex search on `consequences` + `review` fields in all output files.
gpt-oss-20b in run `4/98` now contains specific invented figures: "increase pre-production time by
an estimated 4 weeks", "saving HK$5m in permit costs", "raise P&A by roughly HK$10m, potentially
boosting Hong Kong box office by 15%", "The added legal fees of HK$2m". None of these numbers
appear in the project context. The PR's positive framing change ("Focus on cause-effect
relationships") may be inadvertently encouraging models to invent specific cause-effect metrics.

**4. haiku partial recovery persists (2/5 plans had incomplete LLM call sets).**
Run `5/03` (haiku, after PR #473):
- `20260310_hong_kong_game`: calls_succeeded=1, expected 3 (`partial_recovery` event)
- `20260311_parasomnia_research_unit`: calls_succeeded=2, expected 3

Source: `history/5/03_identify_potential_levers/events.jsonl` and `outputs.jsonl`.
Before (run `2/93`, PR #358) also had 2/5 partial plans. No improvement or regression —
the partial call failures predate this PR.

**5. System prompt / field description length target mismatch.**
The system prompt (section 2) specifies "Target length: 2-4 sentences" for consequences, while
the `Lever.consequences` field description now reads "Target length: 2-3 sentences" (changed by
this PR). The two sources contradict each other — models receive conflicting guidance.

Source: `identify_potential_levers.py:118` (field description) vs `identify_potential_levers.py:232`
(system prompt).

**6. llama3.1 "primary trade-off" template lock slightly worsened.**
After PR #473: 7/87 (8.0%) reviews contain "primary trade-off introduced by this lever" vs
5/82 (6.1%) before. Minor increase. The PR's new example structure ("The primary trade-off…
gap the three options leave unaddressed") in the field description likely reinforced this lock.

---

## Positive Things

**1. gpt-oss-20b catastrophe partially reversed.**
PR #471 caused 5/5 plan timeouts for gpt-oss-20b (run `4/91`). PR #473 recovers to 3/5
completions. Source: `history/4/91_identify_potential_levers/outputs.jsonl` vs
`history/4/98_identify_potential_levers/outputs.jsonl`. For the 3 plans that completed, duration
was acceptable (87s, 265s, 564s).

**2. "Controls X vs. Y. Weakness:" anti-pattern absent (maintained).**
Neither before-batch (runs `2/87-93`) nor after-batch (runs `4/97, 5/00-03`) showed any
"Controls " or "Weakness:" occurrences in output files. Source: pattern search across all
output files. The positive framing change is confirmed as a defensive improvement — preventing
regression if this anti-pattern was to resurface.

**3. Modest field length reduction for most models.**
gpt-oss-20b consequences: 283→240 avg chars (-15%). qwen3-30b consequences: 239→213 avg chars (-11%).
For llama3.1, gpt-5-nano, gpt-4o-mini, gemini: changes within ±5%.

**4. No new constraint violations or structural regressions.**
All models maintain: exactly 3 options per lever, valid JSON schema, no bracket placeholders.
Source: examining option counts in all output files.

**5. Review field quality maintained for most models.**
gpt-oss-20b and gpt-5-nano reviews (after PR #473) show natural cause-effect prose, no
formulaic "the options do not address" lock. haiku reviews use varied sentence structures
despite being verbose.

**6. llama3.1 "Not X could result in Y" prefix eliminated.**
Before (run `2/87`): 8/82 reviews started with "Not X could lead to Y" pattern.
After (run `4/97`): 0/87 reviews with this prefix. Small but measurable improvement.

---

## Comparison

| Metric | Before (2/87-93, PR#358) | After (4/97-5/03, PR#473) | Change |
|--------|--------------------------|---------------------------|--------|
| gpt-oss-20b plans completed | 5/5 (100%) | 3/5 (60%) | -40pp |
| haiku partial recovery plans | 2/5 | 2/5 | unchanged |
| Overall timeout/failure plans | 2/35 | 2/5 (gpt-oss-20b) + 2/5 (haiku partial) | regression |
| Baseline cons ratio (haiku) | 1.8× | 2.1× | regression |
| Baseline cons ratio (gemini) | 1.3× | 1.2× | small improvement |
| Baseline cons ratio (others) | 0.6-1.0× | 0.6-0.9× | no change |
| "Controls / Weakness" patterns | 0 | 0 | unchanged |
| Fabricated % in gpt-oss-20b | 0 | 4 occurrences | regression |
| Fabricated $ in gpt-oss-20b | 1 | 5 occurrences | regression |
| Fabricated time in haiku | 9 | 15 occurrences | regression |

---

## Quantitative Metrics

### Success Rate by Model

| Model | Before timeouts | After timeouts | Before partial | After partial | After max duration |
|-------|-----------------|----------------|----------------|---------------|--------------------|
| llama3.1 | 0/5 | 0/5 | 1/5 | 0/5 | 310s |
| gpt-oss-20b | 0/5 | **2/5** | 0/5 | 0/5 | 565s (ok) |
| gpt-5-nano | 0/5 | 0/5 | 0/5 | 0/5 | 243s |
| qwen3-30b | 0/5 | 0/5 | 0/5 | 0/5 | 210s |
| gpt-4o-mini | 0/5 | 0/5 | 0/5 | 0/5 | 48s |
| gemini-2.0-flash | 0/5 | 0/5 | 0/5 | 0/5 | 41s |
| haiku | 0/5 | 0/5 | 2/5 | 2/5 | 192s |

Sources: `history/4/97..5/03/outputs.jsonl` and `history/2/87..93/outputs.jsonl`.

### Average Field Lengths vs Baseline

Baseline (`baseline/train/` across 5 plans, 75 levers total): consequences=279, options=150, review=152.

| Model | Before cons/opts/rev | After cons/opts/rev | After cons ratio | After opts ratio | After rev ratio |
|-------|---------------------|---------------------|-----------------|-----------------|----------------|
| llama3.1 | 163/100/211 | 161/109/221 | 0.6× | 0.7× | 1.5× |
| gpt-oss-20b | 283/139/170 | 240/129/168 | 0.9× | 0.9× | 1.1× |
| gpt-5-nano | 259/135/199 | 254/139/186 | 0.9× | 0.9× | 1.2× |
| qwen3-30b | 239/87/149 | 213/89/134 | 0.8× | 0.6× | 0.9× |
| gpt-4o-mini | 248/144/159 | 240/144/157 | 0.9× | 1.0× | 1.0× |
| gemini-2.0-flash | 362/187/183 | 345/176/172 | 1.2× | 1.2× | 1.1× |
| haiku | 515/322/321 | **584/306/343** | **2.1×** | 2.0× | 2.3× |

Sources: computed from all `002-10-potential_levers.json` output files for all 5 plans.

haiku is the only model exceeding the 2× warning threshold on consequences after PR #473.

### Lever Count per Plan

All models generate 14-21 levers per plan (consistent with "5-7 per call × 3 calls" logic).
haiku produces the most levers (avg ~23 after PR #473 due to partial recovery skew).

### Template Lock Counts (review field)

| Model | Before "primary trade-off introduced" | After "primary trade-off introduced" | Pct change |
|-------|--------------------------------------|--------------------------------------|------------|
| llama3.1 | 5/82 (6.1%) | 7/87 (8.0%) | +1.9pp |
| gpt-oss-20b | 0/91 | 0/91 | unchanged |
| haiku | 0/93 | 0/114 | unchanged |

### Fabricated Numbers Count (consequences + review fields)

| Model | Before pct% | After pct% | Before $ | After $ | Before time | After time |
|-------|-------------|------------|----------|---------|-------------|------------|
| llama3.1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gpt-oss-20b | 0 | 4 | 1 | 5 | 1 | 3 |
| haiku | 5 | 9 | 3 | 2 | 9 | 15 |

Note: counts are per-lever occurrences (one lever can contain multiple fabricated numbers).
All gpt-oss-20b fabricated figures appear in the hong_kong_game plan (run `4/98`).

---

## Evidence Notes

- `history/4/98_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  lever "Script Adaptation" consequences: "will increase pre-production time by an estimated 4 weeks
  but will reduce on-location VFX needs, keeping the HK$470m budget intact"
- Same file, lever "Audience Engagement": "will raise P&A by roughly HK$10m, potentially boosting
  Hong Kong box office by 15% of the target gross"
- Same file, lever "Budget Allocation": "Shifting 10% of the production budget to digital set
  extensions reduces on-location shooting days by two, saving HK$5m in permit costs"
- `history/5/03_identify_potential_levers/events.jsonl` line 6: `{"event": "partial_recovery",
  "plan_name": "20260310_hong_kong_game", "calls_succeeded": 1, "expected_calls": 3}`
- `history/4/97_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  llama3.1 review examples: "The primary trade-off introduced by this lever is the tension between
  exploiting Hong Kong's cinematic DNA and bringing a Western psychological horror sensibility…"
  (7 of 14 levers use this opener)
- `identify_potential_levers.py:118` field description: "Target length: 2–3 sentences"
- `identify_potential_levers.py:232` system prompt section 2: "Target length: 2–4 sentences"
  (inconsistency)

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (`identify_potential_levers.py:27-93`) warns against:
- Fabricated numbers → gpt-oss-20b and haiku are regressing on this metric after PR #473
- Verbosity amplification → haiku exceeds 2× baseline; the PR description claimed output
  reduction but haiku's consequences grew +13%
- Template-lock migration → llama3.1's "primary trade-off introduced by this lever" pattern
  (7/87 = 8%) qualifies; listed in OPTIMIZE_INSTRUCTIONS lines 73-82 as a known risk

New problem not yet in OPTIMIZE_INSTRUCTIONS worth adding:
- **Cause-effect fabrication trigger**: Positive framing instructions ("Focus on
  cause-effect relationships") combined with the absence of a "no fabricated numbers" reminder
  in the field description (only the system prompt prohibitions section mentions this) appear
  to allow models to invent specific metrics. The `consequences` field description should
  include an explicit reminder: "only cite numbers if the project context provides evidence."
  (This phrase is already in the field description: "only cite numbers if the project context
  provides evidence for them" — but gpt-oss-20b is ignoring it. This may be a training issue
  rather than a prompt gap.)

---

## PR Impact

### What the PR was supposed to fix

1. **Positive framing**: Replace `"Do NOT include 'Controls ... vs.', 'Weakness:'"` with
   `"Focus on cause-effect relationships and factual outcomes"` in the `consequences` field
   description (both `Lever` and `LeverCleaned`).
2. **Reduced output targets**: consequences 2-4→2-3 sentences, options "full sentence"→"one
   sentence", review_lever trimmed to "1-2 sentences".
3. **Primary goal**: Helps gpt-oss-20b complete within 600s (the step makes 3 LLM calls per plan,
   and slow providers take 200-1000s per call). PR #471 caused 5/5 gpt-oss-20b plans to timeout.

### Before vs After Comparison

| Metric | Before (2/87-93) | After (4/97-5/03) | Change |
|--------|-----------------|-------------------|--------|
| gpt-oss-20b: plans completed | 5/5 (0 timeouts) | 3/5 (2 timeouts, 1 near-timeout) | REGRESSION vs baseline |
| gpt-oss-20b: plans completed vs PR#471 | N/A | 3/5 vs 0/5 | IMPROVEMENT vs PR#471 |
| haiku: avg consequences length | 515 chars (1.8×) | 584 chars (2.1×) | REGRESSION |
| "Controls / Weakness" patterns | 0/633 levers | 0/646 levers | MAINTAINED |
| Fabricated numbers (gpt-oss-20b) | 1 dollar, 1 time | 4 pct, 5 dollar, 3 time | REGRESSION |
| Fabricated numbers (haiku) | 5 pct, 3 dollar, 9 time | 9 pct, 2 dollar, 15 time | REGRESSION |
| haiku partial call recovery plans | 2/5 | 2/5 | UNCHANGED |
| System prompt / field description consistency | N/A | inconsistent ("2-4" vs "2-3") | NEW BUG |

### Did the PR fix the targeted issue?

**Positive framing (goal 1)**: NEUTRAL. The "Controls X vs. Y. Weakness:" pattern was already
absent in the best baseline (runs `2/87-93`). Analysis 69's assessment confirms this was
preventative, not corrective. No measurable improvement from this change.

**Output reduction (goal 2)**: PARTIALLY. Most models show modest reductions (0-15%). However
haiku — the most verbose model and the most problematic for content quality — increased
consequences by 13% despite the stricter length target. The reduced targets are not enforced
structurally; haiku ignores them.

**gpt-oss-20b timeout fix (goal 3)**: PARTIALLY. PR #471 catastrophically failed (0/5 plans
completed). PR #473 recovers to 3/5. However, compared to the best baseline (PR #358: 5/5,
max 209s), gpt-oss-20b performance has regressed. The 2 remaining timeouts (silo at 600s,
parasomnia at 600s) and the near-timeout (gta_game at 564s) indicate the fix is insufficient.
The timeouts may be confounded by API latency variability — run `2/88` was on 2026-03-19
and run `4/98` was on 2026-03-31; server load differences cannot be ruled out.

### Regressions introduced?

- haiku verbosity worsened (2.1× consequences vs 1.8× before)
- Fabricated numbers increased for gpt-oss-20b and haiku
- System prompt / field description length target now inconsistent

### Verdict: CONDITIONAL

The PR should be kept because it partially recovers from PR #471's catastrophic gpt-oss-20b
failure (0/5 → 3/5 completions), and reverting would require going back to either PR #471
(catastrophic) or PR #358 (best known state). If the comparison is against PR #471, this is
an improvement. If compared against the best baseline (PR #358), it is a regression on
reliability and content quality.

Follow-up work required:
1. Fix the gpt-oss-20b remaining timeouts (2 plans consistently fail — silo and parasomnia)
2. Add a hard max-length validator on `consequences` to prevent haiku verbosity regression
3. Fix the system prompt / field description length inconsistency (2-4 vs 2-3 sentences)
4. Investigate rising fabricated numbers for gpt-oss-20b (cause unclear — may be unrelated
   to this PR, or the positive framing may be encouraging fabrication)

---

## Questions For Later Synthesis

Q1: Is the gpt-oss-20b timeout (silo + parasomnia) caused by prompt verbosity or by API
latency variability? The plans that timed out in run `4/98` are different from run `4/91`
(which also had gpt-oss-20b timeout all 5 plans in PR #471). Can we isolate the variable?

Q2: Why did haiku's consequences length increase despite the stricter "2-3 sentences" target?
Is haiku ignoring the field description entirely, and would a `max_length` validator help?

Q3: Is the fabricated numbers increase in gpt-oss-20b (4 pct, 5 dollar) caused by the positive
framing change ("Focus on cause-effect relationships"), or is it a stochastic variation?

Q4: The "primary trade-off introduced by this lever" template lock for llama3.1 (8% of reviews)
originates from the field description language ("identify the primary trade-off"). Should this
phrase be reworded in the field description to break the lock?

Q5: haiku's partial recovery (calls_succeeded < 3) for hong_kong_game and parasomnia plans has
persisted across multiple PRs. Is this a schema validation failure (Pydantic rejecting haiku's
output) or a timing issue? Checking `events.jsonl` shows `partial_recovery` events but no
`LLMChatError` entries — this suggests haiku is returning fewer than the required 15 levers
(stopping the adaptive loop early) rather than a hard validation failure.

---

## Reflect

The PR achieves its minimum viable goal: recovering from the PR #471 catastrophe for gpt-oss-20b.
The positive framing change is good practice (consistent with OPTIMIZE_INSTRUCTIONS) even if
it had no measurable effect here. However, the output reduction goal failed for the most
problematic model (haiku), which is the one that actually needs it. The current approach —
adjusting prompt text — is insufficient to control haiku's verbosity; a structural validator
is likely needed.

The fabricated numbers regression for gpt-oss-20b is the most concerning new finding. gpt-oss-20b
was generating essentially clean output before (run `2/88`: 0 pct, 1 dollar), but now generates
specific invented cost figures (HK$2m, HK$5m, HK$10m) and percentages (15%) in the hong_kong_game
plan. This is a content quality regression that the PR may have inadvertently caused.

---

## Potential Code Changes

**C1 (HIGH PRIORITY):** Add a character-count soft cap to the `consequences` field description.
The `Lever.consequences` field currently has only a "Target length: 2-3 sentences" text hint.
Add a `field_validator('consequences', mode='after')` that warns (or truncates) when the field
exceeds ~400 characters. This would prevent haiku from generating 600-800 char consequences
without changing behavior for well-behaved models.
File: `identify_potential_levers.py`, near line 132 (existing `parse_options` validator).

**C2 (MEDIUM):** Fix the length target inconsistency between the `consequences` field description
("Target length: 2–3 sentences", line 119) and the system prompt section 2 ("Target length: 2–4
sentences", line 232). The field description was updated by this PR; the system prompt was not.
Both should read the same value.

**C3 (LOW):** The `review_lever` field description (line 126-130) says "1-2 sentences" but
there is no corresponding `max_length` or character validator. A soft check at 200 chars would
catch extreme verbosity without rejecting reasonable content.

**H1:** Reword the `consequences` field description to remove the phrase "cause-effect
relationships" and replace with "direct effects and trade-offs" to reduce the risk that models
interpret "cause-effect" as requiring invented metrics. Evidence: gpt-oss-20b fabricated
specific cost/time figures increased 4-5× after this PR.

**H2:** Replace the llama3.1 template-lock phrase "primary trade-off introduced by this lever"
in the `review_lever` field description (line 127) with more diverse language. Per
OPTIMIZE_INSTRUCTIONS lines 73-82, the replacement phrase itself became a new template lock.
Suggested alternative: "one sentence stating what decision-maker insight this lever adds and
what the three options collectively leave unresolved."

---

## Summary

PR #473 partially fixes the gpt-oss-20b timeout catastrophe introduced by PR #471 (0/5 → 3/5
plans complete), and its positive framing change is sound as defensive practice. However it
introduces or worsens several problems: gpt-oss-20b remains 2/5 plans timing out (below the
best baseline of 5/5), haiku verbosity increased rather than decreased (now 2.1× baseline
consequences), and fabricated numbers rose for both gpt-oss-20b and haiku. The system prompt
and field description now contain inconsistent length targets. Verdict: **CONDITIONAL** — keep
the PR as it is better than PR #471, but schedule follow-up fixes for the haiku verbosity
regression, gpt-oss-20b remaining timeouts, and fabricated numbers increase before the next
optimization cycle.
