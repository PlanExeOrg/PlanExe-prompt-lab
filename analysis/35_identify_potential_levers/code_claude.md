# Code Review (claude)

Files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `self_improve/runner.py`
- `worker_plan/worker_plan_internal/llm_util/llm_executor.py` (supporting context)

PR under review: #353 "fix: replace review_lever examples to break template lock"

---

## Bugs Found

### B1 — `partial_recovery` triggers on successful 4+ call runs
**File:** `self_improve/runner.py:115` and `runner.py:514`

`_run_levers` hardcodes `expected_calls = 3`:
```python
expected_calls = 3
actual_calls = len(result.responses)
if actual_calls < expected_calls:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls}/{expected_calls} calls succeeded")
return PlanResult(..., calls_succeeded=actual_calls)
```

And `_run_plan_task` also hardcodes `3`:
```python
if pr.calls_succeeded is not None and pr.calls_succeeded < 3:
    _emit_event(events_path, "partial_recovery", ..., expected_calls=3)
```

`IdentifyPotentialLevers.execute()` sets `max_calls = 5` and `min_levers = 15`. If a model
returns only 4 levers per call, it needs 4 successful calls (4+4+4+4 = 16 ≥ 15) and the
loop exits normally. All 4 calls succeed, but `calls_succeeded = 4 > 3` — wait, that would
NOT trigger the bug. The bug fires when a model succeeds with exactly 2 calls: if a model
returns 8 levers per call, call 1 = 8, call 2 = 16 ≥ 15 → stop with `calls_succeeded = 2`,
which emits a false `partial_recovery` event even though no call failed. The `partial_recovery`
event was designed to mean "a call threw an exception and we recovered from prior data", but
the `< 3` test conflates two distinct cases:
1. Early success (model over-generated — all calls succeeded, hit `min_levers` in 2 calls)
2. True partial recovery (the 3rd call threw an exception, continuing with prior levers)

The haiku partial recoveries in run 58 (`silo: 2, parasomnia: 2`) could be either case.
Looking at events.jsonl for run 58, both plans completed with `status: ok`, making it
ambiguous whether calls actually failed or the model simply hit `min_levers` early.

**Fix direction:** Track a separate counter for failed calls inside `IdentifyPotentialLevers`
and return it alongside `calls_succeeded`. Emit `partial_recovery` only when actual failures
occurred, not when the model exceeded `min_levers` in fewer than 3 calls.

---

### B2 — Dispatcher event handler cross-thread contamination
**File:** `self_improve/runner.py:187–191, 217–219`

When `workers > 1`, each plan's thread registers its own `TrackActivity` handler on the
global LlamaIndex `dispatcher`:
```python
with _file_lock:
    set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")
    dispatcher.add_event_handler(track_activity)
```

The lock makes the add/remove atomic but does not prevent cross-thread event dispatch.
During execution, dispatcher events from thread A's LLM call are broadcast to all registered
handlers — including thread B's `TrackActivity` instance. Thread B's handler will write
spurious events to thread B's `track_activity.jsonl`.

The practical damage is limited because `track_activity.jsonl` is deleted at the end
(`runner.py:220`), and `_maybe_generate_activity_overview` reads from `usage_metrics.jsonl`
(which uses thread-local storage). However, any intermediate consumer of `track_activity.jsonl`
(e.g., real-time monitoring) would see cross-plan events. The data corruption is silent.

**Fix direction:** Either use a thread-local dispatcher, or add a thread-ID filter to
`TrackActivity` so it silently drops events originating from other threads.

---

### B3 — Case-sensitive name deduplication allows near-identical lever names through
**File:** `identify_potential_levers.py:337–341`

```python
seen_names: set[str] = set()
for i, lever in enumerate(levers_raw, start=1):
    if lever.name in seen_names:
        logger.warning(f"Duplicate lever name '{lever.name}', skipping.")
        continue
    seen_names.add(lever.name)
```

The set is case-sensitive. If call 1 produces "Workforce Strategy" and call 2 produces
"workforce strategy" (common with models that vary capitalization between calls), both
levers pass through. The downstream `DeduplicateLeversTask` catches these, but at the cost
of extra tokens in the dedup step.

