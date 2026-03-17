# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #334 — "fix: remove unused summary field, slim call-2/3 prefix"

---

## Bugs Found

### B1 — Hard `options == 3` Pydantic validator rejects valid partial output (identify_potential_levers.py:122–133)

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) != 3:
        raise ValueError(f"options must have exactly 3 items, got {len(v)}")
    return v
```

`DocumentDetails` uses `min_length=5` on `levers`. If even one lever fails Pydantic validation (e.g., 2-option lever), the entire document is rejected — all 5–7 levers from that call are discarded, not just the offending lever. This is a disproportionate failure: a single malformed lever cascades into a full call failure, and if it's call 1, the whole plan fails.

The validator comment at line 127 cites "Run 89" as motivation ("silently passed validation and shipped to downstream tasks which assume exactly 3 options"). However, the downstream `DeduplicateLeversTask` already handles over-generation, and a lever with 2 options is far less damaging than losing 6 other valid levers. The strict constraint is over-engineered for the failure mode it prevents.

**Fix**: Replace `len(v) != 3` with `len(v) < 3` (or use `min_length=3` on the Pydantic field). Levers with 4–5 options are not problematic for downstream steps; only under-3 is.

---

### B2 — First `review_lever` example IS the leaked template (identify_potential_levers.py:100–104 and 224–227)

The `Lever.review_lever` Pydantic field description leads with:

```
'This lever governs the tension between centralization and local autonomy,
but the options overlook transition costs.'
```

This identical string also appears verbatim in section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 224–227). The same template-anchor example is injected twice — once via the system prompt and once via the structured-output schema description that llama_index embeds in the function-calling spec. Weaker models (llama3.1, qwen3) see this example as the most salient pattern to follow.

`OPTIMIZE_INSTRUCTIONS` (lines 69–72) explicitly warns: "When the prompt provides exactly one review_lever example, weaker models reproduce that exact syntax 90–100% of the time. Always provide at least two structurally distinct examples." The code has two examples, but the first one is the leaked template itself, meaning it is both the instruction and the prime example of what to reproduce.

The net effect: llama3.1 opens 100% of reviews with "This lever governs the tension between" (insight N3), and qwen3 uses "Core tension:" — a closely related opener not present in the examples but induced by the same framing. This is the root cause of the template lock issue.

---

## Suspect Patterns

### S1 — `execute_function` closure re-defined inside a loop (identify_potential_levers.py:291–299)

```python
for call_index in range(1, total_calls + 1):
    ...
    messages_snapshot = list(call_messages)

    def execute_function(llm: LLM) -> dict:
        sllm = llm.as_structured_llm(DocumentDetails)
        chat_response = sllm.chat(messages_snapshot)  # closed over by reference
        ...

    result = llm_executor.run(execute_function)
```

Python closures capture the variable binding, not the value. `messages_snapshot` is safe here only because `llm_executor.run(execute_function)` is synchronous and blocks before the loop reassigns `messages_snapshot`. If `run()` ever defers execution (async, thread pool), all closures would share the last iteration's `messages_snapshot`. This is a latent bug that would be hard to diagnose. A safer pattern is `def execute_function(llm, msgs=messages_snapshot)` to freeze the value at definition time.

### S2 — Global dispatcher event handler leaks across threads (runner.py:104–109, 146–148)

```python
dispatcher = get_dispatcher()
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`get_dispatcher()` returns a global singleton. When `workers > 1`, multiple plan threads each add their own `track_activity` handler to the same global dispatcher. While the lock protects the add/remove operations, the dispatcher delivers every LLM event to all currently-registered handlers. This means plan B's LLM events are routed to plan A's `track_activity` writer (and vice versa), cross-contaminating `track_activity.jsonl` files. Since `track_activity.jsonl` is deleted at the end (line 149), this doesn't corrupt the final outputs, but it wastes I/O and can cause file-not-found errors if the file is deleted before the other thread's handler finishes writing to it.

`set_usage_metrics_path` uses thread-local storage (correctly isolated), but the dispatcher handler is not thread-local. A per-plan `get_dispatcher()` sub-scope or thread-local event routing would fix this.

### S3 — `_next_history_counter` + `mkdir(exist_ok=False)` race window (runner.py:263–301)

