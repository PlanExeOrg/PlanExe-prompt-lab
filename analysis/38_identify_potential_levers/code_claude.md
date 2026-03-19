# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #356 — "fix: B1 step-gate, medical example, review length cap"

---

## Bugs Found

### B1 — Hard fail with no retry on first-call validation error
**File:** `identify_potential_levers.py:321–322`

```python
if len(responses) == 0:
    raise llm_error from e
```

When the first LLM call produces a `DocumentDetails` response where any `Lever` fails
`check_option_count` (i.e., `len(options) < 3`), Pydantic rejects the entire batch.
Because `responses` is still empty at that point, line 321 raises `LLMChatError`
immediately — no retry, no partial output, no continuation.

This is the direct cause of run 73 (llama3.1, gta_game) becoming a hard fail. All 7
levers in the first call had 1–2 options:
```
levers.0.options: options must have at least 3 items, got 2
levers.2.options: options must have at least 3 items, got 1
...
```
`len(responses) == 0` → raise immediately.

Before PR #356, run 52 (same model, same plan) succeeded with a partial recovery
(calls_succeeded: 2). The behavioral change that caused llama3.1 to return under-generated
options on the first call is likely example-driven, but the code makes zero first-call
retry attempts regardless. A single retry with emphasis on "exactly 3 options per lever"
would have been the safe fallback.

**Severity:** High — converts stochastic under-generation into a guaranteed hard fail
with zero output for that plan.

---

### B2 — `check_option_count` upper bound is unenforced
**File:** `identify_potential_levers.py:140–141`

```python
if len(v) < 3:
    raise ValueError(f"options must have at least 3 items, got {len(v)}")
```

The validator rejects `< 3` but silently accepts `> 3`. The field description says
"Exactly 3 options. No more, no fewer." and the system prompt section 1 says "exactly 3
qualitative strategic choices." A lever returned with 4 or 5 options passes validation
without warning and is written to the output file.

This contradicts the stated contract. Downstream steps (`EnrichLevers`,
`ScenarioGeneration`) that index into `lever.options[2]` are safe, but the data contract
is violated. The comment at `DocumentDetails.levers` (lines 167–169) says "Over-generation
is fine; DeduplicateLevers handles extras" — but that applies to *lever count*, not to
*option count per lever*. These are different things.

If the intent is to allow > 3 options, the field description ("No more, no fewer") and
system prompt ("exactly 3") need to be updated. If the intent is to enforce exactly 3,
the validator needs an upper-bound check.

**Severity:** Medium — schema contract violation, potential data quality issue.

---

### B3 — `dispatcher.event_handlers.remove()` called without lock
**File:** `runner.py:192–194` (add, under lock) vs. `runner.py:220–222` (remove, no lock)

```python
# add — correctly protected:
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)

# remove — NOT protected:
finally:
    with _file_lock:
        set_usage_metrics_path(None)
        dispatcher.event_handlers.remove(track_activity)   # ← inside _file_lock? No.
```

Wait — re-reading lines 220–222:
```python
    finally:
        with _file_lock:
            set_usage_metrics_path(None)
            dispatcher.event_handlers.remove(track_activity)
```

The remove IS inside `_file_lock`. But the lock is a threading.Lock, meaning it is
held by only one thread at a time. If two plan threads finish simultaneously and both
reach the `finally` block, they will each wait on `_file_lock` and then call
`dispatcher.event_handlers.remove(track_activity)` sequentially. The sequencing is
correct. **This is not a bug.** Disregard.

The real concern is that `dispatcher.event_handlers` is a global list shared across
threads. When `workers > 1`, multiple threads add to it concurrently (under lock) and
remove from it (under lock). The list is protected correctly by `_file_lock`.

---

## Suspect Patterns

### S1 — `partial_recovery` threshold `< 3` conflates efficiency with failure
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

The threshold `< 3` with `expected_calls=3` treats any 2-call completion as a
"partial recovery." But `min_levers=15` with 5–7 levers per call means 2 calls is
the normal happy path for models that consistently return 7–8 levers per call (2 × 8
= 16 ≥ 15). Run 73 (llama3.1, parasomnia) shows `calls_succeeded=2` and emits
`partial_recovery` even though it succeeded normally.

This inflates the partial_recovery metric and makes it impossible to distinguish:
- Model stopped early due to errors on call 2
- Model efficiently hit `min_levers` in 2 calls

The `_run_levers` function comment (lines 119–122) acknowledges this: "A 2-call success
is normal for models that produce 8+ levers per call." Yet the warning fires anyway
and emits an event that looks like a failure.

