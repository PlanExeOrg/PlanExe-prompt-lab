# RetryConfig Insight

## Did RetryConfig produce any retries in the experiments?

No. All 7 failures in runs 81-87 were structural, not transient:

- **nemotron** (run 81): 0/5 — model can't produce JSON at all. Retries wouldn't help.
- **gpt-oss-20b** (run 83): 1 failure — EOF truncation. Possibly non-deterministic, but same error on retry.
- **haiku** (run 87): 1 failure — produced 8 levers exceeding `max_length=7`. Model behavior, not transient.

`RetryConfig` only retries errors classified as *transient* by `is_transient_error` (API timeouts, network faults). Pydantic validation errors and JSON parse failures are permanent errors that fall through immediately. So the retry code was never actually exercised.

## Conclusion

The PR produced zero observable improvement in this batch. It is "correct defensive infrastructure" — theoretically useful for future network hiccups — but it should not have been merged before confirming it made a difference. No evidence supports keeping it based on these runs alone.
