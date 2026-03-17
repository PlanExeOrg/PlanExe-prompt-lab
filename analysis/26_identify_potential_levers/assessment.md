# Assessment: fix: replace generic review_lever examples with domain-specific ones

## Issue Resolution

**What the PR aimed to fix:** The 100% template-lock rate where llama3.1 copies "This lever
governs the tension between…" verbatim and qwen3 uses "Core tension:" openers — both
behaviours caused by copyable generic phrases in the `review_lever` Pydantic field
description and system-prompt section 4. The PR replaced those examples with three
domain-specific, non-portable alternatives (agriculture, urban planning, insurance) in all
three locations: `Lever.review_lever`, `LeverCleaned.review`, and system-prompt section 4.

**Is it resolved?**

Yes — the primary lock is broken:

- **llama3.1** (run 82 → 89, hong_kong_game): "This lever governs/balances/navigates"
  opener: 15/15 (100%) → 0/16 (0%). Verified directly in the merged lever files.
- **qwen3** (run 85 → 92, hong_kong_game): "This lever [verb]" opener:
  ~19/19 (100%) → 1/18 (6%). Four of the first five reviews use novel,
  non-templated openers.

All three edited locations are confirmed correct in the live file
(`identify_potential_levers.py:96–111`, `:195–210`, `:234–239`).

**Residual symptoms:**

1. **New secondary template lock (llama3.1):** "The options assume that X is fixed,
   neglecting the possibility that…" appears in levers 8–11 of run 89 hong_kong_game at
   ~76% overall rate (13/17 reviews). Levers 8 and 9 are near-duplicates; levers 14 and 15
   share identical wording. The insurance example in the new prompt contains "the options
   neglect"; the urban-planning example contains "the options assume" — llama3.1 simply
   shifted its copy target to these subphrases.

2. **min_length floor too low:** Run 89 (llama3.1) parasomnia produced a 19-character
   review ("Sensor Data Sharing") that failed the `min_length=20` Pydantic validator,
   causing a plan-level error. The 20-char floor cannot distinguish a stub from a
   real review — the correct threshold is much higher.

3. **qwen3 residual tension framing:** ~28% of qwen3 reviews (run 92) still use "tension"
   framing, though opener variety is dramatically improved.

---

## Quality Comparison

Models in both batches (82–88 = before; 89–95 = after):

| Model | Before run | After run |
|---|---|---|
| ollama-llama3.1 | 82 | 89 |
| openrouter-openai-gpt-oss-20b | 83 | 90 |
| openai-gpt-5-nano | 84 | 91 |
| openrouter-qwen3-30b-a3b | 85 | 92 |
| openrouter-openai-gpt-4o-mini | 86 | 93 |
| openrouter-gemini-2.0-flash-001 | 87 | 94 |
| anthropic-claude-haiku-4-5-pinned | 88 | 95 |

| Metric | Before (runs 82–88) | After (runs 89–95) | Verdict |
|--------|---------------------|---------------------|---------|
| **Success rate** | 34/35 = 97.1% | 34/35 = 97.1% | UNCHANGED |
| **Bracket placeholder leakage** | 0 instances | 0 instances | UNCHANGED |
| **Option count violations** | Run 82 llama3.1 gta_game: 2 levers with 2 options | Same failure pattern per insight (LLMChatError count unchanged for llama3.1) | UNCHANGED |
| **Lever name uniqueness** | Not specifically measured | Not specifically measured | N/A |
| **Template lock — primary** ("This lever governs/balances/navigates") | llama3.1 15/15 (100%); qwen3 ~100% | llama3.1 0/16 (0%); qwen3 1/18 (6%) | **IMPROVED** |
| **Template lock — secondary** ("The options assume/neglect/overlook/fail") | ~0% (not observed) | llama3.1 13/16 (81%) | **REGRESSED** |
| **Review min_length compliance** | No violations observed | Run 89 parasomnia: 1 failure (19-char stub "Sensor Data Sharing") | REGRESSED (minor) |
| **Review format compliance** (baseline "Controls X vs Y. Weakness:…" pattern) | Not present in any model | Not present in any model | UNCHANGED (chronic) |
| **Consequence chain format** (Immediate→Systemic→Strategic markers) | Not in prompt, not present | Not in prompt, not present | UNCHANGED (N/A) |
| **Content depth — avg option length** | haiku ~270 chars; gpt-4o-mini ~130; llama3.1 ~85 | Stable per insight ("Field lengths stable — no verbosity regression") | UNCHANGED |
| **Field length ratio vs baseline — review** (baseline ~110 chars) | haiku ~430 chars (3.9×); llama3.1 ~150 (1.4×); gpt-4o-mini ~150 (1.4×) | Similar to before per insight; haiku may be identical (see New Issues) | UNCHANGED |
| **Cross-call duplication** | Not specifically measured | Not specifically measured | N/A |
| **Over-generation (>7 levers/call)** | haiku: 21 levers hong_kong_game; informational only | Unchanged pattern — downstream DeduplicateLeversTask handles extras | UNCHANGED |
| **Fabricated quantification** | 0 instances | 0 instances | UNCHANGED |
| **Marketing-copy language** | 0 instances | 0 instances | UNCHANGED |

