# Assessment: feat: consolidate deduplicate_levers — classification, safety valve, B3 fix

## Issue Resolution

**What the PR was supposed to fix** (from PR #365 description):
1. Gemini calibration-capping on sovereign_identity — the "4–8" hint introduced by PR #364 caused gemini to stop absorbing at 5 absorbs and keep 9 levers where 5 is correct.
2. Widen calibration range to "4–10" and add "do not stop early".
3. Add `primary`/`secondary` classification for downstream prioritization.
4. Complete the B3 fix: `all_levers_summary` in `deduplicate_levers.py:179` still appended `...` unconditionally (missed by PR #364, caught by code_claude analysis/43 as B1).
5. Document 5th failure mode (calibration-capping) in `OPTIMIZE_INSTRUCTIONS`.

**Is the issue resolved?**

**Issue 1+2 (calibration-capping): FIXED.** Gemini sovereign_identity: 9 kept → 5 kept. Confirmed by reading `history/3/13_deduplicate_levers` (before, 9P+5A+1R=15) vs `history/3/20_deduplicate_levers` (after, 5P+10A=15). The first-batch absorbs (a02b023d, b1a9192f, b19a5405, 5019c4ad, 7166dd86) and second-batch absorbs (1b3c2ca2, 737c7c14, a3994e33, 1079592e, db44b7de) all correctly absorb into the five primary second-batch levers. The "do not stop early" + widened "4–10" range resolved the premature stopping observed in run 13.

**Issue 3 (primary/secondary classification): PARTIAL.** Haiku (run 21) and gpt-4o-mini (run 19) correctly classify EU Standards as secondary on sovereign_identity (4P/1S/10A). gpt-4o-mini also classifies 3 operational levers as secondary on hong_kong_game (Production Efficiency, Audience Engagement, HK Identity Amplification), reducing its kept count from 12 → 9. Four models (llama3.1, gpt-oss-20b, gemini, qwen3) produced 0 secondary classifications on sovereign_identity. The concrete examples ("marketing campaign timing, internal reporting cadence") map poorly onto sovereign_identity's domain, limiting their signal for those models.

**Issue 4 (B3 fix complete): CONFIRMED.** Code review for PR #365 confirms `deduplicate_levers.py:179` now uses the conditional `{'...' if len(lever.consequences) > 120 else ''}` pattern. Both truncation sites (`_build_compact_history` line 103 and `all_levers_summary` line 179) are now correct.

**Issue 5 (OPTIMIZE_INSTRUCTIONS 5th failure mode): CONFIRMED.** PR #365 adds calibration-capping as the 5th documented failure mode alongside blanket-primary, over-inclusion, hierarchy-direction, and chain absorption.

**Residual symptoms:**

The Qwen3-30b sovereign_identity result regressed from 5 kept (before PR #365) to 3 kept (after). Reading `history/3/18_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` directly reveals the mechanism: lever a02b023d points to itself as absorb target (self-referential), and 80b177d0/737c7c14 form a circular pair (each absorbs into the other). The code at `deduplicate_levers.py:281` drops any lever whose classification is not in `keep_classifications`, so both legs of a circular pair are silently discarded. The widened calibration hint ("4–10") amplified Qwen's aggressive absorption tendency, triggering these degenerate decision patterns.

---

## Quality Comparison

Comparing before (runs 08–14, post-PR #364) vs after (runs 15–21, post-PR #365). Models present in both batches: all 7 (llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, claude-haiku).

| Metric | Before (runs 08–14) | After (runs 15–21) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 100% (35/35) | 100% (35/35) | UNCHANGED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |
| **Gemini sovereign_identity kept** | 9 (regression from PR #364) | 5 (correct) | IMPROVED ✅ |
| **Qwen sovereign_identity kept** | 5 | 3 (circular/self-ref absorb) | REGRESSED ❌ |
| **gpt-4o-mini hong_kong kept** | 12 | 9 | IMPROVED ✅ |
| **Secondary usage (sovereign_id)** | 0/7 models | 2–3/7 models | IMPROVED ✅ |
| **B3 fix — all_levers_summary `...`** | incomplete (unconditional) | complete (conditional) | IMPROVED ✅ |
| **Hierarchy-direction errors** | present (gemini, gpt-oss-20b, gpt-5-nano) | present (unchanged) | UNCHANGED |
| **Fabricated quantification** | present (upstream, inherited) | present (upstream, inherited) | UNCHANGED |
| **Field length vs baseline** | ~1.0× (verbatim pass-through) | ~1.0× (verbatim pass-through) | UNCHANGED |
| **Bracket placeholder leakage** | not observed | not observed | UNCHANGED |
| **Option count violations** | not observed (verbatim) | not observed (verbatim) | UNCHANGED |
| **Consequence chain format** | Immediate → Systemic → Strategic present | same (verbatim) | UNCHANGED |
| **Review format compliance** | Controls X vs Y present (verbatim) | same (verbatim) | UNCHANGED |
| **Content depth (option length)** | verbatim pass-through | verbatim pass-through | UNCHANGED |
| **Cross-call deduplication** | N/A — single sequential call | N/A | N/A |
| **Marketing-copy language** | not observed | not observed | UNCHANGED |
| **Self-referential absorb guard** | absent | absent | UNCHANGED ❌ |
| **Circular absorb detection** | absent | absent | UNCHANGED ❌ |
| **OPTIMIZE_INSTRUCTIONS failure modes** | 4 documented | 5 documented | IMPROVED ✅ |

**Notes on metrics not applicable to deduplicate_levers:**

- *Bracket placeholder leakage*, *template leakage*, *over-generation count*: These are relevant to `identify_potential_levers` (the upstream step). The deduplicate step passes `consequences`, `options`, and `review` fields verbatim and does not generate new content, so these metrics are not independently testable here.
- *Field length vs baseline*: The baseline training data (`baseline/train/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`) shows option lengths of 80–130 chars and consequence strings of 160–250 chars — consistent with both before and after runs, since content is verbatim. Ratio is ~1.0×, well below the 2× warning threshold.
- *Fabricated quantification*: Confirmed present in both periods (e.g., "15% increased policy traction", "20% greater likelihood", "25% faster scaling" in sovereign_identity conseq fields). This is an upstream `identify_potential_levers` issue. Deduplicate_levers cannot filter these without a post-processing step.

**OPTIMIZE_INSTRUCTIONS alignment:**

The PR moves closer to the OPTIMIZE_INSTRUCTIONS goals. Calibration-capping (the 5th failure mode) is now documented. The secondary classification addition enables downstream prioritization, which was a gap. The remaining open items from OPTIMIZE_INSTRUCTIONS (hierarchy-direction errors, chain absorption) are not addressed by this PR but are known targets for the next change.

---

## New Issues

**B1 — Self-referential absorb silently drops levers** (`deduplicate_levers.py:258–281`)

Observed in gpt-5-nano run 17 (lever `f1c0d856` justification "Absorb into [f1c0d856]") and in qwen3 run 18 (lever a02b023d absorbs into itself). The code drops any lever not in `keep_classifications`, so self-referential absorbs cause silent data loss. The PR added a fourth classification option (`secondary`) which expands the decision space and increases probability of degenerate decisions — but adds no guard. Fix: check if `classification == "absorb"` and `lever.lever_id in justification`; reclassify to primary if so.

**B2 — Circular absorb pair drops both levers** (`deduplicate_levers.py:258–281`)

Observed in qwen3 run 18 (80b177d0↔737c7c14 — each absorbs into the other). Both are filtered out at line 281, losing two distinct levers. This explains the Qwen sovereign_identity collapse (5→3). The code has no circular pair detection. Fix: post-processing pass over `decisions[]` to detect circular pairs, keep the earlier-indexed lever as primary.

**S1 — "Use primary only as a last resort" is semantically inverted** (`deduplicate_levers.py:135`)

Means "primary is a fallback of last resort," but in practice most levers should be primary. The intent is "don't lazily default every lever to primary; genuinely evaluate whether it's secondary." The inverted phrasing is working for haiku and gpt-4o-mini (which benefited from it) but may mislead weaker instruction-following models toward over-using secondary or absorb. Not an immediate regression, but a latent risk as model versions change.

**B3 — `calls_succeeded` in `_run_deduplicate` counts decisions, not LLM calls** (`runner.py:155`)

`calls_succeeded=len(result.response)` returns 15 (lever decisions) instead of 1 (LLM conversation). The `partial_recovery` event guard is currently limited to `identify_potential_levers`, so there is no immediate functional impact. But any future code reading this field for the deduplicate step will misinterpret 15 as "15 LLM calls succeeded."

**Gap — Secondary examples are domain-narrow**

The concrete secondary examples ("marketing campaign timing, internal reporting cadence, team communication tooling, documentation formatting standards") are all from a corporate operational context. On sovereign_identity and similar civic/policy plans, these examples provide weak signal. The 4 models that didn't use secondary at all on sovereign_identity (llama3.1, gpt-oss-20b, gemini, qwen3) likely failed partly because none of the plan's levers resemble the provided examples.

**Surfaced latent issue — numeric calibration hint is an unstable mechanism**

The range has been revised three times across three PRs: absent → "4–8" → "4–10". Each revision fixed one model and pressured another. This suggests a static numeric range cannot simultaneously calibrate models with heterogeneous absorption tendencies (llama3.1 under-absorbed, gemini capped at 8, qwen3 over-absorbed at 10). The synthesis proposes removing the range and relying on qualitative guidance only.

---

## Verdict

**YES**: The PR resolves its primary regression target (Gemini calibration-capping fixed: 9→5 on sovereign_identity), completes the B3 fix that was half-done in PR #364, adds measurable secondary classification benefit for haiku and gpt-4o-mini, and reduces gpt-4o-mini hong_kong over-inclusion from 12→9 kept levers. The Qwen3 regression (5→3) is real but is caused by a pre-existing code-level bug (circular absorb pair drops both levers), which is now the confirmed target of the next change. Net: improvements outweigh the regression.

---

## Recommended Next Change

**Proposal**: Add circular absorb and self-referential absorb detection to `deduplicate_levers.py`. When a lever absorbs into itself (self-referential), reclassify to primary. When two levers each absorb into each other (circular pair), keep the earlier-indexed lever as primary and discard the other. Document circular absorb as the 6th failure mode in `OPTIMIZE_INSTRUCTIONS`.

**Evidence**: Both failure modes are confirmed in the data:
- Self-referential absorb: gpt-5-nano run 17 (`f1c0d856` absorbs into itself, lever silently dropped), qwen3 run 18 (`a02b023d` absorbs into itself via "Merging into [a02b023d]").
- Circular pair: qwen3 run 18 (80b177d0 absorbs into 737c7c14; 737c7c14 absorbs into 80b177d0 — both dropped), accounting for exactly the 5→3 sovereign_identity regression.
- Code gap confirmed at `deduplicate_levers.py:258–281`: no guard exists. The filter `if classification not in keep_classifications: continue` drops both legs of a circular pair.
- The synthesis (Direction 1) provides ready-to-implement pseudocode for both guards.

**Verify in the next iteration**:
- Qwen sovereign_identity kept count should recover from 3 → 5 after the circular absorb fix.
- gpt-5-nano run 17 lever `f1c0d856` should no longer be silently dropped; it should appear in `deduplicated_levers` as primary.
- Check that the self-referential guard does not incorrectly fire on levers whose justification text legitimately contains their own ID as a reference (rather than an absorb target). The UUID is a 36-char string — false positives are possible if the text discusses the lever by ID.
- Verify that circular detection handles chains (A→B→C→A) as well as simple pairs, since Qwen's sovereign_identity shows evidence of multi-hop chain patterns alongside the simple circular pair.
- Monitor llama3.1 and gemini lever counts after removing the numeric calibration range (Direction 2 from synthesis) — confirm llama3.1 does not regress to blanket-keep without the lower-bound signal.

**Risks**:
- Synthesizing Direction 1 (absorb guard) with Direction 2 (remove numeric calibration range) in a single PR is higher risk than doing them sequentially. The circular absorb guard is a pure code fix with no prompt change; the calibration range removal is a prompt change that may affect llama3.1. If bundled, a regression in llama3.1 is harder to attribute. **Recommendation: implement the absorb guard first, validate, then address the calibration range separately.**
- The circular detection algorithm requires UUID substring search in justification text. If the LLM omits the UUID from the justification (e.g., writes "absorb into the other policy lever" without naming it), the detection will miss the circular pair and the levers will still be silently dropped. This is an incomplete mitigation — not a reason to skip it, but a known limitation to track.
- Pydantic model mutability: the synthesis code reassigns `decision.classification` directly. If `LeverDecision` uses `model_config = ConfigDict(frozen=True)`, this will raise at runtime. Verify before merging.

**Prerequisite issues**: None. The circular absorb guard is a standalone code fix. It does not depend on any prompt changes or schema changes.

---

## Backlog

**Resolved by PR #365 — can close:**
- B1 (analysis/43 code review): `all_levers_summary` unconditional `...` — **FIXED** at `deduplicate_levers.py:179`.
- S1 from analysis/43 (calibration hint range "4–8" creates capping risk) — **FIXED** by widening to "4–10" + "do not stop early".
- Gemini sovereign_identity regression (analysis/43 N2) — **FIXED**.
- OPTIMIZE_INSTRUCTIONS 4th → 5th failure mode — **ADDED** (calibration-capping documented).

**Active — should be tracked:**
- **B1 (circular absorb drops both levers)**: Code bug at `deduplicate_levers.py:258–281`. Confirmed cause of Qwen sovereign_identity collapse (5→3). **Next PR target.**
- **B2 (self-referential absorb drops lever)**: Same location. Observed in gpt-5-nano run 17. **Next PR target (same fix as B1).**
- **B3 (calls_succeeded semantic mismatch in runner)**: `runner.py:155` counts lever decisions (15) as if they were LLM calls. Latent bug. Bundle with next runner.py change.
- **N1 (secondary adoption partial)**: Only 3/7 models use secondary. Secondary examples are domain-narrow for non-corporate plans. May need domain-agnostic examples or a rephrased secondary definition.
- **N2 (hierarchy-direction errors)**: Multiple models absorb general first-batch levers into specific second-batch duplicates, keeping the wrong instance. Persistence across PR #363–365 without improvement. Code-level hierarchy-aware tie-breaking (synthesis Direction 3 / code review I2) is the proposed fix.
- **S1 ("last resort" inverted semantics)**: Low urgency; currently working for haiku/gpt-4o-mini. Revisit after 2 more iterations of secondary adoption data.
- **N5 / upstream fabricated percentages**: `identify_potential_levers` generates ungrounded percentage claims that flow through deduplicate unchanged. Requires a separate self-improve iteration on the upstream step.
- **I4 (numeric calibration range unstable)**: Three revisions across three PRs. Synthesis Direction 2 proposes replacing with qualitative-only guidance. Do after B1/B2 absorb guard is validated.
- **Q4 (downstream secondary consumption)**: Unverified whether `vital_few_levers` and `scenario_generation` consume the `classification: primary|secondary` field. If not, the core motivation for the primary/secondary split is unimplemented at the pipeline level.
