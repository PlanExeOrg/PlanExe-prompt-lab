# Insight Claude

## Rankings

- **Tier A:** Run `38` (`anthropic-claude-haiku-4-5-pinned`). Produces the deepest, most domain-specific output in this batch — specific dollar amounts, percentage effects, and multi-sentence chain consequences. The three successful plans are clearly the best strategic artifacts among runs 32–38. Its weakness is brittleness: it times out on two of five plans and produces at least one double-word template leak in a lever option.
- **Tier B:** Run `35` (`openai-gpt-5-nano`). Fully reliable (5/5), properly chained consequences, good domain specificity, and close to baseline field lengths. It is the best fully-reliable single-model run in this batch.
- **Tier B:** Run `36` (`openrouter-qwen3-30b-a3b`). Fully reliable (5/5), proper chain format, moderate depth. Runs faster than `35` (avg ~127s vs ~199s) with slightly shorter option text.
- **Tier C:** Run `33` (`ollama-llama3.1`). Fully reliable (5/5), structurally valid, but consequence depth is noticeably shallower (~110 chars vs baseline ~280 chars) and options are shorter.
- **Tier C:** Run `37` (`openrouter-openai-gpt-4o-mini`). Fully reliable (5/5) and the fastest successful run (avg ~33s), but **all consequences are plain prose** — none follow the required `Immediate: → Systemic: → Strategic:` chain. Options are well-formed and option prefixes are absent, but the core consequence requirement is violated across all plans.
- **Tier D:** Run `34` (`openrouter-openai-gpt-oss-20b`). 3/5 plans succeed. Two plans fail with truncated/EOF JSON — same pattern seen in run `27` under the previous prompt. The three successful plans show moderate depth.
- **Tier E:** Run `32` (`openrouter-nvidia-nemotron-3-nano-30b-a3b`). 1/5 plans succeed. Four plans fail with JSON extraction errors — same pattern as runs `24` and `25`. This model is not a viable candidate for this step.

---

## Negative Things

- **Run 37 consequence format failure (all plans).** The prompt requires the chain `"Immediate: [effect] → Systemic: [impact] → Strategic: [implication]"` at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9`. Run 37 (`gpt-4o-mini`) ignores this entirely and produces plain prose, e.g. `"Choosing a diversified funding strategy will likely enhance financial stability, increase stakeholder engagement, and mitigate risks associated with funding shortages."` at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`. This occurs across all 15 levers in every plan completed by run 37.

