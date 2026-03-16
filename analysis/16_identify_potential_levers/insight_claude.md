# Insight Claude

## Overview

Seven history runs were examined: `1/17` through `1/23` in
`history/1/`, all using `prompt_3` (SHA-256:
`00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381`).
Each run exercised a different model against five baseline training plans:
`20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`,
`20260310_hong_kong_game`, and `20260311_parasomnia_research_unit`.

The meta.json contains no `pr_url`/`pr_title`/`pr_description` fields,
so no PR Impact section is required.

---

## Quantitative Metrics

### Success Rate by Run

| Run | Model | Workers | Plans | ✓ | ✗ | Rate |
|-----|-------|---------|-------|---|---|------|
| 17 | ollama-llama3.1 | 1 | 5 | 5 | 0 | 100% |
| 18 | openrouter-openai-gpt-oss-20b | 4 | 5 | 4 | 1 | 80% |
| 19 | openai-gpt-5-nano | 4 | 5 | 5 | 0 | 100% |
| 20 | openrouter-qwen3-30b-a3b | 4 | 5 | 4 | 1 | 80% |
| 21 | openrouter-openai-gpt-4o-mini | 4 | 5 | 5 | 0 | 100% |
| 22 | openrouter-gemini-2.0-flash-001 | 4 | 5 | 5 | 0 | 100% |
| 23 | anthropic-claude-haiku-4-5-pinned | 4 | 5 | 3 | 2 | 60% |
| **Total** | | | **35** | **31** | **4** | **88.6%** |

Sources: `events.jsonl` for each run.

### Failure Events

| Run | Plan | Error Type | Key Detail |
|-----|------|-----------|------------|
| 18 | parasomnia | JSON parse (EOF) | `EOF while parsing a list at line 25 column 5` |
| 20 | parasomnia | JSON parse (EOF) | `EOF while parsing a list at line 25 column 5` |
| 23 | hong_kong | review_lever format | 7 validation errors — all levers missing `Controls` prefix |
| 23 | parasomnia | APITimeoutError | 373 s; request interrupted |

All four failures resulted in zero output for the affected plan (entire
LLM call discarded).

Source: `history/1/18_identify_potential_levers/events.jsonl`,
`history/1/20_identify_potential_levers/events.jsonl`,
`history/1/23_identify_potential_levers/events.jsonl`.

### Lever Count in Merged Output Files (002-10-potential_levers.json)

These counts reflect the post-deduplication merged output from multiple
LLM calls (expected to exceed the per-call target of 5–7).

| Run | Plan | Lever count |
|-----|------|-------------|
| 17 | silo | 20 |
| 17 | parasomnia | 16 |
| 19 | parasomnia | 16 |
| 21 | silo | 17 |
| 22 | silo | 17 |
| 22 | parasomnia | 17 |
| 23 | silo | 21 |

All within expected range for 3 × 5–7 LLM calls merged.

### Approximate Consequences Field Lengths (chars, sampled lever 1)

| Run | Plan | Lever 1 name | Consequences length (approx) |
|-----|------|--------------|-------------------------------|
| 17 | silo | Ecosystem Maturity | ~134 |
| 21 | silo | Resource Allocation for Sustainability | ~250 |
| 22 | silo | Resource Allocation Strategy | ~230 |
| 23 | silo | Isolation Posture | ~580 |
| Baseline | silo | Resource Allocation Strategy | ~210 |

Run 17 (llama3.1) produces significantly shorter consequences. Run 23
(claude-haiku) produces the longest and most numerically specific.

### review Field Compliance

The prompt requires the format:
`"Controls [Tension A] vs. [Tension B]. Weakness: The options fail to consider [specific factor]."`
A Pydantic validator enforces that `review_lever` must contain the
literal substring `"Controls "` (with capital C).

| Run | Model | review format compliance | Notes |
|-----|-------|--------------------------|-------|
| 17 | llama3.1 | Partial — format present, content formulaic | Uses only "Physical vs. Informational Tensions" across all levers |
| 18 | gpt-oss-20b | Compliant (4/5 plans) | parasomnia failed pre-validation |
| 19 | gpt-5-nano | Compliant | Domain-specific tension pairs |
| 20 | qwen3-30b-a3b | Compliant (4/5 plans) | parasomnia failed pre-validation |
| 21 | gpt-4o-mini | Compliant | Domain-specific tension pairs |
| 22 | gemini-2.0-flash | Compliant | Domain-specific tension pairs |
| 23 | claude-haiku | Compliant for 3/5 plans | hong_kong: 7/7 levers missing `Controls` prefix |

