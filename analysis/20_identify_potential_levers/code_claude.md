# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py` — main branch (pre-PR)
- `.claude/worktrees/silly-purring-lovelace/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` — PR #309 branch
- `prompt_optimizer/runner.py` — main branch

---

## Bugs Found

### B1 — `break` on partial failure silently drops call 3 (main branch, line 278)

```python
# main branch identify_potential_levers.py:278
break
```

When call 2 raises any exception (including a Pydantic `ValidationError` from a single malformed lever), the loop breaks. Call 3 is never attempted. The caller receives only call 1's levers — roughly 7 instead of ~18 — with no warning beyond an INFO-level log. The PR branch changes this to `continue`, which allows call 3 to proceed independently of call 2's failure. This directly explains insight_codex C3: "fewer than 3 raw calls returned in some outputs" with no `LLMChatError` in `events.jsonl`. The `break` path exits silently without emitting an error event.

**PR #309 fix**: changes line 278 `break` → `continue` (worktree line 318).

---

### B2 — `check_review_format` uses English-only keyword validation (main branch, lines 95–98)

```python
# main branch identify_potential_levers.py:95–98
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if 'Weakness:' not in v:
    raise ValueError("review_lever must contain 'Weakness: ...'")
```

These substring checks break silently for any non-English prompt. A French, Japanese, or Arabic plan that produces a structurally valid two-sentence review without the English words "Controls" or "Weakness:" will be rejected, causing a LLMChatError that wraps the ValidationError. PlanExe explicitly receives plans in many languages (noted in `OPTIMIZE_INSTRUCTIONS` in the PR branch). This is the root cause documented in insight_claude C1 and is also why runs 46–52 pass validation with non-"Controls" reviews: those runs executed the PR branch code, not the main branch.

**PR #309 fix**: replaces keyword checks with structural checks — min 20 characters, no square-bracket placeholders (worktree lines 128–143).

---

### B3 — `consequences` schema description mandates fabricated quantification (main branch, lines 36–45)

```python
# main branch identify_potential_levers.py:36–39
"Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
...
"All three labels and at least one quantitative estimate are mandatory. "
```

The Pydantic field description is rendered verbatim into the structured output schema that the LLM receives. Mandating "at least one quantitative estimate" with "e.g. a % change or cost delta" directly instructs the model to invent numbers when the project context provides none. This is the code-level root cause of fabricated values like "90% waste reduction" (N7 in insight_claude) and the 24 unsupported percentage claims across analysis/20 outputs.

The same instruction appears in `LeverCleaned.consequences` at main branch lines 130–138 — but `LeverCleaned` is only used for output serialization, not for LLM generation, so it has no runtime impact on model behavior. Only `Lever.consequences` (lines 36–45) feeds the structured LLM call.

**PR #309 fix**: replaces the forced-quantification description with "Be concise and grounded — only cite numbers if the project context provides evidence for them" (worktree lines 80–87).

---

### B4 — System prompt forces "conservative → moderate → radical" triad and mandates emerging tech (main branch, lines 169–193)

```python
# main branch identify_potential_levers.py:169–170, 193
"• Show clear progression: conservative → moderate → radical"
"• Radical option must include emerging tech/business model"
```

"Conservative → moderate → radical" forces all options into a single dimensional axis. Options that don't fit the triad (e.g., a lateral pivot vs. a phased rollout) cannot be expressed. "Radical option must include emerging tech/business model" is a direct driver of the "cutting-edge" and "blockchain" violations seen in runs 47 (N5, N6 in insight_claude). The model follows the instruction but produces banned marketing language because the instruction itself requires tech-forcing.

The system prompt also still mandates "Include measurable outcomes: … a % change, capacity shift, or cost delta" at line 164, compounding B3.

**PR #309 fix**: removes both requirements (worktree lines 204–235 system prompt has neither instruction).

---

## Suspect Patterns

### S1 — `messages_snapshot` closure captures loop-local state (main branch, lines 247–257; worktree lines 287–297)

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

`execute_function` closes over `messages_snapshot`. If `llm_executor.run()` were ever to defer execution (e.g., queue it for a thread pool or retry on a different thread), the closure would capture the list reference rather than a deep copy. Since both the main and PR branches call `sllm.chat(messages_snapshot)` synchronously inside `run()`, this is not a current bug — but it is fragile. If `LLMExecutor.run()` ever becomes asynchronous, `messages_snapshot` could be mutated between capture and use. A defensive copy (`list(messages_snapshot)`) inside the closure would eliminate the risk.

---

### S2 — `set_usage_metrics_path` called outside the file lock in runner.py (lines 106–114)

```python
# runner.py:106–114
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")

with _file_lock:
    dispatcher.add_event_handler(track_activity)

...
result = IdentifyPotentialLevers.execute(...)
```

