# Insight Claude

## Analysis Scope

- **Prompt**: `prompts/identify_potential_levers/prompt_6_4669db379cfa31fb66e4098add8d6b3d289c78811ce02760d8ac74cedded53de.txt`
- **History runs**: `1/60` through `1/66` (7 runs, 5 plans each, various models)
- **Baseline**: `baseline/train/` (5 plans)
- **No PR registered** in `meta.json`; PR Impact section is omitted.

### Model assignments

| Run | Model | Workers |
|-----|-------|---------|
| 60 | ollama-llama3.1 | 1 (sequential) |
| 61 | openrouter-openai-gpt-oss-20b | 4 |
| 62 | openai-gpt-5-nano | 4 |
| 63 | openrouter-qwen3-30b-a3b | 4 |
| 64 | openrouter-openai-gpt-4o-mini | 4 |
| 65 | openrouter-gemini-2.0-flash-001 | 4 |
| 66 | anthropic-claude-haiku-4-5-pinned | 4 |

---

## Negative Things

### N1 — Run 60 (llama3.1): Severe Semantic Duplication

`history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
shows 24 levers where at least 8 are semantically near-duplicate:

- "Digital Identity Standards" → "Digital Identity Standards Harmonization" → "Digital Identity Standards Enforcement" → "Digital Identity Standards Development" (4 levers on the same topic)
- "Digital Identity Procurement Reform" ↔ "Digital Identity Procurement Innovation" (options are near-identical: "Streamline the procurement process through electronic tendering", "Create a centralized procurement agency")
- "Digital Identity Research Initiative" ↔ "Digital Identity Research and Development" (same three options verbatim)
- "Digital Identity Skills Certification" ↔ "Digital Identity Skills Development" (same three options verbatim)

The exact-name deduplication in `identify_potential_levers.py` (lines 333–336) catches only exact name matches. When calls 2 and 3 are told "do not reuse these names", the model appends qualifiers ("Harmonization", "Enforcement", "Development") to generate technically different names that are conceptually identical. The downstream `DeduplicateLeversTask` must then handle these; if its semantic threshold is too loose, they propagate.

### N2 — Run 60 (llama3.1): Partial Recovery (2/3 calls) on Two Plans

`history/1/60_identify_potential_levers/events.jsonl`:
```
{"event": "partial_recovery", "plan_name": "20250321_silo", "calls_succeeded": 2, "expected_calls": 3}
{"event": "partial_recovery", "plan_name": "20260311_parasomnia_research_unit", "calls_succeeded": 2, "expected_calls": 3}
```

For these two plans, only 2 of 3 LLM calls succeeded; the failed call was silently skipped (code lines 312–318). This reduces the lever pool to ~10–14 levers before dedup instead of the expected ~15–21. No `LLMChatError` event was logged at the run level, confirming the failure was model-side (likely JSON parse or structured output failure from llama3.1), not a Pydantic schema validation rejection.

### N3 — Option Verbosity Extremes: Terse Labels vs. Overly Long Options

Two opposite failure modes observed across models:

**Too terse (llama3.1, parasomnia)** — `history/1/60_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`:
```
"options": [
  "Targeted social media campaigns with patient advocacy groups",
  "Collaborate with local community centers for outreach and education",
  "Partner with sleep disorder support groups for referrals"
]
```
These are ~50–60 chars each — closer to labels than strategic sentences. The prompt requires "a full sentence with an action verb" and "at least 15 words"; these average ~10 words.

**Too verbose (haiku, hong_kong_game)** — `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
```
"options": [
  "Recruit a Hong Kong or Southeast Asian noir/thriller director with proven box-office or festival credentials who has shot extensively in dense urban environments and understands Hong Kong's architectural and social textures intimately",
  ...
]
```
~230 chars per option (~1.5× baseline). Not a quality regression — the content is substantive — but the length range across models is 50–230 chars.

### N4 — Review Field Formula Repetition (run 60, llama3.1)

Multiple levers in `history/1/60_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` use nearly identical review sentences:
- "This lever governs the tension between standardization and innovation, but the options overlook potential lock-in effects."
- "This lever governs the tension between public awareness and misinformation, but the options overlook potential information overload."

Both appear twice (for near-duplicate lever pairs). Reviews add no new analytical insight when the lever pair is itself a duplicate. This is a symptom of N1 rather than an independent problem.

### N5 — Conservative Path Often Missing in llama3.1 Options

