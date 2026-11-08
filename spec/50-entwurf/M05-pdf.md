# M05 PDF

> Status: Entwurf

## Ziel

Markdown → PDF/A-2b über die portierte Layout-Engine im PTA-Seitenrahmen, mit Folien-Syntax und Grafiken, dazu PDF → Markdown.

## Stories

Reihenfolge = vorgeschlagene Umsetzungsreihenfolge (aus den Verweisen zwischen den Stories).

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E05-S01](../60-prüfung/E05-S01-grundgeruest-pdf.md) | Grundgerüst PDF: reportlab, pikepdf, PDF/A-2b | in Prüfung |
| [E05-S02](../60-prüfung/E05-S02-layout-engine.md) | Layout-Engine portieren | in Prüfung |
| [E05-S03](../60-prüfung/E05-S03-pta-seitenrahmen.md) | PTA-Seitenrahmen | in Prüfung |
| [E05-S04](E05-S04-zeichen-folien-syntax-grafiken.md) | Fehlende Zeichen, Folien-Syntax, Diagramme und Charts im PDF | Entwurf |
| [E07-S04](E07-S04-pdf-nach-markdown.md) | PDF → Markdown | Entwurf |
| [E05-S05](E05-S05-authoring-guide-pdf.md) | Authoring Guide PDF | Entwurf |

## Offene Fragen

1. Passt dieser Zuschnitt?

> (2026-11-07) Ja. M02–M06 werden ohne Zwischenprüfung nacheinander umgesetzt (Agent `docs-2`);
> der Mensch prüft danach alle Stories in `spec/60-prüfung/`.

## Notizen

- Größtes technisches Risiko (Layout-Engine). Bewusst nach M02–M04, damit Word und PowerPoint vorher vollständig sind.
- Nach jedem Meilenstein prüft der Mensch, bevor der nächste beginnt.
