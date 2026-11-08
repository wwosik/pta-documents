"""E06-S03: the ``mermaid`` renderer (port of DocLibs ``MermaidRendererTests.cs`` and
``GenerationTests.cs``). A stand-in ``mmdc`` (a small script) answers with a recorded SVG, so
these run without Node.js; the tests with the real mermaid-cli are skipped without it."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest
from lxml import etree

from pta_documents import NoteCodes
from pta_documents.charts.renderer import ChartRenderer
from pta_documents.design import colors
from pta_documents.design.variants import Language
from pta_documents.diagrams import mermaid
from pta_documents.diagrams.mermaid import MermaidErrorMode, MermaidRenderer, diagram_type
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common import renderers
from pta_documents.generation.common.renderers import (
    CodeBlockRequest,
    DrawingGraphic,
    RendererUnavailableError,
)
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import MarkdownDocument
from tests.conftest import REVIEW_DIR
from tests.diagrams.support import DIAGRAMS, SAMPLES, skip_without_mermaid

FLOWCHART = "flowchart LR\n  A[Start] --> B{Gültig?}\n"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="the stand-in mmdc is a script")


def fake_mmdc(
    tmp_path: Path, *, stdout: Path | None = None, stderr: str = "", code: int = 0
) -> str:
    """A stand-in for mmdc: records its arguments, stdin and Chromium, then answers."""
    script = tmp_path / "mmdc"
    record = tmp_path / "call.json"
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "data = sys.stdin.buffer.read().decode('utf-8')\n"
        f"json.dump({{'args': sys.argv[1:], 'stdin': data,"
        f" 'chromium': os.environ.get('PUPPETEER_EXECUTABLE_PATH')}}, open({str(record)!r}, 'w'))\n"
        f"sys.stderr.write({stderr!r})\n"
        + (f"sys.stdout.buffer.write(open({str(stdout)!r}, 'rb').read())\n" if stdout else "")
        + f"sys.exit({code})\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def call(tmp_path: Path) -> dict[str, object]:
    return json.loads((tmp_path / "call.json").read_text(encoding="utf-8"))


def request(
    code: str = FLOWCHART,
    info: str = "mermaid",
    format: DocumentFormat = DocumentFormat.PPTX,
    line: int | None = 12,
) -> CodeBlockRequest:
    return CodeBlockRequest(info, code, line, format, Language.DE)


# ---------------------------------------------------------------------- without mmdc


@pytest.mark.parametrize(
    ("info", "code"),
    [
        ("python", FLOWCHART),
        ("chart", FLOWCHART),
        ("mermaid", "journey\n  title T\n  section S\n    Task: 5: Ich"),
        ("mermaid", "timeline\n  title T\n  2026 : Release"),
        ("mermaid", "   \n"),
    ],
)
def test_other_languages_and_types_stay_code(info: str, code: str) -> None:
    renderer = MermaidRenderer(command="/does/not/exist")
    assert renderer.render(request(code, info)) is None


@pytest.mark.parametrize(
    ("code", "kind"),
    [
        ("graph TD\n  A-->B", "graph"),
        ("%% Kommentar\n\nsequenceDiagram\n  A->>B: x", "sequenceDiagram"),
        ("---\ntitle: T\n---\nstateDiagram-v2\n  [*] --> A", "stateDiagram-v2"),
        ('%%{init: {}}%%\npie\n  "A" : 1', "pie"),
    ],
)
def test_the_type_is_the_first_word_after_front_matter_and_comments(code: str, kind: str) -> None:
    assert diagram_type(code) == kind


def test_a_missing_mmdc_is_unavailable_with_a_setup_hint() -> None:
    with pytest.raises(RendererUnavailableError, match=r"run \./run\.sh setup"):
        MermaidRenderer(command="/does/not/exist/mmdc").render(request())


def test_find_command_prefers_the_argument_then_the_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(mermaid.COMMAND_VARIABLE, "/from/env")
    assert mermaid.find_command("/given") == "/given"
    assert mermaid.find_command() == "/from/env"
    monkeypatch.delenv(mermaid.COMMAND_VARIABLE)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(mermaid, "REPO_LOCAL", tmp_path / "none")
    assert mermaid.find_command() is None
    fake_mmdc(tmp_path)
    assert mermaid.find_command() == str(tmp_path / "mmdc")


def test_the_init_directive_sets_the_pta_colours_and_strict_security() -> None:
    def config(format: DocumentFormat) -> dict[str, object]:
        line = mermaid.init_directive(format)
        assert line.startswith("%%{init: ") and line.endswith("}%%")
        return json.loads(line.removeprefix("%%{init: ").removesuffix("}%%"))

    slides, word = config(DocumentFormat.PPTX), config(DocumentFormat.DOCX)
    assert (slides["theme"], slides["securityLevel"], slides["htmlLabels"]) == (
        "base",
        "strict",
        False,
    )
    assert slides["flowchart"] == {"htmlLabels": False, "wrappingWidth": mermaid.WRAPPING_WIDTH}
    variables = slides["themeVariables"]
    assert isinstance(variables, dict)
    assert variables["primaryBorderColor"] == "#" + colors.PTA_BLUE
    assert variables["lineColor"] == "#" + colors.GREY_DARK
    assert variables["primaryColor"] == "#" + colors.GREY_LIGHT
    assert variables["background"] == "#" + colors.WHITE
    assert [variables[f"pie{i}"] for i in range(1, 7)] == ["#" + c for c in colors.ACCENTS]
    assert variables["textColor"] == "#" + colors.TEXT_SLIDES
    word_variables = word["themeVariables"]
    assert isinstance(word_variables, dict)
    assert word_variables["textColor"] == "#" + colors.TEXT_WORD
    assert "Segoe UI" in str(slides["fontFamily"])


def test_the_authoring_guide_names_the_types_and_the_error_mode() -> None:
    guide = MermaidRenderer().authoring_guide
    assert guide is not None and guide.startswith("## Diagramme")
    assert "`stateDiagram-v2`" in guide and "bricht" in guide
    kept = MermaidRenderer(on_error=MermaidErrorMode.KEEP_CODE).authoring_guide
    assert kept is not None and "bleibt ein Codeblock" in kept


def test_without_mmdc_the_defaults_leave_mermaid_out_and_the_note_says_what_to_set_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mermaid, "find_command", lambda command=None: None)
    assert renderers.default_renderers() == (ChartRenderer(),)
    markdown = "# Deck\n\n## Ablauf\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
    result = PptxGenerator().generate(MarkdownDocument(markdown), io.BytesIO())
    [note] = result.notes
    assert (note.code, note.line) == (NoteCodes.CODE_NOT_DRAWN, 5)
    assert "mermaid-cli is not set up" in note.message


# ---------------------------------------------------------------------- stand-in mmdc


@posix_only
def test_the_block_goes_to_mmdc_on_stdin_with_the_init_directive(tmp_path: Path) -> None:
    command = fake_mmdc(tmp_path, stdout=SAMPLES / "mermaid-flowchart.svg")
    renderer = MermaidRenderer(command=command, chromium="/my/chromium", puppeteer_config="p.json")
    graphic = renderer.render(request(info="Mermaid"))
    assert isinstance(graphic, DrawingGraphic)
    assert graphic.drawing.items
    recorded = call(tmp_path)
    assert recorded["args"] == [
        "-i",
        "-",
        "-o",
        "-",
        "-e",
        "svg",
        "-b",
        "white",
        "-q",
        "-p",
        "p.json",
    ]
    assert recorded["chromium"] == "/my/chromium"
    stdin = str(recorded["stdin"])
    assert stdin == mermaid.init_directive(DocumentFormat.PPTX) + "\n" + FLOWCHART


@posix_only
def test_the_puppeteer_configuration_comes_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(mermaid.PUPPETEER_CONFIG_VARIABLE, "/etc/pp.json")
    command = fake_mmdc(tmp_path, stdout=SAMPLES / "mermaid-pie.svg")
    MermaidRenderer(command=command).render(request('pie\n  "A" : 1'))
    assert call(tmp_path)["args"][-2:] == ["-p", "/etc/pp.json"]  # type: ignore[index]


@posix_only
def test_a_syntax_error_names_the_line_or_stays_code(tmp_path: Path) -> None:
    stderr = (
        "Error: Parse error on line 2:\n...A -->\n------^\nExpecting 'NODE_STRING', got 'EOF'\n"
        "Parser.parseError (https://mermaid-cli-intercept.invalid/x.mjs:1:2)\n    at y (z.js:1:1)\n"
    )
    command = fake_mmdc(tmp_path, stderr=stderr, code=1)
    with pytest.raises(ValueError) as error:
        MermaidRenderer(command=command).render(request())
    message = str(error.value)
    assert message.startswith("Line 12: The mermaid block cannot be drawn: Parse error on line 2:")
    assert "Expecting 'NODE_STRING'" in message
    assert "mermaid-cli-intercept" not in message
    kept = MermaidRenderer(command=command, on_error=MermaidErrorMode.KEEP_CODE)
    assert kept.render(request()) is None


@posix_only
def test_an_svg_that_cannot_be_drawn_is_an_error_too(tmp_path: Path) -> None:
    svg = tmp_path / "f.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><foreignObject/></svg>'
    )
    command = fake_mmdc(tmp_path, stdout=svg)
    with pytest.raises(ValueError, match="foreignObject"):
        MermaidRenderer(command=command).render(request())


@posix_only
def test_a_chromium_that_does_not_start_is_unavailable(tmp_path: Path) -> None:
    stderr = (
        "Error: Failed to launch the browser process!  Code: null\n\nNo usable sandbox!\n"
        "    at ChildProcess.onClose (file:///x/launch.js:346:24)\n"
    )
    command = fake_mmdc(tmp_path, stderr=stderr, code=1)
    with pytest.raises(RendererUnavailableError, match="cannot start Chromium") as error:
        MermaidRenderer(command=command).render(request())
    assert mermaid.PUPPETEER_CONFIG_VARIABLE in str(error.value)


@posix_only
def test_in_a_deck_the_diagram_is_a_group_of_shapes(tmp_path: Path) -> None:
    command = fake_mmdc(tmp_path, stdout=SAMPLES / "mermaid-flowchart.svg")
    options = PptxOptions(code_block_renderers=(MermaidRenderer(command=command),))
    markdown = "# Deck\n\n## Ablauf\n\n```mermaid\nflowchart TD\n  A --> B\n```\n"
    output = io.BytesIO()
    result = PptxGenerator().generate(MarkdownDocument(markdown), output, options)
    assert result.notes == ()
    groups = slide_groups(output.getvalue())
    assert len(groups) == 1
    presets = {g.get("prst") for g in groups[0].iter(f"{{{A}}}prstGeom")}
    assert {"rect", "ellipse"} <= presets
    assert list(groups[0].iter(f"{{{A}}}custGeom"))  # edges and arrowheads
    words = [t.text for t in groups[0].iter(f"{{{A}}}t")]
    assert "Fertig" in words


@posix_only
def test_in_word_the_diagram_is_an_svg_picture_with_its_caption(tmp_path: Path) -> None:
    """E03-S04: Word places the drawing as a PNG with the SVG beside it, text in Word's colour."""
    pytest.importorskip("resvg_py")
    command = fake_mmdc(tmp_path, stdout=SAMPLES / "mermaid-flowchart.svg")
    options = DocxOptions(code_block_renderers=(MermaidRenderer(command=command),))
    markdown = (
        "---\ntitel: B\n---\n# Bericht\n\n```mermaid\nflowchart TD\n  A --> B\n```\n\n"
        "Abbildung: Der Ablauf\n"
    )
    output = io.BytesIO()
    result = DocxGenerator().generate(MarkdownDocument(markdown), output, options)
    assert result.notes == ()
    assert colors.TEXT_WORD in str(call(tmp_path)["stdin"])
    import zipfile

    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as package:
        names = package.namelist()
        document = package.read("word/document.xml").decode("utf-8")
    assert any(n.endswith(".svg") for n in names) and any(n.endswith(".png") for n in names)
    assert "svgBlip" in document and 'descr="mermaid"' in document
    assert "Der Ablauf" in document and "SEQ Abbildung" in document


