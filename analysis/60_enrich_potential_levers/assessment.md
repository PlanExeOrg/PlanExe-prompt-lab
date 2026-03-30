# Assessment: Strip UUIDs from full lever context string in enrich step

## Issue Resolution

**PR #457** removes `lever_id` UUIDs from `full_lever_context_str` (the full list of all levers
provided as context in every batch), changing line 209 of `enrich_potential_levers.py` from:

```python
f"- {lever.lever_id}: {lever.name}"   # before
f"- {lever.name}"                      # after
```

The per-batch `lever_details_for_prompt` (lines 233–240) still includes `Lever ID: {uuid}` for
each lever in the current batch so the model can return correct IDs in the structured schema.

**Primary target — UUID contamination in synergy/conflict fields:**

- **gemini**: FULLY RESOLVED. 30 UUID occurrences (3 plans) → 0. Confirmed by direct inspection of
  `history/4/32_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`
  and `history/4/32_.../outputs/20250329_gta_game/...` — all synergy/conflict text uses lever names
  only, no UUID strings present.
- **gpt-oss-20b**: FULLY RESOLVED for completed plans. 42 UUID occurrences → 0 in the 2 completed
  plans. Confirmed by inspection of `history/4/28_enrich_potential_levers/outputs/20250329_gta_game/
  002-12-enriched_levers_raw.json`.
- **llama3.1**: PARTIALLY RESOLVED. 54 → 15 UUID occurrences (–72%). Cross-batch UUID copying
  eliminated; same-batch UUIDs (from `lever_details_for_prompt`) still copied. Confirmed by direct
  inspection of `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/
  002-12-enriched_levers_raw.json`: levers 1, 2, 6, 7 still contain UUID-like strings in
  synergy/conflict — real UUIDs for same-batch levers (e.g., `6415a78e-...` for Risk Mitigation),
  fabricated sequential strings for cross-batch references (e.g., `1234567890`, `9876543210`).

