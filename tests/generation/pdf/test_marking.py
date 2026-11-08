"""E12-S03: ``kennzeichnung:`` in the PDF — the text below the rule of every header and on the
cover, the watermark „ENTWURF" behind the content. The PDFs go to
``.tmp/review/pdf-marking-<variante>-<wert>.pdf``."""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Final

import pdfplumber
import pikepdf
import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import word_frame
from pta_documents.design.variants import Marking, WordVariant
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.markdown import MarkdownDocument
from tests.generation.pdf.support import body_texts

CREATED: Final = dt.datetime(2026, 11, 8, 9, 0, tzinfo=dt.UTC)
OPTIONS: Final = PdfOptions(created=CREATED, system_fonts=False)
FILLER: Final = "Wort " * 1200
"""Enough for two pages in every variant."""


def markdown(variant: WordVariant, value: str | None, language: str = "de") -> str:
    key = f"kennzeichnung: {value}\n" if value is not None else ""
    return (
        f"---\nvorlage: {variant.value}\ntitel: Angebot\nautor: Anna Nowak\nsprache: {language}\n"
        f"datum: 2026-11-08\n{key}---\n# Ausgangslage\n\n{FILLER}\n"
    )


def generate(text: str, options: PdfOptions = OPTIONS) -> bytes:
    output = io.BytesIO()
    PdfGenerator().generate(MarkdownDocument(text), output, options)
    return output.getvalue()


def marking_texts(data: bytes, variant: WordVariant) -> list[str]:
    """The text in the marking area of every page."""
    area = word_frame.marking_area(word_frame.read(variant))
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [
            page.crop(
                (area.x_pt, area.y_pt, area.x_pt + area.width_pt, area.y_pt + area.height_pt)
            ).extract_text()
            or ""
            for page in pdf.pages
        ]


def rotated_text(data: bytes) -> list[str]:
    """The characters drawn turned, page by page (the watermark)."""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return ["".join(c["text"] for c in page.chars if turned(c)) for page in pdf.pages]


def turned(char: dict[str, object]) -> bool:
    matrix = char["matrix"]
    assert isinstance(matrix, tuple)
    return abs(float(matrix[1])) > 0.01  # type: ignore[arg-type]


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
@pytest.mark.parametrize("value", [m for m in Marking if m is not Marking.NONE])
def test_every_page_shows_the_marking(
    variant: WordVariant, value: Marking, review_dir: Path
) -> None:
    data = generate(markdown(variant, value.value))
    (review_dir / f"pdf-marking-{variant.value}-{value.value}.pdf").write_bytes(data)
    expected = {
        Marking.CONFIDENTIAL: "VERTRAULICH",
        Marking.INTERNAL: "FÜR DEN INTERNEN GEBRAUCH",
        Marking.DRAFT: "ENTWURF",
    }[value]
    texts = marking_texts(data, variant)
    assert len(texts) >= 2
    assert all(t == expected for t in texts), texts
    watermark = rotated_text(data)
    if value is Marking.DRAFT:
        assert all(w == "ENTWURF" for w in watermark), watermark
    else:
        assert not any(watermark)


def test_the_marking_is_right_aligned_in_pta_blue() -> None:
    variant = WordVariant.PORTRAIT_NO_COVER
    data = generate(markdown(variant, "vertraulich"))
    area = word_frame.marking_area(word_frame.read(variant))
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        chars = [c for c in page.chars if area.y_pt <= c["top"] <= area.y_pt + area.height_pt]
        assert "".join(c["text"] for c in chars) == "VERTRAULICH"
        assert max(c["x1"] for c in chars) == pytest.approx(area.x_pt + area.width_pt, abs=0.5)
        assert {tuple(round(v, 2) for v in c["non_stroking_color"]) for c in chars} == {
            (0.0, 0.44, 0.73)
        }
        assert chars[0]["size"] == pytest.approx(9)


def test_the_cover_shows_the_marking_below_the_byline() -> None:
    data = generate(markdown(WordVariant.PORTRAIT, "intern"))
    cover = body_texts(data)[0].splitlines()
    assert cover[cover.index("Anna Nowak, 08.11.2026") + 1] == "FÜR DEN INTERNEN GEBRAUCH"
    data = generate(markdown(WordVariant.PORTRAIT_NO_COVER, "intern"))
    assert "GEBRAUCH" not in body_texts(data)[0]


def test_english_texts() -> None:
    variant = WordVariant.LANDSCAPE
    data = generate(markdown(variant, "entwurf", language="en"))
    assert set(marking_texts(data, variant)) == {"DRAFT"}
    assert set(rotated_text(data)) == {"DRAFT"}
    data = generate(markdown(variant, "vertraulich", language="en"))
    assert set(marking_texts(data, variant)) == {"CONFIDENTIAL"}


def test_the_watermark_is_behind_the_text_and_without_transparency() -> None:
    data = generate(markdown(WordVariant.PORTRAIT_NO_COVER, "entwurf"))
    with pikepdf.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            states = page.Resources.get("/ExtGState", pikepdf.Dictionary())
            for state in states.values():
                assert float(state.get("/ca", 1)) == 1.0
                assert "/SMask" not in state
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        watermark = [c for c in page.chars if turned(c)]
        body = [c for c in page.chars if not turned(c)]
        assert page.chars.index(watermark[0]) < page.chars.index(body[0])


def test_kein_changes_nothing() -> None:
    variant = WordVariant.PORTRAIT
    assert generate(markdown(variant, "kein")) == generate(markdown(variant, None))


def test_the_option_and_the_front_matter() -> None:
    variant = WordVariant.PORTRAIT_NO_COVER
    text = f"---\nvorlage: {variant.value}\n---\n# Titel\n"
    data = generate(text, PdfOptions(created=CREATED, system_fonts=False, marking=Marking.DRAFT))
    assert set(marking_texts(data, variant)) == {"ENTWURF"}
    data = generate(
        markdown(variant, "intern"),
        PdfOptions(created=CREATED, system_fonts=False, marking=Marking.DRAFT),
    )
    assert not any(rotated_text(data))


def test_an_unknown_value_names_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(markdown(WordVariant.PORTRAIT, "geheim"))
    assert error.value.format is DocumentFormat.PDF
    assert "vertraulich, intern, entwurf, kein" in error.value.reason
