"""Dynamic extra facade loader (agentium.use)."""
from __future__ import annotations

import importlib
from typing import Any, Dict

from .._meta import PACKAGE_NAME

# Mapping from extra name to adapter module path
EXTRA_ADAPTER_MAP: Dict[str, str] = {
    "tenacity": "agentium.adapters.tenacity_adapter",
    "pybreaker": "agentium.adapters.pybreaker_adapter",
    "cachetools": "agentium.adapters.cachetools_adapter",
    "jmespath": "agentium.adapters.jmespath_adapter",
    "rapidfuzz": "agentium.adapters.rapidfuzz_adapter",
    "deepdiff": "agentium.adapters.deepdiff_adapter",
    "pydantic": "agentium.adapters.pydantic_adapter",
    "jsonschema": "agentium.adapters.jsonschema_adapter",
    "tiktoken": "agentium.adapters.tiktoken_adapter",
    "litellm": "agentium.adapters.litellm_adapter",
    "httpx": "agentium.adapters.httpx_adapter",
    "langgraph": "agentium.adapters.langgraph_adapter",
    "crewai": "agentium.adapters.crewai_adapter",
    "openai-agents": "agentium.adapters.openai_agents_adapter",
    "openai": "agentium.adapters.openai_agents_adapter",
}


def use(extra_name: str) -> Any:
    """Facade import for Agentium optional adapters.

    Example:
        tenacity = agentium.use("tenacity")
        retry = tenacity.retry(...)
    """
    clean_name = extra_name.lower().strip()
    module_path = EXTRA_ADAPTER_MAP.get(clean_name)

    if not module_path:
        # Fallback to direct adapter naming convention
        module_path = f"agentium.adapters.{clean_name}_adapter"

    try:
        mod = importlib.import_module(module_path)
        return mod
    except ImportError as exc:
        raise ImportError(
            f"Agentium integration '{clean_name}' requires the '{clean_name}' extra. "
            f"Install it via: pip install '{PACKAGE_NAME}[{clean_name}]'"
        ) from exc
