# Synthesis

**Runs analyzed:** 67–73 (all using prompt_1, sha `b12739343…`)
**PR under review:** #279 — "Remove formulaic naming template from lever prompt"
**Source verified:** `identify_potential_levers.py` read in full

---

## Cross-Agent Agreement

Both insight agents and both code reviews converge on the same core findings:

1. **The `[Domain]-[Decision Type] Strategy` naming example in prompt_1 is the dominant quality failure.** Three of six successful runs (llama3.1 at 100%, gpt-oss-20b at 93%, gpt-4o-mini at 100% for silo) mechanically applied the bracket template. Models that ignored it (haiku, gpt-5-nano, qwen3) produced the best names. Evidence is unambiguous: run 72 has 15 consecutive `Silo-X Strategy` names; run 70 has 15 consecutive `GTA-X Strategy` names; run 68 produced the absurd `Denmark-Procurement-Strategy Strategy`.

2. **No quality gate exists between raw LLM output and the saved cleaned artifact.** Both code reviews confirmed that `identify_potential_levers.py:244–260` is a flat copy with zero validation. Every contaminated lever — review text inside `consequences`, bracket placeholders, partial `review` fields — passes directly into `002-10-potential_levers.json` as a silent "success". Run 71 (qwen3) has 60 of 75 levers with review text contaminating `consequences`. Run 68 (llama3.1) retains bracket placeholders and partial reviews.

3. **Schema/code allows 5–7 levers per call; follow-up prompt explicitly requests 5–7; registered prompt_1 says "EXACTLY 5".** All four agents (two insight, two code review) flagged this mismatch at lines 78–82 and 203. It directly explains the 17–19 lever cleaned outputs in runs 68 and 73.

4. **Run 67 (nemotron) is a complete structural failure** — all 5 plans returned JSON extraction errors, unrelated to prompt content.

5. **Run 73 (haiku) produces the richest content but is operationally unstable** — only 4/5 plans succeeded, field lengths balloon (consequences avg 867.7 chars), and the hong_kong_game plan failed with "List should have at least 5 items after validation, not 1".

6. **The current source prompt in `identify_potential_levers.py` already removed the template.** Line 143 now reads "avoid formulaic patterns or repeated prefixes." PR #279 registers the matching prompt file for the experiment runner — the code-side change is already in place.

---

## Cross-Agent Disagreements

### Disagreement 1: Best overall run — run 73 (claude insight) vs. run 69 (codex insight)

- **Claude insight** ranks run 73 (haiku) #1 for content richness: quantified consequences, no template leakage, varied name forms.
- **Codex insight** ranks run 69 (gpt-oss-20b) #1 for compliance: 5/5 plans, exactly 75 levers, zero violations on all constraint metrics; run 73 ranks 5th.

**Verdict (source-verified):** Both are right about different objectives. For *pipeline reliability*, run 69 is better — it is the only run with zero violations. For *content quality*, run 73 is better. The disagreement reflects an unresolved objective tension. For prompt optimization purposes, run 69's zero-violation profile is the more actionable benchmark.

### Disagreement 2: Run 70 template leakage rate

- **Claude insight** reports ~7% leakage for the silo plan (1/15 names).
- **Codex insight** reports 25 domain-template names across all plans (15 GTA levers and 10 Hong Kong levers all use `X-... Strategy`).

**Verdict (source-verified):** Both are correct — they measured different plan sets. The silo plan was largely clean for run 70, but other plans (GTA, Hong Kong) show heavy domain-prefix behavior. Run 70 is not as resistant to the template as the silo-only view suggests.

### Disagreement 3: Whether count mismatch (B1) is a bug or intentional

- **Both code reviews** frame it as a bug.
- **Module-level docstring (lines 4–9)** explicitly says: "Don't focus on hitting exactly 15 levers. It's more important that there is 15..20 levers." Over-generation is intentional; downstream `deduplicate_levers.py` handles reduction.

**Verdict (source-verified):** The module docstring is authoritative. Over-generating 5–7 per call is the *intended design*. The real mismatch is that registered prompt_1 says "EXACTLY 5" while the source prompt and schema say "5 to 7." This creates conflicting instructions to the model, not a pipeline bug. The fix is to align the registered prompt's count instruction with the code's actual schema, not to force exact-5.

### Disagreement 4: Codex S3 — four batches per plan for haiku

- **Codex code review** notes the source hard-codes `total_calls = 3` (line 192) and that any run showing 4 batches must have used a different code revision.
- **Claude insight** attributes haiku's under-generation on some calls to the fresh-context design, without noting the batch count discrepancy.

**Verdict (source-verified):** Line 192 confirms `total_calls = 3`. If analysis artifacts counted 4 raw batches for run 73, those figures came from a different runner configuration or commit — they are not reproducible with the current source. The haiku count-violation data (19 silo levers vs expected 20) still stands, but the "4th call under-generates" framing in claude's insight may be based on a different code version.

