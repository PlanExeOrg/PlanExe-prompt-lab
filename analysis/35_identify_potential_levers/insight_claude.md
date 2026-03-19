# Insight Claude

## Scope

Analyzing runs `2/52–2/58` (after PR #353) against `2/03–2/09` (before, from analysis 28)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #353 "fix: replace review_lever examples to break template lock"

Changes made: Replace all 3 `review_lever` examples in the system prompt to eliminate "the options"
as grammatical subject. Also update `OPTIMIZE_INSTRUCTIONS` to document template-lock migration.

**Before (analysis 28) examples** (options-centric):
1. "...but none of the options price in the idle-wage burden..."
2. "...the options assume permits will clear..."
3. "...correlation risk absent from every option."

**After (PR #353) examples** (domain-specific mechanisms):
1. "...the idle-wage burden during the 5-month off-season adds a fixed cost..."
2. "Section 106 heritage review triggers a mandatory 45–180-day public comment period..."
3. "...a single regional hurricane season can correlate all three simultaneously, turning the diversification assumption into a concentration risk..."

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/03 | 2/52 | ollama-llama3.1 |
| 2/04 | 2/53 | openrouter-openai-gpt-oss-20b |
| 2/05 | 2/54 | openai-gpt-5-nano |
| 2/06 | 2/55 | openrouter-qwen3-30b-a3b |
| 2/07 | 2/56 | openrouter-openai-gpt-4o-mini |
| 2/08 | 2/57 | openrouter-gemini-2.0-flash-001 |
| 2/09 | 2/58 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **llama3.1 silo: complete template lock elimination.** In run 03 (before), 18/19 silo reviews
   opened with "The options [overlook/fail/assume]…" (94.7% lock). In run 52 (after), 0/21 silo
   reviews use "the options" as grammatical subject. All reviews now start with domain-specific
   subjects: "The silo's ecosystem segmentation strategy is overly reliant on…", "The reliance on
   surveillance as a primary means of control overlooks…", "The vertical farming lever fails to
   consider the potential environmental impact…"
   Evidence: `history/2/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
   vs `history/2/03_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

2. **llama3.1 hong_kong_game: complete elimination of exact-duplicate reviews.** In run 03 (before),
   hong_kong_game produced 6 identical reviews ("The plan assumes a clear distinction between the
   game and reality, but what if the lines between them become blurred…") plus 3 "While these options…
   they overlook/fail/recognize" reviews. In run 52 (after), 0 reviews are exact duplicates and 0 use
   "the options" as subject. Reviews are now plan-specific: "The plan's emphasis on leveraging Hong Kong's
   film infrastructure and local crews may overlook the potential risks associated with relying heavily
   on external partners, such as IP rights management…"
   Evidence: `history/2/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

3. **Overall plan success rate improved from 97.1% to 100%.** Run 04 (before, gpt-oss-20b) failed
   on sovereign_identity with "Invalid JSON: EOF while parsing a list at line 58 column 5". In run 53
   (after, gpt-oss-20b), sovereign_identity completed successfully. No LLMChatErrors in any after run.
   Evidence: `history/2/04_identify_potential_levers/outputs.jsonl` (error) vs
   `history/2/53_identify_potential_levers/outputs.jsonl` (all OK).

4. **llama3.1 partial recoveries reduced from 2 to 1.** Before: sovereign_identity (2/3) and
   hong_kong_game (2/3). After: only gta_game (2/3). The two problematic plans for llama3.1 in
   run 03 now complete with 3/3 calls.
   Evidence: `history/2/52_identify_potential_levers/events.jsonl` and `outputs.jsonl`.

5. **OPTIMIZE_INSTRUCTIONS updated to document template-lock migration pattern.** The update adds
   explicit guidance that examples must avoid reusable transitional phrases and that replacing one
   copyable opener does not eliminate lock — models shift to copying subphrases in the new examples.
   This is accurate and actionable guidance for future prompt engineers.
   Evidence: `identify_potential_levers.py` lines 69–80: "Template-lock migration. Replacing a
   copyable opener does not eliminate template lock…"

6. **No fabricated % claims in llama3.1 consequences for run 52.** Run 03 gta_game levers 1–6
   contained fabricated % claims in consequences ("by at least 20/15/30%"). Run 52 silo
   consequences are clean: no fabricated numbers detected in sampled levers.
   Evidence: `history/2/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
   — no percentage claims in any consequences field.

---

## Negative Things

1. **llama3.1 parasomnia: "the options" lock persists at ~82%.** Of 17 visible reviews in run 52
   parasomnia, ~14 use "the options" or "the lever" as grammatical subject. Examples:
   "The options overlook the potential impact of increased recruitment targets on participant
   retention rates…", "The lever misses the tension between prioritizing accuracy and minimizing
   bias…", "The lever neglects the potential for compromised participant privacy…"
   This is an improvement from 100% (run 03) but is far from eliminated.
   Evidence: `history/2/52_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`

2. **llama3.1 gta_game: template lock shifted but not reduced — possible slight regression.**
   In run 03, 62.5% of gta_game reviews used "The options [verb]" (10/16). In run 52, gta_game
   reviews show ~78% using "These options…" or "While these options… they overlook/neglect".
   The grammatical pattern is the same (options as subject), just using "these options" instead of
   "the options". The shift from one template to another does not count as progress.
   Evidence: `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   — 7 of first 9 reviews open with "While these options…" or "These options focus on…, but neglect…"

3. **New template pattern in llama3.1 hong_kong_game reviews: "The plan's emphasis on X may overlook Y."**
   While "the options" lock is gone, 8 of 17 hong_kong_game reviews follow the formula
   "The plan's emphasis/focus/reliance on X may overlook Y." This is domain-specific (uses plan-specific
   X values) but is still formulaic repetition of a sentence skeleton. Two reviews are near-identical:
   both "Festival Premiere Strategy" and an earlier entry have essentially the same review text.
   Evidence: `history/2/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`

4. **haiku partial recovery regression.** Run 09 (before, haiku): 5/5 plans with 15/15 calls succeeded.
   Run 58 (after, haiku): silo (2/3 calls) and parasomnia (2/3 calls) had partial recovery events.
   The haiku model is not targeted by this PR; the regression may be non-deterministic but is observable.
   Evidence: `history/2/58_identify_potential_levers/events.jsonl` lines 9, 11 — two `partial_recovery`
   events with `calls_succeeded: 2`.

5. **Template-lock migration to "the lever" pattern in parasomnia second LLM call.** For parasomnia
   (after, run 52), levers from the first LLM call use "The options overlook/neglect…" while levers
   from the second LLM call switch to "The lever misses/overlooks/neglects…" — a different but
   equally repetitive grammatical template. The examples broke "the options" lock only to have
   the model invent a new lever-centric template for subsequent calls.
   Evidence: `history/2/52_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
   levers 7–14 vs levers 1–6.

6. **New examples are domain-biased toward construction/agricultural/insurance contexts.** The three
   new examples (idle-wage burden in farm off-season, Section 106 heritage review, hurricane season
   insurance correlation) are all from real-estate/construction/finance domains. Plans in medical
   research (parasomnia) or video-game (gta_game) domains may not benefit as much from these examples
   because the structural patterns don't map naturally. This likely explains why parasomnia and gta_game
   retain higher template lock rates than silo and hong_kong_game.

7. **llama3.1 silo options field is very short (label-like).** System prompt requires "at least 15 words
   with an action verb" per option. Run 52 silo options include: "Zone-based governance empowers local
   self-sufficiency and specialization" (7 words), "Interconnected ecosystems foster resource sharing
   and collaborative innovation" (8 words). These are label-length, not full strategic approaches.
   This is a pre-existing issue not caused by PR #353, but it persists.
   Evidence: `history/2/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
   lever 1, options field.

---

## Comparison

| Metric | Before (runs 03–09) | After (runs 52–58) | Change |
|--------|--------------------|--------------------|--------|
| **Plan-level success rate** | 34/35 = 97.1% | 35/35 = 100% | **+2.9pp IMPROVED** |
| **Call-level success rate** | 100/105 = 95.2% | 102/105 = 97.1% | **+1.9pp IMPROVED** |
| **LLMChatErrors** | 1 (run 04, gpt-oss-20b, sovereign_identity EOF) | 0 | **IMPROVED** |
| **llama3.1 partial recoveries** | 2 (sovereign_identity 2/3, hong_kong_game 2/3) | 1 (gta_game 2/3) | **IMPROVED** |
| **haiku partial recoveries** | 0 | 2 (silo 2/3, parasomnia 2/3) | **REGRESSION** |
| **llama3.1 "the options" lock — silo** | ~94% (18/19) | 0% (0/21) | **FIXED** |
| **llama3.1 "the options" lock — hong_kong_game** | ~100% (6 exact duplicates + options-centric) | 0% "the options" | **FIXED** |
| **llama3.1 "the options" lock — parasomnia** | 100% (18/18 in run 03) | ~82% (14/17) | **PARTIAL IMPROVEMENT** |
| **llama3.1 "these/the options" lock — gta_game** | 62.5% (10/16 in run 03) | ~78% (7/9 visible) | **SLIGHT REGRESSION** |
| **New secondary lock ("the lever") in parasomnia** | Not present | Present (levers 7–14, 2nd LLM call) | **NEW REGRESSION** |
| **Exact-duplicate review texts (llama3.1, hong_kong_game)** | 6 exact duplicates | 0 | **FIXED** |
| **Fabricated % in consequences (llama3.1)** | 5 (run 03 gta_game levers 1–6) | 0 detected in silo | **IMPROVED** |

---

## Quantitative Metrics

### Template Lock Rate — llama3.1, review field

| Plan | Before (run 03) | After (run 52) | Dominant pattern (after) |
|------|-----------------|----------------|--------------------------|
| silo | ~94% (18/19) | 0% (0/21) | Domain-specific lever subjects |
| hong_kong_game | ~100% (6 dup + options-centric) | 0% (0/17) | "The plan's emphasis on X may overlook Y" (formulaic but domain-specific) |
| parasomnia | 100% (18/18) | ~82% (14/17) | "The options overlook" + "The lever misses" |
| gta_game | 62.5% (10/16) | ~78% (7/9) | "These options…" / "While these options… they overlook/neglect" |
| **Overall estimate** | **~85%** | **~40%** | |

### Plan-Level Outcome Summary

| Run | Model | Plans OK | Plans Error | Partial Recovery |
|-----|-------|----------|-------------|-----------------|
| 03 | llama3.1 | 5 | 0 | 2 plans (2/3 calls each) |
| 52 | llama3.1 | 5 | 0 | 1 plan (2/3 calls) |
| 04 | gpt-oss-20b | 4 | 1 (sovereign_identity, JSON EOF) | 0 |
| 53 | gpt-oss-20b | 5 | 0 | 0 |
| 05 | gpt-5-nano | 5 | 0 | 0 |
| 54 | gpt-5-nano | 5 | 0 | 0 |
| 06 | qwen3-30b | 5 | 0 | 0 |
| 55 | qwen3-30b | 5 | 0 | 0 |
| 07 | gpt-4o-mini | 5 | 0 | 0 |
| 56 | gpt-4o-mini | 5 | 0 | 0 |
| 08 | gemini-flash | 5 | 0 | 0 |
| 57 | gemini-flash | 5 | 0 | 0 |
| 09 | haiku | 5 | 0 | 0 |
| 58 | haiku | 5 | 0 | 2 plans (2/3 calls each) |

### Field Length Comparison (silo plan, sampled)

Baseline averages from analysis 27: avg_conseq=279, avg_review=152, avg_opts=453 (all 3 options combined).

| Field | Baseline avg | Before (03/silo) | Ratio | After (52/silo) | Ratio |
|-------|--------------|-----------------|-------|-----------------|-------|
| consequences | 279 chars | ~155 chars | 0.56× | ~161 chars | 0.58× |
| review | 152 chars | ~171 chars | 1.12× | ~223 chars | 1.47× |
| options (3 combined) | 453 chars | ~300 chars | 0.66× | ~228 chars | 0.50× |

Notes:
- Baseline consequences are longer because they include fabricated "Immediate → Systemic → Strategic"
  chains with percentage claims (which OPTIMIZE_INSTRUCTIONS now prohibits).
- After (52) review fields are 1.47× baseline — within the 2× warning threshold, and the extra length
  is substantive domain-specific content rather than template repetition.
- After (52) options fields are 0.50× baseline — possibly too short for some plans (label-like).

---

## Evidence Notes

- silo template lock before: `history/2/03_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  — first 10 reviews all start with "The options [overlook/fail/assume/neglect/miss]..."
- silo template lock after: `history/2/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  — all 21 reviews start with lever-specific subjects (zero "the options")
- hong_kong_game duplicate reviews before: `history/2/03_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  — identical review text "The plan assumes a clear distinction between the game and reality, but what if
  the lines between them become blurred, or if the protagonist's perception of reality is challenged by the game?"
  appears verbatim 6 times (levers 2–7)
- hong_kong_game after: `history/2/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  — 0 duplicate reviews, 0 "the options" subject
- parasomnia lock after: `history/2/52_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
  — levers 1–6 use "The options overlook/neglect/miss…", levers 7–14 use "The lever misses/overlooks/neglects…"
- gta_game lock after: `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
  — 7 of first 9 reviews use "While these options… they overlook" or "These options focus on…, but neglect…"
- haiku regression: `history/2/58_identify_potential_levers/events.jsonl` — two `partial_recovery` events
  (`silo`: calls_succeeded=2, `parasomnia_research_unit`: calls_succeeded=2)
- gpt-oss-20b error resolved: `history/2/04_identify_potential_levers/outputs.jsonl` sovereign_identity
  status=error vs `history/2/53_identify_potential_levers/outputs.jsonl` all status=ok

---

## OPTIMIZE_INSTRUCTIONS Alignment

The updated `OPTIMIZE_INSTRUCTIONS` (lines 69–80 in `identify_potential_levers.py`) now explicitly
documents "Template-lock migration" as a known problem, stating: "Examples must avoid reusable
transitional phrases that fit any domain. Each example must name a domain-specific mechanism or
constraint directly…"

This is good alignment with the observed failure mode. However:

1. The three new examples are all from construction/agricultural/insurance domains. A proposed
   addition to OPTIMIZE_INSTRUCTIONS: *"Examples must span at least two structurally different
   domains so that model generalization is tested across plan types — e.g., one scientific/research
   example and one financial/commercial example alongside any construction example."* Without this,
   medical and entertainment plan types may continue to see template lock even as construction-type
   plans improve.

2. OPTIMIZE_INSTRUCTIONS does not yet warn about secondary template lock forming from structural
   elements of later LLM calls. Proposed addition: *"When multiple LLM calls are made for the same
   plan, each subsequent call is prompted with already-generated lever names but not the prior reviews.
   Template lock can re-emerge independently in each call and may take a different form (e.g., 'the lever
   overlooks' instead of 'the options overlook'). Examples should model call-independent diversity."*

3. The "Options too short / label-like" problem (llama3.1 silo, run 52, options averaging ~76 chars
   or ~7 words) is not addressed in OPTIMIZE_INSTRUCTIONS. The system prompt says ">15 words with an
   action verb" but the validator does not enforce this. Proposed addition: *"Short option labels (under
   10 words) are a known failure mode for smaller models. The system prompt states 15-word minimum but
   this is not validated structurally — consider adding a min-length check."*

---

## Hypotheses

**Prompt hypotheses:**

H1: The three new examples are all from the same broadly construction/finance/agriculture sector.
Adding one medical/scientific example and one technology/software example to the set would provide
a more domain-diverse signal and reduce the observed domain-specificity gap for parasomnia and
gta_game plans.
Expected effect: Reduce template lock rate for parasomnia and gta_game from ~80% to <50%.

H2: The parasomnia "the lever misses/overlooks" secondary lock is forming in the second LLM call
because the system prompt's example section (4 examples) is identical for all calls. Adding a
call-specific instruction like "In your reviews, avoid starting with 'The options' or 'The lever' —
instead name the specific mechanism, constraint, or assumption that is at risk" could break this.
Expected effect: Reduce second-call template lock (which currently runs ~90% "the lever" pattern).

H3: The "The plan's emphasis on X may overlook Y" pattern seen in hong_kong_game (run 52) is a
new secondary template lock. It's better than the previous "the options" lock because X is
domain-specific, but it's still a reusable sentence skeleton. Adding a prohibition in the system
prompt ("Do not use 'The plan's emphasis on X may overlook Y' or 'The plan assumes X' as your
review opener") could diversify further.
Expected effect: Small improvement for film/entertainment plans.

**Code hypotheses:**

C1: The `check_review_format` validator enforces only minimum length (10 chars) and no brackets.
Adding a soft warning (logged, not raised) when `review_lever` starts with "the options" or
"these options" would quantify lock rate in production runs without causing validation failures.
This would make the lock problem observable without affecting success rate.

C2: The options field under-length issue (silo, run 52: ~7-word options) is not caught by any
validator. Adding a soft check (`min(len(opt.split()) for opt in options) < 10 → log warning`)
would surface this without breaking output. A future iteration could raise if all 3 options are
under 10 words.

---

## Questions For Later Synthesis

1. Why did silo improve dramatically (0% lock) while parasomnia and gta_game did not? Is it the
   domain mismatch with the construction/insurance examples, or is it something about the silo
   plan context that naturally produces domain-specific lever names?

2. The haiku partial recovery regression (0 → 2 plans with 2/3 calls) is unexplained. Is this
   non-deterministic network behavior, or did the new examples change haiku's output length and
   trigger length-based truncation?

3. Should the example replacement strategy be extended to include examples from a medical/scientific
   domain and a technology/software domain, or is there a different intervention (e.g., an explicit
   negative example or a per-call system prompt modifier)?

4. The gpt-oss-20b sovereign_identity failure in run 04 resolved in run 53. Was this non-deterministic
   (network/timeout), or did the new examples reduce output length enough to prevent JSON truncation?

---

## Reflect

The PR targets a real and well-understood failure mode (template lock via "the options" as grammatical
subject). The mechanism (replacing options-centric examples with domain-specific mechanism examples)
is theoretically sound and supported by the OPTIMIZE_INSTRUCTIONS update.

The results are real but asymmetric: silo and hong_kong plans show dramatic improvement, while
parasomnia and gta_game show either no improvement or slight regression in template lock rate.
The root cause is likely the domain bias of the three new examples (all construction/agriculture/
insurance) combined with the inherent tendency of smaller models (llama3.1) to find and copy
structural patterns across any example set.

The overall verdict is cautiously positive: success rate improved, the worst single-plan issue
(hong_kong_game exact-duplicate reviews) is fixed, and the overall template lock rate halved for
llama3.1 (~85% → ~40%). However, the problem is not solved, and further work is needed to address
parasomnia and gta_game lock patterns.

---

## PR Impact

### What the PR was supposed to fix

PR #353 targeted the root cause identified in analysis 28: "the options" as grammatical subject in
all three `review_lever` examples caused llama3.1 to reproduce the "The options [verb]" opener in
~94% of review fields. The fix replaced all three examples with domain-specific mechanism sentences
that name concrete constraints rather than "the options."

### Before vs. After Comparison

| Metric | Before (runs 03–09) | After (runs 52–58) | Change |
|--------|--------------------|--------------------|--------|
| Plan success rate | 34/35 = 97.1% | 35/35 = 100% | +2.9pp |
| LLMChatErrors | 1 | 0 | -1 |
| llama3.1 partial recoveries | 2 | 1 | -1 |
| haiku partial recoveries | 0 | 2 | +2 |
| llama3.1 silo "the options" lock | 94% | 0% | -94pp |
| llama3.1 hong_kong exact-duplicate reviews | 6 | 0 | FIXED |
| llama3.1 parasomnia "options/lever" lock | 100% | ~82% | -18pp |
| llama3.1 gta_game "options/lever" lock | 62.5% | ~78% | +15.5pp |
| Overall llama3.1 template lock (est.) | ~85% | ~40% | -45pp |

### Did the PR fix the targeted issue?

**Partially.** The PR fixed silo and hong_kong_game (the two plans with highest lock rate before:
94% and near-100%). However, parasomnia and gta_game still show significant template lock using
"these options" and "the lever" variants. The lock pattern migrated rather than disappearing
completely. This matches the template-lock migration warning now documented in OPTIMIZE_INSTRUCTIONS.

### Regressions

1. haiku partial recoveries increased (0 → 2). This may be non-deterministic but is observable.
2. gta_game lock rate increased slightly (62.5% → ~78%) with a pattern shift.
3. A new "the lever" secondary lock appeared in parasomnia second LLM call reviews.

### Verdict

**KEEP** — The PR produces real, measurable improvement for the two most severely affected plans
(silo: 94% → 0% lock; hong_kong: near-complete fix). Overall template lock rate for llama3.1 halved.
Plan success rate improved. The OPTIMIZE_INSTRUCTIONS update accurately documents the remaining failure
mode (template-lock migration). Further work is needed on parasomnia and gta_game (H1 and H2 above),
but the direction is correct and the PR does not introduce significant regressions.

---

## Summary

PR #353 replaced all three `review_lever` examples with domain-specific mechanism sentences to
eliminate "the options" as grammatical subject. The outcome is a partial but meaningful success:

- **Fully fixed**: silo (94% → 0% "the options" lock), hong_kong (exact-duplicate reviews eliminated)
- **Partially fixed**: parasomnia (100% → ~82% "options/lever" lock)
- **Slight regression**: gta_game (62.5% → ~78% "these options" lock)
- **Overall llama3.1 template lock**: ~85% → ~40% (significant halving)
- **Plan success rate**: 97.1% → 100% (gpt-oss-20b sovereign_identity error resolved)

The key remaining issue is domain bias: the new examples (construction/agriculture/insurance) work
well for construction-adjacent plans (silo, hong_kong) but don't break lock for medical research
(parasomnia) or video-game (gta_game) plans. The recommended next step is H1: add one scientific
and one technology example to complement the existing construction/finance examples.
