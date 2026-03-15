# Insight Claude

**Prompt**: `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`
**History runs**: 60–66 (`history/0/60_identify_potential_levers` … `history/0/66_identify_potential_levers`)

---

## Rankings

Quality tier by run (best to worst, counting only successful outputs):

| Rank | Run | Model | Success | Content Quality |
|------|-----|-------|---------|-----------------|
| 1 | 66 | anthropic-claude-haiku-4-5-pinned | 4/5 | Excellent – domain-grounded, rich numeric estimates |
| 2 | 63 | openai-gpt-5-nano | 5/5 | Good – detailed options, strong specificity |
| 3 | 62 | openrouter-openai-gpt-oss-20b | 4/5 | Good – well-formed options with measurable indicators |
| 4 | 64 | openrouter-qwen3-30b-a3b | 5/5 | Moderate – short options, some cross-call duplication |
| 5 | 61 | ollama-llama3.1 | 5/5 | Mixed – first call good, 2nd/3rd calls use label-only options |
| 6 | 65 | openrouter-openai-gpt-4o-mini | 5/5 | Weak – heavy template leakage, generic lever names |
| 7 | 60 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | Total failure |

---

## Negative Things

### N1 — Total JSON extraction failure (Run 60)
All 5 plans in run 60 (`history/0/60_identify_potential_levers/outputs.jsonl`) errored identically:
```
ValueError('Could not extract json string from output: ')
```
Model `openrouter-nvidia-nemotron-3-nano-30b-a3b` produced output that the pipeline could not parse as JSON at all. Duration was 92–113 s per plan (the model responded, but the response was not parseable). Zero successful outputs.

### N2 — Schema validation failure (Run 66, hong_kong_game)
Run 66 (`history/0/66_identify_potential_levers/outputs.jsonl`) failed on `20260310_hong_kong_game` in 4.81 s:
```
2 validation errors for DocumentDetails
levers  Field required [type=missing, ...]
summary  Field required [type=missing, ...]
```
The error input value shown is `{'strategic_rationale': "...t mainland box office,"}` — the model produced only a `strategic_rationale` key at the top level without wrapping it in the expected `DocumentDetails` structure (`levers` + `summary`). The same model succeeded on all four other plans (see `history/0/66_identify_potential_levers/outputs.jsonl`), so this is not a general model failure but a plan-specific edge case.

### N3 — Lever count inflation in llama3.1 (Run 61)
The prompt says **EXACTLY 5 levers per response**. Examining `history/0/61_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`:
- Response 1: 5 levers ✓
- Response 2: 7 levers ✗
- Response 3: 7 levers ✗

The merged `002-10-potential_levers.json` contains 20 levers for silo instead of 15 (3 calls × 5). The root cause is `num_output: 256` in the llama3.1 metadata (extremely low output token limit), which truncates responses mid-generation. The pipeline still accepts the oversized responses from calls 2/3.

### N4 — Label-only options (Run 61, calls 2 and 3)
The prompt requires options to be *complete strategic approaches*, prohibits generic labels, and mandates conservative→moderate→radical progression with full sentences. In llama3.1 calls 2/3, options are 2–4 word noun phrases:
- `"Hierarchical Governance"`
- `"Decentralized Community Management"`
- `"Holistic Ecosystem Stewardship"`
- `"Closed-Loop Life Cycle Management"`
- `"Predictive Analytics-Driven Defense"`

These are labels, not strategic approaches. Evidence: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, responses 2 and 3. The `num_output: 256` limit likely forces the model to abbreviate aggressively (see C1).

### N5 — Incomplete review fields (Run 61)
Several levers in llama3.1 responses 2/3 omit either the trade-off statement or the weakness:
- `"Controls Power Dynamics vs. Fosters Resident Autonomy."` — missing the `Weakness:` clause
- `"Weakness: The options fail to consider the impact of emerging technologies on resource management."` — missing the `Controls [A] vs. [B].` clause

The prompt requires **both** parts in `review_lever`. Evidence: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, response 2, levers `Silo-Cohesion Strategy` and `Resource-Resilience Strategy`.

