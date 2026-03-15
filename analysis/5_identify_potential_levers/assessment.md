# Assessment: Fix `consequences` and `options` Pydantic field descriptions (schema fix iteration)

## Issue Resolution

**What change was applied:**
The after meta.json contains no `pr_title` or `pr_description`, so the change is inferred from the
code reviews. The `consequences` field description in `identify_potential_levers.py` was changed from
the plain-prose example with "30 words" hint:

```python
# Before
consequences: str = Field(
    description="Briefly describe the likely second-order effects or consequences of pulling this lever "
                "(e.g., 'Choosing a high-risk tech strategy will likely increase talent acquisition "
                "difficulty and require a larger contingency budget.'). 30 words."
)
```

to the chain-format contract:

```python
# After
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "
        "Target length: 150–300 words."
    )
)
```

The `options` description was also updated from `"2-5 options for this lever."` to `"Exactly 3 options for this lever. No more, no fewer."` based on the absence of 2-option violations for most models and the code_claude B2 observation. This is synthesis/4 Direction #1 applied.

**Is the core issue resolved?**

Yes — for the primary target. The root cause of run 37's (gpt-4o-mini) 100% consequence chain failure
was the schema-level plain-prose example overriding the system prompt. After the fix, run 44
(gpt-4o-mini, same model) produces proper I→S→S chains in 75/75 levers.

Verified directly from output files:

- Before (`history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`):
  `"Choosing a diversified funding strategy will likely enhance financial stability, increase stakeholder engagement..."`
  — plain prose, zero chain markers.

- After (`history/0/44_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`):
  `"Immediate: Allocate funding to prioritize essential infrastructure development → Systemic: Achieve a 20% reduction in initial construction costs through strategic partnerships → Strategic: Establish a sustainable financial model that attracts ongoing investment..."`
  — full I→S→S chain with a quantitative indicator.

**Residual symptoms:**

1. **Length target miscalibration.** The "150–300 words" target (≈750–1500 chars) is far above the
   baseline calibration of ~56 words (~280 chars). This new length requirement is the direct cause of
   run 45 (haiku) timing out on parasomnia at 432s. The synthesis/5 Direction #1 recommends replacing
   this with "3–5 sentences (approximately 60–120 words)". Evidence:
   `analysis/5_identify_potential_levers/code_claude.md` S3; haiku avg ~700 chars per consequence
   × 5 levers × 3 calls = ~10,500 chars of consequence text per plan.

2. **Missing trade-off language.** The new description requires measurable indicators but does not
   explicitly require the trade-off tension framing. Run 44 (gpt-4o-mini) has 75/75 consequences
   lacking explicit trade-off language despite proper I→S→S chain. 240/450 levers across successful
   runs (53%) are missing this framing. Source: `analysis/5_identify_potential_levers/code_codex.md` S1.

---

## Quality Comparison

Models present in **both** batches: nemotron (32→39), llama3.1 (33→40), gpt-oss-20b (34→41),
gpt-5-nano (35→42), qwen3-30b (36→43), gpt-4o-mini (37→44), haiku (38→45).

