# Assessment: fix: B1 step-gate, medical example, review length cap

## Issue Resolution

**PR #356 targeted three issues:**

### 1. B1 step-gate fix — scope `partial_recovery` to `identify_potential_levers` only
**Status: RESOLVED.** `runner.py:517` now gates on `step == "identify_potential_levers"` before emitting `partial_recovery`. Runs 73–79 show `partial_recovery` events only for this step with correct `expected_calls: 3`. No spurious events from other pipeline steps observed.

Evidence: `history/2/73_identify_potential_levers/events.jsonl` and `history/2/79_identify_potential_levers/events.jsonl` — partial_recovery events appear only for `identify_potential_levers`.

### 2. Medical example — replace urban-planning (Section 106) with IRB/clinical-site overhead
**Status: PARTIALLY RESOLVED — new regression introduced.** The iter 36 domain collision (game-dev example contaminating gta_game) is eliminated. The new examples (agriculture, medical, insurance) do not collide with any of the five test plans.

However, run 73 (llama3.1, gta_game) hard-fails completely: all 7 levers in the first call have 1–2 options instead of 3, triggering `check_option_count` for every lever. Since `len(responses) == 0`, `identify_potential_levers.py:321–322` raises immediately with no retry. Before the example change, run 52 (same model, same plan) produced output with `calls_succeeded: 2`.

The timing is suspicious — the example change is the only variable between runs 52 and 73 for this model×plan combination, but stochastic variation cannot be ruled out from a single run.

Evidence:
- `history/2/73_identify_potential_levers/outputs.jsonl` line 2: `"status": "error", "calls_succeeded": null` — 7 ValidationErrors, options got 1–2 items
- `history/2/52_identify_potential_levers/outputs.jsonl` line 2: `"status": "ok", "calls_succeeded": 2`

### 3. Review length cap — "20–40 words" guidance in section 6
**Status: PRIMARY GOAL ACHIEVED; structural enforcement absent.** Haiku gta_game no longer EOF-fails. Run 79 haiku succeeds with 3 calls and 21 levers, reviews averaging ~355 chars (~58 words). The iter 37 hard failure (~40KB from ~550 chars × 21 levers × 3 calls) does not recur.

However, the guidance is soft (no Pydantic `max_length`). Haiku averages ~58 words vs. the 40-word cap — 45% over the target. The cap works for now because 355 × 21 × 3 ≈ 22KB < 40KB threshold, but any verbosity increase risks recurrence.

Evidence: `history/2/79_identify_potential_levers/outputs.jsonl` line 2: `"20250329_gta_game", "status": "ok", "calls_succeeded": 3`

**Residual symptom:** The "20–40 words" instruction is consistently ignored by haiku. Structural enforcement (truncation in `LeverCleaned` or a Pydantic constraint) is still absent.

---

## Quality Comparison

All 7 models appear in both batches (llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5-pinned). Comparison covers 7 models × 5 plans = 35 plan executions per era.

