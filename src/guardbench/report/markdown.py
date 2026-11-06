"""Render the project Markdown documents into the FPDF2 report.

The PDF is built from the same files as the repository documentation, so the
report and docs/ can never disagree. Supported subset: headings (#, ##, ###),
paragraphs, dash lists, pipe tables, images, `pdf-figure` comments and fenced
blocks (skipped, Mermaid diagrams have a static twin referenced by a comment).
"""

from __future__ import annotations

import re
from pathlib import Path

from guardbench.report.engine import MARGIN, Report

_LINK = re.compile(r"\[([^\]]+)\]\((?!http)[^)]+\)")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_CODE = re.compile(r"`([^`]+)`")
# GitHub hides HTML comments: this one carries a PDF-only figure (static Mermaid twin).
_PDF_FIGURE = re.compile(r"<!--\s*pdf-figure:\s*(\S+)\s*\|\s*(.+?)\s*-->")


def inline(text: str) -> str:
    """Markdown inline syntax to the subset FPDF2 understands (bold only)."""
    text = _LINK.sub(r"\1", text)
    text = _CODE.sub(r"\1", text)
    return text.replace("--", "- -").replace("__", "_")


def _widths(rows: list[list[str]], total: float) -> list[float]:
    lens = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lens = [min(max(n, 6), 60) for n in lens]
    scale = total / sum(lens)
    return [n * scale for n in lens]


def _split_row(line: str) -> list[str]:
    return [inline(c.strip()) for c in line.strip().strip("|").split("|")]


def render(pdf: Report, md_path: Path, root: Path, skip_title: bool = False,
           table_captions: dict[int, str] | None = None) -> None:
    """Render one Markdown file. table_captions maps table index to a caption."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    captions = table_captions or {}
    i, n_table, para = 0, 0, []

    def flush() -> None:
        if para:
            pdf.para(inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            flush()
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                i += 1
        elif line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            title = inline(line.lstrip("#").strip())
            if level == 1 and not skip_title:
                pdf.h1(title)
            elif level == 2:
                pdf.h2(title)
            elif level >= 3:
                pdf.h3(title)
        elif line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|$", lines[i].strip()):
                    rows.append(_split_row(lines[i]))
                i += 1
            n_table += 1
            pdf.data_table(rows, _widths(rows, pdf.w - 2 * MARGIN),
                           captions.get(n_table, f"{md_path.stem}, table {n_table}."))
            continue
        elif line.startswith("- "):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith(("- ", "  ")):
                if lines[i].startswith("- "):
                    items.append(inline(lines[i][2:].strip()))
                else:
                    items[-1] += " " + inline(lines[i].strip())
                i += 1
            pdf.bullets(items)
            continue
        elif m := _PDF_FIGURE.match(line.strip()):
            flush()
            pdf.figure(root / m.group(1), m.group(2))
        elif line.lstrip().startswith("<!--"):
            flush()  # other HTML comments (table markers) are not rendered
        elif m := _IMAGE.match(line.strip()):
            flush()
            pdf.figure(root / m.group(2).lstrip("./"), inline(m.group(1)))
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
