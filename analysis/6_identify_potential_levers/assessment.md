# Assessment: Iteration 5 — Consequences & Review Field Description Refinements (PR #274)

## Issue Resolution

**What was changed (inferred from evidence, no pr_title in meta.json):**

The after batch (runs 46–52) reflects changes recommended by synthesis/5 Direction 1 + Direction 2, implemented as PR #274 ("schema-field-descriptions"):

1. **Consequences field description revised**: length target reduced from "150–300 words" to approximately "3–5 sentences (~60–120 words)"; explicit trade-off requirement added; contamination prohibition added ("Do NOT include 'Controls … vs.', 'Weakness:', or other review/critique text in this field").
2. **`review_lever` field description strengthened**: both "Controls [A] vs. [B]." and "Weakness: …" now specified as mandatory per-response components.

**Is the primary issue resolved?**

Yes — the haiku timeout on `20260311_parasomnia_research_unit` is confirmed resolved:

- Before (run 45): `APITimeoutError` at 432.62 s; parasomnia fails.
- After (run 52): `{"status": "ok", "duration_seconds": 223.84}` — well within the threshold.

The consequence text for run 52 averages ~550 chars/lever (down from ~1,321 chars in run 45), directly attributable to the length-target reduction.

**Is the review_lever dual-component issue resolved?**

Yes for llama3.1. Run 40 had 15/15 levers with alternating Controls-only or Weakness-only reviews (never both). Run 47 produces dual-component reviews for every lever — verified in sample:

```
history/0/47_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11
"review": "Controls Complexity vs. Efficiency. Weakness: The options fail to consider
the psychological impact on residents living in a highly structured environment."
```

**Residual symptoms:**

1. **qwen3-30b contamination unresolved.** The prohibition is now in the source code (lines 38–39 confirmed by both code-review agents), but run 50 still shows 100% contamination in call-1 levers — worse than run 43's 45/75 Controls + 60/75 Weakness. The model ignores the schema field description. Evidence: `history/0/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` (review text verbatim at end of `consequences` and repeated in `review` field).

2. **llama3.1 option quality regressed further.** Average option length dropped from ~91 chars (run 40) to ~58 chars (run 47), with label-style options ("Utilitarian Grid", "Hierarchical Stack", "Radical Spheroid") averaging ~18 chars on the silo plan. The more demanding consequence format may be consuming llama3.1's effective token budget, leaving inadequate capacity for option descriptions.

3. **Schema enforcement still absent.** `levers` is still an unconstrained `list[Lever]` (no `min_length`/`max_length`); `summary` is still `Optional[str] = None`. Run 52 produced one 6-lever response (hong_kong_game), yielding a 16-lever merged artifact — the same overflow bug that affected prior batches.

---

## Quality Comparison

Models present in **both** batches: nemotron (39→46), llama3.1 (40→47), gpt-oss-20b (41→48), gpt-5-nano (42→49), qwen3-30b (43→50), gpt-4o-mini (44→51), haiku (45→52).

