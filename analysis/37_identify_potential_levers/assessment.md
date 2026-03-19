# Assessment: fix: B1 step-gate partial_recovery, add medical review example

## Issue Resolution

**PR #355 targeted two issues:**

### 1. B1 step-gate fix
Scope `partial_recovery` events to `identify_potential_levers` only by adding a step-name guard in `runner.py`. Remove the stale `expected_calls=3` constant from `_run_levers()`.

**Outcome: Logically correct, non-regressive.** The step guard at `runner.py:517` correctly prevents spurious `partial_recovery` events for `identify_documents` (which always returns `calls_succeeded=1`). Not directly observable in this dataset (all history runs are `identify_potential_levers`), but the code change is sound.

**Gap not fully closed (B3 in code_claude.md):** The `expected_calls=3` literal was removed from `_run_levers()` but remains in the `_run_plan_task()` event emission at line 523 (`"expected_calls": 3`). This value still appears in run 72's `partial_recovery` event for hong_kong (`events.jsonl` line 8). For `identify_potential_levers` the value is accidentally correct (the loop nominally targets 3 calls), but it is conceptually stale and should be derived from `PlanResult`.

### 2. Medical review example
Replace the Section 106 urban-planning example with an IRB/clinical-site sequential-overhead example. Stated goal: break template lock in medical/scientific plans without domain overlap with test plans.

**Outcome: Partial, with a measured regression.**

**Confirmed positive (P1 in insight):** llama3.1 parasomnia call-2 template lock fell from 100% ("The lever misses/overlooks/neglects…") to 0% (mechanism-based reviews). Confirmed by direct file read: `history/2/66_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` levers 7–12 show substantive domain-grounded reviews (e.g., "Participant flow through the residential unit is highly seasonal, peaking in summer months when students are on break — a scheduling challenge that erodes sample representativeness…").

**Confirmed regressions:**
1. **Haiku gta_game hard failure (N1):** Run 72 haiku gta_game failed with `LLMChatError` (JSON EOF at column 40,173), producing zero output. Run 58 haiku gta_game passed with no issues. The medical IRB example (mechanism-dense, ~50 words, naming concrete timelines) caused haiku to generate reviews averaging ~550 chars in parasomnia (confirmed: `history/2/72_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`, reviews 640–700+ chars each). For gta_game — a plan that generates 21+ raw levers × 3 calls — this verbosity multiplied output size to ~40KB, overflowing Anthropic's JSON response limit. Confirmed by `events.jsonl` line 5: `"Invalid JSON: EOF while parsing a string at line 1 column 40173"`.

2. **llama3.1 silo call-1 empty reviews (N2):** 6 of 20 levers from the first LLM call in run 66 silo have `review == name` (e.g., `"review": "Resource Prioritization"`, `"review": "Security Protocols"`). Confirmed by file read: `history/2/66_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` levers 1–6. Run 52 silo had substantive reviews for the same levers. The `check_review_format` validator (length ≥ 10, no brackets) passes these silently — "Resource Prioritization" is 22 chars, no brackets.

**Residual symptoms (unchanged from before):**
- llama3.1 parasomnia call-1: "The options miss…" pattern persists in all 6 levers (100% lock, confirmed by file read of levers 1–6 in run 66 parasomnia).
- llama3.1 gta_game: byte-for-byte identical output in runs 52 and 66, including all lever UUIDs. No game-dev example covers this domain; the lock is 100% and entirely unaffected by the medical example.
- **New in this run:** llama3.1 parasomnia call-3 developed a "[Lever Name] lever overlooks/neglects/misses" pattern (5/5 levers, 100% lock in call 3). The medical example broke the 2nd-call "The lever misses" pattern, but a new lever-name-as-subject template emerged in call 3.

---

## Quality Comparison

Models in **both** batches: llama3.1 (52/66), gpt-oss-20b (53/67), gpt-5-nano (54/68), qwen3-30b (55/69), gpt-4o-mini (56/70), gemini-2.0-flash (57/71), haiku-4-5 (58/72). All 7 models shared; full comparison is valid.

