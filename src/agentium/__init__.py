"""
Agentium v2 — Context & trust integrity toolkit for multi-agent and long-running AI agents.
"""

from __future__ import annotations

import warnings
from typing import Any

__version__ = "2.0.0"
__author__ = "Sanjay N"
__license__ = "MIT"

# Core v2 Foundation Exports
from .core.run import run, get_current_run, RunContext
from .adapters.plain import tool, get_tool_registry, ToolRegistry
from .core.events import Event, EventType, EventWriter, EventReader
from .core.config import load_config, AgentiumConfig
from .core.redact import Redactor, redact_payload
from .core.hashing import canonical_json, sha256_hex
from .core.tokens import estimate_tokens, set_tokenizer

# v2 Pin & Context Integrity Exports
from .pin.store import Pin, PinStore
from .pin.guard import reinject, guard_compaction
from .pin.soak import soak, TruncateCompactor, LastNCompactor, StubSummarizer

# v2 Lineage, Claims, Handoff & Action Gate Exports
from .lineage.claims import Claim, EvidenceRef, ClaimStore
from .lineage.verify import verifier, register_verifier, get_verifier, JsonFieldExtractor
from .lineage.graph import LineageGraph, BlameReport, LineageDiff, diff_lineage
from .lineage.handoff import HandoffPacket, HandoffOverflowError, lint_handoff, enforce_handoff_size
from .lineage.gate import ActionGate, ActionBlockedError, guarded

# v2 Fingerprint & Drift Exports
from .fingerprint.fp import Fingerprint, fingerprint
from .fingerprint.lock import LockFile, read_lock_file, write_lock_file
from .fingerprint.diff import DriftReport, diff_fingerprints

# v2 Experimental Acceleration Exports
from .speed.prefetch import PrefetchManager, ToolPredictor

# v2 Hub, Wrapper, Facade & Recipe Exports
from .hub.wrapper import wrap, wrap_async
from .hub.facade import use
from .hub.plugins import discover_plugins, get_plugin
from . import recipes

# v1 Public Names preserved for backward compatibility
_V1_NAMES = {
    "Agentium",
    "Condenser",
    "CondenserConfig",
    "Optimizer",
    "OptimizerConfig",
    "Rearranger",
    "RearrangerConfig",
    "Communicator",
    "CommunicatorConfig",
    "Extractor",
    "ExtractorConfig",
    "Translator",
    "TranslatorConfig",
    "InsightGenerator",
    "InsightConfig",
    "WorkflowHelper",
    "WorkflowConfig",
    "TemplateManager",
    "TemplateConfig",
    "MemoryHelper",
    "MemoryConfig",
    "CustomSummarizer",
    "SummaryConfig",
    "LoggerUtils",
    "LoggerConfig",
    "LANGCHAIN_INTEGRATION_AVAILABLE",
    "LANGGRAPH_INTEGRATION_AVAILABLE",
    "CREWAI_INTEGRATION_AVAILABLE",
    "GEMINI_INTEGRATION_AVAILABLE",
}


def __getattr__(name: str) -> Any:
    if name in _V1_NAMES:
        warnings.warn(
            f"'{name}' is part of the Agentium v1 text-processing toolkit and is deprecated in Agentium v2.",
            DeprecationWarning,
            stacklevel=2,
        )
        from . import _v1

        return getattr(_v1, name)
    raise AttributeError(f"module 'agentium' has no attribute '{name}'")


__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "run",
    "get_current_run",
    "RunContext",
    "tool",
    "get_tool_registry",
    "ToolRegistry",
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
    "wrap",
    "wrap_async",
    "use",
    "discover_plugins",
    "get_plugin",
    "recipes",
] + list(_V1_NAMES)
