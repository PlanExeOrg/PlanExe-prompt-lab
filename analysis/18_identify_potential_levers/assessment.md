# Assessment: fix: simplify lever prompt to restore content quality

## Issue Resolution

**PR #297 targeted**: Content quality regression identified in analysis/17's external report
comparison (baseline 6.5/10 vs optimized 5.8/10). The mandatory `Immediate → Systemic →
Strategic` consequence chain inflated length without adding substance; mandatory quantification
(`% change, cost delta`) drove fabricated statistics; `conservative → moderate → radical`
option triads produced predictable non-distinct options; "Radical option must include emerging
tech/business model" pushed toward flashy unsupported claims.

**Is the issue resolved?** Yes, definitively on the primary targets:

- **Chain format eliminated**: 614/614 consequences used `Immediate → Systemic → Strategic`
  before; 0/637 use it after. Source: insight_codex pooled metrics.
- **Fabricated % collapsed**: 864 unsupported `%` claims before; 25 after (−97.1%).
  Source: insight_codex heuristic audit against plan briefs in `baseline/train/`.
- **Field bleed eliminated**: qwen3's 66-lever consequence contamination (review text duplicated
  in `consequences`) went from 66/614 (10.7%) to 0/637 (0%).
- **Content length restored**: avg consequence length 417.2 → 309.1 chars (1.49× → 1.11×
  baseline). haiku hong_kong specifically: ~980 → ~450 chars, file size 54 KB → 15 KB (3.6×
  reduction).
- **gpt-oss-20b parasomnia resolved**: 3 consecutive batch failures (runs 18, 20, 25) resolved
  in run 32 (79.1s clean completion) by shorter output fitting within provider token limits.
- **Marketing language reduced**: 16 → 7 instances across all runs.

**Residual symptoms**:

- The `Lever.consequences` Pydantic field description was NOT updated by the PR. It still says
  `"Required format: 'Immediate: [effect] → Systemic: [impact with % change or cost delta] →
  Strategic: [implication]'. All three labels and at least one quantitative estimate are
  mandatory."` (code_claude B1, confirmed by source). This contradictory schema is sent to
  every model on every call. Strong models (haiku, gemini, qwen3) override it; weaker models
  (llama3.1) partially obey it, explaining the one residual fabricated % (N2) and sub-header
  format (N3) in run 31.
