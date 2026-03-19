# Synthesis

## Cross-Agent Agreement

Only one insight agent and one code review agent contributed (both Claude). The two files are internally consistent and reinforce each other:

- Both confirm PR #357's first-call retry fix worked: llama3.1 gta_game went from 2/3 → 3/3 calls succeeded.
- Both identify the "core tension" wording in the `review_lever` field description (line 111) and in system prompt section 4 (line 228) as the root cause of the near-universal "The tension is between X and Y" template lock seen in runs 80 and 86.
- Both flag the `check_option_count` validator as insufficient: it accepts field-name strings as valid options, which allowed `"review_lever"` to ship as an option value in haiku gta_game run 86.
- Both agree the review length cap ("20–40 words") is instruction-only and not enforced at the Pydantic level, causing haiku to generate 60+ word reviews on complex plans despite the instruction.
- Both agree the `partial_recovery` event conflates early loop-exit (model over-generated ≥15 levers in <3 calls) with genuine call failure, inflating failure counts in dashboards.
- Both give a **CONDITIONAL** verdict on PR #357: keep the PR, but address the template lock, validator gap, and verbosity enforcement before updating best.json.

## Cross-Agent Disagreements

No disagreements exist — there is only one insight file and one code review file. No claims needed adjudication.

Source code verification of key claims:

- **"core tension" dual trigger**: Confirmed at `identify_potential_levers.py:111` (field description) and `:228` (section 4). Both serialize to the LLM.
- **`check_option_count` does not reject field names**: Confirmed at lines 130–142. The validator only checks `len(v) < 3`. No content check exists.
- **`review_lever` has no `max_length`**: Confirmed at lines 109–116. Field is `review_lever: str = Field(...)` with only a 10-char floor enforced by `check_review_format`.
- **`partial_recovery` fires on `calls_succeeded < 3` regardless of cause**: Confirmed at `runner.py:517–523`.
- **Review cap instruction is present but advisory only**: Confirmed at line 243.

---

## Top 5 Directions

### 1. Remove "core tension" from both trigger locations
- **Type**: Prompt change (Pydantic field description + system prompt)
- **Evidence**: B1 (code_claude), H1 (insight_claude). The phrase "name the core tension" appears at `identify_potential_levers.py:111` (Lever.review_lever field description) AND at `:228` (system prompt section 4 validation protocol). Both paths are serialized to the LLM. Runs 80 and 86 show ~100% of llama3.1 and haiku reviews opening with "The tension is between X and Y" or "The core tension here is X" — a structural template lock across all 35 plans and at least 2 models.
- **Impact**: Affects review diversity across all plans and all models. Structurally uniform reviews reduce decision-relevance signal downstream (DeduplicateLevers, FocusOnVitalFewLevers). Fixing this is a content-quality improvement for all 35 plans, not a recovery fix for 1.
- **Effort**: Low — rewrite two phrases in two locations. No schema changes required.
- **Risk**: Low. The content goal (trade-off + gap) is preserved; only the structural cue ("tension") is removed. The three section-4 examples already demonstrate domain-specific openers and do NOT start with "The tension is…"; removing the structural cue from the instruction text aligns the instruction with the examples.

**Suggested rewrites:**

Line 111 (`Lever.review_lever` field description):
```
# Current:
"A short critical review of this lever — name the core tension,
then identify a weakness the options miss."

# Proposed:
"A short critical review: identify the primary trade-off this lever
introduces, then state the specific gap the three options leave
unaddressed."
```

Line 228 (system prompt section 4 header):
```
# Current:
"A short critical review — name the core tension, then identify a
weakness the options miss."

# Proposed:
"A short critical review — identify the primary trade-off this lever
introduces, then state the specific gap the three options leave
unaddressed."
```

### 2. Add field-name rejection validator to `options`
- **Type**: Code fix
- **Evidence**: B2 (code_claude), C1 (insight_claude). Run 86, haiku gta_game, lever `bb5f1a82`: the third option is the literal string `"review_lever"`. The `check_option_count` validator at lines 130–142 accepted this because it only counts items (`len(v) < 3`). The defect shipped to all downstream consumers.
- **Impact**: Prevents malformed levers from reaching downstream tasks. Triggers a retry call on the failing plan rather than silently shipping corrupted data. Affects any model that exhausts its token budget mid-generation.
- **Effort**: Very low — add ~6 lines after the existing `check_option_count` validator.
- **Risk**: Very low. The check is a strict equality match against known field names. No valid option text would match `"review_lever"` or `"lever_index"`.

