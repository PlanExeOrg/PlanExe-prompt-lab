# Assessment: fix: add anti-fabrication reminder to call-2/3 prompts

## Issue Resolution

**What the PR was supposed to fix (PR #313):**
24 unsupported percentage claims persisted across 634 levers in iteration 20 (runs 46–52,
3.8% of levers). The fix: one sentence added to the call-2/3 user prompt immediately after
the name-exclusion blacklist — the same attention-decay point that PR #309 used to fix
llama3.1 label degradation:

> "Do not invent percentages, cost savings, or performance deltas — use qualitative
> language unless the project document supplies the number."

**Is the issue actually resolved?**

Partially, for one model and across-the-board by a small margin.

- **qwen3 (run 53 vs 46, hong_kong_game):** 2 percentage claims → 0. Direct evidence from
  `history/1/53_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  — 16 levers with fully qualitative language, no budget percentages. This is the expected
  result of the PR's call-2/3 fix.

- **haiku (run 58 vs 51, hong_kong_game):** 2 claims → 6+. Evidence from
  `history/1/58_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`:
  lever "Lead Casting" contains "US$15–25 million", "25–42% of the entire production budget",
  "US$3–8 million", "HK$30–50 million", "HK$60 million"; lever "Financing Structure" contains
  "40–50% of budget through pre-sales". The raw JSON structure at
  `002-9-potential_levers_raw.json` responses[0] confirms these originate in **call 1**, before
  the PR's reminder fires.

- **gpt-oss-20b (run 54 vs 47, hong_kong_game):** 2 claims → 5. The additional fabrications
  also appear in call-1 levers anchored to the HK$470m budget figure.

- **Overall (insight_codex full-batch count):** 22 unsupported % tokens across 15 levers →
  19 across 13 levers. GTA improved by 4 tokens, parasomnia by 2; hong_kong_game was flat;
  silo worsened by 3.

**Residual symptoms:**
The dominant remaining fabrication source is **call-1 budget anchoring**: when a plan
document states a specific total budget (HK$470m), models invent sub-allocation percentages
(30%/20%/15%) in their first call, before the PR's reminder is active. The PR is architecturally
sound but cannot reach this failure path. A mirrored call-1 reminder is the required follow-up.

**Note on actual PR scope:** The worktree contains several changes beyond the stated "one line":
(1) `Lever.consequences` schema description rewritten to remove "at least one quantitative
estimate are mandatory" — a structural fabrication mandate; (2) `check_review_format` validator
replaced with a language-agnostic structural check; (3) `OPTIMIZE_INSTRUCTIONS` constant added;
(4) both the full-sentence reminder (from PR #309) and the new anti-fabrication reminder appear
in call-2/3. These additional changes are not mentioned in the PR description but are impactful
(particularly the schema fix, which reduces the structural pressure toward fabrication in all
calls).

---

## Quality Comparison

All 7 models appear in both batches (runs 46–52 = before; runs 53–59 = after). Metrics drawn
from insight_claude, insight_codex (primary quantitative source), and code reviews.
Baseline = `baseline/train/*/002-10-potential_levers.json`.

| Metric | Before (runs 46–52) | After (runs 53–59) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 (100%) | 35/35 (100%) | UNCHANGED |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness (global exact dups)** | 15 duplicates | 12 duplicates | IMPROVED |
| **Template leakage (chain-template consequences)** | 0/634 (0%) | 0/626 (0%) | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | Mixed (structural validator) | Mixed (same) | UNCHANGED |
| **Consequence chain format (Imm→Syst→Strat markers)** | 0/634 (0%) | 0/626 (0%) | UNCHANGED |
| **Short-label options (<5 words)** | 0 / 1,902 (0%) | 21 / 1,902 (1.1%) | **REGRESSED** |
| **Fabricated quantification — unsupported % tokens** | 22 across 15 levers (2.4%) | 19 across 13 levers (2.1%) | SLIGHT IMPROVEMENT |
| — qwen3, hong_kong_game % claims | 2 | 0 | **IMPROVED** |
| — haiku, hong_kong_game % claims | 2 | 6+ | **REGRESSED** (call-1; not PR-caused) |
| — gpt-oss-20b, hong_kong_game % claims | 2 | 5 | **REGRESSED** (call-1; not PR-caused) |
| — GTA plan % tokens (all models) | 7 | 3 | **IMPROVED** |
| — silo plan % tokens (all models) | 3 | 6 | **REGRESSED** |
| — parasomnia plan % tokens (all models) | 7 | 5 | IMPROVED |
| — sovereign_identity plan % tokens | 0 | 0 | UNCHANGED |
| **Marketing-copy language hits** | 8 | 7 | UNCHANGED (noise) |
| **Content depth — avg option length (words)** | 18.92 w | 18.61 w | UNCHANGED |
| **Field length vs baseline — consequences** | 1.16× | 1.17× | UNCHANGED |
| **Field length vs baseline — options** | 0.99× | 0.98× | UNCHANGED |
| **Field length vs baseline — reviews** | 1.12× | 1.13× | UNCHANGED |
| **haiku consequence length vs baseline (hong_kong_game)** | ~2.5× | ~4× | **WARNING** (budget-anchor verbosity) |
| **Cross-call duplication (exact name dups)** | 15 | 12 | IMPROVED |
| **Over-generation (>7 levers/call)** | avg 18.0 levers/output | avg 17.9 levers/output | UNCHANGED |
| **Silent partial-call loss (2 responses instead of 3)** | 2 plans | 3 plans | **SLIGHT REGRESSION** |

**OPTIMIZE_INSTRUCTIONS alignment:**
The worktree's OPTIMIZE_INSTRUCTIONS constant (lines 27–69) explicitly prohibits fabricated
numbers, hype language, vague aspirations, and English-only validation. The PR advances these
goals for calls 2/3, and the worktree's schema fix (`Lever.consequences` rewrite) removes the
fabrication mandate that was structurally overriding the prohibition. A new violation appears:
21 short-option slogans in run 53 (qwen3, silo) contravene the "not a slogan" prohibition. The
derived-partitioning pattern (inventing sub-percentages from a real total budget) is not yet
explicitly documented in OPTIMIZE_INSTRUCTIONS despite being the dominant remaining fabrication
mechanism.

---

## New Issues

**N1. Short-option relapse in run 53 (qwen3, silo) — NEW regression.**
insight_codex counts 21 options under 5 words in the after batch (0 before). All concentrated
in `history/1/53_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.
Examples from the file: "Centralize decision-making under a single governing body" (7 words),
"Deploy AI-driven surveillance with real-time monitoring" (7 words), "Use human oversight with
periodic audits" (6 words), "Implement a community-based accountability system" (5 words). These
are slogan-level labels that do not meet the "at least 15 words with an action verb" standard in
the call-2/3 reminder, and they conflict with OPTIMIZE_INSTRUCTIONS' "not a slogan" rule.
The PR's 15-word floor is only in the call-2/3 user prompt reminder; there is no code-level
validator enforcing it in call 1. The relapse is isolated to one run, suggesting model variance
rather than systematic regression, but it should be monitored.

**N2. Silent partial-call loss slightly worse (2 → 3 plans).**
Three after-run raw files contain only 2 responses instead of 3:
`history/1/54_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`,
`history/1/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json`,
and `history/1/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`.
No `LLMChatError` appears in any audited `events.jsonl`. `run_single_plan_complete` fires
even for 2-of-3 runs, making the failure indistinguishable from a full success in artifacts.
The gap is widening: 2 before, 3 after. The PR does not touch `runner.py`, so the observability
gap remains unaddressed.

**N3. haiku and gpt-oss-20b fabrication in call 1 is now more visible as the dominant source.**
The PR's call-2/3 fix makes it clear that the remaining fabrication is concentrated in call 1
for budget-context plans. haiku run 58 hong_kong_game contains 6+ fabricated dollar/percentage
claims all from `responses[0]`, confirmed by reading the raw JSON and the final merged output.
This is not new behavior but is now the most prominent remaining quality issue given that
call-2/3 fabrication has been partially suppressed.

---

## Verdict

**CONDITIONAL**: The PR is worth keeping — it is low-risk, follows the proven attention-decay
reinforcement mechanism, and measurably reduces qwen3 fabrication in budget-context plans —
but it is not a complete fix. The dominant remaining fabrication source is call-1 budget
anchoring (haiku and gpt-oss-20b inventing sub-allocation percentages from a real total
budget), which the call-2/3 reminder cannot reach. A parallel call-1 reminder with explicit
derived-partitioning language is required for the PR to achieve its stated goal across all
models. The conditions:

1. **Must** be followed by a call-1 anti-fabrication reminder (same mechanism, one more callsite).
2. **Monitor** the run-53 short-option relapse (21 options < 5 words in qwen3 silo) in the
   next iteration to determine if it is a one-off variance or a recurring pattern.

---

## Recommended Next Change

**Proposal:** Add the anti-fabrication reminder to the **call-1** user prompt as well,
with explicit derived-partitioning language. The synthesis proposes:

```python
# current
if call_index == 1:
    prompt_content = user_prompt

# proposed
if call_index == 1:
    prompt_content = (
        user_prompt +
        "\nDo not invent percentages, cost savings, or performance deltas — "
        "use qualitative language unless the project document supplies the exact number. "
        "If the plan states a total budget or a numeric range, do not derive or invent "
        "sub-allocation percentages or stricter thresholds from it."
    )
```

The first sentence mirrors the call-2/3 reminder from PR #313 (proven wording). The second
sentence adds the derived-partitioning explicit prohibition: models seeing a real HK$470m
total invent "30% to VFX, 20% to cast"; models seeing a "70–80% capture range" invent a
"90% threshold." Neither pattern is stopped by the generic rule.

**Evidence:** Unanimous across all four agents (insight_claude N3/Q2/C1/H1, insight_codex
H1/H2, code_claude I1, code_codex B1/I1). The raw output structure for haiku run 58 confirms
fabricated dollar amounts and percentages appear in `responses[0]` (call 1), lever_index 3
("Lead Casting"), before the call-2/3 reminder fires. The net fabrication count (22→19
tokens) would have been more dramatic if call-1 had been addressed; the modest improvement
reflects call-2/3-only coverage.

Also add the derived-partitioning pattern to `OPTIMIZE_INSTRUCTIONS` as a documented known
pitfall: "When a plan states a total budget or numeric range, models often invent allocation
sub-percentages (e.g., 30%/20%/15% from HK$470m) or stricter thresholds (90% from 70–80%)
that are mathematically plausible but unsupported. The generic 'no fabricated numbers' rule
does not suppress this — it requires an explicit 'do not partition total budgets or tighten
ranges' instruction."

**Verify in next iteration:**
- Check haiku (run ~65) and gpt-oss-20b (run ~62) hong_kong_game outputs specifically.
  Target: 0 budget-percentage fabrications (was 6+ and 5 respectively). If haiku still
  fabricates dollar amounts in `responses[0]` after the call-1 reminder, escalate to the
  H2 option: preprocess the project context to redact specific dollar figures.
- Check qwen3 silo: did the run-53 short-option relapse (21 options) recur? Check call-1
  options specifically for slogan-level phrases (<8 words, no strategic verb).
- Verify the net unsupported-% token count drops below 10 (from 19). Any reduction to ≤5
  would confirm the call-1 reminder is the dominant fix.
- Confirm 35/35 success rate holds. The call-1 reminder is additive; zero structural risk.
- Confirm haiku silo (no explicit budget) remains clean (it was 0 in run 58). The reminder
  should be neutral for plans without budget anchors.
- Watch for over-qualification: if avg consequence length drops below 250 chars (current
  ~294 words × ~5 chars = very rough) or average option length drops below baseline ratio
  of 0.9×, the "qualitative only" instruction may be overcorrecting.

**Risks:**
- Call-1 options or consequences may become vague if the model interprets "qualitative only"
  too broadly. Monitor avg field lengths vs. baseline (warning if below 0.85×).
- The derived-partitioning rule ("do not sub-allocate total budgets") may cause models to
  avoid all budget references, including legitimately grounded ones. If a plan explicitly
  states "allocate 30% to marketing", the reminder should not suppress this — the exact
  number appears in the document. Verify with a plan that has explicit sub-allocations.
- Run 53's short-option issue (call-1 slogan leak) is unaddressed by the call-1 anti-
  fabrication reminder. If it recurs, a companion call-1 word-count reminder ("at least
  15 words with an action verb, not a short label") would close this gap using the same
  mechanism.

**Prerequisite issues:** None. This is a one- to two-line change in the call-1 branch at
`identify_potential_levers.py`. No other fixes need to land first.

---

## Backlog

**Resolved by PR #313 (remove from backlog):**
- **Fabricated quantification in call-2/3 (HIGH)** from analysis/20 backlog: Partially
  resolved. call-2/3 fabrication is reduced (qwen3 confirmed, GTA improved). However the
  call-1 source remains open; move to: **Fabricated quantification in call-1 (HIGH)**.
  Full closure requires the call-1 reminder.

**Items remaining / updated from prior backlog:**
- **Fabricated quantification — call-1 budget anchoring (HIGH, new priority):** haiku and
  gpt-oss-20b fabricate dollar/percentage values in call-1 responses when the plan context
  includes a specific budget figure. Specific pattern: deriving sub-allocation percentages
  from a stated total or tightening a supplied range into a stricter threshold. Fix: call-1
  anti-fabrication reminder with derived-partitioning language (Recommended Next Change).
- **Short-option relapse in call-1 (MEDIUM, newly observed):** 21 options <5 words in run 53
  (qwen3, silo), all from call-1. The "15 words with an action verb" reminder is in call-2/3
  only. No code-level validator enforces option length. Fix: extend the word-count reminder
  to call-1 as well, or add a `logger.warning` post-generation validator (code_claude I4,
  code_codex B3/I3).
- **Silent partial-call loss (MEDIUM):** 3 plans in after batch have only 2 responses; no
  `LLMChatError` visible in `events.jsonl`; `run_single_plan_complete` fires as if the run
  succeeded fully. Fix: add `completed_calls` field to output, emit `run_single_plan_partial`
  event from `runner.py` (synthesis Direction 4). Worsening: 2→3 plans; schedule for the
  iteration after the call-1 reminder is validated.
- **Numeric-grounding post-generation audit (MEDIUM):** A scan of `levers_cleaned` for `\d+%`
  and currency tokens against `user_prompt` would make fabrication regressions immediately
  visible in logs, eliminating repeating manual measurement work. Warning-only, no retry cost
  (synthesis Direction 3, code_claude I2, code_codex I2).
- **Derived-partitioning pattern not documented in OPTIMIZE_INSTRUCTIONS (LOW):** The "no
  fabricated numbers" prohibition is too generic to suppress the specific pattern of inventing
  budget sub-allocations from a real total. Should be added as a named pitfall.
- **`set_usage_metrics_path` race condition in runner.py (LOW):** Called outside `_file_lock`
  at lines 106/140; in parallel mode, concurrent threads can overwrite each other's metrics
  path. Low-severity (metrics are observational), but a real thread-safety bug. Unaddressed
  by PR #313.
- **Semantic near-duplicate lever detection (LOW):** Name-only dedup passes "Festival Strategy
  for Critical Reception" / "Festival Strategy for Audience Engagement" as distinct levers.
  The module docstring defers this to `deduplicate_levers.py`; verify that downstream dedup
  catches these before investing in a call-level fix.
- **haiku option verbosity monitoring (LOW):** haiku consequence length in budget-context plans
  (~4× baseline in hong_kong_game) exceeds the 2× warning threshold when fabricated dollar
  amounts inflate the text. In non-budget plans (silo, run 58) haiku is substantive but within
  range. Monitor whether call-1 reminder reduces this or if explicit verbosity guidance is needed.
- **Per-call prompt fingerprinting in run metadata (LOW):** Runner records `system_prompt_sha256`
  but not the dynamically assembled call-1/2/3 user prompt hashes or git commit. PR #313's
  change (inline f-string in Python) is invisible from `meta.json` SHA comparison. A per-call
  prompt hash field would make future code-only prompt PRs auditable from artifacts.
