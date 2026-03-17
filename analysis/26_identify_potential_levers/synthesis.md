# Synthesis

## Cross-Agent Agreement

Only one insight agent (claude) and one code review agent (claude) were produced for this analysis round. There are no inter-agent disagreements to resolve. The two artifacts are strongly consistent and mutually reinforcing:

- Both agree **PR #337 verdict: KEEP**. Primary template locks broken (llama3.1: 100% → 0%; qwen3: ~100% → 6%), no success-rate regression, no content-quality regression.
- Both independently identify **B2** (copyable subphrases in replacement examples seeding a secondary lock at 76% in llama3.1) as the most important residual problem.
- Both flag **B1** (`min_length=20` inadequate after the verbose template was removed) as the second priority.
- Both note **S3** (`LeverCleaned.review` field description is dead code, never seen by any LLM).
- The code review additionally surfaces **B3** (global dispatcher cross-contamination in concurrent-worker runs), which the insight file does not address.

## Cross-Agent Disagreements

None. Single agent pair; no contradictions.

Source code verification confirms all key claims:
- `check_review_format` validator at line 151: threshold is `len(v) < 20` — confirmed too low (B1).
- `Lever.review_lever` field description at lines 99–112: three examples present, two contain "the options neglect" (insurance) and "the options assume" (urban planning) — confirmed (B2).
- `LeverCleaned` class at lines 170–211: instantiated only at lines 352–358 by Python code, never serialized for LLM schema — confirmed dead code (S3).
- `check_option_count` docstring at line 132 says "Run 89" but the 2-option error occurred in run 82 — confirmed wrong (S1).
- `runner.py` global dispatcher pattern at lines 106–109, 146–148: `track_activity` added to shared singleton inside `_file_lock`, but event delivery is unlocked and cross-thread — confirmed (B3).

## Top 5 Directions

### 1. Remove copyable subphrases from examples and add a positive diversity constraint (B2 + I2)
- **Type**: prompt change (field description + system prompt)
- **Evidence**: Code review B2, I2; insight C1. Run 89 shows 13/17 llama3.1 reviews (76%) using "The options assume/neglect/overlook" — a direct copy of the exact phrases in the urban-planning ("the options assume") and insurance ("the options neglect") examples introduced by PR #337. The PR broke the sentence-level template but seeded two phrase-level templates in the replacements.
- **Impact**: Affects all models on every plan. Fixing the phrase-level seeds reduces the secondary lock in llama3.1. Adding a positive diversity constraint ("each review must address exactly one risk category: production feasibility, stakeholder conflict, financial viability, technical constraint, or audience reception") prevents template-lock migration to a third pattern by prescribing content rather than only proscribing form. This is the class of fix that OPTIMIZE_INSTRUCTIONS now recommends: "prefer positive diversity constraints."
- **Effort**: Low — edit the three example sentences in `Lever.review_lever` field description (lines 99–112) and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (lines 234–239) to remove "the options assume" and "the options neglect" from the example text; add one positive-constraint sentence to each location. `LeverCleaned.review` update is optional (dead code).
- **Risk**: Positive constraint wording could be too prescriptive for some domains, or the risk-category list may not map well to non-business projects. Mitigated by keeping the list broad (5 categories).

### 2. Raise `review_lever` min_length to 50 characters (B1 + I1)
- **Type**: code fix
- **Evidence**: Code review B1, I1; insight C2, negative finding #3. Run 89 parasomnia failure: `review_lever is too short (19 chars)` — "Sensor Data Sharing" passed as a review. Current threshold of 20 chars allows any short label (e.g., "Weak lever, skip this." = 22 chars) to pass silently.
- **Impact**: Affects all models. The old verbose template ("This lever governs the tension between…") incidentally guaranteed length. Without it, llama3.1 can produce degenerate single-phrase reviews. A 50-char floor requires at minimum a partial sentence with subject + verb + object, which filters the most degenerate cases. This is a cheap code fix with no prompt cost.
- **Effort**: Trivial — one line change at `identify_potential_levers.py:151`.
- **Risk**: Could raise failure rate for llama3.1 on very short degenerate outputs, shifting the failure mode again. But this is the desired behavior: reject degenerate output early rather than silently pass it downstream. Risk of increasing error rate for already-failing plans is negligible (llama3.1 already fails 1/5 plans).

