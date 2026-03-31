# Assessment: Reduce word counts, add anti-echoing, and guide lever_id extraction

## Issue Resolution

**What PR #468 was supposed to fix:**

PR #468 supersedes PR #467, which had introduced a regression: llama3.1 returned
`<lever>uuid</lever>` as the `lever_id` value (i.e., copied the XML wrapper into the field)
rather than stripping it. Run 69 (PR #467, llama3.1, gta_game) confirmed 10 errors —
5 XML-tagged IDs caused 5 `unknown_lever_id` + 5 `incomplete` errors, leaving only 3/8
levers enriched.

PR #468 added two fixes for this:
1. **System prompt XML guidance** (line 170): "extract and return only the hexadecimal uuid
   string inside the tags — strip the XML tags themselves."
2. **lever_id Pydantic field description** (line 138): "The hexadecimal uuid of the lever,
   without XML tags."

Secondary goal: reduce synergy/conflict word targets (40-60 → 20-40 words) so that
gpt-oss-20b can complete within the 600s timeout (runs 63 had 2 timeouts).

**Is the primary issue resolved?**

YES for llama3.1: run 76 shows 0 errors across all 5 plans. The XML-tag stripping guidance
works. The field description + system prompt together prevent llama3.1 from returning the
XML wrapper.

YES for gpt-oss-20b timeout: run 77 completes all 5 plans, fastest at 105s, slowest at
203s — well within 600s. Shorter word targets reduced output token volume sufficiently.

**Residual symptoms:**

A new regression was introduced by the lever_id field description. The phrase "hexadecimal
uuid" is ambiguous: gpt-4o-mini interprets "hexadecimal" as implying a raw hex string with
no hyphens. Run 80 (gpt-4o-mini) shows this precisely — returned IDs are the correct UUIDs
with hyphens stripped:

```
returned:   bd43cd39f2f043589f5be4dbfdccc474   (fails enriched_levers_map lookup)
actual key: bd43cd39-f2f0-4358-9f5b-e4dbfdccc474 (in map)
```

Every `unknown_lever_id` error corresponds to an `incomplete` error with the same UUID
re-hyphenated, confirming this is purely a formatting mismatch, not a wrong lever.
4 of 5 plans affected (sovereign_identity: 0/5 levers enriched; gta_game: 5/8 levers).

---

## Quality Comparison

All 7 models appear in both batches. Before = runs 62–68 (PR #466). After = runs 76–82 (PR #468).

| Metric | Before (runs 62–68) | After (runs 76–82) | Verdict |
|--------|--------------------|--------------------|---------|
| **Plan success rate** | 33/35 (94.3%) | 35/35 (100%) | IMPROVED (+2 plans; gpt-oss-20b fixed) |
| **Lever enrichment rate** | 240/245 (98.0%)* | 232/245 (94.7%) | REGRESSED (−8; gpt-4o-mini −13, gpt-oss-20b +5) |
| **gpt-oss-20b enrichments** | 30/35 (2 timeout) | 35/35 | IMPROVED |
| **gpt-4o-mini enrichments** | 35/35 | 22/35 | REGRESSED (−13; hyphen-stripping) |
| **haiku unknown_lever_id errors** | 5 (2 plans) | 4 (1 plan) | UNCHANGED (≈ noise) |
| **Total internal errors** | 11 | 30 | REGRESSED (+19; all from gpt-4o-mini) |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED (all levers: 3 options each) |
| **Lever name uniqueness** | High (no duplicates observed) | High (no duplicates observed) | UNCHANGED |
| **Template leakage** | Not observed | Not observed | UNCHANGED |
| **Review format compliance** (`Controls X vs Y`) | Present in all spot-checked levers | Present in all spot-checked levers | UNCHANGED |
| **Consequence chain format** (`Immediate → Systemic → Strategic`) | Present across models | Present across models | UNCHANGED |
| **Avg description length** | ~508 chars (1.05× baseline 484) | ~389 chars (0.80× baseline) | IMPROVED (closer to 50-70 word target) |
| **Avg synergy length** | ~337 chars (1.18× baseline 286) | ~203 chars (0.71× baseline) | IMPROVED (within 20-40 word target) |
| **Avg conflict length** | ~347 chars (1.16× baseline 298) | ~210 chars (0.70× baseline) | IMPROVED (within 20-40 word target) |
| **Field length vs baseline (max across models)** | desc 1.35× (gpt-5-nano), synergy 1.55× (haiku) | desc 1.06× (haiku), synergy 0.97× (haiku) | IMPROVED (all below 2× threshold) |
| **Cross-call duplication** | Not measured | Not measured | N/A |
| **Over-generation** | haiku: 5 extra entries (discarded) | haiku: 4 extra entries (discarded) | UNCHANGED |
| **Fabricated quantification** | 47 percentage claims across all models | 41 percentage claims | IMPROVED (−13%; shorter word limits reduce opportunity) |
| **Marketing-copy language** | Not observed in spot checks | Not observed in spot checks | UNCHANGED |
| **LLMChatError events** | 0 | 0 | UNCHANGED |

*Haiku's 5 discarded extra characterizations are not counted as failures.

**OPTIMIZE_INSTRUCTIONS alignment:**

The PR moves closer to the goal of realistic, feasible, actionable plans on most dimensions:
shorter descriptions reduce verbosity and force more precise language; anti-echoing instruction
nudges models toward novel insight rather than consequence paraphrasing; fabricated percentage
claims decrease modestly (47 → 41). However, the OPTIMIZE_INSTRUCTIONS constant does not yet
document the lever_id format fragility introduced by PR #468. A new entry is warranted (see
Backlog).

---

## New Issues

### N1 — gpt-4o-mini lever_id hyphen-stripping regression (introduced by PR #468)

**Root cause:** `lever_id` field description "The hexadecimal uuid of the lever, without
XML tags" (line 138). The word "hexadecimal" implies raw hex encoding to gpt-4o-mini,
which strips all hyphens before returning the UUID. The `enriched_levers_map` at line 277
uses exact-match lookup (`if char.lever_id in enriched_levers_map`), so hyphen-stripped
IDs fail silently.

**Impact:** 13/35 levers unenriched across 4 of 5 plans in run 80. sovereign_identity: 0/5
levers enriched. gta_game: 5/8 levers enriched. silo is the only unaffected plan (reason
unclear — possibly plan-specific or batch-position-dependent).

**Fix:** Change field description from "hexadecimal uuid" to explicit standard UUID format
(e.g., "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"), and add defensive normalization in `execute()`
to strip hyphens from both sides before comparing.

### N2 — System prompt also uses "hexadecimal uuid string" (latent risk, S2)

Line 170: "extract and return only the hexadecimal uuid string inside the tags." This
reinforces the same ambiguous phrasing. System prompts are less directly causative than
Pydantic field descriptions for structured-output models, but it may amplify the
hyphen-stripping behavior in other models. Should be updated alongside the field description.

### N3 — Structural brittleness in enriched_levers_map lookup (pre-existing, now exposed)

The exact-match lookup at line 277 makes the pipeline brittle to any UUID formatting
variation (hyphens, case, whitespace). PR #468 did not introduce this but exposed it via
the ambiguous field description. A defensive normalization layer (strip hyphens from both
key and query before comparison) would prevent this class of regression from any future
model regardless of prompt wording.

### N4 — Latent: "hexadecimal" phrasing carried in OPTIMIZE_INSTRUCTIONS (not yet present)

The OPTIMIZE_INSTRUCTIONS constant does not yet document the lever_id format fragility.
Future prompt changes may reintroduce the same "hexadecimal" ambiguity without knowing
the history. This is a documentation gap, not a runtime defect.

---

## Verdict

**CONDITIONAL**: The PR achieves its two primary goals (llama3.1 XML-tag lever_id regression
fixed, gpt-oss-20b timeout eliminated) and delivers valuable secondary benefits (word count
reductions moving all models below the 2× verbosity threshold, modest reduction in fabricated
percentage claims). However, the lever_id field description introduces a critical regression:
gpt-4o-mini returns hyphen-stripped UUIDs, causing 13/35 levers (37%) to go unenriched
across 4 of 5 plans. This is a production-quality defect for a widely used model tier.

The fix is a one-line change to the field description plus optional defensive normalization
in code. These two changes must be applied before the PR can be fully accepted. The other
three changes in PR #468 (word count reduction, anti-echoing, system prompt XML guidance)
are sound and should be kept as-is.

---

## Recommended Next Change

**Proposal:** Fix the `lever_id` Pydantic field description (from "hexadecimal uuid" to an
explicit standard-format example) and add defensive UUID normalization in `execute()`.
Ship both changes in a single PR against `enrich_potential_levers.py`.

**Specific changes from synthesis.md Direction 1 + Direction 2:**

1. `enrich_potential_levers.py:138` — field description:
   - From: `"The hexadecimal uuid of the lever, without XML tags"`
   - To: `"The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags"`

2. `enrich_potential_levers.py:170` — system prompt:
   - From: `"extract and return only the hexadecimal uuid string inside the tags"`
   - To: `"extract and return only the standard UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) inside the tags"`

3. `enrich_potential_levers.py:276–285` — replace exact-match lookup with normalized lookup:
   ```python
   normalized_map = {k.replace('-', ''): k for k in enriched_levers_map}
   normalized_id = char.lever_id.replace('-', '').strip()
   canonical_id = normalized_map.get(normalized_id)
   if canonical_id:
       enriched_levers_map[canonical_id].update({...})
   else:
       logger.warning(...)
       errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
   ```

**Evidence:** Run 80 (gpt-4o-mini) shows every `unknown_lever_id` error maps exactly to
the same UUID with hyphens stripped (e.g., `bd43cd39f2f043589f5be4dbfdccc474` vs
`bd43cd39-f2f0-4358-9f5b-e4dbfdccc474`). The enriched_levers_map at line 219 uses
hyphenated keys from the input. A normalization fix would have caught all 13 gpt-4o-mini
errors in run 80 at zero additional prompt cost.

**Verify in next iteration:**

- **Primary check**: Run 80-equivalent (gpt-4o-mini) shows 0 `unknown_lever_id` and 0
  `incomplete` errors across all 5 plans. The sovereign_identity and gta_game plans should
  return 5/5 and 8/8 levers enriched respectively.
- **Regression check for llama3.1**: Run 76-equivalent still returns UUIDs without XML
  tags (i.e., system prompt guidance alone is sufficient; field description change does not
  break it).
- **Regression check for haiku**: `unknown_lever_id` error count stays at ≤ 5 (pre-existing
  extra-characterization behavior should be unaffected by a lookup normalization).
- **Format consistency**: Spot-check that returned lever_ids in run 80-equivalent are in
  standard hyphenated UUID format (not hex-only, not XML-wrapped, not uppercase).
- **silo anomaly**: In run 80, silo was the only plan where gpt-4o-mini returned correctly
  formatted UUIDs. Check whether the fix eliminates this inconsistency or if silo was
  already clean for a different reason (batch composition, plan size).

**Risks:**

- The normalization fix (direction 2) strips hyphens for comparison only — stored data and
  original UUIDs are unchanged. Risk of data corruption: none.
- Changing the field description from "hexadecimal uuid" to explicit format example could
  theoretically confuse llama3.1 if it relied on the "hexadecimal" cue for some reason.
  But run 76 confirms llama3.1 already returns correct hyphenated UUIDs — the system prompt
  (not the field description) is what drives llama3.1's behavior. Risk: very low.
- The system prompt phrasing change (replacing "hexadecimal uuid string" with "standard UUID
  (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)") affects all models. Watch for any model that now
  becomes more verbose about the UUID format or misreads the example pattern.

**Prerequisites:** None. This is a standalone fix that does not depend on any other pending
changes.

---

## Backlog

**Resolved — can be removed from backlog:**
- llama3.1 UUID contamination in synergy_text/conflict_text: fully resolved by PR #466,
  confirmed stable in PR #468 runs (0 occurrences in all run 76 outputs).
- gpt-oss-20b 600s timeout: resolved by PR #468 word count reduction (runs 77: max 203s).
- llama3.1 XML-tag lever_id inclusion (PR #467 regression): resolved by PR #468 system
  prompt guidance (run 76: 0 errors).

**Remaining — carry forward:**
- **B1 (gpt-4o-mini lever_id hyphen-stripping)**: Critical regression from PR #468.
  Fix: change field description to explicit UUID format example + add defensive normalization
  in `execute()`. [Priority: HIGH — blocks CONDITIONAL verdict from becoming YES]
- **haiku extra-characterization noise (4–5 unknown_lever_id per run)**: Pre-existing.
  All real levers correctly enriched; errors are discarded extras. Benign but noisy.
  Potential fixes: (a) suppress `errors.append` for `unknown_lever_id` (one-line; safe),
  (b) add no-max_length rationale comment to `BatchCharacterizationResult.characterizations`
  (prevents future accidental cap). [Priority: LOW — no correctness impact]
- **B1 from analysis 65 — Negative prohibition in `Lever.consequences` field description**:
  `identify_potential_levers.py:116–119` names `'Controls ... vs.'` and `'Weakness:'` as
  banned phrases, contradicting OPTIMIZE_INSTRUCTIONS lines 81–82. No observable regression
  yet, but latent template-lock risk for small/non-English models. Fix: replace with positive
  structural framing. Requires a self_improve iteration against `identify_potential_levers`.
  [Priority: MEDIUM]
- **S3 (runner.py partial_recovery threshold)**: `runner.py:131` warns `if actual_calls < 3`,
  but 2-call success is normal. Should be `< 2`. [Priority: LOW — telemetry accuracy only]
- **OPTIMIZE_INSTRUCTIONS documentation gap**: The UUID lever_id format fragility pattern
  (phrase "hexadecimal uuid" → hyphen-stripping) is not yet documented. Add a bullet after
  the fix lands. [Priority: LOW]

**New additions to backlog:**
- **Defensive UUID normalization in `enriched_levers_map` lookup** (`enrich_potential_levers.py:277`):
  Even after fixing the field description, exact-match lookup remains brittle to future
  model formatting variation. Defensive normalization (strip hyphens from both key and
  query) provides format-agnostic matching independent of prompt wording. [Priority: HIGH —
  recommended to ship alongside field description fix]
- **gpt-4o-mini silo anomaly**: In run 80, silo was the only plan where gpt-4o-mini returned
  correctly hyphenated UUIDs (0 errors). Reason unknown — batch composition, plan size, or
  coincidence. Verify once the fix is applied. [Priority: LOW]
