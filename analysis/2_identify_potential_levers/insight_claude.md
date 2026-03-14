# Insight Claude

Analysis of runs `0/17` through `0/23` of the `identify_potential_levers` step against
prompt `fa5dfb88...` (`prompts/identify_potential_levers/prompt_0_fa5dfb88...txt`).

Seven runs spanning seven different models are examined: nvidia-nemotron, llama3.1,
openai-gpt-oss-20b, gpt-5-nano, qwen3-30b-a3b, gpt-4o-mini, and claude-haiku-4-5-pinned.

---

## Rankings

Ordered by output completeness × content quality:

| Rank | Run | Model | Plans OK | Cross-call diversity | Content quality |
|------|-----|-------|----------|----------------------|-----------------|
| 1 | 23 | anthropic-claude-haiku-4-5-pinned | 4/5 | High | Excellent |
| 2 | 21 | openrouter-qwen3-30b-a3b | 5/5 | Low | Good |
| 3 | 20 | openai-gpt-5-nano | 5/5 | Low | Good |
| 4 | 22 | openrouter-openai-gpt-4o-mini | 5/5 | Minimal | Adequate |
| 5 | 18 | ollama-llama3.1 | 5/5 | None | Poor |
| 6 | 17 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 1/5 | None | Poor |
| 7 | 19 | openrouter-openai-gpt-oss-20b | 1/5 | N/A | N/A |

---

## Negative Things

### 1. Cross-call lever duplication is pervasive

Every run that succeeded produces 15 levers per plan (3 LLM calls × 5 levers/call). In five of
the six runs that produced output, lever *names* repeat exactly across all three calls. Runs 18
and 22 exhibit byte-for-byte identical lever content across calls; runs 20 and 21 show minor
wording variation but identical names. Only run 23 shows meaningful content evolution, and only
for the creative-domain plan (GTA game); even run 23 repeats lever names for the constrained-
domain plan (sovereign_identity).

Evidence: `history/0/18_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
contains lever `"Material Adaptation Strategy"` three times with byte-for-byte identical content.
`history/0/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
shows the same exact-duplication pattern for `"Policy Resilience Framing Strategy"`.

### 2. Template leakage from prompt example name

Runs 17 and 18 copy the prompt example lever name **"Material Adaptation Strategy"** verbatim
as their first lever. The prompt (`prompts/identify_potential_levers/prompt_0_fa5dfb88...txt`,
line: `Name levers as strategic concepts (e.g., "Material Adaptation Strategy")`) provides this
as an illustrative example. Models with weaker instruction-following use it as actual output.

Evidence: `history/0/17_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
lever 1 name = "Material Adaptation Strategy". Same in run 18 raw file
`002-9-potential_levers_raw.json` responses[0].levers[0].name = "Material Adaptation Strategy".

### 3. High failure rate for weak models

Runs 17 (nvidia-nemotron) and 19 (gpt-oss-20b) failed 4/5 plans each. Failures fall into two
categories:
- **Truncated JSON** (EOF while parsing): model stopped mid-array. Seen in run 17
  (hong_kong_game error: `"Invalid JSON: EOF while parsing a list at line 25 column 5"`).
  Root cause: ollama `num_output=256` (extreme truncation) in run 18's metadata suggests
  output-token limits may be misconfigured.
- **Non-JSON response**: model returned dialogue or empty string. Run 19 sovereign_identity
  error: `"Could not extract json string from output: I'm happy to expand the analysis
  further. Could you let me know whether you'd like..."` — model answered a clarification
  question that was never asked.

Evidence: `history/0/17_identify_potential_levers/outputs.jsonl` (4 error rows);
`history/0/19_identify_potential_levers/outputs.jsonl` (4 error rows).

### 4. ollama-llama3.1 output token limit crushes diversity

The raw metadata for run 18 shows `"num_output": 256` (extremely small).
This forces each call to produce minimal option text, then the runner initiates a new call with
no memory of the prior call's output — causing repetition. Options are short (avg ~70 chars)
and generic.

Evidence: `history/0/18_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json`
metadata: `"num_output": 256`. Options like `"Influence procurement processes to include
platform-neutral requirements"` are vague 7-word phrases.

