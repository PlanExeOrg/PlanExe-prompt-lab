# Assessment: Qualitative consequences, positive framing, and consistent length targets

## Issue Resolution

**PR #477 targeted three issues:**

### 1. Fabricated quantification — replace number-evidence constraints with qualitative framing

**Claimed fix:** Remove all explicit number-evidence constraints from the `consequences` field
description and system prompt section 5. Replace with "Exact numbers will be determined further
downstream — here the goal is to articulate the cause-effect relationship clearly." Add hard
section 5 prohibition: "NO specific numbers, percentages, or monetary amounts — describe effects
qualitatively."

**Is it resolved?** Partially.
- Haiku (the primary offender): fabricated pct claims dropped from 20 → 6 (−70%). Evidence:
  parasomnia run 93→17 (10→3 `%` occurrences in `002-10-potential_levers.json`); silo
  run 93→17 (16→7).
- Overall across all 7 models: 23 → 12 (−48%).
- **Qwen3-30b is immune** (3→3, unchanged). The code review identifies an anchoring risk in the
  new field description: "Exact numbers will be determined further downstream" may implicitly
  license approximate numbers for models that parse the field description before the system prompt
  prohibition (see New Issues §I3).

**Residual symptoms:**
- 6 pct claims remain in haiku outputs. The parasomnia and silo plans generate domain-grounded
  engineering numbers (e.g., "20% of scored nights re-scored", "40% construction cost overrun")
  that may reflect legitimate plan-document references rather than pure fabrication.
- 2 new pct claims appeared in llama3.1 (0→2), both in engineering-domain plans.

### 2. Positive framing — remove "Do NOT include 'Controls ... vs.'"

**Is it resolved?** This change was inert. The "Controls X vs Y" pattern was absent in 0/633
levers in the before batch (runs 2/87–93). The pattern had already been eliminated by an earlier
iteration. The change slightly reduces system prompt length but has no measurable effect.

### 3. Consistent length targets — "2-3 sentences" everywhere

**Is it resolved?** Neutral. Field lengths are stable and unchanged (consequences: +0.7%,
options: −1.4%, review: +0.5%). No verbosity inflation occurred. Synchronizing the length
instruction across field descriptions and system prompt sections had no measurable output effect —
field lengths were already consistent in practice.

---

## Quality Comparison

The "before" state is the post-PR-#358 output (runs 2/87–93, analysis 40). The "after" state is
post-PR-#477 output (runs 5/11–17, analysis 72). Note: multiple intermediate PRs (#469, #471, #473,
#475) lie between these two states; improvements not attributable to PR #477's described changes are
flagged.

| Metric | Before (2/87–93) | After (5/11–17) | Verdict |
|--------|-----------------|-----------------|---------|
| Plan-level success rate | 35/35 (100%) | 32/35 (91.4%) | **REGRESSED −8.6pp** |
| Call-level success rate | 102/105 (97.1%) | Not separately reported | — |
| LLMChatErrors | 0 | 0 | UNCHANGED |
| Bracket placeholder leakage | 0 (not observed) | 0 (confirmed) | UNCHANGED |
| Option count violations | Not reported | Not reported | — |
| Lever name uniqueness (cross-run) | 97% avg | 99% avg | **IMPROVED +2pp** |
| Template leakage (system prompt examples) | 0 | 0 | UNCHANGED |
| Review format compliance ("Controls X vs Y") | 0/633 (0%) | 0/647 (0%) | UNCHANGED |
| Consequence chain format (Imm→Sys→Strat) | Not used (baseline artifact) | Not used | N/A |
| Fabricated quantification — all models | 23 | 12 | **IMPROVED −48%** |
| Fabricated quantification — haiku only | 20 | 6 | **IMPROVED −70%** |
| Fabricated quantification — qwen3 only | 3 | 3 | UNCHANGED |
| Content depth (avg options, chars) | 491 | 484 | UNCHANGED −1.4% |
| Cross-call duplication (uniqueness) | 97% | 99% | IMPROVED |
| Field length vs baseline — consequences | 1.07× (298 chars) | 1.08× (300 chars) | UNCHANGED |
| Field length vs baseline — review | 1.31× (199 chars) | 1.32× (200 chars) | UNCHANGED |
| Review >200 chars | 33% | 38% | **MINOR REGRESSION +5pp** |
| Marketing-copy language | 17 levers | 16 levers | UNCHANGED |
| Review template lock ("none/all three options") | 85% haiku (run 93 hong_kong_game) | ~0% (run 5/17 confirmed) | **IMPROVED** (see note) |
| Over-generation / early step-gate exit | 2 haiku partial_recovery events | Not reported | — |

