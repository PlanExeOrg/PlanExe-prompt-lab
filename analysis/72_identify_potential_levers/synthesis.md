# Synthesis

## Cross-Agent Agreement

Only one agent (claude) produced both an insight file and a code review for this analysis. Key
confirmed findings:

- **PR #477's primary goal is achieved**: fabricated percentage claims in haiku dropped 70% (20→6).
  The approach of removing the number topic entirely rather than prohibiting it worked as intended.
- **3 timeout failures** (gpt-oss-20b, gpt-5-nano) regressed success rate from 100% to 91.4%.
  These are `plan timeout after 600s` events — not `LLMChatError` — and field lengths are
  unchanged, making infrastructure latency the most likely cause.
- **"Controls" positive framing change is inert.** The targeted pattern was already absent in the
  comparison baseline (runs 2/87–93). The change reduces prompt length slightly but has no
  measurable effect.
- **Qwen3-30b is immune** to the change (3→3 pct claims). The residual claims are
  domain-grounded (silo, parasomnia engineering contexts) but still present.
- **Review field length target unmet**: 38% of `review_lever` outputs exceed 200 chars despite
  the "One sentence (20–40 words)" target. No validator enforces the upper bound.
- **B1 (empty exclusion list bug) and B2 (false partial_recovery event)** are confirmed by source
  code reading. Both are low-severity but produce misleading log/event output.

## Cross-Agent Disagreements

No cross-agent disagreements (single agent). The only internal tension is between the insight's
finding that 3 timeouts are likely infrastructure noise (field lengths unchanged) and the code
review's note that the adaptive loop makes up to 5 serial LLM calls, which could in principle
push a slow model over 600s. Source code confirms: `max_calls=5` at line 289 of
`identify_potential_levers.py`, and the timeout at `runner.py:558` is a hard 600s plan ceiling.
The weight of evidence (identical field lengths before/after, only 2 of 7 models affected) favors
the infrastructure hypothesis.

---

## Top 5 Directions

### 1. Replace anchoring phrase in `consequences` field description (I3)
- **Type**: prompt change
- **Evidence**: code_claude I3; insight negative finding "Silo/parasomnia residual pct claims";
  insight table shows qwen3-30b unchanged (3→3), llama newly gained 2 pct claims
- **Impact**: the phrase "Exact numbers will be determined further downstream" at line 113–116
  may inadvertently license approximate numbers for domain-heavy models (qwen3, silo/parasomnia
  engineering context). Fixing this is the highest-leverage remaining prompt change: 12 pct
  claims remain across all models after PR #477, and this phrase appears in both the Pydantic
  field description (read first during structured output) and the system prompt section 2.
  A rewrite that avoids referencing numbers at all — rather than deferring them — could close
  the residual fabrication for qwen3 and silo/parasomnia without risking the haiku regression
  that explicit prohibition caused in PR #475.
- **Effort**: low — one phrase change in 3 locations: `Lever.consequences` (line 114–116),
  `LeverCleaned.consequences` (line 208–211), and system prompt section 2 (line 232).
- **Risk**: low. The change removes a semantic signal rather than adding a prohibition.
  The only downside is that "qualitative direction/scale" framing is less concrete than
  "no numbers downstream" — but the current framing already demonstrates per-model immunity.

### 2. Fix "MORE levers" retry prompt fired with empty exclusion list (B1)
- **Type**: code fix
- **Evidence**: code_claude B1; source verified at `identify_potential_levers.py:296–304`
- **Impact**: when call 1 fails and `generated_lever_names` is empty, call 2 sends
  "Generate 5 to 7 MORE levers ... Do NOT reuse any of these already-generated names: []"
  — a structurally odd prompt that exposes the template skeleton. Weaker models (llama3.1,
  gpt-oss-20b) are most likely to mirror this framing and produce mislabeled output. The 3
  timeout failures in runs 5/12 and 5/13 were not caused by this bug, but any first-call
  failure (which these models are prone to) currently hits this path.
- **Effort**: low — one-line guard: `if call_index == 1 or not generated_lever_names:`
- **Risk**: minimal. The plain `user_prompt` path already works for all models on call 1.

### 3. Fix false `partial_recovery` event for single-call success (B2)
- **Type**: code fix
- **Evidence**: code_claude B2; source verified at `runner.py:577–583`
- **Impact**: any model that generates ≥15 levers in one call (hitting the `break` at line 352–354)
  exits with `len(responses) == 1`, which triggers `partial_recovery` with `expected_calls=3`.
  This pollutes `events.jsonl` with false failure signals that mislead the analysis pipeline's
  success-rate metrics. With 7 models × 5 plans = 35 runs per iteration, even a few false events
  distort aggregated per-model quality scores.
- **Effort**: low — change condition to `pr.calls_succeeded is not None and pr.calls_succeeded < 2`
  only when lever count is below minimum, or at minimum change `expected_calls=3` to `expected_calls=2`
  and add a clarifying comment.
- **Risk**: minimal. The event is metadata-only and has no downstream effect on lever content.

