# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude and code_claude) agree on all major findings:

1. **C3 (UUID fix) is the highest-priority omission.** The one-line change at
   `enrich_potential_levers.py:190` was documented as a priority in analysis 55 but is still
   absent from PR #453. UUID contamination affects 89% of llama3.1 free-text fields, 34% of
   gemini, and 53% of gpt-oss-20b — degrading content quality in the majority of all
   successful runs.

2. **C1/C2 interaction is a design bug.** Both agents independently identify that C1's
   `max_tokens` bump inflated `num_output` from 8192 to 128000 for gpt-oss-20b, making
   C2's `num_output < 16384` check trivially false. C2 no longer protects the model it
   was designed for. The correct fix is to check `context_window` in addition to (or
   instead of) `num_output`.

3. **The guarded retry is the strongest positive change.** The 3×600s timeout cascade from
   PR #452 is fully eliminated. gpt-oss-20b now fails 3 plans in <2s each via
   `empty_response` rather than timing out at 600s each (~1800s → <6s wasted). This is a
   clear, correctly-implemented win regardless of the C1/C2 flaw.

4. **gpt-oss-20b still fails 3/5 plans.** The failure mode changed (timeout → fast
   empty_response) but functional success rate is unchanged at 2/5. The likely cause is
   `max_tokens=128000 >> context_window=3900` causing provider-level rejections at certain
   OpenRouter backends.

5. **PR verdict: CONDITIONAL.** Keep the guarded retry. Fix C4 (context_window threshold)
   and C3 (UUID strip) as immediate follow-ups.

---

## Cross-Agent Disagreements

No substantive disagreements. code_claude surfaces three issues not mentioned in
insight_claude (B3, B4, S3), but these are additive — insight_claude does not contradict
them.

**B3 (consequences field description naming banned phrases):** Only code_claude flags this.
Verified in `identify_potential_levers.py:113–119`: the `consequences` field description
explicitly names `'Controls ... vs.'` and `'Weakness:'` as forbidden phrases. OPTIMIZE_INSTRUCTIONS
lines 86–92 ("Field-description template lock") warns that naming a structural phrase in a field
description causes models to start outputs with that very phrase. The ban is self-defeating for
small models. This is a valid finding.

**B4 (thread filter captures wrong thread):** Only code_claude flags this. Verified in
`runner.py:543–548`: `_ThreadFilter` captures `_run_plan_task`'s thread ident, but the actual
plan work runs in an inner `ThreadPoolExecutor(max_workers=1)` (line 555). All detailed LLM
execution logs originate from the inner thread and are filtered out. Per-plan `log.txt` files
are nearly empty. This is a real debugging regression but does not affect plan quality or
success rates.

**S3 (false-positive "partial recovery" warning):** Confirmed in `runner.py:131–134`. The
comment above the threshold says "A 2-call success is normal for models that produce 8+ levers
per call", yet the warning fires whenever `actual_calls < 3`, which is exactly that normal
case. The "partial recovery" label in `events.jsonl` is misleading. Low priority.

---

## Top 5 Directions

### 1. Strip UUID from `full_lever_context_str` (C3)
- **Type**: code fix
- **Evidence**: Both agents; code_claude B1 / insight_claude N3. Verified: `enrich_potential_levers.py:190`
  currently reads `f"- {lever.lever_id}: {lever.name}"`. The per-batch details at lines
  213–219 already include `lever.lever_id`, so the ID-echo and `enriched_levers_map` lookup
  are unaffected by removing it from the full-list context string.
- **Impact**: UUID contamination rates of 89% (llama3.1), 34% (gemini), 53% (gpt-oss-20b)
  in synergy/conflict free-text fields. This degrades readability and credibility of
  enriched lever output in the majority of successful plans across 3 of 7 tested models.
  Content quality improvement affects all 32/35 functionally successful plans that use
  these models.
- **Effort**: Low — one-line change.
- **Risk**: Negligible. The UUID is still present in the per-lever batch prompt (lines
  213–214: `f"Lever ID: {lever.lever_id}\n"`) so the LLM can still echo it back for
  the `enriched_levers_map` lookup. Only the full-list context section changes.

---

