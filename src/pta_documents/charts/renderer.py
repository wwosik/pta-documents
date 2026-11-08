"""The ``chart`` code-block renderer (port of DocLibs ``ChartRenderer.cs``).

A ``chart`` block (language without regard to case) becomes a ``ChartGraphic``: PowerPoint and
Word write it as a native, editable chart with its data in an embedded workbook, PDF draws
``ChartGraphic.drawing``. Part of the core: no extra needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pta_documents.charts import drawing, parser
from pta_documents.design import colors
from pta_documents.errors import DocumentFormat
from pta_documents.generation.common.renderers import (
    ChartGraphic,
    CodeBlockGraphic,
    CodeBlockRequest,
)

LANGUAGE: Final = "chart"

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
- **Word:** Das Diagramm steht über die Satzspiegelbreite, mit einem Titel darunter die
  Beschriftung „Abbildung n: Titel".
- Ein Fehler in Einstellungen oder Daten bricht mit der Zeile ab, in der er steht.
"""


@dataclass(frozen=True, slots=True)
class ChartRenderer:
    """Renders ``chart`` blocks as bar, line and area charts in the PTA accents."""

    @property
    def authoring_guide(self) -> str | None:
        return AUTHORING_GUIDE

    def render(self, request: CodeBlockRequest) -> CodeBlockGraphic | None:
        """A ``ChartGraphic`` for a ``chart`` block; None for other languages.

        Raises ``parser.ChartBlockError`` (a ``ValueError``; the generators make it a
        ``DocumentConversionError``) when the block is malformed.
        """
        words = request.info.split()
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


def _palette(request: CodeBlockRequest) -> drawing.ChartColors:
    if request.dark:
        return drawing.ChartColors(text=colors.WHITE)
    if request.format is DocumentFormat.PPTX:
        return drawing.ChartColors(text=colors.TEXT_SLIDES)
    return drawing.ChartColors(text=colors.TEXT_WORD)
