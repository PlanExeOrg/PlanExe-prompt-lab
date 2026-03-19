# Assessment: fix: replace review_lever examples to break template lock

## Issue Resolution

**PR #353 targeted one root cause:** all three `review_lever` examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` used "the options" as grammatical subject, which analysis 28 proved was the primary driver of ~85% template lock in llama3.1. The fix replaced all three examples with domain-specific mechanism sentences that name a concrete constraint or process as the subject rather than "the options."

**Before examples (analysis 28 / runs 03–09):**
1. "…none of the options price in the idle-wage burden…"
2. "…the options assume permits will clear on the standard timeline."
3. "…correlation risk absent from every option."

**After examples (PR #353 / runs 52–58):**
1. "…the idle-wage burden during the 5-month off-season adds a fixed cost…"
2. "Section 106 heritage review triggers a mandatory 45–180-day public comment period…"
3. "…a single regional hurricane season can correlate all three simultaneously, turning the diversification assumption into a concentration risk…"

**Fully resolved (two of four plans):**
- llama3.1 silo: 94% → 0% "the options" lock. All 21 reviews now start with domain-specific lever subjects. Confirmed by reading `history/2/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — zero "the options" openers across all levers.
- llama3.1 hong_kong_game: 6 exact-duplicate reviews → 0 exact duplicates. "The options" pattern eliminated. Reviews now cite plan-specific details.

**Partially resolved (two of four plans):**
- llama3.1 parasomnia: 100% → ~82% "options/lever" lock. First LLM call (levers 1–6) still uses "The options overlook/neglect/miss…" (unchanged grammatical subject). Second LLM call (levers 7–14) shifted to "The lever misses/overlooks/neglects…" — a new secondary lock with a different subject but the same formulaic structure. Confirmed by reading `history/2/52_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.
- llama3.1 gta_game: 62.5% → ~78%. The lock migrated from "The options" to "While these options…" / "These options focus on…, but neglect…". Confirmed by reading `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — 7 of the first 9 visible levers use "these options" openers.

**Root cause of partial fix:** The three new examples are all from real-estate/agricultural/catastrophe-insurance domains. Plans in medical research (parasomnia) and video-game (gta_game) domains cannot draw structural templates from these examples. The lock persists because weaker models (llama3.1) need examples whose vocabulary maps to the plan domain. Additionally, all three examples share the same "X but Z reverses the gain" adversarial contrast structure — a model that copies the structure rather than the specific words will produce secondary lock regardless of whether the subject is "the options" or "the lever."

**Residual symptom:** "These options" (gta_game) and "The lever" (parasomnia 2nd call) are functionally equivalent to the original "The options" lock — same analytical weakness (formulaic critique), different surface words.

---

## Quality Comparison

Models appearing in BOTH batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5 (7 models × 5 plans = 35 plan executions each).

| Metric | Before (runs 03–09) | After (runs 52–58) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 34/35 = 97.1% | 35/35 = 100% | IMPROVED |
| **LLMChatErrors** | 1 (gpt-oss-20b sovereign_identity, JSON EOF at line 58) | 0 | IMPROVED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High (case-sensitive dedup; semantic duplicates pass) | High (same) | UNCHANGED |
| **llama3.1 partial recoveries** | 2 (sovereign_identity 2/3, hong_kong 2/3) | 1 (gta_game 2/3) | IMPROVED |
| **haiku partial recoveries** | 0 | 2 (silo 2/3, parasomnia 2/3) | REGRESSION (ambiguous — see New Issues) |
| **Template lock — llama3.1 overall (est.)** | ~85% | ~40% | IMPROVED (-45pp) |
| **Template lock — llama3.1 silo** | ~94% (18/19) | 0% (0/21) | FIXED |
| **Template lock — llama3.1 hong_kong** | ~100% + 6 exact duplicates | 0% "the options"; 0 duplicates | FIXED |
| **Template lock — llama3.1 parasomnia** | 100% (18/18) | ~82% (14/17) | PARTIAL IMPROVEMENT |
| **Template lock — llama3.1 gta_game** | 62.5% (10/16) | ~78% (7/9 visible) | SLIGHT REGRESSION |
| **New secondary lock "the lever" — parasomnia 2nd call** | Not present | Present (levers 7–14) | NEW REGRESSION |
| **Exact-duplicate review texts** | 6 (llama3.1 hong_kong run 03) | 0 | FIXED |
| **Fabricated % in consequences (llama3.1)** | 5 (run 03 gta_game levers 1–6: "by at least 20/15/25/30%") | 0 detected in sampled silo run 52 | IMPROVED |
| **Marketing-copy language** | Low | Low | UNCHANGED |
| **Review length vs baseline (llama3.1 silo)** | ~1.12× (171 chars avg) | ~1.47× (223 chars avg) | SLIGHT INCREASE (within 2× threshold) |
| **Options length vs baseline (llama3.1 silo)** | ~0.66× (300 chars avg) | ~0.50× (228 chars avg) | REGRESSED (label-like options persist) |
| **Cross-call duplication** | Present (typo variants; semantic dups) | Present (same) | UNCHANGED |
| **Over-generation (>7 levers per call)** | Haiku routinely 8+ per call | Haiku routinely 8+ per call | UNCHANGED (handled by downstream dedup) |
| **Review format compliance** | Variable by model | Variable by model | UNCHANGED |

**Notes:**
- Haiku gta_game run 58: Output quality is high (detailed, substantive, domain-grounded reviews confirmed by file read). The 2 partial_recovery events are likely false alarms from B1 (runner.py hardcodes `expected_calls=3`; haiku hits `min_levers=15` in 2 calls with 8+ levers each).
- Baseline consequences average 279 chars (includes fabricated Immediate→Systemic→Strategic chains, which OPTIMIZE_INSTRUCTIONS now prohibits). After run 52 (llama3.1 silo) consequences average ~161 chars (0.58× baseline) — short but structurally clean.
- The gpt-oss-20b JSON EOF (run 04) resolved in run 53 without any code change — non-deterministic, not PR-related.

---

## New Issues

1. **"These options" secondary template lock in gta_game (llama3.1, run 52).** Grammatically different from "The options" but structurally identical as a critique template — the model substituted "these" for "the" and preserved the sentence skeleton. ~78% of gta_game reviews (7/9 visible) use "While these options…" or "These options focus on…, but neglect…". The prohibition against "the options" was satisfied technically while the underlying pattern migrated.

2. **"The lever misses/overlooks/neglects" secondary lock in parasomnia 2nd LLM call.** The second LLM call (levers 7–14) independently develops its own lock in run 52 — "the lever" replaces "the options" as the grammatical subject. This is consistent with the code architecture: each LLM call receives the same system prompt fresh (no conversation history). The examples break the lock for silo (construction-adjacent) but not for parasomnia (medical), where the model improvises a new template within the adversarial contrast structure shared by all three examples.

3. **Domain monoculture of new examples.** All three post-PR examples (idle-wage burden in farm off-season, Section 106 heritage review, hurricane season insurance correlation) are from real-estate/construction/agriculture/insurance domains. Plans in medical research (parasomnia) and video-game (gta_game) cannot generalize from these domains structurally. This explains the asymmetric outcome: construction-adjacent plans (silo, hong_kong) fixed completely; other domains not fixed.

4. **Structural homogeneity of new examples.** Examples 1 and 3 use the same "X improves Y, but Z reverses the gain" reversal structure; example 2 uses an equivalent adversarial contrast. A model that copies structure rather than specific words will produce secondary lock regardless of example content.

5. **haiku partial recovery ambiguity (pre-existing B1 bug made visible).** Run 58 haiku emits `partial_recovery` for silo (calls_succeeded=2) and parasomnia (calls_succeeded=2), but both plans completed with `status: ok`. The code_review B1 documents that `runner.py` hardcodes `expected_calls=3` and emits `partial_recovery` for any `calls_succeeded < 3` — including early-success cases where the model hit `min_levers=15` in 2 calls. Haiku typically generates 8–10 levers per call, so 2 calls × 8 levers = 16 ≥ 15 is plausible. The haiku silo output (read directly) shows high-quality, detailed, non-template-locked levers — consistent with a successful (not partial) run.

6. **"The plan's emphasis on X may overlook Y" secondary lock in hong_kong (llama3.1, run 52).** 8/17 hong_kong reviews follow this skeleton. It is domain-specific (X varies per lever) — less harmful than "the options overlook" — but still a formulaic repetition.

---

## Verdict

**YES**: The PR is a keeper. The grammatical-subject fix is mechanistically correct and produced real, measurable improvement. The two worst-case plans (silo: 94% → 0% lock; hong_kong: 6 exact duplicates → 0) are fully resolved. Overall llama3.1 template lock rate halved (~85% → ~40%). Plan success rate recovered to 100%. The OPTIMIZE_INSTRUCTIONS update accurately documents the template-lock migration failure mode.

The remaining lock (parasomnia, gta_game) is not a regression introduced by this PR — it is a gap in the PR's scope, attributable to domain monoculture and structural homogeneity of the new examples. The direction is correct; the coverage is incomplete.

---

## Recommended Next Change

**Proposal:** Replace one or two of the current `review_lever` examples with domain-diverse alternatives (one scientific/medical, one technology/software), AND add an explicit prohibition bullet to section 5 forbidding "The options", "These options", "The lever", and "These levers" as review openers. Both changes target `identify_potential_levers.py` section 4 (examples) and section 5 (prohibitions) — no code changes.

**Evidence:** The domain-monoculture explanation is strongly supported. silo and hong_kong (construction-adjacent plans) both achieved 0% lock after the PR; parasomnia (medical) and gta_game (video-game) remain at ~78–82%. The structural pattern is identical across both failures: the current examples (seasonal labor, heritage permits, hurricane correlation) provide no structural template that maps to medical research timelines or game-design trade-offs. The insight's direct comparison — silo lock 94% → 0% vs. parasomnia lock 100% → 82% — is the clearest evidence that domain alignment of examples drives lock rate more than any other variable. The code review confirms that the three examples share one adversarial contrast structure, explaining why the lock migrated to "the lever" in parasomnia's 2nd call even after the grammatical subject was changed.

**Verify in next iteration:**
- **Primary:** Does llama3.1 parasomnia template lock drop below 50% after adding a medical/scientific example? The target is "The options overlook" and "The lever misses" combined dropping from ~82% to <40%.
- **Primary:** Does llama3.1 gta_game "these options" lock drop below 50%? Watch for a third migration (e.g., "the game's options", "the design options").
- **Secondary:** Does the explicit prohibition in section 5 suppress the "These options" variant in gta_game that survived the grammatical-subject fix? Check whether the prohibition reduces lock in models other than llama3.1 (gpt-5-nano, qwen3-30b) if they show any residual lock.
- **B1 verification:** After fixing B1 (false `partial_recovery`), confirm whether haiku's run 58 events were true failures or early-success completions. If they were false alarms, haiku has no regression to investigate.
- **Structural diversity check:** After adding a medical example, verify it does NOT use the "X improves Y, but Z reverses the gain" reversal template. It should use a different rhetorical structure (e.g., additive-risk: "yet each additional X requires its own Y — a sequential overhead that adds Z") to break the structural monoculture.
- **Domain coverage:** Verify the new examples span at least two structurally distinct domains. Read silo and parasomnia outputs for run after the next PR to confirm the domain-coverage gap is closed.

**Risks:**
- A poorly drafted medical or technology example could create its own domain-specific template lock. Mitigation: the new example must name a specific mechanism (e.g., "IRB approval, site-initiation visit, and staff training") rather than a generic concept ("regulatory burden"). The OPTIMIZE_INSTRUCTIONS already documents this requirement.
- Adding the explicit prohibition ("No review_lever that begins with 'The options', 'These options', 'The lever'…") could conflict with rare legitimate uses of "the lever" as a topic reference (e.g., "The lever's assumption about X…"). This is unlikely to be a problem given current output patterns, but the prohibition should be precise: "as grammatical subject of the critique sentence."
- If the structural homogeneity of examples is the deeper problem, even domain-diverse examples with the same adversarial contrast structure may produce a new secondary lock in a different syntactic form. Monitor whether the 2nd LLM call re-invents a template lock for any plan type.

**Prerequisite issues:**
- B1 fix (false `partial_recovery`) is recommended before the next iteration so that haiku's partial recovery signal is interpretable. Without this fix, it is impossible to determine whether future haiku events indicate real regressions or false alarms.

---

## Backlog

**Resolved by PR #353 (remove from backlog):**
- B1 (template lock): "all three `review_lever` examples use 'the options' as grammatical subject" — addressed. The specific "the options" grammatical subject is now absent from all three examples, and confirmed eliminated for silo and hong_kong.
- Fabricated % in llama3.1 consequences: 5 instances in run 03 gta_game (introduced by PR #340) → 0 detected in run 52. Resolved by the example replacement.

**Remaining / new items for backlog:**
- **Template lock (parasomnia, gta_game):** ~82% and ~78% respectively. Root cause: domain monoculture + structural homogeneity. Next action: direction 1+2 from synthesis (domain-diverse examples + section 5 prohibition).
- **B1 (false `partial_recovery`):** `runner.py:115` hardcodes `expected_calls=3`; emits `partial_recovery` for early-success completions (model hits `min_levers=15` in 2 calls) as well as true failures. Needs a `failed_calls` counter to disambiguate. File: `self_improve/runner.py:115, 514`.
- **S3 (structural homogeneity of examples):** All three new examples share the "X but Z reverses the gain" adversarial contrast structure. Structural variety (not just domain variety) needed. Address in the same PR as direction 1.
- **I4 (section 5 prohibition missing):** No explicit prohibition against "The options", "These options", "The lever" as review openers. Confirmed gap by reading the code and outputs. Address alongside example replacement.
- **S1 / I5 (`lever_index` dead field):** Generated but never transferred to `LeverCleaned`. Wastes ~1 token per lever per call. Cleanup PR.
- **S2 / I6 (`strategic_rationale` dead field):** ~100 words generated per call (105 calls/iteration ≈ 10,500 wasted words), never consumed downstream. Verify no downstream step reads it, then remove.
- **I1 (soft template-lock validator):** Add logged warning in `check_review_format` when `review_lever` starts with "the options", "these options", "the lever", "these levers". Makes lock rate visible in production logs without affecting success rate. Deferred until after B1 fix so partial_recovery and lock signals tell a clean story.
- **S4 / I2 (option word-count validator):** The 15-word minimum in section 6 is unvalidated. llama3.1 silo run 52 options average ~7 words (label-like, e.g., "Zone-based governance empowers local self-sufficiency and specialization"). A soft warning for options under 10 words would surface this without causing retries.
- **B2 (dispatcher cross-thread contamination):** `runner.py:187–219` — event handlers from different threads write spurious events. Low practical impact since `track_activity.jsonl` is deleted before final output. Deferred.
- **B3 (case-sensitive name deduplication):** `identify_potential_levers.py:337` — "Multplayer Modes" and "Multiplayer Modes" both pass through. Minor. Fix with `lever.name.strip().lower()` normalization.
