# diagram_builder.py to create readable diagram and Cytoscape JSON
from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Tuple
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

def _node(node_id: str, label: str, node_type: str, level: int | None = None) -> Dict[str, Any]:
    n: Dict[str, Any] = {"id": node_id, "type": node_type, "label": label}
    if level is not None:
        n["level"] = level
    return n

def _edge(source: str, target: str, relation: str, label: str) -> Dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, "label": label}

def _make_cytoscape(diagram_json: Dict[str, Any]) -> Dict[str, Any]:
    cy_nodes = []
    for n in diagram_json.get("nodes", []):
        data = {"id": n["id"], "label": n.get("label", ""), "type": n.get("type", "")}
        if "level" in n:
@@ -57,50 +62,51 @@ def _generate_level_sentences(comparison_spec: Dict[str, Any], summary_text: str
    AB must be concrete and explicit (like your Monet sentence).
    """
    a = comparison_spec.get("artwork_a", {})
    b = comparison_spec.get("artwork_b", {})
    broad = (comparison_spec.get("broad_context") or {})
    rel = (comparison_spec.get("specific_relation") or {})

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
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": DIAGRAM_SENTENCE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.25,
    )
    return json.loads(resp.output_text)

def build_readable_diagrams(comparison_spec: Dict[str, Any], summary_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """ 
    Returns: (diagram_json, cytoscape_json)
    Diagram tweak implemented:
      - AB bridge node at Level 1 (readable sentence)
      - explicit A<->B edge
      - L2-L4 are one-sentence nodes (more elaborate and clear)
      - top-to-bottom direction metadata + cytoscape breadthfirst layout roots=["AB"]
    """
    art_a = comparison_spec.get("artwork_a", {})
    art_b = comparison_spec.get("artwork_b", {})

    sentences = _generate_level_sentences(comparison_spec, summary_text)

    nodes: List[Dict[str, Any]] = [