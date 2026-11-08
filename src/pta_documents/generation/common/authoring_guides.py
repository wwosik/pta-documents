"""The parts the generators' authoring guides share (E02-S05; port of DocLibs
``AuthoringGuides.cs``).

An authoring guide is German Markdown that starts at ``##``, written for whoever writes the
document — people and AI agents. A generator fills its template
(``<package>/authoring_guide/<name>.md``, read with ``template``) with ``fill`` and the sections
here, which are built from the lists in the code, so that guide, checks and code cannot drift
apart: the front matter table from the generator's valid keys (``front_matter_section``), the slide
syntax from ``layout_syntax``, ``heading_attributes`` and ``block_markers``
(``layout_syntax_section``), the icons from ``design.icons``, the notes from ``NoteCodes``, the
renderers' own sections (``renderers_section``) and the characters the fonts lack
(``characters_section``, only the PDF needs it).

Whoever adds a container, alert, heading attribute, block marker or note code adds its text to
the tables below (``CONTAINER_TEXTS``, ``ALERT_TEXTS``, ``ATTRIBUTE_TEXTS``, ``MARKER_TEXTS``,
``NOTE_TEXTS``); the sections raise ``KeyError`` for a name without one, and the tests name it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from typing import Final

from pta_documents.design import icons
from pta_documents.design.colors import StatusCategory
from pta_documents.design.variants import Language
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common import heading_attributes, layout_syntax
from pta_documents.generation.common.audience import Audience
from pta_documents.generation.common.images import ImageConverter
from pta_documents.generation.common.renderers import CodeBlockRenderer
from pta_documents.generation.common.result import NoteCodes
from pta_documents.markdown import block_markers
from pta_documents.markdown.front_matter import NO, YES, Keys

FOLDER: Final = "authoring_guide"
"""The folder of a generator package that holds its guide templates."""

WORD_LIMIT: Final = 2500
"""The most words a guide may have (counted by ``words``)."""

_PLACEHOLDER: Final = re.compile(r"\{\{([A-Za-z]+)\}\}")
_BLANK_LINES: Final = re.compile(r"\n{3,}")
_WORD: Final = re.compile(r"[^\W_]+")

SYNTAX_PATTERN: Final = re.compile(
    r"::: [a-z]+|\[![A-Z]+\]|\{\.?[a-z]+(?==|\}| )|```(?:mermaid|chart|financial-chart)"
)
"""The syntax a guide names, as the samples have to show it (port of vt-tools-libs
``TourTests.SyntaxPattern``): containers, alerts, heading and marker attributes, status classes
and the languages of drawn blocks — ``::: cards``, ``[!NOTE]``, ``{.dark``, ``{kicker``,
````` ```chart `````."""

KEY_PATTERN: Final = re.compile(r"^\| `([a-z][a-z.<>]*)`", re.MULTILINE)
"""The keys of the front matter table of a guide."""

SYMBOLS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("✓", ("[x]",)),
    ("✔", ("[x]",)),
    ("✗", ("[ ]",)),
    ("✘", ("[ ]",)),
    ("☐", ("[ ]",)),
    ("☑", ("[x]",)),
    ("●", ("•", "*")),
    ("○", ("•", "*")),
    ("■", ("•", "*")),
    ("□", ("•", "*")),
    ("▪", ("•", "*")),
    ("◦", ("–", "-")),
    ("★", ("*",)),
    ("☆", ("*",)),
    ("→", ("->",)),
    ("←", ("<-",)),
    ("↔", ("<->",)),
    ("↑", ("hoch",)),
    ("↓", ("runter",)),
    ("▲", ("↑", "hoch")),
    ("▼", ("↓", "runter")),
    ("►", ("→", "->")),
    ("◄", ("←", "<-")),
    ("⇒", ("→", "->")),
    ("⇐", ("←", "<-")),
    ("⇔", ("↔", "<->")),
    ("≡", ("=",)),
    ("≠", ("!=",)),
    ("≈", ("~",)),
    ("‖", ("|",)),
    ("─", ("-",)),
    ("│", ("|",)),
)
"""Symbols writers reach for, each with replacements in order of preference; the last is ASCII
(or a German word), which every font has. ``characters_section`` names those the fonts lack."""

# ---------------------------------------------------------------------- texts of the syntax

CONTAINER_TEXTS: Final[Mapping[str, str]] = {
    layout_syntax.CARDS: (
        "Karten nebeneinander: je Karte `### Titel` und ein kurzer Text, oder eine Liste "
        "`- **Titel** – Text`; ein erster Absatz `**26 %**` ist die Kennzahl der Karte."
    ),
    layout_syntax.ROWS: "Zeilen aus einer Liste `- **Begriff** – Beschreibung`.",
    layout_syntax.PANEL: "Eine Fläche um den Inhalt; `::: panel dark` dunkel.",
    layout_syntax.STATEMENT: "Eine Aussage: der erste Absatz groß und fett, der Rest normal.",
    layout_syntax.COLUMNS: (
        "Spalten, getrennt durch `---` mit einer Leerzeile davor; `::: columns 1:2` oder "
        "`1:1:2` gibt die Breiten vor."
    ),
    layout_syntax.CONCLUSION: (
        "Die PTA-Fazit-Box: nur Text, höchstens zwei Zeilen, einmal je Folie, nicht in einem "
        "anderen Container."
    ),
    layout_syntax.COMMENT: "Die PTA-Kommentarbox zum Block direkt davor; nur Text.",
    layout_syntax.NOTES: (
        "Sprechernotizen der Folie: zwei bis fünf Sätze, die der Vortragende sagt; Tabellen und "
        "Bilder darin entfallen."
    ),
    layout_syntax.TIMELINE: (
        "Ein Zeitstrahl aus einer Liste `- 2026-Q2: Text` (2 bis 8 Einträge, aufsteigend; "
        "Termine `2026`, `2026-03`, `2026-Q2`, `2026-03-15`, `15.03.2026` oder `heute`; "
        "`{.done}` am Ende eines Eintrags heißt erledigt)."
    ),
    layout_syntax.GANTT: (
        "Ein Projektplan aus einer Tabelle mit den Spalten Vorgang, Start, Ende und Wer "
        "(freiwillig), 1 bis 12 Zeilen, Start = Ende ist ein Meilenstein; "
        "`::: gantt raster=monat` (`woche`, `monat`, `quartal`) nur bei Bedarf."
    ),
    layout_syntax.STEPS: (
        "Eine Schrittfolge: 3 bis 6 Schritte, je `### Titel` und höchstens ein kurzer Absatz; "
        "`{.current}` an höchstens einem `###` hebt den aktuellen hervor."
    ),
    layout_syntax.RISK_MATRIX: (
        "Eine Risikomatrix aus einer Tabelle mit den Spalten Nr, Risiko, Wahrscheinlichkeit, "
        "Auswirkung (Werte 1 bis 5) und Maßnahme (freiwillig); "
        "`::: riskmatrix green=4 yellow=12` verschiebt die Schwellen der Farben."
    ),
    layout_syntax.SCENE: (
        'Benannte Formen auf einem Raster, eine je Zeile `- name: box 10,10 40x20 "Text"`, '
        "allein unter einem `##`; zwei Szenenfolien mit denselben Namen und "
        '`{uebergang="morph"}` bewegen die Formen.'
    ),
    layout_syntax.INTERNAL: "Nur in den Fassungen `intern` und `trainer`: Preise, Bemerkungen.",
    layout_syntax.EXERCISE: "Eine Aufgabe; steht in jeder Fassung.",
    layout_syntax.SOLUTION: (
        "Die Lösung der Aufgabe davor (direkt nach oder in ihrem `::: exercise`), nur in der "
        "Fassung `trainer`."
    ),
}
"""What each container of ``layout_syntax.CONTAINER_NAMES`` is for, the same in every format."""

