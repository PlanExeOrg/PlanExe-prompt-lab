# Assessment: Adaptive batch size, guarded retry, and max_tokens bump for enrich step

## Issue Resolution

**What the PR was supposed to fix** (from `pr_title`/`pr_description`):

1. **max_tokens bump**: gpt-oss-20b from 8192 → 128000 in `baseline.json` to avoid
   truncated JSON output.
2. **Adaptive batch size**: Use `batch_size=2` when `context_window < 6000`; gpt-oss-20b
   reports `context_window=3900` (LlamaIndex artifact), so it gets `batch_size=2`.
3. **Guarded retry**: On batch failure, split once (depth=1) within 300s budget, then skip.
   Prevents 600-second timeout cascades.
4. **Accurate batch counting**: Report actual `batches_succeeded` instead of hardcoded `1`.
5. **OPTIMIZE_INSTRUCTIONS**: Document consequence-echoing and UUID format inconsistency as
   known problems.

**Resolution status**:

- **Adaptive batch size** — Correctly implemented. For gpt-oss-20b, LlamaIndex reports
  `context_window=3900 < 6000`, so `batch_size=2` is selected as intended. Logic is sound.

- **Guarded retry** — Correctly implemented. Confirmed in
  `history/4/07_enrich_potential_levers/events.jsonl`: gpt-oss-20b failing plans now
  complete in <2s vs the pre-PR 600s timeout. `MAX_RETRY_DEPTH=1`, `MAX_RETRY_BUDGET_SECONDS=300`,
  and the `insert(0, ...)` ordering are all correct.

- **Accurate batch counting** — Improved. `calls_succeeded=result.batches_succeeded` in
  `runner.py:184` replaces the pre-PR hardcoded `1`. Confirmed: silo/gta show
  `calls_succeeded: 4`; failing plans show `calls_succeeded: 0`. Minor residual issue (B4):
  `batches_succeeded` is incremented even for partial LLM responses.

- **max_tokens bump** — **Introduces a critical regression**. Setting `max_tokens=128000`
  for a model with `context_window=131072` leaves only `131072 − 128000 = 3072` tokens for
  input text. Individual levers consume 3675–3909 input tokens. Every batch — including
  single-lever batches at retry depth=1 — fails with `BadRequestError`.

  Evidence from `history/4/07_enrich_potential_levers/outputs/20260308_sovereign_identity/
  002-12-enriched_levers_raw.json`:
  ```
  "you requested about 131909 tokens (3909 of text input, 128000 in the output).
   Please reduce the length of either one..."
  ```
  12 error entries (3 `batch_retry` + 6 `batch_skipped` + 3 `incomplete`), 0 characterized
  levers, yet `outputs.jsonl` reports `status: "ok"`. The three affected plans
  (sovereign_identity, hong_kong_game, parasomnia) silently produce empty lever sets.

- **Residual symptoms**: 3/5 gpt-oss-20b plans still produce zero characterized levers.
  Root cause shifts from "no retry on overflow" to "max_tokens consumes nearly all context
  window." The fundamental problem — gpt-oss-20b cannot process most plans — persists.

---

## Quality Comparison

**Important confound**: Between runs 3/91 (before) and 4/06 (after), the input baseline
was regenerated. Before-PR runs enriched 14–18 levers per plan (from `002-10`, full
potential levers set); after-PR runs enrich 5–8 levers (from the correctly deduped set
matching baseline `002-12`). Content quality metrics cannot be cleanly attributed to PR
#454 vs. this input change. Only operational reliability metrics are reliable comparisons.

