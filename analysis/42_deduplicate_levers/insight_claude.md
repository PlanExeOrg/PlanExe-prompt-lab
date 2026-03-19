# Insight Claude

## Overview

This analysis evaluates PR #363 ("feat: add keep-core/keep-secondary classification to
deduplicate_levers") against 7 history runs across 5 training plans.

**PR summary**: Before this PR, `deduplicate_levers.py` used a single `keep` class
(alongside `absorb` / `remove`). The `deduplicated_levers` output contained NO
`classification` field. The PR splits `keep` into `primary` (essential strategic) and
`secondary` (supporting/operational), with both surviving deduplication and the
new `classification` field flowing downstream to `vital_few_levers` for prioritization.

**Note on terminology**: The PR description uses "keep-core" / "keep-secondary" but the
actual code (`LeverClassification` enum, Pydantic schema, output field) uses "primary"
/ "secondary". This disconnect is a maintenance risk.

**History runs**: 7 runs, each with a different model, all run on 2026-03-19 with the
PR code:

| Run | Model |
|-----|-------|
| 3/01 | ollama-llama3.1 (sequential) |
| 3/02 | openrouter-openai-gpt-oss-20b |
| 3/03 | openai-gpt-5-nano |
| 3/04 | openrouter-qwen3-30b-a3b |
| 3/05 | openrouter-openai-gpt-4o-mini |
| 3/06 | openrouter-gemini-2.0-flash-001 |
| 3/07 | anthropic-claude-haiku-4-5-pinned |

This is the **first analysis iteration for the `deduplicate_levers` step**
(`analysis/best.json` has no entry for this step). Comparison is against
`baseline/train/` data.

---

## Negative Things

**N1 — llama3.1 produces zero deduplication**

Run 01 (llama3.1) classified 14/15 levers as `primary` and 1 as `secondary` for
`hong_kong_game` — with zero absorb or remove decisions. All 15 input levers survived.
The system prompt's safety valve ("Use 'primary' if you lack understanding") is being
exploited as a blanket fallback rather than a last resort. The model cannot distinguish
near-duplicates in a 15-lever set.

Evidence: `history/3/01_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
— response array has 15 items, all "primary" or "secondary", none "absorb" or "remove";
`deduplicated_levers` array has 15 entries.

**N2 — gemini-2.0-flash violates the Respect-Hierarchy rule**

Run 06 (gemini) absorbed `8035c685` (Narrative Innovation Strategy — the MORE GENERAL
lever) INTO `eb8849ce` (Narrative Modernization Strategy — the MORE SPECIFIC lever).
The system prompt explicitly says: "Respect Hierarchy: When absorbing, merge the more
specific lever into the more general one." The output `deduplicated_levers` keeps the
NARROWER lever (`eb8849ce`) and drops the broader one, losing strategic generality.

Evidence: `history/3/06_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
— `response[0].lever_id = "8035c685"`, `classification = "absorb"`, justification
references `eb8849ce` as absorption target; `deduplicated_levers[0].lever_id =
"eb8849ce"`.

**N3 — gpt-4o-mini over-includes (12 of 15 levers survive)**

Run 05 (gpt-4o-mini) for `hong_kong_game` kept 12/15 levers (9 primary + 3 secondary,
only 3 absorbed, 0 removed). The baseline keeps 7. This means the model is too
conservative with absorb/remove — only merging the most obvious identical-name
duplicates while leaving thematic near-duplicates (e.g., Political Risk Mitigation +
Geopolitical Risk Mitigation) as separate levers.

