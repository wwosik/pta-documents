"""Code blocks in colour: Pygments tokens mapped onto the PTA scheme (E17-S02).

The language comes from the fence (```` ```python ````). Keywords are PTA blue and bold,
strings dark blue, comments grey and italic, numbers and constants dark grey, everything else
the text colour of the format. No token gets a background: the code area keeps its grey.
A block without a language, in an unknown one, or with highlighting off shows in one colour.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Keyword, Name, Number, Operator, String, _TokenType
from pygments.util import ClassNotFound

from pta_documents.design import colors
from pta_documents.generation.common.code_blocks import KNOWN_GRAPHIC_LANGUAGES, fence_language
from pta_documents.generation.common.result import NoteCodes, Notes


class CodeKind(StrEnum):
    """What a piece of code is, as far as its colour goes."""

    KEYWORD = "keyword"
    STRING = "string"
    COMMENT = "comment"
    NUMBER = "number"
    TEXT = "text"


@dataclass(frozen=True)
class CodeLook:
    color: str | None
    """RGB hex; None: the text colour of the format."""
    bold: bool = False
    italic: bool = False


LOOKS: Final = {
    CodeKind.KEYWORD: CodeLook(colors.PTA_BLUE, bold=True),
    CodeKind.STRING: CodeLook(colors.DARK_BLUE),
    CodeKind.COMMENT: CodeLook(colors.GREY_DARK, italic=True),
    CodeKind.NUMBER: CodeLook(colors.TEXT_SLIDES),
    CodeKind.TEXT: CodeLook(None),
}
"""The PTA scheme of each kind."""


@dataclass(frozen=True)
class CodeSpan:
    text: str
    kind: CodeKind = CodeKind.TEXT

    @property
    def look(self) -> CodeLook:
        return LOOKS[self.kind]


CodeLine = tuple[CodeSpan, ...]
"""The spans of one line of code; an empty line has none."""


def lexer(language: str) -> Lexer | None:
    """The Pygments lexer of a fence language (``python``, ``cs``, ``sql`` …); None if unknown."""
    if not language:
        return None
    try:
        return get_lexer_by_name(language, stripnl=False, stripall=False, ensurenl=False)
    except ClassNotFound:
        return None


def highlight(lines: Sequence[str], language: str) -> tuple[CodeLine, ...] | None:
    """The spans of each line of the code in ``language``; None when the language is unknown
    (or empty): the code shows in one colour. As many lines as given."""
    found = lexer(language)
    if found is None:
        return None
    result: list[list[CodeSpan]] = [[]]
    for token_type, value in found.get_tokens("\n".join(lines)):
        kind = _kind(token_type)
        for n, part in enumerate(value.split("\n")):
            if n:
                result.append([])
            if part:
                _add(result[-1], part, kind)
    while len(result) < len(lines):
        result.append([])
    return tuple(tuple(line) for line in result[: len(lines)])


def highlight_fence(
    info: str, lines: Sequence[str], line: int | None, notes: Notes, enabled: bool = True
) -> tuple[CodeLine, ...] | None:
    """``highlight`` for a fence's info string, noting ``code-language-unknown`` when a language
    is given that has no lexer (graphic languages have their own ``code-not-drawn`` note)."""
    if not enabled:
        return None
    language = fence_language(info)
    result = highlight(lines, language)
    if result is None and language and language not in KNOWN_GRAPHIC_LANGUAGES:
        notes.add(
            NoteCodes.CODE_LANGUAGE_UNKNOWN,
            line,
            f"The code block language `{language}` is unknown, so the block shows in one colour. "
            "Write a known language (python, csharp, sql, json, yaml, bash …) or none.",
        )
    return result


def _add(spans: list[CodeSpan], text: str, kind: CodeKind) -> None:
    if spans and (spans[-1].kind == kind or not text.strip()):
        # Spaces join the span before them: fewer runs, and nothing shows of their look.
        spans[-1] = CodeSpan(spans[-1].text + text, spans[-1].kind)
    else:
        spans.append(CodeSpan(text, kind if text.strip() else CodeKind.TEXT))


def _kind(token_type: _TokenType) -> CodeKind:
    if token_type in Comment:
        return CodeKind.COMMENT
    if token_type in String:
        return CodeKind.STRING
    if token_type in Number or token_type in Keyword.Constant or token_type in Name.Constant:
        return CodeKind.NUMBER
    if token_type in Keyword or token_type in Operator.Word:
        return CodeKind.KEYWORD
    return CodeKind.TEXT
