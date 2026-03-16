# Assessment: fix: continue loop after call failure instead of breaking

## Issue Resolution

**PR #295 targeted**: When call-2 fails but call-1 already produced results, the loop
previously hit `break` at line 278 of `identify_potential_levers.py`, silently suppressing
call-3. The fix replaces `break` with `continue`, so call-3 runs and potentially recovers
5–7 additional levers. In the analysis/15 partial-failure scenario (llama3.1 gta_game run
1/02: 7 levers from call-1 only), a `continue` would have attempted call-3 and yielded up
to 14 levers.

**Was the fix triggered in this batch?**

No. All four failures in analysis/16 (runs 1/17–1/23) were call-1 failures:

- Run 18 (gpt-oss-20b, parasomnia): `events.jsonl` line 10 — "Attempt 0 failed during
  'execute' stage: JSON EOF while parsing a list at line 25 column 5". `len(responses) == 0`
  at failure → code takes the `raise` path, not the `break`/`continue` path.
- Run 20 (qwen3, parasomnia): same EOF pattern, same call-1 failure.
- Run 23 (haiku, hong_kong): `events.jsonl` line 5 — "Attempt 0 failed: 7 validation
  errors for DocumentDetails" (all `review_lever` missing "Controls" prefix). Again
  call-1 failure → `len(responses) == 0` → `raise`.
- Run 23 (haiku, parasomnia): APITimeoutError after 373s. Call-1 timed out, no responses.

The fix at line 278 is in the `else` branch (`len(responses) > 0`), which requires at least
one prior call to have succeeded. None of the 35 plan executions in this batch reached that
branch. The fix is a latent improvement — correct and valuable — but untested in this batch.

**Residual symptoms**: None introduced by or attributable to the PR. The four failures
observed are unrelated to the `break` → `continue` change:
- JSON EOF on parasomnia (runs 18, 20): output-token budget exhausted on call-1 — a
  truncation issue predating this PR (first observed here across two different models/providers).
- haiku hong_kong validation failure: model dropped "Controls" prefix on all 7 levers in
  call-1 — a domain-specific format drift issue.
- haiku parasomnia timeout: slow, verbose model on the most token-intensive plan.

---

## Quality Comparison

Models appearing in BOTH batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini,
gemini-2.0-flash, claude-haiku. (Run 1/09 excluded — incomplete, no outputs.)

Before = runs 1/10–1/16 (analysis/15). After = runs 1/17–1/23 (analysis/16).

**Measurement note**: analysis/15 codex measured "exact review matches" using a strict regex
for the complete two-sentence formula; analysis/16 codex measured "raw review violations"
against the Pydantic validator's weaker `'Controls '`-substring check. These are different
metrics and are not directly comparable in the Exact Review Compliance row. A separate note
is included for each.

