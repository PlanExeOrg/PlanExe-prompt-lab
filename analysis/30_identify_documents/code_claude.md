# Code Review (claude)

## Bugs Found

### B1 — `OPTIMIZE_INSTRUCTIONS` defined but never injected into system prompt
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:257–264, 320–331`

`OPTIMIZE_INSTRUCTIONS` is a module-level constant containing critical output constraints:
- `All string fields: maximum 120 characters`
- `steps_to_create / steps_to_find: maximum 3 items per document`
- `If token pressure rises, shorten descriptions — never truncate JSON mid-string`

But it is never referenced in `execute()`. The `system_prompt` variable is set to one of
the three static prompt strings and passed directly to the LLM without appending
`OPTIMIZE_INSTRUCTIONS`. The constant is dead code.

```python
# execute() at line 320–331 — OPTIMIZE_INSTRUCTIONS never used:
system_prompt = system_prompt.strip()
chat_message_list = [
    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
    ChatMessage(role=MessageRole.USER, content=user_prompt),
]
```

This is the primary root cause of the truncation failures (insight N2, N4). Haiku generates
~700-char descriptions and verbose `steps_to_create` lists because the model never receives
the 120-character constraint or the 3-step limit.

---

### B2 — `partial_recovery` event fires for every `identify_documents` run due to hardcoded `expected_calls=3`
**File:** `self_improve/runner.py:155, 514–518`

`_run_documents()` always returns `calls_succeeded=1` (hardcoded):
```python
# runner.py:150–156
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=1,   # <-- hardcoded
)
```

Then `_run_plan_task()` unconditionally fires `partial_recovery` whenever
`calls_succeeded < 3`, regardless of which step is running:
```python
# runner.py:514–518
if pr.calls_succeeded is not None and pr.calls_succeeded < 3:
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)   # <-- always 3, for all steps
```

`IdentifyDocuments.execute()` is a single-call step by design. There are no "calls 2
and 3" to fail. The `partial_recovery` event with `expected_calls=3` fires on every
successful run, producing 35/35 false-positive events in the dataset. The number `3` is
specific to `identify_potential_levers` and was never updated when the step counter was
separated between steps.

By contrast, `_run_levers()` at line 116 computes `actual_calls = len(result.responses)`
dynamically and sets `calls_succeeded=actual_calls`. The `identify_documents` runner
function was never updated to match.

---

### B3 — No deduplication in `cleanup()` across `part1` and `part2`
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:388–426`

`cleanup()` merges `documents_to_create + documents_to_create_part2` and
`documents_to_find + documents_to_find_part2` but performs no deduplication by
`document_name`:

```python
# identify_documents.py:394–395
documents_to_create = document_details.documents_to_create + document_details.documents_to_create_part2
for item in documents_to_create:
    # no seen_names check — duplicates pass through
```

The `_part2` field description says "Do not repeat documents already identified in
the first pass" but this is only a prompt instruction, not enforced in code. When the
model ignores this instruction, duplicates flow silently into the output files.

Compare `identify_potential_levers.py:331–337` which has explicit deduplication:
```python
seen_names: set[str] = set()
for i, lever in enumerate(levers_raw, start=1):
    if lever.name in seen_names:
        logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
        continue
    seen_names.add(lever.name)
```

The `identify_documents` cleanup lacks the equivalent guard.

---

## Suspect Patterns

### S1 — `OPTIMIZE_INSTRUCTIONS` contradicts the Pydantic schema on total item count
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:257–264, 86–101`

`OPTIMIZE_INSTRUCTIONS` says:
> `documents_to_create: maximum 6 items total across both passes`

But the schema allows `max_length=6` for `documents_to_create` plus `max_length=3` for
`documents_to_create_part2`, totalling up to 9 — not 6. If `OPTIMIZE_INSTRUCTIONS` were
ever injected (it currently isn't, per B1), the model would receive contradictory guidance:
the prompt says ≤6 total while the schema silently accepts up to 9.

---

### S2 — `steps_to_create` / `steps_to_find` lack `max_length` in Pydantic schema
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:51, 78`

`OPTIMIZE_INSTRUCTIONS` specifies a maximum of 3 items per document for `steps_to_create`
and `steps_to_find`, but neither field carries a `max_length=3` Pydantic constraint.
A verbose model can return 10+ steps per document, significantly inflating response size
without triggering a validation error. Since B1 means the soft constraint is also missing,
there is no ceiling on steps list length at all.

---

