# Assessment: feat: consolidate deduplicate_levers with classification and safety valve fix

## Issue Resolution

**What PR #364 targeted** (from `pr_description`):
1. Fix llama3.1 blanket-keep (14–15/15 kept before)
2. Fix gpt-4o-mini over-inclusion (10–12/15 kept before)
3. Narrow the safety valve ("Use primary if you lack understanding" → "Use primary only as a last resort")
4. Add calibration hint ("expect 4–8 absorb/remove in 15 levers")
5. Add concrete secondary lever examples
6. Fix B3: `...` appended unconditionally in compact history
7. Add `OPTIMIZE_INSTRUCTIONS` with 4 known failure modes
8. Add `deduplicate_levers` to the self_improve runner

**Resolution status:**

| Target | Status | Evidence |
|--------|--------|----------|
| llama3.1 blanket-keep | **FIXED** | avg kept: 10.6 → 7.0; two 15/15 cases (silo, hong_kong) eliminated. Verified in `history/3/08_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 8 absorbs, 7 survivors. |
| gpt-4o-mini over-inclusion | **NOT FIXED** | avg kept: 9.4 → 9.6, essentially unchanged. hong_kong_game: 12 kept both before and after. Verified in `history/3/12_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 12 items in `deduplicated_levers`. Model still uses "distinct and essential strategic decision" boilerplate for every lever. |
| Safety valve narrowed | **DONE** | `deduplicate_levers.py:131` now reads "Use 'primary' only as a last resort". Old text confirmed removed. |
| Calibration hint added | **PARTIALLY CORRECT** | Hint added at line 133: "expect 4–8 to be absorbed or removed." Fixed llama3.1 but introduced capping regression on gemini (see New Issues). |
| Concrete secondary examples | **DONE** | System prompt now lists: "marketing campaign timing, internal reporting cadence, team communication tooling, documentation formatting standards." |
| B3 fix (_build_compact_history) | **DONE** | `deduplicate_levers.py:99` correctly uses conditional `...`. |
| B3 fix (all_levers_summary) | **MISSED** | `deduplicate_levers.py:175` still appends `...` unconditionally: `{lever.consequences[:120]}...`. The PR fixed the compact history but left the lever summary with the same anti-pattern. |
| OPTIMIZE_INSTRUCTIONS | **DONE** | Present at `deduplicate_levers.py:26–48`, 4 failure modes documented. |
| Runner integration | **DONE** | `_run_deduplicate` wired in; deduplicate_levers step now active in self_improve runner. |

**Residual symptoms:**
- gpt-4o-mini over-inclusion is entirely unaddressed. The calibration hint alone does not move this model; it appears to evaluate levers in isolation rather than comparatively, producing boilerplate "distinct and essential" justifications regardless of instructions.
- The `all_levers_summary` unconditional `...` (the half-missed B3 fix) affects every run of every model, since `all_levers_summary` is injected into the system message for all per-lever calls.

---

## Quality Comparison

Models in both batches (before = runs 01–07, after = runs 08–14), same 7 models × 5 plans = 35 runs each.

