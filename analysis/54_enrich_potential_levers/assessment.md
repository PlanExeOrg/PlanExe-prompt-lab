# Assessment: Include consequences and review in enrich batch prompt

## Issue Resolution

**What the PR was supposed to fix**: PR #451 addressed B3 from analysis 53 —
the batch prompt in `enrich_potential_levers.py` provided only `lever_id`, `name`,
and `options` to the LLM, omitting `consequences` and `review`. This forced the model
to infer `description`, `synergy_text`, and `conflict_text` from the lever name alone,
producing vague or template-driven enrichment.

**Is the issue resolved?** Yes, with clear evidence:

- **gpt-5-nano**: The "Purpose: / Objectives: / Key success metrics:" sub-header
  template (present in all 5 before plans) is entirely absent in all 5 after plans.
  Descriptions are now natural prose grounded in lever-specific context.
  Evidence: `history/3/80_enrich_potential_levers/` vs `history/3/87_enrich_potential_levers/`
  silo plan — Information Control Protocols description went from a rigid Purpose/Objectives
  structure to a content-driven paragraph referencing access tiers and dissemination filters.

- **Cross-model grounding**: After the PR, conflict texts for gpt-4o-mini and gemini-flash
  echo language drawn from each lever's `review` field — a measurable change indicating
  the model is reading the provided context rather than fabricating from the name alone.
  Example — gpt-5-nano, Resource Allocation Strategy: the after conflict_text contains
  "inequitable access" and "favoritism," directly drawn from the `review` field phrase
  "potential for corruption or inequitable access to resources."

**Residual symptoms**:

- **llama3.1 consequence echoing** (N2): llama3.1 now summarizes `consequences`
  verbatim as the description rather than elaborating on it. Descriptions dropped from
  0.80× to 0.65× baseline length. The content is more grounded but shallower — the
  model takes the shortest path when given richer context.

- **qwen3-30b UUID format inconsistency** (N4): The underlying B2 bug
  (`full_lever_context_str` still emits full UUIDs at line 156) was not addressed.
  After the PR, qwen3-30b's format is now nondeterministic — name-only in some plans,
  full UUIDs in others — whereas before it was at least consistently wrong
  (always truncated 8-char UUIDs).

---

## Quality Comparison

All 7 models appear in both batches (runs 78–84 before, runs 85–91 after), mapped by
model. Metrics are drawn from `insight_claude.md` for both analyses.

Note: analysis 53 reports 30/35 (85.7%) overall; analysis 54's comparison table
states 31/35 (88.6%) for both periods — a likely off-by-one in the after-analysis count
(6 models × 5 = 30, plus gpt-oss-20b at 0 = 30, not 31). Both analyses agree the
change is 0. This assessment uses 30/35 (85.7%).

| Metric | Before (runs 78–84) | After (runs 85–91) | Verdict |
|--------|---------------------|---------------------|---------|
| **Overall success rate** | 30/35 (85.7%) | 30/35 (85.7%) | UNCHANGED |
| **gpt-oss-20b success** | 0/5 | 0/5 | UNCHANGED (B1 not fixed) |
| **All other models success** | 30/30 (100%) | 30/30 (100%) | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 100% | 100% | UNCHANGED |
| **Template leakage (gpt-5-nano)** | Present in all 5 plans ("Purpose: / Objectives: / Key success metrics:") | Eliminated in all 5 plans | **IMPROVED** |
| **Template leakage (other models)** | Minor (UUID refs) | Minor (UUID refs, slightly worse for qwen3-30b) | UNCHANGED / marginal REGRESSED |
| **Review format compliance** | Not measured | Not measured | N/A |
| **Consequence chain format** | Not applicable (pass-through field) | Not applicable | N/A |
| **Conflict text grounding** | Ungrounded for most models — inferred from name only | Grounded — echoes `review` and `consequences` language | **IMPROVED** |
| **Description depth (avg across models)** | 506 chars avg | 477 chars avg (–5.8%) | IMPROVED (quality up; length slight decrease) |
| **Description depth — llama3.1** | 386 chars (0.80× baseline) | 316 chars (0.65× baseline) | **REGRESSED** |
| **Description depth — gpt-5-nano** | 663 chars (1.37× baseline, template-driven) | 658 chars (1.36× baseline, natural prose) | IMPROVED (same length, better quality) |
| **Synergy/conflict depth — qwen3-30b** | 183/219 chars (0.58–0.69× baseline) | 213/226 chars (0.74–0.76× baseline) | **IMPROVED** |
| **Synergy/conflict depth — haiku** | 452/485 chars (1.58–1.63× baseline) | 454/488 chars (1.59–1.64× baseline) | UNCHANGED |
| **Cross-call duplication** | Not reported | Not reported | N/A |
| **Over-generation count** | N/A (no cap changes in this PR) | N/A | N/A |
| **Field length vs baseline — all models** | All within 0.58–1.37× | All within 0.65–1.37× | UNCHANGED (llama3.1 dipped below 0.70×) |
| **Fabricated quantification** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Not detected | Not detected | UNCHANGED |
| **Input tokens per call** | 1009–2535 tokens (model-dependent) | +18–20% across all models | **COST REGRESSION** (expected) |
| **Output tokens — gpt-5-nano** | 5526/call | 5239/call (–5.2%) | **IMPROVED** |
| **CJK character contamination** | 0 occurrences | 1 occurrence (qwen3-30b, silo, External Engagement Policy) | Minor REGRESSED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS alignment**:
The PR moves output closer to the OPTIMIZE_INSTRUCTIONS goal of grounded, realistic,
actionable content: the template-lock problem (gpt-5-nano's "Purpose:/Objectives:"
structure) is a direct instance of the "field-description template lock" known problem,
now resolved. However, a new violation has appeared: weak models (llama3.1) exhibit
"consequence echoing without elaboration" — paraphrasing the `consequences` input text
verbatim as the description rather than using it as grounding for a richer explanation.
This failure mode is not yet documented in OPTIMIZE_INSTRUCTIONS.

