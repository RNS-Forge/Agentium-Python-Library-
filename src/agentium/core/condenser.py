"""Backward compatibility shim for Agentium v1 agentium.core.condenser."""
from __future__ import annotations
import warnings
from .._v1.core.condenser import *

warnings.warn(
    "'agentium.core.condenser' is part of Agentium v1 and is deprecated in v2. "
    "Use 'from agentium import Condenser'.",
    DeprecationWarning,
    stacklevel=2,
)