| Metric | Before (runs 01–07) | After (runs 08–14) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | Not tracked (fields passed verbatim from upstream) | Not tracked (same) | UNCHANGED |
| **Option count violations** | Not applicable (options fields passed verbatim) | Not applicable | UNCHANGED |
| **Lever name uniqueness** | Not tracked at deduplication step | Not tracked | UNCHANGED |
| **Template leakage** | Not tracked | Not tracked | UNCHANGED |
| **Review format compliance** | Not applicable (review fields verbatim) | Not applicable | UNCHANGED |
| **Consequence chain format** | Not applicable (consequences verbatim) | Not applicable | UNCHANGED |
| **Content depth (avg consequences len)** | ~283 chars (baseline reference) | ~283 chars (verbatim passthrough, no change) | UNCHANGED |
| **llama3.1 avg kept levers** | 10.6/15 (2 blanket-keep plans) | 7.0/15 (0 blanket-keep plans) | **IMPROVED** ✅ |
| **gpt-4o-mini avg kept levers** | 9.4/15 | 9.6/15 | UNCHANGED (−) |
| **gemini avg kept levers** | 7.0/15 | 7.8/15 | **REGRESSED** ⚠️ |
| **gemini sovereign_identity kept** | 5 (correct; 10 absorbs) | 9 (over-included; only 5 absorbs) | **REGRESSED** ❌ |
| **All-model avg kept** | 7.8/15 | 7.2/15 | **IMPROVED** ✅ |
| **Cross-call duplication** | Not applicable (single call per lever) | Not applicable | UNCHANGED |
| **Over-generation count** | Not applicable at deduplication step | Not applicable | UNCHANGED |
| **Field length vs baseline ratio** | consequences/options/review ~1.0× (verbatim); justification ~1.1–2.5× | Same (verbatim passthrough) | UNCHANGED |
| **Fabricated quantification** | Present in input, passed verbatim (upstream issue) | Present in input, passed verbatim | UNCHANGED (upstream) |
| **Marketing-copy language** | Minimal (some boilerplate in gpt-4o-mini justifications) | Same; "distinct and essential strategic decision" boilerplate in gpt-4o-mini | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS present** | No | Yes (4 failure modes) | **IMPROVED** ✅ |
| **B3: _build_compact_history `...`** | Unconditional | Conditional (fixed) | **IMPROVED** ✅ |
| **B3: all_levers_summary `...`** | Unconditional | Unconditional (missed) | UNCHANGED (confirmed new bug) |
| **Secondary classification examples** | Abstract description only | Concrete examples added | **IMPROVED** ✅ |
| **llama3.1 primary%** | 67% | 41% | **IMPROVED** ✅ |
| **llama3.1 absorb%** | 29% | 53% | **IMPROVED** ✅ |
| **gemini primary%** | 44% | 51% | REGRESSION signal ⚠️ |

**Notes on metrics not applicable at this step:**
The `deduplicate_levers` step passes `consequences`, `options`, and `review` fields verbatim from the `identify_potential_levers` output. Consequently, bracket leakage, option count violations, review format compliance, consequence chain markers, and content depth are all determined by the upstream step and do not change at deduplication. Fabricated quantification (e.g., "30% increase in streaming revenue") is inherited from upstream and flows through unchanged — this is an upstream issue documented in `identify_potential_levers.py`'s `OPTIMIZE_INSTRUCTIONS`.

**OPTIMIZE_INSTRUCTIONS alignment:** The `OPTIMIZE_INSTRUCTIONS` added by PR #364 documents 4 failure modes (blanket-primary, over-inclusion, hierarchy-direction errors, chain absorption). This aligns with the known-problems guidance philosophy from `identify_potential_levers.py`. However, the iteration revealed a **5th failure mode not yet documented**: calibration capping — where models stop absorbing once they reach the upper bound of the calibration hint range. This is directly observable in the gemini sovereign_identity regression (stopped at 5 absorbs when 10 were needed; the "4–8" upper bound acted as a stopping signal).

---

## New Issues

**N1 — Calibration hint upper bound causes premature stopping on high-duplicate plans**

The new calibration hint "expect 4–8 to be absorbed or removed" introduced a regression: gemini-2.0-flash on `sovereign_identity` correctly absorbed 10/15 levers before the PR (leaving 5 kept, matching consensus from all other models). After the PR, gemini absorbed only 5/15 (leaving 9 kept). The "4–8" range appears to have acted as a stopping signal — gemini reached 5 absorbs (the lower bound) and switched to keeping the remaining levers. The correct answer (10 absorbs) is outside the stated range.

Verified in:
- Before: `history/3/06_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — 10 absorbs, 5 kept
- After: `history/3/13_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — 5 absorbs + 1 remove, 9 kept (737c7c14, a3994e33, 1079592e, db44b7de, bd43cd39, 80b177d0, 1731ad9a, f1c0d856, 2e9016aa all survive)

All other 6 models on sovereign_identity after PR kept 5 or fewer — confirming 9 is an outlier and the calibration hint is the likely cause.

**N2 — `all_levers_summary` unconditional `...` (missed half of B3 fix)**

