# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/enrich_potential_levers.py`
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py`
- `self_improve/runner.py`

---

## Bugs Found

### B1 — `SMALL_CONTEXT_THRESHOLD=6000` is above OpenRouter's universal fallback value of 3900

**File:** `enrich_potential_levers.py:112,194-196`

```python
SMALL_CONTEXT_THRESHOLD = 6000   # line 112
...
if context_window < SMALL_CONTEXT_THRESHOLD:   # line 195
    batch_size = SMALL_CONTEXT_BATCH_SIZE       # → 2
```

llama_index's `OpenRouter_LLM` reports `context_window=3900` for **all** OpenRouter-proxied
models, regardless of their actual capability. Since 3900 < 6000, `batch_size=2` is set
for every OpenRouter model. Three production models are affected: qwen3-30b (~32768+
actual), gpt-4o-mini (128 000 actual), gemini-2.0-flash (1 000 000 actual). None of them
benefit from batch_size=2; each now processes 4 batches where before it processed 1.

The PR comment on line 110–111 says "context_window is the correct metric" but the
threshold was not calibrated to exclude the OpenRouter fallback value. The actual small
context model the feature was designed for (gpt-oss-20b before the config fix) now
correctly reports `context_window=131072` and is **not** in the small-batch path — so the
adaptive feature currently protects nothing while penalising three unrelated models.

**Fix options (cheapest first):**
1. Lower `SMALL_CONTEXT_THRESHOLD` from 6000 to 3000. OpenRouter's fallback 3900 clears
   the new limit; genuinely constrained models (< 3000) still trigger small-batch mode.
2. Add an allowlist check: `batch_size=2` only for models whose class name or config name
   matches a known small-context model.
3. Remove the adaptive feature entirely — gpt-oss-20b is now correctly configured with
   `context_window=131072`.

---

### B2 — `MAX_RETRY_BUDGET_SECONDS` does not guard LLMExecutor's internal provider failover

**Files:** `enrich_potential_levers.py:106,216,275-303`, `llm_executor.py:233-286`

`MAX_RETRY_BUDGET_SECONDS=300` is checked **only** when a batch fails in the
`pending_batches` loop (line 280: `elapsed < MAX_RETRY_BUDGET_SECONDS`). It guards whether
to **split and re-queue** a failed batch. It does **not** limit how long a single
`llm_executor.run(execute_function)` call may take.

For gpt-oss-20b, `LLMExecutor.run()` iterates through a long provider fallback list
(DeepInfra → Fireworks → Together → Nebius → Amazon Bedrock → …). Each failed provider
attempt takes 60–120 s before timing out. Nine sequential provider attempts = 540–810 s
for a single batch call. Because the batch ultimately **succeeds** (valid output is
written), the `except Exception` block in `enrich_potential_levers.py:275` is never
reached, so the `elapsed` guard is never checked.

Result: a 5-lever plan with `batch_size=5` makes **one** `pending_batches` iteration that
internally runs 9 LLMExecutor attempts, consuming 600 s+ before the orchestrator's wall
clock fires. The `MAX_RETRY_BUDGET_SECONDS` constraint in the PR provides no relief.

**Root cause hierarchy:**
- Proximate: LLMExecutor's provider fallover sequence for gpt-oss-20b is unbounded in
  time.
- Contributing: `MAX_RETRY_BUDGET_SECONDS` was not designed to limit LLMExecutor's
  per-attempt fallover; it only limits the pending_batches retry loop.

**Fix options:**
1. Add a per-step wall-clock budget that is checked inside LLMExecutor (or passed to it)
   so the total execution time for a single `run()` call is capped.
2. Reduce the number of provider fallbacks registered for gpt-oss-20b in its llm_config
   entry (or add a `max_attempts` cap to LLMExecutor).
3. Increase `DEFAULT_PLAN_TIMEOUT` for the enrich step (e.g., 900 s or 1200 s), accepting
   that gpt-oss-20b is slow but succeeds.

---

### B3 — Probe LLM instance is created but never closed

**File:** `enrich_potential_levers.py:193`

```python
probe_llm = llm_executor.llm_models[0].create_llm()
context_window = probe_llm.metadata.context_window
# probe_llm is never released
```

`create_llm()` calls `get_llm(name)`, which may instantiate HTTP client sessions,
connection pools, or authentication state depending on the provider SDK. The probe is used
only to read one metadata field and then goes out of scope without any explicit close. For
providers that allocate persistent resources in the constructor (e.g., Anthropic, OpenAI
clients), this leaks connections per plan. With 5 plans × 7 concurrent workers, 35
unclosed clients accumulate.

The metadata could be obtained more cheaply by reading `context_window` directly from the
model config dict (if available) or by caching a single probe per model name across plans.

---

### B4 — `consequences` field description contains explicit English-keyword prohibitions

**Files:** `identify_potential_levers.py:113-118` (Lever), `identify_potential_levers.py:211-214` (LeverCleaned)

Both models carry:
```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field"
```

`OPTIMIZE_INSTRUCTIONS` lines 79–82 explicitly documents this as an anti-pattern:
> "Do NOT add explicit prohibitions naming banned phrases — small models treat the
> prohibition text as a template and copy the banned phrases."

The prohibition text is embedded in the Pydantic field description, which is sent to the
LLM as part of the schema prompt. Weak models (llama3.1, qwen3-30b) may echo "Controls
... vs." or "Weakness:" into consequences fields when they encounter the prohibition. The
OPTIMIZE_INSTRUCTIONS document was updated to warn about this pattern, but the field
descriptions themselves were not fixed.

**Fix:** Remove the phrase-specific prohibition from both field descriptions. Structural
guidance ("do not include critique text") can remain; the specific banned strings should
be removed.

---

### B5 — `execute_function` closure captures `chat_message_list` by reference in enrich loop

**File:** `enrich_potential_levers.py:247-254`

```python
chat_message_list = [system_message, ChatMessage(..., content=user_prompt)]