ALERT_TEXTS: Final[Mapping[str, str]] = {
    "NOTE": "Hinweis",
    "TIP": "Tipp",
    "IMPORTANT": "Wichtig",
    "WARNING": "Warnung",
    "CAUTION": "Vorsicht",
}
"""The German name of each alert of ``layout_syntax.ALERT_KINDS``."""

STATUS_TEXTS: Final[Mapping[StatusCategory, str]] = {
    StatusCategory.SUCCESS: "Erfolg, im Plan",
    StatusCategory.WARNING: "Warnung, kritisch",
    StatusCategory.DANGER: "Gefahr, verfehlt",
    StatusCategory.INFO: "Information",
    StatusCategory.NEUTRAL: "neutral, offen",
}
"""What each status category means."""

ATTRIBUTE_TEXTS: Final[Mapping[str, tuple[str, str]]] = {
    ".closing": ("`{.closing}`", "Die Abschlussfolie; kein Inhalt darunter."),
    ".dark": ("`{.dark}`", "Die Folie auf dunklem Grund, für eine Kernaussage."),
    'kicker="…"': ('`{kicker="Kapitel 1"}`', "Eine kleine Zeile über dem Titel."),
    'layout="…"': (
        '`{layout="Titel und Text (zweispaltig)"}`',
        "Ein Layout der PTA-Vorlage mit genau diesem Namen; `---` teilt den Inhalt auf.",
    ),
    'uebergang="…"': (
        '`{uebergang="fade"}`',
        "Der Übergang der Folie (an `#`: aller Folien des Kapitels).",
    ),
    ".agenda": (
        "`{.agenda}`",
        "Die Agenda: eine Liste von höchstens acht Punkten, ohne Liste die Kapitel.",
    ),
    ".interim": ("`{.interim}`", "Ein Zwischenfazit: die Aussage im Titel, kein Inhalt."),
    ".quote": ("`{.quote}`", "Ein Zitat im Titel, höchstens ein Absatz (die Quelle) darunter."),
    ".contact": (
        "`{.contact}`",
        "Kontakte: je Person `### Name` und ein Absatz mit Foto, Funktion, E-Mail, Telefon.",
    ),
    ".internal": ("`{.internal}`", "Folie oder Kapitel nur in den Fassungen `intern`/`trainer`."),
    ".backup": (
        "`{.backup}`",
        "Einmal, nach der Abschlussfolie: die Folien danach sind Reservefolien ohne Nummer.",
    ),
    ".appendix": (
        "`{.appendix}`",
        "Einmal, am ersten Anhangskapitel: ab dort heißen die Kapitel A, B, C.",
    ),
    "dauer=…": (
        "`{dauer=10}`",
        "Geplante Minuten (`90`, `4h`, `1h30`, ohne Anführungszeichen) für den Zeitplan.",
    ),
    ".break": ("`{.break dauer=15}`", "Eine Pause im Zeitplan, immer mit `dauer`, kein Inhalt."),
}
"""How each entry of ``heading_attributes.VALID`` is written, and what it does."""

