# E02-S03 Zeichenmodell `Drawing` und SVG-Ausgabe mit Tooltips

> Status: in Prüfung
> Epic: [E02 Markdown-Grundlagen der Generatoren](../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Paket `src/pta_documents/drawing/` (`model.py`,
`svg_output.py`, Re-Exporte in `__init__.py`), `design.logos.drawing()` (schließt das dritte
Akzeptanzkriterium von E01-S04), `DrawingGraphic.drawing` und `ChartGraphic.drawing` auf `Drawing`
festgezogen (Warnung aus E02-S04). Tests in `tests/drawing/test_model.py`,
`tests/drawing/test_svg_output.py` und `tests/design/test_logos.py`; der Kern-Import-Test in
`tests/design/test_fonts.py` importiert jetzt auch `drawing` und `design.logos`. Doku in
`docs/verwendung.md` (Abschnitt „Zeichenmodell und SVG", Verweise bei Renderern und Logos),
Eintrag in `ai/Gedächtnis.md`. `samples/` und die Anleitungen für Schreiber bleiben unverändert —
keine neue Syntax, kein neuer Front-Matter-Schlüssel.

### Entscheidungen

- **Quelle des Ports:** `Drawing.cs`, `DrawingSvg.cs` und die Tests aus
  `~/mvv/vt-tools-libs` (Schwesterbibliothek, Stand wie DocLibs plus Ergänzungen). Deren
  `DrawingText.LetterSpacing` ist **nicht** übernommen — der Plan nennt es nicht und kein
  geplanter Renderer braucht es bisher; nachrüsten ist ein Feld mit Standardwert.
- Typen wie geplant als `@dataclass(frozen=True, slots=True)`; `__post_init__` wandelt
  übergebene Listen in Tupel (`segments`, `items`, `spans`, `dash`), damit Gleichheit und
  `hash` auch dann stimmen. Optionale Felder (`dash`, `kind`, …, `hover`) sind keyword-only
  (`KW_ONLY`), wie die `init`-Eigenschaften in C#.
- `PathSegment` und `DrawingItem` sind Typ-Unions statt Basisklassen; jedes Segment hat
  `points`. Ausgaben verzweigen mit `match` (pyright prüft Vollständigkeit).
- `DrawingPath.bounds` liefert ein `NamedTuple` `Bounds(x, y, width, height)` — vergleicht
  gleich mit einem einfachen Tupel wie in DocLibs.
- Statt des zweiten C#-Konstruktors gibt es `DrawingText.line(x, baseline, text, size, color,
  *, bold, …)` für eine Zeile in einem Schnitt.
- `ShapeKind`/`TextAnchor` sind `StrEnum` (`"rounded-rectangle"`, `"middle"` …).
- SVG wie DocLibs, Zeichen für Zeichen geprüft gegen die portierten Erwartungen; Zahlen mit
  `round(v, 2)` und `0.##`, `-0` → `0`. Der weiße Rand des Hover-Punkts ist `colors.WHITE`.
- `SvgOptions` holt `fonts.CSS_FAMILY`/`CSS_MONO_FAMILY` über `default_factory` **lazy**: so
  lädt ein Import von `pta_documents.drawing` (auch aus `renderers.py` im Kern) `design.fonts`
  nicht — der bestehende Test „Kern importiert dieses Modul nicht" bleibt gültig und prüft jetzt
  auch `drawing` und `design.logos`.
- `logos.drawing(logo, width=None)`: je SVG-Pfad eine gefüllte `DrawingShape` ohne Linie,
  `even_odd` aus `fill-rule`; ohne `width` in viewBox-Einheiten, sonst proportional auf `width`
  CSS-Pixel skaliert (die Offenen Punkte von E01-S04 nennen „Maßstab nach Bedarf").
- Test „nur Farben aus `design.colors`": die Standard-Ausgabe (Tooltip, Hover-Punkt) enthält nur
  `TEXT_SLIDES`, `WHITE` und die übergebene Farbe; zusätzlich verbietet ein eigener Test jede
  Hex-Farbe (auch ungequotet) in den Quellen von `drawing/`.
- Zum Ansehen schreibt `test_review_page` `.tmp/review/drawing.svg` und `drawing.html`
  (SVG inline, damit `:hover` wirkt): vier Balken und eine Linie mit Punkten, alle mit Tooltip.

### Abweichungen

- Zusätzlich zum Plan: `Bounds`, `Point`, öffentliche Hilfsfunktionen `path_data`, `number`,
  `paint`, `escape` in `svg_output.py` (für Tests und spätere Ausgaben, z. B. PDF-Pfade).
- **Warnung:** `to_svg` wirft `ValueError` für eine Farbe, die nicht `RRGGBB` ist, und für eine
  nicht endliche Zahl (NaN, ∞). DocLibs schrieb beides ungeprüft ins SVG (kaputtes XML bei
  `"` in einer Farbe, `NaN` als Koordinate). Ein Renderer mit solchen Werten hat einen
  Programmierfehler; die Generatoren machen daraus wie bei jedem Renderer-Fehler eine
  `DocumentConversionError`.

### Warnungen

- **Warnung:** Der Tooltip wird wie in DocLibs nur **waagrecht** auf der Fläche gehalten. Liegt
  der Hover-Punkt weniger als 23 px unter dem oberen Rand, ragt der Tooltip oben hinaus und
  wird vom SVG abgeschnitten. Renderer (E06) sollten Hover-Punkte entsprechend setzen oder oben
  Rand lassen; geändert wurde das Verhalten bewusst nicht.
- **Warnung:** Die Textbreite ist geschätzt (0,58 × Größe je Zeichen), nicht gemessen; Tooltip-
  breite und das Verkleinern auf `max_width` sind daher ungefähr. Echte Breiten gäbe es mit
  `design.fonts` (Extra), das der Kern nicht laden soll.

### Prüfpunkte

- `.tmp/review/drawing.html` im Browser öffnen (entsteht mit
  `./run.sh test tests/drawing/test_svg_output.py`): Balken und Punkte überfahren — die Tooltips
  erscheinen ohne Skript (Akzeptanzkriterium 2), der Punkt wird dabei sichtbar.
- `logos.drawing(Logo.WORD)` ergibt sechs Pfade in 496 × 284; `to_svg` davon entspricht in den
  `d`-Attributen dem gespeicherten SVG (Test).

### Offene Punkte

- Ausgabe als PowerPoint-Formen (E06-S02), PDF-Vektor (E05-S04), PNG (E06-S04), in Word
  (E03-S04) und SVG → `Drawing` (E06-S03) folgen in ihren Stories; bis dahin werfen
  `DrawingGraphic` in beiden Generatoren und `ChartGraphic` in Word weiter „does not support yet".
- E15-S02 erweitert `ShapeKind` um `CHEVRON` und `PIE`; dabei jedes `match` über `kind`
  (heute `svg_output._shape`) ergänzen.
