# Code Review (claude)

## Bugs Found

### B1 — `Lever.review_lever` Pydantic field description not updated by PR #316
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:92–100`

The `Lever.review_lever` field description still reads:
```
"Two sentences. First sentence names the core tension this lever controls.
Second sentence identifies a weakness the options miss.
Example: 'Controls centralization vs. local autonomy.
Weakness: The options fail to account for transition costs.'"
```
This is the **old format**. PR #316 updated the external prompt file (`prompt_6`) to use a single flowing example:
> "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs."

But it left the Pydantic field description unchanged. When llama_index submits a structured LLM request, the field descriptions are part of the JSON schema sent to the model. The model therefore simultaneously sees:

- System prompt (from the external file): *new* single-sentence example
- Field schema description: *old* "Two sentences … Weakness:" instruction

These conflict. For a weak model like llama3.1, whichever format appears most frequently or most recently in the context tends to win. The fact that runs 60–66 all followed the new template suggests the system prompt dominated, but the conflict is a source of confusion for call-1 validations and template leakage.

**Fix:** Update the `review_lever` field description on `Lever` to match the new single-sentence format used in prompt_6.

---

### B2 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (hardcoded default) not updated
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:216–218`

The hardcoded constant `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` still contains:
```
- For `review_lever` (one field, two sentences):
  First sentence names the core tension. Second sentence identifies a weakness.
  Example: "Controls centralization vs. local autonomy. Weakness: The options fail to account for transition costs."
```
This is the **old prompt_5 text**. Any call to `IdentifyPotentialLevers.execute()` without an explicit `system_prompt=` argument (e.g., the `__main__` block, unit tests, or any caller that omits the parameter) will use the old format and produce different behaviour from runner-produced results.

The PR only changed the external prompt files; the hardcoded fallback was never updated. This creates a silent divergence between production runs (which use `--system-prompt-file`) and standalone test runs (which use the default constant).

**Fix:** Update `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` to match prompt_6, so the default and the external file agree.

---

### B3 — `set_usage_metrics_path()` called outside the thread lock (race condition)
**File:** `self_improve/runner.py:107`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # line 107 — no lock
with _file_lock:
    dispatcher.add_event_handler(track_activity)                   # line 109-110 — has lock
```

The comment at lines 98–99 says: _"set_usage_metrics_path and the dispatcher are global state, so we hold a lock while configuring"_ — but `set_usage_metrics_path` is called **before** and **outside** the lock block. When `workers > 1`, two threads can concurrently overwrite the global metrics path, causing one plan's LLM usage events to be written to another plan's `usage_metrics.jsonl`. The dispatcher handler addition is protected; the global path setter is not.

In practice this bug is latent for `ollama-llama3.1` because `_resolve_workers` returns 1 for that model. But it would activate for any model with `luigi_workers > 1`.

**Fix:** Move `set_usage_metrics_path(...)` inside the `with _file_lock:` block, alongside `dispatcher.add_event_handler`.

---

## Suspect Patterns

### S1 — Global dispatcher collects events from ALL concurrent threads
**File:** `self_improve/runner.py:109–116`

Each call to `run_single_plan` adds its `TrackActivity` handler to the llama_index global dispatcher via `dispatcher.add_event_handler(track_activity)` and removes it in the `finally` block. However, `IdentifyPotentialLevers.execute()` runs **outside** the lock:

```
add_event_handler(track_activity_A)  [lock held briefly]
                                         add_event_handler(track_activity_B)  [lock held briefly]
execute(...)  -- fires events → captured by BOTH handler A and handler B
                                         execute(...)  -- fires events → captured by BOTH
```

With `workers > 1`, every plan's `track_activity.jsonl` would contain a superset of all concurrent plans' events, not just its own. The `track_activity_path.unlink(missing_ok=True)` at line 153 deletes the file afterwards, so this probably doesn't affect correctness of the final output — but it defeats the purpose of per-plan tracking.

---

### S2 — Full `user_prompt` appended twice in calls 2 and 3
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:270–277`

