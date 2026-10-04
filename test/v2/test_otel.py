import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agentium.core.otel import export_span_attributes, get_tracer


def test_otel_lazy_import_and_helpers():
    print("Testing OpenTelemetry lazy import and helpers...")
    # export_span_attributes should safely handle None without crashing
    export_span_attributes(None, {"key": "val"})

    class MockSpan:
        def __init__(self):
            self.attrs = {}

        def set_attribute(self, key, value):
            self.attrs[key] = value

    mock_span = MockSpan()
    export_span_attributes(mock_span, {"test_attr": "hello", "agentium.already": 123})
    assert mock_span.attrs["agentium.test_attr"] == "hello"
    assert mock_span.attrs["agentium.already"] == 123

    # If opentelemetry is not installed, get_tracer must raise ImportError mentioning extra
    try:
        tracer = get_tracer()
        print("OpenTelemetry is installed, tracer created:", tracer)
    except ImportError as e:
        assert "agentium[otel]" in str(e)
        print("[PASS] Lazy ImportError correctly instructs user to install 'agentium[otel]'")

    print("[PASS] otel helpers OK")


if __name__ == "__main__":
    test_otel_lazy_import_and_helpers()
    print("\nALL OTEL TESTS PASSED!")
