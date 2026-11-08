"""E03-S03: slide-layout Markdown in Word, shown plainly in styles of its own."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from lxml import etree
from PIL import Image

from pta_documents.conversions.docx import DocxConverter
from pta_documents.design import colors, word
from pta_documents.design.variants import WordVariant
from pta_documents.generation.common.openxml import W, w
from pta_documents.markdown import DocumentResource
from tests.expected import assert_matches_expected
from tests.generation.docx.conftest import generate, open_docx, parts, style_name

SAMPLES = Path(__file__).parent / "samples"
LAYOUTS = (Path(__file__).parents[1] / "common" / "samples" / "layouts.md").read_text(
    encoding="utf-8"
)
FRONT = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
NS = {"w": W}
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
TEXT_WIDTH = (11906 - 2 * 1247) * 635
"""The text width of the portrait template in EMU."""


def layouts(variant: WordVariant = WordVariant.PORTRAIT) -> bytes:
    return generate(LAYOUTS.replace("---\n\n# ", f"vorlage: {variant.value}\n---\n\n# ", 1))


def body(data: bytes) -> etree._Element:
    return etree.fromstring(parts(data)["word/document.xml"])


def styles(data: bytes) -> etree._Element:
    return etree.fromstring(parts(data)["word/styles.xml"])


def style_element(data: bytes, name: str) -> etree._Element:
    found = styles(data).xpath(f"w:style[w:name/@w:val='{name}']", namespaces=NS)
    assert isinstance(found, list) and len(found) == 1, name
    element = found[0]
    assert isinstance(element, etree._Element)
    return element


def style_id(data: bytes, name: str) -> str:
    return str(style_element(data, name).get(w("styleId")))


def png(width: int = 600, height: int = 400) -> DocumentResource:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG", dpi=(96, 96))
    return DocumentResource("bild.png", "image/png", buffer.getvalue())


# ---------------------------------------------------------------------- the sample


@pytest.mark.parametrize(
    "variant", [WordVariant.PORTRAIT, WordVariant.LANDSCAPE], ids=lambda v: v.value
)
def test_the_sample_roundtrips(variant: WordVariant, review_dir: Path) -> None:
    data = layouts(variant)
    (review_dir / f"layouts-{variant.value}.docx").write_bytes(data)
    markdown = DocxConverter().convert(data).text
    assert_matches_expected(SAMPLES / f"layouts-{variant.value}.roundtrip.expected.md", markdown)


def test_each_block_lands_in_its_style() -> None:
    paragraphs = [(style_name(p), p.text) for p in open_docx(layouts()).paragraphs]
    expected = [
        # ::: cards: the ### and the figure are bold text, no heading 3.
        ("Standard fett", "Die Konfiguration ist zu kompliziert"),
        ("Standard fett", "26 Tabellen"),
        ("Standard fett", "Jedes Ergebnis hat ein Manifest"),
        # ::: statement: its first paragraph is bold.
        (
            "Standard fett",
            "Ein Broker garantiert die Zustellung mindestens einmal – nicht die "
            "Verarbeitung höchstens einmal.",
        ),
        ("Normal", "Der Wettlauf im alten System geschah mit einem Broker."),
        # ::: columns: one part after the other.
        ("Standard fett", "Heute"),
        ("Standard fett", "Mit Hafen"),
        (
            "Hinweis",
            "Hinweis: Der Fairness halber: Buchungen werden nach der Erfassung noch "
            "bearbeitet – daher Revisionen statt strenger Unveränderlichkeit.",
        ),
        ("Hinweis", "Kommentar: Ziel: 100\u00a0%"),  # typeset: non-breaking space
        (
            "Hinweis",
            "Fazit: Erst wenn der Schattenlauf vier Wochen lang gleiche Ergebnisse "
            "liefert, wird umgestellt.",
        ),
        (
            "Hinweis wichtig",
            "Wichtig: Dann ein Schattenlauf: Hafen berechnet dieselben "
            "Buchungen, und die Ergebnisse werden verglichen.",
        ),
        ("Normal", "Stand heute: im Plan, die Engine unter Beobachtung."),
    ]
    for item in expected:
        assert item in paragraphs, item
    assert "heading 3" not in {s for s, _ in paragraphs}
    # The line between two columns is left out.
    assert not body(layouts()).xpath("//w:pBdr/w:bottom", namespaces=NS)


def test_no_direct_font_size_or_colour_except_code() -> None:
    for r_pr in body(layouts()).iter(w("rPr")):
        assert r_pr.find(w("sz")) is None
        assert r_pr.find(w("color")) is None
        assert r_pr.find(w("shd")) is None
        assert r_pr.find(w("highlight")) is None
        fonts = r_pr.find(w("rFonts"))
        if fonts is not None:
            assert fonts.get(w("ascii")) == "Consolas"


def test_the_new_styles() -> None:
    data = layouts()
    for name, rule in (
        (word.STYLES.note, colors.PTA_BLUE),
        (word.STYLES.note_important, colors.YELLOW),
    ):
        element = style_element(data, name)
        based = element.find(w("basedOn"))
        assert based is not None and based.get(w("val")) == "Standard"
        left = element.find(f"{w('pPr')}/{w('pBdr')}/{w('left')}")
        assert left is not None
        assert (left.get(w("sz")), left.get(w("color"))) == ("24", rule)
        shading = element.find(f"{w('pPr')}/{w('shd')}")
        assert shading is not None and shading.get(w("fill")) == colors.GREY_LIGHT
    mark = style_element(data, word.STYLES.mark)
    assert mark.get(w("type")) == "character"
    shading = mark.find(f"{w('rPr')}/{w('shd')}")
    assert shading is not None and shading.get(w("fill")) == colors.YELLOW
    for category, name in (
        (colors.StatusCategory.SUCCESS, "Status Erfolg"),
        (colors.StatusCategory.WARNING, "Status Warnung"),
        (colors.StatusCategory.INFO, "Status Info"),
    ):
        element = style_element(data, name)
        assert element.find(f"{w('rPr')}/{w('b')}") is not None
        colour = element.find(f"{w('rPr')}/{w('color')}")
        assert colour is not None and colour.get(w("val")) == colors.STATUS_COLORS[category]


def test_marks_and_coloured_words_use_character_styles() -> None:
    data = layouts()
    root = body(data)

    def styled(name: str) -> list[str]:
        found = root.xpath(
            f"//w:r[w:rPr/w:rStyle/@w:val='{style_id(data, name)}']/w:t/text()", namespaces=NS
        )
        assert isinstance(found, list)
        return [str(t) for t in found]

    assert "Hervorhebungsfarbe" in styled(word.STYLES.mark)
    assert "im Plan" in styled("Status Erfolg")
    assert "unter Beobachtung" in styled("Status Warnung")


def test_a_marked_row_is_shaded_and_labels_take_their_status_style() -> None:
    data = layouts()
    tables = open_docx(data).tables
    model = next(t for t in tables if t.cell(0, 0).text == "Status")
    fills = [
        [
            shading.get(w("fill"))
            for shading in row._tr.iter(w("shd"))  # pyright: ignore[reportUnknownMemberType]
        ]
        for row in model.rows
    ]
    assert fills == [[], [], [colors.YELLOW] * 2, [], [colors.YELLOW] * 2]
    status = next(t for t in tables if t.cell(0, 0).text == "Teil")
    done = status.cell(1, 1).paragraphs[0]._p
    r_pr = done.find(f"{w('r')}/{w('rPr')}")
    assert r_pr is not None
    style = r_pr.find(w("rStyle"))
    assert style is not None and style.get(w("val")) == style_id(data, "Status Erfolg")
    assert r_pr.find(w("rFonts")) is None
    # A code cell assigned to no category stays code.
    system = model.cell(1, 1).paragraphs[0]._p.find(f"{w('r')}/{w('rPr')}/{w('rFonts')}")
    assert system is not None and system.get(w("ascii")) == "Consolas"


def test_english_alert_words() -> None:
    markdown = (
        "---\nvorlage: hoch-ohne-deckblatt\nsprache: en\n---\n"
        + "".join(
            f"> [!{kind}]\n> Text\n\n"
            for kind in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
        )
        + "::: conclusion\nEnde\n:::\n"
    )
    found = [(style_name(p), p.text) for p in open_docx(generate(markdown)).paragraphs]
    assert found == [
        ("Hinweis", "Note: Text"),
        ("Hinweis", "Tip: Text"),
        ("Hinweis wichtig", "Important: Text"),
        ("Hinweis wichtig", "Warning: Text"),
        ("Hinweis wichtig", "Caution: Text"),
        ("Hinweis", "Conclusion: Ende"),
    ]


def test_an_alert_of_several_blocks_starts_with_its_word_once() -> None:
    markdown = FRONT + "> [!TIP]\n> Eins\n>\n> Zwei\n>\n> - Punkt\n"
    found = [(style_name(p), p.text) for p in open_docx(generate(markdown)).paragraphs]
    assert found == [("Hinweis", "Tipp: Eins"), ("Hinweis", "Zwei"), ("List Bullet", "Punkt")]


# ---------------------------------------------------------------------- image rows


@pytest.mark.parametrize(("count", "rows", "columns"), [(2, 1, 2), (5, 2, 4)])
def test_an_image_row_is_a_table_without_rules(
    count: int, rows: int, columns: int, review_dir: Path
) -> None:
    images = " ".join(f"![Bild {n}](bild.png)" for n in range(1, count + 1))
    data = generate(FRONT + f"Davor.\n\n{images}\n", resources=(png(1600, 900),))
    (review_dir / f"bildreihe-{count}.docx").write_bytes(data)
    table = open_docx(data).tables[0]
    assert (len(table.rows), len(table.columns)) == (rows, columns)
    style = table._tbl.tblPr.find(w("tblStyle"))
    assert style is not None and style.get(w("val")) == style_id(data, word.STYLES.picture_row)
    borders = style_element(data, word.STYLES.picture_row).find(f"{w('tblPr')}/{w('tblBorders')}")
    assert borders is not None and {b.get(w("val")) for b in borders} == {"nil"}
    captions = [
        p.text
        for row in table.rows
        for cell in row.cells
        for p in cell.paragraphs
        if style_name(p) == "caption"
    ]
    assert captions == [f"Abbildung {n}: Bild {n}" for n in range(1, count + 1)]
    cell_width = TEXT_WIDTH // columns
    for extent in body(data).iter(f"{{{WP}}}extent"):
        assert int(extent.get("cx", "0")) <= cell_width
    for row in table.rows:
        assert row._tr.find(f"{w('trPr')}/{w('cantSplit')}") is not None
    # The table keeps its rows together: every paragraph but those of the last row keeps with
    # the next.
    for row in table.rows[:-1]:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                assert paragraph.paragraph_format.keep_with_next


def test_one_image_stays_a_figure() -> None:
    data = generate(FRONT + "![Bild](bild.png)\n", resources=(png(),))
    assert open_docx(data).tables == []


def test_an_image_row_roundtrips_as_one_paragraph() -> None:
    data = generate(FRONT + "![A](bild.png) ![B](bild.png)\n", resources=(png(),))
    markdown = DocxConverter().convert(data).text
    assert re.search(r"!\[A\]\(\S+\) !\[B\]\(\S+\)\n\nAbbildung 1: A\n\nAbbildung 2: B\n", markdown)


# ---------------------------------------------------------------------- slide kinds


def test_slide_kinds_are_shown_plainly() -> None:
    markdown = FRONT + (
        "# Bericht\n\n## Agenda {.agenda}\n\n# Lage\n\n## Es geht ohne Ausfall {.interim}\n\n"
        "## Wer misst, misst Mist {.quote}\n\n— Unbekannt\n\n# Ziel\n\n"
        "## Kontakt {.contact}\n\n### Erika Mustermann\n\n![Erika](bild.png)\nBeraterin\n"
        "erika@pta.de\n\n# Danke {.closing}\n"
    )
    data = generate(markdown, resources=(png(1200, 1200),))
    found = [(style_name(p), p.text) for p in open_docx(data).paragraphs]
    assert found == [
        ("heading 1", "Bericht"),
        ("heading 2", "Agenda"),
        # Without a list of its own, the agenda lists the chapters after it.
        ("List Paragraph", "Lage"),
        ("List Paragraph", "Ziel"),
        ("heading 1", "Lage"),
        ("Standard fett", "Es geht ohne Ausfall"),
        ("Zitat", "Wer misst, misst Mist"),
        ("Zitat", "— Unbekannt"),
        ("heading 1", "Ziel"),
        ("heading 2", "Kontakt"),
        ("Standard fett", "Erika Mustermann"),
        ("Normal", "\nBeraterin\nerika@pta.de"),
        ("heading 1", "Danke"),
    ]
    extent = next(body(data).iter(f"{{{WP}}}extent"))
    assert int(extent.get("cx", "0")) <= word.CONTACT_PHOTO_CM * 360000
    # The photo of a contact has no caption.
    assert "Abbildung" not in "".join(t for _, t in found)
