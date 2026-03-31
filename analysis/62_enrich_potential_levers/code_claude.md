# Code Review (claude)

PR under review: PlanExeOrg/PlanExe#460 — "Use 6-char lever ID prefix, positive framing, and exact-count instruction"

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — `LeverCharacterization.lever_id` field description gives haiku a blank cheque (HIGH)

**File**: `enrich_potential_levers.py:136`

```python
lever_id: str = Field(description="The 6-character identifier of the lever")
```

The description says "6-character identifier" but gives no example and does not say the string must be a hex prefix drawn from the prompt. Haiku reads this as licence to generate *any* 6-character string and pattern-completes with a sequential alphabetical series (`d9e2f1`, `e8f4g2`, `f2h5i3`, …). The description also has no `pattern` constraint, so Pydantic silently accepts every fabricated value.

Before PR #460, full UUIDs were used in the prompt and `lever_id` returned by the model. Haiku has an easy job: copy the 36-char UUID. After PR #460, the model must recognise a 6-char prefix in the prompt and return *that exact prefix* in a structured field. Haiku's function-calling JSON generation pattern-completes the short field instead of grounding it in the prompt.

This single change is the direct and complete cause of haiku's 7 → 43 `unknown_lever_id` error increase.

---

### B2 — `execute_function` closure captures `chat_message_list` by reference (MEDIUM)

**File**: `enrich_potential_levers.py:262-267`

```python
chat_message_list = [system_message, ChatMessage(role=MessageRole.USER, content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)   # ← captures name, not value
    ...
```

`chat_message_list` is re-assigned on every loop iteration. Python closures capture variable *names*, not snapshot values. If `llm_executor.run()` ever defers or parallelises the call (e.g., stores the callable for a later thread), the closure would use the *last* value of `chat_message_list`, sending the wrong messages for every batch except the last.

The current `LLMExecutor.run()` implementation is synchronous, so this is latent rather than immediately harmful. But `identify_potential_levers.py:317` does this correctly with an explicit snapshot:

```python
messages_snapshot = list(call_messages)   # ← defensive copy
def execute_function(llm: LLM) -> dict:
    ...
    chat_response = sllm.chat(messages_snapshot)
```

The `enrich_potential_levers.py` while-loop should follow the same pattern.

---

### B3 — Plan timeout in `_run_plan_task` blocks the calling thread anyway (MEDIUM)

**File**: `runner.py:554-566`

```python
from concurrent.futures import ThreadPoolExecutor as _TPE, TimeoutError as _TE
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, plan_dir, output_dir, model_names, step)
    try:
        pr = future.result(timeout=plan_timeout)
    except _TE:
        logger.error(f"{plan_name}: killed after {plan_timeout}s (plan timeout)")
        pr = PlanResult(
            name=plan_name,
            status="error",
            duration_seconds=float(plan_timeout),
            error=f"plan timeout after {plan_timeout}s",
        )
```

After catching `TimeoutError`, `pr` is correctly set to an error result. However, the `with _TPE(max_workers=1)` context manager's `__exit__` calls `executor.shutdown(wait=True)`, which **blocks the calling thread until the submitted future completes** — regardless of whether `TimeoutError` was caught. The future is still running.

This means `_run_plan_task` returns only after the underlying plan finishes (or raises), making `plan_timeout` non-functional as a wall-clock guard. The comment at line 90 says "Prevents a single stuck LLM call from blocking the entire run" — but the calling thread is blocked by `shutdown(wait=True)` for as long as the inner thread runs.

In parallel mode (multiple workers), each outer thread is stuck waiting for its inner thread, so all workers can be held indefinitely by slow plans. The `partial_recovery` event and error `PlanResult` are written correctly, but the timing guarantee is illusory.

---

## Suspect Patterns

### S1 — `prefix_to_full` fallback silently passes fabricated ID to the map lookup

**File**: `enrich_potential_levers.py:277`

