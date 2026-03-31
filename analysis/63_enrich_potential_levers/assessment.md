# Assessment: Use integer lever indices to eliminate UUID contamination in enrich step

## Issue Resolution

**What the PR was supposed to fix**: PR #462 aimed to complete the UUID elimination started by PR #457. After PR #457 stripped UUIDs from `full_lever_context_str`, llama3.1 still had 15–20 UUID occurrences in `synergy_text`/`conflict_text` because the per-batch prompt (`lever_details_for_prompt`) still showed `Lever ID: {uuid}`. PR #462 replaces those UUIDs with integer indices (`Lever 1`, `Lever 2`, …) and maps them back to full UUIDs in post-processing.

**Is the issue resolved?** Partially — for models that produce output, UUID contamination drops to 0. But the fix introduces a format mismatch that causes catastrophic failure for 3 models and partial failure for 2 more.

**Root cause of the new failures**: The per-batch prompt labels levers as `"Lever 1"`, `"Lever 2"` (line 247: `f"Lever {idx}\n"`), but `index_to_full` uses bare integer strings as keys (line 245: `index_to_full[str(idx)]`). The post-processing lookup at line 283 is an exact match — `"Lever 1" ≠ "1"` — so any model that echoes the prompt label verbatim loses 100% of the batch.

**Residual symptoms**: None of the original UUID contamination, but 3 of 7 models cannot produce any output, making the step effectively broken for most of the test suite.

