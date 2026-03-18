# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude, code_claude) converge on the following:

1. **PR #346 verdict: CONDITIONAL — do not merge as-is.** The structured classification schema
   (`lever_type` enum + `decision_axis` sentence) is sound in principle and the output quality
   when it succeeds is good. However, the batch-rejection architecture causes a 35–65% lever
   count regression for gemini and gpt-4o-mini, directly contradicting OPTIMIZE_INSTRUCTIONS
   ("over-generation is fine; step 2 handles extras").

2. **Template lock in `review_lever` is a persistent structural problem.** Runs 34 (qwen3),
   35 (gpt-4o-mini), and 36 (gemini) all produce reviews following the pattern
   "The tension between X and Y is [critical/unresolved]. None of the options [explicitly/fully]
   [verb]…". All three current review examples in system prompt section 5 end with
   "none of the options [verb]" phrasing, which models generalize across all domains.

3. **B1 (docstring/implementation mismatch in `check_review_format`):** The docstring says
   "at least 50 characters" but the code checks `< 10`. Both agents recommend raising the
   threshold to 50 chars — a one-line fix that matches documented intent.

4. **Ollama's `options < 3` failures are pre-existing and not caused by the PR.** They appear
   in run 31 (without PR) for gta_game and hong_kong_game. The PR makes this worse by adding
   more validators that trigger the same all-or-nothing batch rejection.

5. **No fabricated percentages** in current runs (31–37): a major improvement over baseline
   (which had 7 in hong_kong_game). Confirmed by both agents; the current prohibitions are working.

---

## Cross-Agent Disagreements

There are no substantive disagreements between the two agents. The code review confirms every
finding from the insight with code-level evidence:

- N4 (lever count regression) → confirmed at `identify_potential_levers.py:329` (batch discard on exception)
- N3 (template lock) → confirmed at `identify_potential_levers.py:247–251` (section 5 examples)
- B1 (docstring mismatch) → confirmed at `identify_potential_levers.py:153–158`

The only open question neither resolves with certainty: whether the lever count drop in runs 24–30
was caused primarily by `lever_type` enum failures or `decision_axis` min-length failures. Both
agents agree the events.jsonl files for runs 24–30 should be checked for Pydantic error messages
to confirm the exact validator responsible.

---

## Top 5 Directions

### 1. Fix PR #346's batch-rejection architecture before merging
- **Type**: code fix
- **Evidence**: N4 (insight), C1/C2 in code review PR section, confirmed at
  `identify_potential_levers.py:329`. Gemini: 17→6 levers (−65%); gpt-4o-mini: 17→11 (−35%).
  Both agents independently conclude this is caused by new Pydantic validators (`lever_type` enum,
  `decision_axis` min-length) triggering the existing all-or-nothing batch discard at line 329.
- **Impact**: Recovers the full lever count (back toward 15–21 range) for all capable models.
  With only 6 levers surviving for gemini, the downstream scenario pipeline has critically
  reduced diversity. This is the single change that determines whether the PR can be merged at all.
- **Effort**: Medium. Requires converting the new field validators from hard `ValueError` raises
  to per-lever normalization. Specifically:
  - `lever_type`: add a `mode='before'` validator that lowercases, strips whitespace, and maps
    common synonyms ("operational"→"operations", "method"→"methodology") before the enum check.
    Only reject if the value cannot be mapped at all; log a warning rather than raising.
  - `decision_axis`: strip the value and apply a soft minimum (log a warning if < 20 chars),
    but do not raise a `ValueError` that discards the entire batch. A short or missing
    `decision_axis` is preferable to losing 5–7 otherwise-valid levers.
- **Risk**: Softening validators may allow low-quality field values into the output. Mitigate
  by logging every normalization/fallback so they can be audited.

---

### 2. Diversify `review_lever` examples to break template lock
- **Type**: prompt change
- **Evidence**: N3 (insight, severe in run 35, moderate in runs 34/36), I3 (code review),
  and OPTIMIZE_INSTRUCTIONS lines 73–79 already name this as "template-lock migration".
  All three examples in system prompt section 5 end with "none of the options [verb]" —
  models generalize this closing across all domains and all levers.
- **Impact**: Affects all models — template lock is present in every model run at moderate
  to severe levels. Diverse examples would reduce the most visible quality regression in the
  current batch (run 35 gpt-4o-mini has 17/17 reviews in the same pattern).
