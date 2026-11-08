"""The embedded templates are the cleaned source templates — nothing more, nothing less."""

from __future__ import annotations

import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import docx
import pptx
import pytest
from lxml import etree

from pta_documents.design import slides as design
from pta_documents.design import templates
from pta_documents.design.variants import (
    SLIDES_SOURCES,
    SLIDES_WITHOUT_TITLE_LOGO,
    Language,
    SlidesVariant,
    WordVariant,
)
from tests.conftest import REPO_ROOT, SOURCE_TEMPLATES

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PERSON_NAMES = ("Robert Fischer", "Ines Erdmann", "Oliver Henkel")
WORD = [(v.package_file, v.source_file) for v in WordVariant]
SLIDES = list(SLIDES_SOURCES.items())


def parts(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n) for n in z.namelist()}


def source_parts(name: str) -> dict[str, bytes]:
    return parts((SOURCE_TEMPLATES / name).read_bytes())


@pytest.mark.parametrize(("embedded", "source"), WORD + SLIDES)
def test_no_sharepoint_trash_or_names(embedded: str, source: str) -> None:
    content = parts(templates.read(embedded))
    assert not [n for n in content if n.startswith(("customXml/", "[trash]/"))]
    assert "docProps/custom.xml" not in content
    assert "docProps/thumbnail.jpeg" not in content
    for name, data in content.items():
        if name.endswith((".xml", ".rels")):
            text = data.decode("utf-8")
            for person in PERSON_NAMES:
                assert person not in text, (name, person)
            assert "_dlc_DocId" not in text


@pytest.mark.parametrize(("embedded", "source"), WORD)
def test_word_template(embedded: str, source: str) -> None:
    data = templates.read(embedded)
    document = docx.Document(io.BytesIO(data))
    assert document.paragraphs == [] and document.tables == []
    content, original = parts(data), source_parts(source)
    for part in (
        "word/styles.xml",
        "word/numbering.xml",
        "word/theme/theme1.xml",
        "word/settings.xml",
        "word/fontTable.xml",
    ):
        assert content[part] == original[part], part
    for name in original:
        if re.fullmatch(r"word/(header|footer)\d+\.xml|word/media/.*", name):
            assert content[name] == original[name], name
    types = content["[Content_Types].xml"].decode()
    assert "wordprocessingml.document.main+xml" in types
    assert "template.main" not in types


@pytest.mark.parametrize(("embedded", "source"), SLIDES)
def test_slides_template(embedded: str, source: str) -> None:
    data = templates.read(embedded)
    presentation = pptx.Presentation(io.BytesIO(data))
    assert len(presentation.slides) == 0
    assert len(presentation.slide_layouts) == 35
    content, original = parts(data), source_parts(source)
    assert not [n for n in content if n.startswith(("ppt/slides/", "ppt/notesSlides/"))]
    kept = [
        n
        for n in original
        if re.fullmatch(r"ppt/(slideMasters|slideLayouts|theme)/[^/]+\.xml", n)
        and n != "ppt/theme/theme4.xml"
    ]
    title_layouts = title_layout_parts(content)
    for name in kept:
        if name in content and not (
            embedded in SLIDES_WITHOUT_TITLE_LOGO and name in title_layouts
        ):
            assert content[name] == original[name], name
    for name in original:
        if re.fullmatch(r"ppt/(slideMasters|slideLayouts)/[^/]+\.xml", name):
            assert name in content, name
    types = content["[Content_Types].xml"].decode()
    assert "presentationml.presentation.main+xml" in types
    assert "template.main" not in types


def title_layout_parts(content: dict[str, bytes]) -> set[str]:
    """The part names of the four title layouts."""
    wanted = set(design.TITLE_SLIDES.values())
    result: set[str] = set()
    for name, data in content.items():
        if not re.fullmatch(r"ppt/slideLayouts/[^/]+\.xml", name):
            continue
        match = re.search(rb'<p:cSld name="([^"]+)"', data)
        if match is not None and match.group(1).decode() in wanted:
            result.add(name)
    return result


def emf_targets(content: dict[str, bytes], layout: str) -> list[str]:
    directory, file = layout.rsplit("/", 1)
    rels = content[f"{directory}/_rels/{file}.rels"].decode()
    return re.findall(r'Target="([^"]+\.emf)"', rels)


@pytest.mark.parametrize("embedded", SLIDES_WITHOUT_TITLE_LOGO)
def test_title_layouts_lose_only_the_german_logo(embedded: str) -> None:
    content = parts(templates.read(embedded))
    original = source_parts(SLIDES_SOURCES[embedded])
    layouts = title_layout_parts(content)
    assert len(layouts) == 4
    for name in layouts:
        assert emf_targets(original, name), name
        assert not emf_targets(content, name), name
        # The source layout without the shapes that show an EMF is the embedded one.
        before = etree.fromstring(original[name])
        directory, file = name.rsplit("/", 1)
        rels = original[f"{directory}/_rels/{file}.rels"].decode()
        emf_ids = set(re.findall(r'Id="(rId\d+)"[^>]*Target="[^"]+\.emf"', rels))
        tree = before.find(f"{{{P}}}cSld/{{{P}}}spTree")
        assert tree is not None and emf_ids
        logos = [
            shape
            for shape in tree
            if any(blip.get(f"{{{R}}}embed") in emf_ids for blip in shape.iter(f"{{{A}}}blip"))
        ]
        assert len(logos) == 1, name
        tree.remove(logos[0])
        assert etree.tostring(before, method="c14n") == etree.tostring(
            etree.fromstring(content[name]), method="c14n"
        ), name


def test_slide_templates_for_variants() -> None:
    for variant in SlidesVariant:
        for language in Language:
            assert templates.slides_template(variant, language)[:2] == b"PK"
    assert templates.read(templates.ENGLISH_LOGO)[:4] == b"\x89PNG"


def test_embedded_templates_are_up_to_date() -> None:
    tool = REPO_ROOT / "tools" / "prepare-templates" / "prepare-templates.py"
    result = subprocess.run(
        [sys.executable, str(tool), "--check"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_wheel_contains_templates(tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--quiet",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(tmp_path),
            str(REPO_ROOT),
        ],
        check=True,
    )
    (wheel,) = tmp_path.glob("*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    for variant in WordVariant:
        assert f"pta_documents/design/templates/{variant.package_file}" in names
    for embedded in SLIDES_SOURCES:
        assert f"pta_documents/design/templates/{embedded}" in names
