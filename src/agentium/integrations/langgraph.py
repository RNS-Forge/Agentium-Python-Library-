import warnings

warnings.warn(
    "agentium.integrations.langgraph is deprecated in Agentium v2 and will be removed in v3.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from .._v1.integrations.langgraph import (
        AgentiumLangGraphBuilder,
        AgentiumLangGraphIntegration,
        AgentiumLangGraphWorkflow,
        get_agentium_langgraph_integration,
    )

    class AgentiumNode:
        @staticmethod
        def condenser_node(state):
            return state

        @staticmethod
        def optimizer_node(state):
            return state

    __all__ = [
        "AgentiumNode",
        "AgentiumLangGraphBuilder",
        "AgentiumLangGraphIntegration",
        "AgentiumLangGraphWorkflow",
        "get_agentium_langgraph_integration",
    ]
except Exception:
    class AgentiumNode:
        @staticmethod
        def condenser_node(state):
            return state

        @staticmethod
        def optimizer_node(state):
            return state

    __all__ = ["AgentiumNode"]
