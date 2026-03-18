# Insight Claude

Analysis of `identify_potential_levers` runs `2/31` through `2/37` (current) versus
prior runs `2/24` through `2/30` (from analysis 31), evaluating PR #346
"Add lever_type and decision_axis to lever schema".

---

## Schema Orientation

**A critical structural difference** separates the two groups:

| Group | Runs | Classification schema | Source code state |
|-------|------|-----------------------|-------------------|
| Current (this analysis) | 31–37 | `lever_classification` (combined phrase) | Main branch without PR |
| Previous (analysis 31) | 24–30 | `lever_type` + `decision_axis` (separate fields) | PR #346 branch |

The current `identify_potential_levers.py` (confirmed by direct read) defines
`lever_classification` as a single combined field:
> "Brief classification: category and what this lever controls. Format: 'category — what this lever decides'."

PR #346 would change this to two separate fields:
- `lever_type` — one of: methodology / execution / governance / dissemination / product / operations
- `decision_axis` — sentence: "This lever controls X by choosing between A, B, and C"

Runs 31–37 were done on the main branch (lever_classification); runs 24–30 were done
on the PR branch (lever_type + decision_axis). All observations below use this framing.

---

## Negative Things

### N1. Ollama (run 31) fails 2 of 5 plans

`history/2/31_identify_potential_levers/events.jsonl` records two complete failures:

```
run_single_plan_error for 20250329_gta_game: 5 validation errors —
  levers.3.options: options must have at least 3 items, got 2
  levers.4.options: options must have at least 3 items, got 2
  levers.5.options: options must have at least 3 items, got 2
  levers.6.options: options must have at least 3 items, got 2
  levers.7.options: options must have at least 3 items, got 2

run_single_plan_error for 20260310_hong_kong_game: 1 validation error —
  levers.5.options: options must have at least 3 items, got 2
```

Both failures are caused by the `min_length=3` validator on `options`. Ollama-llama3.1
consistently under-generates options. This is a recurring problem (same model, same failure mode
as noted in prior analyses). No output file exists for these plans.

### N2. Gemini (run 36) partial_recovery on sovereign_identity

`history/2/36_identify_potential_levers/events.jsonl`:
```json
{"event": "partial_recovery", "plan_name": "20260308_sovereign_identity",
 "calls_succeeded": 1, "expected_calls": 3}
```
Only 1 of 3 LLM calls succeeded. The final lever file for sovereign_identity therefore
has roughly one-third the expected lever diversity. The partial recovery logic is working
correctly (levers from the 1 successful call are preserved), but the plan is under-served.

### N3. Template lock in review fields

Multiple models reproduce structurally identical review patterns regardless of domain:

**Run 35 (gpt-4o-mini, without PR) — hong_kong_game:**
All 17 reviews follow: _"The [tension/conflict] between X and Y [is unresolved /
remains unaddressed]. None of the options [explicitly/fully] [verb] [challenge]."_

Examples:
- "The tension between cultural authenticity and global marketability is unresolved. None of the options explicitly address potential creative clashes…"
- "The conflict between global marketability and local authenticity remains unaddressed. None of the options explicitly tackle…"
- "The tension between realism and narrative control is unresolved. None of the options fully account for…"

**Run 34 (qwen3) and run 36 (gemini)** are less severe but still follow
"The [tension/challenge] between X and Y is [critical/significant]. The options [overlook/do not address/fail to consider]…"

The review examples in the system prompt use "but none of the options price in..."
and "the options assume..." — the models generalise these closings to all levers.

This violates OPTIMIZE_INSTRUCTIONS: "Examples must avoid reusable transitional phrases
that fit any domain."

### N4. Lever count drops sharply when PR is applied

Comparing the same models across the two groups for hong_kong_game:

| Model | Current run (without PR) | Previous run (with PR) | Reduction |
|-------|--------------------------|------------------------|-----------|
| gpt-4o-mini | run 35: 17 levers | run 28: 11 levers | −35% |
| gemini | run 36: 17 levers | run 29: 6 levers | −65% |

This reduction is too large to be random variation. The most plausible cause is that the
new `decision_axis` (minimum-length validator + structured-sentence requirement) and
`lever_type` enum constraint in PR #346 cause LLM call responses to fail Pydantic
validation and be dropped by the partial-recovery logic.

If a single call produces an invalid `decision_axis` (too short or wrong type), the
entire batch of 5–7 levers from that call is discarded. For gemini, two of three calls
appear to have been dropped for hong_kong_game, leaving only 6 levers.

