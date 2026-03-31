# Assessment: Use 6-char lever ID prefix, positive framing, and exact-count instruction

## Issue Resolution

**PR #460** introduces three changes to `enrich_potential_levers.py`:

1. **6-char prefix** — Replace full UUIDs with `lever.lever_id[:6]` in `lever_details_for_prompt`.
   Build a `prefix_to_full` mapping for response parsing. Eliminates the primary source of UUID
   contamination for text-completion models (llama3.1) that copy verbatim from prompt text.

2. **Positive framing** — Add "refer to other levers by their name" instruction to the system
   prompt (replacing the negative prohibition from PR #458, which backfired on llama3.1).

3. **Exact-count instruction** — "Return exactly N characterizations — one per lever, no more,
   no fewer." Targeted at haiku's fabricated-ID extra entries.

**Was the issue resolved?**

**UUID contamination — YES, fully.** Before PR #460 (runs 4/27–33, PR #457 baseline), llama3.1
produced 32 contamination instances (20 full UUIDs + 12 `(lever ID: XXXX)` placeholders) in
synergy_text and conflict_text. After PR #460 (runs 4/41–47), total contamination is **0 across
all 7 models and all 5 plans**.

Verified directly in output files:
- `history/4/41_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  llama3.1 synergy/conflict text references levers by name only — "Procedural Content Strategy",
  "Risk Mitigation Strategy" — no UUIDs or placeholders. Compare to run 27 (same plan, same model)
  where `synergy_text` contained `(lever ID: 7a5e2c4f-6d3b-45f8-a9ab-f1a0ddfcf9fa)` and
  `conflict_text` contained `(lever ID: 6415a78e-...)`. Confirmed clean.
- `history/4/42_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  gpt-oss-20b (was not a contamination offender in runs 4/27–33 either) also clean.

**Haiku fabricated-ID regression — NOT fixed, made significantly worse.** Before PR #460, haiku
had 7 `unknown_lever_id` errors (from PR #457). After PR #460, haiku has **43 errors** (+514%).
The exact-count instruction from PR #460 (identical to PR #458's instruction that had previously
reduced haiku to 2 errors) cannot overcome the regression introduced by the 6-char prefix.

Verified directly:
- `history/4/47_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  24 `unknown_lever_id` errors with IDs: `d9e2f1`, `e8f4g2`, `f2h5i3`, `g3i6j4`, `h4j7k5`, …,
  `b3c6d4`. These follow a sequential alphabetical pattern and contain non-hex characters (g, h, j,
  k, l, etc.). None match the real lever prefixes (`278aac`, `3059cf`, `b35d92`, `ccd487`, etc.).
  The 7 real levers (Social Control Mechanism, Ethical Oversight Framework, etc.) are correctly
  enriched with full, substantive content.

**Root cause of haiku regression (confirmed):** `LeverCharacterization.lever_id` field description
at `enrich_potential_levers.py:136` reads `"The 6-character identifier of the lever"` — no
example, no hex constraint, no instruction to copy from the prompt. Haiku's function-calling JSON
generation pathway pattern-completes the short open-ended field with sequential strings rather
than reading the actual 6-char prefix from the prompt. The 36-char full UUID was distinctive
enough for haiku to copy correctly; the 6-char prefix is not.

**Residual symptoms:**
- llama3.1 has 2 minor new errors (1 `unknown_lever_id` + 1 `incomplete`) in hong_kong_game run 41.
  34/35 levers still enriched. Low severity.
- Haiku's 43 errors are all fabricated extra entries — all 35 real levers per plan are correctly
  enriched and not lost. Functionally harmless, but generates significant log noise and would
  complicate future error-rate tracking.

---

## Quality Comparison

Before = runs 4/27–33 (PR #457 baseline, analysis 60). After = runs 4/41–47 (PR #460, analysis 62).
All 7 models appear in both batches. gpt-oss-20b had 2/5 plans in before (3 timeouts, network noise);
5/5 in after.

| Metric | Before (4/27–33) | After (4/41–47) | Verdict |
|--------|-----------------|-----------------|---------|
| **Success rate (plans completed)** | 32/35 (91.4%) — gpt-oss-20b 2/5 | 35/35 (100%) | **IMPROVED** |
| gpt-oss-20b plan completions | 2/5 (3 timeouts) | 5/5 | **IMPROVED** |
| All other models success | 30/30 (100%) | 30/30 (100%) | UNCHANGED |
| **UUID contamination total** | 32 (20 full UUIDs + 12 placeholders, all llama3.1) | 0 | **IMPROVED (–100%)** |
| llama3.1 UUID contamination | 32 | 0 | **IMPROVED (–100%)** |
| Other models UUID contamination | 0 | 0 | UNCHANGED |
| **Total errors (unknown_lever_id + incomplete)** | 7 (haiku) | 45 (43 haiku + 2 llama3.1) | **REGRESSED (+543%)** |
| haiku unknown_lever_id errors | 7 | 43 | **REGRESSED (+514%)** |
| llama3.1 errors | 0 | 2 | **REGRESSED (new)** |
| LLMChatError entries (events.jsonl) | 0 | 0 | UNCHANGED |
| **Characterized levers (real, non-error)** | 245 (gpt-oss-20b 2 plans only) | 244 (5/5 for all models) | APPROX UNCHANGED |
| Bracket placeholder leakage | 0 | 0 | UNCHANGED |
| Option count violations (≠3 options) | 0 | 0 | UNCHANGED |
| Lever name uniqueness (unique/total) | 35/35 per run | 35/35 per run | UNCHANGED |
| Template leakage | 0 | 0 | UNCHANGED |
| Review format compliance ("Controls X vs Y") | Present (from identify step) | Present (unchanged) | UNCHANGED |
| Consequence chain format (→ markers) | Present in input fields | Present in input fields | UNCHANGED |
| **Avg description length** | 518 chars | 523 chars | UNCHANGED (+1%) |
| **Avg synergy_text length** | 325 chars | 325 chars | UNCHANGED |
| **Avg conflict_text length** | 327 chars | 340 chars | UNCHANGED (+4%) |
| **Haiku description length** | 568 chars (1.17× baseline) | 673 chars (1.39× baseline) | SLIGHT REGRESSION |
| Field length ratio vs baseline (all models) | max 1.17× | max 1.39× (haiku) | WITHIN RANGE (< 2×) |
| Cross-call duplication | Not observed | Not observed | UNCHANGED |
| Over-generation (>7 levers/call) | Not applicable | Not applicable | UNCHANGED |
| **Fabricated quantification (% claims)** | Present (pre-existing, from identify step) | Present (pre-existing) | UNCHANGED |
| **Marketing-copy language** | Present (pre-existing) | Present (pre-existing) | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS currency** | Stale: still references full-UUID per-batch prompt as active vector | Updated: documents positive-framing lesson and 6-char prefix approach | **IMPROVED** |

**Content quality note (verified from files):**

llama3.1 (run 41) synergy/conflict text is substantially cleaner — natural prose references to
lever names ("This lever has strong synergy with the Procedural Content Strategy, as both aim to
leverage advanced technologies...") with no UUID noise. This is the main content quality win.

haiku (run 47) synergy/conflict text is also clean (no UUIDs), well-written, and substantive.
The 43 fabricated-ID errors appear only in the `errors` list and do not degrade any enriched
lever's content. Haiku description length grew to 1.39× baseline (673 chars vs 484 baseline).
Below the 2× warning threshold but upward-trending.

**OPTIMIZE_INSTRUCTIONS alignment:**

PR #460 updates `enrich_potential_levers.py:88–94` to document (a) the UUID fix, (b) the
positive-framing lesson from PR #458, and (c) the current 6-char prefix approach. The update is
accurate for the changes made. **Gap**: the entry does not yet document the haiku regression
introduced by 6-char prefixes on function-calling models — future iterations could re-apply the
same mistake. Adding this lesson is high priority (see code review C4/I4).

---

## New Issues

**Introduced by PR #460:**

1. **Haiku 6-char prefix fabrication (HIGH)**: Haiku's function-calling structured output
   generation pattern-completes the vague `lever_id` field description ("The 6-character identifier
   of the lever") with sequential non-hex strings (d9e2f1, e8f4g2, f2h5i3, …) rather than copying
   the actual prefix from the prompt. PR #458 had already reduced haiku errors from 7 → 2 using
   the exact-count instruction with full UUIDs. PR #460 adds the same exact-count instruction
   but switches to 6-char prefix, causing haiku errors to jump from 2 → 43. The 6-char prefix
   is the direct and sole cause of this regression.

2. **llama3.1 minor new errors (LOW)**: 2 new errors (1 `unknown_lever_id` + 1 `incomplete`) in
   hong_kong_game (run 41). 34/35 levers still enriched. This may be prompt-sensitivity noise
   from the new positive-framing instruction or an edge case in prefix matching.

**Surfaced by PR #460:**

3. **`LeverCharacterization.lever_id` field description inadequate**: The description
   `"The 6-character identifier of the lever"` at `enrich_potential_levers.py:136` is the root
   cause of haiku's fabrication. When the identifier scheme changed from full UUID to 6-char
   prefix, the field description was not updated to anchor the expected format. For function-calling
   models, the field description drives structured-output generation more than the prompt format.

4. **No model-type awareness in identifier strategy**: Text-completion models (llama3.1) and
   function-calling models (haiku, gpt-4o-mini) have fundamentally different failure modes.
   Text-completion models copy verbatim from prompt text → 6-char prefix prevents UUID leakage.
   Function-calling models generate structured JSON via tool-use → 6-char prefix is too short to
   anchor correctly. Using the same identifier strategy for both model types trades one regression
   for another.

---

## Verdict

**CONDITIONAL**: Keep the 6-char prefix for text-completion models; address haiku before treating
as best.

**The core win is real and clean**: UUID/placeholder contamination in llama3.1 is fully eliminated
(32 → 0). This is the primary outstanding issue from analysis 60, and it is resolved by a
structurally sound fix. The positive-framing instruction is also a documented improvement over
PR #458's negative prohibition approach.

**The haiku regression is not acceptable as a stable state**: 43 errors per run vs 7 in PR #457
is a 514% increase in structural noise. PR #458 had already demonstrated 2 errors was achievable
for haiku with full UUIDs + exact-count instruction. PR #460 undoes that progress entirely via the
6-char prefix. While all 35 real levers are correctly enriched, leaving 43 fabricated-ID entries in
every haiku run makes error-rate metrics unreliable and clutters the `errors` list.

**Conditions for YES:**

1. Add model-type-aware identifier strategy: use full UUIDs for function-calling models
   (`is_function_calling_model=True`), 6-char prefix only for text-completion models. ~10 lines
   of code. Evidence from PR #458 shows this restores haiku to ~2 errors. No experiment needed
   for the non-haiku models (no change for them).

2. Update `LeverCharacterization.lever_id` field description to anchor the expected format:
   "The exact identifier shown before the lever name above — copy it exactly as shown, do not
   generate a new value." This guards both function-calling and text-completion model edge cases.

3. Update `OPTIMIZE_INSTRUCTIONS` to document the haiku-specific degradation pattern under 6-char
   prefixes (prevents future re-introduction of this regression).

---

## Recommended Next Change

**Proposal**: Implement model-type-aware identifier strategy in `enrich_potential_levers.py`:
use full 36-char UUIDs for function-calling models (`is_function_calling_model=True`) and retain
the 6-char prefix approach for text-completion models. Bundle with a field description update
for `LeverCharacterization.lever_id` and an `OPTIMIZE_INSTRUCTIONS` documentation fix.

**Evidence**: Strong and multi-source.

- PR #458 demonstrated full UUIDs + exact-count instruction → 2 haiku errors (down from 7).
  PR #460 added the identical exact-count instruction but switched to 6-char prefix → 43 errors.
  The causal factor is isolatable: the only change between PR #458 (2 errors) and PR #460 (43 errors)
  for haiku is the identifier scheme. Full UUID is safe for haiku; 6-char prefix is not.
- UUID contamination (the problem 6-char prefix fixes) was exclusively a text-completion model
  behavior. Haiku never produced UUID contamination in synergy/conflict fields in any run — it
  uses structured tool-call output, not verbatim text copying. The 6-char prefix is solving a
  problem haiku never had.
- `enrich_potential_levers.py:199–208` already probes `probe_llm.metadata.context_window` to
  select batch size. The same pattern applies to `is_function_calling_model` — the attribute is
  on the same `metadata` object. Precedent and infrastructure are in place.
- Both insight and code review files agree on I1/C1 as the highest-priority fix. No dissent.

**Verify in the next experiment run** (all 7 models × 5 plans):

- **haiku (run 47 baseline: 43 errors)**: Count `unknown_lever_id` errors after the fix. Target:
  ≤2 errors (PR #458 demonstrated this is achievable). Confirm all 35 levers enriched. If still
  >5 errors, check whether `is_function_calling_model` is correctly detected for
  `anthropic-claude-haiku-4-5-pinned`.
- **gpt-4o-mini** (another function-calling model): Verify no regression — this model has been
  consistently clean. With full UUIDs restored, confirm no UUID contamination appears in
  synergy/conflict fields (it didn't in earlier runs with full UUIDs).
- **llama3.1 (run 41 baseline: 2 minor errors)**: UUID contamination must remain at 0 (the
  6-char prefix must still apply for non-function-calling models). Watch for the hong_kong_game
  minor errors (1 unknown + 1 incomplete in run 41) — check whether they persist with the
  updated field description.
- **All models**: Confirm total error count drops well below 45. A healthy target is ≤5 total
  errors across all 35 plans × 7 models.
- **OPTIMIZE_INSTRUCTIONS**: Confirm the updated text documents the haiku 6-char regression lesson
  and the model-type-aware fix.

**Risks**:

- **`is_function_calling_model` attribute may be absent**: The probe at `enrich_potential_levers.py:205`
  already uses try/except around `probe_llm.metadata.context_window`. Apply the same defensive
  pattern. Safe default: treat unknown model as text-completion (full UUID is safer — no contamination
  risk; only haiku-style fabrication risk, which we're already handling). Actually, full UUID
  is probably the safer default since function-calling models correctly handle full UUIDs (as PR
  #457 demonstrated).
- **gpt-4o-mini edge case**: gpt-4o-mini is `is_function_calling_model=True`. If it was also
  silent about UUID contamination with full UUIDs (as it was in all previous runs), restoring
  full UUIDs for it is safe. Verify no UUID contamination in gpt-4o-mini synergy/conflict.
- **llama3.1 minor errors from run 41**: The 2 minor errors (hong_kong_game) may be a prompt
  sensitivity artifact from the positive-framing instruction interacting with llama3.1's
  poor instruction-following. Monitor whether these persist; if they do, investigate the
  `prefix_to_full` mapping for edge cases in that plan's lever names.
- **Name-based fallback (I3)**: Not proposed as the primary fix, but worth bundling. Haiku's
  fabricated entries carry correct description/synergy/conflict content — only `lever_id` is
  wrong. A name-based fallback in `prefix_to_full.get()` would silently rescue correct enrichment
  content even when the ID is wrong. Zero prompt change. Implement alongside I1 as defense-in-depth.

**Prerequisite check**: No blocking prerequisites. The model-type-aware fix is independent of
the pending B_id fix (identify step field descriptions) and the runner.py plan timeout issue (B3
in code review).

---

## Backlog

**Resolved by PR #460:**

- ~~B_uuid_prohibition — residual llama3.1 UUID contamination from per-batch lever_details_for_prompt~~:
  The 6-char prefix eliminates all UUID contamination in llama3.1 (32 → 0 in runs 4/41). Remove from
  active backlog. The underlying vector (lever_details_for_prompt) no longer exposes recognizable
  UUIDs to the model.
- ~~N_optimize_stale — OPTIMIZE_INSTRUCTIONS stale post-PR #457~~: PR #460 updates the entry with
  the positive-framing lesson and current fix state. Now accurate. Remove from active backlog.
- ~~N_haiku_extra_chars — haiku fabricated-ID extras (7 errors from PR #457)~~: Partially superseded.
  The PR attempted to fix this via exact-count instruction, but the 6-char prefix made it worse
  (7 → 43). Replace with the new, larger version of this item below.

**New items to add:**

- **B_haiku_prefix_regression (HIGH PRIORITY)**: 6-char prefix causes haiku (and likely
  gpt-4o-mini, untested) to fabricate sequential non-hex strings instead of returning the actual
  prefix from the prompt. Root cause: `LeverCharacterization.lever_id` field description does not
  anchor the expected format; haiku's function-calling pathway pattern-completes the short field.
  Fix: model-type-aware identifier strategy — full UUIDs for `is_function_calling_model=True`,
  6-char prefix for text-completion models. See synthesis I1. Evidence: PR #458 = 2 haiku errors
  (full UUID + exact-count); PR #460 = 43 haiku errors (6-char prefix + exact-count). Difference
  is solely the identifier scheme.
- **B_lever_id_field_desc (MEDIUM)**: `LeverCharacterization.lever_id` field description
  (`enrich_potential_levers.py:136`) is vague: `"The 6-character identifier of the lever"`. For
  function-calling models, this is the primary anchor for the structured output value. Update to:
  `"The exact identifier shown before the lever name above (e.g., '278aac' or a full UUID). Copy
  it exactly as shown — do not generate a new value."` This guards both 6-char prefix and full-UUID
  operating modes.
- **B_optimize_haiku_lesson (LOW)**: `OPTIMIZE_INSTRUCTIONS` (`enrich_potential_levers.py:88–94`)
  documents the UUID fix and positive-framing lesson but does not document the haiku 6-char
  regression. Future iterations may re-introduce 6-char prefix for function-calling models
  without this warning. Add: "6-char prefix degrades function-calling models (haiku): fabricates
  sequential non-hex IDs instead of reading the prompt prefix. Use full UUIDs for
  is_function_calling_model=True models."
- **B_name_fallback (MEDIUM, defensive)**: `prefix_to_full.get(char.lever_id, char.lever_id)` at
  `enrich_potential_levers.py:277` silently discards correct enrichment content when the returned
  ID misses the map. Haiku's fabricated entries have correct description/synergy/conflict — only
  `lever_id` is wrong. Add a name-based fallback: build `name_to_full: dict[str, str]` for the
  batch; on lookup miss, try to match by lever name. Unambiguous for single-lever batches. Pure
  code change, no experiment needed.

**Still open (existing backlog):**

- **B_id** (content quality, identify step): Banned phrases in `Lever.consequences` field
  description (`identify_potential_levers.py:116–117`) — names exact phrases violating
  OPTIMIZE_INSTRUCTIONS lines 79–82. Replace with structural guidance.
- **B5** (operational noise): `partial_recovery` false-alert for normal 2-call completions —
  `runner.py:131` threshold `< 3` → `< 2`. Out of scope for enrich step.
- **N_gpt_oss_slow**: gpt-oss-20b had 3 timeouts in run 4/28 (analysis 60 before batch).
  Run 4/42 (analysis 62) completed 5/5 — suggests the prior timeouts were network noise.
  Monitor; if timeout reappears, raise `--plan-timeout` or flag model as non-production grade.
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` from identify step
  propagate into enriched descriptions for all models. Fix belongs in identify step.
- **B2_closure** (latent, code): `execute_function` closure captures `chat_message_list` by
  name not value at `enrich_potential_levers.py:262`. Safe today (synchronous executor).
  Fix: `messages_snapshot = list(chat_message_list)` before closure definition.
- **B3_timeout** (reliability, runner.py): `with _TPE(max_workers=1)` blocks calling thread on
  `shutdown(wait=True)` even after TimeoutError caught — plan timeout is non-functional.
  Separate PR.
- **S_uuid_post_process** (defensive): Post-process regex strip of UUID patterns from synergy_text
  and conflict_text. Deferred — UUID contamination now eliminated via prompt/identifier approach.
  Keep in backlog as fallback if future prompt changes re-introduce contamination.
