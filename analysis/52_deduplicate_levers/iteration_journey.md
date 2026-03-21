# Iteration Journey: deduplicate_levers (iter 44-52)

**Date**: 2026-03-21

Nine iterations across five PRs to get from the baseline to the current
state. This documents what was tried, what worked, what failed, and why.

---

## The Baseline (iter 48, main)

- **Architecture**: 18 sequential LLM calls, one per lever
- **Taxonomy**: keep / absorb / remove
- **Avg kept**: 13.9 / 18
- **Avg duration**: 120.5s per plan
- **Known failures**: llama3.1 collapsed 7 unrelated levers into "Risk Framing"

The baseline worked but had structural problems: position bias (lever 1
classified differently than lever 18), no global view (model can't compare
all levers simultaneously), and no prioritization signal downstream.

---

## What Was Tried

### Iter 45 — PR #365: 4-way taxonomy (primary/secondary/absorb/remove)

**Hypothesis**: Adding primary/secondary distinction to the existing
absorb/remove system would give richer output.

**Result**: YES verdict. Won 5/7 models vs baseline. Primary/secondary
triage was the real quality gain. But `remove` was dead — models never
used it when `absorb` existed. The 4th category added complexity without
value. Still 18 sequential calls.

**Lesson**: The triage signal matters. The absorb/remove distinction
doesn't (absorb-info isn't consumed downstream).

### Iter 49 — PR #372: 3-way taxonomy (primary/secondary/remove)

**Hypothesis**: Merging absorb into remove (3 categories instead of 4)
would exercise all categories more consistently.

**Result**: YES verdict. All 3 categories exercised (58% primary, 27%
secondary, 15% remove). llama3.1 collapse eliminated. But still 18
sequential calls. Template-lock identified as remaining issue (llama3.1
copies "distinct and useful but supporting" verbatim into all
justifications).

**Lesson**: Fewer categories = more consistent exercise. But the per-lever
sequential architecture was the real bottleneck.

### Iter 50 — PR #373: Likert scoring (-2 to +2), single batch call

**Hypothesis**: Replace categorical classification with numeric scoring
in a single call. Models are better at relative ranking than categorical
classification. 18 calls → 1 call.

**Result**: REVERT verdict. Two catastrophic failures:
1. Relevance ≠ deduplication. The prompt asked "how relevant?" not "is
   this redundant?" Capable models scored overlapping levers as relevant
   and kept them all. 0% removal rate for most models.
2. llama3.1 inverted the Likert scale. Scored 17/18 levers as -2 while
   writing "highly relevant" in justifications. Only 1 lever survived.

**Lesson**: Integers have polarity that can be inverted. Categorical
labels cannot. "Relevance" and "deduplication" are different questions —
a lever can be highly relevant AND redundant. The batch architecture
worked perfectly (35/35 success); the scoring schema was the problem.

### Iter 51 — PR #374: batch call + categorical taxonomy

**Hypothesis**: Keep the batch architecture from PR #373, restore the
categorical taxonomy from PR #372.

**Result**: YES verdict. Deduplication restored (6-33% removal for
capable models). llama3.1 scale inversion eliminated (categorical labels
can't be inverted). Speed preserved (1 call). llama3.1 timed out on
2/5 plans but fell back safely to all-secondary.

**Lesson**: The batch + categorical combination works. Remaining issue
was llama3.1 timeouts (120s not enough for 18 levers in one call).

### Iter 52 — PR #375: refinements (shorter justifications, broader remove)

**Hypothesis**: Shorter justifications (~20-30 words instead of ~40-80)
would let llama3.1 finish within timeout. Broadening `remove` to include
irrelevant levers would improve dedup quality.

**Result**: YES verdict. llama3.1 timeouts eliminated (2/5 → 0/5).
API model justifications 55% shorter. Avg duration 25% faster. Merged.

**Lesson**: Output length directly affects whether slow models can
complete within timeout. Advisory length constraints in Pydantic field
descriptions work for API models but are fragile for local models
(~5s margin on silo).

---

## What Actually Moved the Needle

Looking back across all iterations, three changes mattered:

### 1. Single batch call (iter 50-52)

The biggest architectural improvement. Going from 18 sequential calls to
1 batch call:
- 3x faster overall (120.5s → 40.3s avg)
- No position bias
- Global consistency (model sees all levers at once)
- Simpler code (190 lines vs 330)

This was the change that required the most iteration to get right. The
first attempt (Likert scoring) failed because relevance ≠ deduplication.
The fix was obvious in hindsight: keep the batch architecture, restore
the categorical taxonomy.

### 2. Primary/secondary triage (iter 45+)

Added genuinely new information for downstream steps. Main branch only
had `keep` — FocusOnVitalFewLevers had to re-evaluate every lever from
scratch. Now it gets a pre-classification (54% primary, 31% secondary)
to work with.

### 3. Shorter justifications (iter 52)

A small change with outsized impact: llama3.1 went from timing out on
2/5 plans to completing all 5. The API models also benefited (~55%
shorter output, ~25% faster).

---

## What Didn't Move the Needle

### Taxonomy label changes

Renaming categories (keep→primary, absorb→remove, etc.) across iterations
45-49 produced nearly identical results. The labels are interchangeable —
models don't care whether the category is called "keep" or "primary."
The actual behavior depends on the prompt framing and the model's
understanding of the task, not the label text.

### Anti-template-lock instructions

"Do not reuse the score definition as your justification" was added and
removed across iterations. With integer scores or short categorical
labels, template-lock isn't a problem. It was a real issue 8 months ago
with verbose text definitions — no longer relevant.

### Calibration hints

"Expect 4-10 removals from 15 levers" vs "Expect to remove 25-50%" vs
no calibration hint. Models that remove aggressively do so regardless of
the hint. Models that are conservative (gpt-4o-mini, llama3.1) ignore
it. The hint has minimal effect on actual behavior.

---

## Final State (iter 52, PR #375, merged)

| Metric | Baseline (iter 48) | Final (iter 52) |
|--------|-------------------|-----------------|
| Architecture | 18 sequential calls | 1 batch call |
| Taxonomy | keep/absorb/remove | primary/secondary/remove |
| Triage signal | None | primary (54%) / secondary (31%) |
| Avg kept | 13.9 / 18 | 15.6 / 18 |
| Avg removed | 4.1 / 18 (23%) | 2.4 / 18 (15%) |
| Avg duration | 120.5s | 40.3s |
| Speed improvement | — | 3.0x |
| llama3.1 failures | Collapse into "Risk Framing" | None (completes all plans) |
| Code size | ~330 lines | ~190 lines |

---

## Open Issues (for future iterations)

1. **llama3.1 dedup quality**: Completes all plans but produces 0 removes
   on silo and sovereign_identity. Model limitation, not a code bug.
   The timeout margin on silo is ~5s — fragile.

2. **Observability**: Silent failure masking (timeout → status=ok),
   calls_succeeded hardcoded to 1, no fallback events in events.jsonl.
   Follow-up work, not a blocker.

3. **OPTIMIZE_INSTRUCTIONS documentation debt**: Still says "keep the
   more general lever" but the prompt now says "keep the strategically
   better one." Should be updated.

4. **qwen3 justification swap**: Swaps justification text between two
   remove-classified levers. Pre-existing, newly observable because qwen3
   now removes multiple levers per plan.
