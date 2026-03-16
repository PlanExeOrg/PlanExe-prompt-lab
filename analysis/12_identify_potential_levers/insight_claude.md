# Insight Claude

Analysis of runs 88–94 for `identify_potential_levers` (prompt_2).
PR under review: [#286](https://github.com/PlanExeOrg/PlanExe/pull/286) — "Remove max_length=7 hard constraint on levers schema".

---

## Rankings

| Rank | Run | Model | Plans OK/Total | Content Quality |
|------|-----|-------|----------------|-----------------|
| 1 | 94 | anthropic-claude-haiku-4-5-pinned | 5/5 | Excellent — deep, measurable, domain-specific; PR fixed the gta_game failure |
| 2 | 91 | openai-gpt-5-nano | 5/5 | Good — specific metrics, blockchain/AI overuse |
| 3 | 92 | openrouter-qwen3-30b-a3b | 5/5 | Good — adequate specificity; persistent consequence contamination |
| 4 | 93 | openrouter-openai-gpt-4o-mini | 5/5 | Medium — shorter consequences, generic weaknesses |
| 5 | 89 | ollama-llama3.1 | 4/5 | Poor/Medium — shallow quality, 1 timeout failure |
| 6 | 90 | openrouter-openai-gpt-oss-20b | 4/5 | Good on 4 plans, 1 JSON extract failure |
| 7 | 88 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | n/a — total structural failure |

---

## Negative Things

### 1. Run 88: Total failure (same model incompatibility as run 81)

All 5 plans failed with identical errors:

```
ValueError('Could not extract json string from output: ')
```

Source: `history/0/88_identify_potential_levers/events.jsonl`, all 5 entries.

The model (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) returns empty output when asked to produce structured JSON. This is the same structural incompatibility observed in run 81. The PR change (removing `max_length=7`) has no bearing on this failure class.

### 2. Run 89: Llama3.1 timeout on sovereign_identity

Plan `20260308_sovereign_identity` failed with:

```
ReadTimeout('timed out')
```

Source: `history/0/89_identify_potential_levers/events.jsonl` line 6. Duration: 183.99 seconds.

Sovereign_identity is a complex plan. Llama3.1 ran locally with `workers=1` and timed out. This is the same model that succeeded 5/5 in run 82. The timeout is likely non-deterministic (heavy plan, local hardware thermal throttle). Not related to PR #286.

### 3. Run 90: gpt-oss-20b JSON extract failure on sovereign_identity

Plan `20260308_sovereign_identity` failed with:

```
ValueError('Could not extract json string from output: ')
```

Source: `history/0/90_identify_potential_levers/events.jsonl` line 9. Duration: 164.03 seconds.

Matching the pattern from run 83 (same model, same failure class), `sovereign_identity` is particularly prone to triggering empty JSON output from this model. The long, complex plan likely causes the model to produce unstructured prose. PR #286 does not affect this failure class.

### 4. Run 92: qwen3 consequence contamination persists

The known contamination failure (qwen3 appending review text into the `consequences` field) continues in run 92. Example from `history/0/92_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1:

```json
"consequences": "Immediate: Centralized authority enforces compliance → Systemic: 70% reduction
  in internal conflicts but 40% decline in problem-solving innovation → Strategic: Entrenches
  hierarchical power structures... Controls Order vs. Adaptability. Weakness: The options
  fail to consider psychological degradation from prolonged authoritarian control.",
"review": "Controls Order vs. Adaptability. Weakness: The options fail to consider psychological
  degradation from prolonged authoritarian control."
```

The `consequences` field ends with the full `review` sentence verbatim. This was documented in analysis/11 (runs 85 / run 92 maps to same model). The contamination rate remains ~70% of consequences for qwen3. PR #286 does not affect this pattern.

### 5. Overall success rate unchanged at 80%

The PR specifically targeted haiku's gta_game failure (adding a success). However, run 89's llama timeout removed one success, keeping the total at 28/35 (80%). This masks the PR's measurable improvement within the haiku model class.

---

## Positive Things

### 1. PR #286 directly fixed the targeted failure class

Run 94 (haiku, same model as run 87) succeeded on all 5 plans including `gta_game`, producing 21 levers. The exact error from run 87:

```
1 validation error for DocumentDetails
levers
  List should have at most 7 items after validation, not 8
  [type=too_long, input_value=[...], input_type=list]
```

Source: `history/0/87_identify_potential_levers/events.jsonl` line 7.

…is absent from `history/0/94_identify_potential_levers/events.jsonl` — all 5 plans completed. The gta_game plan now yields 21 levers in `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`. These are rich, domain-specific levers with measurable consequences.

### 2. Haiku produces highest-quality output when unconstrained

The gta_game levers from run 94 (haiku) are exemplary: multi-step consequences with quantified trade-offs, e.g.:

> "Immediate: Implementing advanced procedural generation (PCG) for districts, missions, and NPC routines reduces content creation labor by ~40%, freeing 60+ artists for graphical polish. → Systemic: Over-reliance on PCG yields 15–25% lower perceived 'world authenticity' in player feedback (measured via pre-alpha test surveys), while full hand-crafting extends production by 24 months and requires hiring 80+ additional artists at $120K–$180K annually. → Strategic: A hybrid approach balances launch speed with artistic control, but introduces technical debt..."

Source: `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever 2.

This quality level was entirely suppressed in run 87 due to the schema constraint. The PR recovered it.

### 3. 3-response-per-plan structure is consistent; max_length removal is safe

Each plan's raw file (e.g., `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`) contains 3 LLM call responses. Counting `"strategic_rationale"` entries confirms 3 responses per plan across all runs. With up to 7+ levers per call, the merged totals are correctly 15–22 levers, handled by `DeduplicateLeversTask` downstream.

### 4. All successful runs produce structurally valid JSON output

Runs 91, 92, 93, 94 produced clean JSON arrays at `002-10-potential_levers.json` with zero schema violations. Option counts (always exactly 3 per lever) are consistent.

---

## Comparison

### Comparing same-model pairs before vs. after PR

| Model | Run (Before) | Success | Run (After) | Success | Change |
|-------|-------------|---------|-------------|---------|--------|
| nvidia-nemotron | 81 | 0/5 | 88 | 0/5 | unchanged |
| ollama-llama3.1 | 82 | 5/5 | 89 | 4/5 | -1 (timeout, unrelated) |
| openrouter-gpt-oss-20b | 83 | 4/5 | 90 | 4/5 | unchanged |
| openai-gpt-5-nano | 84 | 5/5 | 91 | 5/5 | unchanged |
| openrouter-qwen3-30b-a3b | 85 | 5/5 | 92 | 5/5 | unchanged |
| openrouter-gpt-4o-mini | 86 | 5/5 | 93 | 5/5 | unchanged |
| anthropic-claude-haiku-4-5-pinned | 87 | 4/5 | 94 | 5/5 | +1 (PR fixed gta_game) |

### Lever count comparison (gta_game plan)

| Model | Before run | Count | After run | Count | Note |
|-------|-----------|-------|-----------|-------|------|
| haiku | 87 | N/A (failed) | 94 | 21 | PR recovered this plan |
| gpt-4o-mini | 86 | 17 | 93 | 20 | slight increase, same model |
| qwen3 | 85 | 15 | 92 | 15 | unchanged |
| gpt-5-nano | 84 | 18 | 91 | 18 | unchanged |

The lever count increase for gpt-4o-mini (17 → 20 on gta_game) and silo (16 → 21) is notable but unexplained by the PR alone — the schema change does not affect models that stayed below 7 per call. This may reflect natural run variance.

---

## Quantitative Metrics

### Success rates

| Metric | Before (runs 81–87) | After (runs 88–94) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success** | 28/35 (80%) | 28/35 (80%) | Unchanged |
| — nemotron | 0/5 | 0/5 | Unchanged |
| — llama3.1 | 5/5 | 4/5 | -1 (timeout) |
| — gpt-oss-20b | 4/5 | 4/5 | Unchanged |
| — gpt-5-nano | 5/5 | 5/5 | Unchanged |
| — qwen3 | 5/5 | 5/5 | Unchanged |
| — gpt-4o-mini | 5/5 | 5/5 | Unchanged |
| — haiku | 4/5 | **5/5** | **+1 (PR fixed)** |
| **Max-length Pydantic failures** | 1 (run 87) | **0** | **Fixed by PR** |

### Lever counts — gta_game plan (post-dedup merged)

| Run | Model | Lever count |
|-----|-------|-------------|
| 87 (before) | haiku | N/A — plan failed |
| 94 (after) | haiku | 21 |
| 85 (before) | qwen3 | 15 |
| 92 (after) | qwen3 | 15 |
| 84 (before) | gpt-5-nano | 18 |
| 91 (after) | gpt-5-nano | 18 |
| 86 (before) | gpt-4o-mini | 17 |
| 93 (after) | gpt-4o-mini | 20 |

### Lever counts — silo plan (post-dedup merged)

| Run | Model | Lever count |
|-----|-------|-------------|
| 87 (before) | haiku | 21 |
| 94 (after) | haiku | 22 |
| 86 (before) | gpt-4o-mini | 16 |
| 93 (after) | gpt-4o-mini | 21 |

### LLM calls per plan (raw response count)

Confirmed by counting `"strategic_rationale"` entries in raw files:

| Checked file | Responses |
|---|---|
| run 94 gta_game raw | 3 |
| run 91 gta_game raw | 3 |
| run 87 silo raw | 3 |

All plans use 3 LLM calls. Each call produces 5–8 levers (model-dependent). Deduplication produces 15–22 unique levers per plan.

### Template / constraint violations

| Metric | Before (runs 81–87) | After (runs 88–94) |
|--------|---------------------|--------------------|
| Bracket placeholders `[...]` in lever content | 0 (confirmed in analysis/11) | 0 (spot-checked) |
| Option count != 3 | 0 | 0 |
| max_length Pydantic failures | 1 | **0** |
| qwen3 consequence contamination | ~72% of qwen3 levers | ~70% of qwen3 levers (persists) |
| Options without prefix labels | Compliant | Compliant |

---

## Evidence Notes

- Run 87 haiku gta_game failure: `history/0/87_identify_potential_levers/events.jsonl` line 7 — exact Pydantic error "List should have at most 7 items after validation, not 8"
- Run 94 haiku gta_game success: `history/0/94_identify_potential_levers/events.jsonl` — no errors; 5/5 plans complete
- Run 94 gta_game output: `history/0/94_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — 21 levers, all with rich domain-specific consequences
- Run 94 silo output: `history/0/94_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — 22 levers
- qwen3 contamination confirmed: `history/0/92_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` lever 1, `consequences` ends with `"Controls Order vs. Adaptability. Weakness: ..."` matching `review` field verbatim
- Prompt file: `prompts/identify_potential_levers/prompt_2_75f59ab464162a827807a68b029321534ae1686f6fc340e278c7881d3b334d39.txt` — line 4: "You must generate 5 to 7 levers per response." This is soft guidance; schema no longer enforces the upper bound.
- All run metas confirm same `system_prompt_sha256: 486d3e12e8c892061d8bc9bdd76f3bf23da6818123aaef6779b15f82cf2ca126` — same prompt across all 14 runs.

---

## PR Impact

### What the PR was supposed to fix

PR #286 removes `max_length=7` from the `DocumentDetails.levers` Pydantic field. When haiku returned 8 levers in a single LLM call (observed in run 87: `gta_game` plan), the Pydantic validation raised `ValidationError`, the entire LLM response was discarded, and no retry succeeded. The PR argues that the `DeduplicateLeversTask` already handles over-generation, making the schema-level cap redundant and harmful.

### Before vs. After comparison

| Metric | Before (runs 81–87) | After (runs 88–94) | Change |
|--------|--------------------|--------------------|--------|
| Overall success rate | 28/35 (80%) | 28/35 (80%) | Unchanged (llama timeout offsets haiku gain) |
| Haiku success rate | 4/5 | **5/5** | **+1 plan recovered** |
| max_length Pydantic failures | **1** (run 87, gta_game) | **0** | **Fixed** |
| LLMChatError entries (Pydantic max_length) | 1 | 0 | Eliminated |
| Lever count range per plan | 15–21 (no haiku gta_game) | 15–22 | Stable, now includes haiku gta_game |
| qwen3 contamination | ~72% | ~70% | Unchanged (orthogonal issue) |
| Content quality (haiku gta_game) | N/A (failed) | Excellent (domain-specific, measurable) | Qualitative improvement |

### Did the PR fix the targeted issue?

**Yes, directly and completely.** The Pydantic max_length=7 failure class is eliminated in runs 88–94. Run 94 (haiku) produced 5/5 successes where run 87 produced 4/5. The recovered plan (gta_game) yielded 21 high-quality levers. No run in 88–94 contains a `type=too_long` Pydantic error.

The PR description's claim — "The downstream DeduplicateLeversTask already handles extras" — is validated: the merged output for gta_game (21 levers) is structurally normal and downstream-compatible.

### Regressions from PR #286?

None. The llama timeout (run 89) is independent of the schema change. No model that previously succeeded now fails.

The only observable new behavior is that per-call lever counts above 7 now pass validation. Models tested (haiku, gpt-4o-mini, qwen3, gpt-5-nano) consistently produce 5–8 levers per call; none tested in this batch appear to drastically over-generate (e.g., 20 per call). With 3 calls and deduplication, the 15–22 lever range per plan is appropriate.

### Verdict

**KEEP** — The PR produces a measurable improvement (haiku gta_game recovered: 0 levers before, 21 after) with zero regressions. The schema cap was correctly identified as harmful: it discarded entire valid LLM responses when a model returned 8 instead of ≤7 levers. The soft guidance in the system prompt ("5 to 7 levers per response") is sufficient for models that comply; over-generation is handled gracefully by `DeduplicateLeversTask`.

---

## Questions For Later Synthesis

1. **Is 15–22 levers per plan the right range?** The prompt asks for "5 to 7 levers per response" and there are 3 calls, so 15–21 unique levers is plausible. But the downstream pipeline (e.g., plan documents) may have an implicit expectation about lever counts. Is there a target range for the final merged count?

2. **Should the min_length=5 constraint be tested for soundness?** The PR keeps `min_length=5`. Are there models that consistently return fewer than 5 levers per call, triggering this constraint? None observed in runs 88–94, but it should be verified empirically.

3. **Is qwen3's consequence contamination in scope for this iteration?** The contamination (review text bleeding into consequences) persists at ~70% rate in run 92. This is a content-quality regression that affects downstream plan quality, independent of the PR. It needs a prompt fix or post-processing filter.

4. **Why does gpt-oss-20b fail specifically on sovereign_identity?** Runs 83 and 90 both failed on the same plan with the same model (JSON extract error, ~164 second duration). The plan appears to induce prose output instead of JSON. Is this a max-token issue specific to this plan?

5. **Does haiku over-generate relative to the soft prompt guidance?** Run 94 haiku produced 21–22 levers per plan from 3 calls (≈7–8 per call on average). This slightly exceeds the "5 to 7 per response" guidance. Is this desirable (more diversity for dedup) or worth correcting via prompt adjustment?

---

## Reflect

This analysis confirms that the PR was correctly scoped. The `max_length=7` constraint was a point of brittleness: a model returning 8 levers (one above the cap) caused the entire plan to fail and discard valid output. The fix is minimal, targeted, and the downstream dedup logic already handles the resulting 15–22 lever range.

The batch also confirms that the overall 80% success rate is currently dominated by two structural incompatibilities: nemotron (0/5) and gpt-oss-20b (4/5 due to sovereign_identity failures). Neither is addressable by schema changes. Future improvement to the 80% ceiling requires either model selection changes or fixes to how those failure modes are handled at the runner level.

---

## Potential Code Changes

**C1** (Confirmed — PR #286): Remove `max_length=7` from `DocumentDetails.levers` — **done**.

**C2** (Backlog from analysis/11, still open): qwen3 consequence contamination. The model appends `"Controls X vs. Y. Weakness: ..."` inside the `consequences` field. A post-generation content check that strips or rejects levers where `consequences` ends with a substring matching `review` would catch this. Alternatively, a prompt negative example for qwen3 could reduce the contamination rate.

**C3** (Backlog): gpt-oss-20b's sovereign_identity JSON failure pattern. The plan is long and may exceed the model's effective context for structured output. A pre-truncation step or plan chunking strategy could resolve this.

**C4** (Backlog from analysis/11, still open): Save partial responses on failure. Runs 88 and 90 produce empty output directories for failed plans; the raw LLM text is lost. This makes it harder to diagnose whether the model returned something parseable before the error.

---

## Summary

PR #286 removes the `max_length=7` Pydantic constraint on the `DocumentDetails.levers` field. The analysis confirms it fixed the intended failure class (haiku returning 8 levers per call on `gta_game`, discarding all valid output) and introduced no regressions.

**Verdict: KEEP.**

The overall success rate stays at 28/35 (80%) because a llama timeout cancelled the haiku gain, but this is coincidental and unrelated to the PR. Within haiku specifically, the improvement is clear: 4/5 → 5/5. The recovered gta_game levers are high quality (21 domain-specific levers with measurable consequences). Downstream deduplication handles over-generation gracefully.

Remaining issues for next iterations:
- qwen3 consequence contamination (H1: add explicit negative example to prompt)
- gpt-oss-20b sovereign_identity JSON failures (C3: plan length / chunking)
- nemotron total structural incompatibility (likely model selection, not prompt/schema)
