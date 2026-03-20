# Synthesis

## Cross-Agent Agreement

Only one agent pair was produced for this analysis (insight_claude + code_claude). Both converge on the same conclusions:

- **PR #372 verdict: KEEP.** The simplification from 4-way (`keep/absorb/remove`) to 3-way (`primary/secondary/remove`) taxonomy is well-implemented and measurably improves output quality. All 35 runs (7 models × 5 plans) succeeded. All `remove` decisions correctly cite the absorbing lever UUID. The degenerate llama3.1 catch-all collapse into Risk Framing is eliminated. Haiku's remove rate improved from 28% to 39%.
- **Primary remaining quality problem**: template-lock in the `secondary` definition (B3) and the contradictory `primary` fallback instruction (B2) together explain llama3.1's 0-removes / 16-secondary pattern on sovereign_identity (N1, N4).
- **Hierarchy direction inconsistency** (N2) is pre-existing and not caused by this PR — it's a prompt-quality gap with no code root cause.

---

## Cross-Agent Disagreements

None. Only one agent set. All findings were independently verified against source code:

- **B1 confirmed**: `runner.py:125` — `if actual_calls < 3` fires on normal 2-call runs. `runner.py:546–552` emits `partial_recovery` for the same condition. The inline comment at line 122 explicitly says 2-call success is normal for high-yield models.
- **B2 confirmed**: `deduplicate_levers.py:102` — "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role, classify it as primary so a potentially important lever is not lost." The contradiction (avoid it / use it as fallback) is verbatim in the source.
- **B3 confirmed**: `deduplicate_levers.py:91` — The `secondary` definition contains the complete reusable phrase "distinct and useful but supporting or operational — matters for delivery but not a top-level strategic choice." This phrase is short, domain-neutral, and memorizable, making it a template-lock target.
- **S1 confirmed**: `deduplicate_levers.py:106` — "In a well-formed set of 15 levers, expect 4–10 to be removed." The generate step sets `min_levers=15` but can return 15–20; for 18 levers the range underestimates and the upper bound (10) may act as a stopping signal.
- **S4 confirmed**: `LeverClassification` enum (lines 22–25) is only used in `keep_classifications` (line 250); `LeverClassificationDecision` and `LeverDecision` use `Literal["primary", "secondary", "remove"]` separately.

---

## Top 5 Directions

### 1. Fix template-lock in the `secondary` definition phrase
- **Type**: prompt change
- **Evidence**: B3 (code_claude), N1/N4 (insight_claude). Root cause confirmed in `deduplicate_levers.py:91`. The phrase "distinct and useful but supporting or operational" is reusable across any domain, short enough to memorize, and appears verbatim in all 14 of llama3.1's secondary justifications on sovereign_identity (run 50). Because the model cannot articulate why levers differ, it also cannot decide to `remove` any — suppressing deduplication entirely.
- **Impact**: Fixes 0-remove pattern for weak models on plans with many levers. Affects all models to some degree — any model that satisfies the description field verbatim instead of reasoning from the lever content. Downstream steps (EnrichLevers, FocusOnVitalFew) receive a better-filtered set.
- **Effort**: Low — prompt text change only in `DEDUPLICATE_SYSTEM_PROMPT`. No schema or code changes.
- **Risk**: Rewriting the definition could introduce a different template phrase if not carefully worded. The fix must describe a *test* for classification rather than a *description* of the class (per OPTIMIZE_INSTRUCTIONS lines 86–92 in `identify_potential_levers.py`).

**Proposed fix** — replace `deduplicate_levers.py:91` (the `secondary` bullet):
```
# current
- secondary: Lever is distinct and useful but supporting or operational — matters for
  delivery but not a top-level strategic choice (e.g., marketing campaign timing, internal
  reporting cadence, team communication tooling, documentation formatting standards).

# replacement
- secondary: Lever addresses a real project concern but does not gate the project's
  core outcome. Ask: "If this lever were ignored entirely, would the project fail or
  succeed in a fundamentally different way?" If no, it is secondary. Name the specific
  concern it addresses in your justification — do not reuse this definition as your
  justification text.
```

