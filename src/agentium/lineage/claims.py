"""F1: Claims & Evidence-Based Trust."""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run


@dataclass
class EvidenceRef:
    source_type: str  # "tool_call", "db_query", "code_exec", "user_input", "external_api"
    source_id: str
    excerpt: str
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceRef:
        return cls(
            source_type=data["source_type"],
            source_id=data["source_id"],
            excerpt=data["excerpt"],
            hash=data.get("hash", ""),
        )


@dataclass
class Claim:
    id: str
    statement: str
    status: str = "unverified"  # "unverified", "verified", "refuted"
    confidence: float = 0.5
    evidence: List[EvidenceRef] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # IDs of claims this claim depends on
    source_agent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_by: Optional[str] = None
    run_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence"] = [e.to_dict() if isinstance(e, EvidenceRef) else e for e in self.evidence]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Claim:
        raw_ev = data.get("evidence", [])
        evidence = [
            EvidenceRef.from_dict(e) if isinstance(e, dict) else e
            for e in raw_ev
        ]
        return cls(
            id=data["id"],
            statement=data["statement"],
            status=data.get("status", "unverified"),
            confidence=float(data.get("confidence", 0.5)),
            evidence=evidence,
            dependencies=data.get("dependencies", []),
            source_agent=data.get("source_agent"),
            created_at=data.get("created_at", ""),
            verified_by=data.get("verified_by"),
            run_id=data.get("run_id", ""),
            metadata=data.get("metadata", {}),
        )


class ClaimStore:
    """Per-run storage for claims, verifications, and peer-agreement defense."""

    def __init__(self, run_id: Optional[str] = None, event_writer: Optional[EventWriter] = None) -> None:
        self.run_id = run_id or str(uuid.uuid4())
        self.event_writer = event_writer
        self._claims: Dict[str, Claim] = {}

    def _emit(self, event_type: Union[EventType, str], payload: Dict[str, Any]) -> None:
        writer = self.event_writer
        if writer is None:
            ctx = get_current_run()
            if ctx is not None:
                writer = ctx.event_writer
        if writer is not None:
            writer.write(event_type, payload)

    def add(
        self,
        statement: str,
        confidence: float = 0.5,
        evidence: Optional[List[EvidenceRef]] = None,
        dependencies: Optional[List[str]] = None,
        source_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        claim_id: Optional[str] = None,
    ) -> Claim:
        """Create and store a new claim (defaults to status='unverified')."""
        cid = claim_id or f"claim_{uuid.uuid4().hex[:12]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        cl = Claim(
            id=cid,
            statement=statement,
            status="unverified",
            confidence=max(0.0, min(1.0, float(confidence))),
            evidence=copy.deepcopy(evidence or []),
            dependencies=list(dependencies or []),
            source_agent=source_agent,
            created_at=now_ts,
            verified_by=None,
            run_id=self.run_id,
            metadata=copy.deepcopy(metadata or {}),
        )
        self._claims[cid] = cl
        self._emit(EventType.CLAIM, {"action": "created", "claim": cl.to_dict()})
        return cl

    def record_peer_agreement(self, claim_id: str, peer_agent: str) -> Claim:
        """Record agreement by a peer agent.
        PEER AGREEMENT DEFENSE: If a claim is unverified, peer agreement CANNOT upgrade
        it to verified without external grounding evidence.
        """
        claim = self.get(claim_id)
        if not claim:
            raise KeyError(f"Claim '{claim_id}' not found.")

        # Update metadata to track peer agreement, but preserve status
        metadata = dict(claim.metadata)
        agreements = list(metadata.get("peer_agreements", []))
        if peer_agent not in agreements:
            agreements.append(peer_agent)
        metadata["peer_agreements"] = agreements

        updated = Claim(
            id=claim.id,
            statement=claim.statement,
            status=claim.status,  # UNTOUCHED: stays unverified!
            confidence=claim.confidence,
            evidence=claim.evidence,
            dependencies=claim.dependencies,
            source_agent=claim.source_agent,
            created_at=claim.created_at,
            verified_by=claim.verified_by,
            run_id=claim.run_id,
            metadata=metadata,
        )
        self._claims[claim_id] = updated
        self._emit(EventType.CLAIM, {"action": "peer_agreement", "claim_id": claim_id, "peer": peer_agent})
        return updated

    def verify(
        self,
        claim_id: str,
        verifier_name: str,
        evidence: Optional[Union[EvidenceRef, List[EvidenceRef]]] = None,
        confidence: float = 1.0,
    ) -> Claim:
        """Mark a claim as verified based on external grounding."""
        claim = self.get(claim_id)
        if not claim:
            raise KeyError(f"Claim '{claim_id}' not found.")

        new_ev = list(claim.evidence)
        if evidence:
            if isinstance(evidence, list):
                new_ev.extend(evidence)
            else:
                new_ev.append(evidence)

        verified_claim = Claim(
            id=claim.id,
            statement=claim.statement,
            status="verified",
            confidence=max(0.0, min(1.0, float(confidence))),
            evidence=new_ev,
            dependencies=claim.dependencies,
            source_agent=claim.source_agent,
            created_at=claim.created_at,
            verified_by=verifier_name,
            run_id=claim.run_id,
            metadata=claim.metadata,
        )
        self._claims[claim_id] = verified_claim
        self._emit(EventType.CLAIM, {"action": "verified", "claim": verified_claim.to_dict()})
        return verified_claim

    def refute(
        self,
        claim_id: str,
        refuter_name: str,
        reason: Optional[str] = None,
        evidence: Optional[Union[EvidenceRef, List[EvidenceRef]]] = None,
    ) -> Claim:
        """Mark a claim as refuted."""
        claim = self.get(claim_id)
        if not claim:
            raise KeyError(f"Claim '{claim_id}' not found.")

        new_ev = list(claim.evidence)
        if evidence:
            if isinstance(evidence, list):
                new_ev.extend(evidence)
            else:
                new_ev.append(evidence)

        metadata = dict(claim.metadata)
        if reason:
            metadata["refutation_reason"] = reason

        refuted_claim = Claim(
            id=claim.id,
            statement=claim.statement,
            status="refuted",
            confidence=0.0,
            evidence=new_ev,
            dependencies=claim.dependencies,
            source_agent=claim.source_agent,
            created_at=claim.created_at,
            verified_by=refuter_name,
            run_id=claim.run_id,
            metadata=metadata,
        )
        self._claims[claim_id] = refuted_claim
        self._emit(EventType.CLAIM, {"action": "refuted", "claim": refuted_claim.to_dict()})
        return refuted_claim

    def get(self, claim_id: str) -> Optional[Claim]:
        return self._claims.get(claim_id)

    def all_claims(self) -> List[Claim]:
        return sorted(self._claims.values(), key=lambda c: (c.created_at, c.id))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "claims": [c.to_dict() for c in self.all_claims()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], event_writer: Optional[EventWriter] = None) -> ClaimStore:
        store = cls(run_id=data.get("run_id"), event_writer=event_writer)
        for c_data in data.get("claims", []):
            claim = Claim.from_dict(c_data)
            store._claims[claim.id] = claim
        return store
