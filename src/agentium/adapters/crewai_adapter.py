"""CrewAI Framework Adapter for Agentium v2.

Integrates Agentium task tracing, handoff packets, and claim lineage with CrewAI.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional

from ..core.events import EventType, EventWriter
from ..core.run import get_current_run
from ..lineage.claims import ClaimStore
from ..lineage.handoff import HandoffPacket


def _check_crewai_installed() -> None:
    try:
        import crewai  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError(
            "CrewAI adapter requires 'crewai'. "
            "Install it via: pip install 'agentium[crewai]'"
        ) from e


class CrewAIAdapter:
    """Adapter bridging CrewAI agents and task delegations to Agentium."""

    def __init__(
        self,
        claim_store: Optional[ClaimStore] = None,
        event_writer: Optional[EventWriter] = None,
    ) -> None:
        self.claim_store = claim_store or ClaimStore()
        self.event_writer = event_writer

    def _get_writer(self) -> Optional[EventWriter]:
        if self.event_writer is not None:
            return self.event_writer
        ctx = get_current_run()
        return ctx.event_writer if ctx is not None else None

    def record_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        constraints: Optional[List[str]] = None,
    ) -> HandoffPacket:
        """Record an explicit delegation/handoff between CrewAI agents."""
        packet = HandoffPacket(
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            constraints=list(constraints or []),
            claims=self.claim_store.all_claims(),
        )

        writer = self._get_writer()
        if writer:
            writer.write(
                EventType.HANDOFF,
                packet.to_dict(),
                agent_id=from_agent,
            )

        return packet

    def check_installed(self) -> None:
        """Verify crewai library is present."""
        _check_crewai_installed()
