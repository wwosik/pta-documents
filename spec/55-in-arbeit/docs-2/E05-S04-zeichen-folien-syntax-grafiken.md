# E05-S04 Fehlende Zeichen, Folien-Syntax, Diagramme und Charts im PDF

> Status: in Bearbeitung (docs-2)
> Epic: [E05 PDF-Generator im PTA-Design](../../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../../50-entwurf/M05-pdf.md)

## Zusammenfassung

Drei Ergänzungen der Layout-Engine aus DocLibs: Zeichen, die der Schrift fehlen, werden gemeldet
oder über `replace_unsupported` ersetzt; die Folien-Syntax wird angenommen und schlicht gezeigt;
Zeichnungen der Code-Block-Renderer (Mermaid, Charts) und konvertierte Bilder (SVG) werden als
Vektoren bzw. Bilder gesetzt.

## Kontext

- DocLibs `LayoutEngine.cs`: `Supported`, `CheckGlyphs`, `Lacks`, `TextElements` (Graphem-
  Cluster über `StringInfo`), `Visible` (Steuerzeichen weg), `Drawing`, `DrawingScale`, `Label`
  (Beschriftungen bis 70 % verkleinern); `MarkdownParser.cs`: Container (`LayoutSyntax.
  CheckContainer`, `---` in `columns` fällt weg), Alerts als Zitat mit fetter Art, `==mark==`,
  `[Wörter]{.success}` (`ColouredWords`), Heading-Attribute werden geprüft und entfernt,
  `Render(fenced)` fragt die Code-Block-Renderer, `Image(resource, scale)` die Bildkonverter.
- Tests: `LayoutTests.cs` (Zeichen- und Zeichnungsfälle, 13), `PdfGeneratorTests.cs`
  (`MissingGlyph_*`, `ReplaceUnsupported_*`, `CodeBlockRenderers_*`,
  `Drawings_AreVectorPaths_WithCurvesDashesAndColours`), `SlideLayoutSyntaxTests.cs` (7) mit
  `layouts.md` und `layouts-neutral.roundtrip.expected.md`.
- Voraussetzungen: Folien-Syntax-Parser (E02-S02), Zeichenmodell `Drawing` (E02-S03),
  Renderer- und Konverter-Schnittstellen (E02-S04). Die Renderer selbst kommen aus E06.

## Vorgeschlagener Ansatz

1. `generation/common/graphemes.py`: Zerlegung in Graphem-Cluster ohne neue Abhängigkeit —
   Grundzeichen mit folgenden kombinierenden Zeichen (`unicodedata.combining`),
   Variationsselektoren, Emoji-Modifikatoren `U+1F3FB`–`U+1F3FF`, ZWJ-Folgen, Regional-Indicator-
   Paare und Tag-Folgen. Testfälle aus DocLibs: `👍🏽`, `❤️`, `👨‍👩‍👧` je ein Cluster.
2. `layout.py`: `supported(runs, face)` wie DocLibs — ohne `replace_unsupported` wirft jedes
   fehlende Zeichen `DocumentConversionError(PDF, "The character 'x' (U+…) is not in the font
   (…)")`; mit Hook wird je Cluster einmal gefragt, und auch der Ersatz muss in der Schrift
   stehen. Geprüft werden Absätze, Überschriften (Lesezeichen zeigen den Ersatz, der Anker bleibt),
   Tabellen, Code (Monospace), Kopf- und Fußzeile (E05-S03) und der Titel in den Metadaten.
   Zeichen außerhalb der BMP werden als ein Codepunkt genannt (`U+1F600`).
