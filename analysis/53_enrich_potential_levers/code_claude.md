# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — No retry on batch failure (enrich_potential_levers.py:209-213)

```python
except PipelineStopRequested:
    raise
except Exception as e:
    logger.error(f"LLM batch interaction failed for levers ...")
    raise ValueError("LLM batch interaction failed.") from e
```

Any exception in any single batch is immediately fatal for the entire plan — there is
no retry, no fallback to smaller batches, and no partial recovery. Compare with
`identify_potential_levers.py:329-348`, which has a 5-call retry loop that continues
accumulating levers even after individual call failures.

When gpt-oss-20b's third batch hits the 8192 output-token limit, the truncated JSON
causes a Pydantic `ValidationError`. That exception propagates to this handler, which
re-raises it, causing `_run_enrich` in `runner.py` to catch it and record the entire
plan as failed. The plan produces no output for any lever — even though the first two
batches succeeded.

### B2 — `full_lever_context_str` exposes full UUIDs, training models to use them (enrich_potential_levers.py:156)

```python
full_lever_context_str = "\n".join(
    [f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize]
)
```

This context string, shown to the LLM in every batch call, presents each lever as
`"- <full-UUID>: <name>"`. The format implicitly teaches models that the canonical
way to reference a lever is `Name (uuid)` or `uuid: Name`. Models with stronger
instruction-following (haiku, gpt-4o-mini) ignore the UUID; weaker models copy the
context format verbatim into their synergy/conflict text. There is no instruction in
the system prompt or field description specifying which format to use — the context
format is the only signal models receive.

The prompt does not say "use the lever's name only (not its ID)". Without that
instruction, models default to the most prominent format they were shown.

### B3 — Batch prompt omits `consequences` and `review` fields (enrich_potential_levers.py:171-173)

```python
lever_details_for_prompt = "\n\n".join(
    [f"Lever ID: {lever.lever_id}\nName: {lever.name}\nOptions: {json.dumps(lever.options)}"
     for lever in batch]
)
```

Each lever has five fields in `InputLever`: `lever_id`, `name`, `consequences`,
`options`, `review`. Only three are passed to the LLM. The `consequences` field
describes what happens when the lever is pulled — it is the most directly relevant
context for generating `description` and `conflict_text`. The `review` field names
the primary trade-off the lever introduces — exactly what `conflict_text` should
elaborate on.

Without `consequences` and `review`, the LLM must infer description and conflicts
from the lever name and three option strings alone. This produces generic
descriptions and weakly grounded conflict texts, since the model has no access to
the lever's documented downstream effects.

---

## Suspect Patterns

### S1 — `calls_succeeded=1` hardcoded regardless of actual batch count (runner.py:183)

```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=1,  # single batch call
)
```

For a 15-lever plan with `BATCH_SIZE=5`, `EnrichPotentialLevers.execute()` makes 3
LLM calls. The comment says "single batch call", which is incorrect for plans with
more than 5 levers. The `partial_recovery` event check at `runner.py:577-583` only
fires for `identify_potential_levers`, so the wrong value currently has no downstream
effect. However, if B1 is fixed to allow partial batch recovery, the hardcoded `1`
would prevent partial-recovery logging from working for enrich.

### S2 — Quantitative word count targets may drive qwen3-30b brevity (enrich_potential_levers.py:104-108 and ENRICH_LEVERS_SYSTEM_PROMPT:134-135)

The field descriptions specify "(80-100 words)" for `description` and "(40-60 words)"
for `synergy_text` and `conflict_text`. The system prompt repeats these targets.
qwen3-30b produces ~183-char synergy texts, approximately 35-40 words — right at or
just below the specified minimum. This suggests the model is treating "40-60 words"
as a ceiling target rather than a minimum quality floor, stopping once it reaches
roughly 40 words.

The same word-count target on `description` (80-100 words) is likely what drives
gpt-5-nano's formulaic "Purpose: / Objectives: / Key success metrics:" sub-structure
(N3): the model fills the required word budget by introducing sub-headers rather than
writing naturally at that length.

### S3 — Prohibition text in `consequences` field description may cause template lock (identify_potential_levers.py:115-119)

```python
consequences: str = Field(
    description=(
        "...Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field..."
    )
)
```

`OPTIMIZE_INSTRUCTIONS` (line 82) explicitly warns: "Do NOT add explicit prohibitions
naming banned phrases — small models treat the prohibition text as a template and copy
the banned phrases." This field description does exactly that: it names `'Controls ...'`
and `'Weakness:'` inside the prohibition, making them visible to the LLM. Weak models
may read this as instruction text and reproduce these strings. The fix (documented in
`OPTIMIZE_INSTRUCTIONS`) is to remove the phrase-specific prohibition and rely on the
system prompt examples plus structural validators.

---

## Improvement Opportunities

### I1 — Specify name-only cross-reference format in ENRICH_LEVERS_SYSTEM_PROMPT

Add an explicit instruction such as:

> "When referencing another lever in `synergy_text` or `conflict_text`, use the
> lever's **name only** (e.g., `Community Governance Model`). Do not include UUIDs,
> backtick formatting, or any other identifier."

Without this, the format of `full_lever_context_str` (B2) is the only signal, and
different models interpret it differently. This is the minimal fix for N4.

### I2 — Add qualitative mechanism guidance for synergy/conflict texts

The "(40-60 words)" target is purely quantitative. Replacing or supplementing it with:

