# Insight Claude

**Analysis of iteration 31** — evaluating PR #346 "Add lever_type and decision_axis to lever schema"

Runs examined:
- **Current (after PR)**: `history/2/24_identify_potential_levers` – `2/30_identify_potential_levers`
- **Previous (before PR)**: `history/2/10_identify_potential_levers` – `2/16_identify_potential_levers`

Model-to-run mapping (before → after):

| Before | After | Model |
|--------|-------|-------|
| Run 10 | Run 24 | ollama-llama3.1 |
| Run 11 | Run 25 | openrouter-openai-gpt-oss-20b |
| Run 12 | Run 26 | openai-gpt-5-nano |
| Run 13 | Run 27 | openrouter-qwen3-30b-a3b |
| Run 14 | Run 28 | openrouter-openai-gpt-4o-mini |
| Run 15 | Run 29 | openrouter-gemini-2.0-flash-001 |
| Run 16 | Run 30 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### N1 — Haiku JSON truncation: 2 new failures caused directly by PR #346

Run 30 (anthropic-claude-haiku-4-5-pinned) failed on 2 plans due to truncated JSON output:
- `20250329_gta_game`: EOF at column 29,300 — `{"strategic_rationale": ...}}}}}}}}}}}}}}}}}}}}`
- `20250321_silo`: EOF at column 43,016

Before the PR (run 16), haiku succeeded on all 5 plans (5/5 ok). After (run 30): 3/5 ok.

Evidence: `history/2/30_identify_potential_levers/events.jsonl` — `run_single_plan_error` events for both plans with `LLMChatError: Invalid JSON: EOF while parsing a string`.

Root cause: PR #346 adds two new fields (`lever_type` ≈ 10–20 chars + `decision_axis` ≈ 289 chars avg for haiku) to every lever in every API response. With 3 calls per plan and 7–9 levers per call, haiku responses grew by ~6,000–8,000 chars per plan. The successful haiku plans in run 30 show 63–67k total chars per plan vs 36–55k in run 16. Two plans exceeded the model's effective max-tokens ceiling.

This is a direct regression caused by PR #346.

### N2 — llama3.1 new failure: lever_type='coalition_building' rejected

Run 24 (ollama-llama3.1) failed on `20260308_sovereign_identity` due to:
```
Value error, lever_type must be one of ['dissemination', 'execution', 'governance',
'methodology', 'operations', 'product'], got 'coalition_building'
```

Evidence: `history/2/24_identify_potential_levers/events.jsonl` — `run_single_plan_error` for `sovereign_identity`.

The previous run 10 succeeded on sovereign_identity. This failure is new and directly caused by PR #346's `lever_type` validator. The model invented a semantically reasonable but non-enumerated type (`coalition_building`), which the hard validator rejected with no retry tolerance.

### N3 — llama3.1 pre-existing failures persist (not caused by PR #346)

Run 24 (llama3.1) also failed on:
- `20250321_silo`: `review_lever is too short (0 chars); expected at least 50` — the model returned empty review fields for 7 levers. This is the same stochastic failure mode seen in run 10 (which failed on `hong_kong_game` and `parasomnia_research_unit` with the same pattern).
- `20260310_hong_kong_game`: `options must have at least 3 items, got 2` — returned 2-option levers.

These two failures are pre-existing llama3.1 reliability issues, not caused by PR #346.

### N4 — Success rate dropped from 94.3% to 85.7%

| Metric | Before (runs 10–16) | After (runs 24–30) | Change |
|--------|--------------------|--------------------|--------|
| Plans succeeded | 33/35 | 30/35 | −3 plans |
| Success rate | 94.3% | 85.7% | **−8.6 pp** |

Of the 3 new failures relative to before: 1 is directly PR-caused (N2: lever_type='coalition_building'), 2 are directly PR-caused (N1: haiku JSON truncation). The pre-existing llama3.1 failures (N3: review_lever too short, options < 3) were also present before. Net new failures from PR #346: **3 plans**.

### N5 — haiku decision_axis non-conformance: 24% use "whether" variant

Run 30 (haiku) produces 17/70 (24%) decision_axis entries using:
> "This lever controls whether the project frames X as Y or Z"

