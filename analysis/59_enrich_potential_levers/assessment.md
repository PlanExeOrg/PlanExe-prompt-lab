# Assessment: Adaptive batch size, guarded retry, and OpenRouter config fixes for enrich step

## Issue Resolution

**PR #456 targeted six infrastructure problems:**

1. **OpenRouter `context_window` fallback (3,900 for all models)** — RESOLVED.
   All four OpenRouter models now have explicit `context_window` values:
   gpt-oss-20b 131,072 · gemini-2.0-flash 1,048,576 · gpt-4o-mini 128,000 · qwen3-30b 40,960.
   Confirmed via metadata inspection in `history/4/2{1,3,4,5}_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json`.

2. **gpt-oss-20b `max_tokens` overflow (8,192 with cw=3,900 → ~0 input budget)** — RESOLVED.
   `max_tokens` raised to 65,536 (balanced within 131K context). gpt-oss-20b went from 0/5 to 4/5 plans.
   Confirmed: `history/4/21_.../outputs/20250321_silo/002-12-enriched_levers_raw.json` shows `context_window=131072`, `num_output=65536`.

3. **Adaptive batch size** — RESOLVED.
   `SMALL_CONTEXT_THRESHOLD=3000` correctly sits below the OpenRouter fallback (3,900), preventing false positives on the old fallback value. Per-plan batch count dropped from 3–4 to 1–2 (correct for 5–8 levers).

4. **Guarded retry** — RESOLVED (implemented, not triggered in current runs).
   `MAX_RETRY_DEPTH=1` with 300s budget implemented at `enrich_potential_levers.py:283–308`. No `batch_retry` errors observed in any of runs 4/20–26, confirming all batches succeeded on first attempt.

5. **Error tracking in raw output** — RESOLVED.
   New `errors` field (types: `unknown_lever_id`, `incomplete`, `batch_retry`, `batch_skipped`) directly surfaced a pre-existing bug: llama3.1 generates phantom lever IDs in 2/5 plans, causing 3 levers to be silently unenriched (N2).

6. **Accurate `batches_succeeded` counter** — RESOLVED.
   `runner.py` now uses `result.batches_succeeded` instead of hardcoded `1`.

**Residual symptoms:**

- **gpt-oss-20b parasomnia timeout** (N1): gpt-oss-20b timed out on `parasomnia_research_unit` at 600s.
  The gta_game plan already took 243s (vs. 21–47s for other models), indicating model throughput is the bottleneck, not a configuration issue. This plan cannot be completed within the current budget by this model.
  Evidence: `history/4/21_enrich_potential_levers/events.jsonl` — `run_single_plan_error plan=20260311_parasomnia_research_unit error="plan timeout after 600s"`.

- **llama3.1 phantom lever IDs** (N2, pre-existing): 3 levers unenriched across gta_game (2 phantom IDs) and hong_kong_game (1 phantom ID). Caused by llama3.1's non-function-calling JSON generation producing truncated UUIDs (e.g., `056fa843-5572-40a5-bca5-bca5cc18408` — 35 chars, missing last digit). This was invisible before PR #456 added error tracking.
  Evidence: `history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` `errors` field.

---

## Quality Comparison

**Caveat**: analysis 54 used `snapshot/1_deduplicate_levers` (14–18 levers/plan); analysis 59 uses `baseline/train` (5–8 levers/plan). This input mismatch confounds content-quality comparisons. Field-length metrics are compared against `baseline/train` (desc=483, syn=285, conf=298 chars) for the after runs directly. Structural metrics (success rate, context_window, batch count) are comparable across both analyses.

Models in both batches (all 7): llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-flash, haiku.

