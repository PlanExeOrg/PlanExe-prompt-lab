# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `self_improve/runner.py`

---

## Bugs Found

**B1 — Spurious `partial_recovery` event for legitimate 2-call completions**

`runner.py:125–133` and `runner.py:546–552`

`_run_levers` emits a `logger.warning` and `_run_plan_task` emits a `partial_recovery` event whenever `calls_succeeded < 3`. But the inline comment at `runner.py:121–123` explicitly states: "A 2-call success is normal for models that produce 8+ levers per call." Models that return 8+ levers per call (common for stronger models) will legitimately complete in 2 calls, yet every such run is mislabeled as a partial recovery in `events.jsonl`. This can make normal runs look like failures in downstream analysis.

```python
# runner.py:121-133
# A 2-call success is normal for models that produce 8+ levers per call.
# Only warn if we got fewer responses than expected for 15 levers (~3 calls at 5-7 levers each).
if actual_calls < 3:      # ← warns on normal 2-call behavior
    logger.warning(...)

# runner.py:546-552
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):   # ← emits partial_recovery for normal completions
    _emit_event(events_path, "partial_recovery", ...)
```

The threshold should be `< 2` (or `< 1`) to only catch true failures. Or the warning and event should be removed and replaced with a check that no levers were generated at all.

---

**B2 — `calls_succeeded` in `_run_deduplicate` always equals `len(input_levers)`**

`runner.py:155`

```python
return PlanResult(
    ...
    calls_succeeded=len(result.response),   # ← always == len(input_levers)
)
```

`result.response` is `List[LeverDecision]`. One `LeverDecision` is always appended per input lever — either from the LLM or from the fallback-to-primary default at `deduplicate_levers.py:218–226`. So `len(result.response)` always equals the number of input levers (e.g., always 15 for a 15-lever plan), regardless of how many LLM calls actually succeeded. The metric is constant and provides zero diagnostic value. It cannot distinguish a run where all 15 LLM calls succeeded from one where all 15 failed and defaulted.

---

**B3 — `_build_compact_history` unconditionally appends `...` suffix**

`deduplicate_levers.py:70`

```python
f"- [{d.lever_id}] {d.classification}: {d.justification[:80]}..."
```

The `...` is appended regardless of whether truncation actually occurred (`len(d.justification) <= 80`). A short, complete 40-character justification will appear in the compacted history as `"...fully justified...` — implying to the LLM that there is additional context it cannot see. For absorption decisions, this matters: the justification often names the target lever ID, and if the LLM infers the justification is incomplete, it may re-classify an already-resolved lever differently during the retry.

Fix: `d.justification[:80] + ("..." if len(d.justification) > 80 else "")`.

---

## Suspect Patterns

**S1 — Safety valve "Use 'primary' if you lack understanding" is too permissive**

`deduplicate_levers.py:104–107`

```
Use "primary" if you lack understanding of what the lever is doing. This way a potential important lever is not getting removed.
Describe what the issue is in the justification.
```

This instruction gives weak models (llama3.1) cover to classify every lever as `primary` without performing any absorb/remove work. Combined with the next line "Don't play it too safe, so you fail to perform the core task", the prompt sends contradictory signals: "when uncertain, use primary" vs. "don't be too conservative." For llama3.1, the safety valve wins — 14/15 levers classified primary, 0 absorb/remove (N1 in insight). There is no countervailing calibration hint like the typical number of absorptions expected for a set of 15 levers.

---

**S2 — `execute_function` closure captures `chat_message_list` by variable reference across rebinding**

`deduplicate_levers.py:164, 170, 192`

```python
chat_message_list: List[ChatMessage] = [...]   # line 164: initial binding

def execute_function(llm: LLM) -> dict:
    return _call_llm(chat_message_list, llm)   # line 170-171: captures variable name

# ... on failure:
chat_message_list = _build_compact_history(...)  # line 192: rebinds to new list
```

The closure reads the variable `chat_message_list` at call time, not at definition time. When the fallback compaction rebinds the local variable (line 192), `execute_function` correctly picks up the new list on the next `run()` call. In current code this is safe: the rebind happens between `run()` calls, never during one. However this pattern is fragile: if `llm_executor.run()` is ever made asynchronous or gains concurrent internal retry logic, calls to `execute_function` could race against a rebind. The comment at line 167–169 acknowledges this but treats it as intentional. Worth isolating with a cleaner closure or by passing the list explicitly.

---

**S3 — review_lever examples 1 and 3 share a rhetorical structure**

`identify_potential_levers.py:248–251`

Example 1: "Switching from seasonal contract labor ... stabilizes harvest quality, **but** the idle-wage burden ... adds a fixed cost that erases the per-unit savings **unless** utilization reaches year-round levels."

Example 3: "Pooling catastrophe risk ... reduces expected annual loss on paper, **but** a single regional hurricane season can correlate all three simultaneously, turning the diversification assumption into a concentration risk ..."

Both follow the pattern: `[X achieves beneficial Y], but [Z introduces a downside unless/at-the-worst W]`. `OPTIMIZE_INSTRUCTIONS` at lines 74–82 explicitly warns: "No two examples should share a sentence pattern or rhetorical structure." The two shared rhetorical patterns here ("X but Z" + a subordinate clause of qualification) provide a template weak models can copy verbatim in any domain.

