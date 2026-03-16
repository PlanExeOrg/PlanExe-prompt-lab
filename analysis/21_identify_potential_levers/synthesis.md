# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on:

1. **PR #313 verdict: CONDITIONAL KEEP.** The one-line call-2/3 reminder is low-risk and directionally correct. qwen3 shows a clean improvement (2→0 fabricated percentage claims in hong_kong_game). No structural regressions, no new LLMChatErrors.

2. **Call 1 is the dominant remaining fabrication source.** haiku (run 58) and gpt-oss-20b (run 54) generate their fabricated dollar amounts and percentages in `responses[0]` (call 1), before the PR's reminder can fire. insight_claude confirmed this by reading the raw JSON structure; both code reviews pinpoint `identify_potential_levers.py:227-229` as the untouched call-1 path.

3. **Silent partial-call loss is unresolved and slightly worsened.** Three after-run raw files contain only 2 responses instead of 3 (vs. 2 before). No `LLMChatError` appears in any audited `events.jsonl`. `run_single_plan_complete` fires even for 2-of-3 runs, masking the failure.

4. **Structural compliance remains perfect.** 35/35 plans succeed, 0 wrong option counts, 0 bracket placeholders, 0 option-prefix labels. Average field lengths are within 1.17× of baseline.

5. **The PR is mechanically correct where applied.** The call-2/3 reminder is placed at the right attention-decay point, immediately after the name-exclusion blacklist.

---

## Cross-Agent Disagreements

### Disagreement 1: Improvement magnitude

- **insight_claude** reports haiku as *worse* after the PR (+4 fabricated claims in hong_kong_game: 2→6+), and gpt-oss-20b also worse (+3).
- **insight_codex** counts a net improvement overall: 22→19 unsupported percentage tokens across all five plans.

Both are correct — they measure different scopes. insight_claude examines a single plan (hong_kong_game) per model; insight_codex counts all five plans. GTA improved by 4 tokens and parasomnia by 2, which offsets the haiku regression and produces the net 22→19 result. The haiku and gpt-oss-20b regressions are real but isolated to budget-context plans. **Neither agent is wrong; the synthesis should report both.**

### Disagreement 2: PR scope vs. PR description

- **code_claude** (backed by both insight files) shows the worktree implements several changes beyond the stated "one line": (a) `Lever.consequences` field description rewritten to remove the fabrication mandate ("at least one quantitative estimate are mandatory"), (b) `check_review_format` validator replaced with a language-agnostic check, (c) `OPTIMIZE_INSTRUCTIONS` constant added, (d) call-2/3 full-sentence reminder added alongside the anti-fabrication line.
- **code_codex** focuses only on the call-2/3 reminder and treats the PR as narrower.

**Verification from source (`identify_potential_levers.py:37-44`):** The mainline `Lever.consequences` field description does include "at least one quantitative estimate are mandatory" — a direct fabrication mandate injected into every LLM call via the structured output schema. The worktree fix (conditional on project context) addresses the structural root cause. **code_claude is correct that the PR contains more than described; this is the most impactful unexplained change.**

### Disagreement 3: Short-option relapse

- **insight_claude** attributes generic short options primarily to llama3.1 (pre-existing behavior, N4).
- **insight_codex** flags 21 options under 5 words as a new post-PR regression, concentrated in run 53 (qwen3, silo plan), not llama3.1.

Metric table from insight_codex: 0 short options before, 21 after. This is a new regression, not a pre-existing pattern. **insight_codex is correct.** The llama3.1 issue (N4 in insight_claude) is about *generic lever names and low lever count*, which is separate from the short-option slogan issue in run 53.

---

## Top 5 Directions

