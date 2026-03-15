# Insight Codex

I examined `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt`, the seven history runs listed in `analysis/6_identify_potential_levers/meta.json`, and the corresponding `baseline/train/*/002-9-potential_levers_raw.json` and `baseline/train/*/002-10-potential_levers.json` artifacts.

## Rankings

1. **Run 49 — `openai-gpt-5-nano`**: best overall balance of specificity, prompt compliance, complete summaries, and diversity; the main drawback is speed.
2. **Run 48 — `openrouter-openai-gpt-oss-20b`**: strong content quality and clean field boundaries, but too many null summaries.
3. **Run 51 — `openrouter-openai-gpt-4o-mini`**: fastest successful run and structurally clean, but less explicit about trade-offs and still drops some summaries.
4. **Run 52 — `anthropic-claude-haiku-4-5-pinned`**: very rich content, but massively overlong and it breaks the exact-5-levers-per-response rule once.
5. **Run 50 — `openrouter-qwen3-30b-a3b`**: high diversity and measurable consequences, but every consequence leaks review text (`Controls ...` / `Weakness:`), which is a severe field-boundary failure.
6. **Run 47 — `ollama-llama3.1`**: completes all plans, but many options collapse into labels rather than strategic approaches and almost all summaries are null.
7. **Run 46 — `openrouter-nvidia-nemotron-3-nano-30b-a3b`**: complete operational failure; no plan produced a clean artifact.

## Negative Things

- **Run 46 is unusable.** All five plans fail in `history/0/46_identify_potential_levers/outputs.jsonl` with JSON-extraction errors such as `Could not extract json string from output`.
- **Run 47 satisfies the outer JSON shape but not the intended content contract.** In `history/0/47_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the first lever uses options like `"Utilitarian Grid"`, `"Hierarchical Stack"`, and `"Radical Spheroid"`, which are labels rather than self-contained strategic approaches. Across the run, 50/225 options are under 35 characters and 14/15 summaries are null in the raw files.
- **Run 50 has systematic field leakage.** In `history/0/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the first `consequences` field ends with `Controls efficiency vs. redundancy. Weakness: ...`, and the `review` field then repeats the same text. This happens in 75/75 consequences.
- **Run 52 breaks the prompt's exact-count requirement and is too verbose for this step.** `history/0/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json` contains 6 levers in its first response, and the final clean file `history/0/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` therefore contains 16 levers instead of 15. Its average consequence length is 1060.1 characters versus 279.5 in baseline.
- **Runs 48 and 51 still have summary-completion problems.** `history/0/48_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` and `history/0/51_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json` both include `"summary": null`; the aggregate counts are 10 null summaries for run 48 and 4 for run 51.
- **Baseline is not a clean gold standard for current prompt compliance.** `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats the same five lever names three times, and baseline overall still has 21/75 consequences without a numeric indicator and 27 duplicate normalized names across raw-call merges.

## Positive Things

- **All successful history runs beat baseline on cross-call name diversity.** Baseline has 27 cross-call duplicate normalized names across the five plans, while runs 47 through 52 all reduce that to 0.
- **Run 49 is the clearest positive example of the target behavior.** In `history/0/49_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, the first lever includes a measured systemic effect (`20%`, `12%`), an explicit trade-off cue (`trade-off: speed vs centralized control`), and three full-sentence options with clear conservative → moderate → radical progression.
- **Run 48 is also materially stronger than baseline on diversity without becoming bloated.** It reaches 74 unique names out of 75 levers and 225 unique options out of 225, versus baseline's 52 unique names out of 75.
- **Run 51 is operationally attractive.** It is the fastest successful run at 42.1 seconds average per plan-set in `history/0/51_identify_potential_levers/outputs.jsonl`, while still keeping 75 exact-unique names and 225 exact-unique options.
- **The prompt successfully suppresses placeholder syntax and explicit option prefixes in successful runs.** I found 0 placeholder strings like `[specific ...]` and 0 `Option A:` / `Choice 1:` prefixes in runs 47 through 52.

## Comparison

