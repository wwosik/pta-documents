# E06-S01 `chart`-Blöcke

> Status: in Prüfung
> Epic: [E06 Diagramme und Charts](../50-entwurf/E06-diagramme-und-charts.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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
- (2026-11-07, E02-S04) Standard eintragen in `generation/common/renderers.default_renderers()`
  (heute leer; die Optionen nutzen es als `default_factory`). `ChartSpec`/`ChartSeries`/
  `ChartKind` liegen schon in `charts/spec.py`; `ChartGraphic.drawing` ist bis E02-S03 als
  `object` typisiert. `code_blocks.draw` wirft heute für `ChartGraphic` „does not support yet".
- (2026-11-07, E04-S04) Die Platzierung auf Folien steht: `DeckParser` macht aus einem
  `ChartGraphic` ein `model.Chart`, wählt `Titel und Diagramm` / `Titel, Text und Diagramm` /
  `Titel, Diagramm und Text` / `Titel und zwei Diagramme` (auch `::: columns` mit genau zwei
  Charts) als `ChartSlide`, `kinds.write_chart_slide` füllt Titel 12, Einheit 13, Quelle 14
  (`ChartSpec.source` ist neu) und setzt den Chart über `generation/pptx/chart.insert_chart`
  (python-pptx `insert_chart`, Reihenfarben aus `ChartSpec.colors`, Legende unten ab zwei
  Reihen, kein Titel im Chart). Hier fehlen noch: der `chart`-Renderer (Eintrag in
  `default_renderers`), der PTA-Diagrammstil in `chart.py` (Lücke, Achsen, Schrift) und Word.
  Charts auf Flow-Folien sind ein Fehler (`flow_parser.FlowReader.items`).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Paket `src/pta_documents/charts/` (`parser.py`,
`drawing.py`, `renderer.py`, Re-Exporte in `__init__.py`; `spec.py` unverändert),
`generation/common/native_chart.py` (Typ, Daten und PTA-Stil der nativen Diagramme für beide
Formate), `generation/pptx/chart.py` (nutzt den Stil), neu `generation/docx/chart.py` und
`BodyWriter.draw`/`chart_figure` in `generation/docx/writer.py`, `colors.tint` in
`design/colors.py`, `ChartRenderer` in `renderers.default_renderers()`. Tests
`tests/charts/test_parser.py`, `test_drawing.py`, `test_renderer.py`,
`tests/generation/pptx/test_chart.py`, `tests/generation/docx/test_chart.py` (49 Fälle);
angepasst: `test_renderers.py` (Word wirft nicht mehr für Charts), `docx/test_notes.py`
(`code-not-drawn` jetzt an einem `mermaid`-Block), `pptx/test_kinds.py` (ohne Renderer
ausdrücklich `code_block_renderers=()`; der Test „Charts in Word folgen mit E06" entfällt — er
scheiterte ohnehin am fehlenden `titel:`, nicht am Chart). `tests/samples/test_funktionen.py`
verlangt jetzt jede Chart-Art, jede Einstellung und beide Trennzeichen. Doku:
`docs/verwendung.md` (neuer Abschnitt „Charts (E06-S01)", Diagramm-Layouts, Renderer, Hinweise),
`docs/anleitung.md` (Abschnitt „Diagramme aus Daten", Word-Tabelle), `docs/ki-anleitung.md`
(Abschnitt „Diagramme aus Daten"); Beispiele in `samples/funktionen/` (Bericht: Abschnitt
„Diagramme aus Daten" mit drei Charts; Präsentation: Kapitel „Diagramme" mit allen vier
Diagrammlayouts) samt README und erneuerten Rundreisen; Eintrag in `ai/Gedächtnis.md`. Keine
neue Abhängigkeit: xlsxwriter kommt mit python-pptx.

### Entscheidungen

- **Quelle des Ports:** `ChartParser.cs`, `ChartDrawing.cs`, `ChartRenderer.cs`,
  `Pptx/ChartWriter.cs`, `ChartTests.cs` und `AuthoringGuide/Charts.md` aus
  `~/mvv/vt-tools-libs` (DocLibs selbst liegt nicht auf der Maschine). Die dortige Einstellung
  `culture` entfällt: Zahlen schreibt die Zeichnung in der Dokumentsprache (`sprache:`), das
  Eingabeformat bestimmt das Trennzeichen (Antwort auf Frage 2).
- **Einstellungen englisch** (Frage 1): `type`, `title`, `unit`, `source` (neu, für die
  Quellenangabe), `stacked`. Schlüssel und Typwerte ohne Groß/Klein; `stacked` nur
  `true`/`false`.
- **Trennzeichen** (Frage 2): Enthält die Kopfzeile außerhalb von Anführungszeichen ein `;`,
  gilt `;` mit Dezimalkomma, sonst `,` mit Dezimalpunkt. Eine Zahl ist nur
  `[+-]Ziffern[Dezimalzeichen Ziffern][e±n]` — kein Tausendertrennzeichen, kein `nan`/`inf`,
  kein Unterstrich (Pythons `float()` nähme all das an).
- **Fehlerzeile:** Die Meldung nennt die Dokumentzeile, in der der Fehler steht (Einstellung,
  Kopf- oder Datenzeile), nicht nur die des Zauns; nur „zu wenige Daten" nennt den Zaun.
  Format wie im Repo üblich: `Line N: The chart block cannot be drawn: …`. Der Parser wirft
  `ChartBlockError(ValueError)`; `renderers.render` macht daraus wie für jeden Renderer eine
  `DocumentConversionError` im Format des Generators (Ursache in `__cause__`).
- **Ein Stil für beide Formate:** `native_chart.apply_style` arbeitet auf einem python-pptx-
  `Chart`; Word parst das Chart-XML von python-pptx (`CategoryChartData.xml_bytes`) und wendet
  denselben Stil an. Stil wie `ChartWriter.cs` und Plan: Lücke 60 %, keine Teilstriche,
  Kategorienachse 0,5 pt `GREY_MID`, Gitter 0,5 pt `GREY_LIGHT`, keine Werteachsenlinie,
  Werteachse ab 0 (bzw. darunter) für Balken und Flächen, Legende unten ab zwei Reihen,
  Diagrammfläche ohne Füllung und Rahmen, eckig; Linien 2,25 pt mit Kreismarken (6 pt).
  PowerPoint 14 pt Segoe UI Light `404040`, Word 10 pt Segoe UI `000000` — für **alle** Texte
  des Diagramms (Achsen und Legende), über `c:txPr` des Diagramms.
- **Word:** Teil `/word/charts/chartN.xml` (Beziehung `…/chart` vom Dokument), Arbeitsmappe
  `/word/embeddings/Microsoft_Excel_WorksheetN.xlsx` (Beziehung `…/package` vom Chart,
  `c:externalData` mit `c:autoUpdate val="0"`), `wp:inline` über die Satzspiegelbreite, Höhe
  380/640 davon, `docPr`-ID über `part.next_id`. Die Einheit steht als waagrechter Titel an der
  Werteachse (wie `ChartWriter.cs`), der Titel nicht im Diagramm, sondern als Beschriftung
  „Abbildung n: Titel" darunter.
- **Mit `layout="…"`** gesetzte Charts (kein Platzhalter für Titel/Einheit) zeigen Titel und
  Einheit im Diagramm selbst.
- **Zeichnung:** Port von `ChartDrawing.cs` (640 × 380 px, Titel 15 px fett, Beschriftung
  11 px). Textfarbe nach Format: `TEXT_WORD` (DOCX, später PDF), `TEXT_SLIDES` (PPTX), `WHITE`
  bei `dark`. Die Quelle steht zusätzlich zu DocLibs unten links.
- `ChartRenderer` ist eine eingefrorene Dataclass (Options-Vergleich mit `default_renderers()`)
  und wird nicht aus `pta_documents.charts` re-exportiert (Importzirkel mit
  `generation.common.renderers`, das `charts.spec` braucht).
- Beispiele (Frage 3): Charts nutzen die Diagrammlayouts aus E04-S04; die Präsentation zeigt alle
  vier.

### Abweichungen

- **Warnung (überlappende Flächen):** DocLibs mischt in der Zeichnung die Reihenfarbe mit Weiß
  (55 %), nativ aber volle Farbe. Hier gilt die aufgehellte Farbe in **beiden** Ausgaben, damit
  hintere Flächen sichtbar bleiben und Zeichnung und natives Diagramm gleich aussehen. Die
  Mischung liegt als `colors.tint` in `design/colors.py`; außer den Akzenten und diesen
  Aufhellungen kommen keine Farben vor (Test). Gestapelte Flächen und alle anderen Arten nutzen
  die Akzente unverändert.
- **Warnung (Info-String):** ```` ```chart bar ```` ist ein Fehler („… after ```chart is not
  read; write settings such as 'type: line' in the block …"), statt die Wörter still zu
  übergehen — sonst glaubte der Schreiber, er habe den Typ gesetzt.
- **Warnung (doppelte Einstellung):** eine Einstellung zweimal ist ein Fehler (DocLibs: die
  letzte gilt).
- **Warnung (Quelle in Word):** Der Plan sagt nichts zu `source` in Word. Gewählt: ein eigener
  Absatz in der Formatvorlage „Beschriftung" **ohne** Nummer direkt unter der Beschriftung
  (bzw. dem Diagramm, wenn es keinen Titel gibt). Der DOCX-Konverter liest ihn als normalen
  Absatz zurück.
- Ein ganzer Kommentar `# …` als Zeile ist in den Einstellungen erlaubt (DocLibs nur `` # ``
  nach einer Einstellung).
- Die PPTX-Diagramme auf dunklen Folien gibt es nicht: `.dark` macht eine Flow-Folie, auf der
  ein Chart ein Fehler ist (E04-S04). Nur die Zeichnung kennt `dark`.

### Warnungen

- **Warnung:** Ohne Office und OOXML-Validator ist nicht geprüft, dass Word das Diagramm öffnet
  und „Daten bearbeiten" die Arbeitsmappe findet; geprüft sind Aufbau (Teile, Beziehungen,
  Content-Types, `c:externalData`, `wp:inline`), Öffnen mit python-docx und die Rundreise. Das
  Chart-XML ist das von python-pptx, das PowerPoint seit Jahren öffnet; Word liest dasselbe
  Schema.
- **Warnung:** Die Konverter (Word/PowerPoint → Markdown) lassen Diagramme weg — in den
  Rundreisen stehen nur Beschriftung, Quelle bzw. die Platzhaltertexte. Ein Rückweg zum
  `chart`-Block (aus dem Daten-Cache des Chart-XML) wäre eine Ergänzung für E07.
- Tests, die einen ```` ```chart ````-Block mit Fantasieinhalt als Code erwarten, müssen jetzt die
  Renderer abschalten — der `ChartRenderer` ist standardmäßig an und wirft bei ungültigen Daten.

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-praesentation.pptx` (Kapitel „Diagramme", vier Folien) und
  `.tmp/review/chart-orders.pptx` in PowerPoint öffnen: Diagramme in den Diagrammplatzhaltern,
  Titel/Einheit/Quelle in deren Feldern, Reihen PTA-Blau, Dunkelblau, Hellblau; Rechtsklick →
  „Daten bearbeiten" öffnet die Tabelle (Akzeptanzkriterium 2).
- `.tmp/review/funktionen/funktionen-bericht.docx` (Abschnitt „Diagramme aus Daten", Abbildung 7
  und 8) und `.tmp/review/chart.docx` in Word öffnen: Diagramm über die Textbreite, Achsen 10 pt
  Segoe UI, „Daten bearbeiten" funktioniert, Abbildungsverzeichnis zählt die Diagramme mit.
- `.tmp/review/charts.html`: die Zeichnungen (Grundlage des PDF) im Browser.
- `./run.sh test tests/charts tests/generation/pptx/test_chart.py tests/generation/docx/test_chart.py`.

### Offene Punkte

- **PDF** (Plan Punkt 5): die Zeichnung ist fertig und getestet (Titel als Text im SVG); setzen
  wird sie der PDF-Generator mit E05-S04. — *(2026-11-08) Erledigt in E05-S04.*
- Der Test „Pdfs_DrawTheChart" aus `ChartTests.cs` folgt mit E05; „OpenXmlValidator" hat in
  Python kein Gegenstück.
