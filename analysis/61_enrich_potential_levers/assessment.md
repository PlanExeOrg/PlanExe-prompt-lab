# Assessment: Add UUID prohibition and exact-count instruction to enrich prompts

## Issue Resolution

**PR #458** adds two prompt changes to `enrich_potential_levers.py`:

1. **System prompt UUID prohibition** (line 178): `"Do NOT include any Lever ID, UUID, or identifier string in these fields."` — targets llama3.1's 15 residual same-batch UUID occurrences from `lever_details_for_prompt`.
2. **Exact-count user prompt** (line 257): `"Return exactly {len(batch)} characterizations — one per lever, no more, no fewer."` — targets haiku's 7 fabricated extra `LeverCharacterization` entries introduced by PR #457.
3. **OPTIMIZE_INSTRUCTIONS update** (lines 88–99): documents residual per-batch UUID vector and haiku's extra-characterization behavior.

**Issue 1 — llama3.1 same-batch UUID copying: NOT RESOLVED (regression introduced)**

The UUID prohibition instruction names `"Lever ID"` — the exact format llama3.1 uses in synergy/conflict output. This is a documented negative-instruction priming risk: `identify_potential_levers.py` lines 80–82 explicitly warns "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases." The warning was not applied when writing the enrich prohibition.

Direct evidence from `history/4/34_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`: a plan that was completely clean in run 4/27 (0 UUID occurrences) now has 20 UUID occurrences in synergy/conflict text — every lever × both fields × 2 UUIDs per field, all real same-batch IDs. Example:
> `"synergy_text": "This lever has strong synergy with the Policy Advocacy Strategy (lever ID: 80b177d0-c67e-4bc2-bd50-3f49b815e633)..."`

Net llama3.1 UUID count: 29 → 29 (gta_game improved, sovereign_identity regressed, net zero).

**Issue 2 — haiku extra characterizations: PARTIALLY RESOLVED (–71%)**

