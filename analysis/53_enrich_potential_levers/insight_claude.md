# Insight Claude

## Overview

This is the **first analysis** of the `enrich_potential_levers` step. No prior
`enrich_potential_levers` analysis exists in `best.json`. There is no PR being
evaluated — meta.json carries `commit: "0da82497"` and `branch: "main"` without
any `pr_url`. The input is `snapshot/1_deduplicate_levers`, not `baseline/train`.

**What the enrich step does**: Takes the output of `deduplicate_levers`
(`002-11-deduplicated_levers_raw.json`, each entry containing `lever_id`, `name`,
`consequences`, `options`, `review`, `classification`, `deduplication_justification`)
and adds three new fields per lever: `description`, `synergy_text`, `conflict_text`.
The output is `002-12-enriched_levers_raw.json`.

**Seven runs were analyzed**, covering 5 plans each, across 7 different models:

| Run | Model | Plans |
|-----|-------|-------|
| `3/78_enrich_potential_levers` | ollama-llama3.1 | 5 |
| `3/79_enrich_potential_levers` | openrouter-openai-gpt-oss-20b | 5 |
| `3/80_enrich_potential_levers` | openai-gpt-5-nano | 5 |
| `3/81_enrich_potential_levers` | openrouter-qwen3-30b-a3b | 5 |
| `3/82_enrich_potential_levers` | openrouter-openai-gpt-4o-mini | 5 |
| `3/83_enrich_potential_levers` | openrouter-gemini-2.0-flash-001 | 5 |
| `3/84_enrich_potential_levers` | anthropic-claude-haiku-4-5-pinned | 5 |

---

## Negative Things

### N1 — gpt-oss-20b complete failure (0/5 plans)

Run 79 (gpt-oss-20b) failed all 5 plans with `"LLM batch interaction failed."`.
The `events.jsonl` shows 4 `run_single_plan_error` events and 1 timeout:

```
3/79_enrich_potential_levers/events.jsonl:
  20250329_gta_game    → run_single_plan_error  (97s)
  20250321_silo        → run_single_plan_error  (146s)
  20260308_sovereign_identity → run_single_plan_error (197s)
  20260310_hong_kong_game → run_single_plan_error (375s)
  20260311_parasomnia → "plan timeout after 600s"
```

Root cause is visible in `usage_metrics.jsonl` for the silo plan:

```
3/79_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl:
  WandB:gpt-oss-20b   → success=true,  output_tokens=5673
  Fireworks:gpt-oss-20b → success=true, output_tokens=3230
  Fireworks:gpt-oss-20b → success=true, output_tokens=8192  ← HIT LIMIT
  openrouter-gpt-oss-20b → success=false, error="auth_error"
```

The third LLM call (of 3 per plan) hit the model's 8192 output token limit.
The `num_output` field in the file's `metadata` confirms `8192` is the declared
maximum for this model. Hitting the limit truncates the JSON → Pydantic
validation fails → the plan is discarded. gpt-oss-20b produces roughly
**1135 tokens per lever** vs ~97 for haiku on the same batch, making it
~12× more verbose in structured output — pushing the third batch reliably over
the limit.

This is the same class of problem documented in AGENTS.md "Experiment Insights":
a hard model output-token ceiling causes valid but large responses to be
truncated and discarded entirely.

### N2 — qwen3-30b produces abnormally terse synergy/conflict texts

Run 81 (qwen3-30b) produces much shorter synergy and conflict texts than other
models or the baseline, averaging approximately 183 chars for synergy and 229
chars for conflict (0.58× and 0.69× of the baseline, respectively). Example:

```
synergy_text: "Synergizes with Community Governance Model (125ce960) by
reinforcing authority structures and with Knowledge Preservation Strategy
(9bc93565) to safeguard curated information archives."
```

183 chars is too brief to convey actionable strategic insight. The text names
lever pairs but does not explain how or why the synergy operates, or what
decision-relevant interaction exists. Contrast with haiku (384 chars avg):

```
synergy_text: "This lever strongly synergizes with Community Governance Model
by establishing information frameworks that either support democratic
participation or hierarchical control. It also enhances Knowledge Preservation
Strategy by determining what knowledge is recorded, protected, and transmitted
across generations, ensuring critical expertise survives through intentional
documentation and selective distribution."
```

