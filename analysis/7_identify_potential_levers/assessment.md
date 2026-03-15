# Assessment: Iteration 7 — Schema Contract Enforcement (lever count + required summary)

## Issue Resolution

**What the PR fixed (inferred from code evidence; no `pr_title` in meta.json):**

Based on code_claude batch 7 review (S2 notes `summary: str` with no default; I4 describes `levers` with `min_length=5, max_length=5`) and the confirmed batch 7 outcomes (P1: zero lever-count violations; P2: summaries now populated), the PR implemented synthesis/6 Direction 1 — the two targeted schema field changes in `identify_potential_levers.py`:

- **Change A** — `DocumentDetails.levers` constrained to `min_length=5, max_length=5` (from unconstrained `list[Lever]`).
- **Change B** — `summary: str = Field(...)` (from `Optional[str] = None`).

**Is the primary issue resolved?**

Yes, partially:

1. **Lever count enforcement — RESOLVED.** Batch 6 produced one 16-lever artifact (run 52, hong_kong_game) because haiku returned a 6-lever response that was silently accepted. Batch 7 shows zero lever-count violations across all 27 successful runs (all produce exactly 3×5=15 levers). Source: `history/0/56_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` — each of three responses has exactly 5 levers.

2. **Null summaries — RESOLVED.** Batch 6 had 28 null summaries (14 from llama3.1/run 47, 10 from gpt-oss-20b/run 48, 4 from gpt-4o-mini/run 51). Batch 7 has zero null summaries across all successful runs. Source: `history/0/56_identify_potential_levers/outputs/20250321_silo/002-9-potential_levers_raw.json` contains populated summaries in all three response objects.

**Residual symptoms:**

1. **qwen3-30b contamination unchanged.** 100% of consequences in run 57 end with review text (`Controls … Weakness: …`). Verified in `history/0/57_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json` — all 15 visible levers contaminated. The multi-call chat structure (synthesis/6 Direction 2) remains unimplemented.

2. **gpt-oss-20b failure mode introduced.** `max_length=5` enforcement causes hard Pydantic failures when gpt-oss-20b over-generates a 6th lever. Before the change, 6-lever responses silently flowed through (batch 6: 5/5 success); with it enforced, trailing content causes `"Invalid JSON: trailing characters at line 11 column 4"` and the entire plan fails. Verified in `history/0/55_identify_potential_levers/outputs.jsonl` lines 3 and 5.

3. **llama3.1 review format has regressed.** Batch 6 assessment confirmed llama3.1 went from 17/75 missing review components to 0 violations (run 47). Batch 7 (run 54) shows the alternating pattern has returned: lever 1 review `"Controls Resource Optimization vs. Human Labor Costs."` (no Weakness), lever 2 `"Weakness: The options fail to consider…"` (no Controls). Codex constraint table confirms: 9 missing trade-off, 6 missing weakness across run 54. Likely caused by the mandatory `summary` field consuming llama3.1's output budget.

---

## Quality Comparison

Models compared: those present in **both** batches — nemotron (46→53), llama3.1 (47→54), gpt-oss-20b (48→55), gpt-5-nano (49→56), qwen3-30b (50→57), gpt-4o-mini (51→58), haiku (52→59).

