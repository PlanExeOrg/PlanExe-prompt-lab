# Synthesis

## Cross-Agent Agreement

All four analysis files converge on the same core diagnosis: **the Pydantic schema descriptions in `identify_potential_levers.py` actively contradict the system prompt**, and **no quality gate exists to reject malformed-but-parseable outputs**.

Specific consensus points:

- **Run 37 (gpt-4o-mini) consequence chain failure** is the clearest regression in this batch. Both insight agents report 75/75 levers with plain-prose consequences (zero I→S→S chains). Both code reviews trace it to the `consequences` field description at line 30–32 of `identify_potential_levers.py`, which provides a plain-prose example and a "30 words" length hint — directly teaching the model the wrong format.

- **6-lever overflow for the gta plan** is confirmed reproducible across four models (runs 33, 35, 37, 38). Both code reviews agree no validator enforces `len(levers) == 5` per call, and both agree the run 38 `placeholder` lever reaching `002-10-potential_levers.json` is a direct consequence.

- **`options` field description says "2-5"** while the system prompt says "exactly 3". Both code reviews flag this as a schema-level permission for non-compliance (B5/code_claude, part of B1/code_codex). Run 33 produced 9 two-option levers in parasomnia.

- **Haiku timeouts (427 s and 721 s)** are caused by unbounded context growth: calls 2 and 3 accumulate two prior ~40 KB haiku assistant turns. Both code reviews agree this is the direct mechanism (B3/code_claude, B3/code_codex).

- **No post-merge filter** lets placeholder names, blank options, and extra levers pass undetected into the final artifact. All four files flag this gap.

- **Telemetry isolation is broken under parallel execution** (`set_usage_metrics_path` outside `_file_lock`; global dispatcher shared across threads). Both code reviews and the missing `activity_overview.json` for run 38 haiku are consistent with this race.

---

## Cross-Agent Disagreements

### Disagreement 1: Best fully-reliable run — run 35 vs. run 36

- **insight_claude** favors run 35 (gpt-5-nano) as "best fully-reliable single-model run": consequences avg ~170 chars, options ~150 chars, proper chain format, no name duplication.
- **insight_codex** favors run 36 (qwen3-30b) as "best full-success / best current drop-in": zero option-count violations, zero review-format violations, zero null summaries.
- **Code reviews**: agree run 36 has label-like options (~53 chars avg; e.g. "Government-Subsidized Construction") that violate the "complete strategic approach / self-contained" requirement. Run 35 is closer to baseline depth but has 38/75 consequence chain violations and 73/75 review opener violations.

**Verdict (from source):** Both agents are right about what they measured. Run 36 wins on mechanical schema compliance; run 35 wins on content depth. Neither is ideal without code fixes. For the next iteration, run 35 is the better content template once the schema fixes (B1, B5) are applied, because its consequence depth (~260 chars) already approximates the baseline (~280 chars) and its option length (~133 chars) is close to baseline (~150 chars). Run 36's terse options (~53 chars) are a content regression even if structurally valid.

### Disagreement 2: Run 38 overall quality

- **insight_claude** ranks run 38 as "Tier A" — highest quality output in the batch, pointing to specific domain numbers and tight chain reasoning in successful plans.
- **insight_codex** ranks run 38 as "worst operationally" alongside run 32, citing the placeholder lever in sovereign_identity, blank option, and timeouts.

**Verdict (from source):** Both are correct for their scope. Confirmed in `identify_potential_levers.py:201–211`: for Anthropic models, the `or` fallback at line 204–207 serializes the Pydantic `DocumentDetails` as the assistant turn for calls 2/3, so haiku is conditioned on a clean normalized JSON rather than its raw output. This is the PR #270 fix in action. The sovereign_identity failure (blank option + `"placeholder"` lever) originates in `002-9-potential_levers_raw.json:75` — haiku generated a 6th sentinel lever that propagated through the unguarded flat merge. Run 38 is simultaneously the quality ceiling (silo) and the reliability floor (sovereign_identity, hong_kong, parasomnia).

### Disagreement 3: Root cause of missing activity_overview.json for run 38 haiku

- **insight_claude** attributes this to haiku's `luigi_workers` config being > 1 triggering the `set_usage_metrics_path` race (code_claude S1).
- **code_codex** B5 attributes it to cross-thread event handler contamination: each plan-local `TrackActivity` receives other plans' LLM events under parallel execution.

**Verdict (from source, `runner.py:99–141`):** Both mechanisms are real and concurrent. `set_usage_metrics_path` at line 106 is called outside `_file_lock`, so path writes race when `workers > 1`. Separately, the dispatcher event handlers are global and not filtered by plan identity, so concurrent plan handlers receive each other's events. Either or both can corrupt or suppress per-plan artifacts. This is not a dispute — it is two independent races in the same telemetry path.

---

## Top 5 Directions

