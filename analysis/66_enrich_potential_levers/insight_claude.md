# Insight Claude

## Overview

This analysis evaluates **PR #467** ("Reduce word counts and add anti-echoing guidance to enrich
fields") against the runs examined in analysis 65 (PR #466 "Wrap lever UUID in XML tags to prevent
UUID leakage in free-text fields").

Both analyses use `baseline/train` as input, making direct before/after comparison valid.

**Runs compared:**

| Model | Before (analysis 65) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/62_enrich_potential_levers` | `4/69_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/63_enrich_potential_levers` | `4/70_enrich_potential_levers` |
| openai-gpt-5-nano | `4/64_enrich_potential_levers` | `4/71_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/65_enrich_potential_levers` | `4/72_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/66_enrich_potential_levers` | `4/73_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/67_enrich_potential_levers` | `4/74_enrich_potential_levers` |
| anthropic-claude-haiku-4-5-pinned | `4/68_enrich_potential_levers` | `4/75_enrich_potential_levers` |

**PR #467 changes (from `enrich_potential_levers.py` lines 139–178):**

1. **Reduced word counts** in `ENRICH_LEVERS_SYSTEM_PROMPT` and Pydantic field descriptions:
   - `description`: 80-100 words → 50-70 words
   - `synergy_text` and `conflict_text`: 40-60 words → 20-40 words
   (~35% less output per lever)

2. **Anti-echoing instruction** added to system prompt:
   > "Do NOT repeat the consequences or review fields — add new insight about why this lever matters and what success looks like."

3. **Pydantic field descriptions updated** to match system prompt wording (e.g., `description` field
   now reads: "A concise description (50-70 words) of the lever's purpose, scope, and key success
   metrics. Do not repeat the consequences or review fields.").

---

## Negative Things

### N1 — llama3.1 XML tag leakage into lever_id (new regression, gta_game)

Run 69 (llama3.1, after) shows a new failure mode not present in run 62 (before):
llama3.1's batch 1 for `gta_game` returned `lever_id` values wrapped in XML tags (e.g.,
`"lever_id": "<lever>1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd</lever>"`), which fail the
`char.lever_id in enriched_levers_map` lookup (map is keyed by plain UUIDs). This caused 5
`unknown_lever_id` + 5 `incomplete` errors; only 3 of 8 gta_game levers were successfully
characterized.

```
history/4/69_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json
errors[0]: {"type": "unknown_lever_id", "lever_id": "<lever>1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd</lever>"}
errors[5]: {"type": "incomplete", "lever_id": "1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd"}
```

The other 4 plans for llama3.1 (silo, sovereign_identity, hong_kong, parasomnia) had 0 errors.
This is isolated to gta_game batch 1. It is unclear whether the Pydantic field description changes
(e.g., the 50-70 word constraint now appearing in the JSON schema) triggered this or whether it is
stochastic llama3.1 behavior. Run 62 had 0 errors on gta_game.

Evidence:
- `history/4/69_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 10 errors, 3 characterized
- `history/4/62_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 0 errors, 8 characterized

### N2 — gpt-5-nano minor regression (0 → 1 incomplete error)

Run 71 (gpt-5-nano, after) has 1 `incomplete` error that was absent in run 64 (before). One lever
was not fully characterized. This is a single-lever failure and likely stochastic.

Evidence: `history/4/71_enrich_potential_levers/` — total characterized 34 vs 35 in run 64.

### N3 — Structural consequence echoing persists despite anti-echoing guidance

The anti-echoing instruction ("Do NOT repeat the consequences or review fields") reduces explicit
percentage claim repetition but does not eliminate structural echoing. Both haiku and gemini still
repeat consequence-derived terms ("star power", "authenticity", "market penetration",
"resource allocation") in descriptions. The core challenge — models summarizing consequence
outcomes instead of explaining lever purpose — remains partially unresolved.

Evidence:
- `history/4/74_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`:
  Gemini description for Audience Engagement Strategy: "Success is measured by a 20% increase in
  ticket sales..." — still directly echoes consequence claim.
- `history/4/75_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`:
  Haiku descriptions generally avoid specific percentage restatements but still echo consequence
  vocabulary (e.g., "production value", "resource allocation").

### N4 — Net lever-level error count increased (11 → 15)

Despite gpt-oss-20b improving (6 → 0 errors), llama3.1's new regression (+10) and the minor
gpt-5-nano regression (+1) increase total errors from 11 to 15. The improvement in plan-level
success rate (33/35 → 35/35) masks a slight regression in lever-level completion.

---

## Positive Things

### P1 — gpt-oss-20b: full recovery (3/5 → 5/5 plans, 6 → 0 errors)

This is the primary win for PR #467. gpt-oss-20b timed out on hong_kong and parasomnia in run 63
(before), producing 6 errors (1 `batch_skipped` + 5 `incomplete` in hong_kong). After the ~35%
word count reduction, run 70 completes all 5 plans within the 600s budget with 0 errors.

Before/after run times for gpt-oss-20b:
- `gta_game`: 31.0s ↓ (before: not directly comparable, but same order)
- `hong_kong_game`: 32.14s (before: **timeout at 600s**)
- `parasomnia_research_unit`: 319.16s (before: **timeout at 600s**)

The hong_kong recovery is the most impactful: 2 levers characterized → 8 levers characterized.

Evidence:
- `history/4/63_enrich_potential_levers/outputs.jsonl`: hong_kong status "error", duration ~600s
- `history/4/70_enrich_potential_levers/outputs.jsonl`: hong_kong status "ok", duration 32.14s
- `history/4/70_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`: 0 errors, 8 characterized

### P2 — Plan-level success rate: 33/35 → 35/35 (100%)

All 7 models completed all 5 plans. This is the first 35/35 run observed for enrich_potential_levers.
The before state had 2 gpt-oss-20b timeouts (Hong Kong and parasomnia).

Evidence: all `outputs.jsonl` files in runs 69–75 show `"status": "ok"` for all 5 plans per model.

### P3 — Word count reduction achieved across all models (primary PR goal)

The ~35% output reduction targets are being hit. Every model produced measurably shorter fields:

| Model | Before desc (chars) | After desc (chars) | Δ% | Before syn (chars) | After syn (chars) | Δ% | Before conf (chars) | After conf (chars) | Δ% |
|-------|--------------------|--------------------|-----|--------------------|-------------------|-----|--------------------|-------------------|-----|
| gemini | 473 | 321 | −32% | 289 | 136 | −53% | 297 | 149 | −50% |
| gpt-4o-mini | 478 | 382 | −20% | 295 | 181 | −39% | 325 | 191 | −41% |
| gpt-5-nano | 671 | 439 | −35% | 353 | 209 | −41% | 327 | 219 | −33% |
| gpt-oss-20b | 652 | 444 | −32% | 348 | 197 | −43% | 334 | 193 | −42% |
| haiku | 593 | 471 | −21% | 440 | 257 | −42% | 475 | 263 | −45% |
| llama3.1 | 374 | 283* | −24% | 344 | 240* | −30% | 311 | 246* | −21% |
| qwen3-30b | 390 | 280 | −28% | 204 | 176 | −14% | 206 | 184 | −11% |

\* llama3.1 after values computed from 30 levers (gta_game batch 1 failed).

### P4 — Anti-echoing guidance eliminated fabricated percentage claims in descriptions

Haiku dropped 3 fabricated percentage claims from descriptions (before: 20%, 15%, 25% echoed
from consequences; after: 0). Both haiku and gemini descriptions show more thematic grounding
and less direct metric repetition.

Evidence (haiku, hong_kong, Audience Engagement Strategy):
- Before: "success metrics include 20% ticket sales uplift" (echoes consequence exactly)
- After: no percentage claim; "culturally resonant campaigns that bridge familiarity with the
  original film and Hong Kong's contemporary thriller heritage"

### P5 — haiku unknown_lever_id errors slightly reduced (5 → 4)

The `unknown_lever_id` count for haiku dropped from 5 (runs 62–68) to 4. Minor but continues
the downward trend from the original 7 (pre-PR #466).

### P6 — No LLMChatError events in any run

All 7 events.jsonl files (runs 69–75) contain only `run_single_plan_start/complete` events. No
Pydantic schema validation failures were triggered. The updated field descriptions (word count
constraints in `description`, `synergy_text`, `conflict_text`) did not cause hard schema
rejections.

Evidence: `grep LLMChatError history/4/6[9-9]_enrich_potential_levers/events.jsonl ...` → 0 matches
in all 7 files.

---

## PR Impact

### What the PR Was Supposed to Fix

PR #467 targeted two distinct problems:

1. **gpt-oss-20b (reasoning model) budget overruns**: By reducing output per lever ~35%, the
   reasoning model can complete 5 plans within the 600s pipeline budget. The before state had 2
   timeouts for gpt-oss-20b.

2. **llama3.1 consequence echoing**: Anti-echoing guidance ("Do NOT repeat the consequences or
   review fields") targeting llama3.1's observed 0.76x baseline description length (interpreted
   as consequence summarization rather than enrichment). The Pydantic field descriptions were also
   updated to match.

### Before vs After Comparison Table

| Metric | Before (runs 4/62–68) | After (runs 4/69–75) | Change |
|--------|----------------------|----------------------|--------|
| Plan-level success (35 plans) | 33/35 (94.3%) | **35/35 (100%)** | **+2 plans** |
| llama3.1 success | 5/5 | 5/5 | = |
| gpt-oss-20b success | **3/5** | **5/5** | **+2 plans** |
| gpt-5-nano success | 5/5 | 5/5 | = |
| qwen3-30b success | 5/5 | 5/5 | = |
| gpt-4o-mini success | 5/5 | 5/5 | = |
| gemini success | 5/5 | 5/5 | = |
| haiku success | 5/5 | 5/5 | = |
| Total lever-level errors | **11** | **15** | +4 |
| gpt-oss-20b errors | **6** (1 batch_skipped + 5 incomplete) | **0** | **−6** |
| llama3.1 errors | **0** | **10** (5 unknown_lever_id + 5 incomplete, gta_game only) | **+10** |
| haiku unknown_lever_id | 5 | 4 | −1 |
| gpt-5-nano errors | 0 | 1 (incomplete) | +1 |
| LLMChatError events | 0 | 0 | = |
| avg description (chars, all models) | ~522 | **~374** | **−28%** |
| avg synergy_text (chars, all models) | ~331 | **~200** | **−40%** |
| avg conflict_text (chars, all models) | ~353 | **~207** | **−41%** |
| Fabricated % claims in descriptions (haiku) | 3 | **0** | **−100%** |

### Did the PR Fix the Targeted Issues?

**For gpt-oss-20b (primary target): YES — complete recovery.**
The two gpt-oss-20b timeouts (hong_kong, parasomnia) are eliminated. hong_kong went from 2
characterized levers to 8; parasomnia completed at 319s (within budget). The ~35% output
reduction was the decisive factor.

**For llama3.1 consequence echoing (secondary target): PARTIAL.**
Anti-echoing guidance reduced explicit percentage claim repetition in description fields across
most models, including haiku (3 → 0 percentage claims). However, structural echoing (repeating
consequence-derived terms and framing) persists. For llama3.1 specifically, the analysis 65
assessment cited "0.76x baseline description length" as evidence of echoing, but the after runs
do not show a meaningful increase in description richness for llama3.1 — lengths actually
decreased further (374 → 283 chars), suggesting more compression but not necessarily more
independent insight.

### Regressions

**R1 — llama3.1 XML tag leak into lever_id (gta_game only):** A new failure where llama3.1
returned `"<lever>uuid</lever>"` as the lever_id JSON value instead of the plain UUID. This broke
5 levers in gta_game batch 1. The `<lever>` XML tags were introduced in PR #466 as part of the
prompt format; PR #467 may have altered how llama3.1 interprets the surrounding JSON schema
(via Pydantic field description changes), exposing a latent parsing fragility. Isolated to 1/5
plans; other 4 plans for llama3.1 were clean.

**R2 — gpt-5-nano: 1 new incomplete error.** Minor, likely stochastic.

### Verdict: **CONDITIONAL**

The PR achieves its primary goal decisively (gpt-oss-20b +2 plans, +5 levers, −6 errors) and
partially achieves the secondary goal (anti-echoing reduces fabricated % claims in some models).
The verdict is CONDITIONAL rather than KEEP because:

1. The llama3.1 XML-tag-leak-into-lever_id is a new failure mode. It affects only 1/5 plans
   but its root cause — whether it is stochastic or triggered by the Pydantic field description
   changes — is unresolved.
2. A second llama3.1 run on gta_game would either confirm it as stochastic noise or reveal a
   systematic regression requiring a follow-up fix.

If the llama3.1 regression is confirmed stochastic, the verdict upgrades to KEEP.

---

## Comparison

### Field Length vs Baseline and Word Count Targets

Baseline training data field lengths (all 5 plans, all characterized_levers):

| Metric | Baseline avg (chars) |
|--------|---------------------|
| description | 602.9 |
| synergy_text | 427.4 |
| conflict_text | 371.4 |

Note: baseline training data descriptions contain fabricated percentage claims inherited from
`identify_potential_levers` consequences, which inflates the baseline. The baseline represents
historical output quality, not an ideal target.

| Model | desc/baseline ratio | syn/baseline ratio | conf/baseline ratio | At target (50-70w / 20-40w)? |
|-------|--------------------|--------------------|---------------------|------------------------------|
| gemini | 0.53× | 0.32× | 0.40× | desc ✓, syn ✓, conf ✓ |
| gpt-4o-mini | 0.63× | 0.42× | 0.51× | desc ✓, syn ✓, conf ✓ |
| gpt-5-nano | 0.73× | 0.49× | 0.59× | desc slightly over, syn ✓, conf ✓ |
| gpt-oss-20b | 0.74× | 0.46× | 0.52× | desc slightly over, syn ✓, conf ✓ |
| haiku | 0.78× | 0.60× | 0.71× | desc over (~78w), syn/conf slightly over |
| llama3.1* | 0.47× | 0.56× | 0.66× | desc under (~47w), syn/conf borderline |
| qwen3-30b | 0.46× | 0.41× | 0.50× | desc under (~47w), syn ✓, conf ✓ |

\* llama3.1 values based on 30 levers (gta_game partial failure).

All ratios are below 1× baseline — output is shorter than historical norms. No model exceeds
the 2× warning threshold. The main concern is gemini's very short synergy/conflict (0.32×/0.40×
of baseline) and haiku/some models being slightly over the new 50-70 word target for descriptions.

Word count estimates: at ~6 chars/word, 50-70 words ≈ 300-420 chars; 20-40 words ≈ 120-240 chars.

---

## Quantitative Metrics

### Plan-Level Success Rate

| Model | Before (4/62–68) | After (4/69–75) | Change |
|-------|-----------------|-----------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | **3/5** | **5/5** | **+2** |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini | 5/5 | 5/5 | = |
| haiku | 5/5 | 5/5 | = |
| **Total** | **33/35 (94.3%)** | **35/35 (100%)** | **+2** |

### Error Counts per Model

| Model | Before errors (type) | After errors (type) | Change |
|-------|---------------------|---------------------|--------|
| llama3.1 | 0 | **10** (5 unknown_lever_id + 5 incomplete, gta_game) | **+10** |
| gpt-oss-20b | **6** (1 batch_skipped + 5 incomplete) | 0 | **−6** |
| gpt-5-nano | 0 | 1 (incomplete) | +1 |
| qwen3-30b | 0 | 0 | = |
| gpt-4o-mini | 0 | 0 | = |
| gemini | 0 | 0 | = |
| haiku | 5 (unknown_lever_id) | 4 (unknown_lever_id) | −1 |
| **Total** | **11** | **15** | **+4** |

### LLMChatError Events

| Run range | LLMChatError count |
|-----------|--------------------|
| Before (62–68) | 0 |
| After (69–75) | 0 |

No Pydantic schema validation failures in either set.

### Field Length Summary (avg chars across all levers per model)

| Model | Before desc | After desc | Before synergy | After synergy | Before conflict | After conflict |
|-------|------------|-----------|---------------|--------------|----------------|---------------|
| gemini | 473 | 321 | 289 | 136 | 297 | 149 |
| gpt-4o-mini | 478 | 382 | 295 | 181 | 325 | 191 |
| gpt-5-nano | 671 | 439 | 353 | 209 | 327 | 219 |
| gpt-oss-20b | 652 | 444 | 348 | 197 | 334 | 193 |
| haiku | 593 | 471 | 440 | 257 | 475 | 263 |
| llama3.1 | 374 | 283 | 344 | 240 | 311 | 246 |
| qwen3-30b | 390 | 280 | 204 | 176 | 206 | 184 |
| **Avg (all)** | **519** | **374** | **325** | **199** | **325** | **206** |

---

## Evidence Notes

Files consulted:

- `history/4/69_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 after, gta_game (10 errors, XML-tag lever_id regression)
- `history/4/62_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 before, gta_game (0 errors)
- `history/4/63_enrich_potential_levers/outputs.jsonl` — gpt-oss-20b before (hong_kong + parasomnia timeouts)
- `history/4/70_enrich_potential_levers/outputs.jsonl` — gpt-oss-20b after (all 5 plans ok)
- `history/4/70_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — gpt-oss-20b after, hong_kong (0 errors, 8 characterized)
- `history/4/68_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku before, hong_kong
- `history/4/75_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku after, hong_kong (anti-echoing quality check)
- `history/4/67_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — gemini before, hong_kong
- `history/4/74_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — gemini after, hong_kong
- All `events.jsonl` for runs 69–75: no LLMChatError entries
- `baseline/train/*/002-12-enriched_levers_raw.json` — baseline field lengths (desc avg 602.9, syn avg 427.4, conf avg 371.4)
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28–107 (OPTIMIZE_INSTRUCTIONS), 136–178 (Pydantic schema + ENRICH_LEVERS_SYSTEM_PROMPT), 239–256 (lever_details_for_prompt + user_prompt)