### N6 — Heavy template leakage / "Silo-" prefix pattern (Run 65)
All 15 lever names in run 65's silo output start with "Silo-":
`"Silo-Resource Allocation Strategy"`, `"Silo-Community Governance Strategy"`, `"Silo-Information Control Strategy"` (appears **twice** with different UUIDs), `"Silo-Ecosystem Sustainability Strategy"`, …

This is the `[Domain]-[Decision Type] Strategy` format from the prompt, but applied robotically to every lever and producing two levers with the exact same name. Evidence: `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### N7 — Exact lever-name duplication across calls (Runs 65, 61)
- Run 65/silo: `"Silo-Information Control Strategy"` appears at lever 3 and lever 13 (different UUIDs, same name).
- Run 61/silo: `"Economy-Empowerment Strategy"` appears at positions 12 and 17 with different content (different economic angle, same lever name). Evidence: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### N8 — Consequences chain vagueness in run 65
Run 65 (`gpt-4o-mini`) consequences often lack the domain-specific measurable indicator required in the Systemic step. Example from `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
> "Immediate: Establish a governance framework for community decision-making → Systemic: Improve resident satisfaction scores by 30% through participatory governance → Strategic: This fosters a sense of ownership but may complicate enforcement of rules."

The 30% figure is bare, unanchored, and appears in another lever as well. The "strategic" step restates a risk rather than describing an implication. Compare with run 66's depth (see Positive N1).

---

## Positive Things

### P1 — Run 66 (claude-haiku) produces highly domain-specific, quantitatively grounded levers
For `20260311_parasomnia_research_unit`, run 66 generated levers with:
- Specific numeric ranges anchored to domain context: `"Raising the inclusion bar from '≥2 episodes/month self-reported' to '≥4 episodes/month' increases per-participant event yield by approximately 35–45%, reducing average stay length from 6 weeks to 4 weeks and lowering per-event cost by ~25%"`
- Full paragraph-length options that are self-contained strategic approaches
- Weaknesses that identify non-obvious second-order problems (e.g., scorer fatigue, model overfitting to small datasets, seasonal variation in parasomnia frequency)

Evidence: `history/0/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`

### P2 — Run 63 (gpt-5-nano) produces detailed options with specific numbers
For silo, gpt-5-nano produces levers like `"Governance Legitimacy & Rule Enforcement"` with consequences stating:
> "Autocracy requires 15–20% of population as enforcers/surveillance, reducing productive capacity by ~25%; democratic models increase compliance by ~30% but slow emergency decisions by 60–90%"

Options are full paragraphs with distinct strategic pathways. Evidence: `history/0/63_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### P3 — Run 62 (gpt-oss-20b) shows clean Immediate→Systemic→Strategic formatting
Run 62 silo levers consistently use the arrow chain with measurable Systemic steps:
> "Systemic: The construction timeline shrinks by 20%, yet the defect rate rises by 15%, as measured by post-construction inspection reports"

Evidence: `history/0/62_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### P4 — Run 65 (gpt-4o-mini) is the fastest at 33–40 s per plan
All 5 plans succeeded in 33–40 s, the fastest of any run (run 66 is similar for successful plans but errored in 4.81 s on hong_kong). Evidence: `history/0/65_identify_potential_levers/outputs.jsonl`.

### P5 — Run 63 (gpt-5-nano) includes `strategic_rationale` in raw responses
Run 63 raw files contain a `strategic_rationale` preamble per call that describes the core tensions the levers are meant to address. This adds analytical framing not directly required by the prompt. Example: `"This megastructure project faces three irreconcilable tensions: (1) maintaining totalitarian control while preserving population morale…"` Evidence: `history/0/66_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` (run 66 also produces this).

---

## Comparison

### vs. Baseline (`baseline/train/20250321_silo/002-10-potential_levers.json`)

The baseline silo output contains 15 levers with well-formed consequences chains (some using `Immediate: → Systemic: [%] → Strategic:` format), full-sentence options, and reviews that include both the trade-off and weakness. Lever names are human-readable but not all follow `[Domain]-[Decision Type] Strategy` format (e.g., `"Resource Allocation Strategy"`, `"Social Control Mechanism"`).