### S3 — No `min_length` on any `DocumentDetails` list field
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:86–101`

All four list fields have `max_length` but no `min_length`. A model could return an
empty `documents_to_create: []` and pass Pydantic validation without any warning. This
creates a silent failure mode that is harder to diagnose than a Pydantic error.

---

### S4 — `_run_documents()` does not propagate success/call metadata from `IdentifyDocuments`
**File:** `self_improve/runner.py:129–156`

`_run_documents()` wraps `IdentifyDocuments.execute()` in `llm_executor.run()` to get
retry/fallback behaviour, but the returned `PlanResult` carries no metadata about which
LLM model was actually used (primary vs. fallback) or how many LLM retries were attempted.
`_run_levers()` has the same gap. This makes post-hoc analysis harder when the executor
falls back to a secondary model.

---

## Improvement Opportunities

### I1 — Inject `OPTIMIZE_INSTRUCTIONS` into the system prompt
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:320`

Append `OPTIMIZE_INSTRUCTIONS` to the selected `system_prompt` before building
`chat_message_list`. This would deliver the 120-char string limit and the 3-step-per-doc
limit to every model and is the minimal fix for truncation. Before doing so, the
contradiction in S1 should also be resolved (align OPTIMIZE_INSTRUCTIONS to say ≤9 total
across both passes, matching the schema).

---

### I2 — Return `calls_succeeded=None` from `_run_documents()` to suppress false `partial_recovery` events
**File:** `self_improve/runner.py:155`

The cleanest fix for B2 is to return `calls_succeeded=None` from `_run_documents()`.
The `_run_plan_task()` check already guards with `if pr.calls_succeeded is not None`,
so a `None` value would silently skip the check without touching the shared event logic.
No other files need to change.

Alternatively, make the `expected_calls` value step-specific by passing it through
`PlanResult` rather than hardcoding `3` in `_run_plan_task()`.

---

### I3 — Add `document_name` deduplication in `cleanup()`
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:394, 410`

Mirror the `seen_names` guard from `identify_potential_levers.py:331–337` in both the
`documents_to_create` and `documents_to_find` merge loops. Exact-match deduplication is
cheap and directly prevents the llama3.1 "Hong Kong Labour Laws and Regulations" duplicate
(insight N5).

---

### I4 — Add `max_length=3` to `steps_to_create` and `steps_to_find` in schema
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:51, 78`

Adds structural enforcement to match the intent already expressed in `OPTIMIZE_INSTRUCTIONS`.
Each document's step list is the second-largest driver of response size after the
description strings.

---

### I5 — Add `min_length=1` to `documents_to_create` and `documents_to_find`
**File:** `worker_plan/worker_plan_internal/document/identify_documents.py:86–90`

Prevents silent empty-list responses from passing validation undetected.

---

## Trace to Insight Findings

| Insight finding | Code root cause |
|---|---|
| **N2** — JSON truncation still happens despite PR (haiku ~40 KB responses) | **B1**: `OPTIMIZE_INSTRUCTIONS` never injected; 120-char limit never sent to model; haiku generates ~700-char descriptions unconstrained |
| **N3** — partial_recovery universal: calls_succeeded=1, expected_calls=3 across all 35 runs | **B2**: `_run_documents()` hardcodes `calls_succeeded=1`; `_run_plan_task()` hardcodes `expected_calls=3` for all steps; `identify_documents` is a single-call step so this always fires as a false positive |
| **N4** — Haiku catastrophic failure (4/5 plans failed via truncation and max_length) | **B1** (truncation via verbose output): constraints never delivered; **PR B2** (max_length): hard cap rejects responses instead of trimming |
| **N5** — Duplicate documents in llama3.1 output | **B3**: `cleanup()` lacks `seen_names` deduplication |
| **N6** — Document count gap vs baseline (9 max vs 17 baseline) | PR adds `max_length=6+3=9`; **S1**: OPTIMIZE_INSTRUCTIONS says 6 total but schema allows 9 — neither matches the 17-item baseline |
| **N7** — llama3.1 produces short, generic descriptions | Not a code bug — model capability; but **B1** means no minimum-length guidance reaches the model either |
| **P3** — No schema structural failures for models within bounds | Schema design is sound; failures are prompt/constraint delivery failures |

---

## PR Review

**PR #342: "fix: cap DocumentDetails list fields to reduce IdentifyDocumentsTask output size"**

### What the PR changed