---

## Top 5 Directions

### 1. Add post-merge quality gate before saving cleaned levers

- **Type**: code fix
- **Evidence**: Both code reviews (claude B3/codex B2); codex insight N3; claude insight N6, N7. Run 71 has 60/75 levers with review text in `consequences`. Run 68 has bracket placeholders and partial reviews. All pass silently into `002-10-potential_levers.json`.
- **Impact**: All models, all runs. Converts silent bad artifacts into detectable failures. Would flag 60 levers in run 71 and ~20 in run 68 rather than treating them as clean. Benefits every downstream analysis step that reads `002-10-potential_levers.json`.
- **Effort**: Low — add 3–4 checks in the `for i, lever in enumerate(levers_raw, start=1)` loop at line 249: (1) `"Controls"` or `"Weakness:"` not in `consequences`; (2) both `"Controls"` and `"Weakness:"` present in `review_lever`; (3) no `[text]` bracket placeholders in any field; (4) name not already in accumulated name set. Log warnings or raise on violation.
- **Risk**: May cause some runs to fail that currently "succeed." This is the desired behavior — false success is worse than explicit failure. No structural change to the output format.

---

### 2. Approve PR #279 — remove the `[Domain]-[Decision Type] Strategy` naming template

- **Type**: prompt change
- **Evidence**: Claude insight H1, codex insight H1; runs 68 (100%), 69 (93%), 72 (100%) for silo all show mechanical leakage directly traceable to `prompt_1_b12739343…:19`. The source prompt at line 143 has already been updated.
- **Impact**: Primarily affects mid-tier models (llama3.1, gpt-oss-20b, gpt-4o-mini). Expected leakage rate drops from 93–100% to near-zero for these models based on how they respond to example-free guidance. No downside for haiku or qwen3 (already 0% leakage). Negligible effect on nemotron (structural failure regardless).
- **Effort**: Already done at the code level. PR #279 only registers the corresponding prompt file. Effort is zero.
- **Risk**: Without a positive naming example, some models may revert to generic names like "Resource Allocation Strategy" (prompt_0 style). Mitigated by the existing "language drawn directly from the project's own domain" instruction in section 3.

---

### 3. Align registered prompt count instruction with the 5–7 schema contract

- **Type**: prompt change
- **Evidence**: Claude insight N4, codex insight N2, both code reviews (B1). Registered prompt_1 says "EXACTLY 5 levers per response" but schema accepts 5–7 and follow-up call says "5 to 7 MORE." Module docstring explicitly endorses over-generation for downstream deduplication.
- **Impact**: Eliminates the confusing dual instruction. Models receiving "EXACTLY 5" in the prompt but validated against a 5–7 schema get mixed signals, which may cause erratic count behavior. Changing "EXACTLY 5" to "5 to 7 levers" in the registered prompt aligns all three contract sites (prompt text, schema, follow-up call). Does not change actual output count behavior (over-generation is intentional).
- **Effort**: One word change in the registered prompt. Very low.
- **Risk**: Removing "EXACTLY" might cause weaker models (llama, gpt-4o-mini) to generate more varied counts. This is acceptable because the deduplication step is designed to handle it.

---

### 4. Add explicit naming anti-repetition instruction to the prompt

- **Type**: prompt change
- **Evidence**: Claude insight H2, codex insight H2; run 72 shows 100% "Silo-X Strategy" for silo even though gpt-4o-mini skips the domain prefix for GTA. Run 70's GTA plan has 15 "GTA-X Strategy" names.
- **Impact**: Reduces the residual risk that models find new ways to mechanically prefix names after the template example is removed. A sentence like "Do not begin more than one lever name with the same project noun; vary the head noun across the full lever set." would block the domain-prefix pattern without requiring a specific example to avoid.
- **Effort**: Low — add one sentence to section 5 (Prohibitions) or section 3 (Strategic Framing).
- **Risk**: May be unnecessary after PR #279 removes the template example. Models like haiku and qwen3 already produce zero domain-prefix names without this instruction. Worth testing after PR #279 to see if the problem persists.

---

### 5. Persist failure artifacts in runner.py

- **Type**: code fix (observability)
- **Evidence**: Codex code review B4/I4, claude code review I6. Run 67 (nemotron) fails on all 5 plans with JSON extraction errors. The runner currently writes nothing on failure except a terse error string in `outputs.jsonl`. The per-plan prompt snapshot, event trail, and raw model response are discarded.
- **Impact**: Does not change output quality for any model. Enables root-cause analysis for parse-failure runs (nemotron class). Would allow the analysis pipeline to distinguish JSON extraction failures from schema validation failures from API errors — without string-matching the error message. Moderate long-term benefit as more edge-case models are tested.
- **Effort**: Medium — requires changes to `runner.py` error path to write a sidecar file containing prompt, model metadata, raw response, and retain `track_activity.jsonl` instead of deleting it.
- **Risk**: None for pipeline correctness. Increases disk usage on failure runs.

