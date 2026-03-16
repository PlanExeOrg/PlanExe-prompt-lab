# Assessment: fix: auto-correct review_lever before hard-rejecting

## Issue Resolution

**PR #296 targeted**: Claude-haiku-4-5-pinned failed on `hong_kong_game` in run 23 with 7
Pydantic ValidationErrors — all 7 levers had `review_lever` written in the format `"Narrative
structure vs. …"` (valid tension pair, missing only the leading word "Controls"). The validator's
substring check (`if 'Controls ' not in v`) treated this as a hard failure, discarding 52s of
inference with zero usable output. PR #296 was supposed to fix this by prepending "Controls "
when `" vs. "` and `"Weakness:"` are present but the prefix is absent, and by normalising
"versus" → "vs." before validation.

**Behavioral evidence** (directly verified from artifacts):

- **Run 23 (before), haiku hong_kong**: `history/1/23_identify_potential_levers/events.jsonl`
  shows `run_single_plan_error` with 7 ValidationErrors, all `review_lever must contain
  'Controls [Tension A] vs. [Tension B].'`. The model wrote e.g. `"Narrative structure vs. …
  not ambiguity increases."` — a semantically valid tension pair, no "Controls" prefix. Zero
  levers output.
- **Run 30 (after), haiku hong_kong**: `history/1/30_identify_potential_levers/events.jsonl`
  shows `run_single_plan_complete` at 219.21s. Direct inspection of
  `history/1/30_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  confirms all reviews start with "Controls …" (e.g., `"Controls directorial auteurism vs.
  commercial risk mitigation…"`). The plan recovered fully.

**Critical discrepancy — code mechanism not confirmed**:

Both code reviewers (code_claude S1; code_codex S1) independently read the current source and
report that `check_review_format` (lines 86–99) contains **no auto-prepend logic** — the
validator still only raises `ValueError` on failure:

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if 'Weakness:' not in v:
    raise ValueError("review_lever must contain 'Weakness: ...'")
