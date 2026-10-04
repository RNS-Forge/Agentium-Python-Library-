from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from ..core.hashing import canonical_json, sha256_hex
from ..core.redact import get_default_redactor


@dataclass(frozen=True)
class Fingerprint:
    combined: str
    components: Dict[str, str]
    tool_names: List[str] = field(default_factory=list)
    raw_components: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "combined": self.combined,
            "components": dict(self.components),
            "tool_names": list(self.tool_names),
        }

    @property
    def model(self) -> str:
        return self.components.get("model", "")

    @property
    def model_and_params(self) -> str:
        return self.components.get("model", "")

    @property
    def system_prompt(self) -> str:
        return self.components.get("system_prompt", "")

    @property
    def tools_full(self) -> str:
        return self.components.get("tools_full", "")

    @property
    def tools_structure(self) -> str:
        return self.components.get("tools_structure", "")

    @property
    def extras(self) -> str:
        return self.components.get("extras", "")

    @property
    def tools_manifest(self) -> List[Dict[str, Any]]:
        return self.raw_components.get("tools_full", [])


def _apply_ignore_path(data: Dict[str, Any], path: str) -> None:
    """Apply simple JSON-path selector such as '$.params.seed' or '$.extras.timestamp'.
    Rejects unsupported complex syntax with ValueError.
    """
    if not path.startswith("$."):
        raise ValueError(
            f"Unsupported ignore selector '{path}'. Selectors must start with '$.' (e.g. '$.params.seed')."
        )
    segments = path[2:].split(".")
    curr: Any = data
    for i, seg in enumerate(segments[:-1]):
        if not re.match(r"^[a-zA-Z0-9_\-]+$", seg):
            raise ValueError(f"Invalid selector segment '{seg}' in '{path}'.")
        if isinstance(curr, dict) and seg in curr:
            curr = curr[seg]
        else:
            return  # Path does not exist in target data, nothing to ignore

    target_key = segments[-1]
    if not re.match(r"^[a-zA-Z0-9_\-]+$", target_key):
        raise ValueError(f"Invalid target key '{target_key}' in '{path}'.")
    if isinstance(curr, dict) and target_key in curr:
        del curr[target_key]


def _normalize_tool_schema(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize tool schema to {name, description, parameters}."""
    name = str(tool.get("name", ""))
    desc = str(tool.get("description", ""))
    params = tool.get("parameters", {}) or tool.get("args_schema", {})
    return {
        "name": name,
        "description": desc,
        "parameters": params,
    }


def fingerprint(
    model: str,
    params: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    extras: Optional[Dict[str, Any]] = None,
    ignore: Optional[List[str]] = None,
    normalize_whitespace: bool = False,
    redact_before_hash: bool = False,
) -> Fingerprint:
    """Compute deterministic run fingerprint composed of:
    1. model: model id + sorted generation parameters
    2. system_prompt: prompt text (with optional whitespace normalization)
    3. tools_full: sorted tool names, descriptions, and parameter schemas
    4. tools_structure: sorted tool names and parameter schemas only (no descriptions)
    5. extras: user-supplied dict
    """
    # 1. Model & params
    params_copy = copy.deepcopy(params) if params else {}
    if ignore:
        wrap = {"params": params_copy, "extras": copy.deepcopy(extras) if extras else {}}
        for ign in ignore:
            _apply_ignore_path(wrap, ign)
        params_copy = wrap.get("params", {})
        extras_clean = wrap.get("extras", {})
    else:
        extras_clean = copy.deepcopy(extras) if extras else {}

    model_payload = {"model": model, "params": params_copy}
    if redact_before_hash:
        model_payload, _ = get_default_redactor()(model_payload)

    model_hash = sha256_hex(model_payload)

    # 2. System prompt
    prompt_str = system_prompt or ""
    if normalize_whitespace:
        prompt_str = " ".join(prompt_str.split())
    if redact_before_hash:
        res_prompt, _ = get_default_redactor()._redact_string(prompt_str)
        prompt_str = res_prompt

    prompt_hash = sha256_hex(prompt_str)

    # 3 & 4. Tools (Full and Structure)
    tools_list = copy.deepcopy(tools) if tools else []
    normalized_tools: List[Dict[str, Any]] = [_normalize_tool_schema(t) for t in tools_list]
    # Sort deterministically by name
    normalized_tools.sort(key=lambda t: t["name"])
    tool_names = [t["name"] for t in normalized_tools]

    # Full tools payload
    tools_full_payload = normalized_tools
    if redact_before_hash:
        tools_full_payload, _ = get_default_redactor()(tools_full_payload)
    tools_full_hash = sha256_hex(tools_full_payload)

    # Structure-only tools payload (description omitted)
    tools_structure_payload = [
        {"name": t["name"], "parameters": t.get("parameters", {})} for t in normalized_tools
    ]
    tools_structure_hash = sha256_hex(tools_structure_payload)

    # 5. Extras
    if redact_before_hash:
        extras_clean, _ = get_default_redactor()(extras_clean)
    extras_hash = sha256_hex(extras_clean)

    components = {
        "model": model_hash,
        "system_prompt": prompt_hash,
        "tools_full": tools_full_hash,
        "tools_structure": tools_structure_hash,
        "extras": extras_hash,
    }

    # Combined hash: canonical representation of the components dict
    combined_hash = sha256_hex(components)

    raw_comp = {
        "model": model_payload,
        "system_prompt": prompt_str,
        "tools_full": tools_full_payload,
        "tools_structure": tools_structure_payload,
        "extras": extras_clean,
    }

    return Fingerprint(
        combined=combined_hash,
        components=components,
        tool_names=tool_names,
        raw_components=raw_comp,
    )