`OPTIMIZE_INSTRUCTIONS` states: "Each lever's options should include at least one conservative, low-risk path."

In `history/1/60_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, several levers offer only varying intensities of the same approach:
- "Implement advanced surveillance systems" / "Focus on community-based security measures" / "Implement a hybrid approach" — the "hybrid" is not a genuinely conservative path; it blends the other two. A truly conservative option (e.g., "Maintain current manual oversight with no new surveillance investment") is absent.

Claude haiku (run 66) and gpt-5-nano (run 62) generally include genuine conservative options in their lever sets.

---

## Positive Things

### P1 — Fabricated Percentages Eliminated

Prompt_6 has successfully removed the fabricated numeric claims that plagued the baseline and earlier iterations.

Baseline `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`:
> "Immediate: Viewer disorientation → Systemic: **15%** higher audience engagement due to novelty → Strategic: Increased critical acclaim"
> "Immediate: Increased media attention → Systemic: **20%** higher pre-sales based on star power"
> "Immediate: Initial box office performance → Systemic: **30%** increase in streaming revenue"

Current runs (all 7): zero fabricated percentages across all plans examined. The explicit prohibition in prompt_6 and `OPTIMIZE_INSTRUCTIONS` is working.

### P2 — No Marketing Language

No instances of "game-changing", "revolutionary", "cutting-edge", "breakthrough", or "disruptive" observed in any of the 7 runs. The prohibition in prompt_6 Section 5 is effective.

### P3 — No Schema Validation Failures (LLMChatError)

None of runs 60–66 produced `LLMChatError` entries in their `events.jsonl`. The removal of the `max_length=7` hard cap on the `levers` field (documented in AGENTS.md) has eliminated the class of validation failures seen in earlier iterations. All 7 runs completed with structural compliance.

### P4 — High Content Quality in haiku and gpt-5-nano

`history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (haiku) shows 21 levers that are:
- All semantically distinct (no exact-name or semantic duplication detectable)
- Grounded in specific project context: cites HK$470M budget, Universal IP rights, TIFF/BIFF festivals, 8–10 week photography schedule
- Options are concrete strategic sentences with action verbs, averaging ~220 chars (1.4× baseline ~155 chars per option), but the extra length contains genuine decision-relevant specificity

`history/1/62_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` (gpt-5-nano) also shows 19 highly specific levers grounded in AltID/MitID context.

### P5 — Review Field Structural Compliance

All examined outputs follow the two-sentence format: (1) name tension, (2) identify weakness. No bracket placeholders observed. The structural validator (min length 20 chars, no `[…]`) is working without relying on English keywords ("Controls", "Weakness:").

---

## Comparison

### Lever Count vs. Baseline

| Plan | Baseline | Run 60 (llama) | Run 62 (gpt-5-nano) | Run 63 (qwen3) | Run 66 (haiku) |
|------|----------|----------------|---------------------|-----------------|-----------------|
| hong_kong_game | 14 | 18 | — | — | 21 |
| silo | 14 | 11 (2/3 calls) | — | 14 | 20 |
| sovereign_identity | 14 | 24 | 19 | — | — |
| parasomnia | 14 | 11 (2/3 calls) | — | — | — |

All runs produce more levers than the baseline 14. This is expected per `OPTIMIZE_INSTRUCTIONS`: "Over-generation is fine; step 2 handles extras." However, run 60's sovereign_identity at 24 contains ~8 semantic duplicates, not handled by exact-name dedup.

### Field Length Ratios vs. Baseline

**Consequences** (sampled, chars):

| Source | Plan | Sample Mean | Ratio vs. Baseline |
|--------|------|-------------|-------------------|
| Baseline | hong_kong_game | ~250 | 1.0× (reference) |
| Baseline | silo | ~250 | 1.0× (reference) |
| Run 60 (llama) | hong_kong_game | ~230 | 0.9× |
| Run 60 (llama) | silo | ~210 | 0.8× |
| Run 62 (gpt-5-nano) | sovereign_identity | ~220 | 0.9× |
| Run 66 (haiku) | hong_kong_game | ~480 | 1.9× |
| Run 66 (haiku) | silo | ~400 | 1.6× |

Ratios are well below the 2× warning threshold for most models. Haiku is approaching 2× for consequences but does not appear to be verbosity-without-substance — the extra length contains project-specific detail (budgets, timelines, stakeholder names). This is acceptable per guidance.

