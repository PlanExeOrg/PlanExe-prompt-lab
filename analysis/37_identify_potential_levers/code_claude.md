# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #355 — "fix: B1 step-gate partial_recovery, add medical review example"

---

## Bugs Found

### B1 — `check_review_format` validator accepts lever name verbatim as review
**File:** `identify_potential_levers.py:139–155`

```python
@field_validator('review_lever', mode='after')
@classmethod
def check_review_format(cls, v):
    if len(v) < 10:
        raise ValueError(...)
    if '[' in v or ']' in v:
        raise ValueError(...)
    return v
```

The only structural checks are: length ≥ 10 chars and no square brackets. A model can return the lever name verbatim as `review_lever` (e.g. `"Resource Prioritization"` — 22 chars, no brackets) and the validator passes silently. This is exactly what llama3.1 did for silo call-1 in run 66: all 6 levers from the first call have `review_lever == name`. The validator lets them through unchanged, and they appear in the cleaned output as `"review": "Resource Prioritization"`.

The fix requires a **model-level** validator (Pydantic `@model_validator(mode='after')`) rather than a field validator, because the field validator for `review_lever` cannot access the sibling `name` field. A model validator can compare `self.review_lever.strip().lower() == self.name.strip().lower()` and raise a `ValueError` to force a retry.

Additionally, the 10-char minimum is too low. Lever names such as "Silo Expansion" (14 chars) or "Waste Management" (16 chars) pass the length check while still being empty reviews. A minimum of 30–40 chars would better separate real reviews from placeholder names.

---

### B2 — `partial_recovery` event threshold hardcoded at 3 regardless of actual lever count
**File:** `runner.py:517–523`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

The adaptive loop in `IdentifyPotentialLevers.execute()` stops as soon as `len(generated_lever_names) >= min_levers` (currently 15). A model that generates 8–9 levers per call legitimately finishes in 2 calls with 16–18 levers — a full success. The runner nevertheless emits a `partial_recovery` event for any `calls_succeeded < 3`, regardless of whether the lever count was actually met.

This creates two problems:

1. **False alarms** in `events.jsonl` that analysis tooling interprets as degraded reliability.
2. **Opaque threshold**: the `< 3` literal is derived from a rough estimate (5–7 levers/call → ~3 calls to reach 15) that is baked in as a constant. If `min_levers` is ever changed, this threshold silently diverges.

The companion check in `_run_levers()` (line 120–124) has the same issue — it logs a `WARNING` for every 2-call success, even when the lever count was met:

```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

The correct fix is to pass the final lever count back through `PlanResult` and emit `partial_recovery` only when `actual_levers < min_levers` (i.e., the minimum threshold was not reached), regardless of call count.

---

### B3 — `expected_calls=3` constant not removed from event emission (PR gap)
**File:** `runner.py:523`

```python
_emit_event(events_path, "partial_recovery",
            plan_name=plan_name,
            calls_succeeded=pr.calls_succeeded,
            expected_calls=3)   # ← still hardcoded
```

The PR description says it "removed stale `expected_calls=3` constant from `_run_levers`." The removal was done from `_run_levers()` itself, but the `_run_plan_task()` event emission still passes `expected_calls=3` as a hardcoded literal. This value appears in `history/2/72_identify_potential_levers/events.jsonl` line 8 (`"expected_calls": 3`) and in the B1 discussion. For identify_potential_levers this value is accidentally correct (the loop nominally targets 3 calls), but it should either be derived from `PlanResult` or removed from the event payload entirely to avoid misleading analysis output.

---

## Suspect Patterns

### S1 — `execute_function` closure captures `messages_snapshot` by variable reference
**File:** `identify_potential_levers.py:282–300`

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)  # ← closed-over variable
    ...

result = llm_executor.run(execute_function)
```

`execute_function` captures `messages_snapshot` by name, not by value. Because `llm_executor.run()` is synchronous (blocking), `messages_snapshot` still holds the correct per-iteration value when `execute_function` is called. There is no actual bug under current usage.

However, if `LLMExecutor.run()` ever acquires an async or deferred execution path (e.g., enqueuing the function for later dispatch), the closure would capture the final iteration's `messages_snapshot` for all calls — a hard-to-diagnose regression. The safe pattern is to capture the value at definition time: `def execute_function(llm: LLM, _snap=messages_snapshot) -> dict: sllm.chat(_snap)`.

---

### S2 — Ollama `num_output: 256` in metadata may mask actual token budget
**File:** `identify_potential_levers.py:295` (metadata extraction path)

The raw file `history/2/66_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` shows:

```json
"metadata_1": {"num_output": 256, "model_name": "llama3.1:latest", ...}
```

Ollama's default `num_output` (reported in `llm.metadata`) is 256 tokens. The actual structured-output responses are much longer (6 full levers × ~200 tokens each ≈ 1,200+ tokens), so the `num_output` value in metadata is clearly not the actual generation limit. LlamaIndex's Ollama backend likely ignores this field for structured generation.

This is suspect because: (a) it produces misleading metadata stored in `002-9-potential_levers_raw.json`, and (b) if any code ever uses `metadata["num_output"]` to set `max_tokens` for a subsequent call, it would silently truncate output. Worth verifying that no downstream code reads this field to set a token cap.

