# Worker 2: Protocol Surface

Recommendation: hybrid of public boundary spans plus the shared provider seam.

Primary rationale:
- `Provider.list_*` is the cleanest lower-level seam inside FastMCP because every provider, mounted server, proxy provider, and custom provider already funnels through it.
- Public client/server list spans keep the wire story visible and make the trace tree easy to read from the outside in.
- A single provider helper gives one place to represent aggregation, transforms, mounted-server hops, and proxy hops without scattering wrappers across provider subclasses.

What I changed:
- Added server spans for `tools/list`, `resources/list`, `resources/templates/list`, and `prompts/list`.
- Added matching client spans for the raw MCP list calls.
- Added provider spans around shared provider list and task-registration paths.
- Expanded tests to cover client/server list tracing and mounted-provider list hops.

Alternatives considered:
- Instrument only `FastMCPProvider` and `ProxyProvider`: too patchy, and it would miss custom providers.
- Instrument only the public server/client methods: better than nothing, but it hides the provider aggregation hop that is the real seam.
- Push this into the MCP Python SDK: not a FastMCP seam, so it would not solve the repo-local design problem.

What would change my mind:
- If the official MCP Python SDK exposes stable lower-level list/handle hooks that FastMCP can adopt without duplicating span logic, I would move more of the tracing there.
- If we decide the next milestone is protocol coverage for initialize/notifications/progress before list operations, I would shift the next investment toward the MCP session layer rather than more public wrappers.