---

**S4 — `generated_lever_names` exit condition counts raw (pre-dedup) names**

`identify_potential_levers.py:350–356`

```python
generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
...
if len(generated_lever_names) >= min_levers:
    break
```

`generated_lever_names` accumulates all names across calls without deduplication. If call 2 returns names that overlap with call 1 (possible for weak models that ignore the exclusion list), the exit condition `>= 15` can be reached with fewer than 15 *unique* levers. The deduplication step at line 364–380 then removes duplicates, potentially leaving fewer than 15 levers in the cleaned output. This is an edge case since the call-2 prompt explicitly names the levers to exclude, but weaker models do not reliably honor that instruction.

---

## Improvement Opportunities

**I1 — Add `OPTIMIZE_INSTRUCTIONS` to `deduplicate_levers.py`**

`deduplicate_levers.py` has no `OPTIMIZE_INSTRUCTIONS` constant. `identify_potential_levers.py` has a 67-line block documenting known failure modes for self-improve guidance. The insight file identifies four confirmed failure modes for `deduplicate_levers`:
- Blanket-primary (llama3.1: 0% deduplication rate)
- Hierarchy-direction errors (gemini: absorbs more-general into more-specific)
- Chain absorption (qwen3: A→B→C where B is itself absorbed)
- Over-inclusion (gpt-4o-mini: 12/15 kept vs. 7 baseline)

None are documented anywhere in the file. Add an `OPTIMIZE_INSTRUCTIONS` block above the class definition, following the format established in `identify_potential_levers.py`.

---

**I2 — Post-deduplication zero-reduction warning**

`deduplicate_levers.py`: after the `output_levers` loop (after line 263)

Add a check before the `return cls(...)`:

```python
if len(output_levers) >= 0.9 * len(input_levers):
    logger.warning(
        f"Deduplication kept {len(output_levers)}/{len(input_levers)} levers "
        f"(≥90% — model likely failed to absorb near-duplicates)."
    )
```

Zero-reduction is always a deduplication failure (N1: llama3.1 kept all 15). N3 (gpt-4o-mini kept 12/15 = 80%) is also suspect. An 80–90% threshold would catch both without triggering on well-performing runs.

---

**I3 — Chain absorption detection**

`deduplicate_levers.py`: after collecting all decisions, before building `output_levers`

After the per-lever loop (after line 232), scan for chains:

```python
absorbed_into = {
    d.lever_id: d.justification  # target ID would need to be parsed from justification
    for d in decisions
    if d.classification == LeverClassification.absorb
}
```

