# Code Review (claude)

## Bugs Found

### B1 — `review_lever` field description still contains "the three options" grammatical anchor
**File:** `identify_potential_levers.py:125–131`

```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): the primary trade-off this lever "
        "introduces and the gap the three options leave unaddressed. "
        "Do not use square brackets or placeholder text."
    )
)
```

The phrase "the three options leave unaddressed" makes "the (three) options" the grammatical subject of the required review sentence. Models that follow field descriptions literally produce reviews starting with "all three options", "none of the options", "the options do not address", etc. This is the primary template-lock root cause documented in analysis/40. PR #478 did not touch this field description.

**Fix:** Replace with a description that avoids naming "the options" as a subject, e.g.:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): name the primary trade-off this lever "
        "forces, then name a real-world constraint or risk that all three "
        "approaches collectively sidestep. Do not use square brackets or "
        "placeholder text."
    )
)
```

---

### B2 — Section 4 system prompt still contains "the three options leave unaddressed"
**File:** `identify_potential_levers.py:244–245`

```
"4. **Validation Protocols**\n"
"   - For `review_lever`:\n"
"     A short critical review — identify the primary trade-off this lever introduces, "
"     then state the specific gap the three options leave unaddressed.\n"
```

Same root cause as B1. The system-prompt narrative reinforces the "three options" subject. Even if B1 is fixed in the Pydantic field description, leaving this phrase in Section 4 will preserve the template lock for models that weight the system prompt heavily.

**Fix:** Mirror the B1 fix:
```
A short critical review — identify the primary trade-off this lever forces,
then name a real-world constraint or risk that all three approaches collectively sidestep.
```

---

### B3 — `options` field description is missing the verbatim-numbers constraint
**File:** `identify_potential_levers.py:121–124`

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option is one sentence — "
                "a concrete strategic approach with an action verb."
)
```

The global Section 5 prohibition ("NO calculated, derived, or estimated figures") exists in the system prompt, and the `consequences` field description explicitly repeats "Use numbers only when the project context provides them directly — do not calculate, derive, or estimate figures." However, the `options` field description omits this constraint entirely. Models that follow field descriptions literally (e.g., haiku) respect the prohibition in `consequences` but ignore it in `options`, generating estimated figures like "2,500+ screens", "300–500 select screens", "70 percent of shooting days" in option text.

**Fix:** Add to the options field description:
```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option is one sentence — "
                "a concrete strategic approach with an action verb. "
                "Use only numbers that appear verbatim in the project context; "
                "do not estimate or derive figures."
)
```

---

### B4 — Partial-recovery threshold is inconsistent between `_run_levers` and `_run_plan_task`
**File:** `runner.py:131` and `runner.py:578–583`

```python
# runner.py:131 (in _run_levers)
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")

# runner.py:578–583 (in _run_plan_task)
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 2):
    _emit_event(events_path, "partial_recovery", ...)
```

The log warning fires when `calls_succeeded < 3`, but the `partial_recovery` event fires only when `calls_succeeded < 2`. A run with `calls_succeeded == 2` triggers the warning log but does NOT emit the event. The insight confirms 2-call successes (haiku/silo, haiku/sovereign_identity) are labeled as `partial_recovery` in the events — but they actually reach the threshold that emits the event only if `calls_succeeded < 2`, so they would NOT emit it. The comment at runner.py:127–130 says "A 2-call success is normal for models that produce 8+ levers per call", which justifies `< 2` for the event, but then the `< 3` warning threshold is over-broad and will log spurious warnings for every normal 2-call completion.

**Fix:** Align the two thresholds. Either:
- Remove the `< 3` warning in `_run_levers` entirely (2-call success is normal and documented), or
- Raise the event threshold to match the warning: `calls_succeeded < 3`.

---

## Suspect Patterns

### S1 — "Generate MORE levers" prompt fires even when no prior names exist
**File:** `identify_potential_levers.py:295–305`

```python
for call_index in range(1, max_calls + 1):
    if call_index == 1:
        prompt_content = user_prompt
    else:
        names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
        prompt_content = (
            f"Generate 5 to 7 MORE levers with completely different names. "
            f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
            f"{user_prompt}"
        )
```

If all prior calls failed (`generated_lever_names` is empty), call 2+ sends "Do NOT reuse any of these already-generated names: []" — an instruction that references an empty list. This is harmless but could confuse weaker models that interpret "[]" as a literal restriction and attempt to avoid generating names containing brackets.

