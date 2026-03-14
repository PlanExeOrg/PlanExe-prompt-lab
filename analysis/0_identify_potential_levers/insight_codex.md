# Insight Codex

## Rankings

Two rankings seem more useful than one here, because the best run for strict drop-in use is not the same as the best run for raw lever richness.

### Best drop-in candidates

1. **Run 01** (`history/0/01_identify_potential_levers`) — strongest full-success balance of compliance and usefulness. It still retried several cases, but the final artifacts are structurally clean and closest to the prompt contract.
2. **Run 09** (`history/0/09_identify_potential_levers`) — richest content by far, with perfect name uniqueness, but three levers violate the exact-3-options rule.
3. **Run 02** (`history/0/02_identify_potential_levers`) — also perfect name uniqueness and strong depth, but it frequently drifts from the required review template (`Trade-off:` instead of `Controls ... vs. ...`) and leaks bracket placeholders.
4. **Run 05** (`history/0/05_identify_potential_levers`) — fast and fully successful, but several consequences drop the required `Immediate:` label and it sometimes copies the prompt example name verbatim.
5. **Run 07** (`history/0/07_identify_potential_levers`) — operationally good, but content quality regresses toward baseline-style duplication.

### Richness-only candidates

1. **Run 09**
2. **Run 04** (only 3/5 cases succeeded, but those 3 are strong)
3. **Run 02**
4. **Run 01**
5. **Run 05**

Runs **03**, **06**, and **08** are unusable because all five cases failed.

## Negative Things

- **Three runs are completely unusable operationally.** Run 03 emits a schema object instead of the expected document payload, producing missing-field errors for `strategic_rationale`, `levers`, and `summary` in `history/0/03_identify_potential_levers/outputs.jsonl:1`. Run 06 fails all five cases because no JSON can be extracted from the model output (`Could not extract json string`) in `history/0/06_identify_potential_levers/outputs.jsonl:1`. Run 08 fails before generation because the configured model name is missing from the local config in `history/0/08_identify_potential_levers/outputs.jsonl:1`.
- **Run 00 leaks placeholders directly into final reviews.** Example: `Controls Trade-off between [Scalability] vs. [Cost Efficiency]` appears in `history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:66`, violating the prompt's prohibition on placeholders and generic scaffolding.
- **Run 02 violates the review template despite otherwise strong content.** The prompt explicitly requires `Controls [Tension A] vs. [Tension B].` in `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`, but Run 02 uses `Trade-off:` forms such as `Trade-off: Governance agility versus stability` in `history/0/02_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`.
- **Run 02 also leaks bracket placeholders in later levers.** Example: `Trade-off: Controls [data richness] vs. [privacy and participant burden]` in `history/0/02_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:66`.
- **Run 05 copies the prompt example name verbatim.** The prompt offers `Material Adaptation Strategy` as an example in `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:19`, and Run 05 reuses it repeatedly in unrelated domains, e.g. `history/0/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4` and `history/0/05_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:4`.
- **Run 05 and Run 07 drift on the required consequence chain labels.** Run 05 omits `Immediate:` in examples like `Choosing a hybrid licensing model will immediately secure rights...` at `history/0/05_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:115`. Run 07 does the same in `history/0/07_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:5`.
- **Run 09 breaks the exact-3-options rule in three levers.** One lever has only one option in `history/0/09_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:83`; two others have four options in `history/0/09_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:116` and `history/0/09_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:139`.
- **Baseline itself is not clean gold.** The baseline repeats names inside the same output set, e.g. `Resource Allocation Strategy` and `Technological Adaptation Strategy` recur multiple times in `baseline/train/20250321_silo/002-10-potential_levers.json:4`, `baseline/train/20250321_silo/002-10-potential_levers.json:26`, `baseline/train/20250321_silo/002-10-potential_levers.json:92`, and `baseline/train/20250321_silo/002-10-potential_levers.json:114`.

## Positive Things