### 3. Add negative constraint blocking "The options assume/neglect/overlook" openers (I3)
- **Type**: prompt change (field description + system prompt)
- **Evidence**: Code review I3; insight C3. 13/17 reviews in run 89 hong_kong_game use this opener.
- **Impact**: Directly addresses the secondary lock. Even if the example subphrases are fixed (direction 1), a negative constraint provides a second line of defense for models that have seen enough "the options assume" training data to generate it independently. Low cost — one sentence added to the prohibitions section.
- **Effort**: Low — add to `Lever.review_lever` field description and system-prompt section 4 prohibitions: `"Do NOT open with 'The options assume', 'The options neglect', or 'The options overlook'."`
- **Risk**: As noted in insight Q5 and OPTIMIZE_INSTRUCTIONS theory, negative-only constraints may trigger a third shift. Should be paired with direction 1 (positive constraint) rather than used alone.

### 4. Document template-lock migration in OPTIMIZE_INSTRUCTIONS (I5)
- **Type**: code change (documentation constant)
- **Evidence**: Code review I5; insight "New recurring problem not yet in OPTIMIZE_INSTRUCTIONS" section. Template-lock migration (one anchor removed → model fills vacuum with next-most-salient pattern) is now confirmed across two iterations: PR #268 removed options-count errors, PR #337 shifted the lock from "This lever governs" to "The options assume". It is a repeating pattern.
- **Impact**: Affects future optimization decisions. OPTIMIZE_INSTRUCTIONS is read by the self-improvement pipeline (see `OPTIMIZE_INSTRUCTIONS` constant usage), and its documented failure classes inform both automated analysis prompts and human reviewers. Adding this entry prevents the next analyst from treating a secondary lock as a novel discovery and proposing another pure negative-constraint fix.
- **Effort**: Low — append one bullet point to the "Known problems" section of `OPTIMIZE_INSTRUCTIONS` at `identify_potential_levers.py:27–73`.
- **Risk**: None. Documentation change only.

### 5. Fix global dispatcher cross-contamination in concurrent-worker runs (B3)
- **Type**: code fix (runner)
- **Evidence**: Code review B3. `self_improve/runner.py:106–109` — `track_activity` handler added to the global LlamaIndex dispatcher singleton inside `_file_lock`, but event delivery happens outside the lock across all threads. Result: per-plan `track_activity.jsonl` files receive events from all concurrent workers.
- **Impact**: Affects any run with `workers > 1`. Does not affect prompt output quality or success rate, but corrupts per-plan usage metrics (token counts, latency) that feed into cost analysis. For the current optimization loop running single-worker batches, this bug is dormant. For future parallel runs, it is a correctness issue.
- **Effort**: Medium — requires either making `track_activity` thread-local (e.g., thread-local storage keyed to `plan_output_dir`) or restructuring the dispatcher subscription to be scoped per-worker thread rather than global.
- **Risk**: LlamaIndex's dispatcher API may not support per-thread or per-context subscriptions cleanly. Incorrect fix could suppress all tracking. Needs careful testing.

## Recommendation

**Pursue direction 1 (B2 + I2) first: rewrite the three example sentences to remove copyable "the options assume/neglect" subphrases, and add a positive diversity constraint.**

