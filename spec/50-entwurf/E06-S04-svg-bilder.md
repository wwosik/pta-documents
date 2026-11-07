# E06-S04 SVG → PNG und SVG-Bilder in Folien und Dokumenten

> Status: Entwurf
> Epic: [E06 Diagramme und Charts](E06-diagramme-und-charts.md)

## Zusammenfassung

SVG-Bilder werden sicher (nichts außerhalb des SVG wird geladen) mit resvg in PNG gewandelt. In
Folien und Word erscheinen sie als PNG mit dem SVG daneben (`asvg:svgBlip`), sodass Office 2016
und neuer das SVG scharf zeichnet; das PDF setzt das PNG.

## Kontext

- DocLibs `DocumentConversions.Svg` (300 Zeilen): `SvgConverter.cs` (170: `Size`, `ToPng`,
  `SvgPngOptions` mit `Scale` 2, `Width`, `Background`, `Fonts`; höchstens 16 384 px je Seite),
  `SvgImageConverter.cs` (49: erkennt SVG an Typ, Endung oder Inhalt), `SvgSanitizer.cs` (79:
  entfernt `script`, `foreignObject`, DTD, externe `href`, externe `url()` und `@import`).
  `Pptx/DeckWriter.cs` (Zeilen 950–975) hängt das SVG als `svgBlip`-Erweiterung
  `{96DAC541-7B7A-43D3-8B79-37D633B846F1}` an das PNG. Tests `SvgConverterTests.cs` (11),
  `ChartPngTests.cs` (1).
- resvg-py 0.5 (Extra `svg`, installiert): `svg_to_bytes(svg_string, zoom|width, background,
  font_files, skip_system_fonts, font_family, sans_serif_family, …)`; Schriften nur als Pfade,
  keine Größenabfrage.
- Heute lehnen DOCX- (`SUPPORTED_IMAGES`) und PPTX-Generator (`PICTURE_TYPES`) SVG mit einem
  Fehler ab; die Bildkonverter-Schnittstelle kommt aus E02-S04.

## Vorgeschlagener Ansatz

1. `src/pta_documents/svg/sanitizer.py`: Port von `SvgSanitizer.cs` mit lxml
   (`resolve_entities=False`, `no_network=True`); nicht wohlgeformt oder keine `svg`-Wurzel →
   `DocumentConversionError(SVG, …)`.
2. `src/pta_documents/svg/converter.py`: `natural_size(svg) -> (w, h)` selbst aus `width`/
   `height` (px, pt, mm, cm, in), sonst `viewBox` — ohne Größe ein Fehler; `to_png(svg, scale=2,
   width=None, background=None) -> bytes` über `resvg_py.svg_to_bytes` mit `zoom` bzw. `width`,
   Grenze 16 384 px, Fehler von resvg (`ValueError`) als `DocumentConversionError(SVG, …)`.
3. Schriften: resvg lädt keine Systemschriften (`skip_system_fonts=True`), sondern genau die
   PTA-Schriften aus E01-S03 (Selawik über `importlib.resources.as_file`, Segoe UI aus dem
   System, wenn vorhanden); die generischen Familien zeigen auf diese. So sieht ein PNG auf
   jedem Rechner gleich aus.
4. `src/pta_documents/svg/image_converter.py`: `SvgImageConverter` nach E02-S04 — nimmt
   `image/svg+xml`, Endung `.svg` oder Inhalt, der mit `<svg`/`<?xml … <svg` beginnt; liefert PNG
   in `scale`-facher Größe plus natürliche Größe in Pixeln; Fehler nennen den Bildpfad.
5. Die Generatoren tragen `SvgImageConverter` als Standard in `image_converters` ein, wenn
   resvg-py installiert ist; sonst nennt der Fehler für SVG-Bilder das Extra `svg`.
6. **Folien** (`generation/pptx/writer.py`, `visuals.py`): SVG-Bild → PNG als Bild, dazu das SVG
   als eigener Bildteil (`image/svg+xml`) und `a:extLst/a:ext/asvg:svgBlip r:embed` im `a:blip`.
   Gilt für Bildplatzhalter und freie Bilder; Größe aus der natürlichen Größe.
7. **Word** (`generation/docx/writer.py`): ebenso — PNG im `pic:blipFill`, SVG-Teil unter
   `word/media/` und `asvg:svgBlip`; Beschriftung „Abbildung n" wie bei anderen Bildern.
8. **PDF**: über den Konverterweg aus E05-S04 (doppelte Platzierungsgröße).
9. Zeichnungen (Finanzdiagramme, Mermaid) erreichen Word als SVG aus `DrawingSvg` (E02-S03)
   über denselben Weg — das nutzt E03-S04.
10. Tests `tests/svg/`: die Fälle aus `SvgConverterTests.cs` — PNG in doppelter Größe auf
    Transparenz, Größe aus `width`/`height` sonst `viewBox`, Hintergrund, Text in Selawik,
    unlesbares SVG als SVG-Fehler, nichts von außen (Datei-, Web- und CSS-Verweise, `@import`,
    Skripte), interne Verweise und `data:`-URIs bleiben; Folie mit PNG und SVG daneben, Tooltips
    eines Finanzdiagramms nicht im PNG, Word mit `svgBlip`, PDF in natürlicher Größe; dazu
    `ChartPngTests` (jedes Finanzdiagramm als PNG in doppelter Größe).

## Akzeptanzkriterien

- [ ] Ein SVG-Bild im Markdown erscheint in PPTX und DOCX als PNG mit `svgBlip`-Erweiterung und
      im PDF als Bild in natürlicher Größe.
- [ ] Ein SVG mit Verweisen auf Dateien, Web-Adressen oder Skripte lädt nichts davon; die
      Umwandlung arbeitet auch ohne Netz.
- [ ] Dasselbe SVG ergibt auf jedem Rechner dasselbe PNG (feste Schriften).
- [ ] Fehlerhafte SVGs ergeben eine `DocumentConversionError` mit Format `svg` und Bildpfad.
- [ ] PowerPoint und Word zeigen das SVG scharf (Prüfpunkt für den Menschen).

## Offene Fragen

1. Auflösung des PNG im PDF: DocLibs rendert in doppelter Größe (≈ 192 dpi). Für Ausdrucke
   wären dreifach (≈ 288 dpi) besser, bei größeren Dateien. Doppelt lassen oder dreifach?

> (2026-11-07) Dreifach (≈ 288 dpi).

## Notizen

- Ein beliebiges SVG als Vektor ins PDF zu übernehmen, ginge über die SVG-Übersetzung aus
  E06-S03, die aber absichtlich nur einen Teil von SVG kennt; deshalb hier das PNG.
- resvg verarbeitet CSS nur teilweise; die Tooltips von `DrawingSvg` müssen ohne `:hover`
  unsichtbar sein — der Test dazu ist Pflicht.
