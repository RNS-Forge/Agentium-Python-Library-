import warnings

warnings.warn(
    "agentium.integrations.crewai is deprecated in Agentium v2 and will be removed in v3.",
    DeprecationWarning,
    stacklevel=2,
)

class AgentiumCrewTool:
    """v1 compatibility stub for AgentiumCrewTool"""
    def __init__(self, *args, **kwargs):
        pass

__all__ = ["AgentiumCrewTool"]
