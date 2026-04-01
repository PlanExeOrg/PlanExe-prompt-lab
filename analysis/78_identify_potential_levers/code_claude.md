# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: Remove template-lock anchor from review_lever (PR #484)

---

## Bugs Found

### B1 — `_run_levers` warning threshold contradicts its own comment
**File**: `self_improve/runner.py:131–136`

```python
actual_calls = len(result.responses)
# A 2-call success is normal for models that produce 8+ levers per call.
# Only warn if we got fewer responses than expected for 15 levers (~3 calls at 5-7 levers each).
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

The comment explicitly states "A 2-call success is normal for models that produce 8+ levers per
call" but the condition `actual_calls < 3` fires for `actual_calls=2`. A normal, healthy 2-call
run (e.g., model yields 8 on call 1 and 9 on call 2, total=17 ≥ 15) logs a warning that says
"partial recovery", which is incorrect. The log message will mislead operators into investigating
runs that completed successfully.

### B2 — Inconsistent `partial_recovery` threshold between warning and event
**Files**: `self_improve/runner.py:131–140` (warning) vs. `runner.py:577–583` (event)

`_run_levers` logs a WARNING at `actual_calls < 3` (fires for 1 or 2 calls).
`_run_plan_task` emits a `partial_recovery` event at `calls_succeeded < 2` (fires only for 1 call).

For a 2-call success the warning fires but no `partial_recovery` event is written to
`events.jsonl`. The insight file (P2) documents that previous runs emitted
`partial_recovery` events with `calls_succeeded=2`, which implies the event threshold was
previously `< 3`. Lowering it to `< 2` silently dropped 2-call partial-recovery detection.

If a model fails its third call and exits with 2 calls / 10–14 levers (below the 15-lever
minimum), that run will log a misleading "partial recovery" warning but emit no event — making
it invisible to downstream analysis scripts that scan `events.jsonl`.

---

## Suspect Patterns

### S1 — English-specific prohibitions in `consequences` field description
**File**: `identify_potential_levers.py:117–118`

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
```

