# Synthesis

## Cross-Agent Agreement

Only one insight agent and one code-review agent ran for this analysis (both Claude). The two reports are highly consistent — they cross-map every finding, cite the same files, and reach the same CONDITIONAL verdict. There are no genuine cross-agent disagreements; the observations below are from a single compound analysis.

Areas of full agreement:

- **Haiku fabricated-claims improvement** is real and large: −67% (67 → 22 percentage claims), consequences in-range 19 % → 69 %. Driven by the explicit 30–60-word target in the field description.
- **gpt-oss-20b call-2+ parroting fixed**: exact-copy parrots went from 6 to 0. Anti-parrot sentence in call-2+ user prompt works as intended.
- **llama3.1 call-1 parrot regression** is the most critical new issue: all 7 first-call levers on gta_game have `review` ≡ `consequences` verbatim (sim=1.0), caused by stripping `"one sentence"` and the section-4 cross-reference from the `review_lever` field description.
- **gpt-4o-mini consequence collapse** is confirmed: 74 % → 0 % in-range, caused by `"one downstream implication"` being parsed as a two-clause format constraint rather than a length minimum.
- **gemini-flash options below floor**: avg fell from 23.5 w to 13.9 w; `"one sentence"` in the options field description is the structural brevity signal pushing gemini below the 15-word minimum.
- **Partial-recovery threshold fix** is correct: `runner.py:579` now reads `< 2`; unambiguous improvement.
- **PR verdict: CONDITIONAL** — the haiku and anti-parrot wins are real, but three regressions (llama3.1 parroting, gpt-4o-mini too-short, gemini-flash too-short) require follow-up.

---

## Cross-Agent Disagreements

None substantive. The single insight agent attributes the llama3.1 regression to both B1 (missing call-1 anti-parrot) and B2 (removed structural anchors); the code-review agent preserves that same dual root-cause analysis. There is mild framing difference — insight highlights B1 as a scope gap vs. B2 as a pure regression, while code-review treats B2 as the primary cause and B1 as the incomplete fix — but they propose the same fixes.

Source-code check confirms both claims:

- `identify_potential_levers.py:117–119` — current `review_lever` description is `"Critical review (20–40 words). No square brackets or placeholders."` — `"one sentence"` and the section-4 cross-reference are absent. Confirmed.
- `identify_potential_levers.py:276` — call-1 branch is `prompt_content = user_prompt` with no modification. Anti-parrot instruction is in the else-branch only. Confirmed.
- `runner.py:579` — threshold reads `pr.calls_succeeded < 2`. Fixed. But `runner.py:583` still emits `expected_calls=3`. Confirmed stale value.

---

## Top 5 Directions

### 1. Restore structural anchors to `review_lever` field description (B2)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: Both agents; code_claude B2, insight_claude Negative #1 and C1. Confirmed by source at `identify_potential_levers.py:117–119`. Pre-PR #482 wording in run 5/39 produced 0 exact-copy parrots; post-PR #483 wording in run 5/46 produced 7.
- **Impact**: Eliminates llama3.1 call-1 parrot regression. Affects all 5 plans in the llama3.1 run. The regression is a complete semantic failure on one plan (all 7 levers are verbatim copies). Low capability models depend on field-description structural anchors as a local high-priority override; without them they fall back to copying the nearest available text (consequences).
- **Effort**: Low — single-line change to a field description.
- **Risk**: Minimal. The proposed wording restores exactly the phrases that were working in run 5/39, without re-introducing any template-lock cue. `"one sentence"` is a structural constraint, not a copyable opener. The OPTIMIZE_INSTRUCTIONS warning targets phrases that model verbatim output structure (e.g., "name the core tension"); `"one sentence"` does not fit that pattern.

### 2. Add anti-parrot instruction to call-1 user prompt (B1)
- **Type**: code change
- **Evidence**: Both agents; code_claude B1, insight_claude Negative #1. Confirmed at `identify_potential_levers.py:276` — call-1 branch is `prompt_content = user_prompt` with no guard.
- **Impact**: Provides a runtime prohibition that works alongside the field description anchor (Direction 1). Together they provide defense in depth: the field description guides format at schema parse time; the user-prompt instruction reinforces intent at generation time. If Direction 1 alone fails on edge cases (other complex plans, other weak models), Direction 2 is the fallback. Also makes the anti-parrot behavior symmetric across all calls.
- **Effort**: Low — prepend a single sentence to the call-1 user prompt.
- **Risk**: Low. The prohibition does not supply a structural template for `review_lever`. The code-review agent explicitly assessed this risk as low: "a prohibition about parroting does not provide a copyable structure for review_lever."

### 3. Rephrase `consequences` field description to decouple content from length (S1)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: Both agents; code_claude S1 and I2, insight_claude Negative #2 and C2. gpt-4o-mini went from 74 % in-range (run 5/43) to 0 % in-range (run 5/50). Confirmed at `identify_potential_levers.py:112`.
- **Impact**: Restores gpt-4o-mini consequence quality for all 5 plans in that run. The current phrasing (`"Direct effect and one downstream implication (30–60 words)."`) causes gpt-4o-mini to produce two-clause sentences of 18–22 words — structurally satisfied but informationally thin. Separating content from length (`"The direct effect of pulling this lever and one key downstream implication. Write 30–60 words."`) prevents the word count from being read as a ceiling.
- **Effort**: Low — single-line change.
- **Risk**: Low-medium. Need to verify haiku's consequence length doesn't regress; the tighter 30–60 word guidance in the system prompt (section 2) likely holds haiku in check independently of the field description.

