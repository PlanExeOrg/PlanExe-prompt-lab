# Synthesis

## Cross-Agent Agreement

Both code review agents (claude, codex) reached strong consensus on four issues:

1. **PR #316 is incomplete.** The system prompt section 4 (`IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`, lines 215–220) still carries the old "First sentence… Second sentence… Controls … / Weakness:" wording. The PR updates the Pydantic field description but not the system prompt, so weaker models that weight the system prompt over field schemas (e.g. llama3.1) continue to see the old two-sentence decomposition. Both agents independently identified this as the most critical gap.

2. **`LeverCleaned.review` is stale.** Both agents flagged that the `LeverCleaned.review` field description (lines 186–194) still documents the old "Two sentences / Controls / Weakness:" format after PR #316. This is a documentation inconsistency rather than a generation bug, but it leaves two schema surfaces in contradiction.

3. **All-or-nothing Pydantic validation (S1).** A single lever with the wrong option count, or a response returning fewer than 5 levers, causes the entire `DocumentDetails` parse to fail. Valid levers from that same call are discarded. Both agents flagged this as a suspect source of wasted retries and, by extension, the 600 s timeouts that prevented the insight agents from completing.

4. **Runner global-state race conditions.** Both agents confirmed that `set_usage_metrics_path` and `dispatcher.add_event_handler` share global state during multi-worker runs, causing cross-plan tracking contamination and corrupt usage metrics.

Both insight files timed out (600 s limit exceeded), so no independent quality observations are available from those agents.

---

## Cross-Agent Disagreements

### Disagreement 1: What exactly is B2?

- **code_claude B2**: "cross-thread TrackActivity handler contamination" — the dispatcher fires all registered handlers regardless of which thread triggered the event, contaminating each plan's `track_activity.jsonl` with sibling-plan LLM events.
- **code_codex B2**: "follow-up prompts embed raw model output without escaping" — lever names from call N are interpolated directly into the prompt for calls N+1 and N+2, creating a prompt-injection/template-leakage vector.

Both are real. They are different bugs sharing the B2 label. Verified in source:

- **Dispatcher contamination** (runner.py lines 105–152): `add_event_handler` is inside `_file_lock`, but the actual LLM call at line 115 runs outside any lock. All registered handlers remain active for the full duration of each plan's LLM calls. With `workers > 1`, sibling handlers are all active simultaneously. Confirmed real.

- **Unescaped lever name interpolation** (identify_potential_levers.py lines 270–276): lever names are joined with `", ".join(f'"{n}"' for n in ...)` and embedded in an f-string. A name containing `"` or `]` would corrupt the prompt. Confirmed real but low-severity in practice since lever names rarely contain those characters.

### Disagreement 2: PR #316 — one sentence or two?

- **code_claude**: The field description still says "Two sentences" but the PR proposes a single flowing example — they must agree. Recommends keeping two sentences as the semantic intent, just expressed as a flowing example.
- **code_codex**: The PR already shows a one-sentence example in the artifacts (`history/1/60…`); the contract is now functionally one sentence. Recommends committing to one sentence explicitly and removing every "Two sentences" reference.

**Verdict (verified from source):** The current field description at lines 93–95 reads `"Two sentences. First sentence names the core tension… Second sentence identifies a weakness…"`. The PR description says it replaces this with a "single flowing example." But the single example (`"This lever governs the tension between centralization and local autonomy, but the options overlook transition costs."`) is structurally a single sentence containing both a tension and a missed consideration joined by "but". Codex is right: the intent is effectively one sentence. The "Two sentences" prose must be removed, or it will still confuse weaker models. Both the old two-sentence requirement *and* the new single-sentence example should be replaced with a single, clearly stated contract.

### Disagreement 3: OPTIMIZE_INSTRUCTIONS vs. system prompt bias

- **code_codex I1**: The system prompt requires "at least one unconventional or non-obvious approach" (line 205), which is the *opposite* of OPTIMIZE_INSTRUCTIONS' requirement for "at least one conservative, low-risk path" (line 48). Only codex flagged this.
- **code_claude**: Did not flag this specific tension.

**Verdict (verified from source):** Confirmed by direct reading. OPTIMIZE_INSTRUCTIONS line 48: "Each lever's options should include at least one conservative, low-risk path." System prompt line 205: "Include at least one unconventional or non-obvious approach." These are anti-correlated biases. The system prompt pushes models toward ambitious options; OPTIMIZE_INSTRUCTIONS says that causes the downstream scenario picker to choose over-ambitious plans. This is a real, meaningful quality regression affecting all successful runs.

---

## Top 5 Directions

