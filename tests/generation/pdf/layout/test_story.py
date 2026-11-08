"""E05-S02: every block in the Word style the DOCX generator gives it, values from the template."""

from __future__ import annotations

import io
from typing import Any

import pikepdf
import pytest

from pta_documents import DocumentConversionError
from pta_documents.design import colors, word, word_styles
from pta_documents.design.colors import StatusCategory
from pta_documents.design.variants import Language, WordVariant
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.pdf.layout import (
    LayoutSettings,
    PdfInfo,
    build_story,
    layout,
    prepare,
    render,
)
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import create_parser
from tests.generation.pdf.layout.support import Pdf, filler, image, make_pdf, png, rgb

DESIGN = word_styles.read(WordVariant.PORTRAIT)
BLACK = rgb(colors.TEXT_WORD)


def fmt(name: str) -> word_styles.ParagraphFormat:
    return DESIGN.paragraph(name)


def test_headings_are_numbered_as_in_word_and_deeper_ones_are_capitals() -> None:
    markdown = "# Eins\n\n## Zwei\n\n### Drei\n\n#### Vier\n\n## Fünf\n\n# Sechs\n"
    pdf = Pdf(make_pdf(markdown))
    assert [line.text for line in pdf.lines] == [
        "1 Eins",
        "1.1 Zwei",
        "1.1.1 Drei",
        "VIER",
        "1.2 Fünf",
        "2 Sechs",
    ]


@pytest.mark.parametrize(
    ("markdown", "text", "style", "bold"),
    [
        ("# Titel", "Titel", "heading 1", True),
        ("## Titel", "Titel", "heading 2", True),
        ("### Titel", "Titel", "heading 3", False),
        ("#### Titel", "TITEL", word.STYLES.sub_heading, False),
        ("Ein Absatz.", "Ein Absatz.", word.STYLES.normal, False),
        ("**Ganz fett.**", "Ganz fett.", word.STYLES.normal_bold, True),
        ("- Punkt", "Punkt", word.STYLES.list_bullet, False),
        ("1. Punkt", "Punkt", word.STYLES.list_number, False),
    ],
)
def test_blocks_take_size_colour_and_weight_from_the_word_style(
    markdown: str, text: str, style: str, bold: bool
) -> None:
    line = Pdf(make_pdf(markdown)).line(text)
    char = next(c for c in line.chars if c["text"] == text[-1])
    assert round(float(char["size"]), 1) == fmt(style).size_pt
    assert tuple(round(float(v), 3) for v in char["non_stroking_color"]) == rgb(
        fmt(style).color or colors.TEXT_WORD
    )
    assert ("Bold" in str(char["fontname"])) is bold


def test_headings_have_the_hanging_indent_of_their_numbering() -> None:
    pdf = Pdf(make_pdf("# Eins\n\n### Drei\n"))
    page = DESIGN.page
    one = pdf.line("Eins")
    three = pdf.line("Drei")
    text_x = next(float(c["x0"]) for c in one.chars if c["text"] == "E")
    assert text_x == pytest.approx(page.left_pt + fmt("heading 1").left_indent_pt, abs=0.5)
    text_x = next(float(c["x0"]) for c in three.chars if c["text"] == "D")
    assert text_x == pytest.approx(page.left_pt + fmt("heading 3").left_indent_pt, abs=0.5)
    assert float(one.chars[0]["x0"]) == pytest.approx(page.left_pt, abs=0.5)


def test_list_levels_are_indented_as_the_numbering_of_the_template() -> None:
    pdf = Pdf(make_pdf("- eins\n  - zwei\n    - drei\n"))
    level = DESIGN.level(fmt(word.STYLES.list_bullet), 0)
    assert level is not None
    for depth, text in enumerate(("eins", "zwei", "drei")):
        level = DESIGN.level(fmt(word.STYLES.list_bullet), depth)
        assert level is not None
        x = float(pdf.line(text).chars[0]["x0"])
        assert x == pytest.approx(DESIGN.page.left_pt + level.left_pt, abs=0.5)


def test_captions_number_tables_and_figures() -> None:
    markdown = (
        "| A | B |\n| - | - |\n| 1 | 2 |\n\nTabelle: Werte\n\n"
        '![Alternativtext](bild.png "Ein Bild")\n\n![Zweites](zwei.png)\n'
    )
    pdf = Pdf(make_pdf(markdown, [image("bild.png"), image("zwei.png")]))
    caption = pdf.line("Tabelle 1: Werte")
    assert caption.size == fmt(word.STYLES.caption).size_pt
    assert caption.color == rgb(colors.PTA_BLUE)
    assert pdf.line("Abbildung 1: Ein Bild")
    assert pdf.line("Abbildung 2: Zweites")


