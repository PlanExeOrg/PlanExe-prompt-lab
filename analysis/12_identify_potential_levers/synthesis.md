# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

**PR #286 verdict: KEEP.** The `max_length=7` removal eliminated the targeted haiku `gta_game` failure (run 87 → run 94: 4/5 → 5/5), recovered 21 high-quality domain-specific levers, and introduced zero regressions. Overall success rate stayed flat at 28/35 (80%) only because a llama timeout in run 89 coincidentally cancelled the haiku gain.

**nemotron is a total structural failure.** Both insight files confirm 0/5 in both runs 81 and 88. Not fixable by schema or prompt changes; requires model replacement.

**gpt-oss-20b fails specifically on `sovereign_identity`.** Runs 83 and 90 both fail with `Could not extract json string from output` at ~164 seconds. Same model, same plan, same failure class — not addressed by the PR.

**qwen3 consequence contamination persists.** ~70% of qwen3 levers append `review_lever` text verbatim into the `consequences` field. Visible in runs 85 and 92. Orthogonal to the PR.

**Missing `options == 3` validator is a confirmed bug.** Both code reviews independently flag that `parse_options()` only coerces string→list but never checks length. Run 89 produced 3 levers with only 2 options each in the final merged output, confirmed by insight_codex metrics (`Levers with wrong option count: 3`).

**Partial result loss on LLM call failure is a confirmed bug.** If call 3 of 3 fails, the two successfully collected `DocumentDetails` objects are discarded and the plan gets zero output. Both code reviews identify this as the root cause of empty output directories in runs 88 and 90.

**Overflow is now invisible.** After PR #286 removed `max_length=7`, 3 raw responses in runs 88–94 exceeded 7 levers with no log entry or metric. Both code reviews flag the absence of overflow telemetry.

---

## Cross-Agent Disagreements

### Disagreement 1: Is haiku's verbosity a problem?

- **insight_codex** ranks run 94 (haiku) #4 of 7, calling it "extremely verbose" with avg consequence length of 886 chars vs. the 279-char baseline.
- **insight_claude** ranks run 94 (haiku) #1, calling it "Excellent — deep, measurable, domain-specific."

**Resolution (verified against source):** The `Lever.consequences` field description in `identify_potential_levers.py:44` specifies "Target length: 3–5 sentences (approximately 60–120 words)." At ~130–150 words, haiku slightly exceeds the target but is substantively on-format. The *content quality* is genuinely superior (measurable trade-offs, domain-specific numbers), as insight_claude documents. The verbosity is a cost/token concern, not a correctness failure. Both views are partially right; haiku is the highest-quality model but the most expensive one.

### Disagreement 2: Is over-generation a "regression" from the PR?

- **insight_codex** frames the 3 raw responses over 7 levers as a new post-PR problem.
- **insight_claude** frames these as normal variance, already handled by `DeduplicateLeversTask`.

**Resolution:** Codex is more accurate here. The code at `identify_potential_levers.py:247–249` flattens all levers from all responses with no trim or log. The system prompt still says "Generate 5 to 7 MORE levers" on calls 2 and 3 (`identify_potential_levers.py:205`). Models producing 8–9 levers per call silently inflate merged output to 21–24 levers with no telemetry. This is a genuine visibility gap, not a correctness failure, and not a reason to revert the PR.

### Disagreement 3: Bug numbering for partial result loss

- **code_claude** calls the partial-result-loss bug **B2** and ties it to `identify_potential_levers.py:231–240`.
- **code_codex** labels it **B3** and ties it to `runner.py:130` (failure artifacts not preserved).

**Resolution:** These are two distinct but related issues. The `identify_potential_levers.py` loop (code_claude B2) discards already-collected `DocumentDetails` objects when a later call raises. The `runner.py` cleanup (code_codex B3) additionally deletes the `track_activity.jsonl` event log on failure. Both are real. The `identify_potential_levers.py` bug is higher priority because it silently discards valid lever content; the runner bug is an observability gap.

---

## Top 5 Directions

### 1. Add `options == 3` post-parse validator (and review-field format enforcement)