The comment at lines 97–98 says "set_usage_metrics_path and the dispatcher are global state, so we hold a lock while configuring and running." However, `set_usage_metrics_path` is called before the lock is acquired, and `IdentifyPotentialLevers.execute()` runs entirely outside the lock. When `workers > 1`, two threads can race on the global path: Thread A sets path to `plan_A/usage_metrics.jsonl`, Thread B overwrites it with `plan_B/usage_metrics.jsonl`, and Thread A's metrics are written to plan_B's directory. Only `dispatcher.add_event_handler` is protected. For local models (`workers=1`, all llama3.1 runs) this is harmless; for multi-worker API model runs it silently corrupts per-plan usage data.

---

### S3 — History counter has a TOCTOU window (runner.py, lines 257–285)

```python
def _next_history_counter(history_dir: Path) -> int:
    """Scan history/ for the highest existing run number and return +1."""
```

`_next_history_counter` scans the filesystem and returns `max + 1`, but this is not atomic with the subsequent `mkdir`. If two `runner.py` processes start concurrently (e.g., analysis pipeline running two models simultaneously), both could scan, see the same max, and create the same run directory. In practice the analysis pipeline serializes runs, so this is low risk — but it would cause silent overwrite of a prior run's outputs if it ever triggered.

---

### S4 — `lever_index` in `Lever` schema is never validated or used (main and PR branch, line 28)

```python
lever_index: int = Field(description="Index of this lever.")
```

`lever_index` is accepted from the LLM but never read in any code path. The cleaned output uses a UUID `lever_id` instead. The field wastes token budget and gives the LLM an opportunity to produce non-sequential indexes or hallucinate "index" semantics. It also creates a mismatch: the LLM might use `lever_index` to reason about ordering, but the final output ignores it entirely.

---

## Improvement Opportunities

### I1 — Add anti-fabrication reminder alongside the sentence-completeness reminder in call-2/3 prompts

The PR branch adds (worktree line 274):
```
Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.
```

Insight_codex H2 and the quantitative data (24 unsupported percentage claims in after-runs) suggest that a companion line would reduce fabricated numbers in later calls:

```
Do not invent percentages, cost savings, or performance deltas — use qualitative language unless the project document supplies the number.
```

This mirrors the `OPTIMIZE_INSTRUCTIONS` warning (worktree lines 51–55) and the system-prompt prohibition (worktree line 228) but restates it inline at the point where attention has shifted to the exclusion blacklist. Same rationale as the sentence-completeness reminder: restate the most important quality rule where attention needs it most.

---

### I2 — Add a minimum-word-count validator for options alongside `check_option_count`

```python
# worktree identify_potential_levers.py:115–126 (check_option_count)
```

The PR prompt instruction says "at least 15 words with an action verb" but this is unenforced in code. A post-generation validator that counts words per option and logs a warning (without rejecting) would make call-3 option depth regressions measurable before they accumulate. Insight_codex C1 proposes rewrite-or-drop behavior; a softer first step is a warning-level log with the word count, enabling the analysis pipeline to track the metric without risking new retry loops.

---

### I3 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant (main branch) should be kept in sync with prompt_5

The main branch constant at lines 154–196 still contains:
- "Show clear progression: conservative → moderate → radical" (line 169)
- "Radical option must include emerging tech/business model" (line 193)
- Mandatory measurable outcomes with % / cost delta (line 164)

The PR branch updates the constant to match prompt_5 (worktree lines 196–235). Until the PR is merged, anyone who runs `python -m worker_plan_internal.lever.identify_potential_levers` directly (the `__main__` block at main branch line 348) gets the old prompt, which the optimization loop has documented as a fabrication and marketing-language driver.

---

### I4 — `DocumentDetails.summary` description drives verbose, formulaic output (main branch, line 114)

```python
# main branch:114
description="Are these levers well picked? Are they well balanced? ... Point out flaws. 100 words."
```

A vague "100 words" target with multiple rhetorical questions gives models room to generate padded meta-commentary that consumes tokens without adding decision-relevant content. The PR branch tightens this to a one-sentence actionable prescription (worktree line 158). Even outside PR #309, aligning the main-branch `summary` description with the PR branch version would reduce token waste.

---

## Trace to Insight Findings

| Insight observation | Code location | Root cause |
|---|---|---|
| N7 — "90% waste reduction" fabrication (llama3.1 silo) | main branch `Lever.consequences` lines 36–45 | B3: field description mandates quantitative estimate, forcing invention when context has none |
| N5 — "cutting-edge" in gpt-oss-20b gta | main branch system prompt line 193 | B4: "Radical option must include emerging tech/business model" drives tech-forcing |
| N6 — "(note: not allowed)" annotation in gpt-oss-20b | main branch system prompt line 193 | B4: same tech-forcing instruction; model tries to comply, self-censors, includes annotation |
| N2 — llama3.1 non-"Controls" review format passes validation | main branch lines 95–98 vs worktree 128–143 | B2: runs 46–52 used worktree (PR branch) with structural validator; main branch would reject these |
| C1 (insight_claude) — validator state contradiction | main branch lines 95–98 | B2: main branch has old English-only validator; runs used PR branch code |
| C2 (insight_claude) — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` out of date | main branch lines 154–196 | B3, B4, I3: constant not updated to match prompt_5 |
| Codex C3 — some outputs missing call 3, no LLMChatError | main branch line 278 | B1: `break` exits loop silently; PR branch `continue` allows call 3 after call 2 failure |
| Codex metric: 24 % claims after PR | Both branches: missing call-2/3 anti-fabrication reminder | I1: sentence reminder added but no anti-fabrication reminder in call-2/3 prompts |
| N1 — call-3 option depth shallower than call-1 for llama3.1 | Both branches: no word-count enforcement | I2: "at least 15 words" is prompt-only, no code-level enforcement |

---

## PR Review

### What PR #309 changes (diff between main and worktree)

**Change 1 — Call-2/3 sentence-completeness reminder** (worktree line 274):
```python
# Before (main branch line 233):
f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
f"{user_prompt}"

