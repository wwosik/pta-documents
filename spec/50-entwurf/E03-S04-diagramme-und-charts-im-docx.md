# E03-S04 Diagramme und Charts im DOCX

> Status: Entwurf
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](E03-docx-generator.md)
> Milestone: [M03 Grafik, Diagramme und Charts](M03-grafik-diagramme-und-charts.md)

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