### 1. Complete PR #316: commit to one `review_lever` contract across all three surfaces
- **Type**: prompt change
- **Evidence**: code_claude (I1/PR Gap 1), code_codex (B3). Both agents independently flagged the system-prompt/field-description mismatch as the most critical gap. Codex additionally confirmed via artifact inspection that the one-sentence example is being produced in practice.
- **Impact**: Affects all models on all runs. Weaker models (llama3.1) weigh the system prompt over Pydantic field descriptions; as long as section 4 of `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` says "First sentence… Second sentence…", the PR's benefit for those models is zero. Fixing this eliminates call-1 validation failures caused by format misinterpretation, recovering failed calls and reducing retry token waste.
- **Effort**: Low — three targeted edits in one file:
  1. `Lever.review_lever` field description (lines 92–100): remove "Two sentences. First sentence… Second sentence…"; replace with one clean contract sentence + single imitable example + anti-copy note.
  2. System prompt section 4 (lines 215–220): replace "one field, two sentences / First sentence… / Second sentence…" with the same single-sentence contract and example.
  3. `LeverCleaned.review` field description (lines 186–194): mirror the updated wording.
- **Risk**: Low. The validator (`check_review_format`) checks only minimum length and no square brackets — it is already compatible with both one-sentence and two-sentence outputs. No validator change required.

**Draft wording for both surfaces:**
```
"A single sentence naming the core tension this lever governs and one limitation the listed
options overlook. Example: 'This lever governs the tension between centralization and local
autonomy, but the options overlook transition costs.' Do not copy this example wording;
write a fresh sentence specific to this lever. Do not use square brackets or placeholder text."
```
Remove the `"Two sentences. First sentence… Second sentence…"` preamble entirely from both
the field description and the system prompt section 4.

---

### 2. Fix system prompt option-bias to match OPTIMIZE_INSTRUCTIONS
- **Type**: prompt change
- **Evidence**: code_codex I1. OPTIMIZE_INSTRUCTIONS explicitly states each lever must include "at least one conservative, low-risk path." System prompt section 2 (line 205) requires the opposite: "at least one unconventional or non-obvious approach."
- **Impact**: Content quality regression that affects all successful plans. The downstream scenario picker (ScenarioSelection) tends to choose the most ambitious scenario; if the levers never include a genuinely conservative option, the entire plan pipeline is biased toward over-ambitious outputs. This is exactly the "overly optimistic scenarios" failure mode documented in OPTIMIZE_INSTRUCTIONS.
- **Effort**: Low — one-line change in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` (line 205): replace "Include at least one unconventional or non-obvious approach" with "Include at least one conventional, low-risk option alongside one more ambitious alternative."
- **Risk**: Low. The change makes the system prompt consistent with the existing OPTIMIZE_INSTRUCTIONS mandate. No validator or schema changes required.

---

### 3. Fix runner.py global-state race conditions (B1 + dispatcher contamination)
- **Type**: code fix
- **Evidence**: Both agents confirmed. code_claude B1/B2; code_codex B1.
- **Impact**: In multi-worker mode, `set_usage_metrics_path(...)` is called outside the lock (line 107), so thread B can overwrite thread A's path before thread A finishes its LLM calls. Each plan's LLM calls then write usage metrics to an arbitrary sibling plan's directory. The `finally` block's `set_usage_metrics_path(None)` (line 150) will prematurely nullify a sibling's path while that sibling is still mid-execution. Dispatcher contamination (lines 109–152) means each `track_activity.jsonl` is polluted with sibling-plan LLM events. Both bugs corrupt observability output silently — plans appear to succeed but metrics and tracking data are wrong.
- **Effort**: Medium. The cleanest fix is to move `set_usage_metrics_path(...)` inside `_file_lock` and hold the lock for the entire duration of the plan run (or switch to a per-thread usage-metrics path mechanism). The dispatcher contamination requires either serializing plan execution for tracking purposes or using per-thread dispatcher instances.
- **Risk**: Medium. Holding the lock for the full plan run would serialize all parallel plans, negating the parallelism benefit. A thread-local usage-metrics path is the better fix but requires changing the global `set_usage_metrics_path` API.

---

### 4. Add anti-copy instruction for the `review_lever` exemplar
- **Type**: prompt change
- **Evidence**: code_codex I2. Confirmed by artifact inspection: the example sentence "This lever governs the tension between centralization and local autonomy, but the options overlook transition costs." appears nearly verbatim in multiple generated outputs (`history/1/60_…`, `history/1/63_…`).
- **Impact**: Template leakage affects content quality across all runs — models copy the example instead of generating lever-specific review text. The result is a `review_lever` field that is meaningless for the actual lever, eroding the credibility of downstream synthesis and scenario generation.
- **Effort**: Low — add one sentence to the field description and system prompt: "Do not copy this example; write a fresh sentence specific to this lever." Optionally supply a second stylistically distinct example to teach the semantic intent rather than a sentence frame.
- **Risk**: Very low. This is additive instruction text. It can be bundled with Direction 1 at no extra cost.

---

### 5. Improve partial-recovery logging and error context (I4)
- **Type**: code fix (observability)
- **Evidence**: code_codex I4. The swallow-and-continue path at `identify_potential_levers.py:305–319` logs a warning but discards which call index failed, which validator rejected it, and the `LLMChatError.error_id`. `runner.py` (line 128–131) only emits an aggregate count.
- **Impact**: Diagnosing prompt regressions currently requires manual inspection of `events.jsonl` and cross-referencing `LLMChatError.error_id` from logs. Emitting the failed call index and error ID into `002-9-potential_levers_raw.json` metadata would make the analysis pipeline's insight and code-review phases much more informative — and would likely have allowed the insight agents to complete within the 600 s budget (less searching).
- **Effort**: Low — add `call_index` and `error_id` to the metadata dict when partial recovery triggers, and include them in `to_dict()` output.
- **Risk**: Very low. Pure additive logging, no behavior change.

---

## Recommendation

**Do Direction 1 first, bundled with Direction 4.**

The root cause of call-1 validation failures for weaker models is that the system prompt section 4 and the `Lever.review_lever` field description disagree with each other *and* with the format actually being produced. PR #316 is directionally correct but incomplete. The fix is:

1. **Remove** "Two sentences. First sentence names the core tension… Second sentence identifies a weakness…" from `Lever.review_lever` (lines 93–95).
2. **Replace** it with a single explicit contract line: "A single sentence naming the core tension this lever governs and one limitation the listed options overlook."
3. **Update** the example to the one from the PR description ("This lever governs the tension between centralization and local autonomy, but the options overlook transition costs.").
4. **Add** "Do not copy this example wording; write a fresh sentence specific to this lever." (Direction 4, zero extra cost).
5. **Update** system prompt section 4 (lines 215–220) with identical wording. Currently it says "For `review_lever` (one field, two sentences): First sentence names the core tension. Second sentence identifies a weakness." — replace with the single-sentence contract and updated example.
6. **Update** `LeverCleaned.review` (lines 186–194) for documentation consistency.

**File**: `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

