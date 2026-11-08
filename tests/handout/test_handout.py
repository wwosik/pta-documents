"""E16-S03: the handout of a presentation (``pta_documents.handout``, ``./run.sh handout``)."""

from __future__ import annotations

import importlib.util
import io
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from docx.document import Document
from lxml import etree
from PIL import Image

from pta_documents.conversions.docx import DocxConverter
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.openxml import W
from pta_documents.generation.common.result import NoteCodes
from pta_documents.handout import (
    Handout,
    HandoutLayout,
    HandoutOptions,
    build_handout,
    slide_pictures,
    write_handout,
)
from pta_documents.handout.handout import geometry, print_picture
from pta_documents.markdown import MarkdownDocument
from pta_documents.preview import PreviewUnavailableError, SlidePicture
from tests.conftest import REPO_ROOT
from tests.expected import assert_matches_expected
from tests.generation.docx.conftest import open_docx

SAMPLES: Final = Path(__file__).parent / "samples"
SOURCE: Final = SAMPLES / "schulung-praesentation.md"
KUNDE_TITLES: Final = (
    "Schulung Markdown",
    "Agenda",
    "Grundlagen",
    "Begriffe",
    "Übung",
    "Praxis",
    "Werkzeuge",
    "Vielen Dank!",
)
"""The slides of the customer's version, in order (without „Preise", which is internal, and
the backup)."""
NOTES: Final = (
    "Begrüßung und Vorstellungsrunde.",
    "Ablauf kurz erklären.",
    "Auf die Rauten eingehen.",
    "Beispiel zeigen",
    "Nur intern: Rabatte nennen.",
    "Nur bei Nachfragen zeigen.",
)
CONTENT_SLIDES: Final = 6
"""Customer's version: every slide but title and closing, which get no lines."""


def deck() -> MarkdownDocument:
    return MarkdownDocument(SOURCE.read_text(encoding="utf-8"))


def fake_pictures(count: int = 20) -> list[SlidePicture]:
    """A picture per slide number without a browser: 1600 × 900, a colour per slide."""
    pictures: list[SlidePicture] = []
    for number in range(1, count + 1):
        output = io.BytesIO()
        Image.new("RGB", (1600, 900), (number * 10, 120, 200)).save(output, "PNG")
        pictures.append(SlidePicture(number, output.getvalue()))
    return pictures


def handout(
    layout: HandoutLayout = HandoutLayout.THREE,
    audience: Audience | None = None,
    pictures: list[SlidePicture] | None = None,
    document: MarkdownDocument | None = None,
) -> Handout:
    return build_handout(document or deck(), pictures, HandoutOptions(layout, audience))


def word(result: Handout) -> Document:
    output = io.BytesIO()
    write_handout(result, output)
    return open_docx(output.getvalue())


def ruled_paragraphs(document: Document) -> int:
    """Paragraphs with a rule below them (lines to write on), in tables too."""
    body: etree._Element = document.element.body  # type: ignore[attr-defined]
    return len(body.findall(f".//{{{W}}}p/{{{W}}}pPr/{{{W}}}pBdr/{{{W}}}bottom"))


def pictures_in(document: Document) -> int:
    body: etree._Element = document.element.body  # type: ignore[attr-defined]
    return len(body.findall(f".//{{{W}}}drawing"))


def captions(document: Document) -> list[str]:
    body: etree._Element = document.element.body  # type: ignore[attr-defined]
    return [
        "".join(t.text or "" for t in p.iter(f"{{{W}}}t"))
        for p in body.iter(f"{{{W}}}p")
        if (style := p.find(f"{{{W}}}pPr/{{{W}}}pStyle")) is not None
        and style.get(f"{{{W}}}val") == "Beschriftung"
    ]


# ---------------------------------------------------------------------- without pictures


