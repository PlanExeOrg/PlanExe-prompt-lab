# Synthesis

## Cross-Agent Agreement

Both insight and code review agree on every major finding:

1. **B1 is the sole root cause of all 152 new errors.** The per-batch prompt labels levers
   `"Lever 1"`, `"Lever 2"` (line 247: `f"Lever {idx}\n"`), but `index_to_full` keys are
   bare integers `"1"`, `"2"` (line 245: `index_to_full[str(idx)]`). The post-processing
   lookup at line 283 is an exact match — `"Lever 1"` ≠ `"1"` — so any model that echoes
   the label gets `unknown_lever_id` + `incomplete` for the entire batch. This is a one-line
   bug that collapses llama3.1 from 35/35 to 0/35 levers.

2. **B2 contributes to haiku's 22 spurious errors.** `lever_id: str` with description
   "integer identifier" sends contradictory signals to function-calling models; haiku makes
   redundant tool calls using raw integers as `lever_id`.

3. **The core design is sound.** Integer indices replace UUID-in-prompt leakage cleanly.
   Gemini achieves 35/35 with 0 UUID contamination. The architecture is right; the
   implementation has a fixable format mismatch.

4. **The OPTIMIZE_INSTRUCTIONS false claim must be corrected.** The PR added "Integer
   indices work universally for both model types" before running the full model suite.
   Four of seven models fail or degrade.

