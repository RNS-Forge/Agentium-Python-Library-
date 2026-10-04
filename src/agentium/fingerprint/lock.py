from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .fp import Fingerprint


@dataclass(frozen=True)
class LockFile:
    schema_version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    combined_fingerprint: str = ""
    components: Dict[str, str] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stored_text: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.stored_text is None:
            del d["stored_text"]
        return d

    @property
    def version(self) -> int:
        return self.schema_version

    @property
    def combined(self) -> str:
        return self.combined_fingerprint

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LockFile:
        schema_v = data.get("schema_version", 1)
        if schema_v != 1:
            raise ValueError(
                f"Unsupported lock file schema_version '{schema_v}'. Expected version 1."
            )
        return cls(
            schema_version=schema_v,
            created_at=data.get("created_at", ""),
            combined_fingerprint=data.get("combined_fingerprint", ""),
            components=data.get("components", {}),
            tools=data.get("tools", []),
            metadata=data.get("metadata", {}),
            stored_text=data.get("stored_text"),
        )


def write_lock_file(
    file_path: Union[str, Path],
    fp: Fingerprint,
    metadata: Optional[Dict[str, Any]] = None,
    store_text: bool = False,
) -> Path:
    """Write agentium.lock file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    stored = None
    if store_text and fp.raw_components:
        stored = {
            "model": fp.raw_components.get("model", {}).get("model"),
            "system_prompt": fp.raw_components.get("system_prompt"),
        }

    lock = LockFile(
        schema_version=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        combined_fingerprint=fp.combined,
        components=fp.components,
        tools=fp.tool_names,
        metadata=metadata or {},
        stored_text=stored,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(lock.to_json() + "\n")

    return path


def read_lock_file(file_path: Union[str, Path]) -> LockFile:
    """Read agentium.lock file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Lock file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Malformed lock file at {path}: expected JSON object.")

    return LockFile.from_dict(data)
