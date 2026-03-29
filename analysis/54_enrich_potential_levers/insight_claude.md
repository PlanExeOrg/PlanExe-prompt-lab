# Insight Claude

## Overview

This analysis evaluates **PR #451** ("Include consequences and review in enrich batch
prompt") against the baseline established in analysis 53. The PR adds `consequences`
and `review` to the per-lever details in the batch prompt, so the LLM has access to
the documented effects and trade-offs when generating `description`, `synergy_text`,
and `conflict_text`.

**Input**: `snapshot/1_deduplicate_levers` (same as analysis 53 — valid for comparison)

**Runs compared**:

| Before (analysis 53) | After (analysis 54) | Model |
|----------------------|---------------------|-------|
| `3/78_enrich_potential_levers` | `3/85_enrich_potential_levers` | ollama-llama3.1 |
| `3/79_enrich_potential_levers` | `3/86_enrich_potential_levers` | openrouter-gpt-oss-20b |
| `3/80_enrich_potential_levers` | `3/87_enrich_potential_levers` | openai-gpt-5-nano |
| `3/81_enrich_potential_levers` | `3/88_enrich_potential_levers` | openrouter-qwen3-30b-a3b |
| `3/82_enrich_potential_levers` | `3/89_enrich_potential_levers` | openrouter-gpt-4o-mini |
| `3/83_enrich_potential_levers` | `3/90_enrich_potential_levers` | openrouter-gemini-2.0-flash |
| `3/84_enrich_potential_levers` | `3/91_enrich_potential_levers` | anthropic-claude-haiku-4-5-pinned |

**Code verified**: `enrich_potential_levers.py` lines 171-178 confirm the PR change:
`Consequences: {lever.consequences}` and `Review: {lever.review}` were added to
`lever_details_for_prompt`. The `full_lever_context_str` at line 156 is unchanged
(still emits full UUIDs).

---

## Negative Things

### N1 — gpt-oss-20b still fails 0/5 plans (unchanged from before)

Run 86 (gpt-oss-20b) fails all 5 plans identically to run 79. The PR does not address
B1 (no per-batch retry) or B2 (output token overflow for verbosity-heavy models). This
was the deferred D1 item from analysis 53.

### N2 — llama3.1 description length dropped below baseline

After the PR, llama3.1's average description length fell from ~386 chars (0.80× baseline)
to ~316 chars (0.65× baseline). The after descriptions now compress the lever's
consequences into a 1-2 sentence summary rather than elaborating:

Before (run 78, silo, Information Control Protocols — 459 chars):
> "Information Control Protocols aim to manage the flow of information within the silo,
> balancing access with security and control. This lever controls what citizens know
> about the outside world, their own roles, and the silo's operations. Objectives include
> maintaining order, suppressing dissent, and fostering a sense of earned privilege
> among loyal citizens. Key success metrics include low levels of unrest, high
> productivity, and minimal information leaks."

After (run 85, silo, Information Control Protocols — 223 chars):
> "Information Control Protocols manage the flow of information within the silo,
> balancing stability and adaptability. This lever controls access to external
> knowledge, internal dissent, and potential threats or opportunities."

The after version echoes `consequences` phrasing directly but omits the elaboration on
objectives and success metrics. At 0.65× baseline, llama3.1 descriptions are now below
the acceptable range — they pass structural validation but provide less decision-relevant
content than before.

Evidence: `history/3/78_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
vs `history/3/85_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`

### N3 — qwen3-30b: CJK character leak in after run

Run 88 (qwen3-30b) contains one instance of Chinese characters in an English-language
plan output. The silo plan, External Engagement Policy conflict_text reads:

> "Clashes with Information Control Protocols by challenging information**封锁** and
> conflicts with Security System Governance by increasing vulnerability to external
> threats."

"封锁" means "blockade/lockdown" in Chinese. This did not occur in the corresponding
before run (run 81). The additional `consequences` and `review` context may be altering
the token probability distribution enough to trigger code-switching in qwen3-30b on
edge cases.

This is a single occurrence, not a systematic regression, but it illustrates that adding
more context can introduce new failure modes in multilingual models.

Evidence: `history/3/88_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
lever "External Engagement Policy" conflict_text (lever index 2).

