# Code Review (claude)

## Bugs Found

**B1: "MORE levers" retry prompt fires on first-call failure with empty exclusion list**
`identify_potential_levers.py:297–304`

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

When call 1 fails (exception path, `continue` at line 346), `generated_lever_names` is still
empty when call 2 runs. The prompt becomes:

> "Generate 5 to 7 MORE levers with completely different names. Do NOT reuse any of these
> already-generated names: []\n\n{user_prompt}"

Problems:
- "MORE" implies the model is continuing a previous batch, which it isn't — it's starting fresh.
- The empty brackets `[]` are syntactically odd and expose the template skeleton to the model.
- Weaker models (llama3.1, gpt-oss-20b) are more likely to mirror the anomalous framing, potentially
  producing mislabeled or off-structure output.

Fix: gate on `if call_index == 1 or not generated_lever_names:` to use the plain `user_prompt`
when no prior levers exist.

---

**B2: False `partial_recovery` event emitted for fast single-call success**
`runner.py:577–583`

```python
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 2):
    _emit_event(events_path, "partial_recovery",
                plan_name=plan_name,
                calls_succeeded=pr.calls_succeeded,
                expected_calls=3)
```

If a model returns ≥ 15 levers in a single call (or the model is verbose and hits `min_levers=15`
on call 1), `len(generated_lever_names) >= 15` triggers an early `break` at line 352–354. The
adaptive loop then exits with `len(responses) == 1`, so `actual_calls == 1 < 2` — and
`partial_recovery` fires with `expected_calls=3` even though the run succeeded perfectly.

This creates misleading noise in `events.jsonl` for analysis scripts that scan for
`partial_recovery` as a failure signal.

Fix: change the condition to check whether lever count is below the minimum (pass lever count
from `_run_levers`), or at minimum change `expected_calls=3` to `expected_calls=2` and add
a comment clarifying that 1-call success is valid.

---

## Suspect Patterns

**S1: No post-loop warning when adaptive loop exits below `min_levers`**
`identify_potential_levers.py:354` (after the `break`) and `identify_potential_levers.py:356`

If calls 1–5 all fail except one that returns 5 levers, the code silently proceeds with 5 levers
— 10 fewer than the `min_levers=15` target. There is no post-loop guard:

```python
if len(generated_lever_names) >= min_levers:
    logger.info(...)
    break
# loop ends — no check here
```

Downstream steps (DeduplicateLevers, EnrichLevers) may behave differently with 5 vs. 15 levers.
A `logger.warning` after the loop when `len(generated_lever_names) < min_levers` would surface
this silently degraded case during analysis.

---

**S2: `options` validator contradicts field description on over-generation**
`identify_potential_levers.py:145–157` and field description at line 121–124

The field description says "Exactly 3 options for this lever. No more, no fewer." The system
prompt section 1 says "Each lever's `options` field must contain exactly 3 qualitative strategic
choices." But the validator only enforces `>= 3`:

```python
if len(v) < 3:
    raise ValueError(...)
return v  # 4, 5, 6 options all pass
```

A model that reads "Exactly 3… no more, no fewer" may infer that 4 options triggers a Pydantic
`ValueError` and become defensive (truncating or adding padding). The mismatch between prompt
language ("no more") and validator behavior (silently accepts more) is a latent confusion source
for instruction-following models. The comment at line 186-191 correctly explains the intent
("over-generation is fine"), but the field description should be updated to say "At least 3
options" to align with actual validation behavior.

---

**S3: `LeverCleaned.consequences` duplicates the LLM-facing `Lever.consequences` description**
`identify_potential_levers.py:206–215`