The TOCTOU window between `_next_history_counter` scanning the filesystem and the `mkdir` creating the directory is handled with a retry loop (50 attempts). This works in practice but the scan is O(n) over all history directories and re-done from scratch on each retry attempt. If two concurrent processes both fail on the same counter, they both re-scan and could converge on the same next counter again. The current approach is safe enough for sequential or low-concurrency use but would spiral under high concurrency.

---

## Improvement Opportunities

### I1 — Add negative constraint to `review_lever` field description (highest priority)

The field description (lines 96–107) should explicitly prohibit the leaked openers:

```python
review_lever: str = Field(
    description=(
        "A short critical review of this lever — name the core tension, "
        "then identify a weakness the options miss. "
        "Do NOT open with 'This lever governs the tension between'. "
        "Do NOT open with 'Core tension:'. "
        "Name the specific tension in your own words. "
        "Examples: ..."
    )
)
```

The same negative constraints should be added to section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`. Evidence: 100% template lock in run 82 (llama3.1) and recurring "Core tension:" opener in runs 78, 85 (qwen3). OPTIMIZE_INSTRUCTIONS already documents "single-example template lock" but the code has not applied the prescribed fix (negative constraint) to the known offending phrases.

### I2 — Reinforce "at least 15 words" in Pydantic field description (not just system prompt text)

The `options` field description (lines 92–95) says "not a label" but does not mention word count. The `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 6 says "at least 15 words with an action verb", but weaker models weight the structured-output schema description more heavily than the system prompt when generating structured JSON. Adding the constraint directly to the Pydantic field description would reinforce it through the schema:

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. Each option must be a complete "
                "strategic approach (at least 15 words with an action verb), not a label. "
                "No more, no fewer than 3 options."
)
```

Evidence: llama3.1 averages ~12 words after the PR added the constraint to section 6 (up from ~7), but still below the 15-word floor (insight N2). The system-prompt instruction partially works; schema-level enforcement would add another signal.

### I3 — OPTIMIZE_INSTRUCTIONS is missing "model-native template openers" as a known problem

The `OPTIMIZE_INSTRUCTIONS` constant (lines 27–73) documents five known failure modes. "Model-native template openers" is not among them, despite being confirmed across analyses 22, 24, and 25 (insight "Reflect" section, and Q-section Q1 equivalent). This constant is presumably read by future optimization iterations, so missing it perpetuates the gap. Suggested addition:

```
- Model-native template openers. Small or MoE models prepend reviews with
  fixed phrases absent from prompt examples ("This lever governs the tension
  between", "Core tension: X."). These are driven by the model's training
  distribution, not by prompt examples. Only a negative constraint in the
  field description ("Do not open with 'This lever governs the tension
  between'") breaks the pattern. Structural validators alone will not catch
  this.
```

### I4 — `LeverCleaned.review` field description duplicates the leaked example unnecessarily (lines 190–200)

`LeverCleaned` is the output-only type — it is never passed to an LLM. Its field descriptions serve no prompting purpose. The duplicated examples in `LeverCleaned.review` (lines 193–199) are dead weight. Removing them (or replacing with a minimal description) reduces confusion and eliminates an accidental second site that might be pasted into a future prompt.

### I5 — Resumable runs skip completed plans by plan name, not by full result (runner.py:385–394)

The resume logic (lines 384–394) reads `outputs.jsonl` and marks plans as completed if `status == "ok"`. This is correct, but if a plan completes successfully and then a code change modifies the output schema or logic, a resumed run would silently skip re-running that plan. There is no version or content hash check. This is acceptable given the current workflow, but should be noted for future experiment reproducibility.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| N1 — llama3.1 gta_game Pydantic failure (2 options on levers 5, 6) | **B1** — hard `len(v) != 3` validator at line 131 rejects entire call when one lever has 2 options |
| N2 — "at least 15 words" not met by llama3.1 (avg ~12 words, call 1) | **I2** — constraint exists only in system prompt text (section 6), not in Pydantic field description; schema-level signal missing |
| N3 — 100% template lock in llama3.1 reviews ("This lever governs the tension between") | **B2** — that exact phrase is the lead example in both the Pydantic field description (line 101) and system prompt section 4 (line 225); negative constraint missing |
| N4 — Partial recoveries (calls_succeeded=2) | **B1** — single-lever validation failures cascade to full call loss, raising the probability that 1 of 3 calls fails |
| N3 continuation — qwen3 "Core tension:" opener | **B2** + **I1** — no negative constraint in field description or system prompt; the framing of the examples induces this opener even without an explicit example |

---

## PR Review

### What the PR claims to fix

1. Remove `DocumentDetails.summary` — required field never used downstream, wastes tokens
2. Remove matching summary validation section from system prompt
3. Add "at least 15 words with an action verb" to section 6 for all calls
4. Slim call-2/3 prefix

### Assessment of each change

**Item 1 (summary removal)**: Fully and correctly implemented. `DocumentDetails` (lines 152–163) has no `summary` field. This is confirmed by the grep evidence in the insight (zero `"summary"` keys in after runs). No edge cases missed.

**Item 2 (system prompt summary section removal)**: Correctly implemented. `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` has no summary-related instruction. Clean removal.

**Item 3 ("at least 15 words" added to section 6)**: Present in the system prompt (line 240): "at least 15 words with an action verb". However, this constraint exists only in the system prompt text, not in the Pydantic `options` field description (lines 92–95). For structured-output models, the schema field description is weighted differently (sometimes more heavily) than the system prompt narrative. The partial improvement (7→12 words for llama3.1) shows the prompt-level constraint is partially effective, but adding it to the Pydantic field description would close the remaining gap. The PR addresses the intended location (section 6) but misses the complementary schema-level enforcement.

**Item 4 (slim call-2/3 prefix)**: Implemented at lines 273–278. The prefix now contains only the "do not reuse names" instruction plus the original user prompt. Duplicate quality/anti-fabrication reminders are removed. The insight (P4, P5) confirms no regression. Clean implementation.

### Gaps / issues in the PR

**Gap 1 — `review_lever` example is the leaked template**: PR #334 changed the call-2/3 prefix and added a word-count constraint, but did not address the field-description example that drives template lock. The "This lever governs the tension between" example was already in the field description before this PR and remains after. Since the PR touched section 4 (Validation Protocols), it was adjacent to the fix site but the fix was not applied. This is the most impactful miss.

**Gap 2 — `options == 3` hard constraint not relaxed**: The PR's word-count change is meant to improve option quality, but the hard Pydantic constraint (`len(v) != 3`) continues to cause full call failures when weaker models produce 2-option levers. The PR summary mentions this pattern (B1), but the change was not included. Given that the PR explicitly touched the Pydantic schema (removed `summary`), this was a natural opportunity to also relax the validator.

**No regressions introduced**: The PR changes are conservative and well-scoped. The summary removal is clean. The prefix slim is correct. No new failure modes were introduced by the PR itself.

---

## Summary

The two most impactful code issues are:

**B1** (`identify_potential_levers.py:131`): The hard `options == 3` Pydantic validator causes full call failure when any single lever has 2 options. A lever with 2 options is a minor LLM compliance failure; discarding all 5–7 levers from that call is a disproportionate response. Fix: change to `len(v) < 3` (reject under-3, accept 4+).

**B2** (`identify_potential_levers.py:100–104` and `224–227`): The "This lever governs the tension between..." phrase is both the lead example in the Pydantic field description AND appears verbatim in the system prompt. Two identical anchors directly cause the 100% template lock observed in llama3.1 (run 82). Fix: add negative constraints ("Do NOT open with 'This lever governs the tension between'") to both locations; replace or reorder examples so the leaked phrase is not the first and most salient example.

**I1** (highest-priority improvement): Add the negative opener constraints to the `review_lever` Pydantic field description — this will propagate through the structured-output schema and is likely more effective than a system-prompt instruction alone for smaller models.

**I3**: Update `OPTIMIZE_INSTRUCTIONS` to document "model-native template openers" as a known failure class so future optimization iterations can address it systematically.

PR #334 is a correct and net-positive change that successfully removes the summary waste and partially improves option length. Its main omissions are the review template-lock fix (B2/I1) and the `options == 3` relaxation (B1), both of which were adjacent to the PR's changes.
