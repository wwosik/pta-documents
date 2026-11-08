from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.conversions import ConversionOptions, ConverterRegistry, convert, registry
from pta_documents.markdown import MarkdownDocument

SAMPLES = Path(__file__).parent / "samples"


class _Spy:
    def __init__(self, format: DocumentFormat) -> None:
        self.format = format
        self.options: ConversionOptions | None = None
        self.data: bytes | None = None

    def can_convert(self, format: DocumentFormat) -> bool:
        return format is self.format

    def convert(
        self, data: bytes | BinaryIO, options: ConversionOptions | None = None
    ) -> MarkdownDocument:
        self.data = data if isinstance(data, bytes) else data.read()
        self.options = options
        return MarkdownDocument("")


class _ForwardOnly(io.BytesIO):
    def seekable(self) -> bool:
        return False


@pytest.mark.parametrize("sample", ["sample.docx", "sample.pptx"])
def test_without_images_nothing_is_extracted_or_referenced(sample: str) -> None:
    with (SAMPLES / sample).open("rb") as stream:
        document = ConverterRegistry.default().convert(
            stream, sample, ConversionOptions(include_images=False)
        )
    assert document.text
    assert document.resources == ()
    assert "![" not in document.text


@pytest.mark.parametrize("sample", ["sample.docx", "sample.pptx"])
def test_convert_gives_each_format_to_its_converter(sample: str) -> None:
    expected = (SAMPLES / f"{sample}.expected.md").read_text(encoding="utf-8")
    assert convert((SAMPLES / sample).read_bytes(), "misleading.pdf").text == expected


def test_unsupported_formats_are_rejected_by_the_registry() -> None:
    with (
        (SAMPLES / "sample.zip").open("rb") as stream,
        pytest.raises(DocumentConversionError) as error,
    ):
        ConverterRegistry.default().convert(stream, "sample.zip")
    assert error.value.format is DocumentFormat.ZIP
    assert error.value.reason.startswith("No converter is registered for this format.")
    assert "Supported formats: pdf, docx, pptx" in error.value.reason


def test_the_registry_passes_the_file_name_on() -> None:
    spy = _Spy(DocumentFormat.DOC)
    with (SAMPLES / "sample.doc").open("rb") as stream:
        ConverterRegistry([spy]).convert(stream, "letter.doc")
    assert spy.options is not None
    assert spy.options.file_name == "letter.doc"
    assert spy.data == (SAMPLES / "sample.doc").read_bytes()


def test_the_file_name_from_the_options_is_used_and_the_other_options_are_kept() -> None:
    spy = _Spy(DocumentFormat.MSG)
    options = ConversionOptions(file_name="mail.msg", include_images=False)
    ConverterRegistry([spy]).convert((SAMPLES / "sample.doc").read_bytes(), options=options)
    assert spy.options == options


def test_the_first_converter_that_accepts_the_format_wins() -> None:
    first, second = _Spy(DocumentFormat.DOCX), _Spy(DocumentFormat.DOCX)
    ConverterRegistry([first, second]).convert((SAMPLES / "sample.docx").read_bytes())
    assert first.options is not None
    assert second.options is None


def test_additional_converters_follow_the_builtin_ones() -> None:
    rtf, docx = _Spy(DocumentFormat.RTF), _Spy(DocumentFormat.DOCX)
    registry_ = ConverterRegistry.default(rtf, docx)
    assert registry_.converters[-2:] == (rtf, docx)
    registry_.convert((SAMPLES / "sample.rtf").read_bytes())
    registry_.convert((SAMPLES / "sample.docx").read_bytes())
    assert rtf.options is not None
    assert docx.options is None
    assert registry_.can_convert(DocumentFormat.RTF)
    assert not registry_.can_convert(DocumentFormat.XLSX)


def test_a_stream_that_cannot_seek_is_accepted() -> None:
    expected = (SAMPLES / "sample.docx.expected.md").read_text(encoding="utf-8")
    assert convert(_ForwardOnly((SAMPLES / "sample.docx").read_bytes())).text == expected


@pytest.mark.parametrize(
    ("file_name", "format", "new_format"),
    [
        ("letter.doc", DocumentFormat.DOC, ".docx"),
        ("table.xls", DocumentFormat.XLS, ".docx"),
        ("slides.ppt", DocumentFormat.PPT, ".pptx"),
        ("mail.msg", DocumentFormat.MSG, ".docx"),
        ("backup.old", DocumentFormat.OLE, ".docx"),
    ],
)
def test_legacy_office_files_are_rejected_with_advice(
    file_name: str, format: DocumentFormat, new_format: str
) -> None:
    with pytest.raises(DocumentConversionError) as error:
        convert((SAMPLES / "sample.doc").read_bytes(), file_name)
    assert error.value.format is format
    assert error.value.reason.startswith("Legacy binary Office files")
    assert f"as {new_format}" in error.value.reason


@pytest.mark.parametrize(
    ("sample", "format"),
    [("sample.rtf", DocumentFormat.RTF), ("sample.xlsx", DocumentFormat.XLSX)],
)
def test_rtf_and_xlsx_name_what_to_save_instead(sample: str, format: DocumentFormat) -> None:
    with pytest.raises(DocumentConversionError) as error:
        convert((SAMPLES / sample).read_bytes())
    assert error.value.format is format
    assert "as .docx and convert that" in error.value.reason
    assert "Supported formats: pdf, docx, pptx" in error.value.reason


@pytest.mark.parametrize("content", [b"# Markdown\n", bytes([1, 2, 0, 3])])
def test_text_and_unknown_input_is_rejected(content: bytes) -> None:
    with pytest.raises(DocumentConversionError) as error:
        convert(content)
    assert error.value.reason.startswith("No converter is registered for this format")


def test_a_missing_pdf_extra_gives_the_installation_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry, "pdf_extra_available", lambda: False)
    with pytest.raises(DocumentConversionError) as error:
        convert((SAMPLES / "sample.pdf").read_bytes())
    assert error.value.format is DocumentFormat.PDF
    assert error.value.reason == "PDF needs the optional extra 'pdf' (pip install -e '.[pdf]')."


def test_the_pdf_converter_is_registered_first_when_it_can_be_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spy = _Spy(DocumentFormat.PDF)

    class _Module:
        @staticmethod
        def PdfConverter() -> _Spy:  # stands in for the class
            return spy

    monkeypatch.setattr(registry, "pdf_extra_available", lambda: True)
    monkeypatch.setattr(registry.importlib, "import_module", lambda name: _Module)
    default = ConverterRegistry.default()
    assert default.converters[0] is spy
    default.convert((SAMPLES / "sample.pdf").read_bytes(), "x.pdf")
    assert spy.options is not None
    assert spy.options.file_name == "x.pdf"


def test_without_the_pdf_extra_the_pdf_converter_is_not_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry, "pdf_extra_available", lambda: False)
    assert not ConverterRegistry.default().can_convert(DocumentFormat.PDF)
