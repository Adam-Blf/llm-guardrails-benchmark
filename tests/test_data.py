"""Dataset assembly tests. No download: loaders are exercised on local frames."""

import pandas as pd

from guardbench.data import LOADERS, build_suite, sources
from guardbench.data.agentic import _insert
from guardbench.data.benign_fr import HARD_NEGATIVES_FR
from guardbench.data.sampling import clip, stratified
from guardbench.types import Sample, Task


def test_sampling_helpers():
    df = pd.DataFrame({"text": list("abcdefgh"), "label": [0, 1] * 4})
    s = stratified(df, "label", 2, seed=3)
    assert s["label"].value_counts().to_dict() == {0: 2, 1: 2}
    assert s.equals(stratified(df, "label", 2, seed=3))
    assert len(clip("x" * 5000)) == 2000


def test_insert_positions():
    ctx = "l1\nl2\nl3\nl4"
    assert _insert(ctx, "ATK", "start").startswith("ATK")
    assert _insert(ctx, "ATK", "end").endswith("ATK")
    assert _insert(ctx, "ATK", "middle").split("\n")[2] == "ATK"


def test_every_task_has_a_loader():
    assert set(LOADERS) == set(Task)


def test_build_suite_rejects_duplicate_uids(monkeypatch):
    dup = [Sample("same", "a", 0, Task.PII, "x"), Sample("same", "b", 1, Task.PII, "x")]
    monkeypatch.setitem(LOADERS, Task.PII, lambda n, seed: dup)
    try:
        build_suite(1, 0, [Task.PII])
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate uids accepted")


def test_sources_are_pinned():
    for row in sources.manifest():
        assert len(row["revision"]) == 40, row


def test_hard_negatives_are_unique_french_prompts():
    assert len(HARD_NEGATIVES_FR) == len(set(HARD_NEGATIVES_FR)) == 40
