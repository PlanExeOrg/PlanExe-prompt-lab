# Insight Claude

## Scope

Analyzed 7 history runs (2/17 through 2/23) covering the `identify_documents` step,
each run using a different primary model. Plans examined: `20250321_silo`,
`20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`,
`20260311_parasomnia_research_unit` (5 plans × 7 models = 35 plan-runs total).

PR under evaluation: [#342](https://github.com/PlanExeOrg/PlanExe/pull/342) —
"fix: cap DocumentDetails list fields to reduce IdentifyDocumentsTask output size".

Baseline reference: `baseline/train/{plan}/017-*.json` files.

---

## Negative Things

### N1 — max_length constraints cause new validation failures

PR #342 adds `max_length=6` to `documents_to_create` and `documents_to_find`, and
`max_length=3` to their `_part2` variants. These constraints directly triggered
`LLMChatError` failures with Pydantic `too_long` errors in at least 2 of 7 runs:

- **Run 21 (gpt-4o-mini)**, plan `gta_game`:
  `"List should have at most 6 items after validation, not 7 [type=too_long]"`
  (`history/2/21_identify_documents/outputs.jsonl`)

- **Run 23 (haiku-4-5)**, plan `sovereign_identity`:
  `"documents_to_create: List should have at most 6 items after validation, not 12"`
  `"documents_to_find: List should have at most 6 items after validation, not 11"`
  (`history/2/23_identify_documents/events.jsonl`)

This is precisely the pattern warned against in AGENTS.md §"Pydantic hard constraints
vs soft prompt guidance". When haiku returns 12 items (2× the cap) and the schema
rejects the entire response, all tokens spent on that call are wasted and no documents
are produced for that plan.

### N2 — JSON truncation still happens despite the PR

The PR was supposed to prevent JSON truncation timeouts, but truncation failures
continue for multiple models:

- **Run 18 (gpt-oss-20b)**, plan `parasomnia_research_unit`:
  `"EOF while parsing a list at line 88 column 5"`
- **Run 20 (qwen3-30b)**, plan `sovereign_identity`:
  `"control character (\\u0000-\\u001F) found while parsing a string at line 70 column 0"`
- **Run 23 (haiku-4-5)**, plan `silo`:
  `"EOF while parsing a string at line 1 column 41788"`
- **Run 23 (haiku-4-5)**, plan `hong_kong_game`:
  `"EOF while parsing a string at line 1 column 39982"`
- **Run 23 (haiku-4-5)**, plan `parasomnia_research_unit`:
  `"EOF while parsing a string at line 1 column 39366"`

Haiku produces ~40 KB responses because it writes very verbose item descriptions
(500–700 chars each), so capping the list length at 6 items still results in large
outputs. The PR addressed list length but not per-item verbosity.

### N3 — Partial recovery is universal: 2 of 3 pipeline calls always fail

Every successful plan-run shows:
```
"event": "partial_recovery", "calls_succeeded": 1, "expected_calls": 3
```
This is consistent across all 7 models and all 5 plans. The `identify_documents` step
is designed to make 3 LLM calls (likely: initial identification + filter-to-find +
filter-to-create), but only call 1 ever succeeds. As a result, output files
`017-7-filter_documents_to_find_raw.json` and `017-9-filter_documents_to_create_raw.json`
never appear in any runner output — but they do exist in the baseline
(`baseline/train/20250329_gta_game/017-7-filter_documents_to_find_raw.json`,
`017-9-filter_documents_to_create_raw.json`).

The PR does not address this failure. It is unclear whether PR #342 introduced or
pre-dated this issue, but it is present in all 35 plan-runs examined here.

### N4 — Haiku catastrophic failure rate

Run 23 (haiku-4-5) produced usable output for only 1 of 5 plans (gta_game).
The other 4 plans all failed:
- `silo`: JSON truncation at 41,788 chars
- `sovereign_identity`: max_length violations (12 and 11 items)
- `hong_kong_game`: JSON truncation at 39,982 chars
- `parasomnia_research_unit`: JSON truncation at 39,366 chars

Haiku generates approximately 7–10× more text per item than llama3.1, which makes
it particularly sensitive to both truncation and max_length violations.
(`history/2/23_identify_documents/outputs.jsonl`)

### N5 — Duplicate documents in llama3.1 output

Run 17 (llama3.1), plan `hong_kong_game`, `017-5-identified_documents_to_find.json`
contains a duplicate entry:
- Item 4: "Hong Kong Labour Laws and Regulations"
- Item 9: "Hong Kong Labour Laws and Regulations" (identical text)

The filter steps (calls 2 and 3), which are responsible for deduplication, never ran
due to N3. Without those steps, duplicates pass through.
(`history/2/17_identify_documents/outputs/20260310_hong_kong_game/017-5-identified_documents_to_find.json`)

### N6 — Document count gap vs baseline

The PR caps output at max 6+3=9 items per field, but the baseline for
`hong_kong_game` produced 17 items in `documents_to_create` (counted from
`baseline/train/20260310_hong_kong_game/017-6-identified_documents_to_create.json`).
The baseline for `gta_game` had 11 draft documents to create (inferred from
`017-13-1` through `017-13-11` in `baseline/train/20250329_gta_game/`).

Runner outputs cap at 6+3=9 per field. Even if calls 2 and 3 worked, the schema
can only return 9 total — leaving 8 documents that exist in baseline but cannot be
generated. This represents a structural output reduction from the PR.

### N7 — llama3.1 produces very short, generic descriptions

Run 17 (llama3.1) field descriptions average ~80–100 chars, compared to baseline's
~200–350 chars. The descriptions are formulaic ("Document outlining the communication
strategy…") and not grounded in project-specific context.

Example from run 17, hong_kong_game, documents_to_create:
> "High-level document outlining the project's purpose, scope, objectives, and deliverables." (88 chars)

Compare to baseline hong_kong_game for the same document:
> "Formal document authorizing the project, defining its objectives, scope, and stakeholders. Includes high-level budget, timeline, and success criteria. Serves as the foundation for all subsequent planning." (205 chars)

(`history/2/17_identify_documents/outputs/20260310_hong_kong_game/017-6-identified_documents_to_create.json`)

---

## Positive Things

### P1 — Single-call schema succeeds for 5 of 7 models

Models llama3.1, gpt-oss-20b (4/5), gpt-5-nano, qwen3-30b (4/5), gemini-2.0-flash,
and gpt-4o-mini (4/5) all successfully parse the 4-field DocumentDetails schema in
a single LLM call. The _part2 variants being in the same response (not a separate
call) is a reasonable design that avoids an extra round-trip.

### P2 — GPT-5-nano and Gemini produce context-grounded output

Run 19 (gpt-5-nano) and Run 22 (gemini-2.0-flash) generate well-tailored documents.
Example from run 19, hong_kong_game (gemini):
> "High-level framework guiding how the original story will be adapted for a modern
> Hong Kong setting, including twist strategy, tonal direction, core themes, IP
> alignment, and censorship considerations."

This is 200 chars, appropriately specific, and aligned with the project's unique lever
(narrative strategy). Gemini also populates `document_template_primary` and
`document_template_secondary` fields with real template names (e.g., "PMI Project
Charter Template", "Lean Production Plan Template").
(`history/2/19_identify_documents/outputs/20260310_hong_kong_game/017-6-identified_documents_to_create.json`)

### P3 — No schema structural failures for items within bounds

For models that stayed within the max_length=6 cap on their first call (llama3.1,
gpt-5-nano, gemini), the Pydantic schema validated successfully and all required
fields were populated. The schema design itself (4 lists + metadata) is reasonable.

### P4 — System prompt is well-structured

The system prompt (`prompts/identify_documents/prompt_0_4fc4063b7ce3ab8ca163eb4f5fb4ee9aad77b5192cb810b0beae4b3a57049727.txt`)
provides clear, specific instructions with:
- Distinction between "documents to create" (high-level strategies) vs "documents to find" (raw source material)
- Naming convention requirements for "documents to find"
- Explicit anti-pattern guidance ("do NOT include detailed implementation plans")
- Examples of correct vs forbidden items

---

## Comparison

### Baseline vs runner outputs

| Metric | Baseline (hong_kong_game) | Runner best (run 22, gemini) | Runner worst (run 17, llama3.1) |
|--------|--------------------------|-----------------------------|---------------------------------|
| docs_to_create count | 17 | 9 (6+3) | 9 (6+3) |
| docs_to_find count | 8+ (est.) | 6–9 | 9 (incl. 1 dup) |
| filter steps run | Yes (017-7, 017-9) | No (partial_recovery) | No (partial_recovery) |
| draft steps run | Yes (017-11-*, 017-13-*) | No | No |
| avg desc length (create) | ~200–300 chars | ~250 chars | ~90 chars |
| template fields populated | Yes | Yes | No (null) |

The runner outputs are structurally valid but quantitatively reduced vs baseline.
The filtering and drafting phases (calls 2 and 3) represent 66% of the pipeline
that never ran in any of the 35 plan-runs.

### Cross-model document count uniformity

All successful plan-runs produce exactly 6 documents_to_create + 3 documents_to_create_part2 = 9 total documents to create. This is because the cap at 6 enforces uniformity even when projects have different complexity levels. A simple project (gta_game) and a complex one (sovereign_identity with geopolitical constraints) receive the same 9-document cap.

---

## Quantitative Metrics

### Success rate by model

| Model (run ID) | Plans | Succeeded | Failed | Failure Types |
|----------------|-------|-----------|--------|---------------|
| ollama-llama3.1 (17) | 5 | 5 | 0 | — |
| openrouter-gpt-oss-20b (18) | 5 | 4 | 1 | JSON truncation (EOF line 88) |
| openai-gpt-5-nano (19) | 5 | 5 | 0 | — |
| openrouter-qwen3-30b (20) | 5 | 4 | 1 | JSON corruption (ctrl char) |
| openrouter-gpt-4o-mini (21) | 5 | 4 | 1 | max_length violation (7>6) |
| openrouter-gemini-2.0-flash (22) | 5 | 5 | 0 | — |
| anthropic-haiku-4-5 (23) | 5 | 1 | 4 | truncation (3), max_length (1) |
| **Total** | **35** | **28** | **7** | |

Overall: **80.0%** plan-level success; **0.0%** full pipeline success (all 3 calls).

### Failure breakdown

| Failure type | Count | Caused by PR #342? |
|--------------|-------|--------------------|
| max_length violation | 2 | **Yes** — directly caused |
| JSON truncation (EOF) | 4 | No — pre-existing; PR didn't fix |
| JSON corruption (ctrl char) | 1 | No — pre-existing |
| Filter call failures | 35 (all) | Unknown — possibly pre-existing |

### Document count vs baseline

| Plan | Baseline docs_to_create | Runner max (with PR) | Reduction |
|------|------------------------|---------------------|-----------|
| hong_kong_game | 17 | 9 (6+3) | −8 (47%) |
| gta_game | 11 | 9 (6+3) | −2 (18%) |
| (others) | unknown | ≤9 | unknown |

### Description length comparison (docs_to_create)

| Model | Avg description length | Ratio vs baseline (~250 chars) |
|-------|----------------------|-------------------------------|
| Baseline | ~250 chars | 1.0× |
| llama3.1 | ~90 chars | 0.36× |
| gpt-5-nano | ~175 chars | 0.70× |
| gemini-2.0-flash | ~250 chars | 1.0× |
| haiku-4-5 | ~500–700 chars | 2.0–2.8× |

Note: llama3.1 is under-generating (below baseline), haiku is over-generating (above
2× threshold flagged in AGENTS.md). Gemini is closest to baseline quality.

### Template fields populated

| Model | `document_template_primary` | `document_template_secondary` |
|-------|----------------------------|-------------------------------|
| llama3.1 | null (all) | null (all) |
| gpt-5-nano | mostly populated | some populated |
| gemini-2.0-flash | populated | partially populated |
| haiku-4-5 | populated (gta only) | partially |
| Baseline | populated | partially populated |

llama3.1 consistently omits template fields despite the system prompt requiring them.

---

## Evidence Notes

- All failure errors cited from: `history/2/{17-23}_identify_documents/outputs.jsonl`
  and `history/2/{17-23}_identify_documents/events.jsonl`
- Partial recovery events confirmed in: `history/2/17_identify_documents/events.jsonl`
  lines 3, 6, 9, 12, 15 (all showing `calls_succeeded: 1, expected_calls: 3`)
- Baseline document count for hong_kong_game from:
  `baseline/train/20260310_hong_kong_game/017-6-identified_documents_to_create.json`
  (17 items counted, lines 1–273)
- Baseline draft document count for gta_game from: 11 files
  `baseline/train/20250329_gta_game/017-13-{1-11}-draft_documents_to_create_raw.json`
- Haiku description lengths measured from:
  `history/2/23_identify_documents/outputs/20250329_gta_game/017-5-identified_documents_to_find.json`
  ("Comparable AAA Game Development Projects" desc ≈ 680 chars)
- System prompt read from:
  `prompts/identify_documents/prompt_0_4fc4063b7ce3ab8ca163eb4f5fb4ee9aad77b5192cb810b0beae4b3a57049727.txt`

---

## PR Impact

### What the PR was supposed to fix

PR #342 adds `max_length` constraints to `DocumentDetails` Pydantic schema fields:
- `documents_to_create`, `documents_to_find`: max 6 items each
- `documents_to_create_part2`, `documents_to_find_part2`: max 3 items each

Goal: prevent JSON truncation timeouts caused by LLMs generating too many items.
Supersedes PR #333 which had CI timeouts.

### Before vs after comparison

There are no "before PR" history runs in the dataset — all 7 runs (17–23) are
post-PR. A strict before/after comparison is not possible.

Comparison is therefore: **post-PR runs vs baseline** (which predates the PR and
had no max_length constraints).

| Metric | Baseline (pre-PR) | Post-PR runs |
|--------|-------------------|-------------|
| Overall success rate | 100% (full pipeline) | 80% plan-level |
| Full pipeline (3 calls) | Yes | 0% (all partial) |
| docs_to_create (hong_kong) | 17 | 9 max (6+3) |
| JSON truncation failures | Unknown | 4 observed |
| max_length failures | 0 (no cap) | 2 observed |

### Did the PR fix the targeted issue?

**Partially, for some models.** Models that naturally generate ≤6 items (llama3.1,
gemini, gpt-5-nano) do not hit the cap and benefit from a tighter schema that
prevents runaway output. However:

1. The PR introduced **new failures** for models that generate >6 items (gpt-4o-mini,
   haiku). These are "correctness" failures — the model's content is discarded
   entirely rather than trimmed.

2. For haiku specifically, the PR failed to prevent truncation (3 plans still hit
   ~40 KB EOF errors). Haiku generates verbose descriptions (~700 chars/item), so
   6 items × 700 chars = ~4,200 chars per field — still large enough to cause
   truncation. The item count cap alone is insufficient.

3. The `expected_calls: 3` / `calls_succeeded: 1` pattern means the filter and
   refinement steps (calls 2 and 3) never run. This is a larger structural issue
   that the PR does not address.

### Regressions

- 2 failures directly caused by max_length=6 constraints (AGENTS.md warns against this)
- Document count cap reduces output by 47% vs baseline for complex plans (hong_kong_game)
- 0% full pipeline success vs 100% in baseline (though this may be pre-existing)

### Verdict: CONDITIONAL

The PR prevents some over-generation for well-behaved models. But it introduces
`too_long` validation failures for models that generate more items, fails to fix
truncation for haiku, and doesn't address the critical `expected_calls: 3` /
`calls_succeeded: 1` structural issue. The approach (hard schema caps) conflicts
with the AGENTS.md principle established from the `identify_potential_levers` step.

**Recommend**: Keep the PR only if the `max_length` values are raised (e.g., to 12
or 15) to function as safety nets rather than tight constraints, OR revert to soft
prompt guidance and handle overflow downstream.

---

## Questions For Later Synthesis

1. **Why do calls 2 and 3 always fail?** The `expected_calls: 3` pattern is
   consistent across all 7 models and all 5 plans. Was the filter/refinement step
   recently broken? Is this a runner integration bug or a new model behavior issue?
   Can the synthesis agent compare git history of `runner.py` and
   `identify_documents.py` to find the regression?

2. **Haiku max_length: 6 is too low, but what is the right value?** Haiku generates
   12 items naturally (sovereign_identity). A cap of 12 or 15 might be safe while
   still preventing true runaway output. What is the maximum items ever seen in
   a baseline plan?

3. **Was PR #333 (the predecessor) also failing on CI for schema reasons, or only
   network timeouts?** Understanding the root cause of the original CI failures
   would inform whether a schema change is the right lever at all.

4. **Should max_length constraints be removed entirely and replaced with soft prompt
   guidance** ("Provide 4–8 documents…")? The AGENTS.md principle supports this.
   Is there a downstream step that trims extras?

5. **Is there a no-trim path** if the filter steps (calls 2 and 3) fail? Currently
   partial_recovery passes all items through unfiltered. This causes duplicates
   (see N5) and potentially lowers overall quality.

---

## Reflect

The core tension is between two goals:
- **Reliability** (avoid truncation → add hard caps)
- **Completeness** (match baseline document count → remove caps)

The PR chose reliability but used the wrong tool (hard schema cap instead of soft
prompt guidance or downstream trimming). The AGENTS.md experiment insights directly
predicted this failure from the `identify_potential_levers` step.

The more critical finding is N3: all 35 plan-runs execute at 33% pipeline capacity
(1/3 calls). This suggests a structural bug that dwarfs the max_length issue in
terms of impact on output completeness. The synthesis agent should prioritize
investigating and fixing the filter step failures before addressing item counts.

**Content quality** is polarized by model:
- Llama3.1 is below baseline (under-describes, omits template fields)
- Haiku is above baseline but in a negative way (over-describes, causes truncation)
- Gemini-2.0-flash is closest to baseline quality

This suggests the system prompt is well-calibrated for mid-tier API models but
provides insufficient guidance for local models (llama3.1) and too much latitude
for verbose models (haiku).

---

## Potential Code Changes

**C1 (high priority — structural bug)**: Investigate why filter calls (calls 2 and 3)
always fail in `identify_documents.py` or `runner.py`. The `partial_recovery:
calls_succeeded: 1, expected_calls: 3` pattern is universal and pre-dates or
coincides with this PR. The filter steps exist in baseline but never run in runner.
Expected effect: restoring full pipeline would add deduplication, refinement, and
drafting, significantly improving output quality.

**C2 (medium priority — PR regression)**: Raise or remove `max_length` constraints
from `DocumentDetails` Pydantic schema. Replace with soft prompt guidance ("Identify
4 to 8 documents to create"). If hard caps are kept, set them at 12–15 (a safety
net, not a tight constraint). Expected effect: eliminate `too_long` validation
failures for haiku and gpt-4o-mini.

**C3 (medium priority — verbosity)**: Add per-field verbosity guidance to the system
prompt for `description` fields. Specify a target length (e.g., "2–4 sentences,
50–200 words"). This would help haiku avoid truncation without needing item count
caps. Expected effect: reduce haiku response size by ~50–60%, eliminating EOF errors.

**C4 (low priority — dedup)**: If filter calls cannot be restored (C1), add a client-side
deduplication step that merges `documents_to_create + documents_to_create_part2` and
removes exact name matches before writing `017-6-identified_documents_to_create.json`.
Expected effect: eliminate duplicates like the llama3.1 "Hong Kong Labour Laws"
duplicate seen in N5.

---

## Prompt Hypotheses

**H1**: Add a sentence to the system prompt: "Identify 4 to 8 documents to create and
4 to 8 documents to find. Descriptions should be 2–4 sentences." This soft guidance
replaces the hard schema cap and reduces verbosity in both directions (too short for
llama3.1, too long for haiku). Expected effect: tighter length distribution across
models, fewer truncation events.

**H2**: Add an instruction to populate `document_template_primary` for all documents:
"For every document, specify the most appropriate template standard (e.g., 'PMI Project
Charter Template', 'ISO 31000 Risk Framework'). If no standard template exists, use
null." Expected effect: improves llama3.1 template field population from 0% to ~50%
without requiring code changes.

**H3**: Add an explicit "Avoid duplication" instruction to the system prompt:
"Ensure each document name is unique. Do not repeat documents across the primary and
part2 lists." Expected effect: reduces duplicate entries when filter calls fail.

---

## Summary

PR #342 partially addresses JSON truncation by capping list sizes, but:

1. **Introduces new max_length validation failures** for models that naturally generate
   more documents (haiku: 12 items, gpt-4o-mini: 7 items). This violates the
   AGENTS.md principle established in the `identify_potential_levers` step.

2. **Does not fix truncation for haiku** — 3 of 4 haiku failures are still JSON
   truncation (at ~40 KB), not max_length violations. The root cause is per-item
   verbosity, not item count.

3. **Does not address the critical structural issue**: all 35 plan-runs show
   `calls_succeeded: 1, expected_calls: 3`. The filter and refinement steps
   (calls 2 and 3) never execute, leaving the pipeline running at 33% capacity
   compared to baseline.

4. **Reduces document count** from baseline's 17 (hong_kong_game) to a maximum of
   9 per run, a 47% reduction for complex plans.

Overall success rate with PR: **80%** plan-level, **0%** full pipeline.
Recommended verdict: **CONDITIONAL** — raise or remove max_length constraints,
and separately investigate why filter calls always fail.
