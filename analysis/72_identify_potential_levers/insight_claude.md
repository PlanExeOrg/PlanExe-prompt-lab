# Insight Claude

## Scope

Analyzing runs `5/11–5/17` (after PR #477) against `2/87–2/93` (before, analysis 40 / best.json
baseline) for the `identify_potential_levers` step.

**PR under evaluation:** PR #477 "Qualitative consequences, positive framing, and consistent length targets"

**Changes made by the PR:**

| Change | Target |
|--------|--------|
| Remove all number-evidence constraints | `consequences` field desc + system prompt section 5 |
| Add "NO specific numbers, percentages, or monetary amounts" | Section 5 Prohibitions |
| Add "describe effects qualitatively" | Section 5 Prohibitions |
| Remove "Do NOT include 'Controls ... vs.'" | Positive framing change |
| Set "2-3 sentences" length target everywhere | `consequences` field desc ×2, system prompt |
| Confirm `review_lever` "One sentence (20-40 words)" | Matches section 6 |

**Model mapping:**

| Before run | After run | Model |
|---|---|---|
| 2/87 | 5/11 | ollama-llama3.1 |
| 2/88 | 5/12 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/13 | openai-gpt-5-nano |
| 2/90 | 5/14 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/15 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/16 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/17 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **Haiku percentage claims reduced 70%.** The primary target model (haiku/run 93) had 20 fields
   containing `%` across five plans before; after (run 17) this dropped to 6 — a 70% reduction.
   This is the intended effect of removing number-evidence constraints from the system prompt.
   Evidence:
   - Before: `history/2/93_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
     — 8 pct-claim fields (e.g. "20% unproductive-admission ceiling", "10% of nights for baseline", "40% of data engineer's time")
   - After: `history/5/17_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
     — 2 pct-claim fields (e.g. "20% of scored nights re-scored")

2. **GTA game pct claims eliminated for haiku.** In the silo plan haiku went from 8 → 3, gta_game
   from 3 → 0, parasomnia from 8 → 2. The two remaining pct claim plans (silo and hong_kong_game)
   have domain contexts where the model is drawing numbers from the plan text rather than fabricating.
   Evidence: `history/5/17_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
   — 0 pct claim fields (before run 93 had 3).

3. **Field lengths stable: no verbosity inflation.** The new "2-3 sentences" language did not inflate
   field lengths. Aggregate averages across all 7 new runs are nearly identical to before:
   consequences 298→300 (+0.7%), options 491→484 (-1.4%), review 199→200 (+0.5%).
   All fields remain within 1.1× of the baseline training data (consequences baseline: 279 chars).

4. **Lever name uniqueness maintained.** Cross-run uniqueness is 96-100% per plan (similar to before).
   No new convergence or template-lock pattern introduced.
   Evidence: see Quantitative Metrics section.

5. **Overall pct claims nearly halved.** Across all 7 models the total pct-claim count dropped
   from 23 to 12 (−48%). Even beyond haiku, the distribution is healthier.

6. **Marketing language unchanged/stable.** 17 levers before and 16 after contained marketing
   language (e.g. "game-changing", "cutting-edge"). The PR had no explicit target for this metric,
   and the baseline is already low.

---

## Negative Things

1. **Success rate regression: 3 plan timeouts.** Runs 5/12 (gpt-oss-20b) and 5/13 (gpt-5-nano) each
   had 1–2 plans time out at 600s. Before (runs 2/87–2/93) all 35 plans succeeded. This brings the
   success rate from 100% to 91.4%.
   - Run 12: `20260311_parasomnia_research_unit` — plan timeout 600s
   - Run 13: `20260308_sovereign_identity`, `20250321_silo` — plan timeouts 600s
   Evidence: `history/5/12_identify_potential_levers/events.jsonl`,
   `history/5/13_identify_potential_levers/events.jsonl`.

2. **Positive framing change had no measurable effect.** The PR removes "Do NOT include 'Controls ...
   vs.'" phrasing. However, the "Controls" pattern appeared in 0/633 levers before and 0/647 after.
   The targeted pattern was never present in the comparison baseline (runs 2/87–2/93), which had
   already resolved the "Controls" template lock in an earlier iteration. The change is inert.

3. **Review field length target still largely unmet.** The `review_lever` field targets "One sentence
   (20–40 words)" — roughly 100-200 chars. In the new runs: 1% are under 100 chars, 59% are 100-200
   chars, and 38% exceed 200 chars. For haiku specifically, the average is 310 chars (review field),
   down slightly from 321. The length target is not enforced by any validator — reviews remain
   1.3× the baseline average (152 chars) and 38% exceed the soft cap.

4. **Qwen pct claims unchanged (3→3).** The three pct claims in qwen3-30b (run 14) are identical
   in count to before (run 90). These appear in the same plans (gta_game, silo, parasomnia). The new
   wording did not help qwen. Evidence: both runs show pct claims in `20250321_silo` options.

5. **Silo plan residual fabrication.** The `20250321_silo` plan (an isolated underground habitat
   design project) consistently generates percentage claims in haiku and qwen outputs even after
   the PR. The plan's engineering context (life-support, agricultural closure) may be drawing
   numbers from the document itself or from model priors about engineering tolerances.
   Evidence: `history/5/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
   — "accepting a 3-year delay and 40% construction cost overrun", "50–100% ensures food security".

