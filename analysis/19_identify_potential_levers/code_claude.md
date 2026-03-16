# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

---

## Bugs Found

### B1 — Source checkout not synced with PR #299 (identify_potential_levers.py)

The three changes PR #299 claims to have made are **absent** from the current source tree. The checkout still contains the pre-PR code on all three targets:

**B1a — English-only validator still in place (lines 95–98)**

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if 'Weakness:' not in v:
    raise ValueError("review_lever must contain 'Weakness: ...'")
```

This Pydantic `field_validator` runs during every LLM response parse, regardless of which system prompt file is passed via `--system-prompt-file`. Any model that writes "Balances X vs. Y" instead of "Controls X vs. Y" will have its entire `DocumentDetails` response rejected and a `ValidationError` raised. Since the validator is at the field level (inside `Lever`), the whole call fails, not just the individual lever. This means:

- Under the current checkout, the "Balances"-format reviews from qwen3 (run 38) and gpt-4o-mini (run 41) that analysis/19 reports would have been **rejected at parse time** and the call would have raised a `ValidationError` caught as `LLMChatError`.
- The analysis/19 experimental results could only have been produced against a patched version. The production code on this branch is still fragile and non-i18n-safe.

**B1b — Bracket placeholders still in `review_lever` field description (lines 54–57)**

```python
description=(
    "Required format: Two sentences. "
    "Sentence 1: 'Controls [Tension A] vs. [Tension B].' "
    "Sentence 2: 'Weakness: The options fail to consider [specific factor].' "
    "Both sentences are mandatory in every response."
)
```

The `[Tension A]`, `[Tension B]`, and `[specific factor]` placeholders are part of the Pydantic field description. With structured LLM output (llamaindex's `as_structured_llm`), the field descriptions are serialised into the JSON schema that accompanies each chat request. A model that faithfully follows the schema example will echo the bracket text verbatim — exactly the failure mode documented in run 19 (6 placeholder levers in gta_game).

**B1c — `LeverCleaned.review` also has stale placeholder descriptions (lines 148–151)**

Same bracket placeholders as `Lever.review_lever`. `LeverCleaned` is populated programmatically (lines 299–304), so the field descriptions don't affect LLM output here — but if this class were ever used as a structured output type in a future refactor, it would immediately regress.

**B1d — `summary` description not aligned with prompt_4/5 format (lines 113–115)**

```python
description="Are these levers well picked? Are they well balanced? Are they well thought out? Point out flaws. 100 words."
```

PR #299 was supposed to align this with the one-sentence "Add…" format. The current description invites a free-form 100-word critique, which accounts for the 90/105 bad-summary rate seen in analysis/18 before the fix was applied.

**B1e — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` still has placeholder markers (lines 179–180)**

```python
"     • State the trade-off explicitly: \"Controls [Tension A] vs. [Tension B].\"\n"
"     • Identify a specific weakness: \"Weakness: The options fail to consider [specific factor].\"\n"
```

When the runner is invoked **without** `--system-prompt-file` (e.g., in the `__main__` block or direct programmatic calls), this constant is used as the system prompt. The bracket placeholders in the Validation Protocols section would then appear as literal format strings that instruct the model to keep the bracket text, recreating the template-leakage failure mode.

---

### B2 — Race condition on global usage-metrics path (runner.py lines 106, 140)

```python
# line 106 — outside the lock
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")

with _file_lock:                          # line 108
    dispatcher.add_event_handler(track_activity)
```

```python
finally:
    set_usage_metrics_path(None)          # line 140 — outside the lock
    with _file_lock:
        dispatcher.event_handlers.remove(track_activity)
```

`set_usage_metrics_path()` writes to a global (module-level) variable. When `workers > 1` and `run_single_plan` is called from multiple threads concurrently:

- Thread A calls `set_usage_metrics_path(path_A)`.
- Thread B immediately calls `set_usage_metrics_path(path_B)`, overwriting Thread A's path.
- Thread A's LLM execution now logs to `path_B`.
- In the `finally` block, Thread B calls `set_usage_metrics_path(None)` while Thread A is still running, silencing Thread A's metrics.

