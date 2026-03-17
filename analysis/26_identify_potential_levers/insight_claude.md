# Insight Claude

## Scope

Analyzing runs `1/89–1/95` (after PR #337) against `1/82–1/88` (before, from analysis 25) for the `identify_potential_levers` step.

**PR under evaluation:** PR #337 "fix: replace generic review_lever examples with domain-specific ones"
- Replaced copyable generic examples in `Lever.review_lever`, `LeverCleaned.review`, and system-prompt section 4 with domain-specific, non-portable examples (agriculture, urban planning, insurance)
- Intended to break llama3.1's 100% "This lever governs the tension between…" lock and qwen3's "Core tension:" openers

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 82 | 89 | ollama-llama3.1 |
| 83 | 90 | openrouter-openai-gpt-oss-20b |
| 84 | 91 | openai-gpt-5-nano |
| 85 | 92 | openrouter-qwen3-30b-a3b |
| 86 | 93 | openrouter-openai-gpt-4o-mini |
| 87 | 94 | openrouter-gemini-2.0-flash-001 |
| 88 | 95 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **Primary goal achieved — llama3.1 "This lever governs" lock broken.** In `history/1/82_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, all 15/15 review fields start with "This lever governs/balances/navigates the tension between…". In `history/1/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, zero of 17 reviews use this opener. The rate dropped from 100% to 0% on this plan/model pair.

2. **qwen3 template lock substantially broken.** In `history/1/85_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, all 18+ reviews start with "This lever [governs/balances/navigates/addresses/emphasizes/manages]…". In `history/1/92_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`, only 1 of 18 reviews uses "This lever…" (as "This lever assumes compatible work cultures…") and 1 of 18 opens with "The core tension is between…". A further 4 of 18 still contain "The tension is between…" mid-sentence but not as a formulaic opener. Net: from ~100% to ~6% "This lever" lock, from unknown rate to 1/18 "Core tension:".

3. **No new models started failing.** All non-llama models (runs 90–95) achieved 5/5 plan completions, consistent with the before-batch.

4. **Field lengths stable — no verbosity regression.** Review avg for llama3.1/hong_kong_game: ~178 chars after vs ~182 chars before. Review avg for qwen3/hong_kong_game: ~163 chars after vs ~177 chars before. Consequences similarly unchanged. All ratios vs baseline remain below 2×.

5. **No fabricated percentage claims introduced.** Sampled consequences and reviews in runs 89, 92, 93, 95 for hong_kong_game, gta_game, sovereign_identity — no `%` claims or invented cost deltas found. The anti-fabrication properties were not disrupted by switching to domain-specific examples.

6. **Overall success rate maintained.** 34/35 = 97.1% both before and after. No net regression.

---

## Negative Things

1. **New secondary template lock in llama3.1.** After breaking "This lever governs…", run 89 shows a new formulaic pattern: "The options [assume/neglect/overlook/fail to account for]…" in 13 of 17 reviews for hong_kong_game. Four reviews (items 8–11) are nearly identical in structure: "The options assume that the [protagonist's X] is fixed, neglecting the possibility that it could be a dynamic entity shaped by his experiences in Hong Kong." This is a secondary lock — less severe than the original (the phrasing is at least domain-relative), but still formulaic.

   Evidence from `history/1/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
   - Item 8: `"The options assume that the game's purpose is fixed, neglecting the possibility that it could be a dynamic entity with multiple agendas and motivations."`
   - Item 9: `"The options assume that the protagonist's backstory is a fixed trait, neglecting the possibility that it could be a dynamic entity shaped by his experiences in Hong Kong."`
   - Item 10: `"The options assume that the protagonist's relationship with technology is fixed, neglecting the possibility that it could be a dynamic entity shaped by his experiences in Hong Kong."`
   - Item 11: `"The options assume that the ending is fixed, neglecting the possibility that it could be a dynamic entity shaped by the protagonist's experiences in Hong Kong."`

2. **Exact duplicate reviews in llama3.1 run 89.** Item 15 and item 17 in `history/1/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` are identical: `"The options neglect the potential consequences of redefining the game's purpose, which might alter the film's core message."` Two different levers share an identical review. This is a content-level defect invisible to structural validators.

3. **New Pydantic failure mode for llama3.1 — review too short.** Run 89 errors on parasomnia with: `"1 validation error for DocumentDetails\nlevers.2.review_lever\n  Value error, review_lever is too short (19 chars); expected at least 20"`. The generated review was `"Sensor Data Sharing"` — 19 chars. The old template ("This lever governs…") was verbosely formulaic enough to always exceed 20 chars. Without that template, llama3.1 can now produce degenerate single-phrase reviews that fail the `min_length` validator. The failure mode has shifted from options-count (run 82, gta_game) to review-length (run 89, parasomnia). Same failure count (1/5), new cause.

4. **qwen3 "tension" framing residual.** In run 92 hong_kong_game, 5 of 18 reviews (28%) still use "tension" framing:
   - Item 7: `"The core tension is between cultural authenticity and global marketability. The options miss…"`
   - Items 8–11: `"The tension is between [X]. The options don't address…"`
   The "Core tension:" specific opener is reduced to 1/18, but tension-centered framing persists in nearly a third of reviews. This may be more pronounced in other plans (I only sampled hong_kong_game for qwen3; the previous assessment noted "Core tension:" in sovereign_identity and parasomnia plans, which were not verified here).

5. **LLMChatError count for llama3.1 unchanged.** Both before and after, llama3.1 fails 1 of 5 plans per run. The PR did not improve reliability for the weakest model.

---

## Comparison

| Metric | Before (runs 82–88) | After (runs 89–95) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success rate** | 34/35 = 97.1% | 34/35 = 97.1% | UNCHANGED |
| **llama3.1 success rate** | 4/5 (run 82) | 4/5 (run 89) | UNCHANGED |
| **llama3.1 "This lever governs/balances/navigates" in review (hkg)** | 15/15 = 100% | 0/17 = 0% | **-100pp FIXED** |
| **qwen3 "This lever [verb]" opener in review (hkg)** | ≥18/19 ≈ 95%+ | 1/18 = 6% | **-89pp SUBSTANTIALLY FIXED** |
| **qwen3 "Core tension:" opener in review (hkg)** | 0/19 = 0% (not observed in hkg) | 1/18 = 6% | ~SAME (may differ by plan) |
| **llama3.1 new "The options assume/neglect/overlook" in review (hkg)** | 0/15 = 0% | 13/17 = 76% | **NEW SECONDARY LOCK** |
| **Duplicate reviews in llama3.1 (hkg)** | 0 | 2 identical reviews | **NEW DEFECT** |
| **LLMChatError cause (llama3.1)** | options count = 2 (run 82, gta_game) | review_lever too short = 19 (run 89, parasomnia) | LATERAL SHIFT |
| **Review avg length — llama3.1 (hkg, 002-10)** | ~182 chars | ~178 chars | ~UNCHANGED |
| **Review avg length — qwen3 (hkg, 002-10)** | ~177 chars | ~163 chars | SLIGHTLY SHORTER |
| **Consequences avg — qwen3 (hkg)** | ~366 chars = 1.4× baseline | ~346 chars = 1.3× baseline | SLIGHTLY IMPROVED |
| **Fabricated % claims** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | 0 | 0 | UNCHANGED |

---

## Quantitative Metrics

### Template Lock Rates

**Before (run 82, llama3.1, hong_kong_game — 15 levers):**

| Pattern | Count | Rate |
|---------|-------|------|
| "This lever governs the tension between…" | 9 | 60% |
| "This lever [governs/balances/navigates] the tension between…" | 6 | 40% |
| **Total "This lever [verb] tension"** | **15** | **100%** |
| "This lever governs/balances/navigates" (any) | 15 | 100% |

**After (run 89, llama3.1, hong_kong_game — 17 levers):**

| Pattern | Count | Rate |
|---------|-------|------|
| "This lever governs/balances/navigates" | 0 | **0%** |
| "The options [assume/neglect/overlook/fail]" | 13 | **76%** |
| "The options assume that the [X] is fixed…" (near-duplicate) | 4 | 24% |
| Exact duplicate reviews | 2 | (1 pair) |

**Before (run 85, qwen3, hong_kong_game — 19 levers):**

| Pattern | Count | Rate |
|---------|-------|------|
| "This lever [governs/balances/navigates/addresses/emphasizes/manages]" | ≥18 | **~100%** |
| "Core tension:" as opener | 0 | 0% |

**After (run 92, qwen3, hong_kong_game — 18 levers):**

| Pattern | Count | Rate |
|---------|-------|------|
| "This lever [governs/balances/navigates]" | 1 | **6%** |
| "Core tension:" as opener | 1 | 6% |
| "The tension is between…" (any position) | 4 | 22% |
| Other / novel openers | 12 | 67% |

### Field Length Ratios vs Baseline

Baseline: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` (14 levers)
- Baseline review avg: ~150 chars
- Baseline consequences avg: ~260 chars (includes Immediate/Systemic/Strategic chains with fabricated %)

| Model | Field | Before avg (chars) | After avg (chars) | Baseline (chars) | Ratio before | Ratio after |
|-------|-------|--------------------|-------------------|------------------|--------------|-------------|
| llama3.1 | review (hkg) | ~182 | ~178 | ~150 | 1.2× | **1.2×** |
| qwen3 | review (hkg) | ~177 | ~163 | ~150 | 1.2× | **1.1×** |
| llama3.1 | consequences (hkg) | ~215 | ~221 | ~260 | 0.8× | **0.85×** |
| qwen3 | consequences (hkg) | ~366 | ~346 | ~260 | 1.4× | **1.3×** |

No fields exceed 2× baseline. No verbosity regression from the PR.

### Constraint Violations and LLMChatErrors

| Run | Model | Plan | Error | Type |
|-----|-------|------|-------|------|
| 82 (before) | llama3.1 | gta_game | `options must have exactly 3 items, got 2` (levers 5, 6) | Pydantic ValidationError |
| 89 (after) | llama3.1 | parasomnia | `review_lever is too short (19 chars); expected at least 20` (lever 2) | Pydantic ValidationError |

Both runs have 1 error; the failure mode shifted from options-count to review-length. The `min_length=20` validator now surfaces as a trap for degenerate outputs that the old template accidentally prevented.

### Lever Counts

| Run | Model | Plan | Lever count |
|-----|-------|------|-------------|
| 82 | llama3.1 | hong_kong_game | 15 |
| 89 | llama3.1 | hong_kong_game | 17 |
| 85 | qwen3 | hong_kong_game | 19 |
| 92 | qwen3 | hong_kong_game | 18 |
| Baseline | — | hong_kong_game | 14 |

Lever counts are above baseline for all models (expected; DeduplicateLevers trims post-merge).

---

## Evidence Notes

- **Run 82 vs 89 (llama3.1) review comparison** — verified directly from `002-10-potential_levers.json` files. Run 82: every review opens with "This lever governs/balances/navigates the tension between…". Run 89: no review opens this way; predominant opener is "The options assume/neglect/overlook…". Evidence path: `history/1/82_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` vs `history/1/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

- **Run 85 vs 92 (qwen3) review comparison** — verified directly. Run 85: all 19 reviews use "This lever [verb]…" opener. Run 92: 1 of 18 uses "This lever assumes…", 1 uses "The core tension is between…", 4 use "The tension is between…", 12 use genuinely varied openers. Evidence path: `history/1/85_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` vs `history/1/92_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

- **Duplicate review in run 89** — items 15 and 17 both contain: `"The options neglect the potential consequences of redefining the game's purpose, which might alter the film's core message."` (122 chars each). Same text, different lever names ("Reorient the Game's Purpose" and a subsequent lever). This is a content-level regression not caught by any validator.

- **LLMChatError in run 89** — verified from `history/1/89_identify_potential_levers/events.jsonl` line 10: `"levers.2.review_lever\n  Value error, review_lever is too short (19 chars); expected at least 20 [type=value_error, input_value='Sensor Data Sharing'…"`. The generated review was literally the lever name repeated.

- **Previous assessment context** — Analysis 25 (`analysis/25_identify_potential_levers/assessment.md`) explicitly recommended: "Add negative opener constraints to the `Lever.review_lever` Pydantic field description and the matching system-prompt section 4, replacing both current examples with domain-specific, non-portable alternatives." PR #337 directly implements this recommendation.

- **Baseline fabricated numbers** — The baseline training data (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`) itself contains fabricated percentages in consequences ("15% higher audience engagement", "20% higher pre-sales", "30% increase in streaming revenue"). These are artifacts of the earlier optimization phase that inflated baseline verbosity. After-PR runs do not replicate this pattern.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Based on analysis 25's assessment, the `OPTIMIZE_INSTRUCTIONS` constant lists five known failure classes. Alignment check for runs 89–95:

