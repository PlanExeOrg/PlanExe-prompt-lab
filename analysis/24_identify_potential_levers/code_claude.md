# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: **#334** — "fix: remove unused summary field, slim call-2/3 prefix"

---

## Bugs Found

### B1 — `DocumentDetails.summary` required field never used downstream
**File:** `identify_potential_levers.py:164–166`

```python
summary: str = Field(
    description="One sentence prescribing a concrete addition to a specific lever. ..."
)
```

`summary` has no `default=None`, making it a **required** field. Every LLM call must
produce a valid summary string or the entire `DocumentDetails` response fails Pydantic
validation. Yet no downstream code ever reads this field:

- `to_dict()` (line 371) calls `response.model_dump()` which includes `summary`, but
  the serialized responses dict is only written to the raw file (`002-9-potential_levers_raw.json`).
- The cleaning loop (lines 341–356) only reads `response.levers`.
- `lever_item_list()` / `save_clean()` never access `summary`.

The summary is silently discarded. Every response wastes tokens generating it and
risks a full validation failure if the model omits it.

**PR #334 claimed to remove this field.** The field is still present in the current code.

---

### B2 — System prompt section 4 still instructs models to generate `summary`
**File:** `identify_potential_levers.py:232–234`

```
   - For `summary`:
     One sentence prescribing a concrete addition to a specific lever.
     Example: "Add 'partner with a regional distributor for last-mile logistics' to Supply Chain Strategy."
```

This section of the system prompt reinforces the `summary` obligation. If the field itself
(B1) were removed from the schema, this instruction would become dead prompt text that
still consumes tokens and potentially confuses models. Together with B1, both the schema
constraint and its prompt instruction need to be removed together.

**PR #334 claimed to remove this section.** It is still present in the current code.

---

### B3 — "at least 15 words" enforcement missing from call 1
**File:** `identify_potential_levers.py:277–286` (call-2/3 prefix) vs `243–247` (section 6)

The PR description states:
> "Add 'at least 15 words with an action verb' to section 6 (option structure) for
> uniform enforcement across all calls"

The current system prompt section 6 (lines 243–247) reads:

```
6. **Option Structure**
   - Maintain parallel grammatical structure across options
   - Ensure options are self-contained descriptions
   - Each option should be a concrete, actionable approach — not a vague aspiration
```

No 15-word requirement appears here.

The constraint **does** appear in the call-2/3 user prefix (line 283):

```python
f"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n"
```

Call 1 (lines 276–277) uses only `user_prompt` with no additional instructions — the
word-count floor is absent entirely for the first call. The PR's stated goal of
"uniform enforcement across all calls" is not achieved: call 1 is left unenforced.

---

### B4 — Global dispatcher event handler shared across concurrent worker threads
**File:** `runner.py:104–109, 146–148`

```python
dispatcher = get_dispatcher()       # global llama_index singleton

with _file_lock:
    set_usage_metrics_path(...)
    dispatcher.add_event_handler(track_activity)   # appended to global list
```

`get_dispatcher()` returns the **process-wide** llama_index dispatcher. When
`workers > 1`, multiple `run_single_plan` threads each add their own `TrackActivity`
handler to the same global list. Every LLM event is then broadcast to **all**
registered handlers simultaneously.

Consequence: plan A's `track_activity.jsonl` will contain interleaved events from
plans B, C, and D that happened to be running concurrently. The `_file_lock` guard
only prevents filesystem writes from racing; it cannot prevent the dispatcher from
dispatching one plan's events to another plan's handler.

`set_usage_metrics_path` is correctly thread-local (per the comment), but
`dispatcher.event_handlers` is not. The per-plan tracking files produced during
multi-worker runs are unreliable for debugging.

---

## Suspect Patterns

### S1 — Case-sensitive lever name deduplication
**File:** `identify_potential_levers.py:279–280, 341–344`

`generated_lever_names` (used to build the "do NOT reuse" list for calls 2/3) and
`seen_names` (used to skip duplicates in the cleaned output) both compare names with
exact string equality. "Supply Chain Strategy" and "supply chain strategy" would pass
through as distinct levers. For models that vary capitalisation between calls this can
produce near-duplicate lever names in the final output that the downstream
`DeduplicateLevers` step must then clean up.

### S2 — Partial recovery results are indistinguishable from full success on resume
**File:** `runner.py:122–131, 363`

