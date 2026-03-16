# Insight Codex

## Rankings

1. **Run 14** (`openrouter-openai-gpt-4o-mini`) — best balance of specificity, uniqueness, and manageable length; still weak on explicit trade-off wording.
2. **Run 11** (`openrouter-openai-gpt-oss-20b`) — strongest structural/content balance after Run 14, but some outputs use `Immediate/Systemic/Strategic` without the arrow chain and the run is operationally noisy.
3. **Run 12** (`openai-gpt-5-nano`) — only run with meaningful summary-template uptake, but it leaks placeholders in one plan and many reviews miss the exact protocol.
4. **Run 15** (`openrouter-gemini-2.0-flash-001`) — very strong consequence content, but review-template compliance collapses.
5. **Run 13** (`openrouter-qwen3-30b-a3b`) — very good consequence compliance and uniqueness, but options often drift into `Title: description` label style and reviews almost always miss the exact wording.
6. **Run 10** (`ollama-llama3.1`) — best exact review compliance, but consequences are much shallower than baseline and it over-generates levers.
7. **Run 16** (`anthropic-claude-haiku-4-5-pinned`) — rich ideas, but severe verbosity and near-total format drift make it hard to use directly.
8. **Run 09** (`ollama-llama3.1`) — unusable for content analysis because it never produced outputs.

## Negative Things

- The prompt successfully pushes uniqueness and measurable consequences, but most models still ignore the **exact** `review_lever` contract from `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`. Baseline already had only `8 / 75` exact review matches; Runs 13, 15, and 16 stay poor at `15 / 85`, `17 / 90`, and `0 / 77`.
- The `summary` instruction is mostly ineffective. Baseline has `0 / 15` exact matches and Runs 10, 11, 13, 14, 15, and 16 also have `0` exact matches. Only Run 12 materially improves this (`9 / 12`).
- Run 10 over-corrects toward rigid template obedience: it gets `87 / 87` exact raw review matches, but `80 / 87` raw consequences still lack measurable outcomes and `86 / 87` lack explicit trade-off language.
- Run 16 swings to the opposite extreme: average consequence length reaches `857.34` characters and average review length `318.40`, while `56` final consequences still miss the strict arrow-chain format.
- Placeholder/template leakage remains possible under the new prompt. `history/1/12_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` contains repeated review strings like `Controls [production scale] vs. [creative autonomy]...`.
- Label-like option formatting still leaks through. `history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` includes options like `Imperial Oversight: ...`, which violates the spirit of the “NO prefixes” rule even though it is not literally `Option A:`.
- Operationally, the batch is noisy: Run 10 has a `ReadTimeout`, Runs 11–16 all contain authentication failures, and Run 09 stopped after a single start event. I found **no** `ValidationError`/Pydantic-schema failures in `events.jsonl` or `outputs.jsonl` for Runs 09–16; the observed failures are infra/auth, not schema rejection.

## Positive Things

- The prompt clearly improves **lever-name diversity** relative to baseline. Baseline raw outputs contain `22` cross-call duplicate names (`53 / 75` unique), while Runs 11, 12, 14, 15, and 16 have `0` duplicate names across raw responses.
- The prompt also improves **measurable consequence content** for most non-llama models. Baseline has `21` consequences without numeric outcomes and `26` without explicit trade-off wording; Runs 11–16 all reduce numeric-missing to `0`.
- The best runs produce more domain-specific lever names than baseline. In `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json`, the same five names repeat three times; Run 14’s `history/1/14_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` replaces that pattern with 17 distinct names.
- Response-level lever count control is mostly good outside Run 10. Baseline is `15 / 15` responses in range; Runs 11–16 stay fully in range (`10 / 10`, `12 / 12`, `15 / 15`, `15 / 15`, `15 / 15`, `11 / 11`).
- Option count stays stable: all successful runs keep exactly 3 options per lever in the final outputs I checked.
- Run 14 is especially promising because it keeps lengths closer to baseline (`240.86` avg consequence chars vs `279.50` baseline) while removing cross-call duplicate names and keeping numeric outcomes present.

## Comparison

