"""Placeholder for highlighting logic."""

from __future__ import annotations

from typing import Set, Tuple

import pandas as pd


def highlight_mismatches(df: pd.DataFrame, mismatch_rows: Set[Tuple[int, int]]) -> pd.DataFrame:
    """Return DataFrame copy with mismatching cells marked.

    Parameters
    ----------
    df : pandas.DataFrame
        Input table.
    mismatch_rows : set[tuple[int, int]]
        Cell coordinates to highlight.
    """
    return df.copy()