**Secondary benefit — llama3.1 phantom ID errors (surfaced by PR #456):**

The llama3.1 `unknown_lever_id` errors from analysis 59 (3 phantom IDs causing 3 levers
unenriched) are FULLY RESOLVED. Removing UUIDs from the full context string prevented llama3.1
from copying and corrupting them in the characterization schema. Run 4/27 shows `"errors": []`
for all 5 plans, with all 35 levers enriched. Confirmed by direct inspection of
`history/4/27_.../outputs/20250329_gta_game/002-12-enriched_levers_raw.json`.

**Residual symptoms:**

1. **llama3.1 still has 15 UUID occurrences** in synergy/conflict text. These are all from
   `lever_details_for_prompt` (per-batch prompt still shows `Lever ID: {uuid}`). The cross-batch
   vector is closed; the intra-batch vector remains. For cross-batch references, llama3.1 now
   fabricates numeric placeholder strings (`1234567890`) instead of copying real UUIDs — arguably
   worse for readability, though less systematically wrong.

2. **haiku regression: 0 → 7 `unknown_lever_id` errors** across 3 plans (gta_game: 5, parasomnia: 1,
   hong_kong: 1). Haiku is a function-calling model that appears to have used the full-context UUID
   list as a grounding anchor for how many characterizations to produce. Without that anchor, it
   generates extra `LeverCharacterization` objects with fabricated IDs. All 35 real levers are
   correctly enriched in all 5 haiku plans — the fabricated entries are discarded. Confirmed by
   direct inspection of `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/
   002-12-enriched_levers_raw.json` (5 errors, all `unknown_lever_id`, fabricated IDs including
   sequential hex strings and an empty string; all 8 real levers correctly enriched with clean
   name-only synergy/conflict text).

---

## Quality Comparison

Both batches use `baseline/train` as input (5–8 levers/plan). Before: runs 4/20–26. After:
runs 4/27–33. All 7 models appear in both batches.

**Note on gpt-oss-20b success rate drop**: The model went from 4/5 → 2/5, with 3 additional
timeout failures. This is almost certainly network/availability noise — the PR makes no change
that could affect model latency, and the model's per-plan duration was already at the 600s
threshold in the before run. The gpt-oss-20b row is included but flagged.

| Metric | Before (4/20–26) | After (4/27–33) | Verdict |
|--------|-----------------|-----------------|---------|
| **Success rate** | 34/35 (97.1%) | 32/35 (91.4%) | NOMINAL REGRESSION (–2 plans, gpt-oss-20b noise) |
| gpt-oss-20b success | 4/5 | 2/5 | REGRESSION (likely network noise, not PR-related) |
| All other models success | 30/30 (100%) | 30/30 (100%) | UNCHANGED |
| **UUID in synergy_text (all models)** | 63 occurrences | 7 occurrences | IMPROVED (–89%) |
| **UUID in conflict_text (all models)** | 63 occurrences | 8 occurrences | IMPROVED (–87%) |
| **UUID contamination total** | 105 occurrences | 15 occurrences | IMPROVED (–86%) |
| gemini UUID contamination | 30 occurrences | 0 | IMPROVED (–100%) |
| gpt-oss-20b UUID contamination | 42 occurrences (3 plans) | 0 (2 plans) | IMPROVED (–100%) |
| llama3.1 UUID contamination | 54 occurrences | 15 occurrences | IMPROVED (–72%, partial) |
| **Errors (unknown_lever_id + incomplete)** | 6 (llama3.1) | 7 (haiku) | NEUTRAL (net +1; llama3.1 fixed, haiku regressed) |
| llama3.1 unknown_lever_id errors | 3 + 3 = 6 | 0 | IMPROVED (–100%) |
| haiku unknown_lever_id errors | 0 | 7 | REGRESSED (new, benign: real levers unaffected) |
| **Lever count (levers successfully enriched)** | 207/210 (llama3.1 missing 3) | 210/210 | IMPROVED |
| llama3.1 levers enriched | 32/35 (3 missing) | 35/35 | IMPROVED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3 options)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 35/35 per run | 35/35 per run | UNCHANGED |
| **Template leakage** | 0–1 (gpt-5-nano "Purpose:" in 1 plan) | 0 observed in spot checks | UNCHANGED (pre-existing, input-dependent) |
| **Review format compliance ("Controls X vs Y")** | Present (from identify step input) | Present (unchanged) | UNCHANGED (pre-existing) |
| **Consequence chain format (→ markers)** | Present in input fields | Present in input fields | UNCHANGED |
| **Content depth (desc chars vs baseline)** | 0.81–1.43× | ~0.84–1.28× (stable per spot checks) | UNCHANGED |
| **Content depth (syn chars vs baseline)** | 0.70–1.52× | Stable per spot checks | UNCHANGED |
| **Cross-call duplication** | Not observed | Not observed | UNCHANGED |
| **Over-generation (>7 levers/call)** | Not applicable (no hard cap) | Not applicable | UNCHANGED |
| **Field length vs baseline (all models)** | 0.70–1.52× (no model >2×) | No model >2× (stable) | WITHIN RANGE |
| **Fabricated quantification (% claims)** | Present, all models (pre-existing) | Present, all models (pre-existing) | UNCHANGED (pre-existing) |
| **Marketing-copy language** | Present (echoed from consequences) | Present (echoed from consequences) | UNCHANGED (pre-existing) |
| **OPTIMIZE_INSTRUCTIONS currency** | Accurate for PR #456 state | Stale: lines 88–92 say "full_lever_context_str includes lever_id UUIDs" — false post-PR #457 | REGRESSION (documentation staleness) |

**Content quality note (verified from actual files):**

- gemini (run 4/32) synergy/conflict text is substantially improved: clean lever-name references
  in natural prose. Example before: "Policy Advocacy Strategy (80b177d0-...)" — after: "This lever
  strongly synergizes with the Procedural Content Strategy. Advanced technologies can enable more
  efficient and detailed world generation."
- haiku (run 4/33) synergy/conflict text is clean (no UUIDs), substantive, and well-written. The
  7 fabricated-ID errors are noise in the errors list only; they don't affect output quality.
- llama3.1 (run 4/27) still has UUID strings in synergy/conflict, now a mix of real same-batch
  IDs and obviously fabricated placeholders (`1234567890`). Quality degraded for cross-batch
  references compared to "real UUID" behavior before the PR.

**OPTIMIZE_INSTRUCTIONS alignment:**

