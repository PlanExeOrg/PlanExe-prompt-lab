# Insight Codex

## Rankings

1. **13 / gpt-oss-20b** — best prompt-shape adherence on successful plans, but one hard failure makes it risky overall.
2. **15 / gpt-4o-mini** — best all-success run for prompt-following stability; strong summaries, but repeated lever names remain common.
3. **14 / qwen3-30b-a3b** — concise and mostly on-topic, but it systematically drops exact consequence marker syntax.
4. **12 / claude-haiku-4.5** — rich strategic content and high name diversity, but extreme verbosity and poor summary-format compliance.
5. **10 / gpt-5-nano** — diverse lever naming, but it repeatedly substitutes `Trade-off:` for the required `Controls A vs. B.` review format.
6. **16 / llama3.1** — lowest structural compliance; option-prefix leakage and one 10-lever response make it the weakest run.

## Negative Things

- The biggest issue is **not model-specific**: both baseline and almost every history run materialize **15 final levers** instead of a 5-lever deliverable, because the final artifact appears to flatten three 5-lever raw responses into one file. The prompt explicitly requires “EXACTLY 5 levers per response” and exactly 3 options per lever in `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:4` and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:5`.
- The **baseline training data is itself structurally non-compliant** with the prompt, so it is a weak oracle for “strict prompt adherence.” Example: `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:4`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:15`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:26`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:37`, and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:48` introduce one 5-lever set, while repeated names reappear later at `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:136`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:147`, and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:158`.
- **H1:** tighten the review syntax instruction. `10 / gpt-5-nano` repeatedly emits `Trade-off:` instead of the required `Controls [Tension A] vs. [Tension B].`, as shown in `history/0/10_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`. The prompt requirement is explicit at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`.
- **H2:** tighten the consequence-string template. `14 / qwen3-30b-a3b` often keeps the semantic chain but drops the exact `Immediate:` / `Systemic:` / `Strategic:` formatting, e.g. `history/0/14_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9` and `history/0/14_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:20`. The prompt asks for the literal marker sequence at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:9`.
- **H3:** add a stronger summary-format instruction or few-shot example. `12 / claude-haiku-4.5` produces summaries that identify a missing dimension, but often phrase the addition as `Add to Governance Philosophy: '...'` rather than `Add '...' to [lever]`, e.g. `history/0/12_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`. The prompt requires the exact pattern at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:29`.
- **H4:** explicitly penalize option prefixes with a model-facing negative example. `16 / llama3.1` leaks `Option 1:`/`Option 2:`/`Option 3:` in generated fields at `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:7`, `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:8`, and `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:9`, despite the prohibition in `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:16` and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:32`.
- **H5:** add an anti-duplication instruction for multi-response generation or final selection. `15 / gpt-4o-mini` is structurally strong but repeats names across responses in the final artifact; `Supplier Diversification Strategy` and `Coalition Building Strategy` recur in `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`, `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:37`, `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:59`, `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:92`, `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:114`, and `history/0/15_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:147`.
- `13 / gpt-oss-20b` has the best field-level compliance, but its failure mode is severe: `history/0/13_identify_potential_levers/outputs.jsonl:4` shows a hard extraction failure for `20260311_parasomnia_research_unit` after emitting an apparently useful but incomplete JSON object.

## Positive Things

- The prompt does succeed at eliciting **strategic-concept lever names** and **three-option structures** from most models. `15 / gpt-4o-mini` is a clean example: `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:8`, `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9`, `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:10`, and `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15` show one lever with exact markers, three options, and a correctly formatted review.
- `13 / gpt-oss-20b` demonstrates that the current prompt **can** induce near-exact compliance when the model stays inside the JSON rails. `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:8`, `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9`, `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:10`, and `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15` are close to the requested shape.
- `15 / gpt-4o-mini` is also the strongest summary follower. Its first raw response closes with the required `Add '...' to ...` pattern at `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- None of the runs showed **direct template leakage in generated fields**: no generated `Option A`, `Choice 1`, `[effect]`, `[impact]`, `[implication]`, or `[specific innovative option]` strings were found. The raw files do store the full system prompt as metadata, e.g. `baseline/train/20250321_silo/002-9-potential_levers_raw.json:383`, but that is metadata echo rather than model output leakage.
- Baseline and several runs still surface useful strategic tensions even when format drifts. The problem is mainly **selection/validation fidelity**, not total content collapse.

## Comparison

