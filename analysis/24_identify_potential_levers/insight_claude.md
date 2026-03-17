# Insight Claude

## Overview

This analysis examines 7 "after" runs (75–81) using the prompt from PR #334
against 7 "before" runs (67–73) using the prompt from PR #326 (prompt_7).

**PR #334 changes:**
1. Remove `DocumentDetails.summary` field — required by schema but never used downstream
2. Remove summary validation section from system prompt
3. Add "at least 15 words with an action verb" to section 6 (option structure) for uniform enforcement
4. Slim call-2/3 prefix: remove duplicate quality/anti-fabrication reminders

**Model lineup:**

| Run | Model | Workers | PR |
|-----|-------|---------|-----|
| 67 | ollama-llama3.1 | 1 | #326 (before) |
| 68 | openrouter-openai-gpt-oss-20b | 4 | #326 (before) |
| 69 | openai-gpt-5-nano | 4 | #326 (before) |
| 70 | openrouter-qwen3-30b-a3b | 4 | #326 (before) |
| 71 | openrouter-openai-gpt-4o-mini | 4 | #326 (before) |
| 72 | openrouter-gemini-2.0-flash-001 | 4 | #326 (before) |
| 73 | anthropic-claude-haiku-4-5-pinned | 4 | #326 (before) |
| **75** | ollama-llama3.1 | 1 | **#334 (after)** |
| **76** | openrouter-qwen3-30b-a3b | 4 | **#334 (after)** |
| **77** | openrouter-qwen3-30b-a3b | 4 | **#334 (after)** |
| **78** | openrouter-qwen3-30b-a3b | 4 | **#334 (after)** |
| **79** | openrouter-openai-gpt-4o-mini | 4 | **#334 (after)** |
| **80** | openrouter-gemini-2.0-flash-001 | 4 | **#334 (after)** |
| **81** | anthropic-claude-haiku-4-5-pinned | 4 | **#334 (after)** |

**Important caveat:** gpt-oss-20b (run 68) and gpt-5-nano (run 69) are absent from
the after set. qwen3-30b-a3b is run three times (76, 77, 78) vs once (run 70).
Matched pairs for clean before/after comparison exist for: llama3.1 (67↔75),
qwen3 (70↔76/77/78), gpt-4o-mini (71↔79), gemini (72↔80), haiku (73↔81).

---

## Negative Things

**N1. llama3.1 template lock WORSENED to 100% in run 75.**
Run 75 (llama3.1, after) silo: all 21 reviews follow "This lever governs the
tension between X and Y, but the options overlook Z." exactly — 100% lock.
Run 67 (llama3.1, before) silo: 71% first example, 29% second example
("Prioritizing X over Y carries hidden costs…"). The second example pattern has
completely disappeared in run 75.

Evidence: `history/1/75_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
— every review is "This lever governs the tension between…"; representative sample:
> "This lever governs the tension between caution and expediency, but the options
> overlook potential environmental consequences of accelerated excavation."
> "This lever governs the tension between centralization and decentralization, but
> the options overlook potential social implications of resource distribution."

Compared to run 67 silo where the second pattern appeared:
> "Prioritizing speed over reliability carries hidden costs: none of the options
> address rollback complexity."
> "Prioritizing control over knowledge carries hidden costs: none of the options
> address potential knowledge gaps or missed opportunities."

Evidence: `history/1/67_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

**N2. hong_kong_game fully failed in run 75 (llama3.1).**
Run 75 events show `run_single_plan_error` for hong_kong_game:
`"LLM chat interaction failed [6b49cb2cd9e2]: Failed to run. Exhausted all LLMs.
Failure summary: Attempt 0 with LLMModelFromName(name='ollama-llama3.1') failed
during 'execute' stage: ReadTimeout('timed out')"`
Duration: 120.11 seconds.

Run 67 had hong_kong_game as a partial_recovery (2/3 calls) but no full timeout.
This is a reliability regression for llama3.1 on the hong_kong_game plan.

Evidence: `history/1/75_identify_potential_levers/events.jsonl`

**N3. qwen3 run 78 had a parasomnia JSON extraction failure.**
Run 78 events show `run_single_plan_error` for parasomnia_research_unit:
`"ValueError('Could not extract json string from output…')"`
Duration: 67.91 seconds.
This suggests the model produced output that the JSON parser could not extract,
which could be a schema-compliance issue or a model quirk. No such error appeared
in run 70 (qwen3, before).

