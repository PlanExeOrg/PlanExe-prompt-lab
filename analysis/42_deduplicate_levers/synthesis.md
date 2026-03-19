# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude, code_claude) agree on:

1. **PR verdict: CONDITIONAL KEEP.** The `classification: primary|secondary` field is correctly added, schema-valid, and populated in all capable-model runs. No regressions; 100% success rate across 7 models × 5 plans.

2. **Safety valve (S1/N1) is the root cause of llama3.1's blanket-primary failure.** The prompt instruction "Use 'primary' if you lack understanding" gives weak models a blanket escape route. llama3.1 classifies 14/15 levers as `primary` and performs zero absorb/remove — confirmed in `history/3/01_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`. gpt-4o-mini also over-includes (12/15 kept vs. 7 baseline) for the same structural reason.

3. **No `OPTIMIZE_INSTRUCTIONS` in `deduplicate_levers.py` (N7/I1).** Four confirmed failure modes (blanket-primary, hierarchy-direction errors, chain absorption, over-inclusion) are undocumented, making future self-improve iterations blind to them.

4. **Terminology mismatch is a maintenance risk (N5).** PR title/description say "keep-core"/"keep-secondary"; the code, enum, schema, and JSON output all use "primary"/"secondary". No runtime impact but confusing for anyone reading the diff.

5. **B1 (spurious `partial_recovery` events) and B3 (`...` appended unconditionally) are real bugs.** Both confirmed in source code.

6. **Post-deduplication zero-reduction check is missing (I2).** No warning is emitted when a model keeps 90%+ of input levers — the clearest signal of deduplication failure.

---

## Cross-Agent Disagreements

There are no material disagreements between agents. Both files are complementary: insight_claude focuses on behavioral analysis of runs, code_claude focuses on source-level root causes. The one area where they emphasize differently:

- **insight_claude** treats N8 (fabricated numbers flowing through deduplication unchanged) as a significant finding.
- **code_claude** correctly notes this is an upstream problem: `identify_potential_levers.py`'s OPTIMIZE_INSTRUCTIONS documents it at lines 51–54, and no structural enforcement is possible at the deduplication step. **Source code confirms**: `deduplicate_levers.py` passes `consequences` fields verbatim; there is no validator on that field. This finding is real but not actionable at this step.

- **code_claude** flags S2 (closure captures `chat_message_list` by reference) as a suspect pattern. Reading the code confirms this is safe in current synchronous operation but fragile. It is not a current bug — the rebind always happens between `llm_executor.run()` calls. Low priority.

---

## Top 5 Directions

### 1. Narrow the safety valve + add absorb-count calibration
- **Type**: prompt change (`deduplicate_levers.py` — `DEDUPLICATE_SYSTEM_PROMPT`)
- **Evidence**: S1 (code_claude), N1 (insight_claude), N3 (insight_claude). Confirmed root cause: `deduplicate_levers.py:104` reads "Use 'primary' if you lack understanding…" with no calibrating expectation. llama3.1: 0 absorb/remove decisions, all 15 levers kept. gpt-4o-mini: only 3 absorb decisions, 12/15 kept vs 7 baseline.
- **Impact**: Reduces downstream token cost for llama3.1 runs by ~50% (15→7 levers entering enrich/vital_few/scenario). Improves gpt-4o-mini deduplication quality. Does not regress haiku-4-5 (already correct at 7/15 kept). Affects 2 of 7 tested models directly.
- **Effort**: Low — single paragraph change in DEDUPLICATE_SYSTEM_PROMPT.
- **Risk**: May cause over-aggressive removal in already-good models (haiku, qwen3). Mitigated by framing as a calibration hint ("typically 4–8 absorb/remove in a 15-lever set") not a hard minimum. Must test haiku and qwen3 to confirm no regression.

### 2. Fix B1 — spurious `partial_recovery` events for 2-call completions
- **Type**: code fix (`runner.py:125` and `runner.py:548`)
- **Evidence**: B1 (code_claude). Confirmed: runner.py:125 `if actual_calls < 3: logger.warning(...)` and runner.py:548 `pr.calls_succeeded < 3` both fire on 2-call completions. The inline comment at runner.py:121–123 explicitly says "A 2-call success is normal for models that produce 8+ levers per call." Analysis pipeline misinterprets these as failures.
- **Impact**: Stops polluting `events.jsonl` with false `partial_recovery` entries for every 2-call run. All current and future analysis code that counts these events currently over-counts failures. Affects all models that return 8+ levers per call.
- **Effort**: Low — change threshold from `< 3` to `< 2` (or remove the event entirely).
- **Risk**: Near-zero. If a genuine 1-call failure with only 10–14 levers occurs, `actual_calls == 2` still fires the warning; with `< 2`, only total 1-call runs trigger it.

### 3. Add `OPTIMIZE_INSTRUCTIONS` to `deduplicate_levers.py`
- **Type**: code change (`deduplicate_levers.py` — new module-level constant)
- **Evidence**: N7 (insight_claude), I1 (code_claude). Four confirmed failure modes currently undocumented: blanket-primary (llama3.1), hierarchy-direction errors (gemini), chain absorption (qwen3), over-inclusion (gpt-4o-mini).
- **Impact**: Enables future self-improve iterations to have documented starting context. Without this, the next analysis iteration for `deduplicate_levers` will have to rediscover these failure modes from scratch. Mirrors the 67-line `OPTIMIZE_INSTRUCTIONS` pattern already established in `identify_potential_levers.py`.
- **Effort**: Low — write a constant block; no behavior change.
- **Risk**: None — documentation only.

