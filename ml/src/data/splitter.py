"""Timestamp-based per-user train/val/test split."""

from __future__ import annotations

import pandas as pd


def split_by_timestamp(
    ratings: pd.DataFrame,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ratings = ratings.sort_values(["userId", "timestamp"])
    train_parts, val_parts, test_parts = [], [], []

    for _, group in ratings.groupby("userId"):
        n = len(group)
        if n < 3:
            train_parts.append(group)
            continue
        train_end = max(1, int(n * train_ratio))
        val_end = max(train_end + 1, int(n * (train_ratio + val_ratio)))
        train_parts.append(group.iloc[:train_end])
        val_parts.append(group.iloc[train_end:val_end])
        test_parts.append(group.iloc[val_end:])

    train = pd.concat(train_parts, ignore_index=True) if train_parts else ratings.iloc[:0]
    val = pd.concat(val_parts, ignore_index=True) if val_parts else ratings.iloc[:0]
    test = pd.concat(test_parts, ignore_index=True) if test_parts else ratings.iloc[:0]
    return train, val, test


def label_implicit(rating: float) -> int | None:
    if rating >= 4.0:
        return 1
    if rating < 2.5:
        return 0
    return None
