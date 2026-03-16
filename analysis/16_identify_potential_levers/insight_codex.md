# Insight Codex

I examined the registered prompt at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:1`, the baseline training outputs for the five plans under `baseline/train/`, and history runs `history/1/17_identify_potential_levers` through `history/1/23_identify_potential_levers`.

## Rankings

1. **Run 22 (`openrouter-gemini-2.0-flash-001`)** — best all-around balance: 5/5 plans succeeded, zero measured prompt-constraint violations, 91/91 final lever names unique, and strong measurable consequences. Example: `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4` and `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`.
2. **Run 21 (`openrouter-openai-gpt-4o-mini`)** — slightly less rich than run 22, but also 5/5 success with zero measured violations and the lowest generic-suffix rate among the fully successful runs (7 generic suffix names across 87 levers). Example: `history/1/21_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:4`.
3. **Run 19 (`openai-gpt-5-nano`)** — high domain specificity and 90/90 unique lever names, but brittle compliance: 53 raw `review_lever` mismatches, 5 forbidden option prefixes, and 6 placeholder leaks in final outputs. Example leaks at `history/1/19_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:143` and `history/1/19_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:152`.
4. **Run 23 (`anthropic-claude-haiku-4-5-pinned`)** — highest richness on successful plans, but too fragile operationally: only 3/5 plans succeeded; Hong Kong failed schema validation on `review_lever`, and parasomnia timed out. Evidence: `history/1/23_identify_potential_levers/outputs.jsonl:1` and `history/1/23_identify_potential_levers/outputs.jsonl:5`.
5. **Run 17 (`ollama-llama3.1`)** — reliable, but shallow and under-specified; five raw responses exceeded the 5–7 lever target, and numeric/measurable consequences were weakest (24/87). Example: `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`.
6. **Run 18 (`openrouter-openai-gpt-oss-20b`)** — one dropped plan due truncated JSON; content is often decent, but schema reliability is not there. Evidence: `history/1/18_identify_potential_levers/outputs.jsonl:5`.
7. **Run 20 (`openrouter-qwen3-30b-a3b`)** — similar truncated-JSON failure to run 18, plus the shortest options on average (8.33 words), which often read more like labels than full strategic approaches. Evidence: `history/1/20_identify_potential_levers/outputs.jsonl:4`.

## Negative Things

- The prompt's exact-format `review_lever` requirement is still too brittle in practice. The prompt demands the exact pattern `Controls [Tension A] vs. [Tension B]. Weakness: ...` at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:23`, but run 23 lost the entire Hong Kong plan because the model wrote semantically valid reviews with `versus` instead of the exact `vs.` token, producing seven validation errors and discarding the whole response: `history/1/23_identify_potential_levers/outputs.jsonl:1`.
- The exact summary format is also fragile. The prompt asks for `Add '[full strategic option]' to [lever]` at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:27`, but run 23 went 0/9 on successful raw summaries even though the summaries were substantive. In `history/1/23_identify_potential_levers/outputs/20250329_gta_game/002-9-potential_levers_raw.json`, the summary says `Add to Lever 4 (or create new lever): ...` rather than the exact required form.
- Run 19 shows prompt-template leakage into final outputs. Six final GTA reviews literally contain `Controls [Tension A] vs. [Tension B]. Weakness: The options fail to consider [specific factor].` at `history/1/19_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:143`, and five silo options still carry forbidden `Radical:` prefixes, e.g. `history/1/19_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:152`.
- Run 18 and run 20 both lost the parasomnia plan to truncated JSON (`EOF while parsing a list`), which means the current setup still wastes full-plan attempts on serialization failure rather than partial salvage or repair: `history/1/18_identify_potential_levers/outputs.jsonl:5` and `history/1/20_identify_potential_levers/outputs.jsonl:4`.
- Run 17 often satisfies surface structure without satisfying the intended quality bar. Its silo levers use short, generic consequence chains and option labels such as `Closed Ecosystem` / `Semi-Open Ecosystem with Managed Exchange`, which are much closer to category labels than complete strategic approaches: `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7`.
- The strongest-content run (23) is probably too verbose for the current step contract. Its average consequence length was 110.14 words and average option length 33.32 words, roughly 2x the next-richest runs, and one plan timed out entirely: `history/1/23_identify_potential_levers/outputs.jsonl:5`.

## Positive Things

- Compared with the baseline training outputs, the prompt clearly improves domain-specific naming. Baseline sovereign-identity output opens with `Technical Feasibility Strategy`, `Policy Advocacy Strategy`, and `Coalition Building Strategy` in `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:4`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:15`, and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:26`. In contrast, run 22 uses tighter project-native names such as `Demonstrator Scope`, `Policy Engagement Intensity`, and `Coalition Breadth` at `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`, `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`, and `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:26`.
- Runs 21 and 22 are the cleanest prompt fits across this model set: both succeeded on all five plans, had zero raw review-format violations, zero summary-format violations, zero prefix violations, zero placeholder leakage, and perfect measured consequence-chain compliance.
- Run 22 especially delivers measurable second-order impacts in the spirit of the prompt. `Demonstrator Scope` cites a 15% stakeholder-belief shift, `Policy Engagement Intensity` cites a target of `3+` formal meetings, and `Coalition Breadth` cites `20+ organizations` and `50+ media mentions` in `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:5`, `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:16`, and `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:27`.
- Run 21 shows the prompt can still produce concise, compliant outputs rather than only inflated ones. The first Hong Kong lever cleanly ties local-talent choices to a `30%` engagement increase and a strategic authenticity/global-appeal trade-off while preserving the exact review structure: `history/1/21_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:4`.
- Final lever-name uniqueness is much better than baseline. Baseline ended at 52 unique names across 75 final levers, while every history run achieved perfect within-run name uniqueness in final merged outputs (63/63 up to 91/91), indicating the prompt does widen the candidate pool and reduce cross-response collapse.

## Comparison

- **Against baseline**: the new prompt substantially reduces formulaic naming and improves measurable specificity, but baseline was more validator-friendly. Baseline had 61 generic-suffix names across 75 levers and only 52 unique names, yet it also had 0 raw review violations and 0 summary violations. The new prompt improves naming across every model, but only runs 21 and 22 preserve baseline-level compliance.
- **21 vs 22**: run 22 is the higher-ceiling version; run 21 is the safer compact version. Run 22 has richer consequences (52.47 average words vs 32.33) and more total final levers (91 vs 87), while run 21 has fewer generic-suffix names (7 vs 21). Both are good prompt-model fits.
- **19 vs 23**: both demonstrate that stronger domain-specificity pressure can backfire. Run 19 produces the cleanest name diversity after run 22/21, but it leaks placeholders and forbidden prefixes into final outputs. Run 23 produces the most detailed content by far, but the exact-format validators and timeout budget turn that richness into lower success rate.
- **17 vs baseline**: run 17 improves uniqueness dramatically but loses too much depth. It had 87/87 unique names, but only 24/87 consequences with explicit numeric indicators and an average consequence length of 16.91 words, far below baseline's 33.65.
- **18 and 20**: these are not obviously bad prompt fits semantically, but their JSON truncation errors make them weak optimizer exemplars because whole plans disappear before downstream comparison can even happen.

## Quantitative Metrics

Metric notes:

- `Raw count viol` = raw responses whose `levers` list was not in the requested 5–7 window.
- `Generic suffix names` = final lever names ending with formulaic suffixes such as `Strategy`, `Framework`, `Model`, `Protocol`, `System`, or `Architecture`.
- `Opener dupes` = duplicate first-two-word option openings across final merged levers, used as a lightweight template-leakage proxy.
- `Raw review viol` and `Summary viol` are computed from `002-9-potential_levers_raw.json`.
- `Chain ok` means the final consequence text contains `Immediate:`, `Systemic:`, `Strategic:`, and at least two `→` arrows.

### Reliability

| Run | Model | Plans OK | Missing plans | LLMChatError | Validation errors | Raw count viol |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | baseline | 5/5 | 0 | 0 | 0 | 0 |
| 17 | ollama-llama3.1 | 5/5 | 0 | 0 | 0 | 5 |
| 18 | openrouter-openai-gpt-oss-20b | 4/5 | 1 | 1 | 1 | 0 |
| 19 | openai-gpt-5-nano | 5/5 | 0 | 0 | 0 | 0 |
| 20 | openrouter-qwen3-30b-a3b | 4/5 | 1 | 1 | 1 | 0 |
| 21 | openrouter-openai-gpt-4o-mini | 5/5 | 0 | 0 | 0 | 0 |
| 22 | openrouter-gemini-2.0-flash-001 | 5/5 | 0 | 0 | 0 | 0 |
| 23 | anthropic-claude-haiku-4-5-pinned | 3/5 | 2 | 2 | 1 | 0 |

### Uniqueness / Leakage

| Run | Unique names | Generic suffix names | Opener dupes | Review dupes | Total levers |
| --- | --- | --- | --- | --- | --- |
| baseline | 52/75 | 61 | 98 | 0 | 75 |
| 17 | 87/87 | 22 | 112 | 1 | 87 |
| 18 | 71/71 | 8 | 82 | 0 | 71 |
| 19 | 90/90 | 10 | 73 | 20 | 90 |
| 20 | 66/66 | 22 | 36 | 0 | 66 |
| 21 | 87/87 | 7 | 123 | 0 | 87 |
| 22 | 91/91 | 21 | 108 | 0 | 91 |
| 23 | 63/63 | 6 | 52 | 0 | 63 |

### Average Field Lengths

| Run | Avg name w | Avg cons w | Avg option w | Avg review w |
| --- | --- | --- | --- | --- |
| baseline | 3.07 | 33.65 | 19.03 | 20.41 |
| 17 | 2.97 | 16.91 | 10.56 | 20.97 |
| 18 | 3.03 | 44.39 | 13.39 | 17.11 |
| 19 | 5.67 | 47.77 | 13.78 | 18.01 |
| 20 | 3.14 | 40.53 | 8.33 | 16.00 |
| 21 | 3.82 | 32.33 | 14.57 | 19.71 |
| 22 | 2.90 | 52.47 | 14.88 | 20.91 |
| 23 | 6.27 | 110.14 | 33.32 | 38.65 |

### Constraint Violations

| Run | Raw review viol | Summary viol | Prefix viol | Placeholder leak | Chain ok | Numeric ok |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 0 | 0 | 0 | 0 | 70/75 | 54/75 |
| 17 | 0 | 1 | 0 | 0 | 87/87 | 24/87 |
| 18 | 0 | 4 | 0 | 0 | 34/71 | 71/71 |
| 19 | 53 | 0 | 5 | 6 | 66/90 | 89/90 |
| 20 | 0 | 0 | 0 | 0 | 66/66 | 66/66 |
| 21 | 0 | 0 | 0 | 0 | 87/87 | 87/87 |
| 22 | 0 | 0 | 0 | 0 | 91/91 | 91/91 |
| 23 | 0 | 9 | 0 | 0 | 21/63 | 63/63 |

## Evidence Notes

- Prompt clauses most correlated with failures are the exact `review_lever` and `summary` string contracts at `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:23` and `prompts/identify_potential_levers/prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt:27`.
- Baseline still shows the old formulaic naming pattern clearly in sovereign identity: `Technical Feasibility Strategy`, `Policy Advocacy Strategy`, `Coalition Building Strategy` at `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:4`, `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:15`, and `baseline/train/20260308_sovereign_identity/002-10-potential_levers.json:26`.
- Run 22 demonstrates the intended improvement path: short domain-native names, measurable systemic effects, and compliant reviews in `history/1/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:4`.
- Run 21 shows that compliance does not require runaway verbosity: `history/1/21_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:4`.
- Run 17 shows what happens when the model hits the shape but misses the substance: `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `history/1/17_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:7`.
- Run 19 exposes two different leakage paths: literal placeholder copying in `history/1/19_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:143` and forbidden `Radical:` prefixes in `history/1/19_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:152`.
- Run 23 confirms that schema-level hard validation still discards otherwise useful outputs. Hong Kong dies on seven `review_lever` validations and parasomnia dies on timeout in `history/1/23_identify_potential_levers/outputs.jsonl:1` and `history/1/23_identify_potential_levers/outputs.jsonl:5`.
- Runs 18 and 20 show a separate failure class: invalid/truncated JSON for parasomnia at `history/1/18_identify_potential_levers/outputs.jsonl:5` and `history/1/20_identify_potential_levers/outputs.jsonl:4`.

