"""Benchmark: server mounting (composing servers together)."""

from __future__ import annotations

import pytest

from fastmcp import FastMCP


def _child(name: str, n_tools: int) -> FastMCP:
    child = FastMCP(name)
    for i in range(n_tools):

        def _make(idx: int):
            async def _fn(x: str) -> str:
                return f"{idx}:{x}"

            _fn.__name__ = f"tool_{idx}"
            _fn.__doc__ = f"Tool {idx}"
            return _fn

        child.tool()(_make(i))
    return child


@pytest.mark.benchmark(group="mount")
def test_mount_1_child(benchmark):
    """Mount 1 child server (10 tools each)."""

    def _run():
        parent = FastMCP("parent")
        parent.mount("child_0", _child("child_0", 10))
        return parent

    benchmark(_run)


@pytest.mark.benchmark(group="mount")
def test_mount_5_children(benchmark):
    """Mount 5 child servers (10 tools each)."""

    def _run():
        parent = FastMCP("parent")
        for i in range(5):
            parent.mount(f"child_{i}", _child(f"child_{i}", 10))
        return parent

    benchmark(_run)


@pytest.mark.benchmark(group="mount")
def test_mount_10_children(benchmark):
    """Mount 10 child servers (10 tools each)."""

    def _run():
        parent = FastMCP("parent")
        for i in range(10):
            parent.mount(f"child_{i}", _child(f"child_{i}", 10))
        return parent

    benchmark(_run)
