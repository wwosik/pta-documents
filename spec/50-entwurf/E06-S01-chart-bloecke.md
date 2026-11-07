# E06-S01 `chart`-Blöcke

> Status: Entwurf
> Epic: [E06 Diagramme und Charts](E06-diagramme-und-charts.md)
> Milestone: [M03 Grafik, Diagramme und Charts](M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Ein Codeblock ` ```chart ` (Einstellungen, `---`, CSV) wird ein Balken-, Linien- oder
Flächendiagramm in den PTA-Farben: in Folien und Word ein natives, bearbeitbares Diagramm mit
eingebetteter Tabelle, im PDF eine Vektorzeichnung.

## Kontext

- DocLibs `DocumentGeneration.Charts`: `ChartParser.cs` (133 Zeilen), `ChartDrawing.cs` (206:
  Titel, Werteachse mit runden Schritten, Kategorien, Legende), `ChartRenderer.cs` (62);
  `ChartSpec`, `ChartSeries`, `ChartKind`, `ChartGraphic` in `CodeBlockRenderer.cs`;
  `Pptx/ChartWriter.cs` (171: Chart-XML von Hand plus Arbeitsmappe). Tests `ChartTests.cs`
  (10 Fälle), Anleitung `AuthoringGuide/Charts.md`.
- python-pptx kann native Diagramme samt eingebetteter Arbeitsmappe (über xlsxwriter, bereits
  installiert); python-docx kann es nicht. Die PTA-Vorlage hat Diagrammlayouts mit
  Diagrammplatzhalter (idx 15/19) und Textplatzhaltern für Diagrammtitel (12), Werteinheit (13)
  und Quellenangabe (14): `Titel und Diagramm`, `Titel und zwei Diagramme`,
  `Titel, Diagramm und Text`, `Titel, Text und Diagramm`.
- PTA-Vorgaben (Designanalyse, *Weitere Muster*): Reihen in Akzent 1, 2, 3 (`colors.ACCENTS`),
  Achsenbeschriftung 14 pt Segoe UI Light, Achsenlinie 0,5 pt, keine Teilstriche.
- Voraussetzungen: `Drawing` (E02-S03), Renderer-Schnittstelle mit `ChartGraphic` (E02-S04).

## Vorgeschlagener Ansatz

1. Paket `src/pta_documents/charts/` (Kern, ohne Extra): `spec.py` (`ChartKind`, `ChartSeries`,
   `ChartSpec` mit `stacked`, `title`, `unit`, `source`, `colors`), `parser.py` (Port von
   `ChartParser.cs`: Einstellungen bis `---`, Kommentare ` # …`, CSV mit Anführungszeichen,
   leere Zellen = Lücken, Linien stapeln nie; jeder Fehler nennt die Zeile des Blocks),
   `drawing.py` (Port von `ChartDrawing.cs` inklusive `scale()`), `renderer.py`
   (`ChartRenderer`: nur Sprache `chart`, ohne Groß/Klein → `ChartGraphic(spec, drawing)`).
2. Farben ausschließlich aus `design/colors.py`: Reihen `ACCENTS` der Reihe nach, Text
   `TEXT_WORD` (PDF/Word) bzw. `TEXT_SLIDES` (Folien), Gitter `GREY_LIGHT`, Achse `GREY_MID`.
   Neue Einstellung `quelle` (Quellenangabe, wie in den Diagrammlayouts).
3. **Folien** (`generation/pptx/chart.py`, ersetzt `ChartWriter.cs`): `CategoryChartData` →
   `COLUMN_CLUSTERED`/`COLUMN_STACKED`, `LINE_MARKERS`, `AREA`/`AREA_STACKED`; Lücke 60 %,
   Reihenfarben, Achsen 14 pt Segoe UI Light `404040`, Achsenlinie 0,5 pt ohne Teilstriche,
   Legende unten. Eine Folie mit genau einem Chart nimmt `Titel und Diagramm` und füllt den
   Platzhalter (`insert_chart`), Titel → Diagrammtitel, Einheit → Werteinheit, Quelle →
   Quellenangabe; Text davor → `Titel, Text und Diagramm`, Text danach → `Titel, Diagramm und
   Text`; zwei Charts in `::: columns` → `Titel und zwei Diagramme`.
