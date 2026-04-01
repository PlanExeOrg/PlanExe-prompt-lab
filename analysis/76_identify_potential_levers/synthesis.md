# Synthesis

## Cross-Agent Agreement

Both the insight agent and the code review agent converge on the following:

1. **PR #482 achieves its stated goal.** The qwen3-30b `"X creates Y risks, leaving Z gaps"` template lock is eliminated (0 instances across 101 levers in run 42). The haiku `"All three options X, but none address Y"` lock (~85% → ~0%) and gpt-oss-20b's `"options do not address/overlook"` pattern are also eliminated as side-effects of removing the structural phrase from the `review_lever` field description. The mechanism is confirmed: structural phrases in field descriptions act as fill-in-the-blank templates for smaller models; removing them breaks the pattern.

2. **llama3.1 later-call consequence parroting is a real regression.** Run 39 shows levers 8–15 where `review_lever` is a near-verbatim restatement of `consequences` with only `"could" → "can"` substitution. Both agents agree the root cause is the subsequent-call user prompt (`identify_potential_levers.py:300–305`), which focuses the model's attention on name novelty with no review-quality guardrail. The code review (S1) and insight (Negative #1) name the same source lines.

3. **haiku-4.5 fabricated numbers are a genuine regression (+8.3pp).** Fabricated percentage claims and dollar figures rose from 22.6% (run 93) to 30.9% (run 45). Both agents flag this violates OPTIMIZE_INSTRUCTIONS ("Fabricated numbers") and the system prompt Section 5 prohibition. Both note the numbers appear in `consequences` and `options`, not `review_lever`, so the PR's field-description change is not the direct cause — the PR #479 "positive framing" instruction carried forward is the suspected culprit.

4. **Three bugs in `runner.py` are independently confirmed.** The code review identifies B1 (partial_recovery threshold mismatch), B2 (global dispatcher contamination under parallel execution), and B3 (timed-out thread continues writing output). B3 is directly evidenced by run 40's gpt-oss-20b behavior: two plans logged `"plan timeout after 600s"` yet both produced complete lever files with 18 levers each.

5. **No cross-field validator exists to catch consequence parroting.** Both agents note that `check_review_format` only enforces minimum length and no square brackets — it cannot detect near-verbatim consequence restatements. This lets llama3.1's parroting pass validation silently.

---

## Cross-Agent Disagreements

**No significant disagreements were found.** The two agents used different analytical lenses (quality metrics vs. code structure) but their findings are fully consistent. One minor divergence in framing:

