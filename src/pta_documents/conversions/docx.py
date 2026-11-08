"""DOCX to Markdown (port of DocLibs ``DocxConverter``)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import BinaryIO, Final

from lxml import etree

from pta_documents.conversions.openxml import OpenXmlPackage, guard, read_input
from pta_documents.conversions.options import ConversionOptions, ResourceCollector
from pta_documents.design import colors, icons, word
from pta_documents.design.variants import TEXTS
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown import text as md
from pta_documents.markdown import typography
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.icon import markdown as icon_markdown

W: Final = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MC: Final = "http://schemas.openxmlformats.org/markup-compatibility/2006"
GANTT_CELL: Final = "■"
"""An empty cell shaded in PTA blue or light blue: a column a task of a Gantt table runs in."""
GANTT_FILLS: Final = (colors.PTA_BLUE, colors.LIGHT_BLUE)
A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP: Final = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
C: Final = "http://schemas.openxmlformats.org/drawingml/2006/chart"
V: Final = "urn:schemas-microsoft-com:vml"
PTA: Final = "urn:pta-documents:wordprocessingml"
"""The DOCX generator's own markup: ``pta:codeLanguage`` holds the language of a code block."""

DOCUMENT_PART: Final = "word/document.xml"
HARD_BREAK: Final = "\\\n"
"""A backslash break, because ``normalize`` trims the two-space form away."""
NOTE_STYLES: Final = (word.STYLES.note, word.STYLES.note_important)
"""The styles of alerts and boxes the DOCX generator writes (E03-S03): read back as quotes."""
ALERT_KINDS: Final = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
ALERT_WORDS: Final = tuple(
    (kind, texts.alert(kind)) for texts in TEXTS.values() for kind in ALERT_KINDS
)
"""The words a generated alert starts with, and its kind."""


def w(name: str) -> str:
    return f"{{{W}}}{name}"


@dataclass(frozen=True)
class _Context:
    package: OpenXmlPackage
    rels: dict[str, str]
    styles: dict[str, str]
    style_names: dict[str, str]
    """Style id (lower case) -> name."""
    numbering_is_ordered: dict[tuple[str, int], bool]
    images: ResourceCollector | None


Segment = tuple[str, str]
"""Text and its emphasis marker (``**``, ``*``, ``***`` or empty)."""


class DocxConverter:
    format: Final = DocumentFormat.DOCX

    def can_convert(self, format: DocumentFormat) -> bool:
        return format is DocumentFormat.DOCX

    def convert(
        self, data: bytes | BinaryIO, options: ConversionOptions | None = None
    ) -> MarkdownDocument:
        options = options or ConversionOptions()
        content = read_input(data)
        return guard(DocumentFormat.DOCX, lambda: self._convert(content, options))

    def _convert(self, data: bytes, options: ConversionOptions) -> MarkdownDocument:
        package = OpenXmlPackage(data)
        try:
            document = package.read_xml(DOCUMENT_PART)
            body = document.find(w("body")) if document is not None else None
            if body is None:
                raise DocumentConversionError(DocumentFormat.DOCX, "word/document.xml has no body.")
            context = _Context(
                package,
                package.relationships(DOCUMENT_PART),
                _load_styles(package),
                _load_style_names(package),
                _load_numbering(package),
                ResourceCollector(options.resource_path_prefix) if options.include_images else None,
            )
            out: list[str] = []
            for block in body:
                _render_block(block, context, out)
            metadata: dict[str, str] = {}
            package.add_core_properties(metadata)
            text = md.normalize("".join(out))
            return MarkdownDocument(
                typography.plain(text) if options.plain_quotes else text,
                tuple(context.images.resources) if context.images else (),
                metadata,
            )
        finally:
            package.close()


def _load_styles(package: OpenXmlPackage) -> dict[str, str]:
    result: dict[str, str] = {}
    styles = package.read_xml("word/styles.xml")
    if styles is None:
        return result
    for style in styles.iterfind(w("style")):
        style_id = style.get(w("styleId"))
        if style_id is None:
            continue
        name_element = style.find(w("name"))
        name = name_element.get(w("val"), style_id) if name_element is not None else style_id
        result[style_id.lower()] = _classify_heading(style_id, name)
    return result


