# Insight Claude

## Scope

Analyzing runs `5/25–5/31` (after PR #479) against `2/87–2/93` (before, analysis 40 baseline)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #479 "Comprehensive prompt refinement: verbatim numbers, template-lock fix, tighter targets"

**PR changes claimed:**
1. Verbatim-numbers rule extended to consequences AND options field descriptions
2. Template-lock fix: "the three options leave unaddressed" → "the proposed options collectively do not resolve" in review_lever field description and section 4/6
3. Positive framing: removed "Do NOT include 'Controls ... vs.'" prohibition
4. Consistent targets: "2–3 sentences" for consequences, "one-sentence" for review, aligned across all descriptions and system prompt
5. Section 5 tighter restriction: "NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context"

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/87 | 5/25 | ollama-llama3.1 |
| 2/88 | 5/26 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/27 | openai-gpt-5-nano |
| 2/90 | 5/28 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/29 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/30 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/31 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### 1. gpt-oss-20b: New template lock on review field
**Before** (run 88): gpt-oss-20b used two patterns: "the options still leave X unaddressed" (most reviews) and "Trade-off: X; gap: Y" (some reviews).
**After** (run 26): The "leaving unaddressed" phrase is gone, but a new formula took its place — 15 out of 17 hong_kong_game reviews follow the pattern:
- "The options do not address the risk that…"
- "None of the options resolve the risk that…"
- "The options fail to mitigate the risk that…"
- "These X strategies reduce Y but do not resolve the risk that…"

The model shifted from "the options still leave X unaddressed" to "The options do not [resolve/address/mitigate] the risk that…". This is template-lock migration, exactly as OPTIMIZE_INSTRUCTIONS warns: "Replacing a copyable opener does not eliminate template lock — weaker models shift to copying subphrases within the new examples."

Evidence: `history/5/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (reviews 1–17 follow this pattern); `history/2/88_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (before).

### 2. qwen3-30b: Regression — new template lock on review field
**Before** (run 90): qwen3-30b reviews were shorter and varied: "Emphasizing recognizable sites risks generic tourism imagery, while uncharted areas may alienate viewers unfamiliar with Hong Kong's geography." — no template lock observable.
**After** (run 28): 9 out of 20 hong_kong_game reviews use "leaves unresolved risk of" or end with "remains unresolved":
- "Balancing iconic location value with operational feasibility creates a risk of either excessive budget overruns or compromised visual storytelling." (OK)
- "Balancing technical authenticity with narrative clarity leaves unresolved risk of alienating audiences through excessive local specificity or diluting thematic impact through abstraction"
- "The tension between local relevance and global marketability leaves unresolved risk of failing to satisfy either audience segment effectively"
- "Synchronizing theatrical and VOD strategies without undermining either channel's value proposition remains unresolved"

This is a NEW template lock that was NOT present in the before run. The PR introduced a regression for qwen3-30b.

Evidence: `history/5/28_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` vs `history/2/90_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### 3. qwen3-30b: Terse, under-specified options
**After** (run 28), qwen3-30b generates options that are only 5–10 words and lack action verbs or strategic specificity, violating the "at least 15 words with an action verb" requirement from Section 6:
- "Prioritize vertical urban structures to heighten claustrophobia"
- "Integrate abandoned industrial zones for dissonant contrasts"
- "Use mirrored surfaces in public spaces to reflect and distort reality"
- "Record ambient city sounds for organic texture"
- "Leverage political neutrality in script to expedite approvals"
- "Hire Hong Kong-based VFX teams to access tax credits"
- "Focus on personal psychological decay over overt societal critique"

These short labels resemble the "NO generic option labels (e.g., 'Optimize X', 'Tolerate Y')" prohibition. The **before** run (run 90) had similar terse options ("Prioritize iconic landmarks to leverage global recognition", "Focus on underutilized urban spaces to emphasize claustrophobia") — so this is a pre-existing issue, not introduced by the PR.

Evidence: `history/5/28_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` levers 14–20.

### 4. gpt-oss-20b: Fabricated percentage numbers in options — regression
**Before** (run 88): gpt-oss-20b used context-adjacent day counts (48-day, 55-day schedule from the plan's stated 45–55 day range) in options. No fabricated percentages were observed.
**After** (run 26): Multiple options contain fabricated percentage allocations not present verbatim in the hong_kong_game project context:
- "Secure a 60% local co-production agreement with the Hong Kong Film Development Fund, locking in tax rebates…"
- "Pursue a 40% foreign equity partnership with a European film studio…"
- "Allocate 20% of total budget to an expanded pre-production phase…"
- "Shift 15% of the budget to a contingency reserve…"
- "Reallocate 10% to a high-end visual effects pipeline…"

The project context mentions "HK$470 million" as a budget figure but nowhere specifies these percentage splits. These are all fabricated. The verbatim-numbers rule in Section 5 of the current prompt ("NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context") is being ignored by gpt-oss-20b.

Evidence: `history/5/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (Budget Allocation lever options) vs `history/2/88_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (no fabricated percentages).

### 5. llama3.1: Residual "leaving unaddressed" in second-call outputs
Run 25 (llama3.1, after PR) shows mixed review patterns. The first set of levers uses natural language, but the second call's levers (levers 9–18) include residual "leaving unaddressed" phrases:
- "This lever introduces trade-offs between creative freedom and operational efficiency, leaving unaddressed the question of how to maintain a cohesive artistic vision amidst decentralized decision-making."
- "This lever highlights the trade-off between critical acclaim and commercial viability, leaving unaddressed the impact of festival selection on long-term audience engagement."

Also, several options in the second call are very short labels rather than full strategic approaches:
- "Empower the Director"
- "Centralize Crew Management"
- "Opt for Venice"
- "Blended Visuals"
- "Aural Storytelling Dominance"

Evidence: `history/5/25_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` levers 9–18.

### 6. "Controls X vs. Y" prohibition was redundant
The PR claims to fix the "Controls X vs Y" pattern in review_lever. However, neither the before runs (87–93) nor the baseline training data's models show this pattern in the runs being analyzed. The pattern was eliminated in an earlier iteration. The PR's removal of the prohibition follows good OPTIMIZE_INSTRUCTIONS practice ("Do NOT add explicit prohibitions naming banned phrases") but has no observable effect.

Evidence: Absence of "Controls " substring in `history/2/87–93_*/outputs/**002-10-potential_levers.json`.

---

## Positive Things

### 1. gpt-4o-mini: Template lock genuinely reduced
**Before** (run 91): gpt-4o-mini reviews ended consistently with "leaving X unaddressed" or "inadequately addressed":
- "Choosing a local director enhances authenticity but may restrict access to globally recognized talent, leaving international marketing strategies unaddressed."
- "A festival launch can build momentum but may delay revenue generation, leaving immediate financial returns unaddressed."

**After** (run 29): The "leaving unaddressed" pattern is gone. Reviews are varied and structurally different:
- "The challenge remains in balancing local authenticity with the need for international marketability, which may not fully align."
- "The risk lies in the potential for audience confusion over multiple release formats, which could dilute the film's impact."
- "The key risk is that an overemphasis on architectural elements could detract from the emotional core of the story."
- "The unresolved risk is that the ensemble cast may dilute the focus on the protagonist's arc if not carefully managed."

The pattern diversity for gpt-4o-mini is meaningfully better after the PR.

Evidence: `history/2/91_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` vs `history/5/29_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### 2. claude-haiku: Consistently high quality, no template lock
**Before** (run 93) and **after** (run 31): claude-haiku produces analytically rich, non-templated reviews. The reviews are specific to each lever's domain and show no copyable opener pattern:
- Run 31: "All three approaches risk alienating audiences who value the original's cathartic redemption arc while failing to guarantee that subversion alone will satisfy newcomers who have no emotional investment in the 1997 version."
- "Overcommitting to verticality as narrative structure may limit locations available within a 45–55 day shoot, forcing expensive set construction to simulate authentic Hong Kong architecture rather than filming in situ."

The consistent quality is evidence that the system prompt changes don't hurt high-capability models. Also, run 31 reviews do NOT use "leaves unresolved" template lock, unlike qwen3-30b.

Evidence: `history/5/31_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### 3. No LLMChatError entries across all 7 after-runs
The events.jsonl shows all 7 models completed without validation errors. The `check_review_format` validator (min 10 chars, no `[]` brackets) passed cleanly for all models in all plans.

Evidence: `analysis/74_identify_potential_levers/events.jsonl` — no `LLMChatError` entries.

### 4. gpt-oss-20b review language is less mechanically repetitive
While gpt-oss-20b developed a new formula ("The options do not resolve/address/mitigate the risk that…"), the reviews are individually meaningful and capture genuinely different risks per lever. Before, many reviews were identical in structure AND substance — e.g., "the options still leave the risk of [same generic budget concern] unaddressed" for multiple levers. After, each review names a specific operational risk tied to the lever's domain.

Evidence: `history/5/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 17 distinct risks named.

### 5. Options field quality improved for gpt-oss-20b
**After** (run 26): gpt-oss-20b options are longer, more strategically specific, and contain action verbs:
- "Launch a city-wide scavenger hunt where participants solve clues tied to film locations, generating organic social media content and deepening pre-release engagement."
- "Adopt a parallel editing workflow, assigning multiple editors to different scenes simultaneously to cut time."

**Before** (run 88): Options were already reasonable but sometimes mixed one-sentence strategic approaches with vague labels. The after run shows more consistent depth.

---

## Comparison

### Template Lock Status Per Model

| Model | Before (runs 87–93) | After (runs 25–31) | Change |
|---|---|---|---|
| llama3.1 | "Not X could result in Y" (call 1); "leaving unaddressed" (call 2) | Mixed; "leaving unaddressed" persists in call 2 | Partial — call 1 improved, call 2 unchanged |
| gpt-oss-20b | "the options still leave X unaddressed" (~10/17) | "The options do not resolve/address the risk that…" (~15/17) | Shifted lock, not eliminated |
| gpt-5-nano | "Key risk: …" prefix (some levers) | "Key risk: …" prefix (same levers) | Unchanged |
| qwen3-30b | No template lock observed | "leaves unresolved risk of…" / "remains unresolved" (~9/20) | Regression — new lock introduced |
| gpt-4o-mini | "leaving X unaddressed" (~10/17) | Varied ("The challenge remains in…", "The risk lies in…") | Improved |
| gemini-2.0-flash | Varied | Varied | Similar |
| claude-haiku | No template lock | No template lock | Maintained |

### Fabricated Numbers Status

| Model | Before | After | Change |
|---|---|---|---|
| gpt-oss-20b | 2–3 context-adjacent day counts | 5–6 fabricated % numbers (20%, 60%, 40%…) | Regression |
| gpt-4o-mini | Mostly none | Mostly none | Unchanged (good) |
| qwen3-30b | Terse options, few numbers | Terse options, few numbers | Unchanged |
| claude-haiku | Option text uses context-specific details | Option text uses context-specific details | Unchanged |

### Review Field Length (hong_kong_game)

| Model | Baseline avg | Before avg (chars) | After avg (chars) | Ratio after/baseline |
|---|---|---|---|---|
| Baseline | ~90 | — | — | 1.0× |
| gpt-oss-20b | ~90 | ~190 | ~165 | 1.8× |
| gpt-4o-mini | ~90 | ~85 | ~95 | 1.1× |
| qwen3-30b | ~90 | ~110 | ~100 | 1.1× |
| claude-haiku | ~90 | ~280 | ~265 | 2.9× |

Note: claude-haiku reviews remain well above 40 words ("one sentence" target), but they were already long before the PR. The baseline training data uses an older format ("Controls X vs. Y. Weakness: …") with shorter reviews (~90 chars), so the ratio is partially an apples-to-oranges comparison — the baseline was generated under different prompt guidance.

### Consequences Field Length (hong_kong_game)

| Model | Baseline avg | Before avg (chars) | After avg (chars) | Ratio after/baseline |
|---|---|---|---|---|
| Baseline | ~280 | — | — | 1.0× |
| gpt-oss-20b | ~280 | ~290 | ~300 | 1.1× |
| gpt-4o-mini | ~280 | ~220 | ~230 | 0.8× |
| qwen3-30b | ~280 | ~230 | ~230 | 0.8× |
| claude-haiku | ~280 | ~430 | ~450 | 1.6× |

Consequences are within acceptable range (below 2× for all models). No evidence of inflation.

---

## Quantitative Metrics

### Template Lock Counts (hong_kong_game, review field)

| Model | Run (before) | Lock count / total levers | Pattern | Run (after) | Lock count / total levers | Pattern |
|---|---|---|---|---|---|---|
| llama3.1 | 2/87 | ~4/18 call-2 | "leaving unaddressed" | 5/25 | ~4/18 call-2 | "leaving unaddressed" |
| gpt-oss-20b | 2/88 | ~10/17 | "options still leave X unaddressed" | 5/26 | ~15/17 | "do not resolve/address the risk that" |
| qwen3-30b | 2/90 | 0/15 | none | 5/28 | ~9/20 | "leaves unresolved risk of" |
| gpt-4o-mini | 2/91 | ~10/17 | "leaving X unaddressed" | 5/29 | ~2/17 | varied |
| claude-haiku | 2/93 | 0/17 | none | 5/31 | 0/17 | none |

### Fabricated Number Counts (hong_kong_game, consequences + options)

| Model | Run (before) | Fabricated numbers | Run (after) | Fabricated numbers |
|---|---|---|---|---|
| gpt-oss-20b | 2/88 | 2–3 (derived day counts) | 5/26 | 5–6 (fabricated % splits) |
| gpt-4o-mini | 2/91 | 0 | 5/29 | 0 |
| qwen3-30b | 2/90 | 0 | 5/28 | 1 (70%, 30% crew split) |
| claude-haiku | 2/93 | 0 | 5/31 | 0 |

### Lever Count and Uniqueness (hong_kong_game)

| Model | Run (before) | Lever count | Unique names | Run (after) | Lever count | Unique names |
|---|---|---|---|---|---|---|
| gpt-oss-20b | 2/88 | 17 | 17 | 5/26 | 17 | 17 |
| gpt-4o-mini | 2/91 | 17 | 17 | 5/29 | 17 | 17 |
| qwen3-30b | 2/90 | 15 | 15 | 5/28 | 20 | 20 |
| claude-haiku | 2/93 | 17 | 17 | 5/31 | 17 | 17 |

All models produce unique lever names within their own run. No exact-match duplicates observed after deduplication.

### Constraint Violations (all plans, all current runs 25–31)

| Constraint | Before runs | After runs | Change |
|---|---|---|---|
| Levers with < 3 options | 0 (estimated) | 0 | None |
| LLMChatError / ValidationError | 0 | 0 | None |
| Square-bracket placeholders in review | 0 | 0 | None |
| Review < 10 chars | 0 | 0 | None |

---

## Evidence Notes

- **Template lock migration (gpt-oss-20b)**: `history/5/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — reviews 1–17 all follow "The options do not [resolve/address/mitigate] [the risk that / the challenge of / the uncertainty that]" pattern.
- **qwen3-30b regression**: `history/5/28_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — levers 7–20 show "leaves unresolved risk of…" or "remains unresolved" endings. Compare to `history/2/90_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` which has no such pattern.
- **gpt-oss-20b fabricated %**: `history/5/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — Budget Allocation lever: "Allocate 20% of total budget…", "Shift 15% of the budget…", "Reallocate 10%…"; Financing Architecture lever: "60% local co-production", "40% foreign equity". None of these % values appear in the project context.
- **gpt-4o-mini improvement**: Compare `history/2/91_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (all reviews end "leaving X unaddressed") with `history/5/29_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (varied conclusions).
- **llama3.1 second-call residual lock**: `history/5/25_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — levers 9–18 include "leaving unaddressed the question of…" and very short option labels ("Empower the Director", "Opt for Venice", "Blended Visuals").
- **Events log**: `analysis/74_identify_potential_levers/events.jsonl` — no LLMChatError entries; all 7 models complete within 6.5 minutes.
- **Source file**: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` — confirms current system prompt wording and field descriptions.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (lines 27–93 of `identify_potential_levers.py`) is accurate and up-to-date. It already documents:
- "Template-lock migration" (added in PR #358): confirmed by qwen3-30b regression
- "Single-example template lock": the system prompt uses 3 diverse examples
- "Fragile English-only validation": the current `check_review_format` validator is structural-only (length + no brackets)
- "Verbosity amplification": haiku's consequences are 1.6× baseline but stable; no new overflow

**New problem to add to OPTIMIZE_INSTRUCTIONS**: The current examples in Section 4 each contain domain-specific compound nouns ("idle-wage burden during the 5-month off-season", "IRB approval, site-initiation visit, and staff credentialing") that are structurally distinctive. However, the field description itself — "that the proposed options collectively do not resolve" — is still a copyable phrase. Weaker models (qwen3-30b, gpt-oss-20b) are picking up on this phrasing and producing variants. The description phrase is functionally a fifth template instruction. The fix: rewrite the field description to describe the GOAL without using the output sentence structure as the description itself.

**Proposed addition to OPTIMIZE_INSTRUCTIONS**:
```
- Field-description copy. The review_lever description phrase "the proposed options
  collectively do not resolve" is itself a copyable template. Models paraphrase it
  into "the options still leave… unresolved", "leaves unresolved risk of…", or "do not
  resolve/address/mitigate the risk that…". Rewrite the description to specify WHAT
  to identify (e.g., "State the operational or structural gap that would persist
  even if all three options were executed in full.") rather than a sentence starting
  point that models copy and vary.
```

---

## PR Impact

### What the PR Was Supposed to Fix

1. Arithmetic-derivation loophole: models fabricating numbers not in the project context
2. Template lock "the three options leave unaddressed" → replace with "the proposed options collectively do not resolve"
3. Remove "Do NOT include 'Controls ... vs.'" prohibition (positive framing)
4. Consistent 2–3 sentence / one-sentence targets across all field descriptions
5. Section 5 hard prohibition on derived/estimated figures

### Before vs After Comparison Table

| Metric | Before (runs 87–93) | After (runs 25–31) | Change |
|---|---|---|---|
| gpt-oss-20b review template lock rate | ~10/17 ("options still leave X unaddressed") | ~15/17 ("options do not resolve/address the risk") | Shifted lock, rate INCREASED |
| qwen3-30b review template lock rate | 0/15 | ~9/20 ("leaves unresolved") | Regression — new lock |
| gpt-4o-mini review template lock rate | ~10/17 ("leaving X unaddressed") | ~2/17 (varied) | Improved |
| claude-haiku template lock rate | 0/17 | 0/17 | Maintained |
| gpt-oss-20b fabricated % numbers (options) | 0 | 5–6 | Regression |
| qwen3-30b fabricated % in options | 0 | 1 | Slight regression |
| gpt-4o-mini fabricated numbers | 0 | 0 | Maintained |
| LLMChatError / validation failures | 0 | 0 | Maintained |
| "Controls X vs Y" pattern | Already absent | Absent | No change |
| Consequences field length (avg) | Within 2× baseline | Within 2× baseline | Maintained |
| Review field length (avg) | Within 2× baseline (exc. haiku) | Within 2× baseline (exc. haiku) | Maintained |

### Did the PR Fix the Targeted Issues?

**Template lock**: Partially. The specific "the three options leave unaddressed" phrase was eliminated for gpt-4o-mini. For gpt-oss-20b, a new lock emerged immediately. For qwen3-30b, a new lock was introduced that wasn't present before. The fix works for higher-quality models (haiku was already lock-free; gpt-4o-mini improved) but fails for mid-tier models.

**Fabricated numbers**: No. The gpt-oss-20b model now generates MORE fabricated % numbers in options than before the PR. The field description instruction ("Use numbers only when the project context provides them directly") and Section 5 prohibition ("NO calculated, derived, or estimated figures") are both present in the current prompt but gpt-oss-20b ignores them.

**"Controls X vs Y"**: No observable effect (already absent in before runs).

**Consistent targets**: Reviews appear to be single-sentence more consistently across models, though haiku continues to write multi-sentence reviews (2–4 sentences, ~250–280 chars) that exceed the 40-word target.

### Regressions Introduced

1. **qwen3-30b**: New template lock "leaves unresolved risk of…" not present in the before run. The PR made this model worse.
2. **gpt-oss-20b**: New fabricated % numbers in options (60%, 40%, 20%, 15%, 10%). The PR made this model worse on number accuracy.

### Verdict: CONDITIONAL

The PR delivers a genuine improvement for gpt-4o-mini (template lock reduced from ~60% to ~12%) but introduces regressions for qwen3-30b (new template lock) and gpt-oss-20b (new fabricated percentages). The verbatim-numbers rule is being ignored by the models most likely to fabricate numbers. The "Controls X vs Y" fix was already handled in a prior iteration. Before merging, the field description should be rewritten to avoid propagating a copyable phrase ("the proposed options collectively do not resolve") as the template for review_lever outputs.

---

## Questions For Later Synthesis

1. **Q1**: Is the gpt-oss-20b fabricated-% regression consistent across plans (silo, gta_game, parasomnia_research_unit) or only observed in hong_kong_game? If it's plan-specific, it may be triggered by the budget figure (HK$470 million) in that plan context.

2. **Q2**: qwen3-30b's "leaves unresolved risk of…" pattern — is this from the field description phrase "the proposed options collectively do not resolve", or from the examples in Section 4? If it's from the examples, adding a fourth example with entirely different sentence structure may break the lock.

3. **Q3**: claude-haiku (run 31) reviews are 2–3 sentences at ~250+ chars, consistently exceeding the "one sentence (20–40 words)" target. The Section 6 instruction says "Keep each review_lever to one sentence (20–40 words)." Should the system prompt add a hard word-count example ("e.g., this review is 28 words") to calibrate haiku? Or should haiku's multi-sentence output be accepted as acceptable quality variance?

4. **Q4**: The `check_review_format` validator only enforces minimum length (10 chars) and no brackets. Should a maximum length check (e.g., warn or reject reviews > 200 chars) be added to enforce the "one sentence" target for all models?

5. **Q5**: The `OPTIMIZE_INSTRUCTIONS` notes "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template." Is there evidence that the removal of "Do NOT include 'Controls ... vs.'" (in this PR) actually prevents that specific phrase from appearing in outputs? Or was the pattern already absent for other reasons?

---

## Reflect

The PR bundled five independent changes, making it harder to isolate which change caused which effect. The template-lock improvement for gpt-4o-mini is likely due to removing "leave unaddressed" from the field description. The qwen3-30b regression is likely a new template lock triggered by the phrase "collectively do not resolve" in the updated description. The gpt-oss-20b fabricated-% regression may be triggered by the explicit percentage-related prohibitions in Section 5 — the model sees "NO calculated, derived, or estimated figures" as implicitly allowing figures from context, and then interprets budget-related context as permission to generate percentage allocations.

The bundled-PR approach meant that a beneficial change (gpt-4o-mini improvement) and two regressions (qwen3-30b lock, gpt-oss-20b fabricated %) coexist. Splitting the bundle would have made these interactions more observable.

The most actionable finding: the `review_lever` field description is still driving template lock via the phrase "collectively do not resolve". This phrase needs to be replaced with goal-oriented language (what information should be present) rather than sentence-structural language (how the sentence should start or end).

---

## Potential Code Changes

**H1 (Prompt)**: Rewrite the `review_lever` field description to avoid copyable sentence structure. Current: "One sentence (20–40 words): identify the key risk or constraint that the proposed options collectively do not resolve." Proposed: "One sentence (20–40 words): state the operational or structural gap that would persist even if all three options were executed in full." — removes "the proposed options collectively do not resolve" as a copyable template opener.

**H2 (Prompt)**: For models that generate fabricated % numbers despite explicit prohibitions (gpt-oss-20b), add a worked example in Section 5 showing a GOOD example without numbers and a BAD example with fabricated numbers: "BAD: 'Allocate 20% of the budget to X.' (20% is not in the project context) GOOD: 'Allocate a portion of the contingency budget to X.'". Concrete examples of what NOT to do outperform abstract prohibitions for mid-tier models.

**H3 (Prompt)**: Add a fourth review example to Section 4 that uses a completely different rhetorical structure — e.g., one that begins with a subject noun (not a verb or "The options"), states the mechanism, and names the unresolved constraint. This would break qwen3-30b's lock on the existing three examples without requiring a field description change.

**C1 (Code)**: Add a soft warning (log-level warning, not validation failure) when a review field exceeds 80 words or contains phrases like "leaving unaddressed", "leaves unresolved", "do not resolve/address" more than once across the levers array. This would catch template lock patterns automatically in CI or pipeline monitoring without breaking successful runs.

---

## Summary

PR #479 produces a **genuine improvement for gpt-4o-mini** (template lock rate dropped from ~60% to ~12% for review_lever) but introduces **two regressions**: (1) qwen3-30b developed a new "leaves unresolved risk of…" template lock not present in the before run; (2) gpt-oss-20b now generates fabricated percentage splits in option text (5–6 fabricated % numbers per plan) where the before run had none. The verbatim-numbers rule in Section 5 is being ignored by gpt-oss-20b.

The core issue is that the `review_lever` field description continues to provide a copyable sentence template — the phrase "the proposed options collectively do not resolve" migrated into model outputs as template lock. The positive change (removing "the three options leave unaddressed") reduced lock for one model but triggered lock in another.

Verdict: **CONDITIONAL** — keep the gpt-4o-mini improvement, but fix the field description to remove the new copyable phrase and add a worked counter-example for fabricated numbers before treating this PR as fully complete.
