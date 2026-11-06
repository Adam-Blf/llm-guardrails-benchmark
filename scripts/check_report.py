"""Quality gate for the generated PDF report.

Fails (exit 1) when a content page leaves more than 40 mm blank at the bottom
or between two blocks, when text crosses the side margins, or when a forbidden
typographic character (em dash, en dash, middle dot) appears. The cover, the
table of contents and the last page are excluded from the blank check.

Usage: python scripts/check_report.py [reports/rapport-guardrails-llm.pdf]
Needs PyMuPDF (pip install pymupdf).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf as fitz

MM = 72 / 25.4
MAX_BLANK_MM = 40
MARGIN_MM = 15
HEADER_MM = 18
FOOTER_MM = 18
SKIP_FIRST = 0
# Code points rather than characters, so this file passes its own typography rule.
FORBIDDEN = {chr(0x2014): "em dash", chr(0x2013): "en dash", chr(0x00B7): "middle dot"}
# Layout fillers left in a source file pass every geometric check: a cover with a test
# summary and a one-word conclusion once rendered green. Refuse them by content.
PLACEHOLDERS = re.compile(
    r"texte de test|paragraphe de test|lorem ipsum|\bTODO\b|\bTBD\b|^\s*Test\.\s*$",
    re.I | re.M,
)


def content_boxes(page: fitz.Page) -> list[fitz.Rect]:
    boxes = [fitz.Rect(b[:4]) for b in page.get_text("blocks") if b[4].strip()]
    boxes += [page.get_image_bbox(img) for img in page.get_images(full=True)]
    boxes += [fitz.Rect(d["rect"]) for d in page.get_drawings() if d["rect"].height > 3 * MM]
    top, bottom = HEADER_MM * MM, page.rect.height - FOOTER_MM * MM
    return sorted((r for r in boxes if r.y0 > top and r.y1 < bottom), key=lambda r: r.y0)


def blanks(page: fitz.Page) -> list[tuple[str, float]]:
    found, bottom = [], HEADER_MM * MM
    for box in content_boxes(page):
        if box.y0 - bottom > MAX_BLANK_MM * MM:
            found.append(("gap", (box.y0 - bottom) / MM))
        bottom = max(bottom, box.y1)
    free = (page.rect.height - FOOTER_MM * MM - bottom) / MM
    if free > MAX_BLANK_MM:
        found.append(("page bottom", free))
    return found


def check(pdf: Path) -> list[str]:
    doc = fitz.open(pdf)
    errors = []
    for number, page in enumerate(doc, start=1):
        text = page.get_text()
        errors += [f"page {number}: {name}" for ch, name in FORBIDDEN.items() if ch in text]
        errors += [f"page {number}: placeholder {m.group(0).strip()!r}"
                   for m in PLACEHOLDERS.finditer(text)]
        for block in page.get_text("blocks"):
            if block[6] == 0 and block[4].strip() and (
                    block[0] < MARGIN_MM * MM or block[2] > page.rect.width - MARGIN_MM * MM):
                errors.append(f"page {number}: text outside margin, {block[4].strip()[:40]!r}")
        if SKIP_FIRST < number < doc.page_count:
            errors += [f"page {number}: {size:.0f} mm blank ({kind})"
                       for kind, size in blanks(page)]
    print(f"{pdf.name}: {doc.page_count} pages")
    return errors


def main() -> int:
    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/rapport-guardrails-llm.pdf")
    errors = check(pdf)
    for error in errors:
        print("  FAIL", error)
    print("OK" if not errors else f"{len(errors)} defect(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
