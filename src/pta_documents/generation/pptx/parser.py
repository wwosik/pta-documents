"""Markdown to slides: ``#`` is the title slide (first) or a chapter, ``##`` a slide.

Follows the DocLibs ``DeckParser``: text under a ``##`` heading becomes the body of a text
slide; a table, an image (row) or a code block makes a slide of its own, with the text before
it above and the text after it below; a second visual starts another slide with the same title.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    code_blocks,
    heading_attributes,
    html,
    layout_syntax,
)
from pta_documents.generation.common.images import GENERATOR_SCALE, convert_image
from pta_documents.generation.common.renderers import ImageGraphic
from pta_documents.generation.common.result import Notes
from pta_documents.generation.pptx.model import (
    BREAK,
    PICTURE_TYPES,
    Align,
    ChapterSlide,
    ClosingSlide,
    Code,
    ContentSlide,
    Image,
    Images,
    Item,
    Kind,
    LayoutSlide,
    Paragraph,
    Run,
    Separator,
    Slide,
    Table,
    TitleSlide,
    Visual,
    VisualSlide,
)
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import child_lines, line_of, parse

FORMAT: Final = DocumentFormat.PPTX
WHAT: Final = "the deck"


@dataclass
class _Style:
    bold: bool = False
    italic: bool = False
    strike: bool = False
    link: str | None = None


@dataclass
class _Section:
    """Collects the items under one heading."""

    items: list[Item] = field(default_factory=lambda: list[Item]())


class DeckParser:
    def __init__(
        self,
        document: MarkdownDocument,
        body: str,
        line_offset: int,
        notes: Notes | None = None,
        options: PptxOptions | None = None,
    ) -> None:
        self.document = document
        self.options = options or PptxOptions()
        self.body = body
        self.line_offset = line_offset
        self.notes = notes if notes is not None else Notes()
        self.slides: list[Slide] = []
        self.has_cover = False
        self.chapters = 0
        self.dark = False
        """The current slide is dark (``## Title {.dark}``): for the code-block renderers."""

    def parse(self) -> list[Slide]:
        tokens = parse(self.body)
        layout_syntax.check(tokens, FORMAT, self.line_offset)
        end = next((i for i, t in enumerate(tokens) if t.type == "footnote_block_open"), None)
        if end is not None:
            tokens = tokens[:end]
        heading: tuple[Token, Token] | None = None
        section = _Section()
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open" and token.tag in ("h1", "h2"):
                self._section(heading, section)
                heading = (token, tokens[i + 1])
                section = _Section()
                level = int(token.tag[1])
                _, attributes = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
                self.dark = attributes is not None and attributes.dark
                i += 3
                continue
            i = self._block(tokens, i, section.items, depth=0, italic=False)
        self._section(heading, section)
        return self.slides

    # ------------------------------------------------------------------ sections

    def _line(self, token: Token) -> int | None:
        return line_of(token, self.line_offset)

    def _error(self, reason: str, token: Token) -> DocumentConversionError:
        line = self._line(token)
        return DocumentConversionError(FORMAT, f"{reason} (line {line})" if line else reason)

    def _section(self, heading: tuple[Token, Token] | None, section: _Section) -> None:
        if heading is None:
            # Text before the first heading is ignored, as in DocLibs.
            return
        open_token, inline = heading
        title, attributes = self._title(inline, int(open_token.tag[1]))
        line = self._line(open_token)
        layout = attributes.layout if attributes else None
        if open_token.tag == "h1":
            text = [i for i in section.items if not isinstance(i, Separator)]
            if attributes is not None and attributes.closing:
                self._no_content(text, "the closing slide", open_token)
                self.slides.append(ClosingSlide(title, line, layout))
            elif not self.has_cover:
                if any(not isinstance(i, Paragraph) for i in text):
                    raise self._error(
                        "The title slide takes only text (the subtitle); put tables, images and "
                        "code under a '##' heading",
                        open_token,
                    )
                paragraphs = tuple(i for i in text if isinstance(i, Paragraph))
                self.slides.append(TitleSlide(title, line, paragraphs, layout))
                self.has_cover = True
            else:
                self._no_content(text, "a chapter slide", open_token)
                self.chapters += 1
                self.slides.append(ChapterSlide(title, line, self.chapters, layout))
            return
        if attributes is not None and attributes.closing:
            raise self._error("{.closing} goes on a '#' heading: the closing slide", open_token)
        if layout is not None:
            segments: list[tuple[Item, ...]] = [()]
            for item in section.items:
                if isinstance(item, Separator):
                    segments.append(())
                else:
                    segments[-1] = (*segments[-1], item)
            self.slides.append(LayoutSlide(title, line, layout, tuple(segments)))
            return
        self._content(title, section.items, line)

    def _no_content(self, items: Sequence[Item], what: str, token: Token) -> None:
        if items:
            raise self._error(
                f"The PTA layout of {what} has no place for content under the heading; "
                "put it under a '##' heading",
                token,
            )

    def _title(
        self, inline: Token, level: int
    ) -> tuple[tuple[Run, ...], heading_attributes.HeadingAttributes | None]:
        inline, attributes = layout_syntax.without_attributes(inline, level, FORMAT)
        return tuple(_trim(self._runs(inline, _Style(), images_as_text=True))), attributes

    def _content(self, heading_runs: tuple[Run, ...], items: list[Item], line: int | None) -> None:
        above: list[Paragraph] = []
        below: list[Paragraph] = []
        visual: Visual | None = None

        def flush() -> None:
            nonlocal above, below, visual
            self.slides.append(VisualSlide(heading_runs, line, tuple(above), visual, tuple(below)))
            above, below, visual = [], [], None

        for item in items:
            if isinstance(item, Separator):
                continue
            if isinstance(item, Paragraph):
                (below if visual is not None else above).append(item)
                continue
            if visual is not None:
                flush()
            if isinstance(item, Table) and above and above[-1].is_bold_only:
                # A bold paragraph right before a table is its title row (PTA sample table).
                title = tuple(r for r in above.pop().runs)
                item = Table(item.rows, item.alignments, item.has_header, title)
            visual = item
        if visual is not None:
            flush()
        else:
            self.slides.append(ContentSlide(heading_runs, line, tuple(above)))

    # ------------------------------------------------------------------ blocks

    def _block(self, tokens: list[Token], i: int, out: list[Item], depth: int, italic: bool) -> int:
        token = tokens[i]
        match token.type:
            case "heading_open":
                runs = self._runs(tokens[i + 1], _Style(italic=italic), images_as_text=True)
                out.append(Paragraph(tuple(runs), Kind.SUBHEADLINE))
                return i + 3
            case "paragraph_open":
                self._paragraph(tokens[i + 1], out, Kind.INTRO, 0, 1, italic)
                return i + 3
            case "bullet_list_open" | "ordered_list_open":
                return self._list(tokens, i, out, depth, italic)
            case "blockquote_open":
                return self._container(tokens, i, "blockquote_close", out, depth, italic=True)
            case "table_open":
                return self._table(tokens, i, out)
            case "fence" | "code_block":
                graphic = self._draw(token) if token.type == "fence" else None
                if graphic is not None:
                    image = Image(graphic.image, token.info.strip(), self._line(token))
                    out.append(Images((self._placeable(image, token),)))
                else:
                    out.append(Code(tuple(token.content.rstrip("\n").split("\n"))))
                return i + 1
            case "html_block":
                if not html.is_comment(token.content):
                    html.note_raw_html(self.notes, self._line(token), WHAT)
                return i + 1
            case "hr":
                out.append(Separator())
                return i + 1
            case "dl_open":
                return self._container(tokens, i, "dl_close", out, depth, italic)
            case "dt_open":
                runs = self._runs(tokens[i + 1], _Style(bold=True, italic=italic), True)
                out.append(Paragraph(tuple(runs), Kind.INTRO))
                return i + 3
            case _:
                return i + 1

    def _container(
        self, tokens: list[Token], i: int, close: str, out: list[Item], depth: int, italic: bool
    ) -> int:
        nesting = 0
        j = i + 1
        while j < len(tokens):
            if tokens[j].type == tokens[i].type:
                nesting += 1
            elif tokens[j].type == close:
                if nesting == 0:
                    return j + 1
                nesting -= 1
                j += 1
                continue
            j = self._block(tokens, j, out, depth, italic)
        return j

    def _list(self, tokens: list[Token], i: int, out: list[Item], depth: int, italic: bool) -> int:
        ordered = tokens[i].type == "ordered_list_open"
        close = "ordered_list_close" if ordered else "bullet_list_close"
        kind = Kind.NUMBERED if ordered else Kind.BULLET
        start = int(tokens[i].attrs.get("start", 1)) if ordered and tokens[i].attrs else 1
        j = i + 1
        while tokens[j].type != close:
            if tokens[j].type != "list_item_open":
                j += 1
                continue
            j += 1
            marked = False
            while tokens[j].type != "list_item_close":
                t = tokens[j]
                if t.type == "paragraph_open" and not marked:
                    self._paragraph(tokens[j + 1], out, kind, depth, start, italic)
                    marked = True
                    j += 3
                elif t.type in ("bullet_list_open", "ordered_list_open"):
                    j = self._list(tokens, j, out, depth + 1, italic)
                else:
                    j = self._block(tokens, j, out, depth, italic)
            j += 1
        return j + 1

    def _paragraph(
        self, inline: Token, out: list[Item], kind: Kind, depth: int, start: int, italic: bool
    ) -> None:
        """Text and images apart: images after the paragraph, as their own visual."""
        runs = self._runs(inline, _Style(italic=italic), images_as_text=False)
        images = [
            self._placeable(Image(self._resource(child, inline), child.content, line), inline)
            for child, line in zip(
                inline.children or [], child_lines(inline, self.line_offset), strict=True
            )
            if child.type == "image"
        ]
        text = _trim(runs)
        if text or not images:
            out.append(Paragraph(tuple(text), kind, depth, start))
        if images:
            out.append(Images(tuple(images)))

    def _resource(self, image: Token, inline: Token) -> DocumentResource:
        source = str(image.attrs.get("src", ""))
        resource = self.document.find_resource(source)
        if resource is None:
            raise self._error(f"The image '{source}' is not among the document's resources", inline)
        return resource

    def _draw(self, fence: Token) -> ImageGraphic | None:
        """The image the code-block renderers make of ``fence``; None: it stays code."""
        return code_blocks.draw(
            self.options.code_block_renderers,
            self.notes,
            fence.info,
            fence.content,
            self._line(fence),
            FORMAT,
            self.options.language,
            self.dark,
        )

    def _placeable(self, image: Image, token: Token) -> Image:
        """``image`` in a format slides take: other formats through the image converters."""
        resource = image.resource
        if resource.content_type in PICTURE_TYPES:
            return image
        converters = self.options.image_converters
        conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
        if conversion is None:
            nobody = ", and no image converter takes it" if converters else ""
            raise self._error(
                f"The image '{resource.path}' is a {resource.content_type}; PPTX takes PNG, JPEG, "
                f"GIF, BMP and TIFF{nobody}",
                token,
            )
        return Image(conversion.image, image.alt, image.line)

    def _table(self, tokens: list[Token], i: int, out: list[Item]) -> int:
        rows: list[tuple[tuple[Run, ...], ...]] = []
        alignments: list[Align] = []
        has_header = False
        current: list[tuple[Run, ...]] = []
        j = i + 1
        while tokens[j].type != "table_close":
            t = tokens[j]
            if t.type == "tr_open":
                current = []
            elif t.type == "tr_close":
                rows.append(tuple(current))
            elif t.type in ("th_open", "td_open"):
                if t.type == "th_open":
                    has_header = True
                    style = str(t.attrs.get("style", "")) if t.attrs else ""
                    alignments.append(
                        {
                            "text-align:left": Align.LEFT,
                            "text-align:center": Align.CENTER,
                            "text-align:right": Align.RIGHT,
                        }.get(style, Align.DEFAULT)
                    )
                current.append(tuple(_trim(self._runs(tokens[j + 1], _Style(), True))))
            j += 1
        out.append(Table(tuple(rows), tuple(alignments), has_header))
        return j + 1

    # ------------------------------------------------------------------ inline

    def _runs(self, inline: Token, style: _Style, images_as_text: bool) -> list[Run]:
        """The runs of an inline token; ``[words]{.success}`` bold without brackets and braces
        (their colour comes with E04-S03)."""
        inline = layout_syntax.coloured(inline, FORMAT)
        runs: list[Run] = []
        current = _Style(style.bold, style.italic, style.strike, style.link)

        def add(text: str, code: bool = False) -> None:
            if text:
                runs.append(
                    Run(text, current.bold, current.italic, current.strike, code, current.link)
                )

        children = inline.children or []
        for child, line in zip(children, child_lines(inline, self.line_offset), strict=True):
            match child.type:
                case "text" if layout_syntax.STATUS in child.meta:
                    bold = current.bold
                    current.bold = True
                    add(child.content)
                    current.bold = bold
                case "text":
                    add(child.content)
                case "softbreak":
                    add(" ")
                case "hardbreak":
                    runs.append(BREAK)
                case "code_inline":
                    add(child.content, code=True)
                case "strong_open":
                    current.bold = True
                case "strong_close":
                    current.bold = style.bold
                case "em_open":
                    current.italic = True
                case "em_close":
                    current.italic = style.italic
                case "s_open":
                    current.strike = True
                case "s_close":
                    current.strike = style.strike
                case "link_open":
                    href = str(child.attrs.get("href", ""))
                    current.link = href if ":" in href else None
                case "link_close":
                    current.link = None
                case "image":
                    if images_as_text:
                        add(child.content)
                case "html_inline":
                    if html.is_checkbox(child.content):
                        add("☒" if "checked" in child.content else "☐")
                    elif html.is_line_break(child.content):
                        runs.append(BREAK)
                    elif not html.is_comment(child.content):
                        html.note_raw_html(self.notes, line, WHAT)
                case "footnote_ref" | "footnote_anchor":
                    pass
                case _:
                    add(child.content)
        return runs


def _trim(runs: list[Run]) -> list[Run]:
    """Without leading and trailing whitespace and breaks."""
    result = list(runs)
    while result and (result[0].is_break or not result[0].text.strip()):
        result.pop(0)
    while result and (result[-1].is_break or not result[-1].text.strip()):
        result.pop()
    if result:
        first, last = result[0], result[-1]
        result[0] = Run(
            first.text.lstrip(), first.bold, first.italic, first.strike, first.code, first.link
        )
        last = result[-1]
        result[-1] = Run(
            last.text.rstrip(), last.bold, last.italic, last.strike, last.code, last.link
        )
    return result
