# Synthesis

## Cross-Agent Agreement

Only one agent produced files for this analysis cycle (Claude, both `insight_claude.md` and
`code_claude.md`). The two files approach the same PR from different angles — behavioral
metrics vs. code mechanics — and their findings are mutually consistent:

- **B1 (consequences length inconsistency)** is independently identified in both files.
  The insight file notices haiku's consequences grew +13% despite the PR's stated output
  reduction goal; the code review identifies the root cause: system prompt line 232 still
  says "2–4 sentences" while the field description (line 118) now says "2–3 sentences."
- **Fabricated numbers increased** for gpt-oss-20b and haiku. Both files flag this as a
  concern correlated with the "Focus on cause-effect relationships" phrasing (S1).
- **Template lock worsened** for llama3.1 (6.1%→8% "primary trade-off introduced" openers).
  Both files identify the field description at line 127 as the source phrase models copy.
- **PR verdict: CONDITIONAL** — the minimum viable goal (recovering gpt-oss-20b from
  PR #471's 0/5 catastrophe) was partially achieved (3/5 completions), but the PR regresses
  on verbosity, fabrication, and consistency.

---

## Cross-Agent Disagreements

No inter-agent disagreements to resolve (single agent). One open question resolved by
source code reading:

**Q: Is haiku's `partial_recovery` event a schema failure or early-stop success?**

Code review says it is likely a false-positive event (B3): `runner.py:577-583` fires the
`partial_recovery` event when `calls_succeeded < 2`, which also triggers for a single call
that generated ≥15 levers (early stop). The adaptive loop at `identify_potential_levers.py:352`
exits via `break` when `len(generated_lever_names) >= 15` — a model generating 15+ levers
in one call sets `calls_succeeded=1` and triggers the event even though the result is complete.
Confirmed: this is a monitoring false positive, not a real failure mode.

**Q: Does LeverCleaned.consequences change affect model behavior?**

No. `identify_potential_levers.py:194` has the comment "Field descriptions here are for
documentation only and have no effect on LLM output." LeverCleaned is never sent to an LLM.
The PR's update to LeverCleaned.consequences is harmless documentation housekeeping.

---

## Top 5 Directions

### 1. Fix consequences length target inconsistency (B1)
- **Type**: prompt change
- **Evidence**: Confirmed bug. Field description line 118 says "Target length: 2–3 sentences";
  system prompt section 2 line 232 says "Target length: 2–4 sentences." The PR updated the
  field description but not the system prompt. The code review directly links this to haiku's
  verbosity regression: haiku likely weights the system prompt over the field description,
  so it never received the stricter constraint the PR intended. Verified in source.
- **Impact**: Fixes contradictory guidance for all 7 models. Most important for haiku (the
  only model currently exceeding 2× baseline consequence length at 2.1×). Without this fix,
  the PR's primary output-reduction goal cannot take effect for haiku.
- **Effort**: Low — single word change in the system prompt (line 232: "2–4" → "2–3").
- **Risk**: Negligible. Makes the two sources consistent; no model behavior changes for
  those already respecting the "2–3" cap.

---

### 2. Strengthen the "no invented numbers" constraint adjacent to the cause-effect directive (S1/I4)
- **Type**: prompt change
- **Evidence**: S1 pattern (correlated, not conclusively causal). After PR #473 replaced
  "Do NOT include…" with "Focus on cause-effect relationships and factual outcomes",
  gpt-oss-20b fabricated numbers jumped 4-5×: 0→4 percentage occurrences, 1→5 dollar
  occurrences in a single plan (hong_kong_game). The current field description places the
  number constraint ("only cite numbers if the project context provides evidence for them",
  line 115) *before* the cause-effect directive (line 116). Models processing left-to-right
  may satisfy the cause-effect requirement by inventing metrics after the constraint is
  already "past." OPTIMIZE_INSTRUCTIONS already warns against fabricated numbers (lines 52-55)
  but does not document the cause-effect amplification mechanism.
- **Impact**: Content quality improvement across all models, especially gpt-oss-20b and haiku.
  Fabricated numbers erode plan credibility for every user of every completed plan — this
  affects 34/35 successful plans, not just the 1-2 that time out.
- **Effort**: Low — reorder sentences in the `consequences` field description and strengthen
  the number constraint wording. Also add a note to OPTIMIZE_INSTRUCTIONS (I5).
- **Risk**: Low. Additive constraint; does not remove the positive framing.

---

### 3. Fix review_lever length inconsistency and break template lock (B2/S2/I2)
- **Type**: prompt change
- **Evidence**: Confirmed bug (B2): field description says "1–2 sentences" (line 127); system
  prompt section 6 says "one sentence (20–40 words)" (line 260). Three conflicting signals
  exist for `review_lever` (S3). Separately, the phrase "the primary trade-off this lever
  introduces" in the field description is the exact opener llama3.1 locks onto (8% of 87
  reviews). OPTIMIZE_INSTRUCTIONS lines 86-92 explicitly warns that structural phrases in
  field descriptions override system-prompt examples.
- **Impact**: Reduces llama3.1 template lock and resolves conflicting guidance. Affects all
  models on review_lever quality. The "one sentence (20–40 words)" target from section 6 is
  the most precise and should become the single canonical target.
- **Effort**: Low — update field description wording and consolidate length guidance.
- **Risk**: Low. llama3.1 may shift to a new lock phrase (per OPTIMIZE_INSTRUCTIONS template-
  lock migration warning), but removing the existing locked phrase is still the right move.

---

