# Synthesis

## Cross-Agent Agreement

Only one insight file (`insight_claude`) and one code review (`code_claude`) were produced for this analysis (no Codex counterpart). Both files reach the same conclusions independently:

- **Verdict: REVERT** PR #464.
- The regression is caused by two composing defects: B1 (UUID moved to end of lever block) and B2 (no name-based fallback in the matching loop). Together they cause 100% failure for llama3.1 and 71% failure for gpt-5-nano.
- Three models (qwen3, gpt-4o-mini, gemini-flash) are unaffected and remain at 100%.
- The preferred fix is either **H1** (pure revert — restore `Lever ID: {uuid}` as first line) or **C2** (code fallback that keeps UUID at end but resolves names). H1 is preferred for simplicity and known-good behavior.
- `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` must be updated to document that UUID *position* (not just format) affects structured-output matching in small models.

## Cross-Agent Disagreements

None. The single insight and single code review are fully consistent. All claims are verifiable directly in the source:

- **B1** confirmed: `enrich_potential_levers.py:240–247` — UUID is the last line, labeled `(internal reference: {lever.lever_id})`.
- **B2** confirmed: `enrich_potential_levers.py:276` — `if char.lever_id in enriched_levers_map` is a strict UUID-keyed lookup with no name fallback.
- **S1** confirmed: `enrich_potential_levers.py:139` — `lever_id: str = Field(description="The uuid of the lever")` gives no extraction hint.
- **S2** confirmed: `enrich_potential_levers.py:178` ("Return exactly one characterization per lever") and `enrich_potential_levers.py:254–255` ("Return exactly {N} characterizations") are duplicative.
- **S3** confirmed: `enrich_potential_levers.py:88–97` documents UUID *format* risk ("keep the full UUID") but is silent about UUID *position* risk — the exact gap PR #464 exploited.
- **S4** confirmed: `runner.py:282` — `dispatcher.event_handlers.remove(track_activity)` in `finally` block is unguarded; a `ValueError` would mask the original exception.
- **I4** confirmed: `runner.py:577–583` — `partial_recovery` event is gated to `identify_potential_levers` only; `enrich_potential_levers` has the same silent-failure mode.

## Top 5 Directions