Comparison:
- **Structural validity**: Baseline ≈ runs 62/63/66 for successful outputs. Run 61 (calls 2/3) is worse; run 65 has template leakage.
- **Option depth**: Baseline ~1–2 sentences per option. Run 66 options are 2–4× longer with domain-specific detail. Run 65 options are comparable to baseline.
- **Measurability**: Baseline has consistent % indicators. Runs 63 and 66 exceed this. Runs 61/64/65 are comparable to baseline on most levers.
- **Domain specificity**: Baseline silo levers address governance, information control, resource allocation, societal structure — relevant but broad. Run 66's parasomnia levers show uniquely high domain grounding, addressing regulatory specifics (AASM criteria, DFG reprofiling, Bonn real estate lead times).

---

## Quantitative Metrics

### Operational reliability

| Run | Model | Plans OK / Total | Error Type |
|-----|-------|-----------------|------------|
| 60 | nvidia-nemotron-3-nano-30b-a3b | 0/5 | JSON extraction failure |
| 61 | ollama-llama3.1 | 5/5 | — |
| 62 | openrouter-openai-gpt-oss-20b | 4/5 | JSON extraction failure (sovereign_identity) |
| 63 | openai-gpt-5-nano | 5/5 | — |
| 64 | openrouter-qwen3-30b-a3b | 5/5 | — |
| 65 | openrouter-openai-gpt-4o-mini | 5/5 | — |
| 66 | anthropic-claude-haiku-4-5-pinned | 4/5 | Pydantic schema validation failure (hong_kong_game) |

### Timing (seconds per plan)

| Run | Model | Min | Max | Avg (approx.) |
|-----|-------|-----|-----|---------------|
| 60 | nemotron-nano | 92 | 113 | ~99 |
| 61 | llama3.1 | 86 | 123 | ~101 |
| 62 | gpt-oss-20b | 27 | 147 | ~75 |
| 63 | gpt-5-nano | 214 | 252 | ~235 |
| 64 | qwen3-30b | 85 | 181 | ~121 |
| 65 | gpt-4o-mini | 34 | 41 | ~37 |
| 66 | claude-haiku | 5 | 144 | ~120 (excl. error) |

### Lever count per plan

All successful runs produce 15 levers per plan (3 sub-calls × 5 per call), **except** run 61 (llama3.1), which produced 20 levers for silo (calls 2/3 returned 7 levers each instead of 5).

| Run | Levers/plan (silo) | Constraint (3×5=15) |
|-----|-------------------|--------------------|
| 61 | 20 | VIOLATION (calls 2+3 returned 7 each) |
| 62 | 15 | OK |
| 63 | 15 | OK |
| 64 | 15 | OK |
| 65 | 15 | OK |
| 66 | 15 | OK |

### Option quality (silo, 15 levers)

"Full approach" = option text is a complete sentence describing a distinct pathway (≥10 words, not just a noun phrase).

| Run | Options as full approaches | Options as labels (<5 words) | Prefix violations |
|-----|--------------------------|------------------------------|-------------------|
| 61 | ~15/45 (first call only) | ~30/45 (calls 2–3) | 0 |
| 62 | 45/45 | 0 | 0 |
| 63 | 45/45 | 0 | 0 |
| 64 | ~30/45 | ~15/45 | 0 |
| 65 | 45/45 | 0 | 0 |
| 66 | 45/45 | 0 | 0 |

### Review field compliance (silo, 15 levers)

Prompt requires both `Controls [A] vs. [B].` AND `Weakness: The options fail to consider [X].` in each review.

| Run | Both parts present | Missing weakness | Missing trade-off |
|-----|-------------------|-----------------|-------------------|
| 61 | ~5/20 fully | ~10/20 missing weakness | ~5/20 missing trade-off |
| 62 | 15/15 | 0 | 0 |
| 63 | 15/15 | 0 | 0 |
| 64 | ~12/15 | ~3 fused/partial | 0 |
| 65 | 15/15 | 0 | 0 |
| 66 | 15/15 | 0 | 0 |

