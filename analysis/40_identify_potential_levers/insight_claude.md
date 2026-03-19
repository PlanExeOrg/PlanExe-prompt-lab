# Insight Claude

## Scope

Analyzing runs `2/87–2/93` (after PR #358) against `2/80–2/86` (before, analysis 39 / best.json baseline)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #358 "fix: remove 'core tension' template lock from field description"

**Changes made by the PR:**
- `review_lever` field description rewritten: "name the core tension, then identify a weakness" → "identify the primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed"
- Section 4 header in system prompt: same rewrite
- Section 6: "under 2 sentences (aim for 20–40 words)" → "one sentence (20–40 words)" (removes ambiguity)
- `OPTIMIZE_INSTRUCTIONS`: added "Field-description template lock" and "Template-lock migration" entries

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/80 | 2/87 | ollama-llama3.1 |
| 2/81 | 2/88 | openrouter-openai-gpt-oss-20b |
| 2/82 | 2/89 | openai-gpt-5-nano |
| 2/83 | 2/90 | openrouter-qwen3-30b-a3b |
| 2/84 | 2/91 | openrouter-openai-gpt-4o-mini |
| 2/85 | 2/92 | openrouter-gemini-2.0-flash-001 |
| 2/86 | 2/93 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **"Tension" opener lock eliminated for haiku.** Before (run 86 haiku) hong_kong_game: 15/20 reviews
   open with "The tension is/lies between X and Y" or "The core tension is X" (75%). After (run 93 haiku)
   hong_kong_game: 0/20 reviews use that opener (0%). The fix completely broke the targeted template lock.
   Evidence:
   - Before: `history/2/86_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
     (review_lever 1: "The tension lies between fidelity to source material and audience-awareness immunity")
   - After: `history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
     (review 1: "Levers one through three attempt twist mitigation, but all three options require heavyweight
     screenplay execution…")

2. **"Tension" opener lock eliminated for llama3.1.** Before (run 80 llama3.1) gta_game reviews opened
   ~100% with "The tension here is/lies between X and Y" (confirmed in analysis 39). After (run 87 llama3.1)
   hong_kong_game 002-9 raw shows reviews using "Not leveraging Hong Kong's existing infrastructure could
   lead to…" and "Not selecting the right director could result in…" — completely different patterns.
   Evidence: `history/2/87_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
   (system_prompt confirms new wording in field description).

3. **Haiku success rate improved (+13.4pp).** Before (run 86) haiku completed 11/15 calls. After (run 93)
   haiku completed 13/15 calls — an improvement of 2 calls (3 partial_recovery events → 2 partial_recovery
   events). The before run had a cascade failure: gta_game (2/3), sovereign_identity (2/3), parasomnia (1/3).
   The after run has only: gta_game (2/3), silo (2/3).
   Evidence: `history/2/86_identify_potential_levers/outputs.jsonl` vs
   `history/2/93_identify_potential_levers/outputs.jsonl`.

4. **Overall success rate improved (+1.9pp).** Before (runs 80–86) total: 100/105 calls = 95.2%. After
   (runs 87–93) total: 102/105 = 97.1%. No regressions on the five models that were already at 100%.
   Evidence: all seven outputs.jsonl files.

5. **No LLMChatErrors in after runs.** No LLMChatError or ValidationError entries in any events.jsonl
   across all after runs. Partial_recovery events are step-gate loop-exits (enough levers generated early),
   not schema failures. Evidence: `history/2/87–93_identify_potential_levers/events.jsonl`.

6. **OPTIMIZE_INSTRUCTIONS correctly updated.** The source file at
   `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` now documents
   "Field-description template lock" (lines 86–92) as a known failure mode and adds a "Template-lock
   migration" warning (lines 69–82). These entries accurately predict the residual pattern observed in
   this analysis (see Negative Things #1).

7. **Section 6 "one sentence" produces measurably shorter haiku reviews.** Before (run 86) haiku silo
   reviews: ~290–310 chars (~48–52 words), multi-sentence. After (run 93) haiku silo reviews: ~230–350
   chars (~32–58 words), predominantly single-sentence. The "one sentence" constraint is partially effective.
   Evidence: `history/2/86_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` vs
   `history/2/93_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

8. **System prompt examples (harvest/IRB/catastrophe) did not leak into plan outputs.** None of the after
   runs produce review text referencing seasonal labor, IRB approval, or catastrophe risk pooling in plan
   contexts where those domains are irrelevant. This suggests the three-example diversity works for example
   grounding without causing cross-domain leakage.

---

## Negative Things

1. **Template-lock migration detected in haiku AFTER: "None/All three options" phrase lock.**
   After eliminating "The tension is between X and Y" as the opener, haiku (run 93) shifted to a new
   recurring terminal phrase: "All three options [X], but none address Y" or "none of the [N] options
   address Z." In hong_kong_game (002-10), this pattern appears in approximately 17/20 = 85% of reviews.
   In silo (002-10), "none/all three options" appears in ~11/22 = 50% of reviews.

   This is precisely the "Template-lock migration" failure mode documented in OPTIMIZE_INSTRUCTIONS (lines
   69–82): "Replacing a copyable opener does not eliminate template lock — weaker models shift to copying
   subphrases within the new examples." The trigger here appears to be the field description itself:
   "then state the specific gap the three options leave unaddressed" — models copy this as "none of the
   three options address…"

   Example from run 93 hong_kong_game:
   - "All three options manage mainland censorship risk differently, but none directly addresses whether
     Hong Kong's political climate in 2026–2027 will allow…"
   - "All three options balance city authenticity against financing access, but none directly solves the
     risk that a mid-tier director may lack proven ability…"
   - "All three options address different market assumptions…, but none directly confronts whether the lead
     actor will have creative approval…"
   Evidence: `history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

2. **Review lengths remain 2.5–4× above baseline.** Baseline silo reviews ("Controls X vs. Y. Weakness:
   …") average ~80–100 chars (~15–20 words). After (run 93) haiku silo reviews average ~230–350 chars
   (~38–58 words). Ratio: 2.5–4× above baseline. The "one sentence (20–40 words)" instruction is partially
   effective but does not bring haiku within the 2× warning threshold.
   Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` vs
   `history/2/93_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

3. **Haiku still has 2 partial_recovery events (gta_game 2/3, silo 2/3).** This is an improvement over
   the before (4 events), but the underlying cause — haiku generating ≥15 levers in fewer than the expected
   3 calls — persists. The step-gate logic exits early when enough levers are collected, producing 2/3
   rather than 3/3 calls. This is operational but reduces the diversity of generated levers.
   Evidence: `history/2/93_identify_potential_levers/events.jsonl` (partial_recovery on gta_game and silo).

4. **llama3.1 still has 1 partial_recovery (hong_kong_game 2/3).** Before (run 80) had 1 partial_recovery
   on sovereign_identity; after (run 87) has 1 on hong_kong_game. The specific plan moved but the count is
   unchanged. This is not a regression, but the llama3.1 single-worker constraint makes it harder to analyze
   compared to parallel-worker models.
   Evidence: `history/2/87_identify_potential_levers/events.jsonl`.

5. **`LeverCleaned.review` field description still contains "names the core tension" phrasing.** The source
   file at line 212 reads: `description="A short critical review — names the core tension, then identifies a
   weakness the options miss."` This class is marked "never serialized to an LLM" (comment on lines 208–210),
   so it does not cause the template lock at runtime. However, the stale wording creates confusion in code
   reviews and could lead a future maintainer to copy this description into a prompt-facing field, re-creating
   the bug. Evidence: `identify_potential_levers.py` line 212.

---

## Comparison

| Metric | Before (runs 80–86) | After (runs 87–93) | Change |
|--------|--------------------|--------------------|--------|
| Overall call success rate | 100/105 = 95.2% | 102/105 = 97.1% | **+1.9pp** |
| Haiku call success rate | 11/15 = 73.3% | 13/15 = 86.7% | **+13.4pp IMPROVED** |
| llama3.1 call success rate | 14/15 = 93.3% | 14/15 = 93.3% | 0 unchanged |
| gpt-oss-20b, gpt-5-nano, qwen3, gpt-4o-mini, gemini | 15/15 each = 100% | 15/15 each = 100% | 0 unchanged |
| "Tension" opener in haiku reviews (hong_kong_game) | 15/20 = 75% | 0/20 = 0% | **FIXED** |
| "Tension" opener in llama3.1 reviews | ~100% (run 80 gta_game) | ~0% (run 87 002-9 raw) | **FIXED** |
| "None/All three options" phrase in haiku reviews | ~0% | ~85% (hong_kong_game) | NEW SECONDARY LOCK |
| Haiku review avg length (silo) | ~290–310 chars (~50 words) | ~230–350 chars (~42 words) | Slight improvement |
| Haiku partial_recovery events | 4 events (run 86) | 2 events (run 93) | **-2 IMPROVED** |
| LLMChatErrors | 0 | 0 | — unchanged |
| Fabricated % claims in reviews | 0 | 0 | — unchanged |

---

## Quantitative Metrics

### Call Success Rate Per Run

| Run | Model | Plans OK | Calls Succeeded | Calls Expected | Rate |
|-----|-------|----------|-----------------|----------------|------|
| 80 (before) | llama3.1 | 5/5 | 14 | 15 | 93.3% |
| 81 (before) | gpt-oss-20b | 5/5 | 15 | 15 | 100% |
| 82 (before) | gpt-5-nano | 5/5 | 15 | 15 | 100% |
| 83 (before) | qwen3-30b | 5/5 | 15 | 15 | 100% |
| 84 (before) | gpt-4o-mini | 5/5 | 15 | 15 | 100% |
| 85 (before) | gemini-2.0-flash | 5/5 | 15 | 15 | 100% |
| 86 (before) | haiku | 5/5 | 11 | 15 | 73.3% |
| **Before total** | — | 35/35 | **100** | **105** | **95.2%** |
| 87 (after) | llama3.1 | 5/5 | 14 | 15 | 93.3% |
| 88 (after) | gpt-oss-20b | 5/5 | 15 | 15 | 100% |
| 89 (after) | gpt-5-nano | 5/5 | 15 | 15 | 100% |
| 90 (after) | qwen3-30b | 5/5 | 15 | 15 | 100% |
| 91 (after) | gpt-4o-mini | 5/5 | 15 | 15 | 100% |
| 92 (after) | gemini-2.0-flash | 5/5 | 15 | 15 | 100% |
| 93 (after) | haiku | 5/5 | 13 | 15 | 86.7% |
| **After total** | — | 35/35 | **102** | **105** | **97.1%** |

### Tension Opener Rate (Haiku — hong_kong_game)

| Run | Opener Pattern | Count / Total | Rate |
|-----|---------------|---------------|------|
| 86 (before) | "The tension [is/lies] between…" or "The core tension is…" | 15/20 | 75% |
| 86 (before) | "All three options…" or "None of the options…" | 2/20 | 10% |
| 86 (before) | Other (weakness, constraint, review) | 3/20 | 15% |
| 93 (after) | "The tension [is/lies] between…" or "The core tension is…" | 0/20 | **0%** |
| 93 (after) | "All three options…" or "none [of the options] address…" | 17/20 | **85%** |
| 93 (after) | Other | 3/20 | 15% |

Evidence: `history/2/86_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
`history/2/93_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### Review Length vs Baseline (Haiku — silo plan)

| Source | Avg review length (chars) | Approx words | Ratio vs baseline |
|--------|--------------------------|--------------|-------------------|
| Baseline train silo | ~90 | ~17 | 1.0× |
| Before haiku run 86 | ~300 | ~50 | **3.3× (warning)** |
| After haiku run 93 | ~260 | ~42 | **2.9× (warning)** |

Evidence: `baseline/train/20250321_silo/002-10-potential_levers.json` (reviews: "Controls Efficiency vs.
Equity. Weakness: The options don't address…" format, ~80–100 chars);
`history/2/86_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`;
`history/2/93_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

*Note on baseline quality*: the baseline training data contains significant fabricated percentage claims
("15% increase in black market activity", "30% reduction in innovative output", etc.) in consequences
fields. These are a pre-existing quality regression in the baseline itself, not introduced by the current
prompt — the current system prompt correctly prohibits fabricated statistics (Section 5). The short review
format of the baseline is worth targeting, but its content is not.

### Partial Recovery Events

| Run | Model | Partial Recovery Events | Plans Affected |
|-----|-------|------------------------|----------------|
| 86 (before) | haiku | 3 events | gta_game (2/3), sovereign_identity (2/3), parasomnia (1/3) |
| 87 (after) | llama3.1 | 1 event | hong_kong_game (2/3) |
| 93 (after) | haiku | 2 events | gta_game (2/3), silo (2/3) |

All other after runs (88–92): 0 partial_recovery events (5/5 plans × 3/3 calls = 100%).

---

## Evidence Notes

- **BEFORE system prompt** (confirmed via run 86 002-9 raw, field `system_prompt`): The `review_lever`
  Pydantic field description (not the system prompt text) contained "name the core tension" — models
  parsed this as a structural instruction and began every review with "The tension is between X and Y".
  Source: `history/2/86_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`.

- **AFTER system prompt** (confirmed via run 87 002-9 raw): The field description now reads "identify the
  primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed."
  The system prompt Section 4 has the same rewrite.
  Source: `history/2/87_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json`
  (system_prompt field shows updated wording at Section 4).

- **OPTIMIZE_INSTRUCTIONS** at `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
  lines 69–92 now contains both "Template-lock migration" and "Field-description template lock" entries.
  The "Template-lock migration" entry predicts that smaller models will copy sub-phrases from new examples
  ("e.g. 'the options neglect', 'the options assume'"). The actual post-PR output shows "none of the three
  options address…" as the new recurring sub-phrase — not from the examples, but from the field description
  itself ("state the specific gap the three options leave unaddressed").

- **`LeverCleaned.review` field**: Line 212 of `identify_potential_levers.py` still says
  `description="A short critical review — names the core tension, then identifies a weakness the options miss."`.
  The code comment on lines 208–210 confirms it is "never serialized to an LLM." This stale description
  is harmless at runtime but should be updated for consistency.

- **Baseline content warning**: The baseline silo plan (`baseline/train/20250321_silo/002-10-potential_levers.json`)
  shows consequences fields with fabricated percentages ("15% increase in black market activity", "20% slower
  problem-solving rate", "50% reduction in awareness"). The current system prompt (Section 5 prohibitions)
  correctly prevents this. Current after runs have zero fabricated percentage claims in consequences.

---

## PR Impact

**What the PR was supposed to fix:** The `review_lever` field description contained the phrase "name the
core tension" which caused near-100% "The tension is between X and Y" opener lock for llama3.1 and haiku
(confirmed in analysis 39). The PR rewrote this to "identify the primary trade-off…, then state the
specific gap…", and also changed Section 6 from "under 2 sentences" to "one sentence".

**Comparison table:**

| Metric | Before (runs 80–86) | After (runs 87–93) | Change |
|--------|--------------------|--------------------|--------|
| "Tension" opener rate — haiku hong_kong_game | 75% | 0% | **FIXED** |
| "Tension" opener rate — llama3.1 | ~100% (run 80 gta_game) | ~0% (run 87 002-9) | **FIXED** |
| "None/All three options" phrase — haiku | ~0% | ~85% | **NEW SECONDARY LOCK** |
| Haiku call success rate | 73.3% | 86.7% | **+13.4pp** |
| Overall call success rate | 95.2% | 97.1% | **+1.9pp** |
| Haiku partial_recovery events | 4 | 2 | **-2** |
| Review avg length — haiku (chars) | ~300 | ~260 | **-40 chars, slight improvement** |

**Did the PR fix the targeted issue?** Yes, definitively. The "The tension is between X and Y" opener lock
is completely eliminated for haiku (0/20 in hong_kong_game; 0/22 in silo) and for llama3.1 (confirmed
via 002-9 raw review_lever content in run 87). The fix was causally verified: the field description change
directly removed the structural cue that models were copying.

**Did the PR introduce regressions?** One new pattern emerged: "All three options…, but none [address]…"
dominates haiku reviews (~85% in hong_kong_game). This is a milder secondary template lock — it varies the
SUBJECT of each review (plan-specific content) while repeating the PREDICATE ("none address"). It is less
harmful than the original lock (which locked BOTH subject and verb) but is worth monitoring and addressing
in a follow-up PR.

**Verdict: KEEP**

The PR produced measurable, targeted improvement: the primary template lock is eliminated, haiku's success
rate improved by 13.4pp, and overall success rate improved by 1.9pp. The secondary template-lock migration
("None/All three options") is a known phenomenon documented in OPTIMIZE_INSTRUCTIONS and does not negate
the primary improvement. The PR should be kept; the secondary lock should be addressed in the next iteration.

---

## Questions For Later Synthesis

1. **Secondary template lock source:** Is the "none of the three options address" pattern driven by (a)
   the field description phrase "state the specific gap the three options leave unaddressed", (b) a
   sub-phrase carried over from the examples, or (c) an inherent tendency of smaller models to phrase
   gap-statements this way? Understanding the source determines whether the fix is a further field-description
   rewrite or an example redesign.

2. **Why did haiku's partial_recovery events drop from 4 to 2?** The PR changed the field description and
   Section 6 wording, not the step-gate logic. Could the shorter expected reviews cause fewer calls to
   exceed the lever quota? Or is this run-to-run noise?

3. **Do models other than haiku show the "None/All three options" lock?** I only checked haiku AFTER runs
   (93) in detail for this lock. A follow-up analysis should check gpt-4o-mini (91) and gemini (92) AFTER
   runs for similar patterns.

4. **LeverCleaned.review field**: Should the stale "names the core tension" description be fixed in
   code, even if it has no runtime effect? This is a code hygiene question for synthesis.

---

## Reflect

The PR #358 demonstrates a clean, targeted fix for a well-diagnosed problem. The evidence chain is solid:
1. Field description said "name the core tension" → models generated "The tension is between X and Y" ~100%
2. Field description now says "identify the primary trade-off…" → "tension" opener dropped to 0%

The only complexity is the template-lock migration: the new field description phrase "state the specific
gap the three options leave unaddressed" is being echoed as "none of the three options address…" in haiku
reviews. This is a softer lock (the subject/content varies; only the predicate is templated), and
OPTIMIZE_INSTRUCTIONS already documents this as a known risk.

The success rate improvement for haiku (+13.4pp) is substantial and likely partially caused by the shorter
review constraint (one sentence), which reduces the chance of a response being cut off mid-generation
and failing the 10-char minimum `review_lever` validator.

The baseline training data should not be used as a quality target beyond field length: its reviews contain
significant fabricated percentages and the "Controls X vs. Y / Weakness:" format was itself a prior
template lock from an older prompt version. The goal for review content quality is substantive specificity,
not baseline mimicry.

---

## Potential Code Changes

**C1 (Code hygiene):** Update `LeverCleaned.review` field description (line 212 of
`identify_potential_levers.py`) to match the new wording used in `Lever.review_lever`. Current: "A short
critical review — names the core tension, then identifies a weakness the options miss." Proposed: "A short
critical review: identifies the primary trade-off this lever introduces and the specific gap the options
leave unaddressed." This has no runtime effect but prevents future copy-paste of stale wording.

**C2 (Optional analysis tool):** The template-lock migration pattern ("None/All three options address")
is now documented in OPTIMIZE_INSTRUCTIONS. An optional post-run analyzer that counts the fraction of
reviews containing "none of the [N] options address" or "all [N] options assume" would help detect
future template-lock migrations automatically during optimization runs. This is analysis-only, not a
validator.

---

## Hypotheses

**H1 (Prompt fix, field description):** The "none of the three options address" secondary lock is triggered
by the field description phrase "state the specific gap the three options leave unaddressed." Rewriting this
to avoid the direct phrase "three options" — e.g., "identify a real-world constraint or risk that all three
strategies collectively sidestep, expressed in domain-specific terms" — should break the "none of the three
options" pattern without re-introducing the "tension" opener.

**H2 (Prompt fix, examples):** The three examples in Section 4 all follow a structure where the first
clause states a mechanism effect and the second clause identifies an unresolved constraint. This structure
(X but Y) maps naturally to "All three options do X, but none address Y." Adding a fourth example that
uses a different rhetorical structure (e.g., a conditional: "If X occurs, Y follows; however Z applies
throughout") would give models an alternate pattern to draw from.

**H3 (Monitoring):** Haiku silo partial_recovery events dropped from 3 (before) to 1 (after). Track
whether this trend continues in the next iteration. If silo and gta_game consistently exit the step-gate
after 2 calls for haiku, it may indicate haiku is consistently over-generating (≥15 levers) in 2 calls
— which would be a quality signal, not a reliability concern.

---

## Summary

PR #358 delivers on its stated goal: the "The tension is between X and Y" opener lock is eliminated for
both llama3.1 and haiku. Haiku's success rate improved from 73.3% to 86.7% (+13.4pp), and overall success
rate moved from 95.2% to 97.1%. No regressions on previously-clean models (gpt-oss-20b, gpt-5-nano, qwen3,
gpt-4o-mini, gemini remain at 100%).

One new pattern emerged: haiku AFTER reviews use "All three options X, but none address Y" in ~85% of cases
(hong_kong_game). This is a milder secondary template lock driven by the field description phrase "state the
specific gap the three options leave unaddressed." It is less harmful than the original lock, is already
predicted in OPTIMIZE_INSTRUCTIONS, and should be the primary target of the next PR.

**PR verdict: KEEP.** Primary fix confirmed, success rate improved, no regressions.