| Metric | Before (runs 3/85–91) | After (runs 4/20–26) | Verdict |
|--------|----------------------|----------------------|---------|
| **Success rate** | 30/35 (85.7%) | 34/35 (97.1%) | IMPROVED (+11.4pp) |
| gpt-oss-20b success | 0/5 (0%) | 4/5 (80%) | IMPROVED |
| Context window (OpenRouter models) | 3,900 (all 4) | 131K / 1M / 128K / 41K | IMPROVED |
| Batches per plan | 3–4 | 1–2 | IMPROVED |
| Error tracking | Not present | Present (`errors` field) | IMPROVED |
| `batches_succeeded` accuracy | Hardcoded 1 | Actual batch count | IMPROVED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Template leakage (gpt-5-nano "Purpose:")** | 0 (in 3/87 runs) | 1 (gta_game, Resource Allocation Strategy) | Minor regression |
| **Review format compliance ("Controls X vs Y")** | Present in input data (from identify step) | Present (unchanged; B1 unfixed) | UNCHANGED |
| **Consequence chain format (Immediate→Systemic→Strategic)** | Present in input fields | Present in input fields | UNCHANGED |
| **Fabricated % claims in description** | Present (pre-existing) | Present (all 7 models; echoed from `consequences`) | UNCHANGED (pre-existing) |
| **UUID artifacts in synergy/conflict (B3)** | Present (B3 documented, unfixed) | Present (B3 still unfixed) | UNCHANGED (confirmed in 4/20 llama3.1 silo: full UUIDs; 4/22 gpt-5-nano gta_game: 8-char truncated UUIDs) |
| **Marketing-copy language** | Present ("cutting-edge" in input levers) | Present (echoed from `consequences`; "cutting-edge" in gpt-oss-20b conflict_text) | UNCHANGED (pre-existing) |
| **Field length vs baseline (desc ratio)** | Input-confounded | 0.81–1.43× (no model >2×) | WITHIN RANGE |
| **Field length vs baseline (syn ratio)** | Input-confounded | 0.70–1.52× | qwen3-30b at 0.70× (terse) |
| **Field length vs baseline (conf ratio)** | Input-confounded | 0.70–1.50× | qwen3-30b at 0.70× (terse) |
| llama3.1 phantom lever IDs (levers unenriched) | Not tracked (pre-existing) | 3/35 (8.6%) across 2 plans | Surfaced (not new regression) |
| **Cross-call lever duplication** | Not observed | Not observed | UNCHANGED |
| **Over-generation (>7 levers/call)** | N/A (hard cap removed earlier) | N/A | N/A |
| **Guarded retry triggered** | No retry existed | Implemented, not triggered | IMPROVED (safety net added) |

**Content quality note**: The input data mismatch makes direct content comparison unreliable. gpt-oss-20b's newly successful plans show well-grounded descriptions and clean lever-name references in synergy/conflict (no UUID artifacts). Quality for the 4 new completions appears on par with other models. No content regression introduced by PR #456.

---

## New Issues

**Surfaced (pre-existing, not introduced by PR):**

1. **llama3.1 phantom lever IDs** (N2): The error tracking added by this PR made visible that llama3.1 (`is_function_calling_model: false`) generates truncated or corrupted UUIDs in characterization responses. This is a pre-existing silent data-loss channel — 3 levers unenriched across 2 plans — that was invisible before the PR. Not a regression; the PR made it diagnosable.

2. **Fabricated % claims echoed from `consequences` into `description`** (N4): All 7 models echo fabricated percentage claims (e.g., "30% reduction in innovative output", "20% reduction in resource consumption") from the `consequences` field into their enriched descriptions. These originate from the `identify_potential_levers` step. No validator exists at source. Pre-existing; not introduced by PR #456.

**Actually new:**

3. **gpt-5-nano "Purpose:" template reappeared in one plan** (N3): One instance in gta_game, Resource Allocation Strategy. PR #451 eliminated this template for the `snapshot/1_deduplicate_levers` input; its reappearance suggests the suppression is input-dependent, not permanent. May be specific to the gta_game lever set in `baseline/train`.

