# Synthesis

## Cross-Agent Agreement

Only one insight file (`insight_claude.md`) and one code review file (`code_claude.md`) are present — both from the same model. The two files are highly consistent:

- **PR verdict: CONDITIONAL.** Both files agree the new fields (`lever_type`, `decision_axis`) add genuine value and are correctly implemented for 5–6 of 7 models, but the PR introduced exactly 3 new plan failures.
- **Root cause of N1 (haiku truncation):** `max_tokens: 16000` in `anthropic_claude.json` exceeds haiku's real API cap (~8,192 tokens). PR #346's additional per-lever payload (~300–400 chars per lever) pushed two large plans over the effective ceiling. Both files identify this as B2/S1.
- **Root cause of N2 (llama3.1 rejection):** The `normalize_lever_type` validator hard-rejects any non-enumerated string. `max_validation_retries=0` at the call site means there is no retry opportunity. `coalition_building` is semantically valid for a sovereign-identity project but was rejected with no recovery path. Both files identify this as B1.
- **Template leakage ("The options [verb]") is pre-existing and unresolved** by this PR: rates remain 50–100% across most models. Both files agree it is a carry-forward issue.
- **`decision_axis` "whether" variant (haiku, 24%):** Both files flag it as an ambiguity in the spec — neither the validator nor the system prompt prohibits or explicitly permits binary framing.
- **`options` field description vs. validator mismatch (B4):** "Exactly 3, no more, no fewer" contradicts the asymmetric validator that only checks the lower bound. Both files flag it as a pre-existing misleading instruction.
- **Timeout not actually enforced (B3 in code review):** `with _TPE()` blocks on `__exit__` even after `TimeoutError`. Only the code review flags this explicitly.

## Cross-Agent Disagreements

No substantive disagreements exist between the two files. The only difference is scope: the code review adds two findings absent from the insight file (B3 timeout, S2 global dispatcher) because the code review reads `runner.py` directly. Both are confirmed by reading the source:

- **B3 (timeout)** — `runner.py:492–503` confirmed: `with _TPE(max_workers=1) as executor:` wraps the submit + `future.result(timeout=...)`. On `TimeoutError`, the code creates the correct `PlanResult` but then falls through to `with` block exit which calls `executor.shutdown(wait=True)`, blocking until the thread finishes. **Confirmed valid bug.**
- **S2 (global dispatcher)** — `runner.py:187–192` confirmed: `get_dispatcher()` returns a global singleton. In parallel mode, each worker adds its own handler to the same object. **Confirmed as a structural fragility, low immediate risk.**
- The insight file suggests "increase `max_tokens` to accommodate the new fields" (C1) — but `anthropic_claude.json` already sets `max_tokens: 16000`, which is *above* the haiku API cap of ~8,192. The real fix is not to increase the configured number further but to document the discrepancy and reduce response size. The code review correctly identifies this distinction (I2). **Code review is right; insight file's C1 recommendation is confused.**

## Top 5 Directions

### 1. Add fuzzy lever_type normalization and enable validation retries
- **Type**: code fix
- **Evidence**: B1 (code_claude), N2 (insight_claude), E3. Confirmed in source: `identify_potential_levers.py:126–135` does `strip().lower()` then immediately raises `ValueError` on any non-enumerated value. `LLMExecutor` supports `max_validation_retries` (defaulting to 0) but `IdentifyPotentialLevers.execute()` does not set it.
- **Impact**: Directly fixes 1 new PR-caused failure (llama3.1, `sovereign_identity`). More importantly, establishes a recovery path for any future schema-validation rejection across all models. As the lever schema grows, the probability of at-least-one-bad-type-per-call increases; without normalization, each schema addition multiplies failure risk.
- **Effort**: Low. Two independent sub-fixes: (a) add a `_LEVER_TYPE_ALIASES` dict at module level and a three-line normalization pass before `raise ValueError`; (b) pass `max_validation_retries=1` at the `LLMExecutor` construction site in `execute()`. Neither change touches the prompt or the downstream pipeline.
- **Risk**: Low. The alias table is additive; it can only recover plans that currently fail, not break plans that currently succeed. Enabling one retry adds at most one extra LLM call per failing lever set.

---

