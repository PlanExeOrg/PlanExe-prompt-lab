# Code Review (claude)

## Scope

Reviewing `identify_potential_levers.py` and `runner.py` against PR #481
("Tighten number constraint in consequences to verbatim-only") and the
accumulated insight findings from analyses 69–74.

**Runs evaluated:** `5/32`–`5/38` (PR #481 against PR #358 baseline)

**Model mapping:**

| Run | Model |
|-----|-------|
| 5/32 | ollama-llama3.1 |
| 5/33 | openrouter-openai-gpt-oss-20b |
| 5/34 | openai-gpt-5-nano |
| 5/35 | openrouter-qwen3-30b-a3b |
| 5/36 | openrouter-openai-gpt-4o-mini |
| 5/37 | openrouter-gemini-2.0-flash-001 |
| 5/38 | anthropic-claude-haiku-4-5-pinned |

---

## Bugs Found

### B1 — `LeverCleaned` field description update in PR #481 is dead code

**File:** `identify_potential_levers.py:196–226`

The `LeverCleaned` class carries an explicit comment at line 197:
> "Cleaned output schema — **never sent to an LLM**."

and at lines 201–202:
> "Field descriptions here are **for documentation only** and have **no effect on LLM output**."

PR #481 nevertheless updated `LeverCleaned.consequences` at line 209 to match
the new wording in `Lever.consequences`. Since `LeverCleaned` is only populated
during the clean-up step (lines 374–382, mapping `Lever` → `LeverCleaned`), its
field descriptions are never included in any chat message sent to the LLM.
The change is cosmetically consistent but has zero behavioral impact.

**Impact:** Wasted line in the PR diff; may mislead future reviewers into
thinking all three locations equally matter for prompt quality.

---

### B2 — PR #481 targets the wrong field: fabricated numbers persist in `options`

**File:** `identify_potential_levers.py:122–125`

The `options` field description reads:
```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option must be a complete "
                "strategic approach (a full sentence with an action verb), not a label."
)
```

It contains no verbatim-numbers constraint. Yet the primary fabrication
violations observed across analyses 73 and 74 occur in `options`, not in
`consequences`. Evidence from haiku run 5/38 (`history/5/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`):

- **"Mainland Revenue Independence"** options: `"40–50% of the budget originates from a major Western streaming platform"` — fabricated % allocation
- **"Post-Production Investment Allocation"** options:
  - `"Allocate 65% of the HK$470 million post-production budget to sound design"`
  - `"Commit 50% of post-production resources to subtle environmental VFX"`
  — both fabricated percentages (HK$470M is verbatim, the percentages are not)
- **"Sound Design Investment"** options: `"HK$8–12M"`, `"HK$4–5M"`, `"HK$18–22M"` — derived budget allocations (only HK$470M total is verbatim in context)

PR #481 updated `Lever.consequences` and the system prompt Section 2, but
`options` remains unprotected. Analysis 73 identified this gap explicitly
(N3, C3) but it was not addressed.

---

### B3 — Fabricated numbers still appear in `consequences` after PR #481

**File:** `identify_potential_levers.py:111–120` (Lever.consequences)

Despite the tightened wording, haiku (run 5/38) generates derived industry
figures in the consequences field:

- **"Sound Design Investment"** consequences: `"typically adding 2–4 weeks and 8–15% to post-production budget"` — "2–4 weeks" and "8–15%" are industry-knowledge estimates, not verbatim from the hong_kong_game project context.

The loophole is the word **"typically"**: haiku interprets this as a
qualification that licenses industry-standard figures even when the project
context does not supply them. The new instruction "do not calculate, derive, or
estimate figures" is not preventing inference from domain knowledge.

**Impact:** The PR's primary claimed improvement (eliminating fabricated %
claims from consequences) is only partial; derived figures still appear via
"typically adds X%" phrasing that models treat as citation rather than
derivation.

---

### B4 — Template lock in `review_lever` persists unchanged

**File:** `identify_potential_levers.py:125–134`

The `review_lever` field description at lines 125–134 still reads:
```python
"A short critical review: identify the primary trade-off "
"this lever introduces, then state the specific gap the "
"three options leave unaddressed. "
```

