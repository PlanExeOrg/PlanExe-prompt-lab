# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #458 "Add UUID prohibition and exact-count instruction to enrich prompts"

---

## Bugs Found

### B1 — Negative-instruction priming introduced by UUID prohibition (PR #458)
**File:** `enrich_potential_levers.py:178` (`ENRICH_LEVERS_SYSTEM_PROMPT`)

PR #458 added:
```
**Important:** In `synergy_text` and `conflict_text`, refer to other levers by NAME only.
Do NOT include any Lever ID, UUID, or identifier string in these fields.
```

This is a negative prohibition that names the exact string format llama3.1 uses: `lever ID: xxx`. The OPTIMIZE_INSTRUCTIONS constant in `identify_potential_levers.py` at lines 82–83 explicitly warns:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."

The insight confirms the regression: the sovereign_identity plan, which had zero UUID occurrences in run 4/27, now has 20 UUID occurrences in synergy/conflict text in run 4/34 (every lever × both fields × 2 UUIDs per field). The prohibition instruction named "Lever ID" — llama3.1's exact output pattern — and appears to have raised its salience for plans that previously did not use it. This is a code-level enactment of the negative-priming problem already documented in `identify_potential_levers.py`'s OPTIMIZE_INSTRUCTIONS, but that warning was not consulted when writing the enrich prompt.

Net result: gta_game improved (synergy/conflict UUIDs ≈ –19) but sovereign_identity regressed (+20), leaving the total UUID count in text fields unchanged at 29.

---

### B2 — No code-level trim for haiku over-generation; exact-count instruction is the only guard
**File:** `enrich_potential_levers.py:277–286`

After PR #458 the user prompt says "Return exactly {len(batch)} characterizations." This reduces haiku errors from 7 to 2, but 2 residual errors remain. The code after parsing does:

```python
for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        enriched_levers_map[char.lever_id].update(...)
    else:
        logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
        errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

When the model returns `len(batch) + 1` characterizations, the extra (which has a fabricated UUID not in `enriched_levers_map`) is logged as an error and silently discarded. The correct levers are still enriched. But the error entry is noise, and no client-side guard prevents this from happening. A pre-loop trim — `characterizations = batch_result.characterizations[:len(batch)]` — would discard the extras before the ID lookup, eliminating all `unknown_lever_id` errors for this class of over-generation. The insight confirms the real levers always appear first, so trimming to the expected count is safe.

---

### B3 — False positive `partial_recovery` events for successful 2-call lever runs
**File:** `runner.py:131–133`, `runner.py:577–583`

Carries over from analysis 60 (B5). Not addressed by PR #458.

```python
# runner.py:131
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

```python
# runner.py:577
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The comment at lines 127–130 states "A 2-call success is normal for models that produce 8+ levers per call." Yet both the warning and the `partial_recovery` event fire for `calls_succeeded=2`, which includes perfectly healthy runs. This creates misleading noise in `events.jsonl`. The threshold should be `< 2` (only 1 call succeeded), or a separate signal (e.g., a call failure count) should drive the event.

---

### B4 — `errors` field type annotation mismatches its default
**File:** `enrich_potential_levers.py:189`

Carries over from analysis 60 (B2). Not addressed by PR #458.

```python
errors: List[Dict[str, Any]] = None
```

Declared type is `List[Dict[str, Any]]` but the default is `None`. The `__post_init__` guard (lines 191–192) handles it at runtime. Static type checkers (mypy, pyright) flag every callsite. Should be `Optional[List[Dict[str, Any]]] = None`.

---

## Suspect Patterns

### S1 — Global dispatcher shared across parallel plan workers
**File:** `runner.py:248–251`, `runner.py:280–282`

Carries over from analysis 60 (S1). Not addressed by PR #458.

```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path` is thread-local, but `dispatcher` is a global singleton. When `workers > 1`, all plan `TrackActivity` handlers are registered simultaneously. LLM events from any thread fire all handlers. Whether this causes cross-plan log contamination depends on whether `TrackActivity` filters by thread ID — worth confirming.

---

### S2 — `__main__` test block in `enrich_potential_levers.py` uses wrong JSON shape
**File:** `enrich_potential_levers.py:374–376` vs `runner.py:172–173`

Carries over from analysis 60 (S2). Not addressed by PR #458.

`runner.py` extracts `json_dict["deduplicated_levers"]` before passing to `EnrichPotentialLevers.execute`. The `__main__` block passes the entire `json.load(f)` result. If the deduplicated file has the top-level `{"deduplicated_levers": [...]}` structure (which it does, per runner.py), the `__main__` block will pass a dict with a single `"deduplicated_levers"` key as the lever list, causing `InputLever(**lever)` to fail. The standalone test runner is broken for real pipeline output.

---

### S3 — `Lever.consequences` field description uses English-specific negative prohibition
**File:** `identify_potential_levers.py:114–120`

Carries over from analysis 60 (S3). Not addressed by PR #458.

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
```

