"""The ``mermaid`` code-block renderer: Mermaid diagrams drawn locally by mermaid-cli (E06-S03).

Port of DocLibs ``MermaidRenderer.cs``; DocLibs used the C# library Mermaider, here mermaid-cli
(``mmdc``, Node.js and a headless Chromium) draws the SVG, and ``drawing.svg`` turns it into a
``Drawing``: editable shapes on slides, vectors in PDF. Nothing leaves the computer: ``mmdc``
runs as a local process with the code on stdin and the SVG on stdout, ``securityLevel:
strict``, and the colours come from ``design.diagram_colors``.

Where ``mmdc`` comes from: ``MermaidRenderer.command``, else the environment variable
``PTA_DOCUMENTS_MMDC``, else ``mmdc`` on the ``PATH``, else the repo-local installation of
``./run.sh setup`` (``tools/mermaid/node_modules/.bin/mmdc`` next to a source checkout). The
Chromium: ``chromium``, else ``PUPPETEER_EXECUTABLE_PATH``, else the one puppeteer installed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from pta_documents.design import colors, diagram_colors
from pta_documents.drawing.svg import SvgDrawingError, to_drawing
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import (
    CodeBlockGraphic,
    CodeBlockRequest,
    DrawingGraphic,
    RendererUnavailableError,
)

LANGUAGE: Final = "mermaid"
COMMAND_VARIABLE: Final = "PTA_DOCUMENTS_MMDC"
CHROMIUM_VARIABLE: Final = "PUPPETEER_EXECUTABLE_PATH"
PUPPETEER_CONFIG_VARIABLE: Final = "PTA_DOCUMENTS_PUPPETEER_CONFIG"
SUPPORTED: Final = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "pie",
    "gantt",
    "mindmap",
)
"""The diagram types drawn, by the first word of the diagram; the others stay code."""
WRAPPING_WIDTH: Final = 300
"""Where mermaid wraps node labels, in pixels; at its default (200) Chromium without Segoe UI
breaks words like "Markdown-Dokument" in the middle."""
REPO_LOCAL: Final = (
    Path(__file__).resolve().parents[3] / "tools" / "mermaid" / "node_modules" / ".bin"
)
"""Where ``./run.sh setup`` installs mermaid-cli, for a source checkout."""
_BROWSER_FAILURES: Final = (
    "Failed to launch the browser process",
    "Could not find Chrome",
    "Could not find chrome",
    "no executable was found",
    "Tried to find the browser",
    "Browser was not found",
)
_STACK_LINE: Final = re.compile(r"^\s*at\s|\((?:file|https?):")

AUTHORING_GUIDE: Final = """## Diagramme

Ein Codeblock mit der Sprache `mermaid` wird ein Diagramm in den PTA-Farben — auf Folien als
Gruppe bearbeitbarer Formen. Diagramme nur dort, wo ein Bild mehr sagt als Aufzählungen: ein
Ablauf, eine Abfolge von Aufrufen, ein Datenmodell, ein Plan.

````markdown
```mermaid
flowchart LR
    A[Antrag] --> B{Vollständig?}
    B -->|ja| C[Bearbeiten]
    B -->|nein| D[Zurück]
```
````

- **Gezeichnet:** `flowchart` (oder `graph`, mit `subgraph`), `sequenceDiagram`,
  `classDiagram`, `stateDiagram-v2`, `erDiagram`, `pie`, `gantt`, `mindmap`.
- **Nicht gezeichnet:** jede andere Art (`journey`, `timeline`, `gitGraph`, C4, …) bleibt ein
  Codeblock. Nicht verwenden.
- Diagramme klein halten: bis etwa zwölf Knoten, kurze Beschriftungen. Ein breites Diagramm wird
  samt Schrift verkleinert und schwer lesbar.
- Farben kommen aus dem Design; `classDef`, `style` und Symbole besser weglassen.
- Word setzt Diagramme noch nicht; dort bleibt der Block Code (mit Hinweis).
- {errors}
"""


class MermaidErrorMode(StrEnum):
    """What ``MermaidRenderer`` does with a block it cannot draw."""

    THROW = "throw"
    """Raise an error naming the block's line and the reason, so mistakes are noticed."""
    KEEP_CODE = "keep-code"
    """Leave the block as code."""


def find_command(command: str | None = None) -> str | None:
    """The ``mmdc`` to run: ``command``, ``PTA_DOCUMENTS_MMDC``, ``mmdc`` on the ``PATH``, or
    the repo-local installation; None when there is none."""
    if command:
        return command
    configured = os.environ.get(COMMAND_VARIABLE)
    if configured:
        return configured
    found = shutil.which("mmdc")
    if found:
        return found
    for name in ("mmdc", "mmdc.cmd"):
        local = REPO_LOCAL / name
        if local.is_file():
            return str(local)
    return None


def setup_hint() -> str:
    """What to set up so that ``mermaid`` blocks are drawn."""
    return (
        "mermaid-cli is not set up. Install Node.js (22 or later) and run ./run.sh setup, or "
        f"point {COMMAND_VARIABLE} at an mmdc (see docs/verwendung.md, Mermaid)."
    )


