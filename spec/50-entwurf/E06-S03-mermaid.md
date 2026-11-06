# E06-S03 Mermaid über mermaid-cli

> Status: Entwurf
> Epic: [E06 Diagramme und Charts](E06-diagramme-und-charts.md)

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

>

2. Wo wird mermaid-cli installiert: global per `npm install -g @mermaid-js/mermaid-cli@<Version>`
   und nur dokumentiert, oder repo-lokal (`tools/mermaid/package.json`, `./run.sh setup` ruft
   `npm ci`, wenn Node vorhanden ist)? Vorschlag: repo-lokal, damit die Version fest ist.

>

## Notizen

- Jeder Aufruf startet ein Chromium (etwa 1–2 s). Bei vielen Diagrammen kann ein Lauf je
  Dokument mit Markdown-Eingabe (`mmdc -i doc.md`) helfen; erst messen, dann entscheiden.
- Prüfpunkt: dass `mmdc` stdin/stdout (`-i -`/`-o -`) in der gewählten Version kann; sonst
  schreibt der Renderer in ein `tempfile.TemporaryDirectory`.
- Die SVG-Übersetzung im Kern kann auch das Logo (E01-S04, E05-S03) als Vektor zeichnen.
