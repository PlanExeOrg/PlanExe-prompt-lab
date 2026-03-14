# Insight Codex

## Negative Things

- `03_identify_potential_levers` (`openrouter-z-ai-glm-4-7-flash`) failed on all 5 train plans by returning schema-like content instead of the required JSON payload. This looks like poor instruction following for structured output.
- `06_identify_potential_levers` (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) failed on all 5 train plans with empty/non-extractable JSON output. The model appears unreliable for this step.
- `04_identify_potential_levers` (`openrouter-stepfun-step-3-5-flash`) was only partially usable. It produced invalid JSON on 2 of 5 plans.
- `08_identify_potential_levers` failed before execution because the model was missing from config, so it contributes no analytical value.
- The registered prompt says "generate EXACTLY 5 levers per response", but every final artifact being compared contains 15 levers. That creates ambiguity about the true unit of evaluation: one call, one batch, or the final merged file.
- `00_identify_potential_levers` often looks generic and repetitive. It repeats lever names inside a single file and sometimes produces placeholder-like review text such as `Controls Trade-off between [Scalability] vs. [Cost Efficiency].`
- `07_identify_potential_levers` is structurally valid but low quality. It repeats the same lever names heavily, especially on `20260308_sovereign_identity`, where 15 levers collapse into only 5 unique names.
- `01_identify_potential_levers` is better than `00` and `07`, but it still repeats names and often sounds like a prompt template filled in rather than grounded analysis.
- Several weaker outputs regurgitate the prompt's review structure too literally: `Controls X vs. Y. Weakness: ...` without adding much domain-specific substance. The format is followed, but the content is shallow.
- Baseline and weaker history runs often produce levers that are too generic to be strategically useful, such as broad labels like "Resource Allocation Strategy" or "Coalition Building Strategy" without enough project-specific distinction.
- `02_identify_potential_levers` is cleaner than I first credited it for on exact-name uniqueness, but it still shows a robotic consequence pattern. On `20250321_silo`, 11 of 15 consequences reuse the phrase `25% faster scaling`, which makes the output feel mechanically optimized rather than analytically varied.
- `09_identify_potential_levers` is the strongest run, but it overshoots in verbosity. Some reviews become mini-essays, which may make downstream comparison or scoring harder.
- Some analysis artifacts have operational caveats that can mislead later scoring if ignored. `outputs.jsonl` is append-only across retries, and `usage_metrics.jsonl` is not schema-consistent across all runs.

## Positive Things

- `02_identify_potential_levers` (`openai-gpt-5-nano`) is the cleanest structured run. It produced 15 unique lever names on all 5 train plans with no duplicate names inside a file.
- `09_identify_potential_levers` (`anthropic-claude-haiku-4-5-pinned`) is the strongest content run. It consistently surfaces concrete institutional, operational, and long-horizon failure modes that are more specific than baseline.
- `04_identify_potential_levers` (`openrouter-stepfun-step-3-5-flash`) deserves more credit than I gave it initially. It only succeeds on 3 of 5 plans, but the successful outputs are unusually vivid and project-grounded.
- `05_identify_potential_levers` (`openrouter-qwen3-30b-a3b`) is solid and reliable. It is not as strong as `09`, but it is materially better than the weaker generic runs.
- The best runs generate insights that are not obvious from the prompt alone. `09` repeatedly introduces second-order risks such as governance handoff failure, generational knowledge decay, recruitment legitimacy, contingency-trigger ambiguity, and coalition capture.
- `09` improves on baseline by making the weaknesses more decision-relevant. Instead of generic "consider X" phrasing, it often explains why each option could fail under realistic political, regulatory, or operational pressure.
- `02` shows that the current prompt can work well when the model is disciplined. That suggests the prompt is not fundamentally broken; model choice matters a lot.
- Compared with baseline, the better runs have fewer duplicate lever names and better differentiation between levers, especially on `20260308_sovereign_identity` and `20250321_silo`.
- Even when the review template is preserved, the stronger runs use it productively by attaching concrete stakes, constraints, and failure mechanisms.
- `09` appears to be the first run that consistently pushes the analysis from "what are the strategic options?" toward "what breaks each option in the real world?" That is a real qualitative shift, not just a longer answer.
- `02` and `09` complement each other: `02` is the strongest signal for structural discipline, while `09` is the strongest signal for strategic depth.
- `04` shows that partial-success runs can still matter analytically. A model with brittle structured-output compliance can nevertheless surface some of the best individual levers, which suggests quality ranking should not only look at plan-level pass/fail counts.

