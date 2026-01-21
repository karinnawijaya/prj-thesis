# app.py for Streamlit UI
import os

import streamlit as st

from data_store import (
    build_painting_options,
    get_two_paintings_by_title,
    guess_title_column,
    load_paintings,
)
from diagram_builder import build_readable_diagrams, _make_cytoscape
from diagram_builder import build_readable_diagrams, cytoscape_to_ascii
from llm_gallerycompare import generate_summary_and_spec

st.set_page_config(page_title="ArtWeave → Diagram", layout="wide")
st.title("ArtWeave")

ALLOWED_TITLES = [
    "Dancers Practicing at the Barre",
    "Madame Manet (Suzanne Leenhoff, 1829–1906) at Bellevue",
    "The Garden of the Tuileries on a Winter Afternoon",
    "By the Seashore",
    "The Bridge at Villeneuve-la-Garenne",
]

if not os.getenv("OPENAI_API_KEY") and "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = str(st.secrets["OPENAI_API_KEY"]).strip()

if not os.getenv("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY not found. Set it to enable summary/diagram generation.")

# Load dataset
df = load_paintings("Painting_Metadata_251030.csv")
title_col = guess_title_column(df)
all_painting_options = build_painting_options(df, title_col, "assets/paintings")
options_by_title = {option["title"]: option for option in all_painting_options}
missing_titles = [title for title in ALLOWED_TITLES if title not in options_by_title]
if missing_titles:
    st.error(
        "Some required paintings are missing from the dataset or assets: "
        + ", ".join(missing_titles)
    )
    st.stop()
painting_options = [options_by_title[title] for title in ALLOWED_TITLES]


def render_painting_selector(
    label: str,
    options: list[dict[str, str]],
    state_key: str,
    columns: int = 4,
) -> str:
    # Streamlit's selectbox can't render images in options; use a card grid instead.
    st.subheader(label)
    if not options:
        st.warning("No paintings available to select.")
        return ""
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0]["title"]

    selected_title = st.session_state.get(state_key, "")
    st.caption(f"Selected: {selected_title}" if selected_title else "Selected: none")

    rows = [options[i : i + columns] for i in range(0, len(options), columns)]
    for row_idx, row in enumerate(rows):
        cols = st.columns(columns)
        for col_idx, option in enumerate(row):
            with cols[col_idx]:
                image_path = option["image_path"]
                if os.path.exists(image_path):
                    st.image(image_path, use_column_width=True)
                else:
                    st.info("Image not found", icon="🖼️")
                st.caption(option["title"])
                is_selected = option["title"] == selected_title
                button_label = "Selected" if is_selected else "Select"
                if st.button(button_label, key=f"{state_key}-{row_idx}-{col_idx}"):
                    st.session_state[state_key] = option["title"]
    return st.session_state.get(state_key, "")


c1, c2 = st.columns(2)
with c1:
    a_title = render_painting_selector("Choose painting A", painting_options, "painting_a_title")
with c2:
    b_title = render_painting_selector("Choose painting B", painting_options, "painting_b_title")

st.divider()

if st.button("1) Generate overview summary", type="primary"):
    missing_selection = [
        title for title in (a_title, b_title) if title not in ALLOWED_TITLES
    ]
    if missing_selection:
        st.error(
            "Please choose a painting from the allowed list: "
            + ", ".join(missing_selection)
        )
        st.stop()
    if (
        df[df[title_col].astype(str) == str(a_title)].empty
        or df[df[title_col].astype(str) == str(b_title)].empty
    ):
        st.error(
            "One or more selected paintings could not be found in the dataset. "
            "Please choose a different painting."
        )
        st.stop()
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
        st.warning("Please generate the overview summary first.")
    else:
        # your existing logic to translate to JSON
        diagram_json = build_readable_diagrams(comparison_spec, summary_text)
        cytoscape_json = _make_cytoscape(diagram_json)

        st.session_state["diagram_json"] = diagram_json
        st.session_state["cytoscape_json"] = cytoscape_json
        st.session_state["cyto_elements"] = cytoscape_json.get("elements", {})
        st.session_state["ascii_diagram"] = cytoscape_to_ascii(
            st.session_state["cyto_elements"]
        )

diagram_json = st.session_state.get("diagram_json")
cytoscape_json = st.session_state.get("cytoscape_json")
cyto_elements = st.session_state.get("cyto_elements")
ascii_diagram = st.session_state.get("ascii_diagram")

if diagram_json:
    st.json(diagram_json)
else:
    st.info("Generate the readable diagram JSON first.")

if cytoscape_json:
    st.subheader("Cytoscape JSON (elements + layout)")
    st.json(cytoscape_json)
else:
    st.info("Generate the Cytoscape JSON first.")

st.subheader("Diagram Structure Summary (in text form)")
if ascii_diagram:
    st.code(ascii_diagram, language="text")
else:
    st.warning("Generate the diagram first to see the text summary.")