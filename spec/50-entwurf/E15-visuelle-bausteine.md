# E15 Visuelle Bausteine: Zeitstrahl, Schrittfolgen, Bewertungen, Icons, Bilder

> Status: Entwurf

## Ziel

Die Grafiken, die in Beratungsfolien immer wieder von Hand gezeichnet werden — Zeitstrahl und
Projektplan, Schrittfolge als Pfeile, Bewertungsmatrix mit Harvey Balls, Risikomatrix, Icons in
Karten — entstehen aus wenigen Markdown-Zeilen im PTA-Design, in PowerPoint als editierbare Formen,
in Word und PDF als Grafik oder editierbare Tabelle. Dazu bekommen Bilder Fokus und Stile, damit
der Beschnitt der PTA-Platzhalter das Richtige zeigt.

## Motivation

Ein Angebot braucht einen Projektplan, ein Statusbericht eine Risikomatrix, eine Konzeptfolie ein
Vorgehen in fünf Schritten. Heute entsteht das in PowerPoint mit Rechtecken und Pfeilen, jedes Mal
anders und selten im Raster der Vorlage; eine KI kann es gar nicht. Weder DocLibs noch
vt-tools-libs kennen solche Bausteine (dort gibt es Mermaid und Charts, aber keine Schrittfolge,
keinen Zeitstrahl, keine Bewertungssymbole) — eigene Idee aus dem Abgleich vom 2026-11-07.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E15-S01](../60-prüfung/E15-S01-zeitstrahl-und-gantt.md) | `::: timeline` aus einer Liste, `::: gantt` aus einer Tabelle: Formen auf Folien, editierbare Tabelle in Word | in Prüfung |
| [E15-S02](../60-prüfung/E15-S02-schritte-bewertungen-risikomatrix.md) | `::: steps` als Chevrons, Harvey Balls `[3/4]` in Tabellen, `::: riskmatrix` als 5 × 5-Matrix | in Prüfung |
| [E15-S03](../60-prüfung/E15-S03-icons.md) | `:icon-name:` aus einem gebündelten Icon-Set in Karten, Listen und Text | in Prüfung |
| [E15-S04](E15-S04-bild-fokus-und-stile.md) | Bildattribute `focus`, `fit` und Stile `.round`, `.grey` | Entwurf |

## Bereichsweite Entscheidungen

- **Syntax englisch** wie die übrige Folien-Syntax (`::: timeline`, `::: steps`, `{.current}`);
  Front-Matter-Schlüssel bleiben deutsch. Die Container werden in `layout_syntax.CONTAINERS`
  (E02-S02) registriert, damit Word, PowerPoint und PDF dieselben Fehler melden.
- **Ein Zeichenweg:** jeder Baustein erzeugt ein `Drawing` (E02-S03). PowerPoint schreibt es als
  Formgruppe in die Inhaltsfläche (editierbar, am Raster von E04-S03), Word und PDF als SVG/PNG
  über E03-S04 bzw. E05-S04 — mit zwei Ausnahmen, die in Word als Tabelle besser aufgehoben sind:
  Gantt (E15-S01) und Risikomatrix (E15-S02).
- **Farben nur aus `design.colors`:** PTA-Blau `006FB9` und Dunkelblau `004676` für Formen,
  Hellblau `9FD8FF` für Nebenflächen, Grau `787878`/`AFAFAF`/`E6E6E6` für Vergangenes und
  Raster, Signalfarben (`STATUS_COLORS`) ausschließlich für Bewertungen und Risiken.
- **Schrift:** Segoe UI über das Designmodell; in Grafiken nicht unter 10 pt; was nicht passt, ist
  ein Fehler oder ein Hinweis (E08-S01), nie ein stummes Kürzen.
- **Rückweg (E07):** Formgruppen und Bilder werden als Bild bzw. Text zurückgelesen; die
  Rundreise hält die Abweichung in den Erwartungsdateien fest.

## Akzeptanz

Ein Beispiel-Deck `visuals.md` (Zeitstrahl, Gantt, fünf Schritte, Bewertungstabelle mit Harvey
Balls, Risikomatrix, Karten mit Icons, Kontaktfoto rund, Foto mit `focus=top`) ergibt in
PowerPoint Folien, deren Formen in der Inhaltsfläche am Raster liegen und sich einzeln bearbeiten
lassen, und in Word denselben Inhalt als Grafiken und Tabellen; alle Farben stammen aus dem
Designmodell.

## Offene Fragen

1. Hat die PTA in der Vorlagensammlung oder in echten Decks Muster für Zeitstrahl, Schrittfolge
   oder Risikomatrix, an denen sich die Maße orientieren sollen? Die Vorlagensammlung
   (`source-templates/PTA-Powerpoint-Vorlagensammlung.pptx`) zeigt keine; die Stories schlagen
   eigene Maße im Raster vor.

> (2026-11-07) Keine Muster vorhanden; eigene Maße im Raster.
2. Sollen die Bausteine auch im **Bericht** (Word/PDF) alle verfügbar sein, oder reichen dort
   Gantt-Tabelle und Risikomatrix, weil Zeitstrahl und Chevrons Folienmuster sind? Vorschlag:
   alle, als Grafik — ein Konzept zeigt dasselbe Vorgehen wie die Folie dazu.

> (2026-11-07) Alle, als Grafik.

## Notizen

- Abhängigkeiten: E02-S02 (Container), E02-S03 (`Drawing`), E04-S03 (Raster, Formen in der
  Inhaltsfläche), E03-S04 (Zeichnungen in Word), E06-S04 (SVG → PNG), E08-S01 (Hinweise).
