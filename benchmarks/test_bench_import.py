"""Benchmark: import time for `from fastmcp import FastMCP`.

Uses pytest-benchmark to measure cold-import in a subprocess (matching the
existing scripts/benchmark_imports.py pattern) and warm-import via importlib
reload.
"""

from __future__ import annotations

import importlib
import subprocess
import sys

import pytest


def _cold_import_ms() -> float:
    """Measure cold import in a fresh subprocess (no module cache)."""
    code = (
        "import time as _t; _s=_t.perf_counter(); "
        "from fastmcp import FastMCP; "
        "print(f'{(_t.perf_counter()-_s)*1000:.4f}')"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    return float(r.stdout.strip())


@pytest.mark.benchmark(group="import")
def test_cold_import(benchmark):
    """Cold import of `from fastmcp import FastMCP` in a subprocess."""
    result = benchmark.pedantic(_cold_import_ms, rounds=5, warmup_rounds=1)
    # Sanity: under 5 seconds even on slow CI
    assert result < 5000


@pytest.mark.benchmark(group="import")
def test_warm_import(benchmark):
    """Warm (cached) import — measures importlib overhead only."""

    def _warm():
        import fastmcp

        importlib.reload(fastmcp)

    benchmark.pedantic(_warm, rounds=20, warmup_rounds=2)
