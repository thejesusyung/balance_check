import pandas as pd
from src.core.reconcile import reconcile
from src.core.highlight import cells_to_highlight
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


def test_cells_to_highlight_none():
    left = pd.DataFrame({"debit": [100], "credit": [0]})
    right = pd.DataFrame({"debit": [100], "credit": [0]})
    det = _det(left)
    matches, partials, unmatched = reconcile(left, right, det, det)
    assert cells_to_highlight(matches, partials, unmatched, det, "left") == set()
    assert cells_to_highlight(matches, partials, unmatched, det, "right") == set()


def test_cells_to_highlight_partial_unmatched():
    left = pd.DataFrame({"debit": [50], "credit": [0]})
    right = pd.DataFrame({"debit": [40], "credit": [0]})
    det = _det(left)
    matches, partials, unmatched = reconcile(left, right, det, det)
    expected = {(0, 0), (0, 1)}
    assert cells_to_highlight(matches, partials, unmatched, det, "left") == expected
    assert cells_to_highlight(matches, partials, unmatched, det, "right") == expected


def test_cells_to_highlight_extra_right_row():
    left = pd.DataFrame({"debit": [20], "credit": [0]})
    right = pd.DataFrame({"debit": [20, 30], "credit": [0, 0]})
    det = _det(left)
    matches, partials, unmatched = reconcile(left, right, det, det)
    assert cells_to_highlight(matches, partials, unmatched, det, "left") == set()
    assert cells_to_highlight(matches, partials, unmatched, det, "right") == {(1, 0), (1, 1)}
