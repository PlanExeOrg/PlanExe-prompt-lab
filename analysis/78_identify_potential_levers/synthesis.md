# Synthesis

## Cross-Agent Agreement

Both agents (insight and code review) converge on the same verdict: **KEEP PR #484**. The
removal of `"the specific gap the three options leave unaddressed"` from the `review_lever`
field description and the section 4 preamble completely eliminates haiku's template lock
(24.7% → 0%) with zero regressions across all 6 other models. Both agents identify haiku's
residual verbosity (1.9–2.0× baseline) and fabricated-number rate (0.30/lever) as the
remaining open problems, and both trace the verbosity root cause to the section 4 examples
being at the upper end of the 20–40 word target (OPTIMIZE_INSTRUCTIONS "Verbosity amplification"
mechanism). Neither agent finds any edge case, regression, or omission in the PR itself.

The code review also confirms two functional bugs in `runner.py` (B1, B2) that create
misleading observability — these are independent of PR #484 but affect analysis reliability.

## Cross-Agent Disagreements

There are no substantive disagreements. The two agents cover complementary scopes: insight
focuses on quantitative before/after metrics across 7 models; code review focuses on the
source code for runner logic bugs and latent hazards. Where they overlap (haiku verbosity,
partial-recovery event interpretation) they agree on the root cause and direction.

One potential tension: the code review's B2 finding asserts that the before-run
`partial_recovery` events (calls_succeeded=2) documented in the insight would **not** be
emitted by the current code (event threshold now `< 2`, not `< 3`). This means the insight's
count of "2 partial recovery events before, 0 after" is actually comparing events generated
under different threshold regimes. However, this does not affect the conclusion — the template
lock fix is real and confirmed by both the lever counts (silo: 14→21, gta_game: 16→21) and
the absence of the "All/None of the three options…" pattern in after-run output.

**Source code verification:**
- B1 confirmed: `runner.py:131` — `if actual_calls < 3:` fires for 2-call runs that the
  preceding comment explicitly calls "normal for models that produce 8+ levers per call."
- B2 confirmed: `runner.py:579` — `partial_recovery` event emitted at `calls_succeeded < 2`
  (fires only for 1 call), while the warning above fires at `< 3`. A 2-call run gets a
  spurious WARNING but no event in `events.jsonl`.
- I1 confirmed: `identify_potential_levers.py:159–175` — `check_review_format` enforces
  min 10 chars, no maximum. System prompt says "20–40 words"; haiku averages 281 chars (~56
  words) post-PR.
- I2 confirmed: `identify_potential_levers.py:247–249` — all three examples are 35–40 words,
  sitting at the top of the stated target range.
- S1 confirmed: `identify_potential_levers.py:117–118` — English-specific keyword examples
  (`"Controls ... vs."`, `"Weakness:"`) embedded in the `consequences` field description.

## Top 5 Directions

