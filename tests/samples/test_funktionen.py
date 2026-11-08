"""E08-S03: ``samples/funktionen/`` is a feature tour the tests keep up to date.

Every file generates in its format (chosen as ``tools/generate`` chooses it) without notes, its
round trip through the converter is committed as ``funktionen/<file>.roundtrip.expected.md``
(renew with PTA_DOCUMENTS_UPDATE_EXPECTED=1), and the documents land in
``.tmp/review/funktionen/``. What has to be shown comes from the code: the front matter keys of
each generator, the template variants, the containers, alerts and heading attributes of the
slide syntax, ``==mark==``, coloured words, status labels, the ``chart`` blocks (every kind,
setting and separator), in the deck the ``financial-chart`` blocks (every type and option), in
the report one of them and an ``Abbildung: …`` caption after a graphic (E03-S04), and every
scheme of generated images (``qr:``, E11-S04).
When the authoring guides exist (E02-S05), the list comes from their syntax instead.
"""

from __future__ import annotations

import importlib.util
import io
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from markdown_it.token import Token

from pta_documents.charts import ChartKind
from pta_documents.charts import parser as chart_parser
from pta_documents.charts.financial import CHART_TYPES
from pta_documents.charts.financial import json_block as financial_block
from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design.colors import StatusCategory
from pta_documents.design.slides import TITLE_SLIDES
from pta_documents.design.variants import Language, SlidesVariant, WordVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import generated_images, heading_attributes, layout_syntax
from pta_documents.generation.common.code_blocks import KNOWN_GRAPHIC_LANGUAGES, fence_language
from pta_documents.generation.common.coloured_words import PATTERN
from pta_documents.generation.docx import generator as docx_generator
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx import generator as pptx_generator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument
from pta_documents.markdown.front_matter import FrontMatter, Keys
from pta_documents.markdown.parser import ALERT, CONTAINER_CLOSE, CONTAINER_OPEN, container, parse
from tests.conftest import REVIEW_DIR
from tests.diagrams.support import drawable
from tests.expected import assert_matches_expected

REPO: Final = Path(__file__).resolve().parents[2]
FOLDER: Final = REPO / "samples" / "funktionen"
EXPECTED: Final = Path(__file__).parent / "funktionen"
NOT_SAMPLES: Final = ("readme.md", "quellen.md")
CHART: Final = "chart"
FINANCIAL: Final = financial_block.LANGUAGE
SOURCE: Final = "markdown"
FIGURE_CAPTION: Final = "Abbildung: … after a graphic"
FIGURE_CAPTIONS: Final = ("Abbildung:", "Figure:")
GENERATED_IMAGE: Final = "![…]({scheme}…)"
"""The language of the fences that show the Markdown source of a feature."""
DOCX: Final = DocumentFormat.DOCX
PPTX: Final = DocumentFormat.PPTX


def load_generate_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_tool", REPO / "tools/generate/generate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL: Final = load_generate_tool()


def sample_files() -> list[Path]:
    return [p for p in sorted(FOLDER.glob("*.md")) if p.name.lower() not in NOT_SAMPLES]


def format_of(path: Path) -> DocumentFormat:
    chosen = TOOL.target_format(path, None)
    assert chosen in ("docx", "pptx"), f"{path.name}: name it …-bericht.md or …-praesentation.md"
    return DOCX if chosen == "docx" else PPTX


def images() -> tuple[DocumentResource, ...]:
    return tuple(TOOL.resources(FOLDER))


# ---------------------------------------------------------------------- generation


def test_every_sample_is_in_the_readme_table() -> None:
    readme = (FOLDER / "README.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| `([^`]+)` \|", readme, re.MULTILINE))
    files = {p.name for p in sample_files()}
    assert files - listed == set(), "add these files to the table in samples/funktionen/README.md"
    assert listed - files - {"images/"} == set(), "the README table lists files that do not exist"


def test_every_expected_round_trip_belongs_to_a_sample() -> None:
    stems = {p.stem for p in sample_files()}
    expected = {p.name.removesuffix(".roundtrip.expected.md") for p in EXPECTED.glob("*.md")}
    assert expected - stems == set()


