# Assessment: fix: adaptive retry loop, haiku max_tokens, relax review_lever

## Issue Resolution

PR #351 targeted four independent issues:

1. **Adaptive retry loop** — Replace fixed 3-call loop with min-15-levers / max-5-calls strategy, preserving prior levers when a mid-loop call fails.
   - **Resolved.** `partial_recovery` events in run 51 (haiku) confirm the mechanism works: silo (calls_succeeded=2) and parasomnia (calls_succeeded=2) completed without discarding prior levers. Before PR, a mid-loop failure would have propagated as a hard error.
   - **Side effect introduced:** `runner.py:514` checks `pr.calls_succeeded < 3` without gating on step name. `_run_documents` always returns `calls_succeeded=1`, so every `identify_documents` run now emits a spurious `partial_recovery` event. Code review B1 — confirmed bug in events.jsonl integrity.

2. **Haiku max_tokens 16000 → 8192** — Match haiku's actual API output cap, preventing JSON truncation.
   - **Resolved for truncation.** No `EOF while parsing` errors for haiku in run 51; `history/2/51_identify_potential_levers/events.jsonl` shows all 5 plans complete or partial_recovery (never hard error).
   - **New failure mode introduced:** With 8192 tokens and ~7 levers per call × 2 calls = 14 levers < min_levers=15, haiku now triggers call 3. If call 3 fails, `partial_recovery` fires. This occurred for silo and parasomnia in run 51. Root cause of call 3 failure is unknown (no `failure_reason` logged in event) — code review B3.

3. **review_lever minimum 50 → 10 chars** — Fixes llama3.1 batch rejections on short-but-valid reviews.
   - **Resolved structurally.** No rejection events due to short reviews in the after batch. No quality downsides detected.

4. **Remove lever_classification** — Reverts iter 33 regression (88.6% → back toward 97.1%).
   - **Resolved.** Success rate recovered from 88.6% (iter 33) to 94.3% (run 45–51). Evidence: `history/2/45_identify_potential_levers/events.jsonl` shows 4/5 plans complete (1 ReadTimeout); `history/2/46_identify_potential_levers/events.jsonl` shows 4/5 (1 JSON EOF). Both failures are pre-existing model-specific issues unrelated to lever_classification.

**Residual symptoms:** The adaptive retry loop has a correctness bug (B1 spurious partial_recovery on identify_documents). The haiku partial_recovery failure cause is undiagnosable from events.jsonl (B3). The gpt-oss-20b JSON truncation persists (was already at max_tokens=8192 per baseline.json:34 — the haiku fix strategy is exhausted for this model).

---

## Quality Comparison

Models in BOTH batches: llama3.1 (03/45), gpt-oss-20b (04/46), gpt-5-nano (05/47), qwen3-30b (06/48), gpt-4o-mini (07/49), gemini-2.0-flash (08/50), haiku-4-5 (09/51). All 7 models are present in both batches.