### 4. Remove or rephrase `"one sentence"` from `options` field description (S2)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: Both agents; code_claude S2 and I4, insight_claude Negative #3 and C3. gemini-flash went from 23.5 w avg (71 % in-range) to 13.9 w avg (37 % in-range). Confirmed at `identify_potential_levers.py:115`.
- **Impact**: Restores gemini-flash options to the 15–25 word target for all 5 plans. `"one sentence"` acts as a brevity permission — gemini uses the shortest grammatically complete sentence that fulfills the semantic requirement, falling under the 15-word floor. The length bound `(15–25 words)` alone should be sufficient; alternatively, `"one complete sentence of 15–25 words"` adds emphasis on completeness without granting brevity permission.
- **Effort**: Low — single-line change.
- **Risk**: Low. The system prompt section 6 independently enforces the 15–25 word range. Removing `"one sentence"` may allow multi-sentence options for some models, but no multi-sentence issue was observed in prior runs, and the system-prompt constraint covers it.

### 5. Update `OPTIMIZE_INSTRUCTIONS` with consequence-parroting entry (I5)
- **Type**: code change (documentation constant)
- **Evidence**: Both agents; code_claude I5, insight_claude C4. The `OPTIMIZE_INSTRUCTIONS` block documents known pitfalls for future optimization iterations. Consequence parroting (review ≡ consequences) is confirmed as a recurring, model-specific failure with a known fix. It has no entry yet.
- **Impact**: Prevents future PRs from re-introducing the same regression. The parroting pattern was independently rediscovered in analysis 76 and 77. With a documented entry, the next optimizer has context to maintain the anti-parrot instruction in both call-1 and call-2+, and to preserve the structural anchors in the `review_lever` field description.
- **Effort**: Low — add ~6–8 lines to the constant in `identify_potential_levers.py:27–93`.
- **Risk**: None at runtime — this constant is read by humans and optimization scripts, not sent to the LLM.

---

## Recommendation

**Do Direction 1 first: restore structural anchors to the `review_lever` field description.**

**File:** `identify_potential_levers.py:117–119`

**Current state:**
```python
review_lever: str = Field(
    description="Critical review (20–40 words). No square brackets or placeholders."
)
```

**Proposed fix:**
```python
review_lever: str = Field(
    description="Critical review in one sentence (20–40 words). See system prompt section 4 for examples. No square brackets or placeholders."
)
```

**Why first:** This is the minimum change that eliminates the most severe confirmed regression: 7/7 first-call levers for llama3.1 on gta_game are verbatim copies of `consequences` (sim=1.0). The pre-PR #483 wording is known to work (run 5/39: 0 exact parrots). The restoration is a 2-word addition (`"in one sentence"`) and the section-4 pointer, totalling 10 added characters of real signal. It is a pure undo of the part of PR #483 that backfired for llama3.1, without reverting the improvements that helped haiku.

**Why not Direction 2 first:** B1 (adding anti-parrot to call-1) is also needed, but it is a defense-in-depth measure. The field description (Direction 1) is the proximate cause of the regression — restoring it brings the call-1 path back to the state that worked. B1 should ship in the same PR or the immediately following one.

**Suggested PR scope (small, targeted):**

1. `identify_potential_levers.py:118` — restore `"one sentence"` and section-4 pointer to `review_lever` field description.
2. `identify_potential_levers.py:276` — prepend anti-parrot sentence to call-1 user prompt (bundle with #1 since they address the same failure).
3. `identify_potential_levers.py:112` — rephrase `consequences` description to decouple content from length (fixes gpt-4o-mini).

Items 4 (options `"one sentence"` removal) and 5 (OPTIMIZE_INSTRUCTIONS update) can follow in a subsequent PR — they are lower urgency since gemini-flash options at 37 % in-range is a degradation but not a zero-output failure.

---

## Deferred Items

**Direction 4 (options field description for gemini-flash):** Low urgency. Options at 13.9 w avg are below the 15-word floor but semantically usable. Fix: replace `"Each is one sentence (15–25 words)"` with `"Each option is 15–25 words — a complete, concrete strategic approach."` Defer to a subsequent PR if Directions 1–3 are bundled.

**Direction 5 (OPTIMIZE_INSTRUCTIONS update):** No runtime risk, no urgency. Can be added at the end of any PR that touches `identify_potential_levers.py`. Draft entry:

```
- Consequence parroting. Weaker models (llama3.1, gpt-oss-20b) copy the
  consequences field verbatim into review_lever, especially in call-1.
  The anti-parrot instruction must appear in both the call-1 and call-2+
  user prompts. The review_lever field description must retain "one sentence"
  as a structural anchor; without it, llama3.1 on complex plans reproduces
  consequences exactly. The section-4 cross-reference ("See system prompt
  section 4 for examples.") is also load-bearing for very small models.
```

**S3 — stale `expected_calls=3` in partial_recovery event (`runner.py:583`):** Low operational impact (the event fires only for genuine partial recoveries, which are rare). Should be fixed to match the corrected threshold semantics — either update to `expected_calls=2` or make it dynamic — but it does not affect LLM output quality.

**S4 — no warning for `options` count > 3:** Add a log warning in `check_option_count` for over-generation. Not urgent; downstream deduplicate handles extras and no over-generation issues were observed.

**qwen3-30b fabricated claims regression (+10):** The increase from 6 to 16 pct claims is likely stochastic — the PR did not change anything that would specifically increase qwen3-30b's fabrication rate. Monitor across the next 2 iterations before treating as a confirmed regression. If it persists, add qwen-specific guidance to the anti-fabrication section of the system prompt.

**gpt-5-nano timeouts (2 new, sovereign_identity + parasomnia):** Plan-level provider latency, not prompt-induced. Sovereign_identity appears in both gpt-oss-20b and gpt-5-nano timeouts, suggesting this plan has high token density. Monitor; no prompt change will fix provider latency ceilings.