### Cross-call duplication (lever name collisions, silo)

| Run | Duplicate lever names | Example |
|-----|-----------------------|---------|
| 61 | 1 (`Economy-Empowerment Strategy` ×2) | Positions 12 and 17 |
| 62 | 0 | — |
| 63 | 0 | — |
| 64 | 0 | — |
| 65 | 1 (`Silo-Information Control Strategy` ×2) | Positions 3 and 13 |
| 66 | 0 | — |

### Approximate avg. consequences field length (chars, silo levers)

Estimated from sampled levers (first 5 of each run):

| Run | Avg consequence length (chars) |
|-----|-------------------------------|
| 61 (call 1) | ~180 |
| 61 (calls 2–3) | ~140 |
| 62 | ~280 |
| 63 | ~400 |
| 64 | ~200 |
| 65 | ~180 |
| 66 | ~500 |
| Baseline | ~220 |

### Template leakage ("Silo-" prefix on lever names, silo)

| Run | % of lever names starting with "Silo-" |
|-----|----------------------------------------|
| 61 | 0% (names like "Silo-Scale Strategy" only in call 1) |
| 62 | 0% |
| 63 | 0% |
| 64 | 0% |
| 65 | 100% (all 15 names) |
| 66 | ~47% (7/15 names) |
| Baseline | 0% |

---

## Evidence Notes

1. **Run 60 failure**: `history/0/60_identify_potential_levers/outputs.jsonl` — all 5 entries have `"status": "error"` and `"Could not extract json string from output: "`.

2. **Run 61 lever count violation**: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` — `responses[1].levers` has 7 entries (indices 1–7), `responses[2].levers` has 7 entries (indices 0–6). `metadata_1.num_output: 256` confirms the extremely low output token ceiling.

3. **Run 61 label-only options**: ibid., `responses[1].levers[0].options` = `["Hierarchical Governance", "Decentralized Community Management", "Holistic Ecosystem Stewardship"]` — 2–3 word noun phrases, not strategic approaches.

4. **Run 62 single failure**: `history/0/62_identify_potential_levers/outputs.jsonl` — `20260308_sovereign_identity` errored with same "Could not extract json string from output" as run 60.

5. **Run 63 quality evidence**: `history/0/63_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — e.g., "Governance Legitimacy & Rule Enforcement" with 200-word consequences including "Autocracy requires 15–20% of population as enforcers…".

6. **Run 65 template leakage**: `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all lever names start "Silo-", and names 3 and 13 are both `"Silo-Information Control Strategy"`.

7. **Run 66 schema failure**: `history/0/66_identify_potential_levers/outputs.jsonl` — `20260310_hong_kong_game` errored with `levers Field required` and `summary Field required`. The `input_value` shown is `{'strategic_rationale': "...t mainland box office,"}` — model produced only `strategic_rationale` without the full `DocumentDetails` wrapper.

8. **Run 66 quality evidence**: `history/0/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — levers like "Participant Pre-Screening Stringency" with multi-paragraph options containing quantitative specifics (`≥4 episodes/month`, `35–45% increase in per-participant event yield`, `€80–120K capital cost`).

9. **Baseline comparison**: `baseline/train/20250321_silo/002-10-potential_levers.json` — well-formed structure with measurable % indicators in Systemic steps, full-sentence options, but options ~1–2 sentences max vs. run 66's multi-sentence paragraphs.

---

## Questions For Later Synthesis

1. **Is run 66's failure on hong_kong_game a prompt issue or a parsing/schema issue?** The error shows the model produced `strategic_rationale` without `levers`/`summary`. Does the hong_kong plan.txt trigger a different reasoning path? Or is the pipeline's Pydantic schema too strict for partial responses? (C1 below addresses this.)

2. **Does the pipeline deduplicate levers across sub-calls before writing `002-10-potential_levers.json`?** Runs 61 and 65 have duplicate lever names from different calls. If deduplication is absent in code, is it worth adding?

