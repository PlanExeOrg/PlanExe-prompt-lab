# Investigation: strategic_rationale and llama3.1

## Question

llama3.1 outputs in iter 41 have `strategic_rationale: null`. Did it used to produce
this field, and were outputs better when it did?

## Findings

### When did llama3.1 stop producing strategic_rationale?

llama3.1 produced `strategic_rationale` 100% of the time in early runs, then stopped
at run 0/33. Something changed between run 0/26 and 0/33 (a prompt or schema change)
that made llama3.1 skip the Optional field.

| Run | strategic_rationale present | null |
|-----|---------------------------|------|
| 0/00 | 15 | 0 |
| 0/16 | 15 | 0 |
| 0/18 | 15 | 0 |
| 0/26 | 15 | 0 |
| **0/33** | **0** | **15** |
| 0/40 | 0 | 15 |
| ... all subsequent runs ... | 0-3 | 11-15 |

Likely cause: Ollama's structured output mode prioritizes required fields. As the
schema grew (more fields, longer descriptions from prompt improvements), llama3.1
started skipping the `Optional[str] = Field(default=None)` field to stay within
its token budget.

### Other models still produce strategic_rationale

| Model | present | null |
|-------|---------|------|
| llama3.1 (run 87) | 0 | 14 |
| gpt-oss-20b (run 88) | 15 | 0 |
| gpt-5-nano (run 89) | 15 | 0 |
| qwen3-30b (run 90) | 15 | 0 |
| gpt-4o-mini (run 91) | 10 | 5 |
| gemini-2.0-flash (run 92) | 15 | 0 |
| haiku-4-5 (run 93) | 13 | 0 |

### Was llama3.1 output better with strategic_rationale?

**No clear evidence that strategic_rationale improved llama3.1 output quality.**
The prompt improvements made across iterations 23-40 matter far more.

| Metric | Early (SR=yes, runs 0/00-0/26) | Recent (SR=no, runs 2/52-2/94) |
|--------|-------------------------------|-------------------------------|
| Review length | 134-146 chars | 207-211 chars |
| Consequences length | 167-194 chars | 144-197 chars |
| Option length | 74-96 chars (~14-17 words) | 100-105 chars (~18-19 words) |
| Short options (<12 words) | 37-73% | 33-42% |
| Template lock | 100% "Controls X vs Y" | ~0% (eliminated by prompt fixes) |
| Lever names | Generic ("Talent Acquisition Strategy") | Domain-specific ("Urban Canvas", "Criminal Economies") |

Early runs had strategic_rationale but also had:
- Heavy "Controls X vs Y. Weakness: The options fail to..." template lock
- Shorter, more label-like options
- Generic lever names

Recent runs have no strategic_rationale but produce:
- Longer, more substantive reviews
- Better option content (full sentences)
- Domain-specific lever names

**Conclusion:** The quality gains are from better examples and field descriptions
(iterations 23-40 prompt improvements), not from chain-of-thought via
strategic_rationale. For llama3.1 specifically, the field is inert — it doesn't
generate it, and output quality improved without it.

For cloud models (gpt-oss-20b, gpt-5-nano, qwen3, gemini, haiku), strategic_rationale
is still actively generated and likely contributes to their higher output quality.
Do not remove it from the schema — it benefits the models that use it.