### N4 — qwen3-30b UUID format regression: now inconsistent within same run

Before (run 81), qwen3-30b consistently used truncated 8-char UUIDs like `(f93eac77)`.
After (run 88), the format is inconsistent:

- silo plan: name-only references (e.g., `Community Governance Model`)
- sovereign_identity plan: full UUIDs (e.g., `(ed16c55c-fd66-41a1-b5e8-b22eccadbaaf)`)

The underlying B2 bug (`full_lever_context_str` still uses full UUIDs at line 156 of
`enrich_potential_levers.py`) was not addressed by this PR. The inconsistency suggests
the additional context changes how qwen3-30b interprets the format signal from the
context string, but without any determinism.

### N5 — Input token cost increased ~18-20% across all models

Adding `consequences` (~1-2 sentences) and `review` (~1 sentence) per lever in the
batch prompt increases input tokens consistently. Verified across all working models:

| Model | Before avg input tokens/call | After avg input tokens/call | Increase |
|-------|-------------------------------|------------------------------|----------|
| haiku | 2535 | 3001 | +18.4% |
| gpt-4o-mini | 1057 | 1255 | +18.7% |
| gemini-flash | 1187 | 1392 | +17.3% |
| gpt-5-nano | 1009 | 1206 | +19.6% |

This is a permanent cost increase per plan execution, not a regression but a
necessary trade-off. The synthesis predicted "~300-500 tokens per batch" — confirmed.

---

## Positive Things

### P1 — gpt-5-nano template artifact eliminated (fixes N3 from analysis 53)

The most significant quality improvement: gpt-5-nano's "Purpose: / Objectives: / Key
success metrics:" sub-header template is gone after the PR. Descriptions are now
natural prose.

Before (run 80, silo, Information Control Protocols):
> "Purpose: Manage information flow within the silo to maintain order, deter rumors,
> and protect sensitive data while supporting productive work. It controls who can
> access different information tiers, how content is curated, and how external
> information is admitted. Objectives: ..."

After (run 87, silo, Information Control Protocols):
> "Information Control Protocols govern what residents can know and when, shaping
> the flow of data, ideas, and warnings inside the silo. The lever establishes access
> tiers, audit trails, and dissemination filters to minimize panic while preserving
> operational continuity..."

