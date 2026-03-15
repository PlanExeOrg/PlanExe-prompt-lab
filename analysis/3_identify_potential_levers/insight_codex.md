# Insight Codex

## Rankings

- **Tier A:** Run `29` (`openrouter-qwen3-30b-a3b`) and run `28` (`openai-gpt-5-nano`). Run `29` is the best operational candidate: `5/5` plans succeed, it is the fastest fully successful run at `96.2s`, it has `73/75` unique names, and it has zero raw-schema failures. Its weakness is compression: option length falls to `63.1` chars on average and only `45/75` systemic phrases are unique, so many levers feel distinct by title but not by reasoning. Run `28` is the best diversity/depth candidate: `5/5` plans succeed, it reaches `75/75` unique names, and its field lengths stay close to baseline, but it overfits to prompt wording and repeats stock phrases like `25% faster` and `The options fail to consider` across most levers.
- **Tier B:** Run `26` (`ollama-llama3.1`). It is fully successful and cheap-looking operationally (`76.4s` average), but the content collapses: `14` levers have only one option, `59/75` consequences have no numeric measure, and `14` raw reviews repeat across merged outputs.
- **Tier C:** Run `31` (`anthropic-claude-haiku-4-5-pinned`). It shows the richest strategic reasoning, but it is too long and too brittle. It times out on one plan, averages `779.2` chars per consequence and `386.2` per review, and inserts a literal placeholder lever into the final artifact.
- **Tier D:** Runs `25`, `27`, and `30`. These produce some usable files, but their reliability problems are too severe to treat them as prompt wins. The failures are mostly extraction/schema failures rather than subtle quality misses.
- **Tier E:** Run `24`. It never reaches a completed plan and only records start events in `history/0/24_identify_potential_levers/events.jsonl:1`.

## Negative Things

