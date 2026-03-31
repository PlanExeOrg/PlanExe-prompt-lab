# Synthesis

## Cross-Agent Agreement

Only one agent produced output: `code_claude.md`. The `insight_claude.md` file
contains only an error — Claude Code exceeded the 1200s timeout and produced no
quality observations. There is therefore no cross-agent comparison possible for
this run.

The single code review identified:
- A medium-severity bug (B1) in `runner.py` that emits false-positive
  `partial_recovery` warnings on healthy 2-call runs.
- Two low-severity bugs (B2, B3) related to case-sensitive deduplication and
  copy-paste drift between `Lever` and `LeverCleaned`.
- Three suspect patterns (S1–S3) related to parallel dispatcher contamination,
  permissive review validation, and a template-lock risk in `strategic_rationale`.
- Five improvement opportunities (I1–I5).
- A KEEP verdict for PR #471.

## Cross-Agent Disagreements

None — only one agent completed. All claims below are verified directly against
the source.

**B1 verified**: `runner.py:131` reads `if actual_calls < 3:`, but the comment
at lines 128-130 explicitly says "A 2-call success is normal for models that
produce 8+ levers per call." The condition fires on `actual_calls == 2` — the
very case the comment labels normal. The `partial_recovery` *event* at
`runner.py:579` correctly uses `< 2`, making the logger threshold inconsistent
with the event threshold.

**B2 verified**: `identify_potential_levers.py:368` uses a plain `set` for
`seen_names`, so `"Market Positioning"` and `"Market positioning"` both pass
through as distinct levers.

**S3 verified**: `identify_potential_levers.py:185` contains "explain how the
chosen levers navigate the fundamental conflicts between speed, cost, scope, and
quality" — a copyable domain phrase in a chain-of-thought field. This is
consistent with the OPTIMIZE_INSTRUCTIONS warning about structural cues in field
descriptions.

**PR #471 verified**: `Lever.consequences` now reads:
> "Focus on cause-effect relationships and factual outcomes; save critical
> assessments for the review_lever field."
This replaces the negative-priming prohibition. `LeverCleaned.consequences`
carries the same text but `LeverCleaned` is never sent to an LLM (confirmed at
line 196), so only the `Lever` change is functional. The OPTIMIZE_INSTRUCTIONS
constant (lines 82-83) explicitly warns against naming banned phrases; PR #471
follows this guidance correctly.

## Top 5 Directions

### 1. Fix the `partial_recovery` warning threshold in runner.py (B1)
- **Type**: code fix
- **Evidence**: code_claude B1 + I3; verified against runner.py:128-134 and
  runner.py:577-583
- **Impact**: Every healthy 2-call run currently emits a misleading
  `partial_recovery` logger warning. This pollutes the self-improve analysis
  signal — analysis tooling reading the log may count healthy runs as degraded.
  The `partial_recovery` *event* in events.jsonl (line 579) already uses the
  correct threshold (`< 2`), so the fix closes the inconsistency between the
  two.
- **Effort**: low — one-character change: `actual_calls < 3` → `actual_calls < 2`
- **Risk**: negligible; no logic depends on the logger threshold value

### 2. Keep PR #471 (positive framing in `consequences` field)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: code_claude PR Review section; consistent with OPTIMIZE_INSTRUCTIONS
  lines 82-83
- **Impact**: Removes negative-priming prohibition from `Lever.consequences` for
  mid-tier models. Small models that copy banned-phrase names from field
  descriptions will no longer see "Controls ... vs." or "Weakness:" as templates.
  The change affects every model and every prompt that calls this step. The
  `LeverCleaned` side is documentation alignment only.
- **Effort**: already done (PR under evaluation)
- **Risk**: low; mild residual template-lock risk on "cause-effect relationships",
  but substantially safer than the prohibition text it replaces

### 3. Harden `review_lever` minimum length (S2 + I2)
- **Type**: code fix
- **Evidence**: code_claude S2 + I2; verified at identify_potential_levers.py:173
- **Impact**: The current validator accepts 10-character strings (e.g. "Too risky.")
  as valid `review_lever` values. The system prompt targets 20–40 words; 40
  characters is the minimum for that. Raising the floor rejects low-quality
  reviews before they reach the `enrich_potential_levers` step, which depends on
  review quality. The soft target comment acknowledges 50 chars as intent; 40 is
  a reasonable enforceable minimum.
