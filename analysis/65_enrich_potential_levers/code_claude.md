# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`

PR under review: #466 "Wrap lever UUID in XML tags to prevent UUID leakage in free-text fields"

---

## Bugs Found

### B1 — Negative prohibition naming banned phrases in `Lever.consequences` field description

**File:** `identify_potential_levers.py:116–119`

```python
consequences: str = Field(
    description=(
        ...
        "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
        "those belong exclusively in review_lever. "
        ...
    )
)
```

The `Lever` schema is sent to the LLM via `llm.as_structured_llm(DocumentDetails)`. Its Pydantic field descriptions are included in the JSON schema the model receives. The phrases `'Controls ... vs.'` and `'Weakness:'` are named explicitly as things to avoid.

`OPTIMIZE_INSTRUCTIONS` (lines 80–82) states:

> "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."

Naming `'Controls ... vs.'` and `'Weakness:'` inside a field description that is sent to the LLM is exactly the pattern OPTIMIZE_INSTRUCTIONS warns against. Small or weaker models may reproduce those very phrases in the `consequences` field.

Additionally, `OPTIMIZE_INSTRUCTIONS` (lines 62–68) calls out "Controls", "Weakness:", and "versus"/"vs." as English-specific keywords that break non-English outputs. Having them in the Pydantic schema compounds this: a model responding in Japanese or Chinese will see English-language prohibitions that don't apply to its output, leading to confusion.

The `LeverCleaned.consequences` field (lines 208–216) has the same negative-prohibition language but is never sent to an LLM (by design per the class docstring), so that copy is harmless.

**Fix direction:** Remove the English-specific prohibitions from the field description. The intent (keep critique out of `consequences`) is already enforced by the `review_lever` field's existence and description. Alternatively, rephrase positively: "Focus on cause-effect relationships and trade-offs within the project domain."

---

### B2 — `unknown_lever_id` errors misclassify expected haiku over-generation as failures

**File:** `enrich_potential_levers.py:281–283`