return v
```

No `"Controls " + v` prepend, no `"versus"` → `"vs."` normalisation. The cross-agent synthesis
confirms: *"Both code reviewers independently verify that no such auto-correction exists in
check_review_format (lines 86–99). The validator still only raises on failure."*

**Implication**: Haiku's hong_kong recovery cannot be attributed to the claimed code change.
Since both batches used the same prompt (prompt_3, identical SHA-256), the improvement is most
likely model stochasticity — the model happened to include "Controls" in run 30 but not in run
23. The parasomnia recovery (373s timeout → 291s success) is similarly unexplained by PR #296
and is probably a variance artefact.

**Residual symptoms**: Without confirmed auto-correction in code, future haiku runs on plans
where the model omits "Controls" would still fail. The original code recommendation (analysis/16
synthesis D5) remains unimplemented.

---

## Quality Comparison

All 7 models appear in both batches. Before = runs 1/17–1/23 (analysis/16). After = runs
1/24–1/30 (analysis/17). Metrics drawn from insight_claude and insight_codex quantitative tables
for both iterations; direct artifact verification performed for haiku (runs 23 and 30) and qwen3
(run 27 silo).

| Metric | Before (runs 1/17–1/23) | After (runs 1/24–1/30) | Verdict |
|--------|------------------------|------------------------|---------|
| **Overall success rate** | 31/35 (88.6%) | 34/35 (97.1%) | IMPROVED (+8.5pp) |
| **haiku success** | 3/5 (60%) — hong_kong validation error, parasomnia timeout | 5/5 (100%) | IMPROVED (+2 plans; mechanism unconfirmed) |
| **qwen3 success** | 4/5 (80%) — parasomnia JSON EOF | 5/5 (100%) | IMPROVED (+1; attribution unclear — PR #296 does not address JSON EOF) |
| **gpt-oss-20b success** | 4/5 (80%) — parasomnia JSON EOF at line 25 | 4/5 (80%) — parasomnia JSON EOF at line 58 | UNCHANGED (persistent failure, EOF line advanced) |
| **gpt-5-nano success** | 5/5 | 5/5 | UNCHANGED |
| **gpt-4o-mini success** | 5/5 | 5/5 | UNCHANGED |
| **gemini-2.0-flash success** | 5/5 | 5/5 (wave-1 config error, wave-2 all ok) | UNCHANGED (infrastructure noise added) |
| **llama3.1 success** | 5/5 | 5/5 | UNCHANGED |
| **Review format hard failures** | 7 (run 23, haiku hong_kong) | 0 across all 34 successful plans | IMPROVED |
| **Bracket placeholder leakage** | 6 levers (run 19, gpt-5-nano, gta_game) | 6 levers (run 24, llama3.1, silo call-3) | UNCHANGED (count same; shifted model) |
| **Option count violations (raw)** | 5 responses out of range (run 17, llama3.1) | 4 responses out of range (run 24, llama3.1) | UNCHANGED (only llama3.1 affected) |
| **Lever name uniqueness (final)** | 100% all runs | 100% all runs | UNCHANGED |
| **Template leakage (raw review violations)** | 53 (run 19, gpt-5-nano) | 41 strict mismatches (run 26, gpt-5-nano) | SLIGHTLY IMPROVED for gpt-5-nano |
| **qwen3 consequence contamination** | Present across 4/5 plans (codex did not measure; claude notes partial detection) | 66/85 levers (100% of all 5 plans; verified in run 27 silo) | REGRESSED in measurement (fully confirmed; likely a detection improvement, not a new regression) |
| **Content depth — avg option words** | haiku=33.3w, gemini=14.9w, gpt-4o-mini=14.6w | haiku=39.3w, gemini=16.0w, gpt-4o-mini=14.3w | SLIGHTLY IMPROVED overall; haiku most notable |
| **Cross-call duplicate lever names** | 22 (run 17, llama3.1); 0 for all others | 22 (run 24, llama3.1); 0 for runs 25–30 | UNCHANGED |
| **gpt-5-nano output tokens (silo)** | Not separately measured | 136k tokens vs. ~40k others (10 calls, 117k output) | NEW ANOMALY (informational; cost=0 at test tier) |
| **Over-generation (>7 levers/call)** | 5 responses (run 17, llama3.1) | 4 responses (run 24, llama3.1) | UNCHANGED (downstream dedup handles extras) |

---

## New Issues

### NI1 — Auto-correction not confirmed in code (primary risk)

The PR title and description claim that `check_review_format` was updated to auto-prepend
"Controls " and normalise "versus" → "vs.". Both code reviewers read the source and find no
such logic. The synthesis is unambiguous: the code only raises, it does not repair.

If haiku (or any model) produces review fields that follow the two-sentence structure but omit
"Controls" on a future plan, the validator will still reject the entire batch — the same failure
mode as run 23. The behavioral improvement is real but fragile. This is the highest-priority
open item.

### NI2 — llama3.1 bracket contamination in call-3 (newly confirmed)

Run 24 (llama3.1) silo: levers 9–14 in the final merged output (`002-10-potential_levers.json`)
have bracket-wrapped consequences: `"Immediate: [Establish a strict hierarchical structure →
Systemic: [Create a controlled environment…] → Strategic: [Risk amplifying…]"`. Calls 1 and 2
are clean; the contamination is specific to call-3. Six of 21 levers (29%) are affected.
Likely cause: the follow-up call prompt injects prior lever names as a bracketed list (lines
231–234 of `identify_potential_levers.py`), and the Pydantic field descriptions use `[Tension A]`
bracket placeholders, together triggering template-mode output from llama3.1 on the third call.

### NI3 — gpt-5-nano token explosion (136k tokens for silo)

Run 26 (gpt-5-nano) generated 136,363 total tokens for a single silo plan (10 calls, ~117k
output tokens) — 3–4× any other model on the same plan. Cost is $0 (free/test tier), but if
moved to a paid endpoint this would be anomalously expensive. Cause is likely extreme per-lever
verbosity in each LLM call. Schema slimming (remove `strategic_rationale` + `summary`) would
reduce this automatically.

### NI4 — gemini stale model alias wastes 5 plan starts

Run 29: the runner attempted `openrouter-paid-gemini-2.0-flash-001` (not registered) for all 5
plans, producing 5 spurious `run_single_plan_error` events before recovering on a second wave
with the correct name `openrouter-gemini-2.0-flash-001`. The stale "paid" alias in the LLM
config is a one-time cleanup item; adding pre-flight model-name validation to `runner.py` before
the plan loop would prevent recurrence with any future typo.

---

## Content Quality Regression (External Feedback)

**Critical finding**: An external review comparing full PlanExe reports for hong_kong_game rated
the baseline report **6.5/10** and the report built on optimized levers **5.8/10**. The reviewer's
verdict: *"Version 2 improved specificity, but regressed in credibility."*

