# Synthesis

## Cross-Agent Agreement

Only one agent produced both insight and code review files (claude), so this section captures internal consistency across those two documents.

Both analyses agree on every major finding:

- **UUID contamination fully eliminated**: PR #460's 6-char prefix + positive framing removed all 32 UUID/placeholder contamination instances from llama3.1 (20 full UUIDs + 12 `(lever ID: XXXX)` placeholders). This is confirmed correct and a genuine content quality win for 6 of 7 models.
- **Haiku regression is the dominant problem**: `unknown_lever_id` errors increased 514% (7 → 43) after PR #460, caused directly by the 6-char prefix confusing haiku's function-calling structured output pathway.
- **Root cause is B1**: `LeverCharacterization.lever_id` field description (line 136) was not updated when the identifier scheme changed. The vague description "The 6-character identifier of the lever" allows haiku to fabricate any 6-char string rather than copying the actual prefix from the prompt.
- **I1 is the cleanest fix**: Use full UUIDs for function-calling models and 6-char prefix only for text-completion models. Evidence from PR #458 shows this approach reduces haiku errors to ~2.
- **I3 is a complementary safety net**: A name-based fallback in `prefix_to_full` lookup at line 277 would silently salvage haiku's correct enrichment content (description/synergy/conflict are all correct; only `lever_id` is wrong).
- **PR verdict: CONDITIONAL** — keep for non-haiku models; fix haiku regression before treating as best.

---

## Cross-Agent Disagreements

No significant disagreements. Both documents agree on the direction, priority, and root cause. Minor nuance: the insight analysis notes that haiku's description length grew to 1.39× baseline (N3) and traces this to the fabrication noise amplifying haiku's word-count padding. The code review does not flag this independently but also does not contradict it.

**Verified by reading source code:**

- **B1 confirmed** (`enrich_potential_levers.py:136`): Field description is exactly `"The 6-character identifier of the lever"` with no `pattern` constraint, no example, no instruction to copy from the prompt. Haiku's fabricated IDs (`d9e2f1`, `e8f4g2`, `f2h5i3`…) follow a sequential alphabetical pattern and include non-hex characters — entirely consistent with the field description giving haiku a blank cheque.
- **B2 confirmed** (`enrich_potential_levers.py:262-264`): `execute_function` closure captures `chat_message_list` by name; `chat_message_list` is reassigned on every while-loop iteration (line 260). `identify_potential_levers.py:317` already has the correct pattern (`messages_snapshot = list(call_messages)`).
- **B3 confirmed** (`runner.py:554-566`): `with _TPE(max_workers=1) as executor:` calls `executor.shutdown(wait=True)` on exit, blocking the calling thread even after `TimeoutError` is caught.
- **S1 confirmed** (`enrich_potential_levers.py:277`): `prefix_to_full.get(char.lever_id, char.lever_id)` fallback passes the fabricated ID to `enriched_levers_map`, which is keyed by full UUIDs and always fails for fabricated values.
- **S3 confirmed** (`enrich_potential_levers.py:199`): Code probes `context_window` (line 205) but does not probe `is_function_calling_model`, even though both attributes are on the same `metadata` object.

---

## Top 5 Directions

### 1. Model-type-aware identifier strategy (I1)
- **Type**: code fix
- **Evidence**: Both insight (C1) and code review (I1, S3) flag this. PR #458 demonstrated that full UUIDs for haiku produced only 2 errors; PR #460 switched to 6-char prefix and haiku jumped to 43. UUID contamination was llama3.1-specific (text-completion model copying verbatim from prompt); haiku uses structured tool-call output and was never a contamination risk with full UUIDs.
- **Impact**: Restores haiku from 43 errors → ~2 errors while preserving llama3.1's contamination fix (0 UUID leaks). Affects 1 of 7 models directly; no regression risk for the other 6. Net effect: total errors drop from 45 to ~4.
- **Effort**: Low. Probe `probe_llm.metadata.is_function_calling_model` (same pattern as `context_window` probe at line 205). Branch the `prefix_to_full` dict and `lever_details_for_prompt` format accordingly. ~10 lines.
- **Risk**: `is_function_calling_model` attribute might be absent on some metadata objects. Wrap in try/except with a safe default (full UUID is safer than 6-char prefix when unknown model type).

