# E07-S04 PDF → Markdown

> Status: in Prüfung
> Epic: [E07 Konvertierung nach Markdown](../50-entwurf/E07-konvertierung-nach-markdown.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

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

- [x] `sample.pdf` ergibt `sample.pdf.expected.md` aus DocLibs — oder eine Abweichung, die durch
      pdfplumber bedingt und in den Implementierungsnotizen begründet ist.
- [x] Das Logo auf jeder Seite und die laufende Fußzeile fehlen im Markdown; das Diagramm auf
      Seite 2 ist eine Ressource.
- [x] Ressourcen und Bildverweise im Markdown stimmen überein.
- [x] Ein beschädigtes PDF wirft `DocumentConversionError` mit Format `pdf`.
- [x] Ein PDF aus dem PTA-PDF-Generator (E05) liest sich ohne Kopf- und Fußzeile zurück
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

## Implementierungsnotizen

### Entscheidungen

- `src/pta_documents/conversions/pdf.py`: `PdfConverter` (`format`, `can_convert`, `convert`)
  wie DOCX/PPTX; Wörter mit `extract_words(return_chars=True)` (Fett und Schriftgröße aus den
  Zeichen, Wörter werden so nicht an Schriftwechseln zerteilt), die Schwellen von DocLibs als
  Konstanten, die Vergleiche auf pdfplumbers Koordinaten (von oben) gedreht. Die Heuristiken sind
  einzeln testbare Funktionen (`build_lines`, `paragraphs`, `paragraph_markdown`, `join`,
  `strip_bullet`, `running_paragraphs`, `code_block`, `ruled_tables`).
- Die Registry bleibt unverändert lazy (`PDF_CONVERTER_MODULE`): der Kern importiert pdfplumber
  weiterhin nie; nur der Kommentar in `_pdf_converter` ist angepasst.
- Bilder: pdfplumber liefert Lage und Objektnummer (`stream.objid`), pikepdf dekodiert
  (`PdfImage`). JPEG bleibt unverändert, auch hinter `ASCII85Decode`/`FlateDecode` (reportlab
  schreibt JPEG so); alles andere wird PNG. Inline-Bilder (ohne eigenes Objekt) und nicht
  dekodierbare zählen in `skippedImages`.
- Tabellen (Antwort auf Frage 1): Gitter über `find_tables` (Linien in beiden Richtungen);
  zusätzlich `ruled_tables` für den Stil `PTA` des PDF-Generators, der nur waagerechte Linien
  hat — mit `find_tables` und der Textstrategie entstanden falsche Tabellen aus Codeblöcken.
  Zellen werden wie Absätze zusammengefügt (Trennung repariert), `|` maskiert.
- Verschlüsselte PDFs: eigene Meldung `ENCRYPTED`, erkannt an `PDFPasswordIncorrect`/
  `PasswordError` in der Ausnahmekette; alles andere wird „The PDF could not be read: …".
- `sample.pdf.expected.md` ist die Datei aus DocLibs (`~/mvv/vt-tools-libs`), byte-gleich; der
  Konverter erzeugt sie ohne Abweichung (der Autor „PTA-Docs" steht nur in den Metadaten).

### Abweichungen von DocLibs (Erweiterungen)

Alle ändern das Ergebnis von `sample.pdf` nicht; sie sind nötig, damit PDFs des PTA-Generators
lesbar zurückkommen:

- Tabellen als Pipe-Tabellen (siehe oben, vom Menschen gewünscht).
- Gezeichnete Aufzählungszeichen: der PDF-Generator zeichnet ■ und ― als Formen, nicht als
  Zeichen. Kleine gefüllte Quadrate und kurze Striche vor einer Zeile beginnen einen Punkt
  `- `, kleine leere Quadrate ein Aufgabenkästchen `- [ ] ` (mit Linien darin `- [x] `).
- Codeblöcke: Zeilen überwiegend in Festbreitenschrift werden ein Zaun ohne Sprache, mit
  Einrückung und Leerzeilen aus den Abständen; die Füllfläche des Codeblocks hält ihn zusammen.
  DocLibs machte aus jeder Codezeile einen Absatz.
- Bilder stehen an ihrer Stelle im Text statt gesammelt am Seitenende.
- Wörter mit überwiegend gleicher Höhe gehören zu einer Zeile (hochgestellte Fußnotenzeichen
  wurden sonst eine eigene Zeile); Wörter ohne Abstand werden ohne Leerzeichen verbunden.
- Kopf-/Fußzeilen: ein Schlüssel, der auf einer Seite mehrfach vorkommt, ist keine Kopf- oder
  Fußzeile — sonst fielen in `long.md` die Punkte 23–25 weg (sie unterscheiden sich nur in den
  Ziffern).
- Gedreht oder senkrecht gesetzte Zeichen (Wasserzeichen „ENTWURF", das pdfplumber für
  `upright` hält) werden vor der Analyse entfernt.

### Warnungen

- **Warnung:** Die Erweiterungen über DocLibs hinaus (gezeichnete Aufzählungszeichen,
  Aufgabenkästchen, Codezäune, Bilder im Fluss, Kopfzeilen-Ausnahme, Zeilen nach Höhe) sind
  eigene Entscheidungen ohne Rückfrage — gewählt, weil die Rundreise der PTA-PDFs sonst
  unbrauchbar ist und `sample.pdf` unverändert bleibt. Die Schwellen (Markergröße 0,2–0,9 ×
  Grundgröße, Abstand ≤ 2,5 × Zeilengröße, Schriftnamen in `MONOSPACED`) sind am PDF-Generator
  abgelesen, nicht an fremden PDFs geprüft.
- **Warnung:** Der Titel auf dem Deckblatt eines PTA-PDFs entfällt, weil er auch in jeder
  Kopfzeile steht (DocLibs-Regel). Er steht in `metadata["title"]`. Vorsichtig belassen statt
  das Deckblatt auszunehmen.
- **Warnung:** Alle Überschriften werden `###` wie in DocLibs; die Ebene ließe sich aus den
  Lesezeichen des PDFs lesen, das ist nicht umgesetzt (Offener Punkt).
- **Warnung:** In PTA-Tabellen mit rechtsbündiger Spalte vor einer linksbündigen stößt der Text
  ohne Zellenrand an (Zellenränder links/rechts 0 wie in Word); pdfplumber liest dann ein Wort
  („1Row 1" in `long.roundtrip.expected.md`). Das ist eine Eigenschaft des erzeugten PDFs, im
  Konverter nicht zu trennen — siehe Notiz in E05-S02.

### Prüfpunkte

- `tests/conversions/test_pdf.py` (43 Tests): Beispiel gegen die DocLibs-Erwartung, Logo weg und
  Diagramm als Ressource, Metadaten (`3`, „Sample document", „PTA-Docs"), kein „Sample document"
  und kein „of 3" im Text, Registry, ohne Bilder, Präfix der Ressourcen, nicht suchbarer Stream,
  beschädigtes und leeres PDF, Kennwort, nicht dekodierbares Bild (`skippedImages`), JPEG
  unverändert, Wasserzeichen, Gittertabelle, `plain_quotes`, leeres PDF; Heuristiken auf
  erfundenen Zeilen (Trennung, Aufzählungszeichen, Überschriften und Verzeichniszeile,
  Absatzgrenzen, Seitenränder, Tabellengrenze, Codezaun, Kopf-/Fußzeilen).
- Rundreise mit Seitenrahmen: `tests/generation/pdf/layout/test_samples.py::
  test_the_round_trip_through_the_pdf_converter` (`report`, `long`); die PDFs liegen in
  `.tmp/review/pdf-roundtrip-*.pdf`. Die Erwartungen bitte lesen: „Seite", „Stand:",
  „PTA IT-Beratung" und der Titel fehlen; Listen, Tabellen und Codeblöcke kommen zurück.
- `tests/conversions/test_registry.py`: die Liste der unterstützten Formate nennt jetzt `pdf`.
- Von Hand geprüft (nicht als Test): alle Word-Beispiele aus `samples/` als PDF und zurück
  (`gsb-bericht`, `funktionen-bericht`, `varianten-*`) — ohne Fehler; Verzeichnis, Tabellen,
  Codezäune und Bilder lesbar.

### Offene Punkte

- Überschriftenebenen aus den Lesezeichen (`#`/`##`/`###` statt immer `###`).
- Verschachtelte Listen (Ebene aus dem Einzug) und nummerierte Listen als Liste statt
  `1\. …`-Absatz — DocLibs unterscheidet sie nicht von nummerierten Überschriften.
- Die Fortsetzungszeile eines Listenpunkts nach einem harten Umbruch wird ein eigener Absatz
  (DocLibs-Regel „früh endende Zeile").
- Fußnoten bleiben Ziffer am Wort und Text am Seitenfuß; keine `[^n]`.
- Der PDF-Generator nummeriert `3.`/`4.` als „1."/„2." (beobachtet in der Rundreise, E05-S02).
