# Synthesis

## Cross-Agent Agreement

**Both insight agents agree on positives:**
- Prompt_6 eliminates round-number fabrications vs baseline across all runs (runs 60–65): zero fabricated round percentages (vs 40+ in baseline).
- No marketing language ("game-changing", "revolutionary") in any of the 7 runs.
- No schema validation failures (LLMChatError); removing `max_length=7` was correct.
- Run 60 (llama3.1) is the weakest: partial recovery on 2/5 plans, semantic duplication, terse/label-like options.

**Both insight agents agree on problems:**
- Review formula monoculture: 82–106 of 91–108 reviews per run begin with "This lever governs…".
- Semantic duplication in run 60 sovereign_identity (58% uniqueness ratio) is caused by name-only anti-repetition in the inter-call prompt.
- Option verbosity range is wide: ~55 chars (llama3.1 labels) to ~290 chars (haiku run 66 verbose sentences).

**Both code review agents agree:**
- Race condition: `set_usage_metrics_path` is called outside `_file_lock` in `runner.py:107,150`, corrupting usage metrics for all parallel runs (61–66, 4 workers). Confirmed by reading the code.
- Per-call failures are not emitted to `events.jsonl`; only `logger` output and a coarse `partial_recovery` count survive.
- Concept-level anti-repetition is needed in the inter-call prompt (currently blocks only exact names).
- Conservative-path requirement from `OPTIMIZE_INSTRUCTIONS` is not present in the active system prompt.
- Single review example anchors all models to identical openings.

---

## Cross-Agent Disagreements

### Run 66 (haiku) quality tier

**insight_claude**: "BEST" tier — outputs are specific, grounded in project context (HK$470M budget, TIFF/BIFF festivals, 8–10 week schedule), semantically unique (21 levers, 100% distinct). Calls fabricated-percentage count "zero."

**insight_codex**: "F-tier" — major content-quality regression with 16 unsupported numeric claims: `60–70% of principal photography`, `40–50% of budget`, `51%/49% equity split`, `3–5% interest rate`, `estimated 40% throughput reduction`.

**Verdict: insight_codex is correct.** The insight_claude reviewer scanned for round-number fabrications (15%, 20%, 30%) but missed the "precision theater" pattern — pseudo-precise operational ranges and splits that are equally fabricated. Both code reviewers independently flag this pattern: code_claude I4 cites the exact same run 66 examples ("60–70% of principal photography", "40–50% of budget"), and code_codex I5 calls for a post-parse numeric audit. OPTIMIZE_INSTRUCTIONS already prohibits "fabricated numbers" but does not name or describe precision theater by example, which is why haiku passes the current prohibition and still generates unsupported thresholds.

### Two-sentence review compliance

**insight_codex** reports near-zero compliance in runs 60, 63, 64 (measures sentences by counting periods; run 60: 0/91, run 64: 5/83).

**code_codex (B1)** explains why: the Pydantic field description at `identify_potential_levers.py:92–98` says "two sentences" but the only example is a single sentence ("This lever governs… but the options overlook…"). The system prompt at lines 214–218 repeats the same contradiction. Models follow the example shape, not the sentence-count claim.

**insight_claude** notes the formula repetition but does not identify the contradictory contract as the root cause.

**Verdict: code_codex is correct.** The "two sentences" requirement is a broken contract because the provided example is one sentence. This explains why all 7 runs converge on one long sentence rather than two.

---

## Top 5 Directions

