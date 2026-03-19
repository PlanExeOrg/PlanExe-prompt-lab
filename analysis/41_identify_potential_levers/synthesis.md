# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude and code_claude) converge on the same core conclusions:

1. **PR #361 verdict: CONDITIONAL.** The `lever_index` field removal is mechanically correct — the field was confirmed dead code (never read by the `LeverCleaned` mapping at lines 360–374 of `identify_potential_levers.py`). The stated risk (index prefixes leaking into `name`/`consequences`) did not materialize across any of the 7 models tested.

2. **Haiku step-gate regression is real.** After PR #361, haiku now triggers `partial_recovery` on all 5 plans (down from 2/5), because it generates 8–12 levers per call instead of ~6–7, crossing `min_levers=15` after just 2 calls. The mechanism is plausible: removing `lever_index: int` makes each lever's JSON ~15–20 tokens shorter, allowing more levers per call within haiku's token budget.

3. **The fix is clear: raise `min_levers` from 15 to 18.** Both agents independently recommend this as the follow-up. With haiku generating 8 levers/call, 2 × 8 = 16 < 18, forcing a third call. Models generating 6–7/call already need 3 calls (3 × 7 = 21 ≥ 18) and would be unaffected.

4. **B1 (false-positive `partial_recovery` in runner.py) is real.** The check at runner.py:517–523 emits `partial_recovery` whenever `calls_succeeded < 3`, regardless of whether `min_levers` was met. A healthy haiku run producing 20 levers in 2 calls is flagged as degraded. This distorts metrics.

5. **The "none/all three options" review_lever template lock (~87%) is unchanged** by PR #361 and remains the pre-existing target from analysis 40. Both agents confirm it needs a separate PR targeting the `review_lever` field description.

---

## Cross-Agent Disagreements

No substantive disagreements. Both agents read the source code consistently and arrived at the same causal chain: `lever_index` removal → more compact per-lever JSON → more levers per call → haiku crosses step-gate threshold in 2 calls → all 5 plans emit `partial_recovery`.

The only nuance: the code review (code_claude) notes that B1's false-positive means the "haiku -20pp regression" metric is partly measuring valid early exits rather than failures. The insight file acknowledges this is a behavioral shift, not a reliability failure. Both perspectives are correct and complementary.

Source code verification confirms:
- `min_levers = 15` at `identify_potential_levers.py:285` (confirmed)
- Step-gate at line 348: `if len(generated_lever_names) >= min_levers: break` (confirmed)
- `partial_recovery` trigger at `runner.py:517–523`: `calls_succeeded < 3` with no lever-count check (confirmed)
- `LeverCleaned` mapping never reads `lever_index` (confirmed — uses `uuid.uuid4()` for `lever_id`)

---

## Top 5 Directions

### 1. Raise `min_levers` from 15 to 18
- **Type**: code fix
- **Evidence**: insight_claude (C1/H2), code_claude (I1); confirmed by source at `identify_potential_levers.py:285`
- **Impact**: Haiku partial_recovery expected to drop from 5/5 plans back toward 0/5 plans. The third call uses a diversity-constraining prompt ("Generate MORE levers with completely different names") that provides a qualitatively distinct perspective. Restoring this call for haiku improves lever diversity for all 5 haiku-run plans. Models generating 6–7/call are unaffected (3 × 7 = 21 ≥ 18 still requires 3 calls). One-line change with no downstream schema impact.
- **Effort**: Low — single integer constant change
- **Risk**: Minimal. Models generating ≥ 18 levers in 2 calls (≥ 9/call) would still exit after 2 calls, but this is the upper edge of observed haiku behavior. No downstream data format changes.

### 2. Fix false-positive `partial_recovery` in runner.py (B1)
- **Type**: code fix
- **Evidence**: code_claude (B1); corroborated by insight_claude's observation that haiku's 2-call runs are valid step-gate exits
- **Impact**: Corrects distorted metrics for all future analyses. Currently, every healthy early-exit (e.g., haiku producing 20 levers in 2 calls) is flagged as degraded output. Fixing this would make `partial_recovery` accurately signal only genuine under-delivery (lever_count < min_levers after all calls). Required for reliable insight analysis going forward.
- **Effort**: Medium — requires surfacing lever count in `PlanResult` (runner.py:96–101), passing it from `IdentifyPotentialLevers.execute()`, and updating the emit condition at runner.py:517–523. Adding `I3` (`min_levers_met: bool` to the result dataclass) would simplify this.
- **Risk**: Low. The change is purely in event semantics — no effect on plan execution or downstream outputs.

### 3. Fix `review_lever` field description to break "none/all three options" template lock
- **Type**: prompt change
- **Evidence**: insight_claude (H3); code_claude (Trace table row 4); analysis 40 designated this the top priority
- **Impact**: The `review_lever` field description currently reads "state the specific gap the three options leave unaddressed." This structural phrase drives haiku to start 87% of reviews with "none of the three options address/resolve/specify…" — a near-verbatim copy of the field description. OPTIMIZE_INSTRUCTIONS (lines 86–92) explicitly warns that structural cues in field descriptions drive template lock. Fixing this field description would reduce the lock rate across haiku and likely other weaker models. Affects all 5 plans × haiku (and potentially other models that show subtler forms of the same lock).
- **Effort**: Low — one field description change, but requires careful wording. The fix must describe required *content* ("identify the primary trade-off and the specific gap") without prescribing *sentence structure*. Candidate wording: `"A short critical review (one sentence, 20–40 words): name the primary trade-off this lever introduces, then name what aspect of the problem the three options collectively leave unaddressed."` The word "name" rather than "state" avoids the structural "none of the three options…" trigger.
- **Risk**: Low-medium. Field description changes are prompt changes — they require a self_improve iteration to verify. Weaker models may shift to a different template lock pattern.