| Metric | Before (runs 39–45) | After (runs 46–52) | Verdict |
|--------|---------------------|---------------------|---------|
| **Overall success rate** | 28/35 = 80.0% | 30/35 = 85.7% | IMPROVED |
| **Nemotron success rate** | 0/5 (run 39) | 0/5 (run 46) | UNCHANGED |
| **llama3.1 success rate** | 5/5 (run 40) | 5/5 (run 47) | UNCHANGED |
| **gpt-oss-20b success rate** | 4/5 (run 41; parasomnia JSON fail) | 5/5 (run 48) | IMPROVED |
| **gpt-5-nano success rate** | 5/5 (run 42) | 5/5 (run 49) | UNCHANGED |
| **qwen3-30b success rate** | 5/5 (run 43) | 5/5 (run 50) | UNCHANGED |
| **gpt-4o-mini success rate** | 5/5 (run 44) | 5/5 (run 51) | UNCHANGED |
| **haiku success rate** | 4/5 (run 45; parasomnia 432 s timeout) | 5/5 (run 52; parasomnia 223 s) | **IMPROVED** |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 1 (run 40, sovereign_identity: 2-option lever) | 0 | IMPROVED |
| **Lever count violations (>15 merged)** | 0 (runs 39–45) | 1 (run 52, hong_kong_game: 16 levers) | REGRESSED |
| **Lever name uniqueness** | 15/15 per plan (all runs) | 15/15 per plan (all runs; run 52 = 16/16 due to 6-lever response) | UNCHANGED |
| **Template / placeholder leakage** | 0 | 0 | UNCHANGED |
| **Review format compliance — llama3.1** | 17/75 missing Controls, 13/75 missing Weakness (run 40, alternating pattern) | 0/75 violations (run 47; both components in every review) | **IMPROVED** |
| **Review format compliance — other models** | 0 violations (runs 41–45) | 0 violations (runs 48–52) | UNCHANGED |
| **Consequence chain I→S→S — all models** | Present in all successful runs | Present in all successful runs | UNCHANGED |
| **Measurable outcome in consequences — haiku** | Present, ~1,321 chars avg (run 45) | Present, ~550 chars avg (run 52) | **IMPROVED (calibrated)** |
| **Measurable outcome in consequences — llama3.1** | Absent (60/75 lacking indicators, run 40) | Absent (75/75 lacking numeric, run 47) | UNCHANGED |
| **Measurable outcome in consequences — gpt-5-nano** | Present, ~386 chars avg (run 42) | Present, ~421 chars avg (run 49) | UNCHANGED |
| **Review-in-consequences contamination — qwen3** | 45/75 Controls, 60/75 Weakness leaked (run 43) | 75/75 Controls, 75/75 Weakness leaked (run 50) | PERSISTS (worsened in rate) |
| **Content depth — avg option chars — haiku** | ~355 chars (run 45) | ~361 chars (run 52) | UNCHANGED |
| **Content depth — avg option chars — llama3.1** | ~91 chars (run 40) | ~58 chars (run 47) | **REGRESSED** |
| **Content depth — avg option chars — gpt-5-nano** | ~121 chars (run 42) | ~117 chars (run 49) | UNCHANGED |
| **Content depth — avg option chars — gpt-4o-mini** | ~131 chars (run 44) | ~124 chars (run 51) | UNCHANGED |
| **strategic_rationale — haiku** | null (run 45) | populated (run 52) | **IMPROVED** |
| **Null summaries — llama3.1** | ~15/15 per plan null (run 40) | 14 nulls across all plans (run 47) | UNCHANGED |
| **Null summaries — gpt-oss-20b** | 6 null summaries (run 41) | 10 null summaries (run 48) | REGRESSED |
| **Null summaries — gpt-4o-mini** | 6 null summaries (run 44) | 4 null summaries (run 51) | SLIGHTLY IMPROVED |
| **Null summaries — gpt-5-nano** | 0 null summaries (run 42) | 0 null summaries (run 49) | UNCHANGED |
| **Cross-call name duplication** | 0 (all runs; name-exclusion loop works) | 0 (all runs) | UNCHANGED |

