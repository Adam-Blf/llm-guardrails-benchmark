"""Assemble the final PDF report from docs/*.md and the committed figures."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

import pandas as pd
from fpdf.enums import XPos, YPos

from guardbench.report.diagram import draw as draw_diagram
from guardbench.report.engine import ASSETS, DARK, GREY, MARGIN, NAVY, ROSE, WHITE, Report
from guardbench.report.markdown import inline, render

ROOT = Path(__file__).resolve().parents[3]
TITLE = "Benchmarking de guardrails pour la sécurité des LLM et des agents LLM"
OUTPUT_NAME = "rapport-guardrails-llm.pdf"
RUN = "results/cpu-baseline"


def project_version() -> str:
    """Read pyproject.toml, never the installed metadata: an editable install keeps the
    version it had when it was installed, and the cover once printed 0.1.0 for 0.6.0."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def cover_synthesis() -> list[list[str]]:
    """One line per tool, best attack Youden J first, from the committed run."""
    df = pd.read_csv(ROOT / RUN / "overall.csv").sort_values("attack_macro_youden", ascending=False)
    rows = [["Outil", "J attaques", "Faux positifs FR", "Latence p50"]]
    for r in df.itertuples():
        ms = r.lat_p50_ms
        p50 = f"{ms / 1000:.1f} s" if ms >= 1000 else f"{ms:.0f} ms" if ms >= 10 else f"{ms:.1f} ms"
        rows.append([r.tool, f"{r.attack_macro_youden:.2f}", f"{r.fr_benign_fpr:.0%}", p50])
    return rows

# Order of the body. (file, skip its own # title, captions of its tables)
SECTIONS = [
    ("docs/report/introduction.md", False, {}),
    ("docs/risk-taxonomy.md", False, {
        1: "Risques recensés hors du périmètre d'un guardrail d'entrée.",
        2: "Correspondance entre familles de risque, référentiels et tranches du benchmark.",
    }),
    ("docs/methodology.md", False, {
        1: "Outils retenus, nature et familles de risque revendiquées par l'éditeur.",
        2: "Tranches de données, sources épinglées et effectifs par classe.",
    }),
    ("docs/results.md", False, {}),
    ("docs/report/conclusion.md", False, {}),
]


def _cover(pdf: Report) -> None:
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 92, "F")
    pdf.set_fill_color(*ROSE)
    pdf.rect(0, 92, pdf.w, 2.2, "F")
    logo = ASSETS / "efrei-logo-blanc.png"
    if logo.exists():
        pdf.image(str(logo), x=MARGIN, y=14, h=13)
    pdf.set_xy(MARGIN, 40)
    pdf.set_text_color(*WHITE)
    pdf.set_font(pdf.display, "", 21)
    pdf.multi_cell(pdf.w - 2 * MARGIN, 9.5, TITLE, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Body", "", 10)
    pdf.multi_cell(0, 5, "Cartographie des risques, méthode d'évaluation et résultats comparatifs",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_y(101)
    pdf.set_text_color(*DARK)
    pdf.set_font("Body", "B", 10)
    pdf.cell(0, 5.5, "Adam Beloucif et Emilien Morice", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Body", "", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 4.6, (
        "Mastère Data Engineering et IA, EFREI Paris. Cours MLOps (XDE826).\n"
        f"Version {project_version()} du dépôt Adam-Blf/llm-guardrails-benchmark, "
        f"{date.today().strftime('%d/%m/%Y')}."), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    resume = (ROOT / "docs/report/resume.md").read_text(encoding="utf-8").split("\n", 1)[1]
    pdf.set_font("Body", "B", 10.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Résumé", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for block in [b for b in resume.split("\n\n") if b.strip()]:
        pdf.para(inline(" ".join(block.split())), size=9.2)
    pdf.ln(3)
    pdf.set_font("Body", "B", 10.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "Synthèse des outils mesurés", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    width = pdf.w - 2 * MARGIN
    pdf.data_table(cover_synthesis(), [width * 0.34, width * 0.2, width * 0.24, width * 0.22],
                   "J de Youden moyen sur les attaques (1 = parfait, 0 = hasard), faux positifs "
                   "sur les consignes françaises ordinaires, latence médiane sur CPU.",
                   size=8.4, align="LRRR")


def _toc(pdf: Report, outline) -> None:
    pdf.set_font(pdf.display, "", 15)
    pdf.set_text_color(*NAVY)
    pdf.set_x(MARGIN)
    pdf.cell(0, 9, "Sommaire", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    for entry in outline:
        level = entry.level
        pdf.set_font("Body", "B" if level == 0 else "", 9.6 if level == 0 else 8.6)
        pdf.set_text_color(*(NAVY if level == 0 else DARK))
        pdf.set_x(MARGIN + 6 * level)
        width = pdf.w - 2 * MARGIN - 6 * level - 12
        h = 5.2 if level == 0 else 4.6
        pdf.cell(width, h, entry.name, link=pdf.add_link(page=entry.page_number))
        pdf.cell(12, h, str(entry.page_number), align="R",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    # The table of contents alone left most of its page empty: the key findings fill it.
    points = (ROOT / "docs/report/a-retenir.md").read_text(encoding="utf-8").splitlines()
    pdf.ln(6)
    pdf.set_font(pdf.display, "", 13)
    pdf.set_text_color(*NAVY)
    pdf.set_x(MARGIN)
    pdf.cell(0, 8, points[0].lstrip("# "), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.bullets([inline(p[2:]) for p in points if p.startswith("- ")], size=9.2)


def build_pdf(out_dir: Path) -> Path:
    draw_diagram(ROOT / "reports/figures/guardrail-placement.png")
    pdf = Report(TITLE, "Benchmark de guardrails LLM, Beloucif et Morice, EFREI XDE826")
    _cover(pdf)
    pdf.add_page()
    pdf.insert_toc_placeholder(_toc, pages=1)
    for rel, skip, captions in SECTIONS:
        render(pdf, ROOT / rel, ROOT, skip_title=skip, table_captions=captions)
    pdf.finish()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / OUTPUT_NAME
    pdf.output(str(path))
    return path