**Fix direction:** Pass a `partial` flag from `_run_levers` when `actual_calls < 3` AND
`len(result.levers) < min_levers`, rather than using a fixed call-count threshold.

---

### S2 — `review_lever` length guidance is soft-only; haiku ignores it
**File:** `identify_potential_levers.py:243` (system prompt), `109–116` (field definition)

The system prompt section 6 says "aim for 20–40 words" and the `Lever.review_lever`
field has no `max_length` Pydantic constraint. Haiku produces reviews averaging ~58
words (~355 chars) in run 79, exceeding the 40-word cap by ~45%. The soft guidance
is insufficient for haiku.

Adding a hard `max_length` on `Lever.review_lever` risks rejecting entire batches
when a model writes one long review. A safer approach is truncation in the
`LeverCleaned` constructor (lines 352–358) after the model output is accepted:

```python
review=lever.review_lever[:300],   # soft truncation, not rejection
```

This preserves the accepted batch while capping output length.

---

### S3 — English marker examples in `consequences` field description reach the LLM
**File:** `identify_potential_levers.py:100–101`

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
```

This text is in `Lever.consequences` — a Pydantic field whose description is serialized
into the JSON schema sent to the LLM. Non-English LLMs receiving a Chinese or Arabic
plan context will see these English-only example phrases embedded in the schema. This
conflicts with OPTIMIZE_INSTRUCTIONS (lines 61–68): "Validators and auto-correct logic
must not rely on English keywords."

The instruction is prompting the LLM what NOT to do, but it does so using English-specific
examples. In non-English contexts, the LLM may (a) not recognize the terms, (b) copy them
into output, or (c) be confused by mixed-language instructions.

The `LeverCleaned.consequences` field (lines 188–195) has the same text, but that class
is correctly not serialized to the LLM (as noted at lines 200–202).

---

### S4 — `messages_snapshot = list(call_messages)` is a redundant shallow copy
**File:** `identify_potential_levers.py:296`

```python
messages_snapshot = list(call_messages)
```

`call_messages` is a new list constructed on every loop iteration and never mutated after
this line. The snapshot was likely added to guard the closure `execute_function` against
capturing a mutating reference, but `call_messages` is reassigned (not mutated) each
iteration. The copy is harmless but unnecessary.

---

### S5 — `_run_levers` logs a warning for 2-call success
**File:** `runner.py:120–124`

```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

The comment says "A 2-call success is normal for models that produce 8+ levers per call"
but the warning fires regardless. This adds noise to logs without indicating whether
`min_levers` was satisfied. The warning should only fire when `len(result.levers) < min_levers`.

---

## Improvement Opportunities

### I1 — Add single retry for first-call validation failure
**File:** `identify_potential_levers.py:308–327`

When `len(responses) == 0` after a Pydantic validation error, add one retry of
`call_index=1` with an augmented prompt that emphasizes the constraint:
```
"CRITICAL: Each lever MUST have exactly 3 options. Generating fewer than 3 options
per lever invalidates the entire response. ..."
```
This converts run 73's hard fail into a recoverable stochastic event. Evidence: the
7 under-generated levers were not a model limitation — the same model (llama3.1) produced
valid options on gta_game in run 52 before the example change.

---

### I2 — Truncate `review` in `LeverCleaned`, not reject in `Lever`
**File:** `identify_potential_levers.py:352–358`

Add soft truncation when mapping `review_lever` → `review`:
```python
review=lever.review_lever[:300],
```
This enforces a structural length cap without risking batch rejection. The downstream
`EnrichLevers` step adds further detail anyway, so truncating at ~250–300 chars is
a safe upper bound.

---

### I3 — Replace one "X, but Y" review example with a non-contrastive structure
**File:** `identify_potential_levers.py:230–233`

Current examples 1 and 3 both end with `..., but ...`:
- Example 1: "stabilizes harvest quality, **but** the idle-wage burden..."
- Example 3: "reduces expected annual loss on paper, **but** a single regional hurricane
  season can correlate..."

OPTIMIZE_INSTRUCTIONS (lines 73–82) states: "No two examples should share a sentence
pattern or rhetorical structure." Despite this, 2/3 examples use the same "X, but Y"
contrastive pattern. Run 79 (haiku, gta_game) shows 14+ reviews following "X
promises/offers Y but introduces/creates Z" — directly copying this shared structure.

Replace example 1 or 3 with a conditional or additive framing that avoids "but":
- Conditional: "If X then Y; if Z then W — the real question is which condition the
  plan is actually in."
- Additive: "X addresses A and B, yet leaves C entirely undecided — and C is the
  variable most sensitive to market shift."

---