def _load_style_names(package: OpenXmlPackage) -> dict[str, str]:
    result: dict[str, str] = {}
    styles = package.read_xml("word/styles.xml")
    if styles is None:
        return result
    for style in styles.iterfind(w("style")):
        style_id = style.get(w("styleId"))
        name = style.find(w("name"))
        if style_id is not None and name is not None:
            result[style_id.lower()] = name.get(w("val"), style_id)
    return result


def _load_numbering(package: OpenXmlPackage) -> dict[tuple[str, int], bool]:
    result: dict[tuple[str, int], bool] = {}
    numbering = package.read_xml("word/numbering.xml")
    if numbering is None:
        return result
    abstract_formats: dict[str, dict[int, bool]] = {}
    for abstract in numbering.iterfind(w("abstractNum")):
        abstract_id = abstract.get(w("abstractNumId"))
        if abstract_id is None:
            continue
        levels: dict[int, bool] = {}
        for lvl in abstract.iterfind(w("lvl")):
            level = _int(lvl.get(w("ilvl")))
            fmt = lvl.find(w("numFmt"))
            value = (fmt.get(w("val")) if fmt is not None else None) or "bullet"
            levels[level] = value.lower() not in ("bullet", "none")
        abstract_formats[abstract_id] = levels
    for num in numbering.iterfind(w("num")):
        num_id = num.get(w("numId"))
        abstract_ref = num.find(w("abstractNumId"))
        abstract_id = abstract_ref.get(w("val")) if abstract_ref is not None else None
        if num_id is None or abstract_id is None or abstract_id not in abstract_formats:
            continue
        for level, ordered in abstract_formats[abstract_id].items():
            result[(num_id, level)] = ordered
    return result


def _int(value: str | None) -> int:
    try:
        return int(value) if value is not None else 0
    except ValueError:
        return 0


def _render_block(block: etree._Element, context: _Context, out: list[str]) -> None:
    if block.tag == w("p"):
        _render_paragraph(block, context, out)
    elif block.tag == w("tbl"):
        _render_table(block, context, out)
    elif block.tag in (w("sdt"), w("customXml")):
        content = block.find(w("sdtContent")) if block.tag == w("sdt") else block
        if content is not None:
            for child in content:
                _render_block(child, context, out)


def _in_fallback(element: etree._Element) -> bool:
    return any(a.tag == f"{{{MC}}}Fallback" for a in element.iterancestors())


def _in_text_box(element: etree._Element) -> bool:
    return any(a.tag == w("txbxContent") for a in element.iterancestors())


def _render_paragraph(paragraph: etree._Element, context: _Context, out: list[str]) -> None:
    _render_paragraph_text(paragraph, context, out)
    for chart in paragraph.iter(f"{{{C}}}chart"):
        if not _in_fallback(chart) and not _in_text_box(chart):
            _render_chart(chart, context, out)
    # Text boxes anchored in this paragraph; mc:Fallback repeats what mc:Choice already holds.
    for box in paragraph.iter(w("txbxContent")):
        if _in_fallback(box):
            continue
        parts = [_render_runs(p, context).strip() for p in box.iter(w("p"))]
        text = " / ".join(p for p in parts if p)
        if not text:
            continue
        _ensure_blank_line(out)
        out.append("> [Text box] " + text.replace(HARD_BREAK, " ") + "\n\n")


