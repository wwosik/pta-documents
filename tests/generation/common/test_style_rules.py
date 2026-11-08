"""E08-S02: the style rules of the PTA sample slides, each positive and negative."""

from __future__ import annotations

from pathlib import Path

import pytest

from pta_documents.errors import DocumentConversionError, DocumentFormat
from pta_documents.generation.common.style_rules import (
    StyleCodes,
    StyleLimits,
    ending_of,
    style_notes,
    words,
)
from pta_documents.markdown import MarkdownDocument

PPTX = DocumentFormat.PPTX
DOCX = DocumentFormat.DOCX


def codes(
    markdown: str,
    format: DocumentFormat = PPTX,
    sources: bool = False,
    skip: tuple[str, ...] = (),
    limits: StyleLimits | None = None,
) -> list[str]:
    notes = style_notes(
        MarkdownDocument(markdown), format, sources=sources, skip=skip, limits=limits
    )
    return [note.code for note in notes]


def deck(body: str) -> str:
    return f"# Deck\n\n## Folie\n\n{body}\n"


def points(n: int, text: str = "Punkt") -> str:
    return "\n".join(f"- {text} {i}" for i in range(1, n + 1))


def test_words_count_runs_with_letters_or_digits() -> None:
    assert words("Rund 500 km – durchgehend rot.") == 5
    assert words("  ") == 0


# ------------------------------------------------------------------ style-bullets


def test_seven_points_are_fine_eight_are_too_many() -> None:
    assert codes(deck(points(7))) == []
    notes = style_notes(MarkdownDocument(deck(points(8))), PPTX)
    assert [n.code for n in notes] == [StyleCodes.BULLETS]
    assert notes[0].line == 3
    assert "8 points" in notes[0].message


def test_sub_points_count_too() -> None:
    assert codes(deck(points(4) + "\n" + "\n".join(f"  - Unter {i}" for i in range(4)))) == [
        StyleCodes.BULLETS
    ]


def test_a_point_of_more_than_20_words_is_running_text() -> None:
    long = " ".join(["Wort"] * 21)
    notes = style_notes(MarkdownDocument(deck(f"- Kurz\n- {long}")), PPTX)
    assert [(n.code, n.line) for n in notes] == [(StyleCodes.BULLETS, 6)]
    assert codes(deck("- " + " ".join(["Wort"] * 20))) == []


def test_the_agenda_may_have_eight_points() -> None:
    assert codes("# Deck\n\n## Agenda {.agenda}\n\n" + points(8) + "\n") == []


def test_the_limits_are_adjustable() -> None:
    assert codes(deck(points(4)), limits=StyleLimits(bullets=3)) == [StyleCodes.BULLETS]


# ------------------------------------------------------------------ style-words


def test_more_than_80_words_on_a_slide() -> None:
    assert codes(deck(" ".join(["Wort"] * 80))) == []
    assert codes(deck(" ".join(["Wort"] * 81))) == [StyleCodes.WORDS]


def test_speaker_notes_and_code_blocks_do_not_count() -> None:
    notes = "::: notes\n" + " ".join(["Wort"] * 200) + "\n:::"
    code = "```python\n" + "x = 1\n" * 100 + "```"
    assert codes(deck(f"Kurz.\n\n{notes}\n\n{code}")) == []


# ------------------------------------------------------------------ style-punctuation


def test_mixed_punctuation_at_the_end_of_points() -> None:
    assert codes(deck("- Erster Punkt.\n- Zweiter Punkt")) == [StyleCodes.PUNCTUATION]
    assert codes(deck("- Erster Punkt\n- Zweiter Punkt")) == []
    assert codes(deck("- Erster Punkt.\n- Zweiter Punkt!")) == []


def test_an_enumeration_may_end_with_a_full_stop() -> None:
    assert codes(deck("- erstens;\n- zweitens;\n- drittens.")) == []


def test_a_point_introducing_sub_points_may_end_with_a_colon() -> None:
    assert codes(deck("- Mitnehmen:\n  - Karte\n  - Wasser\n- Losgehen")) == []


def test_a_closing_bracket_or_quote_is_no_full_stop() -> None:
    assert ending_of('Englisch, z. B. "(cont.)"') == ""
    assert ending_of("„Ein Satz.“") == "."
    assert ending_of("Und so weiter …") == ""


def test_punctuation_is_checked_in_word_too() -> None:
    assert codes("# Kapitel\n\n- Eins.\n- Zwei\n", DOCX) == [StyleCodes.PUNCTUATION]


# ------------------------------------------------------------------ style-title


def test_a_slide_title_of_more_than_60_characters() -> None:
    title = "T" * 61
    assert codes(f"# Deck\n\n## {title}\n\nText.\n") == [StyleCodes.TITLE]
    assert codes(f"# Deck\n\n## {'T' * 60}\n\nText.\n") == []


