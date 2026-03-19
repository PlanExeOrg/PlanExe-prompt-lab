# Synthesis

## Cross-Agent Agreement

Only one insight agent (claude) and one code-review agent (claude) ran for this analysis — no Codex agent. Both files originate from the same model, so "cross-agent agreement" here means consistency between the quality analysis and the code review.

The two files agree strongly on:

- **PR #353 verdict: KEEP.** The grammatical-subject fix ("the options" → domain-specific mechanism) is the right intervention. It correctly halved llama3.1 template lock (~85% → ~40%) and eliminated the worst single-plan failures (silo 94%→0%, hong_kong exact-duplicate reviews gone, plan success rate 97.1%→100%).
- **Root cause of remaining lock: domain monoculture.** All three new examples are from construction/agriculture/insurance. Parasomnia (medical) and gta_game (video-game) plans did not benefit proportionately because the structural patterns don't transfer.
- **Structural homogeneity of examples (S3).** Examples 1 and 3 both use the "X improves Y, but Z reverses the gain" template. Example 2 uses the same adversarial contrast. A model that copies the contrast structure instead of the specific words will produce secondary lock — exactly what is observed in parasomnia's second LLM call ("the lever misses/overlooks").
- **Section 5 missing explicit prohibition (I4).** The PR removed options-centric examples but added no direct negative instruction forbidding "The options overlook", "These options", or "The lever misses" as openers. Models can shift to synonyms without being blocked.
- **B1 (false partial_recovery) is confirmed pre-existing.** `runner.py:115` hardcodes `expected_calls = 3`; `runner.py:514` emits `partial_recovery` for any `calls_succeeded < 3`. If haiku hit `min_levers = 15` in 2 calls (possible with a model that returns 8+ levers per call), it would emit a false alarm. The haiku "regression" in run 58 is ambiguous.
- **S1 and S2: dead fields burn tokens.** `lever_index` is generated but immediately discarded; `strategic_rationale` generates ~100 words per call (105 calls/iteration ≈ 10,500 wasted words) and is never consumed downstream.

---

## Cross-Agent Disagreements

No substantive disagreements between files. The insight attributes the haiku partial-recovery regression primarily to non-deterministic behavior; the code review notes B1 could explain it as a false alarm. These are compatible: the events.jsonl shows `status: ok` for both plans, which is consistent with early-success completions being mislabeled as partial recoveries.

One minor tension: the insight frames the "The plan's emphasis on X may overlook Y" hong_kong_game pattern as a "new secondary template lock" (negative), while the code review treats it as acceptable because X is domain-specific. Source-code reading confirms both are right: the sentence skeleton is reusable (negative), but the domain-specific X values mean each review carries genuinely different content (partially positive). This is a lesser problem than "the options overlook."

---

## Top 5 Directions

### 1. Add domain-diverse `review_lever` examples (and structural variety)
- **Type**: prompt change
- **Evidence**: insight H1, code review I3, S3. Agreed by both files. Confirmed in source: lines 225–227 of `identify_potential_levers.py` show all three current examples are from real-estate/agricultural/catastrophe-insurance domains. The model explanation is sound: parasomnia and gta_game don't benefit because the structural patterns (seasonal labor, heritage permits, hurricane correlation) don't map to medical research or video-game contexts.
- **Impact**: Affects the two remaining high-lock plans for llama3.1 (parasomnia ~82%, gta_game ~78%). Expected to reduce both toward <50%. Also breaks structural homogeneity (S3): adding one example that does NOT use the "X but Z reverses the gain" adversarial form gives weaker models a second rhetorical template to draw from, reducing secondary lock in multi-call runs.
- **Effort**: Low — replace one or two of the three examples, or add a fourth. No code changes.
- **Risk**: A poorly chosen medical/tech example could create its own template lock. Mitigation: ensure the new examples are structurally distinct from one another (e.g., one that names a compounding schedule risk without a simple "but" reversal, one that names a combinatorial state explosion without a seasonal metaphor).

