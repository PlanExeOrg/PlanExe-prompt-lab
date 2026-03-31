# Insight Claude

## Overview

This analysis evaluates **PR #462** ("Use integer lever indices to eliminate UUID contamination in enrich step")
against runs from analysis 60 (PR #457 "Strip UUIDs from full lever context string in enrich step").

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared**:

| Model | Before (analysis 60) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/27_enrich_potential_levers` | `4/48_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/28_enrich_potential_levers` | `4/49_enrich_potential_levers` |
| openai-gpt-5-nano | `4/29_enrich_potential_levers` | `4/50_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/30_enrich_potential_levers` | `4/51_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/31_enrich_potential_levers` | `4/52_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/32_enrich_potential_levers` | `4/53_enrich_potential_levers` |
| anthropic-claude-haiku-4-5-pinned | `4/33_enrich_potential_levers` | `4/54_enrich_potential_levers` |

**PR change summary** (from `enrich_potential_levers.py`):

- Per-batch prompt now uses `Lever {idx}` (integer indices) instead of `Lever ID: {uuid}` for each lever
- `index_to_full` dict maps `str(idx)` → `lever.lever_id` (UUID), built during prompt construction
- Post-processing maps response `char.lever_id` back: `index_to_full.get(char.lever_id, char.lever_id)`
- System prompt adds: "refer to other levers by their name — not an identifier"
- `full_lever_context_str` already stripped UUIDs in PR #457; no change in this PR

---

## Negative Things

### N1 — llama3.1 CATASTROPHIC: 0/35 characterized levers across all 5 plans

Run 4/48 (llama3.1) produces **zero** enriched levers for all 5 plans. Every plan shows
`"characterized_levers": []` with 70 total errors across all plans.

The failure pattern per plan:

- `unknown_lever_id` errors: `lever_id` values are `"Lever1"`, `"Lever2"`, `"Lever 1"`, `"Lever 2"`,
  or full lever names like `"Technological Integration Strategy"` — never plain integers `"1"`, `"2"`
- `incomplete` errors: `lever_id` values are real UUIDs picked up from the input context
  (e.g., from `deduplication_justification` fields which contain UUID references to other levers)

Root cause: the post-processing mapping `index_to_full.get(char.lever_id, char.lever_id)` looks up
keys like `"1"`, `"2"` (plain integers). llama3.1 returns `"Lever1"` or `"Lever 2"` (the full label
as it appears in the prompt: `f"Lever {idx}\n"`). The key `"Lever 1"` is not in `index_to_full`,
so `char.lever_id` is returned unchanged — and no UUID matches it.

Evidence:
- `history/4/48_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  `"characterized_levers": []`, errors include `"lever_id": "Technological Integration Strategy"`
  and `"lever_id": "1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd"` (incomplete)
- `history/4/48_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`:
  errors include `"lever_id": "Lever1"`, `"lever_id": "Lever2"`, ..., `"Lever5"`
- Before (run 27): 35/35 characterized, 0 errors

### N2 — gpt-oss-20b: 23/35 characterized levers (34% loss)

Run 4/49 (gpt-oss-20b) produces 23 out of 35 expected levers. It has 24 errors. The error
pattern is the same `"Lever N"` echo: some batches succeed, others fail with
`"Lever 1"`, `"Lever 2"` as `lever_id`.

Evidence:
- `history/4/49_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  5 unknown_lever_id with `"Lever 1"` through `"Lever 5"`, 8 incomplete with real UUIDs,
  `"characterized_levers": []`
- Before (run 28): 15 levers from 2 plans (3 timed out — unrelated network issue), 0 errors

### N3 — gpt-5-nano: 22/35 characterized levers (37% loss)

Run 4/50 (gpt-5-nano) produces 22 out of 35 expected levers, with 26 errors. This is a
function-calling model (`is_function_calling_model: true`) but it still returns lever names
instead of integer IDs for some batches.

Failure pattern: returns lever names in `lever_id` field (e.g., `"Geopolitical Risk Mitigation
Strategy"`, `"Hong Kong Identity Amplification Strategy"`). Successful batches return correct UUIDs.

Evidence:
- `history/4/50_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  8 unknown_lever_id (lever names), 8 incomplete (UUIDs), 0 characterized_levers
- `history/4/50_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  0 errors, 7 characterized_levers (works for some plans)

### N4 — haiku: 22 new unknown_lever_id errors with raw integer strings

Run 4/54 (haiku) produces all 35 correctly characterized levers, but generates 22 extra
`unknown_lever_id` errors where `lever_id` is a raw integer string like `"4"`, `"5"`, `"6"`.

These extra errors come from haiku returning additional function-call results that use the
integer index itself as the `lever_id` rather than the mapped UUID. The real levers are enriched
correctly, but there are 22 spurious "ghost" characterizations.

Evidence:
- `history/4/54_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  5 unknown_lever_id with `"4"`, `"5"`, `"6"`, `"7"`, `"8"`; 8 characterized_levers correct
- `history/4/54_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  7 unknown_lever_id with raw integers `"3"` through `"7"`; 7 characterized_levers correct
- Before (run 33): 35 characterized, 7 errors (fabricated UUID strings — a different issue)

### N5 — qwen3 and gpt-4o-mini: minor lever losses in 1–2 plans each

Run 4/51 (qwen3-30b): 33/35 characterized, 4 errors — both errors from the `hong_kong_game`
plan's last batch, where levers 6–7 are returned as names instead of integers.

Run 4/52 (gpt-4o-mini): 30/35 characterized, 10 errors — errors from `hong_kong_game` (last
batch, 2 levers lost) and `parasomnia` (last batch, 3 levers lost). Same name-echo pattern.

Evidence:
- `history/4/51_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`:
  unknown_lever_id `"Geopolitical Risk Mitigation Strategy"` and `"Hong Kong Identity Amplification Strategy"`
- `history/4/52_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`:
  unknown_lever_id `"Staffing Coverage Model"`, `"Risk Mitigation Protocol"`, `"Data Annotation Workflow"`

### N6 — Prompt format mismatch: "Lever N" label vs plain integer expected by mapping

The per-batch prompt uses `f"Lever {idx}\n"` (with the "Lever " prefix). The `index_to_full`
mapping uses `str(idx)` as the key (plain integers). Models that faithfully reproduce the
label `"Lever 1"` in the `lever_id` response field fail the mapping lookup. Only models that
extract the bare digit `"1"` from the label succeed.

This is a design flaw in the current PR: the format shown to the model (`"Lever 1"`) is different
from the format the code expects (`"1"`). The PR description says integer indices work "universally"
but that claim is falsified: 4/7 models fail or degrade.

---

## Positive Things

### P1 — gemini: 35/35 characterized levers with 0 UUID contamination

Run 4/53 (gemini) achieves perfect enrichment: 35/35 levers, 0 errors. synergy_text and
conflict_text contain 0 UUID occurrences. The integer index scheme works flawlessly for this model.

Evidence:
- `history/4/53_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  8 characterized_levers with clean synergy/conflict text (no UUID strings)
- Before (run 32): 35 characterized, 0 errors, 0 UUIDs (already clean after PR #457)

### P2 — All 3 working models have 0 UUID contamination in synergy/conflict text

For qwen3 (run 51), gpt-4o-mini (run 52), and gemini (run 53), grep finds zero UUID occurrences
in any `synergy_text` or `conflict_text` field. The integer index scheme, when it works, achieves
its stated goal.

Before (analysis 60): llama3.1 had 20 UUID occurrences remaining in free text (from per-batch
`Lever ID:` — already partially fixed by PR #457). This PR was intended to eliminate these.
After (this analysis): 0 occurrences — but llama3.1 now produces no output at all.

### P3 — 35/35 plan completion rate (status: ok) for all 7 models

All 35 runs completed without timeout or pipeline-level failure. The UUID→integer change
does not introduce LLMChatErrors or retry storms. The errors that appear are post-processing
errors (wrong lever_id format), not LLM schema validation failures.

Evidence: `history/4/48_enrich_potential_levers/outputs.jsonl` through `54_*`: all 5 plans per
model have `"status": "ok"`.

### P4 — Content quality stable for working models (field lengths near baseline)

For the 3 models that work correctly, field lengths are close to or below the 2× warning
threshold vs baseline:

| Source | avg_desc | avg_syn | avg_conf |
|--------|----------|---------|----------|
| Baseline (35 levers) | 484 chars | 286 chars | 298 chars |
| qwen3-30b (run 51) | 388 (0.80×) | 187 (0.65×) | 203 (0.68×) |
| gpt-4o-mini (run 52) | 447 (0.92×) | 272 (0.95×) | 295 (0.99×) |
| gemini (run 53) | 501 (1.04×) | 280 (0.98×) | 298 (1.00×) |

No model exceeds the 2× warning threshold. No fabricated percentage claims observed in
the working models' synergy/conflict text (spot checks). Content quality regression is not
an issue for the models that can produce output.

---

## PR Impact

### What the PR Was Supposed to Fix

PR #462 aimed to complete the UUID elimination work started in PR #457. After PR #457 stripped
UUIDs from `full_lever_context_str`, llama3.1 still had 15–20 UUID occurrences in synergy/conflict
text because the per-batch prompt (`lever_details_for_prompt`) still showed `Lever ID: {uuid}`.
PR #462 replaces `Lever ID: {uuid}` with `Lever 1`, `Lever 2`, etc. in the per-batch prompt
and maps these indices back to UUIDs post-processing.

The PR description claims: "Works universally for both text-completion and function-calling models."

### Before vs After Comparison Table

| Metric | Before (runs 4/27–33) | After (runs 4/48–54) | Change |
|--------|----------------------|----------------------|--------|
| Overall plan success (status:ok) | 34/35 (gpt-oss-20b: 3 timeouts) | **35/35** | +1 |
| Total characterized levers (5 plans each) | 209* | **178** | **–31** |
| llama3.1 characterized | 35/35 | **0/35** | **–35 (catastrophic)** |
| gpt-oss-20b characterized (5 plans) | ~35 (est.) | **23/35** | **–12** |
| gpt-5-nano characterized | 35/35 | **22/35** | **–13** |
| qwen3-30b characterized | 35/35 | 33/35 | –2 |
| gpt-4o-mini characterized | 35/35 | 30/35 | –5 |
| gemini characterized | 35/35 | 35/35 | 0 |
| haiku characterized | 35/35 | 35/35 | 0 |
| Total errors | 7 (haiku fabricated UUIDs) | **152** | **+145** |
| llama3.1 errors | 0 | **70** | **+70** |
| gpt-oss-20b errors | 0 | **24** | **+24** |
| gpt-5-nano errors | 0 | **26** | **+26** |
| qwen3-30b errors | 0 | 4 | +4 |
| gpt-4o-mini errors | 0 | 10 | +10 |
| gemini errors | 0 | 0 | 0 |
| haiku errors | 7 | **22** | +15 |
| UUID in synergy/conflict (llama3.1) | 20 | 0 (no output) | –20 |
| UUID in synergy/conflict (all models) | 20 | **0** | –20 |

*Before gpt-oss-20b: 3 timeout failures (network issue); if all 5 plans ran ~35 would be expected.

### Did the PR Fix the Targeted Issue?

**For UUID contamination in synergy/conflict text**: YES — 0 UUIDs remain in the 3 working
models. The integer index scheme effectively prevents UUID leakage when it works.

**For universal model compatibility**: NO — the PR breaks 4/7 models:
- llama3.1: total failure (0/35 levers)
- gpt-oss-20b: major failure (12/35 levers lost)
- gpt-5-nano: major failure (13/35 levers lost)
- haiku: minor regression (22 extra errors, real levers still OK)
- qwen3 and gpt-4o-mini: minor regressions (2 and 5 levers lost in edge-case batches)

### Root Cause of Failures

The per-batch prompt shows levers as:
```
Lever 1
Name: Technological Integration Strategy
...
```

The `index_to_full` mapping uses plain integer strings as keys: `index_to_full["1"] = uuid`.

The post-processing does: `index_to_full.get(char.lever_id, char.lever_id)`

Models that return `"1"` as `lever_id` → maps to UUID → success.
Models that return `"Lever 1"` as `lever_id` → not in dict → `char.lever_id` returned unchanged →
`unknown_lever_id` error.

The prompt format (`"Lever 1"`) and the mapping key (`"1"`) are mismatched. Models that
faithfully copy the prompt label fail; models that extract the bare integer succeed.

### Regressions

1. **llama3.1 total failure (N1)**: 35 → 0 levers. This is the worst regression.
2. **gpt-oss-20b major failure (N2)**: ~35 → 23 levers.
3. **gpt-5-nano major failure (N3)**: 35 → 22 levers.
4. **haiku extra errors (N4)**: 7 → 22 errors (real levers still OK).
5. **qwen3 and gpt-4o-mini minor failures (N5)**: small lever losses in edge-case batches.

### Verdict: **REVERT**

The PR introduces a fundamental format mismatch between the prompt (`"Lever N"`) and the mapping
key (`"N"`), causing 3 models to lose 30–100% of their characterized levers and 2 more to lose
5–15%. Only gemini and haiku (real levers) achieve full output. The claimed "universal" benefit
is not realized.

The previous state (analysis 60, after PR #457) was strictly better: 209+ levers characterized
with 20 residual UUID occurrences vs 178 levers with 0 UUID occurrences. Losing 31 levers (14.8%)
is a worse outcome than having 20 UUID contamination occurrences in one model's free-text fields.

---

## Comparison

### Characterized Levers: Before vs After (all plans)

| Model | Before (runs 27–33) | After (runs 48–54) | Change |
|-------|--------------------|--------------------|--------|
| llama3.1 | 35/35 | **0/35** | –35 |
| gpt-oss-20b | ~35 (est.) | 23/35 | –12 |
| gpt-5-nano | 35/35 | 22/35 | –13 |
| qwen3-30b | 35/35 | 33/35 | –2 |
| gpt-4o-mini | 35/35 | 30/35 | –5 |
| gemini | 35/35 | 35/35 | 0 |
| haiku | 35/35 | 35/35 | 0 |
| **Total** | **~209** | **178** | **–31** |

### Error Counts: Before vs After

| Model | Before errors (type) | After errors (type) |
|-------|---------------------|---------------------|
| llama3.1 | 0 | **70** (unknown_lever_id + incomplete) |
| gpt-oss-20b | 0 | **24** (unknown_lever_id + incomplete) |
| gpt-5-nano | 0 | **26** (unknown_lever_id + incomplete) |
| qwen3-30b | 0 | 4 (unknown_lever_id + incomplete) |
| gpt-4o-mini | 0 | 10 (unknown_lever_id + incomplete) |
| gemini | 0 | 0 |
| haiku | 7 (fabricated UUIDs) | 22 (raw integer strings) |

---

## Quantitative Metrics

### Lever Recovery Rate per Model

| Model | Characterized (after) | Expected | Recovery % |
|-------|----------------------|----------|-----------|
| llama3.1 | 0 | 35 | **0%** |
| gpt-oss-20b | 23 | 35 | **66%** |
| gpt-5-nano | 22 | 35 | **63%** |
| qwen3-30b | 33 | 35 | **94%** |
| gpt-4o-mini | 30 | 35 | **86%** |
| gemini | 35 | 35 | **100%** |
| haiku | 35 | 35 | **100%** |
| **Aggregate** | **178** | **245** | **73%** |

### Error Type Breakdown (after runs, all models)

| Error Type | Count | Models Affected |
|-----------|-------|----------------|
| unknown_lever_id (name string) | 65 | llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, gpt-4o-mini |
| incomplete (valid UUID found, no characterization) | 65 | llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, gpt-4o-mini |
| unknown_lever_id (raw integer) | 22 | haiku |
| **Total** | **152** | — |

### Field Length vs Baseline (working models only)

| Model | avg_desc | d/b | avg_syn | s/b | avg_conf | c/b |
|-------|----------|-----|---------|-----|----------|-----|
| Baseline | 484 | 1.0× | 286 | 1.0× | 298 | 1.0× |
| qwen3-30b (run 51) | 388 | 0.80× | 187 | 0.65× | 203 | 0.68× |
| gpt-4o-mini (run 52) | 447 | 0.92× | 272 | 0.95× | 295 | 0.99× |
| gemini (run 53) | 501 | 1.04× | 280 | 0.98× | 298 | 1.00× |

No working model exceeds 2× on any field. qwen3 produces notably shorter text (~0.65–0.80×)
but does not pad with marketing language.

### UUID Contamination (synergy_text + conflict_text combined)

| Model | Before (runs 27–33) | After (runs 48–54) |
|-------|--------------------|--------------------|
| llama3.1 | 20 occurrences | 0 (no output) |
| gpt-oss-20b | 0 | 0 |
| gpt-5-nano | 0 | 0 |
| qwen3-30b | 0 | 0 |
| gpt-4o-mini | 0 | 0 |
| gemini | 0 | 0 |
| haiku | 0 | 0 |
| **Total** | **20** | **0** |

---

## Evidence Notes

Files consulted:

- `history/4/48_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 gta_game (0 characterized, lever names + UUIDs as errors)
- `history/4/48_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — llama3.1 sovereign_identity (1 batch, 5 "Lever1"-"Lever5" errors + 5 incomplete)
- `history/4/48_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 hong_kong (7 errors, 0 characterized)
- `history/4/49_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-oss-20b gta_game ("Lever 1"-"Lever 5" errors + UUIDs incomplete)
- `history/4/50_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-5-nano gta_game (lever names, 0 characterized)
- `history/4/50_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — gpt-5-nano silo (0 errors, 7 characterized — works)
- `history/4/51_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — qwen3 gta_game (0 errors, 8 characterized — works)
- `history/4/52_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-4o-mini gta_game (0 errors, 8 characterized — works)
- `history/4/53_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gemini gta_game (0 errors, 8 characterized — works)
- `history/4/54_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku gta_game (5 unknown_lever_id with "4"-"8", 8 characterized)
- `history/4/54_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — haiku silo (7 unknown_lever_id with integers, 7 characterized)
- `history/4/27_enrich_potential_levers/outputs.jsonl` through `33_*` — before success rates
- `history/4/48_enrich_potential_levers/outputs.jsonl` through `54_*` — after success rates (all ok)
- `history/4/48_enrich_potential_levers/events.jsonl` — no LLMChatErrors
- `analysis/63_enrich_potential_levers/events.jsonl` — analysis start/complete timestamps
- PlanExe source: `enrich_potential_levers.py` lines 139 (lever_id schema field), 216 (full_lever_context_str), 242–253 (per-batch prompt + index_to_full map), 282–284 (index-to-UUID mapping back)

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS status after this PR:

| Problem | Status after PR #462 |
|---------|---------------------|
| Boilerplate descriptions | Not observed in working models |
| Phantom lever references | Not observed |
| UUID cross-reference leakage | Fixed for all models that produce output |
| Same-batch UUID copying (per-batch prompt) | Eliminated by integer index scheme |
| Integer index echoing in lever_id field | **NEW — llama3.1/gpt-oss-20b/gpt-5-nano return "Lever N"** |
| Haiku extra characterizations (fabricated UUIDs) | Replaced by extra integer-ID characterizations |

**New problem not yet in OPTIMIZE_INSTRUCTIONS (proposed addition)**:

1. **"Lever N" label copying by text-completion models**: When per-batch levers are labeled
   `Lever 1`, `Lever 2`, etc., several text-completion models return the full label
   `"Lever 1"` as the `lever_id` field rather than extracting the bare integer `"1"`.
   The current mapping code uses `str(idx)` (bare integer) as the dict key and fails to
   match `"Lever 1"`. Propose: change prompt to use bare integer (`f"{idx}\n"`) or add
   "Lever " prefix stripping to the mapping: `index_to_full.get(char.lever_id.removeprefix('Lever ').strip(), char.lever_id)`.

---

## Questions For Later Synthesis

1. **Should the per-batch prompt use bare integers instead of "Lever N"?** Changing
   `f"Lever {idx}\n"` to `f"{idx}\n"` (or `f"Lever ID: {idx}\n"`) would likely fix the
   llama3.1/gpt-oss-20b/gpt-5-nano failures. The mapping code already expects bare integers.

2. **Should the mapping code be made more robust?** Adding a strip of common prefixes
   (`"Lever "`, `"lever_"`, whitespace) to the `char.lever_id` before dict lookup would
   make the system tolerant of model formatting variations without requiring a prompt change.
   Both C1 and C2 below would achieve this.

3. **Why does gpt-5-nano partially succeed?** gpt-5-nano is a function-calling model but
   still fails some plans with lever-name IDs. It succeeds for single-batch plans
   (sovereign_identity) and some multi-batch plans (silo) but fails for gta_game and hong_kong.
   The difference may be plan-specific (the lever names in gta_game/hong_kong trigger name
   copying), or batch-size-specific.

4. **Why does haiku produce raw integer IDs in some function calls?** Haiku returns the
   integer index directly as `lever_id` in additional tool calls, while also returning correctly
   UUID-mapped characterizations. This suggests haiku is making redundant tool calls, with
   some calls mapping correctly and others returning the raw index.

5. **Is this PR's core idea salvageable?** The integer index concept is sound — if the prompt
   were changed to use bare integers and the mapping made robust to prefixes, the UUID
   contamination goal would be achieved. The current PR has a fixable implementation bug.

---

## Reflect

The PR's core design (replace UUIDs with integers, map back post-processing) is architecturally
correct and represents the right direction. PR #457 removed UUIDs from the full-context list;
PR #462 was supposed to remove them from the per-batch prompt.

However, a single implementation detail — the "Lever " prefix in the prompt format — breaks the
entire system for 3 models. The mapping code expects bare `"1"`, `"2"` keys, but the prompt
shows `"Lever 1"`, `"Lever 2"`. Models that are literal about using the label as-is fail;
models that extract the number succeed.

This is a correctness bug, not a fundamental design flaw. The fix is small (either side of the
mapping/prompt interface). The PR should be reverted in its current form, fixed, and re-tested.
The regression for llama3.1 (0/35 levers, was 35/35) is severe enough that the PR cannot be
conditionally accepted as-is.

---

## Potential Code Changes

**C1** — Change per-batch prompt to use bare integer identifier.

In `enrich_potential_levers.py` line ~247, change:
```python
f"Lever {idx}\n"
```
to:
```python
f"Lever ID: {idx}\n"
```
or simply:
```python
f"{idx}\n"
```

This aligns the prompt label with the `index_to_full` key format (bare integer string `"1"`).
Expected effect: llama3.1, gpt-oss-20b, gpt-5-nano recover to near-100% characterization.
Risk: Bare integers might be less clear to function-calling models about what to fill in.
A label like `"Lever ID: 1"` with the schema description `"The integer identifier shown after 'Lever ID:'"` might be clearer.

Evidence: The current failures stem entirely from `"Lever 1"` not matching the key `"1"`.
Changing the prefix resolves the mismatch.

**C2** — Make mapping code robust to "Lever " prefix.

In the post-processing (line ~282):
```python
raw_id = char.lever_id.strip()
if raw_id.upper().startswith("LEVER "):
    raw_id = raw_id[6:].strip()
full_id = index_to_full.get(raw_id, index_to_full.get(char.lever_id, char.lever_id))
```

This is a defensive code-level fix that would recover llama3.1's lever output without
changing the prompt format. Less clean than C1 but lower risk of side effects.

**H1** — Update OPTIMIZE_INSTRUCTIONS to document the "Lever N" copy pattern.

Add to the known-problems list: "Text-completion models may copy the full prompt label
('Lever 1', 'Lever 2') verbatim as the `lever_id` response field instead of extracting
the bare integer. Ensure the prompt format and mapping key format are identical, or make
the mapping code tolerant of common prefixes. Function-calling models are generally more
reliable at using the correct type (integer) but may also produce extra tool calls with
raw integer IDs in some batches."

**H2** — Add explicit instruction in per-batch prompt about the expected ID format.

In the per-batch user prompt, after the lever list, add:
> "Use the integer number shown before each lever's name as that lever's `lever_id` in
> your response (e.g., if the lever begins with '3', set lever_id to '3')."

This directly addresses the lever-name-as-ID and "Lever N"-as-ID failure modes.

---

## Summary

PR #462 ("Use integer lever indices to eliminate UUID contamination in enrich step") introduces
a format mismatch that causes catastrophic failure for llama3.1 (0/35 levers) and major failures
for gpt-oss-20b (~23/35) and gpt-5-nano (22/35). Only gemini, qwen3, gpt-4o-mini, and haiku's
real levers survive intact.

The root cause: the per-batch prompt labels levers as `"Lever 1"`, `"Lever 2"` but the
post-processing mapping expects the bare integer `"1"`, `"2"` as the `lever_id` return value.
Models that echo the full label fail the lookup; models that return just the digit succeed.

Before this PR (analysis 60): 209 levers characterized, 20 UUID occurrences (llama3.1 only).
After this PR (analysis 63): 178 levers characterized, 0 UUID occurrences.

The PR's UUID elimination goal is partially achieved (for working models), but at the cost of
losing 31 levers (-14.8%) — a worse overall outcome. The implementation bug is fixable with
a small prompt or code change (C1 or C2).

**Verdict: REVERT**. The current implementation has a correctness bug that breaks 3/7 models.
Fix the prompt format mismatch (C1 or C2) and re-run before merging this PR.
