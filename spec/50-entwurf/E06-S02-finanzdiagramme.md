# E06-S02 Finanzdiagramme

> Status: Entwurf
> Epic: [E06 Diagramme und Charts](E06-diagramme-und-charts.md)

## Zusammenfassung

Die sechs Diagramme einer Ergebnisübersicht aus DocLibs — Entwicklung, Wachstum je Zeile, Ist
gegen Referenz, Wachstumstrend, zwei Jahre, Übersichtstabelle — als ` ```financial-chart `-Block
(JSON) und als Python-API, gezeichnet als `Drawing` in den PTA-Farben: Formen in Folien, Vektoren
im PDF, eigenständiges SVG mit Tooltips.

## Kontext

- DocLibs `DocumentGeneration.Charts` (~1 950 Zeilen): `FinancialChart.cs` (273, die sechs
  Datensätze), `FinancialChartJson.cs` (99, strenges JSON mit Zeilennummern),
  `FinancialChartOptions.cs` (65: Kultur, Skala, Einheit, Beschriftungen, Toleranz,
  `RestShare`, Breite 560), `FinancialCharts.cs` (60: `Draw`, `ToSvg`, `CategoryColors`),
  `FinancialCanvas.cs` (283: Achse in runden Schritten, Urteilsfarben, Umbruch, Endbeschriftungen),
  `DevelopmentDrawing.cs` (389), `GrowthByRowDrawing.cs` (132), `ActualVsReferenceDrawing.cs`
  (183), `GrowthTrendDrawing.cs` (111), `TwoYearDrawing.cs` (167), `SummaryTableDrawing.cs` (193).
- Tests: `FinancialChartTests.cs` (23 Fälle), `FinancialSamples.cs` (160, Beispieldaten),
  8 Schnappschüsse `Samples/financial/*.expected.svg`, `FinancialChartDeckTests.cs`.
- Die Farbrollen von DocLibs (`ResolvedChartColors`: je Reihe vier Abstufungen, Referenz,
  Referenzfläche, Achse, Gitter, Band, Vorsprung/gleichauf/Rückstand, Fläche, Tabellenkopf,
  Summen, Tooltip) werden aus dem Brand abgeleitet; einen Brand gibt es hier nicht.
- Regeln der Diagramme bleiben: eine Farbe bedeutet eine Reihe, Urteilsfarben nur an Zahlen,
  gestrichelt heißt Prognose, jede Werteachse enthält null.

## Vorgeschlagener Ansatz

1. Paket `src/pta_documents/charts/financial/`: `model.py` (frozen dataclasses der sechs
   Diagramme und ihrer Zeilen, Port von `FinancialChart.cs`), `options.py`
   (`FinancialChartOptions`, `FinancialChartLabels`), `canvas.py`, je Diagramm ein Modul
   (`development.py`, `growth_by_row.py`, `actual_vs_reference.py`, `growth_trend.py`,
   `two_year.py`, `summary_table.py`) und `__init__.py` mit `draw()`, `to_svg()`,
   `category_colors()`.
2. `json_block.py`: Port von `FinancialChartJson.cs` — Diskriminator `type` (`development`,
   `growth-by-row`, `actual-vs-reference`, `growth-trend`, `two-year`, `summary-table`),
   unbekannte Eigenschaften und falsche Typen sind Fehler mit Zeile (Blockzeile +
   `JSONDecodeError.lineno`); die JSON-Schlüssel bleiben englisch, weil Programme sie schreiben.
3. Zahlenformat ohne `CultureInfo`: eigene Formatierung für `de-DE` (Standard: `5,2 %`,
   `1.250,5`) und `en` (`5.2%`, `1,250.5`), dazu `scale` und `unit`. Andere Kulturen sind ein
   Fehler mit Liste der gültigen.
4. Farben: `src/pta_documents/design/chart_colors.py` ordnet jeder Rolle eine PTA-Farbe aus
   `colors.py` zu — Reihen `PTA_BLUE`, `DARK_BLUE`, `LIGHT_BLUE`; Referenz `GREY_DARK`,
   Referenzfläche und Gitter `GREY_LIGHT`, Achse `GREY_MID`; Vorsprung `SIGNAL_GREEN`, Rückstand
   `SIGNAL_RED`, gleichauf `GREY_DARK`; Tabellenkopf `PTA_BLUE`, Text `TEXT_WORD`; Fläche weiß;
   Tooltip `TEXT_SLIDES` mit weißer Schrift. Abstufungen je Reihe siehe Frage 1. Die dunkle
   Variante entfällt: PTA-Folien mit Inhalt sind hell.
5. Renderer: `ChartRenderer` (E06-S01) nimmt zusätzlich `financial-chart` → `DrawingGraphic`.
6. Folien: Port von `Pptx/DrawingWriter.cs` (227) nach `generation/pptx/drawing.py` — eine
   Gruppe bearbeitbarer Formen (Rechteck, abgerundetes Rechteck, Ellipse als Vorlagenformen,
   sonst `custGeom`; Text je Zeile in Segoe UI), gesetzt in die Inhaltsfläche von `Nur Titel`.
   E06-S03 nutzt denselben Schreiber für Mermaid.
7. SVG: `to_svg()` über `DrawingSvg` aus E02-S03, Schriftfamilie `Segoe UI, Selawik,
   sans-serif`, Tooltips ohne Skript.
8. Tests `tests/charts/financial/`: die Fälle aus `FinancialChartTests.cs` außer den Brand- und
   Dunkel-Fällen (`OnDarkSlides_*`, `BrandChartColours_*`, `TheBlock_TakesTheSlidesBrand_*`),
   mit `FinancialSamples` als Python-Daten; die acht Schnappschüsse werden mit PTA-Farben neu als
   `*.expected.svg` geschrieben (`tests/expected.py` um SVG erweitert) und einmal vom Menschen
   angesehen; Folie (Gruppe aus Formen) und PDF (Text der Beschriftungen) je ein Test.

## Akzeptanzkriterien

- [ ] Jedes der sechs Diagramme entsteht aus Python-Daten und aus einem JSON-Block gleich.
- [ ] Die übernommenen Tests aus `FinancialChartTests.cs` sind grün; die Schnappschüsse in
      PTA-Farben sind vom Menschen gesehen.
- [ ] Jede Farbe der Diagramme stammt aus `design/colors.py` über `design/chart_colors.py`.
- [ ] Zahlen erscheinen standardmäßig deutsch (`5,2 %`), mit `culture: en` englisch.
- [ ] In Folien ist das Diagramm eine Gruppe bearbeitbarer Formen; im SVG hat jeder Balken,
      Punkt und jede Linie einen Tooltip, und das SVG enthält kein Skript.

## Offene Fragen

1. DocLibs zeichnet je Reihe vier Abstufungen (z. B. Vorjahr hell, Ist kräftig), gemischt aus
   der Reihenfarbe und Weiß. Diese Zwischentöne stehen nicht in der Designanalyse. Dürfen sie
   aus den PTA-Farben errechnet werden (eine Funktion `tint()` in `colors.py`), oder sollen nur
   die festen PTA-Farben vorkommen (dann z. B. Vorjahr `LIGHT_BLUE`, Ist `PTA_BLUE`)?

> (2026-11-07) Aus den PTA-Farben errechnen (`tint()` in `colors.py`).

2. Die Beschriftungen sind in DocLibs englisch („Previous", „Current", „Reference",
   „Projection", „Estimate", „Change", „Overall", „Value"). Vorschlag für die deutschen
   Standardwerte: „Vorjahr", „Ist", „Plan", „Prognose", „Schätzung", „Veränderung", „Gesamt",
   „Wert" — passt das zum Sprachgebrauch der PTA (z. B. „Plan" oder „Ziel" für die Referenz)?

> (2026-11-07) Ja, passt.

## Notizen

- Abhängig von E02-S03 (`Drawing`, `DrawingSvg`) und E06-S01 (Renderer). Im DOCX erscheinen die
  Diagramme über E03-S04 (als Bild aus dem SVG, E06-S04), im PDF über E05-S04.
- Der Formenschreiber für Folien steht hier statt in E06-S03, weil die Finanzdiagramme ihn als
  Erste brauchen.