## Questions For Later Synthesis

- Should later prompt iterations optimize for the safest cross-model behavior (runs 21/22) or for the higher-ceiling but fragile richness seen in run 23?
- Is the exact `vs.` token in `review_lever` actually important downstream, or is the current validator just enforcing a presentation choice that should be normalized automatically?
- Are duplicated option openers a meaningful quality problem, or just a side effect of asking for parallel structure and progression?
- Should summary quality be judged by semantic content rather than exact `Add '...' to [lever]` formatting, given that run 23's summaries were substantive but non-compliant?
- Is the right target fewer final merged levers with better dedup quality, or more final merged levers with broader scenario coverage?

## Reflect

- The prompt is clearly moving the step in the right direction on **naming specificity** and **measurable consequences**. Baseline outputs are much more formulaic.
- The main remaining problem is not "bad ideas"; it is **format brittleness**. Several runs produced useful strategic content that got downgraded or discarded because they missed exact punctuation, exact quoting, or exact serialization.
- The most robust prompt-model zone in this batch is the **middle**: enough detail to force domain language and quantified systemic effects, but not so much detail that the model starts free-styling around the exact string contracts.

Prompt hypotheses:

- **H1**: Replace the current `review_lever` prose instruction with one positive example plus one negative example that explicitly contrasts `vs.` with invalid variants like `versus` and missing punctuation. Evidence: run 23 Hong Kong failure and run 19's 53 raw review violations. Expected effect: fewer schema-drop failures without sacrificing tension framing.
- **H2**: Make the summary requirement shorter and stricter by telling the model to end the summary sentence with the exact substring `Add '...' to [lever].` Evidence: run 23 went 0/9 on summary-format compliance despite strong content, while runs 21 and 22 handled simpler summaries cleanly. Expected effect: preserve missing-dimension guidance while reducing paraphrase drift.
- **H3**: Add an explicit anti-copy instruction for placeholders and label leakage, e.g. `Never repeat bracketed template tokens or the words Conservative/Moderate/Radical in the output.` Evidence: run 19 final outputs copied both placeholder text and `Radical:` labels. Expected effect: reduce literal template leakage.
- **H4**: Add a brevity guardrail such as `Keep each consequence to one sentence under 45 words and each option to one sentence under 25 words.` Evidence: run 23's very long fields correlated with one timeout and with summary drift. Expected effect: better JSON reliability and lower timeout risk while preserving quantification.

