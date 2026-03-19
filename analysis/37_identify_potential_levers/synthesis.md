# Synthesis

## Cross-Agent Agreement

Both agents agree on the following:

1. **PR verdict: CONDITIONAL.** The B1 fix (scoping `partial_recovery` events to `identify_potential_levers`, removing stale `expected_calls=3` from `_run_levers`) is logically correct and should be kept unconditionally. The medical example delivers a partial improvement with a measured regression.

2. **Haiku gta_game hard failure is a new regression** (N1). Run 58 haiku passed gta_game; run 72 failed with `LLMChatError` (JSON EOF at column 40,173). The most plausible cause is the medical IRB example prompting haiku to generate reviews ~3.9× baseline length (~550 chars vs ~140 chars), which overflows the Anthropic output limit for the largest plan (gta_game, 21+ raw levers × 3 calls).

3. **llama3.1 silo call-1 empty reviews are a regression** (N2). Levers 1–6 from the first LLM call have `review == name` ("Resource Prioritization", "Security Protocols", etc.). These pass the current `check_review_format` validator (len ≥ 10, no brackets) silently. Run 52 had substantive reviews for the same levers.

4. **Medical example broke parasomnia call-2 template lock** (P1). Lock rate for llama3.1 parasomnia call 2 dropped from 100% ("The lever misses") to 0% (mechanism-based). This is the intended effect and confirms the domain-matching hypothesis.

5. **llama3.1 gta_game is entirely unchanged** (N3). Both runs 52 and 66 produce byte-for-byte identical `002-10-potential_levers.json`, including all lever UUIDs. The game-dev domain remains uncovered by any of the three current examples.

6. **A `max_tokens` guard is needed** to prevent haiku (and future verbose models) from overflowing. The current `sllm.chat(messages_snapshot)` call has no token budget.

7. **OPTIMIZE_INSTRUCTIONS should document the verbosity-amplification failure mode.** Neither the current `OPTIMIZE_INSTRUCTIONS` constant nor the system prompt caps `review_lever` length.

---

## Cross-Agent Disagreements

**Disagreement 1: Root cause of empty reviews (N2)**

- *Insight* frames N2 as a quality regression and suggests investigating whether it is stochastic or deterministic (Q1).
- *Code review* identifies the structural root cause: the `check_review_format` field validator cannot compare `review_lever` to `name`. It requires a Pydantic `@model_validator(mode='after')` to do the cross-field check. The 10-char minimum is also too low — "Silo Expansion" (14 chars) passes while containing zero review content.

**Verdict: Code review is right.** I confirmed at line 139–155 of `identify_potential_levers.py` that the validator checks only `len(v) < 10` and the absence of square brackets. A lever name like "Resource Prioritization" (22 chars, no brackets) passes unconditionally. The fix requires a model-level validator.

**Disagreement 2: Shared contrast structure in examples (I2)**

- *Insight* does not explicitly flag that examples 1 and 3 share the "X [positive verb] Y, but [hidden risk] [negates outcome]" pattern.
- *Code review* identifies this as a likely source of the new "[Lever Name] lever overlooks/neglects" lock in parasomnia call 3 (N6). It cites OPTIMIZE_INSTRUCTIONS lines 74–81: "No two examples should share a sentence pattern."

