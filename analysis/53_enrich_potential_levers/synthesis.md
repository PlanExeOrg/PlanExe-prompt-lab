# Synthesis

## Cross-Agent Agreement

Only two analysis artifacts exist for this run: `insight_claude.md` (quality
analysis) and `code_claude.md` (code review), both from the same model. There
is no multi-agent disagreement to resolve. Instead, the two files are
complementary — the insight file observes output patterns; the code review
traces each pattern to its root cause in source code. Every claim in each
file has been verified against the actual source (see below).

Consensus points across both files:

- **gpt-oss-20b 0/5 failure** is caused by no-retry-on-batch-exception (B1) +
  hitting the 8192 output-token limit on the third batch (N1). No dispute.
- **qwen3-30b terse synergy/conflict** is caused by the "(40-60 words)"
  quantitative target, which weak models treat as a ceiling (N2/S2). No dispute.
- **Cross-reference format inconsistency** is caused by `full_lever_context_str`
  exposing full UUIDs with no format instruction (N4/B2). No dispute.
- **gpt-5-nano template-driven descriptions** are caused by the "(80-100 words)"
  word-budget target filling via sub-headers (N3/S2). No dispute.
- **Missing consequences/review in batch prompt** means the LLM writes
  `conflict_text` without the lever's documented trade-off analysis (B3). No
  dispute.

---

## Cross-Agent Disagreements

None. Both artifacts are from the same model and reach consistent conclusions.

The one claim worth verifying independently was S3 — the code review argued
that `identify_potential_levers.py`'s `consequences` field description
violates OPTIMIZE_INSTRUCTIONS by naming banned phrases. This was confirmed:

- `OPTIMIZE_INSTRUCTIONS` line 82: "Do NOT add explicit prohibitions naming
  banned phrases — small models treat the prohibition text as a template and
  copy the banned phrases."
- `consequences` field description (line 115): "Do NOT include 'Controls ...
  vs.', 'Weakness:', or other review/critique text in this field"

The violation is real. It predates the current OPTIMIZE_INSTRUCTIONS guidance.

---

## Code Verification Results

All code claims were confirmed by reading the source:

| Claim | File | Line(s) | Confirmed? |
|-------|------|---------|-----------|
| B1 — no retry, immediate re-raise on batch exception | `enrich_potential_levers.py` | 209-213 | Yes |
| B2 — `full_lever_context_str` includes full UUIDs | `enrich_potential_levers.py` | 156 | Yes |
| B3 — batch prompt omits `consequences` and `review` | `enrich_potential_levers.py` | 171-173 | Yes |
| S1 — `calls_succeeded=1` hardcoded in `_run_enrich` | `runner.py` | 185 | Yes |
| S2 — "(80-100 words)" and "(40-60 words)" targets | `enrich_potential_levers.py` | 102-108 | Yes |
| S3 — banned phrase named in `consequences` field description | `identify_potential_levers.py` | 112-118 | Yes |
| No format instruction in ENRICH_LEVERS_SYSTEM_PROMPT | `enrich_potential_levers.py` | 125-138 | Yes |
| No qualitative mechanism guidance in system prompt | `enrich_potential_levers.py` | 125-138 | Yes |

---

## Top 5 Directions

### 1. Include `consequences` and `review` in the batch prompt (B3 + I4)