PR #481 does not modify this. The phrase **"the three options leave
unaddressed"** is the template-lock root cause documented since analysis 73 (E4)
and quantified in analysis 74 (Template Lock Status table). Evidence from haiku
run 5/38 hong_kong_game:

- Lever 5 review: `"all three options leave unresolved whether the film's target audience…"`
- Lever 8 review: `"none of the three options adequately addresses…"`
- Lever 9 review: `"all three options either concede creative control…"`
- Lever 12 review: `"The three options do not address…"`

This is the primary outstanding structural issue. PR #481 is layering a
narrower fix (consequences numbers) on top of an unfixed template-lock root
cause.

---

### B5 — Case-sensitive lever name deduplication

**File:** `identify_potential_levers.py:368–370`

```python
if lever.name in seen_names:
    logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
    continue
seen_names.add(lever.name)
```

The set membership test is exact-match, case-sensitive. A model returning
`"Festival Launch"` on call 1 and `"festival launch"` on call 2 produces two
distinct entries in the output. Downstream `DeduplicateLevers` may or may not
catch semantic duplicates depending on embedding similarity thresholds.

This is a pre-existing issue, not introduced by PR #481.

---

## Suspect Patterns

### S1 — `check_review_format` enforces minimum length but not maximum

**File:** `identify_potential_levers.py:162–178`

```python
if len(v) < 10:
    raise ValueError(...)
if '[' in v or ']' in v:
    raise ValueError(...)
```

The system prompt (line 264) says "Keep each `review_lever` to one sentence
(20–40 words)." Haiku consistently produces reviews of 250–300 chars
(~40–55 words). A soft warn-level log for reviews > 200 chars (or reviews that
contain more than one terminal sentence) would flag this without breaking runs.
Without enforcement, the one-sentence target is aspirational but unenforced for
all models.

---

### S2 — `_run_levers` warning threshold is miscalibrated

**File:** `runner.py:131–133`

```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

`min_levers=15`, and the system prompt targets 5–7 levers per call. A model
consistently generating 8+ levers will legitimately finish in 2 calls. The
warning fires at `< 3` calls even in the normal-success case for such models.
This produces false-positive warnings in the log that can obscure genuine
problems.

---

### S3 — `generated_lever_names` grows unboundedly and is reused on second call

**File:** `identify_potential_levers.py:299–358`

On the second call the prompt is:
```python
f"Generate 5 to 7 MORE levers with completely different names. "
f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
f"{user_prompt}"
```

This is correct behavior, but the names list grows with every successful call.
By call 3 (e.g., for llama3.1 which generates fewer levers per call), the
prohibition list contains 10–15 names inserted into the user turn. For plans
with verbose user prompts, this inflates the context window without trimming.
The prohibition list is also not deduplicated before insertion; if
`generated_lever_names` somehow accumulates the same name twice (e.g., via
case variation not caught by `seen_names`), it appears twice in the prohibition
string.

---

### S4 — `track_activity_path.unlink` runs even when the plan succeeded

**File:** `runner.py:283`

```python
track_activity_path.unlink(missing_ok=True)
```

This unconditionally deletes the per-plan activity JSONL after the run,
including successful runs. The purpose is that `_maybe_generate_activity_overview`
reads `usage_metrics.jsonl` instead. However, if `usage_metrics.jsonl` is
empty (e.g., for backends where the httpx hook didn't fire), both the activity
file and the overview file may be absent, leaving no token-count record for the
plan. This is a silent data loss rather than a visible error.

---

## Improvement Opportunities

### I1 — Add verbatim-numbers constraint to `options` field description

**File:** `identify_potential_levers.py:122–125`

The analysis 73 insight (N3, C3) already recommended this. PR #481 fixes
`consequences` but leaves `options` unprotected. Proposed addition:

```python
options: list[str] = Field(
    description="Exactly 3 options for this lever. No more, no fewer. Each option must be a complete "
                "strategic approach (a full sentence with an action verb), not a label. "
                "Use only numbers that appear verbatim in the project context; "
                "do not calculate, derive, or estimate figures."
)
```

---

### I2 — Replace copyable phrase in `review_lever` field description

**File:** `identify_potential_levers.py:125–134`

The phrase "the specific gap the three options leave unaddressed" is a copyable
template. Analyses 73 and 74 both identified this as the template-lock root
cause. Replace with goal-oriented language (what to identify) rather than
structural language (how the sentence should start):

```python
review_lever: str = Field(
    description=(
        "A short critical review (one sentence, 20–40 words): name the primary "
        "trade-off this lever forces, then identify a real-world constraint or "
        "risk that would persist even if all three options were executed in full. "
        "See system prompt section 4 for examples. "
        "Do not use square brackets or placeholder text."
    )
)
```

This removes "the three options leave unaddressed" without naming it as a
banned phrase (which per OPTIMIZE_INSTRUCTIONS would cause small models to copy
the prohibition text as a template).

---

### I3 — Add a worked counter-example for fabricated numbers in Section 5

**File:** `identify_potential_levers.py:255–260` (system prompt Section 5)

The abstract prohibition "NO fabricated statistics or percentages without
evidence from the project context" is being ignored by haiku and gpt-oss-20b.
A concrete BAD/GOOD contrast is more effective for mid-tier models:

```
5. **Prohibitions**
   - NO fabricated statistics or percentages. Example:
     BAD: "Allocate 20% of the budget to pre-production." (20% is not in the context)
     GOOD: "Allocate a portion of the contingency reserve to pre-production."
   - NO generic option labels (e.g., "Optimize X", "Tolerate Y")
   ...
