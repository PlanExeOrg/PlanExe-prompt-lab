# Synthesis

## Cross-Agent Agreement

Both insight_claude and code_claude agree on all major findings:

1. **PR #358: KEEP.** The "tension" opener lock is definitively eliminated for both haiku and llama3.1 (haiku: 75% → 0% in hong_kong_game; llama3.1: ~100% → ~0%). Haiku success rate improved +13.4pp (73.3% → 86.7%), overall +1.9pp (95.2% → 97.1%). No regressions on the five previously-clean models.

2. **Secondary template lock introduced.** The replacement field description phrase "state the specific gap the **three options** leave unaddressed" is now being echoed verbatim by haiku as "none of the three options address…" in ~85% of reviews (17/20 hong_kong_game run 93). Same mechanism as the original lock; different surface form.

3. **B1: `LeverCleaned.review` field description is stale.** Line 212 still says "names the core tension, then identifies a weakness the options miss" — exactly the wording the PR was meant to remove. No runtime impact (confirmed not serialized to LLM), but a copy-paste trap.

4. **I1/S1 is the top next action.** Both agents independently identify rewriting the `review_lever` field description to remove "three options" as grammatical subject as the highest-priority next change.

5. **`OPTIMIZE_INSTRUCTIONS` update is accurate and useful.** The new "Field-description template lock" and "Template-lock migration" entries correctly document the failure mode observed in this analysis.

## Cross-Agent Disagreements

There are no inter-agent disagreements — only one insight agent and one code review agent were run for this analysis. Source code verification confirms all code-level claims:

- **S1 confirmed**: `identify_potential_levers.py:120` reads `"three options leave unaddressed"` — the exact phrase echoed in haiku output.
- **S2 confirmed**: `runner.py:120` and `runner.py:517–523` both fire `partial_recovery` for `calls_succeeded < 3` regardless of whether the shortfall was caused by a validation failure or by step-gate early exit (healthy over-generation).
- **S3/S4 confirmed**: `runner.py:190–222` shows the shared `dispatcher` singleton with no thread isolation for event delivery, and the `finally` block calls `.remove()` without guarding against `ValueError`.
- **B2 confirmed**: `identify_potential_levers.py:143` says "Run 82 (llama, gta_game)" but per the model mapping, run 82 is `openai-gpt-5-nano`, not llama.

## Top 5 Directions

### 1. Rewrite `review_lever` field description to eliminate "three options" as grammatical subject
- **Type**: prompt change (field description)
- **Evidence**: S1 (code_claude), H1 (insight_claude). Confirmed: haiku run 93 echoes "none of the three options address…" in 85% of hong_kong_game reviews and ~50% of silo reviews. The trigger is `identify_potential_levers.py:120` — "state the specific gap the **three options** leave unaddressed" — which makes "the three options" the grammatical subject of the review's second clause. This is the same template-lock mechanism documented in OPTIMIZE_INSTRUCTIONS lines 86–92.
- **Impact**: haiku (confirmed); likely any small model (llama3.1, gpt-5-nano) that runs this step. Affects content quality of 100% of generated reviews for affected models. More impactful than fixing a single failed call because it degrades 34/35 successful plans.
- **Effort**: low — targeted single-field rewrite, ~2 lines
- **Risk**: minimal. The fix preserves the intent (identify the gap) while removing the structural cue. OPTIMIZE_INSTRUCTIONS already provides the precise guidance needed for the new wording. The examples in Section 4 are unchanged and remain grounding.

**Draft wording** (for `identify_potential_levers.py:116–124`):
```python
review_lever: str = Field(
    description=(
        "A short critical review: identify the primary trade-off "
        "this lever introduces, then name a real-world constraint "
        "or risk that all three strategies collectively sidestep — "
        "expressed in terms specific to this project's domain. "
        "See system prompt section 4 for examples. "
        "Do not use square brackets or placeholder text."
    )
)
```
This replaces "state the specific gap the three options leave unaddressed" with "name a real-world constraint or risk that all three strategies collectively sidestep — expressed in terms specific to this project's domain." The subject is now a domain-specific constraint, not the options themselves.

Also update Section 4 header in the system prompt (`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT:236`) to match:
> "A short critical review — identify the primary trade-off this lever introduces, then name a real-world constraint or risk that all three strategies collectively sidestep."

### 2. Update `LeverCleaned.review` field description (code hygiene)
- **Type**: code fix (documentation only)
- **Evidence**: B1 (code_claude), Negative #5 (insight_claude). Confirmed at `identify_potential_levers.py:212`.
- **Impact**: no runtime effect, but removes a copy-paste trap. Any future maintainer who promotes `LeverCleaned` into a prompt-facing context or adds a new field by referencing existing descriptions will reproduce the "core tension" lock.
- **Effort**: trivial — one-line description change
- **Risk**: none

**Draft fix** (`identify_potential_levers.py:211–213`):
```python
review: str = Field(
    description=(
        "A short critical review: identifies the primary trade-off this lever "
        "introduces and a real-world constraint that all three strategies collectively sidestep."
    )
)
```