- **Effort**: low — change one integer in the validator
- **Risk**: low; may cause more validation retries for the weakest models on the
  first few attempts, but the adaptive loop handles retries

### 4. Remove the domain-example from `strategic_rationale` description (S3)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: code_claude S3; consistent with OPTIMIZE_INSTRUCTIONS warning about
  structural cues in field descriptions (lines 87-93)
- **Impact**: `strategic_rationale` is chain-of-thought (not passed downstream),
  so template lock here only wastes tokens. However, when models copy
  "speed, cost, scope, and quality" verbatim, their rationale becomes domain-
  agnostic filler rather than genuine analysis, which can degrade lever quality.
  Removing the example phrase leaves the instruction ("justify why the selected
  levers are the most critical") without a copyable template.
- **Effort**: low — minor field description edit
- **Risk**: very low; `strategic_rationale` is discarded before downstream use

### 5. Case-normalise the deduplication guard (B2 + I5)
- **Type**: code fix
- **Evidence**: code_claude B2 + I5; verified at identify_potential_levers.py:368
- **Impact**: Prevents capitalisation variants (e.g. "Market Positioning" vs
  "Market positioning") from passing through as separate levers and inflating
  token cost in the downstream `DeduplicateLeversTask`. Low but real cost saving
  for models that inconsistently capitalise names.
- **Effort**: low — change `lever.name in seen_names` to
  `lever.name.lower() in seen_names` and `seen_names.add(lever.name)` to
  `seen_names.add(lever.name.lower())`; preserve original casing in
  `LeverCleaned.name`
- **Risk**: negligible

## Recommendation

**Fix B1 first**: change `runner.py:131` from `actual_calls < 3` to
`actual_calls < 2`.

This is the single most impactful and lowest-risk fix available. It closes a
real inconsistency between the logger warning threshold and the `partial_recovery`
event threshold, which are currently mismatched:

- Logger warning fires at `actual_calls < 3` — catches 2-call runs (normal)
- `partial_recovery` event fires at `calls_succeeded < 2` — correctly skips 2-call runs

The comment at lines 128-130 explicitly documents that 2-call success is normal.
The warning contradicts the comment and pollutes the analysis signal. Because the
self-improve pipeline reads logs and events to distinguish healthy from degraded
runs, false-positive `partial_recovery` warnings directly degrade the quality of
the optimization loop's input data.

**Exact change:**

File: `/Users/neoneye/git/PlanExeGroup/PlanExe/self_improve/runner.py`
Line: 131

```python
# Before
if actual_calls < 3:

# After
if actual_calls < 2:
```

PR #471 is also sound and should be merged as-is. Its benefit (eliminating
negative-priming in `consequences`) is real for mid-tier models and carries
negligible risk.

## Deferred Items

- **I2 (harden review_lever minimum)**: Raise `identify_potential_levers.py:173`
  from `len(v) < 10` to `len(v) < 40`. Worth doing, but has no direct effect on
  the analysis signal for this experiment.
- **S3 (strategic_rationale domain example)**: Remove "speed, cost, scope, and
  quality" from the field description. Low risk, low urgency.
- **B2/I5 (case-normalise deduplication)**: Change the `seen_names` lookup to
  use `.lower()`. Low effort, low but real token cost saving.
- **I1 (shared field description constants)**: Extract `_CONSEQUENCES_DESCRIPTION`
  and `_OPTIONS_DESCRIPTION` as module-level constants to prevent `Lever` /
  `LeverCleaned` drift. Maintenance improvement, not a functional fix.
- **S1 (dispatcher contamination)**: Background correctness concern for parallel
  workers. Not urgent — the contaminated data is discarded before use — but
  worth a refactor if parallel execution is expanded.
- **I4 (expose min_levers as parameter)**: Convenience for experimentation; not
  a correctness issue.
- **Insight timeout**: The `insight_claude.md` timeout should be investigated
  separately. A 1200s timeout on the insight step suggests the history runs being
  analyzed are large or the insight prompt is very expensive. Consider adding a
  per-file timeout or reducing the history window for future analysis runs.
