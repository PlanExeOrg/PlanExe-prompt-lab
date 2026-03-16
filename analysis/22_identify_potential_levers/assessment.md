# Assessment: Prompt 6 Revision (no registered PR)

## Issue Resolution

**No PR is registered in the after `meta.json`.** The after batch (runs 60–66) reflects a prompt
version change from prompt_5 (with PR #313's call-2/3 anti-fabrication reminder) to prompt_6.
The recommended next change from analysis/21's assessment was:

> Add the anti-fabrication reminder to the **call-1** user prompt with explicit
> derived-partitioning language: "If the plan states a total budget or a numeric range, do
> not derive or invent sub-allocation percentages or stricter thresholds from it."

**Was this implemented?** Partially. Prompt_6 Section 2 adds "Do not fabricate percentages or
cost estimates" inline in the Consequences quality standard, and Section 5 retains "NO fabricated
statistics or percentages without evidence from the project context." The prompt is more
structured than prompt_5, with numbered sections and explicit Prohibitions. However, the
**specific derived-partitioning prohibition** ("do not sub-allocate total budgets or tighten
supplied ranges") is absent from both the prompt file and the Python call-1 branch.

**Was the issue resolved?**

For 5 of 7 models (llama3.1, gpt-5-nano, gpt-4o-mini, gemini, gpt-oss-20b), round-number
fabricated percentages are largely eliminated: gpt-oss-20b dropped from 5 to 1 claim, the
others held at 0. However:

- **haiku (run 66):** Pivoted from round-number fabrication (6+ claims in run 58) to **precision
  theater** — pseudo-precise operational ranges: `60–70% of principal photography`, `40–50% of
  budget`, `51%/49% equity split`, `3–5% interest rate`, `estimated 40% throughput reduction`.
  Insight_codex counts 16 unsupported numeric claims across 5 plans in run 66. The current
  prohibition ("NO fabricated statistics or percentages") does not suppress precision theater
  because haiku interprets it as "avoid round numbers," not "avoid invented operational specifics."
  Evidence: `history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:64,184`,
  `history/1/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:63,73`,
  `history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:31`.

- **qwen3 (run 63):** Slight regression from 0 (run 53, improved by PR #313) to 3 fabricated
  claims ("Allocate 70% of resources…", "Secure 100% government funding…", "90% event capture
  rate") in silo and parasomnia outputs.

**Residual symptoms:** The dominant fabrication source has evolved. haiku no longer uses round-number
percentages but substitutes precision-theater specifics across all 5 plans. The total fabricated-
quantification count is flat (19 before → 20 after), with improvement in gpt-oss-20b offset by
haiku's precision-theater regression and qwen3's mild relapse.

**Note on insight_claude discrepancy:** insight_claude (22) classifies run 66 (haiku) as the
best-quality run, citing zero fabricated percentages. This is incorrect — it scanned for round-
number claims only and missed precision theater. insight_codex correctly classifies run 66 as
F-tier. The synthesis confirms insight_codex's verdict.

---

## Quality Comparison

All 7 models appear in both batches (before = runs 53–59 prompt_5+PR#313; after = runs 60–66
prompt_6). Model alignment: qwen3 53↔63, gpt-oss-20b 54↔61, gpt-5-nano 55↔62, gpt-4o-mini
56↔64, gemini 57↔65, haiku 58↔66, llama3.1 59↔60. Primary source: insight_codex for both
analyses (quantitative tables). Field-length ratios use chars for after-batch (insight_codex 22)
and words for before-batch (insight_codex 21); direct comparison is approximate but directionally valid.

| Metric | Before (runs 53–59) | After (runs 60–66) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 12 global dups / 626 levers | 1 within-run dup (run 60) / 629 levers | IMPROVED |
| **Template leakage (old chain format)** | 0 | 0 | UNCHANGED |
| **Review format — two-sentence compliance** | Not measured (structural validator only) | ~0–82% by run; runs 60,63,64 ≈0% | **REGRESSED** (new broken contract) |
| **Review formula monoculture** | "Controls/Weakness" style (prompt_5) | "This lever governs…" in 82–106 / ~91–108 per run | REGRESSED (different template, same monoculture) |
| **Consequence chain format (Imm→Syst→Strat)** | 0 | 0 | UNCHANGED |
| **Short-label options (<5 words)** | 21 (run 53, qwen3 silo) | 0 identified | IMPROVED |
| **Fabricated quantification — total tokens** | 19 across 13 levers (2.1%) | 20 across ~13 levers | UNCHANGED (redistributed) |
| — haiku (run 58 vs 66), all plans | 6+ round-number claims (call-1) | 16 precision-theater claims | **REGRESSED** |
| — gpt-oss-20b (run 54 vs 61) | 5 | 1 | **IMPROVED** |
| — qwen3 (run 53 vs 63) | 0 | 3 | **REGRESSED** (slight) |
| — gpt-5-nano, gpt-4o-mini, gemini, llama3.1 | ~0 | 0 | IMPROVED / UNCHANGED |
| **Marketing-copy language hits** | 7 | 6 (run 60:2, run 64:3, run 66:1) | UNCHANGED (noise) |
| **Content depth — avg option length vs baseline** | 0.98× (words) | ~0.95× avg (chars); run 66: 1.95× | UNCHANGED overall; haiku WARNING |
| **Field length — consequences vs baseline** | 1.17× (words) | ~1.08× avg (chars); run 66: 1.85× | UNCHANGED overall; haiku WARNING |
| **Field length — reviews vs baseline** | 1.13× (words) | ~1.27× avg (chars); run 66: 2.25× | **SLIGHT REGRESSION** (run 66 drives) |
| **Run 66 (haiku) reviews vs baseline** | ~2× (run 58 hong_kong_game) | 2.25× all-plan avg | **WARNING** (exceeds 2× threshold) |
| **Cross-call duplication (raw cross-call dups)** | 12 global exact dups | 12 raw cross-call dups (codex table) | UNCHANGED |
| **Over-generation (>7 levers/call)** | avg 17.9 levers / run output | avg ~89.9 levers / run (runs 60:4, 66:3 over-cap responses) | INFORMATIONAL (no schema failure) |
| **Silent partial-call loss** | 3 plans (runs 54, 59) | 2 plans (run 60 only) | SLIGHT IMPROVEMENT |
| **Conservative-path in options** | Not flagged | Explicitly missing in llama3.1 run 60 silo | NEW ISSUE IDENTIFIED |

**OPTIMIZE_INSTRUCTIONS alignment:**
Prompt_6 advances the "no fabricated numbers" and "no marketing language" goals. New violations
detected in analysis/22:

1. **Precision theater not documented**: OPTIMIZE_INSTRUCTIONS prohibits "fabricated percentages"
   but does not name or describe precision theater. Haiku technically complies with the current
   wording while generating unsupported operational specifics (budget splits, equity ratios,
   throughput estimates). This gap allows the failure mode to recur in any run.

2. **Conservative-path misalignment**: OPTIMIZE_INSTRUCTIONS lines 48–52 require "at least one
   conservative, low-risk path" per lever. The active system prompt asks only for "at least one
   unconventional or non-obvious approach" — the opposite emphasis. The inter-call prompt omits
   it entirely. This discrepancy persists from prior iterations.

3. **Review contract contradiction**: Prompt_6 claims "review_lever (one field, two sentences)"
   but provides a single-sentence example. The Pydantic field description in
   `identify_potential_levers.py:92–98` and the system prompt constant at lines 214–218 both
   repeat the same contradiction. Result: models follow the example shape (one sentence) and
   ignore the claim (two sentences), producing near-zero two-sentence compliance in most runs.

---

## New Issues

**N1. Precision theater in haiku (run 66) — NEW failure mode.**
Run 66 (haiku) produces 16 unsupported numeric claims across all 5 plans. These are not
marketing-hype phrases but pseudo-precise operational specifics that pass current structural
validators: `60–70% of principal photography`, `40–50% of budget`, `51%/49% equity split`,
`3–5% interest rate`, `estimated 40% throughput reduction`. insight_claude missed these (scanned
for round numbers only); insight_codex correctly rated run 66 F-tier. This pattern was not
present in run 58 (haiku before) at this scale or specificity. OPTIMIZE_INSTRUCTIONS does not
name or describe precision theater, so the next iteration will encounter the same issue unless
the prohibition is explicitly extended.

**N2. Contradictory review contract — NEW structural inconsistency.**
Prompt_6 Section 4 states "review_lever (one field, two sentences)" with the example:
> "This lever governs the tension between centralization and local autonomy, but the options
> overlook transition costs."
That example is one sentence. The Pydantic field description and system prompt constant repeat
the same contradiction (code_codex B1). Two-sentence compliance: run 60 = 0/91, run 63 = 17/74,
run 64 = 5/83, run 65 = 75/92, run 66 = 69/108 (insight_codex table). Models follow the example
shape. This was not a tracked issue in analysis/21.

**N3. Semantic duplication in llama3.1 (run 60) now explicitly documented.**
Run 60 sovereign_identity generates 24 levers with ~14 unique concepts (58% uniqueness ratio):
four variants of "Digital Identity Standards" ("…Harmonization", "…Enforcement", "…Development"),
duplicate procurement and research clusters. Root cause: inter-call anti-repetition is name-only
(`identify_potential_levers.py:269–276`). DeduplicateLeversTask is expected to handle these
downstream but the pre-dedup bloat is wasteful for weaker models. Not a new code bug but newly
flagged in analysis/22.

**N4. Conservative-path gap surfaced — LATENT issue now documented.**
OPTIMIZE_INSTRUCTIONS explicitly requires "at least one conservative, low-risk path" per lever,
but the active system prompt requests "at least one unconventional or non-obvious approach" — the
opposite. Run 60 silo levers show only hybrid/balanced choices with no genuine conservative
baseline option. This discrepancy was present in prior iterations but not flagged until
analysis/22 code reviews (code_codex B4, code_claude I3).

---

## Verdict

**CONDITIONAL**: Prompt_6 is a net improvement for 5 of 7 models — fabricated round-number
percentages are largely eliminated, short-option slogans are gone, and partial-call loss
improved slightly. However, haiku's pivot to precision theater (16 unsupported claims in run 66,
spread across all 5 plans) prevents this from being a clean improvement. The total fabricated-
quantification count is flat (19→20), with gpt-oss-20b improvement offset by haiku's precision-
theater regression and qwen3's mild relapse. The contradictory two-sentence review contract is a
new structural problem affecting all 7 runs (~630 reviews with near-zero compliance).

The recommended next change (Direction 1 from synthesis/22: strengthen anti-fabrication to cover
precision theater) must land before prompt_6 can be considered resolved.

**Conditions:**
1. **Must**: Add explicit precision-theater prohibition to OPTIMIZE_INSTRUCTIONS, system prompt,
   and prompt file (synthesis Direction 1).
2. **Must**: Fix the contradictory review contract — replace single one-sentence example with
   2–3 stylistically varied two-sentence examples (synthesis Direction 3).
3. **Should**: Add concept-level anti-repetition to inter-call prompt (synthesis Direction 2).

---

## Recommended Next Change

**Proposal:** Strengthen the anti-fabrication prohibition in three locations to explicitly cover
"precision theater" — the pattern where models avoid round-number hype while generating pseudo-
precise operational ranges and splits (budget splits, equity ratios, throughput estimates,
interest rates) that are equally ungrounded.

**Evidence:** Unanimous across all four analysis agents (insight_codex F-tier for run 66 with
16 unsupported claims; code_claude I4; code_codex I5; synthesis Disagreements section and Top 5
Directions). Run 66 examples confirmed in output files:
`history/1/66_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:64`
("60–70% of principal photography"), `:184` ("40–50% of budget");
`history/1/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:63`
("estimated 40% throughput reduction"), `:73`;
`history/1/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:31`
("3–5% interest"). Run 63 (qwen3) also has 3 precision-theater claims in silo and parasomnia.

The synthesis proposes changes at three locations:

**Location 1** — `OPTIMIZE_INSTRUCTIONS` in `identify_potential_levers.py`, after the
"Fabricated numbers" bullet. Add:
> - **Precision theater.** Models may avoid round-number hype while still producing unsupported
>   pseudo-precise thresholds: budget splits ("40–50% of budget"), equity splits ("51%/49%"),
>   throughput estimates ("estimated 40%"), interest rates ("3–5%"). These violate the same
>   prohibition. Rule: if the exact figure does not appear verbatim in the project context, do
>   not use it.

**Location 2** — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` Prohibitions section. Replace:
> "NO fabricated statistics or percentages without evidence from the project context"

with:
> "NO fabricated or derived numbers of any kind — percentages, ranges, budget splits, equity
>  ratios, probability thresholds, throughput figures, or interest rates — unless the exact
>  figure appears verbatim in the project context. '60–70% of budget' and '51%/49% equity'
>  are fabricated operational specifics, not grounded analysis."

**Location 3** — prompt file Prohibitions section (kept in sync with Location 2).

**Verify in next iteration:**
- Haiku (next equivalent of run 66) on hong_kong_game and silo: target 0 precision-theater
  claims (was 16 in run 66). Specifically check for range formats (`X–Y%`) and non-round splits
  (`51%/49%`) not present verbatim in `001-2-plan.txt`.
- qwen3 (next equivalent of run 63): verify fabricated % count returns to 0 (was 0 in run 53,
  rose to 3 in run 63). Check silo and parasomnia plans specifically.
- gpt-oss-20b (next equivalent of run 61): verify holds at ≤1 claim (improved from 5 to 1
  already; regression risk is low but confirm).
- Total fabricated-token count across all 7 runs: target ≤5 (was 19 before, 20 after; haiku
  alone accounts for 16 of the current 20).
- Two-sentence review compliance (if Direction 3/review-contract fix also lands): should rise
  from near-zero to ≥50% in the next batch. Measure by period count per review field.
- Confirm 35/35 success rate holds (additive prompt change).
- Monitor avg field lengths: if consequences or options drop below 0.85× baseline after the
  tightened prohibition, the rule is overcorrecting. Run 65 (gemini) at 1.19× consequence ratio
  is the target style — specific but not inflated.

**Risks:**
- Tightening the precision-theater prohibition may cause all models to avoid all numerical
  specificity, including legitimately grounded numbers. Monitor avg field lengths; if
  consequences drop below 0.85× baseline, the rule needs a qualifying clause ("unless the exact
  figure appears verbatim in the project context" — already included in the proposed wording).
- Fixing the review contract (replacing one example with multiple varied examples) may
  temporarily shift models to a new monoculture if the replacement examples all share an opening
  pattern. Use 2–3 structurally varied examples with different opening verbs.
- Direction 2 (concept-level anti-repetition, inter-call prompt) carries low risk for strong
  models but may over-constrain weak models if the topic-description framing is too broad.
  Verify haiku and gpt-5-nano semantic uniqueness does not degrade.

**Prerequisite issues:** None. The anti-fabrication wording change is independent of other fixes.
The synthesis recommends landing Direction 1 (precision theater) before Direction 3 (review
contract) since fabricated numbers affect plan credibility while review monoculture affects
analytical diversity — lower stakes.

---

## Backlog

**Resolved since analysis/21 (remove from backlog):**
- **Short-option relapse in call-1 (MEDIUM)**: 21 options <5 words in run 53 (qwen3 silo) —
  not observed in runs 60–66. No recurrence in qwen3 run 63 or other models. Remove from active
  backlog; retain as watch metric for qwen3 silo specifically.

**Promoted / updated:**
- **Precision theater / derived quantification (HIGH, new priority)**: haiku run 66 has 16
  unsupported precision-theater claims; qwen3 run 63 has 3. Generic prohibition is insufficient.
  Fix: synthesis Direction 1 (three-location wording change). Was previously labeled
  "derived-partitioning" at LOW; upgrade to HIGH and rename.
- **Fabricated quantification — call-1 budget anchoring (HIGH, updated)**: Carried from
  analysis/21. The call-1 specific reminder with derived-partitioning language was not added in
  prompt_6. haiku's precision theater in run 66 spans all 5 plans (not just budget-context
  plans), suggesting the issue is broader than call-1 budget anchoring alone. Direction 1
  (prompt wording change at all call points) should address this more effectively than a
  call-1-specific code change.

**Items remaining:**
- **Contradictory review contract (MEDIUM, new)**: Prompt_6 claims two sentences but provides
  a one-sentence example. Fix: replace single example with 2–3 stylistically varied two-sentence
  examples in `identify_potential_levers.py:94–98` and `:216–218` (synthesis Direction 3,
  code_codex B1). Affects all 7 runs, ~630 reviews per batch.
- **Semantic duplication in weaker models (MEDIUM)**: Inter-call prompt blocks exact name reuse
  but not concept reuse. Run 60 sovereign_identity: 24 levers, 58% uniqueness. Fix: change
  "completely different names" to "entirely different strategic topics and concepts" in the
  inter-call prompt (synthesis Direction 2, code_claude I1, code_codex I4). Very low effort.
- **Conservative-path gap in active prompt (MEDIUM)**: OPTIMIZE_INSTRUCTIONS requires "at least
  one conservative, low-risk path" but the active system prompt and inter-call prompt do not.
  Fix: add one clause to the Options MUST list in prompt file and one sentence to the inter-call
  prompt (synthesis Direction 4, code_codex B4, code_claude I3).
- **Silent partial-call loss (MEDIUM)**: 2 plans in run 60 with 2 responses instead of 3; no
  `LLMChatError` visible in `events.jsonl`. Improved from 3 (before) to 2 (after) but still
  unobservable. Fix: emit structured per-call failure event from `runner.py` with call counts
  and error type (synthesis Direction 5, code_claude B2, code_codex B2).
- **Race condition: `set_usage_metrics_path` outside `_file_lock` (LOW)**: Confirmed in
  `runner.py:107,150`. Corrupts `usage_metrics.jsonl` for all parallel runs (61–66 use 4
  workers). Carried from analysis/21 backlog. (synthesis Direction 5, code_claude B1.)
- **Per-call prompt fingerprinting in run metadata (LOW)**: Runner records `system_prompt_sha256`
  but not the dynamically assembled inter-call prompt hash or git commit. Prompt_6 change (Python
  constants and inline strings) is invisible from `meta.json` SHA comparison. Fix: hash the
  inline call-1/2/3 prompt templates alongside `system_prompt_sha256` (code_codex S2, I7).
- **Option-quality validator (LOW)**: No structural gate for label-like options; `len(options)==3`
  is the only enforced check. A soft warning for options below a character floor (e.g., 60 chars)
  without internal spacing typical of a sentence would surface future short-option regressions
  without rejecting outputs (code_codex B3, I3).