| Metric | Before (runs 52–58) | After (runs 73–79) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 = 100% | 34/35 = 97.1% | REGRESSED |
| **Hard fails** | 0 | 1 (llama3.1 gta_game) | REGRESSED |
| **Partial recoveries** | 3 (llama3.1 gta_game 2/3, haiku silo 2/3, haiku parasomnia 2/3) | 3 (llama3.1 parasomnia 2/3, haiku hong_kong 2/3, haiku silo 2/3) | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (successful runs)** | 0 | 0 | UNCHANGED |
| **Option count violations (failed run)** | n/a | 7 (llama3.1 gta_game, all levers in call 1 had 1–2 options) | NEW FAILURE |
| **Lever name uniqueness** | High | High | UNCHANGED |
| **Template leakage (verbatim prompt examples)** | None detected | None detected | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | Not used (legacy format) | Not used | UNCHANGED |
| **Consequence chain format ("Immediate → Systemic → Strategic")** | Not consistently used | Not consistently used | UNCHANGED |
| **Content depth — haiku gta_game options** | High quality, 3 calls | High quality, 3 calls, ~300 chars/option | UNCHANGED |
| **Content depth — llama3.1 hong_kong options** | Moderate (~228 chars combined) | Moderate (~183 chars combined) | SLIGHT REGRESSION |
| **Cross-call duplication** | Present (semantic dups pass case-sensitive dedup) | Present | UNCHANGED |
| **Over-generation (>7 levers per call)** | haiku routinely 8+ per call | haiku gta_game 21 levers (3 calls), llama3.1 hong_kong 17 levers | UNCHANGED (handled by downstream dedup) |
| **Field length vs baseline — llama3.1 hong_kong consequences** | ~270 chars (1.1× baseline ~241 chars) | ~270 chars (1.1× baseline) | UNCHANGED |
| **Field length vs baseline — haiku hong_kong consequences** | Not available (haiku run 58 succeeded, data not sampled) | ~680 chars (**2.8× baseline** ~241 chars) | WARNING (>2×) |
| **Field length vs baseline — haiku hong_kong reviews** | ~150 chars avg (baseline) | ~340 chars (2.3× baseline ~150 chars) | WARNING (>2×) |
| **Review length vs 20–40 word target (haiku gta_game)** | ~550 chars/review (iter 37 reference) | ~355 chars avg (~58 words); target: 20–40 words | IMPROVED but non-compliant |
| **Fabricated quantification (haiku gta_game)** | Not sampled for run 58 | 4 claims: "25–30% of development costs", "publisher equity investment (50%)", "government research grants (20%)", "dedicated 50-person live team" | PRESENT (unchanged from prior iters) |
| **Marketing-copy language** | Low | Low | UNCHANGED |
| **Template lock — llama3.1 hong_kong** | "The plan's emphasis on X may overlook Y" (~8/17) | "[Lever] lever overlooks…" / "While [Lever] lever…it overlooks" (~10/17) | UNCHANGED (different pattern, same ~60% rate) |
| **Template lock — haiku gta_game reviews** | Not sampled (run 58 not read) | "X promises/offers Y but introduces/creates Z" + "Options focus/assume/ignore…" (~14/21) | PRESENT |
| **B1 partial_recovery scoped correctly** | No (emitted for all steps) | Yes (only for identify_potential_levers) | IMPROVED |

**Baseline reference:** `baseline/train/20260310_hong_kong_game/002-10-potential_levers.json` — 15 levers, legacy gemini output. Consequences avg ~241 chars (include fabricated Immediate→Systemic→Strategic chains with fabricated %); reviews avg ~150 chars ("Controls X vs Y. Weakness: …" format, also legacy).

**Note on haiku field-length warnings:** haiku hong_kong consequences at 2.8× and reviews at 2.3× are above the 2× warning threshold. The extra length in consequences is substantive (specific multi-clause analysis), but the ratio is high enough to warrant attention. The `EnrichLevers` step downstream adds more detail; 2.8× base already risks bloat.

**Note on fabricated quantification:** The 4 fabricated claims in haiku gta_game (run 79) are not new — this problem predates PR #356. The section 5 prohibition ("NO fabricated statistics or percentages without evidence") is text-only with no structural enforcement.

---

## New Issues

### N1 — llama3.1 gta_game hard fail (CRITICAL regression)
Run 73 (llama3.1, gta_game) fails completely with 0 output. Before (run 52), gta_game succeeded with partial recovery (calls_succeeded: 2). The `check_option_count` validator correctly rejects options < 3, but `identify_potential_levers.py:321–322` raises immediately when `len(responses) == 0` — no retry, no fallback. A single re-run would help determine whether this is causal (example change) or stochastic, but a single data point cannot resolve this. The lack of a retry path converts any stochastic first-call under-generation into a guaranteed hard fail.