### 1. Add anti-fabrication reminder to call-1 user prompt
- **Type**: prompt change (inline f-string in Python code)
- **Evidence**: insight_claude (N3, Q2, C1, H1), insight_codex (H1, H2), code_claude (I1), code_codex (B1, I1) — unanimous across all four agents.
- **Impact**: Directly targets the confirmed source of haiku run 58 (6+ fabrications in `responses[0]`) and gpt-oss-20b run 54 (5 fabrications in `responses[0]`). Call-1 generates 5–7 levers per run (first third of all levers). A reminder there uses the same proven attention-decay mechanism as PR #309 and #313. Expected to reduce haiku and gpt-oss-20b fabrication in budget-context plans (hong_kong_game) without affecting other plans. Cross-plan: insight_codex finds silo also still has fabrication (6 tokens after vs. 3 before), and parasomnia still has 5 tokens — both potentially addressable with a call-1 reminder.
- **Effort**: Low — one appended string, same code path pattern as PR #313.
- **Risk**: Minimal. Adding a qualitative reminder to call 1 mirrors a prohibition already in the system prompt. Confirmed safe by the PR #309 and #313 precedents.

### 2. Extend the fabrication prohibition with explicit derived-partitioning language
- **Type**: prompt change (wording improvement to the reminder text)
- **Evidence**: insight_codex (H2, Reflect), code_codex (I1). Specific pattern: models see a real total budget (HK$470m) or range (`70–80%`) and invent allocation sub-percentages or stricter thresholds that are mathematically adjacent to the real number. The current generic "do not invent percentages" text has not suppressed this pattern in haiku or gpt-oss-20b.
- **Impact**: Targets the specific failure mode that survived both the system prompt prohibition and PR #313. A more precise rule ("if the plan mentions a total budget, do not derive allocation percentages from it; if the plan gives a range, do not invent a stricter threshold") gives models an explicit decision rule rather than a general aspiration. Also worth adding to `OPTIMIZE_INSTRUCTIONS` as a documented known pitfall.
- **Effort**: Low — wording change only, pairs naturally with Direction 1.
- **Risk**: Low. More specific language is less likely to be ignored than generic language, and the risk of overcorrection (refusing to mention any numbers) is minimal given the qualifier "unless the project document supplies the exact number."

### 3. Add a numeric-grounding post-generation audit (warning-only)
- **Type**: code fix (new scan in `IdentifyPotentialLevers.execute()`)
- **Evidence**: code_claude (I2, C2), code_codex (I2), insight_codex (C1).
- **Impact**: Makes fabrication regressions immediately visible in logs without triggering expensive retries. Scan `levers_cleaned` for `\d+%` and currency patterns (`\$\d`, `HK\$`, `US\$`); emit `logger.warning` for each token not found verbatim in `user_prompt`. This audit would have automatically flagged every fabrication found by the post-hoc analyses — a repeating manual cost that scales with iteration count. Adding it once eliminates the measurement burden from future synthesis cycles. Unlike a validator rejection, a warning-only approach has zero retry cost.
- **Effort**: Low — a dozen lines added to `execute()` after `levers_cleaned` is assembled.
- **Risk**: False positives if a model paraphrases a number from the source (e.g., "HK$470m" appearing as "$470 million") but these would produce spurious warnings, not rejections, and could be tuned.

### 4. Add partial-call-loss observability (structured telemetry)
- **Type**: code fix (touches `identify_potential_levers.py` and `runner.py`)
- **Evidence**: code_claude (B3, I3), code_codex (B2, I4), insight_codex (C3). Three raw files have only 2 responses in the after batch; `events.jsonl` shows no signal.
- **Impact**: The silent partial-call loss is currently indistinguishable from a full 3-call run. Adding a `completed_calls: int` field to `IdentifyPotentialLevers` and emitting a `run_single_plan_partial` event from `runner.py` (instead of the misleading clean `run_single_plan_complete`) would make this observable from artifacts alone. This also eliminates the manual "count responses in raw JSON" work done by insight_codex. Slightly worsened (2→3 affected plans in after batch) so the gap is growing.
- **Effort**: Medium — two files, but minimal logic change. `IdentifyPotentialLevers` already has `responses: list[DocumentDetails]` so `completed_calls = len(responses)` is trivial; the event emission in `runner.py` requires a conditional.
- **Risk**: Low. Pure observability change; no effect on output content.

