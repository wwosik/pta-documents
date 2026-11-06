from __future__ import annotations

from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of


def test_find_resource_normalizes_references() -> None:
    image = DocumentResource("images/Bild 1.png", "image/png", b"x")
    document = MarkdownDocument("![a](images/Bild%201.png)", [image])
    assert document.find_resource("./images/Bild%201.png") is image
    assert document.find_resource("images\\Bild 1.png") is image
    assert document.find_resource("images/other.png") is None


def test_content_types() -> None:
    assert content_type_of("a.JPG") == "image/jpeg"
    assert content_type_of("a") == "application/octet-stream"
