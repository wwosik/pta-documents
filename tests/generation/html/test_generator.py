"""E10-S01: the HTML deck — the slides of the PPTX generator in one self-contained HTML file."""

from __future__ import annotations

import base64
import hashlib
import html
import io
import re
from pathlib import Path
from typing import Final

import pytest

from pta_documents.design.slides import TITLE_SLIDES
from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.html import generator as html_generator
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions
from pta_documents.generation.html.writer import runtime
from pta_documents.generation.pptx import generator as pptx_generator
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of
from tests.diagrams.support import drawable
from tests.expected import assert_matches_expected
from tests.generation.html.conftest import PLAIN, generate, review, slide_labels
from tests.generation.pptx.conftest import generate as pptx_generate
from tests.generation.pptx.conftest import open_pptx

SAMPLES: Final = Path(__file__).parent / "samples"
PPTX_SAMPLES: Final = Path(__file__).parents[1] / "pptx" / "samples"
DIAGRAM: Final = DocumentResource(
    "diagram.png", "image/png", (PPTX_SAMPLES / "diagram.png").read_bytes()
)
DECK_MD: Final = (PPTX_SAMPLES / "deck.md").read_text(encoding="utf-8")


def pptx_titles(markdown: str, resources: tuple[DocumentResource, ...] = ()) -> list[str]:
    data = pptx_generate(markdown, PptxOptions(code_block_renderers=()), resources)
    titles: list[str] = []
    for slide in open_pptx(data).slides:
        title = slide.shapes.title
        text = " ".join(p.text for p in title.text_frame.paragraphs) if title is not None else ""
        titles.append(text.strip())
    return titles


def html_titles(page: str) -> list[str]:
    result: list[str] = []
    for label in slide_labels(page):
        text = html.unescape(label)
        result.append(text.split(": ", 1)[1] if ": " in text else "")
    return result


def test_the_deck_has_the_slides_and_titles_of_the_pptx() -> None:
    page = generate(DECK_MD, resources=(DIAGRAM,))
    review("deck.html", page)
    assert html_titles(page) == pptx_titles(DECK_MD, (DIAGRAM,))


def test_the_slide_count_is_the_one_of_the_pptx() -> None:
    output = io.BytesIO()
    result = HtmlDeckGenerator().generate(MarkdownDocument(DECK_MD, (DIAGRAM,)), output, PLAIN)
    assert result.slides == len(slide_labels(output.getvalue().decode("utf-8")))
    assert result.slides == len(pptx_titles(DECK_MD, (DIAGRAM,)))


def test_a_long_slide_is_split_where_the_pptx_splits_it() -> None:
    markdown = "# Deck\n\n## Many points\n\n" + "".join(
        f"- Point {n}: a line of text that takes some room on the slide\n" for n in range(40)
    )
    titles = html_titles(generate(markdown))
    assert titles == pptx_titles(markdown)
    assert len(titles) > 2


def normalized(page: str) -> str:
    """The page without the parts that are not the deck: fonts and runtime are replaced by their
    names, every ``data:`` URI by the hash of its content."""
    page = re.sub(r"<style>\n@font-face.*?</style>", "<style>/* fonts */</style>", page, flags=re.S)
    page = page.replace(runtime("deck.css"), "/* deck.css */\n")
    page = page.replace(runtime("deck.js"), "/* deck.js */\n")
    page = re.sub(r"'sha256-[^']*'", "'sha256-…'", page)

    def short(match: re.Match[str]) -> str:
        digest = hashlib.sha256(match.group(2).encode("ascii")).hexdigest()[:12]
        return f"data:{match.group(1)};sha256={digest}"

    return re.sub(r"data:([a-z/+.-]+);base64,([A-Za-z0-9+/=]+)", short, page)


def test_the_deck_matches_its_snapshot() -> None:
    page = generate(DECK_MD, resources=(DIAGRAM,))
    assert_matches_expected(SAMPLES / "deck.expected.html", normalized(page))