### 2. Document haiku max_tokens discrepancy and cap levers-per-call at 5
- **Type**: code fix (config) + prompt change
- **Evidence**: B2 (code_claude), N1 (insight_claude), E1, E2. Confirmed: `anthropic_claude.json:14,34` both set `"max_tokens": 16000`; haiku's real API output ceiling is ~8,192 tokens. PR #346 added ~300–400 chars per lever; at 7 levers × 3 calls the payload grew ~6,000–8,000 chars per plan, pushing large plans over the ceiling.
- **Impact**: Directly fixes 2 of the 3 new PR-caused failures (haiku, `gta_game` and `silo`). Config correction makes the discrepancy visible to all developers reading the file. Capping levers at 5 in the system prompt ("Propose exactly 5 levers") reduces per-plan output by ~28% for haiku, moving large plans safely back under the ceiling. Note: the config fix alone (changing 16000 → 8192) does not prevent truncation — the API was already clamping to ~8,192. Only reducing output size solves the underlying problem.
- **Effort**: Low–Medium. Config line change is trivial. System prompt change from "5 to 7 levers" to "5 levers" is a one-line edit but should be validated against non-haiku models (which may generate fewer high-quality levers if constrained too tightly). A safer variant is to change DocumentDetails description to "Propose 5 levers" while keeping the comment that over-generation is tolerated.
- **Risk**: Low. Fewer levers per call means slightly fewer raw candidates before deduplication, but the pipeline already handles extras via `DeduplicateLeversTask`. Non-haiku models are unaffected structurally; their per-call token usage is well within limits.

---

### 3. Address "The options [verb]" template leakage in review fields
- **Type**: prompt change
- **Evidence**: N7 (insight_claude). Current rates: gpt-oss-20b 50%, gpt-5-nano 61%, qwen3 88%, gpt-4o-mini 100%, gemini-flash 92%, haiku 47%. Three domain-specific examples already exist in system prompt section 5 (agriculture, light-rail, catastrophe-risk). `OPTIMIZE_INSTRUCTIONS` documents this as "template-lock migration" and identifies the agriculture example as the correct structural template. Despite these measures, rates remain high across all models.
- **Impact**: This is the highest-frequency content quality issue in the dataset — affects the majority of levers across 6 of 7 models. The `review` field is supposed to provide a sharp, domain-specific critique; instead, most models produce a generic "The options [verb]" opener that could fit any project. This degrades the downstream scenario picker's ability to reason about genuine lever weaknesses. Fixing it improves every successful plan, not just recovering failed ones.
- **Effort**: Medium. The current approach (examples) has failed to break the pattern. The effective fix requires removing the transitional opener entirely from the format description and replacing the opening instruction with "Start directly with the tension, not with 'The options'." Adding a fourth, non-portable example from a technology domain would also diversify the available templates.
- **Risk**: Low–Medium. Prompt-only change. Some models may shorten reviews excessively if the opener is removed; the 50-char minimum validator provides a floor. The change should be validated across all 7 models before rolling out.

---

### 4. Clarify decision_axis format for binary decisions
- **Type**: prompt change
- **Evidence**: N5, S3 (insight_claude); I4, S3 (code_claude). Confirmed in source: `identify_potential_levers.py:249` specifies the template "This lever controls X by choosing between A, B, and C." but the validator at lines 137–143 only checks `len(v) >= 20`. Haiku produces "This lever controls whether..." for 17/70 levers (24%), concentrated in the `sovereign_identity` plan which has genuinely binary decision points. `OPTIMIZE_INSTRUCTIONS` warns against English-only validators; the decision_axis template is itself English-only.
- **Impact**: Eliminates format ambiguity for downstream consumers. If the scenario picker or any downstream step parses "by choosing between" to extract option names, the 24% "whether" variant silently breaks that parsing. Explicit guidance prevents inconsistent format from polluting structured output. Affects haiku primarily but is a spec clarification for all models.
- **Effort**: Low. One-line addition to system prompt section 2: "For binary decisions, write: 'This lever controls X by choosing between A or B.'" This explicitly permits the binary form with a structure that can be uniformly parsed.
- **Risk**: Very low. Purely additive guidance. Does not change the validator, does not affect successful plans.

---

### 5. Align options field description with the asymmetric validator
- **Type**: code fix (prompt-facing description)
- **Evidence**: B4 (code_claude). Confirmed: `identify_potential_levers.py:112` says "Exactly 3 options for this lever. No more, no fewer." but `check_option_count` at lines 158–170 only enforces `len(v) >= 3`. Same mismatch in `LeverCleaned` at line 229.
- **Impact**: Removes a misleading instruction. When the LLM generates 4 options, it believes it has violated the schema; this may cause self-correction, hallucination of deletions, or erratic behavior in weaker models that over-comply with "no more, no fewer." The downstream `DeduplicateLeversTask` is designed to handle extras, so the asymmetric lower-bound-only check is intentional. Making the description honest ("At least 3 options; extras are fine and will be trimmed downstream") prevents model confusion without changing behavior.
- **Effort**: Very low. Two field description changes in one file.
- **Risk**: Near-zero. The validator behavior is unchanged. Some models that currently produce exactly 3 may start generating 4, which is acceptable.