- Reliability is still the biggest blocker. Run `25` completes only `1/5` plans and fails the others with extraction errors in `history/0/25_identify_potential_levers/outputs.jsonl:1` and `history/0/25_identify_potential_levers/outputs.jsonl:4`. Run `27` fails on invalid JSON and EOF-truncated JSON in `history/0/27_identify_potential_levers/outputs.jsonl:1` and `history/0/27_identify_potential_levers/outputs.jsonl:5`. Run `30` fails two plans because the model returned `levers` but omitted required `strategic_rationale` and `summary` fields in `history/0/30_identify_potential_levers/outputs.jsonl:1` and `history/0/30_identify_potential_levers/outputs.jsonl:5`. Run `31` times out after `427.06` seconds on `20260311_parasomnia_research_unit` in `history/0/31_identify_potential_levers/outputs.jsonl:5`.
- Prompt-template leakage is obvious in run `28`. The prompt gives exact stock phrasings at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:9`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:10`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`, and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:26`; run `28` copies that mold almost verbatim in `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`, `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`, `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`, and `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`.
- Run `26` often satisfies the outer JSON structure while violating the actual task. The prompt requires exactly three options per lever at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:5`, but `Digital Identity Standards`, `Coalition Building`, and `Procurement Intervention` each have only one option in `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`, `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:24`, and `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:33`.
- Run `31` shows a new failure mode: the model emits compliance meta-text as content. The final output literally includes `Placeholder Removed - Framework Compliance` with `Removed` options and a `Structural compliance marker` review at `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:59` and `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:66`. The same file also contains a one-option lever at `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:158`.
- Run `29` looks clean on exact uniqueness, but its options are often label-like and the consequences miss the mandated `Immediate: ... → Systemic: ... → Strategic: ...` chain. The first GTA lever has short option strings and a consequence that starts without `Immediate:` in `history/0/29_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:5` and `history/0/29_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json:7`.

## Positive Things

- Run `29` is the strongest all-around operational run in this batch. It completes `5/5` plans, has zero raw-schema issues, zero cross-call duplicate names, and retains high exact uniqueness (`73/75` names, `75/75` reviews).
- Run `28` is the strongest diversity/depth run. It also completes `5/5` plans, achieves `75/75` unique names, and its average consequence/review lengths (`270.3` / `149.4`) stay close to baseline (`279.5` / `152.3`) while maintaining full option-count compliance.
- Run `26` proves that a cheaper local-style model can stay structurally alive across all five plans. That makes it useful as a validator target: if code-side checks were stronger, a run like this could be repaired rather than discarded.
- The baseline training data is still a useful depth anchor. Baseline option length (`150.2`) and consequence length (`279.5`) remain a better target than the compressed run `29` outputs or the overgrown run `31` outputs.

## Comparison

### Comparison to baseline training data

- The baseline is not a perfect gold set. Across the five training plans it has only `52/75` exact-unique names and `22` cross-call duplicate raw names, so later runs should not be penalized just for exceeding baseline novelty. `Resource Allocation Strategy` and `Technological Adaptation Strategy` repeat within the silo baseline file at `baseline/train/20250321_silo/002-10-potential_levers.json:4`, `baseline/train/20250321_silo/002-10-potential_levers.json:26`, `baseline/train/20250321_silo/002-10-potential_levers.json:92`, `baseline/train/20250321_silo/002-10-potential_levers.json:114`, and `baseline/train/20250321_silo/002-10-potential_levers.json:147`.
- Run `28` and run `29` both beat baseline exact uniqueness, but in different ways. Run `28` is longer and more decision-useful; run `29` is cleaner operationally but compresses options so hard that it often reads like a title generator with a thin rationale layer.
- Run `26` beats baseline uniqueness too (`74/75` names), but that is misleading. Its reviews and consequences recycle a much smaller set of phrases, and it violates the three-option contract frequently. This is a case where exact uniqueness overstates actual breadth.
- Baseline itself misses some of the current prompt contract: `21/75` baseline consequences contain no numeric measure and `5/75` miss the exact chain pattern. That means prompt optimization should aim to improve on baseline, not merely imitate it.
- The major qualitative split is now clearer than in earlier batches: some models fail operationally before content matters (`24`, `25`, `27`, `30`), some are structurally alive but shallow (`26`, partly `29`), and some are rich but overlong (`31`). The main two prompt-relevant candidates are `28` and `29`.

## Quantitative Metrics

Metrics below were computed from `baseline/train/*/002-10-potential_levers.json`, `baseline/train/*/002-9-potential_levers_raw.json`, and the corresponding `history/0/24..31_identify_potential_levers/outputs/*/002-10-potential_levers.json` and `002-9-potential_levers_raw.json` artifacts.

### Operational / structural

| Run | Model | Plans ok | Final plans | Avg sec | Raw schema issues | Missing plans |
|---|---|---:|---:|---:|---:|---|
| baseline | baseline | 5/5 | 5/5 | — | 0 | — |
| 24 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 0/5 | 0/5 | — | 0 | 20250321_silo, 20250329_gta_game, 20260308_sovereign_identity, 20260310_hong_kong_game, 20260311_parasomnia_research_unit |
| 25 | openrouter-nvidia-nemotron-3-nano-30b-a3b | 1/5 | 1/5 | 146.7 | 0 | 20250329_gta_game, 20260308_sovereign_identity, 20260310_hong_kong_game, 20260311_parasomnia_research_unit |
| 26 | ollama-llama3.1 | 5/5 | 5/5 | 76.4 | 0 | — |
| 27 | openrouter-openai-gpt-oss-20b | 2/5 | 2/5 | 132.0 | 0 | 20260308_sovereign_identity, 20260310_hong_kong_game, 20260311_parasomnia_research_unit |
| 28 | openai-gpt-5-nano | 5/5 | 5/5 | 228.7 | 0 | — |
| 29 | openrouter-qwen3-30b-a3b | 5/5 | 5/5 | 96.2 | 0 | — |
| 30 | openrouter-openai-gpt-4o-mini | 3/5 | 3/5 | 39.8 | 0 | 20260308_sovereign_identity, 20260311_parasomnia_research_unit |
| 31 | anthropic-claude-haiku-4-5-pinned | 4/5 | 4/5 | 171.0 | 1 | 20260311_parasomnia_research_unit |

Interpretation: reliability is still highly model-sensitive. Only runs `26`, `28`, and `29` are full-corpus prompt candidates; the others are mainly evidence for code hardening.

### Uniqueness

| Run | Unique names | Unique reviews | Unique systemic phrases | Cross-call dup names | Cross-call dup reviews |
|---|---:|---:|---:|---:|---:|
| baseline | 52/75 | 75/75 | 75/75 | 22 | 0 |
| 24 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| 25 | 15/15 | 15/15 | 15/15 | 0 | 0 |
| 26 | 74/75 | 61/75 | 54/75 | 0 | 14 |
| 27 | 30/30 | 30/30 | 30/30 | 0 | 0 |
| 28 | 75/75 | 71/75 | 75/75 | 0 | 4 |
| 29 | 73/75 | 75/75 | 45/75 | 0 | 0 |
| 30 | 44/45 | 45/45 | 45/45 | 0 | 0 |
| 31 | 61/61 | 61/61 | 60/61 | 0 | 0 |

Interpretation: exact uniqueness alone is not enough. Run `26` looks strong on names, but its duplicated reviews and repeated reasoning patterns make it weaker than run `28`. Run `29` also shows that unique names can coexist with low reasoning diversity (`45/75` unique systemic phrases).

### Average field lengths

| Run | Avg name chars | Avg consequence chars | Avg option chars | Avg review chars | Avg radical option chars |
|---|---:|---:|---:|---:|---:|
| baseline | 27.7 | 279.5 | 150.2 | 152.3 | 179.3 |
| 24 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 25 | 29.7 | 217.8 | 75.2 | 151.9 | 89.5 |
| 26 | 30.7 | 166.7 | 95.6 | 146.4 | 95.2 |
| 27 | 29.9 | 217.3 | 62.8 | 131.9 | 83.6 |
| 28 | 43.9 | 270.3 | 126.6 | 149.4 | 147.0 |
| 29 | 30.6 | 253.3 | 63.1 | 136.5 | 66.7 |
| 30 | 29.5 | 229.0 | 95.9 | 145.9 | 106.8 |
| 31 | 46.6 | 779.2 | 318.7 | 386.2 | 334.7 |

Interpretation: run `28` is the closest to baseline depth. Run `29` is too terse in the option field. Run `31` is not just “better because longer”; it is far outside the baseline operating envelope and correlates with timeout risk.

### Constraint violations

| Run | Option-count violations | Consequence chain violations | No numeric consequence | Review opener violations | Missing `Weakness:` | Placeholders |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0 | 5 | 21 | 0 | 0 | 0 |
| 24 | 0 | 0 | 0 | 0 | 0 | 0 |
| 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| 26 | 14 | 0 | 59 | 7 | 8 | 0 |
| 27 | 0 | 0 | 0 | 0 | 0 | 0 |
| 28 | 0 | 31 | 0 | 0 | 0 | 0 |
| 29 | 0 | 45 | 7 | 0 | 0 | 0 |
| 30 | 0 | 15 | 0 | 0 | 0 | 0 |
| 31 | 1 | 16 | 1 | 1 | 1 | 1 |

Interpretation: the prompt currently creates two different failure clusters: short-form collapse (`26`) and over-creative format drift (`28`, `29`, `31`). Code-side validation would catch both.

### Template leakage / robotic phrasing

| Run | `The options fail to consider` | `25% faster` | Generic suffix names | Radical hype-token options | `Controls ...` reviews | `Trade-off:` reviews |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 8 | 3 | 60 | 32 | 75 | 0 |
| 24 | 0 | 0 | 0 | 0 | 0 | 0 |
| 25 | 0 | 1 | 7 | 7 | 15 | 0 |
| 26 | 53 | 2 | 40 | 22 | 68 | 0 |
| 27 | 13 | 6 | 11 | 18 | 30 | 0 |
| 28 | 69 | 72 | 32 | 61 | 0 | 75 |
| 29 | 5 | 8 | 53 | 36 | 75 | 0 |
| 30 | 3 | 3 | 29 | 15 | 45 | 0 |
| 31 | 0 | 2 | 27 | 33 | 60 | 0 |

Interpretation: run `28` is the clearest prompt-leakage run; run `29` avoids the exact phrases but still leans hard on generic lever suffixes and hype-heavy radical options. Baseline itself is suffix-heavy, so uniqueness gains should be judged against that caveat.

## Evidence Notes

- Prompt wording seems to induce leakage directly. The prompt’s example strings for consequence/review format appear at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:9`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:10`, `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:25`, and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:26`.
- Run `28` mirrors that wording with unusually high consistency at `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5`, `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:11`, `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:16`, and `history/0/28_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:22`.
- Run `26` demonstrates that merged files can look superficially valid while violating the core option-count contract at `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`, `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:24`, and `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:33`.
- Run `30` is the strongest evidence that code should reject partial raw objects before trying to merge them; it fails specifically on missing `strategic_rationale` and `summary` at `history/0/30_identify_potential_levers/outputs.jsonl:1`.
- Run `31` is the strongest evidence for post-merge sanitization; the placeholder lever is already in the final file at `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:59`.
- Baseline should be treated as reference output, not as a flawless gold standard, because it contains repeated lever names in `baseline/train/20250321_silo/002-10-potential_levers.json:4` and `baseline/train/20250321_silo/002-10-potential_levers.json:114`.

## Questions For Later Synthesis

- Should the next candidate optimize first for reliability (`29`) or for richness (`28`) if only one prompt variant is tested next?
- Should `Trade-off:` be accepted as an allowed review opener, or should synthesis insist on the exact `Controls X vs. Y.` form from the prompt?
- Is baseline uniqueness too weak to use as the main success metric for this step, given the repeated names in the training corpus?
- Should the system prefer code-side repair/validation before more prompt iteration, since several failures (`25`, `27`, `30`, `31`) are parser/schema failures rather than genuine idea-generation failures?

## Reflect

- The highest-leverage finding is that prompt improvements alone are unlikely to stabilize this step. Five of the eight runs show failures that a better validator/retry loop could probably catch or repair.
- The second highest-leverage finding is that the prompt’s exact sample wording appears to be over-copied. This is not just surface style drift; it narrows the strategic texture of the lever set.
- The best next experiment is probably a blended prompt derived from runs `28` and `29`: preserve `29`’s completion behavior, restore `28`’s option depth, and explicitly ban reuse of sample phrases.
- I would not use raw exact uniqueness as the lead metric in synthesis. It should be paired with at least one reasoning-diversity metric such as unique systemic-phrase count or repeated-review count.

## Prompt Hypotheses

- **H1:** Remove or diversify the literal sample phrasings in the prompt, and add an explicit rule: `Do not reuse sample wording such as '25% faster scaling' or 'The options fail to consider' across multiple levers.` Evidence: the wording appears in the prompt at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:10` and `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:26`, then explodes in run `28` (`72` uses of `25% faster`, `69` uses of `The options fail to consider`). Expected effect: lower template leakage while keeping the same structural discipline.
- **H2:** Add an explicit self-check before finalizing each lever: `If any lever has fewer or more than 3 options, regenerate that lever only.` Evidence: the prompt requires three options at `prompts/identify_potential_levers/prompt_0_fa5dfb88099db534ef065c73c38934677aec67b938a4e0be7dfa8acd5497e316.txt:5`, but run `26` still emits repeated one-option levers in `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15` and `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:33`. Expected effect: fewer shallow but syntactically acceptable merged artifacts.
- **H3:** Add a length target: `Keep each consequence under ~320 chars and each review under ~220 chars unless a critical trade-off would be lost.` Evidence: run `31` averages `779.2` consequence chars and times out on one plan in `history/0/31_identify_potential_levers/outputs.jsonl:5`. Expected effect: reduce timeout/verbosity failures without forcing the very short option style seen in run `29`.
- **H4:** Add a diversity instruction tied to reasoning, not just names: `Across the 15 merged levers, vary the systemic mechanism and do not repeat the same percentage or same review stem more than twice.` Evidence: run `28` has perfect exact name uniqueness yet still reuses the same `25% faster` mechanism in most consequences, while run `26` repeats review stems heavily. Expected effect: improve semantic breadth instead of only title breadth.

## Potential Code Changes

- **C1:** Validate raw `DocumentDetails` before merge and retry on missing `strategic_rationale`, missing `summary`, wrong response count, or wrong per-response lever count. Evidence: run `30` fails on missing `strategic_rationale` and `summary` in `history/0/30_identify_potential_levers/outputs.jsonl:1`, and run `31` contains a `6`-lever response in raw output leading to `16` final levers. Expected effect: convert partial-schema failures into either retries or explicit rejects.
- **C2:** Add extraction repair for truncated or non-extractable JSON, followed by one constrained retry. Evidence: run `25` fails with `Could not extract json string from output` in `history/0/25_identify_potential_levers/outputs.jsonl:1`, and run `27` fails with trailing-character / EOF JSON errors in `history/0/27_identify_potential_levers/outputs.jsonl:1` and `history/0/27_identify_potential_levers/outputs.jsonl:5`. Expected effect: recover some currently lost runs without prompt changes.
- **C3:** Add a post-merge sanitizer that rejects placeholder/meta entries and any lever whose option count is not exactly `3`. Evidence: run `31` writes a literal compliance placeholder into the final artifact at `history/0/31_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:59`, and run `26` lets one-option levers through at `history/0/26_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json:15`. Expected effect: prevent clearly invalid content from reaching later pipeline stages.
- **C4:** Add a repetition scorer across the merged 15-lever artifact, with penalties for repeated review stems, repeated numeric templates, and repeated hype-token radical options. Evidence: run `28` overuses `25% faster` and `The options fail to consider`, run `26` repeats review text, and baseline itself has repeated names, so simple exact-name dedupe is not enough. Expected effect: better semantic coverage and lower robotic feel.
- **C5:** Track at least two quality metrics in the runner summary: exact structural compliance and reasoning diversity. Evidence: run `29` looks strong on exact uniqueness but weak on systemic-phrase diversity; run `26` looks diverse on names but weak on real option breadth. Expected effect: later synthesis can avoid over-optimizing to the wrong proxy.

## Summary

- The prompt has two viable directions in this batch: run `29` for reliability and run `28` for richness.
- The biggest practical problems are still code-side: extraction failure, partial raw objects, and post-merge invalid content.
- The most important prompt issue is template leakage from the prompt’s own sample phrasing.
- My recommendation for the next round is: keep run `29` as the operational base, borrow depth cues from run `28`, explicitly de-template the prompt, and add validator/sanitizer code before spending another round on pure prompt tuning.