### 4. Fix B3 — `_build_compact_history` unconditionally appends `...`
- **Type**: code fix (`deduplicate_levers.py:70`)
- **Evidence**: B3 (code_claude). Confirmed at line 70: `f"- [{d.lever_id}] {d.classification}: {d.justification[:80]}..."` — `...` is always appended regardless of whether truncation occurred. A 40-char justification appears to the LLM as incomplete.
- **Impact**: Prevents misleading the LLM on the compacted-history retry path. For absorption decisions where the justification names a target lever ID, the LLM may infer truncation and re-classify the lever. Affects all models that hit the fallback compaction path.
- **Effort**: Very low — one-line fix: `d.justification[:80] + ("..." if len(d.justification) > 80 else "")`.
- **Risk**: None.

### 5. Add concrete `secondary` lever examples to the system prompt
- **Type**: prompt change (`deduplicate_levers.py` — `DEDUPLICATE_SYSTEM_PROMPT`)
- **Evidence**: H2 (insight_claude), N4 (insight_claude). Confirmed: qwen3 (run 04) classifies "Production Efficiency" as `primary`; haiku-4-5 (run 07) and gpt-4o-mini (run 05) classify it as `secondary`. The system prompt describes the distinction abstractly but provides no worked example. The existing description "routine process levers belong here" is not concrete enough for mid-tier models.
- **Impact**: More consistent secondary classification across models. The `classification` field's downstream value to `vital_few_levers` depends on models agreeing on what constitutes secondary. With qwen3 misclassifying operational levers as primary, the prioritization signal is noisy.
- **Effort**: Low — add 2–3 example pairs to the `secondary` bullet in the system prompt.
- **Risk**: Low, but secondary examples could anchor models to domain-specific terms. Keep examples domain-neutral (e.g., "Marketing campaign timing: secondary. Budget risk management: primary.").

---

## Recommendation

**Pursue Direction 1 first: narrow the safety valve and add absorb-count calibration.**

**Why first**: This is the only direction that improves content quality across all downstream steps. When llama3.1 keeps all 15 levers instead of 7, it doubles the input to `enrich_potential_levers`, `vital_few_levers`, and `scenario_generation` — all for levers that should have been collapsed. The compounding cost across 3 downstream steps is significant. gpt-4o-mini's over-inclusion (12/15) has the same downstream cost at smaller scale.

The fix is low-risk and low-effort: a prompt change in `DEDUPLICATE_SYSTEM_PROMPT`. No schema changes, no breaking changes.

**File**: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/deduplicate_levers.py`

**Replace** (lines 104–107):
```
Use "primary" if you lack understanding of what the lever is doing. This way a potential important lever is not getting removed.
Describe what the issue is in the justification.

Don't play it too safe, so you fail to perform the core task: consolidate the levers and get rid of the duplicates.
```

**With**:
```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's strategic role after reading the full context. Describe what is unclear in the justification.

In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed. If you find zero absorb/remove decisions, reconsider: the input almost always contains near-duplicates. Do not keep every lever.
```

This preserves the safety fallback for genuine failures while providing a calibrating expectation that directly counteracts the blanket-primary pattern. The count expectation (4–8 absorb/remove for 15 levers) is evidence-grounded: the baseline achieves ~53% reduction (8/15 absorbed/removed), and haiku and qwen3 reproduce this under the PR.

**Before merging**: run a self-improve iteration with haiku-4-5 and qwen3 to confirm they are not pushed toward over-aggressive removal. If either model drops below 5 survivors on any plan, the count range needs widening or the instruction needs softening.

---

## Deferred Items

**D1 — Fix B1 (runner.py spurious `partial_recovery`)**: Change threshold from `< 3` to `< 2` at runner.py:125 and runner.py:548. Simple and safe; do in the next PR alongside Direction 1 or as a standalone 2-line fix.

**D2 — Fix B3 (`...` appended unconditionally)**: One-line fix in `deduplicate_levers.py:70`. Bundle with any next `deduplicate_levers` change.

**D3 — Add `OPTIMIZE_INSTRUCTIONS` to `deduplicate_levers.py`**: Should be done before the next self-improve iteration on this step. Not urgent for the prompt fix in Direction 1.

**D4 — Fix B2 (`calls_succeeded` always constant for deduplicate step)**: Rename the field to `decisions_count` or track actual LLM failures separately. Low urgency — the metric is currently unused in analysis.

**D5 — Add concrete `secondary` examples to system prompt**: After validating Direction 1's effect on classification consistency, revisit whether qwen3's misclassification of "Production Efficiency" persists. If it does, add domain-neutral examples.

**D6 — Terminology reconciliation (N5)**: Update the PR description or add a comment in `deduplicate_levers.py` linking "primary" to "keep-core" from the PR description. Cosmetic but worth a one-line comment before the enum definition.

**D7 — Chain absorption detection (I3)**: Requires adding `absorb_into_id: Optional[str]` to `LeverClassificationDecision` schema to avoid text parsing. Schema change — defer until chain absorptions cause observable downstream problems.

**D8 — Add `vital_few_levers` consumption of `classification` field**: Insight Q1 asks whether `vital_few_levers` already uses the new field. If not, the downstream prioritization benefit of PR #363 has not yet been realized. Investigate and implement.

**D9 — S3 (review_lever examples sharing rhetorical structure)**: Examples 1 and 3 in `identify_potential_levers.py:248–251` both follow "X but Z" pattern, violating the OPTIMIZE_INSTRUCTIONS guideline at lines 74–82. Defer to a future `identify_potential_levers` iteration since it requires validating template-lock behavior with weaker models.
