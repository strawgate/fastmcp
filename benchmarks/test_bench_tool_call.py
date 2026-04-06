"""Benchmark: tool invocation through the in-memory client."""

from __future__ import annotations

import asyncio

import pytest

from fastmcp import Client, FastMCP


def _build(n: int) -> FastMCP:
    mcp = FastMCP(f"bench-call-{n}")
    for i in range(n):

        def _make(idx: int):
            async def _fn(x: str) -> str:
                return f"{idx}:{x}"

            _fn.__name__ = f"tool_{idx}"
            _fn.__doc__ = f"Tool {idx}"
            return _fn

        mcp.tool()(_make(i))
    return mcp


# ---------------------------------------------------------------------------
# list_tools
# ---------------------------------------------------------------------------

@pytest.mark.benchmark(group="tool-call")
def test_list_tools_10(benchmark):
    """List tools on a 10-tool server via in-memory client."""
    mcp = _build(10)

    async def _run():
        async with Client(mcp) as c:
            return await c.list_tools()

    benchmark.pedantic(lambda: asyncio.get_event_loop().run_until_complete(_run()), rounds=20, warmup_rounds=2)


@pytest.mark.benchmark(group="tool-call")
def test_list_tools_100(benchmark):
    """List tools on a 100-tool server via in-memory client."""
    mcp = _build(100)

    async def _run():
        async with Client(mcp) as c:
            return await c.list_tools()

    benchmark.pedantic(lambda: asyncio.get_event_loop().run_until_complete(_run()), rounds=10, warmup_rounds=1)


# ---------------------------------------------------------------------------
# call_tool
# ---------------------------------------------------------------------------

@pytest.mark.benchmark(group="tool-call")
def test_call_tool_10(benchmark):
    """Call a single tool on a 10-tool server via in-memory client."""
    mcp = _build(10)

    async def _run():
        async with Client(mcp) as c:
            return await c.call_tool("tool_0", {"x": "hello"})

    benchmark.pedantic(lambda: asyncio.get_event_loop().run_until_complete(_run()), rounds=20, warmup_rounds=2)


@pytest.mark.benchmark(group="tool-call")
def test_call_tool_burst_10(benchmark):
    """Call 10 different tools sequentially on a 10-tool server."""
    mcp = _build(10)

    async def _run():
        async with Client(mcp) as c:
            for i in range(10):
                await c.call_tool(f"tool_{i}", {"x": f"msg-{i}"})

    benchmark.pedantic(lambda: asyncio.get_event_loop().run_until_complete(_run()), rounds=10, warmup_rounds=1)
