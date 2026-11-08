"""The ``chart`` code-block renderer (port of DocLibs ``ChartRenderer.cs``).

A ``chart`` block (language without regard to case) becomes a ``ChartGraphic``: PowerPoint and
Word write it as a native, editable chart with its data in an embedded workbook, PDF draws
``ChartGraphic.drawing``. A ``financial-chart`` block (JSON, E06-S02) becomes a
``DrawingGraphic``: a financial chart of ``charts.financial``, shapes on slides. Part of the
core: no extra needed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final

from pta_documents.charts import drawing, financial, parser
from pta_documents.charts.financial import json_block
from pta_documents.design import colors
from pta_documents.design.chart_colors import FINANCIAL
from pta_documents.design.variants import Language
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRequest,
    DrawingGraphic,
)

LANGUAGE: Final = "chart"
FINANCIAL_LANGUAGE: Final = json_block.LANGUAGE

AUTHORING_GUIDE: Final = """## Charts

Ein Codeblock mit der Sprache `chart` wird ein Balken-, Linien- oder Flächendiagramm in den
PTA-Farben — in Word und PowerPoint ein echtes Diagramm, dessen Daten sich mit „Daten
bearbeiten" ändern lassen. Oben stehen die Einstellungen, je Zeile `name: wert`, dann eine
Zeile `---`, dann die Daten als CSV: eine Kopfzeile (der Name der Kategorienspalte, dann ein
Name je Reihe) und eine Zeile je Kategorie.

````markdown
```chart
type: bar
title: Aufträge je Monat
unit: Tsd. EUR
source: Quelle: Vertrieb
---
Monat, Plan, Ist
Jan, 120, 132
Feb, 118, 121
Mär, 125, 140
```
````

- **Einstellungen** (englisch, alle freiwillig): `type` ist `bar` (Balken, Standard), `line`
  (Linien) oder `area` (Flächen); `stacked: true` stapelt Balken oder Flächen (Linien nie);
  `title`, `unit` (Einheit der Werte) und `source` (Quellenangabe). Ein Kommentar steht nach
  ` # `. Ohne Einstellungen besteht der Block nur aus der CSV.
- **Zahlen:** Mit `,` als Trennzeichen haben Zahlen einen Dezimalpunkt (`1250.5`), mit `;` ein
  Dezimalkomma (`1250,5`) — die Kopfzeile entscheidet. Keine Tausenderpunkte. Ein Feld in
  Anführungszeichen darf das Trennzeichen enthalten; ein leeres Feld lässt eine Lücke.
- **Folien:** Ein Chart allein kommt auf `Titel und Diagramm`, mit Text davor auf
  `Titel, Text und Diagramm`, mit Text danach auf `Titel, Diagramm und Text`; zwei Charts
  (auch in `::: columns`) auf `Titel und zwei Diagramme`. Titel, Einheit und Quelle stehen in
  den Platzhaltern des Layouts. Auf Folien mit Hinweisboxen, Karten o. Ä. ist ein Chart ein
  Fehler.
- **Word:** Das Diagramm steht über die Satzspiegelbreite (höchstens 5:8 so hoch), mit einem
  Titel darunter die Beschriftung „Abbildung n: Titel". Ein Absatz `Abbildung: …` direkt nach
  dem Block geht dem Titel vor.
- Ein Fehler in Einstellungen oder Daten bricht mit der Zeile ab, in der er steht.

### Finanzdiagramme

Ein Codeblock mit der Sprache `financial-chart` enthält eines der Diagramme einer
Ergebnisübersicht als JSON: `development` (Entwicklung über das Jahr), `growth-by-row`
(Wachstum je Zeile), `actual-vs-reference` (Ist gegen Plan), `growth-trend` (Wachstumstrend),
`two-year` (zwei Jahre Monat für Monat) oder `summary-table` (Übersichtstabelle). Die Schlüssel
sind englisch, weil solche Blöcke meist ein Programm schreibt. Wachstumsraten und Anteile sind
Brüche (`0.05` sind 5 %), `lastActual` zählt die Monate ab 0.

````markdown
```financial-chart
{
  "type": "growth-trend",
  "title": "Wachstum Aufträge",
  "period": "Mai 2026",
  "lastActual": 2,
  "reference": 0.05,
  "months": [
    { "label": "Jan", "change": 0.056 }, { "label": "Feb", "change": 0.054 },
    { "label": "Mär", "change": 0.04 }, { "label": "Apr", "change": 0.045 },
    { "label": "Mai", "change": 0.05 }
  ],
  "options": { "labels": { "reference": "Ziel" } }
}
```
````