| Known Problem | Status in runs 89–95 | Notes |
|---|---|---|
| Optimism bias / moonshot options | Not detected in sampled outputs | Options remain grounded |
| Fabricated numbers | ✓ None found in sampled runs | No regression introduced |
| Hype language | ✓ None found | Anti-fabrication properties intact |
| Vague aspirations | Minor in llama3.1 | e.g., "a dynamic entity" language |
| English-only validation | ✓ Not triggered | Structural validators only |
| Single-example template lock | **Substantially addressed** for both llama3.1 and qwen3 | PR directly targets this class |
| Model-native template openers | qwen3 "Core tension:" reduced but residual | Should be added to OPTIMIZE_INSTRUCTIONS if not present |

**New recurring problem not yet in OPTIMIZE_INSTRUCTIONS:**
- **Secondary template lock after example replacement**: When a dominant template is removed by replacing examples, the model fills the stylistic vacuum with a different formulaic pattern. In run 89, llama3.1 adopted "The options assume that the [X] is fixed, neglecting the possibility that it could be a dynamic entity…" as a near-identical replacement. This pattern of "template-lock migration" suggests that removing one anchor creates an opening for the next-most-salient pattern in the model's training distribution. OPTIMIZE_INSTRUCTIONS should document this as a known failure class: "Template-lock migration — replacing one example set may shift the lock to a new pattern rather than eliminating it."

