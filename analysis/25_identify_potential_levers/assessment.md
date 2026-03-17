# Assessment: fix: remove unused summary field, slim call-2/3 prefix

## Issue Resolution

**PR #334 claimed four changes:**

1. Remove `DocumentDetails.summary` field — required by schema but never used downstream, wastes tokens
2. Remove summary validation section from system prompt
3. Add "at least 15 words with an action verb" to section 6 for uniform enforcement across all calls
4. Slim call-2/3 prefix: remove duplicate quality/anti-fabrication reminders

**Verification against current code (`identify_potential_levers.py`):**

| Claim | Status | Evidence |
|-------|--------|----------|
| Remove `summary` field from `DocumentDetails` | **DONE** | `DocumentDetails` (lines 152–163) has no `summary` field. Grep confirms zero `"summary"` keys in runs 82–88 raw files vs 2–3 per plan in runs 75–81. |
| Remove summary validation section from system prompt | **DONE** | `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` has no summary-related instruction. |
| Add "at least 15 words with an action verb" to section 6 | **DONE** | Line 240 of system prompt: "at least 15 words with an action verb". Also absent from Pydantic field description (schema-level gap remains). |
| Slim call-2/3 prefix | **DONE** | Lines 274–278: prefix contains only the "do not reuse names" instruction and the original user prompt. |

**Residual symptoms:**
- The 15-word floor is still not in the Pydantic `options` field description — structured-output models weigh schema descriptions independently from system-prompt text. llama3.1 averages ~12 words/option (up from ~7), not yet at the 15-word floor.
- The hard `len(v) != 3` options validator was not relaxed. Run 82 (llama3.1 gta_game) failed because two levers produced 2 options each — entire call discarded, plan failed. This is a disproportionate failure mode left unaddressed by the PR.
- Template lock (`"This lever governs the tension between"`) persists at 100% for llama3.1 because the phrase remains as the lead example in both the `review_lever` Pydantic field description (lines 100–104) and system-prompt section 4 (lines 225–227). No negative constraint was added.

**Methodological note (from analysis 25 insight):** Analysis 24 (runs 75–81) was flagged as an INVALID experiment — the runner executed against the old `main` branch, not the PR branch. Analysis 25 (runs 82–88) is the first valid test. The before/after comparison below uses this corrected pairing.

---

## Quality Comparison

Models present in **both** batches (before = runs 75–81, after = runs 82–88):

| Run (before) | Run (after) | Model |
|---|---|---|
| 75 | 82 | ollama-llama3.1 |
| 76 | 83 | openrouter-openai-gpt-oss-20b |
| 77 | 84 | openai-gpt-5-nano |
| 78 | 85 | openrouter-qwen3-30b-a3b |
| 79 | 86 | openrouter-openai-gpt-4o-mini |
| 80 | 87 | openrouter-gemini-2.0-flash-001 |
| 81 | 88 | anthropic-claude-haiku-4-5-pinned |

All 7 models are matched 1:1. Full comparison set.

| Metric | Before (runs 75–81) | After (runs 82–88) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 33/35 = 94.3% | 34/35 = 97.1% | IMPROVED (+2.8 pp) |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (≠3 options)** | 1 (run 78, qwen3 ValueError cascaded) | 1 (run 82, llama3.1 gta_game levers 5,6) | UNCHANGED (lateral swap) |
| **Lever name uniqueness** | 100% (all sampled runs) | 100% (all sampled runs) | UNCHANGED |
| **Template leakage (verbatim prompt copy)** | 0 | 0 | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | N/A (structural check disabled per OPTIMIZE_INSTRUCTIONS) | N/A | UNCHANGED |
| **Consequence chain format (Immediate → Systemic → Strategic)** | Not enforced; freeform consequence text | Not enforced; freeform consequence text | UNCHANGED |
| **Content depth — llama3.1 avg option chars** | ~50 chars/option (run 75) | ~85 chars/option (run 82) | IMPROVED (+70%) |
| **Content depth — haiku avg option chars** | ~220 chars/option (run 81) | ~270 chars/option (run 88) | IMPROVED (+23%) |
| **Content depth — gpt-4o-mini avg option chars** | ~125 chars/option (run 79) | ~130 chars/option (run 86) | UNCHANGED |
| **Cross-call duplication** | Present; handled by downstream DeduplicateLevers | Present; handled by downstream DeduplicateLevers | UNCHANGED |
| **Over-generation (>7 levers/call)** | Rare; DeduplicateLevers handles extras | Rare; DeduplicateLevers handles extras | UNCHANGED |
| **Field length vs baseline — llama3.1 options** | ~0.3× baseline | ~0.55× baseline | IMPROVED (still below 1×) |
| **Field length vs baseline — haiku review** | ~3.4× baseline (run 81) | ~3.9× baseline (run 88) | SLIGHT REGRESSION (approaching 4× warning) |
| **Field length vs baseline — gpt-4o-mini consequences** | ~0.7× | ~0.75× | UNCHANGED |
| **Fabricated quantification (% claims)** | 0 (all matched models) | 0 (all matched models) | UNCHANGED |
| **Marketing-copy language ("game-changing", etc.)** | 0 detected in sampled runs | 0 detected in sampled runs | UNCHANGED |
| **Summary field in raw outputs** | 2–3 per plan per run (run 75–81) | 0 per plan per run (runs 82–88) | **FIXED** |
| **llama3.1 option word count (call 1)** | ~7 words avg | ~12 words avg | IMPROVED (still below 15-word floor) |
| **haiku option word count (gta_game)** | ~28 words | ~41 words | IMPROVED |
| **llama3.1 template lock ("This lever governs")** | 100% (run 75) | 100% (run 82) | UNCHANGED |
| **qwen3 "Core tension:" opener** | Present (run 78) | Present (run 85) | UNCHANGED |
| **Partial recoveries** | 2 (runs 75, 76) | 2 (runs 83, 88) | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS alignment:**

