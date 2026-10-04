"""Backward compatibility shim for Agentium v1 agentium.core.insight_generator."""
from __future__ import annotations
import warnings
from .._v1.core.insight_generator import *

warnings.warn(
    "'agentium.core.insight_generator' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
