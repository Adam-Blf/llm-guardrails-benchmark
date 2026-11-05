"""Seeded, stratified sampling helpers shared by every loader."""

from __future__ import annotations

import pandas as pd


def take(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Deterministic sample of at most n rows (all rows when n >= len)."""
    if n >= len(df):
        return df.sample(frac=1.0, random_state=seed)
    return df.sample(n=n, random_state=seed)


def stratified(df: pd.DataFrame, label_col: str, n_per_class: int, seed: int) -> pd.DataFrame:
    """Up to n_per_class rows of each label value, shuffled with a fixed seed."""
    parts = [take(group, n_per_class, seed) for _, group in df.groupby(label_col, sort=True)]
    return pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def clip(text: str, max_chars: int = 2000) -> str:
    """Bound input length so CPU latency stays comparable across tools."""
    text = str(text).strip()
    return text if len(text) <= max_chars else text[:max_chars]
