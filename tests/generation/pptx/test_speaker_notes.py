"""E09-S01: speaker notes (``::: notes``) on the notes pages, and back from the converter."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import slides as design
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.pptx.model import Kind, Paragraph, Run
from pta_documents.generation.pptx.notes import level
from tests.generation.pptx.conftest import generate, open_pptx
from tests.generation.pptx.test_content import deck

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": A, "p": P}


def notes_texts(data: bytes) -> list[str | None]:
    """The notes text of each slide; None for a slide without a notes page."""
    return [
        s.notes_slide.notes_text_frame.text if s.has_notes_slide else None  # type: ignore[union-attr]
        for s in open_pptx(data).slides
    ]


def notes_parts(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return sorted(n for n in z.namelist() if n.startswith("ppt/notesSlides/"))


def test_notes_go_on_every_slide_of_their_heading(review_dir: Path) -> None:
    data = deck()
    (review_dir / "deck-notes.pptx").write_bytes(data)
    texts = notes_texts(data)
    assert texts[0] == "Welcome everyone and thank the team for the figures."
    assert texts[1] == "Say which chapters follow."
    assert texts[2] is not None and texts[2].startswith("Walk through the formatting, slowly:")
    assert texts[3:7] == [None] * 4
    # The split slide (`Many points`, "Forts.") has the notes on both parts.
    split = "This slide is split; the notes come on every part."
    assert texts[7:9] == [split, split]
    assert texts[9:11] == [None, None]
    assert texts[11] == "Ask for questions."


def test_notes_keep_lists_and_inline_formatting_and_leave_out_tables_and_images() -> None:
    presentation = open_pptx(deck())
    notes = presentation.slides[2].notes_slide
    root = etree.fromstring(etree.tostring(notes.element))
    paragraphs = root.findall(f".//{{{A}}}p")
    lines: list[tuple[str, str]] = []
    for p in paragraphs:
        p_pr = p.find(f"{{{A}}}pPr")
        lvl = p_pr.get("lvl", "0") if p_pr is not None else "0"
        lines.append((lvl, "".join(t.text or "" for t in p.iter(f"{{{A}}}t"))))
    assert lines == [
        ("0", "Walk through the formatting, slowly:"),
        ("1", "bold and italic"),
        ("2", "nested on the second level"),
        ("1", "code and a link"),
    ]
    italic = root.xpath(".//a:r[a:t='slowly']/a:rPr/@i", namespaces=NS)
    assert italic == ["1"]
    code = root.xpath(".//a:r[a:t='code']/a:rPr/a:latin/@typeface", namespaces=NS)
    assert code == [design.CODE_FONT]
    link = root.xpath(".//a:r[a:t='link']/a:rPr/a:hlinkClick/@r:id", namespaces={**NS, "r": R})
    assert isinstance(link, list) and isinstance(link[0], str)
    assert notes.part.rels[link[0]].target_ref == "https://example.com"
    assert not root.findall(f".//{{{P}}}pic") and not root.findall(f".//{{{A}}}tbl")
    assert "Left" not in "".join(t.text or "" for t in root.iter(f"{{{A}}}t"))


def test_code_in_notes_keeps_its_lines_in_the_code_font() -> None:
    """E08-S03: the Markdown source of a slide goes into its notes as a fence."""
    markdown = (
        "# Deck\n\n## A\n\nText.\n\n:::: notes\nSo steht es da:\n\n"
        "```markdown\n::: cards\n  - eingerückt\n\n:::\n```\n::::\n"
    )
    notes = open_pptx(generate(markdown)).slides[1].notes_slide
    root = etree.fromstring(etree.tostring(notes.element))
    body = [p for p in root.iter(f"{{{A}}}p") if p.find(f"{{{A}}}endParaRPr") is not None]
    lines = ["".join(t.text or "" for t in p.iter(f"{{{A}}}t")) for p in body]
    assert lines == ["So steht es da:", "::: cards", "  - eingerückt", "", ":::"]
    fonts = root.xpath(".//a:r[a:t=':::']/a:rPr/a:latin/@typeface", namespaces=NS)
    assert fonts == [design.CODE_FONT]


def test_the_converter_reads_code_in_notes_back_as_a_fence() -> None:
    markdown = (
        "# Deck\n\n## A\n\nText.\n\n:::: notes\nVorher.\n\n"
        "```markdown\n::: cards\n  - `x`\n\n:::\n```\n\nNachher.\n::::\n"
    )
    back = PptxConverter().convert(generate(markdown)).text
    assert (
        ":::: notes\n\nVorher.\n\n```\n::: cards\n  - `x`\n\n:::\n```\n\nNachher.\n\n::::\n"
    ) in back


def test_notes_pages_use_the_notes_master_of_the_pta_template() -> None:
    data = deck()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        masters = [n for n in z.namelist() if n.startswith("ppt/notesMasters/notesMaster")]
        assert masters == ["ppt/notesMasters/notesMaster1.xml"]
        master = z.read(masters[0]).decode()
        rels = z.read("ppt/notesSlides/_rels/notesSlide1.xml.rels").decode()
    assert "Notizenplatzhalter" in master  # the PTA master, not one made up
    assert "../notesMasters/notesMaster1.xml" in rels


def test_a_deck_without_notes_has_no_notes_pages() -> None:
    data = generate("# Deck\n\n## Folie\n\n- " + "\n- ".join(f"Punkt {n}" for n in range(60)))
    assert len(open_pptx(data).slides) >= 3
    assert notes_parts(data) == []


def test_notes_on_flow_and_kind_slides_and_inside_containers() -> None:
    markdown = (
        "# Deck\n\n"
        "## Flow {.dark}\n\n::: cards\n### Karte\nText\n\n::: notes\nIn der Karte.\n:::\n:::\n\n"
        "## Agenda {.agenda}\n\n1. Eins\n2. Zwei\n\n::: notes\nZur Agenda.\n:::\n\n"
        "## Nur Notizen\n\n::: notes\nNichts sonst.\n:::\n"
    )
    data = generate(markdown)
    assert notes_texts(data) == [None, "In der Karte.", "Zur Agenda.", "Nichts sonst."]
    names = [s.slide_layout.name for s in open_pptx(data).slides]
    assert names[3] == design.LAYOUTS.title_and_text


def test_several_notes_blocks_are_joined() -> None:
    data = generate("# Deck\n\n## A\n\n::: notes\nEins.\n:::\n\nText.\n\n::: notes\nZwei.\n:::\n")
    assert notes_texts(data)[1] == "Eins.\nZwei."


def test_notes_before_the_first_heading_are_a_mistake() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate("Vorwort.\n\n::: notes\nWohin?\n:::\n\n# Deck\n")
    assert error.value.reason == (
        "Line 3: A '::: notes' belongs under a heading: put it below the '#' or '##' of its slide."
    )


def test_notes_take_no_arguments() -> None:
    with pytest.raises(DocumentConversionError, match="takes no arguments"):
        generate("# Deck\n\n::: notes lang\nText\n:::\n")


def test_list_levels_on_the_notes_master() -> None:
    runs = (Run("x"),)
    assert level(Paragraph(runs)) == 0
    assert level(Paragraph(runs, Kind.BULLET, 0)) == 1
    assert level(Paragraph(runs, Kind.NUMBERED, 1)) == 2
    assert level(Paragraph(runs, Kind.BULLET, 5)) == 3


def test_the_converter_reads_the_notes_back() -> None:
    data = generate("# Deck\n\n## A\n\nText.\n\n::: notes\nSag das.\n\n- Punkt\n  - tiefer\n:::\n")
    markdown = PptxConverter().convert(data).text
    assert "## A\n\nText.\n\n::: notes\n\nSag das.\n\n- Punkt\n\n  - tiefer\n\n:::\n" in markdown
    without = PptxConverter().convert(data, ConversionOptions(notes=False)).text
    assert "::: notes" not in without and "Sag das." not in without


def test_the_converter_leaves_out_empty_notes_and_the_master_prompt() -> None:
    data = generate("# Deck\n\n## A\n\nText.\n\n## B\n\nMehr.\n")
    presentation = open_pptx(data)
    empty = presentation.slides[1].notes_slide  # an empty notes page
    assert empty.notes_placeholder is not None
    frame = presentation.slides[2].notes_slide.notes_text_frame
    assert frame is not None
    frame.text = "Mastertextformat bearbeiten"
    output = io.BytesIO()
    presentation.save(output)
    markdown = PptxConverter().convert(output.getvalue()).text
    assert "::: notes" not in markdown


def test_the_roundtrip_is_stable() -> None:
    text_only = ConversionOptions(include_images=False)
    first = PptxConverter().convert(deck(), text_only).text
    again = PptxConverter().convert(generate(first), text_only).text
    assert again.count("::: notes") == first.count("::: notes") > 0
    assert [b.split(":::")[0] for b in again.split("::: notes")[1:]] == [
        b.split(":::")[0] for b in first.split("::: notes")[1:]
    ]
