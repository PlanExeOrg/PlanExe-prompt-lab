# Code Review (claude)

## Bugs Found

### B1 — Anti-parrot instruction absent from call-1
**File:** `identify_potential_levers.py:274–284`

The anti-parrot sentence — `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence."` — was added by PR #483 to the `prompt_content` assembled for `call_index >= 2` only. The call-1 branch (`call_index == 1`) sets `prompt_content = user_prompt` with no modification.

```python
for call_index in range(1, max_calls + 1):
    if call_index == 1:
        prompt_content = user_prompt           # ← no anti-parrot guard
    else:
        prompt_content = (
            f"Generate 5 to 7 MORE levers with completely different names. "
            f"Each review_lever must be a genuine critical assessment — "
            f"not a restatement of the consequence. "    # ← call-2+ only
            ...
        )
```

The PR description says "Anti-parrot in call-2+", so this was intentional design — but the insight data confirms it is an incomplete fix. llama3.1 produced 7 exact-copy (sim=1.0) parrots on the gta_game plan in run 5/46, all from call-1. The system prompt's Section 4 contains examples and a brief direction, but without an explicit prohibition in the call-1 user message, llama3.1 falls back to copying `consequences` into `review_lever` verbatim.

**Severity:** High — confirmed regression in run 5/46.

---

### B2 — `review_lever` field description stripped of structural anchors
**File:** `identify_potential_levers.py:117–119`

Current state after PR #483:
```python
review_lever: str = Field(
    description="Critical review (20–40 words). No square brackets or placeholders."
)
```

PR #483 removed two phrases that were present in PR #482:
- `"one sentence"` — structural anchor telling the model to produce a single complete sentence
- `"See system prompt section 4 for examples."` — cross-reference directing models to Section 4

Section 4 of the system prompt (lines 225–229) contains three multi-domain review examples that structurally constrain the output format. Without the pointer, llama3.1 does not use them. The word-count hint `(20–40 words)` alone is insufficient for this model to produce a structurally correct review rather than copying the `consequences` text.

The `OPTIMIZE_INSTRUCTIONS` block (line 69–92) explicitly warns: "A Pydantic field description containing a structural phrase… is read as a literal instruction." The removal follows that principle, but went too far — `"one sentence"` is a minimal structural constraint, not a template-lock trigger phrase.

**Severity:** High — confirmed regression in run 5/46 (7/7 call-1 levers are exact copies).

---

## Suspect Patterns

### S1 — `consequences` description parsed as brevity ceiling by gpt-4o-mini
**File:** `identify_potential_levers.py:112`

```python
consequences: str = Field(
    description="Direct effect and one downstream implication (30–60 words)."
)
```

The phrase `"Direct effect and one downstream implication"` enumerates two clauses. gpt-4o-mini interprets this as: write one clause for the direct effect and one clause for the downstream implication — two short clauses totalling ~18–22 words. The `(30–60 words)` annotation is then treated as an upper bound (ceiling), not a lower bound. Result: gpt-4o-mini went from 74% in-range (run 5/43) to 0% in-range (run 5/50), all consequences 18–25 words.

The phrasing conflates content structure with length requirements in the same short description. Models that interpret `"one downstream implication"` as `"one sentence"` cannot reconcile that with 30–60 words.

---

### S2 — `options` description "one sentence" anchors brevity below the floor
**File:** `identify_potential_levers.py:115`

```python
options: list[str] = Field(
    description="Exactly 3 options. Each is one sentence (15–25 words) — a concrete strategic approach."
)
```

`"one sentence"` is a brevity signal. gemini-flash treats it as permission to produce the shortest complete sentence that satisfies the semantic requirement, landing at 13.9 words average — below the 15-word minimum. The `(15–25 words)` target is overridden by the structural anchor. Prior to PR #483, gemini-flash averaged 23.5 words per option (71% in range).

---

### S3 — `partial_recovery` event hardcodes `expected_calls=3`
**File:** `runner.py:583`

```python
_emit_event(events_path, "partial_recovery",
            plan_name=plan_name,
            calls_succeeded=pr.calls_succeeded,
            expected_calls=3)    # ← always 3
```

The threshold was fixed to `< 2`, correctly identifying plans that completed with only 0 or 1 calls. However, the emitted event still says `expected_calls=3`, which is the maximum typical count. For a plan that completed in 2 calls (the normal happy path when a model produces 8+ levers per call), this value is misleading in the event log. It also does not reflect the actual `min_levers=15` logic. The event fires only for genuine partial recoveries (`calls_succeeded < 2`), so the operational impact is low, but analysis scripts that read `expected_calls` will see an incorrect value.

---

### S4 — No warning when `options` list exceeds 3 items
**File:** `identify_potential_levers.py:133–145`

The `check_option_count` validator only enforces a minimum:
```python
if len(v) < 3:
    raise ValueError(f"options must have at least 3 items, got {len(v)}")
```

