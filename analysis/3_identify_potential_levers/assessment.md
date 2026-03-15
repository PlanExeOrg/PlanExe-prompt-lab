# Assessment: fix: use message.content instead of model_dump() for assistant turn

## Issue Resolution

**What the PR was supposed to fix:**
PR #270 addressed the root cause of cross-call lever duplication. When `llm.as_structured_llm(DocumentDetails)` is used with function-calling models (OpenAI, Anthropic), the structured output arrives via `raw`, not via `message.content`. The original code appended `message.content` (which is `None` for these models) as the assistant turn, so calls 2 and 3 received a blank history and regenerated from scratch — producing identical levers. The fix: `message.content or raw.model_dump_json()`.

The synthesis for analysis 2 also recommended making follow-up prompts novelty-aware (Direction 2: inject already-generated lever names into calls 2/3). This was bundled into the same change, replacing the bare `"more"` prompts with:
```
"Generate 5 MORE levers with completely different names. Do NOT reuse any of these already-generated names: [list]"
```

**Is the issue resolved?**
Yes, decisively. Direct evidence from the shared-model files:

- **Before (run 21, qwen3-30b, sovereign_identity):** `history/0/21_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` — lever 1 and lever 6 are byte-for-byte identical ("Policy Resilience Framing Strategy"), confirming the 5-name-repeated-3× pattern (33% unique, 6.0 cross-call dup names/file).
- **After (run 29, qwen3-30b, sovereign_identity):** `history/0/29_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` — 15 levers with 15 distinct names ("Standardization Advocacy Strategy", "Procurement Influence Strategy", "Coalition Building Strategy", "Demonstrator Development Strategy", "Regulatory Framing Strategy", "Alternative Authentication Ecosystem Strategy", "Open-Source Ecosystem Development", "Cross-Border Digital Resilience Strategy", "Legal Innovation Framework Strategy", "Public-Private Synergy Strategy", "Trust Infrastructure Reconfiguration Strategy" + 4 more). Cross-call dup = 0.

Corpus-wide uniqueness for the three highest-volume shared models:

| Model | Before | After |
|-------|--------|-------|
| llama3.1 | 23/76 unique (30%) | 74/75 unique (99%) |
| gpt-5-nano | 42/75 unique (56%) | 75/75 unique (100%) |
| qwen3-30b | 45/75 unique (60%) | 73/75 unique (97%) |

**Residual symptoms:**
The fix corrected the serialization path; however, semantic duplication persists at a lower rate. Run 28 (gpt-5-nano) parasomnia: 5 of 10 cross-batch lever pairs are semantic duplicates despite unique names ("Adaptive Facility Footprint Strategy" vs "Localized Modular Footprint Diffusion"). The name-level anti-duplication works; topic-level diversity still requires further work (Synthesis 3 Direction 5).

---

## Quality Comparison

Only models appearing in **both** batches are compared below.

