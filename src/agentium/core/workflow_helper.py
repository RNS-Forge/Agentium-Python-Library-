"""Backward compatibility shim for Agentium v1 agentium.core.workflow_helper."""
from __future__ import annotations
import warnings
from .._v1.core.workflow_helper import *

warnings.warn(
    "'agentium.core.workflow_helper' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
