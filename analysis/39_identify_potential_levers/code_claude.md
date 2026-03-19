# Code Review (claude)

## Bugs Found

**B1: Dual "core tension" trigger causes template lock**

- `identify_potential_levers.py:111` — `Lever.review_lever` field description says "name the core tension"
- `identify_potential_levers.py:228` — System prompt section 4 validation protocol also says "name the core tension"

The phrase appears twice in paths that are both serialized to the LLM: once in the Pydantic structured-output schema (the field description), and once in the system prompt instruction. Models read both before generating; seeing "name the core tension" in both places primes them to literally start every review with "The tension is…" or "The core tension is…". The three examples in section 4 (lines 229–232) do NOT open with that phrase — they use domain-specific openers — but the instruction text overrides the examples' implicit structural signal for weaker models.

This is the confirmed root cause of the near-100% "tension" template lock observed in runs 80 and 86. It predates PR #357 and was not addressed by the PR.

**B2: `check_option_count` does not reject field-name leakage strings**

- `identify_potential_levers.py:130–142`

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v
```

The validator accepts any list with ≥ 3 strings, including strings that happen to be Pydantic field names. When haiku exhausted its token budget mid-generation (run 86, gta_game, lever `bb5f1a82`), it emitted the literal string `"review_lever"` as the third option. The validator counted 3 items and passed without error. The defect shipped to all downstream consumers that assume each option is a strategic description.

**B3: Review length cap is unenforced at the schema level**

- `identify_potential_levers.py:243` — "Keep each `review_lever` under 2 sentences (aim for 20–40 words)"
- `identify_potential_levers.py:109–116` — `review_lever: str = Field(...)` has no `max_length`

The cap is advisory only. For complex plans (haiku parasomnia, run 86), models generate 60+ word reviews that pass Pydantic validation because `str` fields have no length constraint. The current `check_review_format` validator (lines 144–160) only checks a minimum of 10 chars and absence of square brackets — it sets a floor, not a ceiling. The insight confirms 6,898 output tokens in a single haiku parasomnia call despite the cap instruction.

**B4: `partial_recovery` event conflates early loop-exit with genuine call failure**

- `runner.py:517–523`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

This fires whenever `calls_succeeded < 3`, regardless of whether the loop exited because:
1. The model generated ≥ 15 levers in 2 calls (normal/good — a loop-exit), or
2. A third API call genuinely failed (an error condition).

Both outcomes produce identical `partial_recovery` events. The insight quantitative table counted 3 haiku partial_recovery events in run 86, but the usage_metrics confirm all three were loop-exits (≥ 15 levers in fewer calls). Dashboards that count `partial_recovery` as a failure proxy are systematically over-counting failures whenever haiku over-generates.

---

## Suspect Patterns

**S1: Silent swallowing of persistent failures across calls 1–(max_calls-1)**

- `identify_potential_levers.py:321–326`

```python
if len(responses) == 0 and call_index == max_calls:
    raise llm_error from e
logger.warning(...)
continue
```

If calls 1 through 4 all fail (e.g., repeated structured-output parse errors), each failure is logged as a warning and the loop continues. Only on call 5 (the last) with still-zero responses does it raise. The error raised is from call 5, not call 1. This is the intended retry behaviour, but it means a model that consistently fails structured-output parsing will silently exhaust 4 retries before surfacing any error. Combined with the 5-call budget, it can produce misleading logs: 4 warning lines, then 1 error — but the 4 warnings are easy to miss.

This pattern is correct for the stochastic-failure use case (llama3.1 gta_game 2-option bug) but potentially misleading for systematic failures.

**S2: "Under 2 sentences" wording is ambiguous**

- `identify_potential_levers.py:243` — "Keep each `review_lever` under 2 sentences"

"Under 2 sentences" is commonly parsed as "fewer than 2 sentences" (i.e., exactly 1 sentence). But combined with "aim for 20–40 words" it's compatible with a 2-sentence interpretation. The insight documents a haiku review that is 2 sentences and 62 words — which satisfies "≤ 2 sentences" but violates "≤ 40 words". The ambiguous bound means models can comply with one reading while violating the other. Since the word count is the more precise bound, "under 2 sentences" adds noise rather than clarity.

**S3: `consequences` field description uses English-specific anti-pattern reference**

- `identify_potential_levers.py:100–101` (and `LeverCleaned` equivalent at lines 189–190)

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
```

This tells the LLM not to use the old English template pattern "Controls X vs. Y / Weakness: Z". For non-English models responding in the source language (Chinese, Japanese, etc.), this is a no-op — they wouldn't produce "Controls" anyway. But for English-biased models, explicitly naming the banned phrases in a prohibition risks the prohibition-backfire effect documented in OPTIMIZE_INSTRUCTIONS lines 81–82: small models can copy the named forbidden phrases rather than avoiding them. The correct pattern is to describe what the field SHOULD contain, not what it should NOT.