**Source citations:** insight_claude.md and insight_codex.md for both analysis/5 and analysis/6; verified directly from `history/0/47,50,52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `outputs.jsonl` files.

---

## New Issues

### N1 — Run 52 (haiku) produces 16 levers for hong_kong_game
One raw response returns 6 levers; the code flatly extends the list with no count check. The merged file `history/0/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` has 16 entries. Schema enforcement (`min_length=5, max_length=5` on `DocumentDetails.levers`) was recommended in synthesis/5 Direction 4 and synthesis/6 Direction 1 but has not been applied. This is a pre-existing code gap now newly triggered by haiku.

### N2 — gpt-5-nano (run 49) produces extreme output volume
33,741 output tokens for one silo plan (three calls: 12,794 + 8,925 + 12,022). Duration ~220 s/plan. At this rate, a harder or longer plan may hit the API timeout analogous to run 45 haiku. The quality is high but the volume is unsustainable. No per-call token cap exists in the runner.

### N3 — qwen3-30b contamination rate worsened despite prohibition in source
Run 43 (before): ~45/75 levers with Controls leakage, ~60/75 with Weakness leakage. Run 50 (after): 75/75 (100%) on both. The contamination prohibition is confirmed present in `identify_potential_levers.py:38–39` but qwen3-30b ignores it. Additionally, run 50 reproduces 2+ levers verbatim from the baseline (`Surveillance Architecture Strategy`, `Energy Generation Strategy` — same options, same structure), suggesting low effective randomness and baseline self-reproduction.

### N4 — Baseline is contaminated (surfaced clearly this batch)
Both code-review agents and insight_claude confirm the `baseline/train/` consequences fields end with "Controls X vs. Y. Weakness: …" — the same contamination pattern as qwen3-30b. The baseline was likely generated by qwen3-30b. This makes baseline-similarity scoring an unreliable quality signal (contaminated outputs score higher on similarity).

### N5 — llama3.1 option quality worsening across three consecutive batches
Option length trajectory: ~88 chars (batch 4, run 33) → ~91 chars (batch 5, run 40 codex avg) → ~58 chars (batch 6, run 47 codex avg), with silo-plan sample averaging ~18 chars in run 47. This is a monotonic regression. The qualitative instruction ("not a label") has not been effective; a quantitative minimum is needed.

---

## Verdict

**YES**: The PR resolves its two primary targets — the haiku parasomnia timeout (432 s → 224 s, 4/5 → 5/5 plans) and the llama3.1 review format alternation (15/15 violations → 0), while improving overall batch success rate from 80% to 85.7%. The consequence length calibration is confirmed correct by the haiku evidence. The qwen3 contamination persists but is now clearly a model-enforcement problem (prohibition present but ignored), not a missing-instruction problem, which correctly redirects the fix toward code-level validation rather than further prompt changes.

---

## Recommendations

### Should the next iteration follow the "after" synthesis recommendation?

**Yes — follow synthesis/6 Direction 1 first (schema contract enforcement).** Specifically:

- Add `min_length=5, max_length=5` to `DocumentDetails.levers` (eliminates run-52-style 16-lever artifacts at parse time).
- Change `summary: Optional[str] = None` to `summary: str` (eliminates null-summary regressions in runs 47, 48, 51).

These are the highest-confidence, lowest-effort changes in the backlog: two targeted field changes that produce hard parse failures instead of silent quality degradation.

**After Direction 1, do synthesis/6 Direction 2 (multi-call chat structure).** Calls 2 and 3 currently replace original plan documents with only a name-exclusion message while inheriting prior assistant JSON. This is the root cause of qwen3 contamination carry-over and gpt-5-nano verbosity amplification (confirmed in source at `identify_potential_levers.py:196–209`). Restructuring to fresh-context calls (system + original plan + name exclusion, no prior assistant JSON) addresses the issue that field-description fixes cannot.

**Direction 3 (post-generation contamination validator) should follow Direction 2** as a redundant safety net.

### Issues from before that are now resolved:

- **Haiku parasomnia timeout** — resolved. Remove from active backlog; add haiku to reliable model set.
- **llama3.1 alternating review format** — resolved. Review dual-component compliance is now 0 violations for llama3.1.
- **`consequences` length miscalibration ("150–300 words")** — resolved. New target produces ~550 chars/lever for haiku (was ~1,321 chars).
- **Option count violations** — reduced to 0 (was 1 in run 40). The "Exactly 3 options" field description is working for all tested models.

### New issues to add to the backlog:

1. **[HIGH] Enforce schema contract: lever count + required summary** — `min_length=5, max_length=5` on `levers`; `summary: str` (not Optional). Synthesis/6 Direction 1. Directly prevents the run-52 16-lever artifact and null-summary regressions.

2. **[HIGH] Fix multi-call chat structure** — on calls 2 and 3, include original plan documents + system prompt + name exclusion list, without prior assistant JSON. Synthesis/6 Direction 2. Root cause of qwen3 contamination propagation and gpt-5-nano verbosity drift.

3. **[MEDIUM] Add post-generation contamination validator** — check `lever.consequences` for `"Controls"` + `"vs."` or `"Weakness:"` before writing to file; flag or reject. Required because qwen3-30b ignores the field-description prohibition entirely. Synthesis/6 Direction 3.

4. **[MEDIUM] Add quantitative minimum to options description** — "Each option must be at least 12–15 words describing a concrete approach, not a label or title." Addresses llama3.1 option regression (~18 chars → needs ~100+ chars). May require capacity testing since llama3.1 appears to trade consequence depth for option length.

5. **[MEDIUM] Per-call token cap for gpt-5-nano** — 33,741 output tokens/plan is a timeout risk on harder plans. Consider `max_tokens=3,000–4,000` per call.

6. **[LOW] Skip nemotron-3-nano-30b-a3b** — 5 consecutive full-batch failures (runs 24, 25, 32, 39, 46); ~8 minutes wasted per batch. Add to a configurable skip list.

7. **[LOW] Fix telemetry race condition** — move `set_usage_metrics_path` calls inside `_file_lock` in `runner.py:106,140`. Correctness fix; does not affect output quality.

8. **[LOW] Investigate baseline contamination** — the baseline `consequences` fields show the qwen3-30b review-leakage pattern. If the baseline is used as a quality reference, contaminated fields should be stripped or the baseline regenerated with a clean model. This affects evaluation reliability.