### Template Leakage Count (Run 17, silo — 20 levers)

| Pattern | Count |
|---------|-------|
| Consequences starting "Immediate: Over-reliance on" | 7 |
| review tension "Physical vs. Informational" | 3 |
| review tension "Informational vs. Physical" | 4 |
| review Weakness clause verbatim: "The options fail to consider the [impact/potential for/risks]" | 20/20 |

All 20 levers in run 17 silo use the identical Weakness clause structure
with only the last noun changed. Source:
`history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### Semantic Duplicate Detection (Run 21, silo — 17 levers)

Two near-duplicate levers were found in the merged output:

| # | Lever name | Consequences opening |
|---|-----------|---------------------|
| 7 | Resource Management for Longevity | "Implement a circular economy model → Systemic: Achieve a 30% reduction in waste generation → Strategic: This enhances resource availability" |
| 12 | Resource Utilization for Resilience | "Implement a circular economy model → Systemic: Achieve a 30% reduction in waste generation → Strategic: This enhances resource security" |

The lever names differ but the consequences and options are nearly
identical. The DeduplicateLeversTask did not catch them because exact-
name matching misses semantic overlap.

Source:
`history/1/21_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

---

## Negative Things

### N1 — Parasomnia is the highest-failure plan (3/7 runs affected)

Runs 18, 20, and 23 all failed on `20260311_parasomnia_research_unit`.
The failure modes differ:

- Runs 18 and 20: JSON truncation at `line 25 column 5` — the LLM
  response was cut off mid-array, producing unparseable JSON. The
  truncation occurs at the same position across two different models and
  providers. This strongly suggests an output-token limit is being hit
  before the response completes.

- Run 23: APITimeoutError after 373 s — the model started generating but
  the connection timed out. Combined with the JSON truncation pattern in
  runs 18/20, this points to parasomnia consistently eliciting longer
  model outputs than other plans (likely due to its technical, multi-
  dimensional research design domain).

Each failure discards the full LLM output and logs an error. No partial
recovery occurs.

Sources: `history/1/18_identify_potential_levers/events.jsonl`,
`history/1/20_identify_potential_levers/events.jsonl`,
`history/1/23_identify_potential_levers/events.jsonl`.

### N2 — Pydantic review_lever validator causes total plan failure (Run 23, hong_kong)

Run 23 (claude-haiku-4-5-pinned) failed on `20260310_hong_kong_game`
with 7 Pydantic `ValidationError`s — all 7 levers had a `review_lever`
field missing the `"Controls"` prefix:

```
levers.0.review_lever: "Narrative structure vs. ...ot ambiguity increases."
levers.1.review_lever: "Corporate versus state t...motionally unambiguous."
...
```

The model produced valid tension-vs-tension pairs but dropped the
"Controls" word. The Pydantic validator treats this as a hard constraint
and rejects the entire response. The same model produced fully compliant
reviews on the silo plan ("Controls irreversible commitment vs. adaptive
contingency. Weakness: ..."), showing the failure is domain-specific
rather than a general model incapability.

The failure cost 52 s of inference with no usable output.

Source:
`history/1/23_identify_potential_levers/events.jsonl` (line 5, full
error trace).

### N3 — Run 17 (llama3.1) produces low-quality, formulaic output

All 20 levers in the run 17 silo output use a rigid consequence template:

> "Immediate: Over-reliance on X → Systemic: Reduced Y → Strategic: Dependence on Z"

Seven of 20 levers open with "Immediate: Over-reliance on". The review
field uses only two tension types across all levers: "Physical vs.
Informational" and "Informational vs. Physical" — regardless of what
the lever is about.

For comparison:
- **Run 17 silo, lever 1 consequences**: "Immediate: Over-reliance on
  initial resources → Systemic: Reduced resilience to external shocks →
  Strategic: Dependence on fragile internal systems" (~134 chars, no
  domain metrics).
- **Run 23 silo, lever 1 consequences**: "Immediate: The facility
  adopts either sealed-off operation or maintains emergency surface
  contact protocols. → Systemic: Full isolation reduces external
  dependency by ~100% but increases catastrophic-failure consequence
  severity by 8–12× (single-point failures become lethal); partial
  contact enables knowledge inflow and reduces psychological strain by
  an estimated 30–40%..." (~580 chars, specific quantitative estimates).