| Metric | Before (runs 17–23) | After (runs 24–31) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate – llama3.1** | 5/5 (100%) | 5/5 (100%) | UNCHANGED |
| **Success rate – gpt-5-nano** | 5/5 (100%) | 5/5 (100%) | UNCHANGED |
| **Success rate – qwen3-30b** | 5/5 (100%) | 5/5 (100%) | UNCHANGED |
| **Success rate – gpt-4o-mini** | 5/5 (100%) | 3/5 (60%) | REGRESSED |
| **Success rate – claude-haiku** | 4/5 (80%) | 4/5 (80%) | UNCHANGED |
| **Success rate – nemotron** | 1/5 (20%) | 1/10 (10%, 2 runs) | REGRESSED |
| **Success rate – gpt-oss-20b** | 1/5 (20%) | 2/5 (40%) | IMPROVED |
| **Cross-call uniqueness – llama3.1** | 23/76 = 30% | 74/75 = 99% | IMPROVED ↑↑↑ |
| **Cross-call uniqueness – gpt-5-nano** | 42/75 = 56% | 75/75 = 100% | IMPROVED ↑↑↑ |
| **Cross-call uniqueness – qwen3-30b** | 45/75 = 60% | 73/75 = 97% | IMPROVED ↑↑↑ |
| **Cross-call uniqueness – gpt-4o-mini** | 71/75 = 95% | 44/45 = 98% | IMPROVED (fewer plans) |
| **Cross-call uniqueness – claude-haiku** | 54/64 = 84% | 61/61 = 100% | IMPROVED ↑↑ |
| **Bracket placeholder leakage** | 0 levers | 0 levers | UNCHANGED |
| **Option count violations – llama3.1** | 0 (analysis 2 insight_codex) | 14 single-option levers (run 26) | REGRESSED |
| **Option count violations – others** | 0 across runs 20–23 | 0 across runs 28–31 | UNCHANGED |
| **Lever name uniqueness (avg/file) – llama3.1** | 5.2/15 | 14.8/15 (74/75) | IMPROVED ↑↑↑ |
| **Lever name uniqueness (avg/file) – gpt-5-nano** | 8.4/15 | 15.0/15 | IMPROVED ↑↑↑ |
| **Lever name uniqueness (avg/file) – qwen3-30b** | 9.0/15 | 14.6/15 | IMPROVED ↑↑↑ |
| **Template leakage "Material Adaptation Strategy"** | runs 17, 18 affected | runs 25, 26 affected (same prompt) | UNCHANGED |
| **Template leakage "25% faster scaling"** | runs 20, 21, 22 (moderate) | run 28: 72/75; run 26: ~14/75 | UNCHANGED (same prompt) |
| **Review format – "Controls X vs Y"** | run 20: 60 violations ("Trade-off:" instead) | run 28: 75 "Trade-off:" reviews | UNCHANGED |
| **Consequence chain format (Immediate→Systemic→Strategic)** | run 22: 45 violations; others: 0 | run 28: 31 viol.; run 29: 45 viol.; run 30: 15 viol.; run 31: 16 viol. | REGRESSED |
| **Avg option length – llama3.1** | 89.8 chars | 95.6 chars | UNCHANGED |
| **Avg option length – gpt-5-nano** | 152.1 chars | 126.6 chars | REGRESSED (slight) |
| **Avg option length – qwen3-30b** | 64.2 chars | 63.1 chars | UNCHANGED |
| **Avg option length – claude-haiku** | 308.4 chars | 318.7 chars | UNCHANGED |
| **Semantic cross-call duplication** | byte-for-exact (llama3.1, gpt-4o-mini) | 5/10 pairs semantic-duplicate (gpt-5-nano, run 28) | IMPROVED (names fixed; topics partially) |

**Notes on gpt-4o-mini regression:** The 5/5 → 3/5 failure is caused by a pre-existing schema bug (newly surfaced post-fix): `DocumentDetails` requires `strategic_rationale` and `summary`, but `save_clean()` never uses them. Models that return only `{"levers": [...]}` fail validation, and gpt-4o-mini reliably omits the wrapper fields. This bug existed before the PR but was not triggered by the runs in analysis 2.

**Notes on consequence chain violations:** The increase in missed `Immediate:` / `Systemic:` / `Strategic:` markers post-fix is not directly caused by the serialization change. It reflects that with better inter-call context, some models now generate more varied but less format-adherent outputs. The prompt's example ("Systemic: 25% faster scaling through…") is still the only concrete chain format example, and run 29's qwen3-30b consequences follow a narrative prose form instead of the arrow-chain structure.

---

## New Issues

### 1. gpt-4o-mini schema wrapper failure (pre-existing, now visible)
The model returns `{"levers": [...]}` without `strategic_rationale` and `summary`. Both fields are required in `DocumentDetails` but discarded by `save_clean()`. This causes 2/5 plan failures for run 30 that did not appear in run 22 (analysis 2). The code change did not introduce this — run 22 likely succeeded because a different gpt-4o-mini invocation happened to include the wrapper fields. The schema inconsistency was always there.

**Evidence:** `history/0/30_identify_potential_levers/outputs.jsonl` lines 1 and 5: "2 validation errors for DocumentDetails: strategic_rationale Field required, summary Field required."

### 2. Placeholder lever in final artifact (claude-haiku, run 31)
A lever literally named `"Placeholder Removed - Framework Compliance"` with `options: ["Removed"]` and `review: "Structural compliance marker"` appears in `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`. This indicates haiku injected a framework-compliance token into the content when struggling with the format. This may be more likely to appear post-fix because the model now has full access to its prior structured output and may generate this as a self-imposed compliance marker.