### 2. Fix adaptive batch size to check `context_window` (C4)
- **Type**: code fix
- **Evidence**: Both agents; code_claude B2 / insight_claude N1, N2. Verified:
  `enrich_potential_levers.py:181` uses `num_output` (which reflects LlamaIndex's
  `max_tokens` setting) rather than `context_window` (the model's actual per-call token
  budget). After C1 bumped gpt-oss-20b's `max_tokens` to 128000, `num_output` inflated
  and the `< 16384` check is always false for that model.
- **Impact**: gpt-oss-20b has `context_window=3900`. With `batch_size=5` and
  `max_tokens=128000`, providers that enforce the actual model limit return `empty_response`
  for 3/5 plans. Switching to `context_window < SMALL_CONTEXT_THRESHOLD (8000)` would
  route gpt-oss-20b to `batch_size=2`, halving input tokens per batch and reducing the
  prompt footprint to within provider limits. This is the primary remaining gpt-oss-20b
  failure path.
- **Effort**: Low — add one constant (`SMALL_CONTEXT_THRESHOLD = 8000`) and change the
  condition from `num_output < SMALL_OUTPUT_THRESHOLD` to
  `num_output < SMALL_OUTPUT_THRESHOLD or context_window < SMALL_CONTEXT_THRESHOLD`.
- **Risk**: Low. The new clause only triggers for models with very small declared
  context windows. Models with large context windows are unaffected. Haiku and other
  models already triggering via `num_output < 16384` continue to do so.

  **Note**: Also consider whether `max_tokens=128000` for gpt-oss-20b is itself causing
  provider rejections (C1 overcorrection). A more conservative bump (e.g., 32000) would
  clear the old 8192 truncation while staying closer to the actual `context_window=3900`
  limit. This could be combined with C4 or treated as a separate follow-up.

---

### 3. Remove English-phrase bans from `consequences` field description (B3)
- **Type**: prompt change (Pydantic field description in `identify_potential_levers.py`)
- **Evidence**: code_claude only. Verified: `identify_potential_levers.py:113–119` (and the
  identical duplicate at `LeverCleaned` lines 208–216) name the exact phrases `'Controls ...
  vs.'` and `'Weakness:'` inside the field description. OPTIMIZE_INSTRUCTIONS lines 86–92
  ("Field-description template lock") warns that naming a structural phrase in a field
  description causes models to begin outputs with that phrase. The prohibition becomes a
  template.
- **Impact**: Affects all models in the identify_potential_levers step. The
  `consequences` field is passed directly into the enrich step's batch prompts. If weak
  models are echoing "Do NOT include 'Controls ... vs.' or 'Weakness:'" verbatim as
  part of their consequences text, the downstream enrichment prompts become polluted.
  Impact is medium — not directly measured in this experiment but predicted by
  OPTIMIZE_INSTRUCTIONS guidance on field-description template lock.
- **Effort**: Low — rewrite the field description to describe what is wanted rather than
  what is forbidden. Example replacement: "Describe the direct effect of pulling this lever
  and at least one downstream implication or trade-off. Be concise and grounded; cite
  numbers only if the project context provides evidence for them. Target 2–4 sentences."
  (Remove the "Do NOT include..." sentence entirely.)
- **Risk**: Low. The `check_review_format` validator already uses structural checks
  (length, no square brackets) without English keyword matching, so validation is not
  affected. The prohibition's intent is already covered by the system prompt examples.

---

### 4. Add anti-echoing instruction to `ENRICH_LEVERS_SYSTEM_PROMPT` (I3)
- **Type**: prompt change
- **Evidence**: Both agents; code_claude I3 / insight_claude H1 / P4. OPTIMIZE_INSTRUCTIONS
  lines 82–87 documents consequence echoing as a known problem but the system prompt at
  `enrich_potential_levers.py:154` does not explicitly guard against it.
