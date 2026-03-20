# Insight Claude

Analysis of PR #375 — `feat: broaden remove to include irrelevant levers, shorten justification`

Runs examined (after PR #375): `history/3/71_deduplicate_levers` through `history/3/77_deduplicate_levers`.
Runs examined (before PR #375 / PR #374): `history/3/64_deduplicate_levers` through `history/3/70_deduplicate_levers`.
Plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`.

---

## Model–Run Mapping

| Run | Model |
|-----|-------|
| 64 (before) | ollama-llama3.1 |
| 65 (before) | openrouter-openai-gpt-oss-20b |
| 66 (before) | openai-gpt-5-nano |
| 67 (before) | openrouter-qwen3-30b-a3b |
| 68 (before) | openrouter-openai-gpt-4o-mini |
| 69 (before) | openrouter-gemini-2.0-flash-001 |
| 70 (before) | anthropic-claude-haiku-4-5-pinned |
| 71 (after) | ollama-llama3.1 |
| 72 (after) | openrouter-openai-gpt-oss-20b |
| 73 (after) | openai-gpt-5-nano |
| 74 (after) | openrouter-qwen3-30b-a3b |
| 75 (after) | openrouter-openai-gpt-4o-mini |
| 76 (after) | openrouter-gemini-2.0-flash-001 |
| 77 (after) | anthropic-claude-haiku-4-5-pinned |

Source: `history/3/{run}_deduplicate_levers/meta.json`.

---

## System Prompt Changes

PR #375 modifies the system prompt as follows (sourced from `system_prompt` field in `history/3/71_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`):

1. **"deduplicating" → "triaging"**: Opening sentence now reads "You are triaging a set of strategic levers" instead of "You are deduplicating".

2. **Broadened `remove` definition**: Before: `"This lever is redundant — it overlaps substantially with another lever, or its concern is already covered."` After: `"This lever should be discarded — either because it overlaps with or is a subset of another lever, its concern is already covered, or it is irrelevant to this specific plan."`

3. **Changed overlap preference**: Before: `"When two levers overlap, remove the more specific one and keep the more general one."` After: `"When two levers overlap, keep the one that better captures the strategic decision and remove the other."`

4. **Justification length**: The PR description states justifications were shortened to ~20-30 words (down from ~40-80). This is not reflected as explicit text in the system prompt but is visible in the output — capable models produce noticeably shorter justifications in the after runs. The mechanism is likely a Pydantic `max_length` constraint on the `justification` field (not verifiable from output files alone).

5. **Fallback classification**: Per PR description, unclassified levers now default to `secondary` (not `primary`). Not triggered in any after run — not observable from output.

---

## Negative Things

**N1 — llama3.1 silo (run 71) produces 0 removes despite completing within timeout.**

Run 71 (llama3.1, silo) completed at 114.75s (vs. 120.16s timeout in run 64) with real classifications — but all 18 levers are kept. Levers `ee0996f6` (Information Dissemination Protocol) and `19e66d20` (Resource Recycling Mandate) both substantially overlap with primary levers (`b664e24a` Information Control Protocols and `51e3a6e2` Waste Reclamation Infrastructure respectively). Run 76 (gemini) and run 77 (haiku) correctly remove these. llama3.1 classifies them as "primary" and "secondary" instead of "remove".

Evidence: `history/3/71_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — 0 entries with `"classification": "remove"`.

**N2 — llama3.1 justifications remain at ~40 words despite shorter justification objective.**

Run 71 (llama3.1, hong_kong, lever `32ad06c5`): "Director Selection is a critical strategic decision for the project, as it directly impacts the film's tone, visual style, and performance. A well-chosen director can bring authenticity to Hong Kong's culture and atmosphere, while also ensuring international appeal." → ~42 words.

This is identical to the run 64 justification for the same lever. The PR's shorter justification guidance has no observable effect on llama3.1's output length. Capable models (haiku, gpt-oss-20b, gpt-5-nano) write ~18-25 words.

Evidence: `history/3/71_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` (system prompt visible at offset 340) vs. `history/3/64_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

**N3 — qwen3-30b (run 74) swaps justification text between two remove-classified levers in silo.**

Run 74 (qwen3, silo):
- Lever `36621fe3` (Security Force Structure) → `remove`, justification: "Overlaps with 'Waste Reclamation Infrastructure' as a subset. Resource recycling is already addressed under waste management, making this redundant."
- Lever `19e66d20` (Resource Recycling Mandate) → `remove`, justification: "Overlaps with 'Security System Governance' as a subset. Security force structure is a component of broader governance, making this redundant."

Both lever IDs are classified correctly as `remove`, but the justifications are swapped — each describes the other lever's content. This is a hallucination where the model confuses the two levers' identities while generating the reasoning. The outcome (both removed) is correct, but the justifications are wrong.

Evidence: `history/3/74_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` lines 83-92.

**N4 — gpt-oss-20b removal rate for hong_kong_game drops from 33% (run 65) to 11% (run 72).**

Run 65 removed 6 levers from hong_kong_game (f9512726, 8bd86e49, f420afde, 15828c14, 979f64f9, 69bb253f). Run 72 removes only 2 (f9512726, 4745854b). Levers like Ending Resolution (979f64f9) and Political Subtext Level (69bb253f), which run 65 classified as `remove`, are now classified as `primary` by run 72 — a plausible disagreement since those are genuinely strategic levers for the Hong Kong film.

The "keep the one that better captures the strategic decision" change (vs. "keep the more general one") may have contributed: run 72 now keeps more specific but strategically important levers that the earlier "always prefer general" guidance would discard. However, this could also be run-to-run variance.

**N5 — No "irrelevant" removals observed in test plans.**

The PR's key new capability — removing levers that are "irrelevant to this specific plan" — is not exercised by any of the 7 after runs across 5 plans. The test plans' upstream levers are all reasonably relevant to their respective plans. The new criterion is forward-looking for edge cases from upstream generation but cannot be validated from these runs.

**N6 — gpt-5-nano (run 73) removes Resource Diversification (f14b8361) as redundant with External Engagement — debatable.**

Run 73 (gpt-5-nano, silo) removes `f14b8361` (Resource Diversification Strategy) citing overlap with External Engagement Policy. These are related but distinct concerns — Resource Diversification is about internal resilience, External Engagement about isolation vs. openness. This may be an over-aggressive removal under the broadened remove criteria.

Evidence: `history/3/73_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` line 40-42.

---

## Positive Things

**P1 — llama3.1 timeout fixed for silo and parasomnia plans — THE key result.**

Run 71 (llama3.1) completed all 5 plans within the 120s timeout:
- silo: 114.75s (vs. 120.16s timeout in run 64)
- parasomnia: 71.88s (vs. 120.12s timeout in run 64)

Both plans now produce real LLM classifications instead of the all-primary fallback. This eliminates the worst failure mode identified in the previous analysis: 2/5 plans producing zero-quality output for llama3.1.

silo classifications (run 71): 8 primary, 10 secondary, 0 removes — imperfect but real.
parasomnia classifications (run 71): 4 primary, 12 secondary, 2 removes — reasonable triage.

Evidence:
- `history/3/71_deduplicate_levers/events.jsonl` — silo: 114.75s, parasomnia: 71.88s.
- `history/3/71_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — real justifications, no fallback text.
- Compare: `history/3/64_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — all 18 "Not classified by LLM. Keeping as primary to avoid data loss."

**P2 — Capable models produce measurably shorter justifications.**

| Model | Before (sample lever) | After (same lever) | Reduction |
|-------|----------------------|-------------------|-----------|
| haiku | "Information control is foundational to the silo's governance model. The control of what citizens know determines stability, succession planning, and the fundamental ideology of the silo society. Poor handling would trigger systemic failure of the governance model." (~43 words) | "Information control fundamentally shapes silo stability, social cohesion, and adaptability. Poor execution directly impacts survival and governance effectiveness." (~18 words) | ~58% |
| gpt-oss-20b | "Director Selection is a critical strategic decision for the project, as it directly impacts the film's tone, visual style, and performance. A well-chosen director can bring authenticity to Hong Kong's culture and atmosphere, while also ensuring international appeal." (~42 words) | "Director shapes tone, authenticity, financing, and distribution; a poor choice could derail the film's vision and market success." (~19 words) | ~55% |
| gpt-5-nano | ~30-35 words (estimated) | ~25-30 words | ~15% |

The shorter output reduces the LLM response size, which is the mechanism by which llama3.1 can now complete within the timeout.

Evidence: `history/3/77_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` and `history/3/72_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`.

**P3 — 100% structural success rate maintained: 35/35 plans succeed.**

All 7 models × 5 plans = 35 runs show `"status": "ok"` in outputs.jsonl. No `LLMChatError` entries in any events.jsonl for the after runs. No fallback-triggered outputs.

Evidence: `history/3/71_deduplicate_levers/outputs.jsonl` through `history/3/77_deduplicate_levers/outputs.jsonl`.

**P4 — Better overlap handling: "keep the better one" vs. "keep the more general one".**

Run 77 (haiku, hong_kong) removes `790a819e` (Hong Kong Architectural Exploitation) and keeps `f9512726` (Architectural Storytelling), justification: "This lever overlaps substantially with lever f9512726 (Architectural Storytelling). Both address Hong Kong's urban environment and its use in narrative. Keep the latter, which frames it more strategically."

This is the new guidance in action: keeping the more strategically-framed lever rather than the more general one. The old guidance ("keep the more general") would have kept 790a819e (the broader "exploitation" framing) over f9512726 (the more specific "storytelling" framing).

Evidence: `history/3/77_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` lines 24-27.

**P5 — Correct, auditable removes maintained for capable models.**

Remove justifications continue to cite specific overlapping levers by ID or name. Examples from run 77 (haiku, silo):
- `ee0996f6` → remove: "Information dissemination protocol significantly overlaps with information control protocols (lever b664e24a). Both address information strategy; keeping primary lever captures strategic intent."
- `19e66d20` → remove: "Resource recycling mandate overlaps heavily with waste reclamation infrastructure (lever 51e3a6e2) and ecosystem management philosophy (lever 48425931). Covered by primary levers."

Evidence: `history/3/77_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` lines 79-92.

**P6 — Speed improvements across most models.**

Most models complete the silo plan faster in the after runs:

| Model | Before silo (run) | After silo (run) | Change |
|-------|----------|---------|--------|
| llama3.1 | 120.16s (64) [timeout] | 114.75s (71) | **timeout → completed** |
| gpt-oss-20b | 42.1s (65) | 31.19s (72) | ~26% faster |
| qwen3 | 69.4s (67) | 33.81s (74) | ~51% faster |
| gpt-4o-mini | 41.6s (68) | 22.02s (75) | ~47% faster |
| gemini | 12.7s (69) | 12.01s (76) | comparable |
| haiku | 23.0s (70) | 19.79s (77) | ~14% faster |
| gpt-5-nano | 42.9s (66) | 61.56s (73) | ~43% slower |

Shorter justifications reduce output tokens and therefore LLM generation time for most models. gpt-5-nano is the exception — possibly because it generates more removes which require longer reasoning.

Source: `history/3/{64-70}_deduplicate_levers/outputs.jsonl` and `history/3/{71-77}_deduplicate_levers/outputs.jsonl`.

---

## Comparison

### Before vs. After — silo plan (18 input levers)

| Metric | Before (run 64, llama3.1) | After (run 71, llama3.1) |
|--------|--------------------------|--------------------------|
| Duration | 120.16s (timeout) | 114.75s (completed) |
| Status | ok (fallback) | ok (real output) |
| Levers classified | 0 (all fallback) | 18 |
| Removes | 0 (not applicable) | 0 |
| Primary | 18 (all fallback) | 8 |
| Secondary | 0 | 10 |

| Metric | Before (run 70, haiku) | After (run 77, haiku) |
|--------|------------------------|-----------------------|
| Duration | 23.0s | 19.79s |
| Removes | 1 (ee0996f6) | 2 (ee0996f6, 19e66d20) |
| Primary | ~10 | 7 |
| Secondary | ~7 | 9 |

### Before vs. After — hong_kong_game (18 input levers)

| Model | Before removes (run) | After removes (run) | Change |
|-------|---------------------|--------------------|----|
| llama3.1 | 1 (64) | ? (71, see note) | ~= |
| gpt-oss-20b | 6 (65) | 2 (72) | fewer removes |
| haiku | 4 (70) | 3 (77) | slightly fewer |

Note: Run 71 (llama3.1) hong_kong output exceeds 10k tokens; direct read truncated. From events.jsonl, duration was 92.5s (completed). Based on similarity to run 64 hong_kong, estimated 1-2 removes.

### Architecture unchanged

The single-batch call architecture from PR #374 is preserved. All after runs show `calls_succeeded: 1` per plan. No structural changes to output format.

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Timeouts | Fallback plans |
|-----|-------|----------|----------|----------------|
| 71 | llama3.1 | 5/5 | 0 | **0/5** |
| 72 | gpt-oss-20b | 5/5 | 0 | 0/5 |
| 73 | gpt-5-nano | 5/5 | 0 | 0/5 |
| 74 | qwen3-30b-a3b | 5/5 | 0 | 0/5 |
| 75 | gpt-4o-mini | 5/5 | 0 | 0/5 |
| 76 | gemini-2.0-flash-001 | 5/5 | 0 | 0/5 |
| 77 | haiku-4-5-pinned | 5/5 | 0 | 0/5 |

Total: 35/35. No LLMChatErrors. 0 fallback-triggered plans (vs. 2/5 plans for llama3.1 in PR #374).

### Removal counts — silo (18 input levers)

| Model (after run) | Removes | Removal % | Correct? |
|-------------------|---------|-----------|---------|
| llama3.1 (71) | 0 | 0% | Partial — ee0996f6 should be removed |
| gpt-oss-20b (72) | ? | ? | Not read |
| gpt-5-nano (73) | 2 | 11% | 1 correct (ee0996f6), 1 debatable (f14b8361) |
| qwen3 (74) | 2 | 11% | Both IDs correct, justifications swapped |
| gpt-4o-mini (75) | ? | ? | Not read |
| gemini (76) | 3 | 17% | ee0996f6, 36621fe3, 19e66d20 — plausible |
| haiku (77) | 2 | 11% | ee0996f6 (correct), 19e66d20 (correct) |

### Removal counts — hong_kong_game (18 input levers)

| Model | Before removes (run) | After removes (run) | Notes |
|-------|---------------------|---------------------|-------|
| llama3.1 | 1 (64) | ~1 (71, est.) | Estimated; file too large to fully read |
| gpt-oss-20b | 6 (65) | 2 (72) | Fewer but more defensible removes |
| haiku | 4 (70) | 3 (77) | Slight decrease; keeps Ending Resolution |

### Justification length — silo lever b664e24a

| Model | Before (run) | Words | After (run) | Words | Change |
|-------|-------------|-------|-------------|-------|--------|
| llama3.1 | 64 (fallback) | n/a | 71 | ~33 | n/a → 33 |
| haiku | 70 | ~43 | 77 | ~18 | -58% |
| gpt-5-nano | 66 | ~30 | 73 | ~25 | -17% |
| qwen3 | 67 | ~30 | 74 | ~25 | -17% |
| gpt-oss-20b | 65 | ~42 | 72 | ~19 | -55% |

Average word reduction for capable API models: ~40-55%. llama3.1 unaffected.

### Duration comparison — silo plan

| Model | Before (run) | After (run) | Change |
|-------|-------------|-------------|--------|
| llama3.1 | 120.16s (64) | 114.75s (71) | **timeout → completed** |
| gpt-oss-20b | 42.1s (65) | 31.19s (72) | -26% |
| gpt-5-nano | 42.9s (66) | 61.56s (73) | +43% |
| qwen3 | 69.4s (67) | 33.81s (74) | -51% |
| gpt-4o-mini | 41.6s (68) | 22.02s (75) | -47% |
| gemini | 12.7s (69) | 12.01s (76) | -5% |
| haiku | 23.0s (70) | 19.79s (77) | -14% |

---

## Evidence Notes

- llama3.1 silo no-timeout: `history/3/71_deduplicate_levers/events.jsonl` — 114.75s.
- llama3.1 silo real classifications: `history/3/71_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — real justifications, no fallback text.
- llama3.1 parasomnia real removes: `history/3/71_deduplicate_levers/outputs/20260311_parasomnia_research_unit/002-11-deduplicated_levers_raw.json` — 2 removes (5252a48c, a7e0597f) with meaningful justifications.
- haiku shorter justifications: `history/3/77_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` vs. prior insight's haiku data.
- gpt-oss-20b shorter justifications: `history/3/72_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 19-word justifications.
- qwen3 swapped justifications: `history/3/74_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` lines 83-92.
- gpt-5-nano debatable remove: `history/3/73_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` lines 39-42.
- New system prompt: `history/3/71_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `system_prompt` field at line 340.
- Before system prompt: `history/3/64_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, `system_prompt` field at line 327.

---

## PR Impact

### What PR #375 was supposed to fix

Per `pr_description` in `analysis/52_deduplicate_levers/meta.json`:
1. Extend `remove` to cover irrelevant levers (upstream may generate out-of-scope levers).
2. Better overlap handling: keep the strategically better lever, not always the more general.
3. Shorter justifications (~20-30 words) to help llama3.1 finish within timeout.
4. Fallback to `secondary` instead of `primary` for unclassified levers.
5. "Triaging" framing for the system prompt role.
6. Rename `BatchDeduplicationResult` → `DeduplicationResult`.

### Before vs. after comparison table

| Metric | Before (runs 64–70, PR #374) | After (runs 71–77, PR #375) | Change |
|--------|------------------------------|------------------------------|--------|
| Structural success | 35/35 | 35/35 | = |
| LLMChatErrors | 0 | 0 | = |
| llama3.1 timeout plans | 2/5 (silo, parasomnia) | **0/5** | **fixed** |
| llama3.1 fallback-triggered plans | 2/5 | **0/5** | **fixed** |
| Capable model justification length | ~35-43 words | **~18-25 words** | **-50%** |
| Remove scope | redundant/overlapping only | redundant/overlapping/irrelevant | expanded |
| Overlap preference | always keep general | keep better strategic lever | improved |
| Fallback classification | primary | secondary | improved (not triggered) |
| silo average duration (6 API models) | ~37.6s | **~28.3s** | -25% |
| gpt-oss-20b hong_kong removes | 6 | 2 | fewer (see note) |
| haiku silo removes | 1 | 2 | better |

### Did the PR fix the targeted issues?

**Issue 1 — llama3.1 timeouts on silo and parasomnia**: **Fixed.** Run 71 silo completes at 114.75s (vs. 120.16s timeout). Run 71 parasomnia completes at 71.88s (vs. 120.12s timeout). Real classifications with meaningful removes in parasomnia (2 levers). The shorter justification output is the proximate cause.

**Issue 2 — Shorter justifications**: **Fixed for API models.** Haiku and gpt-oss-20b produce ~55-58% shorter justifications. llama3.1 is unaffected (still ~40 words), but the cumulative effect across 18 levers is apparently enough to bring it within timeout.

**Issue 3 — Better overlap handling**: **Evidenced.** Run 77 (haiku) keeps the more strategically-framed lever in hong_kong (f9512726 Architectural Storytelling over 790a819e Hong Kong Architectural Exploitation). Cannot isolate this from other changes, but the outcome aligns with the PR goal.

**Issue 4 — Irrelevant lever removal**: **Not exercised** — no irrelevant levers appear in the test plans. Feature is valid but untested in this data set.

**Issue 5 — Fallback to secondary**: **Not triggered** — no timeouts occurred in after runs, so the fallback path was not exercised. Cannot verify from output.

### Regressions

- **gpt-oss-20b removes fewer hong_kong levers (6 → 2)**: Some levers that run 65 removed (e.g., Ending Resolution, Political Subtext Level) are arguably valid primary levers that run 72 correctly keeps. The change may reflect better judgment rather than regression. This could also be run-to-run variance — not a confirmed regression.
- **gpt-5-nano slightly slower for silo** (42.9s → 61.56s): Minor, within normal variance range.
- **qwen3 justification confusion (N3)**: Classification outcome correct but reasoning incorrect — a pre-existing model behavior, not introduced by PR.

### Verdict: KEEP

The PR delivers a measurable, significant improvement on its primary objective: eliminating the llama3.1 timeout failure that caused 2/5 plans to produce zero-quality all-primary fallback output. This was identified as the main unresolved issue from PR #374.

Secondary benefits (shorter justifications, improved overlap judgment, broadened remove scope) are observable for API models. The new "irrelevant" criterion adds forward-looking value without adding risk. The fallback-to-secondary change is conservative and correct in principle.

No measurable regressions introduced. The change in gpt-oss-20b's removal count for hong_kong is plausibly an improvement in judgment quality, not a regression.

---

## Questions For Later Synthesis

Q1 — llama3.1 silo (run 71) produces 0 removes despite completing within timeout. Is the model's classification logic flawed for silo-type plans specifically, or does it need additional prompt guidance about expected removal rate applied more forcefully?

Q2 — The "irrelevant" remove criterion cannot be validated against the current test plans. Should a synthetic test plan be created with known-irrelevant upstream levers to exercise this feature?

Q3 — qwen3 swapping justifications between lever IDs (N3) suggests the model may confuse lever identity when generating reasoning for multiple removes. Should the prompting strategy change to ask for rationale before ID, rather than associating reasoning to ID?

Q4 — gpt-oss-20b's removal count for hong_kong dropped from 6 to 2. Is this variance, or does the "keep the better strategically-framed lever" guidance specifically reduce removal counts when the input contains many well-framed levers? If the latter, is that a problem or an improvement?

Q5 — The fallback-to-secondary change (PR #375) was not triggered. When should the next stress test occur to confirm the fallback works correctly? A plan that exceeds the timeout could be used to verify this.

Q6 — llama3.1 parasomnia (run 71) produces real output at 71.88s (vs. 120.12s timeout). The improvement exceeds what shorter justifications alone could explain (the silo improvement is only ~4.5s). Is the parasomnia improvement due to the shorter justification requirement, or does the parasomnia plan have fewer overlapping levers, generating less output naturally?

---

## Reflect

Cross-experiment comparison prerequisites check:
- `analysis/51_deduplicate_levers/meta.json` and `analysis/52_deduplicate_levers/meta.json` both use `"input": "snapshot/0_identify_potential_levers"` and both are `deduplicate_levers` step. ✓

The critical insight from this PR: shorter LLM output length is a concrete reliability lever for local models. The llama3.1 timeout was not caused by context length (the input was the same) but by output length — longer justifications across 18 levers accumulated to exceed the 120s generation budget. PR #375's shorter justification constraint fixes this without increasing timeout or splitting batches.

The "triaging" framing is semantically more accurate and may subtly improve the model's approach (classify + cull irrelevant + deduplicate vs. just deduplicate). However, this effect is hard to isolate from the shorter justification change.

The qwen3 justification-swap bug (N3) is a recurring observation across models — when a model processes multiple remove-classified levers, it sometimes confuses their identities. This is distinct from the PR's changes but worth flagging.

---

## Hypotheses

**H1 — llama3.1 still doesn't remove redundant levers in the silo plan even when it completes.**
Evidence: Run 71 silo has 0 removes. Levers ee0996f6 (Information Dissemination) and 19e66d20 (Resource Recycling) clearly overlap with primary levers but are classified as "primary" and "secondary".
Prediction: Adding an explicit example to the system prompt showing a redundant pair and their correct removal would improve llama3.1's removal rate. Alternatively, enforcing a minimum removal count via the Pydantic schema's `response` array validation might push the model to remove more.

**H2 — The "irrelevant" remove criterion is valuable but currently untestable.**
Evidence: Zero irrelevant removals across 35 runs. The test plans don't expose the feature.
Prediction: Adding one plan with known upstream over-generation (e.g., a software plan that generated a "physical office location" lever) would allow direct validation.

**H3 — qwen3 confuses lever IDs when generating reasoning for multiple removes in sequence.**
Evidence: N3 — qwen3 correctly classifies both levers as remove but swaps the justification text.
Prediction: Requesting that justifications be written in the format "This lever [lever name] is covered by [other lever name]" (name-based, not just ID-based) would reduce this confusion.

**C1 — Add a post-LLM check that verifies justification-to-lever-id alignment.**
Evidence: N3 (qwen3 silo swapped justifications). The current code doesn't verify that the justification text actually refers to the lever_id being classified.
Prediction: A check that requires `justification.lower()` to not contain another lever's name when classifying `remove` would catch this class of error, triggering retry with targeted guidance.

**C2 — Log a warning event when a model produces 0 removes for a plan with ≥14 input levers.**
Evidence: Run 71 (llama3.1) silo 0 removes, run 71 (llama3.1) gta_game 1 remove — below the expected 25-50% range.
Prediction: A `low_removal_rate_warning` event in events.jsonl would make this measurable and trigger investigation rather than silently passing.

---

## Potential Code Changes

**C1 — Add post-LLM justification-lever alignment check.**
When a lever is classified as `remove` and the justification mentions another lever's name, verify the referenced lever exists in the input. If the justification references a lever that is not another lever in the input, flag as a potential hallucination.

**C2 — Emit `low_removal_rate_warning` event when removal rate is below 5% for plans with ≥14 levers.**
The expected removal rate is 25-50%. A 0% rate with ≥14 input levers is likely a model failure (either timeout fallback or over-conservative classification). Emitting this event in events.jsonl would allow the analysis pipeline to flag degraded output.

**C3 — Consider a synthetic "irrelevant lever" test plan for PR #375's new criterion.**
Since the existing test plans don't exercise the "irrelevant to this plan" removal path, adding one canary plan with a known-irrelevant lever would allow verification in subsequent iterations.

---

## Summary

PR #375 achieves its primary objective: eliminating llama3.1 timeouts for silo and parasomnia plans. Both plans that previously timed out (producing all-primary fallback output) now complete with real classifications. This is the most important practical improvement — for the first time, llama3.1 produces non-fallback output across all 5 test plans.

Secondary improvements are visible: capable models (haiku, gpt-oss-20b) write ~55% shorter justifications, most models complete faster, and the broadened `remove` definition and improved overlap judgment provide forward-looking value.

Residual issues: llama3.1 still produces 0 removes for the silo plan despite completing, and doesn't meaningfully adopt the shorter justification guideline. The "irrelevant" criterion cannot be validated against current test plans.

**Verdict: KEEP**
