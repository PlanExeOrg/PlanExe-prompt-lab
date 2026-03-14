# Insight Codex

## Rankings

- **Tier A:** Run `12` (`claude-haiku-4.5`) and run `10` (`gpt-5-nano`). These are the only fully successful runs that stay close to the prompt contract on most files. Run `12` is cleaner structurally; run `10` is closer to baseline length.
- **Tier B:** Run `14` (`qwen3-30b-a3b`), run `15` (`gpt-4o-mini`), and run `13` (`gpt-oss-20b`). They produce usable material, but each has a meaningful contract or reliability caveat.
- **Tier C:** Run `16` (`llama3.1`). It completes all plans, but quality control is weak: extra levers, prefixed options, bracket placeholders, and widespread loss of measurable outcomes.
- **Tier D:** Run `09` (`stepfun-step-3.5-flash`) and run `11` (`nemotron-3-nano-30b`). These are operational failures rather than content comparisons.

## Negative Things

- Two runs produced no usable outputs at all. Run `09` failed all five plans because the configured model name was missing from the selected config, as shown in `history/0/09_identify_potential_levers/outputs.jsonl:1` and repeated through `:5`. Run `11` failed all five plans with `Could not extract json string from output` in `history/0/11_identify_potential_levers/outputs.jsonl:1` through `:5`.
- Run `13` is only partially usable: `20260311_parasomnia_research_unit` failed because the model emitted a wrapped object with `strategic_rationale` and `levers`, then truncated mid-string, so extraction failed in `history/0/13_identify_potential_levers/outputs.jsonl:4`.
- The prompt says each response must contain exactly 5 levers and each lever exactly 3 options (`prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:3`-`:5`), but run `10` still yields a malformed merged file with **16** items for `20250329_gta_game`. The last lever is split into a 2-option item plus a separate 1-option “Radical Option” item in `history/0/10_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:157`-`:173`.
- The prompt requires the literal consequence chain `Immediate: ... → Systemic: ... → Strategic: ...` (`prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:8`-`:11`), but run `14` and run `15` frequently omit those exact labels. Example: run `14` opens with `Immediate reliance on conventional concrete → Systemic 25% faster scaling ...` in `history/0/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`, and run `15` opens with `Choosing a local director enhances cultural resonance → ...` in `history/0/15_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5`.
- Run `16` breaks multiple prompt prohibitions at once. The prompt bans option prefixes and bracket placeholders (`prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:16`, `:31`-`:36`), yet `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:7`-`:9` uses `Option 1:` / `Option 2:` / `Option 3:`, and `history/0/16_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:119`-`:163` contains bracket placeholders such as `Controls [Financial Risks] vs. [Creative Freedom]`.
- Run `16` also over-produces: `history/0/16_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` contains **20** levers, not 15. The last five items are additional generic levers such as `Social Dynamics Strategy` and `Economic Development Strategy`, visible after the fifteenth item.
- Run `12` is structurally strong but extremely verbose. Its average consequence length is `657.4` characters per lever versus the baseline average `279.5`, average option length is `315.4` versus `150.2`, and average review length is `412.4` versus `152.3`. The first silo entry already shows the pattern in `history/0/12_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`-`:11`.

## Positive Things