This field description is sent to the LLM as part of the JSON schema. When the LLM produces non-English output (as OPTIMIZE_INSTRUCTIONS lines 61–68 explicitly documents may happen), this instruction is meaningless noise. More critically, per OPTIMIZE_INSTRUCTIONS lines 82–83, naming banned phrases in a prohibition can prime small models to use those phrases.

---

## Improvement Opportunities

### I1 — Replace UUID prohibition with a positive-example instruction
**File:** `enrich_potential_levers.py:178`

Instead of "Do NOT include any Lever ID, UUID, or identifier string in these fields," use positive framing with a concrete example:

> "In `synergy_text` and `conflict_text`, always refer to other levers by name — for example, write 'Policy Advocacy Strategy' not any identifier or UUID string."

This gives the model a correct-behavior template rather than naming the forbidden pattern, consistent with OPTIMIZE_INSTRUCTIONS guidance on negative-instruction priming (identify_potential_levers.py lines 82–83). If the sovereign_identity regression is confirmed to be caused by the negative framing, this change would be the minimal targeted fix.

---

### I2 — Add post-process regex strip for UUID patterns in synergy/conflict text
**File:** `enrich_potential_levers.py:277–283`

After updating `enriched_levers_map` with LLM output, apply a regex strip:

```python
import re
_UUID_RE = re.compile(
    r'(?:\(?\s*(?:lever\s+id\s*:\s*)?'
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'\s*\)?)',
    re.IGNORECASE
)
```

Applied to `synergy_text` and `conflict_text` before final assembly. This is a defensive, model-agnostic fix (C1 from insight) that works regardless of whether the prompt instruction succeeds. It also removes the `(lever ID: xxx)` patterns that llama3.1 embeds. Risk: could strip content adjacent to a UUID, but synergy/conflict text should only contain lever names, not raw UUIDs.

---

### I3 — Pre-filter haiku's extra characterizations before the lever-ID lookup
**File:** `enrich_potential_levers.py:277`

Before the `for char in batch_result.characterizations:` loop, add:

```python
expected_ids = {lever.lever_id for lever in batch}
valid_chars = [c for c in batch_result.characterizations if c.lever_id in expected_ids]
extra_count = len(batch_result.characterizations) - len(valid_chars)
if extra_count > 0:
    logger.debug(f"Discarding {extra_count} extra characterization(s) with unknown lever_id(s)")
```

Then iterate over `valid_chars` instead of `batch_result.characterizations`. This eliminates `unknown_lever_id` error entries for over-generated extras (H1 from insight) without generating spurious error log noise. The insight confirms real levers appear before fabricated extras in haiku's output, so valid_chars retains all correct items.

---

### I4 — Update `OPTIMIZE_INSTRUCTIONS` with negative-priming lesson from PR #458
**File:** `enrich_potential_levers.py:88–99`

The current OPTIMIZE_INSTRUCTIONS entry for UUID leakage (lines 88–94) documents that a prohibition was added by "PR #457+1" and suggests "consider a post-process regex strip as a defensive fallback." It should be updated to:

