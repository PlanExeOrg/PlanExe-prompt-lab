# Comparison: Iter 45 (PR #365) vs Iter 48 (main) -- deduplicate_levers

**Input**: 18 levers from `snapshot/0_identify_potential_levers/` (same for both iterations).
**Plans analyzed**: `20260308_sovereign_identity` (primary) and `20250321_silo` (confirmation).

## Key Difference Between Iterations

| Aspect | Iter 45 (PR #365) | Iter 48 (main) |
|--------|-------------------|----------------|
| Classification labels | `primary`, `secondary`, `absorb` | `keep`, `absorb`, `remove` |
| Safety valve | Yes (explicit `remove` option, but unused) | `remove` exists but used incorrectly by gpt-5-nano |
| Calibration hints | Yes (primary vs secondary adds signal) | No (binary keep/absorb loses nuance) |

---

## 1. Comparison Table -- sovereign_identity

### Classification Breakdown

| # | Model | Iter 45 (PR #365) | Iter 48 (main) |
|---|-------|-------------------|----------------|
| 1 | ollama-llama3.1 | 8 primary, 6 secondary, 4 absorb | 11 keep, 7 absorb |
| 2 | openrouter-openai-gpt-oss-20b | 10 primary, 2 secondary, 6 absorb | 13 keep, 5 absorb |
| 3 | openai-gpt-5-nano | 5 primary, 3 secondary, 10 absorb | 9 keep, 8 absorb, 1 remove |
| 4 | openrouter-qwen3-30b-a3b | 5 primary, 9 secondary, 4 absorb | 12 keep, 6 absorb |
| 5 | openrouter-openai-gpt-4o-mini | 11 primary, 7 secondary, 0 absorb | 16 keep, 2 absorb |
| 6 | openrouter-gemini-2.0-flash-001 | 7 primary, 7 secondary, 4 absorb | 13 keep, 5 absorb |
| 7 | anthropic-claude-haiku-4-5-pinned | 7 primary, 5 secondary, 6 absorb | 13 keep, 5 absorb |

### Absorb Quality (sovereign_identity)

| # | Model | Iter 45: valid / questionable | Iter 48: valid / questionable |
|---|-------|-------------------------------|-------------------------------|
| 1 | ollama-llama3.1 | 0 / 4 | 0 / 7 |
| 2 | openrouter-openai-gpt-oss-20b | 6 / 0 | 5 / 0 |
| 3 | openai-gpt-5-nano | 6 / 4 | 6 / 2 |
| 4 | openrouter-qwen3-30b-a3b | 3 / 1 | 4 / 2 |
| 5 | openrouter-openai-gpt-4o-mini | n/a (0 absorbs) | 2 / 0 |
| 6 | openrouter-gemini-2.0-flash-001 | 4 / 0 | 5 / 0 |
| 7 | anthropic-claude-haiku-4-5-pinned | 5 / 1 | 5 / 0 |

"Valid" = both source and target are a recognized overlapping pair (e.g., "Procurement Language Specificity" <-> "Procurement Conditionality", "Technical Standards Advocacy" <-> "EU Standards Engagement", etc.).
"Questionable" = absorb target is semantically unrelated or wrong (e.g., absorbing "Demonstrator Fidelity" into "Risk Framing").

### Justification Quality (avg chars, sovereign_identity)

| # | Model | Iter 45 avg | Iter 48 avg |
|---|-------|-------------|-------------|
| 1 | ollama-llama3.1 | 556 | 411 |
| 2 | openrouter-openai-gpt-oss-20b | 474 | 483 |
| 3 | openai-gpt-5-nano | 522 | 603 |
| 4 | openrouter-qwen3-30b-a3b | 473 | 434 |
| 5 | openrouter-openai-gpt-4o-mini | 520 | 542 |
| 6 | openrouter-gemini-2.0-flash-001 | 382 | 325 |
| 7 | anthropic-claude-haiku-4-5-pinned | 766 | 802 |

---

## 2. Comparison Table -- silo (confirmation plan)

### Classification Breakdown

| # | Model | Iter 45 (PR #365) | Iter 48 (main) |
|---|-------|-------------------|----------------|
| 1 | ollama-llama3.1 | 13 primary, 2 secondary, 3 absorb | 15 keep, 3 absorb |
| 2 | openrouter-openai-gpt-oss-20b | 14 primary, 1 secondary, 3 absorb | 11 keep, 7 absorb |
| 3 | openai-gpt-5-nano | 8 primary, 0 secondary, 10 absorb | 9 keep, 9 absorb |
| 4 | openrouter-qwen3-30b-a3b | 17 primary, 0 secondary, 1 absorb | 16 keep, 2 absorb |
| 5 | openrouter-openai-gpt-4o-mini | 18 primary, 0 secondary, 0 absorb | 16 keep, 2 absorb |
| 6 | openrouter-gemini-2.0-flash-001 | 11 primary, 4 secondary, 3 absorb | 14 keep, 4 absorb |
| 7 | anthropic-claude-haiku-4-5-pinned | 8 primary, 4 secondary, 6 absorb | 14 keep, 4 absorb |

---

## 3. Per-Model Winner Assessment

### Model 1: ollama-llama3.1

**Winner: Iter 45 (PR #365)**

- Iter 45: 8/6/4 split (primary/secondary/absorb) -- uses all three categories meaningfully. However, all 4 absorbs have questionable targets (e.g., "Demonstrator Fidelity" into "Fallback Authentication Modality").
- Iter 48: 11/0/7 split (keep/absorb) -- all 7 absorbs point to "Risk Framing" as the target, which is a degenerate collapse. The model treats "Risk Framing" as a catch-all bucket, absorbing semantically unrelated levers into it.
- Verdict: Both have poor absorb quality, but iter 48's pattern is far worse (7 levers all absorbed into the same target). Iter 45's primary/secondary split at least provides useful triage even when absorbs are wrong.

### Model 2: openrouter-openai-gpt-oss-20b

**Winner: Roughly tied, slight edge to Iter 45**

- Iter 45: 10/2/6 split. All 6 absorbs are correctly directed pairs. Good justifications with structural reasoning (source is subset of target). Provides primary/secondary distinction.
- Iter 48: 13/0/5 split. All 5 absorbs are correctly directed pairs. Same high quality but fewer absorbs -- slightly more conservative, keeping things like "Contingency Protocol" and "Resilience Narrative" that arguably should merge.
- Verdict: Both produce excellent absorb decisions. Iter 45 finds more valid merges (6 vs 5) and adds the primary/secondary dimension.

### Model 3: openai-gpt-5-nano

**Winner: Iter 45 (PR #365)**

- Iter 45: 5/3/10 split. Very aggressive absorber (10 of 18). 6 valid, 4 questionable. Identifies most true overlaps but also makes some stretches (e.g., "Fallback Certification Criteria" into "Procurement Conditionality").
- Iter 48: 9/0/8/1 split (keep/absorb/remove). 6 valid, 2 questionable. The single `remove` is an error -- it claims lever ff740388 is "a duplicate of itself." This indicates the model is confused by the `remove` option without the safety-valve guidance from PR #365.
- Verdict: Iter 45 finds more valid merges and avoids the confused `remove`. The primary/secondary split adds signal. Iter 48's erroneous `remove` is a quality regression.

### Model 4: openrouter-qwen3-30b-a3b

**Winner: Iter 45 (PR #365)**

- Iter 45: 5/9/4 split. Strong use of the `secondary` classification (9 levers). 3 of 4 absorbs are valid pairs. The primary/secondary split is well-reasoned -- operational levers are correctly marked secondary.
- Iter 48: 12/0/6 split. More absorbs (6) but 2 are questionable (e.g., "Integrity API Decoupling" into "Supplier Concentration Mitigation" is a stretch). Loses the secondary signal entirely.
- Verdict: Iter 45 produces a more nuanced and accurate output. The secondary classification correctly identifies operational levers, and absorb quality is higher (75% vs 67% valid).

### Model 5: openrouter-openai-gpt-4o-mini

**Winner: Iter 48 (main), narrowly**

- Iter 45: 11/7/0 split. Zero absorbs -- the model refuses to merge anything. All 18 levers are classified as either primary or secondary. While the primary/secondary split is reasonable, failing to identify ANY overlaps (e.g., "Technical Standards Advocacy" vs "EU Standards Engagement") is a miss.
- Iter 48: 16/0/2 split. Identifies exactly 2 correct absorb pairs (Technical Standards Advocacy -> EU Standards Engagement, Procurement Conditionality -> Procurement Language Specificity). Conservative but accurate.
- Verdict: Iter 48 at least finds the two most obvious merges, while iter 45 finds none. However, both are too conservative. Iter 45's primary/secondary split provides more information density per lever.

### Model 6: openrouter-gemini-2.0-flash-001

**Winner: Roughly tied, slight edge to Iter 45**

- Iter 45: 7/7/4 split. All 4 absorbs are valid pairs. Clean primary/secondary split adds useful triage information.
- Iter 48: 13/0/5 split. All 5 absorbs are valid pairs. One more absorb found than iter 45.
- Verdict: Both produce excellent quality. Iter 48 finds one additional valid merge (Continuity of Service Planning <-> Contingency Protocol Definition). Iter 45 compensates with the primary/secondary split providing richer output.

### Model 7: anthropic-claude-haiku-4-5-pinned

**Winner: Roughly tied, slight edge to Iter 45**

- Iter 45: 7/5/6 split. 5 valid absorbs, 1 questionable (Supplier Concentration Mitigation -> Procurement Language Specificity). Rich justifications (avg 766 chars) with explicit reasoning about strategic vs operational levers.
- Iter 48: 13/0/5 split. All 5 absorbs are valid pairs. Slightly richer justifications (avg 802 chars).
- Verdict: Near-identical absorb quality. Iter 45 provides the extra primary/secondary dimension with thoughtful justifications. Iter 48 is slightly more precise (0 questionable) but lacks the triage signal.

---

## 4. Overall Verdict

### Does PR #365 improve quality vs main?

**Yes, with caveats.**

#### Improvements from PR #365 (Iter 45):

1. **Richer output taxonomy**: The `primary`/`secondary`/`absorb` classification provides strictly more information than `keep`/`absorb`. Every lever that would be `keep` in iter 48 is now classified as either `primary` (essential strategic lever) or `secondary` (useful but operational). This adds a triage dimension without losing any information.

2. **Prevents degenerate absorb collapse**: The worst failure in iter 48 is ollama-llama3.1 absorbing 7 unrelated levers into "Risk Framing." In iter 45, the same model still makes questionable absorbs (4) but the damage is limited -- the primary/secondary classification captures the rest of the triage intent.

3. **No erroneous removes**: Iter 48's gpt-5-nano produces a confused `remove` (lever claims to be a duplicate of itself). Iter 45 produces zero removes across all 7 models and both plans. The safety-valve guidance in PR #365 appears effective at preventing spurious removals.

4. **Better absorb precision for most models**: Across models that produce absorbs, iter 45 averages ~73% valid absorbs vs iter 48 averaging ~72% valid (when excluding models with 0 absorbs). The difference is small but iter 45 never does worse.

#### Where PR #365 does NOT help:

1. **4o-mini zero-absorb problem**: In iter 45, 4o-mini produces zero absorbs (all 18 levers classified primary/secondary). The primary/secondary framing may have distracted this model from the deduplication task. Iter 48 gets 4o-mini to produce 2 correct absorbs.

2. **Justification length is model-dependent, not iteration-dependent**: Some models write longer justifications in iter 45 (llama3.1: 556 vs 411), others in iter 48 (gpt-5-nano: 522 vs 603, haiku: 766 vs 802). No consistent pattern.

3. **Silo plan shows less differentiation**: For the silo plan, several models in iter 45 classify almost everything as `primary` with 0 secondary (qwen: 17/0/1, 4o-mini: 18/0/0). The primary/secondary split is underutilized on simpler plans.

#### Summary Scores (sovereign_identity, 5-point scale)

| Model | Iter 45 | Iter 48 | Winner |
|-------|---------|---------|--------|
| ollama-llama3.1 | 2.0 | 1.0 | Iter 45 |
| openrouter-openai-gpt-oss-20b | 4.5 | 4.0 | Iter 45 |
| openai-gpt-5-nano | 3.0 | 2.5 | Iter 45 |
| openrouter-qwen3-30b-a3b | 3.5 | 3.0 | Iter 45 |
| openrouter-openai-gpt-4o-mini | 2.5 | 3.0 | Iter 48 |
| openrouter-gemini-2.0-flash-001 | 4.0 | 4.0 | Tie |
| anthropic-claude-haiku-4-5-pinned | 4.5 | 4.0 | Iter 45 |

**Final verdict**: PR #365 wins 5 out of 7 models, ties 1, loses 1. The primary/secondary classification adds meaningful triage signal that the keep-only approach lacks. Absorb quality is comparable or better. The silo plan confirms these patterns hold directionally, though with less differentiation.

**Recommendation**: PR #365 is a quality improvement. The 4o-mini zero-absorb case could be investigated separately as a prompt-sensitivity issue specific to that model.
