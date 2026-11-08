"""Versions of one document for its audiences (E16-S01): customer, internal, trainer.

One Markdown source, three versions. What only PTA may read goes in ``::: internal`` or behind
``{.internal}`` (a block marker on the block after it, or a heading attribute on a ``#`` or
``##``: the whole chapter or slide, speaker notes and all); exercises go in ``::: exercise``,
their solutions in ``::: solution`` right after (or inside) the exercise.

=========  =================================================
``kunde``    neither internal blocks nor solutions (the default)
``intern``   internal blocks, no solutions
``trainer``  everything
=========  =================================================

The version is a filtered token stream: every generator calls ``filter_tokens`` right after
``layout_syntax.check`` (which checks the syntax in every version alike) and then works on what
is left, so DOCX, PPTX, PDF and the HTML deck know nothing of audiences, and the converters
read only what is there. The containers themselves are taken away and their content stays as
if it had been written without them; ``{.internal}`` goes once it has done its work. One note
``audience-omitted`` says how many blocks a version left out.

Usage::

    tokens = filter_tokens(tokens, Audience.KUNDE, notes, DocumentFormat.PPTX)
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Final

from markdown_it.token import Token

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import heading_attributes
from pta_documents.generation.common.result import NoteCodes, Notes
from pta_documents.markdown import block_markers
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.markdown.parser import (
    CONTAINER_CLOSE,
    CONTAINER_OPEN,
    container,
    line_of,
    parse,
)

INTERNAL: Final = "internal"
"""``::: internal``: only in the internal and the trainer version."""
EXERCISE: Final = "exercise"
"""``::: exercise``: an exercise, in every version."""
SOLUTION: Final = "solution"
"""``::: solution``: the solution of the exercise right before it (or around it), only in the
trainer version."""
CONTAINER_NAMES: Final = (INTERNAL, EXERCISE, SOLUTION)

SUFFIXES: Final = {"kunde": "", "intern": "-intern", "trainer": "-trainer"}
"""What ``./run.sh generate`` appends to the file name of each version."""


class Audience(StrEnum):
    """Who a version of a document is for (``fassung:``, ``--audience``)."""

    KUNDE = "kunde"
    """The customer: no internal blocks, no solutions. The default."""
    INTERN = "intern"
    """PTA: internal blocks, no solutions."""
    TRAINER = "trainer"
    """The trainer: everything, solutions included."""

    @property
    def shows_internal(self) -> bool:
        return self is not Audience.KUNDE

    @property
    def shows_solutions(self) -> bool:
        return self is Audience.TRAINER

    @property
    def suffix(self) -> str:
        """``""``, ``-intern`` or ``-trainer``: the end of the file name of the version."""
        return SUFFIXES[self.value]


VALUES: Final = ", ".join(a.value for a in Audience)


def resolve(front: FrontMatter, requested: Audience | None) -> Audience:
    """The audience of a document: ``requested`` (``--audience``, the generator options) if
    given, else ``fassung:`` of the front matter, else ``kunde``. A wrong ``fassung:`` raises
    either way."""
    value = front.get(Keys.AUDIENCE)
    written = (
        None
        if value is None
        else front.one_of(Keys.AUDIENCE, value, ((a.value, a) for a in Audience))
    )
    return requested or written or Audience.KUNDE


def needs_marking(audience: Audience, front: FrontMatter) -> bool:
    """Whether the version gets the marking ``intern`` (E12-S03, E04-S05): every version but
    the customer's, unless the front matter sets ``kennzeichnung:`` itself."""
    return audience is not Audience.KUNDE and front.get(Keys.MARKING) is None


# ---------------------------------------------------------------------- checking


