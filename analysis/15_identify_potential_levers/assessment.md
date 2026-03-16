# Assessment: fix: consolidate review_lever prompt to prevent format alternation

## Issue Resolution

**PR #294 targeted**: llama3.1 (and weaker models generally) interpreted the two-bullet
`review_lever` instruction as two *alternative* formats, alternating between Controls-only and
Weakness-only levers within the same call. Because call-1 has no prior responses to fall back on
(the PR #292 partial-recovery guard cannot help), a call-1 validator rejection always means total
plan failure. The fix: consolidate the two bullets into a single combined example showing both
clauses in one field, in one sentence string.

**Is the issue resolved?**

Yes, for the specific failure mode targeted.

Direct evidence from verified output files:

- **llama3.1 silo (run 1/10)**: `history/1/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
contains 22 levers. Every `review` field is formatted as `"Controls X vs. Y. Weakness: The options fail to ..."` — e.g., `"Controls Sustainability vs. Resource Efficiency. Weakness: The options fail to consider the impact of internal politics on resource allocation."` Under
prompt_2 (run 1/02), silo failed with 7 `check_review_format` violations on call-1 and
produced 0 levers. The raw file shows 3 `strategic_rationale` entries, confirming all 3 calls
succeeded.
- **llama3.1 sovereign_identity (run 1/10)**: `events.jsonl` shows
`run_single_plan_complete` for sovereign_identity. Under prompt_2 (run 1/02), sovereign_identity
failed with 7 violations on call-1. Both plans now succeed for the first time across any
llama3.1 run.

**Residual symptoms**:

- llama3.1 parasomnia (run 1/10) failed with `ReadTimeout` after 120s. This is a timeout issue,
not a format compliance issue. Not caused by PR #294.
- gpt-5-nano parasomnia (run 1/12) produced `review_lever = 'Not applicable here'` for all 6
levers in one response, triggering a full plan failure after 357s. This is a new failure mode
(all-or-nothing cascade: one bad value kills the entire DocumentDetails response). It did not
occur under prompt_2 (gpt-5-nano was 5/5 in run 1/04). Whether prompt_3's single business-
domain example inadvertently signalled that the Controls/Weakness format is domain-specific
is unclear; only one run of gpt-5-nano was captured. See New Issues below.

---

## Quality Comparison

Models present in BOTH batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini,
gemini-2.0-flash, claude-haiku. (Run 1/09 excluded — incomplete, no outputs.)

Before = runs 1/02–1/08 (prompt_2, analysis/14).
After  = runs 1/10–1/16 (prompt_3, analysis/15, excluding 1/09).

Notes on measurement: (a) "Chain violations" means missing or incomplete `Immediate → Systemic → Strategic` arrow-chain in `consequences`; analysis/14 codex measured only label
*presence* while analysis/15 codex required `→` arrow separators — numbers may not be directly
comparable. (b) "Exact review compliance" was not tracked in analysis/14; analysis/15 codex
introduces it with a strict regex.


| Metric                                                              | Before (runs 1/02–1/08)                   | After (runs 1/10–1/16)                                                                                                                           | Verdict                                                            |
| ------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Overall success rate**                                            | 32/35 (91.4%)                             | 32/35 (91.4%)                                                                                                                                    | UNCHANGED (net 0)                                                  |
| **llama3.1 success**                                                | 3/5                                       | 4/5                                                                                                                                              | IMPROVED (+1: silo + sovereign_identity fixed)                     |
| **gpt-5-nano success**                                              | 5/5                                       | 4/5                                                                                                                                              | REGRESSED (−1: parasomnia `review_lever = 'Not applicable here'`)  |
| **gpt-oss-20b success**                                             | 4/5                                       | 4/5                                                                                                                                              | UNCHANGED (hong_kong_game JSON fails both runs)                    |
| **qwen3-30b success**                                               | 5/5                                       | 5/5                                                                                                                                              | UNCHANGED                                                          |
| **gpt-4o-mini success**                                             | 5/5                                       | 5/5                                                                                                                                              | UNCHANGED                                                          |
| **gemini-2.0-flash success**                                        | 5/5                                       | 5/5                                                                                                                                              | UNCHANGED                                                          |
| **claude-haiku success**                                            | 5/5                                       | 5/5                                                                                                                                              | UNCHANGED                                                          |
| **Bracket placeholder leakage**                                     | 6/568 (1.1%)                              | ~6 (run 1/12 hong_kong_game); others 0                                                                                                           | UNCHANGED (~1.1%)                                                  |
| **Option count violations**                                         | 0                                         | 0                                                                                                                                                | UNCHANGED                                                          |
| **Lever name uniqueness (final merged)**                            | 568/568 (100%)                            | ~100% (dedup handles raw cross-call dups: run 10 had 12 raw dups)                                                                                | UNCHANGED                                                          |
| **Template leakage (Conservative:/Moderate:/Radical: prefixes)**    | 0/568 (0%)                                | 0                                                                                                                                                | UNCHANGED                                                          |
| **Label-style options (Title: description)**                        | ~0                                        | 15 in run 1/13 (qwen3 silo), 6 in run 1/16 (haiku)                                                                                               | REGRESSED (qwen3 silo prominent)                                   |
| **Review format compliance (validator pass in successful outputs)** | 100% (0 violations in 32 plans)           | 100% (0 violations in 32 successful plans)                                                                                                       | UNCHANGED                                                          |
| **Exact review compliance (strict regex, raw responses)**           | Not measured                              | Highly variable: llama3.1 87/87 (100%), gpt-4o-mini 58/89 (65%), gpt-oss-20b 53/62 (85%), haiku 0/77 (0%), qwen3 15/85 (18%), gemini 17/90 (19%) | NEW METRIC — llama3.1 best; haiku worst                            |
| **Consequence chain format (arrow-chain violations)**               | 0/568 (0%) by label-presence check        | 92 violations in runs 1/11, 1/12, 1/16 (gpt-oss-20b: 18; gpt-5-nano: 18; haiku: 56)                                                              | REGRESSED (but see measurement note above — may be stricter check) |
| **Content depth (avg option chars)**                                | 132.7                                     | Varies: llama3.1 75.88, qwen3 70.60, gpt-oss-20b 79.20, gpt-5-nano 115.70, gpt-4o-mini 109.68, gemini 128.46, haiku 286.38                       | MIXED (most models lower; haiku 2× higher)                         |
| **qwen3 consequences contamination**                                | ~67% of qwen3 levers                      | ~33% in sampled plan (silo run 1/13) — 5/15 levers                                                                                               | SLIGHTLY IMPROVED (small sample)                                   |
| **Cross-call duplication (raw)**                                    | 0 cross-call duplicate names              | Run 1/10 llama3.1: 12 raw dups; others: 0–1                                                                                                      | SLIGHTLY REGRESSED (llama3.1 only)                                 |
| **Over-generation (>7 levers/call)**                                | haiku avg 21.0/plan (3 calls × ~7)        | Run 1/10 llama3.1: avg 7.25/response (3/12 responses out of 5–7 range); haiku run 1/16: 7.0/response                                             | UNCHANGED (informational; downstream dedup handles it)             |
| **Partial successful outputs (< 3 LLM calls in raw file)**          | 2 (gta_game: 7 lvrs; parasomnia: 12 lvrs) | 0 confirmed (no partial recovery triggered in runs 1/10–1/16)                                                                                    | UNCHANGED (design feature present but not activated)               |


---

## New Issues

### NI1 — gpt-5-nano produced `review_lever = 'Not applicable here'` for all levers on a scientific plan

Run 1/12 (gpt-5-nano, parasomnia): all 6 levers in the failed response had `review_lever = 'Not applicable here'`, triggering the all-or-nothing Pydantic validation cascade after 357s
of compute. The model could not map `"Controls [Tension A] vs. [Tension B]"` to a
medical/research protocol domain.

Under prompt_2 (run 1/04), gpt-5-nano was 5/5. Under prompt_3, it is 4/5. The consolidated
business-domain example in prompt_3 may have inadvertently reinforced the idea that the
Controls/Weakness template only applies to organizational/strategic tensions, not
scientific/research tensions. Only one run was captured — this needs more data before
attributing causation to the prompt change vs. random variance.

**Immediate impact**: This failure confirms the all-or-nothing cascade (code_claude B4;
code_codex S2/I3) is still active. One bad lever value in a single response discards all
levers from that call. The per-lever salvage architecture (synthesis Direction 1) would have
preserved any well-formed levers in that batch.

### NI2 — haiku verbosity explosion under prompt_3

Run 1/16 (haiku): average consequence length 857.34 chars, review length 318.40 chars, and 56
chain violations in final output. Under prompt_2 (run 1/08), haiku had 0 chain violations and
avg 21.4 levers/plan with acceptable length. The more explicit combined example in prompt_3
appears to have triggered highly elaborate freeform output from haiku, departing from the
structured `Immediate → Systemic → Strategic` chain format.

This is a quality regression for haiku specifically, though haiku remains 5/5 on success rate.

### NI3 — Exact review compliance gap exposed (new metric, not previously tracked)

The analysis/15 insight_codex introduced strict-regex exact review compliance tracking. Most
models pass the weak validator (`'Controls '` + `'Weakness:'` present) while failing the strict
two-sentence format: haiku 0/77 (0%), qwen3 15/85 (18%), gemini 17/90 (19%), gpt-4o-mini 58/89
(65%). This gap existed before (the validator has always been weak — code_claude S2 in
analysis/14) but is now measured. llama3.1 achieves perfect exact compliance (87/87) under
prompt_3, confirming the fix worked for the target model, while other models continue to drift
on punctuation and wording.

### NI4 — gpt-oss-20b JSON failure converging on hong_kong_game (not new, now confirmed recurring)

Runs 1/03 (analysis/14) and 1/11 (analysis/15) both fail on hong_kong_game with the same
`ValueError('Could not extract json string from output: ')`. Two consecutive gpt-oss-20b runs
have now failed on the same plan, suggesting this is a plan-specific context-length issue, not
random rotation. The analysis/14 assessment noted it was rotating (sovereign_identity →
parasomnia → hong_kong_game); now hong_kong_game has appeared twice in a row.

---

## Verdict

**YES**: PR #294 successfully fixes the targeted issue — llama3.1's silo and sovereign_identity
plans now succeed for the first time, with correctly formatted review_lever fields in all 22
levers. The net success rate is maintained (32/35 = 91.4%), the gpt-5-nano parasomnia failure
needs investigation but cannot be definitively attributed to the prompt change from a single run,
and no other model regressed.

---

## Recommended Next Change

**Proposal**: Change `break` to `continue` at `identify_potential_levers.py:278` so that a
call-2 failure no longer suppresses call-3. When call-2 fails after call-1 succeeded, the loop
currently exits immediately, preventing call-3 from running. A `continue` would preserve call-1's
results AND attempt call-3, potentially doubling the lever output for partial-recovery scenarios.

**Evidence**: Cross-agent consensus across all four analysis files (insight_claude C1, code_claude
B1/I1, code_codex B1/I1). Source code confirmed: line 278 is unconditional `break` inside
`if len(responses) == 0: raise; else: logger.warning; break`. The impact is documented: llama3.1
gta_game in run 1/02 produced 7 levers from call-1 only, while call-3 never ran; a `continue`
would have attempted call-3 and potentially yielded 12–14 levers. All agents rate this as trivial
effort (one character) and zero regression risk.

**Verify**: After the fix, run llama3.1 or any model that triggers partial recovery. Check:

- `002-9-potential_levers_raw.json` should show 2 `"strategic_rationale"` entries (from calls 1
and 3) instead of 1, when call-2 fails.
- Final lever count should approach 12–14 for a partial-recovery plan instead of 7.
- Confirm no regression for models that complete all 3 calls cleanly: their raw files should
still show 3 entries, and final output should be unchanged.
- Check that the call-3 denylist (missing call-2 names) does not cause significant duplicate
lever production downstream; `DeduplicateLeversTask` should handle any near-duplicates.
- Monitor gpt-5-nano parasomnia across 2–3 additional runs to determine whether the `'Not applicable here'` failure is prompt_3-induced or random variance. If it recurs consistently,
a domain-specific worked example is needed (synthesis Direction 4).
- Watch haiku's consequence length under any future prompt changes — the verbosity regression
(857 chars avg vs. prior 400 chars) needs to be stable or improving.

**Risks**:

- When call-2 fails due to a structural format issue (e.g., the model systematically alternates
formats), call-3 will likely fail for the same reason, wasting one additional LLM call. This is
acceptable — the partial recovery guard will still preserve call-1's results and the `continue`
falls through cleanly.
- Call-3 will not have call-2's lever names in its denylist, so weak models may produce some
near-duplicate names. `DeduplicateLeversTask` handles exact duplicates; semantic duplicates are
accepted as the dedup step's responsibility.
- For models with 120s timeouts (llama3.1), allowing call-3 to run after a call-2 failure
extends total plan latency. On the parasomnia plan (which already times out for llama3.1),
this could cause a second timeout.

**Prerequisites**: PR #292 (partial-recovery guard) must be in place. It is. No other
dependencies.

---

## Backlog

### Resolved by PR #294 (remove from backlog):

- **Two-bullet `review_lever` instruction** (was top priority from analysis/14): The consolidated
combined example in prompt_3 fixed llama3.1's alternating Controls-only / Weakness-only pattern
for silo and sovereign_identity. Confirmed by run 1/10 direct output inspection.

### Still open (carried forward from analysis/14):

- `**break` → `continue` in call-2/3 failure handler** (NI2 in analysis/14, now synthesis
Direction 2): Highest-leverage code fix. One character change at line 278. Do in next PR.
- **Partial-recovery telemetry** (NI1 in analysis/14): Emit a structured event to `events.jsonl`
when partial recovery fires. Low effort; makes audit machine-readable instead of requiring raw
file inspection.
- **qwen3 consequence contamination repair validator**: ~33% of levers in sampled run (was ~67%
before; may have improved slightly or may reflect sample variance). Post-parse `@field_validator`
on `consequences` that strips trailing `"Controls … Weakness: …"` text. Medium effort, no
cascade risk (repair, not reject).
- `**activity_overview.json` inflation under parallel workers** (NI3 in analysis/14): One-line
guard in `track_activity.py:207`. Corrects per-plan cost metrics for all workers > 1 runs.
- **gpt-oss-20b hong_kong_game JSON failure**: Confirmed recurring across runs 1/03 and 1/11.
Two consecutive failures on the same plan suggests plan-specific context-length sensitivity.
Fix: prompt-length budgeting or pre-summary truncation before sending to weaker models.
- **Per-lever non-fatal validation (all-or-nothing cascade)**: One malformed lever discards the
entire LLM response (confirmed: gpt-5-nano parasomnia run 1/12, 357s wasted). Replace
`DocumentDetails` whole-response rejection with per-lever validation that filters bad levers
and keeps good ones. Medium effort; do after `break` → `continue` lands.
- **Remove bracket placeholders from Pydantic field descriptions**: `[Tension A]`, `[Tension B]`,
`[specific factor]` in `description=` strings are copyable by models (confirmed: run 1/12
hong_kong_game). Replace with concrete non-bracketed examples.

### New items added by analysis/15:

- **gpt-5-nano domain-specific `review_lever` failure**: `'Not applicable here'` on parasomnia
(run 1/12). Run more gpt-5-nano experiments (2–3 runs) to determine if this is random variance
or systematic. If systematic: add a research/scientific worked example to the `review_lever`
instruction (synthesis Direction 4).
- **haiku verbosity regression under prompt_3**: 857 chars avg consequence vs. 400 before; 56
chain violations (0 before). Monitor in future runs. If persistent, consider an explicit
consequence length cap in the prompt (e.g., "consequences must be under 300 characters") or
in a post-parse truncation step.
- **Exact review compliance gap (strict regex)**: haiku 0/77 (0%), qwen3 15/85 (18%), gemini
17/90 (19%) in raw responses despite passing the weak validator. Two options: (a) post-parse
canonicalizer that normalizes near-miss reviews into the exact two-sentence format (synthesis
Direction 5, medium effort/risk); (b) strengthen `check_review_format` to include `' vs. '`
check (low effort, do after per-lever salvage is in place so tightening doesn't cause new cascades).
- **llama3.1 parasomnia ReadTimeout**: 120s timeout is too short. Consider a plan-adaptive
timeout or configurable per-model timeout. Low priority but easy to fix.