def test_without_pictures_the_handout_has_every_slide_title_and_lines() -> None:
    result = handout()
    assert not result.pictures
    assert result.audience is Audience.KUNDE
    text = result.document.text
    for number, title in enumerate(KUNDE_TITLES, start=1):
        assert f"**Folie {number}: {title}**" in text
    assert "Preise" not in text.split("**Zeitplan**")[1].split("| **30 min**")[-1]
    assert "Reservefolie" not in text
    assert "Ein Einleitungstext" not in text
    assert "Markdown ist ein Textformat.\n\n- Überschriften mit #\n- Listen mit -" in text
    lines = geometry(HandoutLayout.THREE).lines
    assert text.count("\n***\n") == CONTENT_SLIDES * lines
    assert NoteCodes.HANDOUT_WITHOUT_PICTURES in [n.code for n in result.notes]
    assert ruled_paragraphs(word(result)) == CONTENT_SLIDES * lines


def test_without_pictures_the_customer_reads_no_notes() -> None:
    text = handout().document.text
    assert not any(note in text for note in NOTES)
    assert "Geplant" not in text


def test_the_trainer_handout_has_every_note_the_times_and_the_backup() -> None:
    text = handout(audience=Audience.TRAINER).document.text
    for note in NOTES:
        assert note in text
    assert "> Geplant: 09:05–09:15 (10 min)" in text
    assert "**Folie 11: Reservefolie**" in text and "# Backup" in text
    assert "- a\n- b" in text  # the solution


# ---------------------------------------------------------------------- the document


def test_the_front_matter_comes_from_the_deck() -> None:
    text = handout().document.text
    assert text.startswith(
        '---\nvorlage: hoch\ntitel: "Schulung Markdown"\nuntertitel: "Dokumente aus einer '
        'Quelle"\nautor: "Erika Mustermann"\nort: "Köln"\ndatum: "2026-11-08"\n'
        "typografie: nein\n---\n"
    )
    trainer = handout(HandoutLayout.TWO, Audience.TRAINER).document.text
    assert trainer.startswith("---\nvorlage: quer\n")
    assert "\nkennzeichnung: intern\n" in trainer


def test_the_schedule_stands_before_the_chapters_else_the_table_of_contents() -> None:
    text = handout().document.text
    assert text.index("**Zeitplan**") < text.index("| 09:05 | 09:25 | 20 min | **Grundlagen** |")
    assert text.index("| **30 min** |") < text.index("# Grundlagen")
    assert "inhaltsverzeichnis" not in text
    plain = MarkdownDocument("---\ntitel: Kurs\n---\n# Kurs\n\n# Teil\n\n## Folie\n\nText\n")
    text = handout(document=plain).document.text
    assert "\ninhaltsverzeichnis: ja\n" in text and "Zeitplan" not in text
    assert "# Teil" in text


def test_the_layout_chooses_the_template_and_the_pictures_their_place() -> None:
    pictures = fake_pictures()
    two = word(handout(HandoutLayout.TWO, pictures=pictures))
    three = word(handout(HandoutLayout.THREE, pictures=pictures))
    six = word(handout(HandoutLayout.SIX, pictures=pictures))
    assert two.sections[-1].page_width > two.sections[-1].page_height  # type: ignore[operator]
    assert three.sections[-1].page_width < three.sections[-1].page_height  # type: ignore[operator]
    for document in (two, three, six):
        assert pictures_in(document) == len(KUNDE_TITLES)
    # 2: picture | lines side by side, a table per slide but title and closing (and the schedule)
    rows = [t for t in two.tables if style_name_of(t) == "Bildreihe"]
    assert len(rows) == CONTENT_SLIDES and all(len(t.columns) == 2 for t in rows)
    assert ruled_paragraphs(two) == CONTENT_SLIDES * geometry(HandoutLayout.TWO).lines
    # 3: one below the other, no table but the schedule
    assert [style_name_of(t) for t in three.tables] == ["PTA"]
    # 6: two pictures a row; the agenda alone, the chapters' slides in pairs
    rows = [t for t in six.tables if style_name_of(t) == "Bildreihe"]
    assert [len(t.columns) for t in rows] == [2, 2]
    assert ruled_paragraphs(six) == 4 * geometry(HandoutLayout.SIX).lines


