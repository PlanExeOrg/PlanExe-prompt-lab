# Synthesis

## Cross-Agent Agreement

Only one agent produced artifacts for this analysis (insight_claude.md, code_claude.md),
so "agreement" refers to the two independently written analyses converging on the same
findings when compared.

Both files agree on every material point:

- **Primary success confirmed**: haiku gta_game no longer fails with EOF (P1 / code review §Review Length Cap). The 36% review-length reduction was sufficient to clear the 40KB threshold.
- **B1 partial_recovery scoping confirmed**: `partial_recovery` events now correctly fire only for `identify_potential_levers`. Behaviorally correct in all runs 73–79 (P6 / code review §B1 Fix).
- **Critical regression identified**: llama3.1 gta_game (run 73) went from ok-with-partial-recovery to a hard fail. Both analyses trace this directly to `identify_potential_levers.py:321–322` — the `len(responses)==0` path that raises with no retry (insight N1 / code review B1).
- **Review length guidance is soft-only and insufficient**: haiku averages ~58 words vs. the 40-word target. No Pydantic enforcement was added (insight N2 / code review S2). Works for now but fragile.
- **Template lock persists**: 2 of 3 review examples share "X, but Y" contrastive structure; haiku shows this pattern in 14+ of 21 reviews (insight N5 / code review I3). This is exactly the failure mode described in OPTIMIZE_INSTRUCTIONS lines 73–82.
- **Fabricated percentages remain in haiku options** despite section 5 prohibition (insight N4 / code review N4 trace).
- **`partial_recovery` threshold conflates efficiency with failure**: `calls_succeeded < 3` fires even for 2-call completions that legitimately exceeded `min_levers=15` (insight implied / code review S1).

Verdict from both analyses: **CONDITIONAL** — keep the haiku EOF fix, but the llama3.1 regression requires a follow-up.

---

## Cross-Agent Disagreements

No substantive disagreements between the two files. One nuance:

- **code_claude B3** initially flags `dispatcher.event_handlers.remove()` as a possible locking issue, then self-corrects: the remove IS inside `_file_lock`, making the lock protection correct. The insight file does not mention this. The code review's self-correction is accurate — verified by reading `runner.py:527` (`finally:` block). Not a bug.

---

## Top 5 Directions

### 1. Add Single Retry on First-Call Validation Failure
- **Type**: code fix
- **Evidence**: Both insight (N1, C2, Q3) and code review (B1, I1) identify `identify_potential_levers.py:321–322` as the proximate cause of run 73's hard fail. When all levers in call 1 fail `check_option_count`, `len(responses)==0` triggers an immediate raise with no retry. Confirmed by reading the code: the loop runs at most `max_calls=5` times but has no special handling for the first-call-with-zero-successes case.
- **Impact**: Converts stochastic under-generation on call 1 into a recoverable event for all models. The same model (llama3.1) produced valid options on the same plan (gta_game) before the example change (run 52), so this is likely a stochastic miss, not a capability limit. Affects any model that intermittently produces < 3 options per lever — weaker models (llama3.1, similar) are at highest risk. Restores run 73's result from "error / null" back to "ok / partial".
- **Effort**: low — add a `retry_first_call` flag or insert one extra iteration before the `len(responses)==0` raise, with an augmented user message: `"CRITICAL: Each lever MUST have exactly 3 options. Fewer than 3 options per lever will invalidate the entire response. " + user_prompt`.
- **Risk**: minimal — the retry path is additive; if call 1 succeeds normally, this code path is never reached. One extra LLM call only on first-call failure.

### 2. Replace One "X, but Y" Review Example with a Non-Contrastive Structure
- **Type**: prompt change
- **Evidence**: Code review I3 and insight N5/H1 both flag that examples 1 and 3 share the "X ..., but Y ..." rhetorical structure. OPTIMIZE_INSTRUCTIONS lines 73–82 explicitly requires: "No two examples should share a sentence pattern." Run 79 (haiku, gta_game) shows 14+ of 21 reviews matching "X promises/offers Y but introduces/creates Z" — directly copying the shared "but" framing. This is structural template lock affecting every haiku run across all plans.
- **Impact**: Reduces haiku review homogeneity across all plans and all runs (content quality issue, not just one plan). Template-locked reviews are credibility-eroding: 14/21 levers read identically structured. Breaking 2-of-3 "but" patterns to at most 1-of-3 should significantly reduce this lock rate per OPTIMIZE_INSTRUCTIONS' own analysis. Does not risk a hard fail.
- **Effort**: low — rewrite example 1 or 3 in `identify_potential_levers.py:230–233`. Draft replacement for example 1 (agriculture):
  `"Seasonal contract labor concentrates wage spend in the 5-month harvest window, while year-round employment spreads it evenly — yet if utilization outside harvest season stays below roughly 60%, the fixed-wage floor raises per-unit cost above the contract baseline without improving quality."`
  (Uses "while … yet if" conditional framing, not "but".)
