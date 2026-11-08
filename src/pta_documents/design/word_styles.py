"""The paragraph formats of the PTA Word templates, read from their ``styles.xml``.

The PDF generator (E05) lays text out like Word does with the same Markdown: every block takes
the size, weight, colour, spacing and indents of the Word style the DOCX generator uses for it
(``design/word.STYLES``). The values come from the embedded templates, never from a second
table in code: styles are resolved over ``w:basedOn`` and ``w:docDefaults``, colours over the
theme, indents of numbered styles (headings, lists) from ``numbering.xml``, the page from the
``w:sectPr`` of the body.

Styles the templates lack (``word.BORROWED_STYLES`` in the landscape ones) are taken from the
portrait template, as the DOCX generator does.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from lxml import etree

from pta_documents.design import templates, word
from pta_documents.design.variants import WordVariant

W: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
TWIPS_PER_POINT: Final = 20
POINTS_PER_CM: Final = 72 / 2.54
SINGLE_LINE: Final = 240
"""``w:line`` of single spacing with ``w:lineRule="auto"``."""

_THEME_SLOTS: Final = {
    "text1": "dk1",
    "dark1": "dk1",
    "background1": "lt1",
    "light1": "lt1",
    "text2": "dk2",
    "dark2": "dk2",
    "background2": "lt2",
    "light2": "lt2",
    "hyperlink": "hlink",
    "followedHyperlink": "folHlink",
    **{f"accent{n}": f"accent{n}" for n in range(1, 7)},
}


def _w(name: str) -> str:
    return f"{{{W}}}{name}"


class LineRule(StrEnum):
    """How ``line_pt`` is meant (``w:lineRule``)."""

    AUTO = "auto"
    """A multiple of single spacing: ``line_pt`` / 12 lines."""
    AT_LEAST = "atLeast"
    EXACT = "exact"


@dataclass(frozen=True)
class NumberingLevel:
    """One level of a list or heading numbering (``w:lvl``)."""

    format: str
    """``decimal``, ``bullet`` …"""
    text: str
    """``%1.%2`` for numbers; the bullet character for bullets."""
    left_pt: float
    hanging_pt: float
    color: str | None = None
    """The colour of the number or bullet; None: the text colour."""
    font: str | None = None
    """The font of the bullet (``Wingdings``) if it has its own."""


@dataclass(frozen=True)
class ParagraphFormat:
    """A paragraph style with everything inherited, in points."""

    name: str
    size_pt: float
    bold: bool = False
    italic: bool = False
    caps: bool = False
    underline: bool = False
    color: str | None = None
    """RGB hex; None: automatic (black)."""
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    line_pt: float = 12.0
    line_rule: LineRule = LineRule.AUTO
    left_indent_pt: float = 0.0
    hanging_pt: float = 0.0
    """Positive: the first line starts this much further left (numbers and bullets)."""
    keep_next: bool = False
    keep_lines: bool = False
    numbering: tuple[int, int] | None = None
    """``(numId, ilvl)`` of a numbered style."""

    def leading(self, natural: float) -> float:
        """The line height in points for a font whose single line is ``natural`` × size."""
        single = self.size_pt * natural
        match self.line_rule:
            case LineRule.AUTO:
                return single * self.line_pt / (SINGLE_LINE / TWIPS_PER_POINT)
            case LineRule.AT_LEAST:
                return max(self.line_pt, single)
            case LineRule.EXACT:
                return self.line_pt


@dataclass(frozen=True)
class CharacterFormat:
    """A character style (``Hyperlink``, ``footnote reference``)."""

    name: str
    color: str | None = None
    underline: bool = False
    bold: bool = False
    superscript: bool = False


@dataclass(frozen=True)
class TableFormat:
    """The table style ``PTA``: rules between and under rows, a filled header row."""

    rule_color: str
    rule_pt: float
    header_fill: str
    header_color: str
    text_color: str | None
    cell_left_pt: float
    cell_right_pt: float
    space_after_pt: float
    line_pt: float
    line_rule: LineRule


@dataclass(frozen=True)
class PageSetup:
    """Paper and margins of the body section (``w:pgSz``, ``w:pgMar``), in points."""

    width_pt: float
    height_pt: float
    top_pt: float
    bottom_pt: float
    left_pt: float
    right_pt: float
    header_pt: float
    footer_pt: float

    @property
    def text_width_pt(self) -> float:
        return self.width_pt - self.left_pt - self.right_pt

    @property
    def text_height_pt(self) -> float:
        return self.height_pt - self.top_pt - self.bottom_pt


@dataclass(frozen=True)
class WordDesign:
    """What the PDF generator reads from one PTA Word template."""

    paragraphs: Mapping[str, ParagraphFormat]
    """By ``w:name`` (``Normal``, ``heading 1``, ``Standard fett`` …)."""
    characters: Mapping[str, CharacterFormat]
    numbering: Mapping[tuple[int, int], NumberingLevel]
    """By ``(numId, ilvl)``."""
    table: TableFormat
    page: PageSetup
    theme: Mapping[str, str]
    """The theme colours by slot (``dk1``, ``accent1`` …)."""
    default_tab_pt: float

    def paragraph(self, name: str) -> ParagraphFormat:
        return self.paragraphs[name]

    def character(self, name: str) -> CharacterFormat:
        return self.characters[name]

    def level(self, style: ParagraphFormat, ilvl: int | None = None) -> NumberingLevel | None:
        """The numbering level of a numbered ``style`` (its own level, or ``ilvl``)."""
        if style.numbering is None:
            return None
        num_id, own = style.numbering
        return self.numbering.get((num_id, own if ilvl is None else ilvl))


def read(variant: WordVariant) -> WordDesign:
    """The design of the embedded template of ``variant``."""
    parts = _parts(variant)
    borrowed = _parts(WordVariant.PORTRAIT) if variant is not WordVariant.PORTRAIT else parts
    return _design(parts, borrowed)


def _parts(variant: WordVariant) -> dict[str, etree._Element]:
    names = (
        "word/styles.xml",
        "word/numbering.xml",
        "word/document.xml",
        "word/settings.xml",
        "word/theme/theme1.xml",
    )
    with zipfile.ZipFile(io.BytesIO(templates.word_template(variant))) as archive:
        return {name: etree.fromstring(archive.read(name)) for name in names}


def _design(parts: dict[str, etree._Element], borrowed: dict[str, etree._Element]) -> WordDesign:
    theme = _theme(parts["word/theme/theme1.xml"])
    styles = _Styles(parts["word/styles.xml"], theme)
    borrowed_styles = _Styles(
        borrowed["word/styles.xml"], _theme(borrowed["word/theme/theme1.xml"])
    )
    numbering = _numbering(parts["word/numbering.xml"], theme)

    paragraphs: dict[str, ParagraphFormat] = {}
    characters: dict[str, CharacterFormat] = {}
    for name in styles.names("paragraph"):
        paragraphs[name] = styles.paragraph(name, numbering)
    for name in styles.names("character"):
        characters[name] = styles.character(name)
    for name in word.BORROWED_STYLES:
        if name in paragraphs or name in characters:
            continue
        if name in borrowed_styles.names("paragraph"):
            paragraphs[name] = borrowed_styles.paragraph(name, numbering)
        elif name in borrowed_styles.names("character"):
            characters[name] = borrowed_styles.character(name)
    tab = parts["word/settings.xml"].find(_w("defaultTabStop"))
    return WordDesign(
        paragraphs=paragraphs,
        characters=characters,
        numbering=numbering,
        table=styles.table(word.STYLES.table),
        page=_page(parts["word/document.xml"]),
        theme=theme,
        default_tab_pt=_twips(tab, "val") or 0.0,
    )


def _theme(root: etree._Element) -> dict[str, str]:
    result: dict[str, str] = {}
    scheme = root.find(f".//{{{A}}}clrScheme")
    if scheme is None:
        return result
    for slot in scheme:
        rgb = slot.find(f"{{{A}}}srgbClr")
        system = slot.find(f"{{{A}}}sysClr")
        if rgb is not None:
            result[etree.QName(slot).localname] = str(rgb.get("val")).upper()
        elif system is not None and system.get("lastClr"):
            result[etree.QName(slot).localname] = str(system.get("lastClr")).upper()
    return result


def _color(element: etree._Element | None, theme: Mapping[str, str]) -> str | None:
    """The colour of a ``w:color``: the theme colour if named (as Word does), else ``w:val``;
    None for ``auto``."""
    if element is None:
        return None
    slot = _THEME_SLOTS.get(str(element.get(_w("themeColor"), "")))
    if slot is not None and slot in theme:
        return theme[slot]
    value = str(element.get(_w("val"), "auto"))
    return None if value == "auto" else value.upper()


def _fill(element: etree._Element | None, theme: Mapping[str, str]) -> str | None:
    if element is None:
        return None
    slot = _THEME_SLOTS.get(str(element.get(_w("themeFill"), "")))
    if slot is not None and slot in theme:
        return theme[slot]
    value = str(element.get(_w("fill"), "auto"))
    return None if value == "auto" else value.upper()


def _on(element: etree._Element | None) -> bool | None:
    """A toggle property (``w:b``, ``w:caps``): None when absent."""
    if element is None:
        return None
    return str(element.get(_w("val"), "true")).lower() not in ("0", "false", "off", "none")


def _twips(element: etree._Element | None, attribute: str) -> float | None:
    if element is None:
        return None
    value = element.get(_w(attribute))
    return None if value is None else int(value) / TWIPS_PER_POINT


@dataclass
class _Values:
    """Properties collected along a style chain; the last one set wins."""

    size_pt: float = 11.0
    bold: bool = False
    italic: bool = False
    caps: bool = False
    underline: bool = False
    color: str | None = None
    superscript: bool = False
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    line_pt: float = 12.0
    line_rule: LineRule = LineRule.AUTO
    left_indent_pt: float | None = None
    hanging_pt: float | None = None
    keep_next: bool = False
    keep_lines: bool = False
    num_id: int | None = None
    ilvl: int | None = None


class _Styles:
    def __init__(self, root: etree._Element, theme: Mapping[str, str]) -> None:
        self.theme = theme
        self.by_id: dict[str, etree._Element] = {}
        self.by_name: dict[tuple[str, str], etree._Element] = {}
        for style in root.iter(_w("style")):
            self.by_id[str(style.get(_w("styleId")))] = style
            name = style.find(_w("name"))
            if name is not None:
                self.by_name[(str(style.get(_w("type"))), str(name.get(_w("val"))))] = style
        self.defaults = root.find(_w("docDefaults"))

    def names(self, kind: str) -> list[str]:
        return [name for (k, name) in self.by_name if k == kind]

    def chain(self, style: etree._Element) -> list[etree._Element]:
        """``style`` and its ``w:basedOn`` ancestors, the root first."""
        result: list[etree._Element] = []
        current: etree._Element | None = style
        while current is not None and current not in result:
            result.insert(0, current)
            based = current.find(_w("basedOn"))
            current = self.by_id.get(str(based.get(_w("val")))) if based is not None else None
        return result

    def values(self, style: etree._Element) -> _Values:
        values = _Values()
        if self.defaults is not None:
            self._apply(values, self.defaults.find(f"{_w('pPrDefault')}/{_w('pPr')}"), None)
            self._apply(values, None, self.defaults.find(f"{_w('rPrDefault')}/{_w('rPr')}"))
        for link in self.chain(style):
            self._apply(values, link.find(_w("pPr")), link.find(_w("rPr")))
        return values

    def _apply(
        self, values: _Values, p_pr: etree._Element | None, r_pr: etree._Element | None
    ) -> None:
        if p_pr is not None:
            spacing = p_pr.find(_w("spacing"))
            if spacing is not None:
                before = _twips(spacing, "before")
                after = _twips(spacing, "after")
                if before is not None:
                    values.space_before_pt = before
                if after is not None:
                    values.space_after_pt = after
                line = spacing.get(_w("line"))
                if line is not None:
                    values.line_rule = LineRule(spacing.get(_w("lineRule"), "auto"))
                    values.line_pt = int(line) / TWIPS_PER_POINT
            indent = p_pr.find(_w("ind"))
            if indent is not None:
                left = _twips(indent, "left")
                if left is None:
                    left = _twips(indent, "start")
                if left is not None:
                    values.left_indent_pt = left
                hanging = _twips(indent, "hanging")
                first = _twips(indent, "firstLine")
                if hanging is not None:
                    values.hanging_pt = hanging
                elif first is not None:
                    values.hanging_pt = -first
            for name, attribute in (("keepNext", "keep_next"), ("keepLines", "keep_lines")):
                state = _on(p_pr.find(_w(name)))
                if state is not None:
                    setattr(values, attribute, state)
            num = p_pr.find(_w("numPr"))
            if num is not None:
                num_id = num.find(_w("numId"))
                ilvl = num.find(_w("ilvl"))
                if num_id is not None:
                    values.num_id = int(str(num_id.get(_w("val"))))
                values.ilvl = int(str(ilvl.get(_w("val")))) if ilvl is not None else 0
        if r_pr is not None:
            size = r_pr.find(_w("sz"))
            if size is not None:
                values.size_pt = int(str(size.get(_w("val")))) / 2
            for name, attribute in (("b", "bold"), ("i", "italic"), ("caps", "caps")):
                state = _on(r_pr.find(_w(name)))
                if state is not None:
                    setattr(values, attribute, state)
            underline = r_pr.find(_w("u"))
            if underline is not None:
                values.underline = str(underline.get(_w("val"), "single")) != "none"
            color = r_pr.find(_w("color"))
            if color is not None:
                values.color = _color(color, self.theme)
            align = r_pr.find(_w("vertAlign"))
            if align is not None:
                values.superscript = align.get(_w("val")) == "superscript"

    def paragraph(
        self, name: str, numbering: Mapping[tuple[int, int], NumberingLevel]
    ) -> ParagraphFormat:
        values = self.values(self.by_name[("paragraph", name)])
        level = None
        if values.num_id is not None:
            level = numbering.get((values.num_id, values.ilvl or 0))
        left = values.left_indent_pt
        hanging = values.hanging_pt
        if level is not None:
            # The level's indent applies unless the style sets its own.
            left = level.left_pt if left is None else left
            hanging = level.hanging_pt if hanging is None else hanging
        return ParagraphFormat(
            name=name,
            size_pt=values.size_pt,
            bold=values.bold,
            italic=values.italic,
            caps=values.caps,
            underline=values.underline,
            color=values.color,
            space_before_pt=values.space_before_pt,
            space_after_pt=values.space_after_pt,
            line_pt=values.line_pt,
            line_rule=values.line_rule,
            left_indent_pt=left or 0.0,
            hanging_pt=hanging or 0.0,
            keep_next=values.keep_next,
            keep_lines=values.keep_lines,
            numbering=None if values.num_id is None else (values.num_id, values.ilvl or 0),
        )

    def character(self, name: str) -> CharacterFormat:
        style = self.by_name[("character", name)]
        values = _Values()
        for link in self.chain(style):
            self._apply(values, None, link.find(_w("rPr")))
        return CharacterFormat(
            name=name,
            color=values.color,
            underline=values.underline,
            bold=values.bold,
            superscript=values.superscript,
        )

    def table(self, name: str) -> TableFormat:
        style = self.by_name[("table", name)]
        values = _Values()
        rule_color: str | None = None
        rule_pt = 0.0
        left = right = 0.0
        for link in self.chain(style):
            self._apply(values, link.find(_w("pPr")), link.find(_w("rPr")))
            borders = link.find(f"{_w('tblPr')}/{_w('tblBorders')}")
            if borders is not None:
                rule = borders.find(_w("insideH"))
                if rule is None:
                    rule = borders.find(_w("bottom"))
                if rule is not None:
                    rule_color = _color(rule, self.theme)
                    rule_pt = int(str(rule.get(_w("sz"), "4"))) / 8
            margins = link.find(f"{_w('tblPr')}/{_w('tblCellMar')}")
            if margins is not None:
                left = _twips(margins.find(_w("left")), "w") or 0.0
                right = _twips(margins.find(_w("right")), "w") or 0.0
        header_fill: str | None = None
        header_color: str | None = None
        for part in style.iter(_w("tblStylePr")):
            if part.get(_w("type")) == "firstRow":
                header_fill = _fill(part.find(f"{_w('tcPr')}/{_w('shd')}"), self.theme)
                header_color = _color(part.find(f"{_w('rPr')}/{_w('color')}"), self.theme)
        if rule_color is None or header_fill is None or header_color is None:
            raise ValueError(f"the table style {name!r} lacks rules or a header row")
        return TableFormat(
            rule_color=rule_color,
            rule_pt=rule_pt,
            header_fill=header_fill,
            header_color=header_color,
            text_color=values.color,
            cell_left_pt=left,
            cell_right_pt=right,
            space_after_pt=values.space_after_pt,
            line_pt=values.line_pt,
            line_rule=values.line_rule,
        )


def _numbering(
    root: etree._Element, theme: Mapping[str, str]
) -> dict[tuple[int, int], NumberingLevel]:
    abstracts: dict[str, etree._Element] = {
        str(a.get(_w("abstractNumId"))): a for a in root.iter(_w("abstractNum"))
    }
    result: dict[tuple[int, int], NumberingLevel] = {}
    for num in root.iter(_w("num")):
        reference = num.find(_w("abstractNumId"))
        if reference is None:
            continue
        abstract = abstracts.get(str(reference.get(_w("val"))))
        if abstract is None:
            continue
        num_id = int(str(num.get(_w("numId"))))
        for level in abstract.iter(_w("lvl")):
            ilvl = int(str(level.get(_w("ilvl"))))
            fmt = level.find(_w("numFmt"))
            text = level.find(_w("lvlText"))
            indent = level.find(f"{_w('pPr')}/{_w('ind')}")
            fonts = level.find(f"{_w('rPr')}/{_w('rFonts')}")
            result[(num_id, ilvl)] = NumberingLevel(
                format=str(fmt.get(_w("val"))) if fmt is not None else "decimal",
                text=str(text.get(_w("val"))) if text is not None else "",
                left_pt=(_twips(indent, "left") or _twips(indent, "start") or 0.0),
                hanging_pt=_twips(indent, "hanging") or 0.0,
                color=_color(level.find(f"{_w('rPr')}/{_w('color')}"), theme),
                font=str(fonts.get(_w("ascii")))
                if fonts is not None and fonts.get(_w("ascii"))
                else None,
            )
    return result


def _page(document: etree._Element) -> PageSetup:
    sections = list(document.iter(_w("sectPr")))
    if not sections:
        raise ValueError("the template has no section properties")
    section = sections[-1]
    size = section.find(_w("pgSz"))
    margins = section.find(_w("pgMar"))
    if size is None or margins is None:
        raise ValueError("the template's section lacks page size or margins")

    def get(element: etree._Element, name: str) -> float:
        return int(str(element.get(_w(name), "0"))) / TWIPS_PER_POINT

    return PageSetup(
        width_pt=get(size, "w"),
        height_pt=get(size, "h"),
        top_pt=get(margins, "top"),
        bottom_pt=get(margins, "bottom"),
        left_pt=get(margins, "left"),
        right_pt=get(margins, "right"),
        header_pt=get(margins, "header"),
        footer_pt=get(margins, "footer"),
    )