### N5. Some options are underdeveloped (run 34, qwen3)

Run 34 hong_kong_game options are noticeably shorter than other models:
- "Film exclusively on location across Hong Kong's vertical strata to embed the city's architecture as a psychological antagonist" (full sentence but very abstract)
- "Construct a modular soundstage replicating key Hong Kong environments to control narrative pacing and reduce permit hurdles" (reasonable)
- "Use location shooting for exterior sequences and practical sets for interiors to balance authenticity with production efficiency" (also fine)

The shortness is not severe but options average ~70–90 chars vs ~100–150 for gemini/haiku.
These options are closer to labels than full strategic approaches.

---

## Positive Things

### P1. No fabricated percentages in current runs

The baseline training data (hong_kong_game) contains systematic percentage fabrication:
- "15% higher audience engagement due to novelty"
- "20% higher pre-sales based on star power"
- "30% increase in streaming revenue through exclusive deals"
- "25% increase in tourism to filming locations"

Current runs (31–37) show zero fabricated percentages for hong_kong_game and gta_game.
This is a major improvement from baseline and confirms the "No fabricated statistics"
prohibition in the system prompt is working.

### P2. Haiku (run 37) delivers outstanding silo levers

`history/2/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
contains 21 levers of exceptional quality:

- Highly domain-specific (references sealed populations, geothermal gradients,
  bedrock geology, bioreactor contamination, Orwellian surveillance dynamics)
- Long, non-formulaic consequences (300–600 chars per lever)
- Specific, actionable options (e.g., "Construct twelve independent multi-chamber
  airlocks with full decontamination showers, chemical analysis, and biological screening")
- Deep review critiques naming overlooked failure modes
- No marketing language

Sample review: _"None of the options address the institutional divergence problem: what
happens if surface sensors, sensors, or external contacts reveal contradictory information,
making the authority's narrative incoherent?"_

This is the kind of grounded, domain-specific lever set the OPTIMIZE_INSTRUCTIONS asks for.

### P3. Partial recovery logic prevents total failure

When one LLM call fails, the code logs `partial_recovery` and preserves levers from
successful calls instead of discarding everything. This is correctly implemented and
working (confirmed in run 36 sovereign_identity and run 31 parasomnia).

### P4. lever_classification field is concise and informative

Current runs use `lever_classification` strings like:
- `"governance — what information residents receive and who controls it"` (silo, run 37)
- `"execution — the sequence of construction and population phases"` (silo, run 37)
- `"product — how to structure the film's twist to surprise audiences"` (hong_kong, run 32)

These are specific, non-generic, and useful for downstream selection. The combined
"category — what this lever decides" format provides sufficient information without
requiring a separate sentence for the decision axis.

### P5. Review lengths improved ~2-3× over baseline

Estimated average review length:
- Baseline hong_kong_game: ~70 chars
- Current runs (31–37): ~150–300 chars
- Previous runs (24–30): ~180–250 chars

All current groups exceed baseline. Reviews name real project-specific tensions
rather than the formulaic "Controls X vs. Y" pattern seen in older baseline files.

---

## Comparison

| Dimension | Current (without PR, 31–37) | Previous (with PR, 24–30) |
|-----------|----------------------------|--------------------------|
| Classification schema | `lever_classification` (1 combined field) | `lever_type` + `decision_axis` (2 separate fields) |
| Hong_kong_game lever count (gemini) | 17 | 6 |
| Hong_kong_game lever count (gpt-4o-mini) | 17 | 11 |
| Content quality | Comparable | Comparable |
| Template lock (review) | Moderate–severe | Moderate |
| Fabricated percentages | 0 | 0 |
| Ollama success rate | 3/5 plans | ~2/5 plans |
| Gemini partial_recovery | 1 plan (sovereign) | Not measured |
| Structured decision framing | None (free phrase) | "This lever controls X by choosing between A, B, C" |

The PR adds value by splitting the classification into a typed field (`lever_type`) and
a structured decision sentence (`decision_axis`). However, the net effect on lever count
is sharply negative: the same models produce roughly 35–65% fewer levers when the PR code
is active. This suggests that the new validators are rejecting a significant fraction of
LLM-generated lever sets.

---

## Quantitative Metrics

### Lever counts across plans and models

**Hong_kong_game (002-10-potential_levers.json):**

| Run | Model | Group | Lever Count |
|-----|-------|-------|-------------|
| 32 | openrouter-openai-gpt-oss-20b | Current (no PR) | 18 |
| 34 | openrouter-qwen3-30b-a3b | Current (no PR) | 20 |
| 35 | openrouter-openai-gpt-4o-mini | Current (no PR) | 17 |
| 36 | openrouter-gemini-2.0-flash-001 | Current (no PR) | 17 |
| 28 | openrouter-openai-gpt-4o-mini | Previous (with PR) | 11 |
| 29 | openrouter-gemini-2.0-flash-001 | Previous (with PR) | 6 |

**Silo (002-10-potential_levers.json):**

| Run | Model | Group | Lever Count |
|-----|-------|-------|-------------|
| 31 | ollama-llama3.1 | Current (no PR) | 15 (silo succeeded) |
| 37 | anthropic-claude-haiku-4-5-pinned | Current (no PR) | 21 |

### Estimated average field lengths (chars) — hong_kong_game

| Field | Current (no PR, runs 32–36) | Previous (with PR, runs 28–29) | Baseline |
|-------|-----------------------------|-------------------------------|---------|
| lever_classification | ~55 | N/A | N/A |
| lever_type | N/A | ~12 | N/A |
| decision_axis | N/A | ~125 | N/A |
| consequences | ~250 | ~280 | ~200 |
| options (per option) | ~100 | ~110 | ~130 |
| review | ~180 | ~200 | ~70 |

Both current groups have consequences ~1.2–1.4× baseline and review ~2.5–3× baseline.
Neither group shows the 3–4× verbosity seen in earlier iterations (iteration 17 had
consequences at ~980 chars). Lengths are within acceptable range.

### Fabricated quantification counts

| Plan | Current (no PR) | Previous (with PR) | Baseline |
|------|-----------------|--------------------|---------|
| hong_kong_game | 0 | 0 | 7 |
| gta_game | 0 | — | 3 |
| silo (run 37) | 0–2* | — | — |

*Run 37 (haiku) silo levers contain a few specific percentages (e.g., "28–35% of total
power generation", "$2–4 billion") — these appear grounded in engineering plausibility
rather than fabricated claims, but they are specific. Synthesis agents should flag this
for review.

### Template lock (review field)

| Run | Model | Severity | Pattern |
|-----|-------|----------|---------|
| 35 | gpt-4o-mini | Severe | "The tension/conflict between X and Y is unresolved. None of the options explicitly/fully [verb]…" |
| 36 | gemini | Moderate | "The core tension is between X and Y. The options focus on Z but overlook…" |
| 34 | qwen3 | Moderate | "The tension between X and Y is critical. The options do not address…" |
| 37 | haiku (silo) | Low | Domain-specific content despite loose structural similarity |
| 32 | gpt-oss-20b | Moderate | "Balancing X with Y creates tension. None of the options address…" |

Template lock is present in both the current (no PR) and previous (with PR) groups.
It is a persistent structural problem independent of the PR's schema changes.

### LLMChatError events

| Run | Model | Plan | Error type |
|-----|-------|------|-----------|
| 31 | ollama | gta_game | options < 3 (5 levers violated) — FAILED |
| 31 | ollama | hong_kong_game | options < 3 (1 lever violated) — FAILED |
| 36 | gemini | sovereign_identity | partial_recovery (1/3 calls succeeded) |

No LLMChatErrors were observed in other current runs (32, 33, 34, 35, 37).

---

## Evidence Notes

- `history/2/36_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
  17 levers, `lever_classification` format, no fabricated percentages, moderate template lock.
