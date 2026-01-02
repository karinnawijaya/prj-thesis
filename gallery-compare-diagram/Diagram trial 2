# diagram_to_cytoscape.py
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Literal, Optional

import pandas as pd

CSV_PATH_DEFAULT = "/mnt/data/Painting_Metadata_251030.csv"
EdgeKind = Literal["direct", "contextual", "interpretive"]

DIAGRAM_PROMPT_TEMPLATE = """\
You convert an artwork comparison into a non-sequential relational diagram.

Grounding rule:
- Use ONLY what is present in the provided summary. Do NOT invent facts.

Input:
Artwork A: {artwork_a}
Artwork B: {artwork_b}
Comparison Summary: {summary}

Rules:
- Create up to 4 level nodes (levels 1–4). Omit weak levels.
- Levels are conceptual (NOT sequential). Any level can connect to either artwork.
- Include cross-links between levels only if supported by the summary.
- Each artwork is its own node.

Output MUST be valid JSON ONLY (no markdown), in Cytoscape format:

{{
  "elements": {{
    "nodes": [
      {{ "data": {{ "id":"artwork_a", "label":"Artwork A — ...", "type":"artwork", "level":0 }} }},
      {{ "data": {{ "id":"artwork_b", "label":"Artwork B — ...", "type":"artwork", "level":0 }} }},
      {{ "data": {{ "id":"lvl1", "label":"...", "type":"level", "level":1 }} }}
    ],
    "edges": [
      {{ "data": {{ "id":"e1", "source":"artwork_a", "target":"lvl1", "kind":"direct" }} }}
    ]
  }},
  "layoutHint": "short textual layout hint"
}}

Constraints:
- Must include artwork nodes with ids "artwork_a" and "artwork_b".
- Level nodes: max 4 total, levels 1–4.
- Edge.kind must be one of: direct, contextual, interpretive.
- Every edge source/target must match an existing node id.
- If unsure, omit rather than guess.
"""

# ---------- CSV helpers ----------

def load_metadata(csv_path: str = CSV_PATH_DEFAULT) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    return df

def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def find_row_by_title(df: pd.DataFrame, title: str) -> pd.Series:
    if "Title" not in df.columns:
        raise ValueError("CSV missing column: Title")
    titles = df["Title"].fillna("").astype(str)

    target = _normalize_text(title)
    exact = titles.map(_normalize_text) == target
    if exact.any():
        return df[exact].iloc[0]

    contains = titles.map(_normalize_text).map(lambda t: target in t)
    if contains.any():
        return df[contains].iloc[0]

    raise ValueError(f'Title not found: "{title}"')

def artwork_label(row: pd.Series) -> str:
    title = str(row.get("Title", "")).strip()
    artist = str(row.get("Artist", "")).strip()
    year = row.get("Year", None)
    year_str = str(int(year)) if pd.notna(year) and str(year).isdigit() else "Unknown year"
    return f"{title}, {artist}, {year_str}"

def stable_artwork_id(title: str, artist: str, year: Any) -> str:
    # UI can still be title-only; this is just internal stability if you ever need it.
    base = f"{title}|{artist}|{year}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]

# ---------- LLM call (OpenAI) ----------

def call_llm_openai(prompt: str, model: str = "gpt-4.1-mini", temperature: float = 0.2) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError("Set OPENAI_API_KEY to call the LLM.")

    from openai import OpenAI  # pip install openai
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON. No markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""

# ---------- Parse + validate ----------

def _parse_json_strict(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError("LLM output did not contain JSON.")
        return json.loads(m.group(0))

def validate_cytoscape_diagram(d: Dict[str, Any]) -> None:
    if "elements" not in d or not isinstance(d["elements"], dict):
        raise ValueError("Missing 'elements' object.")

    nodes = d["elements"].get("nodes", [])
    edges = d["elements"].get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("'nodes' and 'edges' must be lists.")

    node_ids = set()
    for n in nodes:
        nid = n.get("data", {}).get("id")
        if not nid:
            raise ValueError("Node missing data.id")
        if nid in node_ids:
            raise ValueError(f"Duplicate node id: {nid}")
        node_ids.add(nid)

    if {"artwork_a", "artwork_b"} - node_ids:
        raise ValueError("Must include nodes artwork_a and artwork_b.")

    # Level constraints
    level_nodes = [
        n for n in nodes
        if n.get("data", {}).get("type") == "level"
    ]
    if len(level_nodes) > 4:
        raise ValueError("Max 4 level nodes allowed.")
    for n in level_nodes:
        lvl = n.get("data", {}).get("level")
        if not isinstance(lvl, int) or not (1 <= lvl <= 4):
            raise ValueError(f"Level node must have integer level 1–4. Got: {lvl}")

    valid_kinds = {"direct", "contextual", "interpretive"}
    for e in edges:
        data = e.get("data", {})
        if data.get("source") not in node_ids or data.get("target") not in node_ids:
            raise ValueError(f"Edge references unknown node: {data}")
        if data.get("kind") not in valid_kinds:
            raise ValueError(f"Invalid edge kind: {data.get('kind')}")

def generate_diagram_cytoscape(
    title_a: str,
    title_b: str,
    summary: str,
    csv_path: str = CSV_PATH_DEFAULT,
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    df = load_metadata(csv_path)
    row_a = find_row_by_title(df, title_a)
    row_b = find_row_by_title(df, title_b)

    label_a = artwork_label(row_a)
    label_b = artwork_label(row_b)

    prompt = DIAGRAM_PROMPT_TEMPLATE.format(
        artwork_a=label_a,
        artwork_b=label_b,
        summary=summary.strip(),
    )

    raw = call_llm_openai(prompt, model=model)
    diagram = _parse_json_strict(raw)
    validate_cytoscape_diagram(diagram)
    return diagram
