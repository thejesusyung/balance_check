from __future__ import annotations

from textwrap import dedent
import pandas as pd


FEW_SHOT = dedent(
    """
    You are given CSV data from an accounting workbook. Identify which columns
    hold debit and credit amounts.

    Example CSV:
    date,debit,credit
    2024-01-01,100,0
    2024-01-02,0,50

    Example answer:
    {"debit_column":1,"credit_column":2,"header_row":0,"start_row":1,"end_row":3,"group_keys":["date"]}
    """
)


def build_prompt(df: pd.DataFrame) -> str:
    """Create a prompt showing head and tail rows as CSV."""
    head = df.head(7)
    tail = df.tail(7)
    sample = pd.concat([head, tail]).to_csv(index=False)

    return dedent(
        f"{FEW_SHOT}\nAnalyse the following table and respond with JSON in the same schema.\nCSV:\n{sample}"
    )