For `call_index > 1` the prompt is:
```python
prompt_content = (
    f"Generate 5 to 7 MORE levers ... [{names_list}]\n"
    ...
    f"{user_prompt}"        # ← full plan content repeated again
)
```
The `user_prompt` holds the concatenation of three input files (plan.txt + purpose.md + plan_type.md). For large plans this can be several thousand tokens, doubled unnecessarily on every call after the first. It also means call-2 and call-3 messages are significantly longer than call-1, which could bias models toward shorter outputs to fit within context limits.

Additionally, the quality constraint _"at least 15 words with an action verb"_ appears only in the call-2+ prefix and is absent from the call-1 user message. This inconsistency means call-1 options face looser enforcement than call-2+ options.

---

### S3 — `LeverCleaned.review` description also has old "Weakness:" format
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:186–194`

The `LeverCleaned` class (output model, never sent to the LLM) still has the old field description. This is not a functional bug but shows the cleanup from PR #316 was incomplete — three places had the old format and only one (the external prompt file) was changed.

---

### S4 — `min_length=5` on `levers` may cause unnecessary validation failures for later calls
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:154`

```python
levers: list[Lever] = Field(
    min_length=5,
    description="Propose 5 to 7 levers."
)
```
The system prompt and user prompt both ask for 5–7 levers. For calls 2 and 3, the model is told to generate levers "with completely different names" from the already-generated set. For plans with limited strategic scope, the model may genuinely have fewer than 5 novel levers to propose. Pydantic will reject the entire call-2/3 response if it contains 4 levers, triggering a `partial_recovery` even when those 4 levers are perfectly valid. There is no `max_length` (intentionally, per the comment at lines 150–152), so the asymmetry in treatment is odd.

---

### S5 — `strategic_rationale: null` accepted silently across all calls
**File:** `worker_plan/worker_plan_internal/lever/identify_potential_levers.py:146–148`

```python
strategic_rationale: Optional[str] = Field(
    default=None,
    description="..."
)
```
Every run-60 call-1 response shows `strategic_rationale: null`. There is no warning or soft alert when this field is missing. The field was designed to verify that lever selection is intentional rather than arbitrary, but its absence is invisible in logs and outputs. If it is always null for llama3.1, it contributes nothing and the description creates noise in the schema that the model reads.

---

## Improvement Opportunities

### I1 — Add validator for label-style options (addresses N3)
**File:** `identify_potential_levers.py` — `Lever` class

The `check_option_count` validator (lines 115–126) only checks that exactly 3 options are present. It does not verify that options are substantive. Options like `"Hub-and-Spoke"`, `"Satellite Studios"`, `"Co-Working Spaces"` (run 60, gta_game call-1) are 1–3 word labels with no verb — exactly what the prompt prohibits. A validator that rejects options shorter than ~8 words or lacking a verb would catch these at schema validation time and trigger a retry, consistent with how `check_option_count` already works.

The validator should be structural (word count / presence of any character from the set a-z after the first 5 chars), not English-keyword-based, to avoid breaking non-English plans per OPTIMIZE_INSTRUCTIONS.

---

### I2 — Add validator that detects verbatim copy of the example string (addresses N2)
**File:** `identify_potential_levers.py` — `Lever` class

Run 60, gta_game lever "Location Strategy" has its `review` field set to the exact example string from section 4 of the system prompt:
> "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs."

A validator could check that `review_lever` does not contain the substring `"centralization and local autonomy"` (the tell-tale phrase unique to the prompt example). More robustly: compute the Levenshtein edit distance from any known example string; if it is below a threshold (e.g., ≤ 10 edits), reject it.

This is addressed as **C1** in the insight. The check must be done at the Pydantic level (per-lever, `mode='after'`) and use a list of known example strings to compare against.

---

### I3 — Provide 2–3 varied review examples to break template lock (addresses N1)
**File:** External prompt file (prompt_6 → future prompt_7)

All 17–20 reviews in runs 60–66 start with "This lever governs/manages the tension between X and Y, but…". This is expected: llama3.1 pattern-matches on the single example and applies it universally. No code change can fix this; the prompt must change.

Providing two or three structurally different examples would force the model to engage with the concept rather than copy the syntax:
- Example A: "This lever governs the tension between X and Y, but the options overlook Z."
- Example B: "The choice here is whether to prioritize X or Y; the current options ignore Z entirely."
- Example C: "X and Y pull in opposite directions. None of the options address Z, which could undermine either path."

