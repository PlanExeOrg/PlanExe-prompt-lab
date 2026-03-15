# Assessment: Replace bare 'more' follow-ups with novelty-aware prompts (PR #272)

## Issue Resolution

**What the PR was supposed to fix:**
PR #272 replaced the static `"more"` continuation prompts in `identify_potential_levers.py` with dynamic novelty-aware follow-ups. After each LLM call, generated lever names are collected and injected as an explicit exclusion list in the next call's prompt. Expected to push cross-call lever uniqueness from ~70% toward 90–100%.

The PR also removed the literal template-leaking example phrases from the system prompt (the change from `prompt_0` to `prompt_1`):
- Removed `"Systemic: 25% faster scaling through..."` → replaced with abstract bracket placeholder
- Replaced `"Material Adaptation Strategy"` → replaced with `"[Domain]-[Decision Type] Strategy"` abstraction

**Is cross-call name duplication resolved?**
Yes, but the issue was already partly handled before this PR. In the before batch (runs 24–31, prompt_0), cross-call duplicate names were already 0 for all 5 successful full-coverage models (runs 26, 28, 29, 30, 31). The PR's explicit exclusion list adds enforcement robustness rather than fixing an active failure. After (runs 32–38, prompt_1), name uniqueness remains high: 75/75 for llama3.1 (run 33), gpt-5-nano (run 35), and qwen3 (run 36); 74/75 for gpt-4o-mini (run 37).

**Is the "25% faster scaling" leakage resolved?**
Yes, confirmed. The before batch showed 72/75 levers in gpt-5-nano (run 28) and ~14/75 in llama3.1 (run 26) containing `"25% faster"` verbatim. The after batch shows zero occurrences across all runs.
Evidence: `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` (gpt-4o-mini after — no leakage); `history/0/29_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:27` (qwen3 before — contains `"25% faster scaling"` verbatim).

**Residual symptom — naming anchoring shifted, not eliminated:**
The `"[Domain]-[Decision Type] Strategy"` replacement in prompt_1 substituted one template anchor for another. The after batch shows "hyphen-Strategy" names exploding: 0 in baseline, 1 in before qwen3 (run 29), but 16 in after qwen3 (run 36), 40 in after gpt-5-nano (run 35), and 60 in after gpt-4o-mini (run 37). Run 36's silo output confirms terse names like `"Funding-Subsidy Strategy"`, `"Security-Enforcement Strategy"` (verified in `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`). Template leakage changed form rather than disappearing.

---

## Quality Comparison

Comparison uses only models present in **both** batches:

| Model | Before run | After run | Notes |
|-------|-----------|-----------|-------|
| nemotron-3-nano | 25 (best of 24/25) | 32 | |
| ollama-llama3.1 | 26 | 33 | |
| openai-gpt-oss-20b | 27 | 34 | |
| openai-gpt-5-nano | 28 | 35 | |
| qwen3-30b-a3b | 29 | 36 | |
| openai-gpt-4o-mini | 30 | 37 | |
| anthropic-claude-haiku-4-5 | 31 | 38 | |

