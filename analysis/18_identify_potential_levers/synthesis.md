# Synthesis

## Cross-Agent Agreement

All four agents (insight_claude, insight_codex, code_claude, code_codex) agree on the following:

1. **PR #297 verdict: KEEP.** The simplification produced large, measurable improvements: chain-format consequences eliminated (614→0), unsupported % claims collapsed 97% (864→25), field bleed eliminated (66→0), 100% plan success rate (first ever clean sweep), gpt-oss-20b parasomnia resolved after 3 consecutive failures.

2. **Bracket placeholders in `review_lever` are a live leakage vector.** Both code reviewers flag the self-contradiction between showing `[Tension A]`, `[Tension B]`, `[specific factor]` as the target format while simultaneously prohibiting bracket templates. Both cite run-33 (gpt-5-nano) with 36 bracket placeholder instances as direct evidence. `review_lever` field description at `identify_potential_levers.py:51–57` still shows the bracketed template.

3. **llama3.1 has a persistent multi-call quality degradation.** Analysis/17 saw bracket-wrapped consequences in call-3; analysis/18 sees label-only options in call-2 (7/21 levers, all concentrated in one call group). The root cause — multi-call context crowding, no quality reinforcement in later-call prompts — is flagged by all agents.

4. **Summary field description contradicts the prompt format.** The Pydantic description says "Are these levers well picked? Are they well balanced?" while prompt_4 requires a narrow `Add '[full strategic option]' to [lever]` form. Result: 0 exact matches in runs 32–37 (0/90 plans). All agents flag this.

5. **Post-parse quality gate is absent.** Label-only options, fabricated percentages, and bracket placeholders pass through Pydantic validation undetected because validators only check option count and marker presence. Both code reviewers flag this.

---

## Cross-Agent Disagreements

### Disagreement 1: What is "B1"?

- **code_claude** names B1 as: *`Lever.consequences` Pydantic field description still mandates the old `Immediate → Systemic → Strategic` chain and mandatory quantification*, contradicting prompt_4. This is the highest-priority finding in that review.
- **code_codex** names B1 as: *the bracketed `review_lever` example contradicting the bracket prohibition*. code_codex does not call out the stale `consequences` field description separately.

**Who is right?** Both are real bugs. Source code confirms both:
- `identify_potential_levers.py:34–46`: `Lever.consequences` description says `"Required format: 'Immediate: [direct first-order effect] → Systemic: [second-order impact with a measurable indicator, e.g. a % change or cost delta] → Strategic: [long-term implication for the project]'. All three labels and at least one quantitative estimate are mandatory."` — **verbatim stale text confirmed**.
- `identify_potential_levers.py:51–57`: `review_lever` description shows `[Tension A]`, `[Tension B]`, `[specific factor]` — **bracket template confirmed**.
- `identify_potential_levers.py:130–139`: `LeverCleaned.consequences` has the identical stale chain description — **confirmed stale**.
- `identify_potential_levers.py:154–196`: `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant still mandates `Immediate → Systemic → Strategic`, `% change`, `conservative → moderate → radical`, and "Radical option must include emerging tech/business model" — **all four confirmed stale**.

The code_claude B1 (stale `consequences` description) is the broader bug: it affects EVERY model on EVERY call via the JSON schema, explaining llama3.1's fabricated percentages (N2) and sub-header format (N3). code_codex's B1 (bracket leakage) explains run-33's 36 placeholder instances. Both are real; code_claude B1 has wider model impact.

### Disagreement 2: Is run-33 bracket leakage a new regression or expected behavior?

- **insight_claude** does not independently identify run-33 bracket leakage as a distinct issue (focuses on llama3.1).
- **insight_codex** explicitly identifies run-33 (gpt-5-nano) as having 36 placeholder instances, making it the worst-remaining placeholder issue.
- **code_claude** and **code_codex** both confirm this is caused by the bracket template in `review_lever` field description + prompt_4 section 4 contradicting section 5.

**Who is right?** code_claude and code_codex are right. Source code at `identify_potential_levers.py:51–57` and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT:179–184` both show bracket placeholders actively present, while the prohibition at prompt_4 section 5 says "NO placeholder consequences or bracket-wrapped templates." The double signal (example + prohibition) is a real contradiction.

### Disagreement 3: Is the `break → continue` control-flow change in PR #297 significant?

- **code_codex** (S1) flags this as undeclared scope creep in a prompt-only PR.
- **code_claude** does not mention this change.