def check(tokens: Sequence[Token], format: DocumentFormat, line_offset: int = 0) -> None:
    """Raise for audience syntax that is wrong in some version (``layout_syntax.check`` calls
    it, so every version and every format refuses the same mistakes): a ``::: solution`` with
    no ``::: exercise`` right before or around it, a ``#``/``##`` heading in one of the three
    containers, ``{.internal}`` on a heading inside a container, another block marker on one of
    the containers."""
    names: list[str] = []
    for i, token in enumerate(tokens):
        line = line_of(token, line_offset)
        if token.type == CONTAINER_CLOSE:
            if names:
                names.pop()
            continue
        if token.type == CONTAINER_OPEN:
            name = container(token)[0]
            if name == SOLUTION and EXERCISE not in names and not _after_exercise(tokens, i):
                raise _error(
                    format,
                    line,
                    "A '::: solution' needs a '::: exercise' right before it (or around it).",
                )
            marker = token.meta.get(block_markers.MARKER)
            if (
                name in CONTAINER_NAMES
                and isinstance(marker, block_markers.Marker)
                and marker.name != block_markers.INTERNAL
            ):
                raise _error(
                    format,
                    marker.line + 1 + line_offset,
                    f"The block marker '{marker.text}' cannot mark a '::: {name}': put it inside, "
                    "on the line right before the block it marks.",
                )
            names.append(name)
        elif token.type == "heading_open" and token.tag in ("h1", "h2"):
            inside = next((n for n in reversed(names) if n in CONTAINER_NAMES), None)
            if inside is not None:
                raise _error(
                    format,
                    line,
                    f"A '{'#' * int(token.tag[1])}' heading cannot stand in a '::: {inside}': "
                    "it starts a chapter or slide. Put '{.internal}' on the heading to leave "
                    "out the whole chapter or slide.",
                )
            if token.level != 0 and _internal_heading(tokens[i + 1], format):
                raise _error(
                    format,
                    line,
                    "'{.internal}' goes on a '#' or '##' heading of the document, not on one in a "
                    "container or quote; put the block in '::: internal' instead.",
                )


def _after_exercise(tokens: Sequence[Token], i: int) -> bool:
    """Whether the block before ``tokens[i]`` is a ``::: exercise`` (on the same level)."""
    if i == 0 or tokens[i - 1].type != CONTAINER_CLOSE:
        return False
    level = tokens[i - 1].level
    for j in range(i - 2, -1, -1):
        if tokens[j].type == CONTAINER_OPEN and tokens[j].level == level:
            return container(tokens[j])[0] == EXERCISE
    return False


def _internal_heading(inline: Token, format: DocumentFormat) -> bool:
    children = inline.children or []
    if not children or children[-1].type != "text":
        return False
    _, attributes = heading_attributes.split(children[-1].content, format)
    return attributes is not None and attributes.internal


def _error(format: DocumentFormat, line: int | None, reason: str) -> DocumentConversionError:
    return DocumentConversionError(format, (f"Line {line}: " if line is not None else "") + reason)


# ---------------------------------------------------------------------- filtering


class _Count:
    def __init__(self) -> None:
        self.internal = 0
        self.solutions = 0


def filter_tokens(
    tokens: list[Token],
    audience: Audience,
    notes: Notes | None = None,
    format: DocumentFormat = DocumentFormat.DOCX,
    line_offset: int = 0,
) -> list[Token]:
    """The tokens of the version for ``audience`` (``tokens`` as ``layout_syntax.check``
    passed them; changed in place where kept: levels and markers).

    Left out are, for ``kunde``, ``::: internal``, every block after ``{.internal}`` and every
    chapter (``#``) or slide (``##``) whose heading has ``{.internal}`` — up to the next heading
    of its level or above — and for ``kunde`` and ``intern`` every ``::: solution``. The three
    containers that stay are unwrapped: their blocks stand where they stood, one level up.
    When anything was left out, ``notes`` gets one ``audience-omitted`` note with the numbers.
    In a deck the first ``#`` (the title slide) cannot be internal: that raises.
    """
    _check_title(tokens, format, line_offset)
    count = _Count()
    kept: list[Token] = []
    unwrapped: list[bool] = []
    """For each open container: whether it is one of the three and is taken away."""
    depth = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        drop = _dropped(tokens, i, audience, format)
        if drop is not None:
            end, solution = drop
            if solution:
                count.solutions += 1
            else:
                count.internal += 1
            i = end
            continue
        marker = token.meta.get(block_markers.MARKER)
        if isinstance(marker, block_markers.Marker) and marker.name == block_markers.INTERNAL:
            del token.meta[block_markers.MARKER]
        if token.type == CONTAINER_OPEN:
            own = container(token)[0] in CONTAINER_NAMES
            unwrapped.append(own)
            if own:
                depth += 1
                i += 1
                continue
        elif token.type == CONTAINER_CLOSE and unwrapped and unwrapped.pop():
            depth -= 1
            i += 1
            continue
        if depth:
            token.level -= depth
        kept.append(token)
        i += 1
    if notes is not None and (count.internal or count.solutions):
        notes.add(
            NoteCodes.AUDIENCE_OMITTED,
            None,
            omitted_message(count.internal, count.solutions, audience),
        )
    return kept