4. **gpt-oss-20b fundamentally slow for large plans**: gta_game took 243s (vs. 21–71s for other models); parasomnia timed out at 600s. The correct config has exposed that gpt-oss-20b has a throughput limitation that the previous misconfiguration was hiding. The model is not suitable for time-constrained runs on plans with ≥8 levers.

**Confirmed pre-existing but still unresolved:**

5. **B3 — UUIDs in `full_lever_context_str`** (`enrich_potential_levers.py:209`): Confirmed present and causing UUID artifacts in synergy/conflict for llama3.1 (full UUIDs, e.g., `(b35d92a2-c2a2-42e9-9836-eee6bae98898)`) and gpt-5-nano (8-char truncated, e.g., `(056fa843)`). Listed in OPTIMIZE_INSTRUCTIONS since analysis 54. This PR did not address it, and it remains the top content-quality fix.

6. **B1 — Banned phrases in `Lever.consequences` field description** (`identify_potential_levers.py:116–117`): The field description names exact prohibited phrases ("Controls ... vs.", "Weakness:"), directly violating OPTIMIZE_INSTRUCTIONS lines 79–82. Weak models copy these as templates. Most likely cause of gpt-5-nano "Purpose:" template reappearance (N3) and the widespread "Controls X vs. Y. Weakness:" pattern in `review` fields visible in run 4/20–26 outputs.

---

## Verdict

**CONDITIONAL**: The PR delivers the largest single-iteration success-rate gain in this step's optimization history (+11.4pp, recovering gpt-oss-20b from 0% to 80%), correctly fixes all targeted infrastructure issues, and introduces no content regressions. The CONDITIONAL rather than YES reflects two items requiring follow-up before the step can be declared stable:

1. **gpt-oss-20b on large plans**: the model times out at 600s on `parasomnia_research_unit` (8 levers). Options: raise `--plan-timeout` to 900s, add model-specific timeout config, or document gpt-oss-20b as unsuitable for plans with >7 levers. One of these must be chosen before treating 97.1% as the real success floor.

2. **llama3.1 phantom lever IDs**: 3 levers silently unenriched across 2 plans. Root cause (non-function-calling model misformatting UUIDs) needs a mitigation — either a UUID format pre-check at `enrich_potential_levers.py:267` or a schema-enforced lever_id validator — before phantom ID loss is acceptable in production runs.

---

## Recommended Next Change

**Proposal**: Remove lever UUIDs from `full_lever_context_str` in `enrich_potential_levers.py:209`. Change `f"- {lever.lever_id}: {lever.name}"` to `f"- {lever.name}"`. This is a one-line fix that eliminates UUID artifacts in synergy/conflict fields across all models.

**Evidence**: Both agents flag this independently (code_claude B3, synthesis Direction 1). It is the sole unfixed item in OPTIMIZE_INSTRUCTIONS (lines 88–92) that is both confirmed observable and one-line-fixable. Confirmed present in current runs: llama3.1 silo (full UUIDs in parentheses in synergy_text and conflict_text), gpt-5-nano gta_game (8-char truncated UUIDs). The lever_id is already included in the per-batch `lever_details_for_prompt` section so the LLM can still return structured characterizations; the full-context list's only purpose is cross-lever orientation, for which names are sufficient.

**Verify**: After the fix, in runs for all 7 models across all 5 plans:
- Check `synergy_text` and `conflict_text` for all levers: zero occurrences of UUID-format strings (full 36-char or 8-char truncated). Specifically watch: llama3.1 silo and sovereign_identity (previously worst UUID contamination), gpt-5-nano gta_game (previously 8-char truncations), qwen3-30b (previously nondeterministic format).
- Confirm lever references in synergy/conflict are now plain names (e.g., "Information Control Strategy") not `(b35d92a2-...)` or `(b35d92a2)`.
- Confirm `batches_succeeded` still correct (B4 was fixed in this PR; verify unchanged).
- Confirm llama3.1 phantom lever ID rate does not change (since removing UUID exposure may or may not affect ID hallucination — report either way).

