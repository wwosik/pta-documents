"""Style rules of the PTA sample slides, checked on the Markdown (``./run.sh check``, E08-S02).

The PTA sample slides state their rules in words (only the given layouts, no running text in
bullet lists, the same punctuation at the end of every point); the numbers here are our own
proposals, adjustable through ``StyleLimits`` (decision 2026-11-07). Each rule that fires
becomes a ``GenerationNote`` with a ``style-…`` code (``StyleCodes``), like the generators'
notes: the document can still be generated, but the writer should look at it.

Rules work on the tokens of the shared parser, not on the written document: what the writer
typed is what they can change. Speaker notes (``::: notes``) are not on the slide and are left
out of every rule.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterator, Sequence
from dataclasses import dataclass
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import generated_images, heading_attributes
from pta_documents.generation.common.layout_syntax import NOTES
from pta_documents.generation.common.result import GenerationNote, Notes
from pta_documents.markdown.document import MarkdownDocument
from pta_documents.markdown.front_matter import NO, YES, FrontMatter, Keys
from pta_documents.markdown.parser import CONTAINER_OPEN, child_lines, container, line_of, parse


class StyleCodes:
    """The codes of the style notes; each rule can be skipped by its code."""

    BULLETS: Final = "style-bullets"
    """More than seven points on one slide, or a point of more than 20 words (PPTX)."""
    WORDS: Final = "style-words"
    """More than 80 words on one content slide (PPTX)."""
    PUNCTUATION: Final = "style-punctuation"
    """The points of one list end with different punctuation (PPTX, DOCX)."""
    TITLE: Final = "style-title"
    """A slide title of more than 60 characters, or one ending with a full stop (PPTX)."""
    IMAGE_SOURCE: Final = "style-image-source"
    """An image without author or source in its title, caption or on its slide — only for a
    document folder with a ``QUELLEN.md`` or with ``--sources`` (PPTX, DOCX)."""
    ALT_TEXT: Final = "style-alt-text"
    """An image without alt text (``![](…)``) (PPTX, DOCX); E13-S03 extends it."""
    HEADING_NUMBERS: Final = "style-heading-numbers"
    """A heading that starts with its own number although Word numbers it (DOCX)."""

    ALL: Final = (BULLETS, WORDS, PUNCTUATION, TITLE, IMAGE_SOURCE, ALT_TEXT, HEADING_NUMBERS)
    """Every code, in the order the guides list them."""


OFF: Final = "aus"
ON: Final = "an"


@dataclass(frozen=True)
class StyleLimits:
    """The limits of the rules (decision 2026-11-07: the proposed values, adjustable)."""

    bullets: int = 7
    """Points on one slide (every level counts)."""
    bullet_words: int = 20
    """Words of one point (its own text, not that of its sub-points)."""
    slide_words: int = 80
    """Words on one content slide (title and speaker notes not counted)."""
    title_characters: int = 60
    """Characters of a slide title."""


SOURCE_MARKER: Final = re.compile(
    r"\b(?:Fotos?|Bild(?:er)?|Grafik(?:en)?|Quellen?|Photos?|Images?|Sources?|Credits?)\s*:"
    r"|\bCC\b|©|\bgemeinfrei\b|\bpublic domain\b",
    re.IGNORECASE,
)
"""What names an image's author or source: ``Foto: …``, ``Quelle: …``, a CC licence, ``©``."""
OWN_NUMBER: Final = re.compile(r"^\s*\d{1,2}(?:\.\d{1,2})*\.\s+\S|^\s*\d{1,2}(?:\.\d{1,2})+\s+\S")
"""A heading that starts with its own number: ``1. Einleitung``, ``2.3 Ziele`` (not ``2026 …``)."""
_WORD: Final = re.compile(r"\w", re.UNICODE)
_CLOSING_QUOTES: Final = "\"'»«“”„’‘*_"
_NO_SKIP_LIST: Final = (YES, ON)
_SKIP_ALL: Final = (NO, OFF)


def skipped(front: FrontMatter, skip: Collection[str] = ()) -> frozenset[str]:
    """The codes not to check: those of ``skip`` and of the front matter key ``pruefung``
    (``aus``/``nein`` all, ``an``/``ja`` none, else a comma-separated list of codes).

    Raises ``DocumentConversionError`` for a code that does not exist.
    """
    result = set(_valid_codes(skip, front.format, "--skip"))
    value = front.get(Keys.CHECK)
    if value is None or value.strip().lower() in _NO_SKIP_LIST:
        return frozenset(result)
    if value.strip().lower() in _SKIP_ALL:
        return frozenset(StyleCodes.ALL)
    codes = [part.strip() for part in value.split(",") if part.strip()]
    result.update(_valid_codes(codes, front.format, f"The front matter key '{Keys.CHECK}'"))
    return frozenset(result)