- Runs `10` and `12` both achieve full `5/5` plan coverage and average **15 unique lever names per file**, materially better than the baseline training average of `10.6` unique names per file.
- Runs `10` and `12` also show **zero exact lever-name overlap** with the baseline files across all five plans, so they are not merely copying the training artifacts.
- Run `10` is the best balance of quality and baseline-like brevity: consequence, option, and review lengths (`271.6`, `146.7`, `161.9`) stay close to baseline (`279.5`, `150.2`, `152.3`) while keeping zero average missing-chain and missing-number violations.
- Run `12` is the cleanest high-compliance run on structure. Unlike the baseline average, it has zero option-count violations, zero prefix leakage, zero placeholder leakage, and zero missing chain labels.
- Even the weaker successful runs generally improve on one baseline weakness: the baseline training set itself has substantial duplicate naming across merged turns. For example, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json` repeats the same five names three times (`Technical Feasibility Strategy`, `Policy Advocacy Strategy`, `Coalition Building Strategy`, `Procurement Influence Strategy`, `EU Standards Engagement Strategy`) at lines `4`, `15`, `26`, `37`, `48`, then again at `59`-`103`, and again at `114`-`158`.
- Run `15` is operationally attractive even though content quality is mixed: it is the fastest fully successful run at `49.1` seconds average per plan according to `history/0/15_identify_potential_levers/outputs.jsonl`.

## Comparison

- **Against baseline:** baseline files are moderately sized and always parse, but they are not perfect gold outputs. They average `4.4` duplicate lever names per file and still miss the exact `Immediate:/Systemic:/Strategic:` pattern in some plans. That matters because some history runs beat baseline on uniqueness without necessarily beating it on overall usefulness.
- **Run `10` vs baseline:** run `10` is the closest overall match to baseline density while improving uniqueness and measurable consequence coverage. Its main defect is not genericity; it is malformed counting in one file (`20250329_gta_game`).
- **Run `12` vs baseline:** run `12` is richer and more differentiated than baseline, but it overshoots the likely target length by roughly `2.3x` on consequences and `2.7x` on reviews. This may help ideation but likely hurts downstream readability and token efficiency.
- **Run `14` and run `15` vs baseline:** both are concise and fast, but they drift away from the exact textual contract the prompt asks for. The content often feels like “good strategic prose” rather than “prompt-compliant serialized output.”
- **Run `16` vs baseline:** run `16` has good novelty and sometimes strong topical relevance, but it is materially less controlled than baseline. Prefix leakage, bracket placeholders, missing measurable numbers, and total-lever overproduction all point to a model that needs either stronger runtime validation or a stricter prompt scaffold.
- **Reliability split:** the key divide is no longer just “good model vs bad model”; it is “models that can stay inside a rigid serialization contract” versus “models that produce plausible strategic text but break the container.” Runs `09`, `11`, `13`, and `16` each fail in a different way.

## Quantitative Metrics

I treated each artifact as the final merged lever array because the stored outputs are JSON arrays, not wrapper objects.

### Reliability

| Run | Model | OK plans | Error plans | Avg duration seconds |
|---|---|---:|---:|---:|
| Run 09 | stepfun-step-3.5-flash | 0 | 5 | 0.0 |
| Run 10 | gpt-5-nano | 5 | 0 | 284.3 |
| Run 11 | nemotron-3-nano-30b | 0 | 5 | 134.4 |
| Run 12 | claude-haiku-4.5 | 5 | 0 | 109.3 |
| Run 13 | gpt-oss-20b | 4 | 1 | 176.1 |
| Run 14 | qwen3-30b-a3b | 5 | 0 | 121.0 |
| Run 15 | gpt-4o-mini | 5 | 0 | 49.1 |
| Run 16 | llama3.1 | 5 | 0 | 94.2 |

### Uniqueness And Length

| Row | Coverage | Avg levers/file | Avg unique names/file | Avg consequence chars | Avg option chars | Avg review chars |
|---|---:|---:|---:|---:|---:|---:|
| Baseline train | 5/5 | 15 | 10.6 | 279.5 | 150.2 | 152.3 |
| Run 09 (stepfun-step-3.5-flash) | 0/5 | — | — | — | — | — |
| Run 10 (gpt-5-nano) | 5/5 | 15.2 | 15.2 | 271.6 | 146.7 | 161.9 |
| Run 11 (nemotron-3-nano-30b) | 0/5 | — | — | — | — | — |
| Run 12 (claude-haiku-4.5) | 5/5 | 15 | 15 | 657.4 | 315.4 | 412.4 |
| Run 13 (gpt-oss-20b) | 4/5 | 15 | 14.2 | 217.2 | 94.8 | 133.6 |
| Run 14 (qwen3-30b-a3b) | 5/5 | 15 | 14 | 196.6 | 61.2 | 138.1 |
| Run 15 (gpt-4o-mini) | 5/5 | 15 | 11.2 | 209.3 | 109.4 | 141.4 |
| Run 16 (llama3.1) | 5/5 | 16 | 14.8 | 176.5 | 86.5 | 143.8 |

### Constraint Violations And Template Leakage

| Row | Option-count viol. | Prefix viol. | Placeholder viol. | Missing chain labels | Missing measurable number | Review missing trade-off | Review missing weakness |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline train | 0 | 0 | 0 | 1 | 4.2 | 0 | 0 |
| Run 09 (stepfun-step-3.5-flash) | — | — | — | — | — | — | — |
| Run 10 (gpt-5-nano) | 0.4 | 0 | 0 | 0 | 0 | 0 | 0 |
| Run 11 (nemotron-3-nano-30b) | — | — | — | — | — | — | — |
| Run 12 (claude-haiku-4.5) | 0 | 0 | 0 | 0 | 2.4 | 0 | 0 |
| Run 13 (gpt-oss-20b) | 0.2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Run 14 (qwen3-30b-a3b) | 0 | 0 | 0 | 3 | 0.4 | 0 | 0 |
| Run 15 (gpt-4o-mini) | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| Run 16 (llama3.1) | 0.4 | 1 | 1 | 0 | 15.6 | 0.8 | 1.2 |

### Cross-Call Duplication Proxy

| Row | Avg duplicate-name excess/file | Avg duplicate-consequence excess/file |
|---|---:|---:|
| Baseline train | 4.4 | 0 |
| Run 09 (stepfun-step-3.5-flash) | — | — |
| Run 10 (gpt-5-nano) | 0 | 0.2 |
| Run 11 (nemotron-3-nano-30b) | — | — |
| Run 12 (claude-haiku-4.5) | 0 | 0 |
| Run 13 (gpt-oss-20b) | 0.8 | 0 |
| Run 14 (qwen3-30b-a3b) | 1 | 0 |
| Run 15 (gpt-4o-mini) | 3.8 | 0 |
| Run 16 (llama3.1) | 1.2 | 0 |

### Exact Lever-Name Overlap With Baseline

| Row | Avg shared lever names with matching baseline plan |
|---|---:|
| Run 10 (gpt-5-nano) | 0.0 |
| Run 12 (claude-haiku-4.5) | 0.0 |
| Run 13 (gpt-oss-20b) | 0.2 |
| Run 14 (qwen3-30b-a3b) | 0.6 |
| Run 15 (gpt-4o-mini) | 1.6 |
| Run 16 (llama3.1) | 0.0 |

These numbers mean:

- High uniqueness is achievable for this step; it is not inherently limited to the baseline’s repeated-name pattern.
- Structural success and content quality are partially decoupled. Run `16` is highly novel but badly controlled; run `12` is highly controlled but overly long.
- Template leakage is not a general problem across all runs; it is concentrated in run `16`.

## Evidence Notes

- The registered prompt is strong on contract rules but says nothing about **maximum field length**, **global uniqueness across all three turns**, or **top-level wrapper suppression**. See `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:3`-`:41`.
- Baseline data is useful but imperfect. The sovereign-identity baseline repeats the same five lever names three times in `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:4`-`:158`, so “matching baseline” should not be treated as the only success criterion.
- Run `10` demonstrates that the system can get close to the desired target shape, but it also shows why post-merge validation matters: one split lever creates both an extra item and wrong option counts in `history/0/10_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:157`-`:173`.
- Run `12` demonstrates that a model can satisfy most structural rules while still overspending tokens. The first silo item is coherent but already much denser than the baseline style in `history/0/12_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`-`:11`.
- Run `14` and run `15` show that “close enough prose” is not enough for this step. Their missing literal labels are easy for a validator to detect from `history/0/14_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `history/0/15_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5`.
- Run `16` shows both kinds of template leakage the prompt explicitly bans: prefixed options in `history/0/16_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:7`-`:9` and bracket placeholders in `history/0/16_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:119`, `:130`, `:141`, `:152`, and `:163`.
- The operational failures are not all the same. Run `09` is a configuration/registry problem (`history/0/09_identify_potential_levers/outputs.jsonl:1`-`:5`), while runs `11` and `13` are extraction/serialization failures (`history/0/11_identify_potential_levers/outputs.jsonl:1`-`:5`, `history/0/13_identify_potential_levers/outputs.jsonl:4`).

