"""Agentium Integration Recipes.

Curated combinations of battle-tested ecosystem libraries and Agentium guarantees.
Every recipe delivers:
1. Both sync and async twins.
2. Direct integration with Agentium core primitives (events, claims, gates, lineage).
3. Clear actionable ImportError instructions if required extras are missing.
"""
from .api_call_safe import api_call_safe, api_call_safe_async
from .budget_llm import BudgetExceededError, budget_llm, budget_llm_async
from .cached_tool import cached_tool, cached_tool_async
from .drift_report import DriftReport, drift_report, drift_report_async
from .fuzzy_dedupe_cache import fuzzy_dedupe_cache, fuzzy_dedupe_cache_async
from .fuzzy_verify import fuzzy_verify, fuzzy_verify_async
from .graph_retry import graph_retry, graph_retry_async
from .graph_tracing import graph_tracing, graph_tracing_async
from .http_cache_tool import HttpCacheTool, http_cache_tool, http_cache_tool_async
from .llm_failover import llm_failover, llm_failover_async
from .mcp_bridge import McpBridge, mcp_bridge, mcp_bridge_async
from .mcp_safe_tools import McpSafeToolsBridge, mcp_safe_tools, mcp_safe_tools_async
from .protected_handoff import protected_handoff, protected_handoff_async
from .safe_call import safe_call, safe_call_async
from .smart_compact import smart_compact, smart_compact_async
from .structured_llm import structured_llm, structured_llm_async
from .traced_retry import traced_retry, traced_retry_async
from .typed_agent_tools import typed_agent_tools, typed_agent_tools_async
from .validated_tool_args import validated_tool_args, validated_tool_args_async
from .verified_extract import verified_extract, verified_extract_async

__all__ = [
    # Batch 1
    "safe_call",
    "safe_call_async",
    "cached_tool",
    "cached_tool_async",
    "verified_extract",
    "verified_extract_async",
    "fuzzy_verify",
    "fuzzy_verify_async",
    "drift_report",
    "drift_report_async",
    "DriftReport",
    # Batch 2
    "protected_handoff",
    "protected_handoff_async",
    "validated_tool_args",
    "validated_tool_args_async",
    "smart_compact",
    "smart_compact_async",
    "structured_llm",
    "structured_llm_async",
    "mcp_bridge",
    "mcp_bridge_async",
    "McpBridge",
    # Batch 3
    "budget_llm",
    "budget_llm_async",
    "BudgetExceededError",
    "llm_failover",
    "llm_failover_async",
    "api_call_safe",
    "api_call_safe_async",
    "traced_retry",
    "traced_retry_async",
    # Batch 4 (Remaining Tier 1)
    "graph_retry",
    "graph_retry_async",
    "graph_tracing",
    "graph_tracing_async",
    "typed_agent_tools",
    "typed_agent_tools_async",
    "mcp_safe_tools",
    "mcp_safe_tools_async",
    "McpSafeToolsBridge",
    "http_cache_tool",
    "http_cache_tool_async",
    "HttpCacheTool",
    "fuzzy_dedupe_cache",
    "fuzzy_dedupe_cache_async",
]
