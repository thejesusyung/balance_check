import pandas as pd
from src.llm.detector import detect_columns


def test_detect_columns_heuristic():
    df = pd.DataFrame({
        'Дебет': [1, 2],
        'Кредит': [1, 2],
        'Описание': ['a', 'b'],
    })
    detection = detect_columns(df, api_key="")
    assert detection.debit_column == 0
    assert detection.credit_column == 1
    assert detection.start_row == 1
    assert detection.end_row == len(df)