A full implementation requires parsing the target lever ID from the justification text (since the schema doesn't have an explicit `absorb_into_id` field — see PR Review section). At minimum, a structural check can verify whether any lever that is the target of an absorption is itself marked `absorb`:

```python
absorb_ids = {d.lever_id for d in decisions if d.classification == LeverClassification.absorb}
for d in decisions:
    if d.classification == LeverClassification.absorb:
        # Parse target ID from justification (heuristic: look for lever_id pattern)
        ...
```

If the target of an absorption is itself being absorbed, log a WARNING (N6). The final `output_levers` is still correct (both A and B are filtered), but the justification for A references a lever that won't appear in the output, which is confusing downstream.

---

**I4 — Narrow the safety valve with expected absorb count**

`deduplicate_levers.py:104–107`

Replace:
```
Use "primary" if you lack understanding of what the lever is doing. This way a potential important lever is not getting removed.
```

With something like:
```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's strategic role after reading the full context. In a well-formed set of 15 levers, typically 4–8 should be absorbed or removed. If you find zero absorb/remove decisions, reconsider: the input almost always contains near-duplicates.
```

This preserves the safety fallback while providing a calibrating expectation that counteracts the blanket-primary pattern (N1). Risk: may cause over-aggressive removal for already-good models. Test with haiku and qwen3 to verify they are not affected.

---

**I5 — Fix or document `calls_succeeded` metric for `deduplicate_levers`**

`runner.py:155`

Either:
- Track actual LLM call failures during the deduplication loop and surface them as a distinct count, or
- Rename the field to `levers_processed` or `decisions_count` to accurately reflect what is being counted, so analysis code is not misled into thinking it measures call-level success.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| **N1** — llama3.1 zero deduplication | S1 (safety valve too permissive); I4 (no calibrating absorb expectation); I2 (no post-dedup validation to catch and log it) |
| **N2** — gemini hierarchy-direction errors | No code-level enforcer; prompt ambiguity. Partially tracked by I3 (chain detection would catch related issues). I1 would at least document it for future prompting. |
| **N3** — gpt-4o-mini over-includes (12/15) | I2 (no zero/near-zero reduction warning); I4 (no count guidance in prompt) |
| **N4** — classification disagreement across models | No code-level fix applicable; prompt's abstract descriptions need concrete examples (H2 in insight). I1 would document this. |
| **N5** — terminology mismatch PR vs. code | Documentation only; no code bug. The `LeverClassification` enum values are `primary`/`secondary` throughout the codebase. |
| **N6** — chain absorption not detected | I3 (no chain detection logic exists) |
| **N7** — no `OPTIMIZE_INSTRUCTIONS` | I1 |
| **N8** — fabricated numbers pass through | No validator on `consequences` field (adding one is impractical). The upstream `identify_potential_levers.py` system prompt prohibits fabrication (line 234, 259) but cannot enforce it structurally. `OPTIMIZE_INSTRUCTIONS` at line 51–54 documents it. No code-level fix exists. |

---

## PR Review

**PR #363: feat: add keep-core/keep-secondary classification to deduplicate_levers**

### Does the implementation match the intent?

Yes, for the core deliverable. The PR splits the single `keep` classification into `primary` and `secondary`. The implementation is internally consistent:
- `LeverClassification` enum: `primary`, `secondary`, `absorb`, `remove` (`deduplicate_levers.py:22–26`)
- `LeverClassificationDecision.classification`: `Literal["primary", "secondary", "absorb", "remove"]` (line 30)
- `OutputLever.classification`: `Literal["primary", "secondary"]` (line 58)
- `keep_classifications`: `{LeverClassification.primary, LeverClassification.secondary}` (line 235)
- System prompt: describes `primary`/`secondary` correctly (lines 91–92)

### Terminology mismatch (N5)

The PR title and description use "keep-core" / "keep-secondary". The code uses "primary" / "secondary" everywhere. This disconnect has no runtime impact but creates confusion for anyone reading the PR diff and then looking at log output or JSON files. The `LeverClassification` enum values are used as string literals in the output JSON; changing them in a follow-up would be a breaking change for any downstream consumer that pattern-matches on the string "primary".

### Missing explicit `absorb_into_id` field

When a lever is classified `absorb`, the target lever ID is embedded in free-text `justification` rather than a structured field. The `LeverClassificationDecision` schema at line 28–41 has no `absorb_into_id` field; the field description says "If absorbing, state which lever id it merges into" inside the `justification` text. This means:
- Chain absorption detection (I3) requires text parsing of the justification
- Post-hoc verification that the absorption target exists is impossible without text parsing
- The `deduplication_justification` in `OutputLever` carries this information but it is opaque to code

Adding `absorb_into_id: Optional[str] = None` to `LeverClassificationDecision` would make absorption decisions machine-readable and enable I3 without text parsing. The field could be ignored for `primary`/`secondary`/`remove` classifications.

### Safety valve introduced by PR amplifies llama3.1 failure

The system prompt line 104 reads:
```
Use "primary" if you lack understanding of what the lever is doing.
```

This instruction (or its predecessor) existed before the PR. However, with the PR's expanded classification vocabulary (`primary`/`secondary`/`absorb`/`remove` vs. the previous `keep`/`absorb`/`remove`), models have one additional "safe" category to fall into. For llama3.1, adding `secondary` as an additional keep-classification does not appear to have changed behavior — it still classifies everything as `primary` — but the safety valve now applies to a 4-class schema rather than a 3-class one, potentially making the calibration worse.

### Backwards compatibility

The PR description claims `enrich_potential_levers.py` accepts the new `classification` field as optional. This is correct for the schema side (the field is `Optional` in the enrich schema). No regressions were introduced in the 7-model test runs (100% success rate, 0 `LLMChatError` events).

### Edge case: missing decision default uses `LeverClassification.primary` enum value

`deduplicate_levers.py:243` (missing decision fallback) and `deduplicate_levers.py:219–220` (failed-call fallback) both default to `LeverClassification.primary`. This is correct behavior, but given that `OutputLever.classification` accepts `Literal["primary", "secondary"]`, passing `LeverClassification.primary` (the enum instance, not the string "primary") works because `LeverClassification` extends `str`. This is implicitly relying on `str(Enum)` coercion. Adding an explicit `.value` access (`LeverClassification.primary.value`) would make the intent clearer and avoid surprises if the enum base class changes.

---

## Summary

`deduplicate_levers.py` is functionally correct and the PR achieves its stated goal. The primary code-quality issues are:

1. **B1** (runner.py): Spurious `partial_recovery` events for normal 2-call completions mislead analysis.
2. **B2** (runner.py): `calls_succeeded` for `deduplicate_levers` is always constant (= `len(input_levers)`), providing no diagnostic value.
3. **B3** (deduplicate_levers.py): Compact history always appends `...` even for un-truncated justifications.
4. **S1**: The safety-valve prompt instruction ("Use 'primary' if you lack understanding") is too broad and is the most plausible code-level explanation for the N1 llama3.1 blanket-primary failure.
5. **I1**: No `OPTIMIZE_INSTRUCTIONS` constant exists in `deduplicate_levers.py` despite four confirmed failure modes.
6. **I2/I3**: No post-deduplication validation (zero-reduction check) or chain-absorption detection.

The most actionable near-term fix is I1 (add `OPTIMIZE_INSTRUCTIONS` to document the failure modes) combined with I4 (narrow the safety valve). B1 and B2 in `runner.py` should also be fixed to prevent misleading events in the analysis pipeline.
