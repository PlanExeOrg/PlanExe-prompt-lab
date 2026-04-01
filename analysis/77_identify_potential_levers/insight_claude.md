# Insight Claude

## Scope

Analyzing runs `5/46–5/52` (after PR #483) against `2/87–2/93` (previous analysis 40 / post-PR #358)
and against `5/39–5/45` (analysis 76 / post-PR #482) for the `identify_potential_levers` step.

**PR under evaluation:** PR #483 "Strip field descriptions to word limits, anti-parrot in call-2+, fix threshold"

**Changes made by PR #483:**
- `consequences` field description: `"Direct effect and one downstream implication (30–60 words)."`
- `options` field description: `"Exactly 3 options. Each is one sentence (15–25 words) — a concrete strategic approach."`
- `review_lever` field description: `"Critical review (20–40 words). No square brackets or placeholders."` — removed "one sentence", removed "See system prompt section 4 for examples."
- Anti-parrot in call-2+: added `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence."` to subsequent-call user prompt
- Section 4 preamble: `"A one-sentence critical review (20–40 words). Examples:"` — added explicit word count
- System prompt section 2: consequences target 30–60 words
- System prompt section 6: options 15–25 words
- Fix `partial_recovery` threshold: `runner.py` `< 3` → `< 2`
- Net -22 lines

**Model mapping (current vs previous):**

| Run (before/analysis40) | Run (before/analysis76) | Run (after/analysis77) | Model |
|---|---|---|---|
| 2/87 | 5/39 | 5/46 | ollama-llama3.1 |
| 2/88 | 5/40 | 5/47 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/41 | 5/48 | openai-gpt-5-nano |
| 2/90 | 5/42 | 5/49 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/43 | 5/50 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/44 | 5/51 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/45 | 5/52 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **Haiku fabricated percentage claims: 67 → 22 (−67%).** The most striking improvement is in haiku's
   fabricated quantification. Before (run 5/45), the haiku output contained 67 percentage/dollar claims
   across 110 levers. After (run 5/52), only 22 claims across 93 levers. This is a genuine, large
   reduction driven primarily by the tightened consequences word-limit (30–60 words) preventing haiku
   from inserting multiple fabricated statistics in long consequence paragraphs. Evidence: in run 5/45
   parasomnia plan, `"Manual dual-scoring of all events by independent raters ensures AASM-guideline
   concordance... at 15–30 minutes per event"`, `"requires hundreds of hours of expert time; with
   estimated 70–80% of participants"`. After (run 5/52) parasomnia reviews contain domain reasoning
   without injected percentages.
   Files: `history/5/45_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`,
   `history/5/52_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

2. **Haiku consequences pulled into 30–60 word target range: 19% → 69%.** Before (run 5/45),
   haiku averaged 77.7 words for consequences — 2.18× baseline. Only 19% of consequences were in
   the 30–60 word target range. After (run 5/52), the average dropped to 55.7 words (1.56× baseline)
   and 69% are in range. The explicit word count in the field description appears to be effective
   for haiku. Evidence: run 5/45 silo lever "Construction Phasing and Seal Timeline" is 82 words;
   same plan in run 5/52 shows consequences of 38–43 words as the norm.
   Files: `history/5/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
   `history/5/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

3. **Anti-parrot instruction eliminated gpt-oss-20b exact-copy reviews in call-2+: 6 → 0.** The previous
   analysis (76) found gpt-oss-20b had 6 exact-copy parrots (review ≡ consequence). After PR #483's
   anti-parrot instruction in the subsequent-call user prompt, gpt-oss-20b has 0 exact-copy parrots.
   High-similarity levers also dropped from 11 to 6.
   Files: `history/5/40_identify_potential_levers/` vs `history/5/47_identify_potential_levers/`.

4. **Overall fabricated percentage claims reduced: 80 → 47 (−41%) across all models combined.**
   The combined reduction across all 7 models is substantial, driven primarily by haiku but with
   haiku's improvement dominating. Models without prior fabrication issues (gpt-5-nano, gpt-4o-mini,
   gemini-flash) remain at 0.

5. **Overall high-similarity (review≈consequence) reduced: 100 → 46 across all models.**
   The anti-parrot instruction and tightened review field description collectively reduced parroting
   across the full suite, from 100 high-sim levers to 46. The main driver is gpt-4o-mini reducing
   from 26 to 7 and gemini-flash from 21 to 5, alongside gpt-oss-20b improving.

6. **Partial recovery threshold fix is semantically correct.** The `runner.py` fix from `< 3` to `< 2`
   means `partial_recovery` events now only fire when a plan completed with only 1 call instead of
   the expected 2–3. Previously it fired spuriously when 2 calls succeeded, which is normal
   (expected-calls=3 was based on worst case, not the happy path). This removes false positives
   from analysis event logs. Confirmed at `identify_potential_levers.py` line 279 (line count
   consistent with `min_levers=15`, requiring 2 calls for most plans). Files: `runner.py:579`.

7. **No LLMChatErrors or ValidationErrors in current runs.** All 7 runs have clean event logs
   with zero schema failures. Files: `history/5/46–52_identify_potential_levers/events.jsonl`.

---

## Negative Things

1. **llama3.1 developed call-1 parrot regression on gta_game: 0 → 7 exact copies.** The most alarming
   regression is llama3.1 run 5/46, gta_game plan: all 7 first-call levers (indices 0–6) have
   `review` ≡ `consequences` verbatim (sim=1.0). Example:
   - consequences: `"Assembling a team of experienced developers and industry veterans can accelerate project timelines by up to 6 months, but also increases labor costs by approximately $10 million."`
   - review: *(identical text)*
   This did not exist in run 5/39 (PR #482), where the same plan had sim=0.04–0.30 for all levers.
   The regression correlates precisely with the PR #483 change to `review_lever` field description:
   removing `"one sentence"` and `"See system prompt section 4 for examples."` left llama3.1 with
   only `"Critical review (20–40 words). No square brackets or placeholders."` — no structural anchor
   and no pointer to the examples in section 4. The anti-parrot instruction only applies to call-2+,
   so call-1 parroting is not addressed.
   File: `history/5/46_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

2. **gpt-4o-mini consequences collapsed to below target: 32.5w → 20.6w (in-range 74% → 0%).** Before,
   gpt-4o-mini had 74% of consequences in the 30–60 word range at 32.5 avg words. After, the average
   dropped to 20.6 words and 0% are in range — all consequences are now too short. The new field
   description `"Direct effect and one downstream implication (30–60 words)."` appears to be
   interpreted as "one effect + one implication = two short sentences" rather than "up to 60 words."
   Example from run 5/50 silo: `"Tightening information control can maintain order and prevent panic,
   but risks creating distrust among residents and stifling innovation."` — 18 words, two clauses,
   structurally correct but informationally thin. Before (run 5/43) the same lever had 35 words.
   Files: `history/5/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
   `history/5/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

3. **gemini-flash options shortened below target: 23.5w → 13.9w (in-range 71% → 37%).** The option
   word-count instruction (`"Each is one sentence (15–25 words)"`) drove gemini-flash options well
   below the minimum. Before, gemini averaged 23.5 words per option (near the upper limit). After,
   options average 13.9 words — below the 15-word minimum. Example from run 5/51 silo:
   `"Establish a council of elected representatives from each sector to legislate and oversee silo operations."` — 15 words barely in range. Most options are 14–15 words. Previously they were 20–24.
   File: `history/5/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

4. **qwen3-30b fabricated percentage claims increased: 6 → 16 (+10).** Qwen3-30b had 6 pct claims
   in run 5/42; after PR #483, run 5/49 has 16 pct claims. The fabricated numbers appear consistently
   across silo and gta_game plans: `"22% higher initial investment"`, `"18% and 33%"` mental health
   crisis risk, `"40% more storage space"`, `"18% increase in infrastructure costs"`, etc. The PR did
   not specifically target qwen3-30b's fabrication pattern. This regression is not explainable by
   field description changes and likely reflects model stochasticity.
   File: `history/5/49_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

5. **qwen3-30b options further below target: 10.5w → 9.2w (in-range 11% → 1%).** Qwen3-30b was
   already generating very short options in PR #482 runs (avg 10.5w). After PR #483, options are
   even shorter at 9.2w avg, and only 1% are in the 15–25 word target range. The `"15–25 words"` instruction
   in the field description is having zero positive effect — qwen3-30b continues to ignore it. Example:
   `"Implement a technocratic council with AI-driven policy enforcement"` — 9 words.
   File: `history/5/49_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

6. **Plan-level success rate decreased: 33/35 → 31/35 (gpt-5-nano adds 2 timeout plans).**
   PR #482 had 2 timeout failures (gpt-oss-20b, run 5/40: sovereign_identity + parasomnia). PR #483
   has 4 timeout failures:
   - gpt-oss-20b (run 5/47): sovereign_identity + hong_kong_game
   - gpt-5-nano (run 5/48): sovereign_identity + parasomnia
   The timeouts are plan-specific (sovereign_identity appears in both). Duration stats: gpt-5-nano
   silo and hong_kong_game both completed (426s, 574s) but sovereign_identity hit the 600s wall.
   This may be provider latency rather than prompt-induced token inflation. However, the pattern is
   worsening across iterations.
   Files: `history/5/47–48_identify_potential_levers/outputs.jsonl`.

7. **llama3.1 consequences moving further below target: 33% → 14% in 30–60w range.** The
   consequences field description change appears to be pushing llama3.1 consequences shorter.
   Before: 26.2w avg, 33% in range. After: 21.9w avg, 14% in range. llama3.1 was already
   generating short consequences; the new description compounds this.

---

## Comparison

### vs. analysis 76 (PR #482, runs 5/39–45)

The most relevant comparison for evaluating PR #483's impact is against the immediate predecessor state.

**Summary:** PR #483 produced a major haiku improvement and fixed gpt-oss-20b parroting, but introduced or worsened issues in gpt-4o-mini (consequences too short), gemini-flash (options too short), llama3.1 (call-1 parrot regression), and qwen3-30b (more fabricated numbers).

### vs. analysis 40 (PR #358, runs 2/87–93)

Compared to the pre-PR #482 baseline, PR #483's cumulative changes show:
- Haiku: pct claims went from 35 (2/93) to 22 (5/52) — overall improvement, though PR #482 temporarily increased them to 67 before PR #483 pulled them back down
- Template locks: all previously identified locks eliminated (qwen "creates X gaps", haiku "none/all three options") — these were fixed by PR #482
- gpt-oss-20b: parroting now eliminated vs. before (2/88: 0 exact parrots vs after 5/47: 0 exact parrots; previously intermediate PR #482 run 5/40 had 6 exact parrots)
- New regressions vs. analysis 40: llama3.1 call-1 parroting on gta_game (new), gpt-4o-mini consequences too short (new), gemini-flash options too short (new)

---

## Quantitative Metrics

### Success Rates

| Model | Before (PR #482) | After (PR #483) |
|---|---|---|
| llama3.1 | 5/5 | 5/5 |
| gpt-oss-20b | 3/5 (2 timeouts) | 3/5 (2 timeouts) |
| gpt-5-nano | 5/5 | 3/5 (2 timeouts) |
| qwen3-30b | 5/5 | 5/5 |
| gpt-4o-mini | 5/5 | 5/5 |
| gemini-flash | 5/5 | 5/5 |
| haiku-4.5 | 5/5 | 5/5 |
| **TOTAL** | **33/35 (94.3%)** | **31/35 (88.6%)** |

### Field Length vs. Targets (PR #482 before → PR #483 after)

Targets: consequences 30–60w, review 20–40w, options 15–25w per option.

| Model | cons_w B→A | cons_%in B→A | rev_w B→A | rev_%in B→A | opt_w B→A | opt_%in B→A |
|---|---|---|---|---|---|---|
| llama3.1 | 26.2→21.9 | 33%→**14%** | 17.5→21.6 | 28%→69% | 13.2→11.0 | 34%→28% |
| gpt-oss-20b | 31.5→28.4 | 56%→46% | 22.6→25.2 | 84%→95% | 18.1→17.3 | 82%→92% |
| gpt-5-nano | 31.9→34.2 | 55%→82% | 22.9→25.9 | 81%→96% | 17.0→16.3 | 91%→92% |
| qwen3-30b | 29.4→29.3 | 44%→36% | 16.3→18.7 | 16%→34% | 10.5→9.2 | 11%→**1%** |
| gpt-4o-mini | 32.5→**20.6** | 74%→**0%** | 18.1→18.6 | 18%→30% | 19.1→15.0 | 97%→59% |
| gemini-flash | 45.0→36.0 | 94%→89% | 20.5→19.8 | 60%→48% | 23.5→**13.9** | 71%→**37%** |
| haiku-4.5 | 77.7→**55.7** | 19%→**69%** | 34.9→37.0 | 79%→75% | 38.7→**29.7** | 3%→24% |

Baseline for reference: cons=35.7w, rev=20.4w, opt=19.0w.

Bold entries = significant change (positive = improvement, negative = regression).

### Fabricated Percentage Claims

| Model | Before (PR #482) | After (PR #483) | Change |
|---|---|---|---|
| llama3.1 | 0 | 2 | +2 |
| gpt-oss-20b | 7 | 7 | 0 |
| gpt-5-nano | 0 | 0 | 0 |
| qwen3-30b | 6 | **16** | **+10** |
| gpt-4o-mini | 0 | 0 | 0 |
| gemini-flash | 0 | 0 | 0 |
| haiku-4.5 | **67** | **22** | **−45** |
| **TOTAL** | **80** | **47** | **−33 (−41%)** |

### Parroting (review ≈ consequence)

| Model | exact_before | exact_after | high_sim_before | high_sim_after |
|---|---|---|---|---|
| llama3.1 | 0 | **7** | 20 | 11 |
| gpt-oss-20b | 6 | **0** | 11 | 6 |
| gpt-5-nano | 1 | 2 | 17 | 14 |
| qwen3-30b | 0 | 0 | 1 | 3 |
| gpt-4o-mini | 0 | 0 | 26 | 7 |
| gemini-flash | 0 | 0 | 21 | 5 |
| haiku-4.5 | 0 | 0 | 4 | 0 |
| **TOTAL** | **7** | **9** | **100** | **46** |

### Template Lock Patterns

| Pattern | Before (PR #482) | After (PR #483) |
|---|---|---|
| haiku "none/all three options" | 0 (already fixed by PR #482) | 0 |
| qwen "creates X risks, leaving Y gaps" | 0 (already fixed by PR #482) | 0 |
| gpt-oss-20b "options do not address" | 0 (already fixed by PR #482) | 0 |
| llama gta_game call-1 copy (new) | 0 | **7 (exact copies)** |

---

## Evidence Notes

- `history/5/46_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`:
  levers 0–6 have `review` ≡ `consequences` verbatim. Lever 0 "Team Composition": consequences and review
  both read `"Assembling a team of experienced developers and industry veterans can accelerate project timelines by up to 6 months, but also increases labor costs by approximately $10 million."`
- `history/5/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
  consequences are 38–43 words, review is 31–35 words. Qualitatively improved vs run 5/45 (71–98 words consequences).
- `history/5/49_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
  qwen3-30b fabricated stats: `"22% higher initial investment"`, `"18% and 33%"` for mental health crisis risk, `"40% more storage space"`, `"18% increase"` — none grounded in project context.
- `history/5/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
  gpt-4o-mini consequences examples: 18w (`"Tightening information control can maintain order and prevent panic, but risks creating distrust among residents and stifling innovation."`), 25w, 21w. Consistently below 30-word target.
- `history/5/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
  gemini-flash options: `"Establish a council of elected representatives from each sector to legislate and oversee silo operations."` (15w), `"Implement a meritocratic system where individuals advance based on skills and contributions, forming a technocratic leadership."` (16w). Previously 20–24w.
- `analysis/77_identify_potential_levers/events.jsonl`: No LLMChatErrors. Timeouts in runs 5/47 and 5/48 for sovereign_identity plan (both models) — confirmed as plan-level timeout events, not schema failures.

---

## PR Impact

### What the PR Was Supposed to Fix

From PR description:
1. Minimal field descriptions — strip redundant guidance, keep only word limits
2. Anti-parrot in call-2+ — add prohibition sentence to subsequent-call prompt
3. Minimal section 4 — no copyable template
4. System prompt section 2 word limits for consequences
5. System prompt section 6 word limits for options
6. Fix `partial_recovery` threshold (`< 3` → `< 2`)

The primary targets from analysis 76's recommendations were:
- C1: Add anti-parroting guidance to call-2+ prompt (addressed ✓)
- C2: Investigate haiku fabricated-numbers (partially — word limits reduced haiku verbosity) ✓
- `partial_recovery` threshold fix (addressed ✓)

### Before vs After Comparison

| Metric | Before (runs 2/87–93) | After (runs 5/46–52) | Change |
|---|---|---|---|
| Plan-level success | 35/35 (one plan missing in run 2/92 before) | 31/35 | REGRESSED −4 plans |
| Plan-level timeouts | 0 | 4 (gpt-oss-20b×2, gpt-5-nano×2) | NEW (monitoring needed) |
| LLMChatErrors | 0 | 0 | UNCHANGED |
| haiku pct claims | 35 | 22 | IMPROVED −37% |
| qwen3-30b pct claims | 4 | 16 | REGRESSED +12 |
| All-model pct claims | 39 | 47 | REGRESSED +8 (vs analysis 40) |
| haiku cons avg words | 67.5w | 55.7w | IMPROVED (closer to target) |
| haiku cons in-range | 46% | 69% | IMPROVED +23pp |
| gpt-4o-mini cons in-range | 76% | 0% | REGRESSED −76pp |
| gemini options in-range | 60% | 37% | REGRESSED −23pp |
| qwen3-30b options in-range | 15% | 1% | REGRESSED −14pp |
| Overall high-sim parroting | pre-PR #482 not counted | 46 total | See analysis 76 |
| Template locks | 0 (already fixed) | 0 | UNCHANGED |
| llama3.1 call-1 exact parrot (gta_game) | 0 | 7 | NEW REGRESSION |
| partial_recovery threshold | Incorrect (< 3) | Correct (< 2) | FIXED |

**Compared to analysis 76 (the immediate predecessor PR #482 runs 5/39–45):**

| Metric | Before (PR #482, 5/39–45) | After (PR #483, 5/46–52) | Change |
|---|---|---|---|
| Plan success | 33/35 | 31/35 | REGRESSED −2 |
| haiku pct claims | 67 | 22 | IMPROVED −45 |
| qwen3-30b pct claims | 6 | 16 | REGRESSED +10 |
| All-model pct claims | 80 | 47 | IMPROVED −33 |
| haiku cons in-range (30–60w) | 19% | 69% | IMPROVED +50pp |
| gpt-4o-mini cons in-range | 74% | 0% | REGRESSED −74pp |
| gemini options in-range (15–25w) | 71% | 37% | REGRESSED −34pp |
| gpt-oss-20b exact parrots | 6 | 0 | IMPROVED |
| llama3.1 exact parrots | 0 | 7 | REGRESSED |
| overall high-sim parroting | 100 | 46 | IMPROVED −54 |

### Did the PR Fix the Targeted Issue?

- **Anti-parrot in call-2+:** PARTIALLY. gpt-oss-20b exact parrots dropped from 6 to 0. However, llama3.1 developed new call-1 parroting (not addressed by call-2+ change). The anti-parrot instruction did not help qwen3-30b (which had 0 before and after).
- **Haiku word limits:** YES. Haiku consequences dropped from 77.7w to 55.7w average, with in-range improving from 19% to 69%. Fabricated percentages fell from 67 to 22 (−67%).
- **Partial recovery threshold:** YES. Code fix confirmed in runner.py:579.
- **Field description minimization:** MIXED. Helped haiku (shorter consequences). Hurt gpt-4o-mini (consequences collapsed to 0% in range). Hurt gemini-flash (options below target). Caused llama3.1 call-1 parroting.

### New Issues Introduced

1. **llama3.1 call-1 parrot regression on gta_game.** Removing `"one sentence"` and `"See system prompt section 4 for examples"` from the `review_lever` field description caused llama3.1 to copy consequences verbatim in the first call.
2. **gpt-4o-mini consequences too short (0% in 30–60w range).** The `"Direct effect and one downstream implication"` wording drives gpt-4o-mini to generate two-clause sentences of 18–22 words.
3. **gemini-flash options shortened below target.** The `"15–25 words"` target combined with other guidance is pushing gemini from 23w to 14w per option.
4. **gpt-5-nano added 2 plan timeouts** (though outputs may still be complete on disk — not confirmed for run 5/48).

### Verdict

**CONDITIONAL** — The PR delivers a genuine, large improvement for haiku (fabricated numbers −67%, consequences pulled into target range) and fixes gpt-oss-20b call-2+ parroting, along with the correct partial_recovery code fix. However, three regressions require follow-up:

- **C1:** llama3.1 gta_game call-1 parrot (exact-copy reviews in all 7 first-call levers). The `review_lever` field description needs `"one sentence"` and/or an example cross-reference restored for small models.
- **C2:** gpt-4o-mini consequences collapsed to 0% in range. The `"Direct effect and one downstream implication"` wording is being parsed as a length cap of ~20 words, not a minimum. Rephrase to clarify 30–60 words is a minimum, not a ceiling.
- **C3:** gemini-flash options shortened below 15-word floor (13.9w avg). Investigate whether `"one sentence"` phrasing is the cause.

---

## Questions For Later Synthesis

1. Is the llama3.1 gta_game call-1 parrot deterministic (would reproduce on re-run) or stochastic? If deterministic, it strongly implicates the field description change. A re-run of llama3.1 on gta_game with/without the PR changes would disambiguate.

2. The anti-parrot instruction is in call-2+ only. Should it be added to call-1 as well, given that llama3.1 exhibits parroting in call-1? What's the risk of adding it to call-1 (potential template-lock on "genuine critical assessment")?

3. For gpt-4o-mini, the consequences dropped from 32.5w to 20.6w. The previous field description was from PR #479 (before analysis 76). What exact wording did PR #483 replace? Was there a "2–3 sentences" instruction that got stripped?

4. The qwen3-30b options have been persistently short (10.5w → 9.2w) across two PR iterations. Is qwen3-30b incapable of generating 15–25 word options, or is there a structural reason (e.g., qwen outputs options as bullet fragments rather than full sentences)?

5. gpt-5-nano added 2 new plan timeouts. Is this correlated with specific plans (sovereign_identity appears in both gpt-oss-20b and gpt-5-nano timeouts)? Is sovereign_identity uniquely slow due to token count or model latency?

---

## Reflect

The PR attempted to strip all redundant guidance from field descriptions, leaving only word limits. This worked well for haiku — which had been over-generating — but backfired for models that relied on the additional structural cues (llama3.1, gpt-4o-mini). The "minimal field description" approach follows OPTIMIZE_INSTRUCTIONS principles about field-description template lock, but went too minimal for models at the low end of the capability spectrum.

Key tension: haiku needs constraints to prevent over-generation. llama3.1 and gpt-4o-mini need scaffolding to maintain quality. A single field description serves both. The current PR found a sweet spot for haiku at the cost of small-model quality.

The partial_recovery threshold fix and anti-parrot sentence are unambiguous improvements. The field description minimization is a mixed result — beneficial for the most capable models, potentially harmful for weaker ones.

---

## Potential Code Changes

**C1** (confirmed regression): The `review_lever` field description at `identify_potential_levers.py:118` should have `"one sentence"` restored and optionally an example pointer. Current: `"Critical review (20–40 words). No square brackets or placeholders."` Proposed: `"Critical review in one sentence (20–40 words). See system prompt section 4 for examples."` This restores the exact wording from PR #482 that was working for llama3.1 in run 5/39.

**C2** (confirmed regression): The `consequences` field description at `identify_potential_levers.py:112` reads `"Direct effect and one downstream implication (30–60 words)."` For gpt-4o-mini, this is being parsed as ~20 words. Proposed: `"The direct effect of pulling this lever and one key downstream implication. Write 30–60 words."` — separating the content requirements from the length requirement may prevent gpt-4o-mini from treating "one implication" as a hard brevity constraint.

**C3** (regression to investigate): gemini-flash options shortened from ~23w to ~14w. The options field description reads `"Exactly 3 options. Each is one sentence (15–25 words) — a concrete strategic approach."` Test removing `"one sentence"` from the options description — gemini may be treating it as a brevity signal. If gemini needs `"one sentence"` to prevent multi-sentence options, the length constraint alone (`"15–25 words"`) should be sufficient.

**C4** (pre-existing, not from this PR): `OPTIMIZE_INSTRUCTIONS` in `identify_potential_levers.py` lines 27–93 still lacks a "Consequence parroting" entry, which was recommended in analysis 76. The anti-parrot instruction was added to the runtime prompt, but the self-improve documentation was not updated. Proposed addition: `"- Consequence parroting. In later adaptive-loop calls (call 2+), weaker models (llama3.1) restate the consequences field as the review with minor modal substitution ('could' → 'can'). The subsequent-call user prompt must include an explicit anti-parroting prohibition. The call-1 prompt is also at risk for very weak models (llama3.1 on complex plans). Monitor for exact-copy reviews across all call indices."`

---

## Summary

PR #483 achieves its primary goals for haiku: consequences pulled into the 30–60 word target range (19%→69% in range), fabricated percentages cut by 67%, and word-limit enforcement working. The anti-parrot sentence in call-2+ fixed gpt-oss-20b's exact-copy reviews. The partial_recovery threshold correction is an unambiguous code improvement.

However, three regressions limit a clean KEEP:

1. **llama3.1 gta_game call-1 parrot** (7/7 first-call levers are exact consequences copies in run 5/46) — caused by removing structural anchors from the `review_lever` field description.
2. **gpt-4o-mini consequences collapsed** (0% in 30–60w range, avg 20.6w) — caused by `"one downstream implication"` being parsed as a hard brevity cap.
3. **qwen3-30b fabricated claims increased** (6→16) — source unclear, may be stochastic.

The verdict is **CONDITIONAL**, contingent on:
- Restoring `"one sentence"` and an example pointer to the `review_lever` field description for llama3.1 recovery
- Rewording the `consequences` field description to prevent gpt-4o-mini over-truncation
- Monitoring gemini-flash option lengths in the next iteration