### 1. Fix the `consequences` and `options` Pydantic field descriptions to match the actual contract
- **Type**: code fix
- **Evidence**: code_claude B1 + B5; code_codex B1; insight_claude "Run 37 consequence format failure (all plans)" 75/75 levers; insight_codex constraint violation table shows 75/75 for run 37, 38/75 for run 35, 30/75 for run 36; insight_codex "Run 33 also breaks the exact-3-options rule" — 9 two-option levers in parasomnia.
- **Impact**: Every model that weights schema descriptions over or alongside the system prompt immediately gets correct instructions. Run 37-class failures (100% chain failure) should be eliminated or substantially reduced. Run 33-class 2-option failures should stop. Affects all 5 plans × all future model runs. No prompt file change required.
- **Effort**: low — three lines in `identify_potential_levers.py:30–35`
- **Risk**: Minimal. If a model was previously satisfying the system prompt *despite* the wrong schema description, the change reinforces correct behavior. No regression risk.

### 2. Add per-call validator + retry for exact lever count, option count, chain format, and placeholder content
- **Type**: code fix
- **Evidence**: code_claude B2 + B4 + I3 + I4; code_codex B2 + B4 + I3; insight_claude "Lever count violation for gta plan (16 instead of 15)" runs 33/35/37/38; insight_codex run 38 sovereign_identity `placeholder` lever at `002-10-potential_levers.json:71`; run 33 75/75 levers across chain violations not caught.
- **Impact**: Eliminates the gta 16-lever overflow (reproducible across 4 models), the run 38 placeholder in sovereign_identity, and run 33's 2-option tail. A retry on format violation would also give run 37-class models a second chance to produce chain-formatted consequences. The optimizer would stop reporting `status="ok"` for structurally broken outputs.
- **Effort**: medium — requires adding a `@field_validator` on `DocumentDetails.levers`, a sentinel-name filter in the post-merge loop (`identify_potential_levers.py:215–231`), and a chain-marker check.
- **Risk**: Retries add latency per failed call. A malicious or poorly-calibrated model could loop; capping retries at 1–2 mitigates this. The flat merge becoming a filtered merge could produce < 15 levers if all 3 calls for a plan have a violation — downstream steps should handle this gracefully.

### 3. Truncate conversation context for calls 2 and 3 (fresh prompt instead of replaying prior assistant turns)
- **Type**: code fix
- **Evidence**: code_claude B3 + I6; code_codex B3 + I2; insight_claude "Run 38 timeout on complex plans (427 s, 721 s)" — call 3 context reaches ~90 KB for haiku on silo; hong_kong and parasomnia fail across both haiku (timeout) and gpt-oss-20b (truncation), both are the heaviest plans.
- **Impact**: For haiku, call 3 context drops from ~90 KB to ~12 KB (system + plan + name exclusion list). This should eliminate the timeout failure mode on hong_kong and parasomnia, bringing haiku from 3/5 to 5/5 plan coverage. Also reduces template anchoring across calls — models in calls 2/3 are less likely to echo call 1's wording.
- **Effort**: medium — `identify_potential_levers.py:162–175`: for `call_index > 1`, build a new `chat_message_list = [system_message, ChatMessage(USER, user_prompt + "\n\nGenerate 5 MORE levers...")]` instead of appending to the existing list.
- **Risk**: Without the prior assistant turns in context, models may be less aware of what "completely different" means in practice. The name-exclusion list still prevents name reuse, but strategic mechanism diversity may decrease slightly. A test run confirms whether lever diversity holds.

### 4. Prompt addition: concrete consequence chain example + length advisory
- **Type**: prompt change
- **Evidence**: insight_claude H1 + H3; code_codex H3; insight_codex H3; run 37 produces 75/75 plain-prose consequences exactly matching the schema field description style; run 38 averages ~867 chars per consequence vs. ~280 baseline.
- **Impact**: Complements direction #1 (schema fix). Once the schema description no longer teaches plain prose, adding a structural example to the prompt reinforces the chain for models that follow system-prompt instructions. A length advisory (~150–300 chars) discourages both the run-37 collapse (~95 chars) and the run-38 bloat (~867 chars). Expected: run 37 and run 36-class consequence depth moves toward the baseline ~280-char target.
- **Effort**: low — add 2–3 lines to the prompt file after the chain instruction at prompt_1 line 9.
- **Risk**: A concrete example risks template leakage if domain-specific terms are included (seen with prompt_0). A structural abstract example (using placeholders like `[X]`, not real domain words) avoids this. The codex insight confirms "hyphen-Strategy" and "The options fail to consider" over-anchoring from prompt_1 line 19/26 — the new example must use abstract filler.