@pytest.mark.parametrize("source", sample_files(), ids=lambda p: p.name)
def test_the_sample_generates_without_notes_and_round_trips(source: Path) -> None:
    format = format_of(source)
    if not drawable(source.read_text(encoding="utf-8")):
        pytest.skip("mermaid-cli is not set up or cannot start Chromium (./run.sh mermaid)")
    document = MarkdownDocument(source.read_text(encoding="utf-8"), images())
    output = io.BytesIO()
    generator = DocxGenerator() if format is DOCX else PptxGenerator()
    result = generator.generate(document, output)
    assert result.notes == (), f"{source.name}:\n{result}"
    data = output.getvalue()
    review = REVIEW_DIR / "funktionen"
    review.mkdir(parents=True, exist_ok=True)
    (review / f"{source.stem}.{format.value.lower()}").write_bytes(data)
    converter = DocxConverter() if format is DOCX else PptxConverter()
    markdown = converter.convert(data).text
    assert_matches_expected(EXPECTED / f"{source.stem}.roundtrip.expected.md", markdown)


# ---------------------------------------------------------------------- completeness


def body_tokens(text: str, format: DocumentFormat) -> tuple[FrontMatter, list[Token]]:
    front = FrontMatter.read(text, format)
    return front, parse(front.body)


def attribute_used(attributes: heading_attributes.HeadingAttributes, entry: str) -> bool:
    """Whether ``attributes`` use ``entry`` of ``heading_attributes.VALID`` (``.dark``,
    ``kicker="…"``); an entry this does not know counts as unused, so that it is reported."""
    if entry.startswith("."):
        name = entry[1:]
        if name in heading_attributes.SLIDE_KINDS:
            return attributes.kind == name
        return getattr(attributes, name, None) is True
    key = entry.partition("=")[0]
    return getattr(attributes, key, None) is not None


def inline_text(inline: Token) -> str:
    """The raw text of an inline token without its code spans."""
    return re.sub(r"`+[^`]*`+", "", inline.content)


def shown_in(text: str, format: DocumentFormat, shown: set[str]) -> None:
    front, tokens = body_tokens(text, format)
    for key, value in front.entries:
        shown.add(f"front matter: {key.lower()}")
        if key.lower() in (Keys.TEMPLATE, Keys.TITLE_SLIDE, Keys.LANGUAGE):
            shown.add(f"{key.lower()}: {value.strip().lower()}")
    labels = front.status_labels()
    for i, token in enumerate(tokens):
        if token.type == CONTAINER_OPEN:
            name, arguments = container(token)
            shown.add(f"::: {name}")
            if name == layout_syntax.PANEL and arguments:
                shown.add(f"::: {name} {arguments}")
            if name == layout_syntax.COLUMNS and layout_syntax.column_widths(arguments):
                shown.add(f"::: {name} <widths>")
        elif token.type == "blockquote_open" and ALERT in token.meta:
            shown.add(f"> [!{token.meta[ALERT]}]")
        elif token.type == "heading_open" and token.tag in ("h1", "h2") and token.level == 0:
            _, attributes = heading_attributes.split(tokens[i + 1].content, format)
            for entry in heading_attributes.VALID.split(", "):
                if attributes is not None and attribute_used(attributes, entry):
                    shown.add("{" + entry + "}")
        elif token.type == "fence" and fence_language(token.info) == CHART:
            shown_in_chart(token.content, shown)
        elif token.type == "fence" and fence_language(token.info) == FINANCIAL:
            shown_in_financial_chart(token.content, shown)
        elif token.type == "inline":
            if any(child.type == "mark_open" for child in token.children or ()):
                shown.add("==mark==")
            for child in token.children or ():
                source = str(child.attrs.get("src", "")) if child.type == "image" else ""
                if generated_images.is_generated(source):
                    scheme = source.strip().lower().partition(":")[0] + ":"
                    shown.add(GENERATED_IMAGE.format(scheme=scheme))
            for span in PATTERN.finditer(inline_text(token)):
                shown.add(f"[words]{{.{span.group('category').lower()}}}")
            cell = re.fullmatch(r"`([^`]+)`", token.content.strip())
            if tokens[i - 1].type == "td_open" and cell and cell.group(1) in labels:
                shown.add(f"status label: status.{labels[cell.group(1)].value}")
        if figure_caption_after(tokens, i):
            shown.add(FIGURE_CAPTION)


