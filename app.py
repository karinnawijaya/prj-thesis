# app.py for Streamlit UI
import os
import streamlit as st

from data_store import load_paintings, guess_title_column, list_titles, get_two_paintings_by_title
from llm_gallerycompare import generate_summary_and_spec
from diagram_builder import build_readable_diagrams

st.set_page_config(page_title="ArtWeave → Diagram", layout="wide")
st.title("ArtWeave → Summary → Diagram JSON")

if not os.getenv("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY not found. Set it to enable summary/diagram generation.")

# Load dataset
df = load_paintings("Painting_Metadata_251030.csv")
title_col = guess_title_column(df)
titles = list_titles(df, title_col)

c1, c2 = st.columns(2)
with c1:
    a_title = st.selectbox("Choose painting A", titles, index=0)
with c2:
    b_title = st.selectbox("Choose painting B", titles, index=1 if len(titles) > 1 else 0)

st.divider()

if st.button("1) Generate overview summary", type="primary"):
    a_meta, b_meta = get_two_paintings_by_title(df, title_col, a_title, b_title)
    out = generate_summary_and_spec(a_meta, b_meta)
    st.session_state["summary_text"] = out["summary_text"]
    st.session_state["comparison_spec"] = out["comparison_spec"]

summary_text = st.session_state.get("summary_text", "")
comparison_spec = st.session_state.get("comparison_spec", None)

st.subheader("Overview summary (string)")
st.text_area("Summary", value=summary_text, height=220)

with st.expander("Backend comparison_spec (JSON)"):
    if comparison_spec:
        st.json(comparison_spec)
    else:
        st.info("Generate the summary first.")

st.divider()

if st.button("2) Translate to JSON diagram (readable nodes)"):
    if not comparison_spec or not summary_text.strip():
        st.error("Please generate the summary first.")
    else:
        diagram_json, cytoscape_json = build_readable_diagrams(comparison_spec, summary_text)
        st.session_state["diagram_json"] = diagram_json
        st.session_state["cytoscape_json"] = cytoscape_json

col3, col4 = st.columns(2)
with col3:
    st.subheader("Diagram JSON")
    if "diagram_json" in st.session_state:
        st.json(st.session_state["diagram_json"])
    else:
        st.info("Generate the diagram to see JSON.")

with col4:
    st.subheader("Cytoscape JSON")
    if "cytoscape_json" in st.session_state:
        st.json(st.session_state["cytoscape_json"])
    else:
        st.info("Generate the diagram to see Cytoscape JSON.")
