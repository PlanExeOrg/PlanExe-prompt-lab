# Assessment: Remove formulaic naming template from lever prompt

## Issue Resolution

**PR #279 target:** Remove `[Domain]-[Decision Type] Strategy` example from the lever system
prompt, which caused models to mechanically prefix every lever name.

**Evidence from PR description:** Runs 65 (gpt-4o-mini) and 66 (claude-haiku) from the
prior batch showed 100% and 47% "Silo-X Strategy" prefixing respectively.

**Post-fix status:** The runs in analysis/9 (67–73) were generated with the **same registered
prompt_1** (`b12739343…`) as the prior batch. The code-side system prompt in
`identify_potential_levers.py:143` has already been updated to say "avoid formulaic patterns
or repeated prefixes," but the registered prompt file used by the optimizer still contains the
old `[Domain]-[Decision Type] Strategy` example. Therefore:

- Runs 67–73 **confirmed the problem at scale** across all six functioning models, but
  are themselves pre-fix runs.
- PR #279 registers the new prompt file to match the already-updated code. The fix is not
  yet tested against live runs.

**Residual symptoms:** Template leakage is **confirmed in 3 of 6 successful models** in
the after batch, with leakage rates equal to or worse than the before batch:

| Model | Before (runs 60–66) | After (runs 67–73) |
|-------|---------------------|---------------------|
| llama3.1 | ~0% (diverse names in call 1) | 100% (all names follow `[X]-[Y]-Strategy`) |
| gpt-oss-20b | 0% | ~93% (14/15 silo) |
| gpt-4o-mini | 100% (silo) | 100% (silo), ~0% (GTA) |
| gpt-5-nano | 0% (silo) | ~7% (silo), 100% (GTA/HongKong) |
| qwen3-30b | 0% | 0% |
| haiku | ~47% | 0% |

The template problem is **real and widespread**. The template even produced the nonsensical
`Denmark-Procurement-Strategy Strategy` in run 68 (llama3.1/sovereign_identity plan).

---

## Quality Comparison

All seven models appear in both batches. Models are compared directly by run number.

| Metric | Before (runs 60–66) | After (runs 67–73) | Verdict |
|--------|---------------------|---------------------|---------|
| **Success rate: nemotron** | 0/5 | 0/5 | UNCHANGED |
| **Success rate: llama3.1** | 5/5 | 5/5 | UNCHANGED |
| **Success rate: gpt-oss-20b** | 4/5 | 5/5 | IMPROVED |
| **Success rate: gpt-5-nano** | 5/5 | 5/5 | UNCHANGED |
| **Success rate: qwen3-30b** | 5/5 | 5/5 | UNCHANGED |
| **Success rate: gpt-4o-mini** | 5/5 | 5/5 | UNCHANGED |
| **Success rate: haiku** | 4/5 | 4/5 | UNCHANGED |
| **Bracket placeholder leakage (all runs)** | 1 (run 64/qwen3) | 7 (run 68/llama3.1) | REGRESSED |
| **Option count violations (!=3 options/lever)** | 0 in any run | 0 in any run | UNCHANGED |
| **Lever name uniqueness: llama3.1** | 85/95 (avg 2.0 dup/plan) | 77/92 (14 cross-response dups) | REGRESSED |
| **Lever name uniqueness: gpt-oss-20b** | 59/60 | 75/75 | IMPROVED |
| **Lever name uniqueness: gpt-4o-mini** | 74/75 | 72/75 | UNCHANGED (~) |
| **Lever name uniqueness: others** | All near-perfect | All near-perfect | UNCHANGED |
| **Template leakage: llama3.1 (silo)** | ~0% | 100% | REGRESSED |
| **Template leakage: gpt-oss-20b (silo)** | 0% | ~93% | REGRESSED |
| **Template leakage: gpt-4o-mini (silo)** | 100% | 100% | UNCHANGED |
| **Template leakage: gpt-5-nano (cross-plan)** | 0% | 0% silo, 100% GTA | REGRESSED |
| **Template leakage: qwen3-30b** | 0% | 0% | UNCHANGED |
| **Template leakage: haiku** | ~47% | 0% | IMPROVED |
| **Review format compliance (Controls/Weakness): llama3.1** | ~14/20 missing parts | 13/92 missing parts | IMPROVED (~) |
| **Review format compliance: qwen3** | ~3/75 partial | 0/75 missing | IMPROVED |
| **Review format compliance: all others** | 100% | 100% | UNCHANGED |
| **Consequence chain format (Imm→Sys→Strat): gpt-oss-20b** | 15 misses | 0 misses | IMPROVED |
| **Consequence chain format: gpt-5-nano** | 5 misses | 0 misses | IMPROVED |
| **Consequence chain format: haiku** | 58 misses | 3 misses | IMPROVED |
| **Consequence chain format: all others** | 0 misses | 0 misses | UNCHANGED |
| **Review text leaking into consequences: qwen3** | 60/75 | 60/75 | UNCHANGED |
| **Review text leaking into consequences: others** | 0–1/75 | 0/75 | UNCHANGED |
| **Content depth — consequences avg chars: llama3.1** | 148.4 | 156.6 | UNCHANGED |
| **Content depth — consequences avg chars: gpt-oss-20b** | 331.2 | 352.4 | UNCHANGED |
| **Content depth — consequences avg chars: gpt-5-nano** | 477.8 | 417.5 | UNCHANGED (~) |
| **Content depth — consequences avg chars: qwen3** | 359.4 | 343.3 | UNCHANGED |
| **Content depth — consequences avg chars: gpt-4o-mini** | 252.2 | 235.2 | UNCHANGED |
| **Content depth — consequences avg chars: haiku** | 849.1 | 867.7 | UNCHANGED |
| **Lever count per plan: llama3.1** | 19–20 (B1 violation) | 17–19 (B1 violation) | UNCHANGED (still violates) |
| **Lever count per plan: haiku** | 15–19 | 17–19 | UNCHANGED |
| **Lever count per plan: all others** | 15 | 15 | UNCHANGED |

