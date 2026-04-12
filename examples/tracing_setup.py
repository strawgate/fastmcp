"""OpenTelemetry setup helpers for tracing examples and smoke tests."""

from __future__ import annotations

import os
from typing import Literal

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

TraceExporterMode = Literal["console", "otlp"]


def resolve_trace_exporter_mode(exporter: str | None = None) -> TraceExporterMode:
    """Resolve the trace exporter mode from an argument or environment."""
    value = (
        (
            exporter
            or os.environ.get("FASTMCP_TRACE_EXPORTER")
            or os.environ.get("OTEL_TRACES_EXPORTER")
            or "otlp"
        )
        .strip()
        .lower()
    )
    if value in {"console", "stdout"}:
        return "console"
    return "otlp"


def build_tracer_provider(
    service_name: str,
    *,
    exporter: str | None = None,
    endpoint: str | None = None,
) -> tuple[TracerProvider, TraceExporterMode]:
    """Build a TracerProvider configured for either console or OTLP export."""
    mode = resolve_trace_exporter_mode(exporter)
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if mode == "console":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        return provider, mode

    resolved_endpoint = (
        endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or "http://localhost:4317"
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )

    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=resolved_endpoint, insecure=True))
    )
    return provider, mode


def configure_tracing(
    service_name: str,
    *,
    exporter: str | None = None,
    endpoint: str | None = None,
) -> TraceExporterMode:
    """Configure the global tracer provider and return the exporter mode used."""
    provider, mode = build_tracer_provider(
        service_name,
        exporter=exporter,
        endpoint=endpoint,
    )
    trace.set_tracer_provider(provider)
    return mode
