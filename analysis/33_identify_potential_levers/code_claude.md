# Code Review (claude)

## Bugs Found

**B1 — `check_review_format` docstring says ≥50 chars, code checks <10**
`identify_potential_levers.py:154` — docstring says "minimum length (at least 50 characters)" but the implementation at line 157 checks `if len(v) < 10`. The PR lowered the threshold from 50 to 10 but left the docstring untouched. Any developer reading the docstring will have incorrect expectations.

**B2 — First-call failure exits immediately: adaptive retry provides zero recovery on call 1**
`identify_potential_levers.py:338–339`:
```python
if len(responses) == 0:
    raise llm_error from e
```
When `call_index == 1` raises an exception (e.g., Pydantic validation failure because `lever_classification` is missing), `len(responses) == 0` is always true → the error is re-raised immediately. The loop never reaches `call_index == 2`. The comment at lines 333–337 correctly explains the intent — protect prior-call levers from being discarded — but it only applies from call 2 onward. A model that consistently fails on its first batch (qwen3 omitting `lever_classification`) gets no retry at all. The old fixed-3-call loop would have called the LLM three times regardless; the new adaptive loop calls it zero additional times after first-call failure.

**B3 — `expected_calls = 3` hardcoded in `_run_levers` is stale after adaptive retry**
`runner.py:115`:
```python
expected_calls = 3
actual_calls = len(result.responses)
if actual_calls < expected_calls:
    logger.warning(...)
```
The adaptive retry can now complete in 1 call (if ≥15 levers generated) or go up to 5 calls. Logging a warning for plans that succeed in 1 call ("partial recovery — 1/3 calls succeeded") is misleading and will trigger spurious alerts. The constant `3` is a relic of the old fixed-loop design.

**B4 — `partial_recovery` event hardcodes `expected_calls=3` in runner.py**
`runner.py:514–518`:
```python
if pr.calls_succeeded is not None and pr.calls_succeeded < 3:
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```
Same staleness issue as B3. A plan that legitimately completes in 1 call (e.g., a model generates 20 levers on the first call) will emit a `partial_recovery` event claiming it fell short. This pollutes `events.jsonl` with false-positive recovery events, making downstream analysis (like the assessment pipeline) misclassify successful fast runs as degraded runs.

---

## Suspect Patterns

**S1 — All three `lever_classification` system prompt examples are generic and reusable**
`identify_potential_levers.py:229–230`:
```
"governance — who oversees the review process"
"methodology — which data collection approach to use"
"execution — how to sequence the rollout phases"
```
Every one of these phrases can be trivially applied to any lever in any domain. `OPTIMIZE_INSTRUCTIONS` (lines 69–79) explicitly documents the template-lock risk: "Examples must avoid reusable transitional phrases that fit any domain." The `lever_classification` examples violate this guidance exactly. The evidence is immediate: llama3.1 copies "how to sequence the rollout phases" four times across unrelated levers in hong_kong_game. This is structurally identical to the `review_lever` template-lock described in OPTIMIZE_INSTRUCTIONS but was introduced by this very PR.

The single example in the `Lever.lever_classification` field description (`identify_potential_levers.py:115`) is also the most template-lockable one: `"governance — who oversees the review process"` — a phrase portable to any lever in any governance-adjacent plan.

**S2 — `min_length=5` on levers combined with required `lever_classification` creates a double trap**
`identify_potential_levers.py:179–182`:
```python
levers: list[Lever] = Field(
    min_length=5,
    description="Propose 5 to 7 levers."
)
```
If a model generates 6 levers but omits `lever_classification` on any one, the entire `DocumentDetails` fails. If the same model generates only 4 levers (possible for weaker models on complex plans), it also fails. These two constraints compound: a model that produces 4 levers where 3 are valid and 1 is missing `lever_classification` fails twice over. There is no partial acceptance of valid levers from a batch. OPTIMIZE_INSTRUCTIONS (line 43) says "Over-generation is fine; step 2 handles extras" — but the inverse is not handled: partial batches with some invalid levers are discarded entirely.

**S3 — Case-sensitive exact-match deduplication may pass same-name levers with different casing**
`identify_potential_levers.py:360–365`:
```python
seen_names: set[str] = set()
...
if lever.name in seen_names:
```
If call 1 generates "Budget Management" and call 2 generates "budget management", both pass the deduplication check. The downstream `DeduplicateLeversTask` handles near-duplicates, but exact case-variant duplicates arriving in the same file may confuse it or add noise.

