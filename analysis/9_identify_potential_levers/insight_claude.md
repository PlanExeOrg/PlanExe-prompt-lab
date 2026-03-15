# Insight Claude

**Analysis directory:** `analysis/9_identify_potential_levers/`
**Prompt:** `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`
**PR under review:** #279 — "Remove formulaic naming template from lever prompt"
**History runs:** 67–73 (all using prompt_1, sha `b12739343…`)

---

## Context

### What prompt_1 changed from prompt_0

| Prompt | Section 3 naming guidance |
|--------|--------------------------|
| prompt_0 | `(e.g., "Material Adaptation Strategy")` — generic single example, no domain prefix |
| prompt_1 | `(e.g., "[Domain]-[Decision Type] Strategy")` — prescriptive bracket template with domain placeholder |

PR #279 proposes to remove the `[Domain]-[Decision Type] Strategy` example from prompt_1. Runs 67–73 were all generated **with prompt_1** and reveal what that template does across seven different models.

---

## Rankings

Ranked by overall output quality (template leakage, content richness, constraint compliance):

| Rank | Run | Model | Template Leakage | Success Rate | Content Depth |
|------|-----|-------|-----------------|--------------|---------------|
| 1 | 73 | claude-haiku-4-5-pinned | 0% | 4/5 | Very High |
| 2 | 70 | openai-gpt-5-nano | ~7% (1/15) | 5/5 | High |
| 3 | 71 | openrouter-qwen3-30b-a3b | 0% | 5/5 | Medium |
| 4 | 69 | openrouter-openai-gpt-oss-20b | ~93% | 5/5 | Medium |
| 5 | 72 | openrouter-openai-gpt-4o-mini | 100% (silo), ~0% (GTA) | 5/5 | Low–Medium |
| 6 | 68 | ollama-llama3.1 | 100% | 5/5 | Low |
| 7 | 67 | openrouter-nvidia-nemotron-3-nano-30b-a3b | N/A | 0/5 | None |

---

## Negative Things

### N1 — Nemotron (run 67): 100% failure rate

All 5 plans returned `ValueError("Could not extract json string from output")` or a Pydantic JSON parse error. The model produced no valid lever outputs for any plan.

Evidence: `history/0/67_identify_potential_levers/outputs.jsonl` lines 1–5 — five consecutive `"status": "error"` entries.

### N2 — High template leakage in three of six successful runs

Three models mechanically applied the `[Domain]-[Decision Type] Strategy` bracket template from the prompt example:

- **Run 68 (llama3.1):** All 17 silo levers follow `[Hyphenated]-[Type] Strategy` (e.g., "Silo-Expansion Strategy", "Governance-Structure Strategy"). All 18 GTA levers follow `GTA-X-Lever` (e.g., "GTA-Studio-Lever", "GTA-Funding-Lever"). 100% leakage.
- **Run 69 (gpt-oss-20b):** All 15 silo levers follow `[Hyphenated]-[Type] Strategy` (e.g., "Silo-Construction Strategy", "Governance-Information Strategy", "Technology-Deployment Strategy"). ~93% leakage.
- **Run 72 (gpt-4o-mini):** All 15 silo levers follow `Silo-[Type] Strategy` (e.g., "Silo-Resource Allocation Strategy", "Silo-Behavioral Governance Strategy"). 100% domain-prefixed.

Evidence:
- `history/0/68_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — names 1–17 all hyphenated
- `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all 15 start with "Silo-"

### N3 — Duplicate lever names in run 68 (llama3.1)

Within a single plan's merged output, llama3.1 produced exact name duplicates:

- `silo` plan: "Information-Control Strategy" appears at positions 4 and 8 (17 total levers)
- `gta_game` plan: "GTA-Studio-Lever" (×2), "GTA-Funding-Lever" (×2), "GTA-Partnership-Lever" (×2) — 3 pairs of duplicates in 18 total levers

