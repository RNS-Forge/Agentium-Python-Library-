"""Backward compatibility shim for Agentium v1 agentium.core.communicator."""
from __future__ import annotations
import warnings
from .._v1.core.communicator import *

warnings.warn(
    "'agentium.core.communicator' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
