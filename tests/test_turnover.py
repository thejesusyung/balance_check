import pandas as pd

from src.io.loader import detect_turnover_value


def test_detect_turnover_english():
    df = pd.DataFrame([["Turnover for period", 123.45]])
    assert detect_turnover_value(df) == 123.45


def test_detect_turnover_russian():
    df = pd.DataFrame([["Оборот за период", "1 000"]])
    assert detect_turnover_value(df) == 1000.0