The main gain versus baseline is **diversity**. Baseline still looks like a “three calls, lightly merged” artifact: `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats `Technical Feasibility Strategy`, `Policy Advocacy Strategy`, `Coalition Building Strategy`, `Procurement Influence Strategy`, and `EU Standards Engagement Strategy` three times each. By contrast, Run 14’s corresponding file (`history/1/14_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`) yields a fully distinct set including `Resilience Framing in Policy Advocacy`, `Procurement Language Influence`, and `Decentralized Trust Framework Exploration`.

The second gain is **consequence specificity**. Baseline often has the three-stage structure but misses either numbers or explicit tensions. Run 14’s `history/1/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` includes a concise consequence with a numeric indicator and trade-off: `Reduce material costs by 15%` and `enhances budget flexibility but may compromise quality control.` Run 10’s first lever in `history/1/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` still reads like generic baseline-era content: `Immediate: Complex resource management → Systemic: Increased dependence on internal systems → Strategic: Reduced adaptability to external changes`.

The big unresolved problem is **exact template control**. The prompt explicitly asks for `review_lever` in one exact two-sentence pattern and for a summary beginning `One critical missing dimension... Add '...' to ...`, but most models do not follow that literally. Run 11 often stays semantically correct while drifting on punctuation or wording — for example `history/1/11_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` uses `Controls bulk procurement vs. modular sourcing. Weakness: The options ignore supply chain resilience under geopolitical shocks.` Run 16 drifts further, producing long freeform review prose in `history/1/16_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

The best overall comparison point is therefore:

- **Baseline → Run 14**: strong improvement in uniqueness and numeric specificity, modest regression on explicit trade-off wording.
- **Baseline → Run 12**: strong improvement in uniqueness and the only meaningful summary-template progress, but placeholder leakage appears.
- **Baseline → Run 10**: improvement in exact review formatting, regression in consequence depth and genericity.
- **Baseline → Run 16**: improvement in richness, but likely unusable without normalization because the output is too verbose and often off-format.

## Quantitative Metrics

Method notes:

- Raw-response metrics come from `002-9-potential_levers_raw.json`.
- Final merged metrics come from `002-10-potential_levers.json`.
- “Exact review match” uses the strict pattern `Controls ... vs. .... Weakness: The options fail to consider ...`.
- “Exact summary match” uses the strict pattern `One critical missing dimension is ... . Add '...' to ...`.
- This strictness is useful for auditability, but it does count punctuation-level near-misses as violations.

### Reliability

| Artifact | Model | Successful plans | Error entries | Auth errors | Timeouts | Validation errors |
|---|---|---:|---:|---:|---:|---:|
| Baseline | `reference` | 5 | 0 | 0 | 0 | 0 |
| Run 09 | `ollama-llama3.1` | 0 | 0 | 0 | 0 | 0 |
| Run 10 | `ollama-llama3.1` | 4 | 1 | 0 | 1 | 0 |
| Run 11 | `openrouter-openai-gpt-oss-20b` | 4 | 6 | 5 | 0 | 0 |
| Run 12 | `openai-gpt-5-nano` | 4 | 6 | 5 | 0 | 0 |
| Run 13 | `openrouter-qwen3-30b-a3b` | 5 | 5 | 5 | 0 | 0 |
| Run 14 | `openrouter-openai-gpt-4o-mini` | 5 | 5 | 5 | 0 | 0 |
| Run 15 | `openrouter-gemini-2.0-flash-001` | 5 | 5 | 5 | 0 | 0 |
| Run 16 | `anthropic-claude-haiku-4-5-pinned` | 5 | 5 | 5 | 0 | 0 |

### Raw-response compliance and diversity

| Artifact | Responses | In-range (5–7) | Avg levers/response | Unique names | Exact review matches | Exact summary matches | Cross-call duplicate names |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 15 | 15 | 5.00 | 53 / 75 | 8 / 75 | 0 / 15 | 22 |
| Run 10 | 12 | 9 | 7.25 | 75 / 87 | 87 / 87 | 0 / 12 | 12 |
| Run 11 | 10 | 10 | 6.21 | 62 / 62 | 53 / 62 | 0 / 10 | 0 |
| Run 12 | 12 | 12 | 6.00 | 72 / 72 | 30 / 72 | 9 / 12 | 0 |
| Run 13 | 15 | 15 | 5.67 | 84 / 85 | 15 / 85 | 0 / 15 | 1 |
| Run 14 | 15 | 15 | 5.93 | 89 / 89 | 58 / 89 | 0 / 15 | 0 |
| Run 15 | 15 | 15 | 6.00 | 90 / 90 | 17 / 90 | 0 / 15 | 0 |
| Run 16 | 11 | 11 | 7.00 | 77 / 77 | 0 / 77 | 0 / 11 | 0 |

