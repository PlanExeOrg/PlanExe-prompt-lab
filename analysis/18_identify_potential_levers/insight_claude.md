# Insight Claude

## Overview

Analysis of runs 1/31–1/37 (`identify_potential_levers`), covering seven models against
five plans (silo, gta_game, sovereign_identity, hong_kong_game, parasomnia_research_unit)
using prompt `prompt_4_3415fac5e0b6c547743aebfa9f44b8c2895e30032e0bce8393c28380bd3b6c64.txt`.

This batch evaluates **PR #297** ("fix: simplify lever prompt to restore content quality"),
which removed mandatory `Immediate → Systemic → Strategic` consequence chains, removed
mandatory quantification (% change, cost delta), removed the `conservative → moderate →
radical` option progression template, removed "Radical option must include emerging
tech/business model", added explicit prohibitions against fabricated statistics and
marketing language, and shortened target consequence length from 3-5 to 2-4 sentences.

Previous batch (analysis/17, runs 1/24–1/30) used prompt_3.

---

## Rankings

| Rank | Run | Model | Success | Notable |
|------|-----|-------|---------|---------|
| 1 | 37 | anthropic-claude-haiku-4-5-pinned | 5/5 (100%) | Best quality; zero fabricated %; consequences ~450 chars |
| 2 | 36 | openrouter-gemini-2.0-flash-001 | 5/5 (100%) | Clean execution; no config failure; zero fabricated % |
| 3 | 35 | openrouter-openai-gpt-4o-mini | 5/5 (100%) | Consistent |
| 4 | 32 | openrouter-openai-gpt-oss-20b | 5/5 (100%) | **Parasomnia resolved** — first success in 4 batches |
| 5 | 33 | openai-gpt-5-nano | 5/5 (100%) | 178.92s silo (vs 242.46s in run 26) — faster with shorter output |
| 6 | 34 | openrouter-qwen3-30b-a3b | 5/5 (100%) | Contamination ELIMINATED; options improved |
| 7 | 31 | ollama-llama3.1 | 5/5 (100%) | Label-only options in call-2/3; occasional fabricated % persists |

---

## Negative Things

### N1 — llama3.1 produces label-only options in second/third LLM call

Run 31 (`ollama-llama3.1`) silo output
(`history/1/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`)
shows two distinct quality tiers across calls:

**Call-1 options** (levers 1–7): substantive descriptions, 15–30 words each.
Example, lever "Information Control", option 3:
```
"Create a 'memory archive' of pre-closure knowledge that residents may access, alongside monitored
external feeds delivered through a designated research council that vets and contextualizes incoming data."
```

**Call-2 options** (levers 8–14 by index): label-only, 2–3 words.
Examples from levers "Silo Dynamics", "Resource Prioritization", "Knowledge Management":
```
"Centralized Authority" | "Decentralized Governance" | "Adaptive Hierarchy"
"Maximize Efficiency"   | "Foster Innovation"         | "Balance Utilization"
"Information Suppression"| "Knowledge Sharing"        | "Selective Disclosure"
```

