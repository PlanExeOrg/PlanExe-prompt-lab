# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude, code_claude) converge on the same two highest-priority unfixed issues:

1. **Template lock root cause unaddressed (B1+B2):** The `review_lever` Pydantic field description (lines 125–131) and system-prompt Section 4 (line 245) both still read "the gap the three options leave unaddressed." This is the grammatical anchor that drives 70–94% of haiku reviews — and 28–33% of gpt-4o-mini/gpt-5-nano reviews — to start with "all three options", "none of the options", or "the options do not." Both agents identify this as the primary unresolved issue from analysis/40 and note that PR #478 did not touch it.

2. **Verbatim-numbers constraint missing from options field (B3):** The `consequences` field description carries the explicit prohibition ("Use numbers only when the project context provides them directly — do not calculate, derive, or estimate figures"), but the `options` field description does not. Both agents observe that haiku produces 10+ estimated figures per plan (screen counts, shooting-day splits, VOD windows) in options while correctly respecting the constraint in consequences. The global Section 5 prohibition is insufficient for models that follow field descriptions selectively.

Both agents also agree on PR #478's positive contributions: the positive framing change (consequences prohibition → redirect to review_lever), the verbatim-numbers constraint in consequences, and tighter length targets are valid improvements with no regressions.

Both verdict the PR **CONDITIONAL**: keep it, follow immediately with B1+B2.

---

## Cross-Agent Disagreements

There are no material disagreements. The insight file documents output-level observations (N1–N5, P1–P6); the code review file maps those directly to source locations (B1–B4, S1–S3, I1–I4). They are complementary, not contradictory.

The only apparent discrepancy is on partial-recovery semantics: the insight file (E5, Table 1) calls haiku silo and sovereign_identity "partial_recovery events" while the code review notes (B4) that the `partial_recovery` event actually fires only for `calls_succeeded < 2`, so these 2-call completions do NOT emit the event — they only trigger the `< 3` warning log. Both are correct about different things; neither is wrong.

**Source verification of all key claims:**

- **B1 confirmed:** `identify_potential_levers.py:125–131` reads `"the gap the three options leave unaddressed."` — unchanged by PR #478.
- **B2 confirmed:** `identify_potential_levers.py:245` reads `"then state the specific gap the three options leave unaddressed."` — unchanged.
- **B3 confirmed:** `identify_potential_levers.py:121–124` (options field description) contains no verbatim-numbers constraint; `identify_potential_levers.py:111–120` (consequences field description) does.
- **B4 confirmed:** `runner.py:131` warns at `actual_calls < 3`; `runner.py:578–583` emits the `partial_recovery` event only at `pr.calls_succeeded < 2`. The thresholds are inconsistent.
- **S1 confirmed:** `identify_potential_levers.py:295–304` — on call 2+ when `generated_lever_names` is empty, the prompt reads `"Do NOT reuse any of these already-generated names: []"`.

---

## Top 5 Directions

### 1. Fix "the three options" template lock in field description and Section 4 (B1+B2)
- **Type**: prompt change (Pydantic field description + system prompt)
- **Evidence**: Both agents; B1 (code_claude), B2 (code_claude), N1 (insight_claude), E4 (insight_claude). Confirmed in source lines 125–131 and 245. OPTIMIZE_INSTRUCTIONS lines 73–82 ("Template-lock migration") explicitly prohibit this exact pattern.
- **Impact**: 70–94% of haiku reviews currently show the lock (hong_kong_game: 70%, sovereign_identity: 94%). gpt-4o-mini and gpt-5-nano show 28–33% lock rate. Fixing the grammatical anchor affects all models simultaneously for every plan. Analysis/40 predicted this fix would reduce haiku lock rate to <20%.
- **Effort**: Low — two targeted string substitutions in the same file. The replacement wording is already drafted (see Recommendation below).
- **Risk**: Very low. The replacement text preserves the semantic intent (primary trade-off + gap) while removing "the options" as grammatical subject. No structural validator changes needed. Prior analyses confirm the fix is correct.

---

### 2. Add verbatim-numbers constraint to options field description (B3)
- **Type**: prompt change (Pydantic field description)
- **Evidence**: B3 (code_claude), N3 (insight_claude), E3 (insight_claude). Haiku generates 10+ estimated numeric ranges per plan in options (screen counts, VOD windows, shooting-day splits). The exact same constraint already works for consequences — haiku correctly uses verbatim plan figures there.
- **Impact**: Eliminates fabricated numeric ranges from options across all plans for models that follow field descriptions (primarily haiku, but also any instruction-following model). Content quality improvement for 13/105 = haiku plans, but the fabricated figures appear on every haiku plan — so all haiku outputs benefit.
- **Effort**: Very low — one sentence added to the `options` field description at line 121–124. No system-prompt change required (Section 5 global prohibition already exists; this adds it at field level).
- **Risk**: Low. Only risk is that adding text to the field description could slightly increase prompt token count, but the text is short (~15 words). No validator changes.

---

### 3. Trim Section 4 review_lever examples to ≤40 words and vary rhetorical structure (I1+I3)
- **Type**: prompt change (system prompt examples)
- **Evidence**: I1 (code_claude), I3 (code_claude). Current examples in Section 4 (lines 247–249) are all 45–55 words and all follow the same "X does Y, but Z at the worst moment" structure. Models calibrate length to examples. Haiku reviews average ~220 chars (~44 words), above the 40-word target. OPTIMIZE_INSTRUCTIONS lines 83–85 ("Verbosity amplification") and lines 73–82 ("No two examples should share a sentence pattern") directly call this out.
- **Impact**: Medium. Would reduce haiku review verbosity from ~220 chars toward the ~100–200 char target and diversify review sentence patterns. Affects all models that mirror example structure.
- **Effort**: Low — requires rewriting 1–2 of the three existing examples to be shorter and structurally different (e.g., a forward-looking conditional, or a contrast without a "worst moment" resolution).
- **Risk**: Low-medium. Changing working examples always carries some risk of unanticipated model drift. Should be verified in a self_improve iteration before merging. Does not fix the template-lock root cause (B1+B2 must still be done).

