# Synthesis

## Cross-Agent Agreement

All four analysis files converge on the following:

1. **The #1 root cause is a code/prompt contract mismatch on lever count.** The registered prompt says "EXACTLY 5 levers per response," but `DocumentDetails.levers` allows `min_length=5, max_length=7` (line 78–82) and follow-up calls explicitly say "Generate 5 to 7 MORE levers" (line 203). Both code reviewers name this their top bug; both insight agents document the 17–19-lever artifacts it produces in runs 61 and 66.

2. **The merge loop (lines 244–247) is completely ungated.** It appends all levers from all 3 sub-calls unconditionally, with no count assertion and no name deduplication. Confirmed by both code reviewers and corroborated by duplicate-name findings in runs 61 and 65.

3. **Run 60 is a total failure** (0/5 plans, JSON extraction error). Run 65 (gpt-4o-mini) is the most operationally reliable (5/5, ~37 s/plan) but produces the weakest content. Run 63 (gpt-5-nano) produces the best content but is the slowest (~235 s/plan). All four files rank run 63 first for quality.

4. **The `[Domain]-[Decision Type] Strategy` naming template in the prompt causes robotic prefix overuse.** Run 65 applied "Silo-" to 100% of lever names; run 66 to 47%. Both insight agents flag this as the mechanism.

5. **The prompt-optimizer runner creates `LLMExecutor` with no retry config**, unlike the main pipeline. Single-call failures in runs 60, 62, and 66 are never retried. Both code reviewers confirm this.

---

## Cross-Agent Disagreements

**1. Quality ranking of run 66 (claude-haiku).**
- Claude insight ranks it #1 (richest domain-specific content, best numeric grounding, multi-paragraph options).
- Codex insight ranks it #4 (rich reasoning but "badly off-shape": 4/12 raw responses over-generated, 17–19 lever final files, summary quality collapse to 1/12 `Add…` pattern).
- **Who is right?** Both. The disagreement is about whether to score on content richness or output-contract compliance. Source code confirms overcount: lines 244–247 flatten all levers unconditionally, and run 66 raw files contain 4 responses with !=5 levers. For prompt optimization purposes, contract compliance matters — a 17-lever artifact is a regression regardless of per-lever quality. Codex insight's ranking is more appropriate for the optimization goal.

**2. Severity of run 64 (qwen3-30b) field contamination.**
- Codex insight calls it "severe" (60/75 levers with `Controls`/`Weakness:` text in `consequences`).
- Claude insight mentions it more briefly (N8 notes vagueness but does not count the leak directly).
- **Who is right?** Codex. The `consequences` field description at lines 34–44 explicitly says "Do NOT include 'Controls … vs.', 'Weakness:', or other review/critique text in this field." The codex code review confirmed the leak in `history/0/64_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`. There is no runtime validator, so all 60 leaking levers pass schema validation and are saved as "successful."

**3. Fix ordering — code-first vs. prompt-first.**
Both pairs of agents agree: fix code first, then iterate on prompts. No disagreement.

---

## Top 5 Directions

### 1. Fix the lever-count contract: align schema + follow-up call with "exactly 5"
- **Type**: code fix
- **Evidence**: Both code reviews (claude B1+B2, codex B1); both insight agents (claude N3, codex N1). Direct artifact evidence: runs 61 and 66 produce 17–19 lever files instead of 15.
- **Impact**: Eliminates the primary regression in runs 61 and 66 (overcount artifacts). Aligns the Pydantic schema with the registered prompt. Affects all models since the schema and follow-up text are model-agnostic.
- **Effort**: Low — two one-line changes in `identify_potential_levers.py`
- **Risk**: Minimal. Models that already produce exactly 5 per call are unaffected. Models that relied on returning 7 will be forced to comply; the existing deduplication blacklist in the follow-up prompt already handles name avoidance.

### 2. Enable retry config in the prompt-optimizer runner
- **Type**: code fix
- **Evidence**: Codex code review B2; claude code review S3/I4. `runner.py:94` constructs `LLMExecutor(llm_models=llm_models)` with no retry config; `run_plan_pipeline.py:171–175` passes `retry_config=RetryConfig()` in the main pipeline.
- **Impact**: Converts hard failures (run 60: 5/5 plans; run 62: 1 plan; run 66: 1 plan) into retryable near-misses. Improves overall batch completion rate from 28/35 (80%) toward 100% across all models.
- **Effort**: Low — add `retry_config=RetryConfig()` to the `LLMExecutor` constructor in `runner.py:94`
- **Risk**: Slight increase in total run time for failing plans due to retries. No change to successful-plan behavior.

### 3. Add post-merge count assertion and name deduplication
- **Type**: code fix
- **Evidence**: Claude code review B3/B4; codex code review B1/B4. Both confirm the merge loop at lines 244–247 is unconditional.
- **Impact**: Prevents silent over-count artifacts from reaching `002-10-potential_levers.json`. Eliminates duplicate lever names (observed in runs 61 and 65). Makes any count violation visible (log warning or truncate to first 5 levers per call).
- **Effort**: Low–medium — add a post-merge count check and a `seen_names` set deduplication pass before UUID assignment
- **Risk**: Truncation to first 5 levers per call is a safe fallback; it degrades gracefully. Deduplication could silently drop a unique lever if names are similar but content is different — logging the drop mitigates this.

