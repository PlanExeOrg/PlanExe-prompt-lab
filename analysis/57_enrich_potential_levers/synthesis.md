# Synthesis

## Cross-Agent Agreement

Both agents (insight_claude and code_claude) agree on the following:

- **PR #454 verdict: CONDITIONAL.** Three of the four changes are correctly implemented
  (adaptive batch size, guarded retry, accurate batch counting) and deliver real
  improvements. The max_tokens=128000 value is a miscalibration that introduces a new
  silent failure mode.

- **gpt-oss-20b max_tokens overflow (C1/B2) is the critical bug.** Setting
  `max_tokens=128000` in `baseline.json` for a model with a 131072-token context window
  leaves only 3072 tokens for input text. Single-lever batches (3675–3909 tokens each)
  can't fit. Three of five plans produce zero characterized levers, yet report
  `status="ok"`. Both agents flag this as the top-priority fix.

- **UUID leakage at line 198 (B1 in code_claude / B2 in insight_claude) is a confirmed
  code bug.** `full_lever_context_str` emits `lever.lever_id` UUIDs, causing llama3.1 to
  inject full UUIDs into synergy/conflict text, and contributing to hallucinated
  `unknown_lever_id` errors (N3). Both agents independently identify the same one-line fix
  at `enrich_potential_levers.py:198`.

- **Silent zero-lever failure (B3 / insight Q3) is an observability gap.** When all
  batches fail, `_run_enrich` returns `status="ok"` with `batches_succeeded=0`. Both
  agents agree a zero-lever guard should be added to make this failure visible.

- **Guarded retry and adaptive batch size are correctly implemented.** Both agents confirm
  these work as designed. The 600 s → <2 s fail-fast improvement for gpt-oss-20b is real.

- **Content quality for the 6 remaining models is stable** (0.74×–1.62× baseline).
  No model exceeds the 2× warning threshold.

---

## Cross-Agent Disagreements

**B4 (inflated batches_succeeded metric):** code_claude flags that `batches_succeeded` is
incremented even when the LLM returns a partial response (fewer characterizations than
batch levers). insight_claude does not address this. Reading `enrich_potential_levers.py:254`,
the increment `batches_succeeded += 1` fires immediately after `llm_executor.run()` succeeds,
regardless of how many `characterizations` are in `batch_result`. **code_claude is correct.**
A batch returning 2 of 5 characterizations still counts as 1 succeeded batch. The metric
is inflated but the downstream effect is minor (silent lever loss is already caught by the
`incomplete` error path at line 308). This is a real issue but lower severity than B2/B1.

