"""The guide of the tool ``make_document`` (E08-S04; after ``CombinedGuide.cs`` of vt-tools-libs).

For one format it is that generator's own guide. For several, the guides are merged so that
everything is said once: the sections are matched by their ``##`` heading (outside code
blocks), and within a section the paragraphs, list items, table rows and code blocks by their
text (``difflib``). What all offered formats share stands once and unmarked; what only some
have is marked „Nur Word“, „Nur PowerPoint“ … — a section as a whole in its heading, a table or
list as a whole in a line before it, a single row, item or paragraph in itself. Table heads of
the same shape are one head („In Word / Im PDF“); table rows with the same first cell are one
row whose differing cells name each format's value (so the front matter is one row per key). A
``### Hinweise`` that another guide has as a section of its own becomes one, so that both meet
(``_promote``). Word and the PDF are merged first (``MERGE_ORDER``): they share one guide.
A section „Formate“ comes first and says what
``format`` chooses. The host's notes come last, under ``## In dieser Anwendung`` unless they
start with a heading of their own.

The merge works on the generated guides, not on their templates, so it follows every change of
a guide without code here; a sentence that differs between the formats simply stands twice,
marked.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import StrEnum
from typing import Final

from pta_documents.errors import DocumentFormat

DOCX: Final = DocumentFormat.DOCX
PPTX: Final = DocumentFormat.PPTX
PDF: Final = DocumentFormat.PDF

LABELS: Final[Mapping[DocumentFormat, str]] = {DOCX: "Word", PPTX: "PowerPoint", PDF: "PDF"}
"""How the guide names a format."""

MERGE_ORDER: Final = (DOCX, PDF, PPTX)
"""The order the guides are merged in: Word and the PDF share one guide („Dokumente“), so they
are merged first and PowerPoint's sections and lines fit in around theirs."""

KINDS: Final[Mapping[DocumentFormat, str]] = {
    DOCX: "ein Word-Dokument auf der PTA-Word-Vorlage, zum Weiterbearbeiten",
    PPTX: "eine PowerPoint-Präsentation auf der PTA-Folienvorlage",
    PDF: "ein PDF (PDF/A) im Design der PTA-Word-Vorlage, zum Lesen und Verschicken",
}
"""One line per format in the section „Formate“."""

FORMATS_HEADING: Final = "## Formate"
HOST_HEADING: Final = "## In dieser Anwendung"

_INTRO: Final = "\0intro"
"""The key of each guide's first section, whose heading names the format."""

_TABLE_SEPARATOR: Final = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")
_LIST_ITEM: Final = re.compile(r"^(- |\d+\. )")
_CELL_BORDER: Final = re.compile(r"(?<!\\)\|")


