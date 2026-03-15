# Synthesis

Analysis covers runs 24–31 (`history/0/24_identify_potential_levers` through `history/0/31_identify_potential_levers`), 8 models, 40 plan executions, 25 successful (62.5%).

---

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **Prompt template leakage** is the dominant content quality problem. The phrases `"Systemic: 25% faster scaling through..."` and `"Material Adaptation Strategy"` appear verbatim in the system prompt and are copied wholesale by multiple models. Run 28 (gpt-5-nano) uses "25% faster" in 72 of 75 levers; runs 25 and 26 emit a lever literally named "Material Adaptation Strategy" even for a film production plan.

2. **Schema validation is inverted**: `DocumentDetails` requires `strategic_rationale` and `summary`, but `save_clean()` only writes the flattened `levers` list and discards those fields. This causes run 30 (gpt-4o-mini) to fail 2/5 plans despite generating valid levers, because those wrapper fields were omitted.

3. **No post-merge sanitization**: After the three LLM calls are merged, no code checks option counts, placeholder content, or total lever count. Run 31 (claude-haiku) wrote a lever literally named "Placeholder Removed - Framework Compliance" with options `["Removed"]` into the final artifact. Run 26 (llama3.1) passed through 14 levers with only 1 option.

4. **Anti-duplication instructions cover names only, not topics**: The call-2/3 prompt says "Generate 5 MORE levers with completely different *names*", but also replays the full prior assistant JSON into the chat history. Models can produce new names while covering near-identical topics. Run 28 parasomnia: 5 of 10 cross-batch lever pairs are semantic duplicates.

5. **No context window guard**: nemotron-3-nano has a 3900-token context window (confirmed in run 25 raw metadata). 3-call history growth makes later calls overflow. Result: 0/5 plans in run 24, 1/5 in run 25.

---

## Cross-Agent Disagreements

### D1 — Severity of options cardinality conflict
**code_claude** calls the mismatch between `Lever.options` field description ("2-5 options") and the system prompt ("exactly 3") a confirmed bug (B1) and primary driver of single-option levers in run 26.
**code_codex** bundles this as part of a broader "schema doesn't enforce what the prompt says" pattern (B3) rather than isolating it.
**Verdict (source-verified):** Both are correct. Line 34 of `identify_potential_levers.py` reads `description="2-5 options for this lever."` and line 90 reads `"Each lever's options field must contain exactly 3 qualitative strategic choices"`. These are contradictory. The field description is embedded in the JSON schema sent to the LLM, so models that weight the schema more heavily will not generate exactly 3 options. This is a genuine bug.

### D2 — Best model: run 29 (qwen3) vs run 28 (gpt-5-nano)
**insight_claude** ranks run 29 #1 (clean, no leakage, 5/5 success).
**insight_codex** ranks run 29 best for reliability but run 28 better for *depth/richness*, noting run 29 has only 45/75 unique systemic phrases and average option length of 63 chars vs. baseline 150.
**Verdict:** Both assessments are correct about different dimensions. Run 29 is the better *reliability* candidate; run 28 is closer to baseline on *content depth* despite its leakage problem. This disagreement is not about facts but about which metric to prioritize.

### D3 — Whether baseline is a valid quality target
**insight_claude** uses baseline as the quality anchor.
**insight_codex** flags that baseline itself has 22 cross-call duplicate names and 21/75 consequences with no numeric measure, so it is not a gold standard.
**Verdict:** insight_codex is more accurate. The baseline has repeated lever names (`Resource Allocation Strategy`, `Technological Adaptation Strategy` appear multiple times in the silo baseline). Baseline is a reasonable depth reference for field lengths and specificity, but not a correctness target for uniqueness.

### D4 — Whether validation retries should be enabled (code_claude I6 vs code_codex B5)
**code_claude** calls this I6 (improvement opportunity); **code_codex** calls it B5 (bug), arguing that an optimizer that doesn't retry transient failures is measuring prompt quality through a single brittle call.
**Verdict:** code_codex's framing is more correct. The runner at `runner.py:94` builds `LLMExecutor(llm_models=llm_models)` with no `max_validation_retries`, converting recoverable schema failures into terminal data points. For a prompt optimizer specifically, this inflates the failure rate of prompts that are otherwise viable.

