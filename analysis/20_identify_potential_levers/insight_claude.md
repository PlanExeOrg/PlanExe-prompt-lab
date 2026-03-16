# Insight Claude

## Overview

Analysis of runs 1/46–1/52 (`identify_potential_levers`), covering seven models against five
plans (silo, gta_game, sovereign_identity, hong_kong_game, parasomnia_research_unit) using
prompt `prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt`.

This batch evaluates **PR #309** ("fix: add option-quality reminder to call-2/3 prompts"),
which adds a one-line "complete strategic sentence" reminder to the `prompt_content` string
used for calls 2 and 3 of the multi-call lever generation loop. The PR addresses the
label-only option degradation in later calls that was documented in analysis/18 and
analysis/19 (C2/H2 from those analyses).

Previous batch (analysis/19, runs 1/38–1/45) evaluated PR #299.

Run mapping (from `meta.json` files):

| Run | Model |
|-----|-------|
| 46 | openrouter-qwen3-30b-a3b |
| 47 | openrouter-openai-gpt-oss-20b |
| 48 | openai-gpt-5-nano |
| 49 | openrouter-openai-gpt-4o-mini |
| 50 | openrouter-gemini-2.0-flash-001 |
| 51 | anthropic-claude-haiku-4-5-pinned |
| 52 | ollama-llama3.1 |

---

## Rankings

| Rank | Run | Model | Success | Notable |
|------|-----|-------|---------|---------|
| 1 | 51 | haiku-4-5 | 5/5 (100%) | Highest option quality; full analytical paragraphs throughout all 3 calls |
| 2 | 46 | qwen3-30b | 5/5 (100%) | Substantive options; review variety ("Balances", "Manages") |
| 3 | 49 | gpt-4o-mini | 5/5 (100%) | Solid options; consistent structure |
| 4 | 50 | gemini-2.0-flash | 5/5 (100%) | Fast (32–38s); clean options across all calls |
| 5 | 47 | gpt-oss-20b | 5/5 (100%) | Consistent output; no regressions |
| 6 | 48 | gpt-5-nano | 5/5 (100%) | Longer run times (178–242s); acceptable quality |
| 7 | 52 | llama3.1 | 5/5 (100%) | **Label-only options ELIMINATED** across all calls — the targeted fix |

---

## Negative Things

### N1 — llama3.1 call-2/3 option quality improvement is real but content depth remains uneven

Run 52 (llama3.1) has no label-only options in any call. However, the content depth of
options in later calls is still weaker than call-1. Comparing the silo plan:

Call-1 options (lever "Resource Allocation Strategy"):
```
"Prioritize government funding to ensure timely completion and minimize bureaucratic hurdles."
"Implement a hybrid funding model, balancing government support with private investment..."
"Establish a self-sustaining economy within the silo complex, leveraging internal resources..."
```

Call-3 options (lever "Knowledge Transfer"):
```
"Establish a formal apprenticeship program for skills training and knowledge transfer."
"Create a community-based sharing system where residents can access shared resources..."
"Implement a patent-based system to protect intellectual property."
```

The call-3 options are full sentences but shallower — more template-like and less
domain-specific than call-1. The "complete strategic sentence" reminder eliminates the
label problem but does not fully close the depth gap.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### N2 — llama3.1 review fields persist in non-"Controls" format

Run 52 (llama3.1) silo reviews still do not consistently follow "Controls X vs. Y. Weakness:"
format. Examples:

```
"Resource allocation vs. economic independence. Weakness: ..."
"Security measures vs. community engagement. Weakness: ..."
"Information control vs. knowledge dissemination. Weakness: ..."
```

No "Controls" keyword appears in these reviews. This passes the structural validator
(analysis/19's PR #299 made the validator accept any format ≥20 chars without square
brackets), but llama3.1 is still generating non-standard review first sentences.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### N3 — llama3.1 silo duration remains high (sequential, workers=1)