| Metric | Before (3/85–3/91) | After (4/06–4/12) | Verdict |
|--------|-------------------|------------------|---------|
| **Success rate (status=ok)** | 30/35 (85.7%) | 35/35 (100%) | IMPROVED (but misleading — 3 gpt-oss-20b plans silently empty) |
| **Plans with all levers enriched** | 30/35 (85.7%) | 32/35 (91.4%) | IMPROVED |
| **gpt-oss-20b plans fully enriched** | 0/5 (0%) | 2/5 (40%) | IMPROVED |
| **gpt-oss-20b silent zero-lever failures** | N/A (hard fail) | 3/5 (60%) | REGRESSION (new silent failure mode) |
| **Fail-fast for gpt-oss-20b failures** | 600s | <2s | IMPROVED (300× faster) |
| **Accurate batch count reporting** | Hardcoded 1 | Actual count | IMPROVED |
| **Description length vs baseline** | 0.65×–1.19× | 0.74×–1.40× | UNCHANGED (input confound; all in acceptable range) |
| **Synergy_text length vs baseline** | 0.69×–1.64× | 0.82×–1.62× | UNCHANGED (input confound; all in acceptable range) |
| **Conflict_text length vs baseline** | 0.74×–1.64× | 0.84×–1.56× | UNCHANGED (input confound; all in acceptable range) |
| **Field lengths > 2× warning threshold** | 0 models | 0 models | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Template leakage (gpt-5-nano)** | Eliminated by PR #451 | Still eliminated | UNCHANGED |
| **Review format compliance** | Normal | Normal | UNCHANGED |
| **Consequence chain format** | Normal (passthrough) | Normal (passthrough) | UNCHANGED |
| **UUID leakage (llama3.1 synergy/conflict)** | Present (B2) | Present (7–16 UUIDs/plan) | UNCHANGED — confirmed in `history/4/06/silo/002-12-enriched_levers_raw.json` |
| **Consequence echoing (llama3.1 desc)** | Present (0.74× baseline) | Present (0.74× baseline) | UNCHANGED |
| **unknown_lever_id hallucination (llama3.1)** | 0 | 1 (gta_game) | REGRESSION (minor; likely B2 contributor) |
| **Fabricated % claims (model-generated)** | 0 | 0 (echoed from input) | UNCHANGED (upstream issue) |
| **Marketing-copy language** | Not observed | Not observed | UNCHANGED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |
| **batches_succeeded inflated on partial response** | N/A | Present (B4) | NEW (minor severity) |

**Models only in one batch**: None. All 7 models appear in both before and after batches.

**gpt-oss-20b detail** (from 2 successful plans only):
- Desc: 626 chars (1.29×), Syn: 371 chars (1.29×), Conf: 384 chars (1.28×) — within
  acceptable range.
- Content quality looks good for the 2 plans that succeed (silo, gta_game).

---

## New Issues

### C1 — max_tokens overflow for gpt-oss-20b (critical new regression)

Setting `max_tokens=128000` in `baseline.json` for a model with `context_window=131072`
leaves only 3072 input tokens. The model's own input context for a single lever is
3675–3909 tokens. Every batch, including the depth=1 single-lever retry, fails with
`BadRequestError`. Three of five plans (sovereign_identity, hong_kong_game, parasomnia)
produce zero characterized levers while reporting `status: "ok"`.

This is a worse failure mode than the pre-PR behavior: before, gpt-oss-20b failed visibly
with timeouts. Now it fails silently with empty output and a false success status.

Fix: reduce `max_tokens` to ≤65536 in `baseline.json` for gpt-oss-20b, giving
`131072 − 65536 = 65536` tokens of input headroom.

### C2 — Silent zero-lever failure not flagged in runner (pre-existing, now elevated)

`_run_enrich` returns `status="ok"` even when `characterized_levers` is empty and
`batches_succeeded=0`. The resume logic marks zero-lever plans as completed, and
downstream steps (FocusOnVitalFewLevers, ScenarioGeneration) silently receive an empty
lever list. Pre-PR this was theoretical; post-PR it is confirmed for 3/5 gpt-oss-20b plans.

### C3 — Input confound prevents content quality comparison across PR boundary