### 4. Add a `field_validator` character cap on `consequences` in the Lever class (I1)
- **Type**: code fix
- **Evidence**: haiku produces consequences averaging 584 chars after PR #473, which is 2.1×
  the baseline (279 chars). Text-hint constraints ("Target length: 2–3 sentences") are
  structurally unenforceable — haiku ignores them. A Pydantic validator would force
  regeneration when haiku over-generates, similar to the existing `check_option_count`
  validator that prevents under-generation. Suggested threshold: ~500 chars (generous enough
  to avoid rejecting legitimate 3-sentence outputs while catching haiku's 600-800 char outputs).
- **Impact**: Structural enforcement for haiku verbosity. Unlike prompt changes, a validator
  is model-agnostic and will continue to work if haiku updates change its output distribution.
  Downside: increases haiku retry count, adding latency and cost for haiku users.
- **Effort**: Medium — add `@field_validator('consequences', mode='after')` near line 132,
  after existing `parse_options` validator. Threshold calibration needed.
- **Risk**: Medium. A threshold set too low will cause excessive rejections and retries for
  haiku. A threshold set too high will not catch the verbosity. Suggested starting point:
  500 chars. Must be tested with haiku before merging.

---

### 5. Fix partial_recovery event false positives (B3/B4)
- **Type**: code fix
- **Evidence**: Confirmed bug. `runner.py:579` fires `partial_recovery` when
  `calls_succeeded < 2`, which also triggers for a legitimate single-call early stop
  (model generated ≥15 levers in one call). The warning at line 131 fires at `< 3` while
  the event fires at `< 2` — these thresholds are inconsistent and neither distinguishes
  early stop from true partial failure.
- **Impact**: Improves monitoring signal reliability. Current false-positive events cause
  future analysis to over-count failures for models that legitimately early-stop after one
  call. Haiku's hong_kong_game `partial_recovery` events are likely early-stop successes.
- **Effort**: Medium — add `lever_count: int | None` to `PlanResult`, populate it in
  `_run_levers`, and update event logic to distinguish early stop (lever_count ≥ 15) from
  true partial recovery (lever_count < 15). Also align warning threshold at line 131 to
  match the event threshold.
- **Risk**: Low. Monitoring-only change; no effect on output quality or model behavior.

---

## Recommendation

**Do direction 1 first**: fix the consequences length target inconsistency (B1).

**Why first**: It is the only confirmed root cause of an observed regression (haiku +13%
verbosity despite PR #473's stated goal). The fix is a single token change in one line of
the system prompt. It is zero-risk, takes minutes to implement and verify, and unblocks the
actual measurement of whether the "2–3 sentences" constraint works. Until this inconsistency
is fixed, every subsequent verbosity-reduction experiment for consequences is confounded —
haiku can always fall back to the "2–4" system prompt target and the test results will be
uninterpretable.

**File and line**: `identify_potential_levers.py:232`

Current (system prompt section 2):
```
Consequences: describe the direct effect of pulling this lever, then at least one downstream implication or trade-off. Be concise and grounded — only cite specific numbers if the project context provides evidence for them. Do not fabricate percentages or cost estimates. Target length: 2–4 sentences.
```

Change to:
```
Consequences: describe the direct effect of pulling this lever, then at least one downstream implication or trade-off. Be concise and grounded — only cite specific numbers if the project context provides evidence for them. Do not fabricate percentages or cost estimates. Target length: 2–3 sentences.
```

That is the complete fix — change "2–4" to "2–3" at line 232 of `identify_potential_levers.py`.

After this fix, run a new iteration to measure whether haiku's consequences length drops
toward the 2× baseline threshold. If it does not, escalate to direction 4 (field_validator
cap) as the structural enforcement fallback.

---

## Deferred Items

**Direction 2 (S1/I4 — strengthen number constraint)**: Pursue immediately after direction 1.
The fabricated numbers regression in gpt-oss-20b is a content quality concern. Suggested
field description reorder for `consequences` (lines 113–119):

```python
"What happens when this lever is pulled? Describe the direct effect and "
"at least one downstream implication or trade-off. "
"Focus on cause-effect relationships and factual outcomes; "
"never invent percentages, durations, or monetary figures — "
"only cite numbers the project context supplies directly. "
"Save critical assessments for the review_lever field. "
"Target length: 2–3 sentences."
```

Also add the cause-effect fabrication mechanism to OPTIMIZE_INSTRUCTIONS (I5, after line 55).

**Direction 3 (B2/S2/I2 — review_lever alignment)**: Bundle with direction 2 in the same PR.
Suggested replacement for field description (lines 126–131):

```python
"1 sentence (20–40 words): state what decision-critical insight this lever adds and what "
"risk the three options collectively ignore. "
"Do not use square brackets or placeholder text."
```

This removes "the primary trade-off this lever introduces" (llama3.1's locked opener) and
aligns with the system prompt's "one sentence (20–40 words)" target at line 260.

**Direction 4 (I1 — field_validator cap)**: Pursue only if direction 1 (B1 fix) does not
bring haiku below 2× baseline in the next iteration. Validator threshold ~500 chars.

**Direction 5 (B3/B4 — monitoring fix)**: Low urgency for output quality; schedule when
monitoring accuracy becomes a blocker for analysis. The fix requires adding `lever_count`
to `PlanResult` and aligning the warning/event thresholds.

**gpt-oss-20b remaining timeouts (2/5 plans)**: The two plans that consistently timeout
(silo, parasomnia) may have unusually long user prompts relative to the other 3 plans.
A prompt-length audit comparing these plans' token counts against the 3 that completed
would clarify whether the issue is prompt size or API latency variability. Not addressed
by any of the 5 directions above.
