# Synthesis

## Cross-Agent Agreement

Only one agent produced each artifact (insight_claude and code_claude), so
"cross-agent agreement" here means consistency between the insight and the code
review rather than between independent agents.

The two artifacts agree on every substantive finding:

- **PR primary goal achieved**: gpt-oss-20b recovered from 3/5 → 5/5 plans, 6 → 0
  errors. Word-count reduction (~35%) is confirmed in outputs. Verdict CONDITIONAL,
  not KEEP, because of the llama3.1 regression.
- **B1 (XML-tag in lever_id)**: Consensus that `enrich_potential_levers.py:275`
  performs no stripping before the `enriched_levers_map` lookup, causing 10 errors
  in llama3.1 gta_game batch 1. The fix (C1/I1) is identical in both files.
- **S1 (negative anti-echoing instruction violates OPTIMIZE_INSTRUCTIONS)**: Both
  flag that "Do NOT repeat…" at lines 140 and 171 copies the forbidden prohibition
  pattern documented in `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS
  (lines 79–82). Positive reformulation is recommended in both.
- **S2 (no lever_id output guidance)**: Both note the absence of any instruction
  about what to put in the `lever_id` JSON field, leaving non-function-calling
  models to infer format from the `<lever>uuid</lever>` prompt markup.
- **S3 (stale OPTIMIZE_INSTRUCTIONS word-count reference)**: Both flag line 73 still
  referencing "80-100 word target" after PR #467 changed it to 50-70 words.
- **Partial anti-echoing effect**: Fabricated percentage claims reduced (haiku: 3→0)
  but structural echoing (consequence vocabulary, framing) persists.

## Cross-Agent Disagreements

No material disagreements exist between the two artifacts. The code review adds
B2 (batches_succeeded incremented before lever lookup) and S4 (TrackActivity
handler accumulation in parallel runs), which are absent from the insight but
not contradicted by it.

**Verification of disputed or uncertain claims via source code:**

- **B1 confirmed** (`enrich_potential_levers.py:217, 239–240, 275`): Map is keyed
  by bare UUIDs at line 217. Prompt format uses `<lever>{lever.lever_id}</lever>`
  at lines 239–240. Lookup at line 275 does no stripping. Confirmed bug.
- **B2 confirmed** (`enrich_potential_levers.py:272`): `batches_succeeded += 1` at
  line 272 precedes the `for char in batch_result.characterizations:` loop at
  line 274. A batch where every `char.lever_id` fails the map lookup still
  increments the counter. Confirmed.
- **S1 confirmed** (`identify_potential_levers.py:79–82`): "Do NOT add explicit
  prohibitions naming banned phrases — small models treat the prohibition text as a
  template." The anti-echoing instruction at lines 140 and 171 of
  `enrich_potential_levers.py` directly violates this guidance.
- **S3 confirmed** (`enrich_potential_levers.py:71–73`): OPTIMIZE_INSTRUCTIONS
  still says "Models inflate to hit the 80-100 word target." Stale after PR #467.
- **S4 partially confirmed** (`runner.py:248–250, 280–283`): Handler is added
  inside `_file_lock` but the lock is released during plan execution. Events
  from concurrent plans could trigger the wrong handler. This is a pre-existing
  concern unrelated to PR #467, with no observed misfiling in runs 69–75.

## Top 5 Directions

### 1. Fix XML-tag stripping before lever_id map lookup (B1)
- **Type**: code fix
- **Evidence**: Both artifacts (C1 in insight, B1/I1 in code review). Confirmed by
  source code at `enrich_potential_levers.py:217, 239–240, 275`.
- **Impact**: Recovers 5 levers per affected llama3.1 batch with zero model retries.
  Eliminates the new regression introduced by PR #466 + PR #467 interaction.
  Prevents future occurrences regardless of prompt changes.
- **Effort**: Low — 4 lines before line 275.
- **Risk**: Minimal. The strip only triggers for `lever_id` values that would
  otherwise cause `unknown_lever_id` errors anyway. Bare UUIDs pass through
  unchanged.

### 2. Replace negative anti-echoing instruction with positive directive (S1/I3/H2)
- **Type**: prompt change
- **Evidence**: Both artifacts flag this at `enrich_potential_levers.py:140, 171`.
  The violation of the OPTIMIZE_INSTRUCTIONS principle is confirmed at
  `identify_potential_levers.py:79–82`.
- **Impact**: Expected to reduce structural consequence echoing across all models,
  especially small/weak ones. The current wording partially works (haiku: 3→0
  fabricated % claims) but leaves structural echoing (N3) in gemini and haiku.
  A positive directive removes the "Do NOT" template-as-instruction risk.
- **Effort**: Low — reword two locations (Pydantic field description line 140,
  system prompt line 171).
- **Risk**: Low. Positive directives are consistently more effective than negative
  prohibitions for small models per OPTIMIZE_INSTRUCTIONS.

  Draft wording for line 171:
  > `**description`:** (50-70 words) Explain what this lever is optimising for,
  > what project-specific trade-offs it accepts, and what observable evidence
  > would indicate success — drawing on the lever's own logic rather than
  > restating the consequences or review fields.

  Draft for Pydantic field description line 140:
  > `"A concise description (50-70 words) of the lever's purpose, scope, and
  > success criteria — explain the lever's own optimisation target and the
  > observable evidence of success, not a restatement of the consequences field."`

### 3. Add explicit lever_id output instruction to system prompt (S2/I4/H1)
- **Type**: prompt change
- **Evidence**: Both artifacts (S2 in code review, H1 in insight). The `<lever>uuid</lever>`
  markup in the batch prompt (line 239–240) is the only UUID-format cue, and the
  system prompt (lines 163–178) gives no guidance on what to put in `lever_id`.
