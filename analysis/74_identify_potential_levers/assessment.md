# Assessment: Comprehensive prompt refinement: verbatim numbers, template-lock fix, tighter targets

## Issue Resolution

**What PR #479 was supposed to fix:**
1. Arithmetic-derivation loophole — extend verbatim-numbers rule to consequences AND options fields
2. Template-lock fix — replace "the three options leave unaddressed" with "the proposed options collectively do not resolve" in `review_lever` field description, Section 4, and Section 6
3. Positive framing — remove "Do NOT include 'Controls ... vs.'" prohibition
4. Consistent length targets — "2–3 sentences" for consequences, "one sentence" for review
5. Section 5 hard prohibition on derived/estimated figures

**Resolution status:**

1. **Template lock (primary goal): Partially resolved, regression introduced.**
   The "the three options leave unaddressed" phrase was eliminated. gpt-4o-mini improved from ~5/16 locked reviews to 0/17 (verified from `history/5/29_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`). However, the replacement phrase "the proposed options collectively do not resolve" is itself a copyable structural cue. qwen3-30b developed a new lock ("leaves unresolved risk of…" / "remains unresolved") present in 7/20 reviews in run 28, where it had 0/15 locked before. gpt-oss-20b shifted from one lock pattern to another (lock rate increased from ~10/17 to ~15/17). The root cause — a sentence-structural phrase in the field description — was not eliminated, only changed.

2. **Fabricated numbers: Not resolved; regression introduced.**
   gpt-oss-20b went from 0 fabricated percentage values in run 88 to 5 in run 26 (verified: "Secure a 60% local co-production agreement…", "Allocate 20% of total budget…", "Shift 15% of the budget…", etc.). The abstract Section 5 prohibition ("NO calculated, derived, or estimated figures — use only numbers that appear verbatim") appears to have activated number-generation attention in gpt-oss-20b rather than suppressing it.

3. **"Controls X vs Y" removal: No observable effect.** The pattern was already absent in all before-runs (2/87–2/93). Correct housekeeping per OPTIMIZE_INSTRUCTIONS, but not a net quality gain.

4. **Consistent length targets: Achieved.** Field lengths stable across all models. No regression.

5. **Residual symptoms:**
   - The copyable phrase "collectively do not resolve" now appears in both the Pydantic field description (`identify_potential_levers.py:127–131`) and the Section 4 preamble (`line 247`), doubling the template-lock signal (B3 + B4 per code review).
   - The pre-existing B1 bug ("MORE levers" prompt fires with empty `[]` exclusion list when call 1 fails) still produces short label options and residual "leaving unaddressed" in llama3.1 second-call outputs (levers 9–18 in run 25).

---

## Quality Comparison

Only models appearing in both batches (runs 2/87–2/93 = before; runs 5/25–5/31 = after) are compared.

| Metric | Before (runs 2/87–2/93) | After (runs 5/25–5/31) | Verdict |
|--------|------------------------|------------------------|---------|
| **Overall call success rate** | 102/105 = 97.1% | 105/105 = 100% (no LLMChatErrors) | IMPROVED (+2.9pp) |
| **LLMChatErrors / ValidationErrors** | 0 | 0 | UNCHANGED |
| **Bracket `[...]` placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations (< 3)** | 0 | 0 | UNCHANGED |
| **Lever name uniqueness** | All unique per run | All unique per run | UNCHANGED |
| **"Controls X vs Y" pattern in reviews** | 0 (already absent) | 0 | UNCHANGED |
| **Consequence chain markers** | Not enforced | Not enforced | N/A |
| **Template lock — gpt-4o-mini (hong_kong_game)** | ~5/16 "leaving unaddressed" | 0/17 | IMPROVED |
| **Template lock — qwen3-30b (hong_kong_game)** | 0/15 locked | 7/20 "leaves unresolved / remains unresolved" | REGRESSED (new lock) |
| **Template lock — gpt-oss-20b (hong_kong_game)** | ~10/17 locked | ~15/17 locked (shifted pattern) | REGRESSED (lock shifted + rate increased) |
| **Template lock — claude-haiku** | 0 (no lock) | 0 (no lock) | MAINTAINED |
| **Template lock — llama3.1 (call 2 levers)** | ~4/18 "leaving unaddressed" | ~4/18 "leaving unaddressed" | UNCHANGED (pre-existing B1 bug) |
| **Fabricated % numbers — gpt-oss-20b (options)** | 0 | 5 (60%, 40%, 20%, 15%, 10%) | REGRESSED |
| **Fabricated % numbers — qwen3-30b (options)** | 0 | 1 (70%/30% crew split) | SLIGHT REGRESSION |
| **Fabricated % numbers — gpt-4o-mini, haiku** | 0 | 0 | MAINTAINED |
| **Review avg length — gpt-4o-mini (chars)** | ~85 | ~95 | ~1.1× baseline, UNCHANGED |
| **Review avg length — qwen3-30b (chars)** | ~110 | ~100 | ~1.1× baseline, SLIGHT IMPROVEMENT |
| **Review avg length — claude-haiku (chars)** | ~280 | ~265 | 2.9× baseline, UNCHANGED (warning) |
| **Review avg length — gpt-oss-20b (chars)** | ~190 | ~165 | 1.8× baseline, SLIGHT IMPROVEMENT |
| **Consequences avg length — all models** | ≤ 1.6× baseline | ≤ 1.6× baseline | UNCHANGED (within bounds) |
| **Cross-call lever name duplication** | None observed | None observed | UNCHANGED |
| **Over-generation count (> 7 levers/call)** | qwen3-30b 15→20 total | qwen3-30b 20 total, others stable | INFORMATIONAL |
| **Marketing-copy language** | Not observed | Not observed | UNCHANGED |
| **partial_recovery events (haiku)** | 2 events (run 93) | 0 visible in events.jsonl | IMPROVED |

