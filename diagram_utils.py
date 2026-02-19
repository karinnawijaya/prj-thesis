from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError


class DiagramNode(BaseModel):
    id: str
    type: str
    label: str
    level: int
    x: Optional[float] = None
    y: Optional[float] = None


class DiagramEdge(BaseModel):
    id: str
    source: str
    target: str
    kind: str
    label: Optional[str] = None


class DiagramLayout(BaseModel):
    direction: str = Field(default="TB", pattern="^TB$")
    hint_text: Optional[str] = None


class DiagramPayload(BaseModel):
    nodes: List[DiagramNode]
    edges: List[DiagramEdge]
    layout: DiagramLayout = Field(default_factory=DiagramLayout)


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    return stripped.strip()


def _extract_json(text: str) -> str:
    cleaned = _strip_code_fences(text)
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return cleaned
    return cleaned[first : last + 1]


def parse_diagram_payload(
    raw_text: str,
    *,
    artist_a: Optional[str] = None,
    artist_b: Optional[str] = None,
    movement: Optional[str] = None,
) -> DiagramPayload:
    candidate = _extract_json(raw_text)
    payload = json.loads(candidate)
    diagram = DiagramPayload.model_validate(payload)
    diagram = normalize_diagram(
        diagram, artist_a=artist_a, artist_b=artist_b, movement=movement
    )
    validate_diagram_payload(diagram)
    return diagram


