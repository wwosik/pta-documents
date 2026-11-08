# E06-S04 SVG → PNG und SVG-Bilder in Folien und Dokumenten

> Status: in Prüfung
> Epic: [E06 Diagramme und Charts](../50-entwurf/E06-diagramme-und-charts.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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
- (2026-11-07, E02-S04) Standard eintragen in `generation/common/images.default_converters()`
  (Import von resvg-py dort abfangen). Die Generatoren konvertieren heute schon: DOCX in
  `BodyWriter.place_picture` (natürliche Größe aus `ConvertedImage`), PPTX im Parser
  (`DeckParser._placeable`, das Original-SVG geht dabei verloren — für `asvg:svgBlip` muss das
  `Image`-Modell es mitführen).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Paket `src/pta_documents/svg/` (`sanitizer.py`,
`converter.py`, `image_converter.py`, Re-Exporte in `__init__.py`), `svg_blip.py` in
`generation/common/`, Anbindung in `generation/common/images.py` (`default_converters`,
`svg_available`, `refusal_hint`, Feld `svg` in `ConvertedImage`/`Conversion`), DOCX
(`BodyWriter.place_picture`) und PPTX (`model.Image.natural`/`svg`, `DeckParser._placeable`,
`visuals.picture_size`/`attach_svg`/`draw_pictures`, `DeckWriter.fill_picture`/`note_enlarged`).
Tests in `tests/svg/` (`test_sanitizer.py`, `test_converter.py`, `test_image_converter.py`,
44 Fälle); `tests/generation/docx/test_content.py` prüft die Ablehnung jetzt an einem WebP.
Doku: `docs/verwendung.md` (neuer Abschnitt „SVG-Bilder (E06-S04)", Konverter-Abschnitt,
Zeichenmodell), `docs/anleitung.md`, `docs/ki-anleitung.md`; Beispiele `samples/funktionen/`
(Abschnitt „SVG-Grafik" in Bericht und Präsentation, `images/plan.svg`, `images/plan-folie.svg`,
README) samt erneuerten Rundreisen; Eintrag in `ai/Gedächtnis.md`. Keine neue Abhängigkeit —
resvg-py und fontTools stehen schon im Extra `svg`.

### Entscheidungen

- **Quelle des Ports:** `SvgSanitizer.cs`, `SvgConverter.cs`, `SvgImageConverter.cs` und
  `SvgConverterTests.cs` aus `~/mvv/vt-tools-libs` (wie DocLibs). Die Testfälle für PDF und
  HTML-Deck entfallen (es gibt beide Generatoren noch nicht).
- **Bereinigen:** lxml mit `resolve_entities=False`, `no_network=True`, `load_dtd=False`; die
  DTD fällt beim Serialisieren der Wurzel weg. Zusätzlich zu DocLibs werden Entitäts-Referenzen,
  Processing Instructions und Kommentare entfernt (ein nicht aufgelöstes `&x;` ergäbe sonst
  ungültiges XML). Text nach einem entfernten Element bleibt erhalten.
- **Größe** selbst aus `width`/`height` (px/ohne Einheit, pt, pc, mm, cm, in), sonst
  `viewBox`; fehlt eines von beiden, folgt es aus den Proportionen der `viewBox`. Relative
  Angaben (`%`, `em`, `ex`) zählen als fehlend.
- **Eingebettet wird das bereinigte SVG**, nicht das Original — Office soll keinem Verweis folgen
  können. Dasselbe SVG steht nur einmal im Paket (`svg_blip._existing` vergleicht Typ und Bytes
  der Teile; kein Zustand im Writer). Teilname `/<ppt|word>/media/imageN.svg`, Beziehung vom
  Teil, der das Bild hält (Folie bzw. `document.xml`), Typ `…/relationships/image`; der
  Content-Type kommt als `Override`.
- **PowerPoint:** das `Image`-Modell trägt `natural` und `svg` (keyword-only). `picture_size`
  liefert für umgewandelte Bilder die natürliche Größe, sonst die Pixel wie bisher — Fit und
  Seitenverhältnis bleiben gleich, weil das PNG genau doppelt so groß ist.
- `SvgImageConverter` ist eine eingefrorene Dataclass; `default_converters()` liefert
  `(SvgImageConverter(),)`, wenn `importlib.util.find_spec("resvg_py")` etwas findet — ohne
  resvg zu importieren. Der Fehler für ein SVG ohne Extra endet auf
  `; SVG images need the extra 'svg' (pip install 'pta-documents[svg]')`.
- Fehlermeldung des Konverters: `The image '<pfad>' cannot be converted: <grund>` (Format `svg`),
  ohne das doppelte „The SVG cannot be converted" aus `to_png`.

### Abweichungen

- **Warnung (Schriften):** Der Plan nennt „Segoe UI aus dem System, wenn vorhanden", das
  Akzeptanzkriterium „dasselbe PNG auf jedem Rechner". Beides zugleich geht nicht (unter Windows
  hätte das PNG Segoe UI, sonst Selawik). Gewählt ist die vorsichtigere, reproduzierbare
  Variante: **standardmäßig nur die mitgelieferten Schriften** (`skip_system_fonts=True`);
  `PngOptions(system_fonts=True)` bzw. `SvgImageConverter(system_fonts=True)` lädt zusätzlich
  die Systemschriften. Folge: Text in SVG-Bildern erscheint im PNG immer in Selawik — das
  eingebettete SVG zeichnet Office aber mit den installierten Schriften (Segoe UI).