- `history/2/29_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
  6 levers only, `lever_type` + `decision_axis` format — dramatic under-count vs. 17 for same model without PR.
- `history/2/28_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
  11 levers, `lever_type` + `decision_axis`, gpt-4o-mini.
- `history/2/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
  21 levers, haiku, lever_classification — best quality content in the batch.
- `history/2/31_identify_potential_levers/events.jsonl`:
  Two `run_single_plan_error` entries — options < 3 validator killed both gta_game and hong_kong_game.
- `history/2/36_identify_potential_levers/events.jsonl`:
  `partial_recovery` on sovereign_identity with `calls_succeeded: 1, expected_calls: 3`.
- `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`:
  15 levers, no classification field, 7 fabricated percentages, review length ~70 chars.
- `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 111–117:
  Current `Lever` class has `lever_classification` field only; PR would add `lever_type` + `decision_axis`.
- `identify_potential_levers.py`, lines 163–169: `check_lever_classification` validator requires
  minimum 10 chars only (very permissive).
- `identify_potential_levers.py`, lines 219–264 (system prompt): Section 2 instructs
  `lever_classification` format only; PR would add new section guidance for both new fields.

---

## PR Impact

### What PR #346 was supposed to fix

PR #346 adds two structured fields to the lever schema:
1. `lever_type`: a typed enum (methodology / execution / governance / dissemination / product / operations)
2. `decision_axis`: a single sentence "This lever controls X by choosing between A, B, and C"

