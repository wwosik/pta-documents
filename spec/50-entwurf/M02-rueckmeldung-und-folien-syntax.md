# M02 Rückmeldung und Folien-Syntax

> Status: Entwurf

## Ziel

Generatoren melden, was sie umgehen mussten, `check` prüft ohne zu erzeugen, und die Folien-Syntax samt Flow-Layouts und Sprechernotizen steht in PowerPoint und Word. Darauf bauen alle späteren Meilensteine auf.

## Stories

Reihenfolge = vorgeschlagene Umsetzungsreihenfolge (aus den Verweisen zwischen den Stories).

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E08-S01](../60-prüfung/E08-S01-hinweise-aus-der-erzeugung.md) | Hinweise aus der Erzeugung | in Prüfung |
| [E02-S02](../60-prüfung/E02-S02-folien-syntax.md) | Folien-Syntax: Heading-Attribute, Container, Alerts, Markierungen, Status-Labels | in Prüfung |
| [E02-S04](../60-prüfung/E02-S04-code-block-renderer-und-bildkonverter.md) | Code-Block-Renderer und Bildkonverter | in Prüfung |
| [E04-S03](../60-prüfung/E04-S03-flow-layouts-im-pta-stil.md) | Flow-Layouts im PTA-Stil | in Prüfung |
| [E04-S04](../60-prüfung/E04-S04-weitere-layouts.md) | Weitere Layouts: Agenda, Zwischenfazit, Zitat, Kontakt, Diagramme | in Prüfung |
| [E03-S03](../60-prüfung/E03-S03-folien-syntax-in-word.md) | Folien-Syntax in Word | in Prüfung |
| [E09-S01](../60-prüfung/E09-S01-sprechernotizen.md) | Sprechernotizen | in Prüfung |
| [E07-S01](../60-prüfung/E07-S01-formaterkennung-und-registry.md) | Formaterkennung und Registry | in Prüfung |
| [E17-S02](E17-S02-typografie-und-code.md) | Deutsche Typografie, Silbentrennung, Code-Highlighting | Entwurf |
| [E08-S02](E08-S02-pruefbefehl-und-stilregeln.md) | Prüfbefehl und Stilregeln | Entwurf |
| [E08-S03](E08-S03-funktionsuebersicht-durch-tests.md) | Funktionsübersicht durch Tests gesichert | Entwurf |

## Offene Fragen

1. Passt dieser Zuschnitt?

> (2026-11-07) Ja. M02–M06 werden ohne Zwischenprüfung nacheinander umgesetzt (Agent `docs-2`);
> der Mensch prüft danach alle Stories in `spec/60-prüfung/`.

## Notizen

- E08-S03 legt hier die Funktionsübersicht an; jede spätere Story ergänzt sie um ihre Syntax.
- Nach jedem Meilenstein prüft der Mensch, bevor der nächste beginnt.