## Questions For Later Synthesis

- Should the optimization target prioritize **strict contract adherence** over **ideation richness**, or is some verbosity acceptable if a later step truncates or summarizes?
- Is the correct comparator for this step the baseline training data, or should the baseline be treated only as a rough style/coverage reference because it contains repeated names?
- Would a stronger prompt alone fix run `14`/`15` style drift, or do these runs show the need for hard validation plus retry?
- Should models that cannot reliably emit strict JSON for this step be excluded entirely rather than repaired downstream?
- Is the extra-lever problem in runs `10` and `16` happening inside a single turn or during merge logic after three turns? The stored artifacts only show the merged array.

## Reflect

- My main takeaway is that the current prompt is already fairly demanding, so the remaining variation is less about “more instructions” and more about **which models can obey a rigid output contract**.
- Baseline comparison is tricky here because the baseline itself contains duplicate lever names and some format drift. I therefore treat the baseline as a useful reference, not an untouchable gold standard.
- The most actionable prompt gaps are about things the current prompt does **not** explicitly constrain: global uniqueness across turns, output length bounds, and top-level JSON shape.

### Prompt Hypotheses

- **H1:** Add a global uniqueness instruction for the merged three-turn result: “Across all three responses, produce 15 total levers with distinct names; never split one lever into a separate radical-only item.” Evidence: run `10` splits one lever into two items in `history/0/10_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:157`-`:173`, and run `15` regresses toward baseline-like duplicate naming.
  - **Expected effect:** fewer duplicate names, fewer `16`/`20` lever files, and better cross-turn diversity.
