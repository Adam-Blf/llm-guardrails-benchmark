"""Write result tables into Markdown files between marker comments.

Numbers in docs/results.md and in the README are never typed by hand: each
table sits between `<!-- table:NAME:start -->` and `<!-- table:NAME:end -->`
and is regenerated from the CSV files of a run by `python -m guardbench tables`.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd

from guardbench.analysis import DETECTION_TASKS
from guardbench.report.figures import TASK_FR

STATUS_FR = {"ok": "exécuté", "skipped": "non exécuté", "failed": "échec au chargement"}


def _f(v: float, digits: int = 2) -> str:
    return "n.d." if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{digits}f}"


def _ms(v: float) -> str:
    if v is None or math.isnan(v):
        return "n.d."
    return f"{v:.1f}" if v < 10 else f"{v:.0f}"


def _md(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def overall_table(run_dir: Path) -> str:
    df = pd.read_csv(run_dir / "overall.csv")
    rows = [[f"`{r.tool}`", _f(r.attack_macro_youden), _f(r.attack_macro_f1),
             _f(r.claimed_macro_youden), _f(r.fr_benign_fpr), _ms(r.lat_p50_ms),
             _ms(r.lat_p95_ms), _f(r.hours_per_1k, 3)] for r in df.itertuples()]
    return _md(["Outil", "J attaques", "F1 attaques", "J familles revendiquées", "FPR bénin FR",
                "p50 (ms)", "p95 (ms)", "h-machine / 1 000"], rows)


def task_table(run_dir: Path, metric: str) -> str:
    df = pd.read_csv(run_dir / "metrics.csv")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    rows = []
    for tool in order:
        g = df[df["tool"] == tool].set_index("task")
        cells = []
        for task in DETECTION_TASKS:
            if task not in g.index:
                cells.append("n.d.")
                continue
            r = g.loc[task]
            lo, hi = _f(r[metric + "_ci_lo"]), _f(r[metric + "_ci_hi"])
            cells.append(f"{_f(r[metric])} [{lo}, {hi}]")
        rows.append([f"`{tool}`", *cells])
    return _md(["Outil", *[TASK_FR[t] for t in DETECTION_TASKS]], rows)


def rates_table(run_dir: Path) -> str:
    """Recall and FPR per task, the two numbers an operator sets a threshold on."""
    df = pd.read_csv(run_dir / "metrics.csv")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    rows = []
    for tool in order:
        g = df[df["tool"] == tool].set_index("task")
        rows.append([f"`{tool}`", *[
            f"{_f(g.loc[t, 'recall'])} / {_f(g.loc[t, 'fpr'])}" if t in g.index else "n.d."
            for t in DETECTION_TASKS]])
    return _md(["Outil (rappel / FPR)", *[TASK_FR[t] for t in DETECTION_TASKS]], rows)


def auc_table(run_dir: Path) -> str:
    df = pd.read_csv(run_dir / "metrics.csv")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    rows = []
    for tool in order:
        g = df[df["tool"] == tool].set_index("task")
        if g["roc_auc"].isna().all():
            continue
        rows.append([f"`{tool}`", *[_f(g.loc[t, "roc_auc"]) if t in g.index else "n.d."
                                     for t in DETECTION_TASKS]])
    return _md(["Outil (ROC-AUC)", *[TASK_FR[t] for t in DETECTION_TASKS]], rows)


def coverage_table(run_dir: Path) -> str:
    df = pd.read_csv(run_dir / "coverage.csv", keep_default_na=False).set_index("tool")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    label = {"C+M": "revendiqué, mesuré", "C": "revendiqué, non atteint", "M": "mesuré seul",
             "": ""}
    rows = [[f"`{t}`", *[label[df.loc[t, task]] for task in DETECTION_TASKS]] for t in order]
    return _md(["Outil", *[TASK_FR[t] for t in DETECTION_TASKS]], rows)


def status_table(run_dir: Path) -> str:
    status = json.loads((run_dir / "tools_status.json").read_text(encoding="utf-8"))
    rows = [[f"`{name}`", STATUS_FR.get(st["status"], st["status"]),
             st.get("reason", "") or f"{st.get('n_total', 0)} entrées, {st.get('errors_new', 0)} "
             f"erreurs, chargement {st.get('load_s', 0):.0f} s"] for name, st in status.items()]
    return _md(["Outil", "Statut", "Détail"], rows)


def french_table(run_dir: Path) -> str:
    df = pd.read_csv(run_dir / "by_source.csv")
    fr = df[df["task"] == "benign_fr"].pivot(index="tool", columns="source", values="flag_rate")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    rows = [[f"`{t}`", _f(fr.loc[t, "alpaca_fr"]), _f(fr.loc[t, "hard_negatives_fr"])]
            for t in order if t in fr.index]
    return _md(["Outil", "FPR instructions French-Alpaca (n = 100)",
                "FPR pièges lexicaux (n = 40)"], rows)


BUILDERS = {
    "overall": overall_table,
    "youden": lambda d: task_table(d, "youden"),
    "f1": lambda d: task_table(d, "f1"),
    "rates": rates_table,
    "auc": auc_table,
    "coverage": coverage_table,
    "status": status_table,
    "french": french_table,
}


def update(md_path: Path, run_dir: Path) -> list[str]:
    """Regenerate every marked table of md_path in place. Returns the names updated."""
    text = md_path.read_text(encoding="utf-8")
    done = []
    for name, build in BUILDERS.items():
        # The block may be empty (start and end on consecutive lines) and the file may use
        # CRLF: requiring a newline on both sides of the content silently matched nothing.
        pattern = re.compile(
            rf"(<!-- table:{name}:start -->)\r?\n.*?(<!-- table:{name}:end -->)", re.S
        )
        if pattern.search(text):
            table = build(run_dir)
            text = pattern.sub(lambda m, t=table: f"{m.group(1)}\n{t}\n{m.group(2)}", text)
            done.append(name)
    md_path.write_text(text, encoding="utf-8")
    return done
