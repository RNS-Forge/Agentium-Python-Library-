"""Backward compatibility shim for Agentium v1 agentium.core.translator."""
from __future__ import annotations
import warnings
from .._v1.core.translator import *

warnings.warn(
    "'agentium.core.translator' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
