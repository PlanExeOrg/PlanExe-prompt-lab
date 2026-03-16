# Assessment: Remove max_length=7 hard constraint on levers schema

## Issue Resolution

**What the PR was supposed to fix:** PR #286 removed `max_length=7` from the `DocumentDetails.levers`
Pydantic field. When a model returned 8 levers in a single call, Pydantic raised `ValidationError`
(`List should have at most 7 items after validation, not 8`), discarding all levers from that call —
including valid ones. The PR argues that `DeduplicateLeversTask` already handles over-generation,
making the schema-level cap unnecessary.

**Is it resolved?** Yes, directly and completely.

- **Before (run 87, haiku, gta_game):** `history/0/87_identify_potential_levers/events.jsonl` line 7
  records `LLMChatError` → `1 validation error for DocumentDetails / levers / List should have at most 7 items after validation, not 8 [type=too_long]`. Plan failed; 0 levers saved.
- **After (run 94, same model, same plan):** `history/0/94_identify_potential_levers/events.jsonl`
  shows `run_single_plan_complete` for all 5 plans. `002-10-potential_levers.json` contains 21
  domain-specific, measurable levers for gta_game. No `too_long` error appears anywhere in runs 88–94.
- `too_long` Pydantic failures: **1 before → 0 after.** The failure class is eliminated.
- **Validation-related plan failures** (all types): **2 before → 0 after** (insight_codex metrics table).

**Residual symptoms:** None from the `max_length=7` failure class. The `min_length=5` constraint
(kept by the PR) has not been triggered in any run 88–94 output, so it is currently inert.

---

## Quality Comparison

All seven models appear in both batches (runs 81–87 and 88–94), enabling direct paired comparison.
Quantitative figures from `analysis/12_identify_potential_levers/insight_codex.md` aggregate metrics table.

| Metric | Before (runs 81–87) | After (runs 88–94) | Verdict |
|--------|--------------------|--------------------|---------|
| **Overall success rate** | 28/35 (80%) | 28/35 (80%) | UNCHANGED (net neutral: haiku +1, llama −1) |
| — haiku success | 4/5 | **5/5** | **IMPROVED** (PR fixed gta_game) |
| — llama3.1 success | 5/5 | 4/5 | REGRESSED −1 (ReadTimeout, unrelated to PR) |
| — gpt-oss-20b success | 4/5 | 4/5 | UNCHANGED |
| — gpt-5-nano success | 5/5 | 5/5 | UNCHANGED |
| — qwen3 success | 5/5 | 5/5 | UNCHANGED |
| — gpt-4o-mini success | 5/5 | 5/5 | UNCHANGED |
| — nemotron success | 0/5 | 0/5 | UNCHANGED (structural incompatibility) |
| **max_length Pydantic failures** | 1 | **0** | **FIXED** |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** (levers with ≠3 options) | 0 | 3 (run 89 llama, hong_kong_game) | REGRESSED (latent issue now visible; not caused by PR) |
| **Review format — missing `Controls`** | 0 | 4 (run 89 llama) | REGRESSED (same root cause: no post-parse validator) |
| **Review format — missing `Weakness:`** | 0 | 3 (run 89 llama) | REGRESSED (same root cause) |
| **Lever name uniqueness ratio** | 0.996 (495/497) | **0.998** (513/514) | IMPROVED slightly |
| **Template leakage** (bracket placeholders, forbidden option prefixes) | 0 | 0 | UNCHANGED |
| **Consequence chain format** (avg consequence chars) | 411.6 | 414.1 | UNCHANGED (+2.5, within noise) |
| **Content depth** (avg option chars) | 131.4 | 135.6 | IMPROVED slightly |
| **Cross-call duplication** (duplicate raw lever names) | 13 | **10** | IMPROVED |
| **Total merged levers captured** | 497 | **514** | IMPROVED (+17, recovered from haiku gta_game) |
| **qwen3 consequence contamination** | ~72% | ~70% | UNCHANGED (orthogonal to PR) |
| **Over-generation** (raw responses >7 levers) | 0 (all failed at validation) | 3 (runs 89×2, 94×1) | INFORMATIONAL — handled by DeduplicateLeversTask |

