"""Benchmark: stdio transport round-trip.

Starts a real stdio subprocess server and measures tool-call latency.
These tests are heavier — fewer rounds, but measure the real transport path.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time

import pytest

# The inline server script that will be run as a subprocess
_SERVER_SCRIPT = textwrap.dedent("""\
    from fastmcp import FastMCP

    mcp = FastMCP("stdio-bench")

    @mcp.tool()
    async def echo(x: str) -> str:
        return x

    {extra_tools}

    mcp.run(transport="stdio")
""")


def _server_script(n_tools: int = 1) -> str:
    extra = ""
    if n_tools > 1:
        lines = []
        for i in range(1, n_tools):
            lines.append(
                f"@mcp.tool()\\nasync def tool_{i}(x: str) -> str:\\n    return f'{i}:{{x}}'"
            )
        extra = "\n".join(lines)
    return _SERVER_SCRIPT.format(extra_tools=extra)


@pytest.mark.benchmark(group="stdio")
def test_stdio_startup_time(benchmark):
    """Time to start a stdio server process and connect a client."""

    async def _run():
        from fastmcp import Client
        from fastmcp.client.transports import PythonStdioTransport

        # Write server script to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(_server_script(1))
            script_path = f.name

        try:
            transport = PythonStdioTransport(script_path)
            start = time.perf_counter()
            async with Client(transport=transport) as client:
                elapsed = time.perf_counter() - start
                # Verify it works
                tools = await client.list_tools()
                assert len(tools) == 1
            return elapsed * 1000  # ms
        finally:
            os.unlink(script_path)

    result = benchmark.pedantic(
        lambda: asyncio.get_event_loop().run_until_complete(_run()),
        rounds=5,
        warmup_rounds=1,
    )


@pytest.mark.benchmark(group="stdio")
def test_stdio_tool_call_latency(benchmark):
    """Round-trip latency for a single tool call over stdio."""

    async def _run():
        from fastmcp import Client
        from fastmcp.client.transports import PythonStdioTransport

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(_server_script(1))
            script_path = f.name

        try:
            transport = PythonStdioTransport(script_path)
            async with Client(transport=transport) as client:
                start = time.perf_counter()
                result = await client.call_tool("echo", {"x": "bench"})
                elapsed = time.perf_counter() - start
                return elapsed * 1000
        finally:
            os.unlink(script_path)

    benchmark.pedantic(
        lambda: asyncio.get_event_loop().run_until_complete(_run()),
        rounds=5,
        warmup_rounds=1,
    )