```

Note from OPTIMIZE_INSTRUCTIONS: do not name the specific banned phrase in the
prohibition — the BAD/GOOD contrast should use a neutral domain so small models
don't template-copy the exact example.

---

### I4 — Add companion fix to system prompt Section 4 to match `review_lever` description

**File:** `identify_potential_levers.py:248–249` (system prompt Section 4)

Section 4 currently reads:
> "A short critical review — identify the primary trade-off this lever
> introduces, then state the specific gap the three options leave unaddressed."

This must be updated to match any change to the `review_lever` field
description (I2 above); otherwise field description and system prompt diverge,
which can confuse structured-output models that compare both.

---

### I5 — `LeverCleaned` field descriptions could be simplified

**File:** `identify_potential_levers.py:196–226`

Since `LeverCleaned` is explicitly documented as never sent to an LLM (line
197, 201–202), its verbose field descriptions add maintenance surface without
benefit. Consider collapsing them to terse documentation strings that don't
accidentally mislead maintainers into treating them as LLM-facing prompts:

```python
consequences: str = Field(description="Cleaned consequences text from Lever.consequences.")
```

This would prevent future PRs from unnecessarily mirroring `Lever` field
description changes into `LeverCleaned`.

---

## Trace to Insight Findings

| Code Issue | Insight Finding Explained |
|---|---|
| B2 (`options` has no verbatim-numbers constraint) | Analysis 73/N3: "Haiku options still contain estimated/derived figures despite the prohibition"; Analysis 74/§4: gpt-oss-20b generates fabricated % in options (60%, 40%, 20%) |
| B3 (consequences "typically adds X%" loophole) | Analysis 73/N3: options violation traced here; haiku run 5/38 "8–15%" in consequences confirms gap remains post-PR #481 |
| B4 (template lock in `review_lever` field description) | Analysis 73/E4: "The root cause remains in two locations: the `review_lever` Pydantic field description and Section 4 instruction"; Analysis 74/§1 (gpt-oss-20b shifted lock), §2 (qwen3-30b regression), §5 (llama3.1 residual lock) |
| B1 (LeverCleaned dead code) | No insight-file finding — structural maintenance issue |
| B5 (case-sensitive dedup) | Analysis 73/N5: llama3.1 semantic duplicates ("Festival Launch" / "Festival Launch Strategy") — these pass the name check because they're not exact matches |
| S1 (no max-length enforcement for reviews) | Analysis 73/§2.3: "Haiku review avg length: ~220 chars (2.4× baseline)"; Analysis 74/§Review Field Length table: haiku at 2.9× baseline |
| S2 (miscalibrated warning threshold) | Analysis 73/P1: partial_recovery events for haiku are loop-exits (2-call success is normal), not failures — the warning fires as noise |

---

## PR Review

### What was changed

PR #481 makes one semantic change in three code locations:

| Location | File | Lines | Sent to LLM? |
|---|---|---|---|
| `Lever.consequences` field description | `identify_potential_levers.py` | 114–116 | **Yes** — included in structured output schema |
| `LeverCleaned.consequences` field description | `identify_potential_levers.py` | 211–213 | **No** — LeverCleaned is never sent to LLM |
| System prompt Section 2 | `identify_potential_levers.py` | 236 | **Yes** — included in every chat message |

The actual wording change: `"only cite numbers if the project context provides
evidence for them"` → `"use numbers only when the project context provides them
directly — do not calculate, derive, or estimate figures"`.