**Assessment:** Source code at `identify_potential_levers.py:263–282` shows the current behavior: on call-2/3 failure, continue to next call rather than breaking. This is a real undeclared change but its operational impact is ambiguous — it could recover more levers or generate more weak content. Not a blocker, but worth noting for reproducibility.

---

## Top 5 Directions

### 1. Update stale Pydantic field descriptions and hardcoded constant to match prompt_4
- **Type**: code fix
- **Evidence**: code_claude B1+B2+B3+I1+I2+I3; confirmed by source code inspection of `identify_potential_levers.py:34–46, 130–139, 154–196`. The `Lever.consequences` description still mandates the old chain format with mandatory quantification. `LeverCleaned.consequences` is identically stale. `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant still contains all four removed requirements.
- **Impact**: The JSON schema sent on every structured LLM call contradicts prompt_4. Strong models (haiku, gemini, qwen3) override the contradiction via the system prompt; weaker models (llama3.1) do not — explaining N2 (fabricated %) and N3 (sub-header format) which persist in analysis/18. Updating all three removes the contradictory signal for all models on all calls. The `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` fix ensures `python -m` ad-hoc testing produces valid behavior.
- **Effort**: low — three string/block updates in one file
- **Risk**: very low — removing a contradiction cannot regress the models that already follow prompt_4; it only helps weaker models

### 2. Replace bracket placeholders in review_lever description and prompt with concrete non-bracket examples; strengthen validator to reject brackets
- **Type**: code fix (schema description + validator)
- **Evidence**: code_claude B5+I7; code_codex B1+I1; confirmed at `identify_potential_levers.py:51–57` and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT:179–184`. Run-33 (gpt-5-nano) produced 36 bracket instances despite the prompt prohibition, because both the field description and the constant still show `[Tension A]`, `[Tension B]`, `[specific factor]` as the target format. The prohibition and the example contradict each other.
- **Impact**: Directly eliminates the leakage vector for run-33. Review exact-format compliance is currently 90.3% (after); removing the contradictory bracket signal should push it above 93%. Also prevents future runs with similar models from producing unfillable placeholders in final outputs.
- **Effort**: low — replace bracket text with a concrete literal example; extend `check_review_format` to reject `[` or `]`
- **Risk**: low — a stronger validator may cause initial retry on weaker models, but the rejection is correct behavior

### 3. Align `summary` field description with prompt_4's concrete format requirement
- **Type**: code fix (schema description)
- **Evidence**: code_claude S2+I6; code_codex I5; confirmed at `identify_potential_levers.py:113–115`. Current description: "Are these levers well picked? Are they well balanced?... Point out flaws. 100 words." Prompt_4 requires: `Add '[full strategic option]' to [lever]`. Result: 0/90 exact-format matches in runs 32–37 (only 11/15 in run-31 due to llama3.1 coincidence).
- **Impact**: Affects all 7 models. The `summary` field is currently a noisy open-ended critique rather than the structured one-line recommendation the prompt intends. Aligning the field description would recover exact-format compliance without any prompt change. The `summary` is used in downstream analysis; a consistent format makes it parseable programmatically.
- **Effort**: very low — single string replacement
- **Risk**: very low

### 4. Add option minimum-length validator and reinforce option quality requirements in multi-call user message
- **Type**: code fix (validator + multi-call prompt text)
- **Evidence**: code_claude S1+S3+I5; code_codex B3+I3; insight_claude N1+C1+H2. llama3.1 call-2 produced 7/21 levers with label-only options (2–4 words like "Centralized Authority", "Maximize Efficiency") that pass current validation undetected. Root causes: (a) no minimum-length validator on options, (b) multi-call user message only says "generate more with different names" without reinforcing quality. Additionally, the ever-growing prior-lever name blacklist prepended to calls 2/3 crowds context for weaker models.
- **Impact**: A minimum-word validator (e.g., ≥8 words per option) would convert label-only options into retryable validation errors rather than silent quality failures. Reinforcing option quality in the call-2/3 message would help llama3.1 specifically. Adaptive loop (stop early when enough levers, cap blacklist length) would reduce later-call context pressure for all weaker models. Together these address the single remaining model-specific degradation in analysis/18.
- **Effort**: medium — validator is simple; adaptive loop refactor is more involved
- **Risk**: medium — new validator triggers more retries for llama3.1 initially; need to ensure the retry budget is sufficient before failing