- **Impact**: Directly addresses the root cause of the XML-tag leakage regression.
  A positive instruction ("output only the raw UUID string exactly as shown")
  closes the format ambiguity without requiring a code fix.
- **Effort**: Low — one sentence added to the system prompt.
- **Risk**: Low. Follows the positive-framing pattern established in OPTIMIZE_INSTRUCTIONS.
  Note: this is complementary to B1 (Direction 1), not a replacement.

  Draft addition after the existing `**conflict_text**` item in the system prompt:
  > `In the \`lever_id\` field, output only the raw UUID string exactly as shown
  > in the batch (e.g., \`1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd\`).`

### 4. Update OPTIMIZE_INSTRUCTIONS to reflect new targets and document XML-tag regression (S3/I5)
- **Type**: documentation change (within source file constant)
- **Evidence**: Code review S3/I5; confirmed by source at `enrich_potential_levers.py:71–73`.
- **Impact**: Future optimization iterations read OPTIMIZE_INSTRUCTIONS to understand
  known problems. The stale "80-100 word target" reference will mislead them into
  treating shorter outputs as already optimal rather than as a deliberate change.
  Documenting the XML-tag-in-lever_id failure mode closes a knowledge gap.
- **Effort**: Low — edit two sections of the OPTIMIZE_INSTRUCTIONS string.
- **Risk**: None — pure documentation update.

  Changes:
  - Line 71-73: update "80-100 word target" → "50-70 word description target
    (20-40 for synergy/conflict), changed in PR #467"
  - After the UUID leakage entry (lines 88-96): add XML-tag-in-lever_id inverse
    failure mode as described in I5.

### 5. Fix batches_succeeded counter to reflect actual enrichment (B2)
- **Type**: code fix
- **Evidence**: Code review B2; confirmed at `enrich_potential_levers.py:272`.
- **Impact**: Improves observability. Currently a batch where all lever_id lookups
  fail is still counted as succeeded. Downstream reporting (PlanResult.calls_succeeded,
  partial_recovery check in events.jsonl) receives a misleading signal. Fix makes
  the counter reflect "at least one lever actually enriched" semantics.
- **Effort**: Low — move `batches_succeeded += 1` inside the loop, or track
  `enriched_count` and conditionally increment after the loop.
- **Risk**: Low. No functional impact on lever enrichment itself; only affects
  the counter value.

## Recommendation

**Implement Direction 1: strip XML tags from lever_id before the map lookup.**

File: `enrich_potential_levers.py`, around line 274–275.

Replace:
```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
```

With:
```python
for char in batch_result.characterizations:
    raw_id = char.lever_id.strip()
    if raw_id.startswith("<lever>") and raw_id.endswith("</lever>"):
        raw_id = raw_id[7:-8]
    if raw_id in enriched_levers_map:
```

And update the three subsequent references to `char.lever_id` in the same block
(the `update(...)` call and the `errors.append(...)` call) to use `raw_id` where
appropriate for the map key, while keeping `char.lever_id` in the error record
for traceability.

**Why first:** It is a confirmed bug with a confirmed data loss consequence (5
levers lost per affected batch), a 4-line fix, and zero risk to non-affected
batches. It neutralizes the regression introduced by the PR #466 + PR #467
interaction without requiring further prompt experiments or re-runs. Direction 2
(positive anti-echoing) and Direction 3 (lever_id output instruction) are
complementary and should follow immediately, but the code fix is higher-certainty:
prompt changes require re-runs to validate, while this fix restores correctness
by construction.

## Deferred Items

- **Direction 2 + 3 combined PR**: Replace the negative anti-echoing instruction
  (S1/I3) and add the positive lever_id output instruction (S2/I4) in the same
  prompt-change PR. Both are low-risk wording changes that reinforce each other
  and can be validated in a single self-improve iteration.

- **Direction 4 (OPTIMIZE_INSTRUCTIONS update)**: Can be bundled into either the
  code fix PR or the prompt change PR. Low effort, no functional impact.

- **Direction 5 (B2 counter fix)**: Worth doing but has no impact on output quality
  or error recovery. Bundle with a future code-quality pass.

- **S4 (TrackActivity handler accumulation in parallel runs)**: Pre-existing issue
  in `runner.py`, unrelated to PR #467. No observed failures in runs 69–75.
  Investigate only if misattributed activity data is observed.

- **I6 (check_option_count upper bound)**: In `identify_potential_levers.py:147–158`,
  the validator only enforces a lower bound of 3 options. A `len(v) > 3` warning
  log would improve visibility without changing behavior. Deferred; no evidence
  of active impact on enrich_potential_levers runs.

- **I7 (20-word lower bound tension for conflict_text)**: Gemini's 149-char
  conflict_text average (≈23 words) is at the absolute lower bound. If future
  iterations tighten the target further, genuine tension identification becomes
  structurally difficult. Defend ≥25 words for conflict_text if this becomes an
  issue.

- **Q4 (haiku extra-characterization, batch size)**: Haiku still shows 4
  `unknown_lever_id` errors (down from 5). Whether reducing batch size from 5 to 3
  for haiku would eliminate these remains untested.

- **PR #467 overall verdict**: CONDITIONAL → upgrading to KEEP once B1 is fixed.
  The primary goal (gpt-oss-20b full recovery, 35/35 plans) is a clear win. The
  llama3.1 XML-tag regression is the only blocker, and it is addressable with a
  code fix rather than a PR revert.