| Known Problem | Status in runs 82–88 | Notes |
|---|---|---|
| Overly optimistic scenarios | Not triggered in sampled outputs | No aspirational moonshots detected |
| Fabricated numbers | ✓ None found | PR did not regress fabrication avoidance |
| Hype language | ✓ None found | Anti-fabrication instructions held |
| Vague aspirations | Minor in llama3.1 | e.g., "Create a dynamic system…" |
| English-only validation | ✓ Not triggered | Structural-only validators in place |
| Single-example template lock | Still 100% for llama3.1 | The prescribed fix (negative constraint) has not been applied |
| Model-native template openers ("Core tension:") | Still present in qwen3 | Not yet documented in OPTIMIZE_INSTRUCTIONS |

The PR moves toward OPTIMIZE_INSTRUCTIONS goals: token waste reduced, fabrication avoidance maintained, option length partially improved. The template lock issue (documented in OPTIMIZE_INSTRUCTIONS line 69–72) remains unresolved — the prescribed fix (negative constraint) was not included in this PR.

---

## New Issues

**No new problems introduced by the PR.**

Issues surfaced or confirmed by this analysis:

1. **Hard `options == 3` validator over-reach (pre-existing, newly confirmed):** Run 82 (llama3.1 gta_game) failed because two levers had 2 options each, triggering the hard Pydantic validator and discarding the entire call. This was present before but newly confirmed in this batch. The validator comment cites "Run 89" as motivation — the validator was added specifically to guard against a known failure mode, but the cost (full call discard for 1 malformed lever) is disproportionate.

2. **Haiku review verbosity trend (pre-existing, monitored):** Haiku `review` field length is now ~430 chars avg (~3.9× baseline). This is not introduced by the PR — it was already ~355 chars in run 81 (before). The trend is increasing and approaching the 4× warning threshold. Content reads as substantive, not padded, but should be monitored for one more batch before intervening.

3. **Template lock root cause identified (pre-existing, newly diagnosed):** The code review (analysis 25 code_claude B2) identifies the root cause of 100% template lock: the phrase "This lever governs the tension between centralization and local autonomy" appears as the lead example in **both** the `Lever.review_lever` Pydantic field description (lines 100–104) and system-prompt section 4 (lines 225–227). Two identical anchors produce 100% lock for weaker models. OPTIMIZE_INSTRUCTIONS documents the class of problem (line 69–72: "single-example template lock") but the fix (negative constraint) has never been applied to the code.

---

## Verdict

**YES**: The PR successfully achieved its primary goal — removing the unused `DocumentDetails.summary` field eliminates 105 wasted LLM generations per 7-model experiment with no downstream impact. Success rate improved by 2.8 percentage points (94.3% → 97.1%). Option length improved measurably for llama3.1 (7→12 avg words) and haiku (28→41 words). No content quality regressions were introduced. The call-2/3 prefix slim did not cause any detectable regression in the after batch.

The remaining issues (template lock, hard validator, 15-word floor not fully enforced) are pre-existing and explicitly out of scope for this engineering-cleanup PR. None are new regressions.

---

## Recommended Next Change

**Proposal:** Add negative opener constraints to the `Lever.review_lever` Pydantic field description and the matching system-prompt section 4, replacing both current examples with domain-specific, non-portable alternatives to break the template-lock pull at the source.

**Specific change (synthesis.md, Recommendation section):**

In `identify_potential_levers.py`, replace the `review_lever` field description (lines 96–107) to add:
- `"Do NOT open with 'This lever governs the tension between'."`
- `"Do NOT open with 'Core tension:'."`
- Replace the two generic examples (`centralization and local autonomy`, `speed over reliability`) with domain-specific examples that cannot be lifted verbatim to any plan.

Apply matching negative constraints + new examples in system-prompt section 4 (lines 224–227). Also append to `OPTIMIZE_INSTRUCTIONS` the "model-native template openers" failure class.