def _valid_codes(codes: Collection[str], format: DocumentFormat, where: str) -> list[str]:
    result: list[str] = []
    for code in codes:
        if code.lower() not in StyleCodes.ALL:
            raise DocumentConversionError(
                format,
                f"{where} names '{code}', which is no style rule. Write '{OFF}' to skip all, or "
                f"some of: {', '.join(StyleCodes.ALL)}.",
            )
        result.append(code.lower())
    return result


def style_notes(
    document: MarkdownDocument,
    format: DocumentFormat,
    *,
    sources: bool = False,
    skip: Collection[str] = (),
    limits: StyleLimits | None = None,
) -> tuple[GenerationNote, ...]:
    """The style notes on ``document`` for ``format`` (``PPTX`` or ``DOCX``), sorted by line.

    ``sources`` turns on ``style-image-source`` (the tool does so when the document's folder
    has a ``QUELLEN.md``); ``skip`` names codes not to check, on top of the front matter key
    ``pruefung``. Raises ``DocumentConversionError`` for a broken front matter or an unknown code.
    """
    front = FrontMatter.read(document.text, format)
    off = skipped(front, skip)
    if not sources:
        off |= {StyleCodes.IMAGE_SOURCE}
    notes = Notes()
    rules = _Rules(_body_tokens(front.body), front.body_line, format, limits or StyleLimits())
    rules.check(notes, off)
    return notes.to_tuple()


def _body_tokens(body: str) -> list[Token]:
    """The tokens without footnotes and without anything inside ``::: notes``."""
    tokens = parse(body)
    end = next((i for i, t in enumerate(tokens) if t.type == "footnote_block_open"), None)
    if end is not None:
        tokens = tokens[:end]
    result: list[Token] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == CONTAINER_OPEN and container(token)[0] == NOTES:
            i = close_of(tokens, i) + 1
            continue
        result.append(token)
        i += 1
    return result


def close_of(tokens: Sequence[Token], start: int) -> int:
    """The index of the token that closes ``tokens[start]`` (``…_open`` → ``…_close``)."""
    opening = tokens[start]
    closing = opening.type.removesuffix("_open") + "_close"
    for i in range(start + 1, len(tokens)):
        if tokens[i].type == closing and tokens[i].level == opening.level:
            return i
    return len(tokens) - 1


def words(text: str) -> int:
    """The number of words: runs of non-blank characters with a letter or digit in them."""
    return sum(1 for part in text.split() if _WORD.search(part))


def inline_text(inline: Token) -> str:
    """The text of an inline token as it reads: line breaks are spaces, images left out."""
    parts: list[str] = []
    for child in inline.children or []:
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
    return "".join(parts)


def heading_text(inline: Token, format: DocumentFormat) -> tuple[str, str | None]:
    """The text of a heading without its attributes, and its slide kind (``agenda`` …)."""
    text = inline_text(inline)
    try:
        bare, attributes = heading_attributes.split(text, format)
    except DocumentConversionError:
        return text.strip(), None  # the generator reports it
    return bare.strip(), attributes.kind if attributes else None


@dataclass(frozen=True)
class _Section:
    """A slide of the Markdown: a level-0 ``#``/``##`` heading and the tokens up to the next."""

    heading: int
    """The index of the ``heading_open`` token."""
    end: int
    tag: str
    title: str
    kind: str | None


