# Synthesis

## Cross-Agent Agreement

Only one insight agent (insight_claude) and one code review agent (code_claude) contributed.
Both converge on the same core conclusions:

- **PR #466 verdict: KEEP.** The XML-tag wrapping of per-batch UUIDs (`<lever>{uuid}</lever>`)
  fully eliminated llama3.1 UUID contamination in `synergy_text` and `conflict_text`
  (15 → 0 occurrences, –100%). No regressions observed across any of the 7 tested models.
- **haiku's `unknown_lever_id` errors are noise, not correctness failures.** All 35/35 real
  levers are enriched correctly; the 5 remaining errors are discarded extra characterizations
  with fabricated UUIDs. Both agents flag `errors.append` for `unknown_lever_id` as polluting
  the failure signal (B2/I1 in code review; N1/C1 in insight).
- **Two residual issues warrant follow-up:** (1) haiku extra-characterization noise (5 errors in
  2 plans), and (2) a negative prohibition in the `Lever.consequences` field description in
  `identify_potential_levers.py` that violates OPTIMIZE_INSTRUCTIONS guidance (B1).

## Cross-Agent Disagreements

No substantive disagreements. Both agents read the same source and agree on all major
findings. Minor framing differences:

- Insight labels the duplicate exact-count instructions (Q3) as a question; code review
  promotes it to S2/I3. Both agree it warrants investigation. Code review is correct that
  the system-level abstract instruction ("one per lever") is strictly weaker than the
  user-level concrete instruction ("exactly N") for function-calling models — removing the
  abstract version reduces the signal-to-noise ratio without risking the concrete one.

- Code review flags S1 (missing defensive snapshot in `enrich_potential_levers.py`
  `execute_function` closure) as a latent risk. Insight does not mention it. S1 is a real
  inconsistency with `identify_potential_levers.py` (confirmed by source code reading), but
  the current synchronous `llm_executor.run()` call means no live race condition exists.

## Top 5 Directions

### 1. Fix negative prohibition in `Lever.consequences` field description
- **Type**: prompt change (Pydantic field description sent to LLM)
- **Evidence**: B1 (code_claude), I4 (code_claude). Confirmed by reading
  `identify_potential_levers.py:116–117`. The field description currently contains:
  `"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"`.
  OPTIMIZE_INSTRUCTIONS lines 80–82 explicitly prohibit this pattern: "Do NOT add explicit
  prohibitions naming banned phrases — small models treat the prohibition text as a template
  and copy the banned phrases." The prohibited phrases also include English-specific keywords
  (`Controls`, `Weakness:`, `vs.`) that break non-English outputs (OPTIMIZE_INSTRUCTIONS
  lines 62–68).
- **Impact**: All plans processed with weak or non-English models. If small models are copying
  "Controls … vs." or "Weakness:" into `consequences`, that text propagates to the enrich step
  (where `consequences` is included verbatim in the batch prompt), corrupting
  `description`/`synergy_text`/`conflict_text` for those levers. Fixing this improves content
  quality for all affected plans; the upside is multi-step, not just single-step.
- **Effort**: Low — two lines deleted, one sentence added.
- **Risk**: Low. Positive framing is always safer than negative prohibition for weak models.
  Requires one self_improve iteration to confirm (this is a prompt change to the identify
  step, so it affects runs tagged against `identify_potential_levers`, not `enrich`).

---

### 2. Suppress `errors.append` for `unknown_lever_id` (B2 / I1)
- **Type**: code fix
- **Evidence**: B2 and I1 (code_claude), N1 and C1 (insight_claude). Confirmed in
  `enrich_potential_levers.py:282–283`. The current code appends every haiku extra
  characterization to `errors`, conflating expected model noise with real batch failures.
  Real failures (`batch_skipped`, `incomplete`, `validation_error`) deserve error-list entries;
  fabricated-UUID extras do not.
- **Impact**: haiku `errors` array drops from 5 entries to 0 across all runs. Downstream
  consumers (e.g., run result parsers) get a clean failure signal. No effect on correctness —
  real levers are always enriched.
- **Effort**: Minimal — remove one line (`errors.append(...)`), keep the `logger.warning`.
  Add a one-line comment explaining the intent.
- **Risk**: None. The suppressed entries represent expected, already-discarded over-generation.

---

### 3. Add no-max_length rationale comment to `BatchCharacterizationResult.characterizations` (S3 / I2)
- **Type**: code documentation
- **Evidence**: S3 and I2 (code_claude). Confirmed by reading
  `enrich_potential_levers.py:149–153` (no comment) versus `identify_potential_levers.py:188–189`
  (has explicit comment). Absence of comment creates a maintenance trap: a future developer
  seeing `unknown_lever_id` errors in `errors` might add `max_length=batch_size` to the field,
  which would cause Pydantic to reject the entire batch response rather than accepting it
  partially, converting benign noise into a hard failure.
