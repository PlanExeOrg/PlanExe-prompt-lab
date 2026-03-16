# Synthesis

## Cross-Agent Agreement

All four files agree on the following:

1. **PR #299 achieved its two measurable goals.** Bracket leakage dropped from 37 raw hits to 0; bad summaries dropped from 90/105 to 0/105. Both improvements are confirmed by independent measurement in both insight files.

2. **The new `check_review_format` validator is too weak.** Replacing `'Controls '` / `'Weakness:'` keyword checks with `len >= 20` + no-square-brackets allows arbitrary filler text and loses the tension/weakness structural shape. This is flagged explicitly in code_claude (B1a/C1), code_codex (B1/I1), and insight_claude (N2/C1).

3. **llama3.1 multi-call label-only option degradation is unresolved.** ~33–38% of levers in calls 2/3 collapse to 2–3 word labels (e.g., "Threat Assessment"). This is the same number documented in analysis/18 (B4/code_claude, S2/code_codex, N1/insight_claude, raw-duplication regression/insight_codex).

4. **The runner has a thread-safety gap** on `set_usage_metrics_path` (called outside the lock), confirmed by both code reviews (B2/code_claude, B3/code_codex). Currently masked because llama3.1 runs at workers=1, but will corrupt telemetry if any model uses parallel workers.

5. **The source tree is not synced with PR #299.** The working copy of `identify_potential_levers.py` still contains the pre-PR English-only validator and bracket placeholder field descriptions. Experiments were run on a patched version of the code; the checked-in source does not yet reflect those changes.

---

## Cross-Agent Disagreements

### 1. Overall PR verdict

- **insight_claude**: CONDITIONAL — validator relaxation allows format drift; format consistency across models was inadvertently broken.
- **insight_codex**: KEEP — bracket leakage and summary improvements are dominant wins; duplication regression is orthogonal.
- **code_claude**: Merge with follow-up prompt addition.
- **code_codex**: Keep the direction but tighten the validator implementation before calling it complete.

**Resolution**: All four agree the PR should be kept and that the validator is under-specified. The disagreement is only about urgency. Verdict is **KEEP with a follow-on validator tightening** (see Direction 1).

### 2. Haiku quality ranking

- **insight_claude** ranks haiku #1 (best review quality; substantive multi-clause Weakness sentences; 200-char average).
- **insight_codex** ranks haiku in the weak tier due to 18 fabricated percentage claims in consequences.

**Resolution**: Both observations are correct and non-contradictory. Haiku produces the best *structural* review quality while simultaneously being the worst offender for fabricated quantification in *consequences*. The `consequences` field description mandates "at least one quantitative estimate are mandatory" (lines 38–39), and haiku — the most instruction-following model in the batch — obeys that mandate faithfully by inventing numbers. This is confirmed by reading the source: line 37 says `"e.g. a % change or cost delta"` and line 38 says `"All three labels and at least one quantitative estimate are mandatory."` Haiku's fabrication is caused by the prompt, not by model failure.

### 3. Checkout state interpretation

- **code_claude** reads the current file as pre-PR and identifies all five stale locations (lines 54–57, 95–98, 113–115, 148–151, 179–180).
- **code_codex** references the PR branch by name and identifies the *new* validator as too weak (lines 92, 128, 157, 216 on the PR branch).

**Resolution**: The PlanExe repo is checked out on its own branch separate from the PlanExe-prompt-lab working tree (currently `fix/review-brackets-and-i18n-validator`). The PlanExe repo is on `main` (pre-PR), which is confirmed by reading `identify_potential_levers.py` directly — lines 86–98 show the old `'Controls '`/`'Weakness:'` validator. code_codex inspected the PR branch explicitly (non-merged). Both reports are accurate. The PR has not yet been merged into the PlanExe repo.

---

## Top 5 Directions