---

## New Issues

1. **Consequence echoing without elaboration** — New post-PR failure mode for llama3.1:
   when `consequences` is provided in the prompt, llama3.1 takes the shortest path and
   rephrases it as the description instead of elaborating on purpose, scope, and success
   metrics. Description length dropped from 0.80× to 0.65× baseline. The content is
   more grounded but shallower than before. Not in OPTIMIZE_INSTRUCTIONS yet.

2. **qwen3-30b UUID format became nondeterministic** — Before the PR, qwen3-30b
   consistently used truncated 8-char UUIDs (wrong but predictable). After the PR,
   format varies by plan (name-only in silo, full UUIDs in sovereign_identity). The
   additional context changes how qwen3-30b interprets the format signal from
   `full_lever_context_str`. B2 (strip UUIDs from context) is now more urgent.

3. **qwen3-30b CJK character leak** — Run 88 (silo plan, External Engagement Policy
   conflict_text) contains "封锁" (Chinese for "blockade/lockdown") in an English-language
   output. Single occurrence, not systematic, but indicates the richer context can shift
   token probability toward qwen3-30b's multilingual vocabulary on edge cases.

4. **B2 urgency increased** — The pre-existing B2 bug (`full_lever_context_str` still
   emits full UUIDs at line 156) was latent before but is now a visible nondeterminism
   source for qwen3-30b. The PR surfaced this as a higher-priority issue.

**Latent issues confirmed by code review (not caused by PR)**:
- B3: Incomplete enrichment silently drops levers (`enrich_potential_levers.py:220-228`)
- B4: `calls_succeeded=1` hardcoded in `runner.py:184`
- B5: `partial_recovery` false positive for 2-call successes (identify step, out-of-scope)
- S1–S3: Latent concurrency issues (closure capture, global dispatcher, list mutation)

---

## Verdict

**YES**: PR #451 is a keeper. The fix delivered its stated goal — grounding `description`
and `conflict_text` in each lever's documented consequences and trade-offs — with clear,
measurable evidence (gpt-5-nano template artifact entirely eliminated; conflict texts now
echo `review` language across multiple models). The only regression affecting content
quality (llama3.1 description brevity at 0.65× baseline) is a weak-model artefact
addressable by the next change, not a reason to revert. The 18–20% input token cost
increase is the expected and accepted trade-off. No structural failures were introduced.

---

## Recommended Next Change

**Proposal**: Strip UUIDs from `full_lever_context_str` in `enrich_potential_levers.py`
line 156 — change `f"- {lever.lever_id}: {lever.name}"` to `f"- {lever.name}"`. This
is a single-token deletion that removes the UUID format signal models copy into
synergy/conflict text.

**Evidence**: B2 is confirmed by both agents and source-verified at line 156. Before
PR #451, qwen3-30b consistently emitted truncated 8-char UUIDs — wrong but predictable.
After the PR, qwen3-30b is nondeterministic: name-only in the silo plan, full UUIDs in
the sovereign_identity plan. This regression was caused by the additional context
changing how qwen3-30b weights the format signal. llama3.1 still emits full UUIDs
(e.g., `Security System Governance (40b19bce-62a5-4467-a7c3-0f57662f9a31)`) in
synergy/conflict text because the UUID appears in `full_lever_context_str`. Removing
the UUID from the context string eliminates the template signal for all models.

