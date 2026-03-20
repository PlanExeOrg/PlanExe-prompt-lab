# Code Review (claude)

Reviewed files:
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`

PR under review: #365 — *feat: consolidate deduplicate_levers — classification, safety valve, B3 fix*

---

## Bugs Found

### B1 — `user_prompt` stores levers JSON, not project context (`deduplicate_levers.py:295`)

```python
return cls(
    user_prompt=levers_json,   # ← levers JSON, NOT project_context
    system_prompt=system_prompt,
    ...
)
```

The `project_context` argument (the actual plan description) is passed in but never stored in the dataclass. Instead, `levers_json` (the serialized input levers) is stored under the `user_prompt` key. Anyone reading the saved output JSON (e.g., analysis scripts inspecting `user_prompt`) sees lever data, not the prompt that motivated the run. The `project_context` is only embedded deep inside the concatenated system message.

This creates a misleading output schema and makes it impossible to reconstruct the original context from the saved file alone. All other pipeline steps store the actual user prompt in `user_prompt`.

**Fix**: change line 295 to `user_prompt=project_context`.

---

### B2 — Safety valve instruction maps "primary" to the uncertain-fallback case (`deduplicate_levers.py:135`)

```
Use "primary" only as a last resort — if you genuinely cannot determine
a lever's strategic role after reading the full context. Describe what is
unclear in the justification.
```

This instruction has two problems:

1. **Semantic inversion**: the phrase "if you genuinely cannot determine a lever's strategic role" maps "primary" to the *uncertain* case. A model reading this literally will assign "primary" whenever it is confused, because "primary" is the stated last resort for uncertainty. The intended behaviour is the opposite: only use "primary" for levers you have *positively confirmed* are essential. The uncertain-fallback should be "secondary" (keep it, but don't elevate it).

2. **Wrong fallback direction**: the code-level fallback at line 249 also defaults failed classifications to `primary` ("Classification failed after retries. Keeping this lever to avoid data loss."), compounding the prompt's message that "when in doubt, use primary."

Combined, the prompt instruction and the code fallback both point in the same wrong direction: uncertainty → primary. This is a plausible contributing cause of gpt-4o-mini's blanket-primary failure (N1 in insights).

**Fix**: rephrase to "Only use 'primary' for levers you have actively confirmed are essential strategic decisions. If genuinely uncertain whether a lever is primary vs. secondary, assign 'secondary'."

Also consider changing the code fallback at line 249 from `primary` to `secondary`.

---

### B3 — Calibration hint hard-codes 15 levers; current runs have 18 (`deduplicate_levers.py:137`)

```
In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed.
```

Runs 22–28 feed 18 input levers to this step (up from 15 in runs 15–21). A model that treats "expect 4–10" as a hard cap will stop absorbing once it reaches 10, even though 4–6 further candidates remain in an 18-lever set. The "do not stop early" clause is present but is weaker than a numeric target.

This is the calibration-capping failure mode documented in OPTIMIZE_INSTRUCTIONS. The PR widened the range from "4-8" to "4-10" to fix gemini's under-absorption on 18-lever sets, but the example count ("15 levers") was not updated to match the actual input size.

The resulting ceiling (10 absorbs from 18 inputs = 56%) may be too low for plans with genuine semantic overlap. gpt-5-nano absorbed 10 out of 18 on sovereign_identity (hitting the ceiling) and haiku absorbed 6 — so models are reaching the upper bound.

**Fix**: either (a) make the calibration adaptive ("from N levers, expect 20–55% absorbed or removed"), or (b) update the example to "In a well-formed set of 15–20 levers, expect 4–10 (or more) to be absorbed or removed."

---

### B4 — `calls_succeeded` in `_run_deduplicate` masks partial failures (`runner.py:155`)

```python
return PlanResult(
    name=plan_name,
    status="ok",
    duration_seconds=0,
    calls_succeeded=len(result.response),
)
```

`result.response` always contains one `LeverDecision` per input lever — including levers that failed LLM classification and fell back to the default `"primary"` (code at `deduplicate_levers.py:249`). So `calls_succeeded` is always equal to `len(input_levers)` regardless of how many classifications came from real LLM responses vs. the fallback. Silent partial failures are invisible in the `outputs.jsonl` record.

Compare: `_run_levers` at line 120 correctly uses `len(result.responses)` (number of successful LLM calls), which can be less than the attempt count.

**Fix**: track how many levers fell back to the default in `DeduplicateLevers` and expose that count so `_run_deduplicate` can report it accurately. Or at minimum document the current limitation in a comment.

---

## Suspect Patterns

### S1 — Absorb-target ID lives in freeform justification text, not a structured field (`deduplicate_levers.py:63-74`)

```python
justification: str = Field(
    description="A concise justification (~80 words). If absorbing, state which lever id it merges into."
)
```

When a model classifies a lever as `absorb`, the target lever ID is embedded in the freeform `justification` string. There is no dedicated `absorb_target_id: Optional[str]` field. This means the code cannot:

- Verify that the target lever ID actually exists in the input set
- Detect chain absorptions (A→B→C where B is itself absorbed) — documented as a known failure mode in OPTIMIZE_INSTRUCTIONS
- Check that the target lever is being kept (primary/secondary), not itself discarded

All three failure modes are silent at runtime. Chain absorptions are particularly harmful because detail from intermediary levers is silently lost.

**Fix**: add `absorb_target_id: Optional[str]` to `LeverClassificationDecision`. After the classification loop, scan for chain absorptions and log a warning.

---

### S2 — `_build_compact_history` produces orphaned header when prior_decisions is empty (`deduplicate_levers.py:102-111`)

```python
summary = "\n".join(
    f"- [{d.lever_id}] ..."
    for d in prior_decisions
)
return [
    ChatMessage(role=MessageRole.SYSTEM, content=(
        f"{system_message_with_context}\n\n"
        f"**Prior decisions (compacted):**\n{summary}"
    )),
]
```

If compaction is triggered on the very first lever (i.e., `prior_decisions` is empty), `summary` is an empty string, and the system message ends with `"**Prior decisions (compacted):**\n"` — a hanging header with no content. This is cosmetically odd and might confuse models that expect a non-empty list after a header. It is only triggered during error recovery on the first lever, so it's a rare edge case.

**Fix**: guard with `if prior_decisions:` to omit the section entirely when empty, or add a `"(none yet)"` placeholder line.

---

### S3 — `check_review_format` enforces a 10-char minimum but no maximum (`identify_potential_levers.py:173`)

```python
if len(v) < 10:
    raise ValueError(f"review_lever is too short ({len(v)} chars); expected at least 10")