- **Against baseline:** the new prompt clearly improves diversity. Baseline produces only 52 exact-unique names and 47 normalized-unique names across 75 levers, while every successful run except run 48 reaches 75 exact-unique names and 74+ normalized-unique names.
- **Against baseline:** the new prompt does **not** automatically improve summary reliability. Baseline has 0 null summaries; runs 47, 48, and 51 regress badly on that metric.
- **Run 49 vs. run 48:** run 49 is richer and more explicit about trade-offs, but much slower (220.1 s vs. 90.9 s average). Run 48 is the better speed/quality compromise if summary nulls can be repaired downstream.
- **Run 51 vs. run 49:** run 51 is far faster and structurally clean, but its consequences are plainer and less likely to include explicit trade-off phrasing. The first silo lever in `history/0/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` is competent, but it reads closer to a generic strategic memo than a tension-driven lever set.
- **Run 52 vs. run 49:** run 52 is often more imaginative, but its verbosity looks counterproductive for this step. The outputs are so long that they risk hurting downstream deduplication, review, and cost without clearly improving contract fidelity.
- **Run 50 vs. the rest:** run 50 looks strong on surface metrics like uniqueness and numeric consequences, but that is misleading because every consequence also contains review text. It is less usable than runs 48, 49, and 51 despite its diversity scores.
- **Run 47 vs. baseline:** run 47 improves uniqueness but loses the core idea of “strategic approaches.” Baseline options are long and actionable; run 47 frequently emits compact labels.

## Quantitative Metrics

Normalization note: “Norm. unique names” lowercases names, strips punctuation, and removes generic suffix words such as `strategy`, `plan`, `framework`, and `protocol`.

### Coverage and Diversity

| Run | Model | Plans ok | Avg s | Levers | Unique names | Norm. unique names | Unique options | Cross-call dup names | Null summaries | Raw resp !=5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | baseline | 5/5 | — | 75 | 52 | 47 | 225 | 27 | 0 | 0 |
| 46 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | 94.9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 47 | ollama-llama3.1 | 5/5 | 66.3 | 75 | 75 | 75 | 178 | 0 | 14 | 0 |
| 48 | openrouter-openai-gpt-oss-20b | 5/5 | 90.9 | 75 | 74 | 74 | 225 | 0 | 10 | 0 |
| 49 | openai-gpt-5-nano | 5/5 | 220.1 | 75 | 75 | 75 | 217 | 0 | 0 | 0 |
| 50 | openrouter-qwen3-30b-a3b | 5/5 | 96.7 | 75 | 75 | 75 | 225 | 0 | 0 | 0 |
| 51 | openrouter-openai-gpt-4o-mini | 5/5 | 42.1 | 75 | 75 | 74 | 225 | 0 | 4 | 0 |
| 52 | anthropic-claude-haiku-4-5-pinned | 5/5 | 141.8 | 76 | 76 | 76 | 228 | 0 | 0 | 1 |

What this means:

- Baseline is the least diverse by name because the same concepts recur across raw calls and survive into the merged file.
- Run 47's perfect name uniqueness is not enough by itself; it also has the weakest option depth and worst summary completion.
- Run 52's 76 names are not a strength; that extra count is partly a contract violation caused by one 6-lever response.

### Average Field Lengths

| Run | Avg name chars | Avg consequence chars | Avg option chars | Avg review chars | Avg summary chars |
|---|---:|---:|---:|---:|---:|
| baseline | 27.7 | 279.5 | 150.2 | 152.3 | 443.7 |
| 46 | 0 | 0 | 0 | 0 | 0 |
| 47 | 32.1 | 142.0 | 58.4 | 160.1 | 14.3 |
| 48 | 34.5 | 313.0 | 90.1 | 120.1 | 202.1 |
| 49 | 42.3 | 420.9 | 117.0 | 144.6 | 411.4 |
| 50 | 37.2 | 365.4 | 71.2 | 129.9 | 295.5 |
| 51 | 34.2 | 262.5 | 124.0 | 152.7 | 231.9 |
| 52 | 56.2 | 1060.1 | 361.1 | 443.5 | 1374.7 |

