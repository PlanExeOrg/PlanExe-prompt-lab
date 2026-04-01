# Synthesis

## Cross-Agent Agreement

Only one insight file (`insight_claude.md`) and one code review file (`code_claude.md`) exist for
this analysis. The two perspectives converge tightly on every major finding:

1. **Root cause of qwen3-30b regression and gpt-oss-20b template-lock migration**: the `review_lever`
   Pydantic field description (line 129) and the Section 4 validation-protocol preamble (line 247)
   both contain the phrase "the proposed options collectively do not resolve", which is a
   sentence-structural cue that mid-tier models copy and vary. OPTIMIZE_INSTRUCTIONS (lines 86–92)
   explicitly warns against this anti-pattern; the PR introduced exactly the anti-pattern it was
   meant to fix.

2. **gpt-4o-mini improved**: template-lock rate dropped from ~10/17 to ~2/17. Both agents agree
   this is a genuine positive outcome of PR #479.

3. **gpt-oss-20b fabricated percentages**: 0 → 5–6 per plan. Both agents agree this is a regression
   and link it to the Section 5 abstract prohibition potentially activating number-generation
   attention.

4. **B1 (pre-existing code bug)**: "MORE levers" prompt on call 2+ fires with `[]` exclusion list
   when call 1 failed, producing confused continuation output (llama3.1 short labels, residual
   "leaving unaddressed" in levers 9–18). Both agents identify this.

5. **Verdict: CONDITIONAL**. Both agents agree the PR should not be merged as-is.

## Cross-Agent Disagreements

No meaningful disagreements. The insight and code review files were both produced by the same
model (Claude) and draw on the same evidence. One nuance to note: the insight flags the "Controls
X vs Y" removal as harmless (already absent), while the code review notes it is also correct
housekeeping — both assessments are consistent.

Source-code verification confirms:
- **B3 confirmed** (`identify_potential_levers.py:127–131`): field description reads  
  `"that the proposed options collectively do not resolve"` — exactly the copyable phrase.
- **B4 confirmed** (`identify_potential_levers.py:246–247`): Section 4 preamble reads  
  `"One sentence identifying the key risk or constraint that the proposed options collectively do not resolve."` — same phrase at a second location.
- **B1 confirmed** (`identify_potential_levers.py:297–306`): when call_index != 1 and
  `generated_lever_names` is empty (because call 1 threw), the prompt becomes  
  `"Generate 5 to 7 MORE levers … Do NOT reuse any of these already-generated names: []"`.
- **B2 confirmed** (`runner.py:577–583`): `pr.calls_succeeded < 2` fires `partial_recovery`
  even when a model returns ≥ 15 levers in one clean call.
- **S4 confirmed** (`identify_potential_levers.py:258`): the prohibition  
  `"NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context"`
  is present and is an abstract prohibition of the type OPTIMIZE_INSTRUCTIONS (lines 80–82) warns
  against.

---

## Top 5 Directions

### 1. Rewrite `review_lever` field description and Section 4 preamble to remove copyable phrase
- **Type**: prompt change
- **Evidence**: B3 (code_claude), B4 (code_claude), negative findings 1 and 2 (insight_claude).
  Both locations (`identify_potential_levers.py:127–131` and `246–247`) carry "the proposed options
  collectively do not resolve". qwen3-30b went from 0/15 template-locked to ~9/20 after the PR.
  gpt-oss-20b shifted from "options still leave X unaddressed" to "do not resolve/address/mitigate
  the risk that…" — lock rate increased from 10/17 to 15/17. OPTIMIZE_INSTRUCTIONS lines 86–92
  document this exact anti-pattern.
- **Impact**: Directly removes the root cause driving two regressions. Affects qwen3-30b (new lock)
  and gpt-oss-20b (shifted lock). gpt-4o-mini and claude-haiku are unlikely to regress since
  they are less sensitive to structural cues, and the existing diverse Section 4 examples already
  provide content-goal guidance for stronger models.
