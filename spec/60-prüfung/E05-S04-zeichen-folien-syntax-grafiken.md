# E05-S04 Fehlende Zeichen, Folien-Syntax, Diagramme und Charts im PDF

> Status: in Prüfung
> Epic: [E05 PDF-Generator im PTA-Design](../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

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

- [x] Ein fehlendes Zeichen bricht mit Nennung von Zeichen, Codepunkt und Schrift ab — in Text,
      Überschrift, Tabelle, Code, Kopf-/Fußzeile und Zeichnungsbeschriftung.
- [x] `replace_unsupported` erhält jedes Emoji als ein Cluster, sein Ersatz erscheint an der
      Stelle, Anker und Links bleiben gültig; ein Ersatz, der selbst fehlt, wirft.
- [x] Markdown für Folien (`layouts.md`) erzeugt ein PDF ohne Fehler; falsche Container, Alerts
      und Attribute werfen dieselben Fehler wie in den Folien.
- [x] Eine Zeichnung erscheint als Vektorpfade (keine Rastergrafik) mit Kurven, Strichmustern,
      Farben und durchsuchbarem Text.
- [x] Ein Bild im SVG-Format wird mit Konverter gesetzt und ist ohne Konverter ein Fehler.

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08 im Haupt-Checkout (parallel arbeitet ein anderer Lauf
desselben Agents an E09-S02 in einem Worktree; keine gemeinsamen Dateien außer Doku und
Gedächtnis, dort nur ergänzt). Die Story sammelt die offenen PDF-Punkte von E05-S01, E05-S02,
E05-S03, E06-S01 bis E06-S04, E11-S04, E12-S03 und E15-S01 bis E15-S04; dort steht jeweils
„Erledigt in E05-S04" (oder was offen bleibt).

Neu: `generation/common/graphemes.py` (`clusters`, `code_points`),
`generation/pdf/layout/drawings.py` (`DrawingFlowable`). Geändert: `layout/fonts.py`
(`Replacement`, `question_mark`, `PdfFonts.replace`/`replaced`/`family`, `shown` je
Graphem-Cluster, `register(…, replace)`), `layout/story.py` (`LayoutSettings.replace_unsupported`
und `today`, `graphic_figure`, `drawing_flowable`, `drawing`, `steps`, `risk_matrix`, `gantt`,
`table_commands`/`pta_table`/`column_widths_of`, Icon-Aufzählungszeichen, `::: statement` fett,
`IMAGE_SCALE`; `DRAWN_CONTAINERS` entfallen), `layout/inline.py` (Icons als Bild,
`markup_text`), `layout/flowables.py` (`icon_png`, `icon_image`, `_Parser`,
`PtaParagraph._setup`, `MarkerKind.ICON`), `frame.py` (Deckblatt und Kennzeichnung über
`shown`), `generator.py` (`notes` an `add_generated`, `today` und `replace_unsupported` in die
`LayoutSettings`, `character-missing` nur mit Ersatzfunktion), `options.py`
(`replace_unsupported: Replacement | None = question_mark`), `common/result.py` (Docstrings).
Tests: `tests/generation/common/test_graphemes.py` (11 Fälle),
`tests/generation/pdf/test_characters.py` (11), `layout/test_drawings.py` (7),
`test_graphics.py` (10), `test_slide_syntax.py` (2), `layout/test_inline.py` neu gefasst,
`tests/generation/common/test_layout_syntax.py` für PDF parametrisiert (+26 Fälle),
`test_generator.py`: die drei „zeigt Inhalt mit `code-not-drawn`"-Tests entfallen, die Beispiele
müssen als PDF **ohne Hinweise** entstehen. Doku: `docs/verwendung.md` (neuer Abschnitt
„Grafiken und fehlende Zeichen im PDF (E05-S04)", fehlende Zeichen, Tabellen, Zeitstrahl,
Schritte, Risikomatrix, Icons, Hinweiscodes), `docs/anleitung.md`, `docs/ki-anleitung.md`;
`ai/Gedächtnis.md`. Keine neue Abhängigkeit.

### Entscheidungen

- **Zeichnungen als eigenes Flowable** (`DrawingFlowable`) statt Seitenmodell (Plan Punkt 5
  sprach von `ShapeItem`/`TextItem`, die es seit der Zusammenführung E05-S01/E05-S02 nicht mehr
  gibt, siehe Notiz vom 2026-11-08): der Pfadcode des alten `renderer.py` (Commit 175e572) wurde
  übernommen und um runde Linienenden, Strichmuster in Punkten und Spans ergänzt. Texte sind
  echter Text (durchsuchbar) in Segoe UI bzw. Selawik; `max_width` wird mit der echten Schrift
  gemessen (nicht geschätzt wie SVG/PowerPoint), bis 70 % verkleinert, dann nach `anchor`
  gesetzt.
- **Größe** wie Bilder: 0,75 pt je Pixel, nur verkleinert auf Satzspiegelbreite, 80 % der
  Satzspiegelhöhe (`word.FIGURE_HEIGHT_SHARE`) und so, dass die Zeichnung mit den Überschriften
  davor und ihrer Beschriftung auf eine Seite passt; nie geteilt.
- **Beschriftung:** ein Absatz `Abbildung: …` direkt nach dem Zaun (gleiche Ebene) wird
  „Abbildung n: …" und bleibt mit der Grafik zusammen (wie Word, E03-S04). Charts bekommen ohne
  diesen Absatz **keine** Beschriftung, weil Titel und Quelle schon in der Zeichnung stehen
  (`charts/drawing.py`); Word nimmt dort den Titel, weil sein natives Diagramm ihn anders zeigt.
- **Gantt als Tabelle** wie in Word (Plan-Notiz „Gantt als Tabelle wie in Word"): PTA-Tabelle,
  Laufzeit PTA-Blau/Hellblau, Meilenstein als **gezeichnete** dunkelblaue Raute (◆ fehlt den
  PDF-Schriften), Linie rechts der Spalte von heute (`word.GANTT_TODAY_RULE`/8 = 1,5 pt).
- **Schritte und Risikomatrix** wie Word (`word.STEPS_TEXT_PT`, Liste als Rückfall; Legende als
  PTA-Tabelle unter der Matrix).
- **Icons als PNG**, nicht als Vektor: reportlabs Absätze können Bilder (`<img>`) im Fließtext
  setzen, aber keine Zeichnungen mit Platz in der Zeile. Das PNG ist dasselbe wie in Word
  (`raster.png`, 96 px für 10 pt, ≈ 690 dpi). reportlabs `<img>` nimmt nur Dateien und URLs
  (`data:` sperrt `rl_config.trustedHosts`, globale Einstellung — nicht angefasst); darum liest
  `PtaParagraph` `pta-icon:name` über einen eigenen `ParaParser` (`flowables._Parser`).
  `icon_png` ist mit `functools.cache` gepuffert — das Ergebnis hängt nur vom Namen ab.
- **SVG-Bilder** wandelt das PDF in dreifacher Größe (Antwort aus E06-S04), Word und PowerPoint
  bleiben bei `GENERATOR_SCALE` = 2.
- **Graphem-Cluster ohne Abhängigkeit** (Plan Punkt 1); Variationsselektoren und ZWJ an sonst
  vorhandenen Zeichen werden still weggelassen, unsichtbare Format-/Steuerzeichen (U+200B …),
  die der Schrift fehlen, auch — sie hätten sonst ein `?` erzeugt.
- **`::: statement`:** der erste Absatz fett wie in Word (fehlte im PDF).

### Abweichungen

- **`replace_unsupported` hat einen Standard** (`question_mark`, zeigt `?` mit Hinweis
  `character-missing`) statt „ohne Hook wirft jedes fehlende Zeichen" (Plan Punkt 2, DocLibs).
  `replace_unsupported=None` wirft wie geplant. Grund siehe Warnung.
- **Links ausgerichtet** statt zentriert (Plan Punkt 5): wie Bilder im PDF und Bilder in Word
  (E05-S02 setzt den Rumpf im Word-Design); Grafiken in Satzspiegelbreite sehen gleich aus.
- **Der Titel in den Metadaten** wird nicht ersetzt (Plan Punkt 2): Info-Dictionary und XMP
  sind Unicode und brauchen keine Glyphen; ersetzt werden alle Texte, die auf eine Seite kommen
  (auch Deckblatt, Kopf-/Fußzeile, Kennzeichnung, Inhaltsverzeichnis, Lesezeichen).
- **Zeilenumbruch nur zwischen Clustern** (Plan Punkt 3) ist nicht umgesetzt: reportlab bricht
  an Leerzeichen und Code an jedem Zeichen; ein Bruch mitten in einem Cluster ist nur bei
  zerlegten Akzenten (e + U+0301) in überlangen Wörtern denkbar. Siehe Offene Punkte.
- **Fehlermeldung ohne Zeilennummer:** das fehlende Zeichen wird beim Setzen erkannt, wo die
  Zeile nicht mehr bekannt ist; die Meldung nennt Zeichen, Codepunkte und Schrift. Mit dem
  Standard nennt der Hinweis `character-missing` die Zeile wie bisher.
- **Plan Punkte 4, 6, 7** (Folien-Syntax, Bildkonverter, Fehler der Renderer mit Zeile) gab es
  schon aus E05-S02 bzw. `code_blocks.render_graphic`; hier nur geprüft und getestet
  (`layouts.md` als PDF ohne Hinweise, Fehlerfälle wie in Word/PowerPoint).

### Warnungen

- **Warnung (vorsichtigste Wahl):** Der Plan wollte ohne Hook bei jedem fehlenden Zeichen
  abbrechen. Das hätte jedes bestehende Dokument mit Griechisch, Kyrillisch (ohne Segoe UI) oder
  Emoji, das heute mit `?` und Hinweis entsteht, zum Fehler gemacht, und `PdfOptions` hatte seit
  E05-S01 `replace_unsupported=True` als Standard. Darum bleibt `?` der Standard; streng wird
  es mit `replace_unsupported=None`. Soll der Standard streng sein, genügt `= None` in
  `PdfOptions` (und `LayoutSettings`) und das Anpassen von `test_by_default_…`.
- `Notes.characters` meldet weiter **je Codepunkt**, nicht je Cluster (`👍🏽` gibt zwei
  Hinweise: U+1F44D und U+1F3FD); der Ersatz selbst fragt je Cluster einmal.
- Die Icons im PDF sind Rasterbilder (s. Entscheidungen); beim starken Hineinzoomen bleiben sie
  bis etwa 7-fache Größe scharf.
- Mermaid ist hier nur mit `.tmp/mm/env.sh` geprüft (Chromium mit `--no-sandbox`); ohne die
  Umgebung lassen die Tests `mermaid-bericht.md` aus, `test_a_mermaid_drawing_is_drawn_as_vectors`
  läuft mit der aufgezeichneten SVG immer.

### Prüfpunkte

- `.tmp/review/pdf-funktionen-bericht.pdf`, `pdf-gsb-bericht.pdf`, `pdf-mermaid-bericht.pdf`
  (mit mermaid-cli), `pdf-chart.pdf`, `pdf-drawing.pdf`, `layouts.pdf`: Charts, Finanzdiagramm,
  Mermaid, Zeitstrahl, Gantt, Schritte, Risikomatrix, Icons, SVG-Bild ansehen — Schärfe beim
  Zoomen, Lage der Icons auf der Grundlinie, Raute und Heute-Linie im Gantt.
- Text in Zeichnungen markieren und suchen (z. B. „Bestellungen" im Chart).
- veraPDF (`verapdf --flavour 2b`) über die Beispiel-PDFs, sobald es installiert ist (Icons und
  SVG-Bilder bringen PNG mit Alphakanal = Soft-Mask; PDF/A-2 erlaubt das).
- Ob Charts ohne `Abbildung:`-Absatz wirklich keine Nummer bekommen sollen (Word nummeriert sie
  über den Titel) — Entscheidung des Menschen.

### Offene Punkte

- Zeilenumbruch nur zwischen Graphem-Clustern (Plan Punkt 3), falls zerlegte Akzente in langen
  Wörtern vorkommen; sonst `regex` (`\X`) und ein eigener Wortteiler.
- QR-Codes als Vektor (Notiz aus E11-S04) — heute PNG wie in Word.
- Folien-Syntax als Boxen und Spalten (Notiz aus E05-S02): das PDF zeigt sie wie Word
  nacheinander.
- `notizen: ja` (Notiz aus E09-S01, Sprechernotizen unter der Folie) betrifft ein PDF aus
  Präsentationen, das es nicht gibt; offen bis zu einem Folien-PDF (E10-S02?).
- Silbentrennung (Warnung aus E05-S02).
