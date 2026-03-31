# Code Review (claude)

## Bugs Found

### B1 — Prompt format / mapping-key mismatch (`enrich_potential_levers.py:247, 283`)

**The central bug of PR #462.**

The per-batch prompt labels each lever with a `"Lever "` prefix:

```python
# enrich_potential_levers.py:246-252
for idx, lever in enumerate(batch, start=1):
    index_to_full[str(idx)] = lever.lever_id          # key = "1", "2", …
    lever_details_for_prompt_parts.append(
        f"Lever {idx}\n"                               # label shown = "Lever 1", "Lever 2", …
        f"Name: {lever.name}\n"
        …
    )
```

The `index_to_full` dict uses `str(idx)` — bare integers — as keys.
The post-processing lookup at line 283 is:

```python
full_id = index_to_full.get(char.lever_id, char.lever_id)
```

Models that faithfully echo the prompt label (`"Lever 1"`) are not found in the dict
(key `"Lever 1"` ≠ `"1"`), so `char.lever_id` is returned unchanged. Since `"Lever 1"` is
not a UUID in `enriched_levers_map`, the characterization is recorded as an
`unknown_lever_id` error, and the corresponding lever in `enriched_levers_map` remains
without `description`/`synergy_text`/`conflict_text`, eventually yielding an `incomplete`
error at line 336.

**Effect**: every model that copies the label as-is loses 100% of its batch output.
llama3.1 loses all 35 levers. gpt-oss-20b loses 12/35. gpt-5-nano loses 13/35.
qwen3 and gpt-4o-mini each lose levers in edge-case batches.

**Fix options**:
- C1 (prompt side): Change the format string to remove the "Lever " prefix, e.g.
  `f"Lever ID: {idx}\n"` or simply `f"{idx}\n"`, and add an explicit instruction that
  the integer after "Lever ID:" is what the model must return as `lever_id`.
- C2 (code side): Normalize `char.lever_id` before the dict lookup — strip common
  prefixes such as `"Lever "` (case-insensitive) and surrounding whitespace.

---

### B2 — `LeverCharacterization.lever_id` type/description conflict (`enrich_potential_levers.py:139`)

```python
lever_id: str = Field(description="The integer identifier of the lever, as shown in the prompt")
```

The Pydantic type is `str` but the description says "integer identifier."
For function-calling models (haiku, gpt-5-nano), the JSON Schema generated from this field
shows `{"type": "string"}`. The description says "integer," the schema says string. The
prompt shows `"Lever 1"` (a phrase, not a bare integer). These three signals are mutually
inconsistent, which is why haiku makes redundant tool calls using the raw integer (`"4"`,
`"5"`) as `lever_id` in addition to its correctly mapped calls.

If the intent is to receive an integer, the field should be typed `int` and the mapping
key changed from `str(idx)` to `int(idx)` (or the lookup side-cast: `index_to_full.get(str(char.lever_id), …)`).
If the intent is to receive a string, the description should match: "The identifier string
exactly as it appears in the prompt (e.g., '1' or '2')."

---

## Suspect Patterns