### N2 — haiku review template lock ("X but Y") persists structurally
Run 79 haiku gta_game shows ~14/21 reviews following the "X promises/offers Y but introduces/creates Z" structure, with secondary pattern "Options focus/assume/ignore…". This directly mirrors examples 1 and 3 in the prompt, which both use "X, but Y" contrastive framing. OPTIMIZE_INSTRUCTIONS explicitly warns: "No two examples should share a sentence pattern or rhetorical structure." The PR violated this constraint by retaining the insurance example ("reduces…, but a single regional hurricane season") alongside the agriculture example ("stabilizes…, but the idle-wage burden"). Verified in `history/2/79_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

### N3 — haiku hong_kong field lengths above 2× warning threshold
haiku hong_kong consequences average ~680 chars (2.8× baseline ~241 chars) and reviews ~340 chars (2.3× baseline). Above the 2× warning thresholds defined in the analysis criteria. The extra length is substantive but not proportionally more decision-relevant.

### N4 — Soft review length guidance insufficient; no structural enforcement added
The "20–40 words" guidance works for EOF prevention but not compliance. Haiku ignores it at 58 words average. No `max_length` Pydantic constraint or truncation in `LeverCleaned` was added, leaving the fix fragile — any increase in haiku verbosity (e.g., a different plan type or model update) could re-trigger the EOF failure.

### N5 — `partial_recovery` threshold still conflates efficiency with failure (pre-existing, now visible)
Run 73 (llama3.1, parasomnia) fires `partial_recovery` with `calls_succeeded: 2` despite producing 21 levers (above `min_levers=15`). This is a true efficiency completion, not a failure. The `runner.py:517` guard added by the PR correctly scopes the event to the right step, but the `< 3` threshold still cannot distinguish "2 calls succeeded but hit min_levers" from "2 calls succeeded, 3rd call failed."

---

## Verdict

**CONDITIONAL**: The PR achieves its haiku EOF fix (P1) and B1 scoping fix (P6), but introduces one new hard fail — llama3.1 gta_game (run 73) produces zero output where before it produced low-quality but real output. The net reliability balance is -1 plan (35/35 → 34/35). The review length cap is effective but structurally fragile. Keep the PR for the haiku and B1 fixes; a follow-up implementing first-call retry logic (see Recommended Next Change) is required to restore llama3.1 gta_game to at least partial recovery status.

---

## Recommended Next Change

**Proposal:** Add a single retry when the first LLM call produces zero valid responses due to schema validation failure (i.e., `len(responses) == 0` after a Pydantic error). The retry uses an augmented prompt that explicitly re-states the 3-options constraint.

**Evidence:** Both insight (N1, C2, Q3) and code review (B1, I1) identify `identify_potential_levers.py:321–322` as the proximate cause of run 73's hard fail. The code raises immediately when `len(responses) == 0` — no retry, no partial continuation. The same model (llama3.1) produced valid options for gta_game in run 52 (before the example change), so the failure is likely stochastic or prompt-sensitivity-driven rather than a model capability limit. A single retry with emphasis ("CRITICAL: Each lever MUST have exactly 3 options. Fewer than 3 options per lever invalidates the entire response.") is low-risk and directly addresses the failure mechanism. The synthesis (direction #1) provides a concrete implementation sketch at `identify_potential_levers.py:308–327`.

Secondary: also add soft truncation `review=lever.review_lever[:300]` in the `LeverCleaned` constructor (direction #3 in synthesis) to structurally cap review length without risking batch rejection — this converts the fragile soft-guidance fix into a durable code-level protection against EOF recurrence.

**Verify in next iteration:**
- **Primary:** Does llama3.1 gta_game produce output in the next run? Look for `"status": "ok"` or at minimum `"status": "ok", "calls_succeeded": 1` (partial recovery) instead of `"status": "error"`. If still failing, check whether the retry prompt fires (add a log line in the retry branch).
- **Primary:** Does the retry increase total call count for runs where the first call fails? Check `calls_succeeded` in outputs.jsonl — a model that previously hard-failed should now show `calls_succeeded >= 1`.
- **Secondary:** Does review truncation at 300 chars affect downstream output quality for `EnrichLevers`? Check that `EnrichLevers` produces substantive descriptions despite the truncation.
- **Secondary:** Does haiku gta_game still succeed with `calls_succeeded: 3`? Confirm the truncation does not introduce a new failure mode by reducing the semantic content below the minimum needed for the downstream step.
- **Watch for:** Does the retry augmented prompt ("CRITICAL: 3 options...") affect models that already generate correctly? The retry path should only fire when `len(responses) == 0` — non-failing models should never reach it.
- **OPTIMIZE_INSTRUCTIONS:** After implementing the retry, add a note to `OPTIMIZE_INSTRUCTIONS` documenting the first-call hard-fail risk (the `len(responses)==0` path with no retry) and that the fix is a single-retry before raising. This prevents future iterations from re-discovering the same bug.

**Risks:**
- The retry adds one extra LLM call on first-call failure. For models that consistently under-generate (not just stochastically), the retry will also fail, wasting one additional call before raising. This is acceptable — the net effect is one extra failed call vs. zero successful calls.
- If the retry prompt overemphasizes the 3-options constraint, models that previously generated 4+ options (which passes the current validator) may be forced toward exactly 3, losing potentially useful over-generated options. Monitor option counts in the retry path.
- The soft truncation at 300 chars may cut off the last sentence of reviews at grammatically awkward positions. Check that `EnrichLevers` downstream handles truncated input gracefully.
- If llama3.1 gta_game hard-fails consistently across multiple re-runs even with the retry, the root cause may be structural (example domain mismatch confusing llama3.1's options schema) rather than stochastic. In that case, direction #5 from synthesis (prominent "exactly 3 options" at the top of the system prompt) should be tested alongside the retry.

**Prerequisite issues:** None. The retry logic is a code-only change in `identify_potential_levers.py:308–327`. It is independent of any prompt changes. Implementing it does not require B1 (partial_recovery threshold fix) or any template-lock prompt changes to be in place first.

---

## Backlog

**Resolved by PR #356 (remove from backlog):**
- **Haiku gta_game EOF failure (iter 37):** The ~40KB EOF crash from ~550 chars/review × 21 levers × 3 calls is resolved. Run 79 shows 3 successful calls with ~355 chars avg, well below the threshold.
- **B1 step-gate:** `partial_recovery` events now correctly scoped to `identify_potential_levers` only. Previous false-positive events from other pipeline steps are eliminated.
- **Domain collision with game-dev example (iter 36):** Game-dev example removed; no current example overlaps with the gta_game test plan.

**New items added to backlog:**
- **B-NEW: First-call hard-fail with no retry** (`identify_potential_levers.py:321–322`): `len(responses)==0` raises immediately with no retry on first-call Pydantic validation failure. Direct cause of llama3.1 gta_game regression in run 73. Fix: single retry with augmented prompt before raising. **HIGH priority.**
- **B-NEW: Review truncation absent** (`identify_potential_levers.py:352–358`): The 20–40 word review guidance is soft-only; no `max_length` in Pydantic and no truncation in `LeverCleaned`. If haiku verbosity increases, EOF risk recurs. Fix: `review=lever.review_lever[:300]` in `LeverCleaned` constructor. **Medium priority.**

**Remaining items (carried forward):**
- **Template lock — haiku reviews ("X but Y"):** 2 of 3 review examples share "X, but Y" contrastive structure; haiku shows 14+/21 reviews in this pattern. Fix: replace one example (agriculture or insurance) with a non-contrastive structure (conditional or additive framing). Code review I3 / synthesis direction #2.
- **Template lock — llama3.1 reviews ("[Lever] lever overlooks…"):** ~10/17 hong_kong reviews follow this pattern in run 73. Same structural root cause as haiku template lock.
- **Fabricated quantification in haiku options:** 4 fabricated % / count claims in gta_game run 79 despite section 5 prohibition. Section 5 is text-only; no structural enforcement.
- **S1/S5: `partial_recovery` threshold conflates efficiency with failure** (`runner.py:517–523`): `calls_succeeded < 3` fires for 2-call efficient completions as well as true failures. Needs a `failed_calls` counter to disambiguate. Medium effort, metric hygiene only. **Deferred.**
- **B2: `check_option_count` upper bound unenforced** (`identify_potential_levers.py:140–141`): Validator rejects `< 3` but silently accepts `> 3`. Field description says "No more, no fewer." Pragmatic fix: update description to say "At least 3" since over-generation is benign. **Low priority.**
- **S3: English marker examples in `consequences` field description** (`identify_potential_levers.py:100–101`): "Do NOT include 'Controls ... vs.', 'Weakness:'" text in field description is serialized into JSON schema sent to LLM. Conflicts with OPTIMIZE_INSTRUCTIONS warning about English-only validators in non-English contexts. **Deferred.**
- **I4/OPTIMIZE_INSTRUCTIONS: Document first-call hard-fail risk:** OPTIMIZE_INSTRUCTIONS covers verbosity amplification and template lock but not the `len(responses)==0` immediate-raise path. Add a note. Low effort. **Include in the retry fix PR.**
- **S1/I5: `lever_index` dead field** (`identify_potential_levers.py:84–86`): Generated but never transferred to `LeverCleaned`. Wastes ~1 token per lever per call. Cleanup PR. **Low priority.**
- **S2/I6: `strategic_rationale` dead field** (`identify_potential_levers.py:158–163`): ~100 words generated per call (105 calls/iteration ≈ 10,500 wasted words), never consumed downstream. Verify no downstream step reads it, then remove. **Low priority.**
- **B3: Case-sensitive name deduplication** (`identify_potential_levers.py:337`): "Workforce Strategy" and "workforce strategy" both pass through. Minor. Fix with `lever.name.strip().lower()` normalization. **Low priority.**