The `_file_lock` guards only the dispatcher mutation, not the path assignment. Parallel runs (`workers > 1`) could silently cross-contaminate or lose usage metrics. This is currently masked because llama3.1 (the only model tested with potential parallel demand) is pinned to `workers=1`.

---

### B3 — `consequences` field mandates fabricated quantification (lines 37–39, 164)

```python
"Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta]"
"All three labels and at least one quantitative estimate are mandatory. "
```

And in the system prompt constant (line 164):
```python
"     • Include measurable outcomes: \"Systemic: [a specific, domain-relevant "
"second-order impact with a measurable indicator, such as a % change, capacity "
"shift, or cost delta]\""
```

The word **mandatory** combined with the `% change` example is a direct instruction to fabricate numbers. The codex insight reports 20 fabricated-percentage claims in analysis/19 outputs, 18 of which are from haiku — the most instruction-following model. This instruction is the root cause: haiku obeys "mandatory quantitative estimate" more faithfully than other models, producing invented thresholds like "70%" and "4–8 weeks" in parasomnia output.

---

### B4 — Multi-call prompt drops quality reinforcement (lines 231–236)

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```

Calls 2 and 3 prepend only the name-exclusion instruction. The `user_prompt` (from the plan file) is repeated but the **quality constraints** for options (full sentence with an action verb, not a label) are not re-stated. The `system_message` still carries the quality rules, but system prompt attention decays as context grows. This is the direct mechanism for the llama3.1 label-only option degradation: call-1 options are substantive because quality instructions are prominent; call-2 and call-3 have a longer prefix crowding them out. The degradation rate (~33–38% of levers across two analysis batches) is stable, which means the problem is structural rather than stochastic.

Additionally, the names list is wrapped in square brackets: `[{names_list}]`. If a future prompt variant adds a rule like "reject square brackets in any field", this would conflict with the anti-duplication mechanism.

---

## Suspect Patterns

### S1 — C→M→R triad required but labels forbidden (lines 168–169, 186)

```python
"     • Show clear progression: conservative → moderate → radical\n"
...
"   - NO prefixes/labels in options (e.g., \"Option A:\", \"Choice 1:\", "
      "\"Conservative:\", \"Moderate:\", \"Radical:\")\n"
```

The system prompt simultaneously demands the conservative→moderate→radical structural progression (line 169) and forbids the label prefixes that would normally encode it (line 186). Models that follow both rules produce options that are structurally ordered but not labelled — which works for well-understood levers, but forces an artificial triad structure onto levers that might naturally have two or four distinct approaches. The codex insight still counts 5 triad-template term hits in analysis/19.

### S2 — `Radical option must include emerging tech/business model` (line 193)

```python
"   - Radical option must include emerging tech/business model\n"
```

This constraint applies universally across all lever types in all plan domains. For a silo's "Population Expansion vs. Finite Resources" lever, the radical option doesn't naturally involve emerging tech. This instruction pushes models toward marketing-adjacent language ("cutting-edge AI integration", "disruptive platform") to satisfy the requirement.

### S3 — Closure captures loop variable by reference (lines 247–257)

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

`execute_function` closes over `messages_snapshot` by name, not by value. This is safe because `llm_executor.run(execute_function)` is called synchronously on line 260 before the next iteration reassigns `messages_snapshot`. However, if `LLMExecutor.run()` were ever changed to defer or memoize the callable, the closure would capture the final loop value for all calls. The safer pattern is to pass `messages_snapshot` as a default argument: `def execute_function(llm, _msgs=messages_snapshot)`.

### S4 — `_next_history_counter` is not process-safe (runner.py lines 258–274)

The counter is computed by scanning the filesystem and returns `max + 1`. If two runner invocations start in parallel (e.g., in a CI matrix), they may compute the same counter and create the same history directory, causing one run to overwrite the other's outputs. A file-based lock or UUID suffix on the directory name would eliminate the window.

---

## Improvement Opportunities

### I1 — Reinforce option quality in call-2/3 prompt (lines 231–236)

Append a one-line reminder to the multi-call prompt:

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    f"Each option must be a complete strategic sentence (≥15 words with an action verb), not a label.\n\n"
    f"{user_prompt}"
)
```

