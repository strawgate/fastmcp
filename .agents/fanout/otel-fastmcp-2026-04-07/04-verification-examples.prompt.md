# Workstream 4: Verification Harness And Backend Examples

You are handling one workstream inside a larger FastMCP telemetry fanout.

Assume you are operating as a principal engineer with full autonomy to investigate this workstream.
You may inspect the repo deeply, run tests, edit files, and use web or doc research when that materially improves the result.

## Objective

Create the best verification and demo experience for FastMCP telemetry improvements, with a bias toward tests that agents can run themselves and examples that make Logfire and Elastic feel first-class.

## Why this workstream exists

The user proposed verifying telemetry with an OTel collector printing to a file.
That may be useful as a smoke test, but it is probably not the best primary verification loop for iterative engineering.

This workstream should answer:

- what should be the primary telemetry verification harness for repo development?
- what optional end-to-end smoke path is worth keeping?
- what example or docs changes would make the resulting experience feel lovable?

## Mode

- implementation
- investigate + implement + test
- choose the single best direction after comparing alternatives

## Operating assumptions

- You are expected to investigate this like a principal engineer, not merely summarize nearby files.
- Use repo inspection, tests, docs, and small experiments as needed.
- Prefer deterministic local verification over flaky external-process orchestration unless the latter buys something important.
- Leave behind concrete artifacts that make manual review easy.

## Required execution checklist

- You MUST compare at least these verification strategies:
  - existing in-memory exporter tests
  - OTLP collector writing or printing spans
  - a tiny custom OTLP receiver or capture helper if that is simpler
- You MUST choose one primary strategy and justify it.
- You MUST implement the best near-term verification improvements in the repo.
- You MUST improve at least one example or doc path for Logfire or Elastic if doing so materially improves usability.
- You MUST keep the implementation lightweight and maintainable.

## Required repo context

Read at least these:

- `tests/conftest.py`
- `tests/client/telemetry/test_client_tracing.py`
- `tests/server/telemetry/test_server_tracing.py`
- `docs/servers/telemetry.mdx`
- `examples/run_with_tracing.py`
- `examples/diagnostics/server.py`
- `examples/diagnostics/client_with_tracing.py`

External references:

- <https://pydantic.dev/docs/logfire/integrations/llms/mcp/>
- <https://pydantic.dev/docs/logfire/integrations/llms/openai/>
- <https://www.elastic.co/docs/solutions/observability/applications/llm-observability>
- <https://www.elastic.co/docs/solutions/observability/get-started/opentelemetry/use-cases/llms>

## Deliverable

Write one repo-local output at:

`.agents/fanout/otel-fastmcp-2026-04-07/output/04-verification-examples.md`

Also edit the necessary code or docs in the repo and list the changed files in the final note.

## Constraints

- Keep the verification path runnable by repo contributors and by local/agent workflows.
- Prefer clarity over a fancy but fragile setup.
- If you add an end-to-end smoke path, it should be obviously worth its maintenance cost.

## Success criteria

- There is a clear recommended verification loop.
- The repo gains useful telemetry test or demo improvements.
- The docs/examples make the backend story more concrete, especially for Logfire and Elastic.

## Decision style

End with:

- `Recommendation: <label>`
- `Primary rationale: <short bullets>`
- `Alternatives considered: <short list>`
- `What would change my mind: <specific evidence>`
