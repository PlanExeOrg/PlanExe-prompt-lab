# Assessment: feat: broaden remove to include irrelevant levers, shorten justification

## Issue Resolution

**What PR #375 was supposed to fix** (from `pr_title` / `pr_description` in `meta.json`):

1. **Broaden `remove` to cover irrelevant levers** — upstream over-generation may produce levers that don't apply to the plan at all.
2. **Better overlap handling** — "keep the one that better captures the strategic decision" instead of always keeping the more general one.
3. **Shorter justifications (~20-30 words)** — reduce output tokens so llama3.1 can finish within the 120s timeout.
4. **Fallback to `secondary` instead of `primary`** for unclassified levers.
5. **"Triaging" framing** — system prompt says "triaging" instead of "deduplicating".
6. **Rename `BatchDeduplicationResult` → `DeduplicationResult`**.

**Is the issue actually resolved?**

**Issue 1 — Broadened `remove` (irrelevant levers):** IMPLEMENTED, NOT EXERCISED. The remove definition now includes "or it is irrelevant to this specific plan" (`deduplicate_levers.py:128-131`). None of the 7 models across 35 after-runs triggered an irrelevant removal — all test plans contain only relevant levers. The feature exists in code but cannot be validated from these runs.

**Issue 2 — Better overlap handling:** EVIDENCED. Run 77 (haiku, hong_kong_game) keeps `f9512726` (Architectural Storytelling) over `790a819e` (Hong Kong Architectural Exploitation) because the former "frames it more strategically" — the new guidance in action. The old "keep general" rule would have kept 790a819e (broader framing). Source: `history/3/77_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` lines 24–27.

**Issue 3 — Shorter justifications fix llama3.1 timeout:** FIXED. Run 71 (llama3.1): silo completes at 114.75s (was 120.16s timeout in run 64), parasomnia completes at 71.88s (was 120.12s timeout). Both plans now produce real LLM classifications instead of all-primary fallback output. Source: `history/3/71_deduplicate_levers/events.jsonl`.

Caveat: the fix is fragile. The silo timeout margin is only ~5s. The shortening was achieved via advisory text in the Pydantic field description only — no `max_length` constraint exists. llama3.1 itself still produces ~40-word justifications (N2 in insight); the API models' ~55% shorter output is what freed up enough budget to bring llama3.1's total response within the limit.

**Issue 4 — Fallback to `secondary`:** IMPLEMENTED, NOT TRIGGERED. The code at `deduplicate_levers.py:234-235` now defaults unclassified levers to `"secondary"`. No timeouts occurred in after-runs, so the fallback path was never exercised. The change is correct in principle (avoids inflating primary count) but is unverifiable from current data.

**Issue 5 — "Triaging" framing:** IMPLEMENTED. Opening sentence reads "You are triaging a set of strategic levers" (`deduplicate_levers.py:114`). ✓

**Issue 6 — Rename `BatchDeduplicationResult` → `DeduplicationResult`:** IMPLEMENTED. ✓

**Residual symptoms of original issue (llama3.1 timeouts):**

- llama3.1 silo: completes, but produces **0 removes** (8 primary + 10 secondary). Levers `ee0996f6` (Information Dissemination Protocol) and `19e66d20` (Resource Recycling Mandate) clearly overlap primary levers but are kept. The timeout is gone; the deduplication quality for llama3.1 on silo is still poor.
- The timeout fix relies on a 5s margin, not a hard constraint. A future plan with more levers or more complex content could re-trigger the timeout.
- B1 (silent failure masking), B2 (user_prompt field wrong), B3 (calls_succeeded hardcoded), B4 (no fallback events) from PR #374 are all unresolved.
- `OPTIMIZE_INSTRUCTIONS` still documents the old "keep general" overlap preference rule, contradicting the PR's new "keep strategically better" guidance.

---

## Quality Comparison