### 2. Add explicit prohibition for template-lock openers in section 5
- **Type**: prompt change
- **Evidence**: code review I4, insight H2. Section 5 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (lines 230–235) lists prohibitions (no prefixes, no marketing language, etc.) but does not forbid "The options overlook", "These options", or "The lever misses" as openers. Without a direct negative instruction, models shift to synonyms of the banned example pattern.
- **Impact**: Provides a direct safety net independent of example diversity. Even if a model doesn't generalize well from new examples, an explicit prohibition can stop the most obvious template-lock openers. Affects all models, but especially weaker ones (llama3.1, gpt-oss-20b) that are most prone to pattern-copying.
- **Effort**: Very low — one bullet added to section 5.
- **Risk**: Extremely low. Adding a prohibition has no downside unless the wording accidentally bans legitimate review openings (unlikely given the specificity of "the options/lever" as grammatical subject).

### 3. Fix B1: distinguish true `partial_recovery` from early-success completion
- **Type**: code fix
- **Evidence**: code review B1, confirmed by grep (`runner.py:115` hardcodes `expected_calls = 3`, `runner.py:514` emits `partial_recovery` for any `calls_succeeded < 3`). The haiku "regression" in run 58 (0 → 2 partial-recovery events, both plans `status: ok`) is the immediate observable consequence: it is currently impossible to tell whether haiku truly failed a call or simply hit `min_levers = 15` in 2 successful calls.
- **Impact**: Affects all models; fixes misleading metrics that make it impossible to measure actual failure rates. If the haiku events are false alarms, the "regression" in run 58 disappears, clarifying the PR's true impact. A code fix (unlike a prompt change) benefits all models uniformly and permanently.
- **Effort**: Medium. `IdentifyPotentialLevers.execute()` needs to track a `failed_calls` counter separately from `calls_succeeded`. `runner.py` then emits `partial_recovery` only when `failed_calls > 0`.
- **Risk**: Low. The fix is additive: the `calls_succeeded` counter stays for backward compatibility; `failed_calls` is a new field. The `partial_recovery` event semantics become accurate rather than ambiguous.

### 4. Add soft validator for template-lock detection in `check_review_format`
- **Type**: code fix (observability)
- **Evidence**: code review I1, insight C1. Current `check_review_format` validator (lines 139–155) only checks min length (10 chars) and absence of square brackets. No signal is emitted when the model is in a template-lock state. Adding a logged warning (not raised) when `review_lever` starts with "the options", "these options", "the lever", or "these levers" (case-insensitive) would make the lock rate visible in production logs without affecting success rate or retry cost.
- **Impact**: Does not fix the problem but makes it measurable. After adding I3 and I4 (prompt changes), this validator provides the quantitative feedback loop to verify whether the next iteration actually reduced lock. Without it, the only way to measure lock rate is to manually read output JSON files (as the insight agent did).
- **Effort**: Very low — add ~4 lines to `check_review_format`.
- **Risk**: None for correctness; the log warning does not raise or block.

### 5. Remove `lever_index` and `strategic_rationale` dead fields
- **Type**: code fix (token cost)
- **Evidence**: code review S1 (`lever_index` at line 84 is never transferred to `LeverCleaned`, confirmed by reading lines 339–353), S2 (`strategic_rationale` at lines 158–163 is saved in `raw` dump but never consumed by any downstream step). Combined, these fields waste roughly 10,500 words of generation per iteration (105 calls × ~100 words `strategic_rationale`) plus one integer per lever per call.
- **Impact**: Token cost reduction affects all models and all plans. Removing dead output fields also reduces the cognitive load on the model (fewer fields to generate = more attention on lever content). Secondary benefit: fewer tokens in flight reduces the probability of JSON truncation errors (the gpt-oss-20b sovereign_identity EOF failure in run 04 may have been a truncation boundary).
- **Effort**: Low for `lever_index` (remove field from `Lever`, update the field description reference in `LeverCleaned`). Medium for `strategic_rationale` (verify no downstream step reads it before removal).
- **Risk**: Low if verified — but confirming `strategic_rationale` is genuinely unused requires grepping the full codebase.

---

## Recommendation

**Pursue direction 1 + 2 together as a single prompt-only PR.**