Models returning 4+ options silently pass validation. The field description says "Exactly 3 options." Downstream consumers that index `options[0]`, `options[1]`, `options[2]` are safe, but any code that iterates or counts options expecting exactly 3 could produce unexpected output. A log warning at `len(v) > 3` would make over-generation visible without rejecting it.

---

## Improvement Opportunities

### I1 — Add anti-parrot instruction to call-1
**File:** `identify_potential_levers.py:276`

The call-1 prompt is currently unguarded for parroting. Adding the same anti-parrot sentence used in call-2+ is the minimal fix:

```python
if call_index == 1:
    prompt_content = (
        f"Each review_lever must be a genuine critical assessment — "
        f"not a restatement of the consequence.\n\n"
        f"{user_prompt}"
    )
```

Risk: the `OPTIMIZE_INSTRUCTIONS` note warns that prohibition text can become a template for small models. In practice, a prohibition about parroting does not provide a copyable structure for `review_lever`, so the risk is low. Confirm with a llama3.1 re-run on gta_game.

---

### I2 — Rephrase `consequences` to decouple content from length
**File:** `identify_potential_levers.py:112`

Proposed:
```python
consequences: str = Field(
    description="The direct effect of pulling this lever and one key downstream implication. Write 30–60 words."
)
```

Separating the content requirement (`"The direct effect… and one key downstream implication"`) from the length requirement (`"Write 30–60 words."`) prevents gpt-4o-mini from parsing the word count as a ceiling. The imperative `"Write 30–60 words"` frames length as a minimum, not a cap.

---

### I3 — Restore structural anchor to `review_lever` field description
**File:** `identify_potential_levers.py:117–119`

Proposed:
```python
review_lever: str = Field(
    description="Critical review in one sentence (20–40 words). See system prompt section 4 for examples. No square brackets or placeholders."
)
```

`"one sentence"` provides the structural minimum that llama3.1 needs. `"See system prompt section 4 for examples."` reinstates the cross-reference that directs llama3.1 to the three domain-specific examples, preventing verbatim consequence copying. This is the wording from the pre-PR #483 state that worked for llama3.1 in run 5/39.

---

### I4 — Remove or relax `"one sentence"` from options field description
**File:** `identify_potential_levers.py:115`

The `"one sentence"` constraint in the options description is the likely cause of gemini-flash options falling below the 15-word floor. The length bound `(15–25 words)` is already present; the structural anchor is redundant and counterproductive:

```python
options: list[str] = Field(
    description="Exactly 3 options. Each option is 15–25 words — a concrete strategic approach."
)
```

If `"one sentence"` is retained to prevent multi-sentence options, it should be combined with a lower-bound emphasis: `"one complete sentence of 15–25 words"`.

---

### I5 — Update OPTIMIZE_INSTRUCTIONS with consequence-parroting entry
**File:** `identify_potential_levers.py:27–93`

The `OPTIMIZE_INSTRUCTIONS` block documents known quality problems. The consequence-parroting issue (review ≡ consequences) is now confirmed as a recurring problem but has no entry. Proposed addition after the existing "Verbosity amplification" entry:

```
- Consequence parroting. Weaker models (llama3.1, gpt-oss-20b) copy the
  consequences field verbatim into review_lever, especially in call-1.
  The anti-parrot instruction ("Each review_lever must be a genuine critical
  assessment — not a restatement of the consequence.") must appear in both
  the call-1 and call-2+ user prompts. The review_lever field description
  must retain "one sentence" as a structural anchor; without it, llama3.1
  on complex plans reproduces consequences exactly. The system-prompt
  section-4 cross-reference ("See system prompt section 4 for examples.")
  is also load-bearing for very small models.
```

---

### I6 — Log a warning when `options` count exceeds 3
**File:** `identify_potential_levers.py:133–145`

Add a log warning in the validator to surface over-generation without rejecting it:

```python
if len(v) > 3:
    logger.warning(f"options has {len(v)} items; expected exactly 3 — passing to downstream deduplicate step")
```

This makes the over-generation visible in logs without breaking the pipeline.

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|---|---|
| llama3.1 gta_game call-1 exact-copy parrots (7/7, sim=1.0) — insight Negative #1 | **B1** (no anti-parrot in call-1) + **B2** (removed structural anchor and section-4 pointer from `review_lever` field description) |
| gpt-4o-mini consequences collapsed to 0% in 30–60w range (avg 20.6w) — insight Negative #2 | **S1** (`"one downstream implication"` parsed as a brevity ceiling) |
| gemini-flash options shortened below 15-word floor (avg 13.9w) — insight Negative #3 | **S2** (`"one sentence"` in options field description anchors brevity) |
| Anti-parrot fixed gpt-oss-20b call-2+ exact parrots: 6 → 0 — insight Positive #3 | Confirms the anti-parrot instruction works for call-2+; absence of same instruction in call-1 explains B1 regression |
| partial_recovery threshold fix confirmed — insight Positive #6 | Confirmed in `runner.py:577–583`; threshold now correctly `< 2` |
| OPTIMIZE_INSTRUCTIONS missing consequence-parroting entry — insight code suggestion C4 | **I5** |

