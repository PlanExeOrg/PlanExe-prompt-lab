# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`

PR under review: #468 ("Reduce word counts, add anti-echoing, and guide lever_id extraction")

---

## Bugs Found

### B1 — `lever_id` field description triggers UUID hyphen-stripping in gpt-4o-mini
**File:** `enrich_potential_levers.py:138`

```python
lever_id: str = Field(description="The hexadecimal uuid of the lever, without XML tags")
```

The phrase "hexadecimal uuid" is ambiguous. gpt-4o-mini interprets "hexadecimal" as implying a raw hex string (no hyphens), stripping all hyphens from the UUID before returning it. The field description was added by PR #468 to fix llama3.1's XML-tag inclusion, but its wording introduces a new formatting ambiguity for models that parse field descriptions closely.

Every `unknown_lever_id` error in run 80 maps exactly to the same UUID with hyphens removed:
```
returned:   bd43cd39f2f043589f5be4dbfdccc474   (hex-only — fails lookup)
actual key: bd43cd39-f2f0-4358-9f5b-e4dbfdccc474 (standard UUID — in map)
```

Fix: use an explicit example of the standard format:
```python
lever_id: str = Field(description="The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags")
```

---

### B2 — `enriched_levers_map` lookup uses exact string matching with no UUID normalization
**File:** `enrich_potential_levers.py:277`

```python
if char.lever_id in enriched_levers_map:
```

The map is keyed by the original UUIDs assigned by `identify_potential_levers.py` (with hyphens). Any model that returns the UUID in a different format (hyphens stripped, uppercase, extra whitespace) silently misses the lookup. The lever is then recorded as an `unknown_lever_id` error and its entry in the map is never enriched, so it also appears as `incomplete` at line 329.

This exact-match design makes the pipeline brittle to model formatting variation. A normalized comparison that strips hyphens from both sides before matching would have caught gpt-4o-mini's output in run 80 with zero prompt changes.

Proposed defensive fix at lines 276–285:
```python
# Normalize UUIDs: strip hyphens for comparison only
normalized_map = {k.replace('-', ''): k for k in enriched_levers_map}
normalized_id = char.lever_id.replace('-', '').strip()
canonical_id = normalized_map.get(normalized_id)
if canonical_id:
    enriched_levers_map[canonical_id].update({...})
else:
    logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
```

---

## Suspect Patterns

