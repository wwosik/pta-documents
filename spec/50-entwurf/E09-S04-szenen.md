# E09-S04 Szenen: benannte Formen, die Morph bewegt

> Status: Entwurf
> Epic: [E09 Präsentieren](E09-praesentieren.md)

## Zusammenfassung

Ein `::: scene` unter einem `##` legt benannte Formen — Kästen, Pillen, Kreise, Texte, Linien,
Pfeile, Bilder — an feste Stellen eines Rasters, in PTA-Farben. Folgt eine zweite Szenenfolie mit
`morph`, bewegt PowerPoint die gleichnamigen Formen von der einen Lage in die andere. Das PDF
zeichnet die Szene als Standbild, Word lässt sie weg.

## Kontext

- vt-tools-libs: `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration/Scene.cs` (337 Zeilen:
  `SceneShape`, `Scene.Parse` liest die Quellzeilen des Containers selbst, Regexe für
  `name: kind x,y wxh "text" key=value …`, Fehler mit Zeile), `SceneDrawing.cs` (169 Zeilen:
  Szene → `Drawing` für PDF/SVG), `…Pptx/DeckWriter.cs` (Szenenfolie auf `titleOnly`, Formen
  `rect`/`roundRect`/`ellipse`/`line`, benannt `!!name`, Rotation, `a:alpha`, Schritt als Build).
  Regeln laut `docs/VtToolsLibs.DocumentGeneration.md` (*Scenes*): Raster 160 × 90 über die
  **ganze Folie** (76 200 EMU je Einheit), Arten `box, round, pill, circle, text, line, arrow,
  image`, Attribute `fill, line, text, rotate, opacity, size, bold, solid, step, image`, Farben
  als Rollen (`primary`, `text`, `muted`, `background`, `accent1`–`6`, `surface`, `border`,
  `line`, `success`, `info`, `warning`, `danger`, `neutral`), `#RRGGBB` oder `none`; farbige
  Füllungen sind „weich" (Tönung 12 % mit farbiger Linie) außer `primary` und `solid`; eine
  Szenenfolie enthält nur Titel, Szene und `::: notes`; alles andere wirft mit Zeile.
- Hier: `generation/pptx/parser.py` kennt keine Container (E02-S02); `writer.py` hat
  `layout_slide` auf benannten Layouts, aber kein Zeichnen freier Formen (E04-S03 bringt
  `visuals.py`-Erweiterungen für Flow-Layouts auf `Nur Titel`); das Zeichenmodell `Drawing`
  kommt mit E02-S03, die Farbrollen mit `design/colors.py` (60 Zeilen: PTA-Palette,
  `StatusCategory`). `CONTENT_AREA` in `design/slides.py`: 1,33/4,62 cm, 31,20 × 13,10 cm.
- PTA-Regel: freie Formen nur auf `Nur Titel` und innerhalb der Inhaltsfläche, am Raster
  ausgerichtet (E04, *Bereichsweite Entscheidungen*).

## Vorgeschlagener Ansatz

