# Synthesis

## Cross-Agent Agreement

Both insight_claude and code_claude agree on the following:

1. **PR #339 verdict: KEEP.** The primary fix (raising `review_lever` `min_length` from 20 to 50) directly eliminated the llama3.1 parasomnia `LLMChatError` (19-char stub `"Sensor Data Sharing"`). Success rate improved from 34/35 (97.1%) to 35/35 (100%). No content quality regressions were introduced.

2. **The secondary template lock persists and is rooted in the third example.** The phrase "the options neglect" appears verbatim in both the `Lever.review_lever` Pydantic field description (line 115) and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (line 235). llama3.1 gta_game run 96 produces this pattern in 16/16 reviews (100%). `OPTIMIZE_INSTRUCTIONS` now documents this anti-pattern (lines 73-79) but the trigger phrase remains in the prompts — warning and root cause coexist.

3. **Cross-field contamination (weakness text in consequences) is a persistent llama3.1 issue.** Both agents note this in runs 89 and 96 without improvement. The `consequences` field description explicitly prohibits it, but no validator enforces it.

4. **Option count change (`!= 3` → `< 3`) had zero observable impact.** No model over-generated or under-generated in either batch. The change is directionally correct but currently unexercised.

5. **Partial recovery events increased (1 → 4).** All 35 plans completed, so this is a reliability warning, not a failure. Gemini hong_kong_game producing 6 levers (down from 18) is the most visible symptom.

---

## Cross-Agent Disagreements

**No substantive disagreements** between agents. The code review (code_claude) added one finding not in the insight file: **B2 — duplicate example injection** (the three `review_lever` examples appear in both the Pydantic field description and the system prompt, doubling the copyable-phrase signal and wasting tokens on every call). The insight file did not flag B2 explicitly, but its secondary-lock observations are consistent with B2's mechanism. Source code confirms B2: `Lever.review_lever` field description at lines 107–116 and `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` lines 232–235 contain identical text.

The code review also flags **S1 — shared dispatcher cross-contamination** in `runner.py` (parallel workers share one dispatcher, causing cross-thread `track_activity.jsonl` writes). The insight file does not mention this. Source code confirms the pattern: `dispatcher.add_event_handler(track_activity)` at `runner.py:147` is called per-thread without removing the previous handler. This is a real latent bug masked by `track_activity_path.unlink()` at line 149.

---

## Top 5 Directions

### 1. Replace "the options neglect" in the third review_lever example
- **Type**: prompt change
- **Evidence**: B1 (code_claude), H1 (insight_claude). The phrase "the options neglect" appears at `identify_potential_levers.py:115` (Lever field description) and `identify_potential_levers.py:235` (system prompt). `OPTIMIZE_INSTRUCTIONS` lines 73-75 explicitly names this as the secondary-lock trigger. llama3.1 gta_game run 96: 16/16 reviews use the pattern. Run 89 also 100%.
- **Impact**: Directly removes the lock source for llama3.1. The lock affects every run where llama3.1 is used and appears at 50–100% frequency depending on plan. A domain-specific rewrite (no "the options [verb]" form) would break the template. Affects content quality of all llama3.1 lever reviews.
- **Effort**: low — edit two strings (or one, if B2 deduplication is done simultaneously)
- **Risk**: Weaker models might shift to copying a different subphrase in the replacement text. Mitigated by following the agriculture-example template: critique must be domain-specific and non-portable.

### 2. Deduplicate review_lever examples (remove from Lever field description, keep in system prompt)
- **Type**: code/prompt change
- **Evidence**: B2 (code_claude). Both `Lever.review_lever` field description and system prompt carry the same three examples verbatim. llama_index serializes the full Pydantic schema per call, so every LLM call receives the examples twice.
- **Impact**: Halves the template-lock signal strength. Also reduces token count per call (approximately 150-200 tokens saved per call × 3 calls per plan × N plans). Affects all models; most visible on weaker models that are susceptible to template lock.
- **Effort**: low — remove examples from `Lever.review_lever` field description at lines 107-116, replacing with a one-line structural note (similar to `LeverCleaned.review` at lines 203-205). Can be combined with direction 1 in a single PR.
- **Risk**: Removing the field-description examples slightly reduces the per-field hint. The system prompt still carries the examples, so the LLM retains the guidance. Low risk.

### 3. Add cross-field contamination prohibition to OPTIMIZE_INSTRUCTIONS and consequences validator
- **Type**: code fix + documentation
- **Evidence**: I1 and I3 (code_claude), H2 (insight_claude). llama3.1 places "A weakness in this approach is that…" into `consequences` in both runs 89 and 96. The field description prohibits it but no validator enforces it. `OPTIMIZE_INSTRUCTIONS` has 7 documented problems; this is the 8th undocumented one.
- **Impact**: Catches contaminated `consequences` at validation time, forcing a retry with a clean output. Affects llama3.1 on all plans (pattern observed consistently). Adding it to OPTIMIZE_INSTRUCTIONS makes the problem visible to future analysts.
- **Effort**: medium — adding a validator requires careful i18n-safe structural detection (per the OPTIMIZE_INSTRUCTIONS principle: no English-only keyword matching). Documenting it in OPTIMIZE_INSTRUCTIONS is low effort.
- **Risk**: If the validator is too aggressive (e.g., any "weakness" word), it could reject valid non-English consequences containing similar morphology. A length-gated check ("weakness" appearing in the first 200 chars) or a structural heuristic ("A weakness" as a sentence opener) would be safer.