```

The system prompt says "Keep each `review_lever` to one sentence (20–40 words)." OPTIMIZE_INSTRUCTIONS documents "Verbosity amplification" as a known failure mode. But the validator only enforces a 10-char floor with no ceiling. A model that generates a 400-word `review_lever` passes validation.

This is not a crash bug, but it means the verbosity constraint is only advisory (in the prompt) and never enforced in code.

---

### S4 — `all_levers_summary` truncates consequences at 120 chars (`deduplicate_levers.py:178-180`)

```python
all_levers_summary = "\n".join(
    f"- [{lever.lever_id}] {lever.name}: {lever.consequences[:120]}..."
    for lever in input_levers
)
```

The model uses this summary to decide whether one lever overlaps another. For levers with similar names but different scopes (e.g., "Procurement Language Specificity" vs "Procurement Conditionality"), the 120-char truncation may drop the distinguishing detail. This could contribute to hierarchy-direction errors (N3 in insights) — models see truncated consequences and can't reliably judge which lever is more general.

The full lever is provided in the USER message for the lever being classified, but comparison levers (all other levers) are only available in truncated form.

---

### S5 — `partial_recovery` event only emitted for `identify_potential_levers`, not `deduplicate_levers` (`runner.py:546-552`)

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ...)
```

The `deduplicate_levers` step also has partial-failure semantics (levers that fall back to `primary` after two failed LLM calls), but no analogous event is emitted. This gap means degraded deduplication runs are not flagged in `events.jsonl`.