---

## Comparison

| Metric | Before (2/87–93) | After (5/11–17) | Change |
|--------|-------------------|------------------|--------|
| Plans processed OK | 35/35 | 32/35 | −3 (timeouts) |
| Total levers | 633 | 647 | +14 |
| Pct claims (all models) | 23 | 12 | −48% |
| Pct claims — haiku only | 20 | 6 | −70% |
| Avg consequences (chars) | 298 | 300 | +0.7% |
| Avg options (chars) | 491 | 484 | −1.4% |
| Avg review (chars) | 199 | 200 | +0.5% |
| Review >200 chars | 33% | 38% | +5pp |
| Marketing language levers | 17 | 16 | −6% |
| Cross-run uniqueness (avg) | 97% | 99% | +2pp |
| LLMChatErrors | 0 | 0 | — |

Consequences vs baseline (279 chars): before 1.07×, after 1.08× — both within 2× threshold.
Review vs baseline (152 chars): before 1.31×, after 1.32× — stable.

---

## Quantitative Metrics

### Per-model comparison

| Model | Before OK | Before cons | Before pct | After OK | After cons | After pct |
|-------|-----------|-------------|------------|----------|------------|-----------|
| llama3.1 | 5/5 | 163 | 0 | 5/5 | 196 | 2 |
| gpt-oss-20b | 5/5 | 283 | 0 | 4/5 | 263 | 1 |
| gpt-5-nano | 5/5 | 259 | 0 | 3/5 | 262 | 0 |
| qwen3-30b | 5/5 | 239 | 3 | 5/5 | 220 | 3 |
| gpt-4o-mini | 5/5 | 248 | 0 | 5/5 | 230 | 0 |
| gemini-2.0-flash | 5/5 | 362 | 0 | 5/5 | 346 | 0 |
| claude-haiku-4-5 | 5/5 | 515 | 20 | 5/5 | 560 | 6 |

### Uniqueness per plan (cross-run)

| Plan | Before unique | Before total | After unique | After total |
|------|--------------|-------------|-------------|------------|
| 20250321_silo | 118/124 (95%) | 124 | 123/128 (96%) | 128 |
| 20250329_gta_game | 117/119 (98%) | 119 | 135/136 (99%) | 136 |
| 20260308_sovereign_identity | 133/134 (99%) | 134 | 132/132 (100%) | 132 |
| 20260310_hong_kong_game | 121/125 (96%) | 125 | 125/126 (99%) | 126 |
| 20260311_parasomnia_research_unit | 126/131 (96%) | 131 | 125/125 (100%) | 125 |

### Review field length distribution

| Range | Before count | Before % | After count | After % |
|-------|-------------|----------|-------------|---------|
| <100 chars | 2 | 0% | 9 | 1% |
| 100–200 chars | 422 | 66% | 386 | 59% |
| >200 chars | 209 | 33% | 252 | 38% |

**Note**: the "20-40 word" review target would correspond to ~100-200 chars. The shift toward
>200 chars (+5pp) is a minor regression on this dimension, though the absolute average (200 vs 199)
is unchanged.

