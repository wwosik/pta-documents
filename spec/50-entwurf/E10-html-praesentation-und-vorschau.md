# E10 HTML-Präsentation und Vorschau

> Status: Entwurf

## Ziel

Aus demselben Markdown wie für PowerPoint eine **einzelne HTML-Datei** mit denselben Folien im
PTA-Look, die jeder Browser zeigt — und darauf aufbauend eine Vorschau als Bilder, damit Mensch
und KI ein Deck prüfen können, ohne PowerPoint zu haben.

## Motivation

vt-tools-libs hat `DocumentGeneration.Html` (`~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration.Html/`,
~2 600 Zeilen C# plus 554 Zeilen `deck.css`/`deck.js`): eine selbständige HTML-Datei mit
denselben Folien und Layouts wie PPTX, Notizenpanel mit Timer, Fortschrittsbalken, Druck je Folie
auf eine Seite. Für die PTA kommt ein zweiter Grund hinzu: auf der Entwicklungsmaschine, in CI
und bei einer KI, die Decks schreibt, gibt es kein Office. Heute endet jede Prüfung bei „öffnet
PowerPoint die Datei ohne Reparatur?" als Prüfpunkt des Menschen. Ein HTML-Deck lässt sich im
Browser ansehen und mit Playwright zu PNGs rendern; die KI kann ihr eigenes Ergebnis anschauen,
bevor der Anwender es tut.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E10-S01](../60-prüfung/E10-S01-html-deck-generator.md) | `HtmlDeckGenerator`: eine HTML-Datei, PTA-Look aus dem Designmodell, gleiche Folien wie PPTX, Notizen/Builds/Übergänge aus E09, Druck | in Prüfung |
| [E10-S02](../55-in-arbeit/docs-2/E10-S02-vorschau-als-bilder.md) | `./run.sh preview`: HTML-Deck mit Playwright zu PNG je Folie und Kontaktbogen; Empfehlung an die KI | in Bearbeitung (docs-2) |

## Bereichsweite Entscheidungen

- **Der PTA-Look wird nachgezeichnet, nicht erfunden.** Farben, Schriftgrößen, Lagen von Titel,
  Fußzeile, Logo, Eckklammern und Inhaltsfläche kommen aus dem Designmodell (E01-S01), das sie
  aus `slides-basis.pptx` liest; das Logo aus E01-S04 als SVG. Es gibt keine HTML-eigenen
  Gestaltungsmittel und keine Optionen für Farben.
- **Schrift:** `font-family: "Segoe UI", Selawik, sans-serif`; Selawik (OFL, E01-S03) wird als
  WOFF2 eingebettet, Segoe UI **nie** (Lizenz). Auf PTA-Rechnern sieht das Deck damit exakt wie
  PowerPoint aus, anderswo mit Selawik metrisch gleich.
- **Gleicher Parser, gleiche Modelle** wie PPTX (`generation/pptx/parser.py`, `model.py`,
  `fitting.py`): Folien werden an denselben Stellen geteilt, damit HTML und PPTX dieselbe
  Foliennummer für denselben Inhalt haben. Der HTML-Generator ist ein zweiter Writer, kein
  zweiter Parser.
- **Kein Rohes HTML, kein Skript aus dem Markdown.** Anders als vt-tools-libs (`AllowRawHtml`
  Standard `true`) wird Rohes HTML immer als Text gezeigt; skriptgesteuerte Szenen entfallen.
  Decks werden von einer KI geschrieben und per Mail weitergegeben — sie dürfen nichts
  ausführen, was nicht aus der Bibliothek stammt.
- **Dateiname:** `…-praesentation.html` neben `.pptx`; `./run.sh generate --html` erzeugt es,
  standardmäßig wird es **nicht** miterzeugt (Frage 1).
- Playwright ist ein **Extra** (`[preview]`), nie Pflicht; ohne es funktioniert alles andere.

## Akzeptanz

`samples/gsb/gsb-praesentation.md` ergibt eine HTML-Datei, die in Chrome, Edge und Firefox die
gleichen Folien zeigt wie die PPTX in PowerPoint (gleiche Anzahl, gleiche Titel, gleiche
Teilung), und `./run.sh preview samples/gsb` legt je Folie ein PNG ab.

## Offene Fragen

1. Soll `./run.sh generate` für jede Präsentation **immer** auch das HTML schreiben (Vorschau
   ohne weiteren Befehl), oder nur mit `--html`? Vorschlag: nur mit `--html`, damit `documents/`
   nicht voller Dateien liegt, die niemand öffnet; die KI-Anleitung nennt den Schalter.

> (2026-11-07) Nur mit `--html`.
2. Ist das HTML-Deck auch ein **Zielformat** für die PTA (Vortrag im Browser, Weitergabe als eine
   Datei) oder nur Vorschau? Davon hängt ab, wie viel Mühe in Druck, Notizenpanel und
   Tastaturbedienung geht.

> (2026-11-07) Als Vorschau gewünscht (HTML-Deck und PNG-Vorschau, E10-S01 und E10-S02);
> nicht als Zielformat. Druck, Notizenpanel und Tastatur nur so weit, wie die Vorschau sie braucht.

## Notizen

- Reihenfolge: E10-S01 kann ohne E09 beginnen (Folien ohne Notizen/Builds) und zieht E09 nach,
  sobald es da ist. E10-S02 braucht E10-S01.
- Für Word gibt es keinen vergleichbaren Weg ohne LibreOffice; siehe E10-S02, Frage 2.
