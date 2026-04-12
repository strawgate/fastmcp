# Workstream 3: Lovable Agent Traces For Logfire And Elastic

You are handling one workstream inside a larger FastMCP telemetry fanout.

Assume you are operating as a principal engineer with full autonomy to investigate this workstream.
You may inspect the repo deeply, run tests, edit files, and use web or doc research when that materially improves the result.

## Objective

Make FastMCP traces fit beautifully into modern agent observability stacks, especially Logfire and Elastic, and prototype the most important code changes that would make the trace experience feel magical.

## Why this workstream exists

Agent practitioners are not bragging about "we instrumented JSON-RPC correctly."
They are bragging about traces that clearly show:

- the overall agent run
- model calls
- tool decisions
- function/tool execution
- downstream HTTP or DB work
- failures, latency, token usage, and cost

FastMCP currently tells part of that story. This workstream should optimize for the experience of reading one end-to-end agent trace in Logfire or Elastic and immediately understanding what happened.

## Mode

- prototype
- investigate + prototype + implement + test
- compare multiple credible approaches before choosing

## Operating assumptions

- You are expected to investigate this like a principal engineer, not merely summarize nearby files.
- Use repo inspection, official docs, and small prototypes as needed.
- Prefer changes that improve trace readability and composability with agent frameworks.
- If the best answer requires an optional mode or config seam, propose and prototype it.

## Required execution checklist

- You MUST read:
  - `src/fastmcp/telemetry.py`
  - `src/fastmcp/client/telemetry.py`
  - `src/fastmcp/server/telemetry.py`
  - `docs/servers/telemetry.mdx`
  - `examples/diagnostics/server.py`
  - `examples/diagnostics/client_with_tracing.py`
- You MUST use these external references:
  - OpenTelemetry MCP semantic conventions
  - official MCP C# SDK outer-tool-span reuse behavior
  - Logfire MCP integration docs
  - Logfire OpenAI / Agents docs
  - Elastic LLM observability docs
  - OpenAI Agents tracing docs
- You MUST explicitly answer whether FastMCP should:
  - reuse outer agent tool spans when possible
  - propagate baggage in addition to trace context
  - stop putting resource URIs in span names by default
- You MUST implement the most convincing subset of those changes, with tests or example validation.

## Required repo context

Read at least these:

- `src/fastmcp/telemetry.py`
- `src/fastmcp/client/telemetry.py`
- `src/fastmcp/server/telemetry.py`
- `docs/servers/telemetry.mdx`
- `examples/run_with_tracing.py`
- `examples/diagnostics/server.py`
- `examples/diagnostics/client_with_tracing.py`
- `tests/client/telemetry/test_client_tracing.py`

External references:

- <https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/>
- <https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.Core/Diagnostics.cs>
- <https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.Core/McpSessionHandler.cs>
- <https://pydantic.dev/docs/logfire/integrations/llms/mcp/>
- <https://pydantic.dev/docs/logfire/integrations/llms/openai/>
- <https://openai.github.io/openai-agents-python/tracing/>
- <https://www.elastic.co/docs/solutions/observability/applications/llm-observability>

## Deliverable

Write one repo-local output at:

`.agents/fanout/otel-fastmcp-2026-04-07/output/03-agent-friendly.md`

Also edit the necessary code or docs in the repo and list the changed files in the final note.

## Constraints

- Optimize for trace readability and composability in real agent stacks.
- Avoid a design that is "correct but joyless."
- Do not turn FastMCP into an agent framework; improve the MCP slice of the trace.

## Success criteria

- The result clearly improves how FastMCP traces would appear inside Logfire or Elastic.
- The proposal is opinionated and implementable.
- The code changes or prototypes materially de-risk the recommendation.

## Decision style

End with:

- `Recommendation: <label>`
- `Primary rationale: <short bullets>`
- `Alternatives considered: <short list>`
- `What would change my mind: <specific evidence>`
