# Workstream 1: MCP Semconv And Metrics Core

You are handling one workstream inside a larger FastMCP telemetry fanout.

Assume you are operating as a principal engineer with full autonomy to investigate this workstream.
You may inspect the repo deeply, run tests, edit files, and use web or doc research when that materially improves the result.

## Objective

Implement the strongest credible FastMCP telemetry core that closes the biggest gap with the MCP semantic conventions and the official C# MCP SDK.

## Why this workstream exists

FastMCP already emits useful OTel spans, but the core telemetry layer is still below the best MCP-native implementation in the ecosystem.

FastMCP today has:

- client and server spans
- provider delegation spans
- `_meta` trace propagation with `traceparent` and `tracestate`

FastMCP is missing or incomplete on:

- MCP metrics
- several recommended semconv attributes
- richer error tagging
- protocol-version tagging
- better transport metadata

The official C# SDK is the current best MCP-native reference implementation.

## Mode

- implementation
- investigate + implement + test
- compare multiple credible approaches before choosing the final shape

## Operating assumptions

- You are expected to investigate this like a principal engineer, not merely summarize nearby files.
- Use repo inspection, tests, docs, and web research as needed to produce a grounded result.
- If the problem has meaningful design space, compare multiple credible approaches before recommending one.
- Leave behind repo-local artifacts that make the result easy to review during fan-in.
- End with a decisive recommendation and list the changed files.

## Required execution checklist

- You MUST read:
  - `src/fastmcp/telemetry.py`
  - `src/fastmcp/client/telemetry.py`
  - `src/fastmcp/server/telemetry.py`
  - `tests/client/telemetry/test_client_tracing.py`
  - `tests/server/telemetry/test_server_tracing.py`
  - `tests/server/telemetry/test_provider_tracing.py`
- You MUST compare against:
  - OpenTelemetry MCP semantic conventions
  - official MCP C# SDK diagnostics and session handler implementation
- You MUST implement code and tests, not just a memo.
- You MUST decide whether FastMCP should add metrics now and implement them if the repo shape supports it cleanly.
- You MUST prefer deterministic pytest verification over a collector-driven loop.
- After the required work, use your judgment to explore adjacent improvements only if they materially improve the design.

## Required repo context

Read at least these:

- `src/fastmcp/telemetry.py`
- `src/fastmcp/client/telemetry.py`
- `src/fastmcp/server/telemetry.py`
- `src/fastmcp/server/server.py`
- `docs/servers/telemetry.mdx`
- `tests/conftest.py`
- `tests/client/telemetry/test_client_tracing.py`
- `tests/server/telemetry/test_server_tracing.py`
- `tests/server/telemetry/test_provider_tracing.py`

External references you should use:

- <https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/>
- <https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.Core/Diagnostics.cs>
- <https://github.com/modelcontextprotocol/csharp-sdk/blob/main/src/ModelContextProtocol.Core/McpSessionHandler.cs>

## Implementation hypothesis to pressure-test, not blindly obey

The likely good direction is:

- centralize semconv attribute construction in shared helpers
- add missing attributes such as:
  - `gen_ai.tool.name`
  - `gen_ai.prompt.name`
  - `gen_ai.operation.name`
  - `mcp.protocol.version`
  - `jsonrpc.request.id`
  - `error.type`
  - `rpc.response.status_code`
  - transport metadata when available
- add MCP duration histograms if the plumbing can be kept simple and readable

If you find a better shape than this, use it.

## Deliverable

Write one repo-local output at:

`.agents/fanout/otel-fastmcp-2026-04-07/output/01-semconv-metrics.md`

Also edit the necessary code in the repo and list the changed files in the final note.

## Constraints

- Keep the code readable and aligned with FastMCP style.
- Do not add a framework-heavy abstraction if a simple helper layer is enough.
- Fix causes, not symptoms.
- If metrics are too invasive for this workstream, say exactly why and leave a crisp partial implementation or seam.

## Success criteria

- FastMCP gains a materially stronger telemetry core with tests.
- The result is clearly better aligned with MCP semconv and the official C# SDK.
- The implementation is realistic to merge or selectively cherry-pick during fan-in.

## Decision style

End with:

- `Recommendation: <label>`
- `Primary rationale: <short bullets>`
- `Alternatives considered: <short list>`
- `What would change my mind: <specific evidence>`
