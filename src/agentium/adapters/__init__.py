"""Agentium Framework and Library Adapters."""
from __future__ import annotations

from .plain import ToolDefinition, ToolRegistry, get_tool_registry, tool

__all__ = [
    "tool",
    "get_tool_registry",
    "ToolRegistry",
    "ToolDefinition",
    "LangGraphAdapter",
    "CrewAIAdapter",
    "OpenAIAgentsAdapter",
    "tenacity_adapter",
    "pybreaker_adapter",
    "cachetools_adapter",
    "jmespath_adapter",
    "rapidfuzz_adapter",
    "deepdiff_adapter",
    "pydantic_adapter",
    "jsonschema_adapter",
    "jsonrepair_adapter",
    "tiktoken_adapter",
    "httpx_adapter",
    "litellm_adapter",
    "mcp_adapter",
]

_ADAPTER_MODULES = {
    "LangGraphAdapter": (".langgraph_adapter", "LangGraphAdapter"),
    "CrewAIAdapter": (".crewai_adapter", "CrewAIAdapter"),
    "OpenAIAgentsAdapter": (".openai_agents_adapter", "OpenAIAgentsAdapter"),
    "tenacity_adapter": (".tenacity_adapter", None),
    "pybreaker_adapter": (".pybreaker_adapter", None),
    "cachetools_adapter": (".cachetools_adapter", None),
    "jmespath_adapter": (".jmespath_adapter", None),
    "rapidfuzz_adapter": (".rapidfuzz_adapter", None),
    "deepdiff_adapter": (".deepdiff_adapter", None),
    "pydantic_adapter": (".pydantic_adapter", None),
    "jsonschema_adapter": (".jsonschema_adapter", None),
    "jsonrepair_adapter": (".jsonrepair_adapter", None),
    "tiktoken_adapter": (".tiktoken_adapter", None),
    "httpx_adapter": (".httpx_adapter", None),
    "litellm_adapter": (".litellm_adapter", None),
    "mcp_adapter": (".mcp_adapter", None),
}


def __getattr__(name: str):
    if name in _ADAPTER_MODULES:
        import importlib
        mod_rel, attr = _ADAPTER_MODULES[name]
        mod = importlib.import_module(mod_rel, package=__name__)
        return getattr(mod, attr) if attr else mod
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
