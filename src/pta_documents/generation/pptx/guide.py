"""The authoring guide of the PPTX generator (E04-S06; port of DocLibs
``PptxGenerator.AuthoringGuide`` and ``Pptx/AuthoringGuide/Pptx.md``).

The template ``authoring_guide/pptx.md`` holds the German prose; everything that is a list in
the code comes from there, filled in with the shared sections of
``generation.common.authoring_guides``: the front matter rows describe exactly ``VALID_KEYS``,
the layouts are read from the chosen template, the slide kinds, scenes, transitions and image
attributes from their modules, the diagrams from the renderers of the options. The HTML deck
(E10-S01) reads the same Markdown and follows this guide.
"""

from __future__ import annotations

import io
from collections.abc import Collection, Iterable
from typing import Final

import pptx

from pta_documents.design import slides as design
from pta_documents.design import templates
from pta_documents.design.variants import Marking, SlidesVariant
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import authoring_guides as guides
from pta_documents.generation.common import scene, scene_colors
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.authoring_guides import GuideKey, choices, names
from pta_documents.generation.common.image_attributes import NAMED_FOCUS
from pta_documents.generation.common.slide_transition import SlideTransition
from pta_documents.generation.pptx.options import PptxOptions
from pta_documents.markdown.front_matter import NO, Keys

PACKAGE: Final = "pta_documents.generation.pptx"
NAME: Final = "pptx"
FORMAT: Final = DocumentFormat.PPTX
NATIVE_IMAGES: Final = ("PNG", "JPEG")
"""The image formats a slide takes without a converter."""

EFFECT: Final = (
    "Auf Folien wird eine `##`-Folie mit Container, Alert, Chips, `.dark` oder `kicker` eine "
    "Flow-Folie auf „Nur Titel“: Karten im Raster (höchstens vier je Zeile), die Fazit-Box am "
    "Fuß der Folie, die Kommentarbox als Sprechblase am Block davor, Alerts als graue Fläche mit "
    "blauem oder gelbem Balken, `==…==` fett auf Gelb, Status-Labels mit Ampelpunkt. Was nicht "
    "passt, wird kleiner und dann geteilt; Karten, Flächen und Spalten werden nie geteilt."
)
"""How slides show the slide syntax (E04-S03, E04-S04)."""


def authoring_guide(options: PptxOptions, valid_keys: Collection[str]) -> str:
    """The guide for ``options``: template, marking, renderers and converters as chosen."""
    marking = options.marking or options.variant.default_marking
    values = {
        "variant": options.variant.value,
        "imageFormats": ", ".join(guides.image_formats(NATIVE_IMAGES, options.image_converters)),
        "focusValues": names(NAMED_FOCUS),
        "syntax": guides.layout_syntax_section(FORMAT, EFFECT),
        "agendaShort": str(design.AGENDA_SHORT_ITEMS),
        "agendaItems": str(design.AGENDA_ITEMS),
        "contactPersons": str(design.CONTACT_PERSONS),
        "kindLayouts": _quoted(dict.fromkeys(ls[1] for ls in design.KIND_LAYOUTS.values())),
        "sceneKinds": names((k.value for k in scene.ShapeKind), "und"),
        "sceneAttributes": names(_entries(scene.ATTRIBUTES), "und"),
        "sceneGrid": f"{scene.COLUMNS} × {scene.ROWS}",
        "sceneColors": names(_entries(scene_colors.VALID), "und"),
        "templateLayouts": _quoted(layout_names(options)),
        "icons": guides.icons_section(FORMAT),
        "typography": guides.typography_section(),
        "diagrams": guides.renderers_section(options.code_block_renderers),
        "frontMatter": guides.front_matter_section(
            front_matter_rows(options, marking), valid_keys, _example(options)
        ),
        "notes": guides.notes_section(FORMAT),
    }
    return guides.fill(guides.template(PACKAGE, NAME), values)


