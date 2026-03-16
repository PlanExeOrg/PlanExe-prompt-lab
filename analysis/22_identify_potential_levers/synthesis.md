# Synthesis

## Cross-Agent Agreement

Only one agent (Claude) produced both the insight and code-review files for this cycle.
The two analyses are fully consistent and reinforce each other:

- **PR #316 is directionally correct but incomplete.** The external prompt file was
  updated; the Pydantic `Lever.review_lever` field description and the hardcoded
  `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant were not.
- **Structural contamination is eliminated.** "Weakness:" no longer leaks into
  `consequences` (run 59 → runs 60–66). This is the PR's primary achievement.
- **Template lock persists, just with a different template.** Runs 60–66 show 90–100%
  of reviews starting "This lever governs/manages the tension between X and Y, but…"
  — as rigid as the old "X vs Y. Weakness: Z." pattern it replaced.
- **Two concrete missed code changes** (B1, B2) are independently confirmed by both
  analyses as the root-cause gap in PR #316.
- **Verdict: CONDITIONAL KEEP** — the fix is valid; the Pydantic schema mismatch must
  be closed and the template-lock issue requires a follow-up prompt change.

## Cross-Agent Disagreements

None — the single agent's insight and code-review findings are fully consistent.
Claims were verified against source code; all confirmed as accurate.

---

## Top 5 Directions

### 1. Fix `Lever.review_lever` Pydantic field description (B1)
- **Type**: code fix
- **Evidence**: Code review B1; confirmed at `identify_potential_levers.py:92–100`.
  The field description still reads `"Two sentences. First sentence names the core
  tension… Example: 'Controls centralization vs. local autonomy. Weakness: The options
  fail to account for transition costs.'"` — the old pre-PR #316 format. When
  llama_index submits a structured LLM request it sends field descriptions as part of
  the JSON schema, so every model call sees *both* the new single-sentence example
  (from the external prompt file) and the old "Two sentences / Weakness:" instruction
  (from the schema). This contradiction is the root-level code cause of: run 60 partial
  recoveries, template lock, and the verbatim-copy failure mode.
- **Impact**: All models on all runs using structured LLM calls. Fixing this eliminates
  the contradictory signal sent to the model on every call, reducing residual validation
  failures and potentially weakening the template-lock hold.
- **Effort**: low — single field description rewrite, ~5 lines.
- **Risk**: Minimal. The field description change only affects what the model reads
  from the JSON schema; it does not change validation logic.

### 2. Update hardcoded `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant (B2)
- **Type**: code fix
- **Evidence**: Code review B2; confirmed at `identify_potential_levers.py:214–218`
  (inside the constant). Section 4 "Validation Protocols" of the hardcoded constant
  still contains:
  `"First sentence names the core tension. Second sentence identifies a weakness.
  Example: "Controls centralization vs. local autonomy. Weakness: The options fail to
  account for transition costs."`. Any call that omits `system_prompt=` (the `__main__`
  test block, unit tests, future callers) will use the old format. This silently
  diverges from production runs and makes standalone testing misleading.
- **Impact**: Test correctness; prevents silent divergence between production and
  developer/test runs.
- **Effort**: low — one-paragraph rewrite inside the constant string.
- **Risk**: Minimal. The constant is a fallback; production uses the external file.
  Updating it only affects standalone invocations.

### 3. Provide 2–3 structurally varied `review_lever` examples to break template lock (H1/I3)
- **Type**: prompt change (external prompt file → prompt_7)
- **Evidence**: Insight N1, code review I3; confirmed across runs 60–66: 90–100% of
  reviews open with "This lever governs/manages the tension between X and Y, but…"
  The model pattern-matches on the single example and applies it universally — the
  same behaviour the old "X vs Y. Weakness: Z." format exhibited. A single example
  cannot prevent template lock in small models like llama3.1.
- **Impact**: Content quality for all 35 plans across all 7 runs (60–66). Diverse
  review phrasing means reviewers can distinguish genuinely high-stakes levers from
  minor tactical choices. This is a content-quality improvement that affects every
  successful plan, outweighing structural fixes that address only a handful of
  validation failures.
- **Effort**: medium — requires drafting 2 additional structurally distinct examples
  and updating both the external prompt file and (after direction 1 and 2 are done)
  the Pydantic field description.
- **Risk**: New examples could themselves become new templates if not sufficiently
  varied. Must use structurally distinct openings (direct assertion, rhetorical framing,
  trade-off contrast) rather than variations on the same sentence shape.

### 4. Add validator for label-style options (I1/C2)
- **Type**: code fix
- **Evidence**: Insight N3; code review I1; confirmed at
  `identify_potential_levers.py:115–126` — `check_option_count` validates only
  `len(v) == 3`, not content quality. Run 60 gta_game call-1 has options `"Hub-and-Spoke"`,
  `"Satellite Studios"`, `"Co-Working Spaces"` — single-phrase labels with no verb.
  These survive into the final output. The prompt explicitly prohibits label-style
  options, but the validator does not enforce this.
- **Impact**: Prevents low-quality options from downstream tasks that assume each
  option is an actionable strategic sentence. Affects all models/plans where call-1
  produces label-only outputs (~2–5 per run average for llama3.1).