- **Run 38 double-word option prefix leak.** Prompt_1 prohibits option prefix labels including `"Radical:"` at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:32`. Run 38 (`haiku`) emits option 3 of lever 5 as `"Radical radical openness with compartmentalization: All silo operational data..."` at `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:53`. The word "radical" appears twice, suggesting the model tried to prepend "Radical:" as a label and then also used it as the start of the option name. The colon after "compartmentalization" is a further prefix-style violation.

- **Run 38 timeout on complex plans.** Two plans time out: `20260310_hong_kong_game` at 426.62 seconds and `20260311_parasomnia_research_unit` at 721.45 seconds — both terminated by `APITimeoutError`. This mirrors run `31` (haiku, previous prompt) which timed out on `parasomnia` at `427.06s`. The `002-10-potential_levers.json` file for silo is 40,398 bytes in run 38 vs ~12,000 bytes for other models, confirming haiku generates ~3–5× more output. Evidence: `history/0/38_identify_potential_levers/outputs.jsonl:4` and `history/0/38_identify_potential_levers/outputs.jsonl:5`.

- **Run 34 JSON truncation failures.** Two plans fail: `20260310_hong_kong_game` with `"Could not extract json string from output: ''"` and `20260311_parasomnia_research_unit` with `"Invalid JSON: EOF while parsing a list at line 24 column 5"`. Evidence: `history/0/34_identify_potential_levers/outputs.jsonl:4` and `history/0/34_identify_potential_levers/outputs.jsonl:5`. The same two plans (`hong_kong`, `parasomnia`) that cause run 38 to time out also cause run 34 to truncate, suggesting these are the heaviest plans in the corpus.

- **Run 32 persistent extraction failures.** Four of five plans fail with `"Could not extract json string from output"` or pydantic JSON validation errors. Only `20260311_parasomnia_research_unit` succeeds. Evidence: `history/0/32_identify_potential_levers/outputs.jsonl:1–4`. This model (`openrouter-nvidia-nemotron-3-nano-30b-a3b`) has now failed in runs `24`, `25`, and `32` — the prompt change had no observable effect on its reliability.

- **Lever count violation for gta plan (16 instead of 15).** Across runs 33, 35, 37, and 38, the `20250329_gta_game` plan produces 16 levers in the merged output instead of the expected 15 (3 calls × 5 levers each). The baseline has 15 levers for this plan. This suggests one of the three LLM calls returns 6 levers instead of 5 specifically for the gta context, violating the "EXACTLY 5 levers per response" constraint at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:4`. Evidence: agent-reported lever counts for `history/0/33_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, `history/0/35_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`, etc.

---

## Positive Things

- **Template leakage from prompt_0 examples is gone.** The previous prompt (`prompt_0`) contained explicit sample phrases such as `"25% faster"` and `"The options fail to consider"` which were copied verbatim by models in runs 26 and 28. The new prompt (`prompt_1`) removes those literal example strings. Scanning run 35, 36, 37, and 38 outputs shows no occurrences of `"25% faster"` as a template token. The `"The options fail to consider"` phrasing now appears only where the model follows the `"Weakness: The options fail to consider [specific factor]."` format instruction — which is appropriate use of the format, not leakage.

- **Run 38 output quality is the highest observed.** Consequences follow the full chain with domain-specific numbers: e.g., `"Immediate: Centralized autocratic control enables rapid decision-making but creates single-point accountability for failures → Systemic: Distributed council governance slows decisions by ~40% but diffuses liability and improves population buy-in by ~60%..."` and `"...reduces system failure probability from ~15% annual to ~2.1% annual, cutting emergency response frequency by 85%"`. Options are multi-sentence complete strategic pathways, not label stubs. Reviews identify non-obvious systemic weaknesses. Evidence: `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`, `:16`, `:27`.

- **Four models achieve 5/5 plan reliability with the new prompt.** Runs 33, 35, 36, and 37 each complete all five plans. This is an improvement over the previous batch (runs 24–31) where only runs 26, 28, and 29 were fully reliable. The new prompt appears to have stabilized parsing for borderline models like gpt-4o-mini (run 30 failed 2/5; run 37 succeeds 5/5).

- **Option prefix violations are mostly absent.** No option in runs 33–37 begins with `"Option A:"`, `"Choice 1:"`, `"Conservative:"`, `"Moderate:"`, or `"Radical:"`. Run 38 has one instance (the "Radical radical" double-word). This is a clear improvement over the prior prompt.

- **Lever names are domain-specific.** Run 38 names like `"Population-Selection Criteria"`, `"Supply-Chain Concealment Model"`, and `"Intergenerational-Legitimacy & Mission-Redefinition Governance"` show the prompt's `"[Domain]-[Decision Type] Strategy"` instruction is being followed. Run 35 names for gta such as `"GTA AI-Driven World Dynamics Strategy"` and `"GTA Safety, Moderation, and Community Governance Strategy"` are similarly project-specific.

---

## Comparison

### Comparison to baseline training data

- The baseline (`baseline/train/20250321_silo/002-10-potential_levers.json`) has 15 levers with consequences averaging ~280 chars and options averaging ~150 chars. It contains repeated lever names (e.g., `"Technological Adaptation Strategy"` appears at positions 3, 9, and 14; `"Resource Allocation Strategy"` at positions 1 and 11) — see `baseline/train/20250321_silo/002-10-potential_levers.json`. This cross-call duplication in the baseline is a known issue from the prior analysis.

- Run 38 exceeds baseline depth substantially: ~550 chars avg per consequence vs ~280 in baseline, and ~200 chars per option vs ~150. It has zero repeated lever names within a plan. On content quality run 38 dominates, but it fails on 2/5 plans.

- Run 35 is the closest match to baseline depth among fully reliable runs: consequences ~170 chars (slightly short), options ~150 chars (matching baseline), proper chain format. It also avoids cross-call name duplication.

- Run 37's options are self-contained and correctly structured, but its plain-prose consequences fall well below baseline (~95 chars vs ~280). The consequence format regression in run 37 is the most significant regression vs baseline quality.

- Run 33 (llama3.1) is structurally valid but significantly shallower than baseline (~110 chars consequences). This is consistent with the prior run 26 (llama3.1) pattern.

- The `hong_kong` and `parasomnia` plans appear to be the most complex inputs in the corpus. Both run 34 and run 38 fail specifically on these two plans (truncation and timeout respectively), while simpler plans (silo, gta, sovereign_identity) succeed. This pattern warrants investigating plan input length or complexity as a failure predictor.

---

## Quantitative Metrics

### Operational / Structural

| Run | Model                                 | Plans OK | Plans Failed | Avg sec (ok) | Failure mode                        |
|-----|---------------------------------------|----------|--------------|--------------|-------------------------------------|
| 32  | nvidia-nemotron-3-nano-30b-a3b        | 1/5      | 4            | 196.3        | JSON extraction failure (4 plans)   |
| 33  | ollama-llama3.1                       | 5/5      | 0            | 68.5         | —                                   |
| 34  | openrouter-openai-gpt-oss-20b         | 3/5      | 2            | 177.4        | EOF/truncated JSON (hong_kong, parasomnia) |
| 35  | openai-gpt-5-nano                     | 5/5      | 0            | 199.1        | —                                   |
| 36  | openrouter-qwen3-30b-a3b              | 5/5      | 0            | 126.7        | —                                   |
| 37  | openrouter-openai-gpt-4o-mini         | 5/5      | 0            | 33.1         | —                                   |
| 38  | anthropic-claude-haiku-4-5-pinned     | 3/5      | 2            | 147.4        | API timeout (hong_kong 427s, parasomnia 721s) |

Sources: `history/0/[32–38]_identify_potential_levers/outputs.jsonl`

### Output File Size (proxy for depth) — 20250321_silo / 002-10-potential_levers.json

| Run | File size (bytes) | Model                     |
|-----|-------------------|---------------------------|
| 33  | 10,316            | ollama-llama3.1           |
| 34  | 12,409            | openrouter-openai-gpt-oss-20b |
| 35  | 13,680            | openai-gpt-5-nano         |
| 36  | 8,213             | openrouter-qwen3-30b-a3b  |
| 37  | 13,576            | openrouter-openai-gpt-4o-mini |
| 38  | 40,398            | anthropic-claude-haiku-4-5 |

Note: Run 37's file size appears comparable to run 35, but run 37 achieves this through verbose option text while skipping the consequence chain. Run 38 is ~3× the next largest.

### Approximate Average Field Lengths (silo plan)

| Run | Avg consequence chars | Avg option chars | Consequence chain (I→S→S) |
|-----|----------------------|------------------|--------------------------|
| baseline | ~280 | ~150 | Present (5 gaps in 75 levers) |
| 33  | ~110 | ~70  | Present |
| 34  | ~270 | ~130 | Present |
| 35  | ~170 | ~150 | Present |
| 36  | ~160 | ~80  | Present |
| 37  | ~95  | ~130 | **Absent** (all 15 levers) |
| 38  | ~540 | ~200 | Present |

Sources: Agent-measured estimates from `002-10-potential_levers.json` files; reported to ±20 chars.

### Lever Count per Plan

| Run | silo | gta | sovereign | hong_kong | parasomnia | Notes |
|-----|------|-----|-----------|-----------|------------|-------|
| baseline | 15 | 15 | — | — | — | Cross-call duplicate names present |
| 33  | 15 | 16 | — | — | — | gta has extra lever |
| 34  | 15 | 15 | 15 | — | — | hong_kong / parasomnia failed |
| 35  | 15 | 16 | — | — | — | gta has extra lever |
| 36  | 15 | 15 | 15 | 15 | 15 | All 5 correct |
| 37  | 15 | 16 | 15 | 15 | 15 | gta has extra lever |
| 38  | 15 | 16 | 15 | — | — | gta has extra lever; hong_kong/parasomnia timed out |

The gta plan triggers a 6-lever response in one of the three calls across four different models (llama, gpt-5-nano, gpt-4o-mini, haiku). Run 34 and run 36 do not show this for gta, making it inconsistent rather than universal.

### Constraint Violations

| Run | Missing I→S→S chain | Option count ≠ 3 | Option prefix leak | Double-word | Placeholder text |
|-----|---------------------|------------------|--------------------|-------------|------------------|
| baseline | 5/75 | 0 | 0 | 0 | 0 |
| 33  | 0 | 0 | 0 | 0 | 0 |
| 34  | 0 (3 plans only) | 0 | 0 | 0 | 0 |
| 35  | 0 | 0 | 0 | 0 | 0 |
| 36  | 0 | 0 | 0 | 0 | 0 |
| 37  | **75/75** | 0 | 0 | 0 | 0 |
| 38  | 0 | 0 | 1 (option prefix) | 1 ("Radical radical") | 0 |

Sources: `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`, `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:53`.

---

## Evidence Notes

- The exact error for run 32 silo is `"Could not extract json string from output: "` — the model produced no parseable JSON at all. Evidence: `history/0/32_identify_potential_levers/outputs.jsonl:4`.

- The exact error for run 34 parasomnia is `"Invalid JSON: EOF while parsing a list at line 24 column 5"` with the partial input ending at `"governance board.\"\n    }"` — the model simply stopped mid-JSON. Evidence: `history/0/34_identify_potential_levers/outputs.jsonl:5`.

- Run 37 example consequence (plain prose): `"Implementing strict information control will likely enhance internal cohesion, reduce dissent, and create a unified narrative, but may stifle innovation."` at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`. Compare to run 38 for the same type of lever: `"Immediate: Total information lockdown ... → Systemic: Managed transparency ... reduces cognitive dissonance by ~45%... → Strategic: Information model determines whether population self-stabilizes..."` at `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:49`.