### 4. Add soft-cap logging for `review_lever` over-length (I1)
- **Type**: code fix (soft log only)
- **Evidence**: code_claude I1; insight table shows 38% of reviews exceed 200 chars despite
  "One sentence (20–40 words)" target. OPTIMIZE_INSTRUCTIONS warns against hard Pydantic caps.
- **Impact**: 38% of levers have reviews that are too long, but this is currently invisible
  without parsing output JSON per run. A `logger.warning` at >300 chars gives per-plan
  observability for future iterations without risking retry loops.
- **Effort**: low — 2-line addition in `check_review_format` validator at line 159–175.
- **Risk**: none if implemented as `logger.warning` (not `ValueError`).

### 5. Align `options` field description with actual validator behavior (S2)
- **Type**: prompt change
- **Evidence**: code_claude S2; source verified at `identify_potential_levers.py:121–124, 145–157`
- **Impact**: the field description says "Exactly 3 options. No more, no fewer." but the validator
  silently accepts ≥3. Strong instruction-following models (qwen3, haiku) may infer that 4 options
  would trigger a Pydantic error and become defensive — truncating to exactly 3 when a 4th would
  add value. Changing field description to "At least 3 options" removes a false constraint signal.
- **Effort**: low — one phrase change in `Lever.options` (line 122) and `LeverCleaned.options`
  (line 217).
- **Risk**: low. No models currently generate <3 options (that's caught by the validator). The
  change relaxes an incorrect signal rather than tightening anything.

---

## Recommendation

**Pursue Direction 1 first**: rephrase the `consequences` field description to remove the
"downstream numbers" anchor.

**Why first**: The 3 bugs (B1, B2, I1) are cleanup items that don't affect output quality.
The residual 12 pct claims — especially qwen3's complete immunity to PR #477 — are a content
quality problem that affects planning credibility downstream. The "Exact numbers will be
determined further downstream" phrasing is the only novel signal introduced by PR #477 that
could explain why qwen3 didn't improve: qwen reads the field description before the section 5
prohibition, and the "downstream" framing licenses approximate numbers exactly where the
prohibition would stop them.

**What to change** — three locations, same edit:

**1. `Lever.consequences` (lines 111–119)**
```python
consequences: str = Field(
    description=(
        "What happens when this lever is pulled? Describe the direct effect and "
        "at least one downstream implication or trade-off in qualitative terms. "
        "Focus on direction and relative scale (larger, smaller, faster, slower) — "
        "avoid all specific quantities. "
        "Save critical assessments for the review_lever field. "
        "Target length: 2–3 sentences."
    )
)
```

**2. `LeverCleaned.consequences` (lines 206–214)** — same wording (documentation only, but
keeps schemas in sync per S3).

**3. System prompt section 2 (line 232)**
Replace:
> "Consequences: describe the direct effect of pulling this lever, then at least one downstream
> implication or trade-off in qualitative terms. Exact numbers will be determined further
> downstream — here the goal is to articulate the cause-effect relationship clearly. Target
> length: 2–3 sentences."

With:
> "Consequences: describe the direct effect of pulling this lever, then at least one downstream
> implication or trade-off in qualitative terms. Focus on direction and relative scale — avoid
> all specific quantities. Target length: 2–3 sentences."

**Why this wording**: it removes every reference to numbers (both the prohibition and the
"downstream" deferral), replaces them with positive guidance ("direction and relative scale"),
and avoids adding any new prohibition that models could treat as a permission floor (the
PR #475 lesson).

**Expected result**: qwen3's 3 pct claims (stable through 3 iterations) should drop.
The silo/parasomnia residual claims in haiku (2 remaining) may also reduce, as they appear
in engineering contexts where "downstream numbers" framing gives implicit permission.

---

## Deferred Items

- **B1 (empty exclusion list in retry prompt)**: fix after confirming the anchoring phrase
  change. Low risk, one-line guard.
- **B2 (false partial_recovery event)**: fix alongside B1. Cleanup only; no output quality
  effect.
- **I1 (soft-cap logging for review_lever)**: useful observability addition, but review length
  does not affect downstream plan quality. Defer until after content quality is stable.
- **S2 (options validator vs field description mismatch)**: low priority; no evidence of
  models being harmed by the "no more, no fewer" language currently.
- **S3 (LeverCleaned description duplication)**: cosmetic. The duplication is pre-existing and
  has no functional effect. Acceptable as-is.
- **S4 (misleading lock comment in runner.py)**: documentation only. No behavior impact.
- **I2 (emit lever count in completion event)**: good for future observability; defer until
  content quality is stable.
- **Timeout monitoring**: the 3 timeouts (gpt-oss-20b, gpt-5-nano) need one follow-up run
  to confirm they are infrastructure noise before committing PR #477 to `best.json`. If
  timeouts recur in the same plans, investigate whether those plans have unusually long
  `user_prompt` strings that trigger multi-call paths in slow models.
- **Qwen3-30b targeted fix**: if the anchoring phrase change (Direction 1) doesn't move
  qwen3's pct-claim count, the next step would be adding a second structured-output
  verification pass for `consequences` fields containing numeric patterns — but this doubles
  token cost for affected levers and should only be pursued if lighter changes fail.