Hypothesis H2 from analysis/18 and analysis/19 predicts this would fix the llama3.1 label-only degradation (currently ~33–38% of levers in call-2/3) without affecting other models that already produce complete options.

### I2 — Add `OPTIMIZE_INSTRUCTIONS` constant

Neither file contains the `OPTIMIZE_INSTRUCTIONS` constant referenced in the AGENTS.md. This constant was supposed to encode the quality goals (no bracket placeholders, no fabricated %, no marketing copy, no cross-call name repetition) so future prompt iterations have an auditable policy target. Without it, each reviewer and code author has to reconstruct the policy by reading the insight files.

### I3 — Soften the quantitative-estimate mandate in `consequences`

Replace "All three labels and at least one quantitative estimate are mandatory" with "Prefer concrete, grounded comparisons over fabricated percentages. Use specific numbers only when they appear in the source document." This would reduce haiku's 18 fabricated-percentage hits (the bulk of the remaining 20 in analysis/19) without removing the instruction to be specific.

### I4 — Remove `Radical option must include emerging tech/business model`

Replace with "Include at least one option that challenges the plan's core assumption." This is less prescriptive and produces the same analytical value without pushing toward marketing language.

### I5 — Add minimum option word-count check to `check_option_count`

The existing validator rejects options with the wrong count (line 82–83) but not options that are 2–3 word labels. Adding a minimum token count check during validation (or a Pydantic validator on individual option strings) would catch label-only options at parse time, forcing a retry with a populated quality reminder rather than silently accepting degraded output.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| **N1 — llama3.1 label-only options in call-2/3** (analysis/19) | **B4**: multi-call prompt drops quality reinforcement; the option-quality constraint is only in the system prompt and decays with context growth |
| **N2 — qwen3 and gpt-4o-mini "Balances" reviews** (analysis/19) | **B1a**: in the unpatched checkout, these would be rejected by the English-only validator; the fact that they passed in runs 38/41 confirms the experiments used a patched code version, not this checkout |
| **Codex N3 — fabricated % in haiku (run 43, 18 hits)** | **B3**: `consequences` field description says "at least one quantitative estimate are mandatory", and haiku is the most instruction-following model |
| **Codex N4 — raw duplicate names in llama3.1 (21 vs 10 in analysis/18)** | **B4** + context crowding: later calls carry a longer names list; llama3.1 reverts to label generation and names are repeated before deduplication cleans them |
| **Claude N2 — "Balances" reviews pass validator** (analysis/19) | **B1a** confirmed (patched code relaxed validator); in current unpatched source these would fail |
| **Codex observation — bracket leakage drops from 37 to 0** | **B1b** explains why the current unpatched source is still vulnerable; the PR's field-description fix is essential |
| **Codex observation — bad summaries drop from 90/105 to 0/105** | **B1d**: current `summary` description ("Are these levers well picked? … 100 words") is an open critique prompt; PR alignment to "Add…" format fixes this |
| **Codex C3 — names list uses brackets `[...]`** | **B4**: `[{names_list}]` syntax uses the exact bracket pattern the new validator blocks in review fields; naming inconsistency |
| **Codex C1 — source checkout stale** | **B1** (all sub-items): confirmed; every stale element in C1 maps to B1a–B1e |
| **Codex C2 — missing `OPTIMIZE_INSTRUCTIONS`** | **I2**: no constant found in either file |

---

## PR Review

### PR #299: "fix: remove bracket placeholders and fragile English-only validator"

