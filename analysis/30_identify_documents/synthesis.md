# Synthesis

## Cross-Agent Agreement

Both agents (insight and code review) agree on the following:

- **PR #342 verdict: CONDITIONAL.** The hard `max_length` caps provide a safety net for
  well-behaved models (llama3.1, gemini, gpt-5-nano) but directly cause new
  `too_long` Pydantic failures for haiku (12 items rejected) and gpt-4o-mini (7 items
  rejected). This violates the AGENTS.md principle established during `identify_potential_levers`.
- **Truncation root cause is per-item verbosity, not item count.** Haiku generates
  ~700-char descriptions; capping at 6 items still produces ~40 KB responses that hit
  EOF. The PR attacked the wrong dimension.
- **Deduplication is missing** in `identify_documents.cleanup()` — the `seen_names`
  guard present in `identify_potential_levers.py` was never ported over, directly
  causing N5 (llama3.1 "Hong Kong Labour Laws and Regulations" duplicate).
- **B1 (`OPTIMIZE_INSTRUCTIONS` never injected) is the highest-priority fix.** The
  120-char string limit and 3-step-per-document limit are already written in
  `identify_documents.py` but the constant is dead code — it is never appended to
  the system prompt sent to the LLM.
- **Overall success rate: 80% plan-level, 0% full pipeline (per metrics in insight).**
  The `expected_calls: 3` / `calls_succeeded: 1` pattern is consistent across all
  35 runs.

---

## Cross-Agent Disagreements

### Disagreement 1 — Whether "filter calls always fail" is a real pipeline failure

**Insight (N3/C1)** concluded that 2 of 3 pipeline calls always fail, that
`017-7-filter_documents_to_find_raw.json` and `017-9-filter_documents_to_create_raw.json`
never appear, and that the `identify_documents` step runs at 33% capacity. It ranked
investigating this as the highest-priority code fix (C1).

**Code review (B2)** shows this is a false monitoring alarm. `_run_documents()` in
`runner.py:155` hardcodes `calls_succeeded=1`, which is **correct** — `identify_documents`
is a single-call step by design. The `partial_recovery` event fires on every single run
because `_run_plan_task()` at line 514 unconditionally checks `calls_succeeded < 3`
using the constant `3` that was written for `identify_potential_levers` (which makes
3 calls) and was never made step-specific. There are no "filter calls 2 and 3" to
fail — they don't exist in the `identify_documents` design.

**Verdict: code review is correct.** Confirmed by reading `runner.py:129–156`:
`_run_documents()` calls `IdentifyDocuments.execute()` once (a single structured LLM
call), saves 4 output files, and returns `calls_succeeded=1`. The `017-7-*` and
`017-9-*` files referenced by insight are from a different (older) pipeline layout
visible in `baseline/` but are not produced by the current runner. The "0% full
pipeline success" metric in insight is a false reading of a monitoring bug, not an
actual pipeline failure. This invalidates insight's top recommendation (C1).

### Disagreement 2 — Priority ordering

**Insight** ranked investigating the filter step failures (C1) before fixing
`OPTIMIZE_INSTRUCTIONS` injection (C2/C3). **Code review** ranked B1 first.

Since C1 is a false lead (see above), code review's priority ordering is correct.
B1 (inject OPTIMIZE_INSTRUCTIONS) is the highest-priority change.

---

## Top 5 Directions

### 1. Inject `OPTIMIZE_INSTRUCTIONS` into the system prompt in `identify_documents.py`
- **Type**: code fix
- **Evidence**: B1 (code review, confirmed by source); traces to N2, N4 (insight);
  both agents ranked this as primary root cause of truncation failures.
- **Impact**: The 120-char string-field limit and 3-step-per-document limit are already
  written in `OPTIMIZE_INSTRUCTIONS` at `identify_documents.py:257–264` but never
  appended to `system_prompt` before the LLM call (line ~320). Fixing this delivers
  the verbosity constraint to every model on every call. Haiku's ~700-char descriptions
  (cause of ~40 KB responses and EOF truncations) would be constrained to ≤120 chars,
  reducing per-call response size by ~80% for haiku. Estimated effect: eliminates 3
  of haiku's 4 truncation failures; reduces gpt-4o-mini description bloat; benefits
  all 7 models. Also resolves the S1 contradiction (OPTIMIZE_INSTRUCTIONS says "≤6
  total across both passes" — before injecting it, update that number to ≤9 to match
  the schema, or decide on a single number).
