# Assessment: PR #479 + minimal review_lever to avoid template lock

## Issue Resolution

**What the PR was supposed to fix:** PR #479's `review_lever` field description contained the structural phrase `"the proposed options collectively do not resolve"`, which caused qwen3-30b to produce a fill-in-the-blank template lock (`"X creates Y risks, leaving Z gaps when/between C"` across 100% of reviews in gta_game) and worsened gpt-oss-20b's template rate. PR #482 stripped the field description to minimal content: `"Critical review of this lever (one sentence, 20–40 words). See system prompt section 4 for examples. Do not use square brackets or placeholder text."` Section 4 preamble was also reduced to `"A one-sentence critical review. Examples:"`.

**Is the issue resolved?** Yes, definitively.

- **qwen3-30b (before, run 90, gta_game):** All 8 sampled reviews follow `"[X] creates [Y] risks, leaving [Z] gaps when/between [condition]."` — e.g., `"Hyper-localization creates resource fragmentation risks, leaving procedural consistency gaps between curated zones and algorithmically generated areas."` (8/8 sampled, confirmed by direct file read)
- **qwen3-30b (after, run 42, gta_game):** Reviews are structurally diverse and domain-specific — `"Focusing on Detroit's grit risks diluting the game's aspirational appeal while saving costs, but may limit cross-market commercial reach."` Zero instances of the `"creates X risks, leaving Y gaps"` pattern across all 101 levers. (confirmed by direct file read)

**Side-effect fixes also confirmed:**

- **haiku `"All three options X, but none address Y"` (~85% before):** After run 45 hong_kong_game shows varied, domain-specific reviews with no structural template (confirmed). e.g., `"A twist structure must rewire audience expectations built across decades of Fincher fandom without abandoning the original's core emotional architecture…"` — no common sentence template across first 10 reviews.
- **gpt-oss-20b `"options do not address/overlook"` pattern:** Absent in after run 40 (confirmed by insight agent via silo plan cross-check).

**Residual symptoms:** None for the targeted template-lock patterns. A new pattern emerged (llama3.1 consequence parroting in later calls — distinct mechanism, covered under New Issues).

---

## Quality Comparison