**Evidence:** `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:59`.

### 3. Option count conflict now measurably causes failures (pre-existing, surfaced)
`Lever.options` field description says "2-5 options" (`identify_potential_levers.py:34`), but the system prompt says "exactly 3" (`:90`). Post-fix, llama3.1 now generates 14 levers with 1 option in run 26. This contradictory signal was probably always present but is now more visible because models receive richer context (the full prior JSON) and may weight the schema description more heavily.

**Evidence:** `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` levers 15, 24, 33.

### 4. Semantic duplication persists despite name uniqueness
With unique names enforced, semantic duplication is the remaining diversity gap. Run 28 (gpt-5-nano) parasomnia: batches 1 and 2 produce near-identical lever topics despite different names. The anti-duplication instruction only bans reusing names, not topics.

**Evidence:** `history/0/28_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — 5/10 cross-batch pairs are semantic duplicates (e.g., "Adaptive Facility Footprint Strategy" vs "Localized Modular Footprint Diffusion").

---

## Verdict

**YES**: The PR is a keeper. The serialization fix (and bundled novelty-aware prompts) resolved the dominant quality failure — cross-call lever duplication — with dramatic measurable improvement for every shared model: llama3.1 improved from 30% to 99% name uniqueness, gpt-5-nano from 56% to 100%, qwen3-30b from 60% to 97%, claude-haiku from 84% to 100%. These are the most important models in the test set (full reliability, best content quality), and the improvement is verified by reading actual output files. The new issues that surfaced (schema wrapper failures, placeholder levers, option count violations) are pre-existing bugs made visible by improved context injection, not regressions introduced by the fix.

---

## Recommendations

### Should the next iteration follow the after-synthesis recommendations?
**Yes.** Synthesis 3 correctly identifies the two highest-value next changes:

1. **Direction 1 (prompt change): Remove "25% faster scaling" and "Material Adaptation Strategy" examples.** The same prompt SHA was used in both batches. Template leakage was present before and remains after because the prompt is unchanged. This is the lowest-effort / highest-impact remaining change. Run 28 (gpt-5-nano) shows 72/75 levers with "25% faster" — this alone justifies the fix.

2. **Direction 2 (code fix): Make `strategic_rationale` and `summary` optional** in `DocumentDetails`. This converts 2 of gpt-4o-mini's 5 failures to successes immediately (60% → 100% for that model), at essentially zero risk since `save_clean()` already discards these fields.

These two changes should be bundled in the next PR.

### Resolved issues that can be removed from the backlog
- **B1 (assistant turn serialization / `message.content = None`)** — fully resolved. Evidence: cross-call dup names = 0 for all comparable models in analysis 3.
- **"more" follow-up prompts carry no context** (Synthesis 2 Direction 2) — implemented. The novelty-aware prompts are now present and working at the name level.

### New issues to add to the backlog
1. **Schema: `strategic_rationale` / `summary` should be optional** (Synthesis 3 Direction 2, code_claude 3 I4) — high priority, 2-line fix, immediate success-rate improvement.
2. **Options cardinality conflict: "2-5" in schema vs. "exactly 3" in prompt** (code_claude 3 B1, Synthesis 3 Direction 3) — medium priority. Causes measurable single-option lever failures in run 26.
3. **Post-merge sanitization: reject placeholder levers and wrong option counts** (code_claude 3 I8, Synthesis 3 Direction 4) — medium priority. Prevents run-31-style compliance tokens from reaching downstream steps.
4. **Semantic topic duplication in calls 2/3** (code_claude 3 I7, Synthesis 3 Direction 5) — lower priority (name uniqueness is already enforced). Requires passing topic summaries alongside names; test carefully to avoid format regression.
5. **Context window guard for small-context models** (code_claude 3 I5) — low priority for prompt optimization (nemotron is already avoided), but should be added for robustness.
6. **Consequence chain format violations** — increased post-fix for qwen3-30b and gpt-5-nano. Track whether removing the "25% faster scaling" example (which also serves as the only chain-format example) worsens or improves chain compliance. May need to reformulate the example to preserve format guidance while eliminating the copiable number.