Added `max_length` constraints to `DocumentDetails` fields:
- `documents_to_create`, `documents_to_find`: `max_length=6`
- `documents_to_create_part2`, `documents_to_find_part2`: `max_length=3`
- Updated field description strings to mention the limits

### Does the implementation match the intent?

Partially. The intent was to prevent JSON truncation by reducing total output size.
The implementation adds Pydantic hard caps, which rejects entire responses rather than
trimming them. This is the mechanism described in AGENTS.md §"Pydantic hard constraints
vs soft prompt guidance" as the incorrect approach.

### Gaps and new issues

**Gap 1 — Does not address per-item verbosity.**
The PR caps item count but not description length or steps-list size. Haiku generates
~700-char descriptions. With `max_length=6`, the total response is still ~4–5 KB per
field, still large enough for truncation (~40 KB observed). The root cause of truncation
is verbosity-per-item, not item count. The PR attacked the wrong dimension.

**Gap 2 — Does not fix `OPTIMIZE_INSTRUCTIONS` not being injected (B1).**
The actual verbosity constraint (`All string fields: maximum 120 characters`) already
exists in `OPTIMIZE_INSTRUCTIONS` but was never delivered to the model. The PR added a
second layer of constraint (Pydantic hard cap on item count) while leaving the first
layer (soft prompt verbosity guidance) missing. Fixing B1 alone would have been a
lower-risk intervention.

**New issue — Hard cap causes full-response rejection.**
When haiku returns 12 items, the Pydantic `too_long` error discards all tokens. A soft
prompt instruction ("Identify 4–8 documents") or downstream trimming would have accepted
and used 6 of the 12 rather than discarding all 12. This is the direct cause of the
`LLMChatError` failures in runs 21 (gpt-4o-mini) and 23 (haiku-4-5).

**New issue — Schema cap contradicts `OPTIMIZE_INSTRUCTIONS` total.**
`OPTIMIZE_INSTRUCTIONS` says "maximum 6 items total across both passes" but the schema
now allows 6 (part1) + 3 (part2) = 9 total. If `OPTIMIZE_INSTRUCTIONS` were ever
injected (see B1), the model would receive contradictory instructions.

**New issue — `_part2` fields are conceptually broken under tight caps.**
The design intent of `_part2` is overflow: documents the model identified late in its
reasoning that didn't fit in part1. With `max_length=6` on part1, the model fills part1
to 6 items (or fewer). With `max_length=3` on part2, it gets 3 more slots. But the PR's
stated goal is reducing output size — allowing 9 total is a larger cap than either field
alone. A single field with `max_length=9` would be simpler, cap-equivalent, and avoid the
inconsistency.

### Verdict

The PR provides partial mitigation for well-behaved models (llama3.1, gemini, gpt-5-nano)
that stay within the cap, adding a safety net at no cost for those models. But it:

1. Introduces new hard failures for models that over-generate (haiku, gpt-4o-mini)
2. Doesn't fix the actual truncation root cause (per-item verbosity, B1)
3. Creates a schema vs. OPTIMIZE_INSTRUCTIONS contradiction (S1)

The PR should be revisited. Recommended minimal changes: raise caps to 12–15 (safety net
only), fix B1 to actually deliver the 120-char constraint, and add downstream trimming
so over-generation is handled gracefully rather than rejected.

---

## Summary

The two most impactful bugs are:

**B1** (`OPTIMIZE_INSTRUCTIONS` never injected): The 120-character string limit and
3-step-per-document limit are defined but never sent to any model. This is the primary
cause of haiku's ~700-char descriptions and the resulting 40 KB JSON truncations. It
also explains why PR #342's item-count cap failed to prevent truncation for haiku.

**B2** (false `partial_recovery` events): `_run_documents()` hardcodes `calls_succeeded=1`
and `_run_plan_task()` hardcodes `expected_calls=3` for all steps. Since
`identify_documents` is a single-call step, every run fires `partial_recovery` as a
false positive. The insight file's conclusion that "filter calls always fail" is a
misreading of this monitoring bug — there are no filter calls to fail.

**B3** (no deduplication in `cleanup()`): The `identify_potential_levers` step has
`seen_names` deduplication; `identify_documents` does not. This is the direct cause
of the llama3.1 "Hong Kong Labour Laws" duplicate (insight N5).

PR #342's core design error is using Pydantic hard caps (which reject responses) instead
of soft prompt guidance or downstream trimming (which accept-and-trim responses). The cap
that was needed — on per-item description length — was already written in `OPTIMIZE_INSTRUCTIONS`
but is unreachable due to B1.