- Relative to baseline, the history runs do **not** clearly improve the top-level deliverable shape. Baseline already returns 15 final levers for every plan, and most candidate runs do the same. This suggests the main lever is likely code-side aggregation or validation, not only prompt phrasing.
- Relative to baseline’s duplicate-heavy outputs, `10 / gpt-5-nano` and `12 / claude-haiku-4.5` improve **name diversity** substantially: both average ~15 unique names per plan versus baseline’s 10.6.
- Relative to baseline’s moderate verbosity, `12 / claude-haiku-4.5` overshoots badly: average consequence length is 657.4 characters and average option length is 315.4, more than 2× baseline. This likely hurts consistency and extractability.
- Relative to baseline’s review compliance, `10 / gpt-5-nano` regresses because it systematically chooses `Trade-off:` over `Controls ... vs. ...`.
- Relative to baseline’s duplication issue, `15 / gpt-4o-mini` is mixed: it keeps all five plans successful and has low formal-violation counts, but its final outputs still repeat lever names heavily in some plans.
- Relative to all other successful runs, `13 / gpt-oss-20b` is the closest to the requested format on a per-lever basis, but its one failed plan is a serious reliability regression.

## Quantitative Metrics

### Metric definitions

- **Constraint violations** count one point per violated rule in the final levers: wrong option count, missing `Immediate:`, missing `Systemic:`, missing `Strategic:`, missing arrow, missing `%` metric, malformed review trade-off, missing `Weakness:`, or banned option prefixes.
- **Summary format ok** counts raw responses whose summary matched `Add '...' to [lever]` with exactly one quoted addition.
- **Generated template leakage** excludes raw metadata fields such as `system_prompt` and scans only generated fields.

### Aggregate run metrics

| Run | Plans ok | Avg levers | Avg unique names | Avg unique options | Avg name len | Avg consequence len | Avg review len | Avg option len | Avg constraint violations | Summary format ok | Generated template leakage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 5/5 | 15.0 | 10.6 | 45.0 | 27.7 | 279.5 | 152.3 | 150.2 | 5.2 | 9/15 | 0/5 |
| 10 / gpt-5-nano | 5/5 | 15.2 | 15.2 | 45.0 | 41.4 | 271.6 | 161.9 | 146.7 | 16.8 | 15/15 | 0/5 |
| 12 / claude-haiku-4.5 | 5/5 | 15.0 | 15.0 | 45.0 | 43.4 | 657.4 | 412.4 | 315.4 | 13.4 | 0/15 | 0/5 |
| 13 / gpt-oss-20b | 4/5 | 15.0 | 14.2 | 45.2 | 32.1 | 217.2 | 133.6 | 94.8 | 0.2 | 7/12 | 0/5 |
| 14 / qwen3-30b-a3b | 5/5 | 15.0 | 14.0 | 44.8 | 30.1 | 196.6 | 138.1 | 61.2 | 10.4 | 14/15 | 0/5 |
| 15 / gpt-4o-mini | 5/5 | 15.0 | 11.2 | 45.0 | 30.7 | 209.3 | 141.3 | 109.4 | 4.0 | 15/15 | 0/5 |
| 16 / llama3.1 | 5/5 | 16.0 | 14.8 | 45.8 | 29.3 | 176.5 | 143.8 | 86.5 | 21.0 | 5/15 | 0/5 |

### Violation breakdown

| Run | Wrong option count | Missing `Immediate:` | Missing `Systemic:` | Missing `Strategic:` | Missing arrow | Missing `%` | Bad review trade-off | Missing `Weakness:` | Option prefixes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0 | 5 | 0 | 0 | 0 | 21 | 0 | 0 | 0 |
| 10 / gpt-5-nano | 2 | 0 | 0 | 0 | 32 | 0 | 50 | 0 | 0 |
| 12 / claude-haiku-4.5 | 0 | 0 | 0 | 0 | 30 | 37 | 0 | 0 | 0 |
| 13 / gpt-oss-20b | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 / qwen3-30b-a3b | 0 | 15 | 15 | 15 | 5 | 2 | 0 | 0 | 0 |
| 15 / gpt-4o-mini | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 16 / llama3.1 | 2 | 0 | 0 | 0 | 0 | 78 | 4 | 6 | 15 |

### Per-plan final lever counts

| Run | `20250321_silo` | `20250329_gta_game` | `20260308_sovereign_identity` | `20260310_hong_kong_game` | `20260311_parasomnia_research_unit` |
|---|---:|---:|---:|---:|---:|
| Baseline | 15 | 15 | 15 | 15 | 15 |
| 10 / gpt-5-nano | 15 | 16 | 15 | 15 | 15 |
| 12 / claude-haiku-4.5 | 15 | 15 | 15 | 15 | 15 |
| 13 / gpt-oss-20b | 15 | 15 | 15 | 15 | ERR |
| 14 / qwen3-30b-a3b | 15 | 15 | 15 | 15 | 15 |
| 15 / gpt-4o-mini | 15 | 15 | 15 | 15 | 15 |
| 16 / llama3.1 | 20 | 15 | 15 | 15 | 15 |

