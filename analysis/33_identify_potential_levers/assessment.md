# Assessment: Add lever_classification field, fix haiku config, adaptive retry loop

## Issue Resolution

**PR #349 targeted four issues:**

**1. lever_classification field** — Add a new `"category — what this lever decides"` phrase, placed last in schema so sequential generators (llama3.1) fill important fields first before the new field.

**Result: Partially resolved. Works for strong models; breaks qwen3.**
- haiku (run 44), gemini (run 43), gpt-5-nano (run 40), gpt-4o-mini (run 42): all generate lever_classification correctly with high-quality, domain-specific content. E.g. haiku parasomnia: `"execution — who qualifies for admission and how much pre-screening precedes residential enrollment"`. This is genuine value.
- qwen3 (run 41): fails 3/5 plans (silo, sovereign_identity, hong_kong_game) with `Field required: lever_classification [type=missing]`. The first call generates all 6 levers but omits the new field entirely. Because `len(responses) == 0` → the adaptive retry immediately raises (`identify_potential_levers.py:338`) without attempting call 2. qwen3 gets zero retries.
  Evidence: `history/2/41_identify_potential_levers/events.jsonl` lines 5, 7, 8 — three `run_single_plan_error` events, all with 6 `Field required: lever_classification` errors from Attempt 0.
- llama3.1 (run 38): generates the field but copies system prompt examples verbatim. Verified in `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`: `protagonist_background` gets `"governance — who oversees the review process"` (exact copy), `hong_kong_as_paranoia_machine` gets `"methodology — which data collection approach to use"` (exact copy), four levers get `"[category] — how to sequence the rollout phases"` (structural copy). 7 of 16 levers in that plan carry wrong/template-copied classifications.
- **Residual symptom**: Required field + no first-call retry = permanent hard failure for any model that doesn't generate the field on call 1. The field should be `Optional[str] = None` during rollout.

**2. haiku max_tokens fix (16000 → 8192)**

**Result: Preventative fix with no observable test-set impact.** haiku succeeded on 5/5 plans both before and after. Total output tokens per plan (3 calls combined) were 9380–10301 in run 44 — well below the 8192-per-call cap. The fix is correct and prevents potential truncation on larger-context plans outside the test set.

**3. review_lever minimum relaxed (50 → 10 chars)**

**Result: Valid and low-risk.** No excessively short reviews appear in the after batch. No observable impact on success metrics. The only issue is a stale docstring (`identify_potential_levers.py:154` still says "at least 50 characters"; code checks `< 10`).

**4. Adaptive retry loop (fixed 3 calls → adaptive up to 5)**

**Result: Genuine improvement for calls 2+; design gap on first-call failures.** llama3.1 sovereign_identity improved from 12 levers (2 calls) to 18 levers (3 calls); hong_kong improved from 13 to 16 levers. The retry logic works exactly as intended when call 1 succeeds but yields <15 levers.

Design gap: when call 1 fails schema validation (`len(responses) == 0`), the loop raises immediately — never reaching call 2. qwen3's 3/5 failures all fall into this path. Under the old fixed-3-call loop, qwen3 would have received 3 call attempts regardless; under the new adaptive loop, it receives 1 then quits. The PR made qwen3's situation strictly worse than before.

---

## Quality Comparison

Models in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5 (all 7 shared).

