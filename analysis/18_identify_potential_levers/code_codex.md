# Code Review (codex)

## Bugs Found

### B1 — The PR still embeds a bracketed review template while claiming bracket templates are forbidden
In the PR branch (`fix/simplify-lever-prompt`), `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181-193` tells the model to emit:

- `"Controls [Tension A] vs. [Tension B]. Weakness: The options fail to consider [specific factor]."`

and then, two lines later, forbids `bracket-wrapped templates`.

That is a direct prompt contradiction. It leaves an obvious copyable leakage vector in the exact field (`review_lever`) where `insight_codex.md` found the run-33 placeholder regression. The PR intent was to remove template leakage, but this example still teaches the model to copy square brackets.

### B2 — `check_review_format()` does not validate the format the PR now claims is mandatory
In the PR branch, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:85-108` only checks for substring presence of `Controls ` and `Weakness:`. It does **not** enforce:

- exact clause order,
- two-sentence structure,
- single-field formatting,
- absence of `[` / `]`, or
- a real `Controls A vs. B.` sentence boundary.

It also auto-prepends `Controls ` whenever `' vs. '` and `Weakness:` appear anywhere in the string. So malformed outputs such as `Weakness: ... Controls [A] vs. [B].` or bracket-template leakage can still pass validation.

That explains why review exact-format compliance can stay low even after the PR rewrites the instructions, and why bracket placeholders can survive into final JSON instead of being rejected.

### B3 — The step still hard-codes three full calls, which forces later-call overgeneration and quality drift
`/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:226-239` still does all of the following:

- hard-codes `total_calls = 3`,
- asks each extra call for `5 to 7 MORE levers`, and
- prepends an ever-growing blacklist of prior lever names to later calls.

Because each call can already return `5..7` levers, this guarantees late-call pressure and overgeneration (up to 21 raw levers) instead of stopping once enough unique levers exist. The insight files report that the worst quality problems are concentrated in later calls for weaker models, especially llama3.1. This control flow is a plausible code-level root cause, not just a prompt issue.

## Suspect Patterns

### S1 — The PR quietly changes post-failure control flow from `break` to `continue`
In the PR branch, `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:263-282` changes failed-call handling from “return partial results now” to “keep going with later calls”. That behavior change is not described in PR #297, which is framed as a prompt-simplification PR.

This may recover extra levers after a later-call validation failure, but it also means a degraded call shape can continue consuming tokens and generating more weak content. At minimum, it is scope creep inside a prompt-only PR and makes attribution harder during experiments.

### S2 — There is still no post-parse quality gate before raw levers are promoted into `LeverCleaned`
`/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:293-310` copies `consequences`, `options`, and `review_lever` straight into `LeverCleaned` once the very light validators pass.

Today the hard checks only cover:

- option count, and
- presence of `Controls` / `Weakness:` markers.

There is no code-level guard for:

- label-only options,
- bracket placeholders,
- unsupported percentages in options or consequences,
- marketing words, or
- formulaic headers like `Direct Effect:` / `Downstream Implication:`.

That means the PR depends almost entirely on prompt obedience for quality, which matches the remaining model-specific failures in both insight files.

### S3 — The runner derives worker count from all config files, not the active model profile
`/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:224-254` merges every `llm_config/*.json` file into one dictionary and then reads `luigi_workers` from that merged map. That is not how actual model creation works; `get_llm()` uses the selected profile with fallback logic.

So experiment parallelism and `meta.json` can reflect a different config source than the one actually used to instantiate the model. I do not see a direct line from this to the prompt-quality regressions, but it is a real configuration mismatch inside the experiment harness.

## Improvement Opportunities

### I1 — Remove bracket placeholders everywhere and make the validator reject them
Change both the prompt text and the validator in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`:

- Replace the bracketed `review_lever` example at `:181-184` with a literal example with no brackets.
- Extend `check_review_format()` at `:85-108` to enforce ordered structure and reject `[` / `]` outright.

This is the most direct fix for the run-33 placeholder leakage and the lingering review-format slippage.

### I2 — Add a language-agnostic post-parse lint for low-quality fields
Add a lightweight quality gate before constructing `LeverCleaned` in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:293-310`.

Per `prompt_optimizer/AGENTS.md`, this should stay language-agnostic. Good candidates are:

- reject option strings below a minimum character/word threshold,
- reject bracket placeholders,
- flag `%` claims unless the exact number appears in the input context,
- flag known marketing terms as telemetry or retry feedback rather than as English-only hard validation.

This directly targets the remaining issues from both insight files: llama3.1 label-only options, qwen3/haiku unsupported percentages in options, and low-frequency marketing leakage.

### I3 — Make later calls adaptive instead of always requesting `5 to 7 MORE levers`
Refactor `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:226-239` so the loop:

- stops once enough unique levers have been collected,
- requests only the remaining count, and
- caps or summarizes the prior-name blacklist instead of dumping every prior name verbatim.

This is the cleanest code-level response to the later-call degradation pattern described in `insight_claude.md`.

### I4 — Give the optimizer runner bounded transient retries and better error telemetry
In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:93-94`, the runner builds `LLMExecutor` with default retry behavior disabled. In `/Users/neoneye/git/PlanExeGroup/PlanExe/prompt_optimizer/runner.py:130-137` and `:303-311`, failures are flattened to plain strings.

Use a conservative `RetryConfig` in the runner and preserve structured error data (type/category/error_id) in `outputs.jsonl` / `events.jsonl`. That would make the runner more resilient to provider-side truncation and easier to debug when failures like the historical gpt-oss EOFs recur.

### I5 — If summary exactness matters, enforce it in code instead of hoping the prompt carries it
`/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:113-115` accepts any summary string, while the prompt asks for a narrow `Add '...' to ...` recommendation form.

If downstream analysis cares about exactness, add a tiny validator or repair step for `summary`. The current source has no mechanism that could realistically drive the `11/104` exact-match rate reported in `insight_codex.md` much higher.

## Trace to Insight Findings

- **B1 + B2 → run-33 bracket placeholders / review exact-format slip.** The PR still contains a bracketed review example and the validator never rejects brackets or wrong order. That is the clearest source-level explanation for the placeholder spike and for review exact-format staying around 90% instead of converging upward.
- **B3 + I3 → llama3.1 later-call degradation.** The insight file’s call-local pattern (`call-1` good, `call-2/3` degraded) lines up with the hard-coded three-call loop and the growing name blacklist in later prompts.
- **S2 + I2 → label-only options, fabricated percentages, marketing leakage.** Those issues persist because they are only discouraged by prompt text; the code has no field-global lint or retry trigger for them.
- **I4 → historical gpt-oss EOF failures.** The prompt change reduced output size enough to avoid the failure in this batch, but the runner still has no retry safety net when the provider truncates or transiently fails.
- **I5 → poor summary exactness.** The current source never validates or repairs `summary`, so low exact-match rates are expected.

## PR Review

PR #297 is directionally correct on its main claim. The edits in the PR branch clearly simplify the consequence instructions and remove the old mandatory quantification/template pressure in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:34-57`, `:137-159`, and `:169-199`. That matches the strong before/after improvement in consequence length, chain leakage, and fabricated numbers reported in both insight files.

The implementation is still incomplete in three important ways:

1. It leaves a self-contradictory bracket template in the `review_lever` prompt block at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:181-193`.
2. It does not upgrade validation to match the new “exact order, one field, two sentences” contract in `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:85-108`.
3. It adds no code-level guard for the residual failures that moved into `options` and `review` once the consequence prompt got better.

There is also PR-scope drift: the branch includes a control-flow change at `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py:263-282` (`break` → `continue`) that is not mentioned in the PR description. That should be split out or at least called out explicitly, because it changes experiment behavior independently of prompt wording.

My assessment: the **prompt simplification itself** looks like a real quality win, but the **PR implementation is not fully buttoned up**. The branch still contains one direct leakage vector (square brackets), one underpowered validator, and one undeclared control-flow change.

## Summary

The biggest code-level gap is not in the simplified consequence text; that part is working. The biggest gap is that the PR still relies too heavily on prompt compliance for `review`, `options`, and later-call behavior.

If I had to prioritize fixes, I would do them in this order:

1. remove bracket placeholders and tighten `review_lever` validation,
2. make the multi-call loop adaptive instead of always doing three full rounds,
3. add a language-agnostic post-parse lint for label-only options and unsupported `%` claims,
4. add bounded retry/error telemetry in the optimizer runner.
