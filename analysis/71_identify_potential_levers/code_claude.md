# Code Review (claude)

Files reviewed:
- `/Users/neoneye/git/PlanExeGroup/PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `/Users/neoneye/git/PlanExeGroup/PlanExe/self_improve/runner.py`
- PR #475 diff reconstructed from git metadata (ORIG_HEAD `0097ed2a` → HEAD `2c74f145` on branch `fix/identify-positive-framing-and-concise-v2`)

---

## Bugs Found

### B1 — Python closure captures loop variable `messages_snapshot` by reference

**File:** `identify_potential_levers.py`, lines 315–325

Inside the `for call_index in range(...)` loop, a new `execute_function` closure is
defined on every iteration. The closure refers to `messages_snapshot` by name, not by
value. Python closures close over the enclosing scope, not a snapshot of it. Because
`llm_executor.run(execute_function)` is called synchronously immediately after the
closure is defined, and `messages_snapshot` is a local variable re-assigned each
iteration (not the loop variable itself), the bug is **latent rather than
currently-triggered**: in the single-threaded, synchronous path the closure is always
called before the next iteration re-assigns `messages_snapshot`, so the correct
snapshot is used.

However, if `llm_executor.run()` ever defers execution asynchronously (e.g., across
threads), the closure would see a later iteration's `messages_snapshot`. The pattern
is a known Python footgun. A safe fix is to pass the snapshot as a default argument:

```python
def execute_function(llm: LLM, _msgs=messages_snapshot) -> dict:
    sllm = llm.as_structured_llm(DocumentDetails)
    chat_response = sllm.chat(_msgs)
    ...