### S1 — Global dispatcher registration not isolated per thread (`runner.py:248-251, 280-283`)

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)          # global object
```

`set_usage_metrics_path` uses thread-local storage (safe). But `dispatcher` is a
module-level singleton: `dispatcher.add_event_handler(track_activity)` appends to a global
handler list. When `workers > 1`, every concurrent plan's LLM events fire through every
registered handler. Plan A's `TrackActivity` receives events from plan B and vice-versa.
Practical impact is low because `track_activity_path.unlink(missing_ok=True)` at line 283
discards the file, but the cross-contamination means any activity-based diagnostics are
unreliable during parallel runs.

### S2 — Closure captures loop variable by reference (`enrich_potential_levers.py:266-273`)

```python
chat_message_list = [system_message, ChatMessage(role=MessageRole.USER, content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(BatchCharacterizationResult)
    chat_response = sllm.chat(chat_message_list)    # captured by reference
    …
```

`execute_function` captures `chat_message_list` by reference from the enclosing scope.
Because `llm_executor.run()` is synchronous, this is safe today — the closure is consumed
before the next loop iteration reassigns `chat_message_list`. However, if `run()` were ever
made asynchronous this would silently use the wrong batch's messages. The same pattern
exists in `identify_potential_levers.py:317-327` with `messages_snapshot`.

### S3 — OPTIMIZE_INSTRUCTIONS updated with a false claim (`enrich_potential_levers.py:89-97`)

The PR adds to `OPTIMIZE_INSTRUCTIONS`:

```
Integer indices work universally for both model types.
```

The experiment data directly contradicts this: 4 of 7 models fail or regress with integer
indices in their current form. The documentation should not assert "works universally"
since future developers will read this as validated and skip testing on affected models.

### S4 — `consequences` field description contains English-specific template prohibition (`identify_potential_levers.py:117-120`)

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"
```

`OPTIMIZE_INSTRUCTIONS` (lines 62–68) explicitly warns against embedding English-keyword
checks because PlanExe receives non-English prompts. The field description here is an LLM
instruction rather than a code validator, so the risk is lower — but it is inconsistent
with the documented principle and may confuse models responding in non-English languages.

---

## Improvement Opportunities

### I1 — Align prompt format with mapping key (fixes B1)

**Recommended fix**: change the per-batch lever header to use an unambiguous label that
makes it obvious the integer is the identifier:

```python
# Before (line 247):
f"Lever {idx}\n"

# After option A — bare integer with explicit key name:
f"Lever ID: {idx}\n"
# and update the system prompt: "return the integer shown after 'Lever ID:' as lever_id"

# After option B — bare integer:
f"{idx}\n"
```

Option A is preferable: "Lever ID: 1" has a clear key/value structure that text-completion
models parse more reliably than a bare `1`. Update `lever_id` field description to:
"The integer shown after 'Lever ID:' in the prompt (e.g., '1', '2')."

### I2 — Make mapping lookup prefix-tolerant as a defensive fallback (for B1)

Even after fixing the prompt format, adding a normalization step costs two lines and makes
the system robust against future prompt changes:

```python
raw_id = char.lever_id.strip()
if raw_id.upper().startswith("LEVER"):
    raw_id = raw_id[5:].strip()   # strips "Lever " or "LEVER " etc.
full_id = index_to_full.get(raw_id, char.lever_id)
```

### I3 — Type `lever_id` as `int` in `LeverCharacterization` (fixes B2)

Declaring the field as `int` aligns the JSON Schema type with the description, gives
function-calling models an unambiguous signal, and eliminates the "Lever 1" string echo:

```python
lever_id: int = Field(description="The integer identifier of the lever (e.g., 1, 2, 3).")
```

The mapping lookup becomes: `index_to_full.get(str(char.lever_id), char.lever_id)`.

### I4 — Include integer indices in `full_lever_context_str`

Currently `full_lever_context_str` (line 216) shows only names:

```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

Adding the global indices (which differ from per-batch indices) would confuse rather than
help. Leave this as-is. Instead, the per-batch prompt should be unambiguous enough that
models know exactly what integer to return.

### I5 — Update OPTIMIZE_INSTRUCTIONS to document the "Lever N" label-echo problem

Add to the known-problems list in `enrich_potential_levers.py`:

> "Lever N" label copying. When levers are labeled "Lever 1", "Lever 2", etc., several
> text-completion models return the full label verbatim as lever_id instead of the bare
> integer. The mapping code uses str(idx) as the dict key; "Lever 1" does not match "1".
> Ensure the prompt label format and the mapping key format are identical, or normalize
> the prefix before the dict lookup. Do NOT claim integer indices "work universally" until
> tested across ≥5 models including llama3.1.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| N1 — llama3.1 0/35 levers | B1: `"Lever1"` / `"Lever 2"` not in `index_to_full`; all 35 levers → `unknown_lever_id` + `incomplete` |
| N2 — gpt-oss-20b 23/35 levers | B1: same pattern; some batches use bare integer and succeed, others echo the label |
| N3 — gpt-5-nano 22/35 levers | B1: function-calling model, but still echos label for some plan/batch combos |
| N4 — haiku 22 extra unknown_lever_id with raw integers | B2: `lever_id: str` described as "integer" causes haiku to make extra tool calls returning `"4"`, `"5"`, … directly |
| N5 — qwen3 and gpt-4o-mini minor losses | B1: last-batch label echo in multi-batch plans |
| N6 — root cause statement | B1 as described: format `"Lever N"` vs key `"N"` mismatch |
| S3 — false OPTIMIZE_INSTRUCTIONS claim | PR adds "works universally" which experiments refute |

---

## PR Review

### Intent vs. implementation

The PR correctly identifies the problem (UUIDs in the per-batch prompt cause llama3.1 to
copy them into `lever_id` and free-text fields) and applies a sound architectural fix
(integer indices + post-processing map). The design is correct in principle.

The implementation has one critical gap: **B1** — the prompt format `"Lever {idx}"` is
inconsistent with the mapping key `str(idx)`. The prompt shows `"Lever 1"`; the code
expects `"1"`. Models that reproduce the label as-is (the majority) fail the lookup.

### What the PR gets right

- Removes `Lever ID: {uuid}` from the per-batch prompt — eliminates UUID leakage source.
- Builds the `index_to_full` dict at the right place (per-batch, reset each iteration).
- Post-processing maps back before writing to `enriched_levers_map` — correct location.
- Adds positive framing in system prompt ("refer to levers by name, not an identifier") — aligns with known-problems guidance in OPTIMIZE_INSTRUCTIONS.
- Adds "Return exactly N characterizations" instruction.

### What the PR gets wrong

1. **Prompt/key mismatch (B1)**: `f"Lever {idx}\n"` vs `str(idx)`. One-line fix. This is
   the sole cause of all 152 new errors.

2. **`lever_id` field type (B2)**: `str` type with "integer identifier" description is
   ambiguous. Haiku's extra integer-id tool calls trace here.

3. **False OPTIMIZE_INSTRUCTIONS claim (S3)**: States "Integer indices work universally"
   before verifying across models. Should be conditional: "when the prompt format and
   mapping key format match."

4. **PR description claim "Works universally for both text-completion and function-calling
   models"**: Directly falsified by the experiment — 4/7 models fail or regress.

### Verdict

The PR should be **reverted** in its current form. The implementation bug (B1) is a single
format-string change, but until that fix is tested, the regression to llama3.1 (0/35 levers,
was 35/35) makes the PR a net negative. Fix B1 + B2 and re-run the full model suite before
merging.

---

## Summary

PR #462 introduces one confirmed bug (B1) and one type-conflict (B2) in
`enrich_potential_levers.py`.

**B1** is the root cause of all 152 new errors across 4 models: the per-batch prompt labels
levers as `"Lever 1"`, `"Lever 2"` (lines 246–252) while the `index_to_full` mapping keys
are `"1"`, `"2"` (line 245). The post-processing at line 283 performs an exact dict lookup
— `"Lever 1"` ≠ `"1"` — so any model that echoes the prompt label produces
`unknown_lever_id` + `incomplete` errors for the entire batch. This is a one-character
class of bug (missing a prefix-strip or a consistent format string) that collapses llama3.1
from 35/35 to 0/35 levers.

**B2** (`lever_id: str` typed as "integer identifier") contributes to haiku's 22 spurious
`unknown_lever_id` errors with raw integer strings. The type and description are
inconsistent; function-calling models use the JSON Schema type (`str`) but the description
instructs "integer," producing redundant calls.

`runner.py` has a latent cross-contamination risk (S1) in multi-worker runs due to the
global dispatcher handler list, but practical impact is low because TrackActivity data is
discarded before use.

The `OPTIMIZE_INSTRUCTIONS` constant in `enrich_potential_levers.py` should be corrected
to remove the false "works universally" claim added by this PR, and should instead document
the "Lever N label-echo" pattern as a new known problem.
