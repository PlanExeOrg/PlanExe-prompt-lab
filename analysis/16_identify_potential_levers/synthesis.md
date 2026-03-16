# Synthesis

## Cross-Agent Agreement

All four files (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **`review_lever` hard-rejection discards entire plans on a single format miss.** Run 23
   (claude-haiku-4-5) hong_kong lost all 7 levers because the model omitted the word
   "Controls". The validator treats this as a binary pass/fail on the whole response batch.
   All agents flag this as the most recoverable failure: the content was valid, only the
   prefix was wrong.

2. **JSON EOF truncation on parasomnia is unhandled.** Runs 18 and 20 both hit
   `EOF while parsing a list at line 25 column 5`. The error is not in `_TRANSIENT_PATTERNS`
   and so it gets no retry. All agents agree this is a code fix, not a prompt fix.

3. **Run 22 (gemini-2.0-flash-001) is the best practical performer.** 100% plan success, fast,
   domain-specific consequences, no violations. Mentioned by both insight files as the
   reference optimum.

4. **Semantic deduplication uses name matching only.** Run 21 let "Resource Management for
   Longevity" and "Resource Utilization for Resilience" through with identical consequences.
   All agents note this as a code gap.

5. **The system prompt contains a contradiction that promotes label leakage.** It instructs
   models to show `conservative → moderate → radical` progression (line 169 in the source),
   then explicitly bans `Conservative:` / `Moderate:` / `Radical:` prefixes (line 186).
   Both code reviews flag this as the root cause of run 19's 5 forbidden-prefix violations.

6. **`strategic_rationale` and `summary` are generated on every call but not consumed
   downstream.** `save_clean()` serialises only `self.levers`; `DeduplicateLeversTask` reads
   only the clean file. These fields are dead-generation overhead, produced three times per
   plan, and contribute to EOF and timeout failures on verbose plans.

---

## Cross-Agent Disagreements

### Disagreement 1 — What exactly caused run 23 hong_kong to fail?

- **insight_codex** says the model used `versus` instead of `vs.`, causing the exact-token
  check to reject the response.
- **insight_claude** says all 7 levers were missing the `Controls` prefix (showing excerpts
  like `"Narrative structure vs. ..."`).

**Verdict (confirmed by source code):** insight_claude is correct. The validator at line 95
checks `if 'Controls ' not in v:` — a substring check for the word "Controls", not for "vs.".
The actual validator never checks for "vs." at all (code_claude B2, code_codex B6 both confirm
this). The model wrote valid tension pairs (`Narrative structure vs. [Tension B]`) but omitted
the leading word "Controls". The `vs.` discrepancy in insight_codex conflates two separate
issues: (a) the missing "Controls" that caused the hard failure and (b) a separate `vs.`
enforcement gap that exists but did not directly cause run 23's failure.

### Disagreement 2 — Is B4 (dead-generation overhead) a bug or an improvement?

- **code_codex** classifies `strategic_rationale`/`summary` generation as a bug (B4) because
  downstream never reads them, and it inflates output token cost.
- **code_claude** does not flag this as a bug, only noting lack of `max_tokens` control (I5).

**Verdict:** code_codex is substantially correct. The fields are unused downstream
(confirmed by reading `save_clean()` at line 344 and the pipeline at `run_plan_pipeline.py:422`).
Whether "bug" or "improvement opportunity" is a naming debate; the token waste is real. Removing
these fields from `DocumentDetails` is the most direct way to shrink the per-call response
budget and reduce truncation risk.

### Disagreement 3 — review_lever validator is "too strict" vs. "too weak"

- **insight files** say the validator is too strict: it rejects valid semantic content on a
  cosmetic prefix miss.
- **code reviews** say the validator is also too weak: it uses `not in` (substring) instead of
  `startswith`, does not check for `vs.`, and allows formulaic boilerplate through.

**Verdict:** Both are simultaneously true. The validator is too strict about the "Controls"
prefix (causing catastrophic full-response discard) and too weak about the structural contract
(does not enforce prefix *position*, does not check for `vs.`, does not block boilerplate). The
right fix is auto-correction before rejection for the strict failure mode, and a tighter position
check for the weak enforcement gap — but the auto-correction is higher priority because it
directly affects success rate.

---

## Top 5 Directions

### 1. Auto-correct `review_lever` before hard-rejecting the response
- **Type**: code fix
- **Evidence**: insight_claude N2/C2, insight_codex (run 23 hong_kong, run 19 53 raw violations),
  code_claude I2/B2, code_codex B3/I2. Consensus across all four files.
- **Impact**: Run 23 hong_kong recovers from 0 to 7 levers. Raises run 23 from 3/5 to 4/5 plans.
  Protects all models from catastrophic discard on cosmetic prefix omissions.
- **Effort**: low — 5-line change in `check_review_format` (prepend "Controls " when " vs. "
  and "Weakness:" are present but "Controls " is absent; also normalise "versus" → "vs.").
- **Risk**: Auto-correction could mask a structurally malformed review (e.g., if the model
  wrote a single run-on sentence with "vs." buried in it). The risk is low because the
  auto-correction only fires when "Weakness:" is also present, indicating the two-sentence
  structure was mostly followed.

### 2. Remove `strategic_rationale` and `summary` from the per-call schema
- **Type**: code fix + prompt change (embedded system prompt in source)
- **Evidence**: code_codex B4; confirmed by reading `save_clean()` (line 344) and
  `run_plan_pipeline.py:422` — neither field is consumed downstream.
- **Impact**: Reduces per-call output token budget by an estimated 150–300 tokens (one
  ~100-word `strategic_rationale` + one ~100-word `summary`). Across 3 calls × 5 plans, that
  is ~2250–4500 tokens saved per run. Directly shrinks the footprint that causes EOF truncation
  on parasomnia-class plans. If removed, runs 18 and 20 may recover their lost parasomnia plans
  without any explicit retry logic.
- **Effort**: medium — remove `strategic_rationale` and `summary` from `DocumentDetails` and
  purge their guidance from `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`.
- **Risk**: Loses per-run diagnostic summary. Mitigable by generating summaries in a separate
  post-dedup step or retaining them only in `save_raw()` as an optional field.

### 3. Add EOF/truncation detection to `_TRANSIENT_PATTERNS` in `llm_executor.py`
- **Type**: code fix
- **Evidence**: insight_claude N1/C1, insight_codex (runs 18/20), code_claude I1. Consensus
  from all three non-codex files.
- **Impact**: Would enable automatic retry for runs 18 and 20 on parasomnia (identical EOF at
  `line 25 column 5`). By itself this does not guarantee the retry succeeds unless token budget
  is also increased; combined with Direction 2 (schema slimming), the retry would use fewer
  tokens and has a better chance of completing.
- **Effort**: low for the detection step (add `"eof while parsing"` and `"unexpected end of
  data"` to `_TRANSIENT_PATTERNS` in `llm_executor.py`). Medium if a dedicated
  `LLMResponseTruncatedError` subclass with token-budget escalation is added.
- **Risk**: Retrying on EOF without a smaller schema or higher `max_tokens` may just reproduce
  the same truncation. Should be paired with Direction 2.

### 4. Fix the prompt contradiction: replace `conservative → moderate → radical` wording
- **Type**: prompt change (embedded in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` at line 169)
- **Evidence**: code_codex B2 (confirmed by source lines 169 and 186). Insight_codex flags 5
  forbidden `Radical:` prefix violations in run 19.
- **Impact**: Eliminates the self-referential leakage vector where the prompt teaches the banned
  labels before banning them. Affects all models, with the most benefit for mid-tier models
  (run 19 type) that tend to copy prompt wording literally.
- **Effort**: low — replace line 169 wording from `"clear progression: conservative → moderate
  → radical"` to a non-copyable description, e.g. `"clear progression from conventional
  practices toward disruptive or transformative approaches"`.
- **Risk**: Changing the progression instruction could reduce options quality if models relied
  on the label ladder to anchor diversity. Expect neutral-to-positive impact.

### 5. Add one concrete good example for `review_lever` in the system prompt
- **Type**: prompt change
- **Evidence**: insight_claude H1, insight_codex H1. Run 23 hong_kong (7 missed-prefix
  failures), run 19 (53 raw review violations even before Pydantic filtering).
- **Impact**: Complements the code auto-correction (Direction 1) by steering models toward
  correct output rather than only catching and repairing near-misses. Expected to reduce raw
  review violations across the heterogeneous model set.
- **Effort**: low — add one positive example (`"Controls Technical Ambition vs. Operational
  Risk. Weakness: The options fail to consider regulatory approval timelines."`) and one
  negative example (`Wrong: 'Technical ambition vs. operational risk. Weakness: ...'`) to the
  system prompt Section 4 under `review_lever`.
- **Risk**: Slightly increases prompt length (token cost per call). Low risk overall.

---

## Recommendation

**Pursue Direction 1 first: auto-correct `review_lever` before hard-rejecting the response.**

This is the minimum-effort, maximum-certainty fix available. The failure mode is confirmed:
run 23 hong_kong discarded 7 valid levers (52 s of inference, zero output) because the model
omitted the word "Controls" while otherwise following the two-sentence structure correctly. The
same model produced fully compliant reviews on other plans, proving it understands the format
but occasionally drops the leading word.

**Exact change** — in `identify_potential_levers.py`, update `check_review_format` (lines 86–99):

```python
@field_validator('review_lever', mode='after')
@classmethod
def check_review_format(cls, v):
    # Normalise "versus" to "vs." before any other checks.
    v_norm = v.replace(' versus ', ' vs. ').replace(' Versus ', ' vs. ')

    # Auto-correct: if the field has a tension pair and Weakness clause
    # but is missing the "Controls" prefix, prepend it.
    if 'Controls ' not in v_norm and ' vs. ' in v_norm and 'Weakness:' in v_norm:
        v_norm = 'Controls ' + v_norm

    if 'Controls ' not in v_norm:
        raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
    if 'Weakness:' not in v_norm:
        raise ValueError("review_lever must contain 'Weakness: ...'")
    return v_norm
```

This converts run 23 hong_kong from 0 levers to 7 levers recovered, at negligible performance
cost. It also benefits any future model that produces valid content while dropping the prefix
word.

After landing Direction 1, the next commit should be Direction 2 (schema slimming), which
addresses the root cause of the parasomnia failures. That fix has broader impact (3 plans
across 2 runs) and enables the EOF retry (Direction 3) to actually succeed when paired with a
smaller output budget.

---

## Deferred Items

- **Direction 3 (EOF retry)** — worth doing after Direction 2. On its own it may produce the
  same truncation again. Paired with schema slimming the retry has a real chance of completing.

- **Semantic deduplication** (code_claude I4, code_codex B5) — fingerprint the first 60 chars
  of `consequences` at merge time. Low effort, catches verbatim-consequence duplicates like
  the run 21 silo pair. Lower priority than reliability fixes.

- **`vs.` token position check** (code_claude I3, code_codex B6) — extend the validator to
  verify `' vs. '` appears in the first sentence. Low risk, tightens the contract. Can be added
  in the same commit as Direction 1 or deferred.

- **Direction 4 + 5 (prompt changes)** — label-leakage fix and review example are both low
  effort and should be bundled into a single prompt_4 candidate. Not urgent given runs 21/22
  already achieve 100% compliance with prompt_3.

- **`check_option_count` grace recovery** — similar to review_lever, a single lever with 2
  options causes full-response rejection. Could add the same auto-repair pattern (drop the
  offending lever and continue with remaining valid levers).

- **`set_usage_metrics_path` race condition** (code_claude B1, runner.py:106) — usage metrics
  can be misattributed in parallel workers. Real bug but affects only diagnostics, not output
  quality. Low priority.

- **TOCTOU race in history run-directory creation** (code_claude B3) — affects concurrent
  `python -m prompt_optimizer.runner` invocations from separate terminals. Rare in practice.
  Low priority.
