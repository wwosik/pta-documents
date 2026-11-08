"""E16-S04: backup slides behind the closing slide, appendices A, B, C in Word and PDF."""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import zipfile
from html import unescape
from typing import Final

import pikepdf
import pptx
import pytest
from lxml import etree
from pptx.shapes.autoshape import Shape

from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import slides as design
from pta_documents.design.variants import WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import backup
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.check import DeckStats, check
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from tests.generation.pdf.support import body_texts

W: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CREATED: Final = dt.datetime(2026, 11, 8, 12, 0, tzinfo=dt.UTC)

DECK: Final = """# Schulung

## Agenda {.agenda}

# Grundlagen

## Erste Folie

Text

# Vertiefung

## Zweite Folie

Text

# Vielen Dank {.closing}

# Backup {.backup}

## Reservefolie

Mehr Text

# Weitere Reserve

## Noch eine Folie

Text
"""

REPORT: Final = """---
inhaltsverzeichnis: ja
---

# Einleitung

## Ziel

Text

# Glossar {.appendix}

## Begriffe

Text

### Tiefer

Text

# Quellen

Text
"""


def w(name: str) -> str:
    return f"{{{W}}}{name}"


def text_of(element: etree._Element) -> str:
    return "".join(str(t) for t in element.itertext())


def make_deck(markdown: str = DECK, options: PptxOptions | None = None) -> tuple[bytes, list[str]]:
    output = io.BytesIO()
    result = PptxGenerator().generate(
        MarkdownDocument(markdown), output, options or PptxOptions(code_block_renderers=())
    )
    return output.getvalue(), [n.code for n in result.notes]


def slide_texts(data: bytes) -> list[tuple[str, str, list[str]]]:
    """Layout, name and texts of every slide."""
    deck = pptx.Presentation(io.BytesIO(data))
    return [
        (
            slide.slide_layout.name,
            slide.name,
            [shape.text_frame.text for shape in slide.shapes if isinstance(shape, Shape)],
        )
        for slide in deck.slides
    ]


def make_report(markdown: str = REPORT) -> tuple[bytes, list[str]]:
    output = io.BytesIO()
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER, code_block_renderers=())
    result = DocxGenerator().generate(MarkdownDocument(markdown), output, options)
    return output.getvalue(), [n.code for n in result.notes]


def make_pdf(markdown: str = REPORT) -> tuple[bytes, list[str]]:
    output = io.BytesIO()
    options = PdfOptions(
        variant=WordVariant.PORTRAIT_NO_COVER,
        system_fonts=False,
        created=CREATED,
        code_block_renderers=(),
    )
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, options)
    return output.getvalue(), [n.code for n in result.notes]


# ---------------------------------------------------------------------- decks


def test_backup_slides_stand_behind_the_closing_slide_without_numbers() -> None:
    data, notes = make_deck()
    assert notes == []
    slides = slide_texts(data)
    layouts = [layout for layout, _, _ in slides]
    closing = layouts.index(design.LAYOUTS.closing)
    divider = slides[closing + 1]
    assert divider[0] == design.LAYOUTS.chapter
    assert divider[1] == design.BACKUP_SLIDE_NAME
    assert divider[2] == ["Backup"], "the divider has no chapter number"
    chapters = [texts for layout, _, texts in slides if layout == design.LAYOUTS.chapter]
    assert chapters == [["Grundlagen", "01"], ["Vertiefung", "02"], ["Backup"], ["Weitere Reserve"]]
    assert [s[2][0] for s in slides[closing + 1 :]] == [
        "Backup",
        "Reservefolie",
        "Weitere Reserve",
        "Noch eine Folie",
    ]


def test_the_agenda_leaves_out_the_backup() -> None:
    data, _ = make_deck()
    agenda = next(texts for layout, _, texts in slide_texts(data) if layout.startswith("Agenda"))
    assert "Grundlagen" in agenda and "Vertiefung" in agenda
    assert not any("Reserve" in text or text == "Backup" for text in agenda)