Evidence: `history/0/68_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `outputs/20250329_gta_game/002-10-potential_levers.json`.

### N4 — Lever count constraint violations

The prompt requires "EXACTLY 5 levers per response". Several calls produced more or fewer:

| Run | Model | Plan | Total Levers | Inferred Calls | Violations |
|-----|-------|------|-------------|----------------|-----------|
| 68 | llama3.1 | silo | 17 | 3 | 1 call produced 7 |
| 68 | llama3.1 | gta | 18 | 3 | 2 calls produced 6 and 7 |
| 73 | haiku | silo | 19 | 4 | 1 call produced 4 |
| 73 | haiku | gta | 17 | 4 | 1 call produced 2 |
| Others | — | — | 15 | 3 | 0 |

Evidence: lever counts in `002-10-potential_levers.json` for each run/plan.

### N5 — Haiku (run 73): hong_kong_game plan failed validation

Claude Haiku produced only 1 lever for the hong_kong_game plan, triggering: `List should have at least 5 items after validation, not 1`.

Evidence: `history/0/73_identify_potential_levers/outputs.jsonl` line 3 — `"status": "error"`, duration 159.26 s.

### N6 — Qwen3 (run 71): consequences field pollution with review text

Several run-71 levers have the `review` text duplicated verbatim inside the `consequences` field. Example from silo lever 1:

```
"consequences": "...Controls cost efficiency vs. long-term resilience. Weakness: The options fail to consider geopolitical risks in material availability.",
"review": "Controls cost efficiency vs. long-term resilience. Weakness: The options fail to consider geopolitical risks in material availability."
```

Evidence: `history/0/71_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1.

### N7 — Partial `review` field in run 68 (llama3.1) GTA levers

Several GTA levers are missing either the "Controls [A] vs [B]" or the "Weakness:" component of the review format:

- Lever 6 ("GTA-IP-Lever"): `"Controls IP protection vs. Monetization flexibility."` — no weakness
- Lever 7 ("GTA-Tech-Lever"): `"Weakness: The options fail to consider…"` — no "Controls" line

Evidence: `history/0/68_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 6–8.

### N8 — Run 72 (gpt-4o-mini): inconsistent domain-prefix behaviour across plans

gpt-4o-mini applies "Silo-" prefix to 100% of silo levers but produces generic names for GTA levers (e.g., "Open-World Design Strategy", "Narrative Complexity Strategy") with no "GTA-" prefix. This inconsistency suggests the model only injects the domain name when the plan name is simple and short ("silo") but not when the plan name is multi-word ("gta_game").

Evidence: `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` vs `outputs/20250329_gta_game/002-10-potential_levers.json` first 40 lines.

### N9 — Run 68 (llama3.1): very short option texts — label-like rather than self-contained

Options for GTA levers in run 68 are extremely brief and label-like, violating the "self-contained descriptions" requirement:

- "Establish a Collaborative Studio Environment"
- "Implement Flexible Work Arrangements with Remote Options"
- "Create an Immersive Game Development Experience through Advanced VR/AR"

These read as short option labels rather than complete strategic approaches.

Evidence: `history/0/68_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever 1 options.

---

## Positive Things

### P1 — Haiku (run 73): richest, most domain-specific content by a wide margin

Claude Haiku's outputs have no template leakage and contain extremely detailed, quantified consequences. Examples from silo:

- "Capital Phasing and Funding Resilience" — consequence cites "$180–220 billion", "60–75% per-year capital draw reduction", "8–12 year timeline extension"
- "Life-Support System Redundancy Architecture" — consequence cites "40% capital reduction", "cascade-failure risk by 95%", "55–70% cost increase"

Lever names are varied in form (some end in "Strategy", some in "Architecture", "Model", or "Mechanism") and no two follow the same mechanical pattern.

Evidence: `history/0/73_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P2 — GPT-5-nano (run 70): high-quality content, mostly free of template leakage

Run 70 produces detailed consequences (~510 chars per lever) with specific measurable outcomes ("labor hours decrease by 15%", "energy efficiency improves by 5 percentage points"). Names are multi-word descriptive phrases, closely aligned with the baseline quality level.

Evidence: `history/0/70_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P3 — Five of six models (runs 68–72) achieve 5/5 plan success

Only nemotron (run 67) failed completely. All other models processed all five plans without structural failure, demonstrating the pipeline is reliable for most modern models.

Evidence: outputs.jsonl for runs 68–72 — all show 5 `"status": "ok"` entries.

### P4 — Haiku natural hyphen use is not template leakage

Haiku's GTA output uses hyphens as compound adjectives (e.g., "World-Scale Phasing Strategy", "NPC-Behavior Realism Spectrum", "Narrative-Branching Depth Calibration") but never as `[Domain]-[DecisionType]` separators. No lever name starts with "GTA-" or uses a project-domain word as prefix. This demonstrates natural compound-modifier hyphenation is distinguishable from template-driven domain-prefix leakage.

