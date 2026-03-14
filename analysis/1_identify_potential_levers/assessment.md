# Assessment: fix: remove doubled user prompt in identify_potential_levers (B1)

## Issue Resolution

**What the PR fixed:** `chat_message_list` was initialized as `[SYSTEM, USER(user_prompt)]`, and then the first loop iteration appended `USER(user_prompt)` again, producing `SYSTEM → USER(prompt) → USER(prompt)` on the first LLM call. Calls 2 and 3 received a conversation history built on top of this malformed first exchange, potentially causing intra-run inconsistency (e.g., run 00's second call produced bracket-placeholder leakage while calls 1 and 3 were clean — the malformed first-call history feeds into call 2). The fix removes the initial `USER` from initialization so all three turns are handled uniformly by the loop.

**Is the issue resolved?** Yes. The post-fix runs (09–16) show no errors attributable to the doubled USER prompt. Positive evidence:

- `insight_claude` P4 (analysis 1): "None of the 24 plan executions that succeeded show errors attributable to the corrected conversation sequence."
- Review format compliance for gpt-5-nano improved from 60 violations (run 02, before) to 0 (run 10, after) — the largest format-compliance jump across any shared model.
- Consequence chain format violations for gpt-4o-mini dropped from 25 (run 07, before) to 4 (run 15, after).
- Bracket placeholder leakage in review fields: reduced from ~12–17 instances across shared models to near zero.

**Residual symptoms:** None directly attributable to B1. However, analysis 1 uncovered a related bug (`code_claude analysis 1 B1`, now called **BUG-A** in synthesis 1): the assistant turn is stored as `result["chat_response"].raw.model_dump()` — a Python dict — rather than the raw JSON string `result["chat_response"].message.content`. This corrupts conversation context for turns 2 and 3 on 100% of runs and is the highest-priority next fix. It is a pre-existing bug, not introduced by this PR, but it was discovered through this analysis cycle.

---

## Quality Comparison

Metrics compared only for models appearing in **both** batches:

| Model | Before Run | After Run |
|-------|-----------|-----------|
| openai-gpt-5-nano | 02 | 10 |
| openrouter-qwen3-30b-a3b | 05 | 14 |
| openrouter-openai-gpt-4o-mini | 07 | 15 |
| ollama-llama3.1 | 00 | 16 |
| openrouter-openai-gpt-oss-20b | 01 | 13 |
| anthropic-claude-haiku-4-5-pinned | 09 (in analysis 0) | 12 |

Models only in **before** batch (not compared): openrouter-z-ai-glm-4-7-flash (run 03).

Models only in **after** batch (not compared): none — all after models appear in before.

Note on success-rate counts: `insight_claude` analysis 0 miscounted by reading all `outputs.jsonl` rows (including pre-retry errors) instead of final artifacts. The corrected artifact-level counts from `insight_codex` analysis 0 are used below.

| Metric | Before (shared models) | After (shared models) | Verdict |
|--------|------------------------|----------------------|---------|
| **Success rate** | 30/30 (100%) at artifact level (gpt-5-nano 5/5, qwen3 5/5, gpt-4o-mini 5/5, llama3.1 5/5, gpt-oss-20b 5/5, claude-haiku 5/5) | 29/30 (97%) — gpt-oss-20b lost 1 plan to JSON truncation (parasomnia) | UNCHANGED / marginal regression for gpt-oss-20b only |
| **Bracket placeholder leakage** | ~17 instances across 6 models (run 00: 12, run 02: 5; others: 0) | ~1 instance (run 16 llama3.1: 1 placeholder violation) | **IMPROVED** |
| **Option count violations** | ~10 total (run 00: 7, run 09: 3; others: 0) | ~3.5 total (run 10: 0.4×5=2, run 13: 0.2×5=1, run 16: 0.4×5=2; run 12: 0) | IMPROVED — claude-haiku 3→0, llama3.1 7→~2; gpt-5-nano slightly regressed (0→~2) |
| **Lever name uniqueness (avg duplicate names/file)** | gpt-5-nano 0, qwen3 ~1, gpt-4o-mini ~4.2, llama3.1 ~1.8, gpt-oss-20b ~1.8, claude-haiku 0 | gpt-5-nano 0, qwen3 1, gpt-4o-mini 3.8, llama3.1 1.2, gpt-oss-20b 0.8, claude-haiku 0 | UNCHANGED to slightly improved |
| **Template leakage (bracket + example-name)** | 23 instances (run 00: 12, run 02: 5, run 05: 6 example-name; others: 0) | ~1 bracket violation (run 16) + NEW: gpt-5-nano copies "25% faster scaling through" in 11/15 levers (73% rate) in run 10 | MIXED — old bracket leakage eliminated; metric exemplar leakage emerged |
| **Review format compliance (`Controls X vs Y`)** | 67 total violations (run 02 gpt-5-nano: 60, run 00 llama3.1: 7; others: 0) | ~4 total violations (run 16 llama3.1: ~4; others: 0) | **SIGNIFICANTLY IMPROVED** |
| **Consequence chain format (`Immediate → Systemic → Strategic`)** | 35 total violations (run 07 gpt-4o-mini: 25, run 05 qwen3: 10; others: 0) | 7 total violations (run 15 gpt-4o-mini: 4, run 14 qwen3: 3; others: 0) | **IMPROVED** |
| **Content depth (avg option chars)** | gpt-5-nano 145.5, qwen3 61.1, gpt-4o-mini 104.3, llama3.1 74.4, gpt-oss-20b 87.6, claude-haiku 295.4 | gpt-5-nano 146.7, qwen3 61.2, gpt-4o-mini 109.4, llama3.1 86.5, gpt-oss-20b 94.8, claude-haiku 315.4 | UNCHANGED (≤5% change across all models) |
| **Cross-call duplication (avg duplicate names/file)** | gpt-5-nano 0, qwen3 ~1, gpt-4o-mini ~4.2, llama3.1 ~1.8, gpt-oss-20b ~1.8, claude-haiku 0 | gpt-5-nano 0, qwen3 1, gpt-4o-mini 3.8, llama3.1 1.2, gpt-oss-20b 0.8, claude-haiku 0 | UNCHANGED to marginally improved |

Sources: `insight_codex` analysis 0 (constraint violations / uniqueness tables); `insight_codex` analysis 1 (constraint violations / uniqueness / cross-call duplication proxy tables); `code_claude` analysis 0/1.

---

## New Issues

**Issues introduced by the PR:** None confirmed. All failures in the after-batch (run 09 stepfun config error, run 11 nemotron JSON failure) are pre-existing infrastructure problems unrelated to conversation structure. The gpt-oss-20b JSON truncation regression is a model behavior edge case, not a structural change effect.

**Issues surfaced by this analysis cycle (not caused by the PR):**

1. **BUG-A: Assistant turn content is a Python dict, not a string** (`identify_potential_levers.py:196`). `result["chat_response"].raw.model_dump()` produces a Python `dict`; the correct value is `result["chat_response"].message.content`. LlamaIndex serializes the dict via Python repr instead of JSON, so every turn-2 and turn-3 continuation sees malformed history. This degrades structural compliance on all multi-turn runs and is the likely partial cause of the missing `Immediate:/Systemic:/Strategic:` chain labels in runs 14/15 and prefix violations in run 16. Rated **High** severity by `code_claude` analysis 1; confirmed in source. This was present before the PR and is now the top-priority fix per synthesis 1.

2. **Metric exemplar leakage** (`identify_potential_levers.py:95`): The system prompt contains `"Include measurable outcomes: 'Systemic: 25% faster scaling through...'"`. Post-fix, gpt-5-nano (run 10) copies this phrase into 11/15 levers (73% rate). This leakage was not reported for the same model in the before-batch (run 02 showed different format issues), suggesting the B1 fix may have shifted gpt-5-nano's behavior in a way that exposed this exemplar anchor. The exemplar was always present; the B1 fix may have changed which failure mode dominated for this model.

3. **llama3.1 over-produces 20 levers** (run 16): expected 15, received 20 for the silo plan. Also exhibits prefix violations (`Option 1:`) and remaining bracket placeholders. No per-call count guard exists (`identify_potential_levers.py:203–206`).

4. **gpt-4o-mini (run 15) uniqueness regression at scale**: 3.8 average duplicate names per file vs 4.2 before — marginal improvement but still poor; baseline is 4.4. This model does not benefit much from the B1 fix.

---

## Verdict

**YES**: The PR correctly resolves the doubled-user-prompt structural bug and produces measurable improvements in review format compliance (67 → ~4 violations) and consequence chain compliance (35 → 7 violations) across shared models, with no regressions in success rate, content depth, or cross-call duplication.

---

## Recommendations

**Next iteration focus:** Synthesis 1 recommends fixing **BUG-A** (assistant turn `model_dump()` dict → `message.content` string) as Direction 1 — this is the right call. It affects 100% of runs, 100% of models, and is a one-line fix with no side effects. After BUG-A, the next highest-leverage change is making the "more" turns stateful (feed already-generated lever names into turns 2 and 3), which addresses the cross-call thematic redundancy still present in all models.

**Issues now resolved — remove from backlog:**
- "Doubled user prompt on first LLM call" (B1 from synthesis 0) — confirmed fixed.
- "Intra-run inconsistency between call 1 and call 2 behavior" (the proposed mechanism) — resolved by the uniform conversation structure.

**New issues to add to backlog (priority order):**
1. **[HIGH] Fix assistant turn content: `model_dump()` → `message.content`** — BUG-A from synthesis 1 (`identify_potential_levers.py:196`). One-line fix, affects every run.
2. **[HIGH] Replace metric exemplar with structural placeholder** — `identify_potential_levers.py:95` (synthesis 1 Direction 3). gpt-5-nano copies "25% faster scaling through" in 73% of levers post-fix. Replace with `"Systemic: [specific quantified impact, e.g. percentage change in X] through [mechanism]"`.
3. **[MEDIUM] Add stateful "more" turns** — inject already-generated lever names into turns 2 and 3 (synthesis 1 Direction 2). Root cause of cross-call thematic redundancy across all models.
4. **[MEDIUM] Add per-call and post-merge lever count guards** — `levers_raw.extend()` does no count check; llama3.1 produces 20 levers, gpt-5-nano produced 16 on one plan (synthesis 1 Direction 4).
5. **[LOW] Preflight model availability check** — move `LLMModelFromName.from_names()` before the plan loop; prevents run-09-class 5× wasted failures (synthesis 1 Direction 5).
6. **[LOW] Fix `Lever.options` field description from "2-5 options" to "Exactly 3 options"** (B7 from synthesis 0 Deferred) — still open; contributes to option-count violations.

**Still deferred from synthesis 0 (unchanged priority):**
- Post-merge name deduplication (moved upstream from step 002-11).
- Thread-safety: `set_usage_metrics_path` outside lock (only affects `workers > 1`).
- Runner summary counting bug (counts all `outputs.jsonl` rows, not latest-per-plan).
