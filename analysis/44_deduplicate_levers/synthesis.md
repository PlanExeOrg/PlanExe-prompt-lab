# Synthesis

## Cross-Agent Agreement

Only one insight file and one code review file exist for this analysis, both
produced by Claude. There is no true multi-agent disagreement surface; the
following reflects internal consistency between the two documents.

**Strong consensus (both files)**:

- Gemini calibration-capping is fixed. Sovereign_identity went from 9 kept →
  5 kept after PR #365. The widened range ("4–10") + "do not stop early" is
  the confirmed cause.
- B3 fix is complete. Both the `_build_compact_history` truncation (line 103)
  and the `all_levers_summary` truncation (line 179) now use the correct
  conditional `...`. Confirmed by reading the source and by the
  `track_activity.jsonl` evidence.
- Qwen regression (5→3 on sovereign_identity) is real. The insight identifies
  it as N3; the code review diagnoses it as caused by the numeric calibration
  range (I4). Evidence: `history/3/18_deduplicate_levers/outputs/
  20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`.
- Self-referential absorb (B1 in code review, N4 in insight) is unguarded.
  Lever `f1c0d856` in gpt-5-nano run 17 produced "Absorb into [f1c0d856]" for
  itself; the code drops it silently. Confirmed at `deduplicate_levers.py:258–281`
  — no guard exists.
- Secondary adoption is partial. Only 3 of 7 models (haiku, gpt-4o-mini,
  gpt-5-nano) used secondary at all; the 4 others defaulted to all-primary.
- "last resort" wording for primary (S1) is semantically inverted but
  empirically positive for instruction-following models so far.
- Numeric calibration range is an unstable mechanism (third revision in
  three iterations: none → "4–8" → "4–10", each creating a new model-specific
  pressure point).

---

## Cross-Agent Disagreements

None significant — single-agent pair. Two internal tensions worth noting:

**Tension A — "last resort" wording**: The code review (S1) flags it as
inverted semantics that may cause over-use of secondary/absorb. The insight
(P2, P3) notes it improved haiku and gpt-4o-mini. **Resolution**: both are
correct — the wording works for models with strong instruction-following but
is risky for models that interpret it literally. The phrasing should be
clarified rather than reverted. Defer until secondary adoption data from more
iterations is available.

**Tension B — Qwen regression cause**: Insight N3 attributes the 5→3
collapse to over-absorption driven by the widened calibration hint. Code
review I4 agrees. However, the insight also notes a circular-absorb pattern:
"a02b023d → absorb (into bd43cd39), bd43cd39 → absorb (into a02b023d —
circular?)". If circular absorb is the mechanism — not merely the calibration
hint — then the prompt change (I4) addresses the pressure but not the
underlying bug. **Verified by reading `deduplicate_levers.py:264–281`**: a
circular absorb pair (A→B, B→A) causes both levers to be filtered out at
line 281 (`if lever_decision.classification not in keep_classifications: continue`),
because both are classified "absorb". This is a code-level data loss bug
independent of calibration pressure. **I3/B1 extension (circular detection)
is the higher-impact fix for Qwen.**

---

## Top 5 Directions

### 1. Circular and self-referential absorb detection
- **Type**: code fix
- **Evidence**: B1 (code_claude), N3/N4 (insight_claude), confirmed by reading
  `deduplicate_levers.py:258–281`. Self-referential absorb observed in
  gpt-5-nano run 17 (lever `f1c0d856`). Circular absorb (a02b023d↔bd43cd39)
  is the likely root cause of Qwen's 5→3 regression on sovereign_identity.
