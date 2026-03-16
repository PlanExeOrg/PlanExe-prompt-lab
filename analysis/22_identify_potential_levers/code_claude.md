# Code Review (claude)

## Bugs Found

### B1 — `set_usage_metrics_path` called outside lock (runner.py:107)

**File:** `self_improve/runner.py`, line 107

The comment on lines 97–99 says "we hold a lock while configuring and running to avoid
cross-thread interference," but the actual call:

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # line 107

with _file_lock:                                                   # line 109
    dispatcher.add_event_handler(track_activity)                   # line 110
```

`set_usage_metrics_path` modifies **global** state but is called **outside** the lock.
When `workers > 1`, a second thread can overwrite the path set by a first thread between
lines 107 and 110. Each plan's LLM calls then write usage metrics to whichever path was
last set, not necessarily their own plan's directory.

The `finally` block (line 150) calls `set_usage_metrics_path(None)`, but with concurrent
threads this will prematurely nullify a sibling thread's path while that thread is
mid-execution.

---

### B2 — Cross-thread `TrackActivity` handler contamination (runner.py:109–117)

**File:** `self_improve/runner.py`, lines 109–117

`dispatcher.add_event_handler(track_activity)` adds a handler to a **global** dispatcher.
When `workers > 1`, all registered handlers remain active simultaneously. LLM events fired
during plan A's execution will be dispatched to plan B's `TrackActivity` handler (and vice
versa), because the dispatcher calls every registered handler regardless of which thread
triggered the event.

The result: each plan's `track_activity.jsonl` will contain interleaved events from
unrelated plans. The `finally` block removes the handler on completion, but the window
between add and remove is the entire duration of the LLM calls.

---

## Suspect Patterns

### S1 — All-or-nothing call failure when one lever has a wrong option count (identify_potential_levers.py:115–126)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 115–126

`check_option_count` raises `ValueError` if any `Lever.options` does not have exactly 3
items. Pydantic propagates this as a validation error on the whole `DocumentDetails`
object, which causes `llm.as_structured_llm(DocumentDetails).chat(...)` to throw. This
discards all levers from that call — even the majority that had correct option counts.

The `DocumentDetails.levers` field also has `min_length=5` (line 153); if a model returns
4 levers, the entire response is rejected. There is no lever-level partial recovery.

---

### S2 — `LeverCleaned.review` description is stale (identify_potential_levers.py:186–194)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 186–194

`LeverCleaned.review` still carries the old "Two sentences. First sentence names the core
tension…" description and the "Controls…/Weakness:" example. `LeverCleaned` is created by
mapping from `Lever` objects (line 345), not by LLM generation, so this does not affect
output directly. However, if anyone reads the schema or generates a `LeverCleaned` object
through the API, the schema description contradicts whatever the `Lever.review_lever`
description says after the PR.

---

### S3 — `consequences` cross-reference to "Controls/Weakness:" format will become stale (identify_potential_levers.py:83–84)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 83–84
(and mirrored in `LeverCleaned.consequences` at lines 177–178)

The `consequences` field description says:

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
"those belong exclusively in review_lever. "
```

This prohibition references the specific English markers that appear in the **old**
`review_lever` example ("Controls centralization vs. local autonomy. Weakness: …").
If PR #316 replaces the `review_lever` example with a flowing single-sentence format that
no longer uses "Controls" or "Weakness:", this cross-reference becomes stale and confusing:
models reading the `consequences` description see markers ("Controls … vs.", "Weakness:")
that no longer match the actual `review_lever` format they are expected to produce.

---

## Improvement Opportunities

### I1 — System prompt section 4 out of sync with field description (identify_potential_levers.py:215–220)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 215–220

The system prompt section 4 still reads:

```
- For `review_lever` (one field, two sentences):
  First sentence names the core tension. Second sentence identifies a weakness.
  Example: "Controls centralization vs. local autonomy. Weakness: The options fail to account for transition costs."
```

