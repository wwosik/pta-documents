from __future__ import annotations

import io
from pathlib import Path

import pytest

from pta_documents import DocumentFormat
from pta_documents.conversions import detect

SAMPLES = Path(__file__).parent / "samples"


@pytest.mark.parametrize(
    ("sample", "expected"),
    [
        ("sample.pdf", DocumentFormat.PDF),
        ("sample.docx", DocumentFormat.DOCX),
        ("sample.pptx", DocumentFormat.PPTX),
        ("sample.xlsx", DocumentFormat.XLSX),
        ("sample.zip", DocumentFormat.ZIP),
        ("sample.rtf", DocumentFormat.RTF),
        ("sample.txt", DocumentFormat.TEXT),
        ("sample.doc", DocumentFormat.DOC),
        ("sample.xls", DocumentFormat.XLS),
    ],
)
def test_samples_are_recognised(sample: str, expected: DocumentFormat) -> None:
    with (SAMPLES / sample).open("rb") as stream:
        assert detect(stream, sample) is expected
    assert detect((SAMPLES / sample).read_bytes(), sample) is expected


@pytest.mark.parametrize("sample", ["sample.doc", "sample.xls"])
def test_ole_files_without_a_known_extension_are_just_ole(sample: str) -> None:
    with (SAMPLES / sample).open("rb") as stream:
        assert detect(stream, "backup.old") is DocumentFormat.OLE
        assert detect(stream) is DocumentFormat.OLE


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("Brief.DOT", DocumentFormat.DOC),
        ("liste.xlt", DocumentFormat.XLS),
        ("makro.xla", DocumentFormat.XLS),
        ("folien.pps", DocumentFormat.PPT),
        ("vorlage.pot", DocumentFormat.PPT),
        ("alt.ppt", DocumentFormat.PPT),
        ("mail.msg", DocumentFormat.MSG),
        (r"C:\Ablage\brief.doc", DocumentFormat.DOC),
    ],
)
def test_the_extension_tells_ole_files_apart(file_name: str, expected: DocumentFormat) -> None:
    assert detect((SAMPLES / "sample.doc").read_bytes(), file_name) is expected


@pytest.mark.parametrize(
    ("sample", "file_name"),
    [("sample.pdf", "report.docx"), ("sample.docx", "slides.pptx"), ("sample.txt", "x.doc")],
)
def test_content_wins_over_a_misleading_extension(sample: str, file_name: str) -> None:
    expected = detect((SAMPLES / sample).read_bytes())
    assert detect((SAMPLES / sample).read_bytes(), file_name) is expected


@pytest.mark.parametrize(
    "content", [bytes([1, 2, 0, 3]), b"", bytes([0x50, 0x4B, 0x03, 0x04, 0xFF, 0x00])]
)
def test_binary_and_empty_input_is_unknown(content: bytes) -> None:
    assert detect(content) is DocumentFormat.UNKNOWN
    assert detect(io.BytesIO(content)) is DocumentFormat.UNKNOWN


def test_the_position_is_restored() -> None:
    stream = io.BytesIO((SAMPLES / "sample.docx").read_bytes())
    assert detect(stream) is DocumentFormat.DOCX
    assert stream.tell() == 0


def test_a_document_after_the_start_of_the_stream_is_detected_from_the_position() -> None:
    stream = io.BytesIO(b"prefix" + (SAMPLES / "sample.pptx").read_bytes())
    stream.seek(6)
    assert detect(stream) is DocumentFormat.PPTX
    assert stream.tell() == 6


class _ForwardOnly(io.BytesIO):
    def seekable(self) -> bool:
        return False


def test_a_stream_that_cannot_seek_is_refused() -> None:
    with pytest.raises(ValueError, match="seekable"):
        detect(_ForwardOnly(b"%PDF-1.7"))