- **Warnung (fehlende Familien):** resvg setzt Text, dessen Familie fehlt, in der generischen
  Familie `serif`. Damit fehlende Schriften (Arial, Segoe UI …) nicht in Gelasio Italic
  erscheinen, zeigen `serif`, `sans-serif`, `cursive`, `fantasy` und die Standardfamilie auf
  Selawik, nur `monospace` auf Inconsolata. Gelasio greift nur, wenn es beim Namen genannt wird.
- **Warnung (Hinweise):** PowerPoint meldet für SVG-Bilder kein `image-enlarged` — das SVG ist
  in jeder Größe scharf; nur Office vor 2016 zeigt das PNG (doppelte Auflösung) und könnte bei
  starker Vergrößerung unscharf wirken. `image-cropped` gilt unverändert.
- Statt `ChartPngTests` (Finanzdiagramme kommen mit E06-S02) prüft ein Test eine einfache
  Zeichnung als PNG in doppelter Größe; der Pflicht-Test „Tooltips nicht im PNG" nutzt
  `to_svg` mit `DrawingHover` und `DrawingHotspot` (Ergebnis byte-gleich mit derselben
  Zeichnung ohne Tooltips).

### Warnungen

- **Warnung:** Entitäten in einem SVG werden nie aufgelöst, sondern entfernt — ein SVG, das
  eigene Entitäten für Text nutzt (selten, z. B. aus alten Illustrator-Exporten), verliert diesen
  Text. Sicherer als Auflösen (Billion Laughs, XXE).
- **Warnung:** Die `asvg:svgBlip`-Erweiterung ist ohne Office nicht geprüft (kein Word,
  PowerPoint oder OOXML-Validator auf der Entwicklungsmaschine). Aufbau wie DocLibs
  (`a:blip/a:extLst/a:ext uri="{96DAC541-…}"/asvg:svgBlip r:embed`), Namensraum lokal am
  `asvg:svgBlip` deklariert, wie Office es selbst schreibt.
- Ohne Extra `svg` bleibt ein SVG-Bild ein Fehler (mit Hinweis auf das Extra); `./run.sh setup`
  installiert es.

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-bericht.docx` (Abschnitt „SVG-Grafik") und
  `funktionen-praesentation.pptx` (Folie „SVG-Grafik") in Word bzw. PowerPoint öffnen: das Bild
  muss beim Vergrößern scharf bleiben (Akzeptanzkriterium 5), „Grafik als SVG" bzw. „In Form
  konvertieren" muss angeboten werden; Word zeigt „Abbildung 6".
- In einer älteren Office-Version oder LibreOffice erscheint stattdessen das PNG.
- `./run.sh test tests/svg` — Sicherheit (keine Datei-, Web- oder CSS-Verweise; der Test zeigt,
  dass resvg ohne Bereinigung die Datei geladen hätte), Größen, Schriften, Tooltips.

### Offene Punkte

- **PDF** (Plan Punkt 8, Akzeptanzkriterium „im PDF in natürlicher Größe"): den PDF-Generator
  gibt es noch nicht (E05). Er nutzt denselben Konverterweg; nach der Antwort auf die offene
  Frage soll er mit **dreifacher** Größe (`scale = 3`, ≈ 288 dpi) statt `GENERATOR_SCALE`
  umwandeln — in E05-S04 umzusetzen. *(2026-11-08) Erledigt in E05-S04 (`story.IMAGE_SCALE`).*
- Zeichnungen in Word (Plan Punkt 9) über `to_svg` → `SvgImageConverter`-Weg folgen mit E03-S04;
  `DrawingGraphic` wirft bis dahin weiter.
- Die Konverter DOCX/PPTX → Markdown lesen nur das PNG (`images/imageN.png`); das SVG neben dem
  PNG zurückzugewinnen wäre eine Ergänzung für E07.