**OPTIMIZE_INSTRUCTIONS check:** The constant (lines 27–73) already documents "Single-example
template lock" as a known problem and correctly prescribes "at least two structurally
distinct examples." The PR applied three examples, satisfying this guidance. However,
`OPTIMIZE_INSTRUCTIONS` does not yet document the secondary failure mode: *template-lock
migration*, where replacing one copyable example causes weaker models to shift to copying
subphrases within the new examples (e.g. "the options neglect", "the options assume").
This is a newly discovered pitfall that should be added.

---

## New Issues

**N1. Secondary template lock (llama3.1) — HIGH PRIORITY.**
The PR replaced one copyable opener but embedded two copyable subphrases in the replacement
examples. The insurance example ends "…the options neglect that a single hurricane season…";
the urban-planning example contains "the options assume permits will clear on the standard
timeline." Run 89 shows llama3.1 latched onto both phrases: 13/17 reviews (76%) open with
"The options [assume/neglect/overlook/fail to account for]…". Four levers (8–11) have
structurally near-identical reviews. Two pairs (levers 14/15) have identical wording.
This is the template-lock problem one level deeper.

**N2. haiku run 95 output integrity — INVESTIGATE.**
Sampled file verification found that `history/1/95_identify_potential_levers/outputs/
20260310_hong_kong_game/002-10-potential_levers.json` appears to contain identical content
to run 88 (same 21 levers, same lever IDs, same review text). The insight files do not
flag this. If confirmed, the resumable-runs feature (bug I5 from analysis 25: plans
skipped by name with no version/hash check) reused haiku's pre-PR outputs unchanged,
meaning the after-batch contains no actual post-PR haiku data. This would make the haiku
row of the comparison table unreliable.

**N3. LeverCleaned.review is confirmed dead code.**
Lines 195–211 of `identify_potential_levers.py` contain the `LeverCleaned.review` field
description with the full updated examples. The code review (S3) confirms this class is
never serialized into a schema passed to an LLM — the field description is never read by
any model. The PR correctly updated the text here for consistency, but updating it has no
effect on model output. Future changes to review examples need only target `Lever.review_lever`
(line 96) and the system prompt (line 234), not `LeverCleaned.review`.

**N4. OPTIMIZE_INSTRUCTIONS missing template-lock migration pattern.**
The current constant warns against single-example lock and prescribes multiple examples.
It does not document that copyable *subphrases within examples* also lock weaker models,
even when the opener itself is non-generic. This is a newly discovered failure mode.

---

## Verdict