def validate_diagram_payload(diagram: DiagramPayload) -> None:
    node_ids = [node.id for node in diagram.nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Diagram node ids must be unique.")

    node_id_set = set(node_ids)
    if "artworkA" not in node_id_set or "artworkB" not in node_id_set:
        raise ValueError("Diagram must include artworkA and artworkB nodes.")

    for node in diagram.nodes:
        if not node.label.strip():
            raise ValueError("Diagram node labels must be non-empty.")
        if node.level < 0 or node.level > 4:
            raise ValueError("Diagram node level must be between 0 and 4.")
        if node.type not in {
            "artwork",
            "niche_connection",
            "artist",
            "teacher",
            "movement",
            "theme",
            "context",
            "other",
        }:
            raise ValueError("Diagram node type is invalid.")

        if node.id in {"artworkA", "artworkB"}:
            if node.type != "artwork":
                raise ValueError("Artwork nodes must have type 'artwork'.")
            if node.level != 0:
                raise ValueError("Artwork nodes must have level 0.")
        else:
            if node.level == 0:
                raise ValueError("Non-artwork nodes must have level 1-4.")

    for edge in diagram.edges:
        if edge.source not in node_id_set or edge.target not in node_id_set:
            raise ValueError("Diagram edge references unknown nodes.")
        if edge.kind not in {"direct", "contextual", "interpretive"}:
            raise ValueError("Diagram edge kind is invalid.")

    connections = {node_id: set() for node_id in node_id_set}
    for edge in diagram.edges:
        connections[edge.source].add(edge.target)
        connections[edge.target].add(edge.source)

    for node in diagram.nodes:
        if node.id in {"artworkA", "artworkB"}:
            continue
        connected = connections.get(node.id, set())
        if not connected:
            raise ValueError("Each non-artwork node must connect to at least one node.")
        if node.type == "niche_connection" or node.level == 1:
            if "artworkA" not in connected or "artworkB" not in connected:
                raise ValueError("Level-1 node must connect to both artworks.")


def normalize_diagram(
    diagram: DiagramPayload,
    *,
    artist_a: Optional[str] = None,
    artist_b: Optional[str] = None,
    movement: Optional[str] = None,
) -> DiagramPayload:
    nodes = list(diagram.nodes)
    edges = list(diagram.edges)
    def degree(node_id: str) -> int:
        count = 0
        for edge in edges:
            if edge.source == node_id or edge.target == node_id:
                count += 1
        return count

    non_artwork_nodes = [
        node for node in nodes if node.id not in {"artworkA", "artworkB"}
    ]

    level_one_nodes = [
        node for node in non_artwork_nodes if node.level == 1 and node.type == "niche_connection"
    ]
    if len(level_one_nodes) > 1:
        level_one_nodes.sort(key=lambda node: degree(node.id), reverse=True)
        primary = level_one_nodes[0]
        for node in level_one_nodes[1:]:
            node.level = max(node.level, 2)
            if node.type == "niche_connection":
                node.type = "theme"
    elif len(level_one_nodes) == 0:
        if non_artwork_nodes:
            non_artwork_nodes.sort(key=lambda node: degree(node.id), reverse=True)
            primary = non_artwork_nodes[0]
            primary.level = 1
            primary.type = "niche_connection"
        else:
            nodes.append(
                DiagramNode(
                    id="L1",
                    type="niche_connection",
                    label="Connection could not be structured",
                    level=1,
                )
            )

    existing_edge_ids = {edge.id for edge in edges}

    def add_edge(source: str, target: str, kind: str) -> None:
        edge_id = f"edge-{source}-{target}"
        if edge_id in existing_edge_ids:
            return
        edges.append(
            DiagramEdge(
                id=edge_id,
                source=source,
                target=target,
                kind=kind,
            )
        )
        existing_edge_ids.add(edge_id)

    def label_matches(label: str, target: Optional[str]) -> bool:
        if not label or not target:
            return False
        return target.lower() in label.lower()

    for node in nodes:
        if node.id in {"artworkA", "artworkB"}:
            continue
        has_to_a = any(
            (edge.source == "artworkA" and edge.target == node.id)
            or (edge.source == node.id and edge.target == "artworkA")
            for edge in edges
        )
        has_to_b = any(
            (edge.source == "artworkB" and edge.target == node.id)
            or (edge.source == node.id and edge.target == "artworkB")
            for edge in edges
        )
        if node.type == "niche_connection" or node.level == 1:
            if not has_to_a:
                add_edge("artworkA", node.id, "direct")
            if not has_to_b:
                add_edge("artworkB", node.id, "direct")
            continue
        if node.type == "artist":
            if not has_to_a and label_matches(node.label, artist_a):
                add_edge("artworkA", node.id, "contextual")
            if not has_to_b and label_matches(node.label, artist_b):
                add_edge("artworkB", node.id, "contextual")
            if not has_to_a and not has_to_b:
                add_edge("artworkA", node.id, "contextual")
            continue
        if node.type == "movement":
            if not has_to_a:
                add_edge("artworkA", node.id, "contextual")
            if not has_to_b:
                add_edge("artworkB", node.id, "contextual")

    def ensure_artist_node(artist_label: Optional[str], node_id: str, artwork_id: str) -> None:
        if not artist_label:
            return
        if any(
            node.type == "artist" and artist_label.lower() in node.label.lower()
            for node in nodes
        ):
            return
        nodes.append(
            DiagramNode(
                id=node_id,
                type="artist",
                label=artist_label,
                level=2,
            )
        )
        add_edge(artwork_id, node_id, "contextual")

    ensure_artist_node(artist_a, "artistA", "artworkA")
    ensure_artist_node(artist_b, "artistB", "artworkB")

    if movement:
        has_movement = any(
            node.type == "movement" and movement.lower() in node.label.lower()
            for node in nodes
        )
        if not has_movement:
            nodes.append(
                DiagramNode(
                    id="movement",
                    type="movement",
                    label=movement,
                    level=4,
                )
            )
            add_edge("artworkA", "movement", "contextual")
            add_edge("artworkB", "movement", "contextual")

    return DiagramPayload(nodes=nodes, edges=edges, layout=diagram.layout)


def build_fallback_diagram(
    artwork_a_label: str, artwork_b_label: str
) -> DiagramPayload:
    canvas_width = 920
    padding = 80
    top_row_y = 20
    artwork_width = 220
    category_width = 200
    left_x = padding
    right_x = canvas_width - artwork_width - padding
    center_x = (left_x + artwork_width + right_x) / 2 - category_width / 2
    nodes = [
        DiagramNode(
            id="artworkA",
            type="artwork",
            label=artwork_a_label,
            level=0,
            x=left_x,
            y=top_row_y,
        ),
        DiagramNode(
            id="artworkB",
            type="artwork",
            label=artwork_b_label,
            level=0,
            x=right_x,
            y=top_row_y,
        ),
        DiagramNode(
            id="L1",
            type="niche_connection",
            label="Connection could not be structured",
            level=1,
            x=center_x,
            y=top_row_y,
        ),
    ]
    edges = [
        DiagramEdge(
            id="edge-artworkA-L1",
            source="artworkA",
            target="L1",
            kind="direct",
        ),
        DiagramEdge(
            id="edge-artworkB-L1",
            source="artworkB",
            target="L1",
            kind="direct",
        ),
    ]
    return DiagramPayload(nodes=nodes, edges=edges, layout=DiagramLayout(direction="TB"))


def repair_diagram_json(raw_text: str) -> str:
    return _extract_json(raw_text)


def build_deterministic_diagram(
    *,
    summary: str,
    artwork_a: Dict[str, Any],
    artwork_b: Dict[str, Any],
    movement: Optional[str] = None,
) -> DiagramPayload:
    def extract_comparison_text(text: str) -> str:
        marker = "**Comparison Summary**"
        if marker in text:
            return text.split(marker, 1)[-1].strip()
        return text.strip()

    summary_body = extract_comparison_text(summary)
    summary_lower = summary_body.lower()

    def normalize_text(value: Optional[str]) -> str:
        return (value or "").strip()

    def extract_names(text: str) -> List[str]:
        return re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", text)

    def extract_teacher(text: str) -> Optional[str]:
        patterns = [
            r"studied under ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"education under ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"taught by ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def extract_influences(artist_name: str, text: str) -> List[str]:
        if not artist_name:
            return []
        patterns = [
            rf"{re.escape(artist_name)}[^.]*influenced by ([^.]+)",
            rf"{re.escape(artist_name)}[^.]*drew inspiration from ([^.]+)",
        ]
        influences: List[str] = []
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                chunk = match.group(1)
                parts = re.split(r",| and ", chunk)
                for part in parts:
                    candidate = part.strip()
                    if candidate:
                        influences.append(candidate)
        return influences


    def intersection_name(a: str, b: str) -> Optional[str]:
        names_a = set(extract_names(a))
        names_b = set(extract_names(b))
        shared = [name for name in names_a.intersection(names_b)]
        for name in shared:
            if name.lower() in summary_lower:
                return name
        return shared[0] if shared else None

    def shared_subject() -> Optional[str]:
        left_text = " ".join(
            [
                normalize_text(artwork_a.get("Subject")),
                normalize_text(artwork_a.get("Classification")),
                normalize_text(artwork_a.get("Composition")),
            ]
        ).lower()
        right_text = " ".join(
            [
                normalize_text(artwork_b.get("Subject")),
                normalize_text(artwork_b.get("Classification")),
                normalize_text(artwork_b.get("Composition")),
            ]
        ).lower()

        keywords = [
            "landscape",
            "portrait",
            "ballet",
            "dancers",
            "river",
            "road",
            "bridge",
            "garden",
            "trees",
            "seashore",
            "greenery",
            "leisure",
            "genre",
            "scene",
        ]
        for term in keywords:
            if term in summary_lower and term in left_text and term in right_text:
                return term
        return None

    teacher = intersection_name(
        normalize_text(artwork_a.get("Art Education")),
        normalize_text(artwork_b.get("Art Education")),
    )
    if not teacher:
        teacher = extract_teacher(summary_body)
    subject_term = shared_subject()

    l1_label: Optional[str] = None
    l1_source = None
    shared_location = None
    location_a = normalize_text(artwork_a.get("Artwork Location"))
    location_b = normalize_text(artwork_b.get("Artwork Location"))
    if location_a and location_b and location_a.lower() == location_b.lower():
        shared_location = location_a
    if not shared_location:
        location_match = re.search(r"along the ([A-Z][A-Za-z\s-]+)", summary_body)
        if location_match and "both" in summary_lower:
            shared_location = location_match.group(1).strip()

    if teacher and (
        "studied under" in summary_lower
        or "education" in summary_lower
        or teacher.lower() in summary_lower
    ):
        l1_label = f"Shared education under {teacher}"
        l1_source = "education"
    elif shared_location:
        l1_label = f"Shared location in {shared_location}"
        l1_source = "location"
    elif "shared education" in summary_lower or "artist education" in summary_lower:
        l1_label = "Shared art education"
        l1_source = "education"
    elif "shared location" in summary_lower:
        l1_label = "Shared location setting"
        l1_source = "location"
    elif subject_term:
        l1_label = f"Shared {subject_term} focus"
        l1_source = "subject"
    elif movement and movement.lower() in summary_lower:
        l1_label = f"Shared {movement} movement"
        l1_source = "movement"
    else:
        l1_label = "Connection could not be structured"
        l1_source = "fallback"

    nodes: List[DiagramNode] = []
    edges: List[DiagramEdge] = []

    def add_edge(source: str, target: str, kind: str = "contextual") -> None:
        edge_id = f"edge-{source}-{target}"
        suffix = 1
        while any(edge.id == edge_id for edge in edges):
            suffix += 1
            edge_id = f"edge-{source}-{target}-{suffix}"
        edges.append(DiagramEdge(id=edge_id, source=source, target=target, kind=kind))

    def add_labeled_edge(
        source: str,
        target: str,
        label: str,
        kind: str = "contextual",
    ) -> None:
        edge_id = f"edge-{source}-{target}"
        suffix = 1
        while any(edge.id == edge_id for edge in edges):
            suffix += 1
            edge_id = f"edge-{source}-{target}-{suffix}"
        edges.append(
            DiagramEdge(id=edge_id, source=source, target=target, kind=kind, label=label)
        )

    # Layout constants
    canvas_width = 920
    padding = 80
    top_row_y = 20
    row_spacing = 260
    artwork_width = 220
    category_width = 200

    left_x = padding
    right_x = canvas_width - artwork_width - padding
    center_x = (left_x + artwork_width + right_x) / 2 - category_width / 2

    title_a = normalize_text(artwork_a.get("title")) or "Unknown title"
    title_b = normalize_text(artwork_b.get("title")) or "Unknown title"
    artist_a_label = normalize_text(artwork_a.get("artist")) or "Unknown artist"
    artist_b_label = normalize_text(artwork_b.get("artist")) or "Unknown artist"
    year_a = artwork_a.get("year")
    year_b = artwork_b.get("year")

    nodes.append(
        DiagramNode(
            id="artworkA",
            type="artwork",
            label=f"Artwork A — {title_a}, {artist_a_label}, {year_a}",
            level=0,
            x=left_x,
            y=top_row_y,
        )
    )
    nodes.append(
        DiagramNode(
            id="artworkB",
            type="artwork",
            label=f"Artwork B — {title_b}, {artist_b_label}, {year_b}",
            level=0,
            x=right_x,
            y=top_row_y,
        )
    )

    nodes.append(
        DiagramNode(
            id="L1",
            type="niche_connection",
            label=l1_label,
            level=1,
            x=center_x,
            y=top_row_y,
        )
    )
    add_edge("artworkA", "L1", "direct")
    add_edge("artworkB", "L1", "direct")

    # Artist nodes
    nodes.append(
        DiagramNode(
            id="artistA",
            type="artist",
            label=artist_a_label,
            level=2,
            x=left_x,
            y=top_row_y + row_spacing,
        )
    )
    nodes.append(
        DiagramNode(
            id="artistB",
            type="artist",
            label=artist_b_label,
            level=2,
            x=right_x,
            y=top_row_y + row_spacing,
        )
    )
    add_labeled_edge("artworkA", "artistA", "Created by", "contextual")
    add_labeled_edge("artworkB", "artistB", "Created by", "contextual")

    theme_nodes: List[DiagramNode] = []
    influence_nodes: List[DiagramNode] = []
    level3_nodes: List[DiagramNode] = []

    if subject_term and l1_source != "subject":
        theme_nodes.append(
            DiagramNode(
                id="L2",
                type="theme",
                label=f"Shared {subject_term} focus",
                level=2,
            )
        )

    if teacher:
        level3_nodes.append(
            DiagramNode(
                id="teacher",
                type="teacher",
                label=teacher,
                level=3,
            )
        )

    influences_a = extract_influences(artist_a_label, summary_body)
    influences_b = extract_influences(artist_b_label, summary_body)
    influence_lookup: Dict[str, DiagramNode] = {}

    def normalize_id(text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
        return slug.strip("_") or "influence"

    for name in influences_a + influences_b:
        if name.lower() in {artist_a_label.lower(), artist_b_label.lower()}:
            continue
        node_id = f"influence_{normalize_id(name)}"
        if node_id not in influence_lookup:
            influence_lookup[node_id] = DiagramNode(
                id=node_id,
                type="artist",
                label=name,
                level=2,
            )

    influence_nodes.extend(influence_lookup.values())

    def position_level_nodes(nodes_list: List[DiagramNode], level: int, row_index: int) -> None:
        if not nodes_list:
            return
        total_width = (len(nodes_list) - 1) * 240
        start_x = canvas_width / 2 - total_width / 2 - category_width / 2
        for idx, node in enumerate(nodes_list):
            node.x = start_x + idx * 240
            node.y = top_row_y + row_spacing * row_index
            node.level = level

    row_index = 2
    if theme_nodes:
        position_level_nodes(theme_nodes, 2, row_index)
        row_index += 1
    if level3_nodes:
        position_level_nodes(level3_nodes, 3, row_index)
        row_index += 1
    nodes.extend(theme_nodes)
    nodes.extend(influence_nodes)
    nodes.extend(level3_nodes)

    for node in theme_nodes:
        add_labeled_edge("artworkA", node.id, "Shared theme", "interpretive")
        add_labeled_edge("artworkB", node.id, "Shared theme", "interpretive")
    influences_a_lower = {name.lower() for name in influences_a}
    influences_b_lower = {name.lower() for name in influences_b}
    for node in influence_nodes:
        label_lower = node.label.lower()
        if label_lower in influences_a_lower:
            add_labeled_edge("artistA", node.id, "Influenced by", "contextual")
        if label_lower in influences_b_lower:
            add_labeled_edge("artistB", node.id, "Influenced by", "contextual")
    for node in level3_nodes:
        if node.type == "teacher":
            add_labeled_edge("artistA", node.id, "Studied under", "contextual")
            add_labeled_edge("artistB", node.id, "Studied under", "contextual")
        elif node.type == "artist":
            add_labeled_edge("artistA", node.id, "Shared circle", "contextual")
            add_labeled_edge("artistB", node.id, "Shared circle", "contextual")
        else:
            add_labeled_edge("artworkA", node.id, "Context", "contextual")
            add_labeled_edge("artworkB", node.id, "Context", "contextual")

    if movement and (l1_source != "movement"):
        movement_row_index = max(row_index, 3)
        nodes.append(
            DiagramNode(
                id="movement",
                type="movement",
                label=movement,
                level=4,
                x=center_x,
                y=top_row_y + row_spacing * movement_row_index,
            )
        )
        add_labeled_edge(
            "artistA",
            "movement",
            f"Part of the {movement} movement",
            "contextual",
        )
        add_labeled_edge(
            "artistB",
            "movement",
            f"Part of the {movement} movement",
            "contextual",
        )

    diagram = DiagramPayload(nodes=nodes, edges=edges, layout=DiagramLayout(direction="TB"))
    validate_diagram_payload(diagram)
    return diagram
