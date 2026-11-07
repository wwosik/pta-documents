# E05-S01 Grundgerüst PDF: reportlab, pikepdf, PDF/A-2b

> Status: Entwurf
> Epic: [E05 PDF-Generator im PTA-Design](E05-pdf-generator.md)
> Milestone: [M05 PDF](M05-pdf.md)

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
