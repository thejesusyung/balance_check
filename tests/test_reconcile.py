import pandas as pd
from src.core.reconcile import reconcile, Match, Partial, Unmatched
from src.llm.schema import Detection


def test_reconcile_one_to_one():
    left = pd.DataFrame({"debit": [100, 0], "credit": [0, 50]})
    right = pd.DataFrame({"debit": [100, 0], "credit": [0, 50]})
    det = Detection(
        debit_column=0,
        credit_column=1,
        header_row=0,
        start_row=1,
        end_row=2,
        group_keys=[],
    )

    matches, partials, unmatched = reconcile(left, right, det, det)
    assert len(matches) == 2
    assert not partials
    assert not unmatched


def test_reconcile_many_to_many():
    left = pd.DataFrame({"debit": [60, 40], "credit": [0, 0]})
    right = pd.DataFrame({"debit": [30, 70], "credit": [0, 0]})
    det = Detection(
        debit_column=0,
        credit_column=1,
        header_row=0,
        start_row=1,
        end_row=2,
        group_keys=[],
    )

    matches, partials, unmatched = reconcile(left, right, det, det)
    assert len(matches) == 1
    m = matches[0]
    assert set(m.left_rows) == {0, 1}
    assert set(m.right_rows) == {0, 1}
    assert not partials
    assert not unmatched


def test_reconcile_unmatched():
    left = pd.DataFrame({"debit": [20], "credit": [0]})
    right = pd.DataFrame({"debit": [20, 30], "credit": [0, 0]})
    det = Detection(
        debit_column=0,
        credit_column=1,
        header_row=0,
        start_row=1,
        end_row=2,
        group_keys=[],
    )

    matches, partials, unmatched = reconcile(left, right, det, det)
    assert len(matches) == 1
    assert len(partials) == 1
    assert len(unmatched) == 1
    assert unmatched[0].side == "right"