- **Effort**: low-medium — one new `@field_validator` on `Lever.options`, similar in
  form to `check_option_count`. Must be structural (e.g., token count ≥ 6 or char
  count ≥ 30), not English-keyword-based, per OPTIMIZE_INSTRUCTIONS guidance on
  language-agnostic validation.
- **Risk**: May cause more `partial_recovery` events if the threshold is set too
  aggressively. Should use a permissive lower bound (e.g., ≥ 25 chars) to avoid
  rejecting non-English plans with legitimately compact options.

### 5. Fix `set_usage_metrics_path()` race condition in `runner.py` (B3)
- **Type**: code fix
- **Evidence**: Code review B3; confirmed at `runner.py:107–110`. The comment at
  lines 98–99 says the lock is held to avoid cross-thread interference, but
  `set_usage_metrics_path(...)` is called on line 107, **before** the `with _file_lock:`
  block at line 109. With `workers > 1`, two threads can simultaneously overwrite the
  global metrics path, writing one plan's LLM usage events to another plan's file.
- **Impact**: Latent — `ollama-llama3.1` uses `workers=1` so the bug is not currently
  active. However, any model with `luigi_workers > 1` (GPT-4o, Gemini, etc.) would
  silently corrupt per-plan usage metrics.
- **Effort**: low — move line 107 inside the `with _file_lock:` block.
- **Risk**: None — purely a locking order correction with no semantic change for
  single-worker runs.

---

## Recommendation

**Fix B1 first: update the `Lever.review_lever` Pydantic field description.**

**Why first:** It is the single most impactful incomplete fix from PR #316 and takes
~5 minutes to implement. The code sends the Pydantic field description to the model
as part of the JSON schema on every structured LLM call — this is not a fallback or a
test path, it is live production behaviour. The current description explicitly instructs
the model to produce "Two sentences" with a "Weakness:" clause using the old example,
directly contradicting the new single-sentence format introduced in the external prompt
file. This is the root-level code cause of the residual template inconsistency observed
in run 60 partial recoveries and is the most probable cause of the verbatim-copy failure.

**What to change:**

File: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`, lines 92–100.

Replace:
```python
review_lever: str = Field(
    description=(
        "Two sentences. First sentence names the core tension this lever "
        "controls. Second sentence identifies a weakness the options miss. "
        "Example: 'Controls centralization vs. local autonomy. "
        "Weakness: The options fail to account for transition costs.' "
        "Do not use square brackets or placeholder text."
    )
)
```

With (matching the current prompt_6 single-flowing-sentence format):
```python
review_lever: str = Field(
    description=(
        "A short critical review — name the core tension, then identify a weakness "
        "the options miss. Write it as a single flowing sentence. "
        "Example: 'This lever governs the tension between centralization and local "
        "autonomy, but the options overlook transition costs.' "
        "Do not use square brackets or placeholder text."
    )
)
```

Do the same for `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (B2) in the same commit —
it is the same text in the same file and the two changes are inseparable. Update
section 4 "Validation Protocols" of the constant from the old two-sentence/Weakness
format to the same single-sentence format. Both changes together close the complete
schema contradiction left by PR #316 and bring all three instruction sources (external
prompt, Pydantic schema, hardcoded constant) into alignment.

---

## Deferred Items

- **I3 / H1 (2–3 varied review_lever examples):** High-value follow-up after B1+B2
  are fixed. Once the schema contradiction is closed, template lock is the remaining
  top issue. Draft examples should use structurally distinct openings, e.g.:
  - (current) "This lever governs the tension between X and Y, but the options overlook Z."
  - "The central trade-off is X vs. Y; none of the options address Z, which could
    undermine either path."
  - "Prioritizing X over Y carries hidden costs: Z is absent from all three options."

- **H2 (explicit prohibition against verbatim example copy):** Add to section 5
  (Prohibitions) in the system prompt: "Do not copy any example text verbatim into
  your output." Addresses the run 60 gta_game verbatim-copy failure (N2 / C1 in
  insight). Low effort; pair with I3.

- **I1 / C2 (label-style option validator):** Direction 4 above. Implement after
  prompt changes are stable so the threshold can be calibrated against new-format
  outputs.

- **I4 (remove or require `DocumentDetails.summary`):** The `summary` field is
  required in the schema, consumes model tokens, but is never surfaced in the final
  lever output (`save_clean`, `lever_item_list`). Either wire it into downstream output
  or remove it to save token budget. Low risk, low effort.

- **I5 / C4 (document "single-example template lock" in OPTIMIZE_INSTRUCTIONS):**
  Add a sixth known problem: "Single-example template lock: when the prompt provides
  exactly one format example, small models reproduce that exact syntax in every output.
  Provide ≥2 structurally varied examples or add a do-not-copy prohibition." Update
  `OPTIMIZE_INSTRUCTIONS` in `identify_potential_levers.py:27–68`.

- **S5 / C3 (`strategic_rationale: null`):** llama3.1 consistently returns null for
  this field. Either make it required (forces the model to produce it) or remove it
  to reduce schema noise. Low priority since the field is not consumed downstream.

- **B3 (runner.py lock ordering):** Direction 5 above. Fix when any multi-worker
  model is added to the test suite.

- **S3 (`LeverCleaned.review` old description):** Pure code-quality issue — the
  `LeverCleaned` class is never sent to the LLM. Update its `review` field description
  to match the new format for human-reader clarity.
