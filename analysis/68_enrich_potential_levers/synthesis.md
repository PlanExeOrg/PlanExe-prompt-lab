# Synthesis

## Cross-Agent Agreement

Only one insight agent and one code review agent were used for this analysis, so cross-agent
disagreement is not a significant concern. The two agents are consistent on all key findings:

- **PR #469 is a net improvement** — 100% success rate (up from 94.3%), field lengths normalised,
  haiku errors reduced. Verdict: CONDITIONAL.
- **B1 (`errors.append` for `unknown_lever_id`) is a real bug** that was flagged in analysis 65
  and is still present in the current codebase. Both agents independently identify this as the
  highest-priority fix.
- **The `"dummy_override"` failure mode (N1) is likely caused by the ambiguous "from the prompt"
  wording in the `lever_id` field description (S1/S2)**, not by the system-prompt change alone.
- **The anti-echoing instruction works qualitatively** (haiku parasomnia improvement is concrete),
  but there is no structural enforcement.
- **gpt-oss-20b timeout fix (P1)** is the most structurally important benefit of the PR — two
  fewer plan timeouts directly translates to lower cost and higher reliability.

---

## Cross-Agent Disagreements

None. Both agents agree on root causes, priorities, and the CONDITIONAL verdict. The only open
question is whether `"dummy_override"` is reproducible or a one-off stochastic event (Q1 in the
insight file). This was not disputed — it was flagged as unknown.

---

## Top 5 Directions

### 1. Remove `errors.append` for `unknown_lever_id` (B1)

- **Type**: code fix
- **Evidence**: Both agents flagged this independently. Confirmed present at
  `enrich_potential_levers.py:285`. Was recommended in analysis 65 (B2) and not addressed in
  PR #469. The insight agent's haiku error count (5 → 2) is measuring noise, not real failures —
  both before and after counts are entirely composed of over-generation entries that are correctly
  discarded. The `errors` list is consumed by the analysis pipeline and treated as a quality signal.
- **Impact**: Affects all models and all future runs. Haiku's real error rate becomes 0/35 (not
  2/35). Cleans the analysis pipeline signal immediately with a single line of code removed. No
  runtime behaviour changes — the `logger.warning` on line 284 is sufficient for debugging.
- **Effort**: Low — remove one line (`errors.append({"type": "unknown_lever_id", ...})`).
- **Risk**: Minimal. Over-generation noise stops being reported as errors; real failures
  (`batch_retry`, `batch_skipped`, `validation_error`, `incomplete`) are unaffected.

---

### 2. Add placeholder guard to `lever_id` field description and system prompt (S1/S2, I2)

