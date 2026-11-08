"""E02-S05: the shared parts of the authoring guides (port of DocLibs ``AuthoringGuides`` and
the cases of its ``AuthoringGuideTests`` that do not need a generator's own guide)."""

from __future__ import annotations

import importlib.util
import io
from dataclasses import dataclass
from types import ModuleType
from typing import Final

import pytest

from pta_documents.charts.renderer import ChartRenderer
from pta_documents.design import icons
from pta_documents.design.colors import StatusCategory
from pta_documents.design.variants import WordVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common import heading_attributes, layout_syntax
from pta_documents.generation.common.authoring_guides import GuideKey
from pta_documents.generation.common.renderers import CodeBlockGraphic, CodeBlockRequest
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.docx import generator as docx_generator
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.docx.options import DocxOptions
from pta_documents.generation.pptx import generator as pptx_generator
from pta_documents.markdown import MarkdownDocument, block_markers
from pta_documents.markdown.front_matter import Keys
from tests.conftest import REPO_ROOT
from tests.generation.guides import (
    assert_examples_generate,
    assert_names_everything,
    assert_under,
    examples,
)

DOCX: Final = DocumentFormat.DOCX
PPTX: Final = DocumentFormat.PPTX
PDF: Final = DocumentFormat.PDF
FORMATS: Final = (DOCX, PPTX, PDF)


# ---------------------------------------------------------------------- fill and template


def test_a_placeholder_alone_on_its_line_with_an_empty_value_leaves_no_blank_line() -> None:
    filled = guides.fill("## A\n\n{{empty}}\n\nText\n", {"empty": ""})
    assert filled == "## A\n\nText\n"


def test_fill_trims_the_line_breaks_of_values_and_ends_with_one() -> None:
    filled = guides.fill("{{a}}\n\n{{b}}\n\n\n", {"a": "\n## A\n", "b": "B\n\n"})
    assert filled == "## A\n\nB\n"


def test_fill_replaces_a_placeholder_inside_a_line() -> None:
    assert guides.fill("Bilder: {{formats}}.", {"formats": "PNG, SVG"}) == "Bilder: PNG, SVG.\n"


def test_a_placeholder_without_a_value_is_a_programming_error() -> None:
    with pytest.raises(KeyError, match="missing"):
        guides.fill("{{missing}}", {"other": ""})


def test_the_template_comes_from_the_package_folder() -> None:
    text = guides.template("tests.generation.common", "beispiel")
    assert text.startswith("## Ein Word-Dokument aus Markdown\n")
    assert "\r" not in text
    with pytest.raises(FileNotFoundError):
        guides.template("tests.generation.common", "fehlt")


def test_words_counts_runs_of_letters_and_digits() -> None:
    assert guides.words("## Über `vorlage: hoch-ohne-deckblatt` — 2 500 Wörter!") == 8
    assert guides.words("") == 0


def test_names_and_choices() -> None:
    assert guides.names(["a"]) == "`a`"
    assert guides.names(["a", "b", "c"]) == "`a`, `b` oder `c`"
    assert guides.names(["a", "b"], "und") == "`a` und `b`"
    assert guides.choices(["hoch", "quer"], "hoch") == "`hoch` (Standard), `quer`"


# ---------------------------------------------------------------------- front matter


def rows(keys: tuple[str, ...]) -> list[GuideKey]:
    common = guides.common_keys()
    return [common.get(k) or GuideKey(k, "frei", f"Bedeutung von {k}.") for k in keys]


@pytest.mark.parametrize(
    "valid", [docx_generator.VALID_KEYS, pptx_generator.VALID_KEYS], ids=["docx", "pptx"]
)
def test_the_front_matter_section_lists_every_key(valid: tuple[str, ...]) -> None:
    section = guides.front_matter_section(rows(valid), valid, "titel: Netzausbau 2027")
    assert section.startswith("## Front Matter\n")
    assert_names_everything(section, [f"| `{key}` |" for key in valid])
    assert guides.named_keys(section) == [*valid, f"{Keys.STATUS_PREFIX}<kategorie>"]
    assert all(f"`{c.value}`" in section for c in StatusCategory)
    assert "```markdown\n---\ntitel: Netzausbau 2027\n---\n```" in section