What this means:

- Run 47 is too terse, especially in options and summaries.
- Runs 48, 49, and 51 sit in a usable middle band.
- Run 52 is an outlier in every text field; this is likely too verbose for a lever-generation stage.

### Constraint Violations and Leakage

`Trade-off miss*` is a heuristic count of consequences lacking obvious cue words such as `but`, `while`, `trade-off`, or `vs.`. I use it directionally, not as a hard validator.

| Run | Missing numeric | Missing markers | Trade-off miss* | Short options (<35) | `Controls` in consequences | `Weakness:` in consequences | Placeholders |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 21 | 5 | 27 | 0 | 0 | 0 | 0 |
| 46 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 47 | 75 | 0 | 75 | 50 | 0 | 0 | 0 |
| 48 | 0 | 0 | 1 | 2 | 0 | 0 | 0 |
| 49 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 50 | 0 | 0 | 0 | 0 | 75 | 75 | 0 |
| 51 | 0 | 0 | 30 | 0 | 0 | 0 | 0 |
| 52 | 0 | 0 | 14 | 0 | 0 | 0 | 0 |

What this means:

- Run 47's main failure is not structure; it is shallow content. Every consequence lacks a numeric indicator and many options are just labels.
- Run 50's perfect numeric score hides a more serious problem: the consequence field is contaminated in every single case.
- Baseline already violates several current prompt expectations, so baseline similarity should not be treated as equivalent to prompt compliance.

## Evidence Notes

- **Prompt contract:** `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt` explicitly requires exactly 5 levers per response, exactly 3 options per lever, measurable outcomes in `Systemic:`, and no prefixed / generic option labels.
- **Run 46 parse failure:** `history/0/46_identify_potential_levers/outputs.jsonl` shows five `status: "error"` rows and repeated `Could not extract json string from output` failures.
- **Run 47 label-like options:** `history/0/47_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` starts with `Utilitarian Grid`, `Hierarchical Stack`, and `Radical Spheroid` as the three options.
- **Run 47 null summaries:** `history/0/47_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` has `"summary": null` for all three responses; similar nulls recur in the other four plans.
- **Run 48 summary weakness but otherwise solid content:** `history/0/48_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains measured, actionable levers, but `history/0/48_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` still has null summaries.
- **Run 49 positive exemplar:** `history/0/49_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` first lever is the cleanest example of measured, tension-aware, full-sentence output.
- **Run 50 field leakage:** `history/0/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` first consequence contains both `Controls efficiency vs. redundancy.` and `Weakness:` before the `review` field repeats them.
- **Run 51 speed/quality trade-off:** `history/0/51_identify_potential_levers/outputs.jsonl` shows the best average runtime, while `history/0/51_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows competent but more standardized phrasing.
- **Run 52 overcount:** `history/0/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-9-potential_levers_raw.json` contains 6 levers in response 0, and `history/0/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` consequently has 16 total levers.
- **Baseline duplication:** `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats `Technical Feasibility Strategy`, `Policy Advocacy Strategy`, `Coalition Building Strategy`, `Procurement Influence Strategy`, and `EU Standards Engagement Strategy` three times each.

## Questions For Later Synthesis

- Is the optimization target supposed to favor **prompt compliance** or **similarity to baseline artifacts** when those two disagree?
- Should summary completeness be treated as a hard requirement? The step currently tolerates null summaries, but the prompt asks for a concrete missing dimension and addition.
- Is run 52's verbosity actually helpful downstream, or does it just inflate cost and reduce mergeability?
- Should consequences be required to express trade-offs naturally, or should trade-off wording live only in `review` to reduce leakage like run 50?
- Would a speed-first policy accept run 51 over run 49, or is run 49's richer reasoning worth the 5x runtime penalty?

## Reflect

### H1

**Change:** Tighten the option instruction so each option must be a full sentence with an action verb and a minimum detail floor, for example: “Each option must be 12+ words and describe a concrete approach, not a title.”

**Evidence:** Run 47 produces many label-like options in `history/0/47_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, and quantitatively 50/225 options are under 35 characters.