### 1. Tighten the `check_review_format` validator: i18n-safe but structurally enforced
- **Type**: code fix
- **Evidence**: B1a/C1 (code_claude), B1/I1 (code_codex), N2/C1 (insight_claude), implied by insight_codex's model ranking table
- **Impact**: Restores cross-model review format consistency without English-only keywords. Currently 10/15 qwen3 reviews and 8/17 gpt-4o-mini reviews use non-"Controls" first sentences ("Balances", "Encourages", "Focuses"). The old validator enforced consistent structure by side-effect; the PR removed enforcement without substituting anything structural. A fixed validator that checks for `vs.` presence (language-agnostic in most European languages) plus two-sentence shape would accept non-English equivalents while rejecting filler. Affects 2/7 models in the current batch (28% of model runs), and the format is consumed by downstream scenario-picker logic.
- **Effort**: low — ~5-line change to `check_review_format` in `Lever`
- **Risk**: Could cause ValidationErrors for models that express tensions without `vs.`-equivalent separators (e.g., some Asian languages). Mitigatable by using a broader pattern or keeping the 20-char floor as a secondary fallback. The `vs.` check would have passed all 35 runs in analysis/19 (every review uses `vs.` or `versus`).

### 2. Reinforce option quality in call-2/3 multi-call prompts
- **Type**: code + prompt fix (one-line change)
- **Evidence**: B4/I1 (code_claude), S2/I2/I3 (code_codex), N1/H2 (insight_claude), raw-duplication regression / H2 (insight_codex)
- **Impact**: Fixes llama3.1 label-only option degradation, which persists at ~33–38% of levers in calls 2/3 across two consecutive batches (analysis/18 run 31: 7/21; analysis/19 run 45: 8/21). Call-1 options are substantive (15–30 words) while call-2/3 collapse to 2–3 word labels ("Threat Assessment", "Closed-Loop Ecology"). The root cause is structural: the call-2/3 prompt prepends only a name-exclusion clause; the quality requirement ("full sentence with action verb") is in the system prompt and decays in attention as the names blacklist grows. The fix (I1/code_claude) is one line: append `"Each option must be a complete strategic sentence (≥15 words with an action verb), not a label.\n"` to `prompt_content` in the call-2/3 branch. This reinforce the quality contract without changing anything that affects call-1 or other models.
- **Effort**: very low — one-line prompt addition in the `else` branch at line 231
- **Risk**: Near-zero. Other models already produce complete options; the reminder is a no-op for them. There is no risk of new ValidationErrors. llama3.1 can produce full options (it does in call-1), so this targets a context-attention problem not a model-capability gap.