### 5. Measurable outcome numbers are likely hallucinated

The prompt requires: `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"`
Runs 20, 21, and 22 obey this by inserting percentages (25%, 15%, 20%, 30%, 18%, etc.) into
consequences. These figures appear invented. Example from run 21 (qwen3-30b) sovereign_identity:
`"Systemic: 25% faster scaling through diversified anchors"` — this is the same 25% figure used
across different levers and different plans, suggesting the model memorized the example number
rather than reasoning about the plan context.

Evidence: `history/0/21_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
levers 1, 2, 3, 4, 5 all have "25%" in their consequences. Run 22 uses 25%, 15%, 20%, 30%, 18%
across 5 levers — different but equally unsupported by plan content.

### 6. Timeout failure for haiku on hong_kong_game (run 23)

Run 23 (haiku-4-5) timed out on the hong_kong_game plan after 472 seconds. No output was
produced for that plan. This is the most capable model in the set.

Evidence: `history/0/23_identify_potential_levers/outputs.jsonl`:
`{"name": "20260310_hong_kong_game", "status": "error", "duration_seconds": 472.74, "error":
"APITimeoutError('Request timed out or interrupted...')"}`

### 7. Conservative → moderate → radical progression is inconsistently observed

Run 18 (llama3.1) does not follow a clear progression. Example: lever "Material Adaptation
Strategy" options are (1) "Implement a platform-neutral, open standards-based authentication
protocol", (2) "Develop a mobile app that utilizes FIDO2/WebAuthn and OpenID Connect",
(3) "Create a browser-based fallback authentication path using GrapheneOS..." — no clear
escalation from conservative to radical. Run 23 (haiku) follows the progression clearly
(non-production demonstrator → hybrid prototype → production certification).

### 8. Generic/irrelevant options in run 22

Run 22 (gpt-4o-mini) inserts options that are only tangentially related to the plan context.
For the sovereign_identity plan, lever "Policy Resilience Framing Strategy" includes option
`"Introduce blockchain-based audit trails for procurement transparency"` — blockchain is not
mentioned anywhere in the plan, which explicitly focuses on FIDO2/WebAuthn and eIDAS2.

Evidence: `history/0/22_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
lever "Policy Resilience Framing Strategy", option 3.

---

## Positive Things

### 1. Run 23 (haiku-4-5) produces 15 fully unique levers for creative-domain plan

For the GTA game plan, run 23 produces 15 lever names with NO repetition across 3 calls:
"Graphical Fidelity vs. Development Velocity", "Studio Distribution and Collaboration Model",
"Single-Player Narrative Scope vs. Multiplayer Live Service Integration", "Procedural Generation
Scope for World Simulation", "Funding Source Diversification and Creative Independence",
"Technical Debt Accrual vs. Feature Velocity", "Competitive Multiplayer Structure and Player
Segmentation", "Criminal Economy Simulation Realism vs. Exploitation Prevention",
"Content Release Cadence and Platform Launch Strategy", "NPC Agency and Dynamic Dialogue vs.
Narrative Control", "International Studio Coordination and Cultural Adaptation",
"Monetization Model and Post-Launch Revenue Structure", "Intellectual Property Ecosystem and
Transmedia Expansion", "Specialized Talent Recruitment and Retention Strategy",
"Technical Platform Evolution and Version Fragmentation Management".

Each lever is specific, actionable, and demonstrates genuine understanding of game development
tensions.

Evidence: `history/0/23_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
— 15 unique names.

### 2. Run 23 content evolves meaningfully across calls even when names repeat

For sovereign_identity, even though lever names repeat across 3 calls in run 23, the option
text expands significantly. Call 1 options are concise (~160 chars), call 3 options add specific
timing windows, cost estimates, and institutional names. Example: the third-call version of
"Institutional Engagement Sequencing" includes `"accepting risk of early rejection but
establishing dialogue loop and maximizing design-stage influence; if rejected, shift to EU
standards input and long-term coalition consolidation"` — substantially more specific than call
1's equivalent.