Evidence: `history/1/78_identify_potential_levers/events.jsonl` (inferred from
agent-collected data noting this error).

**N4. "at least 15 words with an action verb" produced no measurable change.**
Option character lengths for llama3.1 silo are approximately the same before and
after the PR:
- Run 67 (before): avg ~113 chars per option; already exceeded 15-word minimum
- Run 75 (after): avg ~110 chars per option
Both runs already satisfied the minimum before the instruction was added. The
instruction enforces an existing baseline rather than raising it.

**N5. Second review example absent in run 75 — diversity reduced for llama3.1.**
The second review example added by PR #326 ("Prioritizing X over Y carries hidden
costs: none of the options address Z") accounted for 29% (5/17) of silo reviews
in run 67. In run 75 it accounts for 0/21 = 0%. This is a regression in review
diversity for llama3.1 specifically, and may be a consequence of the slimmed
call-2/3 prefix (if that prefix previously reinforced the second example).

---

## Positive Things

**P1. Strong models (haiku, gemini, gpt-4o-mini) completed cleanly in all after runs.**
Runs 79 (gpt-4o-mini), 80 (gemini), and 81 (haiku) all show zero errors and zero
partial_recovery events. All 5 plans completed for each run.
Evidence:
- `history/1/79_identify_potential_levers/events.jsonl` — all plans 57–68 seconds, no errors
- `history/1/80_identify_potential_levers/events.jsonl` — all plans 33–38 seconds, no errors
- `history/1/81_identify_potential_levers/events.jsonl` — all plans 87–160 seconds, no errors

**P2. No fabricated percentages in any matched-model run.**
Neither run 75 (llama3.1) nor the matched stronger models show fabricated
percentage claims in the silo or hong_kong_game outputs sampled. The
anti-fabrication instruction continues to hold. The removal of duplicate
anti-fabrication reminders from the call-2/3 prefix did not produce a regression
in fabricated numbers.

**P3. qwen3 reviews shifted toward non-template "Core tension:" pattern.**
Runs 76–78 (qwen3) show reviews that use "Core tension: X. Weakness: Y." or
"Core tension: X. Option-specific analysis." openings. This is a different
pattern from both prompt examples ("This lever governs the tension between" and
"Prioritizing X over Y carries hidden costs"). While still somewhat formulaic,
it represents a different abstraction than the locked first-example pattern seen
in llama3.1.

Example from run 76/77 agent-collected data:
> "Core tension: balancing local authenticity with global thriller cadence..."
> "Core tension: regulatory risk vs market reach..."
> "This lever governs tension between vertical-density storytelling and production logistics..."

This is qwen3-specific — likely derived from the model's own training rather than
the prompt examples — and represents a moderate improvement over pure template lock.

**P4. Summary field removal is an unambiguous engineering improvement.**
The `DocumentDetails.summary` field was required by the Pydantic schema but never
used downstream (per the PR description). Removing it eliminates a source of
unnecessary token generation and removes a potential schema validation failure
point. No negative side effects observed in any run.

**P5. qwen3 runs (76–78) produce plentiful output with good lever counts.**
Run 76: 20 levers for hong_kong_game; run 77: 19 levers; run 78: 16 levers
(parasomnia failed, so the others were unaffected). These are consistent with
the lever-generation targets.

---

## Comparison

### Before (runs 67–73) vs After (runs 75–81)

The central comparison plane is same-model performance before/after the prompt change.

**llama3.1 (67 vs 75):**
Run 67 showed the second review example active at 29% of silo reviews, with
partial_recovery on 3 plans and hong_kong_game partial (2/3). Run 75 shows zero
second-example reviews, 2 partial_recovery, and hong_kong_game fully failed.
This is a regression on llama3.1 across both template diversity and reliability.

**qwen3 (70 vs 76/77/78):**
Run 70 (before) had 17% "governs tension" and 67% "This lever…" opener.
Runs 76–78 (after) show "Core tension:" as a dominant opening — different from
both template examples. Lever count is consistent (16–20 per run). One error
in run 78 (parasomnia ValueError) vs zero errors in run 70. Minor regression in
reliability but possible improvement in review diversity.