1. Record that the prompt prohibition (PR #458) introduced a regression in sovereign_identity.
2. Explicitly note that negative "Do NOT include" instructions that name the forbidden format are counterproductive for llama3.1.
3. Mark the post-process regex strip (I2) as the preferred path forward.
4. Document that the exact-count user-prompt instruction (PR #458) reduced haiku errors 71% (7→2) and is worth keeping.

This keeps the OPTIMIZE_INSTRUCTIONS current and prevents re-attempting the same negative-instruction approach in future iterations.

---

### I5 — `LeverCharacterization.lever_id` field description should emphasize verbatim copy
**File:** `enrich_potential_levers.py:141`

```python
lever_id: str = Field(description="The uuid of the lever")
```

The description is minimal. Strengthening it to "The exact lever_id UUID from the 'Lever ID:' field in the input — copy it verbatim, do not invent or modify" would reduce haiku's fabrication of IDs for extra characterizations and would reinforce the correct copy-through behavior.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| **N1** — sovereign_identity regressed 0 → 20 UUIDs after PR #458 | B1: negative prohibition names "Lever ID" format llama3.1 uses; primes the pattern for plans that were previously clean |
| **N2** — llama3.1 net UUID count unchanged (29 → 29) | B1: prohibition partially helps gta_game but introduces sovereign_identity regression; net zero improvement; I2 (post-process strip) is the correct fix |
| **N3** — haiku extra-characterization persists (7 → 2) | B2: no code-level trim before lever-ID lookup; the prompt instruction reduces but does not eliminate extras; I3 (pre-filter) eliminates residual |
| **N4** — negative instruction priming hypothesis confirmed | B1: OPTIMIZE_INSTRUCTIONS in identify_potential_levers.py lines 82–83 documents this exact risk, but the warning was not applied when writing the enrich prompt prohibition |
| **P1** — haiku errors reduced 71% (7 → 2) | The "Return exactly N" user-prompt instruction (PR #458 line 257) is the correct positive-constraint approach; it works as expected |
| **P4** — other models unaffected | System prompt additions are benign for compliant models; only llama3.1 shows negative-instruction priming behavior |

---

## PR Review

### What PR #458 changes

**Change 1 — System prompt addition (line 178):**
```
**Important:** In `synergy_text` and `conflict_text`, refer to other levers by NAME only.
Do NOT include any Lever ID, UUID, or identifier string in these fields.
```
Targets llama3.1 copying `Lever ID:` UUIDs from `lever_details_for_prompt` into synergy/conflict text.

**Change 2 — User prompt addition (line 257):**
```python
f"Return exactly {len(batch)} characterizations — one per lever, no more, no fewer. "
```
Targets haiku's extra `LeverCharacterization` objects with fabricated IDs.

**Change 3 — OPTIMIZE_INSTRUCTIONS update (lines 88–99):**
Documents both residual problems and the PR's attempted fixes.

---

### Does the implementation match the intent?

**Change 2 (exact-count user prompt): YES, partially effective.**
The "Return exactly N" instruction reduces haiku errors from 7 to 2 (–71%). For gta_game and parasomnia the fix is complete; hong_kong and silo have 1 residual error each. The instruction targets the mechanism (haiku inferring wrong total count) and partially corrects it. This change is worth keeping.

**Change 1 (UUID prohibition in system prompt): NO — ineffective and introduces regression.**
The prohibition instruction names "Lever ID" — the exact format llama3.1 uses in synergy/conflict output. Per `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS lines 82–83, naming the forbidden phrase in a "Do NOT" rule is counterproductive: small models treat the prohibition text as a template. This explains the sovereign_identity regression: a plan that was clean without any instruction now has 20 UUIDs in synergy/conflict text after the prohibition was added. Net UUID count in text fields is unchanged (29 → 29). The prohibition approach should be replaced.

**Change 3 (OPTIMIZE_INSTRUCTIONS update): YES, accurate.**
The updated OPTIMIZE_INSTRUCTIONS correctly documents the post-PR #457 state: per-batch UUID leakage from `lever_details_for_prompt` and haiku's extra-characterization behavior. This is good maintenance.

---

### Edge cases the PR misses

1. **Positive-framing alternative for UUID fix**: The PR uses negative prohibition ("Do NOT include UUID") rather than positive framing ("refer by NAME only, e.g. 'Policy Advocacy Strategy'"). The positive variant gives a correct-behavior template instead of naming the forbidden pattern, which is the recommended approach per OPTIMIZE_INSTRUCTIONS in `identify_potential_levers.py`.

2. **Code-level UUID strip not added**: The only defense is the prompt instruction. A regex post-process strip (I2) as a second layer was not added. Given that the prompt instruction failed and regressed for llama3.1, the code-level fix was the appropriate backup and should be the primary fix.

3. **No pre-filter for haiku extras**: The "Return exactly N" instruction reduces but doesn't eliminate haiku over-generation. The code at lines 277–286 still logs `unknown_lever_id` errors for extras. A pre-filter (I3) before the lever-ID lookup would cleanly discard extras without generating error noise.

4. **Duplication of count constraint between system and user prompts**: The system prompt already contained "Return exactly one characterization per lever requested — no more, no fewer" before PR #458. Adding the exact-count to the user prompt creates redundancy, but the insight shows this helps (the user prompt's specific N is more actionable than the system prompt's general statement). Not a bug, but worth noting.

---

### Verdict

**Change 1 (UUID prohibition): REVERT or REPLACE.** The negative instruction is counterproductive for llama3.1 and introduces a regression. Replace with: (a) positive-framing instruction (I1) as the prompt fix, and (b) post-process regex strip (I2) as the code-level fix. The regex strip alone would achieve zero UUID contamination regardless of model behavior.

**Change 2 (exact-count user prompt): KEEP.** Genuine improvement for haiku (–71%). Supplement with the pre-filter trim (I3) to eliminate remaining errors at the code level.

**Change 3 (OPTIMIZE_INSTRUCTIONS update): KEEP.** Add the negative-priming lesson from this regression (I4).

---

## Summary

PR #458 uses two strategies: a negative prohibition for the UUID problem (backfired) and a positive count constraint for the haiku over-generation problem (worked).

**Confirmed bugs:**
- **B1** (high impact, introduced by PR #458): Negative instruction `"Do NOT include any Lever ID, UUID"` names llama3.1's exact output pattern, priming it to produce UUIDs in plans that were previously clean. sovereign_identity regressed 0 → 20 UUID occurrences. Net UUID improvement: zero.
- **B2** (medium impact, partial fix by PR #458): No code-level trim for haiku's extra characterizations; the prompt instruction reduces errors 71% (7→2) but 2 residual errors remain. A `characterizations[:len(batch)]` pre-filter would eliminate them.
- **B3** (low impact, pre-existing): False `partial_recovery` events for successful 2-call runs; threshold `< 3` fires for normal fast-converging models.
- **B4** (low impact, pre-existing): `errors: List[Dict[str, Any]] = None` type annotation mismatch.

**Key improvements:**
- **I1**: Replace "Do NOT include UUID" prohibition with positive framing + concrete example name.
- **I2**: Add regex post-process strip of UUID patterns from `synergy_text`/`conflict_text` (defensive, model-agnostic).
- **I3**: Pre-filter `batch_result.characterizations` to `[:len(batch)]` before the lever-ID lookup loop.
- **I4**: Update OPTIMIZE_INSTRUCTIONS with the negative-priming lesson from this PR's regression.

**PR #458 overall: CONDITIONAL.** The haiku fix (Change 2) is genuine and should be kept. The llama3.1 UUID fix (Change 1) failed and introduced a regression; it should be replaced with a code-level strip (I2) and, optionally, positive-framing instruction (I1).
