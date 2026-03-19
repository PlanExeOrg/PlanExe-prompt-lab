# Code Review (claude)

Source files reviewed:
- `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `PlanExe/self_improve/runner.py`

PR under evaluation: #358 — "fix: remove 'core tension' template lock from field description"

---

## Bugs Found

**B1 — Stale `LeverCleaned.review` field description**
File: `identify_potential_levers.py:212`

```python
review: str = Field(
    description="A short critical review — names the core tension, then identifies a weakness the options miss."
)
```

The PR updated `Lever.review_lever` (the prompt-facing field, line 116–124) but left this description
unchanged. At runtime this is harmless — the code comment on lines 208–210 confirms `LeverCleaned` is
never serialized to an LLM. However, the description now contradicts the production field, says exactly
what the PR was meant to eliminate ("names the core tension"), and is a copy-paste trap for any future
maintainer who migrates `LeverCleaned` into a prompt-facing context or adds a new prompt field by
referencing existing descriptions.

Severity: code hygiene (no runtime impact), but directly relevant to the PR's stated goal.

---

**B2 — Wrong model name in `check_option_count` docstring**
File: `identify_potential_levers.py:143–146`

```python
"""Reject levers with fewer than 3 options.

Run 82 (llama, gta_game) produced levers with 2 options that
silently passed validation…
"""
```

Per the run mapping in the insight file, run 82 is `openai-gpt-5-nano`, not `llama`. Run 80 is
`ollama-llama3.1`. The comment misattributes the root cause to the wrong model, which could mislead
future debugging (e.g. someone might disable the validator specifically for llama when gpt-5-nano is
the model that needs watching).

Severity: misleading documentation only; no runtime impact.

---

## Suspect Patterns

**S1 — Secondary template lock introduced by "three options" in field description**
File: `identify_potential_levers.py:116–124`

```python
review_lever: str = Field(
    description=(
        "A short critical review: identify the primary trade-off "
        "this lever introduces, then state the specific gap the "
        "three options leave unaddressed. "
        ...
    )
)
```

The phrase "the three options leave unaddressed" is a structural cue identical in mechanism to the
original "name the core tension" that PR #358 removed. The insight file confirms that haiku (run 93)
echoes this phrase as "none of the three options address…" in ~85% of reviews (17/20 in hong_kong_game).
This is documented in OPTIMIZE_INSTRUCTIONS lines 86–92 ("Field-description template lock") but the PR
simultaneously adds this guidance AND introduces a new instance of the same failure mode.

The phrase "three options" explicitly references a structural property of the output format. Models
parse it as a template instruction ("my output must mention the three options") and mirror it literally.
A description that says what the field should CONTAIN without referencing the schema structure avoids
this.

The `OPTIMIZE_INSTRUCTIONS` entry (lines 73–82, "Template-lock migration") predicts exactly this
outcome: "weaker models shift to copying subphrases within the new examples… Each example must name a
domain-specific mechanism or constraint directly rather than referencing 'the options' as grammatical
subject." The field description breaks this rule by making "the three options" the grammatical subject
of its guiding clause.

Severity: confirmed quality regression for haiku; likely affects other small models too.

---

**S2 — `partial_recovery` emitted for normal over-generating behavior**
File: `runner.py:120–123` and `runner.py:518–523`

```python
# runner.py:120-123
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")

# runner.py:518-523
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

The step-gate exits when `len(generated_lever_names) >= min_levers` (15). A model producing 8–10
levers per call reaches 15 after 2 calls and exits cleanly. The `partial_recovery` event fires for any
run with `calls_succeeded < 3`, which includes this normal over-generation path. The insight file
records 2 haiku `partial_recovery` events (run 93, gta_game 2/3 and silo 2/3) and notes "The
step-gate logic exits early when enough levers are collected, producing 2/3 rather than 3/3 calls.
This is operational but reduces the diversity of generated levers."

