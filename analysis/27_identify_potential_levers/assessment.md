# Assessment: fix: relax option count validator, raise review min_length, clean up dead code

## Issue Resolution

**What the PR aimed to fix (PR #339):**

1. Relax `check_option_count` from `len(v) != 3` to `len(v) < 3` — allow over-generation (>3 options), reject under-generation only.
2. Raise `review_lever` `min_length` from 20 to 50 chars — catch stub reviews like the 19-char `"Sensor Data Sharing"` from run 89 parasomnia.
3. Strip dead-code examples from `LeverCleaned.review` field description (confirmed never serialized to LLM).
4. Add template-lock migration pattern to `OPTIMIZE_INSTRUCTIONS`.
5. Fix docstring run reference: 89 → 82 (the actual gta_game 2-option bug).

**Is the issue resolved?**

Yes — all five changes landed correctly:

- **Review min_length fix (primary):** The run 89 llama3.1 parasomnia failure (`"Sensor Data Sharing"`, 19 chars, Pydantic `LLMChatError`) does not recur in run 96. Verified: `history/1/96_identify_potential_levers/events.jsonl` — 5 `run_single_plan_complete`, 0 errors. Parasomnia review averages 149 chars, well above both the old 20-char and new 50-char floors.
- **Option count relaxation:** Zero observable effect — no model over- or under-generated options in runs 96–02. Change is directionally correct and deferred in impact.
- **Dead-code cleanup:** `LeverCleaned.review` field description now carries a comment explaining why no examples are present. Cosmetically correct, functionally inert (class never serialized to LLM).
- **OPTIMIZE_INSTRUCTIONS update:** Lines 73-79 now document template-lock migration. Accurate and grounded in observed run 89 behavior.
- **Docstring correction:** Run reference corrected to 82 (the actual 2-option bug location).

**Residual symptoms:**

- **Secondary template lock persists unaddressed.** The phrase "the options neglect" from the insurance example at `identify_potential_levers.py:115` and `:235` is the confirmed source of llama3.1's new secondary lock. PR #339 documented this problem in OPTIMIZE_INSTRUCTIONS but did not remove the trigger. In run 96 (after PR), the lock persists at 16/16 reviews for gta_game (100%), 11/12 for parasomnia (92%). `OPTIMIZE_INSTRUCTIONS` warns about the pattern on line 73-79 while line 235 still contains the trigger phrase — warning and root cause coexist.
- **Cross-field contamination persists.** llama3.1 places "A weakness in this approach is that…" into the `consequences` field in both run 89 (before) and run 96 (after). Verified directly in `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, levers 1 and 2. No validator enforces the prohibition in the field description.
- **Partial recovery events increased.** 1 partial recovery before (run 94) vs 4 after (runs 96, 99, 01×2). All 35 plans still complete. The gemini hong_kong_game case (run 01: 1/3 calls succeeded → 6 levers vs 18 in run 94) is the most visible symptom; appears to be non-deterministic model behavior, not a code regression.

---

## Quality Comparison

Models appearing in **both** batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, claude-haiku-4-5.

| Metric | Before (runs 89–95) | After (runs 96–02) | Verdict |
|--------|--------------------|--------------------|---------|
| **Overall success rate** | 34/35 = 97.1% | 35/35 = 100.0% | IMPROVED |
| **llama3.1 LLMChatError count** | 1 (parasomnia, 19-char review) | 0 | IMPROVED |
| **Bracket placeholder leakage** | 0 observed | 0 observed | UNCHANGED |
| **Option count violations (< 3)** | 0 | 0 | UNCHANGED |
| **Option count violations (> 3, now permitted)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | Stable across all models | Stable | UNCHANGED |
| **Template lock — llama3.1 secondary "options neglect/overlook/fail"** | Present (run 89: 76% hkg, likely higher on gta) | Present (run 96: 100% gta, 92% parasomnia) | UNCHANGED |
| **Template lock — qwen3 "This lever [verb]" (hkg)** | 6% (1/18, run 92) | Not re-measured (not focus of PR) | UNCHANGED (stable from PR #337) |
| **Review format compliance ("Controls X vs Y" pattern)** | 0 observed violations | 0 observed violations | UNCHANGED |
| **Consequence chain format (Immediate→Systemic→Strategic markers)** | Not enforced | Not enforced | UNCHANGED |
| **Content depth — avg review length (llama3.1)** | ~183 chars (run 89) | ~209 chars (run 96) | SLIGHTLY IMPROVED |
| **Content depth — avg option length (llama3.1)** | ~267 chars (run 89) | ~306 chars (run 96) | SLIGHTLY IMPROVED |
| **Content depth — avg consequences length (llama3.1)** | ~197 chars (run 89) | ~201 chars (run 96) | UNCHANGED |
| **Content depth — avg review length (qwen3)** | ~171 chars (run 92) | ~166 chars (run 99) | UNCHANGED |
| **Cross-call lever name duplication** | Present (expected; deduplication downstream) | Present | UNCHANGED |
| **Over-generation (> 7 levers per call, now allowed)** | Not counted separately; models produce 14–21 total across 3 calls | Same range; downstream DeduplicateLeversTask handles extras | UNCHANGED (informational) |
| **Partial recovery events** | 1 (run 94, gemini sovereign_identity, 2/3) | 4 (runs 96, 99, 01×2) | REGRESSED |
| **Gemini hong_kong_game lever count** | 18 (run 94) | 6 (run 01) | REGRESSED (non-deterministic) |
| **Field length vs baseline — llama3.1 review** | 1.38× baseline | 1.38× baseline | UNCHANGED |
| **Field length vs baseline — haiku review** | 2.1× baseline (analysis 26) | 3.87× baseline (run 02) | WARNING (predates PR #339) |
| **Field length vs baseline — all other models review** | 1.0–1.4× | 1.0–1.4× | UNCHANGED |
| **Fabricated percentage claims — haiku** | 51 total (run 95) | 35 total (run 02) | SLIGHTLY IMPROVED |
| **Fabricated percentage claims — other models** | 0–6 per model | 0–9 per model | STABLE |
| **Marketing-copy language** | 0 observed | 0 observed | UNCHANGED |
| **Cross-field contamination (weakness text in consequences)** | Present — llama3.1 gta, runs 89 | Present — llama3.1 gta, run 96 | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS template-lock migration entry** | Absent | Present (lines 73-79) | IMPROVED |

**Key note on haiku 3.87× review ratio:** This is above the 3× warning threshold, but it predates PR #339 — it was 2.1× in analysis 26 and has grown gradually. It is not a regression introduced by this PR but warrants qualitative review of whether haiku reviews add substance or padding.

**Key note on partial recovery increase:** 1→4 partial recovery events is a regression in reliability, but all 35 plans complete. The gemini hong_kong_game degradation (6 vs 18 levers) appears to be stochastic model behavior — the PR changes (min_length, option count, dead-code) have no mechanism that would cause this specific degradation.

---

## New Issues

1. **Warning-and-root-cause coexistence (critical gap).** PR #339 added `OPTIMIZE_INSTRUCTIONS` warning at lines 73-79 that "weaker models shift to copying subphrases within the new examples (e.g. 'the options neglect', 'the options assume')." The third `review_lever` example at lines 115 and 235 still contains "the options neglect" verbatim. The documentation is accurate but the underlying trigger was not removed. This is the clearest actionable finding from this batch.

2. **Duplicate example injection (B2).** The same three `review_lever` examples appear in both the `Lever` Pydantic field description (lines 107-118) and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (lines 229-236). Because llama_index serializes the full Pydantic schema when constructing structured-output prompts, every LLM call receives the examples twice — doubling the copyable-phrase signal and wasting approximately 150-200 tokens per call. The PR did not address this injection path.

3. **Partial recovery increase warrants monitoring.** Four partial recovery events across the after-batch (vs 1 before) is a trend to watch. If it persists in the next batch, relaxing `DocumentDetails` `levers min_length` from 5 to 3 for calls 2 and 3 (where generating 5+ novel levers is harder) would reduce this failure mode.

4. **Cross-field contamination not yet in `OPTIMIZE_INSTRUCTIONS`.** llama3.1 consistently places critique/weakness text ("A weakness in this approach is that…") into the `consequences` field across runs 89 and 96. This is not listed in `OPTIMIZE_INSTRUCTIONS` known problems (7 entries as of PR #339), making it invisible to future analysts unless they happen to sample gta_game outputs.

---

## Verdict

**YES**: PR #339 eliminates the one concrete LLMChatError from the previous batch (llama3.1 parasomnia 19-char review stub), improves overall success rate from 97.1% to 100%, introduces no content quality regressions, and correctly documents the template-lock migration anti-pattern. The option count relaxation and dead-code cleanup are sound hygiene even with zero observable effect in these runs. The PR does not worsen any existing issue and the partial recovery increase appears stochastic rather than caused by the PR changes.

---

## Recommended Next Change

**Proposal:** Replace the third `review_lever` example to remove the lockable phrase "the options neglect", and remove the duplicate examples from the `Lever` Pydantic field description (keeping them only in the system prompt). This is a two-location edit in a single file.

**Evidence:**
- `identify_potential_levers.py:115` and `:235` both contain `"the options neglect"` verbatim. `OPTIMIZE_INSTRUCTIONS` lines 73-75 names this exact phrase as the secondary-lock trigger. Run 96 llama3.1 gta_game: 16/16 reviews use "the options [fail/neglect/overlook]" — 100% lock rate. Run 96 llama3.1 parasomnia: 11/12 reviews use the same pattern. Confirmed by direct file inspection at `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.
- The same three examples appear in both the `Lever` field description and the system prompt (B2, code_claude). Removing from the field description halves the injection frequency and reduces per-call token cost. The `LeverCleaned.review` field already demonstrates the correct pattern: a comment instead of duplicated examples.
- The synthesis from analysis 27 recommends this as direction 1+2 combined: rewrite the third system prompt example to remove "the options neglect" while simultaneously removing examples from the field description.

**Specific change (system prompt, line 235):**
- Remove: `"Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but the options neglect that a single hurricane season can correlate all three simultaneously."`
- Replace with: `"Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a regional hurricane season can correlate all three simultaneously — correlation risk absent from every option."`

**Specific change (Lever field description, lines 107-118):**
- Replace the three quoted example sentences with a one-line structural note: `"See system prompt section 4 for examples. Do not use square brackets or placeholder text."`

**Verify:**
- llama3.1 gta_game (run ~97+): "the options [neglect/overlook/fail]" rate should drop below 30% (from 100%). If it drops but a new formulaic opener appears, document the migration in `OPTIMIZE_INSTRUCTIONS` and examine whether the new examples themselves contain any new copyable phrase.
- llama3.1 parasomnia: secondary lock rate (currently 92%) should decrease.
- haiku: no regression in review length ratio (currently 3.87× — monitor whether removing field-description examples changes haiku's output length).
- All models: zero new LLMChatErrors (success rate should hold at 100%).
- Token usage per call: should decrease slightly (~100-200 tokens) due to removal from field description.

**Risks:**
- Removing examples from the field description reduces per-field guidance. The system prompt still carries examples, but weaker models that weight field descriptions heavily may produce shallower reviews. Mitigation: keep the structural note ("name the core tension, then identify a weakness") in the field description.
- Replacing the third example may shift the lock to a different subphrase in examples 1 or 2 ("seasonal labor", "heritage review"). Per OPTIMIZE_INSTRUCTIONS warning, check the first two examples for any "the [X] [verb]" pattern that could become the next anchor.
- The agriculture example currently reads "but the idle-wage burden during the 5-month off-season is unpriced in all three options" — this is domain-specific and not easily ported to software/film/game contexts, making it lower-risk than the current insurance example.

**Prerequisites:** None. This is an isolated string replacement in `identify_potential_levers.py` touching two locations in the same file. No schema changes, no validator changes, no runner changes.

---

## Backlog

**Resolved by PR #339 (can be closed):**
- B1 (`min_length=20` insufficient for `review_lever`) — raised to 50, parasomnia failure eliminated.
- S1 (docstring run reference wrong: 89 → 82) — corrected.
- S3 (`LeverCleaned.review` dead-code examples) — replaced with explanatory comment.
- I5 (template-lock migration not in `OPTIMIZE_INSTRUCTIONS`) — documented at lines 73-79.

**Active (carried forward):**
- **B1 (new) — "the options neglect" in third example (lines 115, 235):** Root cause of secondary template lock confirmed in runs 89 and 96. `OPTIMIZE_INSTRUCTIONS` warns about it; prompt still contains it. **Priority: HIGH.** Fix in next PR.
- **B2 — Duplicate example injection (field description + system prompt):** Same three examples injected twice per call. Doubles copyable-phrase signal, wastes ~150-200 tokens per call. **Priority: HIGH.** Fix in same PR as B1 above.
- **B3 / S1 — Shared dispatcher cross-thread contamination (runner.py:106-109, 147):** `track_activity` handlers accumulate per worker on the global dispatcher singleton. Corrupts per-plan `track_activity.jsonl` files when `workers > 1`. Masked by `unlink()` call. **Priority: LOW** (single-worker runs unaffected; no impact on plan quality).
- **Cross-field contamination — weakness text in `consequences` (llama3.1, persistent):** "A weakness in this approach is that…" appears in `consequences` field across runs 89 and 96. No validator catches it. Not yet in `OPTIMIZE_INSTRUCTIONS`. **Priority: MEDIUM.** Add OPTIMIZE_INSTRUCTIONS entry first; validator can follow.
- **Haiku 3.87× review length ratio:** Above the 3× warning threshold. Predates PR #339 (was 2.1× in analysis 26). Sample haiku reviews qualitatively to determine whether length reflects substantive analysis or verbose padding. If padding, add a `max_length` hint to the system prompt. **Priority: LOW** (no plan failures; quality unclear).
- **Partial recovery increase (1 → 4 events):** Monitor in next batch. If persists, create `DocumentDetailsLaterCall` schema with `min_length=3` for calls 2 and 3. **Priority: MONITOR.**
- **Gemini hong_kong_game instability (run 01: 1/3 calls, 6 levers):** May be stochastic. Track in next batch; if gemini hong_kong_game recurs at < 10 levers, investigate whether the plan prompt triggers rate-limiting or context-length issues. **Priority: MONITOR.**
- **S2 — Case-sensitive lever name deduplication in `seen_names` check:** `"Cost Structure"` and `"cost structure"` both pass. Downstream `DeduplicateLeversTask` provides semantic dedup; this is low severity. **Priority: LOW.**
- **qwen3 "Core tension:" residual in non-hkg plans:** Not verified for runs 92 and 99 in sovereign_identity and parasomnia. Sample these in the next batch to confirm PR #337 fully resolved the pattern across all plans. **Priority: LOW.**