- **Type**: prompt change
- **Evidence**: Confirmed at `enrich_potential_levers.py:138` — the field description says
  `"copy it verbatim from the prompt, without XML tags"`. The phrase "from the prompt" is
  imprecise; "the prompt" contains `<lever>uuid</lever>` as text, so a model could read this as
  "copy the whole tag string." The system prompt is more precise ("from inside the tags"), but the
  field description primes the model first in structured-output mode. The `"dummy_override"` entry
  in haiku run 89 is consistent with haiku interpreting the verbatim instruction as permission to
  invent a placeholder when uncertain. No negative constraint exists ("do not substitute
  placeholder text").
- **Impact**: Prevents the new failure mode without regressing the hyphen-stripping fix from #468.
  Affects primarily small/weak models (haiku, llama3.1) that are most likely to misread ambiguous
  field descriptions. The field description and system prompt should also be made identical in
  wording to eliminate maintenance divergence (currently two slightly different phrasings).
- **Effort**: Low — two targeted wording changes (field description + system prompt addition).
- **Risk**: Low. Adding a narrow negative guard ("do not substitute placeholder strings such as
  'dummy', 'test', 'override'") is specific enough to not regress other behaviour. Per
  OPTIMIZE_INSTRUCTIONS, prohibitions naming the banned phrases can be copied by small models —
  keep the guard narrow and domain-specific, not a general UUID explanation.

---

### 3. Recalibrate `partial_recovery` event threshold in `runner.py` (B2)

- **Type**: code fix
- **Evidence**: Confirmed at `runner.py:131` and `runner.py:577–579`. The threshold `< 3` fires
  for every clean 2-call run. The comment on lines 127–130 explicitly acknowledges "A 2-call
  success is normal for models that produce 8+ levers per call." `calls_succeeded` counts
  successful responses, not failures — a model that generates 8 levers per call completes in 2
  clean calls, triggering a spurious `partial_recovery` event. This affects the
  `identify_potential_levers` step only (not `enrich_potential_levers`).
- **Impact**: Removes false `partial_recovery` events from the analysis pipeline. Makes the event
  meaningful again — it should only fire when a call actually failed and recovery happened. Affects
  all models that naturally complete in 2 calls (most models with generous output counts).
- **Effort**: Low to medium. Simplest fix: lower threshold to `< 2`. Better fix: track actual
  call failures in the adaptive loop and only emit `partial_recovery` when `calls_failed > 0`.
  The second option requires adding a `calls_failed` field to `PlanResult`.
- **Risk**: Low. The event is consumed by analysis scripts only; no runtime behaviour changes.

---

### 4. Document the semantic-placeholder pattern in `enrich_potential_levers.py` `OPTIMIZE_INSTRUCTIONS` (I3)

- **Type**: prompt change (documentation)
- **Evidence**: The current `OPTIMIZE_INSTRUCTIONS` at lines 28–107 documents UUID leakage,
  XML-tag wrapping (PR #466), and verbosity problems — but does not mention the
  `"dummy_override"` failure mode: a model generating a semantic placeholder string in the
  `lever_id` field instead of a UUID-format fabrication. This is a new failure pattern introduced
  by the verbatim guidance in PR #469.
- **Impact**: Future prompt engineers will know this failure mode has been observed and what caused
  it (verbatim guidance interpreted as permission to invent). Prevents recurrence when the
  `lever_id` guidance is revised again. Aligns with the OPTIMIZE_INSTRUCTIONS goal of cataloguing
  known pitfalls.
- **Effort**: Low — add one bullet to the `Known problems to guard against` section.
- **Risk**: None. Documentation only; no runtime impact.

---

### 5. Relax or clarify the word count floor for naturally concise models (N2, N3)

- **Type**: prompt change
- **Evidence**: After PR #469, three models (llama3.1: 46.5 words, gemini: 47.8 words, qwen3-30b:
  39.7 words description; qwen3-30b synergy: 18.1 words) fall below the stated 50-word and
  20-word floors. The word-count constraint is prompt-level guidance only (no schema validator
  enforces it — confirmed by zero `LLMChatError` events). These models were already at the low
  end before PR #469; the additional tightening pushed them below the floor. No real failures
  result — all levers are correctly enriched — but the targets are now aspirational for these
  models, not actual guidance.
- **Impact**: Affects 3 of 7 models for description length, 1 for synergy. Since the floor is not
  enforced, the impact is cosmetic: the stated target is inaccurate for concise models. Adjusting
  the floor (e.g. "40–70 words") or making it a soft cap ("aim for 50–70 words, but prioritise
  precision over length") would bring the guidance in line with observed behaviour.
- **Effort**: Low — single wording change in field descriptions and system prompt.
- **Risk**: Low. Widening or softening the floor might slightly increase output length for verbose
  models — test in the next iteration. The primary concern is that relaxing it too far would undo
  the verbosity reduction achieved by PR #469.

---

## Recommendation

**Fix B1 first: remove `errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})` at
`enrich_potential_levers.py:285`.**

**Why first**: It is a single-line code change with immediate, permanent impact on analysis signal
quality across all models and all future runs. The insight file's headline metric — "haiku errors
reduced from 5 to 2" — is measuring noise. Removing this line will reveal haiku's true error rate
(0 for most plans) and make the analysis pipeline's error counts trustworthy again. This fix was
recommended in analysis 65 and has waited two PRs (#467, #468, #469) without being addressed.
Every additional iteration that runs without this fix produces misleading comparison tables.

**Specific change** (`enrich_potential_levers.py`, around line 283–285):

```python
# BEFORE
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})

# AFTER
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    # Do not append to errors — over-generation of characterizations is
    # expected noise, not a real failure. The real levers are all enriched
    # correctly; this entry is discarded. The warning log is sufficient.
```

No other file changes are needed for this fix.

---

## Deferred Items

- **S1/S2 + I2 (placeholder guard)** — Second priority. Add "do not substitute placeholder text
  such as 'dummy', 'test', 'override'" to the `lever_id` system-prompt guidance. Narrow and safe.
  Investigate whether `"dummy_override"` in haiku run 89 gta_game is reproducible before drafting
  the exact wording (Q1 in the insight file).

- **B2 (partial_recovery threshold)** — Third priority. Change `runner.py` to only emit
  `partial_recovery` when a call actually failed. Simplest path: lower threshold from `< 3` to
  `< 2`; better path: track `calls_failed` explicitly.

- **I3 (OPTIMIZE_INSTRUCTIONS)** — Can be bundled with the placeholder guard change. Add a bullet
  documenting the semantic-placeholder failure mode to `enrich_potential_levers.py`
  `OPTIMIZE_INSTRUCTIONS`.

- **N2/N3 (word count floor)** — Low urgency. Since the floor is not enforced by a validator,
  concise models undershooting is benign. Consider a minor wording adjustment ("aim for 50–70
  words") in a future iteration to align guidance with observed behaviour.

- **S3 (missing `messages_snapshot`)** — Not a real bug in current synchronous execution.
  `chat_message_list` is freshly defined in each loop iteration and `execute_function` is called
  immediately — no late-binding capture problem. The inconsistency with `identify_potential_levers.py`
  is cosmetic. Defer unless the code moves to async execution.

- **S4 (cross-batch lever_id match)** — Theoretical correctness concern. In practice, the final
  batch always overwrites the earlier incorrect update, so output is correct. Low priority unless
  batch quality regressions are observed.

- **Q3 (anti-echoing across all models)** — A qualitative review of gpt-4o-mini and gemini
  descriptions before/after would confirm whether the anti-echoing instruction is working beyond
  haiku. Worth checking in the next iteration's insight pass.