**Stated changes:**
1. Replace `[Tension A]`/`[Tension B]`/`[specific factor]` in `review_lever` field descriptions and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` with concrete literal examples.
2. Replace `check_review_format` English keyword checks with structural validation (min 20 chars, reject square brackets).
3. Align `summary` field description with prompt_4 format.

**Does the implementation match the intent?**

Based on the experimental evidence (analysis/19 runs 38–45), the PR changes were applied to a separate working copy and the results are consistent with all three stated changes being implemented correctly. However, **the current source tree does not reflect any of those changes** — the checkout still shows the pre-PR code at every affected location (lines 54–57, 95–98, 113–115, 148–151, 179–180). The PR has not been merged into this branch.

**What the PR gets right:**

- The validator relaxation (change 2) correctly enables non-English and non-"Controls" reviews to pass. Runs 38 and 41 confirm qwen3 and gpt-4o-mini can now produce "Balances X vs. Y" reviews without validation failure — a genuine i18n fix.
- The bracket-placeholder removal from field descriptions (change 1) is the highest-value defensive change: even when a model like haiku tries to follow the schema exactly, it now gets a concrete example instead of a fill-in-the-blank template.
- The summary alignment (change 3) explains the dramatic drop from 90/105 to 0/105 bad summaries. The old description was a general critique prompt; the new one locks the format to "Add…".

**Gaps and edge cases:**

1. **Format consistency regression (unfixed):** The new structural validator (min 20 chars + no square brackets) is too permissive. It accepts "Balances X with Y. Weakness: ..." (qwen3, gpt-4o-mini) but the downstream scenario picker presumably expects the "Controls X vs. Y" analytical framing. The old validator was inadvertently enforcing format consistency. The PR acknowledges this by replacing the validator but does not add a prompt instruction to substitute for the enforcement. Without either a validator or a strong prompt constraint, different models now produce the same field in structurally different formats.

   **Recommended addition:** Add an explicit instruction to the prompt: "First sentence must follow the exact grammatical pattern 'Controls [tension A] vs. [tension B].' — use this structure in any language." This restores format consistency without hardcoding English keywords in code.

2. **`LeverCleaned.review` not updated (B1c):** The `LeverCleaned` class still has the old placeholder description. While currently harmless (it is constructed programmatically), it creates a maintenance hazard and should be updated as part of the same PR.

3. **`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant not fully cleaned:** Lines 162–164 in the constant still use `[effect]`, `[impact]`, `[implication]` placeholders in the consequences section. PR #299's stated scope covers the `review_lever` field and the system prompt's Validation Protocols section (lines 178–183), but the consequences section in the constant also contains bracket placeholders that could leak if the constant is used directly.

4. **No guard on `consequences` field fabrication:** The PR does not touch the `consequences` field description or its "mandatory quantitative estimate" instruction. The 20 fabricated-percentage claims remaining in analysis/19 (18 from haiku) are a direct consequence of this unchanged instruction. This is out of scope for PR #299 but should be tracked.

5. **Multi-call degradation unchanged:** PR #299 makes no changes to the multi-call loop (lines 227–282). The llama3.1 label-only option problem at ~33–38% per batch is confirmed unresolved across two consecutive analysis batches.

**Verdict:** The PR should be merged. Its three stated changes produce measurable improvements (bracket leakage 37→0, bad summaries 90→0, i18n validator unblocked). The two side-effects — format inconsistency for qwen3/gpt-4o-mini and the stale `LeverCleaned.review` description — are manageable via a follow-up prompt addition and a one-line description update respectively.

---

## Summary

**The most important finding is B1:** the current PlanExe checkout is not synced with PR #299's changes. The validator at lines 95–98 still enforces English-only `'Controls '` and `'Weakness:'` keywords, and the `review_lever` field descriptions at lines 54–57 still carry `[Tension A]`/`[Tension B]`/`[specific factor]` bracket placeholders. If this checkout were used to run the baseline experiment today, it would behave as if PR #299 was never written: qwen3 and gpt-4o-mini would fail validation, and models that follow the schema literally would echo bracket placeholders into their output.

**The second most important finding is B3:** the `consequences` field description mandates "at least one quantitative estimate" as mandatory. This is the root cause of haiku's 18 fabricated-percentage claims in analysis/19. Removing or softening this mandate would have a larger quality impact than any remaining prompt tuning.

**B4** (multi-call quality reinforcement) explains the llama3.1 label-only option degradation, which is the last consistently failing quality dimension across two batches. A one-line option-quality reminder in the call-2/3 prompt (I1) is the minimal fix.

**B2** (race condition on global usage metrics path) is a latent correctness bug that would surface if any model were configured with `luigi_workers > 1`. It does not affect current experiments but should be fixed before parallel model testing is enabled.
