"""Agentium Core Runtime primitives and v1 core backwards compatibility."""
from __future__ import annotations

import importlib
import warnings
from typing import Any

from .config import AgentiumConfig, load_config
from .events import Event, EventReader, EventType, EventWriter
from .hashing import canonical_json, sha256_hex
from .redact import Redactor, redact_payload
from .run import RunContext, get_current_run, run
from .tokens import estimate_tokens, set_tokenizer

__all__ = [
    "run",
    "get_current_run",
    "RunContext",
    "Event",
    "EventType",
    "EventWriter",
    "EventReader",
    "load_config",
    "AgentiumConfig",
    "Redactor",
    "redact_payload",
    "canonical_json",
    "sha256_hex",
    "estimate_tokens",
    "set_tokenizer",
]

# v1 core module backward compatibility shims
_V1_CORE_MODULES = {
    "rearranger",
    "condenser",
    "optimizer",
    "communicator",
    "extractor",
    "translator",
    "insight_generator",
    "workflow_helper",
    "template_manager",
    "memory_helper",
    "summarizer",
    "logger_utils",
}


def __getattr__(name: str) -> Any:
    if name in _V1_CORE_MODULES:
        warnings.warn(
            f"'agentium.core.{name}' is part of Agentium v1 and is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return importlib.import_module(f"agentium._v1.core.{name}")
    raise AttributeError(f"module 'agentium.core' has no attribute '{name}'")