**S4: Thread safety: `set_usage_metrics_path` comment vs. lock scope is misleading**

- `runner.py:192–194`

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

The comment on lines 183–185 says `set_usage_metrics_path` uses thread-local storage. If that's true, the lock is not protecting the thread-local write — only the `dispatcher.add_event_handler` call is the shared-state operation that needs serialization. The lock is still correct (it covers the dispatcher), but the comment implies both operations need it, which is inaccurate and may mislead future maintainers into removing the lock thinking it's unnecessary for the dispatcher call.

---

## Improvement Opportunities

**I1: Remove "core tension" from both trigger locations**

- `identify_potential_levers.py:111` — Rewrite `review_lever` field description
- `identify_potential_levers.py:228` — Rewrite section 4 validation protocol

Current:
```
"A short critical review of this lever — name the core tension,
then identify a weakness the options miss."
```

Suggested:
```
"A short critical review: identify the primary trade-off this lever introduces,
then state the specific gap the three options leave unaddressed."
```

This preserves the content goal ("trade-off + gap") while removing the structural cue that triggers "The tension is..." openers. Apply the same rewrite to section 4, line 228. Expected effect per insight H1: reduce "The tension is..." opener frequency from ~100% to <40% for llama3.1 and haiku.

**I2: Add field-name rejection validator to `options`**

After `check_option_count`, add a second validator:

```python
_LEVER_FIELD_NAMES = {"lever_index", "name", "consequences", "options", "review_lever"}

@field_validator('options', mode='after')
@classmethod
def check_no_field_name_leakage(cls, v):
    for item in v:
        if isinstance(item, str) and item.strip() in _LEVER_FIELD_NAMES:
            raise ValueError(f"option '{item}' appears to be a field-name artifact from truncated generation")
    return v
```

This would catch the run-86 haiku gta_game defect at validation time, triggering a retry rather than shipping the malformed lever. Expected effect per insight C1: zero field-name strings in shipped options.

**I3: Distinguish loop-exit from call failure in `partial_recovery`**

In `runner.py`, pass the lever count in `PlanResult` and use it to emit a distinct event:

```python
# in _run_plan_task, after pr.calls_succeeded < 3 check:
if pr.lever_count is not None and pr.lever_count >= 15:
    _emit_event(events_path, "early_exit_sufficient_levers", ...)
else:
    _emit_event(events_path, "partial_recovery", ...)
```

Requires adding `lever_count: int | None = None` to `PlanResult` and populating it in `_run_levers`. Expected effect per insight C2: cleaner failure-rate dashboards, no false alarms from over-generating haiku.

**I4: Add field-description template lock to OPTIMIZE_INSTRUCTIONS**

`identify_potential_levers.py:27–86` — OPTIMIZE_INSTRUCTIONS documents single-example lock and template-lock migration, but not the newly confirmed field-description-induced lock. Suggested addition (after line 85):

```
- Field-description-induced template lock. When a Pydantic field description
  contains a structural phrase like "name the core tension", models read this
  as a literal instruction and start every output in that field with "The
  tension is…" or "The core tension is X versus Y", producing structurally
  identical reviews across all levers and plans. Fix by describing the required
  *content* ("identify the primary trade-off and the specific gap") rather than
  the expected *sentence structure*. The examples in the system prompt are not
  enough to override a cue in the field description itself.
- Field-name leakage in options. When token budget is exhausted mid-generation,
  structured output may emit a Pydantic field name (e.g., "review_lever",
  "consequences") as a literal option value. The current check_option_count
  validator does not catch this — it only checks list length. Add a validator
  that rejects options whose value exactly matches a known field name.
```

**I5: Clarify the `review_lever` length bound**

Replace the ambiguous "under 2 sentences (aim for 20–40 words)" at line 243 with a single, unambiguous bound: "One sentence, 20–40 words." One-sentence reviews are easier for models to verify internally and harder to violate than "under 2 sentences."

---

## Trace to Insight Findings

| Insight observation | Code location | Root cause |
|---|---|---|
| "tension" template lock — 100% of llama3.1 gta_game reviews start "The tension here is between X and Y" | `identify_potential_levers.py:111` and `:228` | "name the core tension" in both Pydantic field description and system prompt section 4 (B1) |
| Template leakage — `"review_lever"` appears as 3rd option in lever 15, haiku gta_game run 86 | `identify_potential_levers.py:130–142` | `check_option_count` validates only list length, not string content (B2) |
| Review length cap not enforced for complex plans — haiku parasomnia 6,898 tokens / 62-word reviews | `identify_potential_levers.py:109–116, :243` | `review_lever: str` has no `max_length`; cap is instruction-only (B3) |
| Haiku partial_recovery event count increased 2→4 but all are loop-exits | `runner.py:517–523` | `partial_recovery` fires on `calls_succeeded < 3` regardless of cause (B4) |
| Persistent failures across calls 1–4 are silently swallowed | `identify_potential_levers.py:321–326` | Raise condition only on `call_index == max_calls` (S1) |
| OPTIMIZE_INSTRUCTIONS gap: field-description template lock not documented | `identify_potential_levers.py:27–86` | New failure mode discovered in run 80/86, not yet in known-problems list (I4) |
| OPTIMIZE_INSTRUCTIONS gap: field-name leakage not documented | `identify_potential_levers.py:27–86` | New failure mode discovered in run 86, not yet in known-problems list (I4) |

