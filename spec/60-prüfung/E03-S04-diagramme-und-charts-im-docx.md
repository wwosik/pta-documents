# E03-S04 Diagramme und Charts im DOCX

> Status: in Prüfung
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](../50-entwurf/E03-docx-generator.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Grafiken aus Code-Block-Renderern erscheinen im Word-Dokument an der Stelle ihres Codeblocks:
Zeichnungen (`DrawingGraphic`: Mermaid, Finanzdiagramme) als scharfes Bild (SVG mit PNG-Ersatz),
Charts (`ChartGraphic`) als natives Word-Diagramm aus E06-S01 — beide gleich bemessen, mit
„Abbildung n: …"-Beschriftung und lesbar für den DOCX-Konverter.

## Kontext

- Schnittstellen aus E02-S04 (`ChartGraphic(chart, drawing)`, `DrawingGraphic(drawing)`); bis zu
  dieser Story werfen beide im DOCX „noch nicht unterstützt".
- **Abgrenzung:** den nativen Word-Chart (Chart-Teil `word/charts/chartN.xml` mit eingebetteter
  Arbeitsmappe über python-pptx' `ChartXmlWriter`) schreibt E06-S01, Schritt 4
  (`generation/docx/chart.py`); SVG-Bilder mit PNG-Ersatz und `asvg:svgBlip` in Word kommen aus
  E06-S04 (`SvgImageConverter`, Schriften aus E01-S03). Diese Story verbindet beides mit dem
  `BodyWriter` und legt die Regeln fest, die für beide Grafikarten gleich sind.
- DocLibs hat keinen DOCX-Generator; Vorbild für Größen ist der PPTX-Teil (`DeckWriter.Drawing`:
  Zeichnungen nie vergrößert, höchstens um die Hälfte; Charts höchstens 5:8 hoch) und für Bilder
  E03-S02 (Satzspiegelbreite, höchstens 80 % der Satzspiegelhöhe, `Beschriftung` mit
  `SEQ Abbildung`).

## Vorgeschlagener Ansatz

1. **Verzweigung** in `BodyWriter.block` für `fence` (`generation/docx/writer.py`): Renderer
   fragen (E02-S04, mit Zeile inklusive Front Matter, `format=DOCX`, `dark=False`); dann
   `ImageGraphic` → Bild wie in E02-S04, `ChartGraphic` → `chart.write_chart(...)` aus E06-S01,
   `DrawingGraphic` → Schritt 2.
2. **Zeichnungen** in `generation/docx/drawings.py`: `drawing.to_svg()` (E02-S03) mit
   `SvgOptions(font_family=fonts.CSS_FAMILY)` → `DocumentResource("<info>-<n>.svg",
   "image/svg+xml", …)` → derselbe Weg wie ein SVG-Bild aus Markdown (E06-S04: PNG im doppelten
   Maßstab im `a:blip`, SVG in `asvg:svgBlip`). Größe: natürliche Größe des Drawings
   (1 px = 0,75 pt), auf Satzspiegelbreite und 80 % der Satzspiegelhöhe verkleinert, nie
   vergrößert. Alt-Text = Info-String. Ist kein SVG-Konverter verfügbar (Extra `svg` fehlt),
   wirft der Generator `DocumentConversionError` mit dem Hinweis auf das Extra.
3. **Beschriftung, für Charts und Zeichnungen gleich:** gibt es einen Titel (`ChartSpec.title`
   bzw. ein Absatz `Abbildung: …` direkt nach dem Codeblock, analog zu `Tabelle: …` in E03-S02),
   folgt „Abbildung n: <Titel>" in `Beschriftung`, fortlaufend mit den Bildern; der Titel steht
   dann nicht zusätzlich im Chart. Ohne Titel keine Beschriftung. Grafik und Beschriftung werden
   zusammengehalten (`keepNext`).
4. **Platz:** ein Chart ist so breit wie der Satzspiegel und höchstens 5:8 so hoch, gedeckelt bei
   80 % der Satzspiegelhöhe — dieselbe Regel wie für Zeichnungen, damit Hoch- und Querformat
   gleich wirken (E06-S01 übernimmt diese Maße statt eines eigenen Seitenverhältnisses).
5. **Rücklesen (E07-S02):** ein natives Chart wird eine Markdown-Tabelle seiner Daten (Kopf:
   Kategorie und Reihennamen), ein Bild bleibt ein Bild — damit die Rundreise prüfbar bleibt.
6. **Tests:** Test-Renderer mit festem `Drawing` und festem `ChartSpec` → DOCX in `hoch` und
   `quer`; Zeichnung als Bild mit `svgBlip` und PNG, Größe begrenzt; Beschriftungen fortlaufend
   mit einem gewöhnlichen Bild davor („Abbildung 2"), mit `sprache: en` „Figure"; ohne Extra
   `svg` der erwartete Fehler; Rundreise `diagrams-hoch.roundtrip.expected.md`. Ansicht
   `.tmp/review/diagrams-hoch.docx`.

## Akzeptanzkriterien

- [ ] Ein Mermaid- oder Finanzdiagramm erscheint in Word scharf (SVG) mit PNG-Ersatz in der
      Satzspiegelbreite oder kleiner.
- [ ] Ein `chart`-Block erscheint als natives Word-Diagramm an seiner Stelle, gleich bemessen in
      Hoch- und Querformat.
- [ ] Beide tragen „Abbildung n: …" bzw. „Figure n: …", fortlaufend mit den übrigen Abbildungen.
- [ ] Word öffnet das Ergebnis ohne Reparaturmeldung (Prüfpunkt für den Menschen).

## Offene Fragen

1. Zeichnungen (Mermaid, Finanzdiagramme) in Word: als **Bild** mit SVG und PNG-Ersatz
   (Vorschlag; braucht das Extra `svg`), oder als editierbare Word-Zeichnungsgruppe aus Formen
   (`wpg:wgp`, wie die Formgruppen in PowerPoint; ohne Extra, aber deutlich mehr Aufwand)?

> (2026-11-07) Als Bild (SVG mit PNG-Ersatz, Extra `svg`).

## Notizen

- Abhängigkeiten: E02-S03, E02-S04, E06-S01 (Word-Chart), E06-S04 (SVG in Word), E01-S03.
- E06-S01 nennt für Word das Seitenverhältnis 640:380 und 10 pt; Schritt 4 hier schlägt vor,
  es an die Regel für Zeichnungen anzugleichen — beim Annehmen beider Pläne abstimmen.
- (2026-11-07, E02-S04) Einstieg: `BodyWriter.block` (Fall `fence`) ruft `self.draw(token)` →
  `code_blocks.draw`, das heute für `DrawingGraphic`/`ChartGraphic` wirft; hier stattdessen
  zeichnen (`draw` dann den Graphic-Typ zurückgeben lassen). `ImageGraphic` setzt
  `place_picture` ohne Beschriftung.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: `generation/docx/writer.py` (`BodyWriter.draw` liefert jede
Grafikart, neu `graphic_figure`, `chart_size`, `_figure_caption`, `insert_picture` als zweiter
Teil von `place_picture`), neu `generation/docx/drawings.py` (`svg_resource`, `convert`),
`generation/docx/chart.py` (`add_chart` nimmt die Höhe), `design/word.py`
(`FIGURE_HEIGHT_SHARE`, `CHART_HEIGHT_RATIO`), `diagrams/mermaid.py` (Word-Zweig entfernt),
Authoring-Guide-Texte in `charts/renderer.py` und `diagrams/mermaid.py`,
`conversions/docx.py` (`_render_chart`: Diagramm → Tabelle). Tests: neu
`tests/generation/docx/test_drawings.py` (14 Fälle, Rundreise
`samples/diagrams-hoch.roundtrip.expected.md`, Ansicht `.tmp/review/diagrams-hoch.docx` und
`diagrams-quer.docx`); angepasst: `docx/test_chart.py` (Höhe 5:8), `docx/test_notes.py`
(Renderer explizit; Beispiele mit Mermaid ohne mmdc übersprungen),
`common/test_renderers.py` und `pptx/test_drawing.py` (der Fall „Word setzt noch keine
Zeichnungen" entfällt bzw. wird „Word setzt sie als Bild"), `diagrams/test_mermaid.py` (Word
zeichnet jetzt, mit Ersatz-`mmdc`), `samples/test_funktionen.py` (verlangt im Bericht einen
`financial-chart` und eine `Abbildung: …`-Beschriftung nach einer Grafik). Beispiele:
`samples/funktionen/funktionen-bericht.md` (Beschriftung per Absatz, Abschnitt
„Finanzdiagramme"), neu `samples/funktionen/mermaid-bericht.md`, README und Rundreisen. Doku:
`docs/verwendung.md` (neuer Abschnitt „Grafiken in Word (E03-S04)", Korrekturen an Renderern,
Charts, Finanzdiagrammen, Mermaid, Zeichenmodell, Hinweisen), `docs/anleitung.md`,
`docs/ki-anleitung.md`; `ai/Gedächtnis.md` (neuer Eintrag, veraltete Aussagen zu Word und
`code_blocks.draw` korrigiert). Keine neue Abhängigkeit.

### Entscheidungen

- **Zeichnungen als Bild** (Frage 1): `drawing.to_svg` mit `SvgOptions()` (Standardfamilie
  `Segoe UI, Selawik, sans-serif`, lazy aus `design.fonts`, damit der Kern das Modul nicht
  lädt) → `DocumentResource("<sprache>-<n>.svg", "image/svg+xml")` → die Bildkonverter der
  Optionen (E06-S04) → PNG im doppelten Maßstab mit `asvg:svgBlip`. Natürliche Größe
  (1 px = 9525 EMU), verkleinert auf Satzspiegelbreite und 80 % der Satzspiegelhöhe, nie
  vergrößert; Alt-Text = Info-String. Der bisherige Bildweg wurde dafür in
  `place_picture` (konvertiert) und `insert_picture` (setzt) geteilt — kein zweiter Bildcode.
- **Ohne SVG-Konverter** ein `DocumentConversionError` wie im Plan:
  `Line N: The `<sprache>` block is a drawing, which Word places as an SVG image with a PNG
  beside it; that needs the extra 'svg' (pip install 'pta-documents[svg]'). …` — bzw. „no image
  converter takes SVG (DocxOptions.image_converters)", wenn das Extra da ist, die Konverter
  aber abgeschaltet sind.
- **Beschriftung:** Ein Absatz, der mit `Abbildung:` oder `Figure:` (bzw. dem Wort der
  Dokumentsprache) beginnt und **direkt** nach dem Zaun auf derselben Token-Ebene steht, wird
  „Abbildung n: …" in „Beschriftung" (wie `Tabelle: …`); er geht dem `title` eines Charts vor.
  Ohne beides keine Beschriftung. Grafikabsatz mit `keepNext`, wenn Beschriftung oder Quelle
  folgt. Die Regel gilt auch für `ImageGraphic` (Bilder eines Renderers), damit alle drei
  Grafikarten gleich beschriftet werden.
- **Chartgröße** (Plan Punkt 4, Notiz zu E06-S01): Satzspiegelbreite, Höhe 5:8 der Breite,
  gedeckelt bei 80 % der Satzspiegelhöhe — im Hochformat 16,6 × 10,4 cm, im Querformat
  25,3 × 11,4 cm (der Deckel greift). Das bisherige 640:380 aus E06-S01 entfällt.
- **Mermaid in Word:** Der Word-Zweig des `MermaidRenderer` (`RendererUnavailableError` „Word
  does not draw Mermaid diagrams yet") ist entfernt (Offener Punkt von E06-S03); mmdc zeichnet
  für Word mit der Word-Textfarbe (`init_directive` kannte das Format schon).
- **Rücklesen** (Plan Punkt 5): Der DOCX-Konverter liest `c:chart` aus dem Wertecache des
  Chart-Teils (`c:cat`/`c:val`, `c:pt`) als Markdown-Tabelle: Kategorien in der ersten Spalte,
  dann je Reihe eine Spalte; Zahlen wie im `chart`-Block (`13` statt `13.0`, Dezimalpunkt),
  leere Werte leer. Zeichnungen kommen als Bild (PNG) zurück.
- **Beispiele:** Finanzdiagramm und Beschriftung per Absatz im großen Bericht (läuft immer);
  Mermaid in einem eigenen kleinen `mermaid-bericht.md`, damit der große Bericht ohne
  mermaid-cli geprüft bleibt (wie bei der Präsentation in E06-S03).

### Abweichungen

- Plan Punkt 1 nennt `chart.write_chart(...)`; die Funktion aus E06-S01 heißt `add_chart` und
  nimmt jetzt Breite **und** Höhe.
- Plan Punkt 6 „mit `sprache: en` Figure" ist getestet; „ohne Extra `svg`" wird durch
  Abschalten der Konverter und Ersetzen von `svg_available` nachgestellt (das Extra ist in der
  Testumgebung installiert).
- Der PPTX-Konverter liest Diagramme weiterhin nicht zurück (der Plan nennt nur E07-S02/Word).

### Warnungen

- **Kopf der Kategorienspalte leer:** Das Chart-XML von python-pptx kennt den Kopf der ersten
  CSV-Spalte (`Quartal`) nicht, `ChartSpec` speichert ihn nicht. Statt ein Wort wie
  „Kategorie" zu erfinden, bleibt die Kopfzelle der Rundreise-Tabelle leer.
- **Absatz geht vor Titel:** Hat ein `chart`-Block einen `title` **und** folgt ein Absatz
  `Abbildung: …`, erscheint der `title` in Word gar nicht (er steht in Word nie im Diagramm). Der
  Plan regelt den Fall nicht; gewählt wurde, dass der ausdrücklich für das Dokument geschriebene
  Absatz gilt. Kein Hinweis dazu.
- **Fehlendes Extra `svg` bricht ab** (wie im Plan), auch bei Mermaid — während ein fehlendes
  mermaid-cli den Block nur als Code mit Hinweis stehen lässt. Wer mermaid-cli, aber nicht das
  Extra `svg` installiert, bekommt also einen Fehler statt Code. `./run.sh setup` installiert
  beides.
- **Querformat:** Charts sind dort wegen des 80-%-Deckels flacher als 5:8 (≈ 2,2:1); „gleich
  bemessen" heißt hier: nach derselben Regel.
- **Ohne Office geprüft:** Dass Word das Bild mit `svgBlip` und das Diagramm in der neuen Größe
  ohne Reparaturmeldung öffnet, ist nicht geprüft (kein Word/LibreOffice auf der Maschine);
  geprüft sind Aufbau, Öffnen mit python-docx und die Rundreise. Der Bildweg ist derselbe wie
  für SVG-Bilder aus E06-S04.
- `check` zählt in Word-Berichten weiterhin nur Markdown-Bilder als Abbildungen (Seitenschätzung);
  Grafiken aus Codeblöcken zählen nicht mit.

### Prüfpunkte

- `.tmp/review/diagrams-hoch.docx` und `diagrams-quer.docx` in Word öffnen
  (Akzeptanzkriterium 4): keine Reparaturmeldung; Bild, Zeichnung, Chart, breite Zeichnung;
  „Abbildung 1–3" fortlaufend, das Chart im Querformat flacher.
- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitte „Diagramme aus Daten"
  (Abbildung 7–9, „Abbildung 9: Aufträge je Region" aus dem Absatz) und „Finanzdiagramme"
  (Abbildung 10, scharf beim Vergrößern); Abbildungsverzeichnis zählt alles mit.
- Mit eingerichtetem mermaid-cli (`PUPPETEER_EXECUTABLE_PATH`,
  `PTA_DOCUMENTS_PUPPETEER_CONFIG`): `.tmp/review/funktionen/mermaid-bericht.docx` — drei
  Diagramme, zwei mit Beschriftung; `./run.sh test` ohne übersprungene Mermaid-Fälle.
- `./run.sh test tests/generation/docx/test_drawings.py tests/generation/docx/test_chart.py`.

### Offene Punkte

- **PDF** (E05-S04) setzt Zeichnungen und Charts später; die Beschriftungsregel
  (`Abbildung: …` nach dem Block) sollte dort gleich gelten.
- Die Implementierungsnotizen von E06-S02/E06-S03 nennen Word noch als offen; mit dieser Story
  erledigt (dort nicht geändert, weil es fremde Story-Dateien sind).
- `code_blocks.draw` und `code_blocks.unsupported` nutzt derzeit kein Generator mehr; sie
  bleiben für den PDF-Generator, solange er nicht alle Grafikarten setzt.
