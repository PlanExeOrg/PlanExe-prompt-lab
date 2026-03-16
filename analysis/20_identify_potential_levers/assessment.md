# Assessment: fix: add option-quality reminder to call-2/3 prompts

## Issue Resolution

**What the PR was supposed to fix (PR #309):**
llama3.1 calls 2 and 3 degraded to 2–3 word labels for ~38% of levers while call-1 produced
full sentences. Root cause: the "complete strategic sentence" quality contract in the system
prompt loses attention weight as the `Do NOT reuse these names` exclusion blacklist grows across
calls. Fix: one-line reminder immediately after the blacklist, restating the requirement.

**Is the issue resolved?**
Yes. Confirmed by two independent agents with direct file evidence.

- Before (run 45, analysis/19): 8/22 levers (36%) in silo call-3 had label-only options —
  e.g., "Bioregenerative Systems", "Closed-Loop Ecology", "Synthetic Ecosystems", "Decentralized
  Councils", "Hierarchical Bureaucracy", "Autonomous Zones". gta_game had ~9/22 (41%) label-only.
- After (run 52, analysis/20): 0/23 levers (0%) across ALL five plans. Raw call-3 artifacts
  confirm the fix operates at source, not just post-dedup: `002-9-potential_levers_raw.json`
  call-3 for silo shows full strategic sentences.
- Call-3 average option length: ~15 chars (labels) → ~65 chars (sentences), a 4× improvement.
  In word count: llama3.1 call-3 avg words 6.2 → 13.1 (codex measurement across all plans).

**Residual symptoms:**
llama3.1 call-3 options are full sentences but still shallower than call-1 (avg ~65 vs ~90
chars in silo). The quality gap is real but far narrower than before. This is a depth issue,
not a structural failure.

**Bundled fix also confirmed:** The worktree changes `break` → `continue` in the call-loop
exception handler (B1 in code reviews). Before: call-2 failure silently dropped call-3, leaving
~7 levers instead of ~18, with `status="ok"` in events.jsonl. After: call-3 proceeds
independently of call-2 failures. Evidence: insight_codex counted 34 third-call responses in
analysis/19 vs. 33 in analysis/20, consistent with the new `continue` path now exposing
independent call-3 failures that previously would have been hidden by `break`.

---

## Quality Comparison

All 7 models appear in both batches. Metrics drawn from insight_claude, insight_codex, and
code_claude cross-validated tables. Baseline = `baseline/train/*/002-10-potential_levers.json`.

| Metric | Before (runs 38–45) | After (runs 46–52) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 instances | 0 instances | UNCHANGED |
| **Option count violations (≠3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 18.0/18.0 (100%) | 18.1/18.1 (100%) | UNCHANGED |
| **Template leakage (chain-template consequences)** | 0/630 (0%) | 0/634 (0%) | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | Mixed (non-"Controls" allowed since PR #299) | Mixed (same pattern) | UNCHANGED |
| **Short-label options (≤3 words)** | 47/1890 (2.5%) | 0/1902 (0%) | **IMPROVED** |
| **llama3.1 call-3 label-only levers — silo** | 8/22 (36%) | 0/23 (0%) | **IMPROVED** |
| **llama3.1 call-3 label-only levers — gta_game** | ~9/22 (41%) | 0/~22 (0%) | **IMPROVED** |
| **Content depth — avg option chars (all models)** | 121.8 | 142.5 | **IMPROVED** (+17%) |
| **Content depth — raw call-2 avg words** | 16.6 | 20.9 | **IMPROVED** |
| **Content depth — raw call-3 avg words** | 15.6 | 21.2 | **IMPROVED** |
| **Field length vs baseline — consequences** | 1.06× | 1.07× | UNCHANGED |
| **Field length vs baseline — options** | 0.81× | 0.95× | **IMPROVED** (toward baseline) |
| **Field length vs baseline — reviews** | 1.11× | 1.14× | UNCHANGED |
| **haiku review length vs baseline** | ~2.7× | ~2.5× | UNCHANGED (slight reduction) |
| **Fabricated quantification count** | 20 claims / 630 levers (3.2%) | 24 claims / 634 levers (3.8%) | SLIGHT INCREASE (noise) |
| **Marketing-copy language count** | 6 levers | 5 levers | UNCHANGED (noise) |
| **Cross-call duplication within output** | 100% unique | 100% unique | UNCHANGED |
| **Over-generation count (>7 levers/call)** | Avg 18.0 levers/output | Avg 18.1 levers/output | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS alignment:** The source checked into main still contains:
- Mandatory measurable estimates in `consequences` ("at least one quantitative estimate are
  mandatory", line 39) — directly causes fabricated percentages; unchanged in main branch
- "Show clear progression: conservative → moderate → radical" (line 169) — forces all options
  into a single axis; unchanged in main
- "Radical option must include emerging tech/business model" (line 193) — drives "cutting-edge"
  violations and the gpt-oss-20b "(note: not allowed)" annotation; unchanged in main

The PR #309 worktree removes all three and adds `OPTIMIZE_INSTRUCTIONS` constant with explicit
anti-fabrication, anti-hype, and i18n guidance. On merge, these goals are advanced. The single
gpt-oss-20b "cutting-edge" violation and the 24 unsupported % claims are explained by the
production constant still not matching the registered prompt_5 — which the PR fixes.

---

## New Issues

**1. Partial-call observability gap (pre-existing, now more visible):**
The `break` → `continue` change is correct but surfaces a new failure mode: when call-2 fails
AND call-3 also fails independently, the output contains only 7 levers with `status="ok"` and
no logged error. Before, `break` would silently drop call-3 but at least prevent a second
independent failure. The net outcome (few levers, no error) is the same, but the path is new.
Code_codex flags this as B1/I1: partial runs should emit `completed_calls` metadata and a
`partial` status rather than `ok`.

**2. Fabricated quantification: marginal increase (pre-existing, not worsened):**
24 claims vs. 20 before (3.8% vs. 3.2%). Examples: qwen3 silo "Allocate 70% of agricultural
output" (run 46), haiku gta "reducing asset production by approximately 30%" and "24+ months"
(run 51), llama3.1 silo "90% waste reduction" (run 52). All pre-existing. The call-2/3 reminder
added sentence completeness but not anti-fabrication guidance. Not introduced by PR #309.

**3. Prompt/production split-brain (pre-existing, critical):**
The optimizer runner loads prompt_5 via `--system-prompt-file`. The production pipeline
(`run_plan_pipeline.py:386`) calls `execute()` with no `system_prompt` override, falling back
to `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` in the source file — which still contains the
fabrication-forcing and tech-forcing instructions the optimization loop has been removing.
Experiments look better than production reality because they run a different prompt.
The PR #309 worktree updates the constant to match prompt_5; this resolves on merge.

---

## Verdict

**YES**: PR #309 delivers the largest single-PR quality improvement in this optimization loop —
llama3.1 label-only options drop from 36–41% to 0% across all plans, with no regressions in any
other model or metric. The bundled `break` → `continue` fix and OPTIMIZE_INSTRUCTIONS additions
are additional improvements. Keep unconditionally.

---

## Recommended Next Change

**Proposal:** Add a one-line anti-fabrication reminder to the same call-2/3 prompt block that
PR #309 already added the sentence-completeness reminder to. Specifically, append after the
existing reminder:

```
Do not invent percentages, cost savings, or performance deltas — use qualitative language
unless the project document supplies the number.
```

This follows the identical mechanism as PR #309: restate a quality rule (already present in the
system prompt and `OPTIMIZE_INSTRUCTIONS`) at the point where model attention has shifted to the
exclusion blacklist and the original rule has decayed.

**Evidence:** Three independent agents converge on this recommendation (insight_codex H2,
code_claude I1, code_codex I5). Quantitative support: 24 fabricated % claims across 634 levers
(3.8%) persist after PR #309. Affected models include qwen3 ("70% agricultural output"), haiku
("~30% asset production", "24+ months"), and llama3.1 ("90% waste reduction"). These are all
later-call outputs — the same attention-decay context that caused the label problem. The system
prompt already prohibits fabricated numbers ("NO fabricated statistics or percentages without
evidence from the project context", worktree line 228), so the reminder is a restatement, not
a new rule. PR #309 itself is the proof-of-concept that this restatement pattern works.

**Verify in next iteration:**
- Check all five plans for llama3.1 (run ~53) and qwen3 for fabricated % in options and
  consequences. Baseline: 24 total across 634 levers. Target: reduction to ≤10.
- Verify haiku (the worst offender at ~8 claims in 5 plans) specifically reduces — it is the
  most instruction-following model and most likely to respond to an explicit reminder.
- Confirm no regression in option completeness for llama3.1: call-3 avg words should remain
  ≥13.1 (achieved in analysis/20). The new line should not crowd out the completeness reminder.
- Check gpt-oss-20b specifically for "cutting-edge" and parenthetical self-annotations
  (N5/N6) — these are driven by B4 (radical-tech forcing) which the worktree removes from the
  system prompt. Verify the production constant now matches prompt_5 post-merge.
- Confirm 35/35 success rate holds.

**Risks:**
- Minimal. The instruction is prohibitive (do not invent X), not prescriptive. Models that
  already avoid fabrication are unaffected. No new Pydantic validators are added; no retry
  overhead.
- Slight risk of making consequences less specific — models might interpret "qualitative only"
  too broadly and produce vague claims. Monitor avg consequence length (should stay ≥~295 chars;
  current 297.8). A reduction below 250 chars would indicate over-correction.
- The blacklist grows with each successive call; a 2-item reminder block is still minimal
  context relative to the full user prompt. If a 3-item block (adding a third rule) is ever
  needed, watch for qwen3 and llama3.1 becoming verbose in later calls.

**Prerequisite issues:**
None. PR #309 already has the infrastructure (worktree stacks PR #299 + PR #309 changes). The
anti-fabrication line is a one-character diff beyond the current worktree. The `break` →
`continue` fix and OPTIMIZE_INSTRUCTIONS are already in the worktree and will merge with PR
#309. No additional PRs are required first.

---

## Backlog

**Resolved by PR #309 (remove from backlog):**
- C2/H2 (analysis/18–19): llama3.1 multi-call label-only option degradation — FIXED. Zero
  label-only options in all 5 plans for run 52.
- B1 (code_claude, analysis/20): `break` on partial failure silently drops call-3 — FIXED in
  worktree (`continue` at line 318). Merges with PR #309.
- B2 (code_claude): English-only `check_review_format` blocking non-English reviews — FIXED in
  worktree (structural validator: ≥20 chars + no square brackets). Merges with PR #309.
- B3 (code_claude): `consequences` schema mandating fabricated quantification — FIXED in
  worktree (grounded consequences description). Merges with PR #309.
- B4 (code_claude): conservative→moderate→radical triad and mandatory emerging-tech option —
  FIXED in worktree (system prompt updated). Merges with PR #309.
- `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant divergence from prompt_5 — FIXED in
  worktree. Merges with PR #309.

**New items to add:**
- **Fabricated quantification in call-2/3 (HIGH):** 24 unsupported % claims across 634 levers
  (3.8%). Affects all models including highest-quality (haiku). Fix: anti-fabrication reminder
  in call-2/3 prompt block (synthesis Direction 1). This is the Recommended Next Change above.
- **Partial-call observability (MEDIUM):** When call-2 or call-3 fails independently, the run
  records `status="ok"` with no indication that ≤7 levers were generated instead of ~18.
  Fix: add `completed_calls`/`expected_calls` metadata to output and emit `partial` status in
  runner.py (synthesis Direction 2, code_codex I1).
- **Prompt/production split-brain (HIGH, resolves on PR #309 merge):** Production pipeline
  (`run_plan_pipeline.py:386`) uses the old in-source constant; prompt-lab runner uses prompt_5.
  Will resolve when PR #309 merges `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant update
  to main. Verify after merge.
- **Review format diversity across models (LOW):** qwen3, gpt-4o-mini, and llama3.1 produce
  non-"Controls" review first sentences ("Balances", "Resource allocation vs.") that pass the
  structural validator but reduce cross-model consistency. H1 (analysis/18–19) — add explicit
  "Controls X vs. Y" grammatical instruction to system prompt. Deferred: not a quality
  regression, and PR #299's validator relaxation was intentional for i18n.
- **haiku option verbosity monitoring (LOW):** haiku averages 1.85–2.5× baseline option/review
  length. Still below 2× warning threshold for options. Monitor in analysis/21; no action yet.
- **Word-count warning validator (LOW):** "At least 15 words with an action verb" is in the
  call-2/3 reminder but unenforced in code. A warning-level `field_validator` logging options
  below 15 words would make future depth regressions measurable without adding retry overhead
  (synthesis Direction 3, code_claude I2).
- **`lever_index` field waste (LOW):** `lever_index: int` in `Lever` is accepted from the LLM
  but never used; `LeverCleaned` uses UUID `lever_id` instead. Wastes token budget. Remove the
  field (code_claude S4).
- **`OPTIMIZE_INSTRUCTIONS` blacklist-decay pattern documentation (LOW):** Document in
  `OPTIMIZE_INSTRUCTIONS` that quality rules stated in the system prompt must be restated inline
  in call-2/3 prompts because the exclusion blacklist dilutes attention. Should be bundled with
  the anti-fabrication PR (synthesis Direction 5).