- **Effort**: low — one-line append in `execute()`, plus a one-line prose fix in
  `OPTIMIZE_INSTRUCTIONS` itself to resolve S1.
- **Risk**: low. The constraint is soft prompt guidance, not a hard schema cap, so it
  won't reject responses — it guides the model toward shorter output. Models that
  already produce short descriptions (llama3.1 at ~90 chars) are unaffected.

### 2. Fix false `partial_recovery` events in `runner.py`
- **Type**: code fix
- **Evidence**: B2 (code review); explains the misleading N3 (insight). Confirmed by
  `runner.py:155` (`calls_succeeded=1` hardcoded) and `:514–518` (`expected_calls=3`
  hardcoded for all steps).
- **Impact**: The `partial_recovery` event fires 35/35 times as a false positive,
  making post-hoc analysis impossible — any future analyst will again mistake this for
  a real pipeline failure. The fix is to return `calls_succeeded=None` from
  `_run_documents()` (line 155); the guard at line 514 already skips when
  `calls_succeeded is None`. Alternatively, pass the expected call count through
  `PlanResult` rather than hardcoding `3`. This is a monitoring correctness fix that
  prevents the same misdiagnosis from occurring in future iterations.
- **Effort**: low — change one value on one line.
- **Risk**: near-zero. The `None` branch already exists in the conditional.

### 3. Raise or remove `max_length` constraints added by PR #342
- **Type**: code fix (PR regression)
- **Evidence**: N1 (insight) directly observed 2 failures caused by the caps;
  code review PR section confirmed the "hard cap rejects rather than trims" mechanism.
  Both agents: CONDITIONAL verdict on the PR.