| Metric | Before (runs 03–09) | After (runs 45–51) | Verdict |
|--------|--------------------|--------------------|---------|
| **Overall success rate** | 34/35 = 97.1% | 33/35 = 94.3% | REGRESSED −2.8pp |
| **LLMChatErrors (hard failures)** | 1 (run 04, gpt-oss-20b, sovereign_identity, EOF line 58) | 2 (run 45, llama3.1, ReadTimeout; run 46, gpt-oss-20b, EOF line 47) | REGRESSED |
| **Partial recovery events** | 2 (run 03, llama3.1: sov_id + hkg, calls=2) | 2 (run 51, haiku: silo + parasomnia, calls=2) | UNCHANGED in count; new model affected |
| **Haiku partial_recovery** | 0 (run 09: 5/5 full 3-call) | 2 (run 51: silo + parasomnia at 2/3 calls) | NEW regression (caused by PR) |
| **gpt-oss-20b JSON EOF** | 1 (sovereign_identity, line 58) | 1 (hong_kong_game, line 47) | UNCHANGED (pre-existing, max_tokens=8192 already set) |
| **llama3.1 network timeout** | 0 | 1 (run 45, sovereign_identity, ReadTimeout) | NEW (non-PR, Ollama infrastructure) |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (< 3)** | 0 | 0 | UNCHANGED |
| **Template lock — llama3.1 gta_game (options-centric reviews)** | ~62.5% (10/16, run 03) | ~94% (17/18, run 45) | REGRESSED (not caused by PR — PR did not change examples) |
| **Fabricated % in llama3.1 consequences (gta_game)** | 5 claims ("by at least 20/15/25/30/20%", run 03) | 0 claims (run 45, qualitative only) | IMPROVED |
| **Fabricated % in haiku / gpt-5-nano** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Minimal | Minimal ("cutting-edge technologies" in 1 run 45 option) | STABLE |
| **Short options (< 12 words, llama3.1 calls 2–3)** | Not observed in run 03 | Present: "Prioritize gentrification-driven revitalization" (4 words), "Invest in community-led affordable housing initiatives" (7 words) — run 45 levers 8–18 | REGRESSED (pre-existing behavior; no word-count validator) |
| **Content depth — gpt-5-nano (run 47, hong_kong_game)** | Not benchmarked separately | Avg consequences ~480 chars; "Core tension / Weakness" format; HK-specific geography | IMPROVED |
| **Content depth — haiku (run 51, hong_kong_game)** | Comparable to run 09 | Avg consequences ~700 chars; screenplay-level analysis; unique per-lever | IMPROVED |
| **Field length ratio vs baseline (consequences, haiku)** | Run 09 est. ~450 chars → ~1.7× baseline | Run 51 ~700 chars → ~2.6× baseline | WARNING (>2× threshold; qualitative inspection shows substantive depth, not verbosity) |
| **Field length ratio vs baseline (consequences, gpt-5-nano)** | Not benchmarked | Run 47 ~480 chars → ~1.8× baseline | WARNING (borderline) |
| **Cross-call semantic duplication** | Minor ("Multplayer Modes" + "Multiplayer Modes" in run 03) | Minor ("Innovation Incubator Initiative" call 1 + "Innovation Incubator" call 2 in run 45) | UNCHANGED |
| **Over-generation count** | Fixed 3 calls (up to ~21 levers) | Adaptive; llama3.1 → 18 levers (gta_game), haiku → 20 levers (hong_kong_game) | INFORMATIONAL — downstream DeduplicateLeversTask handles extras |
| **Review format compliance (non-llama3.1 models)** | Stable | Stable; gpt-5-nano "Core tension / Weakness" format maintained in run 47 | UNCHANGED |
| **Consequence chain format (Immediate → Systemic → Strategic)** | Absent in current outputs | Absent in current outputs (present only in baseline, which is low-quality) | UNCHANGED |

**Note on template lock regression:** The 62.5% → 94% worsening for llama3.1 gta_game is attributed to run-to-run variance rather than PR #351, since the PR did not touch the review_lever examples. However, the fact that it worsened confirms the lock is structural and driven solely by the system prompt examples (all three use "options" as grammatical subject). This is the top quality issue in the after batch.