Evidence: `history/0/23_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
levers 1 and 6 (same name "Technical Proof Anchor Strategy", compare options length and detail).

### 3. Runs 18, 20, 21, 22 achieve 5/5 plan completion

Four models complete all five plans reliably. Reliability matters for a pipeline where partial
failures waste compute and require reruns.

Evidence: `history/0/18_identify_potential_levers/outputs.jsonl`,
`history/0/20_identify_potential_levers/outputs.jsonl`,
`history/0/21_identify_potential_levers/outputs.jsonl`,
`history/0/22_identify_potential_levers/outputs.jsonl` — all show 5 "ok" rows.

### 4. Review field consistently follows required format

All models that succeed produce `review` fields following `"Controls X vs. Y. Weakness: ..."`.
Format compliance for the review field is high across all successful runs.

### 5. Run 23 consequences avoid hallucinated percentages

Unlike runs 20-22 which insert arbitrary numeric figures, run 23 (haiku) consequences use
qualitative causal chains that are specific to the plan context (mentioning AltID, month
timelines, specific institutions). Example: `"Demonstrator-first enables phase-two public
release and media narrative by month 16, accelerating coalition pressure; production-path delays
AltID influence window."` — this references actual plan milestones.

---

## Comparison

### Comparison to baseline training data

The baseline training data (`baseline/train/20260308_sovereign_identity/002-10-potential_levers.json`)
shows 15 levers produced by a strong reference model. The baseline contains:
- Near-exact 3x repetition of 5 lever names, but with slight variations in the radical option
  between batches (baseline quality is moderate; it suffers from the same cross-call duplication
  problem but with more option variation between calls than runs 17/18/22).
- Options with clear conservative → moderate → radical progression. Example lever "Coalition
  Mobilization" options: (1) round-table awareness (conservative), (2) endorsements from NGOs
  (moderate), (3) national media campaign framing platform neutrality as national security
  (radical).
- Options that are specific to the plan domain (not generic blockchain/AI responses).

Comparison findings:
- Runs 17, 18, 22 produce **lower** quality than baseline (shorter options, template leakage,
  exact duplication).
- Runs 20, 21 produce **comparable** quality to baseline (similar duplication pattern but
  slightly richer options for run 20).
- Run 23 produces **higher** quality than baseline for creative-domain plans (15 unique levers
  for GTA game vs. 5 unique in baseline). For constrained-domain plans, run 23 matches or
  slightly exceeds baseline.

The baseline itself has the cross-call duplication problem, meaning the underlying pipeline
issue predates these runs.

---

## Quantitative Metrics

### Table 1: Completion rates

| Run | Model | Plans OK | Plans failed | Failure mode |
|-----|-------|----------|--------------|--------------|
| 17 | nvidia-nemotron-3-nano-30b-a3b | 1 | 4 | EOF truncation + empty response |
| 18 | ollama-llama3.1 | 5 | 0 | — |
| 19 | openrouter-openai-gpt-oss-20b | 1 | 4 | Dialogue response + EOF truncation |
| 20 | openai-gpt-5-nano | 5 | 0 | — |
| 21 | openrouter-qwen3-30b-a3b | 5 | 0 | — |
| 22 | openrouter-openai-gpt-4o-mini | 5 | 0 | — |
| 23 | anthropic-claude-haiku-4-5-pinned | 4 | 1 | API timeout |

### Table 2: Cross-call lever uniqueness (sovereign_identity plan)

| Run | Total levers | Unique names | Name dedup rate | Content dedup |
|-----|-------------|--------------|-----------------|---------------|
| 17 | 15 | 5 | 33% | Exact (3×) |
| 18 | 15 | 5 | 33% | Exact (3×) |
| 19 | n/a | n/a | — | — |
| 20 | 15 | 5 | 33% | Near-exact (minor wording variation) |
| 21 | 15 | 5 | 33% | Near-exact (minor review variation) |
| 22 | 15 | 5 | 33% | Exact (3×) |
| 23 | 15 | 5 | 33% | Content evolves significantly across calls |

Note: 33% name uniqueness = 5 unique names out of 15 total. All runs show the same 5/15 ratio.
What differs is whether the *content* varies across repeated names (only run 23 shows this).