### Does the implementation match the intent?

**Partially.** The two effective locations (Lever field description + system
prompt Section 2) are correctly updated and are genuinely stronger than the
baseline wording. "Do not calculate, derive, or estimate figures" closes the
"provides evidence" loophole that allowed models to reason "the context implies
this percentage."

However, three gaps mean the PR does not fully achieve its intent:

**Gap 1 — Wrong field scope.** The PR title claims to tighten the constraint
in consequences. But analysis 73 N3 and the haiku output from run 5/38
confirm that the primary fabrication site is `options`, not `consequences`.
The PR leaves `options` entirely unprotected.

**Gap 2 — "Typically" loophole persists.** Haiku run 5/38 produces `"typically
adding 2–4 weeks and 8–15% to post-production budget"` in the **consequences**
field — the exact field this PR tightened. "Typically" acts as a qualifier that
models use to frame industry-knowledge figures as domain citations rather than
derivations. The new wording does not prevent this.

**Gap 3 — LeverCleaned update is wasted.** One of the three claimed changes
(LeverCleaned, line 209) has zero effect on LLM output. The PR description
says "three locations" but functionally only two locations matter. Future PRs
that correctly skip the LeverCleaned update may be flagged as incomplete because
the pattern of updating all three was established here.

### Are there edge cases or regressions the PR misses?

1. **gpt-oss-20b options fabrication** (introduced in analysis 74 / PR #479)
   is not addressed by this PR. Run 5/33 (gpt-oss-20b) may still contain
   fabricated percentage allocations in options.

2. **review_lever template lock** (B4 above) is not addressed. Models that
   were template-locked before PR #481 remain locked after it.

3. **The isolation methodology is sound**: the PR description correctly notes
   it tests a single variable against the PR #358 baseline. This is the right
   approach. The concern is that the test addresses the wrong variable (consequences
   description) when the dominant violation site is the options field.

### Verdict

The PR is **safe and non-regressive**: the wording is stronger, the two
effective locations are correctly updated, and the change cannot reduce output
quality. It likely achieves partial improvement for models that were fabricating
numbers specifically in consequences.

However, the PR is **incomplete** relative to the fabrication problem it claims
to solve: the options field constraint is absent, the "typically" loophole
survives, and one of the three claimed fix locations (LeverCleaned) is dead code.

**Recommended follow-ups (in priority order):**
1. Add verbatim-numbers constraint to `options` field description (I1)
2. Replace copyable phrase in `review_lever` field description (I2 + I4)
3. Add worked counter-example to Section 5 (I3)

---

## Summary

**Bugs:** B1 (LeverCleaned dead code), B2 (options unprotected), B3 ("typically"
loophole in consequences), B4 (review_lever template lock), B5 (case-sensitive
dedup)

**Most critical unresolved issue:** B4 — the `review_lever` field description
still contains "the specific gap the three options leave unaddressed," which is
the template-lock root cause confirmed across analyses 73 and 74. PR #481 does
not modify this phrase. Until it is replaced with goal-oriented language, mid-
and lower-tier models will continue to produce mechanically repetitive reviews
at 70–94% lock rates for haiku and higher for gpt-oss-20b.

**PR #481 assessment:** The two effective changes (Lever field description + system
prompt Section 2) are syntactically correct and directionally right. They may
modestly reduce fabricated numbers in consequences. The LeverCleaned change is
dead code. The PR does not address the dominant violation site (options field),
does not close the "typically" loophole in consequences, and does not touch the
template-lock root cause. It is a safe but incomplete fix. **CONDITIONAL** —
merge, but immediately follow with the options field constraint (I1) and the
review_lever description rewrite (I2+I4).