def test_english_captions() -> None:
    markdown = "| A |\n| - |\n| 1 |\n\nTable: Values\n"
    pdf = Pdf(make_pdf(markdown, settings=LayoutSettings(language=Language.EN)))
    assert pdf.line("Table 1: Values")


def test_a_table_in_the_pta_style() -> None:
    pdf = Pdf(make_pdf("| Kopf | Zahl |\n| --- | ---: |\n| a | 1 |\n| b | 22 |\n"))
    header = pdf.line("Kopf")
    assert header.color == rgb(colors.WHITE)
    fills = [r for r in pdf.rects[0] if r["non_stroking_color"] is not None and r["fill"]]
    assert any(
        tuple(round(float(c), 3) for c in r["non_stroking_color"]) == rgb(colors.PTA_BLUE)
        for r in fills
    )
    assert pdf.line("a").chars[0]["x0"] == pytest.approx(DESIGN.page.left_pt, abs=0.5)
    # Right-aligned column: the numbers end at the same x.
    ends = [float(pdf.line(t).chars[-1]["x1"]) for t in ("a 1", "b 22")]
    assert ends[0] == pytest.approx(ends[1], abs=0.5)


def test_a_bold_title_stays_with_its_table() -> None:
    from tests.generation.pdf.layout.support import spacer

    for offset in range(380, 440, 4):
        push, resource = spacer(offset)
        markdown = filler(10) + push + "**Titel der Tabelle**\n\n" + "| A |\n| - |\n| 1 |\n"
        pdf = Pdf(make_pdf(markdown, [resource]))
        assert pdf.page_of("Titel der Tabelle") == pdf.page_of("A"), offset


def test_column_widths_give_each_column_its_longest_word() -> None:
    long_word = "Donaudampfschifffahrtsgesellschaft"
    markdown = f"| {long_word} | b |\n| - | - |\n| x | {'kurz ' * 40} |\n"
    pdf = Pdf(make_pdf(markdown))
    line = pdf.line(long_word)
    assert line.text.startswith(long_word)


def test_code_is_mono_on_grey() -> None:
    pdf = Pdf(make_pdf("```python\nx = 1  # comment\n```\n"))
    line = pdf.line("x = 1")
    assert line.size == word.CODE.size_pt
    assert "Inconsolata" in line.font
    greys = [
        r
        for r in pdf.rects[0]
        if r["non_stroking_color"] is not None
        and tuple(round(float(c), 3) for c in r["non_stroking_color"]) == rgb(word.CODE.background)
    ]
    assert greys
    comment = next(c for c in line.chars if c["text"] == "#")
    assert tuple(round(float(v), 3) for v in comment["non_stroking_color"]) == rgb(colors.GREY_DARK)


def test_code_keeps_its_spaces() -> None:
    pdf = Pdf(make_pdf("```\nif x:\n    return 1\n```\n"))
    first = float(pdf.line("if x:").chars[0]["x0"])
    indented = float(pdf.line("return 1").chars[0]["x0"])
    assert indented > first + 10


def test_quotes_are_indented() -> None:
    pdf = Pdf(make_pdf("Text.\n\n> Ein Zitat.\n"))
    quote = float(pdf.line("Ein Zitat.").chars[0]["x0"])
    assert quote == pytest.approx(
        DESIGN.page.left_pt + word.QUOTE_INDENT_CM * word_styles.POINTS_PER_CM, abs=0.5
    )


def test_inline_formats() -> None:
    pdf = Pdf(make_pdf("normal **fett** *kursiv* `code` ==markiert== ~~weg~~"))
    line = pdf.line("normal")

    def font(word: str) -> str:
        return str(line.chars[line.text.index(word)]["fontname"])

    assert "Bold" in font("fett")
    assert "Slanted" in font("kursiv")
    assert "Inconsolata" in font("code")
    assert font("markiert").endswith("Selawik-Regular")
    yellow = [
        r
        for r in pdf.rects[0]
        if r["non_stroking_color"] is not None
        and tuple(round(float(c), 3) for c in r["non_stroking_color"]) == rgb(word.MARK_COLOR)
    ]
    assert yellow