- The `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant (lines 154–196) was also not updated
  — it still mandates all four removed requirements (B2).
- Marketing language: 7 instances remain (run 35 "cutting-edge"; run 36 "breakthrough",
  "cutting-edge" ×2).
- 25 unsupported `%` claims remain, now concentrated in option fields (haiku, qwen3) rather
  than consequences.

---

## Quality Comparison

All 7 models appear in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini,
gemini-2.0-flash, haiku-4-5. Pooled metrics from insight_codex cover 614 levers (before) and
637 levers (after); baseline is 75 levers across 5 plans.

| Metric | Before (runs 24–30) | After (runs 31–37) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 34/35 (97.1%) | 35/35 (100.0%) | IMPROVED (+2.9pp) |
| **LLMChatError count** | 6 (run 25 EOF + run 29 config ×5) | 0 | IMPROVED |
| **Bracket placeholder leakage** | 12 instances (run 24, llama3.1 silo) | 36 instances (run 33, gpt-5-nano, sovereign_identity) | REGRESSED (3× worse, single model) |
| **Option count violations (raw)** | 4 responses over cap (run 24, llama3.1) | Not re-measured; label-only options now the issue | UNCHANGED / shifted |
| **Lever name uniqueness** | 608/614 (99.0%) | 628/637 (98.6%) | UNCHANGED |
| **Template leakage (review exact-format)** | 573/614 (93.3%) pass | 575/637 (90.3%) pass | REGRESSED (−3.0pp; driven by run 33) |
| **Consequence chain format** | 614/614 (100%) chained | 0/637 (0%) chained | IMPROVED (eliminated) |
| **Consequence field length vs baseline** | 417.2 chars (1.49×) | 309.1 chars (1.11×) | IMPROVED (−0.38× closer to baseline) |
| **Option field length vs baseline** | 133.7 chars (0.89×) | 124.8 chars (0.83×) | SLIGHT REGRESSION (−0.06×; options got shorter) |
| **Review field length vs baseline** | 173.8 chars (1.14×) | 174.0 chars (1.14×) | UNCHANGED |
| **Cross-call duplication** | 22 duplicate names (run 24, llama3.1); 0 others | 0 all models | IMPROVED |
| **Over-generation (>7 levers/call)** | Present in multiple models | Present in multiple models | UNCHANGED (dedup handles it) |
| **qwen3 consequence contamination** | 66/85 levers (78%) | 0/637 (0%) | IMPROVED (eliminated) |
| **Fabricated quantification (unsupported %)** | 864 claims | 25 claims | IMPROVED (−97.1%) |
| **Marketing-copy language** | 16 hits | 7 hits | IMPROVED (−56%) |
| **Review uniqueness** | 593/614 (96.6%) | 636/637 (99.8%) | IMPROVED (+3.2pp) |
| **Summary exact-format compliance** | 8/102 (7.8%) | 11/104 (10.6%) | MARGINALLY IMPROVED (root cause unresolved) |
| **gpt-oss-20b parasomnia** | FAILED (EOF, 3 consecutive) | SUCCESS (79.1s) | RESOLVED |
| **Gemini config failure** | YES (5 wasted starts, recovered) | NO | RESOLVED |
| **llama3.1 bracket consequences (call-3)** | 6/21 levers (29%) | 0 | RESOLVED |
| **llama3.1 label-only options (call-2)** | Not observed | 7/21 levers (33%) | NEW ISSUE |
| **haiku consequence length (hong_kong)** | ~980 chars (4.3× baseline) | ~450 chars (2.0× baseline) | IMPROVED (2.3× reduction) |

**Note on option length regression**: The pooled option char decrease (133.7 → 124.8) is below
baseline (150.2). This appears to be a consequence of removing the `conservative → moderate →
radical` progression template, which gave all models an explicit structural scaffold. Most
models now produce shorter individual options; haiku is the exception (276.1 chars avg option),
which remains verbose. This is worth monitoring but is not a clear quality failure — shorter
options are not inherently worse if they are substantive rather than formulaic.

---

## New Issues

### NI1 — Bracket placeholder leakage INCREASED (12 → 36 instances)

Run 33 (gpt-5-nano) produced 36 bracket-placeholder instances in `review_lever` fields across
all plans (e.g., `Controls [platform resilience through platform-neutral governance] vs.
[vendor lock-in risk...]`). This is 3× the prior count and all concentrated in one model.

Root cause (confirmed by both code reviewers): `review_lever` Pydantic field description
(lines 51–57) still shows `[Tension A]`, `[Tension B]`, `[specific factor]` as the target
format, while prompt_4 section 5 prohibits "bracket-wrapped templates." The prohibition and
the example actively contradict each other. PR #297 added the prohibition but left the
contradictory example in place. Source: code_claude B5, code_codex B1.

### NI2 — llama3.1 label-only options in call-2 (7/21 levers)

Run 31 (llama3.1) silo shows call-1 options are substantive (15–30 words); call-2 options
degrade to 2–4 word labels (`"Centralized Authority"`, `"Maximize Efficiency"`, `"Selective
Disclosure"`). This is a new mode of the persistent llama3.1 multi-call degradation — the
old failure was bracket-wrapped consequences (analysis/17); the new failure is label-only
options. The conservative/moderate/radical template may have provided structural scaffolding
that llama3.1 relied on in later calls.

No minimum-word validator exists for options; these pass `check_option_count` undetected.
Source: code_claude S3, code_codex S2.

### NI3 — Stale Pydantic field descriptions and hardcoded constant not updated by PR