**Note on review template lock improvement:** The "All three options X, but none address Y"
secondary lock that was the top issue in analysis 40 appears resolved in run 5/17. Direct
verification of haiku run 5/17 hong_kong_game `002-10-potential_levers.json` shows 21 reviews,
all using domain-specific, varied openers and closers with no "none of the options" template.
PR #477 did not touch `review_lever` field description, so this improvement was likely delivered
by one of the intermediate PRs (#471 or #473). The analysis 72 insight file did not track or
report this metric. It is a confirmed positive improvement relative to analysis 40.

**Note on plan-level success rate regression:** The 3 failed plans are `plan timeout after 600s`
events (not `LLMChatError` or `ValidationError`), affecting gpt-oss-20b (parasomnia) and gpt-5-nano
(sovereign_identity, silo). Field lengths are unchanged, making infrastructure latency more likely
than prompt-induced token inflation. However, only gpt-oss-20b and gpt-5-nano are affected, and
both were previously at 100%. One follow-up run is needed to confirm causality before updating
`best.json`.

---

## New Issues

### From PR #477

**I3 (Medium): Anchoring risk in `consequences` field description**
The phrase "Exact numbers will be determined further downstream — here the goal is to articulate
the cause-effect relationship clearly" may inadvertently license approximate numbers for models
that read field descriptions before the system prompt prohibition. This explains why qwen3-30b
shows no improvement (3→3): as a strong instruction-follower, qwen parses the Pydantic field
description first; the "downstream" framing implicitly signals that rough numeric estimates are
acceptable now. The remaining haiku pct claims in silo/parasomnia (engineering-domain contexts)
are consistent with the same anchoring effect.
Source: code_claude.md I3.

**B1 (Low): "MORE levers" retry prompt fires with empty exclusion list**
When call 1 fails and `generated_lever_names` is empty, call 2 produces:
"Generate 5 to 7 MORE levers ... Do NOT reuse any of these already-generated names: []" —
exposing a template skeleton to the model and falsely implying prior output exists.
Fix: gate on `if call_index == 1 or not generated_lever_names:`.
Source: code_claude.md B1, `identify_potential_levers.py:297–304`.

**B2 (Low): False `partial_recovery` event for single-call step-gate success**
When a model generates ≥15 levers in one call and exits early, the runner emits `partial_recovery`
with `expected_calls=3`, polluting `events.jsonl` with false failure signals.
Source: code_claude.md B2, `runner.py:577–583`.

### Pre-existing issues newly surfaced

**S1 (Low): No post-loop warning when final lever count < `min_levers`**
The adaptive loop exits silently even if all calls fail and only 5 levers were generated.
Source: code_claude.md S1.

**S2 (Low): `options` validator contradicts "no more, no fewer" field description**
Field says "Exactly 3. No more, no fewer." but validator accepts ≥3. Strong models may truncate
defensively to avoid a perceived hard constraint.
Source: code_claude.md S2.

### Latent issues confirmed absent
- No new template-lock patterns introduced in `review_lever` outputs (confirmed by direct read of
  run 5/17 hong_kong_game).
- No bracket placeholder leakage in any sampled outputs.
- No `LLMChatError` in any after runs.

---

## Verdict

**CONDITIONAL**: The primary improvement (haiku fabricated pct claims −70%, overall −48%) is real
and significant with no content quality regressions on successful plans. Two conditions apply before
this PR is committed to `best.json`:

1. **Confirm timeout failures are infrastructure noise.** Run one follow-up iteration; if gpt-oss-20b
   and gpt-5-nano succeed on parasomnia/sovereign_identity/silo, the 91.4% plan success rate is
   noise and the PR is a full KEEP. If they repeat, investigate whether those plans produce unusually
   long prompts that push slow models past the 600s ceiling.

2. **Address the qwen3-30b anchoring issue.** The "downstream numbers" phrase in the `consequences`
   field description is the most likely explanation for qwen's complete immunity. Removing this
   anchor in the next PR (see Recommended Next Change) should move qwen3's count from 3 toward 0
   and confirm that the fix is durable across all models, not only haiku.

---

## Recommended Next Change

**Proposal:** Replace the "Exact numbers will be determined further downstream" anchor phrase in the
`consequences` field description (three locations: `Lever.consequences`, `LeverCleaned.consequences`,
and system prompt section 2) with direction/scale guidance that avoids referencing numbers entirely.
Draft wording: "Focus on direction and relative scale (larger, smaller, faster, slower) — avoid all
specific quantities."

**Evidence:** The synthesis of analysis 72 identifies this as Direction 1 with high confidence:
qwen3's pct claims are stable at 3 across the before and after batches despite the section 5
prohibition; the field description is read first during structured output generation and the
"downstream" anchor overrides the later prohibition for instruction-following models. The code
review independently confirms this as I3. Haiku's silo and parasomnia residual claims (domain
engineering contexts) are also consistent with this anchoring effect. The PR #477 description
itself identifies that explicit "Never invent" prohibitions (PR #475) backfired by acting as a
permission floor; the proposed wording avoids both that pattern and the current anchoring risk.

**Verify in next iteration:**
- qwen3-30b pct claims in silo/parasomnia/gta_game plans (before: 3; target: ≤1 or 0).
- llama3.1 pct claims (before: 2 after PR #477; target: 0).
- haiku silo/parasomnia residual pct claims (before: 2+5; target: ≤2 with only plan-document-grounded
  values).
- No verbosity inflation in `consequences` fields (avg should stay within 1.1× of 279-char baseline).
- No new template-lock patterns in `review_lever` outputs for haiku/llama (confirmed absent in
  run 5/17; monitor for any "all three strategies collectively" lock since the new wording would use
  that phrase in the `review_lever` field description if the direction-1 fix from analysis 40 was
  not yet applied).
- Timeout failures in gpt-oss-20b and gpt-5-nano (3 failures in PR #477 batch; confirm 0 in next
  run before updating `best.json`).

**Risks:**
- "Direction and relative scale" framing is less concrete than "no numbers downstream." Domain-primed
  models (qwen, haiku in engineering plans) may interpret "relative scale" as permission to use
  qualitative ranges like "roughly half" or "substantially more." If this occurs, the next iteration
  should add a domain-specific example of acceptable qualitative language.
- Removing the "downstream" deferral deletes a true statement about pipeline behavior. This is
  unlikely to cause harm, but if a model questions why it cannot cite numbers, the absence of an
  explanation may increase edge-case fabrication. The section 5 hard prohibition ("NO specific
  numbers") should remain as backstop.
- No prerequisite issues: this change is independent of the timeout investigation and can proceed
  concurrently.

**OPTIMIZE_INSTRUCTIONS note:** The `identify_potential_levers.py` OPTIMIZE_INSTRUCTIONS constant
is confirmed up to date for this PR's findings (analysis 72 insight confirms no new entries needed).
The existing "Fabricated numbers" entry already documents the failure mode. If the next PR's
follow-up reveals that removing the anchor phrase causes a new form of numeric anchoring (e.g.,
"relative scale" → "roughly 50%"), a new entry should be added documenting "Implicit license via
downstream deferral" as a confirmed failure mode.

---

## Backlog

### Resolved (can be removed)

- **Haiku "tension" opener lock** (analysis 39/40 primary issue): Fully resolved by PR #358.
  Confirmed absent in all after batches.
- **Haiku success rate regression** (73.3% in analysis 39): Resolved to 86.7% by PR #358, then
  to 100% in later iterations.
- **"None/All three options" review template lock** (analysis 40 secondary issue, 85% haiku rate):
  Confirmed absent in run 5/17 hong_kong_game (21/21 reviews use domain-specific varied openers).
  Likely fixed by intermediate PRs #471/#473 between analyses 40 and 72. Analysis 72 did not track
  this metric but direct file verification confirms resolution.
- **`LeverCleaned.review` stale field description** (analysis 40 B1: "names the core tension"):
  Not flagged in analysis 72 code review, suggesting it was fixed in an intermediate PR.

### Outstanding from before

- **Review field length still above baseline (haiku):** Review avg 1.31×→1.32× vs baseline (152
  chars). The "one sentence (20–40 words)" instruction is partially effective but 38% of reviews
  exceed 200 chars. No validator enforces the upper bound. Low urgency; content quality is more
  important than length compliance.

### New — add to backlog

- **Qwen3-30b pct claim immunity:** Qwen shows 0% improvement across three iterations (stable at 3
  pct claims in silo/parasomnia/gta_game). The anchoring phrase change (recommended above) is the
  next targeted fix.
- **Silo/parasomnia domain-grounded pct claims:** Engineering-context plans generate borderline
  pct claims (tolerances, cost overruns, retention thresholds) that may be document-grounded rather
  than fabricated. A policy decision is needed: "zero tolerance" vs. "only purely fabricated claims
  are bad." This distinction affects how remaining pct claims in haiku are evaluated.
- **3 plan timeout failures** (gpt-oss-20b parasomnia; gpt-5-nano sovereign_identity, silo):
  Monitor in next iteration. If timeouts repeat, investigate whether these plans produce long
  user_prompts that push the 5-call adaptive loop over the 600s ceiling for slow models.
- **B1: Empty exclusion list in retry prompt** (`identify_potential_levers.py:297–304`): Fix when
  next touching this file. One-line guard: `if call_index == 1 or not generated_lever_names:`.
- **B2: False `partial_recovery` for step-gate early exit** (`runner.py:577–583`): Fix alongside
  B1. Metadata-only change; no output quality effect.
- **S2: Options validator vs. field description mismatch** (`identify_potential_levers.py:121–157`):
  Field says "no more, no fewer" but validator accepts ≥3. Update field description to "At least 3
  options." Low priority; no evidence of harm yet.