# After (worktree lines 273–275):
f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
f"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n\n"
f"{user_prompt}"
```

**Change 2 — `break` → `continue` for partial-failure error handling** (worktree line 318 vs main line 278).

**Also in the worktree (from prior PRs)**: `OPTIMIZE_INSTRUCTIONS` constant, structural `check_review_format`, updated system prompt, simplified `summary` description, updated `consequences` schema.

---

### Assessment of Change 1 (sentence-completeness reminder)

The implementation is correct and well-placed. The reminder appears immediately after the exclusion blacklist — the exact attention-decay point documented in the PR description — and immediately before the original user prompt. This positioning maximizes the chance that the reminder is in the model's active attention window during option generation.

The phrase "at least 15 words with an action verb" is concrete and measurable. Experiment results confirm it works: llama3.1 call-3 short-label rate drops from 46% to 0%.

**Gap**: the reminder addresses sentence completeness but not fabrication. Given that unsupported percentage claims persist after the PR (24 in after-runs vs 20 before), adding a companion anti-fabrication line would extend the same repair pattern to the second-most-common quality problem.

**No regressions introduced**: inserting a line between the blacklist and the user prompt does not change the structural contract (system prompt, schema, validators). Models that already produce full sentences are unaffected, as confirmed by runs 46–51.

---

### Assessment of Change 2 (`break` → `continue`)

`break` was silently dropping call 3 whenever call 2 failed with a validation error (e.g., a single malformed lever). `continue` is strictly better: call 3 proceeds even if call 2 fails, yielding more levers without the risk of further failures contaminating the result.

**One subtle side effect**: when call 2 fails and `continue` is used, `generated_lever_names` does not include any names from call 2 (there are none — call 2 failed). Call 3's exclusion list is therefore shorter than it would be if call 2 had succeeded. This means call 3 might generate names that would have collided with a successful call 2. However, the `seen_names` deduplication at lines 330–336 (worktree) catches any actual duplicates in the final output, so this is not a correctness bug — just a minor efficiency consideration.

**Explains C3**: the `continue` change is the most plausible explanation for insight_codex's observation that "previous runs had 34 third-call responses, while current runs have 33." With `break`: call 2 failure → loop exits, no call 3 attempted → no third-call response. With `continue`: call 2 failure → call 3 attempted → call 3 may itself fail → still no third-call response. The `continue` branch can create a scenario where call 2 fails (previously would have broken the loop early) and call 3 also fails independently, producing a net count of 1 response. This is a new failure mode that did not exist with `break`, but it is rare and the outcome (1 response instead of 3) is no worse than the `break` case.

---

### PR #309 verdict: **KEEP, with one suggestion**

The PR correctly and measurably fixes the targeted problem. Both changes are sound. The one recommendation is to add an anti-fabrication sentence alongside the sentence-completeness reminder (I1 above), since the quantitative data shows fabricated numbers persist and the same mechanism (attention-decay after a growing blacklist) applies to both problems. Adding it would not require re-running experiments — it extends the same fix pattern to the next most common quality issue.

---

## Summary

The main branch (`identify_potential_levers.py`) has four confirmed bugs that explain the quality problems documented in the insight files:

- **B1** (`break` on partial failure, line 278): silently drops call 3 after call 2 validation failure — explains missing third-call responses with no LLMChatError
- **B2** (English-only `check_review_format`, lines 95–98): rejects valid non-English reviews, breaks when PlanExe receives non-English plans
- **B3** (mandatory quantitative estimates in `consequences` schema, lines 36–45): directly drives fabricated percentages and cost deltas
- **B4** (conservative/moderate/radical triad + mandatory emerging tech, lines 169, 193): drives "cutting-edge" violations and homogenizes option structure

PR #309 (worktree) correctly fixes all four and adds the primary targeted fix (sentence-completeness reminder in call-2/3 prompts). The PR also incorporates `OPTIMIZE_INSTRUCTIONS` documentation, a structural-only `check_review_format`, and an updated system prompt that removes fabrication-forcing instructions — a comprehensive upgrade that matches what the optimization loop has learned across analyses 17–20.

The primary remaining gap after PR #309 is the absence of an anti-fabrication reminder in call-2/3 prompts (I1), and the lack of a code-level word-count check to make option-depth regressions measurable without relying solely on manual analysis (I2).