def execute_function(llm: LLM) -> dict:
    ...
    chat_response = sllm.chat(chat_message_list)   # captured by reference
    ...

result = llm_executor.run(execute_function)
```

Python closures bind to the **name** `chat_message_list`, not to the list object at
closure-creation time. Because `llm_executor.run()` is synchronous and blocks until all
provider attempts complete, the current value of `chat_message_list` is consistent
throughout each `while` iteration — so this is not an active bug today.

However, `identify_potential_levers.py:317` defensively takes an explicit snapshot:
```python
messages_snapshot = list(call_messages)
def execute_function(llm):
    ... sllm.chat(messages_snapshot)   # snapshot, not reference
```

The enrich loop does not apply the same defensive pattern. If `LLMExecutor.run()` ever
becomes asynchronous or if `enrich`'s retry loop is refactored to overlap iterations,
this will silently send the wrong batch's messages to a pending provider attempt.

---

## Suspect Patterns

### S1 — Orphaned thread continues consuming API resources after plan timeout

**File:** `runner.py:554-566`

```python
with _TPE(max_workers=1) as executor:
    future = executor.submit(run_single_plan, ...)
    try:
        pr = future.result(timeout=plan_timeout)
    except _TE:
        pr = PlanResult(status="error", ...)   # timeout recorded