- **Run 01 is the cleanest full-success run.** Its first lever already matches the requested pattern well: a three-stage consequence chain with a measurable effect and a compliant review in `history/0/01_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `history/0/01_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`.
- **Run 02 is the strongest uniqueness improvement over baseline.** It reaches 75 unique names out of 75 levers and 225 unique options out of 225 options, versus the baseline's 52/75 names. It removes the baseline-style repeated lever names entirely.
- **Run 09 produces the most thoughtful reviews and downstream-useful levers.** Example: `Controls Oppression vs. Legitimacy` in `history/0/09_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` goes beyond surface trade-offs and identifies a missing assumption about volunteerism and deception; this is much more synthesis-ready than the baseline's shorter, more generic review at `baseline/train/20250321_silo/002-10-potential_levers.json:11`.
- **Run 04 shows that high-detail outputs are possible without going full Run-09 length.** The successful cases have better average consequence and review depth than baseline, and the sample reviews are strong, e.g. `Controls Schedule Pressure vs. Structural Integrity` in `history/0/04_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`.
- **Runs 01, 02, 05, 07, and 09 all satisfy the raw per-call count requirement when they succeed.** For every successful `002-9-potential_levers_raw.json`, the raw file contains exactly 5 levers. The prompt requirement `EXACTLY 5 levers per response` is therefore being met at the raw-call level even though the final `002-10-potential_levers.json` artifacts contain 15 merged levers.

## Comparison

Relative to the baseline training data, the most interesting lever is **not** simply “make outputs longer.” Baseline already has decent option length and mostly compliant reviews, but it suffers from repeated lever names and uneven specificity. The best history runs improve along different axes:

- **Run 01** improves reliability of final structure over baseline while staying terse enough to be usable. It is not more diverse than the top runs, but it is much safer than Run 09 and cleaner than Run 02.
- **Run 02** is a clear diversity win over baseline: 75/75 unique names and 0 within-file duplicate names. However, it overfits to an alternate review template (`Trade-off:`) and still leaks bracket scaffolding in one project.
- **Run 09** is the biggest content-quality leap over baseline. Its consequences, reviews, and options are all roughly 2x the baseline length, and the reviews surface deeper assumptions. The downside is that some levers become overlong or structurally unstable, causing 3 option-count violations.
- **Run 05** is notable because it is fast and succeeds on all five cases, but its options are much shorter than baseline (61 chars average vs. 150 in baseline), suggesting it may be compressing too aggressively. It also reuses the prompt example name.
- **Run 07** lands close to baseline on duplication problems: both have 52 unique names out of 75 levers, and Run 07 has 21 within-file duplicate names versus 22 in baseline. That makes it look more like a lateral move than an improvement.

Operationally, the runs split into three groups:

- **Reliable full-success runs:** 02, 05, 07, 09.
- **Full-success but retry-heavy/noisy:** 00, 01.
- **Operational failures:** 03, 04, 06, 08.

If I had to isolate likely prompt levers from this step alone, I would focus on the **Run 01 / Run 09 / Run 02 triangle**:

- Run 01 for **format discipline**,
- Run 09 for **depth and challenge to assumptions**,
- Run 02 for **uniqueness and breadth**.

## Quantitative Metrics

### Metric notes

- `Raw=5` checks successful `002-9-potential_levers_raw.json` files against the prompt's per-response rule of exactly 5 levers.
- `Final=15` checks successful `002-10-potential_levers.json` files against the observed baseline/final artifact shape of 15 merged levers per project.
- `Review-format violations` counts reviews that do not match the required `Controls ... vs. ...` pattern.
- `Measurable-outcome misses` counts consequences with no numeric signal (`0-9` or `%`).
- `Template leakage` counts bracket placeholders and direct reuse of the prompt example name.

### Operational metrics

| Set | Model | Success cases | Raw=5 | Final=15 | Mean ok sec | Key failure |
|---|---|---:|---:|---:|---:|---|
| Baseline | n/a | 5/5 | 5/5 | 5/5 | n/a | n/a |
| 00 | `ollama-llama3.1` | 5/5 | 5/5 | 3/5 | 85.9 | timeout |
| 01 | `openrouter-openai-gpt-oss-20b` | 5/5 | 5/5 | 5/5 | 156.5 | empty/non-JSON reply on retries |
| 02 | `openai-gpt-5-nano` | 5/5 | 5/5 | 5/5 | 237.7 | none |
| 03 | `openrouter-z-ai-glm-4-7-flash` | 0/5 | 0/5 | 0/5 | — | schema object emitted |
| 04 | `openrouter-stepfun-step-3-5-flash` | 3/5 | 3/3 | 3/3 | 108.8 | invalid JSON |
| 05 | `openrouter-qwen3-30b-a3b` | 5/5 | 5/5 | 5/5 | 78.2 | none |
| 06 | `openrouter-nvidia-nemotron-3-nano-30b-a3b` | 0/5 | 0/5 | 0/5 | — | empty/non-JSON reply |
| 07 | `openrouter-openai-gpt-4o-mini` | 5/5 | 5/5 | 5/5 | 59.5 | none |
| 08 | `anthropic-claude-haiku-4-5-pinned` | 0/5 | 0/5 | 0/5 | — | model config missing |
| 09 | `anthropic-claude-haiku-4-5-pinned` | 5/5 | 5/5 | 5/5 | 106.5 | none |

### Uniqueness and depth metrics

| Set | Unique names / levers | Unique options / options | Avg consequence chars | Avg review chars | Avg option chars | Duplicate names in-file |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 52/75 | 225/225 | 279.5 | 152.3 | 150.2 | 22 |
| 00 | 66/80 | 215/230 | 193.9 | 134.2 | 74.4 | 9 |
| 01 | 66/75 | 225/225 | 199.8 | 135.2 | 87.6 | 9 |
| 02 | 75/75 | 225/225 | 264.4 | 158.2 | 145.5 | 0 |
| 03 | — | — | — | — | — | — |
| 04 | 45/45 | 135/135 | 297.6 | 234.5 | 167.4 | 0 |
| 05 | 68/75 | 223/225 | 227.1 | 139.4 | 61.1 | 5 |
| 06 | — | — | — | — | — | — |
| 07 | 52/75 | 224/225 | 208.0 | 140.4 | 104.3 | 21 |
| 08 | — | — | — | — | — | — |
| 09 | 75/75 | 225/225 | 596.8 | 387.0 | 295.4 | 0 |

### Constraint-violation and leakage metrics

| Set | Option-count violations | Consequence-chain violations | Measurable-outcome misses | Review-format violations | Template leakage |
|---|---:|---:|---:|---:|---:|
| Baseline | 0 | 5 | 21 | 0 | 0 |
| 00 | 7 | 0 | 72 | 7 | 12 |
| 01 | 0 | 0 | 0 | 0 | 0 |
| 02 | 0 | 0 | 0 | 60 | 5 |
| 03 | — | — | — | — | — |
| 04 | 0 | 0 | 4 | 5 | 0 |
| 05 | 0 | 10 | 0 | 0 | 6 |
| 06 | — | — | — | — | — |
| 07 | 0 | 25 | 0 | 0 | 0 |
| 08 | — | — | — | — | — |
| 09 | 3 | 0 | 3 | 0 | 0 |

### What the numbers mean

- **Run 01** is the cleanest quantitative profile among full-success runs: zero counted violations, no template leakage, and reasonable depth.
- **Run 02** is the uniqueness leader tied with Run 09, but its 60 review-format violations are not a small edge case; they are its dominant failure mode.
- **Run 09** is content-rich enough to matter: average review length rises from 152 chars in baseline to 387 chars, but that richness clearly comes with structural stress.
- **Run 07** proves that full success alone is not enough. Its uniqueness and duplicate-name counts are almost a copy of baseline, so it looks fast but not meaningfully better.
- **Run 00** is a warning that placeholder leakage can survive into final artifacts even when the run “succeeds.”

## Evidence Notes

- **Prompt contract reference:** exact-5 rule at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:4`; example lever name at `...:19`; review template requirement at `...:25`; no-prefix rule at `...:16` and `...:32`.
- **Baseline duplicate-name evidence:** `baseline/train/20250321_silo/002-10-potential_levers.json:4`, `:26`, `:92`, `:114`, `:147`.
- **Run 01 compliant exemplar:** `history/0/01_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5` and `:11`.
- **Run 02 review-template drift:** `history/0/02_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` and `:22`.
- **Run 02 bracket leakage:** `history/0/02_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:66`, `:77`, `:88`, `:99`, `:110`.
- **Run 05 prompt-example leakage:** `history/0/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4`, `:59`, `:114`.
- **Run 05 consequence-label drift:** `history/0/05_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:115` and `history/0/05_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:115`.
- **Run 07 duplicate-name regression:** `history/0/07_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:4`, `:15`, `:48`, `:59`, `:70`, `:103`.
- **Run 09 depth exemplar:** `history/0/09_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11` and `:44`.
- **Run 09 option-count failures:** `history/0/09_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:83`, `history/0/09_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:116`, `history/0/09_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json:139`.
- **Run 03 / 04 / 06 / 08 operational failures:** `history/0/03_identify_potential_levers/outputs.jsonl:1`, `history/0/04_identify_potential_levers/outputs.jsonl:1`, `history/0/06_identify_potential_levers/outputs.jsonl:1`, `history/0/08_identify_potential_levers/outputs.jsonl:1`.

