from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CoreConfig:
    events_dir: str = ".agentium/events"
    flush_per_event: bool = True
    redaction: bool = True

    @property
    def dir(self) -> str:
        return self.events_dir


@dataclass
class LineageConfig:
    trusted_tools: List[str] = field(default_factory=list)
    store_path: str = ".agentium/lineage"


@dataclass
class GateConfig:
    mode: str = "enforce"  # enforce | shadow
    on_destructive_undeclared: str = "escalate"  # allow | block | escalate


@dataclass
class HandoffConfig:
    max_tokens: int = 2000
    on_overflow: str = "error"  # error | truncate_unverified | truncate_oldest


@dataclass
class PinConfig:
    reinject_position: str = "end"  # start | end
    reinject_role: str = "system"


@dataclass
class FingerprintConfig:
    store_text: bool = False
    lock_file: str = "agentium.lock"


@dataclass
class DoctorConfig:
    scanners: List[str] = field(default_factory=list)


@dataclass
class PrefetchConfig:
    enabled: bool = False
    max_in_flight: int = 3
    ttl_seconds: int = 60
    max_wasted_per_run: int = 5
    hit_rate_threshold: float = 0.3


@dataclass
class AgentiumConfig:
    core: CoreConfig = field(default_factory=CoreConfig)
    lineage: LineageConfig = field(default_factory=LineageConfig)
    gate: GateConfig = field(default_factory=GateConfig)
    handoff: HandoffConfig = field(default_factory=HandoffConfig)
    pin: PinConfig = field(default_factory=PinConfig)
    fingerprint: FingerprintConfig = field(default_factory=FingerprintConfig)
    doctor: DoctorConfig = field(default_factory=DoctorConfig)
    prefetch: PrefetchConfig = field(default_factory=PrefetchConfig)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def events_dir(self) -> str:
        return self.core.events_dir

    @property
    def events(self) -> CoreConfig:
        return self.core


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Search upward from start_dir for agentium.toml."""
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "agentium.toml"
        if candidate.is_file():
            return candidate
    return None


def _apply_env_overrides(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Override config dict with AGENTIUM_* environment variables.
    Format example: AGENTIUM_CORE_EVENTS_DIR -> raw['core']['events_dir']
    AGENTIUM_GATE_MODE -> raw['gate']['mode']
    """
    for key, val in os.environ.items():
        if not key.startswith("AGENTIUM_"):
            continue
        parts = key[len("AGENTIUM_") :].lower().split("_")
        if len(parts) == 1:
            raw[parts[0]] = val
        elif len(parts) >= 2:
            section = parts[0]
            field_name = "_".join(parts[1:])
            if section not in raw or not isinstance(raw[section], dict):
                raw[section] = {}
            # Boolean conversions
            if val.lower() in ("true", "1", "yes"):
                raw[section][field_name] = True
            elif val.lower() in ("false", "0", "no"):
                raw[section][field_name] = False
            elif val.isdigit():
                raw[section][field_name] = int(val)
            else:
                raw[section][field_name] = val
    return raw


def load_config(config_path: Optional[Path] = None) -> AgentiumConfig:
    """Load configuration using stdlib tomllib with upward search and env overrides."""
    if config_path and config_path.is_dir():
        resolved_path = find_config_file(config_path)
    else:
        resolved_path = config_path or find_config_file()
    raw: Dict[str, Any] = {}

    if resolved_path and resolved_path.is_file():
        try:
            with open(resolved_path, "rb") as f:
                raw = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Invalid TOML in config file at {resolved_path}: {e}") from e

    raw = _apply_env_overrides(raw)

    cfg = AgentiumConfig(raw_data=raw)

    # Core & Events section compatibility
    if "core" in raw and isinstance(raw["core"], dict):
        c = raw["core"]
        cfg.core.events_dir = str(c.get("events_dir", cfg.core.events_dir))
        cfg.core.flush_per_event = bool(c.get("flush_per_event", cfg.core.flush_per_event))
        cfg.core.redaction = bool(c.get("redaction", cfg.core.redaction))
    elif "events" in raw and isinstance(raw["events"], dict):
        ev = raw["events"]
        cfg.core.events_dir = str(ev.get("dir", cfg.core.events_dir))
        cfg.core.flush_per_event = bool(ev.get("flush", cfg.core.flush_per_event))

    # Lineage
    if "lineage" in raw and isinstance(raw["lineage"], dict):
        l = raw["lineage"]
        if "trusted_tools" in l and isinstance(l["trusted_tools"], list):
            cfg.lineage.trusted_tools = [str(x) for x in l["trusted_tools"]]
        cfg.lineage.store_path = str(l.get("store_path", cfg.lineage.store_path))

    # Gate
    if "gate" in raw and isinstance(raw["gate"], dict):
        g = raw["gate"]
        cfg.gate.mode = str(g.get("mode", cfg.gate.mode))
        cfg.gate.on_destructive_undeclared = str(
            g.get("on_destructive_undeclared", cfg.gate.on_destructive_undeclared)
        )

    # Handoff
    if "handoff" in raw and isinstance(raw["handoff"], dict):
        h = raw["handoff"]
        cfg.handoff.max_tokens = int(h.get("max_tokens", cfg.handoff.max_tokens))
        cfg.handoff.on_overflow = str(h.get("on_overflow", cfg.handoff.on_overflow))

    # Pin
    if "pin" in raw and isinstance(raw["pin"], dict):
        p = raw["pin"]
        cfg.pin.reinject_position = str(p.get("reinject_position", cfg.pin.reinject_position))
        cfg.pin.reinject_role = str(p.get("reinject_role", cfg.pin.reinject_role))

    # Fingerprint
    if "fingerprint" in raw and isinstance(raw["fingerprint"], dict):
        fp = raw["fingerprint"]
        cfg.fingerprint.store_text = bool(fp.get("store_text", cfg.fingerprint.store_text))
        cfg.fingerprint.lock_file = str(fp.get("lock_file", cfg.fingerprint.lock_file))

    # Doctor
    if "doctor" in raw and isinstance(raw["doctor"], dict):
        d = raw["doctor"]
        if "scanners" in d and isinstance(d["scanners"], list):
            cfg.doctor.scanners = [str(x) for x in d["scanners"]]

    # Prefetch
    if "prefetch" in raw and isinstance(raw["prefetch"], dict):
        pf = raw["prefetch"]
        cfg.prefetch.enabled = bool(pf.get("enabled", cfg.prefetch.enabled))
        cfg.prefetch.max_in_flight = int(pf.get("max_in_flight", cfg.prefetch.max_in_flight))
        cfg.prefetch.ttl_seconds = int(pf.get("ttl_seconds", cfg.prefetch.ttl_seconds))
        cfg.prefetch.max_wasted_per_run = int(pf.get("max_wasted_per_run", cfg.prefetch.max_wasted_per_run))
        cfg.prefetch.hit_rate_threshold = float(
            pf.get("hit_rate_threshold", cfg.prefetch.hit_rate_threshold)
        )

    # Check experimental env flag for prefetch
    if os.environ.get("AGENTIUM_EXPERIMENTAL_PREFETCH") in ("1", "true", "yes"):
        cfg.prefetch.enabled = True

    return cfg
