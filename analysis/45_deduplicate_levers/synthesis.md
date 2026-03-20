# Synthesis

Covers 7 history runs (3/22–3/28), each across 5 plans = 35 total runs.
PR under evaluation: #365 — *feat: consolidate deduplicate_levers — classification, safety valve, B3 fix*.

---

## Cross-Agent Agreement

Both the insight and code-review files agree on the following:

- **gpt-4o-mini blanket-primary failure is the most critical unresolved problem.** 0 absorbs from 18 diverse input levers directly violates the step's deduplication objective. The model is compliant (no errors) but semantically failing.
- **B2 (safety valve semantic inversion) is the root cause of the blanket-primary failure.** The line "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role" maps *uncertainty → primary*, which is the opposite of the intended behaviour. The code-level fallback at `deduplicate_levers.py:249` also defaults to `primary`, compounding the message.
- **Hierarchy-direction errors affect 3/7 models** (llama3.1, gpt-5-nano, qwen3). All three make direction errors on the Procurement Language Specificity vs. Procurement Conditionality pair. No worked absorb example exists in the prompt.
- **Adding a worked absorb example to the system prompt is the most impactful prompt change available.** Both files recommend it (I1, H1, H2, C1). Secondary examples were added in PR #365 and demonstrably helped classify secondary levers; the same mechanism should apply to absorb direction.
- **Calibration hint hard-codes 15 levers while current inputs have 18** (B3). The ceiling of 10 absorbs = 56% of 18 may be cutting off genuine duplicates.
- **Gemini calibration fix is confirmed.** Gemini went from ~0–2 absorbs (PR #364 era) to 4 absorbs within the "4-10" range, landing on semantically sound merges. This is the clearest measurable improvement from PR #365.
- **B3 truncation fix (both `_build_compact_history` and `all_levers_summary`) is confirmed delivered.** Both conditional `...` additions are present in the current code.

---

## Cross-Agent Disagreements

There are no genuine disagreements between the two analysis files. Both are produced by the same Claude-class model and do not contradict each other. The code-review file extends the insight file with root-cause attribution and source-level evidence.

One tension worth noting: the insight file frames N1 (gpt-4o-mini zero absorbs) as possibly caused by harder input (18 diverse levers vs. 15 duplicated triplicates), while the code-review file argues B2 (semantic inversion) is the proximate cause regardless of input difficulty. Reading `deduplicate_levers.py:135`:

```
Use "primary" only as a last resort — if you genuinely cannot determine
a lever's strategic role after reading the full context.
```

This wording is unambiguous: it tells the model to use "primary" when confused. gpt-4o-mini's blanket assignment of "primary" is a rational response to this instruction. The harder input makes the problem observable, but the instruction is what enables it. **The code-review framing is correct.**

---

## Top 5 Directions

### 1. Fix the safety valve semantic inversion (B2)
- **Type**: prompt change + 1-line code fix
- **Evidence**: code_claude B2 (deduplicate_levers.py:135, :249); insight N1 (gpt-4o-mini 0 absorbs). Confirmed by reading source: line 135 says "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role." The phrase "if you cannot determine" maps uncertainty → primary. Line 249 code fallback also defaults to `primary`.
- **Impact**: gpt-4o-mini is a widely-used production model. Zero absorbs from 18 diverse levers means the deduplication step provides zero value for this model. Fixing the semantic inversion is the most likely single change to push gpt-4o-mini into the 4–10 absorb range. Affects all models that treat uncertainty as a trigger for "primary", which may be more than just gpt-4o-mini.
- **Effort**: Low. One sentence rewrite in DEDUPLICATE_SYSTEM_PROMPT + one-line change in the error-fallback at line 249.
- **Risk**: Models that currently assign "primary" correctly (gemini, haiku) should not be affected — the wording change only constrains the uncertain case. Small risk that very conservative models shift too many levers to "secondary", but this is recoverable and less harmful than zero absorbs.

**Specific fix:**

Replace line 135:
```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's strategic role after reading the full context. Describe what is unclear in the justification.
```
With:
```
Only assign "primary" for levers you have actively confirmed are essential strategic decisions. If genuinely uncertain whether a lever is primary vs. secondary, assign "secondary" — do not default to primary out of caution.
```

Replace line 249:
```python
classification=LeverClassification.primary,
```
With:
```python
classification=LeverClassification.secondary,
```

---

### 2. Add a worked absorb example to the system prompt (I1/H1/H2)
- **Type**: prompt change
- **Evidence**: insight H1, H2, C1; code_claude I1. 3/7 models show hierarchy-direction errors on the same lever pair (Procurement Language Specificity vs. Procurement Conditionality). No worked example of a correct absorb currently exists.
- **Impact**: The secondary-examples addition in PR #365 is the direct precedent — it helped models classify secondary levers correctly. A parallel absorb example should help models (a) absorb at all (reducing blanket-primary) and (b) pick the correct direction (reducing hierarchy errors in gpt-5-nano and qwen3). Affects hierarchy violations in 3/7 models.
- **Effort**: Low. Add ~3 sentences after the "expect 4–10" calibration hint.
- **Risk**: Example lock — the note in `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS warns that a single example causes weaker models to copy its phrasing. Mitigate by keeping the example domain-general or providing two structurally different examples.

**Draft wording (append to DEDUPLICATE_SYSTEM_PROMPT after the calibration hint):**
```
Example absorb: Lever "Procurement Conditionality" (enforces requirements via contract penalty clauses)
absorbs INTO "Procurement Language Specificity" (governs what procurement documents say), because
conditionality is one specific enforcement mechanism within the broader category of procurement
language. The reverse — absorbing language specificity into conditionality — would collapse the
broader concept into its narrower subset, which is wrong hierarchy direction.
```

---

### 3. Update calibration hint to match actual input size (B3)
- **Type**: prompt change
- **Evidence**: code_claude B3 (deduplicate_levers.py:137). Current text: "In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed." Runs 22–28 feed 18 levers. The ceiling of 10 absorbs represents 56% of 18, which gpt-5-nano already hits (absorbed exactly 10), potentially leaving genuine duplicates untouched.
- **Impact**: Primarily affects aggressive deduplicators (gpt-5-nano) that interpret the upper bound as a hard stop. Medium impact: most models don't hit the ceiling, but the stale "15 levers" example also undermines the authority of the calibration hint for confused models.
- **Effort**: Very low. Change one sentence.
- **Risk**: Widening the range further (e.g., "4–12") may cause over-absorption in models that already perform correctly.

**Specific fix:**

Replace:
```
In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed.
```
With:
```
In a well-formed set of 15–20 levers, expect 4–10 (or more on highly similar inputs) to be absorbed or removed.
```

---

### 4. Fix `deduplication_justification` backwards-compatibility gap in enrich_potential_levers (I4)
- **Type**: code fix
- **Evidence**: code_claude I4. `enrich_potential_levers.InputLever.deduplication_justification: str` has no default value. PR #365 claims backwards compatibility, but calling enrich with levers from the identify step (skipping deduplication) raises `ValidationError`.
- **Impact**: All code paths that bypass deduplicate_levers (e.g., testing, partial pipelines) will break. Low probability of hitting in production runs, but breaks testing and self_improve iterations that run individual steps.
- **Effort**: Trivial. Add `= ""` default.
- **Risk**: None. Empty string default is a safe sentinel; downstream code that consumes `deduplication_justification` should handle empty string gracefully.

---

### 5. Document cross-domain absorption as a 6th OPTIMIZE_INSTRUCTIONS failure mode (I3/C4)
- **Type**: documentation change (OPTIMIZE_INSTRUCTIONS in deduplicate_levers.py)
- **Evidence**: insight N2 (llama3.1 absorbs Procurement Conditionality → Fallback Certification Criteria; Demonstrator Fidelity → Fallback Authentication Modality — completely different domains). Currently only 5 failure modes are documented; cross-domain absorption is absent.
- **Impact**: Self-improve iterations reading OPTIMIZE_INSTRUCTIONS will be alerted to watch for this pattern. Affects only small/local models (llama3.1), so the operational impact is limited, but the documentation gap means future iterations will keep rediscovering it.
- **Effort**: Very low. Add one paragraph to OPTIMIZE_INSTRUCTIONS.
- **Risk**: None. Pure documentation.

**Draft addition:**
```
- Cross-domain absorption. A model absorbs a lever into a target from a
  completely unrelated domain (e.g., a procurement lever absorbed into a
  technical certification lever, or a demonstrator-fidelity lever absorbed
  into an authentication-modality lever). Small/local models (llama3.1)
  exhibit this pattern when lever names share a word but not a concept.
  No code-level validation currently detects wrong-domain absorb targets.
```

---

## Recommendation

**Fix B2 first: the safety valve semantic inversion.**

This is the right first move because:

1. **It is the confirmed root cause of the most impactful failure.** gpt-4o-mini's 0-absorb result on 18 diverse levers is not a model capability gap — it is the model correctly following an instruction that points in the wrong direction. The instruction "use 'primary' if you cannot determine the role" is a rational escape hatch that gpt-4o-mini and similar mid-tier models exploit. Fixing the instruction removes the escape hatch.

2. **It affects both the prompt and the code.** The prompt fix removes the escape hatch; the code fix at line 249 removes the second path (error-fallback → primary). Both reinforce the same wrong behaviour; both must change together for the fix to hold.

3. **It is low-effort and low-risk.** One sentence rewrite in DEDUPLICATE_SYSTEM_PROMPT and one line in the fallback at line 249. No structural changes. Gemini, haiku, and gpt-oss-20b, which currently perform correctly, should be unaffected — the change only tightens the uncertain case.

4. **It is measurably testable.** The next self_improve iteration should show gpt-4o-mini producing ≥4 absorbs from 18 diverse inputs. If it doesn't, that tells us the residual problem is model-specific (capability, not instruction), and we know to move to direction 2 (worked absorb example).

**Files to change:**

- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`, line 135: rewrite the safety valve sentence.
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`, line 249: change `LeverClassification.primary` → `LeverClassification.secondary`.

**New line 135 text:**
```
Only assign "primary" for levers you have actively confirmed are essential strategic decisions. If genuinely uncertain whether a lever is primary vs. secondary, assign "secondary" — do not default to primary out of caution.
```

**New line 249:**
```python
classification=LeverClassification.secondary,
```

---

## Deferred Items

- **Direction 2 (worked absorb example)**: Implement immediately after B2 fix if gpt-4o-mini still shows zero absorbs. The worked example additionally fixes hierarchy-direction errors in gpt-5-nano and qwen3, which are independent of the safety valve issue. High expected return; defer only to keep the first iteration's change isolated and measurable.

- **Direction 3 (calibration hint update)**: Low effort, can be bundled with B2 fix in the same PR without adding noise. If bundled, ensure the test set still has ~18 input levers so the calibration change can be verified.

- **Direction 4 (enrich_potential_levers backwards-compat)**: Trivial fix; bundle with the next PR.

- **Direction 5 (OPTIMIZE_INSTRUCTIONS documentation)**: Document after confirming the cross-domain pattern persists with the new prompt. Low priority but costs nothing to add.

- **S1 (structured absorb_target_id field)**: Medium-effort schema change that would enable chain-absorption detection and absorb-target validation. Worth doing after the prompt fixes are stable — it's a structural improvement that requires coordinated changes to the schema, prompt, and downstream consumers.

- **B4 (calls_succeeded masking in runner.py:155)**: Low severity. Replace `len(result.response)` with actual LLM call count. Fix in a cleanup PR.

- **B1 (user_prompt stores levers JSON not project_context)**: Low severity. Naming inconsistency that confuses analysis scripts reading saved output files. Fix `deduplicate_levers.py:296` to `user_prompt=project_context` in a cleanup PR.

- **S2 (orphaned "Prior decisions" header on empty prior_decisions)**: Rare edge case (first-lever compaction). Guard with `if prior_decisions:` in `_build_compact_history`. Low priority.

- **S4 (all_levers_summary truncates consequences at 120 chars)**: A contributing factor to hierarchy-direction errors — models can't see the distinguishing detail. Increasing the truncation limit (e.g., to 200 chars) is low-risk but may increase token cost. Revisit after the prompt fixes are in place.

- **N5 confound (input lever set changed between before/after batches)**: Future self_improve iterations should hold the input set constant (use the same baseline levers in before and after batches) to cleanly isolate prompt/code effects. Not actionable as a code change but important for experimental design.