- Run 38 "Radical radical" option at `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:53`: `"Radical radical openness with compartmentalization: All silo operational data, governance decisions, and external communications fully transparent..."` — the colon after "compartmentalization" is an additional prohibited-prefix pattern.

- Run 35 (gpt-5-nano) activity overview shows 9 LLM calls for silo: `history/0/35_identify_potential_levers/outputs/20250321_silo/activity_overview.json`. Run 37 (gpt-4o-mini) shows 10 calls for silo: `history/0/37_identify_potential_levers/outputs/20250321_silo/activity_overview.json`. The extra call in run 37 may be a retry or an additional deduplication/review step.

- Run 38 haiku silo has no `activity_overview.json` file in its output directory, unlike all other runs which do. This suggests a logging or pipeline difference in how haiku outputs are saved.

- Baseline silo has repeated lever names: `"Technological Adaptation Strategy"` at positions 3, 9, and 14 and `"Resource Allocation Strategy"` at positions 1 and 11 in `baseline/train/20250321_silo/002-10-potential_levers.json`. This cross-call duplication in the baseline is a pre-existing issue (confirmed in prior analysis/3 insight).

---

## Questions For Later Synthesis

1. **Why does gpt-4o-mini (run 37) pass the consequence chain requirement in zero out of 15 levers, while all other models pass it consistently?** Is this a model-specific limitation with the current prompt_1 wording, or a context length issue where the constraint instruction is deprioritized?

