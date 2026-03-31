# Insight Claude

## Overview

This analysis evaluates **PR #469** ("Reduce word counts, add anti-echoing, and use verbatim
id guidance") against the best-prior analysis baseline: analysis 65 (PR #466,
"Wrap lever UUID in XML tags to prevent UUID leakage in free-text fields").

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared:**

| Model | Before (runs 62–68, PR #466) | After (runs 83–89, PR #469) |
|-------|------------------------------|------------------------------|
| ollama-llama3.1 | `4/62_enrich_potential_levers` | `4/83_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/63_enrich_potential_levers` | `4/84_enrich_potential_levers` |
| openai-gpt-5-nano | `4/64_enrich_potential_levers` | `4/85_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/65_enrich_potential_levers` | `4/86_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/66_enrich_potential_levers` | `4/87_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/67_enrich_potential_levers` | `4/88_enrich_potential_levers` |
| anthropic-claude-haiku-4-5-pinned | `4/68_enrich_potential_levers` | `4/89_enrich_potential_levers` |

**PR #469 changes (from description):**

1. **Reduced word counts**: `description` 80–100 → 50–70 words; `synergy_text`/`conflict_text`
   40–60 → 20–40 words.
2. **Anti-echoing** (positive framing): "Add new insight beyond what consequences and review
   already state."
3. **Verbatim id guidance**: Field description now says "copy it verbatim from the prompt, without
   XML tags." System prompt says "copy the id verbatim from inside the tags — strip the XML tags
   but do not alter the id itself." Avoids "hexadecimal" (caused gpt-4o-mini to strip hyphens in
   #468) and avoids "uuid" (models interpret differently). Supersedes #467 and #468.

---

## Negative Things

### N1 — haiku introduced a new `dummy_override` error type (run 89, gta_game)

Run 89 (haiku) for plan `20250329_gta_game` produced an extra characterization with:
```json
{"type": "unknown_lever_id", "lever_id": "dummy_override"}
```
Evidence: `history/4/89_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`.

The string `"dummy_override"` is not a UUID — it is a fabricated placeholder string.
This pattern is new: the previous runs showed haiku hallucinating sequential hex-like UUIDs
(e.g., `"64a2e8f4-5c9e-..."`) but not semantic placeholder strings. The "verbatim id guidance"
change ("copy it verbatim from inside the tags") may have caused haiku to invent a symbolic
placeholder rather than a UUID-formatted fabrication.

All 8 real gta_game levers are correctly enriched (the extra entry is discarded), so this is
a cleanliness issue, not a correctness regression.

### N2 — qwen3-30b now below synergy/conflict word count target

**Before:** qwen3-30b synergy_avg = 23.8 words, conflict_avg = 24.5 words (within old 40–60 target,
near bottom of old range).

**After:** qwen3-30b synergy_avg = 18.1 words, conflict_avg = 19.8 words.

Both are below the new 20–40 target. qwen3-30b was already the most concise model before; the
additional tightening pushed it below the floor.

Evidence: computed from all 5 plans for runs 65 and 86.

### N3 — llama3.1 and gemini description word counts below new floor

**After** averages:
- llama3.1: 46.5 words (below 50–70 target)
- gemini: 47.8 words (below 50–70 target)

These were also near the low end before (48.9 and 65.9 words respectively). The prompt constraint
pushed llama3.1 further down (was already borderline) and over-corrected gemini (65.9 → 47.8).

Evidence: runs 62/83 and 67/88 across all 5 plans.

### N4 — gpt-4o-mini before/after descriptions appear identical for silo plan

The silo plan description for gpt-4o-mini is word-for-word identical between run 66 and run 87
(both 48 words). This suggests either model determinism or cache reuse — either way, the prompt
change had no observable effect on this particular model+plan combination.

Evidence: `history/4/66_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
line 36 vs `history/4/87_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` line 36.

---

## Positive Things

### P1 — Success rate improved: 33/35 → 35/35

Before: gpt-oss-20b timed out on `20260310_hong_kong_game` and `20260311_parasomnia_research_unit`
(both hit the 600s plan timeout in run 63).

After: gpt-oss-20b completed all 5 plans in run 84 (max 166s for hong_kong_game, no timeout).

The shorter prompts (reduced field counts) likely reduced generation time below the timeout
threshold. This is a direct structural benefit of the word-count reduction.

Evidence:
- `history/4/63_enrich_potential_levers/events.jsonl` lines 9–10: two `run_single_plan_error` events
  with `"error": "plan timeout after 600s"`.
- `history/4/84_enrich_potential_levers/events.jsonl`: all 5 `run_single_plan_complete` events,
  max duration 166s.

### P2 — Field lengths reduced across all models, most now at or below baseline

**Baseline** (5 plans, 35 levers, gemini-2.0-flash-001):
- description: 66.9 words avg
- synergy: 36.0 words avg
- conflict: 38.1 words avg

After PR #469, all 7 models produce descriptions at or below the baseline range. The before runs
had several models (gpt-oss-20b, gpt-5-nano) generating descriptions at 85.6 words — 28% over
baseline. After, gpt-oss-20b is at 58.9 words and gpt-5-nano at 55.7 words.

### P3 — haiku errors reduced overall (5 → 2)

**Before (run 68):** 5 `unknown_lever_id` errors across 2 plans (silo: 1, parasomnia: 4).
**After (run 89):** 2 `unknown_lever_id` errors across 2 plans (gta_game: 1 `dummy_override`,
hong_kong_game: 1 UUID-format entry `afb2eeca-...`).

The total error count improved. The parasomnia plan that had 4 errors before now has 0 errors.

Evidence: `history/4/89_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json`
error arrays across all plans.

### P4 — No lever_id hyphen-stripping observed

The PR explicitly targeted the gpt-4o-mini hyphen-stripping regression from #468. All lever_ids
in run 87 (gpt-4o-mini) match the standard UUID format with hyphens intact across all 5 plans.

The before runs (62–68) also had no hyphen-stripping (the baseline from #466 was clean), so this
confirms PR #469 does not regress the fix already in place.

Evidence: run 87, all 5 plans, `lever_id` fields are standard `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
format throughout.

### P5 — Anti-echoing qualitatively visible for haiku

**Before (run 68, haiku, parasomnia, Recruitment Channel Strategy):**
> "The Recruitment Channel Strategy focuses on optimizing participant enrollment for the study of
> adult NREM parasomnias. It controls the sources from which participants are recruited, aiming
> to balance enrollment rates with the representativeness of the sample. Key success metrics
> include the number of participants enrolled, the diversity of the participant demographics, and
> the overall quality of data collected. Effective recruitment is crucial for achieving the study's
> aims and ensuring robust statistical power in the findings."

**After (run 89, haiku, parasomnia, Recruitment Channel Strategy):**
> "Recruitment Channel Strategy determines enrollment volume and participant profile composition.
> The plan leverages three channels: University Hospital Bonn sleep clinic for pre-screened
> referrals, regional neurologist networks, and the Deutsche Gesellschaft für Schlafmedizin for
> broader reach. Success hinges on balancing steady enrollment against diagnostic rigor and
> demographic representativeness. Key metrics include application-to-enrollment ratio,
> time-to-enrollment, and baseline participant characteristics relative to target epidemiology."

The "after" description is shorter, more specific (names the three concrete channels), and
references domain-specific metrics (application-to-enrollment ratio, baseline participant
characteristics) rather than generic phrases. The anti-echoing effect is observable.

Evidence: `history/4/68_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`
vs `history/4/89_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`.

### P6 — No LLMChatError events in any run

Checked all 7 after-run `events.jsonl` files. No LLMChatError entries. No Pydantic validation
failures were triggered. The reduced word-count targets did not push output below schema
minimums.

---

## Comparison

| Aspect | Before (PR #466, runs 62–68) | After (PR #469, runs 83–89) |
|--------|------------------------------|------------------------------|
| Success rate | 33/35 (94.3%) | **35/35 (100%)** |
| gpt-oss-20b success | 3/5 | **5/5** |
| haiku `unknown_lever_id` errors | 5 (2 plans) | **2 (2 plans)** |
| UUID contamination | 0 | 0 |
| Lever_id hyphen-stripping | 0 | 0 |
| New error type (`dummy_override`) | 0 | **1** |
| LLMChatError events | 0 | 0 |
| gpt-4o-mini lever_ids | All valid UUIDs | All valid UUIDs |
| Fabricated % claims in consequences | Present (pre-existing) | Present (pre-existing) |

---

## Quantitative Metrics

### Field Length Comparison (avg words per lever)

| Era | Model | Run | desc (wc) | syn (wc) | conf (wc) | n |
|-----|-------|-----|-----------|----------|-----------|---|
| **Before** | llama3.1 | 62 | 48.9 | 46.8 | 41.6 | 35 |
| **Before** | gpt-oss-20b | 63 | 85.6 | 44.7 | 43.8 | 30 |
| **Before** | gpt-5-nano | 64 | 85.6 | 44.3 | 41.3 | 35 |
| **Before** | qwen3-30b | 65 | 48.9 | 23.8 | 24.5 | 35 |
| **Before** | gpt-4o-mini | 66 | 65.8 | 39.3 | 43.2 | 35 |
| **Before** | gemini | 67 | 65.9 | 39.5 | 40.5 | 35 |
| **Before** | haiku | 68 | 71.5 | 52.9 | 55.3 | 35 |
| Baseline | gemini-flash | — | **66.9** | **36.0** | **38.1** | 35 |
| **After** | llama3.1 | 83 | 46.5 | 33.6 | 30.7 | 35 |
| **After** | gpt-oss-20b | 84 | 58.9 | 25.9 | 25.9 | 35 |
| **After** | gpt-5-nano | 85 | 55.7 | 24.9 | 26.8 | 35 |
| **After** | qwen3-30b | 86 | 39.7 | 18.1 | 19.8 | 35 |
| **After** | gpt-4o-mini | 87 | 53.5 | 25.1 | 25.5 | 35 |
| **After** | gemini | 88 | 47.8 | 22.5 | 24.8 | 35 |
| **After** | haiku | 89 | 56.9 | 31.5 | 32.1 | 35 |

**Target** (PR #469): description 50–70 words, synergy/conflict 20–40 words.

**Target compliance (after):**
- description in-target (50–70): gpt-oss-20b ✓, gpt-5-nano ✓, gpt-4o-mini ✓, haiku ✓ (4/7)
- description below target: llama3.1 (46.5), qwen3-30b (39.7), gemini (47.8) (3/7)
- synergy in-target (20–40): llama3.1 ✓, gpt-oss-20b ✓, gpt-5-nano ✓, gpt-4o-mini ✓, gemini ✓, haiku ✓ (6/7)
- synergy below target: qwen3-30b (18.1) (1/7)
- conflict in-target (20–40): all 7 models ✓ (7/7) — qwen3-30b at 19.8 is borderline

### Field Length vs Baseline Ratio (after / baseline)

| Model | desc ratio | syn ratio | conf ratio |
|-------|-----------|-----------|------------|
| llama3.1 | 0.70× | 0.93× | 0.81× |
| gpt-oss-20b | 0.88× | 0.72× | 0.68× |
| gpt-5-nano | 0.83× | 0.69× | 0.70× |
| qwen3-30b | 0.59× | 0.50× | 0.52× |
| gpt-4o-mini | 0.80× | 0.70× | 0.67× |
| gemini | 0.71× | 0.63× | 0.65× |
| haiku | 0.85× | 0.88× | 0.84× |

All ratios are below 1.0× — the after runs are shorter than the baseline. No model exceeds the
2× warning threshold in either direction. The PR successfully brought content volume below the
baseline, reversing the verbosity inflation from earlier iterations.

### Error Summary

| Model | Before errors | After errors | Delta |
|-------|--------------|-------------|-------|
| llama3.1 | 0 | 0 | 0 |
| gpt-oss-20b | 0 | 0 | 0 |
| gpt-5-nano | 0 | 0 | 0 |
| qwen3-30b | 0 | 0 | 0 |
| gpt-4o-mini | 0 | 0 | 0 |
| gemini | 0 | 0 | 0 |
| haiku | 5 (2 plans) | 2 (2 plans) | **−3** |
| **Total** | **5** | **2** | **−3** |

### Plan Success Rate

| Model | Before (5 plans) | After (5 plans) | Delta |
|-------|-----------------|-----------------|-------|
| llama3.1 | 5/5 | 5/5 | 0 |
| gpt-oss-20b | **3/5** | **5/5** | **+2** |
| gpt-5-nano | 5/5 | 5/5 | 0 |
| qwen3-30b | 5/5 | 5/5 | 0 |
| gpt-4o-mini | 5/5 | 5/5 | 0 |
| gemini | 5/5 | 5/5 | 0 |
| haiku | 5/5 | 5/5 | 0 |
| **Total** | **33/35** | **35/35** | **+2** |

---

## Evidence Notes

1. **gpt-oss-20b timeout fix (P1):**
   - Before: `history/4/63_enrich_potential_levers/events.jsonl` — `run_single_plan_error` for
     hong_kong_game (600s) and parasomnia (600s).
   - After: `history/4/84_enrich_potential_levers/events.jsonl` — all 5 `run_single_plan_complete`,
     max 166s for hong_kong_game.

2. **haiku `dummy_override` error (N1):**
   - `history/4/89_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
   - `"errors": [{"type": "unknown_lever_id", "lever_id": "dummy_override"}]`
   - All 8 real levers enriched correctly alongside this error.

3. **haiku parasomnia improvement (P3):**
   - Before: `history/4/68_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json` — 4 sequential-hex fabricated UUIDs.
   - After: `history/4/89_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json` — `"errors": []`.

4. **Baseline data source:**
   `baseline/train/*/002-12-enriched_levers_raw.json` (5 plans, 35 levers, model: gemini-2.0-flash-001).
   The baseline synergy/conflict fields still contain UUID references (pre-PR #466 content), so the
   baseline word count includes those tokens. The after-run synergy/conflict fields do not contain
   UUIDs (only lever names). This slightly inflates the baseline word count and makes the after-run
   ratios look slightly smaller than they are.

5. **Anti-echoing evidence (P5):**
   - `history/4/68_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`
     (haiku, before): generic phrasing, 76 words for Recruitment Channel Strategy description.
   - `history/4/89_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`
     (haiku, after): domain-specific metrics, names three actual channels, 63 words.

---

## PR Impact

### What the PR was supposed to fix

1. **Regression from #467** (XML-tag regression — not detailed in metadata but mentioned as superseded).
2. **Regression from #468**: gpt-4o-mini stripped hyphens from lever_ids when description said
   "hexadecimal". Fix: replace "hexadecimal" and "uuid" wording with "verbatim" guidance.
3. **Verbosity**: descriptions and synergy/conflict text were above optimal length. Shorter output
   avoids timeout issues and reduces cost.
4. **Echoing**: descriptions were restating content from `consequences` and `review` rather than
   adding new insight.

### Before vs After Comparison Table

| Metric | Before (runs 62–68) | After (runs 83–89) | Change |
|--------|--------------------|--------------------|--------|
| Success rate | 33/35 (94.3%) | 35/35 (100%) | **+2 plans (+5.7%)** |
| gpt-oss-20b success | 3/5 | 5/5 | **+2** |
| haiku total errors | 5 | 2 | **−3** |
| New error type (dummy_override) | 0 | 1 | −1 (new) |
| UUID contamination | 0 | 0 | 0 |
| Lever_id hyphens intact (gpt-4o-mini) | ✓ | ✓ | 0 |
| Avg desc wc (all 7 models, mean) | 67.5 words | 51.3 words | **−16.2 words** |
| Avg syn wc (all 7 models, mean) | 41.6 words | 25.9 words | **−15.7 words** |
| Avg conf wc (all 7 models, mean) | 41.5 words | 26.4 words | **−15.1 words** |
| Models with desc in 50–70 target | 1/7 (qwen3-30b at 49) | 4/7 | **+3** |
| Models with syn in 20–40 target | 3/7 | 6/7 | **+3** |
| Fabricated % claims | Present, all models | Present, all models | 0 |

### Did the PR fix the targeted issues?

1. **Verbosity reduction**: YES. All 7 models reduced field lengths significantly.
   Mean description went from 67.5 → 51.3 words; synergy from 41.6 → 25.9 words.
   Most models now within the new target ranges.

2. **gpt-4o-mini lever_id hyphen-stripping (#468 regression)**: CANNOT FULLY VERIFY from these
   runs alone, because the before baseline (runs 62–68) was from PR #466 which also had clean
   lever_ids. The #468 regression runs are not included in this comparison. However, run 87
   (gpt-4o-mini, PR #469) shows all lever_ids with hyphens intact across all 5 plans, which
   is consistent with the fix working.

3. **Anti-echoing**: QUALITATIVELY YES for haiku. The parasomnia descriptions shifted from
   generic enrollment language to domain-specific metrics and named entities. Hard to quantify
   across all models without a reader evaluation.

4. **Verbatim id guidance**: PARTIALLY VERIFIED. The "dummy_override" error in haiku run 89
   suggests the new guidance introduced a new hallucination pattern (semantic placeholder instead
   of UUID-format fabrication). This is a minor side effect but worth tracking.

### Regressions introduced

- **N1**: haiku gta_game now produces `"dummy_override"` lever_id in errors (new failure mode).
- **N3**: llama3.1 (46.5 words) and gemini (47.8 words) description word counts now below 50-word
  floor. These models were already at the low end; the constraints over-corrected them.
- **N2**: qwen3-30b synergy/conflict now below the 20-word floor (~18–20 words). This model was
  already minimal; the constraint shrinks it further.

### Verdict

**CONDITIONAL**

The PR delivers real improvements:
- 100% success rate (up from 94.3%), driven by shorter output enabling gpt-oss-20b to complete
  within the 600s timeout.
- Field lengths normalized for all 7 models — all now within or below the baseline range, ending
  the multi-iteration verbosity inflation.
- haiku errors reduced from 5 to 2 overall.
- gpt-4o-mini lever_id format is correct.

The conditional qualification is based on:
1. Three models (llama3.1, gemini, qwen3-30b) now produce description or synergy/conflict text
   below the stated target minimums. The word-count constraints are working but over-correcting
   for the most concise models.
2. The `"dummy_override"` error in haiku gta_game run 89 is a new failure mode likely related to
   the verbatim ID guidance wording. It is benign (real levers are unaffected) but should be
   investigated.

**Recommended follow-up:**
- Suppress `errors.append` for `unknown_lever_id` in `enrich_potential_levers.py` (recommended
  in analysis 65 as B2) to clean up the noise signal.
- Investigate whether the "verbatim" phrasing triggered the `"dummy_override"` response in haiku.
  Could be addressed by adding "do not use placeholder strings" to the id guidance.
- Consider raising the floor for small concise models or making the target a soft cap rather than
  a hard constraint.

---

## Questions For Later Synthesis

**Q1**: The `"dummy_override"` lever_id in haiku run 89 gta_game is clearly a fabricated
placeholder string. Is this coming from the "verbatim" wording in the id guidance, or is it
a coincidence (haiku generating exactly this string by chance)? Running haiku again on gta_game
would clarify whether this is reproducible.

**Q2**: Baseline synergy/conflict text contains UUID references (baseline was generated before
PR #466). Does this inflate the baseline word count metrics, making the after-run ratios appear
larger reductions than they are in practice?

**Q3**: The anti-echoing instruction asks for "new insight beyond what consequences and review
already state." Is the improvement observed in haiku's parasomnia descriptions consistent across
other models? A qualitative review of gpt-4o-mini and gemini descriptions would confirm or deny.

**Q4**: qwen3-30b is now at ~18 words for synergy/conflict — below the 20-word floor. Does this
model genuinely not have enough to say at this density, or is it responding too literally to
"brevity first" guidance? A qwen3-30b-specific word count floor adjustment could help.

**Q5**: The backlog item B2 ("suppress `errors.append` for `unknown_lever_id`") was recommended
in analysis 65 but has not been merged yet. If this fix is in PR #469, the haiku error count
comparison would be misleading. Verify whether B2 was included in #469's diff.

---

## Reflect

The PR achieves its primary goals: verbosity is reduced, and the targeted regressions from #467
and #468 are not observable in run 87. The unexpected finding is that brevity constraints are a
double-edged blade — they successfully truncated verbose models (gpt-oss-20b: 85.6 → 58.9 words)
while pushing already-concise models (qwen3-30b, llama3.1) below the minimum floor.

The most structurally important benefit is the 100% success rate: two fewer timeouts means
gpt-oss-20b is now reliably usable for the two longest-running plans. This is a direct consequence
of shorter prompts generating faster, not a quality change.

The content quality trajectory is positive: all models are now within or below baseline length,
and haiku's anti-echoing improvement shows the instruction is reaching at least one model
effectively. The fabricated % claims and marketing-copy language in `consequences` remain
(pre-existing from the identify step), but this is upstream of the enrich step.

---

## Potential Code Changes

**C1 — Suppress `errors.append` for `unknown_lever_id` in `enrich_potential_levers.py`**

Recommended in analysis 65 (B2) and still not resolved. The `"dummy_override"` entry and the
UUID-format fabrications from haiku are all discarded at enrichment — they never affect the
output. Appending them to `errors` conflates expected over-generation noise with real failures.
Remove the `errors.append(...)` call for `unknown_lever_id` events; keep the `logger.warning` for
debugging. This is a one-line code change.

**C2 — Add "do not use placeholder strings" to verbatim id guidance**

The `"dummy_override"` lever_id suggests the current guidance ("copy it verbatim from inside
the tags") is being misinterpreted by haiku as permission to use a placeholder when uncertain.
Adding a negative constraint specifically for placeholder strings ("copy exactly as-is — do not
substitute placeholder text like 'dummy', 'test', or similar") may prevent this. Unlike generic
negative prohibitions, this is a narrow guard for a specific observed failure mode.

**C3 — Consider per-model word count targets or a softer floor constraint**

The current word count targets are single values applied uniformly. qwen3-30b, llama3.1, and
gemini are naturally concise and consistently produce descriptions below 50 words. If the floor
is enforced as a hard constraint via schema validators (which it is not currently, based on no
LLMChatErrors), it would trigger validation failures. As long as the constraint is prompt-level
guidance only, the under-shooting is benign — but it does mean these models are not hitting the
stated target range.

---

## Summary

PR #469 delivers measurable improvements across all key metrics:

- **100% success rate** (35/35 plans, up from 33/35) — the gpt-oss-20b timeout issue resolved.
- **Field lengths normalized** — all 7 models now within or below baseline, ending verbosity
  inflation.
- **haiku errors reduced** (5 → 2) — but a new `"dummy_override"` error type appeared.
- **Lever_id format intact** — no hyphen-stripping in gpt-4o-mini.
- **Anti-echoing visible** in haiku's domain-specific descriptions.

Three minor issues require follow-up (N1, N2, N3), but none affect the correctness of lever
enrichment. The verdict is **CONDITIONAL**: merge, but address the `dummy_override` pattern
and the code-level B2 fix (suppress `errors.append` for `unknown_lever_id`) promptly.