Run 17's output may score as technically valid (no schema errors) but
does not meet the prompt's requirement for "measurable outcomes" and
"chain three SPECIFIC effects."

Sources: `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### N4 — Semantic deduplication misses paraphrased lever pairs

The `DeduplicateLeversTask` (downstream of this step) does not catch
levers that are semantically identical but differ in name. Run 21
(gpt-4o-mini) silo produced "Resource Management for Longevity" and
"Resource Utilization for Resilience" with nearly identical consequences
and options — only the final strategic phrase differed. These occupy two
slots in the merged output instead of one.

This is a code-level issue (deduplication uses name matching rather than
embedding similarity).

Source:
`history/1/21_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
(levers at positions 7 and 12 zero-indexed).

### N5 — review Weakness clause is not validated; formulaic outputs pass silently

The prompt requires: `"Weakness: The options fail to consider [specific
factor]."` but the Pydantic validator only checks for `"Controls"` in
the prefix. Run 17 (llama3.1) uses boilerplate Weakness clauses across
all 20 levers ("The options fail to consider the impact on X" / "The
options fail to consider the potential for Y") that technically comply
with the code validator but are substantively meaningless.

---

## Positive Things

### P1 — 88.6% overall success rate

31 of 35 plan-level executions succeeded. Four runs (17, 19, 21, 22)
achieved 100% success across all five plans.

### P2 — Gemini-2.0-flash achieves best speed/quality/reliability tradeoff

Run 22 (gemini-2.0-flash-001) completed all 5 plans in 34–38 s each
(total wall-clock ~160 s with 4 workers), produced domain-specific
consequences with measurable indicators (e.g., "+30% storage and
annotation costs", "-15% participant retention") and followed the
review format correctly. No errors.

Source: `history/1/22_identify_potential_levers/events.jsonl`,
`history/1/22_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

### P3 — Claude-haiku silo output represents best observed quality

Run 23 (claude-haiku-4-5-pinned) silo output produced 21 levers with
highly specific, numerically grounded consequences (e.g., "N+3
redundancy increases construction cost by 35–45%", "aquifer-dependent
systems reduce capex by $600M", "full isolation reduces psychological
strain by an estimated 30–40%"). Lever names are domain-appropriate and
non-generic ("Sectional Independence and Cascade-Failure Containment",
"Subsystem Commissioning Overlap and Systemic Risk Compression").

This represents the ceiling quality achievable with prompt_3 on the
silo plan.

Source:
`history/1/23_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P4 — review_lever two-sentence consolidation works for majority of models

Prompt_3 added the requirement for a combined one-field `review_lever`
with both clauses. Five of seven models consistently produce the
`Controls X vs. Y. Weakness: ...` two-part structure. This change from
prior iterations appears effective.

### P5 — GPT-5-nano delivers high parasomnia quality with 100% success

Run 19 (openai-gpt-5-nano) succeeded on all 5 plans including parasomnia
(in 284–313 s per plan, the slowest successful model). Its parasomnia
output shows well-structured consequences with percentages:

> "Broadening inclusion criteria increases enrollment rate → Systemic:
> Higher participant diversity (+20% representation of atypical
> parasomnia presentations) but potentially lower event capture rate per
> participant (-10% adjudicated events)"

Source:
`history/1/19_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

---

## Comparison

### vs. Baseline Training Data

The baseline silo output
(`baseline/train/20250321_silo/002-10-potential_levers.json`) uses a
consequence format that leads with a context sentence before the chain:

> "Centralized control of resources will likely lead to inequitable
> distribution and potential social unrest. Immediate: Resource
> hoarding → Systemic: 15% increase in black market activity → Strategic:
> Undermines social stability and long-term silo viability."

This format differs from the three-part chain alone. None of the current
runs use the leading sentence format, suggesting prompt_3 explicitly
constrains the format to the chain only. The baseline levers include
domain-specific tension names ("Controls Efficiency vs. Equity") and
specific Weakness clauses, consistent with the prompt template.

Content richness in the current runs ranges from below baseline
(run 17/llama3.1) to substantially above baseline (run 23/claude-haiku
silo).

### Model Quality Ranking (for comparable successful plans)

1. **claude-haiku-4-5** (when it succeeds): Most specific, longest
   consequences, best domain naming — but lowest reliability (60%)
2. **gemini-2.0-flash-001**: Consistently good quality, fastest, 100%
   reliable
3. **gpt-5-nano**: Good quality, 100% reliable, but slow
4. **gpt-4o-mini**: Good quality, 100% reliable, moderate speed
5. **gpt-oss-20b**: Good quality where it succeeds, fails on parasomnia
6. **qwen3-30b-a3b**: Good quality where it succeeds, fails on parasomnia
7. **llama3.1**: Below baseline quality, template leakage, but 100%
   reliable

---

## Evidence Notes

All claims above cite specific file paths. Key artifacts:

- **Run meta.json files** (model/workers info): `history/1/{N}_identify_potential_levers/meta.json`
- **Error logs**: `history/1/{18,20,23}_identify_potential_levers/events.jsonl`
- **Run 17 template leakage**: `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
- **Run 21 semantic duplicate**: `history/1/21_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (levers "Resource Management for Longevity" vs. "Resource Utilization for Resilience")
- **Run 23 silo quality**: `history/1/23_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
- **Run 22 parasomnia quality**: `history/1/22_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
- **Baseline silo**: `baseline/train/20250321_silo/002-10-potential_levers.json`
- **Prompt**: `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`

---

## Hypotheses

### Prompt Hypotheses

**H1**: The Pydantic `review_lever` validator requires the literal string
`"Controls "` as a prefix. Models that are marginally compliant (e.g.,
using title-cased tension names without the word "Controls") fail the
entire plan. Adding explicit wording reinforcement — such as
`"Your review MUST begin with the exact word 'Controls'"` — may reduce
partial-compliance failures for models like claude-haiku on non-primary
plans. Expected effect: eliminate run 23-style format failures on
hong_kong and similar plans.

**H2**: The current prompt says "5 to 7 levers per response." This
guidance is soft and models comply per-call, but the merged output
always exceeds 7. The downstream consumer (synthesis, downstream steps)
sees 15–21 levers. Whether this causes downstream quality issues is
unclear. If trimming is needed, adding "The final merged set should
contain exactly 7 unique levers" in a post-dedup step would be more
effective than a prompt change.

**H3**: The prompt does not prevent llama3.1-class weak models from
using generic tension types ("Physical vs. Informational") across all
levers. Adding a prohibitions entry like `"NO generic tension categories
(e.g., 'Physical vs. Informational') — tensions must be specific to
this domain"` may improve quality for weaker models without harming
stronger ones.

### Code Hypotheses

**C1**: Runs 18 and 20 both truncate at `line 25 column 5` of the JSON
response for the parasomnia plan. This is a consistent max-tokens hit
point for two different models. The pipeline does not currently detect
JSON truncation and retry with adjusted token limits. Adding a check for
incomplete JSON (e.g., `json.JSONDecodeError` with EOF at end-of-list)
before promoting to `LLMChatError` would enable targeted retry with
higher `max_tokens` for that plan. Expected effect: recover the 2 lost
parasomnia plans (runs 18, 20) without changing the prompt.

**C2**: The `review_lever` Pydantic validator creates a hard binary
outcome: all 7 levers pass or the entire response is discarded. When
claude-haiku produces 7 valid levers with a semantic-but-not-literal
format error, discarding all levers is a large penalty. A code-level
fix could: (a) attempt auto-correction by prepending "Controls " when
a "vs." tension pair is found without the prefix, or (b) apply per-lever
validation and discard only non-compliant levers while keeping valid
ones. Expected effect: recover 7 valid levers from run 23 hong_kong
instead of zero.

**C3**: The `DeduplicateLeversTask` appears to use exact or near-exact
name matching. Run 21's "Resource Management for Longevity" and "Resource
Utilization for Resilience" passed through deduplication despite
having identical consequences and options. Upgrading deduplication to use
embedding similarity (cosine distance on consequences text) would catch
semantic duplicates. Expected effect: reduce lever set redundancy,
improving downstream analysis quality.

---

## Questions For Later Synthesis

1. **Parasomnia plan reliability**: Three of seven models failed on
   `20260311_parasomnia_research_unit`. Is this plan systematically
   harder for LLMs due to its technical domain, or is it a token-budget
   issue? If it is a token-budget issue (C1), should the runner increase
   `max_tokens` per plan or per model when prior attempts returned
   truncated JSON?

2. **review_lever strictness vs. recovery**: Should the Pydantic validator
   for `review_lever` be relaxed (soft-check) or should auto-correction
   be implemented (C2)? What is the precedent from earlier analysis
   iterations (e.g., the `max_length=7` removal)?

3. **llama3.1 quality floor**: Run 17 (llama3.1) is technically 100%
   reliable but produces low-quality output. Is this a prompt issue (H3)
   or an inherent model limitation? Should it be excluded from future
   runs or used only as a reliability baseline?

4. **Should the Weakness clause be validated?** Currently only the
   "Controls X vs. Y." prefix is code-validated. The Weakness clause is
   prompt-only guidance. Run 17 shows models can generate formulaic
   Weakness clauses that pass validation while being substantively empty.
   A code-level validator for the Weakness clause (e.g., minimum length,
   must not start with "The options fail to consider the") would improve
   average quality.

5. **Semantic deduplication**: Is the current `DeduplicateLeversTask`
   using embedding similarity or string matching? If string matching, C3
   (embedding similarity) should be prioritized.

---

## Reflect

Prompt_3 is largely effective: 88.6% plan success across 7 diverse
models, and the review_lever consolidation (from prior iteration) is
working for 5 of 7 models. However, two systemic issues remain:

1. **Token budget exhaustion on complex plans** (runs 18, 20, 23) — this
   is a code-level issue, not a prompt issue. The prompt cannot control
   how much output a model generates before hitting max_tokens. The runner
   needs truncation detection and retry with higher limits.

2. **Hard schema enforcement discards all-or-nothing** — the Pydantic
   validator for `review_lever` discards an entire plan's worth of levers
   when any single lever has a format violation. Partial recovery (C2)
   would significantly improve the failure-to-partial-success conversion
   rate.

The quality gap between llama3.1 and claude-haiku (both 100% reliable
in their respective successes) is striking — the prompt elicits
structured compliance from all models but cannot force strong models'
domain specificity out of weak models. This is expected, but it means
the prompt_3 optimization is hitting a model-capability ceiling for
weaker models.

Gemini-2.0-flash-001 stands out as the practical optimum: 100% reliable,
fast, and good quality. For production use, this model appears safer than
claude-haiku-4-5-pinned for this step.

---

## Potential Code Changes

**C1** (high priority): Detect JSON EOF truncation in
`identify_potential_levers` runner/LLMChat interface. When a
`json.JSONDecodeError` with "EOF" is encountered during parsing of
LLM response, log a specific `LLMChatError` subtype (e.g.,
`LLMResponseTruncatedError`) and retry with increased `max_tokens`.
This would recover the 2 parasomnia failures in runs 18 and 20 and
potentially the run 23 parasomnia timeout.

**C2** (medium priority): In the Pydantic `DocumentDetails` validator for
`review_lever`, add an auto-correction step before raising
`ValueError`: if the field contains " vs. " but does not start with
"Controls", prepend "Controls " and re-validate. This converts a total
failure into a partial correction for cases like run 23 hong_kong.

**C3** (low priority): In `DeduplicateLeversTask`, add embedding-based
similarity as a secondary deduplication pass after name-based dedup.
Use a cosine similarity threshold on the `consequences` text to catch
semantic duplicates like those in run 21 silo.

---

## Summary

Runs 17–23 tested prompt_3 against 7 different models. Overall success
is 31/35 = 88.6%. Four failures occurred across three distinct failure
modes: (1) JSON truncation on the parasomnia plan for gpt-oss-20b and
qwen3-30b-a3b; (2) `review_lever` format validation rejection on
hong_kong for claude-haiku; (3) APITimeout on parasomnia for
claude-haiku. All three failures are code-addressable without prompt
changes.

Content quality varies significantly: llama3.1 (run 17) produces
formulaic, below-baseline consequences with template leakage in review
fields; gemini-2.0-flash (run 22) and gpt-5-nano (run 19) produce
domain-specific, quantitatively grounded outputs; claude-haiku (run 23)
produces the highest quality when it succeeds (extremely detailed
numerical estimates), but has the lowest reliability (60%).

The most impactful next step is C1 (JSON truncation detection and retry),
which would address the most frequent failure mode affecting 3 of 4 total
failures (including the parasomnia timeout cascade for claude-haiku). C2
(review_lever auto-correction) would address the remaining failure. Both
are code fixes with no prompt changes required.
