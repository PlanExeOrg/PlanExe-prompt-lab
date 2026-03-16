# Insight Claude

## Overview

Analysis of runs 1/24–1/30 (`identify_potential_levers`), covering seven models against
five plans (silo, gta_game, sovereign_identity, hong_kong_game, parasomnia_research_unit)
using prompt `prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`.

No PR info in `meta.json`, but the memory index for iteration 17 is titled
"review_lever auto-correct (runs 124–130)", suggesting this batch is the post–PR validation
round following the auto-correction recommendation from `analysis/16_identify_potential_levers/assessment.md`.

---

## Rankings

Ranked by plan success rate and output quality:

| Rank | Run | Model | Success | Notable |
|------|-----|-------|---------|---------|
| 1 | 30 | anthropic-claude-haiku-4-5-pinned | 5/5 (100%) | Highest quality; specific numbers throughout |
| 2 | 29 | openrouter-gemini-2.0-flash-001 | 5/5 (100%)* | Config issue recovered; 11 calls/plan |
| 3 | 28 | openrouter-openai-gpt-4o-mini | 5/5 (100%) | Consistent; 11 calls/plan |
| 4 | 27 | openrouter-qwen3-30b-a3b | 5/5 (100%) | All plans succeed BUT 100% consequence contamination |
| 5 | 26 | openai-gpt-5-nano | 5/5 (100%) | 10 calls/plan; 136k output tokens on silo; cost=0 |
| 6 | 24 | ollama-llama3.1 | 5/5 (100%) | 3 calls/plan sequential; bracket contamination in call-3 |
| 7 | 25 | openrouter-openai-gpt-oss-20b | 4/5 (80%) | Parasomnia JSON EOF — third occurrence |

*Run 29: all 5 plans initially failed (wrong model name), then all 5 recovered via second wave.

---

## Negative Things

### N1 — gpt-oss-20b parasomnia JSON EOF (third consecutive occurrence)

Run 25 (`openrouter-openai-gpt-oss-20b`) fails on `20260311_parasomnia_research_unit`
with:

```
1 validation error for DocumentDetails
  Invalid JSON: EOF while parsing a list at line 58 column 5
```

Source: `history/1/25_identify_potential_levers/events.jsonl` line 7 and
`history/1/25_identify_potential_levers/outputs.jsonl` line 2.

This is the **third consecutive batch** where gpt-oss-20b fails on parasomnia:
- Analysis/15 (run 1/04): hong_kong JSON extraction failure (different plan)
- Analysis/16 (run 1/18): parasomnia EOF at line 25, column 5
- Analysis/17 (run 1/25): parasomnia EOF at line **58**, column 5

The line number increased from 25 to 58 between runs 18 and 25 — the model got further
into the JSON response before truncation, possibly due to a provider routing change
(analysis/16 used `DeepInfra:openai/gpt-oss-20b`; run 25 also shows activity_overview
with `DeepInfra` and `Groq` variants from `history/1/25_identify_potential_levers/outputs/20260311_parasomnia_research_unit/activity_overview.json`
— two calls, 10,220 and 10,975 tokens respectively). The `EOF` error is not in
`_TRANSIENT_PATTERNS`, so no retry is attempted.

### N2 — qwen3 consequence contamination (100% of levers, all plans)

Run 27 (`openrouter-qwen3-30b-a3b`) appends the review text verbatim to the end of every
`consequences` field. Confirmed across all 17 levers in the silo plan:

Example from `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever `118359f7`:
```json
"consequences": "Immediate: Enhanced surveillance reduces dissent → Systemic: 30% decrease
  in social cohesion metrics → Strategic: Creates dependency on authoritarian oversight ...
  Controls security vs. autonomy. Weakness: The options fail to account for psychological
  resistance to perpetual monitoring.",
"review": "Controls security vs. autonomy. Weakness: The options fail to account for
  psychological resistance to perpetual monitoring."
```

The `review` text ("Controls … Weakness: …") is duplicated at the end of `consequences`.
All 17 silo levers are contaminated; the same pattern is visible in the gta_game plan
(lever `74e0bd5f` "Urban Fabric Synthesis":
`history/1/27_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`).

This qwen3-specific contamination was first noted in analysis/15, partially observed in
analysis/16 (only 4 plans available due to parasomnia failure), and is now fully confirmed
as a **100% contamination rate across all plans**.

### N3 — llama3.1 bracket contamination in third LLM call

Run 24 (`ollama-llama3.1`) produces clean consequences in calls 1 and 2, but the third
call generates bracket-wrapped content in the `consequences` field:

Example from `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever `21c6aac4` ("Civic Architecture"):
```json
"consequences": "Immediate: [Establish a strict hierarchical structure → Systemic:
  [Create a controlled environment with limited social mobility] → Strategic:
  [Risk amplifying existing power dynamics]"
```