### 2. Update LeverCharacterization.lever_id field description with anchor + hex example (B1/I5)
- **Type**: code fix (Pydantic schema change = prompt change for function-calling models)
- **Evidence**: Both analyses identify this as the direct cause of haiku's fabrication. Current text: `"The 6-character identifier of the lever"`. This is the weakest possible anchor — haiku reads it as licence to generate any 6-char string.
- **Impact**: Reduces haiku fabrications even without I1. Adds a concrete example that grounds the expected value in the prompt format. Also catches cases where `is_function_calling_model` is not available and the code falls back to 6-char mode.
- **Effort**: Low — one line change at `enrich_potential_levers.py:136`.
- **Risk**: Field description changes affect all models. For well-behaved models (gpt-oss-20b, qwen3-30b, etc.) this is a no-op; they already return correct values. For haiku it should be a strict improvement.

### 3. Name-based fallback in prefix_to_full lookup (I3/S1)
- **Type**: code fix
- **Evidence**: Both analyses agree (code review I3, insight C2). Haiku fabricated entries carry correct `description`, `synergy_text`, `conflict_text` — only `lever_id` is wrong. The current fallback at line 277 passes the fabricated ID to `enriched_levers_map` (keyed by full UUID), which always fails, silently discarding correct enrichment content.
- **Impact**: Silent resolution of `unknown_lever_id` errors for single-lever batches (unambiguous match) and potentially multi-lever batches via lever-name lookup. Zero prompt change. Complementary to I1: even after I1 restores haiku, this provides a safety net for edge cases where any model's ID is marginally wrong.
- **Effort**: Medium. Build `name_to_full: dict[str, str]` mapping for the batch. On lookup miss, try matching by lever name. For batch_size=1, the match is unambiguous; for larger batches, require exact name match.
- **Risk**: Name collisions (unlikely for deduplicated levers). Match-by-elimination (when only one lever in batch is unenriched) is unambiguous and safe.

### 4. Add pattern constraint to LeverCharacterization.lever_id (I2)
- **Type**: code fix (Pydantic schema)
- **Evidence**: Code review I2. Without `pattern=r"^[0-9a-f]{6}$"`, Pydantic silently accepts every fabricated value. Adding the constraint would force a retry on non-hex IDs (e.g., `e8f4g2`, `f2h5i3`).
- **Impact**: Triggers retries for the majority of haiku's fabricated IDs (those containing non-hex chars). Caveat: `d9e2f1` is accidentally valid hex and would pass. Combined with I1 and the field description fix (direction 2), this provides defense-in-depth.
- **Effort**: Low — two-line change at `enrich_potential_levers.py:134-136`.
- **Risk**: A model that genuinely produces valid hex IDs for the wrong lever would pass the pattern check but still fail the `prefix_to_full` lookup. The constraint catches the obvious fabrication class (non-hex) but not accidental hex collisions.

### 5. Fix execute_function closure capture of chat_message_list (B2)
- **Type**: code fix
- **Evidence**: Code review B2. Confirmed in source: `chat_message_list` is assigned at line 260, the closure at line 262 captures the name not the value, and `chat_message_list` is reassigned on the next loop iteration. `identify_potential_levers.py:317` already uses the correct snapshot pattern.
- **Impact**: Latent bug — current synchronous `LLMExecutor.run()` makes this harmless today. If the executor is ever made async or parallel, every batch except the last would silently receive the wrong prompt, corrupting all enrichment. No impact on current runs; prevents a hard-to-diagnose future regression.
- **Effort**: Minimal — one line before the closure definition: `messages_snapshot = list(chat_message_list)` and update the closure to use `messages_snapshot`.
- **Risk**: None. Pure defensive copy, no semantic change.

---

## Recommendation

**Implement I1 (model-type-aware identifier strategy) first.**

This is the single highest-leverage change because it directly targets the dominant regression introduced by PR #460: haiku's `unknown_lever_id` errors jumped from 7 to 43. Evidence is strong — PR #458 already demonstrated that full UUIDs with the exact-count instruction reduces haiku to ~2 errors. The fix is structurally clean and does not require a prompt change for well-behaved models.

