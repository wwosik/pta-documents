# E02-S04 Code-Block-Renderer und Bildkonverter

> Status: in Prüfung
> Epic: [E02 Markdown-Grundlagen der Generatoren](../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

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

- [x] Ein Test-Renderer, der für `testbild` ein PNG liefert, ergibt in DOCX und PPTX ein Bild an
      der Stelle des Codeblocks.
- [x] Ein Test-Konverter für `image/svg+xml` macht ein SVG-Bild in DOCX und PPTX setzbar.
- [x] Jeder Fehler eines Renderers oder Konverters erreicht den Aufrufer als
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

## Implementierungsnotizen

Umgesetzt am 2026-11-07 von `docs-2`.

**Was entstand**

- `generation/common/renderers.py`: `CodeBlockRequest(info, code, line, format, language,
  dark=False)`, `CodeBlockRenderer` (`Protocol` mit `render` und der Eigenschaft
  `authoring_guide`), `DrawingGraphic`, `ImageGraphic`, `ChartGraphic`, `CodeBlockGraphic`,
  `render(renderers, request)` und `default_renderers()`.
- `generation/common/images.py`: `ImageConverter` (`Protocol` mit `convert(image, scale)` und der
  Eigenschaft `format` wie DocLibs `IImageConverter.Format`, für die Guides), `ConvertedImage`,
  `Conversion(image, width, height)` (das Ergebnis am Pfad des Originals),
  `convert_image(converters, image, scale, format)`, `GENERATOR_SCALE = 2`,
  `default_converters()`.
- `charts/spec.py` (neues Paket `pta_documents.charts`): `ChartKind`, `ChartSeries`, `ChartSpec`
  mit `colors = design.colors.ACCENTS`.
- `generation/common/code_blocks.py`: `draw(renderers, notes, info, code, line, format,
  language, dark)` — fragt die Renderer nur bei nicht leerem Info-String, notiert
  `code-not-drawn` nur, wenn nichts gezeichnet hat, gibt `ImageGraphic` zurück und wirft für
  `DrawingGraphic`/`ChartGraphic` ``Line N: The `x` block was rendered as a drawing|chart, which
  DOCX|PPTX does not support yet. …``.
- `DocxOptions`/`PptxOptions`: `code_block_renderers` und `image_converters` mit
  `field(default_factory=default_renderers|default_converters)`.
- DOCX (`BodyWriter`): Fence → `draw`; ein Bild steht in einem Absatz „Standard" ohne
  Beschriftung, Alt-Text = Info-String. `picture` ist aufgeteilt in Ressourcensuche und
  `place_picture(paragraph, resource, source, alt, title, line)`, das nicht unterstützte Formate
  konvertiert und in der natürlichen Größe aus `ConvertedImage` setzt (96 dpi, wie bisher auf
  Satzspiegel und 80 % Seitenhöhe begrenzt). `image-enlarged` rechnet mit den Pixeln der
  konvertierten Datei (ein 2×-PNG in natürlicher Größe gilt also nicht als vergrößert).
- PPTX (`DeckParser`): Fence → `_draw`; ein Bild wird ein `Images`-Visual, also wie ein
  Markdown-Bild allein (eigene Folie bzw. Bildplatzhalter). Bilder werden schon im Parser
  geprüft und konvertiert (`_placeable`); die Prüfung im Writer (`fill_picture`) entfiel, und
  `PICTURE_TYPES` liegt jetzt in `pptx/model.py`. `DeckParser` bekommt die Optionen (nach Front
  Matter) und kennt `dark` des laufenden `##`.
- Tests: `tests/generation/common/test_renderers.py` (25) und `test_images.py` (22), jeweils für
  DOCX und PPTX; 266 → 313 Tests.
- Doku: `docs/verwendung.md` Abschnitt „Code-Block-Renderer und Bildkonverter", Zeile
  `code-not-drawn` angepasst. `docs/anleitung.md` und `docs/ki-anleitung.md` unverändert: für
  Schreiber ändert sich nichts, solange die Bibliothek keine eigenen Renderer/Konverter hat.

**Entscheidungen und Abweichungen**

- Frage 1 („standardmäßig einschalten, wenn verfügbar; abschaltbar"): umgesetzt als
  `default_factory` auf `default_renderers()`/`default_converters()`; `()` schaltet ab. Beide
  Funktionen liefern heute `()`, E06-S01/S03/S04 tragen sich dort ein (in deren Notizen vermerkt).
- Die Hilfsfunktion heißt `convert_image` statt `convert` (eindeutiger beim Import in die
  Writer); sie gibt `Conversion` zurück statt eines Tupels.
- PPTX: Ein Bild in nicht unterstütztem Format in einer **Bildreihe** lief vorher ohne Prüfung bis
  python-pptx (unklarer Fehler); jetzt meldet der Parser es wie das Einzelbild. Die Meldung endet
  nun auf `(line N)` des Absatzes (wie die übrigen Parser-Meldungen) statt der Zeile des `##`.
- Fehlermeldungen eines Renderers: wie im Plan `str(error)` ohne Zeile; die Zeile steht im
  `CodeBlockRequest`, ein Renderer kann sie selbst nennen.

**Warnungen**

- **Warnung:** `DrawingGraphic.drawing` und `ChartGraphic.drawing` sind als `object` typisiert,
  weil das Zeichenmodell (E02-S03, M03) noch nicht existiert. E02-S03 soll den Typ auf `Drawing`
  festziehen.
- **Warnung:** In PPTX wird ein Bild aus einem Renderer wie ein Markdown-Bild gesetzt — allein auf
  einer Folie also in den Bildplatzhalter von „Titel und Bild", der beschneidet (`image-cropped`).
  Für Diagramme ist das ungeeignet; E04-S04/E06 setzen Grafiken eigens.
- **Warnung:** PPTX setzt Bilder ohnehin passend in ihre Fläche; die natürliche Größe aus
  `ConvertedImage` wirkt dort heute nicht (nur in DOCX). Das Original (z. B. SVG für
  `asvg:svgBlip`) wird nicht mitgeführt — E06-S04 muss es dem `Image`-Modell hinzufügen.

**Prüfpunkte**

- Ein konvertiertes Bild bzw. ein Renderer-Bild in Word und PowerPoint öffnen (keine Office-
  Installation auf der Entwicklungsmaschine).