**Verdict: Code review is right.** Reading `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 confirms examples 1 and 3 both use adversarial contrast ("stabilizes X, but [burden] adds [cost] unless [condition]" and "reduces [metric] on paper, but [correlated risk] can [event]"). Example 2 (medical IRB) is structurally distinct (compound-step chain). OPTIMIZE_INSTRUCTIONS explicitly forbids shared sentence patterns between examples, so examples 1 and 3 violate their own guard.

**Disagreement 3: Temperature as root cause of llama3.1 gta_game lock**

- *Insight* raises Q4 and C4: if llama3.1 runs at temperature=0, prompt changes cannot break the gta_game lock — a code change (temperature increase) is needed.
- *Code review* treats the determinism as downstream of the domain gap, not a temperature configuration.

**Verdict: Both may be partially right.** The byte-for-byte UUID identity across runs 52 and 66 strongly implies temperature=0 or equivalent determinism. However, the domain gap is also real — even at temperature=1, a model with no game-dev example to draw from will default to its pretrained template. The correct fix sequence is: (a) add a game-dev example, then (b) if still locked, increase temperature. Temperature should not be changed without the example in place.

---

## Top 5 Directions

### 1. Add `max_tokens` guard to `sllm.chat()` call
- **Type**: code fix
- **Evidence**: code_claude I1, insight N1/C1. Run 72 haiku gta_game produced JSON EOF at column 40,173 with no output. Run 72 haiku parasomnia reviews averaged ~550 chars each. The haiku ok-rate dropped from 100% (run 58) to 80% (run 72). The `execute_function` closure at `identify_potential_levers.py:292–296` passes no `max_tokens`.
- **Impact**: Restores haiku gta_game to passing. Prevents any model with verbose output from triggering a hard EOF failure. Affects all models running on providers that enforce an output token limit (Anthropic, OpenAI). Also add a system-prompt directive "Keep each `review_lever` under 120 words" as a complementary soft cap.
- **Effort**: Low — single parameter addition to `sllm.chat()` and one sentence added to the system prompt.
- **Risk**: Setting `max_tokens` too low could truncate valid responses from verbose-by-design plans. A value of 10,000–12,000 covers 3 calls × 7 levers × ~500 chars/lever comfortably; parasomnia at 550-char reviews × 21 levers × 3 calls = ~35K chars ≈ ~8,750 tokens, so 12,000 is safe.

### 2. Add model-level validator: `review_lever` must differ from `name`
- **Type**: code fix
- **Evidence**: code_claude B1, insight N2/E4. `check_review_format` at `identify_potential_levers.py:139–155` is a field validator that cannot access the sibling `name` field. A `@model_validator(mode='after')` can compare `self.review_lever.strip().lower() == self.name.strip().lower()` and raise `ValueError`. The current 10-char minimum is too low — lever names routinely exceed 10 chars.
- **Impact**: Forces a retry when a model returns a lever name as its own review. In run 66 silo, this would have caught 6 invalid levers in call 1 and triggered a retry or continuation, producing substantive content. Applies to all models.
- **Effort**: Low-medium — add one `@model_validator` to `Lever`, raise `min_length` check to 30 chars.
- **Risk**: If the model consistently returns the name as the review (stuck at temperature=0), a retry loop will hit `max_calls` and fail gracefully (prior calls' levers are preserved). Low blast radius.

### 3. Fix examples 1 and 3 to eliminate shared "X, but Y" contrast pattern
- **Type**: prompt change
- **Evidence**: code_claude I2, insight N6, OPTIMIZE_INSTRUCTIONS lines 74–81. Both example 1 (agriculture) and example 3 (insurance) use the same adversarial-contrast sentence structure: "X [positive claim], but [hidden risk] [negates outcome]." OPTIMIZE_INSTRUCTIONS explicitly forbids shared sentence patterns. This shared structure is the most plausible cause of the "[Lever Name] lever overlooks/neglects/misses" lock that emerged in llama3.1 parasomnia call 3 (N6) and the persistent "The options miss" lock in call 1 (N5).
- **Impact**: Eliminates a structural cue that weaker models extract and reuse as a fill-in-the-blank template. Requires updating 1–2 of the three current `review_lever` examples so each uses a structurally distinct sentence form (e.g., list → consequence chain for example 1; conditional probability inversion for example 3). Affects all models.
- **Effort**: Low — edit prompt text only. The example content does not need to change, only the sentence structure.
- **Risk**: New structure could itself create a new lock. Risk is reduced by the OPTIMIZE_INSTRUCTIONS guidance already in place.

### 4. Add a 4th `review_lever` example in game-dev / software domain
- **Type**: prompt change
- **Evidence**: insight N3/H3/C3, code_claude review section. llama3.1 gta_game produced byte-for-byte identical output in runs 52, 66 (and implicitly all prior runs). Three examples now cover agriculture, medical, insurance — no coverage for game development or interactive entertainment. The domain gap is real and the fix is principled (matches the OPTIMIZE_INSTRUCTIONS "domain-specific mechanism" guidance). Insight Q4 raises whether temperature must also be increased; this example is a prerequisite for testing that hypothesis.
- **Impact**: If llama3.1 gta_game is not fully deterministic (or if temperature is increased), a game-dev example could break the 100% lock. Also benefits stronger models (haiku, GPT-4o-mini) that may use the example structurally. Does not solve the problem if temperature=0 makes gta_game truly immutable to prompt changes — that requires a follow-up code change.
- **Effort**: Low — add ~50 words to section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`. Draft: *"Engine middleware licensing for each first-party storefront requires an independent integration certification cycle — a sequential validation chain of 6–10 weeks per platform that cannot be parallelized, so adding a third storefront does not reduce the certification timeline for the first two."*
- **Risk**: A poorly drafted example can create a new lock in the same way the medical example created the "[Lever Name] lever overlooks" pattern. The example must name a specific domain mechanism (not a generic adversarial contrast) and avoid reusable transitional phrases.