def _render_paragraph_text(paragraph: etree._Element, context: _Context, out: list[str]) -> None:
    properties = paragraph.find(w("pPr"))
    style = properties.find(w("pStyle")) if properties is not None else None
    style_id = style.get(w("val")) if style is not None else None
    if style_id and context.style_names.get(style_id.lower()) == word.STYLES.code:
        _render_code(paragraph, properties, out)
        return
    text = _render_runs(paragraph, context).rstrip()
    heading = context.styles.get(style_id.lower(), "") if style_id else ""
    if not heading and style_id:
        heading = _classify_heading(style_id, style_id)

    if not text.strip():
        out.append("\n")
        return

    if heading in ("title", "h1", "h2", "h3", "h4", "h5", "h6"):
        _ensure_blank_line(out)
        level = 1 if heading == "title" else int(heading[1])
        out.append("#" * level + " " + text.replace(HARD_BREAK, " ").strip() + "\n\n")
        return

    if style_id and context.style_names.get(style_id.lower()) in NOTE_STYLES:
        _ensure_blank_line(out)
        out.append(_note(text) + "\n\n")
        return

    numbering = properties.find(w("numPr")) if properties is not None else None
    if numbering is not None:
        num_element = numbering.find(w("numId"))
        lvl_element = numbering.find(w("ilvl"))
        num_id = (num_element.get(w("val")) if num_element is not None else None) or "0"
        level = _int(lvl_element.get(w("val")) if lvl_element is not None else None)
        ordered = context.numbering_is_ordered.get((num_id, level), False)
        out.append(" " * (level * 2) + ("1. " if ordered else "- ") + text.lstrip() + "\n")
        return

    _ensure_blank_line(out)
    out.append(text + "\n\n")


def _render_chart(chart: etree._Element, context: _Context, out: list[str]) -> None:
    """A native chart (E03-S04) as a table of its data: a column of categories (no header),
    then one column per series, from the values Word caches in the chart part."""
    rel_id = chart.get(f"{{{R}}}id")
    part = context.rels.get(rel_id) if rel_id else None
    space = context.package.read_xml(part) if part else None
    if space is None:
        return
    series = list(space.iter(f"{{{C}}}ser"))
    if not series:
        return
    categories = _chart_points(series[0].find(f"{{{C}}}cat"))
    count = max(
        [max(categories, default=-1) + 1]
        + [max(_chart_points(s.find(f"{{{C}}}val")), default=-1) + 1 for s in series]
    )
    grid: list[list[str]] = [[""] + [md.escape(_series_name(s)) for s in series]]
    values = [_chart_points(s.find(f"{{{C}}}val")) for s in series]
    for index in range(count):
        row = [md.escape(categories.get(index, ""))]
        row += [_chart_number(v.get(index, "")) for v in values]
        grid.append(row)
    _ensure_blank_line(out)
    out.append(md.table(grid))


def _chart_points(element: etree._Element | None) -> dict[int, str]:
    """The cached points (``c:pt``) under ``element``, by index."""
    if element is None:
        return {}
    points: dict[int, str] = {}
    for point in element.iter(f"{{{C}}}pt"):
        value = point.find(f"{{{C}}}v")
        points[_int(point.get("idx"))] = (value.text or "") if value is not None else ""
    return points


def _series_name(series: etree._Element) -> str:
    text = series.find(f"{{{C}}}tx")
    if text is None:
        return ""
    return "".join(v.text or "" for v in text.iter(f"{{{C}}}v"))


def _chart_number(text: str) -> str:
    """A cached value as the ``chart`` block writes it: ``132`` rather than ``132.0``."""
    try:
        value = float(text)
    except ValueError:
        return md.escape(text)
    return str(int(value)) if value.is_integer() else repr(value)


def _render_code(
    paragraph: etree._Element, properties: etree._Element | None, out: list[str]
) -> None:
    """A paragraph in the style "Code" (one code block of the generator) as a fence, with the
    language the generator noted in ``pta:codeLanguage``."""
    parts: list[str] = []
    for node in paragraph.iter(w("t"), w("br"), w("cr"), w("tab")):
        if node.tag == w("t"):
            parts.append(node.text or "")
        elif node.tag == w("tab"):
            parts.append("\t")
        elif node.get(w("type")) not in ("page", "column"):
            parts.append("\n")
    code = "".join(parts)
    if not code.strip():
        return
    language = properties.find(f"{{{PTA}}}codeLanguage") if properties is not None else None
    info = (language.get(f"{{{PTA}}}val") or "") if language is not None else ""
    longest = max((len(run) for run in re.findall("`+", code)), default=0)
    fence = "`" * max(3, longest + 1)
    _ensure_blank_line(out)
    out.append(f"{fence}{info}\n{code}\n{fence}\n\n")