---

## Evidence Notes

- Haiku before (2/93) parasomnia: "20% unproductive-admission ceiling", "10% of nights", "40% of data engineer's time", "30% subsample", "20–30% per year", "retention >90%", "roughly 9% of three-year budget"
  — `history/2/93_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`

- Haiku after (5/17) parasomnia: "20% of scored nights re-scored" and ">80% retention"
  — `history/5/17_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
  Both remaining claims appear to reference threshold values from the research protocol, not fabricated percentages.

- Silo plan residual: "40% construction cost overrun", "50–100% ensures food security", "110% of calculated minimum"
  — `history/5/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  These appear domain-grounded (underground habitat engineering), but are still % claims.

- Timeouts confirmed not LLMChatError:
  `history/5/12_identify_potential_levers/events.jsonl`: `"plan timeout after 600s"` for parasomnia
  `history/5/13_identify_potential_levers/events.jsonl`: `"plan timeout after 600s"` for sovereign_identity and silo

- Baseline training data (for ratio comparisons):
  `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` — 15 levers, 279 char avg consequences

---

## PR Impact

### What the PR was supposed to fix

1. Replace all number-evidence constraints with "describe effects qualitatively" — reducing fabricated
   percentages that appeared especially in haiku's outputs.
2. Positive framing: remove "Do NOT include 'Controls ... vs.'" phrasing.
3. Consistent length targets: unify "2-3 sentences" across field desc and system prompt; confirm
   "One sentence (20-40 words)" for `review_lever` in section 6.

The PR explicitly acknowledges that PR #475's "Never invent" constraint made fabrication 4x worse —
models treated the explicit prohibition as a permission floor and derived numbers arithmetically.
This PR removes the number topic entirely rather than prohibiting it.

### Before vs After Comparison

| Metric | Before (2/87–93) | After (5/11–17) | Change |
|--------|-----------------|-----------------|--------|
| Total pct claims (all models) | 23 | 12 | **−48%** |
| Haiku pct claims | 20 | 6 | **−70%** |
| Qwen pct claims | 3 | 3 | 0% |
| Other models pct claims | 0 | 3 | +3 (llama+gptoss) |
| Plans OK | 35/35 (100%) | 32/35 (91.4%) | −8.6pp |
| Avg consequences length | 298 | 300 | +0.7% |
| Avg review length | 199 | 200 | +0.5% |
| "Controls" pattern levers | 0 | 0 | no change |

### Did the PR fix the targeted issue?

**Primary goal (qualitative numbers): YES, partially.** For haiku — the main model exhibiting the
problem — pct claims dropped from 20 to 6 (−70%). The approach of removing the number topic entirely
rather than prohibiting it worked as intended for haiku.

**Secondary goal (Controls positive framing): INERT.** The "Controls" pattern was already absent in
all comparison runs. This change addresses a pattern that had already been resolved in a prior
iteration. It cannot be credited or blamed for anything.

**Tertiary goal (consistent length targets): NEUTRAL.** Field lengths are stable and well within
2× of baseline. No verbosity inflation was introduced. The "2-3 sentences" consistency didn't change
measurable output lengths.

### Regressions

- **Success rate: 3 timeout failures** in models gpt-oss-20b and gpt-5-nano. These are
  `plan timeout after 600s` events (not `LLMChatError`/`ValidationError`), suggesting external
  service latency rather than prompt-induced token inflation. The same models had 0 timeouts before.
  This warrants monitoring but is likely infrastructure noise.

- **Minor: review >200 chars increased +5pp** (33%→38%). The absolute average is unchanged (199→200),
  suggesting a few outlier reviews got longer while most are stable.

- **Minor: llama3.1 pct claims 0→2.** Two new pct claims appeared in llama (silo and parasomnia plans).
  These appear in engineering-domain contexts. Small enough to be noise.

### Verdict: **CONDITIONAL**

The PR's primary goal is achieved: fabricated percentage claims in haiku dropped 70%. Field lengths
remain stable. However:

1. The "Controls" positive framing change had no observable effect — it targeted an already-absent
   pattern.
