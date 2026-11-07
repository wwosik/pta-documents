"""E08-S01: notes from the PPTX generator (port of GenerationNoteTests.cs in vt-tools-libs)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from pta_documents import GenerationResult, NoteCodes
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from tests.generation.pptx.conftest import open_pptx, texts

REPO = Path(__file__).resolve().parents[3]


def run(markdown: str, resources: tuple[DocumentResource, ...] = ()) -> GenerationResult:
    return PptxGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO())


def png(name: str, width: int, height: int) -> DocumentResource:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG")
    return DocumentResource(name, "image/png", buffer.getvalue())


def test_the_result_counts_the_slides() -> None:
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument("# Deck\n\n## A\n\nText\n"), output)
    assert result.slides == len(open_pptx(output.getvalue()).slides) == 2
    assert result.pages is None
    assert result.notes == ()
    assert str(result) == "No notes.\n"


def test_a_slide_that_does_not_fit_is_noted_as_split_at_its_heading() -> None:
    bullets = "\n".join(f"- Point {i} with a few more words to fill the line" for i in range(40))
    result = run(f"---\ntitel: Lang\n---\n\n# Deck\n\n## Many points\n\n{bullets}\n")
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.SLIDE_SPLIT, 7)
    assert '"Many points"' in note.message
    assert "continues on 1 more" in note.message


def test_a_long_table_and_long_code_are_noted_as_split() -> None:
    rows = "\n".join(f"| {i} | Wert |" for i in range(30))
    code = "\n".join(f"line {i}" for i in range(60))
    result = run(
        f"# D\n\n## Tabelle\n\n| A | B |\n| - | - |\n{rows}\n\n## Code\n\n```\n{code}\n```\n"
    )
    assert [(n.code, n.line) for n in result.notes] == [
        (NoteCodes.SLIDE_SPLIT, 3),
        (NoteCodes.SLIDE_SPLIT, 38),
    ]


def test_a_paragraph_too_long_for_any_slide_is_noted_as_overfull() -> None:
    words = " ".join(["word"] * 1200)
    result = run(f"# Deck\n\n## Wall of text\n\n{words}\n")
    assert [(n.code, n.line) for n in result.notes] == [(NoteCodes.SLIDE_OVERFULL, 3)]
    assert "12 pt" in result.notes[0].message


def test_raw_html_is_left_out_and_noted_but_comments_and_line_breaks_are_not() -> None:
    markdown = (
        '# Deck\n\n## Slide\n\n<div class="x">Hi</div>\n\n<!-- a comment -->\n\n'
        "Text with <b>bold</b> and<br>a break <!-- note -->\n"
    )
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    assert [(n.code, n.line) for n in result.notes] == [
        (NoteCodes.RAW_HTML, 5),
        (NoteCodes.RAW_HTML, 9),
    ]
    assert str(result) == (
        "- line 5: Raw HTML is left out of the deck. Write it in Markdown, or leave it out.\n"
        "- line 9: Raw HTML is left out of the deck. Write it in Markdown, or leave it out.\n"
    )
    slide = open_pptx(output.getvalue()).slides[1]
    text = "\n".join(texts(slide).values())
    assert "<" not in text
    assert "Hi" not in text
    assert "Text with bold and\x0ba break" in text  # <br> is a line break (vertical tab)


def test_inline_html_on_a_later_line_of_a_paragraph_has_that_line() -> None:
    result = run("# Deck\n\n## Slide\n\nFirst line\nsecond <span>line</span>\n")
    assert [(n.code, n.line) for n in result.notes] == [(NoteCodes.RAW_HTML, 6)]


def test_a_diagram_block_without_renderer_is_noted_other_code_is_not() -> None:
    result = run(
        "---\ntitel: D\n---\n# Deck\n\n## Flow\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "```python\nx = 1\n```\n"
    )
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.CODE_NOT_DRAWN, 8)
    assert "`mermaid`" in note.message


def test_a_small_image_blown_up_is_noted_as_enlarged() -> None:
    small = png("images/klein.png", 200, 100)
    result = run("# Deck\n\n## Bilder\n\n![A](images/klein.png) ![B](images/klein.png)\n", (small,))
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.IMAGE_ENLARGED, 5)
    assert "'images/klein.png' is shown at" in note.message
    big = png("images/gross.png", 2000, 1000)
    assert (
        run("# Deck\n\n## Bilder\n\n![A](images/gross.png) ![B](images/gross.png)\n", (big,)).notes
        == ()
    )


def test_an_image_the_placeholder_crops_heavily_is_noted() -> None:
    wide = png("images/breit.png", 4000, 500)
    result = run("# Deck\n\n## Bild\n\nText daneben.\n\n![Breit](images/breit.png)\n", (wide,))
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.IMAGE_CROPPED, 7)
    assert "'Titel und Bild 01'" in note.message
    fitting = png("images/passend.png", 2280, 2000)
    assert (
        run("# Deck\n\n## Bild\n\nText daneben.\n\n![P](images/passend.png)\n", (fitting,)).notes
        == ()
    )


def test_the_same_note_twice_on_one_line_is_kept_once() -> None:
    result = run("# Deck\n\n## Slide\n\n<b>a</b> <i>b</i>\n")
    assert len(result.notes) == 1


def test_the_samples_generate_without_notes() -> None:
    for folder in ("gsb", "funktionen"):
        root = REPO / "samples" / folder
        images = tuple(
            DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
            for p in sorted((root / "images").glob("*"))
        )
        for source in sorted(root.glob("*-praesentation.md")) + sorted(root.glob("*-folien.md")):
            result = run(source.read_text(encoding="utf-8"), images)
            assert result.notes == (), f"{source.name}:\n{result}"
