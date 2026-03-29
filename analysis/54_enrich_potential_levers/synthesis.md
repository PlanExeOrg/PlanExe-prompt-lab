# Synthesis

## PR Under Evaluation

**PR #451** — "Include consequences and review in enrich batch prompt"
Adds `Consequences: {lever.consequences}` and `Review: {lever.review}` to
`lever_details_for_prompt` in `enrich_potential_levers.py:171-178`.

**Verdict: KEEP** (both agents agree).

---

## Cross-Agent Agreement

Both `insight_claude` and `code_claude` agree on the following:

- **PR #451 is correct and should be kept.** The implementation matches the intent
  from analysis 53 synthesis direction 1. gpt-5-nano's template artifact
  ("Purpose: / Objectives: / Key success metrics:") is entirely eliminated; conflict
  texts now echo lever-specific trade-off language across models.

- **B1 (no per-batch retry) is the root cause of gpt-oss-20b's 0/5 failures.**
  Both agents confirmed that `enrich_potential_levers.py:216-218` raises immediately
  on any batch exception, killing all subsequent batches. This was pre-existing and
  unchanged by the PR.

- **B2 (full UUIDs in `full_lever_context_str`) worsened after the PR.**
  `enrich_potential_levers.py:156` still emits `f"- {lever.lever_id}: {lever.name}"`.
  Before the PR, qwen3-30b consistently used truncated 8-char UUIDs. After the PR,
  its format is inconsistent across plans (name-only in silo, full UUIDs in
  sovereign_identity). The added context changes how the model interprets the format
  signal.

- **The ~18-20% input token increase is expected and acceptable.** Both agents
  confirmed the cost table and treated it as a known trade-off, not a regression.

- **I3/I4 (anti-consequence-echoing guidance)** is needed. llama3.1 descriptions
  dropped from 0.80× to 0.65× baseline — the model is summarizing `consequences`
  verbatim rather than elaborating. Neither the system prompt nor OPTIMIZE_INSTRUCTIONS
  currently warns against this.

- **I7 (qualitative mechanism guidance for synergy/conflict)** remains the
  highest content quality gap: qwen3-30b synergy/conflict is still 0.74-0.76×
  baseline.

---

## Cross-Agent Disagreements

There are no material disagreements. The code review raises additional bugs (B3, B4,
B5, S1-S3) not discussed in the insight file. These were verified against source code:

- **B3 (silent lever drop) — confirmed.** `enrich_potential_levers.py:220-228` logs
  an error but returns no count to the caller. No minimum threshold is checked.

- **B4 (calls_succeeded hardcoded to 1) — confirmed.** `runner.py:184` always sets
  `calls_succeeded=1` in `_run_enrich`, regardless of how many batches ran. The
  `_run_levers` function at line 126 correctly uses `len(result.responses)`.

- **B5 (partial_recovery false positives) — confirmed but scoped.** The check at
  `runner.py:577-583` only fires for the `identify_potential_levers` step, not
  `enrich_potential_levers`. B5 is a real bug in the identify step but is out-of-scope
  for this synthesis.

- **S1-S3 (latent concurrency issues) — uncontested, non-blocking.** Closure capture
  (S1), global dispatcher cross-contamination (S2), and unsafe list mutation (S3) are
  real structural concerns but not triggered by the current single-threaded test setup.
  They are deferred.

---

## Top 5 Directions

### 1. Strip UUIDs from `full_lever_context_str`
- **Type**: code fix (1 line)
- **Evidence**: B2 confirmed by both agents; worsened post-PR (N4 in insight, I1 in
  code review). Source-verified at `enrich_potential_levers.py:156`.
- **Impact**: Eliminates UUID artifacts from synergy/conflict text for all 30 working
  plans. Before the PR, qwen3-30b produced consistent (if wrong) 8-char truncations;
  after PR #451 it is now nondeterministic — name-only in some plans, full UUIDs in
  others. A 1-line fix normalizes this for all models immediately.
- **Effort**: minimal — change `f"- {lever.lever_id}: {lever.name}"` to
  `f"- {lever.name}"`.
- **Risk**: none. Lever IDs appear nowhere in synergy/conflict output; only names are
  needed for human-readable references.

### 2. Add per-batch retry in `enrich_potential_levers.py`
- **Type**: code fix
- **Evidence**: B1 confirmed by both agents; root cause of gpt-oss-20b 0/5 success
  (N1 in insight). Source-verified at `enrich_potential_levers.py:216-218`.
- **Impact**: Recovers gpt-oss-20b from 0/5 to potentially 5/5, adding 5 plan
  completions. Also protects all models against transient failures (stochastic token
  overflow, network blips) that currently kill entire plans on a single bad batch.
- **Effort**: low — on exception, continue to next batch (minimal fix) or retry with
  batch_size=1 (stronger fix). Compare with `identify_potential_levers.py:329-348`
  which already implements a correct adaptive loop.
- **Risk**: low. Partial enrichment is already possible (B3 allows it silently). A
  retry loop makes the existing behavior explicit and more resilient.

### 3. Add anti-consequence-echoing guidance to system prompt and OPTIMIZE_INSTRUCTIONS
- **Type**: prompt change + OPTIMIZE_INSTRUCTIONS update
- **Evidence**: I3/I4 in code review; H1/H2 in insight. llama3.1 description length
  dropped from 0.80× to 0.65× baseline post-PR (N2), below the acceptable range.
  Root mechanism: when `consequences` is in the prompt, weak models take the shortest
  path — rephrase it and stop.