- **Impact**: Prevents a future regression. No effect on current runs.
- **Effort**: Minimal — add a 4-line comment block.
- **Risk**: None.

---

### 4. Remove system-level abstract count instruction; keep only user-level concrete count (S2 / I3)
- **Type**: prompt change
- **Evidence**: S2 and I3 (code_claude), Q3 (insight_claude). Confirmed in
  `enrich_potential_levers.py:177` (system prompt: "Return exactly one characterization per
  lever requested — no more, no fewer") and line 254 (user prompt: "Return exactly
  {len(batch)} characterizations — one per lever, no more, no fewer"). The abstract system
  instruction duplicates the concrete user instruction. For haiku's function-calling interface,
  the concrete number in the user prompt is more actionable.
- **Impact**: May reduce haiku's remaining 5 `unknown_lever_id` errors. The gta_game plan
  (previously 5 errors) was resolved by the PR; the residual errors are in parasomnia
  (4) and silo (1). Removing the abstract instruction may reduce ambiguity for haiku.
- **Effort**: Low — remove one sentence from the system prompt.
- **Risk**: Medium — unknown effect on haiku. Could worsen behavior if haiku relies on the
  system-level constraint as a hard cap. Requires one experiment iteration to confirm.
  Do not combine with other changes in the same iteration.

---

### 5. Add defensive snapshot in `execute_function` closure (S1)
- **Type**: code fix
- **Evidence**: S1 (code_claude). Confirmed by comparing `enrich_potential_levers.py:259–266`
  (no snapshot) with `identify_potential_levers.py:317–322` (uses `messages_snapshot = list(...)`).
  Currently safe because `llm_executor.run()` is synchronous. Would become a bug if the
  executor is ever made async.
- **Impact**: Prevents a latent race-condition bug. No effect on current runs.
- **Effort**: Minimal — add `messages_snapshot = list(chat_message_list)` and update the
  closure to reference it.
- **Risk**: None for the defensive copy itself; the risk is only in not making it.

---

## Recommendation

**Pursue Direction 2 first: suppress `errors.append` for `unknown_lever_id`.**

**Rationale:** Direction 2 is a single-line code deletion with zero risk, zero ambiguity, and
immediate observable benefit across all haiku runs. It does not require an experiment iteration —
the fix is structurally identical to a documented principle (real failures vs. expected model
noise) and the evidence is confirmed (all 35 real levers are correctly enriched; the suppressed
entries are fabricated-UUID extras that are already discarded). Doing this first also makes
Direction 4 easier to evaluate: once the `errors` list is clean, a drop from 5 to 0 in a
subsequent experiment is an unambiguous win.

Direction 1 (B1) has higher long-term impact but touches the `identify_potential_levers.py`
step and requires a full self_improve iteration to validate. It should be the first prompt-change
experiment after the code fix is merged.

**Exact change — `enrich_potential_levers.py:281–283`:**

```python
# Current:
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})

# Proposed:
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    # Not appended to errors — extra characterizations from over-generating models
    # (e.g. haiku) are expected and discarded. Real levers are always enriched correctly.
```

Pair with Direction 3 (add the no-max_length rationale comment to `BatchCharacterizationResult`)
in the same commit — both are documentation/cleanup changes in the same file with no behavioral
risk.

---

## Deferred Items

- **Direction 1 (B1)** — Fix `Lever.consequences` negative prohibition in
  `identify_potential_levers.py:116–117`. High impact but requires a dedicated `identify_potential_levers`
  experiment iteration. Proposed replacement wording:
  ```
  "Focus on cause-effect relationships and factual outcomes within the project domain; "
  "save critical assessments and gap analysis for the review_lever field. "
  ```
  (Replace lines 116–117; retain lines 113–115 and 118.)

- **Direction 4 (S2/I3)** — Remove system-level abstract count instruction. Should be
  a standalone experiment iteration after Direction 2/3 is merged, so the `errors`
  signal is clean and the haiku error delta is measurable.

- **Direction 5 (S1)** — Defensive snapshot in `execute_function`. Batch with Direction 2/3
  or any other no-risk code-only cleanup.

- **Haiku batch-size hypothesis (Q4, insight)** — Check whether haiku's extra characterizations
  are batch-size-dependent (errors appear in shorter second batches). If confirmed, a haiku-specific
  batch-size override (e.g., `BATCH_SIZE_HAIKU = 3`) could eliminate the issue structurally
  rather than suppressing its symptom in `errors`. Warrants investigation before the
  Direction 4 experiment.

- **N3 (fabricated percentages from identify step)** — Pre-existing issue; consequences text
  with fabricated numbers propagates into enrich descriptions. Direction 1 (B1) partially
  addresses this by removing the English-specific prohibition that may trigger fabrication in
  small models. Full fix requires a validator or OPTIMIZE_INSTRUCTIONS update in the identify
  step.