- **Type**: code fix
- **Evidence**: code_claude B3, code_codex B1, insight_codex metrics row 89 (`Levers with wrong option count: 3`, `Missing Controls in review: 4`, `Missing Weakness: in review: 3`). Confirmed by reading `identify_potential_levers.py:60–71`: `parse_options()` only decodes JSON string→list, never checks `len(v) == 3`. No other validator exists on `options`.
- **Impact**: Any model that occasionally under-generates options (run 89: llama, 3 violating levers in the final artifact) currently passes validation silently. A validator would either reject the lever at parse time (allowing the call to be retried or the lever to be dropped with a warning) rather than shipping it to downstream tasks that assume exactly 3 options. Also catches malformed `review_lever` fields (missing `Controls` / `Weakness:` clauses).
- **Effort**: Low. Add a `@field_validator('options', mode='after')` that raises `ValueError` if `len(v) != 3`. Add a companion validator on `review_lever` that checks for both the `Controls` and `Weakness:` substrings. No schema migration needed.
- **Risk**: If a model consistently fails the new validator, the entire call raises rather than producing partial output. Mitigated by combining with direction 2 (partial result recovery), so failing one lever doesn't lose the whole call.

---

### 2. Return partial results when any single LLM call fails (not the whole plan)

- **Type**: code fix
- **Evidence**: code_claude B2 (`identify_potential_levers.py:231–240`), code_codex B3. The 3-call loop at line 199 raises `LLMChatError` on any exception, discarding `responses` already collected in prior iterations. Confirmed by empty output directories in runs 88 and 90: nemotron and gpt-oss-20b fail mid-call, producing zero output even if earlier calls succeeded.
- **Impact**: Turns call-3 failures from total losses into partial recoveries. With 2 successful calls producing 10–14 levers, the plan can still proceed. Directly benefits nemotron (though its calls all fail regardless) and gpt-oss-20b's `sovereign_identity` scenario. Generalizes to any transient failure.
- **Effort**: Low-medium. Change the exception handler in the loop to `logger.warning` + `break` when `len(responses) >= 1`. Add a warning in the result metadata that the response count is partial.
- **Risk**: A plan completing with only 10 levers (from 2 calls) instead of 15–22 may have lower diversity. Downstream `DeduplicateLeversTask` would see fewer candidates. Acceptable tradeoff vs. zero output.

---

### 3. Add overflow telemetry (log warning when raw call returns >7 levers)

- **Type**: code fix (observability)
- **Evidence**: code_claude S2/I3, code_codex B2. After PR #286, `identify_potential_levers.py:242–244` appends responses with no check on lever count. insight_codex confirms 3 raw responses exceeded 7 levers in runs 88–94 (runs 89, 94). Neither the log nor the output metadata records this.
- **Impact**: Makes post-PR overflow visible without reverting the beneficial schema change. Enables future prompt tuning decisions: if overflow becomes frequent across models, a soft-clamp or prompt tightening is warranted; if it stays rare, no action needed. Very low implementation cost for high observability gain.
- **Effort**: Very low. After line 242, add `if len(result["chat_response"].raw.levers) > 7: logger.warning(...)`. Optionally record `overflow_count` in metadata.
- **Risk**: None. Purely additive logging.

---

### 4. Fix qwen3 consequence contamination via post-parse strip/reject

- **Type**: code fix + prompt change
- **Evidence**: code_claude (trace table entry for qwen3), code_codex S1/I1, insight_claude §C2 and §Negative-4. The `consequences` field description at `identify_potential_levers.py:34–46` already says "Do NOT include 'Controls ... vs.', 'Weakness:'" but there is no validator enforcing it. ~70% of qwen3 levers in run 92 have `review_lever` text appended verbatim to `consequences`.
- **Impact**: Affects all qwen3 runs (5/5 plans "succeed" but ~70% of levers have polluted `consequences` flowing into downstream plan documents). A post-parse check that detects `consequences` ending with a substring matching `review_lever` would let the code strip or reject the contamination. Alternatively, adding an explicit negative example in the system prompt could reduce the generation rate.
- **Effort**: Medium. The strip approach is lower risk: after building `LeverCleaned`, check if `consequences` ends with the `review` string and strip if so. The prompt approach requires testing across all models to avoid unintended side effects.
- **Risk**: A strip heuristic could over-trigger on levers that legitimately mention tension language. Use exact substring matching of the `review_lever` value as the detection key.

---

### 5. Fix thread-safety race on `set_usage_metrics_path` in runner.py

