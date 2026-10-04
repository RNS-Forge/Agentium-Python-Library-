from __future__ import annotations

from typing import Any, Dict, Optional


def get_tracer(service_name: str = "agentium"):
    """Lazily load OpenTelemetry tracer.
    Raises clear ImportError if OpenTelemetry is not installed.
    """
    try:
        from opentelemetry import trace  # type: ignore

        return trace.get_tracer(service_name)
    except ImportError as e:
        raise ImportError(
            "OpenTelemetry support requires the 'otel' extra. "
            "Install it with: pip install 'agentium[otel]'"
        ) from e


def export_span_attributes(span: Any, attributes: Dict[str, Any]) -> None:
    """Export attributes to an OpenTelemetry span with agentium.* namespace."""
    if span is None:
        return
    for k, v in attributes.items():
        key = k if k.startswith("agentium.") else f"agentium.{k}"
        try:
            span.set_attribute(key, v)
        except Exception:
            pass