- **Impact**: llama3.1 description length ratio is 0.76× baseline (up from 0.65× in
  analysis 54) — a positive trend, but still below 1.0×. The improvement is partially
  attributable to smaller input (baseline/train), not solely to prompt changes. Adding
  an explicit instruction ("The description must add new context beyond what consequences
  already states — do not summarize or rephrase the consequences field") would give all
  models a clear directive to elaborate rather than echo.
- **Effort**: Low — append one sentence to the existing `description` requirement in
  `ENRICH_LEVERS_SYSTEM_PROMPT`.
- **Risk**: Low. The instruction is additive and targets a specific failure mode. There
  is a small risk that models react by padding with filler instead of echoing, but
  OPTIMIZE_INSTRUCTIONS already warns against padding (line 71) and the system prompt
  word-count target constrains length.

---

### 5. Document C1/C2 `max_tokens`/`context_window` confusion in `OPTIMIZE_INSTRUCTIONS`
- **Type**: workflow change (documentation in `enrich_potential_levers.py`)
- **Evidence**: Both agents; insight_claude "OPTIMIZE_INSTRUCTIONS Alignment" section.
- **Impact**: OPTIMIZE_INSTRUCTIONS currently documents the UUID problem (lines 88–92)
  but not the `num_output` vs `context_window` conflation revealed by this PR. Future
  self-improve agents may repeat the same class of error — changing `max_tokens` without
  understanding that LlamaIndex exposes it as `num_output` and that this is separate from
  `context_window`. Adding an entry prevents recurrence across future infrastructure
  changes.
- **Effort**: Low — 3–5 sentence addition to `OPTIMIZE_INSTRUCTIONS` in
  `enrich_potential_levers.py`.
- **Risk**: Negligible — documentation only.

---

## Recommendation

**Do C3 first** (strip UUID from `full_lever_context_str`).

**File**: `enrich_potential_levers.py`
**Line**: 190
**Current code**:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
**Fixed code**:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

**Why first**: This is the highest-impact unfixed bug with the lowest implementation risk.
UUID contamination in free-text fields affects 89% of llama3.1 synergy/conflict outputs,
34% of gemini, and 53% of gpt-oss-20b — degrading content quality across 3 of 7 models in
the majority of all successful plans. The fix was documented as a priority in analysis 55,
is a one-line change, and carries no risk to correctness: the per-lever batch prompt (lines
213–214) still exposes the UUID for the `enriched_levers_map` lookup, so the matching
mechanism is fully preserved. The fix is orthogonal to everything else in PR #453 and
requires no coordination with C1/C2/C4.

By contrast, C4 (direction 2) requires adding a constant and modifying a conditional — still
simple, but has a wider blast radius (changes batch routing for any model with
`context_window < 8000`) and depends on correctly understanding the gpt-oss-20b
empty_response root cause before picking a threshold. It should follow C3 in the next PR.

---

## Deferred Items

- **C4 (context_window threshold fix)**: Do second, immediately after C3. Add
  `SMALL_CONTEXT_THRESHOLD = 8000` and update the batch-size condition.
  `enrich_potential_levers.py:181`.

- **Conservative max_tokens for gpt-oss-20b**: If C4 alone does not resolve
  empty_response failures, consider reducing `max_tokens` from 128000 back to a value
  closer to `context_window` (e.g., 32000 or 65536) in `baseline.json`. This is a
  configuration change, not a code change.

- **B3 (consequences field description)**: Removing the English-phrase ban from
  `identify_potential_levers.py:113–119` and `208–216` is low-risk. Schedule for the
  same PR as C4 or the following one.

- **I3 (anti-echoing in system prompt)**: Add "The description must add new context beyond
  what consequences already states — do not summarize or rephrase the consequences field."
  to `ENRICH_LEVERS_SYSTEM_PROMPT` at `enrich_potential_levers.py:154`.

- **Direction 5 (OPTIMIZE_INSTRUCTIONS entry)**: Add a note about `num_output` vs
  `context_window` conflation. Bundle with the C4 PR.

- **B4 (thread filter captures wrong thread)**: `runner.py:543–548`. The
  `_ThreadFilter` captures `_run_plan_task`'s ident but plan work runs in a child
  executor thread. Per-plan `log.txt` files are nearly empty. Fix by passing the inner
  thread's ident to the filter after `executor.submit()`. Low priority — does not
  affect plan quality, only debugging.

- **S2 (silent lever loss on wrong UUID)**: `enrich_potential_levers.py:248–255`. If the
  LLM echoes a malformed UUID, the lever is silently dropped. Add a regex format check
  before the map lookup to surface this earlier. Low priority for now.

- **S3 (false-positive "partial recovery" warning)**: `runner.py:131`. The `actual_calls < 3`
  threshold fires on normal 2-call early-stop completions. Either raise the threshold to 2
  (`actual_calls < 2`) or change the warning message to distinguish early-stop success
  from failure recovery.