# orphaned thread continues running
```

When `future.result(timeout=plan_timeout)` raises `TimeoutError`, the `run_single_plan`
thread continues executing — Python threads cannot be killed. For gpt-oss-20b plans that
time out at 600 s, the thread keeps making provider API calls. With 5 plans × 3 timing
out, up to 15 uncontrolled LLM calls may be in flight simultaneously. This drives up API
costs and can cause rate-limit cascades for subsequent plans.

Mitigation: add a cancellation event that `run_single_plan` polls between batches, or
pass the `plan_timeout` as an explicit budget to `EnrichPotentialLevers.execute()` so it
can stop before the orchestrator fires.

---

### S2 — Per-plan `log.txt` captures only `_run_plan_task` thread logs, not worker logs

**File:** `runner.py:540-548`

```python
thread_filter = _ThreadFilter(threading.current_thread().ident)  # T1
file_handler.addFilter(thread_filter)
root_logger.addHandler(file_handler)
...
future = executor.submit(run_single_plan, ...)  # runs on T2
```

`_ThreadFilter` is scoped to `_run_plan_task`'s thread (T1). `run_single_plan` executes
on a different thread (T2) inside a nested `ThreadPoolExecutor`. All LLM interaction logs
(batch progress, validation errors, retry events) are emitted from T2 and are therefore
filtered out of `log.txt`. The file contains only the start/timeout/completion events
logged by T1.

In practice this means `log.txt` for a timed-out plan shows only "killed after 600s" and
nothing about which batch was in progress or how many provider attempts were made. The
insight's reference to log.txt (run 14's `hong_kong_game/log.txt`) confirms this — only
the orchestrator-level message appears, not the LLM-level detail.

**Fix:** Either move `run_single_plan` to execute directly in T1 (removing the nested
executor), or pass `file_handler` into `run_single_plan` and apply the filter to T2's
thread ID there.

---

### S3 — `batches_succeeded` incremented even when batch returns unknown lever IDs

**File:** `enrich_potential_levers.py:259-271`

```python
batches_succeeded += 1   # line 260 — incremented unconditionally on parse success

for char in batch_result.characterizations:
    if char.lever_id in enriched_levers_map:
        ...                             # lever updated
    else:
        errors.append({"type": "unknown_lever_id", ...})   # lever lost
```

A batch that parses successfully but returns mutations of the real lever IDs (as with
llama3.1 UUID mutations, N5) increments `batches_succeeded` while producing zero useful
enrichment. The counter overstates actual enrichment coverage. Downstream, this feeds into
`PlanResult.calls_succeeded` in `outputs.jsonl`, which analysis scripts use as a quality
signal.

---

## Improvement Opportunities

### I1 — Add explicit snapshot for `chat_message_list` before closure

**File:** `enrich_potential_levers.py:247`

Apply the same pattern used in `identify_potential_levers.py:317`:
```python
messages_snapshot = list(chat_message_list)
def execute_function(llm: LLM) -> dict:
    ...
    chat_response = sllm.chat(messages_snapshot)
