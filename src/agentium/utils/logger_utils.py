"""Backward compatibility shim for Agentium v1 agentium.utils.logger_utils."""
from __future__ import annotations
import warnings
from .._v1.utils.logger_utils import *

warnings.warn(
    "'agentium.utils.logger_utils' is part of Agentium v1 and is deprecated in v2.",
    DeprecationWarning,
    stacklevel=2,
)
