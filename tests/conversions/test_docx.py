from __future__ import annotations

from pathlib import Path

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.options import ConversionOptions
from pta_documents.markdown import MetadataKeys
from tests.expected import assert_matches_expected, assert_resources_match_references

SAMPLES = Path(__file__).parent / "samples"


def test_sample_converts_to_the_expected_markdown() -> None:
    document = DocxConverter().convert((SAMPLES / "sample.docx").read_bytes())
    assert_matches_expected(SAMPLES / "sample.docx.expected.md", document.text)
    assert_resources_match_references(document)
    assert document.resources


def test_identical_images_are_stored_once() -> None:
    with (SAMPLES / "sample.docx").open("rb") as stream:
        document = DocxConverter().convert(stream, ConversionOptions(resource_path_prefix="media/"))
    (image,) = document.resources
    assert image.path == "media/image1.png"
    assert image.content_type == "image/png"
    assert "![Bar chart](media/image1.png)" in document.text
    assert "![Bar chart again](media/image1.png)" in document.text
    assert document.metadata[MetadataKeys.TITLE] == "Sample document"


def test_without_images_nothing_is_extracted_or_referenced() -> None:
    document = DocxConverter().convert(
        (SAMPLES / "sample.docx").read_bytes(), ConversionOptions(include_images=False)
    )
    assert document.resources == ()
    assert "![" not in document.text


@pytest.mark.parametrize("content", [b"PK\x03\x04 broken", b"not a zip"])
def test_damaged_input_raises(content: bytes) -> None:
    with pytest.raises(DocumentConversionError) as error:
        DocxConverter().convert(content)
    assert error.value.format is DocumentFormat.DOCX