- **Sprache:** Zahlen und Beschriftungen folgen `sprache:` (deutsch: `5,2 %`, *Vorjahr*, *Ist*,
  *Plan*, *Prognose*); `"culture": "en"` (oder `de`, `de-DE`, `en-US`, `en-GB`) stellt um.
- **Optionen** (`options`): `culture`, `scale` und `unit` (`1000000` und `Mio. EUR`), `labels`
  über denen der Sprache (`previous`, `current`, `reference`, `projection`, `estimate`,
  `change`, `overall`, `value`), `tolerance` (ab wann eine Zahl vorn oder hinten liegt, Standard
  `0.005`), `restShare` und `width` (Breite in Pixeln, Standard 560).
- **Regeln:** Eine Farbe bedeutet eine Reihe, Grün und Rot stehen nur an Zahlen, gestrichelt
  heißt Prognose, jede Werteachse enthält null.
- **Folien:** Das Diagramm steht als Gruppe bearbeitbarer Formen in der Inhaltsfläche von
  `Nur Titel` (mit Text davor auf `Titel und Text`), nie größer als gezeichnet.
- **Word:** Das Diagramm steht als Bild (scharf als SVG, mit PNG für ältere Word-Versionen) in
  seiner natürlichen Größe, höchstens über die Satzspiegelbreite; ein Absatz `Abbildung: …`
  direkt nach dem Block wird die Beschriftung „Abbildung n: …". Dafür braucht es das Extra `svg`.
- Ein unbekannter Schlüssel, ein falscher Typ oder ungültiges JSON bricht mit der Zeile ab;
  Kommentare (`//`) und ein Komma nach dem letzten Eintrag sind erlaubt.
"""


@dataclass(frozen=True, slots=True)
class ChartRenderer:
    """Renders ``chart`` blocks as bar, line and area charts in the PTA accents, and
    ``financial-chart`` blocks as the financial charts of ``charts.financial``."""

    @property
    def authoring_guide(self) -> str | None:
        return AUTHORING_GUIDE

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        """A ``ChartGraphic`` for a ``chart`` block; None for other languages.

        Raises ``parser.ChartBlockError`` (a ``ValueError``; the generators make it a
        ``DocumentConversionError``) when the block is malformed.
        """
        words = request.info.split()
        if words and words[0].lower() == FINANCIAL_LANGUAGE:
            return _financial(request, words)
        if not words or words[0].lower() != LANGUAGE:
            return None
        if len(words) > 1:
            where = f"Line {request.line}: " if request.line else ""
            raise parser.ChartBlockError(
                f"{where}The chart block cannot be drawn: '{' '.join(words[1:])}' after "
                "```chart is not read; write settings such as 'type: line' in the block, above "
                "the line '---'."
            )
        spec = parser.parse(request.code, request.line)
        return ChartGraphic(spec, drawing.draw(spec, request.language, _palette(request)))


def _financial(request: CodeBlockRequest, words: list[str]) -> DrawingGraphic:
    """A ``DrawingGraphic`` of a ``financial-chart`` block; ``FinancialChartError`` when it is
    malformed or its data does not fit together."""
    if len(words) > 1:
        raise json_block.error(
            request.line,
            f"'{' '.join(words[1:])}' after ```{FINANCIAL_LANGUAGE} is not read; write settings "
            'in the block, under "options".',
        )
    culture = "en" if request.language is Language.EN else None
    chart, options = json_block.parse(request.code, request.line, culture)
    # Slides take their own text colour; the chart keeps its white surface on dark slides.
    text = colors.TEXT_SLIDES if request.format is DocumentFormat.PPTX else FINANCIAL.text
    options = replace(options, colors=replace(options.colors, text=text))
    try:
        return DrawingGraphic(financial.draw(chart, options))
    except ValueError as failure:
        raise json_block.error(request.line, str(failure)) from None


def _palette(request: CodeBlockRequest) -> drawing.ChartColors:
    if request.dark:
        return drawing.ChartColors(text=colors.WHITE)
    if request.format is DocumentFormat.PPTX:
        return drawing.ChartColors(text=colors.TEXT_SLIDES)
    return drawing.ChartColors(text=colors.TEXT_WORD)