The comment at lines 116–119 acknowledges this ("A 2-call success is normal for models that produce
8+ levers per call"), yet the code still emits `partial_recovery` — polluting analysis metrics with
false quality signals. Analysis tools that count `partial_recovery` events will conflate genuine
failures (call 1 schema error, call 2 exit) with healthy over-generation (2 calls × 8+ levers = 15+).

`expected_calls=3` on line 523 is also hardcoded. If `min_levers` changes from 15, or if the expected
levers-per-call range changes, this constant silently drifts out of sync.

---

**S3 — Shared `dispatcher` across parallel plan threads**
File: `runner.py:190–194` and `runner.py:220–222`

```python
dispatcher = get_dispatcher()

with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`get_dispatcher()` returns a module-level singleton. When `workers > 1`, multiple plan threads each
add their own `TrackActivity` handler to the same dispatcher. All handlers receive all events from all
threads — so plan A's LLM events may be captured in plan B's activity log. The `_file_lock` serializes
the add/remove calls but does not isolate event delivery between threads during execution.

`set_usage_metrics_path` uses thread-local storage (per comment), so usage_metrics.jsonl is correctly
isolated. But `TrackActivity` dispatched via the shared dispatcher is not thread-isolated in the same
way. This may explain why `track_activity_path.unlink(missing_ok=True)` is called at line 223 (the
file might be corrupted by cross-thread events, so it's discarded rather than retained).

---

**S4 — `dispatcher.event_handlers.remove` in finally block can raise `ValueError`**
File: `runner.py:220–222`

```python
finally:
    with _file_lock:
        set_usage_metrics_path(None)
        dispatcher.event_handlers.remove(track_activity)
```

If `dispatcher.add_event_handler(track_activity)` raises inside the setup `with _file_lock:` block,
`track_activity` was never added to `event_handlers`. The `finally` block then calls `.remove()` on a
list that doesn't contain the element, raising `ValueError`. This secondary exception replaces the
original exception in the call stack, making the root cause harder to diagnose. A `try/except
ValueError` guard (or checking membership first) would prevent this masking.

---

## Improvement Opportunities

**I1 — Rewrite `review_lever` field description to avoid structural cues**
File: `identify_potential_levers.py:116–124`

The field description should describe what content to put in the field, not how to structure a
sentence around the schema. Replace the phrase "state the specific gap the three options leave
unaddressed" with something that forces domain-specific content without naming "the options" as a
subject. For example:

> "A short critical review: identify the primary trade-off this lever introduces, then name a
> real-world constraint or risk that all three strategies collectively sidestep — expressed in terms
> specific to this project's domain, not as a generic 'the options fail to address X' statement."

This preserves the intent (find the gap) while breaking the subject-verb template "none of the three
options address…". It also aligns with OPTIMIZE_INSTRUCTIONS lines 73–82 ("Each example must name a
domain-specific mechanism or constraint directly rather than referencing 'the options' as grammatical
subject").

---

**I2 — Distinguish `partial_recovery` from step-gate early exit**
File: `runner.py:118–123` and `runner.py:517–524`

Emit separate event types for the two different `< 3 calls` scenarios:
1. **`early_exit`**: `len(generated_lever_names) >= min_levers` after 2 calls (over-generation, healthy)
2. **`partial_recovery`**: at least one call failed with an error and the remaining calls succeeded

Currently both cases emit `partial_recovery`. The step-gate result is available in `IdentifyPotentialLevers`
(it could return a `stop_reason` field), or the caller can detect it by comparing
`sum(len(r.levers) for r in result.responses)` against `min_levers`.

---

**I3 — Update `LeverCleaned.review` field description**
File: `identify_potential_levers.py:211–213`

Update the stale description to match the current production field wording so that the two classes
stay in sync:

```python
review: str = Field(
    description=(
        "A short critical review: identifies the primary trade-off this lever "
        "introduces and a real-world constraint that all three strategies collectively sidestep."
    )
)
```

No runtime impact, but closes the copy-paste trap identified in B1.

---

**I4 — Add structural variety to Section 4 examples**
File: `identify_potential_levers.py:237–241`

Two of the three review examples use the "X, but Y" adversative connector:
- Example 1: "stabilizes harvest quality, **but** the idle-wage burden…"
- Example 3: "reduces expected annual loss on paper, **but** a single regional hurricane…"

Example 2 uses "so" (cause-effect). The insight file's H2 hypothesis notes that the X-but-Y structure
"maps naturally to 'All three options do X, but none address Y'." Adding a fourth example that uses a
conditional or sequential structure (e.g., "If X occurs, then Y follows, yet Z…") would give models a
non-adversative pattern to draw from.

---

**I5 — Fix stale run number in `check_option_count` docstring**
File: `identify_potential_levers.py:143`

Change "Run 82 (llama, gta_game)" to "Run 80 (llama3.1, gta_game)" per the actual run mapping.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Explanation |
|---|---|---|
| "None/All three options" secondary lock at 85% (Negative #1) | `identify_potential_levers.py:120` — "state the specific gap the **three options** leave unaddressed" | Field description uses "the three options" as grammatical subject; models echo it verbatim as "none of the three options address…" (S1 above) |
| Review lengths still 2.5–4× above baseline (Negative #2) | `identify_potential_levers.py:251` — "one sentence (20–40 words)" | The 40-word upper bound is generous; haiku reviews averaging ~42 words are technically within the range but still 2.5× the ~17-word baseline |
| Haiku partial_recovery events 2/15 (Negative #3) | `runner.py:341–343` (step-gate) + `runner.py:519` (threshold) | Step-gate exits at 15 levers after 2 calls when haiku over-generates; `partial_recovery` fires because threshold is hardcoded at `< 3 calls` regardless of lever count (S2 above) |
| `LeverCleaned.review` stale description (Evidence Notes) | `identify_potential_levers.py:212` | Confirmed: description still says "names the core tension" — PR missed this field (B1 above) |
| "Tension" opener lock fixed at 0% (Positive #1, #2) | `identify_potential_levers.py:118` — removed "name the core tension" | PR's primary change worked; field description no longer uses the structural cue |
| No LLMChatErrors in after runs (Positive #5) | `identify_potential_levers.py:329` — retry loop, `check_review_format` validator | 10-char minimum and no-brackets check are structurally sound; haiku's improved success rate (+13.4pp) likely aided by shorter required output ("one sentence") reducing truncation risk |

---

## PR Review

### What the PR changes

1. `Lever.review_lever` field description (line 116–124): "name the core tension, then identify a
   weakness" → "identify the primary trade-off… then state the specific gap the three options leave
   unaddressed"
2. System prompt Section 4 header (line 236): same rewrite as field description
3. System prompt Section 6 (line 251): "under 2 sentences (aim for 20–40 words)" → "one sentence
   (20–40 words)"
4. `OPTIMIZE_INSTRUCTIONS` (lines 69–92): added "Template-lock migration" and "Field-description
   template lock" entries

### Does the implementation match the intent?

**Primary goal (remove "core tension" cue): Yes, fully achieved.**
The field description no longer contains the phrase "core tension" or any synonym. Run 93 confirms 0/20
haiku reviews open with "The tension is between…" in hong_kong_game. The fix is causally clean and
verified.

**Unintended consequence: introduces a new field-description template lock.**
The replacement phrase "state the specific gap the **three options** leave unaddressed" contains
"three options" as a grammatical subject — exactly the mechanism OPTIMIZE_INSTRUCTIONS warns against
(lines 73–82: "Each example must name a domain-specific mechanism or constraint directly rather than
referencing 'the options' as grammatical subject"). The PR added this warning to OPTIMIZE_INSTRUCTIONS
but the field description it introduces violates it.

Run 93 shows the result: 85% of haiku hong_kong_game reviews end with "none of the three options
address…". This is a weaker lock than the original (subject/content still varies; only the predicate
is templated), but it follows the same mechanism and is already the documented next failure to fix.

**Section 6 "one sentence": partially effective.**
Haiku silo reviews dropped from ~50 words average to ~42 words — within the 20–40 word range at the
lower end, but some reviews still reach 58 words. The change from "under 2 sentences" to "one sentence"
is an improvement but insufficient to bring reviews to baseline length (~17 words).

**`OPTIMIZE_INSTRUCTIONS` update: accurate and useful.**
The two new entries ("Template-lock migration" and "Field-description template lock") correctly
document the failure mode and provide actionable guidance. They are consistent with the observed
behavior and will help future iterations. Note that the PR adds documentation of the exact problem it
then partially reintroduces — a detail worth flagging in the next iteration PR message.

### Edge cases and gaps

- The PR does not update `LeverCleaned.review` (line 212), leaving it with the old "names the core
  tension" wording. This is the B1 bug above.
- The Section 4 examples are unchanged. They are good (domain-specific, non-"tension" openers), but
  two of three use "but" as the adversative connector, which may contribute to the X-but-Y pattern in
  haiku outputs alongside the field description cue.
- The "three options" phrase also appears in `Lever.options` field description (lines 112–115:
  "Exactly 3 options for this lever. No more, no fewer.") and `DocumentDetails.levers` description
  (line 181: "Propose 5 to 7 levers."), but those are in non-review fields and are structural
  constraints, not review-content cues. Only the `review_lever` description's use of "three options"
  as a review-content subject is the template lock source.

### Verdict on the PR

**Correct fix, incomplete execution.** The primary bug is definitively fixed. The PR should be kept.
The secondary template lock introduced by "the three options leave unaddressed" is the most important
issue to address in the next iteration (confirmed I1 above). Separately, `LeverCleaned.review`
should be updated for code hygiene (B1 above).

---

## Summary

| ID | Type | Severity | Description | File:Line |
|----|------|----------|-------------|-----------|
| B1 | Bug (hygiene) | Low | `LeverCleaned.review` description still says "names the core tension" — stale after PR #358 | `identify_potential_levers.py:212` |
| B2 | Bug (comment) | Low | `check_option_count` docstring says "Run 82 (llama, gta_game)" — run 82 is gpt-5-nano, not llama | `identify_potential_levers.py:143` |
| S1 | Suspect | High | `review_lever` field description uses "the three options leave unaddressed" as subject — same template-lock mechanism as the original bug, confirmed at 85% haiku rate | `identify_potential_levers.py:120` |
| S2 | Suspect | Medium | `partial_recovery` event fires for step-gate early exits (healthy over-generation) and for genuine failures — conflates two different signals in analysis metrics | `runner.py:120`, `runner.py:519` |
| S3 | Suspect | Low | Shared `dispatcher` across parallel plan threads — `TrackActivity` handlers not thread-isolated, may capture cross-plan events | `runner.py:190–222` |
| S4 | Suspect | Low | `dispatcher.event_handlers.remove` in finally block raises `ValueError` if handler was never added — masks original exception | `runner.py:221` |
| I1 | Improvement | High | Rewrite `review_lever` field description to avoid "three options" as grammatical subject | `identify_potential_levers.py:116–124` |
| I2 | Improvement | Medium | Differentiate `partial_recovery` (call failure) from `early_exit` (step-gate over-generation) | `runner.py:118–123`, `517–524` |
| I3 | Improvement | Low | Update `LeverCleaned.review` field description to match current production wording | `identify_potential_levers.py:211–213` |
| I4 | Improvement | Low | Add a fourth Section 4 example with non-adversative structure (not X-but-Y) | `identify_potential_levers.py:237–241` |
| I5 | Improvement | Low | Fix stale run number in `check_option_count` docstring | `identify_potential_levers.py:143` |

**Top priority for next iteration:** I1 — the "three options leave unaddressed" phrase in the
`review_lever` field description is the confirmed source of the new secondary template lock. It should
be the primary target of the next PR.
