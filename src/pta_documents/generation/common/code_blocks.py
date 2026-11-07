"""Fenced code blocks: drawn by the code-block renderers, or shown as code.

Blocks in ``KNOWN_GRAPHIC_LANGUAGES`` are meant to be drawn; when no renderer draws one, it shows
as code with a ``code-not-drawn`` note.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from pta_documents.design.variants import Language
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import renderers as code_block_renderers
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRenderer,
    CodeBlockRequest,
    ImageGraphic,
)
from pta_documents.generation.common.result import NoteCodes, Notes

KNOWN_GRAPHIC_LANGUAGES: Final = ("mermaid", "chart", "financial-chart")


def fence_language(info: str) -> str:
    """The language of a fence's info string: its first word, lower case (``""`` if none)."""
    words = info.split(maxsplit=1)
    return words[0].lower() if words else ""


def note_not_drawn(notes: Notes, info: str, line: int | None) -> None:
    """Note a block in a graphic language that shows as code because nothing drew it."""
    language = fence_language(info)
    if language in KNOWN_GRAPHIC_LANGUAGES:
        notes.add(
            NoteCodes.CODE_NOT_DRAWN,
            line,
            f"The `{language}` block was not drawn and shows as code: no renderer for it is "
            "set up, or it has an error. Check it, or leave it out.",
        )


def draw(
    renderers: Sequence[CodeBlockRenderer],
    notes: Notes,
    info: str,
    code: str,
    line: int | None,
    format: DocumentFormat,
    language: Language,
    dark: bool = False,
) -> ImageGraphic | None:
    """The image a renderer makes of a fence; None: the fence stays code (noted if it is in a
    graphic language).

    A fence goes to the renderers only with an info string. Drawings and charts raise until the
    generator places them (``render_graphic`` and ``unsupported`` for those that do).
    """
    graphic = render_graphic(renderers, notes, info, code, line, format, language, dark)
    if graphic is None or isinstance(graphic, ImageGraphic):
        return graphic
    raise unsupported(graphic, info, line, format)


def render_graphic(
    renderers: Sequence[CodeBlockRenderer],
    notes: Notes,
    info: str,
    code: str,
    line: int | None,
    format: DocumentFormat,
    language: Language,
    dark: bool = False,
) -> CodeBlockGraphic | None:
    """The graphic a renderer makes of a fence, of any kind; None: the fence stays code (noted if
    it is in a graphic language). For generators that place some drawings or charts themselves."""
    info = info.strip()
    graphic = None
    if info:
        request = CodeBlockRequest(info, code, line, format, language, dark)
        graphic = code_block_renderers.render(renderers, request)
    if graphic is None:
        note_not_drawn(notes, info, line)
    return graphic


def unsupported(
    graphic: CodeBlockGraphic, info: str, line: int | None, format: DocumentFormat
) -> DocumentConversionError:
    """The error for a graphic of a kind the generator of ``format`` does not place yet."""
    kind = "chart" if isinstance(graphic, ChartGraphic) else "drawing"
    where = f"Line {line}: " if line else ""
    return DocumentConversionError(
        format,
        f"{where}The `{fence_language(info.strip())}` block was rendered as a {kind}, which "
        f"{format.value.upper()} does not support yet. Leave the block out, or turn off the "
        "renderer that takes it.",
    )
