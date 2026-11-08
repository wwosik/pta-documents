# E15-S01 Zeitstrahl und Gantt

> Status: in Prüfung
> Epic: [E15 Visuelle Bausteine](../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

- [x] `::: timeline` und `::: gantt` ergeben in PowerPoint Formgruppen innerhalb der
      Inhaltsfläche, deren Formen sich einzeln verschieben lassen.
- [x] In Word ist der Gantt eine Tabelle im PTA-Tabellenformat mit schattierten Laufzeitzellen; der
      Zeitstrahl eine Grafik in Satzspiegelbreite.
- [x] Vergangene und erledigte Einträge sind grau, laufende PTA-Blau; alle Farben aus `design.colors`.
- [x] Unlesbare Termine, zu viele Zeilen oder Spalten sind Fehler mit Zeile und Hinweis.

## Offene Fragen

1. Soll der Gantt Abhängigkeiten (`nach: Analyse`) und Meilensteine (Start = Ende → Raute)
   kennen? Vorschlag: Meilensteine ja (Raute `004676`), Abhängigkeitspfeile nein — das wird
   schnell ein Projektwerkzeug.

> (2026-11-07) Meilensteine ja (Raute), Abhängigkeiten nein.

2. Wochenraster: Kalenderwochen (`KW 03`) oder Datum des Montags? Vorschlag: KW, wie
   Projektpläne bei Kunden üblich.

> (2026-11-07) Kalenderwochen.

## Notizen

- Datumsgrenzen des Gantt-Rasters werden auf ganze Einheiten gerundet (Monatsanfang, Montag).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: neu `generation/common/schedule.py` (Modell und Leser:
`DateSpan`, `TimelineEntry`, `Timeline`, `GanttRow`, `Gantt`, `Unit`, `Grid`, `parse_date`,
`grid_for`, `units`, `grid_argument`, `read_timeline`, `read_gantt`, `reference_day`) und
`drawing/schedule.py` (`draw`, `timeline`, `gantt`, `wrap`, `collides`); angepasst
`generation/common/layout_syntax.py` (`TIMELINE`, `GANTT`, `check(…, today)` liest beide
Container), `generation/pptx/model.py` (`ScheduleBlock`), `flow_parser.py`, `flow.py`
(`FlowWriter.schedule`), `parser.py`, `generation/docx/writer.py` (`timeline`, `gantt`,
`_right_rule`), `design/word.py` (`GANTT_*`), `conversions/docx.py` (`■` für gefüllte Zellen).
Tests: `tests/generation/common/test_schedule.py`, `tests/drawing/test_schedule.py`,
`tests/generation/pptx/test_schedule.py`, `tests/generation/docx/test_schedule.py`;
`test_funktionen.py` verlangt `::: gantt raster=<grid>`, `test_layout_syntax.py` kennt die neuen
Container. Beispiele: Abschnitte „Zeitstrahl"/„Projektplan" in `funktionen-bericht.md`, Kapitel
„Zeitstrahl und Projektplan" in `funktionen-praesentation.md`, README, Rundreisen. Doku:
`docs/verwendung.md` (Abschnitt „Zeitstrahl und Gantt (E15-S01)", Tabelle der Folien-Syntax),
`docs/anleitung.md`, `docs/ki-anleitung.md`; `ai/Gedächtnis.md`.

### Entscheidungen

- **Prüfung an einer Stelle:** `layout_syntax.check` liest Zeitstrahl und Gantt vollständig
  (`read_timeline`/`read_gantt`), damit Word, PowerPoint und später PDF dieselben Fehler mit
  derselben Zeile melden. Die Leser nennen die Zeile des falschen Eintrags bzw. der falschen
  Tabellenzeile selbst (`Line N: …`).
- **Mehr als 24 Spalten sind in allen Formaten ein Fehler** (Plan: Word), weil die Prüfung
  gemeinsam ist und ein so feines Raster auch auf der Folie nicht lesbar ist. Ohne `raster=`
  weicht die automatische Wahl vorher auf die nächstgröbere Einheit aus (z. B. 25 Monate →
  Quartale).
- **Zeitstrahl:** die Marken stehen **gleichmäßig verteilt in der Reihenfolge der Einträge**,
  nicht zeitproportional — sonst kollidieren eng liegende Termine ständig. Die Einträge müssen
  aufsteigend sein (sonst Fehler). Jahre stehen in einem Band über der Linie, ein Strich auf der
  Linie markiert den Jahreswechsel. Kollisionen: ist ein Termin, ein Wort oder der auf zwei
  Zeilen umbrochene Text breiter als sein Platz, stehen alle Einträge abwechselnd unter/über der
  Linie und haben doppelten Platz; Text wird auf bis zu drei Zeilen umbrochen, was dann noch
  nicht passt, verkleinert die Ausgabe über `max_width` (nie gekürzt).
- **Angezeigter Termin = wie geschrieben** (`2026-Q2`), nicht umformatiert.
- **Gantt-Raster:** Kopf je Spalte `Jan 26`, `Feb`, … (Jahr an der ersten Spalte und im Januar),
  `KW 03` bzw. `Q1 26`; Englisch `CW`/`Mar`. Eine Kopfzeile (keine zweite für Jahre), damit die
  Word-Tabelle ohne verbundene Zellen auskommt und der Konverter sie sauber liest.
- **Vierte Spalte (Wer):** in PowerPoint im Balken (weiß, dunkelblau auf Hellblau), sonst
  rechts daneben, sonst links davor. In Word als eigene Spalte; abweichende Verantwortliche sind
  auch dort hellblau schattiert (Plan nennt für Word nur `006FB9`; so zeigen beide Formate
  dasselbe).
- **Meilenstein** = Start und Ende am selben Tag: Raute `004676` (Folie), `◆` in `004676` in der
  Zelle (Word).
- **Word-Tabelle:** Spaltenbreiten fest 28 % Vorgang, 12 % Wer, der Rest gleich verteilt
  (`design/word.GANTT_*`); Kopfzeile wiederholt sich; Schrift der Tabellenvorlage.
- **PowerPoint:** neuer Flow-Block statt eines Visuals — `::: …` macht die Folie ohnehin zur
  Flow-Folie, so stapeln Text davor/danach und Spalten (`::: columns`) wie gewohnt. Ein Block ist
  eine Einheit beim Teilen auf „(Forts.)"-Folien.
- **Dunkle Folien (`.dark`):** Text weiß, Termine/Heute-Linie hellblau (kleine Ergänzung, damit
  die Bausteine dort lesbar sind).
- **Fehler** für: kein/zu viele Einträge, unlesbarer Termin, fehlender Doppelpunkt, leerer Text,
  falsche Reihenfolge, unbekanntes Attribut (nur `{.done}`), Eintrag aus mehreren Blöcken,
  Container ohne Liste/Tabelle, 3 oder 4 Spalten, leerer Name, fehlender Start/Ende, Ende vor
  Start, 1–12 Zeilen, unbekanntes `raster=`, mehr als 24 Spalten.

### Abweichungen

- `TimelineEntry.text` ist **Klartext** (`str`), nicht `Runs`: das Zeichenmodell hat nur fett
  oder nicht; Fett, Kursiv, Links und Code im Eintrag werden zu Text. Zusätzlich hat der Eintrag
  `label` (der Termin wie geschrieben) und `line`.
- `grid_for(start, end)` statt `grid_for(rows)`; `Gantt` trägt zusätzlich `units`, `today`,
  `name_heading`, `owner_heading`.
- Tests der Leser liegen nach dem Spiegelbaum in `tests/generation/common/test_schedule.py`
  (Plan: `tests/drawing/test_schedule.py`, dort liegen die Zeichnungstests).
- **Konverter (E07):** der PPTX-Konverter lässt die Formgruppen weg (wie alle `Drawing`-Gruppen
  seit E06-S02), statt sie als Bild zu lesen; der DOCX-Konverter liest den Zeitstrahl als Bild
  und den Gantt als Tabelle mit `■` (und `◆` für Meilensteine). Beides steht in den
  Erwartungsdateien der Rundreisen.
- Zeitstrahl in PowerPoint ≈ 3 cm statt ≈ 4 cm hoch (Höhe nach Inhalt, ohne Leerraum).

### Warnungen

- **„Heute"** ist das Front-Matter-`datum`, ohne `datum` der Tag des Erzeugens
  (`date.today()`). Der Plan sagt „vor `heute` bzw. dem Front-Matter-`datum`"; vorsichtigste
  Lesart: das Dokumentdatum gilt, weil es reproduzierbar ist. Ohne `datum` hängt das Ergebnis vom
  Tag ab (Grau, Heute-Linie) — das verletzt streng genommen „jeder Aufruf ist unabhängig" nur
  über die Uhr. Die Beispiele haben ein `datum`.
- **Vergangen** heißt: das **Ende** des Termins liegt vor heute (ein Quartal ist erst nach seinem
  letzten Tag vergangen). Termine des Zeitstrahls: Marke und Termin werden grau, der Text bleibt
  `404040`. Im Gantt gibt es kein Grau (der Plan nennt dort keins).
- **Textbreiten sind geschätzt** (`estimate_width`, halbe Schriftgröße je Zeichen) — wie im
  übrigen Zeichenweg. Breite Buchstaben können in PowerPoint knapper stehen als berechnet.
- **Ohne Office geprüft:** dass PowerPoint die Gruppe und Word die Tabelle mit `tcBorders` und
  `w:shd` ohne Reparaturmeldung öffnet, ist nicht geprüft (kein PowerPoint/LibreOffice auf der
  Maschine); die Schema-Reihenfolge im `w:tcPr` (Breite, Ränder, Schattierung) ist getestet.
- Der Zeitstrahl braucht in Word das Extra `svg` wie alle Zeichnungen (Fehler mit Hinweis).

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-praesentation.pptx`, Kapitel „Zeitstrahl und Projektplan":
  Formen einzeln verschieben; Gantt mit Heute-Linie im November 2026, Abnahme hellblau,
  Go-live als Raute.
- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitte „Zeitstrahl" und „Projektplan":
  Bild in Satzspiegelbreite; Tabelle im PTA-Format, Laufzeit blau, Spalte „Nov" mit dunkelblauer
  Linie rechts.
- `./run.sh test tests/generation/common/test_schedule.py tests/drawing/test_schedule.py
  tests/generation/pptx/test_schedule.py tests/generation/docx/test_schedule.py`.

### Offene Punkte

- **PDF (E05-S04):** der PDF-Generator muss `::: timeline` und `::: gantt` selbst setzen —
  beide als Grafik über `drawing.schedule.draw(…, width)` in Satzspiegelbreite;
  `layout_syntax.check(…, today=schedule.reference_day(datum))` aufrufen.
- E15-S02 (Schritte, Risikomatrix) kann den Weg `ScheduleBlock` → `FlowWriter` und die
  Word-Tabelle mit Schattierung (`_shade`, `_right_rule`) übernehmen.
- Abhängigkeiten zwischen Vorgängen gibt es bewusst nicht (Antwort zu Frage 1).
