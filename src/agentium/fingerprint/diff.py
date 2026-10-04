from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from .fp import Fingerprint
from .lock import LockFile


@dataclass
class ComponentDiff:
    component: str
    baseline_hash: str
    current_hash: str
    matches: bool


@dataclass
class DriftReport:
    has_drift: bool
    baseline_combined: str
    current_combined: str
    component_diffs: Dict[str, ComponentDiff]
    tools_added: List[str] = field(default_factory=list)
    tools_removed: List[str] = field(default_factory=list)
    tools_retained: List[str] = field(default_factory=list)
    tool_description_only_changes: bool = False
    tool_structural_changes: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_drift": self.has_drift,
            "baseline_combined": self.baseline_combined,
            "current_combined": self.current_combined,
            "tools_added": self.tools_added,
            "tools_removed": self.tools_removed,
            "tool_description_only_changes": self.tool_description_only_changes,
            "tool_structural_changes": self.tool_structural_changes,
            "components": {k: asdict(v) for k, v in self.component_diffs.items()},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_text(self) -> str:
        lines = []
        status = "DRIFT DETECTED" if self.has_drift else "MATCHES BASELINE (NO DRIFT)"
        lines.append(f"Agentium Drift Check: {status}")
        lines.append(f"Baseline Fingerprint : {self.baseline_combined[:16]}...")
        lines.append(f"Current Fingerprint  : {self.current_combined[:16]}...")
        lines.append("-" * 55)

        for comp, cd in sorted(self.component_diffs.items()):
            flag = "[MATCH]" if cd.matches else "[CHANGED]"
            lines.append(f"  {flag:9} {comp:16} (base: {cd.baseline_hash[:8]} -> cur: {cd.current_hash[:8]})")

        if self.tools_added or self.tools_removed or self.tool_description_only_changes or self.tool_structural_changes:
            lines.append("\nTool Analysis:")
            if self.tools_added:
                lines.append(f"  + Added Tools   : {', '.join(self.tools_added)}")
            if self.tools_removed:
                lines.append(f"  - Removed Tools : {', '.join(self.tools_removed)}")
            if self.tool_description_only_changes:
                lines.append("  * Tool Descriptions altered (Schema structure remains identical)")
            if self.tool_structural_changes:
                lines.append("  ! Tool Parameter Schemas altered (Structural drift detected)")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        status_badge = "🚨 **Drift Detected**" if self.has_drift else "✅ **No Drift Detected**"
        md = [
            "<!-- agentium-drift -->",
            "### Agentium Configuration Drift Report",
            f"**Status:** {status_badge}\n",
            f"- **Baseline Combined:** `{self.baseline_combined}`",
            f"- **Current Combined:**  `{self.current_combined}`\n",
            "| Component | Status | Baseline Hash | Current Hash |",
            "|:---|:---:|:---|:---|",
        ]

        for comp, cd in sorted(self.component_diffs.items()):
            icon = "✅ Match" if cd.matches else "⚠️ Changed"
            md.append(f"| `{comp}` | {icon} | `{cd.baseline_hash[:12]}` | `{cd.current_hash[:12]}` |")

        if self.tools_added or self.tools_removed or self.tool_description_only_changes or self.tool_structural_changes:
            md.append("\n#### Tool Schema Changes")
            if self.tools_added:
                md.append(f"- **Added Tools:** {', '.join(f'`{t}`' for t in self.tools_added)}")
            if self.tools_removed:
                md.append(f"- **Removed Tools:** {', '.join(f'`{t}`' for t in self.tools_removed)}")
            if self.tool_description_only_changes:
                md.append("- ℹ️ *Tool description-only change: parameter schemas are preserved.*")
            if self.tool_structural_changes:
                md.append("- ⚠️ *Tool structural change: parameter signatures or schemas have drifted.*")

        return "\n".join(md)


def diff_fingerprints(
    baseline: Union[LockFile, Fingerprint],
    current: Fingerprint,
) -> DriftReport:
    """Compare a baseline LockFile/Fingerprint against current Fingerprint."""
    baseline_combined = baseline.combined_fingerprint if isinstance(baseline, LockFile) else baseline.combined
    baseline_components = baseline.components
    baseline_tools = baseline.tools if isinstance(baseline, LockFile) else baseline.tool_names

    current_combined = current.combined
    current_components = current.components
    current_tools = current.tool_names

    all_components = sorted(set(baseline_components.keys()) | set(current_components.keys()))
    component_diffs: Dict[str, ComponentDiff] = {}
    has_drift = False

    for comp in all_components:
        base_h = baseline_components.get(comp, "")
        curr_h = current_components.get(comp, "")
        matches = (base_h == curr_h) and (base_h != "")
        if not matches:
            has_drift = True
        component_diffs[comp] = ComponentDiff(
            component=comp,
            baseline_hash=base_h,
            current_hash=curr_h,
            matches=matches,
        )

    # Tool additions / removals
    base_tools_set = set(baseline_tools)
    curr_tools_set = set(current_tools)
    tools_added = sorted(curr_tools_set - base_tools_set)
    tools_removed = sorted(base_tools_set - curr_tools_set)
    tools_retained = sorted(base_tools_set & curr_tools_set)

    # Structural vs Description-only changes
    tools_full_match = component_diffs.get("tools_full", ComponentDiff("", "", "", True)).matches
    tools_struct_match = component_diffs.get("tools_structure", ComponentDiff("", "", "", True)).matches

    tool_description_only_changes = (not tools_full_match) and tools_struct_match
    tool_structural_changes = not tools_struct_match

    return DriftReport(
        has_drift=has_drift,
        baseline_combined=baseline_combined,
        current_combined=current_combined,
        component_diffs=component_diffs,
        tools_added=tools_added,
        tools_removed=tools_removed,
        tools_retained=tools_retained,
        tool_description_only_changes=tool_description_only_changes,
        tool_structural_changes=tool_structural_changes,
    )