---

### 2. Fix contradictory `primary` fallback instruction
- **Type**: prompt change
- **Evidence**: B2 (code_claude). Confirmed in `deduplicate_levers.py:102`. Directly linked to N1/N4 (llama3.1 over-demoting to secondary, 2 primary on sovereign_identity where haiku assigns 9 primary).
- **Impact**: Removes the "last resort" signal that tells weaker models to avoid `primary`. Corrects the intended behavior: when uncertain between keeping and removing, keep the lever; when keeping, prefer `primary` over `secondary` if the lever is high-stakes. Affects all models but most visibly the weaker ones.
- **Effort**: Low — one sentence replacement.
- **Risk**: Low. The new wording is unambiguous. The two-sentence structure (uncertain→keep as primary; uncertain→prefer secondary over remove) covers both cases without contradiction.

**Proposed fix** — replace `deduplicate_levers.py:102`:
```
# current (contradictory)
Use "primary" only as a last resort — if you genuinely cannot determine a lever's
strategic role, classify it as primary so a potentially important lever is not lost.

# replacement
When uncertain between primary and secondary, prefer primary — a false positive
is recoverable downstream. When uncertain between removing and keeping, prefer
secondary over remove to avoid discarding a potentially important lever.
```

---

### 3. Document template-lock failure mode in `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS`
- **Type**: prompt change (documentation only, not injected into LLM)
- **Evidence**: I6 (code_claude). `identify_potential_levers.py` documents template-lock at lines 69–92. `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS` (lines 111–125) lists 5 failure modes and omits it. B3 is a template-lock instance that the current list does not cover.
- **Impact**: Ensures the self-improve loop recognizes and tracks this failure mode in future iterations. Prevents a future optimizer from re-introducing the problematic phrase.
- **Effort**: Very low — append one item to the existing `OPTIMIZE_INSTRUCTIONS` list.
- **Risk**: None. The OPTIMIZE_INSTRUCTIONS block is not injected into the LLM.

**Proposed addition** — append to `deduplicate_levers.py`'s `OPTIMIZE_INSTRUCTIONS` after item 5:
```
6. Definition mirroring: Weak models copy the classification definition verbatim
   into every justification of that class (e.g. "distinct and useful but supporting
   or operational"), producing content-free boilerplate. The model loses the ability
   to distinguish levers from each other, which also suppresses remove decisions.
   Fix: avoid complete reusable phrases in classification definitions; describe the
   *test* for each class (a conditional question) rather than its dictionary meaning.
   Each justification should name the specific lever and why it is distinct.
```

---

### 4. Update remove-calibration guidance to be input-size-aware
- **Type**: prompt change
- **Evidence**: S1 (code_claude). Confirmed in `deduplicate_levers.py:106`. The generate step (`min_levers=15`, `max_calls=5`) regularly produces 15–20 levers. For 18-lever inputs the upper bound of 10 is only 56% removal — conservative for a set that likely contains more near-duplicates than a 15-lever set.
- **Impact**: Prevents compliant models from stopping deduplication early when the upper bound is reached on larger inputs. Low-impact for strong models (gemini, haiku) that already remove aggressively; higher-impact for conservative models (gpt-4o-mini, 17% remove rate).
- **Effort**: Low — change the static calibration sentence to a proportional framing, or inject the actual input count at runtime.
- **Risk**: Low. Could slightly increase remove rates for conservative models; downstream FocusOnVitalFewLevers can compensate. The simpler static approach (widening the range to "4–10 or more") avoids runtime injection complexity.

**Proposed fix** — replace `deduplicate_levers.py:106`:
```
# current
In a well-formed set of 15 levers, expect 4–10 to be removed.

# replacement
Expect to remove 25–50% of the input levers. For 15 levers, that is 4–8 removals;
for 18–20 levers, 5–10 removals. Plans with many near-duplicate names may require
more — do not stop early. If you find zero remove decisions, reconsider: the input
almost always contains near-duplicates.
```

---