- **Type**: code fix
- **Evidence**: Confirmed at `enrich_potential_levers.py:171-173`. The LLM
  is asked to generate `description` (lever's purpose and effects) and
  `conflict_text` (lever's trade-offs) without being given `consequences`
  (what happens when the lever is pulled) or `review` (the documented
  primary trade-off). This is the most direct information source for both
  fields — the model is currently forced to infer them from `name` and
  `options` alone.
- **Impact**: Affects all 30 successful plans across all 6 working models.
  Content quality improvement is universal — every `description` and
  `conflict_text` generated currently lacks grounding in the lever's
  documented effects. The OPTIMIZE_INSTRUCTIONS goal states this step
  should "enable informed prioritization and trade-off decisions"; vague
  enrichment from insufficient context degrades downstream scenario quality.
  OPTIMIZE_INSTRUCTIONS also warns: "Batch boundary blindness... the full
  lever list is provided as context precisely to prevent this" — but the
  batch-specific lever details are also incomplete.
- **Effort**: Low — a single change to `lever_details_for_prompt` at line
  171-173, adding two fields per lever in the prompt string.
- **Risk**: Mildly increases input tokens per call (each lever gains ~2-4
  sentences of `consequences` + ~1 sentence of `review`). Estimated increase
  ~300-500 tokens per batch. Does not change the output schema or validation.
  Models that were already producing reasonable output may change their
  phrasing; this is expected and desirable.

### 2. Add qualitative mechanism guidance for synergy/conflict (I2 + S2)

- **Type**: prompt change
- **Evidence**: S2 confirmed at `enrich_potential_levers.py:104-108` and
  `ENRICH_LEVERS_SYSTEM_PROMPT` lines 134-135. The "(40-60 words)" targets
  are purely quantitative. qwen3-30b (run 81) produces ~35-40 word synergy
  texts — right at the minimum — that name lever pairs without explaining
  the mechanism. All models lack explicit guidance to explain *how* or *why*
  a synergy or conflict operates.
- **Impact**: Affects all 30 successful plans. Directly fixes qwen3-30b's
  terse output (N2). Also raises the quality floor for all models: haiku and
  gpt-4o-mini already write mechanism-explaining text, but only because they
  naturally expand beyond the minimum — not because the prompt requires it.
  Adding "Explain the specific mechanism or pathway" makes quality explicit
  rather than emergent.
- **Effort**: Low — add one sentence of qualitative guidance to the
  `synergy_text` and `conflict_text` field descriptions and to the system
  prompt output requirements.
- **Risk**: May increase synergy/conflict text length for all models by
  10-20%. Models currently at ~380 chars (haiku) may go to ~450. Still well
  below the 2× baseline warning threshold. The OPTIMIZE_INSTRUCTIONS warning
  "word-count padding" applies — the new guidance should say "explain the
  mechanism" not "write more words".

### 3. Fix UUID format in context string and add format instruction (B2 + I1 + I5)

- **Type**: code fix + prompt change
- **Evidence**: B2 confirmed at `enrich_potential_levers.py:156` —
  `full_lever_context_str` presents levers as `"- <uuid>: <name>"`. No
  instruction in the system prompt specifies which format to use when
  referencing levers. This is the direct cause of N4: llama3.1 copies the
  full UUID, qwen3-30b uses truncated UUID (first 8 chars), gemini uses
  backtick names, others use plain names.
- **Impact**: Affects all 30 successful plans. Downstream code that parses
  synergy/conflict text to extract lever relationships will fail on 3 of 6
  format variants. Standardizing to name-only is the lowest-friction fix and
  makes synergy/conflict text readable without UUID noise.
- **Effort**: Very low — change line 156 from `f"- {lever.lever_id}: {lever.name}"` to `f"- {lever.name}"`, and add one sentence to the system prompt.
  The `lever_id` is still provided in `lever_details_for_prompt` via
  `"Lever ID: {lever.lever_id}"` for the LLM to match its output.
- **Risk**: Very low. Removing the UUID from the context string does not
  remove the UUID from the batch prompt (it's still in `Lever ID:` prefix).
  The change prevents weaker models from copying the UUID into cross-references
  without affecting their ability to return the correct `lever_id` in the
  structured output.

### 4. Add per-batch retry with reduced batch size on failure (B1 + I3)

- **Type**: code fix
- **Evidence**: B1 confirmed at `enrich_potential_levers.py:209-213`. The
  `except Exception: raise ValueError("LLM batch interaction failed.")` pattern
  immediately kills the entire plan on any batch exception — even though prior
  batches in the same plan may have succeeded. `identify_potential_levers.py`
  has a 5-call adaptive retry loop (lines 297-348) as the established pattern.
  The enrich step has none.
- **Impact**: Directly recovers gpt-oss-20b's 5/5 failed plans (if retry at
  half batch size avoids the 8192 token limit). Also adds resilience for all
  models against transient failures. Without this fix, a single unlucky
  truncation on the third batch discards 10+ successfully enriched levers.
- **Effort**: Medium — requires adding a try/except inside the batch loop
  that catches exceptions, halves the batch size, and retries the current
  batch. Need to handle the edge case where batch size 1 still fails (fail
  with a warning rather than aborting the whole plan).
- **Risk**: Medium complexity. Partial recovery (2 batches succeed, third
  fails at reduced size) results in silently incomplete enrichment — some
  levers lack description/synergy/conflict. The current code already handles
  incomplete levers gracefully (line 217: skips levers missing the new fields).
  The `calls_succeeded=1` hardcode in runner.py (S1) should also be fixed to
  report actual batch count for correct partial-recovery logging.

### 5. Remove banned-phrase prohibition from `consequences` field in `identify_potential_levers.py` (S3)

- **Type**: prompt change (field description in `identify_potential_levers.py`)
- **Evidence**: S3 confirmed at `identify_potential_levers.py:112-118`. The
  field description contains: "Do NOT include 'Controls ... vs.', 'Weakness:',
  or other review/critique text in this field". OPTIMIZE_INSTRUCTIONS at line
  82 explicitly warns against this exact pattern: naming banned phrases teaches
  small models to reproduce them.
- **Impact**: Affects identify_potential_levers step (upstream), not enrich.
  Weak models may currently copy `'Controls ... vs.'` or `'Weakness:'` into
  `consequences` — these would then appear in the input to enrich, degrading
  the quality of the enrichment step. Removing the phrase-specific prohibition
  eliminates this source of template lock for small models.
- **Effort**: Very low — remove the prohibition sentence from the field
  description; the system prompt already has structural validators and examples
  that guide the model away from review text in consequences.
- **Risk**: Very low. The prohibition text has no structural enforcement —
  removing it only removes a pattern that OPTIMIZE_INSTRUCTIONS already warns
  against keeping.

---

## Recommendation

**Do B3 + I4 first: include `consequences` and `review` in the batch prompt.**

**Why first**: This is the most impactful fix per unit of effort. The enrich
step's stated goal is to add grounded `description`, `synergy_text`, and
`conflict_text` to each lever. The `description` should explain the lever's
purpose and effects — yet the LLM currently writes this without access to
`consequences` (the field that documents the lever's effects). The `conflict_text`
should identify the lever's trade-offs — yet `review` (the field that explicitly
documents the primary trade-off) is withheld from the LLM. This is a structural
information gap, not a prompt calibration issue.

The fix improves content quality for every enriched lever across all 30
successful plans from all 6 working models. No other change has this reach.
By contrast, B1 (retry fix) recovers 5 failed plans from one model; B2/I1
(UUID format) fixes a formatting inconsistency; I2 (mechanism guidance) raises
a quality floor. All three are valuable but secondary.

**Specific change — `enrich_potential_levers.py:171-173`:**

```python
# Current (line 171-173):
lever_details_for_prompt = "\n\n".join(
    [f"Lever ID: {lever.lever_id}\nName: {lever.name}\nOptions: {json.dumps(lever.options)}"
     for lever in batch]
)

# Proposed:
lever_details_for_prompt = "\n\n".join([
    f"Lever ID: {lever.lever_id}\n"
    f"Name: {lever.name}\n"
    f"Consequences: {lever.consequences}\n"
    f"Options: {json.dumps(lever.options)}\n"
    f"Review: {lever.review}"
    for lever in batch
])
```

No other file changes are required for this fix. The `InputLever` schema
already loads `consequences` and `review` (line 88-96) — they just aren't
forwarded to the prompt.

**Expected outcome**: Descriptions become more specific to each lever's actual
effects rather than inferred from the name alone. Conflict texts gain a
grounded basis in the documented trade-off. The qualitative gap between haiku
(which may implicitly leverage context) and weaker models (which rely entirely
on the prompt) should narrow. Run the next experiment against
`snapshot/1_deduplicate_levers` with the same 7 models to measure the change.

---

## Deferred Items

**D1 — B1 + I3: Per-batch retry (do second)**
Fixes gpt-oss-20b and adds resilience. Medium effort. Do after B3 so the
first experiment confirms the quality improvement direction before adding
retry complexity.

**D2 — B2 + I1 + I5: UUID format standardization (do third)**
Very low effort and high polish value. Should be bundled with B3 or B1 if
the experiment iteration allows multiple changes, but is safe to defer since
it's cosmetic.

**D3 — I2 + S2: Qualitative mechanism guidance (do fourth)**
Prompt change that improves synergy/conflict quality for all models. Low
effort. The "(40-60 words)" target may be relaxed or replaced with "at least
2 substantive sentences explaining the mechanism." Watch for verbosity
amplification on models already producing adequate length.

**D4 — S3: Remove banned-phrase prohibition from `identify_potential_levers.py`**
This is in a different step. Low-risk cleanup that aligns the field description
with OPTIMIZE_INSTRUCTIONS. Do as a maintenance commit, not a full experiment
iteration, since the primary effect is on identify_potential_levers output
rather than enrich.

**D5 — I6: Update OPTIMIZE_INSTRUCTIONS in `enrich_potential_levers.py`**
Document the UUID cross-reference format problem, word-count-driven brevity,
and batch retry absence in the OPTIMIZE_INSTRUCTIONS known-problems list.
Do this as a maintenance commit after B3 is confirmed — the confirmed learnings
from experiment 53 become the documented known problems for future iterations.

**D6 — S1: Fix `calls_succeeded=1` hardcode in `runner.py:185`**
The hardcoded `1` is incorrect for 15-lever plans (which make 3 calls).
This has no current downstream effect but would prevent partial-recovery
logging from working if B1 is implemented. Fix when B1 is implemented.