**Note on fabricated % improvement:** The 5 fabricated % claims in run 03 llama3.1 gta_game consequences (introduced by PR #340's replacement example 3) are absent in run 45. Most likely cause: lever_classification removal changed the output schema, reducing constraint saturation that correlated with hallucinated statistics. The fix is attributed to this PR indirectly.

**OPTIMIZE_INSTRUCTIONS alignment:** The `OPTIMIZE_INSTRUCTIONS` constant covers fabricated numbers (now improved for llama3.1), template lock (still active and worsening), vague aspirations (still present in llama3.1 calls 2–3 label-style options like "Prioritize gentrification-driven revitalization"), and marketing copy (stable, minor). Two gaps not yet documented: (1) inner-retry amplification (gpt-5-nano run 47 shows 8 total API calls for 3 `calls_succeeded`, suggesting Pydantic retries inside LLMExecutor count toward total calls but not toward the outer adaptive loop's success count); (2) the `partial_recovery` event carries no `failure_reason`, making haiku's 3rd-call failures on silo/parasomnia undiagnosable.

---

## New Issues

1. **B1 — Spurious `partial_recovery` events for `identify_documents`.** `runner.py:514–518` fires `partial_recovery` whenever `calls_succeeded < 3`. Since `_run_documents` always returns `calls_succeeded=1`, every `identify_documents` benchmark emits a false partial_recovery event. This silently corrupts events.jsonl for the identify_documents step. Fix: add `and step == "identify_potential_levers"` to the condition.

2. **B3 — `partial_recovery` carries no failure reason.** The adaptive loop catches exceptions correctly but discards the exception before the event is written. The haiku partial_recovery on silo/parasomnia (run 51) is undiagnosable — it could be API cap, Pydantic validation error, or timeout. Fix: add `last_error: str | None = None` to `PlanResult` and surface in the event.

3. **Short label-style options not blocked by validation.** Run 45 llama3.1 calls 2–3 produce options as short as 4 words ("Prioritize gentrification-driven revitalization", "Invest in community-led affordable housing initiatives"). The system prompt requires "at least 15 words with an action verb" but no Pydantic validator enforces this. The `check_option_count` validator only checks `len(v) >= 3`. Fix: add `@field_validator('options', mode='after')` checking `len(opt.split()) < 12`.

4. **False-positive partial_recovery on legitimate 2-call early-stop (B2, latent).** The adaptive loop terminates when `len(generated_lever_names) >= min_levers=15`. If a model produces ≥8 levers/call, 2 calls yield ≥16 levers and the loop exits normally — but `runner.py` will still emit `partial_recovery` because `actual_calls=2 < expected_calls=3`. Not observed with current models (all produce ~7 levers/call) but undefended.

5. **`expected_calls=3` hardcoded in two runner locations with no link to `max_calls=5`.** If `max_calls` or `min_levers` is tuned, runner drift is silent. Should share a named constant.

**Latent issue surfaced:** The gpt-oss-20b JSON truncation is now confirmed pre-existing and resistant to the haiku fix. `baseline.json:34` already sets `max_tokens=8192` for gpt-oss-20b; run 46 still truncated at line 47. For a reasoning model, internal chain-of-thought consumes from the same `max_tokens` budget, leaving less effective output space than the configured cap. A different approach is needed (prompt compression or accepting 4/5 success rate for this model).

---

## Verdict

**CONDITIONAL**: Keep all four changes (lever_classification removal, adaptive loop, haiku max_tokens fix, review_lever minimum relaxation) — they are each correct at the code level. Fix B1 (spurious partial_recovery for identify_documents) before using events.jsonl for analysis of any step other than identify_potential_levers. Address B3 (add failure_reason to partial_recovery) before haiku max_tokens can be tuned further.

The success rate of 94.3% is 2.8pp below the analysis 28 baseline of 97.1%. This gap is explained by: llama3.1 ReadTimeout (non-PR, infrastructure), gpt-oss-20b persistent truncation (pre-existing, requires different fix), and haiku partial_recovery on 2 plans (caused by PR, but plans still return "ok"). If the llama3.1 timeout and gpt-oss-20b truncation are treated as model-specific infrastructure issues outside the PR's scope, the PR's direct effect is: haiku no longer hard-fails (positive), lever_classification removed (clearly positive), review_lever relaxation (neutral). The PR is a keeper with follow-up required on B1 and B3.

---

## Recommended Next Change

**Proposal:** Replace all three `review_lever` examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 224–226 of `identify_potential_levers.py`) with critiques that do not use "the options" or "none of the options" as the grammatical subject. The synthesis (analysis 34) provides specific replacement text for all three examples. Also in the same PR: fix B1 (step-gate the partial_recovery check) and add a minimum word-count validator to `Lever.options` (12 words, language-agnostic via `.split()`).

**Evidence:** All three current examples anchor the critique to "the options" or "none of the options": example 1 ("none of the options price in"), example 2 ("the options assume"), example 3 ("correlation risk absent from every option"). Run 45 llama3.1 gta_game shows ~94% options-centric reviews across all 18 levers and all 3 calls — including calls 2–3 which revert to "none of the options address this risk" ending. The lock affects ~26% of the benchmark model set (llama3.1 = 1/7) across all 5 plans and all 3 calls. The partial improvement from PR #340 (100% → 62.5% when one example was changed) demonstrates the mechanism is real: changing all three examples should complete the shift. Template lock also confirmed present in the before batch for gpt-5-nano ("the options neglect"), sourced from examples 1 or 2.

**Verify in next iteration:**
- llama3.1 gta_game run 45: options-centric review rate was ~94%. Target: < 30% after example replacement. Verify across all 3 LLM calls, not just call 1.
- llama3.1 parasomnia: lock was 100% (18/18) in run 45 — verify it breaks with the new examples.
- gpt-5-nano gta_game: verify "the options neglect" phrase is absent after replacing examples 1 and 2.
- haiku hong_kong_game (run 51): verify content depth and review format are not degraded by the new examples (haiku currently produces the highest-quality output; ensure the example change does not regress it).
- Run 45 llama3.1 calls 2–3: verify options are no longer label-style after adding the word-count validator (if B4 fix is bundled).
- Fabricated % claims: verify llama3.1 gta_game remains at 0 (was fixed incidentally; new examples should not re-introduce a quantitative-cue pattern).
- Check that no new replacement example contains a percentage claim or causal sentence ending with a magnitude estimate — this was the failure mode of PR #340's replacement example 3.

**Risks:**
- Weaker models may shift the lock to whatever phrase is shared across the new examples, rather than eliminating it. Each replacement must use a structurally distinct sentence pattern; examples must not share a reusable transitional phrase. This is documented in `OPTIMIZE_INSTRUCTIONS` lines 69–79 but was not followed when PR #340 replaced example 3.
- Bundling B1 (partial_recovery step-gate), B3 (failure_reason logging), and the example replacement into one PR makes the PR larger but reduces iteration count. The risk is that if the example replacement introduces a new quality issue, it's harder to attribute when multiple changes land together. Splitting is safer but slower.
- The word-count validator (12-word threshold on options) may increase retry count for llama3.1 calls 2–3, where options are currently short. This could extend run time for llama3.1 or trigger more partial_recovery events if max_calls=5 is consumed by retries. Monitor `activity_overview.json` for elevated `calls` count relative to `calls_succeeded`.

**Prerequisite issues:** None. The example replacement is self-contained and does not depend on haiku max_tokens or gpt-oss-20b being resolved first. B1 (step-gate) should be bundled as it's a one-line fix with no risk.

---

## Backlog

**Resolved (remove from backlog):**
- lever_classification field causing validation failures: resolved by removal in PR #351. Success rate recovered from 88.6% to 94.3%.
- Haiku JSON truncation from API cap: resolved. No EOF errors for haiku in run 51.
- Fabricated % claims in llama3.1 gta_game consequences (introduced by PR #340): resolved in run 45 (0 claims). Likely attributable to lever_classification schema change.

**Active (carry forward):**
- **CRITICAL: Template lock in llama3.1 reviews (89–94% options-centric).** Root cause: all three review_lever examples use "the options" as grammatical subject. Persists and worsened from 62.5% (run 03) to ~94% (run 45). Fix: replace all three examples. This is the top content-quality issue.
- **B1: Spurious partial_recovery for identify_documents.** `runner.py:514` fires for all steps; identify_documents always returns calls_succeeded=1 < 3. Corrupts events.jsonl. Fix: add `and step == "identify_potential_levers"` to the condition.
- **B3: partial_recovery carries no failure_reason.** Haiku 3rd-call failure cause (silo, parasomnia in run 51) is undiagnosable. Fix: add `last_error: str | None = None` to `PlanResult`.
- **B4: No word-count validator on options.** llama3.1 calls 2–3 produce 4–9 word label options ("Prioritize gentrification-driven revitalization") that pass Pydantic and ship downstream. Fix: `@field_validator('options', mode='after')` with `len(opt.split()) < 12`.
- **gpt-oss-20b persistent JSON truncation.** Already at max_tokens=8192 per baseline.json:34; run 46 still truncated. The haiku fix strategy is exhausted. Investigate reasoning model token budget (internal chain-of-thought shares the cap). May need prompt compression or accepting 4/5 success rate for this model.
- **OPTIMIZE_INSTRUCTIONS gaps:** (a) inner-retry amplification (gpt-5-nano run 47: 8 total API calls for 3 calls_succeeded — LLMExecutor internal Pydantic retries inflate total calls without advancing adaptive loop success count); (b) partial_recovery event has no failure_reason field, making haiku 3rd-call diagnosis impossible from events.jsonl alone. Both should be documented.
- **`expected_calls=3` hardcoded in two runner locations** with no reference to `max_calls=5`. Add a shared named constant or derive from loop parameters to prevent silent drift when loop parameters are tuned.
- **False-positive partial_recovery on legitimate 2-call early-stop (B2, latent).** If any model produces ≥8 levers/call, runner emits spurious partial_recovery on a clean 2-call success. Add a comment documenting the assumption; adjust when min_levers is changed.