def test_the_front_matter_rows_have_to_match_the_valid_keys() -> None:
    valid = docx_generator.VALID_KEYS
    with pytest.raises(ValueError, match="missing"):
        guides.front_matter_section(rows(valid)[1:], valid, "titel: A")
    with pytest.raises(ValueError, match="not valid"):
        guides.front_matter_section([*rows(valid), GuideKey("farbe", "", "")], valid, "")
    with pytest.raises(ValueError, match="twice"):
        guides.front_matter_section([*rows(valid), rows(valid)[0]], valid, "")


def test_without_status_there_is_no_status_row() -> None:
    section = guides.front_matter_section(rows((Keys.TITLE,)), (Keys.TITLE,), "", status=False)
    assert Keys.STATUS_PREFIX not in section


def test_the_common_keys_are_valid_in_every_generator() -> None:
    for valid in (docx_generator.VALID_KEYS, pptx_generator.VALID_KEYS):
        assert set(guides.common_keys()) <= set(valid)


# ---------------------------------------------------------------------- characters


INTRO: Final = "Zeichen, die den Schriften fehlen, werden `?`."


def test_the_characters_section_names_what_the_fonts_lack_with_a_replacement_they_have() -> None:
    lacking_text = {ord("✓"), ord("●"), ord("•"), ord("▲"), ord("↑")}
    section = guides.characters_section(
        lambda c: c not in lacking_text, lambda c: c != ord("─"), INTRO
    )
    assert section.startswith(INTRO + "\n\n| Vermeiden | Stattdessen |\n")
    assert "| ✓ | `[x]` |" in section
    # The first replacement (•) is missing too, so the next one.
    assert "| ● | `*` |" in section
    # Symbols with the same replacement share a row (symbols are no words: a short guide).
    assert "| ↑ ▲ | `hoch` |" in section
    assert "| ─ | `-` |" in section
    assert "✔" not in section
    assert section.endswith("\n\nIn Code gehen: ✓ ● ↑ ▲. Nur im Text gehen: ─.\n")


def test_a_missing_character_in_both_fonts_has_no_remark_and_pipes_are_escaped() -> None:
    section = guides.characters_section(lambda c: c != ord("│"), lambda c: c != ord("│"), INTRO)
    assert "| │ | `\\|` |" in section
    assert "gehen:" not in section


def test_with_every_symbol_the_characters_section_is_the_intro() -> None:
    assert guides.characters_section(lambda _: True, lambda _: True, INTRO) == INTRO + "\n"


def test_every_replacement_is_shorter_ascii_or_another_symbol() -> None:
    symbols = {s for s, _ in guides.SYMBOLS}
    for symbol, replacements in guides.SYMBOLS:
        assert replacements[-1].isascii(), symbol
        assert all(r.isascii() or r in symbols or r in "•–" for r in replacements), symbol


# ---------------------------------------------------------------------- slide syntax


def test_every_name_of_the_code_has_a_text() -> None:
    assert list(guides.CONTAINER_TEXTS) == list(layout_syntax.CONTAINER_NAMES)
    assert list(guides.ALERT_TEXTS) == list(layout_syntax.ALERT_KINDS)
    assert set(guides.STATUS_TEXTS) == set(StatusCategory)
    assert list(guides.ATTRIBUTE_TEXTS) == [e.strip() for e in heading_attributes.VALID.split(",")]
    assert list(guides.MARKER_TEXTS) == list(block_markers.NAMES)
    assert list(guides.NOTE_TEXTS) == list(NoteCodes.ALL)
    assert {*guides.DOCUMENT_ATTRIBUTES, *guides.DOCUMENT_ONLY_ATTRIBUTES} <= set(
        guides.ATTRIBUTE_TEXTS
    )