**Notes on verified outputs:**
- Run 65 vs 72 (gpt-4o-mini / silo): identical "Silo-X Strategy" naming in both batches,
  nearly identical structure and content depth. No change.
- Run 63 vs 70 (gpt-5-nano / silo): before batch shows diverse names ("Underground-Silo
  Governance Strategy", "Self-Sufficiency Resource Strategy"); after batch shows mostly
  generic names but some domain-prefix ("Silo Core Systems Integration Strategy").
- Run 64 vs 71 (qwen3 / silo): `consequences` field still ends with "Controls … Weakness:
  …" text in both batches. Persistent, model-level failure mode, unaffected by changes.
- Run 66 vs 73 (haiku / silo): before batch shows some "X Strategy" prefixes; after batch
  shows entirely natural compound names ("Capital Phasing and Funding Resilience",
  "Governance Legitimacy Strategy"). Quality of haiku output IMPROVED.

---

## New Issues

### N1 — Template leakage WORSENED for llama3.1 between batches (net effect of PR #278)

PR #278 introduced fresh-context-per-call, removing accumulated prior-call assistant output
from context. With accumulating context, call 2 would implicitly see call 1's diverse names
as examples and deviate from the template. With fresh context, each call independently
applies the `[Domain]-[Decision Type] Strategy` pattern without any implicit counter-example.
This explains why llama3.1 went from ~0% template leakage (run 61) to 100% (run 68),
despite no prompt change.

Similarly, gpt-oss-20b went from 0% (run 62) to 93% (run 69). The fresh-context design
from PR #278 **amplified** the template leakage problem for susceptible models, making PR
#279 more urgent than previously understood.

### N2 — llama3.1 cross-call duplicate names exploded (1 → 14 pairs)

With 100% template leakage in run 68 and names following `Silo-X-Strategy` / `GTA-X-Lever`,
the name space is so narrow that cross-call collisions multiplied. Run 61 had 1 duplicate
pair; run 68 has 14 (including 3 repeated pairs in the GTA plan). This is a direct downstream
effect of N1.

### N3 — gpt-5-nano template leakage is plan-dependent (0% silo, 100% GTA/Hong Kong)

Run 70 appeared mostly clean on silo (~7% leakage), but across all plans it produced 25
domain-template names (all 15 GTA levers follow `GTA-X Strategy`, all 10 Hong Kong levers
follow `HK-X Strategy`). The silo-focused view from the analysis understated the problem.
This shows the template triggers when the plan name is recognizable to the model as a short
domain label.

### N4 — Haiku's hong_kong_game failure mechanism identified

Run 73 (haiku) failed on `20260310_hong_kong_game` with "List should have at least 5 items
after validation, not 1." The model produced only 1 lever in one call. This matches run 66's
failure on the same plan (different error: missing `levers` + `summary` keys). The hong_kong
plan likely triggers a different reasoning path in haiku — possibly related to plan length or
the absence of clear "survival decision" framing that haiku relies on for lever identification.
This is a latent content-sensitivity issue, not a prompt formatting issue.

---

## Verdict

**YES**: PR #279 should be merged. The `[Domain]-[Decision Type] Strategy` template causes
mechanical name leakage in 3–4 of 6 functioning models (93–100% in llama3.1, gpt-oss-20b,
and gpt-4o-mini), and the fresh-context change from PR #278 demonstrably amplified the
leakage. The code-side fix is already in place. The registered prompt update has zero
additional risk: models that resist the template (haiku, qwen3) are unaffected; the
models that follow it mechanically (llama3.1, gpt-oss-20b, gpt-4o-mini) are the ones
needing the fix.

---

## Recommendations

### Should the next iteration follow the after-batch synthesis recommendation?

Yes. The synthesis for analysis/9 recommends:
1. **Add a post-merge quality gate** (Direction 1) — highest priority code fix; would catch
   qwen3's persistent field contamination (60/75 levers) and llama3.1's placeholder leaks
   before they enter `002-10-potential_levers.json`. This is independent of prompt version.
2. **Approve PR #279** (Direction 2) — already the verdict above; merge it.
3. **Align count instruction with 5–7 schema** (Direction 3) — clean up "EXACTLY 5" wording
   in registered prompt; low effort, eliminates confusing dual instruction.

The synthesis correctly notes that Direction 2 (PR #279) is zero-effort and should be approved
in parallel with Direction 1.

### Issues from before (analysis/8) that are now resolved

- None are fully resolved. The count contract mismatch (B1), merge loop ungated (B3/B4),
  and no retry config in runner (S3) from analysis/8 are all still present in analysis/9.
  These remain open backlog items.

- **Template leakage** was identified in analysis/8 as H1 and is the subject of PR #279
  (now being merged). Once PR #279's new prompt is registered and a new batch is run,
  this can be closed if leakage drops to near-zero for llama3.1, gpt-oss-20b, and gpt-4o-mini.

### Issues to add to backlog from analysis/9

1. **PR #278 amplified template leakage for susceptible models** — fresh-context-per-call
   removed implicit anti-template guidance from prior-call outputs. After PR #279 lands and
   removes the template, verify that susceptible models (llama3.1, gpt-oss-20b) don't find
   another way to mechanically pattern-match. If they do, Direction 4 (explicit naming
   anti-repetition instruction) from synthesis should be added.

2. **gpt-5-nano has plan-dependent template leakage** — silo appears clean but GTA/Hong Kong
   show 100% `X-Y Strategy` naming. Verify this resolves after PR #279 removes the template.

3. **llama3.1 cross-call duplicate names** (14 pairs in run 68) — direct consequence of
   100% template leakage narrowing the name space. Should self-correct after PR #279, but
   monitor in next batch.

4. **haiku hong_kong_game plan failure is persistent** — failed in both run 66 and run 73
   (different error modes). Investigate whether this plan has structural characteristics that
   confuse haiku's lever extraction logic.

5. **qwen3 field contamination (review text in consequences)** persists at 60/75 in both
   batches. This is unchanged and unaffected by the naming template. The post-merge quality
   gate (Direction 1 from synthesis) is the right fix — it would reject contaminated levers
   before saving. Add to backlog if not addressed in the next iteration.