@posix_only
def test_a_syntax_error_in_a_deck_is_an_error_of_the_document(tmp_path: Path) -> None:
    command = fake_mmdc(tmp_path, stderr="Error: Parse error on line 2:\nbad\n", code=1)
    options = PptxOptions(code_block_renderers=(MermaidRenderer(command=command),))
    markdown = "---\ntitel: T\n---\n# Deck\n\n## A\n\n```mermaid\nflowchart LR\n  A -->\n```\n"
    with pytest.raises(DocumentConversionError, match="Line 8: The mermaid block"):
        PptxGenerator().generate(MarkdownDocument(markdown), io.BytesIO(), options)


def slide_groups(data: bytes) -> list[etree._Element]:
    import zipfile

    with zipfile.ZipFile(io.BytesIO(data)) as package:
        slides = [n for n in package.namelist() if n.startswith("ppt/slides/slide")]
        groups: list[etree._Element] = []
        for name in sorted(slides):
            tree = etree.fromstring(package.read(name))
            groups += [
                g
                for g in tree.iter(f"{{{P}}}grpSp")
                if g.find(f"{{{P}}}nvGrpSpPr/{{{P}}}cNvPr").get("name", "").startswith("Drawing")  # type: ignore[union-attr]
            ]
        return groups


# ---------------------------------------------------------------------- real mermaid-cli