def style_name_of(table: object) -> str:
    style = getattr(table, "style", None)
    return str(style.name) if style is not None else ""


def test_two_three_and_six_slides_fill_a_page() -> None:
    """The heights the sizes come from: pictures, captions and lines of a page's slides, with
    one chapter heading, fit the text height of the template (estimated as ``geometry``)."""
    for layout in HandoutLayout:
        shape = geometry(layout)
        assert shape.picture_pt > 150  # at least 5.3 cm wide
        assert shape.lines >= 2
    assert geometry(HandoutLayout.TWO).columns == (32, 67)
    assert geometry(HandoutLayout.SIX).picture_pt < geometry(HandoutLayout.THREE).picture_pt


def test_every_picture_has_its_caption_without_a_number() -> None:
    document = word(handout(HandoutLayout.SIX, pictures=fake_pictures()))
    assert captions(document) == [
        f"Folie {n}: {title}" for n, title in enumerate(KUNDE_TITLES, start=1)
    ]
    xml = etree.tostring(document.element).decode()  # type: ignore[attr-defined]
    assert "SEQ Abbildung" not in xml


def test_the_trainer_sees_the_notes_beside_the_pictures() -> None:
    document = word(handout(HandoutLayout.TWO, Audience.TRAINER, fake_pictures()))
    table = next(t for t in document.tables if "Begriffe" in t.cell(0, 0).text)
    notes = table.cell(0, 1).text
    assert "Geplant: 09:05–09:15 (10 min)" in notes and "Auf die Rauten eingehen." in notes
    assert pictures_in(document) == 11
    texts = [p.text for t in document.tables for c in t._cells for p in c.paragraphs]
    assert "Beispiel zeigen" in texts


def test_six_a_page_puts_the_trainers_notes_under_the_row() -> None:
    text = handout(HandoutLayout.SIX, Audience.TRAINER, fake_pictures()).document.text
    row = (
        "![Folie 5: Preise](handout/folie-05.png) ![Folie 6: Übung](handout/folie-06.png)"
        "\n\n**Folie 5:**\n\nGeplant: 09:15–09:20 (5 min)\n\nNur intern: Rabatte nennen."
        "\n\n**Folie 6:**"
    )
    assert row in text


def test_the_pictures_are_framed_and_sized_for_print() -> None:
    picture = print_picture(fake_pictures(1)[0].png, 200)
    with Image.open(io.BytesIO(picture)) as opened:
        assert opened.size == (834, 469)  # 300 dpi at 200 pt
        assert round(opened.info["dpi"][0]) == 300
        rgb = opened.convert("RGB")
        assert rgb.getpixel((0, 0)) == (0xAF, 0xAF, 0xAF)
        assert rgb.getpixel((400, 200)) == (10, 120, 200)


def test_text_from_slides_stays_text() -> None:
    document = MarkdownDocument("# Kurs\n\n## A [x] *b* ==c== {y}\n\nText `#` und [d]{.success}\n")
    text = handout(document=document).document.text
    assert "**Folie 2: A \\[x\\] b c \\{y}**" in text
    docx = word(handout(document=document))
    assert any(p.text == "Folie 2: A [x] b c {y}" for p in docx.paragraphs)


def test_a_mistake_in_the_deck_raises_as_generating_it_would() -> None:
    with pytest.raises(DocumentConversionError, match="Line"):
        handout(document=MarkdownDocument("# Kurs\n\n::: solution\nx\n:::\n"))


def test_the_handout_round_trips_through_the_docx_converter(review_dir: Path) -> None:
    result = handout(HandoutLayout.TWO, Audience.TRAINER, fake_pictures())
    output = io.BytesIO()
    assert write_handout(result, output).codes() == []
    data = output.getvalue()
    (review_dir / "handout").mkdir(exist_ok=True)
    (review_dir / "handout" / "schulung-handout-trainer.docx").write_bytes(data)
    text = DocxConverter().convert(data).text
    assert_matches_expected(SAMPLES / "handout.roundtrip.expected.md", text)