**S2 (options field description mismatch):** code_claude flags that `Lever.options` says
"Exactly 3 options… No more, no fewer" while the validator at `identify_potential_levers.py:157`
only enforces `len(v) < 3`. insight_claude does not mention this. Reading the source,
the discrepancy is confirmed and the validator docstring even acknowledges it ("Over-generation
>3 is tolerable"). **code_claude is correct** but the issue is minor — the validator comment
explains the intent.

**S1 (false-positive partial recovery warning):** code_claude flags `runner.py:131`
`if actual_calls < 3` fires for `actual_calls == 2`, which is the normal success case.
Reading the source, the adjacent comment says "A 2-call success is normal for models that
produce 8+ levers per call" — yet the warning still fires for 2. **code_claude is correct.**
The threshold should be `actual_calls == 0`.

**Input confound (lever count 14–18 before → 5–8 after):** insight_claude raises this as a
significant confound preventing content quality comparison. code_claude does not address it.
This is a real observation and warrants investigation, but is outside the scope of PR #454
itself.

---

## Top 5 Directions

### 1. Fix max_tokens for gpt-oss-20b in baseline.json
- **Type**: code fix (config change)
- **Evidence**: Both agents, B2 (code_claude), C1 (insight_claude). Confirmed at
  `baseline.json` line 34. The error message "you requested about 131909 tokens
  (3909 of text input, 128000 in the output)" is unambiguous.
- **Impact**: Directly recovers the 3/5 gpt-oss-20b plans that currently produce zero
  levers. Affects 60% of gpt-oss-20b runs. Does not touch other models.
- **Effort**: Low — one value change in baseline.json, plus optionally adding
  `"context_window": 131072` to the same entry (S4) so the adaptive code can see the real
  window.
- **Risk**: If max_tokens is set too low, JSON output may be truncated again (the original
  problem). Setting to 65536 (half the 131072 window) is the safe midpoint: leaves 65536
  tokens for input, which comfortably covers the system prompt + full lever context.

### 2. Strip UUIDs from full_lever_context_str
- **Type**: code fix
- **Evidence**: Both agents, B1 (code_claude), B2 (insight_claude). Confirmed at
  `enrich_potential_levers.py:198`. The UUID injection into synergy/conflict text is
  visible in every llama3.1 run (7–16 UUIDs per plan).
- **Impact**: Eliminates UUID leakage for llama3.1 (1 of 7 models), reduces N3
  hallucinated `unknown_lever_id` errors. Improves synergy/conflict text readability for
  all models (cleaner context string). The OPTIMIZE_INSTRUCTIONS already documents this as
  a known problem at lines 88–92, but the code was never changed.
- **Effort**: Low — one-line change at `enrich_potential_levers.py:198`.
- **Risk**: Removing lever_id from the context string means the LLM sees only names in the
  full list. The batch prompt still includes `Lever ID: {lever.lever_id}` for each lever
  being characterized (lines 223–229), so models can still return the correct lever_id for
  the batch. Cross-batch references will shift to name-only, which is the intended behavior
  per OPTIMIZE_INSTRUCTIONS.

### 3. Add zero-lever guard in _run_enrich
- **Type**: code fix
- **Evidence**: code_claude B3, insight_claude Q3. Confirmed at `runner.py:165–185` — no
  check for empty `characterized_levers` before returning `status="ok"`.
- **Impact**: Converts a silent failure into a visible `status="error"`. Prevents the
  resume logic from treating a zero-lever plan as complete. Downstream steps (focus,
  scenario generation) would no longer silently receive an empty lever list. Affects any
  model that experiences total batch failure.
- **Effort**: Low — 2–3 lines added to `_run_enrich`.
- **Risk**: Plans that previously completed silently will now show as errors and may block
  downstream pipeline steps. This is the desired behavior, but it changes observable
  output. If the pipeline has error-handling that stops on first error, this could mask
  problems in other steps if not configured correctly.

### 4. Add context_window to gpt-oss-20b baseline config (S4)
- **Type**: code fix (config)
- **Evidence**: code_claude S4. Confirmed by contrast with `openai-gpt-5-nano` which has
  `"context_window": 400000` in its `arguments`. gpt-oss-20b has a comment "131,072
  context" but no explicit config field, causing LlamaIndex to report 3900.
- **Impact**: Enables the adaptive batch size code to see the real context window (131072)
  instead of the LlamaIndex metadata artifact (3900). This makes the code's adaptive logic
  accurate for gpt-oss-20b and allows a future programmatic max_tokens cap. Paired with
  direction #1, this is the complete fix. On its own, it changes the adaptive batch size
  from 2 → 5 for gpt-oss-20b (since 131072 > 6000), which is only correct if max_tokens
  is also fixed.
- **Effort**: Low — one field addition in baseline.json. Must be paired with direction #1
  to avoid regressing batch size behavior.
- **Risk**: Changing `context_window` from 3900 to 131072 will cause the adaptive batch
  size code to select `batch_size=5` instead of `batch_size=2`. This is the correct
  batch size for a large-context model, but only safe if max_tokens is capped appropriately
  (direction #1). Apply directions #1 and #4 together.

### 5. Fix false-positive partial recovery warning (S1)
- **Type**: code fix
- **Evidence**: code_claude S1. Confirmed at `runner.py:131` — `if actual_calls < 3`
  fires for `actual_calls == 2`, which is normal for models producing 8+ levers per call.
  The adjacent comment acknowledges this but the threshold was not updated.
- **Impact**: Eliminates spurious log warnings for normal 2-call successful runs. Reduces
  log noise in production, making genuine partial-recovery warnings meaningful. Does not
  affect output quality or success metrics.
- **Effort**: Low — change `< 3` to `== 0` at `runner.py:131`.
- **Risk**: Minimal. If the threshold is set to `== 0`, it will only fire on total
  failure (0 successful LLM calls), which is unambiguously a problem.

---

## Recommendation

**Do direction #1 (max_tokens fix) and direction #4 (context_window config) together as a
single PR**, then verify with a new run against all 5 plans for gpt-oss-20b.

**Specific changes:**

In `llm_config/baseline.json`, find the `openrouter-openai-gpt-oss-20b` entry and make
two changes:

1. Add `"context_window": 131072` to the `arguments` block so LlamaIndex reports the real
   window.
2. Reduce `max_tokens` from `128000` to `65536` (half the real context window), leaving
   adequate input headroom.

Result: gpt-oss-20b's adaptive batch size becomes `5` (131072 > 6000 threshold), and the
input budget for each batch is `131072 − 65536 = 65536 tokens` — enough for 7–8 levers
with full context. The three plans that currently produce zero levers (sovereign_identity,
hong_kong_game, parasomnia) should now succeed.

**Why first:** This is a one-location config fix that directly recovers 3/5 gpt-oss-20b
plans from silent failure. It has the highest expected improvement per unit of effort. The
UUID strip (direction #2) affects only llama3.1 output quality (cosmetic/readability) and
is lower urgency. The zero-lever guard (direction #3) is an important observability fix
but does not recover any levers — it just makes existing failures visible. Fixing the root
cause (direction #1+4) before improving observability (direction #3) is the right order.

**Also add to OPTIMIZE_INSTRUCTIONS** in `enrich_potential_levers.py` after the UUID
cross-reference entry:

```
- max_tokens overflow for small-context models. If max_tokens is set close to the
  model's context_window, the available input token budget drops to near zero,
  causing all batches to fail with BadRequestError even at batch_size=1. Cap
  max_tokens at (context_window // 2) or set a model-specific max_tokens in
  baseline.json. Silent failure mode: plan-level status remains "ok" but
  characterized_levers is empty.
```

---

## Deferred Items

**Direction #2 — Strip UUIDs from full_lever_context_str** (`enrich_potential_levers.py:198`)

Change `f"- {lever.lever_id}: {lever.name}"` → `f"- {lever.name}"`. Eliminates UUID
injection into llama3.1 synergy/conflict text and reduces N3 hallucinations. Low-effort,
but impacts only llama3.1 and is a quality improvement rather than a reliability fix.
Worth doing in the next iteration alongside direction #3.

**Direction #3 — Zero-lever guard in _run_enrich** (`runner.py:165–185`)

Add `if not result.characterized_levers: raise ValueError(...)` before the return
statement. Converts silent zero-lever failure into visible `status="error"`. Pair with a
new run to confirm gpt-oss-20b fails visibly before the max_tokens fix, then passes after.

**Direction #5 — Fix partial recovery warning threshold** (`runner.py:131`)

Change `if actual_calls < 3` → `if actual_calls == 0`. Low-effort noise reduction. Can
be bundled with direction #3 in the same PR.

**B4 — Partial batch response counting**
`batches_succeeded` is incremented even for partial responses (2 of 5 levers returned).
The per-lever `incomplete` error path already catches these silently-dropped levers, so
the impact is limited to metric accuracy. Address in a future observability pass alongside
S3 (persist `batches_succeeded` in `save_raw()`).

**Input confound investigation** (insight_claude Q1)
Before-PR runs enriched 14–18 levers (from 002-10); after-PR runs enrich 5–8 (from
002-12). Whether the baseline regeneration between 3/91 and 4/06 was intentional needs
confirmation before drawing content quality conclusions across the PR boundary.
