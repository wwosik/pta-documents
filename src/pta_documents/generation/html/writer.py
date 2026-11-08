"""The page of an HTML deck: the slides of a written PPTX on a 1600 px stage, the runtime around.

One file, nothing loaded from elsewhere: the fonts (Selawik, Inconsolata; OFL) and images are
``data:`` URIs, the runtime (``runtime/deck.css``, ``runtime/deck.js``) is inline, and a content
security policy allows that one script (by its hash) and nothing else — no script of the
Markdown can run, and the deck fetches nothing.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from html import escape
from importlib import resources
from typing import Any, Final

from lxml import etree
from pptx.presentation import Presentation

from pta_documents.design import colors, fonts
from pta_documents.design import slides as design
from pta_documents.design.variants import GeneratedTexts
from pta_documents.generation.html import timing
from pta_documents.generation.html.ooxml import (
    THEME_RELATION,
    Element,
    Palette,
    Theme,
    Units,
    a,
    local,
    number,
    p,
)
from pta_documents.generation.html.shapes import (
    NO_PAINT,
    ImageStore,
    Layer,
    Paint,
    Scene,
    css_background,
    paint,
    render_tree,
)

FONT_FACES: Final = (
    ("Selawik", 300, "Selawik-Light.ttf"),
    ("Selawik", 400, "Selawik-Regular.ttf"),
    ("Selawik", 700, "Selawik-Bold.ttf"),
    ("Inconsolata", 400, "Inconsolata-Regular.ttf"),
    ("Inconsolata", 700, "Inconsolata-Bold.ttf"),
)
"""The OFL fonts shipped with ``design.fonts`` (licences next to them): Segoe UI and Consolas are
never embedded; where they are installed, the deck uses them."""


@dataclass(frozen=True)
class PageInfo:
    title: str
    language: str
    """``de`` or ``en``: ``<html lang>``."""
    texts: GeneratedTexts
    show_progress: bool
    show_chapters: bool


def runtime(name: str) -> str:
    return (resources.files("pta_documents.generation.html") / "runtime" / name).read_text(
        encoding="utf-8"
    )


def _font_faces() -> str:
    rules: list[str] = []
    for family, weight, name in FONT_FACES:
        data = base64.b64encode(fonts.read(name)).decode("ascii")
        rules.append(
            f"@font-face{{font-family:{family};font-weight:{weight};font-style:normal;"
            f"src:url(data:font/ttf;base64,{data}) format('truetype')}}"
        )
    return "\n".join(rules)


def _variables(height: float) -> str:
    """The colours of the page around the stage, from ``design.colors``."""
    values = {
        "--stage-h": f"{number(height)}px",
        "--accent": colors.PTA_BLUE,
        "--dark": colors.DARK_BLUE,
        "--grey": colors.GREY_DARK,
        "--light": colors.GREY_LIGHT,
        "--text": colors.TEXT_SLIDES,
        "--white": colors.WHITE,
        "--emphasis": colors.PTA_BLUE,
    }
    declarations = ";".join(
        f"{name}:{value if value.endswith('px') else '#' + value.lower()}"
        for name, value in values.items()
    )
    return (
        f":root{{{declarations}}}\n@media print{{@page{{size:1600px {number(height)}px;margin:0}}}}"
    )


class HtmlDeckWriter:
    def __init__(self, presentation: Presentation, info: PageInfo) -> None:
        self.presentation = presentation
        self.info = info
        width = int(presentation.slide_width or 12192000)
        self.units = Units.of(width)
        self.height = self.units.px(int(presentation.slide_height or 6858000))
        self.images = ImageStore()
        self.serial = [0]
        defaults = presentation.part._element.find(p("defaultTextStyle"))
        self.defaults: Element | None = defaults

    def write(self) -> str:
        sections: list[str] = []
        chapters: list[str] = []
        chapter = -1
        slides = list(self.presentation.slides)
        # The backup (E16-S04) lies behind the closing slide: no chapter, the progress full.
        backup = design.backup_start([(s.slide_layout.name, s.name) for s in slides])
        main = len(slides) if backup is None else backup
        for number_, slide in enumerate(slides, start=1):
            layout = slide.slide_layout
            title = _title(slide)
            if number_ > main:
                chapter = -1
            elif layout.name == design.LAYOUTS.chapter:
                chapters.append(title)
                chapter = len(chapters) - 1
            sections.append(self.slide(slide, number_, len(slides), title, chapter))
        script = "\n" + runtime("deck.js")
        digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
        policy = (
            "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; "
            f"script-src 'sha256-{digest}'; base-uri 'none'; form-action 'none'"
        )
        texts = self.info.texts
        config: dict[str, str | int] = {
            "notesTitle": texts.notes_title,
            "slideAnnouncement": texts.slide_announcement,
        }
        if main < len(slides):
            config["mainSlides"] = main
        chapter_bar = (
            '<nav id="chapters" aria-hidden="true">'
            + "".join(
                f'<span data-c="{i}">{escape(name)}</span>' for i, name in enumerate(chapters)
            )
            + "</nav>"
            if self.info.show_chapters and chapters
            else ""
        )
        progress = '<div id="progress"><span></span></div>' if self.info.show_progress else ""
        return (
            "<!DOCTYPE html>\n"
            f'<html lang="{self.info.language}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n'
            '<meta name="generator" content="pta-documents">\n'
            f"<title>{escape(self.info.title)}</title>\n"
            f"<style>\n{_font_faces()}\n</style>\n"
            f"<style>\n{_variables(self.height)}\n{runtime('deck.css')}</style>\n"
            f"<style>\n{self.images.css()}</style>\n"
            "</head>\n"
            f'<body data-config="{escape(json.dumps(config, ensure_ascii=False))}">\n'
            f"{chapter_bar}\n"
            '<main id="deck">\n' + "\n".join(sections) + "\n</main>\n"
            f"{progress}\n"
            f'<div id="hint" aria-hidden="true">{escape(texts.key_hint)}</div>\n'
            '<aside id="notes" aria-hidden="true"></aside>\n'
            '<div id="live" class="sr-only" aria-live="polite"></div>\n'
            f"<script>{script}</script>\n"
            "</body>\n</html>\n"
        )

    def slide(self, slide: Any, number_: int, count: int, title: str, chapter: int) -> str:
        layout = slide.slide_layout
        master = layout.slide_master
        theme_part = master.part.part_related_by(THEME_RELATION)
        theme = Theme.read(etree.fromstring(theme_part.blob))
        palette = Palette.of(theme, master._element, layout._element, slide._element)
        scene = Scene(
            self.units,
            palette,
            self.images,
            Layer(master.part, master._element),
            Layer(layout.part, layout._element),
            Layer(slide.part, slide._element),
            self.defaults,
            self.info.language,
            layout.name,
            timing.builds(slide._element),
            self.serial,
        )
        background, background_class = self.background(scene)
        layers: list[str] = []
        shows_master = slide._element.get("showMasterSp") not in ("0", "false")
        if shows_master and layout._element.get("showMasterSp") not in ("0", "false"):
            layers.append(_tree(scene.master, scene))
        if shows_master:
            layers.append(_tree(scene.layout, scene))
        layers.append(_tree(scene.slide, scene))
        attributes = [
            'class="slide"',
            f'id="s{number_}"',
            f'data-layout="{escape(layout.name)}"',
            f'data-steps="{scene.builds.steps}"',
        ]
        if chapter >= 0:
            attributes.append(f'data-chapter="{chapter}"')
        transition = timing.transition(slide._element)
        if transition:
            attributes.append(f'data-transition="{transition}"')
        label = self.info.texts.slide_announcement.replace("{0}", str(number_)).replace(
            "{1}", str(count)
        )
        attributes.append(f'aria-label="{escape(label + (": " + title if title else ""))}"')
        attributes.append('role="group"')
        attributes.append('aria-roledescription="slide"')
        style = f' style="{background}"' if background else ""
        bg_class = f" {background_class}" if background_class else ""
        return (
            f"<section {' '.join(attributes)}>"
            f'<div class="bg{bg_class}"{style}></div>'
            + "".join(layers)
            + _notes(slide)
            + "</section>"
        )

    def background(self, scene: Scene) -> tuple[str, str]:
        for layer in (scene.slide, scene.layout, scene.master):
            bg = layer.element.find(f"{p('cSld')}/{p('bg')}")
            if bg is None:
                continue
            fill: Paint | None = None
            bg_pr = bg.find(p("bgPr"))
            if bg_pr is not None:
                fill = paint(bg_pr, scene)
            reference = bg.find(p("bgRef"))
            if reference is not None:
                color = scene.palette.color(reference)
                fill = Paint("solid", color) if color is not None else NO_PAINT
            if fill is None:
                continue
            css = css_background(fill, scene, layer)
            if css.startswith("--bg:"):
                return "", css[len("--bg:") :]
            return css, ""
        white = scene.palette.color_named("bg1")
        return (f"background:{white.css()}" if white else ""), ""


def _tree(layer: Layer, scene: Scene) -> str:
    tree = layer.tree
    return render_tree(tree, layer, scene) if tree is not None else ""


def _title(slide: Any) -> str:
    for shape in slide.placeholders:
        ph = shape._element.find(f"*/{p('nvPr')}/{p('ph')}")
        if ph is not None and ph.get("type") in ("title", "ctrTitle"):
            return " ".join(
                "".join(t.text or "" for t in paragraph.iter(a("t")))
                for paragraph in shape._element.iter(a("p"))
            ).strip()
    return ""


def _notes(slide: Any) -> str:
    """The speaker notes as plain HTML (hidden; the notes panel shows them)."""
    if not slide.has_notes_slide:
        return ""
    frame: Any = slide.notes_slide.notes_text_frame
    if frame is None:
        return ""
    paragraphs: list[str] = []
    for paragraph in frame._txBody.iterfind(a("p")):
        p_pr = paragraph.find(a("pPr"))
        level = int(p_pr.get("lvl", "0")) if p_pr is not None else 0
        runs: list[str] = []
        code = False
        for run in paragraph:
            if local(run) == "br":
                runs.append("<br>")
                continue
            if local(run) != "r":
                continue
            text = escape("".join(t.text or "" for t in run.iter(a("t"))))
            r_pr = run.find(a("rPr"))
            latin = r_pr.find(a("latin")) if r_pr is not None else None
            mono = latin is not None and latin.get("typeface", "").lower() == "consolas"
            if mono:
                text = f"<code>{text}</code>"
                code = True
            if r_pr is not None and r_pr.get("b") == "1":
                text = f"<strong>{text}</strong>"
            if r_pr is not None and r_pr.get("i") == "1":
                text = f"<em>{text}</em>"
            runs.append(text)
        content = "".join(runs)
        if not content.strip():
            continue
        css_class = ' class="code"' if code and len(runs) == 1 else ""
        indent = f' style="margin-left:{level * 1.2:g}em"' if level else ""
        paragraphs.append(f"<p{css_class}{indent}>{content}</p>")
    if not paragraphs:
        return ""
    return f'<aside class="notes" hidden>{"".join(paragraphs)}</aside>'
