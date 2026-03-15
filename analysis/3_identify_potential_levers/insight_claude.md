# Insight Claude

Analysis of history runs `0/24_identify_potential_levers` through `0/31_identify_potential_levers`
Prompt: `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt`

---

## Rankings

Runs ranked by operational reliability × content quality:

| Rank | Run | Model | Successes | Notable Issues |
|------|-----|-------|-----------|----------------|
| 1 | 29 | openrouter-qwen3-30b-a3b | 5/5 | Minimal template leakage; good format compliance |
| 2 | 28 | openai-gpt-5-nano | 5/5 | Severe "25% faster scaling" leakage in every Systemic field |
| 3 | 26 | ollama-llama3.1 | 5/5 | Shallow consequences; terse option labels; review format violations |
| 4 | 31 | anthropic-claude-haiku-4-5-pinned | 4/5 | 1 timeout; good quality where it succeeds |
| 5 | 30 | openrouter-openai-gpt-4o-mini | 3/5 | 2 schema-field failures; good content otherwise |
| 6 | 27 | openrouter-openai-gpt-oss-20b | 2/5 | Truncated JSON; trailing chars |
| 7 | 25 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 1/5 | 4 empty-output failures |
| 8 | 24 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | All plans failed (empty output) |

---

## Negative Things

### N1 — Low overall reliability (62.5% success rate)

Across 8 runs × 5 plans = 40 plan executions, only 25 produced usable output (62.5%).

| Run | silo | gta | sovereign | hong_kong | parasomnia | Total |
|-----|------|-----|-----------|-----------|------------|-------|
| 24 | ✗ | ✗ | ✗ | ✗ | ✗ | 0/5 |
| 25 | ✓ | ✗ | ✗ | ✗ | ✗ | 1/5 |
| 26 | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| 27 | ✓ | ✓ | ✗ | ✗ | ✗ | 2/5 |
| 28 | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| 29 | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| 30 | ✓ | ✓ | ✗ | ✓ | ✗ | 3/5 |
| 31 | ✓ | ✓ | ✓ | ✓ | ✗ | 4/5 |

Plan-level success totals: silo 6/8 (75%), gta 6/8 (75%), sovereign_identity 4/8 (50%), hong_kong 5/8 (63%), parasomnia 4/8 (50%).

Source: `history/0/2{4-9}_identify_potential_levers/outputs.jsonl`, `history/0/3{0,1}_identify_potential_levers/outputs.jsonl`.

### N2 — Four distinct failure modes, requiring different fixes

1. **Empty output** — nemotron-3-nano (runs 24, 25): "Could not extract json string from output: " (empty string). The model produced no JSON at all.
   Source: `history/0/25_identify_potential_levers/outputs.jsonl` lines 1-4.

2. **Truncated JSON** — gpt-oss-20b (run 27): "Invalid JSON: EOF while parsing a list at line 1 column 2306." JSON was cut off mid-output.
   Source: `history/0/27_identify_potential_levers/outputs.jsonl` line 5.

3. **Missing schema wrapper fields** — gpt-4o-mini (run 30): "2 validation errors for DocumentDetails: strategic_rationale Field required, summary Field required." The model returned levers but omitted the wrapper fields.
   Source: `history/0/30_identify_potential_levers/outputs.jsonl` lines 1, 5.

4. **API timeout** — claude-haiku-4-5-pinned (run 31): "APITimeoutError" after 427 seconds for parasomnia_research_unit.
   Source: `history/0/31_identify_potential_levers/outputs.jsonl` line 5.

### N3 — Pervasive "25% faster scaling" template leakage

The prompt example in section 2 reads: `"Systemic: 25% faster scaling through..."`. Many models copy this verbatim into every lever's consequences.

In run 28 (`openai-gpt-5-nano`), **every single one of the 15 levers** for both silo and parasomnia contains "25% faster scaling" in the Systemic field:

```
"consequences": "Immediate: Eight suites activated with modular renovation baseline →
Systemic: 25% faster scaling through pre-approved modular components and vendor agreements →
Strategic: Enables rapid expansion..."
```

Source: `history/0/28_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` (all 15 levers).