| Metric | Before (runs 03–09) | After (runs 38–44) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 34/35 = 97.1% | 31/35 = 88.6% | **REGRESSED (-8.5pp)** |
| **LLMChatErrors** | 1 (gpt-oss-20b JSON EOF) | 4 (3 qwen3 lever_classification; 1 llama3.1 options < 3) | **REGRESSED** |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (< 3)** | 0 | 1 (llama3.1/silo: all 6 levers have 2/1/1/1/1 options) | **REGRESSED** |
| **Lever name uniqueness** | Stable (typo variants pass dedup) | Stable | UNCHANGED |
| **Template leakage — review_lever** | Present: llama3.1 100% "The options [verb]" parasomnia; 62.5% gta_game | Still present; not addressed by this PR | UNCHANGED |
| **Template leakage — lever_classification (llama3.1)** | N/A (field didn't exist) | 7/16 levers in hong_kong_game copy system prompt examples verbatim | **NEW REGRESSION** |
| **Review format compliance** | Stable | Stable | UNCHANGED |
| **Consequence chain format** | Stable | Stable | UNCHANGED |
| **Content depth (avg option length)** | Stable | Stable; haiku options 1.7× baseline (slight improvement from 2.0×) | UNCHANGED |
| **Cross-call lever count — llama3.1** | sovereign_identity: 12 (2 calls), hong_kong: 13 (2 calls) | sovereign_identity: 18 (3 calls), hong_kong: 16 (3 calls) | **IMPROVED** |
| **Over-generation (> 7 levers/call)** | Moderate; downstream handles extras | Moderate; adaptive retry may add a 4th or 5th call for under-generators | UNCHANGED |
| **Field length vs baseline — haiku review** | 4.1× (hong_kong) — pre-existing | 3.0× (hong_kong) — slight improvement | SLIGHTLY IMPROVED |
| **Field length vs baseline — haiku consequences** | 2.5× (hong_kong) | 2.1× (hong_kong) | SLIGHTLY IMPROVED |
| **Field length vs baseline — gemini/gpt-5-nano** | Within 1.0–1.5× | Within 1.0–1.5× | UNCHANGED |
| **Fabricated quantification — haiku** | 31 fabricated % patterns across 5 plans (run 09) | 44 fabricated % patterns across 5 plans (run 44): silo +5, parasomnia +8 | **SLIGHT REGRESSION** |
| **Fabricated quantification — llama3.1 consequences** | 5 fabricated "by at least X%" (run 03, gta_game call 1) — prior PR regression | Not specifically tracked in after-batch; not worsened | UNCHANGED |
| **Marketing-copy language** | Stable | Stable | UNCHANGED |
| **Partial recovery events** | 2 (run 03: llama3.1 sovereign_identity 2/3, hong_kong 2/3) | 0 explicit partial recoveries for completed plans; runner.py hardcodes expected_calls=3, emitting spurious events for 1-call successes | SEE NOTE |
| **runner.py expected_calls=3 accuracy** | Accurate (fixed 3-call loop) | Stale: plans completing in 1 call emit false-positive `partial_recovery` events | **NEW BUG** |
| **haiku max_tokens** | 16000 (above API cap) | 8192 (correct) | **FIXED (preventative)** |
| **lever_classification presence in outputs** | N/A | 100% in successful plans (0/31 missing field) | **NEW FEATURE** |
| **lever_classification content quality (strong models)** | N/A | High: domain-specific, accurate, non-portable phrases | **NEW POSITIVE** |
| **lever_classification content quality (llama3.1)** | N/A | Poor: 7/16 levers in hong_kong carry verbatim-copied example phrases | **NEW NEGATIVE** |

**OPTIMIZE_INSTRUCTIONS alignment:**
The PR description states the goal is "realistic, feasible, actionable plans." Three new violations of that goal appeared in the after batch:
1. qwen3 failures produce *no* plan output for 3/5 plans — the opposite of actionable.
2. llama3.1 lever_classifications are semantically wrong (e.g., `protagonist_background` lever classified as "governance — who oversees the review process") — actively misleading to a downstream consumer trying to prioritize levers by category.
3. The `OPTIMIZE_INSTRUCTIONS` does not yet document the "new required field → first-call validation failure → no retry recovery" failure mode, meaning future PR authors will replicate the qwen3 regression pattern.

The haiku fabricated % claims regression (31→44) also moves away from the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers, though the increase is moderate and pre-dates this PR conceptually.

---

## New Issues

1. **qwen3 3/5 regression — required field with no retry recovery.** Adding `lever_classification: str` (required) as a schema field causes qwen3 to fail 3 plans that previously succeeded. The adaptive retry's immediate-raise-on-first-failure (`identify_potential_levers.py:338`) provides zero recovery. This is the highest-priority new issue.
   Fix: change `lever_classification: str` to `lever_classification: Optional[str] = Field(default=None, ...)` and update the `check_lever_classification` validator to short-circuit on `None`. Also update `LeverCleaned.lever_classification` at line ~195 to `Optional[str]`.

2. **lever_classification template lock for llama3.1.** System prompt Section 2 examples are generic portable phrases ("governance — who oversees the review process", "methodology — which data collection approach to use", "execution — how to sequence the rollout phases") that can be applied to any lever in any domain. llama3.1 copies them verbatim: 4 levers in hong_kong_game carry "how to sequence the rollout phases", 2 carry "which data collection approach to use", 1 carries "who oversees the review process" — 7/16 levers misclassified. This is the exact failure mode documented in OPTIMIZE_INSTRUCTIONS for `review_lever`, introduced by this PR.
   Fix: Replace all three Section 2 examples with non-portable domain-anchored phrases across different domains (matching the "agriculture example" pattern).

3. **runner.py `expected_calls=3` stale artifact.** `runner.py:115` (`expected_calls = 3`) and `runner.py:514–518` (`calls_succeeded < 3` → emits `partial_recovery` event) were not updated for the adaptive retry design. Plans legitimately completing in 1 call (if ≥15 levers generated on call 1) now emit false-positive `partial_recovery` events that pollute `events.jsonl` and can mislead the assessment pipeline.
   Fix: Remove the `expected_calls=3` constant and the `partial_recovery` event block, or derive `expected_calls` dynamically from `max_calls`.

4. **`check_review_format` docstring stale.** `identify_potential_levers.py:154` says "minimum length (at least 50 characters)" but line 157 checks `if len(v) < 10`. A developer reading the docstring will have incorrect expectations.
   Fix: Update docstring to "minimum length (at least 10 characters)".

5. **llama3.1/silo: options < 3 new failure.** Previously (run 03), llama3.1 succeeded on silo with 19 levers all having 3+ options. After the PR (run 38), silo fails with `options must have at least 3 items, got 2/1/1/1/1`. The added output complexity from the new `lever_classification` field appears to cause llama3.1 to cut corners on the `options` list. This may be resolved when `lever_classification` is made Optional (less schema pressure).

6. **haiku fabricated quantification slightly worsened (31→44 claims).** Not directly caused by this PR, but correlates with the new lever_classification field increasing total output length. This is a known pre-existing issue but worth monitoring.

---

## Verdict

**CONDITIONAL**: Keep the adaptive retry loop, haiku max_tokens fix, and review_lever minimum relaxation unconditionally. The `lever_classification` field is worth retaining but must be changed from `str` (required) to `Optional[str] = None` before it can be considered production-ready.

The adaptive retry is a genuine measurable improvement (llama3.1 sovereign_identity: 12→18 levers, hong_kong: 13→16). The haiku max_tokens fix is a correct preventative fix. The review_lever minimum relaxation is clean and low-risk.

The `lever_classification` field as currently implemented causes a net -8.5pp success rate regression (the PR's largest observed impact) through the combination of a required field constraint and the adaptive retry's immediate-raise-on-first-failure design. The content quality it provides for strong models (haiku, gemini) is genuinely useful, but qwen3's 3/5 hard failures and llama3.1's new template-lock contamination make the field a net negative at current implementation. The fix (make Optional) is a one-line type change with no downside risk. Once qwen3 recovers and the generic examples are replaced, the field becomes a net positive.

---

## Recommended Next Change

**Proposal**: Change `lever_classification: str` to `lever_classification: Optional[str] = Field(default=None, ...)` in `identify_potential_levers.py`, update the `check_lever_classification` validator to short-circuit on `None`, and update `LeverCleaned.lever_classification` to `Optional[str]`. In the same PR: replace all three Section 2 system-prompt examples for lever_classification with non-portable domain-anchored phrases.

**Evidence**:
- qwen3 3/5 failures all trace to `Field required: lever_classification` at Attempt 0 (`history/2/41_identify_potential_levers/events.jsonl`). The fix is confirmed at `identify_potential_levers.py:111` (field type) and line 338 (immediate raise — note the Optional fix makes the first-call output valid, so `len(responses)` will no longer be 0 for qwen3).
- llama3.1 lever_classification lock is confirmed in `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`: `protagonist_background` → `"governance — who oversees the review process"` (verbatim copy of `identify_potential_levers.py:229`); `hong_kong_as_paranoia_machine` → `"methodology — which data collection approach to use"` (verbatim copy of line 230); 4 levers → `"[category] — how to sequence the rollout phases"` (structural copy of line 231). 7/16 levers affected.
- The OPTIMIZE_INSTRUCTIONS pattern ("Examples must avoid reusable transitional phrases that fit any domain") was violated by all three Section 2 examples.
- The synthesis.md from analysis 33 proposes non-portable replacement examples: `"execution — which city blocks to relay the water main in first to minimize service interruption"`, `"governance — which of the four county agencies has authority to sign the discharge permit"`, `"methodology — whether to run paired-sample or repeated-measures ANOVA for the sleep-disruption dataset"`. These follow the "agriculture example" pattern and are non-portable.
- Also replace the single example in `Lever.lever_classification` field description (line ~115) with a domain-specific one.

**Verify in next iteration**:
- qwen3: success rate returns to 5/5 (was 2/5 in run 41; was 5/5 in run 06 before PR)
- qwen3 gta_game and parasomnia (the 2 plans that did succeed): confirm lever_classification is still generated and has reasonable quality when field is Optional
- llama3.1 hong_kong_game: lever_classification template-lock rate (was 7/16; target < 3/16)
- llama3.1 silo: confirm plan now succeeds (the Optional fix removes schema pressure, likely resolving the options < 3 failure)
- llama3.1: verify no new lever_classification-related template-lock patterns from the replacement examples
- gpt-5-nano, gpt-4o-mini, gemini, haiku: confirm lever_classification is still generated and quality is maintained even when Optional (these models generate it reliably; Optional should not affect them)
- runner.py: confirm no spurious `partial_recovery` events in events.jsonl after the expected_calls=3 fix
- Fabricated % claims in haiku (was 44; watch for further increase)

**Risks**:
1. Making the field Optional means qwen3 outputs will have `null` lever_classifications. If the downstream enrich step or lever display code assumes `lever_classification` is always a non-null string, it will need a null-guard. Check `LeverCleaned` usage downstream before merging.
2. The adaptive retry's first-call-failure behavior remains: if qwen3 generates the field on call 1 but fails other validation (e.g., options < 3), it will still get no retry. The Optional fix only recovers the specific `lever_classification: Field required` failure mode.
3. Replacement examples for lever_classification must themselves avoid portable language. A new water-main example should work, but review it for any sub-phrases that could be copied to unrelated levers.
4. `LeverCleaned.lever_classification` also needs to be `Optional[str]` to avoid a type mapping error when the raw `Lever.lever_classification` is `None`. This is a likely gotcha if not updated in the same PR.

**Prerequisite issues**: None. The adaptive retry is already in place; making the field Optional only requires the type change + validator guard + LeverCleaned update. No other fix is needed first.

---

## Backlog

**Resolved by this PR and removable:**
- gpt-oss-20b JSON EOF truncation (run 04, sovereign_identity) — run 39 succeeded on this plan. Likely non-deterministic and resolved; remove from backlog.
- haiku max_tokens over-cap — fixed by this PR.
- Partial recovery 2-call plans for llama3.1 (sovereign_identity, hong_kong_game) — adaptive retry now reaches 3 calls for both.

**Carry forward (unchanged):**
- Template lock "The options [verb]" in review_lever — all three review examples still use options-as-subject construction. Not addressed by this PR. Still the primary open issue from analysis 28.
- OPTIMIZE_INSTRUCTIONS self-contradiction (lines 77–79 praise agriculture example opener as safe; it still uses "none of the options price in").
- Multi-call template divergence — add to OPTIMIZE_INSTRUCTIONS (call 1 vs calls 2–3 produce different format when prompt examples partially displace a lock).
- Replacement-example contamination pattern — add to OPTIMIZE_INSTRUCTIONS.
- Fabricated % claims in llama3.1 consequences (run 03 gta_game levers 1–6, "by at least X%") — introduced by PR #340's replacement example 3; not addressed here.
- `Lever.options` field description says "Exactly 3 options" but validator enforces minimum 3. Clean fix, bundle with next PR.
- Cross-field contamination validator (`consequences` field). Absent in current runs; low priority.
- S4 / MEMORY.md "iteration 2" — assistant turn serialization: stateless multi-call loop means call 2 cannot generate levers complementary to call 1's output. Known architectural gap; not addressed here.
- haiku `review` field verbosity (3–4× baseline). Pre-existing; not introduced by this PR.

**New additions:**
- **qwen3 required-field regression** — introduced by PR #349. `lever_classification: str` causes qwen3 to fail 3/5 plans. Fix: make field Optional. Priority: high (direct success-rate regression).
- **lever_classification template lock (llama3.1)** — introduced by PR #349. Generic Section 2 examples copied verbatim. Fix: replace with non-portable domain-anchored examples. Priority: high (content quality regression for all llama3.1 lever_classification values).
- **runner.py stale expected_calls=3** — `runner.py:115` and `runner.py:514–518` hardcode the pre-PR constant; emit spurious `partial_recovery` events for 1-call successes. Fix: remove or derive dynamically. Priority: medium (pollutes analysis pipeline).
- **check_review_format docstring stale** — `identify_potential_levers.py:154` says 50 chars; code checks 10. Fix: update docstring. Priority: low (trivial one-liner).
- **New required-field failure pattern not in OPTIMIZE_INSTRUCTIONS** — "New required field + first-call validation failure + no retry recovery" is a confirmed failure mode not yet documented. Add to OPTIMIZE_INSTRUCTIONS after the Optional fix is confirmed working.
- **lever_classification template-lock pattern not in OPTIMIZE_INSTRUCTIONS** — same class of issue as review_lever lock but for a new field with Section 2 examples. Add note to OPTIMIZE_INSTRUCTIONS extending the single-example lock warning to cover any new field whose examples are generic portable phrases.