def _note(text: str) -> str:
    """A paragraph of an alert or box as a quote; one that starts with the bold word of an
    alert (``**Hinweis:**``) as that alert again."""
    for kind, word_ in ALERT_WORDS:
        alone = f"**{word_}:**"
        joined = f"**{word_}: "
        if text.startswith(alone):
            rest = text[len(alone) :].lstrip()
        elif text.startswith(joined):
            # Word merges the bold word with bold text after it.
            rest = "**" + text[len(joined) :]
        else:
            continue
        return f"> [!{kind}]\n> " + rest.replace("\n", "\n> ")
    return "> " + text.replace("\n", "\n> ")


def _is_picture_row(table: etree._Element, context: _Context) -> bool:
    style = table.find(f"{w('tblPr')}/{w('tblStyle')}")
    style_id = style.get(w("val")) if style is not None else None
    return bool(style_id) and context.style_names.get(str(style_id).lower()) == (
        word.STYLES.picture_row
    )


def _render_picture_row(table: etree._Element, context: _Context, out: list[str]) -> None:
    """A row of pictures (E03-S03): the pictures in one paragraph, then their captions."""
    pictures: list[str] = []
    captions: list[str] = []
    for paragraph in table.iter(w("p")):
        text = _render_runs(paragraph, context).strip()
        if not text:
            continue
        if next(paragraph.iter(w("drawing")), None) is not None:
            pictures.append(text)
        else:
            captions.append(text)
    if pictures:
        _ensure_blank_line(out)
        out.append(" ".join(pictures) + "\n\n")
    for caption in captions:
        _ensure_blank_line(out)
        out.append(caption + "\n\n")


def _render_table(table: etree._Element, context: _Context, out: list[str]) -> None:
    if _is_picture_row(table, context):
        _render_picture_row(table, context, out)
        return
    grid: list[list[str]] = []
    for row in table.iterfind(w("tr")):
        cells: list[str] = []
        for cell in row.iterfind(w("tc")):
            # Nested tables are flattened into the cell.
            parts = [
                _render_runs(p, context).strip() for p in cell.iter(w("p")) if not _in_text_box(p)
            ]
            text = "<br>".join(p for p in parts if p)
            cells.append(text or (GANTT_CELL if _is_running(cell) else ""))
        grid.append(cells)
    if all(not c for r in grid for c in r):
        return
    _ensure_blank_line(out)
    out.append(md.table(grid))


def _is_running(cell: etree._Element) -> bool:
    """Whether an empty cell is shaded like the columns a task runs in (Gantt table, E15-S01)."""
    shading = cell.find(f"{w('tcPr')}/{w('shd')}")
    fill = shading.get(w("fill")) if shading is not None else None
    return fill is not None and fill.upper() in GANTT_FILLS


def _render_runs(container: etree._Element, context: _Context) -> str:
    segments: list[Segment] = []
    _render_inline(container, context, segments)
    return _emit(segments)


def _emit(segments: list[Segment]) -> str:
    """Adjacent runs with the same emphasis are merged, because Word splits runs mid-word."""
    out: list[str] = []
    i = 0
    while i < len(segments):
        mark = segments[i][1]
        buffer: list[str] = []
        while i < len(segments) and (
            segments[i][1] == mark or (not segments[i][0].strip() and mark)
        ):
            buffer.append(segments[i][0])
            i += 1
        text = "".join(buffer)
        if not mark or not text.strip():
            out.append(text)
            continue
        # Surrounding whitespace stays outside the emphasis markers.
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()) :]
        out.append(lead + mark + text.strip() + mark + trail)
    return "".join(out)


_TRANSPARENT: Final = {w("smartTag"), w("ins"), w("fldSimple"), w("customXml"), w("moveTo")}


def _render_inline(parent: etree._Element, context: _Context, segments: list[Segment]) -> None:
    for node in parent:
        if node.tag == w("r"):
            _render_run(node, context, segments)
        elif node.tag == w("hyperlink"):
            inner: list[Segment] = []
            _render_inline(node, context, inner)
            text = _emit(inner)
            rel_id = node.get(f"{{{R}}}id")
            target = context.rels.get(rel_id) if rel_id else None
            if target is not None and text.strip():
                segments.append((f"[{text}]({md.destination(target)})", ""))
            else:
                segments.append((text, ""))
        elif node.tag == w("sdt"):
            content = node.find(w("sdtContent"))
            if content is not None:
                _render_inline(content, context, segments)
        elif node.tag in _TRANSPARENT:
            _render_inline(node, context, segments)


