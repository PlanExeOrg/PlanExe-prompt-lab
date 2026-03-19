# Insight Claude

Analysis of PR #355: "fix: B1 step-gate partial_recovery, add medical review example"

History runs examined: `history/2/66_identify_potential_levers` through `history/2/72_identify_potential_levers` (7 after-PR runs).
Reference runs: `history/2/52_identify_potential_levers` through `history/2/58_identify_potential_levers` (7 before-PR runs, from analysis 35).

---

## Rankings

| Run | Model | Workers | gta | hk | silo | sov | para | Status |
|-----|-------|---------|-----|----|------|-----|------|--------|
| 66 (after) | ollama-llama3.1 | 1 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 67 (after) | openrouter-openai-gpt-oss-20b | 4 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 68 (after) | openai-gpt-5-nano | 4 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 69 (after) | openrouter-qwen3-30b-a3b | 4 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 70 (after) | openrouter-openai-gpt-4o-mini | 4 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 71 (after) | openrouter-gemini-2.0-flash-001 | 4 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 72 (after) | anthropic-claude-haiku-4-5-pinned | 4 | ERR | 2/3 | 3/3 | 3/3 | 3/3 | ✗ error+partial |

Reference (before-PR):

| Run | Model | gta | hk | silo | sov | para | Status |
|-----|-------|-----|----|------|-----|------|--------|
| 52 (before) | ollama-llama3.1 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | ok (partial) |
| 53 (before) | openrouter-openai-gpt-oss-20b | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 54 (before) | openai-gpt-5-nano | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 55 (before) | openrouter-qwen3-30b-a3b | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 56 (before) | openrouter-openai-gpt-4o-mini | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 57 (before) | openrouter-gemini-2.0-flash-001 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | ✓ full |
| 58 (before) | anthropic-claude-haiku-4-5-pinned | 3/3 | 3/3 | 2/3 | 3/3 | 2/3 | ok (2× partial) |

Columns: gta = 20250329_gta_game, hk = 20260310_hong_kong_game, silo = 20250321_silo, sov = 20260308_sovereign_identity, para = 20260311_parasomnia_research_unit.

---

## Negative Things

### N1 — Haiku gta_game hard failure (run 72): LLMChatError EOF at column 40173

`history/2/72_identify_potential_levers/events.jsonl` line 5:
```
{"event": "run_single_plan_error", "plan_name": "20250329_gta_game",
 "error": "LLM chat interaction failed [f636a24c3eb0]: ... 1 validation error for DocumentDetails
  Invalid JSON: EOF while parsing a string at line 1 column 40173 ..."}
```

The JSON was truncated at ~40KB. Run 58 haiku gta_game succeeded (status=ok, calls_succeeded=3). Run 72 haiku parasomnia produced the largest lever output in this dataset — reviews averaging 500–700 chars per lever (vs ~140 chars in baseline). The medical IRB example is the most plausible trigger: haiku interpreted the verbose, mechanism-laden example as a formatting cue, producing very long reviews for all plans. For gta_game (21+ raw levers × 3 calls = 60+ raw levers × ~1,500 chars/lever in JSON = ~90KB before dedup), the max_tokens cap truncated the response mid-JSON, causing a hard error with no output generated.

Evidence: `history/2/72_identify_potential_levers/outputs.jsonl` (gta_game status="error", calls_succeeded=null); contrast `history/2/58_identify_potential_levers/outputs.jsonl` (gta_game status="ok", calls_succeeded=3). No output directory exists for gta_game in run 72.

### N2 — llama3.1 silo call-1 review failure: reviews are just lever names

