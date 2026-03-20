# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — `runner.py:125,546–552` — `partial_recovery` warning fires on normal 2-call runs

`_run_levers` (line 125) warns when `actual_calls < 3`. `_run_plan_task` (lines 546–552) emits a `partial_recovery` event for the same condition. Yet the inline comment on line 122 explicitly states: "A 2-call success is normal for models that produce 8+ levers per call."

The threshold is therefore wrong: it fires for successful 2-call runs whenever the model is productive, creating false alarms in events.jsonl. The right check is whether enough levers were generated, not whether at least 3 calls occurred.

```python
# runner.py:125 — fires for normal 2-call runs
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

```python
# runner.py:546–552 — emits partial_recovery for all runs with < 3 calls
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

---

### B2 — `deduplicate_levers.py:102` — Contradictory `primary` fallback instruction

Line 102 reads:
> "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role, classify it as primary so a potentially important lever is not lost."

The first clause ("only as a last resort") instructs models to avoid `primary`; the second ("classify it as primary so a potentially important lever is not lost") instructs models to use `primary` as the safe default when uncertain. These are opposite signals.

Observable effect: weaker models (llama3.1 on sovereign_identity, run 50) read "only as a last resort" and avoid `primary`, defaulting every undecided lever to `secondary` instead. Result: 2 primary, 16 secondary, 0 remove — exactly the opposite of the intent.

The intended meaning was: "when uncertain between keeping and removing, keep the lever as primary rather than removing it." That intent needs to be expressed clearly without the "last resort" framing.

---

### B3 — `deduplicate_levers.py:91` — System prompt `secondary` definition causes template-lock justifications

The `secondary` definition in `DEDUPLICATE_SYSTEM_PROMPT` (line 91) provides a complete, reusable phrase:
> "secondary: Lever is distinct and useful but supporting or operational — matters for delivery but not a top-level strategic choice"

Llama3.1 on sovereign_identity (run 50) copies this phrase verbatim into every `secondary` justification. All 14 secondary justifications follow the same template:
> "While [X] is an important consideration for influencing policy and stakeholder perception, it is distinct and useful but supporting or operational. The project's objective is to establish the technical, regulatory, and political basis for formal platform-neutral access requirements and a certified fallback authentication path in Denmark, which suggests that [X] is more of a supportive lever rather than a primary strategic decision."

