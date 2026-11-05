"""Matplotlib charts of a run (object-oriented API, 200 dpi PNG, colour-blind safe)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_curve  # noqa: E402

from guardbench.analysis import DETECTION_TASKS, load_predictions  # noqa: E402

NAVY, ROSE, BLUE, GREY = "#163767", "#FF43B8", "#0C78B4", "#9AA5B1"
TASK_FR = {
    "direct_injection": "Injection directe",
    "jailbreak": "Jailbreak",
    "indirect_injection": "Injection indirecte",
    "agent_tool_abuse": "Abus d'outils",
    "toxicity": "Toxicité",
    "pii": "PII",
    "benign_fr": "Bénin FR",
}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 10})


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def heatmap(metrics: pd.DataFrame, order: list[str], out: Path, metric: str) -> Path:
    """F1 (0..1, cividis) or Youden J (-1..1, diverging) per tool and task."""
    youden = metric == "youden"
    pivot = metrics.pivot(index="tool", columns="task", values=metric).reindex(
        index=order, columns=DETECTION_TASKS)
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(order) + 1.2), constrained_layout=True)
    data = np.ma.masked_invalid(pivot.to_numpy(dtype=float))
    cmap = matplotlib.colormaps["RdBu" if youden else "cividis"].with_extremes(bad="#EEF1F5")
    lo = -1 if youden else 0
    im = ax.imshow(data, cmap=cmap, vmin=lo, vmax=1, aspect="auto")
    for (i, j), v in np.ndenumerate(pivot.to_numpy(dtype=float)):
        if not np.isnan(v):
            dark = abs(v) > 0.6 if youden else v < 0.55
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if dark else "#111")
    ax.set_xticks(range(len(DETECTION_TASKS)), [TASK_FR[t] for t in DETECTION_TASKS],
                  rotation=25, ha="right")
    ax.set_yticks(range(len(order)), order)
    label = "J de Youden (rappel moins FPR)" if youden else "F1"
    fig.colorbar(im, ax=ax, shrink=0.8, label=label)
    ax.set_title(("J de Youden" if youden else "F1") + " par outil et par famille de risque")
    return _save(fig, out, f"{metric}_heatmap")


def f1_with_ci(metrics: pd.DataFrame, order: list[str], out: Path) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(9, 5.6), sharey=True, constrained_layout=True)
    for ax, task in zip(axes.flat, DETECTION_TASKS, strict=True):
        g = metrics[metrics["task"] == task].set_index("tool").reindex(order)
        y = np.arange(len(order))
        err = np.vstack([(g["f1"] - g["f1_ci_lo"]).clip(lower=0),
                         (g["f1_ci_hi"] - g["f1"]).clip(lower=0)]).astype(float)
        ax.barh(y, g["f1"].fillna(0), color=NAVY, height=0.6)
        ax.errorbar(g["f1"].fillna(0), y, xerr=np.nan_to_num(err), fmt="none", ecolor=ROSE,
                    capsize=2, lw=1)
        ax.set_xlim(0, 1)
        ax.set_title(TASK_FR[task])
        ax.set_yticks(y, order)
        ax.invert_yaxis()
    fig.supxlabel("F1 (barre) et IC 95 % bootstrap (trait)")
    return _save(fig, out, "f1_ci")


def recall_vs_fpr(metrics: pd.DataFrame, order: list[str], out: Path) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(9, 5.6), sharex=True, sharey=True,
                             constrained_layout=True)
    markers = "osD^v<>phX*P"
    for ax, task in zip(axes.flat, DETECTION_TASKS, strict=True):
        g = metrics[metrics["task"] == task].set_index("tool")
        for k, tool in enumerate(order):
            if tool in g.index:
                ax.scatter(g.loc[tool, "fpr"], g.loc[tool, "recall"], marker=markers[k % 12],
                           s=36, color=plt.cm.tab10(k % 10), label=tool)
        ax.plot([0, 1], [0, 1], ls=":", color=GREY, lw=0.8)
        ax.set_title(TASK_FR[task])
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.03, 1.03)
    for ax in axes[1]:
        ax.set_xlabel("Taux de faux positifs (FPR)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Rappel")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=7, frameon=False)
    return _save(fig, out, "recall_fpr")


def latency(df: pd.DataFrame, order: list[str], out: Path) -> Path:
    ok = df[~df["is_error"]]
    stats = ok.groupby("tool")["latency_ms"].quantile([0.5, 0.95]).unstack().reindex(order)
    fig, ax = plt.subplots(figsize=(7.2, 0.36 * len(order) + 1.0), constrained_layout=True)
    y = np.arange(len(order))
    ax.barh(y, stats[0.5], color=BLUE, height=0.55, label="p50")
    ax.scatter(stats[0.95], y, color=ROSE, marker="|", s=160, label="p95", zorder=3)
    ax.set_xscale("log")
    ax.set_yticks(y, order)
    ax.invert_yaxis()
    ax.set_xlabel("Latence par requête (ms, échelle log)")
    ax.axvline(100, color=GREY, ls="--", lw=0.8)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Latence d'inférence")
    return _save(fig, out, "latency")


def french_fpr(df: pd.DataFrame, order: list[str], out: Path) -> Path:
    fr = df[(df["task"] == "benign_fr") & ~df["is_error"]]
    rates = fr.groupby(["tool", "source"])["flagged"].mean().unstack().reindex(order)
    fig, ax = plt.subplots(figsize=(7.2, 0.36 * len(order) + 1.0), constrained_layout=True)
    y = np.arange(len(order))
    h = 0.38
    ax.barh(y - h / 2, rates.get("alpaca_fr", 0), height=h, color=NAVY,
            label="Instructions ordinaires (Alpaca FR)")
    ax.barh(y + h / 2, rates.get("hard_negatives_fr", 0), height=h, color=ROSE,
            hatch="//", label="Pièges lexicaux écrits à la main")
    ax.set_yticks(y, order)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Taux de faux positifs sur des requêtes françaises bénignes")
    ax.legend(frameon=False, loc="lower right", fontsize=7)
    ax.set_title("Sur-blocage en français")
    return _save(fig, out, "french_fpr")


def roc(df: pd.DataFrame, order: list[str], out: Path) -> Path:
    tasks = ["direct_injection", "jailbreak", "indirect_injection", "agent_tool_abuse"]
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.9), sharey=True, constrained_layout=True)
    for ax, task in zip(axes, tasks, strict=True):
        for k, tool in enumerate(order):
            g = df[(df["tool"] == tool) & (df["task"] == task) & ~df["is_error"]]
            g = g.dropna(subset=["score"])
            if g["label"].nunique() < 2:
                continue
            fpr, tpr, _ = roc_curve(g["label"], g["score"])
            ax.plot(fpr, tpr, lw=1.2, color=plt.cm.tab10(k % 10), label=tool)
        ax.plot([0, 1], [0, 1], ls=":", color=GREY, lw=0.8)
        ax.set_title(TASK_FR[task])
        ax.set_xlabel("FPR")
    axes[0].set_ylabel("Rappel")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=7, frameon=False)
    return _save(fig, out, "roc")


def draw_all(run_dir: Path, out: Path) -> list[Path]:
    metrics = pd.read_csv(run_dir / "metrics.csv")
    order = pd.read_csv(run_dir / "overall.csv")["tool"].tolist()
    df = load_predictions(run_dir)
    return [
        heatmap(metrics, order, out, "youden"),
        heatmap(metrics, order, out, "f1"),
        f1_with_ci(metrics, order, out),
        recall_vs_fpr(metrics, order, out),
        latency(df, order, out),
        french_fpr(df, order, out),
        roc(df, order, out),
    ]
