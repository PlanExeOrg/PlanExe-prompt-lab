# Assessment: Enable retry config in prompt optimizer runner (PR #283)

## Issue Resolution

**What the PR was supposed to fix:** PR #283 adds `RetryConfig()` to `LLMExecutor` in
`prompt_optimizer/runner.py` so transient LLM API or network failures get up to 2 retries with
exponential backoff.

**Is the issue resolved?** Partially, in a theoretical sense only. No transient network failures
were observed in runs 81–87. The three failures that did occur are all structural:

| Run | Plan | Error | Would retries help? |
|-----|------|-------|---------------------|
| 81 (nemotron) | All 5 | `Could not extract json string from output: ` | No — model cannot produce JSON at all |
| 83 (gpt-oss-20b) | parasomnia | `EOF while parsing a list at line 36` | Possibly — if truncation is non-deterministic |
| 87 (claude-haiku) | gta_game | `List should have at most 7 items after validation, not 8` | No — model behavior, not transient |

The retry config fires on the same model with the same prompt, so none of the structural failure
classes (empty JSON, context truncation, schema count violation) become recoverable through
repetition. The 7/35 failure total is unchanged vs the 7/35 total in runs 74–80 (both batches are
80% success rate overall).

**Residual symptoms:** None directly attributable to PR #283. The batch runs cleanly.

**Important context:** The quality improvement visible in batch 11 (runs 81–87) relative to batch 10
(runs 74–80) is **primarily due to PR #282** (which reverted the keyword quality gate), not PR #283.
Notably, qwen3-30b went from 15 levers (60 silently discarded by the gate) to 78 levers — this is
PR #282's effect. PR #283 adds infrastructure only; it does not change any output.

---

## Quality Comparison

**Scope note:** Analysis/10 (runs 74–80) has no insight or code-review files — that round was
intentionally skipped after the keyword gate disaster. "Before" metrics come from
`analysis/10_identify_potential_levers/assessment.md` only. Entries marked `—` were not measured
for the before batch. All shared models (all 7) appear in both batches.