def layout_names(options: PptxOptions) -> list[str]:
    """The names of the layouts of the chosen template, in its order."""
    data = templates.slides_template(options.variant, options.language)
    return [layout.name for layout in pptx.Presentation(io.BytesIO(data)).slide_layouts]


def front_matter_rows(options: PptxOptions, marking: Marking) -> list[GuideKey]:
    """A row for every key of ``generator.VALID_KEYS``."""
    common = guides.common_keys(options.audience or Audience.KUNDE)
    markings = [
        m.value
        for m in Marking
        if not (m is Marking.NONE and options.variant is SlidesVariant.TRAINING)
    ]
    return [
        GuideKey(
            Keys.TEMPLATE,
            choices((v.value for v in SlidesVariant), options.variant.value),
            "Die PTA-Vorlage; `schulung` ist die Schulungsvorlage mit dem Sticker „intern“.",
        ),
        GuideKey(Keys.TITLE, "frei", "Der Titel; ohne `titel` der Text des ersten `#`."),
        GuideKey(Keys.SUBTITLE, "frei", "Der Untertitel der Titelfolie."),
        GuideKey(Keys.AUTHOR, "frei", "Autor auf der Titelfolie und in den Eigenschaften."),
        GuideKey(Keys.LOCATION, "frei", "Ort auf der Titelfolie, nach dem Autor."),
        common[Keys.DATE],
        common[Keys.LANGUAGE],
        common[Keys.TYPOGRAPHY],
        common[Keys.HIGHLIGHT],
        common[Keys.CHECK],
        GuideKey(
            Keys.FOOTER, "frei", "Die Fußzeile „PTA – …“; ohne Angabe der Titel der Präsentation."
        ),
        GuideKey(
            Keys.TITLE_SLIDE,
            choices(design.TITLE_SLIDES, options.title_slide),
            "Das Layout der Titelfolie.",
        ),
        GuideKey(
            Keys.MARKING,
            choices(markings, marking.value),
            "Der Sticker oben rechts auf allen Folien"
            + (
                "; die Schulungsvorlage braucht einen, `kein` ist dort ein Fehler."
                if options.variant is SlidesVariant.TRAINING
                else "."
            ),
        ),
        GuideKey(
            Keys.BUILD,
            choices((Keys.BUILD_LISTS, NO), Keys.BUILD_LISTS if options.build_lists else NO),
            "`listen`: jede Liste erscheint Punkt für Punkt, als stünde `{.build}` davor.",
        ),
        GuideKey(
            Keys.TRANSITION,
            choices((t.value for t in SlideTransition), options.transition.value),
            "Der Übergang aller Folien, außer wo ein `#` oder `##` einen eigenen hat.",
        ),
        common[Keys.AUDIENCE],
        GuideKey(
            Keys.BEGIN,
            "Uhrzeit `09:00`",
            "Beginn der Schulung: die Agenda zeigt Uhrzeiten.",
        ),
        GuideKey(
            Keys.LENGTH,
            "Minuten `240`, `4h` oder `3h30`",
            "Die geplante Länge, mit der Summe der `dauer` verglichen.",
        ),
    ]


def _example(options: PptxOptions) -> str:
    """The lines of the example block of the front matter section."""
    return "\n".join(
        (
            f"{Keys.TITLE}: Kundenportal 2.0",
            f"{Keys.TEMPLATE}: {options.variant.value}",
            f"{Keys.TITLE_SLIDE}: {next(iter(design.TITLE_SLIDES))}",
            f"{Keys.MARKING}: {Marking.CONFIDENTIAL.value}",
            f"{Keys.STATUS_PREFIX}success: Erledigt; Fertig",
        )
    )


def _entries(text: str) -> list[str]:
    return [entry.strip() for entry in text.split(",")]


def _quoted(values: Iterable[str]) -> str:
    return ", ".join(f"„{value}“" for value in values)