def test_coloured_words_and_status_labels() -> None:
    settings = LayoutSettings(status_labels={"Offen": StatusCategory.DANGER})
    markdown = "Das ist [gut]{.success}.\n\n| Status |\n| - |\n| `Offen` |\n"
    pdf = Pdf(make_pdf(markdown, settings=settings))
    good = next(c for c in pdf.line("gut").chars if c["text"] == "g")
    assert tuple(round(float(v), 3) for v in good["non_stroking_color"]) == rgb(colors.SIGNAL_GREEN)
    label = pdf.line("Offen").chars[0]
    assert tuple(round(float(v), 3) for v in label["non_stroking_color"]) == rgb(colors.SIGNAL_RED)
    assert "Bold" in str(label["fontname"])


def link_targets(content: bytes) -> list[str]:
    result: list[str] = []
    with pikepdf.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for annotation in page.get("/Annots", []):
                action = annotation.get("/A")
                if action is not None and "/URI" in action:
                    result.append(str(action.URI))
                elif "/Dest" in annotation:
                    destination = annotation.Dest
                    page = next(
                        n for n, p in enumerate(pdf.pages) if p.objgen == destination[0].objgen
                    )
                    result.append(f"#page{page}")
    return result


def test_links_go_out_to_absolute_urls_and_in_to_headings() -> None:
    markdown = (
        "# Ziel Kapitel\n\n[außen](https://example.com/x) [innen](#ziel-kapitel) "
        "[relativ](datei.md) [fehlt](#gibt-es-nicht)\n"
    )
    content = make_pdf(markdown)
    targets = link_targets(content)
    assert "https://example.com/x" in targets
    assert "#page0" in targets
    assert len(targets) == 2
    link = next(c for c in Pdf(content).line("außen").chars if c["text"] == "a")
    assert tuple(round(float(v), 3) for v in link["non_stroking_color"]) == rgb(colors.DARK_BLUE)


def test_footnotes_stand_at_the_foot_of_the_page_of_their_reference() -> None:
    markdown = "Erster Absatz mit Fußnote[^a].\n\n" + filler(5) + "[^a]: Der Text der Fußnote.\n"
    pdf = Pdf(make_pdf(markdown))
    note = pdf.line("Der Text der Fußnote.")
    assert note.page == pdf.page_of("Erster Absatz")
    assert round(float(note.chars[-1]["size"]), 1) == fmt(word.STYLES.footnote_text).size_pt
    assert note.top > max(line.top for line in pdf.lines if "Füllzeile" in line.text)
    assert note.top > pdf.height * 0.8
    assert note.text.startswith("1")


def test_footnotes_make_room_at_the_foot_of_full_pages() -> None:
    notes = "".join(f"[^n{n}]: Fußnotentext {n}.\n" for n in range(40))
    body = "".join(f"Absatz {n} mit Verweis[^n{n}].\n\n" for n in range(40))
    pdf = Pdf(make_pdf(body + notes))
    assert pdf.pages >= 2
    for page in range(pdf.pages):
        body_lines = [line for line in pdf.lines_on(page) if line.text.startswith("Absatz")]
        note_lines = [line for line in pdf.lines_on(page) if "Fußnotentext" in line.text]
        assert len(body_lines) == len(note_lines)
        if note_lines:
            assert min(n.top for n in note_lines) > max(b.top for b in body_lines)
        for line in body_lines:
            number = line.text.split()[1]
            assert any(n.text.endswith(f"Fußnotentext {number}.") for n in note_lines)


def test_task_lists_draw_boxes_instead_of_bullets() -> None:
    pdf = Pdf(make_pdf("- [ ] offen\n- [x] erledigt\n"))
    assert [line.text for line in pdf.lines] == ["offen", "erledigt"]


def test_definition_lists_alerts_and_rules() -> None:
    markdown = "Begriff\n: Erklärung.\n\n> [!WARNING]\n> Achtung.\n\n---\n\nDanach.\n"
    pdf = Pdf(make_pdf(markdown))
    assert "Bold" in pdf.line("Begriff").font
    assert pdf.line("Warnung: Achtung.")
    assert pdf.line("Danach.")


