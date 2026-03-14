# Synthesis

## Cross-Agent Agreement

Both insight agents (claude, codex) agree on:
- Three runs are completely unusable: **run 03** (schema mismatch), **run 06** (JSON extraction failure), **run 08** (LLM not found).
- **Run 00** has bracket-placeholder leakage surviving to final artifacts (levers 6–10, second LLM call, silo plan).
- **Run 05** copies the `"Material Adaptation Strategy"` example name verbatim into unrelated domains.
- **Baseline** itself contains ~33% cross-call lever-name duplication — it is not a clean gold standard.
- **Run 09** (claude-haiku-4-5-pinned) produces the richest content depth but has structural violations (option-count errors in three levers across three plans).
- **Run 02** achieves perfect name uniqueness (75/75) but drifts from the required `Controls X vs. Y` review format (60 violations).

Both code review agents (claude, codex) agree on:
- **B1**: The first LLM call receives the user prompt twice (`SYSTEM → USER(prompt) → USER(prompt)`); calls 2 and 3 see the correct `→ ASSISTANT → USER("more")` pattern.
- **No post-call validation**: placeholder leakage, option-count violations, and format drift all survive to final `002-10` files because nothing validates them.
- **No model preflight**: model resolution happens per-plan inside each thread, so a bad alias produces one silent failure per plan rather than one early abort.
- **Thread-safety gap**: `set_usage_metrics_path()` runs outside the lock; concurrent plans can overwrite each other's metrics target.
- **Merge is a blind concatenation**: three independent calls produce the same themes and names; no deduplication at merge time.

---

## Cross-Agent Disagreements

### 1. Run 01 final success rate

`insight_claude` reports run 01 (gpt-oss-20b) as **2/5** successful. `insight_codex` reports it as **5/5** with "retry-heavy" notes and "empty/non-JSON reply on retries" as the key failure mode. The codex insight explicitly shows `Final=15` for run 01 in its operational table, indicating all five plans produced valid merged lever files.

**Who is right**: codex. The claude insight appears to count non-retried plan attempts from `outputs.jsonl` (which includes intermediate error rows), while codex counts final artifacts that actually exist on disk. The runner's resume logic re-runs errored plans and appends a new `ok` row to `outputs.jsonl`; plans with an eventual `ok` row produce valid output files. Run 01 most likely succeeded 5/5 at the artifact level after retries. This is also consistent with codex bug B3 (runner summarizes by raw row count, not latest-status-per-plan), which would make claude's reading of `outputs.jsonl` count both error and ok rows for the same plan.

### 2. Run 00 final success rate

`insight_claude` reports run 00 as **4/5** (80%). `insight_codex` reports **5/5**. Same explanation: claude counted non-retried attempts from `outputs.jsonl`; codex counted final artifacts. The gta_game timeout/retry evidence cited by claude (two rows in `outputs.jsonl`, one error and one ok) actually confirms the retry succeeded, making run 00 5/5 at the artifact level.

### 3. Overall 56% success rate (insight_claude)

`insight_claude` derives 28/50 from a 10-run × 5-plan grid. Given the run 00 and run 01 recount above, the actual artifact-level success rate is closer to **35/50 (70%)**. The 56% figure comes from reading error rows in `outputs.jsonl` without deduplication — which is itself bug B3 in the codex code review.

### 4. Field description vs. system prompt contradiction (B7)

Only `code_claude` flagged this: `Lever.options` field description says `"2-5 options for this lever."` while the system prompt says `"exactly 3"`. Verified in source at `identify_potential_levers.py:33–35`. `code_codex` did not flag this specifically, though it covered the general absence of validation. B7 is a real confirmed bug — structured-output providers use field descriptions to constrain generation, so `"2-5 options"` gives models latitude to deviate from the `"exactly 3"` rule.

### 5. Runner summary counting bug (B3 in codex)

Only `code_codex` flagged the `main()` summary logic at `runner.py:464–468` as counting all rows in `outputs.jsonl` rather than the latest status per plan. Verified in source: `total = len(plans)` counts every appended row, not unique plan names. On a run with retries, a plan that fails once and succeeds once is counted twice in `total` and its two `duration_seconds` values are both summed. This is confirmed.

---

## Top 5 Directions

