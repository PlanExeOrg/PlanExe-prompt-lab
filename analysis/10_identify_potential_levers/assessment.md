# Assessment: Post-merge quality gate for lever validation (PR #281)

## Verdict: NO

This iteration was a disaster. PR #281 added a quality gate that checked for the
presence of hardcoded English keywords ("Controls", "Weakness:") in lever fields
to detect cross-field contamination. The idea was to catch qwen3-30b's tendency
to leak review text into the `consequences` field.

The problem: **PlanExe users create plans in many languages.** Hardcoded checks
for specific English words will silently break for any non-English plan. A user
writing a plan in German, Japanese, or Portuguese would never trigger the filter
— and conversely, a legitimate English-language lever that happens to mention
"Controls" in its consequences would be wrongly rejected.

## Impact on runs 74-80

The keyword-based filter destroyed qwen3-30b's output: run 78 went from ~75
levers down to only 15 (60 levers filtered out). This is the opposite of the
intended effect — the gate was supposed to improve quality, but instead it
silently discarded 80% of a model's output.

The runs also used prompt_2 (naming template removed + "5 to 7" lever count),
which makes the data a mix of two changes. The prompt_2 effect was positive
(Strategy suffix dropped from 83-100% to 2-10%), but the quality gate effect
was destructive.

## What was reverted

PR #282 removed the keyword-based checks, keeping only the language-agnostic
duplicate name filter. The duplicate name check is safe because it compares
lever names against each other, not against hardcoded strings.

## Lesson learned

Any validation logic in PlanExe must be language-agnostic. Structural checks
(duplicate detection, field length ratios, count assertions) are acceptable.
Keyword matching against English words is not — it creates a hidden English-only
assumption that breaks internationalization.

## Runs

| Run | Model | Plans | Levers | Notes |
|-----|-------|-------|--------|-------|
| 74 | nemotron | 0/5 | 0 | 9th consecutive failure |
| 75 | llama3.1 | 5/5 | 96 | Strategy suffix 10% (prompt_2 working) |
| 76 | gpt-oss-20b | 5/5 | 89 | Strategy suffix 2% |
| 77 | gpt-5-nano | 5/5 | 89 | Strategy suffix 2% |
| 78 | qwen3-30b | 5/5 | 15 | **60 levers filtered by keyword gate** |
| 79 | gpt-4o-mini | 5/5 | 87 | Strategy suffix 9% |
| 80 | haiku | 3/5 | 63 | Strategy suffix 7%, hong_kong_game failed (max_length=7 exceeded) |

## Positive signal buried in the data

Despite the quality gate disaster, the prompt_2 change (naming template removed)
shows a clear win: Strategy suffix dropped dramatically across all models compared
to iteration 9. This confirms PR #279 was effective — it just needs to be measured
in a clean run without the keyword gate interfering.
