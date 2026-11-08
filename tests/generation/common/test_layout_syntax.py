"""E02-S02: the slide-layout syntax is read and checked alike by DOCX and PPTX.

Ports of DocLibs ``SlideLayoutTests.Mistakes_Throw``, ``LabelMistakes_Throw``,
``Braces_ThatAreNoAttributes_StayInTheTitle``, ``ColouredWordsTests`` and
``SlideLayoutSyntaxTests.Mistakes_Throw_LikeInDecks`` — each for DOCX and PPTX, and since
E05-S04 for PDF.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pta_documents.design.variants import WordVariant
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.result import GenerationResult
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import MarkdownDocument
from tests.generation.docx.conftest import open_docx
from tests.generation.pdf.support import body_texts
from tests.generation.pptx.conftest import open_pptx

SAMPLES = Path(__file__).parent / "samples"
LAYOUTS = (SAMPLES / "layouts.md").read_text(encoding="utf-8")

Generate = Callable[[str], tuple[GenerationResult, bytes]]


def generate_docx(markdown: str) -> tuple[GenerationResult, bytes]:
    output = io.BytesIO()
    options = DocxOptions(variant=WordVariant.PORTRAIT_NO_COVER)
    result = DocxGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, output.getvalue()


def generate_pptx(markdown: str) -> tuple[GenerationResult, bytes]:
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    return result, output.getvalue()


def generate_pdf(markdown: str) -> tuple[GenerationResult, bytes]:
    output = io.BytesIO()
    options = PdfOptions(variant=WordVariant.PORTRAIT_NO_COVER, system_fonts=False)
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, output.getvalue()


OFFICE = pytest.mark.parametrize(
    ("generate", "format"),
    [(generate_docx, DocumentFormat.DOCX), (generate_pptx, DocumentFormat.PPTX)],
    ids=["docx", "pptx"],
)
GENERATORS = pytest.mark.parametrize(
    ("generate", "format"),
    [
        (generate_docx, DocumentFormat.DOCX),
        (generate_pptx, DocumentFormat.PPTX),
        (generate_pdf, DocumentFormat.PDF),
    ],
    ids=["docx", "pptx", "pdf"],
)


def docx_paragraphs(data: bytes) -> list[str]:
    return [p.text for p in open_docx(data).paragraphs]


def pptx_runs(data: bytes) -> list[tuple[str, bool]]:
    """Text and boldness of every run on every slide."""
    result: list[tuple[str, bool]] = []
    for slide in open_pptx(data).slides:
        for shape in slide.shapes:
            any_shape: Any = shape
            if not any_shape.has_text_frame:
                continue
            for paragraph in any_shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    result.append((run.text, bool(run.font.bold)))
    return result


def docx_runs(data: bytes) -> list[tuple[str, bool]]:
    """Text and boldness of each run: set directly or by its character style (E03-S03)."""

    def bold(run: Any) -> bool:
        style = run.style
        return bool(run.bold) or bool(style is not None and style.font.bold)

    return [(r.text, bold(r)) for p in open_docx(data).paragraphs for r in p.runs]


def runs(data: bytes, format: DocumentFormat) -> list[tuple[str, bool]]:
    return docx_runs(data) if format is DocumentFormat.DOCX else pptx_runs(data)


def texts(data: bytes, format: DocumentFormat) -> str:
    if format is DocumentFormat.DOCX:
        return "\n".join(docx_paragraphs(data))
    if format is DocumentFormat.PDF:
        return " ".join(" ".join(body_texts(data)).split())
    return "".join(text for text, _ in pptx_runs(data))


@GENERATORS
def test_the_layouts_sample_is_accepted(
    generate: Generate, format: DocumentFormat, review_dir: Path
) -> None:
    result, data = generate(LAYOUTS)
    assert result.notes == ()
    (review_dir / f"layouts.{format.value}").write_bytes(data)
    text = texts(data, format)
    for gone in (":::", "==", "[!NOTE]", "[!IMPORTANT]", "{.dark", "kicker=", "{.success}"):
        assert gone not in text, gone
    for kept in ("26 Tabellen", "Unterwegs behoben", "Der Fairness halber", "Schattenlauf"):
        assert kept in text, kept


@GENERATORS
@pytest.mark.parametrize(
    ("markdown", "message"),
    [
        ("## T {.wide}\n", "Line 1: Unknown heading attribute '.wide'"),
        ('## T {kicker="a" kicker="b"}\n', "Line 1: The heading attributes"),
        ('## T {kicker="a" kicker="b"}\n', "name kicker twice"),
        (
            "## T\n\n::: card\n- **a** b\n:::\n",
            "Line 3: Unknown container '::: card'. "
            "Valid containers: cards, rows, panel, statement, columns, conclusion, comment, notes, "
            "timeline, gantt, steps, riskmatrix.",
        ),
        ("## T\n\n::: cards dark\n- **a** b\n:::\n", "Line 3: The container '::: cards dark'"),
        ("## T\n\n::: cards dark\n- **a** b\n:::\n", "takes no arguments."),
        ("## T\n\n::: panel light\nx\n:::\n", "takes no arguments but dark."),
        ("## T\n\n::: columns 1-2\nx\n:::\n", "ratio of two or three whole numbers"),
        (
            "## T\n\n> [!HINT]\n> x\n",
            "Line 3: Unknown alert '[!HINT]'. "
            "Valid alerts: NOTE, TIP, IMPORTANT, WARNING, CAUTION.",
        ),
        ("# Danke {.dark}\n", "Line 1: The heading attribute '.dark' in '{.dark}' goes on"),
        ('# Danke {kicker="K"}\n', "goes on a '##' heading"),
        ("# A\n\n## B {.closing}\n", "Line 3: {.closing} goes on a '#' heading"),
        ("---\ntitel: T\n---\n## S\n\n[late]{.red}\n", "Line 6: '[late]{.red}' names no colour."),
        (
            "## S\n\n[late]{.red}\n",
            "Valid: {.success}, {.warning}, {.danger}, {.info}, {.neutral}.",
        ),
        ("---\nstatus.ok: Erledigt\n---\n## T\n", "names no status category"),
        (
            "---\nstatus.success: Erledigt\nstatus.info: Erledigt\n---\n## T\n",
            "'Erledigt' is assigned to two categories",
        ),
        ("## T\n\n- a\n\n  ::: card\n  x\n  :::\n", "Line 5: Unknown container"),
    ],
)
def test_mistakes_raise_alike(
    generate: Generate, format: DocumentFormat, markdown: str, message: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown)
    assert error.value.format is format
    assert message in error.value.reason


@GENERATORS
def test_braces_that_are_no_attributes_stay_in_the_title(
    generate: Generate, format: DocumentFormat
) -> None:
    _, data = generate("## Sets {a, b}\n\nText\n")
    assert "Sets {a, b}" in texts(data, format)


@GENERATORS
def test_heading_attributes_are_left_out(generate: Generate, format: DocumentFormat) -> None:
    _, data = generate('# Deck\n\n## Titel {.dark kicker="Warum"}\n\nText\n')
    text = texts(data, format)
    assert "Titel" in text
    assert "{" not in text and "kicker" not in text
    # PowerPoint draws the kicker above the title (E04-S03); Word leaves it out.
    assert ("Warum" in text) is (format is DocumentFormat.PPTX)


@OFFICE
def test_coloured_words_lose_their_brackets_and_are_bold(
    generate: Generate, format: DocumentFormat
) -> None:
    _, data = generate(
        "## S\n\nStatus: [on **schedule**]{.success} and [watch closely]{.warning}.\n"
    )
    found = runs(data, format)
    text = "".join(t for t, _ in found)
    assert "Status: on schedule and watch closely." in text
    assert ("watch closely", True) in found
    assert ("on ", True) in found and ("schedule", True) in found
    assert ("Status: ", False) in found


@GENERATORS
@pytest.mark.parametrize(
    ("markdown", "kept"),
    [
        ("[a] {.success}", "[a] {.success}"),
        ("[a]{.success extra}", "[a]{.success extra}"),
        ("`[a]{.success}`", "[a]{.success}"),
        ("[a](https://example.com){.x}", "a{.x}"),
        ("[a\nb]{.success}", "[a b]{.success}"),
    ],
)
def test_other_brackets_and_braces_stay_text(
    generate: Generate, format: DocumentFormat, markdown: str, kept: str
) -> None:
    _, data = generate(f"## S\n\n{markdown}\n")
    assert kept in texts(data, format)


@GENERATORS
def test_marks_and_container_fences_go_their_content_stays(
    generate: Generate, format: DocumentFormat
) -> None:
    _, data = generate("## S\n\n::: panel dark\nSome ==marked== text.\n:::\n\n> [!TIP]\n> A tip.\n")
    text = texts(data, format)
    assert "Some marked text." in text
    assert "A tip." in text
    assert ":::" not in text and "[!TIP]" not in text