### Final merged output depth and consequence compliance

| Artifact | Avg consequence chars | Avg review chars | Avg option chars | Chain violations | Missing numeric outcome | Missing explicit trade-off |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 279.50 | 152.26 | 150.18 | 5 | 21 | 26 |
| Run 10 | 131.75 | 148.68 | 75.88 | 0 | 68 | 74 |
| Run 11 | 298.90 | 131.35 | 79.20 | 18 | 0 | 0 |
| Run 12 | 370.23 | 132.57 | 115.70 | 18 | 0 | 0 |
| Run 13 | 327.46 | 129.26 | 70.60 | 0 | 0 | 2 |
| Run 14 | 240.86 | 149.74 | 109.68 | 0 | 0 | 44 |
| Run 15 | 395.46 | 155.50 | 128.46 | 0 | 0 | 6 |
| Run 16 | 857.34 | 318.40 | 286.38 | 56 | 0 | 8 |

### Template leakage and stylistic violations

| Artifact | Placeholder leakage | Label-like options (`Title: description`) | 1–2 word lever names |
|---|---:|---:|---:|
| Baseline | 0 | 16 | 6 |
| Run 10 | 0 | 0 | 36 |
| Run 11 | 0 | 0 | 16 |
| Run 12 | 6 | 1 | 0 |
| Run 13 | 0 | 15 | 1 |
| Run 14 | 0 | 0 | 1 |
| Run 15 | 0 | 0 | 14 |
| Run 16 | 0 | 6 | 0 |

Interpretation:

- **Run 14** is the best “balanced” row: zero duplicate names, zero missing numeric outcomes, zero chain violations, manageable length, but too many consequences still omit an explicit trade-off phrase.
- **Run 12** is the only row with strong summary-template uptake, but that comes with placeholder leakage and middling exact review compliance.
- **Run 10** shows that exact review compliance alone is not enough; its consequence depth is the weakest of all successful runs.
- **Run 16** shows the failure mode of over-optimization toward elaboration: lots of detail, but the format becomes hard to normalize and expensive to parse.

## Evidence Notes

