# E07-S04 PDF → Markdown

> Status: Entwurf
> Epic: [E07 Konvertierung nach Markdown](E07-konvertierung-nach-markdown.md)
> Milestone: [M05 PDF](M05-pdf.md)

## Zusammenfassung

Der PDF-Konverter aus DocLibs in Python auf pdfplumber: aus der Textschicht werden Zeilen,
Absätze, Überschriften und Listen, getrennte Wörter werden wieder zusammengefügt, laufende Kopf-
und Fußzeilen sowie Bilder auf jeder Seite fallen weg, übrige Bilder werden Ressourcen.

## Kontext

- DocLibs `Pdf/PdfConverter.cs` (412 Zeilen, PdfPig): je Seite `## Page n`; Wörter →
  Zeilen (gleiche Grundlinie, Toleranz halbe Worthöhe) → Absätze (Umbruch bei Aufzählungszeichen,
  nummeriertem Anfang, Rand oben/unten 8 %, Abstand > typischer Abstand + 0,35 × Grundgröße,
  früh endender Vorzeile, Ausrückung, Größenwechsel > 15 %); Überschrift `###`, wenn kurz,
  nicht Verzeichniszeile, nicht mit `.`/`:` endend und ≥ 1,15 × Grundgröße oder fett und
  nummeriert; Silbentrennung („Netz-|nutzung" → „Netznutzung", „GELI-|Anmeldung" bleibt);
  Aufzählungszeichen `•▪■◦·●‣⁃➢→` und Wingdings `U+F000`–`U+F0FF`, schwach `- – * o` mit
  Leerzeichen; Kopf-/Fußzeilen = einer der ersten/letzten zwei Absätze, der ohne Ziffern auf
  ≥ 3 Seiten wiederkehrt; Bilder auf jeder Seite = Logo; JPEG unverändert, sonst PNG;
  Rückfall auf reinen Text, wenn die Seitenanalyse scheitert.
- Tests: `SampleConversionTests.cs` (`sample.pdf` → `sample.pdf.expected.md`,
  `Pdf_DropsTheLogoOnEveryPage_AndKeepsTheChart`, ohne Bilder, nicht suchbarer Stream,
  beschädigtes PDF). Beispiel `sample.pdf` (3,9 KB, neutral, 3 Seiten).
- Vorhanden: `markdown/text.py` (`escape`, `escape_line_start`, `destination`, `normalize`),
  `ConversionOptions`, `ResourceCollector`, `MetadataKeys`, Testhelfer `tests/expected.py`.
  Extra `pdf`: pdfplumber 0.11 (pdfminer.six), pikepdf 10.

## Vorgeschlagener Ansatz

1. `src/pta_documents/conversions/pdf.py`: `PdfConverter` mit `format`, `can_convert()` und
   `convert(data: bytes | BinaryIO, options) -> MarkdownDocument` wie `DocxConverter`; jede
   Ausnahme beim Lesen wird `DocumentConversionError(PDF, "The PDF could not be read: …")`,
   verschlüsselte PDFs mit eigener Meldung.
2. Zeilen aus `page.extract_words(extra_attrs=["fontname", "size", "upright"])`, nur aufrechte
   Wörter. pdfplumber misst von oben (`top`/`bottom` wachsen nach unten), PdfPig von unten — die
   Vergleiche in `BuildLines`, `PageParagraphs` und `InMargin` werden entsprechend gedreht, die
   Schwellen bleiben gleich. Fett: ≥ 80 % der Zeichen mit „Bold" im Schriftnamen; Grundgröße:
   häufigste auf 0,5 pt gerundete Zeichengröße der Seite, sonst Median der Zeilen.
3. Absatz-, Überschriften-, Listen- und Trennheuristik, Kopf-/Fußzeilen-Erkennung,
   `## Page n`, enge Listen und `normalize` 1:1 aus `PdfConverter.cs` (Regex `NumberedStart`,
   `TableOfContentsEntry`, `KeyNoise` übernommen). Rückfall: `page.extract_text()` zeilenweise.
4. Bilder: Positionen und Namen aus `page.images` (von oben nach unten), Dekodierung über
   pikepdf (`PdfImage`): `DCTDecode` als JPEG unverändert, sonst `as_pil_image()` → PNG; was
   nicht dekodierbar ist, zählt in `skippedImages`. Gleiche Bilder (SHA-256) auf jeder Seite
   fallen weg, die übrigen heißen `page{n}-image{i}.png|.jpg` über `ResourceCollector`.
5. Metadaten: `pageCount`, `title` und `author` aus dem Info-Dictionary (getrimmt, nur wenn
   nicht leer), `skippedImages` nur wenn > 0.
6. Registrierung in `ConverterRegistry.default()` (E07-S01).
7. Tests `tests/conversions/test_pdf.py`: `sample.pdf` aus DocLibs nach
   `tests/conversions/samples/` mit `sample.pdf.expected.md`; Logo fällt weg, Diagramm bleibt
   (`images/page2-image1.png`, `image/png`), Metadaten `3`/„Sample document"/„DocLibs", kein
   „of 3" im Text, ohne Bilder, nicht suchbarer Stream, `%PDF-1.7 broken` → Fehler mit Format
   `pdf`, `assert_resources_match_references`. Dazu Einzeltests der Heuristiken (Trennung,
   Aufzählungszeichen, nummerierte Überschrift, Verzeichniszeile) auf erfundenen Zeilen.

## Akzeptanzkriterien

- [ ] `sample.pdf` ergibt `sample.pdf.expected.md` aus DocLibs — oder eine Abweichung, die durch
      pdfplumber bedingt und in den Implementierungsnotizen begründet ist.
- [ ] Das Logo auf jeder Seite und die laufende Fußzeile fehlen im Markdown; das Diagramm auf
      Seite 2 ist eine Ressource.
- [ ] Ressourcen und Bildverweise im Markdown stimmen überein.
- [ ] Ein beschädigtes PDF wirft `DocumentConversionError` mit Format `pdf`.
- [ ] Ein PDF aus dem PTA-PDF-Generator (E05) liest sich ohne Kopf- und Fußzeile zurück
      (Rundreise-Tests in E05-S02).

## Offene Fragen

1. DocLibs erkennt keine Tabellen in PDFs — sie werden zu Absätzen. pdfplumber kann Tabellen mit
   Linien finden (`find_tables`). Soll der Konverter das über DocLibs hinaus nutzen und Pipe-
   Tabellen schreiben (hilfreich für PTA-PDFs mit Linien-Tabellen), oder zunächst 1:1 portieren?

> (2026-11-07) Tabellen mit `find_tables` erkennen und als Pipe-Tabellen schreiben.

## Notizen

- Wie der PPTX-Konverter (E07-S03) bleibt die Seitenüberschrift englisch (`## Page n`), damit
  die Ausgaben der Konverter einheitlich sind.
- Gescannte Seiten ohne Textschicht ergeben leere Seiten; OCR ist nicht vorgesehen.
- Der PDF-Generator (E05-S02) braucht diesen Konverter für seine Rundreise-Tests; er sollte
  daher vor oder mit E05-S02 umgesetzt werden.
- (E07-S01, docs-2) Die Registry ist vorbereitet: `ConverterRegistry.default()` importiert
  `pta_documents.conversions.pdf` (`registry.PDF_CONVERTER_MODULE`) und registriert
  `PdfConverter()` an erster Stelle, sobald das Modul existiert und `pdfplumber`/`pikepdf`
  (`registry.PDF_EXTRA_MODULES`) importierbar sind — nichts weiter zu tun, außer ggf. den Import
  direkt zu schreiben. `sample.pdf` liegt schon in `tests/conversions/samples/` (Autor
  „VT-Tools" byte-gleich lang durch „PTA-Docs" ersetzt). Der Test
  `test_the_pdf_converter_is_registered_first_when_it_can_be_imported` simuliert das Modul;
  dazu ein echter Test mit `convert(sample.pdf)`.
