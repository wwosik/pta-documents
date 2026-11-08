"""PDF to Markdown (port of DocLibs ``PdfConverter`` on pdfplumber; extra ``pdf``).

One section ``## Page n`` per page. Text comes from the text layer only, so scanned pages come
out empty. Words are grouped into lines and lines into paragraphs; running headers and footers
are removed, and so are images that appear on every page.

pdfplumber measures from the top of the page (``top``/``bottom`` grow downwards), PdfPig from
the bottom; the comparisons are turned accordingly, the thresholds are those of DocLibs.

Beyond DocLibs (E07-S04): tables with ruling lines become pipe tables — grids through
pdfplumber's ``find_tables``, tables with a filled header row and horizontal rules only (the
PTA style ``PTA`` of the PDF generator) through ``ruled_tables``; bullets and task boxes drawn
as shapes (the PDF generator draws them) start list items; lines in a monospaced font become a
fenced code block.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import itertools
import re
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Final

import pdfplumber
import pikepdf

from pta_documents.conversions.openxml import read_input
from pta_documents.conversions.options import ConversionOptions, ResourceCollector
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.markdown import text as md
from pta_documents.markdown import typography
from pta_documents.markdown.document import MarkdownDocument, MetadataKeys

UNREADABLE: Final = "The PDF could not be read: "
ENCRYPTED: Final = (
    "The PDF is protected by a password. Save or print it without the protection and convert "
    "that file."
)

MARGIN_SHARE: Final = 0.08
"""Lines this close to the top or bottom edge (share of the page height) end a paragraph."""
HEADING_SIZE: Final = 1.15
"""A short paragraph at least this many times the body size is a heading."""
HEADING_LENGTH: Final = 100
SIZE_CHANGE: Final = 0.15
GAP_SHARE: Final = 0.35
EARLY_END: Final = 0.15
OUTDENT: Final = 1.5
BOLD_SHARE: Final = 0.8
BOILERPLATE_PAGES: Final = 3
BOILERPLATE_LENGTH: Final = 200

STRONG_BULLETS: Final = frozenset("•▪■◦·●‣⁃➢→")
WEAK_BULLETS: Final = frozenset("-–*o")
ITEM: Final = "- "
OPEN_TASK: Final = "- [ ] "
DONE_TASK: Final = "- [x] "

NUMBERED_START: Final = re.compile(r"^\d{1,2}(\.\d{1,2})*\.?\s+\S")
TABLE_OF_CONTENTS_ENTRY: Final = re.compile(r"\.{4,}\s*\d+$")
KEY_NOISE: Final = re.compile(r"\d+|\s+|[#*\-\\]")
MONOSPACED: Final = re.compile(r"mono|courier|consol|inconsolata|cousine|menlo|code", re.I)
"""Font names of monospaced fonts; their lines are code."""

GRID_SETTINGS: Final[dict[str, Any]] = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
}
"""Grid tables need ruling lines in both directions (pdfplumber's default)."""

type Box = tuple[float, float, float, float]
"""x0, top, x1, bottom."""


class PdfConverter:
    """PDF → Markdown; registered by ``ConverterRegistry.default()`` when the extra ``pdf``
    is installed."""

    format: Final = DocumentFormat.PDF

    def can_convert(self, format: DocumentFormat) -> bool:
        return format is DocumentFormat.PDF

    def convert(
        self, data: bytes | BinaryIO, options: ConversionOptions | None = None
    ) -> MarkdownDocument:
        options = options or ConversionOptions()
        content = read_input(data)
        try:
            return _convert(content, options)
        except (DocumentConversionError, MemoryError):
            raise
        except Exception as error:
            if _encrypted(error):
                raise DocumentConversionError(DocumentFormat.PDF, ENCRYPTED) from error
            reason = str(error) or type(error).__name__
            raise DocumentConversionError(DocumentFormat.PDF, UNREADABLE + reason) from error


def _encrypted(error: BaseException) -> bool:
    names = {"PDFPasswordIncorrect", "PDFEncryptionError", "PasswordError"}
    pending: list[BaseException] = [error]
    while pending:
        current = pending.pop()
        if type(current).__name__ in names:
            return True
        pending.extend(a for a in current.args if isinstance(a, BaseException))
        if current.__cause__ is not None:
            pending.append(current.__cause__)
    return False


@dataclass(frozen=True)
class Line:
    """A visual line; ``top``/``bottom`` measured from the top of the page."""

    text: str
    left: float
    right: float
    top: float
    bottom: float
    size: float
    bold: bool = False
    marker: str | None = None
    """The item start of a bullet or task box drawn before the line (``- ``, ``- [ ] ``)."""
    code: bool = False
    """Set in a monospaced font; ``text`` keeps the spaces between the words."""
    advance: float = 0.0
    """Code: the width of one character, for the indentation."""
    area: int | None = None
    """Code: the filled area (the background of a code block) the line lies in."""


@dataclass(frozen=True)
class Block:
    """The Markdown of a paragraph, table or image, with its position on the page; ``opaque``:
    neither a paragraph that can be a running header nor part of a list."""

    markdown: str
    top: float
    opaque: bool = False


@dataclass(frozen=True)
class PageImage:
    digest: str
    content: bytes
    extension: str
    top: float = 0.0


@dataclass
class PageContent:
    number: int
    blocks: list[Block]
    images: list[PageImage] = field(default_factory=lambda: list[PageImage]())
    skipped_images: int = 0

    @property
    def paragraphs(self) -> list[str]:
        return [b.markdown for b in self.blocks if not b.opaque]


def _convert(data: bytes, options: ConversionOptions) -> MarkdownDocument:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        images = _ImageReader(data) if options.include_images else None
        try:
            pages: list[PageContent] = []
            for page in pdf.pages:
                page = page.filter(_not_rotated)
                try:
                    blocks = page_blocks(page)
                except Exception:
                    blocks = _fallback_blocks(page)
                found, skipped = images.page_images(page) if images else ([], 0)
                pages.append(PageContent(page.page_number, blocks, found, skipped))
            metadata = {MetadataKeys.PAGE_COUNT: str(len(pdf.pages))}
            for key_, name in ((MetadataKeys.TITLE, "Title"), (MetadataKeys.AUTHOR, "Author")):
                value = pdf.metadata.get(name)
                if isinstance(value, str) and value.strip():
                    metadata[key_] = value.strip()
        finally:
            if images:
                images.close()
    skipped_images = sum(p.skipped_images for p in pages)
    if skipped_images:
        metadata[MetadataKeys.SKIPPED_IMAGES] = str(skipped_images)
    resources = ResourceCollector(options.resource_path_prefix)
    markdown = render(pages, resources)
    if options.plain_quotes:
        markdown = typography.plain(markdown)
    return MarkdownDocument(markdown, tuple(resources.resources), metadata)


def _not_rotated(obj: dict[str, Any]) -> bool:
    """Keep everything but rotated or vertical characters (pdfplumber calls 45° text
    ``upright``; a watermark is such text)."""
    if obj.get("object_type") != "char":
        return True
    matrix = obj.get("matrix")
    straight = matrix is None or (abs(matrix[1]) < 1e-6 and abs(matrix[2]) < 1e-6)
    return bool(obj.get("upright", True)) and straight


# --- rendering ---------------------------------------------------------------------------------


def render(pages: Sequence[PageContent], resources: ResourceCollector) -> str:
    """The Markdown of all pages: running headers/footers and images on every page dropped,
    the other images where they stand (DocLibs: after the page's text)."""
    repeated: set[str] = set()
    if len(pages) >= 2:
        counts = Counter(d for p in pages for d in {i.digest for i in p.images})
        repeated = {d for d, n in counts.items() if n == len(pages)}
    images = {p.number: [i for i in p.images if i.digest not in repeated] for p in pages}
    if all(not p.blocks and not images[p.number] for p in pages):
        return ""
    boilerplate = running_paragraphs([p.paragraphs for p in pages])
    out: list[str] = []
    for page in pages:
        out.append(f"## Page {page.number}\n\n")
        paragraphs_ = page.paragraphs
        edge = set(paragraphs_[:2] + paragraphs_[-2:])
        kept = [
            b
            for b in page.blocks
            if b.opaque or b.markdown not in edge or key(b.markdown) not in boilerplate
        ]
        for index, image in enumerate(images[page.number], start=1):
            name = f"page{page.number}-image{index}{image.extension}"
            reference = f"![]({md.destination(resources.add(name, image.content))})"
            position = next((i for i, b in enumerate(kept) if b.top > image.top), len(kept))
            kept.insert(position, Block(reference, image.top, opaque=True))
        previous: str | None = None
        for block in kept:
            if previous is not None:
                # Consecutive list items stay one tight list.
                tight = previous.startswith(ITEM) and block.markdown.startswith(ITEM)
                out.append("\n" if tight else "\n\n")
            out.append(block.markdown)
            previous = "" if block.opaque else block.markdown
        out.append("\n\n")
    return md.normalize("".join(out))


def key(paragraph: str) -> str:
    """A paragraph compared without digits, spaces and Markdown marks (page numbers vary)."""
    return KEY_NOISE.sub("", paragraph.lower())


def running_paragraphs(pages: Sequence[Sequence[str]]) -> set[str]:
    """Keys of running headers and footers: one of the first or last two paragraphs of a page
    whose text, digits ignored, recurs in that position on at least three pages. Unlike DocLibs,
    a key that occurs twice on one page is no header (items of a long list differ only in their
    numbers)."""
    if len(pages) < BOILERPLATE_PAGES:
        return set()
    counts = Counter(
        k
        for paragraphs_ in pages
        for k in {
            key(t) for t in [*paragraphs_[:2], *paragraphs_[-2:]] if len(t) < BOILERPLATE_LENGTH
        }
    )
    repeated_on_a_page = {
        k for paragraphs_ in pages for k, n in Counter(map(key, paragraphs_)).items() if n > 1
    }
    return {k for k, n in counts.items() if n >= BOILERPLATE_PAGES} - repeated_on_a_page


# --- page analysis -----------------------------------------------------------------------------


def page_blocks(page: Any) -> list[Block]:
    """Paragraphs and tables of a pdfplumber page, top to bottom."""
    words = [w for w in page.extract_words(return_chars=True) if w["text"].strip()]
    sizes = [
        round(float(c["size"]) * 2) / 2
        for c in page.chars
        if c["text"].strip() and float(c["size"]) > 0
    ]
    body = Counter(sizes).most_common(1)[0][0] if sizes else 0.0
    tables = _tables(page, words, body)
    boxes = [box for box, _ in tables]
    lines = build_lines(w for w in words if not any(_inside(w, box) for box in boxes))
    lines = mark_items(lines, _markers(page, body or median(line.size for line in lines)))
    lines = code_areas(lines, [_box(r) for r in page.rects if r.get("fill")])
    blocks = paragraphs(lines, body, float(page.height), [box[1] for box in boxes])
    for box, markdown in tables:
        position = next((i for i, b in enumerate(blocks) if b.top > box[1]), len(blocks))
        blocks.insert(position, Block(markdown, box[1], opaque=True))
    return blocks


def _inside(word: dict[str, Any], box: Box) -> bool:
    x = (float(word["x0"]) + float(word["x1"])) / 2
    y = (float(word["top"]) + float(word["bottom"])) / 2
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def build_lines(words: Iterable[dict[str, Any]]) -> list[Line]:
    """Groups words (pdfplumber, with ``chars``) into visual lines: by their bottom edge, as
    DocLibs, or by overlapping most of their height (raised footnote marks)."""
    rows: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda w: float(w["bottom"])):
        top, bottom = float(word["top"]), float(word["bottom"])
        row = rows[-1] if rows else None
        if row is not None:
            row_bottom = statistics.fmean(float(w["bottom"]) for w in row)
            row_top = min(float(w["top"]) for w in row)
            overlap = min(bottom, row_bottom) - max(top, row_top)
            if abs(row_bottom - bottom) <= max(bottom - top, 2) * 0.5 or overlap >= 0.5 * min(
                bottom - top, row_bottom - row_top
            ):
                row.append(word)
                continue
        rows.append([word])
    return [_line(sorted(row, key=lambda w: float(w["x0"]))) for row in rows]