**Evidence:** The recommendation is well-supported:
- llama3.1: 100% template lock in runs 75 and 82 (confirmed across two batches)
- qwen3: "Core tension:" opener in runs 78 and 85 (confirmed across two batches)
- Analysis 22 also flagged template lock — confirmed across three separate analysis rounds
- OPTIMIZE_INSTRUCTIONS already documents the root cause (line 69–72) but the fix has never been applied
- Code_claude B2 traces the exact mechanism: the same phrase appears twice (field description + system prompt), doubling the template pull

**Verify in the next iteration:**
- **llama3.1 (run ~90)**: Confirm "This lever governs the tension between" rate drops below 50% on the silo and hong_kong_game plans. Before the fix: 100% (runs 75, 82). Target: <50%.
- **qwen3 (run ~91)**: Confirm "Core tension:" opener rate drops toward 0% on parasomnia and sovereign_identity. Before: ~100% of reviews (runs 78, 85). Target: <20%.
- **haiku and gpt-4o-mini**: Confirm no regression — these models already produced diverse review openers and must not be degraded.
- **Fabrication check**: After removing the old generic examples, verify no new fabricated numbers appear in consequences or options (there is a small risk that models fill the stylistic vacuum with invented quantification).
- **Option count failures**: Check whether run 82-equivalent failures (2-option levers causing hard validator rejection) persist or whether the next PR also relaxes the `options == 3` constraint.

**Risks:**
- Negative constraints may cause over-correction: models that would write genuinely valid "This lever governs…" sentences may avoid the phrasing and produce less precise openers.
- Replacing examples with highly domain-specific ones may confuse models for plans that don't share the domain vocabulary — the examples should be chosen from different domains (financial, technical) so they generalize without being copyable.
- If the negative constraint is only in the Pydantic field description but not the system prompt (or vice versa), weaker models may still see the constraint only once and ignore it. Both locations must be updated together.
- qwen3's "Core tension:" pattern may be deeply baked in training; the negative constraint may shift it to a different formulaic opener rather than eliminating the pattern entirely.

**Prerequisites:**
- None. This change is self-contained and does not depend on any other fix.
- The `options == 3` relaxation (direction 2 from synthesis.md) is independent and can proceed in parallel or in the same PR.

---

## Backlog

**Resolved — can be removed:**
- `summary` field token waste: **closed**. Grep confirms zero `"summary"` keys in runs 82–88. The 105 wasted LLM generations per batch are eliminated.
- "at least 15 words" missing from section 6: **closed**. Line 240 of system prompt now includes it. (Pydantic schema-level gap remains as a separate item.)

**New items to add:**

1. **Hard `options == 3` validator over-reach** (`identify_potential_levers.py:131`): Change `len(v) != 3` to `len(v) < 3`. A lever with 4–5 options is not damaging; discarding the entire call for one 2-option lever is. Confirmed by run 82 (llama3.1 gta_game). One-line fix.

2. **"at least 15 words" missing from Pydantic `options` field description** (`identify_potential_levers.py:92–95`): The system-prompt constraint (line 240) partially works (llama3.1: 7→12 words), but schema-level enforcement would close the remaining gap. Append to `options` field description: `"at least 15 words with an action verb"`.

3. **Model-native template openers not in OPTIMIZE_INSTRUCTIONS**: The constant (lines 27–73) documents five known failure classes but is missing "model-native template openers" confirmed across analyses 22, 24, and 25. Without this entry, future optimization agents will keep rediscovering it. Proposed addition documented in synthesis.md.

4. **`LeverCleaned.review` field description duplicates leaked examples** (`identify_potential_levers.py:190–200`): `LeverCleaned` is never passed to an LLM — its field descriptions serve no prompting purpose. The examples are dead weight and a secondary site where a future editor might inadvertently re-introduce the template. Low priority; no runtime impact.

5. **Closure capture in `execute_function` loop** (`identify_potential_levers.py:291`): `messages_snapshot` is safe only because `llm_executor.run()` is currently synchronous. Adding a default-argument freeze (`def execute_function(llm, msgs=messages_snapshot)`) prevents latent bug if the executor is later made async.

6. **Global dispatcher event handler cross-contamination** (`runner.py:104–109`, `146–148`): Under `workers > 1`, each plan's `track_activity` handler is added to the global dispatcher, routing all concurrent plans' events to all handlers. Affects per-plan debug files, not final output quality. Address when multi-worker plans are user-exposed.

**Retained from before (still open):**
- Review template lock for llama3.1 and qwen3 → **addressed by Recommended Next Change above**
- Haiku review verbosity (~3.9× baseline) → monitor for one more batch; intervene if >4×
- qwen3 JSON extraction failure (run 78) did not recur in run 85 — tentatively resolved, but one more qwen3 run on parasomnia would confirm