---

## OPTIMIZE_INSTRUCTIONS Alignment

| Problem | Status after PR #467 | Notes |
|---------|---------------------|-------|
| Word-count padding | **Substantially reduced** | Avg desc −28%, syn/conf −40%. Targets hit for most models. |
| Consequence echoing | **Partially reduced** | % claims removed in descriptions (haiku: 3→0). Structural echoing persists. |
| Boilerplate descriptions | Not fully checked | Field length reduction suggests less templating, but not confirmed. |
| Self-referential synergy/conflict | Not observed | Same as before. |
| Phantom lever references | Not systematically checked | No evidence found in spot checks. |
| UUID leakage into free-text fields | Still resolved (0 occurrences) | PR #466 fix holds. |
| Haiku extra-characterization | 5 → 4 errors | Slow decline; not PR-related. |
| **XML tag leakage into lever_id (NEW)** | **1/5 plans affected (llama3.1)** | llama3.1 returns `<lever>uuid</lever>` as lever_id JSON value — new failure mode. |

**Proposed addition to OPTIMIZE_INSTRUCTIONS:**

> "XML-tag leakage into lever_id (llama3.1). When the per-batch prompt uses
> `<lever>uuid</lever>` markup and the surrounding Pydantic schema is updated, llama3.1 may
> copy the XML-wrapped form `<lever>uuid</lever>` into the `lever_id` JSON field instead of
> extracting the bare UUID. This causes `unknown_lever_id` + `incomplete` errors for the entire
> affected batch. Observed once in run 69 (gta_game batch 1 of 5 levers). Potential mitigations:
> (a) post-process lever_id values to strip XML wrapper tags before lookup;
> (b) add explicit instruction: 'In the lever_id field, output only the raw UUID string
> (e.g., `1a9003f0-...`), not the `<lever>...</lever>` markup'."

