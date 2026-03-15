# Assessment: Fix multi-call chat history contamination (inferred)

> **Note**: Neither `meta.json` contains a `pr_title` or `pr_description` field.
> The PR is inferred from context: the before synthesis (analysis/7) ranked
> "Reset message context for calls 2/3" as Direction #1 (highest priority), and
> the after analysis's new B1 is a *different* bug (count contract mismatch),
> not the original chat-history contamination — strongly suggesting the
> contamination fix was applied between runs 59 and 60.
> Git log: PR #276 = "enforce schema contract" (most recent before this batch).

---

## Issue Resolution

**Target issue**: Multi-call chat history contamination (before B1). Lines 234–242
of the runner appended the prior call's assistant JSON to calls 2 and 3, causing
qwen3-30b to output field-boundary-contaminated content at 100% rate (persistent
across runs 43, 50, 57).

**Model mapping** — both batches are identical in model lineup (same 7 models,
same order):

| Run (before) | Run (after) | Model |
|---|---|---|
| 53 | 60 | nemotron-3-nano-30b |
| 54 | 61 | llama3.1 (ollama) |
| 55 | 62 | gpt-oss-20b |
| 56 | 63 | gpt-5-nano |
| 57 | 64 | qwen3-30b |
| 58 | 65 | gpt-4o-mini |
| 59 | 66 | haiku-4-5 |

**Is the original issue resolved?**

Partially. qwen3-30b's contamination rate dropped from ~100% (run 57: all levers
across all 5 plans contaminated) to ~80% (run 64: 60/75 levers contaminated).
This is consistent with the fix cleaning up calls 2/3 but not eliminating qwen3's
intrinsic field-boundary leakage on call 1.

gpt-oss-20b improved from 3/5 success (run 55, trailing-char JSON failure in B2)
to 5/5 (run 62, described as "most spec-compliant"). This is the clearest win.

**Residual symptoms**:
- qwen3-30b (run 64): still 60/75 levers contaminated (80%); the after analysis
  identifies this as a *different* root cause — model puts "Controls X vs Y" text
  in the `consequences` field rather than `review` (field-boundary leakage
  intrinsic to qwen3, not caused by chat history).
- A new primary bug emerged (count contract mismatch, see Section C), suggesting
  the code change that fixed chat history may have simultaneously introduced or
  surfaced the count contract issue.

---

## Quality Comparison

All 7 models appear in both batches; all are eligible for comparison.

| Metric | Before (runs 53–59) | After (runs 60–66) | Verdict |
|--------|---------------------|--------------------|---------|
| **Success rate** | 27/35 = 77.1% (nemotron 0/5, gpt-oss-20b 3/5) | ~30/35 = ~85.7% (nemotron 0/5, others 5/5) | IMPROVED |
| **Lever count per plan (contract)** | 15 levers (3 calls × 5) — compliant for all models | gpt-4o-mini/gpt-oss-20b/gpt-5-nano: 15; llama3.1: ~21 (7 per call); haiku: 19 (silo plan verified) | REGRESSED |
| **qwen3 field contamination rate** | ~75/75 (100%) per plan set | 60/75 (80%) per plan set | MARGINALLY IMPROVED |
| **Option count violations (≠3)** | gpt-4o-mini: 0/15; haiku: 0/15 (verified) | gpt-4o-mini: 0/15; haiku: 0/19 (all 3-option, verified) | UNCHANGED |
| **Bracket placeholder leakage** | Not observed in sampled outputs | Not observed in sampled outputs | UNCHANGED |
| **Template leakage ("Silo-" prefix)** | gpt-4o-mini run 58: 15/15 "Silo-[X] Strategy" | gpt-4o-mini run 65: 15/15 "Silo-[X] Strategy" | UNCHANGED |
| **Review format compliance** (`Controls X vs Y`) | gpt-4o-mini: 15/15; haiku: 15/15 (verified) | gpt-4o-mini: 15/15; haiku: 19/19 (verified) | UNCHANGED |
| **Consequence chain format** (`Immediate → Systemic → Strategic`) | gpt-4o-mini: 15/15; haiku: 15/15 (verified) | gpt-4o-mini: 15/15; haiku: 19/19 (verified) | UNCHANGED |
| **Content depth (option length)** | haiku: ~100–200 chars/option; gpt-4o-mini: ~70–120 chars/option | haiku: ~200–300 chars/option; gpt-4o-mini: ~70–120 chars/option | IMPROVED (haiku) |
| **Cross-call lever duplication** | Minimal for gpt-4o-mini/haiku (15 unique levers, verified) | gpt-4o-mini: minimal; haiku: 3+ duplicate-topic pairs visible in silo plan alone | REGRESSED (haiku) |
| **Lever name uniqueness** | haiku run 59: 15/15 unique names | haiku run 66: ~16–17/19 unique (dedup needed) | REGRESSED (haiku) |
| **gpt-oss-20b success rate** | 3/5 (trailing-char JSON; B2 before) | 5/5 (clean formatting, spec-compliant) | IMPROVED |
| **nemotron success rate** | 0/5 (complete failure) | 0/5 (JSON extraction failure) | UNCHANGED (still broken) |
| **llama3.1 lever count** | Not flagged as primary issue | 7 levers/call (21 merged) instead of 5 | REGRESSED |

