"""Report tooling: marked tables, Markdown rendering and the PDF layout rules."""

import pytest

from guardbench.analysis import analyse
from guardbench.report.engine import Report
from guardbench.report.markdown import inline, render
from guardbench.report.tables import update
from tests.test_pipeline import run_dir  # noqa: F401 - pytest fixture reuse


def test_marked_tables_are_regenerated(run_dir, tmp_path):  # noqa: F811
    path, _ = run_dir
    analyse(path, n_boot=10)
    md = tmp_path / "r.md"
    md.write_text("intro\n<!-- table:overall:start -->\nold\n<!-- table:overall:end -->\nend\n",
                  encoding="utf-8")
    assert update(md, path) == ["overall"]
    text = md.read_text(encoding="utf-8")
    assert "old" not in text and "`kw`" in text and text.endswith("end\n")


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_empty_marked_block_is_filled_once(run_dir, tmp_path, newline):  # noqa: F811
    # Regression: an empty block (markers on consecutive lines) or a CRLF file used to
    # match nothing, so the tables stayed empty while the command reported success.
    path, _ = run_dir
    analyse(path, n_boot=10)
    md = tmp_path / "r.md"
    md.write_bytes(
        newline.join(["a", "<!-- table:overall:start -->", "<!-- table:overall:end -->", "b", ""])
        .encode("utf-8")
    )
    assert update(md, path) == ["overall"]
    first = md.read_text(encoding="utf-8")
    assert "`kw`" in first
    update(md, path)
    assert md.read_text(encoding="utf-8") == first  # idempotent, no duplicated table


def test_inline_strips_links_and_code():
    assert inline("voir [la doc](docs/a.md) et `x--y`") == "voir la doc et x- -y"
    assert inline("[site](https://example.org)") == "[site](https://example.org)"


def test_render_and_deferred_figure(tmp_path):
    from PIL import Image

    img = tmp_path / "tall.png"
    Image.new("RGB", (400, 900), "white").save(img)
    md = tmp_path / "doc.md"
    body = " ".join(["Phrase de remplissage pour pousser le texte vers le bas."] * 60)
    md.write_text(
        f"# Titre\n\n{body}\n\n![Une figure haute](tall.png)\n\n{body}\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n\n- point un\n- point deux\n",
        encoding="utf-8",
    )
    pdf = Report("t", "t")
    pdf.add_page()
    pdf.add_page()
    render(pdf, md, tmp_path)
    pdf.finish()
    assert pdf.fig_no == 1 and pdf.tab_no == 1 and not pdf.pending
    out = tmp_path / "doc.pdf"
    pdf.output(str(out))
    assert out.stat().st_size > 5000


@pytest.mark.parametrize("ratio", [0.3, 2.5])
def test_figure_never_overflows_page(tmp_path, ratio):
    from PIL import Image

    img = tmp_path / "f.png"
    Image.new("RGB", (1000, int(1000 * ratio)), "white").save(img)
    pdf = Report("t", "t")
    pdf.add_page()
    pdf.add_page()
    pdf.set_y(200)
    pdf.figure(img, "cap")
    pdf.finish()
    assert pdf.get_y() <= pdf.h - pdf.b_margin + 1