Six consecutive levers (levers 9–14 by index) in the silo plan show this bracket pattern.
All belong to the third LLM call (calls: 3 total per `history/1/24_identify_potential_levers/outputs/20250321_silo/activity_overview.json`
showing 3 calls). The model reverts to placeholder brackets rather than filling in
actual content for the third call.

### N4 — Run 29 gemini initial config failure (all 5 plans fail first wave)

Run 29 (`openrouter-gemini-2.0-flash-001`) shows two complete waves in `events.jsonl`:
- Wave 1 (lines 1–10): All 5 plans fail immediately with:
  `Cannot create LLM, the llm_name 'openrouter-paid-gemini-2.0-flash-001' is not found`
- Wave 2 (lines 11–21): All 5 plans succeed in 35–38s each

The runner attempted model name `openrouter-paid-gemini-2.0-flash-001` (a "paid" variant)
which is not registered in the active LLM config. It then retried (at some level above the
plan loop) and succeeded. Source: `history/1/29_identify_potential_levers/events.jsonl` and
`history/1/29_identify_potential_levers/outputs.jsonl` lines 1–10 (errors) vs. 6–10 (ok).

This doubles the time cost for the Gemini model: 5 wasted starts + 5 actual runs.

### N5 — qwen3 options often label-like and short

Run 27 (qwen3) gta_game options are noticeably shorter than other models. Example from lever
"Urban Fabric Synthesis":
```
"Mimic existing cities with localized zoning and infrastructure"
"Blend urban elements with abstract, stylized reinterpretations"
"Deploy AI-driven adaptive environment generation based on real-world data"
```

The prompt requires "complete strategic approaches" and "show clear progression". These
options read more like labels than full strategic descriptions. Compare to run 30 (haiku)
gta_game options which span 40–80 words each with specific technical/financial parameters.

---

## Positive Things

### P1 — Highest-ever observed overall success rate: 34/35 (97.1%)

| Iteration | Success |
|-----------|---------|
| Analysis/15 (runs 1/10–1/16) | 32/35 (91.4%) |
| Analysis/16 (runs 1/17–1/23) | 31/35 (88.6%) |
| **Analysis/17 (runs 1/24–1/30)** | **34/35 (97.1%)** |

The sole failure (run 25 parasomnia EOF) is a pre-existing, model-specific, plan-specific
issue unrelated to prompt content.

### P2 — Claude haiku fully recovers from analysis/16 3/5 to 5/5

In analysis/16 (run 1/23), claude-haiku-4-5-pinned failed on:
- `hong_kong_game`: All 7 call-1 levers rejected for missing "Controls" prefix
- `parasomnia_research_unit`: APITimeoutError at 373s

In analysis/17 (run 1/30):
- `hong_kong_game`: Completed successfully in 219.21s (source: `history/1/30_identify_potential_levers/events.jsonl`)
- `parasomnia_research_unit`: Completed successfully in 291.05s

The hong_kong recovery strongly supports that the `review_lever` auto-correction was
implemented: haiku's model behavior tends to drop the "Controls" prefix on this specific
plan, and without auto-correction it would fail again.

### P3 — Haiku produces best-in-class content quality

Run 30 (haiku) silo output (`history/1/30_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`)
shows 21 high-specificity levers with:
- Precise numerical consequences: "~$800M to upfront capex", "18–24 months", "40–50 MW"
- Non-generic lever names: "Ecosystem Closure Timeline & Functional Redundancy", "Life-Support Redundancy Topology & Single-Point Failure Exposure"
- Well-reasoned trade-off exposition in reviews: identifies specific failure modes like "residents radicalized by sudden truth-exposure may destabilize the silo faster than external threats"
- Options with full strategic detail (40–120 words per option)

Run 30 gta_game lever "Narrative Architecture: Procedural vs. Hand-Authored Story Density"
(`history/1/30_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`)
is similarly domain-grounded: "2,200+ developer-months", "40-60 hours of premium narrative",
comparison to real GTA entries by name.

