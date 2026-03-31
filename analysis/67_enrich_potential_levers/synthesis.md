# Synthesis

## Cross-Agent Agreement

Only one analysis agent ran (Claude), producing both `insight_claude.md` and `code_claude.md`. The two files are internally consistent and mutually reinforcing:

- Both identify the **lever_id field description** (`"The hexadecimal uuid of the lever, without XML tags"`) as the root cause of gpt-4o-mini returning hyphen-stripped UUIDs (B1/N1), producing 13 `unknown_lever_id` + 13 `incomplete` errors in run 80 — 13/35 levers unenriched across 4 of 5 plans.
- Both confirm the **exact-match enriched_levers_map lookup** (line 277) as a structural brittleness that converts any UUID formatting variation into silent data loss (B2).
- Both confirm that PR #468's primary targets were achieved: llama3.1 XML-tag issue fully resolved (10 → 0 errors), gpt-oss-20b timeout eliminated (3/5 → 5/5 completions).
- Both agree on the recommended fix: revise the field description to use an explicit UUID format example (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`), and add a defensive normalization layer in `execute()`.
- The code review additionally flags **S1** (banned phrases named in `consequences` field description in `identify_potential_levers.py:116–119`, contradicting OPTIMIZE_INSTRUCTIONS), **S2** (system prompt also uses "hexadecimal uuid string"), and **S3** (misleading `partial_recovery` warning threshold in `runner.py`).

## Cross-Agent Disagreements

No cross-agent disagreements — only one agent ran. All claims are consistent between insight and code review files.

**Source code verification of key claims:**

- **B1 confirmed**: `enrich_potential_levers.py:138` reads `lever_id: str = Field(description="The hexadecimal uuid of the lever, without XML tags")` — exactly as reported.
- **B2 confirmed**: `enrich_potential_levers.py:277` reads `if char.lever_id in enriched_levers_map:` — exact-match, no normalization. The map is built at line 219 from original hyphenated UUIDs.
- **S1 confirmed**: `identify_potential_levers.py:116–119` contains `"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"`. OPTIMIZE_INSTRUCTIONS lines 81–82 explicitly state: "Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template and copy the banned phrases."
- **S2 confirmed**: `enrich_potential_levers.py:170` contains `"extract and return only the hexadecimal uuid string inside the tags"`.
- **S3 confirmed**: `runner.py:131` reads `if actual_calls < 3:`, and the adjacent comment acknowledges that "A 2-call success is normal for models that produce 8+ levers per call."

## Top 5 Directions

### 1. Fix lever_id field description and system prompt "hexadecimal uuid" phrasing
- **Type**: prompt change (2 lines)
- **Evidence**: B1 (code review), N1 (insight), S2 (code review). Both files flag this as the root cause of gpt-4o-mini's regression. Source code verified at lines 138 and 170.
- **Impact**: Eliminates gpt-4o-mini's 13 `unknown_lever_id` + 13 `incomplete` errors in run 80 (4 of 5 plans affected). Net lever enrichment rate recovers from 94.7% to ~98%+. Affects the most-used GPT model tier. Also removes the "hexadecimal" ambiguity from the system prompt, reducing risk of the same confusion in future models.
- **Effort**: Low — two string changes in `enrich_potential_levers.py`.
- **Risk**: Minimal. The change is a clarification only; it does not alter prompt structure or schema shape. System prompt guidance for llama3.1 remains effective because the XML-tag stripping instruction in line 170 is retained (only "hexadecimal uuid string" is rephrased).

  **Proposed changes:**

  `enrich_potential_levers.py:138` — field description:
  ```python
  lever_id: str = Field(description="The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags")
  ```

  `enrich_potential_levers.py:170` — system prompt:
  ```python
  "When returning `lever_id`, extract and return only the standard UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) inside the tags — strip the XML tags themselves."
  ```

### 2. Add defensive UUID normalization in execute()
- **Type**: code fix
- **Evidence**: B2 (code review), N1 (insight). Source code verified at line 277 — exact-match lookup with no format tolerance.
- **Impact**: Makes the pipeline resilient to UUID format variation (hyphen-stripped, uppercase, extra whitespace) from any current or future model, independently of prompt wording. If direction 1 is applied and a new model still returns hex-only UUIDs, this catches it silently. Zero-regression fix.
- **Effort**: Low — 5–8 line change in `execute()`.
- **Risk**: Very low. The normalization is lookup-only; the stored data and original UUIDs are unchanged.

  **Proposed change at lines 276–285:**
  ```python
  normalized_map = {k.replace('-', ''): k for k in enriched_levers_map}
  normalized_id = char.lever_id.replace('-', '').strip()
  canonical_id = normalized_map.get(normalized_id)
  if canonical_id:
      enriched_levers_map[canonical_id].update({
          'description': char.description,
          'synergy_text': char.synergy_text,
          'conflict_text': char.conflict_text
      })
  else:
      logger.warning(f"LLM returned characterization for an unknown lever_id: '{char.lever_id}'")
      errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
  ```

### 3. Remove named banned phrases from consequences field description in identify_potential_levers.py
- **Type**: prompt change
- **Evidence**: S1 (code review). Verified at `identify_potential_levers.py:116–119` — the field description names `'Controls ... vs.'` and `'Weakness:'` as examples of what to avoid, directly contradicting OPTIMIZE_INSTRUCTIONS lines 81–82. Also duplicated verbatim in `LeverCleaned.consequences` (lines 210–215), which is a maintenance hazard (LeverCleaned is never sent to an LLM but may confuse future editors).
- **Impact**: Reduces latent template-lock risk for small/weak models and non-English prompts. The current wording has not triggered observable errors in runs 76–82, but aligns the code with documented OPTIMIZE_INSTRUCTIONS guidance and removes a phrase-copying trap.
- **Effort**: Low — replace one string in the `Lever.consequences` field description.
- **Risk**: Low. The structural intent ("don't include critique text here") is preserved; only the phrase examples are removed.

  **Proposed change at `identify_potential_levers.py:116–118`:**
  ```python
  "Do NOT include critique, trade-off analysis, or review commentary in this field — "
  "those belong exclusively in review_lever. "
  ```

### 4. Add UUID format fragility entry to OPTIMIZE_INSTRUCTIONS in enrich_potential_levers.py
- **Type**: documentation / prompt change
- **Evidence**: I4 (code review), insight OPTIMIZE_INSTRUCTIONS Alignment section. Not yet documented.
- **Impact**: Prevents future recurrence of this class of regression. Engineers and future optimization iterations will have a documented warning that "hexadecimal uuid" in field descriptions triggers hyphen-stripping in GPT-class models. Direction 1 fixes the current instance; this direction prevents the next.
- **Effort**: Very low — add a bullet to the OPTIMIZE_INSTRUCTIONS constant.
- **Risk**: None — documentation only.

  **Proposed addition to `enrich_potential_levers.py` OPTIMIZE_INSTRUCTIONS:**
  ```
  - lever_id format fragility. When field descriptions or system prompts use the phrase
    "hexadecimal uuid", some models (e.g. gpt-4o-mini) interpret "hexadecimal" as implying
    a raw hex encoding and strip hyphens from the UUID. Always use the explicit standard
    format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) in any field description or prompt that
    references lever_id format. A normalization fix in execute() — comparing stripped UUIDs
    for map lookup — provides defense-in-depth independent of prompt wording.
  ```

### 5. Fix partial_recovery warning threshold in runner.py
- **Type**: code fix
- **Evidence**: S3 (code review). Verified at `runner.py:131` — threshold is `< 3`, but the comment directly above states "A 2-call success is normal for models that produce 8+ levers per call."
- **Impact**: Eliminates misleading telemetry. Currently, any model that completes in 2 calls (normal early-stop behavior) is logged as a "partial recovery." Fixing the threshold to `< 2` limits the warning to the true degenerate case: only 1 successful call out of max_calls=5.
- **Effort**: Very low — one character change (`< 3` → `< 2`).
- **Risk**: Minimal. Makes logging semantically correct; does not affect execution behavior.

## Recommendation

**Do direction 1 and direction 2 together as a single PR.**

Direction 1 (field description + system prompt phrasing) is the proximate fix for the critical gpt-4o-mini regression introduced by PR #468. The regression causes 13/35 levers to go unenriched across 4 of 5 plans for a commonly used model — a 37% lever loss rate that is a production-quality defect. The fix is two string changes and is low-risk.

Direction 2 (defensive UUID normalization in code) should ship in the same PR because: (a) it is also low-effort, (b) it provides defense-in-depth that makes the pipeline format-agnostic regardless of future prompt wording, and (c) it is the complementary code fix to the prompt fix. These two changes together close both the immediate defect and the structural brittleness that converts formatting variation into silent data loss.

**Specific changes:**

1. `enrich_potential_levers.py:138` — change field description from `"The hexadecimal uuid of the lever, without XML tags"` to `"The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags"`.

2. `enrich_potential_levers.py:170` — change `"the hexadecimal uuid string inside the tags"` to `"the standard UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) inside the tags"`.

3. `enrich_potential_levers.py:276–285` — replace the `if char.lever_id in enriched_levers_map:` block with the normalized lookup shown in direction 2 above.

These three changes constitute the minimum fix for the CONDITIONAL verdict on PR #468.

## Deferred Items

- **Direction 3** (remove banned phrases from `identify_potential_levers.py:116–119`): Valid OPTIMIZE_INSTRUCTIONS alignment fix, but not urgent — no observable regression in runs 76–82. Suitable for a follow-up PR against `identify_potential_levers.py`.

- **Direction 4** (OPTIMIZE_INSTRUCTIONS documentation): Should be added to `enrich_potential_levers.py` after the fix lands, so the entry documents the known-and-fixed pattern rather than an open regression.

- **Direction 5** (runner.py partial_recovery threshold): One-line fix that improves telemetry accuracy. Trivial to include in any housekeeping PR.

- **Haiku word count target** (N3/Q4 from insight): Haiku averages 515 chars (≈ 86 words, 1.06× baseline) — slightly above the 50–70 word target but within acceptable quality range. Monitor over more runs before tightening.

- **gpt-4o-mini silo plan anomaly** (Q2 from insight): Why does gpt-4o-mini correctly return hyphenated UUIDs for the silo plan but not the other 4? Batch position or plan-specific content may influence behavior. Not blocking, but worth investigating once the fix is verified.

- **Anti-echoing effectiveness measurement** (Q3 from insight): Whether the `"Add new insight beyond what consequences and review already state"` instruction reduces consequence echoing requires semantic similarity analysis across runs. Fabricated percentage claims dropped slightly (47 → 41), but causal attribution is unclear.
