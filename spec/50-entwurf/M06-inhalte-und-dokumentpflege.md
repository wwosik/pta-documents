# M06 Inhalte, Dokumenttypen und Dokumentpflege

> Status: Entwurf

## Ziel

Variablen, Bausteine, Tabellen aus Dateien, Historie und Vergleich, Glossar, Querverweise, Barrierefreiheit, Protokoll, Anforderungen, Abnahme, Skelette, Rückweg aus Word, Terminologie, `watch`.

## Stories

Reihenfolge = vorgeschlagene Umsetzungsreihenfolge (aus den Verweisen zwischen den Stories).

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E11-S01](E11-S01-variablen.md) | Variablen: Platzhalter aus Front Matter und Kommandozeile | Entwurf |
| [E11-S02](E11-S02-bausteine.md) | Bausteine: wiederverwendbare Markdown-Abschnitte | Entwurf |
| [E11-S03](E11-S03-tabellen-und-charts-aus-dateien.md) | Tabellen und Charts aus CSV- und Excel-Dateien | Entwurf |
| [E12-S01](E12-S01-aenderungshistorie.md) | Dokumentenhistorie | Entwurf |
| [E12-S02](E12-S02-dokumentvergleich.md) | Dokumentvergleich mit Word-Änderungsverfolgung | Entwurf |
| [E13-S02](E13-S02-querverweise.md) | Querverweise auf Kapitel, Tabellen und Abbildungen | Entwurf |
| [E13-S01](E13-S01-abkuerzungen-und-glossar.md) | Abkürzungen und Glossar | Entwurf |
| [E13-S03](E13-S03-barrierefreiheit.md) | Barrierefreiheit: Alt-Texte, Struktur, PDF/UA | Entwurf |
| [E14-S01](E14-S01-protokoll.md) | Protokoll-Modus: Beschlüsse, Aufgaben, offene Punkte | Entwurf |
| [E14-S02](E14-S02-anforderungen.md) | Anforderungen mit stabilen IDs | Entwurf |
| [E14-S03](E14-S03-abnahme-und-kalkulation.md) | Unterschriftenblock und rechnende Tabellen | Entwurf |
| [E14-S04](E14-S04-dokument-skelette.md) | Dokument-Skelette: `./run.sh new` | Entwurf |
| [E17-S01](E17-S01-rueckweg-aus-word.md) | Rückweg aus Word: Kommentare hin und zurück, Änderungen als Vorschlag | Entwurf |
| [E17-S03](E17-S03-terminologie-und-quellen.md) | Terminologieprüfung und Quellen aus `QUELLEN.md` | Entwurf |
| [E17-S04](E17-S04-watch-und-seitenumbrueche.md) | `watch`, Seitenumbrüche und Querformat-Abschnitte | Entwurf |

## Offene Fragen

1. Passt dieser Zuschnitt?

> (2026-11-07) Ja. M02–M06 werden ohne Zwischenprüfung nacheinander umgesetzt (Agent `docs-2`);
> der Mensch prüft danach alle Stories in `spec/60-prüfung/`.

## Notizen

- Liegt nach M05, damit die Stories mit PDF-Anteil (E13, E17-S04) in einem Zug fertig werden.
- Nach jedem Meilenstein prüft der Mensch, bevor der nächste beginnt.
