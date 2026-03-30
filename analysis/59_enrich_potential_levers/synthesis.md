# Synthesis

## Cross-Agent Agreement

Both agents agree on the following:

- **PR #456 is a sound infrastructure fix.** All targeted issues were fixed:
  OpenRouter `context_window` values corrected (3,900 → 131K/1M/128K/41K),
  gpt-oss-20b `max_tokens` overflow resolved (0/5 → 4/5 plans), adaptive batch size
  threshold set correctly below the OpenRouter fallback value (3,000 < 3,900), guarded
  retry implemented correctly, error tracking added and confirmed useful.
- **Overall success rate improved from 85.7% → 97.1% (+11.4pp)**, the largest single-PR
  gain in this step's optimization history.
- **UUIDs in `full_lever_context_str` (B3) are a documented known problem** listed in
  `OPTIMIZE_INSTRUCTIONS` (lines 88–92) that still has not been fixed. Both agents flag
  this independently.
- **llama3.1 phantom lever IDs (N2)** are a pre-existing bug now surfaced by the PR's
  new error tracking. 3 levers unenriched across 2 plans.
- **Fabricated % claims in `consequences` (N4)** are pre-existing and affect all 7
  models. No validator exists at the source (`identify_potential_levers.py`).
- **OPTIMIZE_INSTRUCTIONS should document phantom lever IDs** as distinct from phantom
  lever names in synergy/conflict text (I3).
- **No regressions were introduced by PR #456.** The gpt-5-nano "Purpose:" reappearance
  (N3) and llama3.1 phantom IDs (N2) are both pre-existing issues made visible by the PR.

## Cross-Agent Disagreements

**B1 (banned phrases in `Lever.consequences` field description):** Only `code_claude`
identified this. The `Lever.consequences` field description at
`identify_potential_levers.py:116–117` reads:

```
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text..."
```

This directly violates the `OPTIMIZE_INSTRUCTIONS` guidance at lines 79–82: "Do NOT add
explicit prohibitions naming banned phrases — small models treat the prohibition text as a
template and copy the banned phrases." The same language also appears in
`LeverCleaned.consequences` (lines 208–217), though `LeverCleaned` is never sent to an
LLM so that instance is harmless.

**Verdict: B1 is confirmed.** Source code inspection confirms the banned phrases are
present in the Pydantic field description sent to the LLM. `code_claude`'s diagnosis
is correct — this is the most likely root cause of the gpt-5-nano "Purpose:" template
reappearance (N3).

**B2 (false `partial_recovery` events):** Only `code_claude` identified this. Source
code confirms it: `runner.py:131` fires `logger.warning` for `actual_calls < 3`, and
`runner.py:577–583` emits a `partial_recovery` event with `expected_calls=3`. The
comment at lines 128–130 itself acknowledges that 2-call success is normal. This is
a confirmed operational false-alert bug.

**Input data mismatch (N5):** Only `insight_claude` raised this methodological concern.
It is valid — analysis 54 used `snapshot/1_deduplicate_levers` (14–18 levers/plan) while
analysis 59 uses `baseline/train` (5–8 levers/plan). This does not change the PR verdict
(success rates and metadata values are unambiguous), but confounds content-quality
comparisons between the two analyses.

## Top 5 Directions

### 1. Remove UUIDs from `full_lever_context_str`
- **Type**: code fix
- **Evidence**: B3 (code_claude), UUID cross-reference known problem (OPTIMIZE_INSTRUCTIONS
  lines 88–92), confirmed present at `enrich_potential_levers.py:209`
- **Impact**: Affects all 34 successful plans (all 7 models). Models currently copy
  UUIDs from the context string into `synergy_text` and `conflict_text` in inconsistent
  formats (full UUID, 8-char truncated, backtick-quoted, plain name). Removing UUIDs
  forces name-only references, producing consistent, human-readable synergy/conflict text.
  This is a content quality improvement for every enriched lever from every model.