In run 26 (llama3.1), the same leakage appears in most levers of the silo plan:
```
"consequences": "Immediate: Reduced material costs → Systemic: 25% faster scaling through
efficient supply chain management → Strategic: Enhanced reputation..."
```
Source: `history/0/26_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1.

### N4 — "Material Adaptation Strategy" name leakage from prompt example

The prompt's Section 3 gives the example: `"Name levers as strategic concepts (e.g., 'Material Adaptation Strategy')"`. Many runs produce a lever literally named "Material Adaptation Strategy" as the first lever, even for plans where this name is incongruous (e.g., for the hong_kong_game film production plan).

Confirmed in:
- `history/0/25_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — lever 1 name: "Material Adaptation Strategy" (appropriate for silo construction)
- `history/0/26_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — lever 1 name: "Material Adaptation Strategy"
- `history/0/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — lever 1 name: "Material Adaptation Strategy" (incongruous for a film production plan)

### N5 — Severe cross-call duplication in batch outputs

Each plan run makes 3 LLM calls, each producing 5 levers (15 total). In some runs, batches 1 and 2 produce near-identical lever topics. In run 28, parasomnia_research_unit:

| Batch 1 Lever | Batch 2 Lever (near-identical topic) |
|---------------|--------------------------------------|
| Adaptive Facility Footprint Strategy | Localized Modular Footprint Diffusion |
| Sensor Suite Architecture Strategy | Federated Sensing and Privacy-First Architecture |
| Ethical Recruitment and Retention Framework | Dynamic Enrollment and Retention Engineering |
| Governance and Data Stewardship Strategy | Open Governance and Compliance Scaffold |
| Funding and Risk Portfolio Strategy | Diversified Financing and Risk Allocation |

5 of 10 cross-batch lever pairs are semantic duplicates. Batch 3 levers (11-15) are genuinely novel.
Source: `history/0/28_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

Similar duplication in run 26, hong_kong_game: the option text "Employ an innovative narrative approach that subverts informed expectations from the original 1997 film." appears in at least 5 different levers' option sets.
Source: `history/0/26_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### N6 — Incomplete review fields (missing trade-off or weakness)

The prompt requires the review to contain both:
- Trade-off statement: "Controls [Tension A] vs. [Tension B]."
- Weakness statement: "Weakness: The options fail to consider [specific factor]."

In run 26, parasomnia_research_unit, 8 of 15 levers have only one of these two components:
```
"review": "Controls participant pool vs. population dynamics."   ← missing Weakness
"review": "Weakness: The options fail to consider participant comfort and privacy."   ← missing trade-off
```
Source: `history/0/26_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

### N7 — Option prefix violations in some runs

Run 25 (nemotron), silo, first 5 levers: options include prohibited prefix labels "Conservative:", "Moderate:", "Radical:" despite the prompt prohibiting prefixes:

```
"options": [
  "Conservative: Use locally sourced conventional concrete with established suppliers.",
  "Moderate: Adopt hybrid concrete incorporating recycled aggregates from regional demolition sites.",
  "Radical: Deploy 3D-printed geopolymer modules fabricated from on-site waste feedstock."
]
```

Source: `history/0/25_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` (batch 1 levers).

Importantly, the later 10 levers in the same plan do NOT have these prefixes. This creates inconsistency within a single plan output.

### N8 — Shallow consequences in some runs (format present but semantically weak)

Run 26, silo, lever 1:
```
"consequences": "Immediate: Reduced material costs → Systemic: 25% faster scaling through
efficient supply chain management → Strategic: Enhanced reputation for innovative problem-solving."
```
This follows the format but "Strategic: Enhanced reputation for innovative problem-solving" is extremely generic and doesn't describe a trade-off between core tensions.

Run 26, parasomnia:
```
"consequences": "Immediate: Increased recruitment rates → Systemic: Enhanced participant diversity
→ Strategic: Improved generalizability of findings."
```
This is a 1-2 word chain with no measurable outcomes and no explicit trade-offs.

By contrast, baseline (silo):
```
"consequences": "Centralized control of resources will likely lead to inequitable distribution and
potential social unrest. Immediate: Resource hoarding → Systemic: 15% increase in black market
activity → Strategic: Undermines social stability and long-term silo viability."
```
Source: `baseline/train/20250321_silo/002-10-potential_levers.json` lever 1.

### N9 — Options as terse labels rather than complete approaches

Run 26, parasomnia_research_unit options are single-phrase labels rather than complete strategic approaches:
```
"options": [
  "Conventional Specialist Clinics",
  "Strategic Community Outreach",
  "Innovative Digital Recruitment Platform"
]
```
These violate the "Ensure options are self-contained descriptions" requirement.
Source: `history/0/26_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` lever 1.

---

## Positive Things

### P1 — qwen3-30b (run 29) produces well-structured, domain-specific outputs

Run 29 succeeds for all 5 plans with rich consequences and specific content that avoids the "25% faster scaling" template leakage. Consequences are meaningful:

```
"consequences": "Choosing advanced composites reduces construction time but increases dependency
on specialized suppliers, risking systemic supply chain vulnerabilities and strategic isolation
from local resources."
```

Options are complete strategic approaches with clear conservative-to-radical progression and no prefix labels.
Source: `history/0/29_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P2 — gpt-5-nano (run 28) achieves 100% reliability with good structural compliance

