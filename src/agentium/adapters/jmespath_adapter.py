"""JMESPath Adapter for Agentium v2.

Provides JSON query capabilities for claim extraction and validation.
"""
from __future__ import annotations

from typing import Any, Optional

from .._meta import PACKAGE_NAME

try:
    import jmespath as _raw_jmespath
except ImportError:
    _raw_jmespath = None  # type: ignore


def _ensure_installed():
    if _raw_jmespath is None:
        raise ImportError(
            f"JMESPath adapter requires the 'jmespath' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[jmespath]'"
        )


raw = _raw_jmespath


def search(expression: str, data: Any) -> Any:
    """Evaluate a JMESPath expression against JSON-compatible data."""
    _ensure_installed()
    return _raw_jmespath.search(expression, data)


def compile(expression: str) -> Any:
    """Pre-compile a JMESPath expression for repeated execution."""
    _ensure_installed()
    return _raw_jmespath.compile(expression)
