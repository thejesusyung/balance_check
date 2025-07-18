"""Reconciliation algorithm matching debit\u2194credit amounts between tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable, Optional

import logging
import pandas as pd

from src.llm.schema import Detection

logger = logging.getLogger(__name__)


@dataclass
class Match:
    """Fully matched row groups."""

    left_rows: List[int]
    right_rows: List[int]
    amount_left: float
    amount_right: float
    diff: float


@dataclass
class Partial:
    """Rows with the same key that do not net to zero."""

    left_rows: List[int]
    right_rows: List[int]
    amount_left: float
    amount_right: float
    diff: float


@dataclass
class Unmatched:
    """Individual rows left without a counterpart."""

    side: str
    row: int
    amount: float


def _to_numeric(series: pd.Series) -> pd.Series:
    """Parse a column of potential numeric strings robustly."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        alt = pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")
        numeric = numeric.fillna(alt)
    return numeric.fillna(0)


def _amounts(df: pd.DataFrame, det: Detection) -> pd.Series:
    debit = _to_numeric(df.iloc[:, det.debit_column])
    credit = _to_numeric(df.iloc[:, det.credit_column])
    return debit - credit


def _group_indices(df: pd.DataFrame, det: Detection) -> Dict[Tuple, List[int]]:
    if det.group_keys:
        groups = df.groupby(det.group_keys).groups
        return {k if isinstance(k, tuple) else (k,): list(v) for k, v in groups.items()}
    return {(): list(df.index)}


def _subset_dp(rows: List[Tuple[int, float]], limit: int = 50) -> Dict[float, List[int]]:
    dp: Dict[float, List[int]] = {0.0: []}
    for idx, amt in rows[:limit]:
        new: Dict[float, List[int]] = dict(dp)
        for s, subset in dp.items():
            key = round(s + amt, 2)
            if key not in new:
                new[key] = subset + [idx]
        dp = new
    return dp


def _match_subsets(left: List[Tuple[int, float]], right: List[Tuple[int, float]]) -> Optional[Tuple[List[int], List[int], float]]:
    left_dp = _subset_dp(left)
    right_dp = _subset_dp(right)
    for total in left_dp:
        if total != 0 and total in right_dp:
            return left_dp[total], right_dp[total], total
    return None


def reconcile(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    detection_left: Detection,
    detection_right: Detection,
) -> Tuple[List[Match], List[Partial], List[Unmatched]]:
    """Return matched, partially matched and unmatched rows.

    Parameters
    ----------
    df_left, df_right: DataFrames to compare
    detection_left, detection_right: column detection results

    Returns
    -------
    tuple of (matches, partials, unmatched)
    """

    logger.info(
        "Starting reconciliation: left rows=%d, right rows=%d",
        len(df_left),
        len(df_right),
    )
    logger.debug("Left detection: %s", detection_left.model_dump())
    logger.debug("Right detection: %s", detection_right.model_dump())

    amount_left = _amounts(df_left, detection_left)
    amount_right = _amounts(df_right, detection_right)
    logger.debug(
        "Computed amounts - left head: %s", amount_left.head().to_dict()
    )
    logger.debug(
        "Computed amounts - right head: %s", amount_right.head().to_dict()
    )

    groups_left = _group_indices(df_left, detection_left)
    groups_right = _group_indices(df_right, detection_right)
    logger.debug(
        "Left groups: %s", {k: len(v) for k, v in groups_left.items()}
    )
    logger.debug(
        "Right groups: %s", {k: len(v) for k, v in groups_right.items()}
    )

    all_keys = set(groups_left) | set(groups_right)

    matches: List[Match] = []
    partials: List[Partial] = []
    unmatched: List[Unmatched] = []

    for key in all_keys:
        logger.debug("Processing group %s", key)
        left_idxs = groups_left.get(key, [])
        right_idxs = groups_right.get(key, [])

        left_rows = [(i, amount_left[i]) for i in left_idxs]
        right_rows = [(i, amount_right[i]) for i in right_idxs]

        # 1-to-1 greedy matching
        right_map: Dict[float, List[int]] = {}
        for idx, amt in right_rows:
            right_map.setdefault(round(amt, 2), []).append(idx)

        remaining_left: List[Tuple[int, float]] = []
        remaining_right: List[Tuple[int, float]] = []

        for l_idx, l_amt in left_rows:
            bucket = right_map.get(round(l_amt, 2))
            if bucket:
                r_idx = bucket.pop(0)
                logger.debug(
                    "1-to-1 match: left %d -> right %d amount %.2f",
                    l_idx,
                    r_idx,
                    l_amt,
                )
                matches.append(
                    Match([l_idx], [r_idx], l_amt, amount_right[r_idx], 0.0)
                )
            else:
                remaining_left.append((l_idx, l_amt))

        for amt_key, idxs in right_map.items():
            remaining_right.extend([(r, amount_right[r]) for r in idxs])

        # m-to-n subset search
        while remaining_left and remaining_right:
            res = _match_subsets(remaining_left, remaining_right)
            if not res:
                break
            l_set, r_set, total = res
            logger.debug(
                "Subset match: left %s -> right %s total %.2f",
                l_set,
                r_set,
                total,
            )
            matches.append(
                Match(l_set, r_set, total, total, 0.0)
            )
            remaining_left = [lr for lr in remaining_left if lr[0] not in l_set]
            remaining_right = [rr for rr in remaining_right if rr[0] not in r_set]

        if remaining_left or remaining_right:
            partial = Partial(
                [i for i, _ in remaining_left],
                [i for i, _ in remaining_right],
                sum(amt for _, amt in remaining_left),
                sum(amt for _, amt in remaining_right),
                sum(amt for _, amt in remaining_left)
                - sum(amt for _, amt in remaining_right),
            )
            logger.debug(
                "Partial group %s: left %s (%.2f) right %s (%.2f) diff %.2f",
                key,
                partial.left_rows,
                partial.amount_left,
                partial.right_rows,
                partial.amount_right,
                partial.diff,
            )
            partials.append(partial)

        for idx, amt in remaining_left:
            logger.debug("Unmatched left row %d amount %.2f", idx, amt)
            unmatched.append(Unmatched("left", idx, amt))
        for idx, amt in remaining_right:
            logger.debug("Unmatched right row %d amount %.2f", idx, amt)
            unmatched.append(Unmatched("right", idx, amt))

    logger.info(
        "Reconciliation finished: %d matches, %d partials, %d unmatched rows",
        len(matches),
        len(partials),
        len(unmatched),
    )
    return matches, partials, unmatched

