from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import re


def load_paintings(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    return df


def guess_title_column(df: pd.DataFrame) -> str:
    # Prefer common names, but match case-insensitively
    normalized_columns = {str(col).strip().lower(): col for col in df.columns}
    for c in ["title", "artwork_title", "artwork title", "painting_title"]:
        if c in normalized_columns:
            return normalized_columns[c]
    # Fall back to first column
    return df.columns[0]


def _to_jsonable(v: Any) -> Any:
    if v is None:
        return None
    # pandas missing values
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    # numpy -> python
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.bool_):
        return bool(v)

    # pandas Timestamp -> string
    if isinstance(v, pd.Timestamp):
        return v.isoformat()

    # already ok
    if isinstance(v, (str, int, float, bool)):
        return v

    # fallback
    return str(v)


def row_to_meta(row: pd.Series) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    for k in row.index:
        v2 = _to_jsonable(row[k])
        if v2 is not None and v2 != "":
            meta[str(k)] = v2
    return meta


def get_two_paintings_by_title(
    df: pd.DataFrame,
    title_col: str,
    a_title: str,
    b_title: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    a_row = df[df[title_col].astype(str) == str(a_title)].iloc[0]
    b_row = df[df[title_col].astype(str) == str(b_title)].iloc[0]
    return row_to_meta(a_row), row_to_meta(b_row)


def list_titles(df: pd.DataFrame, title_col: str) -> List[str]:
    titles = df[title_col].dropna()
    titles = titles.astype(str).str.strip()
    filtered = [title for title in titles.tolist() if title and title.lower() not in {"nan", "none"}]
    return list(dict.fromkeys(filtered))


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "unknown"


def build_painting_options(df: pd.DataFrame, title_col: str, image_root: str) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    for title in list_titles(df, title_col):
        slug = _slugify_title(title)
        options.append(
            {
                "title": title,
                "image_path": f"{image_root}/{slug}.jpg",
            }
        )
    return options