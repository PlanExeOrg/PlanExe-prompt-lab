# Assessment: Wrap lever UUID in XML tags to prevent UUID leakage in free-text fields

## Issue Resolution

**PR #466** targets the residual UUID contamination that remained after PR #457. PR #457
removed UUIDs from `full_lever_context_str` (cross-batch vector), but the per-batch
`lever_details_for_prompt` still contained plain-text `Lever ID: {uuid}` — which llama3.1
copied verbatim into `synergy_text` and `conflict_text` for same-batch levers (15 residual
occurrences in runs 4/27–33).

**Primary change:** `Lever ID: {uuid}` → `<lever>{uuid}</lever>` in `lever_details_for_prompt`.
XML tags signal structured markup; models treat the UUID as metadata rather than prose to copy.

**Secondary changes:**
- Positive framing added to `ENRICH_LEVERS_SYSTEM_PROMPT`: "refer to other levers by their name"
- Exact-count instruction added to both system prompt ("one per lever, no more, no fewer") and
  user prompt ("Return exactly N characterizations — one per lever, no more, no fewer")
- `OPTIMIZE_INSTRUCTIONS` updated to document the XML-tag mitigation and lessons from prior PRs

**Is the issue resolved?**

YES for the primary target. llama3.1 UUID contamination went from 15 occurrences (7 in
synergy_text, 8 in conflict_text) across 2 plans to **0 across all 5 plans** (–100%).
Confirmed by direct inspection of
`history/4/62_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
`"errors": []`, all synergy/conflict text uses lever names in clean prose, zero UUID tokens present.

**Residual symptoms:**

1. **haiku `unknown_lever_id` errors persist** (7 → 5): The exact-count instruction reduced errors
   from 3 plans to 2 plans (gta_game: 5 → 0; parasomnia: 0 → 4; silo: 0 → 1; hong_kong: 1 → 0).
   All 35/35 real levers remain correctly enriched — the 5 remaining errors are discarded fabricated-UUID
   extras. Confirmed: run 4/68, parasomnia shows 4 errors with clearly sequential fabricated IDs
   (`64a2e8f4-5c9e-4a8f-8b8b-1a2b3c4d5e6f`, `c8d7b1f6-4e3a-4b2a-9c7d-8f9e1a2b3c4d`, etc.),
   alongside 8 correctly enriched real levers.

2. **Fabricated % claims in `consequences`** (pre-existing): Models echo fabricated percentages
   from the `identify_potential_levers` step into descriptions (e.g., "30% larger game file size",
   "15% longer development cycles"). Not introduced by this PR. Upstream fix needed.

---

## Quality Comparison

Both batches use `baseline/train` as input (5–8 levers/plan). Before: runs 4/27–33 (after PR #457).
After: runs 4/62–68 (after PR #466). All 7 models appear in both batches.

| Metric | Before (4/27–33) | After (4/62–68) | Verdict |
|--------|-----------------|-----------------|---------|
| **Success rate** | 32/35 (91.4%) | 33/35 (94.3%) | IMPROVED (+1 plan, gpt-oss-20b noise) |
| llama3.1 success | 5/5 | 5/5 | UNCHANGED |
| gpt-oss-20b success | 2/5 | 3/5 | IMPROVED +1 (likely noise, not PR-related) |
| gpt-5-nano success | 5/5 | 5/5 | UNCHANGED |
| qwen3-30b success | 5/5 | 5/5 | UNCHANGED |
| gpt-4o-mini success | 5/5 | 5/5 | UNCHANGED |
| gemini success | 5/5 | 5/5 | UNCHANGED |
| haiku success | 5/5 | 5/5 | UNCHANGED |
| **UUID in synergy_text (llama3.1)** | 7 occurrences / 2 plans | **0** | **IMPROVED (–100%)** |
| **UUID in conflict_text (llama3.1)** | 8 occurrences / 1 plan | **0** | **IMPROVED (–100%)** |
| **UUID contamination (all models, total)** | 15 occurrences | **0** | **IMPROVED (–100%)** |
| gemini UUID contamination | 0 | 0 | UNCHANGED |
| gpt-oss-20b UUID contamination | 0 | 0 | UNCHANGED |
| **haiku unknown_lever_id errors** | 7 (3 plans) | **5 (2 plans)** | IMPROVED (–29%) |
| llama3.1 errors | 0 | 0 | UNCHANGED |
| LLMChatError events | 0 | 0 | UNCHANGED |
| **Levers enriched (all models)** | 210/210 (35×6 plans completed, 2 timeouts) | 210/210 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3 options)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 35/35 per run | 35/35 per run | UNCHANGED |
| **Template leakage** | 0 observed | 0 observed | UNCHANGED |
| **Review format ("Controls X vs Y")** | Present (from identify input) | Present | UNCHANGED |
| **Consequence chain (→ markers)** | Present in input fields | Present | UNCHANGED |
| **Content depth (field lengths vs baseline)** | ~0.84–1.52× (no model >2×) | Stable (no model >2×) | WITHIN RANGE |
| **Cross-call duplication** | Not observed | Not observed | UNCHANGED |
| **Over-generation (>7 levers/call)** | Not applicable | Not applicable | UNCHANGED |
| **Fabricated quantification (% claims)** | Present, all models (pre-existing) | Present, all models | UNCHANGED (pre-existing) |
| **Marketing-copy language** | Present (echoed from consequences) | Present | UNCHANGED (pre-existing) |
| **OPTIMIZE_INSTRUCTIONS currency** | Stale: lines 88–92 described unfixed cross-batch vector | **Updated and accurate** | **IMPROVED** |

**Content quality spot-check (verified):**

- llama3.1 run 4/62, gta_game, lever 1 synergy_text (after): "Technological Integration Strategy
  has strong synergy with Procedural Content Strategy, as both leverage advanced technologies to
  enhance gameplay and world generation..." — clean lever-name prose, no UUID tokens.
- llama3.1 run 4/27, gta_game, lever 1 synergy_text (before): contained `(lever ID: 7a5e2c4f-...)`.
- haiku run 4/68, parasomnia: all 8 real levers correctly enriched with coherent, domain-specific
  synergy/conflict text. The 4 error entries are discarded fabricated-UUID extras, not corruption
  of real levers.

**OPTIMIZE_INSTRUCTIONS alignment:** The updated OPTIMIZE_INSTRUCTIONS (lines 88–96) now
accurately documents both mitigation steps (PR #457 and PR #466), explains the positional
heuristic rationale for keeping the UUID first, and records the lessons from prior failed
approaches (negative prohibitions, hex prefixes, integer indices, UUID-at-end). This is a
net improvement: the optimizer has accurate context for the next iteration.

---

## New Issues

**Introduced by this PR:** None. The XML tag change has no negative side effects on any
of the 7 tested models. The exact-count instruction reduced (not increased) haiku errors.

**Surfaced by this PR:**

1. **Duplicate exact-count instruction** (S2 / code review): Both the system prompt ("Return
   exactly one characterization per lever requested") and user prompt ("Return exactly N
   characterizations") encode the same constraint. For haiku's function-calling interface,
   the abstract system-level instruction may be redundant with or confusing alongside the
   concrete user-level count. The haiku error residual (5 remaining) may be addressable
   by removing the system-level version. Warrants a standalone experiment.

2. **Negative prohibition in `Lever.consequences` field description** (B1 / code review):
   `identify_potential_levers.py:116–119` contains `"Do NOT include 'Controls ... vs.',
   'Weakness:'"` — naming exact banned phrases inside a Pydantic field description sent
   to the LLM. This violates OPTIMIZE_INSTRUCTIONS lines 80–82 ("Do NOT add explicit
   prohibitions naming banned phrases — small models treat the prohibition text as a template
   and copy the banned phrases"). Affects the identify step, not enrich, but the fabricated
   `consequences` text that propagates into enrich descriptions is partly caused by this.

3. **`errors.append` for `unknown_lever_id` pollutes failure signal** (B2 / code review):
   Haiku's extra characterizations are expected model behavior (real levers always enriched),
   but they are appended to `errors` alongside real failures. This is pre-existing but surfaced
   prominently here because haiku errors are now the only non-zero error class.

---

## Verdict

**YES**: PR #466 fully resolves the remaining UUID contamination. The two-PR sequence
(#457 + #466) delivers complete elimination: 105 → 15 → 0 UUID occurrences in synergy/conflict
text across all 7 tested models. No regressions were introduced. haiku's fabricated-ID noise
is slightly reduced and is benign (real levers are always correctly enriched). The OPTIMIZE_INSTRUCTIONS
documentation is now accurate and actionable. The primary goal is achieved without collateral damage.

---

## Recommended Next Change

**Proposal**: Suppress `errors.append` for `unknown_lever_id` events in
`enrich_potential_levers.py:282–283` (one-line deletion). Pair with a rationale comment on
`BatchCharacterizationResult.characterizations` explaining why `max_length` is omitted. No
experiment iteration required — this is a documentation/cleanup change, not a prompt change.

**Evidence**: Convincing and unambiguous.
- All 35/35 real levers are correctly enriched in every haiku run. The 5 remaining
  `unknown_lever_id` entries are discarded fabricated-UUID extras that never enter
  `enriched_levers_map`. They are expected model noise, not failures.
- Confirmed in run 4/68 parasomnia: 4 errors (`64a2e8f4-...`, `c8d7b1f6-...`,
  `f5e9a8b7-...`, malformed `d3c4b5e6-7f8a-9b1a-2c3d-4e5f-6a7b-8c9d-0e1f`),
  alongside 8 correctly enriched real levers with clean synergy/conflict text.
- B2 (code review): appending to `errors` conflates benign over-generation with real batch
  failures, degrading the failure signal for downstream consumers.
- S3 (code review): absence of a rationale comment on `characterizations` risks a future
  maintainer adding `max_length=batch_size`, which would turn expected noise into hard batch
  failures (Pydantic would reject the entire batch response).
- Both insight (C1) and code review (I1/B2/I2) independently recommend the same change.

**Verify**: After the fix, confirm in a standard run:
- haiku `errors` array is `[]` across all 5 plans (was 5 entries in 2 plans after PR #466).
- All 35/35 real levers still enriched for haiku (must not regress).
- No increase in `incomplete` errors for any model (the fix only suppresses `unknown_lever_id`
  noise; genuine missing levers would still appear as `incomplete`).
- `logger.warning` lines still appear in run logs for haiku (debugging signal preserved).

**After the code fix is merged**, pursue Direction 1 from synthesis as the next prompt experiment:
fix the negative prohibition in `Lever.consequences` field description in
`identify_potential_levers.py:116–119`. This is a separate step-level change (affects the
identify step, not enrich) but has multi-step impact: removing the English-specific "Do NOT
include 'Controls ... vs.'" language from the Pydantic schema should reduce template-lock
behavior in small models and improve the `consequences` text that propagates into enrich
descriptions. Replace with positive framing: "Focus on cause-effect relationships and factual
outcomes within the project domain; save critical assessments for the review_lever field."

**Risks**:
- Suppressing `errors.append` is zero-risk — it removes noise only; real enrichment is unaffected.
- Identify-step prompt change requires a full self_improve iteration against
  `identify_potential_levers`. Watch for: any increase in `Controls X vs Y` pattern appearing
  inside `consequences` (the prohibited phrase may disappear without the negative prohibition, or
  it may increase if the prohibition was serving as a weak deterrent for stronger models).
- haiku batch-size hypothesis (insight Q4): errors appear specifically in second batches (shorter
  batches — parasomnia has 8 levers → batch 1: 5 levers, batch 2: 3 levers). Once `errors` is
  clean, a haiku-specific `BATCH_SIZE` override (e.g., 3) could be tested to see if equalizing
  batch sizes eliminates the remaining over-generation structurally.

**Prerequisites**: None. Both the code fix and the identify-step prompt change are independent
of each other and of any outstanding changes.

---

## Backlog

**Resolved by PR #466 (close or update):**

- ~~B_uuid_prohibition (HIGH PRIORITY)~~: Add UUID prohibition to `ENRICH_LEVERS_SYSTEM_PROMPT`
  for per-batch vector. **RESOLVED** — XML tags on `<lever>{uuid}</lever>` achieved the same
  result without a negative prohibition. llama3.1 UUID contamination: 15 → 0. Close this item.
- ~~N_optimize_stale~~: `OPTIMIZE_INSTRUCTIONS` stale after PR #457. **RESOLVED** — PR #466
  updated OPTIMIZE_INSTRUCTIONS (lines 88–96) to document both PRs, the positional heuristic
  rationale, and lessons from failed approaches. Close this item.
- ~~N_haiku_extra_chars (partial)~~: haiku `unknown_lever_id` errors introduced by PR #457
  (7 errors, 3 plans). **PARTIALLY RESOLVED** by PR #466 exact-count instruction (7 → 5 errors,
  2 plans). Update to: "haiku `errors` pollution — suppress `errors.append` for `unknown_lever_id`
  (one-line fix, see Recommended Next Change). haiku still generates 5 extra characterizations
  but they are discarded; errors array just needs to stop counting them as failures."

**New items to add:**

- **B_errors_pollution** (low severity, clear fix): `enrich_potential_levers.py:282–283` appends
  haiku's expected over-generation to `errors`, conflating noise with real failures. Fix: remove
  `errors.append(...)` for `unknown_lever_id`, keep `logger.warning`. Add rationale comment to
  `BatchCharacterizationResult.characterizations` (parallel to `identify_potential_levers.py:188–189`).
  No experiment required; pure code cleanup.
- **S_closure_snapshot** (latent): `execute_function` in `enrich_potential_levers.py:259–266`
  captures `chat_message_list` by reference without a defensive snapshot (contrast with
  `identify_potential_levers.py:317–322` which uses `messages_snapshot = list(...)`). Safe now
  (synchronous executor), but inconsistent and fragile against async refactoring. Fix: add
  `messages_snapshot = list(chat_message_list)` before the closure definition.
- **S_duplicate_count_instruction** (low): System prompt ("one per lever, no more, no fewer")
  duplicates the user prompt ("exactly N characterizations"). May confuse haiku's function-calling
  interface. Warrants a standalone experiment after `B_errors_pollution` is fixed so the haiku
  error delta is measurable without noise.

**Still open (carry forward):**

- **B_id** (content quality, HIGH PRIORITY for identify step): Negative prohibition in
  `Lever.consequences` field description (`identify_potential_levers.py:116–119`) names
  `'Controls ... vs.'` and `'Weakness:'` — violates OPTIMIZE_INSTRUCTIONS lines 80–82.
  Replace with positive framing. Requires identify-step experiment iteration.
- **B5** (operational noise): `partial_recovery` false-alert in `runner.py:131` threshold
  `< 3` should be `< 2` for normal 2-call completions.
- **N_gpt_oss_slow** (operational): gpt-oss-20b still unreliable for ≥8-lever plans (2–3/5
  success across runs 4/28, 4/63). Either raise `--plan-timeout` to 900s or investigate
  OpenRouter routing for this model.
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` from the identify
  step propagate into enrich descriptions for all 7 models. Upstream fix in identify step.
- **S_uuid_post_process** (defensive, deferred): Post-process regex strip of UUID patterns from
  `synergy_text`/`conflict_text`. No longer needed as the primary fix (0 UUID contamination
  achieved via XML tags), but retains value as a defensive guarantee for future model additions.
  Keep in backlog; revisit if any new model shows UUID contamination.