`deduplicate_levers.py:175` still reads `{lever.consequences[:120]}...` — the `...` is appended unconditionally regardless of whether the consequence string exceeds 120 chars. PR #364 fixed the same pattern in `_build_compact_history` (line 99) but did not apply the fix to `all_levers_summary`. The `all_levers_summary` is injected into the system message for every per-lever classification call, so this affects all models on all plans (35/35 after-PR runs). Short consequence strings (≤120 chars) appear to the LLM as truncated, potentially introducing false uncertainty in early classification decisions.

**N3 — Calibration capping not documented as 5th OPTIMIZE_INSTRUCTIONS failure mode**

The `OPTIMIZE_INSTRUCTIONS` block added by PR #364 documents 4 failure modes but omits calibration capping — the newly observed behavior where models interpret the upper bound of a numeric hint as a stopping target rather than a ceiling. This is distinct from the existing "over-inclusion" failure mode and has a different mitigation (widen range, add "do not stop early" language).

---

## Verdict

**YES**: The PR's primary target — llama3.1 blanket-keep — is definitively resolved. Average kept levers for llama3.1 dropped from 10.6 to 7.0, with the two 15/15 zero-deduplication cases (silo and hong_kong_game) both eliminated. The downstream token reduction for that model is ~50%. The OPTIMIZE_INSTRUCTIONS addition and the B3 partial fix are solid infrastructure improvements. The overall all-model average improved from 7.8 to 7.2. The introduced regression (gemini sovereign_identity: 5→9 kept) is limited to one model on one plan and is fixable with a single-line prompt change (widen "4–8" to "4–10").

The missed `all_levers_summary` fix and the unclosed gpt-4o-mini over-inclusion have clear, documented paths forward. Neither represents content quality degradation on the plans that were already working — they represent incomplete repairs and persistent pre-existing issues.

---

## Recommended Next Change

**Proposal:** Widen the calibration hint from "expect 4–8 to be absorbed or removed" to "expect 4–10 to be absorbed or removed" (one line in `deduplicate_levers.py:133`), simultaneously fixing the missed `all_levers_summary` unconditional `...` (`deduplicate_levers.py:175`). Bundle both in a single small PR.

**Evidence:**

The calibration hint regression is mechanically certain: gemini on sovereign_identity absorbed exactly 5 levers — the lower bound of "4–8" — and then kept 9, while all 6 other models kept 5 (consistent with 10 true absorbs). The before-PR baseline shows gemini correctly absorbed 10 on this plan without any calibration hint. The "4–8" range was empirically wrong for this plan class. Widening to "4–10" plus the phrase "do not stop early" in the synthesis recommendation directly addresses this.

The `all_levers_summary` fix is trivial: change `:120}..."` to `:120}{'...' if len(lever.consequences) > 120 else ''}"` — the exact pattern already proven correct in `_build_compact_history`. The synthesis confirms this as direction 2.

**Verify in the next iteration:**