**OPTIMIZE_INSTRUCTIONS alignment:** The PR introduced code (B3, B4 in code review) that directly violates `OPTIMIZE_INSTRUCTIONS` lines 86–92 ("Field-description template lock: A Pydantic field description containing a structural phrase is read as a literal instruction"). The phrase "the proposed options collectively do not resolve" is structurally identical in mechanism to the "name the core tension" phrase PR #358 was designed to remove. The PR fixed one instance of a known anti-pattern while re-introducing the same anti-pattern. OPTIMIZE_INSTRUCTIONS is correct and up-to-date; the live code contradicts it.

---

## New Issues

1. **B3 (new): `review_lever` field description embeds a copyable sentence structure.**
   `identify_potential_levers.py:127–131` — "the proposed options collectively do not resolve" is a sentence-structural cue in the same class as the "name the core tension" phrase this PR was meant to eliminate. Confirmed: qwen3-30b went from 0/15 to 7/20 locked; gpt-oss-20b lock rate increased from ~10/17 to ~15/17.

2. **B4 (new): Section 4 preamble duplicates the copyable phrase.**
   `identify_potential_levers.py:246–247` — the same phrase appears verbatim in the system prompt Section 4 preamble, creating a second reinforcement point. Fixing the field description alone is insufficient; both locations must be updated.

3. **S4 (new): Section 5 abstract numeric prohibition may activate number-generation.**
   `identify_potential_levers.py:258` — the abstract rule "NO calculated, derived, or estimated figures" is of the type OPTIMIZE_INSTRUCTIONS (lines 80–82) warns against ("Do NOT add explicit prohibitions naming banned phrases — small models treat the prohibition text as a template"). gpt-oss-20b regression from 0 to 5 fabricated % values is consistent with this dynamic.

4. **Latent issue surfaced: B1 (pre-existing) — "MORE levers" prompt fires with empty exclusion list.**
   `identify_potential_levers.py:297–306` — when call 1 fails, call 2 sends "Generate 5 to 7 MORE levers … Do NOT reuse any of these already-generated names: []". This produces disjointed continuation output (llama3.1 run 25, levers 9–18: "Empower the Director", "Opt for Venice", "Blended Visuals" as option labels). This was pre-existing but is now clearly confirmed in the after-batch evidence.

---

## Verdict

**CONDITIONAL**: PR #479 delivers a genuine improvement for gpt-4o-mini (template lock eliminated from ~5/16 to 0/17) but introduces two regressions — qwen3-30b gained a new template lock (0/15 → 7/20) and gpt-oss-20b gained 5 fabricated percentage values where it had none. Both regressions are directly traceable to prompt-engineering decisions in this PR that violate OPTIMIZE_INSTRUCTIONS. The PR should not be treated as complete until the `review_lever` field description and Section 4 preamble are rewritten to remove the copyable phrase "the proposed options collectively do not resolve", and the Section 5 abstract numeric prohibition is replaced with a concrete counter-example.

---

## Recommended Next Change

**Proposal**: Rewrite the `review_lever` Pydantic field description (`identify_potential_levers.py:127–131`) and the Section 4 preamble (`line 247`) to use content-goal language rather than sentence-structural language. Specifically, replace "the proposed options collectively do not resolve" with phrasing that describes WHAT gap to identify without providing a copyable sentence template (e.g., "state the specific structural or operational gap that would remain open even if all three options were fully executed"). Optionally, replace the Section 5 abstract numeric prohibition with a BAD/GOOD worked counter-example.