2. **Should the haiku timeout issue be addressed by a prompt-side length limit (H3 from prior analysis, now re-evidenced) or by a code-side `max_tokens` cap?** The file sizes suggest haiku generates 3–5× the tokens of other models.

3. **Is the gta plan consistently causing a 16-lever output because of its content (game development context) or its length?** Should the deduplication/merge step enforce a strict cap of 15 levers post-merge?

4. **Should gpt-4o-mini be re-tested with a consequence format example added to the prompt**, or is it fundamentally incapable of producing the chain format and should be deprioritized?

5. **Does run 35 (gpt-5-nano) or run 36 (qwen3) represent the better base for the next prompt iteration?** Run 35 has deeper consequences (~170 chars) but is slower (~199s). Run 36 is faster (~127s) but shallower (~160 chars). Both are fully reliable.

6. **Is the "hong_kong + parasomnia" dual-failure pattern a plan complexity issue (these plans are longer/harder) or a specific content issue** (certain plan types trigger verbose models to expand beyond timeout thresholds)?

---

## Reflect

- The new prompt (prompt_1) has clearly improved reliability and eliminated template leakage from literal example phrases. The gpt-4o-mini model improved from 3/5 to 5/5 success rate. However, it introduced or failed to fix a new quality gap: gpt-4o-mini ignores the chain format entirely.
- Run 38 (haiku) is the only model that truly demonstrates what the prompt is trying to achieve — deeply consequential, specific, domain-grounded strategic analysis — but at the cost of timeouts. This creates a quality/reliability tension that code changes cannot fully resolve.
- The models that are reliable (33, 35, 36, 37) show a wide quality spread. Run 37's near-zero consequence depth makes it an operational outlier even among fast models. The fastest reliable run that actually follows the consequence format is run 36 (qwen3, ~127s).
- Code-side changes (lever count validation, consequence format check, output length limiting) would catch the most systematic problems without prompt changes.

---

## Potential Code Changes

- **C1: Validate consequence chain format post-merge.** After combining lever lists, check that each consequence contains `"Immediate:"` and `"Systemic:"` and `"Strategic:"`. If a lever's consequence lacks the chain, mark it as a quality violation or trigger a single-lever retry. Evidence: run 37 produces 75 chain-free consequences across 5 plans with zero detection. Expected effect: catch gpt-4o-mini-style failures and either retry or flag for downstream quality signals.