def test_with_mermaid_cli_every_type_of_the_sample_becomes_a_group() -> None:
    skip_without_mermaid()
    document = MarkdownDocument(DIAGRAMS.read_text(encoding="utf-8"))
    output = io.BytesIO()
    result = PptxGenerator().generate(document, output)
    data = output.getvalue()
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    (REVIEW_DIR / "diagramme.pptx").write_bytes(data)
    assert len(slide_groups(data)) == 8
    [note] = result.notes  # the journey stays code
    assert note.code == NoteCodes.CODE_NOT_DRAWN


def test_with_mermaid_cli_a_syntax_error_names_the_line() -> None:
    skip_without_mermaid()
    with pytest.raises(
        ValueError, match=r"Line 12: The mermaid block cannot be drawn: .*Parse error"
    ):
        MermaidRenderer().render(request("flowchart LR\n  A -->\n"))
    kept = MermaidRenderer(on_error=MermaidErrorMode.KEEP_CODE)
    assert kept.render(request("flowchart LR\n  A -->\n")) is None


def test_with_mermaid_cli_nothing_but_mmdc_is_started_locally() -> None:
    """mmdc gets the code on stdin and answers on stdout; no file, no URL is involved."""
    skip_without_mermaid()
    graphic = MermaidRenderer().render(request())
    assert isinstance(graphic, DrawingGraphic)
    texts = " ".join(getattr(i, "text", "") for i in graphic.drawing.items)
    assert "Start" in texts and "Gültig?" in texts
