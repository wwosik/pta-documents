"""E09-S04: scene slides — named shapes on ``Nur Titel`` inside the content area, which Morph
moves between two slides; steps as builds; Word leaves the scene out, the PDF draws it."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Final

from lxml import etree
from PIL import Image

from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.design import slides as design
from pta_documents.design.variants import WordVariant
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.common.scene import UNIT_EMU
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx import scene_writer
from pta_documents.markdown import DocumentResource, MarkdownDocument
from tests.generation.docx.conftest import open_docx
from tests.generation.pdf.layout.support import Pdf, make_pdf
from tests.generation.pptx.conftest import generate, layout_names, open_pptx

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
P: Final = "http://schemas.openxmlformats.org/presentationml/2006/main"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS: Final = {"a": A, "p": P}

TWO_SLIDES: Final = """# Deck

## Drei Orte {uebergang="morph"}

::: scene
- sp: box   10,20  36x14  "SharePoint"
- od: round 62,30  36x14  "OneDrive"                rotate=-3
- q:  pill  45,52  70x9   "Welche Version gilt?"    fill=warning step=1
:::

::: notes
Drei Orte, eine Frage.
:::

## Ein Ort {uebergang="morph"}

::: scene
- sp: box   50,20  60x18  "Ein Ablageort"  fill=primary text=background bold
- od: round 50,20  60x18                   opacity=0
- a:  arrow 80,40  0x14                    step=1
- c:  circle 140,0 20x20  "OK"             fill=success solid
- t:  text  0,60   60x7   "Hinweis"        size=12
- l:  line  0,66   160x0  line=border
:::
"""


def png(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return buffer.getvalue()


def shapes(data: bytes, index: int) -> dict[str, etree._Element]:
    """The named shapes of the slide ``index``, by their name."""
    slide = open_pptx(data).slides[index]
    tree = etree.fromstring(etree.tostring(slide.shapes._spTree))
    result: dict[str, etree._Element] = {}
    for shape in tree:
        c_nv_pr = shape.find("*/p:cNvPr", NS)
        name = str(c_nv_pr.get("name", "")) if c_nv_pr is not None else ""
        if name.startswith("!!"):
            result[name] = shape
    return result


def box(element: etree._Element) -> tuple[int, int, int, int]:
    off = element.find(".//a:xfrm/a:off", NS)
    ext = element.find(".//a:xfrm/a:ext", NS)
    assert off is not None and ext is not None
    return int(off.get("x", 0)), int(off.get("y", 0)), int(ext.get("cx", 0)), int(ext.get("cy", 0))


def test_two_scene_slides_on_title_only_morph_their_namesakes(review_dir: Path) -> None:
    data = generate(TWO_SLIDES)
    (review_dir / "deck-scene.pptx").write_bytes(data)
    assert layout_names(data)[1:] == [design.LAYOUTS.title_only] * 2
    first, second = shapes(data, 1), shapes(data, 2)
    assert list(first) == ["!!sp", "!!od", "!!q"]
    assert list(second) == ["!!sp", "!!od", "!!a", "!!c", "!!t", "!!l"]
    for slide in (1, 2):
        element = open_pptx(data).slides[slide].element
        assert element.find(f"{{{MC}}}AlternateContent") is not None  # morph
    area = design.CONTENT_AREA
    for element in [*first.values(), *second.values()]:
        x, y, w, h = box(element)
        assert area.left <= x and x + w <= area.right + 1
        assert area.top <= y and y + h <= area.bottom + 1
    assert box(first["!!sp"]) == (
        area.left + 10 * UNIT_EMU,
        area.top + 20 * UNIT_EMU,
        36 * UNIT_EMU,
        14 * UNIT_EMU,
    )


def test_the_shapes_are_drawn_in_pta_colours() -> None:
    data = generate(TWO_SLIDES)
    first, second = shapes(data, 1), shapes(data, 2)

    def fill(element: etree._Element) -> str | None:
        found = element.find("p:spPr/a:solidFill/a:srgbClr", NS)
        return found.get("val") if found is not None else None

    def line(element: etree._Element) -> str | None:
        found = element.find("p:spPr/a:ln/a:solidFill/a:srgbClr", NS)
        return found.get("val") if found is not None else None

    assert (fill(first["!!sp"]), line(first["!!sp"])) == (colors.GREY_LIGHT, colors.GREY_MID)
    assert fill(first["!!q"]) == colors.tint(colors.SIGNAL_AMBER, 0.12)
    assert line(first["!!q"]) == colors.SIGNAL_AMBER
    assert fill(second["!!sp"]) == colors.PTA_BLUE
    assert fill(second["!!c"]) == colors.SIGNAL_GREEN
    assert line(second["!!l"]) == colors.GREY_MID
    run = second["!!sp"].find(".//a:r/a:rPr", NS)
    assert run is not None and run.get("b") == "1"
    text_fill = run.find("a:solidFill/a:srgbClr", NS)
    assert text_fill is not None and text_fill.get("val") == colors.WHITE
    alpha = second["!!od"].find("p:spPr/a:solidFill/a:srgbClr/a:alpha", NS)
    assert alpha is not None and alpha.get("val") == "0"
    xfrm = first["!!od"].find("p:spPr/a:xfrm", NS)
    assert xfrm is not None and xfrm.get("rot") == str(357 * 60000)
    pill = first["!!q"].find("p:spPr/a:prstGeom", NS)
    assert pill is not None and pill.get("prst") == "roundRect"
    adjust = pill.find("a:avLst/a:gd", NS)
    assert adjust is not None and adjust.get("fmla") == "val 50000"
    arrow = second["!!a"]
    assert arrow.find("p:spPr/a:ln/a:tailEnd", NS) is not None
    assert arrow.find("p:txBody", NS) is None


def test_steps_are_builds_and_notes_stay() -> None:
    data = generate(TWO_SLIDES)
    deck = open_pptx(data)
    for index, name in ((1, "!!q"), (2, "!!a")):
        slide = deck.slides[index]
        timing = slide.element.find(f"{{{P}}}timing")
        assert timing is not None
        c_nv_pr = shapes(data, index)[name].find("*/p:cNvPr", NS)
        assert c_nv_pr is not None
        spid = c_nv_pr.get("id")
        targets = {t.get("spid") for t in timing.iter(f"{{{P}}}spTgt")}
        assert targets == {spid}
    notes = deck.slides[1].notes_slide.notes_text_frame
    assert notes is not None and "Drei Orte, eine Frage." in notes.text


def test_an_image_is_fitted_into_its_box() -> None:
    markdown = '# D\n\n## F\n\n::: scene\n- logo: image 0,0 40x20 "Logo" image=logo.png\n:::\n'
    data = generate(markdown, resources=(DocumentResource("logo.png", "image/png", png(100, 100)),))
    (picture,) = shapes(data, 1).values()
    assert picture.tag == f"{{{P}}}pic"
    x, y, w, h = box(picture)
    area = design.CONTENT_AREA
    assert (w, h) == (20 * UNIT_EMU, 20 * UNIT_EMU)
    assert (x, y) == (area.left + 10 * UNIT_EMU, area.top)
    c_nv_pr = picture.find("*/p:cNvPr", NS)
    assert c_nv_pr is not None and c_nv_pr.get("descr") == "Logo"


def test_a_dark_scene_slide_has_a_kicker_and_white_free_text() -> None:
    markdown = '# D\n\n## F {.dark kicker="Ziel"}\n\n::: scene\n- t: text 0,0 40x8 "Weiß"\n:::\n'
    data = generate(markdown)
    slide = open_pptx(data).slides[1]
    texts = [t.text for t in slide.element.iter(f"{{{A}}}t")]
    assert "Ziel" in texts and "Weiß" in texts
    (shape,) = shapes(data, 1).values()
    fill = shape.find(".//a:rPr/a:solidFill/a:srgbClr", NS)
    assert fill is not None and fill.get("val") == colors.WHITE


def test_the_converter_reads_the_texts_back() -> None:
    markdown = PptxConverter().convert(generate(TWO_SLIDES)).text
    assert "SharePoint\n\nOneDrive\n\nWelche Version gilt?" in markdown
    assert "Ein Ablageort" in markdown and "Hinweis" in markdown


def test_the_line_widths_follow_the_still_drawing() -> None:
    assert round(2 * UNIT_EMU / 10) == scene_writer.BOX_LINE
    assert round(3 * UNIT_EMU / 10) == scene_writer.LINE_WIDTH


# ---------------------------------------------------------------------- Word and PDF


def test_word_leaves_the_scene_out_with_a_note() -> None:
    output = io.BytesIO()
    result = DocxGenerator().generate(
        MarkdownDocument(TWO_SLIDES),
        output,
        DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER),
    )
    codes = [n.code for n in result.notes]
    assert codes.count(NoteCodes.SCENE_DROPPED) == 2
    text = "\n".join(p.text for p in open_docx(output.getvalue()).paragraphs)
    assert "SharePoint" not in text and "Drei Orte" in text and "Ein Ort" in text


def test_the_pdf_draws_the_scene_as_a_still_picture(review_dir: Path) -> None:
    markdown = TWO_SLIDES.replace("# Deck\n\n", "") + (
        '\n## Bild\n\n::: scene\n- logo: image 0,0 40x20 "Logo" image=logo.png\n:::\n'
    )
    resources = (DocumentResource("logo.png", "image/png", png(100, 50)),)
    data = make_pdf(markdown, resources)
    (review_dir / "scene.pdf").write_bytes(data)
    pdf = Pdf(data)
    text = "\n".join(pdf.page_texts)
    for word in ("SharePoint", "OneDrive", "Welche Version gilt?", "Ein Ablageort", "Hinweis"):
        assert word in text
    assert sum(len(images) for images in pdf.images) == 1
