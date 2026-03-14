# Assessment: fix: remove doubled user prompt in identify_potential_levers (B1)

## Issue Resolution

**PR #268** removed the doubled `USER(user_prompt)` from the initialization of
`chat_message_list` in `identify_potential_levers.py`. Before the fix the conversation
sequence was `SYSTEM → USER → USER → ASSISTANT → USER("more") → ...`; after the fix it is
the correct `SYSTEM → USER → ASSISTANT → USER("more") → ASSISTANT → USER("more") →
ASSISTANT`.

The fix targeted a structural defect that corrupted the conversation turn order on every
first LLM call. Analysis 1 (runs 09–16) confirmed the fix introduced no regressions and
that the corrected sequence is operationally safe.

However, a deeper serialization bug was identified immediately after: even with the correct
turn order in place, the assistant turn injected into calls 2 and 3 carries
`content=result["chat_response"].message.content`, which is `None` or empty for
function-calling-based models (OpenAI, Anthropic). This means call 2 and call 3 receive a
blank assistant turn regardless of the B1 fix, so the model has no memory of its prior
output. The synthesis for analysis 2 confirms this as the root cause of the 33% unique-name
rate observed in all 6 producing runs of the after batch.

**Conclusion**: PR #268 is correct and its specific bug (doubled USER prompt) is resolved.
The fix did not cause any new failures. However, it did not address — and analysis 2 now
confirms — a second serialization bug (`message.content` is None) that is responsible for
the dominant quality failure across both batches.

---

## Quality Comparison

Models are compared only where the same model identity appears in both the before batch
(runs 09–16, analysis 1) and the after batch (runs 17–23, analysis 2). Five models appear
in both batches.

| Metric | Before (runs 09–16) | After (runs 17–23) | Verdict |
|---|---|---|---|
| **gpt-5-nano completion** | 5/5 plans OK (run 10) | 5/5 plans OK (run 20) | No change |
| **gpt-5-nano unique names/file (silo)** | 15/15 (before analysis: 15 unique per insight_claude) | 5/15 unique (insight_codex: avg 8.4/file across all plans) | Worse — before batch had higher silo uniqueness per insight_claude but codex reports 8.4 avg |
| **gpt-5-nano template leakage ("25%")** | 11/15 levers (73%) in silo | Present (hallucinated %; codex: 0/75 misses numeric outcomes but uses "25%"-style numbers) | Mixed: numeric present but still fabricated |
| **gpt-4o-mini completion** | 5/5 plans OK (run 15) | 5/5 plans OK (run 22) | No change |
| **gpt-4o-mini unique names/file (silo)** | 12/15 unique (2 exact duplicates) | 15/15 unique (insight_codex: 15.0 avg) | Improved — zero duplicates after |
| **gpt-4o-mini content quality** | Generic, formulaic | Generic, occasional blockchain suggestions unrelated to plan | No meaningful change |
| **qwen3-30b completion** | 5/5 plans OK (run 14) | 5/5 plans OK (run 21) | No change |
| **qwen3-30b unique names/file (silo)** | 14/15 unique (insight_claude before) | 15.0 avg but collapses to 5/15 on several plans (codex after) | Inconsistent — plan-dependent |
| **qwen3-30b option length** | ~130 chars avg (short labels) | 64.2 chars avg (shorter than before) | Worse — options more terse after |
| **llama3.1 completion** | 5/5 plans OK (run 16) | 5/5 plans OK (run 18) | No change |
| **llama3.1 unique names/file (silo)** | 18/20 unique (20-lever file) | 5/15 unique (5.2 avg; 12 prompt-example copies) | Worse — before was overcount but higher diversity; after is heavily templated |
| **llama3.1 template leakage ("Material Adaptation Strategy")** | 1 copy in silo | 12 copies across 4 plans | Much worse — leakage increased |
| **haiku-4-5 completion** | 5/5 plans OK (run 12) | 4/5 plans OK, 1 timeout (run 23) | Slightly worse — one new timeout |
| **haiku-4-5 unique names/file (silo)** | 15/15 unique (insight_claude before) | 19/15 (overproduction; 19 unique per codex) | Structural violation after — overproduced |
| **haiku-4-5 unique names/file (GTA game)** | Not separately quantified before | 15/15 unique (100%) after | Positive after: full diversity on creative domain |
| **haiku-4-5 content specificity** | High (plan-specific, rich consequences) | High (strategic specificity ceiling; longer consequences 682 chars avg vs 450 before) | Improved depth, but timeout risk increased |
| **nvidia-nemotron completion** | 0/5 (run 11, no JSON output) | 1/5 (run 17, 4 EOF truncations) | Marginal improvement — before was 0%, after 20% |
| **gpt-oss-20b completion** | 4/5 (run 13, 1 JSON truncation) | 1/5 (run 19, 4 non-JSON/truncation failures) | Worse — reliability dropped significantly |
| **Cross-call uniqueness (all models, sovereign_identity)** | Not systematically measured | All: 33% (5/15 unique names) | Persistent — no improvement; root cause unaddressed |
| **Avg unique names/file (codex, all producing runs)** | Baseline avg 10.6 | Run 20: 8.4; Run 21: 9.0; Run 22: 15.0; Run 23: 13.5 | Mixed — gpt-4o-mini improved, others flat or worse |

**Models only in before batch (no after counterpart):** stepfun-step-3-5-flash (run 09, 0/5 config failure).