instead of the required:
> "This lever controls X by choosing between A, B, and C"

Examples from `history/2/30_identify_potential_levers/outputs/20260308_sovereign_identity/`:
- `"This lever controls whether the project frames platform-neutral access as an innovation opportunity..."`
- `"This lever controls whether the non-production demonstrators target regulatory and procurement specialists..."`

These describe binary/conditional decisions rather than multi-option choices. While semantically valid, they deviate from the PR's specified format and indicate that haiku interprets many decisions as binary rather than trinary.

### N6 — Governance bias in gpt-5-nano

Run 26 (openai-gpt-5-nano) assigns `lever_type = governance` to 35% of levers (32/91), compared to the cross-model average of 24%. This suggests the model over-classifies organizational and structural decisions as governance when they might be better categorized as operations or execution.

Evidence: `history/2/26_identify_potential_levers/` — lever_type distribution: governance=32, methodology=15, dissemination=12, product=12, operations=12, execution=8.

### N7 — Template leakage ("The options [verb]") remains unresolved

The "The options [verb]" pattern in `review` fields is unchanged by this PR (which only adds new fields, does not modify the system prompt review section). Rates remain high:

| Run | Model | Before rate | After rate |
|-----|-------|------------|------------|
| 10→24 | ollama-llama3.1 | 63% (33/52) | 0% (0/20)* |
| 11→25 | openrouter-openai-gpt-oss-20b | 47% (43/91) | 50% (42/84) |
| 12→26 | openai-gpt-5-nano | 56% (52/92) | 61% (56/91) |
| 13→27 | openrouter-qwen3-30b-a3b | 70% (64/91) | 88% (83/94) |
| 14→28 | openrouter-openai-gpt-4o-mini | 100% (85/85) | 100% (80/80) |
| 15→29 | openrouter-gemini-2.0-flash-001 | 100% (90/90) | 92% (72/78) |
| 16→30 | anthropic-claude-haiku-4-5-pinned | 61% (65/106) | 47% (33/70) |

\* llama3.1 run 24 had only 20 levers (2/5 plans succeeded), making the 0% rate non-comparable.

No significant trend change. The pattern is a carry-forward issue from prior iterations.

---

## Positive Things

### P1 — lever_type is correctly populated across all models except llama3.1 edge case

All 6 valid lever_type values (`methodology`, `execution`, `governance`, `dissemination`, `product`, `operations`) are represented in every run. No model other than llama3.1 produced an invalid type. The normalized distribution (governance 24%, product 19%, operations 16%, methodology 15%, execution 13%, dissemination 11%) is well-spread across categories.

### P2 — decision_axis format conformance is high

| Run | Model | Conformant (pattern) | "by selecting" variant | "whether" variant | Other |
|-----|-------|---------------------|-----------------------|-------------------|-------|
| 24 | llama3.1 | 100% (20/20) | 0 | 0 | 0 |
| 25 | gpt-oss-20b | 100% (84/84) | 0 | 0 | 0 |
| 26 | gpt-5-nano | 100% (91/91) | 0 | 0 | 0 |
| 27 | qwen3-30b-a3b | 100% (94/94) | 0 | 0 | 0 |
| 28 | gpt-4o-mini | 98% (79/80) | 1 | 0 | 0 |
| 29 | gemini-flash | 100% (78/78) | 0 | 0 | 0 |
| 30 | haiku | 75% (53/70) | 0 | 24% (17/70) | 0 |

The single "by selecting between" deviation in run 28 (`history/2/28_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`, lever "Alternative Authentication Protocols") is minor — semantically equivalent and passes the 20-char min check.

### P3 — decision_axis content is informative and actionable

