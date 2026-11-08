# E05-S01 Grundgerüst PDF: reportlab, pikepdf, PDF/A-2b

> Status: in Prüfung
> Epic: [E05 PDF-Generator im PTA-Design](../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

## Zusammenfassung

Das Fundament des PDF-Generators: Schriften laden und messen, fertig gelayoutete Seiten mit
reportlab zeichnen und das Ergebnis mit pikepdf zu PDF/A-2b machen. Noch ohne Markdown-Layout
(E05-S02) und ohne PTA-Seitenrahmen (E05-S03).

## Kontext

- DocLibs `DocumentGeneration.Pdf`: `PdfGenerator.cs` (121 Zeilen), `PdfOptions.cs` (73),
  `Fonts.cs` (147: `FontFace`, `IFontMetrics`, `FontSet`), `PageModel.cs` (67: `TextItem`,
  `LineItem`, `RectItem`, `ImageItem`, `ShapeItem`, `LinkItem`, `LaidOutPage`, `Bookmark`,
  `PageGeometry`, `Layout`), `PdfRenderer.cs` (363). `PdfTemplateOptions.cs` (Brand-Auswahl)
  entfällt ersatzlos.
- Die PdfPig-Umwege in `PdfRenderer.cs` entfallen: `FixXmp` (XMP im Platz umschreiben),
  `FlagAnnotations` (`/F 4` byteweise einsetzen) und die Schriftkopien zu je 255 Zeichen —
  reportlab teilt Teilschriften selbst, pikepdf schreibt XMP und Annotationen sauber.
- reportlab (Open Source) erzeugt kein PDF/A; das erledigt der Nachlauf mit pikepdf. Extra `pdf`
  ist installiert (reportlab 5.1, pikepdf 10.17). Java und veraPDF sind hier nicht installiert
  (Entscheidung 2026-11-06): Struktur wird mit pikepdf geprüft, veraPDF nur, wenn vorhanden.
- Schriften kommen aus E01-S03 (Selawik gebündelt, Segoe UI aus dem System); Selawik ist
  metrikkompatibel, das Layout ist mit beiden gleich.

## Vorgeschlagener Ansatz

1. Paket `src/pta_documents/generation/pdf/`; nur mit Extra `pdf` importierbar — ein fehlendes
   reportlab/pikepdf ergibt einen `ImportError` mit dem Hinweis `pip install -e '.[pdf]'`.
2. `options.py`: `PdfOptions` (frozen) wie `DocxOptions`: `variant: WordVariant`, `language`,
   `date`, `company`, `toc`; dazu `replace_unsupported` (E05-S04), `code_block_renderers` und
   `image_converters` (Schnittstellen aus E02-S04) und `created: dt.datetime | None`
   (Zeitstempel der Metadaten, Standard jetzt in UTC; Tests setzen ihn fest). Entfallen:
   `Template`, `Brands`, `PageSize` (nur A4), `Orientation` (folgt aus `vorlage`), `TimeProvider`.
3. `fonts.py`: `FontFace` (`REGULAR`, `BOLD`, `ITALIC`, `BOLD_ITALIC`, `MONO`, `MONO_BOLD`; die
   Tabellen-Faces von DocLibs entfallen — Tabellen stehen wie in Word in der Textschrift),
   Protocol `FontMetrics` (`width(text, face, size)`, `has_glyph(char, face)`) und `FontSet` auf
   den Schriftdateien aus E01-S03 (Breiten über reportlab `TTFont`, Glyphen über die cmap).
   Registriert wird bei reportlab unter einem Namen aus dem Inhalts-Hash (`PTA-<sha8>`), damit
   die globale Schriftliste von reportlab das Ergebnis nie beeinflusst (kein Laufzeitzustand).
4. `page_model.py`: Port von `PageModel.cs` (Punkte, Ursprung oben links). `ShapeItem` nutzt die
   Pfadsegmente des Zeichenmodells aus E02-S03; ist E02-S03 noch nicht umgesetzt, werden
   `MoveTo`/`LineTo`/`CubicTo`/`ClosePath` hier angelegt und von E02-S03 übernommen.
5. `renderer.py`: `render(layout, fonts, info) -> bytes` auf `reportlab.pdfgen.canvas.Canvas`
   (`initialFontName` = Regular, damit nie Helvetica eingebunden wird): y-Spiegelung, Farben aus
   Hex, Text, Linien, Flächen, Bilder (PNG/JPEG über `ImageReader`, gleiche Bilder einmal),
   Pfade mit Kurven, Strichmuster und runden Ecken, Links (`linkURL`; interne Ziele über
   `bookmarkHorizontal` + `linkRect`), Lesezeichen verschachtelt nach Ebene (Port von `Nest`).
6. `pdfa.py`: `to_pdfa(data, info) -> bytes` mit pikepdf: XMP über `open_metadata()`
   (`pdfaid:part` 2, `pdfaid:conformance` B, `dc:title` als `rdf:Alt`, `dc:creator` als
   `rdf:Seq`, `dc:language` `de-DE`/`en`, Producer „PTA Documents", Zeitstempel = Info-Dictionary),
   OutputIntent `GTS_PDFA1` mit sRGB-Profil aus Pillow (`ImageCms.createProfile("sRGB")`, keine
   ICC-Datei im Repo), `/F 4` auf jeder Annotation, `/Lang` im Katalog, PDF 1.7,
   `deterministic_id=True`.
7. `generator.py`: `PdfGenerator.generate(document, output, options)` liest das Front Matter mit
   denselben Schlüsseln wie der DOCX-Generator (`VALID_KEYS`, `apply_front_matter`), Titel und
   Autor fallen auf `document.metadata` zurück. Bis E05-S02 entsteht nur eine leere Seite (wie
   DocLibs `EmptyMarkdown_GivesOneEmptyPage`).
8. Tests `tests/generation/pdf/test_renderer.py` auf einem von Hand gebauten `Layout`.
   Übernommen aus `PdfGeneratorTests.cs`: `Output_IsPdfA2b_WithEmbeddedFonts`,
   `Characters_BeyondWinAnsi_SurviveTheRoundTrip`, `MoreThan255DistinctCharacters_Work`,
   `LongNonAsciiTitleAndAuthor_StillFitTheMetadata`, Lesezeichen und Links. Ergebnis nach
   `.tmp/review/pdf-grundgeruest.pdf`.

## Akzeptanzkriterien

- [ ] pikepdf bestätigt: XMP mit `pdfaid:part` 2 und `conformance` B, Titel/Autor in XMP und
      Info-Dictionary gleich, OutputIntent mit eingebettetem sRGB-Profil (`/N 3`).
- [ ] Jede Schrift ist eingebettet (`/FontFile2`); keine der 14 Standardschriften kommt vor.
- [ ] Jede Annotation hat `/F 4`; das PDF ist unverschlüsselt und hat eine `/ID`.
- [ ] Text mit Umlauten, Polnisch, Griechisch, Kyrillisch und mehr als 255 verschiedenen Zeichen
      kommt mit pdfplumber unverändert zurück.
- [ ] Lesezeichen sind nach Ebenen verschachtelt; externe und interne Links funktionieren.
- [ ] Ein Test mit veraPDF (`--flavour 2b`) läuft, wenn `verapdf` im `PATH` liegt, und wird
      sonst übersprungen.
- [ ] Zweimal mit gleichem `created` erzeugt, sind die Dateien byte-gleich.

## Offene Fragen

1. Selawik hat keine Kursive. Soll Kursivtext eine künstlich schräggestellte Selawik Regular
   sein (Textmatrix, etwa 12°) oder aufrecht bleiben, solange Segoe UI fehlt? (Gilt nur, wenn
   E01-S03 das nicht schon festlegt.)

> (2026-11-07) Schrägstellen, wie in E01-S03 entschieden.

2. Codeschrift im PDF: Word nimmt Consolas (Entscheidung 2026-11-06), die nicht mitgeliefert
   werden darf. Vorschlag: Consolas aus dem System, sonst gebündelt **Cascadia Mono** (OFL, von
   Microsoft). Passt das, oder lieber eine andere Monospace-Schrift?

> (2026-11-07) Consolas aus dem System, sonst **Inconsolata** (OFL) statt Cascadia Mono — Entscheidung in E01-S03.

## Notizen

- Abhängig von E01-S03 (Schriftquelle). Die Rundreise über den PDF-Konverter beginnt mit
  E05-S02 und braucht E07-S04.
- Prüfpunkt: Pillows sRGB-Profil ist ICC v2/v4; PDF/A-2 erlaubt beide. Sobald veraPDF auf einem
  Rechner verfügbar ist, einmal `.tmp/review/pdf-grundgeruest.pdf` prüfen.
- (2026-11-07, E02-S04) `PdfOptions.code_block_renderers`/`image_converters` wie in
  `DocxOptions`: `field(default_factory=default_renderers)` bzw. `default_converters`; Fences
  über `generation/common/code_blocks.draw`, Bilder über `images.convert_image(…, 2 * scale, …)`.
- (2026-11-08, E08-S02) `VALID_KEYS` des PDF-Generators braucht `Keys.CHECK` (`pruefung`), wie
  DOCX und PPTX; `generation/common/check.check` nimmt bisher nur DOCX/PPTX — PDF dort ergänzen
  (Probelauf, `GenerationResult.pages` als Seitenzahl statt der Schätzung).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08, parallel zu E05-S02 (anderer Worktree). Neu: Paket
`src/pta_documents/generation/pdf/` — `__init__.py` (Import nur mit Extra, sonst
`ImportError(EXTRA_MISSING)`), `options.py` (`PdfOptions`), `fonts.py` (Protocol `FontMetrics`,
`PdfFonts`, `registered_name`), `page_model.py` (`TextItem`, `LineItem`, `RectItem`, `ImageItem`,
`ShapeItem`, `LinkItem`, `Anchor`, `LaidOutPage`, `Bookmark`, `PageGeometry`, `Layout`),
`metadata.py` (`PdfInfo`, `PRODUCER`), `renderer.py` (`render`, `nest`), `pdfa.py` (`to_pdfa`,
`srgb_profile`), `body.py` (`BodySource`, Protocol `BodyLayout`), `simple_layout.py`
(vorläufiges Layout), `generator.py` (`PdfGenerator`, `VALID_KEYS`, `BODY_LAYOUT`,
`apply_front_matter`). Geändert: `generation/common/check.py` (PDF, `ReportStats.counted_pages`),
`tools/generate/generate.py` und `tools/check/check.py` (`--pdf`), `pyproject.toml`
(Lizenzkommentare des Extras `pdf`, keine neue Abhängigkeit), `docs/verwendung.md` (neuer
Abschnitt „Markdown → PDF (E05-S01)", Hinweise, `check`), `docs/anleitung.md`,
`ai/Gedächtnis.md`. Tests: `tests/generation/pdf/test_renderer.py` (16 Fälle, einer davon veraPDF)
und `test_generator.py` (12 Fälle); Ansicht `.tmp/review/pdf-grundgeruest.pdf`.

### Entscheidungen

- **Naht zur Layout-Engine:** `generator.BODY_LAYOUT: BodyLayout` — eine Funktion
  `(source: BodySource, fonts: FontMetrics) -> Layout`. `BodySource` trägt die geprüften Token
  (`parse(front.body)` nach `layout_syntax.check`), `document` (Ressourcen), `front`
  (`body_line` = Zeilenversatz), die Optionen nach dem Front Matter, `texts` und den
  `Notes`-Sammler. Die Engine wählt die `PageGeometry` selbst (sie liest den Satzspiegel aus der
  Vorlage). E05-S02 setzt dort `layout.lay_out` ein und löscht `simple_layout.py`; Renderer,
  PDF/A und Generator bleiben.
- **Vorläufiges Layout** statt der leeren Seite aus dem Plan (Punkt 7): schlichter Text auf A4
  (Überschriften fett 16/13/11 pt, Text 10 pt, Code Inconsolata 9 pt, Listen „–" bzw. `1.`,
  Zitate eingerückt, Tabellenzeilen als Zellen nebeneinander; gieriger Umbruch, zu lange Wörter
  zeichenweise). Ein leeres Dokument ergibt weiterhin genau eine leere Seite. Damit sind
  `generate --pdf`, `check --pdf` und `GenerationResult.pages` schon jetzt prüfbar.
- **Ränder** des vorläufigen Layouts: links/oben/rechts/unten 2,20/3,50/2,20/2,00 cm (hoch) bzw.
  2,20/4,20/2,20/2,50 cm (quer) aus E05-S02 — als Konstante in `simple_layout.py`, weil das
  Lesen aus `w:sectPr` zu E05-S02 gehört.
- **Fehlende Zeichen:** PDF/A verbietet `.notdef`; das vorläufige Layout setzt `?` (Leerraum →
  Leerzeichen, etwa U+00A0), der Generator meldet jedes Zeichen einmal mit `character-missing`
  über das vorhandene `Notes.characters` (Text: Regular **und** Bold, Code: Mono). Der Renderer
  selbst ersetzt nichts — er zeichnet, was das Layout setzt.
- **Schriften:** `FontFace` ist die aus `design.fonts` (mit `LIGHT` und `QUOTE`), keine zweite
  Aufzählung. `PdfFonts` misst über `FontSet.width`/`has_glyph` (dieselben `hmtx`-Breiten, die
  reportlab beim Zeichnen nimmt) und registriert jede Datei einmal als `PTA-<sha8>`. Kursiv
  (synthetisch) teilt sich Namen und Einbettung mit Regular/Bold und wird mit 12° über
  `setTextTransform` schräggestellt.
- **Renderer:** reportlab im `invariant`-Modus mit `initialFontName` = Regular; Bilder über
  `ImageReader` mit `mask="auto"` (reportlab legt gleiche Bilder schon selbst nur einmal ab);
  interne Ziele als benannte Ziele (`bookmarkHorizontal` je `Anchor`, `linkRect`), ein
  unbekanntes Ziel ist ein `ValueError` (Programmfehler der Engine). Lesezeichen: Ebene höchstens
  eins tiefer als die vorige (`nest`), Lesezeichenleiste wird geöffnet, wenn es welche gibt.
- **PDF/A:** neues Info-Dictionary (reportlabs „ReportLab …"-Producer und feste Daten fallen
  weg), XMP über `open_metadata(set_pikepdf_as_editor=False, update_docinfo=False)` mit
  denselben Werten von Hand gesetzt (`dc:title` Alt, `dc:creator` Seq, `dc:language` Bag,
  `dc:description` = Untertitel, `xmp:CreateDate`/`ModifyDate`/`MetadataDate` = `created`),
  Zeitstempel im Info-Dictionary `D:JJJJMMTTHHMMSSZ`. `save(force_version="1.7",
  deterministic_id=True)`, Objektströme wie von reportlab (PDF/A-2 erlaubt sie).
- **`created`** ohne Zeitzone gilt als UTC; Standard ist jetzt in UTC.
- **Front Matter:** `VALID_KEYS` = DOCX ohne `typografie`/`syntaxhervorhebung` (die bringt
  E05-S02 mit `typeset` und Highlighting mit, laut dessen Notiz). Wie in Word braucht eine
  Vorlage mit Deckblatt einen `titel` — schon jetzt, damit ein Dokument, das heute als PDF geht,
  mit E05-S03 nicht plötzlich scheitert. `vorlage`-Fehler kommen mit `format=PDF` (nicht DOCX).
- **`check`** nimmt `DocumentFormat.PDF`: Probelauf mit dem PDF-Generator (lazy importiert, ein
  fehlendes Extra wird ein Fehler mit der Meldung), Stilregeln wie Word, Statistik
  `ReportStats` mit `counted_pages` = `GenerationResult.pages`.
- **Werkzeuge:** PDF nur mit `--pdf`; Dateinamen bleiben DOCX/PPTX zugeordnet (kein eigenes
  Namenssuffix für PDF).

### Abweichungen

- Plan Punkt 7 „bis E05-S02 nur eine leere Seite": stattdessen das vorläufige Textlayout (siehe
  oben); die leere Seite gilt nur für leere Dokumente.
- `PdfOptions.system_fonts` ist zusätzlich (Standard `True`), damit Tests und byte-gleiche
  Ergebnisse nicht von installierten Schriften abhängen.
- Eine Generator-Registry gibt es im Repo nicht (nur `ConverterRegistry` für die Konverter); die
  „Verdrahtung" sind `check` und die beiden Werkzeuge.
- `metadata.py` (`PdfInfo`) und `body.py` sind neue Module, die der Plan nicht nennt.
- `generate-samples` erzeugt weiterhin nur DOCX/PPTX (die Beispiele nutzen `typografie:`, das
  der PDF-Generator noch ablehnt).

### Warnungen

- **pikepdf steht unter MPL-2.0**, nicht unter MIT/BSD/Apache/OFL. Der Plan hatte es gewählt;
  es wird unverändert als Bibliothek genutzt (die MPL verlangt nur für veränderte MPL-Dateien
  die Offenlegung). Bitte bestätigen oder eine Alternative nennen.
- **Griechisch und Kyrillisch** (Akzeptanzkriterium 4) gehen nur mit Segoe UI aus dem System:
  Selawik hat weder Griechisch noch Kyrillisch (348 Zeichen), Inconsolata kein Kyrillisch,
  Gelasio nur 19 griechische Zeichen. Der Test prüft Umlaute, Polnisch und alle 348
  Selawik-Zeichen (> 255) sowie Griechisch in Gelasio (`QUOTE`); Kyrillisch ist ohne Segoe UI
  nicht prüfbar und wird `?` mit Hinweis. Ein Ersatz (E05-S04, `replace_unsupported`) oder eine
  weitere gebündelte Schrift wäre zu entscheiden.
- **veraPDF nicht geprüft:** veraPDF und Java fehlen hier; der Test
  `test_verapdf_confirms_pdfa_2b` wird übersprungen. Geprüft sind die Strukturmerkmale mit
  pikepdf. Besonders offen: Pillows sRGB-Profil ist **ICC v4.4** (LittleCMS); ob veraPDF es im
  OutputIntent annimmt, ist ungeprüft. Fällt es durch, ist der Header-Versionswert oder ein
  v2-Profil die Abhilfe.
- **ICC-Datum fest:** LittleCMS schreibt die aktuelle Uhrzeit ins Profil; `srgb_profile` setzt
  sie auf 2000-01-01, damit Dateien byte-gleich werden. Das Profil ist sonst unverändert (seine
  Profil-ID ist 0, also keine Prüfsumme zu erneuern).
- **reportlab hält eine prozessweite Schriftliste.** Registriert wird nur unter Inhalts-Hash —
  das Ergebnis hängt nicht davon ab, die Liste wächst aber je neuer Schriftdatei (höchstens um
  die System- und gebündelten Dateien).
- Das vorläufige Layout misst ohne Kerning und ignoriert Fett/Kursiv innerhalb von Absätzen,
  Bilder, Links, Fußnoten und Container-Semantik; es ist bewusst klein und soll nicht
  weiterentwickelt, sondern durch E05-S02 ersetzt werden.
- `Keys.TYPOGRAPHY`/`HIGHLIGHT` fehlen in `VALID_KEYS`: Berichte mit `typografie:` (z. B.
  `samples/funktionen/funktionen-bericht.md`) lehnt der PDF-Generator bis E05-S02 ab.

### Prüfpunkte

- `.tmp/review/pdf-grundgeruest.pdf` öffnen: zwei Seiten, Lesezeichen 1 › 1.1 › 1.1.1 und 2,
  Link „PTA im Netz" auf `https://www.pta.de/`, „zu Abschnitt 1.1" springt auf Seite 2,
  kursiver Text schräg, Bild zweimal (einmal eingebettet), Kurvenform gelb.
- Auf einem Rechner mit veraPDF: `verapdf --flavour 2b .tmp/review/pdf-grundgeruest.pdf` und
  `./run.sh test tests/generation/pdf` ohne Überspringen.
- `./run.sh generate samples/gsb/gsb-bericht.md --pdf --out .tmp/pdf` — Text vollständig,
  polnische Zeichen korrekt.
- Auf einem Rechner mit Segoe UI: Griechisch/Kyrillisch kommen ohne `?` heraus.

### Offene Punkte

- **Für E05-S02:** `generator.BODY_LAYOUT` auf die eigene Engine setzen, `simple_layout.py` und
  ihre Erwähnung in `docs/verwendung.md` entfernen; `typografie`/`syntaxhervorhebung` in
  `VALID_KEYS`, `PdfOptions` und `apply_front_matter` ergänzen; Lesezeichen (`Bookmark`, Ebene
  1–3), Anker (`Anchor`) und Links (`LinkItem`) liefert die Engine, der Renderer kann sie schon.
- Das Ersetzen fehlender Zeichen (`replace_unsupported`) ist E05-S04; bis dahin `?`. — *(2026-11-08) Erledigt in E05-S04.*
- `style_rules` nennt in Docstrings nur PPTX/DOCX; für PDF gelten die Word-Regeln (nicht
  geändert, um die Story klein zu halten).

### Zusammenführung mit E05-S02 (2026-11-08)

E05-S01 und E05-S02 wurden parallel in getrennten Worktrees umgesetzt und danach gemeinsam nach
`main` gebracht (Merge-Commits, dann ein Commit „E05-S01/E05-S02: Layout-Engine in den
PDF-Generator eingebunden"). Vereinheitlicht:

- `PdfGenerator.generate` ruft für den Rumpf die Layout-Engine aus E05-S02 auf
  (`layout.layout(tokens, document, LayoutSettings, notes, PdfInfo)`) und schickt
  `result.content` durch den PDF/A-2b-Schritt aus E05-S01 (`pdfa.to_pdfa`);
  `GenerationResult.pages` kommt aus der Engine. Davor wie im DOCX:
  `layout_syntax.check(…, today)`, `generated_images.add_generated` (QR-Codes), `typeset`.
- Front Matter: `typografie` und `syntaxhervorhebung` stehen jetzt in `VALID_KEYS`, in
  `PdfOptions` (`typography`, `highlight`) und in `apply_front_matter`; `VALID_KEYS` ist damit
  gleich dem des DOCX-Generators. Status-Labels werden wie im DOCX mitgesetzt.
- Ränder und Seitengröße kommen aus der Vorlage (`design.word_styles`), nicht mehr aus
  Konstanten.
- **Eine** Schriftregistrierung (`layout/fonts.register`, `PTA-<sha8>`), **ein** `PdfInfo`
  (`metadata.py`, mit Standardwerten; die Engine nimmt es auch für reportlab).
- Fehlende Zeichen werden jetzt in der Engine `?` (`PdfFonts.shown`, aufgerufen in
  `InlineWriter.text`; Text: Regular und Bold, Code: Mono; die Aliase U+00A0/U+202F/U+2011
  zählen als vorhanden) — dieselbe Regel wie `Notes.characters` im Generator.
- QR-Codes sind im PDF 3 cm breit (mal `scale`) wie in Word; `::: timeline` und `::: gantt`
  zeigen ihren Inhalt mit `code-not-drawn` bis E05-S04 (beide kamen nach den Claims mit E11-S04
  bzw. E15-S01 auf `main`).
- Ein leeres Dokument ergibt wie bisher eine leere Seite (die Engine baut dann einen leeren
  Spacer).

Entfernt (nichts nutzt es mehr; Stand in Commit 175e572): `simple_layout.py` (Zwischenlayout),
`body.py` (`BodySource`/`BodyLayout`, die Naht `generator.BODY_LAYOUT`), `page_model.py` und
`renderer.py` (eigenes Seitenmodell und Zeichner — die Engine setzt mit Platypus direkt auf den
Canvas), `fonts.py` aus E05-S01 (`FontMetrics`, zweite Registrierung). E05-S03 braucht sie
nicht (Seitenrahmen über `layout(…, decorate=…)`), E05-S04 zeichnet Zeichnungen als eigene
Flowables auf dem reportlab-Canvas; das Malen von Pfaden mit Kurven und Strichmustern aus dem
alten `renderer.py` kann dort aus der Git-Geschichte übernommen werden. `test_renderer.py` wurde
zu `test_pdfa.py`: dieselben Prüfungen (PDF/A-Metadaten, OutputIntent, eingebettete Schriften,
>255 Zeichen, lange Titel, Lesezeichen, Links, Bilder einmal, Byte-Gleichheit, veraPDF) laufen
jetzt über den Generator mit Markdown; der Naht-Test entfiel. Neu: Tests für Typografie,
Hervorhebung, QR-Größe, Zeitstrahl-Hinweis, fehlende Zeichen im Code und alle Word-Beispiele in
`samples/` als PDF (nur `code-not-drawn` erlaubt).
