"""German (and English) typography on the parsed Markdown: quotes, dashes, non-breaking spaces.

The writer types straight characters; ``typeset`` turns the text of a token stream into what a
typesetter would set (E17-S02)::

    "Zitat" - z. B. 10 %   →   „Zitat“ – z. B. 10 %   (U+00A0 in "z. B." and "10 %")

Only the ``text`` children of ``inline`` tokens change: code spans, code blocks, link targets,
autolinks, raw HTML and the attribute block of a heading (``{kicker="Warum"}``) stay as written;
the front matter is not part of the token stream. A quote at the edge of a text child looks at
the neighbouring children (``"**fett**"`` opens before the bold text).

Rules, German: ``"…"`` → ``„…“``, ``'…'`` → ``‚…‘``, an apostrophe in a word (``geht's``) →
``’``; a lone ``-`` or ``--`` between spaces → ``–``; ``...`` → ``…``; a non-breaking space in
abbreviations (``z. B.``, ``u. a.``, ``d. h.``), before a number after ``Nr.``, ``S.``, ``Abs.``
or ``§``, between a number and its unit (``10 %``, ``5 km``, ``3 Mio.``) and in dates
(``1. Januar``). English: ``“…”``, ``‘…’``, dashes, ellipsis and units, no abbreviations.

The narrow non-breaking space (U+202F) is never set: the Office fonts do not all have it.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from markdown_it.token import Token

NBSP: Final = " "
APOSTROPHE: Final = "’"
ELLIPSIS: Final = "…"
EN_DASH: Final = "–"


@dataclass(frozen=True)
class _Quotes:
    double_open: str
    double_close: str
    single_open: str
    single_close: str


_GERMAN: Final = _Quotes("„", "“", "‚", "‘")
_ENGLISH: Final = _Quotes("“", "”", "‘", "’")

_OPENING_CONTEXT: Final = "([{<–—-/„‚“‘«»"
"""After these a quote opens, as after a space."""

_DASH: Final = re.compile(r"(?<=\s)--?(?=\s)")
_UNIT: Final = re.compile(
    r"(?<=\d) (?=(?:%|‰|°C|°F|°|€|\$|£"
    r"|(?:Mio|Mrd|Tsd|Std|Pkt|Min|Sek)\."
    r"|(?:EUR|USD|CHF|GBP|Mio|Mrd|Tsd|km|cm|mm|m|kg|mg|g|t|ml|l|h|min|ms|s"
    r"|kB|KB|MB|GB|TB|PB|kWh|MWh|GWh|TWh|kW|MW|GW|kV|V|mA|A|kHz|MHz|GHz|Hz|px|pt)(?!\w)))"
)
_ABBREVIATION: Final = re.compile(r"(?<![\w.])([A-Za-zÄÖÜäöü]\.) (?=[A-Za-zÄÖÜäöü]{1,2}\.)")
"""``z. B.``, ``u. a.``, ``d. h.``, ``i. d. R.``, ``o. Ä.``, ``z. Hd.``: a one-letter part with a
point, then a short part with a point."""
_BEFORE_NUMBER: Final = re.compile(
    r"((?<![\w.])(?:Nr|Nrn|S|Abs|Art|Kap|Abb|Tab|Ziff|Bd|Fn|Anl|Rn|Tz|Bl|Sp)\.|§) (?=\d)"
)
_MONTHS: Final = (
    "Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"
    r"|Jan\.|Feb\.|Mär\.|Apr\.|Jun\.|Jul\.|Aug\.|Sep\.|Sept\.|Okt\.|Nov\.|Dez\."
)
_DATE: Final = re.compile(rf"((?<!\d)\d{{1,2}}\.) (?={_MONTHS})")


def typeset(tokens: Sequence[Token], language: str = "de") -> None:
    """Set the typography of every inline token of ``tokens`` in place (see the module).

    ``language`` is ``de`` or ``en`` (``sprache:``); any other value is set as German.
    """
    quotes = _ENGLISH if language == "en" else _GERMAN
    german = language != "en"
    for i, token in enumerate(tokens):
        if token.type != "inline" or not token.children:
            continue
        heading = i > 0 and tokens[i - 1].type == "heading_open"
        _typeset_inline(token.children, quotes, german, heading)


def typeset_text(text: str, language: str = "de") -> str:
    """The typography of a text on its own (an image description, a status label)."""
    quotes = _ENGLISH if language == "en" else _GERMAN
    return _Setter(quotes, language != "en").text(text, "", "")


_TRAILING_ATTRIBUTES: Final = re.compile(r"\s*\{[^{}]*\}\s*$")


def _typeset_inline(children: list[Token], quotes: _Quotes, german: bool, heading: bool) -> None:
    setter = _Setter(quotes, german)
    proxies = [_proxy(child) for child in children]
    protected = _protected(children)
    last_text = max((k for k, c in enumerate(children) if c.type == "text"), default=-1)
    for k, child in enumerate(children):
        if child.type == "image":
            child.content = setter.isolated(child.content)
            title = child.attrs.get("title")
            if isinstance(title, str) and title:
                child.attrs["title"] = setter.isolated(title)
            if child.children:
                _typeset_inline(child.children, quotes, german, heading=False)
            continue
        if child.type != "text" or k in protected or not child.content:
            continue
        content = child.content
        suffix = ""
        if heading and k == last_text and (match := _TRAILING_ATTRIBUTES.search(content)):
            content, suffix = content[: match.start()], content[match.start() :]
        before = "".join(proxies[:k])[-1:]
        after = (suffix or "".join(proxies[k + 1 :]))[:1]
        child.content = setter.text(content, before, after) + suffix
        proxies[k] = child.content


def _proxy(child: Token) -> str:
    """What a child stands for when a neighbour looks at it: text as it is, a line break a
    space, a code span or an image a letter (``"`x`"`` closes after it), markup nothing."""
    match child.type:
        case "text":
            return child.content
        case "softbreak" | "hardbreak":
            return " "
        case "code_inline" | "image" | "html_inline" | "footnote_ref" | "icon":
            return "x"
        case _:
            return ""


def _protected(children: list[Token]) -> set[int]:
    """The text children inside an autolink (``<https://…>``): they are the URL."""
    result: set[int] = set()
    inside = False
    for k, child in enumerate(children):
        if child.type == "link_open" and child.markup == "autolink":
            inside = True
        elif child.type == "link_close":
            inside = False
        elif inside:
            result.add(k)
    return result


class _Setter:
    """Sets the text children of one inline token: single quotes may open in one child and
    close in another."""

    def __init__(self, quotes: _Quotes, german: bool) -> None:
        self.quotes = quotes
        self.german = german
        self.open_singles = 0

    def isolated(self, text: str) -> str:
        return _Setter(self.quotes, self.german).text(text, "", "")

    def text(self, text: str, before: str, after: str) -> str:
        text = text.replace("...", ELLIPSIS)
        padded = _DASH.sub(EN_DASH, _pad(before + text + after, before, after))
        padded = _UNIT.sub(NBSP, padded)
        if self.german:
            for rule in (_ABBREVIATION, _ABBREVIATION, _BEFORE_NUMBER, _DATE):
                # Twice for abbreviations: "i. d. R." overlaps.
                padded = rule.sub(_KEEP_TOGETHER, padded)
        # The context (or the edge) is one character on each side; no rule changes its length.
        text = padded[1:-1]
        return self._quotes(text, before, after)

    def _quotes(self, text: str, before: str, after: str) -> str:
        if '"' not in text and "'" not in text:
            return text
        q = self.quotes
        out: list[str] = []
        previous = before
        for n, char in enumerate(text):
            following = text[n + 1] if n + 1 < len(text) else after
            if char == '"':
                if _opens(previous, following):
                    char = q.double_open
                elif _closes(previous):
                    char = q.double_close
            elif char == "'":
                if previous.isalnum() and following.isalnum():
                    char = APOSTROPHE
                elif _opens(previous, following):
                    char = q.single_open
                    self.open_singles += 1
                elif _closes(previous):
                    if self.open_singles:
                        char = q.single_close
                        self.open_singles -= 1
                    else:
                        char = APOSTROPHE
            out.append(char)
            previous = char
        return "".join(out)


def _opens(previous: str, following: str) -> bool:
    at_start = not previous or previous.isspace() or previous in _OPENING_CONTEXT
    return at_start and bool(following) and not following.isspace()


def _closes(previous: str) -> bool:
    return bool(previous) and not previous.isspace()


_EDGE: Final = " "
"""Stands for the start or end of the paragraph, which the dash rule treats as a space."""


def _pad(padded: str, before: str, after: str) -> str:
    return (_EDGE if not before else "") + padded + (_EDGE if not after else "")


_KEEP_TOGETHER: Final = r"\1" + NBSP


def plain(markdown: str) -> str:
    """Markdown with typographic characters back to straight ones, outside code (fences and
    code spans): ``„“”`` → ``"``, ``‚‘’`` → ``'``, ``–`` → ``-``, ``…`` → ``...``, U+00A0 and
    U+202F → space. For converters (``ConversionOptions.plain_quotes``)."""
    out: list[str] = []
    fence: str | None = None
    for line in markdown.split("\n"):
        stripped = line.lstrip()
        if fence is not None:
            out.append(line)
            if stripped.startswith(fence) and not stripped[len(fence) :].strip():
                fence = None
            continue
        if match := _FENCE.match(stripped):
            fence = match.group(0)
            out.append(line)
            continue
        out.append(_plain_line(line))
    return "\n".join(out)


_FENCE: Final = re.compile(r"^(`{3,}|~{3,})")
_CODE_SPAN: Final = re.compile(r"(`+)(?:(?!\1).)+?\1")
_PLAIN: Final = str.maketrans(
    {"„": '"', "“": '"', "”": '"', "‚": "'", "‘": "'", "’": "'", "–": "-", NBSP: " "}
    | {" ": " ", ELLIPSIS: "..."}
)


def _plain_line(line: str) -> str:
    parts: list[str] = []
    position = 0
    for span in _CODE_SPAN.finditer(line):
        parts.append(line[position : span.start()].translate(_PLAIN))
        parts.append(span.group(0))
        position = span.end()
    parts.append(line[position:].translate(_PLAIN))
    return "".join(parts)