| Metric | Before (runs 25–31) | After (runs 32–38) | Verdict |
|--------|---------------------|---------------------|---------|
| **Overall success rate** | 25/35 = 71.4% (7-model basis) | 27/35 = 77.1% | IMPROVED |
| **gpt-4o-mini success rate** | 3/5 (run 30) | 5/5 (run 37) | IMPROVED |
| **haiku success rate** | 4/5 (run 31) | 3/5 (run 38) | REGRESSED |
| **gpt-oss-20b success rate** | 2/5 (run 27) | 3/5 (run 34) | IMPROVED |
| **"25% faster" template leakage** | ~86 occurrences (gpt-5-nano: 72, llama3.1: 2, qwen3: 8) | 0 | IMPROVED |
| **Option count violations** | 14 llama3.1 + 1 haiku = 15/136 | 9 llama3.1 + 2 haiku = 11/122 | IMPROVED (minor) |
| **Lever name uniqueness (qwen3)** | 73/75 (run 29) | 75/75 (run 36) | IMPROVED |
| **Lever name uniqueness (gpt-5-nano)** | 75/75 (run 28) | 75/75 (run 35) | UNCHANGED |
| **Cross-call duplicate names** | 0 for all successful models | 0 for all successful models | UNCHANGED (already resolved) |
| **Consequence chain violations (qwen3)** | 45/75 (run 29) | 30/75 (run 36) | IMPROVED |
| **Consequence chain violations (gpt-5-nano)** | 31/75 (run 28) | 38/75 (run 35) | REGRESSED (minor) |
| **Consequence chain violations (gpt-4o-mini)** | 15/45 (run 30, 3 plans) | 75/75 (run 37, 5 plans) | **MAJOR REGRESSION** |
| **Consequence chain violations (haiku)** | 16/61 (run 31) | 17/47 (run 38) | UNCHANGED |
| **Review format violations (qwen3)** | 0/75 (run 29) | 0/75 (run 36) | UNCHANGED |
| **Review format violations (gpt-5-nano)** | 75/75 "Trade-off:" misformat (run 28) | 73/75 violations (run 35) | UNCHANGED (different wrong format) |
| **Placeholder/sentinel lever leakage** | 1 (haiku run 31) | 1 (haiku run 38, sovereign_identity) | UNCHANGED |
| **Avg option chars — gpt-5-nano** | 126.6 (run 28) | 133.4 (run 35) | IMPROVED |
| **Avg option chars — qwen3** | 63.1 (run 29) | 53.4 (run 36) | REGRESSED |
| **Avg option chars — llama3.1** | 95.6 (run 26) | 87.8 (run 33) | REGRESSED (minor) |
| **Avg consequence chars — gpt-5-nano** | 270.3 (run 28) | 260.5 (run 35) | UNCHANGED |
| **Avg consequence chars — qwen3** | 253.3 (run 29) | 208.6 (run 36) | REGRESSED |
| **Hyphen-Strategy naming pattern** | 0 baseline, 0 qwen3, 0 gpt-5-nano (run 28/29) | 16 qwen3, 40 gpt-5-nano, 60 gpt-4o-mini | REGRESSED (new anchoring) |
| **Lever count per plan (gta overflow)** | 0 violations across all models | 4 models produce 16 levers for gta | **NEW REGRESSION** |

---

## New Issues

### N1 — gpt-4o-mini consequence chain: 100% failure (major)
Run 37 (gpt-4o-mini, after) produces plain-prose consequences in every single one of 75 levers — zero chains. Before (run 30, 3 plans), violations were only 15/45 = 33%.

The root cause is the `consequences` Pydantic field description in `identify_potential_levers.py:30–32`, which reads:
> `"Briefly describe the likely second-order effects or consequences of pulling this lever (e.g., 'Choosing a high-risk tech strategy will likely increase talent acquisition difficulty...'). 30 words."`

Run 37's output matches this description precisely: `"Choosing a diversified funding strategy will likely enhance financial stability, increase stakeholder engagement..."`. The PR removed the one incidental chain-format anchor that had been in prompt_0 (`"Systemic: 25% faster scaling through..."`), exposing the schema-level conflict. gpt-4o-mini, which weights schema `Field(description=...)` heavily in structured-output mode, now follows the schema description instead of the system prompt.

This was a latent code bug that the PR made visible. Evidence: `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` (verified).

### N2 — gta plan consistently produces 16 levers (new systematic overflow)
Four models (runs 33, 35, 37, 38) produce 16 levers for the gta_game plan instead of 15. This occurs because one of the three calls returns 6 levers for this plan. Run 29 (before, qwen3) and run 36 (after, qwen3) do not show this for gta, making it inconsistent across models. No per-call validator enforces `len(levers) == 5`, so the overflow silently passes into the final artifact. Evidence: `history/0/33_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` (insight_claude/4 report).

### N3 — Naming over-anchoring pattern shifted form
Replacing `"Material Adaptation Strategy"` with `"[Domain]-[Decision Type] Strategy"` created a new template: models now systematically produce hyphenated names. gpt-4o-mini (run 37) shows 60/75 hyphen-Strategy names vs. 0 in baseline and 0 in run 30. This is the same phenomenon as the "25% faster" leakage — a concrete example in the prompt becomes a strong model anchor. Evidence: `history/0/36_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4` (verified: `"Funding-Subsidy Strategy"`, `"Security-Enforcement Strategy"`, etc.).

