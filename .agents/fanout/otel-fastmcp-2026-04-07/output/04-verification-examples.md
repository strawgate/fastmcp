# Verification And Examples Recommendation

Primary recommendation: keep `pytest` + `InMemorySpanExporter` as the day-to-day verification loop.

Why:

- It is deterministic and fast.
- It already covers the behaviors we care about most: span names, attributes, hierarchy, and error status.
- It avoids introducing a second moving part just to verify telemetry.

What I changed:

- Added a shared example helper at `examples/tracing_setup.py` that can configure either console export or OTLP export.
- Updated `examples/run_with_tracing.py` and `examples/diagnostics/client_with_tracing.py` to support `FASTMCP_TRACE_EXPORTER=console`.
- Added tests for the helper selection logic in `tests/examples/test_tracing_setup.py`.
- Updated `docs/servers/telemetry.mdx` to recommend in-memory tests first and console export as the lightweight smoke path.

Strategy comparison:

- `InMemorySpanExporter` tests: best primary loop.
- OTLP collector printing to a file: useful as an end-to-end smoke test, but too much setup for the main inner loop.
- Tiny custom OTLP receiver: technically possible, but it adds complexity without beating the in-memory approach for most repo work.

Secondary recommendation:

- Keep an OTLP smoke path for final backend validation and vendor demos.
- Prefer `FASTMCP_TRACE_EXPORTER=console` for local eyeballing before reaching for a collector.

What would change my mind:

- If we need to validate exporter-specific serialization or transport behavior that in-memory tests cannot exercise.
- If a backend integration starts depending on collector-only behavior that cannot be covered by the example helper.

Tests run:

- `uv run pytest tests/examples/test_tracing_setup.py tests/telemetry/test_module.py tests/client/telemetry/test_client_tracing.py tests/server/telemetry/test_server_tracing.py tests/server/telemetry/test_provider_tracing.py -n auto`
- `uv run ruff check examples/run_with_tracing.py examples/diagnostics/client_with_tracing.py examples/tracing_setup.py tests/examples/test_tracing_setup.py`