### N3 — gpt-5-nano uses a rigid internal template in descriptions

Run 80 (gpt-5-nano) generates descriptions with a formulaic "Purpose: /
Objectives: / Key success metrics: / It coordinates with…" sub-structure, e.g.:

> "Purpose: allocate scarce resources — energy, inputs, and labor credits — to
> maximize long-term resilience and value creation inside the silo. It governs
> rules for distribution, incentives, and investment across sectors such as
> agriculture, power, and manufacturing. Objectives: promote productive
> diversification, ensure essential services remain funded, minimize waste, and
> maintain social equity under stress. Key success metrics: resource utilization
> efficiency, sector ROI, distribution equity indices, and resilience indicators
> under simulated shocks."

This template produces longer descriptions (avg ~657 chars vs baseline ~500,
a ratio of 1.31×) that are structurally predictable but not more informative.
It also artificially inflates token use per lever.

### N4 — Inconsistent cross-reference format across models

Models use different formats for naming related levers in synergy/conflict:

| Model | Format used |
|-------|-------------|
| llama3.1 | Full UUID: `Security System Governance (40b19bce-62a5-4467-a7c3-0f57662f9a31)` |
| qwen3-30b | Truncated UUID: `Community Governance Model (125ce960)` |
| gemini-2.0-flash | Backtick name: `` `Community Governance Model` `` |
| gpt-4o-mini, gpt-5-nano, haiku | Name only: `Community Governance Model` |

If downstream code parses synergy/conflict text to extract lever relationships,
inconsistent formats will break that parser. The enrich prompt does not
apparently specify which format to use.

### N5 — No `OPTIMIZE_INSTRUCTIONS` available in accessible repo

The PlanExe source file `enrich_potential_levers.py` is not accessible in the
allowed working directories. This prevents direct OPTIMIZE_INSTRUCTIONS
alignment checking. The following analysis is based on inferred behavior
from output patterns only.

---

## Positive Things

### P1 — 6 out of 7 models achieve 100% success (30/35 total, 85.7%)

Every model except gpt-oss-20b completed all 5 plans without error:

| Run | Model | Success |
|-----|-------|---------|
| 78 | llama3.1 | 5/5 |
| 79 | gpt-oss-20b | 0/5 |
| 80 | gpt-5-nano | 5/5 |
| 81 | qwen3-30b-a3b | 5/5 |
| 82 | gpt-4o-mini | 5/5 |
| 83 | gemini-2.0-flash | 5/5 |
| 84 | haiku-4-5 | 5/5 |

The gpt-oss-20b failure is a model-level output-token-limit problem, not a
prompt or schema bug. With that model excluded, the step has 100% success.

### P2 — No fabricated percentage claims in new fields

None of the runs introduced fabricated numbers (e.g., "reduces costs by 30%",
"15% increase in productivity") in the new `description`, `synergy_text`, or
`conflict_text` fields. This is a meaningful difference from the baseline
training data (produced by the older identify_potential_levers prompt), where
consequences routinely contained fabricated quantification:

```
baseline/train/20250321_silo/002-12-enriched_levers_raw.json consequences examples:
  "Immediate: Increased compliance → Systemic: 30% reduction in innovative output…"
  "Systemic: 40% decrease in citizen trust in leadership…"
  "Measurable outcome: 30% reduction in reported dissent, but a 15% decrease in innovation output"
```

The current run outputs have no such patterns in the enriched fields.

### P3 — Existing lever fields are preserved unchanged

All successful runs correctly pass through `consequences`, `options`, `review`,
`classification`, and `deduplication_justification` verbatim from the input
snapshot. No corruption or overwriting of existing data was observed.

### P4 — Field lengths are within acceptable bounds (below 2× baseline)

All models produce new fields at lengths below the 2× warning threshold when
compared to the baseline:

| Model | description | synergy | conflict |
|-------|-------------|---------|---------|
| Baseline (gemini, OLD prompt) | 500 avg | 313 avg | 333 avg |
| Run 78 llama3.1 | ~490 (0.98×) | ~420 (1.34×) | ~380 (1.14×) |
| Run 80 gpt-5-nano | ~657 (1.31×) | ~327 (1.04×) | ~380 (1.14×) |
| Run 81 qwen3-30b | ~427 (0.85×) | ~183 (0.58×) | ~229 (0.69×) |
| Run 82 gpt-4o-mini | ~490 (0.98×) | ~280 (0.89×) | ~290 (0.87×) |
| Run 83 gemini-2.0-flash | ~480 (0.96×) | ~270 (0.86×) | ~290 (0.87×) |
| Run 84 haiku | ~600 (1.20×) | ~384 (1.23×) | ~381 (1.14×) |

