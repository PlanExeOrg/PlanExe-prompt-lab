# Synthesis

## Cross-Agent Agreement

Only one agent produced artifacts for this analysis (Claude, both insight and code review). The two files are highly consistent and mutually reinforcing:

- **B2 (duplicate example removal) is unambiguously positive.** Both files confirm: ~150–200 token savings per call verified via `activity_overview.json`, consequences contamination ("A weakness in this approach is that…") resolved in llama3.1 gta_game run 03, no detected downside.
- **B1 (template lock fix) only partially worked.** gta_game lock dropped 100% → 62.5% but only for first-call levers; parasomnia stayed at ~100%; "the options neglect" persists in gpt-5-nano run 05.
- **Root cause correctly identified.** All three `review_lever` examples in the current system prompt use "the options" or "none of the options" as the critique's grammatical subject. PR #340 changed only example 3, leaving examples 1 and 2 as live template-lock sources.
- **New fabricated % regression confirmed.** Run 03 gta_game levers 1–6 show 5 fabricated "by at least X%" claims in `consequences`; run 96 (before PR) had zero. Both files attribute this to the replacement example 3's causal sentence structure cueing llama3.1 into magnitude-claim endings.
- **gpt-oss-20b JSON truncation failure** (run 04, sovereign_identity) is assessed as non-deterministic and not caused by PR #340.

---

## Cross-Agent Disagreements

No inter-agent disagreements exist (single agent). One internal tension is worth resolving:

**OPTIMIZE_INSTRUCTIONS (lines 73–79) says the agriculture example is "the correct structural template" — but that example still uses "none of the options price in" as its opener.**

Reading the source (line 224): `"Switching from seasonal contract labor to year-round employees stabilizes harvest quality, but none of the options price in the idle-wage burden during the 5-month off-season."`

The OPTIMIZE_INSTRUCTIONS intent was that the domain-specific tail ("idle-wage burden during the 5-month off-season") makes this non-portable. That is true for the tail — but the opener "none of the options price in" is domain-portable and is precisely what weaker models copy as a sentence frame. The code review correctly notes this contradiction: example 1 was praised as the correct template but it still uses "the options" as subject. The OPTIMIZE_INSTRUCTIONS text is partially wrong, and needs to be updated to clarify that even example 1 is a partial template-lock source due to its "none of the options" opener.

Verified by source code: lines 224–226 of `identify_potential_levers.py` confirm all three examples use "the options / none of the options / absent from every option" as the critique anchor.

---

## Top 5 Directions

### 1. Replace all three `review_lever` examples to eliminate "The options [verb]" structure
- **Type**: prompt change
- **Evidence**: insight_claude.md (H1, C1), code_claude.md (B1, I1). Confirmed by source code: example 1 uses "none of the options price in", example 2 uses "the options assume", example 3 (post-PR) ends with "correlation risk absent from every option". All three anchor to options as critique subject. Run 05 gpt-5-nano still produces "the options neglect" — proof examples 1 or 2 are the source. Parasomnia lock at 100% unchanged. First call vs later call divergence shows system prompt examples are the sole driver (calls are stateless).
- **Impact**: Eliminates "The options [verb]" template lock across all three LLM calls and all models. The partial improvement seen in gta_game first-call (100% → 62.5%) when one example was changed predicts that changing all three will complete the shift. Affects all models, all plans, all three calls.
- **Effort**: Low — edit three bullet strings in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (lines 224–226).
- **Risk**: Each replacement example must itself avoid introducing a new portable copyable pattern. The new example 3 demonstrates the failure mode: replacing one lock phrase with another options-anchored clause. New examples must use a named stakeholder, named constraint, or named failure condition as the subject — not "the options". OPTIMIZE_INSTRUCTIONS lines 78–79 already describe the correct form.

