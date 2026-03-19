# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `self_improve/runner.py`

PR under review: #364 "feat: consolidate deduplicate_levers with classification and safety valve fix"

---

## Bugs Found

### B1 — `all_levers_summary` unconditionally appends `...` (missed half of B3 fix)

**File:** `deduplicate_levers.py:175`

```python
all_levers_summary = "\n".join(
    f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}..."
    for lever in input_levers
)
```

The `...` is appended unconditionally even when `lever.consequences` is ≤120 chars. PR #364 fixed the same pattern in `_build_compact_history` (line 99), where the fixed version reads:

```python
f"- [{d.lever_id}] {d.classification}: {d.justification[:80]}{'...' if len(d.justification) > 80 else ''}"
```

But the identical anti-pattern in `all_levers_summary` was left unpatched. The consequences field targets 2–4 sentences, so most entries will exceed 120 chars — but a short consequence (≤120 chars) will be presented to the LLM with a false `...` that signals truncation where none occurred. This causes models processing the lever summary to believe context was cut off, which can lead to unnecessary uncertainty in early classification decisions.

The PR description claims "Fix B3: `...` appended unconditionally in compact history" — but B3 only half-fixed the problem. The insight file marked it as "confirmed fixed" without examining `all_levers_summary`.

**Fix:** Change line 175 to:
```python
f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}{'...' if len(lever.consequences) > 120 else ''}"
```

---

### B2 — Spurious `partial_recovery` events for 2-call successes

**File:** `runner.py:125–128` and `runner.py:546–552`

In `_run_levers`:
```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

In `_run_plan_task`:
```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The inline comment on line 122 says "A 2-call success is normal for models that produce 8+ levers per call." But the threshold `< 3` fires on both 1-call and 2-call completions. A 2-call run that generated ≥15 levers is a full success — not a partial recovery. This produces false `partial_recovery` events in `events.jsonl` for models that are working correctly, polluting the analysis pipeline with misleading signals.

The threshold should be `< 2` (warn only if a single call succeeded and it produced fewer than 15 levers), or the event should include the actual lever count so analysis can distinguish success from failure:

```python
if actual_calls < 2:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

---

### B3 — Nested `ThreadPoolExecutor` in `_run_plan_task` defeats per-plan log filtering

**File:** `runner.py:514–527`

```python
thread_filter = _ThreadFilter(threading.current_thread().ident)  # line 514
file_handler.addFilter(thread_filter)
...
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, ...)  # runs in a NEW thread
```

`_ThreadFilter` captures the ident of the `_run_plan_task` thread (the outer pool thread). `run_single_plan` — which contains all LLM calls, all structured output parsing, and all file I/O — is submitted to a **new** inner `ThreadPoolExecutor`. This inner thread has a different ident, so its log records are filtered out by `_ThreadFilter`. Per-plan `log.txt` files capture only `_run_plan_task`'s own log entries (a handful of lines), missing all substantive diagnostic information from `run_single_plan`.

This bug existed before PR #364 but the PR added `deduplicate_levers` support which makes per-plan logging more valuable for diagnosing classification failures.

---

## Suspect Patterns

### S1 — Calibration hint upper bound creates capping risk on high-duplicate inputs

**File:** `deduplicate_levers.py:133`

```
In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed.
```

The insight file (N2, Q5) observes that gemini on `sovereign_identity` absorbed exactly 5 levers (the lower bound of "4–8") and then kept 9 — while the correct answer (and consensus from 6 other models) was 5 kept / 10 absorbed. The calibration hint appears to act as a stopping signal: once a model reaches the lower end of the stated range, it may treat the range as a target band rather than a minimum floor and stop absorbing.

This is an expected LLM behavior: quantitative ranges in prompts are often interpreted as targets. For structured duplicate inputs (sovereign_identity has paired levers with near-identical names), 10 absorbs is the correct answer — outside the "4–8" range. The hint is empirically wrong for this class of plan.

Not labelled as a confirmed bug because the behavior is stochastic and only observed for one model on one plan, but the expected range should be widened to avoid capping.

### S2 — `options` field description contradicts validator enforcement

**File:** `identify_potential_levers.py:121–124` (field description) and `147–158` (validator)

The field description says "Exactly 3 options for this lever. No more, no fewer." but the validator only rejects `len(v) < 3`. Values of 4, 5, or more pass silently. This contradiction sends mixed signals: the LLM reads "no more than 3" but the code enforces "at least 3." In practice the downstream comment says "Over-generation (>3) is tolerable" — which is the correct policy — but the field description is actively wrong and will cause some models to interpret the schema as requiring exactly 3, while others generate 4+ without issue.

### S3 — `LeverCleaned.consequences` carries full Pydantic field description intended for LLMs

**File:** `identify_potential_levers.py:209–216`

`LeverCleaned` is documented as "never sent to an LLM." But its `consequences` field carries the full LLM-facing description including the prohibition "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field." These descriptions have no effect on LLM output when applied to `LeverCleaned`, but they do mislead code readers into thinking `LeverCleaned` is validated or used in a structured LLM call. The description should be plain documentation, not a Pydantic field description. (Low severity — no runtime impact.)

---

## Improvement Opportunities

### I1 — Widen calibration hint to 4–10 to prevent capping on high-duplicate plans

**File:** `deduplicate_levers.py:133`

Change:
```
In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed.
```
to:
```
In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed. Plans with
many near-duplicate names may require 10 or more absorbs — do not stop early.
```

Evidence: gemini correctly absorbed 10 levers (before PR) but only absorbed 5 after the "4–8" hint was added. Other models on `sovereign_identity` (llama3.1, gpt-5-nano, gpt-4o-mini, gpt-oss-20b, haiku) all kept 5 after PR, consistent with 10 true absorbs. The upper bound of 8 was empirically wrong for this plan.

### I2 — Add post-deduplication zero-reduction runtime warning

**File:** `deduplicate_levers.py`, after line 296 (before `return cls(...)`)

The blanket-keep failure mode (llama3.1 keeping 14–15/15) was caught only by the analysis pipeline, not at runtime. A simple check would surface it immediately:

```python
if len(output_levers) > 0 and len(output_levers) / len(input_levers) > 0.9:
    logger.warning(
        f"Deduplication yielded {len(output_levers)}/{len(input_levers)} levers "
        f"({len(output_levers)/len(input_levers)*100:.0f}%) — possible blanket-keep"
    )
