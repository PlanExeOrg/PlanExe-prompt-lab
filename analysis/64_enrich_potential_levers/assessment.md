# Assessment: Move UUID to end of lever details, add positive framing and exact-count

## Issue Resolution

**PR #464** introduced three changes to `enrich_potential_levers.py`:

1. **UUID repositioned**: `Lever ID: {uuid}` (first line of each batch block) → `(internal reference: {uuid})` (last line).
2. **Positive framing**: System prompt gained: "In `synergy_text` and `conflict_text`, always refer to other levers by their name — for example, write 'Policy Advocacy Strategy', not an identifier."
3. **Exact-count instruction**: User prompt gained: "Return exactly N characterizations — one per lever, no more, no fewer." System prompt gained: "Return exactly one characterization per lever requested — no more, no fewer."

**Targeted issue**: UUID leakage into `synergy_text`/`conflict_text` free-text fields. After PR #457 removed UUIDs from `full_lever_context_str`, the per-batch `lever_details_for_prompt` (which begins each block with `Lever ID: {uuid}`) remained the active leakage vector — primarily for llama3.1, which still had 15 UUID occurrences in synergy/conflict text in runs 4/27.

**Is the issue resolved?**

- **UUID leakage from synergy/conflict text**: Cannot be confirmed from the after runs, because llama3.1 (the primary offender) produces 0 characterized levers after the PR — there is no synergy/conflict text to inspect. For gpt-5-nano (which retains 10/35 levers across 2 plans), synergy/conflict text uses lever names cleanly. For the three unaffected models (qwen3, gpt-4o-mini, gemini-flash), UUID leakage was already 0 before this PR. The leakage reduction cannot be confirmed for the models that previously had it.

- **Structured-output matching (critical regression)**: Moving the UUID to last position broke `lever_id` matching for small models. llama3.1 and gpt-5-nano use positional heuristics: the first item in a block is treated as the identifier to echo into the `lever_id` structured-output field. With UUID at the end, both models return the lever **name** as `lever_id`. The matching code at line 276 of `enrich_potential_levers.py` performs a strict UUID key lookup — names never match — so all characterizations are silently dropped.

  - **llama3.1** (run 55, silo): `characterized_levers: []`, 7 `unknown_lever_id` errors (all lever names), 7 `incomplete` errors. **Verified directly** in `history/4/55_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`.
  - **gpt-5-nano** (run 57, sovereign_identity): `characterized_levers: []`, 5 `unknown_lever_id` errors (all lever names: "Technical Feasibility Strategy", "Policy Advocacy Strategy", etc.), 5 `incomplete` errors. **Verified directly** in `history/4/57_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`.

- **Positive framing**: Haiku's synergy/conflict text (run 61, silo — the haiku plan that did characterize levers) uses lever names only, no UUID patterns. For haiku, the positive framing likely helps. For the other passing models this was already the case.

- **Exact-count instruction**: No measurable effect. Haiku's over-generation (fabricated UUID entries) increased slightly (7 → 11). The instruction did not suppress phantom characterizations.

**Residual symptoms**: The original UUID leakage problem (15 occurrences in llama3.1 run 27) is now moot — llama3.1 produces no characterizations at all. The per-batch UUID leakage concern remains unresolved in principle, though no model in the after runs shows it (because the two that had it either produce nothing or were already clean).

---

## Quality Comparison