### 4. Fix `options` field description vs. validator contradiction (S2)
- **Type**: code/prompt fix
- **Evidence**: code_claude (S2)
- **Impact**: The field description says "Exactly 3 options... No more, no fewer" but the validator at lines 141–153 only enforces a lower bound (`len(v) < 3`). Models that follow the description generate exactly 3; models that don't may generate 4–5, pass validation silently, and pass extra options downstream (callers may expect exactly 3). Fixing the description removes the false promise and prevents silent downstream contract violations.
- **Effort**: Low — either drop "No more, no fewer" from the description, or add an upper-bound trim in the validator. Trimming is safer than raising (avoids a full retry for an extra option).
- **Risk**: Low. Removing "No more, no fewer" from the description may cause some models to generate 4+ options more often, but the trim would handle that cleanly.

### 5. Update `OPTIMIZE_INSTRUCTIONS` with schema-compactness and over-generation notes (I4/I5)
- **Type**: code change (documentation within source)
- **Evidence**: code_claude (I4, I5); insight_claude (OPTIMIZE_INSTRUCTIONS Alignment section)
- **Impact**: PR #361 revealed that removing a single field from `Lever` shifted haiku's per-call lever count from 6–7 to 8–12, triggering early step-gate exit. This is not currently documented in OPTIMIZE_INSTRUCTIONS. Future self_improve iterations that touch the `Lever` schema will not know to check for this effect. Adding the note prevents repeated discovery of the same causal chain. The existing text ("Over-generation is fine; step 2 handles extras") is misleading — it's true at the plan level but ignores the per-call over-generation effect on step-gate timing.
- **Effort**: Low — prose addition only, no runtime effect
- **Risk**: None

---

## Recommendation

**Raise `min_levers` from 15 to 18** in `identify_potential_levers.py` at line 285.

**Why first:** This is the only change that directly addresses the regression introduced by PR #361. The PR's schema cleanup was correct and should be kept; the side effect (haiku consistently exiting the step-gate after 2 calls) reduces per-plan lever diversity by skipping the third call's uniquely constrained "completely different names" prompt. Raising `min_levers` recovers that diversity with a single integer change, no prompt modification, and no downstream impact.

**Specific change:**

File: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, line 285

```python
# Before:
min_levers = 15

# After:
min_levers = 18
```

**Rationale:** With haiku generating 8 levers/call, 2 × 8 = 16 < 18 → third call required. With other models generating 6–7/call, 3 × 7 = 21 ≥ 18 → they still exit after the third call, unchanged. Models at exactly 6/call would need a 4th call (3 × 6 = 18 ≥ 18 on the 3rd call — exactly at threshold). This is still safe: the loop cap is `max_calls=5`, and 4 calls at 6 levers/call yields 24 levers, which is fine.

**Expected outcome:** Haiku partial_recovery drops from 5/5 plans back toward 0/5 (or at worst 1–2/5 on stochastic variance days). Overall call efficiency should recover from 93.3% toward 97%+.

**After this change:** The next iteration should target Direction 3 — fixing the `review_lever` field description to break the "none/all three options" template lock at ~87% in haiku. That is the pre-existing top priority from analysis 40 and is not addressed by any change in this analysis.

---

## Deferred Items

- **B1 (false-positive `partial_recovery` in runner.py):** Direction 2 above. Correct after Direction 1 so that the next iteration's metrics accurately reflect true under-delivery vs. valid early exits. Medium effort.

- **Review_lever template lock fix (Direction 3):** The primary quality issue post-PR. Target the `review_lever` field description (lines 119–127 of `identify_potential_levers.py`) and/or the Section 4 examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`. Requires its own self_improve iteration to measure effect.

- **S3 (English-specific prohibition text in `consequences` field description):** Lines 110–112 reference `'Controls ... vs.'` and `'Weakness:'` — OPTIMIZE_INSTRUCTIONS explicitly warns against English-keyword instructions (lines 61–68). Replace with a structural description: "Do not include critical analysis or trade-off commentary in this field — those belong in review_lever." Low effort, low risk.

- **S1 (closure captures `messages_snapshot` by name):** Latent trap if `LLMExecutor.run()` is ever made async. Safe today; address when async is introduced.

- **B2 (silent under-delivery after error swallowing):** Low severity, masked by `partial_recovery`. Worth adding a post-loop check `if len(generated_lever_names) < min_levers` with explicit logging, but not urgent.

- **OPTIMIZE_INSTRUCTIONS updates (I4/I5):** Add schema-compactness note and revise over-generation language. Safe to bundle with any of the above PRs.