### 5. Fix thread safety for `set_usage_metrics_path` in runner.py
- **Type**: code fix
- **Evidence**: code_claude B4+I4; code_codex S3. `runner.py:106` calls `set_usage_metrics_path` outside the `_file_lock`, while the comment on lines 97–98 claims the lock covers configuration. With `workers > 1`, two threads can overwrite each other's path setting, routing usage metrics to the wrong plan's output file. Currently unexploited because the default is `workers=1`, but the bug is latent in the code.
- **Impact**: Silent data corruption if any experiment or production config sets `luigi_workers > 1`. Would cause misleading token-cost attribution across plans. Not affecting current runs.
- **Effort**: medium — need to either extend the lock scope or move to thread-local storage
- **Risk**: low — the fix only changes locking scope; the happy path (workers=1) is unaffected

---

## Recommendation

**Do Direction 1 first: update the stale Pydantic field descriptions and hardcoded constant.**

**Why first:** This is the most widespread incomplete piece of PR #297. The PR updated the external prompt file but left the `Lever.consequences` field description sending the old mandatory chain + mandatory % instruction to every model on every call via the JSON schema. Strong models ignore it; weaker models (llama3.1) obey it, which directly explains every llama3.1-specific issue in analysis/18 (N2 fabricated %, N3 sub-headers). Fixing this removes a contradictory signal from 100% of calls without any risk of regression.

**What to change — three locations in `identify_potential_levers.py`:**

**1. `Lever.consequences` field description (lines 34–46):**
```python
consequences: str = Field(
    description=(
        "Describe the direct effect of pulling this lever, then at least one downstream "
        "implication or trade-off. Do NOT fabricate percentages, cost estimates, or "
        "statistics unless the exact number appears in the project context. "
        "Do NOT use 'Direct Effect:', 'Downstream Implication:', or any sub-headers. "
        "Target length: 2–4 sentences."
    )
)
```

**2. `LeverCleaned.consequences` field description (lines 130–139):** Apply the same replacement (output-only class, no model impact, but removes misleading documentation).

**3. `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant (lines 154–196):** Replace the constant body with the content of prompt_4, or at minimum remove the four stale requirements:
- Remove: `"Chain three SPECIFIC effects: 'Immediate: [effect] → Systemic: [impact] → Strategic: [implication]'"` (line 163)
- Remove: `"Include measurable outcomes: ... a % change, capacity shift, or cost delta"` (line 164)
- Remove: `"Show clear progression: conservative → moderate → radical"` (line 169)
- Remove: `"Radical option must include emerging tech/business model"` (line 193)

The cleanest fix is to load prompt_4 from the same file the runner uses, so the constant and the production path stay in sync automatically. If that's too complex, replace the constant body with a minimal version matching prompt_4's intent.

---

## Deferred Items

**Direction 2 (bracket placeholder fix)** — do immediately after Direction 1. It's low effort and directly plugs the run-33 leakage vector. Replace `[Tension A]`/`[Tension B]`/`[specific factor]` in both the `review_lever` field description and the `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant with a concrete literal example, e.g.: `"Controls short-term execution speed vs. long-term architectural risk. Weakness: The options fail to consider regulatory approval timelines."` Then extend `check_review_format` to reject `[` or `]` in the output.

**Direction 3 (summary description alignment)** — very low effort, high consistency gain. Change the description to match what prompt_4 requires. Worth doing in the same commit as Direction 2.

**Direction 4 (option minimum-length validator + adaptive multi-call loop)** — medium effort, important for llama3.1's remaining degradation but lower urgency after Direction 1 removes the contradictory schema signal. Schedule after confirming that the stale field description update alone doesn't recover llama3.1's call-2 options.

**Direction 5 (thread safety)** — latent bug, not observable at workers=1. Defer unless any config or test begins using workers > 1.

**C2 / insight_claude (EOF retry pattern for gpt-oss-20b)** — the prompt change resolved parasomnia for now, but adding `"eof while parsing"` to `_TRANSIENT_PATTERNS` remains a defensive improvement for future plans with large context. Low priority given the current 100% success rate.

**insight_codex C3 (quality telemetry per run)** — chain-count, placeholder-count, unsupported-number-count per run would make future PR evaluations much faster. Valuable but out of scope for immediate fixes.

**insight_claude H3 (option diversity measurement)** — the removal of `conservative → moderate → radical` likely improved option diversity, but this is not yet quantified. A human evaluation of option distinctness across runs 30 vs 37 would confirm hypothesis H3 and inform whether future prompt refinements should preserve or add back any structural guidance.

**code_codex S1 (undeclared `break → continue` control-flow change)** — the scope creep in PR #297 should be documented in a follow-up commit message or PR description for experiment reproducibility, even if the behavior change is beneficial.