- **Type**: code fix
- **Evidence**: code_claude B1/I4. `runner.py:106` calls `set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")` outside `_file_lock`, then immediately enters `_file_lock` for `dispatcher.add_event_handler(track_activity)`. Under `workers > 1`, thread A sets its path, thread B overwrites it before thread A uses it, so usage metrics from thread A's plan land in thread B's output directory.
- **Impact**: Data integrity corruption of usage metrics under parallel execution. The `--workers` flag in the runner enables parallel plans; any multi-worker run risks cross-contaminated `usage_metrics.jsonl` files. Does not affect success/failure counts but corrupts cost/token accounting.
- **Effort**: Low. Move `set_usage_metrics_path(...)` inside `_file_lock` at both setup (line 106) and teardown (line 140).
- **Risk**: Minimal. Moves a global-state mutation inside an existing lock that already guards related operations. No behavior change for `workers=1`.

---

## Recommendation

**Fix the `options == 3` post-parse validator first (Direction 1).**

**Why this one:** It is the only issue where malformed data silently ships as "successful" output into the final `002-10-potential_levers.json` artifacts that downstream tasks consume. Run 89 is the concrete proof: 3 levers with 2 options each passed through Pydantic validation, were written to disk, and would have propagated to every downstream step that assumes exactly 3 options per lever. The two code reviews independently reached the same finding via different paths (code_claude B3; code_codex B1).

**What to change:**

File: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

After the existing `parse_options` validator (line 60–71), add two validators to the `Lever` class:

```python
@field_validator('options', mode='after')
@classmethod
def check_option_count(cls, v):
    if len(v) != 3:
        raise ValueError(f"options must have exactly 3 items, got {len(v)}")
    return v

@field_validator('review_lever', mode='after')
@classmethod
def check_review_format(cls, v):
    if 'Controls ' not in v:
        raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
    if 'Weakness:' not in v:
        raise ValueError("review_lever must contain 'Weakness: ...'")
    return v
```

When these validators reject a lever, the entire `DocumentDetails` parse fails, the call raises `LLMChatError`, and the loop moves on (or, once Direction 2 is also implemented, continues with partial results). This is strictly better than silently accepting malformed levers.

**Why not the others first:**
- Direction 2 (partial results) is valuable but requires Direction 1 to exist first so that malformed responses fail loudly rather than partially succeeding with bad levers.
- Direction 3 (overflow telemetry) is almost free but has no quality impact.
- Direction 4 (qwen3 contamination) affects only one model family and requires careful heuristic design.
- Direction 5 (thread-safety) is only observable under `workers > 1` and affects cost accounting, not plan correctness.

---

## Deferred Items

- **Direction 2 (partial result recovery)**: Implement after Direction 1. The two changes are complementary: Direction 1 makes bad partial responses fail loudly; Direction 2 ensures good partial responses aren't wasted.

- **Direction 3 (overflow telemetry)**: Low effort, can be done any time. Suggested as part of the same PR as Direction 1 or 2.

- **Direction 4 (qwen3 contamination)**: After the validator work is done. Consider adding a `@field_validator('consequences')` that checks for `Controls` / `Weakness:` substrings and rejects the lever if contamination is detected. Prompt changes carry cross-model risk and should be tested separately.

- **Direction 5 (thread-safety)**: Fix in `runner.py` as a standalone low-risk cleanup. Not urgent if `workers=1` is the standard operating mode.

- **nemotron model exclusion**: Both before and after runs confirm 0/5. This model should be removed from the test matrix; it adds noise and zero signal to the analysis. Not a code change; a runner configuration change.

- **gpt-oss-20b sovereign_identity**: Runs 83 and 90 both fail on the same plan. The plan appears to be too long for this model to produce structured JSON output. A pre-truncation step or plan chunking would be needed. Deferred pending investigation of whether `sovereign_identity` reliably exceeds the model's effective structured-output context limit.

- **S3 (case-sensitive deduplication)**: Low priority. The downstream `DeduplicateLeversTask` handles semantic near-duplicates. Exact case-insensitive matching is an incremental improvement, not a bug.

- **S2 / codex-S3 (stateless multi-call loop + wrapper prose overhead)**: The 3-call structure passes only lever names as context across calls, not semantic coverage. This limits diversity without eliminating overlap, and the `summary`/`strategic_rationale` fields add token overhead that is thrown away in the cleaned output. Both are architectural concerns warranting a separate design review.