### 5. Fix `partial_recovery` threshold and `expected_calls` in `runner.py`
- **Type**: code fix
- **Evidence**: code_claude B2/B3, insight E3/N4. `runner.py:517–523` emits `partial_recovery` whenever `calls_succeeded < 3`, regardless of whether the lever count target was actually met. A model producing 8+ levers per call legitimately completes in 2 calls with 16+ levers — a full success. The `expected_calls=3` literal in the event payload is stale (the PR description claimed to remove it from `_run_levers`, but it remains in `_run_plan_task` at line 523). Additionally, the `logger.warning` at `_run_levers:120–124` fires for every 2-call success.
- **Impact**: Cleaner `events.jsonl` — false-alarm `partial_recovery` events disappear for normally-completing 2-call runs. The `expected_calls` payload becomes semantically accurate. Analysis tooling that counts `partial_recovery` events as failures no longer penalizes healthy 2-call completions.
- **Effort**: Medium — `PlanResult` needs a `levers_count: int` field; `_run_levers` needs to pass `len(result.levers)` back; `_run_plan_task` gates the event on `levers_count < min_levers` instead of `calls_succeeded < 3`. The `logger.warning` should be demoted to `logger.info` or gated similarly.
- **Risk**: Low. The semantic change is clearly correct. Analysis tooling that currently depends on `partial_recovery` as a signal for degraded performance should be updated to treat 2-call, full-lever-count completions as ok.

---

## Recommendation

**Pursue Direction 1 first: add a `max_tokens` guard to `sllm.chat()` and a system-prompt length cap for `review_lever`.**

**Why first:** The haiku gta_game failure produces zero output — a complete plan failure, not a quality degradation. It is the only change in the dataset that moved `status` from `ok` to `error`. Every other regression (empty reviews, template lock, partial recoveries) still produces usable output. A plan with no output is worse than a plan with empty reviews or locked reviews.

The fix is also the lowest-effort change with the highest reliability impact: one parameter added to `sllm.chat()`, restoring haiku to 5/5 plans passing.

**What to change — file and lines:**

1. `identify_potential_levers.py`, the `execute_function` closure at lines 292–296:

```python
# Before:
chat_response = sllm.chat(messages_snapshot)

# After:
chat_response = sllm.chat(messages_snapshot, max_tokens=12000)
```

2. `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`, Section 6 (Prohibitions), `identify_potential_levers.py:235`:

Add one bullet after the existing prohibitions:
```
   - Keep each `review_lever` under 120 words. Concise, mechanism-focused reviews are preferred over exhaustive multi-paragraph chains.
```

3. `OPTIMIZE_INSTRUCTIONS`, after line 81, add a new bullet to the "Known problems" list:

```
- Verbosity amplification in strong models. Instruction-following models (e.g.
  Claude Haiku, GPT-4 family) mirror the length of review_lever examples in the
  system prompt. A 250-word example licenses 500-word reviews across all levers.
  For plans with 21+ raw levers x 3 calls, this multiplies total output size and
  causes JSON EOF errors. Keep every review_lever example under 80 words and add
  an explicit length cap to Section 6.
```

**Expected outcome:** Haiku gta_game restores to passing. Haiku parasomnia reviews drop from ~550 chars to ≤120-word (≈600-char) range — a soft cap that still allows detail. No regressions for other models (the parameter is a ceiling, not a floor).

---

## Deferred Items

**D1 — Model-level validator (review ≠ name)** [Direction 2]
High-value code fix but lower urgency than the hard failure. The empty-review regression (llama3.1 silo call-1) produces a plan that passes structural validation, which is less critical than a plan that fails entirely. Pursue immediately after Direction 1.

**D2 — Fix shared contrast structure in examples 1 and 3** [Direction 3]
The "[Lever Name] lever overlooks" lock in parasomnia call 3 is a new regression introduced by the PR. Fixing the example sentence structure addresses the root cause. Defer until after D1 (model validator) so regressions are independently observable.

**D3 — Add game-dev example** [Direction 4]
Necessary to close the gta_game domain gap. But must be validated against Q4 (is llama3.1 gta_game deterministic at temperature=0?). If deterministic, the example is needed but insufficient — a temperature increase must accompany it. Defer until temperature configuration is understood.

**D4 — Fix `partial_recovery` threshold and `expected_calls`** [Direction 5]
Correct cleanup but not urgent. The false alarms affect analysis quality, not plan quality. Defer to a cleanup PR alongside D1 or D2.

**D5 — Investigate llama3.1 temperature setting** [insight C4/Q4]
If llama3.1 runs at temperature=0, gta_game will be identically locked regardless of prompt changes. Confirm via `002-9-potential_levers_raw.json` metadata inspection or a test run with `temperature=0.7`. Block D3 on this finding.

**D6 — Verify whether llama3.1 silo empty-review regression is deterministic** [insight Q1]
A re-run at the same conditions will confirm whether call-1 empty reviews are reproducible. If stochastic, the model-validator fix (D1) is still correct (it turns a silent pass into a retry) but the urgency is lower.
