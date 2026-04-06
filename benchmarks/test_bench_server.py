"""Benchmark: FastMCP server construction and tool registration."""

from __future__ import annotations

import pytest

from fastmcp import FastMCP


def _create_server_with_n_tools(n: int) -> FastMCP:
    """Create a server and register *n* tools via the decorator."""
    mcp = FastMCP(f"bench-{n}")
    for i in range(n):

        def _make(idx: int):
            async def _fn(x: str) -> str:
                return f"{idx}:{x}"

            _fn.__name__ = f"tool_{idx}"
            _fn.__doc__ = f"Tool {idx}"
            return _fn

        mcp.tool()(_make(i))
    return mcp


@pytest.mark.benchmark(group="server-construction")
def test_server_create_empty(benchmark):
    """Create an empty FastMCP server."""
    benchmark(FastMCP, "empty")


@pytest.mark.benchmark(group="server-construction")
def test_server_create_1_tool(benchmark):
    """Create a server and register 1 tool."""
    benchmark(_create_server_with_n_tools, 1)


@pytest.mark.benchmark(group="server-construction")
def test_server_create_10_tools(benchmark):
    """Create a server and register 10 tools."""
    benchmark(_create_server_with_n_tools, 10)


@pytest.mark.benchmark(group="server-construction")
def test_server_create_100_tools(benchmark):
    """Create a server and register 100 tools."""
    benchmark(_create_server_with_n_tools, 100)