1. **Parser** `generation/common/scene.py`: Port von `Scene.Parse` und `ShapeReader` — liest die
   Quellzeilen des Containers aus `token.map`, gleiche Grammatik, gleiche Meldungen
   („Scene line 14 '…': unknown kind 'blob'. Valid kinds: …"); `image=` löst über
   `MarkdownDocument.find_resource`. `scene` in `layout_syntax.CONTAINERS`.
2. **Raster:** 160 × 90 Einheiten über die **Inhaltsfläche** statt die ganze Folie (Frage 2):
   eine Einheit ist 31,20 cm / 160 = 0,195 cm waagerecht und 13,10 cm / 90 ≈ 0,1456 cm senkrecht —
   also kein quadratisches Raster. Alternative: quadratische Einheit 0,195 cm, 160 × 67 Einheiten;
   Entscheidung in Frage 2. Formen außerhalb der Inhaltsfläche sind ein Fehler mit Zeile.
3. **Farben** (`generation/common/scene_colors.py`): Rollen auf die PTA-Palette abbilden —
   `primary` 006FB9, `text` 404040 (PowerPoint), `muted` 787878, `background` FFFFFF, `surface`
   F2F2F2, `border` AFAFAF, `line` 787878, `accent1`–`accent6` die Theme-Akzente der Vorlage,
   `success`/`info`/`warning`/`danger`/`neutral` die Signalfarben aus E04-S03; „weiche" Füllung
   wie in vt-tools-libs (Tönung 12 % auf Weiß).
4. **Modell und Folie:** `SceneSlide(Slide)` in `model.py` mit `Scene`; der `DeckParser` erkennt
   ein `##` mit genau einem `::: scene` und sonst nur `::: notes`; `.dark`, `kicker`, `layout`
   und `uebergang` auf dem Heading bleiben erlaubt (`.dark` nach Antwort in E04-S03).
5. **PPTX** (`generation/pptx/scene_writer.py`): Folie auf `Nur Titel`, je Form ein `p:sp`
   (`rect`, `roundRect` mit `adj` für Ecke/Pille, `ellipse`, `line` mit `tailEnd="triangle"`)
   bzw. `p:pic`, benannt `!!name`, Text zentriert in Segoe UI Light, `a:alpha` für Deckkraft,
   `rot` für Drehung; `step` als Build über E09-S02 (`BuildTarget.Other`). Morph über E09-S03.
6. **PDF:** `SceneDrawing` nach `drawing/scene.py` portieren (Szene → `Drawing`), E05-S04 zeichnet
   das Standbild in Seitenbreite. **Word:** Container wird weggelassen, Hinweis über E08
   (Rückmeldung) falls vorhanden.
7. **Tests** (Port von `SceneTests.cs` aus vt-tools-libs, 2 Projekte): Grammatikfehler mit
   Zeile, Formen pro Art, Morph-Namen `!!name` auf zwei Folien, Form außerhalb der
   Inhaltsfläche, Szene unter `#` oder mit weiterem Inhalt; Rundreise: der Konverter gibt den
   Text der Formen als Absätze zurück (wie heute Freitext-Formen).
8. **Doku:** eigener Abschnitt in `docs/anleitung.md` und Guide E04-S06 mit dem Zwei-Folien-
   Beispiel aus vt-tools-libs in PTA-Farben; `samples/funktionen/` zeigt es.

## Akzeptanzkriterien

- [ ] Das Beispiel „Drei Orte → Ein Ort" ergibt zwei Folien auf `Nur Titel`, deren Formen
      innerhalb der Inhaltsfläche liegen und die PowerPoint 365 per Morph ineinander bewegt.
- [ ] Jede Grammatik- und Lagefehler wirft `DocumentConversionError` mit Zeile und gültigen
      Werten; eine Szene unter `#` oder neben anderem Inhalt wirft.
- [ ] Farben kommen ausschließlich aus der PTA-Palette bzw. den Theme-Akzenten; kein Hex-Wert
      im Writer außer aus dem Markdown.
- [ ] PDF zeigt die Szene als Standbild; Word lässt sie ohne Fehler weg.

## Offene Fragen

1. **Bedarf:** Wird das bei der PTA gebraucht — etwa für Architekturbilder, die sich von Folie zu
   Folie verändern —, oder reichen Flow-Layouts (E04-S03) und Mermaid (E06-S03)? Ohne Ja bleibt
   die Story liegen.

> (2026-11-07) Ja.

2. Raster über die Inhaltsfläche (PTA-konform, aber nicht quadratisch: 160 × 90 auf
   31,20 × 13,10 cm) oder quadratische Einheit 0,195 cm mit 160 × 67 Einheiten? Vorschlag:
   quadratisch 160 × 67, damit `20x20` ein Quadrat ist.

>

3. Soll `image` in Szenen die PTA-Bildplatzhalter-Regel (Beschnitt) ignorieren und das Bild
   einpassen? Vorschlag: einpassen, wie vt-tools-libs.

>

## Notizen

- Größte Story des Epics; hängt von E02-S02 (Container), E02-S03 (`Drawing`), E04-S03 (freie
  Formen auf `Nur Titel`, Signalfarben), E09-S02 (Schritte) und E09-S03 (Morph) ab.
- Die skriptgesteuerten Szenen der HTML-Decks (`{#id data-steps=n}`, Rohes HTML) werden nicht
  übernommen — sie wären nur in E10 darstellbar und widersprechen „kein Rohes HTML".