```

This would have flagged llama3.1's pre-PR 14/15 and 15/15 cases in the run log without waiting for analysis.

### I3 — Add anti-boilerplate absorb instruction targeting gpt-4o-mini's "distinct and essential" pattern

**File:** `deduplicate_levers.py:DEDUPLICATE_SYSTEM_PROMPT`

The insight (N1, C2) shows gpt-4o-mini's justifications uniformly contain "is a distinct and essential strategic decision" for nearly every lever, indicating it evaluates each lever in isolation rather than comparing levers to each other. The system prompt instructs to "Explain why the lever is distinct from others" but gpt-4o-mini's behavior suggests it isn't doing comparative analysis.

Adding a worked comparison example for the absorb case (not just defining the classification) would help break this pattern. The current prompt defines `absorb` but provides no demonstration of absorb reasoning.

### I4 — `review_lever` validator minimum (10 chars) is far below the system-prompt target (20–40 words)

**File:** `identify_potential_levers.py:162–177`

The system prompt (line 264) says "Keep each `review_lever` to one sentence (20–40 words)" and the examples are 40–65 words. But the validator accepts anything ≥10 characters. A 10-character `review_lever` (e.g., "Trade-off.") passes validation but violates the intent. There is no upper bound validator either.

The validator should enforce a higher minimum — at least 50 characters to catch blank/stub responses — while remaining language-agnostic (character count, not word count, to support non-English outputs per OPTIMIZE_INSTRUCTIONS):

```python
if len(v) < 50:
    raise ValueError(f"review_lever is too short ({len(v)} chars); expected at least 50")
```

### I5 — OPTIMIZE_INSTRUCTIONS in `deduplicate_levers.py` does not document the calibration capping risk

**File:** `deduplicate_levers.py:26–48`

The `OPTIMIZE_INSTRUCTIONS` block correctly documents blanket-primary, over-inclusion, hierarchy-direction errors, and chain absorption. After iteration 42 analysis, the insight identifies a fifth failure mode: **calibration capping** — where models treat the upper bound of the "expect 4–8" range as a stopping signal on high-duplicate inputs. This should be added:

```
- Calibration capping. When the calibration hint gives a range (e.g. "expect 4–8"),
  some models stop absorbing once they reach the upper bound even when more true
  duplicates remain. Symptom: exactly N absorbs where N is the hint's upper bound.
  Mitigation: widen range upper bound, or add "do not stop early" language.
