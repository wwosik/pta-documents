# E06-S02 Finanzdiagramme

> Status: in Prüfung
> Epic: [E06 Diagramme und Charts](../50-entwurf/E06-diagramme-und-charts.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Paket `src/pta_documents/charts/financial/` (`model.py`,
`options.py`, `canvas.py`, `development.py`, `growth_by_row.py`, `actual_vs_reference.py`,
`growth_trend.py`, `two_year.py`, `summary_table.py`, `json_block.py`, `__init__.py` mit
`draw`, `to_svg`, `category_colors`, `parse`, `to_json`), `design/chart_colors.py`
(`FinancialChartColors`, `SeriesColors`, `FINANCIAL`), `financial-chart` im `ChartRenderer`
(`charts/renderer.py`, mit Abschnitt `### Finanzdiagramme` im Authoring Guide), neu
`generation/pptx/drawing.py` (Formengruppe), Modell-Visual `Diagram` in
`generation/pptx/model.py`, Parser/Writer/Flow-Parser der Folien, `conversions/pptx.py`
(überspringt `Drawing`-Gruppen). Tests: `tests/charts/financial/` (`figures.py` als Port von
`FinancialSamples.cs`, `test_financial.py`, `test_json_block.py`, acht Schnappschüsse
`samples/*.expected.svg`) und `tests/generation/pptx/test_drawing.py` — 77 Fälle; angepasst:
`tests/charts/test_renderer.py` (`financial-chart` gehört jetzt dem Renderer),
`tests/generation/common/test_renderers.py` (nur Word wirft noch für Zeichnungen),
`tests/samples/test_funktionen.py` (verlangt im Deck jeden Typ und jede Option). Doku:
`docs/verwendung.md` (Abschnitt „Finanzdiagramme (E06-S02)", Zeichnungen auf Folien),
`docs/anleitung.md` (Abschnitt „Finanzdiagramme"), `docs/ki-anleitung.md`; Beispiele im Kapitel
„Finanzdiagramme" von `samples/funktionen/funktionen-praesentation.md` (sechs Folien) samt
README und erneuerter Rundreise; Eintrag in `ai/Gedächtnis.md`. Keine neue Abhängigkeit.

### Entscheidungen

- **Quelle des Ports:** `FinancialChart*.cs`, `FinancialCanvas.cs`, die sechs `*Drawing.cs`,
  `FinancialChartTests.cs`, `FinancialSamples.cs` und `Pptx/DrawingWriter.cs` aus
  `~/mvv/vt-tools-libs` (DocLibs selbst liegt nicht auf der Maschine). Geometrie, Regeln und
  Wortlaut sind 1:1 übernommen; ein Abgleich der SVGs mit den DocLibs-Schnappschüssen zeigt nur
  die Farben, die deutschen Wörter und das Leerzeichen vor `%` als Unterschiede.
- **Farben** (Frage 1): Abstufungen je Reihe über `colors.tint` wie in DocLibs (Füllung 18 %,
  blass 8 %, kräftig 65 %, Linie die Farbe selbst). Rollen wie im Plan, dazu: Band
  `tint(GREY_LIGHT, 0.5)`, Gesamtspalte Kopf `DARK_BLUE` und Fläche `tint(PTA_BLUE, 0.1)`,
  gedämpfter Text `GREY_DARK`, Hintergrund der Beschriftungen weiß. Kategorien der
  Zwei-Jahres-Linien: die Akzente in der Reihenfolge des Epics.
- **Beschriftungen** (Frage 2): deutsch *Vorjahr, Ist, Plan, Prognose, Schätzung, Veränderung,
  Gesamt, Wert*; die festen Wendungen deutsch wie in DocLibs (`ggü.`, `Pro Monat`, `Kumuliert`,
  `Ist-Werte bis …`, `Pp.`).
- **Zahlen:** eigenes Format ohne Kultur-Bibliothek (`options.format_decimal`), kaufmännisch
  gerundet, Tausender gruppiert (`1.250,5`), deutsch mit Leerzeichen vor `%` und `Pp.` (`5,2 %`,
  `-1,2 Pp.`) wie im Plan, englisch ohne (`5.2%`, `-1.2pp`). Gültige Kulturen: `de`, `de-DE`,
  `en`, `en-US`, `en-GB` (ohne Groß/Klein); andere sind ein Fehler mit dieser Liste.
- **Standardkultur im Renderer = Dokumentsprache** (`sprache: en` → englisch), `culture` im
  Block geht vor; ohne Renderer (`FinancialChartOptions()`) `de-DE`.
- **JSON-Leser:** ein eigener kleiner Parser statt `json`, weil nur so jede Fehlermeldung die
  Zeile des Werts bzw. Schlüssels nennen kann und Kommentare und ein Komma am Ende wie in
  DocLibs gehen. Fehlerformat wie bei `chart`: `Line N: The financial-chart block cannot be
  drawn: …` (N = Zaunzeile + Zeile im Block); Fehler in den Daten (z. B. „has 2 values for 1
  months") nennen die Zaunzeile. Schlüssel = Feldname in camelCase, Aufzählungswerte ohne
  Groß/Klein (`"growth"`, `"Growth"`). `to_json` schreibt einen Block, den `parse` zum
  gleichen Diagramm zurückliest — Grundlage des Tests „Python-Daten und Block zeichnen gleich".
- **Folien:** Das Diagramm ist ein Visual wie eine Tabelle: Inhaltsfläche von `Nur Titel`, mit
  Text davor `Titel und Text`, Text danach als Textfeld darunter; oben mittig, verkleinert, nie
  vergrößert (wie `DeckWriter.Drawing`). Text in Segoe UI (`design.slides.HEADING_FONT`, wie im
  Plan), Code in Consolas; die Schriftgröße schrumpft mit der Gruppe. Die Gruppe heißt
  `Drawing <id>`, ihr Alternativtext ist der Info-String.
- **Textfarbe nach Format** wie bei den `chart`-Blöcken: `TEXT_WORD` (Word, SVG, später PDF),
  `TEXT_SLIDES` auf Folien.
- **Schnappschüsse und Testdaten deutsch** (`figures.py`: Monate, Titel, Regionen übersetzt,
  `Mio.` statt `M`), damit der Mensch sie so sieht, wie die PTA sie zeigen würde; der
  englische Fall ist eigens getestet. DocLibs zeichnete seine Beispiele in `pl-PL`.

### Abweichungen

- Die Brand- und Dunkel-Fälle (`OnDarkSlides_*`, `BrandChartColours_*`,
  `TheBlock_TakesTheSlidesBrand_*`) entfallen wie geplant; dazu ein Test, dass das Diagramm auf
  weißer Fläche in der Textfarbe steht.
- `tests/expected.py` brauchte keine Erweiterung: `assert_matches_expected` vergleicht beliebigen
  Text, die SVG-Schnappschüsse nutzen es direkt (`PTA_DOCUMENTS_UPDATE_EXPECTED=1` erneuert sie).
- Kein PDF-Test (Plan Punkt 8): es gibt noch keinen PDF-Generator (E05). Die Texte der
  Beschriftungen sind im SVG-Schnappschuss und in der Formengruppe geprüft.
- Kein `OpenXmlValidator`: in Python gibt es kein Gegenstück; der Folientest prüft Aufbau,
  eindeutige Shape-IDs und Inhalte.

### Warnungen

- **Pflichtfelder im JSON:** DocLibs (System.Text.Json) setzt fehlende Konstruktorparameter
  stillschweigend auf 0/leer; hier ist jedes Feld ohne Standardwert Pflicht (z. B. `label`,
  `change` eines Monats, die neun Zahlen eines `DevelopmentMonth`, ein Monat ohne Ist-Wert
  braucht `"current": null`). Vorsichtiger, aber strenger als das Original.
- **`scale` und `width` müssen größer als 0 sein**, `tolerance` und `restShare` mindestens 0 —
  DocLibs nahm einen Maßstab ≤ 0 stillschweigend als 1.
- **Hervorhebung einer Zeile** (`emphasised`) ist die kräftige Abstufung der ersten Reihe, nicht
  wie in DocLibs die Erfolgsfarbe: Grün gehört nach den Regeln nur an Zahlen; der Plan nennt
  keine Farbe dafür.
- **Kategorienfarben:** die sechste Akzentfarbe `GREY_LIGHT` (`E6E6E6`) ist als Linie auf Weiß
  kaum zu sehen, und `PTA_BLUE`/`DARK_BLUE` liegen nah beieinander; DocLibs ordnet seine
  Kategorienfarben so, dass benachbarte sich stark unterscheiden. Bei sechs Kategorien bitte
  ansehen (`two-year.expected.svg` hat fünf).
- **Dunkle Folien:** Ein `financial-chart` auf einer `{.dark}`-Folie ist ein Fehler (Flow-Folie,
  wie bei `chart`); die dunkle Variante entfällt laut Plan. Ohne Flow-Folie gäbe es keinen
  dunklen Hintergrund.
- **Schriftgröße auf Folien:** Ein 560 px breites Entwicklungsdiagramm wird auf die Höhe der
  Inhaltsfläche verkleinert (Titel ≈ 9,5 pt, Beschriftungen ≈ 6–7 pt); das ist DocLibs-Verhalten
  („nie vergrößert"), auf der Folie aber klein.

### Prüfpunkte

- Die acht Schnappschüsse ansehen (Akzeptanzkriterium 2):
  `tests/charts/financial/samples/*.expected.svg` bzw. `.tmp/review/financial/*.svg` im Browser — Farben, deutsche Zahlen, Tooltips beim
  Überfahren.
- `.tmp/review/funktionen/funktionen-praesentation.pptx` (Kapitel „Finanzdiagramme", sechs
  Folien) und `.tmp/review/financial-chart.pptx` in PowerPoint öffnen: keine
  Reparaturmeldung, die Gruppe lässt sich auflösen und jede Form bearbeiten, Text in Segoe UI an
  der richtigen Stelle (die Textfelder sind geschätzt breit, ohne Umbruch).
- `./run.sh test tests/charts tests/generation/pptx/test_drawing.py`.

### Offene Punkte

- **Word** (E03-S04): `DrawingGraphic` als SVG-Bild mit PNG-Ersatz; bis dahin bricht Word mit
  „… does not support yet" ab, darum stehen die Beispiele nur in der Präsentation.
- **PDF** (E05-S04): Zeichnung und Texte sind fertig, das Setzen folgt mit dem PDF-Generator;
  dort auch der Test „InAPdf_TheChartIsDrawnWithItsText".
- Der Formenschreiber `generation/pptx/drawing.py` ist für Mermaid (E06-S03) bereit
  (`round_joins`, `even_odd` wird von PowerPoint-`custGeom` nicht unterschieden — für
  Mermaid-Pfade mit Löchern dort prüfen).
