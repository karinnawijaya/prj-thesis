from typing import Dict, Any, List
from collections import defaultdict


def _make_cytoscape(diagram_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal diagram JSON into Cytoscape elements format.
    """
    elements = {"nodes": [], "edges": []}

    for node in diagram_json.get("nodes", []):
        node_id = node.get("id")
        label = node.get("label", node_id)

        elements["nodes"].append({
            "data": {
                "id": node_id,
                "label": label,
                **{k: v for k, v in node.items() if k not in {"id", "label"}}
            }
        })

    for edge in diagram_json.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        label = edge.get("label", "")

        elements["edges"].append({
            "data": {
                "id": f"{source}->{target}",
                "source": source,
                "target": target,
                "label": label
            }
        })

    return elements


def build_readable_diagrams(comparison_spec: Dict[str, Any], summary_text: str = "") -> Dict[str, Any]:
    """
    Build internal diagram JSON from a comparison spec.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    root_id = "root"
    nodes.append({"id": root_id, "label": "Comparison Overview"})

    last_parent = root_id

    for i, section in enumerate(comparison_spec.get("sections", []), start=1):
        section_id = f"section_{i}"
        section_title = section.get("title", f"Section {i}")

        nodes.append({
            "id": section_id,
            "label": section_title,
            "type": "section"
        })

        edges.append({
            "source": last_parent,
            "target": section_id,
            "label": "has section"
        })

        for j, bullet in enumerate(section.get("bullets", []), start=1):
            bullet_id = f"{section_id}_bullet_{j}"
            nodes.append({
                "id": bullet_id,
                "label": bullet,
                "type": "bullet"
            })

            edges.append({
                "source": section_id,
                "target": bullet_id,
                "label": "has bullet"
            })

        last_parent = section_id

    diagram_json = {
        "nodes": nodes,
        "edges": edges,
        "summary": summary_text or ""
    }

    return diagram_json


def cytoscape_to_ascii(elements: Dict[str, Any], root_id: str | None = None) -> str:
    """
    Convert Cytoscape-style JSON elements into a readable ASCII tree.
    """
    nodes = elements.get("nodes", [])
    edges = elements.get("edges", [])

    labels = {}
    for n in nodes:
        data = n.get("data", {})
        nid = data.get("id")
        label = data.get("label", nid)
        if nid:
            labels[nid] = label

    children = defaultdict(list)
    indeg = defaultdict(int)

    for e in edges:
        d = e.get("data", {})
        s = d.get("source")
        t = d.get("target")
        if s and t:
            children[s].append(t)
            indeg[t] += 1

    if root_id and root_id in labels:
        root = root_id
    else:
        roots = [nid for nid in labels if indeg[nid] == 0]
        root = roots[0] if roots else next(iter(labels), None)

    if not root:
        return "No nodes found."

    for k in children:
        children[k].sort(key=lambda nid: labels.get(nid, nid))

    lines: List[str] = []

    def dfs(nid: str, depth: int, path: set):
        indent = "  " * depth
        label = labels.get(nid, nid)

        if nid in path:
            lines.append(f"{indent}- {label} (cycle)")
            return

        lines.append(f"{indent}- {label}")
        path.add(nid)

        for child in children.get(nid, []):
            dfs(child, depth + 1, path.copy())

    dfs(root, 0, set())
    return "\n".join(lines)