## Questions For Later Synthesis

1. Should the next prompt candidate optimize for **strict formatting** (Run 01) or **assumption-challenging depth** (Run 09), given that this step feeds later consolidation and deduplication?
2. Is the best synthesis path to start from Run 01 and add only a small amount of Run-09-style critique language, rather than adopting Run 09 wholesale?
3. Are the final `002-10` artifacts allowed to contain 15 merged levers by design, or should the analysis and verification machinery also validate the raw `002-9` outputs separately as the true prompt contract surface?
4. Should bracket-placeholder leakage be treated as an automatic hard failure? It appears in Runs 00 and 02 and is very visible to downstream readers.
5. Is there an upper bound on useful verbosity for this step? Run 09 may be objectively better in reasoning depth, but it may also be too long for later stages.

## Prompt Hypotheses

- **H1:** Add an explicit final self-check block requiring the exact review opener `Controls X vs. Y. Weakness:` for every lever. Evidence: Run 02's main failure mode is review-template drift despite otherwise excellent uniqueness and depth (`history/0/02_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`).
- **H2:** Add a hard prohibition against bracketed variables anywhere in the response, not just placeholders like `[specific innovative option]`. Evidence: Run 00 and Run 02 both leak bracket scaffolding into final artifacts (`history/0/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:66`; `history/0/02_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json:66`).
- **H3:** Add `Do not reuse example phrases from this prompt verbatim` near the example lever-name line. Evidence: Run 05 copies `Material Adaptation Strategy` directly into unrelated domains (`history/0/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:4`).
- **H4:** Add a lightweight length target, such as `keep reviews under ~220 characters unless a hidden assumption must be surfaced`, to preserve Run-09-style insight without its structural instability. Evidence: Run 09 has the best content depth but also the only full-success-run option-count failures.
- **H5:** Add an explicit output checklist line: `Count options before finalizing; every lever must have exactly 3 options, no more and no fewer.` Evidence: Run 09 breaks this in three places and Run 00 also drifts on option counts.

