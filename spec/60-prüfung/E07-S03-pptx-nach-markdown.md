# E07-S03 PPTX → Markdown

> Status: in Prüfung
> Epic: [E07 Konvertierung nach Markdown](../50-entwurf/E07-konvertierung-nach-markdown.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Der PPTX-Konverter aus DocLibs in Python: jede Folie wird ein `##`-Abschnitt mit ihrem Titel,
gefolgt von den Texten, Tabellen und Bildern der Folie. In M01 vorgezogen für die
Rundreise-Tests des PPTX-Generators (E04-S02).

## Kontext

DocLibs: `OpenXml/PptxConverter.cs` (140 Zeilen), Beispiel `sample.pptx` mit
`sample.pptx.expected.md`. Baut auf `OpenXmlPackage`, `ResourceCollector` und `MarkdownText`
aus E07-S02 auf.

## Vorgeschlagener Ansatz

1. `PptxConverter.convert(data, options) -> MarkdownDocument`, 1:1 nach DocLibs: Folien in der
   Reihenfolge von `sldIdLst`; Titel aus dem Platzhalter `title`/`ctrTitle`, sonst
   „Slide n"; alle anderen Textkörper außer Fußzeile, Datum und Foliennummer als Absätze;
   Tabellen als Pipe-Tabellen; Bilder (`p:pic`) mit Alt-Text aus `cNvPr/@descr`;
   `mc:Fallback` wird übersprungen.
2. Metadaten: `slideCount`, Titel und Autor aus den Kerneigenschaften.
3. Tests: DocLibs-Beispiel → `sample.pptx.expected.md`, ohne Bilder, beschädigtes Paket.

## Akzeptanzkriterien

- [x] `sample.pptx` ergibt exakt `sample.pptx.expected.md` aus DocLibs.
- [x] `slideCount` stimmt; ohne Bilder gibt es keine Ressourcen und keine Bildverweise.
- [x] Ein beschädigtes Paket wirft `DocumentConversionError` mit Format `pptx`.

## Offene Fragen

Keine — Zuschnitt folgt E07 und der Anweisung vom 2026-11-06, M01 vollständig umzusetzen.

## Notizen

Plan während der Umsetzung von M01 geschrieben (2026-11-06).

## Implementierungsnotizen

- `conversions/pptx.py` (`PptxConverter.convert(bytes | BinaryIO, ConversionOptions)`), 1:1 nach
  DocLibs; das DocLibs-Beispiel ergibt byte-gleich `sample.pptx.expected.md`.
- Wie in DocLibs: Textebenen und Aufzählungen werden zu einfachen Absätzen, Formatierung
  (fett, Links) geht verloren, Tabellen ohne Ausrichtung. Für die Rundreise des PPTX-Generators
  ist das in dessen `*.roundtrip.expected.md` sichtbar; eine reichere Rückwandlung wäre eine
  eigene Story.
- Auf PTA-Folien erscheint die Kapitelnummer der Trennfolie („01") als Absatz, weil sie in einem
  gewöhnlichen Textplatzhalter steht; die unsichtbaren Deko-Platzhalter sind leer und fallen weg.
