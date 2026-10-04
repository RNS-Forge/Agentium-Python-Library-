"""Backward compatibility shim for Agentium v1 agentium.core.rearranger."""
from __future__ import annotations

import warnings

from .._v1.core.rearranger import (
    ArrangementStrategy,
    ContentType,
    Rearranger,
    RearrangerConfig,
)

warnings.warn(
    "'agentium.core.rearranger' is part of Agentium v1 and is deprecated in v2. "
    "Use 'from agentium import Rearranger'.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "Rearranger",
    "RearrangerConfig",
    "ArrangementStrategy",
    "ContentType",
]