### N4 — Surface issues from before that were not fixed
The `options` field description ("2-5 options") still contradicts the system prompt ("exactly 3"), continuing to cause 2-option levers in llama3.1 (9 in run 33, parasomnia) and haiku (2 in run 38). This was identified in synthesis/3 as Direction 3 and carried over unaddressed.

---

## Verdict

**CONDITIONAL**: The PR is a net positive — it eliminates the most pervasive content quality failure (template leakage) and improves gpt-4o-mini reliability from 60% to 100% — but it surfaces a severe new quality failure (100% consequence chain violations for gpt-4o-mini) caused by a pre-existing code bug in the Pydantic field description. The PR should be kept, and the Pydantic field description fix (synthesis/4 Direction #1) must be applied before this iteration can be considered complete.

---

## Recommendations

### Should the next iteration follow the "after" synthesis recommendation?
**Yes.** Synthesis/4 Direction #1 (fix `consequences` and `options` Pydantic field descriptions) is the correct immediate next step. It is the proximate cause of run 37's 100% chain failure, it requires only 3 line changes in `identify_potential_levers.py:30–35`, and it has no regression risk. Apply it before any further prompt iteration so that the schema and system prompt give consistent instructions.

After Direction #1 is applied and re-run, pursue synthesis/4 Direction #2 (per-call validator + retry for lever count, option count, chain format) to catch the gta overflow and residual option-count violations.

### Issues resolved by this PR (can be removed from backlog):
- **"25% faster scaling" template leakage** — eliminated. Do not re-open unless a different literal example is added to the prompt.
- **gpt-4o-mini schema wrapper failures** — resolved by a prior fix (PR #270 serialization fix, confirmed by run 37's 5/5 plans vs run 30's 3/5).
- **Cross-call name duplication** — already low before; now explicitly guarded by exclusion list. No longer a primary concern.

### New issues to add to the backlog:

1. **[HIGH] Fix `consequences` Pydantic field description** — the plain-prose example in `identify_potential_levers.py:30–32` causes gpt-4o-mini (and potentially other schema-sensitive models) to ignore the I→S→S chain instruction entirely. Replace with a format-reinforcing description (see synthesis/4 Direction #1 for exact text).

2. **[HIGH] Fix `options` Pydantic field description** — `"2-5 options"` conflicts with `"exactly 3"` in the system prompt. Change to `"Exactly 3 options."` in `identify_potential_levers.py:34` and in `LeverCleaned` at line 80–82.

3. **[MEDIUM] Add per-call validator: enforce exactly 5 levers per LLM call** — the gta plan produces 6 levers in one of three calls, resulting in a 16-lever merged output for 4/7 models in the after batch. A `@field_validator` on `DocumentDetails.levers` with a retry would catch this.

4. **[MEDIUM] Truncate conversation context for calls 2 and 3** — haiku continues to time out on hong_kong and parasomnia (427 s and 721 s) because calls 2/3 accumulate ~40 KB prior assistant turns. Replacing full assistant replay with a compact summary + name exclusion list would cut call-3 context from ~90 KB to ~12 KB, likely bringing haiku from 3/5 to 5/5.

5. **[LOW] Reduce naming anchor in prompt** — the `"[Domain]-[Decision Type] Strategy"` example is creating a new hyphen-Strategy pattern (0 in baseline → 60/75 in gpt-4o-mini after). Consider replacing with a more abstract instruction or multiple varied examples to reduce over-anchoring.

6. **[LOW] Fix telemetry race** — `set_usage_metrics_path` is called outside `_file_lock` in `runner.py:106`, causing run 38 haiku to produce no `activity_overview.json`. Move inside the existing lock block.

7. **[LOW] Retire nvidia-nemotron-3-nano-30b-a3b from evaluation** — it has now failed in runs 24, 25, and 32 with the same JSON extraction errors. The PR change had zero observable effect on its reliability. Remove from test rotation to save compute.
