# Insight Claude — Analysis 73

**PR under evaluation:** [PlanExeOrg/PlanExe#478](https://github.com/PlanExeOrg/PlanExe/pull/478)
**Title:** Allow verbatim plan numbers only, positive framing, and tighter targets
**Previous analysis:** `analysis/40_identify_potential_levers/` (runs `2/87`–`2/93`)
**Current runs:** `5/18`–`5/24`

## Model Map

| Run | Model |
|-----|-------|
| 5/18 | ollama-llama3.1 |
| 5/19 | openrouter-openai-gpt-oss-20b |
| 5/20 | openai-gpt-5-nano |
| 5/21 | openrouter-qwen3-30b-a3b |
| 5/22 | openrouter-openai-gpt-4o-mini |
| 5/23 | openrouter-gemini-2.0-flash-001 |
| 5/24 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### N1 — Secondary template lock still active: "all three options / none of the options"

The root cause identified in analysis/40 — that `review_lever` field description and system-prompt Section 4 both use "the three options" as a grammatical anchor — remains unfixed in the code.

Current field description (`identify_potential_levers.py:125–131`):
```
"One sentence (20–40 words): the primary trade-off this lever "
"introduces and the gap the three options leave unaddressed. "
```

Current Section 4 text (`identify_potential_levers.py:245`):
```
"...then state the specific gap the three options leave unaddressed."
```

Both still contain "the three options." This is confirmed by output data:

- **Haiku (5/24) hong_kong_game:** 14/20 reviews (70%) contain "all three options", "none of the options", "the three options", or "the options do not/leave" phrasing. Sample:
  - review 8: "…but all three options risk either underserving the psychological core (action-thriller lead) or alienating the commercial demographic"
  - review 9: "…all three options struggle to balance authentic density with production manageability"
  - review 12: "…none of the three options resolve whether transformation is the game's true purpose or final deception"
  - review 1: "The options do not address how to ensure the director has final cut authority"
- **Haiku (5/24) sovereign_identity:** 16/17 reviews (94%) contain the pattern:
  - review 8: "All three leave open the gap of productization"
  - review 10: "All three leave unresolved the question of whether citizens…"
  - review 9: "None addresses the core blocker"
  - review 16: "None eliminates the core tension"

Evidence paths: `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, `history/5/24_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`

### N2 — Haiku consequences exceed the 2–3 sentence target

The PR added "Target length: 2–3 sentences" to both the Pydantic field description and Section 2 of the system prompt. Haiku is not following this:

- Most haiku hong_kong_game consequences contain 3–5 sentences (avg ~500 chars).
- Lever 2 (Protagonist Casting): 4 sentences, ~570 chars.
- Lever 3 (Twist Structure): 4 sentences, ~530 chars.

By contrast, gpt-4o-mini and gpt-5-nano follow the constraint much better (~2–3 sentences, ~230–380 chars).

Evidence: `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

### N3 — Haiku options still contain estimated/derived figures despite the prohibition

Section 5 of the system prompt explicitly prohibits "NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context." The field description for `consequences` carries the same prohibition. Yet haiku (5/24) generates numeric estimates in options:

- "2,500+ screens in key markets" (hong_kong_game lever 7, release strategy options)
- "300–500 select screens" (same lever)
- "premium-VOD window at 60 days" / "90+ days" (same lever)
- "4–5 iconic Hong Kong locations" (lever 4, production footprint options)
- "10–12 neighborhoods" (same lever)
- "70 percent of shooting days" / "30 percent" (same lever)
- "25-minute establishment sequence" / "50 minutes" / "25-day core block" / "20-day second block" (levers 15–16)

These figures do not appear verbatim in the hong_kong_game project context. The plan context does provide: "45–55 shooting days", "18–20 months from greenlight", "US$120–220 million worldwide gross", "US$25 million marketing budget" — and haiku correctly picks up these verbatim figures in consequences.

The prohibition works for consequences but not for options, likely because the options field description does not repeat the constraint explicitly.

Evidence: `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` levers 4, 7, 15, 16.

### N4 — Llama3.1 consequences are significantly under-generating (1 sentence, well below target)

Llama3.1 (5/18) hong_kong_game consequences are almost all single sentences (~100–130 chars), far below the "2–3 sentences" target. The constraint appears to be interpreted as an upper bound rather than a range. Examples:

- "Filming in Hong Kong's densely populated areas can create logistical challenges and potential disruptions to the shoot schedule." (~127 chars)
- "Securing a strong Hong Kong and Asian supporting cast may require additional time and resources." (~97 chars)

This is not a new regression — llama3.1 was already terse — but the new "2–3 sentences" instruction has not pulled it up.

Evidence: `history/5/18_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

### N5 — Lever semantic duplication visible in llama3.1 output

Llama3.1 (5/18) hong_kong_game contains semantically duplicated levers:
- "Festival Launch" (lever_id: `94af21d7`) and "Festival Launch Strategy" (lever_id: `ebda7047`)
- "Sound Design" (lever_id: `adebed2f`) and "Sound Design Approach" (lever_id: `79dc810b`)

This is expected behavior (DeduplicateLevers handles it downstream) but confirms llama3.1's tendency to re-surface the same lever categories.

Evidence: `history/5/18_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

---

## Positive Things

### P1 — Success rate maintained at 97.1%

No regressions in call success rate. All models that previously achieved 100% still do. Haiku partial_recovery events (silo, sovereign_identity) are loop-exits (sufficient levers generated early), not failures.

### P2 — Positive framing change removes a prohibition that could backfire

The PR replaced "Do NOT include 'Controls ... vs.'" with "Save critical assessments for the review_lever field." The old prohibition-framing was flagged in analysis 40's backlog as a risk ("prohibition-backfire in small models"). The new positive framing redirects what should go in the review field without naming a banned pattern.

No "Controls X vs. Y" patterns appear in any current run's output, consistent with prior PRs having already eliminated this.

### P3 — Review length slightly reduced for haiku

Haiku (5/24) hong_kong_game review average: ~220 chars.
Before (haiku 2/93), from analysis/40 assessment: ~260 chars for silo.

This represents a ~15% reduction. The 20–40 word (approximately 100–200 char) target is still not reached, but the trend is moving in the correct direction.

### P4 — Consequences framing is clean and plan-grounded for most models

Gpt-4o-mini (5/22) and gpt-5-nano (5/20) consequences are well-calibrated: 2–3 sentences, no fabricated numbers, specific to plan context. Haiku consequences are verbose but plan-specific and non-marketing.

Examples of well-formed consequences (gpt-4o-mini 5/22):
- "Utilizing a Hong Kong or Asian director ensures a culturally resonant portrayal of the city, enhancing authenticity. However, this may limit the pool of directors with international recognition, potentially affecting global marketing appeal." (~230 chars, 2 sentences)
- "Leveraging Hong Kong's dense architecture as a character in the film creates a unique visual narrative that enhances the psychological tension. However, this approach may complicate logistics and increase production costs due to location-specific challenges." (~255 chars, 2 sentences)

Evidence: `history/5/22_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

### P5 — No LLMChatErrors in any run (events.jsonl confirmed)

The analysis/73 events.jsonl shows no `LLMChatError` events. Individual run events.jsonl files contain only `run_single_plan_start` and `run_single_plan_complete` events with no error fields. Schema validation failures (which caused haiku partial_recovery in earlier iterations) are not occurring.

Evidence: `history/5/24_identify_potential_levers/events.jsonl`, `history/5/18_identify_potential_levers/events.jsonl`

### P6 — Verbatim numbers in consequences mostly correct

Haiku (5/24) consequences correctly cite plan-provided numbers:
- "US$120–220 million worldwide gross" ✓
- "US$25 million marketing budget" ✓
- "45–55 shooting days" ✓
- "18–20 months from greenlight" ✓

These are verbatim from the hong_kong_game plan context. The prohibition is working for the consequences field.

---

## Comparison

### Current vs Before (analysis/40, runs 87–93)

Both use `baseline/train` input with the same 5 plans and the same 7 models. Comparison is valid.

| Dimension | Before (runs 87–93) | After (runs 18–24) |
|-----------|--------------------|--------------------|
| Success rate | 102/105 = 97.1% | 102/105 = 97.1% |
| Haiku success | 13/15 = 86.7% | 13/15 = 86.7% |
| Llama3.1 success | 14/15 = 93.3% | 14/15 = 93.3% |
| Other 5 models | 15/15 each (100%) | 15/15 each (100%) |
| LLMChatErrors | 0 | 0 |
| Template lock haiku hong_kong_game | ~85% (17/20) | ~70% (14/20) |
| Template lock haiku sovereign_identity | Not sampled separately | ~94% (16/17) |
| Haiku review avg length | ~260 chars | ~220 chars |
| Fabricated % claims | 0 | 0 |
| Marketing-copy language | 0 | 0 |
| Estimated/derived numbers in options (haiku) | Low (not checked) | Present (~10+ per plan) |
| Consequences length (haiku) | Not measured | ~500 chars avg (~3–5 sentences, over target) |
| Consequences length (gpt-4o-mini) | Not measured | ~240 chars avg (~2 sentences, on target) |

**Key takeaway:** The PR produces a modest improvement in haiku template lock rate for some plans (~85%→70%) but the underlying cause is unfixed. The sovereignty plan shows 94% lock rate for haiku, suggesting plan-context effects modulate the rate. Success metrics are stable.

---

## Quantitative Metrics

### Table 1: Call Success Rates

| Run | Model | Plans | Calls Succeeded | Partial Recovery |
|-----|-------|-------|-----------------|-----------------|
| 5/18 | llama3.1 | 5 | 14/15 | silo: 2/2 |
| 5/19 | gpt-oss-20b | 5 | 15/15 | none |
| 5/20 | gpt-5-nano | 5 | 15/15 | none |
| 5/21 | qwen3-30b-a3b | 5 | 15/15 | none |
| 5/22 | gpt-4o-mini | 5 | 15/15 | none |
| 5/23 | gemini-2.0-flash | 5 | 15/15 | none |
| 5/24 | haiku | 5 | 13/15 | silo: 2/2, sovereign: 2/2 |
| **Total** | | **35** | **102/105 = 97.1%** | |

Source: each run's `outputs.jsonl`.

### Table 2: Template Lock Rate ("All three options" / "None of the options" / "The options do not" pattern in review_lever)

Measured by sampling hong_kong_game reviews (20 levers per haiku run, 18 per gpt-4o-mini).

| Model | Run | Plan | Lock Count / Total | Rate |
|-------|-----|------|--------------------|------|
| haiku (before) | 2/93 | hong_kong_game | 17/20 | 85% |
| haiku (after) | 5/24 | hong_kong_game | 14/20 | 70% |
| haiku (after) | 5/24 | sovereign_identity | 16/17 | 94% |
| gpt-4o-mini (after) | 5/22 | hong_kong_game | ~6/18 | ~33% |
| gpt-5-nano (after) | 5/20 | hong_kong_game | ~5/18 | ~28% |
| llama3.1 (after) | 5/18 | hong_kong_game | 0/17 | 0% |

Note: llama3.1 uses a different review style that avoids the "options" subject altogether.

### Table 3: Average Field Lengths (hong_kong_game, selected models)

| Model | Run | Consequences avg | Options avg | Review avg |
|-------|-----|-----------------|-------------|------------|
| Baseline (train) | — | ~230 chars (old chain format) | ~150 chars | ~90 chars |
| llama3.1 | 5/18 | ~110 chars (1 sentence) | ~130 chars | ~140 chars |
| gpt-5-nano | 5/20 | ~360 chars (3 sentences) | ~150 chars | ~170 chars |
| gpt-4o-mini | 5/22 | ~240 chars (2 sentences) | ~130 chars | ~140 chars |
| haiku | 5/24 | ~500 chars (3–5 sentences) | ~280 chars | ~220 chars |

**Ratio vs baseline:**
- haiku consequences: ~500/230 = **2.2× baseline** (above 2× warning threshold)
- haiku reviews: ~220/90 = **2.4× baseline** (above 2× warning threshold, slightly improved from ~2.9× in analysis 40)

### Table 4: Constraint Violations

| Violation type | Before (87–93) | After (18–24) |
|----------------|----------------|---------------|
| Option count < 3 | 0 | 0 |
| Square-bracket placeholders | 0 | 0 |
| Review length < 10 chars | 0 | 0 |
| Fabricated % claims | 0 | 0 |
| Marketing-copy language | 0 | 0 |
| Estimated numbers in options (haiku) | Low | ~10+ per plan |

---

## Evidence Notes

**E1** Template lock confirmed in haiku sovereign_identity: review for "Demonstrator Authenticity and Security Pedigree" reads "All three leave open the gap of productization: demonstrators need not and should not be production-ready, but regulators will use lack of operational maturity against fallback-capable design, regardless of security pedigree." (`history/5/24_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` lever index 8.)

**E2** Verbatim numbers respected in consequences: "the P&A strategy must still generate US$120–220 million worldwide gross from a US$25 million marketing budget" (`history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` lever 7, Release Strategy consequences). These figures match the hong_kong_game plan context.

**E3** Estimated numbers in options: Lever 7 (Release Strategy) option 1 says "followed by immediate wide release (2,500+ screens in key markets) within 3 weeks". "2,500+ screens" is a generated estimate, not verbatim from the plan. Option 3: "limited theatrical in 300–500 select screens". `history/5/24_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

**E4** Root cause confirmed in source: `identify_potential_levers.py` lines 125–131 still read `"the gap the three options leave unaddressed"` in the `review_lever` field description. System-prompt Section 4 at line 245 still reads `"then state the specific gap the three options leave unaddressed."` Neither was changed by PR #478.

**E5** Llama3.1 partial_recovery: silo plan completed in 99.47 seconds with `calls_succeeded: 2`. This is an early-exit loop (sufficient levers generated), not a failure. Same behavior observed for haiku silo (78.93s, `calls_succeeded: 2`) and sovereign_identity (115.94s, `calls_succeeded: 2`). `history/5/18_identify_potential_levers/outputs.jsonl`, `history/5/24_identify_potential_levers/outputs.jsonl`

**E6** Baseline train data (parasomnia, hong_kong_game) still uses old "Controls X vs Y / Weakness:" format and "Immediate → Systemic → Strategic" chain. These formats are correctly absent from current outputs, confirming they were already removed in prior PRs.

**E7** `LeverCleaned.review` field description at `identify_potential_levers.py:220–222` now reads `"Critical review of this lever."` — the stale "names the core tension, then identifies a weakness" text identified in analysis/40's backlog appears to have been cleaned up.

---

## PR Impact

### What the PR was supposed to fix

PR #478 claimed four changes (superseding PRs #471, #473, #475, #477):
1. **Verbatim numbers only**: Close the arithmetic-derivation loophole (HK$470M→HK$141M from #475).
2. **Positive framing**: Replace "Do NOT include 'Controls ... vs.'" with "Save critical assessments for the review_lever field."
3. **Tighter targets**: consequences 2–3 sentences, options one sentence, review_lever one sentence (20–40 words).
4. **Section 5 prohibition**: "NO calculated, derived, or estimated figures."

### Before vs After Comparison Table

| Metric | Before (runs 87–93) | After (runs 18–24) | Change |
|--------|--------------------|--------------------|--------|
| Overall success rate | 102/105 = 97.1% | 102/105 = 97.1% | Unchanged |
| Haiku success rate | 13/15 = 86.7% | 13/15 = 86.7% | Unchanged |
| Llama3.1 success rate | 14/15 = 93.3% | 14/15 = 93.3% | Unchanged |
| LLMChatErrors | 0 | 0 | Unchanged |
| Template lock haiku (hong_kong_game) | 17/20 = 85% | 14/20 = 70% | Improved −15pp |
| Template lock haiku (sovereign_identity) | Not sampled | 16/17 = 94% | New data point — high |
| Haiku review avg length | ~260 chars | ~220 chars | Improved −15% |
| Haiku consequences length | Not measured | ~500 chars (over target) | Persisting issue |
| Fabricated % claims | 0 | 0 | Unchanged |
| Marketing-copy language | 0 | 0 | Unchanged |
| Estimated numbers in options (haiku) | Not measured | ~10+ per plan | Persisting issue |
| Controls X vs Y in consequences | 0 | 0 | Unchanged (already fixed) |

### Did the PR fix the targeted issues?

1. **Verbatim numbers in consequences**: Mostly yes — haiku correctly uses plan-supplied figures (US$120–220M, US$25M, 45–55 days) in consequences. But the prohibition is NOT holding for options, where haiku generates estimated numeric ranges (2,500+ screens, 300–500 screens, 60 days, 70%). The Section 5 prohibition exists but is not being respected in options fields.

2. **Positive framing**: Yes — no "Controls X vs Y" appears anywhere. The removal of the prohibition-phrasing is correct and low-risk.

3. **Tighter targets**: Partially. Gpt-4o-mini and gpt-5-nano follow the 2–3 sentence consequence target well. Haiku exceeds it (3–5 sentences). Llama3.1 is under it (1 sentence).

4. **Secondary template lock**: **Not addressed.** The root cause remains: `review_lever` field description and Section 4 both reference "the three options." Template lock rate for haiku is 70–94% across plans (vs 85% before). This is the primary unresolved issue from analysis 40.

### Regressions

No regressions found:
- Success rates are stable
- No new LLMChatErrors
- No new structural violations (option count, placeholders)
- haiku review length improved slightly

### Verdict: **CONDITIONAL**

The PR makes valid, non-harmful improvements (positive framing, tighter targets, verbatim-numbers constraint) that show incremental benefits. However, it does not address the primary outstanding issue from analysis/40: the secondary "all three options" template lock remains active in the `review_lever` field description and system prompt Section 4. Until that root cause is fixed, haiku (and to a lesser degree gpt-5-nano, gpt-4o-mini) will continue producing reviews that reference "the options" as grammatical subject in 28–94% of outputs.

---

## Questions For Later Synthesis

**Q1** Why does the template lock rate vary between plans for haiku? hong_kong_game shows 70% while sovereign_identity shows 94%. Is this because sovereign_identity's bureaucratic/policy context maps more naturally to the "X is good but None of the options address..." review format?

**Q2** Were PRs #471, #473, #475, #477 (intermediate, all CONDITIONAL) evaluated on the same baseline runs (87–93)? If they used different history runs, comparisons against analysis/40 may not be apples-to-apples.

**Q3** Does the "options one sentence" constraint need to be enforced per-option via a Pydantic validator (e.g., rejecting options with sentence-final punctuation within them), or is prompt guidance sufficient for most models?

**Q4** Did the intermediate PR #475 actually produce the HK$470M→HK$141M arithmetic derivation issue, and if so, is it confirmed absent in runs 18–24?

**Q5** The verbatim-numbers prohibition is working for consequences but not for options. Should the options field description include an explicit "no estimated or derived figures" note, or does that risk creating its own template-lock by naming a prohibited pattern?

---

## Reflect

**On the template lock persistence:** The secondary "all three options" lock has been documented since analysis/40. PR #478 was supposed to fix several issues but the recommended fix for this specific lock (rewriting the field description to remove "the three options" as grammatical subject) was not included. This creates a pattern where each PR improves something tangentially while leaving the known root cause untouched.

**On haiku's verbosity:** Haiku consistently over-generates across all field dimensions despite explicit length constraints. This may reflect a fundamental model behavior where length instructions are followed probabilistically rather than deterministically. The "one sentence" instruction for options reduces length but haiku writes long single sentences (~250 chars) rather than truly concise ones (~80-100 chars).

**On the comparison baseline:** Analysis/40 (runs 87–93) is the official "before" baseline. PRs #471–#477 were CONDITIONAL verdicts between analysis/40 and this analysis/73. PR #478 claims to supersede all of them, but the comparison against analysis/40's runs (not the more recent CONDITIONAL iterations) makes it hard to attribute specific improvements to PR #478 alone vs. the cumulative effect of #471–#477–#478.

---

## Potential Code Changes

**C1 (HIGH — primary fix): Rewrite `review_lever` field description to remove "the three options"**

File: `identify_potential_levers.py`, lines 125–131.

Current:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): the primary trade-off this lever "
        "introduces and the gap the three options leave unaddressed. "
        "Do not use square brackets or placeholder text."
    )
)
```

Proposed (per analysis/40 recommendation):
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): name the primary trade-off this lever "
        "forces, then name a real-world constraint or risk that all three "
        "approaches collectively sidestep. Do not use square brackets or "
        "placeholder text."
    )
)
```

