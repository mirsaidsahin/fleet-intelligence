"""Small table helpers shared by the record, dispatch and report views."""
from __future__ import annotations

import pandas as pd


def search_frame(frame: pd.DataFrame, query: str) -> pd.DataFrame:
    """Keep rows where any visible value contains `query`, ignoring case."""
    query = query.strip()
    if not query:
        return frame
    mask = frame.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
    return frame[mask]
