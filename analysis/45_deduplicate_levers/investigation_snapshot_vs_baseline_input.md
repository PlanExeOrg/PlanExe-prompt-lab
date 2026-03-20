# Investigation: Snapshot (diverse) vs Baseline (triplicated) input quality

## Question

Iteration 45 used snapshot input (18 semantically diverse levers from the
improved `identify_potential_levers` prompt) instead of baseline/train (15
triplicated levers = 5 unique x 3 near-identical copies). Does the snapshot
input produce higher-quality deduplication testing?

## Input structure

**Baseline/train (iter 44):** 15 levers with 5 unique concepts, each repeated
3 times with different UUIDs but near-identical content. Names are literally
repeated: "Technical Feasibility Strategy", "Policy Advocacy Strategy", etc.
Minor phrasing and percentage variations between copies.

**Snapshot (iter 45):** 18 levers, all with distinct names: Procurement
Language Specificity, Demonstrator Fidelity, Coalition Breadth, EU Standards
Engagement, Fallback Authentication Modality, Risk Framing, Technical Standards
Advocacy, Procurement Conditionality, etc. Semantic overlap exists between
pairs (e.g., Procurement Conditionality vs Procurement Language Specificity)
but requires genuine reasoning to detect.

## Sovereign identity comparison

| Model | Iter 44 (15 triplicates) | Iter 45 (18 diverse) |
|-------|--------------------------|----------------------|
| Haiku | 5 kept, 10 absorbed (perfect) | 12 kept, 6 absorbed (all semantically correct) |
| Gemini | 5 kept, 10 absorbed (hierarchy flip) | 14 kept, 4 absorbed (all correct direction) |
| Llama3.1 | 5 kept, 10 absorbed (perfect) | 14 kept, 4 absorbed (1-2 questionable targets) |
| GPT-4o-mini | 5 kept, 10 absorbed (perfect) | 18 kept, 0 absorbed (total failure) |

## Analysis

### The triplicated input is a trivially easy test

All 4 models achieve perfect 10/15 absorption on the triplicated input. This
is expected: detecting that "Technical Feasibility Strategy" appears 3 times
requires only name matching, not semantic reasoning. The triplicated input
flatters weak models by making the task trivially solvable.

### The diverse input reveals real capability differences

On 18 diverse levers, the models separate into tiers:

1. **Haiku** (6 absorbs, 12 kept): Best performer. All absorptions semantically
   correct. Justifications are the richest, incorporating project context rather
   than boilerplate. One minor hierarchy reversal (Risk Framing into Resilience
   Narrative Amplification instead of the reverse).

2. **Gemini** (4 absorbs, 14 kept): All absorptions directionally correct.
   Technical Standards Advocacy and EU Interoperability Advocacy both correctly
   absorbed into EU Standards Engagement. Clean reasoning.

3. **Llama3.1** (4 absorbs, 14 kept): Questionable "catch-all bucket" pattern.
   Absorbed 3 of 4 targets into a single lever (Fallback Authentication
   Modality), including Technical Standards Advocacy which is about EU policy
   influence, not authentication. Suggests a "biggest related concept" heuristic
   rather than careful semantic pairing.

4. **GPT-4o-mini** (0 absorbs, 18 kept): Complete deduplication failure. The
   model correctly identifies overlap in summaries but classifies every lever
   as primary or secondary rather than absorbing overlapping pairs. Relies on
   lexical name matching rather than semantic content analysis.

### GPT-4o-mini failure root cause

The assessment traces this to the safety valve semantic inversion at
`deduplicate_levers.py:135`: "Use 'primary' only as a last resort -- if you
genuinely cannot determine a lever's strategic role." This maps uncertainty to
primary, giving the model an escape route from absorbing. The code fallback at
line 249 (defaulting to `LeverClassification.primary`) reinforces the same
path. On triplicated input, the overlap is so obvious the escape route is
unnecessary; on diverse input, any ambiguity triggers it.

### No degenerate patterns on diverse input

The circular absorbs (Qwen 80b177d0<->737c7c14) and self-referential absorbs
(gpt-5-nano f1c0d856) observed in iter 44 did not appear in iter 45. These
patterns were specific to the triplicated input where multiple copies of the
same concept created confusion about which instance to absorb into.

## Conclusion

The snapshot-based diverse input is a significantly better test of
deduplication quality than the triplicated baseline input. It:

- Exposes real semantic reasoning capability differences between models
- Eliminates the false confidence from trivial name-matching dedup
- Reveals the GPT-4o-mini safety valve failure that was invisible on easy input
- Eliminates degenerate circular/self-referential absorb patterns that were
  artifacts of the triplicated structure

Future self_improve iterations for `deduplicate_levers` should use snapshot
input (or equivalent diverse levers) rather than the triplicated baseline. The
triplicated input provides no useful signal about prompt quality -- all models
ace it regardless of prompt changes.
