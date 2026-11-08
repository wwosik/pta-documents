"""E17-S02 in PowerPoint: typography and coloured code blocks."""

from __future__ import annotations

import io
import zipfile

from lxml import etree

from pta_documents.conversions.options import ConversionOptions
from pta_documents.conversions.pptx import PptxConverter
from pta_documents.design import colors
from pta_documents.generation.common.result import NoteCodes
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import MarkdownDocument
from pta_documents.markdown.typography import NBSP
from tests.generation.pptx.conftest import generate

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"a": A}
PYTHON = '```python\ndef answer():\n    return 42  # "so"\n```\n'


def slide(data: bytes, number: int) -> etree._Element:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return etree.fromstring(z.read(f"ppt/slides/slide{number}.xml"))


def code_looks(root: etree._Element) -> list[tuple[str, str | None, bool, bool]]:
    runs = root.xpath("//a:r[a:rPr/a:latin/@typeface='Consolas']", namespaces=NS)
    assert isinstance(runs, list)
    result: list[tuple[str, str | None, bool, bool]] = []
    for run in runs:
        assert isinstance(run, etree._Element)
        r_pr = run.find(f"{{{A}}}rPr")
        assert r_pr is not None
        color = r_pr.find(f"{{{A}}}solidFill/{{{A}}}srgbClr")
        result.append(
            (
                "".join(t.text or "" for t in run.iter(f"{{{A}}}t")),
                color.get("val") if color is not None else None,
                r_pr.get("b") == "1",
                r_pr.get("i") == "1",
            )
        )
    return result


def paragraph_texts(root: etree._Element) -> list[str]:
    return ["".join(t.text or "" for t in p.iter(f"{{{A}}}t")) for p in root.iter(f"{{{A}}}p")]


def test_text_is_typeset_and_code_stays_as_written() -> None:
    data = generate('# Deck\n\n## Folie\n\n"Zitat" - z. B. 10 % und `"code"`\n')
    assert f'„Zitat“ – z.{NBSP}B. 10{NBSP}% und "code"' in paragraph_texts(slide(data, 2))


def test_typography_can_be_turned_off() -> None:
    data = generate('---\ntypografie: nein\n---\n# Deck\n\n## Folie\n\n"Zitat" - z. B.\n')
    assert '"Zitat" - z. B.' in paragraph_texts(slide(data, 2))


def test_a_python_block_is_in_the_pta_colours() -> None:
    looks = code_looks(slide(generate("# Deck\n\n## Code\n\n" + PYTHON), 2))
    assert ("def ", colors.PTA_BLUE, True, False) in looks
    assert ("42  ", colors.TEXT_SLIDES, False, False) in looks
    assert ('# "so"', colors.GREY_DARK, False, True) in looks
    assert ("answer():", colors.TEXT_SLIDES, False, False) in looks


def test_on_a_flow_slide_too() -> None:
    markdown = '# Deck\n\n## Flow {kicker="Code"}\n\nText davor.\n\n' + PYTHON
    looks = code_looks(slide(generate(markdown), 2))
    assert ("def ", colors.PTA_BLUE, True, False) in looks


def test_without_language_in_one_colour() -> None:
    looks = code_looks(slide(generate("# Deck\n\n## Code\n\n```\ndef answer(): pass\n```\n"), 2))
    assert looks == [("def answer(): pass", colors.TEXT_SLIDES, False, False)]


def test_an_unknown_language_is_noted_and_highlighting_can_be_turned_off() -> None:
    output = io.BytesIO()
    markdown = "# Deck\n\n## Code\n\n```klingonisch\nx\n```\n"
    result = PptxGenerator().generate(MarkdownDocument(markdown), output)
    assert result.codes() == [NoteCodes.CODE_LANGUAGE_UNKNOWN]
    off = generate("---\nsyntaxhervorhebung: nein\n---\n# Deck\n\n## Code\n\n" + PYTHON)
    assert all(color == colors.TEXT_SLIDES for _, color, _, _ in code_looks(slide(off, 2)))


def test_a_split_code_block_keeps_its_colours() -> None:
    code = "\n".join(f"x{n} = {n}  # line" for n in range(60))
    data = generate(f"# Deck\n\n## Code\n\n```python\n{code}\n```\n")
    looks = code_looks(slide(data, 3))
    assert ("# line", colors.GREY_DARK, False, True) in looks


def test_plain_quotes_bring_the_written_text_back() -> None:
    data = generate('# Deck\n\n## Folie\n\n"Zitat" - z. B. 10 %\n')
    plain = PptxConverter().convert(data, ConversionOptions(plain_quotes=True)).text
    assert '"Zitat" - z. B. 10 %' in plain