def test_the_footer_of_backup_slides_says_backup() -> None:
    data, _ = make_deck()
    footers = {
        texts[0]: [t for t in texts if t.startswith(design.FOOTER_PREFIX)]
        for _, _, texts in slide_texts(data)
    }
    assert footers["Erste Folie"] == ["PTA – Schulung"]
    assert footers["Reservefolie"] == ["PTA – Schulung · Backup"]
    assert footers["Noch eine Folie"] == ["PTA – Schulung · Backup"]


def test_the_customer_version_keeps_the_backup() -> None:
    data, _ = make_deck(options=PptxOptions(audience=Audience.KUNDE, code_block_renderers=()))
    assert any(name == design.BACKUP_SLIDE_NAME for _, name, _ in slide_texts(data))


def test_a_deck_without_closing_slide_may_have_a_backup() -> None:
    data, notes = make_deck(
        "# Deck\n\n## Folie\n\nText\n\n# Backup {.backup}\n\n## Reserve\n\nText\n"
    )
    assert notes == []
    assert [name for _, name, _ in slide_texts(data)][2] == design.BACKUP_SLIDE_NAME


def test_the_backup_is_never_the_title_slide() -> None:
    data, _ = make_deck("# Backup {.backup}\n\n## Reserve\n\nText\n")
    first = slide_texts(data)[0]
    assert first[0] == design.LAYOUTS.chapter and first[1] == design.BACKUP_SLIDE_NAME


def test_the_appendix_is_ignored_on_slides_with_a_note() -> None:
    data, notes = make_deck("# Deck\n\n# Anhang {.appendix}\n\n## Folie\n\nText\n")
    assert notes == [NoteCodes.ATTRIBUTE_IGNORED]
    chapters = [texts for layout, _, texts in slide_texts(data) if layout == design.LAYOUTS.chapter]
    assert chapters == [["Anhang", "01"]]


def test_the_html_deck_ends_its_progress_at_the_closing_slide() -> None:
    output = io.BytesIO()
    result = HtmlDeckGenerator().generate(
        MarkdownDocument(DECK), output, HtmlDeckOptions(code_block_renderers=())
    )
    assert result.notes == ()
    page = output.getvalue().decode("utf-8")
    config = json.loads(unescape(re.search(r'data-config="([^"]*)"', page).group(1)))  # type: ignore[union-attr]
    slides = re.findall(r'<section class="slide"[^>]*>', page)
    closing = next(i for i, s in enumerate(slides) if design.LAYOUTS.closing in s)
    assert config["mainSlides"] == closing + 1
    chapter_bar = re.search(r'<nav id="chapters".*?</nav>', page).group(0)  # type: ignore[union-attr]
    assert "Grundlagen" in chapter_bar and "Reserve" not in chapter_bar
    assert "Backup" not in chapter_bar
    assert all("data-chapter" not in s for s in slides[closing + 1 :])


def test_the_html_deck_without_backup_has_no_main_slides() -> None:
    output = io.BytesIO()
    HtmlDeckGenerator().generate(
        MarkdownDocument("# Deck\n\n## Folie\n\nText\n"), output, HtmlDeckOptions()
    )
    page = output.getvalue().decode("utf-8")
    config = re.search(r'data-config="([^"]*)"', page)
    assert config is not None and "mainSlides" not in json.loads(unescape(config.group(1)))


def test_check_counts_the_backup_apart() -> None:
    result = check(MarkdownDocument(DECK), DocumentFormat.PPTX)
    assert isinstance(result.stats, DeckStats)
    assert result.stats.backup == 4
    assert result.stats.chapters == 2
    assert result.stats.content == 3, "the agenda and two slides"
    assert result.stats.slides == 11
    assert ", 4 backup" in result.stats.lines()[0]
    plain = check(MarkdownDocument("# Deck\n\n## Folie\n\nText\n"), DocumentFormat.PPTX)
    assert isinstance(plain.stats, DeckStats)
    assert plain.stats.backup == 0 and "backup" not in plain.stats.lines()[0]


