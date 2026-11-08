# E15-S02 Schrittfolge, Harvey Balls und Risikomatrix

> Status: in Prüfung
> Epic: [E15 Visuelle Bausteine](../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Drei Klassiker der Beratungsfolie aus Markdown: `::: steps` zeichnet ein Vorgehen als Chevrons
(Pfeilformen) mit Titel und Untertext je Schritt; Tabellenzellen `[0/4]` … `[4/4]` werden Harvey
Balls ○ ◔ ◑ ◕ ● für Bewertungsmatrizen; `::: riskmatrix` macht aus einer Risikotabelle die
5 × 5-Matrix aus Wahrscheinlichkeit und Auswirkung mit nummerierten Punkten und Legende.

## Kontext

- Flow-Folien und Raster: E04-S03 (Inhaltsfläche 31,20 × 13,10 cm, Spalten 7,00 cm, Abstand
  1,00 cm; Karten-Titel 18 pt PTA-Blau, Text 14 pt). Status-Labels in Tabellenzellen (ein
  Code-Span) kennt E02-S02; Harvey Balls sind das zweite Zellenmuster.
- Signalfarben `STATUS_COLORS` in `design/colors.py` (Grün, Gelb-Orange `EAB500`, Rot);
  Hervorhebung Gelb `FDDC35`. Die Designanalyse erlaubt Signalfarben nur für Status — Risiken
  sind Status.
- Zeichnen über `Drawing` (E02-S03) → Formgruppe (PPTX) bzw. SVG/PNG (Word, E03-S04). Tabellen in
  Word: Tabellenformat „PTA" (E03-S02); Folientabellen: `visuals.draw_table` (E04-S02).

## Vorgeschlagener Ansatz

1. **Schrittfolge** `::: steps`, Inhalt ein `###` je Schritt mit optionalem Absatz darunter, 3–6
   Schritte; `### Umsetzung {.current}` hebt einen hervor.
   - `drawing/steps.py`: Chevrons (`ShapeKind.CHEVRON`, neu im Zeichenmodell — in PPTX die
     Autoform `chevron`, in SVG ein Pfad) nebeneinander über die Inhaltsbreite, erster als
     `homePlate`; Füllung `9FD8FF` mit Titel `004676`, der aktuelle PTA-Blau mit weißer Schrift,
     Schritte vor dem aktuellen `E6E6E6`; Titel 16 pt fett, Untertext 12 pt `404040` unter dem
     Chevron (nicht hinein — PTA-Muster sind schlicht).
   - Ohne `{.current}` alle Hellblau. Mehr als sechs Schritte: Fehler mit Hinweis auf zwei Folien.
   - Word: Grafik in Satzspiegelbreite; Untertexte unter der Grafik als Liste, wenn sie bei
     10 pt nicht unter die Chevrons passen.
2. **Harvey Balls**: eine Tabellenzelle, die genau `[n/4]` enthält (`n` 0–4), in jedem Format:
   - PowerPoint: in der Zelle ein Kreis Ø 0,45 cm, Rand `004676` 1 pt, Füllsegment PTA-Blau als
     Tortenform (`pie`-Autoform mit Winkel `n × 90°`); `[4/4]` voll, `[0/4]` leer. Zelle
     zentriert. Gezeichnet in `visuals.draw_table` als Form über der Zelle (Tabellenzellen
     tragen keine Formen; die Gruppe liegt an der Zellmitte).
   - Word/PDF: Unicode ○◔◑◕● in Segoe UI Symbol, 12 pt, PTA-Blau (Frage 1 zur Alternative als
     Bild).
   - Rückweg (E07): PowerPoint-Form → `[n/4]` nicht rekonstruierbar, bleibt Leerzelle; Word →
     Unicode-Zeichen; der PPTX-Konverter erkennt die Tortenform über ihren Namen `harvey-n`.
   - Guide: „Bewertungsmatrix: Kriterien in Zeilen, Optionen in Spalten, `[3/4]` je Zelle."
3. **Risikomatrix** `::: riskmatrix` mit genau einer Tabelle: Spalten Nr | Risiko |
   Wahrscheinlichkeit (1–5) | Auswirkung (1–5), optional Maßnahme; 1–15 Zeilen.
   - `drawing/riskmatrix.py`: Quadrat 5 × 5 Zellen (Zelle 1,6 cm), Achsen beschriftet
     („Wahrscheinlichkeit" →, „Auswirkung" ↑, 10 pt `787878`), Zellfarben nach Produkt
     W × A: ≤ 4 grün, ≤ 12 Gelb-Orange, sonst rot aus `STATUS_COLORS`, 35 % Deckkraft (Tint);
     Risiken als Kreise Ø 0,6 cm `004676` mit weißer Nummer, mehrere in einer Zelle versetzt.
   - Daneben (PowerPoint) bzw. darunter (Word) die Legende als Tabelle Nr | Risiko | Maßnahme im
     PTA-Tabellenformat; in Word ist die Matrix eine Grafik (Frage 2).
   - Werte außerhalb 1–5 oder fehlende Nummer: Fehler mit Zeile.
4. **Registrierung** in `layout_syntax.CONTAINERS` (`steps`, `riskmatrix`) und `label_cell`
   um `harvey_cell(cell) -> int | None` ergänzt (E02-S02, Token-Hilfen).
5. **Tests**: Chevronzahl und Breite, `{.current}` Farbwechsel, Fehler bei 7 Schritten; Harvey
   Balls in beiden Formaten, Rundreise mit dokumentierter Abweichung; Matrixfarben je Produkt,
   Versatz mehrerer Punkte, Legende fortlaufend; Beispiel in `samples/funktionen/`.

## Akzeptanzkriterien

- [x] `::: steps` ergibt Chevrons über die Inhaltsbreite, der aktuelle Schritt in PTA-Blau.
- [x] `[3/4]` in einer Tabellenzelle wird in PowerPoint eine Tortenform, in Word ◕ in PTA-Blau.
- [x] `::: riskmatrix` ergibt eine 5 × 5-Matrix in Signalfarben mit nummerierten Risiken und
      Legende; Werte außerhalb 1–5 sind Fehler.
- [x] Farben nur aus `design.colors`; Signalfarben nur in der Risikomatrix.

## Offene Fragen

1. Harvey Balls in Word/PDF als Unicode in Segoe UI Symbol (Vorschlag; auf PTA-Rechnern
   vorhanden, im PDF aber nicht in Selawik — dort Ersatz aus einer gebündelten Symbolschrift
   oder als kleines Bild) oder überall als Bild? Vorschlag: Unicode in Word, Bild im PDF.

> (2026-11-07) Unicode in Word, Bild im PDF.

2. Risikomatrix in Word als Grafik (Vorschlag) oder als 5 × 5-Word-Tabelle mit farbigen Zellen
   und Nummern als Text (editierbar, aber Achsenbeschriftung schwierig)?

> (2026-11-07) Als Grafik.

3. Schwellen der Matrixfarben (≤ 4 grün, ≤ 12 gelb, sonst rot) — gibt es eine PTA-Vorgabe aus dem
   Risikomanagement?

> (2026-11-07) Ja, ≤ 4 grün, ≤ 12 gelb, sonst rot; einstellbar.

## Notizen

- `ShapeKind.CHEVRON` und `ShapeKind.PIE` erweitern E02-S03 um zwei Formarten; SVG zeichnet sie
  als Pfad, PPTX als Autoform mit `adj`-Werten.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `generation/common/steps.py` (`Step`, `Steps`,
`read_steps`), `generation/common/risks.py` (`Risk`, `RiskMatrix`, `Thresholds`,
`thresholds_argument`, `read_risk_matrix`), `drawing/shapes.py` (`chevron`, `pie`),
`drawing/steps.py` (`draw`, `texts_fit`, `text_room`), `drawing/riskmatrix.py` (`draw`,
`offsets`), `drawing/harvey.py` (`ball`). Angepasst: `drawing/model.py` (`ShapeKind.CHEVRON`,
`HOME_PLATE`, `PIE`; Felder `point_depth`, `angles`), `drawing/svg_output.py`,
`generation/common/layout_syntax.py` (`STEPS`, `RISK_MATRIX`, Prüfung beider Container),
`layout_tokens.py` (`harvey_cell`, `HARVEY_SYMBOLS`), `schedule.py` (Hilfen `child_blocks`,
`table_rows`, `error_at` öffentlich), PPTX `model.py` (`Run.harvey`, `StepsBlock`,
`RiskMatrixBlock`), `parser.py`, `flow_parser.py`, `flow.py`, `visuals.py` (`harvey_ball`),
`drawing.py` (Autoformen `chevron`/`homePlate`/`pie`, Gruppenname), Word `writer.py`
(`steps`, `risk_matrix`, `drawing_picture`, `_harvey_run`), `design/word.py`,
`design/slides.py` (`RISK_LEGEND_MIN_WIDTH`), PDF `layout/story.py` (`DRAWN_CONTAINERS`) und
`layout/flowables.py` (`HarveyBall`), `conversions/pptx.py` (Harvey Balls zurück als `[n/4]`).
Tests: `tests/generation/common/test_steps.py`, `test_risks.py`, `test_layout_parts.py`
(Harvey-Zellen), `tests/drawing/test_shapes.py`, `test_steps.py`, `test_riskmatrix.py`,
`tests/generation/pptx/test_visual_blocks.py`, `tests/generation/docx/test_visual_blocks.py`,
`tests/generation/pdf/test_generator.py`; `test_funktionen.py` verlangt `[n/4]` und
`::: riskmatrix <thresholds>`. Beispiele: Abschnitte „Schrittfolge", „Bewertungsmatrix",
„Risikomatrix" in `funktionen-bericht.md`, Kapitel „Schritte und Bewertungen" in
`funktionen-praesentation.md`, README, Rundreisen. Doku: `docs/verwendung.md` (Abschnitt
„Schrittfolge, Harvey Balls und Risikomatrix (E15-S02)", Syntaxtabelle, PDF-Stand),
`docs/anleitung.md`, `docs/ki-anleitung.md`; `ai/Gedächtnis.md`.

### Entscheidungen

- **Prüfung an einer Stelle** wie bei E15-S01: `layout_syntax.check` liest `::: steps` und
  `::: riskmatrix` vollständig, alle Formate melden dieselben Fehler mit Zeile.
- **Schritte:** nur `###` zählt als Schritt; je Schritt höchstens ein Absatz; weniger als drei
  Schritte sind ebenfalls ein Fehler (Plan: 3–6), höchstens ein `{.current}`, andere Attribute
  sind Fehler. Chevrons 1,6 cm hoch, Spitze 35 % der Höhe, 4 px Abstand; Titel bis zwei Zeilen
  (dann kleiner, nie unter 70 % = 11,2 pt). Graue Schritte (vor dem aktuellen) haben den Titel in
  `404040` (der Plan nennt dafür keine Schriftfarbe). Text unter dem Pfeil zentriert.
- **Word-Schritte:** Texte zuerst bei 12 pt, dann bei 10 pt unter den Pfeilen (`texts_fit`: kein
  Wort breiter als der Platz, höchstens fünf Zeilen); passt es nicht, zeigt das Bild nur die
  Titel und die Texte folgen als Aufzählung „**Titel**: Text".
- **Harvey Balls** nur in Körperzellen (nicht im Tabellenkopf). PowerPoint: Gruppe `harvey-n` aus
  weißem Kreis, PTA-blauer `pie`-Autoform (`adj1` = 12 Uhr) und Rand `004676` 1 pt, Ø 0,45 cm,
  mittig über der Zelle; die Zelle bleibt leer und ist zentriert. Word: Zeichen in
  „Segoe UI Symbol" 12 pt PTA-Blau (Antwort 1). PDF: als kleine Vektorgrafik auf dem Canvas
  (`HarveyBall`, Antwort 1 „Bild im PDF" — Vektor statt Pixelbild, gleich scharf und ohne Extra).
- **Risikomatrix:** Achsenbeschriftung = die Spaltenköpfe 3 und 4 (deutsch oder englisch, wie
  geschrieben), dazu die Zahlen 1–5 und kleine Pfeile als Formen (nicht als Zeichen ↑ →, die die
  gebündelte Schrift womöglich nicht hat). Zellen 1,6 cm mit 2 px weißem Spalt; Risiken als
  Kreise Ø 0,6 cm mit weißem Rand und Nummer 10 pt fett; mehrere in einer Zelle auf einem Raster
  nebeneinander, ab fünf enger und überlappend. Die Matrix steht in natürlicher Größe
  (≈ 8,5 × 9,1 cm), nicht auf die Breite gezogen.
- **Schwellen einstellbar** (Antwort 3) über Container-Argumente `green=4 yellow=12` (englisch
  wie die übrige Markdown-Syntax; ganze Zahlen 1–24, `green` < `yellow`, fehlende = Standard).
- **Nummern:** Pflicht, eindeutig, höchstens drei Zeichen (`3`, `R3`) — sie stehen im Kreis.
  Die Legende folgt der Reihenfolge der Tabelle.
- **Legende PowerPoint:** rechts neben der Matrix mit `COLUMN_GAP` (1 cm), als normale
  PTA-Tabelle (Größe nach `fit_table`); ist dort weniger als eine Rasterspalte (7 cm) frei — z. B.
  in `::: columns` —, steht sie darunter. Word: Tabelle „PTA" unter dem Bild.

### Abweichungen

- **PPTX-Konverter:** liest Harvey Balls als `[n/4]` zurück (Position der Gruppe `harvey-n` →
  Zelle der Tabelle), statt die Zelle leer zu lassen — die Rundreise ist damit verlustfrei. Der
  DOCX-Konverter liest wie geplant das Unicode-Zeichen (◕).
- Formarten: zusätzlich `ShapeKind.HOME_PLATE` (der Plan nennt `homePlate` nur für PowerPoint);
  Parameter als Felder `point_depth` und `angles` am `DrawingShape`.
- Die Leser liegen als `steps.py`/`risks.py` in `generation/common/` (wie `schedule.py`), die
  Zeichnungen wie geplant in `drawing/steps.py`/`drawing/riskmatrix.py`.
- `label_cell` blieb unverändert; `harvey_cell` steht daneben in `layout_tokens`.

### Warnungen

- **Ohne Office geprüft:** dass PowerPoint die Autoformen `chevron`/`homePlate`/`pie` mit den
  geschriebenen `adj`-Werten genau wie die SVG-Vorschau zeichnet und die Harvey-Gruppen über den
  Zellen sitzen, ist nicht in PowerPoint geprüft (keine Office-/LibreOffice-Installation). Die
  Lage der Bälle ist aus den geschriebenen Zeilenhöhen berechnet; wächst eine Zeile in
  PowerPoint (Umbruch), sitzt der Ball nicht mehr mittig.
- **Segoe UI Symbol** muss auf dem Rechner sein, der das Word-Dokument öffnet (auf PTA-Rechnern
  mit Windows vorhanden); sonst ersetzt Word die Schrift.
- **Textbreiten sind geschätzt** (halbe Schriftgröße je Zeichen) — lange Einzelwörter in
  schmalen Chevrons (sechs Schritte in Word) können trotz Verkleinern über den Pfeil ragen.
- **PDF:** `::: steps` und `::: riskmatrix` zeigen bis E05-S04 nur ihren Inhalt
  (Überschriften mit rohem `{.current}`, Tabelle) mit Hinweis `code-not-drawn`.
- Der Plan sagt „Signalfarben nur in der Risikomatrix"; einen eigenen Test dafür gibt es nicht
  (die Zeichnung der Schritte nutzt nachweislich nur Designfarben, `test_steps.py`).

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-praesentation.pptx`, Kapitel „Schritte und Bewertungen":
  Chevrons einzeln verschieben (Umsetzung PTA-Blau, davor grau); Harvey Balls mittig in den
  Zellen; Risikomatrix links, Legende rechts.
- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitte „Schrittfolge",
  „Bewertungsmatrix", „Risikomatrix": Bild in Satzspiegelbreite, ◕ in PTA-Blau, Matrix mit
  Legende darunter.
- `./run.sh test tests/generation/common/test_steps.py tests/generation/common/test_risks.py
  tests/drawing/test_steps.py tests/drawing/test_riskmatrix.py tests/drawing/test_shapes.py
  tests/generation/pptx/test_visual_blocks.py tests/generation/docx/test_visual_blocks.py`.

### Offene Punkte

- **PDF (E05-S04):** `::: steps` über `drawing.steps.draw(…, Satzspiegelbreite)` mit derselben
  Text-Regel wie Word (`word.STEPS_TEXT_PT`, Liste als Rückfall), `::: riskmatrix` über
  `drawing.riskmatrix.draw` plus Legende als Tabelle; danach `DRAWN_CONTAINERS` in
  `layout/story.py` leeren. — *(2026-11-08) Erledigt in E05-S04; `DRAWN_CONTAINERS` ist
  entfallen.*
- Der DOCX-Konverter könnte ◕ & Co. in Tabellenzellen wieder zu `[n/4]` machen (heute: Zeichen).
