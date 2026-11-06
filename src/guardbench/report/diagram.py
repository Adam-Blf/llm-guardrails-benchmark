"""Static version of the guardrail placement diagram for the PDF.

GitHub renders the Mermaid source in docs/risk-taxonomy.md; FPDF2 cannot, so
the same graph is drawn here with matplotlib and referenced from the Markdown
through a `pdf-figure` comment.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROLE = {
    "input": ("#2563eb", "white"),
    "process": ("#163767", "white"),
    "store": ("#f59e0b", "#111111"),
    "guard": ("#0f766e", "white"),
    "ok": ("#16a34a", "white"),
    "error": ("#dc2626", "white"),
}
NODES = {
    "user": (0.6, 3.0, "Utilisateur", "input"),
    "docs": (0.6, 1.2, "Documents, web,\ncourriels", "input"),
    "rag": (2.6, 1.2, "Récupération\nRAG", "process"),
    "g1": (2.6, 3.0, "Guardrail\nd'entrée", "guard"),
    "refus": (2.6, 4.4, "Refus", "error"),
    "llm": (4.6, 3.0, "LLM", "process"),
    "agent": (6.6, 3.0, "Agent\nchoix d'outil", "process"),
    "tools": (8.6, 3.0, "Outils\net API", "store"),
    "g2": (7.6, 1.2, "Guardrail sur\nsortie d'outil", "guard"),
    "g3": (4.6, 4.6, "Guardrail\nde sortie", "guard"),
    "out": (6.6, 4.6, "Réponse", "ok"),
}
EDGES = [
    ("user", "g1", ""), ("docs", "rag", ""), ("rag", "g1", ""), ("g1", "llm", "autorisé"),
    ("g1", "refus", "bloqué"), ("llm", "agent", ""), ("agent", "tools", ""),
    ("tools", "g2", "réponse"), ("g2", "llm", ""), ("llm", "g3", ""), ("g3", "out", ""),
]
W, H = 1.5, 0.75


def draw(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(-0.3, 9.5)
    ax.set_ylim(0.5, 5.3)
    ax.axis("off")
    for x, y, label, role in NODES.values():
        fill, ink = ROLE[role]
        ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H,
                                    boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=fill, ec="#0b1b33", lw=0.8))
        ax.text(x, y, label, ha="center", va="center", color=ink, fontsize=8.5,
                fontweight="bold")
    for a, b, label in EDGES:
        (xa, ya, *_), (xb, yb, *_) = NODES[a], NODES[b]
        arrow = FancyArrowPatch((xa, ya), (xb, yb), arrowstyle="-|>", mutation_scale=11,
                                color="#4b5563", lw=1.0, shrinkA=28, shrinkB=28)
        ax.add_patch(arrow)
        if label:
            ax.text((xa + xb) / 2 + 0.15, (ya + yb) / 2 + 0.16, label, fontsize=7.5,
                    color="#374151", ha="center")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out