Verified output samples: `history/1/22_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
(gemini, 17 levers, correct review format: "Controls self-sufficiency vs. specialization.
Weakness: The options do not consider the impact of resource scarcity on social unrest.") and
`history/1/21_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
(gpt-4o-mini, 17 levers, correct review format: "Controls immediate funding vs. long-term
sustainability. Weakness: The options fail to consider the potential volatility of private
investment."). Both consistent with analysis/16 claims.

| Metric | Before (runs 1/10–1/16) | After (runs 1/17–1/23) | Verdict |
|--------|-------------------------|------------------------|---------|
| **Overall success rate** | 32/35 (91.4%) | 31/35 (88.6%) | REGRESSED (−1 plan; not caused by PR — all losses are call-1 failures) |
| **PR fix (`break`→`continue`) triggered** | N/A | 0/35 plans | NOT TRIGGERED (all failures were call-1; fix requires call-1 to succeed first) |
| **llama3.1 success** | 4/5 (parasomnia ReadTimeout) | 5/5 | IMPROVED (+1; parasomnia succeeded in run 17 — probable run variance, not PR-related) |
| **gpt-oss-20b success** | 4/5 (hong_kong JSON fail) | 4/5 (parasomnia JSON EOF) | UNCHANGED (4/5 both; failure plan shifted from hong_kong to parasomnia) |
| **gpt-5-nano success** | 4/5 (parasomnia review fail) | 5/5 | IMPROVED (+1; `'Not applicable here'` failure absent in run 19) |
| **qwen3 success** | 5/5 | 4/5 (parasomnia JSON EOF) | REGRESSED (−1; new JSON truncation failure) |
| **gpt-4o-mini success** | 5/5 | 5/5 | UNCHANGED |
| **gemini success** | 5/5 | 5/5 | UNCHANGED |
| **claude-haiku success** | 5/5 | 3/5 (hong_kong validation + parasomnia timeout) | REGRESSED (−2; new failure modes) |
| **Bracket placeholder leakage** | 6 (run 12, hong_kong — `[Tension A]`/`[Tension B]` verbatim) | 6 (run 19, gta_game — same pattern confirmed by insight_codex) | UNCHANGED (~6 per run, confined to gpt-5-nano) |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness (final merged)** | ~100% (run 10 llama3.1: 12 raw cross-call dups collapsed by dedup) | 100% (run 17 llama3.1: 1 review dupe; all others 0) | IMPROVED (llama3.1: 12 cross-call dups → 1) |
| **Label-style options (Title: description), prefix violations** | 21 (15 in run 13 qwen3-silo, 6 in run 16 haiku) | 0 (all runs 17–23 show 0 prefix violations per codex table) | IMPROVED |
| **Review format compliance (Pydantic validator pass, successful plans)** | 100% in 32 successful plans | 100% in 31 successful plans | UNCHANGED |
| **Exact review compliance (strict two-sentence regex — analysis/15 codex)** | llama3.1 100%, gpt-oss-20b 85%, gpt-5-nano 42%, qwen3 18%, gpt-4o-mini 65%, gemini 19%, haiku 0% | Not directly re-measured with same regex; analysis/16 codex raw-violation table (Pydantic check only): gpt-5-nano 53/90 viol (41% non-compliant), all others 0 | MIXED (incompatible measurement; gpt-5-nano is the persistent non-compliant model in both batches) |
| **Consequence chain format (arrow-chain violations, final merged)** | 92 total violations: gpt-oss-20b 18, gpt-5-nano 18, haiku 56 | Chain ok in final: gpt-oss-20b 34/71 (37 viol), gpt-5-nano 66/90 (24 viol), haiku 21/63 (42 viol); all others 100% | MIXED (haiku slightly improved 56→42; gpt-5-nano improved 18→24 inverted; gpt-oss-20b similar; others unchanged) |
| **Content depth (avg option length)** | avg chars: llama3.1 75.9, gpt-oss-20b 79.2, gpt-5-nano 115.7, qwen3 70.6, gpt-4o-mini 109.7, gemini 128.5, haiku 286.4 | avg words (×5.5 ≈ chars): llama3.1 ~58, gpt-oss-20b ~74, gpt-5-nano ~76, qwen3 ~46, gpt-4o-mini ~80, gemini ~82, haiku ~183 | MIXED (haiku: 286→183 chars IMPROVED; most others slightly lower; qwen3 regressed 70→46) |
| **Cross-call duplication (raw lever names)** | llama3.1: 12; others: 0–1 | llama3.1: 1; others: 0 | IMPROVED (llama3.1) |
| **qwen3 consequences contamination** | ~33% in silo run 1/13 (5/15 levers) | Not explicitly measured for run 1/20 (failed on parasomnia, 4 plans available) | UNCLEAR (insufficient data in after batch) |
| **Over-generation (>7 levers/call)** | llama3.1 run 10: avg 7.25/response (5/12 out of range); others in range | llama3.1 run 17: 5 raw responses out of range per codex | UNCHANGED (informational; downstream dedup handles it) |
| **Partial recovery triggered (< 3 calls in raw file)** | 0 (no call-2 failures activated the break guard) | 0 (all failures were call-1; fix never reached) | UNCHANGED |

**Verified samples for 2 shared models:**

*Gemini-2.0-flash silo (run 22 after vs. run 15 before)*: Both show clean format, domain-specific names,
and correct review syntax. Run 22 avg consequence 52.47 words vs. run 15 avg 395.46 chars (~72 words) — slightly shorter
but more concise. No regressions detected.

*GPT-4o-mini silo (run 21 after vs. run 14 before)*: Both show 0 violations, 5/5 plans. Run 21 avg
consequence 32.33 words vs. run 14 240.86 chars (~44 words) — similar range. Quality consistent.

---

## New Issues

### NI1 — JSON EOF truncation on parasomnia for gpt-oss-20b AND qwen3 (new failure mode)

Runs 18 and 20 both fail on `20260311_parasomnia_research_unit` with `EOF while parsing a list
at line 25 column 5`. Two different models, two different providers, same plan, same truncation
point. This strongly indicates the parasomnia plan exceeds the output-token budget for these
models on their first call. This failure mode was NOT present in analysis/15 (gpt-oss-20b's
prior failure was hong_kong JSON extraction, not parasomnia EOF; qwen3 was 5/5).

This appears to be a plan-specific token-budget issue: parasomnia generates longer model outputs
than other plans (more technical, multi-dimensional domain). The failure is a code issue —
EOF is not in `_TRANSIENT_PATTERNS` and so gets no retry.

**Impact**: 2 plans lost per batch (one each for gpt-oss-20b and qwen3). Combined with the
haiku failures, parasomnia is now the highest-failure plan: 3/7 runs failed on it.

### NI2 — haiku hong_kong validation failure from "Controls" prefix omission (surfaced latent issue)

Run 23 (claude-haiku) hong_kong lost all 7 levers because the model wrote semantically valid
tension pairs (`"Narrative structure vs. creative autonomy. Weakness: ..."`) without the leading
word `"Controls"`. The model follows the two-tension format correctly but drops the prefix on
this specific plan. The same model produced fully compliant reviews on silo (`"Controls
irreversible commitment vs. adaptive contingency. Weakness: ..."`) in the same run, confirming
the failure is domain-specific or context-sensitive, not a general model incapability.

This is the same all-or-nothing problem (code_claude I2, code_codex B3) previously confirmed
for gpt-5-nano parasomnia (run 12, analysis/15). The synthesis Direction 1 (auto-correction)
directly addresses this: 7 valid levers would have been recovered if `check_review_format`
prepended "Controls " before rejecting.

### NI3 — haiku parasomnia APITimeoutError (373s) (same class as earlier llama3.1 timeout)

Run 23 haiku parasomnia timed out after 373 seconds. This is consistent with parasomnia
being the most verbose plan (evidenced by runs 18, 20 EOF and run 23 timeout). The 3 failures
on parasomnia across 7 models (43% failure rate on this one plan) confirm it warrants special
handling — either schema slimming to reduce output token cost (Direction 2 from synthesis)
or plan-specific token budget controls.

### NI4 — Semantic deduplication gap confirmed in run 21 silo

"Resource Management for Longevity" (lever 7) and "Resource Utilization for Resilience"
(lever 12) in run 21 silo share nearly identical consequences and options with only the final
strategic phrase differing. The `DeduplicateLeversTask` did not catch them because it uses
exact-name matching. This is a pre-existing gap (code_claude I4, code_codex B5) now confirmed
with specific evidence in run 21.

---

## Verdict

**YES**: PR #295 is a correct, risk-free fix for a confirmed latent bug. The `break` → `continue`
change at line 278 is architecturally sound: it prevents call-3 from being silently suppressed
when call-2 fails after call-1 already succeeded, without any regression path. The fix was not
triggered in this batch because all 4 failures were call-1 failures, but that does not diminish
its value — the scenario it protects against (call-2 transient failure) can and will occur in
future runs. The net success rate change (32/35 → 31/35) is caused by new failure modes
(JSON EOF, haiku format drift, haiku timeout) that are orthogonal to this PR.

---

## Recommended Next Change

**Proposal**: Add auto-correction to `check_review_format` in `identify_potential_levers.py`
before hard-rejecting a response: if the field contains `" vs. "` and `"Weakness:"` but is
missing the `"Controls "` prefix, prepend `"Controls "` (and normalize `"versus"` → `"vs."`).
Only raise `ValueError` if the corrected form still fails. This converts run 23 hong_kong from
0 recovered levers to 7 recovered levers and raises haiku from 3/5 to 4/5 plans.

The synthesis provides a concrete 12-line implementation ready to merge.

**Evidence**: Confirmed by `history/1/23_identify_potential_levers/events.jsonl` line 5: all
7 hong_kong levers contain `" vs. "` and `"Weakness:"` but lack the `"Controls "` prefix
(e.g., `"Narrative structure vs. ..."`). The model followed the two-tension structure but
dropped the leading word. Same model succeeded on silo with fully compliant reviews in the
same run, proving it can produce the correct format and the failure is cosmetic. Cross-agent
consensus: insight_claude C2, code_claude I2/B2, code_codex B3/I1, synthesis Direction 1.
This is the single highest-leverage, lowest-risk code fix available.

**Verify**:
- Run claude-haiku-4-5-pinned against hong_kong_game. After the fix, `002-10-potential_levers.json`
  for hong_kong must contain 7 levers (vs. zero before). Check that auto-corrected reviews
  read naturally: `"Controls Narrative structure vs. creative autonomy. Weakness: ..."`.
- Confirm the auto-correction fires precisely: it must NOT fire on gpt-5-nano gta_game, where
  placeholder-copy reviews already start with `"Controls [Tension A] vs. [Tension B]..."` — those
  have "Controls" and should not be double-prepended.
- Confirm the fix does NOT regress gemini, gpt-4o-mini, or llama3.1 (all currently 5/5):
  their `002-9-potential_levers_raw.json` files should be identical before/after the fix (the
  validator only activates when "Controls " is absent).
- Watch haiku's parasomnia plan: the timeout (373s) is unrelated to `review_lever` auto-correction.
  Haiku is expected to remain 4/5 (not 5/5) after this fix alone.
- Verify the `"versus"` → `"vs."` normalization also fires: use a model known to write "X versus Y"
  (synthesis notes insight_codex identified this variant from run 23) and confirm the normalized
  form is stored in the output, not the raw `"versus"` spelling.
- Check that the `' vs. '` check in the correction condition doesn't misfire on edge cases:
  a review like `"Controls this idea, which is stronger vs. weaker interpretations. Weakness: ..."`
  already has "Controls" so the condition won't trigger — but test with "this is stronger vs.
  weaker interpretations. Weakness: ..." to confirm it gets corrected to something sensible.

**Risks**:
- Auto-prepending `"Controls "` to a model's run-on sentence could create awkward phrasing for
  reviews that are not actually in the intended two-sentence structure. The condition
  (`' vs. '` AND `'Weakness:'` both present) reduces this risk but doesn't eliminate it.
  Watch the first 5 runs of auto-corrected reviews for naturalness.
- The fix does not address the cases where a model writes neither "Controls" nor "vs." — those
  still hard-fail and discard the whole call. Per-lever salvage (synthesis Direction 1 original,
  analysis/15 Direction 1) remains the deeper fix for the all-or-nothing architecture.
- Once the auto-correction is in place, strengthening `check_review_format` to also check for
  `' vs. '` position (code_claude I3, code_codex B6) should be done in the same commit or
  immediately after, otherwise the validator will still be too weak (passes boilerplate with
  "Controls" anywhere in the string).

**Prerequisite issues**: None. PR #295 (`break` → `continue`) is already merged. The
auto-correction fix is independent. Schema slimming (Direction 2) and EOF retry (Direction 3)
are higher-effort improvements that can follow separately.

---

## Backlog

### Resolved by PR #295 (remove from backlog):
- **`break` → `continue` in call-2/3 failure handler** (was top priority from analysis/15
  synthesis, NI2 in analysis/14): The one-character fix is in place. Not yet exercised by
  any call-2-specific failure, but the code is correct.

### Still open (carried forward from analysis/15):

- **Partial-recovery telemetry**: Emit a structured event to `events.jsonl` when partial
  recovery fires (call-2 fails but call-1 succeeded). Low effort; makes audit machine-readable.
  Now that the `break` → `continue` fix is live, this event will eventually fire.
- **qwen3 consequence contamination repair validator**: `@field_validator('consequences', mode='after')`
  that strips trailing `"Controls … Weakness: …"` text. Present but under-sampled in analysis/16
  (qwen3 had a parasomnia failure and only 4 plans available). Still relevant for qwen3 runs.
- **`activity_overview.json` inflation under parallel workers** (race condition): One-line guard
  in `track_activity.py:207`. Low priority; affects diagnostics only.
- **Per-lever non-fatal validation (all-or-nothing cascade)**: The auto-correction (Direction 1)
  is a targeted band-aid. The deeper fix — parse levers individually and keep valid ones —
  remains open for cases where the auto-correction cannot recover a review. Medium effort;
  do after auto-correction lands.
- **Remove bracket placeholders from Pydantic field descriptions** (`[Tension A]`, `[Tension B]`,
  `[specific factor]` in `description=` strings): Confirmed leakage vector (run 12 before,
  run 19 after). Replace with concrete non-copyable examples.
- **`summary`/`strategic_rationale` prompt contradiction** (code_codex B1/B2): The Pydantic
  schema says `summary` is a 100-word critique; the system prompt requires the exact form
  `Add '[full strategic option]' to [lever]`. Additionally, the system prompt instructs
  `conservative → moderate → radical` progression then bans those labels — confirmed as
  the root cause of run 19's prefix violations. Both contradictions exist in source and should
  be resolved in a prompt_4 candidate.
- **`set_usage_metrics_path` race condition in parallel workers**: `runner.py:106,140` — global
  path not protected by `_file_lock`. Affects diagnostics only. Low priority.

### New items added by analysis/16:

- **JSON EOF truncation on parasomnia (runs 18, 20)**: `"eof while parsing"` not in
  `_TRANSIENT_PATTERNS` → no retry. Add to transient patterns, or better: introduce a
  `LLMResponseTruncatedError` subclass with token-budget escalation on retry. Pair with
  `strategic_rationale`/`summary` schema slimming (below) so the retry has room to succeed.
- **`strategic_rationale` and `summary` dead-generation overhead** (code_codex B4): Both
  fields are generated on every call (3× per plan) but `save_clean()` discards them and
  downstream consumes only levers. Removing them from `DocumentDetails` saves an estimated
  2250–4500 tokens per run and directly reduces EOF/timeout risk on parasomnia-class plans.
  This is synthesis Direction 2.
- **haiku hong_kong "Controls" prefix omission**: Auto-correction (recommended next change above)
  will resolve this directly.
- **haiku parasomnia APITimeoutError**: Token-budget exhaustion distinct from the EOF issue.
  Likely exacerbated by haiku's verbose consequence style (110 words avg). Schema slimming
  and/or a per-consequence word-count cap (`max_words=45`) would reduce this risk.
- **Semantic deduplication gap confirmed in run 21 silo** (Resource Management for Longevity
  vs. Resource Utilization for Resilience): Exact-name dedup misses paraphrased lever pairs
  with identical consequences. Lightweight fix: fingerprint first 60 chars of `consequences`
  during merge in `identify_potential_levers.py:290`. Lower priority than reliability fixes.
- **gpt-oss-20b failure shifted from hong_kong to parasomnia**: In analysis/15 it was hong_kong
  JSON extraction; in analysis/16 it is parasomnia EOF. The hong_kong issue may have resolved
  on its own (run 18 succeeds on hong_kong). The parasomnia EOF is a new failure class shared
  with qwen3. Monitor gpt-oss-20b hong_kong in the next batch to confirm whether it was fixed
  or just absent.
