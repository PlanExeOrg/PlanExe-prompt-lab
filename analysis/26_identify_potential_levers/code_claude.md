# Code Review (claude)

## Bugs Found

### B1 — `min_length=20` too low for `review_lever` validator
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:151–152`

```python
if len(v) < 20:
    raise ValueError(f"review_lever is too short ({len(v)} chars); expected at least 20")
```

The threshold is 20 characters, but "Sensor Data Sharing" (19 chars) is the exact failure mode documented in run 89 (insight negative #3). A 25-char degenerate review like "Weak lever, skip this." would silently pass this check. The old "This lever governs…" template was verbose enough to always exceed 20 chars; without it, llama3.1 can now produce single-phrase reviews that only barely miss (or barely pass) the threshold. A 20-char floor provides almost no protection against degenerate output — a full sentence requires at minimum 40–60 chars.

---

### B2 — Insurance example seeds the secondary template lock
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:107–110` (Pydantic field description) and `identify_potential_levers.py:238` (system prompt section 4)

The three replacement examples introduced by PR #337 include the phrase **"the options neglect"** in the insurance example:

> "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but **the options neglect** that a single hurricane season can correlate all three simultaneously."

And the urban-planning example contains **"the options assume"**:

> "Routing the light-rail extension through the historic district unlocks ridership but triggers Section 106 heritage review; **the options assume** permits will clear on the standard timeline."

Run 89 shows llama3.1 adopted "The options assume/neglect/overlook…" at 76% rate (13/17 reviews) — including near-verbatim copies like "The options assume that the [X] is fixed, neglecting the possibility that it could be a dynamic entity…". This secondary lock almost certainly traces back to "the options assume" and "the options neglect" as copyable subphrases in the new examples. The PR broke one template anchor but embedded two new copyable phrases in the replacements. This is a template leakage vector at the sub-sentence level: the examples themselves contain the seeds of the next lock.

---