**Suggested code (after `check_option_count`):**
```python
_LEVER_FIELD_NAMES = frozenset({"lever_index", "name", "consequences", "options", "review_lever"})

@field_validator('options', mode='after')
@classmethod
def check_no_field_name_leakage(cls, v):
    for item in v:
        if isinstance(item, str) and item.strip() in _LEVER_FIELD_NAMES:
            raise ValueError(
                f"option '{item}' is a field-name artifact from truncated generation"
            )
    return v
```

### 3. Enforce review length cap at the schema level
- **Type**: Code fix
- **Evidence**: B3 (code_claude), H2 (insight_claude). The "20–40 words" instruction at line 243 is advisory only. Haiku parasomnia run 86: 6,898 output tokens per call, reviews of 60+ words. The three section-4 examples average ~33 words and comply; haiku ignores the instruction on complex plans. The `check_review_format` validator at lines 144–160 enforces a 10-char floor but no ceiling.
- **Impact**: Reduces per-call token output for complex plans. Haiku parasomnia target: ~3,000 tokens vs current 6,898 (−57%). Fewer loop-exit partial_recovery events for haiku. Cost and latency improvement for all plans with long prompts.
- **Effort**: Low — add `max_length` to the Field or extend `check_review_format`. Using Pydantic's built-in is one line; extending the validator adds ~3 lines.
- **Risk**: Medium. Adding a hard max_length causes Pydantic validation failures on verbose outputs, triggering retries. If the max is set too low, retries could cascade. Recommend `max_length=350` characters (~60 words, 50% headroom above the 40-word target) as a starting point, not the exact 40-word target.

Also fix the ambiguous wording at line 243. Replace "under 2 sentences (aim for 20–40 words)" with "one sentence, 20–40 words" — one sentence is unambiguous and aligns with the section-4 examples (all single-sentence reviews).

### 4. Document field-description template lock in OPTIMIZE_INSTRUCTIONS
- **Type**: Prompt/documentation change
- **Evidence**: I4 (code_claude), OPTIMIZE_INSTRUCTIONS gap (insight_claude). The OPTIMIZE_INSTRUCTIONS block (lines 27–86) already documents single-example template lock and template-lock migration. It does not yet document the newly confirmed failure mode: a Pydantic field description containing a structural phrase ("name the core tension") acting as a stronger cue than the system prompt examples.
- **Impact**: Prevents recurrence of this class of issue in future iterations. OPTIMIZE_INSTRUCTIONS is read by synthesis agents to guide future prompt design. Documenting both field-description-induced template lock and field-name leakage in options closes two known gaps.
- **Effort**: Very low — add ~6 lines of text after line 85.
- **Risk**: None.

**Suggested additions to OPTIMIZE_INSTRUCTIONS (after the "Verbosity amplification" bullet):**
```
- Field-description-induced template lock. When a Pydantic field description
  contains a structural phrase like "name the core tension", models read this
  as a literal instruction and start every output in that field with "The
  tension is…" or "The core tension is X versus Y", producing structurally
  identical reviews across all levers and plans. Fix by describing the required
  *content* ("identify the primary trade-off and the specific gap") rather than
  the expected *sentence structure*. The system-prompt examples alone are not
  enough to override a structural cue embedded in the field description itself.
- Field-name leakage in options. When token budget is exhausted mid-generation,
  structured output may emit a Pydantic field name (e.g., "review_lever",
  "consequences") as a literal option value. The current check_option_count
  validator does not catch this — it only checks list length. Add a validator
  that rejects any option whose value exactly matches a known field name.
```

