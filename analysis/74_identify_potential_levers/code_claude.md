# Code Review (claude)

## Bugs Found

**B1 (pre-existing, not fixed by PR #479): "MORE levers" retry prompt fires with empty exclusion list on first-call failure**
`identify_potential_levers.py:297–306`

```python
if call_index == 1:
    prompt_content = user_prompt
else:
    names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
    prompt_content = (
        f"Generate 5 to 7 MORE levers with completely different names. "
        f"Do NOT reuse any of these already-generated names: [{names_list}]\n\n"
        f"{user_prompt}"
    )
```

When call 1 fails with an exception (`continue` at line 346), `generated_lever_names` is still
empty when call 2 runs. The prompt becomes:

> "Generate 5 to 7 MORE levers with completely different names. Do NOT reuse any of these
> already-generated names: []\n\n{user_prompt}"

The `[]` exposes the template skeleton and the word "MORE" implies the model is continuing a
previous batch when it is not. This is the same residual second-call lock observed for
llama3.1 (run 25) — levers 9–18 show "leaving unaddressed the question of…" and short labels
("Empower the Director", "Opt for Venice") consistent with a model that received a confused
continuation prompt.

Fix: gate on `if call_index == 1 or not generated_lever_names:` to send the plain `user_prompt`
when no prior levers exist.

---

**B2 (pre-existing, not fixed by PR #479): False `partial_recovery` event for fast single-call success**
`runner.py:577–583`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 2):
    _emit_event(events_path, "partial_recovery", ...)
```

If a model returns ≥ 15 levers in one call, the adaptive loop exits after call 1 with
`len(responses) == 1`. `actual_calls == 1 < 2` triggers `partial_recovery` even though the
run succeeded cleanly. This creates misleading noise in `events.jsonl`.

Also reinforced at `runner.py:131`:
```python
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")
```
Both the warning and the event fire for a legitimate 1-call success.

Fix: change the condition to check whether the final lever count is below `min_levers`, not
whether the call count is below an assumed minimum.

---

**B3 (NEW — introduced by PR #479): `review_lever` field description embeds a copyable sentence structure, directly contradicting OPTIMIZE_INSTRUCTIONS**
`identify_potential_levers.py:127–131`

Current field description:
```python
description=(
    "One sentence (20–40 words): identify the key risk or constraint "
    "that the proposed options collectively do not resolve. "
    "Do not use square brackets or placeholder text."
)
```

OPTIMIZE_INSTRUCTIONS (lines 86–92) explicitly warns:
> "Field-description template lock. A Pydantic field description containing a structural phrase
> (e.g. 'name the core tension') is read as a literal instruction — models start every output
> with 'The tension is…'. Describe the required content ('identify the primary trade-off and
> the specific gap') not the expected sentence structure."

The phrase "the proposed options collectively do not resolve" is a sentence-structural cue
(object clause) that models will copy and vary. The insight confirms this: qwen3-30b went from
0/15 template-locked reviews before the PR to ~9/20 using "leaves unresolved risk of…" and
"remains unresolved" — phrases that directly mirror "collectively do not resolve". gpt-oss-20b
shifted from "options still leave X unaddressed" to "The options do not resolve/address/mitigate
the risk that…" — same structural pattern, new lexical surface.

The PR replaced one copyable phrase ("the three options leave unaddressed") with another
("the proposed options collectively do not resolve"). The underlying problem — a Pydantic field
description that encodes output sentence structure rather than content goal — was not fixed.

The OPTIMIZE_INSTRUCTIONS code comments document this exact anti-pattern while the live field
description exhibits it. This is a self-contradiction.

Fix: rewrite the field description with goal-oriented language, e.g.:
> "One sentence (20–40 words): state the specific structural or operational gap that would remain
> open even if all three options were fully executed. Do not use square brackets or placeholder
> text."

---

**B4 (NEW — introduced by PR #479): Section 4 preamble replicates the copyable phrase, double-reinforcing the template lock**
`identify_potential_levers.py:246–247`

```python
"   - For `review_lever`:\n"
"     One sentence identifying the key risk or constraint that the proposed options collectively do not resolve.\n"
```

The phrase "that the proposed options collectively do not resolve" now appears verbatim in two
locations:
1. The `review_lever` Pydantic field description (line 129)
2. The Section 4 validation protocol preamble (line 247)

OPTIMIZE_INSTRUCTIONS notes that "The system-prompt examples alone cannot override a structural
cue embedded in the field description." Having the same structural cue in both the field
description *and* the system prompt compounds the problem — it gives models two aligned signals
to copy from instead of one.

The examples that follow in Section 4 (lines 249–252) are the correct mechanism: they provide
domain-specific, structurally diverse illustrations. The preamble sentence should describe the
CONTENT goal (what gap to identify), not repeat the sentence template.

Fix: rewrite the Section 4 preamble to: "One sentence naming the structural or operational gap
that would persist even if all three options were carried out in full."

---

## Suspect Patterns

**S1 (pre-existing): No post-loop warning when adaptive loop exits below `min_levers`**
`identify_potential_levers.py` post-loop (after line 356)

If all 5 calls fail except one that returns 5 levers, the code silently proceeds with 5 levers —
10 fewer than the `min_levers=15` target. No guard:

```python
if len(generated_lever_names) >= min_levers:
    break
# loop ends — no check here
```

A `logger.warning` after the loop when `len(generated_lever_names) < min_levers` would surface
this silently degraded case.

---

**S2 (pre-existing): `options` validator accepts > 3 despite field description saying "No more, no fewer"**
`identify_potential_levers.py:121–124` and `146–157`

Field description: "Exactly 3 options for this lever. No more, no fewer."
Validator: `if len(v) < 3: raise ValueError(...)` — accepts 4, 5, 6 options silently.

A model that reads "Exactly 3… no more, no fewer" may become defensive about over-generation.
The comment at lines 186–191 explains the intent ("over-generation is fine"), but the field
description should say "At least 3 options" to align with actual validator behavior.

---

**S3 (pre-existing): `LeverCleaned` field descriptions are verbatim copies of `Lever` field descriptions**
`identify_potential_levers.py:206–220`

`LeverCleaned` is documented as "never sent to an LLM" (line 194), but its `consequences` and
`options` field descriptions are identical to `Lever.consequences` and `Lever.options` — including
the prompt-directed language. PR #479 correctly kept both in sync. The risk: a future refactor
that accidentally sends `LeverCleaned` to an LLM would silently use the same (possibly outdated)
instructions. Worth a comment marking `LeverCleaned` field descriptions as documentation-only.

---

**S4 (NEW — related to PR #479 regression): Section 5 numeric prohibition may activate gpt-oss-20b's number-generation behavior**
`identify_potential_levers.py:258`

The PR added to Section 5:
> "NO calculated, derived, or estimated figures — use only numbers that appear verbatim in the
> project context"

OPTIMIZE_INSTRUCTIONS (line 80–82) warns: "Do NOT add explicit prohibitions naming banned
phrases — small models treat the prohibition text as a template." The same principle likely
applies to numeric prohibitions. By naming "calculated, derived, or estimated figures" and then
qualifying with "use only numbers that appear verbatim," the instruction may focus gpt-oss-20b's
attention on the budget figures in the project context (e.g., "HK$470 million") and implicitly
license deriving percentage breakdowns from them as "verbatim-context figures".

The insight observes that gpt-oss-20b went from 0 fabricated percentage values before the PR to
5–6 per plan after (60%, 40%, 20%, 15%, 10% allocations that appear nowhere in the project
context). The insight's "Reflect" section notes: "the model sees 'NO calculated, derived, or
estimated figures' as implicitly allowing figures from context, and then interprets budget-related
context as permission to generate percentage allocations."

This is consistent with OPTIMIZE_INSTRUCTIONS' prohibition-backfire warning applied to numbers.
The abstract prohibition is insufficient; a worked counter-example (see I3) is more reliable.

---

## Improvement Opportunities

**I1 (pre-existing): Add soft-cap logging for `review_lever` over-length**
`identify_potential_levers.py:159–175`

The validator enforces only ≥ 10 chars and no brackets. Adding a `logger.warning` (not a
`ValueError`) at > 300 chars would give observability without risking retry loops:
```python
if len(v) > 300:
    logger.warning(f"review_lever is long ({len(v)} chars); target is 20-40 words")
```

---

**I2 (pre-existing): Emit lever count in `run_single_plan_complete` event**
`runner.py:568–575`

The completion event records only `duration_seconds`. Including lever count would enable silent
under-generation detection in `events.jsonl` without parsing the full output JSON.

---

**I3 (NEW): Replace Section 5 numeric prohibition with worked counter-example**
`identify_potential_levers.py:255–259`

Abstract prohibitions on fabricated numbers have failed for gpt-oss-20b (insight finding 4).
The insight proposes a concrete counter-example pattern that outperforms abstract prohibitions
for mid-tier models:
> "BAD: 'Allocate 20% of the budget to X.' (20% does not appear in the project context)
>  GOOD: 'Allocate a portion of the contingency budget to X.' — qualitative is correct when the
>  split is not specified in the project."

This gives the model a positive example of what correct output looks like, avoiding the
prohibition-backfire dynamic.

---

**I4 (NEW): Add a fourth structurally distinct review_lever example in Section 4**
`identify_potential_levers.py:249–252`

The three current examples all follow a similar structure: subject → mechanism → risk. The
insight (Q2) notes that qwen3-30b's "leaves unresolved risk of…" lock may be driven by
example structure rather than the field description phrase. Adding a fourth example that:
- begins with a subject noun (not "Switching", "Each", or "Pooling")
- uses a different rhetorical structure (e.g., conditional or comparative framing)
- names a constraint in a non-finance/non-clinical domain

…would break qwen3-30b's structural lock by giving models more variety to draw from.

---

**I5 (NEW): Update `OPTIMIZE_INSTRUCTIONS` with finding about field-description phrase propagation**
`identify_potential_levers.py:27–93`

The insight recommends documenting the specific observed failure mode — that the field description
phrase "the proposed options collectively do not resolve" migrated into model outputs as template
lock for qwen3-30b and gpt-oss-20b. This is a concrete instance of the general "Field-description
template lock" warning already in OPTIMIZE_INSTRUCTIONS (lines 86–92). A specific note would
help future iterators recognize the pattern faster:

```
- Field-description copy of review_lever. The review_lever description phrase "the proposed
  options collectively do not resolve" (or "leave unaddressed") is itself a copyable sentence
  fragment. Weaker models paraphrase it: "leaves unresolved risk of…", "do not
  resolve/address/mitigate the risk that…", "remains unresolved". Rewrite the description to
  specify WHAT to identify (e.g., "state the gap that would persist even if all options ran")
  rather than a phrase that encodes how the sentence should begin or end.
```

---

**I6 (RESOLVED from prior review — I3): Anchoring risk in `consequences` field description**

PR #479 replaced "Exact numbers will be determined further downstream — here the goal is to
articulate the cause-effect relationship clearly" with "Use numbers only when the project context
provides them directly — do not calculate, derive, or estimate figures." The anchoring phrase is
gone. The consequences field length ratios remain stable (all models ≤ 1.6× baseline), confirming
no regression from this change. I3 from the prior analysis (72) is resolved.

---

## Trace to Insight Findings

| Insight finding | Code cause |
|----------------|-----------|
| **qwen3-30b: new template lock "leaves unresolved risk of…" (regression)** | B3 — field description embeds copyable phrase "collectively do not resolve"; B4 — Section 4 preamble doubles the signal. qwen3-30b, as a strong instruction-follower, reproduces the structural template from both locations. |
| **gpt-oss-20b: shifted template lock to "The options do not resolve/address the risk that…"** | B3 — same root cause; gpt-oss-20b copies the "collectively do not resolve" clause from the field description. Lock rate increased (10→15/17) rather than decreased because the new phrase is equally copyable. |
| **gpt-4o-mini: template lock genuinely reduced (improvement)** | Positive effect of PR #479's phrase change; gpt-4o-mini is a stronger instruction-follower that responded to the example diversity in Section 4 rather than only the field description structural cue. |
| **gpt-oss-20b: new fabricated % numbers in options (regression)** | S4 — Section 5 numeric prohibition may activate number-generation behavior; the phrase "use only numbers that appear verbatim" licenses interpreting a budget figure (HK$470M) as permission to derive percentages. |
| **llama3.1: second-call residual "leaving unaddressed" and short option labels** | B1 — when call 1 fails (or returns < min_levers), call 2 sends "Generate 5 to 7 MORE levers" with `[]` exclusion list, producing disjointed continuation output. The options ("Empower the Director", "Opt for Venice") are consistent with a model receiving a confused continuation prompt. |
| **claude-haiku: consistently high quality, no template lock** | High-capability models are not sensitive to structural cues in field descriptions — they comply with the content goal regardless. No code change needed. |
| **No LLMChatError across all 7 after-runs** | The `check_review_format` validator (structural-only: ≥ 10 chars, no brackets) correctly avoids English keyword checks. No regression here. |
| **claude-haiku reviews exceeding "one sentence" target** | No validator enforces maximum length on `review_lever`. I1 (soft-cap logging) would surface this. |

---

## PR Review

### PR #479 — "Comprehensive prompt refinement: verbatim numbers, template-lock fix, tighter targets"

**Change 1: Template-lock fix — "the three options leave unaddressed" → "the proposed options collectively do not resolve"**

*Field description* (`review_lever`, lines 127–131):
The replacement phrase "the proposed options collectively do not resolve" is still a sentence-
structural cue: it encodes the grammatical subject ("the proposed options"), verb phrase
("collectively do not resolve"), and object position for the model to complete. OPTIMIZE_INSTRUCTIONS
(lines 86–92) warns against exactly this pattern. The PR replaced one copyable phrase with
another. **This is B3.**

*System prompt Section 4 preamble* (line 247):
"One sentence identifying the key risk or constraint that the proposed options collectively do not
resolve." — replicates the field description phrase verbatim in the system prompt, creating a
second reinforcement point. **This is B4.**

*System prompt Section 6* (line 262):
"Keep each `review_lever` to one sentence (20–40 words). Identify the key unresolved risk
concisely." — this wording does NOT contain the copyable phrase. Section 6 was correctly updated.

**The fix is partial**: Section 6 is cleanly rewritten; Section 4 preamble and the field description
still carry the template phrase. For mid-tier models (qwen3-30b, gpt-oss-20b), the Pydantic field
description is the primary signal during structured output generation, so the Section 6 improvement
has limited effect when the field description contradicts it.

---

**Change 2: Verbatim-numbers rule extended to `options` field description**

*`options` field* (lines 122–124): Added "Use numbers only when the project context provides them
directly." Consistent with the `consequences` field change. For higher-capability models (haiku,
gpt-4o-mini) this works. For gpt-oss-20b, it may be contributing to the fabricated-% regression
(see S4): the phrase "when the project context provides them directly" could be read as permission
to use the HK$470M figure to derive percentage allocations. **Implementation is clean; behavioral
effect is negative for gpt-oss-20b.**

---

**Change 3: Section 5 tighter numeric restriction**

Added: "NO calculated, derived, or estimated figures — use only numbers that appear verbatim in
the project context"

This is an abstract prohibition following the pattern OPTIMIZE_INSTRUCTIONS warns against (lines
80–82). The insight confirms the backfire for gpt-oss-20b: 0→5-6 fabricated % values after the
PR. For haiku and gpt-4o-mini (no change in fabrication), the instruction was already unnecessary.
**Implementation is clean; behavioral effect is negative for gpt-oss-20b.** See I3 for the fix.

---

**Change 4: Removal of "Do NOT include 'Controls ... vs.'"**

Confirmed by the insight: the pattern was absent in all before-runs (87–93), so removal of the
prohibition has no observable effect. The change is harmless and follows OPTIMIZE_INSTRUCTIONS'
guidance to avoid explicit prohibition of named patterns. **Correct.**

---

**Change 5: Consistent targets ("2–3 sentences" for consequences, "one-sentence" for review)**

Field descriptions and system prompt sections now use consistent length targets. Field lengths
are stable across all models. **Correct; no regression.**

---

**Overall PR assessment:**

| Claimed fix | Outcome | Root cause of gap |
|-------------|---------|------------------|
| Template lock eliminated | Shifted (gpt-oss-20b), regressed (qwen3-30b), improved (gpt-4o-mini) | Field description still uses structural phrase (B3); Section 4 preamble duplicates it (B4) |
| Fabricated numbers eliminated | Regressed for gpt-oss-20b (0→5-6 per plan) | Section 5 abstract prohibition may activate number-generation (S4) |
| "Controls X vs Y" removed | No observable effect (already absent) | N/A — correct housekeeping |
| Consistent length targets | Achieved | N/A — correct |

The PR was correctly motivated and most changes are sound. The failure is that the template-lock
fix replaced one structural phrase with another, rather than replacing structural language with
content-goal language as OPTIMIZE_INSTRUCTIONS recommends. One root cause (copyable field
description phrase) drives two observed regressions (qwen3-30b and gpt-oss-20b).

---

## Summary

No new code logic bugs are introduced. The regressions are prompt-engineering bugs in the field
description and system prompt.

| ID | Type | Severity | Location | Description |
|----|------|----------|----------|-------------|
| B1 | Pre-existing | Low | `identify_potential_levers.py:297–306` | "MORE levers" prompt fires with empty exclusion list on first-call failure |
| B2 | Pre-existing | Low | `runner.py:577–583` | False `partial_recovery` event for fast 1-call success |
| B3 | New (PR #479) | Medium | `identify_potential_levers.py:127–131` | `review_lever` field description embeds copyable sentence structure, contradicting OPTIMIZE_INSTRUCTIONS lines 86–92 |
| B4 | New (PR #479) | Medium | `identify_potential_levers.py:246–247` | Section 4 preamble replicates the copyable phrase from the field description, doubling the template-lock signal |
| S1 | Pre-existing | Low | post-loop in `execute()` | No warning when final lever count < `min_levers` |
| S2 | Pre-existing | Low | `identify_potential_levers.py:121–157` | `options` validator accepts > 3 despite "No more, no fewer" description |
| S3 | Pre-existing | Info | `identify_potential_levers.py:206–220` | `LeverCleaned` field descriptions duplicate `Lever` descriptions; no comment marking them documentation-only |
| S4 | New (PR #479) | Medium | `identify_potential_levers.py:258` | Section 5 abstract numeric prohibition may activate number-fabrication for gpt-oss-20b |
| I1 | Pre-existing | Medium | `identify_potential_levers.py:159–175` | Add soft-cap logging for `review_lever` over-length |
| I2 | Pre-existing | Low | `runner.py:568–575` | Emit lever count in completion event |
| I3 | New | Medium | `identify_potential_levers.py:255–259` | Replace abstract numeric prohibition with worked counter-example (bad vs. good pattern) |
| I4 | New | Low | `identify_potential_levers.py:249–252` | Add fourth structurally distinct review_lever example |
| I5 | New | Low | `identify_potential_levers.py:27–93` | Update OPTIMIZE_INSTRUCTIONS with observed field-description phrase propagation finding |
| I3-prior | Resolved | — | — | Anchoring risk "Exact numbers will be determined downstream" is removed by PR #479 |

The most actionable fixes are **B3** and **B4**: rewrite the `review_lever` field description
and the Section 4 preamble to use content-goal language ("state the gap that would persist even
if all three options were executed in full") rather than sentence-structural language ("the
proposed options collectively do not resolve"). This directly addresses the qwen3-30b regression
and should reduce gpt-oss-20b's new template-lock rate without introducing a new copyable phrase.
