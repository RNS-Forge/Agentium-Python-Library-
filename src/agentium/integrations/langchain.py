import warnings

warnings.warn(
    "agentium.integrations.langchain is deprecated in Agentium v2 and will be removed in v3.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from .._v1.integrations.langchain import (
        AgentiumCallbackHandler,
        AgentiumLangChainIntegration,
        AgentiumLangChainTool,
        AgentiumMemory,
        AgentiumOutputParser,
        get_agentium_langchain_integration,
    )

    # Alias for confirmed PyPI export
    AgentiumTool = AgentiumLangChainTool

    __all__ = [
        "AgentiumTool",
        "AgentiumLangChainTool",
        "AgentiumLangChainIntegration",
        "AgentiumMemory",
        "AgentiumOutputParser",
        "AgentiumCallbackHandler",
        "get_agentium_langchain_integration",
    ]
except Exception:
    class AgentiumTool:  # type: ignore
        pass

    __all__ = ["AgentiumTool"]
