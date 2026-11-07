# E15-S02 Schrittfolge, Harvey Balls und Risikomatrix

> Status: Entwurf
> Epic: [E15 Visuelle Bausteine](E15-visuelle-bausteine.md)

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

- [ ] `::: steps` ergibt Chevrons über die Inhaltsbreite, der aktuelle Schritt in PTA-Blau.
- [ ] `[3/4]` in einer Tabellenzelle wird in PowerPoint eine Tortenform, in Word ◕ in PTA-Blau.
- [ ] `::: riskmatrix` ergibt eine 5 × 5-Matrix in Signalfarben mit nummerierten Risiken und
      Legende; Werte außerhalb 1–5 sind Fehler.
- [ ] Farben nur aus `design.colors`; Signalfarben nur in der Risikomatrix.

## Offene Fragen

1. Harvey Balls in Word/PDF als Unicode in Segoe UI Symbol (Vorschlag; auf PTA-Rechnern
   vorhanden, im PDF aber nicht in Selawik — dort Ersatz aus einer gebündelten Symbolschrift
   oder als kleines Bild) oder überall als Bild? Vorschlag: Unicode in Word, Bild im PDF.

>

2. Risikomatrix in Word als Grafik (Vorschlag) oder als 5 × 5-Word-Tabelle mit farbigen Zellen
   und Nummern als Text (editierbar, aber Achsenbeschriftung schwierig)?

>

3. Schwellen der Matrixfarben (≤ 4 grün, ≤ 12 gelb, sonst rot) — gibt es eine PTA-Vorgabe aus dem
   Risikomanagement?

>

## Notizen

- `ShapeKind.CHEVRON` und `ShapeKind.PIE` erweitern E02-S03 um zwei Formarten; SVG zeichnet sie
  als Pfad, PPTX als Autoform mit `adj`-Werten.
