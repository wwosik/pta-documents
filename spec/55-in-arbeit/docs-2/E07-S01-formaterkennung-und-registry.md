# E07-S01 Formaterkennung und Registry

> Status: in Bearbeitung (docs-2)
> Epic: [E07 Konvertierung nach Markdown](../../50-entwurf/E07-konvertierung-nach-markdown.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Ein Einstieg für alle Konverter: das Format eines Dokuments wird am Inhalt erkannt und das
Dokument an den passenden Konverter gegeben. Alte Office-Binärformate (OLE) und andere nicht
unterstützte Formate werden mit einer Meldung abgelehnt, die sagt, was zu tun ist.

## Kontext

- DocLibs: `DocumentFormatDetector.cs` (96 Zeilen), `DocumentConverterRegistry.cs` (32),
  `IDocumentConverter.cs` (30), `DocumentFormat.cs` (47); Tests `DocumentFormatDetectorTests.cs`
  (5 Fälle) und die Registry-Fälle in `SampleConversionTests.cs`
  (`WithoutImages_NothingIsExtractedOrReferenced`, `UnsupportedFormats_AreRejectedByTheRegistry`,
  `TheRegistry_PassesTheFileNameOn`).
- Schon portiert: `DocumentFormat` (alle Werte, `errors.py`), `ConversionOptions` mit
  `file_name` und `ResourceCollector` (`conversions/options.py`), `DocxConverter` und
  `PptxConverter` mit `can_convert()`/`convert(data, options)`. Der PDF-Konverter folgt in
  E07-S04 und braucht das Extra `pdf`.
- `DocumentConversions.WindowsOnly` (`.doc`, `.rtf`, `.xls`, `.xlsx` über Office-COM) entfällt
  (Entscheidung 2026-11-06); OLE-Dateien werden erkannt und abgelehnt (E07).

## Vorgeschlagener Ansatz

1. `src/pta_documents/conversions/detect.py`: `detect(data: bytes | BinaryIO, file_name: str |
   None = None) -> DocumentFormat`, Port von `DocumentFormatDetector.cs`: erste 8 KB prüfen —
   `PK\x03\x04` → ZIP-Einträge `word/document.xml` (DOCX), `xl/workbook.xml` (XLSX),
   `ppt/presentation.xml` (PPTX), sonst ZIP, kaputtes ZIP → UNKNOWN; OLE-Signatur
   `D0 CF 11 E0 A1 B1 1A E1` → nach Endung DOC (`.doc`, `.dot`), XLS (`.xls`, `.xlt`, `.xla`),
   PPT (`.ppt`, `.pps`, `.pot`), MSG (`.msg`), sonst OLE; `%PDF` → PDF; `{\rtf` → RTF; kein
   NUL-Byte → TEXT; sonst UNKNOWN. Der Inhalt gewinnt immer über die Endung. Bei `BinaryIO` muss
   der Stream suchbar sein (sonst `ValueError`); die Position wird wiederhergestellt.
2. `src/pta_documents/conversions/registry.py`: Protocol `DocumentConverter` (`can_convert`,
   `convert`), `ConverterRegistry(converters)` mit `can_convert(format)` und
   `convert(data, file_name=None, options=None)`: Eingabe einmal lesen (`read_input`, damit
   auch nicht suchbare Streams gehen), Format erkennen, ersten passenden Konverter nehmen und ihm
   `options` mit `file_name` geben.
3. `ConverterRegistry.default(*additional)`: PDF (nur, wenn das Extra `pdf` importierbar ist),
   DOCX, PPTX, dann `additional`.
4. Ablehnungen als `DocumentConversionError(format, reason)` — englisch wie alle API-Meldungen:
   - DOC, XLS, PPT, MSG, OLE: „Legacy binary Office files … are not supported. Save the file as
     .docx, .xlsx or .pptx and convert that."
   - RTF, XLSX: welche Formate stattdessen gehen (Word speichern als `.docx`).
   - PDF ohne Extra: „PDF needs the optional extra 'pdf' (pip install -e '.[pdf]')."
   - ZIP, TEXT, UNKNOWN: „No converter is registered for this format." (wie DocLibs), dazu die
     Liste der unterstützten Formate.
5. `src/pta_documents/conversions/__init__.py` exportiert `detect`, `ConverterRegistry`,
   `DocumentConverter`, `ConversionOptions` und eine Abkürzung `convert(data, file_name=None,
   options=None)` über `ConverterRegistry.default()`.
6. Tests `tests/conversions/test_detect.py` und `test_registry.py`: die DocLibs-Fälle (Beispiele
   werden erkannt, OLE ohne bekannte Endung ist OLE, Inhalt schlägt irreführende Endung,
   Binäres und Leeres ist UNKNOWN, Position bleibt), dazu Registry ohne Bilder, ZIP abgelehnt,
   Dateiname wird weitergegeben (Spion-Konverter), jede OLE-Art mit klarer Meldung, nicht
   suchbarer Stream. Beispieldateien: `sample.pdf`, `sample.txt`, `sample.zip` aus
   `DocumentConversions.Tests/Samples`, `sample.doc`, `sample.xls`, `sample.xlsx`, `sample.rtf`
   aus `DocumentConversions.WindowsOnly.Tests/Samples` (nur für die Erkennung; neutral).
7. `docs/verwendung.md`: Abschnitt „Beliebiges Dokument → Markdown" mit `convert(...)` und den
   abgelehnten Formaten.

## Akzeptanzkriterien

- [ ] Alle Beispieldateien werden richtig erkannt, unabhängig von einer irreführenden Endung.
- [ ] `convert()` gibt PDF, DOCX und PPTX an ihren Konverter und reicht den Dateinamen weiter.
- [ ] `.doc`, `.xls`, `.ppt`, `.msg` und unbekannte OLE-Dateien werden mit einer Meldung
      abgelehnt, die das Speichern im neuen Format nennt.
- [ ] Ein fehlendes Extra `pdf` ergibt eine Meldung mit dem Installationsbefehl, keinen
      `ImportError`.
- [ ] Die übernommenen DocLibs-Tests sind grün.

## Offene Fragen

1. Soll eine reine Textdatei (`TEXT`, z. B. `.md` oder `.txt`) unverändert als Markdown
   durchgereicht werden (ein `MarkdownDocument` mit dem Text), oder wie in DocLibs abgelehnt?
   Vorschlag: ablehnen, weil Markdown-Dateien gar nicht konvertiert werden müssen.

> (2026-11-07) Ablehnen.

## Notizen

- Die „Ressourcensammlung" aus der Scope-Tabelle des Epics ist mit E07-S02 schon umgesetzt
  (`ResourceCollector`); hier kommt nichts hinzu.
- Abhängig von E07-S04 nur für den PDF-Teil der Registry; bis dahin enthält `default()` DOCX und
  PPTX, und PDF wird mit der Extra-Meldung abgelehnt.