## Recommendation

**Do direction 1 first: add fuzzy lever_type normalization + enable `max_validation_retries=1`.**

**Why first:** This is the most tractable fix with the clearest implementation path and the highest ratio of impact to effort. It targets a direct PR regression in a single file, using infrastructure that already exists and is tested. The alias table approach (a plain Python dict) adds no dependencies and cannot make any currently-passing plan fail. Enabling `max_validation_retries=1` turns a hard rejection into a recoverable retry for the entire class of "model invented a plausible but non-enumerated type" errors — a failure mode that will recur whenever the lever schema is extended.

**Specific changes:**

**File: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`**

1. Add an alias dict before the `Lever` class (around line 82):

```python
_LEVER_TYPE_ALIASES: dict[str, str] = {
    "coalition_building": "governance",
    "stakeholder_engagement": "governance",
    "partnership": "governance",
    "outreach": "dissemination",
    "communication": "dissemination",
    "technical": "methodology",
    "tech": "methodology",
    "research": "methodology",
    "ops": "operations",
    "operational": "operations",
    "delivery": "execution",
    "implementation": "execution",
}
```

2. Modify `normalize_lever_type` (lines 128–135) to consult the alias dict before raising:

```python
@field_validator('lever_type', mode='after')
@classmethod
def normalize_lever_type(cls, v):
    normalized = v.strip().lower()
    if normalized in cls.VALID_LEVER_TYPES:
        return normalized
    alias = _LEVER_TYPE_ALIASES.get(normalized)
    if alias:
        logger.info(f"lever_type {v!r} normalized to {alias!r} via alias")
        return alias
    raise ValueError(
        f"lever_type must be one of {sorted(cls.VALID_LEVER_TYPES)}, got {v!r}"
    )
```

3. In `IdentifyPotentialLevers.execute()` (line 294), the method receives an `LLMExecutor` from the caller — `max_validation_retries` is set at construction time by the caller, not inside `execute()`. Verify that `runner.py` constructs the executor with at least `max_validation_retries=1` for this step. If the runner uses a shared executor, add a note in `OPTIMIZE_INSTRUCTIONS` that validation retries should be enabled for this step.

**Direction 2 should be done in the same PR** as it is a simple config correction: change `"max_tokens": 16000` to `"max_tokens": 8192` on both haiku entries in `llm_config/anthropic_claude.json` (lines 14 and 34), with a comment explaining this is the model's actual API output cap. Additionally, add a note to `OPTIMIZE_INSTRUCTIONS` (after line 80) documenting that adding new fields to per-lever output increases response size and can push verbose models past their effective output ceiling.

## Deferred Items

- **Direction 3 (template leakage)** — High-frequency content quality issue but requires prompt experimentation to fix. Should be the next PR after the reliability fixes. Suggested approach: replace "A short critical review — name the core tension" opener in section 5 with "Write the core tension first, as a statement, without starting with 'The options'" and add a technology-domain fourth example to diversify the template pool.

- **Direction 4 (decision_axis binary)** — Minor spec clarification. Add one line to system prompt section 2 permitting "choosing between A or B" for binary decisions. Low urgency since the 20-char validator accepts all current outputs.

- **Direction 5 (options description)** — One-line field description fix. Can be bundled into any future PR touching the schema.

- **B3 (timeout not enforced in runner.py)** — Real bug: `with _TPE()` blocks on `__exit__` even after `TimeoutError`. Fix: call `executor.shutdown(wait=False)` after catching `TimeoutError` rather than relying on the `with` block's exit. Deferred because it is not caused by PR #346 and does not manifest in the current test set (no plans hit the timeout).

- **S2 (global dispatcher in parallel mode)** — Structural fragility in `runner.py`. Benign today because `track_activity.jsonl` is deleted in `finally`. Should be fixed before any use of the dispatcher for persistent per-plan attribution. Deferred as low urgency.

- **S4 (case-sensitive duplicate lever detection)** — `seen_names` set uses exact case. Fix: `seen_names.add(lever.name.lower())` and `if lever.name.lower() in seen_names`. Low urgency since the downstream `DeduplicateLeversTask` catches semantic duplicates anyway.

- **I7 (lever_type diversity check)** — Post-processing warning when any single type exceeds ~33% of total levers. Useful development-time diagnostic for catching N6-style governance bias. Low urgency; no failures currently caused by this.

- **Q5 from insight file (multilingual decision_axis)** — When PlanExe receives non-English prompts, the model may respond with a valid decision_axis in the source language. The 20-char validator passes these; only downstream consumers parsing "by choosing between" would fail. Should be addressed when internationalisation is prioritised.
