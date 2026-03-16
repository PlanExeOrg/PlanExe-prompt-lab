# Assessment: fix: remove bracket placeholders and fragile English-only validator

## Issue Resolution

**What PR #299 was supposed to fix** (from `pr_title` / `pr_description`):

1. **Bracket placeholders in `review_lever` field descriptions and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`** — `[Tension A]`, `[Tension B]`, `[specific factor]` were being echoed verbatim into model outputs (36 instances in run 33, gpt-5-nano, analysis/18).
2. **Fragile English-only `check_review_format` validator** — required `'Controls '` and `'Weakness:'` substrings, rejecting any non-English or alternate-phrasing review (e.g. "Balances X vs Y").
3. **`summary` field description misaligned with prompt_4 format** — old description asked for a 100-word open-ended critique instead of the one-sentence "Add…" concrete prescription.

**Is the issue actually resolved?**

- **Issue 1 (bracket leakage)**: FULLY RESOLVED. insight_codex measures 37 raw bracket hits in the before-set (runs 31–37, all from run 33 gpt-5-nano sovereign_identity) → 0 in the after-set (runs 38–45). Direct grep of all after-PR output files confirms zero `[Tension` or `[specific factor]` matches. The fix in field descriptions and the system prompt constant is effective.

- **Issue 2 (English-only validator)**: RESOLVED — with a side effect. Under the new structural validator (min 20 chars + no square brackets), qwen3 (run 38: 10/15 silo reviews) and gpt-4o-mini (run 41: 8/17 silo reviews) now produce and pass "Balances X vs Y. Weakness: …" and other non-"Controls" phrasings. These would have failed under the old validator. This is the intended i18n fix; the side effect is cross-model format inconsistency (see **New Issues**).

- **Issue 3 (summary field)**: FULLY RESOLVED. insight_codex measures 90/105 bad summaries (not starting with "Add ") in the before-set → 0/105 in the after-set. Every run 38–45 summary now begins with "Add …". Source: `history/1/40_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-9-potential_levers_raw.json:73`.

**Residual symptoms of original issues:**

- The PR has not yet been merged to the PlanExe `main` branch. The working tree (`identify_potential_levers.py` lines 54–57, 95–98, 113–115) still shows the pre-PR validator and field descriptions (confirmed by source read). Experiments ran on the PR branch `fix/review-brackets-and-i18n-validator`, not on `main`.
- The `LeverCleaned.review` description (lines 148–151) was not updated; it still carries placeholder markers. This is a maintenance hazard but has no runtime effect (class is constructed programmatically, not via LLM structured output).

---

## Quality Comparison

All 7 models appear in both batches (run 39 is absent from analysis/19; it is not a shared-model discrepancy). Pooled metrics from insight_codex cover 637 levers (before, runs 31–37) and 630 levers (after, runs 38–45); baseline is 75 levers across 5 plans.

Direct output verification: haiku silo (run 43) confirms multi-clause analytical reviews with "Controls X vs Y" format and substantive Weakness sentences (~200 chars); qwen3 silo (run 38) confirms 10/15 reviews use "Balances X vs Y" instead of "Controls"; llama3.1 silo (run 45) confirms label-only options in later call groups (e.g. levers "Ecological Integration", "Governance Architecture" with 2–3 word options), while call-1 options are complete sentences.

| Metric | Before (runs 31–37) | After (runs 38–45) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 37 raw hits (run 33, gpt-5-nano) | 0 | IMPROVED |
| **Bad summaries (not "Add …")** | 90/105 (85.7%) | 0/105 (0.0%) | IMPROVED |
| **Non-"Controls" review first sentences** | 0 (old validator enforced "Controls") | ~18 (qwen3: 10/15, gpt-4o-mini: 8/17, silo) | REGRESSED — validator removed format enforcement |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness (final)** | 0 duplicates per output | 0 duplicates per output | UNCHANGED |
| **Raw cross-call name duplication** | 10 (runs 31–37) | 21 (runs 38–45) | REGRESSED — 21 all from llama3.1 (run 45) |
| **Template leakage (triad terms)** | 7 occurrences | 5 occurrences | UNCHANGED / slightly better |
| **Fabricated % claims (all fields)** | 27 total | 20 total | IMPROVED |
| **Marketing-language hits** | 23 total | 18 total | IMPROVED |
| **Avg consequence length vs baseline** | 302.5 chars (1.08×) | 287.1 chars (1.03×) | IMPROVED (closer to baseline) |
| **Avg review length vs baseline** | 169.0 chars (1.11×) | 164.9 chars (1.08×) | UNCHANGED |
| **Avg option length vs baseline** | 119.1 chars (0.79×) | 116.7 chars (0.78×) | UNCHANGED |
| **llama3.1 label-only options (silo)** | 7/21 levers (~33%, call-2) | 8/21 levers (~38%, calls 2/3) | UNCHANGED (within noise) |
| **haiku fabricated % in consequences** | 19 (run 37, insight_codex table) | 18 (run 43, insight_codex table) | UNCHANGED — root cause (`consequences` field description) untouched |
| **Review format: "Controls" compliance** | ~100% all models | ~73% (5 models "Controls", 2 models mixed) | REGRESSED — intentional trade-off for i18n |
| **OPTIMIZE_INSTRUCTIONS alignment** | Constant absent from source | Constant present on PR branch (advisory only, not wired into runtime) | PARTIAL — not executable |

**Note on haiku fabricated %**: haiku produces 18 of the 20 remaining fabricated percentage claims in analysis/19, concentrated in `consequences` fields (e.g. "70%" and "4–8 weeks" in parasomnia, `history/1/43_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:22`). This is not a PR #299 regression — it was 19 claims in analysis/18. The root cause is the `consequences` Pydantic field description (lines 37–39) which still says "All three labels and at least one quantitative estimate are mandatory." PR #299 did not change this description. Haiku, as the most instruction-following model in the batch, faithfully produces mandatory quantitative estimates when instructed to.

**OPTIMIZE_INSTRUCTIONS check**: The constant appears on the PR branch but was not found in the `main` source. Per code_codex (S3), it is not interpolated into the system prompt assembly path and functions as advisory documentation only. The PR's stated goals (no bracket placeholders, i18n-safe validation, summary alignment) all move toward the OPTIMIZE_INSTRUCTIONS goals of "no fabricated numbers, no English-only validators, no bracket placeholders." The fabricated-% and marketing-language dimensions are not yet enforced at runtime.

---

## New Issues

### N1 — Review format inconsistency across models (direct result of validator relaxation)

Before PR #299, the English-only validator (`'Controls '` check) inadvertently enforced cross-model format consistency. After PR #299, the new structural validator (min 20 chars + no brackets) is too permissive: qwen3 (run 38) produces 10/15 silo reviews starting "Balances X vs Y" instead of "Controls X vs Y"; gpt-4o-mini (run 41) produces 8/17 non-"Controls" reviews. These pass validation but differ structurally from haiku, gemini, llama3.1, and gpt-oss-20b outputs which maintain "Controls" format.

The "Controls X vs Y" pattern has informational content: it names the governing tension with a specific framing that is more precise than "Balances" (which implies trade-off without specifying what controls/governs the decision). If downstream scenario-picker logic uses review fields for tension analysis, varied phrasing may reduce parsability.

Source: `history/1/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (qwen3 reviews 1–5 all "Balances"); `history/1/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (all haiku reviews start "Controls").

### N2 — llama3.1 raw cross-call name duplication increased

Raw duplicate lever names rose from 10 (runs 31–37, all before) to 21 (runs 38–45, all from run 45 llama3.1). Final outputs are deduplicated and this does not affect quality of delivered levers. However, wasted call budget and reduced candidate diversity upstream of dedup are a latent efficiency issue. Source: `history/1/45_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json` — "Regulatory Framework Update" appears at lines 41, 135, and 196. This is likely correlated with the label-only degradation: when llama3.1 falls back to minimal-effort outputs in later calls, it also produces semantically similar names.

### N3 — `check_review_format` does not enforce the documented two-sentence structure

The new validator accepts any string ≥20 chars with no square brackets. It does not check for: (a) two-sentence structure, (b) a tension-pair separator (`vs.`), (c) a Weakness clause, or (d) that the second sentence is materially distinct from the first. Vague filler ("This is an important strategic consideration.") would pass. The PR replaced an over-specified English-only check with an under-specified structural check. A middle-ground validator (check for `vs.` or equivalent separator + two sentences) would be language-agnostic while preserving structural enforcement.

### Latent issue surfaced: PR not merged to main

The source tree on `main` still contains pre-PR code. The experiments were run against the PR branch. This means the production behavior and the analyzable code diverge until the PR is merged.

---

## Verdict

**CONDITIONAL**: The PR's three stated changes produce large, measurable improvements (bracket leakage 37→0, bad summaries 90→0, i18n validator unblocked), but the validator replacement is too permissive, causing observable format inconsistency in 2 of 7 models and dropping structural enforcement that was previously a useful side effect. The PR should be merged, but requires a follow-up fix to tighten `check_review_format` before the validator change is considered complete.

**Justification**: The wins are real and substantial — the summary fix alone (90/105 → 0/105) is high-value, and zero bracket placeholder leakage across 35 plans confirms the field-description fix is effective. The validator relaxation is the right direction for i18n but overshoots: replacing English keyword checks with a pure length gate loses the two-sentence tension/weakness structure that gave the review field its analytical value. This is a single-function fix with low risk.

---

## Recommended Next Change

**Proposal**: Add a one-line option-quality reminder to the call-2/3 multi-call prompt: append `"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n"` to `prompt_content` in the `else` branch at `identify_potential_levers.py` lines 231–236.

This is the synthesis.md Direction 2 recommendation, which it prioritizes over the validator tightening (Direction 1) on grounds of lower risk and zero design choices needed.

**Evidence**: The llama3.1 label-only option degradation is the last consistently failing structural quality dimension across two consecutive batches:
- analysis/18 run 31: 7/21 silo levers have label-only options in call-2 (e.g. "Centralized Authority", "Maximize Efficiency").
- analysis/19 run 45: 8/21 silo levers have label-only options in calls 2/3 (e.g. "Bioregenerative Systems", "Decentralized Councils", "Closed-Loop Ecology").
- Call-1 options are substantive in both batches (15–30 words).

The failure is call-position-dependent, not capability-dependent. The multi-call prompt at lines 231–236 prepends only a name-exclusion clause to calls 2/3; quality constraints live in the system prompt where attention decays as the names blacklist grows. This structural root cause is confirmed by code_claude (B4) and code_codex (S2).

**Verify** (in the next iteration's experiments):

1. **llama3.1 calls 2/3 option length**: Check `history/1/*/outputs/20250321_silo/002-10-potential_levers.json` for llama3.1. Confirm options in the 8th–21st levers are ≥15 words each. The target: label-only levers drop from ~38% to near zero.
2. **llama3.1 raw duplicate names**: Check `002-9-potential_levers_raw.json` for run equivalent to run 45. The count should drop from 21 toward the 0–10 range; dedup makes final outputs clean regardless, but raw diversity is a signal of call quality.
3. **Other models unchanged**: Verify haiku (run equivalent to 43), qwen3 (run equivalent to 38), and gpt-4o-mini (run equivalent to 41) option length distributions are unchanged (they already exceed 15 words and the reminder should be a no-op for them).
4. **No new ValidationErrors**: Check `events.jsonl` for all 7 model runs — the reminder adds no new validation path, so LLMChatErrors should remain 0.
5. **Fabricated % in haiku consequences unchanged**: Verify haiku's ~18 fabricated-% claim count is stable. The option-quality fix does not touch the `consequences` field description and should have no effect here. If the count changes significantly, it indicates an unexpected interaction.

**What could go wrong**:

- The reminder (`"at least 15 words with an action verb"`) may trigger unnecessary self-criticism or hedging from models that produce legitimate terse strategies (e.g. "Adopt a strict information monopoly" is 7 words but substantively complete). If other models start padding options to meet the word count, option content quality could regress.
- llama3.1's degradation may be more about **context length** than instruction salience — if the names blacklist is already crowding the context window, a one-line reminder may not be prominent enough. In that case, capping the names blacklist (e.g. max 7 prior names) or restructuring the call order would be needed.
- Haiku's fabricated-% problem (18 claims, all consequences) is unaffected by this change. If the next analysis focuses only on llama3.1 improvement and ignores haiku % claims, a false-positive "success" verdict could be written.

**Prerequisite issues**: The validator tightening (Direction 1: check `vs.` presence + two-sentence structure in `check_review_format`) should be paired with this change or done immediately after, since the format inconsistency (N1 above) affects 2/7 models and is a direct consequence of PR #299. The synthesis.md recommends doing Direction 2 first on grounds of zero risk; Direction 1 second. Both can be done in the same PR.

Note: The `OPTIMIZE_INSTRUCTIONS` constant should be wired into the system prompt assembly path or at minimum cited in a comment near the validator, so future reviewers know the policy it is enforcing. Currently it is advisory only.

---

## Backlog

### Resolved by PR #299 (remove from backlog):
- **Bracket placeholder leakage in `review_lever` output** (was code_claude B5 / code_codex B1 from analysis/18): 0 occurrences in all 35 after-PR plans. Source: direct grep of output files.
- **`summary` field description contradicts prompt format** (was code_claude S2 from analysis/18): Bad summaries dropped from 90/105 → 0/105. The description now aligns with the one-sentence "Add…" format.
- **run 33 bracket placeholder spike** (was insight_codex N1 from analysis/18): 36 instances → 0. Field description fix was the root cause.

### Persisting items (not resolved by PR #299):

- **`Lever.consequences` Pydantic field description still mandates old chain format + quantification** (code_claude B1 from analysis/18, B3 from analysis/19): lines 37–39 still say "All three labels and at least one quantitative estimate are mandatory." Root cause of haiku's ~18 fabricated-% claims in analysis/19. HIGH PRIORITY.
- **`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant not updated** (code_claude B2 from analysis/18, B1e from analysis/19): constant still mandates `Immediate → Systemic → Strategic`, `% change`, `conservative → moderate → radical`, and "Radical option must include emerging tech/business model." Any code path invoking the module directly reproduces old broken behavior.
- **llama3.1 multi-call label-only option degradation** (code_claude S1/C1, insight_claude N1 from analysis/18; unchanged in analysis/19): ~33–38% of levers in calls 2/3 degrade to 2–3 word labels. Two batches documented; fix proposed (one-line reminder + option minimum-word validator) but not yet applied.
- **Thread safety: `set_usage_metrics_path` called outside lock** (code_claude B4, code_codex S3 from analysis/18; B2/B3 from analysis/19): latent bug at `runner.py:106`. Masked by `workers=1` default. Will corrupt usage metrics if parallel workers are enabled.
- **PR #299 not merged to `main`** (code_claude B1 from analysis/19): the source checkout shows pre-PR code. Running experiments from `main` would reproduce old validator failures.

### New items to add:

- **`check_review_format` validator under-specifies the review structure** (code_codex B1 from analysis/19, insight_claude N2): new validator accepts any 20-char string with no brackets, losing enforcement of two-sentence tension/weakness shape. Affects qwen3 and gpt-4o-mini format consistency. Fix: check `'vs.' in v.lower()` + two-sentence structure, language-agnostically.
- **llama3.1 raw cross-call name duplication increased** (insight_codex from analysis/19): 10 → 21 raw duplicate names. Correlated with label-only option degradation in later calls. Downstream dedup handles it, but it wastes token budget. Fix: adaptive loop that caps names blacklist or stops early when enough unique levers exist.
- **`OPTIMIZE_INSTRUCTIONS` constant advisory-only** (code_codex S3 from analysis/19): constant exists on PR branch but is not wired into system prompt assembly or validated against at runtime. Should be made executable or referenced in validator comments.