5. **Verdict: REVERT.** Before (PR #457): 209 levers, 20 UUID occurrences (llama3.1 only).
   After (PR #462): 178 levers, 0 UUID occurrences. Losing 31 levers (–14.8%) for all
   models to gain 0 UUID occurrences in one model's free-text is a net regression.

## Cross-Agent Disagreements

Only one agent reviewed both dimensions (insight and code review were both produced by
claude), so there are no inter-agent disagreements. All claims are internally consistent and
verified against the source.

**Source-code verification of key claims:**

- Line 245: `index_to_full[str(idx)] = lever.lever_id` — confirmed, bare integer string key.
- Line 247: `f"Lever {idx}\n"` — confirmed, "Lever N" prefix in prompt label.
- Line 283: `full_id = index_to_full.get(char.lever_id, char.lever_id)` — confirmed, exact
  lookup with no prefix normalization.
- Line 139: `lever_id: str = Field(description="The integer identifier of the lever, as
  shown in the prompt")` — confirmed, `str` type with "integer identifier" description.
- OPTIMIZE_INSTRUCTIONS lines 89–97: confirmed, "Integer indices work universally for both
  model types." — this false claim is present in the current source.

## Top 5 Directions

### 1. Fix the prompt format / mapping-key mismatch (B1)
- **Type**: code fix
- **Evidence**: Both agents identify this as the sole cause of all 152 new errors. Confirmed
  in source at lines 245–247 and 283. Affected: llama3.1 (–35 levers), gpt-oss-20b (–12),
  gpt-5-nano (–13), qwen3 (–2), gpt-4o-mini (–5).
- **Fix**: Change line 247 from `f"Lever {idx}\n"` to `f"Lever ID: {idx}\n"` (or bare
  `f"{idx}\n"`). Update `lever_id` field description at line 139 to: `"The integer shown
  after 'Lever ID:' in the prompt (e.g., '1', '2')."` The `"Lever ID: N"` form is
  preferable to bare `"N"` because text-completion models parse key/value lines more reliably
  than a lone digit.
- **Impact**: Recovers all 31 lost levers across 5 models. Enables the PR's UUID elimination
  goal to be realized universally. The aggregate lever recovery rate rises from 73% back to
  ~100%.
- **Effort**: Low — one format string change + one field description update.
- **Risk**: Minimal. "Lever ID: 1" is unambiguous. If a model still echoes "Lever ID: 1"
  rather than "1", direction #2 (prefix stripping) catches it as a fallback.

### 2. Add prefix-tolerant normalization to the mapping lookup (I2/C2)
- **Type**: code fix (defensive)
- **Evidence**: Code review flags this as a robust complement to direction #1. Cost is two
  lines. Makes the system tolerant of future prompt-wording changes.
- **Fix**: At line 283, replace:
  ```python
  full_id = index_to_full.get(char.lever_id, char.lever_id)
  ```
  with:
  ```python
  raw_id = char.lever_id.strip()
  if raw_id.upper().startswith("LEVER"):
      raw_id = raw_id[5:].strip()   # strips "Lever ", "LEVER", etc.
  full_id = index_to_full.get(raw_id, char.lever_id)
  ```
- **Impact**: Defensive fallback. If a future prompt change reintroduces a prefix, this
  normalization absorbs it without requiring another iteration. Also recovers any remaining
  "Lever N" echoes even if direction #1 is applied.
- **Effort**: Low.
- **Risk**: Near-zero. The normalization only activates if `char.lever_id` starts with
  "LEVER" (case-insensitive); valid integer strings and UUIDs pass through unchanged.

### 3. Fix `lever_id` field type/description mismatch (B2)
- **Type**: code fix
- **Evidence**: Code review B2. `lever_id: str` described as "integer identifier" sends
  contradictory signals to function-calling models. Haiku produces 22 spurious extra tool
  calls using raw integer strings (`"4"`, `"5"`) as `lever_id` because JSON Schema says
  `string` but the description says `integer`.
- **Fix option A (preferred)**: Change the field to `int`:
  ```python
  lever_id: int = Field(description="The integer identifier of the lever (e.g., 1, 2, 3).")
  ```
  And update the mapping lookup: `index_to_full.get(str(char.lever_id), char.lever_id)`.
  This aligns JSON Schema type, description, and mapping key — function-calling models get
  a single unambiguous signal.
- **Fix option B** (lower-risk): Keep `str` but clarify the description to match:
  `"The identifier string exactly as it appears after 'Lever ID:' in the prompt (e.g., '1', '2')."`.
- **Impact**: Eliminates haiku's 22 spurious `unknown_lever_id` errors. Also reduces
  ambiguity for all function-calling models (gpt-5-nano, gpt-4o-mini, gemini).
- **Effort**: Low.
- **Risk**: Changing to `int` requires updating the lookup side-cast and ensuring all
  downstream code that reads `char.lever_id` handles `int`. Option B avoids this risk at
  the cost of leaving the type inconsistency in place.

### 4. Correct the false OPTIMIZE_INSTRUCTIONS claim and add "Lever N label-echo" pattern (S3/H1)
- **Type**: documentation (prompt change in `enrich_potential_levers.py`)
- **Evidence**: S3 from code review. The PR added "Integer indices work universally for both
  model types" to OPTIMIZE_INSTRUCTIONS at lines 89–97. The experiment directly refutes this:
  4/7 models fail or degrade. A future developer reading this will skip cross-model testing
  on the assumption it is already validated.
- **Fix**: Remove "Integer indices work universally for both model types." Replace with:
  > Integer indices work correctly only when the prompt label format and the mapping key
  > format are identical. When levers are labeled "Lever N" in the prompt but the mapping
  > key is the bare integer "N", text-completion models (llama3.1, gpt-oss-20b, qwen3) echo
  > the full label as `lever_id` and fail the dict lookup. Use "Lever ID: N" or bare "N"
  > consistently on both sides, and add prefix-stripping normalization to the lookup as a
  > fallback. Do NOT claim integer indices "work universally" until tested on ≥5 models
  > including llama3.1.
- **Impact**: Prevents the next optimizer from shipping the same bug. High documentation
  value, zero runtime cost.
- **Effort**: Low.
- **Risk**: None.

### 5. Add explicit lever-ID format instruction to the per-batch user prompt (H2)
- **Type**: prompt change
- **Evidence**: H2 from insight agent. Even with the format label fixed, some models may
  still echo the full label. An explicit instruction in the user prompt removes ambiguity.
- **Fix**: After the lever list in `user_prompt` (line 263–264), add:
  > "For each lever's `lever_id`, return the integer number shown after 'Lever ID:' (e.g.,
  > if the section begins with 'Lever ID: 3', set lever_id to '3')."
- **Impact**: Additional safety net for text-completion models. Reduces residual name-echo
  errors on edge-case batches (the qwen3 and gpt-4o-mini failures in large multi-batch
  plans with ambiguous lever names).
- **Effort**: Low.
- **Risk**: Slight prompt verbosity increase. Unlikely to cause regressions.

## Recommendation

**Do direction #1 first, bundled with directions #2 and #4.**

Direction #1 is the minimum viable fix: change line 247 from `f"Lever {idx}\n"` to
`f"Lever ID: {idx}\n"` and update the `lever_id` field description at line 139 to match.
This is the exact format mismatch that causes all 152 errors and 31 lost levers.

Bundling direction #2 (prefix stripping) costs two extra lines and makes the fix robust
against model variation. Bundling direction #4 (OPTIMIZE_INSTRUCTIONS correction) takes
two minutes and prevents the same bug from being reintroduced.

**Specific changes:**

`enrich_potential_levers.py` line 139:
```python
# Before:
lever_id: str = Field(description="The integer identifier of the lever, as shown in the prompt")

# After:
lever_id: str = Field(description="The integer shown after 'Lever ID:' in the prompt (e.g., '1', '2').")
```

`enrich_potential_levers.py` line 247:
```python
# Before:
f"Lever {idx}\n"

# After:
f"Lever ID: {idx}\n"
```

`enrich_potential_levers.py` line 283:
```python
# Before:
full_id = index_to_full.get(char.lever_id, char.lever_id)

# After:
raw_id = char.lever_id.strip()
if raw_id.upper().startswith("LEVER"):
    raw_id = raw_id[5:].strip()
full_id = index_to_full.get(raw_id, char.lever_id)
```

`enrich_potential_levers.py` OPTIMIZE_INSTRUCTIONS (~line 97): Replace
`"Integer indices work universally for both model types."` with the corrected language
from direction #4.

**Expected outcome**: llama3.1 recovers from 0/35 to ~35/35. gpt-oss-20b and gpt-5-nano
recover from ~23/35 and 22/35 to near-100%. haiku's 22 spurious errors drop to near-zero.
qwen3 and gpt-4o-mini recover 2 and 5 lost levers. Total: ~209 levers characterized (up
from 178), 0 UUID contamination.

## Deferred Items

- **Direction #3 (B2 type fix)**: Change `lever_id` to `int` or clarify its description.
  Worth doing in the same PR but not blocking — direction #2's prefix stripping absorbs
  haiku's raw-integer edge cases even without the type change. Validate on a second run
  before merging.

- **Direction #5 (H2 explicit ID instruction)**: Low priority. Add after direction #1
  fixes are confirmed effective. Useful if residual edge-case failures remain on
  large-batch plans.

- **S4 (English-specific prohibition in `identify_potential_levers.py:117–120`)**: The
  `consequences` field description contains `'Controls ... vs.', 'Weakness:'` — English
  keywords that OPTIMIZE_INSTRUCTIONS warns against. This is a mild inconsistency (LLM
  instruction, not a code validator), lower risk than the validated prohibition pattern.
  Fix in a separate iteration focused on identify_potential_levers quality.

- **S1 (global dispatcher cross-contamination in runner.py)**: Practical impact is low
  because `track_activity_path.unlink()` discards the data before use. Address if
  parallel-run diagnostics are ever needed for debugging.

- **S2 (closure captures loop variable by reference)**: Safe today because `run()` is
  synchronous. Document the risk in a comment if async execution is ever planned.