`LeverCleaned` is documented as "never sent to an LLM" (line 194-198), but its `consequences`
field description at lines 206–215 is a verbatim copy of `Lever.consequences` at lines 112–119,
including the prompt-directed language ("Exact numbers will be determined further downstream —
here the goal is to articulate the cause-effect relationship clearly."). If a future refactor
accidentally uses `LeverCleaned` as a structured LLM output schema, the field description would
send contradictory signals. Low risk currently, but worth keeping the two schemas clearly separated.

---

**S4: Thread-safety comment is misleading about why the lock is held**
`runner.py:239–251`

```python
# set_usage_metrics_path uses thread-local storage, but we still hold
# _file_lock while configuring it alongside the dispatcher to keep the
# setup/teardown atomic.
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

If `set_usage_metrics_path` is truly thread-local, it needs no lock. The lock is actually needed
only for `dispatcher.add_event_handler` (which mutates a shared list). Bundling both under the
same lock is harmless but the comment conflates two separate concerns. A future maintainer who
refactors `set_usage_metrics_path` to be non-thread-local might drop the lock while still
mutating `dispatcher.event_handlers` unprotected.

---

## Improvement Opportunities

**I1: Add soft-cap logging for `review_lever` over-length**
`identify_potential_levers.py:159–175`

The `check_review_format` validator enforces only `>= 10 chars` and no square brackets. The
insight reports 38% of reviews exceed 200 chars despite the "One sentence (20–40 words)" target.
Adding a `logger.warning` (not a `ValueError`) at, say, > 300 chars would give observability
without risking retry loops:

```python
if len(v) > 300:
    logger.warning(f"review_lever is long ({len(v)} chars); target is 20-40 words")
```

OPTIMIZE_INSTRUCTIONS already warns against hard Pydantic caps, so a soft warning is the right
mechanism here.

---

**I2: Emit lever count in the `run_single_plan_complete` event**
`runner.py:568–575`

The completion event currently records only `duration_seconds`. Including the lever count would
make it possible to detect silent under-generation in `events.jsonl` without parsing the output
JSON:

```python
_emit_event(events_path, "run_single_plan_complete",
            plan_name=plan_name,
            duration_seconds=pr.duration_seconds,
            levers_generated=pr.calls_succeeded)  # or a dedicated field
```

---

**I3: Positive-framing anchoring risk in `consequences` field description**
`identify_potential_levers.py:114–116`

The phrase "Exact numbers will be determined further downstream — here the goal is to articulate
the cause-effect relationship clearly" was introduced by PR #477 to discourage fabricated numbers.
However, it contains a subtle anchoring risk: "exact numbers will be determined downstream" could
be read by a model as permission to provide approximate numbers now ("I'll give rough figures since
exact ones come later"). This reading explains why a subset of models (especially domain-primed
ones like silo/parasomnia) continue to emit percentage values — the instruction implicitly licenses
them to contribute numeric approximations.

A safer framing would avoid referencing numbers at all: "Describe the cause-effect relationship
in plain terms — focus on direction, magnitude order (large/small), and timing, not specific
quantities."

---

## Trace to Insight Findings

| Insight finding | Code cause |
|----------------|-----------|
| **3 plan timeouts (runs 5/12, 5/13)** | Not directly caused by prompt code. The adaptive loop makes up to 5 serial LLM calls; if a model has high per-call latency (e.g. gpt-oss-20b with long structured output), 2–3 calls can exceed 600s. No code-level fix exists for external service latency; the timeout is a correct ceiling. Monitoring whether the same plans time out in subsequent runs is the right test. |
| **38% of reviews exceed 200 chars** | S2 / I1 — no upper-bound validation on `review_lever`; `check_review_format` only enforces a 10-char floor. |
| **Qwen pct claims unchanged (3→3)** | I3 — the "Exact numbers will be determined downstream" anchor phrase may give qwen permission to include domain-grounded approximations; the prohibition in section 5 competes with this positive framing. |
| **Silo/parasomnia residual pct claims** | I3 — same anchoring risk; engineering-domain context activates model priors about tolerances, and the field description inadvertently licenses approximate numbers. |
| **Haiku pct claims reduced 70%** | PR #477's primary change correctly removed number-evidence constraints. The insight confirms this worked. |
| **B2 false partial_recovery events** | Would appear in events.jsonl for models that hit ≥ 15 levers in one call. Doesn't affect output quality but pollutes the analysis signal. |

---

## PR Review

### PR #477 — "Qualitative consequences, positive framing, and consistent length targets"

**Does the implementation match the intent?**

Yes, for the primary goal. The changes are coherent and correctly applied across all three
locations where the text appears (Lever.consequences field desc, LeverCleaned.consequences field
desc, and system prompt section 2 and 5). The redundancy between Lever and LeverCleaned is
pre-existing, not introduced by this PR.

**Specific changes examined:**

1. `consequences` field description — "Exact numbers will be determined further downstream — here
   the goal is to articulate the cause-effect relationship clearly. Target length: 2–3 sentences."

   The intent (remove number-evidence requirement) is achieved, but the phrasing introduces an
   anchoring risk (see I3). The insight's residual silo/parasomnia pct claims are consistent with
   this side-effect. The PR correctly diagnoses that explicit "Never invent" prohibitions
   backfired; however, the downstream-reference framing carries its own risk for models trained
   on engineering corpora.

2. Section 5 Prohibitions — "NO specific numbers, percentages, or monetary amounts — describe
   effects qualitatively"

   This is a direct, strong prohibition and does not suffer the anchoring risk. For haiku, this
   worked: 70% reduction. For qwen, the field description's anchor phrase appears to outweigh the
   section 5 prohibition, since qwen is a strong instruction-follower but the field description
   is read first during structured output generation.

3. Removal of "Do NOT include 'Controls ... vs.'"

   Confirmed inert — the pattern was absent before. The change is harmless but provides no value.
   It does reduce system prompt length slightly (minor positive).

4. "2-3 sentences" consistency

   Correctly synchronized across Lever.consequences, LeverCleaned.consequences, and system prompt
   section 2. Field lengths are stable (298→300 chars avg) confirming no regression.

5. `review_lever` "One sentence (20-40 words)" confirmation

   The field description at line 125–131 and system prompt section 6 now match. However, neither
   the Pydantic validator nor the system prompt enforces this limit, and 38% of reviews still
   exceed 200 chars. The confirmation is cosmetically correct but not enforcement-effective.

**Gaps and edge cases the PR misses:**

- **Qwen3-30b immunity**: Qwen reads the field description before the system prompt prohibition.
  The anchoring phrase in the field description appears to override the section 5 prohibition for
  qwen's structured-output path. A targeted fix for qwen would need to change the field
  description itself (which the PR does do) — but the "determined downstream" anchor replaces one
  problematic phrase with another.

- **No validation change**: The PR changes only prompt text. It doesn't add any validator to
  enforce the "no numbers" or "one sentence" constraints, so regression is entirely dependent on
  prompt compliance. This is consistent with OPTIMIZE_INSTRUCTIONS' guidance to avoid hard Pydantic
  caps, but a soft logged warning (I1) would improve observability.

- **`LeverCleaned.consequences` description is also updated**: The PR correctly keeps Lever and
  LeverCleaned field descriptions in sync. Since LeverCleaned is never sent to an LLM, this
  update is documentation-only and has no functional effect — but it's correct practice.

**Verdict on the PR itself**: The code change is clean, minimal, and correctly applied. The primary
goal (reduce haiku pct claims) is achieved with no structural bugs introduced. The residual issues
(qwen immunity, silo/parasomnia domain anchoring, review length overshoot) are pre-existing
limitations that the PR partially but not fully addresses.

---

## Summary

No critical bugs that would cause data loss or hard failures. Two confirmed bugs (B1, B2) produce
misleading log/event output but do not corrupt lever content. The most actionable improvement is
I3 (anchoring risk in the consequences field description), which may explain why qwen3-30b and
domain-heavy plans continue to emit percentage claims despite the section 5 prohibition.

| ID | Severity | Location | Description |
|----|----------|----------|-------------|
| B1 | Low | `identify_potential_levers.py:297–304` | "MORE levers" retry prompt fires on first-call failure with empty exclusion list |
| B2 | Low | `runner.py:577–583` | False `partial_recovery` event for fast single-call success |
| S1 | Low | `identify_potential_levers.py` post-loop | No warning when final lever count < `min_levers` |
| S2 | Low | `identify_potential_levers.py:121–157` | options validator contradicts "no more, no fewer" field description |
| S3 | Info | `identify_potential_levers.py:206–215` | LeverCleaned.consequences duplicates LLM-facing field description |
| S4 | Info | `runner.py:239–251` | Misleading lock comment conflates thread-local and shared-state concerns |
| I1 | Medium | `identify_potential_levers.py:159–175` | Add soft-cap logging for review_lever over-length |
| I2 | Low | `runner.py:568–575` | Emit lever count in completion event |
| I3 | Medium | `identify_potential_levers.py:114–116` | "Exact numbers will be determined downstream" anchors models to provide approximate numbers |