---

## Improvement Opportunities

### I1 — No `max_tokens` guard for verbose models (root cause of haiku gta_game failure)
**File:** `identify_potential_levers.py:292–296`

```python
def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)   # ← no max_tokens
```

The Anthropic haiku model (run 72) generated reviews averaging ~550 chars per lever for parasomnia. For gta_game (21+ raw levers × 3 calls × ~1,500 chars/lever in JSON), the response exceeded the Anthropic output limit, producing a hard EOF at column 40173 with no output generated.

The fix is to pass a `max_tokens` parameter to the structured chat call, or to add a per-model soft constraint in the system prompt. A suitable value for `identify_potential_levers` is 8,000–12,000 tokens (covers 3 calls of 5–7 levers at 500 chars each). LlamaIndex's `as_structured_llm` passes through `additional_kwargs` to the underlying provider, so:

```python
chat_response = sllm.chat(messages_snapshot, max_tokens=10000)
```

Alternatively, add to section 6 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`: "Keep each `review_lever` under 150 words."

---

### I2 — `review_lever` examples violate OPTIMIZE_INSTRUCTIONS own guidance on shared sentence patterns
**File:** `identify_potential_levers.py:225–228`

The current three examples in section 4:

1. *"Switching from X to Y stabilizes Z, but [burden] adds [cost] unless [condition]."*
2. *"[Process] requires [steps] — a sequential overhead ... that compounds rather than parallelizes, so doubling [X] does not halve [Y]."*
3. *"[Strategy] reduces [metric] on paper, but [correlated risk] can [event], turning the [assumption] into [opposite outcome]."*

Examples 1 and 3 share the same adversarial contrast structure: "X [positive verb] Y, but [hidden risk] [negates outcome]." OPTIMIZE_INSTRUCTIONS (lines 74–81) explicitly states: "No two examples should share a sentence pattern." This shared structure is a plausible source of the "[Name] lever misses/overlooks/neglects" pattern seen in llama3.1 parasomnia call 3 (run 66) — the model extracts the contrast pattern from example 1/3 and applies it with the lever name as subject.

Example 2 (the new medical IRB example from this PR) uses a compound-step chain structure ("requires A, B, C — sequential overhead... so doubling X does not halve Y") that is structurally distinct. The two agricultural/insurance examples should be updated to avoid the shared "X, but Y" contrast opener.

---

### I3 — `levers` field has no `max_length`, contributing to haiku verbosity/overflow risk
**File:** `identify_potential_levers.py:165–168`

```python
levers: list[Lever] = Field(
    min_length=5,
    description="Propose 5 to 7 levers."
)
```

The comment above (lines 162–164) correctly explains why `max_length` is not set: a hard cap would discard the whole response and waste tokens. However, the lack of an upper bound means a verbose model can return 15–20 levers in a single call. Combined with haiku's ~550-char reviews, this multiplies the output size and exacerbates the token overflow risk.

A softer mitigation: add `"Do not generate more than 7 levers per response"` to the system prompt. This keeps the schema permissive but gives the model a clear upper target. The system prompt already says "5 to 7 levers" but models may over-generate regardless.

---

### I4 — `partial_recovery` threshold in `_run_levers()` warning fires for normal 2-call runs
**File:** `runner.py:120–124`

```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

This `logger.warning` fires for every 2-call success, cluttering logs for models that regularly produce 8+ levers per call. It should be demoted to `logger.info` or gated behind a lever-count check: only warn if `len(result.levers) < min_levers`.

---

### I5 — OPTIMIZE_INSTRUCTIONS should document the verbosity-amplification risk
**File:** `identify_potential_levers.py:27–81`

The `OPTIMIZE_INSTRUCTIONS` "Known problems" list (lines 46–81) does not yet include the verbosity-amplification failure mode observed in run 72. Strong instruction-following models (haiku, GPT-4 family) mirror the *verbosity level* of system-prompt examples, not just their structure. The medical IRB example is ~250 words; haiku produced reviews of ~550 words each.

Proposed addition to `OPTIMIZE_INSTRUCTIONS`:

> - **Verbosity amplification in strong models**. Instruction-following models (e.g. Claude haiku, GPT-4 family) often mirror the length of `review_lever` examples in the system prompt. A 250-word example licenses 500-word reviews across all levers. For plans with 21+ raw levers × 3 calls, this multiplies total output size and can cause JSON EOF errors. Keep every `review_lever` example under 80 words. Add an explicit length cap to Section 6: "Keep each `review_lever` under 120 words."

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|---|---|
| N1 — Haiku gta_game JSON EOF at column 40173 | I1: no `max_tokens` guard; I3: no max levers per call; I2: verbose example drives haiku to ~550-char reviews |
| N2 — llama3.1 silo call-1 reviews are just lever names | B1: `check_review_format` validator accepts any string ≥ 10 chars with no brackets — lever names pass |
| N4 — partial_recovery persists for haiku hong_kong | B2: threshold hardcoded at `< 3` calls regardless of lever count; B3: `expected_calls=3` still in event payload |
| N5/N6 — template lock in parasomnia calls 1 and 3 | I2: examples 1 and 3 share "X, but Y" sentence structure, giving llama3.1 a reusable contrast template |
| N3 — llama3.1 gta_game identical output across runs | Not directly a code bug; likely temperature=0 determinism in Ollama + no game-dev example |