## Potential Code Changes

- **C1**: Add a normalization pass before strict validation for `review_lever` and `summary`. Examples: normalize `versus` → `vs.`, add missing period after `vs`, and canonicalize `Add to Lever 4:` into `Add '...' to [lever]` when the semantic payload is recoverable. Evidence: `history/1/23_identify_potential_levers/outputs.jsonl:1` and `history/1/19_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:143`. Expected effect: recover otherwise useful generations instead of discarding whole plans.
- **C2**: Add JSON-repair / truncation-recovery for `json_invalid` EOF cases before marking the plan as failed. Evidence: `history/1/18_identify_potential_levers/outputs.jsonl:5` and `history/1/20_identify_potential_levers/outputs.jsonl:4`. Expected effect: turn some current hard failures into partial successes.
- **C3**: Downgrade non-critical format misses from hard failure to warning where downstream logic can tolerate them. The AGENTS guidance already warns that schema-level hard constraints can waste tokens and success rate. Evidence: run 23 lost an entire plan to review punctuation, and run 17 over-generated raw levers five times without harming final merged outputs. Expected effect: better success rate across heterogeneous models.

## Summary

The prompt is **directionally good**: compared with baseline, it reliably produces more domain-native lever names and more quantified systemic effects. The best evidence is runs **21** and **22**, which keep those gains while staying fully compliant. The main issue is that the prompt currently mixes useful strategic guidance with **overly exact string contracts** that cause disproportionate failures: run **23** loses a whole plan on `review_lever` formatting, run **18** and **20** lose a plan to invalid JSON, and run **19** leaks template artifacts into final outputs. The highest-leverage next step is to preserve the current naming/measurement improvements while making both the prompt and the validator more tolerant of near-miss formatting.