- **Risk**: Weaker models may shift template lock to the new structure rather than eliminating it. OPTIMIZE_INSTRUCTIONS acknowledges this. The move still reduces the "but" rate from 2/3 to 1/3 — net improvement even in the partial-shift case.

### 3. Add Soft Truncation of `review` in `LeverCleaned` Constructor
- **Type**: code fix
- **Evidence**: Code review I2 and S2; insight C1 and Q4. The review length cap is prompt-only; haiku produces ~58-word reviews averaging ~355 chars. If haiku reverts to 450+ chars/review, the 40KB EOF failure returns with no code-level safety net. The `LeverCleaned` constructor at `identify_potential_levers.py:352–358` is the natural truncation point — it maps `Lever.review_lever` → `LeverCleaned.review` and does not reach the LLM.
- **Impact**: Structural protection for ALL models against EOF recurrence. Downstream `EnrichLevers` adds detail anyway, making truncation at ~300 chars safe. Does not introduce a new validation failure path (unlike a Pydantic `max_length` on `Lever.review_lever` which would reject the batch).
- **Effort**: very low — one line: `review=lever.review_lever[:300],` in the `LeverCleaned(...)` constructor call at line 352–358.
- **Risk**: near zero — `LeverCleaned` is output-only; downstream steps receive the truncated review. The `EnrichLevers` step adds description text, so any content cut off here is elaborated downstream. A review of 300 chars ≈ 50 words is still sufficient to name the tension and weakness.

### 4. Fix `partial_recovery` Threshold to Reflect Actual Failure, Not Call Count
- **Type**: code fix
- **Evidence**: Code review S1 and S5; insight Q2. `runner.py:517–523` fires `partial_recovery` when `calls_succeeded < 3`, but models that return 8+ levers per call reach `min_levers=15` in 2 calls — a fully successful run. Run 73 (llama3.1, parasomnia) fires `partial_recovery` despite producing 21 levers. This inflates the partial-recovery metric and masks whether a 2-call completion was efficient or degraded.
- **Impact**: Improves metric accuracy for all models and all plans. Enables the analysis pipeline to distinguish "completed efficiently in 2 calls" from "failed on call 2, recovered with call 1 output." Currently both emit the same event. Affects every run where a model generates 8+ levers per call.
- **Effort**: medium — requires passing lever count from `IdentifyPotentialLevers.execute()` back to the runner, or checking `len(result.levers)` against `min_levers=15` instead of just `calls_succeeded < 3`. The `min_levers` constant in `identify_potential_levers.py:270` would need to be surfaced to the runner.
- **Risk**: low — metric change only; no behavior change for production outputs.

