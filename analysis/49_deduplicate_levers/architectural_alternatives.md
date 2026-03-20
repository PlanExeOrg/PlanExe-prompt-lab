# Architectural Alternatives for deduplicate_levers

**Date**: 2026-03-20

The 3-way taxonomy (primary/secondary/remove) is validated. The remaining
quality problems (hierarchy-direction errors, template-lock, conservative
models) are not taxonomy issues — they stem from the per-lever sequential
classification architecture.

---

## Current Architecture: Per-Lever Sequential

For each of the 18 input levers, one LLM call is made. The model sees:
- System message: full system prompt + project context + summary of all 18 levers (truncated to 120 chars each)
- Prior decisions: compacted list of classifications made so far
- User message: the full JSON of the current lever

**Problems:**

1. **Position bias.** Lever 1 is classified with zero prior decisions. Lever 18
   is classified with 17 prior decisions in context. Early levers get different
   treatment than late levers.

2. **No global view.** When classifying lever 5, the model doesn't know what
   it will decide about levers 6-18. It can't make globally optimal grouping
   decisions. This is the root cause of hierarchy-direction errors — the model
   picks a direction for lever 5 without seeing that lever 12 would have been
   the better absorb target.

3. **18 calls per plan.** Each call has growing context (prior decisions).
   For 7 models × 5 plans = 35 runs × 18 calls = 630 LLM calls per iteration.
   Expensive, slow, and 630 chances for failure/retry.

4. **Context truncation.** The all-levers summary truncates consequences at
   120 chars. For levers with similar names but different scopes, the
   distinguishing detail is lost. The full lever is only available for the
   lever currently being classified, not for comparison targets.

---

## Alternative A: Single-Call Batch Classification

Give all 18 levers in one call. Get back one structured response with all
18 classifications.

```
Input:  [lever_1, lever_2, ..., lever_18]
Output: [{lever_id, classification, justification}, × 18]
```

**Advantages:**
- Model sees all levers simultaneously — can make globally consistent decisions
- One call instead of 18 (faster, cheaper)
- No position bias from sequential context accumulation
- No context truncation — all levers are fully present
- This is how `enrich_potential_levers` already works (batched)

**Disadvantages:**
- All-or-nothing: if the call fails, no partial results
- Output schema is larger (18 items), some models may struggle with structured
  output at this size
- Harder to retry a single lever's classification

**Mitigation:** Use the existing retry/fallback mechanism. If the batch call
fails, fall back to per-lever sequential as a degraded mode.

**Effort:** Medium. Restructure `DeduplicateLevers.execute()` to build one
prompt with all levers, use a batch output schema (list of 18 decisions),
parse the response. Keep the per-lever fallback path.

---

## Alternative B: Two-Phase (Cluster → Classify)

Separate "which levers overlap?" from "which to keep?"

**Phase 1 — Cluster:** One LLM call. Input: all 18 levers. Output: groups
of overlapping levers (e.g., group 1: [lever_3, lever_7, lever_15], group 2:
[lever_1], group 3: [lever_2, lever_9], ...). No keep/remove decision yet.

**Phase 2 — Classify:** For each group with >1 lever, pick the most general
representative. Tag every surviving lever as primary or secondary.

```
Phase 1 input:  [all 18 levers]
Phase 1 output: [[3,7,15], [1], [2,9], ...]  (clusters)

Phase 2 input:  cluster [3,7,15] with full lever details
Phase 2 output: keep lever_3 (primary), remove lever_7, remove lever_15
```

**Advantages:**
- Cleanly separates two cognitive tasks that the current prompt conflates
- Phase 1 (clustering) is easier for models than simultaneous clustering + classification
- Phase 2 can focus purely on quality within each cluster
- Hierarchy-direction errors should decrease because the model compares
  only the 2-3 levers in a cluster, not all 18

**Disadvantages:**
- Two LLM calls minimum (one for clustering, one or more for classification)
- More complex orchestration code
- If clustering is wrong, classification inherits the error

**Effort:** High. New schema for cluster output, new orchestration logic,
phase 2 may need one call per cluster or one batched call.

---

## Alternative C: Score and Threshold

Replace categorical classification with numeric scoring.

```
Input:  [all 18 levers]
Output: [{lever_id, importance_score (1-10), justification}, × 18]
```

Keep levers scoring above a threshold (e.g., ≥5). Optionally tag top-N as
primary, rest as secondary.

**Advantages:**
- Models are often better at relative ranking than categorical classification
- No absorb/remove ambiguity — it's just a score
- Duplicate levers naturally get lower scores ("this is redundant with lever X,
  score: 2")
- Threshold is tunable without changing the prompt

**Disadvantages:**
- Score calibration varies by model (gpt-5-nano might score everything 3-7,
  llama might score everything 6-9)
- Loses the explicit "this lever merges into lever X" relationship
- Threshold tuning adds a parameter to manage

**Effort:** Medium. New output schema (score instead of classification),
threshold logic, potentially normalize scores per-model.

---

## Alternative D: Single-Call with Anti-Template-Lock

Keep the current 3-way taxonomy but move to a single call with explicit
anti-template-lock instructions.

This is the minimal change: same taxonomy, same output schema, but restructured
as one call instead of 18.

```
Input:  all 18 levers (full JSON, not truncated)
Output: [{lever_id, classification, justification}, × 18]

Prompt addition:
"Each justification must name the specific lever and explain what makes it
 distinct from (or redundant with) other levers. Do not repeat the
 classification definition as your justification."
```

**Advantages:**
- Minimal code change (one call instead of 18, same schema)
- Directly addresses B3 (template-lock) and position bias simultaneously
- Compatible with existing downstream consumers (same output format)
- Easy to compare against current approach (same metrics)

**Disadvantages:**
- Still all-or-nothing on failure
- May hit output token limits for some models (18 × ~80 word justifications
  = ~1400 words of structured output)

**Effort:** Low-medium. Restructure the execute loop, adjust the prompt,
keep the output schema identical.

---

## Recommendation

**Start with Alternative D** (single-call, same taxonomy). It's the lowest-risk
change that addresses the most problems:

- Eliminates position bias (no sequential accumulation)
- Enables global consistency (model sees all levers at once)
- Reduces cost from 18 calls to 1
- No schema change — downstream consumers unaffected
- Can be A/B tested against the current per-lever approach in one iteration

If Alternative D shows that models struggle with 18-item batch output, fall
back to Alternative A with a batch size of 6-9 (two calls instead of 18).

Alternative B (cluster → classify) is the most architecturally clean solution
but requires the most implementation work. Worth exploring after D proves
the single-call approach works.

Alternative C (scoring) is interesting but changes the output contract.
Better suited as a separate experiment.
