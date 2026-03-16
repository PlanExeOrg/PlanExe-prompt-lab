# Assessment: Add options count and review format validators to Lever

## Issue Resolution

**What the PR was supposed to fix:** PR #289 added two Pydantic `field_validator` entries to the
`Lever` model in `identify_potential_levers.py`:

1. `check_option_count` — reject levers where `len(options) != 3`
2. `check_review_format` — reject `review_lever` strings missing either `"Controls "` or
   `"Weakness:"` substrings

These were identified as Direction 1 in analysis/12 synthesis after run 89 (llama3.1,
hong_kong_game) produced 3 levers with only 2 options and 7 levers with malformed `review_lever`
fields, all of which silently shipped to the final `002-10-potential_levers.json` artifact.

**Is the issue resolved?** Yes, completely.

- **Option count violations in shipped artifacts:** 3 (run 89) → 0 (all post-PR successful
  runs). Confirmed: no lever with != 3 options appears in any successful artifact in runs 95–1/01.
- **Review format violations in shipped artifacts:** 7 (run 89) → 0. Confirmed: no lever missing
  `Controls` or `Weakness:` appears in any successful artifact.
- **Validators firing on real violations:** `check_review_format` caught llama3.1's systematic
  pattern in run 95 — 9 violations in silo (90.47 s), 8 in gta_game (32.69 s), confirmed in
  `history/0/95_identify_potential_levers/events.jsonl`. All 9 silo levers alternate between
  Controls-only (`"Controls Cost vs. Scalability."`) and Weakness-only (`"Weakness: The options
  fa..."`) — never combining both, exactly as the validator requires.
- **`check_option_count` caught haiku in run 1/01:** `"levers.7.options: options must have
  exactly 3 items, got 7 [input_value=['Assign residents to pri...wed. Removing Lever 8.']]"`,
  confirmed in `history/1/01_identify_potential_levers/events.jsonl`, 2026-03-16T01:02:52Z.

**Residual symptoms:** The validators fire at `DocumentDetails` parse time, which validates the
entire `list[Lever]` as a unit. A single invalid lever fails the whole `DocumentDetails`, which
combined with the pre-existing B1 partial-result-loss bug (`identify_potential_levers.py:231–240`)
causes **total plan failures** instead of individual lever rejections. This cascade was explicitly
predicted as a risk in analysis/12 `assessment.md` (Risks section) and has materialized.
Specifically: run 95 silo and gta_game produce **zero output levers** despite generating
9+ levers before failing; run 1/01 haiku silo produces zero output despite valid levers from
other calls. This is a consequence of deploying Direction 1 without Direction 2 (partial result
recovery), not a flaw in the validators themselves.

---

## Quality Comparison

**Models in both batches:** llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, haiku.
**Before-only models:** nemotron (0/5 structural failure), gpt-4o-mini.
**After-only models:** gemini-2.0-flash (5/5, 5/5).

The overall success rate (28/35 → 31/35) is inflated by the nemotron → gemini swap. The
shared-model rate (92% → 84%) is the more meaningful comparison — both regressions represent
validators working correctly, not independent quality degradation.

Quantitative figures from `analysis/13_identify_potential_levers/insight_codex.md` aggregate
metrics table, cross-verified against `insight_claude.md` run-by-run breakdown and sampled
artifact reads.

