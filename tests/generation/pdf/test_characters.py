"""E05-S04: characters the fonts lack — an error without ``replace_unsupported``, else replaced
grapheme cluster by grapheme cluster (port of DocLibs ``PdfGeneratorTests.MissingGlyph_*`` and
``ReplaceUnsupported_*``)."""

from __future__ import annotations

import dataclasses
import io
from typing import Final

import pdfplumber
import pikepdf
import pytest

from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.result import GenerationResult, NoteCodes
from pta_documents.generation.pdf import PdfGenerator, PdfOptions
from pta_documents.markdown import MarkdownDocument
from tests.generation.pdf.support import body_texts
from tests.generation.pdf.test_generator import NO_COVER, OPTIONS

STRICT: Final = dataclasses.replace(OPTIONS, replace_unsupported=None)
CHART: Final = "```chart\ntitle: Werte\n---\nx, a\nΔ, 2\nB, 3\n```\n"


def generate(markdown: str, options: PdfOptions = OPTIONS) -> tuple[GenerationResult, bytes]:
    output = io.BytesIO()
    result = PdfGenerator().generate(MarkdownDocument(markdown), output, options)
    return result, output.getvalue()


@pytest.mark.parametrize(
    "markdown",
    [
        NO_COVER + "Ein Δ im Text.\n",
        NO_COVER + "# Kapitel Δ\n",
        NO_COVER + "| a |\n| - |\n| Δ |\n",
        NO_COVER + "```\nΔ = 1\n```\n",
        "---\ntitel: Bericht Δ\n---\nText.\n",
        NO_COVER + CHART,
    ],
    ids=["text", "heading", "table", "code", "header", "drawing"],
)
def test_without_a_replacement_a_missing_character_names_itself_and_the_font(
    markdown: str,
) -> None:
    with pytest.raises(DocumentConversionError) as caught:
        generate(markdown, STRICT)
    reason = caught.value.reason
    assert "'Δ' (U+0394) is not in the font (" in reason
    assert "Selawik" in reason or "Inconsolata" in reason


def test_a_character_outside_the_bmp_is_named_as_one_code_point() -> None:
    with pytest.raises(DocumentConversionError, match=r"'😀' \(U\+1F600\)"):
        generate(NO_COVER + "Gut 😀\n", STRICT)


def test_every_emoji_is_asked_for_once_as_one_cluster() -> None:
    asked: list[str] = []

    def replace(cluster: str) -> str:
        asked.append(cluster)
        return "(+)" if cluster == "👍🏽" else "*"

    options = dataclasses.replace(OPTIONS, replace_unsupported=replace)
    markdown = NO_COVER + "# Lob 👍🏽\n\nSiehe [oben](#lob-). 👍🏽 und ❤️ und 👨‍👩‍👧.\n"
    result, data = generate(markdown, options)
    assert asked == ["👍🏽", "❤️", "👨‍👩‍👧"]
    text = body_texts(data)[0]
    assert "Lob (+)" in text and "Siehe oben. (+) und * und *." in text
    # The replacement is in the bookmark; the anchor and the link to it stay.
    with pikepdf.open(io.BytesIO(data)) as pdf:
        with pdf.open_outline() as outline:
            assert [item.title for item in outline.root] == ["1 Lob (+)"]
        annotations = list(pdf.pages[0].obj.Annots)
        assert len(annotations) == 1 and "/URI" not in annotations[0].get("/A", {})
    assert {n.code for n in result.notes} == {NoteCodes.CHARACTER_MISSING}
    assert "replace_unsupported" in result.notes[0].message


def test_a_replacement_the_fonts_lack_too_is_an_error() -> None:
    options = dataclasses.replace(OPTIONS, replace_unsupported=lambda cluster: "Ω")
    with pytest.raises(DocumentConversionError, match=r"replacement 'Ω' of the character 'Δ'"):
        generate(NO_COVER + "Ein Δ.\n", options)


def test_by_default_a_missing_character_shows_as_a_question_mark_with_a_note() -> None:
    result, data = generate(NO_COVER + "Ein Δ und 👍🏽.\n" + CHART)
    assert "Ein ? und ?." in body_texts(data)[0]
    assert {n.code for n in result.notes} == {NoteCodes.CHARACTER_MISSING}
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        assert "?" in "".join(c["text"] for c in pdf.pages[0].chars if c["size"] < 9)


def test_invisible_format_characters_the_fonts_lack_are_left_out() -> None:
    result, data = generate(NO_COVER + "Wort​trenner.\n", STRICT)
    assert "Worttrenner." in body_texts(data)[0]
    assert result.notes == ()
