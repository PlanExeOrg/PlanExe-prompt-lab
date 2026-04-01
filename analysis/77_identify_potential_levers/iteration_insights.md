# Iteration Insights: identify_potential_levers (analyses 69–77)

Nine iterations attempted to beat the current best (analysis 40, PR #358). None were convincingly better. Here's the full picture.

## Iteration comparison

| Analysis | PR | Key change | Template lock | Fabricated numbers | Success rate | Verdict | Mergeable? |
|----------|-----|-----------|--------------|-------------------|-------------|---------|-----------|
| **40 (baseline)** | #358 | — | haiku 85% | 23 total | 100% (35/35) | — | **current best** |
| 69 | #471 | Positive framing only | unchanged | unchanged | 91.4% (gpt-oss-20b 0/5 timeout) | YES | No — gpt-oss-20b broken |
| 70 | #473 | + reduced word counts | unchanged | 4x worse (HKD 5->20) | 94% | CONDITIONAL | No — fabrication regression |
| 71 | #475 | + "Never invent" | unchanged | 4x worse | 91.4% | CONDITIONAL | No — fabrication worse |
| 72 | #477 | Ban all numbers | improved ~0% | -48% (23->12) | 91.4% | CONDITIONAL | Close — too restrictive |
| 73 | #478 | Verbatim numbers (consequences only) | unchanged | unchanged | 97.1% | CONDITIONAL | Close — wrong field |
| 74 | #479 | + template-lock fix + verbatim everywhere | qwen3 0->7/20 new lock | gpt-oss-20b 0->5 | 100% | CONDITIONAL | No — new lock + fabrication |
| 75 | #481 | Verbatim numbers only (tiny) | unchanged | marginal | 98.1% | CONDITIONAL | Close — marginal |
| **76** | **#482** | **#479 + minimal review_lever** | **ALL THREE FIXED (0%)** | haiku +8.3pp | 100%* | CONDITIONAL | **Closest to mergeable** |
| 77 | #483 | Stripped to word limits + anti-parrot | stays broken (0%) | haiku -37% | 88.6% (4 timeouts) | CONDITIONAL | No — stripped too far |

## PR #482 vs baseline (analysis 40): honest comparison

### Better than baseline
- **Template lock: 85% -> 0%** — the #1 issue from analysis 40, fully resolved across all three affected models (haiku, qwen3-30b, gpt-oss-20b). This was the dominant content quality problem in the pipeline step.
- **Review diversity** — haiku produces domain-specific varied reviews instead of monotonous "All three options X, but none Y" pattern.
- **Review length** — haiku 2.06x -> 1.82x baseline (dropped below 2x warning threshold).

### Worse than baseline
- **Haiku fabricated numbers: 22.6% -> 30.9%** (+8.3pp). The section 5 prohibition change ("NO calculated, derived, or estimated figures") likely activated number-generation attention in haiku rather than suppressing it.
- **llama3.1 call-2+ consequence parroting** — 7/7 levers in silo plan had review = consequence with modal verb substitution. The anti-parrot instruction only covers call-2+, and the minimal review_lever description left call-1 unguarded for llama3.1.
- **gpt-oss-20b 2 plan timeouts** (was 0) — likely infrastructure noise but not confirmed.

### Unchanged
- Overall call success rate, option quality, lever naming, consequences depth, bracket leakage, option count violations.

### Assessment
PR #482 is a **lateral move**, not a clear improvement. The template lock fix is the most valuable single change across all 9 iterations — it was the top priority from analysis 40 and no other PR achieved it. But the haiku fabrication regression and llama3.1 parroting are real quality problems that cancel out the gain when assessed holistically.

## What we learned (proven rules)

### Things that work
1. **Minimal review_lever field description** — `"Critical review (20-40 words). See system prompt section 4 for examples."` breaks the template lock without introducing a new one. The key: no structural phrase for models to copy. Let examples teach.
2. **Anti-parrot in call-2+** — `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence."` eliminates gpt-oss-20b's call-2+ parroting.
3. **Word count limits in field descriptions** — models respect `(30-60 words)` and `(15-25 words)` annotations.
4. **partial_recovery threshold fix** — `< 3` -> `< 2` in runner.py. Pure code fix, zero risk.
5. **Positive framing** over negative prohibitions — safe, no regressions.

### Things that don't work
1. **Negative prohibitions naming banned phrases** — "Do NOT include 'Controls ... vs.'" and "Never invent percentages" both trigger the pattern they're trying to suppress.
2. **Abstract number prohibitions in section 5** — "NO fabricated statistics" and "NO calculated figures" both activate number-generation attention.
3. **Replacing one copyable phrase with another** in review_lever — any structural phrase becomes a template.
4. **Stripping field descriptions to pure word counts** — weak models (llama3.1, gpt-4o-mini) need structural anchors ("in one sentence", section 4 pointer) to avoid parroting or collapsing.
5. **Changing too many things at once** — makes it impossible to isolate what helped vs what hurt.

### The fundamental tension
- **Strong models** (haiku, gpt-4o-mini, gemini) follow system prompt instructions and produce rich content. They benefit from concise field descriptions and are hurt by verbose prohibitions that activate the banned pattern.
- **Weak models** (llama3.1, gpt-oss-20b, qwen3-30b) rely on field descriptions as local structural anchors. Stripping them causes parroting or format collapse. They need "in one sentence" and "See section 4 for examples" to produce non-trivial reviews.
- Every change that helps one group tends to hurt the other.

## Recommended next attempt

The strongest combination from these iterations would be:
1. **Only** the minimal review_lever fix from #482 (breaks template lock)
2. **Only** the anti-parrot call-2+ instruction from #483 (fixes parroting)
3. **Only** the partial_recovery threshold fix from #483 (code cleanup)
4. **Nothing else** — keep all other field descriptions, system prompt sections, and prohibitions exactly as baseline

This isolates the three proven wins without the changes that caused regressions (section 5 prohibition, verbatim-numbers on consequences/options, positive framing, word count changes).