- **Effort**: Low. Replace the three existing examples with three that use structurally
  distinct critique styles:
  - One naming an **excluded stakeholder** who bears the risk (e.g., "…but the crew's union
    jurisdiction clause blocks the most cost-efficient option before negotiations even start")
  - One naming a **cost that compounds over time** (agriculture example is good; keep it)
  - One naming a **prerequisite condition the options skip** (e.g., "…yet all three options
    presuppose regulatory approval that has a 14-month backlog")
  Avoid shared sentence endings. Each example must be domain-specific and non-portable.
- **Risk**: New examples might create new lock patterns. Mitigate by ensuring no two examples
  share the same sentence-ending template.

---

### 3. Fix B1: raise `review_lever` minimum from 10 to 50 chars
- **Type**: code fix
- **Evidence**: B1 (code review), I1 (code review), C3 (insight). The docstring at
  `identify_potential_levers.py:153` already states "at least 50 characters"; the
  implementation at line 157 checks `< 10`. This is a documented intent mismatch.
- **Impact**: Catches the worst template-lock reviews (a 10–49 char formulaic one-liner
  currently passes). All observed reviews in runs 31–37 are well above 50 chars, so this
  change would not reject any currently-valid run output. It provides a safety net for
  weaker models that might submit very short reviews in future runs.
- **Effort**: Trivial — one-line change: `if len(v) < 50:`.
- **Risk**: Minimal. No run in the analysis set would be newly rejected by this change.

---

### 4. Fix B3: plan_timeout not actually enforced in runner
- **Type**: code fix
- **Evidence**: B3 (code review), `self_improve/runner.py:491–503`. After `future.result(timeout=N)`
  raises `TimeoutError`, the `with ThreadPoolExecutor(...)` block exits by calling
  `shutdown(wait=True)`, which blocks until the inner thread finishes regardless of the recorded
  timeout. A hung Ollama call (which has been observed) blocks the entire runner indefinitely.
- **Impact**: Affects pipeline reliability for all models but is most critical for Ollama, which
  already has a 40% failure rate and may hang on calls. The fix unblocks the calling thread
  after the timeout and allows other plans to proceed.
- **Effort**: Low. After catching `TimeoutError`, add `executor.shutdown(wait=False, cancel_futures=True)`
  (Python 3.9+). Note: the underlying thread continues in the background since Python threads
  cannot be forcibly cancelled, but the calling thread is freed.
- **Risk**: Low. Background thread resource usage is a known limitation of Python threading;
  any LLM HTTP request will eventually time out or complete on its own.

---

### 5. Add anti-template instruction to `review_lever` field description
- **Type**: prompt change
- **Evidence**: N3 (insight), I4 (code review), H2 (insight). Template lock affects runs 34,
  35, 36 with the "The tension between X and Y" opener appearing in most or all reviews.
- **Impact**: Complements direction #2 (example diversification) by targeting the field
  description rather than just the examples. Together they attack template lock from two angles.
  Affects all models and all plans.
- **Effort**: Trivial. Append to `review_lever` field description in `Lever` at
  `identify_potential_levers.py:103–110`:
  > "Do not begin every review with 'The tension between'. Name a concrete, domain-specific
  > failure the options share — a critique that could NOT be transplanted to a different domain."
- **Risk**: Very low. A field description addition is purely additive.

---

## Recommendation

**Fix the PR #346 batch-rejection architecture (Direction #1) first.**

This is the highest-leverage single change because:

1. **Quantified regression**: The PR causes a 35–65% lever count drop (17→6 for gemini,
   17→11 for gpt-4o-mini on hong_kong_game). This is a 2–3× larger regression than any
   other issue in the batch and affects the input diversity for every downstream step.

2. **Code fix benefits all models**: Unlike prompt tweaks (which may only help some models),
   fixing the validator architecture recovers lever counts across all models that currently
   lose batches to enum/length rejection.

3. **The PR's intent is worth keeping**: The `lever_type` enum and `decision_axis` sentence
   are genuinely more useful downstream than the current free-text `lever_classification`
   phrase — when they succeed, the output quality is comparable or better. The problem is
   purely the validation strictness, not the schema design.

**Specific changes required (both in the PR branch's version of `identify_potential_levers.py`):**

**a) `lever_type` normalization validator** (add `mode='before'` validator):
```python
LEVER_TYPE_ALIASES = {
    "operational": "operations",
    "method": "methodology",
    "methods": "methodology",
    "execute": "execution",
    "govern": "governance",
    "disseminate": "dissemination",
}

@field_validator('lever_type', mode='before')
@classmethod
def normalize_lever_type(cls, v):
    if isinstance(v, str):
        normalized = v.strip().lower()
        return LEVER_TYPE_ALIASES.get(normalized, normalized)
    return v
```

**b) `decision_axis` soft validation** — change from a hard reject to a log-and-continue:
```python
@field_validator('decision_axis', mode='after')
@classmethod
def check_decision_axis(cls, v):
    if len(v.strip()) < 20:
        logger.warning(f"decision_axis is short ({len(v)} chars): {v!r}")
        # Do not raise — a short axis is preferable to losing the entire batch
    return v
```

After these changes, re-run gemini and gpt-4o-mini on hong_kong_game and verify lever counts
return to 15+ before merging.

---

## Deferred Items

- **I2** (fix "exactly 3 / no more, no fewer" options description): Low priority. Change to
  "At least 3 options" to match validator behavior. Accurate documentation reduces LLM confusion
  but has no runtime impact.

- **S1** (generated_lever_names not tracked for failed calls): Low priority. A failed call
  means call 3 may regenerate names from call 2, but the downstream deduplication step handles
  exact and near-duplicates. Not worth fixing until diversity becomes measurably worse.

- **S2** (global dispatcher cross-plan contamination in multi-worker mode): Low priority.
  `track_activity.jsonl` is deleted in the finally block, so contamination does not persist.
  Only relevant if per-plan diagnostics are added without the delete.

- **S3** (expected_calls=3 hardcoded in multiple places): Low priority. Risk is low while
  `total_calls = 3` is stable. Refactor when `total_calls` is changed.

- **I5** (partial_recovery fires even on total failure): Low priority quality-of-life fix
  in runner.py. Add `pr.status == "ok"` guard to the condition.

- **Ollama options<3 failures**: Pre-existing issue (run 31: 2/5 plans failed). Consider
  adding a soft prompt reminder in calls 2 and 3 as H3 suggests ("Each option MUST contain
  a full sentence with at least 15 words. Do NOT generate fewer than 3 options."). Deferred
  because Ollama is a weak model and the validator correctly prevents invalid output from
  propagating downstream.

- **Haiku quality for non-fiction plans**: Run 37 (haiku, silo) produced the highest-quality
  levers in the batch. Whether haiku maintains this quality for non-fiction plans
  (sovereign_identity, gta_game) is unconfirmed and worth a dedicated run.

- **Verify run 24–30 events.jsonl**: Confirm which validator (`lever_type` or `decision_axis`)
  is responsible for the batch rejections in the PR branch. This evidence would strengthen the
  fix targeting in Direction #1.