**Fix direction:** Normalize `lever.name.strip().lower()` for the seen-names check while
preserving the original casing in the output.

---

## Suspect Patterns

### S1 — `lever_index` field is generated but immediately discarded
**File:** `identify_potential_levers.py:84–86`

```python
lever_index: int = Field(description="Index of this lever.")
```

The LLM is asked to produce an integer index for every lever, but it is never read in the
cleaning loop (`levers_raw` → `levers_cleaned`, lines 339–353). `LeverCleaned` has no
`lever_index` field. The field costs tokens in every LLM call — roughly one token per
lever per call — with zero benefit. It may also confuse models into producing sequential
integers rather than focusing on lever content.

### S2 — `strategic_rationale` tokens are always wasted
**File:** `identify_potential_levers.py:158–163`

```python
class DocumentDetails(BaseModel):
    strategic_rationale: Optional[str] = Field(
        default=None,
        description="A concise strategic analysis (around 100 words) ..."
    )
    levers: list[Lever] = ...
```

`strategic_rationale` is included in `save_raw` via `model_dump()` but is never surfaced in
`save_clean()` or used by any downstream step. Every LLM call produces ~100 words of rationale
that is saved in the raw file and then ignored. For 3 calls × 7 models × 5 plans = 105 calls
per iteration, this wastes ~10,500 words of generation capacity that could go toward lever
detail.

### S3 — All three new `review_lever` examples share the same contrast structure
**File:** `identify_potential_levers.py:225–227`

The three post-PR examples:
1. "Switching … stabilizes … **but** the idle-wage burden … adds a fixed cost …"
2. "Section 106 … triggers … **that falls entirely outside** the project schedule …"
3. "Pooling … reduces … **but** a single regional hurricane season can correlate …"

Examples 1 and 3 use the identical "X improves Y, **but** Z reverses the gain" template.
Even example 2 follows the same adversarial contrast structure ("triggers X that falls outside
Y"). A model that internalizes this three-example set learns: "review_lever = describe an
action, then name a hidden risk that cancels it." That structure is correct, but the lack
of variety in rhetorical form gives weaker models very little structural flexibility. The
insight's observation of secondary lock ("The lever misses/overlooks") emerging in parasomnia's
second LLM call is consistent with the model copying the implied contrast structure while
swapping in a new subject.

### S4 — Prompt section 6 mandates 15-word options but no validator enforces it
**File:** `identify_potential_levers.py:240`, `identify_potential_levers.py:125–137`

Section 6: "Each option should be a concrete, actionable approach (at least 15 words with
an action verb) — not a short label or vague aspiration"