### 5. Add option-quality warning validator (minimum word count)
- **Type**: code fix (post-generation warning in `execute()`)
- **Evidence**: code_claude (I4), code_codex (B3, I3), insight_codex (C2). 21 options under 5 words in the after batch (0 before). All concentrated in run 53 (qwen3, silo). Examples: "Implement multi-layered structural reinforcement", "Deploy AI-driven monitoring" — slogans, not strategic sentences.
- **Impact**: Catch option-quality regression immediately in logs rather than discovering it in post-hoc synthesis. A `logger.warning` for options with fewer than 8 words preserves the no-retry guarantee while making the failure observable. Aligns with `OPTIMIZE_INSTRUCTIONS` prohibition on "a slogan" outputs. Unlike a hard Pydantic validator (which would trigger expensive retries), a warning-only check preserves the partial-success behavior added in PR #268.
- **Effort**: Low — a few lines after `levers_cleaned` is assembled, similar to Direction 3.
- **Risk**: Minimal. A warning does not alter output; a high false-alarm rate (e.g., legitimately short strategic options) would be easy to tune by adjusting the threshold.

---

## Recommendation

**Pursue Direction 1 first: add the anti-fabrication reminder to the call-1 user prompt, with Direction 2's specific derived-partitioning language included.**

This is the single highest-leverage next step because:
- All four analysis agents independently identify it as the dominant remaining fabrication source.
- Raw output structure (confirmed by insight_claude reading `002-9-potential_levers_raw.json`) places haiku's dollar fabrications at `responses[0]`, call 1 — outside the current PR's scope.
- It follows the proven attention-decay reinforcement mechanism (PR #309 fixed call-3 label degradation for llama3.1; PR #313 fixed call-2/3 percentage fabrication for qwen3). Same mechanism, one more callsite.
- It is a one- or two-line change with zero structural risk.

**Exact change** — file `identify_potential_levers.py`, the call-1 branch at lines 227–229:

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

The first sentence mirrors the call-2/3 reminder from PR #313 (proven wording). The second sentence adds the derived-partitioning explicit prohibition that insight_codex and code_codex identify as the specific failure pattern not suppressed by the generic rule.

**Also add the derived-partitioning pattern to `OPTIMIZE_INSTRUCTIONS`** as a documented known pitfall (already partially present in the worktree as "fabricated numbers" but not specific enough to capture the "HK$470m → 30%/20%/15% splits" and "70–80% range → 90% threshold" patterns).

---

## Deferred Items

**D1: Numeric-grounding post-generation audit (Direction 3)**
High analytical value; eliminates repeating manual measurement work in future iterations. Defer only because it is diagnostic rather than corrective — the prompt fix (Direction 1) should come first to reduce the fabrication rate, then the audit to verify it.

**D2: Partial-call-loss observability (Direction 4)**
The gap is real and worsening. Schedule for the iteration after the call-1 reminder is validated. Requires touching `runner.py`, which increases review scope; keep separate from the prompt-only Direction 1 change.

**D3: Option-quality warning validator (Direction 5)**
The run-53 short-option relapse (21 options) has not recurred in other runs. A warning-only guard is worth adding but is lower priority than fabrication reduction.

**D4: `set_usage_metrics_path` race condition (code_claude B4)**
Real thread-safety bug in `runner.py:106/140` — `set_usage_metrics_path` is called outside the `_file_lock`. In parallel mode this can corrupt usage metrics. Low-severity in practice (metrics are observational, not functional), but worth fixing before scaling parallel runs. Not addressed by PR #313.

**D5: Language-agnostic `check_review_format` validator (code_claude B2)**
The mainline still uses English-only substring matching (`'Controls '`, `'Weakness:'`). The worktree PR #313 fixes this with structural checks. This fix ships with the PR; no separate action needed.

**D6: Semantic near-duplicate lever detection**
Both code reviews (S1/S2) flag the name-only dedup as insufficient for semantic near-duplicates ("Festival Strategy for Critical Reception" / "Festival Strategy for Audience Engagement"). The module docstring correctly defers this to `deduplicate_levers.py`. Worth verifying whether the downstream dedup catches these before investing in a call-level fix.

**D7: Per-call prompt fingerprinting in run metadata (code_codex I5, S2)**
The runner records `system_prompt_sha256` but not the dynamically assembled call-2/3 user prompt hash or the git commit. This made PR #313 harder to audit (same SHA before and after). Low priority but would improve future experiment reproducibility with minimal effort.
