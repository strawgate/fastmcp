# Worker 3: Agent-Friendly Trace Recommendation

FastMCP should optimize for the trace shape that agent practitioners actually want: one outer agent run, nested model calls, nested tool decisions, and then a clean MCP slice underneath that is easy to read in Logfire or Elastic.

My recommendation is:

- Reuse outer agent tool spans when possible: yes, for `tools/call` only, when the current span already looks like an `execute_tool ...` span or has `gen_ai.operation.name=execute_tool`.
- Propagate baggage in addition to trace context: yes. Trace context alone links the spans, but baggage is the easiest place to carry useful correlation labels across client, server, and proxy hops.
- Stop putting resource URIs in span names by default: yes. Keep the URI on `mcp.resource.uri`, not in the span name. Resource names get noisy fast and hurt readability in real agent traces.

What I implemented in this worker:

- Tool calls can enrich an existing outer agent span instead of creating a duplicate FastMCP client span.
- Trace propagation now carries arbitrary OTel carrier fields, which makes baggage propagation work end to end.
- Resource reads now use generic span names like `resources/read` across client, server, and proxy paths.
- Delegation for mounted resources uses generic `delegate resource` naming instead of URI-heavy names.
- Tests cover baggage injection/extraction, outer-span reuse for tool calls, and the new resource naming behavior.

Why this feels lovable:

- In Logfire, the agent span stays the hero and FastMCP becomes a well-behaved child rather than a competing top-level trace.
- In Elastic, the same spans stay semconv-friendly and lower-cardinality, which makes dashboards and filtering less noisy.
- The trace stays informative without turning every resource URI into a unique span name.

What I would do next, in priority order:

1. Add MCP operation metrics so latency and failure rates are visible alongside spans.
2. Broaden protocol coverage beyond the current tool/resource/prompt core.
3. Add a small end-to-end demo that shows `OpenAI Agents -> FastMCP -> downstream HTTP` in one trace.