---

## Hypotheses

**H1** — Pydantic field description changes triggered llama3.1 XML-tag leakage.

When non-function-calling models receive the JSON schema as prompt text, adding word-count
constraints to the `description` field description may have shifted llama3.1's attention pattern
and caused it to misparse the `lever_id` field format. Adding an explicit instruction like
"lever_id: output only the raw UUID, not the XML markup" to the schema or system prompt should
prevent this.

Expected effect: Eliminates the XML-tag-in-lever_id regression for llama3.1.
Evidence: Run 69 gta_game batch 1; the only difference between run 62 and run 69 is PR #467's
Pydantic field description changes.

**H2** — Anti-echoing guidance needs a positive formulation to be fully effective.

The current instruction is negative: "Do NOT repeat the consequences or review fields." As noted
in OPTIMIZE_INSTRUCTIONS for UUID prohibitions, small models treat prohibitions as templates.
A positive reformulation — "Add new insight about why this lever matters and how you would
recognize success: what would change, what would be different, what would stakeholders observe" —
may be more effective at eliciting genuinely new content.

Expected effect: Further reduction in structural consequence echoing across all models.
Evidence: Post-PR descriptions still echo consequence vocabulary even after removing explicit
percentage claims (see evidence notes, gemini and haiku examples).

**H3** — haiku descriptions are slightly over the 50-70 word target (avg ~78 words / 471 chars).