---

## Top 5 Directions

### 1. Remove the "25% faster scaling" and "Material Adaptation Strategy" examples from the system prompt
- **Type**: prompt change
- **Evidence**: Both insight agents confirm; code_claude I1/I2; code_codex B4/I4. Verified in source at `identify_potential_levers.py:95` ("Systemic: 25% faster scaling through...") and `:104` (`"Material Adaptation Strategy"`). Run 28 shows 72/75 levers contain "25% faster"; runs 25 and 26 emit the literal example lever name.
- **Impact**: Eliminates the most pervasive content quality problem across at least runs 26 and 28, affecting ~45+ levers. Improves domain specificity for all models that currently copy these examples. No reliability risk.
- **Effort**: Low — two phrase replacements inside the `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` string constant in `identify_potential_levers.py`.
- **Risk**: Minimal. Replacing with bracket-style placeholders (`"[measurable second-order impact, e.g., a % change or capacity shift]"`) still guides the model toward structure without providing a copiable filler.

### 2. Make `strategic_rationale` and `summary` optional in `DocumentDetails`
- **Type**: code fix
- **Evidence**: code_claude I4; code_codex B2; both insight agents confirm run 30 failures. Verified: `identify_potential_levers.py:53-62` requires both fields; `save_clean()` at line 267 writes only `self.lever_item_list()` and never uses them.
- **Impact**: Converts 2 of run 30 (gpt-4o-mini)'s 5 failures to successes immediately, from 60% → 100% on that model. Also makes the step more resilient to any model that generates valid levers but skips the wrapper. Affects all models without a prompt change.
- **Effort**: Low — change `strategic_rationale: str` and `summary: str` to `Optional[str] = Field(default=None, ...)` at lines 54 and 60.
- **Risk**: Minimal. These fields are not used downstream (confirmed by `save_clean()` behavior). Optionality may reduce schema strictness slightly, but the levers themselves are what matter.

### 3. Fix the options cardinality conflict: align Pydantic schema with system prompt
- **Type**: code fix
- **Evidence**: code_claude B1; code_codex B3. Verified at `identify_potential_levers.py:34` ("2-5 options") vs. `:90` ("exactly 3"). Run 26 has 14 single-option levers; run 31 has at least 1.
- **Impact**: Removes the contradictory signal sent to the LLM via the JSON schema. Models currently receive conflicting "2-5" from the schema and "exactly 3" from the natural-language prompt and arbitrate unpredictably. Fixing the field description to "exactly 3 options" makes the schema consistent. Also add the explicit prohibition `"Conservative:", "Moderate:", "Radical:"` to the prohibitions list (code_claude I3, currently only "Option A:", "Choice 1:" are listed).
- **Effort**: Low — 1-line change in the `Lever.options` field description; 1 addition to the prohibitions list.
- **Risk**: Minimal. Models that were following the schema "2-5" will converge to exactly 3, which is what the pipeline expects.

### 4. Add post-merge sanitization before writing `002-10-potential_levers.json`
- **Type**: code fix
- **Evidence**: code_claude I8; code_codex I3/B3; both insight agents confirm. Run 31 placeholder lever in final artifact; run 26 single-option levers in final artifact.
- **Impact**: Prevents structurally invalid content from silently propagating to `deduplicate_levers.py` and downstream steps. Catches: placeholder levers (name contains "Placeholder" or "Removed"), wrong option count (!= 3), and total count != 15.
- **Effort**: Medium — add a post-merge filter function after line 229 in `identify_potential_levers.py` with three checks: name pattern match, option count, total count.
- **Risk**: Low. Should log warnings rather than raise exceptions for wrong total count, since the root cause (B2) may return 4 or 6 levers per call silently.