- **Effort**: low — two text-only edits in one file.
- **Risk**: replacing with genuinely goal-oriented language ("state the gap that would persist even
  if all three options were carried out in full") avoids introducing another copyable phrase. The
  risk is low if the fix is goal-focused, not sentence-structural.

### 2. Replace Section 5 abstract numeric prohibition with a worked counter-example
- **Type**: prompt change
- **Evidence**: S4 (code_claude), negative finding 4 (insight_claude), I3 (code_claude).
  `identify_potential_levers.py:258` has the abstract prohibition  
  `"NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the project context"`.
  OPTIMIZE_INSTRUCTIONS (lines 80–82) warns that abstract prohibitions cause weaker models to treat
  the banned pattern as a template. gpt-oss-20b went from 0 fabricated percentages before the PR
  to 5–6 per plan after. The phrase "use only numbers that appear verbatim" may license interpreting
  a budget figure (HK$470M) as permission to derive percentage splits.
- **Impact**: Stops fabricated-% regression for gpt-oss-20b. A concrete BAD/GOOD example pair gives
  the model a positive template to follow rather than an abstract rule to misapply. claude-haiku
  and gpt-4o-mini are unaffected (they already comply).
- **Effort**: low — text-only change replacing ~1 bullet point in Section 5 with a 2-line example.
- **Risk**: The example must avoid introducing any new copyable structure. Keep the BAD example
  minimal and the GOOD example qualitative.

### 3. Fix B1: Gate "MORE levers" continuation prompt on non-empty exclusion list
- **Type**: code fix
- **Evidence**: B1 (code_claude), negative finding 5 (insight_claude), confirmed at
  `identify_potential_levers.py:297–306`.
  When call 1 fails and call 2 runs, `generated_lever_names` is empty and the prompt becomes
  `"Generate 5 to 7 MORE levers … Do NOT reuse any of these already-generated names: []"`.
  This confuses the model into treating it as a continuation rather than a first call. llama3.1
  (run 25) shows this: levers 9–18 have residual "leaving unaddressed" and short labels
  ("Empower the Director", "Opt for Venice").
- **Impact**: Affects all models when their first call fails. Fixes disjointed output quality
  for the retry path. Benefits every model that occasionally fails call 1.
- **Effort**: low — single condition change: `if call_index == 1 or not generated_lever_names:
  prompt_content = user_prompt`.
- **Risk**: negligible. The change only affects the failure path. Normal two-call flow (call 1
  succeeds but yields < 15 levers) is unaffected.

### 4. Add a fourth structurally distinct `review_lever` example in Section 4
- **Type**: prompt change
- **Evidence**: I4 (code_claude), negative finding 1 (insight_claude), Q2 (insight_claude).
  The three current examples (`identify_potential_levers.py:249–252`) all begin with a gerund
  subject ("Switching…", "Each additional…", "Pooling…") and follow a subject→mechanism→risk
  arc. qwen3-30b's lock may be driven by this structural convergence. A fourth example with
  a fundamentally different rhetorical structure (e.g., conditional framing, or beginning with
  a domain-specific noun rather than a verb) would widen the distribution of legal outputs.
- **Impact**: Reduces qwen3-30b's structural lock. Provides additional cover for other mid-tier
  models. Aligns with OPTIMIZE_INSTRUCTIONS' "No two examples should share a sentence pattern
  or rhetorical structure."
- **Effort**: low — add one more example sentence (≤50 words) in a distinct domain with a
  distinct sentence structure.
- **Risk**: Adding an example to Section 4 slightly increases system-prompt length. Keep it
  concise. Ensure it does not introduce a new reusable transitional phrase.

### 5. Fix B2: Correct the `partial_recovery` event condition in runner.py
- **Type**: code fix
- **Evidence**: B2 (code_claude), confirmed at `runner.py:577–583`.
  `pr.calls_succeeded < 2` fires `partial_recovery` for any 1-call success. If a model returns
  ≥ 15 levers in one call, the run succeeded cleanly but the event fires anyway, polluting
  `events.jsonl` with false warnings.
- **Impact**: Eliminates misleading noise in the events log. Prevents false-positive alerts in
  pipeline monitoring that reads `events.jsonl`.
- **Effort**: low — change the condition to check whether the final lever count is below
  `min_levers` (or whether the plan completed with an error), not whether call count < 2.
- **Risk**: negligible — purely an observability fix; no effect on output quality.

---

## Recommendation

**Pursue Direction 1 first: rewrite the `review_lever` field description and the Section 4
preamble.**

This is the single highest-leverage change because:

1. It addresses a **structural root cause** (copyable sentence-template in two locations) rather
   than a symptom. Fixing it simultaneously reduces the qwen3-30b regression and the gpt-oss-20b
   shifted lock without requiring separate follow-up changes.

2. It is **directly required** before PR #479 can be merged. The PR's template-lock fix replaced
   one copyable phrase with another — the underlying defect is still live in the current code.

3. It is **low-effort**: two targeted text edits with zero logic changes.

4. It **aligns with OPTIMIZE_INSTRUCTIONS** lines 86–92, which document the exact anti-pattern.
   The fix makes the code consistent with its own documentation.

**Exact changes:**

**File**: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

**Change A — `Lever.review_lever` field description (`lines 127–131`)**

Current:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): identify the key risk or constraint "
        "that the proposed options collectively do not resolve. "
        "Do not use square brackets or placeholder text."
    )
)
```

Proposed:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): state the specific structural or operational gap "
        "that would remain open even if all three options were fully executed. "
        "Do not use square brackets or placeholder text."
    )
)
```