class _Rules:
    def __init__(
        self, tokens: list[Token], offset: int, format: DocumentFormat, limits: StyleLimits
    ) -> None:
        self.tokens = tokens
        self.offset = offset
        self.format = format
        self.limits = limits

    def line(self, token: Token) -> int | None:
        return line_of(token, self.offset)

    def check(self, notes: Notes, off: Collection[str]) -> None:
        def wanted(code: str) -> bool:
            return code not in off

        if self.format is DocumentFormat.PPTX:
            sections = list(self.sections())
            for index, section in enumerate(sections):
                if wanted(StyleCodes.TITLE):
                    self.title(section, index == 0 and section.tag == "h1", notes)
                if section.tag != "h2" or section.kind == heading_attributes.CONTACT:
                    continue
                if wanted(StyleCodes.BULLETS):
                    self.bullets(section, notes)
                if wanted(StyleCodes.WORDS):
                    self.slide_words(section, notes)
                if wanted(StyleCodes.IMAGE_SOURCE):
                    self.slide_sources(section, notes)
        else:
            if wanted(StyleCodes.HEADING_NUMBERS):
                self.heading_numbers(notes)
            if wanted(StyleCodes.IMAGE_SOURCE):
                self.caption_sources(notes)
        if wanted(StyleCodes.PUNCTUATION):
            self.punctuation(notes)
        if wanted(StyleCodes.ALT_TEXT):
            self.alt_texts(notes)

    # ------------------------------------------------------------------ slides

    def sections(self) -> Iterator[_Section]:
        tokens = self.tokens
        starts = [
            i
            for i, t in enumerate(tokens)
            if t.type == "heading_open" and t.tag in ("h1", "h2") and t.level == 0
        ]
        for n, start in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else len(tokens)
            title, kind = heading_text(tokens[start + 1], self.format)
            yield _Section(start, end, tokens[start].tag, title, kind)

    def title(self, section: _Section, cover: bool, notes: Notes) -> None:
        if cover or section.kind in (heading_attributes.QUOTE, heading_attributes.INTERIM):
            return  # the cover title, a quote and a statement may be long sentences
        line = self.line(self.tokens[section.heading])
        limit = self.limits.title_characters
        if len(section.title) > limit:
            notes.add(
                StyleCodes.TITLE,
                line,
                f'The slide title "{section.title}" has {len(section.title)} characters, more '
                f"than {limit}. Shorten it; details go on the slide.",
            )
        if section.title.endswith(".") and not section.title.endswith(".."):
            notes.add(
                StyleCodes.TITLE,
                line,
                f'The slide title "{section.title}" ends with a full stop. Leave it out.',
            )

    def bullets(self, section: _Section, notes: Notes) -> None:
        tokens = self.tokens
        items = [
            i for i in range(section.heading, section.end) if tokens[i].type == "list_item_open"
        ]
        limit = self.limits.bullets
        if len(items) > limit and section.kind != heading_attributes.AGENDA:
            notes.add(
                StyleCodes.BULLETS,
                self.line(tokens[section.heading]),
                f'The slide "{section.title}" has {len(items)} points, more than {limit}. '
                "Keep the most important ones or split the slide.",
            )
        for item in items:
            count = words(self.item_text(item))
            if count > self.limits.bullet_words:
                notes.add(
                    StyleCodes.BULLETS,
                    self.line(tokens[item]),
                    f"A point of {count} words is running text, more than "
                    f"{self.limits.bullet_words}. Shorten it to a key phrase, or write it as a "
                    "paragraph.",
                )

    def slide_words(self, section: _Section, notes: Notes) -> None:
        count = self.words_between(section.heading + 3, section.end)
        limit = self.limits.slide_words
        if count > limit:
            notes.add(
                StyleCodes.WORDS,
                self.line(self.tokens[section.heading]),
                f'The slide "{section.title}" has {count} words, more than {limit}. Shorten it, '
                "split it, or move details into the speaker notes (::: notes).",
            )

    def words_between(self, start: int, end: int) -> int:
        """The words of the inline tokens in ``tokens[start:end]`` (code blocks not counted)."""
        return sum(words(inline_text(t)) for t in self.tokens[start:end] if t.type == "inline")

    def slide_sources(self, section: _Section, notes: Notes) -> None:
        tokens = self.tokens[section.heading : section.end]
        if any(t.type == "inline" and SOURCE_MARKER.search(inline_text(t)) for t in tokens):
            return  # the slide names them, e.g. "Foto: Jakub Hałun, CC BY-SA 4.0"
        for image, line in self.images(section.heading, section.end):
            if needs_source(image):
                notes.add(StyleCodes.IMAGE_SOURCE, line, self.source_message(image))

    # ------------------------------------------------------------------ documents

    def heading_numbers(self, notes: Notes) -> None:
        tokens = self.tokens
        for i, token in enumerate(tokens):
            if token.type != "heading_open" or token.level != 0 or token.tag not in WORD_NUMBERED:
                continue
            text = inline_text(tokens[i + 1])
            if OWN_NUMBER.match(text):
                notes.add(
                    StyleCodes.HEADING_NUMBERS,
                    self.line(token),
                    f'The heading "{text.strip()}" has its own number, but Word numbers '
                    "headings itself. Leave the number out.",
                )

    def caption_sources(self, notes: Notes) -> None:
        tokens = self.tokens
        inlines = [i for i, t in enumerate(tokens) if t.type == "inline"]
        for n, i in enumerate(inlines):
            nearby = [tokens[i]] + ([tokens[inlines[n + 1]]] if n + 1 < len(inlines) else [])
            if any(SOURCE_MARKER.search(inline_text(t)) for t in nearby):
                continue  # in the paragraph of the image or the one after it
            for image, line in self.images(i, i + 1):
                if needs_source(image):
                    notes.add(StyleCodes.IMAGE_SOURCE, line, self.source_message(image))

    def source_message(self, image: Token) -> str:
        return (
            f"The image '{image.attrs.get('src')}' names no author or source. Write them in its "
            'title (![…](bild.jpg "… (Foto: Name, CC BY 4.0)")) or on the '
            + ("slide" if self.format is DocumentFormat.PPTX else "line below it")
            + ", and in QUELLEN.md."
        )

    # ------------------------------------------------------------------ both

    def punctuation(self, notes: Notes) -> None:
        tokens = self.tokens
        for i, token in enumerate(tokens):
            if token.type not in ("bullet_list_open", "ordered_list_open"):
                continue
            end = close_of(tokens, i)
            items = [
                j
                for j in range(i + 1, end)
                if tokens[j].type == "list_item_open" and tokens[j].level == token.level + 1
            ]
            endings: list[str] = []
            for item in items:
                text = self.item_text(item)
                if not text.strip():
                    continue
                ending = ending_of(text)
                if ending == ":" and self.has_sub_list(item):
                    continue  # "Mitnehmen:" introducing its sub-points
                endings.append(ending)
            if len(endings) > 2 and all(e and e in ",;" for e in endings[:-1]) and endings[-1]:
                # "a;", "b;", "c." — an enumeration ends differently on purpose.
                endings = endings[:-1]
            if len(set(endings)) > 1:
                shown = ", ".join(f"'{e}'" if e else "none" for e in sorted(set(endings)))
                notes.add(
                    StyleCodes.PUNCTUATION,
                    self.line(token),
                    f"The points of this list end with different punctuation ({shown}). End "
                    "them all the same way, usually without a full stop.",
                )

    def alt_texts(self, notes: Notes) -> None:
        for image, line in self.images(0, len(self.tokens)):
            if not image.content.strip():
                notes.add(
                    StyleCodes.ALT_TEXT,
                    line,
                    f"The image '{image.attrs.get('src')}' has no alt text. Say in the brackets "
                    "what it shows: ![Blick auf den Gipfel](…).",
                )

    def images(self, start: int, end: int) -> Iterator[tuple[Token, int | None]]:
        for token in self.tokens[start:end]:
            if token.type != "inline":
                continue
            for child, line in zip(
                token.children or [], child_lines(token, self.offset), strict=True
            ):
                if child.type == "image":
                    yield child, line

    def item_text(self, item: int) -> str:
        """The own text of the list item at ``item``: its paragraphs, not its sub-points."""
        tokens = self.tokens
        end = close_of(tokens, item)
        level = tokens[item].level + 2
        return " ".join(
            inline_text(t)
            for t in tokens[item + 1 : end]
            if t.type == "inline" and t.level == level
        )

    def has_sub_list(self, item: int) -> bool:
        tokens = self.tokens
        end = close_of(tokens, item)
        return any(
            t.type in ("bullet_list_open", "ordered_list_open") for t in tokens[item + 1 : end]
        )


WORD_NUMBERED: Final = ("h1", "h2", "h3")
"""The headings Word numbers ("Überschrift 1-3"); deeper ones are "Zwischenüberschrift"."""


def ending_of(text: str) -> str:
    """The punctuation a point ends with (``.``, ``:``, ``;`` …), "" for none; ``!`` and ``?``
    count as ``.``."""
    stripped = text.rstrip().rstrip(_CLOSING_QUOTES).rstrip()
    if not stripped:
        return ""
    last = stripped[-1]
    if last in ".!?…":
        return "" if stripped.endswith(("...", "…")) else "."
    return last if last in ",;:" else ""


def needs_source(image: Token) -> bool:
    """Whether ``image`` lacks an author or source in its title; a generated image (a QR code,
    E11-S04) has none to name."""
    if generated_images.is_generated(str(image.attrs.get("src", ""))):
        return False
    return not SOURCE_MARKER.search(str(image.attrs.get("title") or ""))