The "Return exactly N" instruction reduced haiku errors from 7 to 2 across the 5-plan run set. gta_game confirmed at `history/4/40_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: `"errors": []` (was 5 errors in run 4/33). Remaining 2 errors: silo gained 1 new error (fabricated ID `d890e123-abcd-4567-ef01-234567890abc`, confirmed from direct inspection) and hong_kong persists with 1 error. All real levers remain correctly enriched.

**Residual symptoms:**

- llama3.1 sovereign_identity: 0 → 20 UUID occurrences in synergy/conflict (PR-introduced regression)
- llama3.1 net synergy/conflict UUID count: ~19 → ~20 (no improvement)
- haiku silo: 1 new error; haiku hong_kong: 1 persisting error

---

## Quality Comparison

Both batches use `baseline/train` (5–8 levers/plan). Before: runs 4/27–33 (after PR #457). After: runs 4/34–40 (after PR #458). All 7 models appear in both batches. Note: gpt-oss-20b recovered to 5/5 in runs 4/35 onward (the 2/5 result in analysis 60's "after" batch was confirmed network noise).

| Metric | Before (4/27–33) | After (4/34–40) | Verdict |
|--------|-----------------|-----------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| llama3.1 success | 5/5 | 5/5 | UNCHANGED |
| gpt-oss-20b success | 5/5 | 5/5 | UNCHANGED |
| gpt-5-nano success | 5/5 | 5/5 | UNCHANGED |
| qwen3-30b success | 5/5 | 5/5 | UNCHANGED |
| gpt-4o-mini success | 5/5 | 5/5 | UNCHANGED |
| gemini success | 5/5 | 5/5 | UNCHANGED |
| haiku success | 5/5 | 5/5 | UNCHANGED |
| **Total errors (unknown_lever_id)** | 7 (haiku, 3 plans) | 2 (haiku, 2 plans) | IMPROVED (–71%) |
| haiku errors | 7 | 2 | IMPROVED (–71%) |
| haiku gta_game errors | 5 | 0 | IMPROVED |
| haiku parasomnia errors | 1 | 0 | IMPROVED |
| haiku hong_kong errors | 1 | 1 | UNCHANGED |
| haiku silo errors | 0 | 1 | REGRESSED (new) |
| llama3.1 errors | 0 | 0 | UNCHANGED |
| All other models errors | 0 | 0 | UNCHANGED |
| **llama3.1 total text-field UUIDs** | 29 | 29 | UNCHANGED (net zero) |
| llama3.1 gta_game synergy/conflict UUIDs | ~19 | ~0 | IMPROVED (gta_game) |
| llama3.1 sovereign_identity synergy/conflict UUIDs | 0 | 20 | REGRESSED (PR-introduced) |
| llama3.1 silo synergy/conflict UUIDs | 0 | 0 | UNCHANGED |
| llama3.1 hong_kong synergy/conflict UUIDs | 0 | 0 | UNCHANGED |
| **gemini UUID contamination** | 0 | 0 | UNCHANGED |
| **gpt-oss-20b UUID contamination** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3 options)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 35/35 per run | 35/35 per run | UNCHANGED |
| **Template leakage** | 0 (spot checks) | 0 (spot checks) | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | Present (from input) | Present (from input) | UNCHANGED |
| **Consequence chain format (→ markers)** | Present in input | Present in input | UNCHANGED |
| **Content depth (field chars vs baseline)** | 0.84–1.52× (no model >2×) | Stable (no model >2×) | WITHIN RANGE |
| **Cross-call duplication** | Not observed | Not observed | UNCHANGED |
| **Over-generation (>7 levers/call)** | Not applicable (no hard cap) | Not applicable | UNCHANGED |
| **Fabricated quantification (% claims)** | Present, all models (pre-existing) | Present, all models (pre-existing) | UNCHANGED (pre-existing) |
| **Marketing-copy language** | Present (echoed from consequences) | Present (echoed from consequences) | UNCHANGED (pre-existing) |
| **OPTIMIZE_INSTRUCTIONS currency** | Stale (PR #457 state undocumented) | Updated by PR #458, accurate for PR #457 residuals | IMPROVED — but now stale again re: PR #458 regression |

**Content quality note (verified from direct file inspection):**

- haiku (run 4/40, silo): synergy/conflict text uses clean name-only references (`"Social Control Mechanism creates significant tension with Ethical Oversight Framework"`). No UUIDs. Quality is good; the 1 error is fabricated-ID noise, not a content problem.
- llama3.1 (run 4/34, sovereign_identity): every lever's synergy/conflict text now includes `"(lever ID: xxx-xxx-xxx)"` patterns for all cross-lever references. Clean run 4/27 output was degraded by the prohibition instruction.
- All other 5 models: identical quality to before — no change from the PR.

**OPTIMIZE_INSTRUCTIONS alignment:**

The OPTIMIZE_INSTRUCTIONS block was updated by PR #458 to document the per-batch UUID vector and haiku's extra-characterization behavior. This is an improvement. However, the block does not yet record that the "Do NOT include UUID" prohibition introduced a regression — making it incomplete relative to the current state. The prohibition instruction text violates the rule documented in `identify_potential_levers.py:80–82` ("Do NOT add explicit prohibitions naming banned phrases"). OPTIMIZE_INSTRUCTIONS in `enrich_potential_levers.py` needs another update to document this lesson.

---

## New Issues

**Introduced by PR #458:**

1. **llama3.1 sovereign_identity UUID regression (N1, B1)**: The `"Do NOT include any Lever ID, UUID"` prohibition names `"Lever ID"` — exactly the format llama3.1 uses. Plans that previously produced clean output (like sovereign_identity in run 4/27 with 0 UUIDs) now produce 20 UUID occurrences. This is an ongoing regression in the current codebase. Net UUID count is unchanged (29 → 29).

2. **haiku silo new error**: silo gained 1 new extra-characterization error (fabricated ID `d890e123-abcd-4567-ef01-234567890abc`) that did not exist in run 4/33. The overall haiku trend is improved (7 → 2), but one previously-clean plan regressed.

**Surfaced by this PR:**

3. **Negative-instruction priming applies cross-file**: The OPTIMIZE_INSTRUCTIONS warning against negative prohibitions naming banned phrases exists only in `identify_potential_levers.py`. This PR demonstrates the same risk applies to `enrich_potential_levers.py`. Both files should be consistent.

---

## Verdict

**CONDITIONAL**: Keep Change 2 (haiku exact-count instruction) — genuine 71% improvement. Revert or replace Change 1 (UUID prohibition) — it introduced an active regression with zero net improvement and violates a documented best practice. Change 3 (OPTIMIZE_INSTRUCTIONS update) is valuable but needs a second update to document the regression from this PR.

The prohibition instruction is counterproductive for llama3.1 and must be replaced with a code-level post-process regex strip (`synergy_text`/`conflict_text` UUID strip after enrichment), which is model-agnostic and prompt-compliance-independent.

---

## Recommended Next Change

**Proposal**: Replace the UUID prohibition in `ENRICH_LEVERS_SYSTEM_PROMPT` with a post-process regex strip of UUID patterns from `synergy_text` and `conflict_text`, optionally supplemented by positive-framing instruction (use name-by-example rather than a do-not rule). Separately, add a pre-filter trim for haiku's remaining 2 extra characterizations.

**Evidence**:

The synthesis Direction 1 recommendation is well-supported:
- The prohibition approach failed and introduced a regression (sovereign_identity 0 → 20 UUIDs). Direct file evidence: `history/4/34_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`.
- `identify_potential_levers.py:80–82` explicitly predicts this failure: "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."
- A regex post-process strip is model-agnostic: it removes `(lever ID: <uuid>)` patterns from synergy/conflict text regardless of what the LLM produces, providing a hard guarantee.
- haiku pre-filter: `batch_result.characterizations[:len(batch)]` before the lever-ID loop cleanly discards fabricated extras. `history/4/40_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` confirms real levers appear first; trimming is safe.

Specific changes:
1. **`enrich_potential_levers.py:178`** — Replace: `"Do NOT include any Lever ID, UUID, or identifier string in these fields."` With positive framing: `"In synergy_text and conflict_text, always refer to other levers by NAME only — for example, write 'Policy Advocacy Strategy' not any identifier or UUID string."`
2. **`enrich_potential_levers.py:279–283`** — Add post-process regex strip after `enriched_levers_map[char.lever_id].update(...)`: compile `r'\(?\s*(?:lever\s+id\s*:\s*)?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*\)?'` (IGNORECASE) at module level; apply to `synergy_text` and `conflict_text`.
3. **`enrich_potential_levers.py:277`** — Add pre-filter before characterization loop: `valid_chars = [c for c in batch_result.characterizations if c.lever_id in enriched_levers_map]`; iterate `valid_chars` instead.
4. **OPTIMIZE_INSTRUCTIONS** — Update to record: (a) prohibition introduced regression; (b) negative do-not rules naming banned phrases are counterproductive for llama3.1; (c) regex strip is the canonical fix.

**Verify**: In the next experiment (all 7 models × 5 plans):
- **llama3.1 sovereign_identity**: Must return to 0 UUID occurrences in synergy/conflict text (was 20 after PR #458). Any non-zero count means the positive-framing instruction is still priming the pattern — the regex strip should catch it regardless.
- **llama3.1 gta_game**: Should maintain near-0 UUID occurrences in synergy/conflict (improved from ~19 to ~0 by PR #458's partial effect). The regex strip will guarantee 0.
- **haiku silo**: Must return to 0 errors (the 1 new error introduced by PR #458). Confirm haiku gta_game and parasomnia remain at 0 errors.
- **haiku hong_kong**: Check whether the 1 residual error is eliminated by the pre-filter. It should be.
- **All models**: Confirm `"errors": []` except for any pre-existing causes. Watch for new `incomplete` errors — the "Return exactly N" instruction could in edge cases cause a model to omit a lever rather than return a partial characterization.
- **gemini, gpt-oss-20b, qwen3, gpt-4o-mini, gpt-5-nano**: Confirm still at 0 UUID occurrences and 0 errors (no regressions from the positive-framing replacement).

**Risks**:

- **Regex over-strip**: The UUID pattern could strip content adjacent to a UUID. Risk is low — synergy/conflict should only contain lever names, not raw UUIDs. The `(lever ID: xxx)` pattern is specific enough to avoid false positives.
- **Positive framing insufficient for llama3.1**: Even with positive framing, llama3.1 may still copy UUIDs. The regex strip is the primary fix; the prompt change is secondary. If the regex strip is implemented, partial prompt non-compliance is benign.
- **Pre-filter masking legitimate under-generation**: If haiku returns fewer characterizations than expected (drops a lever), the pre-filter does not mask it — the missing lever simply remains unenriched and becomes an `incomplete` error downstream. No false silencing.
- **No prerequisite issues**: Both fixes are independent of each other and of pending backlog items.

---

## Backlog

**Resolved by PR #458 (partial):**
- ~~N_haiku_extra_chars~~ (analysis 60 backlog): 7 → 2 errors, –71%. Not fully resolved. Rename to: `N_haiku_extra_chars_residual` — 2 errors remain (hong_kong, silo). Fix: add pre-filter trim (Direction 2 above).

**Updated by PR #458:**
- **N_optimize_stale** (analysis 60 backlog): The OPTIMIZE_INSTRUCTIONS was updated by PR #458 to document per-batch UUID vector and haiku behavior. However, it now needs a second update to record the negative-priming regression from PR #458's prohibition instruction. Status: still open, needs re-update.

**New items from PR #458:**
- **N_llama31_uuid_prohibition_regression** (HIGH PRIORITY, active regression): PR #458 introduced a regression in llama3.1 sovereign_identity (0 → 20 synergy/conflict UUIDs). The prohibition instruction must be replaced with a regex strip + positive framing. Cannot be deferred — it is an active, ongoing regression.
- **N_negative_priming_cross_file** (operational): The OPTIMIZE_INSTRUCTIONS warning against negative do-not prohibitions exists only in `identify_potential_levers.py:80–82`. This lesson should be replicated or cross-referenced in `enrich_potential_levers.py` OPTIMIZE_INSTRUCTIONS to prevent recurrence.

**Still open (carried from analysis 60):**
- **B_uuid_prohibition** → now superseded by `N_llama31_uuid_prohibition_regression` above. Original prompt-based fix failed; replace with code-level regex strip.
- **S_uuid_post_process** (defensive): Post-process regex strip promoted to **primary fix**, no longer deferred.
- **B_id** (content quality): Banned phrases in `Lever.consequences` field description (`identify_potential_levers.py:116–117`). Still open.
- **B5** (operational noise): `partial_recovery` false-alert for normal 2-call completions — `runner.py:131` threshold `< 3` → `< 2`. Still open.
- **N_gpt_oss_slow** (operational): gpt-oss-20b throughput recovered in analysis 61 (5/5). Close or monitor.
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` propagate into all models. Still open.
- **B4_type_annotation** (low impact): `errors: List[Dict[str, Any]] = None` → `Optional[List[Dict[str, Any]]] = None`. Still open.
- **S1_global_dispatcher** (suspect): Shared dispatcher across parallel plan workers. Needs investigation. Still open.
- **S2_main_json_mismatch** (developer tooling): `__main__` block passes wrong JSON shape. Still open.