> "Explain the specific mechanism or pathway through which the interaction operates —
> not just that an interaction exists. Write at least 2 substantive sentences."

would give models a qualitative floor that addresses qwen3-30b's brevity (N2). A
model that writes "Synergizes with X by reinforcing authority structures" (one short
sentence, ~40 words) would need to explain *how* or *why*, producing something closer
to haiku's 3-4 sentence explanations.

### I3 — Add per-batch retry with reduced batch size on token overflow

The simplest implementation: wrap the `llm_executor.run(execute_function)` call in a
try/except that checks whether `result["metadata"].get("output_tokens", 0) >= result["metadata"].get("num_output", float("inf")) - 100`, and if so, retries by splitting
the batch in half. A single retry at half batch size would solve the gpt-oss-20b
failure without requiring model-specific configuration.

Alternatively, catch the batch `Exception` at line 213, reduce `BATCH_SIZE` for the
remaining levers, and retry the current batch rather than immediately failing the
whole plan.

### I4 — Include `consequences` and `review` in batch prompt details

Change `lever_details_for_prompt` (B3) to:

```python
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}"
    for lever in batch
])
```

This gives the LLM direct access to the lever's documented effects and trade-offs
when writing `description` and `conflict_text`, producing more grounded output.

### I5 — Change `full_lever_context_str` to name-only format

As an immediate companion to I1, changing line 156 from:

```python
f"- {lever.lever_id}: {lever.name}"
```

to:

```python
f"- {lever.name}"
```

removes the UUID from the context format so models never see it as a referencing
pattern. The `lever_id` is still available to the LLM in `lever_details_for_prompt`
via `Lever ID:` prefix, but it won't appear in the cross-reference context string.

### I6 — Add OPTIMIZE_INSTRUCTIONS to enrich_potential_levers.py OPTIMIZE_INSTRUCTIONS

The known-problems list in `enrich_potential_levers.py:27-81` does not mention:
- The UUID cross-reference format problem (N4)
- The word-count-driven brevity pattern (N2/S2)
- The absence of retry on batch failure (B1)

These should be added so future prompt optimization experiments are aware of them.

---

## Trace to Insight Findings

| Insight finding | Code location | Root cause |
|---|---|---|
| N1 — gpt-oss-20b 0/5 failure | `enrich_potential_levers.py:209-213` | B1: no retry; one batch overflow kills entire plan |
| N1 — output token overflow | `enrich_potential_levers.py:84` + `209-213` | `BATCH_SIZE=5` fixed; no detection of `output_tokens >= num_output`; no reduction retry |
| N2 — qwen3-30b terse synergy/conflict | `enrich_potential_levers.py:104-108, 134-135` | S2: "(40-60 words)" interpreted as ceiling, not quality floor; no mechanism guidance |
| N3 — gpt-5-nano template structure | `enrich_potential_levers.py:101-103` + `ENRICH_LEVERS_SYSTEM_PROMPT:133` | S2: "(80-100 words)" budget filled by adding sub-headers; no structural guard |
| N4 — inconsistent UUID/name format | `enrich_potential_levers.py:156` + `ENRICH_LEVERS_SYSTEM_PROMPT:134-135` | B2: context shows `"- uuid: name"` with no instruction on which format to use |
| P5 — exactly 3 calls per plan | `enrich_potential_levers.py:84, 164` | `BATCH_SIZE=5`, 15 levers → 3 batches. Working as designed. |
| C1 — output-token overflow guard | `enrich_potential_levers.py:194-213` | No post-call token count check; no truncation detection before Pydantic validation |
| C2 — adaptive batch size | `enrich_potential_levers.py:84` | `BATCH_SIZE` is a module-level constant with no model-aware adjustment |
| C3 — standardize cross-reference format | `ENRICH_LEVERS_SYSTEM_PROMPT:134-135` | Prompt says "name one or two levers" but specifies no format |

---

## Summary

The `enrich_potential_levers.py` step has three code-level issues of different severity:

**B1 (high)** is the most impactful: a single batch exception immediately fails the
entire plan with no retry. This directly causes gpt-oss-20b's 0/5 failure rate. The
`identify_potential_levers.py` step has a 5-call adaptive retry loop as a mitigation
pattern; the enrich step has none. The fix is straightforward: catch the batch
exception, optionally retry with a smaller batch, and only fail the plan when all
retry attempts are exhausted.

**B2 (medium)** and **B3 (medium)** are both prompt construction issues. B2
(UUID-format context) is the direct cause of N4's cross-reference format
inconsistency. B3 (missing `consequences`/`review` in batch prompt) reduces the
contextual grounding available to the LLM when generating descriptions and conflict
texts. Both have simple fixes that don't require model-specific tuning.

The `identify_potential_levers.py` code is clean and its OPTIMIZE_INSTRUCTIONS are
well-maintained. The one flag (S3) is the `consequences` field description including
English keyword prohibitions, which violates the guidance in OPTIMIZE_INSTRUCTIONS
itself — but this appears to be a vestigial prohibition that predates the current
guidance, not a regression.

The most actionable changes, in priority order:
1. **B1**: Add per-batch retry with smaller batch on exception (fixes N1)
2. **B2 + I1 + I5**: Change `full_lever_context_str` to name-only and add explicit
   format instruction in system prompt (fixes N4)
3. **B3 + I4**: Include `consequences` and `review` in batch prompt (improves quality)
4. **I2**: Add qualitative mechanism guidance for synergy/conflict (addresses N2)
