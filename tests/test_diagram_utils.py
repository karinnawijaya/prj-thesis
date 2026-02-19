import pytest

from diagram_utils import DiagramPayload, build_fallback_diagram, parse_diagram_payload


def test_parse_diagram_payload_valid():
    raw = """
    {
      "nodes": [
        {"id": "artworkA", "type": "artwork", "label": "Artwork A — Test A", "level": 0},
        {"id": "artworkB", "type": "artwork", "label": "Artwork B — Test B", "level": 0},
        {"id": "L1", "type": "niche_connection", "label": "Shared river setting", "level": 1}
      ],
      "edges": [
        {"id": "edge-1", "source": "artworkA", "target": "L1", "kind": "direct", "label": "Both set along the Seine"},
        {"id": "edge-2", "source": "artworkB", "target": "L1", "kind": "direct", "label": "Both set along the Seine"}
      ],
      "layout": {"direction": "TB"}
    }
    """
    diagram = parse_diagram_payload(raw)
    assert isinstance(diagram, DiagramPayload)
    assert len(diagram.nodes) == 3
    assert len(diagram.edges) == 2


def test_parse_diagram_payload_invalid_missing_artworks():
    raw = """
    {
      "nodes": [{"id": "L1", "type": "level", "label": "Only", "level": 1, "category": "core"}],
      "edges": [],
      "layout": {"direction": "TB"}
    }
    """
    with pytest.raises(ValueError):
        parse_diagram_payload(raw)


def test_parse_diagram_payload_promotes_level_one():
    raw = """
    {
      "nodes": [
        {"id": "artworkA", "type": "artwork", "label": "Artwork A — Test A", "level": 0},
        {"id": "artworkB", "type": "artwork", "label": "Artwork B — Test B", "level": 0},
        {"id": "L2", "type": "theme", "label": "Shared landscape focus", "level": 2}
      ],
      "edges": [],
      "layout": {"direction": "TB"}
    }
    """
    diagram = parse_diagram_payload(raw)
    level_one = [node for node in diagram.nodes if node.level == 1]
    assert level_one, "Expected a promoted level-1 node."


def test_build_fallback_diagram():
    diagram = build_fallback_diagram("Artwork A — A", "Artwork B — B")
    node_ids = {node.id for node in diagram.nodes}
    assert "artworkA" in node_ids
    assert "artworkB" in node_ids
    assert "L1" in node_ids
