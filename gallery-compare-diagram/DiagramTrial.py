from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

import pandas as pd
import streamlit as st


CSV_PATH_DEFAULT = "Painting_Metadata_251030.csv"

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


# ---------------- CSV helpers ----------------

@st.cache_data(show_spinner=False)
def load_metadata(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    if "Title" not in df.columns:
        raise ValueError("CSV missing required column: Title")
    return df


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def find_row_by_title(df: pd.DataFrame, title: str) -> pd.Series:
    titles = df["Title"].fillna("").astype(str)
    target = _normalize_text(title)

    exact = titles.map(_normalize_text) == target
    if exact.any():
        return df[exact].iloc[0]

    contains = titles.map(_normalize_text).map(lambda t: target in t)
    if contains.any():
        return df[contains].iloc[0]

    raise ValueError(f'Title not found in CSV: "{title}"')


def artwork_label(row: pd.Series) -> str:
    title = str(row.get("Title", "")).strip()
    artist = str(row.get("Artist", "")).strip()
    year = row.get("Year", None)

    year_str = "Unknown year"
    if pd.notna(year):
        try:
            year_str = str(int(float(year)))
        except Exception:
            year_str = str(year).strip() or "Unknown year"

    return f"{title}, {artist}, {year_str}"


# ---------------- LLM + parsing + validation ----------------

def call_llm_openai(prompt: str, model: str = "gpt-4.1-mini", temperature: float = 0.2) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it in your environment and restart Streamlit.")

    from openai import OpenAI
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


def parse_json_strict(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"LLM output did not contain JSON. Output (first 400 chars):\n{text[:400]}")
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
            raise ValueError("A node is missing data.id")
        if nid in node_ids:
            raise ValueError(f"Duplicate node id: {nid}")
        node_ids.add(nid)

    if "artwork_a" not in node_ids or "artwork_b" not in node_ids:
        raise ValueError("Must include nodes with ids: artwork_a and artwork_b")

    # Level constraints
    level_nodes = [n for n in nodes if n.get("data", {}).get("type") == "level"]
    if len(level_nodes) > 4:
        raise ValueError("Too many level nodes. Max is 4.")
    for n in level_nodes:
        lvl = n.get("data", {}).get("level")
        if not isinstance(lvl, int) or not (1 <= lvl <= 4):
            raise ValueError(f"Level node must have integer level 1–4. Got: {lvl}")

    # Edge constraints
    valid_kinds = {"direct", "contextual", "interpretive"}
    for e in edges:
        data = e.get("data", {})
        if data.get("source") not in node_ids or data.get("target") not in node_ids:
            raise ValueError(f"Edge references unknown node(s): {data}")
        if data.get("kind") not in valid_kinds:
            raise ValueError(f"Invalid edge kind: {data.get('kind')}")


def generate_diagram_json(df: pd.DataFrame, title_a: str, title_b: str, summary: str, model: str) -> Dict[str, Any]:
    if not summary or len(summary.strip()) < 20:
        raise ValueError("Summary is too short. Paste a fuller comparison summary (at least ~1–2 sentences).")

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
    diagram = parse_json_strict(raw)
    validate_cytoscape_diagram(diagram)
    return diagram


# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="GalleryCompare — Diagram Generator", layout="wide")
st.title("GalleryCompare — Diagram Generator (MVP)")
st.caption("Paste a dataset-based summary, select two artworks by title, and generate Cytoscape-ready JSON.")

with st.sidebar:
    st.subheader("Settings")
    csv_path = st.text_input("CSV path", value=CSV_PATH_DEFAULT)
    model = st.text_input("LLM model", value="gpt-4.1-mini")
    st.write("API key must be in environment: `OPENAI_API_KEY`")

try:
    df = load_metadata(csv_path)
except Exception as e:
    st.error(f"Failed to load CSV: {e}")
    st.stop()

titles = df["Title"].fillna("").astype(str).tolist()

col1, col2 = st.columns(2)

with col1:
    title_a = st.selectbox("Artwork A (Title)", options=titles, index=0)
with col2:
    title_b = st.selectbox("Artwork B (Title)", options=titles, index=1 if len(titles) > 1 else 0)

summary = st.text_area(
    "Comparison Summary (paste here)",
    height=180,
    placeholder="Both artworks ... [broad context]. [specific relation] ...",
)

generate = st.button("Generate Diagram JSON", type="primary")

if generate:
    with st.spinner("Generating diagram..."):
        try:
            diagram = generate_diagram_json(df, title_a, title_b, summary, model=model)
        except Exception as e:
            st.error(str(e))
        else:
            st.success("Diagram generated!")
            st.subheader("Cytoscape JSON")
            st.json(diagram)

            st.download_button(
                label="Download JSON",
                data=json.dumps(diagram, ensure_ascii=False, indent=2),
                file_name="diagram.json",
                mime="application/json",
            )