## Comparison

Mixed overall, but the best responses are better than `baseline/train`. The low-end runs (`03`, `04`, `06`, `07`, and parts of `00`/`01`) are setbacks because they are invalid, repetitive, or generic. The top-end runs, especially `09` and then `02`, are a meaningful improvement over baseline: they are more specific, more differentiated, and more strategically useful. So the net result is not a clean across-the-board improvement, but it does show a clear path to major improvement when the model follows the prompt well.

More specifically, baseline is not a very high bar. Baseline itself repeats lever names heavily on some plans, including `20260308_sovereign_identity`, where the 15-lever file collapses to only 5 unique names. The strongest new runs are therefore not just "slightly cleaner"; they actually overcome a known weakness in the baseline outputs.

The biggest trade-off among the better runs is not simply quality versus failure rate. It is structure versus richness. `02` is highly regular and evaluator-friendly. `09` is more insightful but much longer, with average review length on `20250321_silo` around 349 characters versus roughly 126-144 for `00`, `01`, `02`, and `05`.

I would now rank the meaningful contenders this way:

- Best overall content: `09`
- Best structural regularity: `02`
- Best high-upside partial run: `04`
- Best reliable middle tier: `05`

## Quantitative Metrics

### Exact Unique Lever Names

| Run | Silo Unique/15 | Sovereign Identity Unique/15 |
|-----|---------------:|-----------------------------:|
| Baseline | 11 | 5 |
| 00 | 14 | 13 |
| 01 | 14 | 11 |
| 02 | 15 | 15 |
| 04 | 15 | N/A |
| 05 | 14 | 15 |
| 07 | 12 | 5 |
| 09 | 15 | 15 |

This metric is useful but incomplete. A run can have perfect exact-name uniqueness and still feel repetitive in consequences or concept coverage. That caveat matters especially for `02`.

### Average Review Length (Characters)

| Run | Silo | Sovereign Identity |
|-----|-----:|-------------------:|
| Baseline | 147.2 | 146.6 |
| 00 | 125.9 | 129.9 |
| 01 | 124.9 | 141.7 |
| 02 | 142.5 | 166.2 |
| 04 | 219.4 | N/A |
| 05 | 144.0 | 142.8 |
| 07 | 135.7 | 123.6 |
| 09 | 349.2 | 482.5 |

`09` is dramatically longer than the rest, but the extra length is often substantive rather than empty padding.

### Option Count Violations

| Run | Plan | Violations |
|-----|------|-----------:|
| 00 | `20260308_sovereign_identity` | 4 |
| 09 | `20260308_sovereign_identity` | 1 |

Run `00` has 4 levers with fewer than 3 options on `sovereign_identity`. Run `09` has a single 4-option lever with what looks like schema-noise in the extra option. The other checked runs were structurally clean on this constraint.

## Evidence Notes

- Best structure: `02_identify_potential_levers` produced 15 unique lever names on all 5 train plans.
- Worst repetition among valid outputs: `07_identify_potential_levers` on `20260308_sovereign_identity` produced only 5 unique names across 15 levers.
- Clear prompt leakage example: `00_identify_potential_levers` includes review text like `Controls Trade-off between [Scalability] vs. [Cost Efficiency].`
- Clear depth improvement example: `09_identify_potential_levers` on `20250321_silo` and `20260308_sovereign_identity` repeatedly names institutional, generational, and governance-failure mechanisms absent from baseline.
- Clear structured-but-robotic example: `02_identify_potential_levers` on `20250321_silo` reuses `25% faster scaling` in 11 of 15 consequences fields.
- Clear high-upside partial example: `04_identify_potential_levers` produces stronger review depth on successful plans than baseline, `00`, `01`, `05`, or `07`.

## Questions For Later Synthesis

- What is the true target artifact: each 5-lever generation or the final 15-lever merged file?
- Should duplicate lever names within one final artifact be treated as a hard failure or a soft penalty?
- Is verbosity helping quality, or is `09` partially winning because it writes more words per review?
- Are we optimizing for one target production model, or for robustness across multiple models?
- Does higher-quality output at `identify_potential_levers` lead to measurably better downstream pipeline artifacts?
- Which failure modes are unacceptable regardless of content quality: invalid JSON, empty output, generic labels, prompt-template leakage, or duplicated strategic dimensions?
- Should the later evaluator reward strong criticism of each option, or reward concise and scan-friendly output that is easier for downstream steps to consume?

