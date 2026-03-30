# Synthesis

## Cross-Agent Agreement

Only one analysis pair (insight_claude + code_claude) is present for this run. Both files
converge strongly on the following:

1. **UUID prohibition (PR #458 Change 1) is counterproductive for llama3.1.** The "Do NOT
   include any Lever ID, UUID, or identifier string" instruction names the exact format
   llama3.1 uses (`lever ID: xxx`) and appears to prime the model to produce it in plans
   that were previously clean. sovereign_identity regressed from 0 to 20 UUID occurrences.
   Net UUID count in text fields: unchanged (29 → 29). Both files identify this as the
   primary problem (N1/N2/N4 in insight; B1 in code review).

2. **The haiku exact-count instruction (Change 2) is a genuine improvement.** Errors
   dropped 71% (7 → 2). Both files agree this change should be kept and supplemented with
   a code-level pre-filter (I3/H1) to eliminate the 2 residual errors.

3. **Post-process regex strip (C1/I2) is the correct fix for llama3.1 UUID contamination.**
   It is model-agnostic, works regardless of prompt compliance, and removes the need for
   a brittle do-not instruction.

4. **OPTIMIZE_INSTRUCTIONS should be updated** to document the negative-priming lesson
   from this regression so future iterations do not repeat the same mistake (I4/P3).

5. **All other models (5/7) are unaffected** — no regressions, no new errors. The PR
   is neutral for gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, and gemini.

---

## Cross-Agent Disagreements

No inter-agent disagreement (single reviewer). One area required source-code verification:

**Claim (code review B1):** The OPTIMIZE_INSTRUCTIONS warning in `identify_potential_levers.py`
lines 81-82 explicitly prohibits negative do-not instructions naming banned phrases.
**Verified:** `identify_potential_levers.py:80-82` reads:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat the
> prohibition text as a template and copy the banned phrases."

This warning exists in the *identify* file but was not applied when writing the UUID
prohibition in the *enrich* system prompt. The code review's root-cause analysis is correct.

**Claim (code review B3):** `runner.py` fires `partial_recovery` for `calls_succeeded < 3`,
which includes normal 2-call runs.
**Verified:** `runner.py:131-133` and `runner.py:577-583` confirm the threshold is `< 3`,
and the comment at lines 127-130 explicitly states "A 2-call success is normal for models
that produce 8+ levers per call." The false-positive is confirmed.

**Claim (code review B4):** `errors: List[Dict[str, Any]] = None` type mismatch.
**Verified:** `enrich_potential_levers.py:189` confirms `errors: List[Dict[str, Any]] = None`.

**Claim (insight/code):** haiku's extra characterizations are discarded extras appended
after real levers, so trimming to `[:len(batch)]` is safe.
**Verified:** `enrich_potential_levers.py:277-286` confirms the loop logs `unknown_lever_id`
for any char whose `lever_id` is not in `enriched_levers_map`. The real levers appear
first (they match real IDs); fabricated extras fall through. Trimming is safe.

---

## Top 5 Directions

### 1. Replace UUID prohibition with a post-process regex strip + positive framing
- **Type**: code fix + prompt change
- **Evidence**: insight N1/N2/N4, code review B1/I1/I2. Confirmed by source: prohibition
  added at `enrich_potential_levers.py:178`; OPTIMIZE_INSTRUCTIONS warning at
  `identify_potential_levers.py:80-82` directly predicts this failure mode.
- **Impact**: Eliminates llama3.1 sovereign_identity regression (+20 UUIDs introduced by
  PR #458). Provides model-agnostic defensive strip for all future runs. Reduces net
  llama3.1 synergy/conflict UUID count from ~20 (after regression) toward 0.
  Affects 1 of 7 models, but the regression is active and ongoing.
- **Effort**: Low-medium. Two changes:
  1. Replace negative prohibition at `enrich_potential_levers.py:178` with positive
     framing: `"In synergy_text and conflict_text, always refer to other levers by NAME
     only — for example, write 'Policy Advocacy Strategy' not any identifier or UUID."`
  2. Add regex post-process strip after `enriched_levers_map.update(...)` at lines
     279-283 to remove `(lever ID: <uuid>)` patterns from `synergy_text`/`conflict_text`.
- **Risk**: Regex strip could clip content adjacent to a UUID, but synergy/conflict fields
  should only contain lever names — not raw UUIDs. The positive framing may still not
  fully suppress llama3.1 (which is why the regex strip is the primary fix, not just the
  prompt change).

### 2. Add pre-filter trim for haiku over-generation before the lever-ID lookup
- **Type**: code fix
- **Evidence**: insight N3/H1, code review B2/I3. Confirmed at
  `enrich_potential_levers.py:277-286` — no guard exists before the loop.
- **Impact**: Eliminates all remaining `unknown_lever_id` errors from haiku's extra
  characterizations (2 residual after PR #458). Zero noise in `errors` for this class.
  Affects haiku only; all real levers are already enriched correctly.
- **Effort**: Low. Add before line 277:
  ```python
  expected_ids = {lever.lever_id for lever in batch}
  valid_chars = [c for c in batch_result.characterizations if c.lever_id in expected_ids]
  if len(valid_chars) < len(batch_result.characterizations):
      logger.debug(f"Discarding {len(batch_result.characterizations) - len(valid_chars)} extra characterization(s)")
  ```
  Then iterate `valid_chars` instead of `batch_result.characterizations`.
- **Risk**: Minimal. If haiku returns fewer characterizations than expected (a different
  failure mode), the pre-filter does not mask the gap — those levers simply remain
  unenriched. No false silencing.

### 3. Update OPTIMIZE_INSTRUCTIONS in enrich_potential_levers.py with the negative-priming regression
- **Type**: prompt change (context improvement)
- **Evidence**: code review I4, insight reflect section. Current entry at lines 88-94
  says "consider a post-process regex strip as a defensive fallback" — it doesn't yet
  record that the prohibition caused a regression.
- **Impact**: Prevents future optimization iterations from re-trying the same negative
  prohibition approach. High leverage on the self-improve loop's future behavior.
  Affects all future PRs touching this file.
- **Effort**: Low. Update lines 88-99 to:
  1. Record that prompt prohibition introduced a regression (sovereign_identity 0 → 20).
  2. State that negative "Do NOT include UUID" instructions are counterproductive for
     llama3.1 (consistent with `identify_potential_levers.py` lines 80-82).
  3. Designate the post-process regex strip as the preferred fix.
  4. Note the exact-count user-prompt instruction (PR #458) reduced haiku errors 71%
     and is worth keeping.
- **Risk**: None. Documentation-only change.

### 4. Fix false-positive partial_recovery events in runner.py
- **Type**: code fix (pre-existing, unrelated to PR #458)
- **Evidence**: code review B3. Confirmed at `runner.py:131-133` and `runner.py:577-583`.
  Comment at lines 127-130 explicitly acknowledges 2-call success is normal.
- **Impact**: Removes misleading `partial_recovery` noise from `events.jsonl` for all
  models that converge in 2 calls on the `identify_potential_levers` step. Affects event
  analysis and any downstream tooling that reads `events.jsonl`.
- **Effort**: Low. Change threshold from `< 3` to `< 2` at both `runner.py:131` and
  `runner.py:579`. A `partial_recovery` event should only fire when exactly 1 call
  succeeded (meaning the adaptive loop barely recovered).
- **Risk**: Low. Only affects event emission, not actual plan processing or output.

### 5. Strengthen LeverCharacterization.lever_id field description
- **Type**: prompt change
- **Evidence**: code review I5. Current description at `enrich_potential_levers.py:141`:
  `lever_id: str = Field(description="The uuid of the lever")` — minimal, no copy
  instruction.
- **Impact**: May reduce haiku's fabrication of lever IDs for extra characterizations by
  emphasizing verbatim copy semantics. Would complement the pre-filter (Direction 2) as
  a defense-in-depth measure. Lower expected impact than Directions 1-4 since the
  pre-filter handles the symptom regardless.
- **Effort**: Low. Change to:
  `lever_id: str = Field(description="The exact lever_id UUID from the 'Lever ID:' field in the input — copy it verbatim, do not invent or modify.")`
- **Risk**: Minimal. Field description changes are prompt changes; test with a self_improve
  iteration. The phrase "copy it verbatim" gives a concrete behavioral instruction.

---

## Recommendation

**Pursue Direction 1 first: replace the UUID prohibition with a post-process regex strip
and positive framing.**

**Why first:** PR #458 Change 1 introduced an active regression. sovereign_identity went
from 0 UUID occurrences (clean) to 20 UUID occurrences (broken) in llama3.1's synergy and
conflict text — a direct result of the negative prohibition naming the exact pattern
llama3.1 uses. This regression is ongoing in the current codebase. The fix must undo the
regression before any other UUID work proceeds.

The post-process strip is the primary fix because it is model-agnostic and prompt-independent:
it removes UUID patterns after enrichment regardless of what the LLM produces. The prompt
change (positive framing) is secondary but removes the priming risk for future runs.

**What to change:**

**File:** `enrich_potential_levers.py`

**Change A — System prompt, line 178.** Replace:
```
**Important:** In `synergy_text` and `conflict_text`, refer to other levers by NAME only. Do NOT include any Lever ID, UUID, or identifier string in these fields.
```
With:
```
**Important:** In `synergy_text` and `conflict_text`, always refer to other levers by NAME only — for example, write "Policy Advocacy Strategy" not any identifier or UUID string.
```

**Change B — Post-process strip, after line 283** (inside the `if char.lever_id in enriched_levers_map:` block, after `.update(...)`). Add:
```python
import re
_UUID_RE = re.compile(
    r'\(?\s*(?:lever\s+id\s*:\s*)?'
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'\s*\)?',
    re.IGNORECASE
)
for field in ('synergy_text', 'conflict_text'):
    enriched_levers_map[char.lever_id][field] = _UUID_RE.sub('', enriched_levers_map[char.lever_id][field]).strip()
```

(Move the `_UUID_RE` compile to module level, not inside the loop.)

**Expected result:** llama3.1 sovereign_identity returns to 0 UUID occurrences in
synergy/conflict text; gta_game maintains its improvement; net UUID count drops to near
0 for synergy/conflict fields across all models.

**OPTIMIZE_INSTRUCTIONS update** (Change B complement): update lines 88-99 to record that
the prohibition introduced a regression and that the regex strip is the canonical fix.

---

## Deferred Items

- **Direction 2 (haiku pre-filter, I3):** High value, low risk, minimal effort. Should
  immediately follow Direction 1 in the next iteration. The 2 residual haiku errors are
  noise, not plan failures, but eliminating them keeps the error log clean.

- **Direction 4 (runner.py partial_recovery threshold):** Pre-existing bug, not introduced
  by PR #458. Fix in a separate cleanup PR to keep scope clear.

- **Direction 5 (lever_id field description, I5):** Speculative improvement. Worth adding
  alongside Direction 2 if the extra characterization issue persists after the pre-filter.

- **S3 (English-only negative prohibition in `Lever.consequences`):** The field description
  in `identify_potential_levers.py:118` contains "Do NOT include 'Controls ... vs.'..." —
  the same priming risk documented in OPTIMIZE_INSTRUCTIONS lines 80-82. This is in a
  different file from the current work but should be addressed when optimizing that step.

- **S2 (`__main__` test block broken JSON shape):** Developer tooling issue in
  `enrich_potential_levers.py:374-376`. Low priority but confusing for local testing.

- **B4 (`errors` type annotation mismatch):** `Optional[List[Dict[str, Any]]] = None`
  is a trivial static-typing fix. Can be bundled with any future cleanup PR.