When only 1 or 2 of 3 calls succeed, `run_single_plan` still returns
`PlanResult(status="ok")`. The resume logic (line 363) adds any `status == "ok"` plan to
the `completed` set and skips it on restart. A plan that succeeded with only 1/3 calls
(potentially 5 levers instead of 15–21) will never be retried, even though its output
may be substantially thinner than a full run.

### S3 — Single-validation-error fails the whole response
**File:** `identify_potential_levers.py:131–132`

```python
def check_option_count(cls, v):
    if len(v) != 3:
        raise ValueError(f"options must have exactly 3 items, got {len(v)}")
```

If a model returns 15 well-formed levers where one happens to have 4 options, the
entire `DocumentDetails` response is rejected and retried. A salvage path (accept the
response, trim the over-long options list to 3) would be more token-efficient. The
comment acknowledges the downstream assumption of exactly 3 options; the choice to
hard-reject vs trim is defensible, but worth revisiting given the qwen3 ValueError
(N3 in insight).

---

## Improvement Opportunities

### I1 — Negative constraint for "This lever governs the tension between" template lock
**File:** `identify_potential_levers.py:97–107` (field description) and `226–231` (system prompt)

Both the `review_lever` field description and the system prompt section 4 show the
first example as the first item. For llama3.1, 100% of run-75 reviews use
"This lever governs the tension between…" — a direct copy of that example. Append a
negative constraint:

```
Do NOT open with the phrase "This lever governs the tension between".
Vary your review structure: name the tension, then identify a weakness the 3 options miss.
```

This directly addresses the template lock regression from N1/N5 in the insight.

### I2 — Negative constraint for qwen3's model-native "Core tension:" opener
**File:** `identify_potential_levers.py:97–107, 226–231`

Runs 76–78 (qwen3) consistently open reviews with "Core tension: X. …" — a
model-native template not derived from either example. Add:

```
Do NOT open with "Core tension:".
```

This is a structural constraint that does not rely on English keywords (safe for
non-English plans) since it targets a specific phrase the model generates
regardless of input language.

### I3 — OPTIMIZE_INSTRUCTIONS gap: model-native template patterns
**File:** `identify_potential_levers.py:27–73`

The current `OPTIMIZE_INSTRUCTIONS` documents *prompt-example-driven* template lock
(line 69–72) but does not mention model-native template patterns — fixed review
openers that emerge from model training rather than from the prompt examples.
qwen3's "Core tension:" is the first observed instance. Proposed addition:

```
- Model-native template patterns. Some models produce reviews through their
  own fixed templates (e.g., "Core tension: X. Y." for qwen3-30b-a3b) that
  are not copies of prompt examples but are equally formulaic. These cannot
  be fixed by changing examples; they require explicit negative constraints
  ("Do not open with 'Core tension:'") or output-diversity instructions.
```

### I4 — Add "at least 15 words" to system prompt section 6
**File:** `identify_potential_levers.py:243–247`

Section 6 currently lacks the word-count floor that only appears in the call-2/3
prefix. Adding it to section 6 ensures call 1 also enforces the constraint
without relying on the call-2/3 prefix to carry all the per-option quality rules.
Both places already reference "action verb" in slightly different wording; aligning
them would make the instruction consistent.

### I5 — Case-insensitive lever name comparison
**File:** `identify_potential_levers.py:279, 341`

Normalize names to lowercase before adding to `generated_lever_names` and
`seen_names`. This prevents near-duplicate lever names that differ only in
capitalisation from passing through to the downstream deduplication step.

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|-----------------|----------------|
| **N1** — llama3.1 100% template lock on "This lever governs the tension between" (run 75) | B3 (call-1 has no extra review constraint), I1 (no negative constraint against that opening) |
| **N2** — llama3.1 hong_kong_game full timeout in run 75 | Not a code bug — model capability/timeout issue. No code change can guarantee ollama-llama3.1 completes complex plans within the default timeout. |
| **N3** — qwen3 run 78 parasomnia `ValueError` (JSON extraction) | S3 — a single malformed lever causes full response rejection. Also potentially the model producing `<think>` tokens or other reasoning-mode output in the JSON. |
| **N4** — "at least 15 words" produced no measurable change | B3 — the constraint was never in section 6 (only in call-2/3 prefix), and both before/after options already exceeded it. The instruction is only enforced for calls 2/3. |
| **N5** — second `review_lever` example absent in run 75 | B3 — if the pre-PR call-2/3 prefix reinforced the second example (even implicitly), slimming it removed that reinforcement. Call 1 never had it. |
| **P3** — qwen3 "Core tension:" reviews | I2, I3 — model-native template unaddressed by current prompt or OPTIMIZE_INSTRUCTIONS |
| **P4** — summary field removal is positive | B1, B2 — the removal is still incomplete in the current code |
| **E2** — hypothesis that prefix slim caused llama3.1 regression | Consistent with B3: call-1 has always been prefix-free; calls 2/3 lost content with each slim; weaker models had less reinforcement of the second example |
| **B4 (runner)** — concurrent per-plan event handler pollution | B4 in this review |