Rationale: The current `review_lever` examples fixed two of four plans (silo, hong_kong) but left parasomnia (~82% lock) and gta_game (~78% lock) largely unchanged. The root cause is identical in both cases: the three examples cluster in one sector and share one rhetorical structure. Direction 1 addresses the domain gap; direction 2 addresses the structural gap. Together they are a complete fix for what the PR left open; separately either one might produce a secondary migration (a new domain lock or a new structural pattern).

Both changes are in `identify_potential_levers.py` section 4 (examples) and section 5 (prohibitions). No code changes. Low risk of regression.

**Specific changes:**

**Section 4 — replace example 1 with a medical/scientific example that uses a different rhetorical structure (no "but X reverses the gain"):**

Current example 1:
```
"Switching from seasonal contract labor to year-round employees stabilizes harvest quality, but the idle-wage burden during the 5-month off-season adds a fixed cost that erases the per-unit savings unless utilization reaches year-round levels."
```

Proposed replacement (medical/scientific, additive-risk structure rather than reversal):
```
"Expanding the clinical trial to a second study site accelerates enrollment, yet each additional site requires its own IRB approval, site-initiation visit, and staff training — a sequential process that adds 3–6 months of overhead before the first new participant can be screened."
```

This example: (a) names a domain-specific mechanism (IRB approval, site-initiation), (b) uses an additive-risk structure ("yet each … adds …") instead of a "but Z reverses Y" reversal, (c) does not use "the options" or "the lever" as subject.

**Section 4 — optionally replace example 3 with a technology/software example to further diversify:**

Current example 3:
```
"Pooling catastrophe risk across three coastal regions reduces expected annual loss on paper, but a single regional hurricane season can correlate all three simultaneously, turning the diversification assumption into a concentration risk at the worst possible moment."
```

Proposed replacement (software/technology, non-seasonal, non-finance):
```
"Migrating the authentication layer to a third-party OAuth provider eliminates credential-management overhead, yet every provider outage propagates directly to user login availability — a 99.9% SLA allows 8.7 hours of potential downtime per year for which the application has no local fallback."
```

**Section 5 — add one prohibition bullet:**
```
- NO review_lever that begins with "The options", "These options", "The lever", or "These levers" — name the specific mechanism, assumption, constraint, or risk directly instead.
```

**Section 5 — also update OPTIMIZE_INSTRUCTIONS to note example-domain diversity requirement** (one sentence after the existing template-lock migration paragraph):
```
Examples must span at least two structurally distinct domains so that the model is not anchored to one sector's vocabulary — e.g., one scientific/research example alongside any construction or finance example.
```

---

## Deferred Items

- **B1 (false partial_recovery)**: Fix after the prompt change, as a separate PR. The haiku run 58 events are ambiguous; fixing B1 will clarify whether the observation is a real regression or an artifact of the `< 3` test. File: `self_improve/runner.py:115` and `:514`.
- **I1 (soft template-lock validator)**: Low-effort, high-signal. Add after B1 fix so the logging tells a clean story (real failure vs. lock vs. early-success). File: `identify_potential_levers.py:139–155`.
- **S1 / I5 (remove `lever_index`)**: Cleanup PR. Grep confirms `lever_index` is never read after generation. File: `identify_potential_levers.py:84–86`.
- **S2 / I6 (remove or use `strategic_rationale`)**: Verify no downstream step reads it, then remove. File: `identify_potential_levers.py:158–163`. Token cost savings ~10,500 words/iteration.
- **B2 (dispatcher cross-thread contamination)**: Low practical impact (the affected file is deleted before it can cause harm), but the data is silently wrong during multi-worker runs. Address when multi-worker support is actively used. File: `self_improve/runner.py:187–219`.
- **B3 (case-sensitive name deduplication)**: Minor. Fix with `lever.name.strip().lower()` in the seen-names check while preserving original casing in output. File: `identify_potential_levers.py:337`.
- **S4 / I2 (option word-count validator)**: The 15-word minimum in section 6 is unvalidated. A soft warning (not raised) for options under 10 words would make the label-like option problem visible. File: `identify_potential_levers.py:125–137`.
- **H3 (prohibit "The plan's emphasis on X may overlook Y")**: Low priority — this pattern is domain-specific (X varies) and less harmful than "the options overlook". Defer until it shows measurable impact on output quality.
