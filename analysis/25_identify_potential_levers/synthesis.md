# Synthesis

## Cross-Agent Agreement

Both insight_claude and code_claude agree on all major points — there are no conflicting interpretations, which strengthens confidence in each finding.

**Agreed verdicts:**
- PR #334 is a **KEEP**. Summary field removal is fully confirmed (grep: 0 `"summary"` keys in runs 82–88 vs 2–3 per plan in runs 75–81). 105 wasted LLM generations per 7-model batch eliminated. No content regressions.
- **B1/C1**: The hard `options == 3` Pydantic validator (`identify_potential_levers.py:131`) causes full-call failure when a single lever returns 2 options. This is disproportionate — it discards all 5–7 valid levers from the call. Confirmed by run 82 (llama3.1 gta_game: levers 5 and 6 failed, entire call discarded).
- **B2/I1**: The phrase "This lever governs the tension between centralization and local autonomy…" is the lead example in **both** the `Lever.review_lever` Pydantic field description (line 101) and system-prompt section 4 (line 225). Two identical anchors directly cause the 100% template-lock observed in llama3.1 (run 82) and the related "Core tension:" opener in qwen3 (runs 78, 85). OPTIMIZE_INSTRUCTIONS documents "single-example template lock" but the prescribed fix (negative constraint) has never been applied.
- **I2/N2**: "at least 15 words with an action verb" exists in system-prompt section 6 (after PR) but not in the Pydantic `options` field description. Structured-output models weight schema descriptions differently; adding it to the field description would provide a second, schema-level enforcement signal.
- **I3**: OPTIMIZE_INSTRUCTIONS (lines 27–73) documents five known failure modes but is missing "model-native template openers" — a pattern confirmed across analyses 22, 24, and 25.

---

## Cross-Agent Disagreements

None. Both files analyzed the same source (identify_potential_levers.py) and reached identical conclusions. There are no disputed claims to adjudicate.

---

## Top 5 Directions

### 1. Fix review template lock — add negative opener constraints
- **Type**: code fix (Pydantic field description) + prompt change (system-prompt section 4)
- **Evidence**: B2 (code_claude), I1 (code_claude), N3 (insight_claude), "Reflect" (insight_claude). Confirmed across analyses 22, 24, and 25. llama3.1 opens 100% of reviews with "This lever governs the tension between" (run 82); qwen3 uses "Core tension:" (runs 78, 85). OPTIMIZE_INSTRUCTIONS already names the root cause (single-example template lock, lines 69–72) but the prescribed fix is absent from the code.
- **Impact**: Affects every plan processed by llama3.1 and qwen3 — 2 of 7 tested models, ~30% of model-run pairs. Review diversity directly affects the quality of the downstream `review` field propagated through DeduplicateLevers → EnrichLevers → FocusOnVitalFewLevers. Homogeneous reviews bias the entire solution space.
- **Effort**: Low — two `Do NOT open with` sentences added to `Lever.review_lever` field description (line 96–107) and a matching negative constraint in section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 224–227).
- **Risk**: Minimal. Negative constraints redirect, not restrict. Weaker models may still use formulaic openers but with different phrases; the variety improves even if perfection isn't reached. No downstream schema changes required.

### 2. Relax `options == 3` hard validator to `min_length=3`
- **Type**: code fix
- **Evidence**: B1 (code_claude), C1 (insight_claude), N1 (insight_claude). Run 82: levers 5 and 6 had 2 options each — entire call discarded, plan failed. Run 88 (haiku, gta_game) partial recovery (`calls_succeeded=2`) traced to the same mechanism. The validator comment at line 127 cites "Run 89 silently passed" as motivation, but the downstream risk of a 4-option lever reaching DeduplicateLevers is far lower than losing 6 valid levers.
- **Impact**: Reduces llama3.1 full-plan failure rate. Currently llama3.1 fails ~1/5 plans per run batch (run 82 gta_game, run 75 hong_kong_game). Relaxing to `min_length=3` means a lever with 2 options would still be rejected at the lever level, but the other 4–6 valid levers from that call would be kept. Change affects `identify_potential_levers.py:131` — one line.
- **Effort**: Trivial — change `len(v) != 3` to `len(v) < 3`.
- **Risk**: A lever with 4 or 5 options reaching downstream steps. DeduplicateLevers and EnrichLevers iterate over options; nothing downstream hard-codes an index of `options[2]`. The schema description says "Exactly 3" which will suppress 4-option generation naturally. Accepting 4 options silently is a minor downstream inconsistency, but far less damaging than full plan failure.