The PR updated the external prompt file but missed three in-code locations:
- `Lever.consequences` description (lines 34–46): still mandates old chain + mandatory %
- `LeverCleaned.consequences` description (lines 130–139): identical stale text
- `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant (lines 154–196): all four removed
  requirements still present (chain, %, conservative/radical, emerging-tech forcing)

This is the highest-impact incomplete work. The JSON schema contradiction directly explains
llama3.1's continued fabricated % (N2) and sub-header format (N3). Source: code_claude B1,
B2, B3.

### NI4 — Undeclared `break → continue` control-flow change

PR #297 includes an undeclared change at `identify_potential_levers.py:263–282`: on call-2/3
failure, behavior changed from `break` (return partial results) to `continue` (proceed to
next call). This is scope creep in a prompt-only PR and makes before/after experiment
attribution harder. Source: code_codex S1.

---

## Verdict

**YES**: The PR produces large, measurable improvements on its primary targets — consequence
chain format eliminated (100%→0%), fabricated quantification collapsed 97%, field bleed
eliminated, gpt-oss-20b parasomnia resolved after 3 consecutive failures, 100% plan success
rate for the first time. These improvements affect every model on every plan. The one new
structural regression (bracket leakage: 12→36 instances, single model) is narrower than the
gains. The stale Pydantic field descriptions are the key incomplete work to fix immediately.

---

## Recommended Next Change

**Proposal**: Update the three stale locations in `identify_potential_levers.py` that
contradict prompt_4: (1) `Lever.consequences` field description, (2)
`LeverCleaned.consequences` field description, and (3) `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`
constant — replacing all four stale requirements (chain format, mandatory %, option progression
template, emerging-tech forcing) with language matching prompt_4. Simultaneously replace bracket
placeholders in the `review_lever` field description with a concrete non-bracket literal example
and extend `check_review_format` to reject `[` / `]` in outputs.

**Evidence**: All four synthesis agents agree this is the highest-priority remaining work.
The contradictory `Lever.consequences` field description directly explains every llama3.1-specific
issue in analysis/18: fabricated % (N2, run 31, `"10-15%"` in silo consequences), sub-header
format (N3, `"Direct Effect: ... Downstream Implication: ..."`), and likely label-only options
(NI2, since conflicting schema signals reduce effective instruction clarity for weaker models).
The bracket placeholder contradiction in `review_lever` directly explains the run-33 36-instance
spike (up from 12 before). Source: synthesis Direction 1+2; code_claude B1+B2+B5; insight_claude
N2+N3; insight_codex metrics table (run 33: 36 placeholders vs 0 for runs 32/34/35/36/37).

**Verify**: After landing the change, run the same 7 models against all 5 plans and confirm:

- **llama3.1 fabricated %**: run 31 had 1 instance (`10-15%` in silo "Resource Optimization");
  after fix, run should show 0 fabricated % in consequences for llama3.1.
- **llama3.1 sub-headers**: run 31 used `"Direct Effect: ... Downstream Implication: ..."` in
  every consequence; after fix, plain prose expected.
- **gpt-5-nano bracket leakage**: run 33 had 36 instances in `review_lever`; after fix,
  review exact-format compliance should rise above 93.3% (back to before-batch level) and
  placeholder count should drop to near 0.
- **llama3.1 label-only options (call-2)**: whether this resolves with the schema fix alone is
  uncertain — if it persists, it is a multi-call context crowding issue (code_codex B3) not a
  schema issue.
- **haiku, gemini, qwen3**: verify no regressions. These models already follow prompt_4; the
  schema update aligns the schema with behavior already exhibited. Spot-check consequence
  format (no chain), review format (no brackets), fabricated % count.
- **Summary exact-format**: also update `DocumentDetails.summary` field description from
  open-ended critique to concrete format (`Add '[full strategic option]' to [lever]`). Verify
  that exact-match rate rises substantially above the current 10.6%.

**Risks**:

- Removing the stale chain format from `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` is low risk
  — the constant is the fallback path; production runs use the prompt file (already updated).
  Ad-hoc testing will improve, not regress.
- The bracket-rejection validator extension may trigger initial validation retries on weaker
  models (gpt-5-nano, llama3.1) for any output that still uses brackets. This is correct
  behavior — it forces regeneration rather than accepting unfilled placeholders. Ensure retry
  budget is adequate (≥2 retries) before concluding a plan has failed due to bracket rejection.
- If llama3.1's label-only options in call-2 are caused by both (a) stale schema and (b)
  multi-call context crowding (code_codex B3), the schema fix alone may not fully resolve the
  issue. Watch for 7/21-lever label-only pattern in run 31's successor; if it persists, the
  multi-call adaptive loop (code_codex I3) is the next fix.

**Prerequisites**: None. The schema/constant update is self-contained. The bracket-validator
extension builds on `check_review_format` which already exists.

---

## Backlog

### Resolved by PR #297 — remove from active backlog:

- **qwen3 consequence contamination** (analysis/15–17, analysis/17 Direction 4): 66/85 levers
  contaminated before; 0/637 after. Root cause was structural similarity between the chain
  format and the review format. Eliminated.
- **gpt-oss-20b parasomnia EOF** (analysis/15–17, synthesis Direction 1): Three consecutive
  batch failures resolved in run 32 by shorter consequence output. No code change required;
  prompt simplification was sufficient.
- **Gemini stale model alias** (analysis/17 NI4, synthesis Direction 5): Run 36 ran cleanly
  with no config failure. Either a separate fix was applied or the alias was corrected; either
  way, the symptom is gone.
- **llama3.1 bracket-wrapped consequences in call-3** (analysis/17 N3): 6/21 → 0. Brackets
  now appear in review fields (gpt-5-nano) rather than consequences (llama3.1).
- **Content quality regression (external report 5.8/10)** (analysis/17 synthesis, Critical
  Finding): Chain format, fabricated %, marketing language all substantially reduced. The
  specific drivers of the credibility regression are eliminated or drastically reduced.

### New issues added to backlog:

- **Stale `Lever.consequences` and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`** (code_claude
  B1, B2, B3): The three in-code locations that still mandate the old chain+% requirements.
  Highest priority — affects every model on every call. **Next PR candidate (synthesis
  Direction 1).**