Before-PR runs (3/85–3/91) used `snapshot/1_deduplicate_levers` (14–18 levers per plan);
after-PR runs (4/06–4/12) use `baseline/train` (5–8 levers per plan, the correctly
deduped set). Any observed change in description/synergy/conflict quality cannot be
attributed to PR #454 vs. the input change. Whether the baseline regeneration was
intentional requires confirmation before drawing content quality conclusions.

### C4 — missing `context_window` in gpt-oss-20b baseline config (latent)

`baseline.json` has a comment "131,072 context" for gpt-oss-20b but no explicit
`"context_window": 131072` in `arguments`. LlamaIndex falls back to an internal default
(~3900) that is wrong by 33×. The adaptive batch size code accidentally benefits from this
wrong value (gets `batch_size=2`), but any future code that probes the real context window
for gpt-oss-20b will get a misleading number. Contrast with `openai-gpt-5-nano` which
correctly has `"context_window": 400000`.

---

## Verdict

**CONDITIONAL**: The three mechanical improvements (guarded retry, adaptive batch size,
accurate batch counting) are correctly implemented and deliver real operational gains —
most notably the 300× fail-fast improvement for gpt-oss-20b. However, the
`max_tokens=128000` value in `baseline.json` introduces a new silent failure mode that
causes 3/5 gpt-oss-20b plans to produce zero levers while reporting `status: "ok"`. This
is strictly worse than the pre-PR behavior (visible timeout vs. silent empty output).

**Condition to promote to full YES**: Reduce `max_tokens` for `openrouter-openai-gpt-oss-20b`
in `baseline.json` from `128000` to ≤65536, and optionally add `"context_window": 131072`
to its `arguments` so the adaptive code sees the real window. A follow-up run should
confirm all 5 gpt-oss-20b plans produce non-empty lever sets.

---

## Recommended Next Change

**Proposal**: Fix `max_tokens` for gpt-oss-20b in `baseline.json` (reduce from 128000 to
65536) and add `"context_window": 131072` to its `arguments` block. Apply both changes
together as a single PR, since fixing context_window alone would change adaptive batch
size from 2 → 5 (correct behavior) but only if max_tokens is also capped.

**Evidence**: Both agents confirm the root cause. The error message is unambiguous:
`"131909 tokens (3909 of text input, 128000 in the output)"`. The comment on
`baseline.json:24` already states "131,072 context" — the correct value was available at
PR time but the input headroom was not checked. `openai-gpt-5-nano` in the same file has
`"context_window": 400000` as a precedent for the correct pattern.

**Verify**: In the next iteration's run:
- gpt-oss-20b: confirm all 5 plans (silo, gta, sovereign_identity, hong_kong_game,
  parasomnia) produce non-zero `characterized_levers`.
- gpt-oss-20b: confirm `outputs.jsonl` shows `calls_succeeded >= 1` for all 5 plans.
- gpt-oss-20b: confirm no `BadRequestError` entries in any plan's `002-12-enriched_levers_raw.json`.
- gpt-oss-20b: check that `batch_size=5` is now used (since `context_window=131072 > 6000`
  threshold) — verify `metadata[].context_window` in the output JSON.
- All models: confirm description/synergy/conflict lengths stay within 0.7×–2.0× baseline.
- llama3.1: `unknown_lever_id` count should remain ≤1 (baseline noise) — watch gta_game.

**Risks**:
- If `max_tokens=65536` is too low, gpt-oss-20b JSON output may be truncated for levers
  with very long generated descriptions. Monitor for truncated/incomplete JSON parse errors.
  If truncation occurs, try `max_tokens=98304` (3/4 of context window).
- Changing `context_window` from 3900 to 131072 shifts adaptive batch size from 2 → 5.
  At `batch_size=5` with longer lever context, input tokens per batch increase ~5×. Verify
  the per-batch input stays under the new headroom (65536 tokens).
- The `batches_succeeded` inflation issue (B4 in code_claude) means partial responses still
  count as full successes. This is a monitoring gap but not a data-loss risk; the per-lever
  `incomplete` error path already catches silently-dropped levers.

