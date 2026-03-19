# Insight Claude

Analysis of history runs 73–79 (after PR #356) vs. 52–58 (before PR #356, baseline from `analysis/35_identify_potential_levers`).

## Model–Run Mapping

| Run | Model | Era |
|-----|-------|-----|
| 52 | ollama-llama3.1 | before |
| 53 | openrouter-openai-gpt-oss-20b | before |
| 54 | openai-gpt-5-nano | before |
| 55 | openrouter-qwen3-30b-a3b | before |
| 56 | openrouter-openai-gpt-4o-mini | before |
| 57 | openrouter-gemini-2.0-flash-001 | before |
| 58 | anthropic-claude-haiku-4-5-pinned | before |
| 73 | ollama-llama3.1 | after |
| 74 | openrouter-openai-gpt-oss-20b | after |
| 75 | openai-gpt-5-nano | after |
| 76 | openrouter-qwen3-30b-a3b | after |
| 77 | openrouter-openai-gpt-4o-mini | after |
| 78 | openrouter-gemini-2.0-flash-001 | after |
| 79 | anthropic-claude-haiku-4-5-pinned | after |

---

## Negative Things

### N1 — llama3.1 regression: gta_game hard fail (new in after)

Run 73 (llama3.1, after) gta_game fails completely with a `LLMChatError` / 7 Pydantic
`ValidationError`s. Every lever produced in the first LLM call had < 3 options
(6 levers had 1–2 options). Because `len(responses) == 0` at the point of failure,
the code raises immediately (line 322 in `identify_potential_levers.py`) with no output
file generated.

Before (run 52, llama3.1), gta_game succeeded with `partial_recovery`
(calls_succeeded: 2, status: ok). The change in examples between runs (urban-planning
removed; agriculture/medical/insurance added) correlates with this regression.

Evidence:
- `history/2/73_identify_potential_levers/outputs.jsonl` line 2: `"status": "error", "calls_succeeded": null`
- `history/2/73_identify_potential_levers/events.jsonl` line 4: error with 7 `options must have at least 3 items`
- `history/2/52_identify_potential_levers/outputs.jsonl` line 2: `"status": "ok", "calls_succeeded": 2`

### N2 — haiku reviews still exceed the 20–40 word target

The PR added "Keep each `review_lever` under 2 sentences (aim for 20–40 words)" to
section 6. Run 79 (haiku) gta_game reviews average ~350 chars (≈57 words), well above
the 40-word cap. The guidance is soft (no Pydantic validator enforces it), so haiku
ignores it.

Sample from `history/2/79_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`:
> "Three cities promise franchise prestige but create sequential bottlenecks in animation,
> environment art, and multiplayer server provisioning that do not parallelize cleanly.
> The options focus on geographic volume but miss the core question: how much simulation
> fidelity per district is necessary to sustain narrative and player agency, versus how
> much can be procedurally thinned without breaking immersion."
> (337 chars, ≈55 words)

### N3 — haiku consequences exceed 2× baseline length

Run 79 haiku hong_kong_game consequences average ~680 chars, versus the baseline
`002-10-potential_levers.json` average of ~241 chars. Ratio ≈ 2.8×, which is above the
2× warning threshold defined in AGENTS.md. The additional length is substantive (specific
consequences are enumerated) but not proportionally more decision-relevant.

Evidence: `history/2/79_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
first lever consequences: 700 chars, second: 661 chars.

### N4 — Fabricated percentages still present in haiku options

Despite the prohibition in section 5 ("NO fabricated statistics or percentages without
evidence from the project context"), haiku gta_game options contain fabricated numeric
claims:
- "negotiating revenue-sharing that offsets 25 to 30 percent of development costs"
- "publisher equity investment (50%), government research grants tied to procedural AI
  systems and graphics innovation (20%), and strategic hardware partnerships with
  Sony/Microsoft for exclusive content tiers (20%)"
- "a dedicated 50-person live team hired during core development's final 12 months"

Source: `history/2/79_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
levers "Funding Model and Strategic Partnerships" and "Live Service Roadmap and Post-Launch
Content Velocity".

### N5 — Template lock persists in llama3.1 and haiku reviews

**llama3.1** (run 73, hong_kong_game): reviews follow "[Lever Name] lever overlooks..." or
"While [Lever Name] lever... it overlooks / a more balanced approach... is required."
Pattern appears in ~10/17 levers. This is not directly copying the new examples
(agriculture/medical/insurance) but is a self-consistent template.

**haiku** (run 79, gta_game): reviews follow "X promises/offers Y but introduces/creates Z."
Pattern visible across 14+ levers. This mirrors the "but" structure shared by example 1
("stabilizes harvest quality, but the idle-wage burden") and example 3 ("reduces expected
annual loss on paper, but a single regional hurricane season").

OPTIMIZE_INSTRUCTIONS explicitly warns: "Replacing a copyable opener does not eliminate
template lock — weaker models shift to copying subphrases within the new examples."
This is occurring exactly as predicted.

---

## Positive Things

### P1 — haiku gta_game no longer EOF-fails

In iter 37, haiku gta_game failed with a ~40KB EOF error caused by ~550 chars/review ×
21 levers × 3 calls. Run 79 (haiku, after) gta_game succeeds with 3 calls and 21 levers,
reviews averaging ~350 chars. The 36% reduction in review verbosity kept the total payload
below the EOF threshold. This is the primary success of the review length cap.

Evidence: `history/2/79_identify_potential_levers/outputs.jsonl` line 1:
`"20250329_gta_game", "status": "ok", "calls_succeeded": 3`

### P2 — haiku partial_recovery count unchanged

Before (run 58): 2 partial recoveries (silo, parasomnia).
After (run 79): 2 partial recoveries (hong_kong_game, silo).
Net change: 0. Haiku reliability is stable despite the prompt change.

### P3 — OpenAI / Gemini / Qwen models: perfect reliability both eras

Runs 53–57 (before) and 74–78 (after): all 5 plans × 5 models × both eras complete with
status "ok" and calls_succeeded: 3. No hard fails, no partial recoveries. The prompt
change has no measurable effect on these models.

### P4 — No domain collision with test plans

PR removed the game-dev example (iter 36 collision). The new examples are agriculture,
medical (IRB/clinical-site), and insurance (coastal catastrophe risk). None of the five
test plans (silo, gta_game, sovereign_identity, hong_kong_game, parasomnia_research_unit)
overlap with these domains. Good hygiene maintained.

### P5 — haiku hong_kong_game content quality is high

Run 79 haiku hong_kong_game levers show specific, domain-grounded options:
- "Commission a Hong Kong or Asian filmmaker (second or third feature) with strong thriller
  credentials and prior experience working with international crews..."
- "Pair a Western psychological horror specialist... with a Hong Kong-based co-director or
  creative partner embedded throughout pre-production..."

These are genuinely distinct strategic approaches, not labels. Source:
`history/2/79_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

### P6 — B1 partial_recovery events properly scoped

After runs emit `partial_recovery` events only for `identify_potential_levers` step as
intended. Events in runs 73 and 79 show `expected_calls: 3` in partial_recovery, consistent
with the runner now correctly monitoring this specific step rather than emitting spurious
events from other pipeline steps.

---

## Comparison

### Before vs After: Success Rate per Plan per Model

| Plan | llama before | llama after | haiku before | haiku after | Others before | Others after |
|------|-------------|-------------|--------------|-------------|---------------|--------------|
| silo | ok (3) | ok (3) | ok (2) | ok (2) | ok | ok |
| gta_game | ok (2)* | **error** | ok (3) | ok (3) | ok | ok |
| sovereign_identity | ok (3) | ok (3) | ok (3) | ok (3) | ok | ok |
| hong_kong_game | ok (3) | ok (3) | ok (3) | ok (2)* | ok | ok |
| parasomnia | ok (3) | ok (2)* | ok (2)* | ok (3) | ok | ok |

`*` = partial_recovery. `error` = hard fail.

Key change: llama3.1 gta_game went from `ok (partial)` to `error`. One new hard fail.

### Aggregate Success Rates

| Era | Hard Fails | Partials | Full Success | Total Plans |
|-----|-----------|---------|-------------|-------------|
| Before (52–58) | 0 | 3 | 32 | 35 |
| After (73–79) | **1** | 3 | 31 | 35 |

### Partial Recovery Events (expected_calls: 3 in all cases)

| Run | Model | Plan | calls_succeeded |
|-----|-------|------|----------------|
| 52 (before) | llama3.1 | gta_game | 2 |
| 58 (before) | haiku | silo | 2 |
| 58 (before) | haiku | parasomnia | 2 |
| 73 (after) | llama3.1 | parasomnia | 2 |
| 79 (after) | haiku | hong_kong_game | 2 |
| 79 (after) | haiku | silo | 2 |

---

## Quantitative Metrics

### Field Length Comparison (hong_kong_game)

| Field | Baseline avg | llama3.1 run 73 avg | Ratio | haiku run 79 avg | Ratio |
|-------|-------------|---------------------|-------|-----------------|-------|
| Consequences | ~241 chars | ~270 chars | 1.1× | ~680 chars | **2.8×** |
| Review | ~150 chars | ~239 chars | 1.6× | ~340 chars | **2.3×** |
| Options | ~172 chars | ~183 chars | 1.1× | ~310 chars | 1.8× |

Baseline from `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` (N=15 levers).
Run 73 sample N=5 levers. Run 79 sample N=3 levers.

> WARNING: haiku hong_kong_game is above 2× for both consequences and reviews.

### Lever Count per Plan (after runs, selected)

| Run | Model | Plan | Lever count |
|-----|-------|------|------------|
| 73 | llama3.1 | hong_kong_game | 17 |
| 79 | haiku | gta_game | 21 |
| 79 | haiku | hong_kong_game | ~14 (partial, 2 calls) |
| 52 | llama3.1 | gta_game | 15 (before) |

### Template Lock Rate

| Model | Plan | Era | Dominant review pattern | Rate |
|-------|------|-----|------------------------|------|
| llama3.1 | hong_kong_game | after | "[Lever] lever overlooks…" or "a more balanced approach is required" | ~10/17 levers |
| haiku | gta_game | after | "X offers/promises Y but introduces/creates Z" | ~14/21 levers |

### Fabricated Numeric Claims (haiku gta_game, run 79)

4 fabricated percentage or count claims found in options/consequences:
1. "25 to 30 percent of development costs"
2. "publisher equity investment (50%), government research grants (20%), hardware partnerships (20%)"
3. "a dedicated 50-person live team"
4. "a dedicated 50-person live team hired during core development's final 12 months"

Baseline hong_kong_game: fabricated percentages present in legacy gemini outputs (15%, 20%, 25%, 30% patterns) but these were from an older prompt that is now replaced.

### Constraint Violations (options < 3 items, run 73 llama3.1 gta_game)

All 7 levers in the first LLM call had 1–2 options instead of 3. This triggered the
`check_option_count` validator for every lever. The first call had 0 valid responses,
causing immediate hard fail.

### Review Length vs. 20–40 Word Target (haiku gta_game, run 79)

| Lever | Review chars | Word count | Target met? |
|-------|-------------|-----------|------------|
| Geographic Scope | 337 | ≈55 | No |
| NPC Simulation | 353 | ≈58 | No |
| Heist Mechanic | 397 | ≈65 | No |
| Visual Fidelity | 331 | ≈54 | No |
| Funding Model | 359 | ≈59 | No |

Mean: ~355 chars, ≈58 words. Target: 20–40 words (≈100–200 chars). Exceedance: ~1.5× over upper bound.

---

## Evidence Notes

- Hard fail error message: `history/2/73_identify_potential_levers/events.jsonl` line 4 (7 `ValidationError`s, options count 1–2)
- gta_game before output (partial recovery, ok): `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` (15 levers, options were short labels but ≥3 each)
- haiku gta_game after output: `history/2/79_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` (21 levers, high quality options)
- Baseline hong_kong_game: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` (15 levers, legacy gemini output)
- OPTIMIZE_INSTRUCTIONS and system prompt: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` lines 27–86 (OPTIMIZE_INSTRUCTIONS), 207–247 (IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT)
- `check_option_count` validator: line 130–142 in identify_potential_levers.py — raises immediately when `len(v) < 3`
- First-call-fail logic: lines 321–327 — if `len(responses) == 0`, raises immediately with no retry from partial results

---

## PR Impact

### What the PR Was Supposed to Fix

1. **B1 fix**: Scope `partial_recovery` events to `identify_potential_levers` only; remove stale `expected_calls=3` from `_run_levers`.
2. **Medical example**: Replace urban-planning (Section 106) example with medical (IRB/clinical-site sequential overhead) to avoid domain collision with gta_game test plan (iter 36 problem).
3. **Review length cap**: Add "20–40 words" guidance to section 6 to prevent haiku verbosity overflow (iter 37 hard failure from ~550 char reviews × 21 levers × 3 calls ≈ 40KB EOF).

### Before vs After Comparison Table

| Metric | Before (runs 52–58) | After (runs 73–79) | Change |
|--------|--------------------|--------------------|--------|
| Hard fails | 0 / 35 plans | 1 / 35 plans (llama3.1 gta_game) | **−1 plan** |
| Partial recoveries | 3 | 3 | same |
| haiku gta_game success | ✓ (iter 37: ✗ EOF fail) | ✓ | **improved** |
| llama3.1 gta_game | ok (2 calls, partial) | **error (0 calls)** | **regressed** |
| haiku review length (gta_game) | ~550 chars (iter 37) | ~355 chars | **improved** |
| Review length target met (haiku) | n/a | No (58 words vs 40-word target) | partial |
| Fabricated % (haiku options) | present | present | unchanged |
| Template lock (llama3.1) | present | present | unchanged |
| Template lock (haiku) | present | present (different pattern) | unchanged |

### Did the PR Fix the Targeted Issues?

**B1 fix**: Partially confirmed. `partial_recovery` events are emitted for the correct
step. The `expected_calls: 3` value still appears in the events, consistent with the step
normally needing 3 calls. The fix appears behaviorally correct for runs 73–79.

**Medical example**: The domain collision from iter 36 (game-dev example contaminating
gta_game test plan) is eliminated — no game-dev example is present in the current prompt.
However, the new examples (agriculture/medical/insurance) correlate with llama3.1
producing 1–2 options per lever on gta_game (regression). The mechanism is unclear
(example-driven confusion vs. unrelated stochastic variation) but the timing is suspicious.

**Review length cap**: gta_game haiku succeeded in run 79 (3 calls, 21 levers, no EOF).
The cap reduced reviews from ~550 to ~355 chars — enough to clear the 40KB EOF threshold.
However, the cap is not enforced structurally (no Pydantic max_length), so models
exceeding it produce no validation error. The soft guidance works for now but is fragile.

### Regressions Introduced

The critical regression is **llama3.1 gta_game going from status "ok" (partial recovery,
2 calls succeeded) to status "error" (hard fail, first call rejected)**. Before, llama3.1
produced output (albeit lower quality with label-style options). After, it produces nothing.
This is a measurable reliability decrease for this model × plan combination.

### Verdict

**CONDITIONAL**

The review length cap successfully eliminated the haiku EOF failure mode (P1), and the
B1 fix is working correctly (P6). However, the llama3.1 regression on gta_game (N1) is a
new hard fail that was not present before. The PR produces a net reliability decrease of
1 plan across 35. The medical example did not eliminate the llama3.1 gta_game problem —
it transformed it from a degraded partial recovery into a complete failure.

The PR should be kept if the haiku EOF risk is judged to outweigh the llama3.1 regression,
or if llama3.1 reliability is considered low-priority. A follow-up fix for llama3.1 is
required before this can be declared a clean success.

---

## Questions For Later Synthesis

Q1: Is llama3.1 gta_game regression caused by the example change or by stochastic
    variation? Would re-running run 73 produce a different result?

Q2: Why does haiku have 2 partial recoveries in both before (silo, parasomnia) and
    after (hong_kong_game, silo) but on different plans? Is this consistent with
    stochastic partial failures for haiku?

Q3: The options `check_option_count` validator causes an immediate hard fail when the
    first call returns levers with < 3 options. Should there be a single immediate
    retry on first-call validation failure before giving up?

Q4: Should the 20–40 word review guidance be enforced as a Pydantic `max_length`
    constraint? The current runs show haiku ignores the soft guidance at ~58 words avg.
    How short is too short to be useful?

Q5: Template lock in haiku reviews follows an "X but Y" pattern matching the example
    structure. Would replacing one example with a non-contrastive structure (e.g.,
    additive or conditional framing) break the template lock?

---

## Reflect

The PR made a targeted fix for haiku's EOF problem by reducing review verbosity, and that
fix works. But it introduced a new hard failure for llama3.1 on gta_game — a plan that
was previously recovering (with low-quality output) now produces nothing. This is the
classic optimization loop risk: fixing one model's problem while regressing another's.

The OPTIMIZE_INSTRUCTIONS verbosity amplification warning is validated: haiku still
produces reviews at ~1.5× the 40-word target despite explicit guidance. The soft guidance
is insufficient for enforcing structural limits on verbose models. A Pydantic `max_length`
enforcement would be more reliable, at the cost of potential validation failures for models
that already struggle to be concise.

The template lock pattern — llama3.1 using "[Lever] lever overlooks..." and haiku using
"X but Y" — shows that three structurally distinct examples are still not enough to fully
break template lock for these models. OPTIMIZE_INSTRUCTIONS has documented this problem
accurately. The next iteration should focus on making each example use a different
subject–verb–object structure rather than just different domain content.

---

## Potential Code Changes

**C1**: Add `max_length` Pydantic constraint for `review_lever` field (~250 chars /
~40 words) to enforce the length cap structurally rather than as prompt guidance alone.
Evidence: haiku ignores the "20–40 words" text instruction (N2, Q4). Risk: models that
naturally produce longer reviews may fail validation; mitigate by making it a soft
truncation in LeverCleaned rather than a rejection in Lever.

**C2**: Add single-retry logic for first-call validation failure. When `len(responses) == 0`
and the first call fails with a Pydantic options-count error, retry once with explicit
emphasis ("Each lever MUST have exactly 3 options — no more, no fewer") before raising
the LLMChatError. Evidence: run 73 llama3.1 gta_game hard fail was triggered by
`len(v) < 3` validator (N1, Q3). Affects: identify_potential_levers.py lines 321–327.

**C3**: Log which specific validator caused a first-call failure. Currently the error
message names the validator but not the prompt context. Adding the prompt snippet would
help diagnose whether example-driven confusion or model stochasticity caused the failure.

---

## Hypotheses

**H1 (prompt)**: The three current examples share a contrastive "X [achieves] Y, but Z"
sentence structure that models are copying as a template. Replace one example with an
additive or conditional framing to increase structural diversity. Evidence: N5 (haiku
reviews uniformly follow "X but Y"); OPTIMIZE_INSTRUCTIONS template-lock documentation.
Expected effect: haiku review diversity increases; template lock for haiku breaks or shifts.

**H2 (prompt)**: The "Exactly 3 options" guidance exists only in the field description and
section 1. Repeating it prominently at the TOP of the system prompt as a hard constraint
("CRITICAL: Every lever must have exactly 3 options. Fewer than 3 invalidates the entire
batch.") may prevent llama3.1 from producing 1–2 option levers. Evidence: N1, run 73
llama3.1 gta_game produced 1–2 options despite "Exactly 3" appearing in the field
description. Expected effect: reduces first-call validation failures for llama3.1.

**H3 (prompt)**: Fabricated percentages in haiku options persist despite section 5
prohibition. Adding a concrete example of the BAD pattern in section 5 ("e.g., 'reduces
costs by 30%' when no cost data is in context — do not do this") may make the rule more
salient. Evidence: N4 (haiku still uses "25 to 30 percent", "50-person team"). Expected
effect: reduces fabricated numeric claims in haiku and similar instruction-following models.

**H4 (OPTIMIZE_INSTRUCTIONS update)**: The current OPTIMIZE_INSTRUCTIONS does not document
the first-call hard-fail risk from the `check_option_count` validator. Add a note:
"The `options must have at least 3 items` validator causes an immediate hard fail if the
first call produces under-generated options (len(responses)==0 path). Consider single
first-call retry logic before raising." This is a code-level issue but should be tracked
in OPTIMIZE_INSTRUCTIONS for synthesis awareness.

---

## Summary

PR #356 achieves its primary goal: haiku gta_game no longer fails with an EOF error (the
iter 37 hard failure is resolved). The medical example replaced the game-dev example
without causing new domain collisions, and the B1 partial_recovery fix is working
correctly.

However, the PR introduces one new hard fail: llama3.1 on gta_game (run 73) fails
completely where before it produced a low-quality partial output. This regression is
likely caused by the example change altering llama3.1's options-generation behavior on
the gta_game context, but a single re-run cannot confirm causality vs. stochastic
variation.

Secondary findings: haiku reviews still exceed the 20–40 word target by ~45% (soft
guidance is insufficient for verbosity enforcement); haiku consequences for hong_kong_game
are 2.8× longer than baseline (above warning threshold); template lock persists for both
llama3.1 and haiku with different patterns; fabricated percentages remain in haiku options.

**Verdict**: CONDITIONAL. Keep the PR for the haiku EOF fix, but track the llama3.1
regression and plan a follow-up to either add retry logic (C2) or adjust the prompt to
prevent under-generation of options in llama3.1 on gta_game (H2).