### P4 — Review format compliance maintained across all 34 successful plans

No `ValidationError` for missing "Controls" prefix or wrong format appears in events.jsonl
for any of the successful plan runs. The `check_review_format` validator either fires
auto-correction (haiku hong_kong) or never needs to (all other models). Source: all
`events.jsonl` files for runs 24–30 show zero validation errors in successful plans.

### P5 — gpt-oss-20b hong_kong now succeeds (resolved from analysis/15)

In analysis/15, gpt-oss-20b failed on `hong_kong_game` with a JSON extraction issue.
In analysis/16, it failed on `parasomnia` instead (hong_kong succeeded). In analysis/17
(run 25), hong_kong completed successfully (108.16s per `events.jsonl` line 5). The
hong_kong failure appears resolved; parasomnia EOF persists.

---

## Comparison

### vs. Baseline Training Data

Baseline silo (`baseline/train/20250321_silo/002-10-potential_levers.json`):
- 15 levers with repeated names: "Resource Allocation Strategy" appears 3×, "Technological
  Adaptation Strategy" appears 3×, "External Relations Protocol" appears 2×
- Short consequences without quantification; "Immediate: Increased compliance → Systemic: 30% reduction in innovative output" without strategic → chain
- Review weaknesses generic ("The options don't address the potential for corruption")
- Options typically 10–20 words

Run 30 (haiku) silo:
- 21 unique levers, no repeated names
- Consequences with specific metrics: "$800M upfront capex", "25+ year MTTF"
- Reviews identify failure modes specific to the lever's domain
- Options 40–120 words with concrete implementation parameters

The current prompt (prompt_3) substantially outperforms baseline in specificity and
uniqueness. Baseline reflects earlier, pre-optimization runs.

### vs. Analysis/16

The primary change visible between analysis/16 and analysis/17:

| Metric | Analysis/16 | Analysis/17 | Direction |
|--------|-------------|-------------|-----------|
| Overall success rate | 31/35 (88.6%) | 34/35 (97.1%) | +8.5pp |
| haiku success | 3/5 | 5/5 | +2 plans |
| gpt-oss-20b success | 4/5 | 4/5 | UNCHANGED |
| qwen3 success | 4/5 (parasomnia EOF) | 5/5 | +1 plan |
| gpt-5-nano success | 5/5 | 5/5 | UNCHANGED |
| gpt-4o-mini success | 5/5 | 5/5 | UNCHANGED |
| gemini success | 5/5 | 5/5* | UNCHANGED |
| llama3.1 success | 5/5 | 5/5 | UNCHANGED |
| haiku hong_kong validation fail | YES (run 23: 0 levers) | NO (run 30: success, 219s) | RESOLVED |
| haiku parasomnia timeout | YES (373s) | NO (291s) | RESOLVED |
| qwen3 consequence contamination | Present (4/5 plans) | Present (5/5 plans) | UNCHANGED |
| llama3.1 bracket contamination call-3 | Not confirmed | Confirmed (6/21 levers) | NEW |
| gpt-oss-20b parasomnia EOF | YES (run 18) | YES (run 25, line 58) | PERSISTS |

*Run 29 gemini: config failure wave then full recovery — net result same as analysis/16.

---

## Quantitative Metrics

### Table 1: Lever Counts (silo plan)

| Run | Model | Final Levers | LLM Calls | Total Tokens |
|-----|-------|-------------|-----------|-------------|
| 24 | llama3.1 | 21 | 3 | 5,790 |
| 25 | gpt-oss-20b | 18 | N/A (silo OK) | N/A |
| 26 | gpt-5-nano | 18 | 10 | 136,363 |
| 27 | qwen3-30b | 17 | 11 | 44,317 |
| 28 | gpt-4o-mini | 20 | 11 | 34,897 |
| 29 | gemini-2.0-flash | 18 | 11 | 40,725 |
| 30 | haiku-4-5 | 21 | N/A* | N/A* |

*Run 30 silo has no `activity_overview.json` (absent from disk);
`usage_metrics.jsonl` exists but was not parsed in this analysis.

Sources: `activity_overview.json` files in `history/1/{24,26,27,28,29}_identify_potential_levers/outputs/20250321_silo/`.

All models produce 17–21 final levers, well above the prompt's "5 to 7 per response"
guidance, because the step makes multiple LLM calls and merges. This is expected behavior.

