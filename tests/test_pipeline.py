"""Runner, resume logic, analysis tables and CLI on a tiny in-memory suite."""

import json

import pandas as pd
import pytest

import guardbench.runner as runner
from guardbench.adapters.base import Decision, Guardrail
from guardbench.analysis import analyse, cost_per_1k
from guardbench.cli import build_parser
from guardbench.types import Sample, Task


class KeywordTool(Guardrail):
    name = "kw"
    claimed = frozenset({Task.DIRECT_INJECTION})

    def __init__(self):
        self.calls = 0

    def _decide(self, text):
        self.calls += 1
        hit = "attack" in text
        return Decision(hit, 0.9 if hit else 0.1)


def _suite():
    out = []
    for i in range(6):
        out.append(Sample(f"d:{i}", f"attack {i}" if i % 2 else f"hello {i}", i % 2,
                          Task.DIRECT_INJECTION, "unit"))
    out.append(Sample("fr:0", "bonjour", 0, Task.BENIGN_FR, "unit", "fr"))
    out.append(Sample("fr:1", "attack en français", 0, Task.BENIGN_FR, "unit", "fr"))
    return out


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    tool = KeywordTool()
    monkeypatch.setattr(runner, "build_suite", lambda n, seed: _suite())
    monkeypatch.setattr(runner, "make", lambda name: tool)
    runner.run(["kw"], tmp_path, n_per_class=3, seed=1, threads=1)
    return tmp_path, tool


def test_run_writes_predictions_status_and_meta(run_dir):
    path, _ = run_dir
    preds = pd.read_csv(path / "predictions" / "kw.csv")
    assert len(preds) == 8
    status = json.loads((path / "tools_status.json").read_text())
    assert status["kw"]["status"] == "ok"
    meta = json.loads((path / "run_meta.json").read_text())
    assert meta["seed"] == 1 and meta["data"]


def test_rerun_resumes_without_duplicates(run_dir, monkeypatch):
    path, tool = run_dir
    before = tool.calls
    runner.run(["kw"], path, n_per_class=3, seed=1, threads=1)
    assert tool.calls - before == 3  # warm-up only, every row already present
    assert len(pd.read_csv(path / "predictions" / "kw.csv")) == 8


def test_analysis_tables(run_dir):
    path, _ = run_dir
    tables = analyse(path, n_boot=20)
    m = tables["metrics"].set_index("task")
    assert m.loc["direct_injection", "f1"] == pytest.approx(1.0)
    assert m.loc["benign_fr", "fpr"] == pytest.approx(0.5)
    assert tables["coverage"].set_index("tool").loc["kw", "direct_injection"] == "C+M"
    assert (path / "overall.csv").exists()


def test_skipped_tool_is_recorded(tmp_path, monkeypatch):
    class Off(KeywordTool):
        def available(self):
            return False, "no key"

    monkeypatch.setattr(runner, "build_suite", lambda n, seed: _suite())
    monkeypatch.setattr(runner, "make", lambda name: Off())
    status = runner.run(["off"], tmp_path, threads=1)
    assert status["off"] == {"status": "skipped", "reason": "no key"}


def test_cost_per_1k():
    assert cost_per_1k(3600.0, 1.0) == pytest.approx(1.0)


def test_cli_parser():
    args = build_parser().parse_args(["--run", "x", "run", "--tools", "a", "b"])
    assert args.run == "x" and args.tools == ["a", "b"] and args.n_per_class == 100


def test_figures_are_drawn(run_dir, tmp_path):
    from guardbench.report.figures import draw_all

    path, _ = run_dir
    analyse(path, n_boot=10)
    files = draw_all(path, tmp_path / "fig")
    assert len(files) == 7 and all(f.stat().st_size > 1000 for f in files)