Adding explicit prohibition: "Do not begin every review with 'This lever governs the tension between'" would be addressed by **H2** in the insight.

---

### I4 — Document or remove the `summary` field from `DocumentDetails`
**File:** `identify_potential_levers.py:157–159`

```python
summary: str = Field(
    description="One sentence prescribing a concrete addition to a specific lever. ..."
)
```

`summary` is required in the Pydantic schema (non-optional, no default), so the LLM must generate it and the model devotes tokens to it. However, `to_dict()`, `save_raw()`, `save_clean()`, and `lever_item_list()` all show that `summary` is recorded in the raw JSON (because `response.model_dump()` includes it) but is **never surfaced in the final lever output**. It is a required schema field that consumes model attention and token budget with no downstream effect. Either use it (e.g., append it as a lever-improvement suggestion) or remove it from the schema.

---

### I5 — OPTIMIZE_INSTRUCTIONS should document the "single example → single template" failure mode
**File:** `identify_potential_levers.py:27–68`

The `OPTIMIZE_INSTRUCTIONS` block documents five known problems. A sixth should be added:
> **Single-example template lock**: When the prompt provides exactly one format example, small models (llama3.1, llama3 family) reproduce that exact syntax in every output, eliminating diversity. Provide ≥ 2 structurally varied examples, or add an explicit do-not-copy prohibition. Evidence: runs 60–66, 95%+ of reviews start with the same 10-word prefix matching the single example.

---

## Trace to Insight Findings

| Insight finding | Code location | Mechanism |
|---|---|---|
| **N1** — 95% template lock on "This lever governs the tension between…" | `Lever.review_lever` field description (L92–100) still says "Two sentences … Weakness:…" while external prompt says single sentence. Model latches on the system-prompt example exclusively. Single example → single template. | B1 causes conflicting instructions; I3 is the fix. |
| **N2** — Verbatim copy of prompt example in run 60 gta_game | No guard against copying the example string verbatim. The example appears in the system prompt at a global level; call-1 sees it before generating levers. | I2 proposes a validator. |
| **N3** — Label-style options ("Hub-and-Spoke", "Satellite Studios") | `check_option_count` (L115–126) only validates count==3; no quality check on option length or verb presence. | I1 proposes a length/verb validator. |
| **N4** — Near-duplicate lever names ("Partnership Model", "Partnership Structure", "Partnership Ecosystem") | Deduplication at L331–337 is exact-name only. Near-duplicates pass through. By design (downstream `DeduplicateLeversTask` handles them), but the comment at L3–5 should be explicit that near-duplicates in the raw output are expected and acceptable. | S3 describes this; no code change needed given the pipeline design. |
| **N5** — Run 60 partial_recovery (2/5 plans had calls_succeeded=2) | Two sources: (a) conflicting format instructions (B1) cause validation failure on some call-1 responses; (b) llama3.1 may interpret the JSON schema field description ("Two sentences…") as the authoritative format and produce a two-sentence string that fails the new single-sentence expectation. | B1 is the primary code-level cause. |
| **N6** — `strategic_rationale: null` in all call-1 responses | Field is `Optional[str]` with `default=None`; no warning when null. llama3.1 systematically ignores it. | S5 notes this; I4-adjacent fix (remove or require the field). |
| **Q1** (insight question) — Was `partial_recovery` logging added with PR #316? | `partial_recovery` event is in `runner.py:331–335` and `PlanResult.calls_succeeded` at L75. The runner file is separate from the Pydantic schema. Runs 53–59 had no `calls_succeeded` logged because the field didn't exist in the old `PlanResult`. The PR likely added the logging alongside or after the prompt fix. | Runtime observation, not a code bug. |

---

## PR Review

### What PR #316 Actually Changed

Comparing prompt_5 (SHA `9c5b2a0d`) vs prompt_6 (SHA `4669db37`), the PR changed exactly **one section** in the external prompt file — section 4 "Validation Protocols":

**Before (prompt_5):**
```
- For `review_lever` (one field, two sentences):
  First sentence names the core tension. Second sentence identifies a weakness.
  Example: "Controls centralization vs. local autonomy. Weakness: The options fail to account for transition costs."
```