**Predicted effect:** Fewer title-only options and better conservative → moderate → radical progression.

### H2

**Change:** Make the summary instruction fully literal, for example requiring exactly two sentences: `One critical missing dimension is ...` and `Add '...' to [lever]`.

**Evidence:** Run 47 has 14 null summaries, run 48 has 10, and run 51 has 4, even though the prompt already requests a concrete missing dimension and addition.

**Predicted effect:** Better summary completion and easier downstream validation.

### H3

**Change:** Add an explicit sentence that `consequences` must describe trade-offs naturally but must never contain `Controls` or `Weakness:` phrases; those strings belong only in `review`.

**Evidence:** Run 50 leaks review text into all 75 consequence fields, with a clear example in `history/0/50_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

**Predicted effect:** Cleaner field boundaries without losing trade-off content.

### H4

**Change:** Add a soft verbosity band for all long fields, especially consequences and summaries, such as “prefer 60–120 words for consequences and 40–90 words for summaries.”

**Evidence:** Run 52 averages 1060.1 characters per consequence and 1374.7 per summary, far above baseline and all other runs, while also breaking the response-size contract once.

**Predicted effect:** Less bloat, lower latency, and fewer overlong outputs that strain downstream review.

## Potential Code Changes

### C1

**Change:** Enforce the raw schema in `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` instead of only describing it. In particular, make `levers` length-constrained to exactly 5 and make `summary` required, because the current model uses `description="Propose exactly 5 levers."` and `summary: Optional[str]` but `execute()` still flattens whatever comes back.

**Evidence:** The relevant implementation points are `../PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` lines reported by ripgrep at 75, 77, 243, and 250. Empirically, run 52 returns a 6-lever response and runs 47/48/51 persist null summaries.

**Predicted effect:** Hard validation failures will catch overcounts and missing summaries before they become saved artifacts.

### C2

**Change:** Add a post-generation validator/repair pass in the same step implementation that rejects or rewrites outputs when `consequences` contains `Controls` / `Weakness:` text or when options look like short labels rather than strategies.

**Evidence:** Run 50 contaminates 75/75 consequence fields with review text, and run 47 emits many title-like options. Both defects survive into `002-10-potential_levers.json`.

**Predicted effect:** Better final-file usability independent of model choice.

### C3

**Change:** Enable retry / validation-retry behavior in `../PlanExe/prompt_optimizer/runner.py` when constructing `LLMExecutor`, instead of the current bare `LLMExecutor(llm_models=llm_models)`.

**Evidence:** `../PlanExe/prompt_optimizer/runner.py` line 94 constructs the executor with no retry configuration. Run 46 then fails all five plans on extraction errors in `history/0/46_identify_potential_levers/outputs.jsonl`.

**Predicted effect:** Fewer total-run failures from transient parse/extraction issues, especially for weaker models.

### C4

**Change:** Split evaluation into two scores: **baseline resemblance** and **prompt-contract compliance**.

**Evidence:** Baseline itself contains duplicate merged levers and several missing numeric / marker cases, so optimizing only toward baseline can reward outputs that are less compliant with the current prompt than runs 48, 49, or 51.

**Predicted effect:** Future prompt iterations should converge toward outputs that are both useful relative to training data and faithful to the current contract.

## Summary

- **Best overall run:** 49 (`openai-gpt-5-nano`) because it combines high diversity, complete summaries, strong measurable consequences, and clean field boundaries.
- **Best fast run:** 51 (`openrouter-openai-gpt-4o-mini`) if speed matters more than peak richness.
- **Main failure modes in this batch:** total parse failure (46), label-only options and null summaries (47), null summaries with otherwise solid content (48, 51), consequence/review leakage (50), and overlong / overcounted outputs (52).
- **Most important synthesis caveat:** baseline is useful as a content prior but not as a strict compliance oracle.
- **Highest-leverage next moves:** tighten option and summary instructions, explicitly forbid review-text leakage into `consequences`, and add schema validation plus retry logic in the step/runner code.
