"""The design model must agree with the PTA templates in source-templates/."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from pta_documents.design import colors, slides, word
from pta_documents.design.variants import SLIDES_SOURCES, WordVariant
from tests.conftest import REPO_ROOT, SOURCE_TEMPLATES

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"a": A, "p": P, "w": W}

WORD_FILES = [SOURCE_TEMPLATES / v.source_file for v in WordVariant]
SLIDE_FILES = [SOURCE_TEMPLATES / name for name in SLIDES_SOURCES.values()]


def xml(path: Path, part: str) -> etree._Element:
    with zipfile.ZipFile(path) as package:
        return etree.fromstring(package.read(part))


def scheme_colors(theme: etree._Element) -> dict[str, str]:
    result: dict[str, str] = {}
    scheme = theme.find(".//a:clrScheme", NS)
    assert scheme is not None
    for slot in scheme:
        value = slot[0].get("val") if slot[0].tag == f"{{{A}}}srgbClr" else slot[0].get("lastClr")
        result[etree.QName(slot).localname] = str(value)
    return result


def expected_scheme(text: str) -> dict[str, str]:
    return {
        "dk1": text,
        "lt1": colors.WHITE,
        "dk2": colors.GREY_LIGHT,
        "lt2": colors.YELLOW,
        "accent1": colors.ACCENTS[0],
        "accent2": colors.ACCENTS[1],
        "accent3": colors.ACCENTS[2],
        "accent4": colors.ACCENTS[3],
        "accent5": colors.ACCENTS[4],
        "accent6": colors.ACCENTS[5],
        "hlink": colors.DARK_BLUE,
        "folHlink": colors.GREY_DARK,
    }


@pytest.mark.parametrize("path", WORD_FILES, ids=lambda p: p.name)
def test_word_theme(path: Path) -> None:
    theme = xml(path, "word/theme/theme1.xml")
    assert scheme_colors(theme) == expected_scheme(colors.TEXT_WORD)
    major = theme.find(".//a:majorFont/a:latin", NS)
    assert major is not None and major.get("typeface") == slides.HEADING_FONT


@pytest.mark.parametrize("path", SLIDE_FILES, ids=lambda p: p.name)
def test_slides_theme(path: Path) -> None:
    theme = xml(path, "ppt/theme/theme1.xml")
    assert scheme_colors(theme) == expected_scheme(colors.TEXT_SLIDES)
    major = theme.find(".//a:majorFont/a:latin", NS)
    minor = theme.find(".//a:minorFont/a:latin", NS)
    assert major is not None and major.get("typeface") == slides.HEADING_FONT
    assert minor is not None and minor.get("typeface") == slides.BODY_FONT
    custom = [c.get("val") for c in theme.iterfind(".//a:custClrLst//a:srgbClr", NS)]
    assert tuple(custom) == colors.SIGNALS


@pytest.mark.parametrize("path", WORD_FILES, ids=lambda p: p.name)
def test_word_styles_exist(path: Path) -> None:
    styles = xml(path, "word/styles.xml")
    names = {s.get(f"{{{W}}}val") for s in styles.iterfind("w:style/w:name", NS)}
    s = word.STYLES
    required = {
        s.normal,
        s.normal_bold,
        s.title,
        s.subtitle,
        s.author,
        *s.headings,
        s.sub_heading,
        s.list_bullet,
        s.list_number,
        s.caption,
        s.footnote_text,
        s.footnote_reference,
        s.table,
    }
    assert required <= names
    # The landscape templates lack these; the generator copies them from the portrait one.
    portrait = xml(SOURCE_TEMPLATES / WordVariant.PORTRAIT.source_file, "word/styles.xml")
    portrait_names = {s.get(f"{{{W}}}val") for s in portrait.iterfind("w:style/w:name", NS)}
    assert set(word.BORROWED_STYLES) <= portrait_names
    # The generator adds these two itself.
    assert s.code not in names
    assert s.quote not in names


def style(styles: etree._Element, name: str) -> etree._Element:
    found = styles.xpath("w:style[w:name/@w:val=$n]", namespaces=NS, n=name)
    assert isinstance(found, list) and found
    element = found[0]
    assert isinstance(element, etree._Element)
    return element


@pytest.mark.parametrize("path", WORD_FILES, ids=lambda p: p.name)
def test_word_style_colors(path: Path) -> None:
    styles = xml(path, "word/styles.xml")
    normal = style(styles, word.STYLES.normal)
    assert normal.find("w:rPr/w:color", NS).get(f"{{{W}}}val") == colors.TEXT_WORD  # type: ignore[union-attr]
    table = style(styles, word.STYLES.table)
    header_fill = table.find("w:tblStylePr[@w:type='firstRow']/w:tcPr/w:shd", NS)
    assert header_fill is not None and header_fill.get(f"{{{W}}}fill") == colors.PTA_BLUE
    rule = table.find("w:tblPr/w:tblBorders/w:insideH", NS)
    assert rule is not None and rule.get(f"{{{W}}}color") == colors.GREY_MID
    link = style(
        xml(SOURCE_TEMPLATES / WordVariant.PORTRAIT.source_file, "word/styles.xml"),
        word.STYLES.hyperlink,
    )
    assert link.find("w:rPr/w:color", NS).get(f"{{{W}}}val") == colors.DARK_BLUE  # type: ignore[union-attr]


def layouts(path: Path) -> dict[str, etree._Element]:
    result: dict[str, etree._Element] = {}
    with zipfile.ZipFile(path) as package:
        for name in package.namelist():
            if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
                layout = etree.fromstring(package.read(name))
                c_sld = layout.find("p:cSld", NS)
                assert c_sld is not None
                result[str(c_sld.get("name"))] = layout
    return result


def placeholder_indices(layout: etree._Element) -> set[int]:
    return {int(ph.get("idx", "0")) for ph in layout.iterfind(".//p:nvPr/p:ph", NS)}


@pytest.mark.parametrize("path", SLIDE_FILES, ids=lambda p: p.name)
def test_slide_layouts_and_placeholders(path: Path) -> None:
    found = layouts(path)
    lay, ph = slides.LAYOUTS, slides.PLACEHOLDERS
    for name in vars(lay).values():
        assert name in found, name
    for title in (lay.title_image_01, lay.title_image_02, lay.title_industries, lay.title_plain):
        assert {ph.title, ph.subtitle, ph.byline} <= placeholder_indices(found[title])
    assert {ph.title, ph.chapter_number} <= placeholder_indices(found[lay.chapter])
    assert {ph.title, ph.body} <= placeholder_indices(found[lay.title_and_text])
    assert {ph.body, ph.second_body} <= placeholder_indices(found[lay.title_and_two_texts])
    assert {ph.body, ph.picture} <= placeholder_indices(found[lay.title_text_image])
    assert ph.picture in placeholder_indices(found[lay.title_image])


def test_content_area_is_the_body_of_title_and_text() -> None:
    layout = layouts(SOURCE_TEMPLATES / "PTA-Powerpoint-Basisvorlage.potx")[
        slides.LAYOUTS.title_and_text
    ]
    body = layout.xpath(".//p:sp[p:nvSpPr/p:nvPr/p:ph/@idx='12']/p:spPr/a:xfrm", namespaces=NS)
    assert isinstance(body, list) and body
    xfrm = body[0]
    assert isinstance(xfrm, etree._Element)
    off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
    assert off is not None and ext is not None
    area = slides.CONTENT_AREA
    tolerance = slides.cm(0.01)
    assert abs(int(off.get("x", "0")) - area.left) <= tolerance
    assert abs(int(off.get("y", "0")) - area.top) <= tolerance
    assert abs(int(ext.get("cx", "0")) - area.width) <= tolerance
    assert abs(int(ext.get("cy", "0")) - area.height) <= tolerance


def test_master_text_level_sizes() -> None:
    master = xml(
        SOURCE_TEMPLATES / "PTA-Powerpoint-Basisvorlage.potx", "ppt/slideMasters/slideMaster1.xml"
    )
    sizes = [
        int(str(master.find(f"p:txStyles/p:bodyStyle/a:lvl{n}pPr/a:defRPr", NS).get("sz"))) / 100  # type: ignore[union-attr]
        for n in range(1, 6)
    ]
    assert tuple(sizes) == slides.LEVEL_SIZES_PT


HEX = re.compile(r"""["'][0-9A-Fa-f]{6}["']""")


def test_no_colour_values_outside_the_colour_module() -> None:
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "src").rglob("*.py")
        if path.name != "colors.py" and HEX.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