`check_option_count` validates only `len(v) < 3`; there is no word-count check. The insight
documents silo run 52 options averaging ~7–8 words (e.g., "Zone-based governance empowers
local self-sufficiency and specialization" = 7 words). The prompt instruction is present but
unenforceable, so it silently fails for weaker models.

---

## Improvement Opportunities

### I1 — Add soft validator for `review_lever` template-lock detection
**File:** `identify_potential_levers.py:139–155`

The insight hypothesizes (code hypothesis C1) that adding a logged warning when `review_lever`
starts with "the options", "these options", or "the lever" would make template-lock observable
in production without causing validation failures. The current `check_review_format` validator
only checks minimum length (10 chars) and no square brackets.

Proposed addition inside `check_review_format`:
```python
lock_prefixes = ("the options ", "these options ", "the lever ")
if v.lower().startswith(lock_prefixes):
    logger.warning("review_lever may be template-locked: starts with '%s'", v[:40])
```
This surfaces the problem in logs without affecting success rate.

### I2 — Add soft validator for option minimum word count
**File:** `identify_potential_levers.py:125–137`

Extend `check_option_count` or add a new validator:
```python
short_options = [opt for opt in v if len(opt.split()) < 10]
if short_options:
    logger.warning("options appear label-like (<%d words): %s", 10, short_options)
```
The insight documents this problem (silo run 52 options at ~7 words). A soft warning (not
raised) would accumulate evidence without causing retries.

### I3 — Add domain-diverse `review_lever` examples
**File:** `identify_potential_levers.py:225–227`

All three post-PR examples are from the construction/agriculture/insurance sector. The insight
shows this produces dramatic improvement for silo and hong_kong_game (construction-adjacent)
but near-zero improvement for parasomnia (medical research) and gta_game (video-game). Adding
one scientific/medical example and one technology/software example would provide structural
templates the model can map to non-construction plans. The OPTIMIZE_INSTRUCTIONS section
already documents that examples must avoid reusable phrases — an analogous note that examples
must span structurally different domains would reinforce this.

### I4 — Add explicit prohibition for template-lock openers in section 5
**File:** `identify_potential_levers.py:230–235`

Section 5 "Prohibitions" does not mention "The options overlook" or "The lever misses" as
forbidden openers. Adding an explicit prohibition alongside the existing ones (no prefixes,
no generic labels, etc.) gives the model a direct negative instruction rather than relying
on example diversity alone. Example addition:
```
- NO review_lever that opens with "The options", "These options", or "The lever" —
  instead name the specific mechanism, assumption, or constraint that is at risk.
```

### I5 — Remove or use `lever_index` field
**File:** `identify_potential_levers.py:84–86`

Either remove `lever_index` from `Lever` (the cleaning loop already uses `enumerate(start=1)`)
or add a comment explaining why it exists. As it stands, it silently consumes output tokens.

### I6 — Remove `strategic_rationale` from `DocumentDetails` or consume it
**File:** `identify_potential_levers.py:158–163`

If `strategic_rationale` is never used downstream, remove the field from the schema to
eliminate ~100 words of wasted generation per LLM call. If it has latent value (e.g., for
debugging), at minimum document why it is kept and which downstream step uses it.

### I7 — Make `expected_calls` in runner.py derive from `min_levers` / per-call minimum
**File:** `self_improve/runner.py:115`

The hardcoded `3` should either be a named constant imported from `identify_potential_levers.py`
(where `min_levers=15` and the per-call target of 5–7 lives) or replaced with a more robust
check that distinguishes true failures from early-success completions.

---

## Trace to Insight Findings

| Insight observation | Root cause in code |
|---|---|
| llama3.1 parasomnia: "the options" lock persists at ~82% | S3: All 3 examples share the same adversarial contrast structure, and none map to medical-research domain. I3, I4 address this. |
| llama3.1 gta_game: lock shifted to "These options…" (~78%) | S3: "These options" is structurally identical to "The options" — the example set doesn't prohibit this variant. I4 addresses this. |
| New "the lever misses/overlooks" pattern in parasomnia 2nd LLM call | S3: Each call receives the same system prompt with the same 3 examples. No call-to-call diversity signal; secondary lock re-emerges in each independent call. |
| llama3.1 silo options are label-length (~7 words) | S4: The 15-word minimum in section 6 is unvalidated. I1 and I2 address detection. |
| haiku partial recoveries (0 → 2 plans, 2/3 calls each) | B1: The `< 3` test is ambiguous between "true failure recovered" and "hit min_levers early in 2 calls." Cannot determine from events.jsonl alone whether these are real regressions or false alarms. |
| Domain-bias of new examples toward construction/finance | S3 + I3: All three examples cluster in the same sector. No code enforces example-domain diversity. |
| Overall template lock halved (~85% → ~40%) for llama3.1 | PR #353 correctly removed "the options" as grammatical subject in all examples, which is the direct, correct fix. The remaining 40% is explained by S3 and I4. |
| gpt-oss-20b sovereign_identity JSON EOF resolved | Likely non-deterministic; the longer/cleaner examples may have slightly reduced output length, avoiding a truncation boundary. No code change explains this definitively. |

---

## PR Review

### What the PR changes

1. Replaces all three `review_lever` examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`
   section 4 (lines 225–227) from options-centric phrases to domain-specific mechanism
   sentences.
2. Adds a "Template-lock migration" block to `OPTIMIZE_INSTRUCTIONS` (lines 73–80)
   documenting the known-problem of shifting templates.

### Does the implementation match the intent?

**Yes, correctly for the targeted problem.** The grammatical-subject fix is the right
intervention. Before the PR, all three examples used "the options" as subject, giving llama3.1
a single reusable opener it reproduced 94% of the time. After the PR, no example uses "the
options", and llama3.1 silo lock dropped to 0%.

### Bugs in the PR itself

None introduced. The PR is additive (replacing text in the system prompt constant and
OPTIMIZE_INSTRUCTIONS string). No logic, validators, or data structures were changed.

### Gaps in the PR

**Gap 1 — Domain monoculture.** All three new examples are from real estate / agriculture /
catastrophe insurance. Plans in medical research (parasomnia) or video-game (gta_game) domains
did not benefit because the structural patterns (seasonal labor, heritage permits, hurricane
correlation) don't transfer. The PR's own OPTIMIZE_INSTRUCTIONS addition correctly warns about
template-lock migration but does not require example-domain diversity. See I3.

**Gap 2 — Structural homogeneity of examples.** Examples 1 and 3 are both "X improves Y, but
Z reverses the gain." Example 2 follows the same adversarial form. A model that copies the
contrast structure instead of the specific words will produce secondary lock ("the lever
misses/overlooks"). This is exactly what the insight observes in parasomnia's second LLM call.
See S3 and I4.

**Gap 3 — No explicit prohibition added.** Section 5 "Prohibitions" was not updated to forbid
"The options overlook", "These options", or "The lever misses" as openers. Without a direct
negative instruction, models can shift to synonyms of the banned example pattern. See I4.

**Gap 4 — No validator for template lock.** Code hypothesis C1 in the insight (adding a soft
warning when `review_lever` starts with a locked pattern) was not implemented. Adding it would
make future regressions visible in logs immediately. See I1.

**Gap 5 — No validator for option word count.** The options field under-length problem (silo
run 52: ~7-word options) persists. See S4 and I2.

### OPTIMIZE_INSTRUCTIONS alignment

The updated OPTIMIZE_INSTRUCTIONS (lines 73–80) is accurate and actionable. It correctly
documents that "replacing a copyable opener does not eliminate template lock" and that
"examples must avoid reusable transitional phrases." It does not yet:

- Require examples to span structurally distinct domains (medical, technology, construction, etc.)
- Warn about secondary lock forming independently in each LLM call's context
- Document the option word-count failure mode observed in silo run 52

These three additions would close the gaps the PR left open.

---

## Summary

PR #353 correctly removes "the options" as grammatical subject from all three `review_lever`
examples — the direct cause of 94% template lock in llama3.1. This single change accounts
for the dramatic improvement in silo (0% lock) and hong_kong_game (0 exact-duplicate reviews).
The OPTIMIZE_INSTRUCTIONS update accurately documents template-lock migration.

The remaining issues are not regressions introduced by the PR but limitations of its scope:

- **B1** (false `partial_recovery` events): Pre-existing; `expected_calls=3` mixes early
  success with true failure recovery. The haiku regression in run 58 may be a false alarm.
- **B2** (dispatcher cross-thread contamination): Pre-existing; affects multi-worker runs.
  Low practical impact because `track_activity.jsonl` is deleted, but data is silently wrong
  during execution.
- **B3** (case-sensitive deduplication): Minor pre-existing issue.
- **S3** (structural homogeneity of examples): The core reason parasomnia and gta_game still
  show ~80% lock. All three examples model the same "X but Y" contrast. The PR fixed the
  subject but not the structure.
- **S4** (unvalidated option word count): Pre-existing; the 15-word requirement in section 6
  has no enforcement.

Priority improvements for the next iteration:
1. **I3** — Add one medical/scientific and one technology/software `review_lever` example.
2. **I4** — Add explicit prohibition for "The options/These options/The lever" openers in
   section 5.
3. **I1** — Add soft logged warning in `check_review_format` for template-lock openers.
4. **B1** — Fix `partial_recovery` to distinguish true failures from early-success completions.