### 3. Add "at least 15 words" to Pydantic `options` field description
- **Type**: code fix (Pydantic field description)
- **Evidence**: I2 (code_claude), N2 (insight_claude). llama3.1 averages ~12 words/option after the PR added the constraint to section 6 (up from ~7). Schema field descriptions are weighted separately from system-prompt text for structured-output calls; adding the constraint at schema level provides a second enforcement signal for small models.
- **Impact**: Would push llama3.1 options closer to the 15-word floor. Strong models (haiku: 25–60 words, gpt-5-nano, gpt-4o-mini) already satisfy this and would be unaffected. The change narrows the quality gap between model tiers for the `options` field specifically.
- **Effort**: Low — append "at least 15 words with an action verb" to the `options` field description at line 92–95.
- **Risk**: Small — if a model now generates 15-word options that are still vague, the word-count metric improves but content quality doesn't. The OPTIMIZE_INSTRUCTIONS prohibition on "vague aspirations posing as options" (line 60) is the complementary guard.

### 4. Update OPTIMIZE_INSTRUCTIONS to document "model-native template openers"
- **Type**: code change (documentation constant, no runtime effect)
- **Evidence**: I3 (code_claude), "OPTIMIZE_INSTRUCTIONS Alignment" (insight_claude). The constant is read by future optimization agents to understand known failure classes. The pattern is confirmed across three analyses (22, 24, 25) but is absent from the documented list. Without this entry, future agents will keep rediscovering it.
- **Impact**: Does not change any model output directly. Improves the optimization loop's institutional memory — future synthesis and insight agents will have the failure class documented and can close it systematically rather than noting it again.
- **Effort**: Trivial — add one bullet to OPTIMIZE_INSTRUCTIONS.
- **Risk**: None.

### 5. Add soft option-length validator (warn, don't reject)
- **Type**: code change (soft validator / logging)
- **Evidence**: C3 (insight_claude). Currently there is no runtime signal when options fall below the 15-word floor. A warning logged to events.jsonl would make sub-15-word options visible in analysis without triggering the partial-recovery path.
- **Impact**: Provides observability for direction 3's effectiveness. After adding the Pydantic field description constraint (#3), a soft validator would confirm whether llama3.1 crosses the 15-word floor or just approaches it. Indirectly improves experiment iteration speed.
- **Effort**: Low — add a post-validation `logger.warning` in `check_option_count` or a separate `field_validator` that calls `logger.warning` without raising.
- **Risk**: Minimal — logging-only change. One edge case: very high warning volume (e.g., all llama3.1 options below floor) could inflate events.jsonl, but this is informational and harmless.

---

## Recommendation

**Pursue direction 1 first: add negative opener constraints to `review_lever`.**

**Why first**: This is the only confirmed content-quality regression that affects every plan produced by two models. Template lock in the `review` field is not a single-run edge case — it is a systematic, 100%-reproduction pattern for llama3.1 and a recurring pattern for qwen3. Reviews that all open identically ("This lever governs the tension between centralization and local autonomy…") provide no discriminating information to the downstream FocusOnVitalFewLevers step, which uses review content to assess lever quality.

Direction 2 (relax `options == 3`) reduces the failure rate but only for plans where llama3.1 produces a 2-option lever, which is a subset of llama3.1 runs. Direction 1 degrades output quality for 100% of llama3.1 runs and ~100% of qwen3 runs — a much larger blast radius.

**Specific change — two files, four locations:**

**File 1**: `identify_potential_levers.py`, `Lever.review_lever` field description (lines 96–107).