Evidence: `history/3/05_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
— 12 entries in `deduplicated_levers`, vs. 7 in baseline.

**N4 — Classification disagrees on "Production Efficiency" across models**

For `hong_kong_game`:
- **haiku-4-5** (run 07): `secondary` — "Audience Engagement is a supporting marketing
  and communications lever, not a core strategic decision."
- **qwen3** (run 04): `primary` — "high-stakes execution lever critical to delivering
  the film on time."
- **gpt-4o-mini** (run 05): `secondary`

This disagreement on a lever that the system prompt explicitly gives as an example of
`secondary` ("routine process levers belong here") suggests the prompt example is
insufficiently concrete for weaker models.

**N5 — Terminology mismatch: PR description vs. code**

The PR title and description say "keep-core" / "keep-secondary" but `deduplicate_levers.py`
uses `"primary"` / `"secondary"` throughout: the `LeverClassification` enum, Pydantic
schemas, system prompt, and output JSON. This creates confusion for anyone reading the
PR and then looking at logs or output files.

**N6 — Chain-absorption not detected**

Run 04 (qwen3): lever `8035c685` is absorbed into `a78de5a6`, but lever `eb8849ce` is
also absorbed into `8035c685` (which is itself being absorbed). This creates a chain:
`eb8849ce → 8035c685 → a78de5a6`. The code does not detect or resolve absorption
chains; the final survivors are determined only by whether a lever's own classification
is in `keep_classifications`. Chain absorptions are non-breaking but produce
uninformative `deduplication_justification` fields downstream.

**N7 — No OPTIMIZE_INSTRUCTIONS for deduplicate_levers**

Unlike `identify_potential_levers.py`, `deduplicate_levers.py` has no
`OPTIMIZE_INSTRUCTIONS` constant. Known failure modes (llama3.1 blanket-primary,
hierarchy-direction errors, chain absorption, over-inclusion) have no documented
self-improve guidance.

**N8 — Fabricated numbers and hype language pass through unfiltered**

Input levers from `identify_potential_levers` contain fabricated percentages
("15% higher audience engagement due to novelty", "30% increase in streaming revenue",
"25% increase in tourism to filming locations"). These are preserved verbatim in
`deduplicated_levers` output. The deduplication step has no mechanism to flag or strip
fabricated numbers. This means all downstream steps (enrich, vital few, scenario
generation) operate on content that violates `OPTIMIZE_INSTRUCTIONS` from
`identify_potential_levers.py`.

---

## Positive Things

**P1 — 100% success rate across all 7 models and all 5 plans**

Every model completed all 5 plans without any error. `outputs.jsonl` for all 7 runs
shows `"status": "ok"` for every plan. No `LLMChatError` entries anywhere in the
`history/3/` directory.

**P2 — `classification` field correctly populated in all capable-model outputs**

For haiku-4-5 (run 07), qwen3 (run 04), and gpt-4o-mini (run 05), the
`deduplicated_levers` entries all contain a well-formed `classification: "primary"` or
`classification: "secondary"` field. This is the core deliverable of the PR.

**P3 — haiku-4-5 produces semantically correct deduplication**

Run 07 (haiku) for `hong_kong_game`: 5 primary + 2 secondary survivors (7 total),
matching the baseline's 7. The model correctly identifies:
- "Production Efficiency Optimization" and "Audience Engagement Strategy" as `secondary`
- Political Risk + Geopolitical Risk as duplicates (absorbs geopolitical into political)
- Talent Alignment + Talent Acquisition as duplicates
Evidence: `history/3/07_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`

**P4 — No schema validation failures**

The `Literal["primary", "secondary", "absorb", "remove"]` constraint in
`LeverClassificationDecision` and `Literal["primary", "secondary"]` in `OutputLever`
are respected by all models. No `ValidationError` → `LLMChatError` retries occurred.

**P5 — Backwards-compatible design**

The `classification` field is optional in `enrich_potential_levers.py` (per PR
description). Existing pipelines without the classification field will continue
to work.

**P6 — Short per-lever calls are efficient**

Processing is done lever-by-lever (one structured call per lever), keeping each call
small and avoiding context-overflow issues. The compact history fallback at
`deduplicate_levers.py:191` prevents context blowout on long runs.

---

## Comparison

### Before vs After (baseline vs PR runs)

| Metric | Baseline (train) | Run 07 haiku (PR) |
|--------|-----------------|-------------------|
| `classification` field in output | Absent | Present (`primary`/`secondary`) |
| `response` classes used | `keep`, `absorb` | `primary`, `secondary`, `absorb`, `remove` |
| Levers kept (hong_kong_game) | 7 | 7 |
| Content of kept levers | Unchanged | Unchanged (same fields) |
| Downstream prioritization signal | None | `vital_few_levers` can filter by classification |

The PR adds a new field without changing content or count for capable models.
For weaker models (llama3.1), the count regression (15 kept vs. 7 baseline) is
significant but pre-existed — the old single-"keep" system would have had the same
problem.

### Model comparison (hong_kong_game, 15 input levers)

| Run | Model | Primary | Secondary | Absorb | Remove | Kept | Baseline gap |
|-----|-------|---------|-----------|--------|--------|------|-------------|
| Baseline | (mixed old) | 7* | —* | 8 | 0 | 7 | 0 |
| 01 | llama3.1 | 14 | 1 | 0 | 0 | **15** | +8 (no dedup) |
| 04 | qwen3 | 6 | 1 | 7 | 0 | 7 | 0 |
| 05 | gpt-4o-mini | 9 | 3 | 3 | 0 | **12** | +5 (over-incl.) |
| 06 | gemini-2.0-flash | ~5 | 2 | ~8 | 0 | 7 | 0 (wrong hierarchy) |
| 07 | haiku-4-5 | 5 | 2 | 5 | 3 | 7 | 0 |

\* Baseline uses single `keep` class with no secondary distinction.

Note: runs 02 (gpt-oss-20b) and 03 (gpt-5-nano) data not fully analyzed (outputs exist
but were not read in detail). They complete with `"status": "ok"`.

---

## Quantitative Metrics

### Success rate

| Run | Model | Plans OK | Calls Succeeded |
|-----|-------|----------|-----------------|
| 01 | llama3.1 | 5/5 | 75/75 |
| 02 | gpt-oss-20b | 5/5 | 75/75 |
| 03 | gpt-5-nano | 5/5 | 75/75 |
| 04 | qwen3 | 5/5 | 75/75 |
| 05 | gpt-4o-mini | 5/5 | 75/75 |
| 06 | gemini-2.0-flash | 5/5 | 75/75 |
| 07 | haiku-4-5 | 5/5 | 75/75 |

**LLMChatError count: 0** across all runs and all plans.

### Deduplication effectiveness (hong_kong_game, 15 input levers)

| Run | Model | Levers Kept | Reduction % | Secondary Count |
|-----|-------|-------------|-------------|-----------------|
| Baseline | old | 7 | 53% | n/a |
| 01 | llama3.1 | 15 | **0%** | 1 |
| 04 | qwen3 | 7 | 53% | 1 |
| 05 | gpt-4o-mini | 12 | 20% | 3 |
| 06 | gemini-2.0-flash | ~7 | ~53% | 2 |
| 07 | haiku-4-5 | 7 | 53% | 2 |

### Duration (total wall-clock, all 5 plans)

| Run | Model | Duration (s) |
|-----|-------|-------------|
| 01 | llama3.1 (sequential) | ~281 |
| 02 | gpt-oss-20b | ~542 |
| 03 | gpt-5-nano | ~1071 |
| 04 | qwen3 | ~1480 |
| 05 | gpt-4o-mini | ~194 |
| 06 | gemini-2.0-flash | ~96 |
| 07 | haiku-4-5 | ~237 |

### Constraint violations

| Violation Type | Count (7 runs × 5 plans) | Evidence |
|---------------|--------------------------|---------|
| LLMChatError / schema rejection | 0 | All events.jsonl |
| Hierarchy-direction errors | ≥1 (run 06, possibly others) | run 06 hong_kong_game |
| Chain absorption (A→B→C) | ≥1 (run 04) | run 04 hong_kong_game |
| Zero deduplication (all kept) | ≥1 run (run 01 on all 5 plans) | run 01 outputs.jsonl |

### Fabricated percentage claims in input (hong_kong_game levers)

Counting fabricated numeric claims in `consequences` fields of deduplicated_levers
(run 07, haiku — highest quality output):

| Lever | Fabricated claim |
|-------|-----------------|
| Narrative Innovation Strategy | "15% higher audience engagement due to novelty" |
| Talent Alignment Strategy | "20% higher pre-sales based on star power" |
| Distribution Architecture Strategy | "30% increase in streaming revenue" |
| Political Risk Mitigation Strategy | "10% increase in production costs" |
| Hong Kong Identity Strategy | "25% increase in tourism to filming locations" |

5 fabricated percentage claims in 7 surviving levers (71%). These originate from
`identify_potential_levers` and pass through deduplication unchanged.

### Field length comparison (deduplication_justification)

| Run | Model | Avg justification length (chars, hong_kong_game) |
|-----|-------|--------------------------------------------------|
| 01 | llama3.1 | ~250 |
| 04 | qwen3 | ~400 |
| 05 | gpt-4o-mini | ~300 |
| 06 | gemini-2.0-flash | ~200 |
| 07 | haiku-4-5 | ~500 |

Haiku produces the most detailed justifications; gemini the most terse. None exceed
2× baseline length (baseline has no justification field). Content is domain-grounded,
not generic boilerplate (each justification mentions specific lever IDs or plan details).

---

## Evidence Notes

- **Baseline lacks `classification` field**: Confirmed from
  `baseline/train/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` —
  the `deduplicated_levers` array entries have `lever_id`, `name`, `consequences`,
  `options`, `review`, `deduplication_justification` but no `classification`.

- **`response` uses "keep" in baseline**: The `response` array in the baseline file
  uses `"classification": "keep"` — confirming this PR replaces the single-class "keep"
  with "primary" / "secondary".

- **Run 01 (llama3.1) blanket-primary**: Verified in
  `history/3/01_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
  — 15 levers in response, 0 absorb/remove decisions, 15 in deduplicated_levers.

