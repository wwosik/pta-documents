"""Markdown to slides: ``#`` is the title slide (first) or a chapter, ``##`` a slide.

Follows the DocLibs ``DeckParser``: text under a ``##`` heading becomes the body of a text
slide; a table, an image (row) or a code block makes a slide of its own, with the text before
it above and the text after it below; a second visual starts another slide with the same title.
A ``##`` section that uses the slide-layout Markdown becomes one flow slide (``flow_parser``),
one with a PTA slide kind (``{.agenda}`` …) its slide (``kind_parser``). A chart (a ``chart``
block a renderer drew as one) goes on the PTA chart layouts.
"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Final

from markdown_it.token import Token

from pta_documents.design import slides as design
from pta_documents.design.colors import StatusCategory
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import (
    code_blocks,
    code_highlight,
    generated_images,
    heading_attributes,
    html,
    icons,
    image_attributes,
    layout_syntax,
    layout_tokens,
    scene,
    schedule,
)
from pta_documents.generation.common.image_attributes import Fit
from pta_documents.generation.common.images import GENERATOR_SCALE, convert_image, refusal_hint
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    DrawingGraphic,
)
from pta_documents.generation.common.result import Notes
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.pptx import flow_parser, kind_parser
from pta_documents.generation.pptx.model import (
    BREAK,
    PICTURE_TYPES,
    Align,
    ChapterSlide,
    Chart,
    ChartSlide,
    Click,
    ClosingSlide,
    Code,
    ContentSlide,
    Diagram,
    Effect,
    Image,
    Images,
    Item,
    Kind,
    LayoutSlide,
    Paragraph,
    Run,
    SceneSlide,
    Separator,
    Slide,
    Table,
    TitleSlide,
    Visual,
    VisualSlide,
    trim,
)
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import block_markers
from pta_documents.markdown.document import DocumentResource, MarkdownDocument
from pta_documents.markdown.parser import (
    ALERT,
    CONTAINER_OPEN,
    child_lines,
    container,
    line_of,
    parse,
)
from pta_documents.markdown.typography import typeset, typeset_text

FORMAT: Final = DocumentFormat.PPTX
WHAT: Final = "the deck"
INLINE_ICON: Final = (
    "Icons in slide text are not drawn. On a slide, an icon goes at the start of a card title "
    "('### :icon-check: Title' in '::: cards') or at the start of every item of a bullet list; "
    "Word also shows it within text."
)
LISTS: Final = ("bullet_list_open", "ordered_list_open")
NOT_BUILT: Final = (
    "Builds ({.build}, {.frag}, {.exit}, {.emphasize}) go on '##' slides of content; the "
    "title, chapter and closing slides and the PTA slide kinds (.agenda, .interim, .quote, "
    ".contact) show everything at once. Take the marker out"
)


@dataclass
class Style:
    bold: bool = False
    italic: bool = False
    strike: bool = False
    link: str | None = None
    mark: bool = False


class DeckParser:
    def __init__(
        self,
        document: MarkdownDocument,
        body: str,
        line_offset: int,
        notes: Notes | None = None,
        options: PptxOptions | None = None,
        labels: dict[str, StatusCategory] | None = None,
    ) -> None:
        self.document = document
        self.labels = labels or {}
        """Status labels of the front matter (``status.<kategorie>``): label text -> category."""
        self.options = options or PptxOptions()
        if self.options.typography:
            # Label cells are typeset like any text, so the labels must be too.
            self.labels = {
                typeset_text(k, self.options.language): v for k, v in self.labels.items()
            }
        self.body = body
        self.line_offset = line_offset
        self.notes = notes if notes is not None else Notes()
        self.slides: list[Slide] = []
        self.tokens: list[Token] = []
        self.has_cover = False
        self.chapters = 0
        self.dark = False
        """The current slide is dark (``## Title {.dark}``): for the code-block renderers."""
        self.speaker_notes: dict[int, tuple[Paragraph, ...]] = {}
        """The ``::: notes`` of each section: by the index of its heading in ``tokens``."""
        self.clicks = 0
        """The last click given out (E09-S02)."""
        self.current: Click | None = None
        """The click of what is read now; None: there from the start."""
        self.each: Effect | None = None
        """``{.build}`` on a list (or ``aufbau: listen``): every paragraph its own click; on
        cards, rows, columns, the reader of the container takes it (``take_each``)."""
        self.list_depth = 0
        self.applied: set[int] = set()
        """The tokens (``id``) whose block marker was read: any other one is an error."""
        self.chapter_transition: SlideTransition | None = None
        """``{uebergang="…"}`` of the last ``#`` heading: for its slides and those of its
        chapter (E09-S03)."""

    def parse(self) -> list[Slide]:
        tokens = parse(self.body)
        layout_syntax.check(
            tokens, FORMAT, self.line_offset, schedule.reference_day(self.options.date)
        )
        self.document = generated_images.add_generated(
            self.document, tokens, FORMAT, self.line_offset, self.notes
        )
        if self.options.typography:
            typeset(tokens, self.options.language)
        end = next((i for i, t in enumerate(tokens) if t.type == "footnote_block_open"), None)
        if end is not None:
            tokens = tokens[:end]
        tokens, speaker_notes = self._take_notes(tokens)
        self.tokens = tokens
        self.speaker_notes = speaker_notes
        heading: tuple[Token, Token] | None = None
        start = 0
        i = 0
        while i < len(tokens):
            token = tokens[i]
            # Only headings of the document itself start slides, none inside a container.
            if token.type == "heading_open" and token.tag in ("h1", "h2") and token.level == 0:
                self._section(heading, start, i)
                heading = (token, tokens[i + 1])
                level = int(token.tag[1])
                _, attributes = layout_syntax.without_attributes(tokens[i + 1], level, FORMAT)
                self.dark = attributes is not None and attributes.dark
                i += 3
                start = i
                continue
            i += 1
        self._section(heading, start, len(tokens))
        return self.slides

    # ------------------------------------------------------------------ sections

    def line(self, token: Token) -> int | None:
        return line_of(token, self.line_offset)

    def code(self, token: Token) -> Code:
        """A code block no renderer took; with a known language in the PTA colours."""
        lines = tuple(token.content.rstrip("\n").split("\n"))
        info = token.info.strip() if token.type == "fence" else ""
        spans = code_highlight.highlight_fence(
            info, lines, self.line(token), self.notes, self.options.highlight
        )
        return Code(lines, spans or (), click=self.current)

    def _error(self, reason: str, token: Token) -> DocumentConversionError:
        line = self.line(token)
        return DocumentConversionError(FORMAT, f"{reason} (line {line})" if line else reason)

    def _section(self, heading: tuple[Token, Token] | None, start: int, end: int) -> None:
        if heading is None:
            # Text before the first heading is ignored, as in DocLibs.
            return
        first = len(self.slides)
        self._slides_of(heading, start, end)
        self._check_markers(start, end)
        notes = self.speaker_notes.get(start - 3, ())
        if notes:
            # On every slide of the heading (decision 2026-11-07), split ones included.
            self.slides[first:] = [replace(s, notes=notes) for s in self.slides[first:]]
        transition = self._transition(heading)
        if transition is not None:
            self.slides[first:] = [replace(s, transition=transition) for s in self.slides[first:]]

    def _transition(self, heading: tuple[Token, Token]) -> SlideTransition | None:
        """The transition of the slides of ``heading``: its own, else its chapter's; a ``#``
        sets the chapter's (E09-S03)."""
        open_token, inline = heading
        level = int(open_token.tag[1])
        _, attributes = layout_syntax.without_attributes(inline, level, FORMAT)
        own = attributes.transition if attributes is not None else None
        if level == 1:
            self.chapter_transition = own
        return own if own is not None else self.chapter_transition

    def _slides_of(self, heading: tuple[Token, Token], start: int, end: int) -> None:
        open_token, inline = heading
        title, attributes = self._title(inline, int(open_token.tag[1]))
        line = self.line(open_token)
        layout = attributes.layout if attributes else None
        if open_token.tag == "h1" or (attributes is not None and attributes.kind is not None):
            for token in self.tokens[start:end]:
                marker = token.meta.get(block_markers.MARKER)
                if isinstance(marker, block_markers.Marker):
                    raise DocumentConversionError(
                        FORMAT, at_line(NOT_BUILT, self.marker_line(marker))
                    )
        scene_at = self._scene_at(start, end) if open_token.tag == "h2" else None
        if scene_at is not None:
            self.slides.append(self._scene_slide(title, line, attributes, scene_at))
            return
        if open_token.tag == "h2" and attributes is not None and attributes.kind is not None:
            if self._uses_layouts(start, end, attributes):
                raise self._error(
                    f"The slide kind .{attributes.kind} has the PTA layout's own design and "
                    "takes no slide-layout Markdown (containers, alerts, tags)",
                    open_token,
                )
            reader = kind_parser.KindReader(self)
            self.slides.append(reader.slide(attributes.kind, title, open_token, layout, start, end))
            return
        if open_token.tag == "h2" and attributes is None:
            charts = self._charts_in_columns(start, end)
            if charts is not None:
                self.slides.append(ChartSlide(title, line, charts))
                return
        if open_token.tag == "h2" and self._uses_layouts(start, end, attributes):
            if layout is not None and layout != design.LAYOUTS.title_only:
                raise self._error(
                    f"The slide uses slide-layout Markdown (containers, alerts, tags, .dark or "
                    f"kicker), which goes on the layout '{design.LAYOUTS.title_only}' only, not "
                    f"on '{layout}'. Leave out layout=\"…\", or the slide-layout Markdown",
                    open_token,
                )
            reader = flow_parser.FlowReader(self)
            self.slides.append(reader.slide(title, line, attributes, start, end))
            return
        items: list[Item] = []
        i = start
        while i < end:
            i = self.block(self.tokens, i, items, depth=0, italic=False)
        section = items
        if open_token.tag == "h1":
            text = [i for i in section if not isinstance(i, Separator)]
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
            for item in section:
                if isinstance(item, Separator):
                    segments.append(())
                else:
                    segments[-1] = (*segments[-1], item)
            self.slides.append(LayoutSlide(title, line, layout, tuple(segments)))
            return
        self._content(title, section, line)

    # ------------------------------------------------------------------ scenes (E09-S04)

    def _scene_at(self, start: int, end: int) -> int | None:
        """Where the ``::: scene`` of a ``##`` section is; ``layout_syntax.check`` made sure it
        is alone there."""
        return next(
            (
                i
                for i in range(start, end)
                if self.tokens[i].type == CONTAINER_OPEN
                and container(self.tokens[i])[0] == layout_syntax.SCENE
            ),
            None,
        )

    def _scene_slide(
        self,
        title: tuple[Run, ...],
        line: int | None,
        attributes: heading_attributes.HeadingAttributes | None,
        i: int,
    ) -> SceneSlide:
        """The scene slide of the ``::: scene`` at ``tokens[i]``: its shapes (texts typeset
        like any text) and its images in a format slides take, fitted into their boxes."""
        token = self.tokens[i]
        read = scene.read_scene(
            self.tokens, i, FORMAT, self.line_offset, self.document.find_resource
        )
        if self.options.typography:
            language = self.options.language
            shapes = tuple(replace(s, text=typeset_text(s.text, language)) for s in read.shapes)
            read = replace(read, shapes=shapes)
        images: list[tuple[int, Image]] = []
        for n, shape in enumerate(read.shapes):
            if shape.resource is not None:
                image = Image(shape.resource, shape.text, shape.line, fit=True)
                images.append((n, self._placeable(image, token)))
        return SceneSlide(
            title,
            line,
            kicker=attributes.kicker if attributes is not None else None,
            dark=attributes is not None and attributes.dark,
            scene=read,
            images=tuple(images),
        )

    # ------------------------------------------------------------------ builds (E09-S02)

    def next_click(self, effect: Effect) -> Click:
        self.clicks += 1
        return Click(self.clicks, effect)

    def paragraph_click(self) -> Click | None:
        """The click of a paragraph read now: its own in a list built item by item."""
        return self.next_click(self.each) if self.each is not None else self.current

    def take_each(self) -> Effect | None:
        """``{.build}`` on the container read now: its elements get a click each, not what is
        inside them."""
        each, self.each = self.each, None
        return each

    @contextmanager
    def at(self, click: Click | None) -> Generator[None]:
        """What is read within is on ``click`` (a card, row or column built one by one)."""
        if click is None:
            yield
            return
        saved = self.current, self.each
        self.current, self.each = click, None
        try:
            yield
        finally:
            self.current, self.each = saved

    @contextmanager
    def marked(self, tokens: list[Token], i: int) -> Generator[None]:
        """Read the block at ``tokens[i]`` within: on a click of its own (``{.frag}``, and
        ``{.build}`` on any block but a list, cards, rows, columns or an image row), or with a
        click for each of its elements (``{.build}`` on those, ``aufbau: listen`` on a list
        that is not inside another)."""
        token = tokens[i]
        marker = token.meta.get(block_markers.MARKER)
        saved = self.current, self.each
        if isinstance(marker, block_markers.Marker):
            self.applied.add(id(token))
            effect = _effect(marker)
            if marker.name == block_markers.BUILD and _builds_items(tokens, i):
                self.each = effect
            else:
                self.current, self.each = self.next_click(effect), None
        elif (
            self.options.build_lists
            and token.type in LISTS
            and self.list_depth == 0
            and self.each is None
        ):
            self.each = Effect.FADE
        try:
            yield
        finally:
            self.current, self.each = saved

    def _check_markers(self, start: int, end: int) -> None:
        """Raise for a block marker of the section that marks a part of a block slides read in
        a way of their own (a card's heading, an item of '::: rows' …)."""
        for token in self.tokens[start:end]:
            marker = token.meta.get(block_markers.MARKER)
            if isinstance(marker, block_markers.Marker) and id(token) not in self.applied:
                raise DocumentConversionError(
                    FORMAT,
                    at_line(
                        f"The block marker '{marker.text}' marks a part of a block that is built "
                        "as a whole: put it before the whole block (cards, rows and columns are "
                        "built one by one with {.build} before their container)",
                        self.marker_line(marker),
                    ),
                )

    def marker_line(self, marker: block_markers.Marker) -> int:
        return marker.line + 1 + self.line_offset

    # ------------------------------------------------------------------ speaker notes

    def _take_notes(
        self, tokens: list[Token]
    ) -> tuple[list[Token], dict[int, tuple[Paragraph, ...]]]:
        """``tokens`` without their ``::: notes`` (at any depth), and the paragraphs of those of
        each section by the index of its heading in the tokens returned; several blocks of a
        section are joined. ``layout_syntax.check`` rejects notes before the first heading."""
        kept: list[Token] = []
        notes: dict[int, list[Paragraph]] = {}
        heading: int | None = None
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open" and token.tag in ("h1", "h2") and token.level == 0:
                heading = len(kept)
            if token.type == CONTAINER_OPEN and container(token)[0] == layout_syntax.NOTES:
                end = flow_parser.block_end(tokens, i)
                if heading is not None:
                    paragraphs = notes.setdefault(heading, [])
                    self._note_blocks(tokens, i + 1, end - 1, paragraphs, Kind.INTRO, 0, 1)
                i = end
                continue
            kept.append(token)
            i += 1
        return kept, {k: tuple(v) for k, v in notes.items() if v}

    def _note_blocks(
        self,
        tokens: list[Token],
        start: int,
        stop: int,
        out: list[Paragraph],
        kind: Kind,
        depth: int,
        number: int,
    ) -> None:
        """The text of the blocks ``tokens[start:stop]`` as note paragraphs: list items of
        ``kind`` at ``depth``, code one paragraph per line in the code font (E08-S03: the
        Markdown source of a slide); tables, images and lines are left out."""
        j = start
        while j < stop:
            token = tokens[j]
            end = flow_parser.block_end(tokens, j)
            match token.type:
                case "paragraph_open" | "heading_open" | "dt_open":
                    style = Style(bold=token.type != "paragraph_open")
                    runs = trim(self.runs(tokens[j + 1], style, images_as_text=False))
                    if runs:
                        out.append(Paragraph(tuple(runs), kind, depth, number))
                case "bullet_list_open" | "ordered_list_open":
                    ordered = token.type == "ordered_list_open"
                    first = int(token.attrs.get("start", 1)) if ordered and token.attrs else 1
                    inner = depth + 1 if kind in (Kind.BULLET, Kind.NUMBERED) else 0
                    for item in flow_parser.children(tokens, j):
                        item_end = flow_parser.block_end(tokens, item) - 1
                        list_kind = Kind.NUMBERED if ordered else Kind.BULLET
                        self._note_blocks(tokens, item + 1, item_end, out, list_kind, inner, first)
                case "html_block":
                    if not html.is_comment(token.content):
                        html.note_raw_html(self.notes, self.line(token), WHAT)
                case "fence" | "code_block":
                    for text in token.content.rstrip("\n").split("\n"):
                        out.append(Paragraph((Run(text, code=True),) if text else ()))
                case "table_open" | "hr":
                    pass
                case _ if token.nesting == 1:
                    self._note_blocks(tokens, j + 1, end - 1, out, kind, depth, number)
                case _:
                    pass
            j = end

    def _uses_layouts(
        self, start: int, end: int, attributes: heading_attributes.HeadingAttributes | None
    ) -> bool:
        """Whether a ``##`` section is a flow slide: ``.dark`` or ``kicker`` on its heading, a
        container or an alert anywhere in it, or a paragraph of tags of its own (DocLibs)."""
        if attributes is not None and (attributes.dark or attributes.kicker is not None):
            return True
        tokens = self.tokens
        for i in range(start, end):
            token = tokens[i]
            if token.type == CONTAINER_OPEN or (
                token.type == "blockquote_open" and ALERT in token.meta
            ):
                return True
            if (
                token.type == "paragraph_open"
                and token.level == 0
                and layout_tokens.tags(tokens[i + 1]) is not None
            ):
                return True
        return False

    def _charts_in_columns(self, start: int, end: int) -> tuple[Chart, ...] | None:
        """The two charts of a section that is one ``::: columns`` of one chart each (``Titel
        und zwei Diagramme``); None for any other section."""
        tokens = self.tokens
        if start >= end or tokens[start].type != CONTAINER_OPEN:
            return None
        if flow_parser.block_end(tokens, start) != end:
            return None
        name, arguments = container(tokens[start])
        if name != layout_syntax.COLUMNS or arguments:
            return None
        kids = flow_parser.children(tokens, start)
        if len(kids) != 3 or tokens[kids[1]].type != "hr":
            return None
        if any(tokens[kid].type != "fence" for kid in (kids[0], kids[2])):
            return None
        charts: list[Chart] = []
        # A look ahead: notes of fences that are no charts come when the flow slide reads them.
        notes, self.notes = self.notes, Notes()
        try:
            for kid in (kids[0], kids[2]):
                items: list[Item] = []
                self.block(tokens, kid, items, depth=0, italic=False)
                if len(items) != 1 or not isinstance(items[0], Chart):
                    return None
                charts.append(items[0])
        finally:
            self.notes = notes
        return tuple(charts)

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
        return tuple(trim(self.runs(inline, Style(), images_as_text=True))), attributes

    def _content(self, heading_runs: tuple[Run, ...], items: list[Item], line: int | None) -> None:
        above: list[Paragraph] = []
        below: list[Paragraph] = []
        visual: Visual | Chart | None = None

        def flush() -> None:
            nonlocal above, below, visual
            if isinstance(visual, Chart):
                text = (*above, *below)
                self.slides.append(ChartSlide(heading_runs, line, (visual,), text, bool(above)))
            else:
                slide = VisualSlide(heading_runs, line, tuple(above), visual, tuple(below))
                self.slides.append(slide)
            above, below, visual = [], [], None

        content = [i for i in items if not isinstance(i, Separator)]
        if len(content) == 2 and all(isinstance(i, Chart) for i in content):
            # Two charts and nothing else: side by side on 'Titel und zwei Diagramme'.
            charts = tuple(i for i in content if isinstance(i, Chart))
            self.slides.append(ChartSlide(heading_runs, line, charts))
            return
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
                item = replace(item, title=title)
            visual = item
        if visual is not None:
            flush()
        else:
            self.slides.append(ContentSlide(heading_runs, line, tuple(above)))

    # ------------------------------------------------------------------ blocks

    def block(self, tokens: list[Token], i: int, out: list[Item], depth: int, italic: bool) -> int:
        with self.marked(tokens, i):
            return self.read_block(tokens, i, out, depth, italic)

    def read_block(
        self, tokens: list[Token], i: int, out: list[Item], depth: int, italic: bool
    ) -> int:
        """The block at ``tokens[i]`` into ``out``, its block marker already applied."""
        token = tokens[i]
        match token.type:
            case "heading_open":
                runs = self.runs(tokens[i + 1], Style(italic=italic), images_as_text=True)
                out.append(Paragraph(tuple(runs), Kind.SUBHEADLINE, click=self.paragraph_click()))
                return i + 3
            case "paragraph_open":
                self._paragraph(tokens[i + 1], out, Kind.INTRO, 0, 1, italic)
                return i + 3
            case "bullet_list_open" | "ordered_list_open":
                return self._list(tokens, i, out, depth, italic)
            case "blockquote_open":
                return self._container(tokens, i, "blockquote_close", out, depth, italic=True)
            case "table_open":
                return self.table(tokens, i, out)
            case "fence" | "code_block":
                graphic = self._draw(token) if token.type == "fence" else None
                click = self.current
                if isinstance(graphic, ChartGraphic):
                    out.append(Chart(graphic, self.line(token), click=click))
                elif isinstance(graphic, DrawingGraphic):
                    alt = token.info.strip()
                    out.append(Diagram(graphic.drawing, alt, self.line(token), click=click))
                elif graphic is not None:
                    image = Image(graphic.image, token.info.strip(), self.line(token), click=click)
                    out.append(Images((self._placeable(image, token),)))
                else:
                    out.append(self.code(token))
                return i + 1
            case "html_block":
                if not html.is_comment(token.content):
                    html.note_raw_html(self.notes, self.line(token), WHAT)
                return i + 1
            case "hr":
                out.append(Separator())
                return i + 1
            case "dl_open":
                return self._container(tokens, i, "dl_close", out, depth, italic)
            case "dt_open":
                runs = self.runs(tokens[i + 1], Style(bold=True, italic=italic), True)
                out.append(Paragraph(tuple(runs), Kind.INTRO, click=self.paragraph_click()))
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
            j = self.block(tokens, j, out, depth, italic)
        return j

    def _list(self, tokens: list[Token], i: int, out: list[Item], depth: int, italic: bool) -> int:
        ordered = tokens[i].type == "ordered_list_open"
        close = "ordered_list_close" if ordered else "bullet_list_close"
        kind = Kind.NUMBERED if ordered else Kind.BULLET
        start = int(tokens[i].attrs.get("start", 1)) if ordered and tokens[i].attrs else 1
        bullets = icons.list_icons(tokens, i)
        item = 0
        self.list_depth += 1
        j = i + 1
        while tokens[j].type != close:
            if tokens[j].type != "list_item_open":
                j += 1
                continue
            j += 1
            marked = False
            icon = bullets[item] if bullets else None
            item += 1
            while tokens[j].type != "list_item_close":
                t = tokens[j]
                if t.type == "paragraph_open" and not marked:
                    inline = icons.without_leading(tokens[j + 1]) if icon else tokens[j + 1]
                    with self.marked(tokens, j):
                        self._paragraph(inline, out, kind, depth, start, italic, icon)
                    marked = True
                    j += 3
                elif t.type in LISTS:
                    with self.marked(tokens, j):
                        j = self._list(tokens, j, out, depth + 1, italic)
                else:
                    j = self.block(tokens, j, out, depth, italic)
            j += 1
        self.list_depth -= 1
        return j + 1

    def _paragraph(
        self,
        inline: Token,
        out: list[Item],
        kind: Kind,
        depth: int,
        start: int,
        italic: bool,
        icon: str | None = None,
    ) -> None:
        """Text and images apart: images after the paragraph, as their own visual; ``icon``
        is the bullet of a list item (E15-S03)."""
        runs = self.runs(inline, Style(italic=italic), images_as_text=False)
        text = trim(runs)
        children = inline.children or []
        if text or icon or not any(child.type == "image" for child in children):
            click = self.paragraph_click()
            out.append(Paragraph(tuple(text), kind, depth, start, icon=icon, click=click))
        images = [
            replace(
                self._placeable(self._image(child, inline, line), inline),
                click=self.paragraph_click(),
            )
            for child, line in zip(children, child_lines(inline, self.line_offset), strict=True)
            if child.type == "image"
        ]
        if images:
            out.append(Images(tuple(images)))

    def _resource(self, image: Token, inline: Token) -> DocumentResource:
        source = str(image.attrs.get("src", ""))
        resource = self.document.find_resource(source)
        if resource is None:
            raise self._error(f"The image '{source}' is not among the document's resources", inline)
        return resource

    def _draw(self, fence: Token) -> CodeBlockGraphic | None:
        """The image, drawing or chart the code-block renderers make of ``fence``; None: it
        stays code."""
        return code_blocks.render_graphic(
            self.options.code_block_renderers,
            self.notes,
            fence.info,
            fence.content,
            self.line(fence),
            FORMAT,
            self.options.language,
            self.dark,
        )

    def image(self, child: Token, inline: Token) -> Image:
        """The image of an ``image`` child of ``inline``, in a format slides take."""
        line = self.line(inline)
        return self._placeable(self._image(child, inline, line), inline)

    def _image(self, child: Token, inline: Token, line: int | None) -> Image:
        """The ``image`` child of ``inline`` as it is written, with its attributes (E15-S04);
        a QR code is fitted, never cropped."""
        generated = generated_images.is_generated(str(child.attrs.get("src", "")))
        attributes = image_attributes.of(child)
        return Image(
            self._resource(child, inline),
            child.content,
            line,
            fit=generated or attributes.fit is Fit.CONTAIN,
            scale=attributes.factor,
            focus=attributes.focus,
            round=attributes.round,
        )

    def _placeable(self, image: Image, token: Token) -> Image:
        """``image`` in a format slides take: other formats through the image converters."""
        resource = image.resource
        if resource.content_type in PICTURE_TYPES:
            return image
        converters = self.options.image_converters
        conversion = convert_image(converters, resource, GENERATOR_SCALE, FORMAT)
        if conversion is None:
            hint = refusal_hint(resource, converters)
            raise self._error(
                f"The image '{resource.path}' is a {resource.content_type}; PPTX takes PNG, JPEG, "
                f"GIF, BMP and TIFF{hint}",
                token,
            )
        return replace(
            image,
            resource=conversion.image,
            natural=(conversion.width, conversion.height),
            svg=conversion.svg,
        )

    def table(self, tokens: list[Token], i: int, out: list[Item], labels: bool = False) -> int:
        """The table at ``tokens[i]``; with ``labels`` (flow slides), a body cell that is one
        code span is a status label: a dot in its category's colour before its text."""
        rows: list[tuple[tuple[Run, ...], ...]] = []
        highlighted: list[bool] = []
        alignments: list[Align] = []
        has_header = False
        current: list[tuple[Run, ...]] = []
        first_cell: Token | None = None
        j = i + 1
        while tokens[j].type != "table_close":
            t = tokens[j]
            if t.type == "tr_open":
                current = []
                first_cell = None
            elif t.type == "tr_close":
                rows.append(tuple(current))
                highlighted.append(first_cell is not None and layout_tokens.is_marked(first_cell))
            elif t.type == "td_open" and (
                (quarters := layout_tokens.harvey_cell(tokens[j + 1])) is not None
            ):
                first_cell = first_cell or tokens[j + 1]
                current.append((Run("", harvey=quarters),))
            elif (
                t.type == "td_open"
                and labels
                and (label := layout_tokens.label_cell(tokens[j + 1]))
            ):
                first_cell = first_cell or tokens[j + 1]
                category = self.labels.get(label, StatusCategory.NEUTRAL)
                current.append((Run("● ", status=category, label=True), Run(label)))
            elif t.type in ("th_open", "td_open"):
                if t.type == "td_open" and first_cell is None:
                    first_cell = tokens[j + 1]
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
                current.append(tuple(trim(self.runs(tokens[j + 1], Style(), True))))
            j += 1
        table = Table(tuple(rows), tuple(alignments), has_header, None, tuple(highlighted))
        out.append(replace(table, click=self.current))
        return j + 1

    # ------------------------------------------------------------------ inline

    def text_runs(self, inline: Token) -> tuple[Run, ...]:
        """The runs of a paragraph or heading, images as their alt text, trimmed."""
        return tuple(trim(self.runs(inline, Style(), images_as_text=True)))

    def runs(self, inline: Token, style: Style, images_as_text: bool) -> list[Run]:
        """The runs of an inline token; ``[words]{.success}`` without brackets and braces, in
        their status category, ``==text==`` marked."""
        inline = layout_syntax.coloured(inline, FORMAT)
        runs: list[Run] = []
        current = replace(style)

        def add(text: str, code: bool = False, status: StatusCategory | None = None) -> None:
            if text:
                runs.append(
                    Run(
                        text,
                        current.bold,
                        current.italic,
                        current.strike,
                        code,
                        current.link,
                        mark=current.mark,
                        status=status,
                    )
                )

        children = inline.children or []
        for child, line in zip(children, child_lines(inline, self.line_offset), strict=True):
            match child.type:
                case "text" if layout_syntax.STATUS in child.meta:
                    add(child.content, status=StatusCategory(child.meta[layout_syntax.STATUS]))
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
                case "mark_open":
                    current.mark = True
                case "mark_close":
                    current.mark = style.mark
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
                case "icon":
                    raise DocumentConversionError(FORMAT, at_line(INLINE_ICON, line))
                case _:
                    add(child.content)
        return runs


def _effect(marker: block_markers.Marker) -> Effect:
    if marker.name == block_markers.EXIT:
        return Effect.EXIT
    if marker.name == block_markers.EMPHASIZE:
        return Effect.EMPHASIZE
    return Effect(marker.entrance)


def _builds_items(tokens: list[Token], i: int) -> bool:
    """Whether ``{.build}`` builds the block at ``tokens[i]`` element by element: a list, cards,
    rows, columns, a paragraph of nothing but images."""
    token = tokens[i]
    if token.type in LISTS:
        return True
    if token.type == CONTAINER_OPEN:
        name = container(token)[0]
        return name in (layout_syntax.CARDS, layout_syntax.ROWS, layout_syntax.COLUMNS)
    if token.type == "paragraph_open":
        kids = tokens[i + 1].children or []
        return any(k.type == "image" for k in kids) and all(
            k.type in ("image", "softbreak") or (k.type == "text" and not k.content.strip())
            for k in kids
        )
    return False


def at_line(reason: str, line: int | None) -> str:
    """``reason`` with its line in front, as ``layout_syntax.check`` reports."""
    return f"Line {line}: {reason}" if line else reason
