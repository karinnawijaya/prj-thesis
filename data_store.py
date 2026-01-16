# data_store.py to select two painting and load csvcd
from __future__ import annotations
import pandas as pd
from typing import Dict, Any, Tuple, List

def load_paintings(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df

def guess_title_column(df: pd.DataFrame) -> str:
    # Prefer common names
    for c in ["title", "Title", "artwork_title", "Artwork title", "Artwork Title", "painting_title"]:
        if c in df.columns:
            return c
    # Fall back to first column
    return df.columns[0]

def row_to_meta(row: pd.Series) -> Dict[str, Any]:
    """
    Pass through all non-null fields to the LLM so it can stay dataset-grounded.
    """
    meta: Dict[str, Any] = {}
    for k in row.index:
        v = row[k]
        if pd.notna(v):
            meta[str(k)] = v
    return meta

def get_two_paintings_by_title(df: pd.DataFrame, title_col: str, a_title: str, b_title: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    a_row = df[df[title_col].astype(str) == str(a_title)].iloc[0]
    b_row = df[df[title_col].astype(str) == str(b_title)].iloc[0]
    return row_to_meta(a_row), row_to_meta(b_row)

def list_titles(df: pd.DataFrame, title_col: str) -> List[str]:
    return df[title_col].astype(str).tolist()
