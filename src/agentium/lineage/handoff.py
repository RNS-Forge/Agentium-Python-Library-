"""F3: Handoff Contract and Packet Linter."""
from __future__ import annotations

import copy
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.tokens import estimate_tokens
from .claims import Claim


class HandoffOverflowError(Exception):
    """Raised when a HandoffPacket exceeds its token budget and cannot be truncated."""


@dataclass
class LintIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    code: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HandoffPacket:
    from_agent: str
    to_agent: str
    task: str
    claims: List[Claim] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    context: List[Dict[str, Any]] = field(default_factory=list)
    run_id: str = ""
    packet_id: str = field(default_factory=lambda: f"pkt_{uuid.uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    max_tokens: int = 2000

    def estimate_total_tokens(self) -> int:
        """Estimate token count of the full packet."""
        json_repr = json.dumps(self.to_dict(), ensure_ascii=False)
        return estimate_tokens(json_repr)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "task": self.task,
            "constraints": list(self.constraints),
            "claims": [c.to_dict() if isinstance(c, Claim) else c for c in self.claims],
            "context": copy.deepcopy(self.context),
            "max_tokens": self.max_tokens,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HandoffPacket:
        claims = [
            Claim.from_dict(c) if isinstance(c, dict) else c
            for c in data.get("claims", [])
        ]
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            task=data["task"],
            claims=claims,
            constraints=data.get("constraints", []),
            context=data.get("context", []),
            run_id=data.get("run_id", ""),
            packet_id=data.get("packet_id", f"pkt_{uuid.uuid4().hex[:12]}"),
            created_at=data.get("created_at", ""),
            max_tokens=int(data.get("max_tokens", 2000)),
        )


def enforce_handoff_size(
    packet: HandoffPacket,
    on_overflow: str = "error",
) -> HandoffPacket:
    """Enforce token limits according to the configured truncation policy.

    Policies:
    - 'error': Raise HandoffOverflowError.
    - 'truncate_unverified': Drop unverified claims first, then oldest context messages.
    - 'truncate_oldest': Drop oldest context messages first.

    CRITICAL RULE: Constraints are NEVER dropped under any policy.
    If constraints alone exceed max_tokens, HandoffOverflowError is raised.
    """
    total_tokens = packet.estimate_total_tokens()
    if total_tokens <= packet.max_tokens:
        return packet

    # Check baseline constraints size
    constraints_tokens = estimate_tokens(json.dumps(packet.constraints, ensure_ascii=False))
    if constraints_tokens > packet.max_tokens:
        raise HandoffOverflowError(
            f"Constraints alone require ~{constraints_tokens} tokens, exceeding max_tokens ({packet.max_tokens}). "
            "Constraints can never be truncated."
        )

    if on_overflow == "error":
        raise HandoffOverflowError(
            f"Handoff packet requires ~{total_tokens} tokens, exceeding max_tokens ({packet.max_tokens})."
        )

    cloned = HandoffPacket(
        from_agent=packet.from_agent,
        to_agent=packet.to_agent,
        task=packet.task,
        claims=list(packet.claims),
        constraints=list(packet.constraints),  # NEVER dropped
        context=list(packet.context),
        run_id=packet.run_id,
        packet_id=packet.packet_id,
        created_at=packet.created_at,
        max_tokens=packet.max_tokens,
    )

    if on_overflow == "truncate_unverified":
        # 1. Drop unverified claims first
        cloned.claims = [c for c in cloned.claims if getattr(c, "status", "") == "verified"]
        if cloned.estimate_total_tokens() <= cloned.max_tokens:
            return cloned

        # 2. Drop oldest context messages
        while cloned.context and cloned.estimate_total_tokens() > cloned.max_tokens:
            cloned.context.pop(0)

        if cloned.estimate_total_tokens() <= cloned.max_tokens:
            return cloned
        raise HandoffOverflowError("Packet still exceeds max_tokens after truncating unverified claims and context.")

    elif on_overflow == "truncate_oldest":
        # Drop oldest context messages first
        while cloned.context and cloned.estimate_total_tokens() > cloned.max_tokens:
            cloned.context.pop(0)

        if cloned.estimate_total_tokens() <= cloned.max_tokens:
            return cloned
        raise HandoffOverflowError("Packet still exceeds max_tokens after truncating context messages.")

    else:
        raise ValueError(f"Unknown on_overflow policy: '{on_overflow}'")


def lint_handoff(packet: HandoffPacket) -> List[LintIssue]:
    """Audit handoff packet for integrity, safety, and policy compliance."""
    issues: List[LintIssue] = []

    # 1. Self-handoff (circular assignment)
    if packet.from_agent and packet.to_agent and packet.from_agent == packet.to_agent:
        issues.append(
            LintIssue(
                severity="ERROR",
                code="CIRCULAR_HANDOFF",
                message=f"Agent '{packet.from_agent}' is handing off task to itself.",
            )
        )

    # 2. Missing task description
    if not packet.task.strip():
        issues.append(
            LintIssue(
                severity="ERROR",
                code="EMPTY_TASK",
                message="Handoff packet has an empty task description.",
            )
        )

    # 3. Missing constraints
    if not packet.constraints:
        issues.append(
            LintIssue(
                severity="WARNING",
                code="NO_CONSTRAINTS",
                message="Handoff packet has no constraints defined. Agents should specify operational boundaries.",
            )
        )

    # 4. Ungrounded claims with high confidence
    for c in packet.claims:
        if c.status == "unverified" and c.confidence > 0.8:
            issues.append(
                LintIssue(
                    severity="WARNING",
                    code="UNGROUNDED_HIGH_CONFIDENCE_CLAIM",
                    message=f"Claim '{c.id}' has status='unverified' but high confidence ({c.confidence}).",
                )
            )

    # 5. Token budget
    est = packet.estimate_total_tokens()
    if est > packet.max_tokens:
        issues.append(
            LintIssue(
                severity="ERROR",
                code="TOKEN_OVERFLOW",
                message=f"Estimated tokens ({est}) exceed max_tokens ({packet.max_tokens}).",
            )
        )

    return issues