### Table 3: Cross-call lever uniqueness (GTA game plan)

| Run | Total levers | Unique names | Name dedup rate |
|-----|-------------|--------------|-----------------|
| 17 | n/a (failed) | — | — |
| 18 | 15 | 5 | 33% |
| 19 | n/a (failed) | — | — |
| 20 | 15 | 5 | 33% |
| 21 | 15 | 5 | 33% |
| 22 | 15 | 5 | 33% |
| 23 | 15 | 15 | **100%** |

Run 23 (haiku) achieves 100% unique lever names across all 3 calls for the GTA game plan.
No other run achieves cross-call diversity for any plan.

### Table 4: Average option text length (sovereign_identity, first 5 levers, chars)

| Run | Option 1 (avg) | Option 2 (avg) | Option 3 (avg) | Overall avg |
|-----|----------------|----------------|----------------|-------------|
| 18 | 68 | 67 | 127 | 87 |
| 20 | 218 | 170 | 146 | 178 |
| 21 | 201 | 155 | 107 | 154 |
| 22 | 81 | 70 | 61 | 71 |
| 23 | 168 | 167 | 156 | 164 (call 1); ~200 (call 3) |
| baseline (run 17) | 75 | 121 | 121 | 106 |

Run 22 (gpt-4o-mini) has the shortest option text despite 5/5 completion.
Run 20 (gpt-5-nano) has the longest average for 5-lever repetition runs.
Run 23 grows option length across calls.

### Table 5: Constraint violations and template leakage

| Run | Template leakage | Missing measurable outcomes | Non-JSON failures |
|-----|-----------------|----------------------------|-------------------|
| 17 | YES ("Material Adaptation Strategy") | YES | YES (4 plans) |
| 18 | YES ("Material Adaptation Strategy") | YES | NO |
| 19 | N/A | N/A | YES (4 plans) |
| 20 | NO | NO (hallucinated %) | NO |
| 21 | NO | NO (hallucinated %) | NO |
| 22 | NO | NO (hallucinated %) | NO |
| 23 | NO | YES (no %) — uses qualitative | NO |

"Hallucinated %" = run inserts percentage numbers (25%, 15%, etc.) not derivable from plan content.
"YES (qualitative)" for run 23 = follows spirit of measurable outcomes without fake numbers.

---

## Evidence Notes

1. **Template leakage** — confirmed by direct comparison of prompt text
   (`prompts/identify_potential_levers/prompt_0_fa5dfb88...txt`, line 3 of section 3:
   `Name levers as strategic concepts (e.g., "Material Adaptation Strategy")`)
   against run 17 output lever 1 name = `"Material Adaptation Strategy"` in
   `history/0/17_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`.

2. **Cross-call duplication confirmed in raw file** — the 002-9 raw file for run 18 shows
   `"responses": [{5 levers}, {5 identical levers}, {5 identical levers}]` with three identical
   response objects including identical `"strategic_rationale"` text. The deduplication step
   (002-11) downstream should collapse these, but the 002-10 file retains all 15.
   Source: `history/0/18_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json`.

3. **GTA game run 23 uniqueness** — verified by reading all 15 lever names in
   `history/0/23_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.
   Each of the 15 names is distinct.

4. **Dialogue response in run 19** — exact error text in
   `history/0/19_identify_potential_levers/outputs.jsonl`: the model returned
   `"I'm happy to expand the analysis further. Could you let me know whether you'd like: 1. **Additional levers** ... 2. **More detail on the existing levers**..."` — a clarification
   request. This indicates the model treated the initial exchange as a conversation, not a
   one-shot JSON generation task.

5. **Haiku timeout** — `history/0/23_identify_potential_levers/outputs.jsonl` shows
   hong_kong_game duration 472 seconds with `APITimeoutError`. The other 4 plans completed
   in 82–139 seconds. Hong Kong game plan may be longer or more complex than others.

---

## Questions For Later Synthesis

1. **Why does haiku achieve 15 unique levers for GTA game but only 5 unique for sovereign_identity?**
   Is this a domain-complexity effect (open creative space vs. constrained policy space), a
   plan length effect, or a prompt interaction effect? The hong_kong_game plan also timed out,
   which may be related to plan length.

2. **Is the 3-call runner design intentional for diversity, or an artifact?**
   If diversity is the goal, the runner should seed each call with the names from prior calls
   to prevent repetition. If the pipeline relies on step 11 (deduplication) to handle this,
   the deduplication step needs to be verified as working correctly (the 002-11 files in
   baseline exist but we have not confirmed their content for all runs here).

3. **Should measurable outcomes be dropped or reformulated in the prompt?**
   The current phrasing `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"` causes models to copy the example number. Alternatives: require "concrete causal claims" or
   drop the quantitative requirement entirely.