**Evidence**: The synthesis cites confirmed evidence from two locations:
- `identify_potential_levers.py:127–131` (B3): field description contains copyable phrase verified present in source
- `identify_potential_levers.py:246–247` (B4): Section 4 preamble contains the same phrase at a second location
- qwen3-30b: 0/15 → 7/20 template-locked reviews (regression confirmed in run 28 outputs)
- gpt-oss-20b: shifted lock pattern, rate increased 10/17 → 15/17 (confirmed in run 26 outputs)
- gpt-4o-mini: genuine improvement (5/16 → 0/17), retained when phrase changes don't add new structural cues
- gpt-oss-20b fabricated %: 0 → 5 instances (confirmed directly in `history/5/26_*/002-10-potential_levers.json`)

The synthesis recommendation is well-evidenced. It cites specific run numbers, file paths, before/after lock counts, and links each regression to a specific line in the source code.

**Verify in the next iteration (runs 5/32–5/38):**
- qwen3-30b: confirm "leaves unresolved risk of…" / "remains unresolved" lock rate returns to ≤ 2/20 (near-zero as before the PR)
- gpt-oss-20b: confirm template lock rate decreases from ~15/17; confirm fabricated % count drops from 5 (Section 5 counter-example change)
- gpt-4o-mini: confirm lock rate does not regress (stays near 0/17; the gpt-4o-mini improvement must be preserved)
- claude-haiku: confirm lock-free status maintained (currently 0/17, should stay 0/17 regardless of field description wording)
- llama3.1: check whether B1 fix (gate "MORE levers" on non-empty exclusion list) eliminates short labels ("Empower the Director") and "leaving unaddressed" in second-call levers
- gpt-oss-20b options field: if Section 5 counter-example is added, verify the "60%/40%/20%" pattern is gone; if only field description is changed without S5 fix, check whether fabricated % persists or reduces

**Risks:**
- The proposed replacement phrase "state the specific structural or operational gap that would remain open even if all three options were fully executed" still contains "all three options" — if this triggers a new "all three options" lock (as happened in analysis 40 with haiku), the phrase would need a further revision. The key property is: the subject of the review sentence should NOT be "the options"; it should be the domain-specific constraint.
- If Direction 2 (Section 5 counter-example) and Direction 1 (field description rewrite) are bundled in the same PR, it becomes harder to isolate which change fixed which regression. If gpt-oss-20b still fabricates numbers after the field description change alone, Direction 2 is confirmed necessary.
- Removing the abstract Section 5 prohibition entirely (rather than replacing with a counter-example) risks reintroducing number fabrication for models that comply via instruction rather than example.

**Prerequisite issues:**
- No blockers. Direction 1 is a standalone prompt change with no code dependencies.
- B1 (empty exclusion list on retry) can be fixed in the same PR or as a standalone; it does not interact with the prompt changes.

---

## Backlog

**Resolved from before (analysis 40 backlog):**
- "None/All three options" secondary lock in haiku (analysis 40 Negative #1) — resolved. Haiku shows 0/17 locked in run 31, no template lock. The lock from analysis 40 (driven by "the three options leave unaddressed") was eliminated by PR #479's phrase change.
- Section 6 "under 2 sentences" ambiguity (analysis 40) — resolved. Section 6 now consistently says "one sentence (20–40 words)".

**New issues to add:**
- **B3**: `review_lever` field description embeds copyable phrase "the proposed options collectively do not resolve" — confirmed source of qwen3-30b regression and gpt-oss-20b lock migration. Fix: rewrite to goal-oriented language. (`identify_potential_levers.py:127–131`)
- **B4**: Section 4 preamble duplicates B3 phrase, doubling the template-lock signal. Must be fixed together with B3. (`identify_potential_levers.py:246–247`)
- **S4**: Section 5 abstract numeric prohibition may activate number-fabrication in gpt-oss-20b. Fix: replace with BAD/GOOD counter-example. (`identify_potential_levers.py:258`)
- **B1 (pre-existing, priority elevated)**: "MORE levers" continuation prompt fires with empty `[]` exclusion list when call 1 fails — confirmed producing short option labels and residual "leaving unaddressed" in llama3.1 run 25. Fix: gate on `if call_index == 1 or not generated_lever_names`. (`identify_potential_levers.py:297–306`)

**Continuing backlog (not yet resolved):**
- Review avg length for claude-haiku remains 2.9× baseline (warning threshold: 2×). Single-sentence constraint partially effective but insufficient to close gap.
- B2 (false `partial_recovery` for fast 1-call success) — low-priority observability fix, no output quality impact. (`runner.py:577–583`)
- S2 (options validator accepts > 3 despite "No more, no fewer" description) — cosmetic mismatch; intent documented in code comments. (`identify_potential_levers.py:121–157`)
- `LeverCleaned` field descriptions: mark as documentation-only to prevent copy-paste confusion. (`identify_potential_levers.py:206–220`)
