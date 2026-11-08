"""E03-S04: drawings and charts of the code-block renderers in Word — drawings as SVG pictures
with a PNG beside them, charts native, both sized by the same rules and captioned
"Abbildung n: …" in turn with the other figures."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

import pytest
from PIL import Image

from pta_documents.charts import ChartKind, ChartSeries, ChartSpec
from pta_documents.charts.renderer import ChartRenderer
from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import colors
from pta_documents.design.variants import WordVariant
from pta_documents.drawing import Drawing, DrawingPath, DrawingShape, DrawingText
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import images
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRequest,
    DrawingGraphic,
)
from pta_documents.generation.docx import drawings
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.markdown import DocumentResource
from tests.charts.financial import figures
from tests.expected import assert_matches_expected
from tests.generation.docx.conftest import generate, open_docx, parts, style_name

pytest.importorskip("resvg_py")

WP: Final = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
ASVG: Final = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}"
SAMPLES: Final = Path(__file__).parent / "samples"
EMU_PER_PIXEL: Final = 9525


def drawing(width: float = 300, height: float = 120) -> Drawing:
    return Drawing(
        width,
        height,
        (
            DrawingShape(DrawingPath.rectangle(10, 10, 120, 60), colors.PTA_BLUE, None, 0),
            DrawingText.line(20, 100, "Ablauf", 14, colors.TEXT_WORD),
        ),
    )


SPEC: Final = ChartSpec(
    ChartKind.BAR,
    ("Q1", "Q2", "Q3"),
    (ChartSeries("Plan", (1.5, 2.0, None)), ChartSeries("Ist", (2.0, 2.5, 3.0))),
    title="Aufträge",
    source="Quelle: erfunden",
)


@dataclass(frozen=True)
class FixedRenderer:
    """``testbild`` blocks become ``drawing`` (``breit``: a wide one), ``testchart`` ``SPEC``."""

    authoring_guide: str | None = None

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        words = request.info.split()
        if words[0] == "testbild":
            wide = "breit" in words
            return DrawingGraphic(drawing(4000, 3000) if wide else drawing())
        if words[0] == "testchart":
            return ChartGraphic(SPEC, drawing())
        return None


OPTIONS: Final = DocxOptions(code_block_renderers=(FixedRenderer(),))


def png(width: int = 96, height: int = 48) -> DocumentResource:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return DocumentResource("bild.png", "image/png", buffer.getvalue())


def report(body: str, variant: str = "hoch", language: str = "de") -> str:
    return f"---\ntitel: Bericht\nvorlage: {variant}\nsprache: {language}\n---\n\n{body}"


BODY: Final = (
    "# Grafiken\n\n"
    '![Bild](bild.png "Ein Bild davor")\n\n'
    "```testbild\nA --> B\n```\n\n"
    "Abbildung: Der Ablauf\n\n"
    "```testchart\nDaten\n```\n\n"
    "Text danach.\n\n"
    "```testbild breit\nGroß\n```\n"
)


def body(data: bytes) -> Any:
    return cast(Any, open_docx(data).element).body


def text_size(data: bytes) -> tuple[int, int]:
    section = open_docx(data).sections[0]
    width = int(section.page_width or 0) - int(section.left_margin or 0)
    width -= int(section.right_margin or 0)
    height = int(section.page_height or 0) - int(section.top_margin or 0)
    height -= int(section.bottom_margin or 0)
    return width, height


def extents(data: bytes) -> list[tuple[int, int]]:
    return [(int(e.get("cx")), int(e.get("cy"))) for e in body(data).iter(f"{WP}extent")]


@pytest.mark.parametrize("variant", [WordVariant.PORTRAIT, WordVariant.LANDSCAPE])
def test_drawings_are_svg_pictures_and_charts_native(
    variant: WordVariant, review_dir: Path
) -> None:
    data = generate(report(BODY, variant.value), OPTIONS, (png(),))
    (review_dir / f"diagrams-{variant.value}.docx").write_bytes(data)
    files = parts(data)
    assert any(n.startswith("word/charts/chart") for n in files)
    svgs = [n for n in files if n.endswith(".svg")]
    assert len(svgs) == 2
    assert b"Ablauf" in files[svgs[0]]
    blips = list(body(data).iter(f"{ASVG}svgBlip"))
    assert len(blips) == 2

    width, height = text_size(data)
    sizes = extents(data)
    assert len(sizes) == 4  # picture, drawing, chart, wide drawing
    # A drawing at its natural size (1 px = 0.75 pt), never enlarged …
    assert sizes[1] == (300 * EMU_PER_PIXEL, 120 * EMU_PER_PIXEL)
    # … a wide one shrunk into the text width and 80 % of the text height,
    wide = sizes[3]
    assert wide[0] <= width and wide[1] <= height * 0.8 + 1
    assert abs(wide[0] / wide[1] - 4 / 3) < 0.01
    # … a chart as wide as the text, at most 5:8 as high, capped at 80 % of the text height.
    assert sizes[2] == (width, min(round(width * 5 / 8), int(height * 0.8)))


def test_portrait_and_landscape_charts_follow_the_same_rule() -> None:
    portrait = generate(report("```testchart\n1\n```\n", "hoch"), OPTIONS)
    landscape = generate(report("```testchart\n1\n```\n", "quer"), OPTIONS)
    width, _ = text_size(portrait)
    assert extents(portrait) == [(width, round(width * 5 / 8))]
    width, height = text_size(landscape)
    assert extents(landscape) == [(width, int(height * 0.8))]  # 5:8 would not fit


def test_captions_run_on_with_the_other_figures() -> None:
    data = generate(report(BODY), OPTIONS, (png(),))
    texts = [p.text for p in open_docx(data).paragraphs]
    captions = [t for t in texts if t.startswith("Abbildung")]
    assert captions == [
        "Abbildung 1: Ein Bild davor",
        "Abbildung 2: Der Ablauf",
        "Abbildung 3: Aufträge",
    ]
    assert "Abbildung: Der Ablauf" not in texts  # the paragraph became the caption
    assert texts[texts.index("Abbildung 3: Aufträge") + 1] == "Quelle: erfunden"
    assert "Text danach." in texts  # an ordinary paragraph after a graphic stays one


def test_the_caption_paragraph_goes_before_the_chart_title() -> None:
    data = generate(report("```testchart\n1\n```\n\nAbbildung: Eigene Beschriftung\n"), OPTIONS)
    texts = [p.text for p in open_docx(data).paragraphs]
    assert "Abbildung 1: Eigene Beschriftung" in texts
    assert not any("Aufträge" in t for t in texts)


def test_in_english_the_caption_is_figure() -> None:
    markdown = report("```testbild\n1\n```\n\nFigure: The flow\n", language="en")
    texts = [p.text for p in open_docx(generate(markdown, OPTIONS)).paragraphs]
    assert "Figure 1: The flow" in texts
    markdown = report("```testbild\n1\n```\n\nAbbildung: Auch deutsch\n", language="en")
    texts = [p.text for p in open_docx(generate(markdown, OPTIONS)).paragraphs]
    assert "Figure 1: Auch deutsch" in texts


def test_graphic_and_caption_stay_together() -> None:
    data = generate(report("```testbild\n1\n```\n\nAbbildung: Zusammen\n"), OPTIONS)
    paragraphs = open_docx(data).paragraphs
    i = next(n for n, p in enumerate(paragraphs) if p._p.find(f".//{WP}inline") is not None)
    assert paragraphs[i].paragraph_format.keep_with_next is True
    assert style_name(paragraphs[i + 1]) == "caption"


def test_without_a_caption_there_is_none_and_nothing_is_kept_with_the_next() -> None:
    data = generate(report("```testbild\n1\n```\n\nWeiter im Text.\n"), OPTIONS)
    paragraphs = open_docx(data).paragraphs
    assert not any(p.text.startswith("Abbildung") for p in paragraphs)
    i = next(n for n, p in enumerate(paragraphs) if p._p.find(f".//{WP}inline") is not None)
    assert paragraphs[i].paragraph_format.keep_with_next is None


def test_the_alt_text_is_the_info_string() -> None:
    data = generate(report("```testbild mit Text\n1\n```\n"), OPTIONS)
    assert [d.get("descr") for d in body(data).iter(f"{WP}docPr")] == ["testbild mit Text"]


def test_without_the_svg_extra_a_drawing_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(drawings, "svg_available", lambda: False)
    options = DocxOptions(code_block_renderers=(FixedRenderer(),), image_converters=())
    with pytest.raises(DocumentConversionError) as error:
        generate(report("# A\n\n```testbild\n1\n```\n"), options)
    assert error.value.format is DocumentFormat.DOCX
    assert error.value.reason.startswith("Line 9: The `testbild` block is a drawing")
    assert "pip install 'pta-documents[svg]'" in error.value.reason


def test_without_converters_a_drawing_is_an_error_that_says_so() -> None:
    options = DocxOptions(code_block_renderers=(FixedRenderer(),), image_converters=())
    with pytest.raises(DocumentConversionError, match="no image converter takes SVG"):
        generate(report("```testbild\n1\n```\n"), options)
    assert images.svg_available()


def test_a_financial_chart_is_a_picture_with_the_default_renderers() -> None:
    from pta_documents.charts.financial import to_json

    block = f"```financial-chart\n{to_json(figures.growth_trend())}\n```\n"
    options = DocxOptions(code_block_renderers=(ChartRenderer(),))
    data = generate(report(f"# Zahlen\n\n{block}\nAbbildung: Wachstum\n"), options)
    assert len(list(body(data).iter(f"{ASVG}svgBlip"))) == 1
    names = [n for n in parts(data) if n.endswith(".svg")]
    assert len(names) == 1
    assert "Abbildung 1: Wachstum" in [p.text for p in open_docx(data).paragraphs]


def test_the_converter_reads_a_chart_as_a_table_of_its_data() -> None:
    data = generate(report("```testchart\n1\n```\n"), OPTIONS)
    markdown = DocxConverter().convert(data).text
    assert "|  | Plan | Ist |\n| --- | --- | --- |\n| Q1 | 1.5 | 2 |\n" in markdown
    assert "| Q3 |  | 3 |" in markdown


def test_roundtrip(review_dir: Path) -> None:
    data = generate(report(BODY), OPTIONS, (png(),))
    markdown = DocxConverter().convert(data).text
    assert_matches_expected(SAMPLES / "diagrams-hoch.roundtrip.expected.md", markdown)
