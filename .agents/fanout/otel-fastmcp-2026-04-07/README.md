# FastMCP OTel Fanout

Date: 2026-04-07

This bundle frames a local/cloud fanout around improving FastMCP's OpenTelemetry story.

## Goal

Produce multiple strong implementation directions for FastMCP telemetry, then compare them and decide what to keep.

## Why now

FastMCP already has real MCP tracing:

- `src/fastmcp/telemetry.py`
- `src/fastmcp/client/telemetry.py`
- `src/fastmcp/server/telemetry.py`
- `src/fastmcp/server/server.py`
- `src/fastmcp/server/providers/fastmcp_provider.py`
- `src/fastmcp/server/providers/proxy.py`

Current strengths:

- client and server spans
- W3C `traceparent` / `tracestate` propagation through MCP `_meta`
- mounted-provider delegation spans
- auth and session attributes

Current gaps versus the MCP semantic conventions and the official C# MCP SDK:

- no MCP metrics
- only a narrow subset of MCP methods are directly instrumented
- missing recommended semconv attributes like `gen_ai.tool.name`, `gen_ai.prompt.name`, `gen_ai.operation.name`, `mcp.protocol.version`, `jsonrpc.request.id`, `error.type`, and `rpc.response.status_code`
- no baggage propagation
- no outer-tool-span reuse to enrich existing agent traces
- resource URI is included in span names by default, which is high-cardinality

## Verification strategy

Primary verification should be deterministic and repo-local:

- use existing pytest-based in-memory span exporter fixtures
- assert concrete span names, attributes, parent/child relationships, and error semantics
- prefer snapshot-like JSON assertions only when they stay stable and readable

Optional secondary verification:

- add a small OTLP smoke path only if it materially improves confidence
- do not make an external collector the main verification loop unless there is a compelling reason

## Inspiration and references

- OpenTelemetry MCP semantic conventions:
  - <https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/>
- Official MCP C# SDK:
  - built-in tracing and metrics
  - outer `execute_tool` span reuse
  - `mcp.session.id`, `mcp.protocol.version`, `gen_ai.tool.name`
- Official MCP Python SDK:
  - built-in tracing, simpler than FastMCP
- Official MCP Go / Java / TypeScript SDKs:
  - mostly middleware or observability hooks, not full native instrumentation
- Logfire MCP integration:
  - <https://pydantic.dev/docs/logfire/integrations/llms/mcp/>
- Logfire OpenAI and Agents integrations:
  - <https://pydantic.dev/docs/logfire/integrations/llms/openai/>
- OpenAI Agents tracing:
  - <https://openai.github.io/openai-agents-python/tracing/>
- Elastic LLM and agentic AI observability:
  - <https://www.elastic.co/docs/solutions/observability/applications/llm-observability>

## Workstreams

- `01-semconv-metrics.prompt.md`
- `02-protocol-surface.prompt.md`
- `03-agent-friendly.prompt.md`
- `04-verification-examples.prompt.md`

## Notes

- The configured Codex Cloud environment on this machine is not for this repo, so these prompts are written to be usable for local worker fanout first.
- If a proper FastMCP cloud environment is added later, these prompts are already self-contained enough to reuse.