@pytest.mark.parametrize("format", FORMATS, ids=lambda f: f.value)
def test_the_slide_syntax_names_every_container_alert_attribute_and_marker(
    format: DocumentFormat,
) -> None:
    section = guides.layout_syntax_section(format, "In diesem Format schlicht.")
    assert section.startswith("## Folien-Syntax\n\n")
    assert "\n\nIn diesem Format schlicht.\n\n" in section
    left_out = guides.LEFT_OUT_CONTAINERS.get(format, ())
    assert_names_everything(
        section,
        [
            f"`{name}`" if name in left_out else f"`::: {name}`"
            for name in layout_syntax.CONTAINER_NAMES
        ],
    )
    assert_names_everything(section, [f"`> [!{kind}]`" for kind in layout_syntax.ALERT_KINDS])
    assert_names_everything(section, [f"`{{.{c.value}}}`" for c in StatusCategory])
    assert_names_everything(section, ["`==Text==`", "`::: panel dark`", "`::: columns 1:2`"])
    for entry in (e.strip() for e in heading_attributes.VALID.split(",")):
        written, _ = guides.ATTRIBUTE_TEXTS[entry]
        assert written in section or f"`{entry}`" in section, entry
    for name in block_markers.NAMES:
        assert f"`{{.{name}}}`" in section or f"`.{name}`" in section, name


def test_word_and_pdf_name_slide_only_syntax_so_that_samples_need_not_show_it() -> None:
    docx = guides.named_syntax(guides.layout_syntax_section(DOCX))
    pdf = guides.named_syntax(guides.layout_syntax_section(PDF))
    deck = guides.named_syntax(guides.layout_syntax_section(PPTX))
    assert "::: notes" not in docx and "::: scene" not in docx
    assert "::: notes" not in pdf and "::: scene" in pdf
    assert "{.dark" not in docx and "{.build" not in docx and "{.appendix" in docx
    assert {"::: notes", "::: scene", "{.dark", "{kicker", "{.build", "{.backup"} <= set(deck)
    assert "::: name" not in deck and "{.appendix" not in deck


@pytest.mark.parametrize(
    ("container", "code"),
    [
        ("::: notes\nGesprochen.\n:::", NoteCodes.NOTES_DROPPED),
        ('::: scene\n- a: box 10,10 40x20 "A"\n:::', NoteCodes.SCENE_DROPPED),
    ],
)
def test_word_leaves_out_what_the_section_says_it_leaves_out(container: str, code: str) -> None:
    assert container.split("\n")[0][4:] in guides.LEFT_OUT_CONTAINERS[DOCX]
    markdown = f"---\nvorlage: hoch-ohne-deckblatt\n---\n# Kapitel\n\n## Teil\n\n{container}\n"
    result = DocxGenerator().generate(MarkdownDocument(markdown), io.BytesIO())
    assert [n.code for n in result.notes] == [code]


# ---------------------------------------------------------------------- other sections


@pytest.mark.parametrize("format", FORMATS, ids=lambda f: f.value)
def test_the_icons_section_names_every_icon(format: DocumentFormat) -> None:
    section = guides.icons_section(format)
    assert_names_everything(section, [f"`{name}`" for name in icons.ICONS])
    assert ("Karte" in section) is (format is PPTX)


@pytest.mark.parametrize("format", FORMATS, ids=lambda f: f.value)
def test_the_notes_section_names_the_codes_of_the_format(format: DocumentFormat) -> None:
    section = guides.notes_section(format)
    for code, (formats, _) in guides.NOTE_TEXTS.items():
        assert (f"| `{code}` |" in section) is (format in formats), code
    assert "`slide-split`" in guides.notes_section(PPTX)
    assert "`character-missing`" in guides.notes_section(PDF)


def test_the_typography_section_names_its_keys() -> None:
    section = guides.typography_section()
    assert_names_everything(section, [Keys.TYPOGRAPHY, Keys.HIGHLIGHT, "code-language-unknown"])


@dataclass(frozen=True)
class Described:
    authoring_guide: str | None

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        return None


def test_the_renderers_section_joins_the_sections_of_renderers_that_have_one() -> None:
    renderers = (
        Described("\n## Eins\n\nA\n"),
        Described(None),
        Described("  \n"),
        Described("## Zwei"),
    )
    assert guides.renderers_section(renderers) == "## Eins\n\nA\n\n## Zwei"
    assert guides.renderers_section(()) == ""


