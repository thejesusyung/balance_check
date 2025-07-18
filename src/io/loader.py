"""Excel file loading utilities."""

from __future__ import annotations

from typing import Literal, Tuple, Dict, Any

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

