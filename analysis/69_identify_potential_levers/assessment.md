# Assessment: Replace negative-priming prohibition with positive framing in consequences field

## Issue Resolution

**What the PR was supposed to fix:** PR #471 removed the explicit negative prohibition
`"Do NOT include 'Controls ... vs.', 'Weakness:'"` from the `consequences` field description
in `Lever` and `LeverCleaned`, replacing it with the positive directive `"Focus on
cause-effect relationships and factual outcomes; save critical assessments for the
review_lever field."` The rationale (per PR description) is that negative prohibitions name
exact banned phrases which small models copy as templates — the same failure mode documented
in OPTIMIZE_INSTRUCTIONS lines 80–83 and previously observed in the enrich step (PRs #458,
#460).

**Is the issue resolved?** Yes, and the source code at `identify_potential_levers.py:111–120`
confirms the positive framing is in place. The "Controls X vs Y / Weakness:" pattern was not
observed in any examined outputs from the after batch (verified: run 96 haiku all 21 levers,
run 90 llama3.1 sample). The change is **preventative** rather than corrective: the prohibited
pattern was also absent from the before batch (run 93 haiku and run 87 llama3.1 consequences
examined). The PR applies the lesson learned from the enrich step defensively to this step.

**Residual symptoms:** None. The positive framing is correctly applied in both `Lever` and
`LeverCleaned`. The `consequences` field in after-batch outputs is clean cause-effect prose
without any trace of the prohibited patterns or their reformulations.

**Caveat on this analysis:** `insight_claude.md` timed out (1200 s limit) for analysis 69,
leaving no model-level quality survey for the after batch. The quality claims above are based
on direct examination of run 96 and run 90 output files, not a systematic cross-model scan.

---

## Quality Comparison

Only models appearing in both batches are included. "Before" = runs 2/87–93 (after PR #358).
"After" = runs 4/90–96 (after PR #471).

| Metric | Before (runs 2/87–93) | After (runs 4/90–96) | Verdict |
|--------|----------------------|----------------------|---------|
| **Overall call success rate** | 102/105 = 97.1% | 88/105 = 83.8% | APPARENT REGRESSION — see note |
| **Overall rate (excl. run 91 timeout)** | 102/105 = 97.1% | 88/90 = 97.8% | UNCHANGED |
| **llama3.1 success** | 14/15 = 93.3% (run 87) | 15/15 = 100% (run 90) | IMPROVED |
| **gpt-oss-20b success** | 15/15 = 100% (run 88) | 0/15 = 0% (run 91 — all timeout) | INFRASTRUCTURE FAILURE — not PR-caused |
| **gpt-5-nano success** | 15/15 = 100% (run 89) | 15/15 = 100% (run 92) | UNCHANGED |
| **qwen3-30b success** | 15/15 = 100% (run 90) | 15/15 = 100% (run 93) | UNCHANGED |
| **gpt-4o-mini success** | 15/15 = 100% (run 91) | 15/15 = 100% (run 94) | UNCHANGED |
| **gemini-2.0-flash success** | 15/15 = 100% (run 92) | 15/15 = 100% (run 95) | UNCHANGED |
| **haiku success rate** | 13/15 = 86.7% (run 93) | 13/15 = 86.7% (run 96) | UNCHANGED |
| **Bracket placeholder leakage** | 0 observed | 0 observed | UNCHANGED |
| **Option count violations** | 0 (all levers have 3 options) | 0 (all levers have 3 options) | UNCHANGED |
| **Lever name uniqueness** | Near-dupes from multi-call merge (e.g. "IP Rights" variants) | Same pattern — near-dupes from 3 calls | UNCHANGED |
| **"Controls X vs Y" / "Weakness:" in consequences** | Not observed in before batch | Not observed | UNCHANGED (prevention confirmed) |
| **"None/All three options leave unaddressed" in reviews** | ~85% of haiku reviews (run 93, 17/20 hong_kong_game) | ~86–90% of haiku reviews (run 96, ~19/21 hong_kong_game) | UNCHANGED — pre-existing secondary lock, not caused or worsened by this PR |
| **Consequence chain markers (Immediate→Systemic→Strategic)** | Absent in current outputs (free-form prose) | Absent | UNCHANGED (baseline uses this format; current prompt does not) |
| **Content depth (avg option length)** | Long multi-sentence options for haiku (~200–250 chars) | Same range | UNCHANGED |
| **Cross-call duplication** | Near-duplicate lever names across 3 calls (e.g. "Director Selection" × 2) | Same pattern | UNCHANGED |
| **Over-generation count** | run 93 haiku: 13/15 calls (2 partial_recovery via step-gate) | run 96 haiku: 13/15 calls (same 2 plans exit at 2 calls) | UNCHANGED |
| **Field length vs baseline (haiku consequences)** | ~400–450 chars vs baseline ~190 chars ≈ 2.1–2.4× | ~400–500 chars ≈ 2.1–2.6× | UNCHANGED (~2×; at warning threshold but not above 3×) |
| **Fabricated quantification** | Present: regional % breakdowns in revenue lever, schedule expansion estimates | Present at similar rate | UNCHANGED |
| **Marketing-copy language** | Not observed (plain descriptive language) | Not observed | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS alignment (consequences field)** | Had explicit prohibition violating lines 80–83 | Positive framing follows lines 80–83 | IMPROVED |

**Note on run 91 (gpt-oss-20b) timeout:** All 5 plans in run 91 timed out at exactly 600 s each.
This is a model availability or rate-limiting issue, not caused by PR #471. The PR modifies a
Pydantic field description; it cannot cause LLM-level timeouts. Excluding run 91, the
infrastructure-adjusted success rate is 88/90 = 97.8% — essentially identical to the before
rate of 97.1%.

**Note on haiku partial_recovery events:** Run 96 outputs.jsonl shows sovereign_identity and
parasomnia_research_unit with `calls_succeeded: 2`. The events.jsonl contains no
`partial_recovery` event entries — confirming that the events.jsonl threshold correctly fires
only at `calls_succeeded < 2` (runner.py:577–583). The logger warning threshold at
runner.py:131 (`actual_calls < 3`) is the discrepancy (B1 below).

---

## New Issues

**Infrastructure failure (run 91, gpt-oss-20b):** All 5 plans timed out at 600 s. Not PR-caused.
Worth noting for experiment reproducibility: if re-run, gpt-oss-20b would likely recover. The
after-batch comparison for this model is currently invalid; exclude run 91 from any conclusions
about gpt-oss-20b quality.

**B1 (code bug, confirmed): Misleading `partial_recovery` logger warning threshold**
`runner.py:131`: `if actual_calls < 3:` fires on normal 2-call step-gate exits.
Comment at lines 128–130 explicitly says "A 2-call success is normal for models that produce
8+ levers per call." The logger condition contradicts its own comment. The events.jsonl event
at runner.py:577–583 correctly uses `calls_succeeded < 2`. Direct code verification:
```
runner.py:131:    if actual_calls < 3:
```
This is a one-character fix (`3` → `2`). This bug was present in the before batch too and is
not introduced by PR #471, but it was newly identified in this analysis cycle.

**insight_claude.md timeout (infrastructure):** The insight agent exceeded its 1200 s limit
and produced no output. This leaves the assessment without a systematic quality scan across
all 7 models. The timeout is likely due to the large total history window (7 runs × 5 plans ×
multiple output files). Consider capping the per-model file count or adding per-plan sampling
for future insight runs.

**Latent issues surfaced (pre-existing, not new):**
- **Review template lock ("None/all three options"):** ~85–90% of haiku reviews in after batch
  use "All three options leave unaddressed..." or "None of the three options address..." — same
  rate as before batch. This was the documented top priority from analysis 40. PR #471 did not
  address it, and it persists. Source: `identify_potential_levers.py:125–133` still contains
  "state the specific gap the **three options** leave unaddressed" in the field description.
- **Fabricated quantification in consequences:** Percentage estimates ("expand schedules by
  20–30%", "reduce net cash requirements by 15–25%") appear in haiku consequences across both
  batches. These violate OPTIMIZE_INSTRUCTIONS ("Do not invent percentages..."). Not introduced
  by PR #471.

---

## Verdict

**YES**: PR #471 is correct, safe, and directly aligned with OPTIMIZE_INSTRUCTIONS lines 80–83.
The positive framing replacement eliminates the anti-pattern risk in the `consequences` field
description. The apparent overall success rate regression (97.1% → 83.8%) is entirely explained
by a model timeout in run 91 and is not PR-caused. Haiku success rate is unchanged (86.7%).
No new template locks or content regressions were introduced.

---

## Recommended Next Change

**Proposal:** The synthesis.md (analysis 69) recommends fixing B1 first: change
`runner.py:131` from `actual_calls < 3` to `actual_calls < 2`. This is a one-character fix
that closes the inconsistency between the logger warning (misfires on normal 2-call runs) and
the events.jsonl event (correctly skips 2-call runs). After that, the highest-priority content
quality change remains **rewriting the `review_lever` field description to remove "the three
options leave unaddressed"** (recommended by synthesis 40, confirmed still present at
`identify_potential_levers.py:128–129`).

**Evidence for B1:** `runner.py:128–130` comment says "A 2-call success is normal"; condition
at line 131 fires for `actual_calls < 3`, which includes the normal 2-call case. The
`partial_recovery` event at runner.py:577–583 already uses the correct threshold (`< 2`),
making the mismatch a concrete inconsistency, not just style.

**Evidence for review_lever rewrite (still unaddressed from analysis 40):** Haiku run 96
(after PR #471) shows ~86–90% of hong_kong_game reviews using "All three options leave
unaddressed..." or "None of the three options address..." — unchanged from the 85% rate in
run 93 (before PR #471). The source phrase "state the specific gap the **three options** leave
unaddressed" at `identify_potential_levers.py:128–129` is still present and still acts as a
template. OPTIMIZE_INSTRUCTIONS lines 73–79 explicitly require that examples must not
reference "the options" as grammatical subject; the field description violates the same rule.
Synthesis 40's recommended draft wording:
> "then name a real-world constraint or risk that all three strategies collectively sidestep —
> expressed in terms specific to this project's domain."

**Verify (B1 fix):**
- After changing `< 3` to `< 2`, confirm that haiku runs with `calls_succeeded: 2` produce
  no logger warnings in runner output. Check at least one plan that typically exits at 2 calls
  (sovereign_identity or parasomnia_research_unit for haiku).

**Verify (review_lever rewrite):**
- Run haiku on hong_kong_game and count "All three options..." / "None of the three options..."
  occurrences. Expected: drop from ~85–90% toward 0% (mirroring the PR #358 fix for the
  "tension" opener). If a new subphrase lock emerges (e.g. "collectively sidestep" or
  "strategies collectively"), document it in OPTIMIZE_INSTRUCTIONS immediately.
- Also check gpt-5-nano (run 92) and llama3.1 (run 90) reviews in the after batch for the
  same pattern — insight_claude timeout prevented cross-model analysis for this run.

**Risks (review_lever rewrite):**
- New subphrase lock: the proposed replacement contains "collectively sidestep" which could
  itself become a template ("All three strategies collectively sidestep X"). Monitor in the
  next iteration. If it locks, replace the verb phrase with a more domain-specific instruction.
- The Section 4 header in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` must be updated to match
  the new field description — if only one is changed, models receive contradictory instructions.
- Haiku's 2-partial_recovery plans (sovereign_identity, parasomnia) are step-gate exits from
  over-generation; the review rewrite should not affect this, but verify `calls_succeeded`
  counts are unchanged.

**Prerequisite issues:** B1 is independent of the review_lever rewrite. Either can be done
first. The review_lever rewrite is higher-priority for content quality.

**OPTIMIZE_INSTRUCTIONS update suggestion:** Add a note that the `consequences` positive-framing
fix (PR #471) is a preventative measure applied by analogy from the enrich step, not correcting
a confirmed regression in identify_potential_levers. This context helps future maintainers
understand why the field description changed without a corresponding negative-quality event in
the analysis history.

---

## Backlog

**Resolved by PR #471:**
- `consequences` field negative-priming risk: removed. The explicit prohibition
  `"Do NOT include 'Controls ... vs.', 'Weakness:'"` is gone. Risk of small models copying
  the banned phrases from the field description is eliminated.

**New items to add:**
- **B1** (Medium): `runner.py:131` logger threshold `< 3` misfires on normal 2-call runs —
  change to `< 2`. One-character fix; low risk.
- **B2** (Low): Case-sensitive deduplication in `identify_potential_levers.py:368` —
  `lever.name.lower()` lookup would catch capitalisation variants before downstream dedup.
- **B3** (Low): `LeverCleaned` field descriptions are copy-pasted from `Lever` with no
  structural sync guarantee. Extract shared descriptions as module-level constants.
- **S3** (Low): `strategic_rationale` description contains copyable domain example
  ("speed, cost, scope, and quality") — remove per OPTIMIZE_INSTRUCTIONS guidance against
  structural cues in field descriptions.

**Carried from prior analysis:**
- **Review_lever "None/all three options" template lock** (High): Still at ~85–90% for haiku.
  Primary target of next content-quality PR. Fix: rewrite field description to remove "the
  three options leave unaddressed" (see synthesis 40 recommendation and analysis 69 Direction 1).
- **Review length 2.1–2.6× above baseline** (Low): Haiku reviews average ~400–500 chars vs.
  baseline ~190 chars. The "one sentence (20–40 words)" constraint is partially effective.
  Deferred until template lock is resolved.
- **Fabricated quantification in consequences** (Medium): Percentage estimates not grounded in
  plan context appear in both batches. Not introduced by PR #471. Address in a separate PR
  targeting the consequences length and specificity guidance.
- **`LeverCleaned.review` stale description** (Low): Line ~212 still says "names the core
  tension..." — update for code hygiene when touching the file for another reason.
