# Code Review (claude)

Source files reviewed:
- `worker_plan/worker_plan_internal/lever/identify_potential_levers.py`
- `prompt_optimizer/runner.py`

Prior review: `analysis/3_identify_potential_levers/code_claude.md`

---

## Bugs Found

### B1 — `consequences` field description teaches plain-prose format and imposes a conflicting word count

**File:** `identify_potential_levers.py:30–32`

```python
consequences: str = Field(
    description="Briefly describe the likely second-order effects or consequences of pulling this lever "
                "(e.g., 'Choosing a high-risk tech strategy will likely increase talent acquisition "
                "difficulty and require a larger contingency budget.'). 30 words."
)
```

Two problems in the same description:

1. The embedded example (`"Choosing a high-risk tech strategy will likely increase talent acquisition difficulty…"`) is plain one-sentence prose — exactly the format the system prompt forbids. For models operating in structured-output mode the field description is injected into the JSON schema the model sees. The example actively trains the model to produce a single-sentence consequence rather than the required three-part chain `"Immediate: … → Systemic: … → Strategic: …"`.

2. The "30 words" length hint directly contradicts the chain format requirement, which requires three sub-sentences and typically runs 50–120 words. For models that weight schema-level constraints over natural-language system prompts, satisfying "30 words" means skipping the chain entirely.

**Direct cause of run 37 (gpt-4o-mini) consequence chain failure.** Run 37 produces exactly the style shown in the field description — one-sentence plain prose (~95 chars average) — across all 75 levers in 5 plans. The constraint-violation rate is 75/75 (100%). The schema example matches run 37's output verbatim in style: `"Choosing a diversified funding strategy will likely enhance financial stability, increase stakeholder engagement, and mitigate risks associated with funding shortages."` at `history/0/37_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`.

---

### B2 — Per-call lever count is never validated; 6-lever responses merge silently

**File:** `identify_potential_levers.py:58–60`, `:215–218`

```python
# Field description only — no validator:
levers: list[Lever] = Field(description="Propose exactly 5 levers.")

# Flat merge, no count check:
for response in responses:
    levers_raw.extend(response.levers)
```

`DocumentDetails.levers` has no `@field_validator` or `model_validator` enforcing `len(levers) == 5`. When a call returns 6 levers all 6 are appended to `levers_raw`, producing a 16-lever merged file with no warning.

**New evidence from runs 32–38.** The gta plan triggers a 6-lever response in one of the three calls across runs 33, 35, 37, and 38, consistently producing 16-lever output files. The run 38 sovereign_identity raw output contains a 6th entry with `name: "placeholder"` at `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-9-potential_levers_raw.json:75`; this placeholder propagates unchecked into the final artifact at `002-10-potential_levers.json:71`.

*(Identified in analysis/3 B2; the new runs add cross-model reproducibility evidence.)*

---

### B3 — Calls 2 and 3 omit the original plan content, creating runaway context pressure for verbose models

**File:** `identify_potential_levers.py:162–170`

```python
if call_index == 1:
    prompt_content = user_prompt                          # full plan content
else:
    names_list = ", ".join(f'"{n}"' for n in generated_lever_names)
    prompt_content = (
        f"Generate 5 MORE levers with completely different names. "
        f"Do NOT reuse any of these already-generated names: [{names_list}]"
    )
```

For calls 2 and 3 the user message is exclusively the anti-duplication instruction. The model must reconstruct the plan from conversation history only. Two consequences:

1. **Context growth is dominated by the assistant turns.** For haiku on the silo plan, call 1's assistant turn is ~40 KB (≈10 000 tokens). By call 3 the context contains: system_prompt + ~8 KB plan + ~40 KB assistant turn 1 + 80 bytes user turn 2 + ~40 KB assistant turn 2 + 80 bytes user turn 3. This is ~90 KB of context per call 3 request, growing with plan complexity.

2. **Complex plans compound the effect.** The hong_kong and parasomnia plans (the two that timeout for run 38 at 427 s and 721 s) are the heaviest input plans in the corpus. Their longer `user_prompt` pushes the stacked context beyond what simpler plans require, directly correlating with the timeout pattern.

---