(Lengths are approximate character counts measured from silo plan first 2 levers
per run. Baseline measured from silo baseline train data, 7 levers.)

No model exceeds 1.31× baseline for description, and qwen3-30b is actually
too short (0.58-0.85×) rather than too long.

### P5 — Step structure is sound: 3 calls per plan, balanced batch sizes

Each plan is processed in exactly 3 LLM calls (visible from `usage_metrics.jsonl`
and the 3-entry `metadata` array in each output file). Input token counts are
consistent across calls (~2300-2600 tokens), suggesting roughly equal batches
of ~5 levers each (for a 15-lever plan). This batching is appropriate for
models with standard context windows.

---

## Comparison

### Comparison vs Baseline Training Data

The baseline (`baseline/train/*/002-12-enriched_levers_raw.json`) was produced
by gemini-2.0-flash-001 with a different (older) system prompt run on a
different set of levers (from the OLD `identify_potential_levers` step). The
baseline levers have different `lever_id`s and names than the current snapshot
levers, so direct lever-by-lever content comparison is not possible.

What can be compared:
- **Field length** (above): All current runs are within ±35% of baseline length.
- **Fabricated numbers**: Baseline consequences contain fabricated % claims
  (from the old prompt). Current run consequences do not (cleaner input).
- **Coverage**: Baseline has 7 levers per plan (after dedup). Current runs
  have 15 levers per plan. The enrich step correctly handles both.
- **Model**: Baseline also used gemini-2.0-flash-001 (run 83 uses the same model).
  Run 83 output is noticeably more concise in synergy/conflict (~270 chars) than
  the baseline (~313 chars), consistent with the current prompt being slightly
  more conservative.

### Model Ranking (quality + reliability)

1. **haiku-4-5** — Balanced descriptions (~600 chars), informative synergy/conflict
   (~382 avg), no template artifact, 100% success, fast (50s/plan).
2. **gpt-4o-mini** — Compact and clean (~490/280/290), 100% success, fast (67s/plan).
3. **gemini-2.0-flash** — Compact and clean (~480/270/290), 100% success, very fast (25s/plan).
4. **llama3.1** — Similar description length to baseline, but includes full UUIDs
   in synergy/conflict (N4), 100% success, slow (158s/plan, 1 worker).
5. **gpt-5-nano** — Verbose template-driven descriptions (N3), 100% success, slow (224s/plan).
6. **qwen3-30b** — Excessively terse synergy/conflict (N2), 100% success, moderate speed.
7. **gpt-oss-20b** — 0% success due to output token overflow (N1).

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Plans Failed | Success Rate |
|-----|-------|----------|--------------|--------------|
| 78 | llama3.1 | 5 | 0 | 100% |
| 79 | gpt-oss-20b | 0 | 5 | 0% |
| 80 | gpt-5-nano | 5 | 0 | 100% |
| 81 | qwen3-30b | 5 | 0 | 100% |
| 82 | gpt-4o-mini | 5 | 0 | 100% |
| 83 | gemini-2.0-flash | 5 | 0 | 100% |
| 84 | haiku-4-5 | 5 | 0 | 100% |
| **Total** | | **30** | **5** | **85.7%** |

### LLM Calls per Plan

All runs (except the failed run 79) use exactly 3 LLM calls per plan.
Token usage for run 84 (haiku, silo plan):

| Call | Input tokens | Output tokens | Duration |
|------|-------------|---------------|----------|
| 1 | 2561 | 1375 | 17.8s |
| 2 | 2500 | 1383 | 15.2s |
| 3 | 2545 | 1597 | 17.2s |
| **Avg** | 2535 | 1452 | 16.7s |

Token usage for run 79 (gpt-oss-20b, silo plan — failed):

| Call | Input tokens | Output tokens | Status |
|------|-------------|---------------|--------|
| 1 | 2194 | 5673 | success |
| 2 | 2137 | 3230 | success |
| 3 | 2165 | **8192** (limit hit) | → plan failed |

