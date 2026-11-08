"""Look at presentations without PowerPoint: one PNG per slide and a contact sheet (E10-S02).

usage: ./run.sh preview <file-or-folder> [...] [--scale <n>] [--slides <list>] [--html]
                         [--audience kunde|intern|trainer]
       ./run.sh preview --check-browser

Every presentation (``…-praesentation.md`` / ``…-folien.md``; a folder means every ``*.md`` in
it) becomes its HTML deck (E10-S01, in memory), and the deck is drawn in a headless Chromium to
``<folder>/vorschau/<name>/folie-01.png`` … and ``uebersicht.png`` (all slides side by side).
The folder ``vorschau/<name>/`` is emptied first. A slide with builds shows its final state.
Word documents (``…-bericht.md`` / ``…-dokument.md``) have no preview.

  --scale <n>      n times the pixels (2: 3200 × 1800, sharper; default 1: 1600 × 900)
  --slides <list>  only these slides, e.g. 3,7-9 (numbers of the whole deck)
  --html           also write the HTML deck into the preview folder
  --audience <a>   the version (E16-S01) instead of ``fassung:`` (else ``kunde``); the internal
                   and the trainer's go to ``vorschau/<name>-intern/`` and ``…-trainer/``
  --check-browser  exit code 0 if Playwright and its Chromium start, 1 otherwise (for setup)

Needs the extra ``preview`` (Playwright) and its Chromium; without them only this tool stops,
with what to install. After each file come the notes of the generator (``  - line 12: …``).
"""

from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path
from typing import Final

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import audience as audiences
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from pta_documents.preview import (
    PreviewUnavailableError,
    chromium_available,
    contact_sheet,
    render_deck,
)

IMAGE_SUFFIXES: Final = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".svg"}
DECK_SUFFIXES: Final = ("-praesentation", "-folien")
WORD_SUFFIXES: Final = ("-bericht", "-dokument")
NOT_DOCUMENTS: Final = ("readme.md", "quellen.md")
PREVIEW_FOLDER: Final = "vorschau"
SHEET_NAME: Final = "uebersicht.png"
AUDIENCE_VALUES: Final = tuple(a.value for a in Audience)


class UsageError(ValueError):
    """A wrong argument; the message says what is expected."""


def resources(folder: Path) -> list[DocumentResource]:
    """The image files below ``folder``, as ``tools/generate`` passes them."""
    return [
        DocumentResource(
            path.relative_to(folder).as_posix(), content_type_of(path.name), path.read_bytes()
        )
        for path in sorted(folder.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in IMAGE_SUFFIXES
        and PREVIEW_FOLDER not in path.relative_to(folder).parts
    ]


def parse_slides(text: str) -> set[int]:
    """``3,7-9`` → {3, 7, 8, 9}."""
    numbers: set[int] = set()
    for part in text.split(","):
        part = part.strip()
        try:
            if "-" in part:
                first, last = (int(n) for n in part.split("-", 1))
                if first > last:
                    raise UsageError(f"--slides: {part} runs backwards")
                numbers.update(range(first, last + 1))
            else:
                numbers.add(int(part))
        except ValueError as error:
            if isinstance(error, UsageError):
                raise
            raise UsageError(
                f"--slides: '{part}' is not a slide number or range like 7-9"
            ) from error
    if not numbers or min(numbers) < 1:
        raise UsageError("--slides: slide numbers start at 1")
    return numbers


def picture_name(number: int) -> str:
    return f"folie-{number:02d}.png"


def preview(
    source: Path,
    scale: int,
    slides: set[int] | None,
    write_html: bool,
    audience: Audience | None = None,
) -> bool:
    """Preview one file in the version ``audience`` (None: ``fassung:``); False on an error.
    Raises ``PreviewUnavailableError``."""
    stem = source.stem
    if stem.endswith(WORD_SUFFIXES):
        print(f"skipped {source}: there is no preview for Word documents")
        return True
    if not stem.endswith(DECK_SUFFIXES):
        print(f"skipped {source}: name it …-praesentation.md or …-folien.md")
        return True
    document = MarkdownDocument(source.read_text(encoding="utf-8"), resources(source.parent))
    deck = io.BytesIO()
    try:
        chosen = audiences.of(document.text, DocumentFormat.HTML, audience)
        result = HtmlDeckGenerator().generate(document, deck, HtmlDeckOptions(audience=chosen))
    except DocumentConversionError as error:
        print(f"ERROR {source}: {error.reason}", file=sys.stderr)
        return False
    pictures = render_deck(deck.getvalue(), scale=scale, slides=slides)
    stem += chosen.suffix
    folder = source.parent / PREVIEW_FOLDER / stem
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    if write_html:
        (folder / f"{stem}.html").write_bytes(deck.getvalue())
    if not pictures:
        print(f"ERROR {source}: the deck has none of the slides asked for", file=sys.stderr)
        return False
    for picture in pictures:
        target = folder / picture_name(picture.number)
        target.write_bytes(picture.png)
        print(f"wrote {target}")
    sheet = folder / SHEET_NAME
    sheet.write_bytes(contact_sheet(pictures))
    print(f"wrote {sheet}")
    for note in result.notes:
        print(f"  - {note}")
    return True


def main(argv: list[str]) -> int:
    scale = 1
    slides: set[int] | None = None
    write_html = False
    audience: Audience | None = None
    paths: list[Path] = []
    args = iter(argv)
    try:
        for arg in args:
            if arg == "--check-browser":
                return 0 if chromium_available() else 1
            if arg == "--scale":
                value = next(args, "")
                if not value.isdigit() or int(value) < 1:
                    raise UsageError(f"--scale: '{value}' is not a whole number from 1")
                scale = int(value)
            elif arg == "--slides":
                slides = parse_slides(next(args, ""))
            elif arg == "--html":
                write_html = True
            elif arg == "--audience":
                value = next(args, "").strip().lower()
                if value not in AUDIENCE_VALUES:
                    raise UsageError(
                        f"--audience takes {', '.join(AUDIENCE_VALUES)}, not '{value}'"
                    )
                audience = Audience(value)
            elif arg.startswith("--"):
                raise UsageError(f"unknown switch {arg}")
            else:
                paths.append(Path(arg))
    except UsageError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 2
    if not paths:
        print(__doc__)
        return 1
    ok = True
    try:
        for path in paths:
            files = sorted(path.glob("*.md")) if path.is_dir() else [path]
            for source in files:
                if source.name.lower() in NOT_DOCUMENTS:
                    continue
                ok &= preview(source, scale, slides, write_html, audience)
    except PreviewUnavailableError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
