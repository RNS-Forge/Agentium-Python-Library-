"""LiteLLM Adapter for Agentium v2.

Provides model-agnostic completion and routing for LLM calls with Agentium event tracing.
"""
from __future__ import annotations

from typing import Any

from .._meta import PACKAGE_NAME

try:
    import litellm as _raw_litellm
except ImportError:
    _raw_litellm = None  # type: ignore


def _ensure_installed() -> None:
    if _raw_litellm is None:
        raise ImportError(
            f"LiteLLM adapter requires the 'litellm' extra. "
            f"Install via: pip install '{PACKAGE_NAME}[litellm]'"
        )


raw = _raw_litellm


def completion(*args: Any, **kwargs: Any) -> Any:
    """Execute sync model completion across providers."""
    _ensure_installed()
    return _raw_litellm.completion(*args, **kwargs)


async def acompletion(*args: Any, **kwargs: Any) -> Any:
    """Execute async model completion across providers."""
    _ensure_installed()
    return await _raw_litellm.acompletion(*args, **kwargs)