def test_the_backup_comes_back_from_the_deck() -> None:
    data, _ = make_deck()
    markdown = PptxConverter().convert(data).text
    assert "## Vielen Dank\n\n# Backup {.backup}\n\n## Reservefolie" in markdown
    assert markdown.count("{.backup}") == 1
    again, _ = make_deck(markdown)
    names = [name for _, name, _ in slide_texts(again)]
    assert names.count(design.BACKUP_SLIDE_NAME) == 1


def test_slides_after_the_closing_slide_come_back_as_backup() -> None:
    data, _ = make_deck("# Deck\n\n# Danke {.closing}\n\n## Nachtrag\n\nText\n")
    markdown = PptxConverter().convert(data).text
    assert "## Danke\n\n# Backup {.backup}\n\n## Nachtrag" in markdown


def test_backup_start() -> None:
    chapter, closing = design.LAYOUTS.chapter, design.LAYOUTS.closing
    assert design.backup_start([("a", ""), (chapter, "")]) is None
    assert design.backup_start([("a", ""), (closing, "")]) is None
    assert design.backup_start([("a", ""), (closing, ""), ("b", "")]) == 2
    assert design.backup_start([("a", ""), (chapter, "Backup"), ("b", "")]) == 1


# ---------------------------------------------------------------------- Word and PDF


def test_the_appendix_is_lettered_in_word() -> None:
    data, notes = make_report()
    assert notes == []
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        document = etree.fromstring(package.read("word/document.xml"))
        numbering = etree.fromstring(package.read("word/numbering.xml"))
    texts = {
        text_of(p): p
        for p in document.iter(w("p"))
        if text_of(p) in ("Einleitung", "Ziel", "Glossar", "Begriffe", "Tiefer", "Quellen")
    }
    assert texts["Einleitung"].find(f"{w('pPr')}/{w('numPr')}") is None
    levels = {}
    num_ids = set()
    for text in ("Glossar", "Begriffe", "Tiefer", "Quellen"):
        num_pr = texts[text].find(f"{w('pPr')}/{w('numPr')}")
        assert num_pr is not None, text
        levels[text] = num_pr.find(w("ilvl")).get(w("val"))  # type: ignore[union-attr]
        num_ids.add(num_pr.find(w("numId")).get(w("val")))  # type: ignore[union-attr]
    assert levels == {"Glossar": "0", "Begriffe": "1", "Tiefer": "2", "Quellen": "0"}
    (num_id,) = num_ids
    num = numbering.find(f"{w('num')}[@{w('numId')}='{num_id}']")
    assert num is not None
    abstract_id = num.find(w("abstractNumId")).get(w("val"))  # type: ignore[union-attr]
    abstract = numbering.find(f"{w('abstractNum')}[@{w('abstractNumId')}='{abstract_id}']")
    assert abstract is not None
    formats = [lvl.find(w("numFmt")).get(w("val")) for lvl in abstract.iterfind(w("lvl"))]  # type: ignore[union-attr]
    texts_of = [lvl.find(w("lvlText")).get(w("val")) for lvl in abstract.iterfind(w("lvl"))]  # type: ignore[union-attr]
    assert formats[:3] == ["upperLetter", "decimal", "decimal"]
    assert texts_of[:3] == ["%1", "%1.%2", "%1.%2.%3"]
    assert abstract.find(f"{w('lvl')}/{w('pStyle')}") is None, "not bound to the styles"
    nsids = [n.get(w("val")) for n in numbering.iter(w("nsid"))]
    assert len(nsids) == len(set(nsids)), "Word tells lists apart by their nsid"
    # The abstract numberings come before the instances (schema order).
    tags = [etree.QName(child).localname for child in numbering]
    assert tags.index("num") > max(i for i, t in enumerate(tags) if t == "abstractNum")


