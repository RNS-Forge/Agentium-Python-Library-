"""Recipe R05: verified_extract (jmespath + F1 claims).

Extracts fields from a tool or API result using JMESPath queries and binds them
directly into verified or unverified Claim records with EvidenceRef provenance.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run
from ..lineage.claims import Claim, ClaimStore, EvidenceRef


def verified_extract(
    data: Union[Dict[str, Any], List[Any], str],
    query: str,
    statement_template: str,
    source_id: str = "tool_output",
    claim_store: Optional[ClaimStore] = None,
    verify: bool = True,
    confidence: float = 0.95,
) -> Tuple[Any, Optional[Claim]]:
    """Query data using JMESPath and construct a grounded Claim record."""
    try:
        import jmespath
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'verified_extract' requires 'jmespath'. "
            f"Install via: pip install '{PACKAGE_NAME}[jmespath]'"
        ) from exc

    extracted_value = jmespath.search(query, data)
    if extracted_value is None:
        return None, None

    # Format statement (e.g. "User account balance is {val}")
    statement = statement_template.format(val=extracted_value, value=extracted_value)
    evidence = EvidenceRef(
        source_type="tool_call",
        source_id=source_id,
        excerpt=f"Extracted '{query}' -> {extracted_value}",
    )

    store = claim_store
    if store is None:
        store = ClaimStore()

    if verify:
        claim = store.add(statement=statement, confidence=confidence, evidence=[evidence])
        store.verify(claim.id, verifier_name="jmespath_extractor", confidence=confidence)
        # Retrieve the updated verified claim
        final_claim = store.get(claim.id)
    else:
        final_claim = store.add(statement=statement, confidence=confidence, evidence=[evidence])

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.CLAIM,
            {"recipe": "verified_extract", "query": query, "claim_id": final_claim.id if final_claim else None},
        )

    return extracted_value, final_claim


async def verified_extract_async(
    data: Union[Dict[str, Any], List[Any], str],
    query: str,
    statement_template: str,
    source_id: str = "tool_output",
    claim_store: Optional[ClaimStore] = None,
    verify: bool = True,
    confidence: float = 0.95,
) -> Tuple[Any, Optional[Claim]]:
    """Async twin: Query data using JMESPath and construct a grounded Claim record."""
    return await asyncio.to_thread(
        verified_extract,
        data,
        query,
        statement_template,
        source_id=source_id,
        claim_store=claim_store,
        verify=verify,
        confidence=confidence,
    )