The conflict_text also improved: after version says "heavy filtering risks blind spots
and biases, constraining innovation and preparedness for unforeseen crises" — this
directly echoes the `consequences` field ("This can lead to stagnation and a lack of
preparedness for unforeseen crises").

Evidence: `history/3/80_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
vs `history/3/87_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`

### P2 — Conflict texts now grounded in documented trade-offs

Several models show conflict_text that references the lever's actual `review` language
after the PR.

For gpt-5-nano, Resource Allocation Strategy:
- `review`: "...these options overlook the potential for corruption or inequitable access
  to resources."
- After conflict_text: "rigid or biased allocation can create inequities and stifle
  experimentation, provoking discontent among under-resourced groups. It risks clashing
  with Information Control Protocols **when misreported inventories are used to justify
  favoritism**"

The phrase "inequitable access" is directly echoed as "inequities and stifle
experimentation" and "favoritism." The before conflict_text contained no such specificity.

### P3 — Descriptions reference lever-specific consequences

After the PR, descriptions for multiple models now use language drawn from the
`consequences` field rather than generic lever descriptions.

Example — llama3.1, Resource Allocation Strategy:
- `consequences` input: "Prioritizing essential services like agriculture and water
  recycling ensures basic survival..."
- After description (run 85): "Resource Allocation Strategy **prioritizes essential
  services like agriculture and water recycling**, balancing immediate needs with
  long-term diversification."

The before description (run 78) said: "Resource Allocation Strategy aims to manage
resources within the silo, balancing distribution with economic growth and
diversification..." — no reference to the actual consequences language.

### P4 — No fabricated percentage claims (consistent with before)

All after runs maintain zero fabricated % claims in the enriched fields. No regression
on this critical content quality metric.

### P5 — No LLMChatError entries in any run (consistent with before)

Events.jsonl shows no LLMChatError events for any of the 7 after runs. Schema
validation is functioning correctly.

### P6 — Output token reduction for gpt-5-nano

The template elimination has a measurable token efficiency benefit: gpt-5-nano output
tokens dropped from 5526 to 5239 (–5.2%) despite similar description lengths. The
natural prose descriptions are more compact than the sub-header format, reducing cost
while improving quality.

---

## Comparison

### Comparison vs Baseline Training Data

Baseline statistics (35 levers, 5 plans, gemini-old-prompt):
- description: 484 chars avg
- synergy_text: 286 chars avg
- conflict_text: 298 chars avg

All after-PR models are within acceptable length bounds except llama3.1 which is now
below baseline (0.65×). haiku's synergy/conflict remain notably above baseline (1.59×
and 1.64×) but this is not new behavior.

### Comparison vs Prior Runs (before PR)

**The most notable cross-model change**: gpt-5-nano changed from template-driven to
natural prose. All other models show minor length changes (±10%) with subtly different
content grounding but no dramatic shifts except llama3.1's description shrinkage.

### Model Ranking (quality + reliability, after PR)

1. **haiku-4-5** — Balanced descriptions, informed synergy/conflict, 100% success.
   Content unchanged from before; no regression, solid baseline for the step.
2. **gpt-5-nano** — Template artifact eliminated; descriptions now grounded in
   consequences. 100% success. Best improved model in this PR.
3. **gpt-4o-mini** — Compact, clean, unchanged from before. 100% success.
4. **gemini-flash** — Slightly shorter post-PR. 100% success.
5. **llama3.1** — Descriptions now below baseline length (N2). Synergy/conflict
   stable. 100% success.
6. **qwen3-30b** — Still terse synergy/conflict (0.74–0.76× baseline). CJK leak
   in one output (N3). UUID format inconsistency (N4). 100% success.
7. **gpt-oss-20b** — 0% success, unchanged (N1).

---

## Quantitative Metrics

### Success Rate

| Run pair | Model | Before | After | Change |
|----------|-------|--------|-------|--------|
| 78→85 | llama3.1 | 5/5 | 5/5 | same |
| 79→86 | gpt-oss-20b | 0/5 | 0/5 | same |
| 80→87 | gpt-5-nano | 5/5 | 5/5 | same |
| 81→88 | qwen3-30b | 5/5 | 5/5 | same |
| 82→89 | gpt-4o-mini | 5/5 | 5/5 | same |
| 83→90 | gemini-flash | 5/5 | 5/5 | same |
| 84→91 | haiku | 5/5 | 5/5 | same |
| **Total** | | **31/35 (88.6%)** | **31/35 (88.6%)** | **same** |

### Field Lengths vs Baseline (484 desc, 286 syn, 298 conf chars)

| Model | Desc B | Desc A | Ratio B→A | Syn B | Syn A | Ratio B→A | Conf B | Conf A | Ratio B→A |
|-------|--------|--------|-----------|-------|-------|-----------|--------|--------|-----------|
| haiku | 578 (1.19×) | 568 (1.17×) | –1.7% | 452 (1.58×) | 454 (1.59×) | +0.4% | 485 (1.63×) | 488 (1.64×) | +0.6% |
| gpt-5-nano | 663 (1.37×) | 658 (1.36×) | –0.8% | 343 (1.20×) | 332 (1.16×) | –3.2% | 343 (1.15×) | 337 (1.13×) | –1.7% |
| gemini | 481 (0.99×) | 456 (0.94×) | –5.2% | 290 (1.02×) | 275 (0.96×) | –5.2% | 308 (1.03×) | 296 (0.99×) | –3.9% |
| gpt-4o-mini | 512 (1.06×) | 482 (1.00×) | –5.9% | 269 (0.94×) | 279 (0.98×) | +3.7% | 286 (0.96×) | 306 (1.03×) | +7.0% |
| qwen3-30b | 382 (0.79×) | 372 (0.77×) | –2.6% | 198 (0.69×) | 213 (0.74×) | +7.6% | 219 (0.74×) | 226 (0.76×) | +3.2% |
| llama3.1 | 386 (0.80×) | 316 (0.65×) | –18.1% | 374 (1.31×) | 372 (1.30×) | –0.5% | 383 (1.28×) | 394 (1.32×) | +2.9% |

**Notable**: Length alone does not capture the gpt-5-nano quality improvement (template
→ natural prose), which appears at nearly identical length. The llama3.1 drop (–18.1%
description) is the only length regression.

### Input Token Increase

| Model | Before avg in/call | After avg in/call | Increase |
|-------|-------------------|-------------------|----------|
| haiku (silo) | 2535 | 3001 | +18.4% |
| gpt-4o-mini (silo) | 1057 | 1255 | +18.7% |
| gemini (silo) | 1187 | 1392 | +17.3% |
| gpt-5-nano (silo) | 1009 | 1206 | +19.6% |

The ~18-20% increase is consistent across models and plans, confirming this is a
deterministic effect of adding `consequences` (~1-2 sentences) and `review` (~1
sentence) per lever.

### Template Leakage

| Model | Before | After |
|-------|--------|-------|
| gpt-5-nano | "Purpose: / Objectives: / Key success metrics:" sub-headers in descriptions | **None** — natural prose |
| gpt-4o-mini | Name-only references | Name-only references (unchanged) |
| haiku | Name-only references | Name-only references (unchanged) |
| qwen3-30b | Truncated UUIDs `(8chars)` | Inconsistent: name-only (silo) OR full UUIDs (sovereign_identity) |
| llama3.1 | Full UUIDs | Full UUIDs (unchanged) |

### Constraint Violations

| Violation Type | Before (78-84) | After (85-91) |
|----------------|----------------|---------------|
| Missing description | 0 | 0 |
| Missing synergy_text | 0 | 0 |
| Missing conflict_text | 0 | 0 |
| Output truncated (plan fails) | 5 (run 79) | 5 (run 86) |
| Fabricated % claims | 0 | 0 |
| CJK character mix-in | 0 | 1 (run 88, qwen3-30b, silo plan) |

---

## PR Impact

### What the PR Was Supposed to Fix

From the PR description:
> "The enrich step's batch prompt only provided `lever_id`, `name`, and `options` to
> the LLM, but omitted `consequences` and `review` — the two fields that document the
> lever's effects and primary trade-off. This forced the model to infer descriptions
> and conflict analysis from the name alone, producing vague or ungrounded enrichment."

### Code Verification

Confirmed in `enrich_potential_levers.py:171-178` (current state):

```python
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"     # ← added by PR
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}"                   # ← added by PR
    for lever in batch
])
```

The fix is exactly as specified in synthesis direction 1 (`enrich_potential_levers.py:171-173`).

### Before vs After Comparison Table

| Metric | Before (runs 78-84) | After (runs 85-91) | Change |
|--------|---------------------|---------------------|--------|
| Overall success rate | 31/35 (88.6%) | 31/35 (88.6%) | none |
| gpt-oss-20b success | 0/5 | 0/5 | none |
| Avg description length | 506 chars | 477 chars | –5.8% |
| Avg synergy_text length | 324 chars | 323 chars | –0.3% |
| Avg conflict_text length | 339 chars | 343 chars | +1.2% |
| Input tokens/call (haiku) | 2535 | 3001 | +18.4% |
| gpt-5-nano template artifact | Present (all 5 plans) | **Absent** (all 5 plans) | **Fixed** |
| Consequence language in descriptions | Rare | Frequent | **Improved** |
| Review echoed in conflict_text | Rare | Frequent | **Improved** |
| Fabricated % claims | 0 | 0 | none |
| CJK chars in output | 0 | 1 (qwen3-30b) | Minor regression |
| llama3.1 description length | 386 chars (0.80×) | 316 chars (0.65×) | Below baseline |

### Did the PR Fix the Targeted Issue?

**Yes, for gpt-5-nano**: The template-driven format (N3 from analysis 53) was
eliminated. Descriptions now use natural prose and conflict texts now echo
`consequences` language. This is the clearest evidence that the PR works as intended.

**Yes, qualitatively for other models**: Descriptions in gpt-4o-mini and gemini now
reference lever-specific consequence language more frequently than before, though the
length change is modest.

**Partially for llama3.1**: Descriptions reference consequences language but are now
too brief (0.65× baseline). The model is summarizing the consequences rather than
elaborating on them.

**No change for haiku**: Already producing grounded output before the PR. No regression.

### Regressions

1. **llama3.1 description brevity** (N2): 0.65× baseline is below the acceptable range.
   Not a blocking issue since the content is more grounded, but a monitoring concern.
2. **qwen3-30b CJK leak** (N3): Single occurrence, one plan, one lever. Not systematic.
3. **qwen3-30b UUID format inconsistency** (N4): The model's format is now less
   predictable than before. B2 remains unaddressed.
4. **Input token cost** (N5): Permanent ~18-20% increase in input tokens per call.
   Expected and acceptable trade-off.

### Verdict: **KEEP**

The PR produced a measurable, significant improvement for gpt-5-nano (template artifact
eliminated, conflict text grounded in consequences) and qualitative grounding improvements
across most other working models. The ~18-20% input token increase is the expected and
predicted cost. The single CJK character leak (qwen3-30b, silo plan) and llama3.1
description brevity are minor concerns that do not outweigh the gains. No structural
failures were introduced.

---

## Evidence Notes

Files consulted:

- `history/3/78–84_enrich_potential_levers/` — before runs (analysis 53 baseline)
- `history/3/85–91_enrich_potential_levers/` — after runs (this analysis)
- `history/3/{78,85}_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — llama3.1 before/after
- `history/3/{80,87}_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — gpt-5-nano before/after
- `history/3/{82,89}_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-4o-mini gta_game
- `history/3/{83,90}_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — gemini sovereign_identity
- `history/3/{84,91}_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku hong_kong_game
- `history/3/{81,88}_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — qwen3-30b silo
- `history/3/{84,91}_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — haiku token counts
- `history/3/{80,87}_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — gpt-5-nano token counts
- `snapshot/1_deduplicate_levers/20250321_silo/002-10-potential_levers.json` — input consequences/review
- `baseline/train/*/002-12-enriched_levers_raw.json` — baseline field lengths
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 27-81, 156, 171-188 — OPTIMIZE_INSTRUCTIONS and prompt code
- `analysis/53_enrich_potential_levers/synthesis.md` — prior synthesis and predictions

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (lines 27-81 in `enrich_potential_levers.py`) lists
these known problems: boilerplate descriptions, self-referential synergy/conflict,
phantom lever references, symmetric parroting, word-count padding, missing conflict_text,
batch boundary blindness.

**Alignment check for current after runs**:

| Problem | Observed? | Notes |
|---------|-----------|-------|
| Boilerplate descriptions | Reduced (gpt-5-nano template eliminated) | Before: major for gpt-5-nano. After: resolved. |
| Self-referential synergy/conflict | Not observed | N/A |
| Phantom lever references | Not checked systematically | Spot checks show valid lever names |
| Symmetric parroting | Not checked systematically | No flagrant examples seen in spot checks |
| Word-count padding | Reduced for gpt-5-nano | "It is important to note that..." not seen in after runs |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not tested | Would require cross-batch reference audit |

**New problem not yet in OPTIMIZE_INSTRUCTIONS**:
- **Consequence echoing without elaboration**: When `consequences` and `review` are
  provided, weak models (llama3.1) may simply rephrase the consequences as the
  description rather than elaborating on purpose, scope, and success metrics. The
  OPTIMIZE_INSTRUCTIONS "boilerplate descriptions" entry should be updated to include
  this specific failure mode: "Models may summarize the lever's `consequences` text
  verbatim rather than using it as grounding for a richer description."

---

## Questions For Later Synthesis

1. **Is llama3.1's 0.65× description length a prompt issue or a model capacity issue?**
   llama3.1 is the weakest model and may struggle to generate more than a 1-2 sentence
   description when given more context. Adding an explicit minimum length guidance
   (e.g., "at least 3 sentences") might help.

2. **Should qwen3-30b be tested with this PR on non-English plans?**
   The CJK character leak in qwen3-30b for an English plan (silo) is a warning sign.
   On non-English plans, qwen3-30b may produce mixed-language output more frequently
   when given richer context from `consequences` and `review`.

3. **Is the UUID format inconsistency in qwen3-30b after the PR a new problem?**
   Before the PR, qwen3-30b consistently used truncated 8-char UUIDs. After, it uses
   name-only in some plans and full UUIDs in others. This may indicate the model is
   more sensitive to prompt length in how it chooses reference format. B2 (fix
   `full_lever_context_str` to name-only) becomes more important.

4. **What is the next priority: B1 (retry), B2 (UUID format), or D3 (mechanism guidance)?**
   The synthesis from analysis 53 deferred B1 (retry), B2 (UUID format), and D3
   (qualitative mechanism guidance). Post-PR, D3 is now the highest remaining content
   quality gap: qwen3-30b synergy/conflict is still terse (0.74-0.76× baseline) and
   the "(40-60 words)" quantitative target was not addressed by this PR.

5. **Does the gemini-flash description quality improve on a qualitative level?**
   Gemini lengths decreased slightly (0.99→0.94×). Spot checks show minor
   phrasing differences but no dramatic change. A deeper qualitative audit would
   clarify whether the shorter descriptions are more grounded or just more terse.

---

## Reflect

The PR delivered on its stated goal: `description` and `conflict_text` fields are now
more grounded in each lever's documented consequences and trade-off analysis. The most
visible proof is gpt-5-nano — its template-driven format disappeared entirely, which was
a known quality problem identified in analysis 53 (N3). This was an unexpected bonus:
the synthesis expected grounding improvements, but the template elimination (which
required removing the context-free "Purpose: / Objectives: / Key success metrics:"
pattern) was not explicitly predicted.

The ~18-20% input token increase is the confirmed cost. At current model pricing, this
is a meaningful but acceptable trade-off for grounding improvements across all models.

Remaining open issues from analysis 53 synthesis (not addressed by this PR):
- B1: no per-batch retry (gpt-oss-20b still fails)
- B2: UUID format in `full_lever_context_str` (inconsistency worsened for qwen3-30b)
- D3: qualitative mechanism guidance for synergy/conflict (qwen3-30b still terse)

---

## Potential Code Changes

**C1 (deferred B1)** — Add per-batch retry with reduced batch size on failure.
Not addressed by this PR. gpt-oss-20b (run 86) still fails 5/5. The fix adds resilience
for all models against transient token overflow.
Evidence: `history/3/86_enrich_potential_levers/outputs.jsonl` — all 5 plans failed.

**C2 (deferred B2)** — Fix `full_lever_context_str` to use names only.
`enrich_potential_levers.py:156` still reads:
`f"- {lever.lever_id}: {lever.name}"`. After this PR, qwen3-30b's UUID format is now
inconsistent across plans (name-only vs full UUID). Fixing B2 would normalize this.
Evidence: `history/3/88_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
(name-only) vs `history/3/88_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`
(full UUIDs).

**H1** — Add minimum length guidance or explicit elaboration instruction for descriptions.
For llama3.1 (and potentially other weak models), the description is now too brief
(0.65× baseline). The current field description says "(80-100 words)" which for llama3.1
maps to approximately 400-500 chars, but after the PR it's producing ~220-230 chars.
Adding "explain the lever's purpose and effects in at least 3 sentences, using the
consequences as context but adding more detail" might prevent consequence-summarizing.
Expected effect: llama3.1 description length returns to 0.75-0.85× baseline.

**H2** — Add explicit instruction against consequence echoing.
OPTIMIZE_INSTRUCTIONS should document the new failure mode observed in N2: weak models
summarizing `consequences` verbatim rather than elaborating. This is distinct from
"boilerplate descriptions" and warrants its own entry.

---

## Summary

PR #451 ("Include consequences and review in enrich batch prompt") produced a
**significant, measurable improvement** in the quality of enriched lever descriptions
and conflict texts. The primary evidence is gpt-5-nano's complete elimination of the
template-driven sub-header format (N3 from analysis 53) and the grounding of conflict
texts in lever-specific trade-off language across multiple models.

The cost is a confirmed ~18-20% input token increase per plan execution, which is the
expected and acceptable price for grounding all models in each lever's documented effects.

Minor regressions:
- llama3.1 descriptions are now too brief (0.65× baseline): weak models summarize
  consequences rather than elaborating on them.
- qwen3-30b: one CJK character leak in the silo plan, and UUID format is now
  inconsistent across plans.

Three deferred items from analysis 53 remain: B1 (retry logic), B2 (UUID format fix),
and D3 (qualitative mechanism guidance). D3 is now the highest remaining content
quality gap since qwen3-30b's terseness (0.74-0.76× baseline for synergy/conflict)
is still present.

**Verdict: KEEP.**