```
This makes the closure safe against future refactoring and matches the existing style in
the codebase.

---

### I2 — `review_lever` Pydantic field description contains structural template phrases

**File:** `identify_potential_levers.py:126-132`

```python
review_lever: str = Field(
    description=(
        "A short critical review: identify the primary trade-off "
        "this lever introduces, then state the specific gap the "
        "three options leave unaddressed. ..."
    )
)
```

`OPTIMIZE_INSTRUCTIONS` lines 87–92 warns: "A Pydantic field description containing a
structural phrase (e.g. 'name the core tension') is read as a literal instruction — models
start every output with 'The tension is…'. Describe the required content not the expected
sentence structure."

The phrases "identify the primary trade-off" and "state the specific gap" are structural
instructions. Models that obey field descriptions literally will begin every `review_lever`
with "The primary trade-off is..." or "The specific gap is...". The system prompt section
4 provides three domain-specific examples that avoid this — but the field description
overrides them for models that weight field descriptions heavily.

**Fix:** Replace the structural framing in the field description with content-focused
language: e.g., "A concise one-sentence analysis of the trade-off and the blind spot in
the three options."

---

### I3 — Fuzzy UUID matching for llama3.1-style lever ID mutations

**File:** `enrich_potential_levers.py:263-271`

When llama3.1 returns a mutated UUID (e.g., `"056fa843-5572-40a5-bca5-bca5cc7c18408"` for
actual `"056fa843-5572-40a5-bca5-cc7c7cc18408"`), the enrichment is discarded and the
lever is marked `incomplete`. Adding a fuzzy-match fallback — e.g., find the lever_id with
the highest character-level similarity when an exact match fails — would recover most of
these cases without retrying the full batch. The lever mutation pattern observed in run 13
is consistent: the UUID prefix is always correct; only the last segment is garbled.

---

### I4 — `DEFAULT_PLAN_TIMEOUT` should be configurable per step

**File:** `runner.py:93`

```python
DEFAULT_PLAN_TIMEOUT = 600
```

gpt-oss-20b with 5-9 provider attempts per batch consistently uses 300–600 s per plan.
The current single timeout value forces a choice between allowing slow-but-valid gpt-oss-20b
plans to complete (requiring 900 s+) and protecting all other models from infinite hangs
(requiring ≤ 600 s). A per-step or per-model timeout override in llm_config would allow
raising the limit for gpt-oss-20b without affecting other models.

---

### I5 — `batches_succeeded` should count only batches where all characterizations matched

**File:** `enrich_potential_levers.py:259-271`

A more accurate counter would track "batches that produced enrichment for every lever in
the batch":
```python
all_matched = all(char.lever_id in enriched_levers_map for char in batch_result.characterizations)
batches_succeeded += 1 if all_matched else 0
# record partial-success in errors separately
```
This makes `calls_succeeded` in `outputs.jsonl` a reliable signal for downstream analysis.

---

## Trace to Insight Findings

| Insight finding | Code location | Explanation |
|-----------------|---------------|-------------|
| N1 — gpt-oss-20b 3/5 plans timeout | `llm_executor.py:233-286` + `enrich:216` | `MAX_RETRY_BUDGET_SECONDS` does not limit LLMExecutor's internal provider failover. 9 sequential provider attempts × 60-90 s = 540-810 s for a single `run()` call. See B2. |
| N2 — OpenRouter models unintentionally get batch_size=2 | `enrich:112,194-196` | `SMALL_CONTEXT_THRESHOLD=6000 > 3900` (OpenRouter's universal llama_index fallback). See B1. |
| N5 — llama3.1 UUID mutations cause silent lever skips | `enrich:263-271,313-315` | No fuzzy match on `unknown_lever_id` path; mutated UUID always discards enrichment and marks lever `incomplete`. See S3 and I3. |
| P3 — Error tracking operational | `enrich:215,271,290,303,312,315` | The new `errors` list correctly captures `unknown_lever_id`, `batch_retry`, `batch_skipped`, `validation_error`, and `incomplete` events. Design is sound. |
| P5 — gpt-oss-20b output written despite status=error | `runner.py:557-566` + `enrich:305-332` | `save_raw()` is called by `run_single_plan` before the orchestrator's `future.result(timeout=...)` fires. Timeout fires in caller thread; enrichment file is already on disk. |
| Analysis confound (N3) | `runner.py:165-184` | Runner reads `FilenameEnum.DEDUPLICATED_LEVERS_RAW` from the plan directory (baseline/train), not from snapshot. The input source is determined by which data is staged at `--baseline-dir` — the runner itself is correct; the confound is in the experiment setup. |

---

## PR Review

PR #455 makes five changes. Assessment of each:

### 1. gpt-oss-20b config fix (`max_tokens` 8192→65536, `context_window=131072`)

**Verdict: Correct and effective.** The `BadRequestError` root cause (8192 max_tokens left
only ~3 K input headroom) is eliminated. All 5 plans now produce valid output files.
No code-level concern.

### 2. Adaptive batch_size (B1)

**Verdict: Bug introduced.** The threshold `SMALL_CONTEXT_THRESHOLD=6000` was chosen
without accounting for llama_index's universal OpenRouter fallback value of 3900. The
feature activates for three production models that do not need it, increasing their API
call counts by 3–4×. The original target (gpt-oss-20b) no longer triggers the feature
after the config fix in change 1. The net result: the adaptive feature provides no benefit
and creates unintended side effects.

The fix is simple: lower `SMALL_CONTEXT_THRESHOLD` to 3000 (below OpenRouter's 3900) or
remove the feature entirely.

### 3. Guarded retry (`pending_batches` loop with depth and budget guards)

**Verdict: Correct in design, insufficient for gpt-oss-20b timeouts.** The retry logic
(split batch on failure, guard by depth and elapsed time) is a sound improvement over
silently dropping failed batches. The guards prevent infinite loops. However, the
`MAX_RETRY_BUDGET_SECONDS=300` budget does not cap the time spent inside a single
`llm_executor.run()` call, so gpt-oss-20b's 6-9 provider attempts per call consume the
entire plan timeout even when the batch ultimately succeeds. This is B2.

The retry infrastructure itself is well-structured and should be kept. The fix is at the
LLMExecutor or config level, not in the `pending_batches` loop.

### 4. Error tracking (`errors` field in JSON output)

**Verdict: Correct and valuable.** The `errors` list correctly captures all failure modes
(unknown_lever_id, batch_retry, batch_skipped, validation_error, incomplete) and is
persisted to disk. Run 13's llama3.1 UUID mutation errors confirm the feature works as
intended. The `save_raw` addition is clean.

Minor: `batches_succeeded` is incremented even for batches that return wrong lever IDs
(S3). This is a semantic imprecision, not a data-loss bug.

### 5. Accurate batch counting (`batches_succeeded` replaces hardcoded `1`)

**Verdict: Correct.** Before this PR, `runner.py` returned `calls_succeeded=1` regardless
of actual batch count. The PR fixes this via `result.batches_succeeded`. The value in
`outputs.jsonl` now correctly reflects 2 batches for llama3.1/gpt-5-nano (7 levers ÷ 5
= 2 batches) and 4 for OpenRouter models (7 levers ÷ 2 = 4 batches, due to B1).

### 6. OPTIMIZE_INSTRUCTIONS additions

**Verdict: Accurate and useful.** The three new entries (consequence echoing, UUID
cross-reference format, max_tokens overflow) document real problems observed in prior
runs. The max_tokens overflow entry documents the exact root cause fixed by change 1,
which provides clear rationale in the codebase. Entry 1 ("consequence echoing") was
proposed in analysis 54 and is now formalized.

---

## Summary

The PR's primary goal — fixing gpt-oss-20b's `BadRequestError` from `max_tokens=8192`
overflow — is confirmed successful. All 5 plans produce valid enriched lever files.

**Critical regression introduced (B1):** The `SMALL_CONTEXT_THRESHOLD=6000` check is too
permissive. llama_index's `OpenRouter_LLM` reports `context_window=3900` for all
OpenRouter-proxied models, which falls below the threshold. Three production models
(qwen3-30b, gpt-4o-mini, gemini-flash) now run in batch_size=2 mode unnecessarily,
tripling their API call counts and activating the "batch boundary blindness" risk
documented in OPTIMIZE_INSTRUCTIONS. This should be the priority fix for the next
iteration.

**Persistent issue (B2):** gpt-oss-20b still times out on 3/5 plans. The root cause is
that LLMExecutor's provider fallover sequence (6-9 attempts × 60-90 s each) consumes the
600 s plan timeout. `MAX_RETRY_BUDGET_SECONDS=300` was introduced to limit retries but
does not cap the time spent inside a single `llm_executor.run()` call. The enriched lever
files are written correctly; only the orchestrator-level status is `error`. Fixing this
requires either increasing `DEFAULT_PLAN_TIMEOUT` for the enrich step or capping
LLMExecutor's total per-call fallover time.

**Pre-existing issues confirmed by this review:**
- B4 (field description containing banned phrases) was present before PR #455 and is now
  documented in OPTIMIZE_INSTRUCTIONS but not yet fixed in the code.
- B5 (closure by reference vs snapshot) is latent and safe today but diverges from the
  pattern used in `identify_potential_levers.py`.
- S2 (per-plan log.txt missing worker thread logs) limits debuggability for future
  timeout investigations.