| Metric | Before (runs 88–94) | After (runs 95–1/01) | Verdict |
|--------|---------------------|----------------------|---------|
| **Overall success rate** | 28/35 (80.0%) | 31/35 (88.6%) | INFLATED — model swap effect |
| **Shared-model success rate** | 23/25 (92%) | 21/25 (84%) | REGRESSED −2 (validators working correctly) |
| — llama3.1 | 4/5 | 3/5 | REGRESSED −1 (`check_review_format` cascade) |
| — gpt-oss-20b | 4/5 | 4/5 | UNCHANGED (different plan fails, unrelated) |
| — gpt-5-nano | 5/5 | 5/5 | UNCHANGED |
| — qwen3 | 5/5 | 5/5 | UNCHANGED |
| — haiku | 5/5 | 4/5 | REGRESSED −1 (`check_option_count` cascade) |
| **Option count violations in artifacts** | 3 (run 89, hong_kong_game) | **0** | **FIXED** |
| **Review format missing `Controls`** | 4 (run 89) | **0** | **FIXED** |
| **Review format missing `Weakness:`** | 3 (run 89) | **0** | **FIXED** |
| **Plans silently shipping malformed levers** | ≥1 | **0** | **FIXED** |
| **Validator-caused plan failures** | 0 | 3 (runs 95×2, 1/01×1) | NEW — intended effect, B1 cascade |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Template leakage (Conservative:/Moderate:/Radical:)** | 0 cells | 20 cells | REGRESSED (new; see New Issues) |
| **Reviews not in exact `Controls … vs. … Weakness: …` shape** | 78/514 (15.2%) | 71/563 (12.6%) | IMPROVED slightly (validators blocking worst cases) |
| **Consequences missing measurable outcome** | 61/514 | 56/563 | IMPROVED slightly |
| **qwen3 consequence contamination** | ~71/514 (13.8%) | ~71/563 (12.6%) | UNCHANGED (flat in count) |
| **Total merged levers captured** | 514 | **563** | IMPROVED (+49, more successful plans) |
| **Lever name uniqueness ratio** | 0.998 | 0.991 | UNCHANGED within noise |
| **Avg consequence chars** | 414.1 | 412.5 | UNCHANGED |
| **Avg option chars** | 135.6 | 136.5 | UNCHANGED |
| **Cross-call duplicate raw lever names** | 10 (after PR#286) | not separately reported | UNCHANGED |
| **Over-generation** (raw responses >7 levers) | 3 (runs 89×2, 94×1) | not separately counted | INFORMATIONAL |

**Note on the shared-model regression:** The two lost plans (llama3.1 silo, haiku silo) both
represent the validators catching genuine violations. Before the PR, these plans "succeeded" by
shipping malformed data. The regression in success rate is a data-integrity improvement expressed
as plan-level failures due to the unresolved B1 cascade bug. The correct fix is Direction 2
(partial result recovery), not reverting the validators.

---

## New Issues

### Introduced by the cascade interaction (not by the validators themselves)

**N1 — Call-level rejection cascade: total plan failure from single-lever violations.**
The pre-existing B1 bug (`identify_potential_levers.py:231–240`) re-raises any exception from the
3-call loop, discarding accumulated `responses`. With validators now firing more frequently —
especially for llama3.1 (100% non-compliance with combined review_lever format) — this converts
"validator rejects one lever" into "zero output for the entire plan." Run 95 silo output directory
contains only `activity_overview.json` and `usage_metrics.jsonl`; run 1/01 haiku silo has only
`usage_metrics.jsonl`. All confirmed by file system inspection. This was explicitly predicted in
analysis/12 `assessment.md` as a risk of shipping Direction 1 without Direction 2.

**N2 — Template leakage worsened: 0 → 20 cells with forbidden labels or bracket placeholders.**
insight_codex observed `Conservative:`, `Moderate:`, `Radical:` option prefixes in run 95 parasomnia
output and bracket placeholders (`[protagonist's culpability and victim status]`) in run 1/01
hong_kong_game reviews. These labels were absent in before-PR runs. Root cause identified by
code_codex (S1): the system prompt at line 138 teaches "Show clear progression: conservative →
moderate → radical" while line 158 explicitly prohibits `Conservative:`, `Moderate:`, `Radical:`
prefixes — a direct contradiction that smaller or more literal models resolve by using the labels.

**N3 — Haiku editorial commentary embedded in JSON options.**
Run 1/01 haiku silo lever 7 produced a 7-element options list including `"Removing Lever 8."` as
one entry — the model embedded self-corrective editorial commentary inside the structured JSON
array. The `check_option_count` validator correctly rejected this (7 != 3), but the cascade
discarded the other 18+ valid levers. This appears to be a haiku-specific behavior under long
multi-lever generation, not triggered before the PR (when `max_length=7` removed the incentive
to self-edit). Could be addressed by a prompt instruction prohibiting meta-commentary within JSON
fields.

### Surfaced (latent, not introduced by PR)

**N4 — `check_review_format` is English-literal, not language-agnostic.**
The validator checks for literal `"Controls "` and `"Weakness:"` substrings (code_codex B1).
`prompt_optimizer/AGENTS.md:165–168` states validators must be language-agnostic for multilingual
plans. Current test matrix is English-only, so this is not currently failing, but it represents
a correctness gap for future non-English plans.

**N5 — `check_review_format` weaker than the prompt contract.**
The validator accepts `"Controls speed of delivery vs operational costs. Weakness: ..."` (missing
the period after `vs`), bracket placeholders like `"Controls [protagonist's culpability] vs.
[audience sympathy]. ..."`, and any string containing both keywords regardless of order or
two-sentence structure. insight_codex counts 71/563 after-PR levers with non-exact review
formatting that pass the validator. The full prompt contract requires `"Controls [A] vs. [B].
Weakness: [text]."` shape; the validator only checks presence.

---

## Verdict

**CONDITIONAL**: The validators are correct, working as designed, and necessary — no malformed
levers ship to downstream tasks. The targeted bugs (option count violations, review format
violations in artifacts) are fully eliminated. However, the pre-existing B1 partial-result-loss
bug converts single-lever validator rejections into total plan failures, which is a meaningful
regression for llama3.1 (2 plans now produce zero output instead of imperfect output). The PR
is worth keeping only if Direction 2 (partial result recovery) is implemented promptly. The
condition is not hypothetical — it materialized in the first test batch (runs 95, 1/01).

---

## Recommended Next Change

**Proposal:** Implement partial result recovery in the 3-call loop: change the exception handler
in `identify_potential_levers.py:231–240` to `break` (not re-raise) when `len(responses) >= 1`,
returning levers from successful earlier calls with a metadata warning flag rather than discarding
everything when a later call fails.

**Evidence:** Convincing. All four analysis agents (insight_claude C1, insight_codex C2,
code_claude I1/B1, code_codex B3/I2) independently flagged this as the highest-priority next
fix. The analysis/12 assessment explicitly predicted this risk and called it a prerequisite
companion to Direction 1. Two concrete before/after failures confirm it:
- Run 95 llama3.1: silo and gta_game fail entirely (0 levers) because `check_review_format`
  rejects every lever on the first call, raising `LLMChatError` before any response is accumulated.
- Run 1/01 haiku: silo fails (0 levers) because `check_option_count` rejects lever 7 with 7
  options, discarding the 18+ valid levers from the same `DocumentDetails` parse.

The synthesis/13 provides the exact code change:
```python
except Exception as e:
    llm_error = LLMChatError(cause=e)
    logger.debug(f"LLM chat interaction failed [{llm_error.error_id}]: {e}")
    logger.error(f"LLM chat interaction failed [{llm_error.error_id}]", exc_info=True)
    if len(responses) == 0:
        raise llm_error from e
    logger.warning(f"Call {call_index} failed [{llm_error.error_id}], returning partial results from {len(responses)} prior call(s).")
    break
```

**Verify in next iteration:**
- **Primary signal:** llama3.1 silo and gta_game should no longer produce zero output. They
  should produce levers from whichever of the 3 calls succeeded before the validator rejection.
  Watch: do calls 1–2 pass the validator for llama3.1, or does call 1 already fail? If call 1
  fails (no accumulated `responses`), the plan still fails entirely — the partial recovery only
  helps when at least one earlier call succeeded.
- **Haiku silo recovery:** Run 1/01 haiku silo failed on lever 7 of a single call. Verify that
  after partial recovery, the plan produces output from at least 2 of 3 calls (the ones that
  did not include the editorial-commentary lever).
- **Shared-model success rate:** Should recover from 84% toward 92% (before-PR baseline). If it
  does not, investigate whether llama3.1 now fails on call 1 of every plan (no prior responses
  to fall back on), which would indicate a systematic compliance issue beyond the cascade.
- **Metadata flag:** Confirm `partial_result` flag appears in run metadata for plans that used
  the fallback path. This is essential for the analysis pipeline to distinguish "plan completed
  with full 3 calls" from "plan completed with partial calls."
- **Overflow telemetry (Direction 3/D4):** Overflow logging was not included in PR #289 and was
  not in this batch either. Confirm it is added to the same PR or shortly after.
- **Do not watch for quality regressions** on gpt-5-nano, qwen3, gemini, or gpt-oss-20b — those
  models had no validator-caused failures, so partial result recovery does not affect their
  control flow at all.

**Risks:**
- **If call 1 fails for llama3.1 (0 accumulated responses):** The partial recovery guard
  (`len(responses) == 0: raise`) preserves the full-failure behavior — no improvement for plans
  where the first call itself fails the validator. This is acceptable; it cannot make things
  worse, and it correctly recovers from call-2 or call-3 failures.
- **Partial output quality:** Plans completing with only 2 of 3 calls will have 10–14 levers
  instead of 15–22. Downstream `DeduplicateLeversTask` may have less diversity to work with. The
  metadata flag allows analysis tools to track this trade-off.
- **llama3.1 systematic non-compliance:** Even with partial recovery, if llama3.1 fails every
  single call for a plan (because every call produces non-compliant reviews), the plan still
  produces zero output. In run 95, the silo and gta_game failures hit on call 1 (single call
  attempted per plan, workers=1, sequential). If that pattern is consistent, partial recovery
  alone is insufficient for llama3.1 — a prompt fix for the `review_lever` format is also needed
  (synthesis/13 Direction 4: add a concrete single-field example with both `Controls` and
  `Weakness:` components).
- **The prompt contradiction (N2) is unresolved:** Template leakage (20 cells) is a separate
  issue from the cascade. Direction 3 (prompt fix: remove "conservative → moderate → radical"
  label names) should be bundled with the next change or tracked separately.

**Prerequisites:** None for the partial result recovery change itself. It is a standalone
5-line modification with no schema changes required.

---

## Backlog

### Resolved — remove from backlog

- **N1/N2 from analysis/12 (assessment): Missing `options == 3` validator.** Fixed by PR #289.
  Evidence: 0 option-count violations in any post-PR successful artifact.
- **N2 from analysis/12 (assessment): Missing `review_lever` format enforcement.** Fixed by PR
  #289. Evidence: 0 missing-`Controls` or missing-`Weakness:` violations in post-PR artifacts.

### Persisting — keep in backlog

- **qwen3 consequence contamination (~70%):** 71/514 before and 71/563 after — flat in absolute
  count. `review_lever` text bleeds into `consequences` in ~12–14% of qwen3 levers. A
  post-parse repair validator on `consequences` (synthesis/13 Direction 2) would fix this.
  Medium effort; no cascade risk since it would be repair, not rejection.
- **gpt-oss-20b plan-specific failures:** Run 90 failed on `sovereign_identity` (JSON extraction,
  164 s); run 96 failed on `parasomnia` (JSON truncation, 34.85 s). Different plans each run —
  may be context-length sensitivity to long/complex plans. Requires investigation; plan chunking
  or pre-truncation may help.
- **Thread-safety race on `set_usage_metrics_path`** (`runner.py:106` outside `_file_lock`):
  Corrupts `usage_metrics.jsonl` under `workers > 1`. Low urgency if standard mode is
  `workers=1`, but a real data-integrity bug.
- **Partial result loss on plan failure** (B1 cascade): **NOW URGENT.** Run 95 silo/gta_game
  and run 1/01 haiku silo all produce zero output due to this. This is the synthesis/13 top
  recommendation. Move to highest priority.

### New — add to backlog

- **N1 (this assessment): Call-level cascade now causing systematic plan failures.** llama3.1
  2/5 plans produce zero output in run 95. haiku 1/5 in run 1/01. Direct consequence of
  deploying PR #289 without PR #289 + Direction 2 together. **URGENT — blocks PR #289 verdict
  from YES.**
- **N2 (this assessment): Template leakage worsened (0 → 20 cells).** Conservative:/Moderate:/
  Radical: labels and bracket placeholders appeared for the first time. Root cause: prompt
  contradiction (line 138 teaches the label framing; line 158 prohibits it). Fix: remove named
  labels from the progression instruction (synthesis/13 Direction 3). Low effort.
- **N3 (this assessment): Haiku editorial commentary in JSON options.** Model embedded "Removing
  Lever 8." as an option string. `check_option_count` correctly caught it but cascade discarded
  18+ valid levers. Prompt instruction prohibiting meta-commentary within JSON fields would reduce
  frequency. Low priority until partial recovery is in place.
- **N4 (this assessment): `check_review_format` is English-literal.** Uses hardcoded `"Controls "`
  and `"Weakness:"` substrings. Low priority for current all-English test matrix but should be
  revisited before multilingual plans are added.
- **N5 (this assessment): `check_review_format` is weaker than the prompt contract.** 71/563
  after-PR levers still have non-exact format (`vs` vs `vs.`, bracket placeholders in tensions,
  wrong ordering). A stricter regex validator would close this gap but should be deferred until
  after partial result recovery is in place (otherwise stricter validation → more cascade
  failures). Synthesis/13 Deferred D8.
- **N6 (this assessment): Overflow telemetry still absent.** Direction 3 from analysis/12,
  carried forward from analysis/13. Very low effort; bundle with next PR.