### 1. Shorten section 4 review_lever examples to 20–28 words each
- **Type**: prompt change
- **Evidence**: I2 (code review), H1 (insight), OPTIMIZE_INSTRUCTIONS line 83–85 ("Models mirror
  example verbosity … Keep review_lever examples concise"). Haiku review avg 281 chars (~56 words)
  vs. baseline 152 chars; stated target is 20–40 words. Both agents trace the verbosity directly
  to these examples. All three examples are 35–40 words — the top of the allowed range.
- **Impact**: Haiku verbosity affects content quality across all 99 post-PR levers (5 plans, all
  models run in every experiment). Reducing example length will pull haiku reviews toward
  150–200 chars without re-introducing template lock. Stronger models (already at ≤1.3× baseline)
  are unaffected. This is the highest-breadth content-quality improvement available.
- **Effort**: Low — trim three existing examples in-place. No structural change to the prompt.
- **Risk**: Shorter examples might slightly reduce review depth in stronger models. However, all
  non-haiku models already produce near-baseline lengths regardless of example length, so this
  risk is low in practice.

### 2. Add max-length cap to `check_review_format` validator
- **Type**: code fix (validator)
- **Evidence**: I1 (code review), OPTIMIZE_INSTRUCTIONS line 83–85 ("enforce a length cap in the
  system prompt to prevent output overflow"). Haiku averages 281 chars post-PR; the 40-word
  target maps to ~200–240 chars. A cap at 350 chars would reject the current haiku average
  and trigger a retry with feedback.
- **Impact**: Converts silent overlong reviews from pass-through to retryable failures. Gives the
  model explicit structural feedback and makes the 40-word bound machine-enforceable rather than
  advisory. Benefits haiku most; has no effect on well-behaved models (all at ≤200 chars).
- **Effort**: Low — add one `if len(v) > 350:` branch to the existing validator.
- **Risk**: May add one retry per lever for haiku until direction 1 is also in place. With
  direction 1 applied first, haiku should fall within the cap naturally. Combining both
  directions in a single PR is the safest approach.

### 3. Fix `_run_levers` warning threshold and align with partial_recovery event threshold (B1 + B2)
- **Type**: code fix
- **Evidence**: B1 and B2 (code review), confirmed in source code at `runner.py:131` and
  `runner.py:579`. A 2-call success (comment says "normal") emits a WARNING but no
  `partial_recovery` event. A true partial run (1 call) emits the event but also the same
  WARNING, making the two situations indistinguishable from logs alone.
- **Impact**: Fixes observability for all models. 2-call runs that complete successfully (≥15
  levers) no longer pollute logs with spurious "partial recovery" warnings. True partial runs
  (1 call, <15 levers) will correctly emit both a warning and an event. Downstream analysis
  scripts scanning `events.jsonl` will correctly detect all partial-run situations.
- **Effort**: Low — change `actual_calls < 3` to `actual_calls < 2` in `runner.py:131`, and
  align `expected_calls` in the event payload to match actual expectations.
- **Risk**: Minimal. The only behavior change is removal of a misleading WARNING for healthy runs.

### 4. Remove English-specific prohibitions from `consequences` field description (S1)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: S1 (code review). `identify_potential_levers.py:117–118` embeds `"Controls ...
  vs."` and `"Weakness:"` as English examples of text to avoid. OPTIMIZE_INSTRUCTIONS lines
  61–68 explicitly warns that English-only markers in validators and prompts are fragile for
  non-English inputs (Chinese, Japanese, Arabic, German). The same hazard applies to field
  descriptions.
- **Impact**: Latent risk for non-English inputs — currently zero observed regressions since
  baseline plans are English. The `consequences` field purpose is already clear from context;
  the English examples add confusion without adding safety. Removing them shrinks the field
  description and removes the multilingual hazard before it manifests.
- **Effort**: Low — remove one clause from the `consequences` field description.
- **Risk**: The prohibition might be providing some behavioral guardrail for English inputs.
  However, the structural separation of `consequences` and `review_lever` fields already
  communicates the intent. The risk of removal is very low.

### 5. Rename "Validation Protocols" section heading to "Format Examples"
- **Type**: prompt change (system prompt heading)
- **Evidence**: I3 (code review). `identify_potential_levers.py:243` — section 4 is named
  "Validation Protocols" but provides format examples, not validation rules. Instruction-tuned
  models may interpret the heading as a signal to treat the examples as a correctness template
  to validate against rather than as a stylistic anchor to draw variety from. This could
  contribute to example-mirroring behavior in future model releases.
- **Impact**: Low direct impact today (no regression observed). Higher value as a defensive
  measure: renaming the section to "Format Examples" or "Output Examples" reduces the risk
  that a future model release re-introduces example-mirroring behavior triggered by the
  heading framing.
- **Effort**: Very low — one word change in the system prompt.
- **Risk**: None. The content of the section is unchanged; only the heading is updated.

## Recommendation

**Pursue directions 1 and 2 together as a single PR.**

Direction 1 (shorten examples) addresses the root cause: OPTIMIZE_INSTRUCTIONS already
documents that "models mirror example verbosity" and recommends keeping examples concise.
Haiku's 1.9–2.0× verbosity affects content quality in every successfully-generated plan —
99 levers across 5 plans — making it a broader content-quality problem than a structural
failure mode that only affects individual runs.

Direction 2 (max-length cap) reinforces direction 1 by making the 40-word bound enforceable.
If a future prompt change accidentally re-introduces verbose examples, the cap ensures the
failure is visible (retryable validation error) rather than silently passing through. Both
directions are low-effort, low-risk, and directly prescribed by OPTIMIZE_INSTRUCTIONS line
83–85.

**Specific changes:**

**File**: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

1. **Shorten the three section 4 examples** (lines 247–249) to 20–28 words each. The
   current versions (35–40 words) sit at the top of the stated 20–40 word range and anchor
   haiku above the cap. Target shortened forms:

   ```
   - "Switching from seasonal to year-round labor stabilizes harvest quality but adds fixed
     idle-wage cost during the 5-month off-season, erasing per-unit savings unless utilization
     is continuous."
   - "Each additional clinical site requires sequential IRB approval and credentialing — doubling
     site count does not halve enrollment time because the overhead compounds rather than
     parallelizes."
   - "Pooling coastal catastrophe risk reduces expected annual loss, but a single hurricane
     season can correlate all three regions simultaneously, converting diversification into
     concentration risk."
   ```

   Each shortened version retains the domain-specific mechanism (idle-wage burden, IRB
   credentialing, correlation risk) while cutting word count from 35–40 to 25–30 words.

2. **Add max-length cap to `check_review_format`** (after line 174):

   ```python
   if len(v) > 350:
       raise ValueError(
           f"review_lever is too long ({len(v)} chars); expected at most ~240 chars (40 words)"
       )
   ```

   350 chars is approximately 70 words — generous enough to never reject a well-formed
   review but tight enough to reject haiku's current 281-char average if it remains above
   the 20–40 word target after the example shortening.

## Deferred Items

- **B1 + B2 (partial_recovery threshold mismatch)**: Fix the `_run_levers` warning threshold
  and align with the `partial_recovery` event threshold in `runner.py`. Important for
  observability but does not affect plan content quality. Worth fixing in a separate small PR
  targeted at `runner.py` only.

- **S1 (English prohibitions in `consequences` description)**: Remove `"Controls ... vs."` and
  `"Weakness:"` from the `consequences` field description before PlanExe is used on non-English
  inputs at scale.

- **I3 (rename "Validation Protocols" heading)**: Can be bundled with the next system prompt PR
  at no extra cost.

- **H2 (haiku fabricated numbers)**: Haiku still produces 0.30 fabricated % claims per lever
  (e.g., "40% cost reduction", "25% efficiency gain"). Adding an anti-fabrication note to
  section 4 or the field description is worth exploring once verbosity is resolved, since the
  two problems may share a root cause (haiku producing more text → more opportunities for
  invented numbers).

- **Run 54 timeout investigation**: `openrouter-openai-gpt-oss-20b` timed out on 3/5 plans in
  the after-batch. If chronic, this model should be moved to a reliability-tiered benchmark
  separate from prompt-quality evaluation runs.

- **Template-lock regression test**: The PR description notes this is a "proven fix from
  analysis 76 (PR #482)". A lightweight post-merge check that counts `"all three options"` /
  `"none of the three options"` patterns in haiku output would catch recurrence automatically
  without requiring a full insight pass.