## Reflect

- **H1:** Add an explicit uniqueness constraint across the full output, not just per lever. Evidence: baseline and `07` collapse to 5 unique names on `sovereign_identity`, while stronger runs benefit from better separation of strategic dimensions.
- **H2:** Require every lever to anchor to at least one project-specific noun, institution, constraint, or measurable factor from the source material. Evidence: the strongest lever names in `04` and `09` are project-grounded; the weakest in baseline, `00`, and `07` are generic abstractions.
- **H3:** Add an anti-template leakage rule for reviews. Evidence: `00` includes bracket placeholders and copied prompt-shape language instead of real critique.
- **H4:** Set a target length band for `review` and `consequences`. Evidence: `07` and `00` are often too short to say anything useful; `09` is rich but may be too long for downstream scoring or synthesis.
- **H5:** Simplify or separate the formatting instructions from the strategic-quality instructions. Evidence: weak models often follow the shell of the schema while missing the substance.
- **H6:** Explicitly demand one non-obvious lever that challenges the default project framing, not just one unconventional option within a lever. Evidence: the biggest gap between `09` and the weaker runs is hidden-assumption pressure, not just more radical option C phrasing.
- **H7:** Make the output contract explicit at the artifact level, not only at the single-response level. Evidence: the system prompt says 5 levers per response, but the stored artifacts being evaluated contain 15.
- **H8:** Add one instruction that each review must mention a failure mechanism not already named in the lever title. Evidence: several weaker runs restate the same tension without introducing any genuinely new concern.
- **H9:** Add a specific anti-robotic-language constraint for measurable consequences. Evidence: `02` shows that a model can satisfy the "include measurable outcomes" rule by repeating the same metric template (`25% faster scaling`) across many levers.

## Potential Code Changes

- **C1:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, fix the first-call prompt duplication. Evidence: the code currently preloads the main `user_prompt` and then appends the same prompt again before the first call.
- **C2:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, replace the bare `"more"` continuation with an anti-repetition continuation prompt. Evidence: the current multi-call setup gives the model no explicit instruction to avoid overlap with prior batches.
- **C3:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, add post-response validation for exactly 5 levers, exactly 3 options per lever, no duplicate names, and basic review/consequence quality checks. Evidence: `00` and `09` both show option-count violations despite being treated as usable outputs.
- **C4:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, move duplicate detection into the main execution path rather than relying on downstream cleanup. Evidence: cross-call duplication is one of the most common quality failures in the dataset.
- **C5:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, consider a generation pass followed by a critique/repair pass. Evidence: some models can produce interesting levers but fail when too many formatting and critique requirements are bundled into one structured call.
- **C6:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, test whether appending `raw.model_dump()` as the assistant turn is causing drift across the multi-turn sequence. A cleaner continuation representation may reduce repetition.
- **C7:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, add runner-side quality gates after generation. Evidence: structurally valid but weak outputs are currently recorded as `ok`, which hides important differences between syntactic success and analytical quality.
- **C8:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, emit richer per-plan summary stats such as duplicate-name count, option-count violations, placeholder leakage count, and average review length. Evidence: later analysis currently has to recompute these metrics by hand from the artifacts.
- **C9:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, write a normalized final summary per run in addition to append-only `outputs.jsonl`. Evidence: resume/retry behavior makes naïve downstream scoring fragile.
- **C10:** In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, preflight-check model availability and structured-output capability before launching a full run. Evidence: `08` failed wholesale on configuration, and some models fail in recognizable structured-output ways that could be screened earlier.

## Summary

This history slice is primarily a model comparison over the same registered prompt, and it shows a wide spread in quality. Several models fail outright or produce shallow, repetitive, prompt-shaped output. Baseline itself is only moderate quality and suffers from repeated lever names and generic framing, so it is beatable. The strongest evidence comes from `09` as the best overall content run, `02` as the cleanest structural run, and `04` as the best high-upside partial-success run. The main opportunities are a mix of prompt and code changes: enforce uniqueness, force stronger source-grounding, block template leakage, clarify the true artifact contract, suppress robotic metric reuse, and fix the multi-call generation path so it does not amplify duplication.