### 1. Revert UUID to first line of `lever_details_for_prompt`
- **Type**: prompt change (1 line revert)
- **Evidence**: Both agents; B1, N1, N2; root cause confirmed in source code. PR #464 introduced this change; it is the direct cause of all regressions.
- **Impact**: Restores llama3.1 from 0/35 to ~35/35 and gpt-5-nano from 10/35 to ~35/35. Recovers ~60 lever characterizations across 5 plans. Affects 2 of 7 models. No negative side-effects on the 5 models currently at 100%. The UUID leakage concern (the PR's motivation) is already partially addressed by PR #457's removal of UUIDs from `full_lever_context_str`; per-batch exposure without cross-batch propagation is the remaining risk, and it is lower priority than complete matching failure.
- **Effort**: low — single line change in `enrich_potential_levers.py:240–247`; no code changes needed.
- **Risk**: Very low. This is a known-good state (PR #457 baseline). Reverting one line restores prior behavior exactly.

### 2. Add name-to-UUID fallback in the matching loop (C2)
- **Type**: code fix
- **Evidence**: Both agents; B2, I1; confirmed at `enrich_potential_levers.py:276`.
- **Impact**: Recovers characterizations where a model returns the correct lever name as `lever_id` instead of the UUID. Independently useful regardless of whether UUID stays first or last — future prompt changes or model behaviors could trigger name-returns again. Would fully recover llama3.1 even in the current (broken) prompt format.
- **Effort**: low-medium — build `name_to_lever_id` reverse map at line 218, add elif branch at line 276. ~10 lines of code. Names in a lever set are designed to be distinct, so ambiguity risk is low.
- **Risk**: Low. The fallback only fires when a UUID lookup fails; it does not affect the happy path. Slight risk of false positives if a lever name happens to equal a UUID string (effectively impossible in practice).

### 3. Update `OPTIMIZE_INSTRUCTIONS` with UUID position risk (I2)
- **Type**: prompt change (documentation only)
- **Evidence**: Both agents; S3; confirmed gap in `enrich_potential_levers.py:88–97`.
- **Impact**: Prevents future developers from repeating the same mistake. `OPTIMIZE_INSTRUCTIONS` correctly warns about UUID format and negative prohibitions, but does not warn that position matters. Adding the entry closes this gap for all future iterations.
- **Effort**: low — append one bullet to the Known Problems section.
- **Risk**: None. Documentation-only change.

### 4. Strengthen `LeverCharacterization.lever_id` field description (I3/S1)
- **Type**: prompt change
- **Evidence**: Code review; S1; confirmed at `enrich_potential_levers.py:139`.
- **Impact**: Telling models *where* to find the UUID reduces reliance on positional heuristics. Most valuable if Direction 1 is NOT taken and UUID remains at end — a field description like `"Copy the UUID exactly from the '(internal reference: ...)' line at the end of the lever block"` gives small models an explicit extraction instruction. May partially recover gpt-5-nano even without reverting B1. For models already working correctly, it is a no-op.
- **Effort**: low — single field description change at `enrich_potential_levers.py:139`.
- **Risk**: Low. `OPTIMIZE_INSTRUCTIONS` warns that structural phrasing in field descriptions can cause template lock, but this description is instructional rather than structural ("copy from X" not "begin with phrase Y").

### 5. Add `partial_recovery` guard for `enrich_potential_levers` in `runner.py` (I4)
- **Type**: code fix
- **Evidence**: Code review; I4; confirmed at `runner.py:577–583` and `enrich_potential_levers.py:99–103`.
- **Impact**: `enrich_potential_levers` already has a documented silent failure mode: status remains "ok" but `characterized_levers` is empty. PR #464 exposed this — all 5 llama3.1 plans showed `status=ok` with 0 levers. An analogous `partial_recovery` event when `batches_succeeded < expected_batches` would surface this in the events log, making monitoring and post-run analysis easier. Does not improve success rates but reduces the observability gap.
- **Effort**: low — ~5 lines mirroring the existing `identify_potential_levers` guard.
- **Risk**: Very low. Additive monitoring only.

## Recommendation

**Implement Direction 1: revert `lever_details_for_prompt` to put UUID first.**

**Why first:** It is the direct cause of a 26% total loss (64/245 lever characterizations) across 2 of 7 models with zero benefit confirmed. The three unaffected models (qwen3, gpt-4o-mini, gemini-flash) were fine before PR #464 too, so reverting loses nothing. The UUID leakage motivation is real but the risk is low: PR #457 already removed UUIDs from `full_lever_context_str`, which is the cross-batch exposure path. Within-batch UUID visibility is a lower-order concern than complete failure.

**Exact change** — `enrich_potential_levers.py:240–247`:

```python
# Current (broken) — PR #464
lever_details_for_prompt = "\n\n".join([
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}\n"
    f"(internal reference: {lever.lever_id})"
    for lever in batch
])

# Recommended — restore UUID as first line
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}"
    for lever in batch
])
```

Also keep the two improvements from PR #464 that are safe:
- **Line 176** (positive framing): "In `synergy_text` and `conflict_text`, always refer to other levers by their name — for example, write 'Policy Advocacy Strategy', not an identifier." — retain this; it is directionally correct and harmless.
- **`OPTIMIZE_INSTRUCTIONS` update** (I2): append the UUID position risk note (see Direction 3 wording) so future iterations do not repeat PR #464's mistake.

Do not retain the "exactly {N}" user prompt addition (S2) — it is redundant with the system prompt and had no measurable effect on haiku over-generation.

## Deferred Items

- **Direction 2 (name-to-UUID fallback, C2)**: Worth doing as a belt-and-suspenders code fix after the revert, but not urgent once UUID is back at first position. When implemented, pair with the field description update (Direction 4) and `OPTIMIZE_INSTRUCTIONS` entry (Direction 3).
- **Direction 4 (lever_id field description)**: Relevant only if UUID-at-end is attempted again in a future PR alongside C2. Park until then.
- **Direction 5 (partial_recovery for enrich_potential_levers)**: Low priority observability fix. Good housekeeping but not blocking.
- **S4 (runner.py remove() unguarded)**: Minor defensive-coding issue at `runner.py:282`. Not related to this PR; fix in a separate cleanup PR.
- **Haiku over-generation (N4)**: Haiku generates phantom characterizations with invented UUIDs (7 before, 11 after). `max_items` constraint in the response schema or a code-level `len(batch_result.characterizations) == len(batch)` check could cap this. Deferred — it is a pre-existing behavior that does not block correct characterizations.
- **Confirm UUID leakage reduction**: Before declaring UUID leakage fully solved, count UUID occurrences in `synergy_text`/`conflict_text` of the 3 working models' outputs. If leakage is negligible even with UUID at first position (because `full_lever_context_str` no longer contains UUIDs), the entire motivation for PR #464 may already be addressed by PR #457 alone.