**Lines to touch**: 92–100 (Lever.review_lever description), 215–220 (system prompt section 4), 186–194 (LeverCleaned.review description).

**Why first**: This is the only change that directly affects call-1 parse failures for weaker models (llama3.1). It is low-effort, low-risk, and addresses the explicit goal of PR #316 while closing the gaps that make the PR incomplete. Directions 2–5 can follow in subsequent iterations; none of them unblock the immediate call-1 failure mode that PR #316 was meant to fix.

---

## Deferred Items

- **Direction 2 (system prompt option bias)**: Fix `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` line 205 to require a conservative option instead of an unconventional one. High content-quality impact but independent of the PR-1 validation failure. Do in the next iteration.

- **Direction 3 (runner.py race conditions)**: Fix `set_usage_metrics_path` call outside lock and dispatcher contamination. Important for observability correctness in multi-worker mode. Requires medium effort and design decision (thread-local path vs. lock-held execution). Defer until the prompt changes are stable.

- **Direction 5 (partial-recovery logging)**: Low effort, pure observability improvement. Bundle with the next code change to runner.py.

- **code_codex B2 (unescaped lever name interpolation)**: Use `json.dumps(generated_lever_names, ensure_ascii=False)` in the follow-up prompt construction (identify_potential_levers.py line 270). Low risk in practice (lever names rarely contain `"` or `]`) but trivial to fix. Bundle with the next prompt-construction touch.

- **code_claude I2 (validator content enforcement)**: `check_review_format` accepts any 20-char string. Consider requiring a minimum word count or sentence boundary (`. `) to catch structurally empty review text. Low priority while the format contract is still being stabilized by Direction 1.

- **code_claude I4 / code_codex I3 (exact-match deduplication)**: Normalize lever names with `casefold()` before set membership checks. Low-cost quality-of-life improvement; defer as it does not affect correctness.

- **code_claude I3 (English-centric example)**: The new example is still English-specific, which OPTIMIZE_INSTRUCTIONS flags as a known problem. Consider adding a note like "respond in the same language as the project context" rather than trying to make the example language-neutral (which would make it less imitable). Medium priority; defer until after Direction 1 is confirmed effective.