| Metric | Before (runs 74–80) | After (runs 81–87) | Verdict |
|--------|---------------------|--------------------|---------|
| **Overall success rate** | 28/35 (80%) | 28/35 (80%) | UNCHANGED |
| — nemotron | 0/5 | 0/5 | UNCHANGED |
| — llama3.1 | 5/5 | 5/5 | UNCHANGED |
| — gpt-oss-20b | 5/5 | 4/5 (1 EOF failure) | REGRESSED |
| — gpt-5-nano | 5/5 | 5/5 | UNCHANGED |
| — qwen3-30b | 5/5 | 5/5 | UNCHANGED |
| — gpt-4o-mini | 5/5 | 5/5 | UNCHANGED |
| — haiku | 3/5 (2 schema failures) | 4/5 (1 schema failure) | IMPROVED (noise) |
| **Total lever yield** | 439 (qwen3: 15 due to gate) | 497 (qwen3: 78, gate removed) | IMPROVED (PR #282) |
| **qwen3-30b lever yield** | 15 (60 filtered by keyword gate) | 78 (no gate) | IMPROVED (PR #282) |
| **Bracket placeholder leakage** | 0 (same prompt_2) | 0 (confirmed, all runs) | UNCHANGED |
| **Option count violations** | 0 (schema enforced) | 0 (schema enforced) | UNCHANGED |
| **Lever name uniqueness** | — not measured | 100% exact-unique for runs 82–87; 0 exact duplicates across plans for runs 83–87 (vs 22 in baseline) | N/A (no before baseline) |
| **Template leakage — Strategy suffix** | 2–10% per run (prompt_2 working) | Not separately measured; generic suffixes (Strategy/Framework/Protocol): 9–28 per run | UNCHANGED (same prompt) |
| **Review format compliance** (`Controls X vs Y`) | — not measured | 0 violations for runs 83–87; 10/86 missing in run 82 | N/A |
| **Consequence chain format** (`Immediate→Systemic→Strategic`) | — not measured | Present in all runs; run 82 lacks measurable indicators (57/86 missing systemic clause) | N/A |
| **Content depth (avg consequence chars)** | — not measured at scale; run 75 (llama3.1) silo sample ~160–220 chars with quantitative content | Run 82 (llama3.1): ~146; run 83: ~329; run 84: ~414; run 85: ~376; run 86: ~255; run 87: ~948 | N/A (no before baseline) |
| **qwen3-30b consequence contamination** | Hidden by keyword gate (gate discarded contaminated levers) | 56/78 (72%) consequences contain review text in `consequences` field | REGRESSED (was hidden) |
| **Cross-call duplication (exact names)** | — not measured | 0 for runs 83–87; 13 exact duplicates for run 82 | N/A |

**Evidence for qwen3 comparison:** `history/0/78_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
is `[]` (empty — gate filtered everything). `history/0/85_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
has 15 levers with measurable consequences but the `consequences` field for lever 1 ends with
`"Controls efficiency vs. equity. Weakness: ..."` — identical to the `review` field. The
contamination was always present; the gate was silently discarding it rather than fixing it.

**Evidence for haiku variance:** Run 80 (before) failed on `silo` and `hong_kong_game` with
`List should have at most 7 items after validation, not 8` (same as run 87's gta_game failure).
The 3/5 → 4/5 change is within natural model variance for which specific plans trigger the
over-generation behaviour, not evidence of retry benefit.

---

## New Issues

### 1. qwen3-30b field contamination now fully exposed

The keyword gate in PR #281 was inadvertently masking a pre-existing failure mode: qwen3-30b
appends review text (`Controls ... vs. ... Weakness: ...`) directly inside the `consequences` field.
The gate was filtering these out (treating "Controls" as a contamination signal), which coincidentally
produced correct-looking but nearly-empty output (15 levers instead of 75+). With the gate removed,
the contaminated levers now reach `002-10-potential_levers.json`. Scale: 56/78 (72%) of qwen3-30b
consequences are contaminated across all 5 training plans. This is a pre-existing prompt compliance
failure, not introduced by PR #283, but is newly visible.

### 2. No new issues from the PR itself

PR #283's changes are additive and passive — retry config wraps existing execution, does not modify
output generation, parsing, or validation. No new failure modes were introduced.

### 3. Latent race condition remains unaddressed

Both code reviews (code_claude B1, code_codex S3) confirm a race condition on the module-level
`set_usage_metrics_path` global at `runner.py:106`. It runs outside `_file_lock` while
`IdentifyPotentialLevers.execute()` at line 114 also runs outside the lock. With `workers > 1`,
this corrupts per-plan usage metrics files. PR #283 does not fix this. The runs in this batch
used `workers=1` so no corruption is visible, but the bug remains latent.

---

## Verdict

**YES**: PR #283 is correct, low-risk defensive infrastructure. It adds retry capability for
transient API/network faults that are plausible in production even if absent in this batch.
The retry config imposes no downside on the current failure modes — structural failures exhaust
their 2 retries quickly (same error, same result) without changing observed success rates.
The batch data confirms that the prompt_2 + no-keyword-gate baseline established by PR #282
is clean and measurable.

---

## Recommendations

### Next iteration focus

The synthesis for analysis/11 ranks five directions by evidence and effort. The top-priority
next change is **direction 1: truncate over-limit lever lists to 7 instead of hard-failing**
(synthesis §1, code_claude B3/I1, code_codex B3). This is:
- A deterministic code fix (not probabilistic like prompt changes)
- ~5–8 lines in `identify_potential_levers.py` (catch `ValidationError` on "List should have at
  most N items", slice levers to 7, re-validate)
- Directly recovers run 87's `gta_game` and run 80's `silo` and `hong_kong_game` failure class
- Zero risk: discards one extra lever per call rather than failing the entire plan

This is the planned **iteration 2** fix after the memory entry "fix assistant turn serialization"
is addressed. However, since the lever-truncation fix is simpler and higher-confidence, it should
be pursued first.

### Issues resolved — remove from backlog

- **Keyword gate disaster (PR #281 / iteration 10)**: Fully resolved by PR #282 (reverted). The
  keyword-gate concept is closed. Any future quality gate must use language-agnostic checks only.
- **Strategy suffix inflation**: Confirmed fixed by prompt_2 (2–10% in batch 10, same prompt in
  batch 11 shows continued compliance). No further action needed on naming template.

### New issues to add to backlog

1. **qwen3-30b consequence contamination (run 85 class)**: 56/78 (72%) `consequences` fields
   contain `Controls ... Weakness: ...` text that belongs only in `review_lever`. Root cause:
   prompt's current prohibition (`"Do NOT include 'Controls ... vs.'"`) is insufficient for this
   model. Fix: add a concrete negative example to the prompt (synthesis direction 2). Priority: High.

2. **Content validation absent before `save_clean` (code_claude S4, code_codex B1)**: Schema-valid
   but semantically broken levers (run 82's one-word options, run 85's contaminated consequences,
   run 86's missing trade-off markers) pass through to `002-10-potential_levers.json` as if
   successful. Fix: add post-generation content checks (synthesis direction 4). Priority: Medium.

3. **Assistant turn threading not implemented (code_claude S1, code_codex S1)**: LLM calls 2 and 3
   start fresh with only a name deny-list. Weaker models reproduce concept-identical levers under
   different names (run 82 has 13 duplicate exact names; run 82's levers are conceptually formulaic
   across all 3 calls). Fix: include prior `ChatMessage(role=ASSISTANT, ...)` in call 2 and call 3
   messages. Planned as iteration 2. Priority: High.

4. **Race condition on `set_usage_metrics_path` (code_claude B1, code_codex S3)**: Latent in
   single-worker runs, will corrupt metrics when `workers > 1` is enabled. Fix: move
   `set_usage_metrics_path` inside `_file_lock` or switch to thread-local storage. Priority: Medium
   (blocks future parallel experiments).

5. **Failed raw artifacts discarded (code_claude B2/I3, code_codex B4)**: Runs 81, 83, and 87
   leave empty `outputs/` directories with only a terminal error string in `outputs.jsonl`. No
   raw model text, no partial levers from prior calls. Fix: save partial `responses` to
   `002-9-potential_levers_raw_partial.json` in `except` block; move
   `track_activity_path.unlink()` to success branch only. Priority: Low (analysis quality).
