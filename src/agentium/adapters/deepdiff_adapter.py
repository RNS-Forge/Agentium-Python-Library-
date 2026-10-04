"""DeepDiff Adapter for Agentium v2.

Provides deep structural diffing for prompt, tool schema, and state drift inspection.
"""
from __future__ import annotations

from typing import Any, Dict

from .._meta import PACKAGE_NAME

try:
    from deepdiff import DeepDiff as _raw_deepdiff
except ImportError:
    _raw_deepdiff = None  # type: ignore


def _ensure_installed():
    if _raw_deepdiff is None:
        raise ImportError(
            f"DeepDiff adapter requires the 'deepdiff' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[deepdiff]'"
        )


raw = _raw_deepdiff


def diff(t1: Any, t2: Any, **kwargs: Any) -> Dict[str, Any]:
    """Compute deep structural difference between two objects."""
    _ensure_installed()
    res = _raw_deepdiff(t1, t2, **kwargs)
    return res.to_dict() if hasattr(res, "to_dict") else dict(res)