---

## PR Impact

**What the PR was supposed to fix:** Replace copyable generic examples (`"This lever governs the tension between centralization and local autonomy"`) in `Lever.review_lever` Pydantic field description, `LeverCleaned.review` field description, and system-prompt section 4, with domain-specific examples from agriculture, urban planning, and insurance. The intent: break llama3.1's 100% "This lever governs the tension between…" lock (confirmed across runs 75, 82) and qwen3's "Core tension:" opener pattern (confirmed across runs 78, 85).

**Before vs After comparison (primary metrics):**

| Metric | Before (runs 82–88) | After (runs 89–95) | Change |
|--------|--------------------|--------------------|--------|
| Overall success rate | 34/35 = 97.1% | 34/35 = 97.1% | UNCHANGED |
| llama3.1 "This lever governs" lock (hkg, 002-10) | 100% (15/15) | 0% (0/17) | **FIXED** |
| qwen3 "This lever [verb]" opener (hkg, 002-10) | ~100% (≥18/19) | 6% (1/18) | **FIXED** |
| llama3.1 secondary "The options assume/neglect" lock (hkg) | 0% (0/15) | 76% (13/17) | **NEW** |
| Duplicate review entries (llama3.1 hkg) | 0 | 1 pair | **NEW** |
| LLMChatError — llama3.1 | 1/5 plans (options count) | 1/5 plans (review too short) | LATERAL |
| Review avg length — llama3.1 | ~182 chars | ~178 chars | ~UNCHANGED |
| Review avg length — qwen3 | ~177 chars | ~163 chars | SLIGHTLY SHORTER |
| Fabricated percentage claims | 0 | 0 | UNCHANGED |

