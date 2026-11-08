# E07-S01 Formaterkennung und Registry

> Status: in Prüfung
> Epic: [E07 Konvertierung nach Markdown](../50-entwurf/E07-konvertierung-nach-markdown.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

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

- [x] Alle Beispieldateien werden richtig erkannt, unabhängig von einer irreführenden Endung.
- [x] `convert()` gibt PDF, DOCX und PPTX an ihren Konverter und reicht den Dateinamen weiter
      (PDF bis E07-S04 nur mit simuliertem Konverter geprüft).
- [x] `.doc`, `.xls`, `.ppt`, `.msg` und unbekannte OLE-Dateien werden mit einer Meldung
      abgelehnt, die das Speichern im neuen Format nennt.
- [x] Ein fehlendes Extra `pdf` ergibt eine Meldung mit dem Installationsbefehl, keinen
      `ImportError`.
- [x] Die übernommenen DocLibs-Tests sind grün (der PDF-Fall von
      `WithoutImages_NothingIsExtractedOrReferenced` folgt mit E07-S04).

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

## Implementierungsnotizen

- `conversions/detect.py` (`detect`), `conversions/registry.py` (`DocumentConverter`,
  `ConverterRegistry`, `convert`, `pdf_extra_available`); `conversions/__init__.py` exportiert
  `detect`, `ConverterRegistry`, `DocumentConverter`, `ConversionOptions`, `convert`. Tests
  `tests/conversions/test_detect.py`, `test_registry.py` (435 → 485 Tests).
- **PDF-Registrierung vorbereitet:** `default()` lädt `pta_documents.conversions.pdf`
  (`PDF_CONVERTER_MODULE`) per `importlib` und registriert `PdfConverter()` an erster Stelle,
  wenn `pdfplumber` und `pikepdf` (`PDF_EXTRA_MODULES`) per `find_spec` gefunden werden und das
  Modul existiert. Fehlt nur das Modul selbst, wird still übersprungen; jeder andere
  `ModuleNotFoundError` wird weitergereicht, damit ein Fehler in E07-S04 nicht verschluckt wird.
  Notiz in E07-S04 ergänzt.
- **Warnung (PDF-Meldung):** Ist das Extra installiert (wie in `.venv`), aber der Konverter noch
  nicht da, lautet die Ablehnung „No converter is registered for this format." mit der Liste —
  die Extra-Meldung kommt nur, wenn das Extra wirklich fehlt (Test per `monkeypatch`).
- **Warnung (Meldungstexte):** Der Plan nennt für DOC/XLS/PPT/MSG/OLE eine gemeinsame Meldung
  „Save the file as .docx, .xlsx or .pptx". Da `.xlsx` selbst abgelehnt wird, nennt jede Art ihr
  eigenes Ziel: `.doc` → `.docx`, `.ppt` → `.pptx`, `.xls` → Tabellen nach Word kopieren und als
  `.docx` speichern, `.msg` → Anhänge bzw. Nachricht als `.docx`/`.pptx`, OLE → `.docx`/`.pptx`.
  Alle beginnen mit „Legacy binary Office files (…) are not supported." RTF, XLSX und TEXT haben
  eigene Sätze und hängen wie ZIP/UNKNOWN die unterstützten Formate an
  („Supported formats: docx, pptx.").
- `TEXT` wird abgelehnt (Antwort 2026-11-07).
- `detect` auf einem Stream liest ab der aktuellen Position; liegt sie nicht bei 0, wird für
  ZIP-Inhalte der Rest in Bytes gelesen (zipfile sucht relativ zum Dateiende). Die Position wird
  immer wiederhergestellt; nicht suchbare Streams → `ValueError`. Kaputte ZIPs → `unknown`.
- `ConverterRegistry.convert` liest die Eingabe einmal (`read_input`) und gibt den Konvertern
  Bytes; `file_name` überschreibt `options.file_name` per `dataclasses.replace`, die übrigen
  Optionen bleiben. Zusätzlich `ConverterRegistry.formats` (Formate, die ein Konverter annimmt).
- **Beispieldateien:** `sample.pdf/.txt/.zip` aus `DocumentConversions.Tests/Samples`,
  `sample.doc/.xls/.xlsx/.rtf` aus `DocumentConversions.WindowsOnly.Tests/Samples` von
  `~/mvv/vt-tools-libs`. Für Neutralität ist der Autor „VT-Tools" byte-gleich lang durch
  „PTA-Docs" ersetzt (in OLE auch UTF-16; XLSX neu gepackt); PDF öffnet mit pdfplumber weiter.
  `sample.docx`/`.pptx` sind die vorhandenen des Repos.
- Doku: `docs/verwendung.md` Abschnitt „Beliebiges Dokument → Markdown", `docs/ki-anleitung.md`
  nutzt jetzt `convert(...)` und nennt die abgelehnten Formate. `ai/Gedächtnis.md` ergänzt.
- **Prüfpunkte:** Formulierung der Ablehnungsmeldungen; ob ein Stream mit Position ≠ 0 so
  behandelt werden soll.
- **Offen:** PDF-Teil (echter Konverter, `WithoutImages`-Fall für PDF) mit E07-S04.