---

## PR Review

PR #334 claims four changes. Against the current code:

### Claim 1: "Remove `DocumentDetails.summary` field"

**NOT DONE.** `summary: str` (no default) remains at line 164.
The field is required by Pydantic validation on every call. Any response that omits
it fails the entire `DocumentDetails` parse and must be retried. The "no negative
side effects" assessment in the insight (P4) assumed the removal happened — if it
did not, those token costs and validation risks persist.

### Claim 2: "Remove summary validation section from system prompt"

**NOT DONE.** Lines 232–234 still instruct models to produce a summary with an
example. Together with B1, the schema and the prompt are inconsistent with the
PR's stated intent — the field and its instructions must be removed atomically.

### Claim 3: "Add 'at least 15 words with an action verb' to section 6 for uniform enforcement across all calls"

**PARTIALLY DONE / MISPLACED.** The constraint is in the call-2/3 user prefix
(line 283) but **not** in system prompt section 6 (lines 243–247). Call 1 — which
receives only `user_prompt` with no extra prefix — has no word-count enforcement.
The PR's claim of "uniform enforcement across all calls" is inaccurate: enforcement
is call-2/3 only, exactly as before except that the text was moved/added to the
per-call prefix rather than the system prompt.

This also means the "at least 15 words" instruction is not visible to models on
call 1 unless they happen to read the Pydantic field description (which structured
LLMs do receive, but weaker models parse inconsistently).

### Claim 4: "Slim call-2/3 prefix: remove duplicate quality/anti-fabrication reminders"

**DONE (but with a side effect).** The current call-2/3 prefix (lines 279–286) is
compact: it names already-generated levers, adds the 15-word requirement, and adds
the no-fabrication reminder. If the pre-PR prefix contained an explicit reference
or echo of the second `review_lever` example, removing it explains the llama3.1
regression observed in insight N1/N5: the second example ("Prioritizing X over Y
carries hidden costs…") dropped from 29% → 0% in run 75. The prefix slim may have
removed the only in-context reminder that reinforced that example for weak models.

### Summary of PR assessment

| Claim | Status | Risk |
|-------|--------|------|
| Remove `summary` field | **Not implemented** | Ongoing token waste, validation failures |
| Remove summary system-prompt section | **Not implemented** | Dead instructions, token waste |
| Add 15-word enforcement to section 6 | **Misplaced** (call-2/3 only) | Call 1 unenforced |
| Slim call-2/3 prefix | Done | Likely caused llama3.1 template-lock regression (N1/N5) |

The intended engineering improvements (B1, B2) have not taken effect. The one
change that did land (prefix slim) has a plausible negative side effect on weak
models. The net impact is: fewer tokens saved than intended, and one regression in
review diversity for llama3.1.

---

## Summary

**Five actionable items in priority order:**

1. **(B1 + B2)** Remove `DocumentDetails.summary: str` field and the matching system
   prompt section 4 `summary` instructions. Do both atomically. This is the
   PR's primary intent and it has not been executed.

2. **(B3)** Add the 15-word option constraint to system prompt section 6 so call 1
   is also covered. Without this, the "uniform enforcement" goal is unmet.

3. **(I1)** Add a negative constraint against the first-example opener in
   `review_lever`: "Do NOT open with 'This lever governs the tension between'."
   This is the single highest-leverage change for reducing template lock in
   llama3.1 (100% lock rate in run 75).

4. **(I2 + I3)** Add "Do NOT open with 'Core tension:'" and document model-native
   template patterns in `OPTIMIZE_INSTRUCTIONS`.

5. **(B4)** Investigate the global dispatcher event handler issue in `runner.py`
   multi-worker mode. Per-plan `TrackActivity` handlers accumulate events from all
   concurrent plans, making the track files unreliable for multi-worker debugging.
   Consider per-plan dispatcher scoping or a filtering predicate on the handler.