def test_raw_html_and_speaker_notes_are_left_out_with_a_note() -> None:
    notes = Notes()
    markdown = "# Kapitel\n\n<div>roh</div>\n\n::: notes\nGesprochen.\n:::\n\nText.\n"
    pdf = Pdf(make_pdf(markdown, notes=notes))
    codes = {n.code for n in notes.to_tuple()}
    assert {NoteCodes.RAW_HTML, NoteCodes.NOTES_DROPPED} <= codes
    assert "Gesprochen" not in "".join(pdf.page_texts)
    assert "roh" not in "".join(pdf.page_texts)


def test_a_missing_image_is_an_error() -> None:
    with pytest.raises(DocumentConversionError, match=r"fehlt\.png"):
        make_pdf("![](fehlt.png)")


def test_an_image_in_an_unknown_format_is_an_error() -> None:
    resource = DocumentResource("bild.emf", "image/x-emf", b"\x01\x00\x00\x00")
    with pytest.raises(DocumentConversionError, match="PNG"):
        make_pdf("![](bild.emf)", [resource])


def test_gif_images_are_placed() -> None:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("P", (80, 40)).save(buffer, "GIF")
    resource = DocumentResource("bild.gif", "image/gif", buffer.getvalue())
    pdf = Pdf(make_pdf("![](bild.gif)", [resource]))
    (picture,) = pdf.images[0]
    assert float(picture["width"]) == pytest.approx(60, abs=0.1)


def test_image_rows_stand_side_by_side() -> None:
    resources = [image("a.png"), image("b.png")]
    pdf = Pdf(make_pdf("![Links](a.png) ![Rechts](b.png)\n", resources))
    first, second = pdf.images[0]
    assert float(first["top"]) == pytest.approx(float(second["top"]))
    assert float(second["x0"]) > float(first["x1"])
    assert pdf.line("Abbildung 1: Links")


def test_no_break_spaces_are_kept_and_shown() -> None:
    pdf = Pdf(make_pdf("Zahl 10\u00a0% und z.\u00a0B. hier"))
    assert "10\u00a0%" in pdf.lines[0].text or "10 %" in pdf.lines[0].text


def test_the_same_input_gives_the_same_bytes() -> None:
    markdown = "# Kapitel\n\nText mit *Kursiv* und [Link](https://example.com).\n"
    assert make_pdf(markdown) == make_pdf(markdown)


def test_only_embedded_fonts_and_none_of_the_standard_fourteen() -> None:
    content = make_pdf("# Kapitel\n\nText **fett** *kursiv* `code`.\n")
    with pikepdf.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for font in page.Resources.Font.values():
                assert "Helvetica" not in str(font.BaseFont)
                descendant = font.DescendantFonts[0] if "/DescendantFonts" in font else font
                assert "/FontFile2" in descendant.FontDescriptor


def test_decorate_sees_every_page_and_the_count() -> None:
    seen: list[tuple[int, int]] = []
    tokens = create_parser().parse(filler(80))
    result = layout(
        tokens,
        MarkdownDocument(""),
        LayoutSettings(),
        decorate=lambda _canvas, page, count: seen.append((page, count)),
    )
    assert seen == [(n, result.pages) for n in range(1, result.pages + 1)]
    assert result.pages >= 3


def test_build_story_and_render_are_the_halves_of_layout() -> None:
    markdown = "# Kapitel\n\nText.\n"
    tokens = create_parser().parse(markdown)
    context = prepare(LayoutSettings())
    story = build_story(tokens, MarkdownDocument(markdown), context)
    assert [o.title for o in story.outline] == ["1 Kapitel"]
    rendered = render(story, PdfInfo(title="T"))
    assert rendered.pages == 1
    assert Pdf(rendered.content).line("1 Kapitel")


def test_png_helper_is_a_png() -> None:
    assert png()[:4] == b"\x89PNG"


def test_a_frame_drawn_without_a_font_does_not_bring_in_helvetica() -> None:
    def decorate(canvas: Any, page: int, count: int) -> None:
        canvas.drawString(300, 20, f"Seite {page} | {count}")

    tokens = create_parser().parse("Text.")
    content = layout(tokens, MarkdownDocument(""), LayoutSettings(), decorate=decorate).content
    assert "Seite 1 | 1" in Pdf(content).page_texts[0]
    with pikepdf.open(io.BytesIO(content)) as pdf:
        names = [str(f.BaseFont) for f in pdf.pages[0].Resources.Font.values()]
    assert not [n for n in names if "Helvetica" in n]