| Metric | Before (runs 46–52) | After (runs 53–59) | Verdict |
|--------|---------------------|---------------------|---------|
| **Overall success rate** | 30/35 = 85.7% | 27/35 = 77.1% | REGRESSED |
| **nemotron success rate** | 0/5 (run 46) | 0/5 (run 53) | UNCHANGED |
| **llama3.1 success rate** | 5/5 (run 47) | 5/5 (run 54) | UNCHANGED |
| **gpt-oss-20b success rate** | 5/5 (run 48) | 3/5 (run 55; trailing-char errors) | REGRESSED |
| **gpt-5-nano success rate** | 5/5 (run 49) | 5/5 (run 56) | UNCHANGED |
| **qwen3-30b success rate** | 5/5 (run 50) | 4/5 (run 57; gta_game JSON truncation) | REGRESSED |
| **gpt-4o-mini success rate** | 5/5 (run 51) | 5/5 (run 58) | UNCHANGED |
| **haiku success rate** | 5/5 (run 52) | 5/5 (run 59) | UNCHANGED |
| **Lever count violations (>15 merged)** | 1 (run 52, hong_kong_game: 16 levers) | 0 | **IMPROVED** |
| **Null summaries (batch-wide)** | 28 (14 llama3.1 + 10 gpt-oss-20b + 4 gpt-4o-mini) | 0 | **IMPROVED** |
| **Bracket placeholder leakage** | 0 | 1 (run 59, haiku, sovereign_identity: `[specific pathway]`) | REGRESSED |
| **Option count violations (≠3 options)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | 15/15 per plan (all successful runs) | 15/15 per plan (all successful runs) | UNCHANGED |
| **Cross-call name duplication** | 0 (all runs) | 0 (all runs) | UNCHANGED |
| **Review format compliance — llama3.1** | 0 violations (run 47; both components present) | 9 missing trade-off, 6 missing weakness (run 54) | **REGRESSED** |
| **Review format compliance — other models** | 0 violations | 0 violations | UNCHANGED |
| **qwen3-30b consequence contamination** | 75/75 (100%) with Controls + Weakness leaked (run 50) | 60/60 (100%) across successful plans (run 57) | UNCHANGED |
| **Consequence I→S→S chain — all models** | Present in all successful runs | Present in all successful runs | UNCHANGED |
| **Measurable indicators — llama3.1** | 0/75 (run 47, codex: "Missing numeric: 75") | 59/75 missing (run 54) | SLIGHTLY IMPROVED |
| **Measurable indicators — haiku** | Present in all (run 52) | Present in all (run 59) | UNCHANGED |
| **Avg option chars — llama3.1** | 58.4 chars (run 47, codex full-batch avg) | 87.7 chars (run 54, codex full-batch avg) | **IMPROVED** |
| **Avg option chars — haiku** | 361.1 chars (run 52, codex) | 374.3 chars (run 59, codex) | UNCHANGED |
| **Avg option chars — gpt-5-nano** | 117.0 chars (run 49, codex) | 125.6 chars (run 56, codex) | UNCHANGED |
| **Avg consequence chars — haiku** | 1060.1 chars (run 52, codex full-batch avg) | 1127.1 chars (run 59, codex full-batch avg) | SLIGHTLY REGRESSED |
| **Avg consequence chars — llama3.1** | 142.0 chars (run 47, codex) | 165.1 chars (run 54, codex) | SLIGHTLY IMPROVED |
| **haiku max plan duration** | 223.84s (run 52, parasomnia) | 470.35s (run 59, hong_kong_game; status OK) | REGRESSED |
| **Raw-call responses per file (≡5 levers each)** | Mostly exact, 1 exception (run 52: 6-lever response) | All exact (schema enforced) | **IMPROVED** |

Sources: insight_claude.md, insight_codex.md, and code_claude.md/code_codex.md for both batches; directly verified from `history/0/{47,52,54,55,57,59}_identify_potential_levers/outputs.jsonl` and `*/outputs/20250321_silo/002-10-potential_levers.json`.

---

## New Issues

### N1 — gpt-oss-20b regression: 5/5 → 3/5 (side effect of `max_length=5` enforcement)

`max_length=5` converts gpt-oss-20b's silent over-count into a hard plan failure. When the model generates a 6th lever, the trailing content causes `"Invalid JSON: trailing characters at line 11 column 4"`. Two plans fail: sovereign_identity and parasomnia_research_unit. The code has no truncation/recovery path — the exception is immediately re-raised, failing the entire plan. Before schema enforcement, the 6th lever was silently merged into the artifact (or may have caused an over-count); now it causes a hard failure. Source: `history/0/55_identify_potential_levers/outputs.jsonl` lines 3 and 5.