def _line(words: Sequence[dict[str, Any]]) -> Line:
    letters = [c for w in words for c in w.get("chars", ()) if str(c["text"]).strip()]
    fonts = [str(c.get("fontname", "")) for c in letters]
    bold = bool(letters) and sum("bold" in f.lower() for f in fonts) >= len(letters) * BOLD_SHARE
    code = (
        bool(letters)
        and sum(bool(MONOSPACED.search(f)) for f in fonts) >= len(letters) * BOLD_SHARE
    )
    advance = median(float(c["x1"]) - float(c["x0"]) for c in letters) if code else 0.0
    parts: list[str] = []
    for index, word in enumerate(words):
        if index:
            gap = float(word["x0"]) - float(words[index - 1]["x1"])
            if code and advance > 0:
                parts.append(" " * max(1, round(gap / advance)))
            elif gap >= 0.5:  # a raised footnote mark sits right after its word
                parts.append(" ")
        parts.append(str(word["text"]))
    return Line(
        "".join(parts).strip(),
        min(float(w["x0"]) for w in words),
        max(float(w["x1"]) for w in words),
        min(float(w["top"]) for w in words),
        max(float(w["bottom"]) for w in words),
        median(float(c["size"]) for c in letters),
        bold,
        code=code,
        advance=advance,
    )