| Metric | Before (runs 32–38) | After (runs 39–45) | Verdict |
|--------|---------------------|---------------------|---------|
| **Overall success rate** | 27/35 = 77.1% | 28/35 = 80.0% | IMPROVED |
| **gpt-4o-mini success rate** | 5/5 (run 37) | 5/5 (run 44) | UNCHANGED |
| **haiku success rate** | 3/5 (run 38; hong_kong+parasomnia timeout) | 4/5 (run 45; parasomnia only) | IMPROVED |
| **gpt-oss-20b success rate** | 3/5 (run 34) | 4/5 (run 41) | IMPROVED |
| **nemotron success rate** | 1/5 (run 32) | 0/5 (run 39) | REGRESSED |
| **llama3.1 success rate** | 5/5 (run 33) | 5/5 (run 40) | UNCHANGED |
| **Consequence chain format — gpt-4o-mini** | 75/75 violations (run 37) | 0/75 violations (run 44) | **MAJOR IMPROVEMENT** |
| **Consequence chain format — gpt-5-nano** | 38/75 chain violations (run 35) | 17/75 missing trade-off (run 42) | IMPROVED |
| **Consequence chain format — qwen3** | 30/75 chain violations (run 36) | 30/75 missing trade-off (run 43) | UNCHANGED |
| **Consequence chain format — haiku** | 17/47 chain violations (run 38) | 52/60 missing trade-off (run 45) | MIXED (format present; trade-off absent) |
| **Consequence chain format — llama3.1** | 0/75 (chain present; non-numeric 59/75) (run 33) | 0/75 (chain present; non-measurable 60/75) (run 40) | UNCHANGED (semantic problem persists) |
| **Avg consequence chars — gpt-4o-mini** | ~198 chars (run 37) | ~285 chars (run 44) | IMPROVED (closer to baseline ~280) |
| **Avg consequence chars — gpt-5-nano** | ~261 chars (run 35) | ~386 chars (run 42) | IMPROVED (above baseline; not excessive) |
| **Avg consequence chars — qwen3** | ~209 chars (run 36) | ~312 chars (run 43; inflated ~80 chars by review leakage) | MIXED |
| **Avg consequence chars — haiku** | ~867 chars (run 38) | ~1321 chars (run 45) | REGRESSED (150–300 word target is driving this) |
| **Avg option chars — gpt-4o-mini** | ~124 chars (run 37) | ~131 chars (run 44) | SLIGHTLY IMPROVED |
| **Avg option chars — gpt-5-nano** | ~133 chars (run 35) | ~121 chars (run 42) | SLIGHTLY REGRESSED |
| **Avg option chars — llama3.1** | ~88 chars (run 33) | ~91 chars (run 40) | UNCHANGED (codex cross-plan avg; silo shows label regression) |
| **Option count violations** | 9 llama3.1 (parasomnia) + 2 haiku = 11/122 | 1 llama3.1 (sovereign) = 1/75 (successful runs only) | IMPROVED |
| **Lever name uniqueness — gpt-4o-mini** | 74/75 (run 37) | 72/75 (run 44) | SLIGHTLY REGRESSED |
| **Lever name uniqueness — gpt-5-nano** | 75/75 (run 35) | 75/75 (run 42) | UNCHANGED |
| **Lever count violations (gta 16-lever overflow)** | 4 models affected (runs 33,35,37,38) | 0 models affected | IMPROVED (non-deterministic; may recur) |
| **Bracket placeholder leakage** | 1 (run 38 sovereign_identity "placeholder" lever) | 0 confirmed | IMPROVED |
| **Template leakage (verbatim prompt copying)** | 0 (already resolved by PR #273) | 0 | UNCHANGED |
| **Option prefix violations** | 1 "Radical radical" (run 38 haiku) | 0 | IMPROVED |
| **Null summaries — gpt-5-nano** | 0/15 raw (run 35) | 0/75 (run 42) | UNCHANGED (remains good) |
| **Null summaries — gpt-4o-mini** | 2/15 (run 37) | 6/75 (run 44) | SLIGHTLY REGRESSED |
| **strategic_rationale field** | Not explicitly reported in analysis/4 | 100% null across all 7 runs | NEWLY QUANTIFIED (universally null) |
| **review dual-component compliance — llama3.1** | 30/75 review opener violations (run 33, codex) | 17/75 review missing Controls + 13/75 missing Weakness (run 40) | UNCHANGED (alternation pattern persists) |
| **Review-in-consequences contamination — qwen3** | Not observed in run 36 | 45/75 Controls leaked + 60/75 Weakness leaked (run 43) | **NEW REGRESSION** |

Notes on metric evolution: "consequence chain violations" in analysis/4 measured missing I→S→S format;
"missing trade-off in consequence" in analysis/5 is a stricter follow-on metric. Direct chain-format
comparison is most reliable for gpt-4o-mini and gpt-5-nano where the before violation was format-level.

---

## New Issues

### N1 — Consequence length target "150–300 words" is severely miscalibrated
The new field description specifies 150–300 *words* as the target. Baseline averages ~56 words (~280 chars).
Run 45 (haiku) averages ~1321 chars (~264 words) per consequence and times out on parasomnia at 432s.
This timeout persists despite haiku improving from 2/5 to 1/5 failures — the miscalibration keeps
the worst plan (parasomnia) in the failure zone. Root cause: the change used "words" not "chars" and
set the minimum at 2.7× the baseline value.
Source: `analysis/5_identify_potential_levers/code_claude.md` S3.

### N2 — qwen3-30b review content contaminating consequences field (new failure mode)
Run 43 (qwen3-30b-a3b) appends the review's "Controls A vs. B. Weakness: ..." text to the end of
every consequences field, then repeats it in review_lever. This did not occur in run 36 (same model,
prior batch). Both code reviews flag the accumulated chat-history conditioning (calls 2/3 condition on
call 1's full JSON blob via `model_dump_json()` fallback) as an amplifier, and the weak field-boundary
description (consequences field now longer and more structured, but still lacks a prohibition on
review text). Affects 45/75 consequences with leaked Controls text, 60/75 with leaked Weakness text.
Source: `analysis/5_identify_potential_levers/code_codex.md` S2; insight_codex constraint table.

### N3 — llama3.1 option quality regression (label-like options)
Run 40 (llama3.1) produces single-word or short-label options ("Dictatorial Rule", "Meritocratic Council")
averaging ~35 chars in the silo plan, vs. run 33's full sentences ("Expand vertically, adding 24 floors
to the existing design"). The review alternation pattern (Controls-only / Weakness-only, never both)
persists from run 33 with the same 15/15 severity. The stricter `consequences` format requirement may
have consumed llama3.1's effective output capacity, degrading option quality. The review alternation
is a pre-existing issue not caused by this change.
Source: `history/0/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7–9`.

### N4 — `strategic_rationale` universally null (now confirmed at scale)
Both code reviews independently confirm `strategic_rationale` is `Optional[str]` with `default=None`
and is never mentioned in the system prompt. The after batch confirms this is 100% null across all
7 runs and all plans — not a model-specific issue but a schema design choice. This field is dead weight.
Source: `analysis/5_identify_potential_levers/synthesis.md` Cross-Agent Agreement point 3.

### N5 — Runner retry config mismatch (experiment skew identified)
code_codex B4 (analysis/5) identifies that `runner.py:94` creates `LLMExecutor(llm_models=llm_models)`
with no `RetryConfig`, while the production pipeline uses `RetryConfig()`. This means prompt-lab runs
have `max_retries=0`, making transient failures that production would retry count as hard failures.
This potentially exaggerates failure counts for gpt-oss-20b and haiku. Not caused by this change but
newly quantified in this batch.

---

## Verdict

**YES**: The `consequences` and `options` field description fix is a clear quality improvement and
should be kept. The gpt-4o-mini chain compliance flip from 0% to 100% (75/75 levers) is the strongest
positive signal in the entire optimization history so far. Haiku reliability improved from 3/5 to 4/5
plans. The 16-lever gta overflow that affected 4 models in the prior batch did not appear in any run
this batch. The immediate backlog item is to reduce the "150–300 words" target to "3–5 sentences"
(synthesis/5 Direction #1), which addresses the remaining haiku timeout without rolling back the
chain-format improvement.

---

## Recommendations

### Should the next iteration follow the "after" synthesis recommendation?

**Yes.** Synthesis/5 Direction #1 is the right immediate next step: reduce the `consequences` length
target from "150–300 words" to "3–5 sentences (approximately 60–120 words)" and add the explicit
trade-off prohibition (`"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text
in this field — those belong exclusively in review_lever."`). This corrects the length miscalibration
without reverting the chain-format win and blocks the qwen3 review-contamination pattern.

**Bundle with it (same PR):** Synthesis/5 Direction #2 — update `review_lever` field description to
require both components in one combined sentence: `"Required format: Two sentences. Sentence 1:
'Controls [Tension A] vs. [Tension B].' Sentence 2: 'Weakness: The options fail to consider
[specific factor].' Both sentences are mandatory."` This directly fixes llama3.1's 15/15 alternation
problem and is a one-line change.

### Issues from before that are now resolved (can be removed from backlog):

- **`consequences` field description plain-prose example** — replaced by chain format contract.
  gpt-4o-mini 0% → 100% chain compliance confirms this is resolved.
- **`options` field description "2-5 options"** — changed to "Exactly 3 options". Option-count
  violations dropped from 11 to 1 across all models.
- **"25% faster" template leakage** — still absent (carried over from PR #273 fix; no regression).
- **gta 16-lever overflow** — did not appear in runs 39–45. Likely non-deterministic rather than
  fixed, but no new evidence of it.

### New issues to add to the backlog:

1. **[HIGH] Reduce `consequences` length target** — change "150–300 words" to "3–5 sentences
   (approximately 60–120 words)" in `identify_potential_levers.py:35–37`. Direct cause of haiku
   timeout on parasomnia (432s). Expected to bring haiku from 4/5 to 5/5 plan coverage.

2. **[HIGH] Fix `review_lever` dual-component requirement** — update field description to require
   both "Controls [A] vs. [B]." AND "Weakness: ..." in every response. Fixes llama3.1's 15/15
   alternation pattern and future regression risk for other models.

3. **[HIGH] Add explicit prohibition: no review text in `consequences`** — add to the consequences
   field description: `"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique
   text in this field."` Fixes qwen3-30b review-in-consequences contamination (45–60/75 levers affected).

4. **[MEDIUM] Remove `strategic_rationale` from schema** — it is `Optional[str]` with `default=None`,
   never requested in the system prompt, and null in 100% of responses across all 7 runs and both
   batches. Remove to reduce schema complexity and false-signal noise. 6-line deletion in
   `identify_potential_levers.py`.

5. **[MEDIUM] Add `field_validator` for lever count and option count** — the 16-lever gta overflow
   did not appear this batch but is non-deterministic; run 40 sovereign_identity still produced one
   2-option lever. Add `@field_validator('levers')` enforcing `len == 5` and `@field_validator('options')`
   enforcing `len == 3` to trigger LLMExecutor retries on contract violations.

6. **[MEDIUM] Add production retry config to runner** — `runner.py:94`: change
   `LLMExecutor(llm_models=llm_models)` to `LLMExecutor(llm_models=llm_models, retry_config=RetryConfig())`.
   Eliminates experiment skew where transient failures count as hard failures vs. production.

7. **[LOW] Skip nemotron-3-nano-30b-a3b model** — 0/5 plans in run 39, now 4 consecutive batch
   failures (runs 24, 25, 32, 39) with identical JSON extraction errors. Wastes ~540s per batch.
   Add to a configurable skip list in `runner.py`.

8. **[LOW] Fix telemetry race condition** — `set_usage_metrics_path` called outside `_file_lock`
   in `runner.py:106`. Move inside lock. Needed for accurate per-plan LLM call counts (after batch
   shows 10 calls where 9 expected — direct symptom of this race).
