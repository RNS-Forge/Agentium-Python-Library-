import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_dir = os.path.join(_project_root, "src")
_src_agentium = os.path.join(_src_dir, "agentium")

if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Set __path__ so all submodules (lineage, core, pin, adapters, fingerprint, speed, recipes, hub)
# resolve directly into src/agentium
__path__ = [_src_agentium]

# Populate this module with the implementation from src/agentium/__init__.py
_src_init = os.path.join(_src_agentium, "__init__.py")
if os.path.exists(_src_init):
    with open(_src_init, "rb") as _f:
        _code = compile(_f.read(), _src_init, "exec")
        exec(_code, globals())