---

## Improvement Opportunities

### I1 — Add a worked absorb example to the system prompt (addresses N1 and N3)

Insight hypothesis H1/H2: adding concrete examples of the correct absorb direction would reduce both gpt-4o-mini's zero-absorb rate and hierarchy-direction errors in gpt-5-nano/qwen3. Secondary examples were added in PR #365 and demonstrably helped; the same pattern should apply to absorb examples. A minimal addition:

```
Example absorb: "Procurement Conditionality" (enforcing requirements via contract clauses)
absorbs INTO "Procurement Language Specificity" (what procurement documents say), because
conditionality is one specific mechanism within the broader category of procurement language.
The reverse direction — absorbing language into conditionality — would be wrong hierarchy.
```

Evidence: 3/7 models in runs 22–28 show hierarchy-direction errors on this exact lever pair.

---

### I2 — Add post-loop zero-absorb detection and warning

After the classification loop, if `absorb_count == 0` and `len(input_levers) > 10`, log a warning and optionally emit a `"zero_absorbs_detected"` event. The prompt already says "If you find zero absorb/remove decisions, reconsider" but models ignore this self-correction instruction. A code-level warning would make the failure visible in `events.jsonl` without requiring a retry.

This is a non-invasive guard that addresses C2 from the insight file.

---

### I3 — Add cross-domain absorption failure mode to OPTIMIZE_INSTRUCTIONS

`OPTIMIZE_INSTRUCTIONS` in `deduplicate_levers.py` documents 5 failure modes. Insight evidence (N2) shows a 6th: llama3.1 absorbs levers into semantically unrelated targets (procurement → certification, demonstrators → fallback authentication). This should be documented as:

```
- Cross-domain absorption. A model absorbs a lever into a target from a
  completely unrelated domain (e.g., procurement levers absorbed into
  technical certification levers). The current absorb-target validation
  is absent at the code level; models like llama3.1 exhibit this pattern
  on sovereign_identity inputs.
```

---

### I4 — `deduplication_justification` required field in `enrich_potential_levers.InputLever` (`enrich_potential_levers.py:40`)

```python
class InputLever(BaseModel):
    classification: Optional[str] = None       # optional ✓
    deduplication_justification: str            # required — no default
```

The `classification` field was correctly made optional (backwards-compatible). But `deduplication_justification` has no default. If `enrich_potential_levers` is called with levers from `identify_potential_levers` (bypassing the deduplicate step, e.g., in testing), `InputLever(**lever)` will raise a `ValidationError`. The backwards-compatibility guarantee in the PR description is therefore partial.

**Fix**: `deduplication_justification: str = ""` to make the enrich step graceful when the deduplicate step is skipped.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| N1 — gpt-4o-mini blanket-primary failure (0 absorbs from 18 levers) | B2: "Use primary only as a last resort — if you cannot determine" maps primary to the uncertain-fallback. Code fallback at `deduplicate_levers.py:249` also defaults to primary. Combined, uncertainty → primary is the reinforced path. |
| N3 — Hierarchy-direction violations (gpt-5-nano, qwen3: Procurement Language Specificity absorbed INTO Conditionality, wrong direction) | S4: `all_levers_summary` truncates consequences at 120 chars, depriving the model of the context needed to judge generality. I1: no worked example demonstrates the correct absorb direction for these levers. |
| N4 — Wide inter-model variance in absorb count (0–10 from 18 inputs) | B3: calibration hint says "15 levers, expect 4-10" but inputs have 18 levers; the upper bound is hit at 56% absorption, leaving genuine duplicates unprocessed for aggressive models, while conservative ones ignore the hint entirely. |
| N5 — Input lever count changed between before/after runs (confound for PR evaluation) | B3: same cause — the calibration hint was not updated to reflect the new input size. |
| Insight P6 — B3 bug fix confirmed (no truncation artifacts) | B3 bug (the conditional `...` fix) is confirmed present in both `_build_compact_history` (line 103) and `all_levers_summary` (line 179). |