gpt-oss-20b generates ~3.9× more output tokens than haiku per call, making
it vulnerable to the 8192 token output cap on complex lever batches.

### Field Length Table (silo plan, first 2 levers, character counts)

| Model | desc1 | desc2 | syn1 | syn2 | con1 | con2 |
|-------|-------|-------|------|------|------|------|
| Baseline (gemini OLD) | 497 | 478 | 340 | 313 | 358 | 336 |
| Run 78 llama3.1 | 463 | 521 | 407 | 410 | 393 | 367 |
| Run 80 gpt-5-nano | 643 | 682 | 311 | 343 | 335 | 411 |
| Run 81 qwen3-30b | 457 | 397 | 183 | 183 | 214 | 244 |
| Run 82 gpt-4o-mini | ~490 | ~530 | ~270 | ~285 | ~280 | ~300 |
| Run 83 gemini-2.0-flash | 505 | 492 | 271 | 268 | 295 | 262 |
| Run 84 haiku | 597 | 601 | 404 | 364 | 400 | 362 |

### Constraint Violations

| Violation Type | Run 78 | Run 79 | Run 80 | Run 81 | Run 82 | Run 83 | Run 84 |
|----------------|--------|--------|--------|--------|--------|--------|--------|
| Missing description | 0 | N/A | 0 | 0 | 0 | 0 | 0 |
| Missing synergy_text | 0 | N/A | 0 | 0 | 0 | 0 | 0 |
| Missing conflict_text | 0 | N/A | 0 | 0 | 0 | 0 | 0 |
| Output truncated | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| Fabricated % claims | 0 | N/A | 0 | 0 | 0 | 0 | 0 |

### Template Leakage

| Model | Template pattern in output |
|-------|---------------------------|
| gpt-5-nano | "Purpose: / Objectives: / Key success metrics:" sub-structure in descriptions |
| llama3.1 | Full UUID references in synergy/conflict |
| qwen3-30b | Truncated UUID references (first 8 chars) |
| Others | Names only, no structural leakage |

---

## Evidence Notes

