# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #473 — "Replace negative-priming with positive framing and reduce output verbosity
in identify step"

---

## Bugs Found

**B1 — Consequences length target inconsistency (introduced by PR #473)**

`identify_potential_levers.py:118` (field description):
```
"Target length: 2–3 sentences."
```
`identify_potential_levers.py:232` (system prompt section 2):
```
"Target length: 2–4 sentences."
```

PR #473 updated the `Lever.consequences` field description from "2-4" to "2-3" sentences but left
the system prompt unchanged. Models receive two simultaneous directives that contradict each other.
LLMs generally give field descriptions and system-prompt instructions equal weight; the result is
undefined behavior (each model may pick the value it prefers). This directly explains why haiku's
consequences length *increased* after the PR rather than decreased — if haiku follows the system
prompt's "2–4" instead of the field description's "2–3", the intended constraint is never applied.

Fix: update `identify_potential_levers.py:232` to read "2–3 sentences" to match the field
description, or revert the field description to "2–4" (the original) and document the chosen
value in a single location.

---

**B2 — `review_lever` length target inconsistency**

`identify_potential_levers.py:127` (field description):
```
"1–2 sentences: the primary trade-off this lever introduces…"
```
`identify_potential_levers.py:260` (system prompt section 6):
```
"Keep each `review_lever` to one sentence (20–40 words)."
```

Field description says 1–2 sentences; system prompt says exactly one sentence. Models parsing
both sources receive conflicting guidance. This is the same class of bug as B1.

Fix: align both to the same value. The "one sentence (20–40 words)" in the system prompt is
more precise; the field description should match.

---

**B3 — `partial_recovery` event fires for legitimate early-stop successes**

`runner.py:577-583`:
```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 2):
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

The adaptive loop in `identify_potential_levers.py:352-354` exits early via `break` once
`len(generated_lever_names) >= 15`. A model that generates 18 levers in a single call will
have `calls_succeeded=1` and stop with a full, valid result — but the runner then records a
`partial_recovery` event for it as though the call sequence was truncated by failure.

`PlanResult` does not distinguish between "1 successful call (over-generated, early stop)" and
"1 successful call followed by 4 failed calls (true partial recovery)". The event label is
therefore semantically wrong for the early-stop case.

The insight file (Q5) asks whether haiku's partial recovery for hong_kong_game is a schema
validation failure or a timing issue. Based on this code analysis the answer is neither: it is
likely a false-positive event caused by haiku generating ≥15 levers in a single call.

Fix options:
- Add `calls_attempted: int` field to `PlanResult` so the runner can distinguish early stop
  (calls_succeeded == calls_attempted) from true partial recovery (calls_succeeded <
  calls_attempted). Then emit the event only for true partial recovery.
- Alternatively, rename the event to `early_stop` when the total lever count is ≥15 and
  `partial_recovery` only when it is <15. This requires passing lever count through PlanResult.

---

**B4 — `_run_levers` warning threshold conflicts with expected two-call behavior**

`runner.py:131-134`:
```python
if actual_calls < 3:
    logger.warning(
        f"{plan_name}: partial recovery — {actual_calls} calls succeeded"
    )
```

The comment on lines 128-130 explicitly states: "A 2-call success is normal for models that
produce 8+ levers per call." Yet the warning still fires for `actual_calls == 2`. For haiku
(which regularly produces 8-10 levers per call), 2 calls yields 16-20 levers, well above the
15-lever minimum — this is a success, not partial recovery. The warning message is misleading
and creates noise in log files.

This is inconsistent with the `_run_plan_task` threshold (`< 2`), which would not emit an event
for a 2-call completion. Having the warning at `< 3` and the event at `< 2` makes the two
monitoring signals disagree on whether a 2-call completion is noteworthy.

Fix: Either raise the event threshold to match the warning (`< 3`), or lower the warning to
match the event (`< 2`). Since 2-call completions are explicitly acknowledged as normal, the
warning threshold of `< 3` appears wrong; changing it to `< 2` would align both signals and
eliminate false-positive log noise.

---

## Suspect Patterns

**S1 — "cause-effect relationships" phrasing may incentivize fabricated numbers**

`identify_potential_levers.py:115-117`:
```
"Focus on cause-effect relationships and factual outcomes; "
```

The insight file reports gpt-oss-20b fabricated numbers increased substantially after PR #473
(0→4 pct occurrences, 1→5 dollar occurrences). The PR description replaced the prohibitive
"Do NOT include…" language with the directive "Focus on cause-effect relationships and factual
outcomes." When a model is told to emphasize cause-effect relationships and invent plausible
figures to make a causal claim concrete, the "only cite numbers if the project context provides
evidence" constraint is farther away in the field description and may be given less weight.

The instruction to "focus on cause-effect" appears before the constraint about evidence-based
numbers; gpt-oss-20b may be satisfying the cause-effect requirement by inventing metrics.
OPTIMIZE_INSTRUCTIONS (lines 52-55) explicitly warns about fabricated numbers, but the field
description's positive framing makes the causal story feel incomplete without numbers.

The existing text already has the correct constraint: "only cite numbers if the project context
provides evidence for them." Repeating it more proximally to the "cause-effect" instruction (or
moving it to immediately after) would reduce this risk without removing positive framing.

---

**S2 — `review_lever` field description contains a template-lockable phrase**

`identify_potential_levers.py:126-130`:
```
"1–2 sentences: the primary trade-off this lever introduces "
"and the gap the three options leave unaddressed. "
```

OPTIMIZE_INSTRUCTIONS (lines 86-92) warns: "A Pydantic field description containing a
structural phrase (e.g. 'name the core tension') is read as a literal instruction — models
start every output with 'The tension is…'. Describe the required content not the expected
sentence structure."

The phrase "the primary trade-off this lever introduces" in the field description is exactly
this kind of structural cue. The insight confirms llama3.1 opens 7/87 (8%) reviews with "The
primary trade-off introduced by this lever is…". This is worse than the 6.1% rate before the
PR. The field description contains the pattern that models are locking onto — the system
prompt examples alone cannot override it (per OPTIMIZE_INSTRUCTIONS line 91-92).

Note the irony: the system prompt's review_lever examples (lines 247-249) follow the
OPTIMIZE_INSTRUCTIONS guidance (domain-specific, structurally distinct, no shared opener), but
the field description then introduces "the primary trade-off" as the expected opener, partially
undoing the examples' diversity.

---

**S3 — Three distinct length-limit signals for `review_lever` create confusion**

For `review_lever`, models receive guidance from three sources:

| Source | Location | Says |
|--------|----------|------|
| Field description | line 127 | "1–2 sentences" |
| System prompt section 4 | line 245 | "A short critical review — identify the primary trade-off…" |
| System prompt section 6 | line 260 | "one sentence (20–40 words)" |

Three signals disagree. Sections 4 and 6 of the system prompt are themselves internally
inconsistent: section 4 describes content without a length, while section 6 specifies "one
sentence (20–40 words)" which contradicts the field description's "1–2 sentences." Models
resolve contradictions stochastically, contributing to variance in output length.

---

## Improvement Opportunities

**I1 — Add a `field_validator` character cap on `consequences` to enforce verbosity constraint**

The `Lever` class has validators for `options` count and `review_lever` format, but none for
`consequences` length. Haiku produces consequences averaging 584 chars (2.1× baseline at 279
chars) despite the "2–3 sentences" text hint. Text hints are insufficient for haiku.

Suggested location: `identify_potential_levers.py` near line 132 (after `parse_options`):
```python
@field_validator('consequences', mode='after')
@classmethod
def check_consequences_length(cls, v):
    if len(v) > 500:
        raise ValueError(
            f"consequences too long ({len(v)} chars); keep to 2-3 sentences / ~400 chars"
        )
    return v
```

A hard cap at 500 chars would reject haiku's 600-800 char outputs and force regeneration. A
soft cap (warn only) avoids token waste but provides no enforcement. The tradeoff is that a
hard cap increases retry count for haiku specifically; a 450-500 char threshold is recommended
to avoid rejecting legitimate 3-sentence outputs while still catching haiku overflows.

---

**I2 — Reword `review_lever` field description to break template lock**

Replace "the primary trade-off this lever introduces and the gap the three options leave
unaddressed" with content-focused language that doesn't start a sentence pattern. Per
OPTIMIZE_INSTRUCTIONS (lines 86-92), describe what to include, not the expected structure.

Suggested replacement:
```
"1 sentence: state what decision-critical insight this lever adds and what risk the three
options collectively ignore. Do not use square brackets or placeholder text."
```

This removes "primary trade-off introduced by this lever" (the locked phrase) and "gap the
three options leave unaddressed" (also a lockable phrase) while preserving the content
requirement.

---

**I3 — Align `consequences` length targets to one canonical value**

`identify_potential_levers.py:118` and `232` both specify length for `consequences` but with
different values. Choose one ("2–3 sentences" is the PR's intent) and update the system prompt
at line 232 to match.

---

**I4 — Add "no invented numbers" reminder adjacent to "cause-effect" directive**

To reduce S1 risk without removing positive framing, move the evidence constraint immediately
after the cause-effect instruction:

Current order (lines 113-119):
```
"What happens when this lever is pulled? Describe the direct effect and "
"at least one downstream implication or trade-off. Be concise and grounded — "
"only cite numbers if the project context provides evidence for them. "
"Focus on cause-effect relationships and factual outcomes; "
"save critical assessments for the review_lever field. "
"Target length: 2–3 sentences."
```

Suggested reorder — place the number constraint immediately after the cause-effect directive:
```
"What happens when this lever is pulled? Describe the direct effect and "
"at least one downstream implication or trade-off. "
"Focus on cause-effect relationships and factual outcomes; "
"never invent percentages, durations, or monetary figures — "
"only cite numbers the project context provides directly. "
"Save critical assessments for the review_lever field. "
"Target length: 2–3 sentences."
```

---

**I5 — Add cause-effect fabrication trigger to OPTIMIZE_INSTRUCTIONS**

The insight identifies a new pattern not currently in OPTIMIZE_INSTRUCTIONS: positive
cause-effect framing without an adjacent number-evidence constraint triggers specific invented
metrics (HK$ costs, percentages, weeks). This is distinct from "fabricated numbers" in general
(lines 52-55) because it is specifically triggered by the causal framing instruction.

Suggested addition to OPTIMIZE_INSTRUCTIONS after line 55:
```
- Cause-effect framing amplifies number fabrication. Instructing models to "focus on
  cause-effect relationships" without an immediately adjacent constraint on evidence
  causes models to invent specific causal metrics (costs, percentages, durations) to
  make the causal story concrete. Always pair cause-effect framing instructions with an
  explicit "never invent numbers not present in the project context" reminder in the
  same sentence or the immediately following sentence.
```

---

**I6 — Distinguish early-stop from partial-failure in `PlanResult`**

Add a `lever_count: int | None` field to `PlanResult` in `runner.py` (populated by
`_run_levers`). The `partial_recovery` event in `_run_plan_task` can then check
`lever_count < 15` (true partial) vs `calls_succeeded < 2` (potentially just early stop).
This makes monitoring accurate without changing the adaptive loop logic.

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|-----------------|-----------------|
| haiku consequences grew +13% despite stricter "2-3 sentences" target | **B1**: system prompt still says "2-4 sentences"; haiku ignores the field description and follows the system prompt |
| gpt-oss-20b fabricated numbers increased 4-5× | **S1**: "Focus on cause-effect relationships" without adjacent number-evidence constraint invites gpt-oss-20b to invent metrics |
| llama3.1 "primary trade-off introduced by this lever" template lock worsened (6.1%→8%) | **S2**: field description directly contains the lockable phrase; system-prompt examples cannot override a structural cue in the field description |
| System prompt / field description length inconsistency | **B1** and **B2**: PR #473 updated field descriptions but not corresponding system-prompt targets |
| haiku partial_recovery events despite possible over-generation | **B3**: event fires when `calls_succeeded < 2`, which also catches 1-call early-stop successes where haiku generated ≥15 levers in one call |
| Unclear whether haiku partial recovery is schema failure or timing | **B3** + **B4**: the monitoring signals are unreliable — `_run_levers` warns at `< 3` and `_run_plan_task` emits an event at `< 2`, and neither distinguishes early stop from true partial failure |
| review_lever has three conflicting length signals | **S3**: field description "1-2 sentences" vs system prompt section 4 (no length) vs system prompt section 6 "one sentence (20-40 words)" |

---

## PR Review

### What the PR changed

PR #473 made three changes to `identify_potential_levers.py`:

1. **`Lever.consequences` field description** (lines 111-119): replaced
   `"Do NOT include 'Controls ... vs.', 'Weakness:'"` with
   `"Focus on cause-effect relationships and factual outcomes"` and changed
   the length target from "2-4" to "2-3" sentences.

2. **`LeverCleaned.consequences` field description** (lines 207-215): same
   change as (1). `LeverCleaned` is never sent to an LLM, so this change has
   zero prompt effect. Updating it is correct for documentation consistency
   but does not influence model behavior.

3. **`Lever.options` field description** (lines 121-124): changed from
   "Each option is a full sentence" to "Each option is one sentence".

4. **`Lever.review_lever` field description** (lines 125-131): changed to
   "1–2 sentences".

### Does the implementation match the intent?

**Goal 1 (positive framing)**: Partially. The prohibitive "Do NOT" text was
replaced with positive framing, which is consistent with OPTIMIZE_INSTRUCTIONS.
However, the change introduced B1: the system prompt still contains "2–4 sentences"
for consequences while the field description now says "2–3 sentences". This
inconsistency directly undermines goal 2. The PR description does not mention
updating the system prompt.

**Goal 2 (reduced output targets)**: Incomplete. The consequences field description
was tightened to "2–3 sentences" but the system prompt at line 232 was not updated
to match. Models receiving both signals may follow whichever they weight more heavily.
For haiku, this explains why consequences length *increased* — haiku may weight the
system prompt over the field description.

**Goal 3 (gpt-oss-20b timeout fix)**: The approach (shorter output targets) is
reasonable. However, the change in `options` description from "a full sentence" to
"one sentence" is a cosmetic rewording that likely has no measurable effect on token
count. The `consequences` 2-4→2-3 change is meaningful but its effect is negated by
the B1 inconsistency for models that follow the system prompt.

### New issues introduced by the PR

1. **B1**: Length target inconsistency for `consequences` — this is the most
   impactful issue from the PR.

2. **Fabricated numbers regression (S1)**: The positive "cause-effect" framing appears
   to be correlated with gpt-oss-20b's increased number fabrication. This is a
   secondary effect not anticipated by the PR description.

3. **Template lock worsened (S2)**: The "primary trade-off introduced" phrase in the
   updated `review_lever` field description reinforced llama3.1's template lock slightly.

### Gaps in the PR

- The system prompt was not audited alongside the field description changes. A search
  for "2-4" or "2–4" in the file before merging would have caught B1.
- The PR description claims "Helps gpt-oss-20b complete within 600s" but 2/5 gpt-oss-20b
  plans still time out, and the root cause (prompt token count × number of calls ×
  slow API) is not addressed structurally. A token-count audit of the full prompt
  (system_prompt + user_prompt + structured output overhead) was not included.
- `LeverCleaned.consequences` was updated but `LeverCleaned` is documentation-only;
  the comment at line 194 (`"Field descriptions here are for documentation only"`) was
  not checked before applying the same change — this is harmless but shows the PR
  was not aware of this distinction.

---

## Summary

PR #473 achieves its minimum viable goal (recovering from PR #471's catastrophic
gpt-oss-20b failure) but introduces one confirmed bug and several quality regressions.

**Confirmed bugs:**
- **B1** (HIGH): Consequences length target inconsistent between field description
  ("2–3 sentences", line 118) and system prompt ("2–4 sentences", line 232). This
  directly explains haiku's verbosity regression after the PR.
- **B2** (MEDIUM): `review_lever` length target inconsistent between field description
  ("1–2 sentences", line 127) and system prompt section 6 ("one sentence", line 260).
- **B3** (MEDIUM): `partial_recovery` event in `runner.py:579` fires for legitimate
  1-call early-stop successes (model generated ≥15 levers in one call) making it
  unreliable as a monitoring signal.
- **B4** (LOW): `_run_levers` warning threshold (`< 3`) conflicts with the event
  threshold (`< 2`) and fires for normal 2-call completions.

**Suspect patterns:**
- **S1** (HIGH): "Focus on cause-effect relationships" without an adjacent number-evidence
  constraint correlates with increased fabricated numbers in gpt-oss-20b. Move the evidence
  constraint immediately adjacent to the cause-effect directive.
- **S2** (MEDIUM): `review_lever` field description contains "the primary trade-off this
  lever introduces" — the exact phrase llama3.1 is locking onto for 8% of its reviews.
  Per OPTIMIZE_INSTRUCTIONS, structural phrases in field descriptions override examples.
- **S3** (LOW): Three conflicting length signals for `review_lever` (field description,
  system prompt section 4, system prompt section 6) produce undefined model behavior.

**Priority fixes:** B1 (update system prompt line 232 to "2–3 sentences"), then S1
(reorder/strengthen number-evidence constraint in `consequences` description), then B2
and I2 (align `review_lever` targets and reword to break template lock).