- **H2:** Add explicit length targets, e.g. one sentence for `consequences` around baseline scale and concise `review`/`options` bounds. Evidence: run `12` averages `657.4` consequence chars and `412.4` review chars versus baseline `279.5` and `152.3`.
  - **Expected effect:** preserve run `12`’s structural quality while reducing token cost and truncation risk.
- **H3:** Add a short compliant mini-example that uses the exact required literals: `Immediate:`, `Systemic:`, `Strategic:`, `Controls A vs. B. Weakness: ...`, plus an explicit self-check line: “No `Option 1:` prefixes; no bracket placeholders.” Evidence: run `14`/`15` omit literal chain labels, and run `16` leaks both prefixes and bracket placeholders despite the current bans.
  - **Expected effect:** better literal compliance on weaker models without changing the conceptual task.
- **H4:** Add a top-level schema reminder such as “Return only the raw JSON array of lever objects; do not include `strategic_rationale`, `summary`, or wrapper keys.” Evidence: run `13` fails on a wrapped object in `history/0/13_identify_potential_levers/outputs.jsonl:4`.
  - **Expected effect:** fewer extraction failures from otherwise usable generations.

## Potential Code Changes

- **C1:** Add a preflight model-availability check before the batch starts, and fail or skip unsupported models immediately. Evidence: run `09` wastes all five plans on a missing model registration in `history/0/09_identify_potential_levers/outputs.jsonl:1`-`:5`.
  - **Expected effect:** eliminate zero-signal runs caused by config drift.
- **C2:** Add per-turn validation and retry before merge: exactly `5` lever objects, each with exactly `3` options, no prefixed options, no bracket placeholders, and exact consequence/review label checks. Evidence: run `10` malformed item split, run `14`/`15` chain-label drift, and run `16` prefix/placeholder leakage.
  - **Expected effect:** convert many current “successful but contract-broken” files into either compliant outputs or explicit retries.
- **C3:** Add a post-merge validator for the final file: enforce `15` total levers, optionally dedupe exact duplicate names, and reject totals like `16` or `20`. Evidence: run `10` averages `15.2` levers/file and run `16` averages `16`, including a `20`-lever silo file.
  - **Expected effect:** catch merge-stage integrity problems even when individual turns seem acceptable.
- **C4:** Strengthen structured-output parsing: if the model returns an object with a `levers` field, parse that field directly; if the JSON is truncated, surface a specific retryable error instead of treating the plan as a normal content miss. Evidence: run `13` emits a wrapper object, and run `11` repeatedly fails extraction.
  - **Expected effect:** recover some partially valid responses and make parser failures easier to diagnose.

## Summary

- The best current candidates are run `12` for compliance and run `10` for balance.
- The biggest residual problems are **runtime reliability** (`09`, `11`, `13`) and **contract enforcement** (`10`, `14`, `15`, `16`), not lack of creativity.
- The prompt already covers many quality rules, but it likely needs additions around **global uniqueness**, **brevity targets**, and **raw-array-only output**.
- The highest-leverage code opportunities are **preflight model validation**, **turn-level contract checks with retry**, and **post-merge total-count validation**.