3. Zeilenumbruch und Code brechen zu lange Wörter nur zwischen Clustern.
4. **Folien-Syntax** (`parser.py`): Container `cards`, `rows`, `panel`, `statement`, `columns`
   werden geprüft wie in den Folien und zeigen ihren Inhalt nacheinander, ohne die `---` von
   `columns`; Heading-Attribute (`{.dark kicker="…"}`, `{layout="…"}`) werden geprüft und
   entfernt; Alerts werden ein Zitat, das mit der Art fett beginnt — deutsch über
   `GeneratedTexts` („Hinweis", „Tipp", „Wichtig", „Warnung", „Vorsicht"; englisch wie DocLibs),
   gleich wie im DOCX (E03-S03); `[Wörter]{.success}` fett in `STATUS_COLORS`; Status-Labels
   (`status.*`) werden geprüft und als Text gezeigt; `==mark==` siehe Frage 1.
5. **Zeichnungen** (`layout.py`): ein `DrawingGraphic` oder `ChartGraphic` eines Renderers wird
   wie ein Bild gesetzt — zentriert, 0,75 pt je Pixel, nur verkleinert auf Satzspiegelbreite und
   Seitenhöhe, bei Bedarf so klein, dass es mit seiner Überschrift auf eine Seite passt. Formen
   werden `ShapeItem` (Kurven, Strichmuster, runde Ecken, Füllung), Texte `TextItem` in Segoe UI
   bzw. Selawik (statt der Tabellenschrift von DocLibs); Beschriftungen mit `max_width` schrumpfen
   bis 70 % und werden dann nach `anchor` gesetzt. Fehlende Zeichen in Beschriftungen werfen.
6. **Bilder anderer Formate**: Bilder, die nicht PNG/JPEG sind, gehen in Reihenfolge durch
   `PdfOptions.image_converters`; die Umwandlung erfolgt in doppelter Platzierungsgröße, gesetzt
   wird in natürlicher Größe (wie DocLibs). Ohne Konverter bleibt es ein Fehler mit Pfad.
7. Fehler aus Renderern und Konvertern kommen als `DocumentConversionError` mit der Zeile des
   Blocks (Front Matter mitgezählt, `line_of`).
8. Tests `tests/generation/pdf/test_characters.py`, `test_drawings.py`, `test_slide_syntax.py`
   mit Renderern aus Funktionen (wie DocLibs `Samples.Renderer`), dazu `layouts.md` aus DocLibs
   → `layouts.roundtrip.expected.md`.

## Akzeptanzkriterien

- [ ] Ein fehlendes Zeichen bricht mit Nennung von Zeichen, Codepunkt und Schrift ab — in Text,
      Überschrift, Tabelle, Code, Kopf-/Fußzeile und Zeichnungsbeschriftung.
- [ ] `replace_unsupported` erhält jedes Emoji als ein Cluster, sein Ersatz erscheint an der
      Stelle, Anker und Links bleiben gültig; ein Ersatz, der selbst fehlt, wirft.
- [ ] Markdown für Folien (`layouts.md`) erzeugt ein PDF ohne Fehler; falsche Container, Alerts
      und Attribute werfen dieselben Fehler wie in den Folien.
- [ ] Eine Zeichnung erscheint als Vektorpfade (keine Rastergrafik) mit Kurven, Strichmustern,
      Farben und durchsuchbarem Text.
- [ ] Ein Bild im SVG-Format wird mit Konverter gesetzt und ist ohne Konverter ein Fehler.

## Offene Fragen

1. `==mark==` im PDF: DocLibs setzt es fett. Vorschlag für die PTA: Hinterlegung in Gelb
   `FDDC35` (PTA-Hervorhebungsfarbe, wie in den Folien vorgesehen), gleich wie im DOCX
   (E03-S03). Einverstanden?

> (2026-11-07) Ja, Hinterlegung in Gelb `FDDC35` wie im DOCX.

## Notizen

- Abhängig von E02-S02, E02-S03, E02-S04 und E05-S02; die Mermaid- und Chart-Renderer liefern
  E06-S01 bis E06-S03, den SVG-Konverter E06-S04 — die Tests hier kommen ohne sie aus.
- Die Graphem-Zerlegung ist bewusst einfach; sie deckt die DocLibs-Fälle ab, nicht alle Regeln
  von UAX #29. Reicht sie nicht, wäre das Paket `regex` (`\X`) die Alternative.
- (2026-11-07, E08-S01) `Notes.characters(markdown, line_offset, in_text, in_code, effect,
  alternatives)` in `generation/common/result.py` ist als Port von `GenerationNotes.Characters`
  vorhanden und getestet; hier nur noch mit den Schriftprüfungen aufrufen. `alternatives`
  ersetzt `AuthoringGuides.Symbols` (Zeichen → Ersatz in Vorzugsreihenfolge).
- (2026-11-07, E02-S02) Lesen und Prüfen der Folien-Syntax ist fertig: der PDF-Generator ruft
  vor dem Schreiben `front.status_labels()` und `layout_syntax.check(tokens, DocumentFormat.PDF,
  front.body_line)` auf und nimmt Überschriften über `layout_syntax.without_attributes`, farbige
  Wörter über `layout_syntax.coloured` (Textkinder mit `meta[STATUS]`); die Fehlerfälle der Tests
  in `tests/generation/common/test_layout_syntax.py` (dort für DOCX/PPTX parametrisiert) um PDF
  ergänzen — das ist der Port von `SlideLayoutSyntaxTests.Mistakes_Throw_LikeInDecks`.
- (2026-11-07, E04-S04) Neue Heading-Attribute `.agenda`, `.interim`, `.quote`, `.contact`
  (`HeadingAttributes.kind`) prüft `layout_syntax.check` auch für PDF; wie Word mindestens
  Überschrift und Inhalt zeigen. Charts aus `ChartGraphic` platziert PowerPoint bereits
  (`generation/pptx/kinds.py`).
- (2026-11-07, E09-S01) `::: notes` ist ein gültiger Container (`layout_syntax.NOTES`, Prüfung
  „vor der ersten Überschrift = Fehler" in `layout_syntax.check`). Das PDF lässt Notizen wie Word
  weg (Hinweis `NoteCodes.NOTES_DROPPED`, vgl. `generation/docx/writer.py`
  `layout_container`); mit `notizen: ja` (DocLibs/vt-tools-libs `showNotes`) zeigt es sie unter
  der Folie. Die Absätze liefert der PPTX-Parser schon als `Slide.notes`
  (`DeckParser._take_notes`).
- (2026-11-08, Zusammenführung E05-S01/E05-S02) Die PDF-Engine ist reportlabs Platypus
  (`generation/pdf/layout/`), es gibt kein `layout.py`, kein Seitenmodell (`ShapeItem`,
  `TextItem`) und keinen eigenen Renderer mehr: Zeichnungen werden eigene Flowables, die das
  `Drawing` direkt auf den Canvas malen (Pfadcode des alten `renderer.py` in Commit 175e572).
  Fehlende Zeichen setzt die Engine bis hierher als `?` (`PdfFonts.shown` in
  `InlineWriter.text`) — dort greift `replace_unsupported` an. Auch `::: timeline` und
  `::: gantt` (E15-S01) zeigt das PDF bis hierher nur als Inhalt mit `code-not-drawn`
  (`StoryBuilder.layout_container`); sie sind hier mitzuzeichnen (`drawing/schedule.py`,
  Gantt als Tabelle wie in Word).
