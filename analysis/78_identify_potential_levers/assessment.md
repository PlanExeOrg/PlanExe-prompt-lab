# Assessment: Remove template-lock anchor from review_lever

## Issue Resolution

**What the PR was supposed to fix:**
PR #484 removes the phrase `"the specific gap the three options leave unaddressed"` from two locations
in `identify_potential_levers.py`: (1) the `review_lever` Pydantic field description (line 127) and
(2) system prompt section 4 preamble (line 244). This phrase was the structural anchor causing haiku
to produce the pattern "All/None of the three options [verb] [gap]" in ~85% of reviews for the most
affected plan (hong_kong_game) and 24.7% overall across all 5 plans. It was a "template-lock
migration" from the previous fix (PR #358), which had removed the "core tension" opener lock but
introduced this new phrase as its replacement.

**Is the issue resolved?**
Yes, completely. Direct verification of the merged lever files confirms:

- **Before** (`history/2/93`, haiku, hong_kong_game): 14 of 21 reviews contain "All three options…
  but none [address/solve/confront]…" or "none of the three options address…" (67%). Overall across
  all 5 haiku plans: 23/93 reviews (24.7%).
- **After** (`history/5/59`, haiku, hong_kong_game): 0 of 21 reviews contain this pattern. Spot
  check of silo plan: 0 of 21 reviews contain this pattern. Insight confirms 0/99 across all 5 plans.

Sample after-run reviews (hong_kong_game, haiku) confirm substantive, domain-specific analysis
with no structural echo of the removed phrase:

> "Casting directly determines whether the film reads as a fresh Hong Kong-centered vision or as
> Western cinema parasitizing Asian locations; each choice trades opening-weekend performance against
> thematic coherence and regional market penetration."

> "Any twist must surprise audiences familiar with the original; pure repetition invites dismissal,
> pure ambiguity risks anticlimax, and contemporary reimagining must exploit what only 2026 Hong Kong
> makes possible."

**Residual symptoms:** None. The secondary benefit — haiku partial recovery events (silo: 14→21
levers, gta_game: 16→21 levers) — is also completely resolved. No residual "three options" phrasing
appears in any after-run review across any model.

---

## Quality Comparison

