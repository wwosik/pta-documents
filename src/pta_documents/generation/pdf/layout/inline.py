"""Inline Markdown as reportlab paragraph markup, formatted as the DOCX writer formats runs.

Bold, italic, strikethrough, inline code in the code font, ``==mark==`` on PTA yellow, coloured
words bold in their status colour, links in the colour and underline of the ``Hyperlink`` style.
Links go out only to absolute URLs and in only to anchors of headings of the document; any other
target leaves the text without a link, as in DocLibs.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import Final
from xml.sax.saxutils import escape, quoteattr

from markdown_it.token import Token

from pta_documents.design import word
from pta_documents.design.colors import STATUS_COLORS
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import html, layout_syntax
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.generation.pdf.layout.styles import PdfStyles
from pta_documents.markdown.parser import child_lines

FORMAT: Final = DocumentFormat.PDF
WHAT: Final = "the PDF"
ABSOLUTE_URI: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def hex_attribute(value: str) -> str:
    return quoteattr("#" + value)


@dataclass
class InlineOptions:
    """How one paragraph's inline content is written."""

    bold: bool = False
    """The whole paragraph is bold (its style is)."""
    italic: bool = False
    caps: bool = False
    line_breaks: bool = False
    """Soft line breaks are line breaks, not spaces."""
    skip_checkbox: bool = False
    """Leave out the task-list checkbox (the list item draws it as its marker)."""
    footnotes: list[Token] = field(default_factory=list[Token])
    """The ``footnote_ref`` children met, in order (filled while writing)."""


class InlineWriter:
    def __init__(
        self,
        styles: PdfStyles,
        anchors: Collection[str],
        notes: Notes,
        line_offset: int,
        footnote_number: Callable[[Token], int],
    ) -> None:
        self.styles = styles
        self.anchors = anchors
        self.notes = notes
        self.line_offset = line_offset
        self.footnote_number = footnote_number

    def markup(self, inline: Token, options: InlineOptions | None = None) -> str:
        options = options or InlineOptions()
        token = layout_syntax.coloured(inline, FORMAT)
        children = token.children or []
        parts: list[str] = []
        links: list[str] = []
        skipping = options.skip_checkbox
        for child, line in zip(children, child_lines(token, self.line_offset), strict=True):
            if skipping:
                if child.type == "html_inline" and html.is_checkbox(child.content):
                    continue
                if child.type == "text" and not child.content.strip():
                    continue
                if child.type == "text":
                    child = child.copy(content=child.content.lstrip())
                skipping = False
            match child.type:
                case "text" if layout_syntax.STATUS in child.meta:
                    status = child.meta[layout_syntax.STATUS]
                    parts.append(self.status(child.content, STATUS_COLORS[status], options))
                case "text":
                    parts.append(self.text(child.content, options))
                case "softbreak":
                    parts.append("<br/>" if options.line_breaks else " ")
                case "hardbreak":
                    parts.append("<br/>")
                case "code_inline":
                    font = quoteattr(self.styles.fonts.mono)
                    code = self.text(child.content, options, code=True)
                    parts.append(f"<font name={font}>{code}</font>")
                case "strong_open":
                    parts.append("<b>")
                case "strong_close":
                    parts.append("</b>")
                case "em_open":
                    parts.append("<i>")
                case "em_close":
                    parts.append("</i>")
                case "s_open":
                    parts.append("<strike>")
                case "s_close":
                    parts.append("</strike>")
                case "mark_open":
                    parts.append(f"<font backColor={hex_attribute(word.MARK_COLOR)}>")
                case "mark_close":
                    parts.append("</font>")
                case "link_open":
                    parts.append(self.link_open(str(child.attrs.get("href", "")), links))
                case "link_close":
                    parts.append(links.pop() if links else "")
                case "image":
                    parts.append(self.text(child.content, options))
                case "icon":
                    # Drawn in the PDF with E05-S04; Word and PowerPoint show it.
                    self.notes.add(
                        NoteCodes.CODE_NOT_DRAWN,
                        line,
                        f"The icon ':icon-{child.meta['name']}:' is left out: the PDF does not "
                        "draw icons yet (E05-S04).",
                    )
                case "footnote_ref":
                    options.footnotes.append(child)
                    parts.append(f"<super>{self.footnote_number(child)}</super>")
                case "html_inline":
                    if html.is_checkbox(child.content):
                        parts.append("[x]" if "checked" in child.content else "[ ]")
                    elif html.is_line_break(child.content):
                        parts.append("<br/>")
                    elif not html.is_comment(child.content):
                        html.note_raw_html(self.notes, line, WHAT)
                case _:
                    if child.content:
                        parts.append(self.text(child.content, options))
        body = "".join(parts)
        if options.italic:
            body = f"<i>{body}</i>"
        if options.bold:
            body = f"<b>{body}</b>"
        return body

    def text(self, text: str, options: InlineOptions, *, code: bool = False) -> str:
        """``text`` escaped for paragraph markup, characters the faces lack as ``?``."""
        return escape(self.styles.fonts.shown(text.upper() if options.caps else text, code))

    def status(self, text: str, color: str, options: InlineOptions) -> str:
        return f"<font color={hex_attribute(color)}><b>{self.text(text, options)}</b></font>"

    def link_open(self, href: str, links: list[str]) -> str:
        target: str | None = None
        if ABSOLUTE_URI.match(href) or (href.startswith("#") and href[1:] in self.anchors):
            target = href
        if target is None:
            links.append("")
            return ""
        color = self.styles.link_color.hexval()[2:].upper()
        underline = self.styles.link_underline
        links.append(("</u>" if underline else "") + "</font></a>")
        return f"<a href={quoteattr(target)}><font color={hex_attribute(color)}>" + (
            "<u>" if underline else ""
        )
