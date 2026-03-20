# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/deduplicate_levers.py`
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `self_improve/runner.py`

PR reviewed: #365 — feat: consolidate deduplicate_levers — classification, safety valve, B3 fix

---

## Bugs Found

### B1 — No self-referential absorb detection (`deduplicate_levers.py:236–262`)

When an LLM returns `classification="absorb"` with a justification that references the current lever's own ID (i.e., "Absorb into [f1c0d856]" for lever `f1c0d856`), the code has no guard. The decision is accepted as-is, appended to `decisions`, and the lever is then silently dropped from `deduplicated_levers` at line 281:

```python
if lever_decision.classification not in keep_classifications:
    continue
```

Net effect: the lever disappears from the output for no valid reason. The LLM has effectively told the system to discard the lever into itself, and the code complies. Observed in gpt-5-nano run 17 (insight N4): lever `f1c0d856` justification reads "Absorb into [f1c0d856]".

No fix is attempted despite the code already defaulting to `primary` for other failure modes (lines 247–256).

### B2 — Compact history truncates absorb-target UUIDs (`deduplicate_levers.py:102–103`)

`_build_compact_history` truncates each decision's justification to 80 characters:

```python
f"- [{d.lever_id}] {d.classification}: {d.justification[:80]}{'...' if len(d.justification) > 80 else ''}"
```

A justification like `"This duplicates lever a02b023d-1234-5678-9012-345678901234 which covers the broader strategic approach"` contains a 36-character UUID. Depending on preamble length, the UUID can be cut at an arbitrary character, leaving the model with a partial UUID in the compacted history (e.g., `"a02b023d-12"`). On a retry call, the LLM sees partial IDs in the prior-decisions summary and may produce incoherent follow-on absorb decisions for subsequent levers.

This only fires on the retry path (first call failed), but the retry path is precisely when the conversation is already corrupted — making the truncation more likely to matter, not less.

### B3 — `calls_succeeded` semantics differ between steps (`runner.py:120` vs `runner.py:155`)

`_run_levers` (line 120) sets:
```python
calls_succeeded=len(result.responses)   # number of LLM API calls, typically 2–3
```

`_run_deduplicate` (line 155) sets:
```python
calls_succeeded=len(result.response)    # number of lever decisions, typically 15
```