**After (prompt_6):**
```
- For `review_lever` (one field, two sentences):
  A short critical review — name the core tension, then identify a weakness the options miss.
  Example: "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs."
```

### What Was NOT Changed (the gap)

1. **`Lever.review_lever` Pydantic field description** (L92–100): Still says `"Two sentences. First sentence names the core tension… Example: 'Controls centralization vs. local autonomy. Weakness: …'"` — the old format verbatim. Since llama_index's structured LLM implementation sends field descriptions as part of the JSON schema, the model simultaneously receives the new system-prompt example and the old schema-level description. These directly contradict each other.

2. **`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`** (L196–235): The hardcoded default constant was not updated; it still contains the old two-sentence format. Any call path that doesn't pass an external prompt file (test scripts, `__main__` block, future callers) will use the old instructions.

3. **`LeverCleaned.review` field description** (L186–194): Still has old format (lower priority — LLM never sees this class).

### Does the PR Fix the Claimed Problem?

Partially yes. Removing the explicit "First sentence…/Second sentence…" bullets in the system prompt reduces the structural ambiguity that caused llama3.1 to produce two alternative formats. The runs 61–66 show 0 partial recoveries, consistent with fewer schema validation failures.

**However**, the PR introduced a schema contradiction (B1) that it didn't close: the Pydantic field description still says "Two sentences" and uses the old "Weakness:" example. For llama3.1, the system prompt won this conflict (resulting in the new template), but the conflict is the root cause of:
- Why run 60 still had 2 partial recoveries (the first run with the new prompt, before the model's context warmed up / before the new format became dominant)
- Why the verbatim copy happened (the single example in the system prompt was the only unambiguous signal the model had to latch onto)

### Specific Code Issue in the PR

The PR description says it replaced the format in both the **field description** and the **system prompt**. Based on the code:
- External prompt file: ✅ updated
- Pydantic `Lever.review_lever` field description: ❌ not updated (still old format)
- Hardcoded `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`: ❌ not updated (still old format)

The PR is incomplete. The intent was correct, the prompt file edit was correct, but the Pydantic schema edit was missed.

---

## Summary

### Confirmed Bugs

| ID | Severity | Location | Description |
|---|---|---|---|
| B1 | High | `identify_potential_levers.py:92–100` | `Lever.review_lever` Pydantic field description uses old "Two sentences/Weakness:" format — contradicts new prompt_6 example, confusing the model |
| B2 | Medium | `identify_potential_levers.py:216–218` | Hardcoded `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` not updated; diverges from external prompt files used in production |
| B3 | Low (latent) | `runner.py:107` | `set_usage_metrics_path()` called outside the thread lock; race condition with `workers > 1` |

### Key Improvement Opportunities

| ID | Description | Addresses Insight |
|---|---|---|
| I1 | Validate option length/verb presence; reject short labels | N3 |
| I2 | Validator to detect verbatim copy of known example strings | N2 |
| I3 | Provide ≥2 structurally varied `review_lever` examples in the prompt | N1 |
| I4 | Remove or require `DocumentDetails.summary` (currently always discarded) | — |
| I5 | Add "single-example template lock" to `OPTIMIZE_INSTRUCTIONS` known-problems list | N1, N2 |

### Overall PR Assessment

PR #316 correctly identified the root cause of call-1 format failures (two-bullet example → ambiguous alternating format for llama3.1) and correctly fixed the external prompt file. The fix is directionally right and its effects are visible in the data (runs 61–66: 0 partial recoveries, clean single-sentence reviews).

The PR is **incomplete** because it did not update the Pydantic `Lever.review_lever` field description (B1), which continues to send the old two-sentence "Weakness:" format to every structured LLM call as part of the JSON schema. This residual conflict is the most likely code-level cause of:
- The single-template lock (model latches on the one unambiguous example in the system prompt)
- The verbatim copy in run 60 (model had no other anchor)
- The run 60 partial recoveries (schema conflict on call-1)

**Recommended follow-up:** Update `Lever.review_lever` description and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` to match prompt_6, then run the next iteration with 2–3 varied examples (I3) to break the template lock.