- **Impact**: Directly eliminates the 2 `too_long` validation failures for haiku
  (sovereign_identity) and gpt-4o-mini (gta_game). Once direction 1 (OPTIMIZE_INSTRUCTIONS
  injection) constrains verbosity, the need for hard caps drops further. The caps
  should be raised to 12–15 to act as a last-resort safety net rather than a tight
  constraint, OR replaced with soft prompt guidance ("Identify 4–8 documents per
  category"). A single `max_length=9` field would be cleaner than the current
  part1/part2 split.
- **Effort**: low — change 4 integer values in the Pydantic schema.
- **Risk**: low if raised to 12–15. Risk of re-introducing truncation is mitigated by
  direction 1 constraining per-item verbosity first.

### 4. Add `document_name` deduplication in `cleanup()` in `identify_documents.py`
- **Type**: code fix
- **Evidence**: B3 (code review); N5 (insight — confirmed llama3.1 "Hong Kong Labour
  Laws" duplicate in `017-5-identified_documents_to_find.json`). The identical guard
  exists in `identify_potential_levers.py:331–337` and was simply not ported.
- **Impact**: Eliminates the N5 duplicate and prevents future cross-part1/part2
  duplicates (the `_part2` field description says "Do not repeat" but this is only
  prompt guidance — not enforced in code). Affects all models when the model reproduces
  a name across the two passes. Cheap to add and zero-regression risk.
- **Effort**: low — 5–7 lines mirroring the `seen_names` pattern already in the codebase.
- **Risk**: none. Deduplication is strictly additive and matches existing behavior in
  the sister step.

### 5. Add per-item description length guidance to the system prompt
- **Type**: prompt change
- **Evidence**: H1 (insight); N7 (insight — llama3.1 ~90 chars vs baseline ~250 chars);
  N4 (insight — haiku ~700 chars). Both agents flagged the description length
  distribution as the key variable differentiating models.
- **Impact**: Complementary to direction 1 (code fix for OPTIMIZE_INSTRUCTIONS
  injection). Adding "Each document description: 2–4 sentences, 50–200 words" to the
  system prompt helps llama3.1 produce richer descriptions (currently 0.36× baseline)
  and reinforces the cap for haiku. Affects content quality for all 35 plan-runs.
  The table in insight shows gemini-2.0-flash at 1.0× baseline is the quality target.
- **Effort**: low — one sentence added to the system prompt.
- **Risk**: low. A qualitative length target ("2–4 sentences") is non-binding guidance
  that weaker models may partially follow; it can't cause validation failures.

---

## Recommendation

**Do direction 1 first: inject `OPTIMIZE_INSTRUCTIONS` into the system prompt in
`identify_documents.py`.**

**Why first:** It is the confirmed root cause of the majority of failures. Three of
haiku's 4 failures (the EOF truncations at ~40 KB) stem directly from verbosity
constraints that were written but never delivered. The fix requires one append:

```python
# In identify_documents.py, inside execute(), around line 320
system_prompt = system_prompt.strip() + "\n\n" + OPTIMIZE_INSTRUCTIONS.strip()
```

Before doing this, also fix the S1 contradiction in the constant itself: the line
`documents_to_create: maximum 6 items total across both passes` should be updated to
`documents_to_create: maximum 9 items total across both passes (part1 + part2)` to
match the schema. Or better, decide on a single total (e.g., 8) and align both the
constant and the schema.

**What changes:**
1. `worker_plan/worker_plan_internal/document/identify_documents.py`, around line 320
   in `execute()`: append `OPTIMIZE_INSTRUCTIONS` to `system_prompt` before building
   `chat_message_list`.
2. Same file, `OPTIMIZE_INSTRUCTIONS` constant at line ~263: update "maximum 6 items
   total" to "maximum 9 items total" (or a consistent chosen number).

**Expected effect:** Haiku's ~700-char descriptions become ≤120 chars per field,
shrinking 40 KB responses to approximately 5–8 KB — well below any truncation
threshold. This converts haiku from a 1/5 success rate (catastrophic) to an estimated
4–5/5. For all models, the 3-step-per-document limit prevents step-list bloat (S2),
which is currently the second-largest driver of response size with no ceiling at all.

After this fix is confirmed in a test run, direction 3 (raising the max_length caps)
becomes lower-risk because the verbosity root cause will have been addressed.

---

## Deferred Items

**Direction 2 (fix false `partial_recovery` events)**: Do second. It's a one-liner
with zero risk and eliminates a persistent source of false analysis. Should be paired
with direction 1 in the same PR to avoid a future analyst re-discovering the same
false alarm.

**Direction 3 (raise max_length caps)**: Do after direction 1 is validated. The new
verbosity constraint changes the risk profile — once items are short, a cap of 12 is
a genuine safety net and not a tight constraint.

**Direction 4 (deduplication in cleanup())**: Do in the same commit as direction 2.
It's a 5-line copy from `identify_potential_levers.py`, zero-risk, and closes a known
duplicate-output bug (N5).

**Direction 5 (prompt description length guidance)**: Lowest priority of the five.
It's reinforcing guidance that overlaps with what direction 1 already achieves via the
`All string fields: maximum 120 characters` constraint. Worth adding in a follow-up
prompt iteration if gemini/gpt-5-nano still show description length variance after
directions 1–4 are in place.

**S2 (`steps_to_create`/`steps_to_find` lack max_length)**: Not in top 5 because
direction 1's soft constraint covers it, but worth adding `max_length=3` to the
Pydantic schema as a structural guard in the same PR as direction 3.

**S3 (no `min_length` on DocumentDetails list fields)**: Low urgency — add
`min_length=1` to `documents_to_create` and `documents_to_find` as a silent-failure
guard in the same schema PR.

**N6 (document count gap vs baseline: 9 max vs 17 in baseline)**: The 17-item
baseline was produced by a different pipeline version with more downstream steps.
The appropriate cap level for the current single-call design needs a separate
calibration run, not a max_length increase alone.

**OPTIMIZE_INSTRUCTIONS for identify_potential_levers.py**: The constant in this file
serves as self-improvement guidance (not runtime-injected), which is by design.
No change needed there. However, the pattern of "runtime verbosity instructions
stored in OPTIMIZE_INSTRUCTIONS but not injected" is now confirmed as a recurring
risk; a comment in the constant header noting whether it is runtime-injected or
self-improve guidance only would prevent future B1-class bugs.
