"""Check Markdown files without writing documents: errors, notes, style notes, statistics.

usage: ./run.sh check <file-or-folder> [...] [--docx | --pptx | --pdf] [--strict]
                      [--skip <code>,...] [--sources] [--json]
                      [--audience kunde|intern|trainer|alle]

Files and formats as with ``generate``: a folder means every ``*.md`` in it, ``…-bericht.md`` /
``…-dokument.md`` are Word, ``…-praesentation.md`` / ``…-folien.md`` PowerPoint, or
``--docx`` / ``--pptx`` / ``--pdf``. Nothing is written. Per file: ``OK <file>`` or
``ERROR <file>: …``, then the notes of the generator and the style notes (``  - line 12: …``),
then two lines of statistics (slides, words, talking time; for Word words, tables, figures and
rough pages; for PDF the pages of the trial PDF).

The style rule ``style-image-source`` runs when the file's folder has a ``QUELLEN.md`` or with
``--sources``. ``--skip style-words,style-title`` leaves rules out (also front matter
``pruefung: aus`` or ``pruefung: style-words``). ``--json`` prints one JSON object per run for
tools. The exit code is 1 for errors, with ``--strict`` also for notes.

``--audience`` checks that version (E16-S01) instead of the one of ``fassung:`` (default
``kunde``); ``alle`` checks every version that differs, each with its statistics
(``OK <file> (fassung: intern)``).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.check import CheckOptions, CheckResult, DeckStats, check
from pta_documents.markdown import MarkdownDocument


def _generate_tool() -> Any:
    """``tools/generate/generate.py``: file names, formats and resources work as there."""
    path = Path(__file__).resolve().parents[1] / "generate" / "generate.py"
    spec = importlib.util.spec_from_file_location("generate_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATE: Any = _generate_tool()

SOURCES_FILE = "QUELLEN.md"


def check_file(source: Path, forced: str | None, options: CheckOptions) -> CheckResult | None:
    """The result for one file; None when its format is unknown."""
    format: str | None = GENERATE.target_format(source, forced)
    if format is None:
        return None
    document = MarkdownDocument(
        source.read_text(encoding="utf-8"), GENERATE.resources(source.parent)
    )
    sources = options.sources or (source.parent / SOURCES_FILE).is_file()
    return check(
        document,
        DocumentFormat(format),
        CheckOptions(sources, options.skip, options.limits, options.audience),
    )


def versions(source: Path, forced: str | None, requested: str | None) -> list[Audience | None]:
    """The versions to check: as ``generate --audience`` writes them."""
    format: str | None = GENERATE.target_format(source, forced)
    if format is None or requested is None:
        return [None]
    return GENERATE.audiences_of(source.read_text(encoding="utf-8"), format, requested)


def label(source: Path, audience: Audience | None) -> str:
    return f"{source} (fassung: {audience.value})" if audience is not None else str(source)


def as_json(source: Path, result: CheckResult, audience: Audience | None = None) -> dict[str, Any]:
    stats: dict[str, Any] | None = None
    if result.stats is not None:
        stats = asdict(result.stats)
        if isinstance(result.stats, DeckStats):
            stats["minutes"] = result.stats.minutes
        else:
            stats["pages"] = result.stats.pages
    return {
        "file": str(source),
        "audience": audience.value if audience is not None else None,
        "ok": result.ok,
        "errors": list(result.errors),
        "notes": [asdict(note) for note in result.notes],
        "stats": stats,
    }


def print_result(source: Path, result: CheckResult, audience: Audience | None = None) -> None:
    name = label(source, audience)
    if result.ok:
        print(f"OK {name}")
    for error in result.errors:
        print(f"ERROR {name}: {error}")
    for note in result.notes:
        print(f"  - {note} [{note.code}]")
    if result.stats is not None:
        for line in result.stats.lines():
            print(f"  {line}")


def main(argv: list[str]) -> int:
    forced: str | None = None
    strict = as_machine = sources = False
    skip: list[str] = []
    audience: str | None = None
    paths: list[Path] = []
    args = iter(argv)
    for arg in args:
        if arg in GENERATE.FORMAT_SWITCHES:
            forced = arg[2:]
        elif arg == "--strict":
            strict = True
        elif arg == "--json":
            as_machine = True
        elif arg == "--sources":
            sources = True
        elif arg == "--audience":
            audience = next(args, "").strip().lower()
            if audience not in GENERATE.AUDIENCE_VALUES:
                values = ", ".join(GENERATE.AUDIENCE_VALUES)
                print(f"--audience takes {values}, not '{audience}'", file=sys.stderr)
                return 1
        elif arg == "--skip":
            skip.extend(code.strip() for code in next(args, "").split(",") if code.strip())
        else:
            paths.append(Path(arg))
    if not paths:
        print(__doc__)
        return 1
    options = CheckOptions(sources=sources, skip=tuple(skip))
    ok = True
    report: list[dict[str, Any]] = []
    for path in paths:
        files = sorted(path.glob("*.md")) if path.is_dir() else [path]
        for source in files:
            if source.name.lower() in ("readme.md", SOURCES_FILE.lower()):
                continue
            for version in versions(source, forced, audience):
                result = check_file(source, forced, replace(options, audience=version))
                if result is None:
                    if not as_machine:
                        print(
                            f"skipped {source}: name it …-bericht.md or …-praesentation.md, "
                            "or pass --docx / --pptx / --pdf"
                        )
                    continue
                ok &= result.ok and not (strict and result.notes)
                if as_machine:
                    report.append(as_json(source, result, version))
                else:
                    print_result(source, result, version)
    if as_machine:
        print(json.dumps({"ok": ok, "files": report}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