| Metric | Before (runs 52–58) | After (runs 66–72) | Verdict |
|--------|--------------------|--------------------|---------|
| **Plan-level success rate** | 35/35 = 100% | 34/35 = 97.1% (haiku gta_game error) | REGRESSION |
| **Hard errors (no output)** | 0 | 1 (run 72 haiku gta_game, JSON EOF @col 40173) | REGRESSION |
| **LLMChatErrors** | 0 | 1 | REGRESSION |
| **Haiku ok rate** | 5/5 = 100% | 4/5 = 80% | REGRESSION |
| **Haiku partial recoveries** | 2 (silo, para; likely B2 false alarms) | 1 (hong_kong) + 1 gta hard error | REGRESSION (real failure vs. false alarm) |
| **llama3.1 partial recoveries** | 1 (gta 2/3) | 0 (all 5 plans 3/3) | IMPROVED |
| **calls_succeeded=3 rate (all models)** | 32/35 = 91.4% | 33/35 = 94.3% | SLIGHT IMPROVEMENT |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | High (case-sensitive dedup) | High (same) | UNCHANGED |
| **Template lock — llama3.1 parasomnia call-1** | 6/6 = 100% "The options miss" | 6/6 = 100% "The options miss" | UNCHANGED |
| **Template lock — llama3.1 parasomnia call-2** | 8/8 = 100% "The lever misses" | 0/6 = 0% (mechanism-based) | **FIXED** |
| **Template lock — llama3.1 parasomnia call-3** | Low / non-template | 5/5 = 100% "[Name] lever overlooks" | NEW REGRESSION |
| **Template lock — llama3.1 gta_game (all calls)** | 100% (identical output) | 100% (byte-for-byte identical to run 52) | UNCHANGED |
| **Template lock — llama3.1 silo calls 2–3** | ~0% (domain-specific) | ~0% (maintained) | UNCHANGED |
| **Empty reviews (review == name)** | 0 | 6 (run 66 silo call-1) | NEW REGRESSION |
| **Fabricated % claims** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Low | Low | UNCHANGED |
| **Review length vs baseline — haiku parasomnia** | ~1.5–2× baseline est. | ~3.9× baseline (~550 chars vs ~140 chars) | REGRESSION (exceeds 2× warning threshold) |
| **Review length vs baseline — llama3.1 hong_kong** | ~1.3× baseline | ~1.6× baseline | SLIGHT INCREASE (within 2× threshold) |
| **Options length (llama3.1 silo)** | ~0.50× baseline (label-like) | ~0.50× baseline (unchanged) | UNCHANGED (pre-existing) |
| **Cross-call duplication** | Present (semantic dups) | Present (same) | UNCHANGED |
| **Over-generation count (>7 levers/call)** | Haiku 8+ per call routinely | Haiku 8+ per call routinely | UNCHANGED |
| **Haiku quality (substantive plans)** | High | Extremely high for parasomnia (verbose but grounded) | IMPROVED (quality) / REGRESSED (reliability) |

**Key note on haiku verbosity:** The medical IRB example produced a verbosity amplification effect for haiku specifically. Run 72 haiku parasomnia reviews cite concrete mechanisms (IRB approval, €3.8M budget, 200–250 PSG nights, €180K equipment cost) and are factually grounded — content quality is high. However, the 3.9× length increase vs. baseline exceeds the 2× warning threshold and directly caused the gta_game hard failure. This is a case where quality and reliability pulled in opposite directions; reliability failure takes priority.

---

## New Issues

1. **Haiku verbosity amplification (root cause of gta_game failure).** The medical IRB example uses mechanism-dense language (~50 words, naming IRB approval, site-initiation visits, 8–14 week timelines). Haiku interprets this as a license to generate equivalently detailed reviews for all plans. Run 72 parasomnia reviews average ~550 chars (3.9× baseline ~140 chars). For gta_game (21+ raw levers × 3 calls × verbose JSON), the total response exceeds the Anthropic API output limit, causing JSON EOF at column 40,173 with zero output. No `max_tokens` guard exists in the `sllm.chat()` call. This is a new failure mode not present in any prior run.

