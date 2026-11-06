import pta_documents
from pta_documents import DocumentConversionError, DocumentFormat


def test_version_is_set() -> None:
    assert pta_documents.__version__


def test_error_carries_format_and_reason() -> None:
    error = DocumentConversionError(DocumentFormat.DOCX, "broken")
    assert error.format is DocumentFormat.DOCX
    assert error.reason == "broken"
    assert str(error) == "docx: broken"