**S4 — Chat history not carried across multi-call loop: each call is stateless**
`identify_potential_levers.py:305–311`:
```python
call_messages = [
    system_message,
    ChatMessage(role=MessageRole.USER, content=prompt_content),
]
```
Each call builds a fresh two-message conversation (system + user). Prior assistant responses are not included. Call 2 only knows which lever *names* to avoid (via the names list in `prompt_content`), but cannot see the actual content of previously generated levers. This means the LLM on call 2 cannot generate complementary levers that build on what call 1 produced. MEMORY.md ("Next: iteration 2, fix assistant turn serialization") flags this as a known issue.

---

## Improvement Opportunities

**I1 — Make `lever_classification` `Optional[str] = None` to prevent hard failures during rollout**
The direct fix for qwen3's 3/5 regression. Changing from:
```python
lever_classification: str = Field(...)
```
to:
```python
lever_classification: Optional[str] = Field(default=None, ...)
```
allows qwen3's otherwise-valid lever batches to pass validation. A post-hoc check can count how many levers are missing the field and either warn or trigger a follow-up call. Once all target models reliably generate the field, it can be made required again.

**I2 — Allow retry on first-call schema validation failure**
Modify the error handling at `identify_potential_levers.py:338` to allow at least one retry when the failure is a Pydantic validation error (not a network/auth error):
```python
if len(responses) == 0:
    # Pydantic validation failures on call 1 may be recoverable on retry
    # (e.g., model omitted a required field but can generate it if asked again).
    # Only raise immediately for non-retryable errors (auth, stop requested, etc.)
    raise llm_error from e
```
The logic could distinguish `ValidationError` from `LLMChatError` caused by auth/rate-limit errors. Retrying on validation failures lets qwen3 have a second chance without requiring `lever_classification` to be made Optional.

**I3 — Replace generic lever_classification examples with non-portable domain-specific phrases**
In `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` Section 2 (`identify_potential_levers.py:229`), replace:
```
"governance — who oversees the review process"
"methodology — which data collection approach to use"
"execution — how to sequence the rollout phases"
```
with domain-anchored examples across different domains, none of which can be plausibly reused in another domain:
```
"execution — which city blocks to sequence first when relaying the water main"
"governance — which of the four county agencies has authority to sign the discharge permit"
"methodology — whether to run paired-sample or repeated-measures ANOVA for the sleep-disruption dataset"
```
This matches the "agriculture example" pattern praised in OPTIMIZE_INSTRUCTIONS lines 76–79.

**I4 — Remove or fix hardcoded `expected_calls` in runner.py**
`runner.py:115` and `runner.py:518`: remove the `expected_calls=3` constant or derive it from the actual `max_calls` value. A clean approach: remove the `partial_recovery` event trigger entirely, since the adaptive retry already means "fewer than N calls" is not an anomaly — it's the happy path for models that reach 15 levers quickly.

**I5 — Document first-call-failure retry gap in OPTIMIZE_INSTRUCTIONS**
Add a new entry to `OPTIMIZE_INSTRUCTIONS` (lines 46–80) covering:
> New-required-field failure. When a required field is added to `Lever`, models that omit it will cause the entire first-call batch to fail validation. The adaptive retry exits immediately on first-call failure (`len(responses) == 0` → raise). The retry only protects levers from *prior* successful calls; it provides zero recovery when the first call fails. Make new fields `Optional` during rollout; promote to required only after verifying all target models generate the field reliably.

This parallels the existing Pydantic hard-constraints note and the template-lock entries.

---

## Trace to Insight Findings

| Insight Finding | Code Location | Explanation |
|---|---|---|
| qwen3 3/5 regression — lever_classification missing, immediate raise | `identify_potential_levers.py:338–339` (B2) | `len(responses) == 0` on first-call failure → raises, loop never retries |
| llama3.1/silo failure — options < 3 | `identify_potential_levers.py:142–143` + required `lever_classification` field | Adding a required field increases output complexity; llama3.1 cuts corners on options to fit |
| lever_classification template lock (llama3.1 copies examples) | `identify_potential_levers.py:229–230` (S1) | All three system prompt examples use portable generic phrases that any lever can copy verbatim |
| review_lever docstring/code mismatch (says 50, checks 10) | `identify_potential_levers.py:154,157` (B1) | PR changed threshold but left docstring stale |
| Spurious `partial_recovery` events in outputs.jsonl for 1-call successes | `runner.py:115,518` (B3, B4) | `expected_calls=3` hardcoded from pre-PR fixed loop, now misleading for adaptive retry |
| Net success regression 97.1% → 88.6% | B2 + `lever_classification: str` required | qwen3's 3 failures and llama3.1's 1 failure all trace to required field + no first-call retry |
| Adaptive retry benefit for llama3.1 on sovereign_identity/hong_kong | `identify_potential_levers.py:350–352` | Works correctly for calls 2–5; the loop exits early at 15 levers (positive finding, not a bug) |

