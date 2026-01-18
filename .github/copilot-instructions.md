# GalleryCompare AI Coding Guidelines

## Project Overview
This is a Streamlit web app for comparing two paintings from a CSV dataset. It uses OpenAI LLM to generate factual summaries and structured comparison specs, then builds readable diagram JSON for visualization.

## Architecture
- **app.py**: Main Streamlit UI with session state for workflow (select paintings → generate summary → build diagram)
- **data_store.py**: Pandas-based CSV loading and metadata extraction (guesses title column, converts rows to dicts)
- **llm_gallerycompare.py**: OpenAI integration for summary text and structured comparison_spec JSON
- **diagram_builder.py**: Generates diagram nodes/edges JSON and Cytoscape format using LLM for readable sentences

Data flow: CSV → DataFrame → Select two paintings → LLM summary/spec → LLM diagram sentences → JSON diagram

## Key Workflows
- Run with: `streamlit run app.py` (requires `OPENAI_API_KEY` env var)
- No build/test process; direct Python execution
- UI workflow: Load data → Select titles → Generate summary → Translate to diagram

## Patterns & Conventions
- **LLM Integration**: Use `openai.OpenAI().responses.create()` with `model="gpt-4.1-mini"`, structured JSON prompts with schema hints, temperature 0.25-0.3
- **Prompt Engineering**: System prompt for context, user prompt with inputs + output format rules (VALID JSON ONLY)
- **Data Handling**: Pandas DataFrame for CSV, convert rows to dicts excluding nulls (`pd.notna(v)`)
- **UI State**: Streamlit session_state for intermediate results (summary_text, comparison_spec, diagram_json)
- **Diagram Structure**: Fixed node IDs (A, B, AB, L2-L4), edges with relation types, top-to-bottom layout

## Examples
- Title guessing: Check columns like "title", "Title", "artwork_title" before falling back to df.columns[0]
- Comparison spec: JSON with artwork_a/b, broad_context (type: movement|era|location), specific_relation (type: ownership|influence|shared_subject)
- Node labels: Artwork nodes use "Artwork A — {title} ({artist}, {year})", connection nodes use LLM-generated sentences

Reference: `app.py` for UI flow, `llm_gallerycompare.py` for prompt patterns, `diagram_builder.py` for JSON structure</content>
<parameter name="filePath">/Users/karinawijaya/Documents/GitHub/prj-thesis/.github/copilot-instructions.md