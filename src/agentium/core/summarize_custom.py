"""Backward compatibility shim for Agentium v1 agentium.core.summarize_custom."""
from __future__ import annotations
import warnings
from .._v1.core.summarize_custom import *

warnings.warn(
    "'agentium.core.summarize_custom' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