---

## PR Review

### Change 1: `lever_classification` required field

**Intent:** Add a categorization field; place it last in schema so sequential generators (llama3.1) fill more important fields first.

**Implementation gap:** Making the field `str` (required) rather than `Optional[str]` is the root cause of the 3/5 qwen3 regression. The field placement at the end of the schema helps llama3.1 (sequential JSON) but does nothing for models that skip unknown fields entirely (qwen3). The system prompt Section 2 examples are all generic portable phrases, creating the same template-lock vector that OPTIMIZE_INSTRUCTIONS already documents and warns against for `review_lever`. The PR introduced the exact failure pattern it was designed to avoid.

**B1 (docstring stale):** The `check_review_format` docstring was not updated when the threshold changed from 50 to 10.

### Change 2: haiku max_tokens fix (16000 → 8192)

**Correct.** The API cap is 8192; the old value was above-cap. No observable regression in test data (no truncation before or after), but the fix prevents potential failures on larger plans not in the test set.

### Change 3: `review_lever` minimum relaxed (50 → 10)

**Valid change.** The old minimum of 50 chars was rejecting legitimate short reviews. The fix is low-risk. The only issue is that the docstring was not updated (B1).

### Change 4: Adaptive retry loop (fixed 3 calls → adaptive up to 5)

**Partially correct.** The retry logic works as intended for calls 2–5: if call 1 succeeds but yields <15 levers, call 2 is triggered. The improvement for llama3.1 on sovereign_identity (+6 levers) and hong_kong (+3 levers) is real and correctly implemented.

**Design gap (B2):** The loop raises immediately on first-call failure (`len(responses) == 0`). This means: models that fail on call 1 (qwen3's 3/5 failures) get FEWER retries under the new adaptive loop than they would have under the old fixed-3-call loop. The old loop would attempt all 3 calls regardless; the new loop attempts 1 then quits. The PR's comment at lines 333–337 correctly describes the intent but the guard condition doesn't cover the case the PR actually needed to fix.

**B3/B4 (stale `expected_calls=3`):** The `runner.py` constants `expected_calls=3` and the `< 3` guard for `partial_recovery` events were not updated to match the new adaptive retry design. Plans completing in 1 call now emit false-positive `partial_recovery` events.

### Overall PR verdict

The adaptive retry, haiku max_tokens fix, and review_lever threshold change are correct and worth keeping. The `lever_classification` implementation has two concrete defects: (a) the field is required rather than Optional, causing qwen3 regressions with no retry fallback; (b) the system prompt examples are all generic, guaranteeing llama3.1 template lock. The runner.py hardcoded `expected_calls=3` is a stale artifact of the pre-PR design.

---

## Summary

**Confirmed bugs (4):**
- **B1** (`identify_potential_levers.py:154`): `check_review_format` docstring says 50-char minimum; code checks 10. Documentation misleads developers.
- **B2** (`identify_potential_levers.py:338`): First-call failure → immediate raise. The adaptive retry loop never retries when call 1 fails schema validation. qwen3's 3/5 regression has no recovery path.
- **B3** (`runner.py:115`): `expected_calls = 3` is stale; emits spurious warnings for 1-call successes.
- **B4** (`runner.py:514–518`): `partial_recovery` event hardcodes `expected_calls=3`; fires for successful fast plans.

**Key suspect patterns (2):**
- **S1** (`identify_potential_levers.py:229`): All three `lever_classification` system prompt examples are generic portable phrases — guaranteed template-lock vectors for llama3.1 and other weak models.
- **S2** (`identify_potential_levers.py:142,179`): Hard Pydantic constraints on both the options list (≥3) and the levers list (≥5) combined with required `lever_classification` mean a single non-compliant field in a single lever discards the entire call batch with no partial-acceptance fallback.

**Highest-priority fixes:**
1. Make `lever_classification: Optional[str] = None` or add retry-on-first-call-failure to recover qwen3.
2. Replace generic Section 2 examples with non-portable domain-anchored phrases.
3. Fix `check_review_format` docstring (trivial but misleading).
4. Remove/update hardcoded `expected_calls=3` in runner.py.