# ---------------------------------------------------------------------- with the preview


@pytest.mark.usefixtures("browser")
def test_with_the_preview_every_slide_is_a_picture(review_dir: Path) -> None:
    pictures = slide_pictures(deck(), Audience.KUNDE)
    assert (
        len(pictures) == 10
    )  # with the two backup slides, which the customer's handout leaves out
    for layout in HandoutLayout:
        result = handout(layout, pictures=pictures)
        output = io.BytesIO()
        write_handout(result, output)
        (review_dir / "handout").mkdir(exist_ok=True)
        (review_dir / "handout" / f"schulung-handout-{int(layout)}.docx").write_bytes(
            output.getvalue()
        )
        assert pictures_in(open_docx(output.getvalue())) == len(KUNDE_TITLES)


def test_without_the_preview_the_pictures_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    with pytest.raises(PreviewUnavailableError, match="preview"):
        slide_pictures(deck())


# ---------------------------------------------------------------------- ./run.sh handout


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "handout_tool", REPO_ROOT / "tools/handout/handout.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL: Final = load_tool()


@pytest.fixture
def no_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*_: object) -> list[SlidePicture]:
        raise PreviewUnavailableError("no preview here")

    monkeypatch.setattr(TOOL, "slide_pictures", unavailable)


@pytest.mark.usefixtures("no_preview")
def test_the_tool_writes_the_handout_next_to_the_deck(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "schulung-praesentation.md"
    source.write_text(SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "notizen-bericht.md").write_text("# Bericht\n", encoding="utf-8")
    assert TOOL.main([str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "no slide pictures" in out and "handout-without-pictures" not in out
    assert "The handout shows the text of each slide" in out
    assert "skipped" in out and "notizen-bericht" in out
    assert (tmp_path / "schulung-praesentation-handout.docx").exists()
    assert TOOL.main([str(source), "--audience", "trainer", "--layout", "2", "--markdown"]) == 0
    stem = "schulung-praesentation-handout-trainer"
    assert (tmp_path / f"{stem}.docx").exists()
    assert "Nur bei Nachfragen zeigen." in (tmp_path / f"{stem}.md").read_text(encoding="utf-8")
    assert TOOL.main([str(source), "--strict"]) == 1  # the notes count


@pytest.mark.usefixtures("no_preview")
def test_the_tool_writes_the_pictures_beside_the_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(TOOL, "slide_pictures", lambda *_: fake_pictures())  # type: ignore[misc]
    source = tmp_path / "schulung-praesentation.md"
    source.write_text(SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    assert TOOL.main([str(source), "--markdown", "--out", str(tmp_path / "aus")]) == 0
    folder = tmp_path / "aus"
    text = (folder / "schulung-praesentation-handout.md").read_text(encoding="utf-8")
    assert "](schulung-praesentation-handout/folie-04.png)" in text
    names = sorted(p.name for p in (folder / "schulung-praesentation-handout").iterdir())
    assert names == [f"folie-{n:02d}.png" for n in range(1, 9)]


def test_the_tool_reports_mistakes_and_wrong_switches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "kaputt-praesentation.md"
    source.write_text("# Kurs\n\n::: solution\nx\n:::\n", encoding="utf-8")
    assert TOOL.main([str(source)]) == 1
    assert "ERROR" in capsys.readouterr().err
    assert TOOL.main([str(source), "--layout", "4"]) == 2
    assert TOOL.main([str(source), "--audience", "chef"]) == 2
    assert TOOL.main([str(source), "--farbe"]) == 2
    assert TOOL.main([]) == 1


def test_the_handout_is_named_in_the_guides() -> None:
    for guide in ("docs/anleitung.md", "docs/ki-anleitung.md", "docs/verwendung.md"):
        text = (REPO_ROOT / guide).read_text(encoding="utf-8")
        assert re.search(r"run\.sh handout", text), guide