### B4 — Placeholder and malformed levers are not filtered before writing final output

**File:** `identify_potential_levers.py:221–231`

```python
for i, lever in enumerate(levers_raw, start=1):
    lever_id = str(uuid.uuid4())
    lever_cleaned = LeverCleaned(
        lever_id=lever_id,
        name=lever.name,
        consequences=lever.consequences,
        options=lever.options,
        review=lever.review_lever,
    )
    levers_cleaned.append(lever_cleaned)
```

No filter exists for:
- Lever names that are sentinel strings (`"placeholder"`, `"Placeholder Removed"`, `""`)
- Options lists with the wrong count (< 3 or > 3)
- Consequence strings that are empty or copy the schema field example verbatim

**Direct evidence:** `history/0/38_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:65` contains a blank fourth option, and `:71` contains a `name: "placeholder"` lever with empty `consequences`, empty `options`, and a structural sentinel `review` — all in the **final** clean output file served to downstream pipeline stages.

*(The post-merge sanitization gap was identified in analysis/3 I8 but remains unimplemented.)*

---

### B5 — `options` field description still says "2-5 options" in both Lever and LeverCleaned

**File:** `identify_potential_levers.py:33–35`, `:80–82`

```python
# Lever (line 33-35):
options: list[str] = Field(description="2-5 options for this lever.")

# LeverCleaned (line 80-82):
options: list[str] = Field(description="2-5 options for this lever.")
```

Both schema descriptions say "2-5", directly contradicting the system prompt's "exactly 3 qualitative strategic choices". In structured-output mode the schema description is a first-class constraint competing with the system prompt. For models that weight schema constraints heavily, 2 options is schema-valid.

**New evidence from run 33 (llama3.1):** 9 of 15 levers in the parasomnia plan contain only 2 options, matching the schema-permitted minimum. No validation error was raised.