Evidence: `history/3/50_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — every secondary entry from lever 9b95a5d0 through d42b2771 uses this identical pattern. The justifications contain no lever-specific reasoning; they are the secondary definition pasted over a fixed project-context sentence.

This failure mode is documented in `identify_potential_levers.py`'s `OPTIMIZE_INSTRUCTIONS` (lines 69–82) but is absent from `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS`. The phrase "distinct and useful but supporting or operational" is the trigger; it is reusable in any domain and is short enough to memorize.

Secondary effect: because the justification is a template, the model loses the ability to distinguish levers from each other within the secondary class — all are treated as identically generic — which also suppresses `remove` decisions. A model that cannot articulate why two levers differ cannot decide to remove one.

---

## Suspect Patterns

### S1 — `deduplicate_levers.py:106` — Removal calibration anchored to 15 levers

> "In a well-formed set of 15 levers, expect 4–10 to be removed."

The generate step (`identify_potential_levers.py:291`) sets `min_levers = 15` and `max_calls = 5`, so the deduplicate step regularly receives 15–20 levers. For 18 levers the calibration "4–10 removals" underestimates the expected range (should be ~5–12); the upper bound 10 may act as a stopping signal for compliant models before they finish deduplicating.

### S2 — `identify_potential_levers.py:121–123,147–159` — "Exactly 3 options" in description but validator only enforces ≥3

`Lever.options` field description and the system prompt (line 231) both say "exactly 3 qualitative strategic choices, no more, no fewer." The validator at line 157 only checks `len(v) < 3`. Models that produce 4+ options per lever pass silently. The mismatch between prompt instruction and validation behavior is a minor inconsistency; it won't cause failures but could confuse model behavior analysis.

### S3 — `identify_potential_levers.py:173` — `review_lever` minimum length too permissive

The `check_review_format` validator at line 173 enforces a 10-character minimum. The system prompt specifies "one sentence (20–40 words)" ≈ 100–200 characters. A string like "Trade-off." (10 chars) passes validation while containing no useful content. The soft target could be raised to 40 characters (roughly 8 words) to catch near-empty reviews without being too aggressive.

### S4 — `deduplicate_levers.py:22–25,250` — `LeverClassification` enum defined but inconsistently used

`LeverClassification` (lines 22–25) is only used in `keep_classifications` (line 250). `LeverClassificationDecision.classification` and `LeverDecision.classification` use `Literal["primary", "secondary", "remove"]` instead of the enum. The values are duplicated across the enum and the Literal types. If a new classification value were added, it would need to be updated in three places. Not a logic bug, but increases maintenance surface.

### S5 — `deduplicate_levers.py` — No validation that `remove` justifications cite a lever ID

The system prompt (line 92) instructs: "Explicitly state the lever ID it merges into and why removing it loses no meaningful detail." There is no code-level check that `remove` decisions actually contain a UUID. In practice (insight P2) all models complied, but the enforcement is prompt-only. A regex check for a UUID pattern in `remove` justifications would make this structural guarantee explicit.

---

## Improvement Opportunities

### I1 — Add classification summary counts to output metadata

Currently validating quality requires parsing all `response` entries in `002-11-deduplicated_levers_raw.json`. Adding a top-level summary:
```json
"classification_summary": {"primary": 9, "secondary": 3, "remove": 6}
```
would let monitoring scripts immediately flag runs with 0 removes (llama3.1 on sovereign_identity) without deep parsing. Addresses insight C1.

### I2 — Add chain-removal detector

When lever A removes into B, and B also removes into C, A's justification ("merge into B") becomes misleading since B no longer exists in the output. A post-processing walk over `remove` justification lever IDs would detect:
- chains (A→B→C): log a warning listing the chain
- circular references (A→B, B→A): log an error; both levers are dropped, which is likely unintended

Addresses insight C2.

### I3 — Fix the `primary` fallback instruction (B2)

Replace lines 102–103 of `deduplicate_levers.py`:
```
# current (contradictory)
Use "primary" only as a last resort — if you genuinely cannot determine a lever's
strategic role, classify it as primary so a potentially important lever is not lost.
```
with a non-contradictory formulation, e.g.:
```
When uncertain between primary and secondary, prefer primary — a false positive here
is recoverable downstream. When uncertain between removing and keeping, prefer secondary
over remove to avoid losing a potentially important lever.
```

### I4 — Fix `partial_recovery` warning threshold (B1)

In `runner.py`:
- Line 125: change `actual_calls < 3` to `actual_calls < 2` (warn only when exactly 1 call succeeded, which is genuinely anomalous).
- Lines 546–552: apply the same threshold change so `partial_recovery` events are not emitted for successful 2-call runs.

Alternatively, replace the call-count check with a lever-count check: warn if `len(result.levers) < min_levers` after the adaptive loop.

### I5 — Dynamic lever-count calibration (S1)

Replace the hardcoded "15 levers" calibration in `DEDUPLICATE_SYSTEM_PROMPT` (line 106) with a value derived from the actual input size, injected at runtime:
```python
calibration = f"With {len(input_levers)} input levers, expect {len(input_levers)//4} to {len(input_levers)//2} removals."
```
Or use a percentage framing independent of absolute count.

### I6 — Document template-lock failure mode in `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS`

`identify_potential_levers.py` documents template-lock at length (lines 69–92). `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS` (lines 111–125) lists 5 failure modes but omits template-lock. Add a mode 6:
> "Definition mirroring: Weak models copy the classification definition ('distinct and useful but supporting or operational') verbatim into every secondary justification, producing content-free boilerplate. Fix: avoid complete reusable phrases in classification definitions; describe the *test* for each class rather than its dictionary meaning."

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|-----------------|-----------------|
| **N1** — llama3.1 produces 0 removes on sovereign_identity | **B3** (template-lock secondary justifications) + **B2** (contradictory "last resort" instruction). Model copies secondary definition, loses ability to distinguish levers, avoids remove. |
| **N4** — llama3.1 over-demotes levers to `secondary` | **B3** directly: the template lock forces every undecided lever into `secondary` because the model has a ready-made boilerplate for that class. |
| **Q1** (synthesis question) — why does llama3.1 behave differently on sovereign_identity vs hong_kong_game? | sovereign_identity's plan context includes a long recurring sentence that gets absorbed into the B3 template. hong_kong_game's more varied context may not offer the same reusable scaffold. |
| **N2** — hierarchy direction inconsistencies across models | Not directly traceable to a code bug. The system prompt rule at lines 98–100 is structurally correct but provides no disambiguation heuristic for near-synonyms. **S1** (calibration) may amplify this by causing models to stop removing early. |
| **N3** — gpt-5-nano removes wrong lever despite plan brief naming it as a key risk | No code path reads the plan brief to validate remove decisions. **S5** (no remove-justification validation) is a partial contributor, but this is fundamentally a prompt-quality issue. |
| **P2** — All models cite lever IDs in remove justifications | System prompt line 92 is effective. No code change needed, but **S5** notes the absence of a structural check. |
| **P4** — llama3.1 degenerate collapse eliminated | The collapse was caused by the old `absorb` category; removing it (PR #372) is the correct fix. |
| **B1** (false `partial_recovery` events) | Would appear in events.jsonl for any 2-call successful run. Does not affect output quality but pollutes event monitoring. |

---

## PR Review

**PR #372: feat: simplify lever classification to primary/secondary/remove**

### Implementation correctness

The current code correctly implements the 3-way taxonomy:

1. `LeverClassification` enum (lines 22–25): `primary`, `secondary`, `remove` — matches PR description.
2. `LeverClassificationDecision.classification` (line 29): `Literal["primary", "secondary", "remove"]` — correct.
3. `OutputLever.classification` (line 59): `Literal["primary", "secondary"]` — correct; `remove`d levers are filtered at line 265–267 before `OutputLever` is constructed, so the narrowed type is safe.
4. `keep_classifications` (line 250): `{LeverClassification.primary, LeverClassification.secondary}` — correct; `remove` decisions are silently filtered.
5. System prompt (lines 88–109): defines all three classes, requires lever ID citation in `remove` justifications, includes calibration guidance and hierarchy rules. Matches PR description.

The `absorb` category is fully gone. The information it carried (which lever absorbs the removed one) is now in the `remove` justification's free-text field, and all models in runs 50–56 comply correctly (insight P2).

### Gaps and edge cases

**Gap 1 — No structural validation that `remove` justifications cite a lever ID.**
The system prompt requires it; the code does not check it. This is prompt-only enforcement. All 7 models complied in runs 50–56, but a future model regression would go undetected. A UUID pattern check on `remove` justifications would harden this.

**Gap 2 — `LeverClassification` enum is not used in `LeverClassificationDecision` or `LeverDecision`.**
Both use `Literal[...]` strings. The enum was likely part of an older design and was not removed during the PR. Not a bug, but creates dual maintenance surface.

**Gap 3 — Contradictory `primary` fallback instruction (B2) is a pre-existing problem not introduced by this PR.**
The PR did not change line 102. However, the PR's taxonomy change from `keep` to `primary`/`secondary` makes this more important: `keep` had a neutral connotation; `primary` carries a "top-tier strategic decision" connotation that makes "last resort" even more confusing.

**Gap 4 — Template-lock risk in secondary definition (B3) is unchanged.**
The `secondary` definition phrase "distinct and useful but supporting or operational" existed before the PR and was not modified. The PR did not introduce this problem, but it is now the dominant quality issue for weaker models on this step.

### Does the PR fix what it claims?

Yes. The hypothesis ("fewer categories means each class gets exercised more") is empirically validated:
- All 35 runs succeeded (no LLMChatErrors).
- All models cite absorbing lever IDs in `remove` justifications (P2).
- Haiku's remove rate improved from 28% to 39% on hong_kong_game (P5).
- The degenerate llama3.1 catch-all collapse into Risk Framing is eliminated (P4).

The PR introduces no regressions. The implementation is clean and the intent matches the code.

**Verdict: KEEP.** The PR is correct and well-implemented.

---

## Summary

Three confirmed bugs, five suspect patterns, and six improvement opportunities.

The most impactful issues are B3 (template-lock in the `secondary` definition causing llama3.1 to produce boilerplate justifications and 0 removes) and B2 (contradictory `primary` fallback instruction driving models toward `secondary` as the default). Together they explain insight N1 and N4 entirely. Both are pre-existing prompt bugs, not introduced by PR #372.

B1 (false `partial_recovery` events) is a runner logic bug that creates noise in events.jsonl but does not affect output quality.

PR #372 is correctly implemented. The main remaining quality problem (template-lock in weaker models) requires fixing the `secondary` definition phrasing and adding template-lock to `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS`.
