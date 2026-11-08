from __future__ import annotations

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import TEXTS, Language, Marking, Orientation, SlidesVariant, WordVariant


def test_word_variants() -> None:
    assert WordVariant.parse("Quer") is WordVariant.LANDSCAPE
    assert WordVariant.LANDSCAPE.orientation is Orientation.LANDSCAPE
    assert WordVariant.PORTRAIT.has_cover
    assert not WordVariant.PORTRAIT_NO_COVER.has_cover
    assert WordVariant.PORTRAIT.package_file == "word-hoch.docx"


def test_unknown_variant_lists_the_valid_ones() -> None:
    with pytest.raises(DocumentConversionError) as error:
        WordVariant.parse("breit")
    assert error.value.format is DocumentFormat.DOCX
    assert "hoch, hoch-ohne-deckblatt, quer, quer-ohne-deckblatt" in error.value.reason


def test_slides_variants() -> None:
    assert SlidesVariant.parse("schulung") is SlidesVariant.TRAINING
    assert SlidesVariant.BASIC.package_file(Language.EN) == "slides-basis-en.pptx"
    assert SlidesVariant.TRAINING.package_file(Language.EN) == "slides-schulung-en.pptx"
    assert SlidesVariant.TRAINING.package_file(Language.DE) == "slides-schulung.pptx"
    assert SlidesVariant.TRAINING.default_marking is Marking.INTERNAL
    assert SlidesVariant.BASIC.default_marking is Marking.NONE
    with pytest.raises(DocumentConversionError) as error:
        SlidesVariant.parse("x")
    assert error.value.format is DocumentFormat.PPTX


def test_language() -> None:
    assert Language.parse("EN", DocumentFormat.DOCX) is Language.EN
    with pytest.raises(DocumentConversionError):
        Language.parse("fr", DocumentFormat.DOCX)


def test_marking() -> None:
    assert Marking.parse(" Vertraulich", DocumentFormat.PPTX) is Marking.CONFIDENTIAL
    with pytest.raises(DocumentConversionError) as error:
        Marking.parse("geheim", DocumentFormat.PPTX)
    assert "vertraulich, intern, entwurf, kein" in error.value.reason
    assert TEXTS[Language.DE].marking(Marking.INTERNAL) == "Für den internen Gebrauch"
    assert TEXTS[Language.EN].marking(Marking.CONFIDENTIAL) == "CONFIDENTIAL"
    assert TEXTS[Language.EN].marking(Marking.DRAFT) == "DRAFT"
    assert TEXTS[Language.DE].marking(Marking.NONE) == ""