### B3 — Global dispatcher cross-contamination under concurrent workers
**File:** `self_improve/runner.py:106–109` and `runner.py:146–148`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path` uses thread-local storage (correct), but `dispatcher` is the global LlamaIndex dispatcher singleton shared across all threads. When `workers > 1`, each thread adds its own `track_activity` handler to the same global list. During the run — outside the lock — the dispatcher fires events from all threads to all active handlers. Thread 1's LLM call events are received by both thread 1's handler (writing to `plan_A/track_activity.jsonl`) and thread 2's handler (writing to `plan_B/track_activity.jsonl`). The per-plan `track_activity.jsonl` files become cross-contaminated with events from other concurrent plans. The `_file_lock` protects add/remove atomicity but does nothing to prevent cross-thread event delivery during execution.

---

## Suspect Patterns

### S1 — `check_option_count` validator docstring references wrong run number
**File:** `identify_potential_levers.py:131–137`

```python
"""Reject levers that don't have exactly 3 options.

Run 89 (llama, hong_kong_game) produced levers with 2 options...
"""
```

The docstring says "Run 89" but the 2-option error occurred in run 82 (before PR #337). Run 89 has the 19-char `review_lever` error on parasomnia. The options-count validator itself is correct, but the embedded evidence reference is wrong. Minor, but will confuse future reviewers.

---

### S2 — `_next_history_counter` bucket arithmetic assumes runs never exceed 99 per bucket
**File:** `self_improve/runner.py:264–280`

```python
bucket_base = int(bucket.name) * 100
idx = int(run_dir.name.split("_")[0])
max_counter = max(max_counter, bucket_base + idx)
```

History runs are named `{counter % 100:02d}_{step_name}` (line 294), so counter 100 maps to bucket `"1"`, entry `"00_…"`. If a bucket contains 100 entries (00–99), the next entry would land in a new bucket. The computation is internally consistent — but the comment in the code says nothing about this, and the two-digit zero-padding (`{counter % 100:02d}`) limits each bucket to 100 slots. As long as runs stay well below 100 per bucket this is fine. Worth a comment to prevent future breakage.

---

### S3 — `LeverCleaned.review` field description is unreachable dead code
**File:** `identify_potential_levers.py:195–211`

`LeverCleaned` is only instantiated by the Python code (line 352–358) — it is never serialized into a schema and passed to an LLM. The verbose `description=` string on the `review` field (which contains the three domain-specific examples) is never seen by any model. PR #337 updated this location as one of the "3 locations", but that update is cosmetically correct yet functionally inert. If the field description is never used for prompting, maintaining it in sync with the live prompt is pure overhead and a future confusion risk (the description may drift from the actual prompt).

---

## Improvement Opportunities

### I1 — Raise `min_length` for `review_lever` to prevent degenerate output
**File:** `identify_potential_levers.py:151`

Change `len(v) < 20` to `len(v) < 50`. A complete critical review (name the tension, identify a weakness) is physically impossible in under 50 characters. The current floor only catches single-word or three-word placeholders. The new threshold catches short labels like "Needs more detail." (18 chars), "Too vague." (10 chars), and the observed "Sensor Data Sharing" (19 chars), while still allowing genuine short reviews.

---

### I2 — Add a positive diversity constraint to `review_lever`
**File:** `identify_potential_levers.py:96–112` and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4

Negative constraints ("do not start with X") create stylistic vacuums that weaker models fill with the next-most-salient pattern. A positive constraint prescribes what to write instead:

> "Each review must address exactly one specific risk not mentioned in the consequences field — choose from: production feasibility, stakeholder conflict, financial viability, technical constraint, or audience reception."

This approach leaves no room for template-lock migration: there is no neutral phrasing vacuum to fill.

---

### I3 — Add "Do NOT open with 'The options assume'" as a third negative constraint
**File:** `identify_potential_levers.py:96–112` and system prompt section 4

Following the same pattern as the existing "Do not use square brackets" constraint, add:

> "Do NOT open with 'The options assume', 'The options neglect', or 'The options overlook' — these are formulaic openers."

This directly addresses the secondary lock observed in run 89. However, as the insight notes (question Q5), adding a second negative constraint may trigger a third shift. I2 (positive constraint) should be preferred; I3 is a cheap additional guard.

---

### I4 — Remove or strip the dead `LeverCleaned.review` field description
**File:** `identify_potential_levers.py:195–211`

Since `LeverCleaned` is never passed to an LLM, the `description=` string on `review` does nothing. Either remove it entirely (and document why `LeverCleaned` has no descriptions), or replace it with a brief human-readable note: `description="Critical review of the lever, copied from Lever.review_lever."`. This prevents the three domain-specific examples from existing in two copies (one live at line 100, one dead at line 199).

---

### I5 — Align `OPTIMIZE_INSTRUCTIONS` with the secondary template-lock migration failure class
**File:** `identify_potential_levers.py:27–73`

The `OPTIMIZE_INSTRUCTIONS` constant does not yet document "template-lock migration" as a known failure class. Add:

> "- Template-lock migration. Replacing a dominant negative example with new examples may shift the model's formulaic output to the next-most-salient pattern in the replacement, rather than eliminating template use entirely. If new examples contain copyable subphrases (e.g., 'the options neglect', 'the options assume'), weaker models will copy those phrases at high rates. Prefer positive diversity constraints over negative example replacement."

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|---|---|
| llama3.1 secondary lock "The options assume/neglect" at 76% (run 89) | **B2**: insurance + urban-planning examples contain "the options neglect" / "the options assume" as copyable subphrases |
| llama3.1 `review_lever is too short (19 chars)` on parasomnia (run 89) | **B1**: `min_length=20` too low; old template incidentally guaranteed verbosity |
| Exact duplicate reviews for items 15 and 17 in run 89 | **B2** (secondary): model exhausted diverse critique framings and fell back on repeated phrase; no structural uniqueness check exists |
| `track_activity.jsonl` cross-contamination in concurrent runs | **B3**: global dispatcher receives events from all threads |
| LeverCleaned.review examples "dead weight" (analysis 25 backlog #4) | **S3**: field description never passed to LLM |
| PR reduced llama3.1 "This lever governs" from 100% → 0% | PR correctly updated both live prompt locations |
| PR broke qwen3 "This lever [verb]" from ~100% → 6% | PR correctly updated both live prompt locations |

---

## PR Review

**PR #337:** "fix: replace generic review_lever examples with domain-specific ones"

### What the PR does
Replaces the single generic example ("This lever governs the tension between centralization and local autonomy") in all three source locations with three domain-specific examples: agriculture (seasonal labor), urban planning (light-rail heritage review), and insurance (catastrophe risk correlation). This was directly recommended by analysis 25.

### Implementation correctness
- **All three locations updated?** Yes: `Lever.review_lever` field description (lines 99–112), `LeverCleaned.review` field description (lines 196–211), and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (lines 234–239). The text is identical across all three locations.
- **Are the new examples domain-specific enough to prevent verbatim copy?** Yes — agriculture, urban planning, and insurance are genuinely non-portable to the software/film/game domains of the test plans. No model in runs 89–95 was observed copying the full example sentences.
- **Does the PR achieve its stated goal?** Yes. llama3.1 "This lever governs" rate: 100% → 0%. qwen3 "This lever [verb]" opener: ~100% → 6%. These are the primary targets.

### Gaps and regressions introduced

1. **Sub-phrase leakage (B2):** The replacement examples contain "the options neglect" (insurance example) and "the options assume" (urban-planning example). llama3.1 adopted "The options assume/neglect/overlook" at 76% in run 89. The PR replaced one copyable opener with examples that carry two copyable verb-phrase seeds. The fix is incomplete: it broke the full-sentence template but seeded a phrase-level template.

2. **`LeverCleaned.review` update is cosmetically correct but functionally inert (S3):** Updating the dead-code field description creates an illusion of completeness. The PR description claims "Updated in all 3 locations" — two of those locations are live (field description that feeds structured LLM output schema, system prompt), while the third (`LeverCleaned`) is never seen by any model. The effective change is two locations, not three.

3. **No compensating protection for the newly exposed `min_length` gap (B1):** Removing the verbose template incidentally removed an accidental length floor. The PR does not raise `min_length` to compensate, leaving a narrow window for degenerate 20–49 char reviews to pass validation.

### Verdict on the PR
The PR is a net positive: primary template locks broken, no success-rate regression, no content quality regression. The implementation matches its stated intent. The gaps (B1, B2) are appropriate scope for a follow-up PR rather than blockers on this one. The `LeverCleaned` update is harmless. **Keep.**

---

## Summary

The current code has one confirmed functional bug that could affect output quality across all models (B1: `min_length=20` insufficient), one structural bug that surfaces in concurrent runs (B3: dispatcher cross-contamination), and one subtle but consequential prompt engineering bug (B2: the replacement examples introduced by PR #337 contain copyable subphrases that directly seeded llama3.1's secondary template lock in run 89).

The highest-priority fix is **B2 + I2**: remove the "the options neglect/assume" subphrases from the examples and add a positive diversity constraint that prescribes what risk category each review must address. This prevents both the original and secondary template locks without creating another stylistic vacuum. The second priority is **B1 + I1**: raise `min_length` to 50 characters. B3 is a correctness issue for concurrent-workers runs and should be fixed in the runner, but it does not affect single-worker runs or the quality of lever output.
