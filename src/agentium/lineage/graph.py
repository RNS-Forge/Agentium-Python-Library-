"""F2: Multi-Agent Lineage Graph (stdlib dict/set DAG)."""
from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.events import Event


@dataclass
class Node:
    id: str
    type: str  # "agent", "claim", "tool_call", "run"
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source_id: str
    target_id: str
    relation: str  # "produces", "depends_on", "verifies", "refutes", "hands_off_to"


@dataclass
class BlameReport:
    claim_id: str
    statement: str
    status: str
    origin_agent: Optional[str]
    root_tool_calls: List[str]
    dependency_chain: List[str]
    is_grounded: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            f"Lineage Blame Report for Claim: {self.claim_id}",
            f"  Statement       : {self.statement}",
            f"  Status          : {self.status.upper()}",
            f"  Origin Agent    : {self.origin_agent or 'unknown'}",
            f"  Is Grounded     : {self.is_grounded}",
            f"  Root Tool Calls : {', '.join(self.root_tool_calls) or 'None'}",
            f"  Dependency Path : {' -> '.join(self.dependency_chain) or 'None'}",
            f"  Summary         : {self.summary}",
        ]
        return "\n".join(lines)


@dataclass
class LineageDiff:
    run_a: str
    run_b: str
    claims_added: List[str]
    claims_removed: List[str]
    claims_status_changed: List[Dict[str, Any]]
    handoffs_added: List[Tuple[str, str]]
    handoffs_removed: List[Tuple[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            f"Lineage Topology Diff ({self.run_a} -> {self.run_b})",
            "-" * 45,
            f"  + Claims Added   : {', '.join(self.claims_added) or 'None'}",
            f"  - Claims Removed : {', '.join(self.claims_removed) or 'None'}",
            f"  * Status Changes : {len(self.claims_status_changed)}",
            f"  + Handoffs Added : {len(self.handoffs_added)}",
            f"  - Handoffs Dropped: {len(self.handoffs_removed)}",
        ]
        return "\n".join(lines)


class LineageGraph:
    """Directed Acyclic Graph (DAG) of agents, claims, tools, and handoffs."""

    def __init__(self, run_id: str = "") -> None:
        self.run_id = run_id
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adj: Dict[str, List[str]] = {}  # source -> [target]
        self._rev_adj: Dict[str, List[str]] = {}  # target -> [source]

    def add_node(self, node_id: str, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None) -> Node:
        node = Node(id=node_id, type=node_type, label=label, metadata=metadata or {})
        self.nodes[node_id] = node
        if node_id not in self._adj:
            self._adj[node_id] = []
        if node_id not in self._rev_adj:
            self._rev_adj[node_id] = []
        return node

    def add_edge(self, source_id: str, target_id: str, relation: str) -> None:
        if source_id not in self.nodes:
            self.add_node(source_id, "unknown", source_id)
        if target_id not in self.nodes:
            self.add_node(target_id, "unknown", target_id)

        edge = Edge(source_id=source_id, target_id=target_id, relation=relation)
        self.edges.append(edge)
        self._adj[source_id].append(target_id)
        self._rev_adj[target_id].append(source_id)

    def has_cycle(self) -> bool:
        """Check for cycles using Kahn's topological sort."""
        in_degree = {nid: len(self._rev_adj.get(nid, [])) for nid in self.nodes}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in self._adj.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count < len(self.nodes)

    def blame(self, claim_id: str) -> BlameReport:
        """Trace claim back to its origin agent, tool calls, and dependencies."""
        if claim_id not in self.nodes:
            raise KeyError(f"Claim node '{claim_id}' not found in lineage graph.")

        claim_node = self.nodes[claim_id]
        meta = claim_node.metadata
        statement = meta.get("statement", claim_node.label)
        status = meta.get("status", "unverified")
        origin_agent = meta.get("source_agent")

        # Walk backward to find root tools and origin agents
        visited: Set[str] = set()
        queue = deque([claim_id])
        root_tools: List[str] = []
        dep_chain: List[str] = []

        while queue:
            curr = queue.popleft()
            if curr in visited:
                continue
            visited.add(curr)
            if curr != claim_id:
                dep_chain.append(curr)

            node = self.nodes.get(curr)
            if node and node.type == "tool_call":
                root_tools.append(node.id)

            for parent in self._rev_adj.get(curr, []):
                pnode = self.nodes.get(parent)
                if pnode and pnode.type == "agent" and not origin_agent:
                    origin_agent = pnode.id
                queue.append(parent)

        is_grounded = len(root_tools) > 0 or len(meta.get("evidence", [])) > 0
        summary = (
            f"Claim '{claim_id}' originated from agent '{origin_agent or 'unknown'}'. "
            f"Grounding evidence: {'verified by tool' if is_grounded else 'UNGROUNDED'}. "
            f"Dependencies traced: {len(dep_chain)}."
        )

        return BlameReport(
            claim_id=claim_id,
            statement=statement,
            status=status,
            origin_agent=origin_agent,
            root_tool_calls=root_tools,
            dependency_chain=dep_chain,
            is_grounded=is_grounded,
            summary=summary,
        )

    def to_mermaid(self) -> str:
        """Render graph as a Mermaid flowchart diagram."""
        lines = ["flowchart TD"]

        # Style definitions
        lines.append("  classDef agent fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;")
        lines.append("  classDef claim fill:#fff3e0,stroke:#f57c00,stroke-width:2px;")
        lines.append("  classDef tool fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;")

        for nid, node in sorted(self.nodes.items()):
            clean_label = node.label.replace('"', '\\"')
            if node.type == "agent":
                lines.append(f'  {nid}["🤖 Agent: {clean_label}"]:::agent')
            elif node.type == "claim":
                lines.append(f'  {nid}["📜 Claim: {clean_label}"]:::claim')
            elif node.type == "tool_call":
                lines.append(f'  {nid}["🔧 Tool: {clean_label}"]:::tool')
            else:
                lines.append(f'  {nid}["{clean_label}"]')

        for edge in self.edges:
            rel = edge.relation
            lines.append(f"  {edge.source_id} -->|{rel}| {edge.target_id}")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render graph as structured Markdown tables and summaries."""
        lines = [
            f"### Multi-Agent Lineage Graph (Run: `{self.run_id or 'unknown'}`)",
            f"- **Nodes:** {len(self.nodes)} | **Edges:** {len(self.edges)} | **Cycle-free:** {not self.has_cycle()}\n",
            "#### Nodes",
            "| ID | Type | Label | Details |",
            "|:---|:---|:---|:---|",
        ]
        for nid, n in sorted(self.nodes.items()):
            det = f"status={n.metadata.get('status')}" if "status" in n.metadata else ""
            lines.append(f"| `{nid}` | `{n.type}` | {n.label} | {det} |")

        lines.append("\n#### Edges")
        lines.append("| Source | Relation | Target |")
        lines.append("|:---|:---:|:---|")
        for e in self.edges:
            lines.append(f"| `{e.source_id}` | `{e.relation}` | `{e.target_id}` |")

        lines.append("\n```mermaid\n" + self.to_mermaid() + "\n```")
        return "\n".join(lines)

    @classmethod
    def from_events(cls, events: List[Event], run_id: str = "") -> LineageGraph:
        """Build graph from event log list."""
        graph = cls(run_id=run_id)

        for ev in events:
            # Agent node
            if ev.agent_id and ev.agent_id not in graph.nodes:
                graph.add_node(ev.agent_id, "agent", ev.agent_id)

            # Claim events
            if ev.type == "claim":
                action = ev.payload.get("action")
                cdata = ev.payload.get("claim", {})
                cid = cdata.get("id") or ev.payload.get("claim_id")
                if cid:
                    stmt = cdata.get("statement", cid)
                    if cid not in graph.nodes:
                        graph.add_node(cid, "claim", stmt, metadata=cdata)
                    else:
                        graph.nodes[cid].metadata.update(cdata)

                    # Source agent edge
                    src_agent = cdata.get("source_agent") or ev.agent_id
                    if src_agent:
                        graph.add_edge(src_agent, cid, "produces")

                    # Dependencies edges
                    for dep in cdata.get("dependencies", []):
                        graph.add_edge(dep, cid, "depends_on")

                    # Evidence edges
                    for ev_ref in cdata.get("evidence", []):
                        src_id = ev_ref.get("source_id") if isinstance(ev_ref, dict) else getattr(ev_ref, "source_id", None)
                        if src_id:
                            if src_id not in graph.nodes:
                                graph.add_node(src_id, "tool_call", src_id)
                            graph.add_edge(src_id, cid, "verifies")

            # Tool call events
            elif ev.type == "tool_call":
                tname = ev.payload.get("tool_name", "tool")
                call_id = f"tool_{ev.event_id}"
                graph.add_node(call_id, "tool_call", tname, metadata=ev.payload)
                if ev.agent_id:
                    graph.add_edge(ev.agent_id, call_id, "invokes")

            # Handoff events
            elif ev.type == "handoff":
                from_ag = ev.payload.get("from_agent")
                to_ag = ev.payload.get("to_agent")
                if from_ag and to_ag:
                    if from_ag not in graph.nodes:
                        graph.add_node(from_ag, "agent", from_ag)
                    if to_ag not in graph.nodes:
                        graph.add_node(to_ag, "agent", to_ag)
                    graph.add_edge(from_ag, to_ag, "hands_off_to")

        return graph


def diff_lineage(graph_a: LineageGraph, graph_b: LineageGraph) -> LineageDiff:
    """Diff two lineage graphs."""
    claims_a = {nid: n for nid, n in graph_a.nodes.items() if n.type == "claim"}
    claims_b = {nid: n for nid, n in graph_b.nodes.items() if n.type == "claim"}

    added = sorted(set(claims_b.keys()) - set(claims_a.keys()))
    removed = sorted(set(claims_a.keys()) - set(claims_b.keys()))
    status_changed = []

    for cid in set(claims_a.keys()) & set(claims_b.keys()):
        st_a = claims_a[cid].metadata.get("status")
        st_b = claims_b[cid].metadata.get("status")
        if st_a != st_b:
            status_changed.append({"claim_id": cid, "before": st_a, "after": st_b})

    handoffs_a = {(e.source_id, e.target_id) for e in graph_a.edges if e.relation == "hands_off_to"}
    handoffs_b = {(e.source_id, e.target_id) for e in graph_b.edges if e.relation == "hands_off_to"}

    return LineageDiff(
        run_a=graph_a.run_id,
        run_b=graph_b.run_id,
        claims_added=added,
        claims_removed=removed,
        claims_status_changed=status_changed,
        handoffs_added=sorted(list(handoffs_b - handoffs_a)),
        handoffs_removed=sorted(list(handoffs_a - handoffs_b)),
    )
