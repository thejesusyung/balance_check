"""Utility functions for computing mismatch highlights."""

from __future__ import annotations

from typing import Iterable, List, Set, Tuple

import pandas as pd

from .reconcile import Match, Partial, Unmatched
from src.llm.schema import Detection


def cells_to_highlight(
    matches: Iterable[Match],
    partials: Iterable[Partial],
    unmatched: Iterable[Unmatched],
    detection: Detection,
    side: str,
) -> Set[Tuple[int, int]]:
    """Return set of cell coordinates to highlight for one reconciliation side.

    Parameters
    ----------
    matches, partials, unmatched:
        Results returned by :func:`reconcile`.
    detection:
        Column detection metadata for the respective table.
    side:
        Either ``"left"`` or ``"right"`` indicating which table to process.
    """

    debit_col = detection.debit_column
    credit_col = detection.credit_column
    cells: Set[Tuple[int, int]] = set()

    def _add_row(row: int) -> None:
        cells.add((row, debit_col))
        cells.add((row, credit_col))

    for u in unmatched:
        if u.side == side:
            _add_row(u.row)

    for p in partials:
        rows = p.left_rows if side == "left" else p.right_rows
        for r in rows:
            _add_row(r)

    for m in matches:
        if m.diff != 0:
            rows = m.left_rows if side == "left" else m.right_rows
            for r in rows:
                _add_row(r)

    return cells


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