Evidence: `history/0/73_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — 17 levers, none starting with "GTA-".

### P5 — GPT-4o-mini (run 72): fastest successful run

gpt-4o-mini completed all 5 plans in 47–55 seconds each (total ~252 s), making it the most time-efficient successful model.

Evidence: `history/0/72_identify_potential_levers/outputs.jsonl` — all durations 47–54 s.

---

## Comparison

### vs. Baseline training data

Baseline silo levers (`baseline/train/20250321_silo/002-10-potential_levers.json`) use generic names without domain prefix: "Resource Allocation Strategy", "Social Control Mechanism", "Technological Adaptation Strategy". This matches the prompt_0 example style ("Material Adaptation Strategy") rather than prompt_1's `[Domain]-[Decision Type] Strategy` style.

Baseline parasomnia levers (`baseline/train/20260311_parasomnia_research_unit/002-10-potential_levers.json`) are highly domain-specific, with long options (200–350 chars each) and quantified consequences. The overall quality is closest to run 73 (haiku) and run 70 (gpt-5-nano).

### vs. Runs 65–66 (previous analysis, not covered here)

The PR description states runs 65–66 showed "100% 'Silo-X Strategy' in run 65, 47% in run 66". This current batch (67–73) confirms the problem persists at scale:
- Runs 68, 69, 72: high to 100% template leakage for silo
- Run 71 (qwen3): 0% but falls into prompt_0-style naming rather than novel domain language
- Only runs 70 and 73 produce genuinely domain-rich names free of template machinery

---

## Quantitative Metrics

### Table 1: Template Leakage Rate (silo plan)

| Run | Model | Total Levers | Domain-Prefix Names | Hyphenated-Pattern Names | Leakage Rate |
|-----|-------|-------------|--------------------|-----------------------------|-------------|
| 67 | nemotron | 0 | N/A | N/A | N/A (all failed) |
| 68 | llama3.1 | 17 | 5 ("Silo-…") | 17/17 | 100% |
| 69 | gpt-oss-20b | 15 | 1 ("Silo-Construction…") | 14/15 | 93% |
| 70 | gpt-5-nano | 15 | 1 ("Silo Core…", no hyphen) | 1/15 | ~7% |
| 71 | qwen3-30b | 15 | 0 | 0/15 | 0% |
| 72 | gpt-4o-mini | 15 | 15 ("Silo-…") | 0/15 | 100% |
| 73 | haiku | 19 | 0 | 0/19 | 0% |

*"Domain-prefix" = name starts with plan-domain word (Silo, GTA, etc.); "hyphenated-pattern" = hyphen between two distinct strategic words.*

### Table 2: Lever Count Compliance (5 levers per call)

| Run | Model | Silo Total | GTA Total | Violations |
|-----|-------|-----------|-----------|------------|
| 67 | nemotron | 0 | 0 | 5 failed runs |
| 68 | llama3.1 | 17 (≠15) | 18 (≠15) | 3 calls over-generated |
| 69 | gpt-oss-20b | 15 | Not sampled | 0 |
| 70 | gpt-5-nano | 15 | Not sampled | 0 |
| 71 | qwen3-30b | 15 | 15 | 0 |
| 72 | gpt-4o-mini | 15 | 15 | 0 |
| 73 | haiku | 19 (≠20) | 17 (≠20) | 2 under-generated calls |

### Table 3: Consequences Field Length (approximate, silo plan first lever)

| Run | Model | Consequences ~Chars | Notes |
|-----|-------|---------------------|-------|
| Baseline | — | ~240 | Reference |
| 68 | llama3.1 | ~142 | Shortest |
| 69 | gpt-oss-20b | ~320 | Medium |
| 70 | gpt-5-nano | ~510 | High |
| 71 | qwen3-30b | ~330 | Polluted (contains review text) |
| 72 | gpt-4o-mini | ~273 | Medium |
| 73 | haiku | ~480 | Longest, most detailed |

### Table 4: Run Reliability

| Run | Model | Plans OK | Plans Failed | Error Type |
|-----|-------|---------|-------------|------------|
| 67 | nemotron | 0/5 | 5/5 | JSON parse failure |
| 68 | llama3.1 | 5/5 | 0/5 | — |
| 69 | gpt-oss-20b | 5/5 | 0/5 | — |
| 70 | gpt-5-nano | 5/5 | 0/5 | — |
| 71 | qwen3-30b | 5/5 | 0/5 | — |
| 72 | gpt-4o-mini | 5/5 | 0/5 | — |
| 73 | haiku | 4/5 | 1/5 | Schema: 1 lever instead of 5 |

### Table 5: Within-Plan Duplicate Lever Names

| Run | Model | Plan | Duplicate Pairs |
|-----|-------|------|----------------|
| 68 | llama3.1 | silo | "Information-Control Strategy" (×2) |
| 68 | llama3.1 | gta | "GTA-Studio-Lever" (×2), "GTA-Funding-Lever" (×2), "GTA-Partnership-Lever" (×2) |
| All others | — | — | 0 |

---

## Evidence Notes

1. **prompt_0 vs prompt_1 diff** — only the naming example changed: `"Material Adaptation Strategy"` → `"[Domain]-[Decision Type] Strategy"`. All other sections (output requirements, quality standards, prohibitions) are identical. Artifact: `prompts/identify_potential_levers/prompt_0_fa5dfb88….txt` and `prompt_1_b12739343….txt`.

2. **Haiku hong_kong_game failure** — the validation error (`List should have at least 5 items after validation, not 1`) is a schema-enforcement catch. The model produced only 1 lever in one call, which the pydantic validator rejected. Artifact: `history/0/73_identify_potential_levers/outputs.jsonl` line 3.

3. **Qwen3 field pollution** — the `consequences` field for run 71 / silo lever 1 ends with literal `review` text: "Controls cost efficiency vs. long-term resilience. Weakness: The options fail to consider geopolitical risks in material availability." — identical to the `review` field. Artifact: `history/0/71_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1.