*(Identified in analysis/3 B1; the schema descriptions themselves were not changed in PRs #268–#272.)*

---

## Suspect Patterns

### S1 — `set_usage_metrics_path()` called outside `_file_lock` creates a metric-path race condition

**File:** `runner.py:106–110`

```python
set_usage_metrics_path(plan_output_dir / "usage_metrics.jsonl")   # ← outside lock

with _file_lock:
    dispatcher.add_event_handler(track_activity)
```

`set_usage_metrics_path` writes to module-level global state. When `workers > 1`, thread A and thread B both call it before either acquires the lock. The last write wins, so both threads write usage metrics to the same file and one plan's metrics are silently discarded.

This is the likely explanation for run 38 haiku silo lacking `activity_overview.json` (or equivalent usage-derived artifacts): if haiku's `luigi_workers` config is > 1, the race discards metric data for whichever plan loses the path race.

(The prior review's S1 noted the dispatcher event-handler sharing issue; this is a separate race on the path global itself.)

---

### S2 — `or` fallback in assistant turn triggers on empty string, not only None

**File:** `identify_potential_levers.py:204–207`

```python
content=(
    result["chat_response"].message.content
    or result["chat_response"].raw.model_dump_json()
),
```

The `or` operator fires the fallback for any falsy value including `""`. For Anthropic Claude models responding via tool_use, `message.content` is often an empty string (output goes into the tool block). The fallback uses `raw.model_dump_json()`, which serializes the validated Pydantic `DocumentDetails` with its Python field names (`lever_index`, `review_lever`, `strategic_rationale`).

Effect: for all Anthropic Claude runs (run 38, haiku), the conversation history for calls 2 and 3 contains a clean Pydantic-serialized JSON, not the raw model output. This changes the "prior response" the model observes in call 2/3 — it sees normalized field names and potentially re-ordered structure. This is the iteration-2 serialization fix (PR #270) working as intended, but the consequence is that haiku's call 2/3 are conditioned on a synthetic assistant turn.

---

### S3 — `lever_index` is schema-required but never validated or used in final output

**File:** `identify_potential_levers.py:24–26`

```python
lever_index: int = Field(description="Index of this lever.")
```

`lever_index` appears in `Lever` and in the raw JSON schema the model sees, but:
1. It is not copied to `LeverCleaned` (which uses a UUID instead).
2. It is not validated for uniqueness or correct range (1–5) within a call.
3. It occupies output tokens per lever (~4–6 tokens per lever × 15 levers = 60–90 tokens per plan) for no downstream benefit.

For a model returning 6 levers in a call (B2), `lever_index` values 1–6 would signal to subsequent calls that the prior batch "ended at index 6", potentially inviting continuation rather than a fresh set.

---

## Improvement Opportunities

### I1 — Rewrite `consequences` field description to match the required chain format

**File:** `identify_potential_levers.py:30–32`

Replace the current plain-prose example and "30 words" hint with a description that mirrors the system prompt requirement:

```
"Required format: 'Immediate: [direct first-order effect] → Systemic: [second-order impact "
"with a measurable indicator, e.g. a % or cost delta] → Strategic: [long-term implication "
"for the project]'. All three labels and at least one quantitative estimate are mandatory."
```

This removes the template-like plain-prose example that run 37-class models follow, and eliminates the "30 words" constraint that makes the chain format impossible to satisfy. Expected effect: reduce or eliminate consequence chain failures for models that weight schema descriptions over system prompt instructions.

---

### I2 — Change `options` field description from "2-5" to "exactly 3" in both classes

**File:** `identify_potential_levers.py:33–35`, `:80–82`

Change both occurrences from `"2-5 options for this lever."` to `"Exactly 3 options for this lever. No more, no fewer."` This eliminates the schema-level permission for 2 or 4 options.

---

### I3 — Add post-merge lever count warning and placeholder filter

**File:** `identify_potential_levers.py:215–231`

After extending `levers_raw`, add:

```python
if len(levers_raw) != 15:
    logger.warning(f"Expected 15 levers after merge, got {len(levers_raw)}")

SENTINEL_TERMS = {"placeholder", "removed", "structural compliance"}
levers_filtered = [
    lev for lev in levers_raw
    if not any(term in lev.name.lower() for term in SENTINEL_TERMS)
    and len(lev.options) == 3
    and lev.name.strip()
]
if len(levers_filtered) != len(levers_raw):
    logger.warning(
        f"Filtered {len(levers_raw) - len(levers_filtered)} malformed levers "
        f"(placeholder names or wrong option count)"
    )
```

Expected effects: prevent `"placeholder"` levers from reaching `002-10-potential_levers.json` (run 38 sovereign_identity); surface the gta 16-lever violation as a warning instead of silent overflow.

---

### I4 — Add consequence chain format validation in post-merge

**File:** `identify_potential_levers.py:221–231`

After constructing each `LeverCleaned`, check the chain markers:

```python
CHAIN_MARKERS = ("Immediate:", "Systemic:", "Strategic:")
missing = [m for m in CHAIN_MARKERS if m not in lever_cleaned.consequences]
if missing:
    logger.warning(
        f"Lever '{lever_cleaned.name}': consequence missing chain markers: {missing}"
    )
```

This surfaces run 37-class failures as observable warnings without breaking the pipeline. A count of violations could gate a retry decision.

---

### I5 — Add a `max_tokens` cap to the structured LLM call

**File:** `identify_potential_levers.py:180–188`

The `sllm.chat(chat_message_list)` call has no token budget. For haiku, call 1 already generates ~10 000 tokens; call 3's combined context is ~90 KB. A per-call cap (e.g., 3000–4000 tokens for the response) would:
- Prevent haiku from timing out on complex plans (run 38: 427 s and 721 s)
- Bound context growth for calls 2 and 3
- Keep output sizes roughly model-agnostic

The cap should be configurable per model, derivable from `llm.metadata` or a config override, rather than hardcoded.

---

### I6 — Include a plan-context anchor in calls 2 and 3

**File:** `identify_potential_levers.py:166–170`

The current call 2/3 user message contains no plan reference. Adding a brief anchor phrase reduces context-drift risk:

```python
prompt_content = (
    f"For the same plan described above, generate 5 MORE levers "
    f"with completely different names. "
    f"Do NOT reuse any of these already-generated names: [{names_list}]"
)
```

"For the same plan described above" explicitly links the follow-up to the prior context. For models whose call-3 context is dominated by their own large prior responses, this reduces the chance of drifting to generic (non-plan-specific) levers.

---

## Trace to Insight Findings

| Code Location | Insight Finding |
|---|---|
| **B1** `consequences` description (plain-prose example, "30 words") | Claude: "Run 37 consequence format failure (all plans)" — 75/75 levers have plain prose, avg ~95 chars. Codex: "75/75 consequence chain violations" for run 37. The style in the field description matches run 37's output verbatim. |
| **B2** No lever count validator; flat merge | Claude: "Lever count violation for gta plan (16 instead of 15)" in runs 33, 35, 37, 38. Codex: run 38 sovereign_identity raw has `name: "placeholder"` as 6th lever of call 1; final file has blank option + placeholder lever. |
| **B3** Calls 2/3 drop plan content; growing conversation context | Claude: "Run 38 timeout on complex plans (427 s, 721 s)". Context for call 3 includes two ~40 KB haiku assistant turns; hong_kong/parasomnia have longer `user_prompt`, compounding growth. |
| **B4** No placeholder/malformed filter in post-merge | Codex: "run 38 is not just verbose; it is malformed" — blank option at `002-10-potential_levers.json:65`, placeholder lever at `:71`. No code catches this before the file is written. |
| **B5** `options` schema says "2-5" | Codex: "Run 33 also breaks the exact-3-options rule in a concentrated tail failure" — 9 levers with only 2 options in parasomnia starting at `002-10-potential_levers.json:70`. |
| **S1** `set_usage_metrics_path` outside `_file_lock` | Claude: "Run 38 haiku silo has no activity_overview.json file in its output directory." Metric path race when workers > 1 explains absent per-plan usage artifacts. |
| **S2** `or` fallback uses Pydantic-serialized JSON for Claude tool_use responses | Related to PR #270 (iteration 2 fix). For haiku (run 38), calls 2/3 are conditioned on a synthetic Pydantic-JSON assistant turn rather than the model's raw output. |
| **I1** Rewrite `consequences` description | Claude H3: "Add a per-consequence length advisory targeting ~200–350 chars." Codex H3: "Add a hard self-check for consequence formatting." Root cause is in the schema description as well as the prompt. |
| **I5** Add `max_tokens` cap | Claude C3: "Add per-call max_tokens limit (or equivalent) for haiku." Codex C4: "Add output-size / latency guardrails before timeouts." |
| **I6** Plan-context anchor in calls 2/3 | Partly explains why gta reproducibly produces 16 levers: call 2/3 models receiving only the name-exclusion list may infer the plan context less precisely and generate an extra safety-net lever. |

---

## Summary

Five bugs in `identify_potential_levers.py` directly explain the most significant quality regressions observed in runs 32–38:

**Highest priority:**

1. **B1** — The `consequences` field description provides a plain-prose example and a "30 words" length target. These are the proximate cause of run 37's 100% consequence chain failure (75/75 levers). This is a schema description bug independent of the system prompt; fixing it requires changing the Pydantic field description, not the prompt.

2. **B2** — No `len(levers) == 5` validator means 6-lever responses silently inflate the merged output. The gta 16-lever pattern is reproducible across four different models; the run 38 placeholder lever reaches the final artifact with no error.

**Medium priority:**

3. **B3** — Calls 2 and 3 contain no plan content. For haiku the stacked assistant turns reach ~80 KB by call 3, directly contributing to the 427 s and 721 s timeouts on the two heaviest plans.

4. **B4** — No post-merge filter removes placeholder or zero-content levers. The `"placeholder"` entry in run 38 sovereign_identity would be caught by a single string check.

5. **B5** — Both `Lever.options` and `LeverCleaned.options` still say "2-5 options", directly contradicting the system prompt's "exactly 3". Run 33 produced 9 two-option levers.

**Fixes carried over from analysis/3 that are still absent:** lever count validator (former B2), post-merge sanitization (former I8), `max_validation_retries > 0` (former I6), context window guard (former I5). Evidence for each is stronger after runs 32–38.

**Fixes from analysis/3 that are confirmed resolved:** "25% faster" example removed (I1), naming example generalized (I2), prefix prohibition extended (I3), wrapper fields made optional (I4).
