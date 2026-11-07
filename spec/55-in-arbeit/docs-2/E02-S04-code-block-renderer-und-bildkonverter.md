# E02-S04 Code-Block-Renderer und Bildkonverter

> Status: in Bearbeitung (docs-2)
> Epic: [E02 Markdown-Grundlagen der Generatoren](../../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Zwei Erweiterungspunkte, über die Diagramme, Charts und fremde Bildformate in die Generatoren
kommen: Renderer machen aus einem Codeblock (`mermaid`, `chart` …) eine Grafik, Konverter machen
aus einem Bild, das ein Generator nicht setzen kann (SVG), ein PNG — beide mit einheitlicher
Fehlerweitergabe als `DocumentConversionError`.

## Kontext

- DocLibs: `DocumentGeneration/CodeBlockRenderer.cs` (136 Zeilen: `ICodeBlockRenderer` mit
  `Render` und `AuthoringGuide`, `CodeBlockRequest(Language, Code, Brand)` mit `Line`,
  `DrawingGraphic`, `ImageGraphic`, `ChartGraphic(ChartSpec, Drawing)`, `ChartSpec`,
  `ChartSeries`, `ChartKind`, `CodeBlockRenderers.Render`), `ImageConverters.cs` (38),
  `DocumentConversions/IImageConverter.cs` (23: `Convert(image, scale)`, `ConvertedImage`).
- Verhalten: Renderer und Konverter werden der Reihe nach gefragt, das erste Ergebnis gewinnt;
  `None` heißt „nicht meins". Eine fremde Ausnahme wird zu `DocumentConversionException` im
  Format des Generators mit der ursprünglichen als `InnerException`; eine
  `DocumentConversionException` geht unverändert durch. Generatoren fragen Konverter mit
  `scale = 2`.
- Heute: DOCX und PPTX werfen bei SVG und anderen Formaten (E03-S02, E04-S01); Codeblöcke sind
  immer Code. `ImageInfo.cs` (Kopf von PNG/JPEG/GIF lesen) wird nicht portiert — Pillow erledigt
  das bereits.

## Vorgeschlagener Ansatz

1. `src/pta_documents/generation/common/renderers.py` (öffentlich):
   - `CodeBlockRequest(info, code, line, format: DocumentFormat, language: Language,
     dark: bool = False)` — `info` ist der Info-String des Zauns (in DocLibs `Language`); statt
     des Brands bekommt der Renderer Zielformat, Dokumentsprache (`sprache:`, für erzeugte Texte
     und Zahlenformat) und ob die Folie dunkel ist; Farben nimmt er aus `design.colors`.
   - `CodeBlockRenderer` als `Protocol`: `render(request) -> CodeBlockGraphic | None` und
     `authoring_guide: str | None` (Abschnitt ab `##`, deutsch, für E02-S05).
   - `DrawingGraphic(drawing)`, `ImageGraphic(resource)`, `ChartGraphic(chart, drawing)`,
     `CodeBlockGraphic = DrawingGraphic | ImageGraphic | ChartGraphic`.
   - `ChartSpec(kind, categories, series, stacked=False, title=None, unit=None,
     colors=colors.ACCENTS)`, `ChartSeries(name, values: tuple[float | None, ...])`,
     `ChartKind` (`BAR`, `LINE`, `AREA`) in `src/pta_documents/charts/spec.py` — dem Paket, das
     E06-S01 um Parser, Zeichnung und `source` ergänzt; hier nur die Datentypen.
   - `render(renderers, request) -> CodeBlockGraphic | None` mit Fehlerweitergabe
     (`raise DocumentConversionError(format, str(error)) from error`).
2. `src/pta_documents/generation/common/images.py`: `ImageConverter`-`Protocol`
   (`convert(image: DocumentResource, scale: float) -> ConvertedImage | None`),
   `ConvertedImage(content, content_type, width, height)` (natürliche Größe in Pixeln),
   `convert(converters, image, scale, format)` mit Meldung „The image '…' cannot be converted: …".
3. **Optionen:** `DocxOptions` und `PptxOptions` bekommen `code_block_renderers:
   tuple[CodeBlockRenderer, ...] = ()` und `image_converters: tuple[ImageConverter, ...] = ()`
   (später auch `PdfOptions`, E05).
4. **Einbindung, soweit ohne E06 möglich:**
   - Ein Fence mit Info-String geht an die Renderer, mit der Zeile des öffnenden Zauns inklusive
     Front Matter; `None` lässt ihn Code. `ImageGraphic` wird wie ein Markdown-Bild gesetzt,
     mit dem Info-String als Alt-Text wie in DocLibs; in DOCX ohne „Abbildung n"-Beschriftung
     (die kommt mit E03-S04 aus dem Diagrammtitel). `DrawingGraphic`/`ChartGraphic` werfen, bis E03-S04 bzw. E04-S04/E06
     sie zeichnen, einen Fehler „… noch nicht unterstützt".
   - Bilder in nicht unterstützten Formaten gehen an die Konverter; das Ergebnis wird in seiner
     natürlichen Größe gesetzt wie ein PNG dieser Größe. Ohne Ergebnis bleibt der bisherige Fehler.
5. **Tests** (Port aus DocLibs `PptxGeneratorTests`, `GenerationTests`, `SvgConverterTests`):
   Renderer bekommt Info-String, Code und Zeile nach Front Matter (`line == 6`); `None` lässt Code
   stehen; erster Treffer gewinnt; fremde Ausnahme → `DocumentConversionError` mit `__cause__`;
   `DocumentConversionError` geht unverändert durch; Konverter analog; SVG ohne Konverter bleibt
   Fehler — jeweils für DOCX und PPTX.

## Akzeptanzkriterien

- [ ] Ein Test-Renderer, der für `testbild` ein PNG liefert, ergibt in DOCX und PPTX ein Bild an
      der Stelle des Codeblocks.
- [ ] Ein Test-Konverter für `image/svg+xml` macht ein SVG-Bild in DOCX und PPTX setzbar.
- [ ] Jeder Fehler eines Renderers oder Konverters erreicht den Aufrufer als
      `DocumentConversionError` im Format des Generators.

## Offene Fragen

1. Sollen die Generatoren Renderer und Konverter **standardmäßig** einschalten, wenn sie verfügbar
   sind (Charts immer, Mermaid und SVG→PNG, wenn mermaid-cli bzw. das Extra `svg` installiert
   ist), oder wie in DocLibs nur, wenn der Aufrufer sie übergibt (Standard leer)?

> (2026-11-07) Standardmäßig einschalten, wenn verfügbar; in den Optionen abschaltbar.

## Notizen

- E06-S01 (Schritt 6) und E06-S04 (Schritt 5) schlagen bereits vor, `ChartRenderer` bzw.
  `SvgImageConverter` standardmäßig einzutragen; Frage 1 entscheidet das für alle zusammen.
- (2026-11-07, E08-S01) `generation/common/code_blocks.py` hat `KNOWN_GRAPHIC_LANGUAGES` und
  `note_not_drawn(notes, info, line)`; beide Generatoren rufen es heute für **jeden** `fence`
  auf. Mit den Renderern nur noch aufrufen, wenn kein Renderer den Block gezeichnet hat.