### Per-plan unique lever names

| Run | `20250321_silo` | `20250329_gta_game` | `20260308_sovereign_identity` | `20260310_hong_kong_game` | `20260311_parasomnia_research_unit` |
|---|---:|---:|---:|---:|---:|
| Baseline | 11 | 14 | 5 | 12 | 11 |
| 10 / gpt-5-nano | 15 | 16 | 15 | 15 | 15 |
| 12 / claude-haiku-4.5 | 15 | 15 | 15 | 15 | 15 |
| 13 / gpt-oss-20b | 14 | 15 | 13 | 15 | ERR |
| 14 / qwen3-30b-a3b | 14 | 14 | 13 | 14 | 15 |
| 15 / gpt-4o-mini | 13 | 13 | 8 | 10 | 12 |
| 16 / llama3.1 | 19 | 15 | 13 | 13 | 14 |

## Evidence Notes

- Prompt requirements live at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:4`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:5`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:9`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:10`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:29`, and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:32`.
- The raw artifacts clearly contain a multi-response structure beginning at `baseline/train/20250321_silo/002-9-potential_levers_raw.json:2` and include prompt metadata at `baseline/train/20250321_silo/002-9-potential_levers_raw.json:383`.
- `15 / gpt-4o-mini` provides the clearest “prompt can work” example in `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:8`, `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9`, `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, and `history/0/15_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:62`.
- `10 / gpt-5-nano` demonstrates a stable but wrong review prefix at `history/0/10_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`.
- `14 / qwen3-30b-a3b` demonstrates semantic compliance but exact-string drift in consequences at `history/0/14_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9`.
- `16 / llama3.1` demonstrates direct option-prefix violations at `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:7`.
- `13 / gpt-oss-20b` demonstrates strong format fidelity in successful runs at `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9` and `history/0/13_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, but hard runtime failure at `history/0/13_identify_potential_levers/outputs.jsonl:4`.

## Questions For Later Synthesis

- Is the real objective to optimize **raw response quality** or **final artifact quality**? The evidence suggests those are diverging because the final writer appears to flatten three raw responses.
- Should baseline be treated as a target for imitation or only as incumbent behavior? It is valuable as “what the system currently produces,” but not as a strict-format gold standard.
- Would a small validator/post-processor change outperform another prompt iteration here?
- If multi-response generation is intentional, should the final step deduplicate to five “vital few” levers rather than concatenate all responses?
- For summary format, is exact string syntax important downstream, or only semantic presence?

## Reflect

- The strongest synthesis candidate is probably **not** “rewrite the prompt from scratch.” The prompt already gets some models very close; the bigger leverage looks like downstream aggregation and validation.
- The most telling signal is that the same 15-lever pattern exists in both baseline and almost every candidate run. That makes the issue look systemic.
- If prompt-only work is pursued, I would focus on **precision instructions for review and consequence strings** plus **anti-duplication guidance**, because those are the most repeatable model-side misses.
- If code changes are allowed later, I would prioritize them ahead of another broad prompt search.

## Potential Code Changes

- **C1:** The final artifact writer likely concatenates `responses[*].levers` instead of selecting one response or deduplicating to a 5-lever output. Evidence: every baseline plan and nearly every successful history plan has 15 final levers, while raw artifacts are visibly multi-response (`baseline/train/20250321_silo/002-9-potential_levers_raw.json:2`).
- **C2:** Structural validation is probably too weak or too late. Runs marked `ok` still contain repeated violations of exact required syntax: `Trade-off:` instead of `Controls ... vs. ...` in `history/0/10_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:15`, missing marker colons in `history/0/14_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json:9`, and prefixed options in `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:7`.
- **C3:** JSON extraction/recovery is brittle for long but near-valid outputs. `history/0/13_identify_potential_levers/outputs.jsonl:4` suggests the run had useful content but failed because the parser could not salvage it.
- **C4:** A deduplication or re-ranking pass is missing before finalization. Repeated names in baseline and `15 / gpt-4o-mini` imply the system lacks a “pick the best five distinct levers” phase even though the step name suggests a vital-few style output.

## Summary

- The central insight is that **aggregation/validation looks like the dominant lever**, not just prompt wording.
- `13 / gpt-oss-20b` shows the best prompt-shape compliance, but `15 / gpt-4o-mini` is the best all-success compromise.
- Baseline is useful as incumbent behavior, but it is already non-compliant with the prompt, especially on final lever count and duplication.
- The highest-value next moves are likely: fix final-response selection, enforce exact-string validation, and only then iterate on narrower prompt hypotheses H1-H5.