### 2. Verify and fix the replacement example 3 to eliminate fabricated % cueing
- **Type**: prompt change
- **Evidence**: insight_claude.md (H2), code_claude.md (B2). Run 03 gta_game levers 1–6 contain 5 fabricated "by at least X%" claims (20%, 15%, 25%, 30%, 20%) in `consequences`. Run 96 (before PR) had zero. Only the first LLM call is affected, which is the call that sees the original user prompt with the unchanged system prompt. The replacement example 3's causal-chain structure ("a regional hurricane season can correlate all three simultaneously") appears to cue llama3.1 into ending consequence sentences with a magnitude estimate. The fabrication directly violates the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers.
- **Impact**: Eliminates a new content quality regression introduced by PR #340. Affects llama3.1 first-call consequences. If this is already subsumed by direction 1 (all three examples replaced), direction 2 becomes a constraint on how direction 1 is written: ensure no replacement example contains percentage claims or quantitative causal chains.
- **Effort**: Low — examine the consequence sentence structure in the new examples and replace with qualitative language. Practically this merges into direction 1.
- **Risk**: Low, but requires careful drafting. The prohibition in section 2 of the system prompt ("Do not fabricate percentages or cost estimates") is already present but not enforced by the examples themselves. The new examples should model qualitatively framed consequences.

### 3. Update `OPTIMIZE_INSTRUCTIONS` with two newly confirmed patterns
- **Type**: code fix (documentation in code)
- **Evidence**: code_claude.md (I5), insight_claude.md (OPTIMIZE_INSTRUCTIONS Alignment section). Two patterns confirmed in runs 03–09 are not yet documented:
  1. **Multi-call template divergence**: first LLM call in the 3-call loop produces a different format because it receives the raw user prompt; subsequent calls include accumulated lever names, and the system prompt examples drive the template independently in every call. When a prompt change partially breaks a lock, it must be verified across all three calls, not just the first.
  2. **Replacement-example contamination**: when replacing a template-locking example, verify the replacement text does not introduce a new leakage pattern in a different field (e.g., percentage claims in `consequences`).
  Also: the existing OPTIMIZE_INSTRUCTIONS note (lines 73–79) says the agriculture example "is the correct structural template" but this is partially wrong — its "none of the options price in" opener is still a copyable template lock source. The note should be corrected.
- **Impact**: Prevents the same mistakes in future iterations. OPTIMIZE_INSTRUCTIONS is read at the start of every analysis cycle; keeping it accurate avoids wasted iterations.
- **Effort**: Low — add two bullet points and correct one existing bullet (lines 69–80).
- **Risk**: None. Pure documentation.

### 4. Fix the `Lever.options` field description to match actual validator behavior
- **Type**: code fix
- **Evidence**: code_claude.md (B4, I2). `Lever.options` description (line 100) says "Exactly 3 options for this lever. No more, no fewer." The validator (`check_option_count`, lines 125–137) only enforces a minimum of 3. Over-generation (4+ options) passes silently. The OPTIMIZE_INSTRUCTIONS comment on lines 161–163 explicitly states over-generation is acceptable. The field description sends conflicting instructions to the LLM via structured output schema serialization: it says "no more" but the code accepts more. This is a lie in the schema that confuses models into being overly strict.
- **Impact**: Models will no longer attempt to truncate to exactly 3 options when 4 would be more accurate. Reduces the chance of silent over-constraint causing a model to drop a valid option. Minor but clean correctness improvement.
- **Effort**: Low — change line 100 from "Exactly 3 options ... No more, no fewer" to "At least 3 options (3 is typical; more is acceptable if genuinely distinct)."
- **Risk**: None. The change aligns the schema description with actual enforcement behavior.

### 5. Add normalized fuzzy deduplication before the cleaned output
- **Type**: code fix
- **Evidence**: code_claude.md (B3, I3). Run 03 gta_game produced both "Multplayer Modes" (typo) and "Multiplayer Modes" — semantically identical levers that both pass the exact-string `seen_names` check. The existing guard (`lines 331–337`) is intended to catch duplicates but only fires on byte-for-byte identical names, which rarely occur because the multi-call prompt explicitly instructs the model not to reuse names. Typo variants and near-matches pass through to downstream `DeduplicateLeversTask`.
- **Impact**: Reduces noise levers in the output. Low marginal value since `DeduplicateLeversTask` handles semantic duplicates; the main value is reducing redundant work downstream and reducing lever count inflation.
- **Effort**: Low — add `re.sub(r'[^a-z0-9 ]', '', name.lower()).strip()` normalization to the seen-names check.
- **Risk**: Low. The normalized check is additive — it only skips levers that are near-identical to already-accepted ones. False positive risk (two distinct levers with normalized-identical names) is negligible in practice.

