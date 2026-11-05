import math

import pytest

from guardbench.metrics import (
    bootstrap_ci,
    confusion,
    latency_stats,
    rates,
    roc_auc,
    summarize,
)


def test_confusion_counts():
    c = confusion([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    assert (c.tp, c.fp, c.tn, c.fn) == (2, 1, 1, 1)
    assert c.n == 5


def test_rates_known_values():
    r = rates(confusion([1, 1, 0, 0, 1], [1, 0, 0, 1, 1]))
    assert r["precision"] == pytest.approx(2 / 3)
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["f1"] == pytest.approx(2 / 3)
    assert r["fpr"] == pytest.approx(0.5)
    assert r["fnr"] == pytest.approx(1 / 3)
    assert r["youden"] == pytest.approx(2 / 3 - 0.5)


def test_youden_is_zero_for_flag_everything():
    r = rates(confusion([1, 1, 0, 0], [1, 1, 1, 1]))
    assert r["f1"] == pytest.approx(2 / 3)
    assert r["youden"] == pytest.approx(0.0)


def test_rates_undefined_are_nan_not_zero():
    r = rates(confusion([0, 0, 0], [0, 0, 1]))
    assert math.isnan(r["recall"])
    assert math.isnan(r["f1"])
    assert r["fpr"] == pytest.approx(1 / 3)


def test_f1_zero_when_positives_all_missed():
    r = rates(confusion([1, 1, 0], [0, 0, 0]))
    assert r["f1"] == 0.0


def test_roc_auc_ignores_missing_scores_and_single_class():
    assert roc_auc([0, 1, 1, 0], [0.1, 0.9, 0.8, 0.2]) == pytest.approx(1.0)
    assert roc_auc([0, 1, 1, 0], [0.1, 0.9, None, None]) == pytest.approx(1.0)
    assert math.isnan(roc_auc([0, 0], [0.1, 0.2]))
    assert math.isnan(roc_auc([0, 1], [None, None]))


def test_bootstrap_ci_brackets_point_estimate_and_is_seeded():
    labels = [1] * 50 + [0] * 50
    preds = [1] * 40 + [0] * 10 + [0] * 45 + [1] * 5
    lo, hi = bootstrap_ci(labels, preds, "recall", n_boot=300, seed=7)
    assert lo <= 0.8 <= hi
    assert (lo, hi) == bootstrap_ci(labels, preds, "recall", n_boot=300, seed=7)


def test_bootstrap_ci_perfect_classifier_is_degenerate():
    labels = [1, 1, 0, 0]
    assert bootstrap_ci(labels, labels, "f1", n_boot=50) == (1.0, 1.0)


def test_latency_stats():
    s = latency_stats([10.0, 20.0, 30.0, 40.0])
    assert s["lat_p50_ms"] == pytest.approx(25.0)
    assert s["lat_mean_ms"] == pytest.approx(25.0)
    assert math.isnan(latency_stats([])["lat_p95_ms"])


def test_summarize_has_all_columns():
    row = summarize([1, 0, 1, 0], [1, 0, 0, 0], [0.9, 0.1, 0.4, 0.2], [1, 2, 3, 4], n_boot=20)
    for key in ("tp", "fp", "precision", "recall", "f1", "fpr", "roc_auc", "f1_ci_lo",
                "fpr_ci_hi", "lat_p95_ms"):
        assert key in row
    assert row["roc_auc"] == pytest.approx(1.0)
