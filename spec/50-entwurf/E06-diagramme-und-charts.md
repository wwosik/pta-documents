# E06 Diagramme und Charts

> Status: Entwurf

## Ziel

Mermaid-Diagramme und `chart`-Blöcke (Balken, Linien, Flächen aus CSV, dazu die Finanzdiagramme)
in DOCX, PPTX und PDF — in den PTA-Farben.

## Motivation

DocLibs: `DocumentGeneration.Diagrams` (1 250 Zeilen, Mermaider) und `DocumentGeneration.Charts`
(2 350 Zeilen). Charts sind reiner eigener Code und lassen sich direkt portieren; Mermaid hängt an
der C#-Bibliothek Mermaider, für die es kein Python-Gegenstück gibt.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| E06-S01 | `chart`-Blöcke: Parser, `ChartSpec`, Zeichnung; native Diagramme in PPTX (python-pptx) und DOCX | noch nicht ausgearbeitet |
| E06-S02 | Finanzdiagramme (Entwicklung, Wachstum je Zeile, Ist vs. Referenz, Trend, zwei Jahre, Übersichtstabelle), auch als SVG | noch nicht ausgearbeitet |
| E06-S03 | Mermaid: Weg festlegen (siehe Offene Fragen), SVG → `Drawing`, editierbare Formen in Folien | noch nicht ausgearbeitet |
| E06-S04 | SVG → PNG (resvg) und SVG-Bilder in Folien (`asvg:svgBlip`) und Dokumenten | noch nicht ausgearbeitet |

## Bereichsweite Entscheidungen

- Diagramm- und Chartfarben aus der PTA-Palette (E01-S01): Akzente `006FB9`, `004676`,
  `9FD8FF`, `787878`, `AFAFAF`, `E6E6E6` in dieser Reihenfolge, soweit die Designanalyse nichts
  Genaueres ergibt.

## Akzeptanz

Die Beispiel-Markdowns von DocLibs (`diagrams.md`, Chart-Beispiele) ergeben in allen drei
Formaten Grafiken in den PTA-Farben.

## Offene Fragen

1. Mermaid: (a) **mermaid-cli** (Node.js + Chromium als Abhängigkeit, `htmlLabels: false`) —
   Vorschlag, wenn Node verfügbar ist; (b) Mermaider nach Python portieren (sehr großer Aufwand);
   (c) Mermaid vorerst weglassen. Wichtig: keine Online-Dienste (mermaid.ink o. Ä.), damit kein
   Inhalt das Haus verlässt.

>

2. Werden die Finanzdiagramme bei der PTA gebraucht, oder genügen die einfachen Charts?

>

## Notizen