---

## Recommendation

**Pursue direction 1 and 2 together as a single PR: replace all three `review_lever` examples with domain-specific, non-"options-centric" critiques that avoid both "The options [verb]" openers and percentage claims.**

**Why first:** This is the direct, unfinished business of PR #340. The template lock analysis across 7 models and 2+ plans shows the lock is wholly driven by the system prompt examples — specifically by all three examples using "the options" or "none of the options" as the critique's grammatical subject. PR #340 changed one of three examples and got a partial improvement; changing all three should complete it. The fabricated % regression (direction 2) is also caused by example phrasing and is addressed in the same edit.

**Specific change — file `identify_potential_levers.py`, lines 224–226:**

Replace the current three examples:
```
- "Switching from seasonal contract labor to year-round employees stabilizes harvest quality, but none of the options price in the idle-wage burden during the 5-month off-season."
- "Routing the light-rail extension through the historic district unlocks ridership but triggers Section 106 heritage review; the options assume permits will clear on the standard timeline."
- "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a regional hurricane season can correlate all three simultaneously — correlation risk absent from every option."
```

With three examples that each name a named constraint, stakeholder, or failure condition as the critique subject — never "the options":

```
- "Switching from seasonal contract labor to year-round employees stabilizes harvest quality, but the idle-wage burden during the 5-month off-season is unaccounted for — a cost that can erase the per-unit quality gain entirely."
- "Routing the light-rail extension through the historic district unlocks ridership, but Section 106 heritage review adds a 12–18 month permitting layer that no financing model in this plan is structured to absorb."
- "Pooling catastrophe risk across three coastal regions looks diversified on paper, but a single Gulf hurricane season can trigger correlated losses in all three simultaneously — an exposure no option in this lever addresses."
```

**Rules for any new examples (to be enforced in the PR review):**
1. The critique subject must be a named entity (a cost, a regulatory process, a correlation condition) — not "the options", "none of the options", or "the options fail/assume/neglect".
2. No fabricated percentages or generic magnitude claims ("by at least X%"). If a number appears, it must be the kind of figure that is inherently tied to the domain context of the example (e.g., "5-month off-season" is a seasonal fact, not a fabricated statistic).
3. The critique's tail must be non-portable — it should only make sense in its specific domain context.

Also in the same PR: update `OPTIMIZE_INSTRUCTIONS` lines 73–79 to note that even the agriculture example's opener ("none of the options price in") is a copyable frame, and clarify that ALL examples must avoid options-as-subject constructions.

---

## Deferred Items

- **Direction 3 (OPTIMIZE_INSTRUCTIONS update)**: Should be included in the same PR as direction 1, but is lower priority on its own. Best done alongside the example replacement so the documentation matches the new examples.
- **Direction 4 (fix "Exactly 3" field description)**: Clean low-effort fix, can be bundled into the same PR.
- **Direction 5 (fuzzy deduplication)**: Worth doing but low impact. Defer to a standalone housekeeping PR.
- **gpt-oss-20b JSON truncation (run 04)**: Suspected non-deterministic. Re-run sovereign_identity with gpt-oss-20b to confirm. If reproducible, investigate context-window limits for that model/plan combination. Not related to the current prompt changes.
- **Multi-call architecture and context accumulation (S1/S2 in code review)**: The current 3-call stateless loop is working as designed; the divergence between call 1 and calls 2–3 is a prompt effect, not an architectural bug. No change needed now, but worth monitoring after the example replacement to see if calls 2–3 also shift.
- **`_resolve_workers` silent degradation (S4)**: Add a warning log for missing config. Useful diagnostic but entirely unrelated to prompt quality. Defer.