The optimization loop has been maximizing structural compliance (success rate: 88.6% → 97.1%)
while the actual content quality has degraded. Key observations from the external review:

- *"The added specificity does not look evidence-backed; it looks selected because it sounds
  plausible."*
- *"The newer version leans harder into marketing copy disguised as analysis."*
- *"The newer report's strategic decisions read more like a framework generator output and less
  like a producer forcing hard decisions."*
- *"It also still contains suspicious uplift numbers like pre-sales increasing 15–20%, which
  remain unsupported."*
- *"The newer report is better at pretending to be investor-ready. The older report is actually
  slightly more trustworthy."*

### Measured impact on lever verbosity

| Metric | Baseline (hong_kong) | Iter 17 haiku (hong_kong) | Change |
|--------|---------------------|--------------------------|--------|
| Lever count | 15 | 21 | +40% |
| Avg consequences length | 269 chars | 980 chars | **+3.6×** |
| Avg option length | 162 chars | 321 chars | **+2.0×** |
| Avg review length | 153 chars | 319 chars | **+2.1×** |

The system prompt's mandatory quantification (*"Include measurable outcomes: a % change, capacity
shift, or cost delta"*), verbose consequence chain (*"Immediate → Systemic → Strategic"*),
formulaic option triads (*"conservative → moderate → radical"*), and tech-forcing (*"Radical option
must include emerging tech/business model"*) are the direct drivers. These produce output that is
longer and more specific on the surface but less grounded and less credible underneath.

**This changes the priority order for the next iteration.** Content quality regression affects
every successful plan (34/35), while the EOF retry fix affects one failure case (1/35). The next
iteration should simplify the system prompt to restore content quality before pursuing further
structural fixes.

---

## Verdict

**CONDITIONAL**: The behavioral outcomes are strong — 97.1% success rate is the best observed
across all three iterations, and haiku recovered from 3/5 to 5/5. However, the PR's claimed
mechanism (auto-correction in `check_review_format`) is not confirmed by code review. Without
the safety net in code, haiku's hong_kong recovery may be stochastic, and a future run of haiku
on a plan where it omits "Controls" would still cause a total-batch discard.

**Conditions to make this a full YES**:
1. Verify whether auto-correction logic exists anywhere in the codebase (not found in
   `check_review_format` lines 86–99, but may be elsewhere).
2. If absent, implement the auto-prepend in `check_review_format` as originally specified in
   analysis/16 synthesis Recommendation (5-line change), providing a reliable safety net.

---

## Recommended Next Change

**Proposal**: Add `"eof while parsing"` (case-insensitive) to `_TRANSIENT_PATTERNS` in
`worker_plan/worker_plan_internal/llm_util/llm_executor.py` (line 41). When gpt-oss-20b
truncates on `parasomnia_research_unit`, the plan currently dies immediately because the error
is not classified as retriable. Classifying it as transient enables automatic retry on the next
fallback LLM in the chain.

**Evidence**: Three consecutive batches — runs 1/18 (analysis/16), 1/20 (analysis/16), and
1/25 (analysis/17) — all fail on the same plan with the same error string (`Invalid JSON: EOF
while parsing a list`). The truncation line advanced from 25 → 58 between runs 18/20 and run
25, showing provider-side variability, which means a retry has a nonzero chance of completing
successfully. All four analysis agents (insight_claude N1/C1; insight_codex C2; code_claude I1;
code_codex I3/B2; synthesis Direction 1) reach consensus on this fix.

**Verify**: After landing the change, run gpt-oss-20b against parasomnia and confirm:
- `events.jsonl` shows the EOF error followed by a retry event (not an immediate `run_single_plan_error`)
- `outputs.jsonl` shows `status=ok` for parasomnia (not `status=error`)
- `history/1/{new_run}_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` exists with ≥10 levers
- No regression on any of the four other plans (silo, gta_game, sovereign_identity, hong_kong)
- Check gpt-oss-20b's LLM chain config: if only one model is in the chain, the retry exhausts
  immediately and the EOF fix alone will not recover the plan — pair with schema slimming (D2).

**Risks**:
- If gpt-oss-20b's LLM chain has no fallback, the transient classification produces a retry
  with the same model at the same token budget, reproducing the truncation. Pair with Direction 2
  (remove `strategic_rationale` + `summary` from `DocumentDetails`) to shrink the per-call
  response budget and give the retry a better chance.
- The string `"eof while parsing"` is highly specific and will not match schema-mismatch or
  model-capability failures. Very low false-positive risk.
- `"invalid json"` is a broader alternative but risks retrying on genuine format errors where
  the model produced syntactically broken JSON for schema reasons. Prefer the narrow pattern.

**Prerequisites**: None. This is a standalone one-line addition. Optionally pair with Direction 2
(schema slimming) for combined effect.

---

## Backlog

### Resolved by PR #296 (conditionally — pending code confirmation):

- **review_lever hard-rejection cascade on haiku hong_kong** (analysis/16 N2, C2): Behavioral
  improvement confirmed — haiku hong_kong went from 0 levers to 5/5 success in the after batch.
  Mark as TENTATIVELY resolved. Re-open if a future haiku run fails with the same ValidationError
  pattern and the auto-correction is confirmed absent.

### Highest priority (carry forward):

- **gpt-oss-20b parasomnia EOF** — Three consecutive batches (runs 18, 20, 25). Fix: add
  `"eof while parsing"` to `_TRANSIENT_PATTERNS`. Pair with schema slimming for effectiveness.
  **Next PR candidate (synthesis Direction 1).**

- **review_lever auto-correction not in code** (analysis/16 synthesis Recommendation, deferred
  as D5 in analysis/17): `check_review_format` still only rejects; it does not prepend "Controls
  " when a valid tension pair exists. Implement the 5-line fix to eliminate the fragility risk.

### Medium priority (carry forward):

- **Remove `strategic_rationale` and `summary` from `DocumentDetails`** (analysis/16 synthesis
  Direction 2; analysis/17 synthesis D2): Both fields are generated three times per plan but
  discarded by `save_clean()`. Estimated savings: 300–700 output tokens per call × 3 calls =
  up to 2,100 tokens per plan. Direct benefit for haiku parasomnia (291s, close to timeout) and
  gpt-oss-20b truncation.

- **Fix `DocumentDetails.summary` field description** (code_claude B2; code_codex B1): The
  Pydantic `description=` for `summary` says "Are these levers well picked? … 100 words."
  while the system prompt requires `Add '[full strategic option]' to [lever]`. The description
  wins in structured generation — causing 0/15 exact-format compliance for runs 25–30. Fix or
  remove the field.

- **qwen3 consequence contamination** (analysis/17 synthesis Direction 4; code_claude I4;
  code_codex B4): 66/85 levers in run 27 have `review` text duplicated at the end of
  `consequences`. Fix: add a `@field_validator('consequences', mode='after')` that strips a
  trailing suffix matching the `Controls … Weakness:` pattern.

- **Pre-flight model name validation** (code_claude I5; code_codex B3; synthesis Direction 5):
  Invalid aliases (e.g., `openrouter-paid-gemini-2.0-flash-001`) currently burn one failed
  attempt per plan before recovery. Validate all `model_names` before the plan loop. Also clean
  up the stale "paid" alias in the LLM config directly.

### Lower priority (carry forward):

- **llama3.1 call-3 bracket contamination** (analysis/17 N3, code_codex S2): 6/21 levers in
  silo call-3 use `[bracket-wrapped]` consequences. The follow-up prompt injects prior lever
  names as a bracketed list, plausibly triggering template-mode output. Fix: use a numbered or
  dash-separated list instead of bracket notation for the names denylist (lines 231–234 of
  `identify_potential_levers.py`).

- **gpt-5-nano token explosion** (analysis/17 N; insight_claude reflection): 136k tokens vs.
  ~40k for other models on the same plan. No cost impact at current test tier, but a potential
  concern on paid endpoints. Schema slimming (above) will reduce this automatically.

- **Optimizer runner missing RetryConfig** (code_codex B2; synthesis D1): `prompt_optimizer/
  runner.py` builds `LLMExecutor` without `RetryConfig`, while the production pipeline at
  `run_plan_pipeline.py:171–174` passes `retry_config=RetryConfig()`. This gap means validation
  retries get only one attempt in the optimizer. Align for parity.

- **Semantic deduplication upgrade** (analysis/16 backlog): `DeduplicateLeversTask` uses
  exact-name matching; semantic near-duplicates (run 21: "Resource Management for Longevity" vs.
  "Resource Utilization for Resilience") pass through. Low priority relative to reliability fixes.

- **`set_usage_metrics_path` race condition** (code_claude B1; runner.py:106): Global path
  not protected by `_file_lock`; usage metrics may be misattributed across parallel plans.
  Affects observability only, not lever output quality.
