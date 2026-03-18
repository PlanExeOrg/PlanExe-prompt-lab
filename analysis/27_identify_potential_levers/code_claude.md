# Code Review (claude)

## Bugs Found

### B1 — Lockable phrase "the options neglect" persists in third example (dual location)

`identify_potential_levers.py:115` and `:235`

The phrase "the options neglect" appears verbatim in two places:

1. `Lever.review_lever` field description, third example (line 115):
   ```python
   "'Pooling catastrophe risk across three coastal regions diversifies "
   "exposure on paper, but the options neglect that a single hurricane "
   "season can correlate all three simultaneously.' "
   ```

2. `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4, third bullet (line 235):
   ```
   - "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but the options neglect that a single hurricane season can correlate all three simultaneously."
   ```

`OPTIMIZE_INSTRUCTIONS` at lines 73-79 explicitly warns that "weaker models shift to copying subphrases within the new examples (e.g. 'the options neglect', 'the options assume')." The warning correctly identifies the problem, but the trigger phrase is still present in the very prompt it is warning about. The llama3.1 runs (96, gta_game: 16/16 reviews use the pattern) demonstrate this is the active root cause of the secondary template lock.

### B2 — `review_lever` examples are injected twice into every LLM call

`identify_potential_levers.py:103–118` (Lever field description) and `identify_potential_levers.py:229–236` (system prompt section 4)

The three `review_lever` examples appear both in the `Lever` Pydantic field description and in the system prompt. Because `llama_index` serialises the full Pydantic schema (including field descriptions) when constructing a structured-output prompt, the LLM receives the same three examples twice per call — once embedded in the JSON schema block and once in the human-readable system prompt. Double injection amplifies the copyable-phrase signal and increases template-lock severity. It also wastes tokens on every call.

The companion class `LeverCleaned` correctly comments that its field descriptions are not serialized (lines 203–205), but no such comment or guard exists on `Lever.review_lever`.

---

## Suspect Patterns

### S1 — Shared dispatcher accumulates cross-thread `TrackActivity` handlers

`runner.py:104–108` and `:146–148`

In `run_single_plan`, a fresh `TrackActivity` instance is created per plan and registered with the singleton `get_dispatcher()`:

```python
dispatcher = get_dispatcher()
with _file_lock:
    set_usage_metrics_path(...)
    dispatcher.add_event_handler(track_activity)