### 3. Add a structurally distinct fourth example to Section 4
- **Type**: prompt change (examples)
- **Evidence**: I4 (code_claude), H2 (insight_claude). Two of the three current examples use the "X, **but** Y" adversative connector; one uses "so" (cause-effect). The X-but-Y structure maps naturally to "All three options do X, but none address Y" — a pattern already appearing in haiku output alongside the field description cue.
- **Impact**: medium. Adding a conditional or sequential example ("If X occurs, Y follows; however Z applies throughout") gives weaker models a non-adversative pattern to draw from. This is a defense-in-depth against template-lock migration for the next iteration.
- **Effort**: low — add one ~30–50 word example to Section 4
- **Risk**: low. A fourth example increases token count slightly; the diversity benefit outweighs the cost. The "Template-lock migration" entry in OPTIMIZE_INSTRUCTIONS already warns that all examples must span distinct domains with distinct rhetorical structures.

### 4. Differentiate `partial_recovery` from step-gate early exit in runner.py
- **Type**: code fix (event taxonomy)
- **Evidence**: S2, I2 (code_claude), Negative #3 (insight_claude). Confirmed at `runner.py:120` and `runner.py:517–523`. `partial_recovery` fires whenever `calls_succeeded < 3`, including when the step-gate exits early because `len(generated_lever_names) >= min_levers` (healthy over-generation). Analysis metrics then conflate genuine call failures with normal behavior.
- **Impact**: medium for analysis quality. The insight file already notes this ambiguity ("partial_recovery events are step-gate loop-exits, not schema failures"). A separate `early_exit` event type would make future optimization runs more interpretable and prevent false alarms.
- **Effort**: medium — requires adding a `stop_reason` field to `IdentifyPotentialLevers` result or checking lever count against `min_levers` in the runner; updating the event emission logic in `runner.py:517–524` and any downstream analysis scripts.
- **Risk**: low runtime risk; medium analysis risk if existing scripts rely on `partial_recovery` semantics and are not updated.

### 5. Fix `dispatcher.event_handlers.remove` in `finally` block
- **Type**: code fix (exception safety)
- **Evidence**: S4 (code_claude). Confirmed at `runner.py:220–222`. If `add_event_handler` fails, the `finally` block calls `.remove()` on a list that does not contain the element, raising `ValueError` that replaces the original exception in the call stack.
- **Impact**: low frequency (setup failures are rare) but high debuggability cost — a `ValueError` masking the real error makes diagnosis much harder. Fix: wrap the `.remove()` call in `try/except ValueError` or check membership first.
- **Effort**: trivial — 3-line guard
- **Risk**: none

## Recommendation

**Do Direction 1 first: rewrite the `review_lever` field description to remove "three options" as grammatical subject.**

**Why first:** It is the only change that addresses an active, confirmed content quality regression affecting ~85% of haiku reviews and likely other small models. All other directions are either code hygiene (B1, B2, S4), analysis tooling (S2/I2), or defensive hardening (I4). Direction 1 fixes the same class of problem that PR #358 fixed — a field-description structural cue that causes template lock — and the OPTIMIZE_INSTRUCTIONS guidance (lines 73–82 and 86–92) provides a precise recipe for what the new wording must avoid.

**What to change:**

1. **`identify_potential_levers.py:116–124`** — `Lever.review_lever` field description:

   Replace:
   ```
   "A short critical review: identify the primary trade-off "
   "this lever introduces, then state the specific gap the "
   "three options leave unaddressed. "
   ```
   With:
   ```
   "A short critical review: identify the primary trade-off "
   "this lever introduces, then name a real-world constraint "
   "or risk that all three strategies collectively sidestep — "
   "expressed in terms specific to this project's domain. "
   ```

2. **`identify_potential_levers.py:236`** — Section 4 header in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`:

   Replace:
   ```
   A short critical review — identify the primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed.
   ```
   With:
   ```
   A short critical review — identify the primary trade-off this lever introduces, then name a real-world constraint or risk that all three strategies collectively sidestep, expressed in domain-specific terms.
   ```

3. **`identify_potential_levers.py:212`** — `LeverCleaned.review` field description (B1, bundle with the above):

   Replace `"A short critical review — names the core tension, then identifies a weakness the options miss."` with the updated wording matching the new `Lever.review_lever` description.

Bundling B1 with Direction 1 is low effort and closes the code hygiene gap in the same PR.

The expected outcome: "none of the three options address…" lock rate drops from 85% toward 0% for haiku, mirroring the "tension" opener fix in PR #358. If template-lock migration occurs again (per OPTIMIZE_INSTRUCTIONS warning), the next iteration will address the new subphrase; but the new wording ("real-world constraint or risk … expressed in domain-specific terms") is substantially harder to mirror verbatim than "the three options leave unaddressed."

## Deferred Items

- **I4 (fourth example)**: Useful defense-in-depth but not needed until after Direction 1 is evaluated. Add in the following iteration if the "all three strategies collectively" subphrase triggers a new lock.
- **S2/I2 (partial_recovery vs. early_exit)**: Correct but low urgency — the current conflation is well-understood and annotated in the insight notes. Implement when the analysis tooling needs to distinguish these cases programmatically.
- **B2 (stale run number in docstring)**: Trivial to fix but no operational impact. Bundle with any future housekeeping PR.
- **S3 (shared dispatcher thread isolation)**: Low frequency bug, not observed to cause incorrect outputs in current runs. Investigate if cross-plan event contamination is suspected in a specific failure; otherwise defer.
- **S4 (dispatcher.remove ValueError masking)**: Fix opportunistically when touching `runner.py` for another reason. 3-line guard, no urgency.
- **Review length still 2.5–4× above baseline (haiku)**: The "one sentence (20–40 words)" constraint is partially effective. Further tightening the upper bound (e.g., 30 words) could help, but should be deferred until the template-lock migration is resolved, since the template lock is the more fundamental quality issue.
