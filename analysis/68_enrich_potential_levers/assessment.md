# Assessment: Reduce word counts, add anti-echoing, and use verbatim id guidance

## Issue Resolution

**What PR #469 was supposed to fix:**

1. **Regression from #467** (XML-tag regression) — superseded by new verbatim id guidance.
2. **Regression from #468** (gpt-4o-mini stripped hyphens when field description said "hexadecimal") — fixed by replacing "hexadecimal"/"uuid" wording with "copy it verbatim from inside the tags."
3. **Verbosity**: descriptions were 80–100 words, synergy/conflict 40–60 words — targets reduced to 50–70 / 20–40.
4. **Echoing**: descriptions restated `consequences` and `review` content verbatim — anti-echoing instruction added.

**Is the issue resolved?**

- **Verbosity** — YES. All 7 models reduced field lengths substantially. Mean description dropped from 67.5 → 51.3 words; mean synergy/conflict from ~41.5 → ~26 words. gpt-oss-20b (the primary timeout victim) went from 85.6 → 58.9 words, enabling it to complete hong_kong_game and parasomnia within the 600s plan timeout (previously timed out in run 63; completed in ≤166s in run 84 — verified via `events.jsonl`).

- **Hyphen stripping (#468 regression)** — YES, no regressions observed. All lever_ids in run 87 (gpt-4o-mini) use standard UUID format with hyphens intact across all 5 plans.

- **Anti-echoing** — QUALITATIVELY YES for haiku. The parasomnia "Recruitment Channel Strategy" description shifted from generic enrollment language to domain-specific metrics (application-to-enrollment ratio) and named concrete channels. Confirmed by direct comparison of runs 68 and 89 for that plan. Not systematically verified across all models.

- **Verbatim id guidance** — PARTIALLY. Resolved hyphen-stripping (#468 regression). However, the new "copy it verbatim from the prompt" wording in `LeverCharacterization.lever_id` field description is ambiguous: "from the prompt" could mean the full `<lever>uuid</lever>` string. Haiku (run 89, gta_game) produced `lever_id: "dummy_override"` — a semantic placeholder, not a UUID-format fabrication. This is a new failure mode traceable to the ambiguous field description. All 8 real gta_game levers were correctly enriched; the extra entry is discarded.

**Residual symptoms:**
- `errors.append({"type": "unknown_lever_id", ...})` at `enrich_potential_levers.py:285` is still present (flagged as B2 in analysis 65, unfixed across PRs #467, #468, #469). The "haiku errors 5 → 2" comparison in the insight file measures noise, not real failures.
- Three models now fall below the word count floor (see Quality Comparison).

---

## Quality Comparison

Models in both batches (before = runs 62–68 / PR #466; after = runs 83–89 / PR #469):
llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash-001, haiku-4-5-pinned.

| Metric | Before (runs 62–68) | After (runs 83–89) | Verdict |
|---|---|---|---|
| **Success rate** | 33/35 (94.3%) | 35/35 (100%) | IMPROVED |
| gpt-oss-20b success | 3/5 (2 timeouts) | 5/5 (max 166s) | IMPROVED |
| haiku `unknown_lever_id` errors | 5 (2 plans) | 2 (2 plans) | IMPROVED (but both counts are noise — see B1) |
| UUID contamination in synergy/conflict | 0 | 0 | UNCHANGED |
| Lever_id hyphen-stripping (gpt-4o-mini) | 0 | 0 | UNCHANGED |
| New error type (`dummy_override` in haiku) | 0 | 1 | REGRESSED (benign, new failure mode) |
| LLMChatError / Pydantic validation failures | 0 | 0 | UNCHANGED |
| Bracket placeholder leakage `[...]` | Not observed | Not observed | UNCHANGED |
| Option count violations (!= 3 options) | Not observed | Not observed | UNCHANGED |
| Lever name uniqueness | Clean | Clean | UNCHANGED |
| Template leakage | Not observed | Not observed | UNCHANGED |
| Review format compliance (`Controls X vs Y`) | Consistent | Consistent | UNCHANGED |
| Consequence chain format (`Immediate → Systemic → Strategic`) | Preserved | Preserved | UNCHANGED |
| **Avg description length (all 7 models, mean)** | 67.5 words | 51.3 words | IMPROVED |
| **Avg synergy length (all 7 models, mean)** | 41.6 words | 25.9 words | IMPROVED |
| **Avg conflict length (all 7 models, mean)** | 41.5 words | 26.4 words | IMPROVED |
| Models with description in 50–70 target | 1/7 | 4/7 | IMPROVED |
| Models with synergy in 20–40 target | 3/7 | 6/7 | IMPROVED |
| **Models below description floor (< 50 words)** | 0/7 | 3/7 (llama3.1: 46.5, gemini: 47.8, qwen3-30b: 39.7) | REGRESSED (cosmetic) |
| **Models below synergy floor (< 20 words)** | 0/7 | 1/7 (qwen3-30b: 18.1) | REGRESSED (cosmetic) |
| Field length vs baseline ratio (max) | Up to 1.28× (gpt-oss-20b desc at 85.6 vs baseline 66.9) | All below 1.0× (max 0.88×) | IMPROVED |
| **Fabricated quantification** (% claims in consequences) | Present in all models (pre-existing from identify step) | Present in all models (pre-existing) | UNCHANGED |
| Marketing-copy language ("cutting-edge", etc.) | Occasional (consequences inherit from identify step) | Occasional (same pre-existing source) | UNCHANGED |
| Cross-call duplication | Not systematically observed | Not systematically observed | UNCHANGED |
| Over-generation count (>7 levers/call) | Not applicable (enrich step, not identify) | Not applicable | N/A |
| **B1 unfixed** (errors.append for unknown_lever_id) | Present | Present | UNCHANGED (pre-existing) |

**Field length vs baseline detail (after / baseline gemini-flash 66.9/36.0/38.1 words):**

| Model | desc ratio | syn ratio | conf ratio |
|---|---|---|---|
| llama3.1 | 0.70× | 0.93× | 0.81× |
| gpt-oss-20b | 0.88× | 0.72× | 0.68× |
| gpt-5-nano | 0.83× | 0.69× | 0.70× |
| qwen3-30b | 0.59× | 0.50× | 0.52× |
| gpt-4o-mini | 0.80× | 0.70× | 0.67× |
| gemini | 0.71× | 0.63× | 0.65× |
| haiku | 0.85× | 0.88× | 0.84× |

All ratios are below 1.0×. The 2× verbosity warning threshold is not exceeded in any direction. Note: baseline synergy/conflict text contains UUID references (pre-PR #466 baseline), slightly inflating baseline word counts and making after-run ratios appear slightly smaller than they are in practice.

**OPTIMIZE_INSTRUCTIONS alignment:**

The OPTIMIZE_INSTRUCTIONS at lines 28–107 of `enrich_potential_levers.py` are up to date for UUID leakage (PR #466) but do not yet document the new semantic-placeholder failure mode (`"dummy_override"`) introduced by PR #469's verbatim id guidance. The "Consequence echoing" problem is now partially addressed by the anti-echoing instruction, but the documentation entry for it predates the fix and does not acknowledge it. No new violations of the known-problems list were introduced; the PR moves closer to the goals (concise, realistic, feasible descriptions) on the verbosity dimension.

---

## New Issues

1. **Semantic placeholder in `lever_id` (haiku gta_game run 89)** — PR #469's verbatim id guidance ("copy it verbatim from the prompt, without XML tags") is ambiguous. The phrase "from the prompt" refers to text that includes `<lever>uuid</lever>` tags, so a model could read it as "copy the whole tag string then strip." Haiku generated `lever_id: "dummy_override"` — a fabricated placeholder string rather than a UUID-format fabrication. All 8 real gta_game levers were correctly enriched; this is a cleanliness regression only. This failure mode is new: earlier haiku errors were UUID-format fabrications (`"64a2e8f4-..."` etc.), not semantic placeholders.

2. **Three models below the stated description word count floor** — After the tighter 50–70 word target, llama3.1 (46.5 words), gemini (47.8 words), and qwen3-30b (39.7 words) fall below the 50-word floor. qwen3-30b synergy (18.1 words) is also below the 20-word floor. Since there is no schema validator enforcing the floor (zero LLMChatError events), these are benign — but the stated target range is now aspirational for naturally concise models.

3. **B1 still unfixed (carried over from analysis 65)** — `errors.append({"type": "unknown_lever_id", ...})` at `enrich_potential_levers.py:285` conflates expected over-generation noise with real failures. This was flagged in analysis 65 and still not addressed. The haiku error comparison (5 → 2) in this analysis is measuring noise, not real failures.

**Surfaced latent issues:** None. No new model categories failed, and no previously hidden validation failures emerged.

---

## Verdict

**CONDITIONAL**: PR #469 delivers a 100% success rate (up from 94.3%) and normalises field lengths across all 7 models, but three models now fall below the word count floor and the verbatim id guidance introduced a new haiku failure mode (`"dummy_override"`). These are minor, correctness-neutral issues — all 35 levers are correctly enriched in every after-run plan — but they require prompt follow-up.

**Conditions for full acceptance:**
1. Fix `errors.append` for `unknown_lever_id` at `enrich_potential_levers.py:285` (B1) — one-line removal, waiting since analysis 65.
2. Add a narrow placeholder guard to the `lever_id` field description and system prompt to prevent the `"dummy_override"` failure mode.
3. Update `OPTIMIZE_INSTRUCTIONS` to document the semantic-placeholder pattern.

---

## Recommended Next Change

**Proposal:** Remove `errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})` at `enrich_potential_levers.py:285`, keeping the `logger.warning` on line 284 unchanged.

**Evidence:** Both agents flagged this in analysis 65 (B2/I1) and again in this analysis (B1/I1). The synthesis confirms: the "5 → 2" haiku error improvement in the before/after comparison is entirely noise — both counts consist of over-generation entries that are already discarded. With B1 fixed, haiku's real error rate is 0/35 (not 2/35). Every analysis iteration that runs without this fix produces a misleading comparison table. The code is `enrich_potential_levers.py:285`; the change is a single line deletion.

Pair with the placeholder guard change (Direction 2 in the synthesis) in the same commit:
- In `LeverCharacterization.lever_id` field description (`enrich_potential_levers.py:138`): change "copy it verbatim from the prompt, without XML tags" to match the system prompt's more precise wording ("copy the id verbatim from inside the tags — do not substitute placeholder text such as 'dummy', 'test', or 'override'").
- Add to `OPTIMIZE_INSTRUCTIONS`: document the semantic-placeholder failure mode observed in haiku run 89 gta_game.

**Verify in the next iteration:**
- Haiku `errors` array should be empty `[]` across all 5 plans (real error rate 0/35), not "2".
- Haiku gta_game should have no `"dummy_override"` or other placeholder strings in the `errors` array. If it does, check whether the placeholder guard in the field description is being ignored.
- Run 87 (gpt-4o-mini) lever_ids should remain hyphen-intact — confirm the verbatim guidance change does not reintroduce hyphen-stripping.
- Run 83 (llama3.1) synergy/conflict should remain UUID-free — confirm PR #466's fix is preserved.
- Specifically check haiku on the parasomnia and silo plans (the two plans that had the most errors before PR #469) to verify the reduction is sustained.

**Risks:**
- The placeholder guard uses narrow negative prohibition ("do not substitute placeholder text such as 'dummy', 'test', 'override'"). OPTIMIZE_INSTRUCTIONS warns against naming banned phrases, but this is domain-specific and narrow enough to not teach general UUID-format fabrications. Watch for haiku generating other new placeholder strings ("placeholder", "example", "n/a") that were not enumerated.
- Widening the lever_id field description wording might affect models that are currently handling it correctly. Verify gpt-4o-mini and gpt-5-nano in the next run — both were clean in runs 87 and 85 respectively.
- No blocking prerequisites. B1 and the placeholder guard can be applied together without depending on other unfixed items.

---

## Backlog

**Resolved (can be closed):**
- UUID contamination in synergy/conflict (llama3.1): fully resolved by PR #466; confirmed still clean in runs 83–89. Remove from active tracking.
- gpt-4o-mini lever_id hyphen-stripping (#468 regression): confirmed absent in run 87.

**Carry forward (pre-existing, not introduced by this PR):**
- **B1** — `errors.append` for `unknown_lever_id` at `enrich_potential_levers.py:285`. Priority: HIGH. Was B2 in analysis 65; still present. Blocks meaningful haiku error-count comparison in future analyses.
- **negative prohibition in `Lever.consequences` field description** (`identify_potential_levers.py:116–119`): Phrases "Controls … vs." and "Weakness:" are named explicitly as things to avoid, violating OPTIMIZE_INSTRUCTIONS. High long-term impact (affects identify step), requires a separate `identify_potential_levers` experiment iteration.
- **Duplicate exact-count instruction** in both system prompt and user prompt of `enrich_potential_levers.py` (lines 179 and 256): system-level abstract ("one per lever") vs. user-level concrete ("exactly N"). Abstract version may be removed to reduce ambiguity for haiku.
- **Missing `messages_snapshot`** in `enrich_potential_levers.py:265` `execute_function` closure (safe in current synchronous execution; inconsistent with `identify_potential_levers.py:317`).
- **`partial_recovery` event threshold** in `runner.py:131` fires for clean 2-call runs; should only fire when a call actually failed.

**New (introduced or confirmed by this PR):**
- **Semantic-placeholder `lever_id` failure mode** (`"dummy_override"` in haiku run 89 gta_game): field description wording "from the prompt" is ambiguous. Add placeholder guard. Document in OPTIMIZE_INSTRUCTIONS.
- **Three models below stated description floor** (llama3.1: 46.5, gemini: 47.8, qwen3-30b: 39.7 words): word count targets may need softening ("aim for 50–70") to align guidance with observed behavior for naturally concise models. Low urgency — no correctness impact.
