"""Value-object tests for the wiki graph.

Expected values are written as literals. Ids are chosen so that a wrong
implementation cannot pass by coincidence: an entity and a passage are given
ids that differ in their sort order, and the two-tenant case reuses the same
node ids under different tenants.
"""

from __future__ import annotations

import dataclasses

import pytest
from redstring_wfm.wiki import EdgeKind, NodeKind, WikiEdge, WikiGraph, WikiNode


def _alice() -> WikiNode:
    return WikiNode(id="e-alice", kind=NodeKind.ENTITY, text="Alice")


def _bob() -> WikiNode:
    return WikiNode(id="e-bob", kind=NodeKind.ENTITY, text="Bob")


def _passage() -> WikiNode:
    return WikiNode(id="p-1", kind=NodeKind.PASSAGE, text="Alice met Bob.")


def _graph() -> WikiGraph:
    return WikiGraph(
        tenant_id="t-1",
        nodes=(_alice(), _bob(), _passage()),
        edges=(
            WikiEdge(source="e-alice", target="e-bob", kind=EdgeKind.RELATION, label="knows"),
            WikiEdge(source="e-alice", target="p-1", kind=EdgeKind.MENTION, label="mentions"),
            WikiEdge(source="e-bob", target="p-1", kind=EdgeKind.MENTION, label="mentions"),
        ),
    )


class TestWikiNode:
    def test_holds_its_fields_as_given(self) -> None:
        node = _alice()
        assert (node.id, node.kind, node.text) == ("e-alice", NodeKind.ENTITY, "Alice")

    def test_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            _alice().text = "Mallory"  # type: ignore[misc]

    def test_is_hashable_and_equal_by_value(self) -> None:
        assert _alice() == WikiNode(id="e-alice", kind=NodeKind.ENTITY, text="Alice")
        assert hash(_alice()) == hash(WikiNode(id="e-alice", kind=NodeKind.ENTITY, text="Alice"))

    def test_rejects_empty_id(self) -> None:
        with pytest.raises(ValueError, match="node id must be non-empty"):
            WikiNode(id="", kind=NodeKind.ENTITY, text="x")

    def test_kind_distinguishes_otherwise_equal_nodes(self) -> None:
        entity = WikiNode(id="x", kind=NodeKind.ENTITY, text="x")
        passage = WikiNode(id="x", kind=NodeKind.PASSAGE, text="x")
        assert entity != passage


class TestWikiEdge:
    def test_holds_its_fields_as_given(self) -> None:
        edge = WikiEdge(source="e-alice", target="e-bob", kind=EdgeKind.RELATION, label="knows")
        assert (edge.source, edge.target, edge.kind, edge.label) == (
            "e-alice",
            "e-bob",
            EdgeKind.RELATION,
            "knows",
        )

    def test_rejects_empty_label(self) -> None:
        with pytest.raises(ValueError, match="edge label must be non-empty"):
            WikiEdge(source="e-alice", target="e-bob", kind=EdgeKind.RELATION, label="")


class TestWikiGraph:
    def test_holds_its_nodes_and_edges_as_given(self) -> None:
        graph = _graph()
        assert graph.tenant_id == "t-1"
        assert graph.nodes == (_alice(), _bob(), _passage())
        assert len(graph.edges) == 3

    def test_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            _graph().tenant_id = "t-2"  # type: ignore[misc]

    def test_node_lookup_returns_the_node_with_that_id(self) -> None:
        assert _graph().node("p-1") == _passage()
        assert _graph().node("e-bob") == _bob()

    def test_node_lookup_raises_for_an_absent_id(self) -> None:
        with pytest.raises(KeyError):
            _graph().node("missing")

    def test_entities_and_passages_partition_the_nodes_in_order(self) -> None:
        graph = _graph()
        assert graph.entities() == (_alice(), _bob())
        assert graph.passages() == (_passage(),)

    def test_rejects_empty_tenant(self) -> None:
        with pytest.raises(ValueError, match="tenant_id must be non-empty"):
            WikiGraph(tenant_id="", nodes=(), edges=())

    def test_rejects_duplicate_node_id_across_kinds(self) -> None:
        # An entity and a passage sharing an id would make every edge to that id ambiguous.
        clash = WikiNode(id="e-alice", kind=NodeKind.PASSAGE, text="Alice's passage")
        with pytest.raises(ValueError, match="duplicate node id 'e-alice'"):
            WikiGraph(tenant_id="t-1", nodes=(_alice(), clash), edges=())

    def test_rejects_edge_to_a_node_not_in_the_graph(self) -> None:
        edge = WikiEdge(source="e-alice", target="e-carol", kind=EdgeKind.RELATION, label="knows")
        with pytest.raises(ValueError, match="names a node not in the graph"):
            WikiGraph(tenant_id="t-1", nodes=(_alice(), _bob()), edges=(edge,))

    def test_rejects_relation_edge_to_a_passage(self) -> None:
        edge = WikiEdge(source="e-alice", target="p-1", kind=EdgeKind.RELATION, label="knows")
        with pytest.raises(ValueError, match="relation edge"):
            WikiGraph(tenant_id="t-1", nodes=(_alice(), _passage()), edges=(edge,))

    def test_rejects_mention_edge_from_a_passage(self) -> None:
        # Direction is part of the contract: mentions run entity -> passage.
        edge = WikiEdge(source="p-1", target="e-alice", kind=EdgeKind.MENTION, label="mentions")
        with pytest.raises(ValueError, match="mention edge"):
            WikiGraph(tenant_id="t-1", nodes=(_alice(), _passage()), edges=(edge,))

    def test_rejects_mention_edge_between_two_entities(self) -> None:
        edge = WikiEdge(source="e-alice", target="e-bob", kind=EdgeKind.MENTION, label="mentions")
        with pytest.raises(ValueError, match="mention edge"):
            WikiGraph(tenant_id="t-1", nodes=(_alice(), _bob()), edges=(edge,))

    def test_same_node_ids_under_two_tenants_are_distinct_graphs(self) -> None:
        # Tenancy is the builder's job, but two graphs with colliding ids must
        # never compare equal just because their node sets match.
        one = WikiGraph(tenant_id="t-1", nodes=(_alice(),), edges=())
        two = WikiGraph(tenant_id="t-2", nodes=(_alice(),), edges=())
        assert one != two
