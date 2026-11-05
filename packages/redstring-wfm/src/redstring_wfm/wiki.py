"""Wiki-graph value objects.

These are the package's own types (ADR 0001): they hold ids, text and kinds,
and nothing here imports redstring. The builder is the only translator from
redstring's records into these.

A `WikiGraph` checks its own invariants on construction, so an invalid graph
cannot exist: ids are unique across entities and passages, and every edge
joins the node kinds its kind permits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeKind(Enum):
    ENTITY = "entity"
    PASSAGE = "passage"


class EdgeKind(Enum):
    # entity -> entity, labelled by the relation type.
    RELATION = "relation"
    # entity -> passage: the passage names the entity.
    MENTION = "mention"


@dataclass(frozen=True, slots=True)
class WikiNode:
    id: str
    kind: NodeKind
    text: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("node id must be non-empty")


@dataclass(frozen=True, slots=True)
class WikiEdge:
    source: str
    target: str
    kind: EdgeKind
    label: str

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("edge label must be non-empty")


@dataclass(frozen=True, slots=True)
class WikiGraph:
    tenant_id: str
    nodes: tuple[WikiNode, ...]
    edges: tuple[WikiEdge, ...]

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise ValueError("tenant_id must be non-empty")
        by_id: dict[str, WikiNode] = {}
        for node in self.nodes:
            if node.id in by_id:
                raise ValueError(f"duplicate node id {node.id!r}")
            by_id[node.id] = node
        for edge in self.edges:
            source = by_id.get(edge.source)
            target = by_id.get(edge.target)
            if source is None or target is None:
                raise ValueError(
                    f"edge {edge.source!r} -> {edge.target!r} names a node not in the graph"
                )
            if edge.kind is EdgeKind.RELATION:
                ok = source.kind is NodeKind.ENTITY and target.kind is NodeKind.ENTITY
            else:
                ok = source.kind is NodeKind.ENTITY and target.kind is NodeKind.PASSAGE
            if not ok:
                raise ValueError(
                    f"{edge.kind.value} edge {edge.source!r} -> {edge.target!r} "
                    f"joins {source.kind.value} to {target.kind.value}"
                )

    def node(self, node_id: str) -> WikiNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)

    def entities(self) -> tuple[WikiNode, ...]:
        return tuple(node for node in self.nodes if node.kind is NodeKind.ENTITY)

    def passages(self) -> tuple[WikiNode, ...]:
        return tuple(node for node in self.nodes if node.kind is NodeKind.PASSAGE)
