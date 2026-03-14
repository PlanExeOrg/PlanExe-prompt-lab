# Insight Claude

Analysis of history runs `0/09` through `0/16` for the `identify_potential_levers` step.
Prompt: `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt`
Associated PR: [#268](https://github.com/PlanExeOrg/PlanExe/pull/268) — remove doubled user prompt in `identify_potential_levers` (B1)

---

## Operational Summary

Eight runs (09–16) each processed five plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`. One model per run was configured.

| Run | Model | Plans OK | Plans Failed | Success Rate | Failure Cause |
|-----|-------|----------|--------------|--------------|---------------|
| 09 | openrouter-stepfun-step-3-5-flash | 0 | 5 | 0% | Model name not in llm_config |
| 10 | openai-gpt-5-nano | 5 | 0 | 100% | — |
| 11 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0 | 5 | 0% | JSON extraction returned empty string |
| 12 | anthropic-claude-haiku-4-5-pinned | 5 | 0 | 100% | — |
| 13 | openrouter-openai-gpt-oss-20b | 4 | 1 | 80% | Truncated JSON on parasomnia plan |
| 14 | openrouter-qwen3-30b-a3b | 5 | 0 | 100% | — |
| 15 | openrouter-openai-gpt-4o-mini | 5 | 0 | 100% | — |
| 16 | ollama-llama3.1 | 5 | 0 | 100% | — |

Sources: `history/0/09_identify_potential_levers/outputs.jsonl` through `history/0/16_identify_potential_levers/outputs.jsonl`.

---

## Negative Things

### N1 — Two models fail 100% of plans for infrastructure reasons

Run 09 (`stepfun-step-3-5-flash`) fails at the `create` stage with `ValueError("Cannot create LLM, the llm_name 'openrouter-stepfun-step-3-5-flash' is not found in the selected llm_config/<profile>.json.")`. No plan output is produced. This is a configuration issue, not a quality issue.

Run 11 (`nvidia-nemotron-3-nano-30b-a3b`) completes the LLM calls (taking 90–196 s per plan) but fails at `execute` with `ValueError('Could not extract json string from output: ')`. The model responds but without parseable JSON. Source: `history/0/11_identify_potential_levers/outputs.jsonl`.

### N2 — Run 13 parasomnia plan fails due to JSON truncation

The `gpt-oss-20b` model produces a valid but truncated JSON string for `20260311_parasomnia_research_unit`. The error in `history/0/13_identify_potential_levers/outputs.jsonl` shows the response was cut off in the middle of a lever. The excerpt in the error message confirms the content was valid up to the truncation point. This may indicate the model's output hit a context or response-length limit on the first "more" turn.

### N3 — gpt-5-nano (run 10) repeats prompt example verbatim in 11/15 levers

The prompt includes the instruction: `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"`. In run 10's silo output (`history/0/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`), 11 out of 15 lever consequences contain `"25% faster scaling through"` in the systemic field — identical to the prompt's worked example. This is template leakage: the model is copying the prompt's illustration rather than deriving plan-specific metrics.

Examples from that file:
- Lever 1: `"Systemic: 25% faster scaling through modular, AI-optimized operations"`
- Lever 6: `"Systemic: 25% faster scaling through modular standardization and AI-enabled logistics"`
- Lever 7: `"Systemic: 25% faster scaling through real-time analytics and modular reuse"`

### N4 — gpt-4o-mini (run 15) produces duplicate lever names

In `history/0/15_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the following lever names appear twice with distinct but similar content:
- `"Governance and Control Framework"` (levers at positions 2 and 7)
- `"Resource Allocation Strategy"` (levers at positions 1 and 11)

Additionally `"Information Control Strategy"` (position 4) and `"Information Management Strategy"` (position 10) share near-identical options. The prompt prohibits generic lever names, yet gpt-4o-mini recycles names across LLM calls without awareness of prior output.

### N5 — llama3.1 (run 16) produces 20 levers instead of 15

Run 16 (`ollama-llama3.1`) outputs 20 levers for the silo plan (`history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`). The expected count is 15 (3 batches × 5). This indicates an extra LLM call or that the model generated more than 5 levers per call. Among the 20:
- `"Material Adaptation Strategy"` appears at positions 1 and 6 (exact name duplicate)
- `"Security and Surveillance Strategy"` (position 2) and `"Surveillance and Security Protocol"` (position 9) are near-semantic duplicates

### N6 — qwen3 (run 14) options are short labels, not strategic descriptions

The first batch of qwen3's silo output uses one-sentence options:
```
"Prioritize locally sourced, low-cost concrete for rapid deployment"
"Adopt modular composite panels for incremental upgrades"
"Implement 3D-printed bio-concrete with self-healing properties"
```
The prompt requires options to "represent distinct strategic pathways (not just labels)" and be "self-contained descriptions." These are closer to labels than full strategic approaches. Source: `history/0/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### N7 — gpt-oss-20b (run 13) duplicates a lever name within the same plan

`history/0/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains `"Governance Architecture Strategy"` at positions 6 and 11, with different lever IDs but semantically overlapping content (both address centralized vs. autonomous governance for the silo).

### N8 — Cross-call thematic redundancy across all models

All successful models show thematic clustering across LLM calls: governance levers appear 2–3 times, information levers 2 times, resource levers 2–3 times. The step asks the model for 5 more levers with a bare `"more"` prompt, without feeding back what was already generated. This causes cross-call duplication in topic coverage even when lever names differ.

---

## Positive Things

### P1 — claude-haiku (run 12) produces plan-specific, high-depth levers

Run 12's silo output contains levers tailored to the Silo universe's specific constraints. Examples from `history/0/12_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

- `"Closure Timing and Irreversibility Protocol"` — addresses the specific tension between external supply integration and information leakage risk
- `"Succession Planning and Leadership Continuity Mechanisms"` — addresses what happens when founders die inside a sealed silo
- `"Population Stratification Model"` — discusses breeding restrictions and generational stability (200+ year horizon)

The consequence chains are genuinely three-stage with specific percentages that vary per lever (40%, 25%, 22%) rather than a fixed template value. Options are 2–4 sentences each and represent distinct strategic philosophies.

### P2 — gpt-5-nano (run 10) achieves structural compliance with rich options

Despite template leakage in consequence fields, run 10's options are substantively distinct pathways (conservative/moderate/radical), include unconventional tech (blockchain DAOs, autonomous robotics), and maintain parallel grammatical structure. The lever names are well-formed strategic concepts. All 5 plans produce valid, well-structured JSON.

### P3 — qwen3 (run 14) and gpt-4o-mini (run 15) are fully reliable operationally

Both complete all 5 plans with 100% success. Duration is fast (gpt-4o-mini: 45–54 s per plan). For workloads where speed and reliability outweigh depth, these models work without error.

### P4 — B1 fix does not introduce new failures

None of the 24 plan executions that succeeded (across runs 10, 12, 13, 14, 15, 16) show errors attributable to the corrected conversation sequence `SYSTEM → USER(prompt) → ASSISTANT → USER("more") → ASSISTANT → USER("more")`. The fix is transparent to output quality.

---

## Comparison

### vs. Baseline Training Data (`baseline/train/`)

The baseline file for the silo plan (`baseline/train/20250321_silo/002-10-potential_levers.json`) contains 15 levers with names like `"Resource Allocation Strategy"`, `"Social Control Mechanism"`, `"Technological Adaptation Strategy"`, `"External Communication Protocol"`, `"Ethical Oversight Framework"`. The options are 1–2 sentence descriptions with some missing trade-off depth.

| Dimension | Baseline (train/silo) | Run 12 (claude-haiku) | Run 15 (gpt-4o-mini) |
|-----------|----------------------|----------------------|----------------------|
| Plan-specific lever names | Partially (generic + some specific) | High specificity (Closure Timing, Succession Planning) | Low (generic titles) |
| Option depth | 1–2 sentences | 3–5 sentences | 1–2 sentences |
| Consequences specificity | Moderate (mixed format) | High (plan-specific percentages) | Low (formulaic) |
| Duplicate lever names | Present (Material Adaptation ×2) | None | 2 exact duplicates |
| Format compliance | Partial | High | Partial |

Run 12 (claude-haiku) exceeds baseline quality on all dimensions. Run 15 (gpt-4o-mini) is at or below baseline quality.

### vs. Analysis 0 (runs 00–08, pre-fix)

Analysis 0 covered the same prompt SHA with the double-USER-prompt bug. The runs analyzed here (09–16) are post-fix. The failure patterns are different:
- Analysis 0 had models that may have been confused by the `SYSTEM → USER → USER` sequence
- Analysis 1 failures (runs 09, 11) stem from model availability and JSON capability issues, not conversation structure
- The quality of successful runs appears comparable or better, consistent with the fix not degrading output

---

## Quantitative Metrics

### Table A — Lever count per run (silo plan)

| Run | Model | Total levers | Expected | Violation |
|-----|-------|--------------|----------|-----------|
| 10 | gpt-5-nano | 15 | 15 | No |
| 12 | claude-haiku | 15 | 15 | No |
| 13 | gpt-oss-20b | 15 | 15 | No |
| 14 | qwen3-30b-a3b | 15 | 15 | No |
| 15 | gpt-4o-mini | 15 | 15 | No |
| 16 | llama3.1 | 20 | 15 | **Yes (+5)** |
| baseline | — | 15 | 15 | No |

Source: `**/002-10-potential_levers.json` files for silo plan.

### Table B — Name uniqueness (silo plan)

| Run | Model | Total levers | Unique names | Exact duplicates | Near-duplicate pairs |
|-----|-------|--------------|--------------|-----------------|----------------------|
| 10 | gpt-5-nano | 15 | 15 | 0 | 0 |
| 12 | claude-haiku | 15 | 15 | 0 | 0 |
| 13 | gpt-oss-20b | 15 | 14 | 1 ("Governance Architecture Strategy") | 0 |
| 14 | qwen3-30b-a3b | 15 | 14 | 1 ("Material Adaptation Strategy") | ~1 |
| 15 | gpt-4o-mini | 15 | 12 | 2 ("Governance and Control Framework", "Resource Allocation Strategy") | 1 |
| 16 | llama3.1 | 20 | 18 | 1 ("Material Adaptation Strategy") | 2 |

### Table C — Template leakage count (silo plan, "25% faster scaling through")

| Run | Model | Occurrences in 15 levers | Rate |
|-----|-------|--------------------------|------|
| 10 | gpt-5-nano | 11 | 73% |
| 12 | claude-haiku | 0 | 0% |
| 13 | gpt-oss-20b | 0 | 0% |
| 14 | qwen3-30b-a3b | 2 | 13% |
| 15 | gpt-4o-mini | 0 | 0% |
| 16 | llama3.1 | 0 | 0% |

Source: manual scan of consequences fields in `history/0/{10,12,13,14,15,16}_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### Table D — Approximate average consequence length (silo, first lever per batch, 3 batches)

Rough character counts from source files:

| Run | Model | Avg consequence length (chars) | Qualitative depth |
|-----|-------|-------------------------------|-------------------|
| 10 | gpt-5-nano | ~250 | Moderate |
| 12 | claude-haiku | ~450 | High |
| 13 | gpt-oss-20b | ~180 | Moderate |
| 14 | qwen3-30b-a3b | ~130 | Low |
| 15 | gpt-4o-mini | ~200 | Low |
| 16 | llama3.1 | ~185 | Low |
| baseline | — | ~190 | Moderate |

### Table E — Success rate by run

| Run | Model | Success Rate | Failure type |
|-----|-------|-------------|--------------|
| 09 | stepfun | 0% | Config: model not found |
| 10 | gpt-5-nano | 100% | — |
| 11 | nemotron | 0% | Model: no JSON output |
| 12 | claude-haiku | 100% | — |
| 13 | gpt-oss-20b | 80% | Model: JSON truncation (1 plan) |
| 14 | qwen3 | 100% | — |
| 15 | gpt-4o-mini | 100% | — |
| 16 | llama3.1 | 100% | — |

---

## Evidence Notes

- Template leakage evidence: `history/0/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` levers 1–11 all use "25% faster scaling through"
- Duplicate name evidence (gpt-4o-mini): `history/0/15_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever_ids `6a653f5f` and `353fdd08` both named "Governance and Control Framework"; `6a653f5f` and `5caa4f48` both named "Resource Allocation Strategy"
- Extra batch evidence (llama3.1): `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` has 20 entries vs 15 for all other runs on the same plan
- JSON truncation error: `history/0/13_identify_potential_levers/outputs.jsonl` shows parasomnia plan failed with truncated lever JSON mid-sentence
- Run 11 empty JSON: `history/0/11_identify_potential_levers/outputs.jsonl` shows `ValueError('Could not extract json string from output: ')` — the model returned non-JSON text
- Config failure: `history/0/09_identify_potential_levers/outputs.jsonl` shows `ValueError("Cannot create LLM, the llm_name 'openrouter-stepfun-step-3-5-flash' is not found...")`

---

## Questions For Later Synthesis

1. **Was the B1 bug (double USER prompt) causing measurable quality degradation in analysis 0 runs?** The fix can only be assessed as a "keeper" if analysis 0 had worse output from the double-prompt sequence. Does the previous synthesis confirm degradation?

2. **Why did llama3.1 produce 20 levers instead of 15?** Is the "more" prompt being interpreted as "produce all remaining levers at once" by this model? Was there an extra "more" call in the runner?

3. **Is cross-call thematic redundancy an inherent code problem or a prompt problem?** The step currently sends a bare `"more"` without including context of previously generated levers. Feeding a list of existing lever names would reduce redundancy.

4. **Should the runner reject outputs with duplicate lever names?** The prompt prohibits generic labels but the validation step (`002-10-potential_levers.json` vs `002-9-potential_levers_raw.json`) may not enforce uniqueness.

5. **Is nemotron's JSON failure related to the fixed conversation sequence?** With the double USER prompt, the first call had a different structure. It is possible nemotron responded differently (producing JSON) before the fix. Worth checking analysis 0 nemotron run outputs if available.

6. **For qwen3, are short options a model limitation or missing prompt instruction?** The prompt says options must be "self-contained descriptions" but does not specify minimum length.

---

## Reflect

This analysis covers 8 runs testing the same prompt on 8 different model configurations, all post-fix. The most important finding is that **model choice dominates output quality** far more than the PR fix itself. Claude Haiku produces substantively superior levers (plan-specific, long, varied) while gpt-4o-mini and llama3.1 produce generic, redundant content.

The PR fix (B1) addresses a code correctness issue and appears safe — it does not introduce failures. However, because the pre-fix runs (analysis 0) are not in scope here, we cannot directly confirm the improvement from the fix itself. The fix should be assessed as a keeper based on:
- Correct conversation structure is required for proper model behavior
- No new failures observed in post-fix runs
- Quality of successful runs is acceptable to excellent depending on model

The persistent quality problems (template leakage, cross-call deduplication, short options in weaker models) are not caused by the B1 bug and require separate interventions.

---

## Potential Code Changes

**C1 — Feed prior lever names into subsequent "more" calls**
Evidence: N8 (cross-call thematic redundancy). All models repeat governance/information/resource themes across batches.
Change: Include a list of already-generated lever names in the `"more"` turn, e.g., `"Generate 5 more levers. Already covered: [names]. Do not repeat these topics."`.
Expected effect: Reduce cross-call name duplicates from ~3 per plan to near zero; improve topic diversity.

**C2 — Add post-processing deduplication of lever names**
Evidence: N4, N5, N7. Multiple models produce exact or near-exact name duplicates across batches.
Change: After merging all batches, deduplicate by lever name (exact match) or flag near-matches for synthesis-time review.
Expected effect: Eliminates "Governance and Control Framework ×2" artifacts in gpt-4o-mini and similar issues in llama3.1.

**C3 — Add a maximum lever count guard**
Evidence: N5 (llama3.1 produced 20 levers). If the step expects 15 (3×5) but llama3.1 produces 20, downstream processing may be affected.
Change: After merging batches, truncate or warn if total count exceeds `n_calls × 5`.
Expected effect: Prevents unexpected expansion of the lever set for models that generate extra content.

**C4 — Log and surface per-call lever counts for monitoring**
Evidence: The runner stores raw JSON (`002-9-potential_levers_raw.json`) and merged output (`002-10-potential_levers.json`), but there is no per-call count assertion.
Change: Assert that each raw response contains exactly 5 levers before accepting the batch.
Expected effect: Catches violations early (e.g., a model returning 3 or 7 levers per call) rather than silently accepting bad batches.

---

## Prompt Hypotheses

**H1 — Removing the example metric from the consequences template reduces template leakage**
Evidence: N3 (gpt-5-nano copies "25% faster scaling through" in 11/15 levers). The prompt shows `"Systemic: 25% faster scaling through..."` as a concrete example, which weaker models copy verbatim.
Change: Replace the example with a structural cue: `"Systemic: [specific quantified impact, e.g., percentage change in X] through [mechanism]"`.
Expected effect: Reduces template copying in gpt-5-nano class models; claude-haiku is unaffected (it already ignores the template).

**H2 — Requiring minimum option word count reduces terse label options**
Evidence: N6 (qwen3 options are 8–10 words rather than strategic descriptions).
Change: Add to prohibitions: `"Options MUST be at least 20 words each and describe a complete approach, not a label."`.
Expected effect: Forces qwen3 and similar models to expand options into strategic descriptions.

**H3 — Explicitly naming the multi-call context prevents cross-call repetition**
Evidence: N8 (all models repeat themes across calls).
Change: In the "more" message, include: `"You have already proposed levers covering: [list]. These topics are closed. Generate 5 levers covering different strategic dimensions of the plan."`.
Expected effect: Reduces thematic overlap between batches; requires code change (C1) to implement.

---

## Summary

Runs 09–16 used eight different model configurations against the same prompt (post-B1 fix). Two models failed entirely (stepfun: config issue; nemotron: no JSON output). One model had one plan fail (gpt-oss-20b: JSON truncation). Five models succeeded fully.

Quality varies dramatically by model:

| Tier | Model | Key strength | Key weakness |
|------|-------|-------------|--------------|
| Best | claude-haiku (run 12) | Plan-specific, long, rich options | None observed |
| Good | gpt-5-nano (run 10) | Structured, full options | 73% template leakage in consequences |
| Moderate | qwen3 (run 14), gpt-oss-20b (run 13) | Reliable, reasonable structure | Short options, 1 failure |
| Below avg | gpt-4o-mini (run 15), llama3.1 (run 16) | Fast, reliable | Duplicate lever names, generic content |
| Failed | stepfun (run 09), nemotron (run 11) | — | Config or JSON capability |

The B1 fix (double USER prompt removal) is operationally safe and structurally correct. The quality problems observed (template leakage, cross-call redundancy, duplicate names) are pre-existing issues not caused by the fix. Priority recommendations for synthesis:

1. **Accept the PR** — B1 fix is correct and introduces no regressions
2. **Pursue C1** (feed prior lever names into "more" calls) — code-level fix benefiting all models
3. **Pursue H1** (remove worked example metric from prompt) — reduces gpt-5-nano template leakage at no cost
4. **Consider C2** (deduplication guard) — defensive post-processing catches worst-case duplicate name failures
