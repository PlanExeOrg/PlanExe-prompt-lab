# Assessment: Reduce word counts and add anti-echoing guidance to enrich fields

## Issue Resolution

**What the PR was supposed to fix (PR #467):**
1. **gpt-oss-20b budget overruns** — The reasoning model timed out on `hong_kong` and `parasomnia` plans (600s limit). Reducing word count targets ~35% (description 80-100 → 50-70 words; synergy/conflict 40-60 → 20-40 words) was intended to bring gpt-oss-20b within budget.
2. **llama3.1 consequence echoing** — llama3.1 was producing descriptions at 0.76× baseline length, interpreted as echoing the `consequences` field rather than generating independent enrichment. Anti-echoing guidance ("Do NOT repeat the consequences or review fields — add new insight...") was added to the system prompt and Pydantic field descriptions.

**Is issue 1 resolved?** YES — completely. gpt-oss-20b went from 3/5 plans (two timeouts: hong_kong and parasomnia) to 5/5 plans with 0 errors. `hong_kong` recovered from 2 characterized levers to 8; `parasomnia` completed at 319s (within budget).

Evidence: `history/4/70_enrich_potential_levers/outputs.jsonl` — all 5 plans `"status": "ok"` vs `history/4/63_enrich_potential_levers/outputs.jsonl` — hong_kong and parasomnia timed out.

**Is issue 2 resolved?** PARTIAL. Fabricated percentage claims in descriptions are reduced (haiku: 3 → 0). However, structural echoing of consequence-derived vocabulary persists across gemini and haiku. Gemini's hong_kong `Audience Engagement Strategy` description still reads "success is measured by a 20% increase in ticket sales..." — directly echoing the consequence. llama3.1 description lengths actually decreased further (374 → 283 chars avg), showing more compression but not more independent insight.

**New regression introduced:** A new failure mode was created. llama3.1's gta_game batch 1 returned `lever_id` values wrapped in XML tags (e.g., `"<lever>1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd</lever>"`), which fail the bare-UUID keyed `enriched_levers_map` lookup at `enrich_potential_levers.py:275`. This caused 5 `unknown_lever_id` + 5 `incomplete` errors — 3 of 8 gta_game levers enriched instead of 8. The root cause is the interaction of the `<lever>uuid</lever>` prompt format (PR #466) with PR #467's Pydantic field-description changes, which made the schema more prominent for non-function-calling models like llama3.1.

---

## Quality Comparison

All 7 models appear in both batches (runs 4/62–68 before, 4/69–75 after), making full comparison valid.

| Metric | Before (runs 4/62–68) | After (runs 4/69–75) | Verdict |
|--------|----------------------|----------------------|---------|
| **Plan-level success rate** | 33/35 (94.3%) | **35/35 (100%)** | IMPROVED |
| **gpt-oss-20b success** | 3/5 (2 timeouts) | 5/5 (0 timeouts) | IMPROVED |
| **llama3.1 lever-level errors** | 0 | **10** (5 unknown_lever_id + 5 incomplete, gta_game batch 1) | REGRESSED |
| **haiku unknown_lever_id errors** | 5 | 4 | IMPROVED (−1) |
| **Total lever-level errors** | 11 | 15 | REGRESSED (+4) |
| **LLMChatError events** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | Not observed | Not observed | UNCHANGED |
| **Option count violations** | Not systematically observed | Not systematically observed | UNCHANGED |
| **Lever name uniqueness** | Not measured | Not measured | UNCHANGED |
| **Template leakage** | Not observed | Not observed | UNCHANGED |
| **Review format compliance** | Not measured | Not measured | UNCHANGED |
| **Consequence chain format** | Not measured | Not measured | UNCHANGED |
| **Content depth (avg option length)** | Not directly measured | Not directly measured | UNCHANGED |
| **Cross-call duplication** | Not observed | Not observed | UNCHANGED |
| **Avg description length** | ~519 chars (0.86× baseline 602.9) | **~374 chars** (0.62× baseline) | IMPROVED (targets hit; no 2× violation) |
| **Avg synergy_text length** | ~325 chars (0.76× baseline 427.4) | **~199 chars** (0.47× baseline) | IMPROVED (targets hit) |
| **Avg conflict_text length** | ~325 chars (0.88× baseline 371.4) | **~206 chars** (0.55× baseline) | IMPROVED (targets hit) |
| **Fabricated quantification (haiku descriptions)** | 3 percentage claims | **0** | IMPROVED |
| **Marketing-copy language** | Not systematically measured | "cutting-edge" appears in gta_game after (gpt-oss-20b run 70) | MARGINAL (pre-existing, not PR-related) |

**Field length detail by model (after):**

| Model | desc ratio vs baseline | syn ratio vs baseline | conf ratio vs baseline | At 50-70w / 20-40w target? |
|-------|----------------------|---------------------|---------------------|---------------------------|
| gemini | 0.53× | 0.32× | 0.40× | desc ✓, syn ✓, conf ✓ |
| gpt-4o-mini | 0.63× | 0.42× | 0.51× | desc ✓, syn ✓, conf ✓ |
| gpt-5-nano | 0.73× | 0.49× | 0.59× | desc slightly over, syn ✓, conf ✓ |
| gpt-oss-20b | 0.74× | 0.46× | 0.52× | desc slightly over, syn ✓, conf ✓ |
| haiku | 0.78× | 0.60× | 0.71× | desc over (~78w), syn/conf slightly over |
| llama3.1* | 0.47× | 0.56× | 0.66× | desc under (~47w), syn/conf borderline |
| qwen3-30b | 0.46× | 0.41× | 0.50× | desc under (~47w), syn ✓, conf ✓ |

\* llama3.1 values based on 30 levers (gta_game partial failure excluded).

No model exceeds the 2× warning threshold. gemini's synergy/conflict at 0.32×/0.40× of baseline (≈23-25 words) is at the absolute lower bound of the 20-40 word target — informationally sufficient but thin.

**OPTIMIZE_INSTRUCTIONS alignment:**

| Known problem | Status after PR #467 |
|---------------|---------------------|
| Word-count padding | Substantially reduced (−28% desc, −40% syn/conf) |
| Consequence echoing | Partially reduced (% claims removed, structural echoing persists) |
| Fabricated quantification | Improved for descriptions (haiku: 3→0) |
| UUID leakage into free-text fields | Still resolved (PR #466 fix holds) |
| Haiku extra-characterization | Slight improvement (5→4) |
| **XML-tag leakage into lever_id (NEW)** | 1/5 plans affected (llama3.1 gta_game) |
| OPTIMIZE_INSTRUCTIONS word-count reference | **STALE** — `enrich_potential_levers.py:73` still says "80-100 word target" after PR #467 changed it to 50-70 |

---

## New Issues

**N1 — llama3.1 XML-tag leakage into lever_id (confirmed regression):**
llama3.1 gta_game batch 1 returned `lever_id` values as `"<lever>uuid</lever>"` instead of bare UUIDs. The `enriched_levers_map` at `enrich_potential_levers.py:217` is keyed by bare UUIDs; the lookup at line 275 performs no stripping, so all 5 characterizations in that batch failed. This is a latent vulnerability in the code that PR #466 created (XML-tagged prompt format) and PR #467 exacerbated (Pydantic schema changes shifted llama3.1's attention pattern). The fix is a 4-line strip before line 275.

Evidence: `history/4/69_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 10 errors, 3/8 levers characterized.

**N2 — Anti-echoing instruction violates OPTIMIZE_INSTRUCTIONS principle (design issue):**
The instruction "Do NOT repeat the consequences or review fields" (lines 140 and 171 of `enrich_potential_levers.py`) uses a negative prohibition. `identify_potential_levers.py`'s OPTIMIZE_INSTRUCTIONS (lines 80-83) explicitly documents this as a known failure mode: "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template." This explains why structural echoing persists despite the fix. The positive clause at the end ("add new insight about why this lever matters and what success looks like") is the useful part; the "Do NOT" prefix undermines it.

**N3 — OPTIMIZE_INSTRUCTIONS stale word-count reference:**
`enrich_potential_levers.py:73` still reads "Models inflate to hit the 80-100 word target" after PR #467 changed the target to 50-70 words. Future optimization iterations reading OPTIMIZE_INSTRUCTIONS will be misled into treating the new shorter outputs as already-optimal rather than as a deliberate change.

**N4 — batches_succeeded counter incremented on total batch failure (B2):**
`enrich_potential_levers.py:272` increments `batches_succeeded` before iterating over characterizations. A batch where all `lever_id` lookups fail (as in N1) still counts as succeeded. The counter surfaces in `PlanResult.calls_succeeded` and `events.jsonl`'s `partial_recovery` check — a failing batch will not trigger a `partial_recovery` warning.

**Latent issue surfaced:** The `<lever>uuid</lever>` prompt format (PR #466) had no output-side guard — no instruction in the system prompt telling models to output only the raw UUID in the `lever_id` field. PR #467's Pydantic schema changes made this latent gap active for llama3.1. The gap exists for all non-function-calling models.

---

## Verdict

**CONDITIONAL**: The primary goal — gpt-oss-20b full recovery to 5/5 plans and 100% overall plan success — is achieved decisively and is a genuine improvement. However, PR #467 introduced a confirmed data-loss regression (B1: llama3.1 loses 5 levers per affected gta_game batch) by not including a defensive code fix for the `<lever>uuid</lever>` prompt format introduced in PR #466. The condition for keeping this PR is: implement the B1 XML-tag stripping fix at `enrich_potential_levers.py:275` before or as part of the merge.

If B1 is fixed, the verdict upgrades to YES. The anti-echoing issue (N2) and stale OPTIMIZE_INSTRUCTIONS (N3) are notable design inconsistencies but do not cause data loss — they can follow in the next iteration.

---

## Recommended Next Change

**Proposal:** Add a defensive XML-tag strip to `enrich_potential_levers.py:275` before the `enriched_levers_map` lookup, so that `lever_id` values in the form `<lever>uuid</lever>` are automatically recovered. This is the code-level fix for bug B1.

Specifically, replace:
```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
```
with:
```python
for char in batch_result.characterizations:
    raw_id = char.lever_id.strip()
    if raw_id.startswith("<lever>") and raw_id.endswith("</lever>"):
        raw_id = raw_id[7:-8]
    if raw_id in enriched_levers_map:
```
Update the three subsequent references to `char.lever_id` in the same block to use `raw_id` for map key operations while preserving `char.lever_id` in the error record for traceability.

**Evidence:** Both `insight_claude.md` (C1) and `code_claude.md` (B1/I1) identify this as a confirmed bug at `enrich_potential_levers.py:275`. Source code confirms: map keyed by bare UUIDs at line 217, prompt format uses `<lever>{lever.lever_id}</lever>` at lines 239-245, lookup at line 275 has no stripping. Run 69 (llama3.1 gta_game) shows 10 errors from a single 5-lever batch, recovering only 3/8 levers. Run 62 (same model, same plan, before PR #467) had 0 errors.

**Verify in next iteration:**
- llama3.1 gta_game: confirm 0 `unknown_lever_id` errors and 8/8 levers characterized (was 3/8 in run 69)
- All other models: confirm no change to their error counts (bare UUIDs pass through the strip unchanged)
- haiku: confirm `unknown_lever_id` errors (currently 4) are unaffected — these are fabricated IDs, not XML-tagged UUIDs, so the strip should not fire
- gemini: verify conflict_text length remains ≥20 words (~120 chars) after any future word-count changes — currently at the absolute lower bound (149 chars avg)

**Risks:**
- The strip is unconditional for `lever_id` values starting with `<lever>` — if a lever UUID coincidentally begins with those 7 characters (impossible since UUIDs start with hex digits), it would be wrongly stripped. In practice, zero risk.
- If a future prompt change modifies the XML tag wrapper (e.g., to `<id>` or `<lever_id>`), the hard-coded strings in the strip would need updating. Mitigated by adding explicit `lever_id` output instruction to system prompt (Direction 3 from synthesis) as a complementary fix.
- Structural echoing (N2, N3) and the stale OPTIMIZE_INSTRUCTIONS remain. The next PR after B1 should replace the "Do NOT repeat" prohibition with a positive directive: "Explain what this lever is optimising for, what project-specific trade-offs it accepts, and what observable evidence would indicate success."

**Prerequisite issues:** None — the B1 fix is self-contained.

**OPTIMIZE_INSTRUCTIONS update recommended:**
1. Update `enrich_potential_levers.py:73`: change "80-100 word target" → "50-70 word description target (20-40 for synergy/conflict), changed in PR #467"
2. Add after the UUID leakage entry (lines 88-96): document the XML-tag-in-lever_id inverse failure mode — non-function-calling models may copy `<lever>uuid</lever>` markup into the `lever_id` JSON field when the prompt format and Pydantic schema are both prominent. Mitigations: (a) strip XML tags from `lever_id` before map lookup; (b) positive instruction "output only the raw UUID string exactly as shown."

---

## Backlog

**Resolved (can be closed):**
- gpt-oss-20b timeout issue — fully resolved by PR #467's word count reduction. gpt-oss-20b is now 5/5 plans with 0 errors.

**Carry forward from before:**
- haiku extra-characterization (unknown_lever_id): 5 → 4 errors, slow decline. Not data-loss (real levers are correctly enriched). Whether batch-size reduction (5 → 3 for haiku) would eliminate this remains untested.
- gpt-5-nano minor error (1 incomplete in run 71): likely stochastic; no structural fix needed.

**New items to add:**
- **B1 (HIGH): XML-tag stripping at `enrich_potential_levers.py:275`** — confirmed data loss, 4-line fix, must fix before or with PR #467 merge
- **S1 (MEDIUM): Replace "Do NOT repeat" anti-echoing instruction with positive directive** — violates OPTIMIZE_INSTRUCTIONS principle; structural echoing persists; reword at lines 140 and 171
- **S2 (MEDIUM): Add positive `lever_id` output instruction to system prompt** — closes the format ambiguity that allowed llama3.1 to copy XML markup; one sentence addition at `enrich_potential_levers.py:163-178`
- **S3 (LOW): Update OPTIMIZE_INSTRUCTIONS word-count reference** — stale "80-100 word target" at `enrich_potential_levers.py:73` misleads future optimization iterations
- **B2 (LOW): Fix `batches_succeeded` counter** — incremented before lever_id lookup, gives misleading success signal when entire batch fails; move inside the enrichment loop at `enrich_potential_levers.py:272`
- **I7 (WATCH): gemini conflict_text at lower bound** — 149 chars avg (≈23 words) is at the absolute floor of the 20-40 word target; defend ≥25 words for conflict_text if future iterations tighten further