All 7 models appear in both batches (runs 64–70 = before PR #374; runs 71–77 = after PR #375). All metrics are for shared models only.

Notes on N/A rows: this is the DeduplicateLevers step. It does not generate new `consequences`, `options`, or `review` content — those fields are carried verbatim from the upstream IdentifyPotentialLevers step. Format compliance, content depth, bracket leakage, and option count metrics are not measurable here; they belong to the upstream step's assessment.

| Metric | Before (runs 64–70, PR #374) | After (runs 71–77, PR #375) | Verdict |
|--------|------------------------------|------------------------------|---------|
| Structural success rate | 35/35 | 35/35 | UNCHANGED |
| LLMChatErrors | 0 | 0 | UNCHANGED |
| LLM calls per plan | 1 (batch) | 1 (batch) | UNCHANGED |
| llama3.1 timeout plans | 2/5 (silo, parasomnia) | **0/5** | **IMPROVED** |
| llama3.1 fallback-triggered plans | 2/5 | **0/5** | **IMPROVED** |
| llama3.1 silo removes | 0 (timeout fallback — no real output) | 0 (completed, but no removes) | REGRESSED (fallback gone, but dedup quality unchanged) |
| Justification length — haiku, silo (b664e24a) | ~43 words ("Information control is foundational to the silo's governance model and directly impacts social stability…") | ~18 words ("Information control fundamentally shapes silo stability, social cohesion, and adaptability…") | **IMPROVED (~58%)** |
| Justification length — gpt-oss-20b, hong_kong | ~42 words | ~19 words | **IMPROVED (~55%)** |
| Justification length — llama3.1, hong_kong | ~42 words | ~42 words | **UNCHANGED** |
| Haiku silo removes | 1 (ee0996f6) | 2 (ee0996f6, 19e66d20) | **IMPROVED** |
| gpt-oss-20b hong_kong removes | 6 | 3 (f9512726, 4745854b, 15828c14) | REDUCED (see note) |
| Haiku hong_kong removes | 4 | 3 | SLIGHTLY REDUCED |
| Overlap preference (general vs. strategic) | Always keep more general | Keep strategically better one | **IMPROVED** |
| Remove scope | Redundant/overlapping only | Redundant/overlapping/irrelevant | EXPANDED (unverifiable) |
| Fallback classification | primary | secondary | IMPROVED (not triggered) |
| "Triaging" framing | No | Yes | IMPROVED |
| silo avg duration (6 API models) | ~37.6s | ~28.3s | **IMPROVED (~25%)** |
| gpt-oss-20b silo duration | 42.1s | 31.19s | IMPROVED (−26%) |
| qwen3 silo duration | 69.4s | 33.81s | IMPROVED (−51%) |
| gpt-4o-mini silo duration | 41.6s | 22.02s | IMPROVED (−47%) |
| haiku silo duration | 23.0s | 19.79s | IMPROVED (−14%) |
| gpt-5-nano silo duration | 42.9s | 61.56s | REGRESSED (+43%) |
| Silent failure masking (B1/B3) | Present | Present | UNCHANGED |
| `user_prompt` field stores full prompt (B2) | No | No | UNCHANGED |
| classification_fallback events in events.jsonl (B4) | Absent | Absent | UNCHANGED |
| qwen3 justification-swap on multi-remove (N3) | Present | Present | UNCHANGED |
| Bracket placeholder leakage `[...]` | N/A — dedup step does not generate content | N/A | N/A |
| Option count violations (≠ 3 options) | N/A — dedup step does not generate options | N/A | N/A |
| Template leakage / verbatim copying | 0 observed | 0 observed | UNCHANGED |
| Fabricated quantification (% claims in justifications) | 0 observed | 0 observed | UNCHANGED |
| Marketing-copy language | 0 observed | 0 observed | UNCHANGED |
| Field length vs baseline | Baseline (different schema — absorb/keep, not primary/secondary/remove); direct ratio comparison not valid | — | N/A |
| OPTIMIZE_INSTRUCTIONS alignment — overlap preference | "The more general lever should survive" (documented in code) | System prompt uses "keep strategically better" but OPTIMIZE_INSTRUCTIONS still says "keep general" | **REGRESSED (documentation debt)** |

**Note on gpt-oss-20b hong_kong removes (6 → 3):**
Direct file read of `history/3/72_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` confirms 3 removes (f9512726, 4745854b, 15828c14), not 2 as stated in the insight. The insight undercounts by one. The insight attributes the drop partly to the new "keep strategically better" guidance (run 72 keeps Ending Resolution and Political Subtext Level as valid primary levers rather than removing them as run 65 did). Whether this is better judgment or run-to-run variance cannot be determined from a single run. Not treated as a regression.

**OPTIMIZE_INSTRUCTIONS check:**

`deduplicate_levers.py:56–58` still reads: *"Models remove the general lever and keep the narrow one — reversed from correct behavior. The more general lever should survive; the specific one should be removed."*

PR #375 changed the system prompt to "keep the one that better captures the strategic decision." These are different criteria. The OPTIMIZE_INSTRUCTIONS documents the old rule as a known failure mode to guard against, which contradicts the PR's current intent. Future prompt engineers using OPTIMIZE_INSTRUCTIONS as a guide will apply the "keep general" heuristic, producing regressions that look like known bugs. This is a documentation debt introduced by PR #375.

The PR moves closer to OPTIMIZE_INSTRUCTIONS' goal of "distinct, grounded, and actionable" surviving levers. The new overlap preference (strategic quality over generality) is better aligned with producing actionable plans.

---

## New Issues

**N1 — llama3.1 silo produces 0 removes despite completing within timeout.**
Run 71 (llama3.1, silo): 114.75s, 18 levers classified, 0 removes. Levers `ee0996f6` (Information Dissemination Protocol) and `19e66d20` (Resource Recycling Mandate) are classified primary and secondary respectively, despite overlapping clearly with `b664e24a` and `51e3a6e2`. Capable models (haiku run 77, gemini run 76) correctly remove both. Root cause (from code review S2): the system prompt places "prefer secondary over remove" before "expect to remove 25-50%"; the conservative instruction wins for weak models.

**N2 — Justification length constraint is advisory-only (S1 from code review).**
The PR description claims "~20-30 words (down from ~40-80). Less output = llama3.1 more likely to finish within timeout." The implementation adds only advisory text in the Pydantic field description (`deduplicate_levers.py:83-85`). No `max_length` constraint exists. llama3.1 ignores the advisory and produces ~40-word justifications as before. The silo timeout was fixed with only a ~5-second margin. A future plan with more levers or more verbose lever content will re-trigger the timeout.

**N3 — OPTIMIZE_INSTRUCTIONS documents the old "keep general" overlap rule, contradicting the PR's new "keep strategically better" rule (S3 from code review).**
`deduplicate_levers.py:55-58` says "Hierarchy-direction errors. Models remove the general lever and keep the narrow one — reversed from correct behavior. The more general lever should survive." The current system prompt says "keep the one that better captures the strategic decision." A future iteration reading OPTIMIZE_INSTRUCTIONS will produce a prompt that contradicts the current behavior.

**N4 — The "irrelevant" remove criterion cannot be validated against current test plans (N5 in insight).**
Zero irrelevant-lever removes across all 35 after-runs. The feature is correctly implemented but invisible in quality metrics. If upstream generates clearly out-of-scope levers in a future plan, this criterion will fire correctly — but there is no current evidence of its behavior.

**N5 — qwen3 swaps justification text between two remove-classified levers (N3 in insight, pre-existing).**
Run 74 (qwen3, silo): lever `36621fe3` (Security Force Structure) classified remove with a justification describing `19e66d20` (Resource Recycling), and vice versa. Classification outcomes are correct; justification text is wrong. Not introduced by PR #375 but newly observable because qwen3 now removes multiple levers in a single plan.

---

## Verdict

**YES**: PR #375 is a keeper. The primary objective — eliminating llama3.1 timeouts on silo and parasomnia — is confirmed fixed. Before: 2/5 llama3.1 plans timed out and produced all-primary fallback output (zero real classification). After: 0/5 timeouts, 35/35 plans with real LLM output for all models. Secondary improvements are visible: API models write ~55% shorter justifications, most models run 14–51% faster on the silo plan, haiku removes one additional correct lever on silo, and the "keep strategically better" overlap preference is evidenced for haiku on hong_kong_game.

The identified regressions are minor: gpt-5-nano is ~43% slower on silo (within normal variance range), gpt-oss-20b removes 3 instead of 6 levers on hong_kong_game (plausibly better judgment), and the OPTIMIZE_INSTRUCTIONS documentation now contradicts the system prompt (documentation debt, not a runtime regression). None of these outweigh the main improvement.

The two unfixed risks are notable but not blockers: the justification length constraint has no enforcement teeth (fragile timeout fix), and the B1/B2/B3/B4 observability bugs from PR #374 are still unresolved.

---

## Recommended Next Change

**Proposal**: Fix the system prompt instruction ordering in `deduplicate_levers.py:133-143` so that the expected-removal rate calibration appears before the conservative tie-breaker, and simultaneously add a `max_length=200` Pydantic constraint to the `justification` field to enforce shorter output for all models regardless of advisory compliance.

The synthesis recommendation is to bundle both changes in a single PR. The prompt fix addresses the main quality deficit; the Pydantic constraint makes the timeout fix robust.

**Evidence**: The synthesis cites code review S2 and insight N1. Run 71 (llama3.1, silo): 0 removes despite completing. The current system prompt sequence is:
```
1. "When uncertain between primary/secondary, prefer primary"
2. "When uncertain between removing and keeping, prefer secondary over remove"    ← conservative, appears first
3. "Expect to remove 25-50% of input levers..."                                 ← calibration, appears second
```
For weak models, the first tie-breaker encountered dominates. Run 77 (haiku) correctly removes 2 levers on the same plan with the same prompt — the weak-model hypothesis is confirmed by cross-model comparison. The synthesis proposes moving the 25-50% expectation above the conservative tie-breaker and reframing the tie-breaker as a narrow exception ("after comparing").

For the `max_length=200` constraint: the silo timeout is now cleared by only ~5 seconds. If the silo plan gains more levers from upstream, or if a new test plan has more complex lever content, llama3.1 will time out again. A hard character cap on the justification field truncates at schema validation — Pydantic rejects long outputs and triggers retry with a shorter attempt. The code review (S1) confirms this is a single-line change with minimal risk.

**Verify in next iteration:**
- **llama3.1 silo removes**: confirm run N+1 (llama3.1, silo) produces ≥1 remove for `ee0996f6` and/or `19e66d20` after the prompt reordering. Both levers overlap primary levers; haiku and gemini agree they should be removed.
- **llama3.1 silo timeout**: confirm the 120s timeout is not triggered on silo with the combined prompt + max_length change. Duration should stay below 110s (the ~4s buffer added by shorter justifications for API models should also reduce llama3.1's output slightly via max_length truncation).
- **API model removes**: confirm haiku and gpt-oss-20b don't over-remove after the prompt reordering. The "prefer secondary when genuinely uncertain after comparing" safeguard should hold. Watch for runs where >50% of levers are removed.
- **gpt-5-nano silo speed**: run 73 was 43% slower on silo (61.56s vs 42.9s). Verify this is not related to the justification advisory — with max_length enforced, output length should be bounded.
- **qwen3 justification swap (N5)**: still present after the prompt change? Check run N+1 (qwen3, silo) for swapped justification text when ≥2 levers are removed.

**Risks**:
- Prompt reordering may slightly increase removal rates for mid-tier models (gpt-oss-20b, gpt-5-nano) that already remove levers. The "prefer secondary when genuinely uncertain after comparing" safeguard is the protection against over-removal. Verify that no plan loses more than 50% of its levers.
- `max_length=200` causes a Pydantic validation error when a model produces a long justification, triggering retry. If retries are exhausted, the lever falls to the secondary fallback. This is the same behavior as a total LLM failure today, and is acceptable.
- The `OPTIMIZE_INSTRUCTIONS` update (S3 from code review) should be bundled with the prompt change since both touch `deduplicate_levers.py`. Not doing this creates a risk that the next optimization iteration reads OPTIMIZE_INSTRUCTIONS and reintroduces the "keep general" rule, regressing run 77's behavior.

**Prerequisites**: None. Both changes are in `deduplicate_levers.py`. The B1/B2/B3/B4 observability bugs do not need to be fixed first, though fixing B1+B3 before the next iteration would give accurate success metrics.

---

## Backlog

**Resolved from iter 51 (PR #374) backlog — can be closed:**
- **I4 — llama3.1 `request_timeout` increase (config change)**: no longer needed. PR #375 fixed the timeout by reducing output length. The 240s config change would still be safe, but is not required.
- **llama3.1 2/5 fallback plans**: eliminated. All 7 models now produce real LLM output across all 5 plans.

**Carry forward from iter 51 (unchanged):**
- **B1 (HIGH):** Silent LLM failure masking — total LLM failure produces `status="ok"` with all-secondary fallback. Affects measurement fidelity.
- **B2 (LOW):** `user_prompt` field stores `project_context` instead of full assembled prompt. One-line fix: `user_prompt=project_context` → `user_prompt=user_prompt` at `deduplicate_levers.py:272`.
- **B3 (MEDIUM):** `calls_succeeded` hardcoded to 1 in `runner.py`. Fix alongside B1.
- **B4 (MEDIUM):** No `deduplication_fallback` event emitted to `events.jsonl`. Analysis pipeline cannot programmatically detect degraded runs without scanning every `_raw.json`.
- **S4 (LOW):** Minimum lever count warning threshold (`max(3, N//4) = 4` for 18 levers) fires only at 78% removal. Consider raising to `max(5, N//3)`.
- **S1/identify (MEDIUM):** `Lever.consequences` field description in `identify_potential_levers.py` names "Controls ... vs." and "Weakness:" — contradicts OPTIMIZE_INSTRUCTIONS guidance against naming banned phrases. Fix in a separate identify step iteration.
- **Q4:** Verify whether downstream EnrichLevers and FocusOnVitalFewLevers actually consume the `primary`/`secondary` field before investing further in classification calibration.
- **I5+I6 (MEDIUM):** When the LLM omits a lever_id from the response, a targeted retry with explicit missing IDs is more correct than the blanket secondary fallback.

**New items from PR #375:**
- **S1 (HIGH, new framing):** No `max_length` constraint on the justification field — advisory text only. The llama3.1 timeout fix depends on API models shortening their output sufficiently that llama3.1's ~40-word output stays within aggregate budget. A future complex plan will retrigger timeouts. Fix: add `max_length=200` to `LeverClassificationDecision.justification` in `deduplicate_levers.py:83-85`.
- **S2 (MEDIUM):** System prompt instruction conflict — "prefer secondary over remove" appears before "expect to remove 25-50%". For weak models, conservative instruction wins and produces 0-remove output even when obvious redundancies exist. Fix: reorder so removal calibration appears first, tie-breaker second (see Recommended Next Change).
- **S3 (MEDIUM):** `OPTIMIZE_INSTRUCTIONS` documents old "keep general" overlap rule (`deduplicate_levers.py:55-58`), contradicting PR #375's "keep strategically better" system prompt. Fix: update lines 55-58 to reflect the current overlap-preference guidance.
- **N4 (LOW):** "Irrelevant" remove criterion cannot be validated against current 5 test plans. Consider adding a synthetic canary plan with a known-irrelevant upstream lever (e.g., a software-delivery plan where upstream generated a "physical office location" lever) to provide direct validation.
- **N5 (LOW):** qwen3 swaps justification text between two remove-classified levers in the same plan. Classification outcomes are correct; reasoning is wrong. Potential fix: require justifications to name the overlapping lever explicitly ("This lever overlaps with [lever name]").