def test_the_only_script_is_the_runtime_and_the_policy_allows_only_it() -> None:
    page = generate(DECK_MD, resources=(DIAGRAM,))
    assert page.count("<script") == 1
    script = "\n" + runtime("deck.js")
    digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
    assert f"<script>{script}</script>" in page
    assert f"script-src 'sha256-{digest}'" in page
    assert "default-src 'none'" in page


def test_raw_html_and_script_from_the_markdown_never_reach_the_page() -> None:
    markdown = (
        "# Deck\n\n## Text\n\n<script>alert(1)</script>\n\n"
        'Before <img src="x" onerror="alert(2)"> after and <b onclick="x()">bold</b>.\n\n'
        "[click](javascript:alert(3)) and [web](https://example.com)\n"
    )
    page = generate(markdown)
    assert page.count("<script") == 1
    assert "<script>alert" not in page and "&lt;script&gt;" not in page  # dropped as in PPTX
    assert "onerror" not in page and "onclick" not in page
    assert 'href="javascript' not in page  # markdown-it leaves the link as text
    assert 'href="https://example.com" target="_blank" rel="noopener noreferrer"' in page


def test_text_is_escaped() -> None:
    page = generate('# Deck\n\n## A <b> & `<i>`\n\nx < y && "z"\n')
    assert "A &lt;b&gt; &amp;" in page or "A  &amp;" in page
    assert "x &lt; y &amp;&amp;" in page


def test_the_file_is_self_contained_utf8_without_bom_and_small() -> None:
    output = io.BytesIO()
    HtmlDeckGenerator().generate(MarkdownDocument(DECK_MD, (DIAGRAM,)), output, PLAIN)
    data = output.getvalue()
    assert not data.startswith(b"\xef\xbb\xbf")
    page = data.decode("utf-8")
    assert len(data) < 5 * 1024 * 1024
    assert not re.search(r"""(src|href)=["']?(?!https?://example\.com)(https?:|//)""", page)
    assert "url(http" not in page and "@import" not in page
    images = re.findall(r"url\(([^)]*)\)", page)
    assert images and all(i.startswith("data:") for i in images)


@pytest.mark.parametrize("name", sorted(TITLE_SLIDES))
def test_every_title_slide_renders(name: str) -> None:
    page = generate(f"---\ntitelfolie: {name}\n---\n# Deck\n\nSub\n\n## One\n\nText\n")
    review(f"titelfolie-{name}.html", page)
    first = page[page.index("<section") : page.index("</section>")]
    assert f'data-layout="{TITLE_SLIDES[name]}"' in first
    assert "Deck" in first
    if name != "ohne-bild":
        assert "data:image/" in first or re.search(r'class="im im\d+"', first)  # the photo


@pytest.mark.parametrize("front", ["vorlage: schulung", "sprache: en", "kennzeichnung: entwurf"])
def test_the_variants_render(front: str) -> None:
    page = generate(f"---\n{front}\n---\n# Deck\n\n## One\n\nText\n\n# Ende {{.closing}}\n")
    review(f"variante-{front.split(':')[0]}.html", page)
    assert len(slide_labels(page)) >= 2
    if front == "sprache: en":
        assert '<html lang="en">' in page and "Slide 1 of" in page


def test_the_logo_of_the_layouts_is_the_svg_logo() -> None:
    page = generate("# Deck\n\n## One\n\nText\n")
    assert "data:image/svg+xml" in page
    assert "image/x-emf" not in page


def test_images_are_data_uris() -> None:
    page = generate("# Deck\n\n## Picture\n\n![A diagram](diagram.png)\n", resources=(DIAGRAM,))
    picture = base64.b64encode(DIAGRAM.content).decode("ascii")
    assert f"url(data:image/png;base64,{picture})" in page
    assert 'aria-label="A diagram"' in page


def test_a_missing_image_is_the_error_of_the_pptx() -> None:
    markdown = "# Deck\n\n## Picture\n\n![Gone](gone.png)\n"
    with pytest.raises(DocumentConversionError) as pptx_error:
        pptx_generate(markdown)
    with pytest.raises(DocumentConversionError) as html_error:
        generate(markdown)
    assert html_error.value.format is DocumentFormat.HTML
    assert html_error.value.reason == pptx_error.value.reason