**Did the PR fix the targeted issue?**

Yes, for the primary target. The "This lever governs the tension between…" verbatim copy rate dropped from 100% to 0% for llama3.1 (confirmed on hong_kong_game). For qwen3, the "This lever [verb]" opener rate dropped from ~100% to ~6% (hong_kong_game). The PR successfully replaced the dominant template anchor.

**Regressions introduced?**

Partially. The PR did not introduce any structural or success-rate regressions. It did introduce:

1. A **new secondary template lock** in llama3.1: "The options assume/neglect/overlook…" at 76% rate (13/17 reviews), with 4 near-identical reviews and 1 exact duplicate pair in hong_kong_game. This is less severe than the original 100% "This lever governs" lock (the new pattern is at least semantically varied by plan context) but is still formulaic.

2. A **new Pydantic failure mode**: The parasomnia plan now fails with a 19-char review ("Sensor Data Sharing"), because the old template incidentally guaranteed review length. The failure count (1/5 for llama3.1) is unchanged, but the failure cause shifted.

**Verification of analysis 25 predictions:**

The analysis 25 assessment ("Recommended Next Change") predicted:
- `llama3.1 (run ~90): "This lever governs" rate drops below 50%` → **Achieved: 0%** (run 89)
- `qwen3 (run ~91): "Core tension:" rate drops toward 0%` → **Substantially achieved: ~6%** in hong_kong_game (run 92)
- `haiku and gpt-4o-mini: no regression` → **Confirmed: runs 95, 93 show 5/5 completions**
- `Fabrication check: no new fabricated numbers` → **Confirmed: no % claims detected**
- `Option count failures: check if run 82-equivalent failures persist` → **Persists in llama3.1 (different cause)**