def figure_caption_after(tokens: list[Token], i: int) -> bool:
    """Whether ``tokens[i]`` is a fence in a graphic language with an ``Abbildung: …``
    paragraph directly after it (E03-S04)."""
    token = tokens[i]
    if token.type != "fence" or fence_language(token.info) not in KNOWN_GRAPHIC_LANGUAGES:
        return False
    after = tokens[i + 1 : i + 3]
    return (
        len(after) == 2
        and after[0].type == "paragraph_open"
        and after[1].content.startswith(FIGURE_CAPTIONS)
    )


def shown_in_chart(code: str, shown: set[str]) -> None:
    """The settings, kind and separator a ``chart`` block shows."""
    spec = chart_parser.parse(code)
    shown.add(f"```{CHART} type: {spec.kind.value}")
    settings, separator, data = code.partition(f"\n{chart_parser.SEPARATOR_LINE}\n")
    for line in settings.splitlines() if separator else ():
        key = line.partition(":")[0].strip().lower()
        if key in chart_parser.SETTINGS:
            shown.add(f"```{CHART} {key}:")
    header = (data if separator else code).strip().splitlines()[0]
    shown.add(f"```{CHART} separator {';' if ';' in header else ','}")


def shown_in_financial_chart(code: str, shown: set[str]) -> None:
    """The type and the options a ``financial-chart`` block shows."""
    chart, _ = financial_block.parse(code)
    names = {kind: name for name, kind in CHART_TYPES.items()}
    shown.add(f"```{FINANCIAL}")
    shown.add(f"```{FINANCIAL} type: {names[type(chart)]}")
    options = re.search(r'"options"\s*:\s*\{(.*)\}', code, re.DOTALL)
    for key in re.findall(r'"(\w+)"\s*:', options.group(1) if options else ""):
        if key in financial_block.OPTION_KEYS:
            shown.add(f"```{FINANCIAL} options: {key}")


def required(format: DocumentFormat) -> set[str]:
    """Everything the samples of ``format`` have to show."""
    keys = docx_generator.VALID_KEYS if format is DOCX else pptx_generator.VALID_KEYS
    variants = WordVariant if format is DOCX else SlidesVariant
    result = {f"front matter: {key}" for key in keys}
    result |= {f"{Keys.TEMPLATE}: {variant.value}" for variant in variants}
    result |= {f"{Keys.LANGUAGE}: {language.value}" for language in Language}
    for category in StatusCategory:
        result.add(f"front matter: {Keys.STATUS_PREFIX}{category.value}")
        result.add(f"status label: {Keys.STATUS_PREFIX}{category.value}")
        result.add(f"[words]{{.{category.value}}}")
    # Word leaves speaker notes out with a note, and the samples generate without notes.
    containers = [
        name for name in layout_syntax.CONTAINER_NAMES if format is PPTX or name != "notes"
    ]
    result |= {f"::: {name}" for name in containers}
    # The arguments ``check_container`` accepts.
    result |= {f"::: {layout_syntax.PANEL} dark", f"::: {layout_syntax.COLUMNS} <widths>"}
    result |= {f"> [!{kind}]" for kind in layout_syntax.ALERT_KINDS}
    result.add("==mark==")
    result |= {GENERATED_IMAGE.format(scheme=scheme) for scheme in generated_images.SCHEMES}
    result |= {f"```{CHART} type: {kind.value}" for kind in ChartKind}
    result |= {f"```{CHART} {key}:" for key in chart_parser.SETTINGS}
    result |= {f"```{CHART} separator ,", f"```{CHART} separator ;"}
    if format is DOCX:
        # Word places drawings as pictures (E03-S04); every type and option is in the deck.
        result |= {f"```{FINANCIAL}", FIGURE_CAPTION}
    if format is PPTX:
        result |= {f"```{FINANCIAL} type: {name}" for name in CHART_TYPES}
        result |= {f"```{FINANCIAL} options: {key}" for key in financial_block.OPTION_KEYS}
        # Word drops the heading attributes; they are slide syntax.
        result |= {"{" + entry + "}" for entry in heading_attributes.VALID.split(", ")}
        result |= {f"{Keys.TITLE_SLIDE}: {name}" for name in TITLE_SLIDES}
    return result