### 1. Strengthen anti-fabrication prohibition to cover precision theater
- **Type**: prompt change (`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` in `identify_potential_levers.py` + prompt_6 text file + `OPTIMIZE_INSTRUCTIONS`)
- **Evidence**: insight_codex F-tier for run 66 (16 unsupported % claims across all 5 plans); code_claude I4; code_codex I5; run 63 also has 3 precision-theater claims ("Allocate 70%…", "Secure 100% government funding…", "90% event capture rate"). The current prohibition "NO fabricated statistics or percentages without evidence" is insufficient — haiku and qwen3 comply literally (they don't use round numbers) while still generating unsupported operational specifics.
- **Impact**: Run 66 (haiku) accounts for 108 levers across 5 plans — the largest lever pool of any run. Run 63 (qwen3) also affected. Precision theater numbers erode plan credibility at scale, potentially for any strong model. A tighter prohibition would benefit all future haiku/qwen3 runs.
- **Effort**: Low — 2–3 sentences added to Prohibitions section in both the prompt file and `OPTIMIZE_INSTRUCTIONS`.
- **Risk**: Low. Makes explicit what the current wording implies but fails to enforce. May slightly reduce option specificity, but models retain full freedom to use qualitative language.

### 2. Concept-level anti-repetition in inter-call prompt
- **Type**: code change (`identify_potential_levers.py:269–276`)
- **Evidence**: insight_claude N1/C1 (run 60 sovereign_identity: 4 "Digital Identity Standards…" variants), code_claude I1, code_codex I4/S1. Both code reviewers propose the same 3-line fix. Confirmed by reading lines 269–276: the exclusion list is names only (`f"Do NOT reuse any of these already-generated names: [{names_list}]"`).
- **Impact**: Reduces pre-dedup semantic bloat for all models, especially weaker ones. Run 60 sovereignty plan yielded 24 levers with 58% uniqueness; fixing this at the source reduces wasted calls and downstream dedup burden. Secondary benefit: if DeduplicateLeversTask has a loose threshold, concept-level duplicates currently slip through.
- **Effort**: Very low — change 2 lines in one function in `identify_potential_levers.py`.
- **Risk**: Very low. Downstream semantic dedup still runs regardless.

### 3. Fix contradictory review contract (add diverse two-sentence examples)
- **Type**: code change (`identify_potential_levers.py:92–98` Pydantic field description and `identify_potential_levers.py:214–218` system prompt constant)
- **Evidence**: code_codex B1 (schema contradiction: claims two sentences, gives one-sentence example); code_claude I2 (single example causes template takeover); insight_codex H1 + quantitative data (82–106 of 91–108 reviews per run start identically "This lever governs…"). Confirmed: prompt_6 line 22 shows "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs" — one sentence, despite "two sentences" claim.
- **Impact**: Affects all 7 runs equally — ~650 total reviews. Downstream `EnrichLevers` and `FocusOnVitalFewLevers` consume the review field; monoculture reduces the analytical signal. Fixing the example also makes the contract honest.
- **Effort**: Very low — replace one example with 2–3 stylistically varied two-sentence examples.
- **Risk**: Negligible. The structural validator (min 20 chars, no `[…]`) is unaffected.

### 4. Add conservative-path requirement to active system prompt
- **Type**: prompt change (prompt_6 text file, "Options MUST" section + inter-call prompt in `identify_potential_levers.py:270–276`)
- **Evidence**: insight_claude N5/H2 (run 60 silo: only hybrid/balanced options, no genuine conservative baseline); code_claude I3; code_codex B4+I6. `OPTIMIZE_INSTRUCTIONS` lines 48–52 explicitly requires "at least one conservative, low-risk path" but the active system prompt asks only for "at least one unconventional or non-obvious approach" — the opposite direction.
- **Impact**: Downstream `ScenarioGeneration` and `ScenarioSelection` tend to pick the most ambitious scenario. Without conservative options in the lever pool, there is no low-risk scenario to select. Fixing this aligns the prompt with `OPTIMIZE_INSTRUCTIONS`' stated goal and improves scenario diversity across all models.
- **Effort**: Low — add one clause to the "Options MUST" list in prompt_6 and one sentence to the inter-call prompt.
- **Risk**: Low. Slight risk that weaker models over-correct and produce passive/do-nothing options, but the system prompt's "concrete, actionable approach" requirement mitigates this.

### 5. Fix race condition: `set_usage_metrics_path` outside `_file_lock`
- **Type**: code fix (`runner.py:107, 150`)
- **Evidence**: code_claude B1 (confirmed by reading `runner.py`). Lines 107 and 150 call `set_usage_metrics_path` outside the `_file_lock` context manager that protects the dispatcher. The comment at lines 98–100 says the lock prevents cross-thread interference, but the code does not enforce it. Parallel runs (61–66 all use 4 workers) can have Thread A's metrics written to Thread B's file, or the path cleared while Thread B's LLM calls are in flight.
- **Impact**: Corrupts `usage_metrics.jsonl` for all parallel runs, making telemetry-based diagnosis unreliable. Run 60's failures were only visible in `usage_metrics.jsonl` (insight_codex evidence note), but if metrics are written to the wrong file in parallel runs, even that signal is lost. Does not affect plan content quality.
- **Effort**: Medium — needs the `set_usage_metrics_path` calls and the `IdentifyPotentialLevers.execute()` call to be enclosed within `_file_lock`, or `set_usage_metrics_path` refactored to use thread-local storage rather than a module global.
- **Risk**: Medium — touching threading/locking code in a production path. Needs careful review to avoid deadlocks.

---

## Recommendation

**Pursue Direction 1: Strengthen anti-fabrication prohibition to cover precision theater.**

**Why first**: Run 66 (haiku) passed all structural validation and produced 108 levers — the largest output of any run — yet 16 of them contain fabricated operational specifics that undermine plan credibility. The content quality guidance says fabricated-number regressions affecting many plans outweigh structural fixes. This is exactly that case: haiku is a strong, widely-used model, and the regression affects all 5 plans in the run. Fixing the prompt wording costs almost nothing and is testable by re-running any haiku plan.

The current prohibition ("NO fabricated statistics or percentages without evidence from the project context") is too narrow. Haiku interprets it as "avoid round-number claims" and substitutes pseudo-precise operational ranges that are equally groundless. Naming the pattern explicitly closes this gap.

**What to change — three locations:**

**Location 1**: `OPTIMIZE_INSTRUCTIONS` in `identify_potential_levers.py`, after line 57 (end of the "Fabricated numbers" bullet). Add a new bullet:

```
- Precision theater. Models sometimes avoid round-number hype while still fabricating
  pseudo-precise operational thresholds: budget splits ("40–50% of budget"), equity
  percentages ("51%/49% equity"), throughput estimates ("estimated 40% throughput
  reduction"), or interest rates ("3–5% interest"). These are as fabricated as
  "15% market-share growth" and violate the same prohibition. The rule is: if the
  exact figure does not appear verbatim in the project context, do not use it.
```

**Location 2**: `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` in `identify_potential_levers.py`, Prohibitions section (around line 227). Replace:

```
   - NO fabricated statistics or percentages without evidence from the project context
```

with:

```
   - NO fabricated or derived numbers of any kind: percentages, ranges, budget splits,
     equity percentages, probability thresholds, throughput figures, or interest rates —
     unless the exact figure appears verbatim in the project context. "60–70% of budget"
     and "51%/49% equity" are fabricated operational specifics, not grounded analysis.
```

**Location 3**: `prompts/identify_potential_levers/prompt_6_4669...txt`, Prohibitions section (line 32). Apply the same replacement as Location 2 (since the system prompt constant and prompt file are kept in sync).

**Why not Direction 2 first**: Concept-level anti-repetition (Direction 2) is a 3-line code change with clear benefit, but it primarily helps weaker models (llama3.1) and is a pre-dedup improvement — the downstream `DeduplicateLeversTask` already handles semantic duplicates. Direction 1 fixes a content quality regression in a strong model (haiku) that downstream dedup cannot fix (fabricated numbers are not duplicates; they pass all filters).

---

## Deferred Items

**Direction 2 (concept-level anti-rep)**: Should follow Direction 1. Very low-effort, improves pre-dedup quality for all models. Exact proposed wording from code_claude I1:

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers covering entirely different strategic topics and concepts. "
    f"Do NOT generate a lever that addresses the same topic as any of these — "
    f"even under a different name: [{topic_summary}]\n"
    ...
)
```

**Direction 3 (review contract fix)**: Replace the single example in `identify_potential_levers.py:95` and `identify_potential_levers.py:217` with 2–3 varied two-sentence examples. Low-effort, affects all runs. Suggested fix from code_claude I2: add "Vary your review opening — do not begin every review with 'This lever governs'."

**Direction 4 (conservative path in system prompt)**: Add to prompt_6 "Options MUST" list: "• Include at least one explicitly conservative, low-risk approach — not just a 'balanced' or 'hybrid' middle ground." Also add the same line to the inter-call prompt in `identify_potential_levers.py:270–276`.

**Direction 5 (race condition)**: Fix `set_usage_metrics_path` threading in `runner.py`. Important for telemetry integrity but does not affect plan content quality. Consider refactoring to thread-local storage to avoid lock scope expansion.

**code_codex I7 (effective prompt fingerprint)**: Record a hash of the inline inter-call prompt template in `runner.py:381–387` alongside `system_prompt_sha256`. Currently, code changes to the inter-call wording (lines 269–275) change model behavior without changing `meta.json`, making prompt-lab history harder to audit.

**code_codex B3 (option length floor)**: Add a structural validator that flags options below a character floor (e.g., 60 chars) or lacking internal spacing typical of a sentence. Language-agnostic per `OPTIMIZE_INSTRUCTIONS`. Lower priority since the inter-call prompt already states "at least 15 words with an action verb."