class _Kind(StrEnum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    FENCE = "fence"
    ITEM = "item"
    HEAD = "head"
    SEPARATOR = "separator"
    ROW = "row"


_TABLE: Final = (_Kind.HEAD, _Kind.SEPARATOR, _Kind.ROW)


def write(guides: Mapping[DocumentFormat, str], host_notes: str | None = None) -> str:
    """The guide for the offered formats (``guides``: each format's own guide, in the order to
    name them) with ``host_notes`` at the end."""
    if not guides:
        raise ValueError("A combined guide needs at least one guide.")
    guide = next(iter(guides.values())) if len(guides) == 1 else combine(guides)
    return with_host_notes(guide, host_notes)


def with_host_notes(guide: str, host_notes: str | None) -> str:
    """``guide`` with ``host_notes`` (Markdown) at the end; under ``HOST_HEADING`` unless they
    start with a heading."""
    notes = (host_notes or "").strip()
    if not notes:
        return guide
    heading = "" if notes.startswith("#") else f"{HOST_HEADING}\n\n"
    return f"{guide.rstrip()}\n\n{heading}{notes}\n"


def combine(guides: Mapping[DocumentFormat, str]) -> str:
    """The guides merged as the module describes."""
    offered = frozenset(guides)
    ordered = {f: guides[f] for f in MERGE_ORDER if f in guides}
    own_titles = {f: set(sections(g)) for f, g in ordered.items()}
    every_title = set().union(*own_titles.values())
    by_format = {f: sections(_promote(g, every_title - own_titles[f])) for f, g in ordered.items()}
    titles: list[str] = []
    for found in by_format.values():
        titles = _merge_titles(titles, list(found))
    parts: list[str] = []
    for title in titles:
        merged: list[_Unit] = []
        for f, found in by_format.items():
            if title in found:
                merged = _merge(merged, units(found[title], f))
        having = frozenset(f for f, found in by_format.items() if title in found)
        body = _render(merged, having)
        if title == _INTRO:
            parts.insert(0, f"{_formats_section(guides)}\n\n{body}")
            continue
        heading = f"## {title}" if having == offered else f"## {title} ({_only(having)})"
        parts.append(f"{heading}\n\n{body}" if body else heading)
    return "\n\n".join(parts) + "\n"


def _promote(guide: str, titles: Collection[str]) -> str:
    """``guide`` with each ``### <title>`` (outside code blocks) of ``titles`` made a ``##``:
    what one guide has as a section of its own (PowerPoint's „Hinweise“), another may have
    under a section (the documents' „Wenn etwas falsch ist“)."""
    lines: list[str] = []
    fence: str | None = None
    for line in guide.split("\n"):
        if fence is None and line.startswith("```"):
            fence = line[: len(line) - len(line.lstrip("`"))]
        elif fence is not None and line.strip() == fence:
            fence = None
        elif fence is None and line.startswith("### ") and line[4:].strip() in titles:
            line = line[1:]
        lines.append(line)
    return "\n".join(lines)


def sections(guide: str) -> dict[str, str]:
    """The sections of ``guide`` by their ``##`` heading (outside code blocks), without the
    heading line; the first one under ``_INTRO``. Text before it is dropped (the guides start
    at ``##``); a heading that comes twice keeps its first section."""
    found: dict[str, str] = {}
    title: str | None = None
    lines: list[str] = []
    fence: str | None = None
    for line in guide.split("\n"):
        if fence is None and line.startswith("```"):
            fence = line[: len(line) - len(line.lstrip("`"))]
        elif fence is not None and line.strip() == fence:
            fence = None
        elif fence is None and line.startswith("## "):
            if title is not None:
                found.setdefault(title, "\n".join(lines).strip("\n"))
            title = line[3:].strip() if found or title is not None else _INTRO
            lines = []
            continue
        lines.append(line)
    if title is not None:
        found.setdefault(title, "\n".join(lines).strip("\n"))
    return found


@dataclass
class _Unit:
    """A paragraph, heading, code block, list item or table row; ``key`` is what the merge
    compares — the text, but only the shape for table heads and separators."""

    kind: _Kind
    key: str
    texts: dict[DocumentFormat, str] = field(default_factory=dict[DocumentFormat, str])

    @property
    def formats(self) -> frozenset[DocumentFormat]:
        return frozenset(self.texts)

    @property
    def text(self) -> str:
        return next(iter(self.texts.values()))


def units(body: str, format: DocumentFormat) -> list[_Unit]:
    """``body`` cut into the units the merge compares."""
    found: list[_Unit] = []
    current: list[str] = []
    kind: _Kind | None = None
    fence: str | None = None

    def close() -> None:
        nonlocal kind
        if kind is not None:
            text = "\n".join(current)
            found.append(_unit(kind, text, format))
        current.clear()
        kind = None

    for line in body.split("\n"):
        if fence is not None:
            current.append(line)
            if line.strip() == fence:
                fence = None
                close()
            continue
        if not line.strip():
            close()
        elif line.startswith("```"):
            close()
            fence = line[: len(line) - len(line.lstrip("`"))]
            kind = _Kind.FENCE
            current.append(line)
        elif line.startswith("|"):
            in_table = kind in (_Kind.HEAD, _Kind.SEPARATOR, _Kind.ROW)
            close()
            if _TABLE_SEPARATOR.match(line.strip()):
                kind = _Kind.SEPARATOR
            else:
                kind = _Kind.ROW if in_table else _Kind.HEAD
            current.append(line)
        elif line.startswith("#"):
            close()
            kind = _Kind.HEADING
            current.append(line)
            close()
        elif _LIST_ITEM.match(line):
            close()
            kind = _Kind.ITEM
            current.append(line)
        elif kind in (_Kind.ITEM, _Kind.PARAGRAPH):
            current.append(line)
        else:
            close()
            kind = _Kind.PARAGRAPH
            current.append(line)
    close()
    return found


def _unit(kind: _Kind, text: str, format: DocumentFormat) -> _Unit:
    cells = _cells(text) if kind in _TABLE else []
    if kind is _Kind.HEAD:
        key = f"head:{cells[0]}:{len(cells)}"
    elif kind is _Kind.SEPARATOR:
        key = f"separator:{len(cells)}"
    elif kind is _Kind.ROW:
        key = f"row:{cells[0]}:{len(cells)}"
    else:
        key = f"{kind}:{text}"
    return _Unit(kind, key, {format: text})


def _cells(row: str) -> list[str]:
    """The cells of a table row; ``\\|`` is a ``|`` inside a cell."""
    inner = row.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in _CELL_BORDER.split(inner)]


