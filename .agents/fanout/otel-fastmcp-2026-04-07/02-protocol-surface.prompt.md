# Workstream 2: Broaden Protocol Surface Instrumentation

You are handling one workstream inside a larger FastMCP telemetry fanout.

Assume you are operating as a principal engineer with full autonomy to investigate this workstream.
You may inspect the repo deeply, run tests, edit files, and use web or doc research when that materially improves the result.

## Objective

Find and implement the best seam for broadening FastMCP instrumentation beyond the current `tools/call`, `resources/read`, and `prompts/get` paths.

## Why this workstream exists

FastMCP's current telemetry is good but narrow. The trace story becomes much more lovable if agent developers can see more of the real MCP lifecycle:

- initialization and negotiation
- list operations
- notifications and progress
- elicitation
- task-related flows
- proxy/provider hops

The key question is not just "add more spans", but "where is the right layer to instrument so the design stays coherent?"

## Mode

- implementation
- investigate + implement + test
- compare 2-3 credible seam choices before choosing

## Operating assumptions

- You are expected to investigate this like a principal engineer, not merely summarize nearby files.
- Use repo inspection, tests, docs, and web research as needed to produce a grounded result.
- If a lower-level hook is better than adding span wrappers everywhere, prefer the lower-level hook.
- Leave behind code, tests, and a short repo-local memo.

## Required execution checklist

- You MUST read:
  - `src/fastmcp/server/server.py`
  - `src/fastmcp/server/providers/fastmcp_provider.py`
  - `src/fastmcp/server/providers/proxy.py`
  - `src/fastmcp/client/mixins/tools.py`
  - `src/fastmcp/client/mixins/resources.py`
  - `src/fastmcp/client/mixins/prompts.py`
- You MUST inspect how the official MCP Python SDK instruments its lower-level send/handle paths.
- You MUST choose a primary seam and explain why it is better than the nearest alternative.
- You MUST implement at least one meaningful expansion of coverage with tests.
- You MUST avoid a patchwork of one-off wrappers if a cleaner seam exists.

## Required repo context

Read at least these:

- `src/fastmcp/server/server.py`
- `src/fastmcp/server/providers/fastmcp_provider.py`
- `src/fastmcp/server/providers/proxy.py`
- `src/fastmcp/client/mixins/tools.py`
- `src/fastmcp/client/mixins/resources.py`
- `src/fastmcp/client/mixins/prompts.py`
- `tests/client/telemetry/test_client_tracing.py`
- `tests/server/telemetry/test_server_tracing.py`
- `tests/server/telemetry/test_provider_tracing.py`

External references you should use:

- <https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/shared/session.py>
- <https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/lowlevel/server.py>
- <https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/>

## Questions to answer

- Should FastMCP keep instrumentation at its current high-level object boundary, move some of it lower, or use a hybrid?
- Which additional MCP operations create the highest-value trace surface with the least design debt?
- How should provider delegation, remote proxying, and task/progress flows appear in a coherent trace tree?

## Deliverable

Write one repo-local output at:

`.agents/fanout/otel-fastmcp-2026-04-07/output/02-protocol-surface.md`

Also edit the necessary code in the repo and list the changed files in the final note.

## Constraints

- Optimize for framework coherence, not maximal span count.
- Be skeptical of broad instrumentation that creates noisy traces without user value.
- Keep tests focused on observable behavior, not private implementation details.

## Success criteria

- You identify and implement a clean expansion seam.
- The result materially broadens useful coverage.
- The change feels like FastMCP, not a pile of compensating wrappers.

## Decision style

End with:

- `Recommendation: <label>`
- `Primary rationale: <short bullets>`
- `Alternatives considered: <short list>`
- `What would change my mind: <specific evidence>`