---

### 4. Fix partial-recovery threshold mismatch in runner.py (B4)
- **Type**: code fix
- **Evidence**: B4 (code_claude). Confirmed: `runner.py:131` warns at `actual_calls < 3`; `runner.py:578–583` emits the event at `calls_succeeded < 2`. Normal 2-call completions (haiku silo, haiku sovereign_identity) trigger the warning log but not the event, causing misleading "partial recovery" log noise on every normal multi-call run.
- **Impact**: Low on output quality; medium on operational observability. Spurious warnings make log-based monitoring unreliable. Aligning to `< 2` would suppress the warning for normal 2-call completions.
- **Effort**: Very low — change one constant in `runner.py:131` from `< 3` to `< 2` (or remove the warning entirely, since the comment at lines 127–130 already documents that 2-call success is normal).
- **Risk**: Very low. The fix is a threshold adjustment in a logging/event path. No output data is affected.

---

### 5. Document asymmetric field-description constraint gap in OPTIMIZE_INSTRUCTIONS (I4)
- **Type**: prompt change (OPTIMIZE_INSTRUCTIONS documentation)
- **Evidence**: I4 (code_claude). The recurring pattern — constraint added to `consequences` field description but not to `options` — is a systematic maintainability risk. It already caused B3. OPTIMIZE_INSTRUCTIONS documents "Field-description template lock" (lines 86–92) but does not document the constraint-propagation rule.
- **Impact**: Medium on future prompt engineering robustness. Adding a note ensures the next prompt author doesn't repeat the B3 mistake for any new constraint. Low immediate output impact.
- **Effort**: Very low — add 2–3 sentences to `OPTIMIZE_INSTRUCTIONS` near the "Field-description template lock" section.
- **Risk**: Zero. Documentation-only change. No LLM behavior affected.

---

## Recommendation

**Fix B1 and B2 first (template lock root cause).**

These are the highest-impact open issues, carried forward from analysis/40, directly documented in OPTIMIZE_INSTRUCTIONS, and explicitly skipped by PR #478. The "all three options / none of the options" pattern currently appears in 70–94% of haiku review_lever fields and 28–33% of gpt-4o-mini/gpt-5-nano fields. It is the dominant content quality problem in this pipeline step.

The fix is two targeted string substitutions in `identify_potential_levers.py`:

**File: `identify_potential_levers.py`, lines 125–131 (Lever.review_lever field description)**

Current:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): the primary trade-off this lever "
        "introduces and the gap the three options leave unaddressed. "
        "Do not use square brackets or placeholder text."
    )
)
```

Replace with:
```python
review_lever: str = Field(
    description=(
        "One sentence (20–40 words): name the primary trade-off this lever "
        "forces, then name a real-world constraint or risk that all three "
        "approaches collectively sidestep. Do not use square brackets or "
        "placeholder text."
    )
)
```

**File: `identify_potential_levers.py`, line 245 (Section 4 system prompt)**

Current:
```
A short critical review — identify the primary trade-off this lever introduces, then state the specific gap the three options leave unaddressed.
```

Replace with:
```
A short critical review — identify the primary trade-off this lever forces, then name a real-world constraint or risk that all three approaches collectively sidestep.
```

Both changes remove "the options" as grammatical subject while preserving the required two-part structure (trade-off + gap). The phrase "collectively sidestep" keeps the meaning without naming "the options" as the actor. The replacement wording was validated in analysis/40 and is now confirmed as the correct fix in both insight and code review.

**Also bundle B3 in the same PR** (add verbatim-numbers note to the `options` field description) since it is a one-sentence addition and directly addresses a documented content quality gap:

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option is one sentence — "
                "a concrete strategic approach with an action verb. "
                "Use only numbers that appear verbatim in the project context; "
                "do not estimate or derive figures."
)
```

B1+B2+B3 together constitute the three-change "next PR" recommended by both analysis agents and directly address the two highest-impact open issues from this analysis.

---

## Deferred Items

- **I1+I3 (example verbosity and structure):** Fix after B1+B2 land. Trimming examples reduces review verbosity further, but verifying example rewrites needs its own self_improve iteration. Not urgent while template lock is the dominant problem.
- **B4 (partial-recovery threshold mismatch):** One-line fix in runner.py; can be bundled in any housekeeping PR. No output quality effect.
- **I4 (OPTIMIZE_INSTRUCTIONS documentation):** Low-cost update worth doing in the B1+B2+B3 PR or immediately after.
- **S1 (empty names_list on failed first call):** Harmless edge case. No evidence of model confusion in output data.
- **S2 (no post-loop min_levers warning):** Observability improvement; not urgent while success rates are stable.
- **S3 (options validator allows >3 silently):** Intentional design (over-generation is handled downstream). Not a bug.
- **I2 (LeverCleaned duplicates field descriptions):** Maintenance debt. Acceptable risk; low priority.
- **Q1 (why lock rate varies by plan for haiku):** Interesting hypothesis (bureaucratic plans map naturally to "None addresses…" structure) but does not change the fix strategy.