`history/2/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, levers 1–6 (from first LLM call):
```json
{"name": "Resource Prioritization", "review": "Resource Prioritization"}
{"name": "Security Protocols", "review": "Security Protocols"}
{"name": "Information Control", "review": "Information Control"}
{"name": "Governance Structure", "review": "Governance Structure"}
{"name": "Silo Expansion", "review": "Silo Expansion"}
{"name": "Community Engagement", "review": "Community Engagement"}
```

The review field is identical to the name field — the model produced no review content whatsoever for the first call. Analysis 35 reported that run 52 silo had "All 21 reviews now start with domain-specific lever subjects" (assessment.md line 18). This is a regression: 6/20 levers (30%) have empty reviews in run 66 silo where run 52 had substantive reviews.

This affects quality but not structural compliance (the schema accepts any non-empty string).

### N3 — llama3.1 gta_game: identical output in run 52 and run 66

The 002-10-potential_levers.json files for gta_game are byte-for-byte identical between run 52 and run 66, including all lever UUIDs:
- Both start with lever_id `ff4dc5ac-ee18-46e9-9db5-c547d1ca6231` "Urban Planning Focus"
- Levers 1–7 all use `"[Lever Name] misses/overlooks..."` template
- Levers 8–21 all use `"The tension here is between ... this lever/these options..."` template

The medical IRB example had zero observable effect on llama3.1 gta_game output. Template lock is 100% across all 21 levers (7 use "[Name] verb" pattern, 6 use "The tension here... this lever", 8 use "The tension here... The weakness in these options").

Evidence: `history/2/66_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` vs `history/2/52_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

### N4 — haiku hong_kong partial_recovery persists (run 72)

`history/2/72_identify_potential_levers/events.jsonl` line 8:
```
{"event": "partial_recovery", "plan_name": "20260310_hong_kong_game", "calls_succeeded": 2, "expected_calls": 3}
```

The B1 fix removed the stale `expected_calls=3` constant from `_run_levers`, but the partial_recovery event in identify_potential_levers still records `expected_calls=3`. This is consistent with the PR description (the stale constant removal was specifically for identify_documents logic; identify_potential_levers still expects 3 calls). However, the fact that haiku had `partial_recovery` for hong_kong in run 72 while run 58 haiku did NOT have hong_kong partial_recovery (only silo and parasomnia) suggests haiku's reliability on hong_kong actually worsened.

### N5 — llama3.1 parasomnia: first-call "The options miss" lock persists

`history/2/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, levers 1–6 (first LLM call):
```
"The options miss the core tension between standardizing sleep environment..."
"The options miss the weakness in relying solely on self-reported episodes..."
"The options miss the trade-off between integrating multiple sensor streams..."
"The options miss the weakness in scaling up residential monitoring operations..."
"The options miss the tension between sharing de-identified physiological data..."
"The options miss the trade-off between developing semi-automated event-triage tools..."
```

All 6 levers from the first call still use "The options miss..." opener. The medical example broke the 2nd call's "The lever misses" pattern but had no effect on the 1st call's "The options miss" pattern.

### N6 — llama3.1 parasomnia: third-call NEW template "[Lever Name] lever overlooks"

`history/2/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, levers 13–17 (third LLM call):
```
"Participant Flow Optimization lever misses the trade-off..."
"Sensor Data Quality Enhancement lever overlooks the potential impact..."
"Event-Triage Algorithm Refining lever neglects the potential computational overhead..."
"Participant Compensation Strategy lever overlooks the potential impact..."
"Participant Inclusion Criteria Relaxation lever overlooks the potential impact..."
```

A new secondary template "[Lever Name] lever misses/overlooks/neglects" emerged in the 3rd LLM call. This is structurally similar to the "The lever misses" pattern from the 2nd call in run 52, migrated to use the lever name as grammatical subject. Lock rate for the 3rd call: 5/5 = 100%.

---

## Positive Things

### P1 — llama3.1 parasomnia call-2 substantially improved

`history/2/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, levers 7–12 (second LLM call) show mechanism-based reviews:

```
"Participant flow through the residential unit is highly seasonal, peaking in summer months
 when students are on break — a scheduling challenge that erodes sample representativeness
 and complicates longitudinal analysis."
"Sensor drift across multiple nights can introduce significant artifacts, particularly in
 EEG data — a challenge not adequately addressed by current tiered acquisition model."
"Data use agreements with pharmaceutical partners may impose conflicting requirements on
 data sharing, potentially undermining the study's primary goals."
"Per-night compensation rates may not adequately account for participants' out-of-pocket
 expenses, potentially introducing selection biases."
"Staff turnover rates remain high despite initial training — a challenge not adequately
 addressed by current staff development strategies."