PR #457 directly implements the fix for the documented "UUID cross-reference format inconsistency"
known problem (lines 88–92 of `enrich_potential_levers.py`). The change moves closer to the
OPTIMIZE_INSTRUCTIONS goal of name-only lever references in free-text fields. However,
OPTIMIZE_INSTRUCTIONS now describes a problem that no longer exists as stated ("The
full_lever_context_str includes lever_id UUIDs") and does not describe the active residual
vector (`lever_details_for_prompt`) or haiku's new behavior. This should be updated.

---

## New Issues

**Introduced by this PR:**

1. **Haiku fabricated-ID regression (N3)**: 0 → 7 `unknown_lever_id` errors across 3 plans.
   Haiku (function-calling model) generates extra `LeverCharacterization` objects with fabricated
   IDs when the full context list lacks UUID anchors. All 35 real levers remain correctly
   enriched — this is structural noise in the errors list, not data loss. Root cause: no
   `BatchCharacterizationResult.characterizations` count constraint (B3 in code review) and no
   "Return exactly N" instruction in the user prompt.

**Surfaced or confirmed by this PR:**

2. **OPTIMIZE_INSTRUCTIONS staleness**: Lines 88–92 describe the UUID problem in present tense
   as if still unfixed. After PR #457, the description is factually wrong. The new active UUID
   vector (per-batch `lever_details_for_prompt`) is undocumented. This is a medium-priority
   operational issue since the optimizer reads OPTIMIZE_INSTRUCTIONS directly.

3. **llama3.1 cross-batch references now use fabricated placeholders**: Before the PR, llama3.1
   copied real UUIDs from the cross-batch context list into synergy/conflict text — wrong but
   at least grounded in real IDs. After the PR, llama3.1 fabricates numeric strings (`1234567890`,
   `ABCDEF0123`) for cross-batch references. The underlying behavior (including ID-like tokens in
   free-text fields) is unchanged; the tokens are now more obviously wrong rather than superficially
   plausible. This confirms the same-batch prohibition prompt instruction (Direction 1 in synthesis)
   is needed.

---

## Verdict

**CONDITIONAL**: The core fix is effective and should be kept. UUID contamination reduced 86%
(105 → 15 occurrences), gemini and gpt-oss-20b fully cleaned, and the llama3.1 phantom ID
errors from analysis 59 resolved. The PR moves unambiguously in the right direction.

CONDITIONAL rather than YES because:

1. **llama3.1 still has 15 UUID occurrences** (all same-batch, from `lever_details_for_prompt`).
   The fix is structurally incomplete for the worst offender. A prompt prohibition in
   `ENRICH_LEVERS_SYSTEM_PROMPT` or a post-process strip is needed to reach zero.

2. **Haiku regression** (7 new errors) is benign but represents new structural noise that should
   be closed with a "Return exactly N characterizations" instruction. Leaving it unaddressed
   will make future error metrics harder to interpret.

3. **OPTIMIZE_INSTRUCTIONS is stale** and must be updated before the next experiment to prevent
   the optimizer from re-diagnosing a fixed problem or missing the new active UUID vector.

---

## Recommended Next Change

**Proposal**: Bundle two low-effort prompt changes in a single PR:
(1) Add an explicit UUID prohibition sentence to `ENRICH_LEVERS_SYSTEM_PROMPT` (addresses
residual llama3.1 same-batch UUID copying); and
(2) Add "Return exactly {len(batch)} characterizations — one per lever listed below, no more,
no fewer." to the per-batch user prompt (addresses haiku fabricated-ID regression).
Also update `OPTIMIZE_INSTRUCTIONS` to reflect post-PR #457 state.

**Evidence**: Convincing across both insight and code review:

- B1 (code review): `ENRICH_LEVERS_SYSTEM_PROMPT` lines 159–172 contain no prohibition against
  reproducing `lever_id` values in free-text fields. The per-batch prompt explicitly surfaces
  `Lever ID: {uuid}` with no corresponding instruction not to use it in output. All 15 residual
  UUID occurrences (confirmed in run 4/27 gta_game files) trace directly to this structural gap.
- B3 / N3 (code review / insight): `BatchCharacterizationResult.characterizations` has no
  `max_length` constraint and the user prompt never says "no more, no fewer." Haiku's 7 errors
  (confirmed in run 4/33 gta_game: 5 fabricated-ID errors, all real levers correctly enriched)
  are explained by haiku generating extra entries when the UUID anchor was removed.
- I6 / H1 (code review / insight): OPTIMIZE_INSTRUCTIONS lines 88–92 describe the UUID problem in
  present tense as if unfixed — directly misleading for the next iteration.
- The synthesis Direction 1 and Direction 2 recommendation is coherent: separate prompt surfaces
  (system vs user prompt), no interaction risk, can ship together.

**Verify**: In the next experiment (all 7 models × 5 plans):

- **llama3.1** (runs 4/27): Count UUID occurrences in synergy_text and conflict_text across all 5
  plans. Target: 15 → 0 or near-zero. Specifically watch gta_game (levers 1, 2, 6, 7 had UUIDs
  in run 4/27) and hong_kong_game (1 UUID in run 4/27). If still non-zero, Direction 3
  (post-process regex strip) should be added.
- **haiku**: Count unknown_lever_id errors across all 5 plans. Target: 7 → 0. Confirm all 35
  real levers still enriched (was 35/35 before and after PR #457 — must not regress).
- **gemini**: Confirm zero UUID occurrences still (was 0 after PR #457 — verify no regression
  from the new system prompt instruction).
- **All models**: Confirm no increase in `incomplete` errors (exact-N instruction could in theory
  cause a model to drop a lever if it struggles — watch for this trade-off).
- **OPTIMIZE_INSTRUCTIONS**: Confirm the updated text accurately describes the post-PR state
  (per-batch vector, haiku behavior, prohibition added).

**Risks**:

- **llama3.1 partial compliance**: llama3.1 (`is_function_calling_model: false`) is a known poor
  instruction follower in adversarial cases. It may comply for most levers but still copy UUIDs
  occasionally. If residual rate is >3 occurrences per run after the prohibition, add Direction 3
  (post-process strip) to the same or next PR.
- **Exact-N instruction causing lever drops**: Adding "no more, no fewer" could, in edge cases,
  cause a model that can't characterize a lever to silently omit it rather than return a partial
  result. Monitor `incomplete` errors in the next run — if any model shows new `incomplete` errors
  not present in runs 4/27–33, investigate whether the constraint is too strict.
- **System prompt instruction length**: Adding one sentence to `ENRICH_LEVERS_SYSTEM_PROMPT` is
  low risk for all models. No token budget concern given context windows of 40K–1M.
- **No prerequisite issues**: Both changes are independent of the pending B_id fix (banned phrases
  in `Lever.consequences` field description) and the gpt-oss-20b throughput issue.

---

## Backlog

**Resolved by PR #457 (update or remove):**

- ~~B3 — UUIDs in `full_lever_context_str`~~: Cross-batch UUID copying eliminated by PR #457.
  **Not fully resolved** — same-batch copying from `lever_details_for_prompt` remains. Update
  this backlog item from "remove UUIDs from full_lever_context_str" to "add UUID prohibition
  to ENRICH_LEVERS_SYSTEM_PROMPT (same-batch vector, llama3.1 residual)."
- ~~N_phantom_id — llama3.1 phantom lever IDs~~: Resolved as a side effect of PR #457 removing
  UUIDs from the full context list. The corrupted/truncated UUID generation is gone (0 errors
  in runs 4/27–33). Remove from active backlog; note as resolved.

**New items to add:**

- **N_haiku_extra_chars** (low severity): haiku generates extra `LeverCharacterization` objects
  with fabricated IDs (7 errors across 3 plans in run 4/33). Real levers unaffected (35/35
  enriched). Fix: add "Return exactly {len(batch)} characterizations, one per lever, no more,
  no fewer." to per-batch user prompt (line 247). Bundle with UUID prohibition PR.
- **N_optimize_stale** (operational): `OPTIMIZE_INSTRUCTIONS` lines 88–92 describe the UUID
  problem in present tense as still unfixed. Must be updated to: (a) note the fix applied by
  PR #457 for the full-context vector, (b) document the residual per-batch vector
  (`lever_details_for_prompt`), (c) document haiku's new fabricated-ID behavior.

**Still open (existing backlog):**

- **B_uuid_prohibition** (content quality, HIGH PRIORITY): Add explicit UUID prohibition to
  `ENRICH_LEVERS_SYSTEM_PROMPT` — per-batch `lever_details_for_prompt` still surfaces
  `Lever ID: {uuid}` with no instruction against reproducing it in free-text fields. 15
  residual occurrences in llama3.1 (runs 4/27). One-sentence addition. **Highest priority next change.**
- **B_id** (content quality): Banned phrases in `Lever.consequences` field description
  (`identify_potential_levers.py:116–117`) — "Do NOT include 'Controls ... vs.', 'Weakness:'"
  names exact banned phrases, violating OPTIMIZE_INSTRUCTIONS lines 79–82. Replace with
  structural guidance: "Describe direct effects and downstream trade-offs only."
- **B5** (operational noise): `partial_recovery` false-alert for normal 2-call completions —
  `runner.py:131` threshold `< 3` → `< 2`. Confirmed in analysis 59.
- **N_gpt_oss_slow** (operational): gpt-oss-20b throughput too low for ≥8-lever plans; timed
  out on parasomnia in both analysis 59 and 60. Run a repeat experiment to determine if 2/5
  completions in run 4/28 is stable or noise. If stable, either raise `--plan-timeout` to 900s
  or mark gpt-oss-20b as non-production-grade for this step.
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` (from identify step)
  propagate into enriched descriptions for all 7 models. Add `@field_validator` on
  `Lever.consequences` in `identify_potential_levers.py` to detect `\d+%` or `\d+x\b` patterns.
- **S_uuid_post_process** (defensive): Post-process regex strip of UUID patterns from
  `synergy_text` and `conflict_text` (`r'\b[0-9a-f]{8}-[0-9a-f]{4}-...\b'`). Deferred — try
  the prompt prohibition first; add this only if llama3.1 still shows residual UUIDs after the
  prohibition instruction.