Replace:
```python
review_lever: str = Field(
    description=(
        "A short critical review of this lever — name the core tension, "
        "then identify a weakness the options miss. "
        "Examples: "
        "'This lever governs the tension between centralization and local "
        "autonomy, but the options overlook transition costs.' "
        "'Prioritizing speed over reliability carries hidden costs: none of "
        "the options address rollback complexity.' "
        "Do not use square brackets or placeholder text."
    )
)
```

With:
```python
review_lever: str = Field(
    description=(
        "A short critical review of this lever — name the core tension, "
        "then identify a weakness the options miss. "
        "Do NOT open with 'This lever governs the tension between'. "
        "Do NOT open with 'Core tension:'. "
        "Name the specific tension in your own words. "
        "Examples: "
        "'Maximizing early revenue through aggressive licensing forces the team to "
        "lock in partners before the technology is stable, creating renegotiation risk.' "
        "'Centralizing data collection accelerates pattern detection but concentrates "
        "liability exposure that the options do not address.' "
        "Do not use square brackets or placeholder text."
    )
)
```

**File 1 continued**: `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`, section 4 (lines 224–227).

Replace the two examples that include "This lever governs the tension between centralization and local autonomy" and "Prioritizing speed over reliability" with the two new examples above, and prepend the negative constraints:
```
- Do NOT open with "This lever governs the tension between". Name the specific tension directly.
- Do NOT open with "Core tension:". Express the tension in your own words.
```

**File 1 continued**: `OPTIMIZE_INSTRUCTIONS` (lines 27–73). Append:
```
- Model-native template openers. Small or MoE models prepend reviews with
  fixed phrases absent from prompt examples ("This lever governs the tension
  between", "Core tension: X."). These are driven by the model's training
  distribution, not by prompt examples. Only a negative constraint in the
  field description ("Do not open with 'This lever governs the tension
  between'") breaks the pattern. Structural validators alone will not catch
  this (confirmed across analyses 22, 24, 25).
```

**Why the new examples matter**: The existing examples (`centralization and local autonomy`, `speed over reliability`) are extremely generic — a model that memorizes them can apply them to any plan without understanding. The replacement examples are domain-specific enough that they cannot be lifted verbatim, forcing the model to generate a novel tension statement for each lever. This is the structural fix OPTIMIZE_INSTRUCTIONS has been pointing at since it documented the single-example template lock problem.

---

## Deferred Items

**Direction 2** (relax `options == 3` to `min_length=3`, `identify_potential_levers.py:131`): Worth doing in the same PR as direction 1 since it is a one-line change with well-understood scope. If separated, do it second.

**Direction 3** (add "at least 15 words" to Pydantic `options` field description, lines 92–95): Low effort, low risk. Addresses the partial compliance gap for llama3.1 (12 words vs 15-word floor). Queue after directions 1–2.

**Direction 5** (soft option-length validator): Defer until direction 3 is implemented and a new run batch confirms whether llama3.1 crosses the floor. Adds observability value only once the signal is ambiguous.

**Q2** (haiku review verbosity): Haiku reviews average ~430 chars (~3.9× baseline). Content reads as substantive, not padded. Monitor for one more run batch before intervening. If the trend continues above 4× baseline, add a soft target length to the `review_lever` field description ("Target length: 2–4 sentences, around 100–150 words").

**Q4** (qwen3 JSON extraction failure in run 78 — did not recur in run 85): One recurrence-free run is insufficient to declare it resolved. Run qwen3 on parasomnia one more time to confirm. Hypothesis: the summary field removal freed enough context headroom to prevent truncation.

**S1** (closure capture in loop, `identify_potential_levers.py:291`): The `messages_snapshot` closure is safe as long as `llm_executor.run()` is synchronous. Freeze the value with a default argument (`def execute_function(llm, msgs=messages_snapshot)`) when/if the executor is made async. Latent risk only, not a current bug.

**S2** (global dispatcher event handler cross-contamination in `runner.py`): Real issue under `workers > 1` but the affected file (`track_activity.jsonl`) is deleted at run end, so it doesn't corrupt final outputs. Address when multi-worker plans are exposed to users.

**I4** (`LeverCleaned.review` field description duplication): Dead code — `LeverCleaned` is never passed to an LLM. Remove or simplify the examples. Low priority; no runtime impact.
