from __future__ import annotations

import json
import re
import time
from typing import Optional

import openai
import pandas as pd

from . import prompts, schema


_DEBIT_RE = re.compile(r"^(дебет|дт|debit)$", re.IGNORECASE)
_CREDIT_RE = re.compile(r"^(кредит|кт|credit)$", re.IGNORECASE)


def _heuristic_detection(df: pd.DataFrame) -> schema.Detection:
    debit_idx: Optional[int] = None
    credit_idx: Optional[int] = None
    for i, col in enumerate(map(str, df.columns)):
        norm = col.strip().lower()
        if debit_idx is None and _DEBIT_RE.match(norm):
            debit_idx = i
        if credit_idx is None and _CREDIT_RE.match(norm):
            credit_idx = i
    if debit_idx is None or credit_idx is None:
        raise ValueError("Could not heuristically determine debit/credit columns")
    return schema.Detection(
        debit_column=debit_idx,
        credit_column=credit_idx,
        header_row=0,
        start_row=1,
        end_row=len(df),
        group_keys=[],
    )


def detect_columns(df: pd.DataFrame, api_key: str, model: str = "gpt-4o-mini") -> schema.Detection:
    """Detect debit and credit columns using OpenAI with heuristic fallback."""
    if not api_key:
        return _heuristic_detection(df)

    openai.api_key = api_key
    prompt = prompts.build_prompt(df)
    messages = [
        {"role": "user", "content": prompt},
    ]

    for attempt in range(3):
        try:
            resp = openai.ChatCompletion.create(model=model, messages=messages)
            content = resp.choices[0].message["content"]
            data = json.loads(content)
            return schema.Detection(**data)
        except Exception:
            time.sleep(2 ** attempt)

    # fallback
    return _heuristic_detection(df)
