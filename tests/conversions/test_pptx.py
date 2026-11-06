from __future__ import annotations

from pathlib import Path

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.markdown import MetadataKeys
from tests.expected import assert_matches_expected, assert_resources_match_references

SAMPLES = Path(__file__).parent / "samples"


def test_sample_converts_to_the_expected_markdown() -> None:
    document = PptxConverter().convert((SAMPLES / "sample.pptx").read_bytes())
    assert_matches_expected(SAMPLES / "sample.pptx.expected.md", document.text)
    assert_resources_match_references(document)
    assert document.resources


def test_slide_titles_become_headings() -> None:
    document = PptxConverter().convert((SAMPLES / "sample.pptx").read_bytes())
    assert document.text.startswith("## Quarterly review\n")
    assert "## Highlights\n" in document.text
    assert "## Slide 3\n" in document.text
    assert "![Team photo](images/image1.png)" in document.text
    assert document.metadata[MetadataKeys.SLIDE_COUNT] == "3"


def test_without_images_nothing_is_extracted_or_referenced() -> None:
    document = PptxConverter().convert(
        (SAMPLES / "sample.pptx").read_bytes(), ConversionOptions(include_images=False)
    )
    assert document.resources == ()
    assert "![" not in document.text


def test_damaged_input_raises() -> None:
    with pytest.raises(DocumentConversionError) as error:
        PptxConverter().convert(b"PK\x03\x04 broken")
    assert error.value.format is DocumentFormat.PPTX
