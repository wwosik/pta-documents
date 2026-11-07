# E12 Dokumentpflege: Historie, Vergleich, Kennzeichnung

> Status: Entwurf

## Ziel

Was ein Dokument über sich selbst sagt und wie es sich über Fassungen hinweg verhält: eine
Dokumentenhistorie nach dem Deckblatt, ein Word-Vergleich zweier Markdown-Fassungen mit
Änderungsverfolgung, und eine Kennzeichnung („Vertraulich", „Entwurf") in Word und PDF, die zum
Sticker der Folien passt.

## Motivation

DocLibs und vt-tools-libs erzeugen jedes Dokument frisch und wissen nichts von seiner
Vorgeschichte. Konzepte und Angebote einer Beratung leben aber in Fassungen: Version 0.9 geht an
den Kunden, 1.0 nach seinen Anmerkungen, 1.1 nach dem Workshop. Eine Historientabelle gehört zu
jedem PTA-Dokument, und die Frage „was hat sich gegenüber der letzten Fassung geändert?" wird
heute mit Word-Vergleich von Hand beantwortet. Ein Entwurf, der ohne Kennzeichnung beim Kunden
landet, ist peinlich; die Folien bekommen ihren Sticker schon (E04-S05), Word und PDF noch nicht.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E12-S01](E12-S01-aenderungshistorie.md) | Dokumentenhistorie als Tabelle nach dem Deckblatt, aus `::: historie` oder aus `git log` | Entwurf |
| [E12-S02](E12-S02-dokumentvergleich.md) | Zwei Markdown-Fassungen → Word mit Änderungsverfolgung; `./run.sh vergleich` | Entwurf |
| [E12-S03](E12-S03-kennzeichnung-word-und-pdf.md) | `kennzeichnung:` in Word-Kopfzeile und PDF, Wasserzeichen „ENTWURF"; Abgleich mit dem PPTX-Sticker | Entwurf |

## Bereichsweite Entscheidungen

- **Git bleibt im Werkzeug.** Die Bibliothek liest weder Dateien noch Git; `tools/generate/`
  und das neue `tools/vergleich/` holen Historie und alte Fassungen aus Git und übergeben sie als
  Text bzw. zweites `MarkdownDocument`.
- **Markdown ist die Quelle der Wahrheit**, nicht das Word-Dokument: der Vergleich vergleicht
  Markdown und erzeugt daraus ein Word mit Änderungsmarkierungen; er liest keine Änderungen aus
  fremden Word-Dateien.
- Die Historientabelle und die Kennzeichnung nutzen Formatvorlagen und Positionen der
  PTA-Vorlagen (E01-S01, E03), keine eigenen Stile; die Texte („Vertraulich", „Entwurf",
  „Dokumentenhistorie") folgen `sprache`.

## Akzeptanz

Ein Konzept in zwei Fassungen in `samples/`: Fassung 2 trägt `kennzeichnung: entwurf` und eine
Historie mit zwei Zeilen; `./run.sh vergleich` beider Fassungen ergibt ein Word-Dokument, dessen
Änderungen Word im Überprüfen-Modus zeigt und akzeptiert, sodass Fassung 2 herauskommt.

## Offene Fragen

1. Gibt es bei der PTA eine feste Form der Dokumentenhistorie (Spalten, Position, Pflicht)? Die
   Word-Vorlagen in `source-templates/` enthalten keine; der Vorschlag in E12-S01 folgt der
   üblichen Form Version | Datum | Autor | Änderung.

>

2. Soll der Vergleich (E12-S02) auch für Präsentationen gelten (PowerPoint kennt keine
   Änderungsverfolgung; denkbar wäre ein Vergleichs-Deck mit gelb markierten Änderungen)?
   Vorschlag: zunächst nur Word.

>

## Notizen

- (2026-11-07) Umsetzung gewünscht (Entscheidung des Menschen zu allen drei Epics E11–E13).
