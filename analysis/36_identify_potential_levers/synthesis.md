# Synthesis

## Cross-Agent Agreement

Both `insight_claude` and `code_claude` reach the same overall verdict (**REVERT** the prompt/example/prohibition changes) with the same evidence base:

- **PR Impact**: Net regression. Plan success rate 100% → 94.3% (−2 plans, both llama3.1). Two new Pydantic validation failures (gta_game: 2 options; parasomnia: `=>` review_lever). llama3.1 hong_kong template lock reversed from 0% (PR #353 working) back to 100%.
- **B1 fix confirmed working**: The `step == "identify_potential_levers"` gate in runner.py:517–519 correctly scopes `partial_recovery` events. Both agents confirm this.
- **S1 prohibition backfire confirmed**: Both agents attribute the hong_kong 0% → 100% regression to the explicit prohibition naming the banned phrases ("The options", "The lever") — this increases their probability mass for small models. Verified in code at `identify_potential_levers.py:239`.
- **S2 domain collision confirmed**: Both agents flag the game-dev example (GPU/artist-hours) as a template leakage vector for llama3.1, which activates the most domain-similar example when generating hong_kong and gta_game reviews. Verified at `identify_potential_levers.py:230`.
- **S3 shared rhetorical structure confirmed**: Both agents observe that all three examples follow the same "apparent benefit → hidden undermining cost in unexpected dimension" adversarial structure. Verified at lines 228–231.
- **B2 (batch atomicity)**: Both agents identify that Pydantic validates the full `DocumentDetails` batch atomically — one bad lever kills all others in the batch. Confirmed by the `check_option_count` and `check_review_format` validators at lines 130–158, and the raise path at line 319–320.

## Cross-Agent Disagreements

**B3 (expected_calls hardcoded)**: `code_claude` flags that `expected_calls=3` is still a hardcoded literal at runner.py:523 (moved inline, not made dynamic), and that the value is semantically coupled to `min_levers=15` in `identify_potential_levers.py:268` without mechanical linkage. `insight_claude` says "B1 fix confirmed working." Both are correct — the step-gating works, but the literal coupling is a latent maintenance risk. Source verification: runner.py:519–523 shows `calls_succeeded < 3` and `expected_calls=3` as literals; `identify_potential_levers.py:268` shows `min_levers = 15` as a separate local variable with no cross-file reference.

**Severity of S3 (rhetorical structure homogeneity)**: `code_claude` treats it as a systemic structural flaw; `insight_claude` focuses more on S1/S2. Both are right — the per-call template drift in silo run 59 (three distinct formulaic patterns, one per LLM call) confirms S3 is real and affects even calls where "The options" prohibition did not apply.

**H2 (game-dev example itself using "The options")**: `insight_claude` raises this as an open question. Verified by reading the current source: the three `review_lever` examples at lines 228–231 do NOT start with "The options" — all three use domain-specific mechanisms as grammatical subject. The regression is attributable to S1 (prohibition increasing salience of banned phrases) and S2 (domain overlap), not to a copyable "The options" opener in the example text itself.

## Top 5 Directions

### 1. Revert prohibition and replace game-dev example with a non-gaming domain
- **Type**: Prompt change
- **Evidence**: S1 (code_claude), S2 (code_claude), H1 (insight_claude), H2 (insight_claude). Both agents agree. The explicit prohibition at line 239 is the primary culprit for the hong_kong 0% → 100% regression; the game-dev example is the secondary domain-collision vector. PR #353 achieved 0% "The options" lock on hong_kong WITHOUT a prohibition and WITHOUT a game-dev example — by changing the example content. That strategy worked; PR #354 undid it.
- **Impact**: Restores plan success rate 94.3% → 100% (2 plans recovered). Eliminates the hong_kong template lock regression. Removes the domain overlap trigger for gta_game. Affects llama3.1 (5 plans). Cloud models are largely unaffected either way.
- **Effort**: Low — remove one line (prohibition at line 239), replace one example review_lever (line 230) with a non-gaming domain (e.g., logistics, construction, finance).
- **Risk**: The new replacement example must itself avoid any rhetorical pattern overlap with existing examples (S3) and must not name any prohibited openers (S1). Verify the domain chosen does not overlap with any of the 5 test plan domains (silo, hong_kong_game, gta_game, parasomnia, sovereign_identity).

### 2. Fix B2: Lever-level rejection instead of batch-level rejection
- **Type**: Code fix
- **Evidence**: B2 (both agents). Both run 59 failures (gta_game: 2 options; parasomnia: `=>` review) were caused by a single bad lever discarding a full 5–7 lever batch on the first call, triggering the hard-raise path at `identify_potential_levers.py:319–320`. The batch-atomicity design means any future prompt change that causes one malformed lever will fail the entire plan if it occurs on the first call.
- **Impact**: Prevents total plan failure when one lever in a batch is invalid. Models that produce 5 valid levers + 1 bad one can still contribute their 5 valid levers to the deduplication pool. Benefits all models — a structural resilience improvement. Makes the system tolerant of the kind of occasional schema violations that small models produce without manual prompt intervention.
- **Effort**: Medium — requires per-lever validation instead of batch validation: extract the raw lever list from the structured LLM response, validate each `Lever` individually, accumulate successes, skip failures (log them). Downstream code that consumes `DocumentDetails` must still work with a partial list.
- **Risk**: More complex validation path. If nearly all levers fail validation (e.g., parasomnia's `=>` pattern across all 7 levers), partial salvage returns 0 levers and still raises — so the failure mode is preserved for total failures. Edge: `DocumentDetails.levers` has `min_length=5` which must be reconciled with per-lever dropping.

### 3. Cherry-pick B1 step-gating fix into a standalone PR
- **Type**: Code fix / workflow
- **Evidence**: B1 (both agents). The fix at runner.py:517–519 correctly gates `partial_recovery` events to `identify_potential_levers`. Currently entangled with the regressive prompt changes in PR #354.
- **Impact**: Clean, correct event semantics. Without it, `identify_documents` 2-call successes would generate spurious `partial_recovery` events. The fix is confirmed working; it just needs to be isolated from the problematic prompt changes so it survives the revert.
- **Effort**: Low — a focused 3-line diff to runner.py:517–519 with no collateral changes.
- **Risk**: Near zero. The logic is verified and correct.

### 4. Add template-lock detection logging (I1) and degenerate review_lever detection (I2)
- **Type**: Code fix / observability
- **Evidence**: I1 and I2 (both agents). Currently there is no way to observe template lock rate from production logs without manual inspection of every lever file. The `=>` failure at run 59 was caught by the generic "too short" error message rather than an actionable diagnostic.
- **Impact**: Makes lock rate measurable in event logs without behavioral changes (I1 is a `logger.warning`, not a raise). I2 catches the `=>` / `->` degenerate pattern with a specific, actionable error that could trigger retry-prompt injection in the future. Both reduce the manual inspection burden for future iterations.
- **Effort**: Low — I1 is ~3 lines in `check_review_format`; I2 is ~4 lines with a regex check.
- **Risk**: Low. I1 does not raise. I2 raises on pure-punctuation values that are already failing the 10-char minimum check — it just improves the error message. Neither change alters successful output.

### 5. Fix B3: Expose MIN_LEVERS constant and make expected_calls dynamic
- **Type**: Code fix / maintenance
- **Evidence**: B3 (code_claude). `min_levers=15` in `identify_potential_levers.py:268` and `expected_calls=3` / `calls_succeeded < 3` in runner.py:519–523 are semantically coupled but physically disconnected literals. If `min_levers` changes (e.g., to 20 for better diversity), the runner threshold silently lags. The PR description claimed to remove the "stale constant" but only moved it inline.
- **Impact**: Prevents silent monitoring breakage when the lever count threshold changes. Low immediate impact (the literal hasn't changed), but the coupling is a maintenance trap. Define `MIN_LEVERS = 15` at module level in `identify_potential_levers.py` and import it in runner.py to replace the bare `3` threshold (since `ceil(MIN_LEVERS / 7)` ≈ 3 calls at 5–7 levers per call).
- **Effort**: Low-Medium — requires cross-file import and a formula comment linking the two values.
- **Risk**: Low. Purely mechanical refactor. The behavior is unchanged; only the source of truth for the threshold value is centralized.

## Recommendation

**Pursue Direction 1 first: revert the explicit prohibition and replace the game-dev example.**

This is the single highest-impact action because it directly restores the 100% success rate (2 plans recovered) and eliminates the hong_kong template lock regression that PR #354 introduced. Both agents agree, the evidence is strong, and the effort is minimal.

**Specific changes:**

**File: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`**

1. **Remove the explicit prohibition from section 5** (line 239):
   ```
   # Remove this line entirely:
   "   - NO starting review_lever with "The options", "These options", "The lever", or "These levers" as the grammatical subject — name a specific mechanism, constraint, or risk instead\n"
   ```
   Rationale: Naming the banned phrases in the prompt increases their probability mass for small models (S1). PR #353 achieved 0% "The options" lock without any prohibition — by changing example content. The prohibition adds no benefit for cloud models (which follow instructions reliably) and actively harms small models.

2. **Replace the game-dev review_lever example** (lines 229–231) with a non-gaming domain:
   The current game-dev example (`"Migrating the rendering pipeline to GPU compute cuts frame time…"`) overlaps with the `hong_kong_game` and `gta_game` test plans, giving llama3.1 a nearby template. Replace it with an example from a domain not represented in the 5 test plans — e.g., logistics/supply-chain or urban infrastructure:
   ```
   # Draft replacement example (verify no rhetorical overlap with the other two):
   "Rail freight and road trucking each carry fixed terminal costs that do not scale with load — splitting a shipment across both modes doubles terminal handling fees and may exceed the per-unit savings from modal optimisation."
   ```
   This uses a different adversarial structure (cost-splitting trap, not hidden-dimension cost) and avoids gaming, medical, and agricultural domains already covered.

3. **Verify the three resulting examples satisfy OPTIMIZE_INSTRUCTIONS requirements**:
   - No shared rhetorical skeleton across examples (S3 concern: ensure the replacement does not also follow the "apparent benefit → hidden cost" pattern).
   - None uses "The options"/"The lever" as grammatical subject.
   - Spans 3+ distinct domains.

**Why this before B2 (batch salvage):** B2 is a correct structural fix but is medium-effort and carries complexity risk. The prompt revert is low-effort and directly addresses the 94.3% regression. Once the success rate is restored to 100%, B2 should follow to make the system resilient to future schema edge cases.

**B1 (step-gating) handling:** Open a focused standalone PR with only the runner.py step-gate change before or in parallel with the revert. Do not lose this fix in the revert.

## Deferred Items

- **B2 (partial batch salvage)**: Correct and important, but medium-effort. Do after the prompt revert restores the baseline. The 10-char minimum on review_lever and the ≥3 options check are correct constraints; the granularity of rejection (lever vs. batch) is what needs fixing.
- **I1 (template-lock logging)**: Low-risk, useful observability. Bundle with B2 or the next iteration.
- **I2 (degenerate review_lever detection)**: Low-risk, actionable error message for `=>` artifacts. Bundle with B2.
- **B3 (MIN_LEVERS constant)**: Latent maintenance risk, not urgent. Can be done as a small housekeeping PR any time.
- **Haiku partial recoveries**: haiku has had 2 partial recoveries (hong_kong, parasomnia) for both PR #353 and PR #354 runs. The root cause is unresolved. Once B2 is implemented (per-lever salvage), investigate whether haiku's failures are on specific levers or entire calls, and whether output length is the trigger.
- **Per-call example diversity (OPTIMIZE_INSTRUCTIONS H2)**: The insight correctly observes that template lock re-forms independently per LLM call. The silo run 59 showed three distinct per-call formulaic patterns. A future experiment could test whether injecting a call-specific instruction suffix (e.g., "start your review with the lever's financial mechanism", "start with the institutional constraint", "start with the execution risk") diversifies review structure across calls more effectively than global example diversity.
- **I6 (English-only field descriptions)**: The `consequences` field description at lines 98–99 contains English keyword examples ("Controls ... vs.", "Weakness:"). Low priority since it's in a field description rather than the system prompt, but it should be cleaned up to use structural guidance for multilingual robustness.