@dataclass(frozen=True)
class Marker:
    """A bullet or task box drawn as a shape left of a line."""

    box: Box
    start: str


def _markers(page: Any, body: float) -> list[Marker]:
    """Small filled squares and short dashes (bullets) and small empty squares (task boxes,
    ticked when lines are drawn inside) — the shapes of the PDF generator's lists."""
    if body <= 0:
        return []
    result: list[Marker] = []
    ticks = [_box(line) for line in page.lines + page.curves]
    for rect in page.rects:
        box = _box(rect)
        width, height = box[2] - box[0], box[3] - box[1]
        if not (0.2 * body <= width <= 0.9 * body and abs(width - height) <= 0.15 * body):
            continue
        if rect.get("fill") and not rect.get("stroke"):
            result.append(Marker(box, ITEM))
        elif rect.get("stroke"):
            ticked = any(_within(tick, box) for tick in ticks)
            result.append(Marker(box, DONE_TASK if ticked else OPEN_TASK))
    for line in page.lines:
        box = _box(line)
        if box[3] - box[1] < 0.2 * body and 0.3 * body <= box[2] - box[0] <= 1.2 * body:
            result.append(Marker(box, ITEM))
    return result


def _box(obj: dict[str, Any]) -> Box:
    return (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))


def _within(inner: Box, outer: Box) -> bool:
    return (
        inner[0] >= outer[0] - 0.5
        and inner[2] <= outer[2] + 0.5
        and inner[1] >= outer[1] - 0.5
        and inner[3] <= outer[3] + 0.5
    )


