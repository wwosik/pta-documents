"""What a generator hands back besides the document: notes for whoever wrote the Markdown.

A generator works around what it cannot show as written — it splits a slide that is too full,
leaves out raw HTML, shows a diagram it cannot draw as code. The document is still usable, so
none of this is an error (errors stay ``DocumentConversionError``); but the writer, often an AI
agent, can only fix what it is told about. Each such workaround becomes a ``GenerationNote``;
``generate()`` returns them in a ``GenerationResult``. Markdown that produces no notes is the
goal.

Port of ``GenerationResult.cs`` in vt-tools-libs (``DocumentGeneration``).

Usage in a generator::

    notes = Notes()
    notes.add(NoteCodes.RAW_HTML, 12, "Raw HTML is left out of the deck. ...")
    return GenerationResult(notes.to_tuple(), slides=len(presentation.slides))

Usage by a caller::

    result = PptxGenerator().generate(document, output)
    if result.notes:
        print(result)  # "- line 12: Raw HTML is left out ..." per note
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final


class NoteCodes:
    """The ``code`` of a ``GenerationNote``: stable kebab-case names, safe to match on.

    New codes are added as features arrive; existing ones keep their name and meaning.
    """

    SLIDE_SPLIT: Final = "slide-split"
    """A slide had too much content and continues on further slides titled "(Forts.)" (PPTX)."""

    SLIDE_OVERFULL: Final = "slide-overfull"
    """Content does not fit on a slide even at the smallest text size (12 pt) and runs past
    its bottom (PPTX)."""

    IMAGE_CROPPED: Final = "image-cropped"
    """A picture placeholder cuts off more than a quarter of an image (PPTX)."""

    IMAGE_ENLARGED: Final = "image-enlarged"
    """An image shown at more than twice its natural size (pixels at 96 dpi), which can look
    blurred (PPTX, DOCX, PDF)."""

    RAW_HTML: Final = "raw-html"
    """Raw HTML, which is left out of the document (PPTX, DOCX, PDF). HTML comments are left out
    without a note."""

    CODE_NOT_DRAWN: Final = "code-not-drawn"
    """A code block in a diagram or chart language (``mermaid``, ``chart`` …) that no renderer
    drew, so it shows as code (PPTX, DOCX, PDF). Word also leaves icons (``:icon-check:``,
    E15-S03) in footnotes out with it."""

    CHARACTER_MISSING: Final = "character-missing"
    """A character the document's fonts lack; it shows as ``?`` or what
    ``PdfOptions.replace_unsupported`` makes of it (PDF)."""

    NOTES_DROPPED: Final = "notes-dropped"
    """Speaker notes (``::: notes``) left out of a format that has none (DOCX, PDF)."""

    CODE_LANGUAGE_UNKNOWN: Final = "code-language-unknown"
    """A code block whose language (```` ```sprache ````) the highlighter does not know: it shows
    in one colour (PPTX, DOCX, PDF)."""

    IMAGE_SCALE_IN_TITLE: Final = "image-scale-in-title"
    """``scale=N`` in the title of an image (E11-S04); it still works until 2027-11 but belongs in
    the braces after the image: ``![…](a.png){scale=0.5}`` (E15-S04) (PPTX, DOCX)."""

    SCENE_DROPPED: Final = "scene-dropped"
    """A scene (``::: scene``, E09-S04) left out of Word, which has no slides to move shapes
    on; the PDF shows it as a still picture (DOCX)."""

    AUDIENCE_OMITTED: Final = "audience-omitted"
    """Internal blocks or solutions left out of the version for an audience (``fassung:``,
    ``--audience``, E16-S01); one note with the numbers (PPTX, DOCX, PDF)."""

    ALL: Final = (
        SLIDE_SPLIT,
        SLIDE_OVERFULL,
        IMAGE_CROPPED,
        IMAGE_ENLARGED,
        RAW_HTML,
        CODE_NOT_DRAWN,
        CHARACTER_MISSING,
        NOTES_DROPPED,
        CODE_LANGUAGE_UNKNOWN,
        IMAGE_SCALE_IN_TITLE,
        SCENE_DROPPED,
        AUDIENCE_OMITTED,
    )
    """Every code, in the order the guides list them."""


@dataclass(frozen=True)
class GenerationNote:
    """Something a generator worked around, which the writer of the Markdown may want to fix.

    ``code`` is one of ``NoteCodes``; ``line`` the one-based line in the Markdown (front matter
    included) it is about, or None when it has none; ``message`` one English sentence on what
    happened and what to write instead.
    """

    code: str
    line: int | None
    message: str

    def __str__(self) -> str:
        """``line 12: message``, or the message alone."""
        return f"line {self.line}: {self.message}" if self.line is not None else self.message


@dataclass(frozen=True)
class GenerationResult:
    """What ``generate()`` returns: the notes, and how many slides or pages it wrote.

    ``slides`` is the number of slides of a deck (None for other formats); ``pages`` the
    number of pages of a PDF (None for other formats — Word counts its pages only when it
    lays the document out).
    """

    notes: tuple[GenerationNote, ...] = ()
    """By line, each once; empty when nothing needed working around."""
    slides: int | None = None
    pages: int | None = None

    def __str__(self) -> str:
        """The notes as a Markdown list (``- line 12: message``), ready to hand back to the
        writer; ``No notes.`` without any. Ends with a line break."""
        if not self.notes:
            return "No notes.\n"
        return "".join(f"- {note}\n" for note in self.notes)

    def codes(self) -> list[str]:
        """The codes of the notes, in order (convenient in tests and checks)."""
        return [note.code for note in self.notes]


class Notes:
    """Collects the notes of one generation: each once, sorted by line in the end.

    One collector per ``generate()`` call; parser and writer add to the same one.
    """

    def __init__(self) -> None:
        self._notes: list[GenerationNote] = []

    def add(self, code: str, line: int | None, message: str) -> None:
        """Add a note; the same code, line and message again is dropped."""
        note = GenerationNote(code, line, message)
        if note not in self._notes:
            self._notes.append(note)

    def to_tuple(self) -> tuple[GenerationNote, ...]:
        """The notes sorted by line (notes without a line first), otherwise in the order added."""
        return tuple(sorted(self._notes, key=lambda n: n.line or 0))

    def __len__(self) -> int:
        return len(self._notes)

    def characters(
        self,
        markdown: str,
        line_offset: int,
        in_text: Callable[[str], bool],
        in_code: Callable[[str], bool],
        effect: str,
        alternatives: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        """Notes on the characters of ``markdown`` the fonts lack, each character once at its
        first line (code ``character-missing``).

        ``markdown`` is the text without front matter, ``line_offset`` the number of lines cut
        off before it. Text is checked with ``in_text``, fenced code and code spans with
        ``in_code`` (each takes one character). ``effect`` says what happens to such a
        character and follows "is not in the fonts and", e.g. "shows in a substitute font".
        ``alternatives`` maps a character to replacements in order of preference; the first
        one the text fonts have is suggested.
        """
        seen: set[str] = set()
        fence: str | None = None
        for number, raw in enumerate(markdown.split("\n")):
            line = raw.rstrip("\r")
            stripped = line.lstrip()
            if fence is None and stripped.startswith(("```", "~~~")):
                marker = stripped[0]
                fence = marker * (len(stripped) - len(stripped.lstrip(marker)))
                continue
            if fence is not None and stripped.startswith(fence) and not stripped.strip(fence[0]):
                fence = None
                continue
            in_span = False
            for char in line:
                if char == "`":
                    in_span = not in_span
                code = ord(char)
                if (
                    code < 0x80
                    or char.isspace()
                    or not char.isprintable()
                    or code in (0xFE0F, 0x200D)
                    or char in seen
                ):
                    continue
                if (in_code if fence is not None or in_span else in_text)(char):
                    continue
                seen.add(char)
                choices = list((alternatives or {}).get(char, ()))
                usable = [c for c in choices if all(in_text(x) for x in c)]
                replacement = (usable or choices[-1:] or [None])[0]
                advice = (
                    f"Write `{replacement}` instead."
                    if replacement is not None
                    else "Leave it out or write it in words."
                )
                self.add(
                    NoteCodes.CHARACTER_MISSING,
                    number + 1 + line_offset,
                    f"'{char}' (U+{code:04X}) is not in the fonts and {effect}. {advice}",
                )