### 1. Fix the doubled user prompt (B1)

- **Type**: code fix
- **Evidence**: Both code review agents. Confirmed in source at `identify_potential_levers.py:148–174`. `chat_message_list` is initialized with `[SYSTEM, USER(user_prompt)]`, then the loop appends `user_prompt` again for the first iteration, producing `SYSTEM → USER(prompt) → USER(prompt)` on call 1. Calls 2 and 3 have a normal `→ ASSISTANT → USER("more")` extension.
- **Impact**: Affects every run, every model, every plan. The non-standard two-consecutive-USER sequence at call 1 is the most plausible structural cause of intra-run inconsistency (run 00's call 2 leakage, while calls 1 and 3 were clean, is consistent with a malformed call-1 history flowing into call 2). Fixing this normalizes the conversation structure for all three calls.
- **Effort**: Low. One-line change: either remove the initial `USER(user_prompt)` from `chat_message_list` initialization (keep only `SYSTEM`), or change `user_prompt_list` from `[user_prompt, "more", "more"]` to `["more", "more"]`.
- **Risk**: Minimal. The fix makes all three calls structurally uniform. The model still receives the plan content (on call 1 either via the seeded USER message or via the loop's first item). Behavior for Tier-1 models is unlikely to regress.

---

### 2. Align field description with system prompt on option count (B7)

- **Type**: code fix
- **Evidence**: `code_claude` only; confirmed by reading source at `identify_potential_levers.py:33–35`. Field description: `"2-5 options for this lever."` System prompt: `"exactly 3 qualitative strategic choices."` Structured-output providers use field descriptions to constrain generation; the mismatch gives models latitude to produce 2 or 4 or 5 options.
- **Impact**: Directly explains option-count violations in run 00 (7 violations) and run 09 (3 violations). Fixing the field description to `"Exactly 3 options for this lever."` closes the ambiguity for every model that uses structured output.
- **Effort**: Low. One-line change in the `Lever` Pydantic model.
- **Risk**: Negligible. The system prompt already says "exactly 3"; the field description is just catching up.

---

### 3. Add post-call validation before accepting each response (B3/claude, B2/codex)

- **Type**: code fix
- **Evidence**: Both code review agents. No validation currently exists between the LLM call and the merge step (`identify_potential_levers.py:204–223`). All of the following survive to `002-10` files: bracket placeholders in `review_lever` fields (run 00, run 02), option-count deviations (runs 00, 09), consequence chain label omissions (runs 05, 07), review template drift (run 02).
- **Impact**: Adding a post-call validator that checks (a) exactly 5 levers, (b) exactly 3 options per lever, (c) no `[…]` bracket patterns in any string field, and (d) `review_lever` starts with `Controls` and contains `Weakness:`, then retries on failure, would eliminate all observed output-quality violations across all models. This is a single fix point that catches what the prompt cannot reliably enforce.
- **Effort**: Medium. Requires a validation function and retry loop inside `execute()`. The retry loop already conceptually exists at the runner level; moving it inside `execute()` per-call is the key change.
- **Risk**: Low. Retry on validation failure adds latency but not correctness risk. The retry budget should be bounded (e.g., max 2 retries per call).

---

### 4. Add model preflight validation before plan loop (B5/claude, S4/codex, I4/codex)

- **Type**: code fix
- **Evidence**: Both code review agents. In `runner.py`, `LLMModelFromName.from_names()` is called inside `run_single_plan()` (line 93), once per plan. Run 08 wasted 5 × 0.01–0.02s on "LLM not found" failures because the model alias was unresolvable and this was only discovered at per-plan execution time.
- **Impact**: A preflight call to `LLMModelFromName.from_names()` at the top of `run()`, before the plan loop, surfaces bad model aliases immediately with a single clear error rather than producing five silent failures. Prevents the entire class of run 08 failures for any future misconfigured model.
- **Effort**: Low. Add one call before the plan loop starts.
- **Risk**: Negligible. The preflight call is read-only (model resolution only).

---

### 5. Remove or replace the "Material Adaptation Strategy" example in the prompt (H1/insight_claude, H3/insight_codex)

- **Type**: prompt change
- **Evidence**: Both insight agents, independently. The system prompt at the "Strategic Framing" section uses `"Material Adaptation Strategy"` as an illustrative example lever name. Run 00 produces this name verbatim as lever 1 and lever 11 (cross-call duplication of the example). Run 05 produces it in unrelated domains (GTA game, parasomnia research). The baseline does not contain this name — it was generated with a different model that did not anchor on the example.
- **Impact**: Models susceptible to example anchoring (ollama-llama3.1, qwen3-30b-a3b confirmed) copy the example name directly. Replacing the example with a more abstract name (e.g., `"Stakeholder Coordination Approach"`) or adding an explicit prohibition (`"Do not reuse example phrases from this prompt verbatim"`) eliminates this anchoring for the affected models.
- **Effort**: Very low. One-line prompt edit.
- **Risk**: Low. Changing the example name has no structural effect on capable models that already ignore it (runs 02, 07, 09 showed no example leakage).

---

## Recommendation

**Fix the doubled user prompt (Direction 1 — B1).**

This is the single best first change because:

1. It is confirmed in source code at `identify_potential_levers.py:148–174`.
2. It affects every run, every model, and every plan — no model escapes the malformed `SYSTEM → USER → USER` sequence on the first call.
3. It is the most structurally plausible root cause of the intra-run inconsistency pattern (run 00 silo: calls 1 and 3 clean, call 2 with bracket leakage — call 2 is the first call that operates on a conversation history built from the malformed call 1 exchange).
4. It is a single-line fix with no downside risk.

**Exact change** in `identify_potential_levers.py`:

Option A — remove the initial user message and let the loop handle all three turns:

```python
# BEFORE (lines 148–157):
chat_message_list = [
    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
    ChatMessage(role=MessageRole.USER, content=user_prompt),  # ← remove this
]
user_prompt_list = [user_prompt, "more", "more"]

# AFTER:
chat_message_list = [
    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
]
user_prompt_list = [user_prompt, "more", "more"]
```

Option B — keep initialization, drop the first item from the loop list:

```python
user_prompt_list = ["more", "more"]  # ← call 1 uses the seeded USER message; calls 2,3 extend with "more"
```

Option A is cleaner: all three user turns are managed uniformly by the loop. After this fix, the conversation sequence will be `SYSTEM → USER(prompt) → ASSISTANT → USER("more") → ASSISTANT → USER("more")` for all three calls.

---

## Deferred Items

**Near-term (do after Recommendation):**

- **B7: Fix field description to `"Exactly 3 options for this lever."`** (Direction 2). One-line fix; eliminates the option-count violation source for all models.
- **B3/B2: Post-call validation + retry** (Direction 3). Catches placeholder leakage, option-count drift, and format violations before they reach the merged output. Medium effort but high correctness payoff.
- **B5/S4: Model preflight validation** (Direction 4). Prevents run-08-class failures. Low effort.
- **H1: Remove "Material Adaptation Strategy" example** (Direction 5). Prompt-only change; affects example-anchoring-susceptible models.

**Lower priority:**

- **B4/C3: Deduplicate lever names at merge time** before writing `002-10`. Downstream `002-11` already handles this, but moving it earlier improves `002-10` artifact quality. Medium effort; requires deciding on a deduplication strategy (drop later duplicates vs. rename).
- **B6 (claude) / I6 (codex): Thread-safety — move `set_usage_metrics_path()` inside the lock** or make usage tracking per-thread. Only relevant when `workers > 1`.
- **B3 (codex): Fix `main()` summary to count unique plans** by latest status rather than all rows in `outputs.jsonl`. Low effort; prevents misleading totals on resumed runs.
- **S2/I5: Serialize assistant history as a compact JSON string**, not a raw `model_dump()` dict, so the conversation history fed to calls 2 and 3 matches what the model originally generated.
- **H3/insight_claude: Add explicit `"Measurable outcome:"` suffix** to the consequence format requirement. Would push mid-tier models toward more quantitative outputs. Low effort prompt change; uncertain impact on weaker models.
- **H5/insight_codex: Add an explicit self-check count** (`"Count options before finalizing; every lever must have exactly 3 options"`) to the prompt. Marginal incremental benefit once B7 is fixed, since the field description will already say "exactly 3".
- **S3 (runner): Validate output files on resume** before deciding to skip a plan. Detects stale partial outputs from mid-write crashes.