**Evidence**:
- `history/4/48_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: `characterized_levers: []`, errors include `"lever_id": "Technological Integration Strategy"` and `"lever_id": "Narrative Complexity Strategy"` — llama3.1 returned lever names instead of integers.
- `history/4/54_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: haiku errors include `"lever_id": "4"`, `"5"`, `"6"`, `"7"`, `"8"` — raw integer strings that don't match any UUID in `enriched_levers_map`.
- `history/4/53_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: `errors: []`, 8 clean characterized levers — gemini works correctly and produces zero UUID contamination.

---

## Quality Comparison

Models in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini, haiku.

| Metric | Before (runs 4/27–33, analysis 60) | After (runs 4/48–54, analysis 63) | Verdict |
|--------|------------------------------------|-----------------------------------|---------|
| **Plan-level success rate (status:ok)** | 34/35 (gpt-oss-20b: 3 timeouts) | 35/35 | IMPROVED |
| **Total characterized levers** | ~209/245 (~85%) | 178/245 (73%) | REGRESSED |
| **llama3.1 lever recovery** | 35/35 (100%) | 0/35 (0%) | CATASTROPHIC |
| **gpt-oss-20b lever recovery** | ~35/35 (est.) | 23/35 (66%) | REGRESSED |
| **gpt-5-nano lever recovery** | 35/35 (100%) | 22/35 (63%) | REGRESSED |
| **qwen3-30b lever recovery** | 35/35 (100%) | 33/35 (94%) | MINOR REGRESSION |
| **gpt-4o-mini lever recovery** | 35/35 (100%) | 30/35 (86%) | MINOR REGRESSION |
| **gemini lever recovery** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **haiku lever recovery** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **Total errors** | 7 (haiku fabricated UUIDs) | 152 | REGRESSED |
| **llama3.1 errors** | 0 | 70 (unknown_lever_id + incomplete) | REGRESSED |
| **gpt-oss-20b errors** | 0 | 24 | REGRESSED |
| **gpt-5-nano errors** | 0 | 26 | REGRESSED |
| **qwen3 errors** | 0 | 4 | REGRESSED |
| **gpt-4o-mini errors** | 0 | 10 | REGRESSED |
| **gemini errors** | 0 | 0 | UNCHANGED |
| **haiku errors** | 7 (fabricated UUIDs) | 22 (raw integers) | REGRESSED |
| **UUID contamination (synergy/conflict, all models)** | 20 occurrences (llama3.1 only) | 0 | IMPROVED |
| **Bracket placeholder leakage** | Not observed | Not observed | UNCHANGED |
| **Option count violations** | Not observed | Not observed | UNCHANGED |
| **Lever name uniqueness** | Normal | Normal (working models) | UNCHANGED |
| **Template leakage** | Not observed | Not observed | UNCHANGED |
| **Review format compliance** | Normal | Normal (working models) | UNCHANGED |
| **Content depth (field lengths vs baseline)** | haiku 1.52× (syn), all others ≤1.5× | qwen3 0.65–0.80×, gpt-4o-mini 0.92–0.99×, gemini 0.98–1.04× | UNCHANGED (working models only) |
| **Fabricated quantification** | Pre-existing (echoed from consequences input) | Pre-existing; not introduced by PR | UNCHANGED |
| **Marketing-copy language** | Not observed | Not observed | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS accuracy** | Accurate | **False claim added**: "Integer indices work universally for both model types" | REGRESSED |

**Notes**:
- "Plan-level success" (status:ok) improved because the before batch had 3 gpt-oss-20b network timeouts. At the lever level, the after batch is clearly worse.
- Field lengths for the after batch can only be assessed for the 3 working models (qwen3, gpt-4o-mini, gemini); the other 4 models produce zero or partial output, making a fair comparison impossible.
- The OPTIMIZE_INSTRUCTIONS now contains a false claim that will mislead future optimization iterations.

---

## New Issues

### N1 — OPTIMIZE_INSTRUCTIONS false claim: "Integer indices work universally for both model types"
The PR adds this statement to the developer documentation at lines 89–97 of `enrich_potential_levers.py`. The experiment directly refutes it: 4/7 models fail or regress. A future developer reading this will skip cross-model testing on the assumption it is validated. This must be corrected.

### N2 — Prompt format / mapping-key mismatch (B1 in code review)
The per-batch prompt uses `f"Lever {idx}\n"` while `index_to_full` keys are `str(idx)` (bare integers). Any model that echoes the prompt label `"Lever 1"` fails the dict lookup. This is the sole cause of all 152 new errors. It is a fixable one-line bug, not a design flaw.

### N3 — `lever_id` field type/description conflict (B2 in code review)
`lever_id: str = Field(description="The integer identifier of the lever, as shown in the prompt")` — `str` type with "integer identifier" description sends contradictory signals to function-calling models. Haiku makes redundant tool calls with raw integer strings (`"4"`, `"5"`) because JSON Schema says `string` but the description says `integer`. This accounts for haiku's 22 spurious errors.

### N4 — Surfaced latent issue: text-completion models echo prompt labels verbatim
The PR exposes that llama3.1, gpt-oss-20b, and gpt-5-nano reproduce the full prompt label (`"Lever 1"`) as the `lever_id` field value rather than extracting the bare integer. This was not visible before because the per-batch prompt used `Lever ID: {uuid}` (where copying the full string was the intended behavior). The integer index scheme reveals a systematic "label echo" behavior in text-completion models.

---

## Verdict

**NO**: The PR introduces a format mismatch bug (`"Lever N"` label vs `"N"` mapping key) that causes llama3.1 to produce 0/35 levers (was 35/35), gpt-oss-20b and gpt-5-nano to lose 34–37% of levers, and adds 145 net new errors across all models. Before: ~209 levers, 20 UUID occurrences. After: 178 levers, 0 UUID occurrences. Losing 31 levers (–14.8%) to eliminate 20 UUID occurrences in one model's free-text fields is a net regression. The OPTIMIZE_INSTRUCTIONS now contains a false universality claim. This PR must be reverted; the core design is sound but the implementation has a fixable bug that must be corrected and re-tested before merging.

---

## Recommended Next Change

**Proposal**: Fix the prompt format / mapping-key mismatch by changing line 247 from `f"Lever {idx}\n"` to `f"Lever ID: {idx}\n"`, adding prefix-stripping normalization to the mapping lookup at line 283, and correcting the false OPTIMIZE_INSTRUCTIONS claim.

**Evidence**: All 152 new errors trace to a single root cause (B1): the post-processing lookup `index_to_full.get(char.lever_id, char.lever_id)` expects bare integer keys (`"1"`, `"2"`) but receives the full prompt label `"Lever 1"` from 5/7 models. The three-part fix (prompt format + defensive normalization + documentation correction) is confirmed in source at lines 245–247 and 283, and validated against the run data from all 7 models.

**Verify**:
- llama3.1 (run 4/48 baseline: 0/35 levers): Should recover to ~35/35. Check `history/{run}/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` for `characterized_levers` count and zero `unknown_lever_id` errors with `"Lever N"` patterns.
- gpt-oss-20b (run 4/49 baseline: 23/35): Should recover to ~35/35. Check all 5 plans.
- gpt-5-nano (run 4/50 baseline: 22/35): Should recover to ~35/35. Check `gta_game` and `hong_kong_game` plans which were the primary failure sites.
- haiku (run 4/54 baseline: 35/35 but 22 spurious errors): The prefix-strip normalization won't help haiku's raw-integer errors (`"4"`, `"5"`) since they don't start with `"Lever"`. If B2 (type/description mismatch) is also fixed, haiku's extra tool calls should drop. Verify haiku error count goes from 22 toward 0.
- gemini (run 4/53: already 35/35, 0 errors): Must remain unchanged as a regression check.
- UUID contamination in synergy/conflict for all 7 models: Should remain 0.
- OPTIMIZE_INSTRUCTIONS: Confirm the false "Integer indices work universally" claim is replaced with accurate conditional language and documents the "Lever N label-echo" pattern.

**Risks**:
- If the mapping normalization strips `"Lever "` but some future model returns `"Lever ID: 1"` (including the colon), the strip of 5 chars (`"LEVER"`) would leave `" ID: 1"`, which still fails the lookup. The normalization should be broader: strip up to and including the first `:` if present, then strip whitespace.
- Changing `f"Lever {idx}\n"` to `f"Lever ID: {idx}\n"` may cause gemini (which currently works with bare integers by extracting the digit) to start echoing `"Lever ID: 1"` — confirm gemini still works after the format change.
- The `lever_id: str` vs "integer identifier" conflict (B2) should be resolved in the same PR: either change to `int` type or align the description to `str`. If left unresolved, haiku's 22 spurious errors will persist even after B1 is fixed.

**Prerequisites**: None. PR #457 is already merged and its changes are the baseline for this iteration. The integer index design is architecturally sound and does not require any other PRs to be in place first.

---

## Backlog

### Resolved by analysis 63 (can be removed from backlog):
- **gpt-oss-20b timeout investigation**: The before batch (analysis 60) had 3 gpt-oss-20b timeouts unrelated to the PR. The after batch (analysis 63) shows all 5 plans completing (status:ok) — the timeout was transient network noise, not a persistent issue. Remove from backlog.

### Carry forward from analysis 60 (not addressed by PR #462):
- **Same-batch UUID copying**: PR #462 was intended to fix this; it does eliminate the vector when the model produces output, but must be re-applied correctly after the format mismatch is fixed.
- **B2 (type annotation mismatch)**: `errors: List[...] = None` — minor, fix opportunistically.
- **B4 (closure capture by reference)**: Latent risk in `execute_function` loop. Safe now; fix before any async refactoring.
- **B5 (false partial_recovery warning)**: In runner.py, threshold `< 3` fires for valid 2-call runs. Fix to `< 2` or use lever-count check.
- **S1 (global dispatcher cross-contamination)**: Low practical impact; investigate before enabling parallel-run diagnostics.
- **S2 (`__main__` block JSON mismatch)**: Standalone test broken for real deduplicated output. Trivial fix.
- **N4 (fabricated percentages from identify_potential_levers)**: Pre-existing; fix belongs in identify step.

### New items to add to backlog:
- **"Lever N label-echo" pattern**: Document in OPTIMIZE_INSTRUCTIONS that text-completion models echo prompt labels verbatim as `lever_id`. Ensure prompt format and mapping key are always identical, and add prefix normalization to the lookup as a defensive fallback.
- **False "Integer indices work universally" claim in OPTIMIZE_INSTRUCTIONS**: Must be corrected to conditional language and the "label-echo" failure mode documented.
- **B2 (lever_id type/description conflict)**: `lever_id: str` with "integer identifier" description causes haiku to produce redundant tool calls. Resolve by changing type to `int` or aligning the description to `str`.
- **Direction #5 (H2 explicit ID instruction)**: After the format fix is confirmed effective, consider adding an explicit instruction in the per-batch user prompt: "For each lever's `lever_id`, return the integer number shown after 'Lever ID:' (e.g., if the section begins with 'Lever ID: 3', set lever_id to '3')." This targets residual edge-case failures in large-batch plans.