### 5. Extend anti-duplication instructions to cover semantic topics, not just names
- **Type**: code fix + prompt change
- **Evidence**: code_claude I7; code_codex B1/I1; insight_claude N5; insight_codex uniqueness metrics. Run 28 parasomnia: 5/10 cross-batch lever pairs are semantic duplicates despite unique names.
- **Impact**: Reduces semantic duplication in batches 2 and 3. Currently the call-2/3 prompt only bans reusing lever *names*. Also, replaying the full prior assistant JSON into the chat history primes the model to rephrase rather than explore new dimensions.
- **Effort**: Medium — modify the call-2/3 prompt at `identify_potential_levers.py:163-168` to also pass a list of short topic summaries (1 sentence per lever) alongside the names. Optionally, instead of appending the full structured JSON as the assistant turn, append a compact summary.
- **Risk**: Medium. Compressing prior assistant content changes the multi-turn conversational structure. Could reduce quality for models that rely on prior structure to maintain format. Should be tested carefully.

---

## Recommendation

**Pursue Direction 1 first: remove the "25% faster scaling" and "Material Adaptation Strategy" examples from the system prompt.**

**Why first:** It is the single change with the broadest reach. Template leakage affects runs 26 and 28 across all 5 plans (72 uses of "25% faster" in run 28 alone), impairs content quality even in otherwise-successful runs, and the fix is two phrase replacements in a string constant. It requires no schema changes, no runner changes, and no risk of regression. Directions 2 and 3 are also very low effort and should be done in the same pass, but Direction 1 addresses the most visible quality failure.

**What to change exactly** — in `identify_potential_levers.py`, inside `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`:

*Line 95, current:*
```
• Include measurable outcomes: "Systemic: 25% faster scaling through..."
```
*Replace with:*
```
• Include measurable outcomes: "Systemic: [a specific, domain-relevant second-order impact with a measurable indicator, such as a % change, capacity shift, or cost delta]"
```

*Line 104, current:*
```
- Name levers as strategic concepts (e.g., "Material Adaptation Strategy")
```
*Replace with:*
```
- Name levers as strategic concepts that are specific to this project's domain (e.g., "[Domain]-[Decision Type] Strategy")
```

*Line 117, current:*
```
- NO prefixes/labels in options (e.g., "Option A:", "Choice 1:")
```
*Replace with:*
```
- NO prefixes/labels in options (e.g., "Option A:", "Choice 1:", "Conservative:", "Moderate:", "Radical:")
```

**Also do immediately (same code change, different lines):** Direction 2 — make `strategic_rationale` and `summary` optional. This is a 2-line change with zero risk and converts run 30's 60% → 100% success rate. The two changes together constitute a single small PR.

---

## Deferred Items

- **Direction 3 (options cardinality fix)**: Still easy, do in the next PR after confirming the prompt changes land cleanly.
- **Direction 4 (post-merge sanitization)**: Medium effort. Do after prompt stabilization so the sanitizer is validating good outputs rather than patching bad ones.
- **Direction 5 (topic-level anti-duplication)**: Higher risk. Should be a separate experiment after Directions 1–3 are in place, since it changes the conversational structure.
- **Enable `max_validation_retries` in runner** (code_claude I6, code_codex B5): Valid improvement for the prompt optimizer's measurement accuracy. Deferred because it changes the infrastructure rather than the prompt or schema, and should be evaluated separately.
- **Context window guard** (code_claude I5, code_codex S3/I6): Clearly correct but affects only model selection for nemotron-class models. Low urgency since those models (runs 24, 25) are already avoided.
- **Stateless/semi-stateless multi-call loop** (code_codex I1): High potential but high complexity. Restructuring chat history across 3 calls could break other behavior. Defer until simpler fixes are validated.
- **Baseline as quality metric**: insight_codex is right that baseline uniqueness is not a reliable gold standard (22 repeated names). Future assessment runs should weight field length proximity to baseline and unique systemic-phrase count alongside exact uniqueness.