### 5. Fix telemetry race: move `set_usage_metrics_path` inside `_file_lock`
- **Type**: code fix
- **Evidence**: code_claude S1; code_codex B5 + I5; insight_claude "Run 38 haiku silo has no activity_overview.json"; insight_codex inconsistent call counts across parallel runs.
- **Impact**: Makes per-plan usage metrics and activity artifacts trustworthy under `workers > 1`. This is required for accurate diagnosis of future runs — if usage data is corrupted, the analysis pipeline cannot determine whether a model is timing out vs. simply being slow, or how many tokens a given plan consumes.
- **Effort**: low — `runner.py:106`: move `set_usage_metrics_path(...)` inside the existing `with _file_lock` block at line 108.
- **Risk**: Holding the lock slightly longer during plan setup. With `workers=4` and lock hold time of microseconds, contention is negligible.

---

## Recommendation

**Do direction #1 first: fix the `consequences` and `options` Pydantic field descriptions.**

**Why it is first:**

Direction #1 is a confirmed, proximate cause of the single worst quality failure in this batch. Run 37 (gpt-4o-mini) produced 75/75 levers with plain-prose consequences — 100% failure rate on the core output requirement. The model's output style matches the field description verbatim:

- Field description says: *`"Briefly describe the likely second-order effects or consequences of pulling this lever (e.g., 'Choosing a high-risk tech strategy will likely increase talent acquisition difficulty and require a larger contingency budget.'). 30 words."`*
- Run 37 produces: *`"Choosing a diversified funding strategy will likely enhance financial stability, increase stakeholder engagement, and mitigate risks associated with funding shortages."`*

The causal chain is: structured-output mode injects the Pydantic `Field(description=...)` into the model-facing JSON schema → gpt-4o-mini (and other schema-sensitive models) weight schema-level constraints equally or above system-prompt instructions → the schema example directly overrides the I→S→S chain instruction. This is a code bug, not a model quirk.

It also directly causes the run 33 (llama3.1) 2-option failure in parasomnia via the same mechanism: `options` says "2-5 options", schema permits 2, model produces 2 for the final 9 levers of a long plan.

**The fix — `identify_potential_levers.py:30–35`:**

```python
# BEFORE (lines 30–35):
consequences: str = Field(
    description="Briefly describe the likely second-order effects or consequences of pulling this lever "
                "(e.g., 'Choosing a high-risk tech strategy will likely increase talent acquisition "
                "difficulty and require a larger contingency budget.'). 30 words."
)
options: list[str] = Field(
    description="2-5 options for this lever."
)

# AFTER:
consequences: str = Field(
    description=(
        "Required format: 'Immediate: [direct first-order effect] → "
        "Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → "
        "Strategic: [long-term implication for the project]'. "
        "All three labels and at least one quantitative estimate are mandatory. "
        "Target length: 150–300 words."
    )
)
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option must be a complete "
                "strategic approach (a full sentence with an action verb), not a label."
)
```

Also update `LeverCleaned.options` at line 80–82 identically (it currently also says "2-5 options").

**Expected outcome:** Run 37-class models receive unambiguous chain format instructions at the schema level. Run 33-class 2-option truncations stop. All other models that correctly followed the system prompt are unaffected — the schema change reinforces correct behavior. This requires no prompt file change, no workflow change, and no model-specific logic.

---

## Deferred Items

**Do next (after #1 is re-run and confirmed):**

- **Direction #2 (validator + retry):** Highest systemic value once the schema is fixed, but adds complexity. The run after the B1/B5 fix will show whether chain compliance improves for run 37-class models; if compliance reaches ~90%+, the retry layer becomes an edge-case guard rather than a primary correctness mechanism.

- **Direction #3 (truncate context for calls 2/3):** Should be done before running haiku on the full corpus again. The 427 s and 721 s timeouts on hong_kong and parasomnia are predictable. Until context is truncated, haiku will continue to fail on these plans regardless of prompt or schema changes.

- **Direction #4 (prompt consequence example + length advisory):** Low-effort complement to direction #1. Should be bundled into the next prompt iteration after #1 is re-run, not before — running #1 alone first shows its isolated effect clearly.

- **Direction #5 (telemetry race fix):** Low effort, high diagnostic value. Should be fixed before the next multi-worker run so activity artifacts are trustworthy. Does not affect output quality.

**Lower priority / later:**

- **code_claude I6 / code_codex I2 (plan-context anchor in calls 2/3):** The phrase `"For the same plan described above"` helps prevent context drift. Worth adding alongside direction #3 (context truncation), not independently.

- **code_codex S2 (cross-call mechanism diversity):** The follow-up prompt bans name reuse but not mechanism reuse. The "hyphen-Strategy" naming pattern and semantic near-duplication across calls are real quality issues, but they are secondary to the chain-format and option-count failures.

- **Retire run 32 model (nvidia-nemotron-3-nano-30b-a3b):** It has now failed in runs 24, 25, and 32 with JSON extraction errors. The prompt change had zero effect. This model should be removed from the evaluation set to avoid wasting compute on a non-viable candidate.

- **Investigate gpt-4o-mini consequence failure depth:** If direction #1 does not fix run 37, add a structural chain example to the prompt (direction #4 component). If it still fails, deprioritize gpt-4o-mini in favor of run 35 (gpt-5-nano) or run 36 (qwen3) as the operational base.