The field description (lines 92–100) and the system prompt must agree. If PR #316 updates
only the Pydantic field description and not this system prompt block, models receive
contradictory guidance: the field schema says one format, the system prompt says another.
Weaker models often weight the system prompt over field descriptions.

---

### I2 — `check_review_format` validator does not enforce content structure (identify_potential_levers.py:128–143)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 128–143

The validator enforces only:
- Minimum length ≥ 20 characters
- No square-bracket placeholders

A value like `"This option is fine and passes."` (30 chars, no brackets) would pass even
though it contains neither a tension nor a weakness/critique. The structural intent of the
field is not verified at all. This means a model that misunderstands the format still
produces a `review_lever` that passes validation and silently ships as useless output.

A lightweight improvement: require at least one sentence boundary (`. `) to ensure the
value is at least two clauses long, or check for a minimum word count (e.g. ≥ 8 words
covering both the tension and critique aspects).

---

### I3 — New example is still English-specific (identify_potential_levers.py:92–100)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 92–100

The current example ("Controls centralization vs. local autonomy. Weakness: The options
fail to account for transition costs.") uses English-specific phrasing. The `OPTIMIZE_INSTRUCTIONS`
block (lines 61–68) explicitly warns about this. The PR's proposed new example ("This lever
governs the tension between centralization and local autonomy, but the options overlook
transition costs.") is still in English and still names domain concepts ("centralization",
"local autonomy") that may push models to respond in English even when the user prompt is
in Chinese, Arabic, German, etc.

A domain-neutral placeholder example (e.g. using `[TENSION]` / `[WEAKNESS]`) would be
language-agnostic. Alternatively, the description could omit the English example and rely
on the structural description alone, with a note that the response language should match
the project context language.

---

### I4 — Duplicate deduplication is exact-match only (identify_potential_levers.py:330–347)

**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 330–347

`seen_names` uses a case-sensitive exact string match. "Market Strategy" and "market
strategy" would both survive this guard and appear as two distinct levers in the output.
Near-duplicate detection is delegated to `DeduplicateLevers` downstream (which is correct
per `OPTIMIZE_INSTRUCTIONS`), but obvious case variants could be normalised here at low
cost (e.g. `lever.name.lower()` as the set key).

---

## Trace to Insight Findings

The insight files both timed out (600 s limit exceeded), so there are no specific
observation-to-code mappings available. Based on the code analysis:

- **B1/B2 (multi-worker race conditions)** would manifest as corrupted or missing usage
  metrics and cross-plan tracking data when `workers > 1`. These are silent data-quality
  bugs; they would not cause timeouts but would corrupt observability output.

- **S1 (all-or-nothing call failure)** is the most likely cause of repeated LLM retries
  or hung runs. If `check_option_count` rejects an entire `DocumentDetails` for one
  bad lever, the executor may retry the whole structured call (depending on the
  `llm.as_structured_llm` retry behavior). Repeated failures exhaust the retry budget and
  can cause the overall run to time out, which is consistent with the 600 s timeouts
  reported in both insight files.

- **I1 (system-prompt/field-description mismatch)** would produce inconsistent
  `review_lever` formats across calls — some levers using the two-sentence format, others
  using free-form text — which is a quality regression that would surface in the
  synthesis/assessment phases.

---

## PR Review

### PR #316 — "fix: replace two-bullet review_lever prompt with single flowing example"

