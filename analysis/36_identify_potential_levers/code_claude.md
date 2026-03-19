# Code Review (claude)

## Bugs Found

### B1 — False `partial_recovery` events for efficient models (runner.py:120–129, 517–523)

Two places fire `partial_recovery` whenever `calls_succeeded < 3`:

```python
# runner.py:120-123
if actual_calls < 3:
    logger.warning(f"{plan_name}: partial recovery — {actual_calls} calls succeeded")

# runner.py:517-523
if (step == "identify_potential_levers"
        and pr.calls_succeeded is not None
        and pr.calls_succeeded < 3):
    _emit_event(events_path, "partial_recovery", ..., expected_calls=3)
```

The inner loop in `identify_potential_levers.py:331–333` stops early when
`len(generated_lever_names) >= min_levers` (min_levers=15). A model that
produces 8+ levers per call stops at 2 calls with a full 16+ lever set — a
complete success — but both code paths above fire `partial_recovery` as if
something failed.

`PlanResult` carries no `levers_count` field, so the runner cannot distinguish
"stopped early with enough levers" from "one call failed and we limped home."
The comment at runner.py:117–119 acknowledges 2-call success is normal yet the
warning fires unconditionally.

### B2 — Single invalid lever discards the entire batch (identify_potential_levers.py:130–158)

Pydantic validates the full `DocumentDetails` object atomically. When one lever
in a 5–7 lever batch has 2 options (`check_option_count`, line 138) or a
degenerate `review_lever` (`check_review_format`, line 154), the entire call's
response is rejected and falls into the `except Exception` handler. If that was
the first call (`len(responses) == 0`, line 319), the plan fails immediately —
no retry, all other valid levers in the batch are lost.

This is the direct cause of run 59's plan-level failures:
- **gta_game**: "options must have at least 3 items, got 2" — one lever
  failed, killed a batch that contained 5 other valid levers.
- **parasomnia**: "review_lever is too short (2 chars); expected at least 10"
  — all levers in the batch had `review_lever='>'`, rejected atomically.

The validator design (strict by intent per the comment at line 131–136) is
correct in principle, but the granularity is wrong: the unit of rejection should
be the individual lever, not the whole call. Partial batches with ≥5 valid
levers could be kept.

### B3 — `expected_calls=3` is still a hardcoded literal (runner.py:523)

The PR description says it removed the "stale `expected_calls=3` constant."
Looking at the code, `expected_calls=3` is still a literal at line 523 — only
moved inline, not made dynamic. This means:

1. The value does not adapt if `min_levers` changes in `identify_potential_levers.py`.
2. The `partial_recovery` threshold (`< 3`) is also hardcoded (lines 519, 120),
   creating the false-positive problem in B1.

The two values (`min_levers=15` in the inner module and `expected_calls=3` in
the runner) are semantically coupled but physically disconnected. Changing one
without the other silently breaks the monitoring.

---

## Suspect Patterns

### S1 — Prohibition text names the banned phrases verbatim (identify_potential_levers.py:239)

```python
"   - NO starting review_lever with "The options", "These options", "The lever", or "These levers" ..."
```

For instruction-following at llama3.1 scale, explicitly printing the exact
banned phrases in the prompt can *increase* their probability mass. The model
sees "The options" as a salient token in the system prompt and may pattern-match
to it rather than respect the negation. The insight confirms hong_kong went from
0% "The options" lock (after PR #353) to 100% lock (after PR #354) — the only
change between those PRs was adding this prohibition.

### S2 — Game-dev example domain overlaps with test plans (identify_potential_levers.py:230)

The third review_lever example ("GPU migration cuts frame time…") targets the
GPU/game-dev domain. The test corpus includes `hong_kong_game` and `gta_game` —
both in the game/entertainment domain. llama3.1 activates the most domain-similar
example as a template. The insight confirms: PR #353 (different examples, no
game-dev) gave 0% lock on hong_kong; PR #354 (game-dev example added) reverted
to 100% lock. The example domain choice is a direct template leakage vector.

### S3 — All three examples share the same "hidden cost" rhetorical structure (identify_potential_levers.py:228–231)

Despite spanning agriculture, medical, and technology:
- Example 1: "X stabilizes Y, but Z adds fixed cost that erases savings unless condition."
- Example 2: "Each additional X requires Y — sequential overhead that compounds, so doubling X does not halve Y."
- Example 3: "Migrating to X cuts Y in benchmarks, yet every Z must be re-profiled — cost is hidden in non-obvious place."

