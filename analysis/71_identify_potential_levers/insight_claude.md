# Insight Claude

## Scope

Analyzing current runs `5/04–5/10` (after PR #475) against previous runs `2/87–2/93`
(after PR #358, the registered best baseline from `analysis/best.json`) for the
`identify_potential_levers` step.

**PR under evaluation:** PR #475 "Positive framing, consistent word counts, and stronger
number-evidence constraint"

**Changes made by PR #475 (per description):**
- Fix 1 — Consistent length targets: all three sources (field desc ×2, system prompt)
  now say "2–3 sentences". PR #473 left system prompt at "2–4", which haiku followed
  → 2.1× baseline verbosity.
- Fix 3 — Stronger number-evidence constraint: "Never invent percentages, costs, or
  timeframes — only cite numbers that appear in the project context." Placed before the
  cause-effect directive. PR #473's "cause-effect" framing correlated with gpt-oss-20b
  inventing HK$2m/5m/10m figures.
- Positive framing: Replace "Do NOT include 'Controls ... vs.'"
- Reduced output: options "one sentence", review_lever "1–2 sentences" (same as #473)
- Supersedes PR #471 and PR #473.

**Model mapping (same models, same order in both batches):**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/87 | 5/04 | ollama-llama3.1 |
| 2/88 | 5/05 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/06 | openai-gpt-5-nano |
| 2/90 | 5/07 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/08 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/09 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/10 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

1. **Fabricated HK$ amounts increased 4×.** The PR's central Fix 3 ("stronger
   number-evidence constraint") failed to reduce and actually worsened HK$-denominated
   fabrication. HKD references: 5 → 20 (before → after). Dollar-sign references:
   6 → 28. The increase is driven by haiku (HKD 3→11, $ 4→19) and gpt-oss-20b
   (HKD 1→6, $ 1→6). See Quantitative Metrics section for per-run detail.

2. **Haiku's financial fabrication pattern.** Haiku generates financing-intensive levers
   for the hong_kong_game plan, where the plan text provides HK$470M, HK$195M, and
   HK$940M–1.7B as real numbers. Haiku then derives additional amounts not in the plan:
   - `HK$75M` from Hong Kong Film Development Fund (plan mentions the Fund but gives no
     specific subsidy amount)
   - `HK$60–80 for 48-hour rental` (fabricated VOD pricing)
   - Specific theatrical window options `21, 30, or 45 days` (not in plan)

   Evidence: `history/5/10_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
   levers "Financing Structure and Mainland China Exposure" and "Release Strategy:
   Theatrical Window and Premium VOD Timing".

3. **gpt-oss-20b fabricates derived arithmetic.** In the "Capital Allocation and
   Incentive Lever" (5/05, hong_kong_game), gpt-oss-20b calculates specific percentages
   of the plan's HK$470M budget:
   - `HK$141 million` (≈30% of 470M) for film fund incentives
   - `HK$117.5 million` (≈25%) for post-production cost sharing
   - `HK$70.5 million` (≈15%) for deferred talent payments

   None of these derived figures appear in the plan. The model is doing mental arithmetic
   off a real plan number and presenting the result as fact.
   Evidence: `history/5/05_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

4. **Fix 1 (consistent length targets) shows no measurable effect.** Average
   consequences length barely changed: 297.8 → 299.8 chars (+0.7%). Average review
   length: 198.8 → 192.3 chars (−3.3%). Haiku's avg_cons actually went up: 515 →
   557 chars (+8%). If the verbosity problem was real, the fix didn't register.

5. **Haiku lever count increased.** Haiku went from 93 to 101 levers across 5 plans
   (+8.6%). Most of the increase is in gta_game (estimated 13→29 for haiku), suggesting
   the prompt may be encouraging over-generation for fictional/creative domains.

---

## Positive Things

1. **Zero execution errors.** All 35/35 plans succeeded in both batches
   (7 models × 5 plans). No LLMChatError or ValidationError entries in any
   events.jsonl file.

2. **No "Controls ... vs." template leakage.** Zero lever names contain the old
   "Controls X" prefix in either batch. The positive framing change had no downside.

3. **Marketing language stable at low rate.** Hype words ("game-changing",
   "revolutionary", "cutting-edge", etc.) appear at roughly the same low frequency
   in both batches. The prompt is not injecting marketing tone.

4. **Haiku produces high-quality, grounded lever content in most levers.** Despite
   the financial fabrication in hong_kong_game, haiku's output for other plans
   (silo, sovereign_identity, parasomnia, gta_game) shows deep contextual awareness,
   multi-stakeholder analysis, and domain-specific reasoning. The fabrication problem
   is plan-domain-specific, not pervasive.

5. **Review field diversity is healthy.** No single opener pattern dominates.
   Both batches show varied review openers: "This", "The", action verbs
   ("Enhancing", "Expanding"), domain-specific framings. No template lock.

6. **qwen3-30b percentage claims dropped.** qwen3's pct% claims: 4 → 1. The only
   model that showed meaningful improvement on the targeted fabrication metric.

7. **Field lengths are proportionate to baseline.** No field exceeds 2× the baseline
   average. Name: 36.0 (baseline 27.7, ratio 1.30). Consequences: 299.8 (baseline
   279.5, ratio 1.07). Options: 477.8 (baseline 450.5, ratio 1.06). Review: 192.3
   (baseline 152.3, ratio 1.26). All within acceptable range.

---

## Comparison

The before runs (2/87–93) represent the state after PR #358 (remove "core tension"
template lock). The after runs (5/04–10) represent PR #475's changes.

| Dimension | Before (2/87–93) | After (5/04–10) | Change |
|---|---|---|---|
| Success rate | 35/35 (100%) | 35/35 (100%) | None |
| Total levers | 633 | 636 | +0.5% |
| Avg name (chars) | 36.2 | 36.0 | −0.6% |
| Avg consequences (chars) | 297.8 | 299.8 | +0.7% |
| Avg options total (chars) | 479.3 | 477.8 | −0.3% |
| Avg review (chars) | 198.8 | 192.3 | −3.3% |
| HKD references (total) | 5 | 20 | **+4×** |
| Percentage claims (total) | 39 | 40 | +2.6% |
| Dollar signs (total) | 6 | 28 | **+4.7×** |
| "Controls" template leakage | 0 | 0 | None |
| LLMChatError events | 0 | 0 | None |

The field-length metrics are essentially flat. The only significant movement is in
fabricated numbers, which worsened substantially.

---

## Quantitative Metrics

### Average Field Lengths vs Baseline

| Metric | Baseline | Before (2/87–93) | After (5/04–10) | Ratio vs Baseline |
|---|---|---|---|---|
| Name (chars) | 27.7 | 36.2 | 36.0 | 1.30× |
| Consequences (chars) | 279.5 | 297.8 | 299.8 | 1.07× |
| Options total (chars) | 450.5 | 479.3 | 477.8 | 1.06× |
| Review (chars) | 152.3 | 198.8 | 192.3 | 1.26× |

No field exceeds 2× the baseline. This is a healthy signal. The name field is
the furthest above baseline (1.30×) but is stable.

### Fabricated Number Counts by Model

| Run | Model | Levers | HKD | Pct% | $ |
|---|---|---|---|---|---|
| 2/87 | llama3.1 | 82 | 0 | 0 | 0 |
| **5/04** | llama3.1 | 78 | 0 | 0 | 0 |
| 2/88 | gpt-oss-20b | 91 | 1 | 0 | 1 |
| **5/05** | gpt-oss-20b | 90 | **6** | 1 | **6** |
| 2/89 | gpt-5-nano | 91 | 1 | 0 | 1 |
| **5/06** | gpt-5-nano | 90 | 3 | 1 | 3 |
| 2/90 | qwen3-30b | 99 | 0 | 4 | 0 |
| **5/07** | qwen3-30b | 101 | 0 | 1 | 0 |
| 2/91 | gpt-4o-mini | 86 | 0 | 0 | 0 |
| **5/08** | gpt-4o-mini | 84 | 0 | 0 | 0 |
| 2/92 | gemini-2.0-flash | 91 | 0 | 0 | 0 |
| **5/09** | gemini-2.0-flash | 92 | 0 | 0 | 0 |
| 2/93 | haiku-4-5 | 93 | 3 | 35 | 4 |
| **5/10** | haiku-4-5 | 101 | **11** | 37 | **19** |

HKD = explicit HK$XXX references; Pct% = percentage claims (e.g. "30%");
$ = dollar-sign references (includes HK$ doubles counted in both columns).

Key observations:
- llama3.1, gpt-4o-mini, gemini: unchanged at 0.
- qwen3-30b: improved (4 → 1 pct%).
- gpt-oss-20b: significant regression (HKD 1→6).
- gpt-5-nano: moderate regression (HKD 1→3).
- haiku-4-5: major regression (HKD 3→11, $ 4→19).

### Hong Kong Game Plan: HK$ Sources in Plan Text

The hong_kong_game plan text (`001-2-plan.txt`) contains these numbers:
HK$470M (production budget), HK$195M (P&A), HK$940M–HK$1.7B (revenue target),
45–55 shoot days, 18–20 months, 4 weeks, 60 days.

Numbers fabricated or derived (not in plan):
- HK$75M Film Development Fund subsidy (plan mentions the Fund but not the amount)
- HK$141M, HK$117.5M, HK$70.5M (arithmetic derivatives of HK$470M)
- HK$60–80 per 48-hr rental (fabricated VOD pricing)
- "21, 30, or 45 days" theatrical window options (not in plan)

The constraint says "only cite numbers that appear in the project context" but models
are: (a) citing plan numbers correctly AND (b) deriving new numbers from those real
numbers. The constraint as written does not prohibit arithmetic derivation.

### Constraint Violations

| Type | Before (2/87–93) | After (5/04–10) |
|---|---|---|
| "Controls " prefix in name | 0 | 0 |
| Square brackets in review | 0 | 0 |
| review_lever < 10 chars | 0 | 0 |
| options count < 3 | 0 | 0 |
| LLMChatError / ValidationError | 0 | 0 |

No structural constraint violations in either batch.

---

## Evidence Notes

1. **gpt-oss-20b arithmetic derivation** (5/05, hong_kong_game, lever "Capital
   Allocation and Incentive Lever"):
   ```
   options[0]: "Allocate HK$141 million of the HK$470 million budget to local film
                fund incentives..."
   options[1]: "Secure a co-production agreement with a regional studio to share
                HK$117.5 million of post-production expenses..."
   options[2]: "Introduce a deferred payment structure for key talent, shifting
                HK$70.5 million of salaries to post-release revenue..."
   ```
   The plan contains HK$470M but none of the derived split amounts. The model
   invented specific allocations (30%, 25%, 15%) off the real total.

2. **haiku HK$75M fabrication** (5/10, hong_kong_game, lever "Financing Structure
   and Mainland China Exposure"):
   ```
   options[0]: "Assemble financing from Hong Kong Film Development Fund (up to HK$75M)
                combined with international pre-sales..."
   ```
   The plan mentions leveraging "Hong Kong Film Development Fund incentives" without
   specifying an amount. HK$75M is fabricated.

3. **haiku HK$60–80 VOD pricing** (5/10, hong_kong_game, lever "Release Strategy:
   Theatrical Window and Premium VOD Timing"):
   ```
   "premium VOD pricing (HK$60-80 for 48-hour rental, modeled on recent high-profile
    releases)"
   ```
   No VOD pricing appears in the plan. This is fabricated market data.

4. **Baseline levers for hong_kong_game** (`baseline/train/20260310_hong_kong_game/
   002-10-potential_levers.json`): Baseline has no HK$ references but has 5 fabricated
   percentage claims (15%, 20%, 30%, 10%, 25%). The current optimization has reduced
   percentage fabrication relative to baseline (haiku has 37 vs baseline's 5, but
   haiku covers 5 plans vs baseline's 1 plan — per-plan haiku has ~7 pct% claims vs
   5 in baseline, roughly comparable).

5. **Haiku verbosity in consequences** (per-run avg_cons): 515 (before) → 557 (after).
   The "Fix 1" length target (2–3 sentences) did not reduce haiku's output length;
   it increased. This contradicts the PR description's claim that fixing the 2–4 vs
   2–3 sentence discrepancy would fix haiku verbosity.

---

## PR Impact

### What the PR was supposed to fix
1. **Fix 1**: Consistent length targets — fix haiku's 2.1× baseline verbosity caused
   by the system prompt saying "2–4" while field descriptions said "2–3".
2. **Fix 3**: Stronger number-evidence constraint — suppress gpt-oss-20b HK$ invention
   that correlated with "cause-effect" framing in PR #473.
3. **Positive framing** of prohibitions (cosmetic change).
4. **Reduced output**: options "one sentence", review_lever "1–2 sentences".

### Before vs After Comparison

| Metric | Before (2/87–93) | After (5/04–10) | Change |
|---|---|---|---|
| Avg haiku consequences (chars) | 515 | 557 | **+8%** ← worsened |
| Avg haiku review (chars) | 321 | 310 | −3% (negligible) |
| Total HKD fabrications | 5 | 20 | **+4×** ← worsened |
| Total $ fabrications | 6 | 28 | **+4.7×** ← worsened |
| gpt-oss HKD count | 1 | 6 | **+6×** ← worsened |
| haiku HKD count | 3 | 11 | **+3.7×** ← worsened |
| Success rate | 35/35 | 35/35 | No change |
| Avg consequences (all, chars) | 297.8 | 299.8 | No change |
| "Controls" template leakage | 0 | 0 | No change |
| LLMChatErrors | 0 | 0 | No change |

### Did the PR fix the targeted issues?

**Fix 1 (haiku verbosity): NOT FIXED.**
Haiku's avg_cons went from 515 to 557 (+8%). This is the opposite of the claimed fix.
The haiku verbosity measured in PR #473's iteration was not caused by the "2–4 vs
2–3" sentence discrepancy, or the fix had no effect.

**Fix 3 (fabricated numbers): MADE THINGS WORSE.**
Total HKD references increased from 5 to 20 (+4×). Dollar sign references from
6 to 28 (+4.7×). gpt-oss-20b specifically went from HKD=1 to HKD=6. The constraint
"Never invent percentages, costs, or timeframes — only cite numbers that appear in
the project context" was strengthened, but fabrication increased. This may be
because models interpret the constraint as permission to use plan numbers extensively
while also deriving new amounts from those plan numbers.

**Positive framing: NEUTRAL.**
No measurable effect on outputs. Zero "Controls" prefix before and after.

**Reduced output for options/review: NEGLIGIBLE.**
Average options length: 479.3 → 477.8 (−0.3%). Average review length: 198.8 →
192.3 (−3.3%). Changes are within noise.

### New issues introduced?

The 4× increase in fabricated HKD and dollar amounts is a new issue — or rather,
an amplification of a pre-existing problem. The anti-fabrication constraint as
currently worded appears to backfire for plans that supply real budget numbers:
models cite the real numbers and then freely derive additional amounts.

### Verdict: CONDITIONAL

The PR does not revert the solid gains from PR #358 (zero template leakage, zero
validation errors, stable success rate). However, its stated goals failed:
- Fix 1 did not reduce haiku verbosity (measurements contradict the premise).
- Fix 3 made fabrication significantly worse (4× HKD increase).

Keep as a neutral structural change (positive framing, consistent wording), but
follow up with a targeted fix for the fabrication regression. The current anti-
fabrication constraint needs to explicitly prohibit **arithmetic derivation** from
plan numbers, not just invention of numbers from nothing.

---

## Questions For Later Synthesis

1. Is the HKD/$ increase driven entirely by the hong_kong_game plan (which supplies
   real budget numbers), or do other plans also show increased numerical references?
   (The data suggests it's concentrated in hong_kong_game and in haiku/gpt-oss-20b.)

2. Is haiku's verbosity increase (avg_cons 515→557) a measurement artifact (e.g.,
   different plan distribution in the two batches) or a genuine prompt effect?

3. The PR claims to supersede #471 and #473 which were evaluated as CONDITIONAL.
   Were those intermediate PRs measured in the optimization loop? If so, what were
   their HKD fabrication counts? Understanding the trajectory would clarify whether
   PR #475 introduced a regression relative to #471/#473 or relative to #358.

4. The anti-fabrication constraint is identical in the system prompt (section 2,
   Consequences bullets) and the Pydantic field description. Does doubling the
   constraint in two locations increase model compliance, or does it have diminishing
   returns and possibly cause "compensation" behavior?

5. The plan `20260310_hong_kong_game` provides unusually rich financial detail
   (budget, P&A, revenue targets) compared to other plans. Should domain-specific
   plan types (film production, real estate) receive different prompt handling to
   suppress derived arithmetic?

---

## Reflect

The fabrication regression is counterintuitive: strengthening the anti-fabrication
constraint worsened fabrication. One explanation: the constraint says "only cite
numbers that appear in the project context." Models with finance domain knowledge
read this as an invitation to deeply engage with the plan's financial figures —
and then helpfully derive breakdowns and allocations from those figures. Haiku in
particular generates elaborate financing levers that fully engage with HK$470M as
a real production budget and extrapolate fund allocations, VOD pricing, and
theatrical window lengths that would apply to a film of this scale.

This suggests the constraint needs a different framing: rather than "only cite
numbers from context," it should also say "do not perform arithmetic on plan
numbers to generate derived figures." This is a qualitatively different
instruction.

Alternatively, a code-level check that flags numerical claims and cross-references
them against the plan text would be more robust than a prompt instruction.

The field lengths being nearly unchanged also suggests that "Fix 1" was solving
a problem that may not have existed in the batch used for this analysis, or the
verbosity problem was in a different metric than what was measured here.

---

## Potential Code Changes

- **C1**: Post-processing validation for fabricated numbers. After receiving lever
  output, check whether specific numbers (dollar amounts, percentages) appear in
  the user_prompt text. If not, log a warning or trigger a retry with an explicit
  "you cited HK$X which is not in the project context" message. This is a code fix
  in `identify_potential_levers.py` (post-response validation) rather than a prompt
  change, and would catch the derivation pattern that text constraints miss.
  File: `identify_potential_levers.py`, in the response-cleaning / validation block.

- **C2**: Add fabrication rate to OPTIMIZE_INSTRUCTIONS' known problems. The
  "arithmetic derivation" pattern (where models compute breakdowns from a real
  plan total) is not documented in the current `OPTIMIZE_INSTRUCTIONS` constant.
  Adding it would help future analysis agents recognize the pattern:
  > "Arithmetic derivation: models that see a real budget total (e.g. HK$470M) will
  > compute and present specific allocations (HK$141M = 30%) as if they are factual.
  > The anti-fabrication constraint must explicitly prohibit this: 'do not split,
  > allocate, or calculate from plan numbers to generate derived figures.'"

---

## Summary

PR #475 produced no measurable improvement on its stated goals:

- **Fix 1 (length consistency)**: haiku avg_cons increased 8%; no field length
  changed meaningfully.
- **Fix 3 (anti-fabrication)**: HKD fabrication increased 4×, dollar fabrication
  increased 4.7×. This is a direct regression on the targeted metric.
- **Positive framing / reduced output**: no observable effect.

The PR maintained zero template leakage, zero execution errors, and 100% success
rate from the prior best baseline (PR #358). These gains are preserved.

The fabrication regression requires a follow-up fix. The constraint wording approach
("Never invent...") is insufficient for plans that supply real budget numbers because
models treat arithmetic derivation from real numbers as legitimate. A stronger
constraint must explicitly prohibit computed derivations, or a code-level validation
should catch them.

**Verdict: CONDITIONAL** — keep the structural/cosmetic changes, but immediately
follow up with a more targeted intervention for the fabrication regression. Do not
treat this PR as a solved iteration.
