"""E03-S01: the document frame on the PTA template."""

from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from pta_documents import DocumentConversionError, DocumentFormat
from pta_documents.design import templates
from pta_documents.design.variants import WordVariant
from pta_documents.generation.docx.options import DocxOptions
from tests.generation.docx.conftest import all_text, generate, open_docx, parts, style_name

REPORT = """---
titel: Statusbericht Projekt Nordlicht
untertitel: Quartal 3
autor: Erika Muster
ort: Hamburg
datum: 2026-11-06
---
# Ausgangslage

Der Text des ersten Kapitels.

# Ergebnisse

## Zahlen

Der Text des zweiten Kapitels.
"""


def styles_of(data: bytes) -> list[tuple[str, str]]:
    document = open_docx(data)
    return [(style_name(p), p.text) for p in document.paragraphs]


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
def test_every_variant(variant: WordVariant, review_dir: Path) -> None:
    data = generate(REPORT.replace("---\n#", f"vorlage: {variant.value}\n---\n#", 1))
    (review_dir / f"frame-{variant.value}.docx").write_bytes(data)
    text = all_text(data)
    for leftover in (
        "Titel des Dokuments",
        "Untertitel des Dokuments",
        "xx.xx",
        "Lorem",
        "Name Nachname",
        "Robert Fischer",
        "customXml",
    ):
        assert leftover not in text, leftover
    assert not [n for n in parts(data) if n.startswith(("customXml/", "[trash]/"))]
    assert "06.11.2026" in text
    paragraphs = styles_of(data)
    if variant.has_cover:
        assert paragraphs[:3] == [
            ("Title", "Statusbericht Projekt Nordlicht"),
            ("Subtitle", "Quartal 3"),
            ("Autor", "Erika Muster, Hamburg, 06.11.2026"),
        ]
    else:
        assert ("Title", "Statusbericht Projekt Nordlicht") not in paragraphs
        assert "Statusbericht Projekt Nordlicht" in text  # in the header
    assert ("heading 1", "Ausgangslage") in paragraphs
    assert ("heading 2", "Zahlen") in paragraphs


@pytest.mark.parametrize("variant", list(WordVariant), ids=lambda v: v.value)
def test_page_setup_header_and_logo_are_the_templates(variant: WordVariant) -> None:
    data = generate(REPORT.replace("---\n#", f"vorlage: {variant.value}\n---\n#", 1))
    result, template = parts(data), parts(templates.word_template(variant))
    section = re.compile(rb"<w:sectPr.*</w:sectPr>", re.S)
    found, expected = (
        section.search(result["word/document.xml"]),
        section.search(template["word/document.xml"]),
    )
    assert found and expected
    assert re.sub(rb' xmlns:\w+="[^"]+"', b"", found.group(0)) == re.sub(
        rb' xmlns:\w+="[^"]+"', b"", expected.group(0)
    )
    for name, content in template.items():
        if name.startswith("word/media/"):
            assert result[name] == content


def test_missing_title_with_cover_raises() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate("# Kapitel\n")
    assert error.value.format is DocumentFormat.DOCX
    assert "titel" in error.value.reason


def test_without_cover_no_title_is_fine() -> None:
    data = generate("---\nvorlage: hoch-ohne-deckblatt\n---\n# Kapitel\n")
    assert "Titel des Dokuments" not in all_text(data)


def test_missing_subtitle_removes_the_styleref() -> None:
    data = generate("---\ntitel: T\n---\n# K\n")
    headers = "".join(c.decode() for n, c in parts(data).items() if "header" in n)
    assert "STYLEREF  Untertitel" not in headers
    assert "STYLEREF  Titel" in headers


def test_footer_date_company_and_english_texts() -> None:
    data = generate(
        "---\ntitel: T\nfirma: PTA GmbH\nsprache: en\n---\n# K\n",
        DocxOptions(date=dt.date(2026, 1, 2)),
    )
    footers = "".join(c.decode() for n, c in parts(data).items() if "footer" in n)
    assert "02.01.2026" in footers
    assert "PTA GmbH" in footers and "PTA IT-Beratung" not in footers
    assert "As of:" in footers and "Stand:" not in footers
    assert ">Page <" in footers or "Page " in footers


def test_footer_falls_back_to_today() -> None:
    data = generate("---\ntitel: T\n---\n# K\n")
    assert dt.date.today().strftime("%d.%m.%Y") in all_text(data)


def test_table_of_contents_on_request() -> None:
    body = parts(generate("---\ntitel: T\n---\n# K\n"))["word/document.xml"].decode()
    assert "TOC " not in body
    data = generate("---\ntitel: T\ninhaltsverzeichnis: ja\n---\n# K\n")
    text = all_text(data)
    assert 'TOC \\o "1-2" \\h \\z \\u' in text
    assert '<w:updateFields w:val="true"/>' in parts(data)["word/settings.xml"].decode()
    paragraphs = styles_of(data)
    assert ("Zwischenüberschrift", "Inhalt") in paragraphs
    assert any(style == "toc 1" for style, _ in paragraphs)


def test_landscape_gets_the_borrowed_styles() -> None:
    data = generate("---\nvorlage: quer\ntitel: T\ninhaltsverzeichnis: ja\n---\n# K\n")
    names = {s.name for s in open_docx(data).styles}
    assert {"Hyperlink", "toc 1", "toc 2"} <= names


def test_properties() -> None:
    document = open_docx(generate(REPORT))
    properties = document.core_properties
    assert properties.title == "Statusbericht Projekt Nordlicht"
    assert properties.subject == "Quartal 3"
    assert properties.author == "Erika Muster"
    assert properties.last_modified_by == "Erika Muster"


@pytest.mark.parametrize(
    ("front", "expected"),
    [
        ("vorlage: breit", "Valid values: hoch, hoch-ohne-deckblatt"),
        ("farbe: rot", "'farbe' is not supported here"),
        ("inhaltsverzeichnis: vielleicht", "expected 'ja' or 'nein'"),
        ("titelfolie: bild-01", "'titelfolie' is not supported here"),
    ],
)
def test_front_matter_mistakes(front: str, expected: str) -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate(f"---\ntitel: T\n{front}\n---\n# K\n")
    assert expected in error.value.reason


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice is not installed")
def test_libreoffice_opens_every_variant(tmp_path: Path) -> None:
    for variant in WordVariant:
        source = tmp_path / f"{variant.value}.docx"
        source.write_bytes(
            generate(REPORT.replace("---\n#", f"vorlage: {variant.value}\n---\n#", 1))
        )
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_path),
                str(source),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        assert (tmp_path / f"{variant.value}.pdf").stat().st_size > 1000