**Models only in after batch (no before counterpart):** None that were fully absent before — the same five model families recur in both batches.

---

## New Issues

The after batch (runs 17–23) reveals several issues not present or not prominent in the before batch:

1. **Confirmed: `message.content` is None for function-calling models (B1 in analysis 2).**
   The synthesis for analysis 2 establishes with high confidence that `message.content` is
   None for OpenAI and Anthropic structured-output calls. This is the direct root cause of
   the 33% unique-name rate across all 6 producing runs in the after batch. This bug is
   independent of and survived the PR #268 fix. The analysis 1 synthesis identified this
   separately as BUG-A (dict-vs-string), but analysis 2 refines the diagnosis: the current
   code uses `message.content` which is None, not a dict, for these model families.

2. **haiku-4-5 timeout on hong_kong_game (run 23, 472 s).** The after batch introduces a new
   API timeout failure for the highest-quality model. The before batch (run 12) had no
   timeout for the same model on the same plan (120 s). The synthesis for analysis 2
   attributes this to context-growth: with the serialization bug still present, or once it
   is fixed and full JSON payloads are replayed, haiku's verbose responses inflate context
   size on later calls. This timeout did not appear before.

3. **haiku-4-5 lever overproduction on silo (run 23, 19 levers instead of 15).** The before
   run (run 12) produced exactly 15 levers for silo. The after run produces 19. No count
   validation exists. This is a new artifact failure.

4. **llama3.1 template leakage increased dramatically.** Run 16 (before) had 1 copy of
   "Material Adaptation Strategy" in silo. Run 18 (after) has 12 copies across 4 plans.
   Both runs use the same prompt; the change in leakage rate is not explained by the PR fix
   and may reflect stochastic model behavior or a different ollama configuration.

5. **gpt-oss-20b failure rate worsened from 20% to 80%.** Run 13 (before) succeeded 4/5
   plans; run 19 (after) succeeded only 1/5. One failure mode is a new conversational
   clarification response ("I'm happy to expand the analysis further...") rather than JSON.
   This is the dialogue-fallback failure mode. The current prompt has no explicit JSON-only
   instruction, and this model appears more sensitive to the current prompt phrasing in the
   after batch.

6. **qwen3-30b option length regression.** Average option text length dropped from ~130
   chars (run 14, before) to 64.2 chars (run 21, after). The before analysis noted short
   options as a weakness; the after batch confirms they are shorter still. Both runs use
   the same prompt.

---

## Verdict

**CONDITIONAL**: PR #268 correctly fixes the doubled USER prompt (the stated bug), introduces
no regressions, and is a keeper — but the dominant quality failure (cross-call lever
duplication at 33% uniqueness) is caused by a separate serialization bug
(`message.content` is None for function-calling models) that the PR did not address, and
this bug must be fixed next before meaningful quality improvement can be measured.

---

## Recommendations

**Immediate (iteration 2):**

1. **Fix assistant turn serialization** — change `identify_potential_levers.py:196` from
   `content=result["chat_response"].message.content` to
   `content=(result["chat_response"].message.content or result["chat_response"].raw.model_dump_json())`.
   This is the confirmed root cause of 33% unique-name rate across all producing runs in
   both batches. All four analysis files in analysis 2 agree this is the highest-priority
   fix. Expected outcome: cross-call uniqueness increases from 33% toward 70–100% for
   capable models.

2. **Make follow-up prompts novelty-aware** — replace bare `"more"` with a dynamic message
   that lists already-generated lever names and instructs the model to use different names.
   After the serialization fix, the model will see its prior output; this ensures it acts
   on that information. Confirmed recommendation across all four analysis 2 files and both
   synthesis documents.

**Near-term (same PR or immediate follow-up):**

3. **Remove the "Material Adaptation Strategy" example name from the prompt** (`identify_potential_levers.py:104`).
   Leakage rate went from 1 copy (run 16 before) to 12 copies (run 18 after). The example
   name is domain-generic and acts as a fill-in-the-blank template for weaker models.

4. **Replace the "Systemic: 25% faster scaling through..." example** (`identify_potential_levers.py:95`)
   with a causal-mechanism framing. Three models in the after batch (runs 20, 21, 22) copy
   the 25% figure across levers from different plans. The same issue appeared in run 10
   (before) at 73% leakage rate. Both synthesis documents identify this as a simple one-line
   prompt fix.

5. **Add an explicit JSON-only output instruction** to the system prompt. Run 19 (after)
   failed 4/5 plans when the model returned a conversational question. An explicit "Your
   entire response must be a single valid JSON object" directive would prevent this failure
   mode.

**Medium-term (separate PRs):**

6. **Add lever count validation** — enforce `min_length=5, max_length=5` on
   `DocumentDetails.levers` and add a post-merge count check. Overproduction is confirmed
   in run 18 (16 levers) and run 23 (19 levers).

7. **Investigate haiku-4-5 timeout** — the hong_kong_game plan caused a 472-second timeout
   in run 23 but completed in 120 seconds in run 12. After fixing the serialization bug,
   monitor whether full JSON payloads in assistant turns cause context growth that triggers
   timeouts; if so, implement context compression (lever-name summaries rather than full
   payloads for continuation turns).

8. **Fix `set_usage_metrics_path` thread safety** (`runner.py:106`) — move inside the
   `_file_lock` block to prevent usage metric cross-contamination when `workers > 1`.
   Confirmed by both synthesis documents as a real bug, low priority since it does not
   affect lever quality.