**Verify**:
- qwen3-30b (runs 88/equivalent): Confirm zero UUID strings in synergy/conflict fields
  across all 5 plans. Before the fix, sovereign_identity had full UUID references;
  after the fix it should use name-only like the silo plan.
- llama3.1 (run 85/equivalent): Confirm full UUID format (e.g., `40b19bce-62a5-4467-a7c3-0f57662f9a31`)
  no longer appears in synergy_text or conflict_text fields.
- All models: Verify `enriched_levers_map` key lookup (line 205) is unaffected — the
  fix touches only the `full_lever_context_str` list, not the enrichment map.
- Check that lever references in synergy/conflict are still unambiguous (no two levers
  with near-identical names in the same plan would cause confusion).
- Track qwen3-30b CJK leak: check if the single occurrence in run 88 (silo,
  External Engagement Policy) disappears or persists in the next run.

**Risks**:
- Removing the UUID means cross-lever references in synergy/conflict text rely on
  exact name matching for downstream parsing. If two levers share a near-identical name,
  this could be ambiguous — unlikely given the dedup step, but worth checking.
- If any downstream code currently extracts lever relationships by scanning for UUID
  patterns in synergy/conflict text, this change will break those parsers. However,
  this would be a pre-existing bug since haiku, gpt-4o-mini, and gpt-5-nano already
  emit name-only references in both before and after runs.
- Might not fully resolve qwen3-30b's nondeterminism — the model may still occasionally
  use UUIDs sourced from the `lever_id` appearing in the `lever_details_for_prompt`
  (line 171: `f"Lever ID: {lever.lever_id}\n"`). Watch for this in the next run.

**Prerequisites**: None. This is an independent 1-line fix with zero dependency on
B1 (retry) or any prompt changes. Can be bundled with the B1 retry fix into one small PR.

**OPTIMIZE_INSTRUCTIONS update needed**: Add a bullet for the new "consequence echoing
without elaboration" failure mode (observed in llama3.1 post-PR): "When `consequences`
is provided as context, weak models may summarize it verbatim as the description rather
than using it as grounding for elaboration on purpose, scope, and success metrics."
This is a variant of the "field-description template lock" known problem, specific to
context fields rather than examples.

---

## Backlog

**Resolved — remove from backlog**:
- B3 from analysis 53 (batch prompt missing `consequences` and `review`) — fixed by PR #451.
- N3 from analysis 53 (gpt-5-nano template artifact) — fixed as a consequence of PR #451.

**Open — carry forward**:
- **B1 (critical)**: No per-batch retry in `enrich_potential_levers.py:216-218`. Root
  cause of gpt-oss-20b 0/5 failure. Priority 2 (right after UUID fix).
- **B2 (elevated)**: Full UUIDs in `full_lever_context_str` at line 156. Now more urgent:
  qwen3-30b went from consistently-wrong to nondeterministic after PR #451. Priority 1.
- **B3 (new, code)**: Silent lever drop in `enrich_potential_levers.py:220-228` — logs
  error but does not return a failure or enforce a minimum threshold. Could cause
  downstream FocusOnVitalFewLevers to receive an incomplete set silently.
- **B4 (new, monitoring)**: `calls_succeeded=1` hardcoded in `runner.py:184`. Monitoring
  metrics are always wrong for multi-batch runs. Low impact on output quality but
  misleads diagnostics.
- **D3 / Direction 4 (content quality)**: Add qualitative mechanism guidance for
  synergy/conflict. qwen3-30b synergy/conflict improved slightly to 0.74–0.76× baseline
  but remains below acceptable range. The "(40-60 words)" quantitative target provides
  no guidance on what those words should contain.
- **New: Consequence echoing without elaboration**: llama3.1 description brevity
  regression (0.65× baseline post-PR). Address via anti-echoing instruction in
  `ENRICH_LEVERS_SYSTEM_PROMPT` and OPTIMIZE_INSTRUCTIONS update (Direction 3).
- **New: qwen3-30b CJK character contamination**: Single occurrence in run 88 (silo,
  External Engagement Policy conflict_text). Monitor in next run; if it recurs, add
  language-locking instruction.
- **S1–S3 (latent, low priority)**: Concurrency bugs in runner.py (closure capture,
  global dispatcher cross-contamination, unsafe list mutation). Not triggered in
  current single-threaded runs; address before enabling `workers > 1`.