def omitted_message(internal: int, solutions: int, audience: Audience) -> str:
    """The note: how many blocks were left out (``12 internal blocks and 3 solutions were left
    out for the audience 'kunde'``) and which ``--audience`` shows them."""
    parts: list[str] = []
    if internal:
        parts.append(f"{internal} internal block{'s' if internal != 1 else ''}")
    if solutions:
        parts.append(f"{solutions} solution{'s' if solutions != 1 else ''}")
    verb = "was" if internal + solutions == 1 else "were"
    shows = Audience.INTERN if internal and not solutions else Audience.TRAINER
    return (
        f"{' and '.join(parts)} {verb} left out for the audience '{audience.value}'; "
        f"'--audience {shows.value}' (or 'fassung: {shows.value}') shows "
        f"{'them' if len(parts) == 1 else 'both'}."
    )


def _dropped(
    tokens: list[Token], i: int, audience: Audience, format: DocumentFormat
) -> tuple[int, bool] | None:
    """Where the block at ``tokens[i]`` ends and whether it is a solution, when the version
    leaves it out; None when it stays."""
    token = tokens[i]
    marker = token.meta.get(block_markers.MARKER)
    internal_marker = (
        isinstance(marker, block_markers.Marker) and marker.name == block_markers.INTERNAL
    )
    if not audience.shows_internal:
        if internal_marker:
            return _block_end(tokens, i), False
        if token.type == CONTAINER_OPEN and container(token)[0] == INTERNAL:
            return _block_end(tokens, i), False
        if (
            token.type == "heading_open"
            and token.tag in ("h1", "h2")
            and token.level == 0
            and _internal_heading(tokens[i + 1], format)
        ):
            return _section_end(tokens, i), False
    if (
        not audience.shows_solutions
        and token.type == CONTAINER_OPEN
        and container(token)[0] == SOLUTION
    ):
        return _block_end(tokens, i), True
    return None


def _block_end(tokens: list[Token], i: int) -> int:
    """The index after the block that starts at ``tokens[i]``."""
    token = tokens[i]
    if token.nesting != 1:
        return i + 1
    j = i + 1
    while not (tokens[j].nesting == -1 and tokens[j].level == token.level):
        j += 1
    return j + 1


def _section_end(tokens: list[Token], i: int) -> int:
    """The index of the next heading of the document at the level of ``tokens[i]`` or above
    (``#`` ends a ``##`` slide and a ``#`` chapter, ``##`` only a slide), or of the footnotes."""
    levels = ("h1",) if tokens[i].tag == "h1" else ("h1", "h2")
    for j in range(i + 1, len(tokens)):
        token = tokens[j]
        if token.level != 0:
            continue
        if token.type == "heading_open" and token.tag in levels:
            return j
        if token.type == "footnote_block_open":
            return j
    return len(tokens)


def _check_title(tokens: list[Token], format: DocumentFormat, line_offset: int) -> None:
    """In a deck the first ``#`` is the title slide: it is in every version."""
    if format not in (DocumentFormat.PPTX, DocumentFormat.HTML):
        return
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1" and token.level == 0:
            if _internal_heading(tokens[i + 1], format):
                raise _error(
                    format,
                    line_of(token, line_offset),
                    "The first '#' heading is the title slide, which every version shows: it "
                    "takes no '{.internal}'. Put it on the chapters and slides after it.",
                )
            return


# ---------------------------------------------------------------------- versions


def of(markdown: str, format: DocumentFormat, requested: Audience | None = None) -> Audience:
    """The audience a generator takes for ``markdown`` (front matter included), as
    ``resolve`` does: for the file names of ``./run.sh generate``."""
    return resolve(FrontMatter.read(markdown, format), requested)


def versions(markdown: str, format: DocumentFormat) -> tuple[Audience, ...]:
    """The audiences whose versions of ``markdown`` differ, in the order ``kunde``, ``intern``,
    ``trainer``: of versions with the same token stream only the first (``--audience alle``).
    ``kunde`` is always there."""
    body = FrontMatter.read(markdown, format).body
    seen: list[tuple[tuple[object, ...], ...]] = []
    result: list[Audience] = []
    for audience in Audience:
        mark = signature(filter_tokens(parse(body), audience, None, format))
        if mark not in seen:
            seen.append(mark)
            result.append(audience)
    return tuple(result)


def signature(tokens: Sequence[Token]) -> tuple[tuple[object, ...], ...]:
    """What makes two token streams the same version."""
    return tuple(
        (t.type, t.tag, t.level, t.content, t.info, tuple(t.map or ()), str(t.meta)) for t in tokens
    )