The intent is to:
- Make lever classification machine-queryable (enum vs. free text)
- Force explicit decision framing in every lever
- Add a system prompt section (section 2) guiding models on both fields
- Add validators: `lever_type` enum enforcement, `decision_axis` min 20-char length

### Before vs. After Comparison

| Metric | Before PR (runs 31–37, current) | After PR (runs 24–30, previous) | Change |
|--------|--------------------------------|--------------------------------|--------|
| Schema fields | `lever_classification` (1) | `lever_type` + `decision_axis` (2) | +1 field |
| hong_kong_game levers (gemini) | 17 | 6 | **−65%** |
| hong_kong_game levers (gpt-4o-mini) | 17 | 11 | **−35%** |
| Decision framing clarity | Implicit in combined phrase | Explicit "controls X by choosing…" | Improved |
| Lever type queryability | Free text | Enum | Improved |
| Template lock | Moderate–severe | Moderate | Slight improvement |
| Fabricated percentages | 0 | 0 | Unchanged |
| Consequences avg length | ~250 chars | ~280 chars | +12% |
| Review avg length | ~180 chars | ~200 chars | +11% |
| Ollama failure rate | 2/5 plans | ~3/5 plans | Worse |

### Did the PR fix the targeted issue?

The PR successfully adds structured classification (`lever_type` + `decision_axis`) and the outputs in
runs 24–30 confirm models can generate both fields correctly when they pass validation.
The `decision_axis` strings like "This lever controls the film's tone and authenticity by choosing
between a Hong Kong auteur, an Asian genre specialist, or an international director." are genuinely
useful — more explicit than the combined `lever_classification` phrase.

**However**, the PR introduces a serious regression: total lever counts per plan drop by 35–65%
for gemini and gpt-4o-mini. The most likely cause is that the new validators
(`lever_type` enum + `decision_axis` min 20-char) reject LLM call batches that contain any
lever failing validation, causing the partial-recovery code to discard entire 5–7 lever
responses. This is precisely the failure mode documented in the experiment insights:
"Schema-level hard constraints that clash with model output tendencies waste tokens
on retries and hurt success rates."

For gemini (run 29, hong_kong_game), dropping from 17 to 6 levers means the
downstream DeduplicateLevers step has much less material to work with. Only 6 levers
after deduplication provides insufficient diversity for the downstream scenario pipeline.

### Regressions

1. **Lever count reduction** (−35% to −65%): Primary regression. With only 6 levers
   (run 29, gemini), the downstream enrichment and scenario pipeline is severely limited.
2. **Ollama performance**: Ollama was already weak; the added schema complexity in PR #346
   appears to worsen its success rate further (run 24 appears to have ~2/5 plan successes
   vs. run 31's 3/5).

### Verdict

**CONDITIONAL**

The structural improvement (typed lever_type, explicit decision_axis sentence) is
genuinely valuable and the field content is good quality when it succeeds. However, the
35–65% reduction in lever count is a meaningful regression — it contradicts the OPTIMIZE_INSTRUCTIONS
principle that "over-generation is fine; step 2 handles extras." If validation is silently dropping
half the LLM output, the quality of what's kept may be good but the pipeline loses diversity.

To keep this PR, the following must be addressed:
1. The `decision_axis` validator minimum must be verified against actual model output distributions
   (hypothesis: many models generate valid <20-char decision_axis values that are being rejected)
2. If `lever_type` enum rejection is the cause, consider allowing type normalization before
   rejection rather than rejecting immediately
3. Check events.jsonl for runs 24–30 for LLMChatError entries with decision_axis
   or lever_type validation messages to confirm the root cause

---

## Questions For Later Synthesis

1. **Root cause of lever count drop**: Is the reduction in runs 24–30 caused by `decision_axis`
   min-length failures, `lever_type` enum failures, or model confusion about having two new
   required fields? Events.jsonl for runs 24–30 should be checked for validation error messages.

2. **Is lever_type enum too strict?**: The PR uses a 6-value enum. Do models sometimes generate
   synonymous but non-matching strings ("methodology" → "method", "operations" → "operational")?
   The PR description mentions "type normalization" validators — are these working?

3. **Haiku quality**: Run 37 (haiku) produced the best levers in this batch for the silo plan.
   Does haiku also produce high-quality levers for non-fiction plans (sovereign_identity, gta_game)?
   Its output for those plans is not confirmed.

4. **Template lock persistence**: Template lock has appeared in every iteration. The current
   system prompt has 3 review examples, but all use "options assume" or "options price in"
   phrasing. Should the examples be more structurally diverse? (See H2.)

5. **Could lever_type + decision_axis replace lever_classification entirely?**:
   Is the lever_classification field kept in the PR, or fully replaced? If both exist together,
   the schema has redundancy.

6. **Gemini partial_recovery on sovereign_identity**: What type of validation error caused 2/3
   calls to fail for sovereign_identity in run 36? Is this related to plan complexity or a
   transient model failure?

---

## Reflect

The strongest output in this batch comes from haiku (run 37) on the silo plan — 21 levers
with deep domain specificity, non-formulaic reviews, and no fabricated numbers. This suggests
haiku may be a better baseline model for content quality evaluation than gemini.

The template lock problem is structural and has persisted across many iterations. The current
examples in section 5 of the system prompt all end with "the options [assume / price in]"
phrasing. Models generalise this to "the options [overlook / do not address / fail to consider]"
across all reviews, regardless of domain. This will not be fixed by prompt wording alone —
the examples themselves need to be replaced with domain-specific, non-portable critiques.

The PR's schema approach is sound in principle. Two separate fields (typed enum + structured
sentence) are more useful downstream than a single free-text phrase. The problem is the
validation strictness. Hard Pydantic constraints that silently drop half the LLM's output are
worse than soft guidance that lets a downstream deduplication step handle over-generation.