3. **Is 15 levers per plan (3 calls × 5) the intended contract?** The prompt says "EXACTLY 5 per response" — this is per-call, and the pipeline makes 3 calls. The `002-10-potential_levers.json` output has 15 items. Is the downstream consumer of these levers designed for 15, or would it work better with 5 or 10?

4. **Why does run 63 (gpt-5-nano) take 213–252 s per plan?** Is this a model latency issue, or is the pipeline doing more work (retries, post-processing)? Does the quality benefit justify the 6× slowdown vs. gpt-4o-mini?

5. **llama3.1's `num_output: 256` is set per-call — is this a config bug?** At 256 tokens, generating 5 levers with full consequences is barely feasible; generating 7 levers in that window forces abbreviation. This may explain why calls 2/3 return label-only options.

---

## Reflect

This batch tests 7 models against the same prompt_1. The failure modes cluster into three distinct types:
1. **JSON unparseable output** (nemotron-nano, gpt-oss-20b): the model responds but doesn't follow JSON structure.
2. **Schema validation mismatch** (claude-haiku/hong_kong): the model follows a valid JSON structure but uses top-level keys that don't match the expected Pydantic model.
3. **Semantic constraint violations** (llama3.1): the model produces structurally valid JSON but violates content constraints (lever count, option quality).

The most informative finding is the quality spread: claude-haiku (run 66) produces remarkably rich, domain-specific output when it succeeds — but its single failure is also the most diagnostic. The failure reveals that the Pydantic schema validation happens at the very first response of a plan, and a single incorrect response structure kills the entire plan even if subsequent calls would have succeeded.

The gpt-4o-mini run (65) is the most "reliable" by count (5/5, 33–40 s) but shows the heaviest template leakage and lowest content quality. This is a common over-fitting-to-format pattern: the model correctly identifies and mimics the [Domain]-[Decision Type] pattern from the prompt but applies it robotically without domain reasoning.

---

## Potential Code Changes

**C1 — Add retry/fallback for schema-only partial responses (addresses N2)**

The run 66 hong_kong error shows the model returned `{'strategic_rationale': ...}` without the expected `levers` and `summary` fields. The pipeline immediately fails rather than retrying. A code-level fix: if a Pydantic `DocumentDetails` validation fails but the raw response contains a `strategic_rationale` key without `levers`, retry the call with an explicit instruction to complete the levers array. This would recover the plan without wasting the strategic_rationale that was generated.

Evidence: `history/0/66_identify_potential_levers/outputs.jsonl` — `20260310_hong_kong_game` failed in 4.81 s; the silo raw file (`002-9-potential_levers_raw.json` for run 66) shows the expected structure has `strategic_rationale` inside a response object alongside `levers` and `summary`.

**C2 — Cap the `num_output` floor for llama3.1 at ≥2048 tokens (addresses N3, N4)**

The `metadata.num_output: 256` setting for llama3.1 (run 61) is almost certainly the cause of truncated options and over-count levers. At 256 tokens, generating 5 complete levers (each ~100+ tokens) is impossible. The pipeline should validate that `num_output` is ≥ some minimum before running, or the model config should set a higher value.

Evidence: `history/0/61_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`, `metadata_1.num_output: 256`.

**C3 — Add cross-call deduplication for lever names (addresses N7)**

When the pipeline merges results from 3 sub-calls into `002-10-potential_levers.json`, it should check for name collisions. If the same lever name appears in two calls, one copy should be dropped or renamed. Runs 61 and 65 both produced duplicate lever names; the downstream consumer likely gets confused by two levers with identical names.