### 5. Add Prominent Options-Count Constraint at the Top of the System Prompt
- **Type**: prompt change
- **Evidence**: Insight H2 and code review I4. The "exactly 3 options" requirement appears only in `DocumentDetails.levers` field description (line 106) and section 1 of the system prompt. Run 73's 7 levers each had 1–2 options — suggesting llama3.1 did not weight this constraint heavily enough. Stronger emphasis ("CRITICAL: Every lever MUST have exactly 3 options. Fewer than 3 invalidates the entire response.") at the opening of the system prompt increases salience for instruction-following models.
- **Impact**: Primarily benefits weaker models (llama3.1, similarly sized models) that under-generate options. Works synergistically with direction #1: the retry prompt would naturally include this emphasis. Has no effect if direction #1 is also implemented (retry already adds emphasis), but independently reduces first-call under-generation rate.
- **Effort**: low — prepend or insert one sentence at the top of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` in `identify_potential_levers.py:207`.
- **Risk**: Over-emphasis on the constraint might cause models to generate exactly 3 options even when context warrants more; however, the `DocumentDetails.levers` comment at line 167–169 already says over-generation is fine for levers, and over-generation of options (4+) passes the current validator (B2 in code review), so the risk of losing over-generated options is the real exposure.

---

## Recommendation

**Implement direction #1: add a single retry on first-call validation failure.**

**Why first**: It is the highest-impact, lowest-risk change available. The llama3.1 gta_game regression (run 73) is a hard fail producing zero output — the worst outcome in the reliability spectrum. The cause is fully understood: `identify_potential_levers.py:321–322` raises immediately when `len(responses)==0`, with no chance to recover from a stochastic first-call miss. Before PR #356, llama3.1 produced output (low quality, but *something*); after, it produces nothing. This is a reliability decrease that affects the weakest models most, and direction #1 directly reverses it.

**What to change** — `identify_potential_levers.py`, lines 308–327:

Replace the exception handling block so that when `len(responses) == 0` AND the exception is a validation error (options count), one retry is made with an augmented message before the final raise:

```python
except Exception as e:
    llm_error = LLMChatError(cause=e)
    logger.debug(f"LLM chat interaction failed [{llm_error.error_id}]: {e}")
    logger.error(f"LLM chat interaction failed [{llm_error.error_id}]", exc_info=True)
    if len(responses) == 0:
        # First call failed — attempt a single retry with reinforced options constraint
        if not getattr(llm_error, '_first_call_retried', False):
            llm_error._first_call_retried = True
            retry_content = (
                "CRITICAL: Each lever MUST have exactly 3 options. "
                "Generating 1 or 2 options per lever will invalidate the entire response.\n\n"
                + user_prompt
            )
            # rebuild call_messages and retry once (call_index=1 equivalent)
            # ... (retry logic using the same system_message + retry_content)
```

The simplest robust approach is to add a `first_call_retried` boolean flag before the loop, set it on first failure with `len(responses)==0`, and on the second pass of `call_index=1` use the reinforced prompt. The current loop already handles `max_calls=5`; a retry can be accommodated by inserting one additional iteration before the loop exits on first-call failure.

**Expected outcome**: Run 73's result changes from `status: error, calls_succeeded: null` to at least `status: ok, calls_succeeded: 1` (partial recovery), restoring the pre-PR #356 behavior and netting zero hard fails across 35 plans.

---

## Deferred Items

**Direction #2 (replace "X but Y" example)**: Worth doing in the next iteration immediately after #1. Haiku template lock at 14+/21 reviews is a content quality issue affecting every haiku run. Draft the non-contrastive replacement for example 1 (see above) before committing.

**Direction #3 (truncate review in LeverCleaned)**: A one-line defensive fix. Low risk and prevents EOF recurrence if haiku verbosity increases. Pair it with direction #1 in the same PR if convenient.

**Direction #4 (fix partial_recovery threshold)**: Important for metric hygiene but does not affect production outputs. Defer to a later iteration focused on observability improvements. Requires surfacing `min_levers` to the runner.

**Direction #5 (prominent 3-options constraint)**: If direction #1's retry prompt includes the emphasis language, this becomes partially redundant. Evaluate after seeing retry results. If llama3.1 still produces under-generated options on retry, add the top-of-prompt constraint.

**B2 (unenforced upper bound on options count)**: The field description says "No more, no fewer" but the validator allows >3. Since over-generation is benign downstream (comment at line 167–169 says deduplication handles extras), the pragmatic fix is to update the field description to say "At least 3" — not add a rejecting upper bound. Deferred to a documentation-only pass.

**S3 (English marker examples in `consequences` field description)**: The `"Do NOT include 'Controls ... vs.', 'Weakness:'"` text is serialized into the JSON schema and reaches the LLM even for non-English prompts. OPTIMIZE_INSTRUCTIONS warns against this. Low urgency (hasn't caused a measured failure yet) but worth cleaning up when editing that section.

**H3 (anti-example for fabricated percentages)**: Adding a concrete bad-pattern example to section 5 may reduce haiku's fabricated-number rate. Deferred — template lock fix (#2) should be validated first before adding more examples that could themselves become templates.

**OPTIMIZE_INSTRUCTIONS update (I5/H4)**: Add a note about the `len(responses)==0` hard-fail path and the importance of first-call retry logic. Low effort, high future-synthesis value. Include in the same PR as direction #1.