2. **Empty reviews pass validation undetected (B1 in code_claude.md for #355).** The `check_review_format` field validator at `identify_potential_levers.py:139–155` checks only `len(v) >= 10` and absence of square brackets. A lever name like "Resource Prioritization" (22 chars, no brackets) satisfies both conditions. 6 levers in run 66 silo call-1 passed validation with `review == name`. This requires a Pydantic `@model_validator(mode='after')` cross-field check — a `@field_validator` cannot access the sibling `name` field.

3. **New call-3 template lock: "[Lever Name] lever overlooks/neglects/misses" (parasomnia, run 66).** The medical example successfully broke the 2nd-call "The lever misses" pattern (P1), but the model invented a new grammatical template in call 3: leveraging the lever name itself as subject ("Participant Flow Optimization lever misses…", "Sensor Data Quality Enhancement lever overlooks…"). The root cause is the shared "X, but Y" adversarial contrast structure shared by examples 1 and 3 — the model extracts the contrast structure and rotates the grammatical subject (call 1: "The options"; call 2: broken by medical example; call 3: "[Name] lever").

4. **gta_game domain gap confirmed irrecoverable by prompt-only change at temperature=0.** Runs 52 and 66 produce byte-for-byte identical `002-10-potential_levers.json` files, including all lever UUIDs. If llama3.1 runs at temperature=0, no prompt change can alter the output. A game-dev example is a necessary but possibly insufficient fix — a temperature increase may also be required.

---

## Verdict

**CONDITIONAL**: Keep the B1 step-gate fix unconditionally (logically correct, non-regressive). The medical example delivers a confirmed partial improvement — llama3.1 parasomnia call-2 template lock broken from 100% to 0% — but introduces a hard failure for haiku on gta_game (a plan that had zero failures in all prior runs). A plan producing zero output is worse than a plan producing locked reviews. The PR must not be reverted, but requires an immediate follow-up fix (max_tokens guard) before it represents a clean improvement over the analysis-35 baseline.

---

## Recommended Next Change

**Proposal:** Add a `max_tokens=12000` parameter to the `sllm.chat()` call in `identify_potential_levers.py` (the `execute_function` closure at lines 292–296), and add a system-prompt directive in Section 6 capping each `review_lever` at 120 words.

**Evidence:** The synthesis is correct that this is the highest-priority fix. The haiku gta_game failure is the only change in this entire dataset that moved `status` from `ok` to `error` — every other regression still produces usable output. The root cause is confirmed by three independent data points: (1) run 72 haiku parasomnia reviews average ~550 chars (3.9× baseline), (2) the gta_game error occurs at column 40,173 (consistent with a verbosity-multiplied response), (3) run 58 haiku gta_game passed at the same temperature and plan before the medical example was introduced. The fix is a single parameter addition with no downside for models that already generate concise output.

The synthesis also recommends adding a `OPTIMIZE_INSTRUCTIONS` bullet for verbosity-amplification risk (I5 in code_claude.md for #355). This is correct and should be included in the same PR to document the newly discovered failure mode.

**Verify in next iteration:**
- **Primary:** Haiku gta_game returns to `status=ok` (calls_succeeded=3). Check `history/2/XX/events.jsonl` for zero `run_single_plan_error` events for gta_game.
- **Primary:** Haiku parasomnia review lengths drop to ≤120-word (≈600-char) range. Sample `history/2/XX/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — review fields should be < 700 chars each.
- **Secondary:** Verify no truncation regression for other models. Check that qwen3-30b, gpt-4o-mini, and gemini-flash still produce calls_succeeded=3 for all 5 plans. Their review lengths (typically 150–300 chars) are well below 120 words, so no truncation expected.
- **Retention:** Confirm P1 (parasomnia call-2 lock at 0%) is preserved — the max_tokens change should not affect the domain-matching benefit of the medical example. Check that call-2 levers in parasomnia still show mechanism-based reviews.
- **B1 validator gap:** After verifying max_tokens fix, separately check whether the model-level cross-field validator (review ≠ name) has been added. The llama3.1 silo empty-review regression (N2) is a second follow-up fix. If not yet implemented, note it in the next assessment.
- **Haiku hong_kong partial_recovery (N4):** Run 72 hong_kong had calls_succeeded=2 (partial_recovery). After the max_tokens fix, verify whether this persists. If hong_kong partial_recovery disappears when review lengths are capped, it confirms verbosity was the proximate cause. If it persists, haiku may have a structural reliability issue with hong_kong independent of length.

**Risks:**
- Setting `max_tokens=12000` too low could truncate valid verbose responses from strong models. At 12,000 tokens (~9,000 words): 21 levers × 3 calls × 120 words/review ≈ 7,560 words of review alone, plus options/consequences, well within 9,000 words. Safe threshold.
- The system-prompt word cap ("under 120 words") might cause haiku to stop mid-chain in a complex mechanism review. Mitigated by the generous cap — even 120 words (≈600 chars) is 4× baseline review length, which is adequate for detailed mechanism chains.
- If the max_tokens cap solves the hard failure, there may be pressure to consider the PR "done." The call-3 template lock ("[Name] lever overlooks") and the parasomnia call-1 lock ("The options miss") are still unresolved and should remain active backlog items.

**Prerequisite issues:**
- None — the max_tokens fix is self-contained and does not depend on any other fix being in place first.

---

## Backlog

**Resolved by PR #355 (remove from backlog):**
- "The lever misses/overlooks" secondary lock in llama3.1 parasomnia call-2 — FIXED (100% → 0%, P1 confirmed).

**New items to add:**
- **Haiku verbosity amplification + max_tokens guard** (CRITICAL — causes hard failure for gta_game). No `max_tokens` on `sllm.chat()` in `execute_function`. Fix: `sllm.chat(messages_snapshot, max_tokens=12000)` + add "Keep each `review_lever` under 120 words" to Section 6. File: `identify_potential_levers.py:292–296`, Section 6.
- **review == name validator gap** (B1 in code_claude.md for #355, HIGH). `check_review_format` cannot catch lever names verbatim as reviews. Requires `@model_validator(mode='after')` in `Lever` to compare `self.review_lever.strip().lower() == self.name.strip().lower()`. Also raise min-length check from 10 to 30 chars. File: `identify_potential_levers.py:139–155`.
- **New "[Name] lever overlooks" call-3 template lock in parasomnia** (MEDIUM). Emerged when the medical example broke the call-2 lock. Root cause: examples 1 and 3 share the "X, but Y" adversarial contrast structure, violating OPTIMIZE_INSTRUCTIONS guidance. Fix: restructure example 1 or 3 to use a different rhetorical form (e.g., additive-risk chain, conditional inversion). File: `identify_potential_levers.py:225–228`.
- **OPTIMIZE_INSTRUCTIONS: verbosity-amplification failure mode** (MEDIUM). Strong instruction-following models mirror example verbosity, not just structure. A 250-word example licenses 500-word reviews. Add to known problems: "Keep every `review_lever` example under 80 words and add an explicit length cap to Section 6." File: `identify_potential_levers.py:27–81`.

**Remaining items from analysis-35 backlog (still open):**
- **Template lock — llama3.1 parasomnia call-1**: "The options miss…" 6/6 = 100%. Unaffected by two example replacements. Likely requires the explicit Section 5 prohibition.
- **Template lock — llama3.1 gta_game**: 100%, byte-for-byte identical output across all runs. Requires (a) game-dev domain example AND possibly (b) temperature increase if llama3.1 runs at temp=0.
- **Shared adversarial contrast structure in examples 1 and 3** (S3/I2): Both use "X [positive claim], but [hidden risk] [negates outcome]". Violates OPTIMIZE_INSTRUCTIONS "no two examples should share a sentence pattern." Direct cause of call-3 template migration.
- **Section 5 prohibition missing** (I4 from analysis-35): No explicit prohibition against "The options", "These options", "The lever", "These levers" as review openers. Confirmed gap.
- **B2 false `partial_recovery` threshold** (`runner.py:517–523`): `< 3` fires for legitimate 2-call success. Also: `logger.warning` at `runner.py:120–124` fires for every 2-call success. Should be gated on lever count vs. `min_levers`. Medium effort.
- **`lever_index` dead field** (S1): Generated but never transferred to `LeverCleaned`. Cleanup PR.
- **`strategic_rationale` dead field** (S2): ~100 words wasted per call (105 calls/iteration ≈ 10,500 words). Verify no downstream use, then remove.
- **Option word-count validator** (S4): 15-word minimum in Section 6 unvalidated. llama3.1 silo options average ~7 words. Soft warning (not raise) for options < 10 words.
- **Case-sensitive name deduplication** (B3 from code_claude.md analysis-35): `lever.name` set comparison is case-sensitive. Fix with `.strip().lower()` normalization while preserving original casing.
- **Dispatcher cross-thread contamination** (B2 from code_claude.md analysis-35): Low practical impact, deferred.