Evidence: `history/0/65_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — `"Silo-Information Control Strategy"` at indices 3 and 13.

---

## Hypotheses

**H1 — The "[Domain]-[Decision Type] Strategy" example format in the prompt causes template over-application**
The prompt specifies `"[Domain]-[Decision Type] Strategy"` as the naming pattern. Run 65 applied this to every single lever name with "Silo-" prefix, losing domain specificity.

*Proposed change*: Remove the explicit format example from the prompt and instead describe the naming intent: "Name each lever as a strategic decision domain specific to the project (e.g., using domain-relevant terminology that would be recognized by a practitioner in this field)."

*Expected effect*: Models will generate names that reflect the actual domain (e.g., "Information Lockdown vs. Transparency Policy" for silo, "Recruitment Stringency Protocol" for parasomnia) without robotically applying a single template.

**H2 — The "Weakness: The options fail to consider [factor]." formula is too rigid and produces generic weaknesses**
The prompt prescribes this exact phrasing. Every run produces this phrasing almost verbatim, but the actual weakness is often thin (e.g., "fails to consider the psychological impact" appears multiple times across different levers).

*Proposed change*: Replace the rigid formula with: `"Identify the most important overlooked constraint, second-order effect, or stakeholder concern that the options collectively miss. Write it as a crisp statement (1–2 sentences), not a template phrase."` Remove the `"Weakness: The options fail to consider"` prefix requirement.

*Expected effect*: More variety in weakness content; less copy-paste feel across levers.

**H3 — Consequences chains frequently omit the trade-off requirement despite being listed**
The prompt says consequences must "explicitly describe trade-offs between core tensions." Many runs include weak trade-off descriptions or embed them only in the review field. Run 63 and 66 do this well; runs 61 call 1, 64, and 65 often do not.

*Proposed change*: Add an explicit example to the consequences format: `"Consequences MUST end with: 'Trade-off: [Option A approach] reduces [X] but risks [Y]; [Option B approach] gains [Y] but costs [X].' This trade-off sentence is REQUIRED."`

*Expected effect*: Consistently explicit trade-off articulation in the consequences chain, reducing reliance on the review field to carry this weight.

**H4 — The "EXACTLY 5 levers" constraint is over-specified per-response but silent on the cross-call contract**
The prompt says "EXACTLY 5 levers per response" but says nothing about the pipeline making 3 calls per plan. Some models (llama3.1) violate the per-call constraint; no models violate the 15-total count except llama3.1. If the pipeline is the place that controls call count, this constraint belongs in code, not the prompt.

*Proposed change (code level — C4)*: Add an assertion in the pipeline that validates each sub-call returned exactly 5 levers before merging. If a call returned more than 5, truncate to first 5. If fewer than 5, retry the call. This prevents cross-call inflation silently corrupting the final output.

---

## Summary

Seven models were tested against the current prompt_1 across 5 plans each (35 plan-runs total). Key findings:

| Metric | Value |
|--------|-------|
| Total plan-runs | 35 |
| Successful | 28 (80%) |
| Failed: JSON unparseable | 6 (runs 60 all, run 62 one) |
| Failed: schema validation | 1 (run 66, hong_kong) |
| Lever count violations (per call) | 2 calls in run 61 |
| Option label violations (full plan) | ~30/45 options in run 61 calls 2–3 |
| Duplicate lever names | 1 each in runs 61 and 65 |
| Template leakage ("Silo-" prefix all levers) | Run 65 100% of lever names |

**Strongest content quality**: run 66 (claude-haiku) — highly domain-specific, realistic numeric estimates, multi-paragraph options that are genuine strategic approaches. The silo (run 63 / gpt-5-nano) result is also strong. Both exceed baseline quality.

**Most reliable by success rate**: runs 63, 64, 65 (5/5 each). Run 65 (gpt-4o-mini) is fastest but has the weakest content quality of the successful models.

**Primary actionable issues**:
1. **C1** (code): Handle the partial-response case in schema validation — retry when `strategic_rationale` is present but `levers`/`summary` are missing.
2. **C2** (code): Set a minimum `num_output` guard for models like llama3.1 that have extremely low token limits.
3. **C3** (code): Deduplicate lever names across sub-calls before merging.
4. **H1** (prompt): Remove the "[Domain]-[Decision Type] Strategy" naming template to reduce format over-application.
5. **H2** (prompt): Replace the rigid "Weakness: The options fail to consider…" formula with an open-ended oversight instruction.