**YES**: The PR achieves its stated goal. The primary llama3.1 template lock ("This lever
governs the tension between…") is completely broken (100% → 0%), and the qwen3 lock is
substantially reduced (~100% → 6%). No success-rate regression, no content-quality
regression in strong models, no fabricated statistics introduced. The secondary template
lock that emerged in llama3.1 is the expected next iteration of the same underlying problem
and is appropriate follow-up work, not a reason to revert.

---

## Recommended Next Change

**Proposal:** Remove copyable subphrases from the three domain-specific examples (strip
"the options neglect" and "the options assume" from the example text), then add a positive
diversity constraint: "Each review must address exactly one risk type not already covered
in the consequences field — choose from: production feasibility, stakeholder conflict,
financial viability, technical constraint, or audience reception." Simultaneously raise
`review_lever` `min_length` from 20 to 50 characters. Both changes are in the same file
and should be combined in one PR.

**Evidence:** The synthesis cites run 89 specifically: 13/17 hong_kong_game reviews (76%)
open with "The options [assume/neglect/overlook/fail]"; levers 8–11 are near-duplicate;
levers 14–15 are identical. The agriculture example ("stabilizes harvest quality, but none
of the options price in the idle-wage burden…") does not contain the offending subphrases
and produced no new lock — it is the correct structural template. The insurance and
urban-planning examples need the same treatment. The min_length finding (run 89 parasomnia:
19-char stub passes 20-char floor) provides a concrete floor for the new threshold.

**Verify:** In the next iteration, check:
- llama3.1 (new run ≈ 96): "The options [assume/neglect/overlook/fail]" opener rate should
  drop from 76% to <20% in hong_kong_game reviews.
- llama3.1: "Sensor Data Sharing"-style stub reviews should be eliminated (min_length=50
  would have caught the 19-char failure).
- qwen3 (new run ≈ 99): Verify residual "tension" framing does not increase.
- haiku (new run ≈ 102): Confirm the run is NOT reusing cached run-88 outputs — check lever
  IDs differ from runs 88 and 95 before treating haiku data as valid.
- All models: Verify no new subphrase from the updated examples achieves >30% adoption.
- All models: Confirm the positive diversity constraint ("production feasibility / stakeholder
  conflict / financial viability…") increases review topic variety without creating a new
  enumeration-copy pattern.

**Risks:**
- The positive diversity constraint enumerates 5 categories, which weaker models may copy
  verbatim ("This review addresses production feasibility risk…"), creating a new label
  lock. If this occurs, remove the explicit enumeration and rephrase as guidance.
- Raising min_length to 50 may cause additional llama3.1 parasomnia failures if that plan
  consistently elicits very short reviews. Monitor LLMChatError count for llama3.1 — if it
  increases from 1/5 to 2/5 or more, the threshold may be too aggressive.
- If haiku run 95 is confirmed as cached run-88 data (issue N2), the next iteration must
  also fix the resumable-runs version/hash check before haiku can serve as a reliable
  test subject.

**Prerequisites:** None strictly required, but investigating and confirming the haiku run-95
data integrity issue (N2) before the next experiment would prevent wasting a haiku run on
potentially cached outputs.

---

## Backlog

**Resolved (can be removed):**
- Template lock root cause: copyable generic opener in `review_lever` example — RESOLVED by PR #337. The primary lock is broken. The secondary lock is a new variant, tracked separately.

**Carry forward from analysis 25:**
- Hard `options == 3` validator over-reach — change `len(v) != 3` to `len(v) < 3` (B1 from analysis 25 code review). Still unresolved.
- "at least 15 words" missing from Pydantic `options` field description (I2 from analysis 25). Still unresolved.
- Closure capture latent bug in `execute_function` loop (S1 from analysis 25). Still unresolved.
- Global dispatcher event handler cross-contamination in concurrent-worker runs (B3 / S2). Still unresolved.

**New items from this analysis:**
- **Secondary template lock (llama3.1):** "The options assume/neglect/overlook/fail" at 76%. Fix: strip copyable subphrases from examples and add positive diversity constraint. HIGH PRIORITY — next PR.
- **Raise review_lever min_length to 50:** 20-char floor fails to reject 19-char stub "Sensor Data Sharing". Fix: change `len(v) < 20` to `len(v) < 50` at line 151.
- **haiku run-95 data integrity:** Investigate whether run 95 outputs are cached from run 88 (same lever IDs observed). If confirmed, fix resumable-runs version/hash check before relying on haiku data.
- **LeverCleaned.review is dead code:** Field description (lines 195–211) is never serialized to an LLM. Either strip the description or add a code comment explaining it is for human readers only. Future prompt changes need not update this location.
- **OPTIMIZE_INSTRUCTIONS: add template-lock migration pattern:** Document that replacing one copyable example can shift weaker models to copying subphrases within the new example. Note the agriculture example as the correct structural template (no copyable subphrases).
- **Docstring cites wrong run:** `check_option_count` docstring (line 131) says "Run 89" but the 2-option error was in run 82 (llama3.1 gta_game). Fix in passing when editing the file for other reasons.
