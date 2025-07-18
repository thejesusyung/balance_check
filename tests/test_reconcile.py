import pandas as pd
import pytest

from src.core.reconcile import reconcile
from src.llm.schema import Detection


def _det(df: pd.DataFrame) -> Detection:
    return Detection(
        debit_column=0,
        credit_column=1,
        header_row=0,
        start_row=1,
        end_row=len(df),
        group_keys=[],
    )


@pytest.mark.parametrize(
    "left,right,expect",
    [
        (
            pd.DataFrame({"debit": [100, 0], "credit": [0, 50]}),
            pd.DataFrame({"debit": [100, 0], "credit": [0, 50]}),
            {"matches": 2, "partials": 0, "unmatched": 0},
        ),
        (
            pd.DataFrame({"debit": [100], "credit": [0]}),
            pd.DataFrame({"debit": [60, 40], "credit": [0, 0]}),
            {"matches": 1, "partials": 0, "unmatched": 0},
        ),
        (
            pd.DataFrame({"debit": [50], "credit": [0]}),
            pd.DataFrame({"debit": [70], "credit": [0]}),
            {"matches": 0, "partials": 1, "unmatched": 2},
        ),
        (
            pd.DataFrame({"debit": ["1,5"], "credit": [0]}),
            pd.DataFrame({"debit": [1.5], "credit": [0]}),
            {"matches": 1, "partials": 0, "unmatched": 0},
        ),
    ],
)
def test_reconcile_parametric(left: pd.DataFrame, right: pd.DataFrame, expect: dict):
    matches, partials, unmatched = reconcile(left, right, _det(left), _det(right))

    assert len(matches) == expect["matches"]
    assert len(partials) == expect["partials"]
    assert len(unmatched) == expect["unmatched"]

    if expect["matches"] and len(left) == 1 and len(right) > 1:
        m = matches[0]
        assert m.left_rows == [0]
        assert set(m.right_rows) == set(range(len(right)))

    if expect["partials"]:
        assert partials[0].diff == -20