**Options** (sampled, chars per option):

| Source | Plan | Sample Mean | Ratio vs. Baseline |
|--------|------|-------------|-------------------|
| Baseline | hong_kong_game | ~155 | 1.0× (reference) |
| Run 60 (llama) | hong_kong_game | ~90 | 0.6× (too terse) |
| Run 60 (llama) | parasomnia | ~55 | 0.4× (label-length) |
| Run 62 (gpt-5-nano) | sovereign_identity | ~130 | 0.8× |
| Run 66 (haiku) | hong_kong_game | ~220 | 1.4× |

Llama3.1 options are well below baseline length and are often labels rather than strategic sentences.

**Review fields** (sampled, chars):

| Source | Sample Mean | Ratio vs. Baseline |
|--------|-------------|-------------------|
| Baseline | ~145 | 1.0× (reference) |
| Run 60 (llama) | ~185 | 1.3× |
| Run 62 (gpt-5-nano) | ~175 | 1.2× |
| Run 66 (haiku) | ~320 | 2.2× |

Haiku reviews exceed 2× but contain substantive critique rather than filler. Run 60 reviews are slightly padded but structurally compliant.

### Content Quality Tier Ranking

1. **Best**: Run 66 (haiku) — specific, grounded, semantically unique, long but substantive
2. **Good**: Run 62 (gpt-5-nano) — clean, specific, no duplication
3. **Adequate**: Runs 63, 64, 65 (qwen3/gpt-4o-mini/gemini) — moderate quality, expected output count
4. **Weak**: Run 60 (llama3.1) — partial recovery, semantic duplication, terse/label options

---

## Quantitative Metrics

### Uniqueness Table (run 60 sovereign_identity — worst case)

24 levers in final output. Semantic clustering:

| Semantic cluster | Lever names |
|-----------------|-------------|
| Standards (×4) | Digital Identity Standards / Standards Harmonization / Standards Enforcement / Standards Development |
| Procurement (×2) | Procurement Reform / Procurement Innovation |
| Research (×2) | Research Initiative / Research and Development |
| Skills (×2) | Skills Certification / Skills Development |
| Awareness (×2) | Awareness Campaign / Awareness and Education |
| Data Governance (×2) | Data Governance / Data Sharing Framework |

**Unique semantic concepts**: ~14; **Total levers**: 24; **Uniqueness ratio**: 58%.

### Uniqueness Table (run 66 haiku hong_kong_game — best case)

21 levers, all semantically distinct. **Uniqueness ratio**: ~100%.

### Fabricated Quantification Count

| Source | Fabricated % claims |
|--------|---------------------|
| Baseline train (all 5 plans) | 40+ instances (15%, 20%, 30%, 50%, 40%…) |
| Runs 60–66 (all plans) | **0** |

### Template Leakage / Review Formula Repetition

| Run | Review formula "This lever governs the tension between X and Y, but the options overlook Z" (approx.) |
|-----|------|
| Run 60 (llama) | ~85% of levers use this exact sentence structure |
| Run 66 (haiku) | ~60% use this structure; ~40% vary |
| Run 62 (gpt-5-nano) | ~70% use this structure |

This is within acceptable range — the prompt explicitly recommends this format — but models should be encouraged to vary the framing to avoid all reviews sounding identical.

### Constraint Violations

| Check | Count (all runs) |
|-------|-----------------|
| Options ≠ 3 per lever | 0 |
| Review with `[…]` placeholders | 0 |
| Review < 20 chars | 0 |
| LLMChatError events | 0 |
| Partial recovery events | 2 (run 60 only: silo, parasomnia) |

---

## Evidence Notes

1. **Semantic duplication root cause**: `identify_potential_levers.py` lines 268–276: calls 2 and 3 receive `f"Generate 5 to 7 MORE levers with completely different names. Do NOT reuse any of these already-generated names: [{names_list}]"`. The constraint is on **names only**, not on concepts/topics. When llama3.1 generates call 2 levers, it appends qualifiers to already-used names, producing technically different names for semantically identical levers.

2. **Exact-name dedup in code** (lines 329–346): `if lever.name in seen_names: continue` — only exact string match. Does not catch "Digital Identity Standards" vs "Digital Identity Standards Enforcement".

