"""FPDF2 report engine with light EFREI branding and no large blank areas.

Layout rules enforced here, measured afterwards by scripts/check_blanks.py:
- a figure that does not fit the rest of the page is first scaled down (ratio
  kept, down to 62 %), then deferred: the following text flows into the gap
  and the figure is placed at the top of the next page;
- a heading never sits alone at the bottom of a page (needs 40 mm below it).
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

NAVY = (22, 55, 103)
ROSE = (255, 67, 184)
DARK = (5, 24, 50)
BLUE = (12, 120, 180)
GREY = (108, 117, 125)
LIGHT = (240, 243, 248)
WHITE = (255, 255, 255)

MARGIN = 17
MIN_FIG_RATIO = 0.62
HEADING_KEEP_MM = 40
ASSETS = Path(__file__).resolve().parents[3] / "reports" / "assets"
FONTS = ASSETS / "fonts"
GILROY = Path("C:/Windows/Fonts/Gilroy-ExtraBold.otf")


class Report(FPDF):
    def __init__(self, title: str, short_title: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.short_title = short_title
        self.set_margins(MARGIN, 20, MARGIN)
        self.set_auto_page_break(True, margin=18)
        self.add_font("Body", "", str(FONTS / "PlusJakartaSans-400.ttf"))
        self.add_font("Body", "B", str(FONTS / "PlusJakartaSans-700.ttf"))
        self.add_font("Body", "I", str(FONTS / "PlusJakartaSans-400i.ttf"))
        self.add_font("Display", "", str(FONTS / "PlusJakartaSans-800.ttf"))
        if GILROY.exists():  # EFREI brand typeface when installed locally (not redistributable)
            try:
                self.add_font("Gilroy", "", str(GILROY))
                self.display = "Gilroy"
            except Exception:  # noqa: BLE001 - fall back silently to the OFL face
                self.display = "Display"
        else:
            self.display = "Display"
        self.set_title(title)
        self.set_author("Adam Beloucif, Emilien Morice")
        self.set_creator("EFREI Paris, Mastère Data Engineering et IA, XDE826")
        self.pending: list[tuple[str, str, float]] = []
        self.fig_no = 0
        self.tab_no = 0

    # ----------------------------------------------------------------- frame
    def header(self) -> None:
        if self.page_no() == 1:  # cover page carries its own layout
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 3, "F")
        self.set_xy(MARGIN, 7)
        self.set_font("Body", "", 7.5)
        self.set_text_color(*GREY)
        self.cell(0, 4, self.short_title, align="L")
        logo = ASSETS / "efrei-logo-couleur.png"
        if logo.exists():
            self.image(str(logo), x=self.w - MARGIN - 16, y=5.5, h=7)  # height only: no distortion
        self.set_y(20)

    def footer(self) -> None:
        if self.page_no() == 1:  # cover page carries its own layout
            return
        self.set_y(-12)
        self.set_draw_color(*ROSE)
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), MARGIN + 12, self.get_y())
        self.set_font("Body", "", 7.5)
        self.set_text_color(*GREY)
        self.cell(0, 6, f"{self.page_no()}", align="R")

    def space_left(self) -> float:
        return self.h - self.b_margin - self.get_y()

    # -------------------------------------------------------------- blocks
    def _flush_pending(self) -> None:
        while self.pending:
            path, caption, width = self.pending[0]
            if not self._place_figure(path, caption, width, allow_break=False):
                return
            self.pending.pop(0)

    def h1(self, text: str) -> None:
        self._flush_pending()
        if self.space_left() < HEADING_KEEP_MM:
            self.add_page()
            self._flush_pending()
        self.ln(3)
        self.start_section(text, level=0)
        self.set_font(self.display, "", 15)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 7.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_fill_color(*ROSE)
        self.rect(MARGIN, self.get_y() + 0.5, 14, 0.9, "F")
        self.ln(3.5)

    def h2(self, text: str) -> None:
        self._flush_pending()
        if self.space_left() < HEADING_KEEP_MM - 10:
            self.add_page()
            self._flush_pending()
        self.ln(1.5)
        self.start_section(text, level=1)
        self.set_font("Body", "B", 10.5)
        self.set_text_color(*BLUE)
        self.multi_cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.8)

    def h3(self, text: str) -> None:
        self._flush_pending()
        if self.space_left() < HEADING_KEEP_MM - 15:
            self.add_page()
            self._flush_pending()
        self.ln(0.8)
        self.set_font("Body", "B", 9.5)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.4)

    def para(self, text: str, size: float = 9.5) -> None:
        self._flush_pending()
        self.set_font("Body", "", size)
        self.set_text_color(*DARK)
        self.multi_cell(0, size * 0.5, text, markdown=True, new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT)
        self.ln(1.6)

    def bullets(self, items: list[str], size: float = 9.5) -> None:
        self._flush_pending()
        self.set_font("Body", "", size)
        self.set_text_color(*DARK)
        for item in items:
            self.set_x(MARGIN + 2)
            self.set_text_color(*ROSE)
            self.cell(4, size * 0.5, "-")
            self.set_text_color(*DARK)
            self.multi_cell(0, size * 0.5, item, markdown=True, new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT)
            self.ln(0.6)
        self.ln(1)

    def data_table(self, rows: list[list[str]], widths: list[float], caption: str,
              size: float = 7.6, align: str | None = None) -> None:
        """rows[0] is the header. align: one letter per column (L, C, R)."""
        self._flush_pending()
        self.tab_no += 1
        self.set_font("Body", "", size)
        self.set_text_color(*DARK)
        self.set_draw_color(210, 217, 228)
        self.set_line_width(0.15)
        head = FontFace(emphasis="BOLD", color=WHITE, fill_color=NAVY)
        aligns = tuple(align) if align else None
        with self.table(
            col_widths=widths, width=sum(widths), line_height=size * 0.48,
            headings_style=head, cell_fill_color=LIGHT, cell_fill_mode="ROWS",
            text_align=aligns or "LEFT", padding=(0.9, 1.2), first_row_as_headings=True,
        ) as tab:
            for row in rows:
                tab.row([str(c) for c in row])
        self._caption(f"Tableau {self.tab_no}. {caption}")

    def _caption(self, text: str) -> None:
        self.ln(1)
        self.set_font("Body", "I", 8)
        self.set_text_color(*GREY)
        self.multi_cell(0, 4, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2.5)

    def figure(self, path: Path, caption: str, width: float | None = None) -> int:
        """Place a figure now if it fits (possibly scaled), else defer it. Returns its number."""
        self.fig_no += 1
        full = f"Figure {self.fig_no}. {caption}"
        width = width or (self.w - 2 * MARGIN)
        if self.pending or not self._place_figure(str(path), full, width, allow_break=False):
            self.pending.append((str(path), full, width))
        return self.fig_no

    def _place_figure(self, path: str, caption: str, width: float, allow_break: bool) -> bool:
        from PIL import Image

        with Image.open(path) as im:
            ratio = im.height / im.width
        caption_h = 9
        avail = self.space_left() - caption_h - 2
        height = width * ratio
        body = self.h - 20 - self.b_margin - caption_h - 2
        if height > body:  # taller than a whole page: fit the page body, ratio kept
            width, height = body / ratio, body
        if height > avail:
            if avail >= height * MIN_FIG_RATIO:
                width, height = avail / ratio, avail
            elif not allow_break:
                return False
            else:
                self.add_page()
        x = (self.w - width) / 2
        self.image(path, x=x, y=self.get_y(), w=width, h=height)
        self.set_y(self.get_y() + height)
        self._caption(caption)
        return True

    def finish(self) -> None:
        while self.pending:
            path, caption, width = self.pending.pop(0)
            self._place_figure(path, caption, width, allow_break=True)