- **Impact**: Restores Qwen sovereign_identity from 3→5 kept (recovers the PR
  #365 regression). Prevents silent lever loss in gpt-5-nano. Protects all
  models from future circular/self-referential edge cases. Benefits 2 models
  directly, defensive for all 7.
- **Effort**: low. Self-referential guard: ~5 lines added immediately after the
  `decision = raw` block (before appending to `decisions`). Circular detection:
  ~15–20 lines post-processing pass over `decisions[]` before building
  `output_levers`, using UUID substring search in justification text.
- **Risk**: very low. Overrides to "primary" in degenerate cases — consistent
  with the existing fallback at lines 247–256. No prompt change, no schema
  change.

### 2. Remove the numeric calibration range; keep qualitative guards
- **Type**: prompt change
- **Evidence**: I4 (code_claude), N3 (insight_claude). The range has been
  revised three times across three iterations, each causing a new model to
  misbehave. Confirmed at `deduplicate_levers.py:137`.
- **Impact**: Reduces prompt pressure on Qwen (and any future model sensitive
  to upper-bound framing). Breaks the revision cycle. Works synergistically
  with Direction 1: Direction 1 removes the code-level data loss; Direction 2
  reduces the condition that triggers it.
- **Effort**: low. Replace the current calibration sentence with:
  ```
  If you find zero absorb/remove decisions, reconsider: the input almost
  always contains near-duplicates. Do not keep every lever. Plans with many
  near-duplicate names may require 10 or more absorbs — do not stop early.
  ```
  This retains the Gemini fix ("may require 10 or more", "do not stop early")
  while removing the "expect 4–10" upper-bound anchor that pressures Qwen.
- **Risk**: moderate. Removing the lower-bound signal ("expect 4–10") could
  allow blanket-primary models (llama3.1) to regress. Mitigation: "do not
  keep every lever" + "input almost always contains near-duplicates" provides
  qualitative pressure. Monitor llama3.1 result counts in the next iteration.

### 3. Hierarchy-aware instance selection (position-based tie-breaking)
- **Type**: code fix
- **Evidence**: I2/C1 (code_claude), N2 (insight_claude). Multiple models
  (Gemini, gpt-oss-20b, gpt-5-nano) absorb first-batch (general) levers into
  second-batch (specific) duplicates, keeping the wrong instance. No structural
  code change can force the LLM to pick correctly; but the runner can apply
  a tie-breaker post-hoc. Confirmed gap at `deduplicate_levers.py:266–293` —
  no position check exists.
- **Impact**: Corrects which lever survives when direction is wrong. Affects
  ~3 of 7 models on sovereign_identity specifically. Content quality improves
  for all plans with near-duplicate batches.
- **Effort**: medium. Requires building a map of absorb-target IDs from
  justification text (UUID substring search) to identify which lever "won"
  and which was absorbed. If the absorbed lever has a lower index in
  `input_levers` than its target, swap the outcome (mark the absorbed lever
  primary, drop the target instead). ~25–30 lines.
- **Risk**: low-moderate. Position as proxy for generality is an approximation.
  In synthetic test data (sovereign_identity: 5 unique × 3 instances), batch
  order is a reliable proxy. In organic plans it may not be — could override a
  correct LLM decision. Add a log warning for each swap so it is auditable.

### 4. Rephrase "Use primary only as a last resort"
- **Type**: prompt change
- **Evidence**: S1 (code_claude), N1 (insight_claude). Current wording:
  "Use 'primary' only as a last resort — if you genuinely cannot determine a
  lever's strategic role after reading the full context." Read literally, this
  says most levers should not be primary, which contradicts the design intent.
  Four of 7 models (llama3.1, gpt-oss-20b, qwen3, gemini) still default to
  all-primary for sovereign_identity despite this instruction.
- **Impact**: Could increase secondary adoption rate beyond the current 3/7
  models. Downstream benefit: levers marked secondary enable FocusOnVitalFew
  to prioritize correctly. The secondary feature is the main new value of PR
  #365 for downstream steps.
- **Effort**: low. Proposed replacement:
  ```
  Before labeling a lever "primary", actively consider whether it is
  "secondary" — distinct and useful, but supporting rather than
  essential. Primary means the lever directly shapes whether the project
  succeeds or fails. If uncertain after reading context, default to
  secondary, not primary.
  ```
- **Risk**: low-moderate. This is a behavior change for models that currently
  get correct primary counts. Could cause over-use of secondary in models that
  already use it correctly (haiku, gpt-4o-mini). Test against both before
  merging.

### 5. Add `save_clean` call in `_run_deduplicate` and fix `calls_succeeded`
- **Type**: code fix (runner correctness)
- **Evidence**: I5 and B3-runner (code_claude). Confirmed at `runner.py:137–156`.
  `_run_deduplicate` writes `002-11-deduplicated_levers_raw.json` but not a
  flat clean JSON. `calls_succeeded=len(result.response)` counts 15 lever
  decisions, not 1 LLM conversation.
- **Impact**: Ensures downstream consumers can find a flat lever list at a
  known path. Fixes misleading `partial_recovery` semantics if the guard is
  ever extended to deduplicate_levers. Low current impact since the
  `partial_recovery` event is guarded to `identify_potential_levers` only.
- **Effort**: very low. Add one `result.save_clean(...)` call and change
  `calls_succeeded=1` in `_run_deduplicate`.
- **Risk**: negligible. Purely additive.

---

## Recommendation

**Pursue Direction 1 first: circular and self-referential absorb guard.**

**Why this first**: The Qwen 5→3 regression is the only confirmed regression
introduced by PR #365. The circular absorb pattern (a02b023d↔bd43cd39, both
dropped) is the best available explanation for that exact count. Direction 1
is a pure code fix — no prompt change, no schema change, no model-specific
tuning. It recovers 2 silently lost levers for Qwen and prevents the same
failure mode in future models and plans.