3. **Run 60 partial recovery**: `events.jsonl` shows `calls_succeeded: 2, expected_calls: 3`. Code lines 312–318 allow continuation when at least one prior call succeeded. No `LLMChatError` in events means failure was silently absorbed.

4. **Anti-fabrication working**: Baseline `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` shows "Systemic: 15% increased policy traction due to concrete evidence", "Systemic: 20% greater likelihood of influencing AltID requirements", "Systemic: 30% stronger advocacy position". All current runs: clean.

5. **Over-generation explicitly intentional**: `identify_potential_levers.py` docstring lines 4–5: "Don't focus on hitting exactly 15 levers. It's more important that there is 15..20 levers." And `OPTIMIZE_INSTRUCTIONS`: "Over-generation is fine; step 2 handles extras." So 14–21 levers in output is expected behavior, not a bug — unless the dedup in step 2 fails to clean them.

---

## Questions For Later Synthesis

1. **How effective is `DeduplicateLeversTask` at semantic dedup?** The output files examined (`002-10-potential_levers.json`) are the result of step 1 only (exact-name dedup). Step 2 (semantic dedup) runs later in the full pipeline. If the semantic dedup threshold catches the 4-way "Digital Identity Standards" cluster, then N1 is a pre-dedup artifact with no downstream impact. If it doesn't, it propagates to `EnrichLevers` and `FocusOnVitalFewLevers`.

2. **Should the anti-repetition prompt be strengthened to concept-level?** Rather than "Do NOT reuse any of these already-generated names", changing to "Do NOT reuse any of these already-generated topics or concepts" (with the lever names as examples) might reduce semantic duplication without requiring code changes.

3. **Is llama3.1 worth supporting?** Run 60 has partial recovery on 2/5 plans, severe semantic duplication on sovereign_identity, and terse/label-like options. If the runner is intended to test prompt quality across models, llama3.1's output quality makes it difficult to interpret as a signal about prompt quality. Is this model still in the intended test matrix?

4. **Should the runner output files be `002-10` (post-step-1) or post-step-2 (post-dedup)?** Analysis is currently comparing pre-dedup lever counts and uniqueness. It would be more informative to compare post-dedup outputs if those are available in the history runs.

---

## Reflect

Prompt_6 has achieved its primary goals: fabricated percentages and marketing language are eliminated across all 7 runs and all 5 plans. This is a clear improvement over the baseline training data.

The main remaining quality gap is model-dependent rather than prompt-dependent: llama3.1 (run 60) produces semantic duplicates due to the name-only anti-repetition mechanism in the code, and generates terse options that don't meet the "complete strategic sentence" bar. Claude haiku (run 66) and gpt-5-nano (run 62) produce high-quality outputs with the current prompt.

The code's "name-only" anti-repetition approach (C1 below) is the most actionable finding that would benefit all models, not just llama3.1.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current `OPTIMIZE_INSTRUCTIONS` (in `identify_potential_levers.py` lines 27–68) covers:
- Realistic/feasible/actionable plans ✓
- Optimism bias / conservative options ✓
- Fabricated numbers ✓ (working)
- Hype/marketing copy ✓ (working)
- Vague aspirations ✓
- Fragile English-only validation ✓ (validator uses structural checks only)

**Gap not yet covered**: The anti-repetition mechanism passes lever names to calls 2 and 3, but the instruction says only "completely different **names**". A model that appends qualifiers to reuse the same concept is technically compliant with the instruction. OPTIMIZE_INSTRUCTIONS should add:

> - **Name-only anti-repetition bypass**: When calls 2 and 3 are instructed to avoid already-generated lever names, models may append qualifiers ("Harmonization", "Enforcement", "Development") to generate technically distinct names for semantically identical levers. The repeated-names list prevents exact-name reuse but not concept reuse. Consider changing the inter-call instruction to prohibit topic reuse, not just name reuse.

---

## Potential Code Changes

**C1 — Concept-level anti-repetition in inter-call prompt**

*File*: `identify_potential_levers.py`, lines 268–276

*Current*:
```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    ...
)
```

*Proposed*:
```python
topic_summary = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 to 7 MORE levers covering entirely different strategic topics and concepts. "
    f"Do NOT generate levers that address the same topic as any of these already-generated levers, "
    f"even under a different name: [{topic_summary}]\n"
    ...
)
```

