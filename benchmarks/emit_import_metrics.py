"""Emit import-time benchmark results as OTLP metrics to the monitor collector.

Usage:
    python benchmarks/emit_import_metrics.py import-bench.json

Reads the JSON output of scripts/benchmark_imports.py and sends each result
as a gauge metric to the OTLP HTTP endpoint specified by $OTLP_ENDPOINT.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request


def sanitize_name(label: str) -> str:
    """Convert a human label to a valid metric name."""
    name = label.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return f"import_{name}"


def emit_metric(endpoint: str, name: str, value: float, group: str) -> None:
    """Send a single OTLP gauge metric."""
    body = json.dumps(
        {
            "resourceMetrics": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "benchkit.run.kind",
                                "value": {"stringValue": "code"},
                            }
                        ]
                    },
                    "scopeMetrics": [
                        {
                            "scope": {"name": "fastmcp-benchmarks"},
                            "metrics": [
                                {
                                    "name": name,
                                    "unit": "ms",
                                    "gauge": {
                                        "dataPoints": [
                                            {
                                                "asDouble": value,
                                                "attributes": [
                                                    {
                                                        "key": "benchkit.scenario",
                                                        "value": {
                                                            "stringValue": group
                                                        },
                                                    },
                                                    {
                                                        "key": "benchkit.direction",
                                                        "value": {
                                                            "stringValue": "smaller_is_better"
                                                        },
                                                    },
                                                ],
                                            }
                                        ]
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )
    req = urllib.request.Request(
        f"{endpoint}/v1/metrics",
        data=body.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)  # noqa: S310 — trusted CI endpoint


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: emit_import_metrics.py <import-bench.json>", file=sys.stderr)
        sys.exit(1)

    endpoint = os.environ.get("OTLP_ENDPOINT", "http://localhost:4318")

    with open(sys.argv[1]) as f:
        results = json.load(f)

    for r in results:
        median = r.get("median_ms")
        if median is None:
            continue
        name = sanitize_name(r["label"])
        group = r.get("group", "import")
        emit_metric(endpoint, name, median, group)
        print(f"  {name}={median}ms (group={group})")


if __name__ == "__main__":
    main()