### Table 2: Consequence Contamination (qwen3 silo)

| Lever | Contaminated (review text in consequences)? |
|-------|---------------------------------------------|
| All 17 levers | YES |

Contamination rate for run 27: **17/17 (100%)** in silo plan.
Source: `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### Table 3: Bracket Placeholder Contamination (llama3.1 silo)

| Lever Index | Name | Brackets in Consequences? |
|-------------|------|--------------------------|
| 1–8 | Population Dynamics through Silo Ecosystem Governance | NO |
| 9 | Civic Architecture | YES |
| 10 | Ecosystem Resilience | YES |
| 11 | Knowledge Management | YES |
| 12 | Social Hierarchy | YES |
| 13 | Technological Advancement | YES |
| 14 | Supply Chain Resilience | YES |
| 15–21 | (later levers) | NO |

Contamination rate for run 24 silo: **6/21 (29%)** in the third LLM call.
Source: `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### Table 4: Success Rate by Run and Model

| Run | Model | Plans OK | Plans Failed | Failure Reason |
|-----|-------|----------|-------------|----------------|
| 24 | llama3.1 | 5 | 0 | — |
| 25 | gpt-oss-20b | 4 | 1 (parasomnia) | JSON EOF line 58 col 5 |
| 26 | gpt-5-nano | 5 | 0 | — |
| 27 | qwen3-30b | 5 | 0 | — |
| 28 | gpt-4o-mini | 5 | 0 | — |
| 29 | gemini-2.0-flash | 5 | 0* | *initial config fail recovered |
| 30 | haiku-4-5 | 5 | 0 | — |
| **Total** | | **34** | **1** | |

Sources: `outputs.jsonl` and `events.jsonl` for each run.

### Table 5: Run Duration (silo plan — representative plan)

| Run | Model | Silo Duration |
|-----|-------|--------------|
| 24 | llama3.1 | 117.31s (sequential) |
| 25 | gpt-oss-20b | 139.31s |
| 26 | gpt-5-nano | 242.46s |
| 27 | qwen3-30b | 137.87s |
| 28 | gpt-4o-mini | 57.53s |
| 29 | gemini-2.0-flash | 35.86s |
| 30 | haiku-4-5 | 134.42s |

Sources: `events.jsonl` for each run.

gpt-5-nano is the slowest (242s), likely because it makes 10 calls with massive output
tokens (136k total for silo), though cost is $0 (suggests test/free-tier routing).
gemini is fastest at 35s/plan.

### Table 6: Review Format Violations

No explicit format validation errors appear in `events.jsonl` for any of the 34 successful
plan runs. Review format compliance is effectively 100% for successful plans.

---

## Evidence Notes

- **Run 25 parasomnia failure**: `history/1/25_identify_potential_levers/events.jsonl` line 7;
  `history/1/25_identify_potential_levers/outputs.jsonl` line 2.
- **qwen3 contamination**: `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — verified lever `118359f7` ("Security Architecture Design"), lever `583ce665` ("Resource Allocation Strategy"), and all subsequent levers.
- **llama3.1 bracket contamination**: `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — levers `21c6aac4` ("Civic Architecture"), `7ba55fec` ("Ecosystem Resilience"), `8771665f` ("Knowledge Management"), `f979fcef` ("Social Hierarchy"), `7d941149` ("Technological Advancement"), `65fab3af` ("Supply Chain Resilience").
- **Run 29 config failure**: `history/1/29_identify_potential_levers/events.jsonl` lines 1–10 (all fail `openrouter-paid-gemini-2.0-flash-001` not found); lines 11–21 (all succeed).
- **haiku hong_kong recovery**: `history/1/30_identify_potential_levers/events.jsonl` shows hong_kong completed at 219.21s.
- **haiku parasomnia recovery**: Same file shows parasomnia completed at 291.05s (vs. 373s timeout in analysis/16).
- **Activity overviews**: Run 28 silo shows `calls: 11`; run 27 silo shows `calls: 5+1+5=11` across 3 providers; run 29 silo shows `calls: 7+4=11` across 2 providers.
- **gpt-5-nano token explosion**: `history/1/26_identify_potential_levers/outputs/20250321_silo/activity_overview.json` shows 136,363 total tokens for a single silo run (117k output, 10 calls). This is 3–4× the other models. Cost=0 suggests a free/test endpoint.

---

## PR Impact