This issue has a known fix (synthesis/7 Direction 2): catch `json_invalid: trailing characters`, truncate at the last valid closing brace, and re-validate.

### N2 — llama3.1 review format alternation has returned (regression from batch 6 fix)

Batch 6 assessment confirmed the alternating Controls-only / Weakness-only pattern was fixed (0 violations, run 47). Batch 7 (run 54) shows it has returned. Direct evidence in `history/0/54_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

- Lever 1 review: `"Controls Resource Optimization vs. Human Labor Costs."` (no Weakness)
- Lever 2 review: `"Weakness: The options fail to consider…"` (no Controls)
- Lever 3 review: `"Controls Information Flow vs. Individual Freedom."` (no Weakness)

The most likely cause: required `summary: str` is consuming llama3.1's output budget, displacing capacity from the `review_lever` field that was previously used for dual-component reviews.

### N3 — qwen3-30b has a new failure mode: gta_game JSON truncation

Run 57 (qwen3-30b) fails on gta_game with `"Invalid JSON: expected ',' or ']' at line 1 column 3625"`. The model's output was truncated mid-JSON. This is distinct from gpt-oss-20b's trailing-character failure. Likely cause: the mandatory `summary` field increases per-call output length, pushing total token count past a truncation threshold. Source: `history/0/57_identify_potential_levers/outputs.jsonl` line 2.

### N4 — haiku (run 59) produces a bracket placeholder for the first time

`history/0/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json` contains the option `[specific pathway]` — a literal bracket placeholder that the prompt explicitly prohibits. This is the first confirmed placeholder violation from haiku across multiple batches. The violation may be related to the hong_kong_game plan's extreme verbosity (470.35s) consuming model capacity, or the model's increased verbosity drifting from format discipline at longer outputs.

### N5 — haiku (run 59) hong_kong_game duration: 470.35s (above previous timeout threshold)

`history/0/59_identify_potential_levers/outputs.jsonl` line 5: `{"name": "20260310_hong_kong_game", "status": "ok", "duration_seconds": 470.35}`. The run completed successfully, but 470.35s exceeds the 432s threshold at which parasomnia previously timed out (run 45). This suggests either: (a) the API timeout has been raised, or (b) hong_kong_game happened to stay below the ceiling. Haiku's average consequence length has crept from ~550 chars (run 52) to ~1127 chars (run 59, codex full-batch average) — a 2× increase that may continue to erode the timeout fix from batch 5.

### N6 — `summary` is required but discarded by `save_clean()`

code_codex S1 identifies this: `summary: str` is required in `DocumentDetails`, stored in `002-9-potential_levers_raw.json`, but `save_clean()` does not write it to `002-10-potential_levers.json`. Each of 3 LLM calls per plan must generate a required paragraph that has no effect on the final scored artifact. This adds latency and parse-failure risk for weaker models (directly contributing to N1 and N3) with zero output benefit.

---

## Verdict

**CONDITIONAL**: The schema enforcement changes (lever count + required summary) are the correct direction and the specific problems they addressed (16-lever artifacts, null summaries) are genuinely resolved. However, the enforcement introduced a hard regression — overall success rate dropped from 85.7% to 77.1% — primarily because `max_length=5` converts gpt-oss-20b's over-generation from a silent overflow into a hard plan failure, and `summary: str` adds output pressure that reverts llama3.1's review format to the alternating pattern. The PR is a keeper if, and only if, the gpt-oss-20b trailing-character recovery path (synthesis/7 Direction 2) is implemented in the next iteration.

---

## Recommendations

### Should the next iteration follow the synthesis/7 recommendation?

**Yes — implement synthesis/7 Direction 1 (reset message context for calls 2 and 3) as the primary change.**

This is the highest-priority unresolved issue: qwen3-30b has had 100% consequence contamination for three consecutive batches (runs 43, 50, 57 ≈ 180 corrupted levers total). The root cause is confirmed in source code at `identify_potential_levers.py:196–244`. The fix is low-effort (construct fresh message list per call rather than accumulating prior assistant JSON) and preserves diversity via the name-exclusion blacklist.

**Simultaneously, implement synthesis/7 Direction 2 (truncation recovery for trailing-character failures).**

This directly restores gpt-oss-20b from 3/5 to ~5/5 success and is the critical fix needed to make the batch 7 schema enforcement a net improvement rather than a net regression. Without this fix, the PR's success-rate regression (-8.6pp) is unresolved.

**Revisit `summary` field design before the next iteration.**

`summary: str` adds mandatory generation burden (3 calls × 5 plans per model) that: (a) reverted llama3.1's review format, (b) may be causing qwen3-30b's JSON truncation, (c) is never written to the final artifact. Options: make `summary: Optional[str]` again (reduces pressure, loses self-evaluation signal), or confirm it contributes to lever quality indirectly and accept the trade-off. At minimum, reduce from 3×-required to 1×-required (only call 1) if the field has no downstream use.

### Issues from before that are now resolved:

- **Lever count overflow** (batch 6 N1: run 52 16-lever artifact) — resolved by `max_length=5` enforcement. Remove from active backlog.
- **Null summaries** (batch 6 metrics: 28 total) — resolved by `summary: str`. Remove from active backlog.
- These are genuine improvements. The enforcement mechanism is correct; only the recovery path for over-generation is missing.

### New issues to add to the backlog:

1. **[HIGH] Trailing-character recovery for `max_length=5` enforcement** — When a model over-generates a 6th lever, truncate the raw JSON at the last valid closing brace and re-validate rather than failing the whole plan. Directly restores gpt-oss-20b to ~100% success. Synthesis/7 Direction 2 (code_claude B2/I2, code_codex S2/I4).

2. **[HIGH] Multi-call chat structure: fresh context for calls 2 and 3** — Build a new `[SYSTEM, USER(user_prompt + name-exclusion)]` list per call without injecting prior assistant JSON. Eliminates qwen3-30b 100% contamination (three consecutive batches). Synthesis/7 Direction 1 (code_claude B1/I1, code_codex B1/I1). Already in backlog from batch 6; still unimplemented.

3. **[MEDIUM] llama3.1 review format regression** — The alternating Controls-only / Weakness-only pattern has returned (batch 7, run 54: 9 missing trade-off + 6 missing weakness). Likely caused by mandatory summary consuming output budget. Investigate by making summary optional for the next llama3.1 test run. If confirmed, add a note to the review format fix that it depends on available output capacity.

4. **[MEDIUM] haiku consequence verbosity drift** — Average consequence chars for haiku: ~550 (run 52) → ~1127 (run 59, codex). hong_kong_game took 470.35s in run 59, exceeding the 432s threshold where parasomnia previously timed out. The batch 5 length fix may be eroding. Add a consequence length monitor and consider adding an explicit per-consequence word ceiling in the prompt or schema field description.

5. **[MEDIUM] `summary` field design** — `summary: str` is required (adds parse-failure risk) but discarded by `save_clean()`. Decide: (a) remove entirely if no downstream use, (b) make `Optional[str]` with a note, or (c) write it to the artifact if it has value. The current state (required + discarded) is the worst of both options.

6. **[LOW] qwen3-30b gta_game JSON truncation** — Run 57 fails with output truncated at column 3625. May resolve once multi-call chat structure is fixed (less total output per call). If it persists, add a per-call max_tokens guard for qwen3-30b specifically.

7. **Items carried from batch 6 backlog (unchanged priority):**
   - [LOW] Skip nemotron-3-nano-30b-a3b (six consecutive 0/5 batches; 8 min wasted per batch)
   - [LOW] Thread-safety: move `set_usage_metrics_path` inside `_file_lock` in `runner.py:106,140`
   - [LOW] Investigate baseline contamination for use as quality reference