All three follow the pattern: *"apparent benefit → hidden undermining cost in
unexpected dimension."* Even without "The options" as subject, weaker models
will apply this shared skeleton, forming a new template lock. The silo run 59
data (insight negative #3) shows exactly this: each call developed its own
variant of the hidden-cost trope.

### S4 — Redundant `messages_snapshot` shallow copy (identify_potential_levers.py:294)

```python
messages_snapshot = list(call_messages)
```

`call_messages` is a new list constructed each loop iteration and not mutated
after creation. `execute_function` is called synchronously within the same
iteration via `llm_executor.run()`. The snapshot adds no correctness guarantee
and creates a misleading "this list might change" implication.

---

## Improvement Opportunities

### I1 — Add soft template-lock detection logging

In `check_review_format` (identify_potential_levers.py:142–158), add a
non-raising warning when `review_lever` starts with known lock openers:

```python
_LOCK_OPENERS = ("the options", "these options", "the lever", "these levers")
if v.lower().startswith(_LOCK_OPENERS):
    logger.warning("template_lock detected: review_lever starts with '%s'", v[:30])
```

This makes the lock rate observable in production logs without causing
validation failures or altering behaviour. (Insight C1)

### I2 — Add degenerate review_lever detection

Extend `check_review_format` to catch values that are pure punctuation or
arrow-separator artifacts:

```python
import re
if re.fullmatch(r'[\s=>\-<|:;,.!?]+', v):
    raise ValueError(f"review_lever appears to be a punctuation artifact: {v!r}")
```

This catches the parasomnia `=>` failure mode (run 59) with an actionable
error message rather than the generic "too short" error. It also enables
targeted retry prompt injection. (Insight C2)

### I3 — Add `levers_count` to PlanResult to fix the partial_recovery false positive

```python
@dataclass
class PlanResult:
    ...
    levers_count: int | None = None   # total levers after dedup
```

Set it in `_run_levers` from `len(result.levers)`. In `_run_plan_task`, emit
`partial_recovery` only if `levers_count < 15` (or whatever `min_levers` is
configured to):

```python
if (step == "identify_potential_levers"
        and pr.levers_count is not None
        and pr.levers_count < 15):
    _emit_event(...)
```

This eliminates false positives for efficient 2-call completions and directly
exposes the `min_levers` coupling between the inner loop and the runner.

### I4 — Expose `min_levers` as a named constant

Define `MIN_LEVERS = 15` at module level in `identify_potential_levers.py` and
re-export it. Import it in `runner.py` instead of the bare integer `3`. This
keeps the two threshold values in sync mechanically.

### I5 — Allow partial batch salvage on Pydantic failure

Rather than failing the entire call when one lever fails validation, parse levers
individually after extracting the raw JSON from the structured LLM response.
Levers that parse successfully can be accumulated; only per-lever failures are
skipped. This requires moving away from batch `DocumentDetails` parsing toward
per-lever validation but would prevent a single bad lever from destroying 5+
valid ones.

### I6 — Remove English-specific field-description text from Lever.consequences

`identify_potential_levers.py:98–99`:
```python
"Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text ..."
```

This is an English-only instruction in a field description that the LLM sees.
For non-English prompts, models may ignore it or reproduce the English pattern
anyway. OPTIMIZE_INSTRUCTIONS (lines 61–68) explicitly flags this class of
problem. The field description should use structural guidance ("keep consequences
to direct effects and trade-offs only") rather than English keyword examples.

---

## Trace to Insight Findings

| Insight finding | Root cause in code |
|---|---|
| llama3.1 hong_kong 0% → 100% "The options" lock (run 59) | S1: prohibition names the banned phrase, increasing its probability. S2: game-dev example domain overlaps hong_kong. |
| llama3.1 parasomnia `=>` Pydantic failure (run 59) | B2: one degenerate lever kills the entire batch; S1: prohibition confuses small models into alternative formats. |
| llama3.1 gta_game 2-options Pydantic failure (run 59) | B2: one lever with 2 options kills a 5–7 lever batch on first call, plan fails. |
| llama3.1 silo/sovereign_identity new per-call template lock | S3: all examples share "hidden cost" structure; weaker models shift to this skeleton. |
| haiku partial_recovery unchanged at 2/3 plans | B1: 2-call result always triggers partial_recovery; cannot tell if haiku stopped early (good) or failed calls. |
| gpt-oss-20b hong_kong "[Name]: [tension]; options [verb]" template | S3: shared rhetorical structure propagated to cloud models; prohibition passed technically (subject is lever name) but pattern persists. |
| B1 fix confirmed working (step-gating) | runner.py:517–519 step guard works. B3 still present (hardcoded literal). |

---

## PR Review

### Intent vs. implementation

**Domain-diverse examples** (lines 228–231): Implementation is correct — three
examples now span agriculture, medical, and technology. None uses "The options"
as grammatical subject. However, the game-dev example (S2) introduces a domain
that directly overlaps the `hong_kong_game` and `gta_game` test plans, which is
a template leakage vector for small models. The PR's intent to introduce diverse
domains is sound; the choice of the gaming domain is the misstep.

**Explicit prohibition** (line 239): The implementation adds the prohibition
string to section 5 of the system prompt. The text is grammatically clear and
technically correct English. The bug is not in the implementation but in the
approach: naming the banned phrases in the prohibition increases their prompt
salience for instruction-following-weak models (S1). The PR implements the
feature correctly but the feature itself is counterproductive for llama3.1-scale
models, as confirmed by the 0% → 100% regression in run 59.

**B1 fix** (runner.py:517–519): Correctly adds `step == "identify_potential_levers"`
guard. The `expected_calls=3` literal (B3) remains hardcoded — the PR description
says the stale constant was "removed" but it was only moved inline. Functionally
the gating works; the constant coupling is still latent.

**OPTIMIZE_INSTRUCTIONS documentation** (lines 69–83): Correctly documents the
structural homogeneity requirement and multi-call template drift. Accurate and
useful for future prompt engineers.

### Gaps and edge cases the PR misses

1. **Prohibition + example conflict**: The prohibition says "do not use 'The
   options'", but the examples are now in a domain (gaming) that llama3.1 will
   reach for when generating hong_kong reviews. The prohibition and the example
   domain interact to produce a worse outcome than either alone.

2. **No check that example review_lever text itself is prohibition-compliant**:
   The three review_lever examples do not start with "The options" — so they
   are compliant. But they were not verified against the OPTIMIZE_INSTRUCTIONS
   requirement that "no two examples share a sentence pattern or rhetorical
   structure." All three share the hidden-cost adversarial structure (S3).

3. **Partial batch recovery not addressed**: The PR description does not mention
   the batch-rejection problem (B2). gta_game and parasomnia both failed because
   one bad lever discarded a full call. This was a pre-existing design tension
   the PR did not address.

4. **`min_levers`/`expected_calls` coupling not documented**: The PR removes the
   "stale constant" label but the value 3 is still implicitly derived from
   `min_levers=15 / ~5 levers-per-call`. No comment links these two numbers.

### Did it fix what it claimed?

| Claim | Outcome |
|---|---|
| Domain-diverse examples fix parasomnia/gta_game template lock | FAILED — both plans now error (Pydantic failures) for llama3.1, not just locked templates |
| Explicit prohibition prevents "The options" as subject | FAILED for llama3.1 (hong_kong: 0% → 100% regression); technically passed for cloud models |
| B1 fix scopes partial_recovery to identify_potential_levers | CONFIRMED WORKING |
| OPTIMIZE_INSTRUCTIONS documents structural homogeneity | CONFIRMED — accurate addition |

---

## Summary

**Three systemic issues explain the PR's regressions:**

1. **Prohibition backfire (S1, B-PR)**: Naming the banned phrases in the
   prohibition increases their probability mass for small models. For llama3.1,
   the prohibition caused or worsened the "The options" lock it was meant to
   eliminate. Cloud models (which follow instructions reliably) were unaffected.

2. **Domain collision (S2, B-PR)**: The game-dev example was added to improve
   coverage of gaming-domain plans (gta_game), but it made hong_kong and
   sovereign_identity worse by giving llama3.1 a nearby template to copy.

3. **Batch rejection atomicity (B2)**: The Pydantic validation model rejects an
   entire 5–7 lever batch when one lever is invalid. The two plan failures in run
   59 (gta_game, parasomnia) both stem from this: a single bad lever on the first
   call caused immediate plan failure because `len(responses)==0` forces a hard
   raise. The PR did not introduce this behavior but the new examples made it more
   likely to trigger for llama3.1.

**The only unambiguously correct change is the B1 step-gating fix** (runner.py:517–519).
It should be preserved in a separate PR. The example and prohibition changes are
the likely net cause of the regression from 100% to 94.3% plan success rate.

**Recommended actions:**
- Revert the game-dev example and the explicit prohibition.
- Cherry-pick the B1 step-gating fix into a standalone PR.
- Fix B2 (partial batch salvage) before re-attempting domain-diverse examples.
- Add I1 (template-lock logging) and I2 (degenerate review_lever detection) to
  make future regressions detectable from event logs without manual inspection.
