# Insight Claude

## Scope

Analyzing runs `5/39–5/45` (after PR #482) against `2/87–2/93` (before, analysis 40 / PR #358)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #482 "PR #479 + minimal review_lever to avoid template lock"

**Changes made by PR #482:**
- `review_lever` Pydantic field description stripped to: `"Critical review of this lever (one sentence, 20–40 words). See system prompt section 4 for examples. Do not use square brackets or placeholder text."` — removes all structural phrases.
- Section 4 preamble in system prompt changed to: `"A one-sentence critical review. Examples:"` — no structural cue.
- Three existing examples (agricultural/clinical/insurance) unchanged and still teach the style.
- From PR #479 (carried over unchanged): verbatim numbers on consequences+options, positive framing, consistent 2–3 sentence targets, section 5 prohibition.

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/87 | 5/39 | ollama-llama3.1 |
| 2/88 | 5/40 | openrouter-openai-gpt-oss-20b |
| 2/89 | 5/41 | openai-gpt-5-nano |
| 2/90 | 5/42 | openrouter-qwen3-30b-a3b |
| 2/91 | 5/43 | openrouter-openai-gpt-4o-mini |
| 2/92 | 5/44 | openrouter-gemini-2.0-flash-001 |
| 2/93 | 5/45 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **qwen3-30b template lock ("X creates Y risks, leaving Z gaps") eliminated.** Before (run 90), the gta_game
   plan shows every review following the pattern `"[X] creates [Y] risks, leaving [Z] gaps when/between
   [condition]."`:
   - `"Hyper-localization creates resource fragmentation risks, leaving procedural consistency gaps between curated zones and algorithmically generated areas."`
   - `"Single-partner reliance creates dependency risks, leaving innovation flexibility gaps when partner priorities conflict with creative vision."`
   - `"Modular prioritization creates integration risks, leaving narrative coherence gaps between independently developed systems."`
   All 8 sampled reviews follow this exact structure.

   After (run 42), the same plan (gta_game) shows varied, domain-specific reviews:
   - `"Focusing on Detroit's grit risks diluting the game's aspirational appeal while saving costs, but may limit cross-market commercial reach."`
   - `"Government grants offer stability but may force compromises on controversial narrative elements central to the franchise's identity."`
   - `"Excessive focus on graphical fidelity may divert resources from core gameplay mechanics that define the series' competitive edge."`
   Zero instances of the "creates X risks, leaving Y gaps" pattern across all 101 levers in run 42.
   Evidence: `history/2/90_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`,
   `history/5/42_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

2. **Haiku "All three options X, but none address Y" secondary lock eliminated.** Analysis 40 found this
   pattern at ~85% frequency in haiku run 93 (hong_kong_game). After (run 45), haiku hong_kong_game reviews
   are structurally diverse:
   - `"A twist structure must rewire audience expectations built across decades of Fincher fandom without abandoning the original's core emotional architecture, or the remake collapses into either derivative repetition or unmoored deconstruction..."`
   - `"Director choice directly trades off creative authenticity against commercial prestige and cost efficiency; the selection determines whether the film feels inhabited or touristic..."`
   - `"Mainland exclusion simplifies creative decision-making and protects narrative coherence, but accepting box office uncertainty in the world's largest theatrical market requires either aggressive P&A scaling..."`
   None of the first 10 reviews in run 45 hong_kong_game follow the "all three options / none address" structure.
   Evidence: `history/5/45_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

3. **gpt-oss-20b "options do not address/overlook" pattern reduced.** Before (run 88), silo plan reviews
   followed: `"X speeds/enables Y but risks Z; options do not address how to reconcile A with B"` or
   `"X guarantees Y but may be slow; options overlook how to handle Z"`. After (run 40), silo reviews show
   independent critical observations without the "options do not/overlook" template:
   - `"Relying on local suppliers cuts transport emissions, but the higher per‑unit cost and limited resource diversity could stall progress if regional supply chains falter during peak construction."`
   - `"Recruiting a high‑skill core team raises quality but inflates wages; the slower hiring pace may delay critical construction phases, undermining the tight schedule."`
   Evidence: `history/2/88_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
   `history/5/40_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

4. **Review lengths moved closer to baseline for most models.** Across 6 of 7 models, average review
   length decreased (haiku: 321→276, llama3.1: 211→129, gpt-5-nano: 199→183, gemini: 183→159,
   gpt-4o-mini: 159→139, qwen3-30b: 149→133). The stripped field description ("Critical review…, 20–40
   words") without structural phrases appears to reduce verbose formula-filling.

5. **Perfect plan-level success across all 5 plans, all 7 after runs.** All 35 plans in the after runs
   produced lever files. One plan was missing in the before runs (run 92/gemini,
   `history/2/92_identify_potential_levers/outputs.jsonl`). After success rate: 35/35 = 100%.

6. **No LLMChatErrors or ValidationErrors in after runs.** The `events.jsonl` files for runs 39–45
   contain no `LLMChatError` or `ValidationError` entries. Validator constraints (`min_length=5` on
   levers, `options >= 3`, `review_lever >= 10 chars`) are all satisfied.
   Evidence: `analysis/76_identify_potential_levers/events.jsonl`, `history/5/39–45_identify_potential_levers/events.jsonl`.

7. **OPTIMIZE_INSTRUCTIONS is current and accurate.** The source file's `OPTIMIZE_INSTRUCTIONS` block
   (lines 27–93) now includes both "Template-lock migration" and "Field-description template lock" entries
   that directly predict the problem this PR fixes. The "Verbosity amplification" entry also applies to
   the haiku findings.
   Evidence: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` lines 27–93.

---

## Negative Things

1. **llama3.1 review regression in later LLM calls — consequence parroting.** In run 39, the silo plan
   shows two distinct quality tiers within the same output file. First-call levers (1–7) have genuine
   critical reviews:
   - `"While it may simplify resource management, relying solely on private investments risks compromising project autonomy and values."`
   Second/third-call levers (8–16) exhibit consequence parroting:
   - `"Failing to prepare for emergencies can result in catastrophic consequences for the entire population."` (consequence: `"Failing to prepare for emergencies could result in catastrophic consequences for the entire population."`)
   - `"Failing to preserve historical knowledge can result in lost skills and forgotten innovations."` (consequence: `"Failing to preserve historical knowledge could result in lost skills and forgotten innovations."`)
   - `"Inadequate communication can lead to misunderstandings, decreased morale, and increased conflict within the silo."` (identical to consequence but with "can" instead of "could")
   The pattern: later levers restate the consequence with only "could" → "can" substitution. The stripped
   field description provides too little guidance for llama3.1 to generate genuine critical reviews in
   later calls, while the initial call still benefits from the full prompt context.
   Evidence: `history/5/39_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

   Note: The BEFORE run 87 (llama3.1) had its own template lock: `"X introduces trade-offs between Y
   and Z; the three options leave unaddressed [gap]"` — structural but at least identified a gap. The
   after run's consequence restatements are arguably worse in analytical depth.

2. **haiku-4.5 fabricated numbers increased (23% → 31%).** In run 93 (before), 21/93 = 22.6% of levers
   contained fabricated percentage claims or dollar figures. In run 45 (after), 34/110 = 30.9%. Sample
   from after run 45 hong_kong_game:
   - `"lower inventory costs"` → `"reducing inventory costs by 20–30 percent"`
   - Consequences reference `"HK$150–250 million"`, `"HK$80–120 million"`, `"25–35 percent of total production budget"`, `"18–22 percent"`, `"8–12 percent production overhead"` throughout the gta_game and hong_kong_game plans.
   These numbers have no basis in the project context and violate OPTIMIZE_INSTRUCTIONS ("Fabricated numbers")
   and Section 5 of the system prompt ("NO calculated, derived, or estimated figures"). This regression is
   NOT caused by the review_lever field description change — the fabricated numbers are in `consequences`
   and `options`, not in `review`. It may be related to the PR #479 `positive framing` change carried
   forward, or haiku's inherent tendency when given complex multi-choice prompts.
   Evidence: `history/5/45_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`,
   `history/5/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

3. **haiku-4.5 consequence field still 2.2× baseline length.** Baseline avg_cons = 279 chars; haiku after
   avg_cons = 607 chars (2.18×). The threshold of 2× is a warning level per AGENTS.md conventions. haiku
   consequences have expanded (515→607 chars from before to after — a 18% increase), while options
   slightly contracted (968→890). This widening on consequences is a mild negative trend.
   Evidence: baseline averages computed from `baseline/train/*/002-10-potential_levers.json`.

4. **gpt-oss-20b had 2 plan-level timeout events.** Run 40 events.jsonl shows:
   ```json
   {"event": "run_single_plan_error", "plan_name": "20260308_sovereign_identity", "error": "plan timeout after 600s"}
   {"event": "run_single_plan_error", "plan_name": "20260311_parasomnia_research_unit", "error": "plan timeout after 600s"}
   ```
   However, both plans produced complete lever files with 18 levers each (sovereign_identity: 18, parasomnia: 18).
   This suggests the timeout was encountered DURING the adaptive loop (after sufficient levers were already
   saved) but the partial output was preserved. This may be a latency regression specific to gpt-oss-20b
   with this prompt version, or an infrastructure issue. The before run 88 had no timeout events.
   Evidence: `history/5/40_identify_potential_levers/events.jsonl`.

5. **qwen3-30b options still below baseline length (0.56x).** Options avg_opt for qwen3-30b: after=253,
   before=264, baseline=452. Both before and after are ~56-58% of baseline length. The options are short
   single-phrase approaches rather than full sentences. This is a persistent limitation across iterations
   and is not caused by PR #482.

---

## Comparison

| Metric | Before (runs 87–93) | After (runs 39–45) | Change |
|--------|--------------------|--------------------|--------|
| qwen3-30b "X creates Y risks, leaving Z gaps" (gta_game) | Present, all reviews | Absent | **FIXED** |
| haiku "All three options / none address" (hong_kong_game) | ~85% | ~0% | **FIXED** |
| gpt-oss-20b "options do not address/overlook" (silo) | Present, multiple reviews | Absent | **FIXED** |
| llama3.1 "X introduces trade-offs; three options leave unaddressed" | Present | Absent, replaced with consequence restatements | CHANGED (mixed) |
| Plan success rate | 35/36 (run 92 missing 1) | 35/35 | **+1 plan** |
| LLMChatErrors | 0 | 0 | — |
| Plan-level timeouts | 0 | 2 (run 40 gpt-oss-20b) | NEW |
| haiku avg_rev (chars) | 321 | 276 | **-45 (closer to baseline)** |
| haiku avg_cons (chars) | 515 | 607 | -92 (further from baseline) |
| haiku fabricated numbers | 21/93 = 22.6% | 34/110 = 30.9% | **REGRESSION +8.3pp** |
| Avg review length — all models | ~197 chars | ~170 chars | -27 chars (shorter, closer to baseline=152) |

---

## Quantitative Metrics

### Field Lengths vs Baseline

Baseline averages (from `baseline/train/` across 5 plans × 15 levers = 75 levers):
- avg_cons = 279 chars, avg_opt = 452 chars, avg_rev = 152 chars

| Model | Run | avg_cons | avg_opt | avg_rev | cons/baseline | opt/baseline | rev/baseline |
|-------|-----|----------|---------|---------|--------------|-------------|-------------|
| llama3.1 | 87 (before) | 163 | 301 | 211 | 0.58× | 0.67× | 1.39× |
| llama3.1 | 39 (after) | 193 | 299 | 129 | 0.69× | 0.66× | **0.85×** |
| gpt-oss-20b | 88 (before) | 283 | 420 | 170 | 1.01× | 0.93× | 1.12× |
| gpt-oss-20b | 40 (after) | 239 | 399 | 169 | 0.86× | 0.88× | 1.11× |
| gpt-5-nano | 89 (before) | 259 | 406 | 199 | 0.93× | 0.90× | 1.31× |
| gpt-5-nano | 41 (after) | 248 | 402 | 183 | 0.89× | 0.89× | 1.20× |
| qwen3-30b | 90 (before) | 239 | 264 | 149 | 0.86× | 0.58× | 0.98× |
| qwen3-30b | 42 (after) | 239 | 253 | 133 | 0.86× | 0.56× | 0.87× |
| gpt-4o-mini | 91 (before) | 248 | 434 | 159 | 0.89× | 0.96× | 1.05× |
| gpt-4o-mini | 43 (after) | 247 | 434 | 139 | 0.88× | 0.96× | 0.91× |
| gemini-2.0-flash | 92 (before) | 362 | 564 | 183 | 1.30× | 1.25× | 1.20× |
| gemini-2.0-flash | 44 (after) | 331 | 533 | 159 | 1.19× | 1.18× | 1.05× |
| **haiku-4.5** | 93 (before) | 515 | 968 | 321 | 1.85× | **2.14×** | **2.11×** |
| **haiku-4.5** | 45 (after) | **607** | 890 | 276 | **2.18×** | 1.97× | 1.82× |

Threshold: ≥2× is a warning sign per AGENTS.md. haiku crosses the threshold on all three fields after
the PR (cons: 2.18×, opt: 1.97×, rev: 1.82×). Haiku's option length improved but consequence length
worsened.

### Lever Counts Per Plan

| Run | Model | silo | gta_game | sovereign | hk_game | parasomnia | Total |
|-----|-------|------|----------|-----------|---------|------------|-------|
| 39 | llama3.1 | 15 | 18 | 11 | 23 | 17 | 84 |
| 40 | gpt-oss-20b | 18 | 18 | 18 | 18 | 18 | 90 |
| 41 | gpt-5-nano | 18 | 18 | 18 | 19 | 20 | 93 |
| 42 | qwen3-30b | 21 | 20 | 19 | 21 | 20 | 101 |
| 43 | gpt-4o-mini | 17 | 19 | 18 | 18 | 18 | 90 |
| 44 | gemini-2.0-flash | 18 | 18 | 18 | 18 | 18 | 90 |
| 45 | haiku-4.5 | 21 | 21 | 21 | 23 | 24 | 110 |

Min target is min_levers=15. llama3.1 sovereign_identity produced only 11 levers (below target), all others
above minimum. All plans produced lever files.

### Template-Lock and Content Quality

| Model | Before template pattern | After pattern | Change |
|-------|------------------------|---------------|--------|
| llama3.1 | "X introduces trade-offs between Y and Z; the three options leave unaddressed [gap]" (100%) | Short consequence restatements in later calls | REPLACED (not eliminated) |
| gpt-oss-20b | "X speeds Y but risks Z; options do not address how to…" | Varied substantive reviews | FIXED |
| qwen3-30b | "X creates Y risks, leaving Z gaps when/between C" (gta_game) | Diverse plan-specific reviews | FIXED |
| gpt-4o-mini | No template detected | No template detected | Unchanged |
| gemini-2.0-flash | No template detected | No template detected | Unchanged |
| haiku-4.5 | "All three options X, but none address Y" (~85% hong_kong_game) | Diverse, no pattern detected | FIXED |
| gpt-5-nano | No strong template | No template detected | Unchanged |

### Fabricated Numbers

| Model | Before run | After run | Before (count/total) | After (count/total) | Delta |
|-------|-----------|----------|---------------------|---------------------|-------|
| llama3.1 | 87 | 39 | 0/82 | 0/84 | 0 |
| gpt-oss-20b | 88 | 40 | 1/91 | 4/90 | +3 |
| gpt-5-nano | 89 | 41 | 1/91 | 0/93 | -1 |
| qwen3-30b | 90 | 42 | 3/99 | 6/101 | +3 |
| gpt-4o-mini | 91 | 43 | 0/86 | 0/90 | 0 |
| gemini | 92 | 44 | 0/91 | 0/90 | 0 |
| **haiku-4.5** | 93 | 45 | **21/93 (22.6%)** | **34/110 (30.9%)** | **+8.3pp** |

Fabricated numbers detection method: regex match for `\d+%`, `\d+ percent`, `$\d+`, `\d+x` in
consequences + options + review combined text.

---

## Evidence Notes

- **Before qwen3-30b template lock confirmed**: `history/2/90_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
  reviews 1–8 all follow `"[X] creates [Y] risks, leaving [Z] gaps when/between [condition]."` pattern.
  Review 8: `"Advanced AI creates debugging bottlenecks, leaving procedural methods as the only scalable solution for non-essential characters"`.

- **After qwen3-30b template lock eliminated**: `history/5/42_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
  shows 20 structurally distinct reviews across the gta_game plan.

- **After haiku "all three options" lock eliminated**: `history/5/45_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  first 10 reviews use no common sentence template; each opens with a domain-specific mechanism.

- **llama3.1 consequence parroting confirmed**: `history/5/39_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  lever "Emergency Preparedness": consequence "Failing to prepare for emergencies could result in catastrophic
  consequences for the entire population." / review "Failing to prepare for emergencies can result in
  catastrophic consequences for the entire population." — 90%+ word overlap.

- **Before llama3.1 template confirmed**: `history/2/87_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  reviews 1–5 all follow `"X introduces trade-offs between Y and Z; the three options leave unaddressed [gap]."`.

- **haiku-4.5 fabricated numbers in after run**: `history/5/45_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  options for lever "Director Selection Lens" contain `"lower logistics overhead by an estimated 20–30 percent"`,
  `"inflate above-the-line costs by an estimated 15–25 percent"`. Lever "Location Logistics": consequences
  reference `"2–4 days of logistics setup"` and options reference `"8–12 percent production overhead"` and
  `"18–22 percent"` increases. None of these figures appear in the project context.

- **gpt-oss-20b timeouts**: `history/5/40_identify_potential_levers/events.jsonl` events `run_single_plan_error`
  at 600s for sovereign_identity and parasomnia. Both plans still have `002-10-potential_levers.json` with 18
  levers — timeout occurred after lever generation was complete.

- **System prompt confirmed (PR #482)**: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
  lines 126–132 show `review_lever` field description; lines 244–255 show Section 4 preamble "A one-sentence
  critical review. Examples:".

---

## PR Impact

**What the PR was supposed to fix:** PR #479's structural phrase `"the proposed options collectively do not resolve"`
in the `review_lever` field description caused qwen3-30b to lock into a template (0→7/20 template-lock
rate) and worsened gpt-oss-20b (10→15/17 template locks). PR #482 strips the field description to a
minimal content-only description with no structural phrase, while keeping the three training examples.

**Before vs after comparison table:**

| Metric | Before (runs 87–93) | After (runs 39–45) | Change |
|--------|--------------------|--------------------|--------|
| qwen3-30b structural template lock (gta_game) | Present in all sampled reviews | Absent from all 101 levers | **FIXED** |
| haiku "all three options / none address" (hong_kong_game) | ~85% rate | ~0% rate | **FIXED** |
| gpt-oss-20b "options do not address" (silo) | Present | Absent | **FIXED** |
| llama3.1 structural template (silo) | "X introduces trade-offs; three options leave unaddressed" | Consequence restatements in later calls | CHANGED (shallow) |
| Plan-level success | 35/36 (1 miss in run 92) | 35/35 | **+1** |
| LLMChatErrors | 0 | 0 | — |
| Plan-level timeouts | 0 | 2 (gpt-oss-20b) | NEW |
| Avg review length (all models, chars) | ~197 | ~170 | **-27 (closer to baseline 152)** |
| haiku fabricated numbers | 22.6% | 30.9% | **-8.3pp REGRESSION** |
| haiku avg_cons vs baseline | 1.85× | 2.18× | WORSE |
| gemini avg_cons vs baseline | 1.30× | 1.19× | BETTER |
| qwen3-30b review quality | Structural template | Substantive, diverse | **IMPROVED** |
| haiku review quality | "All three options…" template | Substantive, diverse | **IMPROVED** |

**Did the PR fix the targeted issue?**

Yes. The primary stated goal — preventing qwen3-30b template lock — is confirmed. The before run 90
(qwen3-30b) shows the `"X creates Y risks, leaving Z gaps"` template throughout gta_game. The after run 42
shows zero instances of this or any structural template across all 101 levers.

Additionally, the PR fixed haiku's secondary template lock (`"All three options X, but none address Y"`,
~85% in hong_kong_game before) and gpt-oss-20b's "options do not address" pattern. These were residual
effects of PR #358's field description phrase `"state the specific gap the three options leave unaddressed"`.
PR #482 removes that phrase entirely, breaking all three derivative template patterns simultaneously.

**Regressions introduced:**

1. **haiku fabricated numbers (+8.3pp)**: haiku-4.5 produces more fabricated percentages and dollar figures
   after the PR (30.9% vs 22.6%). These appear in consequences and options, not reviews. The causal path
   is unclear — the PR changed the review_lever field description, not the consequences or options fields.
   This may be related to the PR #479 "positive framing" instruction carried forward, or a run-to-run
   variance. Haiku's consequence field length also increased (515→607 chars, 2.18× baseline), which
   correlates with more numeric padding.

2. **llama3.1 review shallowing**: Before (run 87), llama3.1 reviews used a structural template ("X
   introduces trade-offs; three options leave unaddressed [gap]"). After (run 39), later-call levers show
   consequence parroting — near-verbatim restatements of the consequence with "could" → "can" substitution.
   The new minimal field description ("Critical review of this lever (one sentence, 20–40 words)") apparently
   does not provide enough guidance for llama3.1 to generate genuine critical assessments in subsequent
   LLM calls. This is a quality regression for llama3.1, though the before template was also formulaic.

3. **gpt-oss-20b timeouts**: Two plan-level timeouts at 600s for run 40 (gpt-oss-20b). Both plans still
   produced complete output. Likely a latency issue with the model provider rather than a prompt regression,
   but warrants monitoring.

**Verdict: CONDITIONAL**

The PR delivers its stated goal — qwen3-30b template lock is eliminated, haiku's secondary lock is
eliminated, and gpt-oss-20b's template pattern is reduced. These are substantial improvements for content
quality. However, haiku-4.5's fabricated number rate increased (+8.3pp) and haiku consequence length
widened further above baseline (2.18×). llama3.1 shows shallow consequence-restatement reviews in later
calls — a quality regression compared to the structured (if formulaic) reviews from the before run.

The PR should be kept, but the following items need follow-up in the next iteration:

1. Investigate and fix haiku-4.5 fabricated number regression (likely tied to PR #479's positive framing).
2. Provide stronger review guidance for llama3.1's later LLM calls (the minimal description is insufficient).
3. Monitor gpt-oss-20b timeout behavior.

---

## Questions For Later Synthesis

1. **haiku fabricated number causal path**: Is the +8.3pp fabrication increase in haiku caused by (a) the
   PR #479 "positive framing" instruction carried forward, (b) haiku's inherent tendency when generating
   many levers, or (c) interaction between the consequence 2–3 sentence target and haiku's style? If (a),
   removing or weakening the positive framing instruction should reduce fabricated numbers. If (b), a
   post-processor that flags and removes numeric claims could help.

2. **llama3.1 later-call review quality**: Why do first-call llama3.1 levers have genuine critical reviews
   while later-call levers have consequence restatements? The adaptive loop adds context about already-generated
   lever names but does not repeat the full field description guidance. Does adding explicit review guidance
   to the subsequent-call prompt fix the degradation, or would it cause its own template issue?

3. **qwen3-30b option length gap**: qwen3-30b options remain at 0.56× baseline (253 chars vs 452). Before
   and after are similar (264 vs 253). Is this a model-level constraint (qwen3-30b produces short options
   regardless of prompting) or a prompt gap? The options field description says "at least 15 words with an
   action verb" — is this being honored?

4. **gpt-oss-20b timeout root cause**: Is the 600s timeout for sovereign_identity and parasomnia in run 40
   due to (a) API rate limiting, (b) extended adaptive loop calls because the initial response was slow,
   or (c) model behavior specific to those two plans? The before run 88 had zero timeouts with the same plans.

5. **Template monitoring in later calls**: The consequence-parroting pattern in llama3.1 appears in levers
   generated by the second or third LLM call. Should the analysis pipeline separately count template-lock
   rates per call index? This would help detect call-order-specific degradation more reliably.

---

## Reflect

PR #482 takes a clean, minimalist approach: if structural phrases in field descriptions cause template
lock, remove all structural phrases and let examples do the work. The result confirms this theory for
qwen3-30b and gpt-oss-20b: removing `"the three options leave unaddressed"` from the field description
eliminates the "leaves Y gaps" and "options do not address" patterns simultaneously.

The haiku improvement is an unexpected bonus: the before secondary lock (`"All three options… but none
address"`) was itself a derivative of the removed phrase. Eliminating the source phrase in the field
description cascaded to fix all three models' template patterns.

The open concern is llama3.1's review degradation in later calls. The minimal field description
(`"Critical review of this lever (one sentence, 20–40 words)."`) appears insufficient for llama3.1
when the adaptive loop generates subsequent batches — it produces filler (consequence restatement)
rather than analysis. The before run's structural template ("X introduces trade-offs; three options
leave unaddressed Y") was formulaic but at least forced a gap-identification step. The replacement
is shallower.

The haiku fabricated-numbers regression deserves attention. The OPTIMIZE_INSTRUCTIONS "Fabricated numbers"
rule and the system prompt Section 5 prohibition are both in place, but haiku is generating more
fabricated numbers after the PR. This suggests the prohibition text is insufficient for haiku and
a structural fix (e.g., removing example numbers, or adding a validator that rejects numeric patterns
not present in the context) may be needed.

---

## Potential Code Changes

**C1 (Monitor template lock per call index):** Add a per-call-index metric to post-run analysis.
The adaptive loop calls are tracked in `outputs.jsonl` — extract which call each lever came from
and compute template-lock rate per call. This would catch llama3.1's second/third-call degradation
automatically. No change to production code; analysis tooling only.

**C2 (Subsequent-call prompt reinforcement):** The subsequent-call prompt in `identify_potential_levers.py`
(after line 296) could include a brief review guidance reminder: `"Each review_lever must be a genuine
critical assessment — not a restatement of the consequence — in one sentence (20–40 words)."` This
targets llama3.1's later-call degradation without affecting the first call or the field description.
Risk: minor — could re-introduce template patterns if the wording itself becomes a template. Test
in isolation.

**C3 (Fabricated number validator):** Add a `field_validator` on `consequences` (and optionally
`options`) that warns or rejects levers with percentage claims or dollar figures not present in the
user prompt. This would enforce the existing prohibition more structurally. Risk: false positives
for context-provided numbers. Implementation: maintain a numeric whitelist from the user prompt.

---

## Hypotheses

**H1 (llama3.1 later-call guidance):** Add a brief note to the subsequent-call prompt that review_lever
must not restate the consequence. Predicted effect: reduces consequence parroting in llama3.1's second
and third LLM calls. Risk: may create a new structural cue. Test only with llama3.1 to isolate the effect.
Evidence: `history/5/39_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
levers 8–15 (consequence restatements from later calls).

**H2 (haiku fabricated numbers — remove positive framing):** The "positive framing" instruction carried
from PR #479 may be causing haiku to construct optimistic numeric scenarios. Remove or neutralize it.
Predicted effect: reduces haiku fabricated numbers from ~31% toward ~22%. Evidence: haiku fabricated
number rate rose from 22.6% to 30.9% across the PR #479→#482 transition.

**H3 (haiku consequence length — explicit cap):** haiku avg_cons at 2.18× baseline. Adding an explicit
consequence length cap to the system prompt (`"Keep consequences to 2–3 sentences"`) may help. The
current prompt already says "Target length: 2–3 sentences" in the field description — haiku may not
be honoring it. A more prominent instruction in the main numbered section may help.
Evidence: haiku avg_cons = 607 chars (2.18× baseline 279).

**H4 (qwen3-30b options):** The options field description says "at least 15 words with an action verb."
qwen3-30b options avg 253 chars (0.56× baseline). A minimum word count check in the validator
(`check_option_count` already rejects <3 options but does not check length) would surface under-length
options. Evidence: `history/5/42_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
— options are present and 3 per lever but shorter than baseline.

---

## Summary

PR #482 achieves its primary goal: qwen3-30b template lock (`"X creates Y risks, leaving Z gaps"`) is
eliminated across all 5 training plans. As a side effect, haiku's secondary lock (`"All three options X,
but none address Y"`, ~85% rate from the prior PR) and gpt-oss-20b's `"options do not address"` pattern
are also eliminated. This is a meaningful improvement in review field diversity for three models.

Review lengths decreased across 6 of 7 models (avg -27 chars), moving closer to the baseline target of
152 chars. The minimal field description succeeds at preventing template-driven verbosity.

Two concerns require follow-up: (1) haiku-4.5 fabricated numbers increased 8.3pp (22.6%→30.9%) and
consequence length increased to 2.18× baseline — likely driven by the PR #479 "positive framing"
instruction carried forward, not the review_lever change itself; (2) llama3.1 produces consequence
restatements in later adaptive-loop calls, replacing a structural template with shallower filler.

**PR verdict: CONDITIONAL.** Core improvement confirmed; two regressions (haiku fabricated numbers,
llama3.1 review shallowing) need targeted follow-up before this can be fully endorsed.