2. The timeout regression (3 plans) needs one more run to confirm it is infrastructure-only.
3. Qwen3-30b shows no improvement (3→3 pct claims), suggesting qwen3 needs targeted attention.

Recommend: KEEP the number-removal approach (it works for haiku). Monitor timeouts in the next run
before updating `best.json`. If timeouts are absent in a follow-up, upgrade to full KEEP.

---

## Questions For Later Synthesis

1. **Timeout causality**: Are the 3 timeouts in runs 5/12 and 5/13 prompt-induced (token inflation)
   or infrastructure noise? The field lengths didn't change, suggesting the latter — but a follow-up
   run would confirm.

2. **Silo/parasomnia residual pct claims**: The remaining pct claims in haiku (silo/parasomnia) appear
   context-grounded. Should the threshold be "zero tolerence" or "only fabricated claims are bad"?
   If the latter, the silo plan may be generating legitimate engineering numbers.

3. **Qwen3-30b immunity**: Qwen shows no improvement (3→3 pct claims). Is this because qwen ignores
   field-level constraints, or because its pct claims are domain-sourced? Review the specific qwen14 claims.

4. **Review field 38% >200 chars**: The review "One sentence (20-40 words)" target isn't reliably
   enforced. Should a validator be added, or is the current distribution acceptable?

5. **"Controls" pattern provenance**: Which prior PR (before #358) fixed the "Controls" pattern?
   Understanding this would help confirm there's no risk of re-introducing it.

---

## Reflect

The PR's approach of **removing the number topic entirely** rather than prohibiting it is confirmed
effective for haiku. The OPTIMIZE_INSTRUCTIONS already documented "Fabricated numbers" as a known
problem, and the system prompt now has an explicit "NO specific numbers, percentages..." prohibition in
section 5. The field description change ("Exact numbers will be determined further downstream...") adds
positive framing that correctly describes downstream pipeline behavior.

The main limitation of this analysis: the comparison baseline (2/87–93) was already a well-performing
state (100% success, low pct claims from all models except haiku). The PR's improvement is concentrated
in haiku, which is a notable model in practice.

The OPTIMIZE_INSTRUCTIONS constant (`identify_potential_levers.py:27-92`) is up to date and already
documents all observed failure modes. No new items need adding for this PR's findings.

One observation worth flagging: the `review` field (mapped from `review_lever`) shows 38% of levers
exceeding 200 chars despite the "20-40 words" prompt target. The validator (`check_review_format`)
only enforces `>= 10` chars and no square brackets. If concise reviews matter for downstream quality,
a soft cap validator around 250 chars could help — though it risks re-introducing the Pydantic
hard-constraint failure mode documented in OPTIMIZE_INSTRUCTIONS.

---

## Potential Code Changes

**C1**: Add a `max_length` soft cap for `review_lever` validation — but only if implemented as a soft
warning (log), not a hard `ValueError`. The current 38% overrun rate for >200 chars is unlikely to
cause downstream issues, but a logged warning would give visibility without risking retry loops.
*Evidence*: review field length distribution above; OPTIMIZE_INSTRUCTIONS §"Pydantic hard constraints
vs soft prompt guidance" warns against hard caps.

**C2**: Consider adding a second LLM call to re-verify percent-containing `consequences` fields
before finalizing levers. This would catch residual fabricated % claims without changing the system
prompt. Risk: doubles token usage for affected levers.
*Evidence*: 12 pct claims remain even after the PR; several are in silo/parasomnia engineering context.

---

## Summary

PR #477 achieves its primary goal: haiku's fabricated percentage claims drop 70% (20→6) across five
plans. The approach of removing the number topic entirely (replacing explicit "Never invent" prohibition
with "Exact numbers will be determined downstream") is confirmed effective, consistent with the PR
description's diagnosis of PR #475's failure mode.

Field lengths are stable and well within baseline ratios. Lever uniqueness is high and improving.
The "Controls" framing change is inert (pattern was already absent). Three timeout failures
(gpt-oss-20b, gpt-5-nano) need follow-up to confirm they are infrastructure noise.

**Verdict: CONDITIONAL** — primary improvement is real and significant for haiku; timeout regression
needs one more run to confirm infrastructure vs. prompt causality before committing to `best.json`.
