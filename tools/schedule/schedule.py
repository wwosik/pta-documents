"""Write the trainer's schedule of a presentation as a Word document (E16-S02).

usage: ./run.sh schedule <praesentation.md> [...] [--out <folder>] [--markdown] [--strict]
                         [--audience kunde|intern|trainer]

Every presentation (``…-praesentation.md`` / ``…-folien.md``; a folder means every ``*.md`` in
it, and decks there without a schedule are skipped) with a schedule — ``{dauer=5}`` on slides or
chapters, ``## Pause {.break dauer=15}``, ``beginn:`` or ``laenge:`` in the front matter —
becomes ``<name>-zeitplan.docx`` next to it (or in ``--out``): the PTA Word template
``hoch-ohne-deckblatt`` with a table From | To | Duration | Chapter/slide | Notes (empty, for the
trainer), the breaks marked, the total last. Without ``beginn:`` the times count from ``+0:00``.

The schedule is that of the trainer version unless ``--audience`` names another (the internal
and the trainer version are marked ``intern``). ``--markdown`` also prints the Markdown of the
document, for an AI to read. After each file come the notes of the deck (``  - line 12: …``,
e.g. slides without ``dauer``); the exit code is 1 for errors, with ``--strict`` also for notes.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path
from typing import Any, Final

from pta_documents.errors import DocumentConversionError
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.training_schedule import deck_schedule, schedule_document
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument

SUFFIX: Final = "-zeitplan"
AUDIENCE_VALUES: Final = tuple(a.value for a in Audience)


def _generate_tool() -> Any:
    """``tools/generate/generate.py``: file names and resources work as there."""
    path = Path(__file__).resolve().parents[1] / "generate" / "generate.py"
    spec = importlib.util.spec_from_file_location("generate_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATE: Any = _generate_tool()


def write_schedule(
    source: Path,
    out: Path | None,
    audience: Audience,
    markdown: bool = False,
    strict: bool = False,
    named: bool = True,
) -> bool:
    """``<name>-zeitplan.docx`` of one presentation; False on an error (or, with ``strict``, on
    notes). A deck without a schedule is an error when ``named``, else (in a folder) skipped."""
    if GENERATE.target_format(source, None) != "pptx":
        print(f"skipped {source}: only presentations (…-praesentation.md) have a schedule")
        return True
    document = MarkdownDocument(
        source.read_text(encoding="utf-8"), GENERATE.resources(source.parent)
    )
    try:
        # The deck itself first: its mistakes and notes are those of generating it.
        result = PptxGenerator().generate(document, io.BytesIO(), PptxOptions(audience=audience))
        schedule = deck_schedule(document, audience)
    except DocumentConversionError as error:
        print(f"ERROR {source}: {error.reason}", file=sys.stderr)
        return False
    if schedule is None and not named:
        print(f"skipped {source}: no schedule")
        return True
    if schedule is None:
        print(
            f"ERROR {source}: no schedule; give the slides their minutes ('## Folie {{dauer=5}}') "
            "or the front matter 'beginn:' / 'laenge:'",
            file=sys.stderr,
        )
        return False
    text = schedule_document(schedule, audience)
    folder = out or source.parent
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{source.stem}{SUFFIX}.docx"
    with target.open("wb") as stream:
        DocxGenerator().generate(MarkdownDocument(text), stream)
    print(f"wrote {target}")
    for note in result.notes:
        print(f"  - {note}")
    if markdown:
        print(text)
    return not (strict and result.notes)


def main(argv: list[str]) -> int:
    out: Path | None = None
    audience = Audience.TRAINER
    markdown = strict = False
    paths: list[Path] = []
    args = iter(argv)
    for arg in args:
        if arg == "--out":
            out = Path(next(args, "."))
        elif arg == "--markdown":
            markdown = True
        elif arg == "--strict":
            strict = True
        elif arg == "--audience":
            value = next(args, "").strip().lower()
            if value not in AUDIENCE_VALUES:
                print(
                    f"--audience takes {', '.join(AUDIENCE_VALUES)}, not '{value}'", file=sys.stderr
                )
                return 1
            audience = Audience(value)
        else:
            paths.append(Path(arg))
    if not paths:
        print(__doc__)
        return 1
    ok = True
    for path in paths:
        files = sorted(path.glob("*.md")) if path.is_dir() else [path]
        for source in files:
            if source.name.lower() in ("readme.md", "quellen.md"):
                continue
            ok &= write_schedule(source, out, audience, markdown, strict, not path.is_dir())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