### 4. Remove the `[Domain]-[Decision Type] Strategy` naming template from the prompt
- **Type**: prompt change
- **Evidence**: Claude insight H1; codex insight S1 (both agree this is the mechanism behind run 65's 100% "Silo-" prefix and run 66's 47%). The template text lives in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` at lines 142–145 of the source (and identically in the candidate prompt file).
- **Impact**: Reduces robotic template application (runs 65, 66). Models will generate domain-specific names anchored to the plan's actual world rather than parroting `[Domain]-[Decision Type]`. Affects all models since it is in the system prompt.
- **Effort**: Low — edit the system prompt text; no code change
- **Risk**: Some models may generate less consistently formatted names. Trade-off: less uniformity vs. more domain specificity. Given that the best-performing model (run 63) already produces diverse names without prefix abuse, the risk is low.

### 5. Add field-boundary validation: ban `Controls`/`Weakness:` in `consequences`
- **Type**: code fix
- **Evidence**: Codex code review B3; codex insight N3 (60/75 levers in run 64 leaked review text into `consequences`); claude code review I3. The field description at lines 34–44 already prohibits this but there is no runtime check.
- **Impact**: Catches "successful but contaminated" levers before they are saved. Run 64 would go from 75 "successful" levers to 15 clean ones (forcing retries or rejection). Affects mainly qwen-class models that appear to merge fields.
- **Effort**: Medium — add a `@field_validator` on `consequences` (or `review_lever`) in the `Lever` or `LeverCleaned` class that raises if `"Controls"` or `"Weakness:"` appears in `consequences`
- **Risk**: Could increase apparent failure rate for models that blend fields (run 64). That is the correct behavior — surfacing contamination is better than silently saving it.

---

## Recommendation

**Fix the lever-count contract mismatch first (Direction 1).**

This is two lines of code in `identify_potential_levers.py`, both confirmed bugs with direct artifact evidence across multiple models:

**Change 1 — Schema (line 78–82):**
```python
# Before
levers: list[Lever] = Field(
    min_length=5,
    max_length=7,
    description="Propose 5 to 7 levers."
)

# After
levers: list[Lever] = Field(
    min_length=5,
    max_length=5,
    description="Propose exactly 5 levers."
)
```

**Change 2 — Follow-up call prompt (line 203):**
```python
# Before
f"Generate 5 to 7 MORE levers with completely different names. "

# After
f"Generate exactly 5 MORE levers with completely different names. "
```

**Why first?**
- It is the single root cause that explains the most regressions (overcount artifacts in runs 61 and 66, label-only options in run 61 calls 2/3 — because generating 7 levers within 256 tokens forces abbreviation).
- It is a pure code fix that benefits all models equally, with no prompt iteration risk.
- It unblocks prompt optimization: once the output contract is stable at 15 levers/plan, per-lever quality differences between prompt variants become interpretable. Right now, a "better" prompt might produce fewer levers due to stricter compliance, making cross-variant comparison unreliable.
- It is low risk and low effort — 2 characters change on two lines.

After this lands and a new batch confirms 15 levers/plan across all models, the next step is Direction 2 (retry config in runner.py), which is similarly one-line and directly improves the batch completion rate from 80% toward 100%.

---

## Deferred Items

- **Direction 4 (prompt: remove `[Domain]-[Decision Type]` example)** — valid but lower urgency than count contract; pursue after the code fixes stabilize the output shape.
- **Direction 5 (field boundary validator)** — important for run 64 class models; pursue after retry config, as retries may already recover some contaminated levers via re-generation.
- **H2 (replace rigid `Weakness: The options fail to consider` formula)** — both insight agents agree this produces generic weakness text; low-risk prompt change, good for a later iteration.
- **H3 (explicit trade-off sentence requirement in consequences)** — would help runs 62/65 that often omit explicit trade-off language; pursue as a prompt iteration after count contract is fixed.
- **H4 (domain anchoring language)** — prevents generic project-finance drift in run 65; low effort, medium impact.
- **S2 (num_output floor guard)** — prevents llama3.1-class degradation; good hygiene, implement in runner or executor config.
- **B5 / I6 (protect `set_usage_metrics_path` with `_file_lock`)** — real race condition in `runner.py:106,140` when `workers > 1`; worth fixing but does not affect output quality.
- **S3 (make `summary` optional)** — `summary` is not in the cleaned artifact; removing it as a required field would reduce token pressure and eliminate a validation surface for weaker models. Low risk, deferred.
- **C3 (cross-call deduplication — Direction 3 above)** — overlaps with the count fix; implement together in the same PR as Direction 1 if effort allows, otherwise immediately after.
