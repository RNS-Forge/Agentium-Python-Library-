"""Recipe R06: fuzzy_verify (rapidfuzz + F1 claims).

Deterministic verifier evaluating whether source text supports a claim using
rapidfuzz partial/full string similarity, without LLM latency or cost.
"""
from __future__ import annotations

import asyncio
from typing import Optional, Tuple

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run
from ..lineage.claims import Claim, ClaimStore, EvidenceRef


def fuzzy_verify(
    claim_text: str,
    source_text: str,
    threshold: float = 0.8,
    claim_store: Optional[ClaimStore] = None,
    claim_id: Optional[str] = None,
    source_id: str = "source_document",
    method: str = "partial_ratio",
) -> Tuple[bool, float, Optional[Claim]]:
    """Evaluate whether source_text supports claim_text via string similarity.

    Args:
        claim_text: The claim statement to verify.
        source_text: The reference source or ground-truth text.
        threshold: Score threshold in range [0.0, 1.0] (or [0, 100]). Defaults to 0.8.
        claim_store: Optional ClaimStore to update or create a Claim in.
        claim_id: Optional existing claim ID to verify/refute in claim_store.
        source_id: Identifier of the source document/tool.
        method: 'partial_ratio' (default) or 'ratio'.

    Returns:
        (is_supported, similarity_score, claim)
    """
    try:
        from ..adapters import rapidfuzz_adapter
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'fuzzy_verify' requires 'rapidfuzz'. "
            f"Install via: pip install '{PACKAGE_NAME}[rapidfuzz]'"
        ) from exc

    norm_threshold = threshold / 100.0 if threshold > 1.0 else threshold

    if method == "ratio":
        score = rapidfuzz_adapter.ratio(claim_text, source_text)
    else:
        score = rapidfuzz_adapter.partial_ratio(claim_text, source_text)

    is_supported = score >= norm_threshold

    claim: Optional[Claim] = None
    if claim_store is not None:
        evidence = EvidenceRef(
            source_type="doc_grounding",
            source_id=source_id,
            excerpt=source_text[:200] if len(source_text) > 200 else source_text,
        )
        if claim_id:
            if is_supported:
                claim = claim_store.verify(
                    claim_id=claim_id,
                    verifier_name="fuzzy_verifier",
                    evidence=evidence,
                    confidence=score,
                )
            else:
                claim = claim_store.refute(
                    claim_id=claim_id,
                    refuter_name="fuzzy_verifier",
                    reason=f"Similarity score {score:.3f} below threshold {norm_threshold:.3f}",
                    evidence=evidence,
                )
        else:
            claim = claim_store.add(
                statement=claim_text,
                confidence=score,
                evidence=[evidence],
            )
            if is_supported:
                claim = claim_store.verify(
                    claim_id=claim.id,
                    verifier_name="fuzzy_verifier",
                    confidence=score,
                )
            else:
                claim = claim_store.refute(
                    claim_id=claim.id,
                    refuter_name="fuzzy_verifier",
                    reason=f"Similarity score {score:.3f} below threshold {norm_threshold:.3f}",
                )

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.CLAIM,
            {
                "recipe": "fuzzy_verify",
                "score": score,
                "is_supported": is_supported,
                "threshold": norm_threshold,
                "claim_id": claim.id if claim else claim_id,
            },
        )

    return is_supported, score, claim


async def fuzzy_verify_async(
    claim_text: str,
    source_text: str,
    threshold: float = 0.8,
    claim_store: Optional[ClaimStore] = None,
    claim_id: Optional[str] = None,
    source_id: str = "source_document",
    method: str = "partial_ratio",
) -> Tuple[bool, float, Optional[Claim]]:
    """Async twin: evaluate whether source_text supports claim_text via string similarity."""
    return await asyncio.to_thread(
        fuzzy_verify,
        claim_text,
        source_text,
        threshold=threshold,
        claim_store=claim_store,
        claim_id=claim_id,
        source_id=source_id,
        method=method,
    )