Run 28 succeeds for all 5 plans. Consequences follow the chain format correctly. Reviews include both trade-off and weakness. The main deficiency is the "25% faster scaling" template copy in every Systemic field.
Source: `history/0/28_identify_potential_levers/outputs.jsonl` (all 5 plans: ok).

### P3 — claude-haiku (run 31) produces high-quality content for 4/5 plans

Where haiku succeeds, the output demonstrates good domain sensitivity and proper format compliance. No template leakage in the 4 successful plans. Options are substantive and self-contained.
Source: `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P4 — Pipeline's multi-batch design (3 calls × 5 levers) is conceptually correct

The design of 3 LLM calls producing 5 levers each (15 total) creates a richer pool for the downstream vital_few_levers step to select from. The approach generates lever diversity in the best runs (e.g., run 29: batch 1 covers resource/construction, batch 2 governance/tech, batch 3 social/psychological).

### P5 — nemotron-3-nano shows what "5 per response" compliance looks like

In run 25's successful silo output, the raw file (`002-9-potential_levers_raw.json`) shows the model correctly generating exactly 5 levers per response in 3 separate responses. The 3 × 5 structure is preserved as designed.
Source: `history/0/25_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`.

---

## Comparison

### Vs. Baseline Training Data

Baseline levers (`baseline/train/`) were generated by a Claude-class model with a different, more narrative system prompt. Key differences:

| Dimension | Baseline | History Runs 24-31 |
|-----------|----------|--------------------|
| Lever names | Domain-specific, unique | Some template leakage ("Material Adaptation Strategy") |
| Consequences format | Chain format with specific metrics | Varies; "25% faster scaling" boilerplate in many runs |
| Options | Complete strategic approaches (70-120 chars each) | Varies; some terse labels (20-40 chars), some complete |
| Review compliance | Both trade-off + weakness | Often only one component |
| Content depth | High specificity (e.g., "15% increase in black market activity") | Often generic (e.g., "enhanced reputation") |
| Extra fields | description, synergy_text, conflict_text | Only name, consequences, options, review |

The baseline represents a higher quality bar. The current prompt generates structurally similar output but with more template leakage and less domain specificity.

### Across Models

| Model | Reliability | Template Leakage | Content Depth | Format Compliance |
|-------|-------------|------------------|---------------|-------------------|
| nemotron-3-nano | Very Low (10%) | Low | Low | Low |
| llama3.1 | High (100%) | Medium | Low | Medium |
| gpt-oss-20b | Low (40%) | Unknown | Medium | Unknown |
| gpt-5-nano | High (100%) | Very High | Medium | High |
| qwen3-30b | High (100%) | Low | High | High |
| gpt-4o-mini | Medium (60%) | Low | Medium | Fail (missing fields) |
| claude-haiku | High (80%) | Low | High | High |

qwen3-30b and claude-haiku produce the best balance of reliability + content quality.

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Plans Failed | Success Rate |
|-----|-------|----------|--------------|--------------|
| 24 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0 | 5 | 0% |
| 25 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 1 | 4 | 20% |
| 26 | ollama-llama3.1 | 5 | 0 | 100% |
| 27 | openrouter-openai-gpt-oss-20b | 2 | 3 | 40% |
| 28 | openai-gpt-5-nano | 5 | 0 | 100% |
| 29 | openrouter-qwen3-30b-a3b | 5 | 0 | 100% |
| 30 | openrouter-openai-gpt-4o-mini | 3 | 2 | 60% |
| 31 | anthropic-claude-haiku-4-5-pinned | 4 | 1 | 80% |
| **TOTAL** | | **25** | **15** | **62.5%** |

### Lever Counts Per Successful Plan Output

All successful plan outputs: exactly **15 levers** (3 LLM calls × 5 levers each). No deviation observed.

### Template Leakage: "25% faster scaling" in Systemic consequences

| Run | Plan | Levers with Leakage | Total Levers | Leakage Rate |
|-----|------|---------------------|--------------|--------------|
| 26 | silo | ~14 | 15 | ~93% |
| 28 | silo | 15 | 15 | 100% |
| 28 | parasomnia | 15 | 15 | 100% |
| 25 | silo | 1 | 15 | 7% |
| 29 | silo | 1-2 | 15 | ~10% |
| 31 | silo | 0 | 15 | 0% |

Baseline: occasional, not systematic.

### Cross-Call Duplication (semantic overlap between batches 1 and 2)

| Run | Plan | Duplicate Pairs (B1 vs B2) | Duplicate Rate |
|-----|------|---------------------------|----------------|
| 28 | parasomnia | 5/5 | 100% |
| 26 | hong_kong | 2-3/5 | ~50% |
| 29 | silo | 0-1/5 | ~10% |
| 25 | silo | 0/5 | 0% |

### Review Field Completeness

(Requires both "Controls A vs. B." AND "Weakness: ...")

| Run | Plan | Compliant | Missing Trade-off | Missing Weakness | Total |
|-----|------|-----------|-------------------|------------------|-------|
| 26 | parasomnia | 7 | 4 | 4 | 15 |
| 25 | silo | 5 | 0 | 10 | 15 |
| 28 | parasomnia | 12 | 0 | 3 | 15 |
| 29 | silo | ~10 | 0 | ~5 | 15 |
| 26 | silo | ~8 | 0 | ~7 | 15 |

(Run 25 silo: first 5 levers compliant; second and third batches often omit the weakness.)

### Average Option Length (Characters, Approximate)

| Run | Plan | Avg Option Length | Complete Approach? |
|-----|------|------------------|--------------------|
| 26 | parasomnia | ~25 | No (terse labels) |
| 25 | silo batch 1 | ~75 | Yes |
| 28 | parasomnia | ~80 | Yes |
| 29 | silo | ~70 | Yes |
| 31 | silo | ~85 | Yes |
| Baseline | silo | ~95 | Yes |

### Constraint Violations Summary

| Violation Type | Runs Affected | Estimated Affected Levers |
|----------------|---------------|---------------------------|
| Template leakage ("25% faster scaling") | 26 (silo), 28 (all) | ~45 levers |
| Name leakage ("Material Adaptation Strategy") | 25, 26 | ~3 plans |
| Option prefix labels ("Conservative:", etc.) | 25 (silo, batch 1) | 5 levers |
| Incomplete review (missing trade-off OR weakness) | 25, 26, 28, 29 | ~50 levers across runs |
| Terse options (not complete approaches) | 26 (parasomnia) | ~15 levers |

---

## Evidence Notes

1. **Run 24 failure**: All 5 plans started (`history/0/24_identify_potential_levers/events.jsonl`) but none produced JSON — the plan directories contain only `track_activity.jsonl` with no `002-10-potential_levers.json`. Nemotron model produced empty output strings.

2. **Run 25 silo success raw structure**: The raw file `history/0/25_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` confirms 3 separate `responses[]` each with exactly 5 levers, plus a flattened `levers[]` array of 15. The pipeline design works as intended.

3. **Model metadata in raw file**: The raw file shows `"context_window": 3900` for nemotron-3-nano. A 3900-token context window is very small; complex plans (like parasomnia or hong_kong) likely exceed it, explaining empty outputs.

4. **Run 27 failure analysis**: Error "Invalid JSON: EOF while parsing a list at line 1 column 2306" means gpt-oss-20b truncated the JSON at ~2306 chars. This aligns with a small output token limit, not a context window issue.

5. **Run 30 failure mode**: gpt-4o-mini returned JSON containing only `{"levers": [...]}` without the wrapper keys `strategic_rationale` and `summary`. This is a schema compliance issue where the model correctly generates levers but ignores the outer wrapper structure.

6. **Run 31 timeout**: Claude Haiku took 427 seconds on parasomnia before timing out. The parasomnia plan text is likely longer or more complex than the other plans. Other plans in run 31 completed in 99-122 seconds.

7. **Baseline quality anchor**: `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` has 7 levers with rich options (~95 chars avg), measurable specific metrics ("20% increase in positive critical reception"), and proper trade-off identification. This is the quality target.

---

## Questions For Later Synthesis

Q1. Should the "5 per response" constraint remain, given that 3 calls × 5 = 15 is the intended behavior? Or should the prompt be changed to "EXACTLY 5 levers in this specific batch" to avoid confusion when final output has 15?

Q2. Is the cross-call duplication (batches 1 and 2 producing near-identical topics) driven by the prompt or by the code passing the same user context to all 3 calls without diversity instructions?

Q3. For gpt-4o-mini's "missing strategic_rationale and summary" failure: is this a schema issue (make fields optional) or a prompt issue (model is skipping the wrapper)?

Q4. The nemotron model's 3900-token context window causes empty outputs for complex plans. Should the runner reject/skip models with context windows below a threshold?

Q5. Does the cross-call duplication (N5) reduce the quality of downstream vital_few_levers selection? If batches 1 and 2 are near-identical, the vital few step is effectively choosing from only ~10 unique levers.

Q6. Is qwen3-30b's consistent high quality generalizable — does it maintain this quality across all plan types, or just the 5 baseline plans tested here?

---

## Reflect

The runs in this analysis group (24-31) span 8 different LLM configurations under the same prompt. The prompt itself seems reasonably well-designed for models that can follow structured output specifications (qwen3-30b, claude-haiku, gpt-5-nano all produce correct 5-per-batch output). The main prompt-level issues are:

1. The example text in the prompt is being copied verbatim ("25% faster scaling", "Material Adaptation Strategy"), suggesting these examples are too prescriptive.
2. The "conservative → moderate → radical" progression description, combined with the prohibition on prefixes like "Option A:", creates an ambiguity — some models infer "Conservative:", "Moderate:", "Radical:" are acceptable labels since they're mentioned as the progression type.

The main code-level issues are:
1. The schema validation rejects entire plan outputs when only wrapper fields (strategic_rationale, summary) are missing, even though the levers themselves are present and valid.
2. No mechanism to detect or deduplicate cross-batch semantic duplicates before downstream processing.
3. No minimum context window guard for model selection.

---

## Potential Code Changes

**C1 (Schema Flexibility):** In the Pydantic schema for `DocumentDetails`, make `strategic_rationale` and `summary` optional (or with defaults). This would prevent run 30's gpt-4o-mini failures where valid levers were generated but the wrapper was omitted.
Evidence: `history/0/30_identify_potential_levers/outputs.jsonl` lines 1 and 5.

**C2 (Context Window Guard):** Add a pre-flight check that rejects model configurations with context windows below a threshold (e.g., 8192 tokens) for this step. Nemotron-3-nano's 3900-token window is clearly insufficient for complex plan inputs.
Evidence: `history/0/25_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` metadata shows `"context_window": 3900`.

**C3 (Cross-Batch Deduplication):** After the 3 LLM calls complete, compare lever names across batches and flag/remove semantic duplicates before writing `002-10-potential_levers.json`. A simple string similarity check on lever names would catch the obvious cases.
Evidence: `history/0/28_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — 5 of 10 cross-batch lever pairs are near-identical.