```

This is a low-severity latent bug today but is a maintenance risk.

### B2 — `review_lever` length constraint says "1–2 sentences" in field description but "one sentence" in system prompt section 6

**File:** `identify_potential_levers.py`
- Line 127: `"1–2 sentences: the primary trade-off this lever introduces …"`
- Line 260: `"Keep each \`review_lever\` to one sentence (20–40 words)."`

The field description embedded in the Pydantic schema (`Lever.review_lever`) directly
influences LLM output because structured-output providers inject field descriptions
into the JSON schema sent to the model. The system prompt section 6 gives a
contradictory limit. Models that read both see conflicting signals and may follow
whichever they weigh more heavily. The haiku run (5/10) produces `review_lever` values
averaging 310 chars — well beyond 40 words — suggesting haiku followed the more
permissive "1–2 sentences" guidance in the Pydantic field description rather than the
stricter system prompt directive.

This is a correctness bug: two authoritative prompt sources disagree, one of them
contradicts the claimed fix in PR #475 (which set field descriptions to "1–2 sentences"
but left the system prompt at "one sentence"). The inconsistency is the fix itself:
PR #475 changed the field description from one target to another without updating the
system prompt section 6 to match.

### B3 — Anti-fabrication constraint does not prohibit arithmetic derivation

**File:** `identify_potential_levers.py`, lines 113–117 and line 232

The constraint reads: "Never invent percentages, costs, or timeframes — only cite
numbers that appear in the project context."

This wording creates a logical permission: if a number appears in the project context,
the model may use it. Models with finance/arithmetic reasoning capability (haiku,
gpt-oss-20b) interpret "only cite numbers that appear in the project context" as
authorizing them to compute derived figures from real plan numbers — which they then
present as facts. The constraint as written does not prohibit:

- Arithmetic derivation: splitting HK$470M into HK$141M (30%) + HK$117.5M (25%) + HK$70.5M (15%)
- Extrapolation: applying film-industry heuristics to infer HK$75M as a Film Development Fund subsidy
- Fabricated analogues: stating "HK$60–80 for 48-hour rental, modeled on recent high-profile releases"

The phrase "only cite numbers that appear in the project context" can be read as a
floor (you must cite from context) rather than a ceiling (you may only state numbers
verbatim from context). The constraint needs to explicitly prohibit derived arithmetic
and domain-knowledge extrapolation.

This is a semantic/prompt correctness bug with a direct causal path to the 4× HKD
fabrication regression observed in the after-PR runs.

---

## Suspect Patterns

### S1 — `min_levers = 15` stop threshold vs. `min_length=5` in DocumentDetails schema

**File:** `identify_potential_levers.py`, lines 189 and 289

`DocumentDetails.levers` has `min_length=5` (Pydantic validation). The adaptive loop
targets `min_levers = 15`. Each call produces 5–7 levers. In the best case (7 levers
per call), 15 levers requires 3 calls; with 5 levers per call it requires 3 calls too.
The stop condition `len(generated_lever_names) >= 15` is therefore met in call 2 when
call 1 produces 8+ levers (possible since `min_length=5` does not cap at 7) or in call
3 otherwise.

For the haiku hong_kong_game run the raw JSON shows a single response containing 7
levers plus a second call containing at least 7 more (total 101 levers across 5 plans).
The adaptive loop stopping at >= 15 allows over-generation to accumulate beyond the
intended range. This is not a hard bug but the stop condition is asymmetric: it can
stop at 15 (fine) or continue through 5 calls and accumulate up to 35+ levers, all of
which get deduplication-checked but still inflate the lever count.

The haiku lever count increase (93 → 101) likely comes from haiku generating more
levers per call for creative/fictional domains (gta_game), not from the loop stopping
too late. This is a pattern worth monitoring, not an immediate fix target.

### S2 — Second-call prompt includes the full user_prompt verbatim after the "already-generated names" instruction

**File:** `identify_potential_levers.py`, lines 299–304

```python
prompt_content = (
    f"Generate 5 to 7 MORE levers with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
    f"{user_prompt}"
)
```

For the hong_kong_game plan, `user_prompt` contains the full plan text with real
HK$ figures (HK$470M, HK$195M, HK$940M–1.7B). In the second call, the model is
exposed to the same plan numbers again and must generate "completely different" levers
from remaining territory. For a financially detailed plan, the model is structurally
pushed toward financial levers on call 2 because the plan's rich financial data is the
most prominent remaining "uncovered" domain. This may amplify fabrication in
subsequent calls — the model's first call (call 1) takes the non-financial angles,
leaving the financial domain for call 2, where the model must generate fresh levers
from the same financial data it was just told not to repeat.

There is no evidence this is the primary driver (haiku's fabrication occurs in call 1
levers 4–5 for hong_kong_game), but it is a structural risk for plans with heavy
financial context.

### S3 — `LLMChatError` raised when `len(responses) == 0 and call_index == max_calls`

**File:** `identify_potential_levers.py`, lines 340–341

The error condition is: raise only if we have zero successful responses AND we've
exhausted all calls. But there is a subtle edge case: if call 1 succeeds and call 2
through 5 all fail, `responses` has one element, `call_index` ends at 5, and the
condition is false — so the error is silently swallowed. The adaptive loop returns
whatever was gathered from call 1, which may be fewer than 15 levers. The
`PlanResult.calls_succeeded` value would be 1, and the warning threshold in
`runner.py` line 131 only fires below 3 calls — so a 1-call result triggers the
warning. This is working as intended by design comments, but the pattern means that a
persistent LLM failure on calls 2–5 is observable only through the warning log, not
through the returned data. Downstream consumers have no machine-readable signal that
the minimum lever count was not met.

---

## Improvement Opportunities

### I1 — Arithmetic derivation must be explicitly prohibited in the constraint wording

**File:** `identify_potential_levers.py`, lines 113–117, 210–211, 232, 256

The current constraint "Never invent percentages, costs, or timeframes — only cite
numbers that appear in the project context" fails for plans with real budget figures
because it permits (or is interpreted to permit) arithmetic on those real figures.

The OPTIMIZE_INSTRUCTIONS block at line 53–55 already documents the problem: "Fabricated
numbers. Do not invent percentages, cost savings, market-share figures, or performance
deltas." But neither the Pydantic field description nor the system prompt prohibits
computing derived quantities from real plan numbers.

Recommended addition to the Prohibitions section (section 5) and to the `consequences`
field description:

> "Do not perform arithmetic on plan numbers to generate derived figures (e.g., if the
> plan states a total budget of X, do not present X×30% as a fact). If a specific
> sub-allocation, percentage split, or per-unit price does not appear verbatim in the
> project context, omit it."

This is the highest-priority improvement given the 4× HKD fabrication regression.

### I2 — Align `review_lever` length target across all three authoritative locations

**File:** `identify_potential_levers.py`, lines 127, 213, 260

Three locations specify the `review_lever` length:
1. `Lever.review_lever` field description (line 127): "1–2 sentences"
2. `LeverCleaned.review` field description (line 213): copied from Lever, also says "Critical review of this lever" (no sentence count)
3. System prompt section 6 (line 260): "one sentence (20–40 words)"

`LeverCleaned` is never sent to an LLM (its docstring says so), so its field
description is irrelevant to output quality. But `Lever.review_lever` (line 127) is
sent to the LLM via the structured output schema. The Pydantic description "1–2
sentences" and the system prompt "one sentence" conflict. Haiku's observed review
length of ~310 chars (averaging ~60 words) is consistent with following the "1–2
sentences" field description.

Whichever target is authoritative, both sources must agree. Since the system prompt
says "one sentence (20–40 words)" and the OPTIMIZE_INSTRUCTIONS block says "Keep
review_lever examples concise and enforce a length cap" (line 84), the field
description should match the system prompt rather than the other way around.

### I3 — The three `review_lever` examples share a structural sentence pattern

**File:** `identify_potential_levers.py`, lines 247–249

All three examples use the form:
- "[doing X] [verb phrase], but [negative consequence]"
- "[constraint], so [derived consequence]"
- "[pooling Y] [verb phrase], but [negative consequence]"

Each example's structure is: "Action/state → positive result, BUT exception/reversal."
The third example uses a slightly different "turning X into Y" structure.

OPTIMIZE_INSTRUCTIONS at line 76–82 explicitly warns: "Examples must avoid reusable
transitional phrases that fit any domain. No two examples should share a sentence
pattern or rhetorical structure." The three examples do not share the exact same opener,
but they all follow a "trade-off + exception" rhetorical template. Haiku in particular
shows `review_lever` values that all follow "X trade-off; Y unaddressed gap" — which
maps to the examples' structure.

This is a partial template lock risk at the sentence-pattern level, not the word level.
The fix from OPTIMIZE_INSTRUCTIONS's own guidance is to ensure each example names a
domain-specific mechanism and uses a different rhetorical structure.

### I4 — Post-processing validation could catch fabricated numbers in-band

**File:** `identify_potential_levers.py`, lines 356–378 (lever cleaning loop)

There is no numeric cross-referencing step after LLM output is parsed. A lightweight
post-processing check could:
1. Extract all numeric tokens (dollar amounts, percentages, explicit figures) from each
   lever's `consequences` and `options` fields using a simple regex.
2. Check each token against the `user_prompt` for exact or fuzzy presence.
3. For tokens not found in the prompt, append a retry prompt that names the
   specific fabricated value: "You cited HK$75M but this does not appear in the
   project context. Please regenerate this lever without inventing financial figures."

This is the C1 recommendation from `insight_claude.md`. It is a code-level fix that
would work for models that ignore prompt-level constraints. It would add latency but
only when fabrication is detected.

### I5 — runner.py `_run_levers` warning threshold is miscalibrated

**File:** `runner.py`, lines 131–134

The warning fires when `actual_calls < 3`. The comment says "only warn if fewer than
expected (~3 calls at 5-7 levers each)." But the adaptive loop with `min_levers=15`
and models generating 7+ levers per call legitimately stops after 2 calls. The haiku
model generates 7–8 levers per call, so stopping at call 2 with 14–16 levers is normal
and correct behavior. Triggering a warning for 2 calls is therefore a false-positive
for capable models.

The threshold would be more accurate at `< 1` (i.e., zero successful calls) or the
warning should be conditioned on lever count, not call count: `if pr.calls_succeeded < 2
and len_levers < min_levers`. As-is, it generates spurious log noise for strong models.

### I6 — Duplicate anti-fabrication constraint in two places may backfire

**File:** `identify_potential_levers.py`, lines 113–117 (Pydantic field desc) and line 232 (system prompt)

The anti-fabrication instruction appears identically in:
- The `Lever.consequences` Pydantic field description
- Section 2 of the system prompt (Lever Quality Standards, consequences bullet)

The `insight_claude.md` (Question 4, line 339–342) raises whether doubling the
constraint causes "compensation behavior." There is a plausible mechanism: when a model
sees the same instruction repeated in the schema and the system prompt, it may interpret
the emphasis as high importance and actively seek plan numbers to satisfy the "only cite
numbers from context" clause — then derives additional figures from those real numbers
to fill in the lever's options with concrete specifics. The duplication may amplify
engagement with financial plan data rather than suppressing it.

This is speculative but worth an experiment: removing the constraint from the Pydantic
field description and keeping it only in the system prompt, then measuring whether
fabrication rates change.

---

## Trace to Insight Findings

### Finding 1: Fabricated HK$ amounts increased 4× after PR #475

Direct root cause: **B3** — the anti-fabrication constraint does not prohibit
arithmetic derivation from real plan numbers. The constraint was strengthened in PR
#475 (placed earlier in the field description) but the wording remains semantically
permissive for derived arithmetic. Models read "only cite numbers that appear in the
project context" as an invitation to deeply engage with plan financials, then compute
allocations or extrapolate industry-standard values from those real numbers. The
strengthened constraint may have increased model focus on the plan's financial figures
(I6 duplication effect) without reducing derivation.

### Finding 2: Haiku generates financing-intensive levers with fabricated amounts

Direct root cause: **B3** combined with **I3** (example structure that rewards
trade-off/gap analysis). Haiku is a larger-context, domain-rich model that knows film
industry norms. When it sees HK$470M, HK$195M, and references to the "Hong Kong Film
Development Fund," it applies domain knowledge to infer HK$75M (a plausible subsidy
for a fund of that type), VOD pricing, and theatrical window options. The constraint
does not prohibit this because Haiku treats the Fund reference as "in the project
context" and derives an amount consistent with its training knowledge of that fund.
The fix for this requires explicitly prohibiting domain-knowledge extrapolation, not
just direct invention.

### Finding 3: gpt-oss-20b fabricates derived arithmetic

Direct root cause: **B3** — arithmetic derivation from a real plan number
(HK$470M). The model computed HK$141M (≈30%), HK$117.5M (≈25%), HK$70.5M (≈15%)
as explicit allocations. The constraint "Never invent percentages, costs, or timeframes"
should prohibit this, but the model's arithmetic derivation bypasses the intent because
the base number (HK$470M) is real. The wording gap (B3) is the direct cause.

### Finding 4: Fix 1 (consistent length targets) shows no measurable effect

Direct root cause: **B2** — the field description says "1–2 sentences" while the
system prompt says "one sentence." These contradict each other. Haiku follows the Pydantic
field description (which structured-output APIs expose directly in the JSON schema)
over the system prompt directive. Since PR #475 changed the field description from one
target to "1–2 sentences" (presumably to match the system prompt's "2–3" for
consequences while reducing review_lever), but the system prompt section 6 still says
"one sentence," there is no consistent signal. The measured non-change in review length
(198.8 → 192.3 chars, −3.3%) is consistent with models ignoring the ambiguous
instruction rather than following either version.

### Finding 5: Haiku lever count increased (93 → 101)

Contributing pattern: **S1** — the adaptive loop's stop condition at `>= 15` levers
and the haiku model's tendency to generate more levers per call for creative domains
(gta_game). This is not directly caused by PR #475 but by the plan domain (fictional
game vs. operational plans). The haiku increase is plan-distribution-specific and
unlikely to be a prompt-driven regression.

---

## PR Review

### PR #475: "Positive framing, consistent word counts, and stronger number-evidence constraint"

**Claimed fixes:**
1. Fix 1 — Align all three length targets to "2–3 sentences" for consequences
2. Fix 3 — Strengthen number-evidence constraint for consequences
3. Positive framing — replace "Do NOT include 'Controls … vs.'" with positive wording
4. Reduced output — options "one sentence", review_lever "1–2 sentences"

**Assessment of each fix:**

**Fix 1 — Partially implemented, introduces a new contradiction (B2)**

The PR updated the `Lever.consequences` and `LeverCleaned.consequences` field
descriptions to say "2–3 sentences" and added the same target to the system prompt
section 2. This is consistent.

However, for `review_lever`, the PR set the field description to "1–2 sentences" (line
127) while the system prompt section 6 still says "one sentence (20–40 words)" (line
260). These now contradict each other, which is a new inconsistency introduced by
this PR. The prior PR (#473) presumably had "2–4 sentences" in the system prompt for
consequences — PR #475 fixed the system prompt for consequences but introduced a
mismatch for review_lever.

The inconsistency means models receive conflicting signals for review_lever length,
which is why Fix 1 produced no measurable effect on review_lever length (−3.3% is
within noise).

**Fix 3 — Correct intent, incorrect implementation (B3)**

The PR moved the anti-fabrication constraint before the cause-effect directive in both
the Pydantic field description and system prompt. This was the intended fix: make the
constraint precede the directive that correlated with fabrication in PR #473.

However, the wording of the constraint itself was not changed to address arithmetic
derivation. The constraint "Never invent percentages, costs, or timeframes — only cite
numbers that appear in the project context" is semantically unchanged. The word
placement change (moving it earlier) had no measurable effect on fabrication; what
was needed was a semantic extension to prohibit derived arithmetic from real plan
numbers.

The PR description says this fix targets gpt-oss-20b's "HK$2m/5m/10m figures" from
PR #473. It succeeded in the sense that gpt-oss-20b no longer fabricates those
specific small amounts — but it introduced a regression where gpt-oss-20b now
fabricates larger derived amounts (HK$141M, HK$117.5M, HK$70.5M) from the real
HK$470M base. The constraint change may have shifted the fabrication pattern without
reducing it.

**Positive framing — Correct, neutral effect**

Replacing "Do NOT include 'Controls … vs.'" with positive framing was correct per the
OPTIMIZE_INSTRUCTIONS warning about adding explicit prohibitions that become templates
(lines 80–82). This change had zero observed effect on outputs, which is the expected
result for a cosmetic correctness fix.

**Reduced output targets — Partially contradictory (B2)**

Setting options to "one sentence" in the field description and system prompt is
consistent. Setting review_lever to "1–2 sentences" in the field description while the
system prompt says "one sentence" is not consistent. The PR appears to have intended
both to say "1–2 sentences" for review_lever, but the system prompt section 6 was not
updated.

**Overall PR assessment:**

The PR is structurally sound in intent but has two implementation gaps:
1. The review_lever length target is inconsistent between field description (1–2
   sentences) and system prompt section 6 (one sentence). The system prompt section 6
   needs to be updated to say "1–2 sentences" to match the field description, OR the
   field description should be changed back to "one sentence" to match section 6.
2. The anti-fabrication constraint does not address the arithmetic-derivation failure
   mode that drives the observed 4× HKD regression. This requires a semantic change to
   the constraint wording, not a positional change.

The PR preserves the zero-template-leakage, zero-error-rate, 100% success rate
characteristics of the prior best (PR #358). It is safe to keep but does not deliver
its stated improvements.

---

## Summary

**Confirmed bugs (ordered by severity):**

- **B3** (Critical for quality): Anti-fabrication constraint permits arithmetic
  derivation from real plan numbers. This is the direct root cause of the 4× HKD
  fabrication regression in the after-PR runs. The fix requires a semantic extension
  to the constraint wording to explicitly prohibit derived arithmetic and
  domain-knowledge extrapolation.

- **B2** (Important): `review_lever` length target is "1–2 sentences" in the Pydantic
  field description (line 127) but "one sentence" in system prompt section 6 (line
  260). This contradiction was introduced by PR #475 and explains why Fix 1 produced
  no measurable effect on review length.

- **B1** (Low, latent): Python closure captures `messages_snapshot` by name in the
  adaptive loop. Currently safe in synchronous execution but fragile if executor
  defers calls to a thread pool.

**Key improvement opportunities:**

- **I1**: Extend the constraint to explicitly prohibit arithmetic derivation and
  domain-knowledge extrapolation from real plan numbers. Highest priority.

- **I2**: Align review_lever length targets across all authoritative locations
  (Pydantic field description and system prompt section 6).

- **I4**: Add post-processing numeric cross-referencing in the lever cleaning loop
  to catch fabricated amounts that prompt constraints miss.

- **I3**: Diversify the rhetorical structure of the three `review_lever` examples
  to reduce structural template lock at the sentence-pattern level.

The most actionable next step is fixing B3 (I1) by extending the anti-fabrication
constraint to read: "Never invent percentages, costs, or timeframes — only cite numbers
that appear verbatim in the project context. Do not compute or derive figures by
applying percentages, multipliers, or domain heuristics to real plan numbers; if a
specific sub-allocation or per-unit price is not stated in the project context, omit
it."