def test_errors_keep_their_lines_with_the_own_keys() -> None:
    body = '# Deck\n\n## One {layout="Nichts"}\n\nText\n'
    with pytest.raises(DocumentConversionError) as pptx_error:
        pptx_generate("---\ntitel: X\n\n---\n" + body)
    with pytest.raises(DocumentConversionError) as html_error:
        generate("---\ntitel: X\nfortschritt: nein\n---\n" + body)
    assert html_error.value.reason == pptx_error.value.reason


def test_front_matter_mistakes_are_reported_as_html() -> None:
    with pytest.raises(DocumentConversionError) as error:
        generate("---\nunbekannt: ja\n---\n# Deck\n")
    assert error.value.format is DocumentFormat.HTML
    assert "fortschritt" in error.value.reason and "kapitelanzeige" in error.value.reason
    with pytest.raises(DocumentConversionError) as error:
        generate("---\ntitelfolie: foto\n---\n# Deck\n")
    assert "bild-01" in error.value.reason


def test_the_valid_keys_are_those_of_the_pptx_and_two_more() -> None:
    assert (
        *pptx_generator.VALID_KEYS,
        "fortschritt",
        "kapitelanzeige",
    ) == html_generator.VALID_KEYS


def test_progress_and_chapters_can_be_turned_off() -> None:
    markdown = "# Deck\n\n# Kapitel\n\n## One\n\nText\n"
    page = generate(markdown)
    assert '<div id="progress">' in page
    assert '<nav id="chapters"' in page and '<span data-c="0">Kapitel</span>' in page
    page = generate("---\nfortschritt: nein\nkapitelanzeige: nein\n---\n" + markdown)
    assert '<div id="progress">' not in page and '<nav id="chapters"' not in page
    options = HtmlDeckOptions(code_block_renderers=(), show_progress=False)
    assert '<div id="progress">' not in generate(markdown, options)


def test_notes_builds_and_transitions_come_along() -> None:
    markdown = (
        "---\nuebergang: push-up\n---\n# Deck\n\n## Steps\n\n{.build}\n- one\n- two\n\n"
        "::: notes\nSay **this**.\n:::\n"
    )
    page = generate(markdown)
    review("builds.html", page)
    assert 'data-transition="push-up"' in page
    assert '<aside class="notes" hidden><p>Say <strong>this</strong>.</p></aside>' in page
    assert 'data-steps="2"' in page
    assert page.count('data-build="1"') == 1 and page.count('data-build="2"') == 1


def test_morph_is_named_for_the_runtime() -> None:
    page = generate("---\nuebergang: morph\n---\n# Deck\n\n## One\n\nText\n")
    assert 'data-transition="morph"' in page


def test_notes_of_the_generator_are_returned() -> None:
    output = io.BytesIO()
    result = HtmlDeckGenerator().generate(
        MarkdownDocument("# Deck\n\n## One\n\n<b>raw</b>\n"), output, PLAIN
    )
    assert any(note.code == "raw-html" for note in result.notes)


def test_the_slide_samples_generate_as_html_without_notes() -> None:
    """Every slide sample is an HTML deck with the slides of its PPTX (samples with Mermaid
    only where mermaid-cli works)."""
    root = Path(__file__).parents[3] / "samples"
    for folder in ("gsb", "funktionen"):
        images = tuple(
            DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
            for p in sorted((root / folder / "images").glob("*"))
        )
        sources = sorted((root / folder).glob("*-praesentation.md")) + sorted(
            (root / folder).glob("*-folien.md")
        )
        for source in sources:
            markdown = source.read_text(encoding="utf-8")
            if not drawable(markdown):
                continue
            output = io.BytesIO()
            result = HtmlDeckGenerator().generate(MarkdownDocument(markdown, images), output)
            assert result.notes == (), f"{source.name}:\n{result}"
            page = output.getvalue().decode("utf-8")
            assert len(slide_labels(page)) == result.slides
            review(f"html-{source.stem}.html", page)