---

## PR Review

### PR #357: "fix: B1 step-gate, medical example, review cap, first-call retry"

**B1 step-gate** (`runner.py:517–519`): Correctly scoped. The `if step == "identify_potential_levers"` guard prevents `partial_recovery` events from other steps from mis-triggering B1. Implementation matches intent. No edge cases found.

**First-call retry** (`identify_potential_levers.py:317–327`): Implementation is correct. The condition `if len(responses) == 0 and call_index == max_calls: raise` lets all retries run and only surfaces an error if the final call also fails with no prior successes. The targeted failure (llama3.1 gta_game producing 2 options stochastically) is fixed: run 80 shows 3/3 calls succeeded. One minor concern: if persistent structural failures cause calls 1–4 to fail silently, the user sees 4 warning lines and then an error from call 5, which may be a different error message than the original root cause.

**Medical example** (`identify_potential_levers.py:231`): The IRB/clinical-site example is domain-appropriate, contains no fabricated numbers, and counts approximately 31 words — within the 20–40 word cap. The example does not use "tension" as a structural cue. No issues with the example content.

**Review length cap** (`identify_potential_levers.py:243`): The instruction "Keep each `review_lever` under 2 sentences (aim for 20–40 words)" was added, but:
1. The cap is purely advisory — there is no Pydantic `max_length` to enforce it.
2. For complex plans (haiku parasomnia), the instruction is ignored: run 86 shows 62-word reviews and 6,898 output tokens per call.
3. The three examples in section 4 (lines 229–232) each count approximately 33, 31, and 37 words — within the cap. So examples and cap are consistent. But without schema-level enforcement, haiku can exceed the cap on complex plans regardless of the instruction.

The PR partially achieved its goal: per-call verbosity dropped 66% for simple plans (7,308→2,489 tokens for gta_game). For complex plans it did not.

**New "tension" template lock introduced (unintended consequence)**: The PR changed the medical example from urban-planning (Section 106) to IRB/clinical-site. This change is good in isolation. However, the `review_lever` field description (line 111) and section 4 instruction (line 228) both still say "name the core tension" — a phrase that predates this PR. The PR did not fix this. The result is that both runs 80 and 86 now exhibit a near-universal "tension" opener, a pattern that was not as dominant in pre-PR runs. The PR's example changes did not trigger this — the pre-existing field description wording is the root cause (B1). The PR's addition of a new example may have shifted which pattern models copy, but the "tension" cue in the field description was always the structural trigger.

**OPTIMIZE_INSTRUCTIONS additions** (lines 81–85): The PR added documentation for prohibition backfire and verbosity amplification. Both are accurate. However, two new failure modes discovered in runs 80–86 were not added: field-description-induced template lock (B1 root cause) and field-name leakage in options (B2). These should be documented in the next iteration.

**Overall PR assessment**: The first-call retry fix is a confirmed improvement with measurable impact. The medical example is a sound addition. The review length cap instruction partially works. The PR should be kept but three follow-up items are needed before updating best.json: fix the "core tension" language in the field description and section 4, add a field-name rejection validator to `options`, and add the two new failure modes to OPTIMIZE_INSTRUCTIONS.

---

## Summary

The most impactful bugs are structural prompt issues, not runtime logic bugs.

**B1** (field description + section 4 both say "name the core tension") is the confirmed root cause of the near-universal "tension" template lock in runs 80 and 86. It predates PR #357 and was not addressed by the PR. Fixing both occurrences (lines 111 and 228) is the highest-priority next action.

**B2** (`check_option_count` accepts field-name strings) caused the template leakage defect in run 86 haiku gta_game. A one-line validator addition would prevent this class of defect entirely.

**B3** (no schema-level enforcement of the review length cap) explains why haiku generates 60+ word reviews on complex plans despite the "20–40 words" instruction. The cap instruction works for simple plans but fails for complex ones where model attention is divided.

**B4** (`partial_recovery` conflates loop-exit and call failure) is an operational/observability issue. It inflates apparent failure counts in dashboards and makes analysis harder. It does not affect output quality.

The PR's first-call retry fix is its strongest contribution. The template lock and leakage issues need the follow-up fixes described in I1–I4.