This is the highest-leverage change because:
1. **It addresses the root cause** of the secondary template lock (76% rate in llama3.1 run 89), not just its symptom.
2. **It benefits all models on all plans** — a positive constraint that prescribes which risk dimension each review must address eliminates the stylistic vacuum that weaker models fill with formulaic patterns, regardless of which examples are present.
3. **It aligns with OPTIMIZE_INSTRUCTIONS** — the documented lesson from iteration 2 is that positive diversity constraints are preferable to negative example replacement. This change embodies that principle.
4. **It is low effort** — two locations need editing: `Lever.review_lever` field description and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4. The `LeverCleaned.review` field description is dead code and can be skipped or minimized separately.

**Specific change:**

**Location 1 — `Lever.review_lever` field description (`identify_potential_levers.py:96–112`):**

Replace the three example sentences while keeping the structural instruction. Edit the insurance example to remove "the options neglect" and the urban-planning example to remove "the options assume". Also add a positive constraint sentence. New field description:

```python
review_lever: str = Field(
    description=(
        "A short critical review of this lever — name the core tension, "
        "then identify a specific risk the options miss. "
        "Each review must address exactly one risk type not already covered in the "
        "consequences field — choose from: production feasibility, stakeholder conflict, "
        "financial viability, technical constraint, or audience reception. "
        "Examples: "
        "'Switching from seasonal contract labor to year-round employees stabilizes harvest "
        "quality, but the idle-wage burden during the 5-month off-season is unpriced in all "
        "three options — this financial gap could make the shift cash-flow negative in year 1.' "
        "'Routing the light-rail extension through the historic district unlocks ridership, but "
        "all three options treat heritage review as a formality; Section 106 proceedings have "
        "delayed comparable projects by 18–36 months in other cities.' "
        "'Pooling catastrophe risk across three coastal regions reduces volatility in normal years, "
        "but a single major hurricane season can correlate all three regions simultaneously — "
        "a risk the options treat as independent when it is not.' "
        "Do not use square brackets or placeholder text."
    )
)
```

**Location 2 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (`identify_potential_levers.py:233–239`):**

Apply the same changes (remove "the options assume/neglect" from examples, add the positive risk-category constraint sentence) to match the field description exactly. Also add a prohibition bullet: `"- Do NOT open with 'The options assume', 'The options neglect', or 'The options overlook' — these are formulaic openers."` under section 5 (Prohibitions).

This single PR covers directions 1 and 3 together (the prohibition is a cheap addition alongside the example rewrite), and should be combined with direction 2 (raise `min_length` to 50) since all three edits are in the same file and low-risk.

## Deferred Items

- **Direction 4 (I5 — OPTIMIZE_INSTRUCTIONS documentation):** Low effort and zero risk, worth adding to the same PR as the primary fix but not a blocker on its own.
- **Direction 5 (B3 — dispatcher cross-contamination):** Deferred until concurrent-worker runs are actively used. Does not affect prompt quality or single-worker analysis batches.
- **S1 — Docstring wrong run number:** Trivial cosmetic fix — the `check_option_count` docstring at line 132 says "Run 89" but the 2-option error was in run 82. Fix in passing when editing the file.
- **S3 — LeverCleaned.review dead code:** The field description at lines 195–211 is never seen by any LLM. Options: (a) strip the three examples and replace with a brief human-readable note (`description="Critical review, copied from Lever.review_lever."`), or (b) leave as-is. Either is fine. Stripping prevents future confusion about which copy is "live".
- **S2 — Bucket arithmetic comment:** Worth a one-line comment near `runner.py:294` documenting the 100-slot-per-bucket limit. No code change needed.
- **qwen3 "Core tension:" residual in non-hong_kong_game plans (insight Q2):** Not yet verified in sovereign_identity and parasomnia for run 92. Should be sampled in the next analysis round to confirm the PR fully resolved this pattern across all plans, not just hong_kong_game.
- **Duplicate review mechanism (insight Q3):** llama3.1 produced identical reviews for two different levers in run 89. No structural uniqueness check exists. A content-level deduplication step (e.g., hash-based check across reviews in the same response) would catch this, but is lower priority than preventing the template lock that causes it.
