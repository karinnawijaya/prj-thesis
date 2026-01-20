# diagram_builder.py to create readable diagram and Cytoscape JSON
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Tuple

from openai import OpenAI


def _get_openai_client() -> OpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or Streamlit secrets.")
    return OpenAI(api_key=api_key)


DIAGRAM_SENTENCE_SYSTEM = """You write concise, highly readable, factual linking sentences for diagram nodes.
Use ONLY the provided comparison_spec + summary_text.
No invented facts. One sentence per node. Plain language."""


def _artwork_label(prefix: str, art: Dict[str, Any]) -> str:
    title = art.get("title") or "Unknown Title"
    artist = art.get("artist") or "Unknown Artist"
    year = art.get("year") or "Unknown Year"
    return f"{prefix} — {title} ({artist}, {year})"


from typing import Dict, Any, List

def _make_cytoscape(diagram_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal diagram JSON into Cytoscape elements.
    """
    elements = {"nodes": [], "edges": []}

    for node in diagram_json.get("nodes", []):
        elements["nodes"].append({
            "data": {
                "id": node.get("id"),
                "label": node.get("label", node.get("id")),
                **{k: v for k, v in node.items() if k not in {"id", "label"}}
            }
        })

    for edge in diagram_json.get("edges", []):
        elements["edges"].append({
            "data": {
                "id": f'{edge.get("source")}->{edge.get("target")}',
                "source": edge.get("source"),
                "target": edge.get("target"),
                "label": edge.get("label", "")
            }
        })

    return elements



def cytoscape_to_ascii(elements: Dict[str, Any], root_id: str | None = None) -> str:
    nodes = elements.get("nodes", []) if isinstance(elements, dict) else []
    edges = elements.get("edges", []) if isinstance(elements, dict) else []

    node_ids: List[str] = []
    labels: Dict[str, str] = {}
    for node in nodes:
        data = node.get("data", {}) if isinstance(node, dict) else {}
        node_id = str(data.get("id", ""))
        if not node_id:
            continue
        node_ids.append(node_id)
        labels[node_id] = str(data.get("label") or node_id)

    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
    indegree: Dict[str, int] = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        data = edge.get("data", {}) if isinstance(edge, dict) else {}
        source = str(data.get("source", ""))
        target = str(data.get("target", ""))
        if not source or not target:
            continue
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append(target)
        if target in indegree:
            indegree[target] += 1
        else:
            indegree[target] = 1
        labels.setdefault(source, source)
        labels.setdefault(target, target)

    root = None
    if root_id and root_id in labels:
        root = root_id
    if root is None:
        for node_id in node_ids:
            if indegree.get(node_id, 0) == 0:
                root = node_id
                break
    if root is None and node_ids:
        root = node_ids[0]

    if not root:
        return ""

    def sorted_children(children: Iterable[str]) -> List[str]:
        return sorted(children, key=lambda child: labels.get(child, child).lower())

    lines: List[str] = []

    def walk(node_id: str, depth: int, path: set[str]) -> None:
        label = labels.get(node_id, node_id)
        indent = "  " * depth
        if node_id in path:
            lines.append(f"{indent}{label} (cycle)")
            return
        lines.append(f"{indent}{label}")
        next_path = set(path)
        next_path.add(node_id)
        for child in sorted_children(adjacency.get(node_id, [])):
            walk(child, depth + 1, next_path)

    walk(root, 0, set())
    return "\n".join(lines)


def _generate_level_sentences(comparison_spec: Dict[str, Any], summary_text: str) -> Dict[str, str]:
    """
    Returns one-sentence labels for AB (L1), L2, L3, L4.
    AB must be concrete and explicit (like your Monet sentence).
    """
    user_prompt = f"""
You will produce 1 readable sentence per node label for a diagram.

Inputs:
comparison_spec:
{json.dumps(comparison_spec, ensure_ascii=False, indent=2)}

summary_text:
{summary_text}

Rules:
- Output VALID JSON ONLY with keys: "AB", "L2", "L3", "L4".
- Each value MUST be exactly ONE sentence, readable to a general museum visitor.
- AB (Level 1) MUST state the core factual link clearly and explicitly (e.g., "Renoir painted X and Manet painted Y, both linked to Monet...").
- L4 should reflect broad_context ONLY if it adds meaning; if broad_context is unknown or redundant, set L4 to an empty string "".
- No invented facts. If something is uncertain, phrase carefully and stay within the provided inputs.
"""

    client = _get_openai_client()
    resp = client.responses.create(
@@ -135,26 +202,44 @@ def build_readable_diagrams(
    # Edges (with explicit A ↔ B)
    edges: List[Dict[str, Any]] = [
        _edge("A", "AB", "direct", "Artwork A supports the core link"),
        _edge("B", "AB", "direct", "Artwork B supports the core link"),
        _edge("A", "B", "direct_comparison", "Artwork A and Artwork B are compared through this shared connection"),
        _edge("AB", "L2", "interpretive", "The core link connects to a shared theme"),
        _edge("A", "L2", "interpretive", "Artwork A expresses the shared theme"),
        _edge("B", "L2", "interpretive", "Artwork B expresses the shared theme"),
        _edge("L2", "L3", "contextual", "The shared theme is supported by shared networks/context"),
    ]

    if any(n["id"] == "L4" for n in nodes):
        edges.append(_edge("L3", "L4", "contextual", "This context sits within the broader art-historical framework"))

    diagram_json: Dict[str, Any] = {
        "direction": "top-to-bottom",
        "nodes": nodes,
        "edges": edges,
        "layout_hint": (
            "Place AB (Level 1) at the top center; place Artwork A left and Artwork B right beneath it; "
            "stack Levels 2–4 downward in the center; keep the A↔B edge as a cross-connection."
        ),
    }

    cytoscape_json = _make_cytoscape(diagram_json)
    return diagram_json, cytoscape_json


if __name__ == "__main__":
    sample_elements = {
        "nodes": [
            {"data": {"id": "root", "label": "Root"}},
            {"data": {"id": "child-a", "label": "Child A"}},
            {"data": {"id": "child-b", "label": "Child B"}},
            {"data": {"id": "leaf", "label": "Leaf"}},
        ],
        "edges": [
            {"data": {"source": "root", "target": "child-a"}},
            {"data": {"source": "root", "target": "child-b"}},
            {"data": {"source": "child-a", "target": "leaf"}},
            {"data": {"source": "leaf", "target": "root"}},
        ],
    }
    print(cytoscape_to_ascii(sample_elements))