---

## PR Review

### What the PR claims to fix and what was actually delivered

**1. primary/secondary classification** — delivered. The `LeverClassification` enum and `OutputLever.classification` field are present and correct. Downstream, `enrich_potential_levers.InputLever.classification: Optional[str] = None` is correctly optional.

**2. Safety valve "Use primary only as a last resort" + calibration hint "expect 4-10"** — partially delivered. The calibration was widened from "4-8" to "4-10" (confirmed benefit for gemini, P2 in insights). However, the safety valve wording has the semantic inversion identified as B2 above. The "expect 4-10" range is tied to a 15-lever example while inputs have grown to 18 levers (B3 above).

**3. "do not stop early" instruction** — delivered. Present at `deduplicate_levers.py:137`.

**4. Concrete secondary examples** — delivered. Marketing timing, reporting cadence, communication tooling, documentation formatting are in the system prompt (line 125).

**5. B3 bug fix: conditional `...` in both `_build_compact_history` AND `all_levers_summary`** — fully delivered. Both locations now have `{'...' if len(...) > N else ''}`. This is the clearest mechanical fix in the PR.

**6. OPTIMIZE_INSTRUCTIONS with 5 documented failure modes** — delivered. The 5 modes are present. The cross-domain absorption pattern (llama3.1 absorbing procurement levers into technical certification levers) is a 6th failure mode discovered in runs 22-28 that should be added (I3).

**7. self_improve runner support for deduplicate_levers step** — delivered. `runner.py` has `_run_deduplicate`, `_DEDUPLICATE_INPUT_FILES`, `_DEDUPLICATE_LEVERS_FILE`, and "deduplicate_levers" in `SUPPORTED_STEPS`. The implementation is functional.

**8. enrich_potential_levers accepts optional `classification` field** — partially delivered. The `classification` field is optional (correct), but `deduplication_justification` is still required, limiting backwards-compatibility (I4).

### Gaps and new issues introduced

- **gpt-4o-mini blanket-primary failure (N1) not addressed**: the PR's intended fix is the safety valve + calibration hint, but as noted in B2, the safety valve wording may be reinforcing the failure rather than correcting it. This was the primary documented failure mode in OPTIMIZE_INSTRUCTIONS before the PR.
- **Hierarchy-direction errors (N3) not addressed**: no worked absorb example exists; 3/7 models still make direction errors.
- **`user_prompt` naming confusion (B1)**: the stored `user_prompt` field contains levers JSON, not the project context. This predates the PR but was not fixed.
- **`calls_succeeded` masking (B4)**: introduced by the PR's `_run_deduplicate` implementation. The identify step correctly measures real call count; the deduplicate step always reports input lever count regardless of fallbacks.

---

## Summary

The PR delivers its mechanical claims cleanly: B3 `...` truncation is fixed in both places, the self_improve runner supports the new step, and the enrich step accepts the new `classification` field. Gemini's calibration regression is measurably resolved (P2 in insights).

The highest-priority remaining issue is **B2**: the safety valve instruction "Use primary only as a last resort — if you genuinely cannot determine a lever's strategic role" semantically maps primary to the *uncertain* fallback, which is the opposite of the intended behaviour. Combined with the code-level fallback at `deduplicate_levers.py:249` also defaulting to primary, uncertainty → primary is doubly reinforced. This is the most likely root cause of gpt-4o-mini's blanket-primary failure, which is the most impactful unresolved quality problem.

The second priority is **B3**: the calibration hint references a 15-lever set while current inputs have 18 levers, causing the upper bound of "4-10 absorbs" to be reached before all genuinely duplicate levers are processed.

**B1** (user_prompt stores levers JSON) and **B4** (calls_succeeded masking partial failures) are lower-severity naming/reporting issues that should be cleaned up but don't affect output quality.
