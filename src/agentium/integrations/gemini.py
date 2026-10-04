import warnings

warnings.warn(
    "agentium.integrations.gemini is deprecated in Agentium v2 and will be removed in v3.",
    DeprecationWarning,
    stacklevel=2,
)

from .._v1.integrations.gemini import (
    GeminiConfig,
    GeminiIntegration,
    GeminiModel,
    get_gemini_integration,
)

__all__ = ["GeminiConfig", "GeminiIntegration", "GeminiModel", "get_gemini_integration"]
