"""Backward compatibility shim for Agentium v1 agentium.core.memory_helper."""
from __future__ import annotations
import warnings
from .._v1.core.memory_helper import *

warnings.warn(
    "'agentium.core.memory_helper' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
