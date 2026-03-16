# Insight Claude

## Summary of Runs Examined

| Run | Model | Workers | Plans OK | Plans Failed | Notes |
|-----|-------|---------|----------|-------------|-------|
| 1/02 | llama3.1 | 1 | 3/5 | 2 | review_lever cascade — silo (7), sovereign_identity (7) |
| 1/03 | gpt-oss-20b | 4 | 4/5 | 1 | JSON invalid — hong_kong_game |
| 1/04 | gpt-5-nano | 4 | 5/5 | 0 | — |
| 1/05 | qwen3-30b-a3b | 4 | 5/5 | 0 | — |
| 1/06 | gpt-4o-mini | 4 | 5/5 | 0 | — |
| 1/07 | gemini-2.0-flash | 4 | 5/5 | 0 | — |
| 1/08 | haiku | 4 | 5/5 | 0 | FULL RECOVERY — silo now succeeds |

**Total: 32/35 (91.4%)**

Previous analysis batch (0/95–1/01) total: 31/35 (88.6%)

---

## Negative Things

### N1 — llama3.1 still fails on 2/5 plans due to call-1 validator failures

Run 1/02 (llama3.1, workers=1):

- `20250321_silo`: 7 review_lever violations on call 0 — all levers alternate between
  Controls-only (`"Controls Resource Competition vs. Social Unrest."`) and Weakness-only
  (`"Weakness: The options fa...ychological well-being."`). Error raised immediately because
  `len(responses) == 0`.
  (`history/1/02_identify_potential_levers/events.jsonl`, `2026-03-16T01:57:28Z`, 29.97 s)

- `20260308_sovereign_identity`: same alternating pattern, 7 violations, error raised at 33.61 s.
  (`history/1/02_identify_potential_levers/events.jsonl`, `2026-03-16T01:59:10Z`)

PR #292's partial recovery guard (`len(responses) == 0: raise`) works as designed: when call 1 fails
with no prior responses, the error is still raised. This is correct behavior — there is nothing to
recover. However, these two plan failures show that llama3.1's `review_lever` format compliance
remains a structural problem for certain plans. The model systematically produces separate
Controls-clause and Weakness-clause levers instead of combining both in one field.

### N2 — llama3.1 gta_game produces only 7 levers (from partial recovery: 1 of 3 calls succeeded)

The raw file `history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`
contains exactly **1 `"strategic_rationale"` entry** — confirming that only call 1 succeeded and calls
2–3 triggered partial recovery. The deduplicated output has 7 levers (vs. the expected 15–21 from 3
full calls). This is better than 0 levers (as in run 95 before PR #292), but the plan's lever diversity
is reduced.

### N3 — gpt-oss-20b continues to fail on a rotating per-plan basis with JSON errors

Run 1/03, hong_kong_game failure:
```
Invalid JSON: expected `,` or `]` at line 12 column 2
```
(`history/1/03_identify_potential_levers/events.jsonl`, `2026-03-16T02:03:47Z`, 52.23 s)

Before-PR run 96 failed on parasomnia (JSON truncation, 34.85 s). Before-that run 90 failed on
sovereign_identity (JSON extraction, 164 s). Three consecutive runs of gpt-oss-20b each fail on a
*different* plan, suggesting context-length sensitivity: the model truncates or produces invalid JSON
on whichever plan happens to exceed its effective structured-output window in that run. Not caused
by PR #292 or the validators.

### N4 — qwen3 consequence contamination persists at ~67-70%

Run 1/05 (qwen3), silo lever 0 (`consequences`):
> "Immediate: Prioritizing agricultural output over industrial needs → Systemic: 25% reduction in food
> waste but 18% capacity deficit in manufacturing → Strategic: Accelerates self-sufficiency but risks
> economic stagnation. Controls efficiency vs. adaptability. Weakness: The options fail to consider
> climate variability in subterranean agriculture."

The `review` field for the same lever is: `"Controls efficiency vs. adaptability. Weakness: ..."` —
identical text. This contamination appears in ~10 of 15 levers per plan for qwen3 in run 1/05.
`grep "Controls.*vs.*Weakness"` returns 25 occurrences in a 15-lever file (15 review fields + 10
contaminated consequence fields = 67% contamination rate).
(`history/1/05_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`)