- **Bracket placeholder contradiction in `review_lever` description** (code_claude B5,
  code_codex B1): Field description shows `[Tension A]`, `[Tension B]`, `[specific factor]`
  while prompt prohibits brackets. Run 33 produced 36 instances. Fix: replace with literal
  example + add bracket-rejection validator. **Next PR candidate (synthesis Direction 2),
  combine with Direction 1.**

- **llama3.1 label-only options in call-2** (insight_claude N1, code_claude S3): 7/21 levers
  with 2–4 word options that pass `check_option_count` undetected. Likely partially caused by
  stale schema (NI3 above); residual cause may be multi-call context crowding. Monitor after
  schema fix before adding a minimum-option-word validator.

- **`summary` field description conflict** (code_claude S2, synthesis Direction 3): Description
  says "Are these levers well picked? ... 100 words." while prompt_4 requires `Add '[full
  strategic option]' to [lever]`. Result: 0/90 exact-format matches in runs 32–37. Very low
  effort fix; include in same commit as Direction 1.

### Carried forward from previous backlog:

- **`review_lever` auto-correction not in code** (analysis/16 D5, analysis/17 NI1): Haiku's
  hong_kong recovery in run 30 was stochastic (prompt-driven), not code-driven. If haiku
  produces a review without "Controls" prefix on a future plan, the validator still hard-rejects.
  Deferred pending next haiku observation.

- **Thread safety: `set_usage_metrics_path` outside lock** (analysis/18 code_claude B4): Global
  path not protected by `_file_lock`; usage metrics misrouted if `workers > 1`. Latent; defer
  until any config uses parallel workers.

- **Multi-call adaptive loop** (code_codex I3): Hard-coded 3 calls with ever-growing name
  blacklist causes later-call context pressure for weaker models. Schedule after schema fix
  confirms whether llama3.1 label-only options persist.

- **EOF retry pattern for gpt-oss-20b** (analysis/17 synthesis D1, analysis/18 code_claude C2):
  Adding `"eof while parsing"` to `_TRANSIENT_PATTERNS` remains a defensive improvement even
  though parasomnia is currently resolved. Low priority given 100% success rate.

- **Optimizer runner missing RetryConfig** (analysis/17 synthesis D1): `runner.py` builds
  `LLMExecutor` without `RetryConfig` while production pipeline passes `retry_config=RetryConfig()`.
  Latent; low urgency.