DOCUMENT_ATTRIBUTES: Final = (".internal", ".appendix")
"""The heading attributes the guides of Word and the PDF describe; the rest is slide syntax,
which they take and show plainly or leave out (``{.backup}`` with the note
``attribute-ignored``). The PTA slide kinds (``.agenda`` …) are among the rest, since the Word
samples do not show them yet (E03-S05 may move them here once they do)."""

DOCUMENT_ONLY_ATTRIBUTES: Final = (".appendix",)
"""The heading attributes decks ignore (with the note ``attribute-ignored``)."""

MARKER_TEXTS: Final[Mapping[str, str]] = {
    block_markers.BUILD: (
        "Der Block erscheint beim Klick — Listen, Karten, Zeilen, Spalten und Bildreihen Punkt "
        "für Punkt."
    ),
    block_markers.FRAGMENT: "Der Block erscheint beim Klick als Ganzes.",
    block_markers.EXIT: "Der Block verschwindet beim Klick.",
    block_markers.EMPHASIZE: "Der Text wird beim Klick PTA-blau.",
    block_markers.INTERNAL: "Der Block steht nur in den Fassungen `intern` und `trainer`.",
}
"""What each block marker of ``block_markers.NAMES`` does."""

DOCUMENT_MARKERS: Final = (block_markers.INTERNAL,)
"""The block markers that do something in Word and the PDF; they leave the others out."""

LEFT_OUT_CONTAINERS: Final[Mapping[DocumentFormat, tuple[str, ...]]] = {
    DocumentFormat.DOCX: (layout_syntax.NOTES, layout_syntax.SCENE),
    DocumentFormat.PDF: (layout_syntax.NOTES,),
}
"""The containers a format leaves out (with ``notes-dropped`` or ``scene-dropped``)."""