def diagram_type(code: str) -> str | None:
    """The first word of the diagram, after a YAML front matter and ``%%`` lines."""
    lines = code.splitlines()
    index = 0
    if lines and lines[0].strip() == "---":
        closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        index = closing + 1 if closing is not None else len(lines)
    for line in lines[index:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("%%"):
            return stripped.split()[0]
    return None


def init_directive(format: DocumentFormat) -> str:
    """The ``%%{init: …}%%`` line set before the code: base theme in the PTA colours, classic
    look, strict security, text as SVG text (``htmlLabels: false``)."""
    text = colors.TEXT_SLIDES if format is DocumentFormat.PPTX else colors.TEXT_WORD
    config = {
        "theme": "base",
        "look": "classic",
        "securityLevel": "strict",
        "htmlLabels": False,
        "flowchart": {"htmlLabels": False, "wrappingWidth": WRAPPING_WIDTH},
        "fontFamily": diagram_colors.FONT_FAMILY,
        "themeVariables": diagram_colors.theme_variables(text),
        "themeCSS": diagram_colors.theme_css(text),
    }
    return "%%{init: " + json.dumps(config, separators=(",", ":")) + "}%%"


@dataclass(frozen=True, slots=True)
class MermaidRenderer:
    """Renders ``mermaid`` blocks of the supported types as a ``DrawingGraphic``."""

    command: str | None = None
    """The ``mmdc`` to run; None: see ``find_command``."""
    chromium: str | None = None
    """The Chromium for puppeteer; None: ``PUPPETEER_EXECUTABLE_PATH`` or puppeteer's own."""
    puppeteer_config: str | None = None
    """A puppeteer configuration file for ``mmdc -p`` (e.g. ``{"args": ["--no-sandbox"]}``
    where Chromium has no sandbox); None: ``PTA_DOCUMENTS_PUPPETEER_CONFIG`` or none."""
    timeout_s: float = 60
    on_error: MermaidErrorMode = MermaidErrorMode.THROW

    @property
    def authoring_guide(self) -> str | None:
        errors = (
            "Ein Diagramm mit Syntaxfehler bricht mit der Zeile seines Blocks und der Meldung "
            "von Mermaid ab."
            if self.on_error is MermaidErrorMode.THROW
            else "Ein Diagramm mit Syntaxfehler bleibt ein Codeblock; das Ergebnis prüfen."
        )
        return AUTHORING_GUIDE.replace("{errors}", errors)

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        """A ``DrawingGraphic`` for a ``mermaid`` block of a supported type; None for other
        languages and types.

        Raises ``RendererUnavailableError`` when mmdc or Chromium cannot run here or the
        format has no place for drawings (Word), and ``ValueError`` for a diagram that cannot
        be drawn (unless ``on_error`` is ``KEEP_CODE``).
        """
        words = request.info.split()
        if not words or words[0].lower() != LANGUAGE:
            return None
        if diagram_type(request.code) not in SUPPORTED:
            return None
        if request.format is DocumentFormat.DOCX:
            raise RendererUnavailableError(
                "Word does not draw Mermaid diagrams yet; PowerPoint does. Leave the block "
                "out of the report, or keep it as code."
            )
        try:
            svg = self.run(request)
            return DrawingGraphic(to_drawing(svg))
        except (MermaidSyntaxError, SvgDrawingError) as error:
            if self.on_error is MermaidErrorMode.KEEP_CODE:
                return None
            where = f"Line {request.line}: " if request.line else ""
            raise ValueError(f"{where}The mermaid block cannot be drawn: {error}") from error

    def run(self, request: CodeBlockRequest) -> bytes:
        """The SVG mermaid-cli draws of the block."""
        command = find_command(self.command)
        if command is None:
            raise RendererUnavailableError(setup_hint())
        arguments = [command, "-i", "-", "-o", "-", "-e", "svg", "-b", "white", "-q"]
        config = self.puppeteer_config or os.environ.get(PUPPETEER_CONFIG_VARIABLE)
        if config:
            arguments += ["-p", config]
        environment = dict(os.environ)
        if self.chromium:
            environment[CHROMIUM_VARIABLE] = self.chromium
        source = init_directive(request.format) + "\n" + request.code
        try:
            completed = subprocess.run(
                arguments,
                input=source.encode("utf-8"),
                capture_output=True,
                timeout=self.timeout_s,
                env=environment,
                check=False,
            )
        except FileNotFoundError as error:
            raise RendererUnavailableError(
                f"mermaid-cli ({command}) cannot be started: {error.strerror}. " + setup_hint()
            ) from error
        except subprocess.TimeoutExpired as error:
            where = f"Line {request.line}: " if request.line else ""
            raise ValueError(
                f"{where}The mermaid block took longer than {self.timeout_s:g} s to draw; "
                "simplify the diagram, or raise MermaidRenderer.timeout_s."
            ) from error
        message = _message(completed.stderr.decode("utf-8", "replace"))
        if completed.returncode != 0 or not completed.stdout.strip():
            if any(failure in message for failure in _BROWSER_FAILURES):
                raise RendererUnavailableError(
                    "mermaid-cli cannot start Chromium: "
                    + _first_sentence(message)
                    + f" Set {CHROMIUM_VARIABLE} to a Chrome or Chromium, and where Chromium has "
                    f"no sandbox, {PUPPETEER_CONFIG_VARIABLE} to a puppeteer configuration with "
                    '{"args": ["--no-sandbox"]} (see docs/verwendung.md, Mermaid).'
                )
            raise MermaidSyntaxError(message or f"mmdc ended with exit code {completed.returncode}")
        return completed.stdout


class MermaidSyntaxError(Exception):
    """mermaid-cli refused the diagram; the message is mermaid's."""


def _message(stderr: str) -> str:
    """mermaid's message without the JavaScript stack."""
    lines: list[str] = []
    for line in stderr.strip().splitlines():
        if _STACK_LINE.search(line):
            if lines:
                break
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip().removeprefix("Error: ")


def _first_sentence(message: str) -> str:
    """The first line of ``message``, ending in a full stop."""
    line = (message.splitlines()[0] if message else "").strip()[:300]
    return line if line.endswith(".") else line + "."