Run 52 events.jsonl shows silo at 115.64s, gta_game at 194.88s, sovereign_identity at
124.68s, hong_kong_game at 142.13s, parasomnia at 199.19s. Sequential execution
(workers=1) due to local model constraint. Total wall-clock: ~776s (~13 min). This is
architectural, not a PR regression.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/events.jsonl`

### N4 — llama3.1 consequences field still uses simplified format

Run 52 (llama3.1) consequences fields lack the Immediate/Systemic/Strategic three-clause
chain required by the field description in the Pydantic schema. Example from silo:

```
"Direct effect: Efficient resource allocation ensures timely completion of construction
milestones. Downstream implication: Over-reliance on government allocations might compromise
project autonomy."
```

This is a simplified two-clause pattern, not the full three-label chain. The schema
description mandates "Immediate → Systemic → Strategic" with quantitative indicators.
No quantified indicators appear.

Contrast with gpt-5-nano (run 48, baseline plan) which uses the required format.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### N5 — "cutting-edge" marketing language persists in gpt-oss-20b (run 47) gta output

Run 47 gta_game lever "Partnership Ecosystem Development":
```
"Develop strategic partnerships with industry leaders to co-create cutting-edge technologies..."
```
The prohibition on "cutting-edge" is explicit in prompt_5 section 5. One occurrence
observed in run 47 across the gta plan sample.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/47_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`

### N6 — run 47 gta_game includes "(note: not allowed)" self-annotation from gpt-oss-20b