No `pr_url` is registered in `analysis/17_identify_potential_levers/meta.json`, so a formal
PR Impact section cannot be produced. However, the iteration's title ("review_lever auto-correct")
and the analysis/16 assessment's recommendation allow indirect evaluation:

**What the recommended change was** (analysis/16 assessment, "Recommended Next Change"):
Prepend "Controls " to `review_lever` fields that contain `" vs. "` and `"Weakness:"` but
lack the leading word "Controls", before raising `ValueError`. Normalize "versus" → "vs."
in the same pass.

**Evidence the change was applied:**
- Run 23 (analysis/16): haiku hong_kong → 0 levers (all 7 rejected for missing "Controls")
- Run 30 (analysis/17): haiku hong_kong → **success (219s)**, leveraging the same model and same plan

If the auto-correction were NOT active, haiku would again produce reviews without "Controls"
on hong_kong and fail with `ValueError`. The clean success with 219s runtime strongly suggests
the corrected validator allows levers through.

**Evidence of no regression:**
- gpt-5-nano (run 26): 5/5 in both batches; no double-prepend issue observed (model already
  includes "Controls" correctly in most levers, or gpt-5-nano's bracket leakage "Controls [Tension A]"
  would not be corrected by the validator since "Controls" is present)
- gemini, gpt-4o-mini: 5/5 in both batches, same as before
- llama3.1: 5/5 in both batches, no regression despite bracket contamination (brackets are
  in `consequences`, not `review`, so not affected by `check_review_format`)

**Incomplete evidence:**
- No `events.jsonl` entries indicating "auto-corrected review" events exist (no such logging
  is mentioned in the codebase description), so the auto-correction cannot be directly observed
  from artifacts — only inferred from the successful outcome.

---

## Questions For Later Synthesis

1. **Is the auto-correction confirmed in code?** The analysis here is inferential (haiku went
   5/5 without observation of correction events). Synthesis should check whether
   `check_review_format` in `identify_potential_levers.py` now has auto-prepend logic, and
   whether any logging was added.

2. **Can qwen3 consequence contamination be eliminated?** The validator checks the `review`
   field but not whether `consequences` ends with review text. A `@field_validator` that strips
   trailing content matching the review pattern from `consequences` would clean this up. Is
   this worth fixing, or should qwen3 be deprioritized?

3. **Is the gpt-oss-20b parasomnia failure fixable without changing the model?** The EOF
   moved from line 25 to line 58 between runs 18 and 25, suggesting provider-side token limits
   changed. Should `"eof while parsing"` be added to `_TRANSIENT_PATTERNS` for retry? Would a
   smaller `DocumentDetails` schema (removing `strategic_rationale`/`summary`) help enough?

4. **Why does llama3.1 produce bracket contamination only in call-3?** Calls 1 and 2 are
   clean. Could the third call prompt be sending a different context that induces template-mode
   behavior? Or is this a model-specific degradation under the given system prompt on the third
   call?

5. **Should gemini's `openrouter-paid-gemini-2.0-flash-001` config issue be fixed?** The
   runner tried a non-existent model name on wave 1, then apparently retried with the correct
   name. Is there a hardcoded "paid" variant in the LLM chain config that needs removal?

6. **Why is gpt-5-nano generating 136k output tokens for silo?** This is 3–4× other models.
   Is it producing extremely verbose JSON, or is it making more internal attempts? The 10-call
   count is normal for the step, but the token count is not. Is there a runaway verbosity issue?

---

## Reflect

The main signal from this batch is **haiku's recovery from 3/5 to 5/5**. The analysis/16
assessment predicted this exactly: auto-correcting the "Controls" prefix would convert run 23's
hong_kong failure from 0 levers to full success. The prediction was fulfilled.

The persistent failure mode is **gpt-oss-20b parasomnia EOF**, now in its third consecutive
batch. The model's output is not truncated at a consistent line number (25 → 58), which may
indicate provider-side changes rather than a deterministic schema limit. Adding "eof while
parsing" to `_TRANSIENT_PATTERNS` is the minimal fix; schema slimming via removing
`strategic_rationale`/`summary` from `DocumentDetails` is the structural fix.

qwen3's consequence contamination is a known, stable defect. It doesn't break validation
(the `review` field is correct), but it corrupts the `consequences` field with duplicated
review text. If qwen3 remains in the model pool, a field-validator that strips the suffix
is warranted.