Rationale: replaces sentence-structural language ("the proposed options collectively do not
resolve") with content-goal language ("the gap that would remain open") that cannot be directly
copied as a sentence opener.

**Change B — Section 4 validation-protocol preamble (`line 247`)**

Current:
```
     One sentence identifying the key risk or constraint that the proposed options collectively do not resolve.
```

Proposed:
```
     One sentence naming the specific structural or operational gap that would persist even if all three options were carried out in full.
```

Rationale: same principle as Change A. Both locations must be updated — fixing only one leaves
the other as a copy source for mid-tier models.

After these two changes, run a new self_improve iteration (5/32–5/38) to confirm:
- qwen3-30b template-lock rate returns to ~0/20 (the before-PR baseline)
- gpt-oss-20b lock rate decreases (expected: shifted to a new phrase or eliminated)
- gpt-4o-mini retains its improvement (lock rate stays ~2/17)

---

## Deferred Items

**Direction 2 (Section 5 counter-example for fabricated numbers)**: Worth doing in the same PR
as Direction 1 if the developer wants a combined fix, or immediately after as a follow-up. The
gpt-oss-20b fabricated-% regression is a real content quality issue, but it can be isolated from
the template-lock root cause. Tracking issue: the BAD/GOOD example must not introduce a new
structural template.

**Direction 3 (B1: empty exclusion list)**: A clean, safe code fix. Can be included in the same
PR as Direction 1 or filed as a standalone code cleanup. It does not interact with the prompt changes.

**Direction 4 (fourth review example)**: Complementary to Direction 1. Best evaluated after
Direction 1's iteration data shows whether the field description change alone is sufficient to
break qwen3-30b's structural lock. If qwen3-30b still locks on example structure, add the fourth
example.

**Direction 5 (B2: false partial_recovery event)**: Low-priority observability fix. No effect on
output quality. Fine to bundle with any future runner.py refactor.

**OPTIMIZE_INSTRUCTIONS update (I5)**: After the field description fix is confirmed working,
add a concrete note to `OPTIMIZE_INSTRUCTIONS` documenting the observed failure mode  
("the review_lever description phrase is itself a copyable sentence fragment — weaker models
paraphrase it…"). This prevents future iterators from repeating the same mistake.

**S2 (options validator accepts > 3)**: The field description says "No more, no fewer" but the
validator allows over-generation. The intent (documented in comment lines 186–191) is that
over-generation is acceptable. The field description should say "At least 3 options" to align
with actual behavior. Low-priority cosmetic fix.

**Q3/I1 (claude-haiku multi-sentence reviews)**: claude-haiku consistently writes 2–4 sentence
reviews (~250–280 chars) that exceed the "one sentence (20–40 words)" target. This is high-quality
output that adds analytical value. The soft-cap logging (I1) would surface this for monitoring
without breaking the run. Defer unless the enrich step (downstream) is confused by longer reviews.