---

## Recommendation

**Do direction 1 first: add the post-merge quality gate in `identify_potential_levers.py`.**

**Why first:** PR #279 (direction 2) is already prepared and ready to merge — it has zero remaining effort and should simply be approved. But after it lands, the next run will still silently save contaminated levers from qwen3 (60/75) and placeholder-bearing levers from llama3.1 as if they were valid clean outputs. The quality gate is the only fix that benefits every model on every run, regardless of prompt version.

**What to change — file and lines:**

File: `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`

In the `execute()` method, replace the flat copy loop at lines 249–260:

```python
# Current (no validation):
levers_cleaned: list[LeverCleaned] = []
for i, lever in enumerate(levers_raw, start=1):
    lever_id = str(uuid.uuid4())
    lever_cleaned = LeverCleaned(
        lever_id=lever_id,
        name=lever.name,
        consequences=lever.consequences,
        options=lever.options,
        review=lever.review_lever,
    )
    levers_cleaned.append(lever_cleaned)
```

Add these four checks before `levers_cleaned.append(lever_cleaned)`:

1. **Review-text contamination in consequences:**
   ```python
   if "Controls" in lever.consequences or "Weakness:" in lever.consequences:
       logger.warning(f"Lever '{lever.name}': consequences contains review markers, skipping.")
       continue
   ```

2. **Required review structure:**
   ```python
   if "Controls" not in lever.review_lever or "Weakness:" not in lever.review_lever:
       logger.warning(f"Lever '{lever.name}': review_lever missing 'Controls' or 'Weakness:', skipping.")
       continue
   ```

3. **Bracket placeholder check:**
   ```python
   import re
   placeholder_pattern = re.compile(r'\[[^\]]{3,}\]')
   all_text = lever.name + lever.consequences + " ".join(lever.options) + lever.review_lever
   if placeholder_pattern.search(all_text):
       logger.warning(f"Lever '{lever.name}': contains bracket placeholder, skipping.")
       continue
   ```

4. **Duplicate name check:**
   ```python
   seen_names: set[str] = set()
   # (declare before the loop, then inside:)
   if lever.name in seen_names:
       logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
       continue
   seen_names.add(lever.name)
   ```

**Why not direction 2 first:** PR #279 should be approved in parallel — it's a one-liner that's already ready. It doesn't need synthesis to unlock it. But the quality gate is the more important *next code action* because it makes every subsequent run's "success" status trustworthy.

**Why not direction 3:** Aligning the count instruction is low-effort but doesn't change any output. It's a cleanup task, not a quality fix.

**Why not direction 4:** Direction 4 is a follow-up to direction 2 (PR #279). Run the next batch after PR #279; if domain-prefix behavior persists, add the anti-repetition instruction then.

---

## Deferred Items

- **Direction 4 (naming anti-repetition):** Run a post-PR-#279 batch first. If domain-prefix leakage persists in models like gpt-4o-mini without the bracket template, add "Do not begin more than one lever name with the same project noun" to section 5 Prohibitions.

- **Direction 5 (preserve failure artifacts):** Important for long-term model coverage, but nemotron is the only current example of total parse failure. Defer until a second model shows this pattern or until nemotron is re-tested.

- **Direction 3 (count instruction alignment):** Simple cleanup — change "EXACTLY 5" to "5 to 7" in the registered prompt. Can be bundled with the next prompt PR rather than done standalone.

- **H3 (remove conservative→radical option framing):** Claude insight H3 flags that the "conservative → moderate → radical" instruction may produce predictable, label-like options (evidence: llama3.1 options avg 92.5 chars vs haiku's 335.5 chars). Low priority because haiku ignores this instruction and produces better options without it. Test after the naming template and quality gate fixes are in place.

- **I3/S2 (semantic anti-duplication for follow-up calls):** Passing a summary of already-covered themes/tensions to calls 2 and 3 would reduce semantic overlap, but this is an architectural change requiring more thought. Defer.

- **Codex S2 (prompt provenance audit trail):** Saving the full prompt text into the run directory alongside the SHA would prevent the "which prompt was actually executed" ambiguity. Worth adding to the runner as a low-effort observability improvement, but not a priority for output quality.

- **B4 (thread safety in runner.py `set_usage_metrics_path`):** Latent race condition when `workers > 1`. Severity depends on whether `set_usage_metrics_path` uses thread-local or module-level storage. Audit the implementation before deciding whether this needs immediate fixing.

- **I3/C2 (retain `strategic_rationale` in clean output):** Both insight agents flagged that this field is discarded in `save_clean`. Useful for downstream synthesis and per-batch audit. Low effort to add as a top-level `"call_rationales"` list in the clean output — defer to a separate PR.