Models in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4.5.
Before = runs 2/87–2/93 (analysis 40 / post-PR #358). After = runs 5/39–5/45 (analysis 76 / post-PR #482).
Baseline avg: cons=279 chars, opt=452 chars, rev=152 chars.

| Metric | Before (runs 87–93) | After (runs 39–45) | Verdict |
|--------|--------------------|--------------------|---------|
| **Plan-level success** | 35/36 (run 92 gemini missing 1 plan) | 35/35 | IMPROVED |
| **Plan-level timeouts** | 0 | 2 (gpt-oss-20b: sovereign_identity, parasomnia) — complete outputs on disk | NEW (monitor) |
| **LLMChatErrors / ValidationErrors** | 0 | 0 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (<3 options)** | 0 | 0 | UNCHANGED |
| **qwen3-30b template lock** ("X creates Y risks, leaving Z gaps") | Present in 100% of sampled gta_game reviews (run 90) | Absent, 0/101 levers (run 42) | **FIXED** |
| **haiku secondary template lock** ("All three options X, but none address Y") | ~85% rate, hong_kong_game (run 93) | ~0%, hong_kong_game (run 45) | **FIXED** |
| **gpt-oss-20b template lock** ("options do not address/overlook") | Present, multiple reviews (run 88) | Absent (run 40) | **FIXED** |
| **llama3.1 structural template** ("X introduces trade-offs; three options leave unaddressed") | ~100% of reviews (run 87) | Absent in levers 1–7; replaced by consequence restatements in levers 8–15 | CHANGED — mixed (structural lock replaced by shallower failure) |
| **llama3.1 consequence parroting** (review ≈ consequence with "could"→"can") | 0 | Levers 9–15, silo: 7/7 confirmed (>90% word overlap) | **NEW REGRESSION** |
| **haiku fabricated numbers** (% claims / dollar figures) | 21/93 = 22.6% (run 93) | 34/110 = 30.9% (run 45) | **REGRESSED +8.3pp** |
| **Avg review length — all models** | ~197 chars | ~170 chars (closer to baseline 152) | IMPROVED |
| **haiku avg_rev vs baseline** | 321 chars (2.11×) | 276 chars (1.82×) | IMPROVED (still above 2×) |
| **haiku avg_cons vs baseline** | 515 chars (1.85×) | 607 chars (2.18×) | **REGRESSED** (crossed 2× warning threshold) |
| **haiku avg_opt vs baseline** | 968 chars (2.14×) | 890 chars (1.97×) | IMPROVED (just below 2×) |
| **llama3.1 avg_rev vs baseline** | 211 chars (1.39×) | 129 chars (0.85×) | IMPROVED (but driven by parroting, not depth) |
| **gpt-4o-mini / gemini avg fields vs baseline** | Both near 1×–1.3× | Both slightly closer to baseline | IMPROVED |
| **qwen3-30b avg_opt vs baseline** | 264 chars (0.58×) | 253 chars (0.56×) | UNCHANGED (persistent under-length) |
| **Over-generation (>7 levers per call)** | Haiku, qwen3-30b produced >15 per plan | Same; all absorbed by downstream deduplication | UNCHANGED (by design) |
| **llama3.1 sovereign_identity lever count** | Not flagged | 11/15 target — below minimum | NEW (minor) |
| **OPTIMIZE_INSTRUCTIONS coverage** | Template-lock migration + Field-description lock documented | Both entries remain accurate; "Consequence parroting" entry absent | GAP (not added in PR) |

---

## New Issues

1. **llama3.1 consequence parroting in later adaptive-loop calls.** Levers generated in calls 2+ (silo plan run 39, levers 9–15) restate the `consequences` field verbatim with only modal verb substitution (`"could"` → `"can"`). Example: consequence `"Failing to prepare for emergencies could result in catastrophic consequences for the entire population."` / review `"Failing to prepare for emergencies can result in catastrophic consequences for the entire population."` — 7/7 of the later-call silo levers exhibit this pattern. Root cause: the subsequent-call user prompt (`identify_potential_levers.py:300–305`) focuses the model on name novelty with no review-quality guard, and the minimal field description provides insufficient guidance for llama3.1 in calls 2+.

2. **haiku fabricated numbers increased (+8.3pp, 22.6% → 30.9%).** Fabricated percentages and dollar figures appear throughout haiku's consequences and options: `"HK$150–250 million"`, `"25–35 percent of total production budget"`, `"8–12 percent production overhead"`, `"18–22 percent"`, etc. (confirmed in run 45 hong_kong_game). These violate OPTIMIZE_INSTRUCTIONS ("Fabricated numbers") and Section 5 of the system prompt. The PR's change to `review_lever` is not the direct cause — the numbers appear in `consequences`/`options`, not `review`. Suspected cause: the `"positive framing"` instruction carried forward from PR #479.

3. **haiku consequence field widened to 2.18× baseline** (515→607 chars). The `consequences` field description has a soft "Target length: 2–3 sentences" cap that haiku is not honoring. This is the only field ratio crossing the 2× warning threshold after the PR (avg_opt improved to 1.97× from 2.14×).

4. **gpt-oss-20b plan-level timeouts (2 plans at 600s).** Sovereign_identity and parasomnia both timed out in run 40, though both produced complete lever files (18 levers each) on disk. Root cause: B3 in the code review — Python `ThreadPoolExecutor` has no cancellation; the thread continues writing after `TimeoutError` is recorded. This creates a silent inconsistency between `events.jsonl` (error) and filesystem state (complete output). Before run 88 had 0 timeouts; may be model-provider latency variance.

5. **`OPTIMIZE_INSTRUCTIONS` missing "Consequence parroting" entry.** The newly observed llama3.1 later-call pattern (review ≈ consequence restatement) is a distinct failure mode not documented alongside the existing "Template-lock migration" and "Field-description template lock" entries.

6. **Fragile cross-reference in `review_lever` field description.** PR #482 added `"See system prompt section 4 for examples."` to the Pydantic schema. This hardcodes a section number that silently becomes wrong if the system prompt is restructured — the opposite direction from the PR's minimalization goal.

**Latent issues surfaced (pre-existing, now visible):**

- `partial_recovery` event threshold mismatch: `runner.py:131` emits a log warning at `actual_calls < 3`, but `runner.py:578` emits the `events.jsonl` entry at `calls_succeeded < 2`. These thresholds are inconsistent; the comment at 128–130 confirms 2-call success is normal. (Code review B1)
- Global dispatcher contamination for `workers > 1`: `TrackActivity` handlers share the same llama_index singleton, causing cross-plan event cross-pollination. (Code review B2)
- Timed-out threads continue executing and writing output: confirmed by run 40 behavior. (Code review B3)
- `strategic_rationale` is `Optional[str]` with `default=None`, allowing models to silently skip the chain-of-thought field. (Code review S2)
- `options` field accepts > 3 items without a validator upper bound. (Code review S4)

---

## Verdict

**CONDITIONAL**: The PR eliminates three confirmed template locks (qwen3-30b, haiku secondary, gpt-oss-20b), improves review length across 6 of 7 models, and fixes the only missing plan from the before batch. These are genuine quality improvements affecting 100% of generated reviews for three models. However, two regressions require follow-up before full endorsement: (1) llama3.1 produces consequence restatements as reviews in later adaptive-loop calls, replacing a structural template with a shallower failure; (2) haiku's fabricated-number rate increased 8.3pp to 30.9%, violating OPTIMIZE_INSTRUCTIONS and Section 5 prohibitions. Keeping the PR is correct; the conditions are:

- **C1:** Add anti-parroting guidance to the subsequent-call user prompt (`identify_potential_levers.py:300–305`) to address llama3.1 consequence parroting.
- **C2:** Investigate and remove (or neutralize) the PR #479 `"positive framing"` instruction to address haiku's fabricated-number regression.
- **C3:** Add a `"Consequence parroting"` entry to `OPTIMIZE_INSTRUCTIONS` documenting the llama3.1 later-call pattern.

---

## Recommended Next Change

**Proposal:** Add a single prohibition sentence to the subsequent-call user prompt at `identify_potential_levers.py:300–305`. The proposed addition: `"Each review_lever must be a genuine critical assessment — not a restatement of the consequence — in one sentence (20–40 words)."` Optionally bundle with: fixing the `partial_recovery` threshold mismatch (runner.py:131 from `< 3` → `< 2`) and removing the fragile `"See system prompt section 4"` cross-reference (identify_potential_levers.py:129).

**Evidence:** The causal chain is confirmed by two independent agents and direct file inspection. The subsequent-call prompt (`identify_potential_levers.py:300–305`) adds only a name-exclusion list (`"Do NOT reuse any of these already-generated names: [...]"`) before the user prompt, with no review-quality guidance. This focus on name novelty dominates weaker models' attention in calls 2+, causing llama3.1 to produce the minimal-effort strategy of restating the consequence with `"could"` → `"can"` substitution. Direct evidence: run 39 silo, levers 9–15 all exhibit this pattern (7/7, confirmed). Levers 1–7 (call 1) are genuine critical reviews, confirming the problem is call-order specific, not model-general. The code review (S1/I1) and insight (Negative #1) independently identify the same root cause.

**Verify in next iteration:**
- llama3.1, silo plan, levers 8–15: confirm 0/7 consequence restatements after change (was 7/7 in run 39).
- llama3.1, gta_game and sovereign_identity: spot-check later-call levers for parroting (sovereign_identity only produced 11 levers in run 39 — check if this changes).
- haiku (run 45 baseline): verify the added sentence doesn't introduce a new template lock pattern in haiku reviews, since haiku is already clean.
- qwen3-30b and gpt-4o-mini: confirm no change in review quality (neither exhibited parroting before; the change should be neutral).
- gpt-oss-20b: confirm parroting-free; also monitor for whether timeout events recur or were transient.
- Fabricated number rate for haiku: if the "positive framing" investigation runs in parallel, use this iteration to confirm whether removing positive framing reduces haiku's fabricated-number rate from 30.9% toward 22.6%.

**Risks:**
- The reminder sentence could become a structural template if phrased as a positive instruction (e.g., `"A genuine critical assessment identifies..."` could create a new opener lock). Mitigation: use prohibition framing only (`"not a restatement of the consequence"`), which matches the approach validated in OPTIMIZE_INSTRUCTIONS.
- Adding any sentence to the subsequent-call prompt increases token count slightly; negligible for all tested models.
- If llama3.1's parroting is partly caused by its own inherent degradation under the adaptive loop (rather than solely the prompt), the fix may reduce but not eliminate parroting — the validator from code review I2 (word-overlap model_validator) would serve as a structural backstop.

**Prerequisites:** None. This change is independent of the haiku fabricated-numbers investigation and can be deployed first. The `partial_recovery` threshold fix (runner.py:131) and cross-reference removal (identify_potential_levers.py:129) are trivial co-bundleable changes.

---

## Backlog

**Resolved by PR #482 (remove from backlog):**
- qwen3-30b `"X creates Y risks, leaving Z gaps"` template lock — confirmed eliminated.
- haiku `"All three options X, but none address Y"` secondary template lock — confirmed eliminated.
- gpt-oss-20b `"options do not address/overlook"` pattern — confirmed eliminated.
- `LeverCleaned.review` stale `"names the core tension"` description (B1 from analysis 40) — superseded: the field description has now changed further (PR #482), making this entry out of date. Needs a fresh update to match the current minimal wording.

**Add to backlog (new issues from analysis 76):**
- **[HIGH] llama3.1 consequence parroting in later calls:** `identify_potential_levers.py:300–305` — subsequent-call prompt lacks review-quality guardrail. Fix: add anti-parroting sentence (Direction 1 in synthesis).
- **[HIGH] haiku fabricated numbers (+8.3pp, now 30.9%):** Suspected cause: PR #479 "positive framing" instruction carried forward. Fix: run targeted haiku experiment with/without positive framing; if confirmed, remove/neutralize it.
- **[MEDIUM] haiku consequence length 2.18× baseline:** Prose cap ("Target: 2–3 sentences") insufficient for haiku. Fix: investigate alongside fabricated-numbers fix (may share root cause).
- **[MEDIUM] `OPTIMIZE_INSTRUCTIONS` missing "Consequence parroting" entry:** Add to OPTIMIZE_INSTRUCTIONS alongside the anti-parroting prompt change PR.
- **[MEDIUM] `partial_recovery` threshold mismatch:** `runner.py:131` (`< 3`) vs `runner.py:578` (`< 2`) — fix in same PR as Direction 1. Trivial one-liner.
- **[LOW] Fragile cross-reference `"See system prompt section 4"` in Pydantic schema:** `identify_potential_levers.py:129` — remove or generalize. Bundle with Direction 1 PR.
- **[LOW] `LeverCleaned.review` description still stale:** Now references wording inconsistent with PR #482's minimal field description. Update to match.
- **[LOW] gpt-oss-20b timeout monitoring:** Two plan-level timeouts at 600s in run 40. Both plans produced complete output. Monitor in next iteration to determine if transient or structural.
- **[DEFERRED] Global dispatcher contamination (B2):** `runner.py:248–251` — `TrackActivity` handlers not thread-isolated for `workers > 1`. Medium effort to fix (thread-ID filter). Defer until parallel execution is more heavily exercised.
- **[DEFERRED] Timed-out thread continues writing (B3):** `runner.py:553–566` — Python `ThreadPoolExecutor` has no cancellation. Document the behavior; no output is lost, but events/filesystem state can diverge.
- **[DEFERRED] `strategic_rationale` silently skippable:** `Optional[str]` with `default=None` — chain-of-thought field can be omitted without warning. Low priority; no observed quality impact in current runs.
- **[DEFERRED] `options` accepts >3 items silently:** Add upper-bound validator to `check_option_count`. No runs in current analysis showed downstream failures from >3 options.
- **[DEFERRED] qwen3-30b option length 0.56× baseline:** Persistent across before and after. Monitor; not caused by current PR.