---

### S2 — No post-loop check that `min_levers` was reached
**File:** `identify_potential_levers.py:356–378`

After the loop exits (either by reaching `min_levers` or exhausting `max_calls`), the code immediately processes whatever levers were collected with no warning if the final count is below `min_levers`. If 3 of 5 calls fail and only 8 levers are collected, the result is silently returned with 8 levers. Downstream steps assume ≥15. A log warning here would help diagnose quality regressions.

---

### S3 — `options` validator allows >3 silently while description says "exactly 3"
**File:** `identify_potential_levers.py:121–123` and `145–157`

The field description says "Exactly 3 options for this lever. No more, no fewer." and the system prompt Section 1 says "exactly 3 qualitative strategic choices." But the validator only enforces `len(v) < 3`; values with 4+ options pass silently. The comment documents this as intentional ("Over-generation is tolerable; DeduplicateLeversTask handles extras"), but the mismatch between the description's "no more, no fewer" and the validator's behavior means models that produce 4 options will never be corrected and downstream consumers may receive unexpected option counts.

---

## Improvement Opportunities

### I1 — System prompt Section 6 length limit for `review_lever` only specifies words, not sentences
**File:** `identify_potential_levers.py:260`

```
"- Keep each `review_lever` to one sentence (20–40 words). State the trade-off and the gap concisely.\n"
```

The field description says "One sentence (20–40 words)" and the system prompt echoes it. However the examples in Section 4 (lines 247–249) are all multi-clause sentences of ~40–50 words — above the stated 40-word target. Models calibrate length to examples more reliably than to explicit word counts. The examples should be trimmed to ≤40 words each to avoid haiku producing ~220-char (≈44-word) reviews.

---

### I2 — `LeverCleaned` duplicates field descriptions from `Lever` unnecessarily
**File:** `identify_potential_levers.py:206–218`

`LeverCleaned` (lines 193–222) duplicates the `consequences` and `options` field descriptions verbatim from `Lever`. Since `LeverCleaned` is never sent to an LLM (documented in the class docstring), these descriptions serve only as developer documentation. Duplicating them creates a maintenance hazard: if the LLM-facing descriptions in `Lever` are updated (e.g., B3 fix), the `LeverCleaned` descriptions must be updated in sync or they will diverge and mislead readers. Consider using a brief `# see Lever.consequences` comment instead of duplicating the full text.

---

### I3 — Section 4 examples are all complex compound sentences; risk of pattern mirroring
**File:** `identify_potential_levers.py:247–249`

All three `review_lever` examples follow the pattern: "X does Y, but Z at the worst/critical moment." Models that mirror example structure (especially haiku) will produce reviews ending with consequence-at-worst-moment phrasing even when it doesn't fit the domain. Per OPTIMIZE_INSTRUCTIONS ("No two examples should share a sentence pattern or rhetorical structure"), at least one example should use a structurally different form (e.g., a rhetorical question, a forward-looking conditional, or a contrast not resolved at end-of-sentence).

---

### I4 — OPTIMIZE_INSTRUCTIONS does not document the asymmetric field-description constraint gap
**File:** `identify_potential_levers.py:27–93`

The current `OPTIMIZE_INSTRUCTIONS` block documents "Field-description template lock" (lines 86–92) and "Verbosity amplification" (lines 83–85). It does not document that constraints added to one Pydantic field description must also be added to related fields, otherwise models that follow field descriptions selectively (haiku pattern) will apply the constraint to the documented field but not to others. This recurring asymmetry (verbatim-numbers present in `consequences`, absent in `options`) should be added as a known problem.

---

## Trace to Insight Findings