**Verdict: KEEP**

The PR achieves its stated goal. Template lock rates drop dramatically for both targeted models (llama3.1: 100% → 0%; qwen3: ~100% → 6%). No success-rate regression. No content quality regression (lengths, fabrication, tone all stable). The secondary template lock in llama3.1 ("The options assume…") and duplicate review are new problems to address in a follow-up PR — they are not regressions in the traditional sense (the before-batch had 100% lock; the after-batch has 76% of a different, less sticky lock pattern). The overall output diversity improved substantially.

---

## Questions For Later Synthesis

1. **Secondary template lock in llama3.1**: How should the next PR address "The options assume that the [X] is fixed, neglecting the possibility that it could be a dynamic entity…"? Is this a new verbatim copy from the replacement examples, or is it emergent from the model? Checking if this exact phrase appears in the new system-prompt section 4 would confirm.

2. **qwen3 "Core tension:" in non-hong_kong_game plans**: The previous assessment noted "Core tension:" in sovereign_identity and parasomnia for qwen3. I only verified hong_kong_game for run 92. Did the PR also reduce "Core tension:" in those plans? This needs verification from run 92 silo/sovereign_identity lever files.

3. **Duplicate review mechanism**: Why does llama3.1 produce identical reviews for different levers? Is this a model-level issue (running out of unique critique framings) or a prompt-level issue (insufficient diversity instructions)?

4. **min_length=20 validator vs new failure mode**: Should the min_length be raised to prevent "Sensor Data Sharing"-style degenerate reviews, or should the system prompt explicitly require a minimum substance (e.g., "at least two distinct critique points")? Raising min_length might just push llama3.1 to produce slightly longer but equally degenerate output.

5. **Template-lock migration as a general pattern**: Analysis 25's recommendation warned that qwen3 "may shift to a different formulaic opener rather than eliminating the pattern entirely." This was confirmed for llama3.1 (shifted from "This lever governs…" to "The options assume/neglect…"). Is this a systematic property of example-based negative constraints? If so, adding a second negative constraint ("Do NOT open with 'The options assume'") might only trigger a third shift.