**Evidence for haiku count regression (primary new defect)**:
- Run 59 silo plan: exactly 15 levers (3 calls × 5) — file verified.
- Run 66 silo plan: 19 levers — file verified. Duplicate topic clusters confirmed:
  "Population Curation & Reproduction Policy" + "Reproductive Licensing &
  Demographic Stability Framework" (both reproduction policy); "Vertical
  Compartmentalization & Cross-Floor Mobility Strategy" + "Vertical Stratification
  & Inter-Floor Connection Topology Strategy" (both floor topology); "Information
  Architecture & Narrative Control" + "Archived Knowledge & Historical Narrative
  Management Strategy" (both information/narrative).

---

## New Issues

**Introduced by this change:**

1. **Count contract mismatch** (after B1, high severity). The follow-up call
   hardcodes "5 to 7 MORE levers" while the system prompt says "EXACTLY 5."
   The schema `DocumentDetails.levers` now allows 5–7. These three sources are
   mutually inconsistent. haiku (most instruction-following) obeys the "5–7"
   call-level instruction, producing 19 merged levers. llama3.1 produces 7/call
   = ~21 merged. gpt-4o-mini ignores the expanded allowance and produces 5/call
   = 15 merged (unchanged). The new code fix appears to have widened the schema
   or changed follow-up call wording as part of enforcing the schema contract.

2. **Cross-call duplicate levers** (after B4, medium severity, consequence of
   #1). When haiku generates 7 levers per call instead of 5, the three calls
   overlap more heavily. The merge loop has no deduplication, so duplicates are
   silently saved. Without count + dedup enforcement, the 15-lever contract is
   unenforceable.

**Latent issues surfaced (pre-existing, now more visible):**

3. **qwen3 intrinsic field-boundary contamination**. The before analysis
   attributed qwen3's failure entirely to chat history contamination. The after
   evidence (still 60/75 contaminated even with the fix) reveals qwen3 has an
   additional independent contamination pattern — placing "Controls X vs Y" text
   in `consequences` rather than `review`. This was masked by the more explosive
   chat-history failure mode.

4. **No retry on JSON extraction failure** (after B2). nemotron fails with JSON
   extraction error (run 60) rather than the "0/5 no output" failure of before
   (run 53). The error mode changed but the outcome is identical. The after
   code_codex identified that the prompt-optimizer runner disables retry behavior
   the main pipeline uses.

---

## Verdict

**CONDITIONAL**: The change achieved its primary goal (gpt-oss-20b improved from
3/5 to 5/5; qwen3 contamination rate dropped from 100% to 80%; overall batch
success rate improved from 77.1% to ~85.7%), but introduced a high-severity count
contract mismatch that causes haiku (the best-quality model) to overgenerate
(19 vs. expected 15 levers) and llama3.1 to produce 21 levers, both with
downstream cross-call duplication. The PR is a keeper only if the count contract
mismatch is fixed in the next iteration before the outputs are used by downstream
consumers.

**Conditions required to promote unconditionally:**
1. Align follow-up call wording and schema `max_items` to "exactly 5" (two
   one-line changes per the after synthesis Direction 1).
2. Add post-merge count assertion: reject or truncate plans with ≠ 15 levers.
3. Add lever-name deduplication before saving.

---

## Recommendations

**Should the next iteration follow the after synthesis Direction 1?**

Yes. Direction 1 ("Fix lever-count contract: align schema + follow-up call with
'exactly 5'") is confirmed as the root cause of the most impactful new regression
and requires only two one-line changes (schema `max_items`, follow-up call
wording). It is the correct next fix.

**Issues from before that are now resolved (remove from backlog):**
- gpt-oss-20b trailing-char JSON failure (B2 before): **RESOLVED**. Run 62 is
  5/5 with clean formatting and spec-compliance. No further action needed for
  this specific model.
- Chat history contamination as the *primary* driver of qwen3 failure:
  **PARTIALLY RESOLVED**. Demote from "critical blocker" to "known model
  limitation." qwen3-30b's residual contamination is now understood as intrinsic
  field-boundary leakage, not a pipeline bug.

**New issues to add to the backlog (prioritized per after synthesis):**
1. **(High, next)** Count contract mismatch: align schema `max_items`, follow-up
   call wording, and system prompt to "exactly 5". Two one-line code changes.
2. **(High, next)** Add post-merge count assertion + lever-name deduplication
   before saving (prevents silent overcount artifacts).
3. **(Medium)** Enable retry config in prompt-optimizer runner: converts hard JSON
   extraction failures (nemotron, run 60) to retryable near-misses.
4. **(Medium)** Add field-boundary validation: ban `Controls`/`Weakness:` patterns
   inside `consequences` field. Directly targets qwen3's residual contamination.
5. **(Low)** Remove `[Domain]-[Decision Type] Strategy` naming template from
   prompt: reduces "Silo-X Strategy" robotic prefix overuse in gpt-4o-mini.
6. **(Low)** Investigate gpt-5-nano's high latency (flagged in after insights as
   slow relative to output quality gain).
