# Assessment: feat: batch categorical dedup — single call + primary/secondary/remove

## Issue Resolution

**What PR #374 was supposed to fix:**
PR #374 combines the single-batch architecture from PR #373 with the categorical primary/secondary/remove schema from PR #372, adding prompt fixes from iter 49 (B2, B3, S1) and robustness guards from the iter 50 assessment (duplicate lever_id detection, minimum count check, per-lever fallback).

**Is the issue resolved?**

**Issue 1 — Deduplication failure (PR #373 kept 0 removes for all capable models):** FIXED.
In the after runs (PR #374), 6 of 7 models remove 1–6 levers per plan via the categorical `remove` classification. Example: run 65 (gpt-oss-20b, hong_kong_game) removed 6 levers with explicit lever-ID citations. Run 70 (haiku, silo) removed 3 levers including ee0996f6 (Information Dissemination Protocol) citing overlap with b664e24a (Information Control Protocols). Run 65 (gpt-oss-20b, silo) removed 5 levers including f14b8361, 9bc93565, ee0996f6, 36621fe3, 19e66d20. In the before (PR #373), gpt-oss-20b removed 0 levers on silo (all 18 scored ≥ 1 on Likert).

**Issue 2 — llama3.1 catastrophic scale inversion (PR #373 kept 1/18 on silo/gta_game):** SUBSTANTIALLY IMPROVED.
The scale-inversion failure mode is eliminated — there is no numeric scale to invert in the categorical schema. llama3.1 now either produces plausible output (gta_game: 17/18 kept, 1 proper remove) or hits a 120s timeout and triggers the robustness fallback (silo, parasomnia: 18/18 promoted to "primary"). The fallback is lossy but safe — downstream steps receive 18 levers rather than 1.

**Issue 3 — Speed (preserve 18× call reduction from PR #373):** PRESERVED.
All after runs show `calls_succeeded: 1` per plan. Single-call architecture is maintained.

**Issue 4 — Prompt fixes from iter 49 (B2, B3, S1):** ADDRESSED.
The new system prompt includes "compare them against each other before making decisions" and "When two levers overlap, remove the more specific one and keep the more general one." These address the iter 49 issues in the categorical system prompt.

**Issue 5 — Robustness guards:** IMPLEMENTED.
- Duplicate lever_id detection: present (seen_ids set check, first entry wins).
- Minimum count check: present (`max(3, N//4)` threshold, warning logged).
- Per-lever fallback: present ("Not classified by LLM. Keeping as primary to avoid data loss.").

**Residual symptoms:**
- llama3.1 still fails for 2/5 plans (timeout → all-primary fallback). The 120s `request_timeout` in the llm_config is the proximate cause.
- gpt-oss-20b missed lever dcb03988 (Cultural Authenticity) in hong_kong_game — fallback applied silently.
- Silent failure masking: when the LLM call times out, `outputs.jsonl` still records `status="ok"` and `calls_succeeded=1` (B1, B3 from code review).
- No structured event is emitted when the fallback fires (B4).
- `user_prompt` field in `_raw.json` stores `project_context` (the plan description) rather than the full assembled prompt including the levers JSON (B2).

---

## Quality Comparison

Models shared across both batches: ollama-llama3.1, openrouter-openai-gpt-oss-20b, openai-gpt-5-nano, openrouter-qwen3-30b-a3b, openrouter-openai-gpt-4o-mini, openrouter-gemini-2.0-flash-001, anthropic-claude-haiku-4-5-pinned (all 7 models appear in both runs 57–63 and 64–70).

Note: the baseline/train directory contains only .gitkeep — no baseline training data exists for field-length ratio comparison. Field-length metrics are therefore reported qualitatively from sampled outputs.

| Metric | Before (PR #373, runs 57–63) | After (PR #374, runs 64–70) | Verdict |
|--------|------------------------------|------------------------------|---------|
| Structural success rate | 35/35 | 35/35 | UNCHANGED |
| LLMChatErrors | 0 | 0 | UNCHANGED |
| LLM calls per plan | 1 (batch) | 1 (batch) | UNCHANGED |
| Deduplication schema | Likert -2 to +2 | primary/secondary/remove | IMPROVED |
| Avg removes — capable models, silo (gpt-oss-20b, haiku, gemini) | 0% (0/18 each) | 6–28% (1–5/18) | IMPROVED |
| Avg removes — capable models, hong_kong_game | 0% | 22–33% (4–6/18) | IMPROVED |
| Remove justifications cite overlapping lever IDs | N/A (no removes) | Yes — all sampled removes cite the lever absorbed | IMPROVED |
| llama3.1 silo output | 1/18 kept (scale inversion) | 18/18 primary (timeout fallback) | IMPROVED |
| llama3.1 plans producing degraded output | 2/5 (catastrophic: 1 lever) | 2/5 (lossy: 18 fallback primaries) | IMPROVED |
| Primary/secondary distinction grounded | Weak (score → label mapping) | Yes — capable models cite plan-specific reasoning | IMPROVED |
| Robustness guard (min count, duplicate lever_id, per-lever fallback) | Absent | Present | IMPROVED |
| gpt-4o-mini silo duration | 20.4s | 41.6s | REGRESSED (~2×) |
| gemini silo duration | 11.2s | 12.7s | UNCHANGED |
| haiku silo duration | 24.3s | 23.0s | UNCHANGED |
| gpt-oss-20b silo duration | 51.0s | 42.1s | IMPROVED (~16%) |
| Silent failure masking (LLM timeout looks like success) | Present | Present | UNCHANGED |
| `user_prompt` field stores correct assembled prompt | No (Likert: stored score field; assessed separately) | No (stores project_context, not full prompt) | UNCHANGED — different bug, same severity |
| `calls_succeeded` reflects actual LLM success | No (hardcoded 1) | No (hardcoded 1) | UNCHANGED |
| classification_fallback events in events.jsonl | N/A | Absent | UNCHANGED (missing) |
| Bracket placeholder leakage `[...]` | 0 observed | 0 observed | UNCHANGED |
| Option count violations (≠ 3 options) | 0 observed | 0 observed | UNCHANGED |
| Template leakage (verbatim prompt copying) | 0 observed | 0 observed | UNCHANGED |
| Fabricated quantification (% estimates in justifications) | 0 observed | 0 observed | UNCHANGED |
| Marketing-copy language in justifications | 0 observed | 0 observed | UNCHANGED |
| Inter-model classification variance (same lever, different models) | Low (all models keep all levers) | High (e.g., Technology Integration: primary vs remove) | NEW VISIBILITY (variance was hidden before) |
| Field length vs baseline | Baseline empty — cannot measure | Baseline empty — cannot measure | N/A |

**OPTIMIZE_INSTRUCTIONS alignment check:**
The `deduplicate_levers.py` OPTIMIZE_INSTRUCTIONS documents "Blanket-primary", "Over-inclusion", "Hierarchy-direction errors", "Chain absorption", and "Calibration capping" as known problems. PR #374 partially addresses:
- Blanket-primary: the system prompt says "Expect to remove 25–50% of input levers." Capable models achieve 6–33% removal (below target, but no longer 0%). llama3.1 fallback produces blanket-primary on 2/5 plans.
- Hierarchy-direction errors: the system prompt says "When two levers overlap, remove the more specific one and keep the more general one." Sampled removes are correctly directed (e.g., Security Force Structure removed in favor of Security System Governance).
- Over-inclusion: still observed for most models (6–33% removal vs 25–50% target). The system prompt calibration guidance may not be strong enough.

The `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS warns against "Do NOT add explicit prohibitions naming banned phrases." The before code review (S1) noted that the `Lever.consequences` field description in identify_potential_levers.py names "Controls ... vs." and "Weakness:" — contradicting this guidance. This was not changed in PR #374 (it is in the upstream step), but it remains in the backlog.

---

## New Issues

**N1 — `user_prompt` field in `_raw.json` stores `project_context` instead of the full assembled prompt.**
The variable `user_prompt` (the full prompt including the levers JSON) is in scope at line 272 of `deduplicate_levers.py`, but `project_context` (the plan description only) is passed to the result constructor. This makes it impossible to reconstruct the exact LLM input from the saved artifact. Present in all 35 after runs. (Code review B2.)

**N2 — gpt-4o-mini silo duration doubled (~2×) compared to PR #373.**
On the silo plan: 20.4s (PR #373) → 41.6s (PR #374). Likely due to longer categorical justification responses vs. terse Likert scores. Does not affect other plans significantly (other models show comparable or faster times). Acceptable tradeoff for deduplication quality.

**N3 — Inter-model classification variance is now visible but was previously hidden.**
Under PR #373, all capable models kept all levers, so variance in classification judgment was masked. Under PR #374, models disagree substantially on some levers (e.g., hong_kong_game: "Technology Integration" is primary for llama3.1/gpt-oss-20b, `remove` for haiku). This is a latent issue surfaced by the PR rather than a new regression. The "gating the core outcome" criterion is subjective and models apply it inconsistently.

**N4 — Robustness fallback masks total LLM failure as success (surfaced, not introduced).**
When llama3.1 times out on silo/parasomnia, the robustness fallback assigns "Not classified by LLM. Keeping as primary to avoid data loss." to all 18 levers, and `outputs.jsonl` records `status="ok"` and `calls_succeeded=1`. This was also true under PR #373 (different failure mode, same silent masking). The PR did not introduce this — it surfaced it by making llama3.1 time out rather than invert the scale.

---

## Verdict

**YES**: PR #374 is a clear keeper. It restores meaningful deduplication (0% → 6–33% removal rate for capable models) with auditable lever-ID-citing justifications, eliminates the catastrophic 1-lever output failure mode from PR #373, and preserves the 18× call reduction in speed. The minor regressions (gpt-4o-mini ~2× slower on silo, llama3.1 timeout fallback instead of scale inversion) do not outweigh the significant improvement in deduplication quality for 6 of 7 models.

---

## Recommended Next Change

**Proposal:** Fix the silent failure path in `deduplicate_levers.py` and `runner.py` so that LLM timeouts and partial classification misses are visible in `outputs.jsonl` and `events.jsonl`. Bundle with the one-line `user_prompt` field fix and a config change to increase llama3.1's request timeout from 120s to 240s.

**Evidence:** The synthesis cites three clustered fixes (directions 1+3+2):
- B2: `user_prompt=project_context` at `deduplicate_levers.py:272` — should be `user_prompt=user_prompt`. One-line fix, zero risk.
- B1+B3: when the LLM call fails, `batch_result` stays `None`, all 18 levers get the fallback, but `outputs.jsonl` shows `status="ok"` and `calls_succeeded=1`. This inflates the 35/35 success metric — the true success rate for PR #374 is 33/35 (94%) for llama3.1's two timeout runs. Fix: expose an `llm_call_succeeded: bool` flag from `DeduplicateLevers.execute()`, read it in `_run_deduplicate()` to set `status="degraded"` and `calls_succeeded=0`.
- B4: no `classification_fallback` event is emitted to `events.jsonl` when the fallback fires. The analysis pipeline cannot programmatically distinguish clean runs from degraded ones without scanning every `_raw.json`. Fix: emit a structured event with fields `plan_name`, `fallback_count`, `cause` (`"llm_failed"` or `"lever_missing"`).
- I4 (config): llama3.1 silo and parasomnia hit exactly 120s, the `request_timeout` in the ollama llm_config. Increasing to 240s would likely allow both plans to complete with real categorical output, as gta_game (which completes at ~65–90s) shows llama3.1 can produce valid primary/secondary/remove output when given enough time.

The synthesis correctly identifies the measurement fidelity problem: with B1+B3 unresolved, future iterations will compare against an inflated 35/35 baseline rather than the accurate 33/35.

**Verify in next iteration:**
- llama3.1 silo and parasomnia: confirm runs complete within 240s and produce real classifications (not fallbacks). Measure how many levers are removed.
- llama3.1 gta_game: verify that the 1-remove result observed in run 64 is stable or improves when the model is no longer racing against timeout pressure.
- gpt-oss-20b hong_kong_game: verify that the missing-lever (dcb03988) issue is isolated or recurring. Check whether the `post-response lever_id` verification log message appears.
- After fixing B1+B3: confirm `outputs.jsonl` now shows `status="degraded"` for the two llama3.1 timeout runs.
- After adding B4 events: verify `events.jsonl` for the llama3.1 silo run shows a `classification_fallback` event with `fallback_count=18` and `cause="llm_failed"`.

**Risks:**
- Increasing llama3.1 timeout to 240s: worst case, slow failures take twice as long to detect. Not a correctness risk.
- Changing `status="ok"` to `status="degraded"` for timeout runs: any analysis script that hard-codes `status == "ok"` as the success criterion will correctly start excluding these runs. If the script uses `status != "error"` it may need updating. Verify `create_analysis_dir.py` and `run_insight.py` do not filter on status in a way that would exclude all llama3.1 runs.
- Emitting `classification_fallback` events: purely additive. No regression risk.

**Prerequisites:** None. The B2 fix (one-liner) and the I4 config change can be shipped immediately without dependencies.

---

## Backlog

**Resolved from iter 50 (PR #373) backlog — can be closed:**
- Likert scale inversion (llama3.1 catastrophic 1-lever output) — eliminated by categorical schema.
- Deduplication failure for capable models (0% removal) — fixed; capable models now remove 6–33%.
- B2/PR#373: duplicate lever_id in model response silently overwrites first entry — `seen_ids` check added in PR #374.
- B3/PR#373: dead "remove" branch in `_score_to_classification` — function removed (Likert schema gone).
- B4/PR#373: no minimum-lever-count guard — guard added in PR #374.
- Conceptual mismatch (relevance ≠ deduplication) — fixed by restoring the categorical schema.
- N6/PR#373: PR abandons working taxonomy instead of fixing prompt bugs — resolved; taxonomy restored and prompt bugs addressed.

**Carrying forward / new items:**
- **B1 (HIGH):** Silent LLM failure masking — timeout produces `status="ok"` with all-primary fallback. Affects measurement fidelity for all future iterations. Fix: expose `llm_call_succeeded` flag from `DeduplicateLevers.execute()`.
- **B2 (LOW):** `user_prompt` field stores `project_context` instead of full assembled prompt. One-line fix in `deduplicate_levers.py:272`.
- **B3 (MEDIUM):** `calls_succeeded` hardcoded to 1 in `runner.py` regardless of actual LLM success. Fix alongside B1.
- **B4 (MEDIUM):** No `classification_fallback` event emitted to `events.jsonl`. Analysis pipeline cannot programmatically detect degraded runs.
- **I4 (LOW):** Increase llama3.1 `request_timeout` from 120s to 240s in llm_config JSON. Config change only, no code required.
- **N3 (LOW):** Inter-model classification variance — "gating the core outcome" criterion is subjective; models disagree on whether a lever is primary vs. secondary. Consider adding concrete anchor examples to the system prompt (analogous to review_lever examples in identify_potential_levers.py). Low urgency — FocusOnVitalFewLevers filters further downstream.
- **S4 (LOW):** Minimum lever count threshold (`max(3, N//4) = 4` for 18 levers) is too low — a model removing 14/18 still clears the warning. Consider raising to `max(5, N//3)`.
- **S1/identify (MEDIUM):** `Lever.consequences` field description in `identify_potential_levers.py` names "Controls ... vs." and "Weakness:" as banned phrases, contradicting `OPTIMIZE_INSTRUCTIONS`' explicit guidance against naming banned phrases (template-lock risk). Fix in a separate identify_potential_levers iteration.
- **Q4:** Verify whether downstream EnrichLevers and FocusOnVitalFewLevers actually consume the primary/secondary field before investing further in classification calibration.
- **I5+I6 (MEDIUM):** When the LLM omits a lever_id from the response (gpt-oss-20b missed dcb03988), a targeted retry is more correct than the blanket primary fallback. Implement after the observability fixes (B4) make it possible to count fallback frequency reliably.
