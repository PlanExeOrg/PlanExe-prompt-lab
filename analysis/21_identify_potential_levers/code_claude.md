# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py` (mainline, current)
- `prompt_optimizer/runner.py` (mainline, current)
- `.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` (PR #313 worktree)

The insight files describe runs 53–59 as "after PR", meaning they were executed using
the worktree version of `identify_potential_levers.py`. The mainline reviewed here is
the **pre-PR state**. The worktree is the PR's implementation target.

---

## Bugs Found

### B1: `Lever.consequences` field description mandates fabricated quantitative estimates

**File:** `identify_potential_levers.py` (mainline), lines 37–44
**Severity:** High — this is the primary root cause of percentage/dollar fabrication.

```python
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "  # ← forces fabrication
        ...
    )
)
```

The phrase **"at least one quantitative estimate are mandatory"** is injected into every
LLM call as part of the structured output schema. It directly instructs the model to
invent a number when none exists in the project context. Regardless of what the system
prompt says about prohibiting fabricated statistics, this Pydantic field description
wins because it appears in the structured output format specification the LLM follows
to satisfy the schema.

The same fabrication mandate appears in:
- `Lever.consequences` description (lines 37–44)
- `LeverCleaned.consequences` description (lines 129–139)
- System prompt section 2 ("Include measurable outcomes: … a % change, capacity shift,
  or cost delta") at line 164

This creates an instruction loop: the system prompt says "no fabricated statistics" but
the schema says "quantitative estimate mandatory". Models resolve this conflict by
fabricating numbers that look plausible (budget splits, percentages of a known total).

The worktree PR rewrites `Lever.consequences` to: *"only cite numbers if the project
context provides evidence for them"* — correctly removing the fabrication mandate.

---

### B2: `check_review_format` validator uses English-only substring matching

**File:** `identify_potential_levers.py` (mainline), lines 95–98

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if 'Weakness:' not in v:
    raise ValueError("review_lever must contain 'Weakness: ...'")
```

Hard-coded English strings `'Controls '` and `'Weakness:'` will reject valid lever
outputs from non-English plans. When PlanExe receives a prompt in Chinese, Japanese,
Arabic, German, etc., the LLM naturally responds in the same language, and neither
marker will appear. Every lever from a non-English plan will fail validation, trigger
a retry, likely fail again, and count as an LLMChatError.

The worktree PR fixes this with language-agnostic structural checks:
```python
if len(v) < 20:
    raise ValueError(...)
if '[' in v or ']' in v:
    raise ValueError(...)
```

---

### B3: Silent partial-call loss not observable in `events.jsonl`

**File:** `identify_potential_levers.py` (mainline and worktree), lines 272–278;
**File:** `runner.py`, lines 302–309

When call 2 or 3 fails after earlier calls succeeded, the code silently breaks:
```python
logger.warning(
    f"Call {call_index} of {total_calls} failed [{llm_error.error_id}], "
    f"returning partial results from {len(responses)} prior call(s)."
)
break
```

A `logger.warning` is written, but no event is emitted to `events.jsonl`. The
`_run_plan_task` wrapper in `runner.py` logs `run_single_plan_complete` as soon as
`status == "ok"`, which it will be even for a 2-of-3 call result. There is no
`partial_call_loss` event type.

Downstream analysis has no way to distinguish a fully complete run from a
2-of-3 partial run by inspecting `events.jsonl`. This is confirmed by the codex
insight: "Plans with only 2 raw responses: 2 → 3 (worse)" and "none contain
`LLMChatError`, so the missing call is still not observable from the event logs."

---

### B4: `set_usage_metrics_path` called outside the thread lock (race condition)

**File:** `runner.py`, lines 106, 140

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")  # line 106 — outside lock

with _file_lock:                                                   # line 108
    dispatcher.add_event_handler(track_activity)

...

finally:
    set_usage_metrics_path(None)                                   # line 140 — outside lock
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)
```

`set_usage_metrics_path` writes to global state, but it is called before and after the
`_file_lock` block. In parallel mode (`workers > 1`), two threads running concurrently
can overwrite each other's metrics path:
- Thread A sets path to `plan_A/usage_metrics.jsonl`
- Thread B sets path to `plan_B/usage_metrics.jsonl`
- Both threads now write metrics to `plan_B`'s file
- `plan_A`'s usage metrics are lost or corrupted

The lock should encompass `set_usage_metrics_path` as well, or usage metrics should
use thread-local storage rather than a global path.

---

### B5: Mainline `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant missing fabrication prohibition

**File:** `identify_potential_levers.py` (mainline), lines 154–196

The constant used when no external system prompt is provided (direct `__main__` usage)
does not contain "NO fabricated statistics or percentages" in its prohibitions section
(lines 185–190). It lists:
- NO prefixes/labels in options
- NO generic option labels
- NO placeholder consequences
- NO `[specific innovative option]` placeholders
- NO value sets without clear strategic progression

No prohibition on invented percentages. Anyone running the module directly
(`python -m worker_plan_internal.lever.identify_potential_levers`) gets a prompt that
both mandates quantitative estimates (B1) and fails to prohibit fabrication. The worktree
system prompt constant adds "Do not fabricate percentages or cost estimates" to section 2.

---

## Suspect Patterns

### S1: Call-2/3 prompt appends the full user prompt again

**File:** `identify_potential_levers.py` (mainline and worktree), lines 231–235

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"  # ← full multi-file user prompt repeated
)
```

The full user prompt (three concatenated files: `001-2-plan.txt`,
`002-6-identify_purpose.md`, `002-8-plan_type.md`) is appended in full on every call.
For longer plans this can push calls 2/3 to 2× the token cost of call 1. For plans with
a specific budget figure (e.g., HK$470m in hong_kong_game), the budget is re-presented
to the model in full context three times, reinforcing the "budget anchor" effect that
drives allocation-percentage fabrication (see N2/N3 in insight_claude).

No structural fix is needed here if the full context is required, but this pattern
interacts with B1 to amplify budget-anchor fabrication.

### S2: Exact-string deduplication catches only verbatim name repeats

**File:** `identify_potential_levers.py` (mainline), lines 290–296

```python
seen_names: set[str] = set()
for i, lever in enumerate(levers_raw, start=1):
    if lever.name in seen_names:
        logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
        continue
    seen_names.add(lever.name)
```

Semantic near-duplicates ("Festival Strategy for Critical Reception" /
"Festival Strategy for Audience Engagement") pass through unchecked. The codex insight
N5 flags this as an unresolved issue. This is expected per the module docstring
("Downstream there is a deduplicate levers") but worth noting that cross-call semantic
near-duplicates can inflate lever counts.

### S3: `execute_function` closure captures `messages_snapshot` by reference

**File:** `identify_potential_levers.py` (mainline), lines 247–257

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

`execute_function` closes over `messages_snapshot`. Because `llm_executor.run()` is
called synchronously immediately after, the closure is evaluated before the next loop
iteration changes `messages_snapshot`. This is safe in current usage. However, if
`LLMExecutor.run` were ever made async or the closure were stored for deferred
execution, it would capture stale messages. The pattern is fragile.

---

## Improvement Opportunities

### I1: Add anti-fabrication reminder to call-1 prompt

**File:** `identify_potential_levers.py`, lines 227–229

The PR adds the reminder only to calls 2/3. The insight analysis confirms that for haiku
(run 58) and gpt-oss-20b (run 54), fabricated dollar amounts appear in `responses[0]`
(call 1), putting them completely outside the PR's scope.

Adding the same one-line reminder to the call-1 path:
```python
if call_index == 1:
    prompt_content = (
        user_prompt +
        "\nDo not invent percentages, cost savings, or performance deltas — "
        "use qualitative language unless the project document supplies the number."
    )
```
This is the highest-leverage follow-up to PR #313, as confirmed by both insight files
(N3 in claude, H1 in codex).

### I2: Add a numeric-claim warning validator (post-generation)

A lightweight post-generation scan for `\d+%` or `\$\s*[\d,]+` or `HK\$` patterns
in option and consequence text could emit `logger.warning` without rejecting the output.
This would make fabrication regressions immediately visible in logs rather than
requiring post-hoc analysis of the JSON outputs.

Suggested location: at the end of `IdentifyPotentialLevers.execute()` before
constructing the return value, iterating over `levers_cleaned`.

### I3: Emit a `partial_call_loss` event when a call fails mid-sequence

When the `break` path is taken at line 278 of the mainline, emit an event to
`events.jsonl` via the caller's event-logging infrastructure (or return a flag in
the `IdentifyPotentialLevers` result). This would make the "2 of 3 calls completed"
state observable without post-hoc JSON inspection, directly addressing the observability
gap in codex insight C3.

The simplest approach: add a `completed_calls: int` field to `IdentifyPotentialLevers`
and have `run_single_plan` in `runner.py` log it in the `run_single_plan_complete`
event.

### I4: Add minimum option word-count warning

The codex insight reports 21 short options (< 5 words) in the after batch, all from
run 53. A post-validation sweep warning when any option is < 8 words would catch
slogan/label regression early. This can be a `logger.warning` (not a Pydantic
validator rejection) to avoid triggering expensive retries.

---

## Trace to Insight Findings

| Insight Finding | Root Code Location | Explanation |
|---|---|---|
| N1/N2/N3 (haiku, gpt-oss-20b fabricate percentages in call 1) | `identify_potential_levers.py:37–44` (B1) | `"at least one quantitative estimate are mandatory"` in `Lever.consequences` field description overrides the system prompt prohibition and directly instructs models to invent numbers. |
| N3 (PR cannot address call-1 fabrication) | `identify_potential_levers.py:227–229` (I1) | Call-1 prompt has no anti-fabrication reminder; the PR only adds it for calls 2/3. |
| Codex: "silent partial-call loss persists and slightly worsens" | `identify_potential_levers.py:272–278` + `runner.py:302–309` (B3) | Partial failures only emit `logger.warning`, not an `events.jsonl` entry; `run_single_plan_complete` fires even for 2-of-3 runs. |
| N4 / codex short-option relapse | `identify_potential_levers.py:47–50` (I4) | No minimum word-count guard on options; call-2/3 reminder helps (worktree line 274) but call-1 path has no equivalent. |
| Codex: "fragile English-only validators" | `identify_potential_levers.py:95–98` (B2) | Hard-coded `'Controls '` and `'Weakness:'` checks break non-English outputs. |
| Codex: parallel usage metrics interference | `runner.py:106,140` (B4) | Global metrics path written outside lock; concurrent threads can overwrite each other's path. |

---

## PR Review

### What PR #313 changes (worktree vs. mainline)

The PR description says "adds one line" but the worktree diff is substantially larger:

**1. Pydantic schema: `Lever.consequences` description rewritten**
- Mainline (line 37–44): mandates "at least one quantitative estimate are mandatory"
- Worktree (line 80–87): "only cite numbers if the project context provides evidence for them"

This is the most impactful change in the worktree. It removes the direct fabrication
mandate from the structured output schema that the LLM follows to produce JSON.
It directly addresses B1.

**2. `check_review_format` validator rewritten (language-agnostic)**
- Mainline (lines 95–98): English-only substring checks
- Worktree (lines 138–143): length ≥ 20 chars + no square brackets

This addresses B2 and is explicitly motivated by the new `OPTIMIZE_INSTRUCTIONS`
warning about fragile English-only validators.

**3. `OPTIMIZE_INSTRUCTIONS` constant added (worktree lines 27–69)**
Documents known failure modes (fabricated numbers, hype, vague aspirations, English-only
validation). This is good developer documentation but has no runtime effect.

**4. Call-2/3 user prompt: anti-fabrication + full-sentence reminder added**
- Worktree lines 274–275:
  ```
  Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.
  Do not invent percentages, cost savings, or performance deltas — use qualitative language unless the project document supplies the number.
  ```

Both reminders are absent from the mainline. The codex insight confirms the full-sentence
reminder was not present in the mainline's call-2/3 path either.

**5. System prompt constant rewritten**
The worktree's `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` removes the "conservative →
moderate → radical" triad mandate and the "measurable outcomes: % change" requirement.
However, since the runner always passes an external system prompt from
`--system-prompt-file`, this change only affects direct module invocation.

### Does the implementation match the PR intent?

The PR description says it adds one line to prevent call-2/3 fabrication. The worktree
contains several more changes that go significantly beyond the stated description. The
most impactful unexplained change is the `Lever.consequences` field description rewrite
(B1 fix), which removes the fabrication mandate from the structured output schema. This
change is not mentioned in the PR description and is more likely to reduce call-1
fabrication than the call-2/3 reminder.

**Gap:** The call-1 prompt (worktree line 267–268) still has no anti-fabrication
reminder. Both insight files identify this as the dominant remaining source of percentage
fabrication. The worktree's schema fix (Lever.consequences rewrite) partially addresses
call-1 fabrication, but budget-anchor behavior (models seeing a specific total budget and
inventing sub-allocations) may persist even without the explicit mandate, as the system
prompt's qualitative language about "budget" still provides the anchor.

### Could the PR introduce new regressions?

- The new `review_lever` validator (worktree) is more permissive than the mainline.
  Any non-empty, non-placeholder two-sentence string passes. This could let through
  structurally weak reviews that previously would have been rejected. Given that the
  mainline English-only checks caused legitimate failures for non-English plans, the
  worktree's structural validator is the better trade-off.
- The "at least 15 words" option reminder in call-2/3 has no corresponding validator
  in the Pydantic schema. Models could still produce short options in call 1 or in call
  2/3 if they ignore the user prompt. A post-generation warning (I4) would catch this
  without forcing a retry.

---

## Summary

The mainline `identify_potential_levers.py` has three primary defects that the PR
addresses in the worktree:

**B1** is the most critical finding: the `Lever.consequences` Pydantic field description
tells every LLM call "at least one quantitative estimate are mandatory", directly
overriding the system prompt's anti-fabrication prohibition. This is the structural
root cause of percentage and dollar fabrication across all models and all calls. The
worktree rewrites this description to be grounding-conditional, and this change is more
impactful than the call-2/3 reminder.

**B2** (English-only validators) is a correctness bug that will reject all non-English
outputs. The worktree's language-agnostic check is the correct fix.

**B3** (silent partial-call loss) remains unaddressed in both mainline and worktree.
The observability gap means production failures that complete 2-of-3 calls are
indistinguishable from full successes in `events.jsonl`.

**B4** (`set_usage_metrics_path` race condition in `runner.py`) is a thread-safety bug
in parallel mode that could corrupt usage metrics across concurrent plan runs. It is
unaddressed by PR #313 (which only touches `identify_potential_levers.py`).

The highest-leverage follow-up to PR #313 is **I1**: adding the anti-fabrication
reminder to call-1 as well. The worktree's schema fix (B1) reduces the structural
pressure toward fabrication, but budget-anchor behavior in call-1 for models like haiku
and gpt-oss-20b will likely persist until the call-1 user prompt explicitly reinforces
the qualitative-only rule.