4. **Is the non-JSON failure mode in run 19 (gpt-oss-20b) a prompt issue or a model-instruction issue?**
   The prompt does not include an explicit "respond only in JSON" instruction. Adding one could
   prevent the clarification-question failure mode. Would it also prevent EOF truncation?

5. **What is the downstream impact of cross-call duplication on step 11 (deduplication)?**
   After 002-11 runs, is the final deduplicated lever set useful, or does deduplication to 5
   unique levers mean the step is producing minimum viable output? Is 5 levers sufficient for
   subsequent steps?

---

## Reflect

The main failure modes in this set are well-separated by model capability tier:
- **Failure to produce valid JSON** — affects weaker models (nemotron, gpt-oss-20b)
- **Cross-call exact duplication** — affects weak-to-moderate models (llama3.1, gpt-4o-mini)
- **Cross-call semantic duplication** — affects moderate models (gpt-5-nano, qwen3-30b)
- **Cross-call name duplication with content enrichment** — affects haiku for constrained plans
- **Full cross-call diversity** — haiku achieves this only for creative-domain plans

This suggests the cross-call duplication problem is driven by two distinct mechanisms:
1. **No memory** — the runner's second and third calls do not know what the first call produced.
   Code change (C1) would address this directly.
2. **Narrow solution space** — for constrained policy domains, there may genuinely be fewer
   distinct strategic lever names. Prompt change (H2) could encourage different naming even
   within a constrained domain.

The template leakage from the example name "Material Adaptation Strategy" is a clear prompt
defect that is trivially fixable (H1). The measurable-outcome number requirement is causing
hallucinated statistics across three models and should be reformulated (H4).

---

## Potential Code Changes

**C1 — Pass prior-call lever names in context to prevent cross-call repetition**
- Motivation: The runner calls the LLM 3 times per plan with no memory of previous calls.
  Every model repeats lever names. Injecting `"You have already generated levers named: [X, Y, Z, ...]
  from prior calls. Your response must use DIFFERENT lever names."` into the second and third
  call's user prompt would eliminate this.
- Evidence: All 6 producing runs show 33% unique name rate. Run 23 achieves 100% only when the
  creative space is wide enough that the model naturally generates different names.
- Expected effect: Cross-call name uniqueness would increase from 33% to potentially 70–100%,
  making step-11 deduplication more valuable.

**C2 — Add explicit JSON-only output instruction to the prompt assembly code**
- Motivation: Run 19 failure was caused by model returning a dialogue response. The prompt
  text does not include an explicit JSON format instruction.
- Expected effect: Would eliminate the "Could not extract json string" failures for models that
  can otherwise produce valid JSON.

**C3 — Review output token limit configuration for each model**
- Motivation: Run 18 (llama3.1) has `num_output: 256` which truncates responses and forces
  exact repetition. Other models likely have higher limits.
- Expected effect: Increasing llama3.1's token limit would allow more option text per call and
  potentially reduce duplication by making each call's output richer.

---

## Hypotheses

**H1 — Remove or replace the "Material Adaptation Strategy" example name in the prompt**
- Change: Replace `(e.g., "Material Adaptation Strategy")` with a non-domain-specific
  placeholder or remove it entirely.
- Evidence: Runs 17 and 18 both use "Material Adaptation Strategy" as lever 1 name, directly
  copied from the prompt example.
- Predicted effect: Eliminates template leakage for weaker models; no effect on stronger models
  that already ignore the example.

