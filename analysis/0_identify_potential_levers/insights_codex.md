# Insights Codex

## Negative Things

- `03_identify_potential_levers` (`openrouter-z-ai-glm-4-7-flash`) failed on all 5 train plans by returning schema-like content instead of the required JSON payload. This looks like poor instruction following for structured output.
- `06_identify_potential_levers` (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) failed on all 5 train plans with empty/non-extractable JSON output. The model appears unreliable for this step.
- `04_identify_potential_levers` (`openrouter-stepfun-step-3-5-flash`) was only partially usable. It produced invalid JSON on 2 of 5 plans.
- `08_identify_potential_levers` failed before execution because the model was missing from config, so it contributes no analytical value.
- `00_identify_potential_levers` often looks generic and repetitive. It repeats lever names inside a single file and sometimes produces placeholder-like review text such as `Controls Trade-off between [Scalability] vs. [Cost Efficiency].`
- `07_identify_potential_levers` is structurally valid but low quality. It repeats the same lever names heavily, especially on `20260308_sovereign_identity`, where 15 levers collapse into only 5 unique names.
- `01_identify_potential_levers` is better than `00` and `07`, but it still repeats names and often sounds like a prompt template filled in rather than grounded analysis.
- Several weaker outputs regurgitate the prompt's review structure too literally: `Controls X vs. Y. Weakness: ...` without adding much domain-specific substance. The format is followed, but the content is shallow.
- Baseline and weaker history runs often produce levers that are too generic to be strategically useful, such as broad labels like "Resource Allocation Strategy" or "Coalition Building Strategy" without enough project-specific distinction.
- `09_identify_potential_levers` is the strongest run, but it overshoots in verbosity. Some reviews become mini-essays, which may make downstream comparison or scoring harder.

## Positive Things

- `02_identify_potential_levers` (`openai-gpt-5-nano`) is the cleanest structured run. It produced 15 unique lever names on all 5 train plans with no duplicate names inside a file.
- `09_identify_potential_levers` (`anthropic-claude-haiku-4-5-pinned`) is the strongest content run. It consistently surfaces concrete institutional, operational, and long-horizon failure modes that are more specific than baseline.
- `05_identify_potential_levers` (`openrouter-qwen3-30b-a3b`) is solid and reliable. It is not as strong as `09`, but it is materially better than the weaker generic runs.
- The best runs generate insights that are not obvious from the prompt alone. `09` repeatedly introduces second-order risks such as governance handoff failure, generational knowledge decay, recruitment legitimacy, contingency-trigger ambiguity, and coalition capture.
- `09` improves on baseline by making the weaknesses more decision-relevant. Instead of generic "consider X" phrasing, it often explains why each option could fail under realistic political, regulatory, or operational pressure.
- `02` shows that the current prompt can work well when the model is disciplined. That suggests the prompt is not fundamentally broken; model choice matters a lot.
- Compared with baseline, the better runs have fewer duplicate lever names and better differentiation between levers, especially on `20260308_sovereign_identity` and `20250321_silo`.
- Even when the review template is preserved, the stronger runs use it productively by attaching concrete stakes, constraints, and failure mechanisms.

## Comparison

Mixed overall, but the best responses are better than `baseline/train`. The low-end runs (`03`, `04`, `06`, `07`, and parts of `00`/`01`) are setbacks because they are invalid, repetitive, or generic. The top-end runs, especially `09` and then `02`, are a meaningful improvement over baseline: they are more specific, more differentiated, and more strategically useful. So the net result is not a clean across-the-board improvement, but it does show a clear path to major improvement when the model follows the prompt well.

## Reflect

- Hypothesis 1: add an explicit uniqueness constraint across the full output, not just per lever. Example intent: "All lever names must be distinct within the response and must not restate the same strategic dimension with minor wording changes." This would directly target the repetition seen in baseline, `00`, `01`, `05`, and especially `07`.
- Hypothesis 2: require every lever to anchor to at least one project-specific noun, institution, constraint, or measurable factor from the source material. This should reduce generic filler such as "Resource Allocation Strategy" and push outputs toward the stronger style seen in `09`.
- Hypothesis 3: add an anti-template leakage rule for reviews. Example intent: "Do not use square-bracket placeholders, do not restate the instruction text, and do not produce generic trade-offs without domain grounding." This is aimed at outputs like `00` where the prompt shape leaks into the answer.
- Hypothesis 4: set a target length band for `review` and `consequences`, for example concise but specific. The weaker models are too short and generic; `09` is sometimes too long. A tighter length target could preserve specificity while improving consistency for downstream evaluation.
- Hypothesis 5: simplify or separate the formatting instructions from the strategic-quality instructions. Some model failures look like instruction overload for structured output. A shorter formatting contract plus a smaller number of high-value quality rules may improve compliance on weaker models.
- Hypothesis 6: explicitly demand one non-obvious lever that challenges the default project framing, not just one unconventional option within a lever. The best `09` outputs often win because they question hidden assumptions, not merely because they offer more radical option C variants.

## Summary

This history slice is primarily a model comparison over the same registered prompt, and it shows a wide spread in quality. Several models fail outright or produce shallow, repetitive, prompt-shaped output. Baseline itself is only moderate quality and suffers from repeated lever names and generic framing, so it is beatable. The strongest evidence comes from `09`, with `02` as the cleanest structured alternative: both show that the step can produce materially better strategic analysis than baseline when the model is capable and compliant. The main prompt-level opportunities are to enforce uniqueness, force stronger source-grounding, block template leakage, and tune verbosity so the output stays specific without turning into long essays.
