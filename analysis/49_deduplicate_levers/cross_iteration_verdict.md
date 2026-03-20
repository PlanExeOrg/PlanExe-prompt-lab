# Cross-Iteration Verdict: Iter 45 vs Iter 48 vs Iter 49

**Date**: 2026-03-20

Three iterations of `deduplicate_levers`, all using the same input
(`snapshot/0_identify_potential_levers`, 18 levers, 5 plans, 7 models).

| Iteration | Code | Taxonomy | Categories |
|-----------|------|----------|------------|
| 45 | PR #365 | primary / secondary / absorb / remove | 4-way |
| 48 | main (c8214511) | keep / absorb / remove | 3-way |
| 49 | PR #372 | primary / secondary / remove | 3-way |

---

## Why Iter 49 Wins

### 1. The absorb/remove distinction adds no downstream value

The `absorb` classification exists to record *which lever absorbs which*. But
the downstream pipeline (`enrich_potential_levers`, `focus_on_vital_few_levers`)
does not read or use this relationship. It only sees the list of surviving levers.
The absorb-info is write-only metadata — useful for debugging, but not a functional
signal.

Given this, having two "reject" categories (`absorb` and `remove`) in iter 45
adds classification complexity without downstream benefit. Models must decide
between two semantically similar actions ("merge into another lever" vs "fully
redundant"), and in practice they overwhelmingly choose `absorb` over `remove`:

- **Iter 45**: 143 total absorb+remove decisions → 143 absorb, ~0 remove
- **Iter 48**: 145 total absorb+remove decisions → 143 absorb, 2 remove

The `remove` category is dead weight in both iterations that have it alongside
`absorb`. Models treat them as the same thing and always pick `absorb`.

### 2. Three categories get fully exercised

In iter 49, all three categories are meaningfully used:

| Classification | Count | % of 630 decisions |
|---------------|------:|-----------:|
| primary | 367 | 58% |
| secondary | 168 | 27% |
| remove | 95 | 15% |

Every model uses all three categories. Compare iter 45 where `remove` was
essentially unused (≈0%), and iter 48 where `remove` appeared twice out of
630 decisions (0.3%).

The 3-way taxonomy forces a cleaner mental model: "Is this lever essential
(primary), useful but supporting (secondary), or redundant (remove)?"

### 3. The primary/secondary split is the real quality gain

Both iter 45 and iter 49 have primary/secondary triage. Iter 48 does not.
This triage signal is the most valuable output change across all three iterations:

- **Haiku on sovereign_identity**: correctly distinguishes phase-specific milestones
  (Procurement Language Specificity, Coalition Breadth → primary) from operational
  concerns (Platform Diversity Incentives, Contingency Protocol → secondary).
- **Gemini on parasomnia**: correctly identifies core research levers (Paranoia
  Narrative Focus, Subject Recruitment Ethics → primary) vs logistics
  (Documentation Standards, Communication Tooling → secondary).

Iter 48 (main) loses this signal entirely — everything that survives is just `keep`.

### 4. The degenerate collapse is fixed

Iter 48's worst failure: llama3.1 absorbed 7 unrelated levers into "Risk Framing"
as a catch-all bucket on sovereign_identity. This is a data-quality disaster —
the model treats one lever as a universal absorb target, losing semantic meaning.

Iter 49 eliminates this. llama3.1 now classifies those same levers as `secondary`
instead of absorbing them into a catch-all. The levers survive with correct
classifications. (The tradeoff is 0 removes on that plan — see "Remaining
Issues" below.)

Iter 45 also fixed this collapse, but with the 4-way overhead.

---

## Where Iter 49 Falls Short (and Why It's Acceptable)

### Models keep more levers (less aggressive dedup)

| Iteration | Avg levers kept (of 18) | Avg removed |
|-----------|------------------------:|------------:|
| 45 | ~12-14* | ~4-6* |
| 48 | 13.9 | 4.1 |
| 49 | 15.3 | 2.7 |

*Iter 45 data from 2 plans only.

Iter 49 keeps ~1.4 more levers on average. This is because levers that were
previously `absorb` (removed from output) are now split: 64% become `secondary`
(kept), 36% become `remove` (dropped).

This is acceptable because:
- The downstream `focus_on_vital_few_levers` step further filters the list.
  Over-inclusion at the dedup stage is recoverable; over-removal is not.
- Having more levers with primary/secondary tags is more useful than fewer
  levers with no triage signal.

### gpt-4o-mini barely removes anything (2/90)

This model is conservative under every taxonomy:
- Iter 45: 0 absorbs on sovereign_identity (zero-absorb problem)
- Iter 48: 2 absorbs on sovereign_identity (minimal)
- Iter 49: 2 removes total across all 5 plans

This is a model-specific limitation, not a taxonomy problem. It exists in all
three iterations.

### llama3.1 produces 0 removes on sovereign_identity

After the fix, llama3.1 classifies 2 primary + 16 secondary + 0 remove.
Better than the degenerate collapse (7 fake absorbs), but still no dedup.

Root cause identified in synthesis.md: template-lock in the `secondary`
definition (B3) — llama3.1 copies "distinct and useful but supporting or
operational" verbatim into all justifications, losing the ability to
distinguish levers and therefore unable to decide which to remove.

This is a prompt-wording issue, fixable without changing the taxonomy.

---

## Final Ranking

| Rank | Iteration | Why |
|------|-----------|-----|
| **1st** | **Iter 49 (PR #372)** | 3-way taxonomy where all categories are exercised. Primary/secondary triage. No degenerate collapse. Simpler than 4-way. Absorb-info in justification text is sufficient (not used downstream). |
| 2nd | Iter 45 (PR #365) | Has primary/secondary, but the 4th category (`remove`) is dead — models never use it when `absorb` exists. Over-engineered. |
| 3rd | Iter 48 (main) | No primary/secondary triage. Degenerate llama3.1 collapse. Missing calibration guidance. |

---

## Next Steps (from synthesis.md)

The taxonomy is right. The remaining issues are prompt-quality problems on
the current 3-way schema:

1. **B3 — Fix template-lock in `secondary` definition**: Replace the
   memorizable phrase with a conditional test question. This is the root cause
   of llama3.1's 0-remove pattern.
2. **B2 — Fix contradictory `primary` fallback instruction**: "Only as a last
   resort" contradicts "classify as primary to avoid data loss." Replace with
   unambiguous two-case guidance.
3. **S1 — Make calibration input-size-aware**: "Expect 4-10 removals from 15
   levers" underestimates for 18-lever inputs.
4. **B1 — Fix false `partial_recovery` events**: `runner.py` threshold fires
   on normal 2-call runs.