---

## PR Review

### B1 fix (scope `partial_recovery` to `identify_potential_levers`)

**Implementation (`runner.py:517`):** The step condition `if (step == "identify_potential_levers"` is correct and properly prevents spurious `partial_recovery` events for `identify_documents` (which always returns `calls_succeeded=1`). The intent matches the implementation.

**Gap:** The `expected_calls=3` literal on line 523 is still hardcoded in the event payload (B3 above). The PR description says it "removed stale `expected_calls=3` constant from `_run_levers`" — and it did remove a variable from `_run_levers()`. But the same value lives on in `_run_plan_task()` event emission, unchallenged. For identify_potential_levers this is accidentally correct, but it is conceptually stale: the comment at `_run_levers()` lines 117–119 acknowledges that 2-call completion is normal, while the event still says `expected_calls=3`.

**Overall:** The B1 fix is logically correct and non-regressive for identify_documents. The remaining hardcoded `3` in the event payload is a minor cleanup gap, not a functional bug.

---

### Medical review example

**Intent:** Replace the urban-planning (Section 106 heritage review) example with a medical domain (IRB/clinical-site sequential overhead) to break template lock in plans with medical or scientific themes.

**Implementation (`identify_potential_levers.py:226–227`):**
```
"Each additional clinical site requires its own IRB approval, site-initiation visit, and staff credentialing — a sequential overhead of 8–14 weeks per site that compounds rather than parallelizes, so doubling site count does not halve enrollment time."
```

The example is structurally distinct from the agricultural example (compound-step chain vs. cost-threshold contrast) and covers a new domain. This matches the stated intent.

**Regression introduced:** The example is ~50 words and names concrete mechanisms (IRB approval, site-initiation visit, 8–14 weeks). Strong instruction-following models (haiku) interpret this as a license for similarly detailed reviews. Run 72 haiku parasomnia reviews averaged ~550 chars — about 3.9× the baseline. For gta_game (a plan with 21+ raw levers per dedup cycle), this verbosity caused a JSON EOF hard failure with no output produced. The PR does not add any length constraint to counterbalance the verbose example.

**Unaddressed domain gap:** The PR covers agriculture, medical, insurance. The gta_game plan domain (game development / interactive entertainment) remains uncovered. llama3.1 gta_game produced byte-for-byte identical output in runs 52 and 66, confirming the domain gap. A fourth example in the software/game-dev domain (or a temperature increase for deterministic models) is needed to address this.

**Verdict:** The B1 fix should be kept unconditionally. The medical example produces a measurable partial improvement (llama3.1 parasomnia call-2 template lock broken 100% → 0%) but introduces a haiku token overflow risk that must be addressed before this PR represents a clean win.

---

## Summary

### Confirmed bugs

| ID | Location | Description |
|---|---|---|
| B1 | `identify_potential_levers.py:151–155` | `check_review_format` validator accepts lever name verbatim as review (≥ 10 chars, no brackets); requires a model-level cross-field validator |
| B2 | `runner.py:517–523` + `120–124` | `partial_recovery` threshold `< 3` is hardcoded and fires for legitimate 2-call success; should gate on actual lever count vs. `min_levers` |
| B3 | `runner.py:523` | `expected_calls=3` still hardcoded in event payload after PR; stale constant not fully removed |

### Improvement opportunities

| ID | Location | Description |
|---|---|---|
| I1 | `identify_potential_levers.py:292–296` | No `max_tokens` guard for haiku / verbose models; haiku gta_game hard failure (N1) is directly caused by this omission |
| I2 | `identify_potential_levers.py:225–228` | Examples 1 and 3 share "X, but Y" contrast structure, contradicting OPTIMIZE_INSTRUCTIONS guidance; likely source of parasomnia call-3 "[Name] lever overlooks" lock (N5/N6) |
| I3 | `identify_potential_levers.py:165–168` | No `max_length` on `levers` field; verbose models can return 15–20 levers per call, amplifying the I1 token overflow risk |
| I4 | `runner.py:120–124` | `logger.warning` fires for every 2-call success; should be `logger.info` or gated behind lever-count check |
| I5 | `identify_potential_levers.py:27–81` | `OPTIMIZE_INSTRUCTIONS` missing verbosity-amplification failure mode; examples should be capped at ≤ 80 words each |

### Priority order

1. **I1** (add `max_tokens` guard) — prevents the haiku gta_game hard failure; critical for reliability
2. **B1** (model-level review ≠ name validator) — prevents empty reviews from passing silently
3. **I2** (fix shared example sentence structure) — reduces template lock in non-haiku models
4. **B2** (fix `partial_recovery` threshold) — reduces false alarm noise
5. **I5** (update OPTIMIZE_INSTRUCTIONS) — documentation/guard for future examples
