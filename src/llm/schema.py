from __future__ import annotations

from typing import List
from pydantic import BaseModel

class Detection(BaseModel):
    """Model returned by the LLM column detector."""

    debit_column: int
    credit_column: int
    header_row: int
    start_row: int
    end_row: int
    group_keys: List[str]