- Rerun gemini-2.0-flash on `sovereign_identity` after widening: expect 5 kept (10 absorbs), matching the before-PR result and the consensus from other models.
- Rerun haiku-4-5 on all 5 plans: confirm it does not increase kept count (was already correct at 6.4 avg; risk of the wider range is negligible since haiku is not at the upper bound).
- Rerun qwen3-30b on `sovereign_identity` and `gta_game`: qwen3 shows per-plan variance (sovereign_identity: 5, gta_game: 11 after PR). Check whether the wider range affects the gta_game count (should not — qwen3's gta_game over-inclusion is a different issue).
- Check gpt-4o-mini on `hong_kong_game`: still expect 12 kept — the gpt-4o-mini over-inclusion does not respond to calibration hint changes and needs a worked absorb example.
- Verify `all_levers_summary` fix does not alter classification behavior (it should be invisible to models with long consequence fields; only models with short consequences ≤120 chars would see a difference).

**What could go wrong:**

- Widening to "4–10" could theoretically push models toward over-absorption on plans with fewer than 10 true duplicates. Current data shows no model is over-absorbing (gpt-5-nano at avg 4.8 kept is the most aggressive, and that pre-dates the hint). The phrase "do not stop early" guards against premature stopping without mandating high absorb counts.
- The `all_levers_summary` fix is zero-risk (applying same pattern as the confirmed-working `_build_compact_history` fix).
- Adding a worked absorb example (direction 3 in synthesis) for gpt-4o-mini should be deferred to the iteration after 1+2 are validated: worked examples carry template-lock risk and require careful domain-neutral example design.

**Prerequisites:** None. Both changes are in `deduplicate_levers.py`, no schema changes, backwards-compatible.

**OPTIMIZE_INSTRUCTIONS update:** After the next iteration validates the calibration hint widening, add calibration capping as a 5th failure mode to `OPTIMIZE_INSTRUCTIONS` in `deduplicate_levers.py`:

> *Calibration capping. When the calibration hint gives a range (e.g. "expect 4–10"), some models stop absorbing once they reach the lower bound rather than continuing until all true duplicates are removed. Symptom: exactly N absorbs where N equals the hint's lower bound, while other models absorb 2× more on the same plan. Mitigation: add "do not stop early" language; avoid tight upper bounds on plans with structural duplicate pairs.*

---

## Backlog

**Resolved by PR #364 (can be removed from backlog):**
- N7/I1 (no `OPTIMIZE_INSTRUCTIONS` in `deduplicate_levers.py`) — added with 4 failure modes.
- N1 (llama3.1 blanket-keep) — eliminated; avg kept 10.6 → 7.0.
- S1 (safety valve "Use primary if you lack understanding" too permissive) — narrowed to "last resort."
- D3 (add `OPTIMIZE_INSTRUCTIONS` before next self-improve iteration) — completed.
- D2 (fix `_build_compact_history` unconditional `...`) — completed (partially; see below).

**New items introduced by PR #364 or revealed in this iteration:**
- **[HIGH] Calibration hint "4–8" causes capping on high-duplicate plans** — widen to "4–10" with "do not stop early" language. Direct evidence from gemini sovereign_identity (5→9 kept). Fix: one line in `deduplicate_levers.py:133`.
- **[HIGH] `all_levers_summary` unconditional `...`** (`deduplicate_levers.py:175`) — missed during B3 fix; affects all 35 after-PR runs. Fix: same conditional pattern already in line 99.
- **[MEDIUM] gpt-4o-mini over-inclusion unresolved** (avg 9.6 kept vs. target 7) — calibration hint is insufficient; needs a worked absorb comparison example in the system prompt. Template-lock risk: keep example to one sentence, domain-neutral. See synthesis I3/direction 3.
- **[MEDIUM] Calibration capping not documented as 5th OPTIMIZE_INSTRUCTIONS failure mode** — add after next iteration validates the "4–10" range.
- **[LOW] B2 (`runner.py` `partial_recovery` threshold `< 3` → `< 2`)** — false events in `events.jsonl` for normal 2-call completions. Pre-existing; bundle with next `runner.py` change.
- **[LOW] B3 nested `ThreadPoolExecutor` defeats per-plan log filtering** (`runner.py:514–527`) — `_ThreadFilter` captures outer thread; inner thread LLM logs filtered out. Pre-existing; address in a future runner refactor.
- **[LOW] Q4 / D8: `vital_few_levers` does not consume `classification: primary|secondary`** — if the downstream prioritization intent of PR #363 has not been implemented in `vital_few_levers`, the investment in secondary classification tuning has not yet produced downstream benefit. Verify before further secondary classification work.

**Carried forward from prior backlog (unchanged):**
- **D6** — Terminology: PR #363 description used "keep-core"/"keep-secondary" but code uses "primary"/"secondary". Cosmetic; add a comment above `LeverClassification` linking the naming.
- **D7** — Chain absorption detection requires `absorb_into_id: Optional[str]` in `LeverClassificationDecision` schema to avoid text-parsing. Defer until chain absorptions cause observable downstream problems.
- **D9** — `review_lever` examples 1 and 3 in `identify_potential_levers.py` share "X but Z" rhetorical pattern — defer to an `identify_potential_levers` iteration.
- **D9b** — `options` field description says "Exactly 3, no more, no fewer" but validator only enforces ≥3; field description contradicts policy. Fix the description. Low urgency.