PPTX: Final = DocumentFormat.PPTX
DOCX: Final = DocumentFormat.DOCX
PDF: Final = DocumentFormat.PDF
_ALL: Final = (PPTX, DOCX, PDF)

NOTE_TEXTS: Final[Mapping[str, tuple[tuple[DocumentFormat, ...], str]]] = {
    NoteCodes.SLIDE_SPLIT: (
        (PPTX,),
        "Zu viel für eine Folie; es geht auf „(Forts.)“-Folien weiter. Kürzen oder teilen.",
    ),
    NoteCodes.SLIDE_OVERFULL: (
        (PPTX,),
        "Passt auch bei 12 pt nicht und läuft über den Folienrand. Kürzen.",
    ),
    NoteCodes.IMAGE_CROPPED: (
        (PPTX,),
        "Der Bildrahmen schneidet mehr als ein Viertel des Bildes ab: `{focus=…}`, "
        "`{fit=contain}` oder ein Bild in passenden Proportionen.",
    ),
    NoteCodes.IMAGE_ENLARGED: (
        _ALL,
        "Ein Bild wird mehr als doppelt so groß gezeigt, wie es Pixel hat, und wirkt unscharf.",
    ),
    NoteCodes.RAW_HTML: (_ALL, "Rohes HTML wird weggelassen; Markdown schreiben."),
    NoteCodes.CODE_NOT_DRAWN: (
        _ALL,
        "Ein Diagramm- oder Chart-Block wurde nicht gezeichnet und steht als Code da.",
    ),
    NoteCodes.CHARACTER_MISSING: (
        (PDF,),
        "Ein Zeichen fehlt in den Schriften und erscheint ersetzt; in Worten schreiben.",
    ),
    NoteCodes.NOTES_DROPPED: ((DOCX, PDF), "Sprechernotizen fallen weg."),
    NoteCodes.CODE_LANGUAGE_UNKNOWN: (
        _ALL,
        "Die Sprache eines Codeblocks ist unbekannt; er steht einfarbig da.",
    ),
    NoteCodes.IMAGE_SCALE_IN_TITLE: (
        (PPTX, DOCX),
        "`scale=N` im Bildtitel gehört als `{scale=N}` hinter das Bild.",
    ),
    NoteCodes.SCENE_DROPPED: ((DOCX,), "Eine Szene (`::: scene`) fällt weg."),
    NoteCodes.AUDIENCE_OMITTED: (
        _ALL,
        "Die Fassung hat interne Blöcke oder Lösungen weggelassen — erwartet, kein Fehler.",
    ),
    NoteCodes.SCHEDULE_MISSING: (
        (PPTX,),
        "Folien ohne `dauer` in einem Deck mit Zeitplan; sie zählen je 2 Minuten.",
    ),
    NoteCodes.SCHEDULE_LENGTH: (
        (PPTX,),
        "Die Summe der Dauern trifft `laenge:` nicht, oder ein Kapitel braucht mehr als seine "
        "`dauer`.",
    ),
    NoteCodes.SCHEDULE_ESTIMATE: (
        (PPTX,),
        "Nur `./run.sh check`: die geplante Zeit weicht stark von der Faustregel ab.",
    ),
    NoteCodes.ATTRIBUTE_IGNORED: (
        _ALL,
        "Ein Überschriftenattribut des anderen Dokumenttyps (`{.backup}` in Word und PDF, "
        "`{.appendix}` auf Folien) bleibt ohne Wirkung.",
    ),
    NoteCodes.HANDOUT_WITHOUT_PICTURES: (
        (DOCX,),
        "Nur `./run.sh handout`: das Handout zeigt den Text der Folien statt ihrer Bilder, weil "
        "die Vorschau fehlt — `./run.sh setup` installiert sie.",
    ),
}
"""For each code of ``NoteCodes.ALL`` the formats that report it and what to do."""

# ---------------------------------------------------------------------- template and filling