```python
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

Haiku (and potentially other function-calling models) generates extra `LeverCharacterization` objects beyond the requested batch size, with fabricated UUIDs. These extra entries are silently and correctly discarded (they never enter `enriched_levers_map`). However, they are also appended to `errors`, which is then serialised into the output JSON (`002-12-enriched_levers_raw.json`).

This conflates two distinct classes of event:
1. **Real errors** — a batch skipped, a lever completely un-enriched, a Pydantic validation failure.
2. **Expected model noise** — haiku generating an extra characterization that has no matching lever.

Downstream consumers reading `errors` cannot distinguish between these without additional parsing. The insight confirms all 35 real levers are correctly enriched in every haiku run; the `unknown_lever_id` entries are entirely cosmetic noise in the error list.

The `BatchCharacterizationResult.characterizations` field has no `max_length` constraint (unlike what the insight notes for `DocumentDetails.levers`, which explicitly avoids a cap for the same reason). There is also no comment explaining why the cap is absent, which is an omission (see I2 below).

---

## Suspect Patterns

### S1 — `execute_function` closure captures `chat_message_list` without a defensive snapshot

**File:** `enrich_potential_levers.py:259–266`

```python
chat_message_list = [system_message, ChatMessage(role=MessageRole.USER, content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)   # captured by reference
    ...
```

Compare with `identify_potential_levers.py:317–322`:

```python
messages_snapshot = list(call_messages)   # defensive copy

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
```

`identify_potential_levers.py` explicitly creates a snapshot before passing the list into the closure. `enrich_potential_levers.py` does not. In Python, while loop iterations do not create new scopes — all iterations share the same `chat_message_list` variable in the function's local scope. Currently, `llm_executor.run()` appears to call `execute_function` synchronously, so the captured reference always points to the current iteration's value. However, if `llm_executor.run()` is ever made asynchronous (e.g., to support concurrent retries), the captured variable could point to a later iteration's message list, silently sending the wrong prompt. The inconsistency with `identify_potential_levers.py` is a latent risk.

---

### S2 — Duplicate exact-count instruction in both system and user prompts

**File:** `enrich_potential_levers.py:177` (system prompt) and `enrich_potential_levers.py:254` (user prompt)

System prompt:
```
Return exactly one characterization per lever requested — no more, no fewer.
```

User prompt:
```
Return exactly {len(batch)} characterizations — one per lever, no more, no fewer.
```

Both sentences instruct the same constraint. The system-level instruction is abstract ("one per lever"); the user-level instruction is concrete (the actual count). For function-calling models like haiku, having two slightly different formulations of the same constraint may create ambiguity about which to follow. The insight (Q3) raises this directly: removing the system-level version would leave only the concrete count in the user prompt, which is more actionable.

---

### S3 — `BatchCharacterizationResult.characterizations` lacks the no-max_length rationale comment

**File:** `enrich_potential_levers.py:149–153`

```python
class BatchCharacterizationResult(BaseModel):
    """The expected JSON structure for a batch of characterizations from the LLM."""
    characterizations: List[LeverCharacterization] = Field(
        description="A list containing the full characterization for each requested lever in the batch."
    )
```

`DocumentDetails.levers` in `identify_potential_levers.py` (lines 188–193) has an explicit comment explaining why no `max_length` is set:

```python
# No max_length constraint: if a model returns more than 7 levers, the downstream
# DeduplicateLeversTask handles extras. A hard cap would discard the entire response
# and waste tokens retrying.
levers: list[Lever] = Field(min_length=5, ...)
```

`BatchCharacterizationResult.characterizations` intentionally omits a max_length for the same reason (haiku returns extra characterizations and they are discarded by the `lever_id` lookup), but there is no comment explaining this. A future maintainer encountering haiku's extra entries in `errors` might add a `max_length=batch_size` constraint, which would cause haiku's entire structured response to be rejected by Pydantic rather than partially accepted, converting a benign warning into a hard batch failure.

---

## Improvement Opportunities

### I1 — Suppress `errors.append` for `unknown_lever_id` (insight C1)

**File:** `enrich_potential_levers.py:282–283`

The `errors` list is used by downstream consumers to detect genuine enrichment failures. Haiku's extra characterizations are expected behavior: all real levers are correctly enriched, and the extras are discarded. Appending them to `errors` pollutes the failure signal.

Proposed change: keep the `logger.warning` for debuggability, but do not append to `errors`:

```python
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    # Not appended to errors — extra characterizations from over-generating models
    # (e.g. haiku) are expected and discarded. Real levers are always enriched.
```

Expected effect: `errors` array goes from 5 entries to 0 for haiku across all runs. Risk: low — correct lever enrichment is unaffected; only noise is removed.

---

### I2 — Add no-max_length rationale comment to `BatchCharacterizationResult.characterizations`

**File:** `enrich_potential_levers.py:149–153`

Add the same style of comment used in `identify_potential_levers.py:188–189`:

```python
# No max_length constraint: haiku and similar function-calling models return extra
# LeverCharacterization entries with fabricated IDs. These are silently discarded
# via the lever_id lookup. A hard cap would reject the entire response, turning
# expected noise into a hard batch failure.
characterizations: List[LeverCharacterization] = Field(...)
```

---

### I3 — Remove system-level exact-count instruction; keep only user-level

**File:** `enrich_potential_levers.py:177`

The system prompt contains: `"Return exactly one characterization per lever requested — no more, no fewer."`
The user prompt already contains: `"Return exactly {len(batch)} characterizations — one per lever, no more, no fewer."`

The user-level instruction is more concrete (it gives a specific integer). Remove the system-level version and leave only the user-level version with the actual count. This reduces ambiguity for haiku's function-calling interface. Risk: unknown — could worsen behavior if haiku relies on the system-level constraint. Warrants one experiment iteration to confirm.

---

### I4 — Clarify negative prohibition in `Lever.consequences` field description (follow-on to B1)

**File:** `identify_potential_levers.py:116–119`

Replace the English-specific negative prohibition with a positive description of what the field should contain. This is a prompt change and requires a self_improve iteration to validate.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Root Cause |
|----------------|---------------|------------|
| N1 — haiku `unknown_lever_id` errors persist (5 remaining) | `enrich_potential_levers.py:274–283` | `BatchCharacterizationResult` has no `max_length` cap, so haiku's extra characterizations pass Pydantic validation. The `errors.append` (B2) adds them to the failure list despite being benign. |
| N3 — Fabricated percentage claims in `consequences` propagate | `identify_potential_levers.py:113–120` | The `Lever.consequences` field description says "only cite numbers if the project context provides evidence" but includes the English-specific negative prohibition (B1) that may cause small models to produce "Controls … vs." pattern text, potentially including fabricated numbers. No code-level validator checks for numeric fabrication. |
| Q3 (insight question) — redundant exact-count instructions | `enrich_potential_levers.py:177,254` | Both system and user prompts contain independent count constraints (S2), potentially confusing haiku into treating one as the binding rule. |
| Q4 (insight question) — batch-size dependent haiku errors | `enrich_potential_levers.py:110,201–208` | Adaptive batch-size logic (lines 201–208) only reduces batch size for small-context models (`context_window < 3000`). Haiku (a function-calling model with adequate context) always uses `BATCH_SIZE=5`. The extra characterizations appear specifically in second batches (shorter batches). No per-model batch-size override exists. |

---

## PR Review

### Intent vs. Implementation

PR #466 targets residual UUID contamination in `synergy_text` and `conflict_text` that remained after PR #457. The per-batch `lever_details_for_prompt` still exposed UUIDs as plaintext (`Lever ID: {uuid}`), which llama3.1 copied into free-text fields for same-batch levers. The PR wraps these with XML tags: `<lever>{uuid}</lever>`.

**Implementation matches intent.** The change at lines 239–246 correctly:
1. Preserves the UUID at the top of each lever block (required for positional heuristic matching per OPTIMIZE_INSTRUCTIONS line 93–94).
2. Wraps the UUID in `<lever>...</lever>` XML tags so models treat it as structured markup rather than copyable prose.
3. Keeps the full UUID (not a short prefix or integer index, both of which broke matching in prior PRs per OPTIMIZE_INSTRUCTIONS lines 93–95).

### Gaps and Edge Cases

**Gap 1 — Haiku over-generation not addressed at code level.**
The PR adds an exact-count instruction that partially reduces haiku errors (7 → 5), but the fix is prompt-only. The code-level change that would fully clean up the output — suppressing `errors.append` for `unknown_lever_id` (I1/B2 above) — is not included in the PR. The OPTIMIZE_INSTRUCTIONS documentation (lines 88–96) correctly describes the XML-tag mitigation but does not document haiku's over-generation behavior or the `unknown_lever_id` error as expected noise.

**Gap 2 — No comment explaining why `BatchCharacterizationResult.characterizations` lacks `max_length`.**
A future maintainer might add a `max_length=batch_size` constraint after seeing haiku errors in `errors`. This would turn expected noise into hard batch failures. The rationale for omitting the cap is not documented (S3/I2 above).

**Gap 3 — Duplicate exact-count constraint may subtly confuse haiku.**
Both system and user prompts now contain count instructions (S2/I3 above). The system-level instruction is abstract ("one per lever"); the user-level is concrete ("exactly N"). For haiku's function-calling interface, these may conflict. This is a secondary concern — the PR improves haiku (7 → 5 errors) — but the residual 5 errors suggest the system-level abstract constraint is not sufficient.

### Regressions

None. The XML tag change is isolated to the per-batch `lever_details_for_prompt`. The insight confirms:
- 0 UUID contamination in `synergy_text`/`conflict_text` across all 7 models.
- No new LLMChatError events.
- No schema-level validation failures.
- haiku errors reduced (not increased).

The positive framing instruction ("always refer to other levers by their name") has no negative side effects on models that were already clean.

### Verdict

The PR correctly implements its stated goal. The XML-tag wrapping is the right approach: it eliminated llama3.1 UUID contamination 100% (15 → 0 occurrences) with no collateral damage. The two remaining code-level issues (B2/I1: `errors` pollution, S3/I2: missing max_length rationale comment) are not regressions introduced by this PR — they are pre-existing omissions that should be addressed in a follow-up.

---

## Summary

| ID | Type | File:Line | Description |
|----|------|-----------|-------------|
| B1 | Bug | `identify_potential_levers.py:116–119` | Negative prohibition naming `'Controls ... vs.'` and `'Weakness:'` in Pydantic field description sent to LLM — violates OPTIMIZE_INSTRUCTIONS anti-template-lock guidance |
| B2 | Bug | `enrich_potential_levers.py:282–283` | `unknown_lever_id` appended to `errors` for haiku's expected over-generation — conflates benign model noise with real failures |
| S1 | Suspect | `enrich_potential_levers.py:261–266` | `execute_function` closure captures `chat_message_list` without snapshot (contrast with `identify_potential_levers.py:317–322`) — safe now but inconsistent |
| S2 | Suspect | `enrich_potential_levers.py:177,254` | Duplicate exact-count instruction in both system and user prompts — abstract + concrete count may confuse function-calling models |
| S3 | Suspect | `enrich_potential_levers.py:149–153` | `BatchCharacterizationResult.characterizations` lacks rationale comment explaining why `max_length` is omitted — risk of future accidental cap |
| I1 | Improvement | `enrich_potential_levers.py:282–283` | Suppress `errors.append` for `unknown_lever_id` — remove noise from failure signal |
| I2 | Improvement | `enrich_potential_levers.py:149–153` | Add no-max_length rationale comment (parallel to `identify_potential_levers.py:188–189`) |
| I3 | Improvement | `enrich_potential_levers.py:177` | Remove system-level abstract count instruction; keep only user-level concrete count |
| I4 | Improvement | `identify_potential_levers.py:116–119` | Replace English-specific negative prohibition in `consequences` field description with positive framing |