### 5. Fix false `partial_recovery` events in `runner.py`
- **Type**: code fix
- **Evidence**: B1 (code_claude). Confirmed in `runner.py:125` and `runner.py:546–552`. The inline comment at line 122 explicitly says 2-call success is normal, but the threshold fires for it.
- **Impact**: Eliminates false alarms in `events.jsonl` for any model that generates 8+ levers per call. Does not affect output quality. Makes event monitoring trustworthy so genuine partial recoveries (1-call successes) are distinguishable from normal 2-call runs.
- **Effort**: Low — change one threshold value in two places, or replace the call-count check with a lever-count check.
- **Risk**: Low. The only risk is setting the threshold too aggressively; `< 2` (warn only on exactly 1 successful call) is the conservative safe choice.

**Proposed fix** — `runner.py`:
```python
# line 125: change
if actual_calls < 3:
# to
if actual_calls < 2:

# lines 547–548: change
and pr.calls_succeeded < 3):
# to
and pr.calls_succeeded < 2):
```

---

## Recommendation

**Fix B3 first: rewrite the `secondary` definition to eliminate template-lock.**

**File**: `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
**Line**: 91 (the `secondary` bullet in `DEDUPLICATE_SYSTEM_PROMPT`)

**Why first:**
- B3 is the single root cause that explains both N1 (0 removes on sovereign_identity) and N4 (over-demoting to secondary). B2 contributes, but B3 is upstream: a model that template-locks on the secondary definition cannot produce lever-specific reasoning in any justification, so even fixing B2's "last resort" wording would not help — the model still cannot distinguish the levers from each other, so it cannot decide to remove any.
- The fix is prompt-only, no schema or code changes, low regression risk.
- It aligns with the documented OPTIMIZE_INSTRUCTIONS principle (lines 86–92 in `identify_potential_levers.py`) of describing the *test* rather than the *description* — the same fix that worked for `review_lever` field descriptions applies here.
- It affects the quality of justifications across all models (not just llama3.1): even stronger models benefit from sharper per-class tests rather than memorizable dictionary definitions.

**Exact change** — `deduplicate_levers.py:91`:
```
# Remove:
- secondary: Lever is distinct and useful but supporting or operational — matters for
  delivery but not a top-level strategic choice (e.g., marketing campaign timing, internal
  reporting cadence, team communication tooling, documentation formatting standards).

# Replace with:
- secondary: Lever addresses a real project concern but does not gate the project's core
  outcome. Ask: "If this lever were ignored entirely, would the project fail or succeed in
  a fundamentally different way?" If the answer is no, it is secondary. Name the specific
  concern it addresses in your justification — do not reuse this definition text verbatim.
```

Also fix B2 in the same PR (one additional sentence change, zero risk, addresses the companion driver of the same failure). Together these constitute a minimal, contained prompt PR with a clear hypothesis: "fixing the template-lock trigger and the contradictory fallback instruction will raise llama3.1's remove rate on sovereign_identity from 0 toward the 3–5 expected, and reduce boilerplate secondary justifications across all models."

---

## Deferred Items

- **I2/C2 — Chain-removal detector**: Useful defensive code (detect A→B→C chains and A→B, B→A circular references), but all 35 after-runs show no chains in practice. Implement after the prompt quality is stable.
- **S5 — UUID validation in `remove` justifications**: All models in runs 50–56 complied without it. Add a regex check once the prompt changes are stable and there is evidence of regression.
- **S4 — Consolidate `LeverClassification` enum with `Literal` types**: Maintenance cleanup, zero user impact. Defer to a refactor pass.
- **I1/C1 — Classification summary counts in output metadata**: Useful for monitoring (catches 0-remove runs immediately), but low priority once the prompt fixes reduce the frequency of that failure mode.
- **S2 — `options` validator: enforce ≤3 as well as ≥3**: Minor schema consistency improvement; does not affect current failures.
- **S3 — Raise `review_lever` minimum length from 10 to 40 characters**: Low risk improvement for `identify_potential_levers.py`; not related to the current step's issues.
- **Q4 (insight) — Provide source lever names upstream to help resolve near-synonyms**: Architectural change (plumbing source context from identify step into deduplicate step). Worth a separate investigation after the prompt fixes land.
