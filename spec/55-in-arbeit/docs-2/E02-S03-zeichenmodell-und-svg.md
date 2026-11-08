# E02-S03 Zeichenmodell `Drawing` und SVG-Ausgabe mit Tooltips

> Status: in Bearbeitung (docs-2)
> Epic: [E02 Markdown-Grundlagen der Generatoren](../../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Das Vektor-Zeichenmodell, in dem Charts (E06-S01/S02), Mermaid-Diagramme (E06-S03) und die Logos
(E01-S04) vorliegen, bevor PPTX sie als Formen, DOCX/PDF sie als Vektor oder Bild ausgeben — plus
ein SVG-Schreiber mit Tooltips ohne Skript für Web-Seiten und als Vorstufe für PNG (E06-S04).

## Kontext

- DocLibs: `DocumentGeneration/Drawing.cs` (241 Zeilen: `Drawing`, `DrawingItem` mit `Hover`,
  `DrawingShape` mit `Kind`/`Dash`/`CornerRadius`/`RoundJoins`, `DrawingPath` mit `MoveTo`,
  `LineTo`, `CubicTo`, `ClosePath` und `Bounds`, `DrawingText` mit `DrawingSpan`, `Anchor`,
  `MaxWidth`, `Mono`, `DrawingHotspot`) und `DrawingSvg.cs` (203 Zeilen: `Write`,
  `EstimateWidth` mit 0,58 × Größe, Tooltip 17 px hoch, Schrift 10 px, Abstand 6 px, Mindestskala
  70 %, Zahlen mit höchstens zwei Nachkommastellen, XML-sichere Texte).
- Tests: `DrawingTests.cs` (4 Fälle), `DrawingSvgTests.cs` (5 Fälle).
- Koordinaten sind CSS-Pixel (0,75 pt) von oben links, Farben `RRGGBB` ohne `#`.
- Im PTA-Paket gibt es keinen Brand: Schriftfamilien und Tooltip-Farben kommen aus
  `design.fonts` (E01-S03) bzw. `design.colors`.

## Vorgeschlagener Ansatz

1. Paket `src/pta_documents/drawing/` (öffentlich, weil Renderer es benutzen):
   - `model.py`: `Drawing(width, height, items)`, `DrawingShape(path, fill, stroke, stroke_width,
     dash=None, kind=ShapeKind.PATH, corner_radius=0, round_joins=False, even_odd=False,
     hover=None)`, `DrawingPath(segments)` mit `bounds` und `rectangle(...)`, `MoveTo`, `LineTo`,
     `CubicTo`, `ClosePath`, `DrawingText(x, baseline, spans, size, color, anchor, max_width,
     mono, hover)` mit `text`, `DrawingSpan(text, bold=False, color=None)`, `DrawingHotspot(x, y,
     radius, dot=None, dot_radius=4, hover=None)`, `DrawingHover(text, x, y)`, `ShapeKind`,
     `TextAnchor`.
   - Alle als `@dataclass(frozen=True, slots=True)` mit Tupeln statt Listen — Gleichheit nach
     Inhalt ergibt sich daraus (DocLibs brauchte dafür eigene `Equals`).
   - **PTA-Ergänzung `even_odd`:** Füllregel `evenodd` statt `nonzero`; nötig für die EMF-Logos
     (E01-S04) und Mermaid-SVGs (E06-S03). DocLibs kannte keine Füllregel.
2. `svg_output.py` (der Name `svg.py` gehört dem SVG-Leser aus E06-S03): `to_svg(drawing,
   options: SvgOptions | None = None) -> str`, im Paket re-exportiert — Port von
   `DrawingSvg.Write` mit denselben Klassennamen (`chart-hoverable`, `chart-tooltip`,
   `chart-tooltip-bg`, `chart-tooltip-text`, `chart-hover-dot`), demselben Inline-`<style>` und
   derselben Platzierung (zentriert über dem Punkt, auf der Fläche gehalten), `estimate_width()`.
   `SvgOptions(font_family=fonts.CSS_FAMILY, mono_family=fonts.CSS_MONO_FAMILY, background=None,
   tooltip_fill=colors.TEXT_SLIDES, tooltip_text=colors.WHITE)` — statt DocLibs' `111827`.
3. Zahlenformat wie DocLibs (`0.##`, keine `-0`), Escape von `& < > "` und Entfernen von
   Steuerzeichen außer Tab/LF/CR.
4. Tests: die neun DocLibs-Fälle sinngemäß (Formen → `rect`/`rect rx`/`ellipse`/`path` mit Farbe,
   Strich, Strichelung, runden Ecken; Text mit Anker, Fett, Spanfarben, Escape; zu breite Zeile
   bis 70 %; Tooltip vorplatziert, an der Fläche geklemmt, ohne `<script>`; Spanfarbe zählt für
   Gleichheit; `bounds` mit Kontrollpunkten), dazu `even_odd` → `fill-rule="evenodd"` und ein
   Test, dass das Modul nur Farben aus `design.colors` verwendet.

## Akzeptanzkriterien

- [ ] Alle DocLibs-Testfälle für `Drawing` und `DrawingSvg` laufen sinngemäß grün.
- [ ] Ein SVG mit Tooltips zeigt sie im Browser beim Überfahren, ohne Skript.
- [ ] Das Modul hängt von keinem Extra ab (reines Python, Kern).

## Offene Fragen

1. Sollen SVGs die Schrift **einbetten** (`@font-face` mit Selawik als Base64, ca. 200 KB je
   Schnitt), damit sie auf Rechnern ohne Segoe UI gleich aussehen, oder nur Familiennamen nennen
   wie in DocLibs (Vorschlag; kleiner, Browser ersetzen die Schrift)?

> (2026-11-07) Nur Familiennamen nennen.

## Notizen

- Die Ausgabe als PowerPoint-Formen (DocLibs `DrawingWriter.cs`) gehört zu E06-S02, als PDF-Vektor
  zu E05-S04, als PNG zu E06-S04, in Word zu E03-S04; SVG → `Drawing` (Mermaid) zu E06-S03.
