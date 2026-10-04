"""Recipe R08: drift_report (deepdiff + F5 fingerprint / state inspection).

Inspects structural and value differences between baseline states, prompt schemas,
or model outputs, returning structured drift reports and logging drift events.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .._meta import PACKAGE_NAME
from ..core.events import EventType
from ..core.run import get_current_run


@dataclass
class DriftReport:
    """Report detailing detected structural or semantic drift."""

    has_drift: bool
    summary: str
    changes: Dict[str, Any] = field(default_factory=dict)
    baseline_id: Optional[str] = None
    target_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def drift_report(
    baseline: Any,
    target: Any,
    baseline_id: Optional[str] = None,
    target_id: Optional[str] = None,
    ignore_order: bool = True,
    **diff_kwargs: Any,
) -> DriftReport:
    """Compute structural drift between baseline and target objects using deepdiff.

    Args:
        baseline: The expected or previous state / structure.
        target: The current state / structure to compare against.
        baseline_id: Optional label or ID for the baseline.
        target_id: Optional label or ID for the target.
        ignore_order: Whether to ignore element ordering in sequences.
        **diff_kwargs: Additional arguments forwarded to deepdiff.

    Returns:
        DriftReport with has_drift, summary, and changes dict.
    """
    try:
        from ..adapters import deepdiff_adapter
    except ImportError as exc:
        raise ImportError(
            f"Recipe 'drift_report' requires 'deepdiff'. "
            f"Install via: pip install '{PACKAGE_NAME}[deepdiff]'"
        ) from exc

    diff_result = deepdiff_adapter.diff(
        baseline,
        target,
        ignore_order=ignore_order,
        **diff_kwargs,
    )

    has_drift = bool(diff_result)
    if not has_drift:
        summary = "No drift detected: baseline and target structures match."
    else:
        changed_keys = list(diff_result.keys())
        summary = f"Drift detected across {len(changed_keys)} change category/categories: {', '.join(changed_keys)}."

    report = DriftReport(
        has_drift=has_drift,
        summary=summary,
        changes=diff_result,
        baseline_id=baseline_id,
        target_id=target_id,
    )

    ctx = get_current_run()
    if ctx and ctx.event_writer:
        ctx.event_writer.write(
            EventType.FINGERPRINT,
            {
                "recipe": "drift_report",
                "has_drift": has_drift,
                "summary": summary,
                "baseline_id": baseline_id,
                "target_id": target_id,
            },
        )

    return report


async def drift_report_async(
    baseline: Any,
    target: Any,
    baseline_id: Optional[str] = None,
    target_id: Optional[str] = None,
    ignore_order: bool = True,
    **diff_kwargs: Any,
) -> DriftReport:
    """Async twin: Compute structural drift between baseline and target objects."""
    return await asyncio.to_thread(
        drift_report,
        baseline,
        target,
        baseline_id=baseline_id,
        target_id=target_id,
        ignore_order=ignore_order,
        **diff_kwargs,
    )