- The code review (S1) calls the subsequent-call prompt gap a "suspect pattern." The insight (Negative #1) treats it as a confirmed root cause. Reading the actual source code confirms the code review is correct to hedge: the system prompt is repeated unchanged across all calls (line 283–285: `system_message` is constructed once, reused), so call-1 levers do receive the full review guidance. The shift in quality between call 1 and calls 2+ is real and the subsequent-call user message is the most plausible differentiator. Both characterizations are accurate; "confirmed" vs. "suspect" is a degree-of-evidence distinction, not a factual disagreement.

---

## Top 5 Directions

### 1. Add anti-parroting guidance to the subsequent-call user prompt
- **Type**: prompt change
- **Evidence**: Both agents (insight Negative #1, code review S1/I1). `identify_potential_levers.py:300–305`. llama3.1 levers 8–15 in run 39 silo plan show >90% word overlap between `consequences` and `review_lever`.
- **Impact**: Fixes llama3.1 consequence-parroting in calls 2+. Low risk of affecting call 1 (not touched) or other models (instruction is additive). Directly addresses a confirmed quality regression visible in the current production code.
- **Effort**: Low — one sentence inserted into the subsequent-call `prompt_content` string at line 302.
- **Risk**: The reminder sentence itself could become a template if it uses structural language. Mitigation: phrase it as a prohibition (`"not a restatement of the consequence"`) rather than a structural cue. The code review's suggested wording (`"Each review_lever must be a genuine critical assessment — not a restatement of the consequence — in one sentence (20–40 words)."`) is already a prohibition, not a template starter.

---

### 2. Investigate and remove (or neutralize) the "positive framing" instruction from PR #479 to address haiku fabricated numbers
- **Type**: prompt change
- **Evidence**: Insight Negative #2 and H2. haiku fabricated-number rate: 22.6% (run 93, before PR #479+#482) → 30.9% (run 45, after). Numbers appear in `consequences` and `options`, not `review_lever`. The `review_lever` change in PR #482 cannot be the cause; the "positive framing" instruction carried from PR #479 is the remaining candidate. OPTIMIZE_INSTRUCTIONS explicitly prohibits fabricated numbers.
- **Impact**: Affects all haiku plans — 34/110 levers (30.9%) contain fabricated percentages or dollar figures that violate the system prompt's Section 5 prohibition and the OPTIMIZE_INSTRUCTIONS "Fabricated numbers" rule. If positive framing is confirmed as the cause, removing it restores haiku's fabricated-number rate toward ~22%. Content quality regression on 30.9% of levers for the highest-capability tested model is high-impact.
- **Effort**: Low-to-medium. The effort is in the investigation: run a targeted haiku experiment with and without the positive-framing instruction to confirm causality. If confirmed, removal is a one-line deletion.
- **Risk**: Removing positive framing may reintroduce some pessimistic framing patterns that PR #479 fixed. Must verify that removing it does not regress the original PR #479 improvements (the specific patterns PR #479 targeted).

---

### 3. Add a `model_validator` for consequence-parroting detection
- **Type**: code fix (validator)
- **Evidence**: Code review S3/I2. `identify_potential_levers.py:160–176`. `check_review_format` only enforces length and no square brackets; it cannot detect near-verbatim consequence restatements. The llama3.1 parroting pattern (>90% word overlap) passes all current validation silently.
- **Impact**: Structural enforcement catches parroting at validation time and forces a retry, rather than relying solely on the prompt guidance from Direction 1. Pairs with Direction 1: the prompt change steers models away from parroting; the validator rejects the rare cases that slip through. Benefits any model that might exhibit this pattern.
- **Effort**: Medium — requires a `model_validator` on `Lever` with word-overlap logic and threshold tuning to avoid false positives on short levers that naturally share domain vocabulary with their consequences.
- **Risk**: Over-sensitive threshold could reject valid reviews. Mitigation: set the overlap threshold conservatively (≥0.75 word overlap) and test against all 7 models' current outputs to confirm zero false positives before deploying.

---

### 4. Fix `partial_recovery` threshold mismatch in `runner.py`
- **Type**: code fix
- **Evidence**: Code review B1. `runner.py:131` (logger.warning fires at `actual_calls < 3`) vs. `runner.py:578` (event emitted at `calls_succeeded < 2`). The comment at line 128–130 explicitly states "A 2-call success is normal for models that produce 8+ levers per call." This means the log warning is a false alarm for 2-call successes, while monitoring dashboards reading `events.jsonl` will miss these.
- **Impact**: Monitoring correctness: false-alarm log warnings for normal 2-call completions and missed events for genuinely partial recoveries. Low functional impact (does not affect LLM output quality), but correct threshold alignment makes the analysis pipeline more reliable and prevents future misdiagnoses.
- **Effort**: Low — one-line change: lower the log threshold from `< 3` to `< 2` to match the event threshold and the comment's own description of normal behavior.
- **Risk**: Minimal. The fix makes the log warning and event emission consistent. Monitored against the comment's explicit intent.

---

### 5. Remove the hardcoded `"See system prompt section 4"` cross-reference from the `review_lever` field description
- **Type**: code fix (prompt/schema)
- **Evidence**: Code review I5. `identify_potential_levers.py:129`: `"See system prompt section 4 for examples."`. This encodes a section number that will silently become wrong if the system prompt is restructured. It also partially re-introduces a directive into the field description — the opposite direction from PR #482's minimalization effort.
- **Impact**: Low — removes a fragile coupling between the Pydantic schema and the system prompt's section numbering. Prevents future silent misreference if the system prompt's section order changes. Makes the schema self-sufficient.
- **Effort**: Very low — replace `"See system prompt section 4 for examples. "` with `"See system prompt for examples. "` or remove the cross-reference entirely.
- **Risk**: Negligible. Models that honor the cross-reference will still find the examples at whatever section they appear. Models that don't honor it are unaffected.

---

## Recommendation

**Implement Direction 1: add an anti-parroting sentence to the subsequent-call user prompt.**

**Why first:** The root cause is confirmed (S1 + insight Negative #1), the fix is a single targeted change that touches only calls 2+ and does not affect call 1, other models, or the field description. The risk of introducing a new template is mitigated by using a prohibition framing. Directions 2–5 either require investigation before implementation (Direction 2), threshold tuning (Direction 3), or are monitoring/hygiene fixes rather than quality improvements (Directions 4–5).

**Specific change — `identify_potential_levers.py:300–305`:**

Current code:
```python
names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```

Proposed change:
```python
names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"Each review_lever must be a genuine critical assessment — "
    f"not a restatement of the consequence — in one sentence (20–40 words).\n\n"
    f"{user_prompt}"
)
```

**Why this wording:** It is a prohibition (`"not a restatement of the consequence"`), not a structural cue. It does not provide a sentence template to copy. The length requirement (`"20–40 words"`) matches the field description and Section 6, ensuring consistency.

**After implementing:** Run a self_improve iteration with llama3.1 only to confirm parroting is eliminated in levers 8–15. If confirmed, run the full 7-model set to verify no regressions in other models.

---

## Deferred Items

- **Direction 2 (haiku fabricated numbers):** Investigate whether removing the PR #479 "positive framing" instruction reduces haiku fabricated numbers from 30.9% toward 22.6%. If positive framing is confirmed as the cause, remove or neutralize it. If it is not (i.e., haiku's inherent tendency regardless of positive framing), add the fabricated-number validator from I6 as a structural guard. Defer until Direction 1 is complete and a clean baseline exists.

- **Direction 3 (consequence-parroting validator):** Implement after Direction 1 is deployed. If Direction 1 eliminates parroting in llama3.1, the validator serves as a safety net. If parroting persists in edge cases, the validator provides structural enforcement. The threshold (≥0.75 word overlap) should be calibrated against all 7 models' run 39–45 outputs first.

- **Direction 4 (partial_recovery threshold):** Fix in the same PR as Direction 1 — it is a trivial one-liner at `runner.py:131` and does not touch prompt logic.

- **Direction 5 (section-4 cross-reference):** Fix in the same PR as Direction 1 — trivial edit at `identify_potential_levers.py:129`.

- **B2 (global dispatcher contamination under parallel execution):** Real correctness bug for `workers > 1` runs. The fix (thread-ID filter on `TrackActivity`, mirroring the existing `_ThreadFilter` pattern) is medium effort. Defer until parallel execution is exercised in the self_improve harness.

- **B3 (timed-out thread continues writing output):** The behavior is confirmed and expected given Python `ThreadPoolExecutor`'s lack of cancellation. The inconsistency (error in events, valid output on disk) is a monitoring gap, not a data-loss risk. Defer; document the behavior in a comment at `runner.py:558` so future readers understand why events and filesystem state can diverge.

- **S2 (strategic_rationale silently skippable):** `Optional[str]` with `default=None` means models can omit the chain-of-thought field without warning. Consider adding a `model_validator` on `DocumentDetails` that logs a warning when `strategic_rationale is None`. Low priority — no evidence this is causing quality regressions in current runs.

- **S4 (options accepts > 3 items silently):** The field description says "Exactly 3 options… No more, no fewer" but `check_option_count` only enforces a lower bound. A simple `if len(v) > 3: raise ValueError(...)` would enforce the upper bound. Defer; no runs in the current analysis showed > 3 options causing downstream failures.

- **H3 (haiku consequence length 2.18× baseline):** The consequence field already has `"Target length: 2–3 sentences."` Haiku is not honoring it. Consider a more prominent instruction or a character-count validator. Investigate in the same iteration as the haiku fabricated-numbers fix (Direction 2), since both are haiku-specific consequence-field regressions and may share a root cause.

- **OPTIMIZE_INSTRUCTIONS documentation:** Add a "Consequence parroting" entry (alongside "Template-lock migration" and "Field-description template lock") documenting the llama3.1 later-call parroting pattern and its fix. Include in the same PR as Direction 1.