### 5. Distinguish loop-exit from genuine call failure in `partial_recovery`
- **Type**: Workflow/code change
- **Evidence**: B4 (code_claude), C2 (insight_claude). `runner.py:517–523` fires `partial_recovery` whenever `calls_succeeded < 3`, regardless of whether the loop exited because ≥15 levers were generated in fewer calls (a normal/good outcome) or because a third call genuinely failed. Run 86 shows 3 haiku partial_recovery events, all of which usage_metrics confirm are loop-exits (≥15 levers in 1–2 calls). Dashboards counting `partial_recovery` as a failure proxy over-count haiku failures by 3 events per run.
- **Impact**: Operational clarity only. No effect on output quality. Improves failure-rate signal reliability for future analysis iterations.
- **Effort**: Medium — add `lever_count: int | None = None` to `PlanResult`, populate it in `_run_levers`, and use it in `_run_plan_task` to emit `"early_exit_sufficient_levers"` vs `"partial_recovery"`.
- **Risk**: Low. Additive change; existing event consumers are unaffected.

---

## Recommendation

**Pursue direction 1 first: remove "core tension" from both trigger locations.**

**Why first:** The template lock is the only confirmed issue that degrades content quality across all 35 plans and at least 2 models simultaneously. Structurally uniform reviews ("The tension is between X and Y") reduce the decision-relevant diversity that downstream steps (DeduplicateLevers, FocusOnVitalFewLevers) depend on to differentiate levers. By contrast, direction 2 (validator) fixes a defect that appeared once in 35 plans, and directions 3–5 are enforcement/observability improvements.

**What to change — exact locations:**

1. `identify_potential_levers.py` line 111 (`Lever.review_lever` field description):
   - Remove: `"name the core tension,"`
   - Replace with: `"identify the primary trade-off this lever introduces,"`

2. `identify_potential_levers.py` line 228 (system prompt section 4 header):
   - Current: `"A short critical review — name the core tension, then identify a weakness the options miss."`
   - Replace with: `"A short critical review — identify the primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed."`

Both changes preserve the content goal (trade-off + gap). They remove the structural cue that primes models to open with "The tension is…". The section-4 examples (lines 229–232) already demonstrate the correct pattern — domain-specific openers like "Switching from seasonal contract labor…" and "Each additional clinical site requires…" — so removing the structural cue from the instructions aligns the instruction with the implicit model of the examples.

**Expected measurable effect:** "The tension is…" / "The core tension is…" opener frequency drops from ~100% to <40% for llama3.1 and haiku. Review openers become domain-specific and plan-grounded, improving lever differentiation downstream.

**After this change, run the next iteration with the same 5 plans and 7 models.** If opener diversity is confirmed, then combine with direction 2 (field-name validator) in the following PR.

---

## Deferred Items

**Direction 2 (field-name validator):** Implement in the next PR alongside direction 1 if the opener lock is confirmed fixed. Very low effort, zero risk.

**Direction 3 (Pydantic max_length for review_lever):** Defer until after the template lock fix. The template lock and the verbosity issue may interact — fixing the structural cue may also reduce average review length by removing the preamble phrase. Measure review lengths after direction 1 before adding a hard schema constraint.

**Direction 5 (loop-exit vs. call failure distinction):** Low priority. The haiku partial_recovery events in run 86 are confirmed loop-exits, not failures. The false-alarm problem only affects analysis dashboards, not output quality. Address when the operational observability need becomes blocking.

**H3 (llama3.1 temperature rollback):** Monitor. The sovereign_identity partial recovery in run 80 (not seen in run 52) is a possible temperature regression, but it may also be a stochastic one-off. One run is insufficient to establish causation. If sovereign_identity continues to show partial_recovery across 2+ future runs, reduce llama3.1 temperature back to 0.6.

**S3 (named-prohibition backfire in `consequences` field description):** Medium priority. The `consequences` field description at lines 100–101 names the banned pattern `'Controls ... vs.', 'Weakness:'`. Per OPTIMIZE_INSTRUCTIONS lines 81–82, naming banned phrases risks prohibition backfire in small models. Rewrite to describe what the field should contain rather than what it should avoid. Defer to a separate PR since it's a minor field description polish, not a confirmed defect.

**S4 (misleading thread-safety comment in runner.py):** Low priority. The comment inaccuracy does not affect behavior. Clarify in a future housekeeping pass.