**What the PR claims to do:**
Replace the "First sentence… / Second sentence…" decomposition in `review_lever` field
description and system prompt with a single flowing example ("This lever governs the
tension between centralization and local autonomy, but the options overlook transition
costs.") so that weaker models (llama3.1) cannot interpret the format as two alternative
outputs.

**Assessment: Partially correct, with meaningful gaps.**

#### What the PR gets right

The diagnosis is accurate. The current field description at lines 94–95:

```python
"Two sentences. First sentence names the core tension this lever "
"controls. Second sentence identifies a weakness the options miss. "
```

explicitly labels the two-sentence requirement as a numbered decomposition. Weaker models
may read "First sentence" and "Second sentence" as headers for two separate choices rather
than as sequential parts of a single required response. Replacing this with a single
imitable example is a sound strategy used in prompt engineering ("show, don't tell").

#### Gap 1 — System prompt section 4 is NOT updated (identify_potential_levers.py:215–220)

The `Lever.review_lever` Pydantic field is one instruction surface; the system prompt is
another. **Both must be changed together.** Section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`
(lines 215–220) still reads:

```
- For `review_lever` (one field, two sentences):
  First sentence names the core tension. Second sentence identifies a weakness.
  Example: "Controls centralization vs. local autonomy. Weakness: ..."
```

If the PR updates only the field description, llama3.1 and other models that weight the
system prompt heavily will still receive the old two-sentence decomposition, and the fix
will have no effect on those models. This is the most critical gap: the bug the PR
diagnoses lives in the system prompt as much as in the field description.

#### Gap 2 — `LeverCleaned.review` is NOT updated (identify_potential_levers.py:186–194)

`LeverCleaned.review` carries an identical "Two sentences…" description (lines 188–193)
with the old example. While `LeverCleaned` is not serialised to the LLM schema during
generation (it's a post-processing container), any tooling that introspects the Pydantic
schema will see inconsistent documentation between `Lever.review_lever` and
`LeverCleaned.review`.

#### Gap 3 — `consequences` cross-reference becomes stale (identify_potential_levers.py:83–84)

The `consequences` field description prohibits `'Controls ... vs.'` and `'Weakness:'`
text (lines 83–84). These are format markers from the **old** `review_lever` example. Once
the new example no longer uses those markers, the prohibition in `consequences` references
ghost markers — it remains technically correct (models should not put review text in
consequences) but the listed examples no longer match what `review_lever` actually
produces. The instruction should be updated to reference the new format's characteristic
phrasing instead.

#### Gap 4 — New example is still English-centric

The proposed replacement example is English-only. `OPTIMIZE_INSTRUCTIONS` lines 61–68
explicitly flags English-specific validation as a known problem. The fix addresses the
structural parsing problem but does not address the language-mismatch problem that
`OPTIMIZE_INSTRUCTIONS` documents. Consider whether the example should be
language-neutral or accompanied by a note like "respond in the same language as the
project context."

#### Summary of PR verdict

| Concern | Status |
|---|---|
| Fixes weaker-model format confusion in field description | ✅ Correct fix |
| System prompt section 4 updated to match | ❌ Gap — must be updated together |
| `LeverCleaned.review` updated for consistency | ❌ Gap — documentation inconsistency |
| `consequences` cross-reference updated | ❌ Gap — will become stale |
| Language-agnostic example | ⚠️ Not addressed |
| `check_review_format` validator compatible with new format | ✅ Validator still works |

The PR is a step in the right direction but is **incomplete**. Without updating the system
prompt section 4 in the same commit, weaker models that rely on the system prompt (not
just the Pydantic schema) will continue to produce the two-sentence decomposition, and
call-1 validation failures will persist for those models.

---

## Summary

The most critical actionable issues are:

1. **(B1/B2)** Thread safety in `runner.py` — `set_usage_metrics_path` and dispatcher
   event handlers are both global state. In multi-worker mode they race, corrupting usage
   metrics and cross-contaminating tracking data between plans.

2. **(S1)** All-or-nothing Pydantic validation — a single lever with the wrong option
   count (or a response with fewer than 5 levers) discards the entire call's levers. This
   is a likely contributor to the timeout behaviour seen in the insight files, since
   repeated structured-LLM retries on bad responses can exhaust the time budget.

3. **(I1 / PR gap 1)** System prompt section 4 must be updated in the same commit as the
   `Lever.review_lever` field description. The PR is incomplete without this change.

4. **(I2)** The `check_review_format` validator accepts any 20-char string, offering no
   structural enforcement of the tension+weakness content requirement introduced by the
   field description. The validator and the description have diverged.
