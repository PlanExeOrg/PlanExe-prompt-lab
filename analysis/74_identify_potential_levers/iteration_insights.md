# Iteration Insights: identify_potential_levers (analyses 69–74)

Six iterations attempted to beat the current best (analysis 40, PR #358). None were convincingly better. Here's what we learned.

## What worked (keep in next attempt)

- **Positive framing** over negative prohibitions. Replacing `"Do NOT include 'Controls ... vs.', 'Weakness:'"` with `"Save critical assessments for the review_lever field"` is safe — no regressions, follows OPTIMIZE_INSTRUCTIONS. The banned pattern was already absent in baseline, so this is defensive hygiene.

- **Verbatim-numbers constraint on consequences**. `"Use numbers only when the project context provides them directly — do not calculate, derive, or estimate figures"` eliminated fabricated % claims from consequences (haiku: 20→0 in #478). Must also be applied to options field.

- **Consistent length targets**. Aligning field descriptions and system prompt to the same "2–3 sentences" / "one sentence (20–40 words)" prevents models from picking the looser source. PR #475 missed updating the system prompt, causing haiku to follow the old "2–4" target.

- **XML tags for structural identifiers** (from enrich step). The `<lever>uuid</lever>` pattern prevents models from copying identifiers into free-text fields. Could potentially be applied to other structural elements.

## What failed (avoid)

- **Negative prohibitions naming specific patterns**. `"Do NOT include 'Controls ... vs.'"` and `"Never invent percentages"` both trigger the pattern they're trying to suppress in small models. This is documented in OPTIMIZE_INSTRUCTIONS lines 80–83 and confirmed across both the enrich and identify steps.

- **Abstract number prohibitions**. `"NO fabricated statistics or percentages without evidence"` (#475) made fabrication 4x worse. `"NO calculated, derived, or estimated figures"` (#479) introduced 5 new fabricated % values in gpt-oss-20b. Models interpret these as attention signals for numbers rather than suppressors.

- **Replacing one copyable phrase with another** in review_lever. Every structural phrase becomes a template:
  - Original: `"the specific gap the three options leave unaddressed"` → 85% haiku lock
  - PR #479: `"the proposed options collectively do not resolve"` → qwen3-30b gained 7/20 new lock, gpt-oss-20b increased to 15/17
  - Any sentence-structural instruction in a Pydantic field description gets treated as a fill-in-the-blank template by small models.

- **Banning all numbers** (#477). Too restrictive — lost useful plan-provided data. ChatGPT's assessment: "if your goal is letting the model reuse plan-provided numbers when helpful, current_best is better."

## The core unsolved problem: review_lever template lock

The #1 issue from analysis 40 remains unsolved after 6 attempts. The mechanism:

1. Pydantic field description contains a structural phrase (e.g., "the gap the three options leave unaddressed")
2. Models (especially haiku, gpt-oss-20b) copy the phrase structure verbatim into their output
3. Replacing the phrase with a different structural phrase just migrates the lock

### Approaches NOT yet tried

- **Remove the review_lever field description entirely** (use only system prompt section 4 examples). The examples in section 4 are diverse and domain-specific — they show the desired style without a copyable template. The field description could be minimal: `"Critical review of this lever."` (which is what `LeverCleaned.review` already uses, and it doesn't lock).

- **Use only examples, no instruction**. The section 4 examples are already good — they demonstrate trade-off identification without a formulaic opener. Making the field description purely declarative ("A one-sentence critical assessment") and letting the examples do the teaching might break the lock.

- **Counter-examples** (BAD/GOOD pairs). Instead of describing what to write, show a BAD example with the locked pattern and a GOOD example with varied phrasing. This works in few-shot learning but risks the BAD example being copied.

- **Rotate field descriptions per call**. The adaptive loop makes 3 calls per plan. Using different field description wording for each call would prevent lock accumulation across calls. Complex but would definitively prove whether it's the wording or the structure causing the lock.

## The secondary unsolved problem: fabricated numbers in options

The verbatim-numbers constraint works on consequences but was never applied to options (#478). The options field has no number constraint at all in the baseline. Adding `"Use numbers only when the project context provides them directly"` to the options field description should close this gap — it's a proven constraint that just needs wider application.

## Recommended next attempt

**Minimal change, maximum signal**: Only change the review_lever field description to `"Critical review of this lever (one sentence, 20–40 words)."` — drop all structural phrases, rely entirely on section 4 examples for style guidance. Keep everything else from the baseline (PR #358). This isolates the template-lock variable.

If that works, layer in the verbatim-numbers constraint on consequences and options as a separate PR.

## Session summary

| Analysis | PR | Key change | Verdict | Why not merged |
|----------|-----|-----------|---------|----------------|
| 69 | #471 | Positive framing only | YES | gpt-oss-20b all 5 plans timed out (infrastructure) |
| 70 | #473 | + reduced word counts | CONDITIONAL | System prompt inconsistency, haiku verbosity +13% |
| 71 | #475 | + "Never invent" constraint | CONDITIONAL | Fabricated numbers 4x worse |
| 72 | #477 | + ban all numbers | CONDITIONAL | Too restrictive, not convincingly better |
| 73 | #478 | + verbatim-numbers (consequences only) | CONDITIONAL | Missing from options field |
| 74 | #479 | + template-lock fix + verbatim everywhere | CONDITIONAL | New lock in qwen3-30b, gpt-oss-20b fabrication |
