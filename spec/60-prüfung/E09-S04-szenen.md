# E09-S04 Szenen: benannte Formen, die Morph bewegt

> Status: in Prüfung
> Epic: [E09 Präsentieren](../50-entwurf/E09-praesentieren.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

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

> (2026-11-07) Quadratisch, 160 × 67.
3. Soll `image` in Szenen die PTA-Bildplatzhalter-Regel (Beschnitt) ignorieren und das Bild
   einpassen? Vorschlag: einpassen, wie vt-tools-libs.

> (2026-11-07) Einpassen.

## Notizen

- Größte Story des Epics; hängt von E02-S02 (Container), E02-S03 (`Drawing`), E04-S03 (freie
  Formen auf `Nur Titel`, Signalfarben), E09-S02 (Schritte) und E09-S03 (Morph) ab.
- Die skriptgesteuerten Szenen der HTML-Decks (`{#id data-steps=n}`, Rohes HTML) werden nicht
  übernommen — sie wären nur in E10 darstellbar und widersprechen „kein Rohes HTML".

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `generation/common/scene.py` (`Scene`, `SceneShape`,
`ShapeKind`, `read_scene`, `check_place`, `is_dark`, Raster `COLUMNS`/`ROWS`/`UNIT_EMU`),
`generation/common/scene_colors.py` (Rollen → `design.colors`, weiche Füllung),
`drawing/scene.py` (Szene → `Drawing` + Bilder), `generation/pptx/scene_writer.py`. Angepasst:
`markdown/parser.py` (Kernregel `container_sources`: jeder Container trägt seine Rohzeilen in
`meta[SOURCE_LINES]`), `layout_syntax.py` (`SCENE` in `CONTAINER_NAMES`, Prüfung in `check`),
`design/colors.py` (`mix`), `result.py` (`NoteCodes.SCENE_DROPPED`), PPTX `model.py`
(`SceneSlide`), `parser.py` (`_scene_at`, `_scene_slide`), `writer.py`, `flow.py`
(`headed_slide` öffentlich, auch für Szenen), `animations.py` (`p:sp` ohne Textkörper ist
`Target.OTHER`), DOCX `writer.py` (Szene weg mit Hinweis), PDF `layout/drawings.py`
(`SceneFlowable`, `SceneImage`), `layout/story.py` (`scene`, `readable` aus `place` gelöst).
Tests: `tests/generation/common/test_scene.py` (66, Grammatik, Farben, Platzfehler in allen drei
Formaten), `tests/drawing/test_scene.py` (5), `tests/generation/pptx/test_scene_writer.py` (10:
Morph-Namen, Inhaltsfläche, Farben, Builds, Bild, `.dark`, Konverter, Word, PDF);
`test_layout_syntax.py` (Containerliste), `test_funktionen.py` (`scene` nur im Deck verlangt).
Beispiel: zwei Szenenfolien „Drei Ablageorte" → „Ein Ablageort" im Kapitel „Präsentieren" von
`samples/funktionen/funktionen-praesentation.md` (alle Arten, `step`, `opacity=0`, Bild,
`solid`), README und Rundreise erneuert. Doku: `docs/verwendung.md` (Abschnitt „Szenen
(E09-S04)", Syntax- und Hinweistabelle), `docs/anleitung.md` („Szenen: Formen, die Morph
bewegt"), `docs/ki-anleitung.md`; `ai/Gedächtnis.md`.

### Entscheidungen

- **Raster** (Frage 2): 160 × 67 quadratische Einheiten zu 0,195 cm (70 200 EMU) ab der oberen
  linken Ecke von `CONTENT_AREA`; 67 × 0,195 = 13,065 cm, die Fläche ist 13,10 cm hoch (0,035 cm
  bleiben unten frei). Eine Form, deren Kasten (bei Linien die Spanne der Enden) über das Raster
  hinausreicht, ist ein Fehler mit Zeile.
- **Bilder** (Frage 3): eingepasst und mittig im Kasten, nie beschnitten; andere Formate (SVG)
  über die Bildkonverter wie sonst (`DeckParser._placeable`, PDF `readable`).
- **Rohzeilen statt Token:** Die Szene wird aus den Quellzeilen gelesen wie in vt-tools-libs. Da
  `layout_syntax.check` nur Token sieht, hängt eine Kernregel des gemeinsamen Parsers die Zeilen
  jedes Containers an sein Token (`SOURCE_LINES`); so prüfen alle Formate dieselbe Szene ohne
  neue Parameter.
- **Prüfung in allen Formaten:** Grammatik, Raster und Platz (nur unter `##`, allein mit
  `::: notes` und HTML-Kommentaren, keine PTA-Folienart, `layout` höchstens „Nur Titel", kein
  Blockmarker) prüft `layout_syntax.check` — auch Word und PDF werfen. Ob ein Bild unter den
  Ressourcen ist, prüfen die Generatoren beim zweiten Lesen.
- **Farbrollen** wie im Plan, aber nur aus `design.colors`: `surface` ist das PTA-Flächengrau
  `GREY_LIGHT` (der Plan nannte F2F2F2, das in der Palette nicht vorkommt), `accent1`–`6` die
  Theme-Akzente, die Signalrollen `STATUS_COLORS` (also `info` = PTA-Blau, darum nie weich,
  `neutral` = mittleres Grau). Weiche Füllung = `colors.tint(farbe, 0,12)`.
- **`.dark`:** Hintergrund wie Flow-Folien (`flow.headed_slide`); freie Texte (`text`) ohne
  `text=` werden weiß, Kästen behalten ihre Farben.
- **Schritte:** `step=n` ist ein Fade-Build auf Klick n der Folie (`Click(n)`, E09-S02).
- **XML** wie vt-tools-libs: `p:sp` mit `rect`/`roundRect` (`adj` = Ecke 12 px bzw. 50 000 für
  `pill`)/`ellipse`/`line` (`tailEnd triangle`, `flipH`/`flipV` bei negativer Breite/Höhe),
  Name `!!name`, `a:alpha` auf Füllung, Linie und Text, `rot` in 60 000stel Grad; jede Form außer
  Linien hat einen Textkörper. Linienbreiten 2 bzw. 3 px der Zeichnung (1,1 bzw. 1,66 pt).

### Abweichungen

- **Meldungen** im Format des Repos (`Line 14: Scene shape '…': unknown kind 'blob'. Valid
  kinds: …`) statt „Scene line 14 '…': …", damit sie wie alle Fehler von `layout_syntax.check`
  mit `Line N:` beginnen.
- **Rollen `link` und `alt`** aus vt-tools-libs fehlen, weil der Plan sie nicht nennt und die PTA
  keinen Alternativ-Hintergrund hat; `#RRGGBB` aus dem Markdown bleibt möglich.
- Der Guide E04-S06 existiert noch nicht; die Syntax steht in `docs/anleitung.md` und
  `docs/ki-anleitung.md`.
- Die Morph-Paarung über `!!name` braucht keinen Code in E09-S03; `animations.target_of` wurde nur
  so geändert, dass eine Linie (Form ohne Textkörper) nicht als Text in `p:bldLst` steht.

### Warnungen

- **Warnung:** Word lässt die Szene weg **mit** Hinweis `scene-dropped` (der Plan: „Hinweis über
  E08, falls vorhanden"). Ein Bericht mit Szene erzeugt also nicht hinweisfrei; das Word-Beispiel
  enthält darum keine Szene (`test_funktionen.py` verlangt `scene` nur im Deck).
- **Warnung:** Drehung wird bei der Rasterprüfung nicht berücksichtigt; eine gedrehte Form nahe
  am Rand kann mit ihren Ecken über die Inhaltsfläche ragen.
- **Warnung:** Im PDF wird Deckkraft auf den Grund gemischt (PDF/A ohne Transparenz): eine
  halbtransparente Form verdeckt, was unter ihr liegt; `opacity=0` lässt sie ganz weg. Bilder
  stehen im PDF immer deckend; Text steht dort ungedreht in **einer** Zeile (auf 70 %
  geschrumpft, dann überlaufend), während PowerPoint im Kasten umbricht.
- **Warnung:** Die Texte der Formen setzt die Typografie (`typografie: ja`) nur in PowerPoint;
  das PDF zeigt sie wie geschrieben.
- **Warnung:** Text erbt keine Absatzebenen des Masters; Schrift ist fest Segoe UI Light bzw.
  `+mj-lt` (Segoe UI) für `bold`, Größe Standard 16 pt.
- **Warnung:** `MAX_TEXT_PT` = 400 pt und die Grenzen der Zahlen sind aus vt-tools-libs
  übernommen; Formen werden nicht auf die Textlänge geprüft (kein `slide-overfull`).

### Prüfpunkte

- In PowerPoint 365 öffnen (keine Reparaturmeldung) und als Bildschirmpräsentation zeigen:
  `.tmp/review/deck-scene.pptx` (Folie 2 → 3: SharePoint wächst und wird PTA-blau, OneDrive
  verschwindet in ihm, die Pille kommt per Klick, der Pfeil per Klick) und
  `.tmp/review/funktionen/funktionen-praesentation.pptx`, Folien „Drei Ablageorte" → „Ein
  Ablageort" (Kreis „E-Mail" geht unsichtbar in den Kasten, Bild und grüne Pille erscheinen).
- Im Auswahlbereich prüfen, dass die Formen `!!sp`, `!!od` … heißen und sich bearbeiten lassen;
  im Animationsbereich die Fades der Schritte.
- PDF-Standbild: `.tmp/review/scene.pdf`, Zeichnung `.tmp/review/scene.svg`.
- PowerPoint-Prüfung steht aus (kein Office auf der Entwicklungsmaschine).

### Offene Punkte

- E10-S01 (HTML-Deck) kann `drawing.scene` bzw. `Scene` für die Bühne nutzen (vt-tools-libs:
  10 px je Einheit, wie hier).
- E04-S06 (Guide PowerPoint) nennt Szenen, Arten, Attribute und Farbrollen.
