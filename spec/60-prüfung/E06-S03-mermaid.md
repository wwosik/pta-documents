# E06-S03 Mermaid über mermaid-cli

> Status: in Prüfung
> Epic: [E06 Diagramme und Charts](../50-entwurf/E06-diagramme-und-charts.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

` ```mermaid `-Blöcke werden lokal mit mermaid-cli (Node.js + Chromium) zu SVG gezeichnet, das SVG
wird in ein `Drawing` übersetzt und erscheint als Vektorgrafik im PDF und als bearbeitbare Formen
in Folien — in den PTA-Farben und ohne Online-Dienst.

## Kontext

- DocLibs `DocumentGeneration.Diagrams` (1 250 Zeilen): `MermaidRenderer.cs` (103, auf
  Mermaider, Typen flowchart, sequence, class, state, ER, pie, gantt, mindmap; `MermaidErrorMode`
  `Throw`/`KeepCode`), `SvgDrawing.cs` (568, SVG → `Drawing`: Grundformen, Pfade, Marker, Text mit
  `tspan`, Gruppen mit Transformationen; Unbekanntes wirft), `SvgGeometry.cs` (355: Pfade, Bögen,
  Transformationen), `SvgStyle.cs` (218: nur Mermaiders CSS-Variablen). Tests: `SvgDrawingTests`,
  `SvgGeometryTests`, `SvgStyleTests`, `MermaidRendererTests`, `GenerationTests` (zusammen ~25
  Fälle), Beispiel `diagrams.md` (127 Zeilen), Anleitung `AuthoringGuide/Diagrams.md`.
- Entscheidung 2026-11-06: mermaid-cli als optionale Abhängigkeit, `htmlLabels: false`, nur
  lokal. Node.js liegt auf diesem Rechner, mermaid-cli und ein Chromium nicht sicher.
- mermaid-cli schreibt anderes SVG als Mermaider: Farben stehen in einem `<style>` mit
  Selektoren (`#id .node rect { … }`), teils als `hsl()`/`rgb()`; Beschriftungen sind mit
  `htmlLabels: false` echtes `<text>`, einzelne Typen nutzen trotzdem `foreignObject`.

## Vorgeschlagener Ansatz

1. **SVG → Drawing im Kern** (`src/pta_documents/drawing/svg.py`, `svg_geometry.py`,
   `svg_style.py`, nur lxml): Port von `SvgDrawing.cs` und `SvgGeometry.cs` 1:1; `SvgStyle`
   erweitert um die CSS von mermaid-cli — Regeln aus `<style>` nach Spezifität auf die Elemente
   anwenden (Selektoren über `lxml.cssselect`, Paket `cssselect` ins Extra `diagrams`), dann
   `style`-Attribut, dann Präsentationsattribute; Farben als Hex, `rgb()`, `hsl()`, Namen;
   Unbekanntes wirft weiterhin. `foreignObject` ist ein Fehler.
2. **Renderer** `src/pta_documents/diagrams/mermaid.py`: `MermaidRenderer(command=None,
   chromium=None, timeout_s=60, on_error=MermaidErrorMode.THROW)`. Befehl aus `command`, sonst
   Umgebung `PTA_DOCUMENTS_MMDC`, sonst `mmdc` im `PATH`; Chromium aus `chromium`, sonst
   `PUPPETEER_EXECUTABLE_PATH` (sonst das von puppeteer mitgebrachte).
3. Aufruf ohne Dateien: `mmdc -i - -o - -e svg -b white -q`, Code über stdin, SVG über stdout,
   `subprocess.run` mit Zeitlimit. Die Einstellungen kommen als `%%{init: …}%%` vor den Code:
   `theme: base`, `securityLevel: strict`, `htmlLabels: false` (auch für `flowchart`),
   `fontFamily: "Segoe UI, Selawik, sans-serif"` und `themeVariables` aus `design/colors.py` —
   Hintergrund weiß, Text `TEXT_WORD` bzw. `TEXT_SLIDES` (je nach Zielformat der Anfrage, E02-S04),
   Linien `GREY_DARK`, Rahmen und Akzent `PTA_BLUE`, Flächen `GREY_LIGHT`, Torten `ACCENTS`.
4. Unterstützte Typen wie DocLibs (flowchart/graph, sequenceDiagram, classDiagram,
   stateDiagram-v2, erDiagram, pie, gantt, mindmap), erkannt an der ersten Zeile; andere Typen
   bleiben Code. Ein Typ, dessen SVG sich bei der Umsetzung nicht ohne `foreignObject` ergibt,
   fliegt aus der Liste und wird in den Implementierungsnotizen genannt.
5. Fehler: ein Syntaxfehler (Exit-Code ≠ 0, Meldung von mermaid auf stderr) wird je nach
   `on_error` ein Fehler mit Zeile des Blocks und Mermaid-Meldung oder bleibt Code; Zeitüberschreitung
   und fehlendes Chromium ergeben klare Meldungen mit dem Hinweis, was einzurichten ist.
6. Ausgabe: `DrawingGraphic` — im PDF durch E05-S04, in Folien als Formengruppe mit dem
   Schreiber aus E06-S02 (`generation/pptx/drawing.py`), Text in Segoe UI, Vorlagenformen für
   Rechteck, abgerundetes Rechteck und Ellipse. Im DOCX über E03-S04.
7. Einrichtung in `docs/verwendung.md`: Node.js, mermaid-cli in festgelegter Version, Chromium
   bzw. `PUPPETEER_EXECUTABLE_PATH`; Abschnitt der Anleitung (`AuthoringGuide/Diagrams.md`,
   deutsch) als `MermaidRenderer.authoring_guide`.
8. Tests: `tests/drawing/test_svg*.py` aus den DocLibs-Fällen (laufen immer); je Typ ein von
   mermaid-cli aufgezeichnetes SVG unter `tests/diagrams/samples/` mit erwarteter Zeichnung
   (Textformat wie DocLibs `DrawingFormat.cs`), damit die Umsetzung ohne Node prüfbar bleibt;
   `test_mermaid.py` (Aufruf, Farben, Fehler, Typen bleiben Code) und `diagrams.md` → PDF und
   PPTX laufen nur, wenn `mmdc` gefunden wird, sonst übersprungen. Dateien nach `.tmp/review/`.

## Akzeptanzkriterien

- [ ] Jeder unterstützte Typ aus `diagrams.md` erscheint im PDF als Vektorgrafik und in Folien
      als bearbeitbare Formengruppe in den PTA-Farben.
- [ ] Kein Aufruf verlässt den Rechner; mermaid-cli wird nur lokal gestartet.
- [ ] Ein Syntaxfehler nennt die Zeile des Blocks; mit `KEEP_CODE` bleibt der Block Code.
- [ ] Die SVG-Übersetzung wirft bei allem, was sie nicht kennt, statt es wegzulassen.
- [ ] Ohne mermaid-cli laufen alle übrigen Tests; die Mermaid-Tests werden übersprungen.

## Offene Fragen

1. Was passiert, wenn ein Dokument einen ` ```mermaid `-Block enthält, mermaid-cli aber nicht
   eingerichtet ist: Fehler mit Einrichtungshinweis (Vorschlag), oder der Block bleibt still als
   Code stehen?

> (2026-11-07) Block bleibt als Code, Hinweis `code-not-drawn` (E08-S01) mit Einrichtungshinweis.

2. Wo wird mermaid-cli installiert: global per `npm install -g @mermaid-js/mermaid-cli@<Version>`
   und nur dokumentiert, oder repo-lokal (`tools/mermaid/package.json`, `./run.sh setup` ruft
   `npm ci`, wenn Node vorhanden ist)? Vorschlag: repo-lokal, damit die Version fest ist.

> (2026-11-07) Repo-lokal (`tools/mermaid/package.json`, `npm ci` in `./run.sh setup`, wenn Node vorhanden).

## Notizen

- Jeder Aufruf startet ein Chromium (etwa 1–2 s). Bei vielen Diagrammen kann ein Lauf je
  Dokument mit Markdown-Eingabe (`mmdc -i doc.md`) helfen; erst messen, dann entscheiden.
- Prüfpunkt: dass `mmdc` stdin/stdout (`-i -`/`-o -`) in der gewählten Version kann; sonst
  schreibt der Renderer in ein `tempfile.TemporaryDirectory`.
- Die SVG-Übersetzung im Kern kann auch das Logo (E01-S04, E05-S03) als Vektor zeichnen.
- (2026-11-07, E02-S04) Standard eintragen in `generation/common/renderers.default_renderers()`
  — nur, wenn mermaid-cli gefunden wird (Entscheidung: standardmäßig an, wenn verfügbar).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: SVG → `Drawing` im Kern (`src/pta_documents/drawing/svg.py`,
`svg_geometry.py`, `svg_style.py`), Renderer `src/pta_documents/diagrams/mermaid.py`
(`MermaidRenderer`, `MermaidErrorMode`, `SUPPORTED`, `find_command`, `init_directive`),
Farben `src/pta_documents/design/diagram_colors.py`, `RendererUnavailableError` in
`generation/common/renderers.py` (Standard-Renderer mit Mermaid, wenn `mmdc` gefunden wird) und
`code_blocks.py` (Hinweis mit Grund und Einrichtungshinweis). mermaid-cli repo-lokal:
`tools/mermaid/package.json` + `package-lock.json` (`@mermaid-js/mermaid-cli` 12.2.0, puppeteer
25.16.0, MIT), `npm ci` in `./run.sh setup` und `run.ps1 setup` (nur mit Node.js),
`node_modules/` git-ignoriert, Werkzeug `./run.sh mermaid` (prüft die Einrichtung, zeichnet
`.mmd`-Dateien nach `.tmp/mermaid/`). Extra `diagrams = ["cssselect>=1.2"]` (BSD-3-Clause),
`setup` installiert es mit. Tests (126 neu): `tests/drawing/test_svg.py`,
`test_svg_geometry.py`, `test_svg_style.py` (Port der DocLibs-Fälle plus mermaid-cli-CSS),
`tests/diagrams/test_recorded.py` (je Typ ein aufgezeichnetes SVG mit Schnappschuss
`samples/mermaid-<typ>.expected.txt`, laufen immer), `tests/diagrams/test_mermaid.py` (mit einem
Ersatz-`mmdc`-Skript ohne Node; drei Fälle mit echtem mmdc, sonst übersprungen),
`tests/diagrams/support.py` (Textformat der Zeichnung wie DocLibs `DrawingFormat.cs`,
`mermaid_works`, `drawable`); angepasst: `tests/generation/pptx/test_notes.py` (Renderer explizit),
die drei Beispieltests (Dateien mit Mermaid ohne funktionierendes mmdc übersprungen). Beispiel
`samples/funktionen/mermaid-praesentation.md` (jede Art, Quelltext in den Notizen) mit README
und Rundreise. Doku: `docs/verwendung.md` (Abschnitt „Mermaid (E06-S03)" mit „SVG →
`Drawing`", Renderer, Hinweiscodes), `docs/anleitung.md` (Einrichten, „Diagramme mit Mermaid",
Fehler), `docs/ki-anleitung.md`; `ai/Standards.md` (Extras, npm-Lockfile), `ai/Gedächtnis.md`.

### Entscheidungen

- **Fehlendes mermaid-cli** (Frage 1): Block bleibt Code, `code-not-drawn` mit
  Einrichtungshinweis. Dasselbe gilt, wenn `mmdc` da ist, aber Chromium nicht startet — dafür
  der neue `RendererUnavailableError` (Meldung nennt `PUPPETEER_EXECUTABLE_PATH` und
  `PTA_DOCUMENTS_PUPPETEER_CONFIG`). Zeitüberschreitung bleibt ein Fehler (Plan Punkt 5).
- **Installation** (Frage 2): repo-lokal in `tools/mermaid/`, mit `package-lock.json`, damit die
  Versionen fest sind. Gewählt wurde die aktuelle mermaid-cli 12.2.0 (sie verlangt puppeteer 25
  als Peer; 25.16.0 fest).
- **Wo `mmdc` herkommt:** `command` → `PTA_DOCUMENTS_MMDC` → `mmdc` im `PATH` → repo-lokales
  `tools/mermaid/node_modules/.bin/mmdc` (relativ zur Quelldatei, gilt also für den editierbaren
  Klon). Ohne das letzte fände die Bibliothek die Installation von `setup` nie.
- **Aufruf** wie im Plan: `mmdc -i - -o - -e svg -b white -q` (stdin/stdout gehen mit 12.2.0,
  Prüfpunkt der Notizen erledigt), Einstellungen als `%%{init: …}%%`-Zeile vor dem Code:
  `theme: base`, `securityLevel: strict`, `htmlLabels: false` (auch `flowchart`), Schrift
  `Segoe UI, Selawik, sans-serif`, Theme-Variablen aus `design/diagram_colors.py`. Zusätzlich
  `look: classic` (Mermaid 12 zeichnet sonst „neo" mit animierten Strichmustern) und
  `flowchart.wrappingWidth: 300` (bei 200 brach Chromium ohne Segoe UI Wörter wie
  „Markdown-Dokument" mitten im Wort).
- **Farben:** Flächen `GREY_LIGHT`, Rahmen/Akzent `PTA_BLUE`, Linien `GREY_DARK`, Text je Format,
  Hintergrund weiß, Torten und Mindmap-Zweige die Akzente in Epic-Reihenfolge, Notizen und
  Aktivierungen `tint(LIGHT_BLUE, 0.3)`, Gruppen `tint(GREY_LIGHT, 0.4)`, Gantt-Balken
  `PTA_BLUE` mit weißer Schrift, kritisch `DARK_BLUE` mit `SIGNAL_RED`-Rand, Heute-Linie
  `SIGNAL_RED`. Was die Variablen nicht erreichen, setzt `themeCSS` (Gantt-Gitter, gefüllte
  Sequenz-Pfeilspitzen); ein Test prüft, dass jede Farbe aller acht Typen eine PTA-Farbe oder
  deren Tint ist.
- **SVG-Übersetzung:** Port von `SvgDrawing`/`SvgGeometry`/`SvgStyle`, erweitert um die
  Kaskade (Regeln nach Wichtigkeit, Spezifität, Reihenfolge; dann `style`, dann Attribute),
  `rgb()`/`hsl()`/Namen/`currentColor`, `em` relativ zur Schriftgröße, `pt`, Marker mit
  `viewBox` (`xMidYMid meet`), CSS-`transform` mit `transform-origin` (Gantt-Meilenstein),
  `dominant-baseline` (zentral = +0,35 em), `fill-rule` (`even_odd` des Modells), Breite `100%`
  = `viewBox`. Leere Attribute (`font-weight=""`) gelten als nicht gesetzt, negative
  `stroke-width` werden wie in CSS verworfen, ein Strichmuster ohne Lücken ist durchgezogen.
- **Weggelassen statt Fehler:** Schatten (`filter`, Element und Eigenschaft), `symbol` (nur
  über `<use>` sichtbar, das wirft), `@keyframes`/`@font-face`/`@import`, Pseudo-Elemente und
  `:hover`. Unbekannte At-Regeln, `foreignObject`, `<image>`, `<use>`, `clip-path`, `mask`,
  gedrehter Text, unbekannte Farben/Einheiten werfen `SvgDrawingError`.
- **Alle acht Typen** ergeben sich mit `htmlLabels: false` ohne `foreignObject`; keiner fiel
  aus der Liste. `graph` ist wie `flowchart` erkannt; `stateDiagram` (v1) wie geplant nicht.
- **Fehlermeldung:** `Line N: The mermaid block cannot be drawn: <Meldung von Mermaid ohne
  JavaScript-Stack>`; die Zeilennummer *in* Mermaids Meldung zählt Mermaid selbst (die
  `init`-Zeile eingeschlossen) — sie ist nicht umgerechnet.

### Abweichungen

- **Word:** Plan Punkt 6 sagt „im DOCX über E03-S04"; bis dahin wirft der Renderer für DOCX
  `RendererUnavailableError` („Word does not draw Mermaid diagrams yet"), der Block bleibt Code
  mit Hinweis — statt wie `financial-chart` mit „does not support yet" abzubrechen, weil
  Mermaid-Blöcke in Word bisher als Code durchliefen und Berichte sonst bräche, sobald
  mermaid-cli eingerichtet wird. `mmdc` startet für Word gar nicht.
- **Kein PDF-Test** (Plan Punkt 8): es gibt noch keinen PDF-Generator (E05).
- `DiagramLook` von DocLibs (Mermaider-spezifisches Umgestalten: fette erste Zeile,
  Datenbank-Symbol, Gruppen als Flächen) ist nicht portiert; das Aussehen kommt aus den
  Theme-Variablen. `letter-spacing` fehlt im Zeichenmodell und wird nicht gelesen.
- `diagrams.md` ist als `tests/diagrams/samples/diagramme.md` deutsch übersetzt; die
  Beispielpräsentation steht als eigene Datei `mermaid-praesentation.md` neben der großen, damit
  diese ohne mermaid-cli weiter geprüft wird.

### Warnungen

- **Chromium-Sandbox:** Auf dieser Maschine lädt puppeteer kein Chrome (kein `unzip`), und das
  vorhandene `chrome-headless-shell` von Playwright startet nur mit `--no-sandbox` (Ubuntu ohne
  User-Namespaces). Darum gibt es `PTA_DOCUMENTS_PUPPETEER_CONFIG` (eine Datei
  `{"args": ["--no-sandbox"]}`) — eine zusätzliche Stellschraube, die der Plan nicht vorsah.
  `--no-sandbox` schwächt die Isolation des Browsers; vertretbar, weil er nur eigenen
  Mermaid-Code mit `securityLevel: strict` und ohne Netz zeichnet, aber eine bewusste
  Entscheidung des Menschen. **Ohne diese beiden Variablen werden auf dieser Maschine alle
  Tests mit echtem mmdc übersprungen** und Mermaid-Blöcke bleiben Code; zum Ausprobieren:
  `export PUPPETEER_EXECUTABLE_PATH=~/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell`
  und `PTA_DOCUMENTS_PUPPETEER_CONFIG` auf eine solche Datei, dann `./run.sh mermaid`.
- **Repo-lokaler Fund** über den Pfad der Quelldatei funktioniert nur im editierbaren Klon;
  ein Paket aus dem Wheel braucht `mmdc` im `PATH` oder `PTA_DOCUMENTS_MMDC`.
- **Mit eingerichtetem mermaid-cli** nehmen alle Generatoren Mermaid standardmäßig; Tests, die
  ```` ```mermaid ```` mit Standardoptionen erzeugen, hängen damit vom Rechner ab (der bisherige
  PPTX-Hinweistest setzt seine Renderer jetzt selbst).
- **Tortenbeschriftungen** sind weiß (`pieSectionTextColor` gilt für alle Stücke): auf
  `LIGHT_BLUE` und `GREY_MID`/`GREY_LIGHT` schlecht lesbar. Die Legende daneben ist lesbar.
- **Gefüllte Pfeilspitzen der Sequenzdiagramme** setzt `themeCSS` über die feste ID
  `my-svg-filled-head`, die mermaid-cli vergibt; Attributselektoren (`[id$=…]`) im `themeCSS`
  zerstören Mermaids `init`-Zeile.
- **Textmaße:** Mermaid misst die Beschriftungen im Chromium; ist Segoe UI dort nicht
  installiert (hier: DejaVu Sans), sind Knoten etwas breiter als nötig. Eine eingebettete
  Selawik per `--cssFile` änderte nichts an der Messung und ist nicht eingebaut.
- Die Ausgabe von mermaid-cli ändert sich von Lauf zu Lauf leicht; die aufgezeichneten SVGs
  werden nur mit `PTA_DOCUMENTS_UPDATE_EXPECTED=1` erneuert, dann den Diff der
  `*.expected.txt` ansehen.

### Prüfpunkte

- `.tmp/review/diagramme.pptx` (aus `tests/diagrams/samples/diagramme.md`, nur mit
  funktionierendem mmdc) und `.tmp/review/funktionen/mermaid-praesentation.pptx` in PowerPoint
  öffnen: keine Reparaturmeldung, jede der acht Folien eine Gruppe bearbeitbarer Formen in den
  PTA-Farben, Text in Segoe UI an der richtigen Stelle, die Journey bleibt Code.
- Mit eingerichtetem mermaid-cli: `./run.sh mermaid`, dann `./run.sh test tests/diagrams`
  (45 Fälle, keiner übersprungen) und `./run.sh generate-samples funktionen` ohne Hinweise.
- Ohne: `./run.sh generate` eines Decks mit Mermaid zeigt den Hinweis mit Einrichtungsanleitung.

### Offene Punkte

- **Word** (E03-S04) und **PDF** (E05-S04): `DrawingGraphic` setzen; dann den Word-Zweig von
  `MermaidRenderer.render` entfernen und die Beispiele um einen Bericht ergänzen.
- Je Block startet ein Chromium (~0,7 s); ein Lauf je Dokument (`mmdc -i doc.md`) wäre erst bei
  vielen Diagrammen zu messen (Notiz des Plans).
- Ob `--no-sandbox` dauerhaft gewollt ist oder Chromium per AppArmor-Profil ordentlich
  eingerichtet werden soll, entscheidet der Mensch.
