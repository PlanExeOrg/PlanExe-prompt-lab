# Insight Claude

## Overview

Analysis of runs 1/38–1/45 (`identify_potential_levers`, run 39 absent), covering seven
models against five plans (silo, gta_game, sovereign_identity, hong_kong_game,
parasomnia_research_unit) using prompt
`prompt_5_9c5b2a0d4c74f350c66b0a83a0ab946f5b36a75e3058733eae1bd9dee7eb813b.txt`.

This batch evaluates **PR #299** ("fix: remove bracket placeholders and fragile
English-only validator"), which made three code and prompt changes:

1. Replaced `[Tension A]`/`[Tension B]`/`[specific factor]` bracket placeholders in
   `review_lever` field descriptions and the `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`
   constant with concrete literal examples.
2. Replaced `check_review_format` English keyword checks (`'Controls '`, `'Weakness:'`)
   with structural validation: min length 20 chars, reject square brackets.
3. Aligned `summary` field description with prompt_4 format (one sentence prescribing a
   concrete addition).

Previous batch (analysis/18, runs 1/31–1/37) used prompt_4.

Run mapping (from `meta.json` files):

| Run | Model |
|-----|-------|
| 38 | openrouter-qwen3-30b-a3b |
| 40 | openai-gpt-5-nano |
| 41 | openrouter-openai-gpt-4o-mini |
| 42 | openrouter-gemini-2.0-flash-001 |
| 43 | anthropic-claude-haiku-4-5-pinned |
| 44 | openrouter-openai-gpt-oss-20b |
| 45 | ollama-llama3.1 |

---

## Rankings

| Rank | Run | Model | Success | Notable |
|------|-----|-------|---------|---------|
| 1 | 43 | haiku-4-5 | 5/5 (100%) | Highest review quality; deeply substantive Weakness sentences |
| 2 | 42 | gemini-2.0-flash | 5/5 (100%) | Fast (29–34s); all reviews start "Controls"; Weakness terse but correct |
| 3 | 44 | gpt-oss-20b | 5/5 (100%) | Consistent; no label-only options |
| 4 | 41 | gpt-4o-mini | 5/5 (100%) | Multiple non-"Controls" reviews pass new validator; options substantive |
| 5 | 38 | qwen3-30b | 5/5 (100%) | 10/15 silo reviews start "Balances" not "Controls"; pass new validator |
| 6 | 40 | gpt-5-nano | 5/5 (100%) | Longer run times (167–203s); acceptable quality |
| 7 | 45 | llama3.1 | 5/5 (100%) | Label-only options persist in later calls (same pattern as analysis/18) |

---

## Negative Things

### N1 — llama3.1 label-only options persist in run 45

Run 45 (llama3.1) silo output still produces label-only options in later call groups. Examples from `history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

```
lever "Ecological Integration":
  options: ["Bioregenerative Systems", "Closed-Loop Ecology", "Synthetic Ecosystems"]

lever "Governance Architecture":
  options: ["Decentralized Councils", "Hierarchical Bureaucracy", "Autonomous Zones"]

lever "Cultural Preservation":
  options: ["Cultural Archives", "Artistic Expression", "Ritualistic Practices"]

lever "Risk Management Protocol":
  options: ["Threat Assessment", "Contingency Planning", "Proactive Mitigation"]