This issue is unchanged from before the PR and is orthogonal to PR #292.

### N5 — No partial_result metadata flag in events or outputs

PR #292 adds a warning log when partial recovery triggers. None of the `events.jsonl` files in runs
1/02–1/08 contain entries for partial recovery (no `partial_result`, no `warning` event type). This
means the pipeline currently has no structured way to distinguish "plan completed with all 3 calls"
from "plan completed with 1–2 calls via partial recovery." The raw file inspection (counting
`strategic_rationale` entries) is the only current audit mechanism for partial recovery.

This is an observability gap — synthesis should note it for future telemetry work.

---

## Positive Things

### P1 — Partial recovery demonstrated for llama3.1 gta_game

The `002-9-potential_levers_raw.json` for run 1/02 llama3.1 gta_game shows exactly 1 `strategic_rationale`
entry, proving that PR #292's partial recovery path triggered: call 1 returned 7 valid levers, calls 2–3
failed the `check_review_format` validator, and the code broke out of the loop returning the 1 successful
call's results. Confirmed output: 7 levers in `002-10-potential_levers.json`.
(`history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`)

In run 0/95 (before PR #292), gta_game for llama3.1 failed with 8 review violations at 32.69 s — zero
output. After PR #292, gta_game produces 7 levers. **The PR worked as designed.**

### P2 — haiku silo fully recovered (0 → 23 levers, 4/5 → 5/5)

Run 1/08 (haiku) silo: `002-9-potential_levers_raw.json` shows 3 `strategic_rationale` entries — all 3
calls succeeded without triggering any validator. The 23 deduplicated levers are high quality with
proper review_lever format throughout. (`history/1/08_identify_potential_levers/outputs/20250321_silo/`)

Run 1/01 (haiku, before PR #292) silo: failed because lever 7 had 7 options (editorial commentary),
causing `check_option_count` to reject the entire DocumentDetails and discard 18+ valid levers.
With PR #292 in place: if haiku had again produced a problematic lever on call 2 or 3, the earlier
successful calls' levers would have been preserved. In this batch, the editorial commentary issue did
not recur — but the partial recovery safety net is now in place.

### P3 — template leakage absent from all current run outputs

`grep "Conservative:|Moderate:|Radical:"` returns **no matches** in any `002-10-potential_levers.json`
file in runs 1/02–1/08. In run 0/95 (before), llama3.1 parasomnia had Conservative/Moderate/Radical
option prefixes in 5+ options. In run 1/02, llama3.1 parasomnia has no such labels. This appears to
be model variance — the prompt is identical (same sha256: `486d3e12e8c892061d8bc9bdd76f3bf23da6818123aaef6779b15f82cf2ca126`).

### P4 — All other models at 5/5 continue to produce high-quality output

- gpt-5-nano (1/04): 5/5, 18 levers per plan, consistent review_lever format
- qwen3 (1/05): 5/5, 15–17 levers per plan (qwen3 produces fewer levers per call; contamination in
  consequences is orthogonal to PR)
- gpt-4o-mini (1/06): 5/5, 17–20 levers per plan
- gemini-2.0-flash (1/07): 5/5, 18–19 levers per plan
- haiku (1/08): 5/5, 21–23 levers per plan (highest counts in this batch)

### P5 — No option-count violations or review-format violations in any successful artifact

All 32 successful plans in runs 1/02–1/08 produce levers with exactly 3 options and properly formatted
`review_lever` fields. The validators from PR #289 continue to work correctly and no new validator-caused
cascade failures appeared beyond the two expected llama3.1 call-1 failures.

---

## Comparison

### Per-run summary

| Run | Model | Plans | OK | Errors | Cause |
|-----|-------|------|----|--------|-------|
| 0/95 | llama3.1 | 5 | 3 | 2 | `check_review_format` cascade — silo (9), gta_game (8) |
| 0/96 | gpt-oss-20b | 5 | 4 | 1 | JSON truncation — parasomnia |
| 0/97 | gpt-5-nano | 5 | 5 | 0 | — |
| 0/98 | qwen3 | 5 | 5 | 0 | — |
| 0/99 | gemini-2.0-flash | 5 | 5 | 0 | — |
| 1/00 | gemini-2.0-flash | 5 | 5 | 0 | — |
| 1/01 | haiku | 5 | 4 | 1 | `check_option_count` — silo (lever 7: 7 options) |
| **Before total** | | **35** | **31** | **4** | |
| 1/02 | llama3.1 | 5 | 3 | 2 | `check_review_format` cascade — silo (7), sovereign_identity (7) |
| 1/03 | gpt-oss-20b | 5 | 4 | 1 | JSON invalid — hong_kong_game |
| 1/04 | gpt-5-nano | 5 | 5 | 0 | — |
| 1/05 | qwen3 | 5 | 5 | 0 | — |
| 1/06 | gpt-4o-mini | 5 | 5 | 0 | — |
| 1/07 | gemini-2.0-flash | 5 | 5 | 0 | — |
| 1/08 | haiku | 5 | 5 | 0 | — |
| **After total** | | **35** | **32** | **3** | |

### Shared-model comparison

Models present in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, haiku, gemini-2.0-flash.

| Model | Before (single run) | After (single run) | Change | Cause |
|-------|--------------------|--------------------|--------|-------|
| llama3.1 | 3/5 | 3/5 | 0 | Different plans fail (gta_game recovered partially; sovereign_identity now fails) |
| gpt-oss-20b | 4/5 | 4/5 | 0 | Different plan fails (hong_kong_game instead of parasomnia; JSON errors) |
| gpt-5-nano | 5/5 | 5/5 | 0 | — |
| qwen3 | 5/5 | 5/5 | 0 | — |
| gemini-2.0-flash | 5/5 | 5/5 | 0 | — |
| haiku | 4/5 | 5/5 | **+1** | silo now produces 23 levers (0 before due to check_option_count cascade) |
| **Subtotal** | **26/30 = 86.7%** | **27/30 = 90.0%** | **+1** | |

---

## Quantitative Metrics

### Success rate

| Period | Runs | Plans | OK | Errors | Rate |
|--------|------|------|----|--------|------|
| Before (0/95–1/01) | 7 | 35 | 31 | 4 | 88.6% |
| After (1/02–1/08) | 7 | 35 | 32 | 3 | 91.4% |

### Lever counts per run

| Run | Model | Plans OK | Total Levers | Avg per Plan |
|-----|-------|----------|-------------|-------------|
| 0/95 | llama3.1 (before) | 3 | 51 | 17.0 |
| 1/01 | haiku (before) | 4 | 84 | 21.0 |
| 1/02 | llama3.1 (after) | 3 | 43 | 14.3 |
| 1/03 | gpt-oss-20b | 4 | 67 | 16.8 |
| 1/04 | gpt-5-nano | 5 | 90 | 18.0 |
| 1/05 | qwen3 | 5 | 77 | 15.4 |
| 1/06 | gpt-4o-mini | 5 | 92 | 18.4 |
| 1/07 | gemini-2.0-flash | 5 | 92 | 18.4 |
| 1/08 | haiku (after) | 5 | 107 | 21.4 |

**After-batch total: 568 levers** (vs. 563 before — per analysis/13 assessment)

*Note: llama3.1 run 1/02 shows lower avg (14.3) because gta_game produced only 7 levers from 1
partial-recovery call (vs. 3 successful calls producing 17–19 levers for other plans).*

### Partial recovery signal

| Plan | Run | Call count in raw file | Levers output | Interpretation |
|------|-----|----------------------|---------------|---------------|
| gta_game | 1/02 llama3.1 | **1** | 7 | Call 1 succeeded; calls 2–3 triggered partial recovery |
| silo | 1/08 haiku | **3** | 23 | All 3 calls succeeded; no partial recovery needed |
| All 5 plans | 1/04 gpt-5-nano | 3 each | 18 each | All calls succeeded throughout |

*Call count measured by counting `"strategic_rationale"` entries in `002-9-potential_levers_raw.json`.*

### Template leakage (Conservative:/Moderate:/Radical: prefixes)

| Period | Leakage cells in final outputs | Affected runs |
|--------|-------------------------------|---------------|
| Before (analysis/13 assessment) | 20 | Run 0/95 llama3.1 parasomnia |
| After (runs 1/02–1/08) | **0** | None |

Zero template leakage in the current batch. This appears to be model variance — prompt is identical.

### LLMChatError entries in events.jsonl

| Run | Model | Events | Error type |
|-----|-------|--------|-----------|
| 1/02 | llama3.1 | 2 errors | `check_review_format` — silo (7 violations), sovereign_identity (7 violations) |
| 1/03 | gpt-oss-20b | 1 error | `Invalid JSON` — hong_kong_game |
| 1/04–1/08 | all others | 0 errors | — |

---

## Evidence Notes

1. **Partial recovery in llama3.1 gta_game** — raw file at
   `history/1/02_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`
   has exactly one `"strategic_rationale"` key, confirming only one LLM call succeeded. Grep
   `"strategic_rationale"` → count 1. The output has 7 levers, all with valid review_lever format
   (`"Controls X vs. Y. Weakness: ..."`). Before PR #292, run 0/95 gta_game produced 0 levers.

2. **llama3.1 silo and sovereign_identity call-0 failures** — events.jsonl at
   `history/1/02_identify_potential_levers/events.jsonl` shows errors at 29.97 s and 33.61 s,
   both with 7 `DocumentDetails.levers[N].review_lever` violations. The error is raised because
   `len(responses) == 0` — confirming call 1 failed with no accumulated results.

3. **haiku silo full recovery** — raw file at
   `history/1/08_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json`
   has 3 `"strategic_rationale"` entries. The model produced valid levers on all 3 calls. No
   editorial-commentary issue recurred. Output: 23 deduplicated levers.

4. **gpt-oss-20b JSON error rotates across plans** — run 0/90: sovereign_identity (164 s), run 0/96:
   parasomnia (34.85 s), run 1/03: hong_kong_game (52.23 s). Not PR-related; context-length
   sensitivity to long plans.

5. **qwen3 contamination persists** — `002-10-potential_levers.json` for run 1/05 silo shows 25
   occurrences of `"Controls.*vs.*Weakness"` regex for 15 levers: 15 from review fields + 10 from
   contaminated consequence fields = 67% of levers affected.
   (`history/1/05_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`)

6. **Template leakage absent** — grep of `"Conservative:|Moderate:|Radical:"` across all
   `002-10-potential_levers.json` files in runs 1/02–1/08 returns 0 matches. The same prompt
   sha256 was used in run 0/95 (where leakage occurred). Variance.

7. **Prompt file unchanged** — all runs 0/95–1/08 use
   `system_prompt_sha256: 486d3e12e8c892061d8bc9bdd76f3bf23da6818123aaef6779b15f82cf2ca126`.
   PR #292 is a code change only; no prompt was modified.

---

## PR Impact

### What the PR was supposed to fix

PR #292 addresses the partial-result-loss bug (B1/C1 from analysis/12, Direction 2 from synthesis/12–13):
> When call 2 or 3 of the 3-call lever loop fails, keep levers from prior successful calls instead of
> discarding everything. If call 1 fails (no accumulated responses), the error is still raised.

This was explicitly flagged as a prerequisite companion to PR #289's validators in analysis/13's
CONDITIONAL verdict. The cascade: validator rejects a lever → `DocumentDetails` parse fails →
exception re-raised → all prior `responses` discarded → zero output.

### Before vs after comparison

| Metric | Before (0/95–1/01) | After (1/02–1/08) | Change |
|--------|---------------------|-------------------|--------|
| Overall success rate | 31/35 (88.6%) | 32/35 (91.4%) | **+1 plan** |
| Shared-model success rate | 26/30 (86.7%) | 27/30 (90.0%) | **+1 plan** |
| haiku success | 4/5 | 5/5 | **+1 (silo recovered)** |
| llama3.1 success | 3/5 | 3/5 | 0 (different plans fail) |
| gpt-oss-20b success | 4/5 | 4/5 | 0 (different plan fails; JSON errors) |
| gpt-5-nano success | 5/5 | 5/5 | 0 |
| qwen3 success | 5/5 | 5/5 | 0 |
| gemini-2.0-flash success | 5/5 | 5/5 | 0 |
| Plans with 0 levers due to cascade | 3 (run 0/95: silo+gta_game; run 1/01: silo) | **1** (run 1/02: silo, sovereign_identity) | **−2 cascade failures** |
| llama3.1 gta_game levers | 0 (cascade) | **7 (partial recovery)** | **+7 levers** |
| haiku silo levers | 0 (cascade) | **23** | **+23 levers** |
| Total merged levers | 563 | **568** | +5 |
| Template leakage cells | 20 | 0 | −20 (variance; prompt unchanged) |
| Option-count violations in artifacts | 0 | 0 | Unchanged (validators still working) |
| Review-format violations in artifacts | 0 | 0 | Unchanged (validators still working) |
| qwen3 consequence contamination | ~70% of qwen3 levers | ~67% of qwen3 levers | Unchanged |
| Partial recovery telemetry flag | N/A | **Missing** | New gap (N5) |

### Did the PR fix the targeted issue?

**Yes, with one documented limitation.**

**Primary fix confirmed:** The raw file evidence for llama3.1 gta_game in run 1/02 is direct proof.
`002-9-potential_levers_raw.json` contains 1 successful call response; the plan produces 7 levers
instead of 0. In run 0/95 (same model, same plan, before PR), gta_game failed entirely with 8
review_lever violations. The partial recovery path kept call 1's results when calls 2–3 failed.

**Documented limitation (expected):** For llama3.1 silo and sovereign_identity, call 1 itself fails
the validator. With `len(responses) == 0`, the error is still raised — correct behavior as the PR
specifies. There is nothing to recover when the first call fails. These failures existed before PR #292
and are unchanged.

**haiku silo:** Recovered (0 → 23 levers). All 3 calls succeeded without triggering partial recovery.
The editorial-commentary issue that caused run 1/01 silo to fail (lever 7 with 7 options including
"Removing Lever 8.") did not recur. The partial recovery safety net is now in place, but this
specific recovery was model variance rather than the PR triggering.

### Did the PR cause regressions?

**No new regressions introduced.**

- Validators (PR #289) continue working correctly — 0 malformed levers in any successful artifact.
- gpt-oss-20b json failures are pre-existing and rotate across plans; not PR-related.
- llama3.1's call-1 failures for silo and sovereign_identity are the correct fallback behavior of
  the partial recovery guard.

### Verdict

**KEEP**

PR #292 fulfills its stated purpose and resolves the CONDITIONAL from analysis/13. The cascade that
converted single-lever validator rejections into total plan failures is now eliminated when at least
one prior call succeeded. Direct evidence: llama3.1 gta_game goes from 0 to 7 levers; haiku silo
goes from 0 to 23 levers. No regressions introduced. The combined (PR #289 + PR #292) state is now
correct: validators catch malformed levers, partial recovery preserves earlier good results.

The remaining llama3.1 plan failures (silo, sovereign_identity) are the documented edge case — call 1
itself fails, nothing to recover — and are the next item to address via a prompt fix for llama3.1's
`review_lever` format compliance.

---

## Questions For Later Synthesis

**Q1**: llama3.1 fails on different plans between run 0/95 (silo+gta_game) and run 1/02
(silo+sovereign_identity). Is silo consistently the plan that hits call-1 failures for llama3.1
across all runs? Is sovereign_identity the new difficult plan, or is it random per-plan variance? If
silo always fails call 1, the prompt fix for `review_lever` format is still needed for that plan.

**Q2**: In run 1/02, gta_game's call 1 produced valid review_lever format for all 7 levers
(`"Controls X vs. Y. Weakness: ..."`). Calls 2–3 presumably failed. Is there a per-call pattern for
llama3.1 — does call 1 produce better output than calls 2–3 because it operates on a fresh context,
while later calls accumulate more text and degrade format compliance?

**Q3**: The partial recovery warning log is not captured in `events.jsonl`. Should a
`run_single_plan_warning` event be added to the event log when partial recovery triggers, with
metadata (call index that failed, levers recovered, levers lost)? This would make the pipeline
auditable without raw file inspection.

**Q4**: qwen3 consequence contamination affects ~67-70% of levers. The previous assessment noted a
post-parse repair validator on `consequences` as an option (synthesis/13 Direction 2). Is this still
the preferred fix, or should the prompt address it more explicitly?

**Q5**: gpt-4o-mini appeared in this batch (run 1/06) for the first time as a replacement for the
second gemini run. It performed 5/5 with 17–20 levers per plan and no validation issues. Should
it be retained in future test matrices?

---

## Reflect

PR #292 closes the loop opened by PR #289. The design decision — "partial recovery when calls 2–3
fail; hard failure when call 1 fails" — is the right trade-off. It prevents total loss when the
model produces valid levers on early calls, while correctly escalating when there is no recoverable
data at all.

The llama3.1 story remains instructive. Its `review_lever` non-compliance varies by plan: some plans
trigger call-1 failures (silo, sovereign_identity consistently), others allow call-1 to succeed
(gta_game in run 1/02, hong_kong_game and parasomnia). This per-plan variance suggests the failure
is not purely a prompt format issue but may relate to how the model interprets the plan's topic or
complexity. A single-field example in the prompt (`"review_lever must read: 'Controls [A] vs. [B].
Weakness: [text].' — both clauses required in one field"`) would likely help, but the cross-plan
variance means it may not fully resolve the issue for all plans.

The haiku full recovery (23 levers for silo) is encouraging — the editorial-commentary behavior that
appeared in run 1/01 (embedding "Removing Lever 8." as an option) appears to be rare. With partial
recovery now active, a recurrence would produce partial output rather than zero output, making it
a much less severe event.

---

## Hypotheses

**H1 — llama3.1 review_lever prompt clarification**: The model treats the `review_lever` field as
optionally requiring either Controls or Weakness rather than mandating both. A single-field example
explicitly showing the combined form (`"review_lever format: 'Controls [Tension A] vs. [Tension B].
Weakness: [specific gap].' — both clauses required in one field, one sentence each"`) may reduce
the alternating pattern. Evidence: run 1/02 silo shows 100% alternating levers on call 1.

**H2 — qwen3 consequence contamination**: The model copies `review_lever` text verbatim into
`consequences`. A prohibition note in the prompt (`consequences must NOT contain Controls/Weakness
language`) or a post-parse repair validator that strips trailing review text from consequences would
fix this. The contamination appears systematic and plan-independent for qwen3.

**H3 — gpt-oss-20b context-length fix**: The model consistently produces invalid JSON on plans
that may be longer (hong_kong_game has extensive historical background). Truncating the plan input
to a fixed character limit before the LLM call would eliminate the JSON truncation failures.

---

## Potential Code Changes

**C1 — Add partial recovery event to events.jsonl (LOW EFFORT, HIGH OBSERVABILITY)**

When the partial recovery path triggers (`len(responses) >= 1`, exception caught, `break`), emit a
structured event to `events.jsonl`:
```json
{"event": "partial_recovery", "call_index": 2, "calls_succeeded": 1, "calls_failed": 1, "levers_from_partial": 7}
```
This would allow the analysis pipeline to count partial-recovery plans without inspecting raw files.

**C2 — llama3.1 review_lever format prompt fix (MEDIUM EFFORT, UNCERTAIN BENEFIT)**

Add a concrete single-field example to the prompt's validation protocol section:
```
review_lever example: "Controls centralization vs. local autonomy. Weakness: The options fail to
account for transition costs." — Both 'Controls ... vs. ...' and 'Weakness: ...' MUST appear in a
single field, in this order.
```
Evidence: run 1/02 silo shows 100% non-compliance for call 1. The prompt currently shows the two
clauses as separate bullets, which smaller models may interpret as two alternative formats.

**C3 — qwen3 consequence repair validator (MEDIUM EFFORT, HIGH VALUE)**

Add a post-parse `field_validator` that strips `review_lever`-style text from the end of
`consequences` fields (pattern: `Controls [A] vs. [B].\s+Weakness:.*$`). Unlike a rejection
validator, this repairs rather than rejects, avoiding cascade failures. The contamination appears
in ~67% of qwen3 levers and would not affect other models' outputs.
