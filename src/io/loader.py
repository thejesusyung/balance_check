"""Excel file loading utilities."""

from __future__ import annotations

from typing import Literal, Tuple, Dict, Any, Optional, Pattern, List

import re

import pandas as pd


def infer_engine(path: str) -> Literal["openpyxl", "xlrd"]:
    """Infer the pandas engine based on file extension.

    Parameters
    ----------
    path: str
        Path to the Excel file.

    Returns
    -------
    Literal["openpyxl", "xlrd"]
        The engine name to use with ``pandas.read_excel``.
    """

    lowered = path.lower()
    if lowered.endswith(".xlsx"):
        return "openpyxl"
    if lowered.endswith(".xls"):
        return "xlrd"
    raise ValueError(f"Unsupported file extension in '{path}'.")


def read_excel(path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Read an Excel file and capture sheet metadata.

    The function loads the first sheet into a ``pandas.DataFrame`` and
    returns a mapping containing the sheet name and original cell
    coordinates (row and column indices starting from 1).

    Parameters
    ----------
    path: str
        Path to the Excel file.

    Returns
    -------
    tuple[pandas.DataFrame, dict]
        The dataframe of the sheet contents and a metadata dictionary.
    """

    engine = infer_engine(path)
    try:
        df = pd.read_excel(path, engine=engine)
    except Exception as exc:  # pragma: no cover - tested via unit tests
        raise RuntimeError(f"Failed to read Excel file '{path}': {exc}") from exc

    # Build coordinates mapping
    coordinates: Dict[str, Any] = {
        "sheet_name": df.attrs.get("sheet_name", getattr(df, "sheet_name", None)),
        "row_coords": list(range(1, len(df) + 1)),
        "col_coords": list(range(1, len(df.columns) + 1)),
    }

    return df, coordinates


def _parse_numeric(value: Any) -> Optional[float]:
    """Parse a numeric value from arbitrary cell contents."""

    if isinstance(value, (int, float)):
        return float(value)
    try:
        num = pd.to_numeric(value, errors="coerce")
    except Exception:
        num = pd.NA
    if pd.isna(num):
        try:
            cleaned = str(value).replace("\xa0", "").replace(" ", "").replace(",", ".")
            num = pd.to_numeric(cleaned, errors="coerce")
        except Exception:
            return None
    return None if pd.isna(num) else float(num)


_DEFAULT_PATTERNS: List[Pattern[str]] = [
    re.compile(r"оборот.*период", re.IGNORECASE),
    re.compile(r"turnover.*period", re.IGNORECASE),
]


def detect_turnover_value(
    df: pd.DataFrame, patterns: Optional[List[Pattern[str]]] = None, offset: int = 1
) -> Optional[float]:
    """Scan ``df`` for turnover labels and return the numeric value to the right.

    Parameters
    ----------
    df : pandas.DataFrame
        Table to search.
    patterns : list of regex patterns, optional
        Custom patterns to match labels. Defaults to Russian and English
        "turnover for period" patterns.
    offset : int, default ``1``
        How many columns to skip to the right from the matched cell to read the
        numeric value.

    Returns
    -------
    float or ``None``
        Parsed turnover value if a label is found and numeric parsing succeeds.
    """

    pats = patterns or _DEFAULT_PATTERNS
    n_rows, n_cols = df.shape
    for r in range(n_rows):
        for c in range(n_cols):
            cell = str(df.iat[r, c])
            if any(p.search(cell) for p in pats):
                val_col = c + offset
                if val_col >= n_cols:
                    continue
                value = _parse_numeric(df.iat[r, val_col])
                if value is not None:
                    return value
    return None

