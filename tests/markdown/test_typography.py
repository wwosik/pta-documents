"""E17-S02: German and English typography on the token stream."""

from __future__ import annotations

import pytest

from pta_documents.markdown.parser import parse
from pta_documents.markdown.typography import NBSP, plain, typeset, typeset_text


def typeset_markdown(markdown: str, language: str = "de") -> list[str]:
    """The text of each inline token after typesetting; code spans in backticks, other inline
    markup left out, non-breaking spaces as ``~``."""
    tokens = parse(markdown)
    typeset(tokens, language)
    result: list[str] = []
    for token in tokens:
        if token.type != "inline":
            continue
        parts: list[str] = []
        for child in token.children or []:
            if child.type == "text":
                parts.append(child.content)
            elif child.type == "code_inline":
                parts.append(f"`{child.content}`")
            elif child.type in ("softbreak", "hardbreak"):
                parts.append("\n")
        result.append("".join(parts).replace(NBSP, "~"))
    return result


def test_the_acceptance_example() -> None:
    assert typeset_markdown('"Zitat" - z. B. 10 %') == ["„Zitat“ – z.~B. 10~%"]


@pytest.mark.parametrize(
    ("written", "set"),
    [
        ('Er sagte "ja".', "Er sagte „ja“."),
        ("Ein 'halbes' Zitat", "Ein ‚halbes‘ Zitat"),
        ("geht's und gibt's", "geht’s und gibt’s"),
        ("Hans' Buch", "Hans’ Buch"),
        ('("Klammer")', "(„Klammer“)"),
        ("Von A -- B", "Von A – B"),
        ("Nur so - mehr nicht", "Nur so – mehr nicht"),
        ("Bindestrich-Wort und E-Mail", "Bindestrich-Wort und E-Mail"),
        ("Und dann...", "Und dann…"),
        ("d. h. und u. a. und i. d. R.", "d.~h. und u.~a. und i.~d.~R."),
        ("Nr. 3, S. 12, Abs. 2, § 5", "Nr.~3, S.~12, Abs.~2, §~5"),
        ("5 km, 3 Mio. Euro, 2 GB, 20 °C", "5~km, 3~Mio. Euro, 2~GB, 20~°C"),
        ("am 1. Januar und 24. Dez. 2026", "am 1.~Januar und 24.~Dez. 2026"),
        ("5 mal", "5 mal"),
        ("Plan B. Er geht.", "Plan B. Er geht."),
    ],
)
def test_german_rules(written: str, set: str) -> None:
    assert typeset_markdown(written) == [set]


def test_code_spans_and_blocks_stay_as_written() -> None:
    tokens = parse('Text `"a" - b...` und\n\n```\n"x" - 10 %\n```\n')
    typeset(tokens)
    assert tokens[-1].content == '"x" - 10 %\n'
    assert typeset_markdown('Text `"a" - b...` und') == ['Text `"a" - b...` und']


def test_quotes_look_across_inline_markup() -> None:
    assert typeset_markdown('"**fett**" und "`code`"') == ["„fett“ und „`code`“"]
    assert typeset_markdown("'*kursiv*'") == ["‚kursiv‘"]


def test_links_keep_their_target_but_set_their_text() -> None:
    tokens = parse('[Ein "Link"](https://example.com/"a") und <https://example.com/"b">')
    typeset(tokens)
    children = tokens[1].children or []
    assert children[0].attrs["href"] == "https://example.com/%22a%22"
    assert children[1].content == "Ein „Link“"
    autolink_text = [c.content for c in children if c.type == "text"][-1]
    assert autolink_text == 'https://example.com/"b"'


def test_heading_attributes_stay_as_written() -> None:
    assert typeset_markdown('## Das "Warum" {kicker="Warum"}') == ['Das „Warum“ {kicker="Warum"}']


def test_image_descriptions_are_set() -> None:
    tokens = parse('![Ein "Bild" - groß](bild.png "Der Titel...")')
    typeset(tokens)
    image = (tokens[1].children or [])[0]
    assert image.content == "Ein „Bild“ – groß"
    assert image.attrs["title"] == "Der Titel…"


def test_english() -> None:
    assert typeset_markdown('"Quote" - it\'s 10 % e.g. z. B.', "en") == [
        "“Quote” – it’s 10~% e.g. z. B."
    ]
    assert typeset_markdown("A 'single' one", "en") == ["A ‘single’ one"]


def test_a_text_on_its_own() -> None:
    assert typeset_text("Nr. 3 - fertig") == f"Nr.{NBSP}3 – fertig"


def test_plain_undoes_the_typography_outside_code() -> None:
    markdown = f"„Zitat“ – z.{NBSP}B. 10{NBSP}% ‚so‘ geht’s…\n\n`„x“`\n\n```\n„y“ –\n```\n"
    assert plain(markdown) == "\"Zitat\" - z. B. 10 % 'so' geht's...\n\n`„x“`\n\n```\n„y“ –\n```\n"
