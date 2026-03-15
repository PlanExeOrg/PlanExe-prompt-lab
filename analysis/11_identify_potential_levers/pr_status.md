# Status: PR 283

PR #283 adds `RetryConfig()` to `LLMExecutor` in `prompt_optimizer/runner.py` so transient LLM API or network failures get up to 2 retries with exponential backoff.

## Are the models outputting better responses?

No. The success rate is unchanged: 28/35 (80%) in both iteration 10 and iteration 11.

| Run | Model | Before (iter 10) | After (iter 11) |
|-----|-------|-------------------|-----------------|
| nemotron | 0/5 | 0/5 | 0/5 |
| llama3.1 | 5/5 | 5/5 | 5/5 |
| gpt-oss-20b | 5/5 | 5/5 | 4/5 |
| gpt-5-nano | 5/5 | 5/5 | 5/5 |
| qwen3-30b | 5/5 | 5/5 | 5/5 |
| gpt-4o-mini | 5/5 | 5/5 | 5/5 |
| haiku | 3/5 | 4/5 | 4/5 |

No retries were observed. All 7 failures in runs 81-87 were structural, not transient:

- **nemotron** (run 81): 0/5 — model can't produce JSON at all. Retries wouldn't help.
- **gpt-oss-20b** (run 83): 1 failure — EOF truncation. Possibly non-deterministic, but same error on retry.
- **haiku** (run 87): 1 failure — produced 8 levers exceeding `max_length=7`. Model behavior, not transient.

`RetryConfig` only retries errors classified as *transient* by `is_transient_error` (API timeouts, network faults). Pydantic validation errors and JSON parse failures are permanent errors that fall through immediately. The retry code was never exercised.

## Is the content of the responses better?

No measurable change. The content quality is identical — the PR only affects error handling, not prompt or schema.

## Verdict

**No significant improvement.** The PR produced zero observable benefit in this batch. It should not have been merged before confirming it made a difference.
