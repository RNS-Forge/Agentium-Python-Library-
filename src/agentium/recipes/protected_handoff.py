"""Recipe R10: protected_handoff (pydantic + jsonschema + F3 handoff + redaction).

Validates, size-checks, redacts secrets/PII, and lints multi-agent handoffs in a single atomic step.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Type, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.redact import redact_payload
from ..core.run import get_current_run
from ..lineage.claims import Claim
from ..lineage.handoff import HandoffPacket, enforce_handoff_size, lint_handoff


def protected_handoff(
    from_agent: str,
    to_agent: str,
    task: str,
    context: Optional[List[Dict[str, Any]]] = None,
    claims: Optional[List[Claim]] = None,
    constraints: Optional[List[str]] = None,
    schema: Optional[Union[Type[Any], Dict[str, Any]]] = None,
    max_tokens: int = 2000,
    run_id: str = "",
    redact: bool = True,
) -> HandoffPacket:
    """Validate, redact, lint, and construct a protected HandoffPacket.

    Args:
        from_agent: Sender agent ID.
        to_agent: Recipient agent ID.
        task: Clear objective or instruction.
        context: Supplemental context dictionaries.
        claims: Verified or unverified claims supporting the handoff.
        constraints: Hard rules or constraints the recipient must follow.
        schema: Optional Pydantic model class or JSON schema to validate context data.
        max_tokens: Maximum allowed token budget for the handoff.
        run_id: Current run ID.
        redact: Whether to redact secrets/PII from context payloads.

    Returns:
        Validated, sanitized HandoffPacket.
    """
    clean_context = context or []

    # 1. Schema Validation (Pydantic or JSONSchema)
    if schema is not None:
        if isinstance(schema, type):
            # Pydantic model validation
            try:
                from ..adapters import pydantic_adapter
                for item in clean_context:
                    pydantic_adapter.validate(schema, item)
            except ImportError as exc:
                raise ImportError(
                    f"Recipe 'protected_handoff' with Pydantic model requires 'pydantic'. "
                    f"Install via: pip install '{PACKAGE_NAME}[pydantic]'"
                ) from exc
        elif isinstance(schema, dict):
            # JSONSchema validation
            try:
                from ..adapters import jsonschema_adapter
                for item in clean_context:
                    jsonschema_adapter.validate(item, schema)
            except ImportError as exc:
                raise ImportError(
                    f"Recipe 'protected_handoff' with JSON schema requires 'jsonschema'. "
                    f"Install via: pip install '{PACKAGE_NAME}[jsonschema]'"
                ) from exc

    # 2. Secret Redaction
    if redact and clean_context:
        clean_context = [redact_payload(item)[0] for item in clean_context]

    # 3. Create Handoff Packet
    packet = HandoffPacket(
        from_agent=from_agent,
        to_agent=to_agent,
        task=task,
        claims=claims or [],
        constraints=constraints or [],
        context=clean_context,
        run_id=run_id,
        max_tokens=max_tokens,
    )

    # 4. Lint and Size Constraints
    issues = lint_handoff(packet)
    error_issues = [i for i in issues if i.severity == "ERROR"]
    if error_issues:
        raise ValueError(f"Handoff validation failed: {[i.message for i in error_issues]}")

    packet = enforce_handoff_size(packet)

    # 5. Emit Event
    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.HANDOFF,
            {
                "recipe": "protected_handoff",
                "packet_id": packet.packet_id,
                "from_agent": packet.from_agent,
                "to_agent": packet.to_agent,
                "task": packet.task,
                "tokens": packet.estimate_total_tokens(),
            },
        )

    return packet


async def protected_handoff_async(
    from_agent: str,
    to_agent: str,
    task: str,
    context: Optional[List[Dict[str, Any]]] = None,
    claims: Optional[List[Claim]] = None,
    constraints: Optional[List[str]] = None,
    schema: Optional[Union[Type[Any], Dict[str, Any]]] = None,
    max_tokens: int = 2000,
    run_id: str = "",
    redact: bool = True,
) -> HandoffPacket:
    """Async twin: Validate, redact, lint, and construct a protected HandoffPacket."""
    return await asyncio.to_thread(
        protected_handoff,
        from_agent=from_agent,
        to_agent=to_agent,
        task=task,
        context=context,
        claims=claims,
        constraints=constraints,
        schema=schema,
        max_tokens=max_tokens,
        run_id=run_id,
        redact=redact,
    )