### S1 — `consequences` field description names banned phrases, contradicting OPTIMIZE_INSTRUCTIONS
**File:** `identify_potential_levers.py:116–119`

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field — "
"those belong exclusively in review_lever. "
```

`OPTIMIZE_INSTRUCTIONS` lines 81–82 explicitly warn:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."

Yet the `consequences` field description names `'Controls ... vs.'` and `'Weakness:'` as examples of what to avoid. For small or weaker models, this functions as a template suggesting those exact phrases should appear somewhere. The same text is duplicated verbatim in `LeverCleaned.consequences` (lines 210–215), which is never sent to the LLM but is a maintenance hazard.

---

### S2 — System prompt also uses "hexadecimal uuid string"
**File:** `enrich_potential_levers.py:170`

```python
"When returning `lever_id`, extract and return only the hexadecimal uuid string inside the tags — strip the XML tags themselves."
```

The phrase "hexadecimal uuid string" appears in the system prompt as well as the Pydantic field description (B1). The system prompt phrasing is less directly causative than the field description (structured-output models weight field descriptions heavily for output formatting), but it may reinforce the hyphen-stripping behavior in models that read both. Changing "hexadecimal uuid string" to "standard UUID string" or "UUID (with hyphens)" here reduces ambiguity further.

---

### S3 — `partial_recovery` warning threshold fires for normal 2-call completions
**File:** `runner.py:129–133`

```python
# A 2-call success is normal for models that produce 8+ levers per call.
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```

The comment explicitly acknowledges that `actual_calls == 2` is normal yet the `< 3` threshold emits a warning for it. Models that over-generate (8+ levers per call) will complete in 2 calls — which is early-stop success, not partial recovery. The warning conflates "fewer calls than the typical case" with "recovery from failure." This produces misleading telemetry in `events.jsonl`, flagging healthy runs as partial recoveries. Threshold should be `< 2` (only warn on 1 successful call, which is the true partial-recovery case).

---

## Improvement Opportunities

### I1 — Revise `lever_id` field description to unambiguously preserve hyphens
**File:** `enrich_potential_levers.py:138`

Change:
```python
lever_id: str = Field(description="The hexadecimal uuid of the lever, without XML tags")
```
To:
```python
lever_id: str = Field(description="The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags")
```

Predicted effect: eliminates gpt-4o-mini hyphen-stripping (13 unknown_lever_id + 13 incomplete errors → 0). The explicit format example leaves no room for ambiguity about hyphens.

---

### I2 — Add defensive UUID normalization in `execute()` (independent of prompt wording)
**File:** `enrich_potential_levers.py:276–285`

Even after fixing B1, future models may return UUIDs in non-standard formats. A one-time normalization pass (strip hyphens from both key and query before comparison) makes the lookup robust against any future formatting variation from new models, without requiring additional prompt tuning. See B2 above for the proposed code.

---

### I3 — Revise "hexadecimal uuid string" phrasing in system prompt
**File:** `enrich_potential_levers.py:170`

Change "hexadecimal uuid string" to "standard UUID string (e.g. xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)" so that both the Pydantic field description and the system prompt give consistent, unambiguous guidance.

---

### I4 — Add UUID format fragility entry to `OPTIMIZE_INSTRUCTIONS`
**File:** `enrich_potential_levers.py:28–107`

The insight analysis (OPTIMIZE_INSTRUCTIONS Alignment section) recommends a new entry:

```
- UUID lever_id format fragility. When field descriptions contain "hexadecimal uuid",
  some models (e.g. gpt-4o-mini) interpret this as a raw hex string and strip hyphens.
  The standard UUID format is xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (8-4-4-4-12 with
  hyphens). Field descriptions must reference the standard format explicitly or provide
  an example. A normalization fix in execute() — comparing stripped UUIDs for map
  lookup — makes the pipeline robust to this variation independent of prompt wording.
