"""Backward compatibility shim for Agentium v1 agentium.core.template_manager."""
from __future__ import annotations
import warnings
from .._v1.core.template_manager import *

warnings.warn(
    "'agentium.core.template_manager' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