4. **Llama3.1 over-generation** — run 68 / silo has 17 levers, not 15. The middle batch accounts for 7 instead of 5. Artifact: `history/0/68_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (17 entries).

5. **GPT-4o-mini domain-selectivity** — gpt-4o-mini applies "Silo-" prefix to all silo levers but not to GTA levers (which get generic names). Artifact: `history/0/72_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (all "Silo-X") vs `outputs/20250329_gta_game/002-10-potential_levers.json` (no "GTA-" prefix).

6. **Baseline comparison** — baseline silo uses prompt_0-style generic names without domain prefix. Artifact: `baseline/train/20250321_silo/002-10-potential_levers.json`.

---

## Questions For Later Synthesis

1. Does removing the `[Domain]-[Decision Type] Strategy` example (PR #279) eliminate domain-prefix leakage in models like llama3.1 and gpt-4o-mini, or do they find other ways to mechanically prefix names?

2. Qwen3 (run 71) produces zero template leakage but also produces shorter, more generic names similar to prompt_0 outputs. Is it ignoring the new naming guidance entirely? If so, would a cleaner guidance phrase bring it closer to the haiku quality level?

3. Haiku (run 73) suffers from lever count violations in some calls (producing 4 or 2 instead of 5). Does this correlate with the `fresh-context-per-call` change from iteration 8? Are some calls missing context about how many levers to produce?

4. Why does haiku fail for hong_kong_game specifically? Is the plan document unusually long or structured differently, causing truncation?

5. Should the `review` field format ("Controls [A] vs. [B]. Weakness: …") be better enforced via schema validation, given that qwen3 and llama3.1 deviate from it?

6. Nemotron (run 67) fails entirely on JSON extraction. Is this model fundamentally incompatible with the schema enforcement approach, or is it a temporary API/model issue?

---

## Reflect

**On the PR hypothesis:** The data strongly supports PR #279. The `[Domain]-[Decision Type] Strategy` template in prompt_1 directly causes mechanical name prefixing in at least 3 of 6 models (50%). The models that resist the template (haiku, gpt-5-nano, qwen3) tend to produce better names anyway. Removing the prescriptive bracket template reduces risk of mechanical leakage without apparent downside for capable models.

**On model diversity:** This batch reveals that model capability dramatically overrides prompt guidance. Haiku generates extremely rich, specific content with no template leakage regardless of the example in the prompt. Nemotron cannot even produce valid JSON. The prompt engineering effort has diminishing value for the strongest and weakest models — it matters most for mid-tier models (llama, gpt-oss-20b, gpt-4o-mini).

**On count violations:** Both llama3.1 and haiku produce lever counts that deviate from "exactly 5". This suggests the constraint is insufficiently enforced at the code level. The pydantic validator in the pipeline uses `at least 5` not `exactly 5` as its lower bound (evidenced by the haiku error message: "List should have at least 5 items after validation, not 1"). This means a call returning 7 levers is never caught.

**On fresh-context-per-call:** With 4 workers (runs 70–73), each plan gets 4 independent calls. If the model is supposed to avoid repeating themes across calls, it cannot do so without seeing prior call outputs. This may explain why haiku's 4th call sometimes under-generates (the model may have run low on truly novel angles, producing fewer levers rather than repeating themes).

---

## Potential Code Changes

**C1 — Enforce exact lever count in schema validator**

Currently the validator catches `< 5` levers but silently accepts `> 5`. The prompt says "EXACTLY 5 levers per response". A schema constraint of `min_items=5, max_items=5` (or equivalent pydantic validator) would flag over-generation and allow the runner to retry. This benefits all models and is independent of prompt text.

Evidence: haiku over-generation in silo (19 levers across 4 calls), llama over-generation (17–18 levers).

**C2 — Log or collect `strategic_rationale` field from raw output**

The raw response (`002-9-potential_levers_raw.json`) contains a `strategic_rationale` field per call (confirmed from run 73 raw file). This field is discarded in the merge step (`002-10-potential_levers.json`). Retaining it in the final output — or at least making it available to later pipeline steps — would add useful context and allow synthesis to see the model's own framing of each batch.

Evidence: `history/0/73_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` line 4 shows `"strategic_rationale"`.

**C3 — Validate `review` field format against expected structure**

Several levers in runs 68 and 71 have malformed or polluted `review` fields. A lightweight regex or structural check ("must contain 'Controls' and 'Weakness:'") in the post-processing step could flag these and trigger a retry.

Evidence: `history/0/71_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (review text inside consequences), `history/0/68_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` (partial review format).

---

## Hypotheses

**H1 — Remove the `[Domain]-[Decision Type] Strategy` example (PR #279)**

Change: Replace `(e.g., "[Domain]-[Decision Type] Strategy")` in section 3 with open-ended guidance such as "Use descriptive language specific to this project's domain without a fixed naming pattern."

Evidence: Runs 68, 69, 72 show 93–100% template leakage directly traceable to that example. Runs 70, 71, 73 (which produce better names) appear to resist or ignore the example.

Predicted effect: Leakage rate drops to near-zero for gpt-oss-20b and gpt-4o-mini. May have no effect on haiku (already 0%) or nemotron (structural failure).

**H2 — Add positive name examples to guide domain-specific naming without a template**

Change: Instead of a bracket template, provide 2–3 concrete example names drawn from different domains (e.g., "Underground Habitat Integrity Strategy", "Event-Capture Intensity and PSG Montage Scheduling") to show variety without prescribing a rigid format.

Evidence: Baseline parasomnia levers demonstrate that high-quality, domain-specific names look nothing like a bracket template. Showing concrete examples may teach by demonstration rather than by formula.

Predicted effect: Mid-tier models (llama, gpt-oss-20b, gpt-4o-mini) adopt more descriptive names. Less likely to produce generic "X Strategy" or domain-prefix leakage.

**H3 — Reduce or remove the "show clear progression: conservative → moderate → radical" options requirement**

This instruction may be encouraging models to produce predictable, formulaic option triplets. Run 68 (llama) options are especially short and label-like. Run 73 (haiku) ignores this instruction and produces much richer standalone option descriptions.

Evidence: Haiku options are 80–200 chars each; llama options are 30–60 chars each (essentially labels). The former better matches the baseline training data quality.

Predicted effect: Removing the "conservative → moderate → radical" framing may increase option specificity for models that currently produce labels.

---

## Summary

Runs 67–73 test prompt_1 (which contains the `[Domain]-[Decision Type] Strategy` naming example) across seven models.

**Key finding:** The naming template causes mechanical leakage in at least 3 of 6 successful models (llama3.1, gpt-oss-20b, gpt-4o-mini), ranging from 93–100% of lever names following the bracket pattern. The two highest-quality runs (haiku and gpt-5-nano) show minimal or zero template leakage, producing rich domain-specific names independently.

**PR #279 verdict (preliminary):** The template is harmful and removing it is well-motivated. Models susceptible to template leakage (smaller or more instruction-literal) lock on to `[Domain]-[Decision Type] Strategy` and produce repetitive, mechanical names. Removing or replacing the example with concrete, diverse illustrations (H2) would likely eliminate this class of failure.

**Secondary issues:** Run 67 (nemotron) is entirely non-functional — a structural incompatibility, not a prompt issue. Lever count violations exist in both llama (over-generation) and haiku (under-generation), suggesting a code-level enforcement gap (C1). Qwen3's field pollution (C3) and haiku's hong_kong_game plan failure are additional reliability gaps worth tracking.

**Baseline gap:** The richest outputs (run 73 / haiku) approach baseline parasomnia quality in field length and specificity. Most other models produce shorter, less quantified consequences that fall below baseline depth.