```

In run 52 parasomnia, levers 7–14 all used "The lever misses/overlooks/neglects..." (100% lock for call 2). In run 66, levers 7–12 (call 2) are 0% template-locked — the medical IRB example successfully broke the 2nd-call pattern for parasomnia.

### P2 — llama3.1 gta_game: calls_succeeded improved from 2 to 3

`history/2/66_identify_potential_levers/outputs.jsonl`: gta_game calls_succeeded=3.
`history/2/52_identify_potential_levers/outputs.jsonl`: gta_game calls_succeeded=2 (with `partial_recovery` event).

The 3rd LLM call now completes for gta_game in llama3.1. Combined with the run 58 haiku regression (2 partial_recovery events → now 1 error + 1 partial in run 72), the net position for calls reliability is mixed.

### P3 — No new LLMChatErrors for non-haiku models

Six of seven models (llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash) completed all 5 plans with calls_succeeded=3. This matches the before-PR rate for these six models.

### P4 — haiku parasomnia quality is high

`history/2/72_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` shows haiku producing extremely detailed, mechanism-specific, domain-grounded reviews for each lever. Examples:

- "Domestic-Clinical Balance in Physical Environment": 640-char review analyzing the specific tension between clinical safety measures and spontaneous parasomnia frequency
- "Tiered Sensing Acquisition": 500-char review citing specific false-negative rate thresholds (15–20%), costing estimates (€180K, €35–45K)
- "Recruitment Pathway Selectivity": long review naming PSA thresholds, 3-year enrollment math, and recruitment conversion rates

These reviews are grounded in the specific project context, cite mechanism chains, and name concrete constraints. No fabricated percentage claims ungrounded in the project.

### P5 — B1 fix is logically correct for identify_documents

The PR removes a stale `expected_calls=3` constant from `_run_levers` and scopes `partial_recovery` events to `identify_potential_levers` only. For identify_documents (which always returns calls_succeeded=1), this prevents spurious partial_recovery alarms. Not directly observable in this dataset (all runs are identify_potential_levers), but the fix addresses a documented bug.

---

## Comparison

### Template lock rates for llama3.1

| Plan | Before (run 52) | After (run 66) | Change |
|------|-----------------|----------------|--------|
| silo (call 1, levers 1–6) | ~0% "the options" (0/6) | 0% content (6/6 = review is just lever name) | **REGRESSION: empty reviews** |
| silo (calls 2–3, levers 7–20) | varied/domain-specific | varied/domain-specific | Maintained |
| parasomnia (call 1, levers 1–6) | "The options miss..." 6/6 = 100% | "The options miss..." 6/6 = 100% | Unchanged |
| parasomnia (call 2, levers 7–14/7–12) | "The lever misses..." 8/8 = 100% | mechanism-based 6/6 = 0% lock | **IMPROVED** |
| parasomnia (call 3, levers 13–17) | short non-template 3/3 | "[Name] lever overlooks" 5/5 = 100% | **NEW LOCK** |
| gta_game (all calls) | ~100% mixed template | **IDENTICAL output** — 100% lock | Unchanged |
| hong_kong | "plan's emphasis" 8/17 ~47% | "[Name]: weakness lever misses" 7/21 = 33% + "core tension" 5/21 = 24% | Shifted but still ~57% |

### Success rates

| Metric | Before (runs 52–58) | After (runs 66–72) | Change |
|--------|--------------------|--------------------|--------|
| status=ok for all plans | 35/35 = 100% | 34/35 = 97.1% | **REGRESSION** (-2.9pp) |
| calls_succeeded=3 for all plans | 32/35 = 91.4% | 33/35 = 94.3% | slight improvement |
| Hard errors (no output) | 0 | 1 (run 72 gta_game) | **NEW FAILURE** |
| Soft partial_recoveries | 3 (run 52 gta; run 58 silo, para) | 1 (run 72 hk) | fewer |
| haiku status=ok | 5/5 = 100% | 4/5 = 80% | **REGRESSION** |

### Lever count and field length (llama3.1 silo, runs 52 and 66)

The silo plan is the best comparator for baseline since both runs have calls_succeeded=3.

| Metric | Run 52 (before) | Run 66 (after) | Baseline train |
|--------|-----------------|----------------|---------------|
| Total levers (deduped) | 21 | 20 | varies |
| Review (levers 1–6) avg chars | ~160 (domain-specific) | ~17 (just lever name) | ~80–100 |
| Review (levers 7–20) avg chars | ~160 | ~150 | ~80–100 |
| Consequences avg chars | ~130 | ~120 | ~150–180 |

Note: Baseline hong_kong review avg is ~140 chars (including fabricated "15% higher audience engagement", "20% higher pre-sales" chains). Current llama3.1 runs avoid fabricated numbers.

### Fabricated percentage claims

| Run (model) | Plan | Fabricated % in consequences or review | Count |
|-------------|------|-----------------------------------------|-------|
| 66 (llama3.1) | silo | 0 detected | 0 |
| 66 (llama3.1) | gta_game | 0 detected (same as run 52) | 0 |
| 72 (haiku) | parasomnia | Specific numbers cited with context (€80/night, €120, €3.8M budget) — grounded in project | 0 fabricated |
| Baseline | hong_kong | "15% higher audience engagement", "20% higher pre-sales", "30% streaming revenue", "25% faster scaling" | 5+ fabricated |

Current outputs are substantially cleaner on fabricated numbers than baseline, consistent with OPTIMIZE_INSTRUCTIONS guidance.

---

## Quantitative Metrics

### Template lock counts (llama3.1 only)

| Run | Plan | Levers | "The options X" | "[Name] X" | "This lever X" | Mechanism-based | Empty reviews |
|-----|------|--------|-----------------|------------|----------------|-----------------|---------------|
| 52 | parasomnia | 17 | 6 (35%) | 8 (47%) | 0 | 3 (18%) | 0 |
| 66 | parasomnia | 17 | 6 (35%) | 5 (29%) | 0 | 6 (35%) | 0 |
| 52 | silo | 21 | 0 | 0 | 0 | 21 (100%) | 0 |
| 66 | silo | 20 | 0 | 0 | 0 | 14 (70%) | 6 (30%) |
| 52 | gta_game | 21 | 0 | 7 (33%) | 14 (67%) | 0 | 0 |
| 66 | gta_game | 21 | 0 | 7 (33%) | 14 (67%) | 0 | 0 |

Note: "[Name] X" = "[Lever Name] misses/overlooks/neglects..." and "[Lever Name] lever misses..."; "this lever X" = "The tension here is between X... this lever Y"; mechanism-based = substantive domain-specific review.

### Lever uniqueness

All runs examined produced uniquely named levers (no exact duplicate names passed through dedup). The deduplication pipeline continues to work correctly.

### Constraint violations

| Violation type | Before (all runs 52–58) | After (all runs 66–72) |
|----------------|------------------------|------------------------|
| Option count ≠ 3 | 0 | 0 |
| Missing required fields | 0 | 0 |
| Empty review (lever name only) | 0 | 6 (run 66 silo call 1) |
| LLMChatError → no output | 0 | 1 (run 72 gta_game) |

### Review length vs baseline (hong_kong)

| Source | Avg review chars | Ratio vs baseline |
|--------|-----------------|-------------------|
| Baseline train (hong_kong) | ~140 | 1.0× |
| Run 52 llama3.1 hong_kong | ~180 | ~1.3× |
| Run 66 llama3.1 hong_kong | ~230 | ~1.6× |
| Run 72 haiku parasomnia | ~550 | ~3.9× (vs para baseline) |

Haiku run 72 parasomnia reviews are ~3.9× baseline length. This exceeds the 2× warning threshold and is the likely cause of the haiku gta_game token overflow.

---

## Evidence Notes

**E1** — Run 52 gta_game and run 66 gta_game produce identical 002-10-potential_levers.json files including all lever_id UUIDs. Confirmed by direct file comparison: both begin with lever_id `ff4dc5ac-ee18-46e9-9db5-c547d1ca6231`, "Urban Planning Focus". This implies llama3.1 generates deterministic output for gta_game regardless of the prompt change (or the prompt change was insufficient to alter generation path).

**E2** — Run 72 haiku error message cites column 40173. Run 58 haiku gta_game completed successfully. Run 72 haiku parasomnia produced 17 levers with reviews averaging ~550 chars each. The jump in verbosity is the likely cause of the overflow.

**E3** — Run 58 haiku events.jsonl shows partial_recovery for silo and parasomnia with `expected_calls=3`. Run 72 haiku events.jsonl shows partial_recovery for hong_kong with `expected_calls=3`. Despite the B1 fix removing the stale constant from `_run_levers`, the expected_calls=3 value still appears in partial_recovery events for identify_potential_levers runs. This is expected since the step genuinely makes 3 calls; the B1 fix targeted identify_documents (calls_succeeded=1) not identify_potential_levers.

**E4** — Run 66 silo levers 1–6 reviews ("Resource Prioritization", "Security Protocols", etc.) are byte-for-byte identical to their lever names. The other 14 levers have substantive reviews of 100–200 chars. The 6 empty reviews come from the first LLM call; calls 2 and 3 produced normal content.

**E5** — Run 72 haiku parasomnia reviews are extremely substantive: citing specific mechanisms (IRB approval, site-initiation visits, €3.8M budget allocation, annotation throughput of 200–250 full PSG nights). These are grounded in the plan and contain no fabricated numbers. Quality is high; verbosity is the concern.

**E6** — Analysis 35 assessment documented haiku run 58 partial_recoveries (silo, parasomnia) as likely false alarms ("haiku hits min_levers=15 in 2 calls"). In run 72, the hong_kong partial_recovery (calls_succeeded=2) co-occurs with a hard gta_game failure, suggesting actual degraded performance (not a false alarm) for haiku in this run.

---

## PR Impact

### What the PR was supposed to fix

1. **B1 fix**: Scope `partial_recovery` events to `identify_potential_levers` only; stop spurious events for `identify_documents` (which always returns `calls_succeeded=1`). Remove stale `expected_calls=3` constant from `_run_levers`.
2. **Medical example**: Replace urban-planning (Section 106 heritage review) with medical domain (IRB/clinical-site sequential overhead). Three examples now span agriculture, medical, insurance — no domain overlap with test plans.

### Before vs after comparison

| Metric | Before (runs 52–58) | After (runs 66–72) | Change |
|--------|--------------------|--------------------|--------|
| status=ok rate | 35/35 = 100% | 34/35 = 97.1% | **−2.9pp** |
| Hard errors (no output) | 0 | 1 (run 72/haiku/gta_game) | **NEW** |
| Haiku ok rate | 5/5 = 100% | 4/5 = 80% | **−20pp** |
| calls_succeeded=3 rate (all models) | 32/35 = 91.4% | 33/35 = 94.3% | +2.9pp |
| Template lock (llama3.1 para call 2) | 8/8 = 100% "The lever X" | 0/6 = 0% template | **−100pp IMPROVED** |
| Template lock (llama3.1 para call 1) | 6/6 = 100% "The options miss" | 6/6 = 100% "The options miss" | Unchanged |
| Template lock (llama3.1 gta_game) | 100% (identical output) | 100% (identical output) | Unchanged |
| Empty reviews (llama3.1 silo call 1) | 0 | 6 | **NEW REGRESSION** |
| haiku verbosity (review avg chars) | ~300 (est. from run 58) | ~550 (run 72 parasomnia) | **+80% increase** |
| partial_recovery in events | 3 (run 52 gta, run 58 silo/para) | 1 (run 72 hk) + 1 error | Mix |
| Fabricated percentages | 0 (maintained from run 52) | 0 | Maintained |

### Did the PR fix the targeted issue?

**B1 fix for identify_documents**: Cannot be directly verified from this dataset (all history runs are identify_potential_levers). The code change is logically correct. The `expected_calls=3` still appears in run 72's identify_potential_levers partial_recovery event, consistent with the explanation that the identify_potential_levers code was not changed (only identify_documents was scoped out).

**Medical example**: Partially effective. The medical IRB example broke the 2nd-LLM-call template lock in llama3.1 parasomnia (100% → 0% for call 2), confirming the AGENTS.md prediction that domain-matching examples break template lock. However:
- Call 1 (levers 1–6) is unchanged — "The options miss" persists
- Call 3 (levers 13–17) developed a NEW lock: "[Lever Name] lever overlooks/neglects/misses"
- gta_game is entirely unaffected (identical output)
- haiku appears to over-generalize the medical example's verbose style

### Did the PR introduce regressions?

Yes:
1. **haiku gta_game hard failure** (run 72): A plan that succeeded in run 58 now fails with JSON EOF. Hypothesis H1: the medical example's verbose/mechanism-heavy style prompted haiku to generate review content 2–3× longer than before, causing token overflow when combined with gta_game's tendency to generate 21+ levers per dedup cycle.

2. **llama3.1 silo empty reviews** (run 66, levers 1–6): The first LLM call for silo produced reviews that are just the lever name with no review content. Run 52 silo had substantive reviews for all levers. This is a quality regression.

### Verdict: CONDITIONAL

The B1 fix is correct and should be kept. The medical example produced the intended partial improvement (parasomnia call 2 improved) but introduced a reliability concern (haiku token overflow) and a quality concern (llama3.1 silo empty reviews). The PR delivers incomplete benefit with a measured regression.

**CONDITIONAL** — keep the B1 fix unconditionally; the medical example requires follow-up work:
1. Add max_tokens protection for haiku (or a system-prompt directive limiting review length to prevent overflow).
2. Investigate and fix the llama3.1 silo first-call empty-review regression.
3. Add a 4th example from a domain that maps to game-dev (gta_game) to break the remaining 100% lock there.

---

## Questions For Later Synthesis

Q1. Is the llama3.1 silo empty-review regression (levers 1–6 having "review": "[lever name]") deterministic, or is it a stochastic event that happened in run 66? A re-run of run 66 silo would distinguish these.

Q2. Is the haiku gta_game token overflow systematic (reproducible across runs) or stochastic? If it occurs >50% of haiku gta_game runs, the medical example's verbosity effect is a real problem requiring a max_tokens fix before the medical example can be kept.

Q3. Does the "[Lever Name] lever overlooks/neglects/misses" pattern in parasomnia call 3 (run 66) also appear in other plans for llama3.1? If so, this is a new secondary lock created by the medical example rather than an incidental per-plan artifact.

Q4. Is the llama3.1 output for gta_game actually deterministic (same UUID same content) across all runs, or did run 66 happen to produce the same output? If deterministic at temperature=0, then no prompt change will break the gta_game lock for llama3.1 — a code change (temperature increase or different call strategy) would be needed instead.

Q5. The medical example's IRB/clinical-site structure is present only in the 3rd `review_lever` example. Which call uses which example for in-context learning? If all calls receive all 3 examples in the system prompt, the domain-specificity of the example should help all 3 calls. If only call 3 uses example 3, call 1 can't benefit.

---

## Reflect

The medical IRB example is doing exactly what the analysis 35 recommendation predicted: it broke the template lock for parasomnia's 2nd LLM call (which maps conceptually to the medical domain). However, the prediction from analysis 35 was also that a "poorly drafted medical or technology example could create its own domain-specific template lock" (assessment.md line 105). The run 66 evidence shows:
- Call 1 ("The options miss"): unchanged — the example had no effect on this call
- Call 2 (mechanism-based): broken ← improvement
- Call 3 ("[Lever Name] lever X"): new lock emerged

This is consistent with the structural homogeneity risk: the medical example introduced a mechanism-chain style (A requires B, B requires C, creating overhead Z), and the model learned this structure but re-applied it with the lever name as the new grammatical subject in call 3.

The haiku verbosity increase suggests an unintended consequence: the IRB example is detailed and specific (it names concrete mechanisms, timelines, and constraints), which haiku interprets as a license to generate similarly detailed review content. For a model with strong instruction-following capability and a tendency toward verbosity (haiku-4-5), this amplification creates a token overflow risk.

The gta_game lockout for llama3.1 is the most intractable problem. The output is entirely deterministic and identical to run 52 — the model generates a fixed pattern for this plan regardless of prompt changes. This suggests a game-dev example is necessary but may not be sufficient; a structural change to the call order or temperature settings may be required.

---

## Potential Code Changes

**C1 — Add max_tokens guard for haiku in identify_potential_levers**

The haiku gta_game failure at column 40173 indicates token overflow. The `_run_levers` function should specify a reduced max_tokens (e.g., 8,000–12,000) for models known to generate verbose output. Alternatively, add a `max_review_length` soft constraint in the system prompt ("Keep each lever review under 200 words").

Evidence: run 72 haiku gta_game LLMChatError (events.jsonl); run 72 haiku parasomnia review avg ~550 chars.

**C2 — Diagnose and fix llama3.1 silo first-call review failure**

The first LLM call for llama3.1 silo produced reviews that are just the lever name. This could be:
- A prompt-format issue where the model didn't understand the `review_lever` field for call 1
- A truncation issue where call 1 response was valid JSON but review fields were not populated
- A dedup/merge issue where a different call's levers were substituted with empty reviews

Reading `history/2/66_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` would reveal whether the raw output had the same problem or whether it occurred during dedup/merge.

**C3 — Add a 4th review example in game-dev / software domain**

The gta_game plan is 100% template-locked in llama3.1 regardless of the current 3 examples (agriculture, IRB, insurance). A game-dev example (e.g., "Engine middleware licensing forces a sequential integration test per partner SDK — a compounding delay that shrinks the PC launch window without reducing the total validation requirement") would give llama3.1 a structural template that maps to gta_game's domain.

**C4 — Verify temperature setting for llama3.1**

The gta_game output is byte-for-byte identical between runs 52 and 66, including all lever_id UUIDs. If llama3.1 is running at temperature=0, no prompt-only change can break the lock for this model. Consider setting temperature=0.7–1.0 for llama3.1 to allow variation between runs.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Based on analysis 35 assessment, OPTIMIZE_INSTRUCTIONS identifies:
- Optimism bias and fabricated numbers: **current outputs are clean** on this dimension
- Formulaic option triads: partially present (gta_game options still use conservative/moderate/radical structures)
- Template lock in `review_lever`: still present in parasomnia call 1 ("The options miss"), call 3 ("[Name] lever overlooks"), and gta_game
- Verbose consequence chains: run 72 haiku consequences are long but grounded in project details

New issue to add to OPTIMIZE_INSTRUCTIONS (if it is not already documented):

**Review-length explosion for strong models**: When system-prompt examples use highly specific, mechanism-dense language (IRB approval, sequential overhead, €180K equipment cost), instruction-following models (haiku, GPT-4 family) may amplify this verbosity into all reviews, causing token overflow for plans with many levers. Add to known problems: "Models with strong instruction-following may mirror example verbosity rather than example structure. Keep review examples at ≤150 words and specify maximum review length in Section 6."

---

## Summary

PR #355 delivers a partial, mixed-result improvement:

**Confirmed positive:** The medical IRB example broke the "The lever misses" template lock in llama3.1 parasomnia call 2 (100% → 0%). The B1 fix for identify_documents is logically correct and non-regressive for identify_potential_levers.

**Confirmed regressions:**
1. haiku gta_game: hard failure (status=error, no output) due to JSON EOF at ~40KB. Was successful in run 58 before the PR. Likely caused by haiku generating much longer reviews after the medical example (run 72 haiku parasomnia reviews average ~550 chars vs ~140 chars baseline).
2. llama3.1 silo: 6/20 levers (30%) have empty reviews (just the lever name) in call 1. Was not observed in run 52.

**Unchanged concerns:**
- llama3.1 gta_game: 100% template lock persists, identical output across runs 52 and 66. Game-dev domain remains uncovered.
- llama3.1 parasomnia call 1: "The options miss" lock persists (6/6 = 100%).
- llama3.1 parasomnia call 3: new "[Lever Name] lever overlooks" lock emerged (5/5 = 100%).

**Verdict: CONDITIONAL** — Keep the B1 fix. The medical example should be kept but requires two follow-up fixes before this PR represents a clear win: (1) a max_tokens guard for haiku to prevent token overflow, and (2) a game-dev/software example to close the remaining domain gap for gta_game.

Hypotheses:
- H1: Haiku gta_game token overflow is caused by the medical IRB example prompting haiku to generate 3–4× longer reviews. If confirmed, limiting example verbosity in the system prompt or adding max_tokens guards will restore haiku gta_game reliability.
- H2: The llama3.1 silo empty-review regression (call 1) is deterministic at temperature=0. A re-run at the same temperature will reproduce it. If confirmed, it points to a structural issue in how the system prompt instructs the first LLM call.
- H3: Adding a game-dev / software engineering `review_lever` example will break llama3.1 gta_game template lock (currently 100% after 2 example replacements failed to affect it). If gta_game output is truly deterministic, this hypothesis requires an increase in model temperature to test.
