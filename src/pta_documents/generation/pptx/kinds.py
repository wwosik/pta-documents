"""Writes the PTA slide kinds (agenda, interim conclusion, quote, contact) and chart slides onto
their PTA layouts (E04-S04)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from lxml import etree
from pptx.slide import Slide as PptxSlide

from pta_documents.design import slides as design
from pta_documents.generation.pptx import chart, fitting
from pta_documents.generation.pptx.model import (
    AgendaSlide,
    ChartSlide,
    ContactSlide,
    InterimSlide,
    Kind,
    Paragraph,
    QuoteSlide,
    Run,
    Slide,
)

if TYPE_CHECKING:
    from pta_documents.generation.pptx.writer import DeckWriter

A: Final = "http://schemas.openxmlformats.org/drawingml/2006/main"
PH: Final = design.PLACEHOLDERS


def _a(name: str) -> str:
    return f"{{{A}}}{name}"


def write_agenda(deck: DeckWriter, slide: AgendaSlide) -> None:
    """Numbers 01 … and items in their placeholders; unused pairs and the rules under the last
    item are left out."""
    target = deck.new_slide(slide.layout, slide)
    deck.set_title(target, slide.title)
    for n, item in enumerate(slide.items):
        deck.set_text(target, PH.agenda_numbers[n], f"{n + 1:02d}")
        _line(deck, target, PH.agenda_texts[n], item)
    unused_rules = set(PH.agenda_rules[max(len(slide.items) - 1, 0) :])
    for shape in list(target.placeholders):
        if shape.placeholder_format.idx in unused_rules:
            _remove(shape)
    deck.finish(target, footer=True)


def write_interim(deck: DeckWriter, slide: InterimSlide) -> None:
    target = deck.new_slide(slide.layout, slide)
    deck.set_title(target, slide.title)
    deck.finish(target, footer=True)


def write_quote(deck: DeckWriter, slide: QuoteSlide) -> None:
    """The quote in the title placeholder; its source a second paragraph there, 24 pt Segoe UI
    Light, not italic (decision 2026-11-07)."""
    target = deck.new_slide(slide.layout, slide)
    deck.set_title(target, slide.title)
    title: Any = target.shapes.title
    if slide.source and title is not None:
        body = title._element.txBody
        source = deck.paragraph_element(target, Paragraph(slide.source, Kind.SUBHEADLINE))
        size = str(round(design.QUOTE_SOURCE_PT * 100))
        for r_pr in source.iter(_a("rPr"), _a("endParaRPr")):
            r_pr.set("sz", size)
            r_pr.set("i", "0")
            if r_pr.tag == _a("rPr") and r_pr.find(_a("latin")) is None:
                latin = etree.Element(_a("latin"))
                latin.set("typeface", design.QUOTE_SOURCE_FONT)
                # a:latin comes after the fill and highlight, before hlinkClick.
                link = r_pr.find(_a("hlinkClick"))
                if link is not None:
                    link.addprevious(latin)
                else:
                    r_pr.append(latin)
        body.append(source)
    deck.finish(target, footer=True)


def write_contact(deck: DeckWriter, slide: ContactSlide) -> None:
    """Per person photo, name, function, e-mail and phone in their placeholders; what a person
    lacks (a photo too) is left out, not shown as an empty placeholder."""
    target = deck.new_slide(slide.layout, slide)
    deck.set_title(target, slide.title)
    for person, (photo, name, function, email, phone) in zip(
        slide.persons, PH.contacts, strict=False
    ):
        _line(deck, target, name, person.name)
        for idx, runs in (
            (function, person.function),
            (email, person.email),
            (phone, person.phone),
        ):
            if runs:
                _line(deck, target, idx, runs)
        if person.photo is not None:
            deck.fill_picture(target, photo, person.photo, slide, alone_hint=False)
    if slide.text:
        _text(deck, target, PH.contact_text, list(slide.text), slide)
    deck.finish(target, footer=True)


def chart_layout(slide: ChartSlide) -> str:
    if len(slide.charts) == 2:
        return design.LAYOUTS.two_charts
    if slide.text:
        return design.LAYOUTS.text_and_chart if slide.text_first else design.LAYOUTS.chart_and_text
    return design.LAYOUTS.chart


def write_chart_slide(deck: DeckWriter, slide: ChartSlide) -> None:
    """The charts in the chart placeholders; title, unit and source of each in the placeholders
    above and below it (left out when empty), not in the chart itself."""
    target = deck.new_slide(chart_layout(slide), slide)
    deck.set_title(target, slide.title)
    first = (PH.chart_title, PH.chart_unit, PH.chart_source, PH.chart)
    for item, (title, unit, source, idx) in zip(
        slide.charts, (first, PH.second_chart), strict=False
    ):
        spec = item.graphic.chart
        with deck.at(target, item.click):
            for ph, value in ((title, spec.title), (unit, spec.unit), (source, spec.source)):
                if value:
                    deck.set_text(target, ph, value)
            chart.insert_chart(deck.placeholder(target, idx), spec, show_title=False)
    if slide.text:
        _text(deck, target, PH.chart_text, list(slide.text), slide)
    deck.finish(target, footer=True)


def _line(deck: DeckWriter, target: PptxSlide, idx: int, runs: tuple[Run, ...]) -> None:
    deck.set_paragraphs(target, idx, [Paragraph(runs, Kind.SUBHEADLINE)])


def _text(
    deck: DeckWriter, target: PptxSlide, idx: int, paragraphs: list[Paragraph], slide: Slide
) -> None:
    """Text in a body placeholder, shrunk to fit it (noted when it does not even then)."""
    shape = deck.placeholder(target, idx)
    scale = fitting.text_scale(deck.body_style, paragraphs, int(shape.width), int(shape.height))
    if scale is None:
        deck.note_overfull(slide)
    deck.set_paragraphs(target, idx, paragraphs, scale or deck.body_style.scales()[-1])


def _remove(shape: Any) -> None:
    element = shape._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)