**gpt-4o-mini (71 vs 79), gemini (72 vs 80), haiku (73 vs 81):**
All three model pairs show clean completion in both before and after runs. No
regressions observed in completion rate for these models.

### Against Baseline Training Data

The baseline train silo (`baseline/train/20250321_silo/002-10-potential_levers.json`)
contains heavily fabricated percentages in consequences (e.g., "15% increase in
black market activity", "30% reduction in innovative output"). Neither the before
nor after runs reproduce this pattern — fabricated numbers remain absent across all
runs, which is a substantial quality improvement over the very early baseline.

The baseline hong_kong_game consequences averaged ~265 chars per prior analysis
findings. Current llama3.1 runs (67, 75) average ~150–174 chars for silo
consequences, which is significantly below the baseline for hong_kong_game but
the plans are different and not directly comparable without a baseline file for silo.

---

## Quantitative Metrics

### Template Lock — silo plan (llama3.1)

| Pattern | Run 67 (before) | Run 75 (after) | Change |
|---------|-----------------|----------------|--------|
| "This lever governs the tension between" | 12/17 (71%) | 21/21 (100%) | **Regression** |
| "Prioritizing X over Y carries hidden costs" | 5/17 (29%) | 0/21 (0%) | **Regression** |
| Other / free-form | 0/17 (0%) | 0/21 (0%) | Same |

### Option Length — silo plan (llama3.1)

| Metric | Run 67 (before, llama3.1) | Run 75 (after, llama3.1) | Change |
|--------|--------------------------|--------------------------|--------|
| Lever count | 17 | 21 | +4 |
| Min option length (chars) | 69 | 68 | Same |
| Max option length (chars) | 158 | 161 | Same |
| Avg option length (chars) | ~113 | ~110 | Negligible |
| Options meeting 15-word min | ~95%+ | ~95%+ | Same |

**Interpretation:** The "at least 15 words with an action verb" instruction did not
increase option length. Options were already well above this threshold in run 67.
The instruction codifies existing behavior rather than raising the bar.

### Consequence Field Length — silo plan (llama3.1)

| Metric | Run 67 (before) | Run 75 (after) | Ratio |
|--------|-----------------|----------------|-------|
| Avg consequence chars | ~150 | ~174 | 1.16× |

No significant change. Ratio of 1.16× is well below the 2× warning threshold.

### Reliability — all plans

| Run | Model | Errors (full) | Partial_recovery | Plans OK |
|-----|-------|---------------|------------------|----------|
| 67 | llama3.1 | 0 | 3 | 2/5 full |
| 68 | gpt-oss-20b | 0 | 0 | 5/5 |
| 69 | gpt-5-nano | 0 | 0 | 5/5 |
| 70 | qwen3-30b-a3b | 0 | 0 | 5/5 |
| 71 | gpt-4o-mini | 0 | 0 | 5/5 |
| 72 | gemini-2.0-flash | 0 | 0 | 5/5 |
| 73 | haiku | 0 | 0 | 5/5 |
| **75** | llama3.1 | **1** | 2 | 2/5 full |
| **76** | qwen3-30b-a3b | 0 | 0 | 5/5 |
| **77** | qwen3-30b-a3b | 0 | 0 | 5/5 |
| **78** | qwen3-30b-a3b | **1** | 0 | 4/5 |
| **79** | gpt-4o-mini | 0 | 0 | 5/5 |
| **80** | gemini-2.0-flash | 0 | 0 | 5/5 |
| **81** | haiku | 0 | 0 | 5/5 |

### Fabricated Percentage Claims

| Model | Run (before) | % claims | Run (after) | % claims | Change |
|-------|-------------|---------|------------|---------|--------|
| llama3.1 | 67 | 0 | 75 | 0 | Same |
| qwen3 | 70 | 0 | 76 | 0 | Same |
| gpt-4o-mini | 71 | 0 | 79 | 0 | Same |
| gemini | 72 | 0 | 80 | 0 | Same |
| haiku | 73 | 0 | 81 | 0 | Same |

Note: The preceding analysis (23) flagged run 69 (gpt-5-nano) as having zero
fabricated percentages, but agent-collected evidence for this analysis found
substantial % claims in run 69's hong_kong_game output ("15% higher audience
engagement", "20% higher pre-sales", "30% increase in streaming revenue", etc.).
gpt-5-nano is not present in the after set, so no before/after comparison is
possible, but this represents a discrepancy in the prior analysis that should
be resolved. See Evidence Notes E1.

---

## Evidence Notes

**E1. Potential discrepancy in prior analysis regarding gpt-5-nano fabrications.**
`analysis/23_identify_potential_levers/insight_claude.md` states P3: "No
fabricated percentages in any run 67–73." However, agent-collected data for the
current analysis found percentage claims in run 69 (gpt-5-nano) hong_kong_game:
"15% higher audience engagement", "20% higher pre-sales", "30% increase in
streaming revenue", "10% increase in production costs", "25% increase in tourism."
If confirmed by re-reading
`history/1/69_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
the prior analysis missed these fabrications. Recommend independent verification.

**E2. llama3.1 template regression in run 75 may trace to slimmed prefix.**
PR #334 removed "duplicate quality/anti-fabrication reminders" from the call-2/3
prefix. If the call-2/3 prefix also included a reinforcement of the second review
example (even implicitly, as a format reminder), removing that text could explain
why the second pattern ("Prioritizing X over Y carries hidden costs") went from
29% in run 67 to 0% in run 75. Without reading the full system prompt diff, this
is a hypothesis, not a confirmed cause.

**E3. Run 75 hong_kong_game timeout vs run 67 partial.**
`history/1/75_identify_potential_levers/events.jsonl`:
```json
{"event": "run_single_plan_error", "plan_name": "20260310_hong_kong_game",
 "error": "LLM chat interaction failed [6b49cb2cd9e2]: Failed to run. Exhausted
 all LLMs. Failure summary: Attempt 0 with LLMModelFromName(name='ollama-llama3.1')
 failed during 'execute' stage: ReadTimeout('timed out')", "duration_seconds": 120.11}
```
`history/1/67_identify_potential_levers/events.jsonl` showed partial_recovery for
hong_kong_game (2/3 calls, no full timeout). The hong_kong_game plan is the most
complex in the set; llama3.1 consistently struggles with it.

**E4. qwen3 "Core tension:" reviews not template-locked to prompt examples.**
Agent-collected data from runs 76–77 shows qwen3 generating reviews that start with
"Core tension:" — a phrase not present in either prompt example. This may indicate
qwen3 is abstracting the concept of tension rather than copying the example surface
form. However, "Core tension:" as a consistent opener is itself a template pattern,
even if not derived from the prompt examples.

**E5. Consequences field length comparison — run 75 vs run 67 (silo, llama3.1).**
Run 67 silo: consequences range from ~108 to ~218 chars; heavily using "Directly
impact the project's X. Downstream implications include…" formula.
Run 75 silo: consequences range from ~63 to ~302 chars; more varied, mixing
"Pulling this lever could lead to…", "Decide how to manage…", and longer
analytical forms. Average run 75: ~174 chars vs run 67: ~150 chars. Neither
exceeds the 2× baseline warning threshold.

---

## PR Impact

### What the PR was supposed to fix

PR #334 targeted token efficiency and structural improvements:
1. Remove `DocumentDetails.summary` field that was required but never used
2. Remove summary validation section from system prompt
3. Standardize option length enforcement ("at least 15 words with an action verb")
4. Slim call-2/3 prefix by removing duplicate reminders already in system prompt

The PR did NOT claim to fix template lock, improve review quality, or change
output content. These are engineering changes targeting prompt cleanliness and
token savings.

### Before vs After Comparison

| Metric | Before (runs 67–73) | After (runs 75–81) | Change |
|--------|--------------------|--------------------|--------|
| Full plan errors | 0 | 2 (run 75 hong_kong_game, run 78 parasomnia) | Regression |
| Partial_recovery events | 3 (all run 67, llama3.1) | 2 (run 75, llama3.1) | Same severity |
| llama3.1 template lock rate (silo) | ~71% "governs tension" | ~100% "governs tension" | Regression |
| Second example present in llama3.1 | 29% (5/17 reviews) | 0% (0/21 reviews) | Regression |
| qwen3 template pattern | "This lever [verb]..." (67%) | "Core tension:" (different) | Slight improvement |
| Fabricated % claims (all models) | 0 (in matched models) | 0 | Same |
| Strong model completions | 5/5 per run (68–73 ex-67) | 5/5 per run (79–81) | Same |
| Option length avg (llama3.1, silo) | ~113 chars | ~110 chars | Same |
| Consequence length avg (llama3.1, silo) | ~150 chars | ~174 chars | +16%, negligible |

### Did the PR fix the targeted issues?

**Token savings (summary field):** Yes — removing an unused required field eliminates
a generation obligation with no downstream consumer. This is unambiguously positive.
No evidence of negative side effects.

**Summary validation section removal:** Positive — dead code in the prompt.
No evidence of harm.

**"At least 15 words with an action verb":** Neutral — options already exceeded this
threshold. The instruction standardizes an already-met baseline without changing
observed behavior.

**Slim call-2/3 prefix:** Possibly negative for llama3.1. The 100% template lock
rate in run 75 vs 71% in run 67 suggests the slimmed prefix may have removed
something that was helping the second example remain accessible to llama3.1.
For stronger models, no negative effect observed.

### Regressions

- **llama3.1 template lock:** 71% → 100% on "governs tension" pattern (silo).
  Second example completely absent. Whether this is due to the prefix slim or
  statistical variance is unconfirmed.
- **hong_kong_game failure in run 75:** Full timeout vs partial_recovery in run 67.
  However, llama3.1 + hong_kong_game has been borderline since the plan is complex;
  this may be noise.
- **qwen3 run 78 parasomnia error:** ValueError on JSON extraction — a new failure
  type not seen in run 70.

### Verdict: CONDITIONAL

The PR's token-saving changes (summary field removal, removing dead validation code)
are clearly positive with no negative side effects. These should be kept.

The slimmed call-2/3 prefix is potentially harmful for llama3.1's review diversity.
The disappearance of the second review example from llama3.1 output (0% vs 29%)
suggests the prefix trim may have removed implicit reinforcement of that example.
This warrants investigation: if re-running llama3.1 confirms the 100% template
lock pattern, the call-2/3 prefix change should be revisited to preserve diversity.

The "at least 15 words" instruction is harmless but also ineffective — already met
before the change.

**Recommended action:** Verify the call-2/3 prefix content diff to determine whether
the second review example was referenced or reinforced in the original prefix. If
yes, restore that reference while keeping the other efficiency gains from PR #334.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The `OPTIMIZE_INSTRUCTIONS` constant in `identify_potential_levers.py` (lines 27–73)
lists known problems: overly optimistic scenarios, fabricated numbers, hype language,
vague aspirations, English-only validation, single-example template lock.

Current run status against each:

| Known Problem | Runs 75–81 Status | Notes |
|---------------|-------------------|-------|
| Overly optimistic | Not measured in this analysis | Would need scenario-picker data |
| Fabricated numbers | ✓ None found (matched models) | gpt-5-nano discrepancy outstanding |
| Hype language | Not counted systematically | No obvious "game-changing" in samples |
| Vague aspirations | Present in llama3.1 options | e.g., "Create a dynamic, adaptive system…" |
| English-only validation | Not triggered in this run set | All plans appear English-input |
| Template lock | Partially addressed by PR #326 | Regressed for llama3.1 in after set |

**New recurring problem not yet in OPTIMIZE_INSTRUCTIONS:**

The "Core tension:" pattern emerging in qwen3 (runs 76–78) is a new model-native
template not derived from prompt examples. The OPTIMIZE_INSTRUCTIONS document
documents prompt-example-driven template lock but not model-native template patterns.
Propose adding:

> "Model-native template patterns. Some models produce reviews through their own
> fixed templates (e.g., 'Core tension: X. Y.' for qwen3) that are not copies of
> prompt examples but are still formulaic. These cannot be fixed by changing
> examples; they require explicit negative constraints ('Do not open with "Core
> tension:"') or output diversity instructions."

---

## Questions For Later Synthesis

Q1. Was the second review example referenced in the original call-2/3 prefix that
was slimmed by PR #334? If yes, the prefix trim directly caused the llama3.1
template lock regression and should be reverted for that section.

Q2. Are run 69 (gpt-5-nano) hong_kong_game consequences fabricated? The prior
analysis (23) said zero; the current agent collection found multiple percentage
claims. Verify by reading
`history/1/69_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

Q3. Is the qwen3 "Core tension:" opener a consistent feature of qwen3-30b-a3b, or
does it appear in some plans only? If consistent, should a negative constraint be
added specifically targeting that model's tendency?

Q4. Should llama3.1 be deprioritized further as a test model given persistent
partial_recovery issues (both run 67 and run 75 have reliability problems)?

Q5. Run 80 (gemini) completed all 5 plans in 33–38 seconds — extremely fast. Is
this output quality comparable to run 72 (gemini before)? Short completion time
can indicate shallow output.

---

## Reflect

The PR is primarily an engineering cleanup: removing unused schema fields and
dead prompt text. These changes are sound engineering practice. The observable
effects are small because the prompt's substance — examples, instructions, output
format — is largely unchanged.

The most concerning finding is the llama3.1 template lock regression (100% vs 71%
on "governs tension"). This is a single-run observation with high variance, but if
confirmed, it suggests the call-2/3 prefix was doing useful work in maintaining
example diversity for small models. The PR's description of removing "duplicate
quality/anti-fabrication reminders" may have inadvertently removed content that
reinforced the second example.

The experimental design confound noted in the prior analysis continues: gpt-oss-20b
and gpt-5-nano are absent from the after set, and qwen3 is run three times. A
cleaner experiment would use the identical model roster in both before and after sets.

---

## Potential Code Changes

C1. **Verify and restore second-example reinforcement in call-2/3 prefix (if
removed by PR #334)**: If the slimmed prefix removed a line that echoed or
referenced the second review_lever example, restore that reference.
Evidence: N1, N5. Expected effect: restores llama3.1 second-pattern rate to ~29%,
prevents 100% first-example lock.

C2. **Add model-native negative constraint for qwen3 "Core tension:" opener**: Add
to the review_lever section: "Do not open with 'Core tension:'; describe the
specific trade-off directly." This targets qwen3's emergent template.
Evidence: P3. Expected effect: qwen3 reviews become more varied in opening style.

C3. **Add explicit negative constraint for "This lever governs/manages the tension
between" opener (from prior C1 analysis)**: This was recommended in analysis 23
and remains unaddressed. The PR #334 did not include this.
Evidence: N1 (100% lock rate in run 75). Expected effect: llama3.1 template lock
reduced from ~71–100% to below 50%.

C4. **Deprioritize llama3.1 from the standard test suite**: Both run 67 and run 75
show chronic partial_recovery issues. The model also shows the strongest template
lock. Learning signal per run is limited given reliability problems.
Evidence: N2, runs 67 and 75 events.jsonl.

---

## Hypotheses

H1: The call-2/3 prefix in prompt_7 (before PR #334) contained a reference or
reminder to the second review_lever example. PR #334's prefix slim removed this
reference, causing llama3.1 to revert to the first example only. Test by reading
the full system prompt diff from PR #334.

H2: The qwen3 "Core tension:" pattern is consistent across qwen3-30b-a3b
regardless of prompt version. Test by reading run 70 (qwen3, before) review
fields and checking if "Core tension:" appears there too.

H3: The "at least 15 words with an action verb" instruction would have measurable
effect only for models producing label-style options (e.g., llama3.1 on gta_game
where 2-3 word option names appeared in prior analyses). For full-sentence options,
the minimum is already exceeded. Test by reading gta_game outputs from run 75.

H4: Run 80 (gemini, 33–38s completion) produces shorter/shallower output than
run 72 (gemini, before). If confirmed, the fast completion suggests a degraded
model response or a prompt change that led to less content generation.
Evidence: completion times alone are insufficient; content must be verified.

---

## Summary

PR #334 achieves its stated goals: the unused `summary` field is removed (token
savings), dead prompt text is eliminated, and option-length enforcement is
standardized. These are sound engineering improvements with no significant negative
effects on strong models (haiku, gemini, gpt-4o-mini all ran cleanly at 5/5 plans).

The main concern is a potential regression in llama3.1 review diversity: the second
review example ("Prioritizing X over Y carries hidden costs") was active at 29% in
run 67 but is absent at 0% in run 75. The cause is unconfirmed — it may be the
prefix slim removing implicit example reinforcement, or it may be statistical
variance in a single run on a weak model. This warrants verification before
fully accepting the PR.

The verdict is **CONDITIONAL**: accept the summary-field removal and dead-code
cleanup; investigate whether the prefix slim affected llama3.1 example diversity
before considering the prefix change final. A follow-up run of llama3.1 with the
post-PR prompt would confirm or refute the regression.