```

When `workers > 1`, multiple threads call `run_single_plan` concurrently. Each adds its own handler to the shared dispatcher. During the overlap window, LLM events from thread A are routed to both thread A's and thread B's `track_activity.jsonl` (the dispatcher broadcasts to all registered handlers). This cross-contamination is then hidden because `track_activity_path.unlink(missing_ok=True)` deletes the file at line 149 regardless of content. The bug is masked but causes the file to be silently incorrect whenever parallel workers overlap.

### S2 — Case-sensitive exact-name deduplication may miss near-identical names

`identify_potential_levers.py:340–345`

```python
if lever.name in seen_names:
```

This is a case-sensitive string equality check. "Cost Structure" and "cost structure" would both pass through. In practice the downstream `DeduplicateLeversTask` handles semantic deduplication, so this is low-severity, but it means the `seen_names` guard only catches exact character-for-character repeats from the same call batch.

---

## Improvement Opportunities

### I1 — No structural validator on `consequences` field

`identify_potential_levers.py:89–98`

The `consequences` field description explicitly says "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field." This prohibition lives only in the prose description and is not enforced by a `@field_validator`. The llama3.1 runs (89 and 96) both place "A weakness in this approach is that…" text directly into `consequences`. A structural validator following the pattern of `check_review_format` could reject this at parse time, forcing a retry. Per `OPTIMIZE_INSTRUCTIONS` lines 61–68, any such check must use structural heuristics rather than English-only keyword matching.

### I2 — `DocumentDetails.levers` `min_length=5` constraint vs. partial-recovery path

`identify_potential_levers.py:173–176`

The `min_length=5` constraint on `levers` means the first call must generate at least 5 levers or the entire call fails with a Pydantic `ValidationError`. This is appropriate for call 1. However, calls 2 and 3 use the same schema and the same `min_length=5` constraint. If call 2 or 3 returns fewer than 5 levers (e.g., model returns 4 to avoid repeating prior names), it raises a `LLMChatError`, discards the partial output, and continues. This is consistent behaviour but may be overly strict for later calls where generating 5 novel levers is genuinely harder. Consider relaxing `min_length` on calls 2 and 3 (e.g., to 3) to improve partial-recovery rates.

### I3 — `OPTIMIZE_INSTRUCTIONS` gap: cross-field contamination not documented

`identify_potential_levers.py:27–80`

`OPTIMIZE_INSTRUCTIONS` covers 7 known problems. Cross-field contamination (critique/weakness text appearing in `consequences` rather than `review_lever`) is observed in both run 89 and run 96 (llama3.1, gta_game, levers 1–2) and described in the insight file as a negative finding. It is not listed in `OPTIMIZE_INSTRUCTIONS`, so future analysts have no documented signal for it. A short entry after the "Fragile English-only validation" item would close this gap.

---

## Trace to Insight Findings

| Insight finding | Code location | Explanation |
|---|---|---|
| Secondary lock "the options neglect/overlook/fail to" persists in run 96 (100% on gta_game) | B1: line 115 and 235 | The third example supplies the exact copyable opener. OPTIMIZE_INSTRUCTIONS warns about it but the prompt was not changed. |
| Consequences field contamination (llama3.1, weakness text in consequences) — unchanged run 89 → 96 | I1: no validator on consequences | Without a structural check, the model's output is accepted even when it violates the prose prohibition in the field description. |
| Third system prompt example contains "the options neglect" — warning and root cause coexist | B1 | Direct code evidence that the root cause identified in OPTIMIZE_INSTRUCTIONS lines 73-75 is still present at line 235. |
| Partial recovery events increased (1 → 4) | I2, S1 | The `min_length=5` on all three calls makes later calls more fragile; the shared-dispatcher bug may cause usage-tracking inconsistencies but does not directly cause partial recoveries. |
| Gemini hong_kong_game: 6 levers vs 18 (1/3 calls succeeded) | No direct code bug; non-deterministic model behaviour. The partial-recovery logging at runner.py:352–356 correctly captures this. |
| Duplicate examples between Lever field description and system prompt (token waste, double lock signal) | B2: lines 103–118 and 229–236 | Double injection amplifies whatever template-lock effect the examples already create. |

---

## PR Review

**PR #339: "fix: relax option count validator, raise review min_length, clean up dead code"**

### Change 1 — `check_option_count`: `len(v) != 3` → `len(v) < 3`

Implementation matches intent. The validator now rejects under-generation (< 3 options) while tolerating over-generation (> 3). The docstring correctly references run 82 (not run 89, which was corrected). Zero observable effect in runs 96-02 — models consistently produce exactly 3 options — but the change is directionally correct because downstream `DeduplicateLeversTask` can handle extras while under-generation silently breaks downstream assumptions.

No bugs in the implementation. Edge case: a model that returns 0 options (empty list) was also caught by `!= 3` but is now caught equally well by `< 3`. No regression.

### Change 2 — `review_lever` `min_length`: 20 → 50

Directly fixed the confirmed LLMChatError in run 89 (parasomnia, "Sensor Data Sharing" — 19 chars, a lever name pasted into the review field). The new threshold is sufficient: in run 96, the parasomnia plan averages 149-char reviews. No new failures were introduced. The chosen value (50) is reasonable — it is high enough to reject one-word or name-only stubs and low enough to accept any genuine critical review sentence.

No bugs. The change does not address the root cause (why llama3.1 pasted a name into the review field) — only the symptom — but catching it structurally is the appropriate approach given the i18n constraint.

### Change 3 — Dead-code examples stripped from `LeverCleaned.review` field description

Correct. The comment added at lines 203–205 accurately explains why the field has no examples. This does not affect LLM behaviour (the class is never serialized to an LLM), but it removes misleading duplication that could confuse developers reading the code.

**Gap**: The PR removed examples from `LeverCleaned.review` but did not audit whether examples in `Lever.review_lever` (lines 107-116) duplicate the system prompt (lines 232-235). Both still carry the same three examples verbatim (B2 above), including the lockable "the options neglect" phrase (B1 above).

### Change 4 — `OPTIMIZE_INSTRUCTIONS` template-lock migration note (lines 73-79)

Accurate documentation. The note correctly identifies the mechanism (subphrase copying rather than full-opener copying) and names the correct non-lockable structural template (the agriculture example). The note will help future analysts identify this pattern.

**Critical gap**: The PR documents the problem without fixing it. Lines 73-79 warn that "examples must avoid reusable transitional phrases" while line 235 still contains "the options neglect" — an example of exactly that anti-pattern. A reviewer following OPTIMIZE_INSTRUCTIONS would correctly flag this inconsistency.

### Change 5 — Docstring run reference: 89 → 82

Correct. The 2-option bug was observed in run 82 (llama, gta_game), not run 89. Factual fix with no behavioural effect.

### Overall PR assessment

The PR achieves its primary goal (eliminating the llama3.1 parasomnia LLMChatError). The supporting changes (option count relaxation, dead-code cleanup, OPTIMIZE_INSTRUCTIONS) are individually correct. The PR does not introduce new bugs. The main weakness is that it documents a root cause (lockable third example) without addressing it — the OPTIMIZE_INSTRUCTIONS warning and the actual trigger phrase now coexist in the same file.

---

## Summary

Two confirmed bugs and one thread-safety suspect are the main findings:

**B1** is the most actionable: the third `review_lever` example at lines 115 and 235 contains "the options neglect", the exact phrase OPTIMIZE_INSTRUCTIONS warns about. Replacing it with domain-specific critique that does not contain any "the options [verb]" pattern (per the agriculture example template) would directly address the 100% template-lock rate in llama3.1 gta_game runs.

**B2** is a prompt-efficiency issue: the same three examples are injected into every LLM call twice — once via the Pydantic field description and once via the system prompt. This doubles the lockable signal and wastes tokens. Removing the examples from the `Lever.review_lever` field description (or from the system prompt) would halve the injection frequency.

**I1** (no consequences validator) is the correct next step for the cross-field contamination problem identified in the insight file and flagged in OPTIMIZE_INSTRUCTIONS as an open gap.

**S1** (shared dispatcher in parallel runner) is a latent data-quality bug that does not affect plan outputs but corrupts per-plan usage tracking files when `workers > 1`. It is masked by the `track_activity_path.unlink()` call.

The PR verdict from the insight file — **KEEP** — is correct. The PR improves success rate, introduces no regressions, and the option count and min_length changes are sound engineering even when their observable impact is currently zero.