**Risks**:
- Near-zero for the one-line change. The lever_id is still in `lever_details_for_prompt` (per-batch section), so the LLM can still match and return characterizations by ID. The only risk is that some model relied on UUID-in-context as a format cue for the characterization return format — unlikely since the batch prompt's per-lever block already supplies `Lever ID:` explicitly.
- Minor risk that removing UUIDs causes some models to make weaker cross-lever references (relying only on names). Watch for any increase in "phantom lever names" (lever names in synergy/conflict that don't exist in the input) — this is a distinct failure mode tracked separately in OPTIMIZE_INSTRUCTIONS.

**Prerequisites**: None. This fix is independent of the pending B1 (banned phrases in `Lever.consequences`) and llama3.1 phantom ID mitigations. It can and should be the next PR.

---

## Backlog

**Resolved by this PR (remove from backlog):**
- ~~B1 (no per-batch retry)~~ → Fixed by guarded retry in PR #456
- ~~B4 (calls_succeeded hardcoded to 1)~~ → Fixed by accurate `batches_succeeded` counter in PR #456
- ~~OpenRouter context_window fallback (3,900 for all models)~~ → Fixed by explicit config in PR #456
- ~~gpt-oss-20b max_tokens overflow~~ → Fixed by PR #456

**Still open (existing backlog):**
- **B3** (content quality): Remove UUIDs from `full_lever_context_str` — `enrich_potential_levers.py:209`. Documented in OPTIMIZE_INSTRUCTIONS since analysis 54. One-line fix. **Highest priority next change.**
- **B_id** (content integrity): Banned phrases in `Lever.consequences` field description (`identify_potential_levers.py:116–117`) violate OPTIMIZE_INSTRUCTIONS lines 79–82. Replace "Do NOT include 'Controls ... vs.', 'Weakness:'" with structural guidance: "Describe direct effects and downstream trade-offs only. Do not include critique or evaluation language."
- **B5** (operational noise): `partial_recovery` false-alert for normal 2-call completions — `runner.py:131` (`< 3` → `< 2`), `runner.py:577` (`expected_calls=3`). Minor but pollutes events.jsonl.
- **D3** (content depth): qwen3-30b synergy/conflict at 0.70× baseline (terse). Add qualitative mechanism guidance to `synergy_text` / `conflict_text` field descriptions: "Name the specific mechanism by which the two levers interact and identify one concrete consequence."
- **S1–S3** (latent concurrency): Closure capture, global dispatcher cross-contamination, unsafe list mutation in runner.py. Not triggered in single-threaded runs.

**New items to add:**
- **N_phantom_id** (data integrity): llama3.1 generates phantom lever IDs (truncated/hallucinated UUIDs) causing 3/35 levers silently unenriched. Root cause: `is_function_calling_model: false` model misformats structured JSON UUIDs. Add UUID format pre-check at `enrich_potential_levers.py:267` to distinguish format-invalid IDs from format-valid but unrecognized IDs. Add OPTIMIZE_INSTRUCTIONS entry distinguishing "phantom lever IDs" (wrong IDs in characterization schema → levers silently dropped) from "phantom lever names" (wrong names in synergy/conflict text).
- **N_pct_claims** (content quality): Fabricated % claims in `consequences` (from identify step) propagate into enriched descriptions for all 7 models. Add `@field_validator` on `Lever.consequences` in `identify_potential_levers.py` to detect `\d+%` or `\d+x\b` patterns and log a warning-level metric.
- **N_gpt_oss_slow** (operational): gpt-oss-20b throughput too low for ≥8-lever plans (gta_game 243s, parasomnia timeout at 600s). Decide: raise `--plan-timeout` to 900s, add model-specific timeout, or mark gpt-oss-20b as non-production-grade for plans with >7 levers.
- **N_input_mismatch** (methodology): Future iterations must use consistent input (`baseline/train` or `snapshot/1_deduplicate_levers`) to enable clean before/after content comparisons. Consider updating the snapshot to match `baseline/train`.