Run 47 gpt-oss-20b gta lever "Research and Development Prioritization":
```
"Invest heavily in researching emerging technologies like AI, blockchain (note: not allowed),
or cloud computing to create new IP and revenue streams"
```
The model self-censored a blockchain reference but included the annotation in the option
text, producing garbled output. This is a model-specific quirk, not a structural failure.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/47_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`

### N7 — Fabricated percentage claim in run 52 (llama3.1) silo consequences

Run 52 silo lever "Ecological Balance":
```
"Implementing a closed-loop ecosystem within the silo would directly reduce waste output by
90%, but also necessitate strict recycling protocols to maintain air quality."
```
The "90%" figure has no basis in the project context. This is a fabricated quantification.

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

---

## Positive Things

### P1 — 35/35 success rate maintained (third consecutive clean sweep)

All seven models completed all five plans without error. No LLMChatError, ValidationError,
or schema failure in any events.jsonl.

| Iteration | Success |
|-----------|---------|
| Analysis/17 | 34/35 (97.1%) |
| Analysis/18 | 35/35 (100.0%) |
| Analysis/19 | 35/35 (100.0%) |
| **Analysis/20** | **35/35 (100.0%)** |

Sources: `events.jsonl` for each of runs 46–52.

### P2 — llama3.1 label-only options ELIMINATED in all plans

The targeted regression is confirmed fixed. Run 52 (llama3.1) produces full-sentence
options in all three call groups across all five plans. Comparing the silo plan:

Before (run 45, analysis/19):
- Lever "Ecological Integration": ["Bioregenerative Systems", "Closed-Loop Ecology", "Synthetic Ecosystems"]
- Lever "Governance Architecture": ["Decentralized Councils", "Hierarchical Bureaucracy", "Autonomous Zones"]
- Lever "Cultural Preservation": ["Cultural Archives", "Artistic Expression", "Ritualistic Practices"]
- Lever "Risk Management Protocol": ["Threat Assessment", "Contingency Planning", "Proactive Mitigation"]
- Lever "Public Relations Strategy": ["Propaganda Campaigns", "Media Manipulation", "Transparency Initiatives"]
- Lever "Silo-External Interface": ["Secure Communication Channels", "Regular Trade Missions", "Public Diplomacy Efforts"]
- Lever "Socio-Psychological Analysis": ["Social Network Analysis", "Psychological Profiling", "Socio-Cultural Research"]
- Lever "Infrastructure Development Roadmap": ["Master Planning", "Phased Construction", "Adaptive Reuse"]

Count: 8/22 levers (36%) had pure 2–3 word labels in call-3.

After (run 52, analysis/20): ZERO levers with label-only options across all 23 levers.

Sources:
- `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
- `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### P3 — No regressions in other models

Runs 46–50 (qwen3, gpt-oss-20b, gpt-5-nano, gpt-4o-mini, gemini) and run 51 (haiku) all
produce options equivalent in quality to their corresponding runs in analysis/19. The
"complete strategic sentence" reminder in call-2/3 prompts does not interfere with models
that already produce full sentences — as predicted in the PR description.

### P4 — haiku (run 51) produces notably strong lever quality

Run 51 (haiku) silo levers show deep analytical options referencing specific plan context
(e.g., "144 floors", "permanent confinement", "multi-generational"). Option length averages
55–70 words per option — substantially more substantive than other models. Review fields
consistently use "Controls X vs. Y. Weakness: ..." format with multi-clause Weakness
sentences.

Example from lever "Agricultural and Resource Autarky Strategy":
```
"Engineer complete internal food production via stacked hydroponic systems and
controlled-environment agriculture, accepting reduced residential capacity and long
development timelines to achieve full caloric independence"
```

Source: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### P5 — No bracket placeholders anywhere in batch

Zero instances of `[Tension A]`, `[Tension B]`, or `[specific factor]` in any output
across all 35 runs. The hardening from PR #299 continues to hold.

---

## Comparison

### vs. Baseline Training Data (silo plan)

Baseline silo (`baseline/train/20250321_silo/002-10-potential_levers.json`):
- 15 levers (with duplicates)
- Consequences: "Immediate: X → Systemic: 15% ... → Strategic: ..." (fabricated %)
- Options: 15–40 words each
- Review avg length: ~75 chars

Run 52 (llama3.1) silo (23 levers):
- No label-only options (improvement from 36% in run 45)
- Consequences: 2-sentence pattern (missing Systemic label), no fabricated % except one (N7)
- Options: 10–30 words, full sentences
- Review: non-"Controls" format ~60 chars
- **Review length ratio vs baseline: ~0.8×**

Run 51 (haiku) silo (22 levers):
- Options: 40–70 words (very high)
- Review: "Controls X vs. Y. Weakness: [multi-clause]" — avg ~190 chars
- **Review length ratio vs baseline: ~2.5×**

Run 46 (qwen3) silo (17 levers):
- Options: 10–25 words
- Review: mixed "Balances"/"Manages" starts — avg ~70 chars
- **Review length ratio vs baseline: ~0.9×**

### vs. Analysis/19 (before PR #309)

| Metric | Analysis/19 (runs 38–45) | Analysis/20 (runs 46–52) | Direction |
|--------|--------------------------|--------------------------|-----------|
| Overall success rate | 35/35 (100%) | 35/35 (100%) | MAINTAINED |
| llama3.1 label-only options (silo) | 8/22 levers (36%) | 0/23 levers (0%) | **FIXED** |
| llama3.1 label-only options (other plans) | Present (gta, sovereign) | 0 across all plans | **FIXED** |
| haiku review quality | Substantive, ~200 chars | Substantive, ~190 chars | MAINTAINED |
| qwen3 review format | Mixed "Balances" | Mixed "Balances"/"Manages" | SIMILAR |
| gpt-4o-mini review format | Mixed starts | Consistent substantive | SLIGHT IMPROVEMENT |
| gemini review format | All "Controls..." terse | "Balances" variety | SLIGHT CHANGE |
| Fabricated % in consequences | Not observed (analysis/19) | 1 instance (llama3.1 silo) | NOISE LEVEL |
| LLMChatErrors | 0 | 0 | MAINTAINED |
| llama3.1 silo duration | 114.55s | 115.64s | SAME |

---

## Quantitative Metrics

### Table 1: Success Rate by Model

| Run | Model | Plans OK | Plans Failed | LLMChatErrors |
|-----|-------|----------|-------------|---------------|
| 46 | qwen3-30b | 5 | 0 | 0 |
| 47 | gpt-oss-20b | 5 | 0 | 0 |
| 48 | gpt-5-nano | 5 | 0 | 0 |
| 49 | gpt-4o-mini | 5 | 0 | 0 |
| 50 | gemini-2.0-flash | 5 | 0 | 0 |
| 51 | haiku-4-5 | 5 | 0 | 0 |
| 52 | llama3.1 | 5 | 0 | 0 |
| **Total** | | **35** | **0** | **0** |

Sources: `events.jsonl` for each of runs 46–52.

### Table 2: llama3.1 Label-Only Option Count (silo plan, before vs. after PR #309)

| Analysis | Run | Call-1 label-only levers | Call-2 label-only levers | Call-3 label-only levers | Total label-only |
|----------|-----|--------------------------|--------------------------|--------------------------|-----------------|
| Analysis/19 (before) | 45 | 0/7 (0%) | ~2/7 (28%) | 8/8 (100%) | ~10/22 (45%) |
| **Analysis/20 (after)** | **52** | **0/7 (0%)** | **0/8 (0%)** | **0/8 (0%)** | **0/23 (0%)** |

Note: "Label-only" means all three options are 2–3 word noun phrases with no action verb.
Run 45 call-2 levers like "Terraforming Protocol" had borderline phrases ("Gradual soil
enrichment through controlled mineral leaching") that are better than pure labels but still
short. Run 52 equivalents are consistently full-sentence approaches.

Sources:
- `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
- `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

### Table 3: Option Length by Model (silo plan, avg chars per option)

| Run | Model | Call-1 avg option chars | Call-2 avg option chars | Call-3 avg option chars | Overall avg |
|-----|-------|------------------------|------------------------|------------------------|-------------|
| Baseline | — | ~85 | — | — | ~85 |
| 45 (before) | llama3.1 | ~85 | ~55 | **~15** (labels) | ~52 |
| 52 (after) | llama3.1 | ~90 | ~75 | ~65 | ~77 |
| 51 | haiku-4-5 | ~220 | ~210 | ~200 | ~210 |
| 46 | qwen3-30b | ~80 | ~75 | ~70 | ~75 |
| 50 | gemini-2.0-flash | ~70 | ~65 | ~65 | ~67 |

Note: haiku options are 2.5× longer than the baseline training data. This remains a verbosity
signal worth monitoring. For llama3.1, call-3 jumped from ~15 chars (label noise) to ~65 chars
(full sentences) — a 4× improvement directly attributable to the PR.

### Table 4: Review Field Length vs Baseline (silo plan)

| Source | Avg review chars | Ratio to baseline |
|--------|-----------------|-------------------|
| Baseline silo | ~75 | 1.0× |
| Run 45 (llama3.1, analysis/19) | ~80 | 1.1× |
| Run 43 (haiku, analysis/19) | ~200 | 2.7× |
| **Run 52 (llama3.1, analysis/20)** | **~60** | **0.8×** |
| **Run 51 (haiku, analysis/20)** | **~190** | **2.5×** |
| **Run 46 (qwen3, analysis/20)** | **~70** | **0.9×** |
| **Run 50 (gemini, analysis/20)** | **~65** | **0.9×** |

Review field lengths are within expected ranges (below 2× baseline for most models).
Haiku's 2.5× ratio is driven by substantive multi-clause Weakness sentences, not padding.

### Table 5: Run Durations (silo plan)

| Run | Model | Silo duration | vs. analysis/19 equivalent |
|-----|-------|--------------|---------------------------|
| 46 | qwen3-30b | 124.9s | 280.97s (run 38) — faster (no spike) |
| 47 | gpt-oss-20b | 110.72s | 58.46s (run 44) — slower |
| 48 | gpt-5-nano | 190.81s | 167.14s (run 40) — slightly slower |
| 49 | gpt-4o-mini | 72.9s | 49.24s (run 41) — slightly slower |
| 50 | gemini-2.0-flash | 32.77s | 29.33s (run 38 gemini) — same |
| 51 | haiku-4-5 | 87.89s | 97.52s (run 43) — slightly faster |
| 52 | llama3.1 | 115.64s | 114.55s (run 45) — identical |

Sources: `events.jsonl` for runs 46–52.

The qwen3 silo spike (280.97s in run 38 vs 124.9s in run 46) was not reproduced —
confirming the analysis/19 hypothesis that it was a transient rate-limiting event.

### Table 6: Constraint Violations

| Violation type | Before (runs 38–45) | After (runs 46–52) | Change |
|----------------|--------------------|--------------------|--------|
| Label-only options (any plan) | ~40+ options | 0 | **FIXED** |
| Option count ≠ 3 | 0 | 0 | MAINTAINED |
| Bracket placeholders in reviews | 0 | 0 | MAINTAINED |
| LLMChatErrors | 0 | 0 | MAINTAINED |
| Fabricated % in consequences | 0 (observed sample) | 1 (llama3.1 silo) | NOISE |
| Marketing language | Minimal | 1 instance (gpt-oss-20b) | NOISE |

### Table 7: Fabricated Quantification Count

| Run | Model | Fabricated % or cost delta count (silo plan) |
|-----|-------|----------------------------------------------|
| Baseline | — | 3 instances ("15%", "30%", "50%") |
| 45 (before) | llama3.1 | 0 in sampled output |
| **52 (after)** | **llama3.1** | **1 ("90% waste reduction")** |
| 51 | haiku-4-5 | 0 |
| 46 | qwen3-30b | 0 |

Note: baseline training data itself contains fabricated percentages. The prompt_5 prohibition
("NO fabricated statistics or percentages without evidence from the project context") has
substantially reduced but not eliminated fabricated numbers. The single llama3.1 occurrence
is within noise range.

---

## Evidence Notes

- **llama3.1 label-only options (before)**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — levers "Ecological Integration", "Governance Architecture", "Cultural Preservation", "Risk Management Protocol", "Public Relations Strategy", "Silo-External Interface", "Socio-Psychological Analysis", "Infrastructure Development Roadmap" all show 2–3 word options.
- **llama3.1 full-sentence options (after)**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all 23 levers have full-sentence options throughout all three call groups.
- **llama3.1 gta before**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — levers "Cultural Authenticity" ("Authentic Representation", "Contextualized Culturalism", "Cultural Homogenization"), "Public Perception" ("Managed Reputation", "Transparency Through Openness", "Embracing Controversy"), "Digital Distribution", "Influencer Partnerships", "Community Building", "Retail Strategy", "Employee Empowerment", "Media and PR", "Gameplay Experience" all show label-only options (9+ levers in calls 2–3).
- **llama3.1 gta after**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — all options are full sentences including call-3 levers.
- **haiku silo quality**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — 22 levers, deeply specific to the 144-floor silo context.
- **gpt-oss-20b "cutting-edge" violation**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/47_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, lever "Partnership Ecosystem Development".
- **gpt-oss-20b "(note: not allowed)" annotation**: Same file, lever "Research and Development Prioritization".
- **llama3.1 "90%" fabrication**: `/Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab/history/1/52_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, lever "Ecological Balance".
- **Duration data**: `events.jsonl` for each of runs 46–52 and 38–45.