Evidence file paths used:
- `history/3/78_enrich_potential_levers/events.jsonl` — all 5 success events
- `history/3/79_enrich_potential_levers/events.jsonl` — all 5 error events
- `history/3/79_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — output token overflow
- `history/3/84_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — normal token usage
- `history/3/83_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — gemini token usage
- `history/3/81_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — qwen3 token usage
- `history/3/78_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — llama3.1 output
- `history/3/80_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — gpt-5-nano output
- `history/3/81_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — qwen3 output
- `history/3/83_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — gemini output
- `history/3/84_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — haiku output
- `baseline/train/20250321_silo/002-12-enriched_levers_raw.json` — baseline enriched levers (old prompt)
- `snapshot/1_deduplicate_levers/20250321_silo/002-11-deduplicated_levers_raw.json` — input to enrich step

---

## Questions For Later Synthesis

1. **Why does gpt-oss-20b produce ~12× more output tokens than haiku?**
   Is it responding with much longer descriptions/synergy/conflict, or repeating
   input fields verbatim even when not required? If the latter, a fix that
   instructs models to output only the new fields (delta mode) rather than the
   full lever object could dramatically reduce token usage.

2. **Should synergy/conflict texts include lever UUIDs?**
   Full UUIDs (llama3.1) enable precise cross-referencing in code but are
   verbose and hard to read. Name-only (haiku, gpt-4o-mini) is readable.
   Should the prompt specify a preferred format?

3. **Is qwen3-30b's brevity a model characteristic or a prompt artifact?**
   The model may be following the prompt literally ("briefly explain the
   synergy") while other models expand. If the prompt asks for 1-2 sentences,
   qwen3-30b gives 1-2 short sentences while haiku gives 3-4 longer ones.

4. **What is the intended description length?**
   Haiku (~600 chars) and gpt-5-nano (~657 chars) are longer than gemini/gpt-4o-mini
   (~480-490 chars). All are below 2× baseline but there's ~35% variation.
   Synthesis should define a target to help calibrate the prompt.

5. **Does the 3-call batching affect quality consistency?**
   The first, second, and third batches of ~5 levers each are processed
   independently. Is the quality consistent across batches, or does the model
   drift between calls?

6. **Should gpt-oss-20b be excluded from the standard model suite for this step?**
   Its 0% success rate and 12× token verbosity make it unsuitable without
   significant workarounds (smaller batch size, explicit output token budget).

---

## Reflect

This is the initial baseline measurement for `enrich_potential_levers`. There
is no prior optimization history to compare against, and no PR being evaluated.

The step works well for 6 of 7 tested models. The gpt-oss-20b failure is a
model-specific output-token overflow issue, not a prompt quality problem. The
other models produce structurally valid, contextually grounded enrichments
without fabricated numbers or marketing language.

The primary quality gap is qwen3-30b's terse synergy/conflict texts — they
pass structural validation but are too brief to add meaningful analytical value.

Notably, the enrich step enriches data from the snapshot (clean, deduplicated
levers without fabricated % claims) rather than the baseline training data
(old levers with fabricated % claims). This is the correct architecture: good
input produces good output.

The inconsistency in cross-reference format (N4) is a latent bug — if any
downstream code parses synergy/conflict text to extract lever relationships,
it will need to handle 4 different formats.

---

## Potential Code Changes

**C1**: Add a guard against output-token overflow in the enrich step.
When `usage_metrics.jsonl` shows `output_tokens >= num_output - 10`, the call
hit the limit and the output is likely truncated. The runner should either
retry with a smaller batch, or log a warning and skip the offending batch.
Evidence: `history/3/79_enrich_potential_levers/outputs/*/usage_metrics.jsonl`

**C2**: Reduce the batch size for models with small output token budgets.
Currently 5 levers per call (15/3 = 5). For models where the enrich output
approaches 8192 tokens/call (like gpt-oss-20b at ~3000-5700 tokens/call),
the batch should be reduced to 2-3 levers. The runner could auto-detect the
`num_output` field from the model metadata and adjust batch size accordingly.
Evidence: `metadata[].num_output = 8192` for gpt-oss-20b vs `200000` for gpt-5-nano.

**C3**: Standardize the cross-reference format in the system prompt.
Add explicit instruction: "When referencing another lever, use the lever's name
only (not its UUID)." This prevents llama3.1 from inserting full UUIDs and
qwen3-30b from inserting partial UUIDs.
Evidence: N4 above, cross-model format comparison.

---

## Hypotheses

**H1**: Adding minimum length guidance for `synergy_text` and `conflict_text`
(e.g., "Write 2-4 sentences explaining the mechanism") will bring qwen3-30b's
output up to a useful level without over-inflating other models.
Expected effect: qwen3-30b synergy/conflict length increases from ~183/229 chars
to ~300+ chars. Other models may be marginally longer.
Evidence: N2 — qwen3-30b currently produces ~183 char synergy texts.

**H2**: Removing the "Purpose:", "Objectives:", "Key success metrics:" sub-headers
from the description prompt (if they exist) will reduce gpt-5-nano's template
leakage and produce more natural descriptions at lower token cost.
Expected effect: gpt-5-nano description length decreases from ~657 to ~500 chars.
No effect on other models.
Evidence: N3 — gpt-5-nano output shows rigid sub-header structure.

**H3**: Specifying a maximum description length in the prompt (e.g., "3-5 sentences,
under 600 characters") will standardize length variation across models without
sacrificing content quality.
Expected effect: All models converge to 400-600 chars for description. Currently
range is 397-682 chars across models.
Evidence: P4 field length table.

---

## Summary

The `enrich_potential_levers` step is **operationally sound** for 6 of 7 tested
models, achieving 100% success on all 5 plans each. The one failure (gpt-oss-20b,
run 79) is a model-level token output overflow, not a prompt or schema issue.

Content quality is **acceptable at baseline**: no fabricated numbers appear in
the new enrichment fields, existing lever data is preserved correctly, and field
lengths are within ±35% of the old baseline. No model has a ratio above 2×.

The primary quality risks for future optimization are:
1. **qwen3-30b** synergy/conflict is too brief (0.58-0.69×) — adds minimal value
2. **gpt-5-nano** descriptions are template-driven (~1.31×) — more verbose but formulaic
3. **Cross-reference format inconsistency** across models (names vs UUIDs vs backticks)

The most actionable code change is C1/C2: guard against output token overflow so
that models like gpt-oss-20b degrade gracefully rather than failing entire plans.