4. **Word** (`generation/docx/chart.py`): Chart-XML mit python-pptx' `ChartXmlWriter`, Arbeitsmappe
   aus `chart_data.xlsx_blob`; neuer Teil `word/charts/chartN.xml` mit Beziehung vom Dokument,
   Arbeitsmappe unter `word/embeddings/` mit `c:externalData`, eingebunden als `wp:inline` mit
   `c:chart`, über die Satzspiegelbreite im Seitenverhältnis 640:380. Text 10 pt Segoe UI
   schwarz; Reihenfarben wie oben. Danach eine Beschriftung „Abbildung n: <Titel>" wie bei
   Bildern (E03-S02), wenn ein Titel gesetzt ist.
5. **PDF**: die Zeichnung aus `drawing.py`, gesetzt durch E05-S04; nur Test.
6. Die Generatoren erhalten `ChartRenderer` standardmäßig in ihren `code_block_renderers`
   (der Kern braucht kein Extra).
7. Tests `tests/charts/test_parser.py`, `test_drawing.py`, `test_renderer.py` (Fälle aus
   `ChartTests.cs`: Einstellungen und Daten, CSV allein, Fehler mit Zeile, `scale()`, Balken je
   Wert plus Legende, nur `chart`-Blöcke), dazu Folie (Chart-Teil mit Arbeitsmappe,
   `clustered`, Reihennamen, Werte, Titel, zwei Charts nebeneinander), Word (Chart-Teil,
   Arbeitsmappe, öffnet mit python-docx) und PDF (Titel als Text). Beispiele nach `.tmp/review/`.

## Akzeptanzkriterien

- [ ] Die Testfälle aus `ChartTests.cs` sind übernommen und grün.
- [ ] In PowerPoint und Word ist das Diagramm nativ: „Daten bearbeiten" öffnet die eingebettete
      Tabelle (Prüfpunkt für den Menschen).
- [ ] Folien mit Charts verwenden die PTA-Diagrammlayouts mit Titel, Einheit und Quelle in deren
      Platzhaltern.
- [ ] Alle Farben stammen aus `design/colors.py`; Reihen folgen der Akzentreihenfolge.
- [ ] Ein Fehler im Block ist eine `DocumentConversionError` mit der Zeile des Blocks.

## Offene Fragen

1. Die Einstellungen im Block sind in DocLibs englisch (`type: bar|line|area`, `title`, `unit`,
   `stacked: true`). Bleiben sie englisch, weil sie Markdown-Syntax sind (wie `::: cards`), oder
   werden sie deutsch wie das Front Matter (`typ: balken|linie|flaeche`, `titel`, `einheit`,
   `gestapelt: ja`, `quelle`)?

> (2026-11-07) Englisch (Markdown-Syntax).

2. Zahlen: nur mit Dezimalpunkt (`1250.5`, wie DocLibs) oder auch deutsch mit Komma (`1250,5`)?
   Mit Komma bräuchte die CSV ein anderes Trennzeichen (`;`).

> (2026-11-07) Beides: Trennzeichen `,` → Dezimalpunkt, Trennzeichen `;` → Dezimalkomma.

3. Die Diagrammlayouts nennt auch E04-S04. Vorschlag: Charts nutzen sie hier, E04-S04 deckt nur
   noch die übrigen Layouts ab. Einverstanden?

> (2026-11-07) Ja.

## Notizen

- Überschneidung mit E03-S04 („natives Word-Diagramm"): der native Word-Chart entsteht hier;
  E03-S04 bleibt für Zeichnungen (Mermaid, Finanzdiagramme) im DOCX.
- `::: columns` für zwei Charts setzt E02-S02/E04-S03 voraus; ohne sie wird der Fall später
  nachgezogen.