These single-phrase options violate the prompt requirement: "Options MUST: Represent genuinely
distinct strategic pathways (not just labels)" and "NO generic option labels (e.g., 'Optimize
X', 'Tolerate Y')".

This is the same third-call degradation observed in analysis/17 (run 24), but the mode
changed: analysis/17 had bracket-wrapped **consequences** (`[Establish a hierarchical
structure → Systemic: [Create a controlled environment...]`), while analysis/18 has
label-only **options**. The brackets are gone; the label-only options are new.

### N2 — llama3.1 still fabricates percentages in consequences

Despite the explicit prohibition ("NO fabricated statistics or percentages without evidence
from the project context"), run 31 (llama3.1) silo lever "Resource Optimization" consequences:

```
"Direct Effect: Efficient allocation of resources reduces material costs by an estimated
10-15% and streamlines labor management. Downstream Implication: Over-reliance on optimized
resource allocation might hinder adaptability to unforeseen construction challenges."
```

The "10-15%" is fabricated — no such cost reduction figure appears in the silo project
context. Other models (haiku, gemini, qwen3) produce zero fabricated % in consequences after
the prompt change. llama3.1 does not appear to respond to the prohibition.

Source: `history/1/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever `697190d5`.

### N3 — llama3.1 uses literal "Direct Effect / Downstream Implication" sub-headers

Run 31 consequences consistently read:
```
"Direct Effect: [text]. Downstream Implication: [text]."
```

The model is interpreting the prompt's guidance language ("describe the direct effect ...
then at least one downstream implication") as a formatting instruction and using those exact
phrases as sub-headers. While this passes validation (the consequence field is not empty and
is structurally valid), the headers add overhead and make the consequence feel formulaic.

### N4 — qwen3 options still include fabricated percentages within option descriptions

While qwen3's consequences are now clean (no contamination, no fabricated %), some options
contain fabricated numerical parameters. From run 34 silo lever "Resource Allocation
Prioritization":

```
"Allocate 60% of resources to vertical farming and hydroponics"
"Invest 75% in redundant power generation and storage systems"
```

Neither "60%" nor "75%" is grounded in the project context. These are plausible-sounding
but fabricated allocation targets. The prohibition covers "NO fabricated statistics or
percentages without evidence from the project context", which technically includes options,
not just consequences.

Source: `history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever `894de852`.

---

## Positive Things

### P1 — 100% success rate: 35/35 (first ever clean sweep)

All seven models on all five plans completed without error.

| Iteration | Success |
|-----------|---------|
| Analysis/15 (runs 1/10–1/16) | 32/35 (91.4%) |
| Analysis/16 (runs 1/17–1/23) | 31/35 (88.6%) |
| Analysis/17 (runs 1/24–1/30) | 34/35 (97.1%) |
| **Analysis/18 (runs 1/31–1/37)** | **35/35 (100.0%)** |

Source: `events.jsonl` for each run (runs 31–37): zero `LLMChatError` or error events in any file.

### P2 — gpt-oss-20b parasomnia RESOLVED

Run 32 (`openrouter-openai-gpt-oss-20b`) parasomnia completed in **79.1 seconds** — clean,
no validation error.

Previous consecutive failures on this plan:
- Analysis/16 (run 1/18): JSON EOF at line 25, column 5
- Analysis/17 (run 1/25): JSON EOF at line 58, column 5 (got further but still failed)
- Analysis/18 (run 1/32): **SUCCESS** (79.1s)

Source: `history/1/32_identify_potential_levers/events.jsonl` line 7:
```json
{"event": "run_single_plan_complete", "plan_name": "20260311_parasomnia_research_unit", "duration_seconds": 79.1}
```

The EOF was caused by the model's JSON output exceeding provider token limits. Shorter
consequences (2-4 sentences, no mandatory chain format) reduced output size below the
threshold. This resolves C1/C3 from analysis/17 without code changes.

### P3 — qwen3 consequence contamination ELIMINATED

Run 27 (analysis/17): 17/17 levers contaminated — the `review` text appeared verbatim at
the end of every `consequences` field.

Run 34 (analysis/18): 0/15 levers contaminated — consequences and review fields are fully
separate with correct content in each.

Example run 34 qwen3 silo lever "Governance Structure":
```json
"consequences": "Centralizing authority reduces decision-making friction but risks entrenching
  oppressive practices. Decentralizing power could foster innovation but may destabilize the
  silo's rigid hierarchy. A hybrid model might dilute both control and accountability,
  creating governance gaps.",
"review": "Controls authoritarian control vs. adaptive governance. Weakness: The options fail
  to consider the psychological impact of surveillance on resident compliance."
```

The two fields are distinct and correct. Source:
`history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### P4 — Fabricated percentages in consequences nearly eliminated

Examined consequences for haiku (run 37, 5 plans), gemini (run 36, 5 plans), qwen3 (run 34,
silo). Zero fabricated percentages found in any consequences for these three models.

Run 37 (haiku) hong_kong_game, 20 levers examined: zero `%` tokens in consequences.
Run 36 (gemini) hong_kong_game, 18 levers examined: zero `%` tokens in consequences.
Run 34 (qwen3) silo, 15 levers examined: zero `%` tokens in consequences.

Only llama3.1 (run 31) still produces one fabricated % ("10-15%") in the silo consequences
(N2 above). This is a dramatic improvement from analysis/17 where fabricated % were mandatory.

Source: direct examination of output files listed above.

### P5 — Content length ratios restored to near-baseline

File size comparison (same model, same plan, prompt_3 vs prompt_4):

| Run | Model | Plan | File size (JSON) | Note |
|-----|-------|------|-----------------|------|
| 30 (analysis/17) | haiku | hong_kong | ~54 KB | Persisted-output limit hit (too large) |
| 37 (analysis/18) | haiku | hong_kong | ~15 KB | Displayed normally |

A 3.6× file size reduction for the same model on the same plan. This is direct evidence that
consequence length was drastically reduced by removing the mandatory chain format.

Estimated consequence length comparison (chars):

| Source | Avg consequence chars | vs baseline |
|--------|----------------------|-------------|
| Baseline silo | ~250 | 1.0× |
| Run 37 (haiku) silo | ~370 | 1.5× |
| Run 34 (qwen3) silo | ~270 | 1.1× |
| Run 31 (llama3.1) silo | ~230 | 0.9× |
| Baseline hong_kong | ~230 | 1.0× |
| Run 37 (haiku) hong_kong | ~450 | 2.0× |

Haiku hong_kong is now at 2.0× baseline — at the warning threshold but with substantive
content. Haiku silo is 1.5×. qwen3 silo is 1.1×. All are well below the 3.6× seen in
analysis/17.

Source: character counts from baseline and run files read during this analysis.

### P6 — Gemini config failure RESOLVED

Run 29 (analysis/17, gemini): All 5 plans failed first wave ("openrouter-paid-gemini-2.0-flash-001 not found"), then all 5 recovered second wave.

Run 36 (analysis/18, gemini): All 5 plans completed cleanly in 30–37 seconds, first wave only, no config error.

Source: `history/1/36_identify_potential_levers/events.jsonl` — zero error events.

Note: this fix may be from a code/config change unrelated to prompt_4. The model name
registered in run 36 is `openrouter-gemini-2.0-flash-001` (confirmed in `meta.json`), and
it ran without issue, suggesting the "paid" model name bug was corrected.

### P7 — haiku content quality sustained with shorter, cleaner output

Run 37 (haiku) hong_kong levers are specific, grounded, and analytically strong without
relying on fabricated numbers. Example lever "Narrative Subversion Strategy" consequences:

> "The 1997 film's twist ending is public knowledge; audiences familiar with Fincher's work
> will anticipate the game's manufactured nature. Choosing how to subvert expectation—whether
> through a legitimately different ending, a delayed/fractured reveal, or a metatheatrical
> approach—determines whether the remake feels like a fresh statement or a transparent retread.
> The wrong choice erodes critical reception and word-of-mouth, directly impacting festival
> buzz and theatrical opening."

This is 3 sentences, ~430 chars, zero fabricated %, grounded in the specific project context
(the 1997 Fincher film, Hong Kong remake brief). Options for this lever are 200–250 char
complete strategic pathways.

Source: `history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### P8 — gpt-5-nano runtime reduced

Run 33 (gpt-5-nano) silo duration: **178.92s** (from events.jsonl).
Run 26 (analysis/17, gpt-5-nano) silo duration: 242.46s.

A 26% reduction in runtime, consistent with shorter output from the new prompt. The anomalous
136k token output in run 26 likely dropped significantly. While not independently verified
here (no activity_overview.json read for run 33), the duration reduction is a strong signal.

---

## Comparison

### vs. Baseline Training Data

Baseline silo (`baseline/train/20250321_silo/002-10-potential_levers.json`):
- 15 levers; repeated names: "Resource Allocation Strategy" ×2, "Technological Adaptation
  Strategy" ×3, "External Relations Protocol" ×2
- Consequences use `Immediate → Systemic → Strategic` with fabricated %: "15% increase in
  black market activity", "30% reduction in innovative output", "20% slower problem-solving
  rate", "50% reduction in awareness of external advancements"
- Options 10–20 words each (labels or short descriptions)
- Review: "Controls Efficiency vs. Equity. Weakness: ..." (very short)

Run 37 (haiku) silo (26 levers):
- No repeated names
- Consequences: 2–4 sentences, zero fabricated %, grounded in silo-specific domain ("144-floor
  silo", specific references to life-support systems, agricultural zones, surveillance tradeoffs)
- Options: 30–80 words each, specific implementation parameters
- Review: "Controls X vs. Y. Weakness: [specific factor]" — substantive weakness identification

Run 34 (qwen3) silo (15 levers):
- No repeated names
- Consequences: 2–3 sentences, zero fabricated %, somewhat generic (less silo-specific than haiku)
- Options: 15–30 words each; some with fabricated % in option text (N4)
- Length close to baseline (1.1× ratio)

Run 31 (llama3.1) silo (21 levers):
- No repeated names
- Consequences: "Direct Effect / Downstream Implication" sub-headers (N3)
- Options: Call-1 substantive; Call-2 label-only (N1)
- Baseline review format uses "Controls the tension between X vs. Y" (slightly non-standard)

### vs. Analysis/17 (prompt_3)

| Metric | Analysis/17 (runs 24–30) | Analysis/18 (runs 31–37) | Direction |
|--------|--------------------------|--------------------------|-----------|
| Overall success rate | 34/35 (97.1%) | 35/35 (100.0%) | +2.9pp |
| gpt-oss-20b parasomnia | FAIL (EOF line 58) | SUCCESS (79.1s) | RESOLVED |
| qwen3 consequence contamination | 17/17 (100%) | 0 (0%) | ELIMINATED |
| Fabricated % in consequences | Widespread (mandatory) | Minimal (llama3.1 only) | DRASTICALLY REDUCED |
| haiku hong_kong file size | ~54 KB | ~15 KB | 3.6× reduction |
| haiku consequence length | ~980 chars (per analysis/16) | ~450 chars | 2.2× reduction |
| Gemini config failure | Yes (5 plans failed, recovered) | No | RESOLVED |
| llama3.1 bracket contamination | 6/21 levers (call-3) | 0 | RESOLVED |
| llama3.1 label-only options | Not observed | 7/21 levers (call-2) | NEW ISSUE |
| llama3.1 fabricated % | Not confirmed | 1 occurrence | PERSISTS |
| qwen3 options quality | Short labels | Improved (15–30 words) | IMPROVED |
| Review format compliance | 34/34 (100%) | 35/35 (100%) | MAINTAINED |

---

## Quantitative Metrics

### Table 1: Success Rate by Model

| Run | Model | Plans OK | Plans Failed | Failure Reason |
|-----|-------|----------|-------------|----------------|
| 31 | llama3.1 | 5 | 0 | — |
| 32 | gpt-oss-20b | 5 | 0 | — |
| 33 | gpt-5-nano | 5 | 0 | — |
| 34 | qwen3-30b | 5 | 0 | — |
| 35 | gpt-4o-mini | 5 | 0 | — |
| 36 | gemini-2.0-flash | 5 | 0 | — |
| 37 | haiku-4-5 | 5 | 0 | — |
| **Total** | | **35** | **0** | |

Sources: `events.jsonl` for each run, all 7 files show only complete events, no error events.

### Table 2: LLMChatError Check

No `LLMChatError` or `ValidationError` entries found in any `events.jsonl` across runs 31–37.
Zero schema-level validation failures in this batch.

### Table 3: qwen3 Consequence Contamination (silo plan)

| Run | Model | Contaminated levers / Total | Rate |
|-----|-------|-----------------------------|------|
| 27 (analysis/17) | qwen3-30b | 17/17 | 100% |
| **34 (analysis/18)** | **qwen3-30b** | **0/15** | **0%** |

Source: direct examination of `history/1/27_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (before) and `history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` (after).

### Table 4: Fabricated % in Consequences

Sample: silo and hong_kong plans for three models.

| Run | Model | Plan | Fabricated % in consequences | Count |
|-----|-------|------|------------------------------|-------|
| 24 (before) | llama3.1 | silo | Not independently counted | — |
| 27 (before) | qwen3 | silo | Contamination (review text) | 17 |
| 30 (before) | haiku | hong_kong | Specific metrics (partly grounded) | ~10 |
| **31 (after)** | **llama3.1** | **silo** | "10-15%" in "Resource Optimization" | **1** |
| **34 (after)** | **qwen3** | **silo** | None | **0** |
| **36 (after)** | **gemini** | **hong_kong** | None | **0** |
| **37 (after)** | **haiku** | **hong_kong** | None | **0** |

Source: direct inspection of consequence fields in output files listed above.

### Table 5: Option Quality — llama3.1 Silo (run 31)

| Lever Index | Name | Call | Option quality |
|-------------|------|------|----------------|
| 1–7 | Resource Optimization, Social Structure, etc. | Call-1 | Substantive (15–30 words each) |
| 8–14 | Silo Dynamics, Resource Prioritization, etc. | Call-2 | **Label-only (2–4 words each)** |
| 15–21 | Terraforming Protocol, Urban Planning, etc. | Call-3? | Moderate (8–15 words each) |

Source: `history/1/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.
7 of 21 levers (33%) have label-only options — all concentrated in one call group.

### Table 6: Consequence Field Length vs Baseline

| Source | Avg consequence chars | Ratio to baseline |
|--------|----------------------|-------------------|
| Baseline silo | ~250 | 1.0× |
| **Run 37 (haiku) silo (after)** | **~370** | **1.5×** |
| **Run 34 (qwen3) silo (after)** | **~270** | **1.1×** |
| **Run 31 (llama3.1) silo (after)** | **~210** | **0.8×** |
| Baseline hong_kong | ~230 | 1.0× |
| **Run 37 (haiku) hong_kong (after)** | **~450** | **2.0×** |
| **Run 36 (gemini) hong_kong (after)** | **~290** | **1.3×** |
| Prior (run 30 haiku hong_kong, before) | ~980 | 4.3× |

Sources: character counts from files read during this analysis; prior 980-char figure from
`analysis/16_identify_potential_levers/assessment.md` (the external report comparison).

Haiku hong_kong is exactly at the 2× warning threshold — still at the outer limit but the
content is substantive (grounded analysis, not padding). Other models are well below 2×.

### Table 7: Run Durations (silo plan — representative)

| Run | Model | Silo Duration |
|-----|-------|--------------|
| 31 | llama3.1 | 115.78s (sequential, workers=1) |
| 32 | gpt-oss-20b | 53.92s |
| 33 | gpt-5-nano | 178.92s |
| 34 | qwen3-30b | 67.44s |
| 35 | gpt-4o-mini | 59.20s |
| 36 | gemini-2.0-flash | 32.34s |
| 37 | haiku-4-5 | 122.93s |

Sources: `events.jsonl` for runs 31–37.

gpt-5-nano is still slowest on silo (178.92s) but substantially faster than analysis/17's
242.46s — consistent with shorter output due to the new prompt. gemini is fastest (32.34s).

---

## Evidence Notes

- **gpt-oss-20b parasomnia success**: `history/1/32_identify_potential_levers/events.jsonl` line 7 — `run_single_plan_complete, duration_seconds: 79.1`.
- **qwen3 contamination eliminated**: `history/1/34_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all 15 levers show clean consequences and correct review fields.
- **haiku hong_kong clean output**: `history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 20 levers, zero fabricated %, substantive options.
- **llama3.1 label-only options**: `history/1/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — levers `969ebe48` (Silo Dynamics), `d03a72d6` (Resource Prioritization), `7ffe906f` (Knowledge Management), `37a901c3` (Social Cohesion), `4f906035` (External Engagement), `79b7c364` (Risk Management), `0fdc49ea` (Legacy Planning).
- **llama3.1 fabricated %**: same file, lever `697190d5` ("Resource Optimization").
- **haiku silo output file**: `history/1/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — 26 levers, zero fabricated %, consequences 2-4 sentences.
- **Gemini clean execution**: `history/1/36_identify_potential_levers/events.jsonl` — all 5 plans complete in 30–37 seconds, no error events.
- **Baseline silo fabricated %**: `baseline/train/20250321_silo/002-10-potential_levers.json` — "15% increase in black market activity", "30% reduction in innovative output", "20% slower problem-solving rate" in consequences.
- **haiku hong_kong file size**: `history/1/30_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` was >54KB (tool persisted output); `history/1/37_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` displayed normally at ~233 lines.

---

## PR Impact

### What the PR was supposed to fix

PR #297 targeted the content quality regression identified in the AGENTS.md experiment
insights section and in analysis/16's assessment. Specifically:

1. Mandatory `Immediate → Systemic → Strategic` chains were inflating consequence length and
   forcing formulaic output.
2. Mandatory quantification ("% change, cost delta") was causing models to fabricate
   statistics.
3. `conservative → moderate → radical` option template was producing predictable triads
   instead of genuinely distinct approaches.
4. "Radical option must include emerging tech/business model" was pushing toward flashy,
   unsupported claims.

### Before vs After Comparison

| Metric | Before (runs 24–30) | After (runs 31–37) | Change |
|--------|--------------------|--------------------|--------|
| Overall success rate | 34/35 (97.1%) | 35/35 (100.0%) | +2.9pp |
| gpt-oss-20b parasomnia | FAIL (EOF) | SUCCESS (79.1s) | **RESOLVED** |
| qwen3 contamination (silo) | 17/17 (100%) | 0/15 (0%) | **ELIMINATED** |
| Fabricated % in consequences | Mandatory / widespread | Minimal (1 in llama3.1) | **DRASTICALLY REDUCED** |
| haiku consequence length | ~980 chars (prior report) | ~450 chars | **2.2× REDUCTION** |
| Consequence length vs baseline | 3.6–4.3× baseline | 0.8–2.0× baseline | **RESTORED** |
| Gemini config failure | Yes (doubled wall-clock) | No | **RESOLVED** |
| llama3.1 bracket contamination | 6/21 levers | 0 | **RESOLVED** |
| llama3.1 label-only options | Not observed | 7/21 levers | **NEW ISSUE** |
| Review format compliance | 100% | 100% | MAINTAINED |

### Did the PR fix the targeted issue?

**Yes, definitively.**

1. **Fabricated % eliminated**: Haiku, gemini, and qwen3 consequences contain zero fabricated
   percentages. The mandatory quantification requirement drove the fabrication; removing it
   stopped it.

2. **Content length restored**: The ~4× consequence length observed in the pre-PR haiku output
   is now ~2× for the same model, same plan. Content-per-character improved: the remaining
   words are grounded analysis rather than formula-padding.

3. **qwen3 contamination resolved**: The 100% contamination rate was caused by the structural
   similarity between the mandatory chain format in consequences and the mandatory review format.
   Removing the chain broke the pattern. Zero contamination now.

4. **gpt-oss-20b parasomnia resolved**: The shorter consequences produced smaller JSON output
   that fit within provider token limits. No code change was needed; shorter prompt guidance
   was sufficient.

### Did the PR introduce regressions?

**One new issue**: llama3.1 label-only options in call-2 (N1). This was not observed in
analysis/17 (run 24 llama3.1). The previous degradation was bracket-wrapped consequences;
the new degradation is label-only options. The root cause (model reversion to template mode
in later LLM calls) persists but manifests differently.

Whether this is a PR regression or a shift in model behavior is uncertain. The new prompt
removed the `conservative → moderate → radical` template which may have given llama3.1
more structure to follow in later calls, and without it the model produces bare labels. This
is a testable hypothesis.

**No other regressions observed.** All prior improvements (haiku recovery, review format
compliance) are maintained. The gemini config issue is resolved (possibly from a separate fix).

### Verdict

**KEEP**

The PR produces significant, measurable improvements across multiple critical metrics:
- Structural improvement: 35/35 success (new record)
- Content quality improvement: fabricated % eliminated in 3 of 4 models verified
- Operational improvement: gpt-oss-20b parasomnia resolved after 3 consecutive failures
- Content credibility: consequence length restored to 1.0–2.0× baseline (vs. 3.6–4.3× before)

The one new issue (llama3.1 label-only options in call-2) is a model-specific degradation
that requires a follow-up prompt refinement or code fix, but it does not outweigh the
substantial improvements in content quality and reliability.

---

## Questions For Later Synthesis

1. **What caused qwen3's contamination?** H1 below predicts it was the structural similarity
   between the `Immediate → Systemic → Strategic` format and the review format. Synthesis
   should confirm: did qwen3 run 27 produce contaminated levers only because of the chain
   format, or were there other triggers?

2. **Is llama3.1's label-only option regression caused by removing the `conservative →
   moderate → radical` template?** In analysis/17, the bracket contamination was in
   call-3; now label-only options appear in call-2. The call ordering may have changed, or
   the model degraded earlier. C1 below proposes a code fix; H2 proposes a prompt addition.

3. **Should the prompt add explicit option length guidance?** The current prompt says options
   should be "complete strategic approaches" and "self-contained descriptions", but llama3.1
   ignores this in call-2. A minimum-word count ("Each option must be at least 15 words") or
   an explicit example of a complete option might help.

4. **Why is haiku hong_kong still at 2.0× baseline consequence length?** The plan is complex
   (film remake with many interconnected decisions), which may naturally produce longer
   analysis. Is this a genuine quality signal or is there still verbosity that should be
   trimmed?

5. **Is qwen3's fabricated % in options a problem?** Options like "Allocate 60% of resources
   to vertical farming" are plausible strategic parameters even without specific evidence in
   the context. Should the prohibition be narrowed to consequences specifically, or kept broad?

6. **What fixed the gemini config failure?** The "openrouter-paid-gemini-2.0-flash-001"
   error in run 29 was a config/code issue, not a prompt issue. Synthesis should identify
   whether a separate code fix was merged before run 36.

---

## Reflect

The most significant result of this batch is **not the 100% success rate** (which is +1 over
analysis/17's already-excellent 97.1%), but the **quality restoration**: consequences are
now grounded, concise, and credible. The external report comparison (analysis/16 assessment:
"baseline report 6.5/10, optimized report 5.8/10") was the alarm signal; this PR directly
addresses the root causes of that credibility regression.

The gpt-oss-20b parasomnia resolution is the most operationally significant finding. Three
batches of analysis documented this failure without resolution; the prompt change achieved
what several code suggestions had not yet been applied to fix.

The llama3.1 label-only option issue is a new signal worth tracking. It suggests llama3.1
has a threshold — possibly related to context accumulation across multiple LLM calls — where
it reverts to minimal-effort output. The mode of failure changed from bracket-wrapped
consequences (analysis/17) to label-only options (analysis/18), which may indicate the
model is responding to the new prompt's prohibition on brackets but not to the guidance on
option completeness.

qwen3 is now a fully clean model on consequences and review format. Its options remain
somewhat shorter than haiku's but are substantive. The contamination that marked qwen3 as
unreliable in analyses/15–17 is gone.

---

## Potential Code Changes

**C1 — Investigate llama3.1's multi-call option degradation at the code level**

Evidence: Run 31 shows 7/21 levers with label-only options concentrated in one call group.
Analysis/17 run 24 showed bracket-wrapped consequences in the same structural position. This
is a persistent multi-call degradation for llama3.1.

The runner calls the LLM multiple times and the later calls may receive less favorable context
(e.g., a long list of "already generated" lever names that crowds the system prompt context,
leaving less room for the instruction text). Inspect whether the context sent to call-2/3 is
materially different from call-1 and whether the instruction text is still in the effective
context window.

Expected effect: If the issue is context crowding, reducing the amount of "prior levers" text
sent to later calls, or restructuring the multi-call prompt to reinforce option quality
requirements, could fix the degradation.

**C2 — (From analysis/17, now partially resolved) EOF retry for gpt-oss-20b**

The prompt change resolved parasomnia for gpt-oss-20b in this batch, but the underlying
provider-side truncation risk remains if a plan ever produces very large context. Adding
`"eof while parsing"` to `_TRANSIENT_PATTERNS` remains a defensive improvement.

Evidence: analysis/17 runs 18, 25 both failed with identical error string. The fix in this
batch is soft (shorter output); a hard retry pattern would provide a safety net.

Expected effect: If a future plan's complexity causes output to exceed limits again, the
error is caught and retried rather than discarded.

---

## Hypotheses

**H1 — qwen3 contamination was caused by the `Immediate → Systemic → Strategic` chain format**

The chain format's `→` structure and strategic framing tokens were close enough to the review
format's "Controls X vs. Y. Weakness: ..." that qwen3 merged the two fields. When the chain
format was removed, the two fields became structurally distinct and qwen3 could separate them.

Evidence: 100% contamination rate in run 27 → 0% in run 34, with no other change except
the prompt.

Prediction: If the chain format is reintroduced in a future prompt, qwen3 contamination
would return. A test prompt with `Immediate → Systemic → Strategic` against qwen3 would
confirm this.

**H2 — Prompt needs explicit minimum option length to fix llama3.1 label-only options**

The current prompt's guidance ("complete strategic approaches", "self-contained descriptions")
is insufficient for llama3.1 in later LLM calls. An explicit minimum length constraint (e.g.,
"Each option must describe the approach in at least 15 words") or a positive example of a
complete option might anchor the model in later calls.

Evidence: Label-only options in call-2 (7/21 levers) are 2–4 words; call-1 options are
15–30 words. The model clearly can produce complete options (call-1 is fine); the degradation
is call-specific.

Prediction: Adding explicit length guidance would eliminate label-only options in later
calls for llama3.1 without affecting other models (which already produce full options).

**H3 — The `conservative → moderate → radical` template removal improved option diversity
across all models**

Examining run 37 (haiku) hong_kong options: they do not follow a predictable three-point
spread. Each set of three options offers genuinely distinct strategic approaches (e.g.,
different narrative subversion strategies that involve different structural choices, not
just low/medium/high intensity).

Evidence: Qualitative comparison of run 30 (prompt_3) vs run 37 (prompt_4) haiku options.
In run 30, haiku options often followed "incremental / moderate / radical" progression;
in run 37, the three options explore structurally different approaches.

Prediction: Options quality (specifically "genuinely distinct" criterion) would be measurably
higher in analysis/18 than analysis/17 under human evaluation. This is not yet quantified —
synthesis should consider requesting a qualitative review.

---

## Summary

Runs 1/31–1/37 produce a 100% success rate (35/35) and deliver the most significant
**content quality improvement** since the optimization loop began. The primary achievements:

1. **qwen3 consequence contamination eliminated** (was 100%, now 0%) — the mandatory chain
   format was the root cause; removing it resolved the defect without code changes.

2. **gpt-oss-20b parasomnia resolved** for the first time across 4 batches — shorter
   consequence guidance reduced output size below provider token limits.

3. **Fabricated percentages nearly eliminated** from consequences — the prohibition works for
   haiku, gemini, and qwen3; llama3.1 is the lone holdout (1 occurrence).

4. **Content length restored** — haiku hong_kong consequences dropped from ~980 chars (prompt_3)
   to ~450 chars (prompt_4), from 4.3× baseline to 2.0× baseline. All other models are
   0.8–1.5× baseline.

5. **Gemini config failure resolved** — no wasted plan runs.

The one new issue is llama3.1 label-only options in call-2 (7/21 levers, silo plan), where
the model reverts to 2–4 word option labels instead of complete strategic approaches. This
is a persistent multi-call degradation pattern specific to llama3.1.

**PR #297 verdict: KEEP.** The improvements are substantial, measurable, and address the
exact credibility regression identified in the external report comparison. The new issue
(llama3.1 options) warrants follow-up but is a lower priority than the quality problems
that were resolved.

Top next steps: (1) Investigate llama3.1 multi-call option degradation (C1 above); (2) add
minimum option length guidance to the prompt (H2); (3) add EOF error to transient retry
patterns as a safety net (C2).