---

## Potential Code Changes

**C1**: Before KEEPING PR #346, verify that the `decision_axis` minimum-length validator
(min 20 chars, per PR description) is not silently dropping valid lever batches. Consider
raising the threshold from "reject whole call" to "fix or skip individual levers" — or
remove the hard minimum and use a soft prompt-guidance approach instead.

**C2**: The `lever_type` enum validator should log a clear warning when a generated type
string is rejected. If normalization (lowercase, whitespace trimming) is insufficient, add
fuzzy matching for common near-misses ("methodology" → "methodology", "operational" → "operations").

**C3**: The `review_lever` validator (min 10 chars, lines 157–161) is very permissive. A
more useful threshold would be 50–80 chars, which would reject the formulaic 10-word reviews
while preserving genuinely short but specific critiques. Increasing it to 50 would not
affect any of the runs observed in this analysis (all reviews are well above that).

**H1**: Replace the three review examples in system prompt section 5 with examples from
three different domains (agriculture, infrastructure, technology) that each highlight a
different structural critique style — one naming an excluded stakeholder, one naming a
cost that compounds over time, one naming a correlated failure the options assume is independent.
This should reduce template lock. (Aligns with OPTIMIZE_INSTRUCTIONS: "Examples must avoid
reusable transitional phrases that fit any domain.")

**H2**: Add an explicit anti-template warning to the review_lever field description:
"Do not start every review with 'The tension between'. Name a concrete, domain-specific
failure the options share. The critique should NOT be portable to a different domain."

**H3**: For ollama specifically, consider adding a soft prompt reminder in the
"generate 5 to 7 MORE levers" call (call 2 and 3) that says: "Each option MUST contain
a full sentence with an action verb and at least 15 words. Do NOT generate fewer than
3 options for any lever — if you cannot think of 3 distinct approaches, skip the lever."
This addresses the recurring options<3 failure mode without tightening the Pydantic validator.

---

## Summary

The current runs (31–37) use `lever_classification` (combined field) and produce 17–21
levers per plan for capable models. The PR branch runs (24–30) use `lever_type` +
`decision_axis` (separate fields) but produce only 6–11 levers for the same models —
a 35–65% reduction that is the dominant regression of PR #346.

Content quality is similar in both groups: no fabricated percentages, moderate template
lock, reviews ~2–3× longer than baseline. The haiku model (run 37, silo) stands out as
the highest-quality output in the batch.

PR #346 verdict: **CONDITIONAL**. The schema design is sound, but the validation
strictness must be verified and softened before merging. The lever count regression
must be diagnosed (LLMChatError in runs 24–30 events.jsonl) and confirmed to be caused
by validator rejections rather than model capability. If the root cause is confirmed and
fixed, the PR is worth keeping for the downstream querying benefit of a typed `lever_type`.

Ollama's options<3 failures are a persistent, separate issue and not caused by this PR.
Template lock in review fields is also a pre-existing problem requiring example-level
fixes in the system prompt.
