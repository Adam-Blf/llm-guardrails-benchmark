"""Detection metrics with bootstrap confidence intervals.

Positive class = "should be blocked" (label 1). All functions are pure and
deterministic for a given seed so that results are reproducible.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import roc_auc_score

NAN = float("nan")


@dataclass
class Confusion:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.tn + self.fn


def _div(num: float, den: float) -> float:
    return num / den if den else NAN


def confusion(labels: Sequence[int], preds: Sequence[int]) -> Confusion:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(preds, dtype=int)
    return Confusion(
        tp=int(((y == 1) & (p == 1)).sum()),
        fp=int(((y == 0) & (p == 1)).sum()),
        tn=int(((y == 0) & (p == 0)).sum()),
        fn=int(((y == 1) & (p == 0)).sum()),
    )


def rates(c: Confusion) -> dict[str, float]:
    """Precision, recall, F1, FPR, FNR, accuracy. NaN when undefined."""
    precision = _div(c.tp, c.tp + c.fp)
    recall = _div(c.tp, c.tp + c.fn)
    if math.isnan(precision) or math.isnan(recall) or precision + recall == 0:
        f1 = 0.0 if c.tp + c.fn > 0 else NAN
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": _div(c.fp, c.fp + c.tn),
        "fnr": _div(c.fn, c.fn + c.tp),
        "accuracy": _div(c.tp + c.tn, c.n),
    }


def roc_auc(labels: Sequence[int], scores: Sequence[float | None]) -> float:
    """ROC-AUC on rows that carry a score; NaN if one class is missing."""
    pairs = [(y, s) for y, s in zip(labels, scores, strict=True) if s is not None]
    if not pairs:
        return NAN
    y = [p[0] for p in pairs]
    if len(set(y)) < 2:
        return NAN
    return float(roc_auc_score(y, [p[1] for p in pairs]))


def bootstrap_ci(
    labels: Sequence[int],
    preds: Sequence[int],
    metric: str,
    n_boot: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile bootstrap CI of one rate metric, resampling rows with replacement.

    Resampling is stratified by label so each replicate keeps the class balance
    of the evaluation slice (otherwise recall/FPR become undefined on tiny slices).
    """
    y = np.asarray(labels, dtype=int)
    p = np.asarray(preds, dtype=int)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    values = []
    for _ in range(n_boot):
        idx = np.concatenate(
            [
                rng.choice(pos, size=pos.size, replace=True) if pos.size else pos,
                rng.choice(neg, size=neg.size, replace=True) if neg.size else neg,
            ]
        )
        v = rates(confusion(y[idx], p[idx]))[metric]
        if not math.isnan(v):
            values.append(v)
    if not values:
        return (NAN, NAN)
    lo, hi = np.percentile(values, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(lo), float(hi))


def latency_stats(latencies_ms: Sequence[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"lat_p50_ms": NAN, "lat_p95_ms": NAN, "lat_mean_ms": NAN}
    arr = np.asarray(latencies_ms, dtype=float)
    return {
        "lat_p50_ms": float(np.percentile(arr, 50)),
        "lat_p95_ms": float(np.percentile(arr, 95)),
        "lat_mean_ms": float(arr.mean()),
    }


def summarize(
    labels: Sequence[int],
    preds: Sequence[int],
    scores: Sequence[float | None],
    latencies_ms: Sequence[float],
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, float]:
    """Full metric row for one (tool, task) slice."""
    c = confusion(labels, preds)
    row: dict[str, float] = {**asdict(c), "n": c.n, **rates(c)}
    row["roc_auc"] = roc_auc(labels, scores)
    for metric in ("f1", "recall", "fpr"):
        lo, hi = bootstrap_ci(labels, preds, metric, n_boot=n_boot, seed=seed)
        row[f"{metric}_ci_lo"], row[f"{metric}_ci_hi"] = lo, hi
    row.update(latency_stats(latencies_ms))
    return row
