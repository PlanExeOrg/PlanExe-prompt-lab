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
- `09_identify_potential_levers` is the strongest run, but it overshoots in verbosity. Some reviews become mini-essays, which may make downstream comparison or scoring harder.
- Some analysis artifacts have operational caveats that can mislead later scoring if ignored. `outputs.jsonl` is append-only across retries, and `usage_metrics.jsonl` is not schema-consistent across all runs.

## Positive Things

- `02_identify_potential_levers` (`openai-gpt-5-nano`) is the cleanest structured run. It produced 15 unique lever names on all 5 train plans with no duplicate names inside a file.
- `09_identify_potential_levers` (`anthropic-claude-haiku-4-5-pinned`) is the strongest content run. It consistently surfaces concrete institutional, operational, and long-horizon failure modes that are more specific than baseline.
- `05_identify_potential_levers` (`openrouter-qwen3-30b-a3b`) is solid and reliable. It is not as strong as `09`, but it is materially better than the weaker generic runs.
- The best runs generate insights that are not obvious from the prompt alone. `09` repeatedly introduces second-order risks such as governance handoff failure, generational knowledge decay, recruitment legitimacy, contingency-trigger ambiguity, and coalition capture.
- `09` improves on baseline by making the weaknesses more decision-relevant. Instead of generic "consider X" phrasing, it often explains why each option could fail under realistic political, regulatory, or operational pressure.
- `02` shows that the current prompt can work well when the model is disciplined. That suggests the prompt is not fundamentally broken; model choice matters a lot.
- Compared with baseline, the better runs have fewer duplicate lever names and better differentiation between levers, especially on `20260308_sovereign_identity` and `20250321_silo`.
- Even when the review template is preserved, the stronger runs use it productively by attaching concrete stakes, constraints, and failure mechanisms.
- `09` appears to be the first run that consistently pushes the analysis from "what are the strategic options?" toward "what breaks each option in the real world?" That is a real qualitative shift, not just a longer answer.
- `02` and `09` complement each other: `02` is the strongest signal for structural discipline, while `09` is the strongest signal for strategic depth.

## Comparison

Mixed overall, but the best responses are better than `baseline/train`. The low-end runs (`03`, `04`, `06`, `07`, and parts of `00`/`01`) are setbacks because they are invalid, repetitive, or generic. The top-end runs, especially `09` and then `02`, are a meaningful improvement over baseline: they are more specific, more differentiated, and more strategically useful. So the net result is not a clean across-the-board improvement, but it does show a clear path to major improvement when the model follows the prompt well.

More specifically, baseline is not a very high bar. Baseline itself repeats lever names heavily on some plans, including `20260308_sovereign_identity`, where the 15-lever file collapses to only 5 unique names. The strongest new runs are therefore not just "slightly cleaner"; they actually overcome a known weakness in the baseline outputs.

The biggest trade-off among the better runs is not simply quality versus failure rate. It is structure versus richness. `02` is highly regular and evaluator-friendly. `09` is more insightful but much longer, with average review length on `20250321_silo` around 349 characters versus roughly 126-144 for `00`, `01`, `02`, and `05`.

## Evidence Notes

- Best structure: `02_identify_potential_levers` produced 15 unique lever names on all 5 train plans.
- Worst repetition among valid outputs: `07_identify_potential_levers` on `20260308_sovereign_identity` produced only 5 unique names across 15 levers.
- Clear prompt leakage example: `00_identify_potential_levers` includes review text like `Controls Trade-off between [Scalability] vs. [Cost Efficiency].`
- Clear depth improvement example: `09_identify_potential_levers` on `20250321_silo` and `20260308_sovereign_identity` repeatedly names institutional, generational, and governance-failure mechanisms absent from baseline.

## Questions For Later Synthesis

- What is the true target artifact: each 5-lever generation or the final 15-lever merged file?
- Should duplicate lever names within one final artifact be treated as a hard failure or a soft penalty?
- Is verbosity helping quality, or is `09` partially winning because it writes more words per review?
- Are we optimizing for one target production model, or for robustness across multiple models?
- Does higher-quality output at `identify_potential_levers` lead to measurably better downstream pipeline artifacts?
- Which failure modes are unacceptable regardless of content quality: invalid JSON, empty output, generic labels, prompt-template leakage, or duplicated strategic dimensions?
- Should the later evaluator reward strong criticism of each option, or reward concise and scan-friendly output that is easier for downstream steps to consume?

## Reflect