| Insight observation | Root-cause code location |
|---------------------|--------------------------|
| N1 — "all three options / none of the options" in 70–94% of haiku reviews | **B1** (`review_lever` field description lines 125–131) + **B2** (Section 4 line 245): both use "the three options" as grammatical anchor |
| N2 — Haiku consequences exceed 2–3 sentence target | No code bug; the "Target length: 2–3 sentences" instruction was added to the field description and Section 2, but haiku treats it probabilistically. **I1** (examples too long) and **I3** (all examples share rhetorical structure) amplify the problem |
| N3 — Haiku options contain estimated/derived figures | **B3**: `options` field description is missing the verbatim-numbers constraint that `consequences` carries; global Section 5 prohibition is insufficient for models following field descriptions |
| N4 — Llama3.1 consequences 1 sentence (under-generating) | No code bug; "2–3 sentences" interpreted as upper bound by small models. OPTIMIZE_INSTRUCTIONS should document this model-dependent behavior (**I4**) |
| N5 — Lever semantic duplication in llama3.1 | Expected behavior; downstream `DeduplicateLeversTask` handles it. The multi-call avoidance list (lines 298–300) helps but doesn't prevent semantic (vs. name) duplicates |
| P5 — No LLMChatErrors | Loop error handling (lines 327–346) correctly catches errors and continues with partial results; the `raise llm_error` only fires when zero calls succeeded |
| Partial-recovery event inconsistency | **B4**: Warning logs at `< 3`, event fires at `< 2`; the 2-call successes seen in haiku/silo and haiku/sovereign_identity are in the log-warning zone but not in the event zone |

---

## PR Review

**PR #478: "Allow verbatim plan numbers only, positive framing, and tighter targets"**

### What the PR changed

Based on diffing the current file state against the analysis/40 observations:

1. **`consequences` field description** — Added verbatim-numbers constraint ("Use numbers only when the project context provides them directly") and "Save critical assessments for the review_lever field." and "Target length: 2–3 sentences." (lines 112–119). These are correct additions.

2. **Section 2 system prompt** — Added "Use numbers only when the project context provides them directly" and "Target length: 2–3 sentences" to the Consequences bullet (lines 232–234). Correct.

3. **Replaced prohibition framing** — Removed "Do NOT include 'Controls ... vs.'" and replaced with "Save critical assessments for the review_lever field." in `consequences`. This is the positive-framing improvement claimed by the PR; OPTIMIZE_INSTRUCTIONS explicitly flags prohibition-framing as risky for small models, so this change is correct.

4. **Section 5** — Added "NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context" (line 256). Correct.

5. **Section 6 (new)** — Added length limits for `review_lever` (one sentence, 20–40 words) and options (one sentence with action verb) (lines 259–264). The "options one sentence" guidance partially reduces haiku verbosity but haiku produces long single sentences rather than concise ones.

### What the PR missed

1. **Primary open issue (B1 + B2):** The `review_lever` field description and Section 4 both still contain "the gap the three options leave unaddressed." This is the template-lock root cause from analysis/40 that was explicitly recommended for fixing. The PR made four other improvements but did not apply the top-priority C1+C2 fix from analysis/40.

2. **Asymmetric constraint coverage (B3):** The verbatim-numbers constraint was added to `consequences` (field description and Section 2) and to Section 5 globally, but was not added to the `options` field description. Since haiku demonstrably follows field descriptions more reliably than global system-prompt sections, this gap explains N3 entirely.

3. **No evidence of regression:** The PR introduces no new bugs, does not break existing validators, and does not harm non-haiku models. The improvements (positive framing, verbatim-numbers in consequences, length targets) are valid and produce incremental gains.

### Implementation assessment

The code changes are mechanically correct. String changes in field descriptions and the system prompt are applied consistently (field description + system prompt) for `consequences`, but inconsistently for `options` (system prompt only, no field description update). The Section 6 length limits are a net positive. The positive-framing change for consequences is well-executed. The only implementation gap is the omission of B1+B2+B3.

---

## Summary

The two highest-priority unfixed bugs are **B1** and **B2** (the "three options" grammatical anchor in the `review_lever` field description and Section 4 respectively), which directly cause the 70–94% template lock rate observed in haiku. These were the top recommendation from analysis/40 and were not addressed by PR #478.

**B3** (options field description missing verbatim-numbers constraint) is the direct code-level explanation for N3 (haiku generating estimated figures in options). Fixing it requires adding one sentence to the `options` field description — the same constraint that was correctly added to `consequences` in PR #478.

**B4** (partial-recovery threshold mismatch between `_run_levers` and `_run_plan_task`) is a minor consistency bug that generates spurious warning log entries for every normal 2-call completion.

The remaining findings (S1–S3, I1–I4) are quality and maintainability issues that do not cause data corruption but contribute to model verbosity and make future prompt engineering harder.

**Recommended next PR:** Apply C1 (rewrite `review_lever` field description, line 125–131), C2 (rewrite Section 4 instruction, line 245), and C3 (add verbatim-numbers note to `options` field description, line 121–124). These three targeted changes address the two highest-impact open issues from this analysis.