This embeds English keyword examples ("Controls ... vs.", "Weakness:") directly in the Pydantic
field description that is read by the LLM as part of the schema. OPTIMIZE_INSTRUCTIONS line 61–68
warns that English-only substring checks must not be used in validators — but the same hazard
applies to prohibitions in field descriptions: a model responding in German or Japanese cannot
map "Controls ... vs." to the equivalent pattern in its output language, and the instruction
becomes incoherent. This is not a validator (so it won't *reject* output), but it may confuse
non-English models into copying the English prohibition text.

### S2 — `execute_function` closure over `messages_snapshot` inside loop
**File**: `identify_potential_levers.py:315–325`

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

`execute_function` closes over `messages_snapshot` by reference. Because `execute_function` is
called synchronously within the same loop iteration before the next iteration reassigns
`messages_snapshot`, the current behavior is correct. However if `LLMExecutor.run()` ever
switches to lazy or async invocation, all calls would share the last iteration's
`messages_snapshot`. Capturing the value explicitly (e.g., default argument
`def execute_function(llm, _snap=messages_snapshot)`) would make the intent safe against that
change.

---

## Improvement Opportunities

### I1 — `check_review_format` has no max-length cap
**File**: `identify_potential_levers.py:159–175`

The validator enforces a minimum of 10 characters but no maximum. The system prompt specifies
"one sentence, 20–40 words", and OPTIMIZE_INSTRUCTIONS line 83–85 explicitly recommends
"enforce a length cap in the system prompt to prevent output overflow." Haiku currently averages
281 chars (~56 words) per review — 40% above the stated 40-word target. Adding a max-length
check (e.g., reject if `len(v) > 350` chars) would give the model retry-level feedback and
signal the bound to analysis tooling, at no risk of breaking well-behaved models.

### I2 — Section 4 examples are at the upper end of the target word range
**File**: `identify_potential_levers.py:247–249`

The three review examples are 35–40 words each — sitting at the top of the 20–40 word target.
Per OPTIMIZE_INSTRUCTIONS "Verbosity amplification" (line 83): "Models mirror example verbosity."
The insight analysis (N2) shows haiku averaging 281 chars (~56 words), likely anchored above the
cap by these examples. Shortening the examples to 20–28 words would pull haiku toward the
baseline (152 chars) without removing example diversity, and should have no effect on stronger
models that already produce near-baseline lengths.

### I3 — Section 4 heading "Validation Protocols" is misleading
**File**: `identify_potential_levers.py:243–244`

```
4. **Validation Protocols**
   - For `review_lever`:
     A one-sentence critical review (20–40 words).
     Examples:
```

This section provides *format examples*, not validation rules. Calling it "Validation Protocols"
may cause models — particularly instruction-tuned models that treat headings as intent signals —
to treat the examples as correctness criteria to check against rather than as stylistic anchors
to draw variety from. Renaming to "Format Examples" or "Output Examples" would align the
heading with the actual content.

### I4 — `expected_calls=3` hardcoded in `partial_recovery` event payload
**File**: `self_improve/runner.py:582–583`

```python
_emit_event(events_path, "partial_recovery",
            plan_name=plan_name,
            calls_succeeded=pr.calls_succeeded,
            expected_calls=3)
```

`expected_calls=3` is hardcoded but reflects the historical baseline for models that produce
5–7 levers per call. Models that naturally complete in 2 calls (8+ levers per call, which is
described in a comment as "normal") would misrepresent the expectation if a partial_recovery
event were ever emitted for them. The value should either be derived from `min_levers / avg_levers`
or removed from the payload, since it is misleading for fast models.

---

## Trace to Insight Findings

| Code issue | Insight finding |
|---|---|
| B1 — `actual_calls < 3` warning fires on normal 2-call runs | N3 (run 54 timeouts) — not directly related, but the noisy warning makes it harder to distinguish real failures from normal fast completions in log output |
| B2 — event threshold `< 2` vs. warning threshold `< 3` | P2 — the insight reports `calls_succeeded=2` events in the *before* runs; those events would NOT be emitted by the current code, making before/after comparisons of partial_recovery counts unreliable if the threshold changed mid-experiment |
| S1 — English prohibitions in field description | Not directly linked to a PR #484 finding, but touches the same fragile-English-only concern in OPTIMIZE_INSTRUCTIONS (line 61–68) |
| I1 — no max-length validator | N2 — haiku field lengths remain 1.9–2.0× baseline; a hard cap would convert overlong reviews from silent pass-through to retryable validation failures |
| I2 — examples at upper word-count bound | N2 — "The verbosity likely mirrors the three long, domain-rich examples in section 4" (insight_claude.md); shorter examples are the targeted fix recommended by OPTIMIZE_INSTRUCTIONS line 83–85 |
| I3 — "Validation Protocols" heading | No direct regression observed; stylistic risk for future models |
| I4 — `expected_calls=3` hardcoded | P2 — haiku's `calls_succeeded=2` events in before-runs carried `expected_calls=3`, which framed a 2-call run as falling one short of expected; this framing is incorrect for fast models |

---

## PR Review

### What was changed

PR #484 removes the phrase `"the specific gap the three options leave unaddressed"` from:
1. `review_lever` Pydantic field description (line 127) — the phrase was the structural anchor
2. System prompt section 4 preamble (line 244) — removed from the sentence preceding the examples

### Does the implementation match the intent?

Yes. The current field description (lines 125–131) now reads:

> "Critical review of this lever (one sentence, 20–40 words). See system prompt section 4 for
> examples. Do not use square brackets or placeholder text."

No structural phrase remains that models can latch onto as a sentence template. Section 4 now
goes directly from the format spec to the three domain-specific examples, none of which share a
grammatical pattern with "All/None of the three options…".

### Are the right locations changed?

Both locations documented in the PR description are addressed. The field description and the
system prompt preamble were the two points of injection for the template phrase.

### Edge cases and gaps

None identified. The three examples in section 4 are domain-distinct (agribusiness, clinical
trials, catastrophe reinsurance) and do not share reusable transitional phrases. The fix aligns
exactly with the OPTIMIZE_INSTRUCTIONS "Field-description template lock" entry (lines 86–92) and
the "Template-lock migration" guidance (lines 73–82).

### Could the change introduce new problems?

No regressions are present. The insight confirms 0 template-lock instances across all 7 models
after the PR. The validator (`check_review_format`) is unchanged and structural-only (no
English-keyword checks added). The only residual haiku quality issues (N1 verbosity, N2
fabricated numbers) predate this PR and are already tracked in OPTIMIZE_INSTRUCTIONS.

### Verdict on the PR

**KEEP.** The change is minimal (two lines removed from two locations), precisely targeted at the
documented failure mode, and delivers a complete fix with zero regressions. The OPTIMIZE_INSTRUCTIONS
documentation base already contains the lesson this PR implements.

---

## Summary

**B1** and **B2** are the only functional bugs: the partial-recovery warning in `_run_levers` fires
for 2-call completions that the code itself labels as normal, and the event-emission threshold
in `_run_plan_task` does not match the warning threshold. This means 2-call partial runs generate
noisy log warnings but no `events.jsonl` entry, making them invisible to analysis scripts.

**S1** (English prohibitions in field description) is a latent multilingual hazard consistent with
the OPTIMIZE_INSTRUCTIONS concern about fragile English-only checks. It does not affect current
runs (all baseline plans appear to be English) but should be addressed before PlanExe is used on
non-English inputs.

**I1** (no max-length cap on `check_review_format`) and **I2** (examples at upper word-count
bound) are the most actionable improvements for the documented haiku verbosity problem (N2). They
are independent of PR #484 and warrant a follow-up iteration.

PR #484 itself is correct, complete, and well-scoped.