*Evidence*: Run 60 sovereign_identity has 4 near-identical levers on "Digital Identity Standards" with names "…Standards", "…Standards Harmonization", "…Standards Enforcement", "…Standards Development". These are all technically "different names" but the exact-name filter doesn't catch them. The downstream DeduplicateLeversTask should catch them, but the pre-dedup lever count of 24 is wasteful for models like llama3.1 that produce lower-quality completions.

*Expected effect*: Reduces semantic duplication in calls 2 and 3, especially for weaker models. Would reduce the burden on DeduplicateLeversTask to catch concept-level duplicates.

**C2 — Add a conservative-path requirement to the inter-call prompt**

*File*: `identify_potential_levers.py`, lines 268–276

*Current inter-call instruction*: Does not repeat the conservative-path requirement from `OPTIMIZE_INSTRUCTIONS`.

*Proposed*: Append to the inter-call prompt: `"Each lever must include at least one explicitly conservative, low-risk option — not just a 'balanced' or 'hybrid' approach."`

*Evidence*: Run 60 silo levers ("Surveillance and Security Measures", "Information Control and Propaganda") have options that offer hybrid/moderate choices but not a genuinely conservative baseline option (e.g., "Continue with current practices while documenting issues"). This is an `OPTIMIZE_INSTRUCTIONS` violation observed specifically in llama3.1 outputs.

*Expected effect*: Improves downstream scenario diversity by ensuring conservative paths survive into ScenarioSelection.

---

## Hypotheses

**H1 — Changing "different names" to "different topics/concepts" in inter-call prompt reduces semantic duplication**

*Change*: Inter-call prompt wording (see C1).
*Evidence*: Run 60 sovereign_identity shows 4-way semantic duplication. Run 66 (haiku), which naturally avoids this, likely does so because haiku interprets the anti-repetition instruction more conservatively.
*Predicted effect*: Weaker models (llama3.1, potentially others) produce fewer semantic duplicates; meaningful lever count per plan approaches 15–18 unique concepts.
*Testable by*: Re-running run 60 plans with the modified prompt and comparing semantic duplication rates.

**H2 — Adding "at least one conservative option" reminder to inter-call prompt improves scenario diversity**

*Change*: Append conservative-path reminder to calls 2 and 3 inter-call prompt.
*Evidence*: Run 60 silo has no genuinely conservative option in several lever sets.
*Predicted effect*: Scenario selection downstream includes at least one low-risk scenario across all plans.
*Testable by*: Re-running silo/parasomnia with modified prompt; inspecting ScenarioGeneration output.

**H3 — llama3.1 requires a separate, shorter system prompt to produce strategic sentences (not labels) in options**

*Change*: Prompt-level (not code-level): shorter, simpler phrasing for the option content requirement.
*Evidence*: Run 60 parasomnia options average ~55 chars (label-length). The prompt says "at least 15 words with an action verb" in the inter-call prompt, but this may not be prominent enough.
*Predicted effect*: llama3.1 options meet the length threshold; DeduplicateLeversTask receives more actionable options to score.
*Testable by*: Add an explicit minimum-word-count example ("e.g. 'Establish a dedicated outreach team targeting university sleep labs and neurology departments, beginning with the three closest institutions'") to the inter-call prompt.

**C1 (code)** — See above.
**C2 (code)** — See above.

---

## Summary

Prompt_6 is working as intended on its primary objectives: fabricated percentages and marketing language are eliminated across all 7 runs, and no schema validation failures occurred. The content produced by stronger models (haiku, gpt-5-nano) is well-grounded, specific, and close to 2× baseline field lengths — acceptable given the content quality.

The main remaining problems are:

1. **Semantic duplication** in weaker models (llama3.1): 3 LLM calls with name-only anti-repetition allows concept reuse under different names. A code-level fix (C1) — changing the anti-repetition instruction from "different names" to "different topics" — would reduce this without a prompt change.

2. **Terse options in llama3.1**: Options are label-length (~55 chars) rather than strategic sentences (~150 chars). A prompt-level or inter-call-level reminder with a concrete example (H3) would address this.

3. **Conservative-path gap**: Some lever sets lack a genuinely low-risk option; only hybrid/balanced choices are offered. Adding a conservative-path reminder to calls 2 and 3 (C2/H2) would fix this without changing the system prompt.

No fabricated numbers, no marketing language, and no schema validation failures were observed across all 7 runs. Prompt_6 represents a solid baseline for content quality; the remaining work is code-level (anti-repetition improvements) and prompt-level (minor reinforcements for conservative paths and option length).