- **C2: Enforce strict lever count = 5 per LLM call in raw validation.** Before merging, reject any raw call response that contains ≠ 5 levers and retry that call. Evidence: the gta plan consistently triggers 6-lever responses in at least one call across multiple models (runs 33, 35, 37, 38), producing 16-lever merged files. Expected effect: stabilize merged count at 15 across all plans.

- **C3: Add per-call `max_tokens` limit (or equivalent) for haiku.** Run 38 generates ~40KB per plan for silo. The two timeout plans (hong_kong, parasomnia) are presumably larger; one timed out at 721s. A `max_tokens=4096` (or similar) per-call cap would prevent runaway verbosity. Evidence: `history/0/38_identify_potential_levers/outputs.jsonl:4–5`. Expected effect: prevent haiku timeouts while preserving its quality advantage on simpler plans.

- **C4: Detect and reject option prefix leaks in post-merge sanitizer.** Check each option string: if it starts with a word matching `/^(Radical|Conservative|Moderate|Option [A-Z]:|Choice \d+:)/i`, flag the lever for review. Evidence: `history/0/38_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:53`. Expected effect: prevent prefix-leaked options from reaching downstream pipeline stages.

- **C5: Log `activity_overview.json` for all models consistently.** Run 38 haiku silo output lacks this file; all other runs have it. The activity overview provides call count and token usage, which are important for diagnosing timeout vs. output quality trade-offs. Evidence: missing file at `history/0/38_identify_potential_levers/outputs/20250321_silo/activity_overview.json`.

---

## Prompt Hypotheses

- **H1: Add a concrete consequence chain example to reinforce the I→S→S format for weaker models.** The prompt instructs the chain format at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:9–10` but provides no illustrative example. For gpt-4o-mini (run 37), the instruction produces zero chain-formatted consequences. Adding a short illustrative consequence like `"Immediate: [X happens] → Systemic: [Y metric shifts by ~N%] → Strategic: [Z long-term implication]"` directly below the instruction text could anchor the format. Expected effect: bring gpt-4o-mini into compliance without adding example-phrase leakage, since the example would be structural rather than domain-specific.

- **H2: Add an explicit negative example for option prefixes.** The prohibition at `prompts/identify_potential_levers/prompt_1_b12739343b9a3bc2f0aec73a8605e712a3f663b0e2323cc068a7e328129523d3.txt:32` lists prohibited labels but does not show what a violating option looks like. Run 38 still slips in "Radical radical" with a colon. Adding `"BAD: 'Radical: Open all information to all residents' GOOD: 'Open all information...'"` as a quick contrast could close this gap. Expected effect: reduce label-prefix leakage in verbosity-prone models like haiku.

- **H3: Add a per-consequence length advisory targeting ~200–350 chars.** Run 38 averages ~540 chars and times out; run 37 averages ~95 chars and lacks the chain entirely. The baseline is ~280 chars. An explicit target range would discourage both extremes. Evidence: run 38 timeout (`history/0/38_identify_potential_levers/outputs.jsonl:4–5`), run 37 consequence collapse (`history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`). Expected effect: reduce haiku timeout risk while nudging gpt-4o-mini to expand consequences.

---

## Summary

- **Reliability has improved vs prior batch.** Four models complete 5/5 plans (runs 33, 35, 36, 37), up from three models in runs 24–31. The new prompt appears to have fixed gpt-4o-mini from 3/5 (run 30) to 5/5 (run 37).
- **Persistent model-class failures remain.** nvidia-nemotron (run 32) and gpt-oss-20b (run 34) continue to fail on the same hard plans. haiku (run 38) continues to timeout on complex plans. These are code-level reliability gaps, not prompt gaps.
- **Quality split has sharpened.** Run 38 (haiku) sets a new quality ceiling with specific numbers, tight chain reasoning, and zero name duplication — but it is unreliable. Run 35 (gpt-5-nano) is the best reliable model in this batch. Run 37 (gpt-4o-mini) violates the core consequence format on every single lever.
- **Three immediate actions emerge:** (1) C1 — validate consequence chain in code; (2) C2 — enforce 5-lever-per-call limit; (3) H1 — add a structural consequence example for models that ignore the chain instruction.
- The best candidate for the next prompt iteration is to take run 35 as the operational base, add H1 (chain example) to nudge run 37-class models, and add H3 (length advisory) to reduce run 38-class timeouts.
