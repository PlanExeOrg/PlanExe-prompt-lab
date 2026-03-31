# Code Review (claude)

## Bugs Found

### B1 — XML-tag leakage not stripped before `enriched_levers_map` lookup
**File:** `enrich_potential_levers.py:275`

```python
if char.lever_id in enriched_levers_map:
```

`enriched_levers_map` is keyed by bare UUIDs (built at line 217). When llama3.1
returns `"<lever>1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd</lever>"` as the
`lever_id` JSON value, the dict lookup silently fails. No stripping is performed
before the check. The result is an `unknown_lever_id` error for every
characterization in the batch, plus an `incomplete` error for every original
lever that was never enriched — 10 errors from a single 5-lever batch.

The `<lever>uuid</lever>` prompt format was introduced in PR #466 (line 239–245)
to prevent UUID leakage into free-text fields. That format gives non-function-
calling models (llama3.1) an unambiguous copyable template for the `lever_id`
output field. PR #467's Pydantic field-description changes may have shifted
attention enough to trigger the copy behaviour in one plan's batch.

**Fix (C1 from insight):** Before the lookup, strip the XML wrapper:

```python
raw_id = char.lever_id.strip()
if raw_id.startswith("<lever>") and raw_id.endswith("</lever>"):
    raw_id = raw_id[7:-8]
if raw_id in enriched_levers_map:
    ...
```

### B2 — `batches_succeeded` incremented when all `lever_id` lookups fail
**File:** `enrich_potential_levers.py:272`

```python
batches_succeeded += 1
```

`batches_succeeded` is incremented after a successful LLM call, before
iterating over `char` results. If every `char.lever_id` fails the lookup (B1),
the batch is counted as succeeded even though zero levers were enriched. The
counter is surfaced in `runner.py` as `PlanResult.calls_succeeded` and in
`events.jsonl`'s `partial_recovery` check — a batch that returns garbage
lever_ids will not trigger a `partial_recovery` warning.

---

## Suspect Patterns

### S1 — Anti-echoing instruction uses prohibited negative form in two places
**File:** `enrich_potential_levers.py:140, 171`

Line 140 (Pydantic field description):
> "Do not repeat the consequences or review fields."

Line 171 (system prompt):
> "Do NOT repeat the consequences or review fields — add new insight…"

`identify_potential_levers.py`'s OPTIMIZE_INSTRUCTIONS (lines 80–83) explicitly
documents this failure mode:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat
> the prohibition text as a template and copy the banned phrases."