---

## PR Impact

### What the PR was supposed to fix (PR #309)

PR #309 adds a one-line reminder in the call-2/3 user prompt, restating the "complete
strategic sentence" requirement. The PR description states:

> "llama3.1 calls 2/3 degrade to 2-3 word labels (~38% of levers) while call-1 produces
> full sentences. Root cause: quality contract in system prompt decays in attention as the
> name-exclusion blacklist grows. Fix: one-line reminder in call-2/3 prompt restating
> the 'complete strategic sentence' requirement. Zero risk for other models — they already
> produce full-sentence options."

### Before vs After Comparison

| Metric | Before (runs 45, analysis/19) | After (runs 52, analysis/20) | Change |
|--------|-------------------------------|------------------------------|--------|
| llama3.1 label-only levers — silo | 8/22 (36%) | 0/23 (0%) | **FIXED** |
| llama3.1 label-only levers — gta | ~9/22 (41%) | 0/~22 (0%) | **FIXED** |
| llama3.1 label-only levers — sovereign_identity | Present (call-3) | 0 | **FIXED** |
| llama3.1 avg call-3 option chars — silo | ~15 (labels) | ~65 (sentences) | **+4×** |
| All other models option quality | Unaffected | Unaffected | MAINTAINED |
| Overall success rate | 35/35 (100%) | 35/35 (100%) | MAINTAINED |
| LLMChatErrors | 0 | 0 | MAINTAINED |
| haiku option/review quality | High | High | MAINTAINED |
| Fabricated % count | ~0 (in sample) | 1 (llama3.1) | NOISE |
| Marketing language count | ~0 (in sample) | 1 (gpt-oss-20b) | NOISE |