def mark_items(lines: Sequence[Line], markers: Sequence[Marker]) -> list[Line]:
    """Lines with a marker shortly before their start (within 2.5 × their size) and within
    their height start a list item."""
    result: list[Line] = []
    for line in lines:
        start = next(
            (
                m.start
                for m in markers
                if line.top <= (m.box[1] + m.box[3]) / 2 <= line.bottom
                and m.box[2] <= line.left + 0.5
                and line.left - m.box[2] <= 2.5 * max(line.size, 1)
            ),
            None,
        )
        result.append(dataclasses.replace(line, marker=start) if start else line)
    return result


def code_areas(lines: Sequence[Line], fills: Sequence[Box]) -> list[Line]:
    """Code lines get the filled area they lie in; a monospaced line outside one without a
    neighbour like it is text (a line of a paragraph that starts with inline code)."""
    result = [
        dataclasses.replace(line, area=_area(line, fills)) if line.code else line for line in lines
    ]
    for index, line in enumerate(result):
        alone = not any(
            0 <= other < len(result) and result[other].code and result[other].area is None
            for other in (index - 1, index + 1)
        )
        if line.code and line.area is None and alone:
            result[index] = dataclasses.replace(line, code=False)
    return result


def _area(line: Line, fills: Sequence[Box]) -> int | None:
    x, y = (line.left + line.right) / 2, (line.top + line.bottom) / 2
    return next((i for i, f in enumerate(fills) if f[0] <= x <= f[2] and f[1] <= y <= f[3]), None)


