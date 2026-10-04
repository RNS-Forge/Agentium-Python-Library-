"""Package metadata and centralized configuration values."""
from __future__ import annotations

import os

# Central package name variable to allow frictionless renaming
PACKAGE_NAME = os.environ.get("AGENTIUM_PACKAGE_NAME", "agentium")
VERSION = "2.0.3"
AUTHOR = "Sanjay N"
LICENSE = "MIT"
PLUGIN_ENTRYPOINT_GROUP = "agentium.plugins"