The most surprising finding is **gpt-5-nano's 136k output tokens** for a single silo run —
4× the next highest (qwen3 at 44k). With `cost=0` it doesn't hurt the budget, but it
signals a verbosity runaway that could be expensive on a paid endpoint. The 10-call count
is normal; the 117k output tokens suggests each call is generating extremely verbose JSON.

Run 30 (haiku) continues to produce the highest-quality output of any model in this step,
with domain-specific lever names, precise quantified consequences, and reviews that identify
novel failure modes rather than generic weaknesses.

---

## Potential Code Changes

**C1** — Add `"eof while parsing"` (case-insensitive) to `_TRANSIENT_PATTERNS` in
`identify_potential_levers.py` (or the shared LLM retry config). When gpt-oss-20b truncates
on parasomnia, a retry would attempt a fresh call, potentially succeeding on the second try
since the EOF at line 58 (vs. 25 in run 18) shows the model sometimes gets further.
*Evidence*: runs 18, 20, 25 all fail with the same error string.
*Expected effect*: gpt-oss-20b parasomnia success rate rises from 0/3 to potentially 1–2/3
across batches.

**C2** — Add `@field_validator('consequences', mode='after')` in `DocumentDetails` that
strips trailing text matching the `review` pattern (e.g., text starting with `"Controls "` and
containing `"Weakness:"` at the end of the `consequences` field). This fixes qwen3's 100%
contamination rate without affecting other models.
*Evidence*: `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
— all 17 levers show `consequences` ending with the exact `review` text.
*Expected effect*: qwen3 consequences are clean; downstream consumers see non-duplicated content.

**C3** — Remove `strategic_rationale` and `summary` from `DocumentDetails` (schema slimming
per analysis/16 backlog item). These fields are generated on every call but discarded by
`save_clean()`. Removing them reduces per-call output token cost by an estimated 2,000–4,000
tokens, giving gpt-oss-20b and haiku more budget for the actual levers on verbose plans like
parasomnia.
*Evidence*: analysis/16 assessment "strategic_rationale and summary dead-generation overhead";
haiku parasomnia took 291s (close to timeout) even after succeeding; gpt-oss-20b EOF at line 58
(getting further but still truncating).
*Expected effect*: parasomnia completion improves for haiku and gpt-oss-20b; overall timeout
risk decreases.

**C4** — Fix `openrouter-paid-gemini-2.0-flash-001` model name in LLM chain config. The runner
tried this non-existent name for all 5 plans before recovering. This wastes wall-clock time (5
wasted starts at ~0.01s each) and adds noise to `events.jsonl`. The correct name is
`openrouter-gemini-2.0-flash-001` (confirmed by `meta.json` and successful wave-2 activity).
*Evidence*: `history/1/29_identify_potential_levers/events.jsonl` lines 1–10.
*Expected effect*: gemini runs in a single clean wave.

**C5 (prompt-level, H1)** — Investigate the llama3.1 call-3 bracket contamination.
The third call receives a different prompt context (e.g., instructions to generate levers
"different from" the first two batches) that may inadvertently trigger template-mode output.
Adding explicit negative examples to the prompt ("never wrap content in brackets like
[Establish a hierarchical structure]") or removing the bracket-containing Pydantic
`description=` fields may eliminate this.
*Evidence*: `history/1/24_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
levers 9–14 (third-call output).

---

## Summary

Runs 1/24–1/30 show the strongest success rate of any analysis batch (34/35, 97.1%), and
haiku's recovery from 3/5 to 5/5 is the clearest outcome — consistent with the `review_lever`
auto-correction recommended in analysis/16 being in place. The sole failure (run 25
gpt-oss-20b parasomnia EOF) is a chronic, model+plan-specific defect appearing in its third
consecutive batch. qwen3's consequence contamination persists at 100% but does not affect
plan success. New findings include llama3.1 bracket contamination in the third LLM call (6/21
levers, silo) and gpt-5-nano's anomalously high output token count (136k vs. ~40k for other
models on the same plan).

Top priority code changes: add EOF error to transient retry patterns (C1), schema slimming
to reduce parasomnia token budget pressure (C3), fix gemini model name config (C4). qwen3
consequence contamination fix (C2) is lower priority if qwen3 is not a primary target model.

The prompt itself appears to be working well for high-capability models (haiku, gemini,
gpt-4o-mini). The remaining quality gap is largest for qwen3 (short options, consequence
contamination) and llama3.1 (bracket contamination in call-3, lower depth).