- **Effort**: Low — one-line change at `enrich_potential_levers.py:209`
- **Risk**: Near-zero. The lever_id is already included in the per-batch
  `lever_details_for_prompt` section so the LLM can still return it in the
  characterization schema. The full-context string is for orientation only.

### 2. Remove banned phrases from `Lever.consequences` field description
- **Type**: prompt change
- **Evidence**: B1 (code_claude), OPTIMIZE_INSTRUCTIONS lines 79–82 ("Do NOT add
  explicit prohibitions naming banned phrases"), confirmed at
  `identify_potential_levers.py:116–117`
- **Impact**: Affects all models at the `identify_potential_levers` step. The prohibited
  phrases "Controls ... vs." and "Weakness:" in the field description are copied verbatim
  by weak models (llama3.1, qwen3-30b) into the wrong fields. This propagates into
  `enrich_potential_levers` input — corrupted `consequences` fields degrade description
  quality for all downstream models. Most likely root cause of gpt-5-nano "Purpose:"
  template reappearance (N3).
- **Effort**: Low — replace the "Do NOT include 'Controls ... vs.', 'Weakness:'" clause
  with a structural cue (see Recommendation)
- **Risk**: Low. Removing a prohibition cannot make output worse unless a model was
  somehow correctly using the banned-phrase text as a formatting cue — unlikely given
  that the OPTIMIZE_INSTRUCTIONS explicitly warns against this pattern.

### 3. Add OPTIMIZE_INSTRUCTIONS entry for phantom lever IDs
- **Type**: prompt change (documentation within OPTIMIZE_INSTRUCTIONS)
- **Evidence**: I3 (code_claude), N2 (insight_claude), confirmed surfaced by PR #456
  error tracking
- **Impact**: Prevents future PRs from ignoring or re-introducing the phantom lever ID
  problem. The current OPTIMIZE_INSTRUCTIONS entry ("Phantom lever references") covers
  wrong *names* in synergy/conflict text. It does not cover wrong *IDs* returned in
  the characterization schema itself — a distinct failure mode that silently skips lever
  enrichment. Non-function-calling models (`is_function_calling_model: false`) such as
  llama3.1 are most susceptible.
- **Effort**: Low — add a paragraph to `enrich_potential_levers.py:OPTIMIZE_INSTRUCTIONS`
- **Risk**: None (documentation only)

### 4. Fix `partial_recovery` false-alert threshold in runner.py
- **Type**: code fix
- **Evidence**: B2 (code_claude), confirmed at `runner.py:131` and `runner.py:577–583`
- **Impact**: Every 2-call completion of `identify_potential_levers` currently emits a
  WARNING log entry and a `partial_recovery` event with `expected_calls=3`. The comment
  in the code itself acknowledges this is normal. False alerts pollute `events.jsonl`
  and make it harder to identify real partial-recovery situations during analysis.
  With 7 models × 5 plans = 35 runs, many of which are 2-call completions, this generates
  substantial noise.
- **Effort**: Low — change threshold at `runner.py:131` from `< 3` to `< 2`, and
  update `expected_calls=3` to `expected_calls=2` in the event emission
- **Risk**: Low. The only risk is missing a genuine 1-call completion that happens to
  meet `min_levers=15` — but those would still be flagged at `< 2`.

### 5. Add UUID format pre-check for phantom lever ID diagnostic
- **Type**: code fix
- **Evidence**: I1 (code_claude), N2 (insight_claude), confirmed at
  `enrich_potential_levers.py:267–276`
- **Impact**: Currently, phantom lever IDs are caught only by the map-lookup check
  (`char.lever_id in enriched_levers_map`). For llama3.1, the root cause is UUID
  truncation (e.g., `056fa843-5572-40a5-bca5-bca5cc18408` — 35 chars, missing final
  digit). A UUID format pre-check would immediately distinguish:
  - Format-invalid ID (truncated/hallucinated UUID, e.g. llama3.1's non-function-calling
    structured output): requires prompt/schema fix
  - Format-valid but unrecognized ID (hallucinated valid UUID): requires input validation
  This distinction is necessary to pick the right fix for each model type.
- **Effort**: Low — add a UUID regex constant and one conditional before the map lookup
- **Risk**: None — additive diagnostic only, no behavior change

## Recommendation

**Pursue Direction 1 first: remove UUIDs from `full_lever_context_str`.**

This is the highest-impact change for the lowest risk. It fixes a content quality
problem that affects every enriched lever from every model — 34/35 successful plans.
The UUID contamination in synergy/conflict fields has been documented in
OPTIMIZE_INSTRUCTIONS since at least analysis 54 and was confirmed present in the current
runs. It is the only unfixed item in OPTIMIZE_INSTRUCTIONS that is both confirmed
observable and one-line-fixable.

**Specific change:**

File: `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`, line 209

Current:
```python
full_lever_context_str = "\n".join([
    f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize
])
```

Replace with:
```python
full_lever_context_str = "\n".join([
    f"- {lever.name}" for lever in levers_to_characterize
])
```

The `lever_id` is already included in the per-batch `lever_details_for_prompt` section
(the part that asks the LLM to return characterizations), so the LLM can still identify
which lever it's writing about. The full-context string's purpose is cross-lever
orientation — for that, names are sufficient and more readable.

Expected outcome: synergy_text and conflict_text will reference other levers by name
only, eliminating the UUID/truncated-UUID/backtick inconsistency currently documented
in OPTIMIZE_INSTRUCTIONS.

## Deferred Items

- **B1 (banned phrases in `Lever.consequences` field)**: High-value second change.
  Replace "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique
  text in this field — those belong exclusively in review_lever." with "Describe direct
  effects and downstream trade-offs only. Do not include critique or evaluation language."
  This is a prompt change at `identify_potential_levers.py:116–117` (and the identical
  text at `LeverCleaned.consequences:213–215`, though that instance is harmless).

- **I3 (OPTIMIZE_INSTRUCTIONS phantom lever ID entry)**: Add after the existing "Phantom
  lever references" entry: a new entry distinguishing phantom lever *IDs* returned in the
  characterization schema (unknown_lever_id error) from phantom lever *names* in
  synergy/conflict text. Note non-function-calling models as most susceptible.

- **B2 (false partial_recovery threshold)**: Low-effort operational cleanup.
  `runner.py:131` threshold `< 3` → `< 2`.

- **I1 (UUID format pre-check)**: Useful diagnostic for llama3.1 phantom IDs but
  deferred until the B3 fix establishes a new baseline (since B3 may reduce phantom
  ID frequency by removing UUID exposure in the context string).

- **I2 (fabricated % validator in `identify_potential_levers`)**: Pre-existing problem
  affecting all models. A `@field_validator` on `consequences` detecting `\d+%` or
  `\d+x\b` patterns would quantify prevalence. Medium effort; deferred because it
  doesn't block the immediate quality improvement path.

- **I5 (`review_lever` length cap)**: System prompt says 20–40 words but validator only
  enforces 10-char minimum. Low priority — word-count padding is already listed in
  OPTIMIZE_INSTRUCTIONS and content-level verbosity hasn't been observed as a top
  problem in recent analyses.

- **gpt-oss-20b parasomnia timeout (N1)**: gpt-oss-20b is fundamentally slow (gta_game:
  243s, parasomnia: timeout at 600s). Options: raise `--plan-timeout` to 900s, add a
  model-specific timeout config, or document gpt-oss-20b as non-production-grade for
  this step. Deferred — not a code bug, a model capability limitation.

- **Input data standardization (N5)**: Future iterations should use a consistent input
  set to enable clean before/after content-quality comparisons. Consider updating the
  snapshot to match `baseline/train`.