**C4 (Timeout Tuning):** The 427-second timeout for claude-haiku on parasomnia suggests the per-plan timeout is too generous and may hide other failures. Consider reducing per-LLM-call timeout to 90 seconds and adding explicit retry-with-different-model logic.
Evidence: `history/0/31_identify_potential_levers/outputs.jsonl` line 5.

---

## Hypotheses

**H1 — Remove or anonymize the "25% faster scaling" example in the prompt**
The Systemic example "Systemic: 25% faster scaling through..." in section 2 is copied verbatim by many models.
Change: Replace with a non-numeric placeholder like `"Systemic: [measurable second-order impact, e.g., describes system-level cascade]"`.
Expected effect: Eliminate the "25% faster scaling" boilerplate from at least 80% of affected runs, making consequences more domain-specific.
Motivated by: N3, evidence from runs 26, 28.

**H2 — Replace or remove the "Material Adaptation Strategy" example lever name**
Section 3's `(e.g., "Material Adaptation Strategy")` is adopted verbatim as the first lever name.
Change: Replace with a generic placeholder like `(e.g., "[Project-Specific Strategy Name]")` or remove the parenthetical entirely.
Expected effect: Eliminate name leakage for non-construction plans.
Motivated by: N4, run 26 hong_kong output.

**H3 — Clarify the progression prohibition to explicitly exclude "Conservative:", "Moderate:", "Radical:" prefixes**
The current prohibition only lists "Option A:", "Choice 1:" as examples to avoid, but the "conservative → moderate → radical" wording implies these labels might be acceptable.
Change: Add to Prohibitions: `- NO directional labels in options (e.g., "Conservative:", "Moderate:", "Radical:", "Approach 1:")`.
Expected effect: Eliminate prefix-label violations across all models.
Motivated by: N7, run 25 silo batch 1.

