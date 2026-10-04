import warnings

warnings.warn(
    "agentium.integrations is deprecated in Agentium v2 and will be removed in v3. "
    "All v2 adapters reside in agentium.adapters.*.",
    DeprecationWarning,
    stacklevel=2,
)

from .._v1.integrations import *