The PR introduces the same prohibited pattern it is trying to fix. A negative
"Do NOT repeat X" instruction gives models a phrase containing the very content
they should avoid. A positive directive ("Explain the lever's purpose from the
project's own logic — what it is optimising for, what trade-offs it accepts,
and what observable success looks like") would be more effective and consistent
with the established OPTIMIZE_INSTRUCTIONS guidance.

### S2 — `<lever>uuid</lever>` format in batch prompt has no output-side guard
**File:** `enrich_potential_levers.py:239–245`

```python
lever_details_for_prompt = "\n\n".join([
    f"<lever>{lever.lever_id}</lever>\n"
    f"Name: {lever.name}\n"
    ...
    for lever in batch
])
```

The XML markup `<lever>…</lever>` is the only UUID-containing string in the
per-batch prompt. For non-function-calling models that receive the JSON schema
as prompt text, this format is the most prominent structural cue for
`lever_id`. The system prompt and Pydantic field description say nothing
about what to put in `lever_id`; models infer the format by example.

The OPTIMIZE_INSTRUCTIONS documents UUID leakage in the opposite direction
(UUID copied from prompt into free-text fields) but not this direction (XML
markup copied into the structured `lever_id` output field).

Adding an explicit positive instruction — "In the `lever_id` field, output
only the raw UUID string exactly as provided (e.g., `1a9003f0-...`)" — to
the system prompt would close this gap without requiring a code fix.

### S3 — OPTIMIZE_INSTRUCTIONS word-count reference is stale after PR #467
**File:** `enrich_potential_levers.py:72–73`

```
- Word-count padding. Models inflate to hit the 80-100 word target with
  filler phrases ...
```

PR #467 changed the description target to 50–70 words and synergy/conflict
to 20–40 words. The OPTIMIZE_INSTRUCTIONS constant still references the old
"80-100 word target". Future optimisation iterations will read this constant
to understand known problems; the stale target misleads them into treating
the new, shorter outputs as already optimal rather than as a deliberate
change with its own trade-offs.

### S4 — `TrackActivity` dispatcher handlers accumulate during parallel execution
**File:** `runner.py:248–250, 280–283`

```python
with _file_lock:
    set_usage_metrics_path(...)
    dispatcher.add_event_handler(track_activity)
```

`dispatcher` is a global LlamaIndex singleton. When `workers > 1`, each
plan's thread registers its own `TrackActivity` handler. An LLM event fired
by plan A's thread is delivered to *all* registered handlers, including plan
B's handler. `_file_lock` protects the add/remove operations but not the
delivery of events during execution. `set_usage_metrics_path` uses
thread-local storage (safe), but `TrackActivity` may write activity events
from another plan's LLM calls into the wrong plan's output directory.

---

## Improvement Opportunities

### I1 — Add XML-tag stripping to `lever_id` before map lookup
**File:** `enrich_potential_levers.py:274–283` (continuation of B1)

The C1 defensive fix from the insight is the correct approach: strip
`<lever>…</lever>` tags from `char.lever_id` before the dict lookup. This
recovers levers lost to the XML-markup copy behaviour without requiring
prompt changes or model retries. Risk is low — the strip only triggers for
malformed `lever_id` values that would otherwise cause an error anyway.

### I2 — Add `field_validator` on `LeverCharacterization.lever_id`
**File:** `enrich_potential_levers.py:136–147`

A `field_validator` on `lever_id` that strips XML tags and validates UUID
format would catch malformed values at parse time with a structured error
message, rather than silently failing the map lookup at line 275. This
provides a cleaner stack trace for future debugging and separates the
"model returned malformed lever_id" failure mode from "model returned an
entirely wrong UUID".

### I3 — Replace negative anti-echoing instruction with positive directive
**File:** `enrich_potential_levers.py:140, 171`

Replace "Do NOT repeat the consequences or review fields" with a positive
formulation: "Add new insight — explain what this lever is optimising for,
what project-specific trade-offs it accepts, and what observable evidence
would indicate success." This aligns with the OPTIMIZE_INSTRUCTIONS
principle that positive directives outperform prohibitions for small models.
The addition "add new insight about why this lever matters and what success
looks like" is a step in the right direction; the problem is the leading
"Do NOT" clause, which dominates small-model attention.

### I4 — Add positive `lever_id` output instruction to system prompt
**File:** `enrich_potential_levers.py:163–178`

The system prompt describes `description`, `synergy_text`, and `conflict_text`
in detail but says nothing about `lever_id`. For non-function-calling models,
the absence of guidance leaves them to infer the expected format from the
prompt markup. Adding one sentence — "In the `lever_id` field, output only
the raw UUID string exactly as shown in the batch (e.g.,
`1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd`)." — closes the gap without
triggering the prohibition-as-template failure mode.

### I5 — Update OPTIMIZE_INSTRUCTIONS to document XML-tag-in-lever_id regression
**File:** `enrich_potential_levers.py:88–96`

The existing OPTIMIZE_INSTRUCTIONS entry for UUID leakage covers only the
forward direction (UUID copied from prompt into free-text fields). It should
be extended with the inverse failure mode:
> XML-tag leakage into lever_id. When the per-batch prompt wraps the UUID
> in `<lever>uuid</lever>` markup, non-function-calling models (e.g.
> llama3.1) may copy the XML-wrapped form into the `lever_id` JSON field.
> This causes `unknown_lever_id` + `incomplete` errors for the entire
> affected batch. Mitigations: (a) strip XML tags from `lever_id` before the
> map lookup; (b) add a positive instruction in the system prompt specifying
> that `lever_id` must contain only the raw UUID string.

Also update line 73 to reflect the new word-count targets (50–70 words for
description, 20–40 for synergy/conflict) introduced by PR #467.

### I6 — `check_option_count` only enforces lower bound; upper bound silently ignored
**File:** `identify_potential_levers.py:147–158`

```python
def check_option_count(cls, v):
    if len(v) < 3:
        raise ValueError(...)
    return v
```

The Lever field description says "Exactly 3 options for this lever. No more,
no fewer." and the system prompt repeats this. A model that returns 4 options
passes validation silently. This is intentional for the levers list (over-
generation is fine) but inconsistent for options, where downstream steps
assume exactly 3 strategic pathways per lever. At minimum a warning log when
`len(v) > 3` would make the failure visible.

### I7 — 20-word minimum for `conflict_text` creates tension with substance requirement
**File:** `enrich_potential_levers.py:145, 173`

PR #467 set the synergy/conflict target to 20–40 words. OPTIMIZE_INSTRUCTIONS
(line 75–77) states: "Every lever has trade-offs — the conflict_text must
identify at least one genuine tension." At 20 words (≈120 chars), a model must
name another lever AND explain the trade-off. Gemini's observed 149-char
conflict_text average (≈23 words) is at the absolute lower bound. If future
iterations tighten further, genuine tension identification will become
structurally impossible within the limit. The lower bound should be defended
at ≥25 words for conflict_text specifically.

---

## Trace to Insight Findings

| Code issue | Insight observation |
|------------|---------------------|
| **B1** — no XML-tag strip before map lookup | **N1** — llama3.1 gta_game returns `<lever>uuid</lever>` as lever_id; 5 `unknown_lever_id` + 5 `incomplete` errors |
| **B1** + **B2** | **N4** — net lever-level error count increased 11 → 15 |
| **S1** — negative "Do NOT repeat" prohibition | **N3** — structural consequence echoing persists despite anti-echoing guidance |
| **S1** | **H2** — positive formulation hypothesis in insight |
| **S2** — `<lever>uuid</lever>` prompt format with no output guard | **H1** — Pydantic field description changes triggered XML-tag leakage; **N1** |
| **S3** — stale word-count reference in OPTIMIZE_INSTRUCTIONS | Gap that would mislead future optimisation iterations |
| **I4** — missing `lever_id` instruction in system prompt | **N1**, **H1** — llama3.1 has no instruction to output bare UUID |
| **I3** — positive anti-echoing reformulation | **H2** — "positive formulation may be more effective" |
| **I7** — 20-word lower bound too tight for conflict_text | Q2 — is gemini's 23–25 word synergy/conflict informationally sufficient? |

---

## PR Review

### What the PR changes (`enrich_potential_levers.py` lines 139–178)

1. **Word count reduction** in `LeverCharacterization` Pydantic field descriptions
   and `ENRICH_LEVERS_SYSTEM_PROMPT`:
   - `description`: 80–100 → 50–70 words
   - `synergy_text`, `conflict_text`: 40–60 → 20–40 words

2. **Anti-echoing instruction** added to system prompt (line 171) and Pydantic
   field description (line 140).

### Does the implementation match the intent?

**Word count reduction — Yes.** Both the system prompt and the Pydantic field
descriptions are updated consistently. The targets are matched between the two
locations. The observed output (avg desc −28%, synergy −40%, conflict −41%) confirms
the targets are being hit.

**Anti-echoing — Partial.** The instruction is present in both locations, which
creates redundancy without adding clarity. More importantly, the "Do NOT repeat"
phrasing directly violates the OPTIMIZE_INSTRUCTIONS principle established in
`identify_potential_levers.py` for the same codebase:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat
> the prohibition text as a template."
The positive clause ("add new insight about why this lever matters and what success
looks like") is the useful part; the negative clause is the problematic part.
The insight confirms the result: percentage claims were reduced (haiku: 3 → 0)
but structural echoing of consequence vocabulary persists (N3).

### Gaps in the PR

1. **No defensive code fix for B1.** The insight's C1 recommendation — strip XML
   tags from `lever_id` before the map lookup — was identified as a low-risk fix
   in the same analysis cycle. The PR does not implement it. The XML tag format
   introduced in PR #466 was not guarded against in the output path.

2. **OPTIMIZE_INSTRUCTIONS not updated.** The `OPTIMIZE_INSTRUCTIONS` constant
   (line 73) still references "80-100 word target", which is now stale. The PR
   updates the functional code but does not update the documentation that guides
   future optimisation work.

3. **Anti-echoing instruction duplicated.** The "Do not repeat…" clause appears
   in both the Pydantic field description (line 140) and the system prompt (line 171).
   For function-calling models, the Pydantic field description is embedded in the
   JSON schema sent alongside the system prompt, so the instruction appears twice.
   Duplication adds prompt noise without benefit; it may confuse some models into
   treating it as a structural format requirement.

4. **No explicit `lever_id` output instruction.** The PR's Pydantic field
   description changes made the schema more prominent for non-function-calling
   models. Adding an explicit positive instruction about `lever_id` format
   (I4 above) would have been a natural companion to the other field-description
   changes.

### Regressions introduced

- **llama3.1 XML-tag-in-lever_id (B1):** Isolated to gta_game batch 1 in run 69,
  but the failure mode is systematic: the `<lever>uuid</lever>` prompt format
  plus the now-more-prominent Pydantic schema (with word-count constraints)
  altered llama3.1's parsing of the `lever_id` field. The code-level fix (B1/I1)
  would recover these levers without requiring further prompt changes.

---

## Summary

**PR #467's primary goal (gpt-oss-20b timeout fix) is correctly implemented.**
The ~35% word count reduction is confirmed in outputs and the two gpt-oss-20b
timeouts are eliminated. The code changes are coherent and the targets are
consistent between system prompt and Pydantic schema.

**Two confirmed bugs unrelated to the PR's stated goals, but exacerbated by it:**

- **B1** (`enrich_potential_levers.py:275`): No XML-tag stripping before the
  `enriched_levers_map` lookup. The `<lever>uuid</lever>` prompt format (PR #466)
  combined with PR #467's Pydantic field-description changes caused llama3.1 to
  copy the markup into the `lever_id` JSON field. The fix is a 4-line strip before
  the dict lookup.

- **B2** (`enrich_potential_levers.py:272`): `batches_succeeded` is incremented
  even when all characterizations in the batch return unrecognised `lever_id`
  values, giving a misleading success signal.

**Key design inconsistency (S1):** The anti-echoing instruction uses "Do NOT
repeat…" — a prohibited pattern per the project's own OPTIMIZE_INSTRUCTIONS.
This explains why N3 (structural echoing) persists despite the fix. A positive
reformulation (I3) would be more effective.

**Documentation gap (S3):** OPTIMIZE_INSTRUCTIONS still references the old
"80-100 word target" after PR #467 changed it to 50–70 words. This should be
updated to avoid misleading future optimisation iterations.

**Priority actions:**
1. Implement B1 fix (strip XML tags before map lookup) — low risk, recovers 5
   lost levers per affected batch.
2. Update OPTIMIZE_INSTRUCTIONS to reflect new word-count targets and document
   the XML-tag-in-lever_id failure mode.
3. Add positive `lever_id` output instruction to system prompt (I4).
4. Replace "Do NOT repeat" with a positive directive in description field (I3).