@pytest.mark.parametrize("format", [DOCX, PPTX], ids=lambda f: f.value)
def test_the_samples_show_every_syntax_key_and_variant(format: DocumentFormat) -> None:
    shown: set[str] = set()
    for source in sample_files():
        if format_of(source) is format:
            shown_in(source.read_text(encoding="utf-8"), format, shown)
    missing = sorted(required(format) - shown)
    assert missing == [], (
        f"samples/funktionen/ has no {format.value} example of: {', '.join(missing)}"
    )


def test_a_missing_example_is_named() -> None:
    shown: set[str] = set()
    shown_in("# Deck\n\n## Folie {.dark}\n\n::: cards\nText\n:::\n", PPTX, shown)
    missing = required(PPTX) - shown
    assert "{.dark}" not in missing and "::: cards" not in missing
    assert {"{.agenda}", "::: rows", "> [!NOTE]", "==mark==", "titelfolie: branchen"} <= missing


# ---------------------------------------------------------------------- source next to result


@dataclass(frozen=True)
class Section:
    heading: str
    sources: tuple[str, ...]
    """The Markdown source fences of the section (in a deck: those in its ``::: notes``)."""


def sections(text: str, format: DocumentFormat) -> tuple[list[Section], list[str]]:
    """The ``##`` sections of ``text`` with their source fences, and for each source fence the
    file without the lines of that fence (where its result has to be)."""
    front, tokens = body_tokens(text, format)
    lines = text.split("\n")
    found: list[tuple[str, list[str]]] = []
    rest: list[str] = []
    open_containers: list[str] = []
    for i, token in enumerate(tokens):
        if token.type == CONTAINER_OPEN:
            open_containers.append(container(token)[0])
        elif token.type == CONTAINER_CLOSE:
            open_containers.pop()
        elif token.type == "heading_open" and token.level == 0 and token.tag in ("h1", "h2"):
            found.append((tokens[i + 1].content, []) if token.tag == "h2" else ("", []))
        elif token.type == "fence" and token.info.strip() == SOURCE and token.map is not None:
            in_notes = layout_syntax.NOTES in open_containers
            if found and (format is DOCX or in_notes):
                found[-1][1].append(token.content)
            start, end = (n + front.body_line for n in token.map)
            rest.append("\n".join(lines[:start] + lines[end:]))
    return [Section(h, tuple(s)) for h, s in found if h], rest


@pytest.mark.parametrize(
    ("name", "format"),
    [("funktionen-bericht.md", DOCX), ("funktionen-praesentation.md", PPTX)],
)
def test_every_feature_shows_its_source_and_its_result(name: str, format: DocumentFormat) -> None:
    """The report has a ``markdown`` fence in every ``##`` section, the deck one in the notes of
    every ``##`` slide; the source is found verbatim outside its fence, as the result."""
    text = (FOLDER / name).read_text(encoding="utf-8")
    found, rests = sections(text, format)
    assert found
    without = [s.heading for s in found if not s.sources]
    assert without == [], f"{name}: no ```markdown source under: {', '.join(without)}"
    _, tokens = body_tokens(text, format)
    all_fences = [t.content for t in tokens if t.type == "fence" and t.info.strip() == SOURCE]
    for source, rest in zip(all_fences, rests, strict=True):
        assert source in rest, f"{name}: the result of this source is missing:\n{source}"