def test_the_word_agenda_leaves_out_the_appendix() -> None:
    markdown = "## Agenda {.agenda}\n\n# Eins\n\n# Zwei\n\n# Glossar {.appendix}\n\n# Quellen\n"
    data, _ = make_report(markdown)
    text = DocxConverter().convert(data).text
    agenda = text.split("# Eins")[0]
    assert "Zwei" in agenda and "Glossar" not in agenda and "Quellen" not in agenda


def test_the_appendix_comes_back_from_word() -> None:
    data, _ = make_report()
    markdown = DocxConverter().convert(data).text
    assert "# Glossar {.appendix}\n\n## Begriffe" in markdown
    assert markdown.count("{.appendix}") == 1
    assert "# Quellen\n" in markdown
    again, _ = make_report(markdown)
    assert DocxConverter().convert(again).text == markdown


def test_the_backup_is_ignored_in_word_and_pdf_with_a_note() -> None:
    markdown = "# Eins\n\nText\n\n# Backup {.backup}\n\nText\n"
    _, notes = make_report(markdown)
    assert notes == [NoteCodes.ATTRIBUTE_IGNORED]
    data, notes = make_pdf(markdown)
    assert notes == [NoteCodes.ATTRIBUTE_IGNORED]
    assert "2 Backup" in "\n".join(body_texts(data))


def test_the_pdf_letters_the_appendix() -> None:
    data, notes = make_pdf()
    assert notes == []
    text = "\n".join(body_texts(data))
    for line in (
        "1 Einleitung",
        "1.1 Ziel",
        "A Glossar",
        "A.1 Begriffe",
        "A.1.1 Tiefer",
        "B Quellen",
    ):
        assert line in text
    with pikepdf.open(io.BytesIO(data)) as pdf, pdf.open_outline() as outline:
        titles = [str(item.title) for item in outline.root]
    assert titles[-2:] == ["A Glossar", "B Quellen"]


def test_letters() -> None:
    assert [backup.letters(n) for n in (1, 2, 26, 27, 28)] == ["A", "B", "Z", "AA", "BB"]
    with pytest.raises(ValueError):
        backup.letters(0)


# ---------------------------------------------------------------------- mistakes


@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        (
            "# Deck\n\n# Backup {.backup}\n\n## A\n\n# Danke {.closing}\n",
            "Line 7: The closing slide {.closing} goes before the backup ({.backup} on line 3)",
        ),
        (
            "# Deck\n\n# Backup {.backup}\n\n# Mehr {.backup}\n",
            "Line 5: {.backup} is on line 3 already",
        ),
        (
            "# Eins {.appendix}\n\n# Zwei {.appendix}\n",
            "Line 3: {.appendix} is on line 1 already",
        ),
        ("# Deck\n\n## Folie {.backup}\n", "{.backup} goes on a '#' heading"),
        ("# Eins\n\n## Abschnitt {.appendix}\n", "{.appendix} goes on a '#' heading"),
        ("# Danke {.closing .backup}\n", "name .closing and .backup"),
        ("# Anhang {.appendix .internal}\n", "name .internal and .appendix"),
        (
            "# Deck\n\n::: panel\n# Backup {.backup}\n:::\n",
            "Line 4: {.backup} goes on a '#' heading of the document itself",
        ),
    ],
)
@pytest.mark.parametrize("format", [DocumentFormat.PPTX, DocumentFormat.DOCX, DocumentFormat.PDF])
def test_mistakes_raise_with_their_line_in_every_format(
    markdown: str, message: str, format: DocumentFormat
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        match format:
            case DocumentFormat.PPTX:
                make_deck(markdown)
            case DocumentFormat.DOCX:
                make_report(markdown)
            case _:
                make_pdf(markdown)
    assert message in error.value.reason