def _render_run(run: etree._Element, context: _Context, segments: list[Segment]) -> None:
    properties = run.find(w("rPr"))
    bold = _is_on(properties.find(w("b")) if properties is not None else None)
    italic = _is_on(properties.find(w("i")) if properties is not None else None)
    content: list[str] = []
    icon = False
    for child in run:
        after_icon, icon = icon, False
        if child.tag == w("drawing") and (name := _icon(child)) is not None:
            # A bundled icon of the generator (E15-S03): its Markdown again, not a picture.
            content.append(icon_markdown(name))
            icon = True
        elif child.tag == w("t"):
            content.append(md.escape(child.text or ""))
        elif child.tag == w("tab"):
            content.append(" " if after_icon else "\t")
        elif child.tag == w("br") and child.get(w("type")) in ("page", "column"):
            # PTA: page and column breaks are layout, not text (DocLibs wrote a line break).
            continue
        elif child.tag in (w("br"), w("cr")):
            content.append(HARD_BREAK)
        elif child.tag == w("noBreakHyphen"):
            content.append("-")
    if content:
        mark = "***" if bold and italic else "**" if bold else "*" if italic else ""
        segments.append(("".join(content), mark))
    if context.images is not None:
        segments.extend((image, "") for image in _images(run, context))


def _icon(drawing: etree._Element) -> str | None:
    """The bundled icon a ``w:drawing`` shows (alternative text ``icon:check``); None: none."""
    doc_pr = next(drawing.iter(f"{{{WP}}}docPr"), None)
    return icons.from_alt(doc_pr.get("descr")) if doc_pr is not None else None


def _images(run: etree._Element, context: _Context) -> list[str]:
    """DrawingML pictures (a:blip) and legacy VML pictures (v:imagedata); icons aside."""
    assert context.images is not None
    result: list[str] = []
    for element in run.iter(f"{{{A}}}blip", f"{{{V}}}imagedata"):
        if _in_fallback(element) or _in_text_box(element):
            continue
        if element.tag == f"{{{A}}}blip":
            rel_id = element.get(f"{{{R}}}embed")
            drawing = next((a for a in element.iterancestors(w("drawing"))), None)
            if drawing is not None and _icon(drawing) is not None:
                continue
            doc_pr = next(drawing.iter(f"{{{WP}}}docPr"), None) if drawing is not None else None
            alt = None
            if doc_pr is not None:
                alt = doc_pr.get("descr") or doc_pr.get("title")
        else:
            rel_id = element.get(f"{{{R}}}id")
            parent = element.getparent()
            alt = (parent.get("alt") if parent is not None else None) or element.get("title")
        part = context.rels.get(rel_id) if rel_id else None
        content = context.package.read_bytes(part) if part else None
        if part is None or content is None:
            continue
        path = context.images.add(part[part.rfind("/") + 1 :], content)
        alt_text = md.escape(alt or "").replace("\n", " ")
        result.append(f"![{alt_text}]({md.destination(path)})")
    return result


def _ensure_blank_line(out: list[str]) -> None:
    tail = "".join(out[-2:])[-2:] if out else ""
    if not out or tail == "\n\n":
        return
    if not tail.endswith("\n"):
        out.append("\n")
    out.append("\n")


def _is_on(toggle: etree._Element | None) -> bool:
    if toggle is None:
        return False
    return toggle.get(w("val")) in (None, "1", "true", "on")


def _classify_heading(style_id: str, name: str) -> str:
    """Style ids and names are localized; the German ones are matched as well."""
    probe = (style_id + " " + name).lower()
    if "subtitle" in probe or "untertitel" in probe:
        return ""
    if "zwischenberschrift" in probe or "zwischenüberschrift" in probe:
        # PTA style for headings below level 3 (the DOCX generator writes #### into it).
        return "h4"
    if "title" in probe or "titel" in probe:
        return "title"
    is_heading = "heading" in probe or "berschrift" in probe
    if not is_heading or "toc" in probe or "verzeichnis" in probe:
        return ""
    for level in range(1, 7):
        if str(level) in probe:
            return f"h{level}"
    return "h1"
