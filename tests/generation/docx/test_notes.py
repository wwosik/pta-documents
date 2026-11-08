"""E08-S01: notes from the DOCX generator."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from pta_documents import GenerationResult, NoteCodes
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from tests.generation.docx.conftest import open_docx

REPO = Path(__file__).resolve().parents[3]
FRONT = "---\nvorlage: hoch-ohne-deckblatt\n---\n"
"""Three lines of front matter before the body."""


def run(markdown: str, resources: tuple[DocumentResource, ...] = ()) -> GenerationResult:
    return DocxGenerator().generate(MarkdownDocument(markdown, resources), io.BytesIO())


def png(name: str, width: int, height: int, dpi: int = 96) -> DocumentResource:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 111, 185)).save(buffer, "PNG", dpi=(dpi, dpi))
    return DocumentResource(name, "image/png", buffer.getvalue())


def test_a_plain_document_has_no_notes_and_no_counts() -> None:
    result = run(FRONT + "# Kapitel\n\nText.\n")
    assert result == GenerationResult()
    assert str(result) == "No notes.\n"


def test_raw_html_is_left_out_and_noted_with_its_line() -> None:
    markdown = FRONT + (
        "# Kapitel\n\n<div>\nBlock\n</div>\n\n<!-- Kommentar -->\n\n"
        "Text mit <b>fett</b> und<br>Umbruch.\n"
    )
    output = io.BytesIO()
    result = DocxGenerator().generate(MarkdownDocument(markdown), output)
    assert [(n.code, n.line) for n in result.notes] == [
        (NoteCodes.RAW_HTML, 6),
        (NoteCodes.RAW_HTML, 12),
    ]
    assert "left out of the document" in result.notes[0].message
    text = "\n".join(p.text for p in open_docx(output.getvalue()).paragraphs)
    assert "<" not in text
    assert "Block" not in text
    assert "Text mit fett und\nUmbruch." in text


def test_html_in_tables_lists_and_footnotes_is_noted() -> None:
    markdown = FRONT + (
        "| A | B |\n| - | - |\n| <span>x</span> | y<br>z |\n\n- Punkt <em>x</em>\n\n"
        "Fußnote[^1]\n\n[^1]: Mit <u>HTML</u>.\n"
    )
    assert [(n.code, n.line) for n in run(markdown).notes] == [
        (NoteCodes.RAW_HTML, 6),
        (NoteCodes.RAW_HTML, 8),
        (NoteCodes.RAW_HTML, 12),
    ]


def test_a_diagram_block_is_noted_as_not_drawn() -> None:
    result = run(FRONT + "# K\n\n```mermaid\ngraph TD\n```\n\n```json\n{}\n```\n")
    assert [(n.code, n.line) for n in result.notes] == [(NoteCodes.CODE_NOT_DRAWN, 6)]
    assert "`mermaid`" in result.notes[0].message


def test_an_image_far_below_96_dpi_is_noted_as_enlarged() -> None:
    blurry = png("images/a.png", 100, 50, dpi=24)
    sharp = png("images/b.png", 200, 100, dpi=72)
    result = run(FRONT + "# K\n\n![A](images/a.png)\n\nText ![B](images/b.png)\n", (blurry, sharp))
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.IMAGE_ENLARGED, 6)
    assert "'images/a.png' is shown at 4.0 times its size" in note.message


def test_the_samples_generate_without_notes() -> None:
    for folder in ("gsb", "funktionen"):
        root = REPO / "samples" / folder
        images = tuple(
            DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
            for p in sorted((root / "images").glob("*"))
        )
        for source in sorted(root.glob("*-bericht.md")) + sorted(root.glob("*-dokument.md")):
            result = run(source.read_text(encoding="utf-8"), images)
            assert result.notes == (), f"{source.name}:\n{result}"


def test_speaker_notes_are_left_out_with_a_note() -> None:
    """E09-S01: ``::: notes`` belong to slides; Word drops them, without an error."""
    markdown = FRONT + "# Kapitel\n\nText.\n\n::: notes\nNur für den **Vortrag**.\n\n- Punkt\n:::\n"
    output = io.BytesIO()
    result = DocxGenerator().generate(MarkdownDocument(markdown), output)
    assert result.codes() == [NoteCodes.NOTES_DROPPED]
    assert result.notes[0].line == 8
    text = "\n".join(p.text for p in open_docx(output.getvalue()).paragraphs)
    assert "Vortrag" not in text and "Punkt" not in text and "Text." in text