**What to change — `enrich_potential_levers.py`, in the `execute` method, around lines 237–247:**

```python
# Detect whether this model uses function-calling structured output.
# Function-calling models (haiku, gpt-4o-mini) generate lever_id via
# tool-use JSON and do NOT copy text into free-text fields — UUID
# contamination was only observed in text-completion models (llama3.1).
# Use full UUIDs for function-calling models so the ID is a distinct
# 36-char value that is easy to copy; use 6-char prefix for text-
# completion models to prevent UUID leakage into synergy/conflict text.
try:
    _is_fc = probe_llm.metadata.is_function_calling_model
except AttributeError:
    _is_fc = False  # unknown → treat as text-completion (safer default)

if _is_fc:
    prefix_to_full = {lever.lever_id: lever.lever_id for lever in batch}
    lever_details_for_prompt = "\n\n".join([
        f"Lever {lever.lever_id}\n"
        f"Name: {lever.name}\n"
        f"Consequences: {lever.consequences}\n"
        f"Options: {json.dumps(lever.options)}\n"
        f"Review: {lever.review}"
        for lever in batch
    ])
else:
    prefix_to_full = {lever.lever_id[:6]: lever.lever_id for lever in batch}
    lever_details_for_prompt = "\n\n".join([
        f"Lever {lever.lever_id[:6]}\n"
        f"Name: {lever.name}\n"
        f"Consequences: {lever.consequences}\n"
        f"Options: {json.dumps(lever.options)}\n"
        f"Review: {lever.review}"
        for lever in batch
    ])
```

Also update `LeverCharacterization.lever_id` field description (`enrich_potential_levers.py:136`) to anchor both cases:

```python
lever_id: str = Field(
    description="The exact identifier shown before the lever name above (e.g., '278aac' or a full UUID). Copy it exactly as shown — do not generate a new value."
)
```

And add to `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py`:

```
- 6-char prefix regression on function-calling models. Using 6-char hex
  prefixes as lever IDs causes function-calling models (haiku, gpt-4o-mini)
  to pattern-complete the short field with fabricated sequential strings
  (d9e2f1, e8f4g2, f2h5i3, …) rather than reading the actual prefix from
  the prompt. The actual enrichment content (description, synergy_text,
  conflict_text) is correct — only lever_id is wrong. Use full UUIDs for
  function-calling models (is_function_calling_model=True) and 6-char
  prefixes for text-completion models (llama3.1). UUID contamination into
  free-text fields is a text-completion-only failure mode.
```

This change, combined with direction 2 (anchor the field description), eliminates the haiku regression while preserving all gains from PR #460 for llama3.1 and the other 5 models.

---

## Deferred Items

- **I3 (name-based fallback)**: Worth adding as defense-in-depth after I1 lands. It requires no experiment — it's a pure code change that silently rescues correct enrichment content when any model's ID lookup fails. Implement in the same PR as I1 to avoid a separate iteration.

- **I2 (pattern constraint on lever_id)**: Add `pattern=r"^[0-9a-f]{6}$"` for the 6-char branch only (not the full-UUID branch). Provides a retry trigger for non-hex fabrications. Low effort; can be bundled with the I1 PR.

- **B2 (closure capture fix)**: One-line defensive copy (`messages_snapshot = list(chat_message_list)`) before the `execute_function` closure. No experiment needed. Bundle with I1 PR to close the latent bug.

- **B3 (runner.py plan timeout non-functional)**: The `with _TPE(max_workers=1)` context manager blocks the calling thread on `shutdown(wait=True)` regardless of whether `TimeoutError` was caught. Fix: use `executor.shutdown(wait=False, cancel_futures=True)` after the `except _TE:` block, or restructure to not rely on `with` block cleanup for timeout enforcement. This is a separate concern from the lever enrichment prompt work and should be its own PR.

- **S2 (partial_recovery mislabels 2-call successes)**: The `partial_recovery` event fires for any run with `calls_succeeded < 3`, including 2-call runs that legitimately succeeded early. Add a `pr.status == "ok"` guard or check `calls_succeeded < expected_calls` where `expected_calls` is computed from the actual lever count. Low impact but pollutes event analysis.