**Prerequisite issues**: None. The fix is self-contained in `baseline.json`. The zero-lever
guard (Direction #3 from synthesis) is a valuable safety net but not required for the fix
to work — adding it alongside would make the success/failure more visible.

**OPTIMIZE_INSTRUCTIONS update recommended**: Add the entry proposed in `synthesis.md`:
```
- max_tokens overflow for small-context models. If max_tokens is set close to the
  model's context_window, the available input token budget drops to near zero, causing
  all batches to fail with BadRequestError even at batch_size=1. Cap max_tokens at
  (context_window // 2) or set a model-specific max_tokens in baseline.json.
  Silent failure mode: plan-level status remains "ok" but characterized_levers is empty.
```

---

## Backlog

**Resolved by PR #454 (can be removed from active tracking)**:
- B1 (no per-batch retry in `enrich_potential_levers.py`): Guarded retry is now implemented
  correctly at depth=1 with a 300s budget. This was the root cause of gpt-oss-20b's pre-PR
  0/5 success rate from timeout cascades.
- B4 (calls_succeeded hardcoded to 1 in `runner.py`): Now uses `result.batches_succeeded`.

**Remaining from before, unchanged**:
- **B2/UUID leakage** (`enrich_potential_levers.py:198`): `full_lever_context_str` still
  emits `lever.lever_id` UUIDs. llama3.1 injects 7–16 full UUIDs per plan into
  synergy/conflict text. Fix: change `f"- {lever.lever_id}: {lever.name}"` →
  `f"- {lever.name}"`. Now also documented in OPTIMIZE_INSTRUCTIONS.
- **Consequence echoing (llama3.1)**: Description length ~0.74× baseline; model summarizes
  `consequences` field rather than elaborating. Fix: add anti-echoing guidance to system
  prompt and OPTIMIZE_INSTRUCTIONS. Now documented in OPTIMIZE_INSTRUCTIONS.
- **D3/qualitative mechanism guidance** for synergy/conflict: qwen3-30b synergy/conflict
  remains terse (0.82× baseline syn, 0.84× conf). System prompt gives "(40-60 words)" but
  no guidance on what kind of content fills those words.
- **B5/partial_recovery false positive** (`runner.py:131`): `if actual_calls < 3` fires
  for normal 2-call successes. Fix: change to `actual_calls == 0`.
- **S1-S3/latent concurrency issues** in `runner.py`: Closure capture, global dispatcher
  cross-contamination, unsafe list mutation. Not triggered in single-threaded runs.
- **I5/options validator inconsistency**: `identify_potential_levers.py` validator accepts
  >3 options despite "Exactly 3. No more, no fewer" in field description.
- **I6/English-only anti-patterns**: `consequences` field description lists English phrases
  as anti-patterns, violating OPTIMIZE_INSTRUCTIONS guidance on language-agnostic validators.

**New issues to track**:
- **C1/max_tokens overflow** for gpt-oss-20b: `baseline.json` max_tokens=128000 leaves
  only 3072 input tokens for 131072-token context model. **Priority: HIGH** (blocking fix
  for PR #454 CONDITIONAL verdict).
- **C2/Silent zero-lever failure**: `_run_enrich` returns `status="ok"` with empty
  `characterized_levers`. Add guard: `if not result.characterized_levers: raise ValueError(...)`.
- **C3/Input confound**: Before-PR runs used 14–18 levers (002-10); after-PR runs use
  5–8 levers (002-12). Confirm whether baseline regeneration was intentional before drawing
  content quality conclusions across the PR boundary.
- **C4/Missing context_window in gpt-oss-20b config**: Add `"context_window": 131072` to
  `baseline.json` `arguments` for gpt-oss-20b. Must be paired with max_tokens fix (C1) to
  avoid changing batch size without adequate output headroom.
- **B4/inflated batches_succeeded metric**: `batches_succeeded` incremented even for partial
  LLM responses (2 of 5 levers returned). Low severity; the per-lever `incomplete` path
  already catches dropped levers.
