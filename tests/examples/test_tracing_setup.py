from __future__ import annotations

import sys
from pathlib import Path

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

import tracing_setup  # noqa: E402


class FakeExporter:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis: int | None = None):
        return True


def test_resolve_trace_exporter_mode_prefers_argument(monkeypatch):
    monkeypatch.delenv("FASTMCP_TRACE_EXPORTER", raising=False)
    monkeypatch.delenv("OTEL_TRACES_EXPORTER", raising=False)

    assert tracing_setup.resolve_trace_exporter_mode("console") == "console"
    assert tracing_setup.resolve_trace_exporter_mode("otlp") == "otlp"


def test_build_tracer_provider_console_uses_simple_processor(monkeypatch):
    monkeypatch.setattr(tracing_setup, "ConsoleSpanExporter", FakeExporter)

    provider, mode = tracing_setup.build_tracer_provider(
        "fastmcp-test",
        exporter="console",
    )

    assert mode == "console"
    assert provider.resource.attributes["service.name"] == "fastmcp-test"

    processor = provider._active_span_processor._span_processors[0]
    assert isinstance(processor, SimpleSpanProcessor)
    assert isinstance(processor.span_exporter, FakeExporter)
    assert processor.span_exporter.args == ()
    assert processor.span_exporter.kwargs == {}


def test_build_tracer_provider_otlp_uses_batch_processor():
    provider, mode = tracing_setup.build_tracer_provider(
        "fastmcp-test",
        exporter="otlp",
        endpoint="http://collector:4317",
    )

    assert mode == "otlp"
    assert provider.resource.attributes["service.name"] == "fastmcp-test"

    processor = provider._active_span_processor._span_processors[0]
    assert isinstance(processor, BatchSpanProcessor)
    exporter = processor._batch_processor._exporter
    assert isinstance(exporter, OTLPSpanExporter)
    assert exporter._endpoint == "collector:4317"
    assert exporter._insecure is True
