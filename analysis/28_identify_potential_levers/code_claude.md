# Code Review (claude)

Files reviewed:
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `/Users/neoneye/git/PlanExeGroup/PlanExe/self_improve/runner.py`
- PR #340 diff (via prompt snapshot comparison: `prompt_8` = before, `prompt_9` = after)

---

## Bugs Found

**B1 — Template lock not eliminated: examples 1 and 2 still use "The options [verb]" openers**

File: `identify_potential_levers.py`, lines 224–226 (system prompt section 4)

```
- "Switching from seasonal contract labor to year-round employees stabilizes harvest quality, but none of the options price in the idle-wage burden during the 5-month off-season."
- "Routing the light-rail extension through the historic district unlocks ridership but triggers Section 106 heritage review; the options assume permits will clear on the standard timeline."
- "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a regional hurricane season can correlate all three simultaneously — correlation risk absent from every option."
```

Example 2 uses "the options assume" and example 3 (the PR's replacement) ends with "correlation risk absent from every option" — a stylistic variation that still anchors reviews to an "options-centric" critique formula. The raw output confirms this: llama3.1 gta_game run 03 levers 7–16 and all 18 parasomnia levers use "The options [verb]" patterns. Since PR #340 only changed example 3, examples 1 and 2 remain live template-lock sources. The run 05 (gpt-5-nano) output contains `"the options neglect explicit risk hedges"` — this can only be attributed to examples 1 or 2. This is a confirmed bug because the PR's stated goal was to eliminate the template lock, but the root cause (shared "The options" opener structure across multiple examples) was not fully addressed.

**B2 — New fabricated percentage claims introduced by replacement example 3 (PR regression)**

File: `identify_potential_levers.py`, lines 209–210 (system prompt section 2, Consequences) and the replacement example text

The system prompt in section 2 explicitly prohibits "fabricated percentages or cost estimates." The replacement example 3 text added by PR #340 does not itself contain percentages, but the run data shows that llama3.1 first-call levers in run 03 (gta_game) generate "by at least 20%", "by at least 15%", "by at least 25%", "by at least 30%", "by at least 20%" — a pattern entirely absent from run 96 (before the PR). Run 96 had zero fabricated % claims in consequences; run 03 has 5. The structural change in the replacement example (longer, more complex text including a quantitative causal chain "but a regional hurricane season can correlate all three simultaneously") appears to cue llama3.1 into a mode of writing causal consequence sentences that conclude with a magnitude claim. This is a regression introduced by PR #340 and is directly inconsistent with the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers.

Evidence: `history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 1–6 consequences fields.

**B3 — Case-sensitive exact-name deduplication misses semantic and typo duplicates**

File: `identify_potential_levers.py`, lines 331–337

```python
seen_names: set[str] = set()
for i, lever in enumerate(levers_raw, start=1):
    if lever.name in seen_names:
        logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
        continue
    seen_names.add(lever.name)
```

The deduplication check uses exact string equality on `lever.name`. Run 03 (llama3.1, gta_game) produced both `"Multplayer Modes"` (lever 5, typo) and `"Multiplayer Modes"` (lever 9) — semantically the same lever, different names. Neither is caught by the `in seen_names` check because the strings are not identical. Both pass through to the cleaned output and then to the downstream `DeduplicateLeversTask`. While the downstream task is the intended deduplication point, the upstream deduplication logic's log message ("Duplicate lever name ... skipping") implies it is meant to catch at least obvious duplicates. In practice it only catches byte-for-byte identical names, which rarely occur because the multi-call prompt already instructs the model not to reuse exact names.

**B4 — options list capped at exactly 3 in field description but validator only enforces minimum of 3**

File: `identify_potential_levers.py`, lines 99–101 and 125–137

The `Lever.options` field description says "Exactly 3 options ... No more, no fewer." The `check_option_count` validator enforces `len(v) < 3` but accepts any count >= 3. A model producing 4 or 5 options passes validation silently. This is a contradiction between the stated schema contract ("No more, no fewer") and the actual enforcement (no upper-bound check). While the comment on lines 128–133 explains the intent (over-generation is tolerable, under-generation is not), the field description is misleading and will cause models to believe they must produce exactly 3, when in fact the code accepts 4+. If the intent is "at least 3", the description should say so. If the intent is "exactly 3", an upper-bound check is missing. The current state sends conflicting signals to both the model and the developer.

---

## Suspect Patterns

**S1 — Multi-call context accumulation re-establishes old template**

File: `identify_potential_levers.py`, lines 268–321

Each call is a fresh `[system_message, user_message]` pair — there is no chat history carried across calls. However, the second and third call user messages include the already-generated lever names:

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```

The names list itself is short and doesn't include the prior lever content. This means each call sees the system prompt's examples cold and independently produces template-locked reviews. The observed behavior — first call uses a slightly different pattern, subsequent calls revert to the canonical "The options [verb]" lock — is consistent with the examples in the system prompt being the sole template source (not accumulated context). This rules out context accumulation as the root cause but confirms the system prompt examples alone drive the lock in every call independently.

**S2 — `execute_function` closure over `messages_snapshot` in a loop**

File: `identify_potential_levers.py`, lines 288–298

```python
messages_snapshot = list(call_messages)

def execute_function(llm: LLM) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(messages_snapshot)
    ...
```

`execute_function` is a closure that captures `messages_snapshot` from the enclosing loop scope. In Python, closures capture variables by reference, but since `messages_snapshot` is reassigned (not mutated) each iteration, this is safe here because `llm_executor.run(execute_function)` is called synchronously before the next iteration begins. If `llm_executor.run` were ever made asynchronous or deferred, all calls would use the last `messages_snapshot`. The pattern is technically safe today but fragile under future changes.

**S3 — `generated_lever_names` accumulates across failed calls**

File: `identify_potential_levers.py`, lines 266, 321

```python
generated_lever_names: list[str] = []
...
generated_lever_names.extend(lever.name for lever in result["chat_response"].raw.levers)
```

This line is only reached on success (it follows the `continue` in the exception handler). So failed calls do not pollute the exclusion list. This is correct, but the logic is non-obvious: there is no explicit separation between "names accumulated so far" and the `responses` list. A future refactor that moves line 321 before the `responses.append` would break the invariant that names only include successful call output.

**S4 — `_resolve_workers` silently returns 1 on any config miss**

File: `runner.py`, lines 230–260

If a model name is not found in any `llm_config/*.json` file, the function returns 1 (single-threaded). There is no warning logged. A user who typoes a model name in `llm_config/` gets sequential execution without notification. This is a silent degradation, not a crash, but could cause unexpectedly slow runs.

**S5 — Thread-safety issue with `dispatcher.event_handlers.remove`**

File: `runner.py`, lines 146–148

```python
with _file_lock:
    set_usage_metrics_path(None)
    dispatcher.event_handlers.remove(track_activity)
```

The `_file_lock` guards `set_usage_metrics_path` and `dispatcher.event_handlers.remove` together. If the `llama_index` dispatcher's `event_handlers` is itself a list that is iterated by other threads between the lock acquisition points, this could still be unsafe depending on the dispatcher's internal thread model. The lock here serializes the PlanExe-level setup/teardown but does not protect against the dispatcher's own concurrent event dispatch. This is a suspect pattern rather than a confirmed bug — depends on `llama_index`'s internal thread safety.

---

## Improvement Opportunities

**I1 — Replace examples 1 and 2 in section 4 with non-"options-centric" openers**

File: `identify_potential_levers.py`, lines 224–225

Example 2 ("the options assume permits will clear on the standard timeline") uses "the options assume", which is structurally identical to the template lock pattern models reproduce. Example 1 ("none of the options price in the idle-wage burden") also anchors to the options as the subject of the critique. Both should be rewritten to name a stakeholder, a system condition, or a domain-specific constraint as the subject — not "the options". The existing comment in OPTIMIZE_INSTRUCTIONS (lines 73–79) describes this correctly: "The agriculture example ... is the correct structural template: its critique is domain-specific and non-portable." However example 1 IS the agriculture example and it still uses "none of the options" as the negative anchor. The fix requires removing "The options [verb]" and "none of the options" from ALL three examples, not just from example 3's opener.

**I2 — Remove or qualify "exactly 3" in field description to match validator behavior**

File: `identify_potential_levers.py`, line 100

The `Lever.options` field description says "Exactly 3 options for this lever. No more, no fewer." This conflicts with the validator which only enforces a minimum of 3. Since the OPTIMIZE_INSTRUCTIONS comment on lines 161–163 explicitly says over-generation is fine and a hard cap wastes tokens, the field description should be updated to say "At least 3 options" or "3 or more options". Models read the field description via structured output schema serialization and will attempt to comply with "Exactly 3, no more".

**I3 — Fuzzy deduplication before the cleaned output**

File: `identify_potential_levers.py`, lines 331–337

Add a basic normalized-name comparison (lowercase, strip punctuation, collapse whitespace) before the `in seen_names` check. This would catch "Multplayer Modes" vs "Multiplayer Modes" and similar typo variants. The downstream `DeduplicateLeversTask` handles semantic duplicates, but near-exact name matches with minor edits are cheaper to catch here. A simple approach: normalize each name with `re.sub(r'[^a-z0-9 ]', '', name.lower()).strip()` and check against a set of normalized names.

**I4 — Log a warning when `_resolve_workers` finds no matching config**

File: `runner.py`, lines 230–260

When none of the supplied model names appear in any `llm_config/*.json` file, emit a warning:
```python
logger.warning("No luigi_workers found for %s — defaulting to 1 worker", model_names)
```
This turns a silent performance degradation into a visible diagnostic.

**I5 — Add OPTIMIZE_INSTRUCTIONS entries for the two new patterns discovered in analysis 28**

File: `identify_potential_levers.py`, lines 27–80

Two patterns confirmed in runs 03–09 are not yet documented:
1. "Multi-call template divergence": the first LLM call in a 3-call loop may produce a different review format than subsequent calls because subsequent calls carry accumulated lever names that implicitly re-establish the old template context. Document that when prompt changes partially break a lock, the fix must apply to all calls, not just the first.
2. "Replacement-example contamination": when replacing a template-locking example, verify the replacement text does not introduce a new leakage pattern in a different field (e.g., percentage claims in `consequences`). Confirmed in run 03 gta_game levers 1–6 with 5 fabricated % claims in consequences.

---

## Trace to Insight Findings

| Insight finding | Code location | Explanation |
|---|---|---|
| 1. "The options [verb]" template lock | `identify_potential_levers.py` L224–226 — all 3 system prompt examples use "the options" or "none of the options" as the critique subject | Examples 1 ("none of the options price in"), 2 ("the options assume"), and the old example 3 ("the options neglect") all share the same opening structure. PR #340 only changed example 3, leaving examples 1 and 2 intact. |
| 2. Fabricated % claims after PR #340 (llama3.1 levers 1–6) | `identify_potential_levers.py` L209 — system prompt section 2 says "Do not fabricate percentages or cost estimates" | The prohibition exists but is overridden in first-call output. The replacement example 3 (PR #340) introduces a complex causal sentence structure that may cue llama3.1 into ending consequence sentences with magnitude claims. The prohibition is not reinforced with an explicit example of correct consequences text. |
| 3. gpt-oss-20b JSON truncation failure (EOF at line 58) | `identify_potential_levers.py` L291–292 — `sllm.chat(messages_snapshot)` | The structured LLM chat call has no maximum-output-token guard at this layer. If gpt-oss-20b's output token limit is exhausted mid-JSON, the response is truncated and Pydantic raises `json_invalid`. There is no retry-with-fewer-levers fallback. |
| 4. Multi-call pattern divergence (call 1 vs calls 2–3) | `identify_potential_levers.py` L268–278 — fresh `[system, user]` pair per call | Each call is independent (no conversation history). The second/third call's prompt_content includes accumulated lever names but not accumulated lever text, so the system prompt's examples drive the template independently for every call. Call 1's slightly different format in run 03 is caused by the prompt_content difference (original user prompt vs "Generate MORE..."), not accumulated context. |
| 5. Duplicate lever names ("Multplayer Modes" / "Multiplayer Modes") | `identify_potential_levers.py` L335 — exact string equality check | The deduplication guard uses `lever.name in seen_names`, which requires byte-for-byte identical names. Typo variants and near-matches pass through. |
| 6. Partial recovery events (2/3 calls succeeding) | `identify_potential_levers.py` L313–318 — continue logic after exception | The code intentionally continues on failure if `len(responses) > 0`. The runner correctly records `calls_succeeded` and emits `partial_recovery` events. The insight is accurately explained by the existing code behavior. |

---

## PR Review

**PR #340: "fix: remove template-lock phrase and deduplicate examples"**

The PR makes two changes:
1. **B1 (example 3 replacement)**: The old example 3 contained "the options neglect". The new example 3 is: "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a regional hurricane season can correlate all three simultaneously — correlation risk absent from every option."
2. **B2 (duplicate example removal)**: The review_lever examples that were duplicated in the `Lever.review_lever` Pydantic field description were removed, leaving examples only in the system prompt.

### Does the implementation match the intent?

**B2 — Yes.** Comparing `prompt_8` (before) and `prompt_9` (after): the `prompt_9` Lever field description no longer contains the examples — they appear only in section 4 of the system prompt. This is verified by the prompt text files. Token savings are confirmed (insight_claude.md: `input_tokens: 6433` for llama3.1 parasomnia). Consequences contamination in llama3.1 is resolved in run 03. B2 is a clean, verified improvement with no detected downside.

**B1 — Partially.** The PR description says the goal is to "remove the lockable phrase 'the options neglect'" and fix the "llama3.1 secondary template lock (100% gta_game, 92% parasomnia)." The actual outcome:
- gta_game lock rate: 100% → 62.5% (partial improvement)
- Parasomnia lock rate: 92% → 100% (unchanged / marginally worse)
- "the options neglect" persists in gpt-5-nano run 05 (sourced from examples 1 or 2)
- The replacement example 3 text itself ends with "correlation risk absent from every option" — a semantically equivalent "options-centric" critique that still models the same style

The PR did not achieve its stated goal of fixing the template lock. The root cause — all three examples using "the options" or "none of the options" as the critique subject — was not addressed. Only the most recently flagged example was changed.

### Bugs or gaps in the PR itself

**Gap 1 — Replacement example 3 still anchors to "options" as critique subject.** The old example 3 said "the options neglect". The new example 3 ends with "correlation risk absent from every option." Both critique the options. Weaker models will still learn from this that reviews should discuss what the options fail to capture.

**Gap 2 — Example 2 uses "the options assume" — not changed.** This phrase is the direct source of the persistent "The options assume..." pattern seen in run 03 parasomnia levers. Example 2's opener was not audited as part of PR #340.

**Gap 3 — No check that replacement example text is free of fabricated quantities.** The new example 3 text does not contain explicit percentages, but the run data shows llama3.1 generated "by at least 20%" etc. in first-call consequences after the PR. The causal sentence style introduced in example 3 may be the trigger. The PR lacked a test for this.

**Gap 4 — The `OPTIMIZE_INSTRUCTIONS` "Template-lock migration" note (lines 73–79) describes exactly what happened here.** The note says: "Replacing a copyable opener does not eliminate template lock — weaker models shift to copying subphrases within the new examples." This warning was already in the codebase before the PR. The PR's example 3 replacement was made without verifying that the new text satisfies the structural requirement described in lines 78–79 ("its critique is domain-specific and non-portable"). The new example 3's closing clause ("correlation risk absent from every option") is domain-portable and was predictably copied.

### New issues introduced by the PR

1. **Fabricated % claims in llama3.1 first-call consequences (run 03 gta_game, 5 instances).** These are absent in run 96 (before PR). Likely caused by the replacement example 3's causal structure cuing a magnitude-claim pattern in llama3.1. This is a regression against the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers.

2. **Lock displacement, not elimination.** The 62.5% gta_game rate hides the structure: first call (levers 1–6) shifted to "[Lever name] lever [verb]" — itself a new template. Calls 2 and 3 (levers 7–16) are still at close to 100% "The options [verb]". The PR moved where the lock occurs within the call sequence without eliminating it.

---

## Summary

**B2 (duplicate example removal) is a confirmed improvement** with no regressions. It reduces per-call token cost by ~150–200 tokens, removes doubled template-lock signal, and likely contributed to eliminating the `consequences` contamination bug seen in run 96 llama3.1.

**B1 (example 3 replacement) is a partial fix** that introduces a new regression. The template lock was reduced for gta_game's first LLM call (100% → 62.5%) but is unchanged for parasomnia (92% → 100%). The phrase "the options neglect" was removed from example 3, but equivalent phrases in examples 1 and 2 ("none of the options price in", "the options assume") remain as live template sources — confirmed by gpt-5-nano run 05 still producing "the options neglect". Additionally, the replacement example 3 introduced or exacerbated fabricated % claims in llama3.1 consequences (5 instances in run 03 gta_game vs 0 before).

**The core structural problem** — all three `review_lever` examples use "the options" or "none of the options" as the critique's grammatical subject — was not addressed. The OPTIMIZE_INSTRUCTIONS constant at line 73 already documents this failure mode ("Template-lock migration: replacing a copyable opener does not eliminate template lock"). The PR changed one example without auditing whether the remaining two examples contain the same pattern.

**Recommended follow-up actions:**
1. Audit examples 1 and 2 for "The options [verb]" and "none of the options" openers and replace with domain-specific, non-portable critique subjects (named stakeholders, named constraints, named failure conditions).
2. Verify the replacement example 3 does not contain percentage claims or causal sentence structures that cue fabricated magnitude claims in `consequences`.
3. Update `OPTIMIZE_INSTRUCTIONS` with the two new documented patterns: multi-call template divergence and replacement-example contamination.
4. Fix the `Lever.options` field description (line 100) to say "At least 3 options" rather than "Exactly 3, no more, no fewer", aligning the description with the actual validator behavior.