**What to change** — `deduplicate_levers.py`:

**Part A — Self-referential guard** (insert after line 239, before
`decisions.append(...)` at line 258):
```python
# Guard against self-referential absorb: LLM says "absorb into [this lever's own id]".
# Treat as primary to avoid silent data loss.
if decision.classification == "absorb" and lever.lever_id in decision.justification:
    logger.warning(
        f"Lever {lever.lever_id}: self-referential absorb detected. Reclassifying as primary."
    )
    decision = LeverClassificationDecision(
        classification=LeverClassification.primary,
        justification="Self-referential absorb detected; reclassified to avoid data loss."
    )
```

**Part B — Circular absorb resolution** (insert after line 263, before
`keep_classifications` at line 265):
```python
# Detect and resolve circular absorb pairs (A→B and B→A: both would otherwise be dropped).
# Parse absorb targets by searching for other lever IDs in each absorb justification.
_lever_id_to_idx = {l.lever_id: i for i, l in enumerate(input_levers)}
_absorb_target: dict[str, str] = {}
for d in decisions:
    if d.classification == LeverClassification.absorb:
        for other_id in _lever_id_to_idx:
            if other_id != d.lever_id and other_id in d.justification:
                _absorb_target[d.lever_id] = other_id
                break

# Resolve circular pairs by keeping the earlier-indexed lever as primary.
_decisions_by_id = {d.lever_id: d for d in decisions}
for lever_a_id, lever_b_id in list(_absorb_target.items()):
    if _absorb_target.get(lever_b_id) == lever_a_id:
        idx_a = _lever_id_to_idx[lever_a_id]
        idx_b = _lever_id_to_idx[lever_b_id]
        keep_id = lever_a_id if idx_a <= idx_b else lever_b_id
        d_keep = _decisions_by_id[keep_id]
        if d_keep.classification == LeverClassification.absorb:
            d_keep.classification = LeverClassification.primary
            d_keep.justification = "Circular absorb pair resolved; retained as primary (earlier position)."
            logger.warning(
                f"Circular absorb resolved: keeping {keep_id}, the other leg remains absorb."
            )
```

Note: `LeverDecision` is a Pydantic model — mutating `.classification` directly
works in Pydantic v2 (mutable by default). Verify before merging if model config
uses `frozen=True`.

**Also document this in `OPTIMIZE_INSTRUCTIONS`** as a 6th failure mode:
```
- Circular absorb. A model absorbs lever A into B and simultaneously absorbs
  B into A; both are then dropped from output. Currently detected by UUID
  substring search in justification text and resolved by keeping the
  earlier-indexed lever.
```

---

## Deferred Items

**I4 — Remove numeric calibration range** (Direction 2): Do this in the
same PR or the next one. It works synergistically with Direction 1 by reducing
the pressure that makes Qwen produce circular absorbs in the first place.
Proposed wording is in Direction 2 above.

**I2 — Hierarchy-aware instance selection** (Direction 3): Higher effort,
requires UUID parsing infrastructure also used by Direction 1 Part B. Once
Part B is merged and validated, I2 can reuse `_absorb_target` to implement
position-based tie-breaking with minimal additional code.

**S1 — Rephrase "last resort" primary instruction** (Direction 4): Defer
until secondary adoption metrics from at least 2 more iterations are available.
The current wording is working for haiku and gpt-4o-mini; the cost of a
regression there outweighs the marginal gain from pushing gemini/llama3.1
toward secondary.

**I5 — save_clean + calls_succeeded fix in runner.py** (Direction 5):
Trivial housekeeping. Bundle with the next PR that touches runner.py.

**S3 — English-only prohibition in consequences field description**: The
`"Do NOT include 'Controls ... vs.', 'Weakness:'"` text in `LeverCleaned`
and `Lever` field descriptions contradicts `OPTIMIZE_INSTRUCTIONS`'s
language-agnosticism principle. Remove or replace with structural guidance.
Low urgency — no active harm observed.

**S4 — "See system prompt section 4" hard-coded reference**: Fragile but
currently correct. Flag for cleanup when sections are next restructured.

**N5 — Fabricated percentages in consequences**: Upstream issue in
`identify_potential_levers`. Not addressable in deduplicate_levers. Needs a
separate self-improve iteration on that step.

**Q4 from insight — gpt-5-nano justification noise**: Meta-commentary leaking
into justification fields ("Wait formatting: I inserted extra {}."). This is
a model-capability issue. Consider adding a post-processing sanitiser to strip
lines containing "Wait" or similar meta-commentary patterns. Low priority until
gpt-5-nano is used in production.