def paragraphs(
    lines: Sequence[Line], body: float, page_height: float, breaks: Sequence[float] = ()
) -> list[Block]:
    """Joins lines into paragraphs, list items, headings and code blocks (Markdown). ``body``
    is the body text size (0: the median line size); no paragraph spans a position of
    ``breaks`` (tables)."""
    if not lines:
        return []
    if body <= 0:
        body = median(line.size for line in lines)
    margin_top = page_height * MARGIN_SHARE
    margin_bottom = page_height * (1 - MARGIN_SHARE)
    rights = sorted(line.right for line in lines)
    lefts = sorted(line.left for line in lines)
    text_right = rights[int(len(rights) * 0.9)]
    text_left = lefts[int(len(lefts) * 0.1)]
    width = max(text_right - text_left, 1)
    gaps = [b.top - a.bottom for a, b in itertools.pairwise(lines)]
    gaps = [g for g in gaps if g > 0]
    typical_gap = median(gaps) if gaps else body * 0.3

    def in_margin(line: Line) -> bool:
        return line.top < margin_top or line.bottom > margin_bottom

    output: list[Block] = []
    current: list[str] = []
    current_lines: list[Line] = []
    item: str | None = None

    def flush() -> None:
        nonlocal current, current_lines, item
        if current_lines and current_lines[0].code:
            output.append(Block(code_block(current_lines), current_lines[0].top))
        elif (text := "".join(current).strip()) != "":
            size = statistics.fmean(line.size for line in current_lines)
            bold = all(line.bold for line in current_lines)
            markdown = paragraph_markdown(text, size, bold, body, item)
            output.append(Block(markdown, current_lines[0].top))
        current = []
        current_lines = []
        item = None

    previous: Line | None = None
    for line in lines:
        text = line.text
        bullet = None if line.code else line.marker
        stripped = None if line.code or bullet else strip_bullet(text)
        if stripped is not None:
            bullet, text = ITEM, stripped
        if previous is not None:
            gap = line.top - previous.bottom
            if line.code and previous.code:
                if line.area != previous.area or (
                    line.area is None and gap > typical_gap + body * GAP_SHARE
                ):
                    flush()
            elif (
                line.code != previous.code
                or any(previous.bottom <= b <= line.top for b in breaks)
                or gap > typical_gap + body * GAP_SHARE
                or in_margin(previous)
                or in_margin(line)
                or (
                    not line.code
                    and (
                        bullet is not None
                        or starts_numbered(text)
                        or previous.right < text_right - width * EARLY_END  # ended early
                        or line.left < previous.left - body * OUTDENT  # outdent ends an item
                        or abs(line.size - previous.size) > max(previous.size, 1) * SIZE_CHANGE
                    )
                )
            ):
                flush()
        if bullet is not None:
            item = bullet
        join(current, text)
        current_lines.append(line)
        previous = line
    flush()
    return output


def paragraph_markdown(
    text: str, size: float, bold: bool, body: float, item: str | None = None
) -> str:
    """A heading ``###`` when short, no table-of-contents line, not ending in ``.``/``:``
    (unless numbered) and larger than the body or bold and numbered; else an item (``item``
    is its start, ``- `` or a task) or text."""
    numbered = starts_numbered(text)
    heading = (
        item is None
        and len(text) < HEADING_LENGTH
        and not TABLE_OF_CONTENTS_ENTRY.search(text)
        and (numbered or not text.endswith((".", ":")))
        and (size >= body * HEADING_SIZE or (bold and numbered))
    )
    escaped = md.escape(text)
    if heading:
        return "### " + escaped
    return item + escaped if item is not None else md.escape_line_start(escaped)


def code_block(lines: Sequence[Line]) -> str:
    """A fenced code block; indentation from the lines' starts in character widths."""
    left = min(line.left for line in lines)
    advance = median(line.advance for line in lines) or 1.0
    pitch = min(
        (b.top - a.top for a, b in itertools.pairwise(lines) if b.top > a.top),
        default=0.0,
    )
    pitch = min(pitch, 1.5 * median(line.size for line in lines))
    content: list[str] = []
    for index, line in enumerate(lines):
        if index and pitch > 0:  # empty lines of the code take their height
            content.extend([""] * max(0, round((line.top - lines[index - 1].top) / pitch) - 1))
        content.append(" " * round((line.left - left) / advance) + line.text)
    longest = max((len(run) for run in re.findall(r"`+", "\n".join(content))), default=0)
    fence = "`" * max(3, longest + 1)
    return "\n".join([fence, *content, fence])


def join(current: list[str], text: str) -> None:
    """Joins a line onto the paragraph and repairs words hyphenated across lines:
    "Netz-|nutzung" joins, "GELI-|Anmeldung" keeps its hyphen."""
    if not text:
        return
    if not current:
        current.append(text)
        return
    tail = current[-1]
    if tail.endswith("-") and len(tail) >= 2 and tail[-2].isalpha():
        if tail[-2].islower() and text[0].islower():
            current[-1] = tail[:-1]
        current.append(text)
        return
    current.append(" " + text)