These measure different things. The field name implies LLM call count in both cases (matching the intent of the `partial_recovery` event). While the `partial_recovery` check at lines 546–552 is guarded by `step == "identify_potential_levers"` so there is no immediate functional impact, the mismatch is a latent bug: any future code that reads `calls_succeeded` for the deduplicate step will interpret 15 as "15 LLM calls succeeded", which is wrong (it's 1 batched conversation with 15 per-lever turns).

---

## Suspect Patterns

### S1 — "Use primary only as a last resort" semantics are inverted (`deduplicate_levers.py:135`)

```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's
strategic role after reading the full context.
```

Read literally, this says `primary` is an exceptional fallback. In reality, most kept levers should be `primary`. The intent is: "don't lazily default every lever to `primary`; genuinely consider whether it is `secondary` before labeling it `primary`." The current wording could cause instruction-following models to under-classify as primary and over-use secondary or absorb. Empirically, this wording improved haiku and gpt-4o-mini (P2, P3), but its long-term effect on models with stronger literal interpretation is unpredictable.

### S2 — No absorb-target ID validation (`deduplicate_levers.py:258–262`)

When `classification == "absorb"`, the justification text is recorded as-is with no extraction or validation of the target lever ID. The code never checks:
- whether the target ID appears in the input lever list
- whether the target ID is the current lever's own ID (see B1)
- whether a circular absorb pair (A→B and B→A) exists

Because the absorb target exists only in free-text justification, chain resolution and hierarchy enforcement cannot be done without parsing it.

### S3 — English-only prohibition in `consequences` field description (`identify_potential_levers.py:118–119`)

```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"
```

This English-specific prohibition is inside a Pydantic field description that is serialised into the JSON schema sent to the LLM. `OPTIMIZE_INSTRUCTIONS` explicitly warns against this pattern ("Fragile English-only validation — PlanExe receives initial prompts in many non-English languages"). A Chinese or Japanese model responding in the prompt's language will never produce the string "Controls" or "Weakness:", so the prohibition is vacuous for non-English responses. But more importantly, it is inconsistent with the corrected structural validator at lines 161–177 which is explicitly language-agnostic. The field description still references the old English pattern it documents as known-bad.

### S4 — `review_lever` description references prompt section number (`identify_potential_levers.py:130`)

```python
"See system prompt section 4 for examples."
```

This hard-codes a section number. If the system prompt sections are reordered or merged, this reference silently becomes stale. Models that read it will look for a "section 4" that no longer exists or refers to something different.

---

## Improvement Opportunities

### I1 — Post-process self-referential absorb decisions (`deduplicate_levers.py:258–262`)

After obtaining `decision`, add a guard:
```python
if decision.classification == "absorb" and lever.lever_id in decision.justification:
    # LLM produced a self-referential absorb — treat as primary instead
    decision = LeverClassificationDecision(
        classification="primary",
        justification="Self-referential absorb detected; re-classified as primary."
    )
```
This directly fixes B1 and is consistent with the existing fallback pattern at lines 247–256.

### I2 — Hierarchy-aware instance selection in deduplication result (`deduplicate_levers.py:266–293`)

Currently the code keeps whichever lever the LLM labels `primary` (or `secondary`), and discards the one labeled `absorb`. When the LLM incorrectly absorbs a first-batch (general) lever into a second-batch (specific) lever, the code retains the second-batch instance — violating the hierarchy instruction. A position-based tie-breaker is possible: if a lever marked `absorb` has a lower index in `input_levers` than the lever it is absorbed into, swap the decision (keep the lower-index lever and discard the higher-index one). This does not require parsing the absorb-target from the justification text — it only requires knowing which lever the LLM absorbed and which one it kept (both are available from `decisions`). Insight C1 describes this approach.

### I3 — Chain-absorption detection (`deduplicate_levers.py:264–293`)

`OPTIMIZE_INSTRUCTIONS` explicitly documents "Chain absorption" as a known failure mode: lever A absorbs into B, B absorbs into C, only C survives. The current code does not detect or warn about this. Adding a post-processing pass over `decisions` to flag cases where an absorb target is itself marked `absorb` would at minimum surface the problem in logs. The flagged chain could fall back to retaining A as `primary` to avoid data loss.

### I4 — Decouple the numeric calibration range from the system prompt (`deduplicate_levers.py:137`)

The single range `"4–10"` fixed Gemini but caused Qwen to over-absorb (insight N3). A static range cannot simultaneously serve models that under-absorb (Gemini before this fix) and models that over-absorb (Qwen after this fix). The numeric range was added to fix llama3.1's blanket-primary failure; it then calibration-capped Gemini at "4–8"; widening to "4–10" now puts pressure on Qwen. Consider replacing the numeric range with purely qualitative guidance:

```
If you find zero absorb/remove decisions, reconsider: the input almost always contains
near-duplicates. Do not keep every lever. Do not stop early.
```

This removes the model-specific numeric signal while preserving the intent.

### I5 — Add `save_clean` call in `_run_deduplicate` (`runner.py:137–156`)

`_run_levers` writes both a raw JSON (with metadata) and a clean JSON (flat lever list). `_run_deduplicate` only writes the raw JSON. While the raw file's `deduplicated_levers` key contains the clean data, omitting the clean file means any consumer that expects a flat deduplicated-levers file at a known path will silently not find it. For consistency and downstream safety, `_run_deduplicate` should also call `result.save_clean(...)`.

### I6 — `LeverClassification` enum is defined but `LeverDecision` uses `Literal` (`deduplicate_levers.py:55–79`)

`LeverClassification` (lines 55–59) is a `str, Enum`. `LeverDecision.classification` (line 78) uses `Literal["primary", "secondary", "absorb", "remove"]` instead of the enum. Both coexist for the same domain values. The `keep_classifications` set at line 265 uses the enum constants. Because `LeverClassification` is a `str` subclass, `LeverClassification.primary == "primary"` and the `in` check at line 281 works correctly — no functional bug. But maintaining two parallel type representations for the same values is unnecessary complexity.

---

## Trace to Insight Findings

| Insight Observation | Root Code Cause |
|---------------------|-----------------|
| **N4** — gpt-5-nano self-referential absorb: lever `f1c0d856` justification "Absorb into [f1c0d856]", lever lost from output | **B1** — no self-referential absorb guard in `deduplicate_levers.py:258–262` |
| **N2** — Hierarchy-direction violations persist (general absorbs into specific, wrong instance kept) | **S2** — no absorb-target validation or hierarchy-aware tie-breaking in `deduplicate_levers.py:266–293` |
| **N3** — Qwen3-30b over-collapse on sovereign_identity (5→3) after calibration hint widened to "4–10" | **I4** — numeric calibration hint creates model-specific pressure in `deduplicate_levers.py:137` |
| **N4** — gpt-5-nano meta-commentary leaking into justification fields | Structural: no post-processing sanitisation of justification text. Not a code bug per se — the LLM is producing malformed output the schema cannot reject |
| **N1** — "secondary" adoption is patchy (only 3 of 7 models use it) | **S1** — "last resort" wording for primary is semantically inverted, may confuse weaker models |
| **N5** — Fabricated percentage claims in consequences field pass through unchanged | No fabrication validator in `identify_potential_levers.py:147–159`; the `check_option_count` and `check_review_format` validators exist but none check for `\d+%` patterns in consequences |
| **P5/P6** — B3 fix confirmed, compact history conditional `...` works | `deduplicate_levers.py:103` and `179` both correctly use the conditional; fix is complete |

---

## PR Review

### What the PR claims to fix and whether the code matches

**1. Gemini calibration-capping fix (widened "4–8" → "4–10" + "do not stop early")**

Confirmed implemented at `deduplicate_levers.py:137`. The `DEDUPLICATE_SYSTEM_PROMPT` now reads:
```
expect 4–10 to be absorbed or removed. Plans with many near-duplicate names may require
10 or more absorbs — do not stop early.
```
This directly matches the PR claim and is confirmed effective by the analysis (Gemini: 9→5 kept on sovereign_identity). However, see **I4** — the numeric range creates opposite pressure for Qwen (N3 regression).

**2. primary/secondary classification**

`LeverClassification.secondary` added at line 57. `LeverClassificationDecision` and `OutputLever` updated. System prompt examples added. Correctly implemented. The `keep_classifications` set at line 265 now includes `secondary`, so these levers correctly survive deduplication.

**3. B3 fix — conditional `...` in `all_levers_summary`**

Confirmed at `deduplicate_levers.py:179`:
```python
f"{'...' if len(lever.consequences) > 120 else ''}"
```
The companion fix in `_build_compact_history` at line 103 was already present (PR #364). Both conditional truncations are now in place.

**4. deduplicate_levers step in self_improve runner**

The `_run_deduplicate` function was added at `runner.py:137–156`. It correctly loads the levers JSON, runs `DeduplicateLevers.execute`, and writes the raw output. However:
- It does not call `save_clean` (see **I5**).
- `calls_succeeded=len(result.response)` counts lever decisions (15) not LLM calls (see **B3**).

**5. enrich_potential_levers accepts optional `classification`**

`enrich_potential_levers.py:39` — `classification: Optional[str] = None`. Correctly added with a default, making it backwards-compatible with old data lacking this field.

### Gaps and edge cases the PR misses

**Gap 1 — Self-referential absorb not guarded (B1)**: The PR adds a `secondary` classification that makes the schema more complex and expands the LLM's classification space. More classification options increase the probability of malformed decisions (gpt-5-nano already exhibited self-referential absorbs before this PR). The PR does not add any absorb-target validation.

**Gap 2 — No circular absorb detection**: Adding `secondary` alongside `absorb` means the LLM now has four choices, increasing the risk of decision-pair conflicts (A absorbs B, B absorbs A). This pair is not detected.

**Gap 3 — "last resort" phrasing is semantically inverted (S1)**: The intent is "don't default to primary lazily"; the wording says "primary is a last resort". This has worked for haiku and gpt-4o-mini (P2, P3) but is not clearly correct English semantics. A future model update may interpret it literally.

**Gap 4 — Secondary examples are domain-narrow**: The concrete secondary examples — "marketing campaign timing, internal reporting cadence, team communication tooling, documentation formatting standards" — are all operational/process levers from a corporate context. For non-corporate plans (e.g., sovereign_identity, hong_kong_game), these examples provide weak signal because they don't map onto those domains. Models that lack strong instruction-following (Gemini, llama3.1, qwen3) fail to use `secondary` at all on sovereign_identity, partly because the examples don't resemble any sovereign_identity lever.

---

## Summary

The PR successfully addresses its primary target: Gemini's calibration-capping on sovereign_identity is fixed (9→5 kept levers). The B3 fix (`all_levers_summary` conditional truncation) is correctly implemented. The `secondary` classification feature works for instruction-following models (haiku, gpt-4o-mini). The runner now supports the deduplicate step.

**Confirmed bugs**:
- **B1**: Self-referential absorb decisions are not detected; the lever is silently dropped. Observed in gpt-5-nano run 17. (`deduplicate_levers.py:258–262`)
- **B2**: `_build_compact_history` truncates justifications to 80 chars, cutting UUID absorb-target references. (`deduplicate_levers.py:103`)
- **B3**: `calls_succeeded` in `_run_deduplicate` counts lever decisions (15) rather than LLM API calls. (`runner.py:155`)

**Most impactful improvements**:
- **I1**: Guard self-referential absorbs immediately after decision is obtained — one-line fix.
- **I2**: Hierarchy-aware tie-breaking to keep the earlier-batch lever when direction is wrong.
- **I3**: Chain-absorption detection to prevent data loss from multi-hop absorb chains.
- **I4**: Replace the numeric calibration range ("4–10") with qualitative guidance to avoid model-specific pressure (Qwen regression, N3).