**Note on regressions:** The three new option-count and review-format violations all come from a
single run (89, llama3.1) in a single plan (hong_kong_game). This represents a pre-existing
enforcement gap (no post-parse validator), not a regression introduced by PR #286. The PR neither
caused nor widened this gap — llama3.1 was 5/5 before and 4/5 after (due to an unrelated timeout).
The violations would have been caught by `max_length=7` only if the call had also over-generated
levers, which is coincidental rather than causal.

---

## New Issues

### Surfaced (latent, not introduced by PR)

**N1 — Missing `options == 3` post-parse validator.** Run 89 (llama3.1, hong_kong_game) produced
3 levers with only 2 options each in the final `002-10-potential_levers.json` artifact. These passed
Pydantic validation silently because `parse_options()` (identified at `identify_potential_levers.py:60–71`)
only decodes JSON string → list and never checks `len(v) == 3`. Two code reviews independently
confirmed this gap (code_claude B3, code_codex B1). Downstream tasks that assume exactly 3 options
per lever will consume malformed data without warning.

**N2 — Missing review-field format enforcement.** The same run 89 output contains levers where
`review_lever` is missing `Controls` (4 levers) or `Weakness:` (3 levers), or both. No validator
checks for these substrings after parse. This was noted as a structural gap in both code reviews.

### Introduced (new after PR)

**N3 — Overflow is now invisible.** Before PR #286, a raw call returning 8 levers raised a
`ValidationError` that was logged as a plan error. After the PR, 3 raw responses in runs 88–94
returned 8–9 levers with no log entry or metric (confirmed by `insight_codex.md` constraint table:
`Raw responses >7 levers: 3`). The `identify_potential_levers.py:242–244` merge loop appends
responses with no count check. This makes overflow invisible to future analysis and operators.

**N4 — Haiku verbosity increased substantially.** Run 94 (haiku) averages 886 chars for
`consequences` versus the 279-char baseline target and 500-char before-PR average. The `Lever`
field spec at `identify_potential_levers.py:44` targets 60–120 words; haiku now runs at ~130–150
words per consequence. This is a token-cost concern, not a correctness failure — content quality
is substantively superior — but unchecked verbosity drift could become expensive at scale.

---

## Verdict

**YES**: The PR eliminates a targeted, confirmed failure class (haiku returning 8 levers → Pydantic
hard-fail → 0 levers saved) with zero net regressions. All four analysis agents (insight_claude,
insight_codex, code_claude, code_codex) independently reached the same verdict: KEEP. The overall
success rate staying at 28/35 (80%) is coincidental — a llama timeout cancelled the haiku gain —
and does not diminish the PR's correctness.

---

## Recommended Next Change

**Proposal:** Add a `@field_validator('options', mode='after')` to the `Lever` class in
`identify_potential_levers.py` that raises `ValueError` if `len(v) != 3`, plus a companion
`@field_validator('review_lever', mode='after')` that requires both `Controls` and `Weakness:`
substrings. This makes malformed levers fail at parse time rather than silently propagate to
downstream tasks.

**Evidence:** Convincing. Two independent code reviews reached the same finding via different paths
(code_claude B3, code_codex B1). Run 89 is a concrete, reproducible artifact: 3 levers with 2
options each in `history/0/89_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:48,58,68`,
confirmed by insight_codex's constraint metrics (`Levers with wrong option count: 3`,
`Missing Controls in review: 4`, `Missing Weakness: in review: 3`). The prompt at
`prompts/identify_potential_levers/prompt_2_...txt:5` explicitly requires exactly 3 options per
lever, so the validator enforces the stated contract rather than imposing a new constraint.

**Verify (next iteration):**
- **Primary signal:** Levers with wrong option count must drop from 3 → 0 across all models.
  Watch run 89's successor (llama3.1, hong_kong_game) specifically — that is where all 3 violations
  originated.
- **Review format compliance:** `Missing Controls in review` and `Missing Weakness: in review`
  must drop from 4/3 → 0. If they do not, the `check_review_format` validator is not triggering,
  which would indicate a code path miss.
- **Confirm no new total-plan failures:** If the new validator causes entire LLM calls to fail
  (rather than individual levers), check whether runs that were previously 5/5 regress. The key
  models to watch are llama3.1 (run 89 had the violations) and any model with lower baseline
  compliance.