def strip_bullet(text: str) -> str | None:
    """The text after a leading bullet glyph, or None if the line is no bullet item."""
    if len(text) < 2:
        return None
    first = text[0]
    if first in STRONG_BULLETS or "" <= first <= "":
        return text[1:].lstrip()
    if first in WEAK_BULLETS and text[1].isspace():
        return text[2:].lstrip()
    return None


def starts_numbered(text: str) -> bool:
    """ "1.", "2.3", "4.1.2 ": numbered headings and items start a new paragraph."""
    return NUMBERED_START.match(text) is not None


def median(values: Iterable[float]) -> float:
    """The upper median of the positive values; 0 without any."""
    ordered = sorted(v for v in values if v > 0)
    return ordered[len(ordered) // 2] if ordered else 0.0


def _fallback_blocks(page: Any) -> list[Block]:
    """Plain text lines when the page analysis fails."""
    text: str = page.extract_text() or ""
    lines = (line.strip() for line in text.replace("\r\n", "\n").split("\n"))
    return [Block(md.escape_line_start(md.escape(line)), 0) for line in lines if line]


# --- tables ------------------------------------------------------------------------------------


def _tables(page: Any, words: Sequence[dict[str, Any]], body: float) -> list[tuple[Box, str]]:
    """Tables with ruling lines as (bounding box, pipe table), top to bottom."""
    found: list[tuple[Box, list[list[str]]]] = []
    for table in page.find_tables(GRID_SETTINGS):
        rows = _rows(table.extract())
        if rows:
            x0, top, x1, bottom = (float(v) for v in table.bbox)
            found.append(((x0, top, x1, bottom), rows))
    rules = [_box(line) for line in page.lines] + [
        _box(r) for r in page.rects if float(r["bottom"]) - float(r["top"]) < 1.5
    ]
    fills = [_box(r) for r in page.rects if r.get("fill")]
    for box, rows in ruled_tables(fills, rules, words, body):
        if not any(_overlaps(box, other) for other, _ in found):
            found.append((box, rows))
    found.sort(key=lambda t: t[0][1])
    return [(box, md.table(rows).rstrip("\n")) for box, rows in found]


def ruled_tables(
    fills: Sequence[Box], rules: Sequence[Box], words: Sequence[dict[str, Any]], body: float
) -> list[tuple[Box, list[list[str]]]]:
    """Tables with a filled header row and horizontal rules only (the style ``PTA``): a fill
    with a rule of the same width along its bottom edge is the header; each further rule of
    that width closes a row as long as the row's text starts as far below the rule above as the
    header's text below its top (a paragraph after the table starts further down)."""
    tolerance = 2.0
    result: list[tuple[Box, list[list[str]]]] = []
    for fill in sorted(fills, key=lambda b: b[1]):
        x0, top, x1, bottom = fill
        if bottom - top < body or x1 - x0 < 10 * body:
            continue
        same = sorted(
            (r for r in rules if abs(r[0] - x0) <= tolerance and abs(r[2] - x1) <= tolerance),
            key=lambda r: r[1],
        )
        if not any(abs(r[1] - bottom) <= tolerance for r in same):
            continue
        header = _band(words, x0, x1, top, bottom)
        if not header:
            continue
        padding = min(float(w["top"]) for w in header) - top
        edges = [top, bottom]
        for rule in same:
            if rule[1] <= edges[-1] + tolerance:
                continue
            row = _band(words, x0, x1, edges[-1], rule[1])
            if not row or min(float(w["top"]) for w in row) - edges[-1] > padding + tolerance:
                break
            edges.append(rule[1])
        if len(edges) < 3:
            continue
        box = (x0, top, x1, edges[-1])
        if any(_overlaps(box, other) for other, _ in result):
            continue
        rows = _ruled_rows(words, box, edges, body)
        if rows:
            result.append((box, rows))
    return result


def _band(
    words: Sequence[dict[str, Any]], x0: float, x1: float, top: float, bottom: float
) -> list[dict[str, Any]]:
    return [w for w in words if _inside(w, (x0, top, x1, bottom))]


def _ruled_rows(
    words: Sequence[dict[str, Any]], box: Box, edges: Sequence[float], body: float
) -> list[list[str]]:
    """Cells: rows between the edges, columns where no word of any row lies."""
    inside = _band(words, box[0], box[2], box[1], box[3])
    spans = sorted((float(w["x0"]), float(w["x1"])) for w in inside)
    columns: list[list[float]] = []
    for start, end in spans:
        if columns and start - columns[-1][1] < max(0.8 * body, 4):
            columns[-1][1] = max(columns[-1][1], end)
        else:
            columns.append([start, end])
    rows: list[list[str]] = []
    for top, bottom in itertools.pairwise(edges):
        cells: list[str] = []
        for start, end in columns:
            cell_words = [
                w
                for w in _band(words, box[0], box[2], top, bottom)
                if start <= (float(w["x0"]) + float(w["x1"])) / 2 <= end
            ]
            parts: list[str] = []
            for line in build_lines(cell_words):
                join(parts, line.text)
            cells.append(md.escape("".join(parts).strip()))
        rows.append(cells)
    return _rows(rows)


def _overlaps(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _rows(extracted: Sequence[Sequence[str | None]]) -> list[list[str]]:
    """The non-empty rows and columns; tables need two of each."""
    rows = md.compact([[_cell(c) for c in row] for row in extracted])
    return rows if len(rows) >= 2 and max(len(r) for r in rows) >= 2 else []


def _cell(value: str | None) -> str:
    parts: list[str] = []
    for line in (value or "").split("\n"):
        join(parts, line.strip())
    return "".join(parts).strip()


# --- images ------------------------------------------------------------------------------------


class _ImageReader:
    """Decodes the images pdfplumber finds through pikepdf: JPEG data as it is, everything
    else as PNG; what cannot be decoded is counted as skipped."""

    def __init__(self, data: bytes) -> None:
        self._pdf: pikepdf.Pdf | None
        try:
            self._pdf = pikepdf.open(io.BytesIO(data))
        except Exception:  # pdfplumber read the file; the images are then skipped
            self._pdf = None

    def close(self) -> None:
        if self._pdf is not None:
            self._pdf.close()

    def page_images(self, page: Any) -> tuple[list[PageImage], int]:
        """The page's images top to bottom and the number of undecodable ones."""
        images: list[PageImage] = []
        skipped = 0
        for image in sorted(page.images, key=lambda i: float(i["top"])):
            decoded = self._decode(image.get("stream"))
            if decoded is None:
                skipped += 1
                continue
            content, extension = decoded
            digest = hashlib.sha256(content).hexdigest()
            images.append(PageImage(digest, content, extension, float(image["top"])))
        return images, skipped

    def _decode(self, stream: Any) -> tuple[bytes, str] | None:
        objid = getattr(stream, "objid", None)
        pdf = self._pdf
        if pdf is None or objid is None:
            return None  # inline images have no object of their own
        generation = getattr(stream, "genno", 0) or 0
        return decode_image(lambda: _pdf_image(pdf.get_object(objid, generation)))


def _pdf_image(obj: pikepdf.Object) -> pikepdf.PdfImage:
    if not isinstance(obj, pikepdf.Stream):
        raise TypeError("not an image stream")
    return pikepdf.PdfImage(obj)


def decode_image(image: Callable[[], pikepdf.PdfImage]) -> tuple[bytes, str] | None:
    """JPEG data unchanged (``.jpg``), anything else Pillow can read as PNG; None: undecodable."""
    try:
        pdf_image = image()
        raw = _jpeg(pdf_image)
        if raw is not None:
            return raw, ".jpg"
        output = io.BytesIO()
        pdf_image.as_pil_image().save(output, format="PNG")
        return output.getvalue(), ".png"
    except Exception:  # unsupported filters or colour spaces count as undecodable
        return None


def _jpeg(image: pikepdf.PdfImage) -> bytes | None:
    """The JPEG data of a ``DCTDecode`` image, undoing filters before it (reportlab writes
    ``ASCII85Decode`` first); None: no JPEG."""
    filters = list(image.filters)
    if filters[-1:] != ["/DCTDecode"]:
        return None
    data = bytes(image.obj.read_raw_bytes())
    if len(filters) > 1:
        if any(p for p in image.decode_parms[:-1]):
            return None  # parameters of the outer filters are not carried over
        with pikepdf.Pdf.new() as scratch:
            stream = pikepdf.Stream(scratch, data)
            stream.Filter = pikepdf.Array([pikepdf.Name(f) for f in filters[:-1]])
            data = bytes(stream.read_bytes())
    return data if data.startswith(b"\xff\xd8\xff") else None