```

---

## Trace to Insight Findings

| Insight finding | Code location | Root cause |
|-----------------|---------------|------------|
| N1 — gpt-4o-mini over-inclusion unchanged | `deduplicate_levers.py:127` (absorb definition) | No worked absorb example; model evaluates levers in isolation; "distinct and essential" boilerplate shows lack of comparative reasoning |
| N2 — gemini sovereign_identity regression (5→9 kept) | `deduplicate_levers.py:133` calibration hint "4–8" | Upper bound 8 is a stopping signal; 10 true absorbs exceed the range, causing premature stop (S1 / I1) |
| N4 — fabricated percentages flow through verbatim | `deduplicate_levers.py:160–170` (InputLever construction) | Consequences fields passed verbatim; no numeric validation at either step |
| P3 — B3 partially confirmed fixed | `deduplicate_levers.py:99` fixed; `deduplicate_levers.py:175` missed | PR fixed `_build_compact_history` but left `all_levers_summary` with identical anti-pattern (B1) |
| B2 (prior synthesis) — spurious partial_recovery events | `runner.py:125,546` | Threshold `< 3` fires on normal 2-call completions (B2) |
| Per-plan log files missing substantive content | `runner.py:514–527` | `_ThreadFilter` captures outer thread; inner `ThreadPoolExecutor` thread logs are filtered out (B3) |

---

## PR Review

### What the PR claims to fix

1. Narrow safety valve → fix llama3.1 blanket-keep
2. Fix gpt-4o-mini over-inclusion
3. Add calibration hint ("expect 4–8 absorb/remove in 15 levers")
4. Add concrete secondary lever examples
5. Fix B3: `...` appended unconditionally in compact history
6. Add `OPTIMIZE_INSTRUCTIONS` with 4 failure modes
7. Add `deduplicate_levers` to runner

### Assessment

**Item 1 (llama3.1 blanket-keep): FIXED.** Changing "Use primary if you lack understanding" to "Use primary only as a last resort" with the calibration hint produced the measured result: llama3.1 average kept dropped from 10.6 to 7.0. The code change is correct.

**Item 2 (gpt-4o-mini over-inclusion): NOT FIXED.** The insight data shows 9.4→9.6 — essentially no change. The calibration hint alone is insufficient. The PR description claimed this would be fixed; the implementation does not deliver it. gpt-4o-mini needs a worked absorb example or explicit anti-pattern instruction, not just a quantitative range.

**Item 3 (calibration hint "4–8"): PARTIALLY CORRECT.** The hint fixed llama3.1 but introduced a regression on gemini for plans with more than 8 true duplicates. The upper bound 8 is incorrect for the `sovereign_identity` plan (10 true absorbs). See S1 and I1.

**Item 4 (secondary examples): WORKS.** The concrete examples (marketing timing, reporting cadence, etc.) appear in the system prompt correctly. Models use them with partial success (P4 in insight).

**Item 5 (B3 fix): HALF DONE.** `_build_compact_history` at line 99 is correctly fixed. But `all_levers_summary` at line 175 still uses the same unconditional `...` pattern. This is B1 above — a missed fix that the insight analysis incorrectly marked as fully resolved.

**Item 6 (OPTIMIZE_INSTRUCTIONS): COMPLETE.** The OPTIMIZE_INSTRUCTIONS block in `deduplicate_levers.py` is present with 4 failure modes documented. However, after iteration 42's analysis reveals a 5th failure mode (calibration capping, see I5), it should be updated.

**Item 7 (runner integration): COMPLETE.** `_run_deduplicate` and the `DEDUPLICATE_INPUT_FILES` / `_DEDUPLICATE_LEVERS_FILE` constants are correctly wired in. The `calls_succeeded=len(result.response)` in `_run_deduplicate` returns the decision count (one per input lever, typically 15), not the LLM call count — but since the `partial_recovery` event check is gated on `step == "identify_potential_levers"`, this semantic mismatch doesn't cause false events.

### Edge cases and gaps in the PR

**Gap 1:** The `all_levers_summary` unconditional `...` (B1) — the most direct miss from the B3 fix.

**Gap 2:** The `partial_recovery` threshold (`< 3` in both `_run_levers` and `_run_plan_task`) pre-dates the PR and emits false events for 2-call completions that are documented as normal. The PR added `deduplicate_levers` to the runner without auditing this adjacent logic.

**Gap 3:** No worked absorb example. The insight and OPTIMIZE_INSTRUCTIONS both name over-inclusion as a failure mode. The PR addresses it only with a quantitative hint, which is insufficient for gpt-4o-mini (the model that was explicitly targeted). A single absorb example in the system prompt (showing a reasoning trace: "lever A's name and consequences substantially overlap lever B — absorb A into B") would be a lower-risk intervention than a wider calibration range.

---

## Summary

**Confirmed bugs:**

- **B1** (`deduplicate_levers.py:175`): `all_levers_summary` still appends `...` unconditionally — the same pattern that was fixed in `_build_compact_history` by the PR. The PR's B3 fix is incomplete.
- **B2** (`runner.py:125,546`): `partial_recovery` events fire for normal 2-call completions because the threshold `< 3` is one too high. Creates misleading noise in `events.jsonl`.
- **B3** (`runner.py:514–527`): Nested `ThreadPoolExecutor` in `_run_plan_task` means per-plan `log.txt` files capture only outer-thread logs; all LLM-interaction logs from `run_single_plan` are filtered out by the `_ThreadFilter`.

**Most impactful improvement opportunities:**

- **I1**: Widen calibration hint from "4–8" to "4–10" to prevent gemini-style capping on high-duplicate plans (directly explains N2 regression).
- **I2**: Add post-deduplication zero-reduction warning to surface blanket-keep at runtime.
- **I3**: Add worked absorb comparison example to address gpt-4o-mini's isolationist evaluation pattern (the only remaining over-inclusion target).

**PR verdict:** The PR's primary target (llama3.1 blanket-keep) is fixed. The secondary target (gpt-4o-mini over-inclusion) is not fixed. The B3 fix is half-complete. One new regression was introduced (gemini sovereign_identity: 5→9 kept) from an over-constrained calibration range. The code quality additions (OPTIMIZE_INSTRUCTIONS, runner integration) are solid. Net result: merge is acceptable given the llama3.1 win, but the calibration hint range (I1) and the missed `all_levers_summary` fix (B1) should be addressed in the next iteration.