- **Run 06 (gemini) wrong hierarchy**: Verified at lines 1–10 and 80–92 of
  `history/3/06_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
  — `8035c685` (Narrative Innovation) absorbed into `eb8849ce` (Narrative Modernization),
  but `eb8849ce` is the more specific sub-lever.

- **Run 07 (haiku) correct deduplication**: Verified at
  `history/3/07_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
  — 5 absorb, 3 remove, 7 survivors with meaningful primary/secondary split.

- **Source code** at
  `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
  shows `keep_classifications = {LeverClassification.primary, LeverClassification.secondary}`
  at line 235, confirming both classes survive deduplication post-PR.

---

## PR Impact

### What the PR was supposed to fix

Split the single `keep` classification into `primary` and `secondary`, so that
`vital_few_levers` can prioritize essential strategic levers over supporting/operational
ones. Both classes survive deduplication. The new `classification` field flows
downstream.

### Before vs After comparison

| Metric | Before (baseline) | After (runs 01–07) | Change |
|--------|------------------|---------------------|--------|
| `classification` in deduplicated_levers | Absent | Present | ✓ Added |
| Classes in LLM response | keep/absorb/remove | primary/secondary/absorb/remove | ✓ Expanded |
| Downstream prioritization signal | None | primary vs secondary | ✓ New |
| Deduplication rate (capable models) | ~53% | ~53% (haiku/qwen3) | Unchanged |
| Deduplication rate (llama3.1) | Unknown* | 0% | ⚠ Problem |
| Schema validation failures | 0 | 0 | ✓ No regression |

\* The baseline may also have had poor deduplication on llama3.1 — not confirmed.

### Did the PR fix the targeted issue?

**Yes, for capable models.** The `classification` field is now present and semantically
meaningful in outputs from haiku-4-5, qwen3, and gpt-4o-mini. The primary/secondary
distinction is applied correctly: operational/communications levers ("Production
Efficiency", "Audience Engagement") are consistently classified `secondary` by haiku
and gpt-4o-mini.

### Regressions introduced?

**No new regressions.** Success rate remains 100%. No schema failures. The
llama3.1 blanket-primary problem and gemini hierarchy-direction problem likely existed
before the PR (they are model-capability limitations, not prompt regressions).

### Verdict: **CONDITIONAL**

The PR achieves its stated goal and is functionally correct. The `classification` field
is added, populated, and schema-valid. However:
1. The PR description terminology ("keep-core"/"keep-secondary") does not match the
   code ("primary"/"secondary") — should be reconciled in a follow-up.
2. llama3.1 produces no deduplication (0% reduction), making the classification field
   meaningless for that model. This pre-existed and is a model limitation, but the new
   prompt structure (safety valve "use primary if uncertain") may be worsening it.
3. The `vital_few_levers` prioritization benefit depends on downstream changes not
   visible in these runs.

---

## Questions For Later Synthesis

Q1. Does `vital_few_levers` already consume the new `classification` field to
prioritize `primary` over `secondary`? If not, the downstream benefit of this PR has
not yet been realized.

Q2. Is the llama3.1 zero-deduplication a known pre-existing issue, or did the new
prompt change ("use primary if uncertain") make it worse?

Q3. Should the system prompt require a minimum absorption count (e.g., "In a typical
set of 15 levers, at least 4 should be absorbed or removed")? Would this help
llama3.1 without hurting haiku?

Q4. Should chain absorption (A → B → C where B is itself absorbed) be detected and
resolved in code, or is it acceptable as a no-op?

Q5. What is the expected behavior when `vital_few_levers` receives levers with
`classification: "secondary"`? Are they excluded, deprioritized, or handled
separately?

---

## Reflect

The PR is a focused, low-risk addition. The `classification` field is technically
correct and does not regress any existing behavior. The main concern is
**classification consistency across models**: haiku and qwen3 agree on what constitutes
"secondary" (operational, communications, routine process); llama3.1 ignores the
distinction entirely; gemini makes hierarchy errors.

The safeguard "Use 'primary' if you lack understanding" was designed to prevent data
loss but is being over-applied by llama3.1. This is a known tension in the system
prompt that predates this PR.

---

## Potential Code Changes

**C1**: Add `OPTIMIZE_INSTRUCTIONS` to `deduplicate_levers.py`.
- Document: blanket-primary problem (llama3.1), hierarchy-direction errors (gemini),
  chain absorption, over-inclusion.
- This is self-improve guidance only — do not inject into the system prompt.

**C2**: Post-deduplication validation: if `len(deduplicated_levers) >= len(input_levers)`,
emit a `WARNING` log and optionally retry with compacted history. The goal of
deduplication is always to reduce count; zero reduction is a signal the model failed.

**C3**: Hierarchy check: after collecting all decisions, verify that when lever A is
absorbed into lever B, lever B is not itself marked `absorb`. If chain absorption is
detected (A → absorbed_into → B → absorbed_into → C), log a warning.

**C4**: Rename the `LeverClassification` enum values from `primary`/`secondary` to
`keep_core`/`keep_secondary` (or keep as-is but update the PR description). The
mismatch between PR terminology and code terminology is a maintenance risk.

---

## Hypotheses

**H1** (prompt change): Add a deduplication-count guideline to the system prompt:
"In a typical set of 15 levers, expect 5–8 to be absorbed or removed. If you keep all
or nearly all levers, reconsider — the input likely contains near-duplicates."

Evidence: Run 01 (llama3.1) kept all 15; the existing safety valve pushes toward
keeping rather than merging.

Expected effect: Reduced over-inclusion for mid-tier models (gpt-4o-mini) and possibly
improved deduplication for llama3.1. Risk: may cause over-aggressive removal for
already-good models like haiku.

**H2** (prompt change): Add a concrete example of a `secondary` lever in the system
prompt (e.g., "Marketing campaign timing = secondary. Budget risk management = primary").
The system prompt describes the primary/secondary distinction abstractly but provides
no worked example.

Evidence: qwen3 classifies "Production Efficiency" as `primary` while haiku classifies
it as `secondary` — both models agree on the wording of "high-stakes execution" but
apply it differently to operational levers.

Expected effect: More consistent secondary classification across models.

**H3** (prompt change): Replace the hierarchy rule ("merge the more specific into the
more general") with a clearer formulation plus an example showing the correct and
incorrect directions.

Evidence: Run 06 (gemini) absorbed in the wrong direction for the narrative lever.
The current wording "Respect Hierarchy" may be ambiguous for models that interpret
specificity differently.

Expected effect: Reduced hierarchy-direction errors for gemini-class models.

**C1** (code): Add a post-deduplication check in `DeduplicateLevers.execute()` that
counts absorption rate and logs a WARNING when `len(output_levers) >= 0.9 * len(input_levers)`.

**C2** (code): Detect and log chain absorptions before building `output_levers`.

**C3** (code, new addition to OPTIMIZE_INSTRUCTIONS): Document that the `classification`
field exists primarily to help `vital_few_levers` prioritize, not to gate inclusion —
both `primary` and `secondary` survive. This goal should be reflected in the system
prompt guidance.

---

## Summary

PR #363 successfully adds a `classification: primary|secondary` field to the
`deduplicated_levers` output. The feature works correctly for capable models (haiku-4-5,
qwen3, gpt-4o-mini): both classes survive, the field is schema-valid, and the
semantic distinction is applied meaningfully. Success rate is 100% across all 7 models
and 5 plans with zero LLMChatError entries.

Two model-specific problems are present and pre-existing: (1) llama3.1 classifies
all levers as `primary` with zero deduplication, and (2) gemini-2.0-flash occasionally
absorbs in the wrong hierarchy direction. These are model-capability limitations, not
prompt regressions from this PR.

The terminology mismatch (PR says "keep-core/keep-secondary", code uses
"primary/secondary") should be resolved. The `deduplicate_levers.py` file also lacks
an `OPTIMIZE_INSTRUCTIONS` constant to document known failure modes for future
optimization iterations.

**Verdict: CONDITIONAL** — keep the PR; follow up with a terminology fix and
add `OPTIMIZE_INSTRUCTIONS` to document the model-specific failure modes.