def test_a_slide_title_ending_with_a_full_stop() -> None:
    assert codes("# Deck\n\n## Wir sind fertig.\n\nText.\n") == [StyleCodes.TITLE]
    assert codes("# Deck\n\n## Und dann...\n\nText.\n") == []


def test_cover_quote_and_statement_titles_may_be_sentences() -> None:
    sentence = "Was man nicht messen kann, kann man nicht lenken, sagt man so gern."
    assert codes(f"# {sentence}\n\n## {sentence} {{.quote}}\n\n## {sentence} {{.interim}}\n") == []


# ------------------------------------------------------------------ style-image-source


def test_an_image_without_source_only_with_sources() -> None:
    markdown = deck("![Gipfel](images/gipfel.jpg)")
    assert codes(markdown) == []
    assert codes(markdown, sources=True) == [StyleCodes.IMAGE_SOURCE]


def test_the_source_may_be_on_the_slide_or_in_the_title() -> None:
    on_slide = deck("Foto: Jakub Hałun, CC BY-SA 4.0\n\n![Gipfel](images/gipfel.jpg)")
    in_title = deck('![Gipfel](images/gipfel.jpg "Der Gipfel (© PTA)")')
    assert codes(on_slide, sources=True) == []
    assert codes(in_title, sources=True) == []


def test_in_word_the_source_is_in_the_title_or_the_line_below() -> None:
    caption = '# Kapitel\n\n![Gipfel](images/gipfel.jpg "Gipfel (Foto: Yarl, CC BY-SA 3.0)")\n'
    below = "# Kapitel\n\n![Gipfel](images/gipfel.jpg)\n\nQuelle: eigene Aufnahme\n"
    missing = "# Kapitel\n\n![Gipfel](images/gipfel.jpg)\n\nEin Absatz.\n"
    assert codes(caption, DOCX, sources=True) == []
    assert codes(below, DOCX, sources=True) == []
    assert codes(missing, DOCX, sources=True) == [StyleCodes.IMAGE_SOURCE]


# ------------------------------------------------------------------ style-alt-text


def test_an_image_without_alt_text() -> None:
    notes = style_notes(MarkdownDocument(deck("![](images/gipfel.jpg)")), PPTX)
    assert [(n.code, n.line) for n in notes] == [(StyleCodes.ALT_TEXT, 5)]
    assert codes(deck("![Gipfel](images/gipfel.jpg)")) == []
    assert codes("# Kapitel\n\n![](images/gipfel.jpg)\n", DOCX) == [StyleCodes.ALT_TEXT]


# ------------------------------------------------------------------ style-heading-numbers


def test_a_heading_with_its_own_number_in_word() -> None:
    assert codes("# 1. Einleitung\n\nText.\n", DOCX) == [StyleCodes.HEADING_NUMBERS]
    assert codes("# Kapitel\n\n## 2.3 Ziele\n\nText.\n", DOCX) == [StyleCodes.HEADING_NUMBERS]
    assert codes("# 2026 in Zahlen\n\n#### 1. Zwischentitel\n\nText.\n", DOCX) == []


def test_slides_keep_their_numbers() -> None:
    assert codes("# Deck\n\n## 1. Schritt\n\nText.\n") == []


# ------------------------------------------------------------------ switching off


def test_rules_are_skipped_by_code() -> None:
    markdown = deck(points(8) + "\n- Letzter.")
    assert codes(markdown) == [StyleCodes.BULLETS, StyleCodes.PUNCTUATION]
    assert codes(markdown, skip=(StyleCodes.BULLETS,)) == [StyleCodes.PUNCTUATION]


def test_the_front_matter_switches_rules_off() -> None:
    body = deck(points(8) + "\n- Letzter.")
    assert codes("---\npruefung: aus\n---\n" + body) == []
    assert codes("---\npruefung: style-bullets\n---\n" + body) == [StyleCodes.PUNCTUATION]
    assert codes("---\npruefung: an\n---\n" + body) == [
        StyleCodes.BULLETS,
        StyleCodes.PUNCTUATION,
    ]


def test_an_unknown_code_is_an_error() -> None:
    with pytest.raises(DocumentConversionError, match="style-words"):
        codes("---\npruefung: style-wort\n---\n# Deck\n")
    with pytest.raises(DocumentConversionError, match="--skip"):
        codes("# Deck\n", skip=("words",))


def test_codes_are_unique_kebab_case() -> None:
    assert len(set(StyleCodes.ALL)) == len(StyleCodes.ALL)
    assert all(code.startswith("style-") for code in StyleCodes.ALL)


def test_every_code_is_described_in_the_usage_guide() -> None:
    guide = (Path(__file__).resolve().parents[3] / "docs" / "verwendung.md").read_text("utf-8")
    assert all(f"`{code}`" in guide for code in StyleCodes.ALL)