```

---

### I5 — Remove English prohibition phrases from `consequences` field description
**File:** `identify_potential_levers.py:116–119`

Remove the literal phrase citations (`'Controls ... vs.'`, `'Weakness:'`) from the field description. Replace with structural guidance:

```python
"Do NOT include critique, trade-off analysis, or review commentary in this field — "
"save those for the review_lever field. "
```

This preserves the intent while complying with OPTIMIZE_INSTRUCTIONS' rule against naming banned phrases.

---

### I6 — Fix `partial_recovery` warning threshold in runner
**File:** `runner.py:131`

Change:
```python
if actual_calls < 3:
```
To:
```python
if actual_calls < 2:
```

This limits the warning to the true partial-recovery case (only 1 successful call out of a max of 5), matching the intent described in the comment.

---

## Trace to Insight Findings

| Code issue | Insight observation |
|------------|---------------------|
| B1 (`lever_id` field description "hexadecimal uuid") | N1: gpt-4o-mini returns hex-only UUIDs → 13 `unknown_lever_id` + 13 `incomplete` errors in run 80 |
| B2 (exact-match enriched_levers_map lookup) | N1: confirms that hex-only IDs silently fail — the `unknown_lever_id` + `incomplete` error pair is the direct observable consequence |
| S2 (system prompt "hexadecimal uuid string") | N1: system prompt may amplify the same confusion B1 causes, though the field description is the proximate cause |
| B1 + B2 together | Comparison table: lever enrichments drop from 240/245 to 232/245 (−8 net), driven entirely by gpt-4o-mini −13 |
| S1 (banned phrases named in field description) | Not directly observed in runs 76–82, but is a latent risk for small models on non-English prompts per OPTIMIZE_INSTRUCTIONS |
| S3 (misleading partial_recovery threshold) | Not relevant to runs 76–82 (enrich step), but applies to identify step runner telemetry |

---

## PR Review

### What PR #468 changes

1. **Word count reduction** — description 80-100 → 50-70 words, synergy/conflict 40-60 → 20-40 words (`enrich_potential_levers.py:139–147`).
2. **Anti-echoing instruction** — added to description field description: "Add new insight beyond what consequences and review already state" (`enrich_potential_levers.py:141`).
3. **`lever_id` Pydantic field description** — `"The hexadecimal uuid of the lever, without XML tags"` (`enrich_potential_levers.py:138`).
4. **System prompt XML guidance** — explains that lever IDs are wrapped in `<lever>uuid</lever>` tags and instructs extracting only the UUID (`enrich_potential_levers.py:170–171`).

### Does the implementation match the intent?

**Changes 1 and 2:** Yes. Word count reductions are reflected in the Pydantic field descriptions and work as intended. All 7 models show synergy/conflict reductions of 20–44%. No regressions.

**Change 4 (system prompt XML guidance):** Yes, for the target model (llama3.1). The instruction clearly says to strip the XML tags. Run 76 confirms llama3.1 returns 0 errors vs. 10 in the PR #467 run.

**Change 3 (lever_id field description):** Partially. The intent was to prevent llama3.1 from returning the XML wrapper as the lever_id. The system prompt (change 4) achieves that correctly. The field description (change 3) adds redundant guidance but introduces the ambiguity that causes B1: "hexadecimal uuid" has a legitimate hex-only interpretation for models that parse "hexadecimal" as implying the raw encoding. gpt-4o-mini exploits this ambiguity and strips hyphens. The implementation does fix llama3.1 (partially because the system prompt does most of the work) but introduces a new defect for gpt-4o-mini.

### Edge cases the PR misses

1. **Hyphen-stripped UUID normalization in code** — The PR only adds prompt guidance to discourage bad formatting. It does not add defensive normalization in `execute()` to handle models that return non-standard UUID formats despite guidance. A code-level fix (B2/I2) would make the pipeline format-agnostic.

2. **"hexadecimal" in system prompt** — Change 4 uses "hexadecimal uuid string" (line 170), repeating the same ambiguous word choice used in the field description. If the field description is fixed (I1), the system prompt should also be updated (I3) for consistency.

3. **Other UUID format variations** — The PR addresses XML-tag inclusion and hyphens but not uppercase, extra whitespace, or partial UUIDs. The normalization approach in I2 handles all of these simultaneously.

### Verdict on the PR

The PR correctly fixes its primary target (llama3.1 XML-tag issue) and its secondary target (gpt-oss-20b timeout). Changes 1, 2, and 4 are sound. Change 3 introduces B1: the field description wording is imprecise in a way that degrades a different model. The fix for B1 is a one-line change. Combining B1's fix with B2's defensive normalization would make the pipeline robust to UUID format variation from any model regardless of future prompt changes.

---

## Summary

Two confirmed bugs, both in `enrich_potential_levers.py`, both introduced or exposed by PR #468:

- **B1** (`enrich_potential_levers.py:138`): The `lever_id` field description `"hexadecimal uuid"` causes gpt-4o-mini to return UUIDs without hyphens. This is the root cause of 13 `unknown_lever_id` + 13 `incomplete` errors in run 80 (4 of 5 plans affected, 13/35 levers unenriched).

- **B2** (`enrich_potential_levers.py:277`): The `enriched_levers_map` lookup is exact-match with no UUID format normalization. Any model-returned UUID that differs in format (hyphens, case, whitespace) silently misses the lookup. This is not new to PR #468 but is what converts B1's output into silent data loss.

The minimum fix for the regression is I1 (one-line field description change). The more robust fix is I1 + I2 (normalized lookup), which would prevent this class of regression from any future model.

One misalignment with OPTIMIZE_INSTRUCTIONS worth noting: S1 (`identify_potential_levers.py:116–119`) names banned English phrases in the `consequences` field description, directly contradicting the documented guideline against it.
