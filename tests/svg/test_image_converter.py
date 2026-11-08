"""E06-S04: SVG images in slides and documents — a PNG with the SVG beside it."""

from __future__ import annotations

import io
import zipfile

import pytest
from lxml import etree
from PIL import Image

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import images
from pta_documents.generation.common.images import GENERATOR_SCALE, default_converters
from pta_documents.generation.common.svg_blip import ASVG, SVG_BLIP_URI
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.svg import SvgImageConverter, is_svg

pytest.importorskip("resvg_py")

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
SQUARES = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">'
    b'<rect width="20" height="20" fill="#FF0000"/>'
    b'<rect x="20" width="20" height="20" fill="#0000FF"/>'
    b'<image href="https://example.org/tracker.png" width="1" height="1"/></svg>'
)
PLAN = DocumentResource("images/plan.svg", "image/svg+xml", SQUARES)
DOCUMENT = "---\ntitel: T\n---\n\n# Plan\n\n![Plan](images/plan.svg)\n"
DECK = "---\ntitel: T\n---\n\n## Plan\n\n![Plan](images/plan.svg)\n\nDazu ein Satz.\n"
ROW = "---\ntitel: T\n---\n\n## Plan\n\n![Plan](images/plan.svg) ![Noch einmal](images/plan.svg)\n"


@pytest.mark.parametrize(
    ("path", "content_type", "content", "expected"),
    [
        ("a.svg", "application/octet-stream", b"", True),
        ("a.SVG", "application/octet-stream", b"", True),
        ("a", "image/svg+xml", b"", True),
        ("a", "application/octet-stream", b"\xef\xbb\xbf \n<svg/>", True),
        ("a", "application/octet-stream", b'<?xml version="1.0"?>\n<svg/>', True),
        ("a", "application/octet-stream", b"<?xml version='1.0'?><html/>", False),
        ("a.png", "image/png", b"\x89PNG", False),
    ],
)
def test_an_svg_is_known_by_type_path_or_content(
    path: str, content_type: str, content: bytes, expected: bool
) -> None:
    assert is_svg(DocumentResource(path, content_type, content)) is expected


def test_the_converter_gives_a_png_at_scale_its_natural_size_and_the_clean_svg() -> None:
    converted = SvgImageConverter().convert(PLAN, GENERATOR_SCALE)
    assert converted is not None
    assert (converted.content_type, converted.width, converted.height) == ("image/png", 40, 20)
    assert Image.open(io.BytesIO(converted.content)).size == (80, 40)
    assert converted.svg is not None
    assert b"example.org" not in converted.svg
    assert SvgImageConverter().convert(DocumentResource("a.png", "image/png", b""), 2) is None
    assert SvgImageConverter().format == "SVG"


def test_a_broken_svg_is_an_svg_error_naming_the_image() -> None:
    broken = DocumentResource("images/kaputt.svg", "image/svg+xml", b"<svg")
    with pytest.raises(DocumentConversionError) as error:
        SvgImageConverter().convert(broken, 2)
    assert error.value.format is DocumentFormat.SVG
    assert error.value.reason.startswith("The image 'images/kaputt.svg' cannot be converted: ")
    with pytest.raises(DocumentConversionError) as error:
        DocxGenerator().generate(
            MarkdownDocument(DOCUMENT.replace("plan", "kaputt"), (broken,)), io.BytesIO()
        )
    assert error.value.format is DocumentFormat.SVG
    assert "'images/kaputt.svg'" in error.value.reason


def test_the_generators_convert_svg_by_default_with_the_extra() -> None:
    assert default_converters() == (SvgImageConverter(),)
    assert DocxOptions().image_converters == (SvgImageConverter(),)
    assert PptxOptions().image_converters == (SvgImageConverter(),)


def test_without_the_extra_the_error_names_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(images, "svg_available", lambda: False)
    assert default_converters() == ()
    for generate, markdown in ((DocxGenerator(), DOCUMENT), (PptxGenerator(), DECK)):
        with pytest.raises(DocumentConversionError) as error:
            generate.generate(MarkdownDocument(markdown, (PLAN,)), io.BytesIO())
        assert "pta-documents[svg]" in error.value.reason
        assert "'images/plan.svg'" in error.value.reason


def blips(data: bytes, prefix: str) -> list[tuple[str, str, str, str]]:
    """Per picture with an SVG: its part, PNG type, SVG type and the SVG's part name."""
    found: list[tuple[str, str, str, str]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        types = etree.fromstring(archive.read("[Content_Types].xml"))
        overrides = {o.get("PartName"): o.get("ContentType") for o in types}
        defaults = {d.get("Extension"): d.get("ContentType") for d in types}

        def content_type(name: str) -> str:
            return str(overrides.get("/" + name) or defaults.get(name.rsplit(".", 1)[-1]))

        for name in archive.namelist():
            if not (name.startswith(prefix) and name.endswith(".xml")) or "_rels" in name:
                continue
            root = etree.fromstring(archive.read(name))
            blip_list = list(root.iter(f"{{{A}}}blip"))
            if not blip_list:
                continue
            folder, file = name.rsplit("/", 1)
            rels = etree.fromstring(archive.read(f"{folder}/_rels/{file}.rels"))
            targets = {r.get("Id"): f"{folder}/{r.get('Target')}" for r in rels}
            for blip in blip_list:
                vectors = list(blip.iter(f"{{{ASVG}}}svgBlip"))
                if not vectors:
                    continue
                ext = vectors[0].getparent()
                assert ext is not None and ext.get("uri") == SVG_BLIP_URI
                png = _resolve(targets[blip.get(f"{{{R}}}embed")])
                svg = _resolve(targets[vectors[0].get(f"{{{R}}}embed")])
                assert b"example.org" not in archive.read(svg)
                found.append((name, content_type(png), content_type(svg), svg))
    return found


def _resolve(path: str) -> str:
    parts: list[str] = []
    for piece in path.split("/"):
        if piece == "..":
            parts.pop()
        else:
            parts.append(piece)
    return "/".join(parts)


@pytest.mark.parametrize("markdown", [DECK, ROW], ids=["placeholder", "row"])
def test_a_svg_image_in_a_deck_is_a_png_with_the_svg_beside_it(markdown: str) -> None:
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown, (PLAN,)), output)
    found = blips(output.getvalue(), "ppt/slides/")
    assert found and all(f[1:3] == ("image/png", "image/svg+xml") for f in found)
    assert len({f[3] for f in found}) == 1  # the same SVG is in the deck once
    assert [n for n in result.notes if n.code == "image-enlarged"] == []


def test_a_svg_image_in_a_document_is_a_png_with_the_svg_beside_it_at_its_natural_size() -> None:
    output = io.BytesIO()
    result = DocxGenerator().generate(MarkdownDocument(DOCUMENT, (PLAN,)), output)
    found = blips(output.getvalue(), "word/")
    assert [f[1:] for f in found] == [("image/png", "image/svg+xml", "word/media/image1.svg")]
    with zipfile.ZipFile(output) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    extent = next(root.iter(f"{WP}extent"))
    assert (int(extent.get("cx", "0")), int(extent.get("cy", "0"))) == (40 * 9525, 20 * 9525)
    assert "Abbildung" in "".join(str(t) for t in root.itertext())
    assert result.notes == ()