@dataclass(frozen=True)
class Converter:
    format: str | None

    def convert(self, image: object, scale: float) -> None:
        return None


def test_image_formats_are_the_native_ones_then_those_of_the_converters() -> None:
    converters = (Converter("SVG"), Converter(None), Converter("png"))
    assert guides.image_formats(("PNG", "JPEG"), converters) == ("PNG", "JPEG", "SVG")


# ---------------------------------------------------------------------- a guide from the parts


def example_guide() -> str:
    """A Word guide as E03-S05 builds one: template plus the shared parts, without repeating a
    list of keys or syntax."""
    valid = docx_generator.VALID_KEYS
    return guides.fill(
        guides.template("tests.generation.common", "beispiel"),
        {
            "syntax": guides.layout_syntax_section(DOCX, "Word zeigt sie schlicht."),
            "icons": guides.icons_section(DOCX),
            "typography": guides.typography_section(),
            "diagrams": guides.renderers_section((ChartRenderer(),)),
            "frontMatter": guides.front_matter_section(
                rows(valid), valid, "titel: Netzausbau 2027\nvorlage: hoch"
            ),
            "notes": guides.notes_section(DOCX),
            "characters": "",
        },
    )


def generate_docx(markdown: str) -> None:
    options = DocxOptions(
        variant=WordVariant.PORTRAIT_NO_COVER, code_block_renderers=(ChartRenderer(),)
    )
    result = DocxGenerator().generate(MarkdownDocument(markdown), io.BytesIO(), options)
    assert result.notes == (), str(result)


def test_a_guide_from_template_and_parts_generates_every_example() -> None:
    guide = example_guide()
    assert "{{" not in guide and "\n\n\n" not in guide and guide.endswith("> Ein Hinweis.\n````\n")
    assert len(examples(guide)) == 4  # front matter, chart, financial chart, the report
    assert_examples_generate(guide, generate_docx, at_least=4)
    assert_under(guide)
    assert_names_everything(guide, [f"`{key}`" for key in docx_generator.VALID_KEYS])


def test_a_failing_example_is_shown() -> None:
    guide = "## A\n\n```markdown\n# Kapitel\n\n::: karte\nx\n:::\n```\n"
    with pytest.raises(AssertionError, match="karte"):
        assert_examples_generate(guide, generate_docx)


def test_a_guide_over_the_limit_fails() -> None:
    with pytest.raises(AssertionError, match="3 words"):
        assert_under("ein zwei drei", 3)


# ---------------------------------------------------------------------- the tool


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "authoring_guide_tool", REPO_ROOT / "tools/authoring-guide/authoring-guide.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL: Final = load_tool()


@pytest.mark.parametrize("args", [[], ["odt"], ["docx", "pptx"]])
def test_the_tool_stops_with_exit_code_2_on_wrong_arguments(
    args: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert TOOL.main(args) == 2
    assert "usage" in capsys.readouterr().err


@pytest.mark.parametrize("format", ["docx", "pptx", "pdf"])
def test_the_tool_prints_the_guide_once_the_generator_offers_one(
    format: str, capsys: pytest.CaptureFixture[str]
) -> None:
    module_name, class_name = TOOL.GENERATORS[format]
    try:
        offers = hasattr(
            getattr(importlib.import_module(module_name), class_name), "authoring_guide"
        )
    except ImportError:
        offers = False
    code = TOOL.main([format.upper()])
    captured = capsys.readouterr()
    if offers:
        assert code == 0 and captured.out.startswith("## ")
    else:
        assert code == 1 and captured.out == "" and captured.err.strip()


def test_the_tool_prints_what_the_generator_returns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Offering:
        def authoring_guide(self) -> str:
            return "## Guide für Schreiber\n"

    module = ModuleType("fake_generator")
    module.Fake = Offering  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "fake_generator", module)
    monkeypatch.setitem(TOOL.GENERATORS, "docx", ("fake_generator", "Fake"))
    assert TOOL.main(["docx"]) == 0
    assert capsys.readouterr().out == "## Guide für Schreiber\n"