def template(package: str, name: str) -> str:
    """The guide template ``<package>/authoring_guide/<name>.md`` (package data, line ends
    normalised to ``\\n``). A missing template is a ``FileNotFoundError``: a programming error."""
    text = resources.files(package).joinpath(FOLDER, f"{name}.md").read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def fill(template: str, values: Mapping[str, str]) -> str:
    """``template`` with every ``{{name}}`` replaced by its value (without leading and trailing
    line breaks). Runs of blank lines become one, so a placeholder alone on its line with an
    empty value leaves no blank line behind; the result ends with exactly one line break.

    A placeholder without a value is a programming error: ``KeyError``."""

    def value(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise KeyError(f"The authoring guide has no value for '{match.group(0)}'.")
        return values[name].strip("\n")

    filled = _PLACEHOLDER.sub(value, template)
    return _BLANK_LINES.sub("\n\n", filled).strip("\n") + "\n"


def names(values: Iterable[str], last: str = "oder") -> str:
    """The values as code, the last joined by ``last``: ```` `a`, `b` oder `c` ````."""
    quoted = [f"`{v}`" for v in values]
    if len(quoted) <= 1:
        return "".join(quoted)
    return f"{', '.join(quoted[:-1])} {last} {quoted[-1]}"


def choices(values: Iterable[str], default: str | None = None) -> str:
    """The values as code, ``default`` marked: ```` `hoch` (Standard), `quer` ````."""
    return ", ".join(f"`{v}` (Standard)" if v == default else f"`{v}`" for v in values)


def words(guide: str) -> int:
    """How many words ``guide`` has: runs of letters or digits."""
    return len(_WORD.findall(guide))


def named_syntax(guide: str) -> list[str]:
    """The syntax ``guide`` names (``SYNTAX_PATTERN``), each once, in order."""
    return list(dict.fromkeys(m.group(0) for m in SYNTAX_PATTERN.finditer(guide)))


def named_keys(guide: str) -> list[str]:
    """The keys of the front matter table of ``guide`` (``KEY_PATTERN``), each once, in order."""
    return list(dict.fromkeys(KEY_PATTERN.findall(guide)))


# ---------------------------------------------------------------------- front matter


@dataclass(frozen=True, slots=True)
class GuideKey:
    """A row of the front matter table: the key, the values it takes and what it does."""

    key: str
    values: str
    """Markdown: ```` `ja`, `nein` (Standard) ```` or a description (``frei``)."""
    meaning: str


def common_keys(default_audience: Audience = Audience.KUNDE) -> dict[str, GuideKey]:
    """The rows of the keys that mean the same in every format, by key."""
    rows = (
        GuideKey(
            Keys.DATE,
            "`2026-11-08` oder `08.11.2026`",
            "Das Datum des Dokuments statt des heutigen.",
        ),
        GuideKey(
            Keys.LANGUAGE,
            choices((v.value for v in Language), Language.DE.value),
            "Die Sprache der erzeugten Texte („Seite“, „Tabelle“, Hinweisnamen).",
        ),
        GuideKey(
            Keys.TYPOGRAPHY,
            choices((YES, NO), YES),
            "Gerade Anführungszeichen, ` - ` und `...` werden „…“, – und …; `nein` lässt sie.",
        ),
        GuideKey(
            Keys.HIGHLIGHT,
            choices((YES, NO), YES),
            "Codeblöcke mit Sprache werden farbig; `nein`: einfarbig.",
        ),
        GuideKey(
            Keys.CHECK,
            "`aus` oder `style-…`-Codes, durch Kommas getrennt",
            "Nur `./run.sh check`: diese Stilregeln nicht prüfen.",
        ),
        GuideKey(
            Keys.AUDIENCE,
            choices((a.value for a in Audience), default_audience.value),
            "Die Fassung: `kunde` ohne Internes und Lösungen, `intern` mit Internem, `trainer` "
            "mit allem.",
        ),
    )
    return {row.key: row for row in rows}


def front_matter_section(
    keys: Sequence[GuideKey],
    valid: Collection[str],
    example: str,
    *,
    status: bool = True,
) -> str:
    """The section „Front Matter“: the syntax with ``example`` (the lines between the ``---``),
    then a table row per key, then ``status.<kategorie>`` when ``status``.

    ``valid`` is the generator's list of valid keys (``VALID_KEYS``): ``keys`` must describe
    exactly those, in any order, so that the guide and ``FrontMatter.check_keys`` cannot drift
    apart — otherwise ``ValueError``, a programming error."""
    described = [k.key for k in keys]
    missing = [k for k in valid if k not in described]
    extra = [k for k in described if k not in valid]
    if missing or extra or len(set(described)) != len(described):
        raise ValueError(
            f"The front matter rows do not match the valid keys: missing {missing}, "
            f"not valid {extra}, twice {sorted({k for k in described if described.count(k) > 1})}."
        )
    lines = [
        "## Front Matter",
        "",
        "Einstellungen stehen in einem Block ganz oben, vor allem anderen, zwischen zwei Zeilen "
        "`---`: je Zeile `schlüssel: wert`, ohne Verschachtelung und ohne Listen. Schlüssel und "
        f"Werte sind deutsch, Wahrheitswerte `{YES}` oder `{NO}`. Was der Standard schon tut, "
        "weglassen.",
        "",
        "```markdown",
        "---",
        example.strip("\n"),
        "---",
        "```",
        "",
        "| Schlüssel | Werte | Bedeutung |",
        "| --------- | ----- | --------- |",
        *(f"| `{k.key}` | {k.values} | {k.meaning} |" for k in keys),
    ]
    if status:
        categories = ", ".join(f"`{c.value}` ({STATUS_TEXTS[c]})" for c in StatusCategory)
        lines.append(
            f"| `{Keys.STATUS_PREFIX}<kategorie>` | Texte, durch `;` getrennt | Tabellenzellen "
            f"nur aus einem dieser Texte als Code (`` `Erledigt` ``) werden Status-Labels in der "
            f"Farbe der Kategorie: {categories}. Jeder Text gehört zu einer Kategorie. |"
        )
    lines += [
        "",
        "Ein unbekannter Schlüssel, ein doppelter oder ein ungültiger Wert ist ein Fehler, der "
        "die gültigen nennt.",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------- slide syntax


def layout_syntax_section(format: DocumentFormat, effect: str = "") -> str:
    """The section „Folien-Syntax“ for ``format``: containers, alerts, highlighting, heading
    attributes and block markers, named from ``layout_syntax``, ``heading_attributes`` and
    ``block_markers``. ``effect`` is the guide's own paragraph on how ``format`` shows them; it
    follows the first paragraph.

    Word and the PDF get the slide-only names in a sentence of their own, as plain names
    (``notes``, ``.dark``), so that ``named_syntax`` finds only what they show."""
    slides = format is PPTX
    left_out = LEFT_OUT_CONTAINERS.get(format, ())
    lines = [
        "## Folien-Syntax",
        "",
        "Word, PowerPoint und PDF lesen dieselbe Syntax und prüfen sie, bevor sie schreiben: "
        "ein Fehler bricht mit der Zeile ab (`Line 12: …`) und nennt die gültigen Namen. "
        "Klammern, die nicht genau so aussehen, bleiben Text.",
    ]
    if effect.strip():
        lines += ["", effect.strip("\n")]
    lines += [
        "",
        "### Container",
        "",
        "Ein Container beginnt mit einer Zeile `::: <name>` (Argumente dahinter) und endet mit "
        "`:::`; ineinander stehen sie mit längeren Zäunen (`::::` außen).",
        "",
        "| Container | Wofür |",
        "| --------- | ----- |",
    ]
    lines += [
        f"| `::: {name}` | {CONTAINER_TEXTS[name]} |"
        for name in layout_syntax.CONTAINER_NAMES
        if name not in left_out
    ]
    if left_out:
        lines += ["", f"{_FORMAT_NAMES[format]} lässt {names(left_out, 'und')} weg (mit Hinweis)."]
    lines += [
        "",
        "### Hinweise und Hervorhebungen",
        "",
        "- Ein Zitat, dessen erste Zeile ein Alert ist, wird ein Hinweis: "
        + ", ".join(f"`> [!{kind}]` ({ALERT_TEXTS[kind]})" for kind in layout_syntax.ALERT_KINDS)
        + ".",
        "- `==Text==` markiert wie ein Textmarker; ist die erste Zelle einer Tabellenzeile ganz "
        "markiert, die ganze Zeile.",
        "- `[Wörter]{.success}` setzt Wörter fett in einer Statusfarbe: "
        + ", ".join(f"`{{.{c.value}}}` ({STATUS_TEXTS[c]})" for c in StatusCategory)
        + ". Signalfarben nur für Status, zur Hervorhebung `==…==`.",
        f"- Status-Labels: `{Keys.STATUS_PREFIX}success: Erledigt; Fertig` im Front Matter und "
        "eine Tabellenzelle nur aus `` `Erledigt` `` ergeben ein Label in der Farbe.",
        "",
        "### Attribute an Überschriften",
        "",
        "Am Ende einer Überschrift, in geschweiften Klammern; mehrere in einer Klammer "
        + ('(`{.dark kicker="Kapitel 1"}`).' if slides else "durch Leerzeichen getrennt."),
        "",
    ]
    lines += _attributes(format)
    lines += ["", "### Blockmarker", ""]
    lines += _markers(slides)
    return "\n".join(lines) + "\n"


_FORMAT_NAMES: Final = {PPTX: "PowerPoint", DOCX: "Word", PDF: "Das PDF"}


def _entries(text: str) -> list[str]:
    return [e.strip() for e in text.split(",")]


def _attributes(format: DocumentFormat) -> list[str]:
    section = set(_entries(heading_attributes.VALID_ON_SECTION))
    slide = set(_entries(heading_attributes.VALID_ON_SLIDE))
    shown = [
        entry
        for entry in _entries(heading_attributes.VALID)
        if (
            entry not in DOCUMENT_ONLY_ATTRIBUTES
            if format is PPTX
            else entry in DOCUMENT_ATTRIBUTES
        )
    ]
    lines = ["| Attribut | An | Wirkung |", "| -------- | -- | ------- |"]
    for entry in shown:
        written, meaning = ATTRIBUTE_TEXTS[entry]
        where = ", ".join(h for h, valid in (("`#`", section), ("`##`", slide)) if entry in valid)
        lines.append(f"| {written} | {where} | {meaning} |")
    others = [e for e in _entries(heading_attributes.VALID) if e not in shown]
    if others:
        lines += [
            "",
            f"Die übrigen ({names(others, 'und')}) gelten nur für "
            f"{'Word und PDF' if format is PPTX else 'Folien'}: {_FORMAT_NAMES[format]} nimmt "
            "sie an, die Überschrift bleibt eine gewöhnliche Überschrift.",
        ]
    return lines


def _markers(slides: bool) -> list[str]:
    shown = [n for n in block_markers.NAMES if slides or n in DOCUMENT_MARKERS]
    lines = [
        "Eine Zeile nur aus dem Marker, direkt vor dem Block (Absatz, Liste, Tabelle, Container):",
        "",
        *(f"- `{{.{name}}}`: {MARKER_TEXTS[name]}" for name in shown),
    ]
    entrances = [e for e in block_markers.ENTRANCES if e != block_markers.FADE]
    if slides:
        lines.append(
            f"- Eingang: `{{.{block_markers.BUILD}={entrances[0]}}}`, "
            + ", ".join(f"`={e}`" for e in entrances[1:])
            + f" (Standard `={block_markers.FADE}`, einblenden), ebenso an "
            f"`{{.{block_markers.FRAGMENT}}}`. Nur unter `##`-Folien, sparsam."
        )
    else:
        others = [n for n in block_markers.NAMES if n not in shown]
        lines += ["", f"Word und PDF lassen {names((f'.{n}' for n in others), 'und')} weg."]
    return lines


# ---------------------------------------------------------------------- other sections


def icons_section(format: DocumentFormat) -> str:
    """The section „Icons“ with every name of ``design.icons.ICONS``."""
    where = (
        "Auf Folien nur vor dem Titel einer Karte (`### :icon-rocket: Start` in `::: cards`) und "
        "vor **jedem** Punkt einer Liste (dann das Aufzählungszeichen); anderswo ist ein Icon "
        "ein Fehler."
        if format is PPTX
        else "Im Text so hoch wie die Schrift; beginnt **jeder** Punkt einer Liste mit einem "
        "Icon, wird es das Aufzählungszeichen."
    )
    return (
        "## Icons\n\n"
        "`:icon-check:` setzt ein Strich-Icon in PTA-Blau — keine Bilddatei, keine Quelle nötig. "
        f"{where} Nur diese Namen; ein anderer ist ein Fehler, der ähnliche nennt:\n\n"
        + " ".join(f"`{name}`" for name in icons.ICONS)
        + "\n"
    )


def notes_section(format: DocumentFormat) -> str:
    """The section „Hinweise“: the codes of ``NoteCodes.ALL`` that ``format`` reports."""
    rows = []
    for code in NoteCodes.ALL:
        formats, text = NOTE_TEXTS[code]
        if format in formats:
            rows.append(f"| `{code}` | {text} |")
    return (
        "## Hinweise\n\n"
        "Was der Generator umgehen musste, meldet er als Hinweis mit Zeile "
        "(`line 12: …`); das Dokument ist trotzdem geschrieben. Das Markdown so ändern, dass "
        "keine Hinweise mehr kommen.\n\n"
        "| Code | Was tun |\n| ---- | ------- |\n" + "\n".join(rows) + "\n"
    )


def typography_section() -> str:
    """The section „Typografie und Code“ (E17-S02)."""
    return (
        "## Typografie und Code\n\n"
        "Gerade Anführungszeichen (`\"…\"`, `'…'`), ` - ` und `...` schreiben: der Generator "
        "setzt „…“, ‚…‘, – und … und schützt Leerzeichen in `z. B.`, `Nr. 3`, `10 %`. "
        "Code, Links und Front Matter bleiben unberührt; "
        f"`{Keys.TYPOGRAPHY}: {NO}` schaltet es ab. Codeblöcke mit Sprache "
        "(```` ```python ````) werden farbig (`"
        f"{Keys.HIGHLIGHT}: {NO}` schaltet ab); eine unbekannte Sprache ergibt den Hinweis "
        f"`{NoteCodes.CODE_LANGUAGE_UNKNOWN}`.\n"
    )


def renderers_section(renderers: Iterable[CodeBlockRenderer]) -> str:
    """The sections of the renderers that have one, in order, separated by a blank line; empty
    when none has."""
    parts = (r.authoring_guide for r in renderers)
    return "\n\n".join(p.strip("\n") for p in parts if p and p.strip())


def image_formats(native: Iterable[str], converters: Iterable[ImageConverter]) -> tuple[str, ...]:
    """The image formats a generator places: ``native``, then those its converters name, each
    once (without regard to case)."""
    found: dict[str, str] = {}
    for name in [*native, *(c.format for c in converters if c.format)]:
        found.setdefault(name.lower(), name)
    return tuple(found.values())


def characters_section(
    has_text_glyph: Callable[[int], bool],
    has_code_glyph: Callable[[int], bool],
    intro: str,
) -> str:
    """The body of a section on characters: ``intro`` (what happens to a character the fonts
    lack), then a table of the ``SYMBOLS`` the fonts lack, grouped by the first replacement they
    all have, and a sentence each on those only the text or only the code font lacks — or only
    ``intro`` when they have every symbol. Only the PDF needs it: Word and PowerPoint take the
    installed font. (Symbols are no words for ``words``: the grouping keeps the guide short.)"""

    def everywhere(text: str) -> bool:
        return all(has_text_glyph(ord(c)) and has_code_glyph(ord(c)) for c in text)

    groups: dict[str, list[str]] = {}
    in_code: list[str] = []
    in_text: list[str] = []
    for symbol, replacements in SYMBOLS:
        text_has, code_has = has_text_glyph(ord(symbol)), has_code_glyph(ord(symbol))
        if text_has and code_has:
            continue
        instead = next((r for r in replacements if everywhere(r)), replacements[-1])
        groups.setdefault(instead, []).append(symbol)
        if code_has:
            in_code.append(symbol)
        elif text_has:
            in_text.append(symbol)
    if not groups:
        return intro.strip("\n") + "\n"
    rows = [
        f"| {' '.join(symbols)} | `{instead.replace('|', chr(92) + '|')}` |"
        for instead, symbols in groups.items()
    ]
    lines = [
        intro.strip("\n"),
        "",
        "| Vermeiden | Stattdessen |",
        "| --------- | ----------- |",
        *rows,
    ]
    remarks = [
        f"{label} {' '.join(symbols)}."
        for label, symbols in (("In Code gehen:", in_code), ("Nur im Text gehen:", in_text))
        if symbols
    ]
    if remarks:
        lines += ["", " ".join(remarks)]
    return "\n".join(lines) + "\n"