Sample from `history/2/27_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
- "This lever controls critical momentum by choosing between Toronto, Busan, or Venice as the primary festival platform."
- "This lever controls regulatory compliance by choosing between implicit thematic framing, local content partnerships, or neutralizing sensitive topics."

These are specific, grounded choices tied to actual project constraints. They add genuine value for downstream decision-making (the scenario picker can select options with explicit awareness of what's being traded off).

### P4 — No content quality regressions for 5 of 7 models

Most models show field lengths similar to or slightly above before-PR levels. All well-cited models are within the 2× baseline threshold:

| Model | Cons (B/A) | Options (B/A) | Review (B/A) |
|-------|-----------|--------------|-------------|
| gpt-oss-20b | 287/338 | 433/404 | 154/144 |
| gpt-5-nano | 288/375 | 449/424 | 193/172 |
| qwen3 | 217/259 | 264/281 | 171/190 |
| gpt-4o-mini | 250/270 | 412/381 | 182/175 |
| gemini-flash | 333/335 | 535/534 | 228/211 |

Baseline averages: consequences ~279, options ~463, review ~152. All 5 models are below the 2× warning threshold on all fields.

### P5 — Zero fabricated percentage claims in 5 of 7 models

| Run | Model | Pct claims |
|-----|-------|------------|
| 24 | llama3.1 | 0 |
| 25 | gpt-oss-20b | 3 |
| 26 | gpt-5-nano | 0 |
| 27 | qwen3 | 2 |
| 28 | gpt-4o-mini | 0 |
| 29 | gemini-flash | 0 |
| 30 | haiku | 7 |

Haiku continues to fabricate numeric claims (7 instances in 70 levers = 10%). The 3 from gpt-oss-20b and 2 from qwen3 are low-level stochastic noise. No causal relationship to this PR.

### P6 — lever_type adds useful categorization signal

The type distribution across plans shows domain-appropriate variation. For `hong_kong_game` (a film project): governance (director/IP/financing), execution (casting/scheduling), product (narrative design), dissemination (festival/release strategy) are all represented. For `sovereign_identity` (a digital identity research project): governance, methodology, and operations dominate — appropriate for a research/technical project.

---

## Comparison

### Content quality vs baseline

Baseline (`baseline/train/*/002-10-potential_levers.json`, 5 plans): avg consequences=279, options=463, review=152, levers per plan=15.

| Field | Baseline avg | After avg (runs 24–30, excl. haiku) | Ratio | After avg (haiku run 30) | Ratio |
|-------|-------------|--------------------------------------|-------|--------------------------|-------|
| consequences | 279 | 315 | 1.13× | 682 | **2.44×** |
| options | 463 | 405 | 0.87× | 944 | **2.04×** |
| review | 152 | 175 | 1.15× | 564 | **3.71×** |
| decision_axis | — (new) | 151 | — | 289 | — |
| levers per plan (successful) | 15 | ~17–19 | 1.2× | ~22–25 | 1.5× |

Non-haiku models: All ratios below 2×. Quality is acceptable.

Haiku: consequences 2.44× (warning), options 2.04× (warning), review 3.71× (well above 3× regression threshold). Haiku was already verbose before this PR (run 16: consequences=551, options=928, review=475), but the new fields appear to compound the verbosity. The successful haiku plans in run 30 have total plan output 19–30% larger than run 16's successful plans.

---

## Quantitative Metrics

### Success rate

| Metric | Before (runs 10–16) | After (runs 24–30) | Change |
|--------|--------------------|--------------------|--------|
| Plans succeeded | 33/35 | 30/35 | −3 plans |
| Success rate | 94.3% | 85.7% | **−8.6 pp** |
| PR-caused failures | — | 3 (1×lever_type, 2×JSON-EOF) | new |
| Pre-existing llama3.1 failures | 2 | 2 | unchanged |
| haiku failures | 0 | 2 | **+2 (PR-caused)** |

### Field length comparison (after PR, all models)

| Run | Model | N levers | Avg cons | Avg opts | Avg review | Avg DA |
|-----|-------|---------|----------|----------|------------|--------|
| 24 | llama3.1 | 20 | 290 | 221 | 194 | 213 |
| 25 | gpt-oss-20b | 84 | 338 | 404 | 144 | 145 |
| 26 | gpt-5-nano | 91 | 375 | 424 | 172 | 170 |
| 27 | qwen3 | 94 | 259 | 281 | 190 | 152 |
| 28 | gpt-4o-mini | 80 | 270 | 381 | 175 | 147 |
| 29 | gemini-flash | 78 | 335 | 534 | 211 | 139 |
| 30 | haiku | 70 | **682** | **944** | **564** | **289** |
| — | Baseline | 15/plan | 279 | 463 | 152 | — |

### Lever_type distribution (all after runs combined, 517 levers)

| lever_type | Count | % |
|-----------|-------|---|
| governance | 125 | 24% |
| product | 100 | 19% |
| operations | 83 | 16% |
| methodology | 82 | 15% |
| execution | 68 | 13% |
| dissemination | 59 | 11% |

### Decision_axis conformance

| Pattern | Count | % |
|---------|-------|---|
| "This lever controls X by choosing between A, B, C" | 499/517 | 97% |
| "This lever controls whether X" | 17/517 | 3% |
| "by selecting between" (minor variant) | 1/517 | <1% |
| Invalid (< 20 chars or blank) | 0/517 | 0% |

### Fabricated claims and constraint violations

| Run | Model | Pct claims | Marketing words | Option < 3 | DA < 20 chars | Invalid lever_type |
|-----|-------|-----------|----------------|-----------|--------------|-------------------|
| 24 | llama3.1 | 0 | 4 | 3 plans* | 0 | 1 plan |
| 25 | gpt-oss-20b | 3 | 0 | 0 | 0 | 0 |
| 26 | gpt-5-nano | 0 | 1 | 0 | 0 | 0 |
| 27 | qwen3 | 2 | 0 | 0 | 0 | 0 |
| 28 | gpt-4o-mini | 0 | 7 | 0 | 0 | 0 |
| 29 | gemini-flash | 0 | 0 | 0 | 0 | 0 |
| 30 | haiku | 7 | 1 | 0 | 0 | 0 |

\* llama3.1 option < 3 violations caused a full plan failure (not counted in lever output).

---

## Evidence Notes

**E1** — Haiku JSON-EOF truncation:
`history/2/30_identify_potential_levers/events.jsonl`: `run_single_plan_error` for `gta_game` at column 29,300 and `silo` at column 43,016. The value snippet shows the JSON ended mid-string with repeated closing braces — a clear sign of max-tokens truncation.

**E2** — haiku plan sizes before vs after:
Run 16 (before): silo=35,579 chars, gta_game=36,928 chars, sovereign_identity=49,984 chars, hong_kong_game=47,593 chars, parasomnia=54,742 chars.
Run 30 (after): sovereign_identity=66,866 chars, hong_kong_game=58,470 chars, parasomnia=63,555 chars. The surviving plans grew ~19–34% in size. The failing plans would have needed ~29k and ~43k chars just to reach their truncation points.

**E3** — llama3.1 lever_type='coalition_building':
`history/2/24_identify_potential_levers/events.jsonl`: `run_single_plan_error` for `sovereign_identity` with error `lever_type must be one of ['dissemination', 'execution', 'governance', 'methodology', 'operations', 'product'], got 'coalition_building'`. The model invented a plausible but non-enumerated lever_type for the sovereign identity project (which has significant coalition-building aspects).

**E4** — gpt-5-nano governance bias:
`history/2/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`: "Financing mix" = governance, "Director and cast alignment" = governance, "Adaptation rights and distribution" = governance — 3 of the first 5 levers are governance. Total: 32/91 = 35% governance vs 24% cross-model average.

**E5** — haiku "whether" pattern:
`history/2/30_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`: All 17 non-conformant entries use "This lever controls whether..." and originate from the `sovereign_identity` plan, which has many binary go/no-go decision points rather than multi-option strategic choices.

---

## PR Impact

### What the PR was supposed to fix

PR #346 added two new fields to the lever schema:
1. `lever_type` — one of `methodology/execution/governance/dissemination/product/operations` — classifies each lever's category.
2. `decision_axis` — one sentence in the format "This lever controls X by choosing between A, B, and C" — describes the controllable choice explicitly.

Both fields propagate through `Lever` → `LeverCleaned` → JSON output. A new system prompt section 2 ("Lever Classification") guides the LLM on both fields. The PR implements proposals 1+2 from `docs/proposals/119-lever-pipeline-impl.md` (section 3.1).

### Before vs after comparison

| Metric | Before (runs 10–16) | After (runs 24–30) | Change |
|--------|--------------------|--------------------|--------|
| lever_type field present | No | Yes | **Added** |
| decision_axis field present | No | Yes | **Added** |
| Overall success rate | 94.3% (33/35) | 85.7% (30/35) | **−8.6 pp** |
| haiku success rate | 100% (5/5) | 60% (3/5) | **−40 pp** |
| llama3.1 success rate | 60% (3/5) | 40% (2/5) | **−20 pp** |
| DA format conformance | N/A | 97% (pattern matched) | N/A |
| Invalid lever_type rejections | N/A | 1 plan (llama3.1) | New failure mode |
| JSON-EOF truncation errors | 0 | 2 (haiku) | **+2 PR-caused** |
| Avg decision_axis length | N/A | 179 chars (excl. haiku: 151) | N/A |
| Field lengths (non-haiku) | Within 2× baseline | Within 2× baseline | Stable |
| Field lengths (haiku) | 2-3× baseline | 2.4–3.7× baseline | Worse |
| Template leakage (options) | ~24% avg | ~26% avg | Unchanged |
| Fabricated pct claims (haiku) | ~22% (from prior analysis) | 10% (7/70) | Improved (stochastic) |

### Did the PR fix the targeted issue?

Yes — the new fields are present and correctly populated in all successful runs. The `lever_type` taxonomy is meaningful (valid values only from 6/7 models), and `decision_axis` entries are informative and actionable for 5/7 models.

However, the structural addition came with **direct reliability regressions**:
- Haiku dropped from 5/5 to 3/5 due to JSON truncation caused by the larger per-lever payload.
- llama3.1 gained a new failure mode (invented lever_type) caused by the hard validator.

### Check for regressions?

Yes — clear regressions:
1. **Haiku reliability** (N1): 2 new failures from JSON-EOF truncation. Root cause: PR #346 added ~400+ chars per lever (lever_type + decision_axis), pushing haiku over its effective max-tokens limit.
2. **llama3.1 reliability** (N2): 1 new failure from `lever_type='coalition_building'`. Root cause: llama3.1 generated a plausible but non-enumerated type; hard validator rejected it with no fuzzy matching or normalization.

### Verdict: CONDITIONAL

The PR delivers genuine value — `lever_type` and `decision_axis` are useful fields that make levers more actionable and classifiable. The decision_axis content is mostly well-formed and specific. However, two direct reliability regressions were introduced:

1. Haiku's max-tokens limit is now exceeded by the larger lever payloads (fix: increase max_tokens for haiku, or add an output-size estimation step).
2. llama3.1's lever_type validator is too strict — it rejects plausible-but-invalid types (fix: add a fuzzy-normalization pass before hard rejection, or reduce the max_length constraint to encourage shorter, more conformant responses).

These regressions drop overall success rate by 8.6 pp. The PR should be kept only if the max-tokens and validation-tolerance issues are addressed in a follow-up.

---

## Questions For Later Synthesis

**Q1** — What is the `max_tokens` setting for the haiku model in the current runner configuration? The JSON-EOF truncation at columns 29,300 and 43,016 suggests a hard limit around 8,000–10,000 output tokens per call. Was this limit set before PR #346, and has it not been adjusted to account for the larger per-lever payload?

**Q2** — The llama3.1 `lever_type='coalition_building'` failure used no retries (exhausted on attempt 0). Does the runner allow retries for schema validation failures? If so, is the retry budget large enough, and does it use a different seed/temperature on retry?

**Q3** — The haiku "whether" pattern (24% of its levers) is concentrated in the `sovereign_identity` plan. Is this plan genuinely characterized by binary decisions (unlike multi-option plans like `hong_kong_game`)? If so, should the `decision_axis` format guidance allow the "whether" variant, or should it explicitly prohibit it?

**Q4** — The governance bias for gpt-5-nano (35% vs 24% average) is notable but not a failure. Should the system prompt specify a maximum share for any single lever_type (e.g., "no more than 30% of levers should share the same lever_type") to ensure diversity?

**Q5** — The decision_axis field is English-only in its required phrasing ("This lever controls X by choosing between A, B, and C"). When PlanExe receives prompts in non-English languages, will the model respond in the source language, breaking this format check? The current `min_length=20` validator would pass non-English entries, but any downstream consumer that parses "by choosing between" from the text would fail.

---

## Reflect

PR #346 is a well-intentioned schema enhancement. The new fields genuinely improve lever actionability and classification. However, the implementation created two reliability issues that were not caught before merging:

1. The haiku model's responses are now large enough to exceed its max-tokens limit for some plans. This is a systematic, reproducible failure (not stochastic) — the same 2 plans failed, and the surviving 3 plans are also close to the limit.

2. The llama3.1 hard validator for lever_type is too unforgiving. A soft normalization step (mapping similar strings to valid types) would have kept the sovereign_identity plan succeeding.

The deeper concern is the decision_axis format requirement ("by choosing between"). This is a positive pattern — it forces models to name explicit options rather than describing abstract trade-offs. But it is English-only in its validation. For multilingual PlanExe use, this format should be documented as English-only or the validation should be made language-agnostic.

The haiku verbosity problem (consequences 2.4×, review 3.7× baseline) predates this PR but is compounded by it. The extra fields are the proximate cause of the truncation failures, but haiku's underlying verbosity makes it the most at-risk model for any payload increase.

---

## Potential Code Changes

**C1 — Increase haiku max_tokens or add output-size guard** (high priority)
The haiku JSON-EOF failures result from the model's verbose output exceeding the effective response size limit. Either:
- Increase `max_tokens` in the haiku LLM config to accommodate the new fields, OR
- Add a server-side output-size estimation (approximate bytes per lever × expected lever count) that warns if the response is likely to be truncated before making the call.
Evidence: E1, E2. Affects `history/2/30_identify_potential_levers/events.jsonl`.

**C2 — Add lever_type fuzzy normalization before hard rejection** (medium priority)
The current validator rejects any unrecognized lever_type outright. A normalization pass using edit-distance or a small lookup table (e.g., `'coalition_building' → 'operations'`, `'tech' → 'methodology'`) before the hard validator would recover valid levers from stochastic model deviations.
Evidence: E3 — llama3.1 returned `'coalition_building'` for a lever in a coalition-building-heavy project.
Predicted effect: reduce llama3.1 failure rate on plans with atypical terminology; no change to other models.

**C3 — Add decision_axis format note about binary choices** (low priority)
The system prompt section 2 ("Lever Classification") should clarify whether binary decisions ("This lever controls whether...") are acceptable or whether all axes must offer 3+ explicit options. Currently haiku produces the "whether" variant at 24% for binary-decision-heavy plans, and no validator catches this.
Evidence: N5, E5.
Predicted effect: either normalize all axes to the trinary format or explicitly permit the binary "whether" form, eliminating ambiguity.

**C4 — OPTIMIZE_INSTRUCTIONS update: add max-tokens risk warning** (low priority)
The `OPTIMIZE_INSTRUCTIONS` constant should document that adding new fields to per-lever output increases response size and can push verbose models (especially haiku) over their max-tokens limit. This is a new recurring risk not previously documented.
Predicted effect: future analysts will flag max-tokens risk when evaluating PRs that add output fields.

---

## Summary

PR #346 adds `lever_type` and `decision_axis` to the lever schema. The new fields are structurally correct and semantically valuable: 97% of `decision_axis` entries follow the specified format, `lever_type` values are valid for 6/7 models, and the fields add actionable classification information to each lever.

However, the PR introduced **3 new plan-level failures** (a success rate drop of 8.6 pp, from 94.3% to 85.7%):
- 2 haiku failures caused by JSON-EOF truncation (haiku now exceeds max-tokens on some plans due to larger per-lever payloads)
- 1 llama3.1 failure caused by the hard lever_type validator rejecting `'coalition_building'`

Non-haiku models show stable field lengths (all under 2× baseline). Haiku remains a persistent quality concern: consequences 2.44×, review 3.71× above baseline, all above the warning thresholds.

The template leakage problem ("The options [verb]" in review fields) is unchanged at ~50–100% by model — this PR does not address it and the carry-forward issue persists.

**Verdict: CONDITIONAL** — Keep the schema changes but fix haiku max-tokens and lever_type validation tolerance before considering the PR complete. The core additions are sound; the reliability regressions are fixable.
