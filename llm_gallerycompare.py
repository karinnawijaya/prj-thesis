# llm_gallerycompare.py to generate summary (string) and structured spec (JSON)
from __future__ import annotations
import json
import os
from typing import Dict, Any
from openai import OpenAI

def _get_openai_client() -> OpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or Streamlit secrets.")
    return OpenAI(api_key=api_key)

SYSTEM_PROMPT = """GalleryCompare analyzes and compares two artworks using the provided dataset.
It identifies both broad contextual links (movement, era, location) and specific relational ties
(ownership, collaboration, influence, shared subject, shared exhibition, personal relationship).

Keep broad context brief and use the specific connection as the central insight.
All information must be factual and dataset-based — no assumptions or invented context."""

def generate_summary_and_spec(art_a_meta: Dict[str, Any], art_b_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      {
        "summary_text": "<string shown in UI>",
        "comparison_spec": {... structured backend object ...}
      }
    """

    # Schema: summary string for UI + structured spec for backend diagram logic
    schema_hint = {
        "summary_text": "**Overview**\n- Artwork A: [title], [artist], [year]\n- Artwork B: [title], [artist], [year]\n\n**Comparison Summary**\n<one paragraph>",
        "comparison_spec": {
            "artwork_a": {"title": "", "artist": "", "year": ""},
            "artwork_b": {"title": "", "artist": "", "year": ""},
            "broad_context": {
                "type": "movement|era|location|mixed|unknown",
@@ -43,35 +48,36 @@ def generate_summary_and_spec(art_a_meta: Dict[str, Any], art_b_meta: Dict[str,
            }
        }
    }

    user_prompt = f"""
You will be given dataset metadata for two artworks.

Artwork A metadata (dataset fields):
{json.dumps(art_a_meta, ensure_ascii=False, indent=2, default=str)}

Artwork B metadata (dataset fields):
{json.dumps(art_b_meta, ensure_ascii=False, indent=2, default=str)}

Output format rules:
- Return VALID JSON ONLY (no markdown).
- Must match this exact shape:
{json.dumps(schema_hint, ensure_ascii=False, indent=2)}

Comparison logic:
- Broad context: short phrase on movement/era/region (brief).
- Specific relation: detailed factual link (emphasize this more).
- If a field is missing, acknowledge it in missing_fields_used and explain briefly in notes.
- If you cannot identify a specific relation, set specific_relation.type="unknown" and explain in notes.
"""

    client = _get_openai_client()
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return json.loads(resp.output_text)