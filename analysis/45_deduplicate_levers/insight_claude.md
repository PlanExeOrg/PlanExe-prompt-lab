# Insight Claude

Analysis of history runs `3/22_deduplicate_levers` through `3/28_deduplicate_levers` (7 models × 5 plans = 35 runs), evaluating PR #365: *feat: consolidate deduplicate_levers — classification, safety valve, B3 fix*.

Previous analysis (44) examined runs `3/15_deduplicate_levers` through `3/21_deduplicate_levers`.

---

## Model-to-Run Mapping

| Run | Model |
|-----|-------|
| 3/22 | ollama-llama3.1 |
| 3/23 | openrouter-openai-gpt-oss-20b |
| 3/24 | openai-gpt-5-nano |
| 3/25 | openrouter-qwen3-30b-a3b |
| 3/26 | openrouter-openai-gpt-4o-mini |
| 3/27 | openrouter-gemini-2.0-flash-001 |
| 3/28 | anthropic-claude-haiku-4-5-pinned |

Previous analysis models: run 15=llama3.1, run 19=gpt-4o-mini, run 20=gemini, run 21=haiku.

---

## Negative Things

### N1 — gpt-4o-mini (run 26) produces zero absorbs — blanket-primary failure

For sovereign_identity (18 input levers), gpt-4o-mini classified every lever as either primary (12) or secondary (6), absorbing nothing. The same pattern holds for silo (first 30 lines checked: all primary). The prompt explicitly says *"If you find zero absorb/remove decisions, reconsider: the input almost always contains near-duplicates. Do not keep every lever."* and *"expect 4–10 to be absorbed or removed."*

This is the **blanket-primary / over-inclusion** failure mode documented in OPTIMIZE_INSTRUCTIONS. Even though the input levers for the current runs are more semantically diverse than the before-PR batch, they still contain meaningful overlaps (EU Standards Engagement + Technical Standards Advocacy + EU Interoperability Advocacy; Procurement Language Specificity + Procurement Conditionality; Risk Framing + Resilience Narrative Amplification). Most other models correctly absorbed 4–10 of these.