## Reflect

The baseline comparison matters here because the baseline is not a perfect target. It already violates some of the stated ideals: repeated lever names, some missing measurable signals, and moderate genericity. That means a run can be materially better than baseline without being perfectly compliant to the prompt. Run 02 is the clearest example: better diversity than baseline, but worse template discipline.

The split between `002-9-potential_levers_raw.json` and `002-10-potential_levers.json` also matters. The prompt says `EXACTLY 5 levers per response`, and the successful raw files do satisfy that. The final files contain 15 levers in baseline and in most successful runs, so future synthesis should be careful not to confuse the raw-call contract with the merged artifact contract.

My bias after reading the artifacts is that **format reliability is easier to add than strategic depth**. That is why Run 09 remains attractive despite its three structural misses. But for the next candidate prompt, I would still start from a Run-01-style compliance base and selectively import Run-09-style review depth.

## Potential Code Changes

- **C1:** Add a post-generation validator/repair step on final lever arrays that enforces exactly 15 merged levers and exactly 3 options per lever before writing `002-10-potential_levers.json`. Evidence: Run 00 writes 16- and 19-lever finals, and Run 09 writes three malformed option arrays.
- **C2:** Add a hard fail/retry when bracket placeholders survive into final fields. Evidence: placeholder leakage in Run 00 and Run 02 survives all the way to the final artifact.
- **C3:** Strengthen JSON extraction and retry routing for models that return empty or malformed text. Evidence: Run 01 retries through empty/non-JSON and invalid JSON before eventually succeeding; Run 04 and Run 06 never recover.
- **C4:** Add model-config preflight validation before scheduling jobs. Evidence: Run 08 wastes all five cases on a missing model alias (`history/0/08_identify_potential_levers/outputs.jsonl:1`).
- **C5:** Add a duplicate-name dedupe/rerank pass on merged outputs. Evidence: baseline and Run 07 both contain large within-output name repetition, which reduces solution-space breadth even when individual levers are valid.

## Summary

The strongest improvement levers are visible in three runs: **Run 01** for formatting discipline, **Run 02** for diversity, and **Run 09** for assumption-challenging depth. The best next prompt should probably combine Run 01's compliance with a constrained slice of Run 09's review style, while explicitly blocking Run 02/00-style template leakage and example copying. On the code side, final-output validation, JSON-recovery retries, placeholder hard-fails, and model-config preflight checks look immediately actionable.