**H2 — Add explicit cross-call diversity instruction**
- Change: Add to the prompt: "Generate levers that are distinctly different from any levers you
  may have generated previously for this plan. Avoid repeating lever names across multiple
  responses."
- Evidence: 6/6 producing runs show ≤33% unique lever names across calls. Baseline shows the
  same pattern.
- Predicted effect: Moderate improvement for mid-tier models; likely ineffective without C1
  since models have no memory of prior calls at inference time.

**H3 — Replace "measurable outcomes" requirement with "concrete causal claims"**
- Change: Replace `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"`
  with `"State concrete causal mechanisms: explain HOW the systemic effect operates, not a
  number."` The "25% faster scaling" example should be removed or changed to a format that
  doesn't invite copying.
- Evidence: Runs 20, 21, 22 all insert "25%" or similar percentages inconsistently across
  levers and plans, showing the number is copied from the example rather than derived.
- Predicted effect: Removes hallucinated statistics; encourages models to explain mechanisms
  instead of fabricating figures. May improve consequence quality for all models.

**H4 — Add explicit "no dialogue / JSON only" instruction**
- Change: Add to section 1 of the prompt: `"Your entire response must be a single valid JSON
  object. Do not include any explanatory text, questions, or commentary outside the JSON."`
- Evidence: Run 19 failure was a dialogue response instead of JSON. The current prompt relies
  on implicit understanding of JSON output format.
- Predicted effect: Would prevent dialogue-response failures for models like gpt-oss-20b.
  Would not help with EOF truncation failures.

**H5 — Add explicit "unconventional approach" diversity instruction**
- Change: Add to section 2 (Options MUST): `"At least one option must be specific to THIS
  plan's domain, constraints, and named stakeholders. Do not use generic AI/blockchain/
  optimization options that could apply to any plan."`
- Evidence: Run 22 adds "Introduce blockchain-based audit trails" as the radical option for
  the sovereign_identity policy plan — generic and unrelated to the plan's actual technical
  scope.
- Predicted effect: Would reduce generic options and encourage plan-specific radical
  alternatives.

---

## Summary

Seven models were tested against the same prompt and 5 training plans. The main systemic
findings are:

1. **Cross-call duplication is the dominant quality problem**: All 6 models that produced
   output generated only 5 unique lever names out of 15 per plan (33% uniqueness). Only Claude
   haiku-4-5 broke this pattern, but only for creative-domain plans (GTA game: 100% unique;
   sovereign_identity: same name repetition but enriched content). The root cause is that the
   runner makes 3 sequential LLM calls per plan with no memory of prior calls (code issue C1).

2. **Template leakage in the prompt**: The example name "Material Adaptation Strategy" is
   copied verbatim by weaker models (runs 17 and 18). This is a trivial prompt defect (H1).

3. **Fake measurable outcomes**: Three models (runs 20, 21, 22) insert percentage figures
   (25%, 15%, 20%, etc.) from the prompt example. The "25% faster scaling" example phrase in
   the prompt is being parroted. Reformulating to require causal reasoning instead of numbers
   would fix this (H3).

4. **Reliability stratification**: Models split into three tiers — (a) high failure rate
   (nemotron, gpt-oss-20b: 1/5 plans succeeded), (b) full reliability but high duplication
   (llama3.1, gpt-5-nano, qwen3-30b, gpt-4o-mini: 5/5 plans, low diversity), (c) high quality
   with one timeout (haiku-4-5: 4/5 plans, highest diversity and specificity).

5. **The most impactful change is code-level (C1)**: Injecting prior-call lever names into the
   context of subsequent calls would increase cross-call uniqueness for all models. This is a
   runner code change with no prompt modification required and would benefit every model equally.

**Priority recommendations for synthesis**:
- C1 (pass prior-call names as context) — highest leverage, model-agnostic, code-only change
- H3 (remove hallucinated percentage requirement) — affects 3 of 7 models, easy prompt fix
- H1 (remove "Material Adaptation Strategy" example name) — trivial prompt fix
- H4 (explicit JSON-only instruction) — fixes one failure mode without harming success cases