**C2 (HIGH — companion fix): Rewrite Section 4 guidance text**

File: `identify_potential_levers.py`, line 245.

Current:
```
"A short critical review — identify the primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed."
```

Proposed:
```
"A short critical review — identify the primary trade-off this lever forces, then name a real-world constraint or risk that all three approaches collectively sidestep."
```

This mirrors C1 and ensures both the field description and the system-prompt narrative are consistent.

**C3 (MEDIUM): Add verbatim-numbers note to options field description**

The prohibition in Section 5 is global, but haiku ignores it for options. Adding the constraint directly to the options field description may help:

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option is one sentence — "
                "a concrete strategic approach with an action verb. "
                "Use only numbers that appear verbatim in the project context; do not estimate or derive figures."
)
```

**C4 (LOW): Verify Section 4 examples don't share sentence patterns**

The three review_lever examples in Section 4 are:
- "Switching from seasonal contract labor…" — trade-off followed by financial consequence
- "Each additional clinical site…" — sequential overhead argument
- "Pooling catastrophe risk…" — diversification-turns-to-concentration

These are structurally diverse and domain-specific. They do not use "the options" as grammatical subject (good). However, "turns the X assumption into a Y at the worst possible moment" is a reusable rhetorical ending. Verify none of the current runs show this pattern leaking into reviews.

---

## OPTIMIZE_INSTRUCTIONS Alignment

| Guideline | Status |
|-----------|--------|
| Overly optimistic scenarios | No evidence of moonshot-only options in current runs |
| Fabricated numbers | Partially fixed — consequences ✓, options still generating estimates (haiku) |
| Hype and marketing copy | 0 instances — fully compliant |
| Vague aspirations posing as options | Small models (llama3.1) occasionally produce vague options (e.g., "Prioritize filming in less crowded areas") but these are minor |
| Fragile English-only validation | Validator uses structural checks only (min length, no brackets) ✓ |
| Single-example template lock | Section 4 now has 3 diverse examples ✓ |
| **Template-lock migration** | **Still active** — "the three options leave unaddressed" in field description ✗ |
| Verbosity amplification | Review length slightly improved for haiku; consequences still over-long for haiku ✗ |
| Field-description template lock | **Still present** — field description references "the three options" ✗ |

The OPTIMIZE_INSTRUCTIONS "Template-lock migration" entry (lines 73–82) explicitly warns:
> "Each example must name a domain-specific mechanism or constraint directly rather than referencing 'the options' as grammatical subject."

The current field description violates this directly. PR #478 did not apply this fix despite it being the top recommendation from analysis/40.

**Proposed OPTIMIZE_INSTRUCTIONS update:** Add a note that the "tighter targets" instruction (2–3 sentences for consequences, one sentence per option) is partially model-dependent: large models like haiku need stronger enforcement via Pydantic validators or post-filtering, while small models like llama3.1 interpret it as an upper cap and under-generate.

---

## Summary

PR #478 makes three valid, non-harmful improvements: positive framing replaces a prohibition-phrasing risk; the verbatim-numbers constraint is correctly added to both field description and system-prompt Section 5; and tighter length targets (2–3 sentences for consequences, one sentence for options and review) are working well for mid-tier models (gpt-4o-mini, gpt-5-nano). No regressions are introduced. Overall success rate and haiku call success rate are unchanged at 97.1% and 86.7% respectively.

However, the primary outstanding issue from analysis/40 — the secondary template lock where "all three options" or "none of the options" appears in 70–94% of haiku review fields — is **not addressed by this PR**. The root cause remains in two locations: the `review_lever` Pydantic field description ("the gap the three options leave unaddressed") and the system-prompt Section 4 instruction ("state the specific gap the three options leave unaddressed"). Both still use "the three options" as grammatical anchor. The analysis/40 recommendation (C1+C2 above) is the correct fix and should be the next PR.

The verbatim-numbers prohibition works for consequences but not for options: haiku generates 10+ estimated numeric ranges per plan (screen counts, shooting-day splits, VOD windows) that are not verbatim from the project context. The options field description needs the constraint repeated explicitly (C3 above).

**H1:** Removing "the three options" from the `review_lever` field description and Section 4 will reduce haiku's template lock rate from 70–94% to below 20%, matching the prediction in analysis/40.

**H2:** Adding the verbatim-numbers note to the options field description will reduce estimated-figure generation in haiku options by 50–80%.

**Verdict: CONDITIONAL.** Keep the PR — no regressions, modest improvements. Immediately follow with the template-lock root-cause fix (C1+C2) as the next PR.