---

## PR Review

**PR #483: "Strip field descriptions to word limits, anti-parrot in call-2+, fix threshold"**

### What the PR claims to do

1. Minimal field descriptions — strip redundant guidance, keep only word limits
2. Anti-parrot in call-2+ — add prohibition sentence to subsequent-call user prompt
3. Minimal section 4 — no copyable template
4. System prompt sections 2 and 6 — add word limits for consequences and options
5. Fix `partial_recovery` threshold: `< 3` → `< 2`

### Assessment

**Threshold fix (item 5):** Correct. `runner.py:579` now has `pr.calls_succeeded < 2`. The companion check in `_run_levers` at `runner.py:131` (`if actual_calls < 2`) is consistent. This is an unambiguous improvement.

**Anti-parrot in call-2+ (item 2):** Partially correct. The sentence was placed correctly in the call-2+ user prompt (`identify_potential_levers.py:281`). It successfully eliminated gpt-oss-20b call-2+ exact-copy parrots. However, the PR does not extend this protection to call-1, where llama3.1 exhibits the same failure mode. The PR description states "call-2+" explicitly — this is a known scope limitation, not an oversight — but it created a new regression (B1).

**Minimal field descriptions (item 1):** Mixed outcome. The `review_lever` description change (removing `"one sentence"` and the section-4 cross-reference) caused llama3.1 to copy consequences verbatim in call-1 on the gta_game plan. The `consequences` description change (`"Direct effect and one downstream implication"`) caused gpt-4o-mini to collapse consequence length to 0% in-range. The `options` description (`"one sentence (15–25 words)"`) caused gemini-flash to fall below the 15-word floor.

The PR's rationale ("field descriptions stripped of everything the system prompt already says") is sound in principle but assumes all models adequately use the system prompt. For llama3.1 and gpt-4o-mini, field descriptions serve as local, high-priority instructions that override system-prompt guidance when there is ambiguity. Stripping them too aggressively caused these models to misinterpret the remaining cues.

**Implementation gap — call-1 user prompt not modified:** `identify_potential_levers.py:276` sets `prompt_content = user_prompt` for call-1 with no anti-parrot instruction. Since the PR's stated goal is "Anti-parrot in call-2+", this is consistent with the intent, but the implementation leaves call-1 vulnerable. This is the primary code-level gap.

**Implementation gap — `expected_calls=3` not updated:** After the threshold change from `< 3` to `< 2`, the `expected_calls=3` argument in the event emission at `runner.py:583` was not updated to reflect the corrected semantics. It still reads `expected_calls=3`, which does not match the changed threshold logic.

**Section 4 preamble change (item 3):** The preamble was changed to `"A one-sentence critical review (20–40 words). Examples:"`. This is an improvement in the system prompt — it makes the word count explicit and names the structure. The examples themselves are domain-varied and structurally distinct (farming/labor, clinical trials, insurance), consistent with the `OPTIMIZE_INSTRUCTIONS` guideline about spanning multiple domains.

**Net assessment:** The PR achieves its primary objectives (haiku consequence compression, gpt-oss-20b call-2+ anti-parrot, threshold fix) but introduced three regressions by over-stripping field descriptions (B1, B2, S1, S2). The implementation is technically correct for its stated scope; the issue is the stated scope was too narrow.

---

## Summary

The most critical bugs are both caused by PR #483's field-description minimization:

**B1** — The anti-parrot instruction was added only to the call-2+ user prompt. llama3.1 parrots consequences in call-1, so the fix does not reach the regression. This is the code-level root cause of the 7 exact-copy levers observed in run 5/46 gta_game.

**B2** — Removing `"one sentence"` and `"See system prompt section 4 for examples."` from the `review_lever` field description eliminated the structural cues llama3.1 relies on. The model reverted to copying consequences verbatim when deprived of both the sentence-level constraint and the pointer to the examples.

Three suspect patterns explain the other regressions: `consequences` description phrasing causes gpt-4o-mini to treat `"one downstream implication"` as a length cap (S1); `options` description `"one sentence"` drives gemini-flash below the 15-word floor (S2); and the `partial_recovery` event emits a stale `expected_calls=3` after the threshold fix (S3).

The `partial_recovery` threshold fix and anti-parrot sentence for call-2+ are correct and effective; the path to resolution is targeted additions (B1: extend anti-parrot to call-1) and targeted restores (B2, S1, S2: add back minimal structural anchors to field descriptions without restoring the template-lock phrases that were previously causing problems).
