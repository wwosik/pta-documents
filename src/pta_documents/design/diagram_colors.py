"""The colours of Mermaid diagrams (E06-S03): mermaid's theme variables in the PTA colours.

mermaid-cli draws with its ``base`` theme; these variables set every colour the supported
diagram types use. Each value is a colour of ``design.colors`` or a tint of one (decision
2026-11-07); the text colour depends on the format (Word ``TEXT_WORD``, slides
``TEXT_SLIDES``). Diagrams stand on white.
"""

from __future__ import annotations

from typing import Final

from pta_documents.design import colors

FONT_FAMILY: Final = "Segoe UI, Selawik, sans-serif"
"""The diagram font as mermaid measures it: Segoe UI, else its metric stand-in Selawik."""
FONT_SIZE: Final = "16px"

SCALE: Final = (
    colors.PTA_BLUE,
    colors.DARK_BLUE,
    colors.LIGHT_BLUE,
    colors.GREY_DARK,
    colors.GREY_MID,
    colors.GREY_LIGHT,
)
"""The colours of mindmap branches and pie slices, in the accent order of the themes."""
DARK: Final = frozenset({colors.PTA_BLUE, colors.DARK_BLUE, colors.GREY_DARK})
"""Colours that take white text."""


def _hex(color: str) -> str:
    return "#" + color


def theme_variables(text: str) -> dict[str, str]:
    """mermaid's ``themeVariables`` for the ``base`` theme with ``text`` as text colour."""
    line = colors.GREY_DARK
    area = colors.GREY_LIGHT
    border = colors.PTA_BLUE
    values: dict[str, str] = {
        "background": colors.WHITE,
        "primaryColor": area,
        "primaryTextColor": text,
        "primaryBorderColor": border,
        "secondaryColor": colors.tint(colors.LIGHT_BLUE, 0.3),
        "secondaryTextColor": text,
        "secondaryBorderColor": border,
        "tertiaryColor": colors.WHITE,
        "tertiaryTextColor": text,
        "tertiaryBorderColor": colors.GREY_MID,
        "mainBkg": area,
        "nodeBorder": border,
        "nodeTextColor": text,
        "lineColor": line,
        "textColor": text,
        "titleColor": text,
        "edgeLabelBackground": colors.WHITE,
        "clusterBkg": colors.tint(area, 0.4),
        "clusterBorder": colors.GREY_MID,
        "noteBkgColor": colors.tint(colors.LIGHT_BLUE, 0.3),
        "noteBorderColor": colors.LIGHT_BLUE,
        "noteTextColor": text,
        "actorBkg": area,
        "actorBorder": border,
        "actorTextColor": text,
        "actorLineColor": line,
        "signalColor": text,
        "signalTextColor": text,
        "labelBoxBkgColor": area,
        "labelBoxBorderColor": border,
        "labelTextColor": text,
        "loopTextColor": text,
        "activationBkgColor": colors.tint(colors.LIGHT_BLUE, 0.3),
        "activationBorderColor": border,
        "sequenceNumberColor": colors.WHITE,
        "sectionBkgColor": colors.tint(area, 0.5),
        "altSectionBkgColor": colors.WHITE,
        "sectionBkgColor2": colors.tint(area, 0.5),
        "gridColor": colors.GREY_MID,
        "taskBkgColor": border,
        "taskBorderColor": colors.DARK_BLUE,
        "taskTextColor": colors.WHITE,
        "taskTextLightColor": colors.WHITE,
        "taskTextDarkColor": text,
        "taskTextOutsideColor": text,
        "taskTextClickableColor": text,
        "activeTaskBkgColor": colors.LIGHT_BLUE,
        "activeTaskBorderColor": border,
        "doneTaskBkgColor": colors.GREY_MID,
        "doneTaskBorderColor": colors.GREY_DARK,
        "critBkgColor": colors.DARK_BLUE,
        "critBorderColor": colors.SIGNAL_RED,
        "todayLineColor": colors.SIGNAL_RED,
        "pieTitleTextColor": text,
        "pieSectionTextColor": colors.WHITE,
        "pieLegendTextColor": text,
        "pieStrokeColor": colors.WHITE,
        "pieOuterStrokeColor": colors.WHITE,
        "attributeBackgroundColorOdd": colors.WHITE,
        "attributeBackgroundColorEven": colors.tint(area, 0.5),
    }
    for i in range(12):
        color = SCALE[i % len(SCALE)]
        values[f"pie{i + 1}"] = color
        values[f"cScale{i}"] = color
        values[f"cScaleInv{i}"] = color
        values[f"cScaleLabel{i}"] = colors.WHITE if color in DARK else text
    themed = {name: _hex(value) for name, value in values.items()}
    themed["fontFamily"] = FONT_FAMILY
    themed["fontSize"] = FONT_SIZE
    themed["pieOpacity"] = "1"
    return themed


def theme_css(text: str) -> str:
    """CSS mermaid appends to its own (``themeCSS``) for what its theme variables do not
    reach: the gantt grid lines (``currentColor``, else black) and the filled arrowheads of
    sequence diagrams (black; the id is the one mermaid-cli gives its SVG). Attribute
    selectors break mermaid's init directive."""
    return (
        f".grid .tick line{{stroke:{_hex(colors.GREY_MID)};}}"
        f"#my-svg-filled-head path{{fill:{_hex(text)};stroke:none;}}"
    )