```

These are 2–3 word labels. Call-1 options for the same run are substantive (10–30 words). PR #299 made no changes to multi-call context handling, so this pre-existing degradation (tracked since analysis/18) is unchanged.

### N2 — qwen3 and gpt-4o-mini produce non-"Controls" review first sentences

The new structural validator accepts reviews that do not start with "Controls". Run 38 (qwen3) silo has 10 of 15 reviews beginning with "Balances" or other verbs instead of "Controls":

```
"Balances immediate needs vs systemic resilience. Weakness: ..."
"Balances reliability vs innovation. Weakness: ..."
"Balances ecological interdependence vs. system fragility. Weakness: ..."
```

Run 41 (gpt-4o-mini) silo has 8 of 17 reviews not starting with "Controls":

```
"Balances ecological responsibility with immediate resource needs. Weakness: ..."
"Encourages openness vs. maintaining control over information. Weakness: ..."
"Focuses on preparedness vs. resource allocation for daily operations. Weakness: ..."
"Enhances community spirit vs. prioritizing basic needs. Weakness: ..."
"Manages information flow vs. resident transparency. Weakness: ..."
"Supports cultural diversity vs. potential exclusion. Weakness: ..."
"Encourages innovation vs. dependency on external solutions. Weakness: ..."
"Focuses on holistic well-being vs. individual needs. Weakness: ..."
```

These pass validation but deviate from the intended format. The old validator enforced "Controls" precisely. The new validator's permissiveness is the direct cause.

Source: `history/1/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
`history/1/41_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

### N3 — review quality for lower-tier models remains terse

Run 42 (gemini) silo reviews use very short Weakness sentences, e.g.:

```
"Controls transparency vs. security. Weakness: The options don't address the potential for black markets of information."
```

This is structurally correct and passes validation, but the Weakness sentence adds minimal insight. Haiku (run 43) produces multi-clause Weakness sentences identifying root-cause failures; gemini's one-liners are comparatively superficial.

### N4 — run 45 (llama3.1) silo duration is 684s sequential

Run 45 events.jsonl shows silo at 114.55s, gta at 120.23s, sovereign at 116.63s, hong_kong at 197.5s, parasomnia at 135.41s. These are sequential (workers=1). Total wall-clock for silo alone exceeds the parallel model times by 3-4×. This is a known architectural limitation (llama3.1 requires workers=1), not a PR regression.

Source: `history/1/45_identify_potential_levers/events.jsonl`.

---

## Positive Things

### P1 — 35/35 success rate maintained (second consecutive clean sweep)

All seven models completed all five plans without error. No LLMChatError, ValidationError, or schema failure in any events.jsonl.

| Iteration | Success |
|-----------|---------|
| Analysis/17 | 34/35 (97.1%) |
| Analysis/18 | 35/35 (100.0%) |
| **Analysis/19** | **35/35 (100.0%)** |

Sources: `events.jsonl` for each of runs 38, 40–45.

### P2 — Bracket placeholders eliminated from review fields

No instance of `[Tension A]`, `[Tension B]`, or `[specific factor]` appears in any review
field across all 35 runs. The PR's replacement of these placeholders in the field description
text and system prompt was effective.

In contrast, run 19 (an earlier batch using prompt_3) contained 6 verbatim placeholder levers
in gta_game output. The reduction from 6+ occurrences to 0 is confirmed.

Source: Grep across `history/1/38_identify_potential_levers/`, `history/1/40_identify_potential_levers/`,
through `history/1/45_identify_potential_levers/` — zero matches for `[Tension` or `[specific factor]`.

### P3 — haiku review quality significantly improved

Run 43 (haiku) produces the highest-quality review fields observed in this optimization loop.
All 25 silo levers have substantive, context-specific Weakness sentences. Example from
`history/1/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
lever "Population Expansion vs. Finite Resources":

```
"Controls demographic growth versus resource stability. Weakness: The options ignore the
political economy of selection — none meaningfully address how external stakeholders or
internal factions contest admission decisions."
```

This is a genuinely analytical observation, not a template restatement. The Weakness sentence
raises a new consideration not present in the options themselves.

Comparison with run 37 (haiku, analysis/18) silo: review fields were already substantive then
(same "Controls X vs. Y. Weakness: ..." pattern). The improvement in run 43 is in depth: the
2026-03-16 output shows longer, more analytically precise Weakness sentences.

### P4 — Structural validator allows non-English first-sentence patterns

The new validator passes `review` fields that do not use English keyword "Controls". This
directly addresses the AGENTS.md concern about internationalization: a non-English LLM response
using equivalent non-English phrasing for the tension would previously have failed validation.

Run 38 (qwen3) and run 41 (gpt-4o-mini) demonstrate this: reviews like "Balances X vs. Y.
Weakness: ..." pass the new 20-char minimum and no-square-brackets check. Under the old
validator, these would have triggered `ValueError: review_lever must contain 'Controls [Tension A] vs. [Tension B].'`
and caused a retry or failure.

### P5 — No new failure modes introduced by PR #299

Compared to analysis/18, there are no new error patterns, no timeout increases attributable
to the new prompt, and no model that was working in analysis/18 now failing in analysis/19.
The changes are narrowly scoped: review field descriptions, validator logic, and summary format.

---

## Comparison

### vs. Baseline Training Data

Baseline silo (`baseline/train/20250321_silo/002-10-potential_levers.json`):
- 15 levers (with duplicates: "Resource Allocation Strategy" ×3, "Technological Adaptation
  Strategy" ×3, "External Relations Protocol" ×2)
- Consequences: `Immediate: X → Systemic: 15% ... → Strategic: ...` (fabricated %)
- Options: 15–40 words each
- Review: `"Controls Efficiency vs. Equity. Weakness: ..."` — short, terse, consistent format
- Review avg length: ~75 chars

Run 43 (haiku) silo (25 levers after deduplication):
- No repeated names
- Consequences: 2–3 grounded sentences, zero fabricated %, specific to the 144-floor setting
- Options: 25–50 words each, distinct strategic pathways
- Review: `"Controls X vs. Y. Weakness: [multi-clause specific observation]"` — avg ~200 chars
- **Review length ratio vs baseline: ~2.7×**

Run 38 (qwen3) silo (15 levers):
- No repeated names
- Consequences: 2 sentences, terse but grounded
- Options: 8–20 words, some substantive, some short
- Review: 10 of 15 start with "Balances" — avg ~75 chars — at baseline length
- **Review length ratio vs baseline: ~1.0×**

Run 41 (gpt-4o-mini) silo (17 levers):
- No repeated names
- Consequences: 2–3 sentences, no fabricated %
- Options: 15–35 words
- Review: mixed "Controls" and non-"Controls" starts — avg ~90 chars
- **Review length ratio vs baseline: ~1.2×**

Run 45 (llama3.1) silo (21 levers):
- Label-only options in later call groups (N1)
- Consequences: 2 sentences, mixed quality
- Review: all start with "Controls" or "Centralizing" — avg ~80 chars

### vs. Analysis/18 (prompt_4)

| Metric | Analysis/18 (runs 31–37) | Analysis/19 (runs 38–45) | Direction |
|--------|--------------------------|--------------------------|-----------|
| Overall success rate | 35/35 (100%) | 35/35 (100%) | MAINTAINED |
| Bracket placeholders in review fields | 0 (already resolved) | 0 | MAINTAINED |
| Non-"Controls" review first sentences | 0 (old validator blocked them) | ~18 across qwen3+gpt-4o-mini | NEW (validator relaxed) |
| haiku review quality | Substantive, ~180 char avg | Substantive, ~200 char avg | SLIGHT IMPROVEMENT |
| qwen3 review quality | "Controls X vs Y. Weakness: short" | "Balances X vs Y. Weakness: short" | CHANGED FORMAT, same depth |
| gpt-4o-mini review quality | "Controls X vs Y. Weakness: ok" | Mixed starts, similar depth | CHANGED FORMAT |
| llama3.1 label-only options | 7/21 levers (call-2) | Multiple levers in later calls | PERSISTS |
| Fabricated % in consequences | Minimal (llama3.1 only) | Not observed in sample | MAINTAINED |
| LLMChatErrors | 0 | 0 | MAINTAINED |

---

## Quantitative Metrics

### Table 1: Success Rate by Model

| Run | Model | Plans OK | Plans Failed | LLMChatErrors |
|-----|-------|----------|-------------|---------------|
| 38 | qwen3-30b | 5 | 0 | 0 |
| 40 | gpt-5-nano | 5 | 0 | 0 |
| 41 | gpt-4o-mini | 5 | 0 | 0 |
| 42 | gemini-2.0-flash | 5 | 0 | 0 |
| 43 | haiku-4-5 | 5 | 0 | 0 |
| 44 | gpt-oss-20b | 5 | 0 | 0 |
| 45 | llama3.1 | 5 | 0 | 0 |
| **Total** | | **35** | **0** | **0** |

Sources: `events.jsonl` for each run, all showing only `run_single_plan_complete` events.

### Table 2: Review Field — "Controls" vs Other Starts (silo plan)

| Run | Model | Reviews starting "Controls" | Reviews starting other | Total |
|-----|-------|---------------------------|----------------------|-------|
| 34 (analysis/18) | qwen3 | 15 | 0 | 15 |
| 37 (analysis/18) | haiku | 26 | 0 | 26 |
| 35 (analysis/18) | gpt-4o-mini | ~17 | 0 | 17 |
| **38 (analysis/19)** | **qwen3** | **5** | **10** | **15** |
| **41 (analysis/19)** | **gpt-4o-mini** | **9** | **8** | **17** |
| **42 (analysis/19)** | **gemini** | **18** | **0** | **18** |
| **43 (analysis/19)** | **haiku** | **25** | **0** | **25** |
| **45 (analysis/19)** | **llama3.1** | **~20** | **~1** | **21** |

Source: direct examination of review fields in output files listed above. The before values
(runs 34, 37) are from files read during analysis/18; the after values are from output files
in this batch. qwen3 and gpt-4o-mini now produce non-"Controls" reviews that pass the new
validator.

### Table 3: Bracket Placeholder Count in Review Fields

| Batch | Runs | Occurrences of `[Tension A]`/`[Tension B]`/`[specific factor]` |
|-------|------|----------------------------------------------------------------|
| Before (runs 31–37) | analysis/18 | 0 |
| After (runs 38–45) | analysis/19 | 0 |

Note: bracket placeholders were more prevalent in earlier batches (run 19 had 6 verbatim
placeholder levers). By analysis/18, the prompt_4 change had already eliminated them.
PR #299 replaced the placeholder text in the field descriptions to prevent future recurrence.
Source: Grep for `\[Tension` and `\[specific factor` across all after-PR output files.

### Table 4: Review Field Length vs Baseline (silo plan)

| Source | Avg review chars | Ratio to baseline |
|--------|-----------------|-------------------|
| Baseline silo | ~75 | 1.0× |
| Run 34 (qwen3, analysis/18) | ~80 | 1.1× |
| Run 37 (haiku, analysis/18) | ~180 | 2.4× |
| **Run 38 (qwen3, analysis/19)** | **~75** | **1.0×** |
| **Run 41 (gpt-4o-mini, analysis/19)** | **~90** | **1.2×** |
| **Run 42 (gemini, analysis/19)** | **~65** | **0.9×** |
| **Run 43 (haiku, analysis/19)** | **~200** | **2.7×** |
| **Run 45 (llama3.1, analysis/19)** | **~80** | **1.1×** |

Source: character count averages from examination of silo plan output files per run.
Haiku's review length increased slightly (+0.3× baseline) compared to analysis/18; other
models are at or below baseline. The 2.7× haiku ratio consists of genuinely substantive
multi-clause Weakness sentences, not padding.

### Table 5: Run Durations (silo plan)

| Run | Model | Silo Duration | vs. analysis/18 equivalent |
|-----|-------|--------------|---------------------------|
| 38 | qwen3-30b | 280.97s | 67.44s (run 34) — 4.2× SLOWER |
| 40 | gpt-5-nano | 167.14s | 178.92s (run 33) — similar |
| 41 | gpt-4o-mini | 49.24s | 59.20s (run 35) — similar |
| 42 | gemini-2.0-flash | 29.33s | 32.34s (run 36) — similar |
| 43 | haiku-4-5 | 97.52s | 122.93s (run 37) — faster |
| 44 | gpt-oss-20b | 58.46s | 53.92s (run 32) — similar |
| 45 | llama3.1 | 114.55s | 115.78s (run 31) — identical |

Sources: `events.jsonl` for runs 38, 40–45; analysis/18 values from its `events.jsonl` files.

The qwen3 silo duration anomaly (280.97s vs 67.44s) is striking. This may reflect cloud rate
limiting or a heavier context in one of the LLM calls, not an artifact of the PR change. Other
qwen3 plans in run 38 ran in 67–126s, not anomalously slow.

### Table 6: Label-Only Options in llama3.1 (silo plan)

| Batch | Run | Model | Label-only option levers / Total |
|-------|-----|-------|----------------------------------|
| Analysis/18 | 31 | llama3.1 | 7/21 (33%) |
| **Analysis/19** | **45** | **llama3.1** | **~8/21 (38%)** |

Source: `history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.
Levers "Ecological Integration", "Governance Architecture", "Cultural Preservation", "Risk
Management Protocol", "Public Relations Strategy", "Silo-External Interface",
"Socio-Psychological Analysis", "Infrastructure Development Roadmap" all show 2–3 word options.
This is the same multi-call degradation documented in analysis/18 (N1). The count is slightly
higher (8 vs 7) but within noise range.

---

## Evidence Notes

- **Run 38 qwen3 non-"Controls" reviews**: `history/1/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, 10/15 review fields begin with "Balances".
- **Run 41 gpt-4o-mini non-"Controls" reviews**: `history/1/41_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, 8/17 review fields use non-"Controls" starts.
- **Run 43 haiku high-quality reviews**: `history/1/43_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` and `history/1/43_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — all reviews substantive, all start "Controls".
- **Run 42 gemini clean format**: `history/1/42_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all reviews start "Controls", terse Weakness sentences.
- **Run 45 llama3.1 label-only options**: `history/1/45_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — levers 15–21 (call-3) show 2–3 word option labels.
- **No bracket placeholders anywhere in after-PR batch**: Grep for `\[Tension` and `\[specific factor` in all output files under `history/1/38_identify_potential_levers/` through `history/1/45_identify_potential_levers/` returns zero results.
- **Run 38 silo slow duration**: `history/1/38_identify_potential_levers/events.jsonl` line 10 — `"duration_seconds": 280.97`. Other plans in same run: 85.39s, 87.26s, 126.04s, 67.09s.
- **Baseline review format**: `baseline/train/20250321_silo/002-10-potential_levers.json` — all 15 reviews start "Controls X vs. Y." at ~75 chars.

---

## PR Impact

### What the PR was supposed to fix (PR #299)

1. **Bracket placeholders** (`[Tension A]`, `[Tension B]`, `[specific factor]`) in the
   `review_lever` field description and system prompt were being echoed literally into output.
   The PR replaced them with concrete literal examples.

2. **Fragile English-only validator** (`check_review_format` checking for `'Controls '` and
   `'Weakness:'`): Any non-English model output or any output that expressed the tension
   differently (e.g., "Balances") would fail validation. The PR replaced this with structural
   checks: min 20 chars + reject square brackets.

3. **Summary format alignment**: Aligned with prompt_4's one-sentence concrete prescription
   format.

### Before vs After Comparison

| Metric | Before (runs 31–37) | After (runs 38–45) | Change |
|--------|--------------------|--------------------|--------|
| Overall success rate | 35/35 (100%) | 35/35 (100%) | MAINTAINED |
| Bracket placeholders in reviews | 0 | 0 | MAINTAINED (already resolved in prompt_4) |
| Non-"Controls" reviews allowed by validator | 0 | ~18 (qwen3+gpt-4o-mini) | NEW — validator now permissive |
| LLMChatErrors | 0 | 0 | MAINTAINED |
| haiku review quality | Substantive, ~180 chars | Substantive, ~200 chars | SLIGHT IMPROVEMENT |
| qwen3 review format | All "Controls..." | 10/15 "Balances..." | FORMAT CHANGED |
| gpt-4o-mini review format | All "Controls..." | 8/17 non-"Controls" | FORMAT CHANGED |
| llama3.1 label-only options | 7/21 levers | ~8/21 levers | UNCHANGED |
| Fabricated % in consequences | Minimal | Not observed | MAINTAINED |

### Did the PR fix the targeted issues?

**Issue 1 — Bracket placeholders**: The bracket placeholder issue was already resolved by
prompt_4 (no occurrences in analysis/18 either). PR #299 hardened the defence by removing
the placeholder text from field descriptions and the system prompt constant. This is a
preventive measure against future regression. **Effect: confirmed preventive, not curative.**

**Issue 2 — English-only validator**: The old validator (`check_review_format` requiring
`'Controls '` and `'Weakness:'`) did block non-English output and alternative phrasings.
The new structural validator (min 20 chars, reject square brackets) demonstrably allows qwen3
and gpt-4o-mini to produce "Balances" and other non-"Controls" review first sentences. These
would have caused validation failures under the old validator.

This is a genuine fix for internationalization. However, it introduces a format divergence:
qwen3 and gpt-4o-mini now use varied first sentences while haiku and gemini still use "Controls".
The question is whether this variety represents an improvement or loss of consistency.

**Issue 3 — Summary field alignment**: Not independently verified in this analysis; no summary
field comparison was performed between runs 31–37 and 38–45. Flagging for synthesis.

### Did the PR introduce regressions?

**Format inconsistency across models**: The old validator enforced a consistent "Controls X
vs. Y. Weakness: ..." format across all models. The new validator allows varied first
sentences. This means different models now produce reviews in different formats, which may
complicate downstream comparison and aggregation.

Whether this is a regression depends on the intended use of the `review` field. If the format
is used for display or structured parsing downstream, inconsistency is a regression. If the
field is intended to convey the semantic content of a tension and weakness, the variety is
acceptable.

**No other regressions detected.** Success rate is maintained at 100%, fabricated % remain
absent in consequences, and no new error patterns appear.

### Verdict

**CONDITIONAL**

PR #299 successfully addresses the internationalization concern by removing the English-only
keyword validator. The bracket placeholder prevention is a valid hardening measure. However:

1. The validator relaxation allows format variation (run 38 qwen3, run 41 gpt-4o-mini) that
   reduces cross-model consistency. The old format ("Controls X vs. Y.") had concrete
   informational structure; the new permissive validator allows shorter, less structured
   first sentences.

2. The bracket placeholder problem was already solved by prompt_4 — PR #299 provides
   defense in depth but its primary observable effect in this batch is the validator relaxation.

3. Whether "Balances X with Y. Weakness: ..." is equivalent in quality to "Controls X vs. Y.
   Weakness: ..." is a judgment call for synthesis. The new format passes structural checks
   but may dilute the analytical framing the "Controls X vs. Y" pattern provides.

The PR should be kept if internationalization is a priority and format consistency can be
enforced via the prompt alone. The prompt already says "First sentence names the core tension"
with example "Controls centralization vs. local autonomy." — this guidance is present but not
universally followed. If maintaining consistent format matters more than non-English tolerance,
the validator change needs reconsideration.

---

## Questions For Later Synthesis

1. **Is "Balances X with Y" inferior to "Controls X vs. Y" for downstream use?** The
   downstream scenario picker uses lever reviews to understand tensions. Does the "Controls"
   framing provide any structural advantage, or is any tension statement acceptable?

2. **Should the prompt be strengthened to enforce "Controls X vs. Y" phrasing without
   requiring a code validator?** Adding the instruction "First sentence must use the pattern
   'Controls [tension A] vs. [tension B].' — use this exact grammatical structure" might
   enforce consistency across models without hard-coding English keywords in code.

3. **What is the root cause of qwen3's shift from "Controls" to "Balances"?** In analysis/18
   (run 34, prompt_4), qwen3 used "Controls" exclusively. In analysis/19 (run 38, prompt_5),
   10/15 use "Balances". The change is likely driven by removing the validator that rejected
   non-"Controls" output. This means the old validator was shaping qwen3's output to "Controls"
   even when qwen3 would naturally produce "Balances".

4. **Was the summary field change observable?** The analysis did not compare summary field
   content between prompt_4 and prompt_5 runs. Synthesis should verify whether the summary
   format changed meaningfully.

5. **Is llama3.1 multi-call degradation a prompt issue or a code issue?** The pattern
   persists across both prompt_4 and prompt_5. Neither prompt changed the multi-call structure.
   The C1 hypothesis from analysis/18 (context crowding in later calls) remains untested.

6. **What caused qwen3 silo to take 280.97s in run 38?** Spike may indicate rate limiting.
   This should be checked against run 38's other plan durations and any provider-side metrics.

---

## Reflect

The most significant observable effect of PR #299 in this batch is the validator relaxation
rather than the bracket placeholder fix. The bracket placeholder problem was already resolved
by prompt_4 (analysis/18); PR #299's preventive hardening adds defensive value but produces
no observable change in outputs.

The validator change is genuinely important for internationalization, but it introduces a
measurable format consistency regression: qwen3 and gpt-4o-mini now produce varied first
sentences in review fields. Whether this matters depends on downstream use of `review` fields.

Haiku (run 43) continues to produce the best lever quality in this optimization loop, with
analytically substantive review fields that raise genuinely new considerations. The PR did not
harm haiku's output.

The llama3.1 multi-call label-only option degradation is now documented in two consecutive
batches (analysis/18 and analysis/19) without improvement. It is the clearest remaining
structural quality problem. A code fix (C1 from analysis/18) or prompt addition (H2 from
analysis/18) is the next logical step.

---

## Potential Code Changes

**C1 — The `check_review_format` validator in the new code now passes reviews of any form
as long as they are ≥20 chars and contain no square brackets.**

This is correct for internationalization. However, if "Controls X vs. Y" provides structural
value downstream, the validator could be enhanced to check for `vs.` (language-agnostic in
English/French/Spanish) rather than `'Controls '`. Alternatively, the validator could accept
multiple patterns via a regex.

Evidence: runs 38 (qwen3) and 41 (gpt-4o-mini) both produce structurally valid but
format-inconsistent reviews under the new validator. Under the old validator, these would have
failed and retried to produce "Controls" format. The old validator was unintentionally
enforcing format consistency.

Expected effect: If the validator included a soft structural check (e.g., `vs.` present), it
would accept non-English equivalents while still guiding models toward the tension-naming
structure.

**C2 — Multi-call context crowding for llama3.1 (from analysis/18, still unresolved)**

The runner sends a growing list of "already-generated lever names" to calls 2 and 3. For
llama3.1, this appears to crowd the instruction text to the point where the model reverts to
minimal-effort outputs. Reducing the names list or restructuring the call-2/call-3 prompt to
reinforce option quality could fix the label-only option degradation.

Evidence: label-only options persist at ~33–38% of levers in runs 31 and 45 (both llama3.1
silo), while call-1 options are substantive. The degradation is call-position-dependent, not
model-capability-dependent.

---

## Hypotheses

**H1 — Adding explicit "Controls X vs. Y" wording guidance to the prompt would restore format
consistency without requiring a validator change**

The current prompt says: "Example: 'Controls centralization vs. local autonomy. Weakness: The
options fail to account for transition costs.'" This example is sufficient for haiku and gemini
but not for qwen3 and gpt-4o-mini under the new validator.

Adding "First sentence must follow this exact pattern: 'Controls [one tension] vs. [opposite
tension].' — use this grammatical structure even if the specific words differ" might enforce
consistency via the system prompt rather than code.

Evidence: qwen3 (run 34, analysis/18) produced all "Controls" reviews under the old validator.
qwen3 (run 38, analysis/19) produces 10/15 "Balances" reviews under the new validator. The
validator was guiding qwen3's output format.

Prediction: Adding explicit grammatical pattern guidance to the prompt would produce
consistent "Controls X vs. Y" format across all models while still allowing the structural
validator to accept non-English equivalents.

**H2 — Minimum option length guidance would fix llama3.1 label-only options (from
analysis/18, still valid)**

The same hypothesis from analysis/18 remains untested. An explicit "each option must describe
the approach in at least 15 words" in the prompt would anchor llama3.1 in later calls.

Evidence: call-1 options are substantive (15–30 words) and call-2/call-3 options are labels
(2–3 words), in both analysis/18 and analysis/19. The model can produce full options; the
degradation is context-dependent.

Prediction: Adding minimum-word-count guidance would eliminate label-only options in later
calls for llama3.1 without affecting other models (which already produce complete options).

**H3 — The bracket placeholder prevention in PR #299 protects against regression from
future prompt variants**

If a future prompt experiment reintroduces structural language close to the old placeholder
format, the new field description (with concrete examples replacing brackets) reduces the risk
of models echoing bracket text. This is a defensive hypothesis — no observable effect in
this batch, but the change reduces one failure mode in the hypothesis space.

Evidence: Run 19 (using an older prompt with `[Tension A]`/`[Tension B]` placeholder text in
the field description) produced 6 verbatim placeholder levers. Removing the placeholder text
from the field description eliminates the template-echo trigger.

---

## Summary

Runs 1/38–1/45 maintain the 100% success rate established in analysis/18. The primary PR
changes produce these observable outcomes:

1. **Bracket placeholder prevention**: No bracket placeholders observed — but this was already
   true in analysis/18. PR #299 adds defensive hardening.

2. **Validator relaxation**: qwen3 and gpt-4o-mini now produce non-"Controls" review first
   sentences ("Balances", "Encourages", "Focuses") that pass structural validation but deviate
   from the format other models maintain. This is the most visible change in this batch.

3. **Format consistency regression**: Before PR, all models produced "Controls X vs. Y.
   Weakness: ..." reviews (enforced by the old validator). After PR, two of seven models
   produce varied first sentences.

4. **Internationalization improvement**: The new structural validator correctly accepts
   equivalent non-English review expressions — the intended fix.

5. **No new errors**: All 35 plans complete successfully with zero LLMChatErrors.

The one unresolved issue from analysis/18 — llama3.1 label-only options in later calls
(~33–38% of levers) — is unchanged and requires follow-up (C2/H2).

**Highest priority next step**: Add explicit "Controls X vs. Y" grammatical pattern guidance
to the prompt (H1) to restore cross-model format consistency while preserving the structural
validator's internationalization benefit.

**PR #299 verdict: CONDITIONAL.** The internationalization fix is valid and should be kept.
The bracket placeholder hardening is defensively sound. However, the validator relaxation
produces a format inconsistency that should be addressed via a prompt addition before
declaring the change fully successful.