### I4 — Align `options` field description with validator behavior
**File:** `identify_potential_levers.py:105–108` (field), `130–142` (validator)

The field description says "No more, no fewer" but the validator only rejects `< 3`.
If over-generation is acceptable (as OPTIMIZE_INSTRUCTIONS says at line 44), remove
"No more, no fewer" from the field description and change "Exactly 3" to "At least 3."
If exactly 3 is required, add the upper-bound check:
```python
if len(v) > 3:
    raise ValueError(f"options must have exactly 3 items, got {len(v)}")
```

---

### I5 — Document first-call hard-fail risk in OPTIMIZE_INSTRUCTIONS
**File:** `identify_potential_levers.py:27–86`

OPTIMIZE_INSTRUCTIONS covers verbosity amplification, template lock, and English-only
validators, but does not document the `len(responses) == 0` hard-fail path. Add:

> **First-call batch rejection.** If the first LLM call produces a response where
> any lever fails schema validation (e.g., `options < 3`), the entire batch is
> rejected and `len(responses) == 0`. The code raises immediately — no retry, no
> partial output. This converts stochastic under-generation into a guaranteed hard
> fail. Mitigate with a single first-call retry before raising.

---

## Trace to Insight Findings

| Insight ID | Code Location | Explanation |
|-----------|---------------|-------------|
| N1 (llama3.1 gta_game hard fail) | `identify_potential_levers.py:321–322` | `len(responses)==0` path raises immediately; no retry for first-call validation failure (B1) |
| N1 (cause: options 1–2) | `identify_potential_levers.py:140–141` | `check_option_count` correctly rejects but offers no recovery mechanism — the example change likely caused llama3.1 to under-generate; no retry absorbs the stochastic miss |
| N2 (haiku reviews too long) | `identify_potential_levers.py:243`, `109–116` | Soft "20–40 words" guidance with no Pydantic enforcement; haiku ignores it (S2) |
| N3 (haiku consequences 2.8× longer) | `identify_potential_levers.py:95–104` | `consequences` has no length constraint; haiku's verbosity amplification is uncontrolled |
| N4 (fabricated percentages) | `identify_potential_levers.py:239` | Section 5 prohibition is text-only; no structural enforcement prevents fabricated numbers |
| N5 (template lock, "X but Y") | `identify_potential_levers.py:230–233` | Two of three review examples share "X, but Y" contrastive structure; haiku copies the shared pattern (I3) |
| P1 (haiku gta_game no longer EOF) | Prompt change: section 6 length guidance | Soft guidance reduced haiku reviews from ~550 to ~355 chars; enough to clear 40KB threshold |
| P6 (partial_recovery scoped to step) | `runner.py:517` | `step == "identify_potential_levers"` guard added by PR #356 — confirmed working |
| Q3 (no first-call retry) | `identify_potential_levers.py:321–322` | Confirmed: no retry path exists when `len(responses)==0` (I1) |
| Q4 (enforce review length?) | `identify_potential_levers.py:352–358` | Truncation in `LeverCleaned` is the safe path — avoids batch rejection (I2) |
| Q5 (break "X but Y" template) | `identify_potential_levers.py:230–233` | Structural fix: replace one "but"-framed example with additive or conditional framing (I3) |

---

## PR Review

### B1 Fix (scope `partial_recovery` to `identify_potential_levers`)

**Implementation:** `runner.py:517` — `if step == "identify_potential_levers" and ...`

**Correct.** Previously the event was emitted for all steps; now it fires only for this
step. Confirmed working: runs 73–79 show `partial_recovery` only for
`identify_potential_levers` events with correct `expected_calls: 3`.

**Gap:** The `expected_calls=3` value is still hardcoded. For models that reach
`min_levers=15` in 2 calls, `calls_succeeded=2` triggers `partial_recovery` even on
a successful run (S1). Run 73 parasomnia fires it despite the plan succeeding with
21 levers. This metric inflation was not addressed by the PR.

---

### Medical Example (replace urban-planning with IRB/clinical-site)

**Implementation:** `identify_potential_levers.py:231`

```
"Each additional clinical site requires its own IRB approval, site-initiation visit,
and staff credentialing — a sequential overhead that compounds rather than parallelizes,
so doubling site count does not halve enrollment time."
```

**Domain collision fix: correct.** No game-dev example remains; the new example uses
medicine/clinical trials, which does not overlap with any of the five test plans.

**Structural homogeneity issue introduced.** The insurance example (example 3) uses
"reduces..., **but** a single...". The agriculture example (example 1) uses "stabilizes...,
**but** the idle-wage burden...". Now 2 of 3 examples share the contrastive "X, but Y"
structure. The medical example (example 2) correctly uses a different structure
("A requires B — sequential overhead — so C does not D").

