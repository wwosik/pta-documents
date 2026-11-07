# E15-S01 Zeitstrahl und Gantt

> Status: Entwurf
> Epic: [E15 Visuelle Bausteine](E15-visuelle-bausteine.md)

## Zusammenfassung

`::: timeline` macht aus einer Liste von Terminen einen horizontalen Zeitstrahl mit Marken und
Beschriftungen; `::: gantt` macht aus einer Tabelle (Vorgang, Start, Ende) einen Projektplan — in
PowerPoint Balken aus Formen in der Inhaltsfläche, in Word eine editierbare Tabelle mit
schattierten Zellen je Monat oder Woche. Beides sind die Grafiken, die in Angeboten und
Statusberichten sonst von Hand entstehen.

## Kontext

- Mermaid kennt `gantt` (E06-S03), braucht aber Node.js und Chromium und zeichnet in fremdem Stil;
  einen Zeitstrahl kennt es gar nicht. Die Bausteine hier laufen ohne Extra und im PTA-Design.
- Zeichnen: `Drawing` (E02-S03) → Formgruppe in PPTX (Weg aus E06-S03, „editierbare Formen in
  Folien"), SVG/PNG in Word (E03-S04). Raster und Inhaltsfläche: E04-S03 (1,33/4,62 cm,
  31,20 × 13,10 cm, Spalten 7,00/15,10 cm).
- Front Matter `datum` wird schon geparst (`FrontMatter.date`, `2026-11-06` oder `06.11.2026`);
  dieselbe Datumslogik dient den Terminen.
- Container-Prüfung und Argumente (`::: gantt raster=woche`): `layout_syntax` aus E02-S02.

## Vorgeschlagener Ansatz

1. **Syntax** in `generation/common/layout_syntax.py` registrieren:

   ```markdown
   ::: timeline
   - 2026-01: Kick-off
   - 2026-Q2: Analyse abgeschlossen {.done}
   - 15.09.2026: Go-live
   - 2027: Betrieb
   :::

   ::: gantt raster=monat
   | Vorgang   | Start      | Ende       | Wer    |
   | --------- | ---------- | ---------- | ------ |
   | Analyse   | 2026-01-12 | 2026-02-27 | PTA    |
   | Umsetzung | 2026-03-02 | 2026-06-30 | PTA    |
   | Abnahme   | 2026-07-01 | 2026-07-15 | Kunde  |
   :::
   ```

   Termine: Jahr, Jahr-Monat, Jahr-Quartal (`2026-Q2`), Datum in beiden Schreibweisen;
   `heute` als Wort. Ein unlesbarer Termin ist ein Fehler mit Zeile; `timeline` braucht 2–8
   Einträge, `gantt` 1–12 Zeilen (mehr: Fehler mit Hinweis auf Teilung). Die vierte Spalte ist
   frei benannt und optional.
2. **Modell** `generation/common/schedule.py`: `Timeline(entries: tuple[TimelineEntry, ...])`,
   `TimelineEntry(when: DateSpan, text: Runs, done: bool)`, `Gantt(rows, grid: Grid)`,
   `GanttRow(name, start, end, owner)`; `DateSpan` mit `start`/`end` (ein Monat, ein Quartal
   oder ein Tag) und `grid_for(rows) -> Grid` (`monat`, wenn die Gesamtdauer über 16 Wochen
   liegt, sonst `woche`; `quartal` ab zwei Jahren; `raster=` erzwingt).
3. **Zeichnung** `drawing/schedule.py` (reine `Drawing`-Erzeugung, format­unabhängig):
   - Zeitstrahl: Linie `AFAFAF` 2 px über die volle Breite, Marken als Kreise Ø 14 px, PTA-Blau,
     erledigte (`{.done}`) und vergangene (vor `heute` bzw. dem Front-Matter-`datum`) in
     `787878`; Termin 12 pt fett PTA-Blau über der Linie, Text 12 pt `404040` darunter,
     abwechselnd oben/unten, wenn Beschriftungen kollidieren; Jahre als Abschnittsmarken.
   - Gantt: links Vorgangsnamen (14 pt), rechts das Raster mit Spalten je Einheit (Linien
     `E6E6E6`, Monats-/KW-Beschriftung 10 pt `787878`), Balken PTA-Blau Höhe 60 % der Zeile,
     Vorgänge der Spalte „Wer" ungleich dem ersten Wert in Hellblau `9FD8FF` mit dunkler Schrift;
     Heute-Linie `004676` gestrichelt, wenn `heute` im Bereich liegt.
4. **PowerPoint** (`generation/pptx/`): das `Drawing` als Formgruppe auf `Nur Titel`, Breite der
   Inhaltsfläche, Höhe nach Inhalt (Zeitstrahl ≈ 4 cm, Gantt 0,9 cm je Zeile + Kopf), gestapelt
   wie Flow-Blöcke (E04-S03); passt es nicht, Hinweis `slide-overfull` (E08-S01).
5. **Word** (`generation/docx/`): Zeitstrahl als Grafik über E03-S04 (Satzspiegelbreite);
   Gantt als **Tabelle** im Tabellenformat „PTA" (E03-S02): Spalte Vorgang, optional Wer, dann
   eine schmale Spalte je Einheit mit Kopf (Monatskürzel/KW), Zellen der Laufzeit mit Schattierung
   `006FB9` (`w:shd`), Heute-Spalte mit rechtem Rand `004676`. Breite Raster (> 24 Spalten) sind
   ein Fehler mit Hinweis auf `raster=`. PDF (E05-S04) zeichnet beide als Grafik.
6. **Konverter (E07):** Formgruppe → Bild, Gantt-Tabelle → Markdown-Tabelle mit leeren/gefüllten
   Zellen (`■`); Abweichung in den Erwartungsdateien.
7. **Tests** `tests/drawing/test_schedule.py` (Terminparser, Rasterwahl, Kollisionen der
   Beschriftung, Farben nur aus `design.colors`), `tests/generation/*/test_schedule.py`
   (Formgruppe in der Inhaltsfläche, Word-Tabelle mit richtiger Zellenzahl und Schattierung,
   Fehler bei zu vielen Zeilen/Spalten), Beispiel in `samples/funktionen/`.

## Akzeptanzkriterien

- [ ] `::: timeline` und `::: gantt` ergeben in PowerPoint Formgruppen innerhalb der
      Inhaltsfläche, deren Formen sich einzeln verschieben lassen.
- [ ] In Word ist der Gantt eine Tabelle im PTA-Tabellenformat mit schattierten Laufzeitzellen; der
      Zeitstrahl eine Grafik in Satzspiegelbreite.
- [ ] Vergangene und erledigte Einträge sind grau, laufende PTA-Blau; alle Farben aus `design.colors`.
- [ ] Unlesbare Termine, zu viele Zeilen oder Spalten sind Fehler mit Zeile und Hinweis.

## Offene Fragen

1. Soll der Gantt Abhängigkeiten (`nach: Analyse`) und Meilensteine (Start = Ende → Raute)
   kennen? Vorschlag: Meilensteine ja (Raute `004676`), Abhängigkeitspfeile nein — das wird
   schnell ein Projektwerkzeug.

>

2. Wochenraster: Kalenderwochen (`KW 03`) oder Datum des Montags? Vorschlag: KW, wie
   Projektpläne bei Kunden üblich.

>

## Notizen

- Datumsgrenzen des Gantt-Rasters werden auf ganze Einheiten gerundet (Monatsanfang, Montag).