- The prompt itself adds the new hard asks: 5–7 levers per response, exact `review_lever` phrasing, measurable consequences, explicit trade-offs, no prefixes, and exact summary syntax in `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`.
- `history/1/09_identify_potential_levers/events.jsonl` contains only a `run_single_plan_start` for `20250321_silo`; there is no `outputs.jsonl`, so I excluded Run 09 from content conclusions.
- `history/1/10_identify_potential_levers/events.jsonl` and `history/1/10_identify_potential_levers/outputs.jsonl` show a `ReadTimeout` for `20260311_parasomnia_research_unit`.
- `history/1/11_identify_potential_levers/events.jsonl`, `history/1/12_identify_potential_levers/events.jsonl`, `history/1/13_identify_potential_levers/events.jsonl`, `history/1/14_identify_potential_levers/events.jsonl`, `history/1/15_identify_potential_levers/events.jsonl`, and `history/1/16_identify_potential_levers/events.jsonl` all contain `AuthenticationError` entries; none of these files show `ValidationError`.
- `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats the same five lever names three times; this is the clearest baseline duplicate-pattern artifact.
- `history/1/14_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` shows the strongest upgrade over that baseline duplicate pattern: 17 distinct names with domain-specific framing.
- `history/1/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows exact review formatting paired with shallow consequences (`Ecosystem Design`, `Governance Structure`, etc.), illustrating that the prompt can be obeyed mechanically without producing richer leverage.
- `history/1/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows a more useful consequence style: `Reduce material costs by 15%` plus a real trade-off sentence.
- `history/1/12_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` contains literal bracket placeholders in six review fields, despite the prompt’s placeholder prohibition.
- `history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` shows label-style options such as `Imperial Oversight: ...`, `Decentralized Council: ...`, and `Hybrid AI-Human Governance: ...`.
- `history/1/16_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` shows the extreme verbosity failure mode: long lever names, paragraph-scale consequences, and expanded reviews.
- `baseline/train/20250321_silo/002-9-potential_levers_raw.json` and `history/1/14_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` both show that the `summary` field remains semantically decent but misses the exact requested prefix in most runs.

## Prompt Hypotheses

- **H1** — Replace the prose `review_lever` instruction with a mini-grammar plus one valid and two invalid examples. Evidence: most runs miss the exact review string even when semantically close (`history/1/11_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `history/1/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `history/1/15_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`). Predicted effect: higher exact review compliance without sacrificing consequence quality.
- **H2** — Add one explicit valid `summary` example and explicitly forbid `Missing dimension:` and `Lever 5` shorthand. Evidence: only Run 12 partially learns the target summary format (`9 / 12` exact); baseline and all other runs are near-zero. Predicted effect: summary compliance should rise materially, especially for models already close to the target.
- **H3** — Add one compact gold consequence example that includes arrows, a number, and an explicit trade-off in under ~300 characters. Evidence: Run 11 keeps good numbers/trade-offs but drops arrows; Run 14 keeps brevity but often omits explicit trade-off phrasing; Run 16 explodes in length. Predicted effect: better consistency on all three consequence constraints at once.
- **H4** — Add a direct ban on `Title: description` option formatting and on bracket placeholders inside `review_lever`. Evidence: Run 13 has `15` label-like options; Run 12 leaks six bracket placeholders in one plan. Predicted effect: cleaner option phrasing and fewer obvious template leaks.
- **H5** — Add a domain-specific naming reminder immediately before generation, with one example contrasting generic vs project-native lever names. Evidence: Run 10 still emits many generic 1–2 word names (`36 / 75`), while Runs 12/14/16 nearly eliminate that pattern. Predicted effect: less generic naming on weaker/local models without affecting stronger models much.

## Questions For Later Synthesis

- Should the next prompt iteration optimize for **Run 14-style balance** or **Run 12-style exact summary compliance**?
- Are review/summary exact-string requirements important enough to keep in-prompt, or would a post-processor be higher leverage?
- How much of the duplicate-name reduction in Runs 11 and 16 is prompt-driven versus reduced raw response counts (`10` and `11` responses instead of baseline `15`)?
- Should `Title: description` option formatting be treated as a hard violation in future metrics?
- Is the large merged lever count in `002-10-potential_levers.json` expected downstream, or should the merge step trim more aggressively?

## Reflect

- The strict regex metrics are intentionally harsh. Some “violations” are near-misses rather than semantic failures. Example: Run 11 often uses `Immediate:` / `Systemic:` / `Strategic:` correctly but with periods instead of arrows.
- That said, the exact-template failures are still real if downstream evaluation expects literal conformance. The prompt is not strong enough yet to guarantee literal review/summary syntax across models.
- The authentication failures in Runs 11–16 are not prompt problems, but they do make those run directories operationally messy. I treated the successful outputs as analyzable and the auth failures as separate reliability noise.
- I do **not** see evidence for the earlier schema-level `max_length` failure mode in this batch. This analysis pass should focus on prompt adherence, verbosity, and post-processing opportunities instead.

## Potential Code Changes

- **C1** — Add a post-generation canonicalizer for `review_lever` that rewrites semantically correct near-misses into `Controls X vs. Y. Weakness: The options fail to consider Z.` Evidence: Runs 11, 14, 15, and 16 frequently contain recoverable near-misses rather than unusable reviews. Predicted effect: large jump in exact review compliance without another model call.
- **C2** — Add a consequence formatter that normalizes `Immediate/Systemic/Strategic` separators and trims overlong segments. Evidence: Run 11 often has all three labels but no arrows; Run 16 contains valid substance but bloated paragraphs. Predicted effect: better structural compliance and lower downstream parsing risk.
- **C3** — Add a placeholder/label detector after generation to reject or repair bracketed review text and `Title: description` options. Evidence: Run 12 leaks `[production scale]` / `[creative autonomy]`; Run 13 emits many label-style options. Predicted effect: catches the most obvious style failures automatically.
- **C4** — Separate “transient infra failure” entries from final content results in run logging. Evidence: Runs 11–16 mix authentication failures and later successes in the same history directories, which complicates analysis. Predicted effect: cleaner experiment metrics and fewer false interpretations of prompt quality.

## Summary

Prompt 3 is a real improvement over baseline for **uniqueness**, **domain specificity**, and **measurable consequence writing**, especially in Runs 11, 12, 14, and 15. Its weak point is still **literal protocol control**: reviews and summaries often stay semantically close while missing the exact required syntax. My main recommendation for synthesis is to treat **Run 14 as the best content-quality anchor**, **Run 12 as the best summary-compliance clue**, and to strongly consider **code-side normalization** for review/consequence formatting instead of trying to force every model to hit exact strings through prompt text alone.