- **Partial result behavior:** If Direction 2 (partial result recovery) is NOT implemented
  alongside this change, verify that a single lever failing the validator does not silently discard
  the remaining 14–21 valid levers in the call. Check that error handling is at the lever level,
  not the call level — or confirm that the `DocumentDetails` parse fails the whole list at once
  (the current behavior), which means the call raises `LLMChatError` and the loop continues.
- **Overflow visibility:** Confirm that N3 is also addressed (e.g., by adding a warning log when
  a raw response returns >7 levers) so overflow becomes observable in the next analysis batch.

**Risks:**
- **Call-level rejection cascade:** The current Pydantic structure validates `DocumentDetails` as
  a unit. If `check_option_count` raises on a single lever, the entire `DocumentDetails.levers`
  list fails and the call raises `LLMChatError`. For models that occasionally produce one
  malformed lever alongside 6 valid ones, this discards the entire call rather than just the bad
  lever. Without Direction 2 (partial result recovery) in place, a strict validator could
  reintroduce a variant of the B2 partial-result-loss bug. Mitigate by implementing Direction 2
  at the same time, or by catching the validator error at the lever level before building the list.
- **qwen3 contamination amplification:** qwen3's `consequences` field often ends with `Controls ...
  Weakness: ...` text from the `review` field. If `check_review_format` is added to `review_lever`,
  qwen3 will likely still pass (its review fields appear intact); but if the validator is
  accidentally applied to `consequences` content, it would incorrectly match the contamination and
  suppress valid levers. Ensure validators are scoped only to the `options` and `review_lever`
  fields.
- **haiku's verbosity is not constrained by this change.** N4 (886-char consequences) will persist.
  If token cost becomes a concern, a separate compactness instruction or consequence-length cap
  would be needed.

**Prerequisites:** None. The options == 3 validator can be implemented independently. The synthesis
recommends doing Direction 3 (overflow telemetry) in the same PR as a very-low-effort observability
improvement.

---

## Backlog

### Resolved — remove from backlog

- **B3 (analysis 11): `max_length=7` hard-fails instead of truncating.** Fixed by PR #286.
  Evidence: zero `too_long` Pydantic failures in runs 88–94.

### Persisting — keep in backlog

- **qwen3 consequence contamination (~70%):** `review_lever` text bleeds into `consequences` in
  ~70% of qwen3 levers (confirmed in runs 85 and 92). A post-parse strip heuristic or prompt
  negative example is needed. Medium effort.
- **gpt-oss-20b `sovereign_identity` JSON failure:** Runs 83 and 90 both fail on the same plan
  with `Could not extract json string from output` at ~164 seconds. Likely a model context limit
  on long structured plans. Requires investigation into pre-truncation or plan chunking.
- **nemotron structural incompatibility (0/5):** All 10 nemotron runs (81, 88) fail with empty
  JSON output. Not addressable by schema or prompt changes; the model should be removed from the
  test matrix.
- **B2 (analysis 11) / Partial result loss:** When any LLM call in the 3-call loop raises,
  previously collected `DocumentDetails` objects are discarded. Empty output directories in runs
  88 and 90 confirm this. Complement to the new validator work (Direction 1 + Direction 2 should
  be done together).
- **Thread-safety race on `set_usage_metrics_path`** (`runner.py:106` outside `_file_lock`):
  Corrupts `usage_metrics.jsonl` under `workers > 1`. Low urgency if standard mode is
  `workers=1`.

### New — add to backlog

- **N1: Missing `options == 3` post-parse validator.** Run 89 produced 3 levers with 2 options
  in a successful final artifact. No validator exists to catch this at parse time. **(High
  priority — this is the synthesis's top direction.)**
- **N2: Missing `review_lever` format enforcement** (`Controls` + `Weakness:` both required).
  Run 89 had 4 levers missing `Controls` and 3 missing `Weakness:` in a successful artifact.
  Can be addressed in the same change as N1.
- **N3: Overflow telemetry absent.** After PR #286, 3 raw responses exceeded 7 levers with no log
  entry. Low effort to add; pairs well with the N1/N2 validator PR.
- **N4: Haiku verbosity drift.** Avg consequence length 886 chars vs 60–120 word target. Token
  cost concern at scale. Low urgency; monitor in future iterations.