But haiku runs show template lock on the "X but Y" pattern across 14+ reviews (N5).
OPTIMIZE_INSTRUCTIONS explicitly warns: "No two examples should share a sentence pattern
or rhetorical structure." The PR did not break the 2/3 "but" pattern and may have
worsened it by keeping the insurance example structurally similar to the agriculture
example.

**Correlation with llama3.1 regression.** The new examples include domain-specific
language (IRB approvals, catastrophe risk pooling) that differs substantially from the
urban-planning / Section 106 context that was removed. Run 73 (llama3.1) on gta_game
failed on first call with under-generated options. Whether this is causal (new examples
disrupted llama3.1's output format on game-dev plans) or stochastic is unclear, but the
timing is suspicious. B1's no-retry code ensures any first-call under-generation becomes
a guaranteed hard fail.

---

### Review Length Cap ("20–40 words" guidance in section 6)

**Implementation:** `identify_potential_levers.py:243`

```
"Keep each `review_lever` under 2 sentences (aim for 20–40 words)."
```

**Partially effective.** Haiku gta_game reviews dropped from ~550 chars (iter 37) to
~355 chars (run 79) — enough to prevent the 40KB EOF crash. So the primary goal
(prevent haiku EOF hard fail) was achieved.

**Insufficient for compliance.** ~355 chars ≈ 58 words, which is 45% above the 40-word
target. The guidance is soft — no Pydantic `max_length`, no truncation in code. The PR's
claim to "cap" review length is only partially true. Haiku complies enough to avoid EOF
but not enough to meet the stated word target.

**No structural enforcement was added.** The fix works for now because 355 chars × 21
levers × 3 calls ≈ 22KB which is below the ~40KB threshold. But if haiku ever reverts
to 450 chars/review, the EOF failure returns with no code-level safety net.

---

### Summary Assessment

The PR achieves its primary goal (haiku gta_game EOF fix, P1) and its scoping fix (B1
partial_recovery event, P6). However it introduces or leaves unaddressed:

1. **No first-call retry logic** — the llama3.1 regression (run 73, gta_game → hard fail)
   is directly caused by B1 in combination with first-call under-generation. The PR does
   not add a retry path.

2. **Review length enforcement is fragile** — the 20–40 word guidance works marginally
   but is not structurally enforced. A Pydantic-level max_length or truncation in
   `LeverCleaned` would be more durable.

3. **2/3 review examples share "X, but Y" structure** — haiku's template lock on this
   pattern persists. The PR replaced the example that caused domain collision but
   maintained the shared contrastive structure.

4. **`partial_recovery` threshold is still misleading** — 2-call efficient completions
   are reported as partial recoveries, inflating the metric.

---

## Summary

**Confirmed bugs:**
- **B1** (`identify_potential_levers.py:321–322`): No retry on first-call validation
  failure. When `len(responses)==0`, raises immediately. This is the proximate cause of
  run 73's hard fail.
- **B2** (`identify_potential_levers.py:140–141`): `check_option_count` only enforces
  lower bound (≥ 3). Upper bound (≤ 3) unenforced despite "no more, no fewer" spec.

**Key suspect patterns:**
- **S1** (`runner.py:517–523`): `partial_recovery` threshold `< 3` conflates efficient
  2-call completions with partial failures, inflating the metric.
- **S2** (`identify_potential_levers.py:243`): Soft length guidance for `review_lever`
  without structural enforcement; haiku ignores it.
- **S3** (`identify_potential_levers.py:100–101`): English-only examples in
  `consequences` field description sent to the LLM; conflicts with OPTIMIZE_INSTRUCTIONS
  warning about non-English prompts.

**Top improvement opportunities:**
- **I1**: Add single retry when `len(responses)==0` with an emphatic options-count prompt.
- **I2**: Truncate `review` in `LeverCleaned` constructor (not a validator) to enforce
  a soft length cap without risking batch rejection.
- **I3**: Replace one "X, but Y" review example with a conditional or additive structure
  to break the 2/3 shared rhetorical pattern and reduce haiku template lock.
- **I5**: Document the first-call hard-fail risk in `OPTIMIZE_INSTRUCTIONS`.

The PR's net effect is one new hard fail (llama3.1 gta_game, run 73) traded for one
hard fail eliminated (haiku gta_game EOF, P1). The reliability balance is roughly neutral
but the regression is more severe in kind: haiku's EOF was a recoverable prompt-size
issue; llama3.1's hard fail produces zero output.