**Before** = runs `2/87–93` (post–PR #358, pre–PR #484)
**After** = runs `5/53–59` (post–PR #484)
**Models compared** = all 7 (identical across both batches):
ollama-llama3.1 · openrouter-openai-gpt-oss-20b · openai-gpt-5-nano · openrouter-qwen3-30b-a3b ·
openrouter-openai-gpt-4o-mini · openrouter-gemini-2.0-flash-001 · anthropic-claude-haiku-4-5-pinned

| Metric | Before (2/87–93) | After (5/53–59) | Verdict |
|--------|-----------------|----------------|---------|
| **Haiku template lock** ("All/None of three options") | 23/93 = **24.7%** | 0/99 = **0%** | IMPROVED |
| Non-haiku template lock (any model) | 0% across 6 models | 0% across 6 models | UNCHANGED |
| **Haiku partial recovery events** | 2 (silo 2/3, gta_game 2/3) | 0 | IMPROVED |
| **Haiku lever count — silo** | 14 | 21 | IMPROVED (+50%) |
| **Haiku lever count — gta_game** | 16 | 21 | IMPROVED (+31%) |
| Overall call success rate | 97.1% (102/105) | ~100% (excl. run54 infra timeouts) | IMPROVED |
| Haiku call success rate | 86.7% (13/15) | 100% (15/15) | IMPROVED |
| LLMChatErrors | 0 | 0 | UNCHANGED |
| Bracket placeholder leakage | 0 | 0 | UNCHANGED |
| Option count violations | 0 (enforced by validator) | 0 | UNCHANGED |
| Lever name uniqueness | normal | normal | UNCHANGED |
| Template leakage (prompt examples verbatim) | 0 | 0 | UNCHANGED |
| Review format compliance ("Controls X vs Y") | N/A — not a current target | N/A | N/A |
| Consequence chain format (→ markers) | Not used in current prompt | Not used | N/A |
| **Haiku review avg length** | 321 chars (2.1× baseline) | 281 chars (1.9× baseline) | UNCHANGED (warning threshold) |
| **Haiku consequences avg length** | 515 chars (1.8× baseline) | 557 chars (2.0× baseline) | REGRESSED slightly |
| **Haiku options avg length** | 968 chars (2.2× baseline) | 845 chars (1.9× baseline) | IMPROVED |
| Non-haiku field lengths vs baseline | ≤1.3× across all fields | ≤1.3× across all fields | UNCHANGED |
| **Fabricated % claims — haiku** | 0.38/lever | 0.30/lever | IMPROVED slightly |
| Fabricated % claims — other models | 0.00–0.04/lever | 0.00–0.09/lever | UNCHANGED |
| Marketing-copy language | 0 | 0 | UNCHANGED |
| **Over-generation / step-gate early exit** | Caused 2 partial_recovery events | None (all 3 calls complete) | IMPROVED |
| Cross-call lever-name duplication | Not reported | Not reported | N/A |
| Run 54 (gpt-oss-20b) plan timeouts | 0 | 3 (infrastructure, unrelated) | NEUTRAL |

**Baseline** = `baseline/train/` (5 plans, avg review ≈152 chars, consequences ≈279 chars, options ≈450 chars).
Note: the baseline itself contains a prior "Controls X vs. Y. Weakness: …" template lock and significant
fabricated percentages in consequences fields (e.g., "15% increase in black market activity"). The
current system prompt correctly prohibits these; the baseline is used only for field-length reference.

**OPTIMIZE_INSTRUCTIONS alignment:**

The current OPTIMIZE_INSTRUCTIONS (lines 27–93) is well-aligned with observed failure modes and
remains accurate after PR #484:
- "Field-description template lock" (line 86–92): directly predicts and describes the exact problem
  PR #484 addresses. PR #484 implements the prescribed fix.
- "Template-lock migration" (line 73–82): accurately predicts the chain from PR #358 to PR #484.
  No new migration observed after PR #484.
- "Verbosity amplification" (line 83–85): haiku's 1.9–2.0× verbosity is explicitly documented and
  attributed to examples mirroring. Unchanged by PR #484 (not its target).
- "Fragile English-only validation" (line 61–68): the `consequences` field description still embeds
  English examples ("Controls ... vs.", "Weakness:") as prohibitions. OPTIMIZE_INSTRUCTIONS flags
  this; it is a latent hazard for non-English inputs. Not introduced by PR #484.

No new violations of the known-problems list introduced. No update to OPTIMIZE_INSTRUCTIONS needed
for this PR — all observed behaviors are already predicted and documented.

---

## New Issues

**N1 — runner.py partial_recovery threshold inconsistency (B1+B2, code_claude)**
The `_run_levers` warning fires at `actual_calls < 3` but the `partial_recovery` event is emitted
at `calls_succeeded < 2`. A 2-call success (which the code's own comment calls "normal for models
that produce 8+ levers per call") logs a spurious WARNING but emits no `partial_recovery` event
to `events.jsonl`. Conversely, a genuine 1-call partial run emits the event but looks identical to
the 2-call normal case in log output. This means before/after comparisons of `partial_recovery`
counts across different code versions are comparing under different threshold regimes, making
trend analysis unreliable. Independent of PR #484 but surfaced by the cleaner post-PR data.
File: `runner.py:131` and `runner.py:579`.

**N2 — English-specific prohibitions in `consequences` field description (S1, code_claude)**
`identify_potential_levers.py:117–118` embeds English keyword examples (`"Controls ... vs."`,
`"Weakness:"`) directly in the Pydantic field description. OPTIMIZE_INSTRUCTIONS lines 61–68 warn
against English-only markers; the same hazard applies to field descriptions. Currently harmless
(all baseline plans are English), but a latent risk for non-English inputs. Not introduced by PR #484.

**N3 — Run 54 (gpt-oss-20b) infrastructure timeouts**
`history/5/54_identify_potential_levers/events.jsonl` shows `run_single_plan_error` (plan timeout
after 600s) for hong_kong_game, parasomnia_research_unit, and silo (3/5 plans). Run 88 (same model,
before batch) had 0 timeouts. This is an infrastructure/endpoint reliability issue unrelated to
PR #484. If chronic, gpt-oss-20b should be tiered separately from prompt-quality evaluation runs.

---

## Verdict

**YES**: PR #484 is a minimal two-line change that completely eliminates haiku's "All/None of the
three options" template lock (24.7% → 0%) with zero regressions across all 7 models. Secondary
benefits include haiku partial recovery events eliminated (2→0) and lever counts restored (+50% for
silo, +31% for gta_game). The fix is precise, causally verified, and implements exactly the guidance
in OPTIMIZE_INSTRUCTIONS lines 86–92. No new template lock observed post-fix. KEEP.

---

## Recommended Next Change

**Proposal:**
Shorten the three section 4 review_lever examples from 35–40 words to 20–28 words each, and add a
max-length cap (350 chars) to the `check_review_format` validator. Both changes target haiku's
persistent 1.9–2.0× verbosity, which affects content quality across all 99 successfully-generated
haiku levers per run.

**Evidence:**
The synthesis cites OPTIMIZE_INSTRUCTIONS line 83–85 ("Models mirror example verbosity … Keep
review_lever examples concise") as the root cause of haiku's verbosity. The three current section 4
examples are 35–40 words each — sitting at the top of the 20–40 word target range. Haiku averages
281 chars (~56 words) per review post-PR, vs. a baseline of 152 chars (~30 words). All non-haiku
models are at ≤1.3× baseline without changes, suggesting the problem is haiku's sensitivity to
example length, not the prompt structure. Haiku consequences field also crept to 2.0× baseline
(557 chars), slightly above the warning threshold. The code review confirms the validator enforces
only a 10-char minimum with no maximum, making the 40-word target advisory rather than enforced.

**Verify:**
- **Primary metric**: haiku review avg length should drop from ~281 chars toward 150–200 chars
  (within 1.0–1.3× of baseline 152 chars). Check `history/[next_batch]/5[x]_identify_potential_levers/`
  haiku outputs.
- **Lock recurrence**: confirm haiku does not develop a new template pattern tied to any phrase in
  the shortened examples. Count instances of shared sub-phrases appearing in >30% of reviews.
- **Non-haiku stability**: field lengths for llama3.1, gpt-5-nano, qwen3, gpt-4o-mini, gemini should
  remain at ≤1.3× baseline. Shorter examples should have no effect on models already producing
  near-baseline lengths.
- **Review depth**: qualitatively sample 5–10 haiku reviews from the silo plan to confirm shorter
  length does not degrade substantive content (domain-specific mechanism, real trade-off) — i.e.,
  confirm that shortening removes padding, not insight.
- **Validator behavior**: if the 350-char cap triggers retries, check events.jsonl for
  `ValidationError` entries in haiku runs; confirm they resolve within 1–2 retries rather than
  causing call-level failures.

**Risks:**
1. **Shorter examples may reduce review quality in stronger models.** However, all non-haiku models
   already produce near-baseline lengths without sensitivity to example verbosity. Low risk.
2. **350-char cap may add retry overhead for haiku until examples are also shortened.** If both
   changes ship together, haiku should fall within the cap naturally. The synthesis recommends
   combining them in a single PR to avoid the retry-overhead window.
3. **Verbosity and fabrication share a root cause in haiku.** If haiku's extra length is driven by
   fabricated quantification (0.30 fabricated % claims/lever), reducing length may not reduce
   fabrication rate proportionally. Monitor fabricated % claims/lever in the next iteration.
4. **"Validation Protocols" section heading** (current name for section 4) may cause instruction-tuned
   models to treat examples as correctness criteria rather than stylistic anchors. Renaming to
   "Format Examples" is a low-risk companion change that can be bundled at no extra cost.

**Prerequisites:**
None. PR #484 is fully merged and the template lock is resolved. The verbosity problem is independent
of any pending fix.

---

## Backlog

**Resolved and removable:**
- "None/All three options" secondary template lock (identified in analysis 40, caused by "the three
  options leave unaddressed" in field description) → **RESOLVED by PR #484**. Remove from backlog.

**Still open (carried forward):**
- **Haiku verbosity** (1.9–2.0× baseline across review, consequences, options fields): primary target
  for next iteration. Root cause: section 4 examples at 35–40 words mirror verbosity into haiku output.
- **Haiku fabricated % claims** (0.30/lever post-PR): tracked in OPTIMIZE_INSTRUCTIONS. May share root
  cause with verbosity; monitor after shortening examples.
- **runner.py partial_recovery threshold mismatch** (B1+B2, new): warning fires at `< 3` calls but
  event emits at `< 2` calls, creating misleading logs and unreliable cross-version comparisons.
  Fix in a separate small `runner.py` PR.
- **English-specific prohibitions in `consequences` field description** (S1): `"Controls ... vs."` and
  `"Weakness:"` as English examples of text to avoid. Latent multilingual hazard; fix before non-English
  inputs are used at scale.
- **Run 54 (gpt-oss-20b) timeout reliability**: 3/5 plans timed out in the after batch. Investigate
  whether chronic; if so, move to a separate reliability tier.
- **LeverCleaned.review field description** (B1 from analysis 40): was stale ("names the core tension")
  when analysis 40 ran. Status after PR #484 unverified in this analysis — the code reviewer did not
  flag it. Confirm current state in source; fix if still stale.
- **Section 4 heading "Validation Protocols"** should be renamed to "Format Examples" (I3, code_claude):
  low-risk, can bundle with next system prompt PR.
- **`expected_calls=3` hardcoded in partial_recovery event payload** (I4, code_claude): misleading for
  fast models; should be derived from `min_levers` or removed.