### 3. Soften the fabricated-quantification mandate in `consequences`
- **Type**: prompt change (field description)
- **Evidence**: B3/I3 (code_claude), 18/20 fabricated % hits concentrated in haiku (insight_codex metrics table), OPTIMIZE_INSTRUCTIONS "no fabricated numbers" goal
- **Impact**: The `consequences` field description at lines 37–39 says "at least one quantitative estimate are mandatory" with example "e.g. a % change or cost delta." This is a direct instruction to fabricate numbers when none appear in the source plan. Haiku — the highest-quality model and most instruction-following in the batch — produces 18 of the remaining 20 fabricated-percentage claims. Removing "mandatory" and replacing it with "Prefer grounded comparisons; cite specific numbers only when the source document provides them" would reduce fabricated claims in the highest-quality model outputs, improving plan credibility across 5/35 runs while leaving other models largely unaffected. Content quality regressions in the best model's outputs are high-priority because they affect the plans users are most likely to rely on.
- **Effort**: low — field description edit plus matching edit in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` line 163–165
- **Risk**: Low. Some models might become less specific, but specificity without grounding is not an improvement. The change moves toward the OPTIMIZE_INSTRUCTIONS goal ("no fabricated numbers") without touching structural constraints.

### 4. Add minimum-word-count validator to individual options
- **Type**: code fix
- **Evidence**: B2 (code_codex), I5/I2 (code_claude, code_codex), N1 (insight_claude)
- **Impact**: The `options` field description says "a full sentence with an action verb, not a label" (line 48) but the only validator is `check_option_count` which checks `len(v) == 3`. Adding a per-option minimum word count check (e.g., ≥ 8 words with at least one non-title-case word, or simply ≥ 8 words) would catch label-only options at parse time, forcing a retry. Combined with Direction 2 (quality reminder in call-2/3), this creates a two-layer defence: the prompt prevents label generation; the validator ensures any that slip through trigger a retry. This is the validator-level complement to the prompt-level fix in Direction 2.
- **Effort**: medium — new `check_option_quality` field validator in `Lever`, needs careful threshold to avoid false rejections on legitimately short but valid options
- **Risk**: Moderate. Too strict a threshold could cause ValidationErrors on borderline options from models that write terse-but-valid strategies. Needs empirical calibration. Implement Direction 2 first and measure whether label-only options disappear before adding this gate.

### 5. Fix runner thread-safety on global usage metrics path
- **Type**: code fix
- **Evidence**: B2 (code_claude), B3 (code_codex)
- **Impact**: `set_usage_metrics_path()` at runner.py line 106 is called outside the `_file_lock`. With `workers > 1`, Thread A's path can be overwritten by Thread B before Thread A's LLM calls complete, silently routing Thread A's metrics to Thread B's file or to `None`. Currently masked because all models tested use `workers=1`, but any future parallel testing would corrupt `usage_metrics.jsonl` and `track_activity.jsonl` — the primary evidence files for analysis pipeline decisions. Fix by moving `set_usage_metrics_path` inside the lock or by using thread-local storage for the path.
- **Effort**: low — extend the lock scope by 2 lines
- **Risk**: Near-zero. The fix is narrowly scoped and does not affect LLM execution or output content.

---

## Recommendation

**Do Direction 2 first: add a one-line option-quality reminder to the call-2/3 prompt.**

**File**: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
**Location**: lines 231–236 (`else` branch of `if call_index == 1`)
**Current code**:
```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```
**Fixed code**:
```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n"
    f"Each option must be a complete strategic sentence (at least 15 words with an action verb), not a short label.\n\n"
    f"{user_prompt}"
)
```

**Why first**: The llama3.1 label-only option failure is the last consistently failing structural quality dimension across two consecutive batches (analysis/18 and analysis/19), with no improvement. ~38% of levers from llama3.1's calls 2/3 degrade to 2–3 word labels that provide no strategic value. The fix is a single line with zero risk of regression: other models already produce full-sentence options and will ignore the reminder, while llama3.1 is demonstrably capable of complete options (it produces them in call-1) and is failing due to context-attention decay, not capability.

Directions 1 and 3 require more decision-making (what structural check to use for i18n-safe review validation; how to word the softer quantification guidance) and carry slightly higher regression risk. Direction 2 does not require any design choices — it restates an existing contract from the field description in the place where the contract is actually needed.

**Expected outcome**: llama3.1 label-only options in calls 2/3 drop from ~38% to near zero. The 21 raw duplicate names in analysis/19 (all from llama3.1) should also decrease because label generation and name repetition are correlated (the model falls back to minimal-effort output in later calls). No other model or metric should change.

---

## Deferred Items

**Direction 1 (tighten review validator)**: Do second. The approach: check `'vs.' in v.lower()` plus `len(v.split('.')) >= 2` (two-sentence structure) as replacements for the current English-only keywords. This preserves i18n while restoring structural enforcement. The current state (min 20 chars + no brackets) allows any non-trivial string to pass.

**Direction 3 (soften fabricated-% mandate)**: Do third. Change `"All three labels and at least one quantitative estimate are mandatory."` to `"All three labels are mandatory. Use specific numbers only if they appear in the source document — do not invent percentages."` This directly addresses the remaining 20 fabricated-% claims concentrated in haiku.

**Direction 4 (option word-count validator)**: Implement after Direction 2 and measure whether label-only options persist. If Direction 2 (prompt) eliminates them, the code validator becomes optional hardening.

**Direction 5 (runner thread-safety)**: Fix before enabling any parallel model testing. Currently harmless but a latent corruption hazard.

**insight_codex C2 / code_claude I2 — `OPTIMIZE_INSTRUCTIONS` constant**: The constant exists on the PR branch but is not wired into the runtime (code_codex S3). Once PR #299 is merged, add the constant to the system prompt assembly path or at minimum add a comment reference in the validator so reviewers know the policy it is enforcing. This is documentation/maintenance, not a quality fix.

**insight_codex H3 — broader anti-marketing ban**: Removing `"Radical option must include emerging tech/business model"` (line 193) and replacing with `"Include at least one option that challenges the plan's core assumption"` (code_claude I4/S2) would reduce the remaining 18 marketing-language hits. Defer until after the llama3.1 and fabrication fixes are measured.

**insight_claude Q4 — summary field comparison**: The summary field change (prompt_4 → prompt_5 alignment) was confirmed effective by insight_codex (90/105 → 0/105) but not independently verified by insight_claude. No follow-up action needed; codex's quantitative check is sufficient.

**S4 (runner.py `_next_history_counter` not process-safe)**: Low risk in practice (prompt-lab is typically run from a single process). Deferred until CI matrix or parallel runner usage is planned.