- **Impact**: Restores llama3.1 description depth to ≥0.75× baseline without
  removing the PR's grounding benefit. Also documents the new failure mode in
  OPTIMIZE_INSTRUCTIONS so it survives future iterations.
- **Effort**: low — add one clause to the `description` field instruction in
  `ENRICH_LEVERS_SYSTEM_PROMPT`, and one bullet to `OPTIMIZE_INSTRUCTIONS`.
- **Risk**: low. The elaboration instruction can only increase description depth; the
  only risk is verbosity for already-long models (haiku, gpt-5-nano), which is
  manageable.

### 4. Add qualitative mechanism guidance for synergy/conflict
- **Type**: prompt change
- **Evidence**: I7 in code review; D3 deferred from analysis 53, still unaddressed.
  qwen3-30b synergy/conflict at 0.74-0.76× baseline. The current system prompt
  gives a quantitative "(40-60 words)" target but no guidance on what kind of
  information fills those words.
- **Impact**: Would improve synergy/conflict specificity for all models, especially
  qwen3-30b. Content quality improvement affects all 30 working plans in downstream
  steps (FocusOnVitalFewLevers, ScenarioGeneration).
- **Effort**: low — add one sentence to the `synergy_text` and `conflict_text` field
  descriptions: "Name the specific mechanism by which the two levers interact, and
  identify one concrete consequence of that interaction."
- **Risk**: low-medium. Adding mechanism guidance may cause some models to over-specify
  or produce false mechanism claims. Should be tested in one iteration before merging.

### 5. Fix silent lever drop and `calls_succeeded` monitoring
- **Type**: code fix
- **Evidence**: B3 and B4 confirmed by code review. Source-verified at
  `enrich_potential_levers.py:220-228` and `runner.py:184`.
- **Impact**: B3 fix adds a minimum threshold check before returning, ensuring
  downstream steps (FocusOnVitalFewLevers) receive a complete lever set or an
  explicit error. B4 fix makes `calls_succeeded` report the actual batch count
  rather than a hardcoded 1, enabling monitoring tools to detect partial failures.
  Combined, these close a silent data-loss channel.
- **Effort**: low — B3 needs ~5 lines (threshold check + error/warning return); B4
  needs the `EnrichPotentialLevers` dataclass to surface batch count, then
  `runner.py:_run_enrich` to use it.
- **Risk**: low. These are observability fixes that do not change the happy-path logic.

---

## Recommendation

**Pursue Direction 1 first: strip UUIDs from `full_lever_context_str`.**

**File**: `enrich_potential_levers.py`, **line 156**

**Current code**:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

**Fix**:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

**Why first**: This is the smallest possible change (delete `{lever.lever_id}: ` from
a format string) with the highest confidence of improvement and zero risk of regression.
It directly addresses a bug that measurably worsened with PR #451 — qwen3-30b went from
consistently wrong (truncated 8-char UUIDs) to nondeterministically wrong (name-only in
some plans, full UUIDs in others). The fix removes the format signal that causes models
to copy UUID strings into human-readable output, improving synergy/conflict text quality
for all 30 currently working plans. The `lever_id` field is needed only for the
`enriched_levers_map` key lookup (line 205) and output JSON, neither of which require
it to appear in the context list.

Direction 2 (retry) should follow immediately after, as it is also a code-only fix with
no prompt impact and high expected yield (restoring 5 failed plans). These two can be
bundled in one PR.

---

## Deferred Items

- **Direction 2 (B1 retry)**: Should be the immediate follow-up to Direction 1, or
  bundled with it. gpt-oss-20b's 0/5 failure rate is the most severe ongoing issue.

- **Direction 3 (anti-echoing guidance)**: Important to address the llama3.1 regression
  introduced by PR #451. Combine with an OPTIMIZE_INSTRUCTIONS update documenting
  "consequence echoing" as a distinct failure mode.

- **Direction 4 (mechanism guidance)**: D3 from analysis 53 remains open. qwen3-30b
  synergy/conflict terseness (0.74-0.76× baseline) is the highest remaining content
  quality gap for working models.

- **Direction 5 (B3/B4 monitoring)**: Data integrity and observability improvements.
  Implement alongside Direction 2 (retry) since both touch the same code path.

- **B5 (partial_recovery false positive for identify_potential_levers)**: The warning
  at `runner.py:131` and event at `runner.py:579-583` fire for normal 2-call successes.
  The comment acknowledges 2-call is expected for models producing ≥8 levers per call.
  The threshold should be lowered to `< 2` or removed entirely. Out-of-scope for this
  synthesis (identify step, not enrich), but should be tracked.

- **S1-S3 (latent concurrency issues)**: Closure variable capture (S1), global
  dispatcher cross-contamination (S2), and unsafe list mutation (S3) in runner.py.
  None triggered in current single-threaded runs. Address before enabling
  `workers > 1`.

- **I5 (options validator inconsistency)**: The `check_option_count` validator in
  `identify_potential_levers.py:147-158` accepts >3 options despite "Exactly 3"
  specification. Align field description, system prompt, and validator policy.

- **I6 (English-only anti-patterns in consequences field description)**:
  `identify_potential_levers.py:113-119` lists English-specific phrases
  ("Controls ... vs.", "Weakness:") as anti-patterns in the field description — exactly
  the behavior OPTIMIZE_INSTRUCTIONS warns against at lines 61-68. Replace with
  structural guidance: "do not include critique or trade-off text — that belongs in
  `review_lever`."