**H4 — Add explicit anti-duplication instruction for multi-batch generation**
No instruction prevents the 3 LLM calls from generating the same lever topics.
Change: In the user prompt or in the context passed to calls 2 and 3, include a list of lever names already generated, with the instruction "Do not repeat or rephrase the following lever topics: [list]."
Expected effect: Reduce cross-call duplication from ~50-100% to near zero.
Motivated by: N5, run 28 parasomnia evidence.

**H5 — Separate the review trade-off and weakness into two explicit sub-fields**
The single `review` field is hard for some models to fill correctly with both components.
Change: Split into `review_tradeoff` ("Controls A vs. B.") and `review_weakness` ("Weakness: ...") in the schema and prompt. Or add an explicit two-part formatting rule: "The review MUST contain two sentences: sentence 1 starts with 'Controls', sentence 2 starts with 'Weakness:'."
Expected effect: Improve review completeness from ~50% to >80%.
Motivated by: N6, quantitative table in Quantitative Metrics section.

---

## Summary

Runs 24-31 test 8 different LLM configurations against the same prompt (SHA: `fa5dfb88...`). Overall reliability is 62.5% (25/40 plans), with four distinct failure modes: empty output (nemotron, context window too small), truncated JSON (gpt-oss-20b, output token limit), missing schema wrapper fields (gpt-4o-mini, schema compliance), and API timeout (claude-haiku on parasomnia).

The best-performing model is **qwen3-30b-a3b** (run 29): 5/5 success, minimal template leakage, good domain specificity. Claude Haiku (run 31) is a close second (4/5, one timeout).

The most actionable content issues are:
1. **Pervasive "25% faster scaling" leakage** — caused by prompt example text being copied verbatim (H1)
2. **Cross-call semantic duplication** — 3 LLM calls producing near-identical lever topics (H4, C3)
3. **Review field incompleteness** — models reliably produce only half the review requirement (H5)

The most actionable code issues are:
1. **gpt-4o-mini fails on schema wrapper** — making `strategic_rationale`/`summary` optional would recover 40% of its failures (C1)
2. **Context window guard** — nemotron's 3900-token window is fatal for complex plans (C2)

The prompt itself is sound for high-capability models but requires two small changes to eliminate boilerplate leakage: remove the numeric example ("25% faster scaling") and remove the specific lever name example ("Material Adaptation Strategy").