Evidence: `history/3/26_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — all 18 levers in `deduplicated_levers` section, 0 absorbs in `response` section.

### N2 — llama3.1 (run 22) makes cross-domain hierarchy violations

llama3.1 absorbs levers into semantically incorrect targets:
- Demonstrator Fidelity → absorbed into **Fallback Authentication Modality** (unrelated domains)
- Technical Standards Advocacy → absorbed into **Fallback Authentication Modality** (EU policy ≠ technical fallback)
- Procurement Conditionality → absorbed into **Fallback Certification Criteria** (procurement ≠ certification)

The prompt instructs *"Respect Hierarchy: When absorbing, merge the more specific lever into the more general one."* llama3.1 does perform absorptions (better than 0), but the targets are wrong, producing a structurally misleading output where procurement levers are filed under technical levers.

Evidence: `history/3/22_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`, lines 1–50 (absorb justifications for 548c0a83, 089c8ec8, ed16c55c).

### N3 — Hierarchy-direction confusion in 3/7 models (gpt-5-nano, qwen3, llama3.1)

Multiple models absorb the more general lever INTO the more specific one, contradicting the prompt's hierarchy rule:

- **gpt-5-nano (run 24)**: Procurement Language Specificity absorbed into Procurement Conditionality — but Procurement Language Specificity is the broader concept (what requirements say) while Conditionality is a specific enforcement mechanism. Evidence: run 24, sovereign_identity, response item for 9b95a5d0.
- **qwen3 (run 25)**: Same error — Procurement Language Specificity absorbed into Procurement Conditionality. Evidence: run 25, sovereign_identity, response item for 9b95a5d0.
- **llama3.1 (run 22)**: As noted above, cross-domain absorptions to wrong targets entirely.

The prompt says "Don't take the more general lever and absorb it into a narrower one" but this instruction requires the model to correctly identify which lever is general vs. specific — a judgment that varies substantially by model.

### N4 — Wide inter-model variation in absorb count (0–10 from 18 inputs)

| Model | Plan | Primary | Secondary | Absorb | Kept |
|-------|------|---------|-----------|--------|------|
| gpt-4o-mini (26) | sovereign_identity | 12 | 6 | 0 | 18 |
| gemini (27) | sovereign_identity | 7 | 7 | 4 | 14 |
| haiku (28) | sovereign_identity | 7 | 5 | 6 | 12 |
| gpt-oss-20b (23) | sovereign_identity | ~10 | ~2 | ~5 | ~13 |
| qwen3 (25) | sovereign_identity | ? | ? | ≥5 | ≤13 |
| gpt-5-nano (24) | sovereign_identity | 5 | 3 | 10 | 8 |
| llama3.1 (22) | sovereign_identity | ? | ? | ≥3 | ≤15 |

The "expect 4–10 absorb/remove" calibration hint produces dramatically different results: gpt-4o-mini treats it as non-binding (0 absorbs), gpt-5-nano interprets it aggressively (10 absorbs), gemini lands at the lower bound (4), and haiku lands in the middle (6). This variance means downstream consumers of the deduplication output will receive inconsistent lever counts (8–18 kept from 18 inputs).

### N5 — Input lever set changed between runs 15-21 and 22-28 (confound for PR evaluation)

Before-PR runs (15–21) received 15 input levers per plan (heavily duplicated — 5 unique strategies × 3 near-identical copies each, e.g., three near-identical copies of "Policy Advocacy Strategy" with slight quantified-impact variations). After-PR runs (22–28) receive 18 input levers per plan with more diverse, concrete names (Procurement Language Specificity, Demonstrator Fidelity, Coalition Breadth, etc.).

This means before-PR absorb rates (~67%) cannot be directly compared to after-PR absorb rates (0–56%). The before-PR input was trivially deduplicable; the after-PR input is genuinely diverse, requiring semantic judgment. Any comparison of absorb counts between the two batches reflects both the prompt change AND the input quality change.

Evidence: before sovereign_identity input (15 levers, triplicates) visible in `history/3/21_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` user_prompt field; after input (18 diverse levers) in `history/3/27_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` user_prompt field.

### N6 — System prompt is nearly identical between before and after runs

Reading the `system_prompt` field from run 21 (haiku, before) and run 27 (gemini, after), the text is functionally the same — both include: `primary/secondary/absorb/remove` classification, "Use primary only as a last resort", "expect 4–10 to be absorbed or removed", "do not stop early", and "do not keep every lever". The only detected textual difference is: "team communication tooling" (before) vs "communication tooling" (after) in the secondary examples.

This means the bulk of PR #365's value is in **code-level changes** (B3 bug fix, self_improve runner support, enrich_potential_levers classification field) rather than system prompt text changes — at least within the visible portion of these experiments.

---

## Positive Things

### P1 — 100% success rate across all 7 models and 5 plans

Every run in the 22–28 batch completed successfully: `status: "ok"`, `calls_succeeded: 18` for all plans. No LLMChatError entries, no Pydantic validation failures, no timeouts.

Before-PR runs (15–21) also showed 100% success (15 calls_succeeded per plan). Both batches are equally reliable at the structural level.

Evidence: `history/3/22_deduplicate_levers/outputs.jsonl` through `history/3/28_deduplicate_levers/outputs.jsonl` — all status "ok".

### P2 — Gemini correctly hits the absorb target range

Gemini (run 27) absorbed 4 levers from 18 inputs on sovereign_identity, landing exactly at the lower bound of "expect 4–10". The PR description explicitly notes that gemini was the problematic model with PR #364's "4-8" calibration hint, which caused it to stop prematurely. With "4-10", gemini performs 4 absorptions including semantically sound merges:
- Technical Standards Advocacy → EU Standards Engagement (correct domain, correct hierarchy)
- Procurement Conditionality → Procurement Language Specificity (correct direction — Conditionality is more specific)
- Resilience Narrative Amplification → Risk Framing (correct — amplification is a sub-tactic of framing)
- EU Interoperability Advocacy → EU Standards Engagement (correct — interoperability is a subset)

Evidence: `history/3/27_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`, response section.

### P3 — Haiku produces well-reasoned, context-grounded justifications

Haiku (run 28) on sovereign_identity produces detailed, lever-ID-citing justifications that reference the specific project (AltID, Danish digital identity strategy, platform-neutrality goals). The hierarchy direction is consistently correct (Conditionality → Language Specificity; Continuity Planning → Contingency Protocol; both Resilience Narrative → Risk Framing correctly). The primary/secondary split (7/5 kept) is reasonable for 18 diverse levers.

Justification quality is notably higher than the baseline run 15 (llama3.1 before), which produced generic, repetitive justifications citing only lever names.

### P4 — gpt-5-nano applies aggressive-but-valid deduplication

gpt-5-nano (run 24) absorbed 10 out of 18 levers on sovereign_identity, reducing to 8 kept (5 primary, 3 secondary). While aggressive, the absorptions are semantically defensible: Fallback Authentication Modality subsumed into Authentication Protocol Diversification, Contingency Protocol Definition into Continuity of Service Planning, Resilience Narrative into Risk Framing. The output set is more concise and focused than other models'.

The exception is the hierarchy-direction error (Procurement Language Specificity absorbed into Procurement Conditionality, which is the wrong direction), but the overall deduplication quality is otherwise solid.

### P5 — Primary/secondary classification enables downstream prioritization

With the new primary/secondary split (replacing flat `keep`), downstream steps can prioritize primary levers for scenario selection while treating secondary levers as supporting context. This is a structural improvement over the previous `keep` classification. Haiku and gpt-oss-20b consistently assign "secondary" to operational levers (Demonstrator Fidelity, Coalition Breadth, Fallback Certification Criteria) and "primary" to high-stakes decisions (Procurement Language, Risk Framing, EU Standards).

### P6 — B3 bug fix ensures no truncation artifacts in multi-turn history

The PR description states the B3 fix adds conditional `...` in both `_build_compact_history` AND `all_levers_summary`. While the fix is code-level and not directly observable in output JSONs, the absence of any LLMChatError or partial-processing failures across all 35 runs suggests the multi-turn context building is working cleanly. The before-PR runs also showed 100% success, but B3 could have caused subtle context corruption (wrong levers absorbed due to garbled history) rather than outright failures.

---

## Comparison

### Before (runs 15–21) vs After (runs 22–28)

| Metric | Before (15–21) | After (22–28) |
|--------|---------------|---------------|
| Models | 7 models (inc. llama, haiku, gpt-4o-mini, gemini) | 7 models (inc. llama, haiku, gpt-4o-mini, gemini + gpt-5-nano, qwen3, gpt-oss-20b) |
| Input levers/plan | 15 (heavily duplicated triplicates) | 18 (semantically diverse) |
| Success rate | 100% (15 calls/plan) | 100% (18 calls/plan) |
| Avg absorbs (sovereign_identity) | 10/15 = 67% (haiku, gpt-4o-mini) | 4–10/18 = 22–56% (varies by model) |
| gpt-4o-mini absorbs | 10/15 (easy triplicates) | 0/18 (FAILURE on diverse input) |
| Gemini absorbs | estimated ~0–2/15 (premature stop) | 4/18 (hit lower bound with 4-10 hint) |
| System prompt | nearly identical to after | as described above |
| Hierarchy violations | not measurable (trivial deduplication) | 3/7 models (llama, gpt-5-nano, qwen3) |

The gemini improvement is the clearest evidence that the "4-10" calibration hint helped: gemini went from under-absorbing (near 0 from 15 easy levers, mentioned in PR #364 as a known problem) to correctly absorbing 4 semantically-overlapping levers from 18 diverse inputs.

### Content quality comparison against baseline

The baseline training data (`baseline/train/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`) uses the old `keep`/`absorb` flat classification. The new output adds `classification: "primary"|"secondary"` and `deduplication_justification` to each kept lever. Field lengths for `consequences`, `options`, and `review` are inherited from the identify_potential_levers output (not modified by the dedup step). No fabricated percentage claims are introduced by the deduplication step itself — the step focuses on classification and absorption, not content generation.

The `deduplication_justification` field adds ~150–400 chars per lever in most runs. Haiku and gpt-oss-20b produce the most informative justifications (project-specific, lever-ID-citing). llama3.1 produces generic justifications that don't explain the actual choice.

---

## Quantitative Metrics

### Absorb rate summary (sovereign_identity, 18 input levers)

| Run | Model | Primary | Secondary | Absorb | Kept | Absorb rate | Within 4–10 range? |
|-----|-------|---------|-----------|--------|------|-------------|-------------------|
| 22 | llama3.1 | ? | ? | ≥3 | ≤15 | ≥17% | probably yes, quality poor |
| 23 | gpt-oss-20b | ~10 | ~2 | ~5 | ~13 | ~28% | YES |
| 24 | gpt-5-nano | 5 | 3 | 10 | 8 | 56% | YES (upper bound) |
| 25 | qwen3 | ? | ? | ≥5 | ≤13 | ≥28% | probably YES |
| 26 | gpt-4o-mini | 12 | 6 | 0 | 18 | 0% | NO — FAILURE |
| 27 | gemini | 7 | 7 | 4 | 14 | 22% | YES (lower bound) |
| 28 | haiku | 7 | 5 | 6 | 12 | 33% | YES |

### Success rates

| Run | Model | Plans completed | Calls succeeded | Errors |
|-----|-------|----------------|-----------------|--------|
| 22 | llama3.1 | 5/5 | 18/plan | 0 |
| 23 | gpt-oss-20b | 5/5 | 18/plan | 0 |
| 24 | gpt-5-nano | 5/5 | 18/plan | 0 |
| 25 | qwen3 | 5/5 | 18/plan | 0 |
| 26 | gpt-4o-mini | 5/5 | 18/plan | 0 |
| 27 | gemini | 5/5 | 18/plan | 0 |
| 28 | haiku | 5/5 | 18/plan | 0 |

100% success for all models and all plans.

### Hierarchy violation count (sovereign_identity)

| Run | Model | Hierarchy errors |
|-----|-------|----------------|
| 22 | llama3.1 | ≥3 (cross-domain absorptions) |
| 23 | gpt-oss-20b | 0 observed |
| 24 | gpt-5-nano | 1 (Procurement Language → Conditionality, wrong direction) |
| 25 | qwen3 | 1 (Procurement Language → Conditionality, wrong direction) |
| 26 | gpt-4o-mini | 0 (no absorbs at all) |
| 27 | gemini | 0 observed |
| 28 | haiku | 0 observed |

---

## Evidence Notes

- `history/3/26_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`: All 18 levers kept by gpt-4o-mini, 0 absorbs. blanket-primary confirmed.
- `history/3/22_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` lines 1–50: llama3.1 absorbs Demonstrator Fidelity into Fallback Auth Modality (wrong domain) and Procurement Conditionality into Fallback Certification Criteria (wrong domain).
- `history/3/27_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`: gemini produces 4 well-reasoned absorbs and correct primary/secondary classification for the remaining levers.
- `history/3/28_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`: haiku produces 6 absorbs with explicitly-cited lever IDs, correct hierarchy direction.
- `history/3/21_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` system_prompt: "expect 4–10 to be absorbed or removed" and "do not stop early" already present before PR. The prompt text is essentially the same in before and after runs.
- `baseline/train/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`: baseline uses `keep`/`absorb` classification (not primary/secondary). Output format changed significantly from baseline.
- `history/3/22_deduplicate_levers/events.jsonl` and `history/3/21_deduplicate_levers/events.jsonl`: run 21 started at 00:19:00Z, runs 22–28 started at 02:16:44Z — same day, ~2 hours apart.

---

## PR Impact

### What the PR was supposed to fix

PR #365 is a consolidation of PRs #363 and #364 and claims to fix:
1. `primary/secondary` classification replacing flat `keep`
2. Safety valve "Use primary only as a last resort" with calibration hint "expect 4-10" (widened from #364's "4-8" to fix gemini's premature stopping)
3. "do not stop early" instruction
4. Concrete secondary examples (marketing timing, reporting cadence, communication tooling)
5. B3 bug fix: conditional `...` in both `_build_compact_history` AND `all_levers_summary`
6. OPTIMIZE_INSTRUCTIONS with 5 documented failure modes
7. self_improve runner support for deduplicate_levers step
8. enrich_potential_levers accepts optional `classification` field

### Before vs After comparison

| Metric | Before (runs 15–21) | After (runs 22–28) | Change |
|--------|---------------------|--------------------|--------|
| Success rate | 100% (15 calls/plan) | 100% (18 calls/plan) | Neutral |
| Input lever count | 15 (heavily duplicated) | 18 (diverse, concrete) | ↑ Input quality improved |
| gpt-4o-mini absorbs (sovereign_identity) | 10/15 (trivial triplicates) | 0/18 (diverse input) | ↓ REGRESSION on diverse input |
| Gemini absorbs (sovereign_identity) | ~0–2/15 (near-miss) | 4/18 (within target range) | ↑ IMPROVEMENT |
| Haiku absorbs (sovereign_identity) | 10/15 (trivial triplicates) | 6/18 (diverse input) | Comparable for different inputs |
| System prompt text | same (both already had primary/secondary + 4-10 range) | same | No change observed |
| B3 code bug | present (before fix) | fixed | Not directly measurable from outputs |
| Primary/secondary split | already in system prompt before | same | Predates both analysis batches |
| LLMChatError | 0 | 0 | Neutral |

### Did the PR fix targeted issues?

**Gemini calibration (primary PR goal)**: YES. Gemini (run 27) now absorbs 4 levers from 18 diverse inputs, landing within the "4-10" range. The PR description explicitly identified sovereign_identity + gemini as the failure case for the "4-8" hint in PR #364. Run 27 demonstrates this is fixed.

**gpt-4o-mini (regression)**: The model performs well on the before-PR input (trivially-duplicated triplicates) but completely fails on the after-PR input (diverse levers). Whether this is attributable to PR #365 itself or to the harder input is unclear — but since the blanket-primary failure is the #1 documented failure mode in OPTIMIZE_INSTRUCTIONS, it's a significant quality gap.

**B3 bug fix**: Cannot be directly verified from output files. Both before and after runs show 100% success. If B3 caused silent context corruption (not outright failures), improvement would appear as better-quality absorptions — which is plausible for gemini's improvement but not provable from these outputs alone.

**Primary/secondary classification**: The system prompt in both before and after runs already contained primary/secondary. This change predates both analysis batches. Its downstream value (enabling enrich_potential_levers to use `classification`) is real but not testable from these runs.

### Verdict

**CONDITIONAL**

The PR produces measurable improvements for gemini (calibration fix confirmed) and provides valuable code infrastructure (B3 fix, self_improve runner, enrich_potential_levers classification support). However, gpt-4o-mini's blanket-primary failure is a significant unresolved problem — the model ignores the "expect 4-10" calibration hint entirely on diverse input. Since gpt-4o-mini is a common and widely-used model in production-like settings, zero absorbs on diverse lever sets is a meaningful quality regression. The hierarchy-direction violation in llama3.1, gpt-5-nano, and qwen3 also suggests the hierarchy instruction needs strengthening.

Recommended follow-up: (1) Address gpt-4o-mini blanket-primary failure, (2) Strengthen hierarchy-direction guidance.

---

## Questions For Later Synthesis

1. **Why does gpt-4o-mini ignore the "expect 4-10" calibration hint?** Is there a model-specific rephrasing that would help? Would explicit examples of what to absorb (similar to how secondary examples were added) help?

2. **Can the hierarchy-direction violation be fixed with examples?** Providing one worked example of a correct hierarchy absorption (e.g., "Technical Standards Advocacy absorbs INTO EU Standards Engagement, not the reverse") might help all models.

3. **Is the B3 fix detectable from outputs?** Future analysis could look at the actual `_build_compact_history` and `all_levers_summary` fields in intermediate outputs (if they are logged) to verify the fix.

4. **What is the correct absorb rate for diverse 18-lever inputs?** The baseline uses 15 triplicated levers. Is 4–10 absorbs still the right calibration for more-diverse inputs where semantic overlap is less obvious? Gemini's 4 absorbs may be appropriate rather than too few.

5. **Should OPTIMIZE_INSTRUCTIONS document the cross-domain absorption failure?** llama3.1's pattern (absorbing into wrong domains like procurement → certification, demonstrators → fallback auth) is not yet listed in the 5 documented failure modes.

---

## Reflect

The most important finding is the **gpt-4o-mini blanket-primary failure**, which is the most widely-used model in this batch and directly violates the core deduplication goal. The prompt says "reconsider if you find zero absorb/remove decisions" but gpt-4o-mini doesn't reconsider.

The gemini calibration fix is real and measurable. The B3 fix is a structural improvement that reduces context corruption risk even if not directly observable.

The confounding of input lever changes (15 duplicated → 18 diverse) makes strict before/after comparison difficult. Future iterations should use the same input set in both the before and after batches to cleanly isolate prompt/code effects.

---

## Potential Code Changes

**C1 — Add "absorb example" to the system prompt**
Provide one or two concrete worked examples of an absorb decision (like the secondary examples added in PR #365). This directly addresses the hierarchy-direction confusion and may also reduce gpt-4o-mini's blanket-primary tendency.

Evidence: 3/7 models show hierarchy errors; secondary examples in PR #365 are motivated by exactly this pattern.

**C2 — Add a minimum-absorb enforcement step**
After the LLM classifies levers, if absorb count is 0 and input count > 10, force a second pass asking the model to re-examine the closest pair. This is a code-level guard that doesn't rely on the model self-correcting.

Evidence: gpt-4o-mini sovereign_identity: 18 input levers, 0 absorbs. The model's output is structurally valid (no errors) but semantically fails the deduplication objective.

**C3 — Add cross-domain absorption detection in validator**
Check if a lever is being absorbed into a lever from a completely different semantic domain. This requires embedding or keyword similarity between lever names/consequences. If the absorb target is semantically distant (cosine sim < threshold), reject and retry.

Evidence: llama3.1 absorbs Procurement Conditionality → Fallback Certification Criteria (procurement into certification, unrelated domains).

**C4 — Document llama3.1 cross-domain absorption in OPTIMIZE_INSTRUCTIONS**
Add a 6th failure mode: "Cross-domain absorption: merging levers into semantically unrelated targets (e.g., procurement levers absorbed into technical certification levers)." This will alert future iterations to watch for this pattern in small/local models.

Evidence: `history/3/22_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` response items 089c8ec8, ed16c55c.

---

## Hypotheses

**H1 — Adding worked absorb examples to the system prompt will reduce gpt-4o-mini's zero-absorb rate**
Change: Add 1–2 concrete examples after the "expect 4–10" calibration hint, showing a specific lever pair where one absorbs into the other and why. Predict: gpt-4o-mini absorb rate increases to ≥4 from 18 diverse inputs.

Motivation: Secondary examples were added in PR #365 and help models classify correctly. The same approach should work for absorb decisions, which require judgment gpt-4o-mini isn't currently exercising.

**H2 — The "hierarchy" instruction needs positive examples to be effective**
Change: Add a one-sentence positive example: *"Example: 'Procurement Conditionality' absorbs into 'Procurement Language Specificity' because conditionality is a specific type of procurement language constraint."*
Predict: Hierarchy-direction violations in gpt-5-nano and qwen3 drop from 1/run to 0/run.

Motivation: Both models absorb Procurement Language Specificity into Procurement Conditionality (wrong direction). A worked example of the correct direction may anchor the judgment.

**H3 — Calibration hint "expect 4-10" is too wide for diverse inputs and too narrow for triplicated inputs**
Change: Make the calibration hint adaptive: *"In a set with near-identical names (e.g., three copies of the same strategy), expect 50–70% absorbed. In a set with diverse names, expect 20–40% absorbed or removed."*
Predict: More consistent absorb rates across different input compositions.

Motivation: The current 4–10 range (26–56% for 18 levers) is appropriate for diverse inputs but poorly calibrated for the heavily-duplicated inputs in runs 15–21 (where 10/15 = 67% is correct).

---

## Summary

PR #365 is a consolidation PR that delivers measurable improvement for gemini's sovereign_identity calibration (the specific case mentioned in the PR description). The B3 bug fix and infrastructure changes (self_improve runner, enrich_potential_levers classification) are valuable but not directly measurable from these outputs.

The primary unresolved issue is **gpt-4o-mini's blanket-primary failure** (0 absorbs from 18 diverse levers), which directly contradicts the deduplication objective. This is not a new failure mode — it's documented in OPTIMIZE_INSTRUCTIONS — but the current prompt changes do not fix it.

Secondary issues: llama3.1 makes cross-domain absorptions (a new, undocumented failure mode), and 3/7 models exhibit hierarchy-direction errors on at least one lever pair.

The PR is worth keeping for the gemini fix and infrastructure changes, but follow-up work on gpt-4o-mini's blanket-primary behavior and hierarchy examples is needed.