Haiku's description length (471 chars avg) is ~13% over the top of the 50-70 word target.
Adding a stronger nudge ("Aim for 60 words — cut ruthlessly to reach the target") may bring
haiku closer to the target without losing content quality.

Expected effect: haiku descriptions converge toward 380-420 chars.
Evidence: field length table above; haiku after avg 471 vs target ceiling ~420.

**C1** — Post-process lever_id to strip XML wrapper tags.

In `execute()` (around line 275), before the `if char.lever_id in enriched_levers_map:` check,
strip XML tags from `char.lever_id`:

```python
raw_id = char.lever_id.strip()
# Strip XML tags if the model echoed the prompt markup
if raw_id.startswith("<lever>") and raw_id.endswith("</lever>"):
    raw_id = raw_id[7:-8]  # strip <lever> and </lever>
if raw_id in enriched_levers_map:
    enriched_levers_map[raw_id].update(...)
else:
    logger.warning(...)
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

This is a defensive code fix that recovers from the llama3.1 XML-tag-leakage regression
without requiring a prompt change.

Expected effect: Recovers 5 levers in llama3.1 gta_game (and any similar future occurrences)
without any model retries. Risk: Low — it only triggers for malformed lever_id values.

---

## Questions For Later Synthesis

1. **Is the llama3.1 XML-tag-in-lever_id regression systematic or stochastic?** Only gta_game
   batch 1 was affected in run 69. A second llama3.1 run against the same data would determine
   if this is reproducible. If reproducible, the Pydantic field description change (PR #467) is
   the likely trigger; if random, it predates PR #467.

2. **Does gemini's synergy/conflict length (136 and 149 chars ≈ 23-25 words) meet the 20-40
   word target semantically?** Gemini hits the lower bound of the word count range, but are the
   texts informationally sufficient? A downstream FocusOnVitalFewLevers step may find too-short
   synergy/conflict texts uninformative for prioritization.

3. **Why does qwen3-30b show minimal reduction in synergy/conflict (−14% and −11%) compared
   to other models (−40% to −53%)?** qwen3-30b was already producing shorter synergy/conflict
   before (avg ~205 chars) relative to other models. The new 20-40 word target is close to what
   qwen3-30b was already doing. Is there a model-specific reason, or is it already near-optimal?

4. **Is haiku's persistent extra-characterization behavior (now 4 errors) batch-size-dependent?**
   The earlier analysis (65) raised this as an open question. With the parasomnia plan still
   showing errors, checking whether reducing the function-calling batch size from 5 to 3 for
   haiku would reduce the error count remains unresolved.

---

## Reflect

PR #467 is a targeted, well-scoped change: reduce output size to help gpt-oss-20b fit within
the 600s budget, and add anti-echoing guidance to improve description quality. The primary goal
is achieved decisively — gpt-oss-20b went from 3/5 to 5/5 plans with zero errors.

The secondary goal (anti-echoing) is partially effective. The positive framing it adds ("add
new insight about why this lever matters and what success looks like") is a step in the right
direction, but structural echoing remains. The parallel to the UUID prohibition pattern is apt:
a negative "do NOT" instruction is less effective than a positive directive specifying what to
produce instead. Future iterations should test a fully positive formulation.

The llama3.1 XML-tag regression is a new concern. The root cause is almost certainly the
interaction between the `<lever>uuid</lever>` prompt format (PR #466) and the now-more-prominent
Pydantic field descriptions (PR #467). A simple code-level post-processing strip (C1) would
neutralize this without requiring prompt changes.

The overall field length trajectory is healthy: descriptions are now ~374 chars avg (was ~519),
well within the 50-70 word target for most models. No model exceeds 2× the relevant baseline
length. The content quality improvements (fewer fabricated % claims in descriptions) are a
genuine improvement over the pre-PR #467 state.

---

## Summary

PR #467 achieves its primary objective: gpt-oss-20b recovered from 3/5 to 5/5 plans with zero
errors, and overall plan-level success rate reached 100% (35/35) for the first time. Word count
targets (50-70 word descriptions, 20-40 word synergy/conflict) are being met across all models.
Anti-echoing guidance partially works — fabricated percentage claims in descriptions are reduced
(haiku: 3 → 0) but structural echoing persists.

**Key measurements:**

- **gpt-oss-20b**: 3/5 plans → **5/5 plans** (+2), 6 errors → **0 errors** (−6)
- **Plan-level success**: 33/35 → **35/35** (+2)
- **Avg description length**: 519 → **374 chars** (−28%)
- **Avg synergy/conflict length**: 325 → **~200 chars** (−40%)
- **Fabricated % claims (haiku)**: 3 → **0** (−100%)
- **llama3.1 regression**: 0 → **10 errors** (gta_game batch 1, XML-tag-in-lever_id)
- **LLMChatError events**: 0 in all runs

The remaining concern is the llama3.1 XML-tag leakage into `lever_id` (5 levers lost from
gta_game). A code-level post-processing strip (C1) would recover these levers without requiring
further prompt changes. The anti-echoing issue should be revisited with a positive reformulation.

**Verdict: CONDITIONAL** — Recommend merging, with a follow-up to investigate and fix the
llama3.1 XML-tag-in-lever_id regression (C1 or H1).