### 4. Relax DocumentDetails levers min_length=5 for calls 2 and 3
- **Type**: code fix
- **Evidence**: I2 (code_claude). All three LLM calls use `DocumentDetails` with `min_length=5`. Calls 2 and 3 must generate 5+ novel levers while explicitly avoiding all previously generated names — a harder constraint. If the model returns 4 levers, the entire call fails with `LLMChatError` and enters partial recovery. Partial recovery events increased from 1 to 4 across runs 96-02.
- **Impact**: Reduces partial recovery failures for calls 2 and 3. Gemini hong_kong_game produced only 6 levers because 1/3 calls succeeded. Relaxing later-call `min_length` to 3 would reduce the chance of total call failure when the model underproduces slightly.
- **Effort**: medium — `DocumentDetails` is a single shared schema. To enforce different constraints per call, either create a second schema (`DocumentDetailsLaterCall` with `min_length=3`) or wrap the validation in the call loop. The loop currently passes the same `sllm = llm.as_structured_llm(DocumentDetails)` for all three calls.
- **Risk**: Accepting 3 levers per later call reduces total lever diversity slightly. This is tolerable — the downstream `DeduplicateLeversTask` already handles extras, and `FocusOnVitalFewLevers` selects 4-6 final levers from whatever pool exists.

### 5. Fix shared dispatcher cross-thread handler accumulation in runner.py
- **Type**: code fix
- **Evidence**: S1 (code_claude). `run_single_plan` adds a `TrackActivity` handler to the shared singleton dispatcher on every call without removing it. With `workers > 1`, handlers accumulate across threads and LLM events broadcast to multiple plans' `track_activity.jsonl` files simultaneously.
- **Impact**: Corrects per-plan usage tracking when running in parallel. Affects data quality of `track_activity.jsonl` files — currently these files may contain events from other plans' calls. Does not affect plan output quality (levers, reviews, options), only the side-channel usage logs.
- **Effort**: medium — fix requires either removing the handler after each plan completes (`dispatcher.remove_event_handler(...)`) or using a per-plan dispatcher instance rather than the global singleton.
- **Risk**: If the dispatcher API does not support removal, a workaround (per-plan dispatcher) would require more refactoring. Must verify the llama_index dispatcher API supports `remove_event_handler` before committing to this approach.

---

## Recommendation

**Pursue direction 1 (replace "the options neglect" in the third example) combined with direction 2 (remove the duplicate examples from the Lever field description) in a single PR.**

These are the same two strings in the same file, and fixing them together eliminates the root cause of the secondary template lock while also halving the per-call token cost for examples.

**Specific change:**

In `identify_potential_levers.py`, the third `review_lever` example appears at two locations. Remove it from the Pydantic field description entirely (directions 1+2 together), and replace it in the system prompt with a version that contains no "the options [verb]" phrase:

**Location 1 — `Lever.review_lever` field description (lines 107–118):**

Replace the three quoted examples in the field description with a structural note (no examples). The system prompt (section 4) already carries the examples; having them in the field description too is the source of B2. The `LeverCleaned.review` field (lines 203-205) shows the correct pattern: a comment explaining why no examples are present.

New field description body (replace lines 107-117):
```python
        description=(
            "A short critical review of this lever — name the core tension, "
            "then identify a weakness the options miss. "
            "Do not use square brackets or placeholder text. "
            "See system prompt section 4 for examples."
        )
```

**Location 2 — `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (line 235):**

Replace the third bullet:
```
- "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but the options neglect that a single hurricane season can correlate all three simultaneously."
```
With a domain-specific critique that does not contain any "the options [verb]" pattern:
```
- "Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but a regional hurricane season can correlate all three simultaneously — correlation risk that is absent from every option."
```

**Why first:** The secondary template lock affects llama3.1 at 50–100% depending on plan (100% for gta_game). It degrades review quality for every lever that llama3.1 generates. It is confirmed in two consecutive run batches (89 and 96). The fix is a two-line string replacement with no structural changes. The risk is low (worst case: the model finds a different subphrase to lock on — detectable in the next analysis batch). Directions 3-5 are correct but require validators, schema changes, or dispatcher refactoring that introduce more risk and touch more code.

The `OPTIMIZE_INSTRUCTIONS` already documents this problem. The next natural step is to act on that documentation.

---

## Deferred Items

- **Direction 3 (consequences validator + OPTIMIZE_INSTRUCTIONS entry)**: Worth doing after the template-lock fix. The contamination pattern is persistent but does not cause plan failures — it degrades llama3.1 output quality silently. Adding it to OPTIMIZE_INSTRUCTIONS is a low-effort first step; the validator can follow in a later PR once a safe i18n-robust check is designed.

- **Direction 4 (relax min_length for calls 2 and 3)**: The partial recovery increase (1→4) warrants a second look after more run data. If the pattern persists across the next batch, a `DocumentDetailsLaterCall` schema with `min_length=3` is the cleanest fix.

- **Direction 5 (shared dispatcher fix in runner.py)**: Real bug but only affects side-channel usage logs, not plan outputs. Fix when usage tracking data is needed for cost accounting or audit; not urgent for plan quality.

- **Gemini hong_kong_game instability**: Gemini produced 1/3 calls for hong_kong_game in run 01 (6 levers vs 18 in run 94). This may be non-deterministic model behavior. Monitor across the next batch before treating as a code-level issue.

- **Haiku 3.87× review length ratio**: Elevated but predates PR #339. Worth sampling reviews qualitatively to determine if length reflects substantive analysis or verbose padding. If padding, add a `max_length` hint to the field description or system prompt.

- **S2 (case-sensitive exact deduplication)**: Low severity — downstream `DeduplicateLeversTask` provides semantic deduplication. Mention in a later PR if seen_names misses something observable.