- Hypothesis 1: add an explicit uniqueness constraint across the full output, not just per lever. Example intent: "All lever names must be distinct within the response and must not restate the same strategic dimension with minor wording changes." This would directly target the repetition seen in baseline, `00`, `01`, `05`, and especially `07`.
- Hypothesis 2: require every lever to anchor to at least one project-specific noun, institution, constraint, or measurable factor from the source material. This should reduce generic filler such as "Resource Allocation Strategy" and push outputs toward the stronger style seen in `09`.
- Hypothesis 3: add an anti-template leakage rule for reviews. Example intent: "Do not use square-bracket placeholders, do not restate the instruction text, and do not produce generic trade-offs without domain grounding." This is aimed at outputs like `00` where the prompt shape leaks into the answer.
- Hypothesis 4: set a target length band for `review` and `consequences`, for example concise but specific. The weaker models are too short and generic; `09` is sometimes too long. A tighter length target could preserve specificity while improving consistency for downstream evaluation.
- Hypothesis 5: simplify or separate the formatting instructions from the strategic-quality instructions. Some model failures look like instruction overload for structured output. A shorter formatting contract plus a smaller number of high-value quality rules may improve compliance on weaker models.
- Hypothesis 6: explicitly demand one non-obvious lever that challenges the default project framing, not just one unconventional option within a lever. The best `09` outputs often win because they question hidden assumptions, not merely because they offer more radical option C variants.
- Hypothesis 7: make the output contract explicit at the artifact level, not only at the single-response level. If the final stored object is expected to contain 15 levers assembled from multiple calls, the prompting and evaluation setup should say so clearly.
- Hypothesis 8: add one instruction that each review must mention a failure mechanism that is not already named in the lever title. That would reduce tautological criticism and force more analytical distance.

## Potential Code Changes

- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, the first loop iteration appears to send the main `user_prompt` twice: once in the initial `chat_message_list` and again as the first item in `user_prompt_list`. That duplication may blur the intended conversation structure and could contribute to repetitive or over-templated output. I would change the multi-turn sequence so the first call uses the original prompt once, then follow-up turns use explicit continuation instructions rather than re-sending the same prompt.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, the follow-up prompt is currently just `"more"`. That is too underspecified for a task where uniqueness and breadth matter. A stronger continuation prompt would say something like: generate 5 additional levers that are materially distinct from previous levers, avoid repeating strategic dimensions, and deepen project-specificity. This is one of the most plausible code-level improvements for reducing duplicates.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, the Pydantic schema validates types but not many of the actual quality constraints. The code does not enforce exactly 5 levers, exactly 3 options, distinct lever names, or review formatting. Adding post-response validators or a repair/retry pass would convert some currently "ok" but weak outputs into retries instead of silently accepting them.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, deduplication is externalized to another script and is not part of the main execution path. Since duplicate lever names are a recurring observed failure mode, I would consider integrating deduplication or at least duplicate detection directly into `execute()` before persisting outputs.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, the system prompt is trying to do too much at once: formatting, style, strategy, review requirements, and anti-patterns. A code-level improvement could be to split this into a generation pass and a critique/repair pass. The first pass generates candidate levers; the second pass checks for overlap, genericity, placeholder leakage, and weak reviews.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, the assistant turn is appended using `result["chat_response"].raw.model_dump()`. Even if that works, it means the next turn is conditioned on a serialized structured object rather than a controlled natural-language continuation state. I would test whether a cleaner assistant continuation message, or no assistant echo at all, reduces drift and repetition across the three response batches.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, `run_single_plan()` treats any structurally successful generation as `ok`. That means outputs with repeated lever names, generic reviews, or prompt leakage all count as successes. I would add a quality gate after generation to compute simple metrics such as duplicate-name count, placeholder-pattern count, average review length, and option-count compliance. Runs failing these checks should be flagged or retried.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, the runner does not currently separate "valid JSON" from "high-quality structured output." Adding richer per-plan summary stats would make prompt optimization much more trustworthy, because it would reveal when a model is only winning on syntax rather than on strategic usefulness.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, `outputs.jsonl` is append-only across retries and resumes. That is operationally fine, but it complicates later analysis and may distort simple scoring scripts. A code-level improvement would be to emit a normalized final summary file per run with the last status per plan plus derived quality metrics.
- In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py`, model availability is not preflight-checked before processing all plans, which is why `08` could fail wholesale on configuration alone. Adding an upfront model resolution and structured-output capability check would avoid wasting runs on models that cannot execute the task cleanly.

## Summary

This history slice is primarily a model comparison over the same registered prompt, and it shows a wide spread in quality. Several models fail outright or produce shallow, repetitive, prompt-shaped output. Baseline itself is only moderate quality and suffers from repeated lever names and generic framing, so it is beatable. The strongest evidence comes from `09`, with `02` as the cleanest structured alternative: both show that the step can produce materially better strategic analysis than baseline when the model is capable and compliant. The main prompt-level opportunities are to enforce uniqueness, force stronger source-grounding, block template leakage, clarify the true artifact contract, and tune verbosity so the output stays specific without turning into long essays.