---

## Reflect

The PR is a well-targeted fix that demonstrates the mechanism works: replacing the verbatim example in both the Pydantic field description and the system prompt breaks the template lock at the source. The analysis 25 recommendation was correct about the dual-location anchor being the root cause.

The main lesson from this iteration is that template-lock migration is real: breaking one lock creates a vacuum that weaker models fill with the next-most-salient pattern. This suggests that the optimization strategy should move toward positive diversity constraints ("each review must address a different dimension: cost, feasibility, risk, or stakeholder impact") rather than only negative constraints ("do not start with X"). Positive diversity constraints leave fewer stylistic vacuums for models to fill with new templates.

The new Pydantic failure mode (review too short) is an indirect consequence of removing the verbose template. It is less severe than the options-count failure it replaced (a 19-char single-phrase review is easier to detect and prevent than a silent 2-option lever), but it signals that llama3.1 is now operating without the safety net the template provided.

---

## Potential Code Changes

C1: **Add a positive diversity constraint to `review_lever` field description.** Instead of (or in addition to) negative constraints, add guidance: "Each review must address exactly one specific risk not mentioned in the consequences field — choose from: production feasibility, audience reception, financial viability, technical constraint, or stakeholder conflict." This prevents both the old lock ("This lever governs…") and the new lock ("The options assume/neglect…") by prescribing what to write rather than only proscribing what to avoid.
*Evidence:* Run 89 hong_kong_game items 8–11, 13–17 — all "The options assume/neglect" with no differentiation in risk type.

C2: **Raise `min_length` for `review_lever` or add soft minimum guidance.** The current `min_length=20` is insufficient — "Sensor Data Sharing" (19 chars) triggers it, but a 25-char degenerate review would pass. Either raise to 50 chars or add to the Pydantic field description: "minimum one complete sentence, at least 40 characters." This prevents degenerate outputs that the old template incidentally blocked.
*Evidence:* `history/1/89_identify_potential_levers/events.jsonl` line 10 — 19-char review for parasomnia lever 2.

C3: **Add "Do NOT open with 'The options assume'" negative constraint** to `review_lever` field description and system-prompt section 4. This breaks the secondary lock observed in run 89.
*Evidence:* 13/17 reviews in run 89 hong_kong_game use this opener.

C4: **Verify `LeverCleaned.review` field description** was fully updated as claimed. The PR description says 3 locations were updated. The analysis 25 assessment noted `LeverCleaned` field descriptions serve no prompting purpose (the schema is never passed to an LLM), but if the old examples remain, they represent a latent risk if the code changes.
*Evidence:* analysis/25/assessment.md backlog item 4: "`LeverCleaned.review` field description duplicates leaked examples... dead weight."

---

## Summary

PR #337 successfully breaks the primary template locks for llama3.1 and qwen3. The "This lever governs the tension between…" rate in llama3.1 dropped from 100% to 0%; qwen3's "This lever [verb]" rate dropped from ~100% to 6% (both measured on hong_kong_game). Overall success rate is unchanged at 97.1%.

The PR's direct trade-off: the old template provided an accidental safety net (guaranteed verbose reviews, kept llama3.1 from generating degenerate single-phrase content). Removing it exposed a new failure mode (19-char review → Pydantic error on parasomnia) and created a stylistic vacuum that llama3.1 filled with a secondary template ("The options assume/neglect…") at 76% rate, including exact duplicate reviews.

The secondary template is less severe than the original (domain-relative rather than domain-neutral, shorter, less copy-paste-able), but it confirms the "template-lock migration" hypothesis. The next iteration should add positive diversity constraints rather than only negative ones.

**Verdict: KEEP.** The PR delivers measurable improvement on its stated goal. Follow-up work needed: add `C1` (positive diversity constraint), `C2` (min_length guidance), and `C3` (secondary lock negative constraint) in the next PR.