```python
full_id = prefix_to_full.get(char.lever_id, char.lever_id)
if full_id in enriched_levers_map:
    ...
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

When `prefix_to_full.get()` misses (because the returned ID was fabricated), the fallback is `char.lever_id` itself, which is then looked up in `enriched_levers_map` keyed by full UUIDs. This always fails for fabricated IDs, producing an `unknown_lever_id` error. The correct enrichment content produced by haiku (description, synergy_text, conflict_text) is silently discarded even though all real lever content is correct.

A name-based fallback — using `char.lever_id` or the lever name to route the enrichment — would salvage haiku's correct content without requiring a prompt change.

### S2 — `partial_recovery` event fires for successful 2-call runs

**File**: `runner.py:577-583`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The adaptive loop in `identify_potential_levers.py` stops early when `len(generated_lever_names) >= 15`. A model that returns 8–10 levers per call can reach the threshold in 2 calls — a perfectly normal success. `_run_levers` already logs a warning for `actual_calls < 3`, but emitting a `partial_recovery` event in `events.jsonl` for every 2-call success mislabels healthy runs as degraded in downstream event analysis. The check should also verify that `pr.status == "ok"` or the criterion should be narrowed.

### S3 — `probe_llm.metadata.is_function_calling_model` not checked

**File**: `enrich_potential_levers.py:199-208`

The code probes `probe_llm.metadata.context_window` to choose batch size, but does not probe `is_function_calling_model` to choose between full UUID and 6-char prefix. Both attributes are on the same `metadata` object. The batch-size probe is gated by a try/except that silently falls back on failure — the same pattern should apply to an `is_function_calling_model` probe.

---

## Improvement Opportunities

### I1 — Use full UUIDs for function-calling models (HIGH)

**File**: `enrich_potential_levers.py:239-247`

Function-calling models generate structured JSON via tool-use. They do not copy identifiers into free-text fields (synergy_text/conflict_text). The UUID contamination problem observed with llama3.1 (PR #457) was specific to text-completion models that copy verbatim from the prompt.

Using full 36-char UUIDs for function-calling models would:
- Eliminate haiku's fabricated-ID regression (the 36-char UUID is distinct enough to match)
- Preserve the 6-char prefix benefit for text-completion models (llama3.1)
- Mirror what PR #458 already achieved (2 haiku errors vs 43 now)

Detection:

```python
probe_llm.metadata.is_function_calling_model  # bool attribute
```

### I2 — Add `pattern` constraint to `LeverCharacterization.lever_id` (MEDIUM)

**File**: `enrich_potential_levers.py:136`

A regex constraint would reject non-hex fabricated IDs from haiku immediately at schema validation time, triggering a retry instead of silently writing an error:

```python
lever_id: str = Field(
    description="The exact 6-character hex prefix shown before the lever name above — e.g. '278aac'",
    pattern=r"^[0-9a-f]{6}$"
)
```

Caveat: haiku's first fabricated ID (`d9e2f1`) is accidentally valid hex. The pattern catches IDs with non-hex characters (`e8f4g2` → rejects `g`, `f2h5i3` → rejects `h`, `i`) but not the first entry. Combined with I3 (anchor description), this would catch the majority of fabrications and force retries.

### I3 — Add name-based fallback in `prefix_to_full` lookup (MEDIUM)

**File**: `enrich_potential_levers.py:275-286`

When `prefix_to_full.get(char.lever_id, char.lever_id)` fails to find a full UUID, the characterization is discarded. Haiku's fabricated entries carry *correct* description, synergy_text, and conflict_text — only the ID is wrong. A name-based fallback could route the enrichment correctly:

1. Build an auxiliary `name_to_full: dict[str, str]` mapping lever names to full UUIDs for the batch.
2. On `unknown_lever_id`, check if any lever in the batch was not yet enriched and match by elimination (when batch size = 1, there is only one candidate).

This is a pure code change requiring no prompt modification and no new experiment run to validate.

### I4 — Update `OPTIMIZE_INSTRUCTIONS` to document haiku 6-char regression (LOW)

**File**: `enrich_potential_levers.py:88-94`

The current entry (lines 88-94) documents the UUID fix and the positive-framing lesson. It does not mention that 6-char prefixes *regress* function-calling models (haiku). Future optimisation attempts will repeat this mistake without a documented note:

> "6-char prefixes confuse function-calling models (haiku, gpt-4o-mini): haiku's structured JSON generation pattern-completes the short field with fabricated sequential strings (d9e2f1, e8f4g2, …) rather than reading the actual prefix from the prompt. Full UUIDs are the correct identifier strategy for function-calling models; 6-char prefixes are the correct strategy for text-completion models (llama3.1)."

### I5 — Anchor `lever_id` field description with a concrete example (LOW)

**File**: `enrich_potential_levers.py:136`

The current description "The 6-character identifier of the lever" is the weakest possible anchor. Changing it to reference the prompt format directly reduces model ambiguity at near-zero cost:

```
"The exact 6-character hex prefix shown before the lever name above (e.g., '278aac'). Copy it exactly as shown — do not generate a new value."
```

This partially mitigates B1 even without the structural fix (I1).

---

## Trace to Insight Findings

| Insight Finding | Root Code Cause |
|----------------|----------------|
| N1: Haiku `unknown_lever_id` errors 7 → 43 | B1: vague `lever_id` field description; haiku pattern-completes any 6-char string instead of returning the actual prompt prefix |
| N2: llama3.1 2 new minor errors | S1: `prefix_to_full` has no name-based fallback; one lever name collision or truncation causes a miss |
| N3: Haiku description inflation (1.39×) | Indirect: haiku's function-calling path is already generating extra fabricated entries; the model's word-count padding behaviour is amplified when it generates 3–4× more entries than expected |
| P1/P2: UUID contamination eliminated | Confirmed correct: 6-char prefix + positive framing works for text-completion models (llama3.1) because they no longer have a 36-char UUID to copy |
| P3: No timeouts / LLMChatErrors | B3 is latent: the timeout guard is non-functional, but all runs happened to complete within plan_timeout |

---

## PR Review

### What the PR changes

1. `enrich_potential_levers.py:239`: `prefix_to_full = {lever.lever_id[:6]: lever.lever_id for lever in batch}` and `lever.lever_id[:6]` in prompt formatting
2. `enrich_potential_levers.py:173`: Positive framing — "refer to other levers by their name — for example, write 'Policy Advocacy Strategy', not an identifier"
3. `enrich_potential_levers.py:254-255`: Exact-count instruction — "Return exactly {len(batch)} characterizations — one per lever, no more, no fewer."
4. `enrich_potential_levers.py:88-94`: OPTIMIZE_INSTRUCTIONS entry for the UUID fix

### Does the implementation match the intent?

**6-char prefix**: Partially. The prefix-to-full mapping at line 239 and the prompt formatting at lines 240-247 are consistent. The fallback at line 277 (`prefix_to_full.get(char.lever_id, char.lever_id)`) is a reasonable safety valve. The critical gap is that `LeverCharacterization.lever_id`'s field description (line 136) was not updated to reflect the new shorter format, leaving haiku free to fabricate.

**Positive framing**: Correct and well-scoped. The instruction is in the system prompt (line 173) and avoids naming forbidden patterns (the PR #458 lesson). No issue here.

**Exact-count instruction**: Correct syntax, but the instruction at line 255 is in the user prompt, not the system prompt. System-prompt instructions carry higher weight for function-calling models. For haiku, this instruction is overridden by the model's tendency to generate one entry per fabricated ID.

**OPTIMIZE_INSTRUCTIONS**: Documents the UUID fix and positive-framing lesson accurately. Does not yet document the haiku regression (I4).

### Gaps and edge cases the PR misses

1. **No model-type awareness**: The same 6-char prefix is used for all models. Function-calling and text-completion models have different failure modes. The PR fixed llama3.1's failure mode while triggering haiku's.

2. **`LeverCharacterization.lever_id` field not updated**: Changing the prompt to show `Lever 278aac` while leaving the schema description as "The 6-character identifier of the lever" is the root of B1. The two are inconsistent: the prompt implies "copy this prefix"; the schema implies "generate a 6-char identifier."

3. **No validation on the returned `lever_id` format**: Without a `pattern` constraint, every 6-char string — hex or not — passes Pydantic validation and reaches the `prefix_to_full.get()` lookup, producing only a warning.

4. **Exact-count regression**: PR #458's exact-count instruction reduced haiku errors from 7 to 2. PR #460 retains the instruction but undoes the reduction entirely (43 errors) by changing the identifier scheme. This shows the exact-count instruction is insufficient on its own when the model's identification mechanism fails.

### Verdict on the PR

**Correct for its stated goal (UUID contamination)**: The 6-char prefix + positive framing eliminates llama3.1's 32 UUID/placeholder contamination instances cleanly. For 6 of 7 tested models the PR is a net positive.

**Introduces a haiku-specific regression**: The root cause (B1) is a one-line oversight: `LeverCharacterization.lever_id`'s field description was not updated when the identifier scheme changed. Haiku reads the field description, not the prompt format, when generating structured output.

---

## Summary

The highest-priority finding is **B1**: the `LeverCharacterization.lever_id` Pydantic field description (line 136) was not updated when the identifier scheme changed from full UUID to 6-char prefix. Haiku's structured-output pathway reads field descriptions to fill values; without an explicit anchor ("copy the exact 6-char prefix shown in the prompt"), haiku generates sequential strings. This is the entire cause of the 514% haiku error increase.

**B2** (closure captures `chat_message_list` by reference, line 262) is latent but would silently send wrong prompts if the executor is ever made async. The fix already exists in `identify_potential_levers.py` — assign a snapshot before defining the closure.

**B3** (plan timeout non-functional, runner.py:554-566) means a stuck plan silently blocks its calling thread indefinitely despite the timeout guard. This does not affect correctness of the current runs but will become visible under real network hangs.

The two cleanest fixes with no experiment required are:
- **I3** (name-based fallback in `prefix_to_full`): salvages haiku's correct enrichment content even when the ID is wrong — pure code change
- **I1** (model-type-aware ID strategy): use full UUIDs for function-calling models, restoring the PR #458 baseline (2 haiku errors)

Both can be applied independently. I1 is the cleaner structural fix; I3 is an additional safety net.
