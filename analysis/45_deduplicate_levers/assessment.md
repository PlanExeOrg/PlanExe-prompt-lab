# Assessment: feat: consolidate deduplicate_levers — classification, safety valve, B3 fix

## Issue Resolution

**What the PR was supposed to fix** (from PR #365 `pr_title`/`pr_description`):
1. Gemini calibration-capping on sovereign_identity — the "4–8" hint caused premature stop at 5 absorbs, keeping 9 levers where 5 is correct.
2. Widen calibration range to "4–10" + add "do not stop early".
3. Add `primary`/`secondary` classification for downstream prioritization (replaces flat `keep`).
4. Complete the B3 fix: conditional `...` in `all_levers_summary` (PR #364 only fixed `_build_compact_history`).
5. Document 5th failure mode (calibration-capping) in `OPTIMIZE_INSTRUCTIONS`.
6. Broaden secondary examples; add self_improve runner support; enrich_potential_levers backwards-compat.

**Is the issue resolved in the after (runs 22–28) outputs?**

**Issue 1+2 (calibration-capping): CONFIRMED FIXED.** Gemini (run 27) absorbed exactly 4 levers from 18 diverse sovereign_identity inputs, landing at the lower bound of "4–10". The absorptions are semantically sound (Technical Standards → EU Standards Engagement; Procurement Conditionality → Procurement Language Specificity; Resilience Narrative → Risk Framing; EU Interoperability → EU Standards Engagement). The widened range + "do not stop early" continues to work with the new 18-lever input set, not just the 15-lever triplicate set from analysis/44.

Evidence: `history/3/27_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — 4 `absorb` entries, 7 `primary` + 7 `secondary` = 14 kept from 18 inputs.

**Issue 3 (primary/secondary classification): PARTIAL — new failure discovered.** All 7 models in runs 22–28 produce `primary`/`secondary` output (no model outputs the old flat `keep`). However, gpt-4o-mini (run 26) classified every lever as primary or secondary with zero absorbs — the `absorb` classification is being bypassed entirely. Secondary examples from haiku and gpt-oss-20b are qualitatively good (operational levers correctly marked secondary). llama3.1 makes cross-domain absorptions (procurement → certification targets) rather than not absorbing.

**Issue 4 (B3 fix): CONFIRMED.** Both `_build_compact_history` (line 103) and `all_levers_summary` (line 179) use the conditional `'...'` pattern. The fix holds with the larger 18-lever inputs where truncation risk is higher.

**Issue 5 (OPTIMIZE_INSTRUCTIONS): CONFIRMED.** Calibration-capping is documented as the 5th failure mode. Runs 22–28 surfaced a 6th failure mode (cross-domain absorption in llama3.1) not yet documented.

**Residual symptoms:**

The system prompt was essentially **identical** between runs 15–21 (analysis/44 batch) and runs 22–28 (analysis/45 batch) — per insight N6, both already contained `primary/secondary`, "4–10", "do not stop early", and the same secondary examples. The only detected difference is "team communication tooling" → "communication tooling". This means most of PR #365's value in these batches comes from **code-level changes** (B3 truncation fix, runner support, enrich backwards-compat), not prompt text.

The **input set changed** between analysis/44 and analysis/45 batches: 15 heavily triplicated levers → 18 semantically diverse levers per plan. This is a confound that inflates apparent quality degradation in the after batch and limits direct before/after comparison.

---

## Quality Comparison

Comparing before (runs 15–21, analysis/44 batch, 15-lever triplicate inputs) vs after (runs 22–28, analysis/45 batch, 18-lever diverse inputs). All 7 models appear in both batches. **Caution: input set changed between batches; metrics that depend on absorb count are not directly comparable.**

| Metric | Before (runs 15–21) | After (runs 22–28) | Verdict |
|--------|---------------------|--------------------|---------|
| **Success rate** | 100% (35/35) | 100% (35/35) | UNCHANGED |
| **LLMChatError count** | 0 | 0 | UNCHANGED |
| **Gemini absorbs / sovereign_identity** | 10/15 (67%) — fixed by PR #365 | 4/18 (22%) — within "4–10" range | STABLE ✅ |
| **Haiku absorbs / sovereign_identity** | 10/15 (67%) on triplicates | 6/18 (33%) on diverse | PROPORTIONALLY STABLE |
| **gpt-4o-mini absorbs / sovereign_identity** | 10/15 (67%) on trivial triplicates | 0/18 (0%) on diverse input | REGRESSED ❌ |
| **gpt-4o-mini kept / hong_kong** | 9 (improved from 12 in prior batch) | not checked separately | — |
| **Secondary usage (all models)** | 2–3/7 models used secondary | All 7 produce primary/secondary output; gpt-4o-mini blanket-classifies with 0 absorbs | MIXED |
| **Haiku justification quality** | Context-grounded, lever-ID-citing | Context-grounded, lever-ID-citing, correct hierarchy | MAINTAINED ✅ |
| **Hierarchy-direction violations** | Present (gemini, gpt-oss-20b, gpt-5-nano in analysis/44 context) | Present (llama3.1, gpt-5-nano, qwen3 — 3/7 models) | UNCHANGED ❌ |
| **Cross-domain absorptions** | Not observed | llama3.1: procurement → certification, demonstrators → fallback auth | NEW ISSUE ❌ |
| **Fabricated quantification** | Present (upstream, inherited) | Present (upstream, inherited) | UNCHANGED |
| **Bracket placeholder leakage** | Not observed | Not observed | UNCHANGED |
| **Option count violations** | Not observed | Not observed | UNCHANGED |
| **Field length vs baseline** | ~1.0× (verbatim pass-through) | ~1.0× (verbatim pass-through) | UNCHANGED |
| **Marketing-copy language** | Not observed | Not observed | UNCHANGED |
| **Review format compliance** | Controls X vs Y present (verbatim) | Controls X vs Y present (verbatim) | UNCHANGED |
| **Consequence chain format** | Inherited from upstream | Inherited from upstream | UNCHANGED |
| **Calibration hint accuracy** | "15 levers, expect 4–10" — matched input | "15 levers, expect 4–10" — 18-lever input, hint is stale | REGRESSED ❌ |
| **Self-referential absorb guard** | Absent | Absent | UNCHANGED ❌ |
| **Circular absorb detection** | Absent | Absent | UNCHANGED ❌ |
| **OPTIMIZE_INSTRUCTIONS failure modes** | 5 documented (analysis/44 added calibration-capping) | 5 documented; 6th (cross-domain) not yet added | INCOMPLETE |

**Notes on non-applicable metrics:**

- *Over-generation count*: With the hard cap removed and 18-lever inputs, most models keep 8–14 levers per plan. The DeduplicateLeversTask downstream handles the extras; this is informational only.
- *Cross-call duplication*: Not applicable to deduplicate_levers — it is a single sequential multi-turn conversation, not parallel calls.
- *Template leakage, bracket placeholders*: These are generated by `identify_potential_levers` (upstream). The deduplicate step passes `consequences`, `options`, and `review` verbatim.
- *Field length vs baseline*: Baseline (`baseline/train/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`) uses flat `keep`/`absorb` format. Content fields are inherited unchanged; ratio is ~1.0×, well below the 2× threshold.

**OPTIMIZE_INSTRUCTIONS alignment:**

The PR brought the codebase closer to OPTIMIZE_INSTRUCTIONS goals (calibration-capping documented as failure mode 5; secondary classification enables downstream prioritization; "do not stop early" prevents premature stopping). The analysis/45 batch reveals that the safety valve instruction "Use primary only as a last resort — if you genuinely cannot determine a lever's strategic role" **maps uncertainty → primary**, which is the opposite of intent. This is documented as a known problem in OPTIMIZE_INSTRUCTIONS' spirit but not yet as a named failure mode. It is the most likely root cause of gpt-4o-mini's 0-absorb failure on diverse inputs.

---

## New Issues

**B2 — Safety valve semantic inversion** (`deduplicate_levers.py:135`)

The instruction "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role" tells the model to use `primary` when confused. The code-level fallback at line 249 also defaults failed classifications to `primary`. Both reinforce the path: uncertainty → primary. For gpt-4o-mini, this means "when I am unsure about any lever, I will classify it primary rather than absorb it" — which explains the 0-absorb result on 18 diverse levers. This bug predates PR #365 (the wording was already in the pre-PR prompt per insight N6) but is now confirmed as the root cause of a significant quality failure.

Evidence: `history/3/26_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — all 18 levers in `deduplicated_levers`, 0 absorbs in `response`. Every lever is classified primary or secondary with a justification that argues each is "distinct and essential."

**N1 — gpt-4o-mini blanket-primary/secondary failure on diverse inputs**

Zero absorbs from 18 diverse sovereign_identity levers. The model correctly identifies overlap (Procurement Language Specificity vs Procurement Conditionality, EU Standards vs Technical Standards Advocacy, Risk Framing vs Resilience Narrative) when asked to summarize, but classifies each as `primary` or `secondary` rather than absorbing overlapping pairs. This is the #1 documented failure mode in OPTIMIZE_INSTRUCTIONS ("blanket-primary / over-inclusion"). The calibration hint ("expect 4–10") and the "reconsider if zero absorbs" instruction are both being ignored.

**N2 — llama3.1 cross-domain absorptions**

llama3.1 (run 22) absorbs levers into semantically unrelated targets:
- Demonstrator Fidelity → absorbed into Fallback Authentication Modality (demonstrators ≠ fallback auth)
- Technical Standards Advocacy → absorbed into Fallback Authentication Modality (EU policy ≠ technical fallback)
- Procurement Conditionality → absorbed into Fallback Certification Criteria (procurement ≠ certification)

This is a distinct failure mode from the hierarchy-direction violations (general→specific) seen in gpt-5-nano and qwen3. Cross-domain absorption is not documented in OPTIMIZE_INSTRUCTIONS.

Evidence: `history/3/22_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`, absorb justifications for 548c0a83, 089c8ec8, ed16c55c.

**B3 (code_claude/45) — Calibration hint references 15 levers; current inputs have 18**

`deduplicate_levers.py:137` reads "In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed." Runs 22–28 feed 18 levers. The upper bound of 10 absorbs = 56% of 18, which gpt-5-nano already hits (10 absorbs). Models that interpret the bound as a cap will stop before processing all genuine duplicates. The stale example ("15 levers") also undermines the calibration hint's authority for models that notice the discrepancy.

**N5 — Input set changed between analysis/44 and analysis/45 batches (confound)**

Runs 15–21 (analysis/44 "before") used 15-lever triplicate inputs (5 unique strategies × 3 near-identical copies). Runs 22–28 (analysis/45 "after") use 18-lever semantically diverse inputs. Absorb counts from the two batches measure different things. Any apparent regression in absorb rate partly reflects harder input, not a prompt/code regression. Future iterations should hold the input set constant across before/after batches.

**I4 (code_claude/45) — `deduplication_justification` field not backwards-compatible in enrich_potential_levers**

`enrich_potential_levers.InputLever.deduplication_justification: str` has no default. Calling enrich with levers that bypass the deduplicate step will raise a `ValidationError`. PR #365 claims backwards-compatibility but only made `classification` optional; `deduplication_justification` remains required.

---

## Verdict

**YES**: PR #365 remains a keeper across both analysis batches. Gemini's calibration fix holds with 18-lever diverse inputs (4 absorbs within range), the B3 truncation fix is confirmed, and the secondary classification feature is structurally functional across all 7 models. The gpt-4o-mini blanket-primary failure (0 absorbs) is caused by the pre-existing B2 safety valve semantic inversion — a bug in the prompt wording that predates PR #365 and is not introduced by it. The cross-domain absorption in llama3.1 (N2) is newly observed with the more diverse input set but is also not a PR #365 regression. Net: the PR's benefits (Gemini fix, B3 correctness, runner support, enrich backwards-compat for `classification`) outweigh the residual issues it leaves unaddressed.

---

## Recommended Next Change

**Proposal**: Fix the safety valve semantic inversion — rewrite the "Use primary only as a last resort" sentence in `DEDUPLICATE_SYSTEM_PROMPT` (`deduplicate_levers.py:135`) and change the code-level fallback at line 249 from `LeverClassification.primary` to `LeverClassification.secondary`.

**Evidence**: The synthesis/45 cites code_claude/45 B2 as the confirmed root cause. The current wording "Use 'primary' only as a last resort — if you genuinely cannot determine a lever's strategic role" maps uncertainty → primary. The code fallback at line 249 independently makes the same choice. Both reinforce: confused model → primary, enabling blanket-primary failure without constraint. gpt-4o-mini's 0-absorb result on 18 diverse levers is the most impactful consequence: the deduplication step provides zero value for this widely-used model on non-trivial inputs. The synthesis/45 Direction 1 (fix B2) also has a clear falsifiable test: "the next iteration should show gpt-4o-mini producing ≥4 absorbs from 18 diverse inputs."

Specific fix (from synthesis/45):
- Replace line 135: `"Use 'primary' only as a last resort..."` → `"Only assign 'primary' for levers you have actively confirmed are essential strategic decisions. If genuinely uncertain whether a lever is primary vs. secondary, assign 'secondary' — do not default to primary out of caution."`
- Replace line 249: `classification=LeverClassification.primary` → `classification=LeverClassification.secondary`

**Verify in the next iteration**:
- gpt-4o-mini sovereign_identity absorb count should increase from 0 to ≥4 on 18-lever diverse inputs. Confirm by reading `history/3/XX_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` for the gpt-4o-mini run — count `"classification": "absorb"` entries.
- Haiku and gemini lever counts should not regress — both currently assign primary correctly and should be unaffected by narrowing the uncertain-fallback to secondary. Monitor haiku sovereign_identity (currently 7P/5S/6A = 12 kept) and gemini (currently 7P/7S/4A = 14 kept) to confirm they are stable.
- gpt-oss-20b and qwen3 secondary adoption should be checked — the change from "primary as last resort" to "secondary when uncertain" may push them toward more secondary usage. Verify the secondary levers they produce are operationally meaningful, not just moved from primary.
- If gpt-4o-mini still produces 0 absorbs after the B2 fix, add the worked absorb example (synthesis/45 Direction 2). The example should be domain-general, not sovereign_identity-specific.
- After B2 fix is validated, implement the circular/self-referential absorb guard (synthesis/44 Direction 1) as the next code fix — it is still unaddressed.

**Risks**:
- Models that currently assign primary correctly (haiku, gemini) should not be affected, since the change only constrains the uncertain case. But very conservative models may over-use secondary (too many levers demoted). This is recoverable and less harmful than zero absorbs.
- The code fallback change (line 249 → secondary) affects LLMs that fail structured output entirely. After the change, a failed lever will be kept as secondary rather than primary. This is more correct semantically but changes the downstream behavior of `vital_few_levers` for any fallback-classified levers.
- Bundling B2 prompt fix + B3 calibration hint update (stale "15 levers" → "15–20 levers") in the same PR is low-risk; bundle them to avoid a separate iteration for the minor calibration text fix.
- Do NOT bundle B2 with the circular absorb guard (synthesis/44 Direction 1) — keep code fix and prompt change in separate PRs to isolate regression sources.

**Prerequisite issues**: None. B2 is a standalone prompt + 1-line code change. No schema changes, no structural changes. The enrich_potential_levers backwards-compat gap (I4) is trivial (`= ""` default) and should be fixed in the same PR as a low-risk cleanup.

---

## Backlog

**Resolved by analysis/44 and analysis/45 — can close:**
- Gemini calibration-capping: FIXED in PR #365, confirmed across both analysis batches.
- B3 `all_levers_summary` unconditional `...`: FIXED in PR #365 (confirmed analysis/44).
- OPTIMIZE_INSTRUCTIONS 4th → 5th failure mode (calibration-capping): ADDED in PR #365.

**Carried from analysis/44 backlog — still open:**
- **Circular absorb drops both levers** (`deduplicate_levers.py:258–281`): Confirmed root cause of Qwen sovereign_identity 5→3 collapse in analysis/44. Still unguarded. Implement after B2 fix is validated.
- **Self-referential absorb silently drops lever** (same location): Observed in gpt-5-nano run 17 (lever `f1c0d856`). Still unguarded.
- **`calls_succeeded` semantic mismatch in `_run_deduplicate`** (`runner.py:155`): Counts 15 lever decisions instead of 1 LLM conversation. Latent. Bundle with next runner.py change.
- **Hierarchy-direction violations** (general lever absorbed into specific, wrong instance kept): Persists in 3/7 models (llama3.1, gpt-5-nano, qwen3). No prompt example or code tie-breaker exists. Synthesis/44 Direction 3 (position-based hierarchy-aware selection) is still the proposed fix.
- **Secondary examples domain-narrow**: "marketing campaign timing, internal reporting cadence, communication tooling" examples don't translate to civic/policy plans. Models like llama3.1 and gemini ignore secondary on sovereign_identity partly because no example resembles those plan's levers.
- **Numeric calibration range unstable mechanism**: Three revisions across three PRs. Synthesis/44 Direction 2 proposed replacing with qualitative-only guidance. Deferred until absorb guard and B2 fix are in place.
- **Upstream fabricated quantification**: "15% increased policy traction", "20% greater likelihood" etc. in `consequences` fields inherited from `identify_potential_levers`. Not fixable in deduplicate step — needs separate iteration on upstream step.
- **`user_prompt` stores levers JSON not project_context** (`deduplicate_levers.py:295`): Naming inconsistency that confuses analysis scripts. Low priority.

**New in analysis/45 — add to backlog:**
- **B2 safety valve semantic inversion** (`deduplicate_levers.py:135`, line 249): **Top priority next change.** Confirmed root cause of gpt-4o-mini 0-absorb failure. Requires prompt rewrite + 1-line code fix.
- **Cross-domain absorption (6th OPTIMIZE_INSTRUCTIONS failure mode)**: llama3.1 absorbs procurement levers into technical certification targets and demonstrator levers into fallback auth targets. Not yet documented. Add to OPTIMIZE_INSTRUCTIONS after confirming pattern persists with new prompt.
- **Calibration hint references 15 levers; inputs have 18** (`deduplicate_levers.py:137`): Stale example may anchor model ceilings incorrectly. Bundle with B2 fix: update to "15–20 levers, expect 4–10 (or more on highly similar inputs)".
- **`deduplication_justification` not backwards-compatible in enrich** (`enrich_potential_levers.py:40`): Missing `= ""` default breaks pipelines that bypass deduplicate step. Trivial fix; bundle with B2 PR.
- **Input set confound in experimental design**: Before (analysis/44) and after (analysis/45) batches used different input lever sets (15 triplicates vs 18 diverse). Future iterations should hold the input set constant across evaluation batches to cleanly isolate prompt/code effects.
- **S1 (structured `absorb_target_id` field)**: Absorb target lives in freeform justification text; the code cannot validate it. Required for chain-absorption detection and hierarchy-aware tie-breaking. Medium-effort schema change; defer until prompt fixes are stable.
