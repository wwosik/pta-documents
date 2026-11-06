# E07-S02 DOCX → Markdown

> Status: Entwurf
> Epic: [E07 Konvertierung nach Markdown](E07-konvertierung-nach-markdown.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Der DOCX-Konverter aus DocLibs in Python: `.docx` → `MarkdownDocument` mit Überschriften,
Absätzen, Listen, Tabellen, Links und Bildern. In M01 vorgezogen, weil die Rundreise-Tests des
DOCX-Generators (E03-S02) ihn brauchen.

## Kontext

DocLibs: `OpenXml/DocxConverter.cs` (461 Zeilen), `OpenXmlPackage.cs`, `ResourceCollector`,
`ConversionOptions`, `MarkdownText` (Escaping, Tabellen, Normalisierung), Beispiel
`Samples/sample.docx` mit `sample.docx.expected.md`. Der Konverter liest das XML direkt
(kein Word-Objektmodell) und ist tolerant gegenüber fremden Dokumenten.

## Vorgeschlagener Ansatz

1. `pta_documents.conversions`: `ConversionOptions` (`resource_path_prefix="images/"`,
   `include_images=True`, `file_name`), `ResourceCollector` (gleiche Bilder einmal, Namen
   eindeutig), `OpenXmlPackage` (ZIP + lxml, Beziehungen, Kerneigenschaften, beschädigte Pakete
   → `DocumentConversionError`).
2. `pta_documents.markdown.text`: `MarkdownText` aus DocLibs (`escape`, `escape_line_start`,
   `code`, `destination`, `cell`, `table`, `compact`, `normalize`) — vorgezogen aus E07-S06,
   weil alle Konverter es brauchen.
3. `DocxConverter.convert(data: bytes | BinaryIO, options) -> MarkdownDocument`, 1:1 nach
   DocLibs: Stile über ID und Namen klassifizieren (deutsch und englisch), Nummerierung aus
   `numbering.xml` (geordnet/ungeordnet je Ebene), Tabellen mit `<br>` für mehrere Absätze,
   Textfelder als `> [Text box] …`, Bilder aus DrawingML und VML, Hyperlinks, fett/kursiv mit
   zusammengeführten Runs.
4. **PTA-Ergänzung:** Die PTA-Formatvorlage `Zwischenüberschrift` (enthält „überschrift", aber
   keine Ebene) wird zu `####` statt zu `#`, damit die Rundreise des DOCX-Generators stimmt.
5. Tests: DocLibs-Beispiel `sample.docx` → `sample.docx.expected.md` (übernommen), gleiche Bilder
   einmal, ohne Bilder, beschädigtes Paket; `MarkdownText`-Fälle aus DocLibs.

## Akzeptanzkriterien

- [ ] `sample.docx` ergibt exakt `sample.docx.expected.md` aus DocLibs.
- [ ] Ressourcen und Bildverweise im Markdown stimmen überein.
- [ ] Ein beschädigtes Paket wirft `DocumentConversionError` mit Format `docx`.

## Offene Fragen

Keine — Zuschnitt folgt E07 und der Anweisung vom 2026-11-06, M01 vollständig umzusetzen.

## Notizen

Plan während der Umsetzung von M01 geschrieben (2026-11-06).
