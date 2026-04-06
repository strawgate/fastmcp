"""Shared fixtures for FastMCP benchmarks."""

from __future__ import annotations

import asyncio
from collections.abc import Generator

import pytest

from fastmcp import FastMCP


def _build_server(n_tools: int) -> FastMCP:
    """Create a FastMCP server with *n_tools* trivial echo tools."""
    mcp = FastMCP(f"bench-{n_tools}")
    for i in range(n_tools):

        def _make(idx: int):
            async def _tool(x: str) -> str:
                return f"tool-{idx}: {x}"

            _tool.__name__ = f"tool_{idx}"
            _tool.__doc__ = f"Echo tool {idx}"
            return _tool

        mcp.tool()(_make(i))
    return mcp


@pytest.fixture(scope="module")
def server_1() -> FastMCP:
    return _build_server(1)


@pytest.fixture(scope="module")
def server_10() -> FastMCP:
    return _build_server(10)


@pytest.fixture(scope="module")
def server_100() -> FastMCP:
    return _build_server(100)


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