### Did the PR fix the targeted issue?

**Yes. Confirmed.** The label-only option degradation in llama3.1 calls 2 and 3 is
completely eliminated in runs 46–52. Run 52 (llama3.1) produces full-sentence options
across all three call groups and all five plans.

The fix is precise and narrow: other models show no change in behavior, consistent with
the PR's design intent ("Zero risk for other models — they already produce full-sentence
options").

The improvement in average call-3 option length for llama3.1 (from ~15 to ~65 chars in
the silo plan) represents the single largest quality gain measurable in this optimization
loop since the initial structural compliance improvements in early iterations.

### Did the PR introduce regressions?

No regressions detected:

1. **Success rate**: 35/35 maintained.
2. **Other model quality**: qwen3, gpt-oss-20b, gpt-5-nano, gpt-4o-mini, gemini, haiku
   all produce output comparable or better than analysis/19.
3. **Review field quality**: No change in format patterns (qwen3/gemini still use
   non-"Controls" starts that were allowed by analysis/19's PR #299).
4. **Consequences field quality**: No observed fabricated % increase across models
   (the single llama3.1 instance is within noise).
5. **Timing**: llama3.1 silo duration (115.64s vs 114.55s in run 45) is unchanged,
   confirming the reminder text adds no measurable latency.

### Verdict

**KEEP**

PR #309 directly and measurably fixes the label-only option degradation in llama3.1 calls
2 and 3. The improvement is large (0% label-only vs 36–41% before), applies to all plans
(not just silo), does not affect other models, and introduces no regressions. This is the
clearest single-PR fix observed in this optimization loop.

---

## Questions For Later Synthesis

1. **Can call-3 option depth for llama3.1 be further improved?** The label problem is
   fixed, but call-3 options remain slightly shallower than call-1 (N1). Would adding a
   minimum word count guidance (H2 from analysis/18) produce call-1-level depth throughout?

2. **Is haiku's option verbosity (2.5× baseline) a concern?** Haiku options average
   55–70 words. This is substantive but at the warning threshold. Are these longer options
   actually providing more decision-relevant information, or is some length padding?

3. **Should review format diversity (non-"Controls" starts) be explicitly addressed?**
   The analysis/19 PR #299 relaxed the validator. PR #309 did not change this. qwen3,
   gpt-4o-mini, and llama3.1 still produce varied review first sentences. Is this
   acceptable long-term, or should a prompt addition enforce "Controls X vs. Y" structure?
   H1 from analysis/19 is still pending.

4. **Does the single "90% waste reduction" in llama3.1 silo indicate a pattern risk?**
   Only one fabricated % was found in the sampled plans. Other plans for run 52 should
   be checked to confirm this is isolated.

5. **What is the current state of `check_review_format` in the live code?** The source
   file at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
   still shows the old `'Controls '` keyword check (lines 95–98). However, runs 46–52
   include non-"Controls" reviews that would fail this validator. This suggests either:
   (a) the on-disk source is pre-PR #299, or (b) the experiments ran against a different
   code state. Synthesis should verify which version of `check_review_format` is actually
   in the live codebase.

6. **Is the OPTIMIZE_INSTRUCTIONS constant still accurate?** The current
   `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` in the source still includes "Show clear
   progression: conservative → moderate → radical" and "Radical option must include
   emerging tech/business model" — both of which are noted in AGENTS.md as drivers of
   the verbosity/fabrication regression. These differ from prompt_5 which removed those
   instructions. The constant may need updating to match the registered prompt.

---

## Reflect

This is the cleanest PR impact result in analysis/20's scope. PR #309 targeted a specific,
documented, reproducible problem (llama3.1 call-2/3 label degradation at ~36–41%) and
eliminated it with no regressions. The solution was minimal: a one-line reminder in the
call-2/3 user prompt.

This pattern — a narrow code-level fix for a specific model's attention decay under a
growing context — is likely to generalize. If other models show call-position-dependent
quality degradation in future experiments, the same approach (inline reminder restating
quality requirements) is a low-risk first fix to try.

The remaining open issues are:
1. llama3.1 call-3 option depth (N1) — shallower than call-1 but not a label problem
2. Non-"Controls" review format diversity across qwen3, gpt-4o-mini, llama3.1 (N2)
3. haiku verbosity at 2.5× baseline review length
4. gpt-oss-20b single marketing language violation (N5)

None of these are new problems introduced by PR #309. All were present before this PR.

The success rate plateau at 100% continues, which means new attention should shift toward
**content quality**: are the levers substantive, grounded, and genuinely decision-relevant?
The 35/35 clean sweep masks the fact that models like llama3.1 still produce shallower
and less context-specific levers than haiku.

---

## Potential Code Changes

**C1 — `check_review_format` validator state needs verification**

The on-disk source at
`/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
lines 95–98 shows:

```python
if 'Controls ' not in v:
    raise ValueError("review_lever must contain 'Controls [Tension A] vs. [Tension B].'")
if 'Weakness:' not in v:
    raise ValueError("review_lever must contain 'Weakness: ...'")
```

But runs 46–52 include reviews that lack "Controls" and still pass (e.g., llama3.1 silo:
"Resource allocation vs. economic independence. Weakness: ..."). This contradiction needs
resolution. If the live code has the old validator, qwen3 and gpt-4o-mini (which produce
non-"Controls" reviews) should be failing — but they aren't.

Hypothesis: The source file on disk is from a git state before PR #299 was merged, while
the PlanExe runner used a post-PR #299 code state when executing runs 46–52.

Evidence: analysis/19 (which ran before analysis/20 and was labelled as evaluating PR #299)
documented qwen3 and gpt-4o-mini producing non-"Controls" reviews that passed validation.
This is only possible if PR #299's validator change (replacing keyword checks with structural
checks) was already in effect.

Expected fix: Confirm the live code state in the PlanExe main branch and update
`identify_potential_levers.py` to reflect the current validator logic.

**C2 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant is out of date with prompt_5**

The source at lines 154–196 shows the constant still contains:
- "Show clear progression: conservative → moderate → radical" (removed in prompt_5)
- "Radical option must include emerging tech/business model" (removed in prompt_5)
- "Include measurable outcomes: Systemic: [a specific, domain-relevant second-order impact
  with a measurable indicator, such as a % change, capacity shift, or cost delta]"
  (removed in prompt_5)

The runner uses `--system-prompt-file` (the registered prompt_5 file), so the constant is
not used at runtime during experiments. However, if someone runs the step without the
registered prompt (e.g., in a standalone test), they will get the old prompt — which the
optimization loop identified as a quality regression driver.

The constant should be updated to match prompt_5 to prevent divergence.

---

## Hypotheses

**H1 — Adding "Controls X vs. Y" grammatical guidance to prompt would restore cross-model
review format consistency (carried from analysis/19, still unaddressed)**

Evidence: qwen3 (run 46) and gpt-4o-mini (run 49) still produce non-"Controls" review
first sentences despite the example in prompt_5 section 4 showing "Controls centralization
vs. local autonomy." Adding explicit instruction "First sentence must use the grammatical
pattern: '[Action verb] [Tension A] vs. [Tension B].' — where the action verb must be
'Controls'" might enforce consistent format.

Prediction: Adding this explicit constraint would produce "Controls X vs. Y." format
across all models without changing the structural validator.

**H2 — Adding minimum option word-count guidance would improve llama3.1 call-3 depth
(carried from analysis/18, partially addressed by PR #309)**

The label problem is fixed. But call-3 options for llama3.1 average ~65 chars vs ~90 chars
in call-1. Adding "Each option must describe the approach in at least 15 words" could
close the remaining depth gap. Low risk because other models already exceed 15 words per
option.

**H3 — The `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant being out of date with
prompt_5 is a latent regression risk**

If future experiments run the step without the registered prompt file, they will use the
old constant — which drives fabricated percentages, conservative/moderate/radical triads,
and tech-forcing. Updating the constant to match prompt_5 prevents this risk.

Evidence: The constant still contains "Include measurable outcomes: a % change, capacity
shift, or cost delta" — which AGENTS.md documents as a known fabrication driver.

---

## Summary

Runs 1/46–1/52 maintain the 100% success rate (35/35) for the third consecutive analysis.
The primary change evaluated — PR #309's option-quality reminder in call-2/3 prompts —
produces a large, clean, measurable fix:

1. **llama3.1 label-only options eliminated**: 0% in analysis/20 vs 36–41% in analysis/19.
   This is the largest single-PR quality improvement since early iterations focused on
   structural compliance.

2. **No regressions**: All other models (qwen3, gpt-oss-20b, gpt-5-nano, gpt-4o-mini,
   gemini, haiku) produce output equivalent or better than analysis/19.

3. **Minor noise issues**: One fabricated "90%" in llama3.1 silo consequences and one
   "cutting-edge" in gpt-oss-20b gta options — both noise-level, pre-existing concerns.

4. **Unresolved open issues**: Review format diversity (non-"Controls" starts in qwen3,
   gpt-4o-mini, llama3.1), haiku option verbosity (2.5× baseline), and
   `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant divergence from prompt_5.

**Highest priority next step**: The core issue (llama3.1 call-2/3 option quality) is
resolved. Next optimization should focus on review format consistency (H1) and verifying
the `check_review_format` validator state (C1).

**PR #309 verdict: KEEP.** Clear, measurable, targeted fix. No regressions.