def _merge_titles(merged: list[str], titles: list[str]) -> list[str]:
    result: list[str] = []
    matcher = SequenceMatcher(None, merged, titles, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        result.extend(merged[i1:i2])
        if tag != "equal":
            result.extend(t for t in titles[j1:j2] if t not in merged)
    return result


def _merge(merged: list[_Unit], new: list[_Unit]) -> list[_Unit]:
    """``new`` (one format's units) merged into ``merged``: equal units take its text, the
    others keep their place."""
    result: list[_Unit] = []
    matcher = SequenceMatcher(None, [u.key for u in merged], [u.key for u in new], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for old, other in zip(merged[i1:i2], new[j1:j2], strict=True):
                old.texts.update(other.texts)
                result.append(old)
        else:
            # Rows that go on with a table just written stay with it, before what replaces them.
            rows = 0
            if result and result[-1].kind in _TABLE:
                while j1 + rows < j2 and new[j1 + rows].kind is _Kind.ROW:
                    rows += 1
            result.extend(new[j1 : j1 + rows])
            result.extend(merged[i1:i2])
            result.extend(new[j1 + rows : j2])
    return result


def _runs(merged: Sequence[_Unit]) -> list[list[_Unit]]:
    """The units grouped into blocks: a table (from its head), a list, or a single unit."""
    runs: list[list[_Unit]] = []
    for unit in merged:
        last = runs[-1][-1] if runs else None
        joins = last is not None and (
            (unit.kind is _Kind.ITEM and last.kind is _Kind.ITEM)
            or (unit.kind in (_Kind.SEPARATOR, _Kind.ROW) and last.kind in _TABLE)
        )
        if joins:
            runs[-1].append(unit)
        else:
            runs.append([unit])
    return runs


def _render(merged: Sequence[_Unit], context: frozenset[DocumentFormat]) -> str:
    blocks: list[str] = []
    for run in _runs(merged):
        having = frozenset().union(*(u.formats for u in run))
        if having != context and run[0].kind is _Kind.HEADING:
            blocks.append(f"{run[0].text} ({_only(having)})")
            continue
        if having != context and run[0].kind is _Kind.PARAGRAPH:
            blocks.append(f"*{_only(having, capital=True)}:* {run[0].text}")
            continue
        # A table or list that only some formats have is marked once, in a line before it, and
        # its rows or items against those.
        whole = having != context
        lines = [_line(u, having if whole else context) for u in run]
        text = "\n".join(lines)
        if whole:
            text = f"*{_only(having, capital=True)}:*\n\n{text}"
        blocks.append(text)
    return "\n\n".join(blocks)


def _line(unit: _Unit, context: frozenset[DocumentFormat]) -> str:
    if unit.kind is _Kind.HEAD:
        return _head(unit)
    if unit.kind is _Kind.SEPARATOR:
        return unit.text
    if unit.kind is _Kind.ROW:
        return _row(unit, context)
    if unit.formats == context:
        return unit.text
    if unit.kind is _Kind.ITEM:
        marker = _LIST_ITEM.match(unit.text)
        cut = marker.end() if marker else 0
        return f"{unit.text[:cut]}*{_only(unit.formats, capital=True)}:* {unit.text[cut:]}"
    return unit.text


def _row(unit: _Unit, context: frozenset[DocumentFormat]) -> str:
    """One table row from the formats' rows with the same first cell: a cell that differs names
    each format's value; a row that not every format of ``context`` has says which have it."""
    by_format = {f: _cells(t) for f, t in unit.texts.items()}
    cells: list[str] = []
    for column in range(len(next(iter(by_format.values())))):
        values: dict[str, set[DocumentFormat]] = {}
        for f, row in by_format.items():
            values.setdefault(row[column], set()).add(f)
        if len(values) == 1:
            cells.append(next(iter(values)))
        else:
            cells.append(" ".join(f"*{_names(fs)}:* {value}" for value, fs in values.items()))
    if unit.formats != context:
        cells[-1] = f"{cells[-1]} *({_only(unit.formats)})*"
    return "| " + " | ".join(cells) + " |"


def _head(unit: _Unit) -> str:
    """One table head from the heads of the formats: differing cells joined with „ / “."""
    heads = [_cells(t) for t in unit.texts.values()]
    cells = [" / ".join(dict.fromkeys(column)) for column in zip(*heads, strict=True)]
    return "| " + " | ".join(cells) + " |"


def _names(formats: Iterable[DocumentFormat]) -> str:
    """„Word und PDF“, in the order of ``LABELS``."""
    wanted = set(formats)
    named = [LABELS[f] for f in LABELS if f in wanted]
    return named[0] if len(named) == 1 else f"{', '.join(named[:-1])} und {named[-1]}"


def _only(formats: Iterable[DocumentFormat], *, capital: bool = False) -> str:
    """„nur Word und PDF“ (``capital``: „Nur …“)."""
    return f"{'Nur' if capital else 'nur'} {_names(formats)}"


def _formats_section(guides: Mapping[DocumentFormat, str]) -> str:
    lines = [
        FORMATS_HEADING,
        "",
        "Der Parameter `format` entscheidet, was aus dem Markdown wird:",
        "",
        *(f"- `{f.value}`: {KINDS[f]}." for f in guides),
        "",
    ]
    documents = [LABELS[f] for f in guides if f in (DOCX, PDF)]
    reading: list[str] = []
    if documents:
        who = " und ".join(documents)
        reading.append(
            f"{who} lesen das Markdown als Bericht: `#` ist ein Kapitel, der Titel kommt aus "
            "`titel:`."
            if len(documents) > 1
            else f"{who} liest das Markdown als Bericht: `#` ist ein Kapitel, der Titel kommt "
            "aus `titel:`."
        )
    if PPTX in guides:
        reading.append(
            "PowerPoint liest es als Präsentation: das erste `#` ist die Titelfolie, jedes "
            "weitere eine Trennfolie, `##` eine Folie."
        )
    reading.append(
        "Was nur für einen Teil der Formate gilt, ist mit „Nur …“ markiert; alles andere gilt "
        "für alle."
    )
    lines.append(" ".join(reading))
    return "\n".join(lines)
