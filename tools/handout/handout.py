"""Write the handout of a presentation as a Word document (E16-S03).

usage: ./run.sh handout <praesentation.md|folder> [...] [--layout 2|3|6]
                        [--audience kunde|intern|trainer] [--out <folder>] [--markdown]
                        [--strict]

Every presentation (``…-praesentation.md`` / ``…-folien.md``; a folder means every ``*.md`` in
it) becomes ``<name>-handout.docx`` next to it (or in ``--out``) on the PTA Word template: the
cover from the front matter, the title slide small, the schedule (E16-S02) or a table of
contents, a chapter per divider slide and per slide its picture with „Folie n: Titel"; beside it
(``--layout 2``, landscape) or below it (``3``, the default, and ``6``, portrait) lines to write
on — or, in the trainer's version (``--audience trainer``, ``<name>-handout-trainer.docx``), the
speaker notes with the planned times and the backup slides. ``--audience`` wins over
``fassung:`` of the deck; without either the handout is the customer's (``kunde``).

The pictures come from the preview (extra ``preview``, E10-S02); without it the handout shows
the text of each slide instead, and the tool says so. ``--markdown`` also writes the Markdown of
the handout (``<name>-handout.md``) and its pictures (``<name>-handout/``) for editing by hand.
After each file come the notes (``  - line 12: …``: lines of the presentation); the exit code is
1 for errors, with ``--strict`` also for notes.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Any, Final

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import audience as audiences
from pta_documents.generation.common.audience import Audience
from pta_documents.handout import (
    HandoutLayout,
    HandoutOptions,
    build_handout,
    slide_pictures,
    write_handout,
)
from pta_documents.handout.handout import PICTURE_FOLDER
from pta_documents.markdown import MarkdownDocument
from pta_documents.preview import PreviewUnavailableError

SUFFIX: Final = "-handout"
AUDIENCE_VALUES: Final = tuple(a.value for a in Audience)
LAYOUT_VALUES: Final = tuple(str(int(layout)) for layout in HandoutLayout)
NOT_DOCUMENTS: Final = ("readme.md", "quellen.md")


class UsageError(ValueError):
    """A wrong argument; the message says what is expected."""


def _generate_tool() -> Any:
    """``tools/generate/generate.py``: file names and resources work as there."""
    path = Path(__file__).resolve().parents[1] / "generate" / "generate.py"
    spec = importlib.util.spec_from_file_location("generate_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATE: Any = _generate_tool()


def write(
    source: Path,
    out: Path | None,
    layout: HandoutLayout,
    audience: Audience | None,
    markdown: bool = False,
    strict: bool = False,
) -> bool:
    """``<name>-handout[-intern|-trainer].docx`` of one presentation; False on an error (or,
    with ``strict``, on notes)."""
    if GENERATE.target_format(source, None) != "pptx":
        print(f"skipped {source}: only presentations (…-praesentation.md) have a handout")
        return True
    document = MarkdownDocument(
        source.read_text(encoding="utf-8"), GENERATE.resources(source.parent)
    )
    try:
        chosen = audiences.of(document.text, DocumentFormat.PPTX, audience)
        try:
            pictures = slide_pictures(document, chosen)
        except PreviewUnavailableError:
            pictures = None
            print(f"no slide pictures for {source}: the handout shows the slides' text")
        handout = build_handout(document, pictures, HandoutOptions(layout, chosen))
    except DocumentConversionError as error:
        print(f"ERROR {source}: {error.reason}", file=sys.stderr)
        return False
    folder = out or source.parent
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{source.stem}{SUFFIX}{chosen.suffix}"
    target = folder / f"{stem}.docx"
    with target.open("wb") as stream:
        result = write_handout(handout, stream)
    print(f"wrote {target}")
    if markdown:
        write_markdown(handout.document, folder, stem)
    for note in result.notes:
        print(f"  - {note}")
    return not (strict and result.notes)


def write_markdown(document: MarkdownDocument, folder: Path, stem: str) -> None:
    """The handout's Markdown as ``<stem>.md``, its pictures in ``<stem>/`` (emptied first)."""
    pictures = folder / stem
    if pictures.exists():
        shutil.rmtree(pictures)
    prefix = f"{PICTURE_FOLDER}/"
    text = document.text.replace(f"]({prefix}", f"]({stem}/")
    for resource in document.resources:
        target = pictures / resource.path.removeprefix(prefix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(resource.content)
    markdown = folder / f"{stem}.md"
    markdown.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {markdown}")


def main(argv: list[str]) -> int:
    out: Path | None = None
    layout = HandoutLayout.THREE
    audience: Audience | None = None
    markdown = strict = False
    paths: list[Path] = []
    args = iter(argv)
    try:
        for arg in args:
            if arg == "--out":
                out = Path(next(args, "."))
            elif arg == "--markdown":
                markdown = True
            elif arg == "--strict":
                strict = True
            elif arg == "--layout":
                value = next(args, "").strip()
                if value not in LAYOUT_VALUES:
                    raise UsageError(f"--layout takes {', '.join(LAYOUT_VALUES)}, not '{value}'")
                layout = HandoutLayout(int(value))
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
    for path in paths:
        files = sorted(path.glob("*.md")) if path.is_dir() else [path]
        for source in files:
            if source.name.lower() in NOT_DOCUMENTS:
                continue
            ok &= write(source, out, layout, audience, markdown, strict)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