Both batches use `baseline/train` (5–8 levers/plan, 35 levers total per model over 5 plans). Before: runs 4/27–33 (analysis 60, PR #457 state). After: runs 4/55–61 (this analysis, PR #464). All 7 models appear in both batches.

| Metric | Before (runs 27–33) | After (runs 55–61) | Verdict |
|--------|--------------------|--------------------|---------|
| **Overall characterized levers** | 245/245 (100%)* | 181/245 (74%) | **REGRESSED (–26%)** |
| **llama3.1 characterized** | 35/35 (100%) | 0/35 (0%) | **REGRESSED (–100%, critical)** |
| **gpt-5-nano characterized** | 35/35 (100%) | 10/35 (29%) | **REGRESSED (–71%, severe)** |
| **gpt-oss-20b characterized** | 35/35 (100%) | 32/35 (91%) | **REGRESSED (–9%, minor)** |
| **qwen3-30b characterized** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **gpt-4o-mini characterized** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **gemini-2.0-flash characterized** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **haiku characterized** | 35/35 (100%) | 34/35 (97%) | **REGRESSED (–3%, minor)** |
| **Total unknown_lever_id errors** | 7 (haiku phantom UUIDs) | 84 (llama:36, gpt-5-nano:25, gpt-oss:3, haiku:10, others:10) | **REGRESSED (+1100%)** |
| **Total incomplete errors** | 0 | 72 (llama:35, gpt-5-nano:25, gpt-oss:3, haiku:1, others:8) | **REGRESSED (new class)** |
| **Success rate** | 34/35 plans (97%)** | ~29/35 plans (83%)*** | **REGRESSED** |
| **UUID in synergy_text (all models)** | 7 (llama3.1, 2 plans) | ~0 (no passing models had it) | UNCONFIRMED (no baseline model to compare) |
| **UUID in conflict_text (all models)** | 8 (llama3.1, 1 plan) | ~0 | UNCONFIRMED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 35/35 per run | 35/35 (passing models) | UNCHANGED |
| **Template leakage** | 0 observed | 0 observed | UNCHANGED |
| **Review format compliance** | Present (from input) | Present (from input) | UNCHANGED |
| **Consequence chain format (→)** | Present (from input) | Present (from input) | UNCHANGED |
| **Content depth — desc (chars vs baseline 483)** | 0.76–1.36× | 0.83–1.43× (passing models) | UNCHANGED |
| **Content depth — syn (chars vs baseline 285)** | 0.62–1.56× | 0.64–1.57× (passing models) | UNCHANGED |
| **Content depth — conf (chars vs baseline 298)** | 0.63–1.53× | 0.65–1.59× (passing models) | UNCHANGED |
| **Field length vs baseline (>2× warning)** | No model >2× | No model >2× | UNCHANGED |
| **Fabricated quantification (% claims)** | Present, all models (pre-existing) | Present, all models (pre-existing) | UNCHANGED (pre-existing) |
| **Marketing-copy language** | Present (echoed from input) | Present (echoed from input) | UNCHANGED (pre-existing) |
| **Cross-call duplication** | Not observed | Not observed | UNCHANGED |
| **Over-generation (>7 levers/call)** | Not applicable | Not applicable | UNCHANGED |
| **haiku extra characterizations** | 7 phantom entries | 11 phantom entries | **REGRESSED (+4)** |
| **OPTIMIZE_INSTRUCTIONS currency** | Stale (lines 88–92 describe fixed issue) | Updated (per PR #464 description), but missing position-risk warning | **PARTIALLY IMPROVED, INCOMPLETE** |

\* haiku had 7 extra phantom entries in before runs; the 35/35 row counts only correct characterizations.
\*\* Before: gpt-oss-20b ran 5/5 successfully (vs 2/5 in analysis 60, but the analysis 60 was baseline for this comparison — run 28 completed 5/5 successfully).
\*\*\* Counting plans where all levers were characterized: llama3.1 = 0/5, gpt-5-nano = 2/5, gpt-oss-20b = 4/5, others = 5/5 each.

**Content quality note (verified from actual files)**:

- haiku (run 61, silo): All 7 characterized levers use lever names in synergy/conflict — no UUID patterns. Content is substantive and well-organized. The 5 phantom errors have fabricated sequential UUIDs (`72f9e8a1-...`, `1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p` — invalid UUID format). Real levers are unaffected.
- gemini (run 60, gta_game): `errors: []`, 8 characterized levers. Clean, no regressions. **Verified directly.**
- llama3.1 (run 55, silo): `characterized_levers: []`. 14 errors total. Total failure confirmed.
- gpt-5-nano (run 57, sovereign_identity): `characterized_levers: []`. 10 errors total. Total failure confirmed.

**OPTIMIZE_INSTRUCTIONS alignment**:

PR #464's description states it updates OPTIMIZE_INSTRUCTIONS to document lessons from PRs #457–462. The update adds the UUID-at-end approach as a known mitigation but fails to document the critical risk: small models use positional heuristics to populate `lever_id`. The `OPTIMIZE_INSTRUCTIONS` entry at lines 91–92 warns about UUID *format* ("Short hex prefixes and integer indices both caused matching failures... keep the full UUID") but is completely silent about UUID *position* — the exact gap this PR exploited. A reader of the current OPTIMIZE_INSTRUCTIONS would find no warning against moving the UUID to a less prominent position.

---

## New Issues

**Introduced by PR #464:**

1. **llama3.1 total failure (B1 + B2)**: Positional heuristic causes llama3.1 to return lever names as `lever_id`; strict UUID-key lookup drops all characterizations. 0/35 levers enriched across all 5 plans. Root cause: `enrich_potential_levers.py:240–247` (UUID last) + `enrich_potential_levers.py:276` (no name fallback).

2. **gpt-5-nano severe regression (B1 + B2)**: Same mechanism as llama3.1 but with partial compliance. 3/5 plans total failure, 2/5 plans partial success. 25/35 levers lost.

3. **gpt-oss-20b minor regression (B1)**: One plan (parasomnia) had 3 levers returned with names instead of UUIDs. 3/35 levers lost.

4. **Haiku phantom errors slightly increased**: 7 → 11 fabricated-UUID phantom entries. The "Return exactly N" instruction had no measurable effect. Real levers remain correctly enriched (35/35 → 34/35 with 1 `incomplete`).

5. **Silent failure mode exposed**: llama3.1 and gpt-5-nano show `status: "ok"` in `outputs.jsonl` with `calls_succeeded: 2`, yet `characterized_levers: []`. There is no `partial_recovery` event for the enrich step (unlike the identify step). A plan with 0 enriched levers looks identical to a fully successful plan in the runner events log.

**Surfaced by PR #464 (pre-existing gaps now made visible):**

6. **OPTIMIZE_INSTRUCTIONS missing position-risk warning**: The existing entry warns about UUID *format* (short prefixes, integers) but says nothing about UUID *position* affecting small-model structured-output matching. This gap should have prevented PR #464 from being attempted in its current form.

7. **No name-to-UUID fallback in matching code (B2)**: `enrich_potential_levers.py:276` performs a strict UUID-key lookup with no name-based recovery path. This is a pre-existing gap that becomes critical under PR #464's format change.

---

## Verdict

**NO**: PR #464 introduces critical regressions (llama3.1: 100% → 0%, gpt-5-nano: 100% → 29%) with no confirmed benefit. The UUID leakage fix — the PR's stated purpose — cannot be verified in the after runs because the two models that previously had leakage now produce no characterizations at all. The three models that remain at 100% had no UUID leakage before this PR either. The net result is a 26% reduction in total lever characterizations (64 levers lost) with zero measurable improvement in output quality.

---

## Recommended Next Change

**Proposal**: Revert `lever_details_for_prompt` to put `Lever ID: {uuid}` as the first line (restoring the PR #457 baseline format). Retain the two safe changes from PR #464: the positive-framing system prompt addition, and the `OPTIMIZE_INSTRUCTIONS` update (but extend it with a UUID position-risk warning).

**Evidence**: Both the insight and code review independently confirm the regression mechanism:
- `enrich_potential_levers.py:240–247` — UUID at last line causes small models to return `Name:` field value as `lever_id`.
- `enrich_potential_levers.py:276` — strict UUID-key lookup drops all name-returns as `unknown_lever_id`.
- Confirmed in actual output files: `history/4/55_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` (llama3.1, all 7 lever names as errors); `history/4/57_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` (gpt-5-nano, all 5 lever names as errors).
- The PR #457 baseline (runs 27–33) had 100% characterization across all 7 models (245/245). This is the known-good state to return to.

**Verify**: In the next experiment (after revert):
- **llama3.1**: Confirm all 5 plans return 35/35 characterized levers with 0 `unknown_lever_id` errors (was 35/35 in runs 27). Specifically verify gta_game (run 27 had 8/8) and silo (run 27 had 7/7).
- **gpt-5-nano**: Confirm all 5 plans return 35/35 levers with 0 errors (was 35/35 in runs 29).
- **gpt-oss-20b**: Confirm parasomnia recovers to 8/8 levers (was 8/8 in run 28 per analysis 60 baseline).
- **haiku**: Confirm phantom error count returns to ≤7 (was 7 in run 33). Watch for `incomplete` count — must be 0 (was 0 in run 33).
- **UUID leakage in llama3.1 synergy/conflict**: After revert, llama3.1 will again produce characterizations. Count UUID occurrences in synergy/conflict text across all 5 plans. Baseline from run 27 was 15 occurrences. If the positive-framing addition from PR #464 is retained, it may reduce this; if it stays at 15, the per-batch UUID leakage remains open for the next fix attempt.
- **Gemini, qwen3, gpt-4o-mini**: Confirm 35/35, 0 errors, no regressions (these were unaffected by PR #464).

**Risks**:
- **UUID leakage regresses to PR #457 state** (15 occurrences in llama3.1): This is the accepted trade-off for the revert. It is strictly better than 0 characterized levers. Retaining the positive-framing system prompt addition ("always refer to other levers by their name") may partially reduce leakage even with the UUID back at first position; watch this in the verification run.
- **Retained positive-framing conflicts with UUID at first line**: The system prompt instruction "write 'Policy Advocacy Strategy', not an identifier" combined with `Lever ID:` being the first visible item in the block might confuse some models. If qwen3 or gemini shows new leakage regression after the revert + retained positive framing, consider whether to keep or drop that addition.
- **Exact-count instruction removal**: The synthesis recommends not retaining "Return exactly {N}" in the user prompt (it's redundant with the system prompt's "one per lever" wording and had no measurable effect). Removing it reduces prompt noise.

**Prerequisite issues**: None. The revert is a one-line change that restores known-good behavior independently of any other pending work.

---

## Backlog

**Resolved by PR #457 (confirmed in before runs, no longer active):**

- ~~Cross-batch UUID copying into synergy/conflict~~ (gemini, gpt-oss-20b): Fully resolved. Confirmed 0 occurrences in runs 32 and 28. Remove from backlog.

**Items to ADD (new from this analysis):**

- **UUID_position_risk** (documentation, HIGH): Add to `OPTIMIZE_INSTRUCTIONS` known-problems section: small models (llama3.1, gpt-5-nano) use positional heuristics to populate `lever_id` — the first item in each block becomes the identifier. Moving UUID to any non-first position causes 100% matching failure for these models. Keep `Lever ID: {uuid}` as the first line of `lever_details_for_prompt`; use other techniques (PR #457's full-context UUID removal, prompt framing) to reduce leakage into free-text fields.
- **name_fallback** (code, MEDIUM): Add a `name → lever_id` reverse map at `enrich_potential_levers.py:218` and a name-based fallback at `enrich_potential_levers.py:276`. This provides belt-and-suspenders recovery if any future prompt change causes a model to return lever names instead of UUIDs. Independent of the revert but pairs well with it as a follow-up.
- **enrich_partial_recovery_guard** (observability, LOW): Add a `partial_recovery` event emission for `enrich_potential_levers` in `runner.py` (analogous to the existing one at line 577 for `identify_potential_levers`). PR #464 exposed that 0-characterization runs show `status: ok` with no warning in events logs.

**Still open (existing backlog):**

- **B_uuid_same_batch** (content quality, HIGH): llama3.1 still has ~15 UUID occurrences in synergy/conflict text after revert (from per-batch `lever_details_for_prompt`). The positive-framing addition from PR #464, if retained, may partially address this. If UUID leakage persists at ≥10 after the revert, add a post-process regex strip (`r'\b[0-9a-f]{8}-...\b'`) from `synergy_text`/`conflict_text` as a fallback.
- **haiku_phantom_entries** (noise, LOW): haiku generates 7–11 extra `LeverCharacterization` objects with fabricated UUIDs (correct levers still enriched 35/35). A `max_items` constraint in the response schema, or a code-level count check, could cap this. Deferred.
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` (from identify step) propagate into enriched descriptions. Pre-existing. Belongs in identify step.
- **N_gpt_oss_slow** (operational): gpt-oss-20b timed out on parasomnia in multiple runs. Investigate or raise timeout threshold.
- **B5_partial_recovery_threshold** (operational noise): `partial_recovery` warning fires for successful 2-call runs in identify step. Threshold `< 3` → `< 2` in `runner.py:131`.
